#!/usr/bin/env python3
"""
AIMO3 Adaptive Strategy Simulator
====================================
Simulate different compute allocation strategies using actual attempt data.
Answers: "What score would we get with config X?"

Strategies:
    fixed-N       Use exactly N attempts per problem (N=1..16)
    adaptive      Easy=4 attempts, Medium=8, Hard=16 (classified by early signals)
    wave-N-M      N waves of M attempts with inter-wave early stop
    es-N          Use all attempts but change early stop threshold to N
    aggressive    ES=2, stop aggressively on agreement
    conservative  ES=5, maximize consensus before stopping
    budget-N      Cap total time budget at N minutes (project from attempt times)

Usage:
    python log_exploration/adaptive_simulator.py <logfile> [strategy] [args...]
    python log_exploration/adaptive_simulator.py output/v22/diagnostic.log all
    python log_exploration/adaptive_simulator.py output/v22/diagnostic.log fixed 4
    python log_exploration/adaptive_simulator.py output/v22/diagnostic.log wave 3 6
    python log_exploration/adaptive_simulator.py output/v22/diagnostic.log adaptive
    python log_exploration/adaptive_simulator.py --help
"""

import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def simulate_fixed(problems, n_attempts):
    """Use exactly first N attempts per problem."""
    score = 0
    total_time = 0.0
    details = []

    for p in problems:
        subset = p.attempts[:n_attempts]
        answers = [a.answer for a in subset if a.answer is not None]
        wall = max((a.time_s for a in subset), default=0) if subset else 0
        total_time += wall

        predicted = None
        if answers:
            predicted = Counter(answers).most_common(1)[0][0]

        correct = predicted is not None and predicted == p.expected
        if correct:
            score += 1
        details.append((p.problem_id, correct, predicted, p.expected, wall, len(answers), len(subset)))

    return score, total_time, details


def simulate_es(problems, threshold):
    """Use all attempts but stop counting when threshold reached."""
    score = 0
    total_time = 0.0
    avg_attempts_used = 0

    for p in problems:
        answers = []
        attempts_used = 0
        wall = 0

        for a in p.attempts:
            attempts_used += 1
            wall = max(wall, a.time_s)
            if a.answer is not None:
                answers.append(a.answer)
                top = Counter(answers).most_common(1)[0][1]
                if top >= threshold:
                    break

        total_time += wall
        avg_attempts_used += attempts_used

        predicted = None
        if answers:
            predicted = Counter(answers).most_common(1)[0][0]

        if predicted is not None and predicted == p.expected:
            score += 1

    avg_att = avg_attempts_used / max(len(problems), 1)
    return score, total_time, avg_att


def simulate_wave(problems, n_waves, wave_size, es_threshold=3):
    """Simulate wave-based execution with inter-wave early stop."""
    score = 0
    total_time = 0.0
    total_waves_used = 0
    early_stopped = 0

    for p in problems:
        answers = []
        problem_time = 0.0
        idx = 0
        waves_used = 0

        for w in range(n_waves):
            wave = p.attempts[idx:idx + wave_size]
            if not wave:
                break
            waves_used += 1

            wave_time = max((a.time_s for a in wave), default=0)
            problem_time += wave_time
            idx += wave_size

            for a in wave:
                if a.answer is not None:
                    answers.append(a.answer)

            # Inter-wave early stop check
            if answers:
                top = Counter(answers).most_common(1)[0][1]
                if top >= es_threshold:
                    early_stopped += 1
                    break

        total_time += problem_time
        total_waves_used += waves_used

        predicted = None
        if answers:
            predicted = Counter(answers).most_common(1)[0][0]

        if predicted is not None and predicted == p.expected:
            score += 1

    avg_waves = total_waves_used / max(len(problems), 1)
    return score, total_time, avg_waves, early_stopped


def simulate_adaptive(problems, easy_attempts=4, hard_attempts=None):
    """Adaptive: classify problem as easy/hard after first wave, allocate accordingly."""
    if hard_attempts is None:
        hard_attempts = max(len(p.attempts) for p in problems)

    score = 0
    total_time = 0.0
    easy_count = 0
    hard_count = 0

    for p in problems:
        # Phase 1: first 4 attempts (classification wave)
        phase1 = p.attempts[:easy_attempts]
        phase1_answers = [a.answer for a in phase1 if a.answer is not None]
        phase1_time = max((a.time_s for a in phase1), default=0)

        # Classify
        is_easy = False
        if phase1_answers:
            top_count = Counter(phase1_answers).most_common(1)[0][1]
            # Easy: majority agreement in first wave
            if top_count >= 2:
                is_easy = True

        if is_easy:
            easy_count += 1
            answers = phase1_answers
            total_time += phase1_time
        else:
            hard_count += 1
            # Use all available attempts
            all_attempts = p.attempts[:hard_attempts]
            answers = [a.answer for a in all_attempts if a.answer is not None]
            total_time += max((a.time_s for a in all_attempts), default=0)

        predicted = None
        if answers:
            predicted = Counter(answers).most_common(1)[0][0]

        if predicted is not None and predicted == p.expected:
            score += 1

    return score, total_time, easy_count, hard_count


def run_all(problems):
    """Run all strategies and print comparison table."""
    total = len(problems)
    current_score = sum(1 for p in problems if p.correct)
    max_att = max(len(p.attempts) for p in problems)

    print(f"\n{'=' * 75}")
    print(f"  STRATEGY COMPARISON ({total} problems, current: {current_score}/{total})")
    print(f"{'=' * 75}")

    results = []

    # Fixed strategies
    for n in [1, 2, 3, 4, 5, 6, 7, 8]:
        if n > max_att:
            break
        s, t, _ = simulate_fixed(problems, n)
        results.append((f'fixed-{n}', s, t, f'{n} attempts/problem'))

    # Early stop strategies
    for es in [2, 3, 4, 5]:
        s, t, avg_att = simulate_es(problems, es)
        results.append((f'es-{es}', s, t, f'ES threshold={es}, avg {avg_att:.1f} att used'))

    # Wave strategies
    for n_waves, w_size in [(2, 4), (2, 6), (3, 4), (3, 6)]:
        s, t, avg_w, es_count = simulate_wave(problems, n_waves, w_size, es_threshold=3)
        results.append((f'wave-{n_waves}x{w_size}', s, t, f'{n_waves} waves of {w_size}, ES=3, {es_count} early stopped, avg {avg_w:.1f} waves'))

    # Adaptive strategies
    for easy_n in [3, 4, 5]:
        s, t, e_count, h_count = simulate_adaptive(problems, easy_attempts=easy_n)
        results.append((f'adaptive-{easy_n}', s, t, f'easy={easy_n} att, hard=all, {e_count} easy / {h_count} hard'))

    # Print results
    print(f"\n  {'Strategy':<16} {'Score':>7} {'%':>6} {'Time':>8} {'Avg/P':>7} {'Details':<45}")
    print(f"  {'─'*16} {'─'*7} {'─'*6} {'─'*8} {'─'*7} {'─'*45}")

    for name, score, time_s, detail in results:
        pct = score / max(total, 1) * 100
        avg = time_s / max(total, 1)
        marker = ' ***' if score >= current_score else ''
        print(f"  {name:<16} {score:>5}/{total:<1} {pct:>5.1f}% {time_s:>7.0f}s {avg:>6.1f}s {detail:<45}{marker}")

    # Best strategies
    best = max(results, key=lambda r: (r[1], -r[2]))
    fastest_same = min((r for r in results if r[1] >= current_score), key=lambda r: r[2], default=None)

    print(f"\n  Highest score: {best[0]} ({best[1]}/{total})")
    if fastest_same:
        print(f"  Fastest at current score ({current_score}): {fastest_same[0]} ({fastest_same[2]:.0f}s)")

    # Competition projection
    print(f"\n  COMPETITION PROJECTION (50 problems, 300 min budget):")
    for name, score, time_s, detail in results:
        if score >= current_score:
            per_problem = time_s / max(total, 1)
            proj_time = per_problem * 50 + 120  # +120s for vLLM startup
            fits = proj_time < 18000
            print(f"    {name:<16} {per_problem:.0f}s/prob * 50 + startup = {proj_time/60:.0f}min {'FITS' if fits else 'EXCEEDS'}")


def main():
    if '--help' in sys.argv or len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0 if '--help' in sys.argv else 1)

    logfile = sys.argv[1]
    if not os.path.exists(logfile):
        print(f"Error: {logfile} not found")
        sys.exit(1)

    problems = parse_log(logfile)
    strategy = sys.argv[2] if len(sys.argv) > 2 else 'all'

    if strategy == 'all':
        run_all(problems)
    elif strategy == 'fixed':
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 4
        s, t, details = simulate_fixed(problems, n)
        print(f"Fixed-{n}: {s}/{len(problems)} in {t:.0f}s")
        wrong = [(d[0], d[2], d[3]) for d in details if not d[1]]
        if wrong:
            print(f"Wrong: {wrong}")
    elif strategy == 'wave':
        n_waves = int(sys.argv[3]) if len(sys.argv) > 3 else 3
        w_size = int(sys.argv[4]) if len(sys.argv) > 4 else 6
        s, t, avg_w, es = simulate_wave(problems, n_waves, w_size)
        print(f"Wave {n_waves}x{w_size}: {s}/{len(problems)} in {t:.0f}s, avg {avg_w:.1f} waves, {es} early stopped")
    elif strategy == 'adaptive':
        easy_n = int(sys.argv[3]) if len(sys.argv) > 3 else 4
        s, t, e, h = simulate_adaptive(problems, easy_attempts=easy_n)
        print(f"Adaptive (easy={easy_n}): {s}/{len(problems)} in {t:.0f}s ({e} easy, {h} hard)")
    elif strategy.startswith('es'):
        thresh = int(sys.argv[3]) if len(sys.argv) > 3 else 3
        s, t, avg = simulate_es(problems, thresh)
        print(f"ES-{thresh}: {s}/{len(problems)} in {t:.0f}s, avg {avg:.1f} attempts used")
    else:
        print(f"Unknown strategy: {strategy}. Use --help.")
        sys.exit(1)


if __name__ == '__main__':
    main()
