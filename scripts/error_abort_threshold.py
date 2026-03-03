#!/usr/bin/env python3
"""
Error Abort Threshold Simulation
==================================
DATA-DRIVEN analysis: for each threshold T, simulate aborting attempts
with too many errors (both CONSECUTIVE and TOTAL), re-run voting,
and report exact score impact.

For each threshold T in [1, 2, 3, 4, 5, 6, 7, 8, 10, 15, 999]:
  - For each problem, for each attempt:
    - CONSECUTIVE mode: count max consecutive errors in a row within turns.
      If consecutive errors >= T, that attempt is "aborted" (answer -> None)
    - TOTAL mode: count total error turns in the attempt.
      If total errors >= T, that attempt is "aborted" (answer -> None)
  - Re-run majority voting with modified attempt results
  - Report: score, problems lost, problems gained, time saved

Usage: python3 scripts/error_abort_threshold.py
"""

import sys
import os
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "output", "v23", "diagnostic.log")

THRESHOLDS = [1, 2, 3, 4, 5, 6, 7, 8, 10, 15, 999]


def max_consecutive_errors(attempt):
    """Count the maximum run of consecutive error turns in an attempt."""
    max_run = 0
    current_run = 0
    for turn in attempt.turns:
        if turn.is_error:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 0
    return max_run


def total_errors(attempt):
    """Count total error turns in an attempt."""
    return sum(1 for t in attempt.turns if t.is_error)


def should_abort(attempt, threshold, mode):
    """Check if an attempt should be aborted given threshold and mode."""
    if mode == "consecutive":
        return max_consecutive_errors(attempt) >= threshold
    elif mode == "total":
        return total_errors(attempt) >= threshold
    else:
        raise ValueError(f"Unknown mode: {mode}")


def vote_entropy_weighted(attempts):
    """Entropy-weighted majority vote matching the actual solver logic.

    Each vote is weighted by 1/(1+entropy). On ties, the answer with the
    highest total entropy-weighted score wins. This matches the baseline notebook.
    """
    vote_counts = Counter()
    weighted_scores = defaultdict(float)
    for a in attempts:
        if a.answer is not None:
            vote_counts[a.answer] += 1
            weight = 1.0 / (1.0 + a.entropy)
            weighted_scores[a.answer] += weight
    if not vote_counts:
        return None
    # Primary: highest vote count. Tiebreak: highest entropy-weighted score.
    max_votes = max(vote_counts.values())
    candidates = [ans for ans, cnt in vote_counts.items() if cnt == max_votes]
    if len(candidates) == 1:
        return candidates[0]
    # Tiebreak by entropy-weighted score (higher = more confident)
    return max(candidates, key=lambda a: weighted_scores[a])


def simulate_threshold(problems, threshold, mode):
    """Simulate a given error abort threshold. Returns detailed results."""
    results = {
        'threshold': threshold,
        'mode': mode,
        'score': 0,
        'total_problems': 0,
        'problems_detail': [],
        'total_aborted_attempts': 0,
        'total_attempts': 0,
        'time_saved': 0.0,
        'total_time': 0.0,
    }

    for prob in problems:
        if prob.expected is None:
            continue

        results['total_problems'] += 1
        results['total_attempts'] += len(prob.attempts)
        results['total_time'] += prob.wall_time

        # Classify each attempt
        kept_attempts = []
        aborted_attempts = []
        for att in prob.attempts:
            if should_abort(att, threshold, mode):
                aborted_attempts.append(att)
            else:
                kept_attempts.append(att)

        results['total_aborted_attempts'] += len(aborted_attempts)
        results['time_saved'] += sum(a.time_s for a in aborted_attempts)

        # Re-vote with kept attempts
        new_predicted = vote_entropy_weighted(kept_attempts)
        new_correct = (new_predicted == prob.expected) if new_predicted is not None else False

        if new_correct:
            results['score'] += 1

        results['problems_detail'].append({
            'pid': prob.problem_id,
            'expected': prob.expected,
            'original_predicted': prob.predicted,
            'original_correct': prob.correct,
            'new_predicted': new_predicted,
            'new_correct': new_correct,
            'kept': len(kept_attempts),
            'aborted': len(aborted_attempts),
            'total': len(prob.attempts),
            'original_votes': dict(prob.votes) if prob.votes else {},
            'aborted_time': sum(a.time_s for a in aborted_attempts),
            # For deeper analysis: what answers were aborted vs kept
            'kept_answers': [a.answer for a in kept_attempts],
            'aborted_answers': [a.answer for a in aborted_attempts],
        })

    return results


def print_header(title):
    print()
    print("=" * 100)
    print(f"  {title}")
    print("=" * 100)


def print_section(title):
    print()
    print("-" * 80)
    print(f"  {title}")
    print("-" * 80)


def run_analysis(problems, mode):
    """Run full analysis for a given mode (consecutive or total)."""
    mode_label = "CONSECUTIVE" if mode == "consecutive" else "TOTAL"
    print_header(f"ERROR ABORT THRESHOLD ANALYSIS — {mode_label} ERRORS")
    print(f"\n  Mode: Abort attempt if {mode_label.lower()} errors >= threshold")
    print(f"  Aborted attempts have their answer set to None (removed from voting)")

    # Get baseline (no abort = threshold 999)
    baseline = simulate_threshold(problems, 999, mode)
    baseline_score = baseline['score']

    # Run all thresholds
    all_results = {}
    for t in THRESHOLDS:
        all_results[t] = simulate_threshold(problems, t, mode)

    # ── Summary table ──
    print_section(f"SUMMARY TABLE — {mode_label} Error Abort Thresholds")
    print(f"\n  Baseline score (no abort): {baseline_score}/{baseline['total_problems']}")
    print()
    print(f"  {'Threshold':>10} {'Score':>8} {'Delta':>7} {'Aborted':>9} {'%Aborted':>9} {'Time Saved':>12} {'Lost':>6} {'Gained':>8}")
    print(f"  {'─'*10} {'─'*8} {'─'*7} {'─'*9} {'─'*9} {'─'*12} {'─'*6} {'─'*8}")

    for t in THRESHOLDS:
        r = all_results[t]
        delta = r['score'] - baseline_score
        pct_aborted = 100 * r['total_aborted_attempts'] / r['total_attempts'] if r['total_attempts'] else 0
        lost = sum(1 for d in r['problems_detail'] if d['original_correct'] and not d['new_correct'])
        gained = sum(1 for d in r['problems_detail'] if not d['original_correct'] and d['new_correct'])
        time_str = f"{r['time_saved']:.0f}s ({r['time_saved']/60:.1f}m)"

        label = f">={t}" if t < 999 else "none"
        delta_str = f"{delta:+d}" if delta != 0 else "0"
        print(f"  {label:>10} {r['score']:>5}/{r['total_problems']} {delta_str:>7} {r['total_aborted_attempts']:>9} {pct_aborted:>8.1f}% {time_str:>12} {lost:>6} {gained:>8}")

    # ── Detailed problem-level diffs for each threshold ──
    print_section(f"PROBLEM-LEVEL FLIPS — {mode_label} Mode")
    print(f"\n  Which specific problems change at each threshold?\n")

    for t in THRESHOLDS:
        r = all_results[t]
        flipped = [d for d in r['problems_detail']
                   if d['original_correct'] != d['new_correct']]
        if not flipped:
            continue

        label = f">={t}" if t < 999 else "none"
        print(f"  --- Threshold {label} ---")
        for d in flipped:
            direction = "LOST" if d['original_correct'] and not d['new_correct'] else "GAINED"
            print(f"    [{direction}] Problem {d['pid']}: "
                  f"original={d['original_predicted']} new={d['new_predicted']} expected={d['expected']} "
                  f"kept={d['kept']}/{d['total']} "
                  f"kept_answers={_summarize_answers(d['kept_answers'])} "
                  f"aborted_answers={_summarize_answers(d['aborted_answers'])}")
        print()

    # ── Per-problem error profile ──
    print_section(f"PER-PROBLEM ERROR PROFILE — {mode_label} Mode")
    print(f"\n  For each problem: how many attempts would be aborted at each threshold?\n")

    # Build per-problem error counts
    prob_error_profiles = []
    for prob in problems:
        if prob.expected is None:
            continue
        if mode == "consecutive":
            error_vals = [max_consecutive_errors(a) for a in prob.attempts]
        else:
            error_vals = [total_errors(a) for a in prob.attempts]

        profile = {
            'pid': prob.problem_id,
            'correct': prob.correct,
            'expected': prob.expected,
            'predicted': prob.predicted,
            'num_attempts': len(prob.attempts),
            'error_vals': error_vals,
            'max_error': max(error_vals) if error_vals else 0,
            'mean_error': sum(error_vals) / len(error_vals) if error_vals else 0,
        }
        # How many aborted at each threshold
        for t in THRESHOLDS:
            profile[f'aborted_{t}'] = sum(1 for v in error_vals if v >= t)
        prob_error_profiles.append(profile)

    # Sort: problems with most errors first
    prob_error_profiles.sort(key=lambda x: -x['max_error'])

    err_label = "MaxConsec" if mode == "consecutive" else "MaxTotal"
    print(f"  {'Problem':<10} {'OK':>3} {'Atts':>5} {err_label:>10} {'MeanErr':>8}", end="")
    for t in [1, 2, 3, 4, 5, 6, 8, 10, 15]:
        print(f" {'T>=' + str(t):>6}", end="")
    print(f"  {'Error distribution'}")

    print(f"  {'─'*10} {'─'*3} {'─'*5} {'─'*10} {'─'*8}", end="")
    for _ in [1, 2, 3, 4, 5, 6, 8, 10, 15]:
        print(f" {'─'*6}", end="")
    print(f"  {'─'*30}")

    for p in prob_error_profiles[:40]:  # Show top 40
        ok = "Y" if p['correct'] else "N"
        print(f"  {p['pid']:<10} {ok:>3} {p['num_attempts']:>5} {p['max_error']:>10} {p['mean_error']:>8.1f}", end="")
        for t in [1, 2, 3, 4, 5, 6, 8, 10, 15]:
            aborted = p[f'aborted_{t}']
            if aborted == 0:
                print(f" {'·':>6}", end="")
            else:
                print(f" {aborted:>6}", end="")
        dist = sorted(p['error_vals'], reverse=True)
        print(f"  {dist}")

    # ── Attempt-level detail for aborted attempts ──
    print_section(f"ATTEMPT DETAIL — What gets aborted at T=3? ({mode_label})")
    print(f"\n  Every attempt that would be aborted with threshold >= 3:\n")

    abort_details = []
    for prob in problems:
        if prob.expected is None:
            continue
        for att in prob.attempts:
            if mode == "consecutive":
                err_val = max_consecutive_errors(att)
            else:
                err_val = total_errors(att)
            if err_val >= 3:
                abort_details.append({
                    'pid': prob.problem_id,
                    'attempt': att.attempt_num,
                    'answer': att.answer,
                    'expected': prob.expected,
                    'is_correct_answer': att.answer == prob.expected if att.answer is not None else False,
                    'error_val': err_val,
                    'total_turns': len(att.turns),
                    'error_turns': sum(1 for t in att.turns if t.is_error),
                    'time_s': att.time_s,
                    'is_none': att.is_none,
                })

    if abort_details:
        print(f"  {'Problem':<10} {'Att#':>5} {'Answer':>8} {'Expected':>9} {'Correct?':>9} "
              f"{'ErrVal':>7} {'ErrTurns':>9} {'TotTurns':>9} {'Time':>7} {'None?':>6}")
        print(f"  {'─'*10} {'─'*5} {'─'*8} {'─'*9} {'─'*9} "
              f"{'─'*7} {'─'*9} {'─'*9} {'─'*7} {'─'*6}")
        for d in sorted(abort_details, key=lambda x: (-x['error_val'], x['pid'], x['attempt'])):
            corr = "YES" if d['is_correct_answer'] else ("None" if d['answer'] is None else "no")
            print(f"  {d['pid']:<10} {d['attempt']:>5} {str(d['answer']):>8} {d['expected']:>9} {corr:>9} "
                  f"{d['error_val']:>7} {d['error_turns']:>9} {d['total_turns']:>9} {d['time_s']:>6.0f}s "
                  f"{'Y' if d['is_none'] else 'N':>6}")

        # Key stat: how many aborted attempts actually had the correct answer?
        correct_aborted = sum(1 for d in abort_details if d['is_correct_answer'])
        none_aborted = sum(1 for d in abort_details if d['is_none'])
        wrong_aborted = len(abort_details) - correct_aborted - none_aborted
        total_time = sum(d['time_s'] for d in abort_details)

        print(f"\n  Summary of aborted attempts (T>=3, {mode_label}):")
        print(f"    Total aborted:        {len(abort_details)}")
        print(f"    Had CORRECT answer:   {correct_aborted} ({100*correct_aborted/len(abort_details):.1f}%) <-- these are dangerous to abort")
        print(f"    Had WRONG answer:     {wrong_aborted} ({100*wrong_aborted/len(abort_details):.1f}%)")
        print(f"    Had NONE:             {none_aborted} ({100*none_aborted/len(abort_details):.1f}%)")
        print(f"    Total time in aborted: {total_time:.0f}s ({total_time/60:.1f}m)")
    else:
        print("  No attempts would be aborted at T=3.")

    return all_results


def _summarize_answers(answers):
    """Compact answer summary."""
    counts = Counter(answers)
    parts = []
    for ans, cnt in counts.most_common(5):
        if ans is None:
            parts.append(f"None:{cnt}")
        else:
            parts.append(f"{ans}:{cnt}")
    return "{" + ", ".join(parts) + "}"


def compare_modes(consec_results, total_results, problems):
    """Compare consecutive vs total error modes."""
    print_header("CONSECUTIVE vs TOTAL — Side-by-Side Comparison")

    baseline_score = consec_results[999]['score']  # Same for both
    total_problems = consec_results[999]['total_problems']

    print(f"\n  Baseline: {baseline_score}/{total_problems}")
    print()
    print(f"  {'Thresh':>7} │ {'CONSECUTIVE':^35} │ {'TOTAL':^35} │ {'Better?':>8}")
    print(f"  {'':>7} │ {'Score':>8} {'Delta':>6} {'Abort':>7} {'Save':>12} │ {'Score':>8} {'Delta':>6} {'Abort':>7} {'Save':>12} │ {'':>8}")
    print(f"  {'─'*7} │ {'─'*8} {'─'*6} {'─'*7} {'─'*12} │ {'─'*8} {'─'*6} {'─'*7} {'─'*12} │ {'─'*8}")

    for t in THRESHOLDS:
        if t == 999:
            continue
        cr = consec_results[t]
        tr = total_results[t]
        cd = cr['score'] - baseline_score
        td = tr['score'] - baseline_score
        c_save = f"{cr['time_saved']/60:.1f}m"
        t_save = f"{tr['time_saved']/60:.1f}m"

        if cd > td:
            better = "CONSEC"
        elif td > cd:
            better = "TOTAL"
        elif cr['time_saved'] > tr['time_saved']:
            better = "CONSEC"
        elif tr['time_saved'] > cr['time_saved']:
            better = "TOTAL"
        else:
            better = "TIE"

        label = f">={t}"
        print(f"  {label:>7} │ {cr['score']:>5}/{total_problems} {cd:>+5} {cr['total_aborted_attempts']:>7} {c_save:>12} │ "
              f"{tr['score']:>5}/{total_problems} {td:>+5} {tr['total_aborted_attempts']:>7} {t_save:>12} │ {better:>8}")

    # Which problems differ between modes at T=3?
    print_section("WHERE MODES DISAGREE — Threshold >= 3")
    cr3 = consec_results[3]
    tr3 = total_results[3]

    for cd, td in zip(cr3['problems_detail'], tr3['problems_detail']):
        if cd['new_correct'] != td['new_correct']:
            print(f"  Problem {cd['pid']}: "
                  f"CONSEC={'OK' if cd['new_correct'] else 'WRONG'} "
                  f"TOTAL={'OK' if td['new_correct'] else 'WRONG'} "
                  f"expected={cd['expected']} "
                  f"consec_kept={cd['kept']}/{cd['total']} "
                  f"total_kept={td['kept']}/{td['total']}")


def analyze_error_turn_patterns(problems):
    """Deep dive: what do error sequences look like within attempts?"""
    print_header("ERROR TURN SEQUENCES — What patterns exist?")
    print(f"\n  Showing the error/success sequence for each attempt that has errors.\n")
    print(f"  Legend: '.' = clean turn, 'E' = error turn, final char: answer status")
    print(f"  Answer: C=correct, W=wrong, N=none\n")

    patterns = Counter()
    pattern_outcomes = defaultdict(lambda: {'correct': 0, 'wrong': 0, 'none': 0, 'time': 0, 'count': 0})

    for prob in problems:
        if prob.expected is None:
            continue
        for att in prob.attempts:
            if not att.turns:
                continue

            seq = ""
            for t in att.turns:
                seq += "E" if t.is_error else "."

            # Simplify pattern: just the error positions
            error_count = seq.count("E")
            if error_count == 0:
                continue

            # Compute consecutive runs
            runs = []
            current_char = seq[0]
            current_len = 1
            for c in seq[1:]:
                if c == current_char:
                    current_len += 1
                else:
                    runs.append((current_char, current_len))
                    current_char = c
                    current_len = 1
            runs.append((current_char, current_len))

            error_runs = [length for char, length in runs if char == 'E']
            max_consec = max(error_runs) if error_runs else 0

            # Pattern key: (total_errors, max_consecutive)
            pattern_key = (error_count, max_consec)
            patterns[pattern_key] += 1

            outcome = 'correct' if (att.answer is not None and att.answer == prob.expected) else (
                'none' if att.is_none else 'wrong')
            pattern_outcomes[pattern_key][outcome] += 1
            pattern_outcomes[pattern_key]['time'] += att.time_s
            pattern_outcomes[pattern_key]['count'] += 1

    # Print pattern analysis
    print(f"  {'TotalErr':>9} {'MaxConsec':>10} {'Count':>6} {'Correct%':>9} {'Wrong%':>8} {'None%':>7} {'AvgTime':>8}")
    print(f"  {'─'*9} {'─'*10} {'─'*6} {'─'*9} {'─'*8} {'─'*7} {'─'*8}")

    for (tot, consec) in sorted(pattern_outcomes.keys()):
        d = pattern_outcomes[(tot, consec)]
        n = d['count']
        c_pct = 100 * d['correct'] / n
        w_pct = 100 * d['wrong'] / n
        n_pct = 100 * d['none'] / n
        avg_t = d['time'] / n
        print(f"  {tot:>9} {consec:>10} {n:>6} {c_pct:>8.1f}% {w_pct:>7.1f}% {n_pct:>6.1f}% {avg_t:>7.0f}s")

    # Key insight: at what (total, consecutive) pair does correct rate drop to near zero?
    print(f"\n  KEY INSIGHT: When does correct answer probability drop to near zero?")
    for (tot, consec) in sorted(pattern_outcomes.keys()):
        d = pattern_outcomes[(tot, consec)]
        n = d['count']
        if n >= 3:  # Need enough data
            c_pct = 100 * d['correct'] / n
            if c_pct < 10:
                print(f"    total={tot}, max_consec={consec}: {c_pct:.0f}% correct ({n} attempts)")


def main():
    print(f"Loading log from: {LOG_PATH}")
    if not os.path.exists(LOG_PATH):
        print(f"ERROR: Log file not found: {LOG_PATH}")
        sys.exit(1)

    problems = parse_log(LOG_PATH)
    problems_with_expected = [p for p in problems if p.expected is not None]
    print(f"Parsed {len(problems)} problems, {len(problems_with_expected)} with expected answers.")
    print(f"Total attempts: {sum(len(p.attempts) for p in problems_with_expected)}")

    # Quick baseline stats
    baseline_score = sum(1 for p in problems_with_expected if p.correct)
    total_attempts = sum(len(p.attempts) for p in problems_with_expected)
    total_error_attempts = sum(
        1 for p in problems_with_expected
        for a in p.attempts
        if sum(1 for t in a.turns if t.is_error) > 0
    )
    print(f"Baseline score: {baseline_score}/{len(problems_with_expected)}")
    print(f"Attempts with at least 1 error: {total_error_attempts}/{total_attempts} ({100*total_error_attempts/total_attempts:.1f}%)")

    # Run both modes
    consec_results = run_analysis(problems_with_expected, "consecutive")
    total_results = run_analysis(problems_with_expected, "total")

    # Compare
    compare_modes(consec_results, total_results, problems_with_expected)

    # Error pattern analysis
    analyze_error_turn_patterns(problems_with_expected)

    # Final recommendation
    print_header("FINAL RECOMMENDATION")

    # Find the sweet spot: max time saved with zero score loss
    best_consec = None
    best_total = None
    for t in THRESHOLDS:
        cr = consec_results[t]
        if cr['score'] >= baseline_score:
            if best_consec is None or cr['time_saved'] > consec_results[best_consec]['time_saved']:
                best_consec = t
        tr = total_results[t]
        if tr['score'] >= baseline_score:
            if best_total is None or tr['time_saved'] > total_results[best_total]['time_saved']:
                best_total = t

    print(f"\n  ZERO SCORE LOSS — Maximum time savings:")
    if best_consec:
        cr = consec_results[best_consec]
        print(f"    CONSECUTIVE >= {best_consec}: saves {cr['time_saved']/60:.1f}m, aborts {cr['total_aborted_attempts']} attempts, score stays {cr['score']}/{cr['total_problems']}")
    else:
        print(f"    CONSECUTIVE: No safe threshold found (all thresholds lose score)")

    if best_total:
        tr = total_results[best_total]
        print(f"    TOTAL >= {best_total}: saves {tr['time_saved']/60:.1f}m, aborts {tr['total_aborted_attempts']} attempts, score stays {tr['score']}/{tr['total_problems']}")
    else:
        print(f"    TOTAL: No safe threshold found (all thresholds lose score)")

    # Find where score first drops
    print(f"\n  FIRST SCORE DROP:")
    for mode, results in [("CONSECUTIVE", consec_results), ("TOTAL", total_results)]:
        for t in sorted(THRESHOLDS):
            if t == 999:
                continue
            if results[t]['score'] < baseline_score:
                delta = results[t]['score'] - baseline_score
                lost = [d for d in results[t]['problems_detail'] if d['original_correct'] and not d['new_correct']]
                print(f"    {mode} >= {t}: first score loss ({delta:+d})")
                for d in lost:
                    print(f"      Problem {d['pid']}: expected={d['expected']}, "
                          f"original_votes={d['original_votes']}, "
                          f"kept_answers={_summarize_answers(d['kept_answers'])}")
                break

    # Overall recommendation
    print(f"\n  BOTTOM LINE:")
    if best_consec and best_total:
        if consec_results[best_consec]['time_saved'] >= total_results[best_total]['time_saved']:
            winner = f"CONSECUTIVE >= {best_consec}"
            save = consec_results[best_consec]['time_saved']
        else:
            winner = f"TOTAL >= {best_total}"
            save = total_results[best_total]['time_saved']
        print(f"    Use {winner}")
        print(f"    Saves {save/60:.1f} minutes with ZERO score loss")
        print(f"    This is free compute budget that can be reallocated to more attempts on hard problems")
    else:
        print(f"    ERROR: Could not find a safe threshold. Every threshold loses score.")
        print(f"    This means error-heavy attempts sometimes contribute correct answers.")


if __name__ == "__main__":
    main()
