# Attempt Marginal Value Analysis: v23 (16 attempts)

**Question**: Did going from 8 to 16 attempts per problem actually help?

> Note: 78 unique problems after deduplication (last batch wins for problems appearing in multiple batches: VAL BENCH, PRIORITY DEBUG, DOUBLE-RUN RETRY).

## Executive Summary

| Metric | Value |
|--------|-------|
| Score at 8 attempts | **61/78** (78.2%) |
| Score at 16 attempts | **62/78** (79.5%) |
| Net gain from attempts 9-16 | **+1** problems |
| Problems first found correct in 9-16 | **0** |
| Problems requiring >8 att to win vote | **3** |
| Time spent on attempts 9-16 | **1298 min** |
| Cost per gained problem | **1298 min** |

### Verdict

Going to 16 attempts provided **marginal benefit**: +1 problem(s). The extra 1298 minutes may not justify the gain.

**Optimal attempt count**: 15 attempts achieves the maximum score of 63/78.

---

## 1. First Correct Attempt Distribution

Total problems with expected answers: **78**
Problems where correct answer was NEVER found: **12**
Problems where correct answer was found at least once: **66**

| Attempt # | First Found | % of Total | Cumulative | Cum % |
|-----------|-------------|------------|------------|-------|
|         1 |          26 |      33.3% |         26 | 33.3% | ##########################
|         2 |           9 |      11.5% |         35 | 44.9% | #########
|         3 |          13 |      16.7% |         48 | 61.5% | #############
|         4 |           7 |       9.0% |         55 | 70.5% | #######
|         5 |           6 |       7.7% |         61 | 78.2% | ######
|         6 |           4 |       5.1% |         65 | 83.3% | ####
|         7 |           1 |       1.3% |         66 | 84.6% | #
|         8 |           0 |       0.0% |         66 | 84.6% | 
|         9 |           0 |       0.0% |         66 | 84.6% | 
|        10 |           0 |       0.0% |         66 | 84.6% | 
|        11 |           0 |       0.0% |         66 | 84.6% | 
|        12 |           0 |       0.0% |         66 | 84.6% | 
|        13 |           0 |       0.0% |         66 | 84.6% | 
|        14 |           0 |       0.0% |         66 | 84.6% | 
|        15 |           0 |       0.0% |         66 | 84.6% | 
|        16 |           0 |       0.0% |         66 | 84.6% | 
|     Never |          12 |      15.4% | | |

**26/66** problems that have a correct answer find it on attempt 1 (39%).

## 2. Problems Requiring >8 Attempts to Find Correct Answer

**No problems** had their first correct answer in attempts 9-16.
Going from 8 to 16 attempts did NOT discover any new correct answers.

### Additional correct votes from attempts 9-16
**64 problems** had correct answers in BOTH halves:

| Problem ID | Correct in 1-8 | Correct in 9-16 | Total Correct | Total Attempts |
|------------|---------------|----------------|---------------|----------------|
| 76aef9 | 2 | 3 | 5 | 16 |
| 424e18 | 2 | 3 | 5 | 16 |
| dd7f5e | 2 | 2 | 4 | 16 |
| b4ec47 | 3 | 2 | 5 | 16 |
| 2d282e | 3 | 2 | 5 | 16 |
| 8fea51 | 2 | 3 | 5 | 16 |
| 269012 | 3 | 2 | 5 | 16 |
| 06788e | 3 | 2 | 5 | 16 |
| 095efa | 3 | 2 | 5 | 16 |
| 0aa751 | 2 | 3 | 5 | 16 |
| 0c55f3 | 2 | 3 | 5 | 16 |
| 12a146 | 3 | 2 | 5 | 16 |
| 1363c5 | 3 | 2 | 5 | 16 |
| 14f73f | 4 | 1 | 5 | 16 |
| 170362 | 1 | 4 | 5 | 16 |
| 17a3b6 | 2 | 3 | 5 | 16 |
| 17fb59 | 4 | 1 | 5 | 16 |
| 19570e | 3 | 2 | 5 | 16 |
| 27cec1 | 4 | 1 | 5 | 16 |
| 2c40d6 | 3 | 2 | 5 | 16 |
| 2e2ccb | 3 | 2 | 5 | 16 |
| 3070ea | 3 | 2 | 5 | 16 |
| 32690e | 2 | 4 | 6 | 16 |
| 3980cd | 1 | 1 | 2 | 16 |
| 3cf8bf | 3 | 2 | 5 | 16 |
| 3e5546 | 3 | 3 | 6 | 16 |
| 3edbcf | 2 | 3 | 5 | 16 |
| 3eee67 | 4 | 1 | 5 | 16 |
| 414a5b | 2 | 3 | 5 | 16 |
| 443a0e | 3 | 2 | 5 | 16 |
| 481584 | 3 | 2 | 5 | 16 |
| 485d27 | 2 | 3 | 5 | 16 |
| 4985d4 | 4 | 1 | 5 | 16 |
| 4ebdaa | 4 | 1 | 5 | 16 |
| 53de2d | 2 | 3 | 5 | 16 |
| 581a58 | 4 | 1 | 5 | 16 |
| 676ce2 | 2 | 3 | 5 | 16 |
| 69e477 | 3 | 2 | 5 | 16 |
| 6c042a | 3 | 2 | 5 | 16 |
| 6c1fb9 | 3 | 2 | 5 | 16 |
| 72a159 | 3 | 2 | 5 | 16 |
| 777281 | 4 | 1 | 5 | 16 |
| 89c921 | 4 | 1 | 5 | 16 |
| 9bfdb0 | 4 | 1 | 5 | 16 |
| a240b5 | 2 | 3 | 5 | 16 |
| a7b83d | 3 | 2 | 5 | 16 |
| a83f0b | 1 | 4 | 5 | 16 |
| a86319 | 4 | 1 | 5 | 16 |
| ac93ce | 3 | 2 | 5 | 16 |
| b286eb | 2 | 3 | 5 | 16 |
| ba89f9 | 2 | 3 | 5 | 16 |
| bad5bf | 2 | 3 | 5 | 16 |
| c19295 | 1 | 3 | 4 | 16 |
| c4d8d5 | 2 | 3 | 5 | 16 |
| c9a608 | 2 | 3 | 5 | 16 |
| ca2a54 | 4 | 1 | 5 | 16 |
| cbbc1b | 2 | 3 | 5 | 16 |
| cf3142 | 2 | 3 | 5 | 16 |
| d5054a | 1 | 4 | 5 | 16 |
| d5f758 | 3 | 2 | 5 | 16 |
| d6f389 | 3 | 3 | 6 | 16 |
| d75200 | 4 | 1 | 5 | 16 |
| ddba8e | 2 | 3 | 5 | 16 |
| e5a7c0 | 3 | 2 | 5 | 16 |

## 3. Minimum Attempts Needed to Win Majority Vote

For each problem that is CORRECT in v23, what is the smallest N such that majority vote over attempts 1..N gives the correct answer?

| Min Attempts | Problems | Cum Problems | Notes |
|-------------|----------|-------------|-------|
|           1 |       25 |          25 |  |
|           2 |        7 |          32 |  |
|           3 |       12 |          44 |  |
|           4 |        7 |          51 |  |
|           5 |        4 |          55 |  |
|           6 |        4 |          59 |  |
|           7 |        1 |          60 |  |
|           8 |        0 |          60 | <-- v22 cap |
|           9 |        0 |          60 |  |
|          10 |        0 |          60 |  |
|          11 |        0 |          60 |  |
|          12 |        0 |          60 | <-- mid option |
|          13 |        1 |          61 |  |
|          14 |        0 |          61 |  |
|          15 |        2 |          63 |  |
|          16 |        0 |          63 | <-- v23 cap |

**3 problem(s)** require more than 8 attempts to win the majority vote:

| Problem ID | Min N Needed | Expected | Margin at Min N |
|------------|-------------|----------|-----------------|
| 76aef9 | 15 | 8 | +1 |
| 414a5b | 13 | 42 | +1 |
| c19295 | 15 | 48 | +1 |

### Vote Stability Check
Problems that are correct at N=16 but WRONG at some intermediate N:

| Problem ID | Wrong at N= | Expected |
|------------|------------|----------|
| 76aef9 | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14 | 8 |
| dd7f5e | 7 | 160 |
| 8fea51 | 3, 4, 5 | 42 |
| 06788e | 1, 2, 3, 4 | 9 |
| 27cec1 | 2, 3, 4, 5 | 2304 |
| 414a5b | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14 | 42 |
| 581a58 | 1, 2, 3 | 18 |
| c19295 | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16 | 48 |

## 4. Score Simulation: 8 vs 12 vs 16 Attempts

Using v23 data, truncate to first N attempts and compute majority vote score.

### Simple Truncation (no early stop)

| Max Attempts | Score | Accuracy | Delta vs 16 | Delta vs 8 |
|-------------|-------|----------|-------------|------------|
|           1 | 26/78 |    33.3% |         -36 |        -35 |
|           2 | 33/78 |    42.3% |         -29 |        -28 |
|           3 | 45/78 |    57.7% |         -17 |        -16 |
|           4 | 52/78 |    66.7% |         -10 |         -9 |
|           5 | 56/78 |    71.8% |          -6 |         -5 |
|           6 | 60/78 |    76.9% |          -2 |         -1 |
|           7 | 60/78 |    76.9% |          -2 |         -1 |
|           8 ** | 61/78 |    78.2% |          -1 |          0 |
|           9 | 61/78 |    78.2% |          -1 |          0 |
|          10 | 61/78 |    78.2% |          -1 |          0 |
|          11 | 60/78 |    76.9% |          -2 |         -1 |
|          12 ** | 60/78 |    76.9% |          -2 |         -1 |
|          13 | 61/78 |    78.2% |          -1 |          0 |
|          14 | 60/78 |    76.9% |          -2 |         -1 |
|          15 | 63/78 |    80.8% |          +1 |         +2 |
|          16 ** | 62/78 |    79.5% |           0 |         +1 |

### Key Comparison
- **8 attempts**: 61/78 (78.2%)
- **12 attempts**: 60/78 (76.9%)
- **16 attempts**: 62/78 (79.5%)

### Problems that CHANGE between 8 and 16 attempts

**Gained** (wrong@8, correct@16): 2 problems
  - `76aef9`: expected=8, votes@8={999: 3, 1: 2, 8: 2}, votes@16={999: 4, 1: 2, 8: 5, 1997: 2}
  - `414a5b`: expected=42, votes@8={216: 1, 95: 2, 42: 2, 6: 1, 23: 1}, votes@16={216: 1, 95: 4, 42: 5, 6: 1, 23: 3}

**Lost** (correct@8, wrong@16): 1 problems
  - `ae2add`: expected=24931, votes@8={24931: 1, 19946: 1, 9973: 1, 19945: 1}, votes@16={24931: 1, 19946: 3, 9973: 2, 19945: 3}

### With Early Stop (ES=N matching answers triggers stop)

| Cap | ES=3 | ES=4 | ES=5 | No ES |
|-----|------|------|------|-------|
|   8 | 61/78 | 61/78 | 61/78 | 61/78 |
|  10 | 61/78 | 61/78 | 61/78 | 61/78 |
|  12 | 60/78 | 60/78 | 60/78 | 60/78 |
|  14 | 60/78 | 61/78 | 60/78 | 60/78 |
|  16 | 60/78 | 62/78 | 62/78 | 62/78 |

## 5. Marginal Value of Each Additional Attempt

How many NEW problems does attempt N make correct (that attempts 1..N-1 could not)?

| Attempt N | Score at N | Marginal (+) | Marginal (-) | Net | Problems Flipped |
|-----------|-----------|-------------|-------------|-----|-----------------|
|         1 | 26/78 | +26 | -0 | +26 | (baseline) |
|         2 | 33/78 | +7 | -0 | +7 | +424e18, +69e477, +6c042a, +6c1fb9, +ca2a54, +cf3142, +d6f389 |
|         3 | 45/78 | +12 | -0 | +12 | +2d282e, +095efa, +0c55f3, +2c40d6, +3edbcf, +443a0e, +481584, +4ebdaa, +72a159, +a83f0b, +bad5bf, +e5a7c0 |
|         4 | 52/78 | +7 | -0 | +7 | +0aa751, +2e2ccb, +3eee67, +53de2d, +581a58, +a7b83d, +ba89f9 |
|         5 | 56/78 | +4 | -0 | +4 | +06788e, +3070ea, +3cf8bf, +c4d8d5 |
|         6 | 60/78 | +4 | -0 | +4 | +8fea51, +27cec1, +c9a608, +cbbc1b |
|         7 | 60/78 | +1 | -1 | +0 | +d5054a, -dd7f5e |
|         8 | 61/78 | +1 | -0 | +1 | +dd7f5e |
|         9 | 61/78 | +0 | -0 | +0 | - |
|        10 | 61/78 | +1 | -1 | +0 | +3980cd, -ae2add |
|        11 | 60/78 | +0 | -1 | -1 | -3980cd |
|        12 | 60/78 | +0 | -0 | +0 | - |
|        13 | 61/78 | +1 | -0 | +1 | +414a5b |
|        14 | 60/78 | +0 | -1 | -1 | -414a5b |
|        15 | 63/78 | +3 | -0 | +3 | +76aef9, +414a5b, +c19295 |
|        16 | 62/78 | +0 | -1 | -1 | -c19295 |

### First-Ever-Solvable-At Analysis

At which attempt cap N does each problem FIRST become solvable (majority vote correct)?

| First Solvable At | Count | Cumulative | Problem IDs |
|-------------------|-------|------------|-------------|
|                 1 |    26 |         26 | dd7f5e, b4ec47, 269012, 12a146, 1363c5, 14f73f, 170362, 17a3b6, 17fb59, 19570e, 32690e, 3e5546, 485d27, 4985d4, 676ce2, 777281, 89c921, 9bfdb0, a240b5, a86319, ac93ce, ae2add, b286eb, d5f758, d75200, ddba8e |
|                 2 |     7 |         33 | 424e18, 69e477, 6c042a, 6c1fb9, ca2a54, cf3142, d6f389 |
|                 3 |    12 |         45 | 2d282e, 095efa, 0c55f3, 2c40d6, 3edbcf, 443a0e, 481584, 4ebdaa, 72a159, a83f0b, bad5bf, e5a7c0 |
|                 4 |     7 |         52 | 0aa751, 2e2ccb, 3eee67, 53de2d, 581a58, a7b83d, ba89f9 |
|                 5 |     4 |         56 | 06788e, 3070ea, 3cf8bf, c4d8d5 |
|                 6 |     4 |         60 | 8fea51, 27cec1, c9a608, cbbc1b |
|                 7 |     1 |         61 | d5054a |
|                 8 |     0 |         61 | - |
|                 9 |     0 |         61 | - |
|                10 |     1 |         62 | 3980cd |
|                11 |     0 |         62 | - |
|                12 |     0 |         62 | - |
|                13 |     1 |         63 | 414a5b |
|                14 |     0 |         63 | - |
|                15 |     2 |         65 | 76aef9, c19295 |
|                16 |     0 |         65 | - |
|             Never |    13 | | |

### Diminishing Returns Summary

| Range | Attempts Used | Problems Gained | Per-Attempt Yield |
|-------|--------------|----------------|-------------------|
| 1-4   | 4            | +26 | 6.50/attempt |
| 5-8   | 4            | +9 | 2.25/attempt |
| 9-12  | 4            | -1 | -0.25/attempt |
| 13-16 | 4            | +2 | 0.50/attempt |
| **1-8 total** | 8 | **61** | 7.62/attempt |
| **9-16 total** | 8 | **+1** | 0.12/attempt |

## 6. v22 vs v23 Comparison (Shared Problems)

Shared problems: **8**

| Run | Score (shared) | Config |
|-----|---------------|--------|
| v22 (actual, 8 att) | 6/8 | 8 att, ES=3, flat temp=0.5 |
| v23 @ 8 att (simulated) | 6/8 | 16 att truncated to 8, ES=5, temp schedule |
| v23 (actual, 16 att) | 7/8 | 16 att, ES=5, temp schedule |

### Problems that changed between runs

| Problem ID | v22 (8att) | v23@8att | v23 (16att) | Expected |
|------------|-----------|---------|------------|----------|
| 76aef9 | WRONG | WRONG | OK | 8 |
