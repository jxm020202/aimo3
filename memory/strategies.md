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
- Current approaches use uniform N candidates per problem
- If model is confident (low entropy across candidates), stop early and reallocate compute
- The 44/50 baseline does early-stop if 4 agree (we raised to 5), but doesn't reallocate saved compute
- [DiffAdapt](https://arxiv.org/html/2510.19669v2): 82.3% of problems benefit from "Easy" strategy (fewer samples)
- With 50 problems in 9 hours (~10.8 min/problem), easy problems finish in ~3 min → gives 15+ min per hard problem
- Could allocate 16-32 attempts on hardest problems instead of uniform 8

### Self-Reflection / Answer Verification
- After generating an answer, ask the model to verify it
- "Check: does this answer satisfy all constraints in the problem?"
- Can catch obvious errors without needing a separate reward model
- Simple to implement, surprisingly effective

### Few-Shot Examples
- Provide worked examples in the prompt for each problem type
- Could improve performance on problem types the model struggles with
- Balance: more examples = less context for reasoning

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

## Inference Engine: SGLang vs vLLM

- SGLang delivers ~29% higher throughput than vLLM on H100 (16,200 vs 12,500 tok/s general benchmarks) — [source](https://blog.premai.io/vllm-vs-sglang-vs-lmdeploy-fastest-llm-inference-engine-in-2026/)
- However, [Clarifai benchmark](https://www.clarifai.com/blog/comparing-sglang-vllm-and-tensorrt-llm-with-gpt-oss-120b) specifically for GPT-OSS-120B showed vLLM ahead
- **Verdict**: Test both. If SGLang wins, 29% more generations = ~29% more candidates per problem.

## Prioritized Roadmap (6 weeks remaining)

### Phase 1: Low-Hanging Fruit (Week 1)
| Technique | Expected Gain | Complexity |
|-----------|--------------|------------|
| Adaptive compute allocation | +1-2 problems | Low |
| Self-verification loop | +0.5-1 | Low |
| Problem-type routing | +0.5-1 | Low |
| Better voting (CISC) | +0.5-1 | Low |

### Phase 2: Architecture Changes (Weeks 2-3)
| Technique | Expected Gain | Complexity |
|-----------|--------------|------------|
| GenSelect (untrained) | +1-3 | Medium |
| ThinkPRM integration | +1-3 | Medium-High |

### Phase 3: Advanced (Weeks 4-5)
| Technique | Expected Gain | Complexity |
|-----------|--------------|------------|
| MCTS with step-level search | +1-4 | High |
| Multi-model ensemble | +1-2 | Medium |

### Phase 4: Polish (Week 6)
- Optimize time budget allocation across 50 problems
- SGLang vs vLLM benchmarking
- Final reference problem testing

**Note**: Gains are NOT additive — significant overlap. Stacking top 3-4 techniques could realistically push 44→46-47.

## Second Model Candidates (for ensemble/verification)

- **GPT-OSS-20B**: Smaller, faster, matches o3-mini on competition math. Good for quick verification.
- **DeepSeek-R1-Distill-Qwen-8B**: Strong math reasoning, efficient
- **ThinkPRM-14B/1.5B**: Dedicated verifier
- All must be released before March 15, 2026 model cutoff.

## Competition Intelligence

- AIMO3 current landscape: Multiple notebooks at 43-44/50 using GPT-OSS-120B
- [seshurajup's "Agentic Solver"](https://www.kaggle.com/code/seshurajup/aimo-3-gpt-oss-120b-agentic-solver) uses agentic approach
- Nobody has publicly cracked 45+ yet
- The 47/50 bonus ($1.59M) has **never been claimed** across any AIMO competition
- **AIMO1**: Winner 29/50, 3rd place 21/50 with ZERO training (just 120-160 candidates + smart filtering)
- **AIMO2**: Winner 34/50, 3rd-5th place 29-30/50 with ZERO training
- **Pattern**: Inference engineering alone gets within 4-5 problems of trained models

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
