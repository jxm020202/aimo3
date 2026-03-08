# Strategies & Research

## Implemented Techniques

### Tool-Integrated Reasoning (TIR)
- LLM generates interleaved reasoning + Python code, executed in sandbox
- Used by ALL AIMO winners. Non-negotiable baseline.

### Self-Consistency (SC-TIR)
- 24 parallel attempts, majority vote on final answer
- Entropy-weighted voting for confidence

### GenSelect (NVIDIA, AIMO2) — IMPLEMENTED
- Dual judges: 7B trained (OpenReasoning-Nemotron-7B-BNB4) + 120B zero-shot
- Streaming summarization during R1 (NVIDIA's pipeline)
- 3-way decision: majority + 7B + 120B
- See `genselect-and-summaries.md` for full details

### Wave 1 Classifier — IMPLEMENTED
- 42 agents classify problem difficulty/category
- Budget pool: 6000s total, distributed per problem

## Unexploited Opportunities

### Process Reward Models (PRMs)
- Verify each reasoning STEP, not just final answer
- ThinkPRM-14B: ~8GB in 4-bit, could coexist with 120B
- GPT-OSS-120B (~45GB MXFP4) + ThinkPRM-14B (~8GB 4-bit) = ~53GB on 80GB H100
- Status: NOT STARTED

### MCTS (Monte Carlo Tree Search)
- rStar-Math: 58.8% → 90.0% on MATH benchmark with 7B model
- Needs PRM for step-level evaluation
- High complexity. Status: NOT STARTED

### Strategy Retrieval Bank (1000-problem RAG)
- 1000 hard problems with solving strategies + key insights
- TF-IDF matching in numpy (~20 lines), inject top 3-5 matched strategies (~240 tokens)
- Primary target: confident-wrong problems where model consistently uses wrong approach
- Status: IDEA — not started

## What Doesn't Work
- RL training (PPO, RLOO): promising reward curves, zero performance gain
- Model merging (DARE, TIES, WARP): regressions every time
- Larger models on limited hardware: slow inference → fewer candidates → worse
- Pure CoT without code execution: capped at 8/50
- SGLang vs vLLM: vLLM ahead for GPT-OSS-120B specifically
- Wave-based batching: 2x slower than all-parallel (707 min vs 313 min)
- Early stop: broken, all attempts already on GPU when stop fires

## Key Research Sources
- [AIMO-2 NemoSkills](https://arxiv.org/abs/2504.16891)
- [GenSelect Paper](https://arxiv.org/abs/2507.17797)
- [rStar-Math MCTS](https://arxiv.org/abs/2501.04519)
- [ThinkPRM](https://github.com/mukhal/ThinkPRM)
- [GPT-OSS-120B Model Card](https://arxiv.org/abs/2508.10925)
