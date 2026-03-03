# Wrong Problems Deep Dive — v23

**Log**: `output/v23/diagnostic.log`
**Total wrong problems**: 17
**Analysis**: Full vote tables, per-attempt detail, classification, temperature patterns, entropy signals

## Table of Contents

- [1ec970 (expected 8700)](#problem-1ec970--expected-8700-predicted-5000)
- [21fb4e (expected 16)](#problem-21fb4e--expected-16-predicted-17)
- [23586c (expected 386)](#problem-23586c--expected-386-predicted-773)
- [26bee3 (expected 108)](#problem-26bee3--expected-108-predicted-97)
- [29714f (expected 297)](#problem-29714f--expected-297-predicted-99)
- [3980cd (expected 46)](#problem-3980cd--expected-46-predicted-642)
- [3b88b3 (expected 979)](#problem-3b88b3--expected-979-predicted-982)
- [414a5b (expected 42)](#problem-414a5b--expected-42-predicted-95)
- [673b29 (expected 3)](#problem-673b29--expected-3-predicted-3032)
- [86e8e5 (expected 8687)](#problem-86e8e5--expected-8687-predicted-8687)
- [89c921 (expected 29800)](#problem-89c921--expected-29800-predicted-39601)
- [9010d9 (expected 10320)](#problem-9010d9--expected-10320-predicted-6400)
- [a824c1 (expected 24)](#problem-a824c1--expected-24-predicted-13)
- [a9dbc8 (expected 15744)](#problem-a9dbc8--expected-15744-predicted-15743)
- [ae2add (expected 24931)](#problem-ae2add--expected-24931-predicted-19945)
- [aff75c (expected 3571)](#problem-aff75c--expected-3571-predicted-3600)
- [dbbfe8 (expected 22)](#problem-dbbfe8--expected-22-predicted-8)
- [Cross-Problem Summary](#cross-problem-summary)

---

================================================================================
## Problem `1ec970` — Expected: **8700**, Predicted: **5000**
================================================================================

- **Runs**: 2 (dual-run), **32** total attempts
- **Classification**: **Never found**
- **None rate**: 25/32 (78%)
- **Correct answer found**: NO — never appeared in any attempt

### Vote Distribution

| Answer | Votes | % of answered |
| ------ | ----: | ------------: |
| 9900   |     3 |           43% |
| 5000   |     2 |           29% |
| 4950   |     1 |           14% |
| 7450   |     1 |           14% |
| None   |    25 |           78% |

### Run 1 — Per-Attempt Detail

Predicted: 5000, Early stop: False, Votes: {5000: 2, 9900: 1, 4950: 1, 7450: 1}

| Att# | Temp | Answer | Entropy | Code | Errors | Time  | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ----: | -----: |
|    1 |  0.1 | None   |   0.788 |   21 |      3 |  5.1m |  15726 |
|    2 |  0.3 | 5000   |   0.984 |    0 |      0 | 56.9s |   4801 |
|    3 |  0.3 | None   |   0.774 |   22 |      0 |  5.0m |  25345 |
|    4 |  0.3 | None   |   0.798 |   19 |      1 |  5.0m |  18096 |
|    5 |  0.3 | 4950   |   0.890 |    3 |      0 |  1.5m |   7292 |
|    6 |  0.5 | None   |   0.729 |   22 |      1 |  5.3m |  10491 |
|    7 |  0.5 | 9900   |   0.927 |    3 |      0 |  1.1m |   5445 |
|    8 |  0.5 | None   |   0.791 |   22 |      3 |  5.4m |  12034 |
|    9 |  0.5 | None   |   0.750 |   23 |      6 |  5.0m |  17751 |
|   10 |  0.5 | 5000   |   1.043 |    0 |      0 | 31.9s |   2801 |
|   11 |  0.5 | None   |   0.793 |   13 |      1 |  5.1m |  19389 |
|   12 |  0.7 | None   |   0.794 |   22 |      0 |  5.0m |  19908 |
|   13 |  0.7 | 7450   |   0.781 |   20 |      2 |  4.1m |  12563 |
|   14 |  0.7 | None   |   0.855 |   13 |      2 |  5.2m |  18918 |
|   15 |  0.7 | None   |   0.747 |   22 |      2 |  5.0m |  14424 |
|   16 |  0.9 | None   |   0.854 |   34 |      1 |  5.2m |  16965 |

### Run 2 — Per-Attempt Detail

Predicted: 9900, Early stop: False, Votes: {9900: 2}

| Att# | Temp | Answer | Entropy | Code | Errors | Time | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ---: | -----: |
|    1 |  0.1 | None   |   0.681 |   14 |      3 | 5.0m |  13907 |
|    2 |  0.3 | None   |   0.684 |   23 |      1 | 5.5m |  14174 |
|    3 |  0.3 | None   |   0.773 |   22 |      3 | 5.0m |  11916 |
|    4 |  0.3 | None   |   0.782 |   39 |      0 | 5.2m |  21829 |
|    5 |  0.3 | None   |   0.678 |   20 |      3 | 5.0m |  12481 |
|    6 |  0.5 | 9900   |   0.868 |    5 |      0 | 1.4m |   6587 |
|    7 |  0.5 | None   |   0.763 |   23 |      2 | 5.0m |  11619 |
|    8 |  0.5 | None   |   0.831 |   16 |      3 | 5.0m |  10788 |
|    9 |  0.5 | None   |   0.743 |   26 |      0 | 5.0m |  23935 |
|   10 |  0.5 | None   |   0.835 |   17 |      2 | 5.0m |  16344 |
|   11 |  0.5 | None   |   0.794 |   28 |      2 | 5.0m |  21853 |
|   12 |  0.7 | None   |   0.831 |   23 |      3 | 5.0m |  13456 |
|   13 |  0.7 | None   |   0.738 |   29 |      2 | 5.0m |  22893 |
|   14 |  0.7 | None   |   0.755 |   16 |      1 | 5.0m |  17023 |
|   15 |  0.7 | None   |   0.761 |   23 |      4 | 5.1m |  10763 |
|   16 |  0.9 | 9900   |   0.873 |    4 |      4 | 5.3m |  13462 |

### Correct Answer Analysis

Correct answer **8700** was **NEVER** found in any of the 32 attempts across 2 run(s).

Closest answer: **9900** (off by 1200)

### Code Calls vs No-Code Analysis

| Group          | Answered | None     | Correct | Avg code calls |
| -------------- | -------: | -------: | ------: | -------------: |
| With code (30) |  5 (17%) | 25 (83%) |  0 (0%) |           19.6 |
| No code (2)    | 2 (100%) |   0 (0%) |  0 (0%) |              0 |

### Entropy Signal

- No correct attempts found. Wrong attempts avg entropy: **0.909**

---

================================================================================
## Problem `21fb4e` — Expected: **16**, Predicted: **17**
================================================================================

- **Runs**: 2 (dual-run), **32** total attempts
- **Classification**: **Outvoted**
- **None rate**: 18/32 (56%)
- **Correct answer found**: YES — in 2 attempt(s)
- **Temps that found correct**: 0.5, 0.7
- **Run(s) that found correct**: 1

### Vote Distribution

| Answer           | Votes | % of answered |
| ---------------- | ----: | ------------: |
| 17               |     9 |           64% |
| 16 **(CORRECT)** |     2 |           14% |
| 7                |     2 |           14% |
| 81               |     1 |            7% |
| None             |    18 |           56% |

### Run 1 — Per-Attempt Detail

Predicted: 17, Early stop: False, Votes: {17: 4, 16: 2}

| Att# | Temp | Answer     | Entropy | Code | Errors | Time | Tokens |
| ---: | ---: | ---------- | ------: | ---: | -----: | ---: | -----: |
|    1 |  0.1 | None       |   0.480 |   33 |     13 | 5.5m |  10821 |
|    2 |  0.3 | None       |   0.529 |   20 |     10 | 5.0m |   9113 |
|    3 |  0.3 | None       |   0.584 |   24 |      5 | 5.0m |   9998 |
|    4 |  0.3 | None       |   0.610 |   24 |      8 | 5.3m |   8841 |
|    5 |  0.3 | 17         |   0.667 |   20 |      2 | 2.3m |   9925 |
|    6 |  0.5 | None       |   0.516 |   34 |     12 | 5.0m |  13257 |
|    7 |  0.5 | 17         |   0.665 |   20 |      4 | 4.6m |  14233 |
|    8 |  0.5 | 17         |   0.589 |   27 |      9 | 4.6m |  14458 |
|    9 |  0.5 | None       |   0.681 |   19 |      7 | 5.0m |  14572 |
|   10 |  0.5 | 16 **[C]** |   0.610 |   22 |      3 | 3.6m |   9754 |
|   11 |  0.5 | None       |   0.597 |   26 |      6 | 5.1m |  13619 |
|   12 |  0.7 | 17         |   0.675 |   17 |      3 | 3.1m |   7301 |
|   13 |  0.7 | None       |   0.572 |   29 |      7 | 5.1m |  12928 |
|   14 |  0.7 | 16 **[C]** |   0.572 |   31 |      7 | 4.2m |  10111 |
|   15 |  0.7 | None       |   0.620 |   29 |      8 | 5.4m |  11189 |
|   16 |  0.9 | None       |   0.663 |   25 |      7 | 5.1m |  12151 |

### Run 2 — Per-Attempt Detail

Predicted: 17, Early stop: True, Votes: {17: 5, 7: 2, 81: 1}

| Att# | Temp | Answer | Entropy | Code | Errors | Time  | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ----: | -----: |
|    1 |  0.1 | None   |   0.500 |   36 |     13 |  5.3m |  11802 |
|    2 |  0.3 | 17     |   0.691 |   14 |      3 |  3.5m |  16527 |
|    3 |  0.3 | 17     |   0.660 |   13 |      4 |  3.9m |   7836 |
|    4 |  0.3 | 17     |   0.542 |   20 |      7 |  4.8m |   9043 |
|    5 |  0.3 | None   |   0.555 |   26 |      7 |  5.1m |   8432 |
|    6 |  0.5 | None   |   0.511 |   43 |      6 |  4.9m |  12609 |
|    7 |  0.5 | None   |   0.653 |   20 |      7 |  4.9m |  16979 |
|    8 |  0.5 | None   |   0.654 |   29 |     12 |  4.9m |  15282 |
|    9 |  0.5 | 17     |   0.569 |   34 |      5 |  4.0m |  11123 |
|   10 |  0.5 | 17     |   0.604 |   23 |      7 |  1.2m |   7396 |
|   11 |  0.5 | 7      |   0.773 |    3 |      0 | 24.8s |   1835 |
|   12 |  0.7 | None   |   0.589 |   31 |     11 |  5.3m |  12470 |
|   13 |  0.7 | 7      |   0.650 |    4 |      0 | 24.4s |   1805 |
|   14 |  0.7 | 81     |   0.662 |   19 |      7 |  3.1m |   8430 |
|   15 |  0.7 | None   |   0.665 |    6 |      6 |  5.4m |  11418 |
|   16 |  0.9 | None   |   0.704 |   20 |      7 |  5.2m |  12535 |

### Correct Answer Analysis

Correct answer **16** was found by **2** of **32** attempts (6%).

Attempts that found correct:

| Run   | Att# | Temp | Entropy | Code | Errors | Time |
| ----- | ---: | ---: | ------: | ---: | -----: | ---: |
| Run 1 |   10 |  0.5 |   0.610 |   22 |      3 | 3.6m |
| Run 1 |   14 |  0.7 |   0.572 |   31 |      7 | 4.2m |

**Why it lost**: Correct got 2 vote(s) vs winner `17` with 9 vote(s).

### Code Calls vs No-Code Analysis

| Group          | Answered | None     | Correct | Avg code calls |
| -------------- | -------: | -------: | ------: | -------------: |
| With code (32) | 14 (44%) | 18 (56%) |  2 (6%) |           23.2 |

### Entropy Signal

- Correct attempts avg entropy: **0.591**
- Wrong attempts avg entropy: **0.646**
- None attempts avg entropy: **0.594**
- Signal: **Correct has LOWER entropy** (diff: 0.055) -- entropy weighting WOULD help

---

================================================================================
## Problem `23586c` — Expected: **386**, Predicted: **773**
================================================================================

- **Runs**: 2 (dual-run), **32** total attempts
- **Classification**: **Confident wrong**
- **None rate**: 20/32 (62%)
- **Correct answer found**: NO — never appeared in any attempt

### Vote Distribution

| Answer | Votes | % of answered |
| ------ | ----: | ------------: |
| 773    |    12 |          100% |
| None   |    20 |           62% |

### Run 1 — Per-Attempt Detail

Predicted: 773, Early stop: True, Votes: {773: 7}

| Att# | Temp | Answer | Entropy | Code | Errors | Time  | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ----: | -----: |
|    1 |  0.1 | None   |   0.754 |    1 |      0 | 30.1s |   2266 |
|    2 |  0.3 | None   |   0.832 |    1 |      0 | 29.8s |   2237 |
|    3 |  0.3 | 773    |   0.762 |    2 |      0 | 33.3s |   1830 |
|    4 |  0.3 | None   |   0.858 |    3 |      1 | 30.7s |   2335 |
|    5 |  0.3 | 773    |   0.773 |    2 |      0 | 28.3s |   2324 |
|    6 |  0.5 | None   |   0.831 |    0 |      0 | 30.9s |   2401 |
|    7 |  0.5 | 773    |   0.831 |    3 |      0 | 18.7s |   1599 |
|    8 |  0.5 | None   |   0.842 |    1 |      1 | 30.3s |   2299 |
|    9 |  0.5 | None   |   0.820 |    2 |      1 | 29.9s |   2403 |
|   10 |  0.5 | 773    |   0.814 |    3 |      0 | 26.8s |   2210 |
|   11 |  0.5 | 773    |   0.768 |    2 |      0 | 23.3s |   1952 |
|   12 |  0.7 | None   |   0.806 |    3 |      0 | 33.8s |   2252 |
|   13 |  0.7 | 773    |   0.796 |    3 |      0 | 35.9s |   2354 |
|   14 |  0.7 | None   |   0.880 |    3 |      0 | 30.8s |   2378 |
|   15 |  0.7 | None   |   0.822 |    2 |      0 | 30.3s |   2309 |
|   16 |  0.9 | 773    |   0.866 |    3 |      0 | 29.4s |   2407 |

### Run 2 — Per-Attempt Detail

Predicted: 773, Early stop: True, Votes: {773: 5}

| Att# | Temp | Answer | Entropy | Code | Errors | Time  | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ----: | -----: |
|    1 |  0.1 | 773    |   0.780 |    3 |      0 | 31.4s |   2575 |
|    2 |  0.3 | None   |   0.832 |    0 |      0 | 34.2s |   2601 |
|    3 |  0.3 | None   |   0.753 |    3 |      0 | 33.9s |   2556 |
|    4 |  0.3 | 773    |   0.817 |    2 |      0 | 32.8s |   2684 |
|    5 |  0.3 | None   |   0.818 |    1 |      0 | 34.1s |   2613 |
|    6 |  0.5 | None   |   0.752 |    2 |      1 | 33.6s |   2609 |
|    7 |  0.5 | None   |   0.864 |    2 |      0 | 33.9s |   2615 |
|    8 |  0.5 | None   |   0.812 |    3 |      0 | 34.1s |   2575 |
|    9 |  0.5 | None   |   0.813 |    3 |      0 | 34.8s |   2687 |
|   10 |  0.5 | None   |   0.819 |    2 |      0 | 34.5s |   2637 |
|   11 |  0.5 | 773    |   0.822 |    3 |      0 | 25.7s |   1931 |
|   12 |  0.7 | 773    |   0.793 |    4 |      0 | 26.1s |   2175 |
|   13 |  0.7 | None   |   0.862 |    3 |      0 | 34.5s |   2637 |
|   14 |  0.7 | None   |   0.877 |    0 |      0 | 34.2s |   2601 |
|   15 |  0.7 | 773    |   0.909 |    3 |      0 | 32.5s |   2654 |
|   16 |  0.9 | None   |   0.849 |    1 |      1 |  1.3m |   1717 |

### Correct Answer Analysis

Correct answer **386** was **NEVER** found in any of the 32 attempts across 2 run(s).

Closest answer: **773** (off by 387)

### Code Calls vs No-Code Analysis

| Group          | Answered | None     | Correct | Avg code calls |
| -------------- | -------: | -------: | ------: | -------------: |
| With code (29) | 12 (41%) | 17 (59%) |  0 (0%) |            2.4 |
| No code (3)    |   0 (0%) | 3 (100%) |  0 (0%) |              0 |

### Entropy Signal

- No correct attempts found. Wrong attempts avg entropy: **0.811**

---

================================================================================
## Problem `26bee3` — Expected: **108**, Predicted: **97**
================================================================================

- **Runs**: 2 (dual-run), **32** total attempts
- **Classification**: **Scattered**
- **None rate**: 21/32 (66%)
- **Correct answer found**: NO — never appeared in any attempt

### Vote Distribution

| Answer | Votes | % of answered |
| ------ | ----: | ------------: |
| 136    |     3 |           27% |
| 256    |     3 |           27% |
| 97     |     2 |           18% |
| 145    |     1 |            9% |
| 77     |     1 |            9% |
| 128    |     1 |            9% |
| None   |    21 |           66% |

### Run 1 — Per-Attempt Detail

Predicted: 97, Early stop: False, Votes: {128: 1, 256: 1, 145: 1, 77: 1, 97: 1, 136: 1}

| Att# | Temp | Answer | Entropy | Code | Errors | Time  | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ----: | -----: |
|    1 |  0.1 | None   |   0.671 |   21 |      3 |  5.0m |  12874 |
|    2 |  0.3 | None   |   0.747 |    8 |      2 |  5.0m |  17420 |
|    3 |  0.3 | None   |   0.766 |    7 |      3 |  5.0m |  20877 |
|    4 |  0.3 | 136    |   0.798 |    3 |      0 |  4.2m |  17177 |
|    5 |  0.3 | None   |   0.742 |   16 |      7 |  5.0m |  20742 |
|    6 |  0.5 | 97     |   0.759 |    9 |      1 |  3.4m |  12672 |
|    7 |  0.5 | None   |   0.794 |    2 |      0 |  5.0m |  24199 |
|    8 |  0.5 | None   |   0.716 |   16 |      3 |  5.0m |  14660 |
|    9 |  0.5 | None   |   0.783 |    5 |      0 |  5.0m |  22809 |
|   10 |  0.5 | None   |   0.765 |   11 |      1 |  5.0m |  19138 |
|   11 |  0.5 | None   |   0.826 |   14 |      2 |  5.0m |  23917 |
|   12 |  0.7 | 145    |   0.882 |    0 |      0 |  3.0m |  13801 |
|   13 |  0.7 | 77     |   0.765 |    9 |      2 |  3.4m |  12731 |
|   14 |  0.7 | None   |   0.768 |    5 |      3 |  5.2m |  20934 |
|   15 |  0.7 | 128    |   0.860 |    0 |      0 | 45.7s |   3601 |
|   16 |  0.9 | 256    |   0.916 |    0 |      0 |  2.1m |   9601 |

### Run 2 — Per-Attempt Detail

Predicted: 136, Early stop: False, Votes: {256: 2, 136: 2, 97: 1}

| Att# | Temp | Answer | Entropy | Code | Errors | Time | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ---: | -----: |
|    1 |  0.1 | 136    |   0.827 |    0 |      0 | 2.2m |  10801 |
|    2 |  0.3 | 136    |   0.804 |    3 |      0 | 3.5m |  15933 |
|    3 |  0.3 | None   |   0.827 |    2 |      0 | 5.0m |  21646 |
|    4 |  0.3 | None   |   0.770 |    7 |      0 | 5.0m |  21543 |
|    5 |  0.3 | None   |   0.763 |    3 |      0 | 5.0m |  21804 |
|    6 |  0.5 | None   |   0.756 |    6 |      2 | 5.0m |  21601 |
|    7 |  0.5 | None   |   0.729 |   21 |      5 | 5.4m |  15888 |
|    8 |  0.5 | None   |   0.775 |    5 |      0 | 5.0m |  21741 |
|    9 |  0.5 | 256    |   0.845 |    0 |      0 | 1.7m |   8601 |
|   10 |  0.5 | None   |   0.809 |    9 |      2 | 5.0m |  21559 |
|   11 |  0.5 | None   |   0.837 |    0 |      0 | 5.0m |  21801 |
|   12 |  0.7 | None   |   0.848 |    4 |      1 | 5.0m |  21767 |
|   13 |  0.7 | 97     |   0.767 |   14 |      1 | 4.6m |  16216 |
|   14 |  0.7 | 256    |   0.868 |    0 |      0 | 3.1m |  14401 |
|   15 |  0.7 | None   |   0.846 |    2 |      0 | 5.0m |  21637 |
|   16 |  0.9 | None   |   0.881 |    1 |      1 | 5.5m |  19814 |

### Correct Answer Analysis

Correct answer **108** was **NEVER** found in any of the 32 attempts across 2 run(s).

Closest answer: **97** (off by 11)

### Code Calls vs No-Code Analysis

| Group          | Answered | None     | Correct | Avg code calls |
| -------------- | -------: | -------: | ------: | -------------: |
| With code (25) |  5 (20%) | 20 (80%) |  0 (0%) |            8.1 |
| No code (7)    |  6 (86%) |  1 (14%) |  0 (0%) |              0 |

### Entropy Signal

- No correct attempts found. Wrong attempts avg entropy: **0.826**

---

================================================================================
## Problem `29714f` — Expected: **297**, Predicted: **99**
================================================================================

- **Runs**: 2 (dual-run), **32** total attempts
- **Classification**: **Outvoted**
- **None rate**: 16/32 (50%)
- **Correct answer found**: YES — in 2 attempt(s)
- **Temps that found correct**: 0.5 (2x)
- **Run(s) that found correct**: 1, 2

### Vote Distribution

| Answer            | Votes | % of answered |
| ----------------- | ----: | ------------: |
| 99                |    10 |           62% |
| 297 **(CORRECT)** |     2 |           12% |
| 4299              |     2 |           12% |
| 12135             |     1 |            6% |
| 4335              |     1 |            6% |
| None              |    16 |           50% |

### Run 1 — Per-Attempt Detail

Predicted: 99, Early stop: True, Votes: {99: 5, 4299: 1, 297: 1, 12135: 1}

| Att# | Temp | Answer      | Entropy | Code | Errors | Time | Tokens |
| ---: | ---: | ----------- | ------: | ---: | -----: | ---: | -----: |
|    1 |  0.1 | None        |   0.626 |   17 |      0 | 3.8m |  16252 |
|    2 |  0.3 | 99          |   0.643 |   10 |      0 | 1.5m |   6350 |
|    3 |  0.3 | None        |   0.629 |   19 |      0 | 3.8m |  15180 |
|    4 |  0.3 | 99          |   0.644 |   10 |      0 | 3.8m |  16350 |
|    5 |  0.3 | None        |   0.667 |    6 |      2 | 4.0m |  14419 |
|    6 |  0.5 | 297 **[C]** |   0.523 |   10 |      0 | 3.6m |  15070 |
|    7 |  0.5 | None        |   0.653 |    9 |      1 | 3.8m |  12296 |
|    8 |  0.5 | 99          |   0.647 |    5 |      0 | 1.9m |   8365 |
|    9 |  0.5 | 99          |   0.677 |   16 |      0 | 3.6m |  14846 |
|   10 |  0.5 | 12135       |   0.723 |    7 |      1 | 3.7m |  13668 |
|   11 |  0.5 | None        |   0.665 |   12 |      3 | 3.9m |  16217 |
|   12 |  0.7 | None        |   0.619 |   28 |      1 | 3.8m |  13273 |
|   13 |  0.7 | 99          |   0.596 |   17 |      0 | 3.0m |  12814 |
|   14 |  0.7 | 4299        |   0.612 |    6 |      0 | 3.3m |  13891 |
|   15 |  0.7 | None        |   0.663 |   11 |      0 | 3.8m |  16321 |
|   16 |  0.9 | None        |   0.663 |   20 |      2 | 3.8m |  11449 |

### Run 2 — Per-Attempt Detail

Predicted: 99, Early stop: True, Votes: {99: 5, 4299: 1, 297: 1, 4335: 1}

| Att# | Temp | Answer      | Entropy | Code | Errors | Time | Tokens |
| ---: | ---: | ----------- | ------: | ---: | -----: | ---: | -----: |
|    1 |  0.1 | 4335        |   0.587 |   14 |      0 | 4.3m |  18756 |
|    2 |  0.3 | 99          |   0.659 |   10 |      0 | 2.4m |   9571 |
|    3 |  0.3 | None        |   0.624 |   15 |      0 | 4.5m |  19237 |
|    4 |  0.3 | None        |   0.566 |   30 |      1 | 4.5m |  18255 |
|    5 |  0.3 | 99          |   0.688 |   16 |      0 | 3.0m |  12771 |
|    6 |  0.5 | 297 **[C]** |   0.670 |   19 |      1 | 4.0m |  16518 |
|    7 |  0.5 | None        |   0.607 |   26 |      4 | 4.9m |  14276 |
|    8 |  0.5 | None        |   0.647 |   25 |      0 | 4.5m |  17581 |
|    9 |  0.5 | 4299        |   0.645 |   17 |      1 | 3.3m |  13680 |
|   10 |  0.5 | None        |   0.655 |   17 |      2 | 4.6m |   9637 |
|   11 |  0.5 | 99          |   0.689 |    6 |      0 | 1.6m |   7413 |
|   12 |  0.7 | None        |   0.718 |   14 |      2 | 4.6m |  14967 |
|   13 |  0.7 | None        |   0.600 |   22 |      1 | 4.5m |  18841 |
|   14 |  0.7 | 99          |   0.682 |   15 |      1 | 4.5m |  16509 |
|   15 |  0.7 | 99          |   0.672 |   10 |      1 | 3.9m |  14540 |
|   16 |  0.9 | None        |   0.726 |    3 |      3 | 5.0m |  12682 |

### Correct Answer Analysis

Correct answer **297** was found by **2** of **32** attempts (6%).

Attempts that found correct:

| Run   | Att# | Temp | Entropy | Code | Errors | Time |
| ----- | ---: | ---: | ------: | ---: | -----: | ---: |
| Run 1 |    6 |  0.5 |   0.523 |   10 |      0 | 3.6m |
| Run 2 |    6 |  0.5 |   0.670 |   19 |      1 | 4.0m |

**Why it lost**: Correct got 2 vote(s) vs winner `99` with 10 vote(s).

### Code Calls vs No-Code Analysis

| Group          | Answered | None     | Correct | Avg code calls |
| -------------- | -------: | -------: | ------: | -------------: |
| With code (32) | 16 (50%) | 16 (50%) |  2 (6%) |           14.4 |

### Entropy Signal

- Correct attempts avg entropy: **0.597**
- Wrong attempts avg entropy: **0.655**
- None attempts avg entropy: **0.645**
- Signal: **Correct has LOWER entropy** (diff: 0.058) -- entropy weighting WOULD help

---

================================================================================
## Problem `3980cd` — Expected: **46**, Predicted: **642**
================================================================================

- **Runs**: 2 (dual-run), **32** total attempts
- **Classification**: **Outvoted**
- **None rate**: 14/32 (44%)
- **Correct answer found**: YES — in 3 attempt(s)
- **Temps that found correct**: 0.3, 0.5 (2x)
- **Run(s) that found correct**: 1, 2

### Vote Distribution

| Answer           | Votes | % of answered |
| ---------------- | ----: | ------------: |
| 642              |    10 |           56% |
| 46 **(CORRECT)** |     3 |           17% |
| 644              |     2 |           11% |
| 440              |     1 |            6% |
| 2                |     1 |            6% |
| 516              |     1 |            6% |
| None             |    14 |           44% |

### Run 1 — Per-Attempt Detail

Predicted: 642, Early stop: True, Votes: {642: 5, 644: 2, 46: 1, 440: 1, 2: 1}

| Att# | Temp | Answer     | Entropy | Code | Errors | Time | Tokens |
| ---: | ---: | ---------- | ------: | ---: | -----: | ---: | -----: |
|    1 |  0.1 | None       |   0.666 |   28 |      3 | 4.6m |  17965 |
|    2 |  0.3 | 644        |   0.703 |    0 |      0 | 1.1m |   5138 |
|    3 |  0.3 | None       |   0.680 |   16 |      3 | 4.7m |  15430 |
|    4 |  0.3 | 46 **[C]** |   0.592 |   27 |      1 | 3.3m |  14022 |
|    5 |  0.3 | 642        |   0.674 |   14 |      1 | 3.7m |  12792 |
|    6 |  0.5 | 644        |   0.635 |   11 |      1 | 3.3m |  13969 |
|    7 |  0.5 | 642        |   0.675 |   14 |      0 | 4.6m |  20984 |
|    8 |  0.5 | None       |   0.671 |   13 |      4 | 4.7m |  20944 |
|    9 |  0.5 | 642        |   0.703 |    2 |      0 | 2.9m |  12694 |
|   10 |  0.5 | 440        |   0.661 |   27 |      1 | 4.2m |  15800 |
|   11 |  0.5 | None       |   0.693 |   10 |      1 | 4.7m |  18758 |
|   12 |  0.7 | None       |   0.638 |   40 |      2 | 4.7m |  18223 |
|   13 |  0.7 | 642        |   0.724 |    0 |      0 | 1.4m |   6801 |
|   14 |  0.7 | 642        |   0.697 |    5 |      0 | 1.7m |   7763 |
|   15 |  0.7 | None       |   0.647 |   21 |      2 | 4.6m |  17993 |
|   16 |  0.9 | 2          |   0.702 |   18 |      3 | 4.4m |  17766 |

### Run 2 — Per-Attempt Detail

Predicted: 642, Early stop: True, Votes: {642: 5, 46: 2, 516: 1}

| Att# | Temp | Answer     | Entropy | Code | Errors | Time | Tokens |
| ---: | ---: | ---------- | ------: | ---: | -----: | ---: | -----: |
|    1 |  0.1 | None       |   0.681 |    2 |      1 | 4.3m |  18167 |
|    2 |  0.3 | 642        |   0.633 |   18 |      2 | 4.2m |  15790 |
|    3 |  0.3 | 516        |   0.652 |    6 |      0 | 2.6m |  11153 |
|    4 |  0.3 | None       |   0.660 |   15 |      3 | 4.3m |  15811 |
|    5 |  0.3 | None       |   0.693 |    4 |      0 | 4.3m |  18116 |
|    6 |  0.5 | 46 **[C]** |   0.716 |   14 |      0 | 3.4m |  14918 |
|    7 |  0.5 | None       |   0.718 |   14 |      1 | 4.3m |  16063 |
|    8 |  0.5 | None       |   0.681 |   25 |      0 | 4.3m |  17319 |
|    9 |  0.5 | None       |   0.705 |    3 |      0 | 4.2m |  17509 |
|   10 |  0.5 | 46 **[C]** |   0.764 |    1 |      0 | 1.8m |   8386 |
|   11 |  0.5 | 642        |   0.743 |    3 |      0 | 1.7m |   7791 |
|   12 |  0.7 | 642        |   0.678 |   20 |      0 | 3.8m |  16036 |
|   13 |  0.7 | 642        |   0.675 |   15 |      1 | 4.1m |  15379 |
|   14 |  0.7 | 642        |   0.808 |    5 |      0 | 1.6m |   7473 |
|   15 |  0.7 | None       |   0.701 |   16 |      2 | 4.3m |  12296 |
|   16 |  0.9 | None       |   0.706 |    4 |      4 | 4.8m |   9708 |

### Correct Answer Analysis

Correct answer **46** was found by **3** of **32** attempts (9%).

Attempts that found correct:

| Run   | Att# | Temp | Entropy | Code | Errors | Time |
| ----- | ---: | ---: | ------: | ---: | -----: | ---: |
| Run 1 |    4 |  0.3 |   0.592 |   27 |      1 | 3.3m |
| Run 2 |    6 |  0.5 |   0.716 |   14 |      0 | 3.4m |
| Run 2 |   10 |  0.5 |   0.764 |    1 |      0 | 1.8m |

**Why it lost**: Correct got 3 vote(s) vs winner `642` with 10 vote(s).

### Code Calls vs No-Code Analysis

| Group          | Answered | None     | Correct | Avg code calls |
| -------------- | -------: | -------: | ------: | -------------: |
| With code (30) | 16 (53%) | 14 (47%) | 3 (10%) |           13.7 |
| No code (2)    | 2 (100%) |   0 (0%) |  0 (0%) |              0 |

### Entropy Signal

- Correct attempts avg entropy: **0.691**
- Wrong attempts avg entropy: **0.691**
- None attempts avg entropy: **0.681**
- Signal: **Correct has LOWER entropy** (diff: 0.000) -- entropy weighting WOULD help

---

================================================================================
## Problem `3b88b3` — Expected: **979**, Predicted: **982**
================================================================================

- **Runs**: 2 (dual-run), **32** total attempts
- **Classification**: **Confident wrong**
- **None rate**: 22/32 (69%)
- **Correct answer found**: NO — never appeared in any attempt

### Vote Distribution

| Answer | Votes | % of answered |
| ------ | ----: | ------------: |
| 982    |    10 |          100% |
| None   |    22 |           69% |

### Run 1 — Per-Attempt Detail

Predicted: 982, Early stop: True, Votes: {982: 5}

| Att# | Temp | Answer | Entropy | Code | Errors | Time | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ---: | -----: |
|    1 |  0.1 | None   |   0.428 |    0 |      0 | 1.6m |   7401 |
|    2 |  0.3 | 982    |   0.390 |    6 |      0 | 1.4m |   6349 |
|    3 |  0.3 | None   |   0.441 |    3 |      1 | 1.6m |   7451 |
|    4 |  0.3 | None   |   0.480 |    7 |      0 | 1.6m |   6737 |
|    5 |  0.3 | None   |   0.416 |    0 |      0 | 1.6m |   7401 |
|    6 |  0.5 | None   |   0.415 |    3 |      1 | 1.6m |   7483 |
|    7 |  0.5 | None   |   0.423 |    6 |      0 | 1.6m |   7357 |
|    8 |  0.5 | 982    |   0.427 |    8 |      0 | 1.0m |   4875 |
|    9 |  0.5 | None   |   0.448 |    4 |      0 | 1.6m |   7295 |
|   10 |  0.5 | None   |   0.481 |    3 |      0 | 1.6m |   7455 |
|   11 |  0.5 | 982    |   0.430 |    3 |      0 | 1.2m |   5947 |
|   12 |  0.7 | 982    |   0.472 |    2 |      0 | 1.4m |   6508 |
|   13 |  0.7 | None   |   0.417 |    4 |      0 | 1.6m |   7329 |
|   14 |  0.7 | 982    |   0.499 |    5 |      0 | 1.6m |   7483 |
|   15 |  0.7 | None   |   0.484 |    8 |      2 | 1.6m |   4516 |
|   16 |  0.9 | None   |   0.481 |    2 |      0 | 1.7m |   7465 |

### Run 2 — Per-Attempt Detail

Predicted: 982, Early stop: True, Votes: {982: 5}

| Att# | Temp | Answer | Entropy | Code | Errors | Time | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ---: | -----: |
|    1 |  0.1 | 982    |   0.452 |    6 |      0 | 1.4m |   6445 |
|    2 |  0.3 | None   |   0.463 |    0 |      0 | 1.4m |   6601 |
|    3 |  0.3 | 982    |   0.417 |    3 |      0 | 1.0m |   5012 |
|    4 |  0.3 | None   |   0.470 |    2 |      0 | 1.4m |   6510 |
|    5 |  0.3 | None   |   0.474 |    5 |      0 | 1.4m |   6571 |
|    6 |  0.5 | 982    |   0.413 |    5 |      0 | 1.3m |   5982 |
|    7 |  0.5 | None   |   0.446 |    5 |      1 | 1.4m |   6470 |
|    8 |  0.5 | 982    |   0.470 |    6 |      0 | 1.4m |   6566 |
|    9 |  0.5 | None   |   0.443 |    3 |      0 | 1.4m |   6571 |
|   10 |  0.5 | None   |   0.487 |    1 |      0 | 1.4m |   6475 |
|   11 |  0.5 | None   |   0.406 |    0 |      0 | 1.4m |   6601 |
|   12 |  0.7 | None   |   0.427 |    5 |      0 | 1.4m |   6395 |
|   13 |  0.7 | 982    |   0.478 |    6 |      1 | 1.1m |   5424 |
|   14 |  0.7 | None   |   0.503 |    9 |      0 | 1.4m |   6477 |
|   15 |  0.7 | None   |   0.479 |    5 |      0 | 1.4m |   6583 |
|   16 |  0.9 | None   |   0.516 |    1 |      1 | 1.9m |   4275 |

### Correct Answer Analysis

Correct answer **979** was **NEVER** found in any of the 32 attempts across 2 run(s).

Closest answer: **982** (off by 3)

### Code Calls vs No-Code Analysis

| Group          | Answered | None     | Correct | Avg code calls |
| -------------- | -------: | -------: | ------: | -------------: |
| With code (28) | 10 (36%) | 18 (64%) |  0 (0%) |            4.5 |
| No code (4)    |   0 (0%) | 4 (100%) |  0 (0%) |              0 |

### Entropy Signal

- No correct attempts found. Wrong attempts avg entropy: **0.445**

---

================================================================================
## Problem `414a5b` — Expected: **42**, Predicted: **95**
================================================================================

- **Runs**: 2 (dual-run), **32** total attempts
- **Classification**: **Outvoted**
- **None rate**: 11/32 (34%)
- **Correct answer found**: YES — in 6 attempt(s)
- **Temps that found correct**: 0.3, 0.5 (3x), 0.7 (2x)
- **Run(s) that found correct**: 1, 2

### Vote Distribution

| Answer           | Votes | % of answered |
| ---------------- | ----: | ------------: |
| 95               |     9 |           43% |
| 42 **(CORRECT)** |     6 |           29% |
| 23               |     4 |           19% |
| 216              |     1 |            5% |
| 6                |     1 |            5% |
| None             |    11 |           34% |

### Run 1 — Per-Attempt Detail

Predicted: 95, Early stop: True, Votes: {95: 5, 42: 1, 23: 1}

| Att# | Temp | Answer     | Entropy | Code | Errors | Time  | Tokens |
| ---: | ---: | ---------- | ------: | ---: | -----: | ----: | -----: |
|    1 |  0.1 | None       |   0.664 |    9 |      0 |  1.2m |   5287 |
|    2 |  0.3 | None       |   0.730 |    3 |      0 |  1.2m |   5337 |
|    3 |  0.3 | 95         |   0.778 |    1 |      0 | 23.0s |   1864 |
|    4 |  0.3 | 95         |   0.691 |    1 |      0 | 25.8s |   2068 |
|    5 |  0.3 | 95         |   0.725 |    8 |      0 |  1.0m |   4534 |
|    6 |  0.5 | 95         |   0.734 |    6 |      0 |  1.2m |   5353 |
|    7 |  0.5 | None       |   0.762 |    6 |      0 |  1.2m |   5190 |
|    8 |  0.5 | None       |   0.754 |    4 |      1 |  1.2m |   5226 |
|    9 |  0.5 | 23         |   0.674 |    4 |      0 | 50.9s |   3847 |
|   10 |  0.5 | 42 **[C]** |   0.705 |    2 |      0 | 47.9s |   3647 |
|   11 |  0.5 | None       |   0.731 |    5 |      1 |  1.2m |   5224 |
|   12 |  0.7 | None       |   0.678 |    5 |      0 |  1.2m |   5258 |
|   13 |  0.7 | 95         |   0.752 |    3 |      0 |  1.0m |   4494 |
|   14 |  0.7 | None       |   0.709 |    5 |      1 |  1.2m |   5301 |
|   15 |  0.7 | None       |   0.732 |    5 |      0 |  1.2m |   5320 |
|   16 |  0.9 | None       |   0.805 |    4 |      0 |  1.2m |   5229 |

### Run 2 — Per-Attempt Detail

Predicted: 42, Early stop: True, Votes: {42: 5, 95: 4, 23: 3, 216: 1, 6: 1}

| Att# | Temp | Answer     | Entropy | Code | Errors | Time  | Tokens |
| ---: | ---: | ---------- | ------: | ---: | -----: | ----: | -----: |
|    1 |  0.1 | 216        |   0.722 |    0 |      0 | 17.0s |   1401 |
|    2 |  0.3 | 95         |   0.722 |    4 |      0 |  1.0m |   4581 |
|    3 |  0.3 | None       |   0.630 |    6 |      0 |  1.0m |   4604 |
|    4 |  0.3 | 95         |   0.727 |   12 |      0 |  1.7m |   8731 |
|    5 |  0.3 | 42 **[C]** |   0.653 |   11 |      1 |  1.8m |   9027 |
|    6 |  0.5 | 6          |   0.793 |    0 |      0 | 16.9s |   1401 |
|    7 |  0.5 | 42 **[C]** |   0.794 |    5 |      0 |  1.3m |   5911 |
|    8 |  0.5 | 23         |   0.645 |    0 |      0 | 42.1s |   3201 |
|    9 |  0.5 | 23         |   0.753 |    3 |      0 | 48.5s |   3633 |
|   10 |  0.5 | 95         |   0.792 |    7 |      0 |  1.8m |   9418 |
|   11 |  0.5 | 42 **[C]** |   0.702 |    8 |      0 |  1.6m |   7613 |
|   12 |  0.7 | 23         |   0.822 |    5 |      1 | 43.5s |   3277 |
|   13 |  0.7 | 42 **[C]** |   0.675 |    9 |      0 |  1.8m |   9561 |
|   14 |  0.7 | 95         |   0.807 |   10 |      0 |  1.8m |   9541 |
|   15 |  0.7 | 42 **[C]** |   0.785 |    6 |      0 |  1.8m |   9371 |
|   16 |  0.9 | None       |   0.741 |    3 |      3 |  2.6m |   3333 |

### Correct Answer Analysis

Correct answer **42** was found by **6** of **32** attempts (19%).

Attempts that found correct:

| Run   | Att# | Temp | Entropy | Code | Errors | Time  |
| ----- | ---: | ---: | ------: | ---: | -----: | ----: |
| Run 1 |   10 |  0.5 |   0.705 |    2 |      0 | 47.9s |
| Run 2 |    5 |  0.3 |   0.653 |   11 |      1 |  1.8m |
| Run 2 |    7 |  0.5 |   0.794 |    5 |      0 |  1.3m |
| Run 2 |   11 |  0.5 |   0.702 |    8 |      0 |  1.6m |
| Run 2 |   13 |  0.7 |   0.675 |    9 |      0 |  1.8m |
| Run 2 |   15 |  0.7 |   0.785 |    6 |      0 |  1.8m |

**Why it lost**: Correct got 6 vote(s) vs winner `95` with 9 vote(s).

### Code Calls vs No-Code Analysis

| Group          | Answered | None     | Correct | Avg code calls |
| -------------- | -------: | -------: | ------: | -------------: |
| With code (29) | 18 (62%) | 11 (38%) | 6 (21%) |            5.5 |
| No code (3)    | 3 (100%) |   0 (0%) |  0 (0%) |              0 |

### Entropy Signal

- Correct attempts avg entropy: **0.719**
- Wrong attempts avg entropy: **0.742**
- None attempts avg entropy: **0.721**
- Signal: **Correct has LOWER entropy** (diff: 0.023) -- entropy weighting WOULD help

---

================================================================================
## Problem `673b29` — Expected: **3**, Predicted: **3032**
================================================================================

- **Runs**: 2 (dual-run), **32** total attempts
- **Classification**: **Confident wrong**
- **None rate**: 20/32 (62%)
- **Correct answer found**: NO — never appeared in any attempt

### Vote Distribution

| Answer | Votes | % of answered |
| ------ | ----: | ------------: |
| 3032   |    12 |          100% |
| None   |    20 |           62% |

### Run 1 — Per-Attempt Detail

Predicted: 3032, Early stop: True, Votes: {3032: 6}

| Att# | Temp | Answer | Entropy | Code | Errors | Time  | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ----: | -----: |
|    1 |  0.1 | 3032   |   0.967 |    0 |      0 | 38.8s |   3401 |
|    2 |  0.3 | 3032   |   0.963 |    0 |      0 | 33.7s |   3001 |
|    3 |  0.3 | None   |   0.975 |    0 |      0 | 41.6s |   3401 |
|    4 |  0.3 | None   |   0.971 |    0 |      0 | 41.6s |   3401 |
|    5 |  0.3 | None   |   1.010 |    0 |      0 | 41.6s |   3401 |
|    6 |  0.5 | None   |   0.891 |    0 |      0 | 41.6s |   3401 |
|    7 |  0.5 | None   |   1.000 |    0 |      0 | 41.6s |   3401 |
|    8 |  0.5 | None   |   0.922 |    0 |      0 | 41.6s |   3401 |
|    9 |  0.5 | 3032   |   0.955 |    0 |      0 | 28.9s |   2601 |
|   10 |  0.5 | 3032   |   1.002 |    0 |      0 | 38.8s |   3401 |
|   11 |  0.5 | None   |   1.003 |    0 |      0 | 41.5s |   3401 |
|   12 |  0.7 | 3032   |   0.981 |    0 |      0 | 38.8s |   3401 |
|   13 |  0.7 | 3032   |   0.924 |    0 |      0 | 33.7s |   3001 |
|   14 |  0.7 | None   |   0.985 |    0 |      0 | 41.6s |   3401 |
|   15 |  0.7 | None   |   1.024 |    0 |      0 | 41.5s |   3401 |
|   16 |  0.9 | None   |   1.031 |    0 |      0 | 41.5s |   3401 |

### Run 2 — Per-Attempt Detail

Predicted: 3032, Early stop: True, Votes: {3032: 6}

| Att# | Temp | Answer | Entropy | Code | Errors | Time  | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ----: | -----: |
|    1 |  0.1 | 3032   |   0.991 |    0 |      0 | 29.1s |   2601 |
|    2 |  0.3 | None   |   0.987 |    0 |      0 | 49.3s |   4001 |
|    3 |  0.3 | 3032   |   0.970 |    0 |      0 | 36.2s |   3201 |
|    4 |  0.3 | 3032   |   0.919 |    0 |      0 | 36.2s |   3201 |
|    5 |  0.3 | 3032   |   0.940 |    0 |      0 | 46.6s |   4001 |
|    6 |  0.5 | 3032   |   0.960 |    0 |      0 | 44.0s |   3801 |
|    7 |  0.5 | None   |   0.988 |    0 |      0 | 49.3s |   4001 |
|    8 |  0.5 | 3032   |   0.893 |    0 |      0 | 46.7s |   4001 |
|    9 |  0.5 | None   |   0.940 |    0 |      0 | 49.3s |   4001 |
|   10 |  0.5 | None   |   0.986 |    0 |      0 | 49.4s |   4001 |
|   11 |  0.5 | None   |   0.953 |    0 |      0 | 49.4s |   4001 |
|   12 |  0.7 | None   |   0.956 |    0 |      0 | 49.4s |   4001 |
|   13 |  0.7 | None   |   1.007 |    0 |      0 | 49.4s |   4001 |
|   14 |  0.7 | None   |   0.987 |    0 |      0 | 49.3s |   4001 |
|   15 |  0.7 | None   |   1.029 |    0 |      0 | 49.3s |   4001 |
|   16 |  0.9 | None   |   1.001 |    0 |      0 |  1.3m |   4001 |

### Correct Answer Analysis

Correct answer **3** was **NEVER** found in any of the 32 attempts across 2 run(s).

Closest answer: **3032** (off by 3029)

### Code Calls vs No-Code Analysis

| Group        | Answered | None     | Correct | Avg code calls |
| ------------ | -------: | -------: | ------: | -------------: |
| No code (32) | 12 (38%) | 20 (62%) |  0 (0%) |              0 |

### Entropy Signal

- No correct attempts found. Wrong attempts avg entropy: **0.955**

---

================================================================================
## Problem `86e8e5` — Expected: **8687**, Predicted: **96985**
================================================================================

- **Runs**: 3 (dual-run), **48** total attempts
- **Classification**: **Outvoted**
- **None rate**: 17/48 (35%)
- **Correct answer found**: YES — in 3 attempt(s)
- **Temps that found correct**: 0.3, 0.5, 0.7
- **Run(s) that found correct**: 1

### Vote Distribution

| Answer             | Votes | % of answered |
| ------------------ | ----: | ------------: |
| 8687 **(CORRECT)** |     3 |           10% |
| 41754              |     3 |           10% |
| 73218              |     2 |            6% |
| 96985              |     2 |            6% |
| 31033              |     1 |            3% |
| 91036              |     1 |            3% |
| 54680              |     1 |            3% |
| 11                 |     1 |            3% |
| 23                 |     1 |            3% |
| 64020              |     1 |            3% |
| 93764              |     1 |            3% |
| 82588              |     1 |            3% |
| 46426              |     1 |            3% |
| 5                  |     1 |            3% |
| 98744              |     1 |            3% |
| 21513              |     1 |            3% |
| 64885              |     1 |            3% |
| 49917              |     1 |            3% |
| 25238              |     1 |            3% |
| 98449              |     1 |            3% |
| 20139              |     1 |            3% |
| 7535               |     1 |            3% |
| 77463              |     1 |            3% |
| 40958              |     1 |            3% |
| 4                  |     1 |            3% |
| None               |    17 |           35% |

### Run 1 — Per-Attempt Detail

Predicted: 8687, Early stop: False, Votes: {8687: 3, 64020: 1, 31033: 1, 46426: 1, 73218: 1, 54680: 1, 11: 1, 93764: 1, 91036: 1, 23: 1, 82588: 1, 41754: 1}

| Att# | Temp | Answer       | Entropy | Code | Errors | Time  | Tokens |
| ---: | ---: | ------------ | ------: | ---: | -----: | ----: | -----: |
|    1 |  0.1 | 31033        |   0.656 |   20 |      5 |  7.7m |  22133 |
|    2 |  0.3 | 73218        |   0.620 |   28 |      0 |  9.0m |  33438 |
|    3 |  0.3 | 91036        |   0.628 |   19 |      4 |  9.9m |  29945 |
|    4 |  0.3 | 8687 **[C]** |   0.599 |   71 |      1 |  7.2m |  26271 |
|    5 |  0.3 | 54680        |   0.595 |   31 |      4 |  9.1m |  34255 |
|    6 |  0.5 | 11           |   0.636 |   31 |      2 |  9.2m |  32063 |
|    7 |  0.5 | 23           |   0.598 |   41 |      6 | 11.3m |  47587 |
|    8 |  0.5 | 64020        |   0.623 |   12 |      0 |  5.9m |  23795 |
|    9 |  0.5 | None         |   0.567 |   68 |      6 | 13.5m |  47838 |
|   10 |  0.5 | 93764        |   0.603 |   38 |      3 |  9.3m |  30699 |
|   11 |  0.5 | 8687 **[C]** |   0.607 |   36 |      1 |  8.8m |  31820 |
|   12 |  0.7 | 41754        |   0.611 |   81 |      9 | 13.5m |  40722 |
|   13 |  0.7 | 82588        |   0.580 |   68 |      8 | 13.2m |  44962 |
|   14 |  0.7 | 8687 **[C]** |   0.619 |   45 |      2 |  7.0m |  25083 |
|   15 |  0.7 | 46426        |   0.604 |   41 |      5 |  8.0m |  27629 |
|   16 |  0.9 | None         |   0.621 |   66 |      5 | 10.0m |  36646 |

### Run 2 — Per-Attempt Detail

Predicted: 96985, Early stop: False, Votes: {96985: 2, 41754: 2, 73218: 1, 7535: 1, 20139: 1, 21513: 1, 98449: 1, 98744: 1, 25238: 1, 77463: 1, 64885: 1, 5: 1, 49917: 1}

| Att# | Temp | Answer | Entropy | Code | Errors | Time  | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ----: | -----: |
|    1 |  0.1 | 73218  |   0.602 |   20 |      5 |  6.2m |  24380 |
|    2 |  0.3 | 5      |   0.605 |   45 |      1 | 10.9m |  40157 |
|    3 |  0.3 | None   |   0.614 |   52 |      5 | 11.2m |  36579 |
|    4 |  0.3 | 98744  |   0.593 |   56 |      5 | 10.5m |  39179 |
|    5 |  0.3 | 21513  |   0.566 |   27 |      3 |  9.2m |  30332 |
|    6 |  0.5 | 64885  |   0.619 |   39 |      2 | 10.7m |  37616 |
|    7 |  0.5 | 49917  |   0.540 |   39 |      3 | 11.3m |  42289 |
|    8 |  0.5 | 96985  |   0.593 |   48 |      1 | 11.9m |  48520 |
|    9 |  0.5 | 25238  |   0.603 |   38 |      6 | 10.5m |  25202 |
|   10 |  0.5 | 41754  |   0.618 |   40 |      2 |  9.2m |  32063 |
|   11 |  0.5 | 98449  |   0.603 |   42 |      2 | 10.0m |  36848 |
|   12 |  0.7 | 96985  |   0.648 |   28 |      1 |  6.5m |  25062 |
|   13 |  0.7 | 20139  |   0.689 |   33 |      3 |  7.9m |  21796 |
|   14 |  0.7 | 7535   |   0.619 |   20 |      1 |  7.2m |  27519 |
|   15 |  0.7 | 77463  |   0.628 |   76 |      7 | 10.6m |  32258 |
|   16 |  0.9 | 41754  |   0.690 |   71 |      3 | 10.3m |  34727 |

### Run 3 — Per-Attempt Detail

Predicted: 40958, Early stop: False, Votes: {4: 1, 40958: 1}

| Att# | Temp | Answer | Entropy | Code | Errors | Time  | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ----: | -----: |
|    1 |  0.1 | None   |   0.623 |   38 |      8 |  5.0m |  16309 |
|    2 |  0.3 | None   |   0.656 |   18 |      1 |  5.0m |  17846 |
|    3 |  0.3 | None   |   0.627 |   12 |      0 |  5.0m |  20411 |
|    4 |  0.3 | None   |   0.634 |   22 |      1 |  5.0m |  17690 |
|    5 |  0.3 | None   |   0.661 |   12 |      0 |  5.2m |  20186 |
|    6 |  0.5 | 40958  |   0.653 |   23 |      3 |  4.7m |  19020 |
|    7 |  0.5 | None   |   0.659 |   13 |      2 |  5.0m |  20122 |
|    8 |  0.5 | None   |   0.661 |   21 |      3 |  5.4m |  16055 |
|    9 |  0.5 | None   |   0.683 |    5 |      0 |  5.0m |  20532 |
|   10 |  0.5 | None   |   0.650 |   15 |      4 |  5.2m |  17177 |
|   11 |  0.5 | None   |   0.611 |   22 |      1 |  5.0m |  17314 |
|   12 |  0.7 | 4      |   0.718 |    2 |      0 | 24.2s |   2025 |
|   13 |  0.7 | None   |   0.686 |   21 |      1 |  5.4m |  18112 |
|   14 |  0.7 | None   |   0.705 |    1 |      1 |  5.0m |  20612 |
|   15 |  0.7 | None   |   0.680 |   12 |      0 |  5.0m |  20378 |
|   16 |  0.9 | None   |   0.648 |    3 |      3 |  5.5m |  15009 |

### Correct Answer Analysis

Correct answer **8687** was found by **3** of **48** attempts (6%).

Attempts that found correct:

| Run   | Att# | Temp | Entropy | Code | Errors | Time |
| ----- | ---: | ---: | ------: | ---: | -----: | ---: |
| Run 1 |    4 |  0.3 |   0.599 |   71 |      1 | 7.2m |
| Run 1 |   11 |  0.5 |   0.607 |   36 |      1 | 8.8m |
| Run 1 |   14 |  0.7 |   0.619 |   45 |      2 | 7.0m |

**Why it lost**: Correct got 3 vote(s) vs winner `8687` with 3 vote(s).

### Code Calls vs No-Code Analysis

| Group          | Answered | None     | Correct | Avg code calls |
| -------------- | -------: | -------: | ------: | -------------: |
| With code (48) | 31 (65%) | 17 (35%) |  3 (6%) |           33.5 |

### Entropy Signal

- Correct attempts avg entropy: **0.608**
- Wrong attempts avg entropy: **0.619**
- None attempts avg entropy: **0.646**
- Signal: **Correct has LOWER entropy** (diff: 0.011) -- entropy weighting WOULD help

---

================================================================================
## Problem `89c921` — Expected: **29800**, Predicted: **39601**
================================================================================

- **Runs**: 2 (dual-run), **32** total attempts
- **Classification**: **Outvoted**
- **None rate**: 18/32 (56%)
- **Correct answer found**: YES — in 5 attempt(s)
- **Temps that found correct**: 0.1, 0.3, 0.5 (3x)
- **Run(s) that found correct**: 2

### Vote Distribution

| Answer              | Votes | % of answered |
| ------------------- | ----: | ------------: |
| 39601               |     8 |           57% |
| 29800 **(CORRECT)** |     5 |           36% |
| 39404               |     1 |            7% |
| None                |    18 |           56% |

### Run 1 — Per-Attempt Detail

Predicted: 39601, Early stop: True, Votes: {39601: 5}

| Att# | Temp | Answer | Entropy | Code | Errors | Time | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ---: | -----: |
|    1 |  0.1 | 39601  |   0.562 |    3 |      0 | 3.0m |  13276 |
|    2 |  0.3 | 39601  |   0.504 |   13 |      0 | 3.0m |  13165 |
|    3 |  0.3 | 39601  |   0.537 |   10 |      0 | 2.2m |  10044 |
|    4 |  0.3 | None   |   0.572 |   12 |      1 | 3.1m |  12099 |
|    5 |  0.3 | 39601  |   0.492 |    4 |      0 | 1.7m |   7824 |
|    6 |  0.5 | None   |   0.554 |   19 |      0 | 3.0m |  12923 |
|    7 |  0.5 | None   |   0.555 |    2 |      0 | 3.0m |  13132 |
|    8 |  0.5 | None   |   0.501 |    3 |      2 | 3.0m |  11211 |
|    9 |  0.5 | None   |   0.554 |    7 |      0 | 3.0m |  13125 |
|   10 |  0.5 | None   |   0.553 |    0 |      0 | 3.0m |  13201 |
|   11 |  0.5 | None   |   0.551 |   12 |      0 | 3.0m |  13191 |
|   12 |  0.7 | None   |   0.567 |    9 |      1 | 3.0m |  11376 |
|   13 |  0.7 | None   |   0.567 |    4 |      1 | 3.0m |  13186 |
|   14 |  0.7 | None   |   0.649 |    0 |      0 | 3.0m |  13201 |
|   15 |  0.7 | None   |   0.624 |    3 |      0 | 3.0m |  13207 |
|   16 |  0.9 | 39601  |   0.544 |    9 |      0 | 2.0m |   9241 |

### Run 2 — Per-Attempt Detail

Predicted: 29800, Early stop: True, Votes: {29800: 5, 39601: 3, 39404: 1}

| Att# | Temp | Answer        | Entropy | Code | Errors | Time | Tokens |
| ---: | ---: | ------------- | ------: | ---: | -----: | ---: | -----: |
|    1 |  0.1 | 29800 **[C]** |   0.479 |   18 |      0 | 2.8m |  12313 |
|    2 |  0.3 | None          |   0.560 |    0 |      0 | 4.5m |  21001 |
|    3 |  0.3 | 29800 **[C]** |   0.442 |   12 |      0 | 3.7m |  16439 |
|    4 |  0.3 | None          |   0.554 |    3 |      0 | 4.5m |  20971 |
|    5 |  0.3 | 39601         |   0.526 |    1 |      0 | 2.2m |  10165 |
|    6 |  0.5 | None          |   0.605 |   14 |      0 | 4.5m |  20696 |
|    7 |  0.5 | 29800 **[C]** |   0.485 |    5 |      0 | 2.3m |  10368 |
|    8 |  0.5 | 29800 **[C]** |   0.531 |    8 |      0 | 4.5m |  20900 |
|    9 |  0.5 | 29800 **[C]** |   0.495 |   12 |      0 | 3.3m |  14563 |
|   10 |  0.5 | 39404         |   0.434 |    8 |      1 | 2.5m |  11133 |
|   11 |  0.5 | 39601         |   0.557 |    8 |      1 | 2.2m |  10056 |
|   12 |  0.7 | 39601         |   0.609 |    1 |      0 | 1.8m |   8436 |
|   13 |  0.7 | None          |   0.651 |   32 |      0 | 4.5m |  20626 |
|   14 |  0.7 | None          |   0.654 |    6 |      0 | 4.5m |  20965 |
|   15 |  0.7 | None          |   0.687 |    9 |      2 | 4.7m |  16631 |
|   16 |  0.9 | None          |   0.617 |    4 |      4 | 5.1m |  11343 |

### Correct Answer Analysis

Correct answer **29800** was found by **5** of **32** attempts (16%).

Attempts that found correct:

| Run   | Att# | Temp | Entropy | Code | Errors | Time |
| ----- | ---: | ---: | ------: | ---: | -----: | ---: |
| Run 2 |    1 |  0.1 |   0.479 |   18 |      0 | 2.8m |
| Run 2 |    3 |  0.3 |   0.442 |   12 |      0 | 3.7m |
| Run 2 |    7 |  0.5 |   0.485 |    5 |      0 | 2.3m |
| Run 2 |    8 |  0.5 |   0.531 |    8 |      0 | 4.5m |
| Run 2 |    9 |  0.5 |   0.495 |   12 |      0 | 3.3m |

**Why it lost**: Correct got 5 vote(s) vs winner `39601` with 8 vote(s).

### Code Calls vs No-Code Analysis

| Group          | Answered | None     | Correct | Avg code calls |
| -------------- | -------: | -------: | ------: | -------------: |
| With code (29) | 14 (48%) | 15 (52%) | 5 (17%) |            8.7 |
| No code (3)    |   0 (0%) | 3 (100%) |  0 (0%) |              0 |

### Entropy Signal

- Correct attempts avg entropy: **0.486**
- Wrong attempts avg entropy: **0.529**
- None attempts avg entropy: **0.587**
- Signal: **Correct has LOWER entropy** (diff: 0.043) -- entropy weighting WOULD help

---

================================================================================
## Problem `9010d9` — Expected: **10320**, Predicted: **6400**
================================================================================

- **Runs**: 2 (dual-run), **32** total attempts
- **Classification**: **Confident wrong**
- **None rate**: 21/32 (66%)
- **Correct answer found**: NO — never appeared in any attempt

### Vote Distribution

| Answer | Votes | % of answered |
| ------ | ----: | ------------: |
| 6400   |    10 |           91% |
| 3240   |     1 |            9% |
| None   |    21 |           66% |

### Run 1 — Per-Attempt Detail

Predicted: 6400, Early stop: True, Votes: {6400: 5, 3240: 1}

| Att# | Temp | Answer | Entropy | Code | Errors | Time  | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ----: | -----: |
|    1 |  0.1 | None   |   0.821 |    0 |      0 |  1.9m |   9001 |
|    2 |  0.3 | None   |   0.753 |    4 |      0 |  1.9m |   8882 |
|    3 |  0.3 | None   |   0.790 |    0 |      0 |  1.9m |   9001 |
|    4 |  0.3 | None   |   0.710 |    0 |      0 |  1.9m |   9001 |
|    5 |  0.3 | 6400   |   0.848 |    0 |      0 |  1.0m |   5401 |
|    6 |  0.5 | None   |   0.744 |    3 |      1 |  1.9m |   8971 |
|    7 |  0.5 | 6400   |   0.709 |    0 |      0 |  1.1m |   5756 |
|    8 |  0.5 | None   |   0.762 |    2 |      0 |  1.9m |   8832 |
|    9 |  0.5 | None   |   0.843 |    2 |      1 |  1.9m |   8980 |
|   10 |  0.5 | 6400   |   0.802 |    0 |      0 |  1.9m |   9001 |
|   11 |  0.5 | None   |   0.797 |    3 |      1 |  2.3m |   8520 |
|   12 |  0.7 | None   |   0.811 |    2 |      0 |  1.9m |   8855 |
|   13 |  0.7 | 6400   |   0.855 |    0 |      0 | 40.8s |   3601 |
|   14 |  0.7 | 6400   |   0.846 |    0 |      0 |  1.6m |   8001 |
|   15 |  0.7 | None   |   0.782 |    0 |      0 |  1.9m |   9001 |
|   16 |  0.9 | 3240   |   0.909 |    0 |      0 |  1.0m |   5201 |

### Run 2 — Per-Attempt Detail

Predicted: 6400, Early stop: True, Votes: {6400: 5}

| Att# | Temp | Answer | Entropy | Code | Errors | Time | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ---: | -----: |
|    1 |  0.1 | None   |   0.726 |    2 |      1 | 2.8m |  10694 |
|    2 |  0.3 | 6400   |   0.766 |    0 |      0 | 2.8m |  13001 |
|    3 |  0.3 | None   |   0.782 |    3 |      0 | 2.8m |  12891 |
|    4 |  0.3 | 6400   |   0.778 |    1 |      0 | 2.2m |  10536 |
|    5 |  0.3 | 6400   |   0.804 |    0 |      0 | 1.2m |   6001 |
|    6 |  0.5 | None   |   0.763 |    5 |      0 | 2.8m |  12958 |
|    7 |  0.5 | None   |   0.771 |    4 |      1 | 2.8m |  10763 |
|    8 |  0.5 | None   |   0.793 |    0 |      0 | 2.8m |  13001 |
|    9 |  0.5 | 6400   |   0.802 |    0 |      0 | 2.4m |  11401 |
|   10 |  0.5 | None   |   0.817 |    0 |      0 | 2.8m |  13001 |
|   11 |  0.5 | 6400   |   0.760 |    2 |      1 | 2.6m |  10025 |
|   12 |  0.7 | None   |   0.873 |    4 |      0 | 2.8m |  12863 |
|   13 |  0.7 | None   |   0.760 |    2 |      1 | 2.8m |  10786 |
|   14 |  0.7 | None   |   0.826 |    1 |      0 | 2.8m |  12831 |
|   15 |  0.7 | None   |   0.835 |    1 |      0 | 2.8m |  12811 |
|   16 |  0.9 | None   |   0.874 |    0 |      0 | 3.3m |  12801 |

### Correct Answer Analysis

Correct answer **10320** was **NEVER** found in any of the 32 attempts across 2 run(s).

Closest answer: **6400** (off by 3920)

### Code Calls vs No-Code Analysis

| Group          | Answered | None     | Correct | Avg code calls |
| -------------- | -------: | -------: | ------: | -------------: |
| With code (16) |  2 (12%) | 14 (88%) |  0 (0%) |            2.6 |
| No code (16)   |  9 (56%) |  7 (44%) |  0 (0%) |              0 |

### Entropy Signal

- No correct attempts found. Wrong attempts avg entropy: **0.807**

---

================================================================================
## Problem `a824c1` — Expected: **24**, Predicted: **13**
================================================================================

- **Runs**: 2 (dual-run), **32** total attempts
- **Classification**: **Confident wrong**
- **None rate**: 17/32 (53%)
- **Correct answer found**: NO — never appeared in any attempt

### Vote Distribution

| Answer | Votes | % of answered |
| ------ | ----: | ------------: |
| 13     |    10 |           67% |
| 12     |     3 |           20% |
| 26     |     2 |           13% |
| None   |    17 |           53% |

### Run 1 — Per-Attempt Detail

Predicted: 13, Early stop: True, Votes: {13: 5, 26: 2, 12: 1}

| Att# | Temp | Answer | Entropy | Code | Errors | Time | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ---: | -----: |
|    1 |  0.1 | None   |   0.624 |   12 |      5 | 3.4m |   9609 |
|    2 |  0.3 | None   |   0.644 |   19 |      3 | 3.4m |  10931 |
|    3 |  0.3 | None   |   0.676 |   15 |      5 | 3.3m |  10971 |
|    4 |  0.3 | 13     |   0.559 |   29 |      3 | 3.2m |  12318 |
|    5 |  0.3 | 13     |   0.707 |   14 |      4 | 3.3m |  12135 |
|    6 |  0.5 | 12     |   0.731 |    7 |      0 | 1.5m |   6739 |
|    7 |  0.5 | 13     |   0.715 |   11 |      0 | 1.5m |   6546 |
|    8 |  0.5 | 26     |   0.515 |   15 |      0 | 1.3m |   5865 |
|    9 |  0.5 | None   |   0.651 |   28 |      3 | 3.3m |  13490 |
|   10 |  0.5 | 26     |   0.612 |   11 |      0 | 1.1m |   4834 |
|   11 |  0.5 | None   |   0.759 |   18 |      4 | 3.3m |  11476 |
|   12 |  0.7 | 13     |   0.813 |    1 |      0 | 1.4m |   6186 |
|   13 |  0.7 | None   |   0.699 |   21 |      2 | 3.7m |  15506 |
|   14 |  0.7 | 13     |   0.743 |   18 |      2 | 3.1m |  15860 |
|   15 |  0.7 | None   |   0.716 |   21 |      0 | 3.3m |  14319 |
|   16 |  0.9 | None   |   0.824 |    4 |      4 | 3.8m |   6324 |

### Run 2 — Per-Attempt Detail

Predicted: 13, Early stop: True, Votes: {13: 5, 12: 2}

| Att# | Temp | Answer | Entropy | Code | Errors | Time  | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ----: | -----: |
|    1 |  0.1 | None   |   0.609 |   17 |      5 |  3.9m |  13236 |
|    2 |  0.3 | None   |   0.709 |   14 |      2 |  4.0m |  14144 |
|    3 |  0.3 | 13     |   0.664 |   16 |      0 |  3.0m |  13355 |
|    4 |  0.3 | 13     |   0.694 |   10 |      1 |  3.9m |  15618 |
|    5 |  0.3 | None   |   0.641 |   22 |      4 |  3.9m |  14637 |
|    6 |  0.5 | None   |   0.699 |   22 |      4 |  4.2m |   8900 |
|    7 |  0.5 | None   |   0.695 |   22 |      1 |  3.9m |  13651 |
|    8 |  0.5 | None   |   0.631 |   15 |      3 |  4.1m |  10613 |
|    9 |  0.5 | 12     |   0.698 |   12 |      4 |  2.2m |   9468 |
|   10 |  0.5 | 13     |   0.930 |    0 |      0 | 18.8s |   1601 |
|   11 |  0.5 | 12     |   0.764 |    2 |      0 |  1.5m |   6683 |
|   12 |  0.7 | 13     |   0.683 |   20 |      1 |  3.1m |  12365 |
|   13 |  0.7 | None   |   0.711 |   24 |      6 |  3.9m |  14542 |
|   14 |  0.7 | None   |   0.697 |   24 |      3 |  3.9m |  17046 |
|   15 |  0.7 | 13     |   0.715 |   12 |      2 |  3.5m |  12867 |
|   16 |  0.9 | None   |   0.747 |    3 |      3 |  4.4m |  11315 |

### Correct Answer Analysis

Correct answer **24** was **NEVER** found in any of the 32 attempts across 2 run(s).

Closest answer: **26** (off by 2)

### Code Calls vs No-Code Analysis

| Group          | Answered | None     | Correct | Avg code calls |
| -------------- | -------: | -------: | ------: | -------------: |
| With code (31) | 14 (45%) | 17 (55%) |  0 (0%) |           15.5 |
| No code (1)    | 1 (100%) |   0 (0%) |  0 (0%) |              0 |

### Entropy Signal

- No correct attempts found. Wrong attempts avg entropy: **0.703**

---

================================================================================
## Problem `a9dbc8` — Expected: **15744**, Predicted: **15743**
================================================================================

- **Runs**: 2 (dual-run), **32** total attempts
- **Classification**: **Confident wrong**
- **None rate**: 20/32 (62%)
- **Correct answer found**: NO — never appeared in any attempt

### Vote Distribution

| Answer | Votes | % of answered |
| ------ | ----: | ------------: |
| 15743  |     6 |           50% |
| 2      |     3 |           25% |
| 15745  |     1 |            8% |
| 7877   |     1 |            8% |
| 1      |     1 |            8% |
| None   |    20 |           62% |

### Run 1 — Per-Attempt Detail

Predicted: 15743, Early stop: True, Votes: {15743: 5, 1: 1, 15745: 1, 7877: 1}

| Att# | Temp | Answer | Entropy | Code | Errors | Time | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ---: | -----: |
|    1 |  0.1 | None   |   0.603 |   16 |      2 | 5.6m |  19969 |
|    2 |  0.3 | None   |   0.639 |   16 |      0 | 5.6m |  22959 |
|    3 |  0.3 | 15745  |   0.653 |    6 |      1 | 3.5m |  12655 |
|    4 |  0.3 | None   |   0.690 |    9 |      0 | 5.6m |  18379 |
|    5 |  0.3 | None   |   0.678 |   11 |      1 | 5.6m |  19465 |
|    6 |  0.5 | None   |   0.705 |    5 |      2 | 5.6m |  18454 |
|    7 |  0.5 | 15743  |   0.678 |   10 |      0 | 5.2m |  21046 |
|    8 |  0.5 | 7877   |   0.623 |   19 |      1 | 4.4m |  18289 |
|    9 |  0.5 | None   |   0.637 |   11 |      0 | 5.6m |  20906 |
|   10 |  0.5 | 15743  |   0.581 |   10 |      1 | 4.6m |  16622 |
|   11 |  0.5 | None   |   0.595 |   11 |      3 | 5.6m |  22982 |
|   12 |  0.7 | 15743  |   0.679 |   14 |      3 | 5.6m |  22971 |
|   13 |  0.7 | 15743  |   0.679 |   18 |      1 | 4.6m |  18741 |
|   14 |  0.7 | 15743  |   0.698 |    9 |      0 | 4.1m |  16860 |
|   15 |  0.7 | 1      |   0.620 |    6 |      1 | 1.9m |   5325 |
|   16 |  0.9 | None   |   0.770 |    8 |      8 | 6.5m |   8154 |

### Run 2 — Per-Attempt Detail

Predicted: 2, Early stop: False, Votes: {2: 3, 15743: 1}

| Att# | Temp | Answer | Entropy | Code | Errors | Time | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ---: | -----: |
|    1 |  0.1 | None   |   0.624 |   25 |      0 | 5.0m |  20388 |
|    2 |  0.3 | None   |   0.578 |   14 |      2 | 5.0m |  16876 |
|    3 |  0.3 | 2      |   0.658 |    4 |      0 | 2.2m |   9974 |
|    4 |  0.3 | 2      |   0.621 |    6 |      3 | 4.1m |  10320 |
|    5 |  0.3 | None   |   0.606 |   12 |      0 | 5.1m |  20926 |
|    6 |  0.5 | None   |   0.721 |    4 |      0 | 5.0m |  21096 |
|    7 |  0.5 | 15743  |   0.658 |    3 |      0 | 1.9m |   8290 |
|    8 |  0.5 | None   |   0.666 |   13 |      3 | 5.1m |  18417 |
|    9 |  0.5 | None   |   0.681 |   17 |      2 | 5.0m |  14306 |
|   10 |  0.5 | None   |   0.629 |   13 |      3 | 5.0m |  13350 |
|   11 |  0.5 | None   |   0.590 |   15 |      1 | 5.0m |  17497 |
|   12 |  0.7 | 2      |   0.634 |    5 |      0 | 3.0m |  13506 |
|   13 |  0.7 | None   |   0.649 |    9 |      2 | 5.2m |  15467 |
|   14 |  0.7 | None   |   0.673 |   13 |      1 | 5.0m |  18925 |
|   15 |  0.7 | None   |   0.646 |   18 |      2 | 5.0m |  15231 |
|   16 |  0.9 | None   |   0.781 |    7 |      7 | 5.5m |   6522 |

### Correct Answer Analysis

Correct answer **15744** was **NEVER** found in any of the 32 attempts across 2 run(s).

Closest answer: **15745** (off by 1)

### Code Calls vs No-Code Analysis

| Group          | Answered | None     | Correct | Avg code calls |
| -------------- | -------: | -------: | ------: | -------------: |
| With code (32) | 12 (38%) | 20 (62%) |  0 (0%) |           11.2 |

### Entropy Signal

- No correct attempts found. Wrong attempts avg entropy: **0.649**

---

================================================================================
## Problem `ae2add` — Expected: **24931**, Predicted: **19945**
================================================================================

- **Runs**: 2 (dual-run), **32** total attempts
- **Classification**: **Outvoted**
- **None rate**: 16/32 (50%)
- **Correct answer found**: YES — in 1 attempt(s)
- **Temps that found correct**: 0.1
- **Run(s) that found correct**: 2

### Vote Distribution

| Answer              | Votes | % of answered |
| ------------------- | ----: | ------------: |
| 19945               |     8 |           50% |
| 9973                |     3 |           19% |
| 19946               |     3 |           19% |
| 2                   |     1 |            6% |
| 24931 **(CORRECT)** |     1 |            6% |
| None                |    16 |           50% |

### Run 1 — Per-Attempt Detail

Predicted: 19945, Early stop: True, Votes: {19945: 5, 9973: 1, 2: 1}

| Att# | Temp | Answer | Entropy | Code | Errors | Time  | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ----: | -----: |
|    1 |  0.1 | None   |   0.693 |   14 |      0 |  2.7m |  10868 |
|    2 |  0.3 | None   |   0.773 |    3 |      1 |  2.7m |   9676 |
|    3 |  0.3 | None   |   0.595 |   13 |      0 |  2.7m |  10282 |
|    4 |  0.3 | None   |   0.692 |    6 |      1 |  2.7m |  12521 |
|    5 |  0.3 | None   |   0.686 |    8 |      1 |  2.7m |  12436 |
|    6 |  0.5 | None   |   0.708 |    6 |      0 |  2.7m |  12508 |
|    7 |  0.5 | None   |   0.790 |    3 |      1 |  2.7m |  10194 |
|    8 |  0.5 | None   |   0.738 |    5 |      0 |  2.7m |  12583 |
|    9 |  0.5 | 19945  |   0.777 |    5 |      0 |  1.8m |   8405 |
|   10 |  0.5 | 19945  |   0.727 |    2 |      0 |  2.1m |   9294 |
|   11 |  0.5 | 19945  |   0.779 |    2 |      0 |  2.7m |  12679 |
|   12 |  0.7 | 19945  |   0.776 |    0 |      0 | 48.8s |   4001 |
|   13 |  0.7 | 19945  |   0.785 |    0 |      0 |  1.8m |   8201 |
|   14 |  0.7 | 9973   |   0.763 |    0 |      0 | 28.7s |   2401 |
|   15 |  0.7 | None   |   0.680 |    9 |      0 |  2.7m |  12539 |
|   16 |  0.9 | 2      |   0.786 |    0 |      0 |  1.6m |   5201 |

### Run 2 — Per-Attempt Detail

Predicted: 19945, Early stop: False, Votes: {19946: 3, 19945: 3, 9973: 2, 24931: 1}

| Att# | Temp | Answer        | Entropy | Code | Errors | Time  | Tokens |
| ---: | ---: | ------------- | ------: | ---: | -----: | ----: | -----: |
|    1 |  0.1 | 24931 **[C]** |   0.739 |    1 |      0 |  3.5m |  14948 |
|    2 |  0.3 | 19946         |   0.717 |    5 |      0 |  3.0m |  13061 |
|    3 |  0.3 | None          |   0.614 |   32 |      4 |  5.0m |  19632 |
|    4 |  0.3 | 9973          |   0.671 |    0 |      0 |  2.7m |  11801 |
|    5 |  0.3 | None          |   0.687 |   10 |      0 |  5.0m |  22678 |
|    6 |  0.5 | 19945         |   0.677 |   22 |      1 |  4.9m |  19397 |
|    7 |  0.5 | None          |   0.701 |   16 |      2 |  5.0m |  18778 |
|    8 |  0.5 | None          |   0.633 |   14 |      2 |  5.0m |  19088 |
|    9 |  0.5 | None          |   0.730 |    3 |      0 |  5.0m |  22789 |
|   10 |  0.5 | 19946         |   0.711 |    5 |      0 |  1.0m |   4829 |
|   11 |  0.5 | 19946         |   0.698 |    7 |      0 |  3.9m |  16859 |
|   12 |  0.7 | None          |   0.678 |   25 |      2 |  5.1m |  19560 |
|   13 |  0.7 | 9973          |   0.754 |    2 |      0 | 25.3s |   2128 |
|   14 |  0.7 | 19945         |   0.685 |    9 |      1 |  4.3m |  16041 |
|   15 |  0.7 | 19945         |   0.758 |   13 |      0 |  4.8m |  21307 |
|   16 |  0.9 | None          |   0.764 |    5 |      5 |  5.5m |  10965 |

### Correct Answer Analysis

Correct answer **24931** was found by **1** of **32** attempts (3%).

Attempts that found correct:

| Run   | Att# | Temp | Entropy | Code | Errors | Time |
| ----- | ---: | ---: | ------: | ---: | -----: | ---: |
| Run 2 |    1 |  0.1 |   0.739 |    1 |      0 | 3.5m |

**Why it lost**: Correct got 1 vote(s) vs winner `19945` with 8 vote(s).

### Code Calls vs No-Code Analysis

| Group          | Answered | None     | Correct | Avg code calls |
| -------------- | -------: | -------: | ------: | -------------: |
| With code (27) | 11 (41%) | 16 (59%) |  1 (4%) |            9.1 |
| No code (5)    | 5 (100%) |   0 (0%) |  0 (0%) |              0 |

### Entropy Signal

- Correct attempts avg entropy: **0.739**
- Wrong attempts avg entropy: **0.738**
- None attempts avg entropy: **0.698**
- Signal: Correct has HIGHER entropy (diff: 0.001) -- entropy weighting would NOT help

---

================================================================================
## Problem `aff75c` — Expected: **3571**, Predicted: **3600**
================================================================================

- **Runs**: 2 (dual-run), **32** total attempts
- **Classification**: **Outvoted**
- **None rate**: 12/32 (38%)
- **Correct answer found**: YES — in 3 attempt(s)
- **Temps that found correct**: 0.3 (2x), 0.5
- **Run(s) that found correct**: 1

### Vote Distribution

| Answer             | Votes | % of answered |
| ------------------ | ----: | ------------: |
| 3600               |     5 |           25% |
| 3571 **(CORRECT)** |     3 |           15% |
| 3601               |     3 |           15% |
| 3599               |     2 |           10% |
| 3658               |     2 |           10% |
| 3540               |     1 |            5% |
| 1802               |     1 |            5% |
| 3543               |     1 |            5% |
| 2774               |     1 |            5% |
| 3165               |     1 |            5% |
| None               |    12 |           38% |

### Run 1 — Per-Attempt Detail

Predicted: 3600, Early stop: False, Votes: {3600: 4, 3571: 3, 3601: 2, 3599: 2, 3543: 1, 1802: 1, 3658: 1, 3540: 1, 2774: 1}

| Att# | Temp | Answer       | Entropy | Code | Errors | Time  | Tokens |
| ---: | ---: | ------------ | ------: | ---: | -----: | ----: | -----: |
|    1 |  0.1 | 3540         |   0.601 |   40 |      0 |  7.0m |  31104 |
|    2 |  0.3 | 3571 **[C]** |   0.618 |   44 |      4 |  8.3m |  27965 |
|    3 |  0.3 | 3600         |   0.792 |    7 |      7 |  7.5m |  16687 |
|    4 |  0.3 | 3600         |   0.646 |   51 |      1 |  8.4m |  35028 |
|    5 |  0.3 | 3571 **[C]** |   0.633 |   48 |      7 |  8.5m |  31804 |
|    6 |  0.5 | 3599         |   0.623 |   69 |      5 | 10.2m |  33839 |
|    7 |  0.5 | 3600         |   0.735 |   32 |      4 |  7.0m |  26674 |
|    8 |  0.5 | 3571 **[C]** |   0.647 |   56 |      4 |  9.6m |  32396 |
|    9 |  0.5 | 3658         |   0.671 |   40 |      2 |  6.2m |  23530 |
|   10 |  0.5 | 3601         |   0.794 |    5 |      0 |  1.6m |   7216 |
|   11 |  0.5 | 1802         |   0.678 |   18 |      2 |  3.4m |  13888 |
|   12 |  0.7 | 3599         |   0.742 |   27 |      3 |  7.1m |  22752 |
|   13 |  0.7 | 3600         |   0.775 |   32 |      2 |  6.2m |  20479 |
|   14 |  0.7 | 3543         |   0.845 |   10 |      0 |  3.4m |  13587 |
|   15 |  0.7 | 3601         |   0.672 |   26 |      2 |  4.8m |  12418 |
|   16 |  0.9 | 2774         |   0.663 |   44 |      7 |  9.7m |  22290 |

### Run 2 — Per-Attempt Detail

Predicted: 3165, Early stop: False, Votes: {3600: 1, 3658: 1, 3601: 1, 3165: 1}

| Att# | Temp | Answer | Entropy | Code | Errors | Time | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ---: | -----: |
|    1 |  0.1 | 3165   |   0.668 |   15 |      0 | 4.0m |  13204 |
|    2 |  0.3 | None   |   0.588 |   37 |      1 | 5.0m |  16959 |
|    3 |  0.3 | None   |   0.698 |   16 |      4 | 5.0m |  12017 |
|    4 |  0.3 | 3658   |   0.694 |   14 |      0 | 1.9m |   7433 |
|    5 |  0.3 | None   |   0.702 |   30 |      4 | 5.0m |  14953 |
|    6 |  0.5 | None   |   0.694 |   27 |      1 | 5.1m |  18441 |
|    7 |  0.5 | 3601   |   0.731 |   11 |      3 | 3.1m |  13279 |
|    8 |  0.5 | None   |   0.660 |   26 |      4 | 5.0m |  20724 |
|    9 |  0.5 | None   |   0.641 |   25 |      5 | 5.0m |  15172 |
|   10 |  0.5 | None   |   0.640 |   23 |      6 | 5.0m |  14311 |
|   11 |  0.5 | None   |   0.645 |   29 |      4 | 5.0m |  16101 |
|   12 |  0.7 | 3600   |   0.825 |    2 |      0 | 1.1m |   5186 |
|   13 |  0.7 | None   |   0.702 |   14 |      3 | 5.0m |  14144 |
|   14 |  0.7 | None   |   0.699 |   33 |      2 | 5.0m |  20913 |
|   15 |  0.7 | None   |   0.763 |   22 |      0 | 5.0m |  20808 |
|   16 |  0.9 | None   |   0.813 |    6 |      6 | 5.9m |  12533 |

### Correct Answer Analysis

Correct answer **3571** was found by **3** of **32** attempts (9%).

Attempts that found correct:

| Run   | Att# | Temp | Entropy | Code | Errors | Time |
| ----- | ---: | ---: | ------: | ---: | -----: | ---: |
| Run 1 |    2 |  0.3 |   0.618 |   44 |      4 | 8.3m |
| Run 1 |    5 |  0.3 |   0.633 |   48 |      7 | 8.5m |
| Run 1 |    8 |  0.5 |   0.647 |   56 |      4 | 9.6m |

**Why it lost**: Correct got 3 vote(s) vs winner `3600` with 5 vote(s).

### Code Calls vs No-Code Analysis

| Group          | Answered | None     | Correct | Avg code calls |
| -------------- | -------: | -------: | ------: | -------------: |
| With code (32) | 20 (62%) | 12 (38%) |  3 (9%) |           27.5 |

### Entropy Signal

- Correct attempts avg entropy: **0.633**
- Wrong attempts avg entropy: **0.715**
- None attempts avg entropy: **0.687**
- Signal: **Correct has LOWER entropy** (diff: 0.082) -- entropy weighting WOULD help

---

================================================================================
## Problem `dbbfe8` — Expected: **22**, Predicted: **8**
================================================================================

- **Runs**: 2 (dual-run), **32** total attempts
- **Classification**: **Outvoted**
- **None rate**: 18/32 (56%)
- **Correct answer found**: YES — in 1 attempt(s)
- **Temps that found correct**: 0.7
- **Run(s) that found correct**: 1

### Vote Distribution

| Answer           | Votes | % of answered |
| ---------------- | ----: | ------------: |
| 8                |     8 |           57% |
| 24               |     2 |           14% |
| 12               |     1 |            7% |
| 22 **(CORRECT)** |     1 |            7% |
| 16               |     1 |            7% |
| 7                |     1 |            7% |
| None             |    18 |           56% |

### Run 1 — Per-Attempt Detail

Predicted: 8, Early stop: True, Votes: {8: 5, 24: 2, 12: 1, 22: 1, 16: 1}

| Att# | Temp | Answer     | Entropy | Code | Errors | Time | Tokens |
| ---: | ---: | ---------- | ------: | ---: | -----: | ---: | -----: |
|    1 |  0.1 | 24         |   0.603 |   53 |     10 | 6.3m |  24300 |
|    2 |  0.3 | 8          |   0.678 |   63 |     15 | 7.7m |  21171 |
|    3 |  0.3 | 8          |   0.712 |   17 |      0 | 2.1m |   8956 |
|    4 |  0.3 | 8          |   0.667 |   25 |      4 | 4.5m |  19039 |
|    5 |  0.3 | 24         |   0.657 |   45 |      3 | 5.9m |  24592 |
|    6 |  0.5 | None       |   0.708 |   42 |      6 | 7.9m |  16098 |
|    7 |  0.5 | 12         |   0.739 |   18 |      6 | 5.0m |  12613 |
|    8 |  0.5 | None       |   0.498 |   43 |     13 | 7.7m |  23610 |
|    9 |  0.5 | None       |   0.604 |   60 |     20 | 7.8m |  22535 |
|   10 |  0.5 | 8          |   0.727 |   12 |      4 | 3.6m |  13433 |
|   11 |  0.5 | None       |   0.586 |   28 |     10 | 7.7m |  21178 |
|   12 |  0.7 | None       |   0.579 |   33 |      8 | 7.8m |  22806 |
|   13 |  0.7 | 8          |   0.634 |   28 |      7 | 6.1m |  15858 |
|   14 |  0.7 | None       |   0.574 |   32 |      7 | 7.7m |  24814 |
|   15 |  0.7 | 22 **[C]** |   0.722 |   28 |      6 | 6.4m |  18727 |
|   16 |  0.9 | 16         |   0.819 |    4 |      4 | 7.2m |  23526 |

### Run 2 — Per-Attempt Detail

Predicted: 8, Early stop: False, Votes: {8: 3, 7: 1}

| Att# | Temp | Answer | Entropy | Code | Errors | Time | Tokens |
| ---: | ---: | ------ | ------: | ---: | -----: | ---: | -----: |
|    1 |  0.1 | 8      |   0.756 |    9 |      1 | 4.0m |  16612 |
|    2 |  0.3 | None   |   0.549 |   36 |      8 | 5.2m |  17788 |
|    3 |  0.3 | None   |   0.670 |   27 |      3 | 5.0m |  18419 |
|    4 |  0.3 | None   |   0.645 |   28 |      5 | 5.0m |  18776 |
|    5 |  0.3 | None   |   0.650 |   20 |      4 | 5.0m |  16351 |
|    6 |  0.5 | 8      |   0.711 |   12 |      3 | 3.7m |  15134 |
|    7 |  0.5 | None   |   0.663 |   16 |      6 | 5.0m |  13408 |
|    8 |  0.5 | None   |   0.663 |   17 |      5 | 5.4m |  16569 |
|    9 |  0.5 | None   |   0.756 |    8 |      5 | 5.2m |  15017 |
|   10 |  0.5 | None   |   0.593 |   35 |     12 | 5.1m |  18549 |
|   11 |  0.5 | None   |   0.625 |   11 |      5 | 5.0m |  16673 |
|   12 |  0.7 | 8      |   0.745 |   14 |      2 | 2.2m |   7347 |
|   13 |  0.7 | 7      |   0.699 |   19 |      4 | 4.1m |  13114 |
|   14 |  0.7 | None   |   0.720 |   21 |      4 | 5.5m |   9611 |
|   15 |  0.7 | None   |   0.765 |   25 |      4 | 5.3m |  16577 |
|   16 |  0.9 | None   |   0.840 |    4 |      4 | 5.5m |  13154 |

### Correct Answer Analysis

Correct answer **22** was found by **1** of **32** attempts (3%).

Attempts that found correct:

| Run   | Att# | Temp | Entropy | Code | Errors | Time |
| ----- | ---: | ---: | ------: | ---: | -----: | ---: |
| Run 1 |   15 |  0.7 |   0.722 |   28 |      6 | 6.4m |

**Why it lost**: Correct got 1 vote(s) vs winner `8` with 8 vote(s).

### Code Calls vs No-Code Analysis

| Group          | Answered | None     | Correct | Avg code calls |
| -------------- | -------: | -------: | ------: | -------------: |
| With code (32) | 14 (44%) | 18 (56%) |  1 (3%) |           26.0 |

### Entropy Signal

- Correct attempts avg entropy: **0.722**
- Wrong attempts avg entropy: **0.704**
- None attempts avg entropy: **0.649**
- Signal: Correct has HIGHER entropy (diff: 0.018) -- entropy weighting would NOT help

---

================================================================================
# Cross-Problem Summary
================================================================================

## Classification Breakdown

| Classification  | Count | Problem IDs                                                            |
| --------------- | ----: | ---------------------------------------------------------------------- |
| Outvoted        |     9 | 21fb4e, 29714f, 3980cd, 414a5b, 86e8e5, 89c921, ae2add, aff75c, dbbfe8 |
| Confident wrong |     6 | 23586c, 3b88b3, 673b29, 9010d9, a824c1, a9dbc8                         |
| Never found     |     1 | 1ec970                                                                 |
| Scattered       |     1 | 26bee3                                                                 |

## Master Table — All 17 Wrong Problems

| Problem  | Expected | Predicted | Class           | Correct Found? | Nones | None% | Unique Ans | Temps (correct) |
| -------- | -------: | --------: | --------------- | -------------- | ----: | ----: | ---------: | --------------- |
| `23586c` |      386 |       773 | Confident wrong | NO             | 20/32 |   62% |          1 | -               |
| `3b88b3` |      979 |       982 | Confident wrong | NO             | 22/32 |   69% |          1 | -               |
| `673b29` |        3 |      3032 | Confident wrong | NO             | 20/32 |   62% |          1 | -               |
| `9010d9` |    10320 |      6400 | Confident wrong | NO             | 21/32 |   66% |          2 | -               |
| `a824c1` |       24 |        13 | Confident wrong | NO             | 17/32 |   53% |          3 | -               |
| `a9dbc8` |    15744 |     15743 | Confident wrong | NO             | 20/32 |   62% |          5 | -               |
| `1ec970` |     8700 |      5000 | Never found     | NO             | 25/32 |   78% |          4 | -               |
| `21fb4e` |       16 |        17 | Outvoted        | YES (2)        | 18/32 |   56% |          4 | 0.5, 0.7        |
| `29714f` |      297 |        99 | Outvoted        | YES (2)        | 16/32 |   50% |          5 | 0.5             |
| `3980cd` |       46 |       642 | Outvoted        | YES (3)        | 14/32 |   44% |          6 | 0.3, 0.5        |
| `414a5b` |       42 |        95 | Outvoted        | YES (6)        | 11/32 |   34% |          5 | 0.3, 0.5, 0.7   |
| `86e8e5` |     8687 |     96985 | Outvoted        | YES (3)        | 17/48 |   35% |         25 | 0.3, 0.5, 0.7   |
| `89c921` |    29800 |     39601 | Outvoted        | YES (5)        | 18/32 |   56% |          3 | 0.1, 0.3, 0.5   |
| `ae2add` |    24931 |     19945 | Outvoted        | YES (1)        | 16/32 |   50% |          5 | 0.1             |
| `aff75c` |     3571 |      3600 | Outvoted        | YES (3)        | 12/32 |   38% |         10 | 0.3, 0.5        |
| `dbbfe8` |       22 |         8 | Outvoted        | YES (1)        | 18/32 |   56% |          6 | 0.7             |
| `26bee3` |      108 |        97 | Scattered       | NO             | 21/32 |   66% |          6 | -               |

## Temperature Pattern for Correct Finds

Which temperatures found the correct answer (across all 17 wrong problems):

| Temperature | # correct finds |
| ----------: | --------------: |
|         0.1 |               2 |
|         0.3 |               5 |
|         0.5 |               7 |
|         0.7 |               4 |

## Entropy Signal Summary

For problems where correct was found (outvoted), does correct have lower entropy?

| Problem  | Correct Entropy | Wrong Entropy | Diff   | Signal       |
| -------- | --------------: | ------------: | -----: | ------------ |
| `21fb4e` |           0.591 |         0.646 | +0.055 | LOWER (good) |
| `29714f` |           0.597 |         0.655 | +0.058 | LOWER (good) |
| `3980cd` |           0.691 |         0.691 | +0.000 | LOWER (good) |
| `414a5b` |           0.719 |         0.742 | +0.023 | LOWER (good) |
| `86e8e5` |           0.608 |         0.619 | +0.011 | LOWER (good) |
| `89c921` |           0.486 |         0.529 | +0.043 | LOWER (good) |
| `ae2add` |           0.739 |         0.738 | -0.001 | HIGHER (bad) |
| `aff75c` |           0.633 |         0.715 | +0.082 | LOWER (good) |
| `dbbfe8` |           0.722 |         0.704 | -0.018 | HIGHER (bad) |

**7/9** outvoted problems have correct answers with lower entropy.

## Code Usage — Correct vs Wrong

- Correct attempts using code: **26/26** (100%)

## Actionable Summary

### Outvoted (9 problems) — Fixable with better voting

- `21fb4e`: correct found 2x, but predicted 17 instead of 16
- `29714f`: correct found 2x, but predicted 99 instead of 297
- `3980cd`: correct found 3x, but predicted 642 instead of 46
- `414a5b`: correct found 6x, but predicted 95 instead of 42
- `86e8e5`: correct found 3x, but predicted 96985 instead of 8687
- `89c921`: correct found 5x, but predicted 39601 instead of 29800
- `ae2add`: correct found 1x, but predicted 19945 instead of 24931
- `aff75c`: correct found 3x, but predicted 3600 instead of 3571
- `dbbfe8`: correct found 1x, but predicted 8 instead of 22

### Confident Wrong (6 problems) — Need strategy diversity

- `23586c`: model consistently says 773, correct is 386
- `3b88b3`: model consistently says 982, correct is 979
- `673b29`: model consistently says 3032, correct is 3
- `9010d9`: model consistently says 6400, correct is 10320
- `a824c1`: model consistently says 13, correct is 24
- `a9dbc8`: model consistently says 15743, correct is 15744

### Never Found (1 problems) — Need stronger model/reasoning

- `1ec970`: expected 8700, never appeared in 32 attempts

### Scattered (1 problems) — No consensus, high variance

- `26bee3`: 6 unique answers, none dominant

