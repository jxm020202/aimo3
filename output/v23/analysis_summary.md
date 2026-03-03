# V23 Analysis Summary

**Run**: 80 problems (97 entries with dual-runs), 16 attempts, ES=5, temp schedule [0.1,0.3×4,0.5×6,0.7×4,0.9]
**Result**: 63/80 correct (78.8%), 313.5 min, OOM crash during nbconvert (80MB notebook)
**OOM cause**: Full conversation logging to stdout made notebook too large. Fix: write to file only.

## Score Breakdown

| Batch | Score |
|-------|-------|
| Priority Debug (dual-run) | 3/4 (86e8e5 correct run 1, wrong run 2) |
| At-Risk (from v22) | 6/6 (all stable) |
| Val Bench (70 new) | 54/70 (16 new failures) |
| Double-Run Retry | 2/17 |
| **Total** | **65/97** |

## Critical Numbers

| Metric | v22 | v23 | Delta |
|--------|-----|-----|-------|
| None rate | 40.4% | **59.2%** | +18.8pp WORSE |
| Total errors | 183 | **1,481** | +8x |
| Correct rate | 96.7% | 78.8% | -17.9pp (harder problems) |
| Runtime | ~70 min | 313.5 min | +4.5x (16 att vs 8) |
| Early stop rate | - | 85% (82/97) | - |

## Top 5 Actionable Findings

### 1. Unavailable Libraries = 145 Wasted Errors (TRIVIAL FIX)
Model tries pulp (74), ortools (53), z3 (10), mip (8) — none installed.
**Fix**: Add to prompt: "NOT available: pulp, ortools, z3, mip, pyscipopt, pysat, constraint."

### 2. Temp=0.9 is Useless (76% None, 7% correct, 54% error rate)
**Fix**: Drop 0.9, replace with more 0.3-0.5 attempts.

### 3. ES=4 = ES=5 Score, Saves 73.5 min (23%)
ES=4 gives 64/97, same as ES=5 but 2.6 fewer avg attempts.
**Fix**: Set ES=4.

### 4. 228 Extractable Answers Lost (24.8% of Nones)
Model produces answer in reasoning/output but regex misses it.
169 of these would have been CORRECT.
**Fix**: Better extraction regex, bare integer on last line, "answer is N" patterns.

### 5. Abort After 3 Errors Per Attempt Saves 1,081 min, Loses Only 1 Problem
**Fix**: Add error counter per attempt, abort at 3.

## Wrong Problems (17)

| ID | Predicted | Expected | Type | Votes |
|----|-----------|----------|------|-------|
| 86e8e5 | 96985 | 8687 | Scattered (13 unique) | Run 1 correct, Run 2 wrong |
| 1ec970 | 5000 | 8700 | Outvoted | 5000×2 vs others |
| 21fb4e | 17 | 16 | Off-by-1, outvoted | 17×4 vs 16×2 |
| 23586c | 773 | 386 | Confident wrong | 773×7 |
| 26bee3 | 97 | 108 | Scattered | 6 unique answers |
| 29714f | 99 | 297 | Outvoted | 99×5 vs 297×1 |
| 3980cd | 642 | 46 | Outvoted | 642×5 vs 46×1 |
| 3b88b3 | 982 | 979 | Off-by-3 | 982×5 |
| 414a5b | 95 | 42 | Outvoted | 95×5 vs 42×1 |
| 673b29 | 3032 | 3 | Confident wrong | 3032×6 |
| 89c921 | 39601 | 29800 | Confident wrong | 39601×5 |
| 9010d9 | 6400 | 10320 | Confident wrong | 6400×5 |
| a824c1 | 13 | 24 | Outvoted | 13×5 vs 26×2 |
| a9dbc8 | 15743 | 15744 | Off-by-1 | 15743×5 |
| ae2add | 19945 | 24931 | Confident wrong | 19945×5 |
| aff75c | 3600 | 3571 | Outvoted, close | 3600×4 vs 3571×3 |
| dbbfe8 | 8 | 22 | Outvoted | 8×5 vs 22×1 |

### Classification
- **Off-by-small** (3): 21fb4e, 3b88b3, a9dbc8 — rounding/precision bugs
- **Outvoted** (9): correct answer appeared but lost vote — 21fb4e, aff75c, 29714f, 3980cd, 414a5b, dbbfe8, ae2add, 1ec970, a824c1
- **Confident wrong** (5): model consistently gets wrong answer — 23586c, 673b29, 89c921, 9010d9, 3b88b3
- **Scattered** (2): no consensus at all — 86e8e5, 26bee3

## Temperature Analysis

| Temp | Attempts | None% | Correct% |
|------|----------|-------|----------|
| 0.1 | 97 | 57% | 27% |
| 0.3 | 388 | 56% | 24% |
| 0.5 | 582 | 59% | 23% |
| 0.7 | 388 | 59% | 21% |
| 0.9 | 97 | 76% | 7% |

## Error Breakdown

| Type | Count | % |
|------|-------|---|
| Timeout | 796 | 53.7% |
| NameError | 239 | 16.1% |
| ImportError | 154 | 10.4% |
| TypeError | 122 | 8.2% |
| Other | 170 | 11.5% |

Recovery rate: 66.9% overall. Retry=8%, simplify=70%, change_approach=74%.

## None Classification (919 total)

| Category | Count | % |
|----------|-------|---|
| other_extraction_failure | 247 | 26.9% |
| timeout | 160 | 17.4% |
| answer_in_output_not_extracted | 123 | 13.4% |
| answer_in_reasoning_not_extracted | 105 | 11.4% |
| no_code_generated | 105 | 11.4% |
| last_turn_error | 79 | 8.6% |
| partial/all_code_errors | 76 | 8.3% |
| print_output_not_parsed | 24 | 2.6% |

## Library Risk

**High error rate**: pulp (66%), z3 (63%), ortools (59%), mip (57%) — ALL unavailable
**Anti-correlated with success**: deque (5% correct), ortools (7%), cmath (8%)
**Positive lift**: heapq (100%), mpmath (75%), random (58%), math (57%)

## Cross-Cutting Insights (from deep analysis)

### Temperature Schedule: Nuanced Picture
- **"Flat 0.5 is best" is WRONG** when accounting for voting dynamics
- Flat 0.5: 67 problems have ≥1 correct attempt, but only 58 win majority vote
- Current schedule: 61/78 (diversity helps fragmentation)
- **Best tested: 0.1×4 + 0.3×8 + 0.5×4 = 62/78**
- Diversity has TWO hidden benefits for hard problems:
  1. **Fragmentation**: wrong answers split across many values, letting correct win with fewer votes (86e8e5)
  2. **Strategy exploration**: different temps trigger different approaches (76aef9: game tree solver only appeared at higher temps)
- **Drop 0.9** (zero unique value). Keep 0.1-0.7.

### Outvoted Problems: 6 True Voting Failures
- Only 6/9 "outvoted" are real (ae2add, 1ec970, a824c1 never found correct)
- "Attractive nuisance" pattern: round/obvious wrong answers (3600=60², 642) emerge in 1-3 turns with 0 code calls
- **Correct answers have LOWER entropy** in 5/6 cases → entropy weighting would help
- Attempts with 0 code calls were NEVER correct in outvoted problems → downweight in voting

### Close Misses: Systematic Bugs
- **a9dbc8** (off-by-1): fencepost error, confuses edge vs vertex count. Correct answer NEVER found.
- **21fb4e** (off-by-1): wrong lower bound proof. Correct found 2/6 times, just outvoted 4:2.
- **3b88b3** (off-by-3): ALL 5 attempts get 982. Completely systematic formula error.
- **aff75c** (off-by-29): MODEL'S OWN CODE computed 3571 (correct!) but model overrode it with reasoning → answered 3600. Lost by 1 vote (3:4).
- **Fix**: "Verify your answer against code output" prompt step.

### Nones Can PROTECT the Vote (Cautionary)
- dd7f5e: 38% None in v22 with 3:2 correct margin → 0% None in v23 with 4:12 correct:wrong
- Better extraction produced more WRONG answers that diluted correct votes
- Extraction improvements must be paired with better vote weighting

### Wrong Problem Categories (for v24 strategy)
| Category | Problems | Fix Type |
|----------|----------|----------|
| Outvoted (correct found) | 21fb4e, aff75c, 29714f, 3980cd, 414a5b, dbbfe8 | Better voting (entropy, min-code filter) |
| Close miss (systematic bug) | a9dbc8, 3b88b3 | Verification step, exact arithmetic |
| Confident wrong | 23586c, 673b29, 89c921, 9010d9 | Strategy diversity, different approaches |
| Model can't solve | ae2add, 1ec970, a824c1, 26bee3 | Need fundamentally different reasoning |
| Non-deterministic | 86e8e5 | More attempts + fragmentation |

## V24 Priority Changes

### Tier 1: Mechanical Fixes (recover ~6 points)
1. **Better voting**: entropy-weighted, downweight 0-code-call attempts, runoff for close races
2. **"Verify against code" prompt step**: catches aff75c-type errors where code is right but reasoning overrides
3. **Add unavailable library list to prompt**: eliminates 145 import errors (pulp/ortools/z3/mip)
4. **Drop temp=0.9**: zero unique value, 76% None, 63% error rate
5. **Write logs to file only**: fix OOM (80MB notebook)
6. **Add `sys.set_int_max_str_digits(100000)` to sandbox**: 14 errors

### Tier 2: Efficiency (save ~100+ min for more attempts)
7. **ES=4**: same score as ES=5, saves 73.5 min
8. **Abort after 3 errors per attempt**: saves 1,081 min, loses 1 problem
9. **Best temp schedule**: 0.1×4 + 0.3×8 + 0.5×4 (drop 0.9, heavier low)

### Tier 3: Strategy Diversity (crack hard problems)
10. **Per-attempt strategy prompts**: force different approaches (algebraic, brute force, modular arithmetic)
11. **"Code first" mandate**: require code execution within first 2 turns (105 no-code attempts)
12. **Better extraction**: 228 lost answers, but careful not to extract wrong answers that dilute votes

## Analysis Reports Index

| File | Contents |
|------|----------|
| `analysis_summary.md` | This file — consolidated findings |
| `outvoted_deep_dive.md` | 9 outvoted problems, "attractive nuisance" pattern, entropy analysis |
| `close_miss_analysis.md` | 4 off-by-small problems, systematic bugs, code-overriding-reasoning |
| `common_problems_deep_comparison.md` | 8 shared v22/v23 problems, fragmentation benefit, dd7f5e cautionary tale |
| `temperature_analysis.md` | Basic temp stats, per-problem matrix |
| `temperature_deep_analysis.md` | Schedule simulations, unique solvers, hard-problem accuracy |
| `v22_vs_v23_comparison.md` | Overall comparison, regressions, improvements |

## New Scripts Created

| Script | What it does |
|--------|-------------|
| `log_exploration/temperature_analysis.py` | Per-temp accuracy, None rate, per-problem matrix, schedule simulation |
| `log_exploration/temperature_deep_analysis.py` | Deep temp: hard-problem accuracy, outvoted matrix, diversity contribution, 7 schedule sims |
| `log_exploration/close_miss_analysis.py` | Auto-find problems where |predicted-expected| < threshold, classify by error type |
