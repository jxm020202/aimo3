# Reference Problems (Local Test Set)

Source: `data/reference.csv` and `data/AIMO3_Reference_Problems.pdf`

These 10 problems are for local testing ONLY. Too small for training/fine-tuning.

## Problem List

| # | ID | Answer | Difficulty | Source | Notes |
|---|-----|--------|-----------|--------|-------|
| 1 | 92ba6a | 50 | Easy | AIMO2 private ("SWEETS") | 85% of AIMO2 submissions solved it. Quick sanity check. |
| 2 | a295e9 | 520 | Hard | AIMO2 public ("RECTIL") | Only handful of top 100 solved. OpenAI high-compute FAILED this one. |
| 3 | 86e8e5 | 8687 | Medium-Hard | AIMO2 private | Number theory, n-Norwegian integers |
| 4 | 9c1c5f | 580 | Medium | AIMO2 private | Functional equation f(m)+f(n)=f(m+n+mn) |
| 5 | 0e644e | 336 | Hard (AIMO3-level) | Novel | Geometry: triangle, circumcircle, incircle |
| 6 | 26de63 | 32951 | Hard (AIMO3-level) | Novel | Double sum with floor function, number theory |
| 7 | 424e18 | 21818 | Hard (AIMO3-level) | Novel | Tournament combinatorics |
| 8 | 42d360 | 32193 | Hard (AIMO3-level) | Novel | Base representation, digit sum game |
| 9 | 641659 | 57447 | Very Hard (AIMO3-level) | Novel | Geometry + Fibonacci + cyclic quadrilateral |
| 10 | dd7f5e | 160 | Hard (IMO-level) | Adapted from IMO Shortlist | "Shifty" functions, convolution |

## Model Performance on Reference Problems (pass@3)

**Problems 1-4** (AIMO2 level): Most open-weight models can solve these.
**Problems 5-10** (AIMO3/IMO level): Only commercial models + DeepSeek-v3.1-terminus solve these.

| Model | Solved | Type |
|-------|--------|------|
| GPT-5 Pro | 10/10 | Commercial |
| GPT-5.1 (high) | 10/10 | Commercial |
| GPT-5 (high) | 9/10 | Commercial (failed P10) |
| Grok-4 | 9/10 | Commercial |
| Gemini 2.5 Pro | 9/10 | Commercial |
| DeepSeek-v3.1-terminus (thinking) | 9/10 | Open-weight 671B |
| GPT-OSS-120B | **4/10** | Open-weight 117B |

**IMPORTANT**: The 4/10 benchmark is **pass@3 with no code execution**. Pure reasoning only.
Our TIR setup (8 attempts + code sandbox + entropy-weighted voting) scored **9/10** — see v19 results below.

## Our v19 Results (actual Kaggle H100 run, 2026-03-02)

| # | ID | Expected | Got | Time | Status |
|---|-----|----------|-----|------|--------|
| 1 | 92ba6a | 50 | 50 | 28s | CORRECT |
| 2 | 9c1c5f | 580 | 580 | 99s | CORRECT |
| 3 | a295e9 | 520 | 520 | 495s | CORRECT |
| 4 | 86e8e5 | 8687 | **23** | 717s | **WRONG** |
| 5 | 0e644e | 336 | 336 | 172s | CORRECT |
| 6 | 26de63 | 32951 | 32951 | 101s | CORRECT |
| 7 | 424e18 | 21818 | 21818 | 138s | CORRECT |
| 8 | 42d360 | 32193 | 32193 | 117s | CORRECT |
| 9 | 641659 | 57447 | 57447 | 424s | CORRECT |
| 10 | dd7f5e | 160 | 160 | 268s | CORRECT |

**Score: 9/10 (90%)** | Total: ~52 min | Kaggle version: scriptVersionId=300944599

### Key Findings from v19
- **Problems 5-10 ALL solved** — these were supposed to be unsolvable by GPT-OSS-120B
- The difference: TIR (code execution) + 8-attempt voting vs pass@3 pure reasoning
- Most "hard" problems solved in 100-270s (fast!), not burning full 900s
- Our 9/10 matches Grok-4, Gemini 2.5 Pro, and DeepSeek-v3.1 (all much larger models)
- Problem 9 (641659, "very hard") took 424s but solved — geometry + Fibonacci combo

### Problem 4 Failure Analysis
- **Predicted 23, expected 8687**. Took 717s (didn't hit full 900s budget)
- The model DID produce an answer, so it didn't completely hang
- Problem involves M=3^{2025!} — astronomically large number
- **We don't have detailed logs for this run** (old cell-17 without diagnostics)
- Need to re-run with new logging to see: what code the model ran, whether it
  tried naive bigint computation, and what reasoning led to 23
- Hypothesis: model may have made a modular arithmetic error, or computed
  something wrong symbolically. Cannot confirm without logs.

## Key Remarks from PDF
- Problem 1 is "easier than any problem used in AIMO3" — pure sanity check
- Problem 2: OpenAI's high-compute run FAILED but low-compute runs got it right (interesting!)
- Problems 5-9: "difficulty is intentionally higher than AIMO2"
- Problem 10: Adapted from IMO Shortlist, hardest problem, only GPT-5 Pro and GPT-5.1 (high) solved it
