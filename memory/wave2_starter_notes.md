# Wave 2 Starter Notes — Strategic Hints by Topic

> **Purpose**: When a problem fails in Wave 1 (16 attempts), inject the relevant topic section into Wave 2's system prompt to guide 16 fresh attempts with different strategies.
>
> **How to use**: A classifier (the 1-runner) identifies the topic, then loads ONLY the matching section below. Keep injection short — the model has limited context.

---

## Topic Index

| Topic ID | Section | Typical Keywords in Problem |
|----------|---------|---------------------------|
| `combinatorics` | [Combinatorics / Discrete](#combinatorics) | board, grid, game, player, dice, domino, tile, coin, maze, graph, vertex, edges, color, path, placement |
| `geometry` | [Geometry / Spatial](#geometry) | polygon, circle, angle, observer, lattice, convex, diagonal, chessboard, triangle, bisector |
| `number_theory` | [Number Theory](#number-theory) | divisor, prime, modulo, roots of unity, complex numbers, Norwegian, product, gcd |
| `algebra` | [Algebra / Optimization](#algebra) | function, maximize, inequality, recurrence, polynomial, sequence, grid-fill, sum |
| `off_by_one` | [Off-by-One / Boundary](#off-by-one) | (detected by Wave 1 classifier if answers cluster near expected) |

---

## Combinatorics

### Common Failure Patterns (from 6 failing problems across 2 runs)

**Pattern 1: Pure reasoning without verification (CRITICAL)**
- Problems like maze/game theory get solved in 1 turn with long reasoning — model writes 15k+ chars of pure logic, arrives at wrong answer, never runs code to check
- The WRONG answer is typically an obvious structural number (e.g., answering "3032" for a 3032-column maze when the real answer is 3)
- Fix: ALWAYS write code to verify on small cases before committing to an answer
- Example: 673b29 (maze) — 15/16 attempts pure-reasoned to 3032, the 1 correct attempt also pure-reasoned but explored the problem more deeply (54k chars vs 3-5k chars)

**Pattern 2: Misunderstanding the problem constraint**
- Model frequently misinterprets what "optimal strategy" means in game/strategy problems
- Example: 414a5b (dice re-throw) — model computes overall optimal probability (95/216) when problem asks specifically for the n=2 case (42/216)
- Fix: Re-read the problem statement twice. Identify EXACTLY what quantity is asked for. If the problem says "when n=2", compute only that case, not the overall optimum

**Pattern 3: Brute force on NP-hard board problems**
- Problems like "minimum dominos on 7x7 board" (dbbfe8) or "minimum marked squares on 13x13 board" (a824c1) are combinatorial optimization
- Model tries ILP solvers (pulp, ortools — unavailable!), then falls back to heuristic search that finds locally optimal but globally wrong solutions
- For dbbfe8: wrong answer 8 (found small config, but real min is 22 — needs dominos to block EACH OTHER)
- For a824c1: wrong answer 13 (thinks one per diagonal suffices, but bishops threaten BOTH diagonals)
- Fix: Prove a LOWER BOUND first, then find a matching construction. Never trust a computer search that says "found k" without proving k is minimal

**Pattern 4: Off-by-one in coin/walk problems**
- a9dbc8 (coin flipping walk): model consistently gets 15743 instead of 15744
- Boundary condition error — miscounting whether the first/last move is included
- Fix: Test formula on small cases (n=3, n=5, n=7) before extrapolating to n=7873

### Strategy Guidance for Wave 2

```
WAVE 2 COMBINATORICS INSTRUCTIONS:
1. Before solving, classify: is this (a) counting, (b) optimization/extremal, (c) game/strategy, (d) constructive?
2. For optimization: PROVE a lower/upper bound FIRST, then construct a matching example
3. For game/strategy: Simulate small cases (n=3,4,5) with code. The answer is often logarithmic (log2 or log3), not linear
4. For counting: Write code to enumerate small cases, look for patterns/recurrences
5. ALWAYS verify with code on small instances before giving final answer
6. Re-read the problem: what EXACTLY is being asked? Not the overall optimum, but a specific parameter value?
7. Available libraries: itertools, functools, collections, numpy, scipy. NO pulp, ortools, z3, mip
```

---

## Geometry

### Common Failure Patterns (from 4 failing problems across 2 runs)

**Pattern 1: Wrong constructibility condition (23586c)**
- Model concludes centroid is constructible iff m is divisible by 105 (factors of 735), giving 773 multiples
- Real answer is 386 — the condition is more nuanced than just "prime factors of 735 divide m"
- The model skips the case where m-section combined with affine operations has richer constructibility
- Fix: Don't jump to "m divides 735" — consider what AFFINE COMBINATIONS are constructible with m-section and which denominators can be built

**Pattern 2: Trivial bound claimed without verification (1ec970)**
- 100 observers with 100-degree viewing angles: model claims all pairs can see each other (9900) by clustering
- But the problem likely asks for a WORST-CASE or constrained configuration (positions may be fixed, or observers face fixed directions)
- Fix: Read problem constraints extremely carefully. "Each observer has a viewing angle" may mean FIXED direction, not choosable. Check if the answer 9900 = 100*99 seems too easy for a competition problem

**Pattern 3: Grid geometry — wrong extremal bound (26bee3)**
- 16x16 grid with directed diagonals: model gets various wrong answers (97, 136, 256) instead of 108
- Problem involves directed graph structure on grid — the answer relates to graph theory on grid diagonals
- Fix: Model the problem as a graph/matching problem. Draw small cases (4x4, 8x8). The answer often factors nicely (108 = 4*27 or 12*9)

**Pattern 4: Lattice point selection with trapezoid avoidance (ae2add)**
- Expected 24931 = 2.5*9973 - 2 (approx), model gets 19945 = 2*9973 - 1
- Model misses that the forbidden pattern (isosceles trapezoid) allows more points than it thinks
- Wrong approach: treating horizontal and vertical constraints independently
- Fix: The answer likely involves 2.5*n + small_correction, not 2*n. Check construction where each row has ~2.5 points on average

### Strategy Guidance for Wave 2

```
WAVE 2 GEOMETRY INSTRUCTIONS:
1. If the answer seems "too easy" (like n*(n-1)), it's probably WRONG. Competition geometry problems have non-trivial answers
2. For constructibility problems: be precise about what operations are available. m-section gives denominators that are powers of m's prime factors, but COMBINED operations may give more
3. For extremal geometry (min/max on grids): draw small cases first, then find the EXACT bound with proof
4. For lattice point problems: the answer often involves ceil/floor of n*ratio. Test constructions on small grids
5. Watch for "viewing angle" problems: distinguish between "observer chooses direction" vs "direction is fixed"
6. ALWAYS verify: if your answer is a simple formula like n*(n-1), you're probably oversimplifying
```

---

## Number Theory

### Common Failure Patterns (from 2 failing problems across 2 runs)

**Pattern 1: Roots of unity / complex number products (3980cd)**
- Problem: max m such that product of (r_k^e + 1) = 1 for e=1..m, with 645 complex numbers
- Model gets 642 (= 645-3) or 516 consistently — wrong structural guess
- Real answer: 46 (mod 848). This requires deep number theory about cyclotomic polynomials
- The few correct attempts used heavy symbolic computation + number-theoretic reasoning
- Fix: This is NOT a simple "count prime factors" problem. Think cyclotomic: what order roots of unity make (r^e + 1) have product 1?

**Pattern 2: Brute force on large number theory (86e8e5)**
- n-Norwegian numbers (three divisors summing to n): model tries to brute-force enumerate but the answer (8687) requires computing over huge ranges
- Attempts get wildly different wrong answers (40958, 17794, 71, etc.) — no consensus
- Only 1-3 out of 32 attempts across both runs get it right, always via extended computation (119 turns!)
- Fix: The correct approach uses number-theoretic properties of divisor sums. Think about what makes a number n-Norwegian: it needs divisors d1 < d2 < d3 with d1+d2+d3 = n. Smallest such number relates to factoring properties

### Strategy Guidance for Wave 2

```
WAVE 2 NUMBER THEORY INSTRUCTIONS:
1. For "product equals 1" problems with complex numbers: think ROOTS OF UNITY. The key is cyclotomic polynomial theory
2. For divisor-sum problems: don't brute-force. Characterize the structure: which numbers have divisor triples summing to n?
3. For large modular arithmetic: use Chinese Remainder Theorem, Euler's theorem, multiplicative functions
4. If brute force gives different answers each attempt → the search space is too large. Find the mathematical structure first
5. sympy.ntheory has divisor_sigma, factorint, primitive_root — use them
6. Verify on small cases (n=6,7,8...) before extrapolating to large n
```

---

## Algebra

### Common Failure Patterns (from 3 failing problems across 2 runs)

**Pattern 1: Numerical optimization gives wrong analytical formula (3b88b3)**
- CRITICAL: ALL 32 attempts across both runs get 982, expected 979
- Model derives f(k) = k^2/sqrt(k^2-1) analytically, which gives S = 982 exactly
- This formula satisfies numerical Monte Carlo verification — but it's STILL WRONG
- The error is in the optimization: model finds a critical point that is NOT the global maximum
- The Lagrange multiplier / KKT conditions may have been applied incorrectly, or a boundary case was missed
- Fix: Do NOT trust a clean analytical formula just because Monte Carlo confirms it. Check ALL boundary cases: z=0, x=0, y=0, and all KKT conditions. The true max may occur at a different critical point

**Pattern 2: Functional equation misinterpretation (29714f)**
- g: N x N -> N with g(0,0)=0 and recursive structure
- Model gets 99 (expected 297 = 3*99) — consistent factor-of-3 error
- Likely misinterprets the domain or counts only one-third of the function values
- Fix: Carefully enumerate g(x,y) for small x,y. Check if the recurrence generates a 3-fold symmetric structure

**Pattern 3: Grid optimization wrong approach (aff75c)**
- 60x60 grid filling with 1..3600, maximize minimum adjacent sum S
- Model gets various wrong answers (3600, 3658, 3601, 3165) — timeout-dominated
- The problem requires clever arrangement theory, not computational search
- Fix: Think checkerboard-style: alternate high and low values. The answer 3571 suggests S = 3600 - 29. Find the theoretical bound via averaging argument

### Strategy Guidance for Wave 2

```
WAVE 2 ALGEBRA INSTRUCTIONS:
1. For constrained optimization with floor(): check ALL critical points AND boundary cases. A clean formula is suspicious if it gives an integer — competition problems often have floor() that matters
2. For functional equations: enumerate f(0,0), f(0,1), f(1,0), f(1,1), ... up to f(5,5) with code. Find the pattern EMPIRICALLY before attempting theory
3. For grid arrangement problems: think about averaging and parity. The optimal S is usually total_sum/num_adjacencies ± correction
4. If your answer differs by a small factor (2x, 3x) from attempts: you likely have a COUNTING ERROR in the domain. Re-examine boundaries
5. Use sympy for symbolic optimization. VERIFY with scipy.optimize on grid search. If they disagree, there are multiple critical points — find ALL of them
6. Monte Carlo verification is NECESSARY but NOT SUFFICIENT — it can confirm a local max that isn't global
```

---

## Off-by-One

### Detection Rule

If Wave 1 attempts cluster tightly around expected answer (within +/- 3), this section applies.

### Common Patterns

**Pattern 1: Boundary inclusion/exclusion**
- a9dbc8: 15743 vs 15744 — model miscounts whether first/last step is included in walk length
- Fix: Test on n=3, n=5, n=7 explicitly, compare formula to hand computation

**Pattern 2: Floor vs. ceil vs. round**
- 3b88b3: 982 vs 979 — model gets exact integer from wrong formula; floor() doesn't help because formula itself is wrong
- Fix: If optimization gives a clean integer, be suspicious. The true function value is likely irrational, and floor() takes it to something else

**Pattern 3: Off-by-factor**
- 23586c: 773 vs 386 (factor of ~2) — the constructibility condition is stricter than the model thinks
- 29714f: 99 vs 297 (factor of 3) — counting error in the function domain
- Fix: If answer is exactly 2x or 3x the expected, re-examine the problem for double/triple counting or domain errors

### Strategy Guidance for Wave 2

```
WAVE 2 OFF-BY-ONE INSTRUCTIONS:
1. Compute answer for smallest non-trivial case by HAND (or exhaustive code)
2. Compare hand computation with formula. If they disagree on n=3 or n=5, the formula is wrong
3. Check: does the problem count 0-indexed or 1-indexed? Include or exclude endpoints?
4. For walk/path problems: is the answer #steps or #positions visited?
5. For grid problems: is it n or n-1 intervals?
```

---

## Cross-Topic Anti-Patterns

These mistakes appear across ALL topics and should always be warned against:

1. **"Obvious" answers that are too simple**: If answer = n*(n-1) or similar clean formula for an olympiad problem, it's almost certainly wrong. Olympiad answers require deeper analysis.

2. **Unavailable libraries**: pulp, ortools, z3, mip are NOT available in Kaggle runtime. Never attempt to import them. Use scipy.optimize.milp for ILP if needed.

3. **Trusting Monte Carlo alone**: Numerical simulation can confirm a local optimum. It CANNOT distinguish local from global optimum. Always seek analytical confirmation.

4. **Pure reasoning marathons**: If 15/16 attempts write 5-15k chars of reasoning without code and all get the same wrong answer, the reasoning has a systematic flaw. Use code to check small cases FIRST.

5. **Timeout spiral**: If brute force times out, do NOT retry with slightly optimized brute force. Switch to mathematical analysis — closed form, recurrence, or generating function.

6. **Problem misreading**: Re-read the problem statement. Check: what exactly is being maximized/minimized? What are the constraints? Is there a specific parameter value asked for?

---

## Classifier Prompt (for the 1-runner)

```
Given the problem text below, classify it into exactly ONE of these categories:
- combinatorics: boards, games, counting, graphs, paths, tiling, coloring, dice, coins, mazes
- geometry: polygons, circles, angles, lattice points, constructibility, observers, diagonals
- number_theory: divisors, primes, modular arithmetic, roots of unity, products over complex numbers
- algebra: optimization, inequalities, functional equations, sequences, grid arrangements
- unknown: cannot classify

Also check: did Wave 1 answers cluster within +/-3 of each other? If yes, add tag: off_by_one

Return: {"topic": "<topic>", "off_by_one": true/false}
```

---

## Problem-Specific Notes (for known hard problems)

These are notes for problems we KNOW will fail. If a problem ID matches, inject these specific hints.

**NEVER CORRECT** = 0 correct attempts across all runs. These need fundamentally different approaches.
**OUTVOTED** = correct answer appeared but lost the vote. More attempts, better voting, or starter hints may flip these.

| PID | Answer | Status | Hint |
|-----|--------|--------|------|
| `dbbfe8` | 22 | OUTVOTED (7/48) | Dominos must block EACH OTHER, not just touch walls. Answer is 22, not 8. Prove lower bound via counting |
| `a824c1` | 24 | NEVER (0/48) | Bishop covers BOTH diagonals. Need to hit all 49 diag lines. Answer is 24, not 13 |
| `673b29` | 3 | OUTVOTED (1/48) | Maze answer is 3 (logarithmic!), not 3032 (linear). Use binary-search strategy on columns |
| `23586c` | 386 | NEVER (0/48) | Not just 105-divisibility. Constructibility needs deeper analysis. Answer is 386, not 773 |
| `3b88b3` | 979 | NEVER (0/48) | f(k)=k^2/sqrt(k^2-1) is WRONG. Check ALL boundary cases. True floor(S)=979, not 982 |
| `414a5b` | 42 | OUTVOTED (7/48) | Asks for 216*p when n=2 SPECIFICALLY, not overall optimal. Answer 42, not 95 |
| `a9dbc8` | 15744 | OUTVOTED (1/48) | Off-by-1 in walk/flip count. Answer 15744, not 15743. Test on n=3,5 |
| `9010d9` | 10320 | OUTVOTED (2/48) | Graph theory: max edges with "each vertex has a private neighbor". Not n^2/4=6400. Answer 10320 |
| `3980cd` | 46 | OUTVOTED (6/48) | Roots of unity / cyclotomic. Answer 46 mod 848, not 642. Deep NT needed |
| `86e8e5` | 8687 | OUTVOTED (6/80) | Norwegian numbers: long computation needed (100+ turns). Don't settle for early wrong answer |
| `1ec970` | 8700 | NEVER (0/48) | Observers with viewing angles. Answer is 8700, NOT 9900=100*99. Constraint is non-trivial |
| `ae2add` | 24931 | OUTVOTED (1/48) | Lattice points avoiding iso. trapezoids. Answer ~2.5*9973, not 2*9973. Construction allows more |
| `aff75c` | 3571 | OUTVOTED (3/48) | Grid fill: max min-adjacent-sum. Answer 3571, not 3600. Needs averaging/parity argument |
| `29714f` | 297 | OUTVOTED (3/48) | Functional equation: answer 297=3*99. Model gets 99 (factor-of-3 counting error) |
| `26bee3` | 108 | OUTVOTED (1/48) | Directed diagonals in 16x16 grid. Answer 108, not 97 or 256 |
