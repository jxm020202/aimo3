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

- **Never add `Co-Authored-By` to commits** — user doesn't want it
- **DO NOT push to git without asking** — auto-push triggers Kaggle deploy (GitHub Actions)
- **GitHub Actions auto-push is ON** — pushing `notebooks/**` to main auto-deploys to Kaggle. Must disable workflow before pushing code casually.
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

## Current State (March 2, 2026 evening)

- **v15 SUBMITTED** to competition — first entry, awaiting re-run results
- **v18**: Running 10 reference problems. 3/3 correct so far (50, 580, 520). Slow/stuck on problem 4.
- **v19**: Running with tiered test framework (cell-17).
- **Code is functionally identical to baseline** — see `handover.md` for full diff
- **No uncommitted code changes** — working tree is clean
- **`strategies.md` has uncommitted research notes** (sandbox library research)

## Critical Insights

1. **GPT-OSS-120B solves only 4/10 reference problems** (easy ones). 0/6 hard AIMO3-level.
2. **Our solver is identical to baseline for solving** — only diffs are early_stop 4→5, deterministic tie-breaking, model/test.csv path discovery. None affect solving speed.
3. **Hard problems take 900s** because 8 parallel attempts each burn full budget with no consensus. This is expected baseline behavior, not a regression.
4. **Sandbox kernel hangs** are possible when model generates naive code (e.g., `3**factorial(2025)`). SIGINT can't interrupt C-level bigint operations.
5. **Highest-impact next step**: Prompt engineering to make model generate efficient code (modular arithmetic, not brute-force bigints). See `strategies.md` "Sandbox Libraries & Compute Efficiency".

## Memory Files — What's Where

| File | Contains | Read when... |
|------|----------|-------------|
| `handover.md` | **START HERE for new sessions.** Where we stopped, open questions, exact diffs from baseline, what to investigate | Starting a new session |
| `competition.md` | Rules, constraints, submission format, evaluation, prizes, timeline | Setting up submissions, checking rules |
| `models.md` | Model landscape, benchmarks, what fits on H100 | Choosing/switching models |
| `solutions.md` | Analyzed solutions — baseline 44/50, Numina, NemoSkills, underdogs | Understanding what's been tried |
| `strategies.md` | Improvement techniques, research findings, **sandbox library research** | Planning next experiment |
| `history.md` | Past AIMO1/2 results, leaderboards, patterns | Competition dynamics |
| `tools.md` | **CLI commands, Kaggle API, workflow, gotchas** | Before any push/deploy/CLI work |
| `reference_problems.md` | 10 reference problems with answers, difficulty, model scores | Testing, validating approaches |
| `changelog.md` | Every change to the project, most recent first | What's been done, avoiding duplicates |

## Project Structure

```
aimo3/
├── memory/              ← You are here. Start with memory.md → handover.md
├── baseline-44-50.ipynb ← Original 44/50 notebook (READ-ONLY reference)
├── notebooks/           ← Our working notebooks (pushed to Kaggle)
│   ├── aimo3-solver.ipynb    ← Active solver
│   └── kernel-metadata.json  ← Kaggle kernel config
├── data/                ← Competition data + test sets
├── scripts/             ← build_test_sets.py, evaluate.py
├── output/              ← Kaggle run outputs (download.txt etc)
├── .github/workflows/   ← kaggle-push.yml (AUTO-DEPLOYS on push!)
└── CLAUDE.md            ← Project config (read by Claude Code automatically)
```

## Kaggle Dataset

- `jxm222/aimo3-test-data` — uploaded dataset with test CSVs for cell-17
- Contains: reference.csv, test_fixed_50.csv, test_fixed_50_answers.csv, test_random_50.csv, test_random_50_answers.csv
- Added to `kernel-metadata.json` dataset_sources
