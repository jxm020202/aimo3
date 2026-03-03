# V21 Code Error Analysis

## Summary

- **120 traceback errors** across **13 problems** (out of 50)
- **37 problems** (74%) had zero code errors
- All 120 errors concentrated in 13 problems; 4 problems account for 78% of all errors

## Error Type Distribution

| Error Type | Count | % | Root Cause |
|-----------|-------|---|-----------|
| NameError | 46 | 38.3% | Cross-cell state loss |
| TypeError | 34 | 28.3% | Sympy/Python mixing, None propagation, hallucinated kwargs |
| AttributeError | 13 | 10.8% | Hallucinated API methods |
| ValueError | 12 | 10.0% | Bigint str limit, math domain errors |
| KeyError | 5 | 4.2% | Bad dict lookups |
| IndexError | 4 | 3.3% | Out of bounds |
| ImportError | 2 | 1.7% | Wrong import paths |
| OverflowError | 1 | 0.8% | int→float overflow |
| Others | 3 | 2.5% | UnboundLocal, NotImplementedError, ModuleNotFound |

## Root Cause Taxonomy

### 1. Sandbox State Loss (46 errors, 38.3%) — THE #1 ISSUE

**What**: Model defines a function/variable in code cell N, references it in code cell N+1, but it's not defined.

**Why**: Each attempt uses a persistent Jupyter kernel (state carries between code calls within the same attempt). BUT when a code cell errors out mid-execution, only assignments made before the error survive. If the model defines `compute_M_mod` at line 20 and the cell errors at line 15, `compute_M_mod` never gets created.

**Pattern**: The model then says "Oops, lost definitions, let me re-define" and re-writes the function. This wastes a code call and tokens. On problem 641659, this happened **22 times** in a single attempt.

**Concrete examples**:
- `triangle_data_given_n_r` — defined in cell that errored, referenced 7x in subsequent cells
- `compute_M_mod` — defined after an error-causing line, never executed
- `find_point`, `segment_intersection`, `circumcenter_mp` — geometry helpers lost
- `compute_ratio`, `ratio_for_n` — partial execution

**The vicious cycle**: Error → definitions lost → model redefines → but also introduces new error → more definitions lost. Problem 641659 had 71 errors in 366 code calls (19% error rate) because of this cascade.

### 2. Sympy/Python Type Mixing (30 errors, 25.0%)

**What**: Model mixes sympy symbolic objects with Python native operations.

**Subtypes**:
- **`pow(int, Zero, int)`** (3x): Model uses `pow(base, exp, mod)` where `exp` is `sympy.Integer(0)` instead of Python `int(0)`. Python's 3-arg pow doesn't accept sympy types.
- **None propagation** (12x): A function returns `None` unexpectedly (often because an intermediate computation failed silently), then model tries arithmetic on the result: `None * 3.0`, `None - 5`, `None()`.
- **Other type mismatches** (15x): `int` where `float` expected, tuple unpacking failures, wrong argument counts.

**Why**: GPT-OSS-120B doesn't distinguish between sympy's `Integer`, `Float`, `Rational` and Python's `int`, `float`. When it does `from sympy import *` and then uses `pow()`, sympy objects leak into Python builtins.

### 3. Hallucinated APIs (20 errors, 16.7%)

**What**: Model calls methods/attributes/imports that don't exist.

**Subtypes**:
- **Wrong attributes** (13x): `sympy.crt` (should be `sympy.ntheory.modular.crt`), `mpmath.linalg` (doesn't exist), `Float.real`
- **Hallucinated kwargs** (4x): `print(result, simple=True)`, `print(result, a=True)` — neither `simple` nor `a` are valid kwargs for `print()`
- **Wrong import paths** (2x): `from sympy import crt` (correct: `from sympy.ntheory.modular import crt`), `from sympy import valuation` (correct: `sympy.factorint` or `sympy.multiplicity`)
- **Missing module** (1x): `import matplotlib` — not available in sandbox

**Why**: The model hallucinates API surfaces. It "knows" sympy has CRT functionality but guesses the import path wrong. The `print(x, simple=True)` pattern suggests the model confuses `print()` with `sympy.pprint(simple=True)` or similar.

### 4. Large Number Handling (5 errors, 4.2%)

**What**: Problems involving astronomically large numbers hit Python/float limits.

**Subtypes**:
- **Bigint string limit** (4x): Python 3.11+ limits `str(huge_int)` to 4300 digits. The model tries to `print()` a number like `3^{2025!}` which has billions of digits.
- **Int→float overflow** (1x): Model converts huge integer to float, exceeds `float64` range (~1.8e308).

**Why**: These all come from problem 86e8e5 (Norwegian numbers with M=3^{2025!}) and 26de63. The model's instinct is to compute the actual number first, then reduce modularly — but the actual number has more digits than atoms in the universe.

### 5. Logic Errors (17 errors, 14.2%)

**What**: Standard programming bugs — bad dict keys, index out of range, domain errors.

- **KeyError** (5x): Accessing dict keys that don't exist
- **IndexError** (4x): List/tuple index out of range
- **ValueError** (8x): Math domain errors (`sqrt(-1)` in float), failed numerical solvers, bad unpacking

**Why**: These are normal bugs that any programmer makes. The model writes complex code (geometry, number theory, combinatorics) and sometimes the logic is wrong. These are the least concerning error category — they're expected and the model usually recovers by adjusting.

## Errors by Problem

| Problem | Errors | Top Cause | Notes |
|---------|--------|-----------|-------|
| 641659 | 55 | cross-cell (22), none-propagation (10), type-error (10) | Geometry+Fibonacci. Vicious error cascade. |
| 86e8e5 | 16 | bigint-str (4), cross-cell (3), sympy-mix (3) | Norwegian numbers. Large number handling failures. |
| b4ec47 | 13 | cross-cell (9), index-error (2) | Dodecagon rectangles. Complex enumeration. |
| dd7f5e | 9 | cross-cell (4), wrong-attribute (3), key-error (2) | Shifty functions. Sympy API confusion. |
| 737d44 | 5 | key-error (2), wrong-attr (1), missing-module (1) | Various small issues. |
| 26de63 | 4 | wrong-attribute (2), overflow (1), wrong-import (1) | Number theory. |
| f84c73 | 4 | cross-cell (2), type-error (1), wrong-attr (1) | — |
| 424e18 | 3 | cross-cell (3) | Tournament problem. |
| All others | 11 | mixed | 1-3 errors each |

## When Do Errors Happen?

```
Attempt 1:  37 errors  ██████████████████████████████████████
Attempt 3:  16 errors  ████████████████
Attempt 7:  22 errors  ██████████████████████
Attempt 5:  14 errors  ██████████████
Attempt 2:   9 errors  █████████
Attempt 8:   9 errors  █████████
Attempt 4:   8 errors  ████████
Attempt 6:   5 errors  █████
```

Attempt 1 has 3x more errors than average. This makes sense: attempt 1 has no "early stop" benefit — it always runs to completion. Hard problems that burn lots of code calls will disproportionately rack up errors in attempt 1 (longest attempt).

## Error-to-Outcome Correlation

| Problem | Errors | Code Calls | Error Rate | Outcome |
|---------|--------|------------|-----------|---------|
| 641659 | 55 (71 incl non-traceback) | 366 | 19.4% | CORRECT (barely — 4 of 8 attempts) |
| 86e8e5 | 16 (24 incl non-traceback) | 225 | 10.7% | **WRONG** |
| b4ec47 | 13 (19 incl non-traceback) | 290 | 6.6% | CORRECT (barely — 4 of 8 attempts) |
| dd7f5e | 9 (16 incl non-traceback) | 179 | 8.9% | CORRECT (barely — 4 of 8 attempts) |

All 4 high-error problems are the ones flagged as HARD/FAILED. The error cascade directly causes:
1. Wasted code calls (re-defining lost functions)
2. Wasted tokens (model explaining what went wrong)
3. Wrong final answers (when errors corrupt the computation path)

## Relationship to 44.5% None Rate

The 44.5% None rate (178/400 attempts return no answer) is NOT caused by code errors. Most None attempts are from the early_stop mechanism: when 4 attempts agree on an answer, the remaining attempts return None immediately (they were running in parallel but get stopped).

However, for HARD problems without early stop, None results DO come from:
1. Timeout (code ran too long)
2. Answer not found in output (model reasoned correctly but didn't format as `\boxed{}`)
3. Error cascade consuming all code turns without reaching a conclusion

## Comparison with Baseline 44/50

The sandbox code (`AIMO3Sandbox.execute()`), answer extraction (`_scan_for_answer()`), and streaming extraction are **identical** between baseline and v21. The 44.5% None rate is likely the same in the baseline — it's inherent to the architecture (8 parallel attempts, early_stop=4, so 4 always return None in the happy path).

The baseline scored 44/50 on the actual competition (public LB). Our v21 scores 49/50 on test. The difference is:
1. v21 has the `break` fix in extraction (baseline had it too)
2. v21 has prompt improvements (efficiency, bigint hints, code robustness)
3. v21 has `jupyter_timeout 30s` vs baseline's `6s`
4. Different test sets (competition vs our benchmark)
