# Why GPT-OSS-120B ignores "query first" and how to fix it

**Reasoning models systematically deprioritize procedural instructions in favor of autonomous problem-solving — and this is a training-level property, not a prompting failure.** Research across multiple 2024–2025 papers shows that frontier reasoning models follow in-reasoning instructions less than 25% of the time, with GPT-OSS-20B scoring just 11% on instruction compliance. The good news: a combination of API-level forcing (`tool_choice`), host-side context injection, and (if needed) lightweight fine-tuning can achieve near-100% compliance. No AIMO competition winner has used a hint-database pattern — all relied on SFT for tool-integrated reasoning — but architectural solutions exist that bypass the model's resistance entirely.

This report covers the root causes of the behavior, every viable fix from prompt engineering through constrained decoding, and concrete recommendations for the math olympiad agentic pipeline.

---

## 1. Reasoning training creates a fundamental tension with procedural compliance

The core problem is architectural, not incidental. Three landmark papers from 2025 establish that scaling up reasoning capability *directly degrades* instruction following:

**"Scaling Reasoning, Losing Control" (MathIF, arXiv:2505.14810)** evaluated 23 large reasoning models and found "a consistent tension between scaling up reasoning capacity and maintaining controllability — models that reason more effectively often struggle to comply with user directives." The degradation worsens with harder problems and multi-constraint settings, meaning olympiad-level problems trigger the worst compliance.

**"ReasonIF" (arXiv:2510.15211)** directly tested GPT-OSS-120B, GPT-OSS-20B, Qwen3-235B, and DeepSeek-R1. **Frontier LRMs failed to follow reasoning instructions more than 75% of the time.** GPT-OSS-20B achieved an instruction-following score (IFS) of just **0.11** — meaning 89% noncompliance. Even after Reasoning Instruction Finetuning (RIF), this only reached 0.27. The paper attributes this to the RL training pipeline: "reinforcement learning with verifiable reward is deployed at scale to augment reasoning capability, while little attention is paid to their reasoning traces."

**"The Danger of Overthinking" (arXiv:2502.08235)** identified three patterns in reasoning models during agentic tasks. The most relevant is **analysis paralysis**: the model spends excessive time in internal reasoning while making minimal environmental progress. Reasoning models exhibited this pattern nearly **3× more often** than non-reasoning models. Per-unit increase in overthinking correlated with **7.9% lower task success rates**. Critically, o1-low run multiple times outperformed o1-high — evidence that deep reasoning actively undermines agentic tool-use compliance.

The mechanism is straightforward: GPT-OSS-120B was trained with RL that rewards correct final answers, not procedural compliance during reasoning. When it encounters an olympiad problem, its trained reasoning patterns activate immediately. The system prompt instruction to "query a database first" competes with — and loses to — the model's optimization to start solving. OpenAI's own guidance acknowledges this: reasoning models "perform best when provided with clear, direct instructions" but warns against "over-complicating your prompt with excessive instructions" because this "can confuse the model and hinder its built-in reasoning capabilities."

Additional compounding factors include **lost-in-the-middle effects** (system prompt instructions become effectively "middle" content after long reasoning traces, suffering 30%+ performance drops), **multi-turn degradation** (average performance drops 39% when instructions are revealed across multiple turns), and **vanilla CoT actually hurting instruction following** by producing "superficial reasoning that simply paraphrases the instructions" rather than decomposing and following them (RAIF, arXiv:2506.01413).

---

## 2. Prompting alone has a ceiling, but several techniques move the needle

### The only guaranteed prompt-level solution: `tool_choice` API parameter

The single most reliable mechanism is not a prompting technique — it is the **`tool_choice` API parameter**. Setting `tool_choice: {"type": "function", "function": {"name": "query_database"}}` forces the model to call that specific function. OpenAI confirmed this works with o1 and o3 reasoning models. vLLM supports this as of version 0.8.3+ for `required` and earlier for named functions. Under the hood, vLLM uses guided decoding (Outlines/XGrammar) to guarantee valid tool-call output.

The recommended pattern is a **two-phase agentic loop**: Call 1 forces the database query via `tool_choice`, Call 2 passes the results and uses `tool_choice: "auto"` for free reasoning. This removes the model's ability to skip the tool call entirely, transforming an unreliable prompting problem into a deterministic architecture choice.

### Prompting techniques ranked by effectiveness

**Instruction placement matters.** Put the "query database first" instruction in both the developer message (GPT-OSS-120B uses "developer messages" rather than system messages — the system message is reserved for meta-configuration like reasoning effort) and at the very end of the user message. Research on serial position effects (arXiv:2406.15981) confirms LLMs exhibit a U-shaped attention curve — strong primacy and recency bias, with poor attention to the middle. Google Research (December 2025) showed that simply repeating the prompt improved accuracy by up to **76 percentage points** on targeted tasks.

**XML-tagged mandatory steps** provide semantic structure that models can parse reliably. Anthropic's documentation recommends XML tags for complex prompts mixing instructions, context, and variables. The LPML framework demonstrated that XML-structured mathematical reasoning protocols (`<THINK>`, `<PYTHON>`, `<OUTPUT>`, `<ANSWER>` tags) achieved **76.6%** on GSM8K versus 57.1% for vanilla CoT. A practical template:

```xml
<CRITICAL_WORKFLOW>
STEP 1 (MANDATORY — BEFORE ANY REASONING):
Call query_database() to retrieve technique hints.
DO NOT reason about the problem until you have database results.

STEP 2: Analyze the database results alongside the problem.
STEP 3: Apply mathematical reasoning to solve.
</CRITICAL_WORKFLOW>
```

**Lowering reasoning effort helps.** The Overthinking paper showed that o1-low outperformed o1-high on agentic tasks at a fraction of the cost ($400 vs. $1,400). For the initial database-query step specifically, lower reasoning effort reduces the model's tendency to "overthink" and skip the tool call. You could use LOW or MEDIUM for the first forced call, then switch to HIGH for the actual solving step.

**Few-shot examples of correct behavior** can help, but NVIDIA explicitly found that "few-shot examples turned out to be unsuccessful" for inducing TIR behavior in strong reasoning models (DeepSeek-R1, QwQ-32B). Few-shot works better for models that already have good instruction-following but need behavioral nudging.

**Capitalization and emphasis** (ALWAYS, MUST, CRITICAL) have weak but nonzero effects. Production agent systems like Bolt use "ULTRA IMPORTANT" capitalization, but this is the weakest technique in the stack.

### Prefill / assistant turn injection

Anthropic supports "prefill" — starting the assistant message with specific tokens to force the model to continue from that point. Their documentation states: "when `tool_choice` is set to `any` or `tool`, Anthropic automatically prefills the assistant message to force a tool call." However, **prefilling is not supported with extended thinking enabled** — a critical limitation for reasoning models.

vLLM supports an equivalent via the `continue_final_message` parameter (detailed in Section 6 below). This is a powerful technique but requires careful implementation with GPT-OSS-120B's Harmony format.

---

## 3. Host-side injection beats model-side retrieval for reliability

### No AIMO winner has used a hint database

This finding is striking. None of the top AIMO-1 or AIMO-2 solutions employed retrieval databases or technique hints:

- **AIMO-1 winner (Project Numina, 29/50)**: Fine-tuned DeepSeekMath-7B with Tool-Integrated Reasoning on 70K problems plus self-consistency decoding. No RAG.
- **AIMO-2 winner (NVIDIA NemoSkills, 34/50)**: 540K unique problems, 1.7M TIR solutions, GenSelect for solution selection. No RAG.
- **AIMO-2 runner-up (imagination-research, 34/50)**: SFT + DPO for output length reduction. No RAG.

All winners relied on training data quality, tool-integrated reasoning (code execution), and inference-time compute (majority voting). OpenAI's o3-preview scored **47/50** on AIMO-2 problems without any retrieval system.

### When RAG does help math reasoning

**"How Much Can RAG Help the Reasoning of LLM?"** (arXiv:2410.02338) provides the definitive analysis. Retrieved documents containing intermediate reasoning results reduce the number of reasoning layers needed, extending reasoning depth from `l` to `l+c`. But the help is limited: noise in retrieved documents consumes reasoning capacity that potentially negates the benefit. **If filtering noise costs more than the RAG benefit, performance degrades.**

For GPT-OSS-120B at **97%+ on AIME with tools**, the model already knows most mathematical techniques from training. Hints are valuable only when they identify a **specific non-obvious technique** (e.g., "This problem can be solved using Vieta jumping") or provide a **direct intermediate result**. Vague or marginally relevant hints actively harm performance — the GSM-IC benchmark showed that even simple irrelevant sentences in math word problems degrade accuracy.

### The hybrid architecture recommendation

Anthropic's "Effective Context Engineering for AI Agents" (2025) recommends a hybrid approach: retrieve essential baseline context up front while enabling further exploration as needed. For the olympiad system, this translates to:

1. **Host-side**: Classify the problem type (algebra/geometry/number theory/combinatorics) and inject **1–2 highest-relevance technique hints** as a labeled section after the problem statement. Keep each hint to 50–150 tokens. Use soft guidance: "The following techniques MAY be relevant. Consider them only if they apply."
2. **Model-side (optional)**: Expose the SQLite database as a queryable tool for cases where the model explicitly needs additional techniques mid-reasoning.
3. **Minimize total context**: "Context Length Alone Hurts LLM Performance Despite Perfect Retrieval" (arXiv:2510.05381) showed **13.9%–85% degradation** as input length increases, even with perfect retrieval. Shorter context is always better.

This hybrid approach eliminates the compliance problem entirely for the initial retrieval step: the host always injects context, so the model never needs to "remember" to query the database.

---

## 4. GPT-OSS-120B's architecture shapes the solution space

GPT-OSS-120B is a real model released **August 5, 2025** under Apache 2.0. Its **116.8B total parameters with only 5.1B active** (128 experts per layer, 4 active per token) make it deployable on a single 80GB GPU via MXFP4 quantization. It scores **96.6% on AIME 2024** and **97.9% on AIME 2025** with tool access — jumping from ~88% without tools.

### The Harmony format is non-negotiable

GPT-OSS-120B uses the Harmony response format, a structured token protocol with three channels: `analysis` (chain-of-thought, not safety-trained), `final` (user-facing response), and `commentary` (function calls and preambles). The model's instruction hierarchy separates **system messages** (meta-config like reasoning effort), **developer messages** (your "system prompt" with task instructions and tool definitions), and **user messages** (the actual problem). Critically, **task instructions belong in the developer message, not the system message** — the system message is reserved for `"Reasoning: high"` and similar configuration.

The model is documented as **extremely verbose** — generating 11× more tokens than the average model at comparable capability. Its analysis channel commonly runs 20,000+ tokens for AIME problems. This verbosity directly contributes to the instruction-skipping behavior: by the time the model has reasoned through thousands of tokens, the developer message instruction to "query the database first" is effectively buried.

### Reasoning effort affects compliance

The model supports LOW, MEDIUM, and HIGH reasoning effort. Official benchmarks use HIGH for competition math, but an OpenAI community member reported that MEDIUM (69) outperformed HIGH (61) on LiveCodeBench v5 — suggesting HIGH can over-reason on certain tasks. For the database-query step specifically, **using MEDIUM or LOW reduces the reasoning preamble** that precedes tool calls, improving the odds that the model executes the tool call before getting absorbed in problem-solving.

The recommended two-phase approach leverages this: use LOW/MEDIUM reasoning effort for the forced database query call, then switch to HIGH for the actual solving step.

---

## 5. NVIDIA proved that prompting fails and fine-tuning works for TIR

The AIMO-2 winning paper (arXiv:2504.16891) provides the strongest evidence on this question. The NVIDIA NemoSkills team explicitly states:

> **"Our initial attempts to induce Tool-Integrated Reasoning from DeepSeek-R1 and QwQ-32B through simple prompting proved unsuccessful... Even few-shot examples turned out to be unsuccessful. Unable to solve this via prompting, we had to develop a more elaborate pipeline."**

Their hypothesis: "These models struggle to deviate from their standard solution format due to extensive training on reasoning tasks and limited exposure to instruction-following." This is the exact mechanism at work with GPT-OSS-120B.

### The SFT pipeline that works

NVIDIA's solution was an iterative SFT pipeline starting with LIMO-Qwen-32B (an instruction-following model fine-tuned on ~1,000 reasoning samples that retained instruction-following ability). They generated 15K filtered TIR examples, fine-tuned QwQ-32B on them, generated 700K new solutions, filtered to 260K, and repeated — building up to 1.7M TIR examples. The key insight: **a non-reasoning instruct model retained its instruction-following abilities after limited reasoning fine-tuning**, but strong reasoning models could not be prompted into novel behavioral patterns.

### How much data you need

The evidence suggests modest amounts suffice for behavioral pattern changes:

- NVIDIA NemoSkills started with just **15K filtered TIR samples** for stage-0 SFT
- LIMO showed that **~1,000 samples** suffice for long-CoT instruction following
- ComplyAdvantage achieved reliable format compliance with **~1,000 labeled examples**
- Stanford's "Instruction Following Without Instruction Tuning" found that even narrow single-task fine-tuning yields surprisingly broad instruction-following behavior

For "check hints first" behavior specifically, **500–2,000 synthetic examples** showing the desired sequence (receive problem → query database → incorporate hints → solve) would likely suffice for LoRA/QLoRA fine-tuning.

### When to choose fine-tuning vs. alternatives

| Approach | Best for | Fails when |
|----------|----------|------------|
| **Prompting only** | Instruct models, simple tool selection | Reasoning models with entrenched patterns, high reliability needs |
| **Few-shot examples** | Behavioral nudging for instruct-tuned models | Deep-RL reasoning models (NVIDIA confirmed failure) |
| **Constrained decoding** | Syntactic format compliance (JSON, XML structure) | Semantic/behavioral sequencing, reasoning quality preservation |
| **SFT fine-tuning** | Behavioral patterns, procedural sequences, reliable format following | Dynamic requirements, factual knowledge injection |
| **Architecture/orchestration** | Guaranteed tool invocation regardless of model | When model agency over retrieval is desired |

The guiding principle comes from Anyscale: **"Fine-tuning is for form, not facts."** Teaching the model to always query hints first is precisely a "form" problem — it is about action sequence structure, not new knowledge.

---

## 6. Constrained decoding and forced prefill provide deterministic guarantees

When prompting cannot be trusted, inference-level mechanisms provide hard guarantees. vLLM offers several approaches that work with GPT-OSS-120B.

### `tool_choice` with named function (simplest reliable approach)

vLLM's OpenAI-compatible API supports `tool_choice: {"type": "function", "function": {"name": "query_database"}}`. This uses guided decoding under the hood (XGrammar or Outlines) to guarantee the output is a valid call to the specified function. Start vLLM with `--enable-auto-tool-choice --tool-call-parser <parser>` and the model is forced to produce a valid tool call. The content of the call (e.g., the SQL query) is model-generated but the structure is guaranteed.

### `continue_final_message` for assistant prefill

vLLM supports injecting a partial assistant response that the model must continue from. By setting `continue_final_message: true` and `add_generation_prompt: false`, the final message in the conversation becomes a prefix the model extends:

```python
messages = [
    {"role": "developer", "content": "Always query the hint database first."},
    {"role": "user", "content": "Solve this olympiad problem: ..."},
    {"role": "assistant", "content": '```python\nimport sqlite3\nconn = sqlite3.connect("hints.db")\n'}
]
# Model continues from the partially-written code block
```

This bypasses the reasoning preamble entirely by starting the model mid-code-block. The technique has been available since vLLM 0.6.x.

### Combined prefill + constrained decoding (maximum reliability)

The strongest approach combines both: prefill fixes the first N tokens deterministically, while structured output constraints (grammar, regex, or JSON schema) guarantee the remaining tokens conform to a valid structure. vLLM supports `structured_outputs` with `grammar`, `regex`, or `json` constraints applied simultaneously with `continue_final_message`. XGrammar is the default backend; LLGuidance handles complex schemas better; both support caching for repeated schema compilations.

### SGLang as an alternative

SGLang offers compressed FSM-based constrained decoding that can skip token sampling entirely for deterministic sequences. When the constraint specifies `{"name": "query_database"` as a fixed prefix, SGLang skips those tokens in a single step. It also supports `tool_choice` parsing via `--tool-call-parser` and `--reasoning-parser` flags for reasoning models that emit thinking tokens before tool calls.

---

## Concrete recommendation: a three-tier solution

**Tier 1 — Architectural (implement immediately, guaranteed):** Restructure the agentic loop so the host always retrieves hints before presenting the problem to GPT-OSS-120B. Classify the problem type, query the SQLite database host-side, and inject 1–2 concise technique hints after the problem statement in the user message. This eliminates the compliance problem entirely since the model never needs to "remember" to query the database.

**Tier 2 — API-level forcing (implement if model-side retrieval is needed):** Use `tool_choice: {"type": "function", "function": {"name": "query_database"}}` for the first API call in the agentic loop, then switch to `tool_choice: "auto"` for subsequent calls. Alternatively, use `continue_final_message` to prefill the assistant response with the beginning of a database query code block. Use LOW or MEDIUM reasoning effort for this first call, then HIGH for solving.

**Tier 3 — Fine-tuning (implement if Tiers 1–2 are insufficient):** Generate 500–2,000 synthetic examples showing the correct behavioral sequence (problem → database query → hint incorporation → solution). Fine-tune GPT-OSS-120B via LoRA/QLoRA on these examples. This directly addresses the root cause identified by NVIDIA's AIMO-2 team: reasoning models cannot be prompted into novel behavioral patterns that conflict with their RL training.

## Conclusion

The model's behavior is not a bug — it is a predictable consequence of RL-based reasoning training that optimizes for correct answers over procedural compliance. The ReasonIF benchmark quantifies this at **<25% instruction compliance** across all frontier reasoning models. The most robust solution avoids the compliance problem entirely through host-side context injection (Tier 1), while API-level forcing (Tier 2) provides guaranteed tool-call execution when model-driven retrieval is required. Fine-tuning (Tier 3) is the proven solution for deep behavioral change, validated by AIMO-2's winning team, but requires the most engineering investment. The key insight across all evidence: **never rely on prompting alone to enforce procedural behavior in reasoning models** — use architectural and API-level mechanisms as your primary enforcement layer, with prompting as a supplementary signal.