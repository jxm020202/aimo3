# Kaggle AIMO3 Environment: Pre-installed Python Libraries

## Environment Architecture

The Kaggle notebook environment is built as a **layered Docker image**:

1. **Base layer**: Google Colab GPU image (`us-docker.pkg.dev/colab-images/public/runtime:release-colab-external_20260126`)
2. **Kaggle layer**: Additional packages from `kaggle_requirements.txt` installed on top
3. **Our notebook layer**: Cell 0 uninstalls keras, matplotlib, scikit-learn, tensorflow to free memory, then installs vllm, unsloth, trl, openai_harmony from bundled wheels (`aimo-3-utils`)

Source: [Kaggle/docker-python on GitHub](https://github.com/Kaggle/docker-python)

### Docker Image Pinning

Our `kernel-metadata.json` pins a specific Docker image:
```json
"docker_image": "gcr.io/kaggle-private-byod/python@sha256:536e3d97..."
"machine_shape": "NvidiaH100"
"accelerator": "nvidiaH100"
```

This is the **standard Kaggle GPU image**, not a custom AIMO3 competition image. The competition uses the regular Kaggle Python environment.

### No Internet During Submission

`enable_internet: false` -- any package not pre-installed or bundled in a dataset must be pip-installed from offline wheels.

---

## Confirmed from v23 Kernel Logs

### Successfully imported (no errors):
- `numpy` (as np) -- used extensively
- `sympy` (as sp) -- used extensively
- `math` -- stdlib, always available
- `itertools` -- stdlib, always available
- `collections` -- stdlib, always available
- `functools` -- stdlib, always available
- `fractions` -- stdlib, always available
- `decimal` -- stdlib, always available
- `random` -- stdlib, always available
- `time` -- stdlib, always available
- `sys` -- stdlib, always available
- `os` -- stdlib, always available
- `json` -- stdlib, always available
- `copy` -- stdlib, always available
- `heapq` -- stdlib, always available
- `statistics` -- stdlib, always available
- `typing` -- stdlib, always available
- `subprocess` -- stdlib, always available

### Confirmed MISSING (ModuleNotFoundError in logs):
- `pulp` -- **14+ failures** in v23 logs. Most frequently attempted missing package.
- `ortools` -- **11+ failures**. Second most attempted missing package.
- `z3` (z3-solver) -- **2 failures** in v23 logs
- `mip` -- **1 failure** in v23 logs

### Never attempted by the model (unknown status):
- `scipy` -- never imported in code execution cells
- `networkx` -- never imported in code execution cells
- `matplotlib` -- uninstalled by cell 0 (was pre-installed)
- `pandas` -- never imported in code execution cells
- `scikit-learn` -- uninstalled by cell 0 (was pre-installed)
- `cvxpy` -- never attempted
- `pyscipopt` -- never attempted
- `pysat` -- never attempted
- `constraint` -- never attempted

---

## Full Package Availability Assessment

### DEFINITELY AVAILABLE (from Colab base image + Kaggle layer)

| Package | Source | Notes |
|---------|--------|-------|
| **numpy** | Colab base | v2.4.x. Core scientific computing. Confirmed working in v23. |
| **sympy** | Colab base | Symbolic math. Confirmed working in v23. Model uses it heavily. |
| **scipy** | Colab base | Scientific computing, optimization, linear algebra. Pre-installed in Colab. |
| **matplotlib** | Kaggle layer | Listed in kaggle_requirements.txt. Pre-installed BUT our notebook uninstalls it (cell 0) to save memory for vllm. |
| **pandas** | Colab base | Data manipulation. Pre-installed. |
| **scikit-learn** | Kaggle layer | Listed in kaggle_requirements.txt. Pre-installed BUT our notebook uninstalls it (cell 0). |
| **tensorflow** | Colab base | Pre-installed BUT our notebook uninstalls it (cell 0). |
| **keras** | Colab base | Pre-installed BUT our notebook uninstalls it (cell 0). |
| **torch/pytorch** | Colab base | Pre-installed. Required by vllm. |
| **jax/jaxlib** | Colab base | Pre-installed in Colab base. |
| **optuna** | Kaggle layer | Listed in kaggle_requirements.txt. Hyperparameter optimization. |
| **onnx** | Kaggle layer | Listed in kaggle_requirements.txt. |
| **catboost** | Kaggle layer | Listed in kaggle_requirements.txt. |
| **opencv** | Colab base | Pre-installed. |
| **pillow** | Colab base | Pre-installed. |
| **graphviz** | Kaggle Dockerfile | Installed via apt + pip in Dockerfile. |
| **nltk** | Kaggle Dockerfile | Pre-installed with many corpora. |

### PROBABLY AVAILABLE (from Colab base image, high confidence)

| Package | Reasoning |
|---------|-----------|
| **networkx** | Standard Colab package, widely used in data science. Colab includes it. |
| **cvxpy** | Confirmed in Colab release notes (upgraded from 1.3.4 to 1.5.2). Convex optimization. |
| **mpmath** | Dependency of sympy. If sympy works, mpmath is there. |
| **numba** | In Kaggle release notes (v0.63.0b1). JIT compilation for numerical code. |
| **igraph** | Listed in kaggle_requirements.txt. Graph theory. |
| **h2o** | Listed in kaggle_requirements.txt. |
| **gensim** | Listed in kaggle_requirements.txt. |

### CONFIRMED NOT AVAILABLE (must pip install from offline wheels)

| Package | Evidence | Impact on AIMO3 |
|---------|----------|-----------------|
| **pulp** | 14+ ModuleNotFoundError in v23 logs | LP/MILP solver. Model tries this VERY frequently for optimization problems. |
| **ortools** (Google OR-Tools) | 11+ ModuleNotFoundError in v23 logs | CP-SAT solver. Model tries this frequently for constraint programming. |
| **z3-solver** | 2 ModuleNotFoundError in v23 logs | SMT solver. Model tries for constraint satisfaction. |
| **mip** (Python-MIP) | 1 ModuleNotFoundError in v23 logs | MILP solver. Model tries as pulp fallback. |

### PROBABLY NOT AVAILABLE (specialized packages, not in any requirements)

| Package | Reasoning |
|---------|-----------|
| **pyscipopt** | SCIP optimization suite Python interface. Not in Colab or Kaggle requirements. |
| **pysat** | SAT solver. Not in standard data science stacks. |
| **constraint** (python-constraint) | CSP solver. Niche package. |
| **sagemath** | Full math system. Enormous, never in Docker images. |
| **galgebra** | Geometric algebra. Niche. |
| **gmpy2** | GNU multiple precision. Might be a sympy dependency but not guaranteed. |

---

## Impact Analysis: What the Model Tries to Import

From v23 logs, the model's code execution attempts these library patterns:

### Most common successful imports:
1. `import math, itertools` -- almost every code cell
2. `import numpy as np` -- very frequent
3. `import sympy as sp` -- frequent for symbolic math
4. `from collections import Counter` -- frequent
5. `import random, time` -- frequent for search algorithms
6. `import functools, heapq, copy` -- occasional

### Most common FAILED imports (by frequency):
1. **`import pulp`** -- 14+ failures. Model wants LP/MILP solving.
2. **`from ortools.sat.python import cp_model`** -- 11+ failures. Model wants constraint programming.
3. **`import z3`** -- 2 failures. Model wants SMT solving.
4. **`import mip`** -- 1 failure. Model wants MILP as pulp fallback.

### Typical failure pattern:
The model tries pulp first, gets ModuleNotFoundError, then tries ortools, gets another error, then either gives up on optimization or falls back to brute-force/backtracking search with numpy.

---

## Actionable Recommendations

### Option A: Bundle missing solvers as offline wheels

Add these to the `aimo-3-utils` wheels dataset:
- `pulp` (~2MB) -- pure Python, easy to bundle
- `ortools` (~50MB+) -- large, C++ extensions, harder to bundle but high value
- `z3-solver` (~30MB+) -- C++ extensions
- `mip` (~5MB) -- needs CBC solver binary

**Pros**: Model can solve optimization/constraint problems it currently fails on.
**Cons**: Adds to setup time, disk space. ortools + z3 are large packages with C dependencies.

### Option B: Add to system prompt "these packages are NOT available"

Tell the model explicitly:
```
The following packages are NOT installed: pulp, ortools, z3, mip, pyscipopt, pysat, constraint, sage.
Available math packages: numpy, sympy, scipy, itertools, math, fractions, collections.
For optimization problems, use scipy.optimize or implement algorithms directly.
```

**Pros**: Zero overhead. Stops wasted code execution attempts.
**Cons**: Model loses optimization solver capability.

### Option C: Hybrid -- bundle pulp (small, pure Python) + prompt about others

Bundle just `pulp` (small, pure Python, easy) and tell the model ortools/z3 are unavailable but pulp is.

**Pros**: Best cost/benefit. pulp is small and covers most LP/MILP needs.
**Cons**: Misses constraint programming (ortools CP-SAT) which is powerful.

### Available packages useful for math competition:

| Package | What it does for math olympiad |
|---------|-------------------------------|
| **sympy** | Symbolic algebra, number theory (factorint, isprime, mod_inverse, ntheory), polynomial manipulation, combinatorics, Diophantine equations |
| **numpy** | Fast numerical computation, matrix operations, large array processing |
| **scipy.optimize** | Numerical optimization (minimize, linear_sum_assignment) |
| **scipy.special** | Special functions (comb, factorial, gamma) |
| **scipy.linalg** | Matrix decompositions, eigenvalues |
| **itertools** | Permutations, combinations, product, chain |
| **fractions.Fraction** | Exact rational arithmetic |
| **decimal.Decimal** | Arbitrary precision decimal |
| **math** | Basic functions, gcd, isqrt, comb, factorial |
| **collections.Counter** | Counting, multisets |
| **functools.lru_cache** | Memoization for dynamic programming |
| **heapq** | Priority queues for graph algorithms |
| **networkx** (probably) | Graph algorithms if complex graph theory needed |
| **cvxpy** (probably) | Convex optimization if available |

---

## Key Insight

The model wastes significant tokens and code execution budget trying pulp and ortools (25+ combined failures in v23). Each failure costs:
- 1 code execution turn (wasted)
- Token budget for the import attempt + error message
- Model confusion/recovery tokens

**Estimated waste per problem**: 2-4 code execution turns on failed imports when the model wants to solve an optimization or constraint problem. At ~500 tokens per failed attempt + recovery, this is roughly 1000-2000 tokens per affected problem.

The simplest fix is to add a system prompt line: "pulp, ortools, z3, mip are NOT installed. Use scipy.optimize or implement algorithms directly with numpy/sympy."
