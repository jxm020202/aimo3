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

1. Check `log_exploration/README.md` for existing scripts (30 scripts covering errors, timing, voting, extraction, reasoning, etc.)
2. If script exists → `python3 log_exploration/<script>.py output/<version>/diagnostic.log`
3. If no script exists → write a new one in `log_exploration/`, import `from log_exploration.log_query import parse_log`, then run it
4. Core parser returns `list[Problem]` with `.attempts[].turns[]` — structured data, not text matching

## User Preferences

- **NO GPG signing for this repo** — personal account (jxm020202), NOT WeMoney. Never use `-S` flag or `git config user.signingkey`. GPG signing is ONLY for `~/Desktop/WeMoney/` repos.
- **DO NOT push to git without asking** — auto-push triggers Kaggle deploy (GitHub Actions)
- **GitHub Actions auto-push is NOW DISABLED** — changed to `workflow_dispatch` (manual only). Safe to push.
- Voice input: messages prefixed with `[voice]` are speech-to-text, expect transcription errors
- User prefers concise communication, doesn't want hand-holding
- User has CAT 99.63 percentile — strong math intuition, don't underestimate domain knowledge
- User is in **research mode** — no code changes until core issues are understood

## Research Tools

- **ChatGPT Research**: User has ChatGPT deep research mode. For broad surveys, suggest delegating there instead of spinning up 3+ Claude agents.
- **Claude agents**: Better for code search, file reading, codebase work, writing code.

## Quick Context

- **Competition**: AIMO Progress Prize 3 — solve 110 original math problems (olympiad to IMO level)
- **Prize**: $2.2M total. 1st: $262K. 47/50 bonus: $1.59M (never claimed).
- **Deadline**: April 15, 2026 (entry by April 8). ~6 weeks from March 2, 2026.
- **Hardware**: Free H100 GPUs on Kaggle. No internet during submission.
- **Answers**: 5-digit integers (0-99999). 50 public + 50 private problems.
- **Scoring**: Double-run. Both correct=1, one=0.5, both wrong=0.
- **1 submission/day**. Model cutoff March 15, 2026.
- **Kaggle**: jxm222 | **GitHub**: jxm020202/aimo3 (private)

## Current State (March 6, 2026 — Session 11)

- **v34**: 24/50 (48%) — last version without Wave 1. 50 problems, 220 min.
- **v17 running**: First full Wave 1 + Wave 2 run on 50 random problems.
- **Wave 1 architecture**: Classification (24 attempts, temp 0.1, MCQ taxonomy tree) → DB note injection → Wave 2 solving (24 attempts, temp schedule).
- **Problem DB**: 264 entries across 4 categories + basic.basic.basic fallback.
- **Full changelog**: `memory/changelog-vs-baseline.md` — every diff vs baseline
- **GitHub Actions auto-deploy DISABLED** (workflow_dispatch). Safe to push.

## Critical Insights

1. **Competition is about variance reduction, not capability** — host data: pass@100 ~50/50. With TIR, baseline gets 44/50 at pass@8. [thread #679559]
2. **GPT-OSS-120B is MoE with ~5.1B active params** — "120B" is misleading. Fits in 5 hours because sparse.
3. **`break` in answer extraction is critical** — without it, 41% None. Root cause of 38/50.
4. **Early stop is BROKEN and REMOVED** — All attempts launch simultaneously via ThreadPoolExecutor. stop_event.set() fires but all 16 are already mid-inference. Post-ES attempts take identical wall time. ES saves ZERO time. Removed from code entirely in v24. See `memory/ideas/parallelism-and-early-stop.md`. Waves also don't help (GPU has zero queuing, waves 2x slower).
5. **47% of Nones are extraction failures** — model had the answer, regex missed it. Biggest recoverable failure. [from log analysis]
6. **Wrong attempts have clear signature** — 3.4x longer reasoning, 45 restarts, 16 turns. Detectable early. [from log analysis]
7. **133 min wasted on errors** — "simplify" recovery = 100% success. Prompt: "simplify after error". [from log analysis]
8. **Budget utilization only 7.8%** — massive headroom for adaptive allocation.
9. **First 4 attempts capture 90% of score** — diminishing returns after that. [from log analysis]
10. **Aborting 3+ error attempts is safe** — zero score impact, saves 87 min. [from log analysis]

## Memory Files — What's Where

| File | Contains | Read when... |
|------|----------|-------------|
| `handover.md` | **START HERE for new sessions.** Where we stopped, v23 changes, next steps | Starting a new session |
| `competition.md` | Rules, constraints, submission format, evaluation, prizes, timeline | Setting up submissions, checking rules |
| `models.md` | Model landscape, benchmarks, what fits on H100 | Choosing/switching models |
| `solutions.md` | Analyzed solutions — baseline 44/50, Numina, NemoSkills, underdogs | Understanding what's been tried |
| `history.md` | Past AIMO1/2 results, leaderboards, patterns | Competition dynamics |
| `tools.md` | **CLI commands, Kaggle API, discussion scraping, workflow, gotchas** | Before any push/deploy/CLI work |
| `reference_problems.md` | 10 reference problems with answers, difficulty, model scores | Testing, validating approaches |
| `changelog.md` | Every change to the project, most recent first | What's been done, avoiding duplicates |
| `changelog-vs-baseline.md` | **Exhaustive diff** of notebook vs baseline-44-50.ipynb | Understanding exactly what's changed |

### Ideas & Strategy (in `memory/ideas/`)
- `strategies.md` — **Future scope**: full technique catalog, priority queue, research links. What we could do next.
- Individual files — **Feature docs**: deep dives on specific features we're planning. Each is a concrete next step.

| File | Key Content |
|------|-------------|
| `strategies.md` | Technique catalog, priority queue, what failed, research sources |
| `parallelism-and-early-stop.md` | Early stop is broken, KV cache math (233K tokens, 6.3x max), adaptive batching for v24 |

### Kaggle Discussion Summaries (in `memory/discussions/`)
| File | Key Insight |
|------|-------------|
| `pass-at-100.md` | **#679559** Host data: pass@100 ~50/50. More attempts = more points. |
| `runtime-and-scoring.md` | 5hr/run, dual run sequential (10hr total), 236 min headroom |
| `competitive-intel.md` | SymPy decoupling, MoE architecture, ref set unreliable |

### Discussion Raw Data (in `data/available/discussions/`)
| File | Contains |
|------|----------|
| `all_discussions.json` | Raw API data — 20 threads, 118 comments, all markdown |
| `all_discussions.md` | Readable markdown of all discussion content |
| `competitive_intel.md` | **Structured analysis** — strategies, model info, host announcements, key URLs |

### Diagnostics (in `diagnostics/v21/`)
| File | Contains |
|------|----------|
| `diagnostic.log` | Full 167K line run log — every turn, code call, output |
| `analysis_report.txt` | Struggle scoring: 1 FAILED, 3 HARD, 10 MODERATE, 36 CLEAN |
| `error_analysis.md` | Root cause taxonomy: 120 errors, 5 categories, per-problem breakdown |
| `error_patterns.md` | Deep patterns: which functions break, cascade analysis, time impact |
| `none_analysis.json` | 178/400 None attempts classified by reason |
| `all_problems.json` | Structured data for all 50 problems |
| `hard_problems.json` | Just the 4 struggling problems |

### Log Exploration Toolkit (in `log_exploration/`)
**30 scripts** for querying diagnostic.log as structured data. See `log_exploration/README.md` for full list.

| Category | Key Scripts |
|----------|-------------|
| Overview | `dashboard_prototype.py`, `export_csv.py` |
| Inspect | `problem_deep_dive.py <pid>`, `attempt_viewer.py <pid> <att>`, `compare_problems.py` |
| Search | `search_reasoning.py <regex>`, `search_code.py`, `search_errors.py`, `filter_attempts.py` |
| Errors | `error_deep_dive.py`, `error_patterns.py`, `error_timing.py`, `error_adaptive.py` |
| Performance | `timing_analysis.py`, `voting_analysis.py`, `token_efficiency.py`, `attempt_progression.py` |
| Strategy | `adaptive_compute.py`, `adaptive_simulator.py`, `code_strategy.py`, `library_analysis.py` |
| Quality | `reasoning_quality.py`, `extraction_analysis.py`, `problem_difficulty.py` |
| Comparison | `compare_runs.py <log1> <log2>` |
| Docs | `proposed_logging.md` — 22 logging proposals for v24 |

Core parser: `log_exploration/log_query.py` — also has 29 built-in queries.

### Legacy Scripts (in `scripts/`)
| Script | What it does |
|--------|-------------|
| `parse_diagnostics.py` | Parses diagnostic.log → struggle scores, problem categories |
| `analyze_errors.py` | Extracts traceback errors → root cause taxonomy |
| `analyze_nones.py` | Classifies NO ANSWER attempts by failure reason |

## Project Structure

```
aimo3/
├── memory/              ← You are here. Start with memory.md → handover.md
├── baseline-44-50.ipynb ← Original 44/50 notebook (READ-ONLY reference)
├── notebooks/           ← Our working notebooks (pushed to Kaggle)
│   ├── aimo3-solver.ipynb    ← Active solver
│   └── kernel-metadata.json  ← Kaggle kernel config
├── data/
│   ├── active/          ← What the notebook uses (test CSVs, reference)
│   └── available/       ← Everything else (val bench, old benchmarks, discussions)
├── log_exploration/     ← 30-script log query toolkit (see README.md inside)
├── scripts/             ← build_test_v23.py, parse_diagnostics.py, analyze_*.py
├── output/              ← Kaggle run outputs (download.txt etc)
├── .github/workflows/   ← kaggle-push.yml (AUTO-DEPLOYS on push!)
└── CLAUDE.md            ← Project config (read by Claude Code automatically)
```

## Kaggle Datasets

- `jxm222/aimo3-problem-db` — Problem DB (264 entries, public). Push with jxm222 creds.
- `shivzzzzzz02/aimo3-test-data` — Test CSVs (133 problems+answers, private). Uploaded under shivzzzzzz02.
- Both in `kernel-metadata.json` dataset_sources
