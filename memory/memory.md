# AIMO3 Memory Index

> **Read this file first.** It contains essential context and points to detailed files. Don't load detail files unless you need them for your current task.

## Update Rules

- **Update memory files when**: you learn something new that future agents need (new technique, failed experiment, config change, insight)
- **Update at ~80% context compaction**: before you lose context, dump everything the next agent needs into the relevant memory file. This is CRITICAL — don't let knowledge die with your context.
- **Update after major milestones**: successful submission, score change, new approach validated/invalidated
- **Update tools.md when**: you hit an error using a tool/command, discover a new useful command, or learn something about the environment. Future agents shouldn't repeat your mistakes.
- **Don't duplicate**: check if info already exists before writing. Update existing entries instead.
- **Keep memory.md under 200 lines**: move details to topic files, keep only references here
- **New agents**: Read ONLY memory.md first. Load topic files only when relevant to your task.
- **Before any big change**: re-read `tools.md` to know what's available and avoid reinventing.

## HARD RULE: Log Analysis via Query Scripts

**ALWAYS use `log_exploration/` scripts for log extraction. NEVER grep/awk/sed raw diagnostic logs.**

1. Check `log_exploration/README.md` for existing scripts (35+ scripts)
2. If script exists → `python3 log_exploration/<script>.py output/<version>/diagnostic.log`
3. If no script exists → write a new one in `log_exploration/`, import `from log_exploration.log_query import parse_log`, then run it
4. Core parser returns `list[Problem]` with `.attempts[].turns[]` — structured data, not text matching
5. Parser now includes Wave 1 fields: `wave1_taxonomies`, `wave1_votes`, `wave1_time`, etc.

## User Preferences

- **NO GPG signing for this repo** — personal account (jxm020202), NOT WeMoney
- **GitHub Actions auto-deploy DISABLED** — `workflow_dispatch` (manual only). Safe to push.
- Voice input: messages prefixed with `[voice]` are speech-to-text, expect transcription errors
- User prefers concise communication, doesn't want hand-holding
- User has CAT 99.63 percentile — strong math intuition, don't underestimate domain knowledge

## Quick Context

- **Competition**: AIMO Progress Prize 3 — solve 110 original math problems (olympiad to IMO level)
- **Prize**: $2.2M total. 1st: $262K. 47/50 bonus: $1.59M (never claimed).
- **Deadline**: April 15, 2026 (entry by April 8). ~5 weeks from March 6, 2026.
- **Hardware**: Free H100 GPUs on Kaggle. No internet during submission.
- **Answers**: 5-digit integers (0-99999). 50 public + 50 private problems.
- **Scoring**: Double-run. Both correct=1, one=0.5, both wrong=0.
- **1 submission/day**. Model cutoff March 15, 2026.
- **Kaggle**: shivzzzzzz02 (primary), jxm222 (DB dataset) | **GitHub**: jxm020202/aimo3 (private)

## Current State (March 6, 2026 — Session 12)

- **v18 pushed but FAILED**: Loaded `test_2problems.csv` instead of `test_problems.csv`. Fixed locally, need v19 push.
- **v34 (jxm222)**: 24/50 (48%) — last version without Wave 1
- **v17**: 42/50 (84%) — first Wave 1 run (but old config: 24 attempts)
- **Current config**: 32 Wave 2 attempts, 42 Wave 1 agents, 398-problem test set
- **Problem DB**: 340 entries, pushed as v10 to `jxm222/aimo3-problem-db`
- **Test data**: 398 problems (val+aux+hard30), all valid 0-99999

## Critical Insights

1. **Competition is about variance reduction, not capability** — host data: pass@100 ~50/50. With TIR, baseline gets 44/50 at pass@8.
2. **GPT-OSS-120B is MoE with ~5.1B active params** — "120B" is misleading.
3. **Early stop is BROKEN and REMOVED** — All attempts launch simultaneously. ES saves ZERO time. See `memory/ideas/parallelism-and-early-stop.md`.
4. **NameErrors from missing aliases** — 22% of all errors. Fixed in v36 by adding np/sp/random/time/nx to sandbox init+reset.
5. **Wave 1 classification is very accurate** — 83-95% of agents pick correct taxonomy in v18 test.
6. **DB notes dramatically help trap problems** — centroid/735-gon got 32/32 correct with notes (was 0/16 without).
7. **Deadline overshoot up to 30s** — effective max per problem is ~430s not 400s.
8. **All attempts fully parallel** — 42 Wave 1 + 32 Wave 2 all run concurrently, GPU handles it fine.

## Memory Files — What's Where

| File | Contains | Read when... |
|------|----------|-------------|
| `handover.md` | **START HERE for new sessions.** Where we stopped, what changed, next steps | Starting a new session |
| `problem-db-guide.md` | **How to add entries to Problem DB** — schema, Python snippet, push instructions | Adding DB entries |
| `competition.md` | Rules, constraints, submission format, evaluation, prizes, timeline | Setting up submissions, checking rules |
| `models.md` | Model landscape, benchmarks, what fits on H100 | Choosing/switching models |
| `solutions.md` | Analyzed solutions — baseline 44/50, Numina, NemoSkills, underdogs | Understanding what's been tried |
| `history.md` | Past AIMO1/2 results, leaderboards, patterns | Competition dynamics |
| `tools.md` | **CLI commands, Kaggle API, discussion scraping, workflow, gotchas** | Before any push/deploy/CLI work |
| `reference_problems.md` | 10 reference problems with answers, difficulty, model scores | Testing, validating approaches |
| `changelog.md` | Every change to the project, most recent first | What's been done, avoiding duplicates |
| `changelog-vs-baseline.md` | **Exhaustive diff** of notebook vs baseline-44-50.ipynb | Understanding exactly what's changed |

### Ideas & Strategy (in `memory/ideas/`)
| File | Key Content |
|------|-------------|
| `strategies.md` | Technique catalog, priority queue, what failed, research sources |
| `parallelism-and-early-stop.md` | Early stop is broken, KV cache math, adaptive batching |

### Kaggle Discussion Summaries (in `memory/discussions/`)
| File | Key Insight |
|------|-------------|
| `pass-at-100.md` | Host data: pass@100 ~50/50. More attempts = more points. |
| `runtime-and-scoring.md` | 5hr/run, dual run sequential (10hr total), 236 min headroom |
| `competitive-intel.md` | SymPy decoupling, MoE architecture, ref set unreliable |

### Log Exploration Toolkit (in `log_exploration/`)
**35+ scripts** for querying diagnostic.log as structured data. See `log_exploration/README.md` for full list.
Core parser: `log_exploration/log_query.py` — includes Wave 1 parsing + 30 built-in queries.

### Available Logs
| Version | Location | Problems | Score |
|---------|----------|----------|-------|
| v32-v34 | `output/v32/` etc | 50 | 24/50 (v34) |
| shiv-v1 to v15 | `output/shiv-v*/` | varies | varies |

## Project Structure

```
aimo3/
├── memory/              ← You are here. Start with memory.md → handover.md
├── baseline-44-50.ipynb ← Original 44/50 notebook (READ-ONLY reference)
├── notebooks/           ← Our working notebooks (pushed to Kaggle)
│   ├── aimo3-solver.ipynb    ← Active solver
│   └── kernel-metadata.json  ← Kaggle kernel config
├── data/
│   ├── active/          ← test_problems.csv (398), test_answers.csv (398)
│   ├── problem_db/      ← problems.db (340 entries, working copy)
│   ├── problem_db_upload/ ← problems.db (upload copy for Kaggle)
│   └── available/       ← val bench, old benchmarks, discussions
├── log_exploration/     ← 35+ script log query toolkit
├── scripts/             ← nb.py, db_view.py, parse_diagnostics.py
├── output/              ← Kaggle run outputs
└── CLAUDE.md            ← Project config
```

## Kaggle Datasets

- `jxm222/aimo3-problem-db` — Problem DB (340 entries, public). Push with jxm222 creds.
- `shivzzzzzz02/aimo3-test-data` — Test CSVs (398 problems+answers, private).
- Both in `kernel-metadata.json` dataset_sources
