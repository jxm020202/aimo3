#!/usr/bin/env python3
"""
Build the final number_theory_algebra.json database from parsed log data.
Aggregates across multiple runs of the same problem in v23 (double-run, retry).
"""

import sys
import os
import json
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def main():
    os.chdir('/Users/intern/Desktop/sideprojects/aimo3')

    v23 = parse_log('output/v23/diagnostic.log')
    v31 = parse_log('output/v31/diagnostic.log')

    # Index by problem_id, collecting ALL runs
    all_runs = {}
    for ver, probs in [('v23', v23), ('v31', v31)]:
        for p in probs:
            pid = p.problem_id
            if pid not in all_runs:
                all_runs[pid] = []
            all_runs[pid].append((ver, p))

    # Now build entries for target problems
    target_pids = ['3980cd', '86e8e5', '3b88b3', '29714f', 'aff75c']

    # Print aggregated stats
    for pid in target_pids:
        runs = all_runs.get(pid, [])
        total_att = sum(len(p.attempts) for _, p in runs)
        total_correct = sum(
            sum(1 for a in p.attempts if a.answer == p.expected)
            for _, p in runs
        )
        all_answers = Counter()
        for _, p in runs:
            for a in p.attempts:
                if a.answer is not None:
                    all_answers[a.answer] += 1

        none_count = sum(
            sum(1 for a in p.attempts if a.is_none)
            for _, p in runs
        )

        print(f"\n{pid}: {len(runs)} runs, {total_att} attempts, "
              f"{total_correct} correct, {none_count} None")
        expected = runs[0][1].expected
        wrong_answers = {k: v for k, v in all_answers.items() if k != expected}
        print(f"  Expected: {expected}")
        print(f"  Wrong answers: {dict(Counter(wrong_answers).most_common(10))}")
        print(f"  Version results:")
        for ver, p in runs:
            print(f"    {ver}: predicted={p.predicted}, correct={p.correct}, "
                  f"votes={dict(p.votes) if p.votes else {}}")


if __name__ == '__main__':
    main()
