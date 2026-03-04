#!/usr/bin/env python3
"""
Retry budget simulation: Given 290 min for 110 problems,
what base timeout + retry strategy maximizes score?

The idea:
  1. Run all 110 problems with base timeout T
  2. Problems with top_votes < 5 get retried with remaining time
  3. Retry adds more attempts to improve vote confidence

Usage:
    python3 log_exploration/retry_budget_sim.py <diagnostic.log>
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log_exploration.log_query import parse_log
from collections import Counter
import numpy as np


def simulate(logfile):
    problems = parse_log(logfile)

    # Deduplicate
    seen = set()
    unique = []
    for p in problems:
        if p.problem_id not in seen:
            seen.add(p.problem_id)
            unique.append(p)
    problems = unique

    TOTAL_BUDGET = 17400  # 290 min in seconds
    N_COMPETITION = 110
    RETRY_THRESHOLD = 5  # top_votes < this → retry

    print(f"{'='*90}")
    print(f"  RETRY BUDGET SIMULATION")
    print(f"  Total budget: {TOTAL_BUDGET}s ({TOTAL_BUDGET/60:.0f} min)")
    print(f"  Competition problems: {N_COMPETITION}")
    print(f"  Retry threshold: top_votes < {RETRY_THRESHOLD}")
    print(f"  Test data: {len(problems)} problems from v32")
    print(f"{'='*90}")

    # For each base timeout, simulate:
    # 1. Score from first pass
    # 2. How many problems would trigger retry
    # 3. How much time left for retries
    # 4. Expected score improvement from retries

    print(f"\n  {'─'*86}")
    print(f"  SIMULATION: Score at different base timeouts")
    print(f"  {'─'*86}")
    print(f"  {'Base T':>8} {'Score':>7} {'Low-conf':>9} {'Time used':>10} "
          f"{'Spare':>8} {'Retries':>8} {'Expected':>9}")
    print(f"  {'(s)':>8} {'(/53)':>7} {'(top<5)':>9} {'(min)':>10} "
          f"{'(min)':>8} {'possible':>8} {'gain':>9}")
    print(f"  {'─'*8} {'─'*7} {'─'*9} {'─'*10} {'─'*8} {'─'*8} {'─'*9}")

    best_config = None
    best_expected = 0

    for base_t in [90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 200, 210, 240, 270, 300, 360]:
        # Score at this timeout
        score = 0
        low_conf = 0
        low_conf_has_correct = 0
        problem_times = []

        for p in problems:
            votes = Counter()
            max_time = 0
            for a in p.attempts:
                at = getattr(a, 'time_s', None)
                if at is not None and at <= base_t and a.answer is not None:
                    votes[a.answer] += 1
                if at is not None:
                    max_time = max(max_time, min(at, base_t))

            problem_times.append(max_time)

            if votes:
                winner, top_count = votes.most_common(1)[0]
                if winner == p.expected:
                    score += 1
                if top_count < RETRY_THRESHOLD:
                    low_conf += 1
                    # Check if correct answer exists in votes
                    if p.expected in votes:
                        low_conf_has_correct += 1
            else:
                low_conf += 1

        # Scale to 110 problems
        avg_time = np.mean(problem_times)
        total_first_pass = avg_time * N_COMPETITION
        spare_time = TOTAL_BUDGET - total_first_pass

        # Scale low_conf to 110
        low_conf_scaled = int(low_conf * N_COMPETITION / len(problems))
        low_conf_correct_scaled = int(low_conf_has_correct * N_COMPETITION / len(problems))

        # How many retries fit in spare time?
        retries_possible = int(spare_time / base_t) if spare_time > 0 else 0
        retries_actual = min(retries_possible, low_conf_scaled)

        # Expected gain from retries (conservative: 20% chance of flipping a wrong problem)
        # Only problems that have correct in some votes can be flipped
        flippable = min(retries_actual, low_conf_correct_scaled)
        expected_gain = flippable * 0.3  # 30% flip rate with more samples

        # Scale score to 110
        score_scaled = score * N_COMPETITION / len(problems)
        total_expected = score_scaled + expected_gain

        if total_expected > best_expected:
            best_expected = total_expected
            best_config = base_t

        print(f"  {base_t:>8} {score:>4}/53 {low_conf:>9} {total_first_pass/60:>9.0f}m "
              f"{max(spare_time/60,0):>7.0f}m {retries_actual:>8} {expected_gain:>8.1f}")

    print(f"\n  Best config: base_t = {best_config}s (expected total ≈ {best_expected:.1f})")

    # Detailed analysis for a few key configs
    print(f"\n\n{'='*90}")
    print(f"  DETAILED ANALYSIS FOR KEY CONFIGS")
    print(f"{'='*90}")

    for base_t in [120, 150, 180, 240]:
        print(f"\n  {'─'*86}")
        print(f"  BASE TIMEOUT: {base_t}s ({base_t/60:.1f} min)")
        print(f"  {'─'*86}")

        score = 0
        low_conf_problems = []
        correct_problems = []
        wrong_problems = []

        for p in problems:
            votes = Counter()
            for a in p.attempts:
                at = getattr(a, 'time_s', None)
                if at is not None and at <= base_t and a.answer is not None:
                    votes[a.answer] += 1

            if votes:
                winner, top_count = votes.most_common(1)[0]
                correct = (winner == p.expected)
                if correct:
                    score += 1
                    correct_problems.append((p.problem_id, top_count, len(votes)))
                else:
                    wrong_problems.append((p.problem_id, winner, p.expected, top_count,
                                          p.expected in votes,
                                          votes.get(p.expected, 0) if p.expected else 0))

                if top_count < RETRY_THRESHOLD:
                    has_correct = p.expected in votes
                    low_conf_problems.append((p.problem_id, top_count, len(votes), correct, has_correct))
            else:
                low_conf_problems.append((p.problem_id, 0, 0, False, False))
                wrong_problems.append((p.problem_id, None, p.expected, 0, False, 0))

        avg_time = np.mean([min(getattr(a, 'time_s', base_t), base_t)
                           for p in problems for a in p.attempts
                           if getattr(a, 'time_s', None)])
        # Use max attempt time per problem for wall clock estimate
        problem_wall = []
        for p in problems:
            times = [min(getattr(a, 'time_s', base_t), base_t) for a in p.attempts if getattr(a, 'time_s', None)]
            problem_wall.append(max(times) if times else base_t)

        total_time = sum(problem_wall)
        scaled_time = total_time * N_COMPETITION / len(problems)
        spare = TOTAL_BUDGET - scaled_time

        print(f"  Score: {score}/{len(problems)}")
        print(f"  Est. time for 110 problems: {scaled_time/60:.0f} min")
        print(f"  Spare time: {max(spare, 0)/60:.0f} min")
        print(f"  Low-confidence (top<{RETRY_THRESHOLD}): {len(low_conf_problems)}")

        if low_conf_problems:
            print(f"\n  Low-confidence problems:")
            for pid, top, uniq, corr, has_c in low_conf_problems:
                status = "CORRECT" if corr else ("HAS_CORRECT" if has_c else "NO_CORRECT")
                print(f"    {pid}: top_votes={top}, unique={uniq}, {status}")

        # Wrong problems with correct in votes (salvageable)
        salvageable = [w for w in wrong_problems if w[4]]  # has_correct=True
        print(f"\n  Wrong problems with correct answer in votes (salvageable): {len(salvageable)}")
        for pid, pred, exp, top, _, correct_votes in salvageable:
            print(f"    {pid}: pred={pred} (top={top}), correct={exp} ({correct_votes} votes)")

    # Analysis: what problems are we losing at each timeout?
    print(f"\n\n{'='*90}")
    print(f"  PROBLEMS LOST AT EACH TIMEOUT STEP")
    print(f"{'='*90}")

    prev_correct = set()
    for base_t in [120, 150, 180, 240, 300, 360]:
        current_correct = set()
        for p in problems:
            votes = Counter()
            for a in p.attempts:
                at = getattr(a, 'time_s', None)
                if at is not None and at <= base_t and a.answer is not None:
                    votes[a.answer] += 1
            if votes:
                winner = votes.most_common(1)[0][0]
                if winner == p.expected:
                    current_correct.add(p.problem_id)

        gained = current_correct - prev_correct
        lost = prev_correct - current_correct  # shouldn't happen but check

        if gained:
            print(f"\n  At {base_t}s: gained {len(gained)} → {', '.join(gained)}")
        if lost:
            print(f"  At {base_t}s: LOST {len(lost)} → {', '.join(lost)}")

        prev_correct = current_correct

    print(f"\n  Total at 360s: {len(prev_correct)}/{len(problems)}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <diagnostic.log>")
        sys.exit(1)

    simulate(sys.argv[1])
