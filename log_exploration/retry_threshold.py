#!/usr/bin/env python3
"""
Retry Threshold Analysis: Find the sweet spot for "when should we retry?"

Simulates: if the top-voted answer has fewer than K votes, we consider the
result low-confidence and would benefit from a retry.

Also analyzes:
- None count thresholds (4+ Nones → retry?)
- Unique answer count thresholds (4+ unique answers → retry?)
- Combined signals

Usage:
    python3 log_exploration/retry_threshold.py <diagnostic.log>
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log_exploration.log_query import parse_log
from collections import Counter


def analyze_retry_thresholds(problems):
    # Deduplicate
    seen = set()
    unique = []
    for p in problems:
        if p.problem_id not in seen:
            seen.add(p.problem_id)
            unique.append(p)
    problems = unique

    print(f"{'='*80}")
    print(f"  RETRY THRESHOLD ANALYSIS")
    print(f"{'='*80}")
    print(f"  Total problems: {len(problems)}\n")

    # Gather stats per problem
    stats = []
    for p in problems:
        votes = Counter()
        none_count = 0
        total = len(p.attempts)
        for a in p.attempts:
            if a.answer is not None:
                votes[a.answer] += 1
            else:
                none_count += 1

        if not votes:
            top_vote_count = 0
            top_answer = None
            unique_answers = 0
        else:
            mc = votes.most_common()
            top_vote_count = mc[0][1]
            top_answer = mc[0][0]
            unique_answers = len(votes)

        correct = (top_answer == p.expected) if top_answer is not None else False

        stats.append({
            'id': p.problem_id,
            'expected': p.expected,
            'predicted': top_answer,
            'correct': correct,
            'top_votes': top_vote_count,
            'none_count': none_count,
            'unique_answers': unique_answers,
            'total': total,
            'vote_dist': dict(votes.most_common()),
        })

    total_correct = sum(1 for s in stats if s['correct'])
    total_wrong = sum(1 for s in stats if not s['correct'])

    # 1. Top-vote threshold analysis
    print(f"  {'─'*76}")
    print(f"  1. TOP-VOTE THRESHOLD: 'Retry if winner has < K votes'")
    print(f"  {'─'*76}")
    print(f"  {'K':>4} {'Would retry':>12} {'Correct→Retry':>15} {'Wrong→Retry':>13} {'Keep correct':>14} {'Precision':>10}")

    for k in range(1, 17):
        retry = [s for s in stats if s['top_votes'] < k]
        keep = [s for s in stats if s['top_votes'] >= k]
        correct_retry = sum(1 for s in retry if s['correct'])
        wrong_retry = sum(1 for s in retry if not s['correct'])
        correct_keep = sum(1 for s in keep if s['correct'])
        wrong_keep = sum(1 for s in keep if not s['correct'])
        # Precision = fraction of retried that are actually wrong
        precision = wrong_retry / len(retry) if retry else 0
        print(f"  {k:>4} {len(retry):>12} {correct_retry:>15} {wrong_retry:>13} {correct_keep:>14} {precision:>10.1%}")

    # 2. None count threshold
    print(f"\n  {'─'*76}")
    print(f"  2. NONE-COUNT THRESHOLD: 'Retry if >= K attempts returned None'")
    print(f"  {'─'*76}")
    print(f"  {'K':>4} {'Would retry':>12} {'Correct→Retry':>15} {'Wrong→Retry':>13} {'Precision':>10}")

    for k in range(1, 13):
        retry = [s for s in stats if s['none_count'] >= k]
        correct_retry = sum(1 for s in retry if s['correct'])
        wrong_retry = sum(1 for s in retry if not s['correct'])
        precision = wrong_retry / len(retry) if retry else 0
        print(f"  {k:>4} {len(retry):>12} {correct_retry:>15} {wrong_retry:>13} {precision:>10.1%}")

    # 3. Unique answer threshold
    print(f"\n  {'─'*76}")
    print(f"  3. UNIQUE-ANSWER THRESHOLD: 'Retry if >= K different answers'")
    print(f"  {'─'*76}")
    print(f"  {'K':>4} {'Would retry':>12} {'Correct→Retry':>15} {'Wrong→Retry':>13} {'Precision':>10}")

    for k in range(1, 13):
        retry = [s for s in stats if s['unique_answers'] >= k]
        correct_retry = sum(1 for s in retry if s['correct'])
        wrong_retry = sum(1 for s in retry if not s['correct'])
        precision = wrong_retry / len(retry) if retry else 0
        print(f"  {k:>4} {len(retry):>12} {correct_retry:>15} {wrong_retry:>13} {precision:>10.1%}")

    # 4. Combined: top_votes < K AND unique > M
    print(f"\n  {'─'*76}")
    print(f"  4. COMBINED: 'Retry if top_votes < K AND unique_answers >= M'")
    print(f"  {'─'*76}")
    print(f"  {'K':>4} {'M':>4} {'Would retry':>12} {'Correct→Retry':>15} {'Wrong→Retry':>13} {'Precision':>10}")

    for k in [3, 4, 5, 6, 7, 8]:
        for m in [2, 3, 4, 5]:
            retry = [s for s in stats if s['top_votes'] < k and s['unique_answers'] >= m]
            correct_retry = sum(1 for s in retry if s['correct'])
            wrong_retry = sum(1 for s in retry if not s['correct'])
            precision = wrong_retry / len(retry) if retry else 0
            if retry:  # Only show non-empty
                print(f"  {k:>4} {m:>4} {len(retry):>12} {correct_retry:>15} {wrong_retry:>13} {precision:>10.1%}")

    # 5. Detailed table for wrong problems
    print(f"\n  {'─'*76}")
    print(f"  5. ALL PROBLEMS (sorted by top_votes)")
    print(f"  {'─'*76}")
    print(f"  {'ID':<10} {'OK':>4} {'Top':>4} {'None':>5} {'Uniq':>5} {'TopAnswer':>10} {'Expected':>10} {'Distribution'}")

    for s in sorted(stats, key=lambda x: x['top_votes']):
        ok = 'Y' if s['correct'] else 'N'
        dist_str = str(s['vote_dist'])
        if len(dist_str) > 40:
            dist_str = dist_str[:40] + '..'
        print(f"  {s['id']:<10} {ok:>4} {s['top_votes']:>4} {s['none_count']:>5} {s['unique_answers']:>5} "
              f"{str(s['predicted']):>10} {str(s['expected']):>10} {dist_str}")

    # 6. Focus on wrong problems that could be saved
    print(f"\n  {'─'*76}")
    print(f"  6. WRONG PROBLEMS — COULD RETRY HELP?")
    print(f"  {'─'*76}")
    wrong = [s for s in stats if not s['correct']]
    for s in sorted(wrong, key=lambda x: x['top_votes']):
        has_correct = s['expected'] in s['vote_dist']
        correct_votes = s['vote_dist'].get(s['expected'], 0)
        print(f"  {s['id']}: top={s['top_votes']}x{s['predicted']}, "
              f"correct_in_votes={'YES(' + str(correct_votes) + ')' if has_correct else 'NO'}, "
              f"nones={s['none_count']}, uniq={s['unique_answers']}")

    # 7. Time saved if we skip retries on correct unanimous
    print(f"\n  {'─'*76}")
    print(f"  7. TIME SAVINGS: Skip retries on high-confidence correct problems")
    print(f"  {'─'*76}")
    # Can't compute time without attempt time data, but show counts
    for k in [8, 10, 12, 14, 16]:
        confident_correct = [s for s in stats if s['correct'] and s['top_votes'] >= k]
        print(f"  top_votes >= {k}: {len(confident_correct)} problems would NOT need retry")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <diagnostic.log>")
        sys.exit(1)

    problems = parse_log(sys.argv[1])
    analyze_retry_thresholds(problems)
