# Handover Document — March 2, 2026

## Where We Stopped

User and I were analyzing why v18 (Kaggle test run) appeared stuck on reference
problem 4 (86e8e5, the Norwegian number with M=3^{2025!}). After detailed code
comparison, we confirmed our solver is **functionally identical to the 44/50 baseline**
for solving behavior. The long runtimes are inherent to the architecture, not our changes.

User wants no more code changes until we deeply understand the issues. "Every run
takes ages, we need to be sure what we do is correct."

## Current Kaggle State

- **v15**: Submitted to competition. Waiting for re-run results. First competition entry.
- **v19 COMPLETE**: **9/10 reference problems correct (90%)**. Only P4 (Norwegian, 86e8e5) wrong.
  Used OLD cell-17 (no detailed logging). Total runtime ~52 min.
- **New logging version**: Pushed to GitHub (fb9841f) but NOT yet pushed to Kaggle.
  Has full conversation logging (every turn, every code execution, GPU stats).
  Needs `kaggle kernels push -p notebooks/` to deploy.
- **GitHub Actions auto-push DISABLED** — changed to `workflow_dispatch` (manual only).

## Exact Diffs from Baseline 44/50

Our notebook (`notebooks/aimo3-solver.ipynb`) vs `baseline-44-50.ipynb`:

| Change | Location | Impact |
|--------|----------|--------|
| `early_stop = 5` (was 4) | cell-8 CFG | Needs 1 more agreeing answer. ~10-20s more on easy problems. Zero on hard. |
| No `break`/`cancel` on early stop | cell-13 solve_problem | Collects all futures vs breaking early. But `executor.shutdown(wait=True)` waits in both versions anyway. **Effectively identical timing.** |
| Deterministic tie-breaking | cell-13 _select_answer | `sort by (score, votes, answer)` vs just `score`. Zero timing impact. |
| `find_model_path()` | cell-5 | Auto-discovers model mount path. No impact on solving. |
| Test CSV auto-discovery | cell-16 | Tries multiple paths. No impact on solving. |
| Cell-17 test framework | cell-17 (NEW) | Tiered reference problem testing. Only runs in test mode. |
| `dataset_sources` added | kernel-metadata.json | `jxm222/aimo3-test-data` for test framework CSVs. |

**Conclusion: Our code is functionally identical to baseline for solving.** Long runtimes
are inherent to the 8-attempt parallel architecture with 900s budgets.

## Open Questions to Investigate

### 1. Why do problems take so long? (Architecture understanding)
- 8 parallel attempts, each with multi-turn LLM + code execution
- Each attempt runs for up to 900s (15 min) on hard problems
- Easy problems: ~20-30s (quick consensus)
- Medium: ~100-300s
- Hard (no consensus): full 900s budget burned
- **Question**: Is this actually the optimal time allocation? Could we detect "no consensus
  likely" early and give up sooner?

### 2. Sandbox kernel hangs (the real v18 issue)
- Problem 4 has M=3^{2025!}. If model generates `3**math.factorial(2025)`, Python's
  bigint engine hangs forever in C-level code
- `interrupt_kernel()` sends SIGINT but can't interrupt C-level operations
- Sandbox timeout (6s) fires, but kernel becomes zombie — subsequent executes also timeout
- **Research needed**: How to hard-kill hung kernels? `resource.setrlimit()`?
  Subprocess wrapper with SIGKILL? Process-level timeout?

### 3. Better math libraries for sandbox (ADDED TO strategies.md)
- `gmpy2`: Fast modular arithmetic, orders of magnitude faster than Python builtins
- `cypari2`: Number theory (PARI/GP backend)
- `python-flint`: Fast polynomial/number theory (C backend)
- `networkx`: Graph theory for combinatorics problems
- **Key question**: Which are available on Kaggle's docker image? Can any be installed
  from the wheels tarball?

### 4. ~~Prompt engineering for efficient code~~ — DONE (1e0334e)
- **IMPLEMENTED**: Added `pow(base, exp, mod)` hint to `preference_prompt` in cell-8
- Line: "For very large exponents (e.g. a^(n!)), use pow(base, exp, mod) or analytical methods — never materialize the full number"
- Could still add more hints (generating functions, recurrences vs brute-force)

### 5. ~~Should we revert early_stop to 4?~~ — DONE (1e0334e)
- **IMPLEMENTED**: Reverted `early_stop` from 5 → 4 (matches baseline)

### 6. Should we restore break+cancel on early stop?
- Currently we collect all futures even after early stop
- Baseline breaks out and cancels remaining
- Analysis shows both versions wait for running futures due to `executor.shutdown(wait=True)`
- **But**: the `break` does avoid calling `future.result()` on remaining futures, which
  could matter if any future hangs. Recommend restoring for safety.

## What User Explicitly Wants

1. **No code changes until we understand the core issues** — research first, implement later
2. **Disable GitHub Actions auto-push** before any git push
3. **Research better Python math libraries** for faster computation
4. **Research prompt engineering** to make model generate efficient code
5. **Understand why hard problems take 900s** — is this expected? Can we do better?

## Files Modified (Not Committed)

Currently clean — all changes were reverted. `memory/strategies.md` has new research
notes under "Sandbox Libraries & Compute Efficiency" section. This IS committed
implicitly via the earlier memory updates... actually wait, let me check.

**strategies.md changes are NOT committed** — the library research notes were added
after the last commit. Need to commit when ready.

## Context for Next Agent

- Start by reading `memory/memory.md` (index) then this file
- The notebook on Kaggle is working — v15 submitted, v18/v19 running tests
- Do NOT push code without disabling the GitHub Actions trigger first
- The user is in "research and understand" mode, not "implement" mode
- Key files: `notebooks/aimo3-solver.ipynb`, `baseline-44-50.ipynb`, `memory/strategies.md`
- Kaggle dataset `jxm222/aimo3-test-data` exists with test CSVs for cell-17
