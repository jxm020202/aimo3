# Analyzed Solutions

## Our Baseline: 44/50 Public LB (nihilisticneuralnet)

**Source**: `baseline-44-50.ipynb` in project root
**Training**: ZERO — pure inference on off-the-shelf model
**Score**: 44/50 public leaderboard

### Architecture
- **Model**: GPT-OSS-120B loaded from `/kaggle/input/gpt-oss-120b/transformers/default/1`
- **Serving**: vLLM with fp8 KV cache (`kv_cache_dtype='fp8_e4m3'`), `gpu_memory_utilization=0.96`
- **Inference**: 8 parallel attempts per problem
- **Code execution**: 16 Jupyter kernel sandboxes for Tool-Integrated Reasoning
- **Voting**: Entropy-weighted majority voting
- **Early stop**: If 4 attempts agree on same answer, stop early

### Key Config
```
temperature = 0.5
min_p = 0.02
context_tokens = 65536
attempts = 8
workers = 16 (Jupyter kernels)
turns = 128 (max reasoning steps per attempt)
```

### What It Does NOT Have
- No tree-of-thought / MCTS
- No self-reflection or answer verification loop
- No problem classification / routing
- No GenSelect (reading multiple solutions to pick best)
- No few-shot examples
- No multi-model ensemble
- No formal verification (SymPy/Lean)
- No Process Reward Model
- No fine-tuning of any kind

---

## AIMO1 Winner: Project Numina (29/50)

**Model**: DeepSeekMath-7B-Base → full fine-tuned
**Prize**: $131,072 (1st place)

### Training Recipe
- **Stage 1 (CoT SFT)**: Hundreds of thousands of math problems. Sources: Chinese high school exams, US olympiad, international olympiad, online PDFs. OCR'd, translated, reformatted into Chain-of-Thought. Learning rate 2e-5, batch 32, block 2048, 3 epochs.
- **Stage 2 (TIR SFT)**: ~60K problems filtered for numerical outputs. GPT-4 generated TORA-format solutions (rationale + Python + output). 3x iterations, filtered correct only. Learning rate 2e-5, batch 32, block 1024, 4 epochs.
- **Full fine-tuning** (no LoRA/DoRA). 8xH100, 10 hours.

### Inference: SC-TIR
- N=48 candidates per problem, depth M=4
- Each candidate: generate reasoning → write Python → execute → use output → repeat M times
- Majority voting on final numerical answer
- 8-bit GPTQ quantization (T4 GPUs didn't support bfloat16)

### Score Progression
| Stage | Score |
|-------|-------|
| Stage 1 only (CoT) | 8/50 |
| MMOS single-turn | 16/50 |
| Full SC-TIR (N=48, M=4) | **29/50** |

The 16→29 jump was entirely from inference algorithm, not more training.

### Failed Experiments
- **RL (PPO, RLOO)**: Promising reward curves, zero performance gain
- **Model merging (DARE, TIES, WARP)**: Regressions every time
- **Larger models (InternLM-20B, CodeLlama-33B, Mixtral-8x7B)**: Too slow on T4, couldn't beat DeepSeek-7B
- **KTO**: Got 27/50, ran out of time to apply to final model (+1-2 problems estimated)
- **Static KV cache + torch.compile**: Worked on H100, crashed on T4

---

## AIMO2 Winner: NemoSkills / NVIDIA (34/50)

**Model**: Qwen2.5-14B base, fine-tuned
**Team**: 7 people at NVIDIA
**Prize**: $262,144 (1st place)

### Key Techniques
- SFT + DPO (Direct Preference Optimization to reduce output length)
- Tool-Integrated Reasoning
- GenSelect: trained a model to READ multiple solution candidates and SELECT the best one (outperforms majority voting)

### 2nd Place: imagination-research (34/50, improved to 35/50 on re-eval)
- Tsinghua/Microsoft Research team
- DeepSeek-R1-Distill-Qwen-14B base

---

## AIMO2 Underdogs (No Fine-Tuning)

| Rank | Team | Score | Approach |
|------|------|-------|----------|
| 3rd | Aliev | 30/50 | Off-the-shelf model, inference engineering |
| 4th | sravn (solo) | 29/50 | Off-the-shelf, only team to solve hardest "WEIRDY" problem |
| 5th | usernam | 29/50 | Off-the-shelf model |

All 3rd-5th place were just 4-5 problems behind NVIDIA's 7-person team.

---

## AIMO1 Underdogs

| Rank | Team | Score | Notes |
|------|------|-------|-------|
| 2nd | CMU_MATH (solo) | 22/50 | Policy + reward model weighted voting, $65K prize |
| 3rd | "after exams" | 21/50 | ZERO fine-tuning, DeepSeekMath-7B off-the-shelf, 120-160 candidates/question |
| 4th | codeinter | 21/50 | Unknown details |
| 5th-12th | Various (many solo) | 20/50 | Tight cluster, likely variants of Abdur Rafae's notebook |

**"after exams" (3rd)** is the most remarkable: no training, just massively parallelized sampling (120-160 candidates) with smart filtering (penalize small numbers, answers found in problem text). Won ~$32K.

**Abdur Rafae**: Won $10K early sharing prize. His public notebook defined the meta — all top 4 teams credited it.

---

## AIMO3 Other Public Notebooks

| Score | Approach | Author |
|-------|----------|--------|
| 43/50 | GPT-OSS-120B + weighted entropy | kurianbenoy |
| ~40s? | GPT-OSS-120B + Agentic Solver | seshurajup |
| ? | GPT-OSS-120B with tools | andreasbis |
| ? | GPT-OSS-120B baseline | takuji, markwang |
| ? | DeepSeek-R1-Distill-Qwen-7B | nihilisticneuralnet |
