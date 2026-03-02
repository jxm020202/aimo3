# Changelog

All key changes to the AIMO3 project. Most recent first.

## 2026-03-02

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
