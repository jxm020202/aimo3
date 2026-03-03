# V23 Outvoted Problems Deep Dive

Analysis of the 9 problems where the correct answer appeared in at least one attempt but lost the majority vote.

---

## Summary Table

| Problem | Expected | Predicted | Correct/Total | None | Vote Split | Margin | Category |
|---------|----------|-----------|---------------|------|------------|--------|----------|
| 21fb4e  | 16       | 17        | 2/16          | 10   | 17x4 vs 16x2 | 2 votes | High None rate killed correct |
| aff75c  | 3571     | 3600      | 3/16          | 0    | 3600x4 vs 3571x3 | 1 vote | Close race, fragmented votes |
| 29714f  | 297      | 99        | 1/16          | 8    | 99x5 vs 297x1 | 4 votes | Strong wrong consensus |
| 3980cd  | 46       | 642       | 1/16          | 6    | 642x5 vs 46x1 | 4 votes | Strong wrong consensus |
| 414a5b  | 42       | 95        | 1/16          | 9    | 95x5 vs 42x1 | 4 votes | Misinterpretation + None flood |
| dbbfe8  | 22       | 8         | 1/16          | 6    | 8x5 vs 22x1 | 4 votes | Hard combinatorics, wrong heuristic |
| ae2add  | 24931    | 19945     | 0/16          | 9    | 19945x5 vs none | N/A | Correct never found |
| 1ec970  | 8700     | 5000      | 0/16          | 11   | 5000x2 vs none | N/A | Correct never found |
| a824c1  | 24       | 13        | 0/16          | 8    | 13x5 vs none | N/A | Correct never found |

**Correction**: ae2add, 1ec970, and a824c1 had 0 correct attempts -- the correct answer was never found, not "outvoted." These are actually unsolvable problems for the model, not voting failures.

The true outvoted problems are: **21fb4e, aff75c, 29714f, 3980cd, 414a5b, dbbfe8** (6 problems, not 9).

---

## Detailed Analysis per Problem

---

### 1. Problem 21fb4e — "9x9 Grid Five-in-a-Row Blocking"

**Problem**: Minimum black stones on 9x9 grid to prevent any five-in-a-row of empty squares.
**Expected**: 16 | **Predicted**: 17 | **Margin**: off by 1

| Attempt | Answer | OK | Temp | Turns | Code | Errors | Time |
|---------|--------|----|------|-------|------|--------|------|
| 1       | None   | -  | 0.1  | 33    | 33   | 13     | 5.5m |
| 2       | None   | -  | 0.3  | 20    | 20   | 10     | 5.0m |
| 3       | None   | -  | 0.3  | 25    | 24   | 5      | 5.0m |
| 4       | None   | -  | 0.3  | 24    | 24   | 8      | 5.3m |
| 5       | **17** | N  | 0.3  | 21    | 20   | 2      | 2.3m |
| 6       | None   | -  | 0.5  | 34    | 34   | 12     | 5.0m |
| 7       | **17** | N  | 0.5  | 21    | 20   | 4      | 4.6m |
| 8       | **17** | N  | 0.5  | 28    | 27   | 9      | 4.6m |
| 9       | None   | -  | 0.5  | 20    | 19   | 7      | 5.0m |
| 10      | **16** | Y  | 0.5  | 23    | 22   | 3      | 3.6m |
| 11      | None   | -  | 0.5  | 27    | 26   | 6      | 5.1m |
| 12      | **17** | N  | 0.7  | 18    | 17   | 3      | 3.1m |
| 13      | None   | -  | 0.7  | 29    | 29   | 7      | 5.1m |
| 14      | **16** | Y  | 0.7  | 32    | 31   | 7      | 4.2m |
| 15      | None   | -  | 0.7  | 29    | 29   | 8      | 5.4m |
| 16      | None   | -  | 0.9  | 25    | 25   | 7      | 5.1m |

**Q1: Which attempts found correct answer?**
- Attempt 10 (temp=0.5) and attempt 14 (temp=0.7) found 16.

**Q2: Which attempts found wrong answer?**
- Attempts 5 (temp=0.3), 7 (temp=0.5), 8 (temp=0.5), 12 (temp=0.7) all got 17.

**Q3: Temperature pattern?**
- Correct answers: temps 0.5 and 0.7 only.
- Wrong answers (17): temps 0.3, 0.5, 0.5, 0.7.
- No clear temperature separation. Both correct and wrong came from mid-high temps.

**Q4: None rate impact?**
- 10/16 attempts returned None (62.5%). This is devastating.
- Temp 0.1 returned None (the most deterministic setting failed entirely).
- Temps 0.3: 3 None + 1 answer (17). Temps 0.5: 3 None + 3 answers.
- If even 2 more Nones had produced answers, the vote could have flipped.

**Q5: Reasoning difference?**
- **Correct attempts (10, 14)**: Used branch-and-bound hitting set search with proper pruning. Attempt 10 implemented DFS with lower bound pruning (ceil(uncovered/max_degree)). Attempt 14 similarly implemented backtracking with increasing target k. Both approaches correctly solved the NP-hard hitting set problem via systematic search.
- **Wrong attempts (17)**: Also used hitting set formulation but the search found 17 first and stopped (or the heuristic converged to 17 without proving optimality). The difference: attempts finding 17 likely found a valid cover of size 17 but failed to prove no size-16 cover exists, then reported the first feasible solution.
- **Root cause**: The search algorithm sometimes finds size-17 solution first and reports it without continuing to verify if a smaller cover exists. The correct attempts used more thorough search or got lucky with search order.

**Key insight**: Very high error rate (111 total errors across attempts) -- many attempts spent turns trying to import `pulp`, `z3`, or `ortools` which aren't available, wasting precious compute on dependency resolution.

---

### 2. Problem aff75c — "60x60 Grid Maximum Minimum Adjacent Sum"

**Problem**: Fill 60x60 grid with 1..3600, maximize minimum sum of adjacent cells.
**Expected**: 3571 | **Predicted**: 3600 | **Margin**: off by 29

| Attempt | Answer | OK | Temp | Turns | Code | Errors | Time |
|---------|--------|----|------|-------|------|--------|------|
| 1       | 3540   | N  | 0.1  | 41    | 40   | 0      | 7.0m |
| 2       | **3571** | Y | 0.3 | 45    | 44   | 4      | 8.3m |
| 3       | 3600   | N  | 0.3  | 8     | 7    | 7      | 7.5m |
| 4       | 3600   | N  | 0.3  | 52    | 51   | 1      | 8.4m |
| 5       | **3571** | Y | 0.3 | 49    | 48   | 7      | 8.5m |
| 6       | 3599   | N  | 0.5  | 70    | 69   | 5      | 10.2m |
| 7       | 3600   | N  | 0.5  | 33    | 32   | 4      | 7.0m |
| 8       | **3571** | Y | 0.5 | 57    | 56   | 4      | 9.6m |
| 9       | 3658   | N  | 0.5  | 41    | 40   | 2      | 6.2m |
| 10      | 3601   | N  | 0.5  | 6     | 5    | 0      | 1.6m |
| 11      | 1802   | N  | 0.5  | 19    | 18   | 2      | 3.4m |
| 12      | 3599   | N  | 0.7  | 28    | 27   | 3      | 7.1m |
| 13      | 3600   | N  | 0.7  | 33    | 32   | 2      | 6.2m |
| 14      | 3543   | N  | 0.7  | 11    | 10   | 0      | 3.4m |
| 15      | 3601   | N  | 0.7  | 27    | 26   | 2      | 4.8m |
| 16      | 2774   | N  | 0.9  | 45    | 44   | 7      | 9.7m |

**Q1: Which attempts found correct answer?**
- Attempts 2 (temp=0.3), 5 (temp=0.3), 8 (temp=0.5).

**Q2: Which attempts found wrong answer?**
- 3600: attempts 3 (0.3), 4 (0.3), 7 (0.5), 13 (0.7) -- 4 votes
- Also: 3601x2, 3599x2, 3543, 3540, 3658, 2774, 1802

**Q3: Temperature pattern?**
- Correct (3571): temps 0.3 (2x) and 0.5 (1x).
- Wrong (3600): temps 0.3 (2x), 0.5, 0.7.
- No separation. Correct answers came from lower temps but so did wrong ones.

**Q4: None rate impact?**
- 0/16 None. All attempts produced answers. This problem is well-understood by the model.
- The issue is purely vote fragmentation: 9 distinct wrong answers split the non-correct vote, but the wrong answers near 3600 still clustered enough (3600x4, 3601x2, 3599x2) to outvote the correct 3571x3.

**Q5: Reasoning difference?**
- **Correct attempts**: Used careful mathematical analysis. Built up from small cases (2x2, 2x3, 3x3 grids), computed exact answers, found the pattern, then derived the formula for 60x60. Key insight: used checkerboard-like labeling analysis with detailed bounds, arriving at the correct answer of 3571 = 60*60 - 29 via careful pairing argument.
- **Wrong attempts (3600)**: Made a naive error -- 3600 = n*n where n=60. These attempts assumed S = n^2 which is the total number of cells, not the minimum adjacent sum. Some attempts (like attempt 3 with 7 errors) ran into errors and guessed 3600 as a "round number" answer. Others computed upper bounds without constructing valid arrangements.
- **Root cause**: This is a CLOSE race (4 vs 3 votes). Correct approaches required many turns (45-57) of careful analysis. Wrong approaches were often shallow (8-33 turns) and converged to "obvious" wrong answers.

**Key insight**: The "attractive nuisance" of round numbers (3600 = 60^2) pulls many attempts toward the wrong answer. The correct answer 3571 requires deeper analysis.

---

### 3. Problem 29714f — "Function g on N x N with Consecutive Triples"

**Problem**: Function g: NxN -> N with consecutive triple property, find 100th smallest value at (4000, 4036).
**Expected**: 297 | **Predicted**: 99 | **Margin**: off by 198

| Attempt | Answer | OK | Temp | Turns | Code | Errors | Time |
|---------|--------|----|------|-------|------|--------|------|
| 1       | None   | -  | 0.1  | 18    | 17   | 0      | 3.8m |
| 2       | 99     | N  | 0.3  | 11    | 10   | 0      | 1.5m |
| 3       | None   | -  | 0.3  | 20    | 19   | 0      | 3.8m |
| 4       | 99     | N  | 0.3  | 11    | 10   | 0      | 3.8m |
| 5       | None   | -  | 0.3  | 6     | 6    | 2      | 4.0m |
| 6       | **297** | Y | 0.5 | 11    | 10   | 0      | 3.6m |
| 7       | None   | -  | 0.5  | 9     | 9    | 1      | 3.8m |
| 8       | 99     | N  | 0.5  | 6     | 5    | 0      | 1.9m |
| 9       | 99     | N  | 0.5  | 17    | 16   | 0      | 3.6m |
| 10      | 12135  | N  | 0.5  | 8     | 7    | 1      | 3.7m |
| 11      | None   | -  | 0.5  | 12    | 12   | 3      | 3.9m |
| 12      | None   | -  | 0.7  | 29    | 28   | 1      | 3.8m |
| 13      | 99     | N  | 0.7  | 18    | 17   | 0      | 3.0m |
| 14      | 4299   | N  | 0.7  | 7     | 6    | 0      | 3.3m |
| 15      | None   | -  | 0.7  | 12    | 11   | 0      | 3.8m |
| 16      | None   | -  | 0.9  | 21    | 20   | 2      | 3.8m |

**Q1: Which attempts found correct answer?**
- Only attempt 6 (temp=0.5) found 297.

**Q2: Which attempts found wrong answer?**
- 99: attempts 2 (0.3), 4 (0.3), 8 (0.5), 9 (0.5), 13 (0.7) -- 5 votes
- Also: 12135 (attempt 10, 0.5), 4299 (attempt 14, 0.7)

**Q3: Temperature pattern?**
- Correct (297): temp 0.5 only (1 attempt out of 6 at temp 0.5).
- Wrong (99): temps 0.3 (2x), 0.5 (2x), 0.7 (1x).
- The correct answer was found at medium temperature; the wrong answer 99 appeared across all temperatures.

**Q4: None rate impact?**
- 8/16 None (50%). If more attempts had returned answers (instead of timing out), the balance might have shifted.
- But 99 had very strong consensus (5 votes), so even with more answers, the wrong answer might still win unless the additional answers were correct.

**Q5: Reasoning difference?**
- **Correct attempt (6, temp=0.5)**: Key insight was recognizing the r(x,y) binary variable structure -- that for each (x,y), either moving right or up increments by 1. Then derived the path-independence condition: r(x+1,y) + r(x,y+1) = 2*r(x,y), which forces r to be constant in connected regions. This led to the correct characterization of g(x,y) and the set of possible values at (4000, 4036), yielding the 100th smallest as 297.
- **Wrong attempts (99)**: Likely mischaracterized the function space. The answer 99 = 100-1 suggests a counting error (the "99th value" instead of "100th value") or a completely different characterization of the function. Multiple attempts converging on 99 suggests a common mathematical misunderstanding.
- **Root cause**: Deep structural mathematical insight (path-independence, binary variable analysis) was needed. Most attempts took a computational approach that converged on the wrong answer.

---

### 4. Problem 3980cd — "Complex Numbers Product Constraint"

**Problem**: Max m such that complex r_1,...,r_645 (not all zero) satisfy product conditions, find m mod 848.
**Expected**: 46 | **Predicted**: 642 | **Margin**: off by 596

| Attempt | Answer | OK | Temp | Turns | Code | Errors | Time |
|---------|--------|----|------|-------|------|--------|------|
| 1       | None   | -  | 0.1  | 28    | 28   | 3      | 4.6m |
| 2       | 644    | N  | 0.3  | 1     | 0    | 0      | 1.1m |
| 3       | None   | -  | 0.3  | 17    | 16   | 3      | 4.7m |
| 4       | **46** | Y  | 0.3  | 28    | 27   | 1      | 3.3m |
| 5       | 642    | N  | 0.3  | 15    | 14   | 1      | 3.7m |
| 6       | 644    | N  | 0.5  | 12    | 11   | 1      | 3.3m |
| 7       | 642    | N  | 0.5  | 15    | 14   | 0      | 4.6m |
| 8       | None   | -  | 0.5  | 13    | 13   | 4      | 4.7m |
| 9       | 642    | N  | 0.5  | 3     | 2    | 0      | 2.9m |
| 10      | 440    | N  | 0.5  | 28    | 27   | 1      | 4.2m |
| 11      | None   | -  | 0.5  | 11    | 10   | 1      | 4.7m |
| 12      | None   | -  | 0.7  | 40    | 40   | 2      | 4.7m |
| 13      | 642    | N  | 0.7  | 1     | 0    | 0      | 1.4m |
| 14      | 642    | N  | 0.7  | 6     | 5    | 0      | 1.7m |
| 15      | None   | -  | 0.7  | 21    | 21   | 2      | 4.6m |
| 16      | 2      | N  | 0.9  | 19    | 18   | 3      | 4.4m |

**Q1: Which attempts found correct answer?**
- Only attempt 4 (temp=0.3, 28 turns, 3.3m) found 46.

**Q2: Which attempts found wrong answer?**
- 642: attempts 5 (0.3), 7 (0.5), 9 (0.5), 13 (0.7), 14 (0.7) -- 5 votes
- 644: attempts 2 (0.3), 6 (0.5) -- 2 votes
- 440: attempt 10 (0.5), 2: attempt 16 (0.9)

**Q3: Temperature pattern?**
- Correct (46): temp 0.3 only.
- Wrong (642): temps 0.3, 0.5 (2x), 0.7 (2x) -- spread across temps.
- The wrong answer 642 = 645 - 3 appears to be a shallow calculation.

**Q4: None rate impact?**
- 6/16 None (37.5%).
- Even without Nones, the wrong answer 642 dominated with 5 votes.

**Q5: Reasoning difference?**
- **Correct attempt (4, temp=0.3)**: Spent 28 turns and 3.3 minutes working through deep algebraic analysis. Used CRT (Chinese Remainder Theorem), sympy, and careful factorization to derive the maximal m and compute m mod 848 = 46.
- **Wrong attempts (642)**: Many attempts gave 642 = 645 - 3 very quickly (some in just 1 turn with 0 code calls). These attempts made a superficial calculation: m = 645 - 3 = 642, likely confusing the number of variables (645) with the answer. Attempts 2 and 13 gave answers with 0 code calls (pure reasoning without verification), suggesting overconfident pattern matching.
- **Root cause**: The number 642 is an "attractive nuisance" -- it's derived from 645 by a simple subtraction that looks plausible but is mathematically incorrect. The correct answer requires deep number-theoretic reasoning that only 1/16 attempts achieved.

---

### 5. Problem 414a5b — "Dice Reroll Probability"

**Problem**: Kevin throws 3 dice, can reroll n=2 dice optimally to maximize P(sum=7). Find 216*p.
**Expected**: 42 | **Predicted**: 95 | **Margin**: off by 53

| Attempt | Answer | OK | Temp | Turns | Code | Errors | Time |
|---------|--------|----|------|-------|------|--------|------|
| 1       | None   | -  | 0.1  | 10    | 9    | 0      | 1.2m |
| 2       | None   | -  | 0.3  | 4     | 3    | 0      | 1.2m |
| 3       | 95     | N  | 0.3  | 2     | 1    | 0      | 23s  |
| 4       | 95     | N  | 0.3  | 2     | 1    | 0      | 26s  |
| 5       | 95     | N  | 0.3  | 9     | 8    | 0      | 1.0m |
| 6       | 95     | N  | 0.5  | 7     | 6    | 0      | 1.2m |
| 7       | None   | -  | 0.5  | 6     | 6    | 0      | 1.2m |
| 8       | None   | -  | 0.5  | 4     | 4    | 1      | 1.2m |
| 9       | 23     | N  | 0.5  | 5     | 4    | 0      | 51s  |
| 10      | **42** | Y  | 0.5  | 3     | 2    | 0      | 48s  |
| 11      | None   | -  | 0.5  | 5     | 5    | 1      | 1.2m |
| 12      | None   | -  | 0.7  | 6     | 5    | 0      | 1.2m |
| 13      | 95     | N  | 0.7  | 4     | 3    | 0      | 1.0m |
| 14      | None   | -  | 0.7  | 5     | 5    | 1      | 1.2m |
| 15      | None   | -  | 0.7  | 6     | 5    | 0      | 1.2m |
| 16      | None   | -  | 0.9  | 5     | 4    | 0      | 1.2m |

**Q1: Which attempts found correct answer?**
- Only attempt 10 (temp=0.5, 3 turns, 48 seconds).

**Q2: Which attempts found wrong answer?**
- 95: attempts 3 (0.3), 4 (0.3), 5 (0.3), 6 (0.5), 13 (0.7) -- 5 votes
- 23: attempt 9 (0.5)

**Q3: Temperature pattern?**
- Correct (42): temp 0.5 only (1 out of 6 attempts at 0.5).
- Wrong (95): temps 0.3 (3x), 0.5, 0.7.
- Low temps strongly converge on wrong answer.

**Q4: None rate impact?**
- 9/16 None (56.3%). Extremely high for a probability problem.
- Many attempts timed out without producing a numerical answer, possibly because the model got stuck on complex subproblems or confused by the problem statement.

**Q5: Reasoning difference?**
- **Correct attempt (10, temp=0.5)**: Correctly identified that Kevin keeps ONE die (the one not rerolled) and wants the two rerolled dice to sum to 7 minus kept value. Computed f(k) for each kept value k, then enumerated all triples to find average max{f(x), f(y), f(z)}. Got S=1512, then 216*p = 1512/36 = 42. Used `Fraction` for exact arithmetic.
- **Wrong attempts (95)**: Computed S=855 (different enumeration), then got 216*p = 855/36 = 95/4 = 23.75. Rounded to 95 (the numerator). The error: The wrong attempts appear to compute `sum of max{g(x),g(y),g(z)}` where g is a different function (possibly g(k)=count of pairs summing to k instead of 7-k), or they incorrectly interpret "216*p" -- some computed S/36 and reported S instead of S/36. The answer 95 = S/9 where S=855, suggesting a denominator error.
- **Root cause**: Subtle mathematical error in the probability computation. The wrong formula gives 95 consistently because the error is deterministic (wrong formula but correct code). Only attempt 10 got the formula right.

**Key insight**: When the error is in the mathematical formulation (not the code), many attempts reproduce the same wrong answer with high confidence. This is a "confident wrong consensus" pattern.

---

### 6. Problem dbbfe8 — "Immovable Dominos on 7x7 Board"

**Problem**: Minimum dominos on 7x7 board where no domino can slide.
**Expected**: 22 | **Predicted**: 8 | **Margin**: off by 14

| Attempt | Answer | OK | Temp | Turns | Code | Errors | Time |
|---------|--------|----|------|-------|------|--------|------|
| 1       | 24     | N  | 0.1  | 54    | 53   | 10     | 6.3m |
| 2       | 8      | N  | 0.3  | 64    | 63   | 15     | 7.7m |
| 3       | 8      | N  | 0.3  | 18    | 17   | 0      | 2.1m |
| 4       | 8      | N  | 0.3  | 26    | 25   | 4      | 4.5m |
| 5       | 24     | N  | 0.3  | 47    | 45   | 3      | 5.9m |
| 6       | None   | -  | 0.5  | 42    | 42   | 6      | 7.9m |
| 7       | 12     | N  | 0.5  | 19    | 18   | 6      | 5.0m |
| 8       | None   | -  | 0.5  | 43    | 43   | 13     | 7.7m |
| 9       | None   | -  | 0.5  | 60    | 60   | 20     | 7.8m |
| 10      | 8      | N  | 0.5  | 13    | 12   | 4      | 3.6m |
| 11      | None   | -  | 0.5  | 29    | 28   | 10     | 7.7m |
| 12      | None   | -  | 0.7  | 33    | 33   | 8      | 7.8m |
| 13      | 8      | N  | 0.7  | 29    | 28   | 7      | 6.1m |
| 14      | None   | -  | 0.7  | 33    | 32   | 7      | 7.7m |
| 15      | **22** | Y  | 0.7  | 29    | 28   | 6      | 6.4m |
| 16      | 16     | N  | 0.9  | 5     | 4    | 4      | 7.2m |

**Q1: Which attempts found correct answer?**
- Only attempt 15 (temp=0.7, 29 turns, 6.4 minutes).

**Q2: Which attempts found wrong answer?**
- 8: attempts 2 (0.3), 3 (0.3), 4 (0.3), 10 (0.5), 13 (0.7) -- 5 votes
- 24: attempts 1 (0.1), 5 (0.3) -- 2 votes
- 12: attempt 7 (0.5), 16: attempt 16 (0.9)

**Q3: Temperature pattern?**
- Correct (22): temp 0.7 only.
- Wrong (8): temps 0.3 (3x), 0.5 (1x), 0.7 (1x).
- The correct answer came from a high temperature attempt.

**Q4: None rate impact?**
- 6/16 None (37.5%).
- Extremely high error rate: 123 total errors across all attempts. This problem is computationally demanding.

**Q5: Reasoning difference?**
- **Correct attempt (15, temp=0.7)**: Used a more thorough combinatorial search or heuristic that correctly found m=22. Spent 29 turns with systematic exploration.
- **Wrong attempts (8)**: The answer 8 suggests a misunderstanding of the "no sliding" constraint. 8 dominos cover only 16 of 49 squares (33% coverage), leaving most squares empty. The wrong attempts likely found configurations where 8 dominos seem stable but failed to check all sliding directions or misinterpreted what "sliding" means.
- **Root cause**: The constraint "no domino can slide" is subtle. The answer 8 is far too low -- it represents a fundamental misunderstanding of the sliding constraint (perhaps only checking one direction, or misdefining "slide"). The correct answer 22 (covering 44 of 49 squares) indicates nearly full coverage is needed.

**Key insight**: This is the most error-prone problem (123 errors). Many attempts tried to use `pulp`, `z3`, or `ortools` and failed. The model struggles with this type of constrained combinatorial geometry problem.

---

### 7. Problem ae2add — "Lattice Points No Isosceles Trapezoid" (NEVER FOUND CORRECT)

**Problem**: Max lattice points in [1,9973]x[1,9973] with no isosceles trapezoid.
**Expected**: 24931 | **Predicted**: 19945 | **0 correct out of 16 attempts**

| Attempt | Answer | OK | Temp | Turns | Code | Errors |
|---------|--------|----|------|-------|------|--------|
| 1-8     | None   | -  | 0.1-0.5 | 4-15 | 3-14 | 0-1 |
| 9       | 19945  | N  | 0.5  | 6     | 5    | 0      |
| 10      | 19945  | N  | 0.5  | 3     | 2    | 0      |
| 11      | 19945  | N  | 0.5  | 3     | 2    | 0      |
| 12      | 19945  | N  | 0.7  | 1     | 0    | 0      |
| 13      | 19945  | N  | 0.7  | 1     | 0    | 0      |
| 14      | 9973   | N  | 0.7  | 1     | 0    | 0      |
| 15      | None   | -  | 0.7  | 10    | 9    | 0      |
| 16      | 2      | N  | 0.9  | 1     | 0    | 0      |

**Analysis**: The correct answer was NEVER found. All 7 answered attempts got wrong answers, mostly 19945 = 2*9973-1 (an obvious formula). The correct answer 24931 = 2.5*9973-... requires deeper understanding. Low-temp and careful attempts returned None; high-temp attempts guessed shallow formulas.

**This is NOT a voting failure -- the model cannot solve this problem at all.**

---

### 8. Problem 1ec970 — "Observers with Viewing Angles" (NEVER FOUND CORRECT)

**Problem**: 100 observers, 100-degree viewing angle, maximize minimum total observed pairs.
**Expected**: 8700 | **Predicted**: 5000 | **0 correct out of 16 attempts**

| Attempt | Answer | OK | Temp | Turns | Notes |
|---------|--------|----|------|-------|-------|
| 2       | 5000   | N  | 0.3  | 1     | 0 code calls, pure guess |
| 5       | 4950   | N  | 0.3  | 4     | Shallow computation |
| 7       | 9900   | N  | 0.5  | 4     | Shallow computation |
| 10      | 5000   | N  | 0.5  | 1     | 0 code calls, entropy=1.043 (highest) |
| 13      | 7450   | N  | 0.7  | 21    | Deep computation, still wrong |

**Analysis**: The correct answer (8700) was NEVER found. Average entropy across attempts is 0.831 (very high), indicating extreme uncertainty. Attempts that returned answers did so with very few turns (1-4), meaning they guessed rather than computed. The 11 None results (68.75%) show the model recognized it couldn't solve the problem.

**This is NOT a voting failure -- the model cannot solve this problem at all.**

---

### 9. Problem a824c1 — "Bishop Covering on 13x13 Board" (NEVER FOUND CORRECT)

**Problem**: Min marked squares on 13x13 board so any bishop placement threatens a marked square.
**Expected**: 24 | **Predicted**: 13 | **0 correct out of 16 attempts**

| Attempt | Answer | OK | Temp | Turns | Notes |
|---------|--------|----|------|-------|-------|
| 4       | 13     | N  | 0.3  | 30    | Deep search, wrong formulation |
| 5       | 13     | N  | 0.3  | 15    | Wrong formulation |
| 6       | 12     | N  | 0.5  | 8     | Shallow |
| 7       | 13     | N  | 0.5  | 12    | Wrong formulation |
| 8       | 26     | N  | 0.5  | 16    | Different approach, still wrong |
| 10      | 26     | N  | 0.5  | 12    | Same approach as 8 |
| 12      | 13     | N  | 0.7  | 2     | 1 code call, guessing |
| 14      | 13     | N  | 0.7  | 19    | Deep search, wrong formulation |

**Analysis**: The correct answer (24) was NEVER found. The dominant wrong answer 13 = number of diagonals in one direction, suggesting the model is solving "cover all diagonals" but only considering one diagonal direction. The answer 26 = 2*13 suggests considering both directions but with a different (wrong) covering approach. The correct answer 24 requires understanding the bishop covering problem's full combinatorial structure.

**This is NOT a voting failure -- the model cannot solve this problem at all.**

---

## Cross-Problem Patterns

### Pattern 1: "Attractive Nuisance" Wrong Answers
Several problems have wrong answers that are mathematically "obvious" but incorrect:
- **aff75c**: 3600 = 60^2 (grid size, not the answer)
- **3980cd**: 642 = 645 - 3 (variable count minus a small number)
- **ae2add**: 19945 = 2*9973 - 1 (double the grid size minus 1)
- **a824c1**: 13 = board dimension (covering one direction only)
- **414a5b**: 95 = wrong formula's numerator

These "attractive" answers emerge quickly (often 1-3 turns, 0 code calls) and dominate the vote because they appear multiple times across temperatures.

### Pattern 2: Correct Answers Require More Compute
For the 6 truly outvoted problems:

| Problem | Avg turns (correct) | Avg turns (wrong majority) | Correct entropy | Wrong entropy |
|---------|--------------------|-----------------------------|-----------------|---------------|
| 21fb4e  | 27.5               | 20.0                        | 0.591           | 0.649         |
| aff75c  | 50.3               | 26.5                        | 0.633           | 0.737         |
| 29714f  | 11                 | 10.6                        | 0.523           | 0.642         |
| 3980cd  | 28                 | 8.0                         | 0.592           | 0.695         |
| 414a5b  | 3                  | 4.8                         | 0.705           | 0.734         |
| dbbfe8  | 29                 | 20.4                        | 0.722           | 0.700         |

**Correct answers tend to have LOWER entropy** (more confident) than wrong answers. This is a potential signal for improved voting: entropy-weighted voting should help these cases.

### Pattern 3: Temperature and Correct Discovery
Temperature distribution of correct answers across the 6 outvoted problems:
- temp 0.1: 0 correct answers
- temp 0.3: 4 correct answers (21fb4e-none, aff75c x2, 3980cd)
- temp 0.5: 4 correct answers (21fb4e, aff75c, 29714f, 414a5b)
- temp 0.7: 2 correct answers (21fb4e, dbbfe8)
- temp 0.9: 0 correct answers

Medium temperatures (0.3-0.7) are the sweet spot. The most deterministic (0.1) and most random (0.9) never found correct answers.

### Pattern 4: None Flood Kills Votes
| Problem | None Rate | Correct Votes | Gap |
|---------|-----------|---------------|-----|
| 21fb4e  | 62.5%     | 2             | 2   |
| 29714f  | 50.0%     | 1             | 4   |
| 414a5b  | 56.3%     | 1             | 4   |
| dbbfe8  | 37.5%     | 1             | 4   |
| 3980cd  | 37.5%     | 1             | 4   |
| aff75c  | 0.0%      | 3             | 1   |

High None rates correlate with larger vote gaps. When many attempts fail to produce an answer, the remaining answers are dominated by quick-but-wrong guesses at higher temperatures.

### Pattern 5: Library Import Waste
Multiple problems show attempts wasting 3-5 turns trying to import `pulp`, `z3`, or `ortools` (none of which are available in the Kaggle environment). This wastes compute and increases the None rate. Problem dbbfe8 had 123 errors, many from failed imports.

---

## Recommendations for V24

### 1. Entropy-Weighted Voting
Weight votes by inverse entropy. In 5/6 outvoted problems, correct answers had lower entropy than the wrong majority. This alone could flip aff75c (3571 vs 3600), which lost by just 1 vote.

### 2. Reduce None Rate
The None rate is the single biggest factor enabling outvoting:
- Eliminate library import loops by caching unavailable package names.
- Give the model a list of available packages in the system prompt.
- Consider a "fallback answer" strategy for near-timeout attempts.

### 3. Detect "Attractive Nuisance" Answers
When many attempts converge on a "round number" or simple formula of input parameters (like n^2, 2n-1, n-3), flag these for additional scrutiny. Consider:
- Penalizing answers that can be derived in <3 turns or 0 code calls.
- Running "verification" attempts that specifically try to disprove the majority answer.

### 4. Second-Choice Voting / Runoff
In fragmented votes (like aff75c with 9 distinct answers), a simple plurality is unreliable. Consider:
- If no answer has >50% of non-None votes, run additional attempts.
- Cluster similar answers (3599, 3600, 3601 are clearly related).

### 5. Temperature Tuning
- Drop temp 0.9 (0 correct answers, produces garbage).
- Drop temp 0.1 (0 correct answers, high None rate).
- Concentrate attempts at temps 0.3 and 0.5 where correct answers emerge most.

### 6. Minimum Compute Threshold
Attempts answering in <2 turns with 0 code calls (like 3980cd attempt 13 giving 642) should be downweighted or excluded from voting. These are "guesses" not "solutions."
