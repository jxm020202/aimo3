# Competitive Intelligence
**Tags**: #competition #teams #strategy
**Source**: Scraped discussions (2026-03-02), 20 threads, 118 comments

## Key Intel

### GPT-OSS-120B is MoE (~5.1B active params)
Thread #679339. The "120B" label is total params. Only ~5.1B active at inference time.
Dense models (Qwen3.5-27B at 27B active) will be SLOWER despite lower nominal count.
This is why GPT-OSS-120B fits and runs fast on H100.

### Leading Team: SymPy Decoupling
Thread #635859 reply 13:
> "our pipeline was specifically engineered to ensure consistent outputs across multiple runs...
> By decoupling reasoning from execution via SymPy, we address the 5-digit precision requirement
> without relying on stochastic arithmetic."

Strategy: LLM reasons, translates to SymPy, SymPy computes deterministically. Reduces variance between dual runs.

### Reference Set is Unreliable
Thread #676458: "8/10 on reference -> only 6/50 on public LB."
Do not over-index on reference problem performance. Use broader test sets.

### Submission Failures Common
- "Notebook Inference Server Never Started" errors from slow model loading (#678800)
- Model loading can be 7x slower during peak times (around 0:00 UTC)
- Submission fails count against daily 1/day limit (#635859 reply 14)
- XSRF token issues common (#675789)

### Competitors Discussing
- Triton backend: slower than default in some experiences (#672978)
- B200 GPU: not actually available despite discussion title (#672978)
- Image support: no image input in AIMO3, only text problems (#674770)

## Public Notebook Configs (March 3 analysis)

| Notebook | Model | Attempts | ES | Temp | Key Differentiator |
|----------|-------|----------|---|------|-------------------|
| Top voted (120v) | GPT-OSS-120B | 8 | 4 | **0.99** | min_p=0.02, no schedule |
| Qwen3.5-9B (35v) | Qwen3.5-9B | 8 | 4 | 1.0 | **presence_penalty=1.5**, thinking mode |
| Qwen3-32B (14v) | Qwen3-32B | 4 | 2 | 0.7 | **workers=1** (sequential), max_tokens=16K/turn |

Key findings:
- Everyone uses entropy-weighted voting + TIR — no innovation in voting/selection
- Top notebook uses near-random temp (0.99) + min_p pruning instead of schedule
- Qwen3-32B notebook found parallel is 6x slower per stream — sequential better for dense models
- SGLang confirmed slower than vLLM for this use case (#676019)
- No one is doing MCTS, PRM, GenSelect, or multi-model ensemble publicly

## What We Don't Know
- What private teams (non-public notebooks) are doing
- Whether anyone has implemented MCTS or PRM secretly
- Whether the #1 team ("just public 44, all is luck") has any modifications
