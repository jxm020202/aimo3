#!/usr/bin/env python3
"""
Error Timing — Temporal Analysis
==================================
Error rate by turn number, attempt number, error clustering by problem,
and time cost of errors.

Usage: python3 log_exploration/error_timing.py output/v22/diagnostic.log
"""

import sys
import os
import re
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def classify_problem_type(prob):
    """Infer problem type from problem text and reasoning."""
    text = (prob.problem_text or '').lower()
    # Also scan first attempt's first turn reasoning for topic clues
    reasoning = ''
    if prob.attempts and prob.attempts[0].turns:
        reasoning = (prob.attempts[0].turns[0].reasoning_text or '').lower()

    combined = text + ' ' + reasoning

    if any(w in combined for w in ['probability', 'expected value', 'random', 'dice', 'coin', 'choose at random']):
        return 'probability'
    if any(w in combined for w in ['triangle', 'circle', 'angle', 'polygon', 'area', 'perimeter',
                                    'circumscribe', 'inscribe', 'perpendicular', 'midpoint',
                                    'quadrilateral', 'rectangle', 'square']):
        return 'geometry'
    if any(w in combined for w in ['sequence', 'series', 'recurrence', 'a_n', 'a_1', 'fibonacci',
                                    'arithmetic progression', 'geometric progression']):
        return 'sequences'
    if any(w in combined for w in ['prime', 'divisor', 'gcd', 'lcm', 'modulo', 'mod ', 'congruent',
                                    'remainder', 'factor', 'coprime', 'euler', 'totient']):
        return 'number_theory'
    if any(w in combined for w in ['polynomial', 'equation', 'root', 'solve', 'coefficient',
                                    'quadratic', 'cubic', 'degree']):
        return 'algebra'
    if any(w in combined for w in ['how many', 'count', 'number of ways', 'permutation',
                                    'combination', 'arrange', 'select', 'choose']):
        return 'combinatorics'
    if any(w in combined for w in ['matrix', 'determinant', 'eigenvalue', 'vector', 'linear']):
        return 'linear_algebra'
    if any(w in combined for w in ['integral', 'derivative', 'limit', 'continuous', 'differentiable']):
        return 'calculus'
    if any(w in combined for w in ['function', 'f(x)', 'domain', 'range', 'injective', 'surjective']):
        return 'functions'
    return 'other'


def analyze_error_timing(problems):
    """Temporal and clustering analysis of errors."""
    print("=" * 80)
    print("ERROR TIMING & TEMPORAL ANALYSIS")
    print("=" * 80)

    # ── 1. Error rate by turn number ──
    print(f"\n{'─' * 60}")
    print("1. ERROR RATE BY TURN NUMBER")
    print(f"{'─' * 60}")

    turn_stats = defaultdict(lambda: {'total': 0, 'errors': 0})
    for prob in problems:
        for att in prob.attempts:
            for turn in att.turns:
                turn_stats[turn.turn_num]['total'] += 1
                if turn.is_error:
                    turn_stats[turn.turn_num]['errors'] += 1

    print(f"\n  {'Turn':>6} {'Total':>7} {'Errors':>7} {'Error %':>8} {'Visual':}")
    print(f"  {'─'*6} {'─'*7} {'─'*7} {'─'*8} {'─'*30}")

    max_turn = max(turn_stats.keys()) if turn_stats else 0
    for t in range(1, max_turn + 1):
        if t not in turn_stats:
            continue
        d = turn_stats[t]
        rate = 100 * d['errors'] / d['total'] if d['total'] else 0
        bar = '#' * int(rate / 2)
        print(f"  {t:>6} {d['total']:>7} {d['errors']:>7} {rate:>7.1f}% {bar}")

    # Early vs late error rate
    early_turns = sum(d['errors'] for t, d in turn_stats.items() if t <= 3)
    early_total = sum(d['total'] for t, d in turn_stats.items() if t <= 3)
    late_turns = sum(d['errors'] for t, d in turn_stats.items() if t > 3)
    late_total = sum(d['total'] for t, d in turn_stats.items() if t > 3)

    if early_total and late_total:
        print(f"\n  Early (turns 1-3): {100*early_turns/early_total:.1f}% error rate ({early_turns}/{early_total})")
        print(f"  Late  (turns 4+):  {100*late_turns/late_total:.1f}% error rate ({late_turns}/{late_total})")

    # ── 2. Error rate by attempt number ──
    print(f"\n{'─' * 60}")
    print("2. ERROR RATE BY ATTEMPT NUMBER")
    print(f"{'─' * 60}")

    attempt_stats = defaultdict(lambda: {'total': 0, 'with_errors': 0, 'error_turns': 0, 'total_turns': 0})
    for prob in problems:
        for att in prob.attempts:
            attempt_stats[att.attempt_num]['total'] += 1
            has_error = any(t.is_error for t in att.turns)
            if has_error:
                attempt_stats[att.attempt_num]['with_errors'] += 1
            attempt_stats[att.attempt_num]['error_turns'] += sum(1 for t in att.turns if t.is_error)
            attempt_stats[att.attempt_num]['total_turns'] += len(att.turns)

    print(f"\n  {'Attempt':>8} {'Attempts':>9} {'With Err':>9} {'%':>7} {'Err Turns':>10} {'Tot Turns':>10} {'Turn Err%':>10}")
    print(f"  {'─'*8} {'─'*9} {'─'*9} {'─'*7} {'─'*10} {'─'*10} {'─'*10}")

    for anum in sorted(attempt_stats):
        d = attempt_stats[anum]
        pct = 100 * d['with_errors'] / d['total'] if d['total'] else 0
        turn_pct = 100 * d['error_turns'] / d['total_turns'] if d['total_turns'] else 0
        print(f"  {anum:>8} {d['total']:>9} {d['with_errors']:>9} {pct:>6.1f}% {d['error_turns']:>10} {d['total_turns']:>10} {turn_pct:>9.1f}%")

    # ── 3. Time cost of errors ──
    print(f"\n{'─' * 60}")
    print("3. TIME COST OF ERRORS")
    print(f"{'─' * 60}")

    error_attempt_times = []
    clean_attempt_times = []

    for prob in problems:
        for att in prob.attempts:
            if att.errors > 0:
                error_attempt_times.append(att.time_s)
            else:
                clean_attempt_times.append(att.time_s)

    if error_attempt_times and clean_attempt_times:
        avg_err = sum(error_attempt_times) / len(error_attempt_times)
        avg_clean = sum(clean_attempt_times) / len(clean_attempt_times)
        total_err_time = sum(error_attempt_times)
        total_clean_time = sum(clean_attempt_times)

        print(f"\n  Attempts with errors:    {len(error_attempt_times)}")
        print(f"  Attempts without errors: {len(clean_attempt_times)}")
        print(f"")
        print(f"  Avg time (with errors):    {avg_err:.1f}s")
        print(f"  Avg time (without errors): {avg_clean:.1f}s")
        print(f"  Time overhead of errors:   {avg_err - avg_clean:+.1f}s ({100*(avg_err/avg_clean - 1):+.0f}%)")
        print(f"")
        print(f"  Total time on errored attempts:  {total_err_time:.0f}s ({total_err_time/60:.1f}m)")
        print(f"  Total time on clean attempts:    {total_clean_time:.0f}s ({total_clean_time/60:.1f}m)")

        # Estimate wasted time: if errored attempts took avg_clean instead
        wasted = total_err_time - len(error_attempt_times) * avg_clean
        print(f"  Estimated time wasted by errors: {max(0,wasted):.0f}s ({max(0,wasted)/60:.1f}m)")

    # ── 4. Error clustering by problem ──
    print(f"\n{'─' * 60}")
    print("4. ERROR CLUSTERING BY PROBLEM")
    print(f"{'─' * 60}")

    prob_error_data = []
    for prob in problems:
        err_count = sum(1 for a in prob.attempts for t in a.turns if t.is_error)
        total_turns = sum(len(a.turns) for a in prob.attempts)
        prob_error_data.append((
            prob.problem_id, err_count, total_turns,
            100 * err_count / total_turns if total_turns else 0,
            prob.correct, len(prob.attempts),
            classify_problem_type(prob)
        ))

    # Distribution of errors per problem
    err_counts = [d[1] for d in prob_error_data]
    zero_err = sum(1 for c in err_counts if c == 0)
    low_err = sum(1 for c in err_counts if 1 <= c <= 3)
    med_err = sum(1 for c in err_counts if 4 <= c <= 8)
    high_err = sum(1 for c in err_counts if c > 8)

    print(f"\n  Error distribution across {len(prob_error_data)} problems:")
    print(f"    0 errors:    {zero_err} problems")
    print(f"    1-3 errors:  {low_err} problems")
    print(f"    4-8 errors:  {med_err} problems")
    print(f"    9+ errors:   {high_err} problems")

    # Top error-heavy problems
    prob_error_data.sort(key=lambda x: x[1], reverse=True)
    print(f"\n  Most error-prone problems:")
    print(f"  {'Problem':<12} {'Errors':>7} {'Turns':>6} {'Err%':>6} {'Correct':>8} {'Atts':>5} {'Type':<15}")
    print(f"  {'─'*12} {'─'*7} {'─'*6} {'─'*6} {'─'*8} {'─'*5} {'─'*15}")
    for pid, ec, tt, pct, corr, natts, ptype in prob_error_data[:15]:
        corr_str = 'Yes' if corr else 'No'
        print(f"  {pid:<12} {ec:>7} {tt:>6} {pct:>5.0f}% {corr_str:>8} {natts:>5} {ptype:<15}")

    # Problems with 0 errors — how do they perform?
    zero_err_probs = [d for d in prob_error_data if d[1] == 0]
    has_err_probs = [d for d in prob_error_data if d[1] > 0]
    if zero_err_probs and has_err_probs:
        zero_correct = sum(1 for d in zero_err_probs if d[4])
        has_correct = sum(1 for d in has_err_probs if d[4])
        print(f"\n  Correctness comparison:")
        print(f"    Problems with 0 errors:  {100*zero_correct/len(zero_err_probs):.0f}% correct ({zero_correct}/{len(zero_err_probs)})")
        print(f"    Problems with 1+ errors: {100*has_correct/len(has_err_probs):.0f}% correct ({has_correct}/{len(has_err_probs)})")

    # ── 5. Error rate by problem type ──
    print(f"\n{'─' * 60}")
    print("5. ERROR RATE BY PROBLEM TYPE")
    print(f"{'─' * 60}")

    type_stats = defaultdict(lambda: {'problems': 0, 'errors': 0, 'turns': 0, 'correct': 0})
    for pid, ec, tt, pct, corr, natts, ptype in prob_error_data:
        type_stats[ptype]['problems'] += 1
        type_stats[ptype]['errors'] += ec
        type_stats[ptype]['turns'] += tt
        if corr:
            type_stats[ptype]['correct'] += 1

    print(f"\n  {'Type':<18} {'Problems':>9} {'Errors':>7} {'Turns':>7} {'Err%':>6} {'Correct%':>9}")
    print(f"  {'─'*18} {'─'*9} {'─'*7} {'─'*7} {'─'*6} {'─'*9}")

    for ptype in sorted(type_stats, key=lambda x: type_stats[x]['errors'], reverse=True):
        d = type_stats[ptype]
        err_rate = 100 * d['errors'] / d['turns'] if d['turns'] else 0
        corr_rate = 100 * d['correct'] / d['problems'] if d['problems'] else 0
        print(f"  {ptype:<18} {d['problems']:>9} {d['errors']:>7} {d['turns']:>7} {err_rate:>5.1f}% {corr_rate:>8.0f}%")

    # ── 6. Error streaks within attempts ──
    print(f"\n{'─' * 60}")
    print("6. ERROR STREAKS (consecutive error turns within attempts)")
    print(f"{'─' * 60}")

    streak_lengths = []
    for prob in problems:
        for att in prob.attempts:
            current_streak = 0
            for turn in att.turns:
                if turn.is_error:
                    current_streak += 1
                else:
                    if current_streak > 0:
                        streak_lengths.append(current_streak)
                    current_streak = 0
            if current_streak > 0:
                streak_lengths.append(current_streak)

    if streak_lengths:
        streak_counter = Counter(streak_lengths)
        print(f"\n  {'Streak Length':>13} {'Count':>6} {'Cumulative %':>13}")
        print(f"  {'─'*13} {'─'*6} {'─'*13}")

        total_streaks = len(streak_lengths)
        cumulative = 0
        for length in sorted(streak_counter):
            count = streak_counter[length]
            cumulative += count
            pct = 100 * cumulative / total_streaks
            print(f"  {length:>13} {count:>6} {pct:>12.1f}%")

        avg_streak = sum(streak_lengths) / len(streak_lengths)
        max_streak = max(streak_lengths)
        print(f"\n  Average streak length: {avg_streak:.1f}")
        print(f"  Maximum streak length: {max_streak}")
        if max_streak >= 3:
            print(f"  -> Streaks of 3+ errors suggest the model is stuck and not recovering.")
            print(f"     Consider: prompt hint 'If you get 3 errors in a row, restart from scratch.'")

    # ── 7. First-turn errors ──
    print(f"\n{'─' * 60}")
    print("7. FIRST-TURN ERRORS (errors on the very first code execution)")
    print(f"{'─' * 60}")

    first_turn_errors = 0
    first_turn_total = 0
    first_turn_error_types = Counter()

    for prob in problems:
        for att in prob.attempts:
            if att.turns:
                first_turn_total += 1
                if att.turns[0].is_error:
                    first_turn_errors += 1
                    etype = classify_error_type(att.turns[0].output) if att.turns[0].output else 'Unknown'
                    first_turn_error_types[etype] += 1

    if first_turn_total:
        print(f"\n  First-turn error rate: {100*first_turn_errors/first_turn_total:.1f}% ({first_turn_errors}/{first_turn_total})")
        if first_turn_error_types:
            print(f"\n  First-turn error types:")
            for etype, count in first_turn_error_types.most_common():
                print(f"    {etype}: {count}")
        print(f"\n  -> First-turn errors waste the most time (model has to redo initial setup).")
        print(f"     These are the highest-value errors to prevent via prompt engineering.")

    # ── 8. Actionable insights ──
    print(f"\n{'=' * 80}")
    print("ACTIONABLE INSIGHTS")
    print("=" * 80)

    # When do errors happen most?
    if turn_stats:
        worst_turn = max(turn_stats, key=lambda t: turn_stats[t]['errors'] / turn_stats[t]['total'] if turn_stats[t]['total'] > 5 else 0)
        worst_rate = 100 * turn_stats[worst_turn]['errors'] / turn_stats[worst_turn]['total']
        print(f"\n  [!] Highest error rate at turn {worst_turn} ({worst_rate:.0f}%)")

    if early_total and late_total:
        early_rate = 100 * early_turns / early_total
        late_rate = 100 * late_turns / late_total
        if late_rate > early_rate * 1.3:
            print(f"  [!] Errors increase in later turns ({early_rate:.0f}% early vs {late_rate:.0f}% late)")
            print(f"      -> Model may be getting more speculative. Prompt: 'Stay methodical in later steps.'")
        elif early_rate > late_rate * 1.3:
            print(f"  [!] Errors concentrate early ({early_rate:.0f}% early vs {late_rate:.0f}% late)")
            print(f"      -> Model needs better initial setup. Ensure imports/definitions in first cell.")

    if error_attempt_times and clean_attempt_times:
        wasted = total_err_time - len(error_attempt_times) * avg_clean
        if wasted > 60:
            print(f"  [!] ~{wasted/60:.0f} minutes wasted on errors — that's computation time for")
            print(f"      {int(wasted / avg_clean)} extra clean attempts!")

    # Problem type with most errors
    if type_stats:
        worst_type = max(type_stats, key=lambda t: type_stats[t]['errors'] / type_stats[t]['turns'] if type_stats[t]['turns'] > 10 else 0)
        worst_type_rate = 100 * type_stats[worst_type]['errors'] / type_stats[worst_type]['turns'] if type_stats[worst_type]['turns'] else 0
        print(f"  [!] Problem type with highest error rate: {worst_type} ({worst_type_rate:.0f}%)")
        print(f"      -> Consider type-specific prompt strategies for {worst_type} problems.")


def classify_error_type(output):
    """Get the base Python error type from output."""
    patterns = [
        (r'NameError', 'NameError'),
        (r'TypeError', 'TypeError'),
        (r'ValueError', 'ValueError'),
        (r'IndexError', 'IndexError'),
        (r'KeyError', 'KeyError'),
        (r'AttributeError', 'AttributeError'),
        (r'ZeroDivisionError', 'ZeroDivisionError'),
        (r'OverflowError', 'OverflowError'),
        (r'MemoryError', 'MemoryError'),
        (r'RecursionError', 'RecursionError'),
        (r'TimeoutError|timed?\s*out|execution.*time', 'Timeout'),
        (r'SyntaxError', 'SyntaxError'),
        (r'ImportError|ModuleNotFoundError', 'ImportError'),
        (r'RuntimeError', 'RuntimeError'),
    ]
    for pat, label in patterns:
        if re.search(pat, output, re.IGNORECASE):
            return label
    return 'Other'


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 log_exploration/error_timing.py <diagnostic.log>")
        sys.exit(1)

    problems = parse_log(sys.argv[1])
    analyze_error_timing(problems)


if __name__ == '__main__':
    main()
