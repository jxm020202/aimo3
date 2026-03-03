# Tools & Workflow

## Kaggle CLI

```bash
# Push notebook to Kaggle (runs on H100)
kaggle kernels push -p notebooks/

# Check run status
kaggle kernels status jxm222/aimo3-solver

# Pull output after run completes
kaggle kernels output jxm222/aimo3-solver -p output/

# Submit to competition
kaggle competitions submit -c ai-mathematical-olympiad-progress-prize-3 \
  -f submission.csv -k jxm222/<NOTEBOOK> -v <VERSION> -m "Message"

# Download competition data
kaggle competitions download ai-mathematical-olympiad-progress-prize-3 -p data/

# List competition notebooks (sorted by score)
kaggle kernels list --competition ai-mathematical-olympiad-progress-prize-3 --sort-by scoreAscending

# Pull someone else's notebook
kaggle kernels pull <username>/<kernel-slug> -p /tmp/
```

**Kernel metadata** at `notebooks/kernel-metadata.json`:
- `id`: `jxm222/aimo3-solver`
- `competition_sources`: `ai-mathematical-olympiad-progress-prize-3`
- `kernel_sources`: `andreasbis/aimo-3-utils` (provides `wheels.tar.gz` with vLLM/unsloth wheels + tiktoken encodings)
- `model_sources`: `danielhanchen/gpt-oss-120b/Transformers/default/1`
- `dataset_sources`: `jxm222/aimo3-test-data` (test CSVs for cell-17)
- `machine_shape`: `NvidiaH100` (MUST set — default P100 can't fit 120B model)
- `docker_image`: borrowed from another notebook (see changelog.md hard fixes)
- `enable_gpu`: true, `enable_internet`: false

**IMPORTANT: kernel_sources vs dataset_sources**:
- `kernel_sources` = output of another Kaggle notebook, mounted at `/kaggle/input/<kernel-slug>/`
- `dataset_sources` = a Kaggle dataset, mounted at `/kaggle/input/<dataset-slug>/`
- The `wheels.tar.gz` comes from `andreasbis/aimo-3-utils` notebook OUTPUT, not a dataset
- Using `dataset_sources` for this will FAIL — the dataset `capthwi/aimo-3-utils` is different and doesn't have the tar
- **Fallback**: If `andreasbis/aimo-3-utils` output goes stale, fork it under `jxm222/aimo3-utils`
- **Model source**: We use `danielhanchen/gpt-oss-120b/Transformers/default/1`.
  `openai/gpt-oss-120b` does NOT work on Kaggle (doesn't exist in their registry).
  Model mounts at: `/kaggle/input/models/danielhanchen/gpt-oss-120b/transformers/default/1`

## Workflow: Local → Kaggle

1. Develop/edit notebook locally in `notebooks/`
2. `kaggle kernels push -p notebooks/` → uploads and runs on Kaggle H100
3. `kaggle kernels status jxm222/aimo3-solver` → check if done
4. `kaggle kernels output jxm222/aimo3-solver -p output/` → pull results
5. Submit: `kaggle competitions submit ...`
6. No local GPU needed — all inference runs on Kaggle

## Python Libraries Available

| Library | What for | Install |
|---------|----------|---------|
| `youtube-transcript-api` | Pull YouTube transcripts | `pip3 install youtube-transcript-api` |
| `kaggle` | Kaggle CLI | `pip3 install kaggle` |

## On Kaggle (available in notebook runtime)

| Library | What for |
|---------|----------|
| `vllm` | LLM serving/inference engine |
| `transformers` | HuggingFace model loading |
| `torch` | PyTorch |
| `jupyter_client` | Python sandbox for TIR (code execution) |
| `sympy` | Symbolic math verification |

## YouTube Transcript API

```python
from youtube_transcript_api import YouTubeTranscriptApi
api = YouTubeTranscriptApi()
transcript = api.fetch('VIDEO_ID')
for entry in transcript:
    print(f'[{int(entry.start//60)}:{int(entry.start%60):02d}] {entry.text}')
```

## ChatGPT Research (Deep Research Mode)

User has ChatGPT with deep research capability. For tasks requiring extensive web research, literature review, or broad exploration across many sources, suggest delegating to ChatGPT Research instead of spinning up multiple Claude agents. Better for:
- Surveying papers on a technique (e.g., "all MCTS for math reasoning papers")
- Understanding a new model's capabilities in depth
- Competitive intelligence (what other teams are doing)
- Finding and summarizing tutorials/implementations

Claude agents are better for: code search, file reading, codebase exploration, writing code.

**When research is getting out of hand** (3+ agents, deep web crawling, broad surveys): suggest ChatGPT Research instead. One focused research query there saves many agent-hours here.

## Local Testing (Dev Deployment)

```bash
# Build test sets (fixed 50 + random 50)
python scripts/build_test_sets.py

# Evaluate output against answers
python scripts/evaluate.py output/submission.csv data/test_fixed_50_answers.csv

# Simulate double-run scoring (two submission files)
python scripts/evaluate.py output/run1.csv data/test_fixed_50_answers.csv output/run2.csv
```

- `data/test_fixed_50.csv` — deterministic benchmark (10 reference + 15 hard AIME + 25 AIME+IMO)
- `data/test_random_50.csv` — random sample, regenerated each run
- To test on Kaggle: swap the path in notebook's `run_local_gateway()` to point at test CSV

## Kaggle Runtime Gotchas

- **Kaggle log interleaving**: pip stderr from setup (298s) gets mixed into stdout from
  later cells (688s+). Looks like errors appearing mid-solve but they're harmless pip
  dependency warnings from earlier.
- **Model mount paths**: `model_sources` mount at `/kaggle/input/models/<owner>/<name>/<framework>/<variant>/<version>`.
  Our `find_model_path()` in cell-5 auto-discovers this.
- **Competition data paths**: Test runs mount at `/kaggle/input/competitions/...`,
  competition re-runs may differ. Cell-16 tries both.
- **`KAGGLE_IS_COMPETITION_RERUN`**: Env var set during real competition scoring.
  When set → `serve()`. When not → `run_local_gateway()`. Cell-17 tests only run when NOT set.
- **Kernel output**: `kaggle kernels output` only works for completed runs. Can't pull
  logs from running kernels via CLI. Must use Kaggle UI for live logs.
- **Version-specific output**: No CLI flag to pull output from a specific version number.
  Always gets latest completed version.
- **H100 queue**: Multiple versions can run simultaneously but may compete for GPU time.
  Cancel old versions from UI if they're wasting resources.

## Scraping Kaggle Competition Discussions

Kaggle has NO official API for discussions. The approach that works:

1. **Get session cookies**: `GET` the competition discussion page to obtain `XSRF-TOKEN` cookie
2. **List all topics**: `POST` to `https://www.kaggle.com/api/i/discussions.DiscussionsService/GetTopicListByForumId`
   - Body: `{"forumId": <FORUM_ID>, "pageSize": 100}`
   - Header: `X-XSRF-TOKEN: <token from cookie>`
3. **Get topic messages**: `POST` to `https://www.kaggle.com/api/i/discussions.DiscussionsService/GetForumTopicById`
   - Body: `{"forumTopicId": <TOPIC_ID>, "includeComments": true}`
   - Returns: `rawMarkdown` for OP + all comments
4. **Forum IDs**: Found via `GetForum` endpoint or by intercepting browser network calls

**AIMO3 Forum ID**: `9129558` (competition ID: 118448)
**Competition slug**: `ai-mathematical-olympiad-progress-prize-3`

**What doesn't work**:
- Meta Kaggle dataset: AIMO3 topics too recent (max ID 679507, AIMO3 starts at 679559+)
- Direct Kaggle API (`/api/v1/...`): No discussion endpoints
- Basic auth on internal endpoints: Returns 400 (needs session cookies)
- Plain HTTP fetch: JS-rendered pages, only get 5KB shell

**Data stored at**: `data/discussions/all_discussions.json` and `data/discussions/all_discussions.md`

## GitHub Actions (CAUTION)

- `.github/workflows/kaggle-push.yml` auto-pushes to Kaggle on any push to `main`
  that touches `notebooks/**`
- **This means git push = Kaggle run = burns H100 time**
- To push code without triggering: either disable workflow first, or don't change
  notebooks/ files in the commit
- To disable: change `on: push:` to `on: workflow_dispatch:` in the YAML

## Diagnostic Log Analysis

### Parser Scripts
```bash
# Parse diagnostic.log → struggle scores, risk analysis, key insights
python3 scripts/parse_diagnostics.py

# Analyze code errors → root causes, patterns, per-problem breakdown
python3 scripts/analyze_errors.py
```
- Input: `output/v21/diagnostic.log` (167K lines, 10MB)
- Diagnostics output: `diagnostics/v21/` (analysis_report.txt, error_analysis.md, all_problems.json, hard_problems.json, error_analysis.json)
- Categories: FAILED (wrong answer) → HARD (struggle≥30) → MODERATE (10-29) → CLEAN (<10)
- Error analysis: `diagnostics/v21/error_analysis.md` has full root cause taxonomy

### Log Format (diagnostic.log)
Structure: `~~~~~~` separators split problem blocks in pairs (ID block + content block).
```
======================================================================
  TIER_NAME (N problems)
======================================================================

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  [1/N] Problem id=XXXXXX
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Problem: <text>
Budget: 900.00 seconds | Deadline: <unix_ts>
Final Answer: <N>

  >> CORRECT  (or  >> *** WRONG ***)
     Predicted: X | Expected: Y | Wall time: Zs
     Attempts answered: A/B | Code calls: C | Errors: E | Tokens: T
     Avg entropy: X | Early stop: Yes|No (threshold=4)
     Attempt times: min=Xs  max=Xs  avg=Xs
     Votes: [answer: N votes | ...]

     ATTEMPT K  |  answer=X  entropy=Y  code_calls=Z  errors=E  tokens=T  time=Xs << STATUS
     [Turn N]
     [Reasoning] (N chars): ...
     [Code]: ...
     [Output]: ...
```

### Quick grep patterns for the log
```bash
# Summary lines only (one per problem)
grep -E 'Predicted:.*Expected:' output/v21/diagnostic.log

# Wrong answers only
grep -E '\*\*\* WRONG' output/v21/diagnostic.log

# Tier summaries
grep -E 'Score:|Total time:' output/v21/diagnostic.log

# Final score
grep -E 'FINAL SUMMARY' -A3 output/v21/diagnostic.log

# All attempt lines (compact view)
grep 'ATTEMPT.*<<' output/v21/diagnostic.log

# High error attempts
grep -E 'errors=[5-9][0-9]*|errors=[1-9][0-9]+' output/v21/diagnostic.log
```

### Key metrics from v21 analysis
- **44.5% None rate**: Almost half of all attempts fail answer extraction. #1 bottleneck.
- **Normal happy path**: 4/8 answered, 4 None, early_stop=Yes — this is NOT struggling.
- **Real struggle indicators**: wrong_count>0, unique_answers≥3, no early stop, wall_time>200s
- **5 problems ≥200s consume 50% of total time** (1909s / 3829s)
- **Error rate misleading for small N**: 1/1 = 100% but 1 error is nothing. Use absolute counts.

## Git

- Repo: https://github.com/jxm020202/aimo3 (private)
- `data/` and `memory/` are tracked (private repo, useful for agents)
- Personal GitHub account (no GPG signing needed, unlike WeMoney repos)
