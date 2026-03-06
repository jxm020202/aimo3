# AIMO3 Research

ChatGPT deep research reports and compass artifacts, collected March 2-5, 2026.

| # | File | Date | Topic |
|---|------|------|-------|
| 1 | `01-aimo3-competition-landscape.md` | Mar 2 | Full competition overview: rules, prizes, timeline, leaderboard, top notebooks |
| 2 | `02-kaggle-notebook-oom-prevention.md` | Mar 4 | Preventing post-run OOM from output bloat, sandbox logging, vLLM metrics |
| 3 | `03-gpt-oss-120b-model-deep-dive.md` | Mar 4 | GPT-OSS-120B architecture (MoE 5.1B active), benchmarks, fine-tuning, known issues |
| 4 | `04-pushing-to-50-technical-playbook.md` | Mar 5 | Strategy playbook: GenSelect, PRM, category-aware prompting, SC-TIR |
| 5 | `05-reasoning-model-instruction-compliance.md` | Mar 5 | Why reasoning models ignore instructions (<25% compliance) + fixes |
| 6 | `06-few-shot-and-rag-for-math-reasoning.md` | Mar 5 | Few-shot harms RL models, RAG risks, context length tax, math taxonomy, embeddings |
| 7 | `07-forcing-tool-calls-on-reasoning-models.md` | Mar 5 | tool_choice on vLLM/Harmony (broken), constrained decoding, two-phase architecture |

## Key Findings

- **Few-shot hurts reasoning models** — zero-shot is strictly better (paper 6)
- **RAG is risky** — hard negatives worse than no context, 10-40% regression risk (paper 6)
- **Context budget: <500 tokens** — every token degrades performance monotonically (paper 6)
- **tool_choice broken for GPT-OSS-120B on vLLM** — only "auto" works, Harmony has no native forcing (paper 7)
- **No AIMO winner used RAG or tool_choice** — all used training-based TIR + majority voting (papers 5-7)
- **Pre-injected conversation turns** is the most practical approach for our setup (synthesis of all papers)
