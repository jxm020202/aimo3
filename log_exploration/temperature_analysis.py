#!/usr/bin/env python3
"""
AIMO3 Temperature Effectiveness Analysis
==========================================
Analyzes how different temperatures affect answer quality, correctness,
reasoning patterns, and overall performance.

Usage:
    python log_exploration/temperature_analysis.py <logfile>

Outputs:
    - Summary table: accuracy, None rate, errors per temp
    - Unique correct: problems solved ONLY at a specific temp
    - Reasoning/code/error stats per temp
    - Timing analysis per temp
    - Recommendation for optimal temp distribution
"""

import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def bucket_temp(t):
    """Round temperature to nearest 0.1 for bucketing."""
    if t is None:
        return None
    return round(t, 1)


def analyze_temperatures(problems):
    """Full temperature analysis across all problems and attempts."""

    # Collect all attempts grouped by temperature
    by_temp = defaultdict(list)  # temp -> [(problem, attempt), ...]
    all_attempts = []

    for p in problems:
        for a in p.attempts:
            t = bucket_temp(a.temperature)
            by_temp[t].append((p, a))
            all_attempts.append((p, a))

    temps_sorted = sorted([t for t in by_temp.keys() if t is not None])

    # ── Section 1: Summary Table ──
    print("=" * 90)
    print("  TEMPERATURE EFFECTIVENESS ANALYSIS")
    print("=" * 90)
    print(f"\n  Total problems: {len(problems)}")
    print(f"  Total attempts: {len(all_attempts)}")
    print(f"  Temperatures found: {temps_sorted}")

    print(f"\n  {'Temp':>5} {'Total':>6} {'Correct':>8} {'Wrong':>6} {'None':>6} {'Acc%':>7} {'NoneR%':>7} {'AvgErr':>7} {'AvgTok':>8} {'AvgTime':>8}")
    print(f"  {'─'*5} {'─'*6} {'─'*8} {'─'*6} {'─'*6} {'─'*7} {'─'*7} {'─'*7} {'─'*8} {'─'*8}")

    temp_stats = {}
    for t in temps_sorted:
        pairs = by_temp[t]
        total = len(pairs)
        correct = sum(1 for p, a in pairs if a.answer is not None and a.answer == p.expected)
        wrong = sum(1 for p, a in pairs if a.answer is not None and a.answer != p.expected)
        nones = sum(1 for _, a in pairs if a.is_none)
        non_none = total - nones
        acc = (correct / non_none * 100) if non_none > 0 else 0.0
        none_rate = (nones / total * 100) if total > 0 else 0.0
        avg_errors = sum(a.errors for _, a in pairs) / total if total > 0 else 0.0
        avg_tokens = sum(a.tokens for _, a in pairs) / total if total > 0 else 0.0
        avg_time = sum(a.time_s for _, a in pairs) / total if total > 0 else 0.0

        temp_stats[t] = {
            'total': total, 'correct': correct, 'wrong': wrong, 'nones': nones,
            'acc': acc, 'none_rate': none_rate, 'avg_errors': avg_errors,
            'avg_tokens': avg_tokens, 'avg_time': avg_time, 'non_none': non_none,
        }

        print(f"  {t:>5.1f} {total:>6} {correct:>8} {wrong:>6} {nones:>6} {acc:>6.1f}% {none_rate:>6.1f}% {avg_errors:>7.2f} {avg_tokens:>8.0f} {avg_time:>7.1f}s")

    # Unknown temps
    if None in by_temp:
        pairs = by_temp[None]
        print(f"  {'?':>5} {len(pairs):>6}  (temperature not recorded)")

    # ── Section 2: Correct Rate Including Nones (raw accuracy) ──
    print(f"\n\n  RAW ACCURACY (correct / total, including Nones as wrong)")
    print(f"  {'Temp':>5} {'Correct':>8} {'Total':>6} {'RawAcc%':>8}")
    print(f"  {'─'*5} {'─'*8} {'─'*6} {'─'*8}")
    for t in temps_sorted:
        s = temp_stats[t]
        raw_acc = (s['correct'] / s['total'] * 100) if s['total'] > 0 else 0.0
        print(f"  {t:>5.1f} {s['correct']:>8} {s['total']:>6} {raw_acc:>7.1f}%")

    # ── Section 3: Per-Problem Temperature Breakdown ──
    print(f"\n\n  PER-PROBLEM TEMPERATURE CORRECTNESS")
    print(f"  Which temps get each problem right?\n")

    # For each problem, track which temps got correct answers
    prob_temp_correct = defaultdict(set)  # pid -> set of temps that got it correct
    prob_temp_attempts = defaultdict(lambda: defaultdict(int))  # pid -> temp -> count
    prob_temp_correct_count = defaultdict(lambda: defaultdict(int))  # pid -> temp -> correct count

    for p in problems:
        for a in p.attempts:
            t = bucket_temp(a.temperature)
            if t is None:
                continue
            prob_temp_attempts[p.problem_id][t] += 1
            if a.answer is not None and a.answer == p.expected:
                prob_temp_correct[p.problem_id].add(t)
                prob_temp_correct_count[p.problem_id][t] += 1

    # Header
    temp_hdrs = ''.join(f' {t:>5.1f}' for t in temps_sorted)
    print(f"  {'ProbID':<10} {'Exp':>7} {'Final':>7} {'OK':>3}{temp_hdrs}")
    sep = ''.join(' ' + '─' * 5 for _ in temps_sorted)
    print(f"  {'─'*10} {'─'*7} {'─'*7} {'─'*3}{sep}")

    for p in sorted(problems, key=lambda x: x.problem_id):
        exp = str(p.expected) if p.expected is not None else '?'
        pred = str(p.predicted) if p.predicted is not None else '?'
        ok = 'Y' if p.correct else 'N'
        cells = []
        for t in temps_sorted:
            att_count = prob_temp_attempts[p.problem_id].get(t, 0)
            corr_count = prob_temp_correct_count[p.problem_id].get(t, 0)
            if att_count == 0:
                cells.append('    -')
            elif corr_count > 0:
                cells.append(f' {corr_count}/{att_count:>2}')  # e.g. "2/ 3"
            else:
                cells.append(f' 0/{att_count:>2}')
        print(f"  {p.problem_id:<10} {exp:>7} {pred:>7} {ok:>3}{''.join(cells)}")

    # ── Section 4: Unique Correct by Temperature ──
    print(f"\n\n  UNIQUE CORRECT BY TEMPERATURE")
    print(f"  Problems where ONLY a specific temperature found the correct answer\n")

    unique_by_temp = defaultdict(list)  # temp -> [problem_ids]
    for pid, temps_set in prob_temp_correct.items():
        if len(temps_set) == 1:
            unique_by_temp[list(temps_set)[0]].append(pid)

    any_unique = False
    for t in temps_sorted:
        pids = unique_by_temp.get(t, [])
        if pids:
            any_unique = True
            # Get expected answers for context
            pid_details = []
            for pid in pids:
                for p in problems:
                    if p.problem_id == pid:
                        pid_details.append(f"{pid} (exp={p.expected}, final={'CORR' if p.correct else 'WRONG'})")
                        break
            print(f"  Temp {t:.1f}: {len(pids)} unique correct")
            for d in pid_details:
                print(f"    - {d}")

    if not any_unique:
        print("  No problems with unique-temperature-only correct answers.")

    # Also show problems where a temp is the DOMINANT source of correct answers
    print(f"\n\n  DOMINANT TEMPERATURE PER PROBLEM")
    print(f"  Temperature that produced the most correct answers for each problem\n")

    for p in sorted(problems, key=lambda x: x.problem_id):
        if not prob_temp_correct[p.problem_id]:
            continue
        best_temp = max(
            prob_temp_correct_count[p.problem_id].items(),
            key=lambda x: x[1]
        )
        total_correct = sum(prob_temp_correct_count[p.problem_id].values())
        if total_correct > 0:
            print(f"  {p.problem_id}: best temp={best_temp[0]:.1f} ({best_temp[1]}/{total_correct} correct)")

    # ── Section 5: Reasoning Depth by Temperature ──
    print(f"\n\n  REASONING DEPTH BY TEMPERATURE")
    print(f"  {'Temp':>5} {'AvgTurns':>9} {'AvgReasoning':>13} {'AvgCodeCalls':>13} {'AvgCodeLen':>11}")
    print(f"  {'─'*5} {'─'*9} {'─'*13} {'─'*13} {'─'*11}")

    for t in temps_sorted:
        pairs = by_temp[t]
        avg_turns = sum(len(a.turns) for _, a in pairs) / len(pairs) if pairs else 0
        avg_reasoning = 0
        total_code_len = 0
        total_code_calls = 0
        for _, a in pairs:
            for turn in a.turns:
                avg_reasoning += turn.reasoning_chars
            total_code_calls += a.code_calls
            for turn in a.turns:
                total_code_len += len(turn.code)
        avg_reasoning = avg_reasoning / len(pairs) if pairs else 0
        avg_code_calls = total_code_calls / len(pairs) if pairs else 0
        avg_code_len = total_code_len / len(pairs) if pairs else 0

        print(f"  {t:>5.1f} {avg_turns:>9.1f} {avg_reasoning:>13.0f} {avg_code_calls:>13.1f} {avg_code_len:>11.0f}")

    # ── Section 6: Error Analysis by Temperature ──
    print(f"\n\n  ERROR ANALYSIS BY TEMPERATURE")
    print(f"  {'Temp':>5} {'TotalErr':>9} {'AvgErr':>7} {'ErrRate%':>9} {'AvgErrPerTurn':>14}")
    print(f"  {'─'*5} {'─'*9} {'─'*7} {'─'*9} {'─'*14}")

    for t in temps_sorted:
        pairs = by_temp[t]
        total_errors = sum(a.errors for _, a in pairs)
        avg_errors = total_errors / len(pairs) if pairs else 0
        err_attempts = sum(1 for _, a in pairs if a.errors > 0)
        err_rate = (err_attempts / len(pairs) * 100) if pairs else 0
        total_turns = sum(len(a.turns) for _, a in pairs)
        err_per_turn = total_errors / total_turns if total_turns > 0 else 0
        print(f"  {t:>5.1f} {total_errors:>9} {avg_errors:>7.2f} {err_rate:>8.1f}% {err_per_turn:>14.3f}")

    # ── Section 7: Time Efficiency by Temperature ──
    print(f"\n\n  TIME EFFICIENCY BY TEMPERATURE")
    print(f"  {'Temp':>5} {'TotalTime':>10} {'AvgTime':>8} {'TimePerCorr':>12} {'TimePerAns':>11}")
    print(f"  {'─'*5} {'─'*10} {'─'*8} {'─'*12} {'─'*11}")

    for t in temps_sorted:
        s = temp_stats[t]
        pairs = by_temp[t]
        total_time = sum(a.time_s for _, a in pairs)
        time_per_correct = total_time / s['correct'] if s['correct'] > 0 else float('inf')
        time_per_answer = total_time / s['non_none'] if s['non_none'] > 0 else float('inf')

        tpc_str = f"{time_per_correct:.1f}s" if time_per_correct < 10000 else "inf"
        tpa_str = f"{time_per_answer:.1f}s" if time_per_answer < 10000 else "inf"

        print(f"  {t:>5.1f} {total_time:>9.0f}s {s['avg_time']:>7.1f}s {tpc_str:>12} {tpa_str:>11}")

    # ── Section 8: Simulated flat-temp comparison ──
    print(f"\n\n  SIMULATED FLAT-TEMPERATURE COMPARISON")
    print(f"  If we used all attempts at a single temperature, how many problems")
    print(f"  would be solved? (Based on observed per-temp correctness rates)\n")

    for t in temps_sorted:
        # Problems that got at least one correct at this temp
        solved_at_t = set()
        for p in problems:
            for a in p.attempts:
                bt = bucket_temp(a.temperature)
                if bt == t and a.answer is not None and a.answer == p.expected:
                    solved_at_t.add(p.problem_id)
                    break
        # Current schedule: problems solved overall
        solved_overall = set(p.problem_id for p in problems if p.correct)

        only_this = solved_at_t - set()  # all problems this temp gets right
        missed = solved_overall - solved_at_t  # problems schedule gets but this temp doesn't

        print(f"  Flat temp={t:.1f}: would solve {len(solved_at_t)}/{len(problems)} problems")
        if missed:
            print(f"    Would LOSE: {sorted(missed)}")

    # Current schedule
    solved_overall = set(p.problem_id for p in problems if p.correct)
    print(f"\n  Current schedule: solves {len(solved_overall)}/{len(problems)} problems")

    # ── Section 9: Recommendation ──
    print(f"\n\n{'='*90}")
    print(f"  RECOMMENDATION")
    print(f"{'='*90}\n")

    # Find best temps by various metrics
    best_acc_temp = max(temps_sorted, key=lambda t: temp_stats[t]['acc']) if temps_sorted else None
    best_raw_temp = max(temps_sorted, key=lambda t: temp_stats[t]['correct'] / max(temp_stats[t]['total'], 1)) if temps_sorted else None
    lowest_none_temp = min(temps_sorted, key=lambda t: temp_stats[t]['none_rate']) if temps_sorted else None
    most_efficient_temp = min(
        [t for t in temps_sorted if temp_stats[t]['correct'] > 0],
        key=lambda t: sum(a.time_s for _, a in by_temp[t]) / temp_stats[t]['correct'],
        default=None
    )

    print(f"  Best accuracy (correct/non-None): temp={best_acc_temp}")
    print(f"  Best raw accuracy (correct/total): temp={best_raw_temp}")
    print(f"  Lowest None rate: temp={lowest_none_temp}")
    print(f"  Most time-efficient (time/correct): temp={most_efficient_temp}")

    # Check if any temp is strictly dominated
    print(f"\n  Temperature assessment:")
    for t in temps_sorted:
        s = temp_stats[t]
        unique_count = len(unique_by_temp.get(t, []))
        assessment = []
        if s['acc'] >= max(temp_stats[t2]['acc'] for t2 in temps_sorted) - 1:
            assessment.append("TOP accuracy")
        if s['none_rate'] <= min(temp_stats[t2]['none_rate'] for t2 in temps_sorted) + 1:
            assessment.append("LOW none-rate")
        if s['none_rate'] >= max(temp_stats[t2]['none_rate'] for t2 in temps_sorted) - 1:
            assessment.append("HIGH none-rate")
        if unique_count > 0:
            assessment.append(f"UNIQUE: {unique_count} problems")
        if not assessment:
            assessment.append("no standout traits")
        print(f"  temp={t:.1f}: acc={s['acc']:.1f}%, none={s['none_rate']:.1f}%, unique={unique_count} -> {', '.join(assessment)}")

    # Final recommendation
    print(f"\n  Suggested strategy:")

    # Check if schedule adds value over flat
    schedule_solves = len(solved_overall)
    best_flat = max(temps_sorted, key=lambda t: len([
        p.problem_id for p in problems
        if any(bucket_temp(a.temperature) == t and a.answer is not None and a.answer == p.expected
               for a in p.attempts)
    ])) if temps_sorted else None

    if best_flat:
        best_flat_count = len([
            p.problem_id for p in problems
            if any(bucket_temp(a.temperature) == best_flat and a.answer is not None and a.answer == p.expected
                   for a in p.attempts)
        ])
        print(f"  - Best flat temperature: {best_flat:.1f} (solves {best_flat_count}/{len(problems)})")
        print(f"  - Current schedule: solves {schedule_solves}/{len(problems)}")
        if schedule_solves > best_flat_count:
            print(f"  - Schedule adds {schedule_solves - best_flat_count} problems over flat → KEEP schedule")
            print(f"  - Consider dropping temps with 0 unique correct and low accuracy")
        elif schedule_solves == best_flat_count:
            print(f"  - Schedule matches flat → SIMPLIFY to flat temp={best_flat:.1f}")
        else:
            print(f"  - Schedule loses {best_flat_count - schedule_solves} vs flat → SWITCH to flat temp={best_flat:.1f}")

    return temp_stats, by_temp, unique_by_temp


def main():
    if '--help' in sys.argv or len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0 if '--help' in sys.argv else 1)

    logfile = sys.argv[1]
    if not os.path.exists(logfile):
        print(f"Error: {logfile} not found")
        sys.exit(1)

    problems = parse_log(logfile)
    analyze_temperatures(problems)


if __name__ == '__main__':
    main()
