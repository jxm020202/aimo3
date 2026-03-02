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

## Current State (March 2, 2026 night)

- **v15 SUBMITTED** to competition — first entry, awaiting re-run results
- **v19 COMPLETE**: 9/10 reference problems correct (90%)! See `reference_problems.md` for full breakdown
- **New logging version pushed to GitHub** but NOT yet pushed to Kaggle
- **Cell-13**: Full conversation logging (every turn, every code execution, no truncation)
- **Cell-17**: Max diagnostic display (turn-by-turn flow, libraries, GPU stats, all attempts)
- **GitHub Actions auto-deploy DISABLED** (workflow_dispatch). Safe to push.

## Critical Insights

1. **We scored 9/10 on reference problems** — matching Grok-4 and Gemini 2.5 Pro benchmarks. The PDF said GPT-OSS-120B only gets 4/10 at pass@3, but TIR + 8-attempt voting gets 9/10.
2. **TIR (code execution) is the secret sauce** — problems 5-10 that were "unsolvable" by GPT-OSS-120B in pure reasoning mode were ALL solved with code sandbox access.
3. **Only failure: Problem 4** (86e8e5, Norwegian numbers with M=3^{2025!}). Got 23 instead of 8687. Need detailed logs to understand why.
4. **Most hard problems solved in 100-270s** — fast! Not burning full 900s. Only P4 (wrong) and P3/P9 took longer.
5. **Solver code is functionally identical to baseline** — our diffs (early_stop 5, deterministic tie-breaking) don't explain the 9/10 score. The baseline architecture itself is this good.
6. **Next priority**: Push new logging version to Kaggle, re-run reference problems to get full diagnostics on P4 failure and understand HOW problems 5-10 were solved.

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
