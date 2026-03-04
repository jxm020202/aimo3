# Attempt Marginal Value Analysis: v23 (16 attempts)

**Question**: Did going from 8 to 16 attempts per problem actually help?

> Note: 52 unique problems after deduplication (last batch wins for problems appearing in multiple batches: VAL BENCH, PRIORITY DEBUG, DOUBLE-RUN RETRY).

## Executive Summary

| Metric | Value |
|--------|-------|
| Score at 8 attempts | **36/52** (69.2%) |
| Score at 16 attempts | **36/52** (69.2%) |
| Net gain from attempts 9-16 | **+0** problems |
| Problems first found correct in 9-16 | **0** |
| Problems requiring >8 att to win vote | **0** |
| Time spent on attempts 9-16 | **1582 min** |
| Cost per gained problem | **inf** (no gain) |

### Verdict

Going to 16 attempts provided **NO benefit** on the final score. The extra 1582 minutes were entirely wasted.

**Optimal attempt count**: 6 attempts achieves the maximum score of 38/52.

---

## 1. First Correct Attempt Distribution

Total problems with expected answers: **52**
Problems where correct answer was NEVER found: **6**
Problems where correct answer was found at least once: **46**

| Attempt # | First Found | % of Total | Cumulative | Cum % |
|-----------|-------------|------------|------------|-------|
|         1 |          32 |      61.5% |         32 | 61.5% | ################################
|         2 |           3 |       5.8% |         35 | 67.3% | ###
|         3 |           4 |       7.7% |         39 | 75.0% | ####
|         4 |           1 |       1.9% |         40 | 76.9% | #
|         5 |           3 |       5.8% |         43 | 82.7% | ###
|         6 |           0 |       0.0% |         43 | 82.7% | 
|         7 |           2 |       3.8% |         45 | 86.5% | ##
|         8 |           1 |       1.9% |         46 | 88.5% | #
|         9 |           0 |       0.0% |         46 | 88.5% | 
|        10 |           0 |       0.0% |         46 | 88.5% | 
|        11 |           0 |       0.0% |         46 | 88.5% | 
|        12 |           0 |       0.0% |         46 | 88.5% | 
|        13 |           0 |       0.0% |         46 | 88.5% | 
|        14 |           0 |       0.0% |         46 | 88.5% | 
|        15 |           0 |       0.0% |         46 | 88.5% | 
|        16 |           0 |       0.0% |         46 | 88.5% | 
|     Never |           6 |      11.5% | | |

**32/46** problems that have a correct answer find it on attempt 1 (70%).

## 2. Problems Requiring >8 Attempts to Find Correct Answer

**No problems** had their first correct answer in attempts 9-16.
Going from 8 to 16 attempts did NOT discover any new correct answers.

### Additional correct votes from attempts 9-16
**37 problems** had correct answers in BOTH halves:

| Problem ID | Correct in 1-8 | Correct in 9-16 | Total Correct | Total Attempts |
|------------|---------------|----------------|---------------|----------------|
| 21fb4e | 8 | 8 | 16 | 16 |
| dbbfe8 | 3 | 3 | 6 | 16 |
| 89c921 | 6 | 6 | 12 | 16 |
| 9010d9 | 1 | 1 | 2 | 16 |
| 3980cd | 2 | 1 | 3 | 16 |
| 32690e | 8 | 8 | 16 | 16 |
| ba89f9 | 3 | 6 | 9 | 16 |
| 170362 | 7 | 7 | 14 | 16 |
| 095efa | 8 | 8 | 16 | 16 |
| cf3142 | 8 | 7 | 15 | 16 |
| 3e5546 | 7 | 8 | 15 | 16 |
| 3070ea | 6 | 5 | 11 | 16 |
| 17a3b6 | 8 | 7 | 15 | 16 |
| 14f73f | 8 | 8 | 16 | 16 |
| c4d8d5 | 8 | 7 | 15 | 16 |
| a240b5 | 8 | 8 | 16 | 16 |
| 1363c5 | 3 | 2 | 5 | 16 |
| a86319 | 8 | 8 | 16 | 16 |
| 676ce2 | 7 | 5 | 12 | 16 |
| 0aa751 | 8 | 8 | 16 | 16 |
| d75200 | 8 | 8 | 16 | 16 |
| c19295 | 2 | 2 | 4 | 16 |
| 2e2ccb | 6 | 1 | 7 | 16 |
| d6f389 | 8 | 8 | 16 | 16 |
| 777281 | 7 | 3 | 10 | 16 |
| ac93ce | 8 | 8 | 16 | 16 |
| 2c40d6 | 8 | 1 | 9 | 16 |
| ddba8e | 7 | 3 | 10 | 16 |
| a7b83d | 7 | 7 | 14 | 16 |
| cbbc1b | 2 | 2 | 4 | 16 |
| 06788e | 8 | 7 | 15 | 16 |
| 4ebdaa | 8 | 8 | 16 | 16 |
| bad5bf | 7 | 7 | 14 | 16 |
| 485d27 | 2 | 2 | 4 | 16 |
| a83f0b | 3 | 5 | 8 | 16 |
| 19570e | 6 | 1 | 7 | 16 |
| e5a7c0 | 7 | 8 | 15 | 16 |

## 3. Minimum Attempts Needed to Win Majority Vote

For each problem that is CORRECT in v23, what is the smallest N such that majority vote over attempts 1..N gives the correct answer?

| Min Attempts | Problems | Cum Problems | Notes |
|-------------|----------|-------------|-------|
|           1 |       32 |          32 |  |
|           2 |        3 |          35 |  |
|           3 |        0 |          35 |  |
|           4 |        1 |          36 |  |
|           5 |        0 |          36 |  |
|           6 |        1 |          37 |  |
|           7 |        0 |          37 |  |
|           8 |        0 |          37 | <-- v22 cap |
|           9 |        0 |          37 |  |
|          10 |        0 |          37 |  |
|          11 |        0 |          37 |  |
|          12 |        0 |          37 | <-- mid option |
|          13 |        0 |          37 |  |
|          14 |        0 |          37 |  |
|          15 |        0 |          37 |  |
|          16 |        0 |          37 | <-- v23 cap |

**0 problem(s)** require more than 8 attempts to win the majority vote:

### Vote Stability Check
Problems that are correct at N=16 but WRONG at some intermediate N:

| Problem ID | Wrong at N= | Expected |
|------------|------------|----------|
| 89c921 | 2 | 29800 |
| 1363c5 | 2, 3 | 10211 |
| c19295 | 2 | 48 |
| 581a58 | 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 | 18 |
| ddba8e | 1 | 15 |
| 53de2d | 1, 2, 3, 4, 5 | 576 |

## 4. Score Simulation: 8 vs 12 vs 16 Attempts

Using v23 data, truncate to first N attempts and compute majority vote score.

### Simple Truncation (no early stop)

| Max Attempts | Score | Accuracy | Delta vs 16 | Delta vs 8 |
|-------------|-------|----------|-------------|------------|
|           1 | 32/52 |    61.5% |          -4 |         -4 |
|           2 | 32/52 |    61.5% |          -4 |         -4 |
|           3 | 35/52 |    67.3% |          -1 |         -1 |
|           4 | 36/52 |    69.2% |           0 |          0 |
|           5 | 37/52 |    71.2% |          +1 |         +1 |
|           6 | 38/52 |    73.1% |          +2 |         +2 |
|           7 | 36/52 |    69.2% |           0 |          0 |
|           8 ** | 36/52 |    69.2% |           0 |          0 |
|           9 | 36/52 |    69.2% |           0 |          0 |
|          10 | 37/52 |    71.2% |          +1 |         +1 |
|          11 | 36/52 |    69.2% |           0 |          0 |
|          12 ** | 36/52 |    69.2% |           0 |          0 |
|          13 | 36/52 |    69.2% |           0 |          0 |
|          14 | 36/52 |    69.2% |           0 |          0 |
|          15 | 36/52 |    69.2% |           0 |          0 |
|          16 ** | 36/52 |    69.2% |           0 |          0 |

### Key Comparison
- **8 attempts**: 36/52 (69.2%)
- **12 attempts**: 36/52 (69.2%)
- **16 attempts**: 36/52 (69.2%)

### Problems that CHANGE between 8 and 16 attempts

**No problems gained** by going from 8 to 16 attempts.

**No problems lost** by going from 8 to 16 attempts.

### With Early Stop (ES=N matching answers triggers stop)

| Cap | ES=3 | ES=4 | ES=5 | No ES |
|-----|------|------|------|-------|
|   8 | 36/52 | 36/52 | 36/52 | 36/52 |
|  10 | 36/52 | 36/52 | 37/52 | 37/52 |
|  12 | 36/52 | 36/52 | 37/52 | 36/52 |
|  14 | 36/52 | 36/52 | 37/52 | 36/52 |
|  16 | 36/52 | 36/52 | 37/52 | 36/52 |

## 5. Marginal Value of Each Additional Attempt

How many NEW problems does attempt N make correct (that attempts 1..N-1 could not)?

| Attempt N | Score at N | Marginal (+) | Marginal (-) | Net | Problems Flipped |
|-----------|-----------|-------------|-------------|-----|-----------------|
|         1 | 32/52 | +32 | -0 | +32 | (baseline) |
|         2 | 32/52 | +3 | -3 | +0 | +ba89f9, +ddba8e, +a83f0b, -89c921, -1363c5, -c19295 |
|         3 | 35/52 | +3 | -0 | +3 | +89c921, +9010d9, +c19295 |
|         4 | 36/52 | +2 | -1 | +1 | +1363c5, +581a58, -9010d9 |
|         5 | 37/52 | +1 | -0 | +1 | +a9dbc8 |
|         6 | 38/52 | +2 | -1 | +1 | +3980cd, +53de2d, -581a58 |
|         7 | 36/52 | +0 | -2 | -2 | -a9dbc8, -3980cd |
|         8 | 36/52 | +0 | -0 | +0 | - |
|         9 | 36/52 | +0 | -0 | +0 | - |
|        10 | 37/52 | +1 | -0 | +1 | +dbbfe8 |
|        11 | 36/52 | +0 | -1 | -1 | -dbbfe8 |
|        12 | 36/52 | +0 | -0 | +0 | - |
|        13 | 36/52 | +0 | -0 | +0 | - |
|        14 | 36/52 | +0 | -0 | +0 | - |
|        15 | 36/52 | +0 | -0 | +0 | - |
|        16 | 36/52 | +0 | -0 | +0 | - |

### First-Ever-Solvable-At Analysis

At which attempt cap N does each problem FIRST become solvable (majority vote correct)?

| First Solvable At | Count | Cumulative | Problem IDs |
|-------------------|-------|------------|-------------|
|                 1 |    32 |         32 | 21fb4e, 89c921, 32690e, 170362, 095efa, cf3142, 3e5546, 3070ea, 17a3b6, 14f73f, c4d8d5, a240b5, 1363c5, a86319, 676ce2, 0aa751, d75200, c19295, 2e2ccb, d6f389, 777281, ac93ce, 2c40d6, a7b83d, 3edbcf, cbbc1b, 06788e, 4ebdaa, bad5bf, 485d27, 19570e, e5a7c0 |
|                 2 |     3 |         35 | ba89f9, ddba8e, a83f0b |
|                 3 |     1 |         36 | 9010d9 |
|                 4 |     1 |         37 | 581a58 |
|                 5 |     1 |         38 | a9dbc8 |
|                 6 |     2 |         40 | 3980cd, 53de2d |
|                 7 |     0 |         40 | - |
|                 8 |     0 |         40 | - |
|                 9 |     0 |         40 | - |
|                10 |     1 |         41 | dbbfe8 |
|                11 |     0 |         41 | - |
|                12 |     0 |         41 | - |
|                13 |     0 |         41 | - |
|                14 |     0 |         41 | - |
|                15 |     0 |         41 | - |
|                16 |     0 |         41 | - |
|             Never |    11 | | |

### Diminishing Returns Summary

| Range | Attempts Used | Problems Gained | Per-Attempt Yield |
|-------|--------------|----------------|-------------------|
| 1-4   | 4            | +4 | 1.00/attempt |
| 5-8   | 4            | +0 | 0.00/attempt |
| 9-12  | 4            | +0 | 0.00/attempt |
| 13-16 | 4            | +0 | 0.00/attempt |
| **1-8 total** | 8 | **36** | 4.50/attempt |
| **9-16 total** | 8 | **+0** | 0.00/attempt |
