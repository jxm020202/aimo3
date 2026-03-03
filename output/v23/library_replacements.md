# Library Replacement Analysis: v23 Deep Dive

## Executive Summary

The model wastes **201 code execution turns** across v23 attempting to import unavailable libraries
(pulp, ortools, z3, mip). Worse, it often doesn't know that `scipy.optimize.linprog` and
`scipy.optimize.milp` ARE available -- repeatedly saying "scipy.optimize.linprog not available"
in reasoning even though it works perfectly when actually tried.

The 6 problems most affected by missing ILP solvers (21fb4e, dbbfe8, a824c1, c19295, aff75c,
26bee3) have a combined correct rate of **~10%** across 96 attempts -- the worst-performing
problems in the entire run.

---

## Library-by-Library Analysis

### 1. pulp (115 import attempts, 75 errors, 11 problems)

**What the model is trying to do:**

| Use Case | Specific pulp API | Example Problem | Math Context |
|----------|-------------------|-----------------|--------------|
| Binary Integer Programming | `LpProblem`, `LpVariable(cat='Binary')`, `LpMinimize` | a824c1 | Minimum covering set on chessboard diagonals (bishop cover) |
| Set Cover / Hitting Set | `LpProblem`, `lpSum`, `PULP_CBC_CMD` | 21fb4e | Minimum stones to cover all 5-in-a-row lines on 9x9 grid |
| Maximum Independent Set (as ILP) | `LpMaximize`, binary variables + constraints | c19295 | Maximum induced matching on 15x15 grid |
| Grid Placement (ILP) | `LpVariable.dicts`, `LpBinary`, row/col constraints | ba89f9 | Number placement with ratio constraints |
| Maximum Points (ILP) | `LpMaximize`, `LpVariable(cat='Binary')` | ae2add | Maximum subset of grid points with row-pair constraints |
| Domino Tiling (ILP) | Binary placement variables + adjacency | dbbfe8 | Minimum domino tiling with neighbor constraints on 7x7 |

**Specific pulp functions attempted:**
- `pulp.LpProblem('name', pulp.LpMinimize)` or `pulp.LpMaximize`
- `pulp.LpVariable('name', lowBound=0, upBound=1, cat='Binary')`
- `pulp.LpVariable.dicts('prefix', indices, ...)`
- `pulp.lpSum([...])`
- `prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=30))`
- `pulp.LpStatus[prob.status]`
- `pulp.value(prob.objective)`

**Recovery patterns:**
- Model falls back to brute-force backtracking with pruning (branch-and-bound)
- Greedy heuristics (coverage-based)
- Manual DFS with iterative deepening
- **Recovery success: POOR.** Backtracking on NP-hard problems usually times out (30s limit per cell).
  On 21fb4e (hitting set), only 2/16 attempts succeed. On a824c1 (covering set), 0/16 succeed.

**What it SHOULD use:**
- `scipy.optimize.milp` -- MILP solver available since scipy 1.9 (Kaggle has scipy). The model
  NEVER tries this. In reasoning, it says "scipy.optimize.linprog? Not integer" -- it doesn't
  know scipy has MILP support.
- `scipy.optimize.linprog` -- for LP relaxations (actually available, model wrongly thinks unavailable
  in most attempts for problem 0c55f3; some attempts discover it works)
- For small problems: `itertools.combinations` with pruning, bitmask DP

---

### 2. ortools (92 import attempts, 54 errors, 9 problems)

**What the model is trying to do:**

| Use Case | Specific ortools API | Count | Math Context |
|----------|---------------------|-------|--------------|
| CP-SAT constraint solver | `from ortools.sat.python import cp_model` | ~22 | Grid placement, tiling, constraint satisfaction |
| Linear/Integer solver | `from ortools.linear_solver import pywraplp` | ~109 | Same ILP problems as pulp |

**CP-SAT specific usage patterns:**
- `model = cp_model.CpModel()`
- `model.Add(constraint)` for integer constraints
- `solver = cp_model.CpSolver()`
- `solver.parameters.max_time_in_seconds = 30.0`
- `result == cp_model.OPTIMAL`

**Linear solver specific patterns:**
- `pywraplp.Solver.CreateSolver('SCIP')` or `('CBC')`
- Used as fallback after pulp fails

**Overlap with pulp:** 100% overlap. Same 9 problems that try ortools also try pulp.
The model follows a strict cascade: pulp -> ortools -> z3 -> mip -> manual fallback.

**Recovery patterns:**
- Same as pulp -- falls back to brute force / backtracking
- Recovery success: Same poor rate

**What it SHOULD use:**
- `scipy.optimize.milp` for ILP problems (covers ~80% of ortools.linear_solver use cases)
- For CP-SAT constraint satisfaction: manual backtracking with constraint propagation,
  or encode as ILP via scipy.optimize.milp
- `networkx` IS available and has graph algorithms (max matching, coloring heuristics)

---

### 3. z3 (16 import attempts, 10 errors, 5 problems)

**What the model is trying to do:**

Z3 is used EXCLUSIVELY as a last-resort fallback after pulp AND ortools fail. The model
never reaches z3 as a first choice.

| Use Case | Context | Problem |
|----------|---------|---------|
| Integer constraint satisfaction | After ILP solvers fail, tries SMT solver | 21fb4e, dbbfe8 |
| Grid placement constraints | Same placement problems | c19295 |
| Boolean satisfiability | Set cover / hitting set | a824c1 |
| Feasibility checking | Check if constraint system has solution | 26bee3 |

The model's z3 reasoning pattern is always:
> "Could use z3 solver? Not available." (mentions this 69 times in reasoning)

**What it SHOULD use:**
- `scipy.optimize.milp` with binary constraints (covers most z3 use cases in this context)
- Manual backtracking with pruning for constraint satisfaction
- `sympy.solvers` for small symbolic constraint systems

---

### 4. mip / python-mip (14 import attempts, 8 errors, 5 problems)

**What the model is trying to do:**

Same ILP problems as pulp. mip is tried as the 4th fallback after pulp, ortools, z3 all fail.

**Specific mip API attempted:**
- `from mip import Model, xsum, BINARY, MINIMIZE, OptimizationStatus`
- `Model(sense=MINIMIZE)`
- `model.add_var(var_type=BINARY)`
- `model += xsum(...)` (constraints)
- `model.optimize()`

**Recovery:** Same brute-force fallbacks.

**What it SHOULD use:**
- `scipy.optimize.milp` -- literally the same thing, already installed

---

## Wasted Turn Analysis

### Turn Budget Impact

| Library | Error Turns | Probe Turns (try/except) | Total Wasted |
|---------|-------------|-------------------------|--------------|
| pulp | 75 | ~25 | ~100 |
| ortools | 54 | ~20 | ~74 |
| z3 | 10 | ~6 | ~16 |
| mip | 8 | ~3 | ~11 |
| **Total** | **147** | **54** | **201** |

### Sequential Probe Cascade Pattern

70 attempts have multi-library probe sequences. Typical pattern wastes 3-6 turns:
```
Turn N:   import pulp          -> ModuleNotFoundError (1 wasted turn)
Turn N+1: from ortools import  -> ModuleNotFoundError (1 wasted turn)
Turn N+2: import z3            -> ModuleNotFoundError (1 wasted turn)
Turn N+3: import mip           -> ModuleNotFoundError (1 wasted turn)
Turn N+4: (finally starts manual approach)
```

Worst case: c19295 attempt 1 -- **85 total turns, 26 errors**, wastes first 6 turns on
library probes before any actual problem-solving.

### Token Waste Estimate

Each failed import costs:
- ~50 tokens for the import code
- ~100 tokens for the error traceback
- ~200 tokens for "let me try another library" reasoning
- Total: ~350 tokens per failure

At 201 wasted turns: **~70,000 tokens wasted** on unavailable library imports.
That's equivalent to ~1 full problem-solving attempt.

---

## The scipy.optimize.milp Discovery

**Critical finding:** The model mentions `scipy.optimize.linprog` 96 times in reasoning across
6 problems, almost always saying "not available" -- but it IS available. When attempts 6 and 14
of problem 0c55f3 actually import it, it works perfectly.

**Even worse:** The model NEVER once mentions or tries `scipy.optimize.milp`, which is the
integer programming solver that would replace pulp/ortools/mip. It was added in scipy 1.9.0
(2022) and uses the HiGHS solver. It supports:
- Binary variables (integrality constraints)
- Linear objective
- Linear inequality/equality constraints
- Bounds

This is exactly what the model needs for 80%+ of its pulp/ortools use cases.

### scipy.optimize.milp API (what the prompt should teach):

```python
from scipy.optimize import milp, LinearConstraint, Bounds

# Example: minimize c^T x subject to A_ub x <= b_ub, x binary
result = milp(
    c=objective_coefficients,           # minimize c^T x
    constraints=LinearConstraint(A, lb, ub),  # lb <= Ax <= ub
    integrality=np.ones(n),             # 1 = integer, 0 = continuous
    bounds=Bounds(lb=0, ub=1),          # variable bounds
)
# result.x = solution, result.fun = objective value
```

---

## Problem-by-Problem Impact

| Problem | Expected | Correct/16 | None/16 | Main Failure Mode |
|---------|----------|------------|---------|-------------------|
| 21fb4e | 16 | 2 | 10 | Minimum hitting set -- needs ILP, backtracking times out |
| dbbfe8 | 22 | 1 | 6 | Minimum domino covering -- needs ILP or clever DP |
| a824c1 | 24 | 0 | 8 | Minimum diagonal cover -- needs ILP, brute force infeasible for n=13 |
| c19295 | 48 | 4 | 1 | Maximum induced matching -- some attempts solve analytically |
| aff75c | 3571 | 3 | 0 | Optimization with constraints |
| 26bee3 | 108 | 0 | 10 | Grid tiling/Hamiltonian -- needs constraint solver |
| 581a58 | 18 | 5 | 8 | Maximum independent set / clique |
| ae2add | 24931 | 0 | 9 | Maximum grid points with constraints |

Total: **15/128 correct (11.7%)** on ILP-needing problems, vs ~44/50 baseline.

---

## Current Prompt vs Reality

The v23 prompt already includes:
```
# Available Libraries:
- sympy, numpy, scipy, networkx, mpmath, random, itertools, math, functools, fractions, collections, decimal, heapq, statistics
- NOT available (ImportError): pulp, ortools, z3-solver, mip, pyscipopt, pysat, constraint, matplotlib, sklearn
- For optimization: use scipy.optimize or sympy instead of pulp/cvxpy
- For constraint satisfaction: use itertools + filtering or sympy.solvers instead of z3/constraint
- For graph problems: use networkx or manual BFS/DFS with collections.deque
```

**This is clearly not working.** The model still attempts 115 pulp imports and 92 ortools imports.
The problems:
1. "use scipy.optimize" is too vague -- model doesn't know about `milp()` specifically
2. "use itertools + filtering" for constraint satisfaction is laughable for problems with 10^15 search spaces
3. No concrete API examples -- model doesn't know the scipy.optimize.milp signature
4. The prohibition isn't strong enough -- model "forgets" or ignores the NOT available list

---

## Exact Prompt Text Recommendations

### Option A: Minimal -- Just tell model what's unavailable and what to use instead

Replace the current library section with:

```
LIBRARY AVAILABILITY:
- NOT installed: pulp, ortools, z3-solver, mip, pyscipopt, pysat, cvxpy
- Available: numpy, sympy, scipy (including scipy.optimize), math, itertools, collections,
  functools, fractions, networkx, heapq

OPTIMIZATION REPLACEMENTS:
- For linear programming: use scipy.optimize.linprog (it IS available)
- For integer/binary programming (ILP/MILP): use scipy.optimize.milp with integrality parameter
  Example: milp(c, constraints=LinearConstraint(A, lb, ub), integrality=ones(n), bounds=Bounds(0,1))
- For constraint satisfaction: implement backtracking with pruning, or encode as ILP via scipy.optimize.milp
- For graph optimization (max matching, coloring): use networkx
- Do NOT attempt to import pulp, ortools, z3, or mip -- they will fail
```

### Option B: Detailed with examples

Add to system prompt:

```
LIBRARY AVAILABILITY:
The following are NOT installed and will error: pulp, ortools (CP-SAT/linear_solver), z3-solver,
mip (python-mip), pyscipopt, pysat, cvxpy, constraint (python-constraint).
Do NOT try to import them. Do NOT waste turns probing for them.

For optimization and constraint problems, use these AVAILABLE alternatives:

1. INTEGER LINEAR PROGRAMMING (replaces pulp, mip, ortools linear_solver):
   from scipy.optimize import milp, LinearConstraint, Bounds
   import numpy as np
   # Minimize c^T x, subject to lb <= Ax <= ub, x in {0,1}
   res = milp(c=c_vec, constraints=LinearConstraint(A, lb, ub),
              integrality=np.ones(n), bounds=Bounds(0, 1))
   # res.success, res.x (solution), res.fun (objective value)

2. LINEAR PROGRAMMING (replaces pulp for LP):
   from scipy.optimize import linprog
   res = linprog(c, A_ub=A, b_ub=b, bounds=[(None,None)]*n, method='highs')

3. GRAPH ALGORITHMS (replaces networkx-dependent ortools):
   import networkx as nx  # IS available
   # Max matching: nx.max_weight_matching(G)
   # Shortest path: nx.shortest_path(G, source, target)
   # Connected components: nx.connected_components(G)

4. CONSTRAINT SATISFACTION (replaces z3, ortools CP-SAT):
   Encode as ILP via scipy.optimize.milp, or implement backtracking with pruning.
   For small problems: use itertools.product to enumerate, with early termination.

5. ASSIGNMENT PROBLEMS:
   from scipy.optimize import linear_sum_assignment
   row_ind, col_ind = linear_sum_assignment(cost_matrix)
```

### Option C: Ultra-compact (minimal token cost)

```
AVAILABLE: numpy, sympy, scipy (scipy.optimize.linprog, scipy.optimize.milp), networkx, itertools, math, functools, fractions, heapq, collections.
NOT AVAILABLE (do not import): pulp, ortools, z3, mip, pyscipopt, pysat, cvxpy.
For ILP/MILP: use scipy.optimize.milp(c, constraints=LinearConstraint(A,lb,ub), integrality=ones(n), bounds=Bounds(0,1)).
For LP: use scipy.optimize.linprog.
For graphs: use networkx.
```

---

## Recommended Approach

**Option B** (detailed with examples) because:

1. The model's #1 problem is not knowing `scipy.optimize.milp` exists. Just saying "not available"
   doesn't fix the ILP gap. The model needs to know MILP is solved by scipy.

2. Showing the exact API signature saves the model from hallucinating the interface (which wastes
   more turns on wrong API calls).

3. The token cost of Option B in the prompt is ~300 tokens. This saves ~70,000 tokens of wasted
   library probing per run, a 230x return.

4. The problems that need ILP (21fb4e, a824c1, 26bee3, etc.) are currently near-zero success.
   Even a modest improvement (say 30% -> ILP finds optimal) would add 2-3 correct problems.

---

## Recovery Pattern Summary

When the model fails to import optimization libraries, it uses these alternatives
(ordered by frequency):

| Recovery Strategy | Frequency | Success Rate | Notes |
|-------------------|-----------|-------------|-------|
| Brute-force backtracking with pruning | Very High | Low (~15%) | Usually times out on problems larger than ~20 variables |
| Greedy heuristic (max coverage) | High | Very Low (~5%) | Gets suboptimal answer, wrong for "find minimum" problems |
| Bitmask DP | Medium | Medium (~40%) | Only works when state space fits in memory (<25 elements) |
| Analytical reasoning (no code) | Low | High (~60%) | When model reasons through math without needing solver |
| scipy.optimize.linprog | Very Low (3 problems) | High (~80%) | Model rarely discovers this is available |
| Manual bipartite matching | Very Low | High | Model implements Hungarian/Hopcroft-Karp from scratch |

**Key insight:** The model's best recovery is analytical reasoning (skip the solver entirely),
but this only works for problems with elegant mathematical structure. For combinatorial
optimization problems that truly need ILP, the model's fallbacks are inadequate -- which is
exactly why teaching it about scipy.optimize.milp is critical.

---

## Verification Needed

Before adding scipy.optimize.milp to the prompt, verify it works in the Kaggle environment:

```python
from scipy.optimize import milp, LinearConstraint, Bounds
import numpy as np

# Test: minimize -x1 - x2, subject to x1 + x2 <= 3, x1,x2 binary
c = np.array([-1, -1])
A = np.array([[1, 1]])
res = milp(c, constraints=LinearConstraint(A, -np.inf, 3),
           integrality=np.ones(2), bounds=Bounds(0, 1))
print(res.x, res.fun)  # Should give [1, 1], -2
```

Also verify `networkx` is importable (logs show it works for some problems, fails for
deprecated API calls like `graph_clique_number`, but basic import succeeds).
