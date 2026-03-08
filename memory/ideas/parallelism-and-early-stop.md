# Parallelism & Early Stop — Settled

## Key Finding: Early Stop Never Worked
All attempts launch simultaneously via ThreadPoolExecutor. `stop_event.set()` fires but all attempts are already mid-inference on GPU. Post-ES attempts take identical wall time. **Early stop saves ZERO time.** Removed from code in v24.

## GPU KV Cache (H100 80GB)
- Available KV cache: 8.01 GiB = 233,296 tokens
- 24 attempts at median usage (5K tokens each) = 120K/233K = fits comfortably
- At P90 usage (16K tokens): 384K/233K = queuing likely → but we use 24 workers and it works fine in practice

## Wave-Based Batching: DEAD
Tested: 707 min vs 313 min all-parallel. 2x slower. GPU has zero queuing overhead with 24 concurrent.

## Current Config
- 24 attempts, 24 workers, all-parallel, flat temp 0.5
- No early stop, no batching, no waves
