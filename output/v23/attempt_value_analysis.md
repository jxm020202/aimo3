# Attempt Marginal Value Analysis: v23 (16 attempts)

**Question**: Did going from 8 to 16 attempts per problem actually help?

> Note: 53 unique problems after deduplication (last batch wins for problems appearing in multiple batches: VAL BENCH, PRIORITY DEBUG, DOUBLE-RUN RETRY).

## Executive Summary

| Metric | Value |
|--------|-------|
| Score at 8 attempts | **37/53** (69.8%) |
| Score at 16 attempts | **38/53** (71.7%) |
| Net gain from attempts 9-16 | **+1** problems |
| Problems first found correct in 9-16 | **4** |
| Problems requiring >8 att to win vote | **0** |
| Time spent on attempts 9-16 | **1060 min** |
| Cost per gained problem | **1060 min** |

### Verdict

Going to 16 attempts provided **marginal benefit**: +1 problem(s). The extra 1060 minutes may not justify the gain.

**Optimal attempt count**: 6 attempts achieves the maximum score of 38/53.

---

## 1. First Correct Attempt Distribution

Total problems with expected answers: **53**
Problems where correct answer was NEVER found: **7**
Problems where correct answer was found at least once: **46**

| Attempt # | First Found | % of Total | Cumulative | Cum % |
|-----------|-------------|------------|------------|-------|
|         1 |          33 |      62.3% |         33 | 62.3% | #################################
|         2 |           1 |       1.9% |         34 | 64.2% | #
|         3 |           4 |       7.5% |         38 | 71.7% | ####
|         4 |           0 |       0.0% |         38 | 71.7% | 
|         5 |           3 |       5.7% |         41 | 77.4% | ###
|         6 |           0 |       0.0% |         41 | 77.4% | 
|         7 |           1 |       1.9% |         42 | 79.2% | #
|         8 |           0 |       0.0% |         42 | 79.2% | 
|         9 |           2 |       3.8% |         44 | 83.0% | ##
|        10 |           0 |       0.0% |         44 | 83.0% | 
|        11 |           0 |       0.0% |         44 | 83.0% | 
|        12 |           1 |       1.9% |         45 | 84.9% | #
|        13 |           0 |       0.0% |         45 | 84.9% | 
|        14 |           0 |       0.0% |         45 | 84.9% | 
|        15 |           1 |       1.9% |         46 | 86.8% | #
|        16 |           0 |       0.0% |         46 | 86.8% | 
|     Never |           7 |      13.2% | | |

**33/46** problems that have a correct answer find it on attempt 1 (72%).

## 2. Problems Requiring >8 Attempts to Find Correct Answer

**4 problem(s)** had their first correct answer in attempts 9-16:

| Problem ID | First Correct At | Expected | Predicted (vote) | Final Correct? |
|------------|-----------------|----------|-----------------|----------------|
| a824c1 | Attempt 12 | 24 | 13 | NO |
| 9010d9 | Attempt 15 | 10320 | 6400 | NO |
| 3980cd | Attempt 9 | 46 | 642 | NO |
| ae2add | Attempt 9 | 24931 | 19945 | NO |

These 4 problems would have had **zero** correct attempts with only 8 tries.

### Additional correct votes from attempts 9-16
**40 problems** had correct answers in BOTH halves:

| Problem ID | Correct in 1-8 | Correct in 9-16 | Total Correct | Total Attempts |
|------------|---------------|----------------|---------------|----------------|
| dbbfe8 | 3 | 2 | 5 | 16 |
| 32690e | 8 | 8 | 16 | 16 |
| 26bee3 | 1 | 1 | 2 | 16 |
| 89c921 | 2 | 2 | 4 | 16 |
| 21fb4e | 8 | 7 | 15 | 16 |
| bad5bf | 7 | 7 | 14 | 16 |
| 170362 | 8 | 8 | 16 | 16 |
| 095efa | 8 | 8 | 16 | 16 |
| d5054a | 8 | 8 | 16 | 16 |
| 3edbcf | 8 | 8 | 16 | 16 |
| 3cf8bf | 5 | 8 | 13 | 16 |
| 3070ea | 8 | 6 | 14 | 16 |
| 17a3b6 | 8 | 7 | 15 | 16 |
| 14f73f | 8 | 8 | 16 | 16 |
| c9a608 | 5 | 5 | 10 | 16 |
| a7b83d | 8 | 7 | 15 | 16 |
| 1363c5 | 5 | 5 | 10 | 16 |
| ac93ce | 8 | 8 | 16 | 16 |
| 69e477 | 8 | 8 | 16 | 16 |
| 0aa751 | 7 | 8 | 15 | 16 |
| d75200 | 7 | 8 | 15 | 16 |
| c19295 | 2 | 3 | 5 | 16 |
| 2e2ccb | 3 | 6 | 9 | 16 |
| cf3142 | 8 | 8 | 16 | 16 |
| 9bfdb0 | 7 | 6 | 13 | 16 |
| e5a7c0 | 8 | 8 | 16 | 16 |
| 2c40d6 | 5 | 6 | 11 | 16 |
| 4985d4 | 8 | 8 | 16 | 16 |
| 481584 | 6 | 7 | 13 | 16 |
| 72a159 | 8 | 7 | 15 | 16 |
| d5f758 | 8 | 8 | 16 | 16 |
| a83f0b | 8 | 8 | 16 | 16 |
| ddba8e | 7 | 7 | 14 | 16 |
| c4d8d5 | 8 | 8 | 16 | 16 |
| 3eee67 | 8 | 8 | 16 | 16 |
| cbbc1b | 7 | 8 | 15 | 16 |
| 06788e | 8 | 8 | 16 | 16 |
| a86319 | 7 | 7 | 14 | 16 |
| 676ce2 | 8 | 8 | 16 | 16 |
| 19570e | 5 | 6 | 11 | 16 |

## 3. Minimum Attempts Needed to Win Majority Vote

For each problem that is CORRECT in v23, what is the smallest N such that majority vote over attempts 1..N gives the correct answer?

| Min Attempts | Problems | Cum Problems | Notes |
|-------------|----------|-------------|-------|
|           1 |       32 |          32 |  |
|           2 |        1 |          33 |  |
|           3 |        3 |          36 |  |
|           4 |        0 |          36 |  |
|           5 |        0 |          36 |  |
|           6 |        2 |          38 |  |
|           7 |        0 |          38 |  |
|           8 |        0 |          38 | <-- v22 cap |
|           9 |        0 |          38 |  |
|          10 |        0 |          38 |  |
|          11 |        0 |          38 |  |
|          12 |        0 |          38 | <-- mid option |
|          13 |        0 |          38 |  |
|          14 |        0 |          38 |  |
|          15 |        0 |          38 |  |
|          16 |        0 |          38 | <-- v23 cap |

**0 problem(s)** require more than 8 attempts to win the majority vote:

### Vote Stability Check
Problems that are correct at N=16 but WRONG at some intermediate N:

| Problem ID | Wrong at N= | Expected |
|------------|------------|----------|
| dbbfe8 | 2, 3, 4, 5, 11, 12, 13 | 22 |
| c19295 | 2, 3, 4, 5, 7, 8, 9 | 48 |
| 2e2ccb | 1, 2 | 876 |
| 9bfdb0 | 1 | 90 |
| 2c40d6 | 1, 2, 3, 4, 5 | 34628 |
| 481584 | 1, 2 | 820 |

## 4. Score Simulation: 8 vs 12 vs 16 Attempts

Using v23 data, truncate to first N attempts and compute majority vote score.

### Simple Truncation (no early stop)

| Max Attempts | Score | Accuracy | Delta vs 16 | Delta vs 8 |
|-------------|-------|----------|-------------|------------|
|           1 | 33/53 |    62.3% |          -5 |         -4 |
|           2 | 33/53 |    62.3% |          -5 |         -4 |
|           3 | 35/53 |    66.0% |          -3 |         -2 |
|           4 | 35/53 |    66.0% |          -3 |         -2 |
|           5 | 36/53 |    67.9% |          -2 |         -1 |
|           6 | 38/53 |    71.7% |           0 |         +1 |
|           7 | 37/53 |    69.8% |          -1 |          0 |
|           8 ** | 37/53 |    69.8% |          -1 |          0 |
|           9 | 37/53 |    69.8% |          -1 |          0 |
|          10 | 38/53 |    71.7% |           0 |         +1 |
|          11 | 37/53 |    69.8% |          -1 |          0 |
|          12 ** | 38/53 |    71.7% |           0 |         +1 |
|          13 | 38/53 |    71.7% |           0 |         +1 |
|          14 | 38/53 |    71.7% |           0 |         +1 |
|          15 | 38/53 |    71.7% |           0 |         +1 |
|          16 ** | 38/53 |    71.7% |           0 |         +1 |

### Key Comparison
- **8 attempts**: 37/53 (69.8%)
- **12 attempts**: 38/53 (71.7%)
- **16 attempts**: 38/53 (71.7%)

### Problems that CHANGE between 8 and 16 attempts

**Gained** (wrong@8, correct@16): 1 problems
  - `c19295`: expected=48, votes@8={72: 1, 18: 2, 12: 2, 48: 2}, votes@16={72: 1, 144: 1, 48: 5, 18: 4, 12: 2, 40: 2}

**No problems lost** by going from 8 to 16 attempts.

### With Early Stop (ES=N matching answers triggers stop)

| Cap | ES=3 | ES=4 | ES=5 | No ES |
|-----|------|------|------|-------|
|   8 | 38/53 | 38/53 | 38/53 | 38/53 |
|  10 | 37/53 | 37/53 | 37/53 | 37/53 |
|  12 | 37/53 | 37/53 | 37/53 | 37/53 |
|  14 | 37/53 | 37/53 | 38/53 | 38/53 |
|  16 | 37/53 | 37/53 | 38/53 | 38/53 |

## 5. Marginal Value of Each Additional Attempt

How many NEW problems does attempt N make correct (that attempts 1..N-1 could not)?

| Attempt N | Score at N | Marginal (+) | Marginal (-) | Net | Problems Flipped |
|-----------|-----------|-------------|-------------|-----|-----------------|
|         1 | 33/53 | +33 | -0 | +33 | (baseline) |
|         2 | 33/53 | +1 | -1 | +0 | +9bfdb0, -c19295 |
|         3 | 35/53 | +3 | -1 | +2 | +c9a608, +2e2ccb, +481584, -89c921 |
|         4 | 35/53 | +0 | -0 | +0 | - |
|         5 | 36/53 | +1 | -0 | +1 | +89c921 |
|         6 | 38/53 | +3 | -1 | +2 | +dbbfe8, +c19295, +2c40d6, -89c921 |
|         7 | 37/53 | +0 | -1 | -1 | -c19295 |
|         8 | 37/53 | +0 | -0 | +0 | - |
|         9 | 37/53 | +0 | -0 | +0 | - |
|        10 | 38/53 | +1 | -0 | +1 | +c19295 |
|        11 | 37/53 | +0 | -1 | -1 | -dbbfe8 |
|        12 | 38/53 | +1 | -0 | +1 | +3980cd |
|        13 | 38/53 | +0 | -0 | +0 | - |
|        14 | 38/53 | +1 | -1 | +0 | +dbbfe8, -3980cd |
|        15 | 38/53 | +0 | -0 | +0 | - |
|        16 | 38/53 | +0 | -0 | +0 | - |

### First-Ever-Solvable-At Analysis

At which attempt cap N does each problem FIRST become solvable (majority vote correct)?

| First Solvable At | Count | Cumulative | Problem IDs |
|-------------------|-------|------------|-------------|
|                 1 |    33 |         33 | 32690e, 89c921, 21fb4e, bad5bf, 170362, 095efa, d5054a, 3edbcf, 3cf8bf, 3070ea, 17a3b6, 14f73f, a7b83d, 1363c5, ac93ce, 69e477, 0aa751, d75200, c19295, cf3142, e5a7c0, 4985d4, 72a159, d5f758, a83f0b, ddba8e, c4d8d5, 3eee67, cbbc1b, 06788e, a86319, 676ce2, 19570e |
|                 2 |     1 |         34 | 9bfdb0 |
|                 3 |     3 |         37 | c9a608, 2e2ccb, 481584 |
|                 4 |     0 |         37 | - |
|                 5 |     0 |         37 | - |
|                 6 |     2 |         39 | dbbfe8, 2c40d6 |
|                 7 |     0 |         39 | - |
|                 8 |     0 |         39 | - |
|                 9 |     0 |         39 | - |
|                10 |     0 |         39 | - |
|                11 |     0 |         39 | - |
|                12 |     1 |         40 | 3980cd |
|                13 |     0 |         40 | - |
|                14 |     0 |         40 | - |
|                15 |     0 |         40 | - |
|                16 |     0 |         40 | - |
|             Never |    13 | | |

### Diminishing Returns Summary

| Range | Attempts Used | Problems Gained | Per-Attempt Yield |
|-------|--------------|----------------|-------------------|
| 1-4   | 4            | +2 | 0.50/attempt |
| 5-8   | 4            | +2 | 0.50/attempt |
| 9-12  | 4            | +1 | 0.25/attempt |
| 13-16 | 4            | +0 | 0.00/attempt |
| **1-8 total** | 8 | **37** | 4.62/attempt |
| **9-16 total** | 8 | **+1** | 0.12/attempt |
