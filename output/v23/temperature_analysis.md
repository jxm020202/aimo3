# V23 Temperature Effectiveness Analysis

## Executive Summary

The v23 temperature schedule (0.1, 0.3, 0.5, 0.7, 0.9) is **actively hurting performance**. Flat temp=0.5 would solve **70/97 problems vs 64/97** with the current schedule. The schedule wastes budget on high-temperature attempts (0.9) that have catastrophic 76% None rate and 30% accuracy.

## Temperature Distribution

v23 uses a 5-temperature schedule with uneven allocation:

| Temp | Attempts | % of Total |
|------|----------|-----------|
| 0.1  | 97       | 6.3%      |
| 0.3  | 388      | 25.0%     |
| 0.5  | 582      | 37.5%     |
| 0.7  | 388      | 25.0%     |
| 0.9  | 97       | 6.3%      |

## Key Metrics by Temperature

| Temp | Total | Correct | Wrong | None | Accuracy | None Rate | Avg Errors | Avg Time |
|------|-------|---------|-------|------|----------|-----------|-----------|----------|
| 0.1  | 97    | 26      | 16    | 55   | **61.9%** | 56.7%    | 1.49      | 151.8s   |
| 0.3  | 388   | 92      | 80    | 216  | 53.5%    | **55.7%** | 0.92      | 146.2s   |
| 0.5  | 582   | 132     | 105   | 345  | 55.7%    | 59.3%    | 1.08      | 146.3s   |
| 0.7  | 388   | 80      | 79    | 229  | 50.3%    | 59.0%    | 0.98      | 143.9s   |
| 0.9  | 97    | 7       | 16    | 74   | **30.4%** | **76.3%** | **1.62** | **166.3s** |

### Raw Accuracy (correct/total, Nones counted as wrong)

| Temp | Correct | Total | Raw Accuracy |
|------|---------|-------|-------------|
| 0.1  | 26      | 97    | **26.8%**   |
| 0.3  | 92      | 388   | 23.7%       |
| 0.5  | 132     | 582   | 22.7%       |
| 0.7  | 80      | 388   | 20.6%       |
| 0.9  | 7       | 97    | **7.2%**    |

## Critical Finding: Flat vs Schedule

**Simulated flat-temperature problem counts:**

| Strategy | Problems Solved | vs Schedule |
|----------|----------------|-------------|
| Flat 0.1 | 26/97          | -38         |
| Flat 0.3 | 60/97          | -4          |
| **Flat 0.5** | **70/97**  | **+6**      |
| Flat 0.7 | 52/97          | -12         |
| Flat 0.9 | 7/97           | -57         |
| **Current schedule** | **64/97** | baseline |

**Flat temp=0.5 beats the schedule by 6 problems.** The schedule loses diversity where it matters -- the low temps (0.1) have high per-attempt accuracy but solve few unique problems because they get so few attempts, while the high temps (0.7, 0.9) just waste budget on wrong/None answers.

### Problems lost by flat 0.5

Only **1 problem** (ddba8e) gets solved by the schedule but NOT by flat 0.5. Problem ddba8e was only solved at temp=0.7 (unique correct). Meanwhile flat 0.5 picks up 7 additional problems.

### Would flat 0.3 outperform the schedule?

Flat 0.3 solves 60/97 -- **4 fewer** than the schedule (64). It would lose 6 problems that other temps handle: 170362, 17a3b6, c9a608, cbbc1b, d5054a, dd7f5e. These are all solved at temp=0.5 or 0.7 but not 0.3. So flat 0.3 is worse than the schedule but not catastrophically so.

## Unique Correct by Temperature

Problems where ONLY a specific temperature found the correct answer:

| Temp | Problems | Details |
|------|----------|---------|
| 0.1  | 1        | ae2add (exp=24931) -- final vote was WRONG |
| 0.5  | 1        | 29714f (exp=297) -- final vote was WRONG |
| 0.7  | 1        | dbbfe8 (exp=22) -- final vote was WRONG |

All three unique-correct problems were **outvoted** in the final answer, meaning the schedule found the right answer but couldn't capitalize on it. This suggests the schedule adds marginal exploration value but the voting mechanism fails to preserve it.

## Reasoning Depth by Temperature

| Temp | Avg Turns | Avg Reasoning (chars) | Avg Code Calls | Avg Code Length |
|------|-----------|----------------------|----------------|----------------|
| 0.1  | 11.2      | 32,728               | 10.5           | 5,169          |
| 0.3  | 10.1      | 33,073               | 9.3            | 4,187          |
| 0.5  | 10.0      | 33,086               | 9.2            | 4,157          |
| 0.7  | 10.2      | 32,867               | 9.4            | 3,958          |
| 0.9  | **7.8**   | **30,508**           | **7.2**        | **2,700**      |

Temp 0.9 produces significantly shorter reasoning, fewer code calls, and shorter code. The model seems to "give up" or produce less coherent solutions at high temperature.

## Error Analysis by Temperature

| Temp | Total Errors | Avg Errors | Error Rate | Errors/Turn |
|------|-------------|-----------|-----------|-------------|
| 0.1  | 145         | 1.49      | 43.3%     | 0.133       |
| 0.3  | 358         | **0.92**  | **38.9%** | **0.091**   |
| 0.5  | 631         | 1.08      | 43.8%     | 0.108       |
| 0.7  | 382         | 0.98      | 42.5%     | 0.096       |
| 0.9  | 157         | **1.62**  | **62.9%** | **0.207**   |

Temp 0.3 is the cleanest -- lowest average errors, lowest error rate, lowest errors/turn. Temp 0.9 is catastrophic with 63% of attempts hitting errors and the highest error density.

## Time Efficiency by Temperature

| Temp | Total Time | Avg Time | Time per Correct | Time per Answer |
|------|-----------|---------|-----------------|----------------|
| 0.1  | 14,723s   | 151.8s  | **566.3s**      | **350.5s**     |
| 0.3  | 56,732s   | 146.2s  | 616.7s          | 329.8s         |
| 0.5  | 85,157s   | 146.3s  | 645.1s          | 359.3s         |
| 0.7  | 55,842s   | 143.9s  | 698.0s          | 351.2s         |
| 0.9  | 16,132s   | 166.3s  | **2,304.6s**    | **701.4s**     |

Temp 0.1 is most time-efficient per correct answer. Temp 0.9 burns 2,300s per correct answer -- 4x worse than temp 0.1. Note: temp 0.1 gets fewer attempts (1 per problem) but uses each efficiently.

## Recommendations for v24

### Primary: Switch to flat temp=0.5

- Solves 70/97 vs 64/97 (+6 problems)
- Only loses 1 problem (ddba8e, which was outvoted anyway)
- Simpler implementation, no schedule overhead

### Alternative: Narrow schedule (0.3, 0.5)

If diversity is desired, use only temps 0.3 and 0.5:
- 0.3 has the lowest error rate and lowest None rate
- 0.5 has the highest raw problem coverage
- Drop 0.1 (too few attempts to matter), 0.7 (lower accuracy, no unique benefit), 0.9 (catastrophic)

### Drop temp=0.9 immediately

- 76.3% None rate (highest)
- 30.4% accuracy (lowest by far)
- 62.9% error rate (highest)
- Only 7/97 correct, 0 unique
- 2,300s per correct answer (worst)
- Shorter reasoning, fewer code calls -- model degrades at this temperature

### Consider temp 0.1 for "high confidence" mode

- Highest per-attempt accuracy (61.9%)
- But 56.7% None rate limits coverage
- Could be useful as a "verification" pass on already-solved problems

## Raw Data Notes

- Cross-checked with `filter_attempts.py --temp 0.1 --stats` and `--temp 0.9 --stats` -- numbers match
- 97 problems total, 1552 total attempts
- Schedule appears to be: 1 attempt at 0.1, 4 at 0.3, 6 at 0.5, 4 at 0.7, 1 at 0.9 (per problem for standard batch)
- Double-run problems get 2x this allocation
