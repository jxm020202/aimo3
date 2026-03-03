# Library x Topic Analysis — AIMO3 v23

Log: `output/v23/diagnostic.log`  
Problems: 97 | Attempts: 1552 | Score: 65/97

## Summary

This analysis covers:
1. **Library x Topic Matrix** — which libraries are used for which topics, success rates
2. **Unavailable Library Replacements** — pulp, ortools, z3, mip recovery analysis
3. **Optimal Library Recommendations** — data-driven recommendations per topic
4. **Anti-patterns** — library+function combos that always fail

## Part 1: Library x Topic Matrix

### Algebra

**352 attempts, base accuracy: 59%**

| Library | Uses | Correct | Wrong | None | Accuracy | None% |
|---------|------|---------|-------|------|----------|-------|
| sympy | 166 | 38 | 35 | 93 | 52% | 56% |
| random | 86 | 19 | 11 | 56 | 63% | 65% |
| itertools | 84 | 14 | 30 | 40 | 32% | 48% |
| math | 71 | 22 | 8 | 41 | 73% | 58% |
| numpy | 47 | 9 | 5 | 33 | 64% | 70% |
| fractions | 41 | 10 | 4 | 27 | 71% | 66% |
| Fraction | 39 | 10 | 4 | 25 | 71% | 64% |
| cmath | 22 | 1 | 11 | 10 | 8% | 45% |
| functools | 16 | 1 | 6 | 9 | 14% | 56% |
| lru_cache | 15 | 1 | 5 | 9 | 17% | 60% |
| collections | 14 | 2 | 5 | 7 | 29% | 50% |
| mpmath | 14 | 3 | 3 | 8 | 50% | 57% |
| product | 12 | 1 | 6 | 5 | 14% | 42% |
| combinations | 9 | 1 | 7 | 1 | 12% | 11% |
| defaultdict | 9 | 1 | 4 | 4 | 20% | 44% |

**Best libraries for algebra:** math (73%), fractions (71%), Fraction (71%)

**Worst libraries for algebra:** cmath (8%), combinations (12%), functools (14%)

### Combinatorics

**448 attempts, base accuracy: 39%**

| Library | Uses | Correct | Wrong | None | Accuracy | None% |
|---------|------|---------|-------|------|----------|-------|
| itertools | 312 | 55 | 86 | 171 | 39% | 55% |
| random | 130 | 23 | 31 | 76 | 43% | 58% |
| math | 122 | 24 | 24 | 74 | 50% | 61% |
| functools | 120 | 19 | 35 | 66 | 35% | 55% |
| lru_cache | 118 | 18 | 35 | 65 | 34% | 55% |
| pulp | 106 | 8 | 38 | 60 | 17% | 57% |
| sys | 98 | 9 | 33 | 56 | 21% | 57% |
| ortools | 88 | 7 | 32 | 49 | 18% | 56% |
| collections | 77 | 13 | 22 | 42 | 37% | 55% |
| importlib | 71 | 8 | 22 | 41 | 27% | 58% |
| combinations | 46 | 9 | 13 | 24 | 41% | 52% |
| time | 42 | 3 | 13 | 26 | 19% | 62% |
| pywraplp | 36 | 1 | 14 | 21 | 7% | 58% |
| fractions | 33 | 8 | 9 | 16 | 47% | 48% |
| Fraction | 31 | 8 | 8 | 15 | 50% | 48% |

**Best libraries for combinatorics:** heapq (100%), product (55%), math (50%)

**Worst libraries for combinatorics:** mip (0%), comb (0%), networkx (0%)

### Game Theory

**48 attempts, base accuracy: 56%**

| Library | Uses | Correct | Wrong | None | Accuracy | None% |
|---------|------|---------|-------|------|----------|-------|
| itertools | 33 | 10 | 4 | 19 | 71% | 58% |
| functools | 28 | 12 | 4 | 12 | 75% | 43% |
| lru_cache | 27 | 11 | 4 | 12 | 73% | 44% |
| combinations | 19 | 6 | 4 | 9 | 60% | 47% |
| math | 14 | 5 | 0 | 9 | 100% | 64% |
| collections | 11 | 4 | 3 | 4 | 57% | 36% |
| random | 10 | 2 | 1 | 7 | 67% | 70% |
| Counter | 9 | 2 | 3 | 4 | 40% | 44% |
| Fraction | 5 | 0 | 2 | 3 | 0% | 60% |
| fractions | 5 | 0 | 2 | 3 | 0% | 60% |
| heapq | 3 | 2 | 0 | 1 | 100% | 33% |
| sys | 2 | 1 | 0 | 1 | 100% | 50% |
| sympy | 2 | 0 | 0 | 2 | 0% | 100% |
| comb | 2 | 0 | 0 | 2 | 0% | 100% |

**Best libraries for game theory:** math (100%), functools (75%), lru_cache (73%)

**Worst libraries for game theory:** Counter (40%), collections (57%), combinations (60%)

### Geometry

**272 attempts, base accuracy: 53%**

| Library | Uses | Correct | Wrong | None | Accuracy | None% |
|---------|------|---------|-------|------|----------|-------|
| itertools | 108 | 26 | 19 | 63 | 58% | 58% |
| math | 90 | 19 | 7 | 64 | 73% | 71% |
| random | 85 | 19 | 9 | 57 | 68% | 67% |
| sympy | 66 | 18 | 6 | 42 | 75% | 64% |
| fractions | 19 | 7 | 0 | 12 | 100% | 63% |
| sys | 18 | 4 | 7 | 7 | 36% | 39% |
| pulp | 18 | 4 | 8 | 6 | 33% | 33% |
| Fraction | 15 | 5 | 0 | 10 | 100% | 67% |
| combinations | 15 | 2 | 3 | 10 | 40% | 67% |
| collections | 15 | 4 | 2 | 9 | 67% | 60% |
| importlib | 15 | 4 | 5 | 6 | 44% | 40% |
| functools | 14 | 5 | 7 | 2 | 42% | 14% |
| ortools | 13 | 3 | 8 | 2 | 27% | 15% |
| lru_cache | 13 | 4 | 7 | 2 | 36% | 15% |
| numpy | 12 | 2 | 3 | 7 | 40% | 58% |

**Best libraries for geometry:** fractions (100%), Fraction (100%), sympy (75%)

**Worst libraries for geometry:** mip (0%), cp_model (0%), ortools (27%)

### Number Theory

**208 attempts, base accuracy: 62%**

| Library | Uses | Correct | Wrong | None | Accuracy | None% |
|---------|------|---------|-------|------|----------|-------|
| sympy | 104 | 23 | 23 | 58 | 50% | 56% |
| math | 74 | 13 | 26 | 35 | 33% | 47% |
| random | 46 | 15 | 1 | 30 | 94% | 65% |
| fractions | 40 | 8 | 19 | 13 | 30% | 32% |
| Fraction | 39 | 8 | 19 | 12 | 30% | 31% |
| itertools | 25 | 3 | 8 | 14 | 27% | 56% |
| crt | 11 | 4 | 5 | 2 | 44% | 18% |
| collections | 9 | 1 | 6 | 2 | 14% | 22% |
| gcd | 9 | 0 | 7 | 2 | 0% | 22% |
| numpy | 8 | 1 | 0 | 7 | 100% | 88% |
| sys | 7 | 0 | 4 | 3 | 0% | 43% |
| factorial | 6 | 0 | 3 | 3 | 0% | 50% |
| factorint | 6 | 1 | 4 | 1 | 20% | 17% |
| combinations | 6 | 0 | 4 | 2 | 0% | 33% |
| time | 5 | 0 | 2 | 3 | 0% | 60% |

**Best libraries for number theory:** random (94%), sympy (50%), crt (44%)

**Worst libraries for number theory:** gcd (0%), sys (0%), factorial (0%)

### Optimization

**688 attempts, base accuracy: 50%**

| Library | Uses | Correct | Wrong | None | Accuracy | None% |
|---------|------|---------|-------|------|----------|-------|
| math | 245 | 54 | 53 | 138 | 50% | 56% |
| itertools | 236 | 34 | 71 | 131 | 32% | 56% |
| sympy | 203 | 44 | 42 | 117 | 51% | 58% |
| random | 165 | 30 | 33 | 102 | 48% | 62% |
| fractions | 103 | 25 | 31 | 47 | 45% | 46% |
| Fraction | 99 | 25 | 30 | 44 | 45% | 44% |
| sys | 88 | 6 | 31 | 51 | 16% | 58% |
| pulp | 86 | 6 | 29 | 51 | 17% | 59% |
| functools | 77 | 3 | 25 | 49 | 11% | 64% |
| lru_cache | 75 | 3 | 25 | 47 | 11% | 63% |
| ortools | 70 | 4 | 24 | 42 | 14% | 60% |
| importlib | 65 | 5 | 18 | 42 | 22% | 65% |
| collections | 60 | 7 | 25 | 28 | 22% | 47% |
| numpy | 52 | 9 | 7 | 36 | 56% | 69% |
| time | 37 | 3 | 11 | 23 | 21% | 62% |

**Best libraries for optimization:** mpmath (75%), numpy (56%), sympy (51%)

**Worst libraries for optimization:** pywraplp (0%), deque (0%), comb (0%)

### Other

**144 attempts, base accuracy: 51%**

| Library | Uses | Correct | Wrong | None | Accuracy | None% |
|---------|------|---------|-------|------|----------|-------|
| math | 48 | 8 | 10 | 30 | 44% | 62% |
| itertools | 32 | 10 | 0 | 22 | 100% | 69% |
| sympy | 22 | 3 | 5 | 14 | 38% | 64% |
| fractions | 13 | 4 | 0 | 9 | 100% | 69% |
| Fraction | 10 | 3 | 0 | 7 | 100% | 70% |
| collections | 6 | 1 | 0 | 5 | 100% | 83% |
| functools | 5 | 0 | 0 | 5 | 0% | 100% |
| product | 4 | 0 | 0 | 4 | 0% | 100% |
| lru_cache | 4 | 0 | 0 | 4 | 0% | 100% |
| numpy | 3 | 1 | 0 | 2 | 100% | 67% |
| Counter | 3 | 1 | 0 | 2 | 100% | 67% |
| random | 3 | 2 | 0 | 1 | 100% | 33% |
| deque | 2 | 0 | 0 | 2 | 0% | 100% |
| sys | 2 | 1 | 0 | 1 | 100% | 50% |

**Best libraries for other:** itertools (100%), fractions (100%), Fraction (100%)

**Worst libraries for other:** sympy (38%), math (44%), itertools (100%)

### Probability

**160 attempts, base accuracy: 46%**

| Library | Uses | Correct | Wrong | None | Accuracy | None% |
|---------|------|---------|-------|------|----------|-------|
| itertools | 66 | 15 | 20 | 31 | 43% | 47% |
| collections | 48 | 6 | 16 | 26 | 27% | 54% |
| random | 43 | 12 | 1 | 30 | 92% | 70% |
| deque | 30 | 1 | 10 | 19 | 9% | 63% |
| functools | 28 | 10 | 5 | 13 | 67% | 46% |
| lru_cache | 27 | 9 | 5 | 13 | 64% | 48% |
| Counter | 26 | 5 | 9 | 12 | 36% | 46% |
| fractions | 25 | 5 | 9 | 11 | 36% | 44% |
| Fraction | 24 | 5 | 8 | 11 | 38% | 46% |
| math | 23 | 6 | 3 | 14 | 67% | 61% |
| combinations | 18 | 7 | 4 | 7 | 64% | 39% |
| sympy | 12 | 2 | 4 | 6 | 33% | 50% |
| product | 11 | 3 | 5 | 3 | 38% | 27% |
| numpy | 10 | 0 | 0 | 10 | 0% | 100% |
| sys | 4 | 2 | 1 | 1 | 67% | 25% |

**Best libraries for probability:** random (92%), functools (67%), math (67%)

**Worst libraries for probability:** deque (9%), collections (27%), sympy (33%)

## Part 2: Unavailable Library Replacements

### `pulp` — Linear programming / Integer LP solver

- **Import attempts:** 115
- **Import errors:** 75
- **Problems affected:** 11
- **Successful recoveries:** 24
- **Outcomes:** correct=10, wrong=38, none=65
- **Topics:** combinatorics(106), optimization(86), geometry(18), probability(1)
- **Alternatives:** scipy.optimize.linprog (for LP), itertools + brute force (for small ILP), sympy (for constraint solving), manual branch-and-bound

### `ortools` — Google OR-Tools: constraint programming, SAT, LP

- **Import attempts:** 92
- **Import errors:** 54
- **Problems affected:** 9
- **Successful recoveries:** 15
- **Outcomes:** correct=7, wrong=32, none=51
- **Topics:** combinatorics(88), optimization(70), geometry(13)
- **Alternatives:** itertools (constraint enumeration), backtracking search (manual), scipy.optimize.linprog (for LP), sympy (for symbolic constraints)

### `z3` — Z3 SMT solver: satisfiability, constraint solving

- **Import attempts:** 16
- **Import errors:** 10
- **Problems affected:** 5
- **Successful recoveries:** 4
- **Outcomes:** correct=2, wrong=6, none=8
- **Topics:** combinatorics(16), optimization(12), geometry(3)
- **Alternatives:** sympy.solve (for algebraic constraints), itertools + brute force (for small domains), backtracking (manual)

### `mip` — Python-MIP: Mixed Integer Programming

- **Import attempts:** 14
- **Import errors:** 8
- **Problems affected:** 5
- **Successful recoveries:** 3
- **Outcomes:** correct=0, wrong=6, none=7
- **Topics:** combinatorics(13), optimization(7), geometry(4)
- **Alternatives:** scipy.optimize.linprog (for LP relaxation), itertools (for small search spaces), manual branch-and-bound

## Part 3: Optimal Library Recommendations

Based on the data, here are the recommended library mappings per topic:

| Topic | Recommended Libraries & Functions |
|-------|-----------------------------------|
| Number Theory | sympy (factorint, isprime, divisors, totient, mod_inverse), math (gcd, isqrt), itertools |
| Combinatorics | itertools (product, combinations, permutations), math (comb, factorial), functools (lru_cache for DP/memoization) |
| Geometry | math (sqrt, cos, sin, atan2, pi), sympy (solve, Rational, sqrt, simplify, nsimplify), numpy (array, linalg) |
| Algebra | sympy (symbols, solve, expand, factor, simplify, Eq, Poly, roots, diff, integrate), fractions (Fraction) |
| Optimization | itertools (brute force for small ILP), scipy.optimize.linprog (for LP), functools (lru_cache for DP) |
| Probability | fractions (Fraction for exact arithmetic), sympy (Rational, binomial), math (comb, factorial), random (Monte Carlo verification) |
| Game Theory | functools (lru_cache for game tree memo), itertools (move enumeration) |

### Key Replacements for Unavailable Libraries

| Unavailable | Trying to do | Use Instead |
|-------------|-------------|-------------|
| pulp | Linear Programming | scipy.optimize.linprog |
| ortools (linear_solver) | LP/MIP | scipy.optimize.linprog + itertools |
| ortools (cp_model) | Constraint Programming | itertools + backtracking |
| z3 | SMT/SAT solving | sympy.solve + itertools enumeration |
| mip | Mixed Integer Programming | scipy.optimize.linprog + itertools |

## Part 4: Anti-patterns

### 0% Accuracy Functions (never produce correct answer, min 3 non-None uses)

| Function | Wrong | None | Total |
|----------|-------|------|-------|
| sympy.factorial | 6 | 5 | 11 |
| math.lcm | 6 | 5 | 11 |
| queue.popleft | 6 | 13 | 19 |
| dq.append | 6 | 3 | 9 |
| dq.popleft | 6 | 3 | 9 |
| chosen.pop | 5 | 6 | 11 |
| segs.append | 5 | 7 | 12 |
| sympy.mod_inverse | 4 | 2 | 6 |
| sys.set_int_max_str_digits | 4 | 3 | 7 |
| new_divs.append | 4 | 0 | 4 |
| options.append | 4 | 2 | 6 |
| sympy.prod | 4 | 1 | 5 |
| cell_to_segs.items | 4 | 2 | 6 |
| grid.copy | 4 | 5 | 9 |
| factors.items | 3 | 0 | 3 |
| S.denominator | 3 | 1 | 4 |
| ratios.append | 3 | 1 | 4 |
| residues.append | 3 | 0 | 3 |
| moduli.append | 3 | 0 | 3 |
| poly.expand | 3 | 0 | 3 |
| points.append | 3 | 14 | 17 |
| deg.append | 3 | 0 | 3 |
| lsb.bit_length | 3 | 10 | 13 |
| selected.remove | 3 | 7 | 10 |
| degs.sort | 3 | 0 | 3 |
| cell_to_segs.values | 3 | 3 | 6 |
| assign.copy | 3 | 4 | 7 |
| adj.items | 3 | 1 | 4 |
| rows.items | 3 | 5 | 8 |
| cols.items | 3 | 4 | 7 |
| placement_masks.append | 3 | 2 | 5 |
| new_required.add | 3 | 1 | 4 |

Total: 32 functions with 0% accuracy

### Import Count vs Success Rate

| Imports | Total | Correct | Wrong | None | Accuracy | None% |
|---------|-------|---------|-------|------|----------|-------|
| 0-1 | 571 | 146 | 59 | 366 | 71% | 64% |
| 2-3 | 434 | 90 | 73 | 271 | 55% | 62% |
| 4-5 | 178 | 45 | 46 | 87 | 49% | 49% |
| 6-7 | 84 | 14 | 28 | 42 | 33% | 50% |
| 8+ | 85 | 6 | 31 | 48 | 16% | 56% |

### Unavailable Library Cascades

Total attempts trying 2+ unavailable libraries: 86

Examples:
- `21fb4e att=1: pulp -> ortools`
- `21fb4e att=4: pulp -> z3 -> ortools`
- `21fb4e att=5: pulp -> ortools`
- `21fb4e att=6: pulp -> ortools`
- `21fb4e att=7: pulp -> ortools`
- `21fb4e att=9: pulp -> ortools`
- `21fb4e att=10: pulp -> z3 -> ortools`
- `21fb4e att=11: pulp -> ortools`
- `21fb4e att=12: pulp -> ortools`
- `21fb4e att=13: pulp -> ortools`

## Key Takeaways

1. **pulp/ortools/z3/mip are never available** — the model wastes turns trying them, then cascading through alternatives. Add a prompt hint: "The following libraries are NOT available: pulp, ortools, z3, mip, cvxpy. Use scipy.optimize.linprog for LP, itertools for constraint enumeration."

2. **Import count correlates with failure** — attempts importing 6+ libraries have much lower accuracy. The model is searching rather than solving.

3. **sympy is beneficial overall** (55% vs 52% baseline) but has a high None rate (59%). The model often gets stuck in symbolic computation.

4. **deque, cmath, sys, functools** are anti-pattern indicators — they correlate with complex but failing code patterns.

5. **mpmath, decimal, heapq** are rare but highly effective when used correctly.

6. **Board/grid optimization problems** are the main trigger for unavailable libraries. These problems need explicit guidance toward itertools-based enumeration or scipy LP.

