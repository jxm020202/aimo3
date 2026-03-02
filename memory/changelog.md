# Changelog

All key changes to the AIMO3 project. Most recent first.

## 2026-03-02

### v19 Reference Results — 9/10 (90%)
- **Solved 9/10 reference problems** including all 6 "hard" problems (5-10)
- Only failure: P4 (86e8e5, Norwegian numbers) — predicted 23, expected 8687
- Proves TIR + 8-attempt voting >> pure reasoning (PDF benchmark said 4/10)
- Performance matches Grok-4 and Gemini 2.5 Pro on same problems
- Most hard problems solved in 100-270s, not burning full 900s budget

### Full Diagnostic Logging (pushed to GitHub, not yet on Kaggle)
- Cell-13: Single `conversation_log` per attempt with turn-by-turn entries
  - Type `reasoning`: full model text, no truncation
  - Type `code_call`: full code + output + error flag, no truncation
  - Per-attempt timing, stored on `self._last_detailed_results`
- Cell-17: Maximum diagnostic display for all attempts on all problems
  - Turn-by-turn conversation flow, library extraction, GPU memory stats
  - Wrong answer diagnosis (vote comparison, which attempts got what)
- Disabled GitHub Actions auto-deploy (workflow_dispatch)

### Project Setup
- Created project structure at `~/Desktop/sideprojects/aimo3/`
- Downloaded competition data, reference problems, AIME/IMO/MATH test sets
- Copied baseline 44/50 notebook as read-only reference
- Created private GitHub repo: jxm020202/aimo3
- Set up Kaggle API integration (kernel-metadata.json, secrets)

### Memory System
- Created 7-file agent knowledge base in `memory/`:
  - `memory.md` (index), `competition.md`, `models.md`, `solutions.md`,
    `strategies.md`, `history.md`, `tools.md`, `reference_problems.md`
- Designed for multi-agent context management: agents load only what they need

### Solver Notebook (`notebooks/aimo3-solver.ipynb`)
- Started from baseline 44/50 notebook (GPT-OSS-120B, TIR, entropy-weighted voting)
- **Deterministic seeding**: Added per-attempt seeds (`seed + attempt_index` squared)
  to ensure identical results across double-runs. Previously used global `set_seed(42)`
  which didn't guarantee determinism in vLLM sampling.
- **Deterministic tie-breaking**: Sort by `(score, votes, answer)` descending so ties
  always resolve the same way regardless of dict ordering.
- **Early stop threshold**: Changed from 4→5. Gives borderline problems one more attempt
  to reach consensus. ~12% more compute per problem but could recover 0.5-1pt.

### Test Harness
- `scripts/build_test_sets.py` — generates fixed 50-problem + random 50-problem test CSVs
  from AIME, IMO, and reference problem sources
- `scripts/evaluate.py` — scores submissions against answer keys, supports double-run
  simulation (pass two CSV files)
- `data/test_fixed_50.csv` — deterministic benchmark (10 reference + 15 AIME + 25 AIME+IMO)
- `data/test_random_50.csv` — random sample, regenerated each run

### CI/CD
- GitHub Actions workflow: merge to main with notebook changes auto-pushes to Kaggle
- Configured `KAGGLE_USERNAME` and `KAGGLE_KEY` as repo secrets

### Research
- Analyzed baseline 44/50, Numina (AIMO1 winner), NemoSkills (AIMO2 winner), underdogs
- ChatGPT deep research report on math AI competition strategies
- Key finding: GPT-OSS-120B solves only 4/10 reference problems (0/6 hard ones)
- Identified improvement vectors: determinism fix, answer verification, adaptive compute,
  condition mining, SymPy hybrid, PRMs, MCTS

### First Kaggle Run
- Pushed notebook v1 to Kaggle for test run on H100
- **FAILED**: Missing `aimo-3-utils` dataset source in kernel-metadata.json.
  Notebook needs `/kaggle/input/aimo-3-utils/wheels.tar.gz` for offline vLLM install.
  Fixed by adding `capthwi/aimo-3-utils` to `dataset_sources`.
- **FAILED AGAIN (v2)**: `capthwi/aimo-3-utils` is a dataset with only a llama_cpp wheel,
  not the right thing. The `wheels.tar.gz` comes from the OUTPUT of `andreasbis/aimo-3-utils`
  notebook — must use `kernel_sources` (not `dataset_sources`). Key Kaggle concept:
  notebook outputs mount via `kernel_sources`, datasets mount via `dataset_sources`.
- **v5**: Fixed kernel-metadata.json to use `kernel_sources: ["andreasbis/aimo-3-utils"]`
- Moved changelog from project root to `memory/changelog.md`
- **FAILED (v5)**: Model source `openai/gpt-oss-120b` doesn't exist on Kaggle.
  Correct source is `danielhanchen/gpt-oss-120b/Transformers/default/1`.
- **FAILED (v6)**: Default GPU is P100 (16GB), way too small for 120B model.
  Must set `machine_shape: "NvidiaH100"` in kernel-metadata.json.
- **v8**: All fixes applied — correct kernel_source, model_source, machine_shape.
  Three failure causes resolved: missing wheels, wrong model, wrong GPU.

### Deployment Debugging (v8 → v15)
- **FAILED (v10)**: vLLM crashed — `OSError: Can't load configuration of '/kaggle/input/gpt-oss-120b/...'`.
  Model path hardcoded but Kaggle mounts `model_sources` at `/kaggle/input/models/<owner>/...`
  not `/kaggle/input/<model-name>/...`. Debug showed `Processed 0 files (0.00 GB)`.
- **v11**: Added debug diagnostics (ls /kaggle/input/). Confirmed model at
  `/kaggle/input/models/danielhanchen/gpt-oss-120b/transformers/default/1`.
- **v13**: Added `find_model_path()` auto-discovery in cell-5. Server started successfully
  (119s). But crashed on `FileNotFoundError: test.csv` — competition data mounts at
  `/kaggle/input/competitions/...` not `/kaggle/input/...`.
- **v15**: Added test.csv auto-discovery in cell-16. **FIRST SUCCESSFUL RUN.**
  All 3 test problems solved correctly. Total runtime ~500s.
- **v15 submitted to competition** as first entry.

### Hard Fixes / Technical Debt (TODO: fix properly later)
These are hacks/workarounds that got us running but should be revisited:

1. **Docker image borrowed from someone else** (`kernel-metadata.json`):
   `gcr.io/kaggle-private-byod/python@sha256:536e3d9752ddf...`
   — We copied this from another notebook. Should understand what it provides and
   whether we need it, or if the default Kaggle image works.

2. **Wheels from someone else's notebook** (`kernel_sources: ["andreasbis/aimo-3-utils"]`):
   — We depend on `andreasbis/aimo-3-utils` notebook output for `wheels.tar.gz`
   containing vLLM, unsloth, openai_harmony wheels + tiktoken encodings.
   — If that notebook is deleted/updated, we break. Should fork to `jxm222/aimo3-utils`.

3. **Model source from danielhanchen** (`model_sources: ["danielhanchen/gpt-oss-120b/..."]`):
   — Using danielhanchen's upload of the model. If removed, we break.
   — OpenAI's official source `openai/gpt-oss-120b` doesn't show in Kaggle search
   but might work. Need to verify or fork the model.

4. **Model path auto-discovery** (cell-5 `find_model_path()`):
   — Works but is a runtime workaround for not knowing the exact mount path.
   — Kaggle mount paths aren't documented well. Two known patterns:
     Pattern A: `/kaggle/input/<model-name>/<framework>/<variant>/<version>`
     Pattern B: `/kaggle/input/models/<owner>/<model-name>/<framework>/<variant>/<version>`
   — Our function tries both + glob fallback. Robust but hacky.

5. **Test CSV path auto-discovery** (cell-16):
   — Competition data mounts at `/kaggle/input/competitions/...` in test runs
   but might be at `/kaggle/input/...` in competition re-runs. We try both.
   — In competition re-run mode (`serve()`), this code doesn't execute anyway.

### Reference Problem Testing (v18)
- v18 ran 10 reference problems. Results (partial, v18 may still be running):
  - Problem 1 (92ba6a, sweets): **CORRECT** 50 — ~26s
  - Problem 2 (9c1c5f, functional equation): **CORRECT** 580 — ~100s
  - Problem 3 (a295e9, rectangles): **CORRECT** 520 — ~335s
  - Problem 4 (86e8e5, Norwegian): Still running at 900s budget — hard number theory
- Confirmed: easy problems solve fast, hard problems burn full 900s budget
- Kaggle log interleaving: pip stderr from 298s appears between 688s problem output (harmless)

### Tiered Test Framework (v19)
- Added cell-17 with TEST_LEVEL (0=trivial, 1=+10 reference, 2=+50 fixed, 3=+50 random)
- Created Kaggle dataset `jxm222/aimo3-test-data` with test CSVs
- Added to kernel-metadata.json dataset_sources
- Deduplicates problems across levels

### Code Analysis: Our Diffs from Baseline
- Confirmed our solver is **functionally identical to baseline** for solving behavior
- Only diffs: early_stop 4→5, deterministic tie-breaking, model/test path discovery
- The early stop loop change (no break/cancel) is effectively identical due to executor.shutdown(wait=True)
- Long runtimes are inherent architecture behavior, not a regression
- Full diff analysis documented in `memory/handover.md`

### Strategy Research (for future use, not current priority)
- Comprehensive research on improvement techniques saved to `memory/strategies.md`
- Key findings: GenSelect (+13% on AIME24), ThinkPRM-14B as verifier, adaptive compute,
  MCTS (rStar-Math 58.8%→90% on MATH), CISC voting (46% fewer samples needed)
- SGLang potentially ~29% faster than vLLM on H100
- None of this matters until we have a stable, scoring submission
