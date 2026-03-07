#!/usr/bin/env python3
"""Simulate impact of different rerun thresholds on score.

Simulates: if we had rerun problems with top_votes < threshold,
what's the maximum possible score improvement?

Usage: python3 log_exploration/rerun_simulation.py <diagnostic.log>
"""
import sys
from collections import Counter
sys.path.insert(0, '.')
from log_exploration.log_query import parse_log


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <diagnostic.log>")
        sys.exit(1)

    problems = parse_log(sys.argv[1])
    n = len(problems)
    baseline = sum(1 for p in problems if p.correct)

    print(f"{'='*72}")
    print(f"  RERUN THRESHOLD SIMULATION")
    print(f"{'='*72}")
    print(f"  Baseline: {baseline}/{n} ({baseline*100/n:.0f}%)")
    # Auto-detect base attempts as mode
    attempt_counts = Counter(len(p.attempts) for p in problems)
    base_attempts = attempt_counts.most_common(1)[0][0] if attempt_counts else 48
    current_threshold = max(1, (base_attempts + 2) // 3)  # ceil(attempts/3)
    print(f"  Current rerun threshold: top_votes < {current_threshold} (ceil({base_attempts}/3))")
    print()

    # For each threshold, identify which problems would get a rerun
    for threshold in [5, 8, 11, 14, 16, 20]:
        rerun_problems = []
        for p in problems:
            votes = Counter(a.answer for a in p.attempts if a.answer is not None)
            if votes:
                top_v = votes.most_common(1)[0][1]
                if top_v < threshold:
                    rerun_problems.append((p, top_v))

        # Best case: rerun fixes all wrong problems in the set
        wrong_rerun = [p for p, _ in rerun_problems if not p.correct]
        correct_rerun = [p for p, _ in rerun_problems if p.correct]
        # Risk: rerun could flip correct to wrong
        best_case = baseline + len(wrong_rerun)
        worst_case = baseline - len(correct_rerun)

        # Realistic: check if correct answer exists in the attempts
        fixable = []
        for p, tv in rerun_problems:
            if not p.correct:
                has_correct = any(a.answer == p.expected for a in p.attempts)
                fixable.append((p, tv, has_correct))

        # Time cost estimate: ~340s per rerun problem
        time_cost = len(rerun_problems) * 340

        print(f"  Threshold < {threshold}: {len(rerun_problems)} problems would rerun")
        print(f"    Correct in set: {len(correct_rerun)} (risk of regression)")
        print(f"    Wrong in set: {len(wrong_rerun)}")
        for p, tv, has_correct in fixable:
            tag = "has_correct_in_attempts" if has_correct else "never_found_correct"
            print(f"      {p.problem_id}: top_v={tv}, pred={p.predicted}, exp={p.expected} [{tag}]")
        print(f"    Best case: {best_case}/{n}, worst case: {worst_case}/{n}")
        print(f"    Est. time cost: {time_cost//60}min")
        print()

    # Detailed: problems sorted by top votes
    print(f"  {'─'*72}")
    print(f"  ALL PROBLEMS BY TOP VOTES (ascending)")
    print(f"  {'─'*72}")
    prob_votes = []
    for p in problems:
        votes = Counter(a.answer for a in p.attempts if a.answer is not None)
        if votes:
            top_ans, top_v = votes.most_common(1)[0]
            n_distinct = len(votes)
            has_correct = any(a.answer == p.expected for a in p.attempts)
        else:
            top_v, n_distinct, has_correct = 0, 0, False
        prob_votes.append((p, top_v, n_distinct, has_correct))

    for p, tv, nd, hc in sorted(prob_votes, key=lambda x: x[1]):
        status = "OK" if p.correct else "WRONG"
        hc_tag = "correct_in_attempts" if hc and not p.correct else ""
        print(f"    {p.problem_id}: top_v={tv:2d}, distinct={nd:2d}, {status:5s} {hc_tag}")


if __name__ == '__main__':
    main()
