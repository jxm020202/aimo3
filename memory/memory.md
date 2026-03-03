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

## Current State (March 3, 2026 — Session 4)

- **v15 SUBMITTED**: Scored 38/50 (broken extraction, no `break`)
- **v21**: 49/50 on test (8 attempts, ES=4, temp=0.5, 50 problems, 63.8 min)
- **v22**: 58/60 on test (8 attempts, ES=3, temp=0.5, 60 problems). Failures: 86e8e5, 76aef9.
- **v23 RUNNING**: Just pushed. 16 attempts, ES=5, temp schedule [0.1,0.3×4,0.5×6,0.7×4,0.9], 80 problems.
- **Full changelog**: `memory/changelog-vs-baseline.md` — every diff vs baseline
- **GitHub Actions auto-deploy DISABLED** (workflow_dispatch). Safe to push.

## Critical Insights

1. **Competition is about variance reduction, not capability** — host data: Model B (GPT-OSS-120B) solves ~50/50 at pass@100 without TIR. With TIR, baseline gets 44/50 at pass@8. See `memory/discussions/pass-at-100.md`. [thread #679559]
2. **GPT-OSS-120B is MoE with ~5.1B active params** — "120B" is misleading. This is why it fits in 5 hours. Dense replacements will be slower. [from discussions]
3. **`break` in answer extraction is critical** — without it, 41% of attempts return None. This was the root cause of 38/50.
4. **TIR (code execution) is the secret sauce** — hard problems only solvable with code sandbox.
5. **Leading teams use SymPy for deterministic arithmetic** — decoupling reasoning from execution. [from discussions]
6. **Reference set is unreliable** — 8/10 ref → 6/50 public LB reported. Use 347-problem community benchmark instead. [from discussions]
7. **Current #1 is the public 44/50 notebook** — team "just public 44, all is luck". Winning is partly stochastic. [from discussions]
8. **Qwen3.5-35B-A3B** is most promising model upgrade but vLLM tool-calling broken (Gated DeltaNet arch). AIMO4 play. [from discussions]

## Memory Files — What's Where

| File | Contains | Read when... |
|------|----------|-------------|
| `handover.md` | **START HERE for new sessions.** Where we stopped, v23 changes, next steps | Starting a new session |
| `competition.md` | Rules, constraints, submission format, evaluation, prizes, timeline | Setting up submissions, checking rules |
| `models.md` | Model landscape, benchmarks, what fits on H100 | Choosing/switching models |
| `solutions.md` | Analyzed solutions — baseline 44/50, Numina, NemoSkills, underdogs | Understanding what's been tried |
| `strategies.md` | Improvement techniques, research findings, **sandbox library research** | Planning next experiment |
| `history.md` | Past AIMO1/2 results, leaderboards, patterns | Competition dynamics |
| `tools.md` | **CLI commands, Kaggle API, discussion scraping, workflow, gotchas** | Before any push/deploy/CLI work |
| `reference_problems.md` | 10 reference problems with answers, difficulty, model scores | Testing, validating approaches |
| `changelog.md` | Every change to the project, most recent first | What's been done, avoiding duplicates |
| `changelog-vs-baseline.md` | **Exhaustive diff** of notebook vs baseline-44-50.ipynb | Understanding exactly what's changed |

### Discussion Data (in `data/discussions/`)
| File | Contains |
|------|----------|
| `all_discussions.json` | Raw API data — 20 threads, 118 comments, all markdown |
| `all_discussions.md` | Readable markdown of all discussion content |
| `competitive_intel.md` | **Structured analysis** — strategies, model info, host announcements, key URLs |

### Important Discussions (in `memory/discussions/`)
| File | Key Insight |
|------|-------------|
| `pass-at-100.md` | **#679559** Host data: pass@100 ~50/50. More attempts = more points. |
| `runtime-and-scoring.md` | 5hr/run, dual run sequential (10hr total), 236 min headroom |
| `competitive-intel.md` | SymPy decoupling, MoE architecture, ref set unreliable |

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

### Analysis Scripts (in `scripts/`)
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
├── scripts/             ← build_test_v23.py, parse_diagnostics.py, analyze_*.py
├── output/              ← Kaggle run outputs (download.txt etc)
├── .github/workflows/   ← kaggle-push.yml (AUTO-DEPLOYS on push!)
└── CLAUDE.md            ← Project config (read by Claude Code automatically)
```

## Kaggle Dataset

- `jxm222/aimo3-test-data` — uploaded dataset with test CSVs for cell-17
- Contains: reference.csv, test_problems.csv (70 Val Bench), test_answers.csv
- Old files (test_fixed_50, test_random_50) moved to `data/available/`
- Added to `kernel-metadata.json` dataset_sources
