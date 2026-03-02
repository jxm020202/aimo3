# Model Landscape

## Primary: GPT-OSS-120B

- **Params**: 117B total, 5.1B active (MoE: 128 experts, 4 active per token)
- **License**: Apache 2.0
- **Context**: 130K tokens
- **Math**: 96.6% AIME 2024 w/ tools, 97.9% AIME 2025
- **AIMO3 reference bench**: 4/10 (only easy AIMO2-level problems 1-4, NONE of harder 5-10)
- **Fits on**: Single H100 80GB with fp8/MXFP4 quantization
- **Kaggle path**: `/kaggle/input/gpt-oss-120b/transformers/default/1`
- **Released**: August 2025, trained via large-scale distillation + RL
- **Long CoT**: Uses 20K+ CoT tokens on hard problems
- **Weakness**: Cannot solve IMO-level problems (the hard 6 in AIMO3)

## GPT-OSS-20B

- Smaller variant of GPT-OSS
- Matches or exceeds o3-mini on competition math
- Faster inference, could be used for verification or ensemble diversity
- Less capable on hardest problems

## DeepSeek-v3.1-terminus (thinking)

- **Params**: 671B
- **AIMO3 reference bench**: 9/10 — matched second-tier commercial models
- **Problem**: Likely too large for Kaggle H100 (80GB VRAM)
- **If it fits**: Would be a game-changer. Solves problems GPT-OSS-120B can't.
- **Key question**: Can we quantize to 4-bit or lower and still fit? 671B × 0.5 bytes = ~335GB — needs multi-GPU or extreme compression. Likely impractical on single H100.

## Qwen3-Next

- Enhanced reasoning capabilities, "thinking mode"
- Surpasses QwQ and Qwen2.5
- Qwen2.5-14B was AIMO2 winner's base model
- Good for ensemble diversity with GPT-OSS-120B

## DeepSeek-R1 Distilled Models

- Range: 1.5B to 70B
- Trained on 800K high-quality reasoning samples
- DeepSeek-R1-Distill-Qwen-14B was "overwhelmingly popular" in AIMO2
- DeepSeek-R1-Distill-Qwen-7B has AIMO3 notebook already
- Good for: fast verification model, ensemble member, reward model

## Benchmark: AIMO3 Reference Problems (pass@3)

| Model | Problems Solved (/10) | Type |
|-------|----------------------|------|
| GPT-5 Pro | 10 | Commercial |
| GPT-5.1 (high) | 10 | Commercial |
| GPT-5 (high) | 9 | Commercial |
| Grok-4 | 9 | Commercial |
| Gemini 2.5 Pro | 9 | Commercial |
| DeepSeek-v3.1-terminus (thinking) | 9 | Open-weight (671B) |
| GPT-OSS-120B | 4 | Open-weight (117B) |

**The gap**: Commercial models solve 9-10/10. Best practical open-weight (GPT-OSS-120B) solves only 4/10. DeepSeek-v3.1-terminus closes the gap but may not fit on Kaggle hardware.

## Model Cutoff Rule

Any AMLT used at runtime must be released before **March 15, 2026**. Models released after this date cannot be used in submissions. Models used only for data generation (not at runtime) have no cutoff.
