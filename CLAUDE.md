# AIMO3 — AI Mathematical Olympiad Progress Prize 3

## First Steps for Any Agent

1. Read this file (you're doing it now)
2. Read `memory/memory.md` for full context index and current state
3. Only load specific memory files (`memory/*.md`) when needed for your task
4. Before writing code, understand the baseline: `baseline-44-50.ipynb`

## Competition Summary

- **Kaggle**: https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3
- **Prize**: $2.2M main + $110K extras. 1st: $262K. 47/50 bonus: $1.59M (unclaimed).
- **Deadline**: April 15, 2026 (entry by April 8)
- **Hardware**: Free H100 GPUs on Kaggle. No internet during submission.
- **Task**: 110 original math problems, 5-digit integer answers, olympiad to IMO level
- **Model cutoff**: Runtime AMLTs must be released before March 15, 2026
- **Open source required**: Winners must release everything (CC-BY 4.0)

## Project Structure

```
aimo3/
├── memory/              ← Knowledge base (gitignored). Start with memory.md.
│   ├── memory.md        ← INDEX: read this first, points to all other files
│   ├── competition.md   ← Rules, dates, prizes, submission format
│   ├── models.md        ← Model landscape, benchmarks, hardware fit
│   ├── solutions.md     ← All analyzed solutions (baseline, Numina, NemoSkills, underdogs)
│   ├── strategies.md    ← Improvement vectors, what works/doesn't, research
│   ├── history.md       ← Past AIMO1/2 results, leaderboards, patterns
│   ├── tools.md         ← CLI commands, workflow, libraries, ChatGPT research
│   └── reference_problems.md ← 10 reference problems with answers for local testing
├── baseline-44-50.ipynb ← Original 44/50 notebook (read-only reference)
├── notebooks/           ← Our working notebooks (pushed to Kaggle via API)
│   └── kernel-metadata.json
├── data/                ← Competition data (gitignored)
├── scripts/             ← Helper scripts
└── research/            ← Research notes
```

## Workflow

1. Develop notebooks locally in `notebooks/`
2. Push to Kaggle: `kaggle kernels push -p notebooks/`
3. Check status: `kaggle kernels status jxm222/aimo3-solver`
4. Pull output: `kaggle kernels output jxm222/aimo3-solver -p output/`
5. GPU runs happen on Kaggle's H100s — no local GPU needed

## Current State

- **Baseline**: 44/50 public LB (GPT-OSS-120B, zero training, entropy-weighted voting)
- **Our score**: Not yet submitted
- **Critical insight**: GPT-OSS-120B solves only 4/10 reference problems (easy ones). Gets 0/6 hard AIMO3-level problems. The 44→47 gap requires either a stronger model or fundamentally smarter reasoning.

## Research Tools

- **ChatGPT Research**: User has ChatGPT deep research mode. For broad surveys, competitive intel, paper reviews → suggest ChatGPT Research instead of 3+ Claude agents.
- **Claude agents**: Best for code search, file reading, codebase work, implementation.

## Kaggle

- Username: jxm222
- API key: `~/.kaggle/kaggle.json`
- GitHub: jxm020202/aimo3 (private)
