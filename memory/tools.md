# Tools & Workflow

## Kaggle API Setup (REQUIRED before any Kaggle commands)

The Kaggle CLI needs an API key at `~/.kaggle/kaggle.json`. If it doesn't exist:
1. Ask the user to provide their Kaggle API key
2. Create the file: `mkdir -p ~/.kaggle && echo '{"username":"jxm222","key":"<KEY>"}' > ~/.kaggle/kaggle.json && chmod 600 ~/.kaggle/kaggle.json`
3. Install the CLI if needed: `pip3 install kaggle`
4. Verify: `kaggle kernels status jxm222/aimo3-solver`

**Do NOT attempt Kaggle commands without verifying `~/.kaggle/kaggle.json` exists first.**

## Kaggle CLI

```bash
# Push notebook to Kaggle (runs on H100)
kaggle kernels push -p notebooks/

# Check run status
kaggle kernels status jxm222/aimo3-solver

# Pull output after run completes
kaggle kernels output jxm222/aimo3-solver -p output/

# Download competition data
kaggle competitions download ai-mathematical-olympiad-progress-prize-3 -p data/

# List competition notebooks (sorted by score)
kaggle kernels list --competition ai-mathematical-olympiad-progress-prize-3 --sort-by scoreAscending

# Pull someone else's notebook
kaggle kernels pull <username>/<kernel-slug> -p /tmp/
```

**Kernel metadata** at `notebooks/kernel-metadata.json`:
- `id`: `jxm222/aimo3-solver`
- `code_file`: `aimo3-solver.ipynb` (must match the notebook filename in `notebooks/`)
- `competition_sources`: `ai-mathematical-olympiad-progress-prize-3`
- `model_sources`: `openai/gpt-oss-120b/transformers/default/1`
- `enable_gpu`: true, `enable_internet`: false

## Submission Flow (Step by Step)

This is a **code competition** — submission = running a notebook on Kaggle, not uploading a CSV.

1. **Develop** notebook locally in `notebooks/aimo3-solver.ipynb`
2. **Push to Kaggle**: `kaggle kernels push -p notebooks/`
   - This uploads the notebook + metadata and starts a run on Kaggle's H100
   - The notebook runs against `test.csv` (3 placeholder problems locally, 50 real problems on competition rerun)
3. **Wait for run** (takes hours on real problems):
   - `kaggle kernels status jxm222/aimo3-solver` — check status
   - States: `queued` → `running` → `complete` or `error`
4. **Check output**: `kaggle kernels output jxm222/aimo3-solver -p output/`
5. **Submit to leaderboard**: On Kaggle website, go to notebook → "Submit to Competition"
   - Or via CLI: the notebook auto-submits when `KAGGLE_IS_COMPETITION_RERUN` is set
6. **1 submission per day** — don't waste it. Test locally first with reference problems.

### How the notebook becomes a submission
- When pushed via `kaggle kernels push`, it runs in "test mode" against placeholder data
- To submit to the actual competition leaderboard, you must select "Submit" on the Kaggle notebook page
- During competition rerun, `KAGGLE_IS_COMPETITION_RERUN` is set → the notebook calls `inference_server.serve()` which handles the real 50 problems via gRPC
- The competition runs each submission **TWICE** on the private set. Both must agree for full credit. This is why determinism matters.

### Pre-submission checklist
- [ ] Verify `kernel-metadata.json` has correct `code_file`, `competition_sources`, `model_sources`
- [ ] Test against reference problems locally if possible
- [ ] Check notebook runs without errors on Kaggle (push first, check status)
- [ ] Only then submit to competition leaderboard

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

## Git

- Repo: https://github.com/jxm020202/aimo3 (private)
- `data/` and `memory/` are gitignored
- Personal GitHub account (no GPG signing needed, unlike WeMoney repos)
