# Notes & Future Improvements

## Remaining Ideas

1. **Formal verification layer** — use SymPy to verify numerical answers satisfy constraints
2. **Per-problem-type prompting** — domain-specific hints for algebra/combinatorics/geometry/number-theory
3. **Strategy Retrieval Bank** — 1000 hard problems with insights, RAG at runtime, steer model toward correct approach. See strategies.md for details.

## Closed / Done

- [x] Test data collection (398 problems across val+aux+hard30)
- [x] GenSelect (7B trained + 120B zero-shot, dual judge)
- [x] Streaming summarization during R1
- [x] Wave 1 classifier + adaptive compute
- [x] Temperature schedule → settled on flat 0.5
- [x] Early stop analysis → proven broken, removed
