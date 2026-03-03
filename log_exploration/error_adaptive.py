#!/usr/bin/env python3
"""
Error-Based Adaptive Compute Allocation
=========================================
Uses error patterns as signals for adaptive time allocation.
Core question: Can we PREDICT from early errors whether a problem is easy/hard,
and use that to allocate compute smarter?

Key analyses:
1. Early error signals: Do errors in attempts 1-2 predict problem difficulty?
2. Error-based stopping rules: When do errors signal "stop wasting time"?
3. Time savings from error-aware early stop
4. None prediction from error patterns
5. Optimal budget simulation with error-aware allocation

Usage: python3 log_exploration/error_adaptive.py output/v22/diagnostic.log
"""

import sys
import os
import re
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


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


def compute_attempt_error_signature(attempt):
    """Compute error signature for an attempt: (error_count, timeout_count, none_flag)."""
    errors = sum(1 for t in attempt.turns if t.is_error)
    timeouts = sum(1 for t in attempt.turns if t.is_error and
                   re.search(r'timed?\s*out|timeout|execution.*time', t.output, re.IGNORECASE))
    return errors, timeouts, attempt.is_none


def analyze_error_adaptive(problems):
    """Error-based adaptive compute allocation analysis."""

    print("=" * 85)
    print("ERROR-BASED ADAPTIVE COMPUTE ALLOCATION")
    print("=" * 85)
    print("\nGoal: Use error patterns to predict difficulty and allocate time smarter.")
    print(f"Dataset: {len(problems)} problems, {sum(len(p.attempts) for p in problems)} attempts")

    # ── 1. Early Error Signals ──
    print(f"\n{'─' * 70}")
    print("1. EARLY ERROR SIGNALS — Do attempts 1-2 errors predict difficulty?")
    print(f"{'─' * 70}")

    # For each problem, compute early signals and final outcome
    problem_signals = []
    for prob in problems:
        early_atts = [a for a in prob.attempts if a.attempt_num <= 2]
        all_atts = prob.attempts

        early_errors = sum(sum(1 for t in a.turns if t.is_error) for a in early_atts)
        early_nones = sum(1 for a in early_atts if a.is_none)
        early_timeouts = sum(
            sum(1 for t in a.turns if t.is_error and
                re.search(r'timed?\s*out|timeout|execution.*time', t.output, re.IGNORECASE))
            for a in early_atts
        )
        early_correct = sum(1 for a in early_atts
                           if a.answer is not None and prob.expected is not None
                           and a.answer == prob.expected)

        total_errors = sum(sum(1 for t in a.turns if t.is_error) for a in all_atts)
        total_time = prob.wall_time
        unique_answers = len(set(a.answer for a in all_atts if a.answer is not None))

        problem_signals.append({
            'pid': prob.problem_id,
            'early_errors': early_errors,
            'early_nones': early_nones,
            'early_timeouts': early_timeouts,
            'early_correct': early_correct,
            'total_errors': total_errors,
            'total_time': total_time,
            'correct': prob.correct,
            'unique_answers': unique_answers,
            'num_attempts': len(all_atts),
            'wall_time': prob.wall_time,
        })

    # Classify by early error count
    buckets = {
        '0 early errors': [p for p in problem_signals if p['early_errors'] == 0],
        '1-2 early errors': [p for p in problem_signals if 1 <= p['early_errors'] <= 2],
        '3+ early errors': [p for p in problem_signals if p['early_errors'] >= 3],
    }

    print(f"\n  {'Early Error Bucket':<22} {'Problems':>9} {'Correct%':>9} {'Avg Time':>9} {'Avg Tot Err':>12}")
    print(f"  {'─'*22} {'─'*9} {'─'*9} {'─'*9} {'─'*12}")

    for label, probs in buckets.items():
        if not probs:
            continue
        n = len(probs)
        corr = sum(1 for p in probs if p['correct'])
        avg_time = sum(p['wall_time'] for p in probs) / n
        avg_err = sum(p['total_errors'] for p in probs) / n
        print(f"  {label:<22} {n:>9} {100*corr/n:>8.0f}% {avg_time:>8.0f}s {avg_err:>11.1f}")

    # Early correct signal
    print(f"\n  Early correct answer signal (attempts 1-2):")
    early_corr_yes = [p for p in problem_signals if p['early_correct'] >= 1]
    early_corr_no = [p for p in problem_signals if p['early_correct'] == 0]
    if early_corr_yes:
        pct_yes = 100 * sum(1 for p in early_corr_yes if p['correct']) / len(early_corr_yes)
        print(f"    Has correct in first 2 attempts: {len(early_corr_yes)} problems, {pct_yes:.0f}% final correct")
    if early_corr_no:
        pct_no = 100 * sum(1 for p in early_corr_no if p['correct']) / len(early_corr_no)
        print(f"    No correct in first 2 attempts:  {len(early_corr_no)} problems, {pct_no:.0f}% final correct")

    # ── 2. Error-Based Difficulty Classification ──
    print(f"\n{'─' * 70}")
    print("2. ERROR-BASED DIFFICULTY CLASSIFICATION")
    print(f"{'─' * 70}")

    # Classify each problem as EASY / MEDIUM / HARD based on error signals
    for p in problem_signals:
        if p['early_correct'] >= 1 and p['early_errors'] == 0:
            p['difficulty'] = 'EASY'
        elif p['early_correct'] >= 1 or (p['early_errors'] <= 1 and p['early_nones'] == 0):
            p['difficulty'] = 'MEDIUM'
        else:
            p['difficulty'] = 'HARD'

    diff_groups = defaultdict(list)
    for p in problem_signals:
        diff_groups[p['difficulty']].append(p)

    print(f"\n  Classification rule:")
    print(f"    EASY:   Correct in first 2 attempts AND 0 early errors")
    print(f"    MEDIUM: Correct in first 2 OR (<=1 early error AND no early Nones)")
    print(f"    HARD:   Everything else")

    print(f"\n  {'Difficulty':<12} {'Count':>6} {'Correct%':>9} {'Avg Time':>9} {'Avg Errors':>11} {'Avg Answers':>12}")
    print(f"  {'─'*12} {'─'*6} {'─'*9} {'─'*9} {'─'*11} {'─'*12}")

    for diff in ['EASY', 'MEDIUM', 'HARD']:
        probs = diff_groups.get(diff, [])
        if not probs:
            continue
        n = len(probs)
        corr = sum(1 for p in probs if p['correct'])
        avg_time = sum(p['wall_time'] for p in probs) / n
        avg_err = sum(p['total_errors'] for p in probs) / n
        avg_ans = sum(p['unique_answers'] for p in probs) / n
        print(f"  {diff:<12} {n:>6} {100*corr/n:>8.0f}% {avg_time:>8.0f}s {avg_err:>10.1f} {avg_ans:>11.1f}")

    # ── 3. Time Savings from Error-Aware Early Stop ──
    print(f"\n{'─' * 70}")
    print("3. TIME SAVINGS — Error-Aware Early Stop Simulation")
    print(f"{'─' * 70}")

    print(f"\n  Simulating: 'If EASY, stop after 3 attempts. If MEDIUM, 5. If HARD, 8.'")
    print(f"  vs current: All problems get 8 attempts.\n")

    # For each problem, simulate reduced attempts
    current_total_time = sum(p['wall_time'] for p in problem_signals)
    adaptive_limits = {'EASY': 3, 'MEDIUM': 5, 'HARD': 8}

    # Simulate score with reduced attempts
    adaptive_correct = 0
    adaptive_time = 0.0
    problems_by_id = {p.problem_id: p for p in problems}

    for ps in problem_signals:
        prob = problems_by_id[ps['pid']]
        limit = adaptive_limits[ps['difficulty']]
        limited_atts = [a for a in prob.attempts if a.attempt_num <= limit]

        # Recompute vote with limited attempts
        vote_counts = Counter()
        for a in limited_atts:
            if a.answer is not None:
                vote_counts[a.answer] += 1

        predicted = vote_counts.most_common(1)[0][0] if vote_counts else None
        correct = (predicted == prob.expected) if predicted is not None and prob.expected is not None else False
        if correct:
            adaptive_correct += 1

        # Estimate time: proportional to attempts used
        if prob.attempts:
            time_per_att = prob.wall_time / len(prob.attempts)
            adaptive_time += time_per_att * len(limited_atts)

    full_correct = sum(1 for p in problem_signals if p['correct'])

    print(f"  {'Metric':<30} {'Current (8 att)':>16} {'Adaptive':>16} {'Delta':>12}")
    print(f"  {'─'*30} {'─'*16} {'─'*16} {'─'*12}")
    print(f"  {'Score':<30} {full_correct:>16} {adaptive_correct:>16} {adaptive_correct-full_correct:>+12}")
    print(f"  {'Total time (min)':<30} {current_total_time/60:>15.0f}m {adaptive_time/60:>15.0f}m {(adaptive_time-current_total_time)/60:>+11.0f}m")
    print(f"  {'Time saved (min)':<30} {'':>16} {(current_total_time-adaptive_time)/60:>15.0f}m {'':>12}")

    saved_attempts = sum(
        len(problems_by_id[ps['pid']].attempts) - adaptive_limits[ps['difficulty']]
        for ps in problem_signals
        if len(problems_by_id[ps['pid']].attempts) > adaptive_limits[ps['difficulty']]
    )
    print(f"  {'Attempts saved':<30} {'':>16} {saved_attempts:>16} {'':>12}")

    if current_total_time - adaptive_time > 0:
        avg_clean_time = sum(
            a.time_s for p in problems for a in p.attempts if a.errors == 0
        ) / max(1, sum(1 for p in problems for a in p.attempts if a.errors == 0))
        extra_attempts = int((current_total_time - adaptive_time) / avg_clean_time)
        print(f"\n  Time saved could fund ~{extra_attempts} additional clean attempts")
        print(f"  (at {avg_clean_time:.0f}s avg per clean attempt)")

    # ── 4. None Prediction from Error Patterns ──
    print(f"\n{'─' * 70}")
    print("4. NONE PREDICTION — Can errors predict None outcomes?")
    print(f"{'─' * 70}")

    # For each attempt, correlate error features with None outcome
    att_features = []
    for prob in problems:
        for att in prob.attempts:
            errors, timeouts, is_none = compute_attempt_error_signature(att)
            att_features.append({
                'errors': errors,
                'timeouts': timeouts,
                'is_none': is_none,
                'turns': len(att.turns),
                'answer': att.answer,
            })

    # Error count vs None rate
    err_vs_none = defaultdict(lambda: {'total': 0, 'nones': 0})
    for af in att_features:
        bucket = min(af['errors'], 5)  # Cap at 5+
        err_vs_none[bucket]['total'] += 1
        if af['is_none']:
            err_vs_none[bucket]['nones'] += 1

    print(f"\n  {'Errors in Attempt':>18} {'Attempts':>9} {'None Rate':>10} {'Predictive?':}")
    print(f"  {'─'*18} {'─'*9} {'─'*10} {'─'*30}")

    baseline_none_rate = sum(1 for af in att_features if af['is_none']) / len(att_features) if att_features else 0

    for ec in sorted(err_vs_none):
        d = err_vs_none[ec]
        rate = d['nones'] / d['total'] if d['total'] else 0
        label = f"{ec}" if ec < 5 else "5+"
        signal = ""
        if rate > baseline_none_rate * 2:
            signal = "<-- STRONG None predictor"
        elif rate > baseline_none_rate * 1.3:
            signal = "<-- moderate signal"
        elif rate < baseline_none_rate * 0.5:
            signal = "<-- LOW None risk"
        print(f"  {label:>18} {d['total']:>9} {100*rate:>9.1f}% {signal}")

    print(f"\n  Baseline None rate: {100*baseline_none_rate:.1f}%")

    # Timeout specifically vs None
    timeout_atts = [af for af in att_features if af['timeouts'] > 0]
    no_timeout_atts = [af for af in att_features if af['timeouts'] == 0]
    if timeout_atts and no_timeout_atts:
        to_none = sum(1 for af in timeout_atts if af['is_none']) / len(timeout_atts)
        no_to_none = sum(1 for af in no_timeout_atts if af['is_none']) / len(no_timeout_atts)
        print(f"\n  Timeout impact on None rate:")
        print(f"    With timeouts:    {100*to_none:.0f}% None rate ({len(timeout_atts)} attempts)")
        print(f"    Without timeouts: {100*no_to_none:.0f}% None rate ({len(no_timeout_atts)} attempts)")

    # ── 5. Per-Attempt Error Budget ──
    print(f"\n{'─' * 70}")
    print("5. ERROR BUDGET — When should we abort an attempt?")
    print(f"{'─' * 70}")

    # After N errors in an attempt, what's the probability of getting a correct answer?
    print(f"\n  Cumulative errors within attempt vs final outcome:")
    print(f"  'After seeing N errors, what are the chances this attempt produces a correct answer?'\n")

    err_threshold_stats = {}
    for prob in problems:
        for att in prob.attempts:
            err_count = sum(1 for t in att.turns if t.is_error)
            is_correct = (att.answer is not None and prob.expected is not None
                         and att.answer == prob.expected)
            for threshold in range(0, 6):
                if err_count >= threshold:
                    if threshold not in err_threshold_stats:
                        err_threshold_stats[threshold] = {'total': 0, 'correct': 0, 'time': 0}
                    err_threshold_stats[threshold]['total'] += 1
                    if is_correct:
                        err_threshold_stats[threshold]['correct'] += 1
                    err_threshold_stats[threshold]['time'] += att.time_s

    print(f"  {'Errors >= N':>12} {'Attempts':>9} {'Correct%':>9} {'Avg Time':>9} {'Recommendation':}")
    print(f"  {'─'*12} {'─'*9} {'─'*9} {'─'*9} {'─'*30}")

    for threshold in sorted(err_threshold_stats):
        d = err_threshold_stats[threshold]
        corr_rate = 100 * d['correct'] / d['total'] if d['total'] else 0
        avg_time = d['time'] / d['total'] if d['total'] else 0
        rec = ""
        if corr_rate < 15:
            rec = "<-- ABORT: low ROI"
        elif corr_rate < 30:
            rec = "<-- consider aborting"
        else:
            rec = "keep going"
        print(f"  {'>= ' + str(threshold):>12} {d['total']:>9} {corr_rate:>8.1f}% {avg_time:>8.0f}s {rec}")

    # ── 6. Problem-Level: Would early abort hurt? ──
    print(f"\n{'─' * 70}")
    print("6. PROBLEM-LEVEL IMPACT — Would aborting error-heavy attempts hurt score?")
    print(f"{'─' * 70}")

    # Simulate: abort any attempt that hits 3+ errors. Re-vote.
    abort_threshold = 3
    original_score = sum(1 for p in problems if p.correct)
    abort_score = 0
    abort_time_saved = 0
    problems_changed = []

    for prob in problems:
        kept = [a for a in prob.attempts
                if sum(1 for t in a.turns if t.is_error) < abort_threshold]
        aborted = [a for a in prob.attempts
                   if sum(1 for t in a.turns if t.is_error) >= abort_threshold]

        # Re-vote with kept attempts only
        vote_counts = Counter()
        for a in kept:
            if a.answer is not None:
                vote_counts[a.answer] += 1

        predicted = vote_counts.most_common(1)[0][0] if vote_counts else None
        correct = (predicted == prob.expected) if predicted is not None and prob.expected is not None else False
        if correct:
            abort_score += 1

        abort_time_saved += sum(a.time_s for a in aborted)

        if correct != prob.correct:
            problems_changed.append((prob.problem_id, prob.correct, correct,
                                    len(kept), len(aborted)))

    print(f"\n  Simulation: Abort attempts with {abort_threshold}+ errors, re-vote with remaining.\n")
    print(f"  Original score:      {original_score}/{len(problems)}")
    print(f"  Score after aborts:  {abort_score}/{len(problems)}")
    print(f"  Time saved:          {abort_time_saved:.0f}s ({abort_time_saved/60:.1f}m)")
    print(f"  Attempts aborted:    {sum(1 for p in problems for a in p.attempts if sum(1 for t in a.turns if t.is_error) >= abort_threshold)}")

    if problems_changed:
        print(f"\n  Problems where score changed:")
        print(f"  {'Problem':<12} {'Was':>8} {'Now':>8} {'Kept':>6} {'Aborted':>8}")
        print(f"  {'─'*12} {'─'*8} {'─'*8} {'─'*6} {'─'*8}")
        for pid, was, now, kept, aborted in problems_changed:
            print(f"  {pid:<12} {'OK' if was else 'WRONG':>8} {'OK' if now else 'WRONG':>8} {kept:>6} {aborted:>8}")
    else:
        print(f"\n  No problems changed — aborting error-heavy attempts is SAFE.")

    # ── 7. Optimal Adaptive Strategy Summary ──
    print(f"\n{'─' * 70}")
    print("7. RECOMMENDED ADAPTIVE STRATEGY (from error analysis)")
    print(f"{'─' * 70}")

    # Compute some key stats for recommendations
    easy_count = len(diff_groups.get('EASY', []))
    med_count = len(diff_groups.get('MEDIUM', []))
    hard_count = len(diff_groups.get('HARD', []))

    print(f"""
  CLASSIFICATION (after 2 attempts):
    EASY   ({easy_count} problems): Correct in first 2, no errors
    MEDIUM ({med_count} problems): Correct in first 2 OR low-error
    HARD   ({hard_count} problems): No early correct, multiple errors/nones

  ATTEMPT ALLOCATION:
    EASY:   3 attempts max (early stop at 2 consensus)
    MEDIUM: 5 attempts max
    HARD:   8 attempts max (full budget)

  ERROR-BASED RULES:
    - Abort any attempt after 3+ code errors (saves time, doesn't hurt score)
    - If attempt has timeout, flag problem as potentially HARD
    - If first 2 attempts both None: escalate to HARD immediately

  PROJECTED SAVINGS:
    Score:  {adaptive_correct}/{len(problems)} (vs {full_correct}/{len(problems)} current)
    Time:   {adaptive_time/60:.0f}m (vs {current_total_time/60:.0f}m current)
    Saved:  {(current_total_time-adaptive_time)/60:.0f}m = {100*(current_total_time-adaptive_time)/current_total_time:.0f}% reduction""")

    if current_total_time > adaptive_time:
        print(f"    Extra budget per hard problem: {(current_total_time-adaptive_time)/max(1,hard_count)/60:.1f}m")

    # ── 8. Per-problem recommendations ──
    print(f"\n{'─' * 70}")
    print("8. PER-PROBLEM CLASSIFICATION")
    print(f"{'─' * 70}")

    print(f"\n  {'Problem':<10} {'Diff':<8} {'EarlyErr':>9} {'EarlyCorr':>10} {'TotErr':>7} {'Time':>7} {'Correct':>8} {'Rec Atts':>9}")
    print(f"  {'─'*10} {'─'*8} {'─'*9} {'─'*10} {'─'*7} {'─'*7} {'─'*8} {'─'*9}")

    for ps in sorted(problem_signals, key=lambda x: ('EASY', 'MEDIUM', 'HARD').index(x['difficulty'])):
        corr_str = 'Yes' if ps['correct'] else 'No'
        rec_att = adaptive_limits[ps['difficulty']]
        print(f"  {ps['pid']:<10} {ps['difficulty']:<8} {ps['early_errors']:>9} {ps['early_correct']:>10} {ps['total_errors']:>7} {ps['wall_time']:>6.0f}s {corr_str:>8} {rec_att:>9}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 log_exploration/error_adaptive.py <diagnostic.log>")
        sys.exit(1)

    problems = parse_log(sys.argv[1])
    analyze_error_adaptive(problems)


if __name__ == '__main__':
    main()
