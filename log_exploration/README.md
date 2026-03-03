# Log Exploration Toolkit — Query Reference

> **HARD RULE FOR ALL AGENTS**: When you need data from diagnostic logs, ALWAYS use these scripts. NEVER grep/awk/sed raw logs. If no script exists for your question, write one here first, then run it.

Query system for AIMO3 diagnostic logs. Treats logs as structured data — every question about a run should be answerable with a script.

## Quick Start

```bash
# One-page summary of any run
python3 log_exploration/dashboard_prototype.py output/v23/diagnostic.log

# Deep dive into a specific problem
python3 log_exploration/problem_deep_dive.py output/v23/diagnostic.log 86e8e5

# Replay a specific attempt turn-by-turn
python3 log_exploration/attempt_viewer.py output/v23/diagnostic.log 86e8e5 2

# Compare two runs
python3 log_exploration/compare_runs.py output/v22/diagnostic.log output/v23/diagnostic.log

# Search for a pattern in errors
python3 log_exploration/search_errors.py output/v23/diagnostic.log "int_max_str_digits"
```

## Core Parser

**`log_query.py`** — Parses diagnostic.log into structured Python objects.

```python
from log_exploration.log_query import parse_log
problems = parse_log('output/v23/diagnostic.log')
# Returns: list[Problem], each with .attempts: list[Attempt], each with .turns: list[Turn]
```

Data structures:
- **Problem**: problem_id, batch_name, budget, predicted, expected, correct, wall_time, votes, attempts
- **Attempt**: attempt_num, answer, entropy, temperature, code_calls, errors, tokens, time_s, turns, is_none
- **Turn**: turn_num, reasoning_text, code, output, is_error

Also has 29 built-in queries: `python3 log_exploration/log_query.py <logfile> <query>` (run without args to see all).

## Complete Script Inventory (36 scripts)

### Dashboard & Overview (2)
| Script | Usage | What it does |
|--------|-------|-------------|
| `dashboard_prototype.py` | `<log>` | One-page terminal summary: score, time, trends, top issues |
| `export_csv.py` | `<log>` | Export to problems.csv, attempts.csv, turns.csv for spreadsheets |

### Problem Inspection (4)
| Script | Usage | What it does |
|--------|-------|-------------|
| `problem_deep_dive.py` | `<log> <pid>` | Everything about one problem: attempts, turns, reasoning, code, errors |
| `attempt_viewer.py` | `<log> <pid> <att>` | Replay one attempt turn-by-turn |
| `compare_problems.py` | `<log>` | Side-by-side comparison of multiple problems' attempts and voting |
| `wrong_problem_deep_dive.py` | `<log> [-o file] [--problem pid]` | All 17 wrong problems: vote tables, per-attempt detail, classification, entropy/temp/code analysis |

### Run Comparison (1)
| Script | Usage | What it does |
|--------|-------|-------------|
| `compare_runs.py` | `<log1> <log2>` | Diff two runs: score delta, flipped problems, per-problem comparison |

### Search & Filter (4)
| Script | Usage | What it does |
|--------|-------|-------------|
| `filter_attempts.py` | `<log> [--filters]` | Filter by temp, errors, time, answer, turns. Use `--temp 0.5 --stats` |
| `search_reasoning.py` | `<log> <regex>` | Search reasoning text across all attempts |
| `search_code.py` | `<log> <regex>` | Search code blocks across all attempts |
| `search_errors.py` | `<log> <regex>` | Search error output across all attempts |

### Error Analysis (4)
| Script | Usage | What it does |
|--------|-------|-------------|
| `error_deep_dive.py` | `<log>` | Cascade/recovery analysis, per-error-count correct rate, recovery strategies |
| `error_patterns.py` | `<log>` | Root cause taxonomy: timeout, NameError, ValueError, etc. |
| `error_timing.py` | `<log>` | Error rate by turn number, attempt number, problem type |
| `error_adaptive.py` | `<log>` | **Abort threshold analysis**: score impact of aborting at N errors. Key for v24 |

### Performance Analysis (5)
| Script | Usage | What it does |
|--------|-------|-------------|
| `timing_analysis.py` | `<log>` | Time distributions, time-vs-correctness, budget utilization |
| `voting_analysis.py` | `<log>` | Vote distributions, early stop simulation at various thresholds |
| `token_efficiency.py` | `<log>` | Token waste on Nones, reasoning length vs accuracy |
| `attempt_progression.py` | `<log>` | Answer convergence, reduced-attempt simulations |
| `gpu_timing_analysis.py` | `<log> [--save FILE]` | GPU timing, parallelism, budget analysis, reduced-attempt simulation |

### Temperature Analysis (2)
| Script | Usage | What it does |
|--------|-------|-------------|
| `temperature_analysis.py` | `<log>` | Per-temp accuracy, None rate, error rate, per-problem matrix, flat-temp simulations |
| `temperature_deep_analysis.py` | `<log>` | Hard-problem accuracy by temp, outvoted matrix, diversity contribution, 7 schedule simulations |

### Reasoning & Code Quality (6)
| Script | Usage | What it does |
|--------|-------|-------------|
| `reasoning_quality.py` | `<log>` | Success/failure keywords, approach restart counts |
| `code_quality.py` | `<log>` | Library usage, code length vs correctness, strategy classification |
| `code_strategy.py` | `<log>` | Per-attempt code strategy detection (brute_force, number_theory, etc.) |
| `problem_difficulty.py` | `<log>` | Difficulty scoring, topic detection, problem classification |
| `extraction_analysis.py` | `<log>` | None classification: extraction failure, no code, timeout, etc. |
| `close_miss_analysis.py` | `<log>` | Problems where |predicted - expected| < threshold. Off-by-one analysis |

### Library Analysis (3)
| Script | Usage | What it does |
|--------|-------|-------------|
| `library_analysis.py` | `<log>` | Which libraries used, accuracy per library, error rates |
| `library_failures.py` | `<log>` | Failed imports: pulp, ortools, z3, mip — counts and affected problems |
| `python_usage.py` | `<log>` | Python stdlib and 3rd-party usage patterns |

### Strategy & Simulation (4)
| Script | Usage | What it does |
|--------|-------|-------------|
| `adaptive_compute.py` | `<log>` | Wave-based batching simulation, time projections |
| `adaptive_simulator.py` | `<log>` | Strategy comparisons: fixed vs adaptive attempt counts |
| `attempt_marginal_value.py` | `<log> [--v22 <log>] [-o <file>]` | **8 vs 16 attempts ROI**: first-correct distribution, truncation score sim, marginal value per attempt, vote stability, v22 comparison |
| `early_stop_optimizer.py` | `<log> [--v22 <log>] [--save <file>]` | ES threshold optimizer: grid search (att,ES), false positive analysis, vote stabilization, v22/v23 comparison |

### Ordering & Time Pressure (1)
| Script | Usage | What it does |
|--------|-------|-------------|
| `problem_ordering_analysis.py` | `<log> [-o file.md]` | Problem ordering vs correctness, time pressure analysis, DOUBLE-RUN RETRY impact, Val Bench distribution |

### Logging Improvements (2)
| Script | Usage | What it does |
|--------|-------|-------------|
| `logging_gaps.py` | `<log>` | What's missing from logs: blind spots, unanswerable questions |
| `proposed_logging.md` | (doc) | 22 concrete logging proposals for v24 with code locations |

## Available Log Files

| Log | Problems | Notes |
|-----|----------|-------|
| `output/v22/diagnostic.log` | 60 (8 att, ES=3, flat 0.5) | 12MB, clean run |
| `output/v23/diagnostic.log` | 80 (16 att, ES=5, temp schedule) | 69MB, 940K lines |

## Key Findings

### v23 (80 problems, 63/80 = 78.8%)
1. **242 import errors** on unavailable libs (pulp 114, ortools 92, z3 16, mip 14)
2. **42 sys.set_int_max_str_digits errors**, all from problem 86e8e5
3. **Temp 0.9 is useless**: 0% unique solves, 76% None, 63% error rate
4. **Best schedule tested**: 0.1x4 + 0.3x8 + 0.5x4 = 62/78 (+1 over current)
5. **Error abort at 3**: loses 1 problem, saves 1,081 min
6. **ES=4 = ES=5** score (64/97), saves 73.5 min
7. **6 outvoted problems**: correct found but lost vote (21fb4e, aff75c, 29714f, 3980cd, 414a5b, dbbfe8)
8. **Correct answers have lower entropy** in 5/6 outvoted cases

### v22 (60 problems, 58/60 = 96.7%)
1. **Early stop 2 = same score as 5**, 47% less time
2. **47% of Nones are extraction failures** — model had the answer, regex missed it
3. **Wrong attempts: 3.4x longer reasoning**, 45 restarts, 16 turns
4. **133 min wasted on errors** — "Simplify" recovery = 100% success
5. **Budget utilization only 7.8%** — massive headroom
6. **First 4 attempts capture 90% of score**

## Common Questions → Which Script

| Question | Script |
|----------|--------|
| What's the overall score? | `dashboard_prototype.py` |
| Why did problem X fail? | `problem_deep_dive.py <log> X` |
| What does attempt N look like turn-by-turn? | `attempt_viewer.py <log> X N` |
| Which temperature is best? | `temperature_analysis.py` or `temperature_deep_analysis.py` |
| How many import errors? | `library_failures.py` or `search_errors.py <log> "ModuleNotFoundError"` |
| What's the optimal error abort? | `error_adaptive.py` |
| Would early stop N give same score? | `voting_analysis.py` |
| Which problems are close misses? | `close_miss_analysis.py` |
| Where is the model wasting tokens? | `token_efficiency.py` |
| Which problems were outvoted? | `voting_analysis.py` + `problem_deep_dive.py` |
| Did the run improve vs last? | `compare_runs.py <old_log> <new_log>` |
| What's the None rate breakdown? | `extraction_analysis.py` |
| How much time could we save? | `timing_analysis.py` + `error_adaptive.py` |

## Adding New Queries

1. Create a new `.py` in this folder
2. Import the parser: `from log_exploration.log_query import parse_log`
3. Parse: `problems = parse_log(sys.argv[1])`
4. Query the structured data (Problem -> Attempt -> Turn)
5. Add argparse with `--help` for CLI usage
6. **Update this README** with the new script in the correct category
7. Run it and verify output before using results
