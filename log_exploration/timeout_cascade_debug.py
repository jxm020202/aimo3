#!/usr/bin/env python3
"""
Debug the surprising finding: attempts with 5 timeouts in first 5 turns
have 96% correctness. What's happening?

Also: deep dive into what the model is ACTUALLY computing in timed-out cells.
"""

import sys
import os
import re
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 timeout_cascade_debug.py <diagnostic.log>")
        sys.exit(1)

    logfile = sys.argv[1]
    problems = parse_log(logfile)
    print(f"Parsed {len(problems)} problems.\n")

    # ── 1. Investigate 5-timeout-in-first-5 attempts ──
    print("=" * 80)
    print("1. ATTEMPTS WITH 5 TIMEOUTS IN FIRST 5 TURNS")
    print("=" * 80)

    five_to_attempts = []
    for prob in problems:
        for att in prob.attempts:
            timeouts_in_first5 = 0
            for turn in att.turns[:5]:
                if turn.is_error and 'timed out' in turn.output.lower():
                    timeouts_in_first5 += 1
            if timeouts_in_first5 == 5:
                five_to_attempts.append((prob, att))

    print(f"\n  Found {len(five_to_attempts)} attempts with 5/5 early timeouts")

    # Check how many total turns these have and their outcomes
    total_turns_dist = Counter()
    answer_dist = Counter()
    problem_dist = Counter()

    for prob, att in five_to_attempts:
        total_turns_dist[len(att.turns)] += 1
        if att.answer is not None:
            answer_dist['has_answer'] += 1
        else:
            answer_dist['no_answer'] += 1
        problem_dist[prob.problem_id] += 1

    print(f"\n  Turn count distribution for these attempts:")
    for turns, count in sorted(total_turns_dist.items()):
        print(f"    {turns} turns: {count} attempts")

    print(f"\n  Answer distribution:")
    for k, v in answer_dist.items():
        print(f"    {k}: {v}")

    print(f"\n  Problems these come from (top 15):")
    for pid, count in problem_dist.most_common(15):
        prob = next(p for p in problems if p.problem_id == pid)
        print(f"    {pid}: {count} attempts, correct={prob.correct}")

    # ── 2. What code are they running in those first 5 timed-out turns? ──
    print("\n" + "=" * 80)
    print("2. CODE IN FIRST 5 TIMED-OUT TURNS (sample)")
    print("=" * 80)

    seen = 0
    for prob, att in five_to_attempts[:5]:
        print(f"\n  --- Problem {prob.problem_id}, Attempt {att.attempt_num} ---")
        print(f"  Total turns: {len(att.turns)}, Answer: {att.answer}")
        for turn in att.turns[:5]:
            code_snippet = turn.code[:300].replace('\n', ' | ')
            print(f"  Turn {turn.turn_num}: {code_snippet[:200]}...")
        seen += 1

    # ── 3. These are likely "all 8 turns timeout" = complete timeout attempts ──
    # Check: how many of these 140 attempts have ALL turns as timeouts?
    print("\n" + "=" * 80)
    print("3. ARE THESE COMPLETE TIMEOUT ATTEMPTS?")
    print("=" * 80)

    all_timeout_count = 0
    partial_timeout_count = 0
    for prob, att in five_to_attempts:
        all_timeout = all(t.is_error and 'timed out' in t.output.lower() for t in att.turns)
        if all_timeout:
            all_timeout_count += 1
        else:
            partial_timeout_count += 1

    print(f"\n  All turns timeout: {all_timeout_count}")
    print(f"  Partial timeout:   {partial_timeout_count}")
    print(f"\n  NOTE: 'Correct' for these means the PROBLEM got correct (voted answer)")
    print(f"        NOT that THIS ATTEMPT contributed the correct answer.")
    print(f"        These timeout attempts likely return None, and the problem")
    print(f"        was solved by OTHER non-timeout attempts.")

    # ── 4. Verify: what answers do 5-timeout attempts produce? ──
    print("\n" + "=" * 80)
    print("4. ANSWERS FROM 5-TIMEOUT ATTEMPTS")
    print("=" * 80)

    answer_breakdown = Counter()
    for prob, att in five_to_attempts:
        if att.answer is None:
            answer_breakdown['None'] += 1
        elif att.answer == prob.expected:
            answer_breakdown['Correct answer'] += 1
        else:
            answer_breakdown['Wrong answer'] += 1

    for k, v in answer_breakdown.most_common():
        print(f"  {k}: {v} ({v/len(five_to_attempts)*100:.1f}%)")

    # ── 5. BETTER METRIC: per-attempt correctness vs timeouts ──
    print("\n" + "=" * 80)
    print("5. PER-ATTEMPT CORRECTNESS (attempt's own answer) vs TIMEOUTS")
    print("=" * 80)

    bucket_stats = defaultdict(lambda: {'correct': 0, 'wrong': 0, 'none': 0})
    for prob in problems:
        for att in prob.attempts:
            n_timeouts = sum(1 for t in att.turns if t.is_error and 'timed out' in t.output.lower())
            total_turns = len(att.turns)
            if total_turns == 0:
                continue
            to_pct = n_timeouts / total_turns

            if n_timeouts == 0:
                bucket = '0 timeouts'
            elif to_pct <= 0.25:
                bucket = '1-25% timeout'
            elif to_pct <= 0.50:
                bucket = '26-50% timeout'
            elif to_pct <= 0.75:
                bucket = '51-75% timeout'
            else:
                bucket = '76-100% timeout'

            if att.answer is None:
                bucket_stats[bucket]['none'] += 1
            elif att.answer == prob.expected:
                bucket_stats[bucket]['correct'] += 1
            else:
                bucket_stats[bucket]['wrong'] += 1

    print(f"\n  {'Timeout %':<20} {'Correct':>9} {'Wrong':>7} {'None':>7} {'Total':>7} {'Correct%':>10} {'None%':>8}")
    print(f"  {'─'*20} {'─'*9} {'─'*7} {'─'*7} {'─'*7} {'─'*10} {'─'*8}")
    for bucket in ['0 timeouts', '1-25% timeout', '26-50% timeout', '51-75% timeout', '76-100% timeout']:
        d = bucket_stats[bucket]
        total = d['correct'] + d['wrong'] + d['none']
        answered = d['correct'] + d['wrong']
        pct = d['correct'] / answered * 100 if answered > 0 else 0
        none_pct = d['none'] / total * 100 if total > 0 else 0
        print(f"  {bucket:<20} {d['correct']:>9} {d['wrong']:>7} {d['none']:>7} {total:>7} {pct:>9.1f}% {none_pct:>7.1f}%")

    # ── 6. Time wasted per timeout bucket ──
    print("\n" + "=" * 80)
    print("6. TIME EFFICIENCY: Clean vs Timeout-heavy attempts")
    print("=" * 80)

    time_buckets = defaultdict(lambda: {'time': 0, 'count': 0, 'produced_answer': 0})
    for prob in problems:
        for att in prob.attempts:
            n_timeouts = sum(1 for t in att.turns if t.is_error and 'timed out' in t.output.lower())
            if n_timeouts == 0:
                bucket = 'clean'
            elif n_timeouts <= 2:
                bucket = '1-2 timeouts'
            elif n_timeouts <= 5:
                bucket = '3-5 timeouts'
            else:
                bucket = '6+ timeouts'
            time_buckets[bucket]['time'] += att.time_s
            time_buckets[bucket]['count'] += 1
            if att.answer is not None:
                time_buckets[bucket]['produced_answer'] += 1

    print(f"\n  {'Bucket':<20} {'Count':>7} {'Total time':>12} {'Avg time':>10} {'Got answer':>12} {'Answer%':>9}")
    print(f"  {'─'*20} {'─'*7} {'─'*12} {'─'*10} {'─'*12} {'─'*9}")
    for bucket in ['clean', '1-2 timeouts', '3-5 timeouts', '6+ timeouts']:
        d = time_buckets[bucket]
        avg = d['time'] / d['count'] if d['count'] > 0 else 0
        ans_pct = d['produced_answer'] / d['count'] * 100 if d['count'] > 0 else 0
        print(f"  {bucket:<20} {d['count']:>7} {d['time']:>10.0f}s {avg:>9.0f}s {d['produced_answer']:>12} {ans_pct:>8.1f}%")

    # ── 7. The real question: what patterns appear in FIRST timeout of an attempt? ──
    print("\n" + "=" * 80)
    print("7. FIRST TIMEOUT CODE PATTERN IN EACH ATTEMPT")
    print("=" * 80)

    first_timeout_patterns = Counter()
    first_timeout_libs = Counter()
    first_timeout_turn = Counter()

    for prob in problems:
        for att in prob.attempts:
            for turn in att.turns:
                if turn.is_error and 'timed out' in turn.output.lower():
                    first_timeout_turn[turn.turn_num] += 1

                    code = turn.code.lower()
                    # Classify the first timeout
                    if 'for' in code and ('for' in code[code.index('for')+3:]):
                        first_timeout_patterns['nested_loops'] += 1
                    elif 'itertools.product' in code:
                        first_timeout_patterns['itertools.product'] += 1
                    elif 'itertools.combinations' in code or 'itertools.permutations' in code:
                        first_timeout_patterns['itertools.comb/perm'] += 1
                    elif '.solve(' in code:
                        first_timeout_patterns['sympy.solve'] += 1
                    elif '.simplify(' in code or '.expand(' in code:
                        first_timeout_patterns['sympy.simplify/expand'] += 1
                    elif 'milp(' in code:
                        first_timeout_patterns['milp'] += 1
                    elif 'while' in code:
                        first_timeout_patterns['while_loop'] += 1
                    elif 'random' in code:
                        first_timeout_patterns['random_sampling'] += 1
                    else:
                        first_timeout_patterns['other'] += 1

                    # Libraries
                    if 'sympy' in code or 'sp.' in code:
                        first_timeout_libs['sympy'] += 1
                    if 'numpy' in code or 'np.' in code:
                        first_timeout_libs['numpy'] += 1
                    if 'itertools' in code:
                        first_timeout_libs['itertools'] += 1
                    if 'milp' in code:
                        first_timeout_libs['milp'] += 1

                    break  # Only first timeout

    print(f"\n  Pattern in first timeout of each attempt:")
    print(f"  {'Pattern':<25} {'Count':>8}")
    print(f"  {'─'*25} {'─'*8}")
    for pat, count in first_timeout_patterns.most_common():
        print(f"  {pat:<25} {count:>8}")

    print(f"\n  Turn number of first timeout:")
    print(f"  {'Turn':<8} {'Count':>8}")
    print(f"  {'─'*8} {'─'*8}")
    for turn, count in sorted(first_timeout_turn.items())[:15]:
        print(f"  {turn:<8} {count:>8}")


if __name__ == '__main__':
    main()
