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

### GenSelect (NVIDIA, AIMO2)
- Train a model to READ multiple solution candidates and SELECT the best one
- Outperforms majority voting because it can evaluate solution quality, not just answer frequency
- Key AIMO2 innovation from NemoSkills

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

### MCTS (Monte Carlo Tree Search)
- Tree search over reasoning paths
- MCTSr: integrates LLMs with MCTS for iterative refinement
- CMCTS: partitions action space (understand/reflect/code/summary) for diversity
- SCULPT: constraint-guided pruning
- rStar-Math: 58.8% → 90.0% on MATH benchmark
- **Gap**: Computationally expensive but H100s make it viable. Few public notebooks do this.

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
- The 44/50 baseline does early-stop if 4 agree, but doesn't reallocate saved compute

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

## Math AI Landscape (Beyond Kaggle)

- **AlphaProof/AlphaGeometry 2** (DeepMind): Gold at IMO 2025, uses formal theorem proving + neural
- **Gemini Deep Think**: Gold at IMO 2025
- **DeepSeek-R1**: GRPO training, strong math reasoning
- **MCTS + PRM combinations**: rStar-Math showed massive gains (58.8% → 90.0%)
- **FrontierMath benchmark**: Only ~25% solved by best models
- **Key trend**: Inference-time compute scaling (more thinking = better results) is the dominant paradigm
