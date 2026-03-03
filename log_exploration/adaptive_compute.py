#!/usr/bin/env python3
"""
AIMO3 Adaptive Compute Allocation Analyzer
============================================
Answers: "How should we allocate 5 hours across 50 problems?"

Analyzes v22 diagnostic.log to determine:
1. Can we predict easy/hard from first 2-3 attempts?
2. What's the optimal attempt cutoff per difficulty class?
3. How much compute is wasted (redundant correct, hopeless Nones)?
4. What's the concrete wave-based batching config for v24?

Usage:
    python log_exploration/adaptive_compute.py [logfile]
    (default: output/v22/diagnostic.log)
"""

import sys
import os
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def early_signal_detection(problems):
    """Can we predict easy/hard from the first N attempts?"""
    print("=" * 70)
    print("  1. EARLY SIGNAL DETECTION")
    print("     Can we predict problem difficulty from first 2-3 attempts?")
    print("=" * 70)

    # For each problem, simulate what we'd know after N attempts
    for n_early in [2, 3, 4]:
        print(f"\n  After first {n_early} attempts:")
        print(f"  {'Signal':<30} {'Total':>6} {'Final OK':>9} {'Final WRONG':>11} {'Precision':>10}")
        print(f"  {'─'*30} {'─'*6} {'─'*9} {'─'*11} {'─'*10}")

        signals = {
            'all_correct': {'total': 0, 'final_ok': 0, 'final_wrong': 0},
            'majority_correct': {'total': 0, 'final_ok': 0, 'final_wrong': 0},
            'any_correct': {'total': 0, 'final_ok': 0, 'final_wrong': 0},
            'all_none': {'total': 0, 'final_ok': 0, 'final_wrong': 0},
            'any_answer': {'total': 0, 'final_ok': 0, 'final_wrong': 0},
            'no_answer': {'total': 0, 'final_ok': 0, 'final_wrong': 0},
            'high_agreement': {'total': 0, 'final_ok': 0, 'final_wrong': 0},
            'low_entropy_avg': {'total': 0, 'final_ok': 0, 'final_wrong': 0},
        }

        for p in problems:
            if len(p.attempts) < n_early:
                continue
            early = p.attempts[:n_early]

            early_answers = [a.answer for a in early if a.answer is not None]
            early_nones = sum(1 for a in early if a.is_none)
            early_entropies = [a.entropy for a in early if a.entropy < float('inf')]
            avg_entropy = sum(early_entropies) / max(len(early_entropies), 1)

            final_ok = p.correct

            # Signal: all early attempts got correct answer
            if early_answers and all(a == p.expected for a in early_answers) and len(early_answers) == n_early:
                signals['all_correct']['total'] += 1
                signals['all_correct']['final_ok' if final_ok else 'final_wrong'] += 1

            # Signal: majority of early answers are correct
            if early_answers:
                correct_count = sum(1 for a in early_answers if a == p.expected)
                if correct_count > len(early_answers) / 2:
                    signals['majority_correct']['total'] += 1
                    signals['majority_correct']['final_ok' if final_ok else 'final_wrong'] += 1

            # Signal: any correct answer in early attempts
            if any(a == p.expected for a in early_answers):
                signals['any_correct']['total'] += 1
                signals['any_correct']['final_ok' if final_ok else 'final_wrong'] += 1

            # Signal: all early attempts returned None
            if early_nones == n_early:
                signals['all_none']['total'] += 1
                signals['all_none']['final_ok' if final_ok else 'final_wrong'] += 1

            # Signal: any answer produced (not all None)
            if early_answers:
                signals['any_answer']['total'] += 1
                signals['any_answer']['final_ok' if final_ok else 'final_wrong'] += 1
            else:
                signals['no_answer']['total'] += 1
                signals['no_answer']['final_ok' if final_ok else 'final_wrong'] += 1

            # Signal: high agreement (all answers same)
            if early_answers and len(set(early_answers)) == 1 and len(early_answers) >= 2:
                signals['high_agreement']['total'] += 1
                signals['high_agreement']['final_ok' if final_ok else 'final_wrong'] += 1

            # Signal: low average entropy
            if early_entropies and avg_entropy < 0.5:
                signals['low_entropy_avg']['total'] += 1
                signals['low_entropy_avg']['final_ok' if final_ok else 'final_wrong'] += 1

        for sig_name, counts in signals.items():
            t = counts['total']
            if t == 0:
                continue
            ok = counts['final_ok']
            wrong = counts['final_wrong']
            precision = ok / t * 100
            print(f"  {sig_name:<30} {t:>6} {ok:>9} {wrong:>11} {precision:>9.1f}%")

    # Recommend best early classifier
    print(f"\n  RECOMMENDATION:")
    print(f"  After 3 attempts:")
    print(f"    EASY (stop): all 3 answered + all agree → safe to stop, nearly 100% precision")
    print(f"    HARD (continue): 0 answers (all None) → definitely needs more attempts")
    print(f"    MEDIUM: mixed signals → run more attempts")


def optimal_attempt_cutoffs(problems):
    """What's the marginal value of each additional attempt?"""
    print(f"\n{'=' * 70}")
    print("  2. MARGINAL VALUE OF ADDITIONAL ATTEMPTS")
    print("     Score if we stopped after N attempts")
    print("=" * 70)

    max_attempts = max(len(p.attempts) for p in problems)

    print(f"\n  {'Cutoff':>7} {'Score':>7} {'%':>6} {'Delta':>6} {'Avg Time':>9} {'Total Time':>11} {'Saved vs Max':>13}")
    print(f"  {'─'*7} {'─'*7} {'─'*6} {'─'*6} {'─'*9} {'─'*11} {'─'*13}")

    prev_score = 0
    max_time = sum(p.wall_time for p in problems)

    for cutoff in range(1, max_attempts + 1):
        score = 0
        total_time_est = 0.0

        for p in problems:
            early = p.attempts[:cutoff]
            if not early:
                continue

            # Simulate voting with only first N attempts
            answers = [a.answer for a in early if a.answer is not None]
            if answers:
                # Simple majority vote
                vote_counter = Counter(answers)
                predicted = vote_counter.most_common(1)[0][0]
                if predicted == p.expected:
                    score += 1

            # Estimate time: max of first N attempt times (they run in parallel)
            attempt_times = [a.time_s for a in early if a.time_s > 0]
            if attempt_times:
                total_time_est += max(attempt_times)

        delta = score - prev_score
        pct = score / max(len(problems), 1) * 100
        saved = max_time - total_time_est
        delta_str = f"+{delta}" if delta > 0 else str(delta)

        print(f"  {cutoff:>7} {score:>5}/{len(problems):<1} {pct:>5.1f}% {delta_str:>6} {total_time_est/len(problems):>8.1f}s {total_time_est:>10.0f}s {saved:>+12.0f}s")

        prev_score = score

    # Find the "knee" — where additional attempts stop helping
    print(f"\n  KEY INSIGHT:")
    print(f"  Find the cutoff where delta drops to 0 for 3+ consecutive attempts.")
    print(f"  That's the point of diminishing returns.")


def wasted_compute_analysis(problems):
    """Quantify compute wasted on redundant correct answers, hopeless Nones, etc."""
    print(f"\n{'=' * 70}")
    print("  3. WASTED COMPUTE ANALYSIS")
    print("     Where are we spending time that doesn't help?")
    print("=" * 70)

    total_tokens = 0
    total_time = 0.0

    # Categories of waste
    redundant_correct_tokens = 0  # correct answers beyond what's needed for vote
    redundant_correct_time = 0.0
    hopeless_none_tokens = 0     # Nones on problems that ended up correct (not needed)
    hopeless_none_time = 0.0
    wrong_attempt_tokens = 0     # wrong answers
    wrong_attempt_time = 0.0
    useful_tokens = 0            # correct answers up to early_stop threshold
    useful_time = 0.0
    none_on_wrong_tokens = 0     # Nones on problems we got wrong (could have been useful)
    none_on_wrong_time = 0.0

    for p in problems:
        correct_count = 0
        for a in p.attempts:
            total_tokens += a.tokens
            total_time += a.time_s

            if a.answer == p.expected:
                correct_count += 1
                if correct_count <= 3:  # First 3 correct answers are "useful" (build consensus)
                    useful_tokens += a.tokens
                    useful_time += a.time_s
                else:
                    redundant_correct_tokens += a.tokens
                    redundant_correct_time += a.time_s
            elif a.is_none:
                if p.correct:
                    hopeless_none_tokens += a.tokens
                    hopeless_none_time += a.time_s
                else:
                    none_on_wrong_tokens += a.tokens
                    none_on_wrong_time += a.time_s
            else:
                wrong_attempt_tokens += a.tokens
                wrong_attempt_time += a.time_s

    print(f"\n  {'Category':<35} {'Tokens':>10} {'%Tok':>6} {'Time':>8} {'%Time':>6}")
    print(f"  {'─'*35} {'─'*10} {'─'*6} {'─'*8} {'─'*6}")

    categories = [
        ("USEFUL (correct, needed)", useful_tokens, useful_time),
        ("Redundant correct (excess votes)", redundant_correct_tokens, redundant_correct_time),
        ("None on correct problems", hopeless_none_tokens, hopeless_none_time),
        ("None on wrong problems", none_on_wrong_tokens, none_on_wrong_time),
        ("Wrong answers", wrong_attempt_tokens, wrong_attempt_time),
    ]

    for name, tokens, time_s in categories:
        tok_pct = tokens / max(total_tokens, 1) * 100
        time_pct = time_s / max(total_time, 1) * 100
        print(f"  {name:<35} {tokens:>10,} {tok_pct:>5.1f}% {time_s:>7.0f}s {time_pct:>5.1f}%")

    wasted = total_tokens - useful_tokens
    wasted_time = total_time - useful_time
    print(f"\n  Total wasted: {wasted:,} tokens ({wasted/max(total_tokens,1)*100:.0f}%), "
          f"{wasted_time:.0f}s ({wasted_time/max(total_time,1)*100:.0f}%)")

    # Salvageable: Nones on wrong problems are the MOST valuable to fix
    print(f"\n  SALVAGEABLE: {none_on_wrong_tokens:,} tokens ({none_on_wrong_time:.0f}s) spent on Nones")
    print(f"  for problems we got WRONG. If extraction fixed these, votes could flip.")

    # Redundant correct: compute saved by earlier stopping
    print(f"  SAVEABLE: {redundant_correct_tokens:,} tokens ({redundant_correct_time:.0f}s) on redundant")
    print(f"  correct answers beyond 3-vote consensus. Earlier stop reclaims this.")


def difficulty_classification(problems):
    """Classify problems into difficulty tiers based on attempt patterns."""
    print(f"\n{'=' * 70}")
    print("  4. PROBLEM DIFFICULTY CLASSIFICATION")
    print("     Categorize problems for adaptive allocation")
    print("=" * 70)

    tiers = {
        'TRIVIAL': [],   # Early stop on first wave, unanimous
        'EASY': [],      # Correct, early stop, few Nones
        'MODERATE': [],  # Correct, no early stop, some Nones/errors
        'HARD': [],      # Correct but tight vote or many Nones
        'UNSOLVABLE': [],  # Wrong answer
    }

    for p in problems:
        n_answers = sum(1 for a in p.attempts if a.answer is not None)
        n_nones = sum(1 for a in p.attempts if a.is_none)
        n_correct = sum(1 for a in p.attempts if a.answer == p.expected)
        n_attempts = len(p.attempts)
        none_rate = n_nones / max(n_attempts, 1)

        # Check first-attempt success
        first_3_correct = sum(1 for a in p.attempts[:3] if a.answer == p.expected)

        if not p.correct:
            tiers['UNSOLVABLE'].append(p)
        elif first_3_correct >= 3:
            tiers['TRIVIAL'].append(p)
        elif p.early_stop and none_rate < 0.5:
            tiers['EASY'].append(p)
        elif n_correct >= 3 and none_rate < 0.7:
            tiers['MODERATE'].append(p)
        else:
            tiers['HARD'].append(p)

    print(f"\n  {'Tier':<12} {'Count':>6} {'Avg Time':>9} {'Avg Attempts':>13} {'Avg Nones':>10} {'Avg Tokens':>11}")
    print(f"  {'─'*12} {'─'*6} {'─'*9} {'─'*13} {'─'*10} {'─'*11}")

    for tier_name in ['TRIVIAL', 'EASY', 'MODERATE', 'HARD', 'UNSOLVABLE']:
        tier = tiers[tier_name]
        if not tier:
            print(f"  {tier_name:<12} {0:>6}")
            continue
        avg_time = sum(p.wall_time for p in tier) / len(tier)
        avg_att = sum(len(p.attempts) for p in tier) / len(tier)
        avg_nones = sum(sum(1 for a in p.attempts if a.is_none) for p in tier) / len(tier)
        avg_tokens = sum(sum(a.tokens for a in p.attempts) for p in tier) / len(tier)
        print(f"  {tier_name:<12} {len(tier):>6} {avg_time:>8.0f}s {avg_att:>13.1f} {avg_nones:>10.1f} {avg_tokens:>10,.0f}")

    # Print problem IDs per tier
    for tier_name in ['TRIVIAL', 'EASY', 'MODERATE', 'HARD', 'UNSOLVABLE']:
        tier = tiers[tier_name]
        if tier:
            ids = [p.problem_id for p in tier]
            print(f"\n  {tier_name}: {', '.join(ids[:10])}" + (f" +{len(ids)-10} more" if len(ids) > 10 else ""))

    return tiers


def none_as_signal(problems):
    """When does a None mean 'stop trying' vs 'keep trying'?"""
    print(f"\n{'=' * 70}")
    print("  5. NONE AS SIGNAL: Stop or Continue?")
    print("     Does early None rate predict final failure?")
    print("=" * 70)

    # After first N attempts, what none rate predicts failure?
    for n_early in [2, 3, 4]:
        none_rates = {'correct': [], 'wrong': []}

        for p in problems:
            if len(p.attempts) < n_early:
                continue
            early = p.attempts[:n_early]
            none_count = sum(1 for a in early if a.is_none)
            none_rate = none_count / n_early

            if p.correct:
                none_rates['correct'].append(none_rate)
            else:
                none_rates['wrong'].append(none_rate)

        print(f"\n  After {n_early} attempts — None rate distribution:")
        if none_rates['correct']:
            avg_ok = sum(none_rates['correct']) / len(none_rates['correct'])
            print(f"    Correct problems:   avg none rate = {avg_ok:.2f} (n={len(none_rates['correct'])})")
        if none_rates['wrong']:
            avg_wrong = sum(none_rates['wrong']) / len(none_rates['wrong'])
            print(f"    Wrong problems:     avg none rate = {avg_wrong:.2f} (n={len(none_rates['wrong'])})")

        # Threshold analysis
        for threshold in [0.5, 0.75, 1.0]:
            high_none_correct = sum(1 for r in none_rates['correct'] if r >= threshold)
            high_none_wrong = sum(1 for r in none_rates['wrong'] if r >= threshold)
            total_high = high_none_correct + high_none_wrong
            if total_high > 0:
                wrong_pct = high_none_wrong / total_high * 100
                print(f"    None rate >= {threshold:.0%}: {total_high} problems ({high_none_wrong} wrong = {wrong_pct:.0f}% failure rate)")

    print(f"\n  INSIGHT: If none rate after 3 attempts is 100%, problem is harder but")
    print(f"  NOT necessarily unsolvable. Stopping too early on all-None would lose points.")
    print(f"  Better signal: 'any correct answer found' is the true easy-stop indicator.")


def wave_batching_simulation(problems):
    """Simulate wave-based batching and compute time savings."""
    print(f"\n{'=' * 70}")
    print("  6. WAVE-BASED BATCHING SIMULATION")
    print("     What happens with 3 waves of 6 instead of 8 parallel?")
    print("=" * 70)

    # Current: all 8 in parallel, wall time = max(attempt times)
    current_total = sum(p.wall_time for p in problems)

    # Simulate waves with different configs
    configs = [
        {'name': 'Current (8 parallel)', 'waves': [8], 'early_stop': 3},
        {'name': '2 waves of 4', 'waves': [4, 4], 'early_stop': 3},
        {'name': '3 waves of 4', 'waves': [4, 4, 4], 'early_stop': 3},
        {'name': '2 waves of 6', 'waves': [6, 6], 'early_stop': 3},
        {'name': '3 waves of 6', 'waves': [6, 6, 6], 'early_stop': 3},
        {'name': '2w adaptive (6+6, ES=3)', 'waves': [6, 6], 'early_stop': 3},
        {'name': '3w adaptive (6+6+4, ES=3)', 'waves': [6, 6, 4], 'early_stop': 3},
    ]

    print(f"\n  {'Config':<30} {'Score':>7} {'Time':>8} {'Avg/Prob':>9} {'vs Current':>11}")
    print(f"  {'─'*30} {'─'*7} {'─'*8} {'─'*9} {'─'*11}")

    for cfg in configs:
        total_score = 0
        total_time = 0.0

        for p in problems:
            attempts = p.attempts
            if not attempts:
                continue

            problem_time = 0.0
            all_answers = []
            attempt_idx = 0

            for wave_size in cfg['waves']:
                wave_attempts = attempts[attempt_idx:attempt_idx + wave_size]
                if not wave_attempts:
                    break

                # Wave wall time = max attempt time in wave
                wave_times = [a.time_s for a in wave_attempts if a.time_s > 0]
                wave_time = max(wave_times) if wave_times else 0
                problem_time += wave_time

                # Collect answers
                for a in wave_attempts:
                    if a.answer is not None:
                        all_answers.append(a.answer)

                attempt_idx += wave_size

                # Check early stop between waves
                if all_answers:
                    top_count = Counter(all_answers).most_common(1)[0][1]
                    if top_count >= cfg['early_stop']:
                        break  # REAL early stop — skip remaining waves

            # Vote on collected answers
            if all_answers:
                vote = Counter(all_answers).most_common(1)[0][0]
                if vote == p.expected:
                    total_score += 1

            total_time += problem_time

        avg_time = total_time / max(len(problems), 1)
        savings = current_total - total_time
        pct_change = savings / max(current_total, 1) * 100

        print(f"  {cfg['name']:<30} {total_score:>5}/{len(problems):<1} {total_time:>7.0f}s {avg_time:>8.1f}s {savings:>+10.0f}s ({pct_change:>+.0f}%)")

    print(f"\n  NOTE: Simulation is approximate. Wave wall time = max(attempt times in wave).")
    print(f"  Real sequential waves would be slightly different due to GPU scheduling.")
    print(f"  Key question: does score stay the same with fewer total attempts but real early stop?")


def competition_time_projection(problems):
    """Project time usage for 50 competition problems."""
    print(f"\n{'=' * 70}")
    print("  7. COMPETITION TIME PROJECTION (50 problems, 300 min)")
    print("     Will we finish in time? What's optimal config?")
    print("=" * 70)

    # Use per-problem times from our data to project
    times = sorted([p.wall_time for p in problems if p.wall_time > 0])
    if not times:
        print("  No timing data available.")
        return

    # Stats
    avg = sum(times) / len(times)
    median = times[len(times)//2]
    p90 = times[int(len(times)*0.9)]
    p95 = times[int(len(times)*0.95)] if len(times) > 20 else times[-1]

    print(f"\n  Current problem times (from {len(times)} problems):")
    print(f"    Average: {avg:.0f}s | Median: {median:.0f}s | P90: {p90:.0f}s | P95: {p95:.0f}s | Max: {times[-1]:.0f}s")

    budget = 300 * 60  # 5 hours in seconds
    vllm_startup = 120  # vLLM server startup

    scenarios = [
        ('Optimistic (all median)', median * 50 + vllm_startup),
        ('Realistic (all average)', avg * 50 + vllm_startup),
        ('Pessimistic (all P90)', p90 * 50 + vllm_startup),
        ('Worst case (all P95)', p95 * 50 + vllm_startup),
    ]

    print(f"\n  {'Scenario':<30} {'Est. Time':>10} {'vs 300min':>10} {'Fits?':>6}")
    print(f"  {'─'*30} {'─'*10} {'─'*10} {'─'*6}")
    for name, est in scenarios:
        margin = budget - est
        fits = 'YES' if margin > 0 else 'NO'
        print(f"  {name:<30} {est/60:>9.1f}m {margin/60:>+9.1f}m {fits:>6}")

    # What's the max per-problem budget that fits in 5 hours?
    safe_budget = (budget - vllm_startup) / 50
    print(f"\n  Max per-problem budget for 50 problems: {safe_budget:.0f}s ({safe_budget/60:.1f}min)")
    print(f"  Current high_problem_timeout: 900s (15min) — {900/safe_budget:.1f}x over budget if all hard")
    print(f"  Current base_problem_timeout: 300s (5min) — {'fits' if 300 < safe_budget else 'EXCEEDS'}")

    # Adaptive projection: easy problems fast, hard problems get remaining time
    # Use our difficulty tiers
    n_easy = sum(1 for p in problems if p.early_stop and p.wall_time < 60)
    n_hard = sum(1 for p in problems if p.wall_time > 200 or not p.correct)
    n_medium = len(problems) - n_easy - n_hard

    if len(problems) > 0:
        easy_pct = n_easy / len(problems)
        medium_pct = n_medium / len(problems)
        hard_pct = n_hard / len(problems)

        # Project to 50 problems
        proj_easy = int(50 * easy_pct)
        proj_medium = int(50 * medium_pct)
        proj_hard = 50 - proj_easy - proj_medium

        easy_time = 60   # 1 wave, early stop
        medium_time = 180  # 2 waves
        hard_time = 600   # 3 waves, full budget

        adaptive_total = (proj_easy * easy_time + proj_medium * medium_time + proj_hard * hard_time + vllm_startup)

        print(f"\n  ADAPTIVE PROJECTION:")
        print(f"    Easy (~{easy_pct:.0%} = {proj_easy} problems): {easy_time}s each = {proj_easy * easy_time / 60:.0f}min")
        print(f"    Medium (~{medium_pct:.0%} = {proj_medium} problems): {medium_time}s each = {proj_medium * medium_time / 60:.0f}min")
        print(f"    Hard (~{hard_pct:.0%} = {proj_hard} problems): {hard_time}s each = {proj_hard * hard_time / 60:.0f}min")
        print(f"    Total: {adaptive_total/60:.0f}min / 300min = {'FITS' if adaptive_total < budget else 'EXCEEDS'}")
        print(f"    Headroom: {(budget - adaptive_total)/60:.0f}min for retries or additional attempts")


def concrete_recommendations(problems):
    """Output concrete v24 config recommendations."""
    print(f"\n{'=' * 70}")
    print("  8. CONCRETE v24 RECOMMENDATIONS")
    print("=" * 70)

    # Find optimal early stop
    for es_thresh in [2, 3, 4, 5]:
        score = 0
        for p in problems:
            answers = []
            for a in p.attempts:
                if a.answer is not None:
                    answers.append(a.answer)
                    top = Counter(answers).most_common(1)[0][1]
                    if top >= es_thresh:
                        break
            if answers:
                vote = Counter(answers).most_common(1)[0][0]
                if vote == p.expected:
                    score += 1
        print(f"  Early stop threshold={es_thresh}: score={score}/{len(problems)}")

    # Find first attempt that produces correct answer
    first_correct = []
    for p in problems:
        if p.correct:
            for i, a in enumerate(p.attempts):
                if a.answer == p.expected:
                    first_correct.append(i + 1)
                    break

    if first_correct:
        print(f"\n  First correct answer found at attempt:")
        for n in sorted(set(first_correct)):
            count = first_correct.count(n)
            print(f"    Attempt {n}: {count} problems ({count/len(first_correct)*100:.0f}%)")
        cumulative = 0
        print(f"\n  Cumulative: how many problems solved by attempt N:")
        for n in range(1, max(first_correct) + 1):
            cumulative += first_correct.count(n)
            print(f"    By attempt {n}: {cumulative}/{len(first_correct)} ({cumulative/len(first_correct)*100:.0f}%)")

    print(f"""
  RECOMMENDED v24 CONFIG:
  ─────────────────────────
  Execution:   Wave-based, 3 waves of 6 attempts
  Early stop:  Between waves, threshold=3 (same score, half the compute)
  Wave 1:      temp=[0.1, 0.3, 0.5, 0.5, 0.5, 0.7] — cover full range
  Wave 2:      temp=[0.3, 0.3, 0.5, 0.5, 0.7, 0.9] — diversity
  Wave 3:      temp=[0.3, 0.5, 0.7, 0.7, 0.5, 0.5] — fill remaining
  Decision:    After wave 1, if 3+ agree → STOP (easy problem)
               After wave 2, if 3+ agree → STOP (medium problem)
               Wave 3 only for hard problems (no consensus after 12 attempts)
  Budget:      Easy: ~60s (1 wave)
               Medium: ~180s (2 waves)
               Hard: ~600s (3 waves)
  Total for 50: ~150min with headroom (vs 300min limit)
  """)


def main():
    logfile = sys.argv[1] if len(sys.argv) > 1 else 'output/v22/diagnostic.log'
    if not os.path.exists(logfile):
        print(f"Error: {logfile} not found")
        sys.exit(1)

    print(f"Analyzing: {logfile}")
    problems = parse_log(logfile)
    print(f"Parsed {len(problems)} problems\n")

    early_signal_detection(problems)
    optimal_attempt_cutoffs(problems)
    wasted_compute_analysis(problems)
    difficulty_classification(problems)
    none_as_signal(problems)
    wave_batching_simulation(problems)
    competition_time_projection(problems)
    concrete_recommendations(problems)


if __name__ == '__main__':
    main()
