# AI math competition solving: what works and what doesn't for AIMO 3

**The evidence is clear: for RL-trained reasoning models like DeepSeek-R1, QwQ-32B, and GPT-OSS-120B, less is more.** Few-shot prompting consistently degrades performance, RAG offers marginal gains on hard problems while risking significant regression, and every token of injected context carries a measurable performance tax. The winning AIMO-2 strategy—massive training data, tool-integrated reasoning, and solution selection—used none of these techniques at inference time. Below is a deep synthesis of the research across all five questions, with specific numbers and actionable recommendations for an AIMO 3 pipeline.

---

## 1. Few-shot prompting actively harms RL-trained reasoning models

The evidence is unanimous: **few-shot examples degrade math performance for reasoning-native models**. This holds across every model family tested and every benchmark examined.

DeepSeek's own technical report (arXiv:2501.12948, published in Nature) states plainly: "Few-shot prompting consistently degrades its performance. We recommend users directly describe the problem and specify the output format using a zero-shot setting." Microsoft's study of o1-preview (arXiv:2411.03590) isolated the few-shot component and found that 5-shot prompting caused a "significant decrease" in performance—zero-shot o1-preview outperformed GPT-4 running the full Medprompt framework (which includes dynamic few-shot, CoT, and ensembling). OpenAI's own API documentation recommends: "Try zero shot first, then few shot if needed." A systematic study by Cheng et al. (arXiv:2506.14641) used attention analysis to show that **models ignore exemplar reasoning content entirely** and attend primarily to instructions and the test query. Even "enhanced CoT exemplars" constructed from DeepSeek-R1 and Qwen2.5-Max outputs failed to improve reasoning.

The mechanism is straightforward: RL-trained models have internalized chain-of-thought through reinforcement learning. External examples compete with this native reasoning process, causing the model to mimic example patterns rather than deploying its superior internal strategies. One controlled experiment measured **85% → 70% accuracy** (a 15-point drop) when switching from zero-shot to few-shot on an RL model, while a supervised model improved from 78% → 82% under the same conditions.

**The format vs. technique distinction matters but doesn't save few-shot.** NVIDIA's AIMO-2 paper (arXiv:2504.16891) found that few-shot examples for Tool-Integrated Reasoning format compliance "turned out to be unsuccessful"—DeepSeek-R1 and QwQ-32B "struggle to deviate from their standard solution format." For technique transfer (e.g., showing Vieta's formulas application before a Vieta's problem), no paper has demonstrated a benefit for reasoning models, and the attention analysis evidence suggests models would ignore the worked example entirely. The sole remaining function of few-shot—output format alignment—fails for strongly RL-trained models and requires fine-tuning instead.

**Recommendation for AIMO 3:** Use zero-shot prompting exclusively. If technique hints are needed, inject them as brief instructions ("Consider using Vieta's formulas") rather than worked examples. Invest compute in majority voting across multiple solution samples rather than enriching single prompts.

---

## 2. RAG provides shallow help but introduces deep risks for competition math

The theoretical and empirical evidence converges on a sobering conclusion: **RAG primarily helps with shallow reasoning steps and actively risks degrading hard problem performance.**

The most relevant theoretical framework comes from "How Much Can RAG Help the Reasoning of LLM?" (arXiv:2410.02338), which models the reasoning process as a tree with fixed depth. Their key theorem shows that if a model can initially solve problems requiring reasoning depth *l*, RAG extends this to *l + c*, where *c* is a small constant. Unlike chain-of-thought (which can extend depth indefinitely), **RAG's "fission" effect primarily erases lower layers** of the reasoning tree—easier sub-problems. For olympiad problems requiring deep multi-step reasoning, this means RAG assistance is structurally limited.

The empirical numbers are modest. ARM-RAG on GSM8K showed improvement from **73.2% to 77.4%** (+4.2 points) using obfuscated structural retrieval. A formal-language RAG approach using Lean achieved **73% vs 54%** over standard text RAG on the Google Mathematics Dataset. But these are easy-to-moderate problems, not AIME-level.

The regression risk is the real concern. Multiple studies quantify the damage from injected context:

- **GSM-NoOp:** Up to **65% performance drop** when irrelevant numerical information is added to math problems—models consistently incorporate irrelevant numbers into calculations
- **PROBLEMATHIC** (arXiv:2406.15444): **~26% average relative performance drop** from adversarial irrelevant variables
- **GSM-DC:** Reasoning-specialized models decline **14-20 points** with distractors despite consuming 5× more tokens
- **MATH-Perturb** (arXiv:2502.06453): ICL with the original (unperturbed) problem and solution **actually hurts** on hard perturbations—"models may fail to recognize subtle differences and get misled by the demonstration"

A critical finding from "The Power of Noise" (arXiv:2401.14887, SIGIR 2024): **semantically related but incorrect documents are more harmful than completely random documents.** This means "hard negatives"—retrieved problems that look similar but differ subtly—are the most dangerous type of context for math reasoning, precisely the type a similarity-based retrieval system would surface.

The RetrievalPRM paper (arXiv:2502.14361) offers one nuance: for easy datasets like GSM8K, question-level retrieval suffices, but for harder datasets (OlympiadBench, OmniMATH), **step-level retrieval** providing fine-grained guidance becomes "significantly more crucial." No explicit regression rate has been published, but cross-referencing the evidence suggests **10-40% of previously correct problems could flip to incorrect** after context injection, depending on retrieval quality and problem difficulty.

**Recommendation for AIMO 3:** The NVIDIA winning approach (no RAG, massive training data + TIR + GenSelect) is the proven path. If RAG is used, apply it selectively—only on problems the model initially fails, with extremely high-precision retrieval, keeping injected text under 500 tokens. Use structural/obfuscated similarity matching rather than naive semantic similarity to reduce hard-negative risk.

---

## 3. Every injected token carries a measurable performance tax

The context length research reveals a counterintuitive finding: **even perfectly relevant, perfectly retrieved information degrades reasoning when it increases input length.**

"Context Length Alone Hurts LLM Performance Despite Perfect Retrieval" (arXiv:2510.05381, EMNLP 2025 Findings) tested five models (GPT-4o, Claude-3.7-Sonnet, Gemini-2.0, Llama-3.1-8B, Mistral-v0.3-7B) across GSM8K (math), MMLU, and HumanEval. The results are stark: **13.9%–85% performance degradation** as input extends to 30K tokens, even when retrieval is perfect. The most shocking sub-experiment: inserting only whitespace (zero semantic distraction) between evidence and question still caused **7–48% degradation** at 30K tokens. With complete attention masking (model attends only to evidence + question), a minimum **7.9% drop** persisted—meaning **positional distance alone** hurts performance, independent of any distraction.

The degradation curve is not a cliff but a consistent monotonic decline observable starting at **1K–5K inserted tokens**, accelerating between 5K and 15K. Open-source models degrade much faster than closed-source models, but all models degrade. The Chroma Research "Context Rot" study (July 2025), testing 18 frontier models including GPT-4.1 and Claude 4, confirmed: "Performance degrades at EVERY context length increment, not just near the limit."

The "Lost in the Middle" paper (Liu et al., 2024, TACL) established the **U-shaped positional bias**: models perform best when relevant information is at the beginning or end of context, with **>30% accuracy degradation** when it falls in the middle. In worst cases (20-30 document settings), performance drops **below the closed-book baseline**—meaning having no documents is better than having the answer buried in the middle.

For long-context models (64K+), degradation thresholds are **not proportionally higher**. Llama 4 Scout with a 10M token window shows reasoning degradation after just 128K–256K tokens. Effective context length remains far below nominal capacity due to positional under-training, softmax crowding, and attention dilution.

One mitigation shows promise: the "Retrieve then Recite" strategy—prompting the model to restate retrieved evidence before solving—improved Llama-3.1-8B by **up to 31.2%** on GSM8K and GPT-4o by up to 4%, by effectively converting a long-context task into a short-context one.

The practical context budget for math reasoning, synthesized across all evidence:

| Injected tokens | Expected impact | Guidance |
|---|---|---|
| **0–100** | Negligible | Safe for brief hints or theorem statements |
| **100–500** | Minimal (<3% degradation) | Acceptable for 1-2 concise technique references |
| **500–2,000** | Measurable (3-10%) | Use only with high-relevance content |
| **2,000–5,000** | Significant (10-25%) | Likely net-negative for competition math |
| **5,000+** | Severe to catastrophic | Actively counterproductive |

**Recommendation for AIMO 3:** Keep total non-problem context under **500 tokens**. Place the problem statement first (beginning gets strongest attention). If injecting technique references, place them immediately after the problem. Consider the "recite then solve" pattern. Never pad prompts with marginally relevant context.

---

## 4. No technique-level taxonomy exists at scale, but one can be built

**No existing dataset provides fine-grained technique-level tags (Vieta's formulas, Pigeonhole, CRT) at scale.** Every major dataset operates at the broad topic level or, at best, the sub-topic level. However, several partial sources can be combined.

The landscape of existing taxonomies breaks down by granularity:

The **MATH dataset** (Hendrycks et al., 12,500 problems) uses just 7 categories—three of which are algebra variants—with 5 difficulty levels. No technique tags. **NuminaMath** (~900K problems) has a `source` field reflecting data provenance (e.g., "cn_contest", "inequalities"), not mathematical content. **NVIDIA's OpenMathReasoning** (306K problems) uses only AoPS forum category tags like "aops_c6_high_school_olympiads"—no mathematical topic or technique classification whatsoever.

**Omni-MATH** (4,428 problems, ICLR 2025) offers the best sub-topic hierarchy: 7 major areas branching into **33+ sub-domains** (e.g., Prime Numbers, Modular Arithmetic, Plane Geometry, Sequences). Classification was done using GPT-4o. This is the strongest existing L2-level (sub-topic) taxonomy but still doesn't reach technique granularity.

The **CHAMP dataset** (Mao et al., ACL Findings 2024) is the single most relevant resource: 270 problems from Engel's "Problem-Solving Strategies," each annotated with **concepts** (~1.4 per problem, e.g., "Fermat's Little Theorem," "AM-GM inequality") and **hints** (~1.7 per problem, e.g., "Consider residues mod 3"). This is the only dataset with actual technique-to-problem mappings, but at only 270 problems, it's a seed, not a solution.

The **AoPS Wiki** contains hundreds of articles on individual techniques (Vieta's Formulas, Burnside's Lemma, Power of a Point) with extensive problem links, but the problem-to-technique mapping isn't structured—it lives in wiki hyperlinks, not a database. Arthur Engel's "Problem-Solving Strategies" provides the canonical 14-chapter strategy-level framework used by both Omni-MATH and CHAMP.

The practical path forward is a three-level taxonomy: **~6 L1 topics → ~40 L2 sub-topics (Omni-MATH backbone) → ~50-60 L3 technique tags** (built from CHAMP concepts + AoPS Wiki article titles + Engel's chapter sub-sections). GPT-4o has been validated for L2 classification by Omni-MATH, suggesting LLM-based auto-tagging of existing problem databases is feasible. Multi-label tagging is essential since most olympiad problems require 2-3 techniques. The sweet spot for retrieval is **~50-60 total tags**—enough for precision, few enough for reliable auto-classification.

---

## 5. Math embedding is an unsolved problem, but hybrid retrieval works

**No perfect math embedding model exists**, but practical solutions are available. The field is still developing—the MIRB benchmark (the first systematic evaluation of math information retrieval for embeddings) was published only in May 2025.

The only truly math-specific sentence embedding models are the **math-similarity** family (CICM'24): `math-similarity/Bert-MLM_arXiv-MP-class_zbMath` (~110M parameters), trained on 351K title pairs using Mathematics Subject Classification code similarity. These are available on HuggingFace, compatible with sentence-transformers, and designed specifically for mathematical text similarity. **MathBERTa** (`witiko/mathberta`, ~125M params) offers superior LaTeX tokenization (extended vocabulary with LaTeX math symbols) but requires fine-tuning for embedding tasks. The original **MathBERT** (Peng et al., arXiv:2105.00377) captures formula semantics via Operator Tree representations but isn't available as a ready-to-use sentence embedding.

General-purpose embeddings fail on math text in specific ways: LaTeX commands get split into meaningless subwords, notation equivalence is lost (`x^2 + 1` vs. "x squared plus one" produce distant embeddings), variable substitution is invisible (`f(x) = x²` vs. `g(t) = t²`), and structural differences in formulas aren't captured. The all-MiniLM-L6-v2 (22M params) handles topical matching acceptably but has significant quality gaps for math-specific similarity.

The MIRB benchmark reveals a critical finding: **cross-encoder rerankers generally hurt performance on math tasks.** Both bge-reranker-v2-m3 and jina-reranker-v2-base-multilingual degraded results, meaning the standard retrieve-then-rerank pipeline should skip reranking for math.

For a collection of 500-1,000 math problems, **BM25 is extremely competitive** and may be the single best approach. Math's distinctive vocabulary (theorem names, LaTeX tokens, specific terms like "eigenvalue" or "modular") plays to BM25's strengths in exact term matching. BM25 handles LaTeX tokens as exact strings, requires no GPU, and runs in under 1ms per query at this scale.

The recommended approach for AIMO 3:

| Rank | Model | Size | Rationale |
|---|---|---|---|
| 1 | **Hybrid BM25 + e5-base-v2** | 278M (dense) | Best cost/quality ratio; RRF fusion with k=60 |
| 2 | **math-similarity/Bert-MLM_arXiv-MP-class_zbMath** | 110M | Only math-specific sentence embedding; use alongside BM25 |
| 3 | **BAAI/bge-base-en-v1.5** | 109M | Strong MTEB results; well-tested general retrieval |
| 4 | **BM25 alone** | — | Surprisingly strong baseline; zero compute overhead |

Preprocessing is crucial: normalize LaTeX (strip display-only commands), add natural language descriptions alongside formulas, standardize variable names, and optionally use an LLM to generate topic summaries per problem for additional matching signal. At 500-1,000 documents, brute-force cosine similarity is instant—no vector index needed.

---

## Conclusion: the minimal-intervention strategy wins

The research converges on a counterintuitive conclusion for AIMO 3 pipeline design: **the most effective strategy is to do less, not more, at inference time.** Few-shot hurts. RAG helps marginally on easy problems but risks significant regression on hard ones. Every token of injected context degrades reasoning. The winning AIMO-2 approach—zero-shot prompting, tool-integrated reasoning, massive training data, and solution selection across many samples—used none of these augmentation techniques.

If building a retrieval component, the evidence supports an extremely conservative design: hybrid BM25 + small dense embeddings for retrieval, a ~50-tag technique taxonomy built from CHAMP + AoPS Wiki, strict 500-token context budgets, and selective application only on problems the model initially fails. The most impactful investment is **more solution samples with majority voting**, not richer prompts. For technique injection, a single-sentence instruction ("Consider the Chinese Remainder Theorem") likely outperforms a 500-token worked example—though even this remains empirically unvalidated for reasoning models.

Three genuinely novel insights emerge from this synthesis. First, the "recite then solve" pattern (up to 31.2% improvement on GSM8K) offers a way to have context without paying the full length tax—worth testing for AIMO 3. Second, structural/obfuscated similarity retrieval (ARM-RAG) outperforms semantic similarity by avoiding hard negatives, suggesting that if retrieval is used, problems should be matched by structure, not surface semantics. Third, the absence of any technique-level tagged dataset at scale represents both a gap and an opportunity—building a 50-tag taxonomy and auto-labeling 1,000 curated problems could provide a genuine competitive edge if the retrieval system is kept within the tight context budgets the evidence demands.