# Handover Document — March 7, 2026 (Session 14)

## Where We Stopped

All changes applied to notebook. No pending /tmp edits. Notebook is the source of truth.

**Latest committed version**: v38 (git). Kaggle runs pending — 20B v1 errored (dataset path issue, now fixed), needs re-push.

## Notebook Structure

**Single notebook, auto-detects model at runtime.**

```
notebooks/aimo3-solver.ipynb   <-- EDIT THIS (source of truth)
push-20b/
  kernel-metadata.json          (mounts gpt-oss-20b)
  aimo3-solver.ipynb            (symlink -> ../notebooks/aimo3-solver.ipynb)
push-120b/
  kernel-metadata.json          (mounts gpt-oss-120b)
  aimo3-solver.ipynb            (symlink -> ../notebooks/aimo3-solver.ipynb)
```

**To push**: `kaggle kernels push -p push-20b/` or `kaggle kernels push -p push-120b/`
No copy step needed — symlinks auto-resolve. Never edit files in push dirs.

**To edit cells**: `python3 scripts/nb.py read CELL > /tmp/cell.py` → edit → `python3 scripts/nb.py write CELL /tmp/cell.py`
**To read full notebook**: `python3 scripts/read_nb.py`

## Key Notebook Cells

| Cell | What | Key features |
|------|------|-------------|
| 5 | `find_model_path()` | Auto-discovers any mounted model under `/kaggle/input/` |
| 8 | CFG | `_is_20b = '20b' in MODEL_PATH.lower()` — sets attempts/workers/temps. 72 for 20B, 24 for 120B |
| 11 | AIMO3Template | Chat template, reasoning effort support |
| 14 | AIMO3Solver | Main solver. Has `_build_cluster_summaries` for rerun context |
| 17 | Serve/Gateway | `run_local_gateway` for submission.parquet (dummy 3-question run) |
| 18 | Test framework | `TEST_SET = 'set_c'`, full diagnostic output to `/kaggle/working/diagnostic.log` |

## Recent Changes (This Session)

1. **Cluster summaries for reruns** (Cell 14): `_build_cluster_summaries()` adds per-answer-cluster approach/code/output to rerun context. Cross-cluster signal detection flags when an attempt computed another cluster's answer. Cap 1500 chars.
2. **submission.parquet restored** (Cell 17): `run_local_gateway` runs 3 dummy questions for Kaggle submission selection.
3. **20B auto-detection** (Cell 8): Single notebook adapts config based on mounted model.
4. **Push directory cleanup**: Symlinks instead of copies. Removed `notebooks/kernel-metadata.json` (was redundant). Removed `notebooks-20b/` dir.

## Kaggle State

- **Kernel 120B**: `jxm222/aimo3-solver` — last good run was v20 (44/50 on set_a)
- **Kernel 20B**: `jxm222/aimo3-solver-20b` — v1 errored, needs re-push
- **DB dataset**: `jxm222/aimo3-problem-db` (public, 374 entries, v12)
- **Test data**: `jxm222/aimo3-test-data` (has set_a/b/c/d)
- **All under `jxm222` account** (API key at `~/.kaggle/kaggle.json`)

## v20 Analysis (120B, set_a)

### Score: 44/50, 213 min
- 3 reruns triggered (27cec1, 67ec70, 19570e) — all correct after rerun
- 6 wrong: 76aef9, f7d683, 7302b5, 25e584, 4c5391, 517772
- All 6 had confident wrong majorities (not a Nones problem)
- 5/6 had correct answer in votes but outvoted

## Architecture: Wave 1 + Wave 2

### Wave 1: Classification (42 agents, MEDIUM effort)
- Budget from 6000s pool, skip if <=30s left
- Classifies taxonomy (MCQ from DB) + difficulty ([EASY]/[MEDIUM]/[HARD])

### Wave 2: Solving
- 120B: 24 agents, flat temp 0.5, timeout 450s
- 20B: 72 agents, flat temp 0.5, timeout 450s
- Rerun: 600s timeout, HIGH effort, cluster summaries in context
- Rerun triggers: `total_answered < ceil(attempts/3)` OR no-consensus

## Known Issues
1. **Difficulty classification gap** — model never votes HARD
2. **fp8 + prefix caching** — possibly incompatible, good results though
3. **Deadline overshoot** — up to 30s past problem_timeout
4. **Cross-cluster false positives** — regex `\b(\d{1,5})\b` matches digits inside floats. Low impact.

## Key Commands

```bash
python3 scripts/nb.py list                    # 19 cells (0-18)
python3 scripts/nb.py read CELL > /tmp/cell.py
python3 scripts/nb.py write CELL /tmp/cell.py
python3 scripts/read_nb.py                    # dump full notebook
kaggle kernels push -p push-20b/              # push 20B
kaggle kernels push -p push-120b/             # push 120B
kaggle kernels status jxm222/aimo3-solver-20b
kaggle kernels output jxm222/aimo3-solver-20b -p output/20b-v2
python3 log_exploration/simulate_run.py output/shiv-latest-4/diagnostic.log
```

## User Directive
"just focus on 20b notebook now ever ever touch 120b, you handle 20b, logs and maths"
