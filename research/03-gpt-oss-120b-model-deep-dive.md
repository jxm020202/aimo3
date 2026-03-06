# GPT-OSS-120B: OpenAI's open-weight reasoning model

**GPT-OSS-120B is OpenAI's most powerful open-weight language model — a 117-billion-parameter Mixture-of-Experts Transformer that activates only 5.1 billion parameters per token, fits on a single 80 GB GPU, and rivals OpenAI's own o4-mini on core reasoning benchmarks.** Released on August 5, 2025, under the permissive Apache 2.0 license, it marks OpenAI's first open-weight language model since GPT-2 in 2019. The model was trained using reinforcement learning techniques derived from OpenAI's frontier o3 system, trained on **2.1 million H100-hours** of compute, and natively supports configurable reasoning effort, tool use, and a 128K-token context window. It represents a significant strategic pivot by OpenAI toward open-source, arriving in a landscape already shaped by Meta's LLaMA, DeepSeek R1, and Qwen 3 — and it competes aggressively on the efficiency-performance frontier, though it trails larger open models on composite intelligence scores.

---

## Who built it, and why it matters

OpenAI developed and released GPT-OSS-120B alongside a smaller sibling, GPT-OSS-20B (21B total parameters, 3.6B active). The stated goals were to **democratize access to reasoning-capable AI** and provide developers with a production-grade open model for on-premises deployment, fine-tuning, and commercial use without copyleft restrictions. The release came with an extensive partner ecosystem — Azure, Hugging Face, vLLM, Ollama, llama.cpp, LM Studio, AWS, NVIDIA NIM, Groq, OpenRouter, and more — all supporting the model at launch.

The motivations were both ideological and competitive. OpenAI framed GPT-OSS as advancing open science, but the release also responded to competitive pressure from Meta's LLaMA ecosystem, DeepSeek's R1, and Alibaba's Qwen 3, all of which had captured significant open-source mindshare. GPT-OSS-120B's key differentiator is its combination of **frontier-class reasoning** (near o4-mini performance) with **extreme deployment efficiency** (single-GPU inference via MXFP4 quantization). The model comes with full chain-of-thought visibility, three adjustable reasoning levels, and native agentic capabilities including function calling, web browsing, and Python code execution.

---

## Architecture: 128 experts, 4 active, and a 2,880-dimensional residual stream

GPT-OSS-120B is an autoregressive MoE Transformer with **36 decoder layers**, a residual stream dimension of **2,880**, and **128 experts per MoE layer** with top-4 routing (softmax applied after top-k selection). This extreme sparsity — only ~3.1% of experts active per token — is what enables the model to deliver competitive performance while activating just 5.1B of its 116.8B total parameters.

| Component | Specification |
|---|---|
| Total parameters | 116.83B (marketed as ~120B) |
| Active parameters per token | **5.13B** |
| Transformer layers | 36 |
| Hidden dimension | 2,880 |
| Experts per MoE layer | 128 (top-4 routing) |
| Attention heads | 64 query heads, 8 KV heads (GQA, group size 8) |
| Head dimension | 64 |
| Positional encoding | RoPE with YaRN extension |
| Context length | **131,072 tokens (128K)** |
| Tokenizer | o200k_harmony (BPE, 201,088 vocab) |
| Checkpoint size | 60.8 GiB (MXFP4) |
| Activation function | SwiGLU (with "unconventional" clamping and residual connection) |
| Normalization | RMSNorm (pre-normalization) |

The attention mechanism alternates between **dense full-context attention** and **locally banded sparse attention** with a 128-token sliding window (ratio 1:1, every other layer). This is reminiscent of GPT-3's sparse attention patterns. A novel feature is **learned attention sinks** — each attention head has a learned bias in the softmax denominator, allowing the model to effectively "attend to nothing" when appropriate, addressing the known problem of spurious attention to semantically meaningless tokens.

The MoE weights (which constitute **90%+ of total parameters**) were post-trained with **MXFP4 quantization** — a quantization-aware training approach, not post-hoc compression. Weights are stored at ~4.25 bits per parameter in the OCP Microscaling Formats specification, with paired `tensor.blocks` (FP4 values packed as uint8) and `tensor.scales` (block-level scaling factors). All non-MoE weights (attention layers, embeddings) remain in BF16. All official benchmark evaluations were performed with this same MXFP4 quantization.

---

## Training: reinforcement learning from o3, trillions of tokens, and the Harmony format

### Pre-training and data

The model was pre-trained on a **text-only, mostly English** dataset of **"trillions of tokens"** with a focus on STEM, coding, and general knowledge. OpenAI has **not disclosed specific training data sources** — no named datasets, no composition ratios, no data provenance details. The knowledge cutoff is **June 2024**. Safety filtering during pre-training reused CBRN (Chemical, Biological, Radiological, Nuclear) content filters from GPT-4o. Total pre-training compute was **2.1 million H100-hours** using PyTorch with expert-optimized Triton kernels and FlashAttention.

### Post-training and reasoning

Post-training used **"similar CoT RL techniques as OpenAI o3"** — reinforcement learning that teaches chain-of-thought reasoning and tool use across coding, math, science, and general knowledge domains. OpenAI states the models were trained using "a mix of reinforcement learning and techniques informed by OpenAI's most advanced internal models, including o3 and other frontier systems." Whether this involved direct knowledge distillation (e.g., synthetic data generated by o3) or purely technique transfer remains undisclosed. The RL training gives the model a "personality similar to models served in first-party products like ChatGPT."

### The Harmony response format

GPT-OSS models **require** the Harmony chat format — a custom protocol using special tokens to delineate message boundaries, enforce a role hierarchy (System > Developer > User > Assistant > Tool), and separate output into **three channels**: `analysis` (chain-of-thought reasoning, not intended for end users), `commentary` (function/tool calling), and `final` (user-facing answers). The model was trained exclusively on this format, and using it without Harmony will produce broken outputs. OpenAI open-sourced both the Harmony renderer (Python and Rust implementations) and the o200k_harmony tokenizer.

The configurable reasoning effort (low, medium, high) is set via the system prompt (e.g., `"Reasoning: high"`) and controls chain-of-thought length. The impact is dramatic: on **AIME 2025**, accuracy ranges from **50.4% at low effort to 92.5% at high effort** — a near-doubling of performance at the cost of increased latency and token usage.

---

## Benchmark performance reveals a strong but uneven competitor

GPT-OSS-120B occupies a distinctive niche: it is **the most capable model that runs on a single H100 GPU**, but it does not top every leaderboard. Its strengths are concentrated in mathematical reasoning, knowledge tasks, and health-related queries, while it has notable weaknesses in certain coding benchmarks and tool use.

### Against OpenAI's own models

At high reasoning effort, GPT-OSS-120B **surpasses o3-mini** broadly and achieves **near-parity with o4-mini** on core reasoning, while **exceeding o4-mini** on competition math (AIME 2024: **96.6%**, AIME 2025: **97.9%** with tools), HealthBench, and TauBench Retail (**67.8%**). It reaches **90.0% on MMLU** and **80.9% on GPQA Diamond**. However, it trails the full o3 model and significantly lags proprietary frontier models like GPT-5 on coding tasks (SWE-bench Verified: **62.4%** vs. GPT-5's 74.9%).

### Against open-weight competitors

The competitive picture is nuanced. GPT-OSS-120B dominates on math but faces stiff competition from larger models elsewhere:

- **DeepSeek R1 (671B total, 37B active):** GPT-OSS-120B wins decisively on math (AIME 2024: 96.6% vs. ~87.5%) but trails on composite intelligence scores (Artificial Analysis Index: **33 vs. 59**) and some coding benchmarks. DeepSeek R1 requires roughly 10× more memory.
- **Qwen3 235B:** Scores significantly higher on the Artificial Analysis Intelligence Index (**64 vs. 33**) and edges ahead on function calling (BFCL-v3: 71.9% vs. ~67-68%), but trails on math and MMLU. Qwen3 is ~2× larger.
- **GLM-4.5 (Zhipu):** Dominates on agentic/tool-use tasks (TauBench Retail: **79.7%** vs. 67.8%, BFCL-v3: **77.8%**) but trails on knowledge and math benchmarks. Requires multi-GPU clusters.
- **Kimi K2 (Moonshot):** GPT-OSS-120B dominates on reasoning and math but Kimi K2 edges ahead on SWE-bench (65.8% vs. 62.4%) and some agentic tasks.
- **LLaMA models:** GPT-OSS-120B significantly outperforms LLaMA 3.3 70B and generally exceeds LLaMA 4 variants on reasoning, while offering better inference speed due to MoE architecture (up to **13× faster** token generation). LLaMA 4 models are multimodal, which GPT-OSS is not.
- **Mistral, Falcon, Command R+:** Generally considered a tier below the frontier open models listed above. GPT-OSS-120B significantly exceeds these.

An independent academic evaluation (arXiv 2508.12461, "Is GPT-OSS Good?") found that while GPT-OSS-120B shows relative strength in code generation, it delivers "mid-tier overall performance within the current open-source landscape" when compared against models ranging from 14.7B to 235B parameters. The same study found, surprisingly, that GPT-OSS-20B outperformed 120B on HumanEval and MMLU in unquantized testing. On the Aider Polyglot coding benchmark, GPT-OSS-120B scored just **44.4%**, well behind GPT-5 (88.0%), Gemini 2.5 Pro (83.1%), and DeepSeek V3.1 (76.3%).

Cost-wise, GPT-OSS-120B is remarkably efficient: median API pricing of **$0.15/$0.60 per million input/output tokens** — roughly **90% cheaper than o3** — with output speeds reaching **260-291 tokens/second** (or up to 2,224 t/s on Cerebras hardware).

---

## Known issues: hallucinations, verbosity, and safety gaps

### Hallucination is the headline weakness

OpenAI's own evaluations reveal alarming hallucination rates. On **SimpleQA**, GPT-OSS-120B shows a ~**91% hallucination rate** among attempted answers — one of the highest figures reported for a major model on this benchmark. On **PersonQA** (questions about people), the hallucination rate is ~**49%**. These figures exceed o4-mini's rates (75% SimpleQA, 36% PersonQA). OpenAI explicitly warns that chain-of-thought outputs "can contain hallucinated content, including language that does not reflect OpenAI's standard safety policies" and should not be shown to end users.

### Safety vulnerabilities materialized quickly

A Promptfoo security audit reported only a **51.2% pass rate** across 50+ vulnerability tests, finding 3 critical and 5 high-severity security issues. Top vulnerabilities included Divergent Repetition (100% exploitation rate), ASCII Smuggling (100%), and PII via Direct Exposure (97.78%). Security researchers reported successful jailbreaks **within 4-6 hours of release**. OpenAI acknowledges this as inherent to open-weight models: "determined attackers could fine-tune them to bypass safety refusals or directly optimize for harm." Indeed, an uncensored community variant (**ArliAI/gpt-oss-120b-Derestricted**) appeared on HuggingFace using abliteration techniques. On instruction hierarchy tests, GPT-OSS-120B underperforms o4-mini on system prompt extraction resistance (0.832 vs. 0.993).

### Other documented limitations

The model is **text-only** with no multimodal capabilities — a significant gap versus competitors like LLaMA 4, Gemini, and GPT-4o. It is notoriously **verbose**, generating **78 million tokens** during one standardized evaluation versus a median of 7 million for comparable models. The strict dependency on the Harmony chat format means the model produces broken output without proper formatting. Community developers discovered complications with the MXFP4 weight storage format (stored as `nn.Parameter` rather than `nn.Linear`), which complicated integration with standard quantization tools. OpenAI's Preparedness Framework adversarial fine-tuning evaluation found the model stays below "High" capability thresholds for biological, chemical, cyber, and AI self-improvement risks — even when adversarially fine-tuned. This was reviewed and confirmed by external experts (METR, SecureBio, and Daniel Kang).

---

## Fine-tuning ecosystem and community variants

GPT-OSS-120B can be fine-tuned on **a single H100 node** (65 GB VRAM for QLoRA, 210 GB for full BF16 LoRA). The community has rapidly built tooling around it:

- **Unsloth** is the leading fine-tuning tool, offering QLoRA at 65 GB VRAM with claims of 1.5× faster training and 70% less VRAM. Recommended LoRA config: r=16, alpha=32, targeting all projection layers. Unsloth also supports GRPO reinforcement learning.
- **Baseten + Axolotl** provides multi-node H100 fine-tuning recipes using a dequantized base model.
- **AWS SageMaker** offers official guides using HuggingFace TRL with DeepSpeed ZeRO-3.
- OpenAI published an official fine-tuning cookbook demonstrating LoRA fine-tuning of the 20B variant for multilingual reasoning.

Quantized variants proliferate across HuggingFace: **ggml-org/gpt-oss-120b-GGUF** (73 quantized variants, 363K+ monthly downloads), Unsloth GGUFs, and bartowski community quants ranging from Q2_K (~66 GB) to Q8_0 (~124 GB). For Apple Silicon users, MLX versions are available in 6-bit, 8-bit, and BF16 formats, requiring 64-96 GB unified memory for the 120B model. Official safety-specialized variants (**gpt-oss-safeguard-120b** and **-20b**) were released in October 2025 for content moderation use cases.

---

## Running GPT-OSS-120B on Kaggle

Kaggle's free H100 GPU access makes it one of the most accessible platforms for running GPT-OSS-120B. The model has been most prominently used in the **AIMO 3 (AI Mathematical Olympiad - Progress Prize 3)** competition, with multiple public notebooks demonstrating full inference pipelines:

- **"AIMO 3 Baseline - GPT OSS 120B"** by takuji — competition baseline
- **"⚡️AIMO 3 - GPT OSS 120B [~3hours wow H100]⚡️"** by seshurajup — demonstrates full inference within ~3 hours on a single Kaggle H100
- **"AIMO 3 | GPT-OSS-120B (with tools)"** by andreasbis — leverages the model's native tool-use capabilities for agentic math solving
- **"launch-gpt-oss-120b-in-6mins"** by threerabbits — quick-start deployment guide

For Kaggle integration, the model's native MXFP4 format requires no additional quantization on H100 hardware. The recommended serving framework is vLLM with the special GPT-OSS wheel (`vllm==0.10.1+gptoss`). Alternatively, the Transformers pipeline automatically handles the Harmony format. For competitions, tuning the reasoning effort level is the simplest way to balance accuracy against Kaggle's GPU time limits — low effort for fast coverage, high effort for difficult problems.

---

## Practical strategies for maximizing performance

The most impactful "low-hanging fruit" for GPT-OSS-120B performance falls into five categories, ordered from easiest to most involved:

**Reasoning effort tuning** delivers the largest marginal gain for zero effort. On AIME 2025, switching from low to high reasoning nearly doubles accuracy (50.4% → 92.5%). For most applications, start with medium and escalate to high only for complex queries. DataRobot's evaluation found that **GPT-OSS-20B at low thinking effort** often matches or beats **120B at high thinking effort** on cost-adjusted metrics — making intelligent routing between the two models a powerful optimization.

**Prompting best practices** include using the Harmony format's role hierarchy (Developer messages for system-level instructions, User messages for queries), keeping prompts concise and high-level rather than over-specifying step-by-step, and setting temperature=1.0 and top_p=1.0 as OpenAI recommends. For structured extraction tasks, lower temperatures (0.1-0.3) may help.

**RAG integration** exploits the 128K context window effectively. Optimal performance comes from 3-6 highly relevant passages rather than flooding the context. RAG significantly reduces the model's hallucination tendency by grounding answers in retrieved evidence. Enforce JSON schemas for structured outputs and implement retry logic for parse failures.

**Inference acceleration** through speculative decoding (using GPT-OSS-20B as a draft model to propose tokens verified by 120B), continuous batching, and KV cache quantization can dramatically improve throughput. Groq delivers up to 2,224 tokens/second using its TruePoint Numerics approach.

**Domain-specific fine-tuning** via QLoRA on a single H100 (65 GB VRAM with Unsloth) enables adaptation to specialized use cases. Key considerations: mix chain-of-thought and direct-answer examples to preserve reasoning ability, use the dequantized base model for training when possible, and note that most inference frameworks currently require merging LoRA adapters into the base model before serving.

---

## Conclusion

GPT-OSS-120B is a genuinely significant release that fundamentally changes the economics of deploying reasoning-capable AI. Its MoE architecture delivers what amounts to a 5B-parameter inference cost with 120B-parameter knowledge, fitting frontier-class reasoning into a single GPU. The model's **97.9% AIME 2025 score** with tools and **90% MMLU** demonstrate that OpenAI's RL distillation from o3 transfers remarkably well to an open-weight format. However, the model's weaknesses are equally real: **91% SimpleQA hallucination rate**, text-only limitations in a multimodal world, extreme verbosity, and rapid jailbreak susceptibility inherent to open weights. Composite intelligence indices from Artificial Analysis rank it below DeepSeek R1 and Qwen3 235B — both significantly larger models — suggesting that OpenAI optimized aggressively for efficiency over raw capability. For practitioners, the highest-impact optimization is not fine-tuning the 120B model itself, but rather implementing intelligent routing between the 20B and 120B variants based on query complexity, which DataRobot's analysis suggests can match high-effort 120B performance at a fraction of the cost.