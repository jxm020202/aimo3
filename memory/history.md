# AIMO Competition History

## Overview

| Aspect | AIMO 1 (2024) | AIMO 2 (2025) | AIMO 3 (2026) |
|--------|---------------|---------------|---------------|
| Winner | Numina (29/50) | NemoSkills (34/50) | TBD |
| Prize | $1.048M | ~$2M | $2.207M + $110K extras |
| Difficulty | Pre-selection / National | National Olympiad | National to IMO |
| Answers | 3-digit integers | 3-digit integers | 5-digit integers |
| Hardware | 2x T4 | 4x L4 | H100 |
| Key model | DeepSeekMath-7B | DeepSeek-R1-Distill-Qwen-14B | GPT-OSS-120B |
| Best public | 29/50 | 34/50 | 44/50 |
| 47/50 bonus | Not claimed | Not claimed | Not claimed |
| Teams | 1,161 | 2,000+ | 2,740+ |

The 47/50 bonus ($1.59M) has NEVER been claimed. It rolls over each competition.

## AIMO1 Detailed Leaderboard (Top 20, Private)

| Rank | Team | Score | Notes |
|------|------|-------|-------|
| 1 | **Numina** | 29 | HuggingFace team, two-stage SFT, SC-TIR |
| 2 | **CMU_MATH** | 22 | Single person, policy + reward model |
| 3 | **after exams** | 21 | ZERO training, 120-160 candidates |
| 4 | codeinter | 21 | Unknown approach |
| 5 | Conor #2 | 20 | Individual, submitted very early |
| 6 | TheEighthDay | 20 | |
| 7 | [Deleted] | 20 | |
| 8 | Vaishnavi Mudaliar | 20 | Individual (real name) |
| 9 | kaiwu | 20 | |
| 10 | curiousgeorge | 20 | |
| 11 | Hoang Tu Anh | 20 | Individual |
| 12 | Quickpanda | 20 | |
| 13 | zby | 19 | |
| 14 | aigood | 19 | |
| 15 | ZhujunXu | 19 | Individual |
| 16 | BU123 | 19 | |
| 17 | Practice makes perfect | 19 | |
| 18 | rl12 | 19 | |
| 19 | Dileep Jayamal | 19 | Individual |
| 20 | aha | 18 | |

**Key pattern**: 1st (29) to 2nd (22) = 7-point gap. 2nd (22) to 20th (18) = only 4-point spread. Extremely tight field from 2nd place down. 81 countries participated.

## AIMO2 Top Results

| Rank | Team | Score | Notes |
|------|------|-------|-------|
| 1 | NemoSkills (NVIDIA, 7 people) | 34 | Qwen2.5-14B, SFT+DPO, GenSelect |
| 2 | imagination-research (Tsinghua/MSRA) | 34 (35 on re-eval) | DeepSeek-R1-Distill-Qwen-14B |
| 3 | Aliev | 30 | Off-the-shelf, no fine-tuning |
| 4 | sravn (solo) | 29 | Only team to solve "WEIRDY" problem |
| 5 | usernam | 29 | Off-the-shelf |

Combined open-source (all 2000+ teams): 47/50
o3-preview high-compute: 47/50 on same problems

## Key Patterns Across All AIMOs

1. **Solo/small teams consistently place top 5** with no fine-tuning
2. **Inference engineering > training** for underdogs
3. **The gap between 1st and 3rd-5th is only 4-5 problems**
4. **Hardware equalizer**: Limited compute forces everyone to similar model sizes
5. **Score distributions are extremely tight** below 1st place
6. **Abdur Rafae effect**: One person's public notebook defined the entire AIMO1 meta
7. **Private LB drops are real**: Score can shift significantly from public to private
8. **The "WEIRDY" / hard problem factor**: Solving the hardest problem nobody else does is a differentiator (sravn in AIMO2)
