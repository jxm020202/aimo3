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

**GPT-OSS-120B solves ONLY Problems 1-4. Zero on Problems 5-10.**

## Using Reference Problems

```bash
# reference.csv has id, problem, answer columns
# Use for local validation before burning daily submission
# Test against these first with any new approach
```

## Key Remarks from PDF
- Problem 1 is "easier than any problem used in AIMO3" — pure sanity check
- Problem 2: OpenAI's high-compute run FAILED but low-compute runs got it right (interesting!)
- Problems 5-9: "difficulty is intentionally higher than AIMO2"
- Problem 10: Adapted from IMO Shortlist, hardest problem, only GPT-5 Pro and GPT-5.1 (high) solved it
