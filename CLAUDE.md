# AIMO3 — AI Mathematical Olympiad Progress Prize 3

## Competition
- **Kaggle**: https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3
- **Prize**: $2.2M main + $110K extras. 1st: $262K. 47/50 bonus: $1.59M (unclaimed).
- **Deadline**: April 15, 2026 (entry by April 8)
- **Hardware**: H100 GPUs on Kaggle (free), up to 128 H100s for fine-tuning via Fields Model Initiative

## Task
- 110 original math problems (algebra, combinatorics, geometry, number theory)
- Difficulty: national olympiad to full IMO level
- 5-digit integer answers (0–99999)
- 50 public + 50 private test problems
- Private LB: submitted twice, penalized scoring (both correct=1, one=0.5, both wrong=0)
- All code/models/data must be open-sourced to qualify for prizes

## Project Structure
```
aimo3/
  baseline-44-50.ipynb    — Original 44/50 public notebook (GPT-OSS-120B, zero training)
  notebooks/              — Our working notebooks (pushed to Kaggle via API)
    kernel-metadata.json  — Kaggle push config
  data/                   — Competition data (need to accept rules first)
  scripts/                — Helper scripts
  research/               — Research notes, papers
```

## Workflow
1. Develop notebooks locally in `notebooks/`
2. Push to Kaggle: `kaggle kernels push -p notebooks/`
3. Check status: `kaggle kernels status jxm222/aimo3-solver`
4. Pull output: `kaggle kernels output jxm222/aimo3-solver -p output/`
5. GPU runs happen on Kaggle's H100s — no local GPU needed

## Current Baseline (44/50)
- **Model**: GPT-OSS-120B (117B total, 5.1B active MoE, Apache 2.0)
- **Serving**: vLLM with fp8 KV cache, gpu_memory_utilization=0.96
- **Inference**: 8 parallel attempts per problem, 16 Jupyter kernel sandboxes for TIR
- **Voting**: Entropy-weighted majority voting, early stop if 4 agree
- **Training**: ZERO — pure inference
- **Key config**: temperature=0.5, min_p=0.02, context=65536 tokens, turns=128

## Improvement Vectors (Not in baseline)
1. Process Reward Models (step-level verification)
2. MCTS over reasoning paths
3. Multi-model ensemble (GPT-OSS-120B + Qwen3-Next or DeepSeek-R1)
4. Problem-type routing (different strategies per math domain)
5. Formal verification (SymPy/Lean4)
6. Adaptive compute (more attempts on harder problems)
7. GenSelect (train model to read & rank solution candidates)
8. Self-reflection loops / answer verification step
9. Few-shot examples per problem type
10. SFT on tool-integrated reasoning traces

## Key Models
- **GPT-OSS-120B**: Best current model. 96.6% AIME 2024 w/ tools. MoE 128 experts, 4 active.
- **GPT-OSS-20B**: Faster variant, matches o3-mini
- **Qwen3-Next**: Strong reasoning, "thinking mode"
- **DeepSeek-R1 distills**: 7B-70B range, good for verification/ensemble

## Historical Context
- AIMO1 winner: 29/50 (Numina, DeepSeekMath-7B, two-stage SFT, SC-TIR N=48 M=4)
- AIMO2 winner: 34/50 (NemoSkills/NVIDIA, Qwen2.5-14B, SFT+DPO, GenSelect)
- AIMO2 solo competitors: 29-30/50 with NO fine-tuning (3rd-5th place)
- Current AIMO3 public best: 44/50 (GPT-OSS-120B, zero training, entropy voting)

## Kaggle CLI
- Username: jxm222
- API key: ~/.kaggle/kaggle.json
- Push: `kaggle kernels push -p notebooks/`
- Status: `kaggle kernels status jxm222/aimo3-solver`
