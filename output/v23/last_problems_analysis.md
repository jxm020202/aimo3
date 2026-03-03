# V23 Problem Ordering Analysis — 17 Wrong Problems

**Total entries**: 97 (97 expected — some problems run twice for dual-run)
**Total runtime**: 313.5 min (budget: 300 min)
**Over budget by**: 13.5 min

## 1. Problem Order — Where Each Wrong Problem Fell

| # | Problem ID | Batch | Wall Time | Start (min) | End (min) | Correct | Early Stop | Attempts |
|---|-----------|-------|-----------|-------------|-----------|---------|------------|----------|
| 1/97 | 86e8e5 | PRIORITY DEBUG (dual | 13m 32s | 0.0 | 13.5 | WRONG | No | 16 |
| 2/97 | 86e8e5 | PRIORITY DEBUG (dual | 11m 55s | 13.5 | 25.5 | WRONG | No | 16 |
| 22/97 | 1ec970 | VAL BENCH (new unsee | 5m 27s | 72.1 | 77.5 | WRONG | No | 16 |
| 23/97 | 21fb4e | VAL BENCH (new unsee | 5m 30s | 77.5 | 83.0 | WRONG | No | 16 |
| 24/97 | 23586c | VAL BENCH (new unsee | 36.0s | 83.0 | 83.6 | WRONG | Yes | 16 |
| 25/97 | 26bee3 | VAL BENCH (new unsee | 5m 11s | 83.6 | 88.8 | WRONG | No | 16 |
| 27/97 | 29714f | VAL BENCH (new unsee | 4m 3s | 92.3 | 96.4 | WRONG | Yes | 16 |
| 32/97 | 3980cd | VAL BENCH (new unsee | 4m 42s | 104.2 | 108.9 | WRONG | Yes | 16 |
| 33/97 | 3b88b3 | VAL BENCH (new unsee | 1m 40s | 108.9 | 110.5 | WRONG | Yes | 16 |
| 38/97 | 414a5b | VAL BENCH (new unsee | 1m 14s | 117.3 | 118.5 | WRONG | Yes | 16 |
| 46/97 | 673b29 | VAL BENCH (new unsee | 41.7s | 130.2 | 130.9 | WRONG | Yes | 16 |
| 53/97 | 89c921 | VAL BENCH (new unsee | 3m 3s | 137.8 | 140.9 | WRONG | Yes | 16 |
| 54/97 | 9010d9 | VAL BENCH (new unsee | 2m 16s | 140.9 | 143.1 | WRONG | Yes | 16 |
| 58/97 | a824c1 | VAL BENCH (new unsee | 3m 49s | 152.6 | 156.4 | WRONG | Yes | 16 |
| 61/97 | a9dbc8 | VAL BENCH (new unsee | 6m 28s | 159.0 | 165.5 | WRONG | Yes | 16 |
| 63/97 | ae2add | VAL BENCH (new unsee | 2m 45s | 166.6 | 169.3 | WRONG | Yes | 16 |
| 64/97 | aff75c | VAL BENCH (new unsee | 10m 14s | 169.3 | 179.6 | WRONG | No | 16 |
| 78/97 | dbbfe8 | VAL BENCH (new unsee | 7m 55s | 227.0 | 234.9 | WRONG | Yes | 16 |
| 81/97 | 86e8e5 | DOUBLE-RUN RETRY | 5m 31s | 239.5 | 245.0 | WRONG | No | 16 |
| 82/97 | 1ec970 | DOUBLE-RUN RETRY | 5m 28s | 245.0 | 250.5 | WRONG | No | 16 |
| 83/97 | 21fb4e | DOUBLE-RUN RETRY | 5m 22s | 250.5 | 255.8 | WRONG | Yes | 16 |
| 84/97 | 23586c | DOUBLE-RUN RETRY | 1m 20s | 255.8 | 257.2 | WRONG | Yes | 16 |
| 85/97 | 26bee3 | DOUBLE-RUN RETRY | 5m 31s | 257.2 | 262.7 | WRONG | No | 16 |
| 86/97 | 29714f | DOUBLE-RUN RETRY | 4m 59s | 262.7 | 267.7 | WRONG | Yes | 16 |
| 87/97 | 3980cd | DOUBLE-RUN RETRY | 4m 46s | 267.7 | 272.4 | WRONG | Yes | 16 |
| 88/97 | 3b88b3 | DOUBLE-RUN RETRY | 1m 55s | 272.4 | 274.4 | WRONG | Yes | 16 |
| 89/97 | 414a5b | DOUBLE-RUN RETRY | 2m 39s | 274.4 | 277.0 | WRONG | Yes | 16 |
| 90/97 | 673b29 | DOUBLE-RUN RETRY | 1m 19s | 277.0 | 278.3 | WRONG | Yes | 16 |
| 91/97 | 89c921 | DOUBLE-RUN RETRY | 5m 4s | 278.3 | 283.4 | WRONG | Yes | 16 |
| 92/97 | 9010d9 | DOUBLE-RUN RETRY | 3m 16s | 283.4 | 286.7 | WRONG | Yes | 16 |
| 93/97 | a824c1 | DOUBLE-RUN RETRY | 4m 24s | 286.7 | 291.1 | WRONG | Yes | 16 |
| 94/97 | a9dbc8 | DOUBLE-RUN RETRY | 5m 30s | 291.1 | 296.6 | WRONG | No | 16 |
| 95/97 | ae2add | DOUBLE-RUN RETRY | 5m 32s | 296.6 | 302.1 | WRONG | No | 16 |
| 96/97 | aff75c | DOUBLE-RUN RETRY | 5m 54s | 302.1 | 308.0 | WRONG | No | 16 |
| 97/97 | dbbfe8 | DOUBLE-RUN RETRY | 5m 30s | 308.0 | 313.5 | WRONG | No | 16 |

**Distribution across run thirds** (each third = ~32 problems):
- Early (1-32): 8 wrong
- Middle (33-64): 9 wrong
- Late (65-97): 18 wrong

## 2. Problems Near the Time Limit

**Problems that STARTED after 300 min budget**: 2
  - #96 aff75c — started at 302.1 min, ended 308.0 min ** WRONG **
  - #97 dbbfe8 — started at 308.0 min, ended 313.5 min ** WRONG **

**Problems that started in last 30 min of budget (270-300 min)**: 8
  - #88 3b88b3 — started at 272.4 min, ended 274.4 min ** WRONG **
  - #89 414a5b — started at 274.4 min, ended 277.0 min ** WRONG **
  - #90 673b29 — started at 277.0 min, ended 278.3 min ** WRONG **
  - #91 89c921 — started at 278.3 min, ended 283.4 min ** WRONG **
  - #92 9010d9 — started at 283.4 min, ended 286.7 min ** WRONG **
  - #93 a824c1 — started at 286.7 min, ended 291.1 min ** WRONG **
  - #94 a9dbc8 — started at 291.1 min, ended 296.6 min ** WRONG **
  - #95 ae2add — started at 296.6 min, ended 302.1 min ** WRONG **

### Last 10 Problems in the Run

| # | Problem ID | Batch | Start (min) | End (min) | Correct? | Wall Time |
|---|-----------|-------|-------------|-----------|----------|-----------|
| 88 | 3b88b3 | DOUBLE-RUN RETRY | 272.4 | 274.4 | **WRONG** | 1m 55s |
| 89 | 414a5b | DOUBLE-RUN RETRY | 274.4 | 277.0 | CORRECT | 2m 39s |
| 90 | 673b29 | DOUBLE-RUN RETRY | 277.0 | 278.3 | **WRONG** | 1m 19s |
| 91 | 89c921 | DOUBLE-RUN RETRY | 278.3 | 283.4 | CORRECT | 5m 4s |
| 92 | 9010d9 | DOUBLE-RUN RETRY | 283.4 | 286.7 | **WRONG** | 3m 16s |
| 93 | a824c1 | DOUBLE-RUN RETRY | 286.7 | 291.1 | **WRONG** | 4m 24s |
| 94 | a9dbc8 | DOUBLE-RUN RETRY | 291.1 | 296.6 | **WRONG** | 5m 30s |
| 95 | ae2add | DOUBLE-RUN RETRY | 296.6 | 302.1 | **WRONG** | 5m 32s |
| 96 | aff75c | DOUBLE-RUN RETRY | 302.1 | 308.0 | **WRONG** | 5m 54s |
| 97 | dbbfe8 | DOUBLE-RUN RETRY | 308.0 | 313.5 | **WRONG** | 5m 30s |

**Last 10 accuracy**: 2/10 (20%)

## 3. Timing Comparison: Wrong vs Correct Problems

| Metric | Correct Problems | Wrong Problems |
|--------|-----------------|----------------|
| Count | 65 | 35 |
| Mean time | 2m 37s | 4m 43s |
| Median time | 1m 58s | 4m 59s |
| Std dev | 2m 38s | 2m 54s |
| Min | 11.2s | 36.0s |
| Max | 15m 22s | 13m 32s |
| Total | 169.7 min | 165.1 min |

### Per-Problem Timing Detail (17 Wrong)

| Problem ID | Wall Time | Attempts | Answered | Errors | Early Stop | Batch |
|-----------|-----------|----------|----------|--------|------------|-------|
| 86e8e5 | 13m 32s | 16 | 14 | 61 | No | PRIORITY DEBUG (dual |
| 86e8e5 | 11m 55s | 16 | 15 | 50 | No | PRIORITY DEBUG (dual |
| aff75c | 10m 14s | 16 | 16 | 50 | No | VAL BENCH (new unsee |
| dbbfe8 | 7m 55s | 16 | 10 | 123 | Yes | VAL BENCH (new unsee |
| a9dbc8 | 6m 28s | 16 | 8 | 24 | Yes | VAL BENCH (new unsee |
| aff75c | 5m 54s | 16 | 4 | 43 | No | DOUBLE-RUN RETRY |
| ae2add | 5m 32s | 16 | 9 | 17 | No | DOUBLE-RUN RETRY |
| 86e8e5 | 5m 31s | 16 | 2 | 28 | No | DOUBLE-RUN RETRY |
| 26bee3 | 5m 31s | 16 | 5 | 12 | No | DOUBLE-RUN RETRY |
| dbbfe8 | 5m 30s | 16 | 4 | 75 | No | DOUBLE-RUN RETRY |
| a9dbc8 | 5m 30s | 16 | 4 | 26 | No | DOUBLE-RUN RETRY |
| 21fb4e | 5m 30s | 16 | 6 | 111 | No | VAL BENCH (new unsee |
| 1ec970 | 5m 28s | 16 | 2 | 33 | No | DOUBLE-RUN RETRY |
| 1ec970 | 5m 27s | 16 | 5 | 22 | No | VAL BENCH (new unsee |
| 21fb4e | 5m 22s | 16 | 8 | 102 | Yes | DOUBLE-RUN RETRY |
| 26bee3 | 5m 11s | 16 | 6 | 27 | No | VAL BENCH (new unsee |
| 89c921 | 5m 4s | 16 | 9 | 8 | Yes | DOUBLE-RUN RETRY |
| 29714f | 4m 59s | 16 | 8 | 17 | Yes | DOUBLE-RUN RETRY |
| 3980cd | 4m 46s | 16 | 8 | 14 | Yes | DOUBLE-RUN RETRY |
| 3980cd | 4m 42s | 16 | 10 | 22 | Yes | VAL BENCH (new unsee |
| a824c1 | 4m 24s | 16 | 7 | 39 | Yes | DOUBLE-RUN RETRY |
| 29714f | 4m 3s | 16 | 8 | 10 | Yes | VAL BENCH (new unsee |
| a824c1 | 3m 49s | 16 | 8 | 35 | Yes | VAL BENCH (new unsee |
| 9010d9 | 3m 16s | 16 | 5 | 4 | Yes | DOUBLE-RUN RETRY |
| 89c921 | 3m 3s | 16 | 5 | 5 | Yes | VAL BENCH (new unsee |
| ae2add | 2m 45s | 16 | 7 | 4 | Yes | VAL BENCH (new unsee |
| 414a5b | 2m 39s | 16 | 14 | 5 | Yes | DOUBLE-RUN RETRY |
| 9010d9 | 2m 16s | 16 | 6 | 3 | Yes | VAL BENCH (new unsee |
| 3b88b3 | 1m 55s | 16 | 5 | 3 | Yes | DOUBLE-RUN RETRY |
| 3b88b3 | 1m 40s | 16 | 5 | 4 | Yes | VAL BENCH (new unsee |
| 23586c | 1m 20s | 16 | 5 | 2 | Yes | DOUBLE-RUN RETRY |
| 673b29 | 1m 19s | 16 | 6 | 0 | Yes | DOUBLE-RUN RETRY |
| 414a5b | 1m 14s | 16 | 7 | 3 | Yes | VAL BENCH (new unsee |
| 673b29 | 41.7s | 16 | 6 | 0 | Yes | VAL BENCH (new unsee |
| 23586c | 36.0s | 16 | 7 | 3 | Yes | VAL BENCH (new unsee |

## 4. Attempt Count Analysis — Were Problems Cut Short?

| Metric | Correct Problems | Wrong Problems |
|--------|-----------------|----------------|
| Mean attempts | 16.0 | 16.0 |
| Median attempts | 16 | 16 |
| Early stop rate | 62/65 (95%) | 22/35 (63%) |

### Problems with Very Few Attempts (Possible Time Cutoff)

All 17 wrong problems had >= 5 attempts. Max in run: 16

## 5. Truncated or Incomplete Attempts

**Baseline**: Average attempt time = 2m 27s, Average turns per attempt = 10.0

### Wrong Problems — Attempt Details

**86e8e5** (#1, started 0.0 min):
  - 16 attempts, 2 Nones, avg time 9m 33s, avg turns 44.4
  - Attempt times: [7m 43s, 9m 1s, 9m 56s, 7m 12s, 9m 6s, 9m 11s, 11m 21s, 5m 56s, 13m 29s, 9m 21s, 8m 48s, 13m 32s, 13m 10s, 7m 1s, 8m 0s, 9m 57s]
  - Attempt turns: [21, 29, 20, 72, 32, 32, 42, 13, 68, 39, 37, 82, 69, 46, 42, 66]

**86e8e5** (#2, started 13.5 min):
  - 16 attempts, 1 Nones, avg time 9m 37s, avg turns 43.1
  - Attempt times: [6m 11s, 10m 54s, 11m 12s, 10m 27s, 9m 11s, 10m 40s, 11m 16s, 11m 55s, 10m 31s, 9m 10s, 9m 58s, 6m 28s, 7m 54s, 7m 11s, 10m 38s, 10m 20s]
  - Attempt turns: [21, 46, 52, 57, 28, 40, 40, 49, 39, 41, 43, 29, 34, 21, 77, 72]

**1ec970** (#22, started 72.1 min):
  - 16 attempts, 11 Nones, avg time 4m 2s, avg turns 16.7
  - Attempt times: [5m 3s, 56.9s, 5m 0s, 5m 0s, 1m 32s, 5m 20s, 1m 6s, 5m 27s, 5m 1s, 31.9s, 5m 5s, 5m 0s, 4m 8s, 5m 11s, 5m 0s, 5m 12s]
  - Attempt turns: [21, 1, 23, 19, 4, 22, 4, 22, 23, 1, 13, 23, 21, 13, 23, 34]

**21fb4e** (#23, started 77.5 min):
  - 16 attempts, 10 Nones, avg time 4m 38s, avg turns 25.6
  - Attempt times: [5m 30s, 5m 1s, 5m 1s, 5m 18s, 2m 20s, 5m 1s, 4m 34s, 4m 34s, 5m 1s, 3m 38s, 5m 4s, 3m 9s, 5m 8s, 4m 14s, 5m 24s, 5m 6s]
  - Attempt turns: [33, 20, 25, 24, 21, 34, 21, 28, 20, 23, 27, 18, 29, 32, 29, 25]

**23586c** (#24, started 83.0 min): [LAST ATT SHORT] [MANY SHORT]
  - 16 attempts, 9 Nones, avg time 29.5s, avg turns 2.9
  - Attempt times: [30.1s, 29.8s, 33.3s, 30.7s, 28.3s, 30.9s, 18.7s, 30.3s, 29.9s, 26.8s, 23.3s, 33.8s, 35.9s, 30.8s, 30.3s, 29.4s]
  - Attempt turns: [2, 2, 3, 3, 3, 1, 4, 1, 2, 4, 3, 4, 4, 4, 3, 4]

**26bee3** (#25, started 83.6 min):
  - 16 attempts, 10 Nones, avg time 4m 12s, avg turns 8.6
  - Attempt times: [5m 1s, 5m 1s, 5m 1s, 4m 11s, 5m 2s, 3m 25s, 5m 2s, 5m 0s, 5m 2s, 5m 2s, 5m 0s, 3m 3s, 3m 24s, 5m 11s, 45.7s, 2m 7s]
  - Attempt turns: [21, 9, 8, 4, 16, 10, 3, 17, 5, 12, 14, 1, 10, 5, 1, 1]

**29714f** (#27, started 92.3 min):
  - 16 attempts, 8 Nones, avg time 3m 28s, avg turns 13.5
  - Attempt times: [3m 51s, 1m 30s, 3m 50s, 3m 50s, 4m 3s, 3m 36s, 3m 50s, 1m 53s, 3m 33s, 3m 43s, 3m 57s, 3m 50s, 3m 3s, 3m 17s, 3m 50s, 3m 50s]
  - Attempt turns: [18, 11, 20, 11, 6, 11, 9, 6, 17, 8, 12, 29, 18, 7, 12, 21]

**3980cd** (#32, started 104.2 min):
  - 16 attempts, 6 Nones, avg time 3m 40s, avg turns 16.1
  - Attempt times: [4m 39s, 1m 4s, 4m 42s, 3m 18s, 3m 39s, 3m 15s, 4m 38s, 4m 40s, 2m 54s, 4m 14s, 4m 39s, 4m 40s, 1m 26s, 1m 41s, 4m 38s, 4m 26s]
  - Attempt turns: [28, 1, 17, 28, 15, 12, 15, 13, 3, 28, 11, 40, 1, 6, 21, 19]

**3b88b3** (#33, started 108.9 min):
  - 16 attempts, 11 Nones, avg time 1m 32s, avg turns 4.8
  - Attempt times: [1m 37s, 1m 24s, 1m 38s, 1m 38s, 1m 37s, 1m 38s, 1m 38s, 1m 0s, 1m 37s, 1m 38s, 1m 14s, 1m 22s, 1m 37s, 1m 36s, 1m 37s, 1m 40s]
  - Attempt turns: [1, 7, 3, 8, 1, 3, 7, 9, 5, 4, 4, 3, 5, 6, 8, 3]

**414a5b** (#38, started 117.3 min):
  - 16 attempts, 9 Nones, avg time 1m 3s, avg turns 5.2
  - Attempt times: [1m 14s, 1m 14s, 23.0s, 25.8s, 1m 1s, 1m 13s, 1m 14s, 1m 13s, 50.9s, 47.9s, 1m 13s, 1m 14s, 1m 0s, 1m 13s, 1m 14s, 1m 13s]
  - Attempt turns: [10, 4, 2, 2, 9, 7, 6, 4, 5, 3, 5, 6, 4, 5, 6, 5]

**673b29** (#46, started 130.2 min):
  - 16 attempts, 10 Nones, avg time 39.3s, avg turns 1.0
  - Attempt times: [38.8s, 33.7s, 41.6s, 41.6s, 41.6s, 41.6s, 41.6s, 41.6s, 28.9s, 38.8s, 41.5s, 38.8s, 33.7s, 41.6s, 41.5s, 41.5s]
  - Attempt turns: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

**89c921** (#53, started 137.8 min):
  - 16 attempts, 11 Nones, avg time 2m 50s, avg turns 7.6
  - Attempt times: [3m 1s, 3m 1s, 2m 13s, 3m 3s, 1m 40s, 3m 1s, 3m 2s, 3m 2s, 3m 2s, 3m 2s, 3m 3s, 3m 2s, 3m 3s, 3m 2s, 3m 3s, 2m 1s]
  - Attempt turns: [4, 14, 11, 12, 5, 20, 3, 3, 8, 1, 13, 9, 4, 1, 4, 10]

**9010d9** (#54, started 140.9 min):
  - 16 attempts, 10 Nones, avg time 1m 40s, avg turns 1.9
  - Attempt times: [1m 55s, 1m 54s, 1m 55s, 1m 55s, 1m 3s, 1m 55s, 1m 8s, 1m 53s, 1m 55s, 1m 53s, 2m 16s, 1m 53s, 40.8s, 1m 38s, 1m 55s, 1m 0s]
  - Attempt turns: [1, 5, 1, 1, 1, 3, 1, 3, 3, 1, 3, 3, 1, 1, 1, 1]

**a824c1** (#58, started 152.6 min):
  - 16 attempts, 8 Nones, avg time 2m 45s, avg turns 16.0
  - Attempt times: [3m 22s, 3m 24s, 3m 19s, 3m 14s, 3m 19s, 1m 31s, 1m 29s, 1m 19s, 3m 20s, 1m 4s, 3m 19s, 1m 22s, 3m 40s, 3m 8s, 3m 19s, 3m 49s]
  - Attempt turns: [12, 19, 16, 30, 15, 8, 12, 16, 29, 12, 18, 2, 21, 19, 22, 5]

**a9dbc8** (#61, started 159.0 min):
  - 16 attempts, 8 Nones, avg time 4m 59s, avg turns 11.9
  - Attempt times: [5m 38s, 5m 37s, 3m 27s, 5m 36s, 5m 36s, 5m 38s, 5m 11s, 4m 27s, 5m 36s, 4m 34s, 5m 36s, 5m 35s, 4m 38s, 4m 4s, 1m 56s, 6m 27s]
  - Attempt turns: [16, 16, 7, 10, 11, 6, 11, 20, 11, 11, 12, 15, 19, 10, 7, 8]

**ae2add** (#63, started 166.6 min):
  - 16 attempts, 9 Nones, avg time 2m 14s, avg turns 5.6
  - Attempt times: [2m 44s, 2m 43s, 2m 43s, 2m 44s, 2m 44s, 2m 43s, 2m 44s, 2m 44s, 1m 51s, 2m 3s, 2m 42s, 48.8s, 1m 48s, 28.7s, 2m 45s, 1m 35s]
  - Attempt turns: [15, 4, 14, 6, 9, 6, 4, 6, 6, 3, 3, 1, 1, 1, 10, 1]

**aff75c** (#64, started 169.3 min):
  - 16 attempts, 0 Nones, avg time 6m 48s, avg turns 35.3
  - Attempt times: [7m 3s, 8m 17s, 7m 28s, 8m 24s, 8m 30s, 10m 14s, 7m 0s, 9m 35s, 6m 10s, 1m 36s, 3m 25s, 7m 7s, 6m 11s, 3m 22s, 4m 45s, 9m 39s]
  - Attempt turns: [41, 45, 8, 52, 49, 70, 33, 57, 41, 6, 19, 28, 33, 11, 27, 45]

**dbbfe8** (#78, started 227.0 min):
  - 16 attempts, 6 Nones, avg time 6m 21s, avg turns 34.0
  - Attempt times: [6m 19s, 7m 42s, 2m 5s, 4m 32s, 5m 53s, 7m 55s, 5m 2s, 7m 43s, 7m 45s, 3m 35s, 7m 43s, 7m 50s, 6m 7s, 7m 43s, 6m 26s, 7m 15s]
  - Attempt turns: [54, 64, 18, 26, 47, 42, 19, 43, 60, 13, 29, 33, 29, 33, 29, 5]

**86e8e5** (#81, started 239.5 min):
  - 16 attempts, 14 Nones, avg time 4m 49s, avg turns 15.6
  - Attempt times: [5m 0s, 5m 2s, 5m 2s, 5m 2s, 5m 9s, 4m 43s, 5m 0s, 5m 24s, 5m 2s, 5m 12s, 5m 2s, 24.2s, 5m 26s, 5m 2s, 5m 1s, 5m 31s]
  - Attempt turns: [38, 19, 13, 23, 12, 24, 14, 21, 6, 15, 23, 3, 21, 1, 13, 4]

**1ec970** (#82, started 245.0 min):
  - 16 attempts, 14 Nones, avg time 4m 51s, avg turns 21.6
  - Attempt times: [5m 1s, 5m 28s, 5m 2s, 5m 10s, 5m 0s, 1m 24s, 5m 2s, 5m 0s, 5m 1s, 5m 1s, 5m 1s, 5m 1s, 5m 1s, 5m 1s, 5m 4s, 5m 15s]
  - Attempt turns: [14, 23, 22, 39, 28, 6, 25, 16, 27, 17, 29, 23, 32, 17, 23, 5]

**21fb4e** (#83, started 250.5 min):
  - 16 attempts, 8 Nones, avg time 3m 54s, avg turns 21.9
  - Attempt times: [5m 18s, 3m 31s, 3m 56s, 4m 50s, 5m 5s, 4m 54s, 4m 52s, 4m 56s, 4m 1s, 1m 14s, 24.8s, 5m 21s, 24.4s, 3m 4s, 5m 21s, 5m 13s]
  - Attempt turns: [36, 15, 14, 21, 26, 43, 21, 29, 35, 24, 4, 31, 5, 20, 7, 20]

**23586c** (#84, started 255.8 min): [MANY SHORT]
  - 16 attempts, 11 Nones, avg time 35.6s, avg turns 3.1
  - Attempt times: [31.4s, 34.2s, 33.9s, 32.8s, 34.1s, 33.6s, 33.9s, 34.1s, 34.8s, 34.5s, 25.7s, 26.1s, 34.5s, 34.2s, 32.5s, 1m 20s]
  - Attempt turns: [4, 1, 4, 3, 2, 2, 3, 4, 4, 3, 4, 5, 4, 1, 4, 1]

**26bee3** (#85, started 257.2 min):
  - 16 attempts, 11 Nones, avg time 4m 27s, avg turns 5.7
  - Attempt times: [2m 14s, 3m 28s, 5m 0s, 5m 0s, 5m 2s, 5m 1s, 5m 22s, 5m 2s, 1m 43s, 5m 1s, 5m 2s, 5m 2s, 4m 38s, 3m 3s, 5m 0s, 5m 31s]
  - Attempt turns: [1, 4, 3, 8, 4, 7, 21, 5, 1, 10, 1, 5, 15, 1, 3, 2]

**29714f** (#86, started 262.7 min):
  - 16 attempts, 8 Nones, avg time 4m 0s, avg turns 16.8
  - Attempt times: [4m 21s, 2m 23s, 4m 29s, 4m 29s, 3m 1s, 3m 59s, 4m 52s, 4m 29s, 3m 18s, 4m 38s, 1m 39s, 4m 34s, 4m 30s, 4m 28s, 3m 56s, 4m 59s]
  - Attempt turns: [15, 11, 15, 30, 17, 20, 26, 25, 18, 17, 7, 14, 23, 16, 11, 4]

**3980cd** (#87, started 267.7 min):
  - 16 attempts, 8 Nones, avg time 3m 37s, avg turns 11.2
  - Attempt times: [4m 16s, 4m 14s, 2m 34s, 4m 16s, 4m 15s, 3m 27s, 4m 16s, 4m 16s, 4m 15s, 1m 48s, 1m 41s, 3m 48s, 4m 5s, 1m 35s, 4m 15s, 4m 46s]
  - Attempt turns: [2, 19, 7, 15, 5, 15, 15, 26, 4, 2, 4, 21, 16, 6, 17, 5]

**3b88b3** (#88, started 272.4 min):
  - 16 attempts, 11 Nones, avg time 1m 24s, avg turns 4.7
  - Attempt times: [1m 22s, 1m 26s, 1m 2s, 1m 25s, 1m 26s, 1m 16s, 1m 25s, 1m 24s, 1m 26s, 1m 25s, 1m 26s, 1m 25s, 1m 8s, 1m 26s, 1m 25s, 1m 55s]
  - Attempt turns: [7, 1, 4, 3, 6, 6, 5, 7, 3, 2, 1, 6, 7, 10, 5, 2]

**414a5b** (#89, started 274.4 min):
  - 16 attempts, 2 Nones, avg time 1m 20s, avg turns 6.5
  - Attempt times: [17.0s, 1m 2s, 1m 3s, 1m 44s, 1m 47s, 16.9s, 1m 16s, 42.1s, 48.5s, 1m 50s, 1m 33s, 43.5s, 1m 51s, 1m 50s, 1m 49s, 2m 39s]
  - Attempt turns: [1, 5, 7, 13, 12, 1, 6, 1, 4, 8, 9, 6, 10, 11, 7, 3]

**673b29** (#90, started 277.0 min):
  - 16 attempts, 10 Nones, avg time 47.6s, avg turns 1.0
  - Attempt times: [29.1s, 49.3s, 36.2s, 36.2s, 46.6s, 44.0s, 49.3s, 46.7s, 49.3s, 49.4s, 49.4s, 49.4s, 49.4s, 49.3s, 49.3s, 1m 19s]
  - Attempt turns: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

**89c921** (#91, started 278.3 min):
  - 16 attempts, 7 Nones, avg time 3m 36s, avg turns 9.6
  - Attempt times: [2m 47s, 4m 31s, 3m 42s, 4m 31s, 2m 13s, 4m 31s, 2m 16s, 4m 30s, 3m 19s, 2m 28s, 2m 12s, 1m 48s, 4m 30s, 4m 30s, 4m 40s, 5m 3s]
  - Attempt turns: [19, 1, 13, 4, 2, 15, 6, 9, 13, 9, 9, 2, 32, 6, 9, 4]

**9010d9** (#92, started 283.4 min):
  - 16 attempts, 11 Nones, avg time 2m 39s, avg turns 2.6
  - Attempt times: [2m 48s, 2m 46s, 2m 47s, 2m 11s, 1m 9s, 2m 48s, 2m 48s, 2m 48s, 2m 24s, 2m 48s, 2m 36s, 2m 47s, 2m 48s, 2m 47s, 2m 47s, 3m 16s]
  - Attempt turns: [3, 1, 4, 2, 1, 6, 5, 1, 1, 1, 3, 5, 3, 2, 2, 1]

**a824c1** (#93, started 286.7 min):
  - 16 attempts, 9 Nones, avg time 3m 22s, avg turns 15.5
  - Attempt times: [3m 55s, 3m 60s, 2m 58s, 3m 54s, 3m 55s, 4m 14s, 3m 55s, 4m 7s, 2m 13s, 18.8s, 1m 30s, 3m 7s, 3m 55s, 3m 54s, 3m 28s, 4m 24s]
  - Attempt turns: [18, 14, 17, 11, 22, 23, 23, 15, 13, 1, 3, 21, 25, 25, 13, 4]

**a9dbc8** (#94, started 291.1 min):
  - 16 attempts, 12 Nones, avg time 4m 31s, avg turns 11.9
  - Attempt times: [5m 2s, 5m 0s, 2m 10s, 4m 8s, 5m 3s, 5m 1s, 1m 56s, 5m 3s, 5m 2s, 5m 2s, 5m 1s, 3m 2s, 5m 13s, 5m 1s, 5m 2s, 5m 30s]
  - Attempt turns: [26, 14, 5, 7, 12, 5, 4, 13, 18, 14, 16, 6, 9, 14, 19, 8]

**ae2add** (#95, started 296.6 min):
  - 16 attempts, 7 Nones, avg time 4m 1s, avg turns 11.4
  - Attempt times: [3m 30s, 3m 1s, 5m 1s, 2m 41s, 5m 2s, 4m 52s, 5m 2s, 5m 1s, 5m 2s, 1m 1s, 3m 56s, 5m 3s, 25.3s, 4m 17s, 4m 46s, 5m 31s]
  - Attempt turns: [2, 6, 32, 1, 11, 23, 17, 15, 4, 6, 8, 25, 3, 10, 14, 6]

**aff75c** (#96, started 302.1 min):
  - 16 attempts, 12 Nones, avg time 4m 28s, avg turns 21.2
  - Attempt times: [3m 60s, 5m 3s, 5m 2s, 1m 56s, 5m 1s, 5m 7s, 3m 6s, 5m 3s, 5m 0s, 5m 1s, 5m 2s, 1m 7s, 5m 2s, 5m 1s, 5m 0s, 5m 54s]
  - Attempt turns: [16, 37, 17, 15, 30, 27, 12, 27, 25, 24, 29, 3, 14, 34, 23, 6]

**dbbfe8** (#97, started 308.0 min):
  - 16 attempts, 12 Nones, avg time 4m 46s, avg turns 19.2
  - Attempt times: [4m 2s, 5m 13s, 5m 0s, 5m 0s, 5m 1s, 3m 39s, 5m 2s, 5m 27s, 5m 11s, 5m 8s, 5m 1s, 2m 12s, 4m 7s, 5m 27s, 5m 16s, 5m 30s]
  - Attempt turns: [10, 36, 27, 28, 20, 13, 16, 17, 8, 35, 11, 15, 20, 21, 25, 5]

## 6. Order vs Correctness — Are Later Problems Less Accurate?

### Accuracy by Quintile (run position)

| Quintile | Problems | Correct | Wrong | Accuracy | Avg Time |
|----------|----------|---------|-------|----------|----------|
| Q1 (#1-19) | 19 | 18 | 1 | 95% | 3m 29s |
| Q2 (#20-38) | 19 | 11 | 8 | 58% | 2m 45s |
| Q3 (#39-58) | 20 | 16 | 4 | 80% | 1m 54s |
| Q4 (#59-77) | 19 | 16 | 3 | 84% | 3m 43s |
| Q5 (#78-97) | 20 | 4 | 16 | 20% | 4m 20s |

### Rolling Accuracy (window=10)

| Window | Problems | Correct | Accuracy | Cumul Time |
|--------|----------|---------|----------|------------|
| #1-10 | 10 | 9 | 90% | 53.2 min |
| #11-20 | 10 | 10 | 100% | 67.4 min |
| #21-30 | 10 | 5 | 50% | 103.8 min |
| #31-40 | 10 | 7 | 70% | 120.0 min |
| #41-50 | 10 | 9 | 90% | 135.4 min |
| #51-60 | 10 | 7 | 70% | 159.0 min |
| #61-70 | 10 | 7 | 70% | 213.2 min |
| #71-80 | 10 | 9 | 90% | 239.5 min |
| #81-90 | 10 | 1 | 10% | 278.3 min |
| #91-97 | 7 | 1 | 14% | 313.5 min |

## 7. Cumulative Runtime Timeline — All Problems

Each problem plotted against the 300 min budget. Wrong problems marked with `***`.

```
  #      PID Batch                   Start      End     Wall     Status  Timeline (5min=|)
--------------------------------------------------------------------------------------------------------------
  1   86e8e5 PRIORITY DEBUG (dual     0.0m    13.5m     812s    CORRECT  ===                                                         |    
  2   86e8e5 PRIORITY DEBUG (dual    13.5m    25.5m     715s   ***WRONG    ####                                                      |    
  3   76aef9 PRIORITY DEBUG (dual    25.5m    29.8m     260s    CORRECT       =                                                      |    
  4   76aef9 PRIORITY DEBUG (dual    29.8m    33.6m     226s    CORRECT       ==                                                     |    
  5   424e18 AT-RISK PROBLEMS        33.6m    36.1m     154s    CORRECT        ==                                                    |    
  6   dd7f5e AT-RISK PROBLEMS        36.1m    41.0m     288s    CORRECT         ==                                                   |    
  7   b4ec47 AT-RISK PROBLEMS        41.0m    45.2m     256s    CORRECT          ==                                                  |    
  8   2d282e AT-RISK PROBLEMS        45.2m    46.1m      53s    CORRECT           =                                                  |    
  9   8fea51 AT-RISK PROBLEMS        46.1m    49.2m     184s    CORRECT           =                                                  |    
 10   269012 AT-RISK PROBLEMS        49.2m    53.2m     244s    CORRECT           ==                                                 |    
 11   06788e VAL BENCH (new unsee    53.2m    54.0m      47s    CORRECT            =                                                 |    
 12   095efa VAL BENCH (new unsee    54.0m    54.2m      11s    CORRECT            =                                                 |    
 13   0aa751 VAL BENCH (new unsee    54.2m    54.4m      14s    CORRECT            =                                                 |    
 14   0c55f3 VAL BENCH (new unsee    54.4m    58.5m     243s    CORRECT            ==                                                |    
 15   12a146 VAL BENCH (new unsee    58.5m    58.9m      23s    CORRECT             =                                                |    
 16   1363c5 VAL BENCH (new unsee    58.9m    62.4m     210s    CORRECT             ==                                               |    
 17   14f73f VAL BENCH (new unsee    62.4m    63.9m      91s    CORRECT              =                                               |    
 18   170362 VAL BENCH (new unsee    63.9m    65.5m      97s    CORRECT              ==                                              |    
 19   17a3b6 VAL BENCH (new unsee    65.5m    66.1m      38s    CORRECT               =                                              |    
 20   17fb59 VAL BENCH (new unsee    66.1m    67.4m      75s    CORRECT               =                                              |    
 21   19570e VAL BENCH (new unsee    67.4m    72.1m     282s    CORRECT               ==                                             |    
 22   1ec970 VAL BENCH (new unsee    72.1m    77.5m     327s   ***WRONG                ##                                            |    
 23   21fb4e VAL BENCH (new unsee    77.5m    83.0m     330s   ***WRONG                 ##                                           |    
 24   23586c VAL BENCH (new unsee    83.0m    83.6m      36s   ***WRONG                  #                                           |    
 25   26bee3 VAL BENCH (new unsee    83.6m    88.8m     311s   ***WRONG                  ##                                          |    
 26   27cec1 VAL BENCH (new unsee    88.8m    92.3m     211s    CORRECT                   ==                                         |    
 27   29714f VAL BENCH (new unsee    92.3m    96.4m     243s   ***WRONG                    ##                                        |    
 28   2c40d6 VAL BENCH (new unsee    96.4m    98.8m     143s    CORRECT                     =                                        |    
 29   2e2ccb VAL BENCH (new unsee    98.8m   101.8m     183s    CORRECT                     ==                                       |    
 30   3070ea VAL BENCH (new unsee   101.8m   103.8m     118s    CORRECT                      =                                       |    
 31   32690e VAL BENCH (new unsee   103.8m   104.2m      22s    CORRECT                      =                                       |    
 32   3980cd VAL BENCH (new unsee   104.2m   108.9m     282s   ***WRONG                      ##                                      |    
 33   3b88b3 VAL BENCH (new unsee   108.9m   110.5m     100s   ***WRONG                       ##                                     |    
 34   3cf8bf VAL BENCH (new unsee   110.5m   111.1m      37s    CORRECT                        =                                     |    
 35   3e5546 VAL BENCH (new unsee   111.1m   112.2m      62s    CORRECT                        =                                     |    
 36   3edbcf VAL BENCH (new unsee   112.2m   113.5m      77s    CORRECT                        =                                     |    
 37   3eee67 VAL BENCH (new unsee   113.5m   117.3m     227s    CORRECT                        ==                                    |    
 38   414a5b VAL BENCH (new unsee   117.3m   118.5m      74s   ***WRONG                         #                                    |    
 39   443a0e VAL BENCH (new unsee   118.5m   119.5m      62s    CORRECT                         =                                    |    
 40   481584 VAL BENCH (new unsee   119.5m   120.0m      28s    CORRECT                         =                                    |    
 41   485d27 VAL BENCH (new unsee   120.0m   123.1m     184s    CORRECT                         ==                                   |    
 42   4985d4 VAL BENCH (new unsee   123.1m   123.6m      32s    CORRECT                          =                                   |    
 43   4ebdaa VAL BENCH (new unsee   123.6m   124.1m      32s    CORRECT                          =                                   |    
 44   53de2d VAL BENCH (new unsee   124.1m   126.0m     115s    CORRECT                          ==                                  |    
 45   581a58 VAL BENCH (new unsee   126.0m   130.2m     249s    CORRECT                           ==                                 |    
 46   673b29 VAL BENCH (new unsee   130.2m   130.9m      42s   ***WRONG                            #                                 |    
 47   676ce2 VAL BENCH (new unsee   130.9m   132.8m     114s    CORRECT                            =                                 |    
 48   69e477 VAL BENCH (new unsee   132.8m   133.7m      55s    CORRECT                            =                                 |    
 49   6c042a VAL BENCH (new unsee   133.7m   134.2m      32s    CORRECT                            =                                 |    
 50   6c1fb9 VAL BENCH (new unsee   134.2m   135.4m      70s    CORRECT                            ==                                |    
 51   72a159 VAL BENCH (new unsee   135.4m   136.3m      54s    CORRECT                             =                                |    
 52   777281 VAL BENCH (new unsee   136.3m   137.8m      91s    CORRECT                             =                                |    
 53   89c921 VAL BENCH (new unsee   137.8m   140.9m     183s   ***WRONG                             ##                               |    
 54   9010d9 VAL BENCH (new unsee   140.9m   143.1m     136s   ***WRONG                              #                               |    
 55   9bfdb0 VAL BENCH (new unsee   143.1m   149.9m     405s    CORRECT                              ==                              |    
 56   a240b5 VAL BENCH (new unsee   149.9m   150.9m      62s    CORRECT                               ==                             |    
 57   a7b83d VAL BENCH (new unsee   150.9m   152.6m     100s    CORRECT                                =                             |    
 58   a824c1 VAL BENCH (new unsee   152.6m   156.4m     229s   ***WRONG                                ##                            |    
 59   a83f0b VAL BENCH (new unsee   156.4m   157.9m      89s    CORRECT                                 =                            |    
 60   a86319 VAL BENCH (new unsee   157.9m   159.0m      68s    CORRECT                                 =                            |    
 61   a9dbc8 VAL BENCH (new unsee   159.0m   165.5m     388s   ***WRONG                                 ###                          |    
 62   ac93ce VAL BENCH (new unsee   165.5m   166.6m      65s    CORRECT                                   =                          |    
 63   ae2add VAL BENCH (new unsee   166.6m   169.3m     165s   ***WRONG                                   #                          |    
 64   aff75c VAL BENCH (new unsee   169.3m   179.6m     614s   ***WRONG                                   ###                        |    
 65   b286eb VAL BENCH (new unsee   179.6m   181.8m     136s    CORRECT                                     ==                       |    
 66   ba89f9 VAL BENCH (new unsee   181.8m   188.3m     388s    CORRECT                                      ==                      |    
 67   bad5bf VAL BENCH (new unsee   188.3m   190.6m     138s    CORRECT                                       ==                     |    
 68   c19295 VAL BENCH (new unsee   190.6m   206.0m     922s    CORRECT                                        ====                  |    
 69   c4d8d5 VAL BENCH (new unsee   206.0m   208.0m     120s    CORRECT                                           =                  |    
 70   c9a608 VAL BENCH (new unsee   208.0m   213.2m     317s    CORRECT                                           ==                 |    
 71   ca2a54 VAL BENCH (new unsee   213.2m   216.0m     166s    CORRECT                                            ==                |    
 72   cbbc1b VAL BENCH (new unsee   216.0m   218.7m     159s    CORRECT                                             =                |    
 73   cf3142 VAL BENCH (new unsee   218.7m   220.8m     126s    CORRECT                                             ==               |    
 74   d5054a VAL BENCH (new unsee   220.8m   222.1m      82s    CORRECT                                              =               |    
 75   d5f758 VAL BENCH (new unsee   222.1m   223.3m      72s    CORRECT                                              =               |    
 76   d6f389 VAL BENCH (new unsee   223.3m   224.0m      40s    CORRECT                                              =               |    
 77   d75200 VAL BENCH (new unsee   224.0m   227.0m     181s    CORRECT                                              ==              |    
 78   dbbfe8 VAL BENCH (new unsee   227.0m   234.9m     475s   ***WRONG                                               ##             |    
 79   ddba8e VAL BENCH (new unsee   234.9m   237.1m     128s    CORRECT                                                ==            |    
 80   e5a7c0 VAL BENCH (new unsee   237.1m   239.5m     146s    CORRECT                                                 =            |    
 81   86e8e5 DOUBLE-RUN RETRY       239.5m   245.0m     331s   ***WRONG                                                 ###          |    
 82   1ec970 DOUBLE-RUN RETRY       245.0m   250.5m     328s   ***WRONG                                                   ##         |    
 83   21fb4e DOUBLE-RUN RETRY       250.5m   255.8m     322s   ***WRONG                                                    ##        |    
 84   23586c DOUBLE-RUN RETRY       255.8m   257.2m      80s   ***WRONG                                                     #        |    
 85   26bee3 DOUBLE-RUN RETRY       257.2m   262.7m     331s   ***WRONG                                                     ##       |    
 86   29714f DOUBLE-RUN RETRY       262.7m   267.7m     299s   ***WRONG                                                      ##      |    
 87   3980cd DOUBLE-RUN RETRY       267.7m   272.4m     286s   ***WRONG                                                       ##     |    
 88   3b88b3 DOUBLE-RUN RETRY       272.4m   274.4m     115s   ***WRONG                                                        #     |    
 89   414a5b DOUBLE-RUN RETRY       274.4m   277.0m     159s    CORRECT                                                        ==    |    
 90   673b29 DOUBLE-RUN RETRY       277.0m   278.3m      79s   ***WRONG                                                         #    |    
 91   89c921 DOUBLE-RUN RETRY       278.3m   283.4m     304s    CORRECT                                                         ==   |    
 92   9010d9 DOUBLE-RUN RETRY       283.4m   286.7m     196s   ***WRONG                                                          ##  |    
 93   a824c1 DOUBLE-RUN RETRY       286.7m   291.1m     264s   ***WRONG                                                           ## |    
 94   a9dbc8 DOUBLE-RUN RETRY       291.1m   296.6m     330s   ***WRONG                                                            ##|    
 95   ae2add DOUBLE-RUN RETRY       296.6m   302.1m     332s   ***WRONG                                                             ##    
 96   aff75c DOUBLE-RUN RETRY       302.1m   308.0m     354s   ***WRONG                                                              ##   
 97   dbbfe8 DOUBLE-RUN RETRY       308.0m   313.5m     330s   ***WRONG                                                              |##  
```

Legend: `=` = correct problem time span, `#` = wrong problem, `|` at position 60 = 300 min budget

## 8. Val Bench Batch — Were Failures Concentrated at the End?

**Val Bench total**: 70 problems, 54 correct, 16 wrong

### Val Bench Accuracy by Quarter (within batch)

| Quarter | Problems | Correct | Wrong | Accuracy | Time Range (min) |
|---------|----------|---------|-------|----------|------------------|
| Q1 (1-17) | 17 | 12 | 5 | 71% | 53-96 |
| Q2 (18-35) | 18 | 15 | 3 | 83% | 96-130 |
| Q3 (36-52) | 17 | 12 | 5 | 71% | 130-167 |
| Q4 (53-70) | 18 | 15 | 3 | 83% | 167-239 |

### Val Bench Wrong Problems — Positions Within Batch

| Batch Pos | Global # | Problem ID | Start (min) | End (min) | Wall Time | Attempts |
|-----------|----------|-----------|-------------|-----------|-----------|----------|
| 12/70 | #22 | 1ec970 | 72.1 | 77.5 | 5m 27s | 16 |
| 13/70 | #23 | 21fb4e | 77.5 | 83.0 | 5m 30s | 16 |
| 14/70 | #24 | 23586c | 83.0 | 83.6 | 36.0s | 16 |
| 15/70 | #25 | 26bee3 | 83.6 | 88.8 | 5m 11s | 16 |
| 17/70 | #27 | 29714f | 92.3 | 96.4 | 4m 3s | 16 |
| 22/70 | #32 | 3980cd | 104.2 | 108.9 | 4m 42s | 16 |
| 23/70 | #33 | 3b88b3 | 108.9 | 110.5 | 1m 40s | 16 |
| 28/70 | #38 | 414a5b | 117.3 | 118.5 | 1m 14s | 16 |
| 36/70 | #46 | 673b29 | 130.2 | 130.9 | 41.7s | 16 |
| 43/70 | #53 | 89c921 | 137.8 | 140.9 | 3m 3s | 16 |
| 44/70 | #54 | 9010d9 | 140.9 | 143.1 | 2m 16s | 16 |
| 48/70 | #58 | a824c1 | 152.6 | 156.4 | 3m 49s | 16 |
| 51/70 | #61 | a9dbc8 | 159.0 | 165.5 | 6m 28s | 16 |
| 53/70 | #63 | ae2add | 166.6 | 169.3 | 2m 45s | 16 |
| 54/70 | #64 | aff75c | 169.3 | 179.6 | 10m 14s | 16 |
| 68/70 | #78 | dbbfe8 | 227.0 | 234.9 | 7m 55s | 16 |

**First half**: 8/35 wrong (23%)
**Second half**: 8/35 wrong (23%)

## 9. DOUBLE-RUN RETRY Batch — Critical Structural Insight

**The DOUBLE-RUN RETRY batch re-runs the same problems that were already wrong.**
This means 15-17 of the 'late run' entries are NOT new failures — they are
second attempts at problems that already failed in their first batch.

**DOUBLE-RUN RETRY batch**: 17 entries, 2 correct, 15 wrong
**Non-retry entries**: 80 entries, 63 correct, 17 wrong

### First Run vs Retry — Same Problem Comparison

| Problem ID | First Batch | First Result | First Time | Retry Result | Retry Time | Changed? |
|-----------|-------------|--------------|------------|--------------|------------|----------|
| 1ec970 | VAL BENCH (new unsee | WRONG | 5m 27s | WRONG | 5m 28s | No |
| 21fb4e | VAL BENCH (new unsee | WRONG | 5m 30s | WRONG | 5m 22s | No |
| 23586c | VAL BENCH (new unsee | WRONG | 36.0s | WRONG | 1m 20s | No |
| 26bee3 | VAL BENCH (new unsee | WRONG | 5m 11s | WRONG | 5m 31s | No |
| 29714f | VAL BENCH (new unsee | WRONG | 4m 3s | WRONG | 4m 59s | No |
| 3980cd | VAL BENCH (new unsee | WRONG | 4m 42s | WRONG | 4m 46s | No |
| 3b88b3 | VAL BENCH (new unsee | WRONG | 1m 40s | WRONG | 1m 55s | No |
| 414a5b | VAL BENCH (new unsee | WRONG | 1m 14s | CORRECT | 2m 39s | YES |
| 673b29 | VAL BENCH (new unsee | WRONG | 41.7s | WRONG | 1m 19s | No |
| 86e8e5 | PRIORITY DEBUG (dual | CORRECT | 13m 32s | WRONG | 5m 31s | YES |
| 89c921 | VAL BENCH (new unsee | WRONG | 3m 3s | CORRECT | 5m 4s | YES |
| 9010d9 | VAL BENCH (new unsee | WRONG | 2m 16s | WRONG | 3m 16s | No |
| a824c1 | VAL BENCH (new unsee | WRONG | 3m 49s | WRONG | 4m 24s | No |
| a9dbc8 | VAL BENCH (new unsee | WRONG | 6m 28s | WRONG | 5m 30s | No |
| ae2add | VAL BENCH (new unsee | WRONG | 2m 45s | WRONG | 5m 32s | No |
| aff75c | VAL BENCH (new unsee | WRONG | 10m 14s | WRONG | 5m 54s | No |
| dbbfe8 | VAL BENCH (new unsee | WRONG | 7m 55s | WRONG | 5m 30s | No |

**Stayed correct**: 0
**Flipped to correct (retry helped)**: 2
**Stayed wrong (retry useless)**: 14
**Flipped to wrong (retry hurt)**: 1

### Q6 Corrected — Order vs Correctness (Excluding DOUBLE-RUN RETRY)

| Quintile | Problems | Correct | Wrong | Accuracy |
|----------|----------|---------|-------|----------|
| Q1 (#1-16) | 16 | 15 | 1 | 94% |
| Q2 (#17-32) | 16 | 10 | 6 | 62% |
| Q3 (#33-48) | 16 | 13 | 3 | 81% |
| Q4 (#49-64) | 16 | 10 | 6 | 62% |
| Q5 (#65-80) | 16 | 15 | 1 | 94% |

(This is the real test — without the retry batch artificially inflating late failures.)

## 10. Retry Batch — Were Retries Hurt by Time Pressure or Model Degradation?

**29714f**: [MORE ERRORS]
  - First: 8 answered, 8 Nones, 10 errors, 4m 3s
  - Retry: 8 answered, 8 Nones, 17 errors, 4m 59s

**414a5b**: [MORE ERRORS]
  - First: 7 answered, 9 Nones, 3 errors, 1m 14s
  - Retry: 14 answered, 2 Nones, 5 errors, 2m 39s

**86e8e5**: [MORE NONES] [FEWER ANSWERS]
  - First: 14 answered, 2 Nones, 61 errors, 13m 32s
  - Retry: 2 answered, 14 Nones, 28 errors, 5m 31s

**89c921**: [MORE ERRORS]
  - First: 5 answered, 11 Nones, 5 errors, 3m 3s
  - Retry: 9 answered, 7 Nones, 8 errors, 5m 4s

**a9dbc8**: [MORE NONES] [FEWER ANSWERS]
  - First: 8 answered, 8 Nones, 24 errors, 6m 28s
  - Retry: 4 answered, 12 Nones, 26 errors, 5m 30s

**ae2add**: [MORE ERRORS]
  - First: 7 answered, 9 Nones, 4 errors, 2m 45s
  - Retry: 9 answered, 7 Nones, 17 errors, 5m 32s

**aff75c**: [MORE NONES] [FEWER ANSWERS]
  - First: 16 answered, 0 Nones, 50 errors, 10m 14s
  - Retry: 4 answered, 12 Nones, 43 errors, 5m 54s

**dbbfe8**: [MORE NONES] [FEWER ANSWERS]
  - First: 10 answered, 6 Nones, 123 errors, 7m 55s
  - Retry: 4 answered, 12 Nones, 75 errors, 5m 30s

**Aggregate (across all retried problems)**:
  - First run: 134 total answered, 138 total Nones
  - Retry:     105 total answered, 167 total Nones
  - None increase: +29 (+21%)

## 11. Summary & Key Findings

### Stats (First-Run Only — Excluding DOUBLE-RUN RETRY)

1. **Average position of wrong problems**: #39.1 (vs overall avg #40.5)
   -> Wrong problems are NOT biased toward late positions

2. **Average start time of wrong problems**: 191.0 min (vs overall avg 147.8 min)

3. **Wrong problems starting after 300 min**: 2
   **Wrong problems starting after 270 min**: 10

4. **Attempt counts**: Wrong problems avg 16.0 attempts vs correct avg 16.0
   **Cut short (< 5 attempts)**: 0 problems

5. **Timing**: Wrong problems avg 4m 43s vs correct avg 2m 37s
   -> Wrong problems took 1.8x longer (harder, more attempts)

6. **Failure rate by batch**:
   - VAL BENCH (new unseen): 16/70 wrong (23%)
   - DOUBLE-RUN RETRY: 15/17 wrong (88%)
   - PRIORITY DEBUG (dual-run): 1/4 wrong (25%)

### Verdict: Did Time Pressure Cause Failures?

**YES (partially)**: 2 wrong problem(s) started AFTER the 300 min budget.
  - aff75c: started at 302.1 min
  - dbbfe8: started at 308.0 min
