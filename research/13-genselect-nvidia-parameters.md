# GenSelect & NVIDIA Parameter Reference

## Sources
- **GenSelect paper**: arXiv:2507.17797 — "GenSelect: A Generative Approach to Best-of-N" (Toshniwal et al., ICML 2025 AI4Math Workshop)
- **AIMO-2 paper**: arXiv:2504.16891 — "AIMO-2 Winning Solution" (Moshkov et al.)

## NVIDIA's Exact Parameters

### Solution Generation
- temp=0.6-0.7, top-p=0.95, max 16384-32768 tokens
- Up to 32 candidates per problem (AIMO-2) or 64 (GenSelect paper)
- Kaggle submission used temp=0 (greedy) with ReDrafter speculative decoding

### GenSelect Judge
- temp=0.6, top-p=0.95 (same as generation — no differentiation)
- Judge models: QwQ-32B, DeepSeek-R1-0528 (both zero-shot, simple prompting)
- N=8 passes with random solution permutations, majority vote over selected answers
- Trained 7B model also works well (AIMO-2 trained on 566K GenSelect traces)

### GenRM (Pointwise Verification)
- temp=0.6 ("We sample multiple verifications from QwQ at a temperature of 0.6")
- Binary Yes/No output

### Summary Generation
- Model: Qwen2.5-32B-Instruct (not the reasoning model)
- Max 2048 tokens output
- 4 candidate summaries per solution, pick longest where \boxed{answer} matches
- "No significant benefit from complete reasoning traces compared to summaries"

### Stability Results (GenSelect Paper Table 4)
| N (comparison size) | GenSelect@1 | GenSelect@8 |
|---|---|---|
| 2 | 72.1 | 73.4 |
| 4 | 72.6 | 73.0 |
| 8 | 72.3 | 73.4 |
| 16 | 72.1 | 73.4 |

GenSelect is remarkably stable across different N values and number of passes.

### GenSelect Scaling (AIMO-2 Paper Figure 2)
- Most accuracy gains come at small N (2-8 solutions)
- Becomes unstable with >32 generations in a single prompt
- For >16 solutions: use N-ary knockout tournament (bracket-style)
- For inference: subsets of 16 from 64 solutions, repeated 64 times, majority vote

## Key Design Decisions

### What NVIDIA DID NOT do in Kaggle submission
- Did NOT use GenSelect inference (time constraints)
- Used temp=0 greedy + ReDrafter for diverse generation
- "experimented with various sampling parameters but observed minimal differences"

### Time Management (AIMO-2 Kaggle)
- 350s base per problem
- Unused time → shared buffer
- Max 560s per problem (350 + 210 buffer)
- Early stopping: cancel remaining if first 4-5 agree

### Code Execution Limits
- Max 6 code calls per generation
- 2s timeout per execution
- First 200 chars of output shown back to LLM

## Prompt Templates

### GenSelect Prompt (Figure 2)
```
You will be given a challenging math problem followed by {num_solutions} solutions.
Your task is to systematically analyze these solutions to identify the most
mathematically sound approach.

Input Format:
Problem: A complex mathematical word problem at advanced high school or college level
Solutions: Detailed solutions indexed 0-{max_idx}, each concluding with an answer in \boxed{} notation

YOUR TASK
Problem: {problem}
Solutions: {solutions}

Evaluation Process:
1. Initial Screening
- Group solutions by their final answers
- Identify and explain mathematical contradictions between different answers
- Eliminate solutions with clear mathematical errors

2. Detailed Analysis
For remaining solutions, evaluate:
- Mathematical precision and accuracy
- Logical progression of steps
- Completeness of mathematical reasoning
- Proper use of mathematical notation, including \boxed{}
- Handling of edge cases or special conditions
- For solutions containing and addressing errors, evaluate the error identification and correction methodology.

3. Solution Comparison
Compare viable solutions based on:
- Efficiency of approach
- Clarity of mathematical reasoning
- Sophistication of method
- Robustness of solution (works for all cases)

Your response should include:
1. Brief analysis of conflicting answers
2. Detailed evaluation of mathematically sound solutions
3. Justification for eliminating incorrect solutions
4. Clear explanation for selecting the best approach

End your evaluation with exactly:
Judgment: [IDX]
where IDX is the index 0-{max_idx} of the best solution.
```

### Summary Prompt (Appendix A.1)
```
I will give you a math problem and a long solution to that problem exploring
different approaches, making mistakes along the way, correcting them, switching
around and so on. But eventually that solution gets to the right approach and solves
the problem. Your task is to write a clean version of the final correct solution
without all the exploration. Cover all the details of the final solution.

Problem: {problem}
Solution: {generation}

Now write a clean version of the final correct solution without all the exploration
but cover all the details of the final solution.
```

## Implications for Our Setup

### What to match:
- temp=0.6, top-p=0.95 for R1 generation (we had [0.2-0.4], way too low)
- temp=0.6 for GenSelect judges (we already had 0.6 — correct!)
- 8 passes with permutation + majority vote (we have this)
- Summary: max 2048 tokens, pick longest valid (we match this exactly)

### What we do differently:
- We use min_p=0.05 instead of top-p=0.95 (different sampling strategy, similar effect)
- We use 120B (GPT-OSS) as judge instead of QwQ-32B — much larger, Qwen2.5-based
- We use trained 7B as second judge (dual judge) — NVIDIA only used self-GenSelect
- We use streaming summarization (during R1) — NVIDIA did batch post-hoc
- Our rerun adds expert context from judges — NVIDIA didn't do reruns with GenSelect

### Recommended parameter alignment:
| Layer | Current | NVIDIA | Recommendation |
|---|---|---|---|
| R1 generation | normal(0.3,0.05)→[0.2,0.4] | 0.6-0.7, top-p=0.95 | **0.6 flat** |
| Rerun | same schedule | temp=0 (greedy) | **0.3** (has expert context) |
| Summarizer | 0.3 | Qwen2.5-32B-Instruct | **0.3** (keep) |
| GenSelect 7B | 0.6 | N/A (trained model) | **0.6** (keep) |
| GenSelect 120B | 0.6 | 0.6 (QwQ zero-shot) | **0.6** (keep) |
