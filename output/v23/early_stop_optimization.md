# Early Stop & Attempt Count Optimization (v23)

**Source**: `output/v23/diagnostic.log`  
**Problems**: 97 (with expected answers)  
**Current config**: 16 attempts, ES=5  
**Current score**: 65/97 (67.0%)  

## Q1: Early Stop Threshold Simulation (v23)

All 16 attempts available; ES stops counting when N consecutive same-answer votes reached.

| ES | Score | Accuracy | Avg Att Used | Median Att | ES Triggered | Total Time (sum) | Avg Time/Prob |
|---:|------:|---------:|-------------:|-----------:|-------------:|-----------------:|--------------:|
| 2 | 60/97 | 61.9% | 5.6 | 5 | 94/97 | 17144s (285.7m) | 176.7s |
| 3 | 62/97 | 63.9% | 8.6 | 8 | 90/97 | 17620s (293.7m) | 181.6s |
| 4 | 64/97 | 66.0% | 11.2 | 11 | 86/97 | 17822s (297.0m) | 183.7s |
| 5 | 64/97 | 66.0% | 13.8 | 14 | 82/97 | 17966s (299.4m) | 185.2s |
| None | 64/97 | 66.0% | 16.0 | 16 | 0/97 | 18799s (313.3m) | 193.8s |

## Q2: Early Stop False Positive Analysis

A 'false positive' = ES triggers, locks in a WRONG answer, AND the correct answer
appears in unused later attempts (i.e., ES prevented a correct vote from being counted).

### ES=2
- ES triggered on 94/97 problems
- Correct lock-in: 60 (64%)
- Wrong lock-in: 34
- **Rescuable false positives**: 12 (correct answer existed in unused attempts)

| Problem | ES locked answer | Expected | Stopped at | Correct found at |
|---------|:----------------:|:--------:|:----------:|:----------------:|
| 76aef9 | 999 | 8 | 3/16 | 4, 5, 7, 9, 16 |
| 76aef9 | 999 | 8 | 4/16 | 5, 7, 10, 14, 15 |
| dd7f5e | 80 | 160 | 7/16 | 8, 9, 12 |
| 21fb4e | 17 | 16 | 7/16 | 10, 14 |
| 27cec1 | 2 | 2304 | 4/16 | 5, 6, 7, 9 |
| 29714f | 99 | 297 | 4/16 | 6 |
| 414a5b | 95 | 42 | 4/16 | 10 |
| aff75c | 3600 | 3571 | 4/16 | 5, 8 |
| c19295 | 18 | 48 | 5/16 | 11, 12, 15 |
| dbbfe8 | 8 | 22 | 3/16 | 15 |
| 29714f | 99 | 297 | 5/16 | 6 |
| 414a5b | 95 | 42 | 4/16 | 5, 7, 11, 13, 15 |

### ES=3
- ES triggered on 90/97 problems
- Correct lock-in: 62 (69%)
- Wrong lock-in: 28
- **Rescuable false positives**: 7 (correct answer existed in unused attempts)

| Problem | ES locked answer | Expected | Stopped at | Correct found at |
|---------|:----------------:|:--------:|:----------:|:----------------:|
| 76aef9 | 999 | 8 | 6/16 | 7, 10, 14, 15 |
| 21fb4e | 17 | 16 | 8/16 | 10, 14 |
| 414a5b | 95 | 42 | 5/16 | 10 |
| aff75c | 3600 | 3571 | 7/16 | 8 |
| c19295 | 18 | 48 | 9/16 | 11, 12, 15 |
| dbbfe8 | 8 | 22 | 4/16 | 15 |
| 414a5b | 95 | 42 | 10/16 | 11, 13, 15 |

### ES=4
- ES triggered on 86/97 problems
- Correct lock-in: 63 (73%)
- Wrong lock-in: 23
- **Rescuable false positives**: 4 (correct answer existed in unused attempts)

| Problem | ES locked answer | Expected | Stopped at | Correct found at |
|---------|:----------------:|:--------:|:----------:|:----------------:|
| 76aef9 | 999 | 8 | 9/16 | 10, 14, 15 |
| 21fb4e | 17 | 16 | 12/16 | 14 |
| 414a5b | 95 | 42 | 6/16 | 10 |
| dbbfe8 | 8 | 22 | 10/16 | 15 |

### ES=5
- ES triggered on 82/97 problems
- Correct lock-in: 62 (76%)
- Wrong lock-in: 20
- **Rescuable false positives**: 1 (correct answer existed in unused attempts)

| Problem | ES locked answer | Expected | Stopped at | Correct found at |
|---------|:----------------:|:--------:|:----------:|:----------------:|
| dbbfe8 | 8 | 22 | 13/16 | 15 |

## Q3: Vote Stabilization Analysis

After attempt N, adding more attempts never changes the majority-vote winner.

| Stabilizes at attempt | Count | Cumulative | % |
|:---------------------:|------:|-----------:|--:|
| 1 | 32 | 32/97 | 33% |
| 2 | 12 | 44/97 | 45% |
| 3 | 17 | 61/97 | 63% |
| 4 | 9 | 70/97 | 72% |
| 5 | 7 | 77/97 | 79% |
| 6 | 6 | 83/97 | 86% |
| 7 | 1 | 84/97 | 87% |
| 8 | 1 | 85/97 | 88% |
| 9 | 2 | 87/97 | 90% |
| 10 | 2 | 89/97 | 92% |
| 11 | 2 | 91/97 | 94% |
| 12 | 1 | 92/97 | 95% |
| 13 | 1 | 93/97 | 96% |
| 15 | 2 | 95/97 | 98% |
| 16 | 2 | 97/97 | 100% |

**Mean stabilization**: 3.9 attempts | **Median**: 3 | **P90**: 10

### Late-Stabilizing Problems (stabilize at >= 6)

| Problem | Stabilizes at | Total att | Winner | Expected | Correct |
|---------|:------------:|:---------:|:------:|:--------:|:-------:|
| 76aef9 | 16 | 16 | 8 | 8 | Y |
| c19295 | 16 | 16 | 18 | 48 | Y |
| 76aef9 | 15 | 16 | 8 | 8 | Y |
| 414a5b | 15 | 16 | 42 | 42 | Y |
| aff75c | 13 | 16 | 3600 | 3571 | N |
| 86e8e5 | 12 | 16 | 96985 | 8687 | N |
| 86e8e5 | 11 | 16 | 8687 | 8687 | Y |
| 3980cd | 11 | 16 | 642 | 46 | N |
| a9dbc8 | 10 | 16 | 15743 | 15744 | N |
| ae2add | 10 | 16 | 19946 | 24931 | N |
| 3980cd | 9 | 16 | 642 | 46 | N |
| ae2add | 9 | 16 | 19945 | 24931 | N |
| dd7f5e | 8 | 16 | 160 | 160 | Y |
| d5054a | 7 | 16 | 251 | 251 | Y |
| 8fea51 | 6 | 16 | 42 | 42 | Y |

## Q4: Optimal (Attempts, ES) Grid Search

Budget: 300 min (18000s) for 50 problems + 120s vLLM startup.
Time projection: scale per-problem average from this log to 50 problems.

### Score Grid

| Att \ ES | 2 | 3 | 4 | 5 | None |
|:--------:|:---:|:---:|:---:|:---:|:---:|
| 4 | 52/97  | 52/97  | 52/97  | 52/97  | 52/97  |
| 6 | 59/97  | 61/97  | 61/97  | 61/97  | 61/97  |
| 8 | 59/97  | 62/97  | 63/97  | 63/97  | 63/97  |
| 10 | 59/97  | 62/97  | 63/97  | 63/97  | 63/97  |
| 12 | 60/97  | 62/97  | 63/97  | 63/97  | 63/97  |
| 14 | 60/97  | 62/97  | 63/97  | 62/97  | 62/97  |
| 16 | 60/97  | 62/97  | 64/97  | 64/97  | 64/97  |

*Cells without (X) fit within 300-min budget for 50 problems.*

### Projected Time Grid (minutes for 50 problems)

| Att \ ES | 2 | 3 | 4 | 5 | None |
|:--------:|:---:|:---:|:---:|:---:|:---:|
| 4 | 146m  | 147m  | 147m  | 147m  | 147m  |
| 6 | 146m  | 149m  | 149m  | 149m  | 149m  |
| 8 | 148m  | 151m  | 152m  | 153m  | 153m  |
| 10 | 149m  | 153m  | 154m  | 155m  | 155m  |
| 12 | 149m  | 153m  | 154m  | 155m  | 155m  |
| 14 | 149m  | 153m  | 154m  | 155m  | 156m  |
| 16 | 149m  | 153m  | 155m  | 156m  | 164m  |

### Pareto-Optimal Configs

| Config | Score | Accuracy | Avg Att | Proj. Time (50p) | Fits 300m? |
|--------|------:|---------:|--------:|-----------------:|:----------:|
| att=16,ES=4 | 64/97 | 66.0% | 11.2 | 155m | YES |
| att=8,ES=4 | 63/97 | 64.9% | 7.8 | 152m | YES |
| att=8,ES=3 | 62/97 | 63.9% | 7.0 | 151m | YES |
| att=6,ES=3 | 61/97 | 62.9% | 5.7 | 149m | YES |
| att=12,ES=2 | 60/97 | 61.9% | 5.4 | 149m | YES |
| att=6,ES=2 | 59/97 | 60.8% | 4.5 | 146m | YES |
| att=4,ES=2 | 52/97 | 53.6% | 3.6 | 146m | YES |

**RECOMMENDED**: att=16, ES=4 -> 64/97 (66.0%), projected 155min for 50 problems

## Q5: v22 vs v23 Head-to-Head on Common Problems

Common problems: 8

| Problem | v22 | v22 Att | v22 ES | v22 Time | v23 | v23 Att | v23 ES | v23 Time | Changed |
|---------|:---:|:------:|:------:|:--------:|:---:|:------:|:------:|:--------:|:-------:|
| 269012 | Y | 8 | Y | 214.3s | Y | 16 | Y | 244.3s | same |
| 2d282e | Y | 8 | Y | 69.2s | Y | 16 | Y | 53.0s | same |
| 424e18 | Y | 8 | Y | 117.3s | Y | 16 | Y | 154.4s | same |
| 76aef9 | N | 8 | Y | 135.7s | Y | 16 | Y | 226.5s | +1 |
| 86e8e5 | N | 8 | N | 494.8s | N | 16 | N | 331.4s | same |
| 8fea51 | Y | 8 | Y | 154.2s | Y | 16 | Y | 183.6s | same |
| b4ec47 | Y | 8 | Y | 217.6s | Y | 16 | Y | 256.2s | same |
| dd7f5e | Y | 8 | Y | 209.5s | Y | 16 | N | 288.4s | same |

**v22**: 6/8 | **v23**: 7/8
- Improved (v22 wrong -> v23 correct): 1 ['76aef9']
- Regressed (v22 correct -> v23 wrong): 0 []
- Same: 7

### Extra-Attempt Benefit Analysis

For common problems, simulate v23 data with v22 config (8 att, ES=3) vs actual v23 config (16 att, ES=5):

| Problem | v23@(8,ES=3) | v23@(16,ES=5) | v23@(16,NoES) | Extra att helped? |
|---------|:------------:|:-------------:|:-------------:|:-----------------:|
| 269012 | Y | Y | Y | same |
| 2d282e | Y | Y | Y | same |
| 424e18 | Y | Y | Y | same |
| 76aef9 | N | Y | Y | YES |
| 86e8e5 | N | N | N | same |
| 8fea51 | Y | Y | Y | same |
| b4ec47 | Y | Y | Y | same |
| dd7f5e | Y | Y | Y | same |

## Bonus: Detailed ES Behavior on Wrong Problems

Analyzing 32 wrong problems across ES thresholds:

| Problem | Expected | ES=2 | ES=3 | ES=4 | ES=5 | NoES | Best ES |
|---------|:--------:|:----:|:----:|:----:|:----:|:----:|:-------:|
| 86e8e5 | 8687 | N | N | N | N | N | None |
| 1ec970 | 8700 | N | N | N | N | N | None |
| 21fb4e | 16 | N | N | N | N | N | None |
| 23586c | 386 | N | N | N | N | N | None |
| 26bee3 | 108 | N | N | N | N | N | None |
| 29714f | 297 | N | N | N | N | N | None |
| 3980cd | 46 | N | N | N | N | N | None |
| 3b88b3 | 979 | N | N | N | N | N | None |
| 414a5b | 42 | N | N | N | N | N | None |
| 673b29 | 3 | N | N | N | N | N | None |
| 89c921 | 29800 | N | N | N | N | N | None |
| 9010d9 | 10320 | N | N | N | N | N | None |
| a824c1 | 24 | N | N | N | N | N | None |
| a9dbc8 | 15744 | N | N | N | N | N | None |
| ae2add | 24931 | N | N | N | N | N | None |
| aff75c | 3571 | N | N | N | N | N | None |
| dbbfe8 | 22 | N | N | N | N | N | None |
| 86e8e5 | 8687 | N | N | N | N | N | None |
| 1ec970 | 8700 | N | N | N | N | N | None |
| 21fb4e | 16 | N | N | N | N | N | None |
| 23586c | 386 | N | N | N | N | N | None |
| 26bee3 | 108 | N | N | N | N | N | None |
| 29714f | 297 | N | N | N | N | N | None |
| 3980cd | 46 | Y | N | N | N | N | 2 |
| 3b88b3 | 979 | N | N | N | N | N | None |
| 673b29 | 3 | N | N | N | N | N | None |
| 9010d9 | 10320 | N | N | N | N | N | None |
| a824c1 | 24 | N | N | N | N | N | None |
| a9dbc8 | 15744 | N | N | N | N | N | None |
| ae2add | 24931 | N | N | N | N | N | None |
| aff75c | 3571 | N | N | N | N | N | None |
| dbbfe8 | 22 | N | N | N | N | N | None |

## Summary: Recommended Configuration

Current baseline: **65/97** correct, 18811s (313.5min)

| Config | Score | Avg Att | Total Time | Time Saved | 50p Projection | Fits? |
|--------|------:|--------:|-----------:|-----------:|:--------------:|:-----:|
| Current (16att, ES=5) | 64/97 | 13.8 | 17966s | +846s | 156m | YES |
| Conservative (16att, ES=4) | 64/97 | 11.2 | 17822s | +989s | 155m | YES |
| Moderate (16att, ES=3) | 62/97 | 8.6 | 17620s | +1191s | 153m | YES |
| Aggressive (12att, ES=4) | 63/97 | 10.4 | 17691s | +1121s | 154m | YES |
| Aggressive (12att, ES=3) | 62/97 | 8.2 | 17548s | +1263s | 153m | YES |
| Minimal (8att, ES=3) | 62/97 | 7.0 | 17373s | +1438s | 151m | YES |
| Tight (8att, ES=2) | 59/97 | 5.0 | 16953s | +1858s | 148m | YES |
| Wide (16att, ES=2) | 60/97 | 5.6 | 17144s | +1667s | 149m | YES |
