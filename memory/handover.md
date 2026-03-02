# Handover Document — March 2, 2026 (Session 2)

## Where We Stopped

v21 pushed to Kaggle. All prompt improvements applied, answer extraction restored to baseline behavior. Waiting for v21 test run results (~5 hours).

## Current Kaggle State

- **v15**: Submitted to competition → **scored 38/50** (double-run scoring)
- **v20**: Test run complete → **19/20** (9/10 ref + 10/10 fixed). Ran with early_stop=4 but old extraction.
- **v21**: Just pushed. Has all improvements below. Running TEST_LEVEL=4 (~50 problems + double-run retry).

## Root Cause: Why v15 Scored 38 (not 44)

The baseline has `break` in answer extraction. We removed it. This was the killer:

**Baseline (44/50):** When `\boxed{N}` is found during streaming, `break` stops generation immediately. The 32-chunk search window never matters because the answer is always in the latest chunk.

**Our v15 (38/50):** No `break` → model keeps generating "let me verify..." → 200+ more tokens → later `}` triggers rescan of last 32 chunks → `\boxed{N}` has scrolled out → returns None. Combined with `early_stop=5` (need 5/8 to agree, but only ~5 produce answers) → fragile voting → 38/50.

**v21 fix:** Restored baseline exact: `text_chunks[-self.cfg.search_tokens:]` + `break`. Proven at 44/50.

## v21 Changes (All Additive Over Baseline)

| Change | Cell | What |
|--------|------|------|
| Answer extraction | 13 | **Restored to baseline** (32-chunk window + break) |
| early_stop = 4 | 8 | **Matches baseline** |
| Efficiency prompt | 8 | Don't overthink trivial problems (saves tokens on easy Qs) |
| Code Robustness Rules | 8 | Self-contained cells, sympy bloat guard, geometry→numpy, dedup |
| Bigint hint | 8 | `pow(base, exp, mod)` for large exponents |
| jupyter_timeout 6→30 | 8 | Let brute-force approaches finish |
| Sandbox preloads | 11 | +functools, +fractions |
| TEST_LEVEL=4 | 17 | All tiers: 10 ref + 10 hard diagnostic + 10 random + ~23 comprehensive |
| TeeLogger | 17 | Persistent `/kaggle/working/diagnostic.log` |
| Hard FIXED_10_IDS | 17 | 1 easy, 1 medium, 8 hard across diverse domains |
| Double-run retry | 17 | Re-runs failures, simulates competition double-run scoring |

## Key Insights from This Session

1. **`break` in extraction is critical** — without it, the 32-chunk window bug fires and 41% of attempts return None
2. **Pass@n graph from competition organizers**: Model B (GPT-OSS-120B) at pass@8 ≈ 43-44, pass@20 ≈ 47-48, pass@100 ≈ 49-50. Almost every problem is solvable — it's a consistency/variance game.
3. **Double-run scoring** doesn't change expected score (E[double] = E[single]) but increases variance. Non-determinism hurts.
4. **GPU is near-optimal**: vLLM handles ~6 concurrent full-context requests on H100. 8 parallel attempts, 2 queue. No gains from more threading.
5. **Competition deadline**: April 15, 2026 (entry by April 8). Model cutoff March 15.

## What to Do Next

1. **Wait for v21 results** — should take ~5 hours
2. **If score >= 44**: Submit to competition, then work on prompt improvements for 47+
3. **If score < 44**: Something else is wrong. Compare v21 logs against baseline carefully.
4. **Deferred improvements** (wait for v21 data):
   - Post-hoc adjudication for fragmented votes (only if P4-like failures persist)
   - Agent specialization (too risky until baseline score recovered)
   - Adaptive spawning (premature optimization)

## Context for Next Agent

- Read `memory/memory.md` first, then this file
- v21 is on Kaggle running now — check with `kaggle kernels status jxm222/aimo3-solver`
- Pull results: `kaggle kernels output jxm222/aimo3-solver -p output/`
- GitHub Actions auto-push DISABLED (workflow_dispatch). Safe to push.
- Key files: `notebooks/aimo3-solver.ipynb`, `baseline-44-50.ipynb`, `prompts.md`
