# Deep Temperature Analysis — v23

**Log**: `output/v23/diagnostic.log`
**Problems**: 78 (64 correct, 14 wrong)
**Temperature schedule**: [0.1, 0.3, 0.5, 0.7, 0.9]
**Attempts per problem**: 16 (across dual-runs: up to 32)

## 1. Per-Temp Accuracy on HARD Problems

Hard = overall result was WRONG or had >70% None rate.

Hard problems identified: 14 / 78

| Temp | Attempts | Correct | Wrong | None | Accuracy% | None% |
|------|----------|---------|-------|------|-----------|-------|
| 0.1 | 28 | 1 | 10 | 17 | 9.1 | 60.7 |
| 0.3 | 112 | 3 | 45 | 64 | 6.2 | 57.1 |
| 0.5 | 168 | 6 | 62 | 100 | 8.8 | 59.5 |
| 0.7 | 112 | 2 | 51 | 59 | 3.8 | 52.7 |
| 0.9 | 28 | 0 | 8 | 20 | 0.0 | 71.4 |

## 2. Correct-But-Outvoted Matrix (Wrong Problems)

For each wrong problem: which temps found the correct answer?

| Problem | Expected | Predicted | 0.1 | 0.3 | 0.5 | 0.7 | 0.9 | Total Correct |
|---------|----------|-----------|--- | --- | --- | --- | ---|---------------|
| 1ec970 | 8700 | 5000 | N/2 | 0/8 | 0/12 | 0/8 | 0/2 | 0 |
| 21fb4e | 16 | 17 | N/2 | 0/8 | **1/12** | **1/8** | N/2 | 2 |
| 23586c | 386 | 773 | 0/2 | 0/8 | 0/12 | 0/8 | 0/2 | 0 |
| 26bee3 | 108 | 97 | 0/2 | 0/8 | 0/12 | 0/8 | 0/2 | 0 |
| 29714f | 297 | 99 | 0/2 | 0/8 | **2/12** | 0/8 | N/2 | 2 |
| 3980cd | 46 | 642 | N/2 | **1/8** | **2/12** | 0/8 | 0/2 | 3 |
| 3b88b3 | 979 | 982 | 0/2 | 0/8 | 0/12 | 0/8 | N/2 | 0 |
| 673b29 | 3 | 3032 | 0/2 | 0/8 | 0/12 | 0/8 | N/2 | 0 |
| 9010d9 | 10320 | 6400 | N/2 | 0/8 | 0/12 | 0/8 | 0/2 | 0 |
| a824c1 | 24 | 13 | N/2 | 0/8 | 0/12 | 0/8 | N/2 | 0 |
| a9dbc8 | 15744 | 15743 | N/2 | 0/8 | 0/12 | 0/8 | N/2 | 0 |
| ae2add | 24931 | 19945 | **1/2** | 0/8 | 0/12 | 0/8 | 0/2 | 1 |
| aff75c | 3571 | 3600 | 0/2 | **2/8** | **1/12** | 0/8 | 0/2 | 3 |
| dbbfe8 | 22 | 8 | 0/2 | 0/8 | 0/12 | **1/8** | 0/2 | 1 |

Legend: **bold** = found correct answer. `N/x` = all None. `0/x` = answered but wrong.

## 3. Unique Solvers

Problems where ONLY one specific temp found the correct answer (no other temp did).

**Temp 0.1**: 1 unique solves
  - `ae2add` (expected=24931) — WRONG overall (outvoted!)

**Temp 0.5**: 1 unique solves
  - `29714f` (expected=297) — WRONG overall (outvoted!)

**Temp 0.7**: 1 unique solves
  - `dbbfe8` (expected=22) — WRONG overall (outvoted!)

**Unique solver summary:**

| Temp | Unique Solves | Of Which Outvoted |
|------|---------------|-------------------|
| 0.1 | 1 | 1 |
| 0.3 | 0 | 0 |
| 0.5 | 1 | 1 |
| 0.7 | 1 | 1 |
| 0.9 | 0 | 0 |

## 4. Near-Miss Analysis by Temperature

Problems where predicted is off-by-small (<=5). Which temps got exact vs near-miss?

### `21fb4e` — Expected: 16, Predicted: 17 (diff=1)

- **Temp 0.1**: None, None
- **Temp 0.3**: None, None, None, 17 (off-by-1), 17 (off-by-1), 17 (off-by-1), 17 (off-by-1), None
- **Temp 0.5**: None, 17 (off-by-1), 17 (off-by-1), None, 16 (EXACT), None, None, None, None, 17 (off-by-1), 17 (off-by-1), 7 (off-by-9)
- **Temp 0.7**: 17 (off-by-1), None, 16 (EXACT), None, None, 7 (off-by-9), 81 (off-by-65), None
- **Temp 0.9**: None, None

### `26bee3` — Expected: 108, Predicted: 97 (diff=11)

- **Temp 0.1**: None, 136 (off-by-28)
- **Temp 0.3**: None, None, 136 (off-by-28), None, 136 (off-by-28), None, None, None
- **Temp 0.5**: 97 (off-by-11), None, None, None, None, None, None, None, None, 256 (off-by-148), None, None
- **Temp 0.7**: 145 (off-by-37), 77 (off-by-31), None, 128 (off-by-20), None, 97 (off-by-11), 256 (off-by-148), None
- **Temp 0.9**: 256 (off-by-148), None

### `3b88b3` — Expected: 979, Predicted: 982 (diff=3)

- **Temp 0.1**: None, 982 (off-by-3)
- **Temp 0.3**: 982 (off-by-3), None, None, None, None, 982 (off-by-3), None, None
- **Temp 0.5**: None, None, 982 (off-by-3), None, None, 982 (off-by-3), 982 (off-by-3), None, 982 (off-by-3), None, None, None
- **Temp 0.7**: 982 (off-by-3), None, 982 (off-by-3), None, None, 982 (off-by-3), None, None
- **Temp 0.9**: None, None

### `a824c1` — Expected: 24, Predicted: 13 (diff=11)

- **Temp 0.1**: None, None
- **Temp 0.3**: None, None, 13 (off-by-11), 13 (off-by-11), None, 13 (off-by-11), 13 (off-by-11), None
- **Temp 0.5**: 12 (off-by-12), 13 (off-by-11), 26 (off-by-2), None, 26 (off-by-2), None, None, None, None, 12 (off-by-12), 13 (off-by-11), 12 (off-by-12)
- **Temp 0.7**: 13 (off-by-11), None, 13 (off-by-11), None, 13 (off-by-11), None, None, 13 (off-by-11)
- **Temp 0.9**: None, None

### `a9dbc8` — Expected: 15744, Predicted: 15743 (diff=1)

- **Temp 0.1**: None, None
- **Temp 0.3**: None, 15745 (off-by-1), None, None, None, 2 (off-by-15742), 2 (off-by-15742), None
- **Temp 0.5**: None, 15743 (off-by-1), 7877 (off-by-7867), None, 15743 (off-by-1), None, None, 15743 (off-by-1), None, None, None, None
- **Temp 0.7**: 15743 (off-by-1), 15743 (off-by-1), 15743 (off-by-1), 1 (off-by-15743), 2 (off-by-15742), None, None, None
- **Temp 0.9**: None, None

### `aff75c` — Expected: 3571, Predicted: 3600 (diff=29)

- **Temp 0.1**: 3540 (off-by-31), 3165 (off-by-406)
- **Temp 0.3**: 3571 (EXACT), 3600 (off-by-29), 3600 (off-by-29), 3571 (EXACT), None, None, 3658 (off-by-87), None
- **Temp 0.5**: 3599 (off-by-28), 3600 (off-by-29), 3571 (EXACT), 3658 (off-by-87), 3601 (off-by-30), 1802 (off-by-1769), None, 3601 (off-by-30), None, None, None, None
- **Temp 0.7**: 3599 (off-by-28), 3600 (off-by-29), 3543 (off-by-28), 3601 (off-by-30), 3600 (off-by-29), None, None, None
- **Temp 0.9**: 2774 (off-by-797), None

### `dbbfe8` — Expected: 22, Predicted: 8 (diff=14)

- **Temp 0.1**: 24 (off-by-2), 8 (off-by-14)
- **Temp 0.3**: 8 (off-by-14), 8 (off-by-14), 8 (off-by-14), 24 (off-by-2), None, None, None, None
- **Temp 0.5**: None, 12 (off-by-10), None, None, 8 (off-by-14), None, 8 (off-by-14), None, None, None, None, None
- **Temp 0.7**: None, 8 (off-by-14), None, 22 (EXACT), 8 (off-by-14), 7 (off-by-15), None, None
- **Temp 0.9**: 16 (off-by-6), None

## 5. First-Correct by Temperature

For each correct problem: which temp FIRST found the correct answer?

| Temp | Times First-Correct | Percentage |
|------|---------------------|------------|
| 0.1 | 26 | 37.1% |
| 0.3 | 38 | 54.3% |
| 0.5 | 5 | 7.1% |
| 0.7 | 1 | 1.4% |
| 0.9 | 0 | 0.0% |

**Interpretation**: Lower temps run first in the schedule (attempt 1 is temp=0.1).
First-correct reflects both schedule position AND inherent accuracy.

First-correct by attempt number:

| Attempt# | Temp | Count |
|----------|------|-------|
| 1 | 0.1 | 26 |
| 2 | 0.3 | 10 |
| 3 | 0.3 | 13 |
| 4 | 0.3 | 10 |
| 5 | 0.3 | 5 |
| 6 | 0.5 | 3 |
| 7 | 0.5 | 1 |
| 10 | 0.5 | 1 |
| 15 | 0.7 | 1 |

## 6. Diversity Contribution

For each temp: how many unique correct problem-answers does it contribute
that would NOT exist with just temp=0.5?

Problems solved by temp=0.5 alone: 67

| Temp | Problems Solved | Unique vs 0.5 | Marginal Value |
|------|-----------------|---------------|----------------|
| 0.1 | 26 | 2 | ['ae2add', 'ddba8e'] |
| 0.3 | 60 | 1 | ['ddba8e'] |
| 0.5 | 67 | 0 | none |
| 0.7 | 52 | 2 | ['dbbfe8', 'ddba8e'] |
| 0.9 | 7 | 1 | ['ddba8e'] |

**Union of all non-0.5 temps adds 3 problems beyond 0.5**: ['ae2add', 'dbbfe8', 'ddba8e']

## 7. Simulated Schedules

We simulate different temperature schedules by subsetting available attempts.
For each schedule, we take up to N attempts at each temp from the available pool,
then majority-vote to determine the answer.

| Schedule | Score | Correct | Wrong | Delta vs Current |
|----------|-------|---------|-------|------------------|
| Flat 0.5 x16 | **58/78** | 58 | 20 | -3 |
| Flat 0.3 x16 | **49/78** | 49 | 29 | -12 |
| 0.3x8 + 0.5x8 | **60/78** | 60 | 18 | -1 |
| 0.1x2 + 0.3x6 + 0.5x8 | **61/78** | 61 | 17 | 0 |
| 0.3x6 + 0.5x6 + 0.7x4 | **59/78** | 59 | 19 | -2 |
| Current [0.1,0.3x4,0.5x6,0.7x4,0.9] | **61/78** | 61 | 17 | 0 |
| Heavy low: 0.1x4 + 0.3x8 + 0.5x4 | **62/78** | 62 | 16 | +1 |
| Conservative: 0.1x2 + 0.3x8 + 0.5x6 | **61/78** | 61 | 17 | 0 |

### Schedule Comparison Details

Problems where schedules DISAGREE (correct in one, wrong in another):

**Flat 0.5 x16** vs Current:
  - GAINED: `89c921` (expected=29800)
  - LOST: `485d27` (expected=29)
  - LOST: `86e8e5` (expected=8687)
  - LOST: `b4ec47` (expected=315)
  - LOST: `ddba8e` (expected=15)

**Flat 0.3 x16** vs Current:
  - GAINED: `aff75c` (expected=3571)
  - LOST: `170362` (expected=12)
  - LOST: `17a3b6` (expected=53)
  - LOST: `19570e` (expected=224)
  - LOST: `27cec1` (expected=2304)
  - LOST: `32690e` (expected=4050)
  - LOST: `676ce2` (expected=666)
  - LOST: `76aef9` (expected=8)
  - LOST: `86e8e5` (expected=8687)
  - LOST: `8fea51` (expected=42)
  - LOST: `c9a608` (expected=11)
  - LOST: `cbbc1b` (expected=96)
  - LOST: `d5054a` (expected=251)
  - LOST: `dd7f5e` (expected=160)

**0.3x8 + 0.5x8** vs Current:
  - GAINED: `aff75c` (expected=3571)
  - LOST: `32690e` (expected=4050)
  - LOST: `dd7f5e` (expected=160)

**0.1x2 + 0.3x6 + 0.5x8** vs Current:
  - GAINED: `aff75c` (expected=3571)
  - LOST: `86e8e5` (expected=8687)

**0.3x6 + 0.5x6 + 0.7x4** vs Current:
  - GAINED: `c19295` (expected=48)
  - LOST: `32690e` (expected=4050)
  - LOST: `76aef9` (expected=8)
  - LOST: `dd7f5e` (expected=160)

**Heavy low: 0.1x4 + 0.3x8 + 0.5x4** vs Current:
  - GAINED: `ae2add` (expected=24931)
  - GAINED: `aff75c` (expected=3571)
  - LOST: `86e8e5` (expected=8687)

**Conservative: 0.1x2 + 0.3x8 + 0.5x6** vs Current:
  - GAINED: `aff75c` (expected=3571)
  - LOST: `86e8e5` (expected=8687)

## 8. Error Rate by Temperature

Which temps produce the most code execution errors? Does low temp = cleaner code?

| Temp | Attempts | Total Errors | Avg Errors | Error-Free% | Correct When Error-Free | Correct When Errors |
|------|----------|--------------|------------|-------------|------------------------|---------------------|
| 0.1 | 97 | 145 | 1.49 | 56.7% | 40.0% (22/55) | 9.5% (4/42) |
| 0.3 | 388 | 358 | 0.92 | 61.1% | 29.5% (70/237) | 14.6% (22/151) |
| 0.5 | 582 | 631 | 1.08 | 56.2% | 31.8% (104/327) | 11.0% (28/255) |
| 0.7 | 388 | 382 | 0.98 | 57.5% | 29.6% (66/223) | 8.5% (14/165) |
| 0.9 | 97 | 157 | 1.62 | 37.1% | 19.4% (7/36) | 0.0% (0/61) |

### Error Type Distribution by Temp

| Temp | Other | NameError | ModuleNotFoundError | TypeError | KeyError | AttributeError | ValueError | ZeroDivisionError |
|------|--- | --- | --- | --- | --- | --- | --- | ---|
| 0.1 | 59 | 26 | 15 | 12 | 8 | 2 | 2 | 3 |
| 0.3 | 168 | 55 | 19 | 34 | 11 | 10 | 6 | 4 |
| 0.5 | 264 | 104 | 79 | 47 | 19 | 22 | 13 | 5 |
| 0.7 | 184 | 46 | 37 | 23 | 12 | 6 | 13 | 2 |
| 0.9 | 122 | 8 | 0 | 5 | 0 | 1 | 6 | 0 |

## 9. Full Problem x Temperature Heat Map

Compact view: for each problem and temp, shows `C`=correct, `W`=wrong, `N`=None, `.`=no attempt.
Shaded row = overall WRONG.

| Problem | Exp | Result | 0.1 | 0.3 | 0.5 | 0.7 | 0.9 |
|---------|-----|--------|--- | --- | --- | --- | ---|
| 1ec970 | 8700 | **WRONG** | 2N | 2W/6N | 3W/9N | 1W/7N | 1W/1N |
| 21fb4e | 16 | **WRONG** | 2N | 4W/4N | 1C/5W/6N | 1C/3W/4N | 2N |
| 23586c | 386 | **WRONG** | 1W/1N | 3W/5N | 4W/8N | 3W/5N | 1W/1N |
| 26bee3 | 108 | **WRONG** | 1W/1N | 2W/6N | 2W/10N | 5W/3N | 1W/1N |
| 29714f | 297 | **WRONG** | 1W/1N | 4W/4N | 2C/5W/5N | 4W/4N | 2N |
| 3980cd | 46 | **WRONG** | 2N | 1C/4W/3N | 2C/5W/5N | 5W/3N | 1W/1N |
| 3b88b3 | 979 | **WRONG** | 1W/1N | 2W/6N | 4W/8N | 3W/5N | 2N |
| 673b29 | 3 | **WRONG** | 2W | 4W/4N | 4W/8N | 2W/6N | 2N |
| 9010d9 | 10320 | **WRONG** | 2N | 4W/4N | 4W/8N | 2W/6N | 1W/1N |
| a824c1 | 24 | **WRONG** | 2N | 4W/4N | 7W/5N | 4W/4N | 2N |
| a9dbc8 | 15744 | **WRONG** | 2N | 3W/5N | 4W/8N | 5W/3N | 2N |
| ae2add | 24931 | **WRONG** | 1C/1N | 2W/6N | 6W/6N | 6W/2N | 1W/1N |
| aff75c | 3571 | **WRONG** | 2W | 2C/3W/3N | 1C/6W/5N | 5W/3N | 1W/1N |
| dbbfe8 | 22 | **WRONG** | 2W | 4W/4N | 3W/9N | 1C/3W/4N | 1W/1N |
| 06788e | 9 | OK | 1W | 2C/2N | 2C/4N | 1C/3N | 1N |
| 095efa | 10609 | OK | 1N | 1C/3N | 4C/2N | 4N | 1N |
| 0aa751 | 6564 | OK | 1N | 1C/3N | 2C/4N | 1C/3N | 1C |
| 0c55f3 | 64 | OK | 1N | 1C/3N | 2C/4N | 2C/1W/1N | 1N |
| 12a146 | 360 | OK | 1C | 1C/3N | 2C/4N | 1C/3N | 1N |
| 1363c5 | 10211 | OK | 1C | 2C/2N | 1C/5N | 1C/3N | 1N |
| 14f73f | 245 | OK | 1C | 2C/2N | 2C/4N | 4N | 1N |
| 170362 | 12 | OK | 1C | 4N | 1C/5N | 3C/1N | 1N |
| 17a3b6 | 53 | OK | 1C | 4N | 2C/4N | 2C/2N | 1N |
| 17fb59 | 2234 | OK | 1C | 2C/2N | 1C/5N | 1C/3N | 1N |
| 19570e | 224 | OK | 1C | 1C/1W/2N | 2C/1W/3N | 1C/2W/1N | 1N |
| 269012 | 751 | OK | 1C | 1C/3N | 3C/3N | 4N | 1N |
| 27cec1 | 2304 | OK | 1N | 2C/2W | 3C/3N | 1W/3N | 1N |
| 2c40d6 | 34628 | OK | 1N | 2C/2N | 1C/5N | 2C/2N | 1N |
| 2d282e | 117 | OK | 1N | 2C/2N | 2C/4N | 1C/3N | 1N |
| 2e2ccb | 876 | OK | 1N | 2C/2N | 2C/4N | 1C/3N | 1N |
| 3070ea | 23 | OK | 1N | 1C/3N | 2C/4N | 2C/2N | 1N |
| 32690e | 4050 | OK | 1C | 1C/2W/1N | 1C/1W/4N | 2C/1W/1N | 1C |
| 3cf8bf | 4 | OK | 1N | 1C/3N | 4C/2N | 4N | 1N |
| 3e5546 | 1250 | OK | 1C | 1C/3N | 1C/5N | 3C/1N | 1N |
| 3edbcf | 247 | OK | 1N | 1C/3N | 3C/3N | 1C/3N | 1N |
| 3eee67 | 27290 | OK | 1N | 2C/2N | 2C/4N | 1C/3N | 1N |
| 414a5b | 42 | OK | 1W/1N | 1C/5W/2N | 3C/6W/3N | 2C/3W/3N | 2N |
| 424e18 | 21818 | OK | 1N | 1C/3N | 3C/3N | 1C/3N | 1N |
| 443a0e | 505 | OK | 1N | 3C/1N | 1C/5N | 1C/3N | 1N |
| 481584 | 820 | OK | 1N | 2C/2N | 2C/4N | 4N | 1C |
| 485d27 | 29 | OK | 1C | 1C/3N | 1C/3W/2N | 2C/1W/1N | 1N |
| 4985d4 | 384 | OK | 1C | 2C/2N | 1C/5N | 4N | 1C |
| 4ebdaa | 196 | OK | 1N | 2C/2N | 2C/4N | 1C/3N | 1N |
| 53de2d | 576 | OK | 1N | 1C/1W/2N | 2C/4N | 2C/1W/1N | 1N |
| 581a58 | 18 | OK | 1W | 3C/1N | 1C/1W/4N | 1W/3N | 1C |
| 676ce2 | 666 | OK | 1C | 1C/1W/2N | 1C/5N | 2C/2N | 1N |
| 69e477 | 1151 | OK | 1N | 2C/2N | 2C/4N | 1C/3N | 1N |
| 6c042a | 88 | OK | 1N | 2C/2N | 3C/3N | 4N | 1N |
| 6c1fb9 | 724 | OK | 1N | 2C/2N | 2C/4N | 1C/3N | 1N |
| 72a159 | 315 | OK | 1N | 2C/2N | 2C/4N | 1C/3N | 1N |
| 76aef9 | 8 | OK | 2N | 3C/5W | 4C/4W/4N | 2C/2W/4N | 1C/1W |
| 777281 | 592 | OK | 1C | 1C/3N | 2C/4N | 1C/3N | 1N |
| 86e8e5 | 8687 | OK | 2W/1N | 1C/6W/5N | 1C/11W/6N | 1C/8W/3N | 1W/2N |
| 89c921 | 29800 | OK | 1C/1W | 1C/4W/3N | 3C/2W/7N | 1W/7N | 1W/1N |
| 8fea51 | 42 | OK | 1N | 1C/1W/2N | 2C/3W/1N | 2C/2N | 1N |
| 9bfdb0 | 90 | OK | 1C | 2C/2N | 2C/4N | 4N | 1N |
| a240b5 | 670 | OK | 1C | 1C/3N | 2C/4N | 1C/3N | 1N |
| a7b83d | 9396 | OK | 1N | 2C/2N | 1C/5N | 2C/2N | 1N |
| a83f0b | 9120 | OK | 1N | 1C/3N | 2C/4N | 2C/2N | 1N |
| a86319 | 56751 | OK | 1C | 1C/3N | 3C/3N | 4N | 1N |
| ac93ce | 424 | OK | 1C | 2C/2N | 1C/5N | 1C/3N | 1N |
| b286eb | 14 | OK | 1C | 1C/3N | 1C/5N | 2C/2N | 1N |
| b4ec47 | 315 | OK | 1C | 2C/2N | 1C/2W/3N | 1C/1W/2N | 1W |
| ba89f9 | 667 | OK | 1N | 2C/2N | 1C/5N | 2C/2N | 1W |
| bad5bf | 67 | OK | 1N | 1C/3N | 3C/3N | 1C/3N | 1W |
| c19295 | 48 | OK | 1N | 1C/3W | 1C/5W | 2C/2W | 1W |
| c4d8d5 | 454 | OK | 1N | 1C/3N | 3C/3N | 1C/3N | 1N |
| c9a608 | 11 | OK | 1N | 4N | 3C/3N | 2C/2N | 1N |
| ca2a54 | 32 | OK | 1N | 2C/2N | 3C/3N | 4N | 1N |
| cbbc1b | 96 | OK | 1N | 4N | 2C/4N | 3C/1N | 1N |
| cf3142 | 462 | OK | 1N | 1C/3N | 1C/5N | 3C/1N | 1N |
| d5054a | 251 | OK | 1N | 4N | 3C/3N | 2C/2N | 1N |
| d5f758 | 886 | OK | 1C | 2C/2N | 1C/5N | 1C/3N | 1N |
| d6f389 | 258 | OK | 1N | 2C/2N | 2C/4N | 2C/2N | 1N |
| d75200 | 571 | OK | 1C | 2C/2N | 2C/4N | 4N | 1N |
| dd7f5e | 160 | OK | 1C | 4W | 2C/4W | 1C/3W | 1W |
| ddba8e | 15 | OK | 1C | 1C/3N | 6N | 2C/2N | 1C |
| e5a7c0 | 11021 | OK | 1N | 1C/3N | 3C/3N | 1C/3N | 1N |

## 10. Key Findings & Recommendations

1. **Best single temperature**: 0.5 (solves 67/78)
2. **Current schedule**: solves 61/78

3. **Temp 0.9 unique value**: solves 0 problems that no other temp solves → DROP

4. **Temp 0.1 unique value**: solves 1 problems that no other temp solves → KEEP
   - `ae2add`

5. **Best simulated schedule**: "Heavy low: 0.1x4 + 0.3x8 + 0.5x4" → 62/78
   This is +1 over current schedule!

6. **Outvoted correct answers**: 6/14 wrong problems had the correct answer in at least one attempt
   These represent the gap between "can solve" and "does solve" — voting/aggregation improvements matter here.

7. **Near-miss (off-by-<=5)**: 3 wrong problems. These may benefit from answer refinement/self-check.

