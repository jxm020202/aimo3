# Handover Document — March 4, 2026 (Session 7)

## Where We Stopped

**v31 completed with 38/53 (72%).** Deep analysis done. Time awareness + exam bell implemented. Vboxed analysis complete. Ready for v32 push.

## Current Kaggle State

- **v15**: Submitted to competition → **scored 38/50** (broken extraction, no `break`)
- **v21**: Test run → **49/50** (8 attempts, ES=4, temp=0.5, 50 problems, 63.8 min)
- **v22**: Test run → **58/60** (8 attempts, ES=3, temp=0.5, 60 problems)
- **v23**: OOM during nbconvert (80MB notebook). 63/80 correct (78.8%), 313 min.
- **v30**: TEST_TIER=-1 (submission only). Failed — likely OOM from HiGHS output flooding.
- **v31**: TEST_TIER=2 (full test). **38/53 (72%)** — completed all 53 problems, OOM during nbconvert.
  - Tier 2 (val bench): 34/35 (97%)
  - Tier 1 (previous failures): 2/14 (14%)
  - Tier 0.5 (historical hard): 3/16 (19%)
  - Output: `output/v31/diagnostic.log` (41MB), submission.parquet

## Changes Applied Since v31 (for v32)

### New This Session

#### Time Awareness — Exam Bell (cell 13)
- **`_DEADLINE` variable** injected into each attempt's sandbox: `sandbox.execute(f'import time as _time; _DEADLINE = {deadline}')`
- **Exam bell** — automatic time warnings appended to tool (code execution) responses:
  - `<100s remaining`: checkpoint warning — "Checkpoint your best answer with \Vboxed{N} now"
  - `<30s remaining`: urgent warning — "Write \Vboxed{YOUR_ANSWER} immediately. No new computations."
- **System prompt** (cell 8) now has `# Time Management` section explaining _DEADLINE and the automatic warnings
- Bell fires on every code execution result. Model sees it passively like an exam proctor.
- If model doesn't call code, it still has `_DEADLINE` from system prompt + its own awareness of time.

#### Timeout Simplification (cell 8 + cell 13)
- Removed `high_problem_timeout` / `base_problem_timeout` dual config
- Single `problem_timeout = 900`
- Budget = `time_left / problems_remaining`, capped at `problem_timeout`, floor at 60s

#### Bug Fix: `consecutive_errors` (cell 13)
- Variable was used without initialization → now initialized to 0 before turn loop

#### Removed: `early_stop` (cell 13)
- Removed broken `early_stop` reference in `solve_problem`. Early stop was proven non-functional (all 16 attempts launch simultaneously, stop_event fires too late).

### From Previous Sessions (still applied)

#### Prompt Changes (cell 8)
- **Temp schedule**: `[0.3×8, 0.5×8]` — data shows +3 problems over old `[0.1, 0.3×5, 0.5×6, 0.7×4]`
- **Strategic rules** (from timeout analysis of 1,528 timeouts):
  - Estimate complexity before coding (>10^6 ops → find shortcut)
  - Don't reduce-and-retry after timeout → find closed-form/recurrence/DP
  - 3+ timeouts in first 5 cells → stop coding, reason mathematically
- **Code robustness rules**:
  - sympy.solve() timeout guard (31.5% timeout rate)
  - sympy.simplify()/expand() guard for large expressions

#### Bug Fixes (cells 11-15)
- `store_history=False` in sandbox — prevents IPython In[]/Out[] memory leak
- `_ensure_last_print` — skip wrapping assignments, control flow, decorators
- Code fence stripping — strips ````python` wrappers before execution
- Output cap at 8K chars — prevents HiGHS MILP output from causing OOM
- `math.pow()` → `**` operator (avoids float precision loss)
- NaN/Inf entropy guard
- Fallback scan includes `code` key
- Sandbox pool depletion fix — replace dead sandboxes
- Stop reason logging (7 reasons tracked per attempt)

## V31 Deep Analysis — Key Findings

### Vboxed Analysis (new this session)
- 91 \Vboxed uses across 848 attempts (10.7% of attempts)
- Vboxed attempts are **79.7% correct** vs 67.0% non-Vboxed
- Only 13/848 attempts use Vboxed as FINAL answer source (61.5% accuracy)
- Weight sweep: keep 0.7 (changing it gains/loses net zero)
- dbbfe8 (T0): 3 Vboxed attempts had correct answer but were outvoted

### Time Distribution (new this session)
- Correct P50=132s, Wrong P50=190s, None P50=331s
- Score peaks at 660s timeout cap (37/53), actually drops at 900s
- T2 plateaus at 240s (35/37) — easy problems solved fast
- T0/T0.5/T1 get 0-1/19 at ALL timeouts — timeout doesn't matter for hard problems
- New script: `log_exploration/time_distribution.py`

### Previous Analysis
- Reduce attempts 16 → 6-8 (peak at N=6)
- Speed = accuracy: <60s → 84%, >300s → 19%
- Geometry weakest topic (46.7%)
- Extraction failures are NOT the problem (84% of Nones are timeouts)

## Tier System

Use these labels — NOT "hard/easy":
- **T0**: dbbfe8, 3b88b3 (known hard, from reference problems)
- **T0.5**: 86e8e5 (historical hard)
- **T1**: V31_WRONG_IDS + TIER_15_IDS + DODGY_WIN_IDS - T0 - T0.5 (defined in cell 17)
- **T2**: everything else (consistently solved)

Group for analysis: T0/T0.5/T1 together vs T2 alone.

## User's Mentality

**Aiming for 50/50** — all correct. Time savings exist purely to fund Wave 2 attempts on unsolved problems. The plan is 1-16-1-16 wave architecture.

## Notebook Editing Helper

Created `scripts/nb.py` for reliable notebook cell editing:
```bash
python3 scripts/nb.py list              # Show all cells
python3 scripts/nb.py read CELL_INDEX   # Print cell to stdout
python3 scripts/nb.py write CELL_INDEX FILE  # Replace cell from file
python3 scripts/nb.py diff CELL_INDEX FILE   # Diff current vs file
```

## Open Decisions for Next Session

1. **Reduce attempts 16 → 8?** Data strongly supports it but not yet applied.
2. **Wave architecture**: Run 16 attempts, then re-run failed problems with different prompts/temps.
3. **Push v32?** All changes ready — need user approval for Kaggle push.

## Diagnostics & Analysis Files

| Location | What |
|----------|------|
| `output/v31/` | Full v31 output (diagnostic.log 41MB, gpu_metrics, submission.parquet) |
| `log_exploration/` | 35+ query scripts (see README.md) |
| `log_exploration/vboxed_deep_analysis.py` | Vboxed checkpoint usage analysis |
| `log_exploration/time_distribution.py` | Time distributions, optimal timeout, per-topic/tier |
| `scripts/nb.py` | Notebook cell read/write/diff helper |

## Hard Rules

- **NEVER push to Kaggle without explicit user approval**
- **NO GPG signing** — personal account, not WeMoney
- **GitHub Actions auto-deploy DISABLED** (workflow_dispatch). Safe to git push.

## Context for Next Agent

- Read `memory/memory.md` first, then this file
- Full baseline diff: `memory/changelog-vs-baseline.md`
- v31 results in `output/v31/`
- Use `scripts/nb.py` for notebook editing (extract → edit → write back)
