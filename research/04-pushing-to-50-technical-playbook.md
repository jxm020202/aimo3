# Pushing AIMO 3 from 43/50 to perfect: a complete technical playbook

**GPT-OSS-120B is already the strongest single model that fits on one H100, and no open-weight alternative comes close on AIME-level math.** The path to 50/50 lies not in swapping models but in layering advanced techniques around the current solver: GenSelect for answer selection (replacing or augmenting entropy-weighted voting), a sequential 7B PRM pipeline, category-aware prompting with differentiated tool strategies, and a Pairwise RM tournament for the hardest problems. This report synthesizes findings from AIMO 1 and 2 winner writeups, published papers on tool-integrated reasoning, HuggingFace model benchmarks, and available AIMO 3 competition intelligence.

The competition targets **110 IMO-level problems** with 5-digit integer answers on H100 hardware — substantially harder than AIME. OpenAI's o3-preview scored 50/50 on AIMO 2's public set, proving perfect scores are achievable. The gap between the current 42–46/50 and 50/50 almost certainly comes from the **7–8 hardest problems** where the model either applies wrong techniques, fails to explore enough solution paths, or selects the wrong answer from a correct candidate pool.

---

## Model landscape: GPT-OSS-120B has no viable open-weight rival

GPT-OSS-120B (117B total parameters, **5.1B active** per token, MoE architecture) achieves **96.6% on AIME 2024** and **97.9% on AIME 2025** with tool use — scores that dwarf every open alternative. It runs on a single H100 80GB via MXFP4 quantization at roughly **58GB** of VRAM, leaving ~22GB for KV cache.

The model alternatives break down as follows. **Qwen3-235B-A22B** cannot fit on a single H100 at any useful quantization — even at aggressive 2-bit, all 235B parameters must reside in VRAM regardless of MoE activation sparsity, requiring ~448GB at FP16. At Q2/IQ2 (~70–80GB) there would be zero KV cache headroom and severe quality degradation. Its AIME 2025 score of **81.5%** is 16 points below GPT-OSS-120B anyway. **QwQ-32B** fits easily (64GB BF16 or 32GB INT8) and leads the 32B class at **79.5% AIME 2024**, but still trails GPT-OSS-120B by 17 points. **DeepSeek-R1-Distill-Qwen-32B** (72.6% AIME 2024) and **DeepSeek-R1-Distill-Llama-70B** (70.0%) are weaker still — the 70B model actually scores lower than the 32B distillation despite double the parameters. **Qwen2.5-Math-72B-Instruct** is a pre-reasoning-era model scoring just ~30% greedy on AIME 2024; it has been thoroughly superseded. **Sky-T1-32B** at 43.3% is not competitive.

The most interesting secondary model is **Qwen3-30B-A3B-Thinking-2507**, which scores **85.0% on AIME 2025** with only 3B active parameters. At FP8 it consumes ~30GB, making it extremely fast for verification or second-opinion generation. The model referenced as **"Qwen3-Next"** in the AIMO 3 announcement is actually **Qwen3-Next-80B-A3B** — a completely different architecture from Qwen3-235B, using hybrid Gated DeltaNet + Gated Attention with 512 MoE experts. It has 80B total parameters but only **3B active**, fits in ~50GB quantized, and claims 10x speed improvement over standard transformers. This is worth monitoring closely as a potential co-model.

### Running two models on one H100

vLLM does not natively support multiple models in a single server instance, but you can run **two separate vLLM instances** on the same GPU using the `--gpu-memory-utilization` flag to partition VRAM. The most practical pair for your setup is **GPT-OSS-120B (MXFP4, ~58GB) + a tiny verifier** like Qwen2.5-Math-PRM-7B (~4GB quantized). Alternatively, if you were willing to drop GPT-OSS-120B, the combination of **QwQ-32B INT4 (~16GB) + Qwen3-30B-A3B FP8 (~30GB)** leaves ~34GB for KV caches and gives two independent strong reasoners. However, given GPT-OSS-120B's massive accuracy advantage, the recommended approach is to keep it as the primary solver and use remaining VRAM for a lightweight PRM in a sequential pipeline.

---

## GenSelect is the single highest-leverage technique you're not using

The AIMO 2 winning team (NVIDIA NemoSkills, 34/50 private) identified **Generative Solution Selection (GenSelect)** as their most impactful innovation, significantly outperforming majority voting. GenSelect works by presenting multiple candidate solution *summaries* to a reasoning model in a single prompt and asking it to reason about which is correct, outputting the index of the best candidate. For inference, the team sampled subsets of 16 solutions from a pool of 64, ran GenSelect 64 times with random permutations, then performed **majority voting over the GenSelect-selected answers** (majority@8 over outputs).

Critically, the standalone GenSelect paper (arXiv:2507.17797) demonstrates that **reasoning models like QwQ-32B and DeepSeek-R1 can perform GenSelect out of the box with simple prompting** — no fine-tuning required. This means you can implement GenSelect immediately with GPT-OSS-120B itself acting as both generator and selector, or use a secondary model for selection. The NVIDIA team trained dedicated GenSelect capability via SFT on 566K examples, but even prompted GenSelect substantially outperforms both majority voting and traditional reward model scoring.

**Recommended implementation for your pipeline:** After generating 16 parallel attempts, create structured summaries of each solution's approach and final answer. Present groups of 8 summaries to GPT-OSS-120B with a prompt asking it to identify the correct solution through reasoning. Run this selection multiple times with shuffled orderings and take the majority of selected answers. This replaces or augments your current entropy-weighted voting and directly addresses the scenario where the correct answer exists in your candidate pool but is outvoted by a more common wrong answer.

---

## Process reward models add value but have sharp limits on olympiad problems

**Math-Shepherd PRM** (Mistral-7B based, ~14GB FP16 or ~4GB quantized) fits alongside GPT-OSS-120B and consistently outperforms majority voting — improving DeepSeek-67B from base accuracy to **93.3% GSM8K** and **48.1% MATH** with 256-candidate verification. **Qwen2.5-Math-PRM-7B** similarly outperforms maj@8 by an average **1.4%** across math tasks and beats GPT-4o on the ProcessBench error identification benchmark.

However, there is a critical caveat: on **Hard2Verify** (frontier/olympiad-level math), even the 72B Qwen PRM drops from 78.3% to just **37.3%** accuracy. Small 7B PRMs will perform worse. PRMs are trained predominantly on GSM8K/MATH-level reasoning traces, and their error detection degrades significantly on the creative, multi-step reasoning characteristic of IMO-level problems.

**Pairwise Reward Models** offer a more promising approach for hard problems. The Pairwise RM (arXiv:2501.13007), trained on Qwen2.5-7B-Instruct, evaluates two candidates simultaneously through chain-of-thought comparison and runs a knockout tournament. It achieves **40–60% relative improvement** over standard PRMs on the hardest 50% of problems and outperforms every tested ORM and PRM on Olympiad Bench by **3.9 absolute points**. This approach is particularly well-suited to your setup: after generating 16 candidates, run a tournament of pairwise comparisons using either a dedicated Pairwise RM or GPT-OSS-120B itself in pairwise-comparison mode.

**Self-verification — asking the model to check its own answer — is unreliable.** Research by Tyen et al. (ACL 2024) shows LLMs achieve only ~52.9% accuracy at finding reasoning errors. Huang et al. (ICLR 2024) demonstrated that self-correction without external feedback actually **degrades performance** as correct answers flip to incorrect. Your rerun logic with structured summaries is far more effective than naive self-verification because it provides external signal (prior attempt outcomes) rather than asking the model to introspect.

### Practical PRM integration on single H100

The recommended architecture is **sequential, not simultaneous**: generate all 16 candidate solutions with GPT-OSS-120B at full VRAM utilization, then unload (or reduce memory) and load a 7B PRM for rapid scoring. PRM scoring is a single forward pass per solution — not autoregressive generation — so scoring 16 solutions takes roughly **10–30 seconds** with batching, versus minutes for generation. Total PRM overhead is approximately 5–10% of pipeline time. Load with HuggingFace `transformers` rather than a second vLLM instance for simpler memory management.

---

## SC-TIR architecture and the optimal code execution recipe

**SC-TIR** (Self-Consistency Tool-Integrated Reasoning), which won AIMO 1, combines multiple TIR trajectories with majority voting. The algorithm generates **N candidate trajectories** (NuminaMath used N=48), each involving up to **M=4 rounds** of interleaved natural-language reasoning and Python code execution. If code execution produces a traceback, the error is fed back to the model for self-correction in the next round. Ill-formed responses are pruned before majority voting. The winning team found that increasing beyond N=48 or M=4 provided no further benefit.

**TORA** (Tool-Integrated Reasoning Agent, ICLR 2024) established the interleaved format that SC-TIR builds upon. Its key insight is that neither pure chain-of-thought nor pure code generation is optimal — the model should write natural language reasoning, then a code block for computation, receive execution output, continue reasoning, and iterate. TORA's error analysis found **45% of failures** come from reasoning errors (not code errors), suggesting that improving the model's mathematical reasoning matters more than improving code execution mechanics.

**Optimal turn count research converges on 4–6 code execution cells per problem.** Beyond this, returns diminish sharply. The model should use code for computation, enumeration, equation solving, and numerical verification, but reason verbally for abstract arguments, proof structure, case analysis, and insight generation. If the code approach has failed twice on the same sub-problem, the model should switch strategies entirely rather than retry.

### Python sandbox: beyond sympy and numpy

The most impactful additions to your sandbox are **z3-solver** (Microsoft's SMT solver) for constraint satisfaction and Diophantine equations, **mpmath** for arbitrary-precision arithmetic (critical for geometry problems where you need to verify whether a computed value is an integer), and **networkx** for graph-theoretic combinatorics problems. SageMath is not available in Kaggle kernels.

Key library recommendations by problem type:

- **sympy.ntheory**: `factorint()`, `crt()` for CRT, `totient()`, `multiplicity()` for p-adic valuations, `discrete_log()`, `primitive_root()`
- **z3-solver**: Integer constraint satisfaction (`Solver()`, `Int()`, `And()`, `ForAll()`), enumerating all solutions with a `while s.check() == sat` loop, proof by contradiction
- **scipy.optimize.milp**: Mixed-integer linear programming for optimization-flavored combinatorics
- **itertools + functools.lru_cache**: Brute-force enumeration (feasible when search space < 10⁷) and memoized dynamic programming

### Systematic failure mitigations

The most dangerous failure modes are **sympy.solve() hanging** on complex polynomial systems (mitigation: wrap with 5–10 second timeout via `signal.alarm()`, fall back to `scipy.optimize.fsolve` or `nsolve`), **sympy.simplify() exponential blowup** on trigonometric expressions (mitigation: use targeted `trigsimp()`, `ratsimp()`, `cancel()` instead of generic `simplify()`), and **numpy integer overflow** (mitigation: always use Python native `int` for number theory, never `np.int64`). For infinite loops in generated code, enforce a **10–30 second execution timeout** per cell with try/except wrapping. Python's built-in `pow(a, b, mod)` is the single most important function for competition number theory — it handles arbitrary precision modular exponentiation in O(log b) time.

---

## Category-specific strategies deliver measurable gains

Research from arXiv 2411.00042 directly measured optimal strategy weights by problem category:

**Geometry** should use **90% chain-of-thought reasoning, 10% code**. LLMs consistently perform worst on geometry across all studies — even DeepSeek-V3 shows its lowest scores here. For the 10% where code helps, the coordinate bash pattern works: place triangle vertices strategically (A=(0,0), B=(c,0), C=(x,y) to reduce degrees of freedom), compute symbolically or with mpmath at **50+ decimal places**, and check whether the result is close to an integer. Complex number representations of points are particularly elegant for collinearity, concyclicity, and rotation problems. The key failure mode is symbolic expression explosion — switch to numerical verification with mpmath when symbolic computation exceeds 5 seconds.

**Combinatorics** should use **65% code, 35% reasoning** — the highest code proportion of any category. When the search space is below 10⁷, brute-force enumeration via `itertools.product` or `itertools.combinations` is both fast and reliable. Dynamic programming with `@lru_cache` handles recursive counting problems efficiently. For graph problems, `networkx` provides shortest paths, chromatic numbers, matchings, and clique detection. The critical distinction is between problems where parameters are small enough for enumeration versus those requiring closed-form insight — the model should estimate this before choosing an approach.

**Algebra and number theory** split **50/50 between reasoning and code**. For algebra, always declare `symbols('x', real=True)` to avoid sympy returning spurious complex solutions. For number theory, the `sympy.ntheory` module provides `crt()` for the Chinese Remainder Theorem, `factorint()` for factorization, and `multiplicity()` for p-adic valuations. Models frequently misapply the Lifting the Exponent Lemma by forgetting its preconditions (p | a-b but p ∤ a and p ∤ b) — having the code verify conditions before applying theorems is a reliable mitigation.

### Problem difficulty classification improves compute allocation

Having the model estimate difficulty before solving enables **adaptive compute budgets**: allocate more parallel attempts and longer timeouts to harder problems. The AIMO 2 second-place team implemented a dynamic speed adjustment module that monitors remaining time and adjusts both sample count and early-stopping thresholds. Their question-level early stopping terminates generation when approximately **70% of samples agree** (e.g., 5/7 or 7/10), freeing compute for harder problems. This dovetails with your tiered time management — route easy problems through fewer attempts with aggressive early stopping, and concentrate remaining budget on the hardest 5–10 problems.

---

## What top AIMO teams actually do: lessons from three competition cycles

**AIMO 1 winner (NuminaMath, 29/50):** Fine-tuned DeepSeekMath-7B on 860K math problems (CoT) then 70K TIR examples. Used SC-TIR with N=48 candidates and M=4 depth. No reward model — pure majority voting with pruning.

**AIMO 2 winner (NVIDIA NemoSkills, 34/50):** Fine-tuned Qwen2.5-14B on 540K problems with 3.2M CoT solutions and 1.7M TIR solutions (the OpenMathReasoning dataset). The decisive innovation was **GenSelect** — training the model to select the best solution from candidates, which significantly outperformed majority voting. Inference used temperature 0.6, top-p 0.95, max 32K tokens, 64 generations per problem. On unconstrained 8×H100, they reached 35/50.

**AIMO 2 runner-up (imagination-research, 31/50 private, 34/50 public):** Used SFT + DPO training, dynamic speed adjustment with three tiers, and question-level early stopping at 70% agreement. On unconstrained hardware, also reached 35/50 — matching the winner.

**AIMO 3 current state:** GPT-OSS-120B dominates public notebooks. A notebook titled "[43/50] AIMO 3: gpt-oss-120b weighted entropy" represents the known best public score, using entropy-weighted voting similar to your approach. Agentic solver notebooks suggest teams are exploring multi-step tool-use architectures. The competition provides H100 GPUs and explicitly mentions GPT-OSS-120B and Qwen3-Next as target models. Fine-tuning is allowed, with up to 128 H100s available for select participants through the Fields Model Initiative partnership.

**The o3-preview benchmark** scored **50/50** on AIMO 2's public test set (high-compute mode), proving perfect scores are achievable on this problem distribution. The gap between o3-preview low-compute (43/50) and high-compute (50/50) came entirely from additional test-time compute — more samples, longer reasoning chains, and better selection.

---

## Concrete recommendations for reaching 50/50

The 7–8 problems you're currently missing likely fall into specific failure categories. Based on the research, here is a prioritized action plan:

**Implement GenSelect immediately.** This is zero-cost in terms of model changes. After generating 16 attempts, create concise summaries of each solution's method and answer. Prompt GPT-OSS-120B to select the best solution from groups of 8 summaries, repeating with shuffled orderings. Take majority vote over selected answers. This specifically addresses the failure mode where the correct answer exists in your candidate pool but loses to a more popular wrong answer — a scenario entropy-weighted voting handles poorly when the correct solution has lower confidence.

**Add a sequential 7B PRM pass.** After generation, load Qwen2.5-Math-PRM-7B (~4GB quantized) to score all 16 reasoning traces. Use PRM scores as additional signal alongside GenSelect and entropy-weighted voting. The overhead is ~30 seconds per problem. On Olympiad-level problems, consider **Pairwise RM-style tournament comparison** instead of pointwise scoring — research shows 40–60% relative improvement on the hardest problems.

**Differentiate tool strategy by category.** Add a classification step that routes geometry problems to CoT-heavy prompts (with coordinate bash fallback), combinatorics to code-heavy prompts (with brute-force enumeration when feasible), and algebra/number theory to balanced prompts. Include category-specific library hints in your SQLite technique database: z3-solver patterns for constraint problems, `sympy.ntheory.modular.crt()` for CRT problems, `mpmath` precision settings for geometry numerical verification.

**Harden the code execution sandbox.** Wrap all sympy operations in **5–10 second timeouts**. Replace generic `simplify()` calls with targeted simplification functions. Enforce `symbols('x', real=True)` by default. Add `mpmath` with `mp.dps=50` for numerical verification of all computed answers — if the result should be an integer, check `abs(result - round(result)) < 1e-10`. Pre-install z3-solver for constraint satisfaction problems.

**Implement adaptive early stopping.** When 70%+ of samples agree (e.g., 12/16), stop and reallocate compute to unsolved problems. Track remaining time dynamically and adjust both sample count and timeout thresholds. This alone freed significant compute for the AIMO 2 runner-up team, who matched the winner's unconstrained score.

**For the rerun logic**, feed not just structured summaries but explicit **error categorization**: "Attempt 3 failed because sympy.solve() timed out on the polynomial system" or "Attempts 1, 5, 9 all got answer 42 but attempts 2, 7 got 37 — investigate the discrepancy." This gives the model actionable signal rather than just outcome data. Consider having the rerun specifically try an alternative approach (coordinate bash if synthetic geometry failed, numerical brute force if symbolic algebra failed).

The theoretical ceiling is clear: o3-preview achieves 50/50 with sufficient test-time compute. Your architecture is sound. The remaining gains come from **better answer selection** (GenSelect + PRM), **category-aware tool use**, and **smarter compute allocation** across the 110-problem set.