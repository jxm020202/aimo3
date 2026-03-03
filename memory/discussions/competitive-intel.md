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

## What We Don't Know
- What specific voting/selection method top teams use
- Whether anyone has implemented MCTS or PRM
- Exact model configurations of top LB entries
- Whether anyone uses multi-model ensemble
