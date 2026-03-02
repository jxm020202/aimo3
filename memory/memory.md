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
- Voice input: messages prefixed with `[voice]` are speech-to-text, expect transcription errors
- User prefers concise communication, doesn't want hand-holding
- User has CAT 99.63 percentile — strong math intuition, don't underestimate domain knowledge
- User values being challenged on assumptions (e.g., corrected "private set is harder" misconception)

## Research Tools

- **ChatGPT Research**: User has ChatGPT deep research mode. For broad surveys (papers, techniques, competitive intel), suggest delegating there instead of spinning up 3+ Claude agents. One ChatGPT research query replaces hours of agent work.
- **Claude agents**: Better for code search, file reading, codebase work, writing code.
- **Rule of thumb**: If research needs >3 agents or deep web crawling → suggest ChatGPT Research.

## Quick Context

- **Competition**: AIMO Progress Prize 3 — solve 110 original math problems (olympiad to IMO level)
- **Prize**: $2.2M total. 1st: $262K. 47/50 bonus: $1.59M (never claimed across any AIMO).
- **Deadline**: April 15, 2026 (entry by April 8). ~6 weeks from March 2, 2026.
- **Hardware**: Free H100 GPUs on Kaggle. No internet during submission.
- **Answers**: 5-digit integers (0-99999). 50 public + 50 private problems.
- **Scoring**: Private LB runs each submission twice. Both correct=1, one correct=0.5, both wrong=0.
- **Open source required**: Winners must release all code, data, weights under CC-BY 4.0.
- **1 submission/day**, 1 final submission selected.
- **Model cutoff**: AMLTs used at runtime must be released before March 15, 2026.
- **Kaggle user**: jxm222 | **GitHub**: jxm020202/aimo3 (private repo)

## Current State

- **Baseline**: 44/50 public LB (GPT-OSS-120B, zero training, entropy-weighted voting)
- **Our score**: Not yet submitted
- **Approach**: Starting from baseline, improving inference strategy

## Critical Insight

GPT-OSS-120B solves only 4/10 reference problems (the easy AIMO2-level ones, Problems 1-4). It gets ZERO of the harder AIMO3-designed problems (5-10). The 44/50 baseline's remaining 6 unsolved problems are likely the hardest IMO-level ones where more sampling won't help. Path to 47+ requires either a stronger model or fundamentally different reasoning strategy for hard problems.

## Memory Files — What's Where

| File | Contains | Read when... | Update when... |
|------|----------|-------------|----------------|
| `competition.md` | Rules, constraints, submission format, evaluation, extra prizes, timeline | Setting up submissions, checking rule compliance | Rules clarified or deadlines change |
| `models.md` | Model landscape, benchmarks, what fits on H100, quantization details | Choosing/switching models, planning ensemble | New model discovered, benchmark results obtained |
| `solutions.md` | All analyzed solutions — baseline 44/50, Numina, NemoSkills, underdogs | Understanding what's been tried, planning improvements | New solution analyzed, approach validated/failed |
| `strategies.md` | Improvement vectors, research findings, what works/doesn't, math AI techniques | Planning next experiment, choosing approach | Technique tested (success or failure), new research found |
| `history.md` | Past AIMO1/2 results, leaderboards, underdog stories, score progressions | Understanding competition dynamics, setting expectations | New competitive intel, leaderboard shifts |
| `tools.md` | CLI commands, libraries, workflow, Kaggle API, local test harness | **Before any big change**, pushing notebooks, debugging workflow, setting up env | Tool errors, new commands discovered, env quirks found |
| `reference_problems.md` | The 10 reference problems with answers, difficulty notes, model performance | Local testing, validating our solution before submitting | New model tested on reference, scores updated |

## Project Structure

```
aimo3/
├── memory/              ← You are here
├── baseline-44-50.ipynb ← Original 44/50 notebook (read-only reference)
├── notebooks/           ← Our working notebooks
│   ├── aimo3-solver.ipynb    ← Active solver (pushed to Kaggle)
│   └── kernel-metadata.json  ← Kaggle kernel config
├── data/                ← Competition data
│   ├── reference.csv         ← 10 reference problems with answers
│   ├── test_fixed_50.csv     ← Fixed 50-problem benchmark for dev testing
│   ├── test_fixed_50_answers.csv
│   ├── test_random_50.csv    ← Random 50-problem set (regenerate with script)
│   ├── test_random_50_answers.csv
│   ├── test.csv              ← Kaggle placeholder (3 trivial problems)
│   ├── sample_submission.csv
│   ├── AIMO3_Reference_Problems.pdf
│   ├── kaggle_evaluation/    ← Submission framework code
│   └── test_sets/            ← Source datasets (AIME, IMO, MATH)
├── scripts/
│   ├── build_test_sets.py    ← Generates fixed/random test CSVs
│   └── evaluate.py           ← Scores output, supports double-run simulation
├── research/            ← Research notes
└── CLAUDE.md            ← High-level project config (read by Claude Code automatically)
```
