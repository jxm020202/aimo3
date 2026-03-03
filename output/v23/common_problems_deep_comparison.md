# Deep Comparison: 8 Common Problems Between v22 and v23

## Executive Summary

8 problems appear in both v22 and v23 diagnostic runs. 6 stayed correct; 2 flipped from WRONG to OK.

**Key structural differences between runs:**
- v22: 8 attempts/problem, no temperature schedule, early_stop threshold=3
- v23: 16 attempts/problem, temperature schedule (0.1/0.3/0.3/0.3/0.3/0.5/0.5/0.5/0.5/0.5/0.5/0.7/0.7/0.7/0.7/0.9), early_stop threshold=5

---

## Part 1: Stable-Correct Problems (6)

### Problem `269012` — Cube geometry (answer: 751)

| Metric | v22 | v23 | Change |
|--------|-----|-----|--------|
| Attempts | 8 | 16 | +8 |
| Answered | 4 | 5 | +1 |
| None | 4 | 11 | +7 (worse) |
| Correct votes | 3 (751) | 5 (751) | +2 |
| Wrong votes | 1 (101) | 0 | improved |
| Vote margin | 3:1 | 5:0 | unanimous |
| Total tokens | 155.0K | 244.0K | +57% |
| Total errors | 4 | 4 | same |
| Wall time | 3.6m | 4.1m | +14% |
| Early stop | Yes(3) | Yes(5) | - |

**Analysis:** In v23, the correct answer became unanimous (5/5 answered attempts all said 751, vs 3:1 in v22). However, the None rate increased dramatically (11/16 = 69% vs 4/8 = 50%). The extra attempts didn't produce more *answered* results -- they mostly timed out or failed to extract. The problem was already solved in v22; v23 just made the margin safer at cost of more Nones.

**Temperature impact:** Correct answers came from temps 0.1, 0.3, 0.5 -- the lowest temps. Higher temps (0.7, 0.9) all produced Nones.

**Approach:** Same core strategy in both: sympy determinant to find cube side length s=6, then Monte Carlo to verify water volume = 747/4 = 186.75, yielding m+n = 751.

---

### Problem `2d282e` — Bin packing/groups (answer: 117)

| Metric | v22 | v23 | Change |
|--------|-----|-----|--------|
| Attempts | 8 | 16 | +8 |
| Answered | 4 | 5 | +1 |
| None | 4 | 11 | +7 (worse) |
| Correct votes | 3 (117) | 5 (117) | +2 |
| Wrong votes | 1 (118) | 0 | improved |
| Vote margin | 3:1 | 5:0 | unanimous |
| Total tokens | 54.3K | 64.2K | +18% |
| Total errors | 0 | 1 | +1 |
| Wall time | 1.2m | 53.0s | -37% (faster!) |
| Early stop | Yes(3) | Yes(5) | - |

**Analysis:** This is the most token-efficient problem across both runs. Most attempts are 1-turn, either pure reasoning or one code call. In v23, answer became unanimous (5:0 vs 3:1). Wall time actually decreased because the problem solves quickly and early stop kicks in.

**Temperature impact:** Correct answers at temps 0.3, 0.5, 0.7 -- broad range. Low temp (0.1) produced None. Very high temp (0.9) also None. The sweet spot is 0.3-0.7.

**None rate concern:** 11/16 = 69% Nones in v23 vs 4/8 = 50% in v22. Many Nones are extraction failures on this reasoning-heavy problem (model derives answer in reasoning but doesn't output it cleanly).

**Approach:** Same in both: bin packing optimization loop over number of items, computing ceiling of remaining capacity. Both versions have the off-by-one confusion between 117 and 118, but correct attempts resolve it.

---

### Problem `424e18` — Tournament/runners (answer: 21818)

| Metric | v22 | v23 | Change |
|--------|-----|-----|--------|
| Attempts | 8 | 16 | +8 |
| Answered | 5 | 5 | same |
| None | 3 | 11 | +8 (worse) |
| Correct votes | 3 (21818) | 5 (21818) | +2 |
| Wrong votes | 2 (62140) | 0 | eliminated |
| Vote margin | 3:2 | 5:0 | unanimous |
| Total tokens | 77.7K | 166.6K | +114% |
| Total errors | 11 | 15 | +4 |
| Wall time | 2.0m | 2.6m | +30% |
| Early stop | Yes(3) | Yes(5) | - |

**Analysis:** Major improvement in reliability. v22 had a tight 3:2 vote split (21818 vs 62140), meaning this was dangerously close to being wrong. v23 made it unanimous 5:0. The competitor answer 62140 was completely eliminated. However, token cost more than doubled.

**Temperature impact:** Correct answers came from temps 0.3, 0.5, 0.7 -- all mid-range. Low temp (0.1) produced None. Highest temp (0.9) also None.

**Error rate:** More errors in v23 (15 vs 11), but they didn't propagate to final answers. The errors are mostly timeout/runtime issues in simulation code.

**Approach:** Both versions use combinatorial simulation of tournament brackets. v22 had attempts that computed the wrong combinatorial formula (giving 62140). v23's temperature diversity may have avoided getting stuck in that wrong formula.

---

### Problem `8fea51` — Base-7 digit removal (answer: 42)

| Metric | v22 | v23 | Change |
|--------|-----|-----|--------|
| Attempts | 8 | 16 | +8 |
| Answered | 4 | 9 | +5 |
| None | 4 | 7 | +3 |
| Correct votes | 3 (42) | 5 (42) | +2 |
| Wrong votes | 1 (0) | 4 (6:2, 24:1, 0:1) | +3 |
| Vote margin | 3:1 | 5:4 | tighter! |
| Total tokens | 81.1K | 138.0K | +70% |
| Total errors | 7 | 14 | +7 |
| Wall time | 2.6m | 3.1m | +19% |
| Early stop | Yes(3) | Yes(5) | - |

**Analysis:** Interesting case -- the vote margin actually got WORSE in v23. v22 was 3:1, but v23 is 5:4. The extra attempts produced more wrong answers too (answer=6 appeared twice, plus 24 and 0). The problem is code-heavy (200+ code calls) with many turns, making it error-prone at higher temperatures.

**Temperature impact:** Correct answers at temps 0.3, 0.5, 0.7. Wrong answers at temps 0.3, 0.5 also. No clear temperature pattern -- this problem's difficulty is inherent.

**None rate:** Actually improved somewhat (7/16=44% vs 4/8=50%), meaning more attempts extracted *something*, but some of those extracted wrong answers.

**Approach:** Both versions do brute-force search over base-7 numbers checking the digit-removal sum property. The difference is in search range and verification -- some attempts search too small a range and get 0 or incomplete counts.

---

### Problem `b4ec47` — Dodecagon rectangles (answer: 315)

| Metric | v22 | v23 | Change |
|--------|-----|-----|--------|
| Attempts | 8 | 16 | +8 |
| Answered | 5 | 9 | +4 |
| None | 3 | 7 | +4 |
| Correct votes | 3 (315) | 5 (315) | +2 |
| Wrong votes | 2 (6:1, 24:1) | 4 (39:2, 60:1, 27:1) | +2 |
| Vote margin | 3:2 | 5:4 | similar risk |
| Total tokens | 146.4K | 206.1K | +41% |
| Total errors | 13 | 43 | +230% |
| Wall time | 3.6m | 4.3m | +19% |
| Early stop | Yes(3) | Yes(5) | - |

**Analysis:** This problem has the most dramatic error increase: 43 errors in v23 vs 13 in v22 (3.3x). The extra attempts at higher temperatures produce more runtime errors and wrong geometric computations. Vote margin stayed similarly tight (3:2 -> 5:4). This is a computationally intensive geometry problem with many code calls (217 in v22, 310 in v23).

**Temperature impact:** Correct answers at temps 0.1, 0.3, 0.5, 0.7. Wrong answers appear at 0.5, 0.7, 0.9. Higher temps clearly increase error rate on computational geometry.

**Approach:** Both versions enumerate lines through dodecagon vertices and check for rectangle configurations. The approach is identical but error-prone -- many attempts get partial counts (6, 24, 27, 39, 60) due to miscounting or incomplete enumeration.

---

### Problem `dd7f5e` — Function space convolution (answer: 160)

| Metric | v22 | v23 | Change |
|--------|-----|-----|--------|
| Attempts | 8 | 16 | +8 |
| Answered | 5 | 16 | +11 |
| None | 3 | 0 | eliminated! |
| Correct votes | 3 (160) | 4 (160) | +1 |
| Wrong votes | 2 (71:1, 114:1) | 12 (varied) | +10 |
| Vote margin | 3:2 | 4:3 (160 vs 80+44) | tighter |
| Total tokens | 126.5K | 220.0K | +73% |
| Total errors | 16 | 32 | +100% |
| Wall time | 3.5m | 4.8m | +37% |
| Early stop | Yes(3) | No(5) | didn't trigger |

**Analysis:** The most striking change: Nones went from 3 to 0 (100% extraction rate in v23!). However, this came at a cost -- many wrong answers flooded in. The vote was actually tighter: 4 correct (160) vs 3 votes each for 80 and 44, plus scattered others. The problem barely won the majority. This is a case where **better extraction + higher temps = more wrong answers competing with the correct one**.

**Temperature impact:** The sole correct answer at temp 0.1 (attempt 1, pure reasoning, 0 code calls!) is the most reliable. Higher temps (0.3-0.9) produced 12 different wrong answers. This problem benefits enormously from low temperature.

**None rate:** Going from 38% to 0% is impressive but misleading -- the Nones in v22 were protecting the vote by not diluting it with wrong answers.

**Approach:** v22 correct attempts used algebraic reasoning + code verification (polynomial ring structure). v23 attempts at higher temps explored wrong formulations (polynomial convolution, matrix approaches) that produced plausible but wrong numbers.

---

## Part 2: Flipped Problems (WRONG -> OK)

### Problem `86e8e5` — Norwegian numbers (answer: 8687)

**The Problem:** Find the smallest n-Norwegian positive integer (having 3 distinct divisors summing to n), then compute a number-theoretic function involving 3^{2025!}.

| Metric | v22 | v23 | Change |
|--------|-----|-----|--------|
| Attempts | 8 | 16 | +8 |
| Answered | 6 | 14 | +8 |
| None | 2 | 2 | same |
| Correct votes | 2 (8687) | 3 (8687) | +1 |
| Wrong votes | 4 (23:2, 2404:1, 41754:1) | 11 (scattered) | +7 |
| Vote margin | 2:2 TIE (lost!) | 3:1:1:1:1:1:1:1:1:1:1 (won!) | flipped |
| Total tokens | 253.9K | 534.9K | +111% |
| Total errors | 30 | 61 | +103% |
| Wall time | 8.2m | 13.5m | +65% |
| Early stop | No(3) | No(5) | - |

**WHY DID IT FLIP?**

In v22, the vote was a 2:2 tie between 8687 (correct) and 23 (wrong). Tiebreaking apparently chose 23. In v23, the vote was 3 for 8687 vs a scattered field of 11 different wrong answers. The wrong answers in v23 are all unique (64020, 31033, 46426, 73218, 54680, 11, 93764, 91036, 23, 82588, 41754) -- each appears only once. So the correct answer 8687 wins plurality with just 3 votes.

**The extra attempts helped by fragmenting the wrong answers.** In v22, wrong attempts coalesced around 23 (2 votes). In v23 with higher temperatures, wrong attempts produced diverse wrong answers instead of clustering on one wrong answer. This is the "diversity advantage" of temperature scheduling.

**Correct attempt details in v23:**
- Attempt 4 (temp=0.3): 72 turns, 71 code calls, 7.2min. Used sympy divisor enumeration + number-theoretic formulas. Methodical brute force.
- Attempt 7 (temp=0.5): NOT correct (answer=23, 42 turns, 41 code calls). The temp 0.5 attempt went wrong.
- Attempt 14 (temp=0.7): Correct! 46 turns, 45 code calls, 7.0min. Used sympy.factorint, CRT (Chinese Remainder Theorem), fractions. More sophisticated number theory.
- Attempt 16 (temp=0.9): Correct! (from the full data)

**v22 correct attempts:**
- Attempt 5 (no temp info): 21 turns, 20 code calls, 5.2min. Used fraction arithmetic, divisor search.
- Attempt 7: 38 turns, 37 code calls, 6.4min. Similar approach.

**Key insight:** The problem requires computing f(n) values up to large n, then analyzing a sum involving 3^{2025!}. This needs both careful brute force AND number-theoretic insight. v23's temperature diversity at 0.3 and 0.7 both produced correct answers through different approaches, while v22 only got 2 correct out of 8 attempts.

**Libraries used in correct v23 attempts:**
- Attempt 4: math, itertools, sympy, fractions
- Attempt 14: sympy.factorint, sympy.ntheory.modular.crt, fractions, math

The CRT-based approach in attempt 14 is notably more sophisticated than v22's approaches.

---

### Problem `76aef9` — Game theory/cookies (answer: 8)

**The Problem:** Players A and B play a game on 1997 copies of 1. A erases two numbers x,y; B writes x+y or |x-y|. Game ends when some condition is met. Find optimal number of cookies A gets.

| Metric | v22 | v23 | Change |
|--------|-----|-----|--------|
| Attempts | 8 | 16 | +8 |
| Answered | 3 | 9 | +6 |
| None | 5 | 7 | +2 |
| Correct votes | 0 | 5 (8) | +5 (from zero!) |
| Wrong votes | 3 (all 999) | 4 (all 999) | +1 |
| Vote margin | 0:3 (total loss) | 5:4 (narrow win) | flipped |
| Total tokens | 95.6K | 213.2K | +123% |
| Total errors | 4 | 14 | +250% |
| Wall time | 2.3m | 4.3m | +87% |
| Early stop | Yes(3) | Yes(5) | - |

**WHY DID IT FLIP?**

This is the most dramatic flip. In v22, ZERO attempts found the correct answer. All 3 answered attempts said 999, which is a reasoning trap (1997 copies of 1, and 999 "looks like" about half). In v23, 5 out of 9 answered attempts found 8 (the correct answer), beating the 4 that still said 999.

**What changed:**
1. **More attempts** gave more chances to find the correct approach
2. **Temperature diversity** was critical -- correct answers came from temps 0.3, 0.5, and even 0.9
3. **Code-verified game theory** -- the correct v23 attempts used actual game tree search with memoization to verify the answer

**Detailed analysis of correct v23 attempts:**

**Attempt 4 (temp=0.3, answer=8):** This is the breakthrough attempt. 9 turns, 8 code calls, 4.1min.
- Turn 1: Wrote a complete game tree solver using `lru_cache` memoization. Normalized states, computed A's optimal strategy (maximize cookies) vs B's adversarial strategy (minimize cookies). Ran for n=2 through n=8.
- Turns 2-4: Extended to n=2 through n=32, observing the pattern: answer = number of 1-bits in binary representation.
- Turn 5: Computed `bin(1997).count('1')` = 8. Pattern confirmed.
- Turns 6-8: Verified with theoretical analysis of parity invariants.
- Turn 9: Final reasoning to confirm answer = 8.

**Attempt 5 (temp=0.3, answer=8):** Similar approach with `lru_cache` game tree, but used `itertools.combinations` for move enumeration.

**Attempt 7 (temp=0.5, answer=8):** Used `Counter` for state tracking. 6 turns, more reasoning-heavy (37,794 chars reasoning in final turn).

**Attempt 9 (temp=0.5, answer=8):** Again `lru_cache` game tree search. 48,466 chars reasoning in turn 1 (massive initial analysis).

**Attempt 16 (temp=0.9, answer=8):** Even at the highest temperature, this approach works. Used `functools, itertools, math`.

**v22 wrong attempts analysis:**
- Attempt 4 (answer=999): Only 2 turns, 1 code call. The code call was just an import statement with no output. The model reasoned for 27,003 + 15,806 chars but never built a game tree solver. It relied on pure mathematical reasoning and got trapped in the "999" attractor.
- Attempt 5 (answer=999): 1 turn, 0 code calls, pure reasoning (14,321 chars). Never computed anything.
- Attempt 6 (answer=999): 6 turns, 5 code calls, but the code was apparently not a game tree solver.

**Root cause:** In v22, all attempts tried to solve this problem by mathematical reasoning alone, falling into the 999 trap. In v23, at least some attempts built actual game tree solvers that computed the answer from small cases, discovered the binary-popcount pattern, and extrapolated correctly to n=1997.

**The game tree solver is the key innovation.** The `normalize(state)` + `lru_cache` + minimax approach is what cracks this problem. v22 never discovered it; v23 found it in multiple attempts.

---

## Part 3: Cross-Cutting Analysis

### 1. Temperature Schedule Impact

| Temperature | Correct answers produced | Wrong answers | None |
|-------------|------------------------|---------------|------|
| 0.1 | 3 (269012, dd7f5e, b4ec47) | 1 | 3 |
| 0.3 | 14 | 7 | ~12 |
| 0.5 | 13 | 10 | ~15 |
| 0.7 | 6 | 6 | ~8 |
| 0.9 | 2 | 1 | ~4 |

**Low temperatures (0.1-0.3)** are most reliable for problems the model already knows how to solve.
**Mid temperatures (0.3-0.5)** are the sweet spot, producing the most correct answers while keeping errors manageable.
**High temperatures (0.7-0.9)** contribute critical diversity for hard problems (86e8e5, 76aef9) where the standard approach fails, but also produce more errors on already-solved problems.

### 2. None Rate Comparison

| Problem | v22 None% | v23 None% | Change |
|---------|-----------|-----------|--------|
| 269012 | 50% (4/8) | 69% (11/16) | worse |
| 2d282e | 50% (4/8) | 69% (11/16) | worse |
| 424e18 | 38% (3/8) | 69% (11/16) | worse |
| 8fea51 | 50% (4/8) | 44% (7/16) | better |
| b4ec47 | 38% (3/8) | 44% (7/16) | worse |
| dd7f5e | 38% (3/8) | 0% (0/16) | much better |
| 86e8e5 | 25% (2/8) | 13% (2/16) | better |
| 76aef9 | 63% (5/8) | 44% (7/16) | better |

**Pattern:** Reasoning-heavy problems (269012, 2d282e, 424e18) got worse None rates in v23. Problems requiring heavy code (8fea51, dd7f5e, 86e8e5, 76aef9) got better. This suggests the extraction improvements in v23 work better for code-based answers than reasoning-based ones.

### 3. Token Efficiency

| Problem | v22 tokens/correct vote | v23 tokens/correct vote |
|---------|------------------------|------------------------|
| 269012 | 51.7K | 48.8K | slightly better |
| 2d282e | 18.1K | 12.8K | much better |
| 424e18 | 25.9K | 33.3K | worse |
| 8fea51 | 27.0K | 27.6K | same |
| b4ec47 | 48.8K | 41.2K | better |
| dd7f5e | 42.2K | 55.0K | worse |
| 86e8e5 | 127.0K | 178.3K | worse |
| 76aef9 | N/A (0) | 42.6K | from impossible |

### 4. Error Scaling

| Problem | v22 errors | v23 errors | Ratio |
|---------|-----------|-----------|-------|
| 269012 | 4 | 4 | 1.0x |
| 2d282e | 0 | 1 | - |
| 424e18 | 11 | 15 | 1.4x |
| 8fea51 | 7 | 14 | 2.0x |
| b4ec47 | 13 | 43 | 3.3x |
| dd7f5e | 16 | 32 | 2.0x |
| 86e8e5 | 30 | 61 | 2.0x |
| 76aef9 | 4 | 14 | 3.5x |

Errors roughly scale with the 2x increase in attempts, except b4ec47 and 76aef9 which scale super-linearly (3.3x and 3.5x). These are problems where higher-temperature attempts produce more code execution errors.

### 5. Was 16 Attempts Worth It?

**For the stable-correct problems:** Marginally. Vote margins improved (most became unanimous), but at 2x token cost and significantly more errors. The problems were already being solved correctly.

**For the flipped problems:** Absolutely essential.
- 86e8e5 went from 2:2 tie (wrong) to 3:scattered (correct)
- 76aef9 went from 0:3 (completely wrong) to 5:4 (correct)

Without 16 attempts, neither flip would have occurred. The flipped problems represent +2 score (from potentially 6/8 to 8/8 on common problems).

### 6. The Diversity Hypothesis

The temperature schedule creates two beneficial effects:
1. **For hard problems:** Higher temps explore different solution strategies (e.g., game tree solver vs pure reasoning), increasing the chance of finding the right approach.
2. **For the voting mechanism:** Higher temps fragment wrong-answer clusters. In v22's 86e8e5, wrong answers coalesced on 23 (2 votes). In v23, wrong answers scattered across 11 different values, letting the correct answer win with just 3 votes.

This "fragmentation benefit" is a key insight: **temperature diversity helps not just by finding correct answers, but by preventing wrong answers from forming a consensus.**

---

## Recommendations for v24

1. **Keep 16 attempts** -- the 2 flipped problems justify the cost
2. **Consider adaptive early stop** -- stable problems like 2d282e solve in under 1 minute; spending 4+ minutes is wasteful
3. **Weight low-temperature votes higher** -- temps 0.1-0.3 are more reliable, so their votes could carry more weight
4. **Fix extraction on reasoning-heavy problems** -- the None rate increase for 269012, 2d282e, 424e18 suggests extraction regressed for some problem types
5. **Monitor error scaling** -- b4ec47's 3.3x error increase suggests diminishing returns on high-temp attempts for geometry problems
6. **The game tree solver pattern** -- 76aef9's breakthrough came from building actual game tree solvers. The prompt could potentially encourage this approach for game theory problems.
