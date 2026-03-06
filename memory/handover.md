# Handover Document — March 6, 2026 (Session 11)

## Where We Stopped

**v17 pushed and running.** Full 50-problem run with Wave 1 classification + Wave 2 solving. No hardcoded problems — loads from test CSV, shuffles with seed=42, takes first 50.

## Current Kaggle State

- **v15 (Kaggle v15)**: FileNotFoundError — test CSV was on jxm222, kernel on shivzzzzzz02
- **v16**: Same error (dataset created but not yet available)
- **v17**: Running — first full Wave 1 + Wave 2 run on 50 random problems
- Previous baselines: v34 scored 24/50 (48%) on 50 problems without Wave 1

## Architecture: Wave 1 + Wave 2

### Wave 1: Classification (cell 14: `classify_problem()`)
- 24 parallel attempts, temp 0.1, 100s timeout, ReasoningEffort HIGH
- Model sees full taxonomy tree (264 entries, ~106K chars) as MCQ options
- Multi-turn flow: `\Vboxed{taxonomy}` → host injects DB entry → `\boxed{taxonomy : id}` confirms
- 1-4 picks allowed per attempt
- Voting: any taxonomy with >50% of attempts (confidence-weighted) gets selected
- No consensus → injects warning: "expert could not classify, be careful"
- `basic.basic.basic` → injects "quick solve, save time for tough questions"

### Wave 2: Solving (cell 14: `solve_problem()`)
- 24 parallel attempts, temp schedule [0.1→0.7], 400s timeout
- Notes from Wave 1 selected taxonomies prepended to problem text
- Rerun logic: if top votes < threshold, reruns all 24 attempts
- Entropy-weighted voting for final answer

## Key Files Modified This Session

### Cell 8 (CFG)
- `wave1_temperature = 0.1`
- `wave1_system_prompt`: MCQ framing, 1-4 picks, `\Vboxed` then `\boxed{taxonomy : id}` verification
- Added: "If very easy, pick basic.basic.basic"

### Cell 9 (ProblemDB)
- `get_taxonomy_tree()`: returns all taxonomies with triggers + full technique text
- `format_notes()`: header "Our IMO expert has given tips and tricks", footer with DB query instructions
- Schema uses `id` (not `problem_id`)

### Cell 11 (AIMO3Template)
- `apply_classifier_template()`: ReasoningEffort.HIGH, no developer message, no tools
- `DB_INSTRUCTIONS`: simplified to "read expert notes if present"

### Cell 14 (AIMO3Solver)
- `_scan_for_taxonomy()`: extracts taxonomy from `\boxed{tax : id}`, strips id suffix
- `_build_taxonomy_injection()`: Vbox → queries DB → shows entry with id → confirm prompt
- `_select_taxonomy()`: confidence-weighted votes, 50% absolute threshold
- `_process_classification_attempt()`: 6 max turns, no code execution, handles python tool rejection
- `solve_problem()`: Wave 1 → basic detection → DB retrieval → Wave 2
- Basic handling: `basic.basic.basic` always prepends "quick solve" message, even with other taxonomies

### Cell 18 (Test Framework)
- No tiers, no hardcoded problems
- Loads all from `/kaggle/input/aimo3-test-data/test_problems.csv` + `test_answers.csv`
- Shuffles seed=42, takes first 50
- fd-level TeeLogger to prevent Kaggle UI log leakage

### Problem DB
- 264 entries (was 160 in v34 → grew via bulk import sessions)
- Schema: `id, category, topic, subtopic, taxonomy, triggers, technique, question, answer`
- Column renamed from `problem_id` to `id` (done multiple times, keeps reverting on credential swap)
- Added `basic.basic.basic` entry for easy problems
- 4 duplicate taxonomies (am_gm, crt, fermat, sum_of_divisors) — both entries get injected, harmless
- Pushed as v9 to `jxm222/aimo3-problem-db`

### Kernel Metadata
- `dataset_sources`: changed `jxm222/aimo3-test-data` → `shivzzzzzz02/aimo3-test-data`
- Test data uploaded under shivzzzzzz02 account (was private to jxm222)

### Simulation Script
- `log_exploration/wave1_simulation.py` fully updated to match current code
- New commands: `--tree`, `--wave1 <pid>`, `--inject <taxonomy>`
- `--log`: now uses confidence-weighted voting with 50% threshold
- Verified against v13 and v14 logs

## Time Budget Analysis

v34 (no Wave 1) ran 50 problems in 220 min with 70 min headroom.
With Wave 1 at ~30-50s avg/problem: 245-262 min, 28-45 min headroom. No budget squeezing.
Current config is safe for 50 problems. Bug #6 (Wave 1 not in reserve) doesn't cause actual issues.

## Tested Problems Tracking

All tested problems tracked in `data/fixed.txt` — 18 problems across v10-v14.

## Notebook Editing

```bash
python3 scripts/nb.py list              # 19 cells (0-18)
python3 scripts/nb.py read CELL > /tmp/cell.py
python3 scripts/nb.py write CELL /tmp/cell.py
```

## Kaggle Accounts

- Kernel: `shivzzzzzz02/aimo3-solver`
- DB dataset: `jxm222/aimo3-problem-db` (public)
- Test data: `shivzzzzzz02/aimo3-test-data` (private)
- DB pushes use jxm222 credentials (swap before/after)

## Hard Rules

- **NEVER push to Kaggle without explicit user approval**
- **NO GPG signing** — personal account, not WeMoney
- **GitHub Actions auto-deploy DISABLED** (workflow_dispatch). Safe to git push.
