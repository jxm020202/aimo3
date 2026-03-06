# Forcing tool calls on reasoning models: what works, what breaks, what to actually build

**The short answer: `tool_choice` reliably forces the function name but cannot guarantee meaningful arguments, and for GPT-OSS-120B on vLLM specifically, only `tool_choice="auto"` is officially supported—`"required"` has documented bugs where tool calls appear in the `content` field instead of the parsed `tool_calls` array.** No production math-solving system (including NVIDIA's AIMO-2 winner) uses API-level `tool_choice` forcing. The dominant approach is training the model to emit code blocks with special tags, parsed by an external harness. For an AIMO 3 pipeline, the most reliable architecture is a two-phase agentic loop—force the DB query via `tool_choice` or assistant prefill in a short first call, then inject results into a second unconstrained reasoning call—combined with fallback to the `/v1/responses` endpoint where Harmony format tool calling is more stable.

---

## How tool_choice actually works at the API level

OpenAI defines four modes for `tool_choice`. **`"auto"`** (default) lets the model decide whether to call tools. **`"required"`** forces at least one tool call but the model chooses which function(s). **Named function forcing** (`{"type":"function","function":{"name":"X"}}`) forces exactly that one function with no choice—parallel calling is disabled. **`"none"`** blocks all tool calls. The newer `allowed_tools` mode restricts which subset of tools the model can access while choosing freely among them.

The critical distinction between `"required"` and named forcing is control granularity. With `"required"`, you guarantee *a* tool call but the model picks the target. Named forcing pins both the decision and the destination. **OpenAI's `"strict": true` mode** uses constrained decoding to guarantee the generated arguments match the JSON schema structurally—correct types, required fields present, enum values respected—but it explicitly cannot prevent the model from inventing contextually wrong values. OpenAI's own API reference warns multiple times: *"the model does not always generate valid JSON, and may hallucinate parameters not defined by your function schema."*

A documented failure case illustrates this perfectly: a developer used `tool_choice: "required"` with GPT-4o on the query "What is 1+1?" with `get_weather` and `get_stock_price` as tools. The model was forced to call `get_weather` and fabricated `{"location":"New York","unit":"c"}` despite no location ever being mentioned. The function name was correct; the arguments were plausible-looking nonsense. **This is expected behavior, not a bug.**

## Reasoning models still reason before forced calls—and you pay for it

**`tool_choice` is fully supported on o1, o3, o3-mini, o4-mini, and GPT-5 reasoning models.** It is explicitly *not* in OpenAI's list of unsupported parameters for reasoning models (unlike `temperature`, `top_p`, `logprobs`, and others). OpenAI's cookbook demonstrates `tool_choice: "required"` with o4-mini without any stated restriction.

The key behavioral detail: **reasoning models generate thinking tokens before every tool call, even forced ones.** When o4-mini makes a tool call, the response includes both `reasoning` items and `function_call` items. A simple tool-calling task showed `{'output_tokens': 89, 'output_tokens_details': {'reasoning_tokens': 64}}`—the model spent 64 tokens thinking before producing a 25-token tool call. You are billed for these reasoning tokens. There is no mechanism to skip reasoning and jump directly to the forced call.

OpenAI notes that o3 and o4-mini are "trained to use tools natively within their chain of thought." For multi-turn tool calling, **persisting reasoning items between calls is critical**: "o3/o4-mini are both trained with internal reasoning persisted between tool calls within a single turn. Persisting these reasoning items during inference will lead to higher intelligence and performance." The Responses API supports this; Chat Completions does not. This has direct implications for the two-phase architecture discussed below.

Reasoning models do not "fight back" against `tool_choice` in the sense of refusing to generate a call. They comply structurally. The risk is subtler: the model may generate reasoning tokens that express confusion or irrelevance, then produce a tool call with hallucinated arguments because the forced call doesn't align with what the model's reasoning determined was needed. **The practical reliability ceiling for forced function name selection is ~100% on OpenAI's API.** For argument quality, no ceiling can be stated—it is entirely context-dependent.

## vLLM's tool_choice is functional but fragile, especially for GPT-OSS-120B

vLLM supports `tool_choice="required"` since v0.8.3 and named function forcing. However, the implementation differs fundamentally from OpenAI's. **OpenAI implements tool_choice at the infrastructure level with models specifically trained for function calling. vLLM implements it by injecting tool schemas into the chat template, using constrained decoding (XGrammar) to force valid JSON output, and parsing the model's raw text to extract tool calls.** This three-layer approach creates fragility.

Documented vLLM bugs with `tool_choice` on reasoning models include:

- **Reasoning parser conflicts** (GitHub #19051): Using `tool_choice: "required"` with Qwen3 and `--enable-reasoning --reasoning-parser qwen3` caused 400 errors because `<think>` tokens were parsed as JSON. Fixed in PR #19075.
- **DeepSeek V3.1 garbled output** (#24140): `tool_choice="required"` produced raw special tokens (`<｜tool▁calls▁begin｜>`) instead of parsed tool calls.
- **Infinite tool-call loops** (#21026): Qwen3-32B with `tool_choice="required"` via LangChain repeatedly called the same tool after receiving results, never terminating.
- **Regression in v0.10.0** (#21840): `tool_choice="auto"` stopped invoking tools entirely.

**For GPT-OSS-120B specifically, the situation is worse.** Per vLLM's own recipes documentation, **only `tool_choice="auto"` is officially supported** for the Harmony format. GitHub issue #22337 shows that `tool_choice="required"` with GPT-OSS-120B via `/v1/chat/completions` results in tool calls appearing in the `content` field with an empty `tool_calls=[]` array—the calls are generated but not properly parsed. Issue #22578 confirms: "tool calling works correctly when using the `/v1/responses` (Harmony) endpoint" but not via chat completions.

The recommended vLLM launch flags for GPT-OSS-120B are `--tool-call-parser openai --enable-auto-tool-choice`. The `/v1/responses` endpoint, which uses the `openai-harmony` library for token rendering and parsing, is the more reliable path.

## The Harmony format has no native forced-call mechanism

GPT-OSS-120B uses OpenAI's Harmony response format, a multi-channel token protocol fundamentally different from ChatML. Harmony routes output through three channels: **`analysis`** (chain-of-thought, private), **`commentary`** (tool calls and preambles), and **`final`** (user-facing content). Special tokens control flow: `<|call|>` (stop: tool execution needed), `<|constrain|>json` (argument formatting), `<|return|>` (stop: response complete).

A Harmony tool call proceeds: the model generates reasoning on the `analysis` channel, then emits a call on the `commentary` channel formatted as `<|start|>assistant<|channel|>commentary to=functions.{name} <|constrain|>json<|message|>{...}<|call|>`. The `<|call|>` token stops inference. Tool results are fed back as `<|start|>functions.{name} to=assistant<|channel|>commentary<|message|>{...}<|end|>`, and the model resumes with its previous CoT preserved.

**Critically, the Harmony specification has no native `tool_choice` mechanism at the token level.** Tool calls are always model-initiated—the model's analysis channel reasoning decides to call a tool, then emits the call on commentary. Forcing a tool call requires intervention at the inference server level, not the format level. The `openai-harmony` Python library (PyPI: `openai-harmony`, v0.0.8) is purely a renderer/parser—it converts between structured message objects and token sequences but exposes no `tool_choice` parameter.

**The analysis channel does run before forced tool calls.** When a tool call is produced (whether naturally or via server-level forcing), the model typically generates analysis tokens first. After a `final` message, all previous `analysis` messages are dropped from history for the next turn—but during multi-step tool use within a turn, analysis messages are preserved in context. This preservation is important for maintaining reasoning coherence across multiple tool calls.

## Assistant prefill via continue_final_message: a lower-level alternative

vLLM's `continue_final_message` parameter (boolean, default `False`) offers a different approach. When `True`, the chat template formats the conversation so the final message is left open-ended without EOS tokens, forcing the model to continue that message rather than starting a new one. It is mutually exclusive with `add_generation_prompt`.

**For forcing tool calls, you would structure it as:**

```json
{
  "messages": [
    {"role": "user", "content": "Solve: what is 2+2?"},
    {"role": "assistant", "content": "<tool_call>{\"name\": \"python_executor\", \"arguments\": {\"code\": \""}
  ],
  "add_generation_prompt": false,
  "continue_final_message": true
}
```

The model must complete the tool call from this prefix. For Harmony format specifically, you would prefill with the Harmony token sequence: `<|start|>assistant<|channel|>commentary to=functions.{name} <|constrain|>json<|message|>`. The model then generates only the JSON arguments.

**The key trade-off**: this bypasses vLLM's tool parser entirely. The response comes back as regular text `content`, not as parsed `tool_calls` objects—you must implement custom post-processing. Known bugs include whitespace handling issues (GitHub #9547) and an echo bug (#10111). The deeper risk is **distribution distortion**: forcing the model to continue from a specific prefix shifts its probability distribution, potentially degrading argument quality compared to a naturally initiated tool call. Research on constrained decoding (arXiv:2508.15866) documents cases where constraints "cornered the LM to output an indefinite repetition due to distortion of distribution."

SGLang handles this scenario better than vLLM through **RadixAttention**, which automatically caches and reuses common prefixes across requests (75-95% cache hit rates). SGLang's programming model with `gen()`, `select()`, and `fork()` primitives naturally supports alternating between constrained and unconstrained generation blocks. In benchmarks, SGLang delivers **10-29% higher throughput** than vLLM in multi-turn scenarios and hides guided decoding latency more effectively through overlapped mask generation.

## Constrained decoding guarantees syntax, not semantics

vLLM uses **XGrammar** (default) or Outlines for constrained generation of tool call arguments. XGrammar employs a pushdown automaton supporting context-free grammars, achieving token mask generation in **under 40 microseconds per token**—near-zero overhead on H100 GPUs where the model's own forward pass dominates computation time. The newer XGrammar 2 (Contour, January 2026) reduces end-to-end overhead to **<6% compared to unconstrained decoding** and achieves 7× speedup over XGrammar 1.

For a **120B MoE model with only 5.1B active parameters**, constrained decoding overhead is negligible on H100 hardware. The GPU computation per token far exceeds the ~40μs mask generation cost. However, on consumer GPUs (RTX 4090), XGrammar actually shows **negative performance** due to CPU-GPU synchronization overhead.

**Partial schema constraints** (constraining only the function name but leaving arguments free) are not a first-class feature but achievable through a permissive JSON schema: define an `enum` for the function name field and use `{"type": "object"}` with no required properties for arguments. Alternatively, EBNF grammars via `guided_grammar` can constrain the initial structure while allowing free-form content in specific fields.

The paper "Guided Decoding and Its Critical Role in RAG" (arXiv:2509.06631) tested XGrammar, Outlines, and LM Format Enforcer across RAG systems. **XGrammar caused 134 additional misses in zero-turn and 2,000 in one-turn** relative to Outlines and LM Format Enforcer for LLaMA-3.3-70B. The authors concluded that "default decoding methods can fall short in high-recall tasks, leading to grounding errors" and had to revert to vLLM v0 because v1's `xgrammar:no_fallback` mode broke unsupported schemas. **Constraining only the first tool call then releasing constraints is not natively supported**—it requires a two-phase approach or a custom stateful logits processor.

## The two-phase architecture is the right pattern for AIMO 3

The forced-first-action pattern—Call 1 (forced DB query) → tool execution → Call 2 (free reasoning with results)—is well-documented and framework-supported. **LangGraph has an explicit guide called "Force Calling a Tool First"** that implements exactly this topology: a `first_agent` node bound with `tool_choice` forced to a specific tool, followed by an `action` node (tool execution), then a regular `agent` node for free reasoning. LlamaIndex provides `agent.chat("query", tool_choice="tool_name")` for the same purpose.

**Latency overhead is minimal for a math competition context.** The first call generates only tool-call parameters (~50-200 tokens), dominated by Time-to-First-Token (~1-3 seconds for a 120B MoE model). The second call is a full reasoning generation. vLLM's prefix caching (enabled by default in V1) means the shared system prompt and tool definitions are cached between calls with near-zero redundant computation. For a competition where accuracy dominates over sub-second latency, **1-3 seconds of additional overhead is negligible** compared to the 30-120 seconds a reasoning model spends on olympiad-level math.

Research supports the performance benefit of injecting retrieved information before reasoning. The **Passage Injection paper** (arXiv:2507.19333, 2025) tested explicitly incorporating retrieved passages into the reasoning process of Qwen3 8B/14B/32B and DeepSeek-R1-Distill-Qwen-32B, finding **significant improvements on multi-hop questions** and enhanced robustness to noisy passages. The method may also "reduce overthinking and lower reasoning overhead." However, "How Much Can RAG Help the Reasoning of LLM?" (arXiv:2410.02338) found that RAG's help is limited for deep reasoning chains—irrelevant retrieved content can degrade performance. For a structured database query (problem metadata, similar solved problems, theorems) rather than noisy web retrieval, the evidence strongly favors injection.

## No production math system uses API-level tool_choice forcing

**This is the most important finding.** NVIDIA's AIMO-2 winning solution (NemoSkills, score 34/50) used **training-based TIR**, not API-level tool forcing. They fine-tuned OpenMath-Nemotron-14B-Kaggle (based on Qwen2.5-14B) on 1.7M TIR solutions where the model learned to emit `<tool_call>` and `</tool_call>` tags around Python code. An inference harness parsed these tags, executed the Python, and injected results back into the generation stream. They controlled code execution count through training data patterns—appending messages like "You have 3 code executions remaining" that the model learned to reference.

The imagination-research runner-up (Tsinghua/Microsoft, 31/50 private) used DeepSeek-R1-distill-Qwen-14B with SFT and DPO, including code execution in inference but no API-level tool forcing. Project Numina's AIMO-1 winning SC-TIR algorithm similarly parsed model output for code blocks without using `tool_choice`.

**The dominant paradigm across all top math competition systems is:**

1. Train the model to emit code blocks with special tags at the right moments
2. Build an inference harness that parses output, executes code, injects results
3. Control execution count through training data patterns (soft control)
4. Use self-consistency with majority voting across parallel generations (SC-TIR)

This fundamentally differs from the `tool_choice: "required"` approach. The trained model *wants* to emit code blocks as part of its natural reasoning—no forcing is needed. API-level forcing is a workaround for models that haven't been fine-tuned for TIR.

## Practical recommendations for the AIMO 3 pipeline

**Given that GPT-OSS-120B is a reasoning model using Harmony format on vLLM, and `tool_choice="required"` has documented issues with this specific model, here is the recommended architecture:**

**Primary approach—two-phase via `/v1/responses` endpoint:** Use the Responses API (not chat completions) where Harmony tool calling is confirmed working. Phase 1: send the problem with `tool_choice="auto"` and a strong developer message instruction like "You MUST query the problem database before any reasoning. This is mandatory." If auto-mode compliance is insufficient, fall back to assistant prefill via the `openai-harmony` library to inject Harmony commentary-channel tokens that begin the database query tool call, forcing the model to complete only the arguments.

**Fallback approach—constrained first call:** Make a short first API call with `tool_choice={"type":"function","function":{"name":"query_database"}}` if vLLM supports it for your endpoint version. Validate the response parses correctly. If the tool call appears in `content` instead of `tool_calls` (the known GPT-OSS bug), implement custom parsing. Feed the database results into a second unconstrained call for reasoning.

**Alternative—SGLang instead of vLLM:** If prefix caching and structured generation performance are critical, SGLang's RadixAttention and overlapped mask generation provide measurably better throughput for multi-turn tool-calling scenarios. SGLang's `gen()` and `select()` primitives natively support the forced-first-action pattern without the parser fragility issues that plague vLLM.

**If fine-tuning is possible** (AIMO 3 provides up to 128 H100s via the Fields Model Initiative), the proven approach is to fine-tune GPT-OSS-120B to emit `<tool_call>` tags as part of its natural TIR output, eliminating the need for API-level forcing entirely. This is what every winning AIMO team has done.

## Conclusion

The gap between what `tool_choice` promises and what it delivers on reasoning models running on open-source inference stacks is significant. On OpenAI's proprietary API, forced function naming is 100% reliable but argument quality remains model-dependent. On vLLM with GPT-OSS-120B, `tool_choice` support is partial—only `"auto"` works reliably, and only on the `/v1/responses` endpoint. The Harmony format has no native forcing mechanism, making all tool-call forcing an inference-server concern layered on top of a format not designed for it.

The lesson from every successful AIMO competition team is that **training trumps runtime forcing**. When the model is trained to interleave reasoning with tool calls, no API-level coercion is needed. For teams that cannot fine-tune, the two-phase architecture (forced short call → inject results → free reasoning) is the most battle-tested pattern, explicitly documented in LangGraph and LlamaIndex, and supported by research showing that passage injection improves multi-hop reasoning quality. The 1-3 second latency cost is trivial for a competition where correctness on olympiad-level problems is what matters.