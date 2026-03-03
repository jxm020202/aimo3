#!/usr/bin/env python3
"""
Error Deep Dive — Cascade & Recovery Analysis
===============================================
Analyzes error recovery patterns: when errors occur, does the model recover?
How many turns does recovery take? Do cascaded errors correlate with None outcomes?

Usage: python3 log_exploration/error_deep_dive.py output/v22/diagnostic.log
"""

import sys
import os
import re
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def classify_error(output):
    """Classify error type from output text."""
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
        (r'StopIteration', 'StopIteration'),
        (r'AssertionError', 'AssertionError'),
    ]
    for pat, label in patterns:
        if re.search(pat, output, re.IGNORECASE):
            return label
    return 'Other'


def extract_next_action(turn):
    """Summarize what the model does in reasoning after an error."""
    text = turn.reasoning_text.lower()
    if not text:
        return 'no_reasoning'
    if any(w in text for w in ['fix', 'correct', 'mistake', 'bug', 'wrong']):
        return 'acknowledges_and_fixes'
    if any(w in text for w in ['try again', 'retry', 'redo', 'reattempt']):
        return 'retries'
    if any(w in text for w in ['different approach', 'alternative', 'instead', 'another way']):
        return 'changes_approach'
    if any(w in text for w in ['simplif', 'manual', 'by hand', 'without']):
        return 'simplifies'
    if any(w in text for w in ['import', 'define', 'set up']):
        return 'adds_missing_def'
    return 'continues'


def analyze_recovery(problems):
    """Analyze error recovery patterns across all attempts."""
    print("=" * 80)
    print("ERROR RECOVERY ANALYSIS")
    print("=" * 80)

    # Track per-error events
    recovery_events = []  # (error_type, recovered, turns_to_recover, next_action, problem_id, attempt_num)
    cascade_info = []     # (problem_id, attempt_num, error_count, is_none, answer_correct)

    for prob in problems:
        for att in prob.attempts:
            turns = att.turns
            if not turns:
                continue

            error_indices = [i for i, t in enumerate(turns) if t.is_error]
            if not error_indices:
                continue

            # Cascade tracking
            cascade_info.append((
                prob.problem_id,
                att.attempt_num,
                len(error_indices),
                att.is_none,
                att.answer == prob.expected if att.answer is not None and prob.expected is not None else None
            ))

            # Per-error recovery tracking
            for ei in error_indices:
                error_turn = turns[ei]
                error_type = classify_error(error_turn.output)

                # Check if subsequent turns recover (no more errors until end or next code)
                recovered = False
                turns_to_recover = 0

                for j in range(ei + 1, len(turns)):
                    turns_to_recover += 1
                    if turns[j].is_error:
                        recovered = False
                        break
                    if turns[j].code and not turns[j].is_error:
                        recovered = True
                        break
                else:
                    # Reached end of attempt without another code turn
                    if att.answer is not None:
                        recovered = True
                        turns_to_recover = len(turns) - ei - 1

                # What did the model do right after the error?
                next_action = 'end_of_attempt'
                if ei + 1 < len(turns):
                    next_action = extract_next_action(turns[ei + 1])

                recovery_events.append((
                    error_type, recovered, turns_to_recover, next_action,
                    prob.problem_id, att.attempt_num
                ))

    # ── 1. Overall recovery rate ──
    print(f"\n{'─' * 60}")
    print("1. OVERALL RECOVERY RATE")
    print(f"{'─' * 60}")

    total = len(recovery_events)
    recovered = sum(1 for e in recovery_events if e[1])
    not_recovered = total - recovered

    print(f"  Total error events: {total}")
    print(f"  Recovered:          {recovered} ({100*recovered/total:.1f}%)" if total else "  No errors found")
    print(f"  Not recovered:      {not_recovered} ({100*not_recovered/total:.1f}%)" if total else "")

    # ── 2. Recovery rate by error type ──
    print(f"\n{'─' * 60}")
    print("2. RECOVERY RATE BY ERROR TYPE")
    print(f"{'─' * 60}")

    by_type = defaultdict(lambda: {'total': 0, 'recovered': 0, 'turns_to_recover': []})
    for error_type, rec, ttr, _, _, _ in recovery_events:
        by_type[error_type]['total'] += 1
        if rec:
            by_type[error_type]['recovered'] += 1
            by_type[error_type]['turns_to_recover'].append(ttr)

    print(f"\n  {'Error Type':<22} {'Total':>6} {'Recovered':>10} {'Rate':>8} {'Avg Turns':>10}")
    print(f"  {'─'*22} {'─'*6} {'─'*10} {'─'*8} {'─'*10}")

    for etype in sorted(by_type, key=lambda x: by_type[x]['total'], reverse=True):
        d = by_type[etype]
        rate = 100 * d['recovered'] / d['total'] if d['total'] else 0
        avg_t = sum(d['turns_to_recover']) / len(d['turns_to_recover']) if d['turns_to_recover'] else 0
        print(f"  {etype:<22} {d['total']:>6} {d['recovered']:>10} {rate:>7.1f}% {avg_t:>9.1f}")

    # ── 3. Next action after error ──
    print(f"\n{'─' * 60}")
    print("3. MODEL BEHAVIOR AFTER ERROR")
    print(f"{'─' * 60}")

    action_stats = defaultdict(lambda: {'total': 0, 'recovered': 0})
    for _, rec, _, action, _, _ in recovery_events:
        action_stats[action]['total'] += 1
        if rec:
            action_stats[action]['recovered'] += 1

    print(f"\n  {'Action':<28} {'Count':>6} {'Recovery Rate':>14}")
    print(f"  {'─'*28} {'─'*6} {'─'*14}")

    for action in sorted(action_stats, key=lambda x: action_stats[x]['total'], reverse=True):
        d = action_stats[action]
        rate = 100 * d['recovered'] / d['total'] if d['total'] else 0
        print(f"  {action:<28} {d['total']:>6} {rate:>13.1f}%")

    # ── 4. Recovery: recovered vs not — what's different? ──
    print(f"\n{'─' * 60}")
    print("4. RECOVERED vs NOT RECOVERED — ACTION COMPARISON")
    print(f"{'─' * 60}")

    rec_actions = Counter()
    unrec_actions = Counter()
    for _, rec, _, action, _, _ in recovery_events:
        if rec:
            rec_actions[action] += 1
        else:
            unrec_actions[action] += 1

    all_actions = set(list(rec_actions.keys()) + list(unrec_actions.keys()))
    total_rec = sum(rec_actions.values())
    total_unrec = sum(unrec_actions.values())

    print(f"\n  {'Action':<28} {'% of Recovered':>16} {'% of Not Recov':>16}")
    print(f"  {'─'*28} {'─'*16} {'─'*16}")

    for action in sorted(all_actions):
        r_pct = 100 * rec_actions.get(action, 0) / total_rec if total_rec else 0
        u_pct = 100 * unrec_actions.get(action, 0) / total_unrec if total_unrec else 0
        print(f"  {action:<28} {r_pct:>15.1f}% {u_pct:>15.1f}%")

    # ── 5. Error cascades and None correlation ──
    print(f"\n{'─' * 60}")
    print("5. ERROR CASCADES AND NONE CORRELATION")
    print(f"{'─' * 60}")

    # Group cascade info by error count
    by_cascade_size = defaultdict(lambda: {'total': 0, 'nones': 0, 'correct': 0})
    for pid, anum, ecount, is_none, is_correct in cascade_info:
        by_cascade_size[ecount]['total'] += 1
        if is_none:
            by_cascade_size[ecount]['nones'] += 1
        if is_correct:
            by_cascade_size[ecount]['correct'] += 1

    print(f"\n  {'Errors/Attempt':>15} {'Attempts':>9} {'None Rate':>10} {'Correct Rate':>13}")
    print(f"  {'─'*15} {'─'*9} {'─'*10} {'─'*13}")

    for ecount in sorted(by_cascade_size):
        d = by_cascade_size[ecount]
        none_rate = 100 * d['nones'] / d['total'] if d['total'] else 0
        corr_rate = 100 * d['correct'] / d['total'] if d['total'] else 0
        print(f"  {ecount:>15} {d['total']:>9} {none_rate:>9.1f}% {corr_rate:>12.1f}%")

    # ── 6. Worst cascade examples ──
    print(f"\n{'─' * 60}")
    print("6. WORST ERROR CASCADES (5+ errors in one attempt)")
    print(f"{'─' * 60}")

    heavy = [(pid, anum, ec, none, corr) for pid, anum, ec, none, corr in cascade_info if ec >= 5]
    heavy.sort(key=lambda x: x[2], reverse=True)

    if not heavy:
        print("\n  No attempts with 5+ errors.")
    else:
        print(f"\n  {'Problem':<12} {'Attempt':>8} {'Errors':>7} {'None?':>6} {'Correct?':>9}")
        print(f"  {'─'*12} {'─'*8} {'─'*7} {'─'*6} {'─'*9}")
        for pid, anum, ec, none, corr in heavy[:20]:
            none_str = 'Yes' if none else 'No'
            corr_str = 'Yes' if corr else ('No' if corr is not None else '?')
            print(f"  {pid:<12} {anum:>8} {ec:>7} {none_str:>6} {corr_str:>9}")

    # ── 7. Per-problem error impact ──
    print(f"\n{'─' * 60}")
    print("7. PROBLEMS WITH HIGHEST ERROR RATES (top 15)")
    print(f"{'─' * 60}")

    prob_errors = []
    for prob in problems:
        total_turns = sum(len(a.turns) for a in prob.attempts)
        error_turns = sum(1 for a in prob.attempts for t in a.turns if t.is_error)
        if total_turns > 0:
            prob_errors.append((prob.problem_id, error_turns, total_turns,
                                100 * error_turns / total_turns, prob.correct))

    prob_errors.sort(key=lambda x: x[3], reverse=True)

    print(f"\n  {'Problem':<12} {'Err Turns':>10} {'Total Turns':>12} {'Error %':>8} {'Correct?':>9}")
    print(f"  {'─'*12} {'─'*10} {'─'*12} {'─'*8} {'─'*9}")
    for pid, et, tt, pct, corr in prob_errors[:15]:
        corr_str = 'Yes' if corr else 'No'
        print(f"  {pid:<12} {et:>10} {tt:>12} {pct:>7.1f}% {corr_str:>9}")

    # ── 8. Actionable insights ──
    print(f"\n{'=' * 80}")
    print("ACTIONABLE INSIGHTS")
    print("=" * 80)

    # Find most damaging error type (lowest recovery rate with sufficient count)
    worst_recovery = None
    for etype, d in sorted(by_type.items(), key=lambda x: x[1]['total'], reverse=True):
        if d['total'] >= 3:
            rate = d['recovered'] / d['total']
            if worst_recovery is None or rate < worst_recovery[1]:
                worst_recovery = (etype, rate, d['total'])

    if worst_recovery:
        print(f"\n  [!] Most damaging error type: {worst_recovery[0]}")
        print(f"      Recovery rate: {100*worst_recovery[1]:.0f}% (out of {worst_recovery[2]} occurrences)")
        print(f"      -> Consider adding specific prompt guidance to prevent this error class.")

    # Check if multi-error attempts strongly correlate with None
    single_err = by_cascade_size.get(1, {'total': 0, 'nones': 0})
    multi_err = {'total': 0, 'nones': 0}
    for k, v in by_cascade_size.items():
        if k >= 3:
            multi_err['total'] += v['total']
            multi_err['nones'] += v['nones']

    if multi_err['total'] > 0 and single_err['total'] > 0:
        single_none_rate = single_err['nones'] / single_err['total']
        multi_none_rate = multi_err['nones'] / multi_err['total']
        print(f"\n  [!] Error cascade impact on None rate:")
        print(f"      1 error:  {100*single_none_rate:.0f}% None rate")
        print(f"      3+ errors: {100*multi_none_rate:.0f}% None rate")
        if multi_none_rate > single_none_rate * 1.5:
            print(f"      -> Cascading errors dramatically increase None rate!")
            print(f"         Consider: early attempt abort after 3 consecutive errors.")

    # Best recovery strategy
    if action_stats:
        best_action = max(
            [(a, d) for a, d in action_stats.items() if d['total'] >= 3],
            key=lambda x: x[1]['recovered'] / x[1]['total'],
            default=None
        )
        if best_action:
            rate = 100 * best_action[1]['recovered'] / best_action[1]['total']
            print(f"\n  [!] Best recovery strategy: '{best_action[0]}' ({rate:.0f}% recovery rate)")
            print(f"      -> Prompt could explicitly suggest this strategy after errors.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 log_exploration/error_deep_dive.py <diagnostic.log>")
        sys.exit(1)

    problems = parse_log(sys.argv[1])
    analyze_recovery(problems)


if __name__ == '__main__':
    main()
