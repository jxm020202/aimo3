# v22 vs v23 Comparison Analysis

## Executive Summary

| Metric | v22 | v23 | Delta |
|--------|-----|-----|-------|
| **Score** | 58/60 (97%) | 65/97 (67%) | +7 raw, -30% accuracy |
| **Total time** | 70.0 min | 313.5 min | +243.5 min |
| **Avg time/problem** | 70s | 194s | +124s |
| **Budget utilization** | 7.8% | 35.7% | +27.9% |
| **Total attempts** | 480 | 1,552 | +1,072 |
| **None rate** | 58.3% | 59.2% | +0.9% |
| **Total errors** | 252 | 1,673 | +1,421 |
| **Early stops** | 59/60 (1 wrong) | 82/97 (20 wrong) | +19 wrong |
| **Tokens** | 2,702,070 | 14,314,309 | +11.6M |

**Key takeaway**: v22 and v23 are NOT directly comparable on overall accuracy because they ran different problem sets. v22 ran 60 curated problems (reference + benchmarks). v23 ran 97 problems including 70 new unseen validation problems. The 8 common problems are the only valid head-to-head comparison.

---

## Problem Set Differences

- **v22**: 60 problems across 4 batches (REFERENCE PROBLEMS, HARD BENCHMARK, RANDOM 10, COMPREHENSIVE BENCHMARK)
- **v23**: 97 problems across 4 batches:
  - AT-RISK PROBLEMS: 6/6 (100%) -- same 6 at-risk problems
  - PRIORITY DEBUG (dual-run): 3/4 (75%) -- includes 86e8e5 + 76aef9
  - VAL BENCH (new unseen): 54/70 (77%) -- brand new problems
  - DOUBLE-RUN RETRY: 2/17 (12%) -- second pass on hard problems
- **Only 8 problems overlap** between the two runs

---

## 1. Problem Flips (8 common problems)

### Gained (wrong -> correct): 1
- **76aef9**: v22 predicted 999 (wrong), v23 predicted 8 (CORRECT)
  - v22 votes: {999: 3} -- model was stuck on wrong answer
  - v23 votes: {8: 5, 999: 4, 1997: 2, 1: 2} -- correct answer emerged with more attempts (16 vs 8)
  - This is a clear win from the increased attempt count

### Lost (correct -> wrong): 0
No regressions on the 8 common problems.

### Stable correct: 6
All 6 at-risk problems remained correct: 424e18, dd7f5e, b4ec47, 2d282e, 8fea51, 269012

### Stable wrong: 1
- **86e8e5**: Still wrong in both runs
  - v22: predicted 23, expected 8687 (votes: {8687: 2, 23: 2, 2404: 1, 41754: 1})
  - v23: predicted 40958, expected 8687 (votes: {4: 1, 40958: 1})
  - v23 is WORSE: only 2 non-None attempts out of 16, and neither found the correct answer
  - v22 at least had 2 votes for the correct answer (8687)
  - 86e8e5 has 14/16 Nones and 28 errors in v23 -- this problem is severely broken

---

## 2. At-Risk Problems (424e18, dd7f5e, b4ec47, 2d282e, 8fea51, 269012)

All 6 at-risk problems are **CORRECT** in both v22 and v23. No regressions.

| Problem | v22 Pred | v23 Pred | Expected | v22 Nones | v23 Nones | Status |
|---------|----------|----------|----------|-----------|-----------|--------|
| 424e18 | 21818 | 21818 | 21818 | 38% | 69% | STABLE OK |
| dd7f5e | 160 | 160 | 160 | 38% | 0% | STABLE OK (improved nones) |
| b4ec47 | 315 | 315 | 315 | 38% | 44% | STABLE OK |
| 2d282e | 117 | 117 | 117 | 50% | 69% | STABLE OK |
| 8fea51 | 42 | 42 | 42 | 50% | 44% | STABLE OK |
| 269012 | 751 | 751 | 751 | 50% | 69% | STABLE OK |

**Concern**: None rates increased for 4/6 at-risk problems (424e18, b4ec47, 2d282e, 269012). dd7f5e improved dramatically (38% -> 0%). Despite higher None rates, all still get correct answers because the non-None attempts consistently converge.

---

## 3. Priority Debug: 86e8e5 and 76aef9

### 76aef9 -- FIXED
- v22: WRONG (pred=999), v23: CORRECT (pred=8)
- v23 gave it 16 attempts instead of 8, and the correct answer (8) got 5 votes vs 999's 4 votes
- The model CAN solve this problem -- it just needs enough attempts for correct answers to outvote wrong ones

### 86e8e5 -- STILL BROKEN, WORSE
- v22: WRONG (pred=23, exp=8687), v23: WRONG (pred=40958, exp=8687)
- v23 is significantly worse: 14/16 attempts produced None, 28 errors
- v22 at least had 2 votes for the correct answer; v23 has zero
- This problem generates massive errors and the model cannot produce valid code for it
- This remains the hardest unsolved reference problem

---

## 4. None Rate Comparison

| Metric | v22 | v23 |
|--------|-----|-----|
| Overall None rate | 58.3% (280/480) | 59.2% (919/1552) |
| Extraction failures (answer text but None) | 132 (47% of Nones) | 498 (54% of Nones) |

The None rate is effectively unchanged (+0.9%). The extraction failure rate worsened slightly (47% -> 54%), meaning more attempts produce answer-like text that the extraction regex fails to capture.

### None rate by v23 batch:
- AT-RISK PROBLEMS: 49% (better than overall)
- PRIORITY DEBUG: 20% (much better -- dual-run helps)
- VAL BENCH (new unseen): 62% (worst)
- DOUBLE-RUN RETRY: 61% (still high on retries)

---

## 5. Error Rate Comparison

| Metric | v22 | v23 |
|--------|-----|-----|
| Total errors | 252 | 1,673 |
| Errors/attempt | 0.53 | 1.08 |
| Error trend | IMPROVING (0.75 -> 0.30) | WORSENING (0.96 -> 1.20) |
| Attempts with errors | 143 | -- |

v23 has roughly 2x the error rate per attempt. The error trend in v23 is worsening over time (first half 0.96, second half 1.20), while v22 was improving.

### Errors by v23 batch:
- PRIORITY DEBUG: 2.06 errors/attempt (worst -- complex problems)
- DOUBLE-RUN RETRY: 1.57 errors/attempt
- AT-RISK PROBLEMS: 1.14 errors/attempt
- VAL BENCH: 0.90 errors/attempt (best)

---

## 6. Early Stop Analysis

| Metric | v22 | v23 |
|--------|-----|-----|
| Early stops | 59/60 (98%) | 82/97 (85%) |
| Wrong early stops | 1 | 20 |

**Critical**: v23 has 20 false-positive early stops -- problems where the model early-stopped on a wrong answer. This is a 20x increase from v22's single false positive. This is likely because:
1. v23 includes harder problems where the model converges on wrong answers
2. The early stop threshold may be too aggressive for harder problem sets

---

## 7. Time Comparison

| Metric | v22 | v23 |
|--------|-----|-----|
| Min time | 3s | 11s |
| Median time | 45s | 154s |
| Max time | 495s | 922s |
| Total time | 70.0 min | 313.5 min |
| Budget used | 7.8% | 35.7% |

v23 uses 4.5x more time than v22. This is expected because:
- v23 has 16 attempts/problem vs v22's 8
- v23 has 97 problems vs v22's 60
- v23 problems are generally harder (new unseen validation set)

**Common problem timing** (8 overlapping problems):
- 86e8e5: 495s -> 331s (-163s, fewer successful attempts = less time)
- dd7f5e: 210s -> 288s (+79s, 0% None rate in v23 = more compute on actual answers)
- 76aef9: 136s -> 226s (+91s, more attempts finding correct answer)

---

## 8. v23 New Problem Performance (VAL BENCH)

54/70 (77%) on new unseen problems is a strong baseline. The 16 wrong problems break down as:

### Outvoted (correct answer was in votes): 6
- **21fb4e**: pred=17, exp=16 (OFF-BY-1), outvoted 4:2
- **29714f**: pred=99, exp=297, outvoted 5:1
- **3980cd**: pred=642, exp=46, outvoted 5:1
- **414a5b**: pred=95, exp=42, outvoted 5:1
- **aff75c**: pred=3600, exp=3571 (VERY CLOSE 1.008x), outvoted 4:3
- **dbbfe8**: pred=8, exp=22, outvoted 5:1

### Near-misses (close to correct but wrong): 4
- **21fb4e**: OFF-BY-1 (17 vs 16)
- **3b88b3**: OFF-BY-3 (982 vs 979)
- **a9dbc8**: OFF-BY-1 (15743 vs 15744)
- **aff75c**: within 1% (3600 vs 3571)

### Model fundamentally wrong: 10
- Problems where no attempt found the correct answer or was very far off

---

## 9. DOUBLE-RUN RETRY Performance

Only 2/17 correct (12%) -- the retry batch performed very poorly. These are the hardest problems that failed in the first pass, and giving them a second pass with the same model/approach does not help.

Notable failures:
- **86e8e5**: 14/16 Nones, 28 errors (completely broken)
- **21fb4e**: OFF-BY-1 on retry too (17 vs 16)
- **aff75c**: outvoted on retry too (3165 vs 3571)
- **dbbfe8**: 75 errors, high None rate

---

## 10. Key Conclusions

### What improved v22 -> v23:
1. **76aef9 fixed** -- 16 attempts (vs 8) gave correct answer enough votes to win
2. **All at-risk problems stable** -- no regressions on the 6 monitored problems
3. **Budget utilization up** -- using 36% of budget vs 8%, getting more compute per problem

### What worsened v22 -> v23:
1. **86e8e5 degraded** -- went from having 2 correct votes to having zero
2. **Error rate doubled** (0.53 -> 1.08 errors/attempt) and trend is worsening
3. **Early stop false positives** surged from 1 to 20
4. **None rate unchanged** at ~59% despite prompt improvements

### Top actionable items for v24:
1. **Fix early stop false positives**: 20 problems early-stopped on wrong answer. Increase threshold or add entropy/confidence check before stopping.
2. **Fix near-misses**: 4 problems are off-by-1 or off-by-3 -- add rounding/integer check to final answer extraction.
3. **Fix outvoted problems**: 6 problems had the correct answer but wrong answer won. Improve voting weights (entropy, recency, confidence).
4. **Fix extraction**: 54% of Nones had answer text that wasn't extracted. Improve regex patterns.
5. **Reduce error rate**: 2x error rate suggests prompt or code execution issues. Investigate top error types.
6. **86e8e5**: Needs special handling -- possibly a different prompt strategy or problem decomposition.
