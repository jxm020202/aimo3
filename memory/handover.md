# Handover Document — March 3, 2026 (Session 3)

## Where We Stopped

**v22 pushed to Kaggle.** Running now. v21 scored 49/50 (98%). v22 applies 4 improvements.

## Current Kaggle State

- **v15**: Submitted to competition → **scored 38/50** (broken extraction, no `break`)
- **v21**: Test run complete → **49/50** (98%). Breakdown:
  - Reference: 9/10 (P4 86e8e5 wrong — same failure as v19)
  - Hard diagnostic: 10/10
  - Random: 10/10
  - Comprehensive: 20/20
  - Total time: 63.8 min (well under 5h limit)
- **v22**: Pushed, running. Changes below.

## v22 Changes (from v21)

| Change | Cell | What |
|--------|------|------|
| early_stop 4→3 | 8 | Faster convergence on easy problems, saves budget for hard ones |
| temp_schedule | 8 | `[0.3, 0.4, 0.5, 0.5, 0.6, 0.7, 0.8, 0.9]` per attempt |
| Per-attempt temperature | 13 | `_process_attempt` accepts `temperature` param, used in completions.create |
| Retry on None | 13 | If all 8 attempts return None, retry with +0.2 temp and remaining budget |
| Hard benchmark Level 2 | 17 | Replaced hand-picked 10 with 10 random from 28 IMO-AnswerBench problems |
| hard_benchmark_30.csv | dataset | Uploaded to `jxm222/aimo3-test-data` (28 problems, 7/domain) |

## The One Failure: 86e8e5

**Problem**: Norwegian numbers with M=3^{2025!}. Requires finding smallest divisors of `3^{2025!} + d` for various d values.

**What happened in v21**: Attempt 2 got correct answer (8687) but lost vote to 41754 (2 votes vs 1). All 8 attempts produced wildly different answers. The model's math is correct but it runs out of compute searching for divisors.

**v22 might help**: Temperature diversity could let one low-temp attempt converge more reliably. Retry on None helps if the problem is extraction failure, not wrong answer.

## v21 Changes (from baseline, still in v22)

| Change | Cell | What |
|--------|------|------|
| Answer extraction | 13 | **Restored to baseline** (32-chunk window + break) |
| Efficiency prompt | 8 | Don't overthink trivial problems |
| Code Robustness Rules | 8 | Self-contained cells, sympy bloat guard, geometry→numpy |
| Bigint hint | 8 | `pow(base, exp, mod)` for large exponents |
| jupyter_timeout 6→30 | 8 | Let brute-force approaches finish |
| Sandbox preloads | 11 | +functools, +fractions |
| TEST_LEVEL=4 | 17 | 10 ref + 10 hard(IMO) + 10 random + remaining comprehensive |
| TeeLogger | 17 | Persistent diagnostic.log |

## Important Files

| File | Purpose |
|------|---------|
| `output/v21/diagnostic.log` | Full v21 run logs (167K lines, 10MB) |
| `output/v21/submission.parquet` | v21 test submission |
| `data/discussions/competitive_intel.md` | Competition intelligence summary |
| `data/hard_benchmark_30.csv` | 28 IMO-level problems (7/domain) for harder testing |
| `notebooks/aimo3-solver.ipynb` | Active solver |
| `baseline-44-50.ipynb` | Original baseline (read-only reference) |

## Context for Next Agent

- Read `memory/memory.md` first, then this file
- v21 output at `output/v21/` — already pulled
- v22 is running on Kaggle — check with `kaggle kernels status jxm222/aimo3-solver`
- Pull v22 output: `kaggle kernels output jxm222/aimo3-solver -p output/v22/`
- GitHub Actions auto-push DISABLED (workflow_dispatch). Safe to push.
