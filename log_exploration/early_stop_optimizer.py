#!/usr/bin/env python3
"""
AIMO3 Early Stop & Attempt Count Optimizer
============================================
Comprehensive analysis of early_stop thresholds and total attempt counts.
Answers 5 specific questions:

1. ES simulation (ES=2..5): score, avg attempts used, total time estimate
2. False positive rate of early stop (ES triggers on wrong answer)
3. Vote stabilization: after attempt N, adding more doesn't change winner
4. Optimal (attempts, ES) grid search under 300-min budget
5. v22 vs v23 head-to-head on common problems

Usage:
    python3 log_exploration/early_stop_optimizer.py output/v23/diagnostic.log
    python3 log_exploration/early_stop_optimizer.py output/v23/diagnostic.log --v22 output/v22/diagnostic.log
    python3 log_exploration/early_stop_optimizer.py output/v23/diagnostic.log --save output/v23/early_stop_optimization.md
"""

import sys
import os
import argparse
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


# ─── Helpers ──────────────────────────────────────────────────────────────────

def majority_vote(answers):
    """Return (winner, count) from a list of answers, or (None, 0)."""
    if not answers:
        return None, 0
    c = Counter(answers)
    winner, count = c.most_common(1)[0]
    return winner, count


def simulate_es(problems, es_threshold, max_attempts=None):
    """
    Simulate early stop with a given threshold.
    Time is max(time_s) of used attempts (parallel execution model).
    Returns per-problem results: list of dicts with
      pid, predicted, expected, correct, attempts_used, time_s, es_triggered, answers_at_stop
    """
    results = []
    for p in problems:
        answers = []
        attempts_used = 0
        max_time = 0.0
        es_triggered = False

        limit = max_attempts if max_attempts else len(p.attempts)
        for a in p.attempts[:limit]:
            attempts_used += 1
            max_time = max(max_time, a.time_s)
            if a.answer is not None:
                answers.append(a.answer)
                top_answer, top_count = majority_vote(answers)
                if top_count >= es_threshold:
                    es_triggered = True
                    break

        predicted, _ = majority_vote(answers)
        correct = predicted is not None and predicted == p.expected

        results.append({
            'pid': p.problem_id,
            'predicted': predicted,
            'expected': p.expected,
            'correct': correct,
            'attempts_used': attempts_used,
            'time_s': max_time,
            'es_triggered': es_triggered,
            'answers_at_stop': list(answers),
        })
    return results


def simulate_fixed_attempts(problems, n_attempts):
    """Simulate using exactly first N attempts with majority vote.
    Time is max(time_s) of used attempts (parallel execution model)."""
    results = []
    for p in problems:
        subset = p.attempts[:n_attempts]
        answers = [a.answer for a in subset if a.answer is not None]
        max_time = max((a.time_s for a in subset), default=0)
        predicted, _ = majority_vote(answers)
        correct = predicted is not None and predicted == p.expected

        results.append({
            'pid': p.problem_id,
            'predicted': predicted,
            'expected': p.expected,
            'correct': correct,
            'attempts_used': len(subset),
            'time_s': max_time,
            'answers': list(answers),
        })
    return results


def simulate_attempts_with_es(problems, n_attempts, es_threshold):
    """Simulate: use up to n_attempts, but early-stop at es_threshold."""
    return simulate_es(problems, es_threshold, max_attempts=n_attempts)


# ─── Question 1: ES Simulation ───────────────────────────────────────────────

def q1_es_simulation(problems, output_lines):
    """Simulate ES=2,3,4,5 across all problems."""
    output_lines.append("## Q1: Early Stop Threshold Simulation (v23)")
    output_lines.append("")
    output_lines.append("All 16 attempts available; ES stops counting when N consecutive same-answer votes reached.")
    output_lines.append("")
    output_lines.append("| ES | Score | Accuracy | Avg Att Used | Median Att | ES Triggered | Total Time (sum) | Avg Time/Prob |")
    output_lines.append("|---:|------:|---------:|-------------:|-----------:|-------------:|-----------------:|--------------:|")

    print(f"\n{'='*75}")
    print(f"  Q1: EARLY STOP THRESHOLD SIMULATION")
    print(f"{'='*75}")
    print(f"\n  {'ES':>3} {'Score':>8} {'Acc%':>7} {'AvgAtt':>7} {'MedAtt':>7} {'ES Trig':>8} {'TotalTime':>10} {'AvgT/P':>8}")
    print(f"  {'─'*3} {'─'*8} {'─'*7} {'─'*7} {'─'*7} {'─'*8} {'─'*10} {'─'*8}")

    for es in [2, 3, 4, 5]:
        results = simulate_es(problems, es)
        score = sum(1 for r in results if r['correct'])
        total = len(results)
        acc = 100 * score / total if total else 0
        atts_used = [r['attempts_used'] for r in results]
        avg_att = sum(atts_used) / len(atts_used)
        med_att = sorted(atts_used)[len(atts_used) // 2]
        es_count = sum(1 for r in results if r['es_triggered'])
        total_time = sum(r['time_s'] for r in results)
        avg_time = total_time / total if total else 0

        print(f"  {es:>3} {score:>5}/{total} {acc:>6.1f}% {avg_att:>7.1f} {med_att:>7} {es_count:>8} {total_time:>9.0f}s {avg_time:>7.1f}s")
        output_lines.append(f"| {es} | {score}/{total} | {acc:.1f}% | {avg_att:.1f} | {med_att} | {es_count}/{total} | {total_time:.0f}s ({total_time/60:.1f}m) | {avg_time:.1f}s |")

    # Also show "no ES" (threshold = total attempts)
    max_att = max(len(p.attempts) for p in problems)
    results_no_es = simulate_es(problems, max_att + 1)
    score_no = sum(1 for r in results_no_es if r['correct'])
    total_time_no = sum(r['time_s'] for r in results_no_es)
    avg_att_no = sum(r['attempts_used'] for r in results_no_es) / len(results_no_es)
    print(f"  {'None':>3} {score_no:>5}/{len(problems)} {100*score_no/len(problems):>6.1f}% {avg_att_no:>7.1f} {max_att:>7} {'0':>8} {total_time_no:>9.0f}s {total_time_no/len(problems):>7.1f}s")
    output_lines.append(f"| None | {score_no}/{len(problems)} | {100*score_no/len(problems):.1f}% | {avg_att_no:.1f} | {max_att} | 0/{len(problems)} | {total_time_no:.0f}s ({total_time_no/60:.1f}m) | {total_time_no/len(problems):.1f}s |")
    output_lines.append("")


# ─── Question 2: False Positive Rate ─────────────────────────────────────────

def q2_false_positive_rate(problems, output_lines):
    """
    False positive: ES triggers on WRONG answer, but correct answer exists later.
    For each ES threshold, count how many times:
    - ES triggered on wrong answer (false lock-in)
    - Among those, the correct answer appeared in later (unused) attempts
    """
    output_lines.append("## Q2: Early Stop False Positive Analysis")
    output_lines.append("")
    output_lines.append("A 'false positive' = ES triggers, locks in a WRONG answer, AND the correct answer")
    output_lines.append("appears in unused later attempts (i.e., ES prevented a correct vote from being counted).")
    output_lines.append("")

    print(f"\n{'='*75}")
    print(f"  Q2: EARLY STOP FALSE POSITIVE RATE")
    print(f"{'='*75}")

    for es in [2, 3, 4, 5]:
        results = simulate_es(problems, es)

        wrong_es = 0          # ES triggered but answer was wrong
        rescuable = 0          # correct answer existed in unused attempts
        correct_es = 0        # ES triggered and answer was correct
        es_total = 0          # ES triggered at all

        rescuable_problems = []

        for i, r in enumerate(results):
            p = problems[i]
            if not r['es_triggered']:
                continue
            es_total += 1

            if r['correct']:
                correct_es += 1
            else:
                wrong_es += 1
                # Check: did the correct answer appear in unused attempts?
                used_count = r['attempts_used']
                unused = p.attempts[used_count:]
                correct_in_unused = any(a.answer == p.expected for a in unused if a.answer is not None)
                if correct_in_unused:
                    rescuable += 1
                    rescuable_problems.append({
                        'pid': p.problem_id,
                        'es_answer': r['predicted'],
                        'expected': p.expected,
                        'attempts_used': used_count,
                        'total_attempts': len(p.attempts),
                        'correct_later_at': [a.attempt_num for a in unused if a.answer == p.expected],
                    })

        print(f"\n  ES={es}:")
        print(f"    ES triggered: {es_total}/{len(problems)} problems")
        print(f"    Correct lock-in: {correct_es} ({100*correct_es/max(es_total,1):.0f}%)")
        print(f"    Wrong lock-in: {wrong_es} ({100*wrong_es/max(es_total,1):.0f}%)")
        print(f"    Rescuable (correct later): {rescuable}/{wrong_es}")

        output_lines.append(f"### ES={es}")
        output_lines.append(f"- ES triggered on {es_total}/{len(problems)} problems")
        output_lines.append(f"- Correct lock-in: {correct_es} ({100*correct_es/max(es_total,1):.0f}%)")
        output_lines.append(f"- Wrong lock-in: {wrong_es}")
        output_lines.append(f"- **Rescuable false positives**: {rescuable} (correct answer existed in unused attempts)")

        if rescuable_problems:
            output_lines.append("")
            output_lines.append("| Problem | ES locked answer | Expected | Stopped at | Correct found at |")
            output_lines.append("|---------|:----------------:|:--------:|:----------:|:----------------:|")
            for rp in rescuable_problems:
                correct_at = ", ".join(str(a) for a in rp['correct_later_at'][:5])
                print(f"      {rp['pid']}: locked on {rp['es_answer']}, expected {rp['expected']}, "
                      f"stopped at att {rp['attempts_used']}/{rp['total_attempts']}, "
                      f"correct found at att {correct_at}")
                output_lines.append(f"| {rp['pid']} | {rp['es_answer']} | {rp['expected']} | {rp['attempts_used']}/{rp['total_attempts']} | {correct_at} |")
        output_lines.append("")


# ─── Question 3: Vote Stabilization ──────────────────────────────────────────

def q3_vote_stabilization(problems, output_lines):
    """
    For each problem, find the attempt N after which the majority-vote winner
    never changes again. This is the 'stabilization point'.
    """
    output_lines.append("## Q3: Vote Stabilization Analysis")
    output_lines.append("")
    output_lines.append("After attempt N, adding more attempts never changes the majority-vote winner.")
    output_lines.append("")

    print(f"\n{'='*75}")
    print(f"  Q3: VOTE STABILIZATION POINT")
    print(f"{'='*75}")

    stabilization_points = []
    problem_details = []

    for p in problems:
        # Compute majority vote winner after each attempt
        running_answers = []
        winners_by_attempt = []

        for a in p.attempts:
            if a.answer is not None:
                running_answers.append(a.answer)
            winner, _ = majority_vote(running_answers)
            winners_by_attempt.append(winner)

        # Find last attempt where winner changes
        if not winners_by_attempt:
            continue

        final_winner = winners_by_attempt[-1]
        stabilize_at = 1  # default: stable from the start

        for i in range(len(winners_by_attempt)):
            if winners_by_attempt[i] != final_winner:
                stabilize_at = i + 2  # next attempt stabilized it

        # Clamp to valid range
        stabilize_at = min(stabilize_at, len(p.attempts))

        stabilization_points.append(stabilize_at)
        problem_details.append({
            'pid': p.problem_id,
            'stabilize_at': stabilize_at,
            'total_attempts': len(p.attempts),
            'final_winner': final_winner,
            'expected': p.expected,
            'correct': p.correct,
        })

    # Distribution of stabilization points
    counter = Counter(stabilization_points)
    print(f"\n  {'Stabilizes at':>14} {'Count':>6} {'Cumulative':>11} {'Bar'}")
    print(f"  {'─'*14} {'─'*6} {'─'*11} {'─'*20}")

    output_lines.append("| Stabilizes at attempt | Count | Cumulative | % |")
    output_lines.append("|:---------------------:|------:|-----------:|--:|")

    cum = 0
    for n in range(1, max(stabilization_points) + 1):
        count = counter.get(n, 0)
        cum += count
        pct = 100 * cum / len(stabilization_points)
        bar = '#' * count
        print(f"  {n:>14} {count:>6} {cum:>8}/{len(stabilization_points)} {bar}")
        if count > 0:
            output_lines.append(f"| {n} | {count} | {cum}/{len(stabilization_points)} | {pct:.0f}% |")

    # Summary stats
    avg_stab = sum(stabilization_points) / len(stabilization_points)
    med_stab = sorted(stabilization_points)[len(stabilization_points) // 2]
    p90_stab = sorted(stabilization_points)[int(len(stabilization_points) * 0.9)]

    print(f"\n  Mean: {avg_stab:.1f} | Median: {med_stab} | P90: {p90_stab}")
    print(f"  Interpretation: after attempt {med_stab} (median), adding more doesn't change the answer")

    output_lines.append("")
    output_lines.append(f"**Mean stabilization**: {avg_stab:.1f} attempts | **Median**: {med_stab} | **P90**: {p90_stab}")
    output_lines.append("")

    # Show late-stabilizing problems (these are the ones that benefit from more attempts)
    late = sorted([d for d in problem_details if d['stabilize_at'] >= 6],
                  key=lambda x: -x['stabilize_at'])
    if late:
        print(f"\n  Late-stabilizing problems (stabilize at >= 6):")
        print(f"  {'Problem':<10} {'Stab@':>6} {'Total':>6} {'Winner':>10} {'Expected':>10} {'OK':>4}")
        print(f"  {'─'*10} {'─'*6} {'─'*6} {'─'*10} {'─'*10} {'─'*4}")

        output_lines.append("### Late-Stabilizing Problems (stabilize at >= 6)")
        output_lines.append("")
        output_lines.append("| Problem | Stabilizes at | Total att | Winner | Expected | Correct |")
        output_lines.append("|---------|:------------:|:---------:|:------:|:--------:|:-------:|")

        for d in late[:15]:
            ok = 'Y' if d['correct'] else 'N'
            print(f"  {d['pid']:<10} {d['stabilize_at']:>6} {d['total_attempts']:>6} {str(d['final_winner']):>10} {str(d['expected']):>10} {ok:>4}")
            output_lines.append(f"| {d['pid']} | {d['stabilize_at']} | {d['total_attempts']} | {d['final_winner']} | {d['expected']} | {'Y' if d['correct'] else 'N'} |")
        output_lines.append("")


# ─── Question 4: Optimal (attempts, ES) Grid Search ──────────────────────────

def q4_optimal_grid_search(problems, output_lines):
    """
    Grid search over (max_attempts, es_threshold) combinations.
    For each, compute score and projected time for 50 competition problems.
    Highlight configs that maximize score under 300-min budget.
    """
    output_lines.append("## Q4: Optimal (Attempts, ES) Grid Search")
    output_lines.append("")
    output_lines.append("Budget: 300 min (18000s) for 50 problems + 120s vLLM startup.")
    output_lines.append("Time projection: scale per-problem average from this log to 50 problems.")
    output_lines.append("")

    print(f"\n{'='*75}")
    print(f"  Q4: OPTIMAL (ATTEMPTS, ES) GRID SEARCH")
    print(f"  Budget: 300 min for 50 problems")
    print(f"{'='*75}")

    budget_s = 300 * 60 - 120  # 300 min minus vLLM startup
    n_problems = len(problems)
    n_competition = 50  # scale factor

    grid_results = []

    for max_att in [4, 6, 8, 10, 12, 14, 16]:
        for es in [2, 3, 4, 5, 99]:  # 99 = no ES
            results = simulate_attempts_with_es(problems, max_att, es)
            score = sum(1 for r in results if r['correct'])
            total_time = sum(r['time_s'] for r in results)
            avg_time_per_prob = total_time / n_problems if n_problems else 0
            projected_time = avg_time_per_prob * n_competition + 120  # +startup

            grid_results.append({
                'max_att': max_att,
                'es': es if es < 99 else None,
                'score': score,
                'total': n_problems,
                'accuracy': 100 * score / n_problems if n_problems else 0,
                'avg_time': avg_time_per_prob,
                'projected_50': projected_time,
                'fits': projected_time < 18000,
                'avg_attempts': sum(r['attempts_used'] for r in results) / n_problems,
            })

    # Print grid
    es_labels = [2, 3, 4, 5, None]
    print(f"\n  Score Grid (score/{n_problems}):")
    att_es = 'Att\\ES'
    print(f"  {att_es:>8}", end="")
    for es in es_labels:
        label = str(es) if es else "None"
        print(f"  {label:>8}", end="")
    print()
    print(f"  {'─'*8}", end="")
    for _ in es_labels:
        print(f"  {'─'*8}", end="")
    print()

    output_lines.append("### Score Grid")
    output_lines.append("")
    header = "| Att \\ ES | " + " | ".join(str(e) if e else "None" for e in es_labels) + " |"
    output_lines.append(header)
    output_lines.append("|:--------:|" + "|".join(":---:" for _ in es_labels) + "|")

    for max_att in [4, 6, 8, 10, 12, 14, 16]:
        print(f"  {max_att:>8}", end="")
        row = f"| {max_att} |"
        for es_val in es_labels:
            match = [g for g in grid_results if g['max_att'] == max_att and g['es'] == es_val]
            if match:
                g = match[0]
                marker = '*' if g['fits'] else '!'
                print(f"  {g['score']:>5}{marker:>2}", end="")
                row += f" {g['score']}/{n_problems}{' ' if g['fits'] else ' (X)'} |"
            else:
                print(f"  {'?':>7}", end="")
                row += " ? |"
        print()
        output_lines.append(row)

    output_lines.append("")
    output_lines.append("*Cells without (X) fit within 300-min budget for 50 problems.*")
    output_lines.append("")

    # Projected time grid
    print(f"\n  Projected Time for 50 problems (minutes):")
    att_es = 'Att\\ES'
    print(f"  {att_es:>8}", end="")
    for es in es_labels:
        label = str(es) if es else "None"
        print(f"  {label:>8}", end="")
    print()
    print(f"  {'─'*8}", end="")
    for _ in es_labels:
        print(f"  {'─'*8}", end="")
    print()

    output_lines.append("### Projected Time Grid (minutes for 50 problems)")
    output_lines.append("")
    output_lines.append(header)
    output_lines.append("|:--------:|" + "|".join(":---:" for _ in es_labels) + "|")

    for max_att in [4, 6, 8, 10, 12, 14, 16]:
        print(f"  {max_att:>8}", end="")
        row = f"| {max_att} |"
        for es_val in es_labels:
            match = [g for g in grid_results if g['max_att'] == max_att and g['es'] == es_val]
            if match:
                g = match[0]
                mins = g['projected_50'] / 60
                marker = ' ' if g['fits'] else '!'
                print(f"  {mins:>6.0f}{marker}", end="")
                row += f" {mins:.0f}m{' ' if g['fits'] else ' **EXCEEDS**'} |"
            else:
                print(f"  {'?':>7}", end="")
                row += " ? |"
        print()
        output_lines.append(row)
    output_lines.append("")

    # Find Pareto-optimal configs
    print(f"\n  PARETO-OPTIMAL CONFIGS (highest score at each time budget):")
    print(f"  {'Config':>16} {'Score':>8} {'Acc%':>7} {'AvgAtt':>7} {'Time(50p)':>10} {'Fits?':>6}")
    print(f"  {'─'*16} {'─'*8} {'─'*7} {'─'*7} {'─'*10} {'─'*6}")

    output_lines.append("### Pareto-Optimal Configs")
    output_lines.append("")
    output_lines.append("| Config | Score | Accuracy | Avg Att | Proj. Time (50p) | Fits 300m? |")
    output_lines.append("|--------|------:|---------:|--------:|-----------------:|:----------:|")

    # Sort by score desc, then time asc
    sorted_results = sorted(grid_results, key=lambda g: (-g['score'], g['projected_50']))

    seen_scores = set()
    pareto = []
    for g in sorted_results:
        if g['score'] not in seen_scores:
            seen_scores.add(g['score'])
            pareto.append(g)

    for g in pareto[:10]:
        es_label = str(g['es']) if g['es'] is not None else "None"
        config = f"att={g['max_att']},ES={es_label}"
        mins = g['projected_50'] / 60
        fits = 'YES' if g['fits'] else 'NO'
        print(f"  {config:>16} {g['score']:>5}/{g['total']} {g['accuracy']:>6.1f}% {g['avg_attempts']:>7.1f} {mins:>8.0f}min {fits:>6}")
        output_lines.append(f"| {config} | {g['score']}/{g['total']} | {g['accuracy']:.1f}% | {g['avg_attempts']:.1f} | {mins:.0f}m | {fits} |")

    output_lines.append("")

    # Best config that fits
    best_fit = max((g for g in grid_results if g['fits']), key=lambda g: (g['score'], -g['projected_50']), default=None)
    if best_fit:
        es_label = str(best_fit['es']) if best_fit['es'] is not None else "None"
        print(f"\n  RECOMMENDED: att={best_fit['max_att']}, ES={es_label} -> "
              f"{best_fit['score']}/{best_fit['total']} ({best_fit['accuracy']:.1f}%), "
              f"projected {best_fit['projected_50']/60:.0f}min for 50 problems")
        output_lines.append(f"**RECOMMENDED**: att={best_fit['max_att']}, ES={es_label} -> "
                           f"{best_fit['score']}/{best_fit['total']} ({best_fit['accuracy']:.1f}%), "
                           f"projected {best_fit['projected_50']/60:.0f}min for 50 problems")
        output_lines.append("")


# ─── Question 5: v22 vs v23 Head-to-Head ─────────────────────────────────────

def q5_v22_vs_v23_comparison(problems_v23, problems_v22, output_lines):
    """Compare v22 (8 att, ES=3) vs v23 (16 att, ES=5) on common problems."""
    output_lines.append("## Q5: v22 vs v23 Head-to-Head on Common Problems")
    output_lines.append("")

    print(f"\n{'='*75}")
    print(f"  Q5: v22 vs v23 HEAD-TO-HEAD ON COMMON PROBLEMS")
    print(f"{'='*75}")

    # Build lookup dicts
    v22_by_id = {p.problem_id: p for p in problems_v22}
    v23_by_id = {p.problem_id: p for p in problems_v23}

    common_ids = sorted(set(v22_by_id.keys()) & set(v23_by_id.keys()))

    if not common_ids:
        msg = "  No common problems found between v22 and v23 logs."
        print(msg)
        output_lines.append(msg)
        return

    print(f"\n  Common problems: {len(common_ids)}")
    output_lines.append(f"Common problems: {len(common_ids)}")
    output_lines.append("")

    # Per-problem comparison
    print(f"\n  {'Problem':<10} {'v22':>5} {'v22 Att':>7} {'v22 ES':>7} {'v22 Time':>9} {'v23':>5} {'v23 Att':>7} {'v23 ES':>7} {'v23 Time':>9} {'Delta':>6}")
    print(f"  {'─'*10} {'─'*5} {'─'*7} {'─'*7} {'─'*9} {'─'*5} {'─'*7} {'─'*7} {'─'*9} {'─'*6}")

    output_lines.append("| Problem | v22 | v22 Att | v22 ES | v22 Time | v23 | v23 Att | v23 ES | v23 Time | Changed |")
    output_lines.append("|---------|:---:|:------:|:------:|:--------:|:---:|:------:|:------:|:--------:|:-------:|")

    v22_score = 0
    v23_score = 0
    improved = []
    regressed = []
    same = []

    for pid in common_ids:
        p22 = v22_by_id[pid]
        p23 = v23_by_id[pid]

        ok22 = 'Y' if p22.correct else 'N'
        ok23 = 'Y' if p23.correct else 'N'
        v22_score += int(p22.correct)
        v23_score += int(p23.correct)

        es22 = 'Y' if p22.early_stop else 'N'
        es23 = 'Y' if p23.early_stop else 'N'

        delta = ''
        if p23.correct and not p22.correct:
            delta = '+1'
            improved.append(pid)
        elif p22.correct and not p23.correct:
            delta = '-1'
            regressed.append(pid)
        else:
            same.append(pid)

        print(f"  {pid:<10} {ok22:>5} {len(p22.attempts):>7} {es22:>7} {p22.wall_time:>8.1f}s {ok23:>5} {len(p23.attempts):>7} {es23:>7} {p23.wall_time:>8.1f}s {delta:>6}")
        output_lines.append(f"| {pid} | {ok22} | {len(p22.attempts)} | {es22} | {p22.wall_time:.1f}s | {ok23} | {len(p23.attempts)} | {es23} | {p23.wall_time:.1f}s | {delta or 'same'} |")

    output_lines.append("")

    print(f"\n  Summary: v22={v22_score}/{len(common_ids)}, v23={v23_score}/{len(common_ids)}")
    print(f"  Improved (v22 wrong -> v23 correct): {len(improved)} {improved}")
    print(f"  Regressed (v22 correct -> v23 wrong): {len(regressed)} {regressed}")
    print(f"  Same: {len(same)}")

    output_lines.append(f"**v22**: {v22_score}/{len(common_ids)} | **v23**: {v23_score}/{len(common_ids)}")
    output_lines.append(f"- Improved (v22 wrong -> v23 correct): {len(improved)} {improved}")
    output_lines.append(f"- Regressed (v22 correct -> v23 wrong): {len(regressed)} {regressed}")
    output_lines.append(f"- Same: {len(same)}")
    output_lines.append("")

    # Deep dive: for each common problem, simulate what v23's extra attempts add
    output_lines.append("### Extra-Attempt Benefit Analysis")
    output_lines.append("")
    output_lines.append("For common problems, simulate v23 data with v22 config (8 att, ES=3) vs actual v23 config (16 att, ES=5):")
    output_lines.append("")

    print(f"\n  Simulating v22 config (8 att, ES=3) on v23 data for common problems:")
    print(f"  {'Problem':<10} {'v23@8,ES3':>10} {'v23@16,ES5':>11} {'v23@16,NoES':>12} {'Benefit':>8}")
    print(f"  {'─'*10} {'─'*10} {'─'*11} {'─'*12} {'─'*8}")

    output_lines.append("| Problem | v23@(8,ES=3) | v23@(16,ES=5) | v23@(16,NoES) | Extra att helped? |")
    output_lines.append("|---------|:------------:|:-------------:|:-------------:|:-----------------:|")

    for pid in common_ids:
        p23 = v23_by_id[pid]

        # v22-like config on v23 data
        r_v22config = simulate_attempts_with_es([p23], 8, 3)[0]
        # v23 actual config
        r_v23config = simulate_attempts_with_es([p23], 16, 5)[0]
        # v23 no ES
        r_noes = simulate_attempts_with_es([p23], 16, 99)[0]

        ok_v22c = 'Y' if r_v22config['correct'] else 'N'
        ok_v23c = 'Y' if r_v23config['correct'] else 'N'
        ok_noes = 'Y' if r_noes['correct'] else 'N'

        benefit = ''
        if r_v23config['correct'] and not r_v22config['correct']:
            benefit = 'YES'
        elif not r_v23config['correct'] and r_v22config['correct']:
            benefit = 'HURT'

        print(f"  {pid:<10} {ok_v22c:>10} {ok_v23c:>11} {ok_noes:>12} {benefit:>8}")
        output_lines.append(f"| {pid} | {ok_v22c} | {ok_v23c} | {ok_noes} | {benefit or 'same'} |")

    output_lines.append("")


# ─── Bonus: Deep Analysis of ES Behavior ─────────────────────────────────────

def bonus_es_detailed_behavior(problems, output_lines):
    """Show exactly what happens under each ES threshold for wrong problems."""
    output_lines.append("## Bonus: Detailed ES Behavior on Wrong Problems")
    output_lines.append("")

    print(f"\n{'='*75}")
    print(f"  BONUS: DETAILED ES BEHAVIOR ON WRONG PROBLEMS")
    print(f"{'='*75}")

    # Find all problems that are wrong under current actual voting
    wrong = [p for p in problems if not p.correct and p.expected is not None]

    if not wrong:
        output_lines.append("No wrong problems to analyze.")
        return

    output_lines.append(f"Analyzing {len(wrong)} wrong problems across ES thresholds:")
    output_lines.append("")
    output_lines.append("| Problem | Expected | ES=2 | ES=3 | ES=4 | ES=5 | NoES | Best ES |")
    output_lines.append("|---------|:--------:|:----:|:----:|:----:|:----:|:----:|:-------:|")

    print(f"\n  {'Problem':<10} {'Expected':>10}", end="")
    for es in [2, 3, 4, 5, 99]:
        label = str(es) if es < 99 else "NoES"
        print(f"  {label:>6}", end="")
    print(f"  {'Best':>6}")

    for p in wrong:
        print(f"  {p.problem_id:<10} {p.expected:>10}", end="")
        row = f"| {p.problem_id} | {p.expected} |"
        best_es = None

        for es in [2, 3, 4, 5, 99]:
            r = simulate_attempts_with_es([p], len(p.attempts), es)[0]
            ok = 'Y' if r['correct'] else 'N'
            print(f"  {ok:>6}", end="")
            row += f" {ok} |"
            if r['correct'] and best_es is None:
                best_es = es if es < 99 else None

        best_label = str(best_es) if best_es else "None"
        print(f"  {best_label:>6}")
        row += f" {best_label} |"
        output_lines.append(row)

    output_lines.append("")


# ─── Bonus: Time savings summary ─────────────────────────────────────────────

def bonus_time_savings(problems, output_lines):
    """Summarize projected time savings for top configs."""
    output_lines.append("## Summary: Recommended Configuration")
    output_lines.append("")

    print(f"\n{'='*75}")
    print(f"  SUMMARY: TIME SAVINGS & RECOMMENDATIONS")
    print(f"{'='*75}")

    n = len(problems)
    current_score = sum(1 for p in problems if p.correct)
    current_time = sum(p.wall_time for p in problems)

    # Compare key configs
    configs = [
        ("Current (16att, ES=5)", 16, 5),
        ("Conservative (16att, ES=4)", 16, 4),
        ("Moderate (16att, ES=3)", 16, 3),
        ("Aggressive (12att, ES=4)", 12, 4),
        ("Aggressive (12att, ES=3)", 12, 3),
        ("Minimal (8att, ES=3)", 8, 3),
        ("Tight (8att, ES=2)", 8, 2),
        ("Wide (16att, ES=2)", 16, 2),
    ]

    print(f"\n  Current: {current_score}/{n} correct, total time {current_time:.0f}s ({current_time/60:.1f}min)")
    print(f"\n  {'Config':<28} {'Score':>8} {'AvgAtt':>7} {'TotalT':>8} {'SavedT':>8} {'50p Proj':>9} {'Fits':>5}")
    print(f"  {'─'*28} {'─'*8} {'─'*7} {'─'*8} {'─'*8} {'─'*9} {'─'*5}")

    output_lines.append(f"Current baseline: **{current_score}/{n}** correct, {current_time:.0f}s ({current_time/60:.1f}min)")
    output_lines.append("")
    output_lines.append("| Config | Score | Avg Att | Total Time | Time Saved | 50p Projection | Fits? |")
    output_lines.append("|--------|------:|--------:|-----------:|-----------:|:--------------:|:-----:|")

    for name, max_att, es in configs:
        results = simulate_attempts_with_es(problems, max_att, es)
        score = sum(1 for r in results if r['correct'])
        total_t = sum(r['time_s'] for r in results)
        avg_att = sum(r['attempts_used'] for r in results) / n
        saved = current_time - total_t
        avg_per_prob = total_t / n
        proj = avg_per_prob * 50 + 120
        fits = 'YES' if proj < 18000 else 'NO'

        print(f"  {name:<28} {score:>5}/{n} {avg_att:>7.1f} {total_t:>7.0f}s {saved:>+7.0f}s {proj/60:>8.0f}m {fits:>5}")
        output_lines.append(f"| {name} | {score}/{n} | {avg_att:.1f} | {total_t:.0f}s | {saved:+.0f}s | {proj/60:.0f}m | {fits} |")

    output_lines.append("")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Early Stop & Attempt Optimizer for AIMO3")
    parser.add_argument("logfile", help="Path to v23 diagnostic.log")
    parser.add_argument("--v22", help="Path to v22 diagnostic.log for comparison", default=None)
    parser.add_argument("--save", help="Save markdown results to file", default=None)
    args = parser.parse_args()

    if not os.path.exists(args.logfile):
        print(f"Error: {args.logfile} not found")
        sys.exit(1)

    print(f"Parsing {args.logfile}...")
    problems = parse_log(args.logfile)
    print(f"Parsed {len(problems)} problems")

    # Filter to problems with expected answers
    problems_with_expected = [p for p in problems if p.expected is not None]
    print(f"Problems with expected answers: {len(problems_with_expected)}")
    current_score = sum(1 for p in problems_with_expected if p.correct)
    print(f"Current score: {current_score}/{len(problems_with_expected)}")

    output_lines = [
        "# Early Stop & Attempt Count Optimization (v23)",
        "",
        f"**Source**: `{args.logfile}`  ",
        f"**Problems**: {len(problems_with_expected)} (with expected answers)  ",
        f"**Current config**: 16 attempts, ES=5  ",
        f"**Current score**: {current_score}/{len(problems_with_expected)} ({100*current_score/len(problems_with_expected):.1f}%)  ",
        "",
    ]

    # Run all analyses
    q1_es_simulation(problems_with_expected, output_lines)
    q2_false_positive_rate(problems_with_expected, output_lines)
    q3_vote_stabilization(problems_with_expected, output_lines)
    q4_optimal_grid_search(problems_with_expected, output_lines)

    # Q5 requires v22 log
    if args.v22:
        if os.path.exists(args.v22):
            print(f"\nParsing {args.v22} for comparison...")
            problems_v22 = parse_log(args.v22)
            problems_v22_exp = [p for p in problems_v22 if p.expected is not None]
            print(f"v22: {len(problems_v22_exp)} problems with expected answers")
            q5_v22_vs_v23_comparison(problems_with_expected, problems_v22_exp, output_lines)
        else:
            print(f"Warning: v22 log {args.v22} not found, skipping Q5")
    else:
        # Try default path
        default_v22 = os.path.join(os.path.dirname(os.path.dirname(args.logfile)), 'v22', 'diagnostic.log')
        if os.path.exists(default_v22):
            print(f"\nFound v22 log at {default_v22}, loading for comparison...")
            problems_v22 = parse_log(default_v22)
            problems_v22_exp = [p for p in problems_v22 if p.expected is not None]
            print(f"v22: {len(problems_v22_exp)} problems with expected answers")
            q5_v22_vs_v23_comparison(problems_with_expected, problems_v22_exp, output_lines)

    bonus_es_detailed_behavior(problems_with_expected, output_lines)
    bonus_time_savings(problems_with_expected, output_lines)

    # Save results
    if args.save:
        save_dir = os.path.dirname(args.save)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        with open(args.save, 'w') as f:
            f.write('\n'.join(output_lines))
        print(f"\nResults saved to {args.save}")


if __name__ == '__main__':
    main()
