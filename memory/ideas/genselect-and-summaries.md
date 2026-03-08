# GenSelect & Summarization Pipeline

## Current Implementation (v38+)

### Streaming Summarization (NVIDIA-aligned)
- During R1, as each attempt finishes, immediately submit to 120B vLLM for summarization
- 4 concurrent summarization slots via ThreadPoolExecutor
- Uses `_SUMMARIZE_PROMPT` (from NVIDIA's `summarize-solution.yaml`)
- Each summary: max 2048 tokens, temp 0.3, ReasoningEffort.MEDIUM
- Validation: \boxed{answer} must match original → falls back to raw trace on mismatch
- Input traces > 6000 chars truncated (first 3000 + last 3000)
- Summaries overlap with remaining R1 work → practically free wall time

### GenSelect Judge Pipeline
1. R1 produces 24 attempts with answers
2. Streaming summaries collected into `self._cached_summaries`
3. `_build_genselect_solutions()` groups by answer cluster, for each:
   - Finds all cached summaries with matching answer
   - Picks the **longest valid summary** (NVIDIA's exact criterion)
   - Falls back to raw trace with smart truncation if no summary available
4. Both judges (7B + 120B) receive the **same** solution text
5. Dual GenSelect runs in parallel (ThreadPoolExecutor(2)):
   - 7B trained (OpenReasoning-Nemotron-7B-BNB4): 8 passes
   - 120B zero-shot (GPT-OSS via vLLM): 8 passes
6. 3-way decision: majority vote + 7B + 120B → consensus or rerun

### Rerun Path
- Rerun attempts don't get streaming summaries (only R1 does)
- For rerun GenSelect, clusters will use summaries from R1 attempts if available,
  raw traces for R2-only answer clusters

## Future Idea: Additive Summaries Per Answer (User's Concept)

### Problem with Current Approach
Current: pick ONE representative attempt per cluster (the best), summarize it.
This loses information from other attempts that solved the same problem differently.

### Additive Approach
Instead of picking a single representative, the summarization agent **accumulates knowledge** across all attempts with the same answer:

1. As R1 attempts finish, the summarizer groups by answer
2. For each answer cluster, it builds a **cumulative summary**:
   - First attempt with answer X → base summary describing approach A (e.g., brute force enumeration)
   - Second attempt with answer X → adds approach B if different (e.g., analytical derivation)
   - Third attempt with answer X → adds verification if it confirms via different method
3. The final summary for each answer mentions **all distinct approaches** used:
   - "This answer was reached via: (1) direct computation using modular arithmetic, (2) brute force enumeration confirming the pattern, (3) generating function approach"
4. This gives the GenSelect judge MORE evidence — not just one solution path but multiple independent validations

### Tradeoffs
- **Pro**: Richer signal for GenSelect — multiple independent paths to same answer = stronger evidence
- **Pro**: GenSelect can better judge which answer cluster has more rigorous/diverse validation
- **Con**: More complex summarization logic
- **Con**: Cumulative summary grows with cluster size — needs budget management
- **Con**: Requires the summarizer to compare approaches (not just transcribe)

### Implementation Notes
- Could use the 120B itself to merge summaries: "Here is a solution summary. Here is another attempt at the same problem reaching the same answer. If it uses a meaningfully different approach, add it to the summary. Otherwise skip."
- Cap at ~3000 chars per cluster summary to fit GenSelect prompt budget
- Only worth doing for large clusters (5+ votes) — small clusters already have limited diversity

### Status: IDEA — not implemented. Current streaming approach (one-best-per-cluster) follows NVIDIA's proven methodology.
