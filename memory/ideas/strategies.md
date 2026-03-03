# Strategies & Research

## Proven Techniques (Used by Winners)

### Tool-Integrated Reasoning (TIR)
- LLM generates interleaved reasoning + Python code
- Code executed in sandbox, output fed back to model
- Enables self-correction through execution feedback
- Used by ALL AIMO winners. Non-negotiable baseline.

### Self-Consistency (SC-TIR)
- Generate N candidate solutions per problem
- Each candidate goes through M rounds of code gen → execute → self-correct
- Majority vote on final numerical answer
- Numina: N=48, M=4. "after exams": N=120-160.
- More candidates = more robust, but diminishing returns + compute cost

### Majority Voting Variants
- **Simple majority**: Count most frequent answer. Basic but effective.
- **Entropy-weighted**: Weight votes by model confidence (lower entropy = higher weight). Used in 44/50 baseline.
- **Reward-model weighted**: Train/use a reward model to weight each solution. CMU-MATH (AIMO1 2nd place) used this, doubled solve rate from 2/10 to 4/10.
- **CISC (Confidence-Improved Self-Consistency)**: 46% reduction in samples needed for same accuracy ([arxiv 2502.06233](https://arxiv.org/pdf/2502.06233))
- **Self-Certainty Based Voting**: Borda count-inspired ranking by confidence, consistently outperforms self-consistency
- **RASC**: Score both answer AND reasoning path quality

### GenSelect (NVIDIA, AIMO2)
- Train a model to READ multiple solution candidates and SELECT the best one
- Outperforms majority voting because it can evaluate solution quality, not just answer frequency
- Key AIMO2 innovation from NemoSkills
- **Concrete numbers**: OpenMath-Nemotron-14B went from 73.7% pass@1 to 86.7% under GenSelect on AIME24 (+13%)
- **No-training variant**: Can use GPT-OSS-120B itself as untrained GenSelect judge (generate 16-32 solutions, summarize each, ask model to pick best). Effectiveness uncertain without fine-tuning.
- GenSelect becomes unstable beyond 32 generations (solutions don't fit in one prompt)
- NemoSkills total training data: 5.5M samples (3.2M CoT + 1.7M TIR + 566K GenSelect)

### DPO (Direct Preference Optimization)
- Used by AIMO2 teams to reduce output length while maintaining quality
- Shorter outputs = faster inference = more candidates in time budget
- Applied after SFT

## Unexploited Opportunities (Not in Public Notebooks)

### Process Reward Models (PRMs)
- Verify each reasoning STEP, not just final answer
- ThinkPRM: verbalized step-wise verification with CoT, works with 1% of PRM800K labels
- R-PRM: reasoning-driven process reward modeling
- Could catch errors that slip through majority voting
- **Gap**: Most public AIMO3 notebooks use outcome-level voting only
- **Available models**:
  - [ThinkPRM-14B](https://github.com/mukhal/ThinkPRM) — open-source verbalized CoT verifier, outperforms discriminative PRMs trained on 100x more data. ~8GB in 4-bit.
  - [Qwen2.5-Math-RM-72B](https://github.com/QwenLM/Qwen2.5-Math) — dedicated math reward model, too large to coexist with GPT-OSS-120B
  - ThinkPRM-1.5B — smallest variant, ~1GB in 4-bit, could coexist with GPT-OSS-120B easily
- **Feasibility**: GPT-OSS-120B (~45GB MXFP4) + ThinkPRM-14B (~8GB 4-bit) = ~53GB on 80GB H100. Tight but possible. Sequential loading (generate all, then score) is safer.

### MCTS (Monte Carlo Tree Search)
- Tree search over reasoning paths
- MCTSr: integrates LLMs with MCTS for iterative refinement
- CMCTS: partitions action space (understand/reflect/code/summary) for diversity. 83.4% with 7B model surpassing 72B baselines ([Springer](https://link.springer.com/article/10.1007/s10489-025-07044-6))
- SCULPT: constraint-guided pruning
- rStar-Math: 58.8% → 90.0% on MATH benchmark with Qwen2.5-Math-7B ([arxiv 2501.04519](https://arxiv.org/abs/2501.04519))
- Requires PRM (ThinkPRM) for step-level evaluation during search
- **Gap**: Computationally expensive but H100s make it viable. Few public notebooks do this.
- **Implementation**: Break problem into steps → generate multiple candidate next-steps → PRM evaluates → expand promising, prune bad → repeat. TIR sandbox already available for code execution at each step.

### Multi-Model Ensemble
- Use GPT-OSS-120B for generation + different model for verification
- Different models have different error modes → diversity catches more
- Could route easy problems to fast model, hard problems to strong model
- **Gap**: Everyone using single model currently

### Problem-Type Routing
- Different strategies for algebra vs combinatorics vs geometry vs number theory
- One-size-fits-all prompting leaves performance on table
- Could classify problem first, then apply domain-specific prompt/strategy
- **Gap**: No public notebook does this

### Formal Verification
- SymPy for algebraic verification
- Lean4/Isabelle for formal proofs
- Mathematical certainty > statistical confidence
- Could be used as a filter: only accept solutions that verify symbolically
- **Gap**: Underexplored in competition context

### Adaptive Compute
- Spend more inference budget on harder problems, less on easier ones
- Early stop is currently broken (see `ideas/parallelism-and-early-stop.md`) — all attempts run to completion
- Adaptive batched execution (proposed for v24) would enable real early stop and compute reallocation
- [DiffAdapt](https://arxiv.org/html/2510.19669v2): 82.3% of problems benefit from "Easy" strategy (fewer samples)
- With batched execution: easy problems use 1 wave (~3 min), hard get 3 waves (~10 min)

### Self-Reflection / Answer Verification
- After generating an answer, ask the model to verify it
- "Check: does this answer satisfy all constraints in the problem?"
- Can catch obvious errors without needing a separate reward model
- Simple to implement, surprisingly effective

### Few-Shot Examples
- Provide worked examples in the prompt for each problem type
- Could improve performance on problem types the model struggles with
- Balance: more examples = less context for reasoning

### Sandbox Libraries (RESEARCH NEEDED)

Current sandbox preloads: `math`, `numpy`, `sympy`, `itertools`, `collections`, `mpmath`, `functools`, `fractions`

Research needed — which are available in Kaggle docker or installable from wheels?
- **`gmpy2`**: GMP-backed arbitrary precision, critical for number theory
- **`networkx`**: Graph theory (combinatorics often reduces to graphs)
- **`scipy.special`**: Fast combinatorial functions (comb, perm)
- **`galois`**: Finite field arithmetic

#### Prompt Engineering for Efficient Code — PARTLY DONE
Already added to v23:
- bigint hint: `pow(base, exp, mod)` for large exponents
- 9 code robustness rules including modular arithmetic, feasibility checks
- Efficiency directive: skip Python for trivial problems

Still could add:
- "For combinatorics, use generating functions or recurrences rather than brute-force enumeration."
- Negative examples of common hallucinated APIs

## What Doesn't Work (Failed in Past Competitions)

- **RL training (PPO, RLOO)**: Numina tried it, promising reward curves but zero performance gain
- **Model merging (DARE, TIES, WARP)**: Regressions every time (Numina)
- **Larger models on limited hardware**: Slow inference → fewer candidates → worse scores
- **Pure CoT without code execution**: Capped at 8/50 (Numina Stage 1 only)
- **Single-turn code generation (MMOS)**: Capped at 16/50

## The 44 → 47 Gap

The remaining 6 problems are likely the hardest IMO-level ones. GPT-OSS-120B gets 0/6 on hard reference problems. Two possible paths:

1. **Stronger model**: DeepSeek-v3.1-terminus (671B) solves 9/10 reference problems but may not fit on H100
2. **Smarter reasoning**: MCTS, formal verification, multi-model ensemble, problem routing — engineer around the model's limitations

Path 2 is more realistic for us given hardware constraints.

## Inference Engine: SGLang vs vLLM — DEAD IDEA

- SGLang delivers ~29% higher throughput than vLLM on general benchmarks
- **But**: Clarifai benchmark for GPT-OSS-120B showed vLLM ahead
- **And**: Discussion #676019 confirms SGLang slightly slower for this exact use case
- **Verdict**: Stay on vLLM. Don't waste time testing.

## Priority Queue (as of v23, updated with notebook analysis)

| Priority | Technique | Expected Gain | Status |
|----------|-----------|--------------|--------|
| 1 | Adaptive batched execution | +1-2 problems (time savings) | Proposed — see `parallelism-and-early-stop.md` |
| 2 | Better extraction (reduce 46% None rate) | +0.5-1 | Partly done (v23 fallbacks), more needed |
| 3 | Test `temp=0.99 + min_p=0.02` vs schedule | +0-1 (simplification) | Not started — top notebook uses this |
| 4 | `presence_penalty` for repetition breaking | +0-0.5 | Not started — Qwen3.5 notebook uses 1.5 |
| 5 | Per-turn token cap (`max_tokens_per_turn`) | +0-0.5 | Not started — prevents thinking runaway |
| 6 | Self-verification loop | +0.5-1 | Not started |
| 7 | GenSelect (untrained, use GPT-OSS as judge) | +1-3 | Not started |
| 8 | ThinkPRM-14B/1.5B as verifier | +1-3 | Not started — needs memory budget analysis |
| 9 | MCTS with step-level search | +1-4 | Not started — high complexity |

**Note**: Gains are NOT additive. Stacking top 3-4 techniques could realistically push 44→46-47.

## Notebook Landscape (from March 3 analysis)

All public notebooks use the same pattern: parallel attempts + entropy-weighted voting + TIR sandbox. Nobody is doing MCTS, PRMs, GenSelect, or multi-model ensemble publicly.

| Notebook | Model | Attempts | ES | Temp | Special |
|----------|-------|----------|---|------|---------|
| Top voted (120v) | GPT-OSS-120B | 8 | 4 | 0.99 | min_p=0.02, no schedule |
| Qwen3.5-9B (35v) | Qwen3.5-9B | 8 | 4 | 1.0 | presence_penalty=1.5, thinking mode |
| Qwen3.5-27B (18v) | Qwen3.5-27B | — | — | — | Quantization recipe only |
| Qwen3-32B (14v) | Qwen3-32B | 4 | 2 | 0.7 | workers=1, max_tokens=16K/turn, thinking |
| **Ours** | GPT-OSS-120B | **16** | **5** | **schedule** | Temp schedule, GPU monitor, retry on None |

Key takeaway: We have 2x more attempts than anyone else. Our main differentiator.

## Second Model Candidates (for ensemble/verification)

- **GPT-OSS-20B**: Smaller, faster, matches o3-mini on competition math. Good for quick verification.
- **DeepSeek-R1-Distill-Qwen-8B**: Strong math reasoning, efficient
- **ThinkPRM-14B/1.5B**: Dedicated verifier
- All must be released before March 15, 2026 model cutoff.

## Competition Intelligence

Moved to `memory/discussions/competitive-intel.md`. Key takeaway: inference engineering alone gets within 4-5 problems of trained models in past competitions.

## Key Research Sources

- [AIMO-2 Winning Solution (NemoSkills)](https://arxiv.org/abs/2504.16891)
- [rStar-Math MCTS](https://arxiv.org/abs/2501.04519)
- [ThinkPRM Paper](https://arxiv.org/abs/2504.16828) / [GitHub](https://github.com/mukhal/ThinkPRM)
- [CISC Voting](https://arxiv.org/pdf/2502.06233)
- [DiffAdapt Adaptive Reasoning](https://arxiv.org/html/2510.19669v2)
- [Test-Time Compute Scaling](https://arxiv.org/html/2408.03314v1)
- [GPT-OSS-120B Model Card](https://arxiv.org/abs/2508.10925)

## Math AI Landscape (Beyond Kaggle)

- **AlphaProof/AlphaGeometry 2** (DeepMind): Gold at IMO 2025, uses formal theorem proving + neural
- **Gemini Deep Think**: Gold at IMO 2025
- **DeepSeek-R1**: GRPO training, strong math reasoning
- **MCTS + PRM combinations**: rStar-Math showed massive gains (58.8% → 90.0%)
- **FrontierMath benchmark**: Only ~25% solved by best models
- **Key trend**: Inference-time compute scaling (more thinking = better results) is the dominant paradigm
