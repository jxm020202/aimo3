# Handover Document — March 4, 2026 (Session 9)

## Where We Stopped

**v33 ready for push.** Problem DB complete — all 35 problems have rich summaries (avg 290 chars) and approaches (avg 688 chars), including deep log-extracted fixes for all 15 v32 wrong problems. Model queries DB directly via Python tool (no pre-fetch class). Rerun logic added for low-confidence votes.

## Current Kaggle State

- **v15**: Submitted → **38/50** (broken extraction)
- **v21**: Test → **49/50** (8 attempts, ES=4)
- **v22**: Test → **58/60** (8 attempts, ES=3)
- **v23**: **63/80 (78.8%)**, 313 min, OOM during nbconvert
- **v31**: **38/53 (72%)**, 300 min, OOM during nbconvert
- **v32**: **38/54 (70.4%)**, 220 min. T2=35/35 (100%), T1=2/15, T0=1/2, T0.5=0/2
  - GAINED: dbbfe8. LOST: 89c921 (regression, close vote 5-4)
  - Errors halved, None rate halved, 27% faster, no OOM
  - Optimal at 6 attempts — 10 of 16 add nothing

## v33 Changes (This Session)

### Problem Knowledge Database — Model Queries Directly
- **No ProblemDB class** — removed pre-fetch. Model queries SQLite DB itself via Python tool
- **System prompt** tells model: "open-book exam, scan technique_summaries before solving"
- **Schema**: `problems(problem_id, category, topics, technique_summary, question, approach, expected_answer)`
- **35 problems** with rich summaries (avg 290 chars) and approaches (avg 688 chars)
  - All 15 v32 wrong problems have detailed log-extracted approaches
  - 6 PARTIAL entries improved with deep v32 log analysis (root cause + fix for each)
  - All summaries describe: what the problem tests, the common trap, the correct approach
- **DB files**: `data/problem_db/problems.db` (144KB), `data/problem_db_upload/` for Kaggle
- **Build**: `python3 scripts/build_sqlite_db.py` (reads unified.json + reextracted.json patches)
- **Upload**: `kaggle datasets create -p data/problem_db_upload/`

### Timeout & Budget Changes
- `problem_timeout`: 900 → 600
- `reserved_per_problem`: NEW, 100s (reserves time for future problems)
- Budget formula: `time_left - (remaining-1)*100`, capped at 600, floor at 100
- Removed old `max(budget, 60)` floor

### Low-Confidence Rerun
- After voting, if top_votes < 5 AND time permits (>30s), rerun all 16 attempts
- Merges original + rerun results and re-votes
- `_select_answer` now returns `(answer, top_votes)` tuple

### Cell Changes
- Cell 8 (CFG): DB prompt in system_prompt, `problem_timeout=600`, `reserved_per_problem=100`
- Cell 9: Simplified to comment (ProblemDB class removed)
- Cell 14 (AIMO3Solver): Removed ProblemDB init/hints, new budget formula, rerun logic

## v32 Wrong Problems Analysis

8 HINTABLE (DB should fix), 6 PARTIAL (DB helps but not enough), 1 UNHINTABLE (86e8e5):

| PID    | Pred  | Exp   | Rating    | Root Cause |
|--------|-------|-------|-----------|------------|
| 414a5b | 95    | 42    | HINTABLE  | Misinterprets "probability when n=2" |
| 673b29 | 3032  | 3     | HINTABLE  | Thinks need ALL gates, not just 2 |
| 29714f | 99    | 297   | HINTABLE  | Misses mod-3 constraint |
| 26bee3 | 97    | 108   | HINTABLE  | Counts 2 diags instead of 4 |
| 9010d9 | 6400  | 10320 | HINTABLE  | Symmetric pairing, misses core-leaf |
| 3980cd | 642   | 46    | HINTABLE  | Prime-root not binary construction |
| 89c921 | 39601 | 29800 | HINTABLE  | Misses odd/even parity decomposition |
| aff75c | 3658  | 3571  | HINTABLE  | Upper bound ≠ achievable minimum |
| 23586c | 773   | 386   | PARTIAL→FIXED | Divisor 105 not 210 (geometric factor of 2) |
| ae2add | 19945 | 24931 | PARTIAL   | Confuses budget with answer |
| a824c1 | 13    | 24    | PARTIAL→FIXED | Cell domination (13) vs diagonal coverage (24), Konig's theorem |
| 1ec970 | 9900  | 8700  | PARTIAL→FIXED | 5/16 output trivial 9900, need analytical arc coverage formula |
| 3b88b3 | 982   | 979   | PARTIAL→FIXED | Cone vs simplex constraint at k=1 (f(1)=2 vs f(1)=1) |
| a9dbc8 | 15743 | 15744 | PARTIAL→FIXED | Initial state encoding off-by-one, try both interpretations |
| 86e8e5 | varies| 8687  | UNHINTABLE→IMPROVED | Capability gap, but DB now has modular arithmetic guidance |

## Tier System

- **T0**: dbbfe8 (FIXED in v32!), 3b88b3
- **T0.5**: 86e8e5 (×2 runs)
- **T1**: wrong/dodgy problems from v31/v32
- **T2**: everything else (35/35 in v32)

## Before v33 Push

1. Upload Kaggle dataset: `kaggle datasets create -p data/problem_db_upload/`
2. Add dataset as notebook input in Kaggle UI
3. Push notebook: `kaggle kernels push -p notebooks/`

## Notebook Editing

```bash
python3 scripts/nb.py list              # 19 cells (0-18)
python3 scripts/nb.py read CELL > /tmp/cell.py
python3 scripts/nb.py write CELL /tmp/cell.py
```

## Hard Rules

- **NEVER push to Kaggle without explicit user approval**
- **NO GPG signing** — personal account, not WeMoney
- **GitHub Actions auto-deploy DISABLED** (workflow_dispatch). Safe to git push.
