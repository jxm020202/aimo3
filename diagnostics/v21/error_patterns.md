# V21 Deep Error Pattern Analysis

## Executive Summary

120 traceback errors across 13/50 problems. 4 problems account for 78% of all errors.
The dominant pattern is a **vicious cycle**: code cell errors -> function definitions lost ->
model re-defines them -> introduces new errors -> more definitions lost. This cycle
consumed **~300 extra seconds per high-error problem** and is the single biggest
source of wasted compute.

---

## 1. Broken Functions and Libraries

### 1.1 Cross-Cell NameError: Lost Function Names (46 errors, 38.3%)

These are functions the model defined in a code cell that errored partway through,
so the definitions never executed. The model then references them in the next cell.

| Lost Name | Occurrences | Problem | What It Does |
|-----------|-------------|---------|-------------|
| `triangle_data_given_n_r` | 7 | 641659 | Geometry helper computing triangle properties given n and inradius |
| `compute_ratio` | 5 | 641659 | Computes BT/BC ratio for the geometry problem |
| `find_point` | 5 | b4ec47 | Finds intersection points for dodecagon rectangles |
| `sp` (sympy alias) | 3 | dd7f5e, f84c73 | `import sympy as sp` lost when cell errors before import |
| `p` | 2 | 86e8e5 | Prime variable in Norwegian numbers problem |
| `ratio_for_n` | 2 | 641659 | Wrapper around compute_ratio |
| `x` | 2 | 641659, f84c73 | Sympy Symbol variable |
| `compute_M_mod` | 1 | 86e8e5 | Computes M mod various primes |
| `D_exact` | 1 | 0e644e | Exact discriminant value |
| `F` | 1 | 0e644e | Function variable |
| `new_groups` | 1 | 424e18 | Tournament grouping computation |
| `v2_total` | 1 | 424e18 | Version 2 total count |
| `compute_vals` | 1 | 424e18 | Value computation helper |
| `debug_compute` | 1 | 641659 | Debug wrapper |
| `find_t` | 1 | 641659 | Finds parameter t in geometry |
| `circumcenter_mp` | 1 | 641659 | Mpmath circumcenter calculation |
| `O_ABC` | 1 | 641659 | Circumcenter point |
| `O_center` | 1 | 641659 | Center point variable |
| `B` | 1 | 641659 | Triangle vertex |
| `circumcenter` | 1 | 641659 | Sympy circumcenter function |
| `odd_part` | 1 | dd7f5e | Extracts odd part of integer |
| `pairs` | 1 | 471086 | Pair enumeration variable |
| `n` | 1 | b4ec47 | Loop variable |
| `verts` | 1 | b4ec47 | Vertex list for dodecagon |
| `segment_intersection` | 1 | b4ec47 | Line segment intersection helper |
| `points_float` | 1 | b4ec47 | Float-converted vertex coordinates |
| `c` | 1 | f84c73 | Variable |

**Key observation**: Problem 641659 alone lost 22 distinct function definitions across
its 8 attempts. The model kept re-defining `triangle_data_given_n_r` 7 times and
`compute_ratio` 5 times. Each re-definition wastes a code call and ~500-2000 tokens.

### 1.2 Hallucinated Sympy/Mpmath APIs (13 AttributeErrors + 2 ImportErrors)

The model confidently calls methods that do not exist.

| Hallucinated Call | Correct Alternative | Occurrences | Problem(s) |
|------------------|-------------------|-------------|-----------|
| `sympy.crt(...)` | `from sympy.ntheory.modular import crt` | 4 AttributeError + 1 ImportError | 86e8e5, f84c73 |
| `sympy.valuation(...)` | `sympy.multiplicity(p, n)` or `sympy.factorint` | 2 AttributeError + 1 ImportError | 26de63 |
| `mpmath.linalg` | Does not exist; use `mp.matrix` operations directly | 1 | 641659 |
| `mp.matrix.dot(...)` | Manual dot product: `sum(a[i]*b[i] for i in range(n))` | 2 | 641659 |
| `sympy.npolycyclotomic_poly(...)` | `sympy.cyclotomic_poly(n, x)` | 1 | dd7f5e |
| `sympy.npolycyclotomic(...)` | `sympy.cyclotomic_poly(n, x)` | 1 | dd7f5e |
| `sympy.npoly(...)` | Does not exist | 1 | dd7f5e |
| `Float.real` | `Float.as_real_imag()[0]` or `re(x)` | 1 | 6837b1 |

**Repeat offender**: `sympy.crt` is hallucinated in 4 separate attempts across 2 problems.
The model "knows" sympy has CRT but always guesses the import path wrong. After the
AttributeError, it sometimes tries `from sympy import crt` (also wrong), wasting a
second code call on the same mistake.

**The `npolycyclotomic_poly` pattern**: The model invents a function name that is a
mashup of real sympy function names (`nthroot`, `cyclotomic_poly`). It tried this
3 times in problem dd7f5e, each time with a slightly different invented name.

### 1.3 Sympy/Python Type Mixing (3 TypeErrors)

| Pattern | What Happens | Occurrences | Problem |
|---------|-------------|-------------|---------|
| `pow(int, sympy.Zero, int)` | Python's 3-arg `pow()` rejects sympy's `Zero` type. Model uses `from sympy import *` then `pow(base, exp, mod)` where `exp` became `sympy.Integer(0)` instead of Python `int(0)`. | 3 | 86e8e5 (attempts 1, 3, 5) |

This is a cross-attempt persistent bug: the model makes the exact same `pow(int, Zero, int)`
mistake in 3 separate attempts. It never learns the fix within the problem scope.

### 1.4 Hallucinated print() kwargs (6 TypeErrors)

| Pattern | Occurrences | Problem |
|---------|-------------|---------|
| `print(simple = lambda x: x+1)` | 3 | 641659 |
| `print(a = 5)` | 1 | 641659 |
| `print(x=5)` | 1 | 641659 |
| `print(yA_sq = c_len**2 - xA)` | 1 | 641659 |

The model confuses Python's `print()` with f-string debugging syntax (`print(f"{yA_sq=}"`)
or with sympy's `pprint(simple=True)`. The `print(simple = lambda x: x+1)` pattern
was repeated identically 3 times in the same attempt -- the model did not learn from
the first failure and kept retrying the same wrong syntax.

### 1.5 None Propagation Cascades (12 TypeErrors)

When a geometry helper function returns `None` (because its internal computation failed
silently), the model proceeds to use the result in arithmetic:

| Error Message | Occurrences | Problem |
|--------------|-------------|---------|
| `unsupported operand type(s) for *: 'NoneType' and 'float'` | 3 | 641659 |
| `'NoneType' object is not subscriptable` | 3 | 641659 |
| `unsupported operand type(s) for -: 'float' and 'NoneType'` | 2 | 641659 |
| `cannot unpack non-iterable NoneType object` | 2 | 641659 |
| `unsupported operand type(s) for /: 'NoneType' and 'int'` | 1 | 86e8e5 |
| `unsupported operand type(s) for +: 'NoneType' and 'int'` | 1 | 641659 |
| `unsupported operand type(s) for -: 'NoneType' and 'int'` | 1 | 641659 |
| `'NoneType' object is not callable` | 1 | c8adf3 |

All 12 of these are secondary errors: a computation upstream returned `None`
(the root cause), and the model blindly used the result. The model never adds
`if result is None: handle_error()` guards.

### 1.6 Large Number Handling (5 errors)

| Error | Occurrences | Problem |
|-------|-------------|---------|
| `ValueError: Exceeds the limit (4300 digits) for integer string conversion` | 4 | 86e8e5 |
| `OverflowError: int too large to convert to float` | 1 | 26de63 |

Problem 86e8e5 involves M = 3^{2025!}. The model's instinct is to compute the actual
number first, then reduce -- but M has more digits than atoms in the universe. This
error recurs across 4 separate attempts (1, 4, 5, 6). The model fails to learn
"always work modularly" even after hitting the 4300-digit limit multiple times.

### 1.7 Missing Modules (1 error)

| Module | Problem |
|--------|---------|
| `matplotlib` | 737d44 |

The Kaggle sandbox does not have matplotlib available. The model tried to
`import matplotlib` once.

---

## 2. Error Impact on Time

### 2.1 Problem-Level: High-Error vs Clean Problems

| Group | Count | Avg Wall Time | Avg Errors | Avg Tokens | Correct % |
|-------|-------|--------------|------------|------------|-----------|
| High error (>5 errors) | 6 | **330.4s** | 24.5 | 156,605 | 83.3% |
| Low error (1-5 errors) | 33 | **46.3s** | 2.5 | 31,401 | 100% |
| Zero error | 11 | **28.8s** | 0.0 | 21,815 | 100% |

High-error problems take **7.1x longer** than low-error problems and
**11.5x longer** than zero-error problems. They also consume **5.0x more tokens**
and have a **16.7% failure rate** (1/6 got the wrong answer: 86e8e5).

### 2.2 Attempt-Level: Within-Problem Comparison

**Problem 641659** (geometry, 71 total errors):

| Attempt Group | N | Avg Time | Avg Code Calls | Avg Tokens | Correct |
|--------------|---|----------|----------------|------------|---------|
| Errors >= 5 | 5 | **495.3s** | 64.4 | 38,712 | 2/5 (40%) |
| Errors 1-4 | 2 | **197.5s** | 22.0 | 14,870 | 2/2 (100%) |
| Errors = 0 | 1 | **476.8s** | 0.0 | 49,541 | 0/1 (0%) |

Within the same problem, error-heavy attempts take **2.5x longer** than low-error
attempts and have **2.5x lower** success rate.

Note: The zero-error attempt (attempt 2) used 0 code calls but still took 476.8s
because it tried to reason purely through text (and got the wrong answer). This
shows the problem is genuinely hard -- but errors make it worse.

**Problem 86e8e5** (Norwegian numbers, 24 total errors):

| Attempt Group | N | Avg Time | Avg Code Calls | Avg Tokens | Correct |
|--------------|---|----------|----------------|------------|---------|
| Errors >= 5 | 2 | **403.2s** | 37.5 | 37,963 | 0/2 (0%) |
| Errors 1-4 | 6 | **277.1s** | 25.0 | 25,068 | 1/6 (17%) |

Error-heavy attempts are **45% slower** and have 0% success. The one correct attempt
(attempt 2, answer 8687) had only 2 errors.

**Problem b4ec47** (dodecagon, 19 total errors):

| Attempt Group | N | Avg Time | Avg Code Calls | Avg Tokens | Correct |
|--------------|---|----------|----------------|------------|---------|
| Errors >= 5 | 2 | **333.2s** | 58.0 | 29,049 | 2/2 (100%) |
| Errors 1-4 | 3 | **248.8s** | 44.7 | 24,311 | 0/3 (0%) |
| Errors = 0 | 3 | **110.1s** | 13.3 | 11,237 | 2/3 (67%) |

Clean attempts are **3x faster** than high-error attempts.

### 2.3 Time Cost Per Error

Rough estimate across all high-error problems:
- Each error wastes approximately **1 code call** (re-defining the lost function)
- Each re-definition costs ~500-2000 tokens of model output
- Average code call takes ~5-8 seconds (kernel execution + model reasoning)
- But the cascade effect multiplies: 7 consecutive `triangle_data_given_n_r` NameErrors
  wasted ~7 code calls = ~35-50 seconds of pure mechanical recovery

**Conservative estimate**: The 120 errors wasted ~250-400 code calls and
~100,000-200,000 tokens across the entire run, adding ~20-30 minutes of total
wall time (spread across parallel attempts).

---

## 3. Error Cascades: The Vicious Cycle

### 3.1 The Core Cascade Pattern

The most common cascade follows this sequence:

```
Step 1: Model writes code cell with function definition + computation
Step 2: Computation hits an error (e.g., wrong API, type mismatch)
Step 3: Error kills the cell -> function definition at top of cell is LOST
Step 4: Model says "let me try again" and references the function
Step 5: NameError: function not defined
Step 6: Model re-defines function, introduces slight variation -> new error
Step 7: Go to Step 3
```

### 3.2 Documented Cascades

**Cascade A: 641659 Attempt 1 (22 errors, lines 39130-44443)**

```
L39130: NameError: triangle_data_given_n_r  (function lost from failed cell)
  |-- Model re-defines it, cell errors again
L39405: NameError: triangle_data_given_n_r  (still lost)
  |-- Repeat 5 more times (L39640, L39873, L40106, L40376, L40754)
  |-- Model gives up on that approach, tries different code
L41277: TypeError: print(simple=...) -- hallucinated kwarg
L41291: TypeError: print(simple=...) -- same mistake repeated
L41307: TypeError: print(simple=...) -- third time, still not learning
L41533: TypeError: print(a=5) -- slightly different hallucinated kwarg
  |-- These errors kill cells that defined new helper functions
L41912: TypeError: float - NoneType  <-- None propagation from lost computation
L41986: TypeError: float - NoneType  <-- same cascade
L42136: NameError: ratio_for_n       <-- function lost from the TypeError cells
L42182: NameError: ratio_for_n       <-- still lost
L42289: TypeError: NoneType unpack   <-- None from ratio_for_n absence
L42355: NameError: debug_compute     <-- another lost function
L42670: NameError: find_t            <-- another lost function
L43661: ValueError: math domain      <-- model tries different approach, sqrt(-1)
L43899: AttributeError: mpmath.linalg  <-- hallucinated API
L44331: NameError: circumcenter_mp   <-- function lost from the linalg failure
L44443: TypeError: mpf from Fraction <-- type mixing
```

This is a textbook cascade: 7 rounds of losing `triangle_data_given_n_r`, then 3 rounds
of `print(simple=...)`, then None propagation, then more lost functions, then API
hallucination, then more lost functions. **22 errors in one attempt**, consuming 84 code
calls and 51,671 tokens over 564 seconds -- and it produced NO ANSWER.

**Cascade B: 641659 Attempt 5 (8 errors, lines 54059-58934)**

```
L54059: NameError: compute_ratio    (lost function)
L54384: NameError: compute_ratio    (re-define attempt failed)
L54696: NameError: compute_ratio    (third attempt)
L55365: NameError: compute_ratio    (fourth attempt -- 4 code calls wasted)
L56526: ValueError: unpack mismatch (model finally gets compute_ratio defined
                                     but it returns wrong number of values)
L56771: TypeError: None + int       <-- compute_ratio returned None
L58294: NameError: O_center          <-- new function lost from TypeError cell
L58934: IndexError: out of range     <-- downstream logic error
```

4 consecutive NameErrors for `compute_ratio`, then when it finally works, the return
value is wrong, leading to None propagation, leading to another lost function.

**Cascade C: 641659 Attempt 3 (6 errors, lines 48492-50853)**

```
L48492: NameError: O_ABC             (lost circumcenter variable)
L48782: UnboundLocalError: proj      (partial execution left variable unset)
L49024: TypeError: None[0]           <-- function returned None
L49743: TypeError: None[0]           <-- same None propagating further
L50483: TypeError: NoneType unpack   <-- same None, different usage
L50853: TypeError: None * float      <-- same None, yet another usage
```

One lost variable (`O_ABC`) triggered a chain of 5 None-propagation errors, each
representing a different downstream use of the same `None` value.

**Cascade D: 86e8e5 Attempts 3 and 5 (identical pattern)**

```
L14032/16249: TypeError: pow(int, Zero, int)  -- sympy/Python mixing
L14102/16360: AttributeError: sympy.crt       -- hallucinated API
L14747/16919: NameError: p / ValueError: 4300 digits  -- cascading consequences
```

The model makes the EXACT SAME sequence of mistakes in attempts 3 and 5.
It does not learn across attempts within a single problem.

### 3.3 Cascade Statistics

| Cascade Type | Occurrences | Typical Chain Length | Time Wasted per Chain |
|-------------|-------------|---------------------|----------------------|
| NameError repeat (same function) | 6 distinct chains | 2-7 errors | 15-50s |
| Error -> NameError (function lost from failed cell) | 4 instances | 2-3 errors | 10-20s |
| None propagation chain | 4 chains | 2-4 errors | 10-30s |
| Cross-attempt identical mistake | 2 patterns | 2-3 attempts each | 60-120s total |
| print() kwarg repeat | 1 chain | 3-4 errors | 15-25s |

### 3.4 Cross-Attempt Non-Learning

The most concerning cascade pattern is the model making the **exact same mistake across
separate attempts** within the same problem:

1. **`pow(int, Zero, int)`** in 86e8e5: Attempts 1, 3, and 5 all hit this error.
   The model never adds `int()` cast around sympy's Zero.

2. **`sympy.crt`** in 86e8e5: Attempts 2, 3, 5, and 7 all try `sympy.crt` or
   `from sympy import crt`. 4 separate attempts, same wrong import path.

3. **`4300 digit limit`** in 86e8e5: Attempts 1, 4, 5, and 6 all try to print
   a number with billions of digits. The model never learns to work modularly.

4. **`triangle_data_given_n_r` loss** in 641659: The function is lost and re-defined
   across multiple attempts. Each time, the model re-writes it from scratch rather
   than putting the definition at the top of every cell.

---

## 4. Problem-Specific Breakdown

### Problem 641659 (Geometry + Fibonacci) -- 71 errors

The worst-performing problem by error count. This is a geometry problem involving
triangle incircle, circumcircle, reflections, and Fibonacci sequences.

- **Why so many errors**: Geometry code requires many helper functions
  (`circumcenter`, `find_point`, `segment_intersection`, `compute_ratio`,
  `triangle_data_given_n_r`). When any cell errors, multiple functions are lost.
  The model also struggles with mpmath vs sympy vs numpy type boundaries.
- **Error profile**: 22 cross-cell-reference, 10 none-propagation, 10 type-error-other,
  4 hallucinated-api, 3 value-error-other, 2 wrong-attribute
- **Outcome**: Got correct answer (57447) in 4/8 attempts, but the 3 failed attempts
  (timed out at 562s each) consumed 235 code calls and 137,494 tokens for no result.

### Problem 86e8e5 (Norwegian Numbers) -- 24 errors

M = 3^{2025!} involves astronomically large numbers. The model repeatedly tries to
compute M directly instead of working modularly.

- **Error profile**: 4 bigint-str-limit, 3 sympy-int-mix, 3 cross-cell-reference,
  4 wrong-attribute/wrong-import, 1 none-propagation, 1 key-error
- **Outcome**: WRONG. Predicted 41754, correct answer 8687. Only 1/8 attempts got
  the right answer. Errors directly contributed to failure by wasting code calls
  that could have been used for correct computation.

### Problem b4ec47 (Dodecagon Rectangles) -- 19 errors

Counting rectangles in a regular 12-gon. The `find_point` function was lost 5 times
in attempt 1 alone.

- **Error profile**: 9 cross-cell-reference, 2 index-error, 2 type-error-other,
  2 hallucinated-api, 4 other
- **Outcome**: Correct (315) but took 390.5s wall time. Clean attempts solved it
  in 103-144s.

### Problem dd7f5e (Shifty Functions) -- 16 errors

Number theory problem with cyclotomic polynomials. The model hallucinated
`sympy.npolycyclotomic_poly` (doesn't exist), tried it 3 times with slight
name variations, then also lost `sp` (sympy alias) 3 times.

- **Error profile**: 4 cross-cell-reference, 3 wrong-attribute, 3 none-propagation,
  2 key-error, 2 type-error-other, 1 value-error-other, 1 missing-module
- **Outcome**: Correct (160) in 4/8 attempts.

---

## 5. Summary of Actionable Findings (Diagnosis Only)

### Top 5 Error Patterns by Impact

1. **Cross-cell function loss** (46 errors, ~150 wasted code calls):
   Model defines functions in cells that error, losing the definitions.
   Geometry problems are worst because they need many helper functions.

2. **Hallucinated sympy/mpmath APIs** (15 errors, repeated across attempts):
   `sympy.crt`, `sympy.valuation`, `mpmath.linalg`, `matrix.dot`,
   `sympy.npolycyclotomic_poly`. Model confidently calls non-existent methods.

3. **None propagation chains** (12 errors, always secondary):
   Upstream function returns None silently, downstream code crashes.
   Model never adds None guards.

4. **Sympy/Python type boundary** (3+6 errors):
   `pow(int, sympy.Zero, int)` and `print(variable_name=value)` patterns.
   Model confuses Python builtins with sympy/f-string idioms.

5. **Large number mis-handling** (5 errors):
   Model tries to compute/print numbers with billions of digits instead of
   working modularly. Repeats the same mistake across attempts.

### The Non-Learning Problem

The most concerning finding is that the model does **not learn from its own errors
within the same problem**. It repeats:
- `sympy.crt` in 4 separate attempts
- `pow(int, Zero, int)` in 3 separate attempts
- `4300 digit limit` in 4 separate attempts
- `print(simple=...)` 3 times in the same attempt

Each attempt starts fresh with the same system prompt but no memory of previous
attempts' errors. This means prompt-level fixes (telling the model what NOT to do)
are the only lever for these patterns.
