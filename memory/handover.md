# Handover Document — March 3, 2026 (Session 4)

## Where We Stopped

**v23 pushed to Kaggle.** Major config changes, new test framework, improved extraction. Waiting for results.

## Current Kaggle State

- **v15**: Submitted to competition → **scored 38/50** (broken extraction, no `break`)
- **v21**: Test run → **49/50** (8 attempts, ES=4, temp=0.5 flat, 50 problems, 63.8 min)
- **v22**: Test run → **58/60** (8 attempts, ES=3, temp=0.5 flat, 60 problems). Two failures:
  - 86e8e5: Norwegian numbers. Predicted 23, expected 8687. Got correct 8687 twice but tied 2:2.
  - 76aef9: Game theory/cookies. Predicted 999, expected 8. Model can't solve (capability limit).
- **v23**: Just pushed → awaiting results. 16 attempts, ES=5, temp schedule, 80 problems.
  - Check: `kaggle kernels status jxm222/aimo3-solver`

## v23 Changes (vs baseline)

Full diff: `memory/changelog-vs-baseline.md`

### Config (cell 8)
- `attempts`: 8 → 16
- `early_stop`: 4 → 5
- `jupyter_timeout`: 6 → 30
- `temp_schedule`: NEW — `[0.1, 0.3×4, 0.5×6, 0.7×4, 0.9]` (bell curve centered on baseline 0.5)
- `model_path`: hardcoded → dynamic `find_model_path()`
- Prompt: added efficiency directive, 9 code robustness rules, bigint hint

### Solver (cell 13)
- Temperature schedule wired into attempt creation (was ignored before — always flat 0.5)
- Temperature logged per attempt in result dict
- GPU monitor: background thread polls vLLM /metrics every 5s → `gpu_metrics.log`
- Extraction: added fallback patterns — "the answer is X", "answer: X", "answer = X"
- Early-stop: collects ALL results (no break), more robust voting
- All-None retry: retries at +0.2 temp if first pass produces zero answers
- Vote tie-breaking: deterministic (score, votes, answer value)
- Full conversation logging (reasoning + code calls per turn)

### Sandbox (cell 11)
- Added `import functools` and `import fractions` to kernel init

### Test Framework (cell 17) — NEW CELL
- 3-tier system (replaces old 4-level TEST_LEVEL):
  - Tier 0: Priority Debug — 86e8e5 ×2, 76aef9 ×2 (dual-run simulation)
  - Tier 1: At-Risk — 6 problems with dodgy voting in v22
  - Tier 2: Val Bench — 70 new unseen BeyondAIME problems from CSV
- Quick-glance summary table (ID, status, predicted, expected, votes, errors, time, ES)
- Double-run retry with scoring simulation
- GPU metrics summary print
- TeeLogger for full diagnostic capture

### Data Restructure
- `data/active/` — test_problems.csv (70), test_answers.csv (70), reference.csv (10)
- `data/available/` — all old data organized (val bench, hard benchmark, old test sets, discussions, etc.)
- `scripts/build_test_v23.py` — reproducible test set builder

## v22 Analysis Results

### None Rate (the real picture)
- Raw: 280/480 = 58.3% — but 110 are early-stopped (by design)
- **Effective None rate: 170/370 = 45.9%** (same as v21's 44.5%)
- Token limit only 6.1% of Nones (was 43% in v21 — that was early-stop, not real)
- 32 attempts (18.8%) said "the answer is X" but extraction missed → **fixed in v23**
- 76 attempts (44.7%) had code errors → prompt hints should help

### Key Insight
The v21 "43% token limit" Nones were actually early-stopped attempts, not real failures. The real None rate has been ~46% consistently. The new extraction fallbacks target the 32 "answer is X" cases.

## Diagnostics & Analysis Files

| Location | What |
|----------|------|
| `diagnostics/v21/` | Full v21 analysis (167K log, error taxonomy, None analysis) |
| `diagnostics/v22/` | v22 diagnostic log + summary |
| `memory/changelog-vs-baseline.md` | Every change vs original baseline notebook |
| `scripts/build_test_v23.py` | Builds the 70-problem Val Bench test set |
| `scripts/parse_diagnostics.py` | Parse diagnostic.log → struggle analysis |
| `scripts/analyze_errors.py` | Extract tracebacks → root cause taxonomy |
| `scripts/analyze_nones.py` | Classify NO ANSWER attempts by reason |

## What to Look For in v23 Results

1. **Temperature analysis**: Each attempt logs `temp=X`. Check which temps produce correct answers.
   - If 0.5 dominates → narrow the schedule
   - If 0.9 cracks unique problems → widen it
2. **GPU metrics**: `gpu_metrics.log` tells if 16 attempts cause queuing
   - peak_waiting=0 → could go higher (20+)
   - waiting in <10% samples → 16 is near-optimal
   - waiting in >10% → drop to 12
3. **Extraction improvement**: Compare None rate to v22's 45.9%. The new fallbacks should reduce it.
4. **New problem failures**: 70 unseen BeyondAIME problems — expect some failures. These identify what to fix next.

## v24 Ideas

- **Adaptive batched execution**: Run attempts in waves of 4-6 instead of all 16 parallel. Real early stop between waves. See `memory/discussions/parallelism-and-early-stop.md` for full analysis — includes KV cache math, GPU constraints, proposed implementation.
- **Extraction further**: still ~45% None rate after fixes — code output parsing
- **Submit to competition**: v23 results should tell us if we're ready

## Hard Rules

- **NEVER push to Kaggle without explicit user approval**
- **NO GPG signing** — personal account, not WeMoney

## Context for Next Agent

- Read `memory/memory.md` first, then this file
- Full baseline diff: `memory/changelog-vs-baseline.md`
- v23 is running on Kaggle: `kaggle kernels status jxm222/aimo3-solver`
- GitHub Actions auto-push DISABLED (workflow_dispatch). Safe to push.
