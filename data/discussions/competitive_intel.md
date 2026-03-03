# AIMO3 Competitive Intelligence Summary

Extracted from 20 competition discussion threads (scraped 2026-03-02).

## Top Findings

### 1. Competition is About Variance Reduction
Host (Simon Frieder) confirmed: pass@100 without tool-calling nearly solves ALL problems.
The bottleneck is NOT model capability — it's extracting correct answers reliably within the
5-hour/single-answer constraint. [ID: 679559]

### 2. GPT-OSS-120B is MoE (~5.1B active params)
The "120B" label is misleading. It's a Mixture of Experts model with only ~5.1B active
parameters at inference. This is why it fits in 5 hours on H100. Any dense replacement
(e.g., Qwen3.5-27B at 27B active) will be SLOWER despite lower nominal count. [ID: 679339]

### 3. Leading Team Strategy: SymPy Decoupling
A top team quoted: "our pipeline was specifically engineered to ensure consistent outputs
across multiple runs... By decoupling reasoning from execution via SymPy, we address the
5-digit precision requirement without relying on stochastic arithmetic." [ID: 635859]

### 4. Reference Set is Unreliable as Local Eval
Reported: 8/10 on reference → only 6/50 on public LB. Do not over-index on 10-problem
reference set. Use community benchmark instead (347 verified problems). [ID: 635859]

### 5. Current #1 is a Public 44/50 Notebook
Team "just public 44, all is luck" at #1 confirms the stochastic nature.
The exact same public notebook can win first place purely by luck. [ID: 678966]

### 6. Two Test Problems Were Corrected + Rescored
Problem A: wrong answer key. Problem B: invalid answer format. All submissions
re-evaluated. [ID: 669690]

## Model Landscape

| Model | Type | Active Params | Status |
|-------|------|--------------|--------|
| GPT-OSS-120B | MoE | ~5.1B | Competition standard, 44/50 baseline |
| GPT-OSS-20B | ? | ? | Suspected in host's benchmark study |
| Qwen3.5-35B-A3B | MoE | 3B | Beats GPT-OSS w/o tools, but vLLM broken (Gated DeltaNet) |
| Qwen3.5-27B | Dense | 27B | Slower than GPT-OSS, not recommended |
| Qwen3.5-122B | ? | ? | Mentioned as potentially competitive |

## Important Resources

| Resource | URL | Why It Matters |
|----------|-----|---------------|
| Community validation benchmark | kaggle.com/datasets/jordane95/aimo3-validation-benchmark | 347 verified integer-answer problems — better than 10 ref problems |
| GPT-OSS traces on H100 | kaggle.com/code/sonphamorg/traces-h100-gptoss-curated | Reasoning traces from our exact model/hardware |
| CrystalMath | huggingface.co/datasets/ycchen/Crystal-Math-Preview | 2,129 verified hard contest math problems for RLVR |
| Tool-calling dataset | kaggle.com/datasets/wenliangtlh/aimo3-high-difficulty-tool-calling-dataset | High-difficulty tool-calling data |
| GPT-OSS TIR preference pairs | huggingface.co/datasets/VITHURSHAN/DFO-Kaggle | For tool-calling fine-tuning |
| Qwen3.5 notebook | kaggle.com/code/shelterw/qwen3-5-w-python | Only known working Qwen3.5 attempt |
| MathArena | matharena.ai/ | Shows LLM responses to reference problems |
| Qwen3.5 models | huggingface.co/collections/Qwen/qwen35 | All Qwen3.5 variants |

## Host Announcements

- Team size limit increased to 20 [ID: 663402]
- Math Corpus Prize character limit raised to 100k [ID: 635859]
- Failed submissions count toward daily limit of 1 [ID: 635859]
- Private LB evaluated TWICE for robustness [ID: 635859]
- Runtime display obfuscated by ±30 min [ID: 679451]
- CUDA capped at 12.6 in Kaggle image [ID: 635859]

## Known Issues

- Platform slowdown around 00:00 UTC on 2026-02-25 (7x slower model loading) [ID: 678800]
- Triton backend slower than CUDA for vLLM [ID: 672978]
- SGLang slightly slower than vLLM for this use case [ID: 676019]
- Some accounts experience persistent submission errors with no Kaggle support response [ID: 669690]

## Best Training Data (from linked URLs)

| Rank | Dataset | Size | Why It Matters |
|------|---------|------|---------------|
| 1 | jeannkouagou/aimo3-tool-integrated-reasoning | 141K traces | GPT-OSS-120B + Jupyter, exactly our pipeline |
| 2 | wenliangtlh/aimo3-high-difficulty-tool-calling-dataset | 7.3K problems, 70K trajectories | ONLY hard problems (≤7/8 pass). Targets 44→47 gap. |
| 3 | AIMO-Corpus/PolyMath (HuggingFace) | 11K problems | With per-model pass rates for difficulty filtering |
| 4 | ycchen/Crystal-Math-Preview (HuggingFace) | 4.2K problems | Pass-rate annotations at multiple reasoning budgets |

## Best Validation Sets

| Dataset | Size | Source |
|---------|------|--------|
| ritwikakancharla/aimo-3-benchmark | 196 eval + 204 CoT | Google DeepMind IMO-Bench |
| jordane95/aimo3-validation-benchmark | 347 verified | BeyondAIME/AMO-Bench/IMO-AnswerBench |
| zfturbo/hard-math-problems-for-aimo-3 | Aggregated | AIME/IMO/Nemotron-Math-v2 in CSV |

## Key Stat from Discussions
Tool-calling accuracy: **79.45% vs 75.77% without tools** — 3.68% absolute gain.
(From wenliangtlh's 8-sample study on hard problems with GPT-OSS-120B)

## Implications for Our Solver

1. **Don't change the model** — GPT-OSS-120B's MoE nature is a feature, not a limitation
2. **Focus on variance reduction** — more reliable answer extraction > smarter reasoning
3. **SymPy integration could help** — deterministic arithmetic for final answers
4. **Use 347-problem benchmark** for local eval instead of 10-problem reference set
5. **Qwen3.5 is future play** (AIMO4), not viable now due to vLLM incompatibility
6. **Double-run consistency** is rewarded — our deterministic seeding helps here
7. **Fine-tuning data exists in abundance** — 141K tool-calling traces ready to use
8. **Hard-problem targeting** is the strategy — wenliangtlh's ≤7/8 filter directly addresses our gap
