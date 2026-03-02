# AIMO3 — AI Mathematical Olympiad Progress Prize 3

Competitive solution for [AIMO Progress Prize 3](https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3) on Kaggle.

**Goal**: Solve 110 original math problems (olympiad → IMO level) using open-weight LLMs on free H100 GPUs.

## Quick Start

```bash
# Push notebook to Kaggle (runs on H100)
kaggle kernels push -p notebooks/

# Check run status
kaggle kernels status jxm222/aimo3-solver

# Pull output after completion
kaggle kernels output jxm222/aimo3-solver -p output/

# Submit to competition (manual, 1/day)
kaggle competitions submit -c ai-mathematical-olympiad-progress-prize-3 \
  -f submission.csv -k jxm222/aimo3-solver -v <VERSION> -m "Message"
```

## CI/CD

Merging to `main` with changes in `notebooks/` automatically pushes the notebook to Kaggle for a test run via GitHub Actions. This is a **run only** — competition submission is always manual.

Secrets required: `KAGGLE_USERNAME`, `KAGGLE_KEY` (already configured).

## Project Structure

```
aimo3/
├── notebooks/              # Working notebooks (pushed to Kaggle)
│   ├── aimo3-solver.ipynb  # Active solver
│   └── kernel-metadata.json
├── baseline-44-50.ipynb    # Original 44/50 reference (read-only)
├── data/                   # Competition data + test sets
├── scripts/                # Test harness (build_test_sets.py, evaluate.py)
├── memory/                 # Agent knowledge base (see below)
├── research/               # Research notes and reports
├── CLAUDE.md               # Claude Code project config
├── memory/changelog.md     # All key changes logged here
└── notes.md                # Improvement ideas and TODOs
```

## For Agents: Commenting & Documentation Standards

**Every agent working on this codebase must follow these rules:**

### Code Comments

1. **Explain WHY, not WHAT.** Don't comment `# increment counter` — comment why the counter exists and what it tracks.
2. **Document non-obvious decisions.** If you chose approach A over B, say why in a comment.
3. **Mark changes with context.** When modifying existing code, add a brief comment explaining what changed and why:
   ```python
   # Changed early_stop from 4→5: gives borderline problems one more
   # attempt to reach consensus before stopping. Costs ~12% more compute
   # but should recover 0.5-1 point on problems near the voting threshold.
   early_stop = 5
   ```
4. **Flag assumptions.** If code depends on external behavior (vLLM version, Kaggle environment, model behavior), document it.
5. **Keep notebook markdown cells rich.** Each major section in the notebook should have a markdown cell explaining what it does, why, and any key parameters.

### Commit Messages

1. Be specific: "Fix double-run determinism via per-attempt seeding" not "Fix bug"
2. Reference the problem being solved: "Recover 0.5-1pt from borderline problems"
3. If changing a parameter, state old→new value and reasoning

### Memory Updates

1. Read `memory/memory.md` before starting any work
2. Update relevant memory files when you learn something new
3. Update at ~80% context compaction — don't let knowledge die with your context
4. See `memory/memory.md` for full update rules

### Changelog

Log every meaningful change in `CHANGELOG.md` with date, what changed, and why.

## Current Approach

- **Model**: GPT-OSS-120B (117B MoE, 5.1B active params, Apache 2.0)
- **Inference**: vLLM with fp8 KV cache on H100
- **Strategy**: Tool-Integrated Reasoning (TIR) with Self-Consistency voting
  - 8 parallel attempts per problem, 16 Jupyter sandbox workers
  - Entropy-weighted majority voting for answer selection
  - Deterministic per-attempt seeding for double-run consistency
- **Baseline**: 44/50 public leaderboard (not our submission, reference point)
