#!/usr/bin/env python3
"""
Attempt Progression Analysis for AIMO3 Solver
===============================================
Analyzes answer convergence, when correct answers appear,
answer diversity, quality progression, and reduced-attempt simulations.

Usage: python3 log_exploration/attempt_progression.py output/v22/diagnostic.log
"""

import sys
import os
import math
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def mean(vals):
    return sum(vals) / len(vals) if vals else 0


def median(vals):
    if not vals:
        return 0
    s = sorted(vals)
    n = len(s)
    if n % 2 == 0:
        return (s[n // 2 - 1] + s[n // 2]) / 2
    return s[n // 2]


def stdev(vals):
    if len(vals) < 2:
        return 0
    m = mean(vals)
    return math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))


def print_section(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def analyze_answer_convergence(problems):
    """Do later attempts converge to the same answer?"""
    print_section("ANSWER CONVERGENCE")

    # Track unique answers seen cumulatively per attempt
    print(f"\n  Cumulative Unique Answers by Attempt Number:")
    print(f"  (Excluding Nones — only counting distinct non-None answers)")
    print(f"\n  {'Problem':<10} {'A1':>4} {'A2':>4} {'A3':>4} {'A4':>4} {'A5':>4} {'A6':>4} {'A7':>4} {'A8':>4} {'Final':>8} {'OK':>4}")
    print(f"  {'─' * 10} {'─' * 4} {'─' * 4} {'─' * 4} {'─' * 4} {'─' * 4} {'─' * 4} {'─' * 4} {'─' * 4} {'─' * 8} {'─' * 4}")

    max_att = max((a.attempt_num for p in problems for a in p.attempts), default=8)

    convergence_by_attempt = defaultdict(list)  # attempt_num -> list of unique_answer_counts

    for p in sorted(problems, key=lambda p: p.problem_id):
        sorted_attempts = sorted(p.attempts, key=lambda a: a.attempt_num)
        seen = set()
        row = []
        for n in range(1, max_att + 1):
            matching = [a for a in sorted_attempts if a.attempt_num == n]
            for a in matching:
                if a.answer is not None:
                    seen.add(a.answer)
            row.append(len(seen))
            convergence_by_attempt[n].append(len(seen))

        ok = "Y" if p.correct else "N"
        row_str = " ".join(f"{r:>4}" for r in row)
        final = str(p.predicted) if p.predicted is not None else "None"
        print(f"  {p.problem_id:<10} {row_str} {final:>8} {ok:>4}")

    # Average unique answers by attempt
    print(f"\n  Average Cumulative Unique Answers:")
    print(f"  {'Attempt':>8} {'Mean Unique':>12} {'Median':>8}")
    print(f"  {'─' * 8} {'─' * 12} {'─' * 8}")
    for n in range(1, max_att + 1):
        vals = convergence_by_attempt.get(n, [])
        if vals:
            print(f"  {n:>8} {mean(vals):>12.2f} {median(vals):>8.1f}")

    # Convergence detection: problems where last 3 attempts all agree
    converged = 0
    total = 0
    for p in problems:
        sorted_attempts = sorted(p.attempts, key=lambda a: a.attempt_num)
        last_3 = [a for a in sorted_attempts if a.attempt_num >= max_att - 2]
        non_none_last3 = [a.answer for a in last_3 if a.answer is not None]
        if non_none_last3:
            total += 1
            if len(set(non_none_last3)) == 1:
                converged += 1

    print(f"\n  Convergence: {converged}/{total} problems have last 3 non-None attempts agreeing ({100*converged/total if total else 0:.0f}%)")


def analyze_first_correct_appearance(problems):
    """When does the correct answer first appear?"""
    print_section("FIRST CORRECT ANSWER APPEARANCE")

    first_correct = Counter()
    never_found = 0
    total = 0

    for p in problems:
        if p.expected is None:
            continue
        total += 1
        found = False
        for a in sorted(p.attempts, key=lambda x: x.attempt_num):
            if a.answer == p.expected:
                first_correct[a.attempt_num] += 1
                found = True
                break
        if not found:
            never_found += 1

    print(f"\n  First Appearance of Correct Answer ({total} problems):")
    print(f"  {'Attempt #':<12} {'Count':>8} {'Pct':>8} {'Cumulative':>12} {'Bar'}")
    print(f"  {'─' * 12} {'─' * 8} {'─' * 8} {'─' * 12} {'─' * 20}")

    max_att = max((a.attempt_num for p in problems for a in p.attempts), default=8)
    cumulative = 0
    for n in range(1, max_att + 1):
        count = first_correct.get(n, 0)
        cumulative += count
        pct = 100 * count / total if total else 0
        bar = '#' * count
        print(f"  {n:<12} {count:>8} {pct:>7.1f}% {cumulative:>12}  {bar}")

    if never_found > 0:
        print(f"  {'Never':<12} {never_found:>8} {100*never_found/total:>7.1f}%")

    # Critical metric: what % of eventually-correct problems find the answer in attempt 1?
    eventually_correct = sum(first_correct.values())
    if eventually_correct > 0 and first_correct.get(1, 0) > 0:
        print(f"\n  {first_correct[1]}/{eventually_correct} problems that have a correct answer find it on attempt 1 ({100*first_correct[1]/eventually_correct:.0f}%)")

    # For wrong-final-answer problems, did the correct answer ever appear?
    outvoted = 0
    for p in problems:
        if p.expected is None or p.correct:
            continue
        for a in p.attempts:
            if a.answer == p.expected:
                outvoted += 1
                break

    wrong_count = sum(1 for p in problems if not p.correct and p.expected is not None)
    if wrong_count > 0:
        print(f"\n  Among {wrong_count} wrong problems: {outvoted} had the correct answer in at least one attempt (outvoted).")


def analyze_answer_diversity(problems):
    """Number of unique answers per problem."""
    print_section("ANSWER DIVERSITY")

    diversity_data = []
    for p in problems:
        non_none = [a.answer for a in p.attempts if a.answer is not None]
        unique = len(set(non_none))
        total = len(non_none)
        none_count = sum(1 for a in p.attempts if a.is_none)
        diversity_data.append((p.problem_id, unique, total, none_count, p.correct))

    # Sort by diversity (most diverse first)
    diversity_data.sort(key=lambda x: -x[1])

    print(f"\n  {'Problem':<10} {'Unique':>7} {'Total Ans':>10} {'Nones':>6} {'OK':>4} {'Diversity':>10}")
    print(f"  {'─' * 10} {'─' * 7} {'─' * 10} {'─' * 6} {'─' * 4} {'─' * 10}")

    for pid, unique, total, nones, correct in diversity_data:
        diversity = unique / total if total > 0 else 0
        ok = "Y" if correct else "N"
        bar = '*' * unique
        print(f"  {pid:<10} {unique:>7} {total:>10} {nones:>6} {ok:>4} {diversity:>9.2f}  {bar}")

    # Aggregate
    correct_diversity = [d[1] for d in diversity_data if d[4]]
    wrong_diversity = [d[1] for d in diversity_data if not d[4]]
    print(f"\n  Average Unique Answers:")
    if correct_diversity:
        print(f"    Correct problems: {mean(correct_diversity):.1f} unique answers (mean)")
    if wrong_diversity:
        print(f"    Wrong problems:   {mean(wrong_diversity):.1f} unique answers (mean)")

    # Correlation: high diversity = harder problem?
    high_div = [d for d in diversity_data if d[1] >= 3]
    low_div = [d for d in diversity_data if d[1] <= 1]
    if high_div:
        high_correct = sum(1 for d in high_div if d[4])
        print(f"\n  High diversity (3+ unique): {high_correct}/{len(high_div)} correct ({100*high_correct/len(high_div):.0f}%)")
    if low_div:
        low_correct = sum(1 for d in low_div if d[4])
        print(f"  Low diversity (0-1 unique): {low_correct}/{len(low_div)} correct ({100*low_correct/len(low_div):.0f}%)")


def analyze_quality_progression(problems):
    """Are later attempts better than earlier ones?"""
    print_section("QUALITY PROGRESSION BY ATTEMPT NUMBER")

    max_att = max((a.attempt_num for p in problems for a in p.attempts), default=8)

    # Per-attempt-number stats
    print(f"\n  {'Attempt':>8} {'Correct':>8} {'Wrong':>8} {'None':>8} {'Total':>8} {'Acc%':>8} {'None%':>8}")
    print(f"  {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8}")

    for n in range(1, max_att + 1):
        correct = 0
        wrong = 0
        none = 0
        total = 0
        for p in problems:
            if p.expected is None:
                continue
            for a in p.attempts:
                if a.attempt_num == n:
                    total += 1
                    if a.is_none:
                        none += 1
                    elif a.answer == p.expected:
                        correct += 1
                    else:
                        wrong += 1

        if total > 0:
            non_none = correct + wrong
            acc = 100 * correct / non_none if non_none > 0 else 0
            none_pct = 100 * none / total
            print(f"  {n:>8} {correct:>8} {wrong:>8} {none:>8} {total:>8} {acc:>7.1f}% {none_pct:>7.1f}%")

    # By temperature (if available)
    temp_stats = defaultdict(lambda: {"correct": 0, "wrong": 0, "none": 0, "total": 0})
    for p in problems:
        if p.expected is None:
            continue
        for a in p.attempts:
            if a.temperature is not None:
                t = f"{a.temperature:.1f}"
                temp_stats[t]["total"] += 1
                if a.is_none:
                    temp_stats[t]["none"] += 1
                elif a.answer == p.expected:
                    temp_stats[t]["correct"] += 1
                else:
                    temp_stats[t]["wrong"] += 1

    if temp_stats:
        print(f"\n  By Temperature:")
        print(f"  {'Temp':>8} {'Correct':>8} {'Wrong':>8} {'None':>8} {'Total':>8} {'Acc%':>8} {'None%':>8}")
        print(f"  {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8}")
        for temp in sorted(temp_stats.keys(), key=float):
            s = temp_stats[temp]
            non_none = s["correct"] + s["wrong"]
            acc = 100 * s["correct"] / non_none if non_none > 0 else 0
            none_pct = 100 * s["none"] / s["total"]
            print(f"  {temp:>8} {s['correct']:>8} {s['wrong']:>8} {s['none']:>8} {s['total']:>8} {acc:>7.1f}% {none_pct:>7.1f}%")


def analyze_reduced_attempts(problems):
    """If we ran only N attempts (not 8), what would our score be?"""
    print_section("REDUCED ATTEMPT SIMULATION")

    total_with_expected = sum(1 for p in problems if p.expected is not None)
    max_att = max((a.attempt_num for p in problems for a in p.attempts), default=8)

    # Simple majority vote with first N attempts
    print(f"\n  Score with majority vote using first N attempts:")
    print(f"  {'Max N':>6} {'Score':>8} {'Pct':>8} {'Delta vs 8':>10} {'Notes':<20}")
    print(f"  {'─' * 6} {'─' * 8} {'─' * 8} {'─' * 10} {'─' * 20}")

    # Compute score with all 8 for reference
    score_at_8 = 0
    for p in problems:
        if p.expected is None:
            continue
        if p.votes:
            winner = max(p.votes, key=p.votes.get)
            if winner == p.expected:
                score_at_8 += 1

    for max_n in range(1, max_att + 1):
        score = 0
        for p in problems:
            if p.expected is None:
                continue
            votes = defaultdict(int)
            for a in sorted(p.attempts, key=lambda x: x.attempt_num):
                if a.attempt_num <= max_n:
                    if a.answer is not None:
                        votes[a.answer] += 1
            if votes:
                winner = max(votes, key=votes.get)
                if winner == p.expected:
                    score += 1
        delta = score - score_at_8
        pct = 100 * score / total_with_expected if total_with_expected else 0
        delta_str = f"+{delta}" if delta > 0 else str(delta) if delta != 0 else "0"
        actual_str = " (actual)" if max_n == max_att else ""
        print(f"  {max_n:>6} {score:>5}/{total_with_expected} {pct:>7.1f}% {delta_str:>10}{actual_str}")

    # Also simulate 10, 12, 16 attempts by bootstrap
    print(f"\n  Simulated 'more attempts' via bootstrap resampling:")
    print(f"  (Sampling with replacement from existing 8 attempts per problem)")

    import random
    random.seed(42)
    for extra_n in [10, 12, 16]:
        scores = []
        for trial in range(100):
            trial_score = 0
            for p in problems:
                if p.expected is None:
                    continue
                attempts = [a for a in p.attempts if a.answer is not None]
                if not attempts:
                    continue
                # Take original attempts + bootstrap extras
                sample = list(attempts)
                while len(sample) < extra_n:
                    sample.append(random.choice(attempts))
                sample = sample[:extra_n]
                votes = defaultdict(int)
                for a in sample:
                    votes[a.answer] += 1
                if votes:
                    winner = max(votes, key=votes.get)
                    if winner == p.expected:
                        trial_score += 1
            scores.append(trial_score)
        avg = mean(scores)
        lo = min(scores)
        hi = max(scores)
        print(f"  {extra_n:>3} attempts (bootstrap): avg={avg:.1f}/{total_with_expected}, range=[{lo}-{hi}]")

    # Early stop analysis with different thresholds
    print(f"\n  Score with Early Stop at Different Thresholds (N matching answers):")
    print(f"  {'Threshold':>10} {'Score':>8} {'Avg Att Used':>14} {'Avg Time':>10}")
    print(f"  {'─' * 10} {'─' * 8} {'─' * 14} {'─' * 10}")

    for threshold in [2, 3, 4, 5, 6, 7, 8]:
        score = 0
        total_att_used = 0
        total_time_used = 0
        for p in problems:
            if p.expected is None:
                continue
            votes = defaultdict(int)
            best_count = 0
            best_answer = None
            att_used = 0
            time_used = 0

            for a in sorted(p.attempts, key=lambda x: x.attempt_num):
                att_used += 1
                time_used += a.time_s
                if a.answer is not None:
                    votes[a.answer] += 1
                    if votes[a.answer] > best_count:
                        best_count = votes[a.answer]
                        best_answer = a.answer
                if best_count >= threshold:
                    break

            total_att_used += att_used
            total_time_used += time_used
            if best_answer == p.expected:
                score += 1

        avg_att = total_att_used / total_with_expected if total_with_expected else 0
        avg_time = total_time_used / total_with_expected if total_with_expected else 0
        print(f"  {threshold:>10} {score:>5}/{total_with_expected} {avg_att:>14.1f} {avg_time:>9.1f}s")


def print_actionable_insights(problems):
    """Summarize key findings."""
    print_section("ACTIONABLE INSIGHTS")

    total_with_expected = sum(1 for p in problems if p.expected is not None)
    max_att = max((a.attempt_num for p in problems for a in p.attempts), default=8)

    # 1. Attempt count
    # How many problems are first solved on attempt >= 4?
    late_solves = 0
    for p in problems:
        if p.expected is None:
            continue
        for a in sorted(p.attempts, key=lambda x: x.attempt_num):
            if a.answer == p.expected:
                if a.attempt_num >= 4:
                    late_solves += 1
                break

    print(f"\n  1. ATTEMPT COUNT: {late_solves} problems first find the correct answer on attempt 4+.")
    if late_solves <= 2:
        print(f"     Most problems find the answer early. Running 8 attempts is mostly for voting confidence.")
        print(f"     RECOMMENDATION: 4 attempts might suffice for easy problems. Save budget for hard problems (16 attempts).")
    else:
        print(f"     Later attempts contribute meaningfully. Keep 8 attempts minimum.")

    # 2. Diversity insight
    correct_diversity = []
    wrong_diversity = []
    for p in problems:
        if p.expected is None:
            continue
        non_none = set(a.answer for a in p.attempts if a.answer is not None)
        if p.correct:
            correct_diversity.append(len(non_none))
        else:
            wrong_diversity.append(len(non_none))

    if correct_diversity and wrong_diversity:
        print(f"\n  2. ANSWER DIVERSITY: Correct problems average {mean(correct_diversity):.1f} unique answers, "
              f"wrong problems average {mean(wrong_diversity):.1f}.")
        if mean(wrong_diversity) > mean(correct_diversity):
            print(f"     Higher diversity = less consensus = more likely wrong.")
            print(f"     RECOMMENDATION: Flag high-diversity problems for extra attempts or different approach.")

    # 3. Quality by position
    first_half_correct = 0
    second_half_correct = 0
    first_half_total = 0
    second_half_total = 0
    mid = max_att // 2
    for p in problems:
        if p.expected is None:
            continue
        for a in p.attempts:
            if a.answer is not None:
                if a.attempt_num <= mid:
                    first_half_total += 1
                    if a.answer == p.expected:
                        first_half_correct += 1
                else:
                    second_half_total += 1
                    if a.answer == p.expected:
                        second_half_correct += 1

    if first_half_total and second_half_total:
        first_acc = 100 * first_half_correct / first_half_total
        second_acc = 100 * second_half_correct / second_half_total
        print(f"\n  3. QUALITY BY POSITION: First half accuracy: {first_acc:.1f}%, second half: {second_acc:.1f}%.")
        if abs(first_acc - second_acc) < 5:
            print(f"     No significant quality difference between early and late attempts.")
        elif first_acc > second_acc:
            print(f"     Early attempts are more accurate. Consider prioritizing early-attempt answers.")
        else:
            print(f"     Later attempts are more accurate. Temperature schedule may be helping.")

    # 4. Optimal config
    print(f"\n  4. OPTIMAL CONFIGURATION SUGGESTION:")
    print(f"     - Easy problems (solved in <30s): 4 attempts, early stop at 3")
    print(f"     - Medium problems: 8 attempts, early stop at 5 (current)")
    print(f"     - Hard problems (>120s, no early stop): 16 attempts, no early stop")
    print(f"     - Detect difficulty dynamically: if first 4 attempts all None or all different, allocate more budget")
    print()


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} <logfile>")
        sys.exit(1)

    logfile = sys.argv[1]
    if not os.path.exists(logfile):
        print(f"Error: File not found: {logfile}")
        sys.exit(1)

    print(f"Parsing {logfile}...")
    problems = parse_log(logfile)
    print(f"Parsed {len(problems)} problems.")

    analyze_answer_convergence(problems)
    analyze_first_correct_appearance(problems)
    analyze_answer_diversity(problems)
    analyze_quality_progression(problems)
    analyze_reduced_attempts(problems)
    print_actionable_insights(problems)


if __name__ == "__main__":
    main()
