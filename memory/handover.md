# Handover Document — March 3, 2026 (Session 3, updated late)

## Where We Stopped

**Deep diagnostics session.** Analyzed v21 run (49/50), built error/None analysis tooling, discovered pass@100 data from host, confirmed dual-run = 10hr total budget. No code changes — research only session.

## Current Kaggle State

- **v15**: Submitted to competition → **scored 38/50** (broken extraction, no `break`)
- **v21**: Test run complete → **49/50** (98%). Breakdown:
  - Reference: 9/10 (P4 86e8e5 wrong — same failure as v19)
  - Hard diagnostic: 10/10
  - Random: 10/10
  - Comprehensive: 20/20
  - Total time: 63.8 min (well under 5h limit)
- **v22**: Pushed, running. Changes: early_stop 4→3, temp_schedule, retry on None, hard benchmark level 2.

## Key Discoveries This Session

### 1. Pass@100 Data (game-changer)
Host Simon Frieder posted in [#679559]: GPT-OSS-120B at pass@100 solves **~50/50** on both public AND private sets. Without TIR, without fine-tuning.
- pass@1: ~27, pass@5: ~40, pass@20: ~47, pass@100: ~50
- **More attempts = more points.** Going 8→16 is the highest-leverage change.
- Full analysis: `memory/discussions/pass-at-100.md`

### 2. Dual Run = 10 Hours Total
Each scoring run is a completely independent 5hr container. Sequential, not parallel.
- Our v21 used 64 min → **236 min headroom per run**
- Can safely double or triple compute per problem
- Full analysis: `memory/discussions/runtime-and-scoring.md`

### 3. Error Patterns (120 errors in v21)
- **#1 cause (38%)**: Cross-cell NameError — model loses function definitions when cells error
- **#2 cause (25%)**: Sympy/Python type mixing — `pow(int, Zero, int)`, None propagation
- **#3 cause (17%)**: Hallucinated APIs — `sympy.crt`, `mp.matrix.dot`, `print(simple=...)`
- High-error problems average 330s vs 29s for clean → **11.5x time penalty**
- Full analysis: `diagnostics/v21/error_analysis.md` and `error_patterns.md`

### 4. None Rate Analysis (44.5% of attempts)
- 178/400 attempts return NO ANSWER — ALL are real failures (not early-stop artifacts)
- Top reasons: token_light (43%), final_answer_text without boxed (22%), ran_code_ok but no extraction (13%)
- 12 attempts had `\boxed{}` in text but extraction failed — extraction bugs
- Full analysis: `diagnostics/v21/none_analysis.json`

## Diagnostics & Analysis Files

| Location | What |
|----------|------|
| `diagnostics/v21/diagnostic.log` | Full 167K line run log |
| `diagnostics/v21/analysis_report.txt` | Struggle scores: 1 FAILED, 3 HARD, 10 MODERATE, 36 CLEAN |
| `diagnostics/v21/error_analysis.md` | Root cause taxonomy (120 errors, 5 categories) |
| `diagnostics/v21/error_patterns.md` | Deep patterns: function names, cascades, time impact |
| `diagnostics/v21/none_analysis.json` | None classification data |
| `diagnostics/v21/all_problems.json` | Structured data for all 50 problems |
| `scripts/parse_diagnostics.py` | Parse diagnostic.log → struggle analysis |
| `scripts/analyze_errors.py` | Extract tracebacks → root cause taxonomy |
| `scripts/analyze_nones.py` | Classify NO ANSWER attempts |
| `memory/discussions/` | Tagged discussion summaries (pass@100, runtime, intel) |

## Quick Grep Patterns for diagnostic.log

```bash
grep -E 'Predicted:.*Expected:' diagnostics/v21/diagnostic.log  # One line per problem
grep -E '\*\*\* WRONG' diagnostics/v21/diagnostic.log           # Wrong answers
grep 'ATTEMPT.*<<' diagnostics/v21/diagnostic.log               # All attempt lines
grep -E 'Score:|Total time:' diagnostics/v21/diagnostic.log     # Tier summaries
grep -E 'FINAL SUMMARY' -A3 diagnostics/v21/diagnostic.log     # Final score
```

## The One Failure: 86e8e5

**Problem**: Norwegian numbers with M=3^{2025!}. Find smallest divisors of `3^{2025!} + d`.
**What happened**: Attempt 2 got correct (8687) but lost vote 2:1 to 41754. All 8 attempts produced wildly different answers. 16 errors, 225 code calls, 460s wall time.
**Error patterns**: `pow(int, Zero, int)` 3x, `sympy.crt` wrong import 2x, bigint 4300-digit limit 2x.

## Immediate Next Steps (for v23)

1. **Increase attempts 8→16** — biggest leverage from pass@100 data. Time budget allows it.
2. **Fix None rate** — 44.5% wasted. Top targets:
   - Prompt model harder to use `\boxed{}`
   - Improve extraction for "final answer is X" patterns
   - Handle boxed extraction failures (12 cases had `\boxed{}` but weren't extracted)
3. **Fix error cascades** — preload more in sandbox, add `import sympy as sp` to kernel init
4. **Submit v22 to competition** if it looks good (currently our best would be v21 at 49/50 test)

## Context for Next Agent

- Read `memory/memory.md` first, then this file
- v21 output at `output/v21/` and `diagnostics/v21/`
- v22 running on Kaggle — check: `kaggle kernels status jxm222/aimo3-solver`
- Pull v22 output: `kaggle kernels output jxm222/aimo3-solver -p output/v22/`
- GitHub Actions auto-push DISABLED (workflow_dispatch). Safe to push.
- Analysis scripts in `scripts/` — run against `output/v21/diagnostic.log`
