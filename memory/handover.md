# Handover Document — March 6, 2026 (Session 12)

## Where We Stopped

**v18 pushed — ran 50 problems** but used OLD datasets (264-entry DB instead of 340, old 113-problem test CSV instead of 398). Cell 17 gateway also wasted time loading `test_2problems.csv`. Both fixed locally. Need to push v19.

## Current Kaggle State

- **v18**: Ran 50 problems but with old datasets (264 DB, old test CSV). Cell 17 gateway used test_2problems.csv. Fixed locally.
- **v34 (jxm222)**: 24/50 (48%) — last version without Wave 1
- Previous: v17 scored 42/50 on 50 problems

## What Changed This Session (v36 git, v18 Kaggle)

### Cell 8 (CFG)
- `attempts`: 24 → **32**
- `workers`: 24 → **32**
- `wave1_attempts`: 24 → **42**
- `wave1_temperature` replaced with `wave1_temp_schedule = [0.02]*11 + [0.1]*21 + [0.3]*10`
- `temp_schedule`: new 32-entry schedule centered on 0.5 (18/32), range 0.2-0.55

### Cell 12 (AIMO3Sandbox)
- Added missing aliases to `_init_environment()` and `reset()`: `np`, `sp`, `random`, `time`, `nx`
- Added `sys.set_int_max_str_digits(100000)` to `reset()` (was missing)
- Fixes 22% of NameErrors (120/533)

### Cell 14 (AIMO3Solver)
- `_select_taxonomy()` rewritten: basic >50% = basic-only, normal taxonomies >1/3 threshold
- Wave 1 executor: `max_workers=wave1_attempts` (42, independent of Wave 2)
- Wave 1 temperature: indexed from `wave1_temp_schedule` per attempt
- Rerun threshold: hardcoded `5` → `math.ceil(attempts/3)` = 11

### Cell 17 (Test Runner Gateway)
- **BUG FIX**: `test_2problems.csv` → `test_problems.csv` in CSV candidates

### Cell 18 (Test Framework)
- Loads from CSV, shuffles seed=42, takes first 50 (unchanged)

### Test Data
- Combined val+aux+hard30 = **398 problems** (all valid 0-99999)
- Old 113-problem CSV replaced
- `test_2problems.csv` deleted from data/active/
- Uploaded to `shivzzzzzz02/aimo3-test-data`

### Problem DB
- **340 entries** (was 264). Pushed as v10 to `jxm222/aimo3-problem-db`
- Guide for adding entries: `memory/problem-db-guide.md`

## v18 Log Observations (2 problems only)

- Wave 1 classification: 35/42 and 38/40 correct taxonomy — very accurate
- DB notes injection working perfectly — problem 2 (centroid/735-gon trap) got 32/32 correct
- All 42 Wave 1 + 32 Wave 2 attempts fully parallel (wall time = slowest attempt)
- Setup overhead: ~440s (model load 100s, vLLM 124s, pip 200s)
- Some attempts overshoot deadline by up to 25-30s — acceptable, factor into planning

## Architecture: Wave 1 + Wave 2

### Wave 1: Classification
- 42 parallel attempts, temp schedule [0.02]*11+[0.1]*21+[0.3]*10, 100s timeout
- Model sees full taxonomy tree as MCQ options
- Multi-turn: `\Vboxed{taxonomy}` → DB entry shown → `\boxed{taxonomy : id}` confirms
- Voting: basic >50% = basic-only, others >1/3 threshold

### Wave 2: Solving
- 32 parallel attempts, temp schedule centered on 0.5, 400s timeout
- Notes from Wave 1 taxonomies prepended to problem
- Rerun if top votes < ceil(32/3) = 11, merges all 64 results for final vote

## Known Issues

1. **Cell 17 CSV bug** — FIXED locally, not yet pushed
2. **fp8 + prefix caching** — possibly incompatible, but good results so far
3. **Wave 1 time not in reserve** — `reserved_per_problem=150` doesn't account for Wave 1's ~30-50s
4. **Deadline overshoot** — attempts can run up to 30s past `problem_timeout`. Effective max ~430s

## Key Files

```bash
python3 scripts/nb.py list              # 19 cells (0-18)
python3 scripts/nb.py read CELL > /tmp/cell.py
python3 scripts/nb.py write CELL /tmp/cell.py
```

## Kaggle Accounts

- Kernel: `shivzzzzzz02/aimo3-solver`
- DB dataset: `jxm222/aimo3-problem-db` (public, push with jxm222 creds)
- Test data: `shivzzzzzz02/aimo3-test-data` (private)
