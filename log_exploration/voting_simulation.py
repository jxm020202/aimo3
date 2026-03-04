#!/usr/bin/env python3
"""
Voting Simulation: Compare entropy-weighted vs majority-vote scoring.

For each problem, simulates both scoring methods and shows which problems
would flip (change from correct→wrong or wrong→correct).

Usage:
    python3 log_exploration/voting_simulation.py output/v23/diagnostic.log
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log_exploration.log_query import parse_log
from collections import defaultdict


def simulate_voting(problems):
    """Compare entropy-weighted vs majority-vote for all problems."""

    results = []

    for p in problems:
        if not p.attempts:
            continue

        # Collect per-attempt data
        answer_entropy_weights = defaultdict(float)
        answer_votes = defaultdict(int)
        attempt_details = []

        for a in p.attempts:
            if a.answer is not None:
                entropy = a.entropy if a.entropy and a.entropy != float('inf') else 1.0
                weight = 1.0 / max(entropy, 1e-9)
                answer_entropy_weights[a.answer] += weight
                answer_votes[a.answer] += 1
                attempt_details.append({
                    'attempt': a.attempt_num,
                    'answer': a.answer,
                    'entropy': entropy,
                    'weight': weight,
                    'temp': getattr(a, 'temperature', None),
                })

        if not answer_votes:
            results.append({
                'id': p.problem_id,
                'expected': p.expected,
                'entropy_pick': None,
                'majority_pick': None,
                'entropy_correct': False,
                'majority_correct': False,
                'flip': 'none→none',
                'details': [],
                'vote_dist': {},
                'weight_dist': {},
            })
            continue

        # Entropy-weighted winner (current method)
        entropy_scored = []
        for ans, total_weight in answer_entropy_weights.items():
            entropy_scored.append((total_weight, answer_votes[ans], ans))
        entropy_scored.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        entropy_pick = entropy_scored[0][2]

        # Majority-vote winner (proposed method)
        majority_scored = []
        for ans, votes in answer_votes.items():
            majority_scored.append((votes, answer_entropy_weights[ans], ans))
        majority_scored.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        majority_pick = majority_scored[0][2]

        entropy_correct = (entropy_pick == p.expected)
        majority_correct = (majority_pick == p.expected)

        if entropy_correct and majority_correct:
            flip = 'both_correct'
        elif entropy_correct and not majority_correct:
            flip = 'REGRESSION'  # majority would break this
        elif not entropy_correct and majority_correct:
            flip = 'FIX'  # majority would fix this
        else:
            flip = 'both_wrong'

        results.append({
            'id': p.problem_id,
            'expected': p.expected,
            'entropy_pick': entropy_pick,
            'majority_pick': majority_pick,
            'entropy_correct': entropy_correct,
            'majority_correct': majority_correct,
            'flip': flip,
            'details': attempt_details,
            'vote_dist': dict(answer_votes),
            'weight_dist': {ans: round(w, 2) for ans, w in answer_entropy_weights.items()},
            'entropy_scored': [(ans, votes, round(w, 2)) for w, votes, ans in entropy_scored],
            'majority_scored': [(ans, votes, round(w, 2)) for votes, w, ans in majority_scored],
        })

    return results


def print_report(results):
    """Print the comparison report."""

    entropy_total = sum(1 for r in results if r['entropy_correct'])
    majority_total = sum(1 for r in results if r['majority_correct'])
    total = len(results)

    print(f'{"="*80}')
    print(f'  VOTING SIMULATION: Entropy-Weighted vs Majority-Vote')
    print(f'{"="*80}')
    print(f'  Total problems: {total}')
    print(f'  Entropy-weighted score: {entropy_total}/{total}')
    print(f'  Majority-vote score:    {majority_total}/{total}')
    print(f'  Delta: {majority_total - entropy_total:+d}')
    print()

    # Show problems that would FLIP
    fixes = [r for r in results if r['flip'] == 'FIX']
    regressions = [r for r in results if r['flip'] == 'REGRESSION']
    both_wrong = [r for r in results if r['flip'] == 'both_wrong']
    disagree_both_wrong = [r for r in results if r['flip'] == 'both_wrong' and r['entropy_pick'] != r['majority_pick']]

    if fixes:
        print(f'  === FIXES (majority would correct these): {len(fixes)} ===')
        for r in fixes:
            print(f'    {r["id"]}: expected={r["expected"]}')
            print(f'      Entropy picked: {r["entropy_pick"]} (WRONG)')
            print(f'      Majority picked: {r["majority_pick"]} (CORRECT)')
            # Show top 5 by votes
            sorted_votes = sorted(r['vote_dist'].items(), key=lambda x: -x[1])[:5]
            sorted_weights = sorted(r['weight_dist'].items(), key=lambda x: -x[1])[:5]
            print(f'      Top by votes:   {sorted_votes}')
            print(f'      Top by entropy: {sorted_weights}')
            print()

    if regressions:
        print(f'  === REGRESSIONS (majority would break these): {len(regressions)} ===')
        for r in regressions:
            print(f'    {r["id"]}: expected={r["expected"]}')
            print(f'      Entropy picked: {r["entropy_pick"]} (CORRECT)')
            print(f'      Majority picked: {r["majority_pick"]} (WRONG)')
            sorted_votes = sorted(r['vote_dist'].items(), key=lambda x: -x[1])[:5]
            sorted_weights = sorted(r['weight_dist'].items(), key=lambda x: -x[1])[:5]
            print(f'      Top by votes:   {sorted_votes}')
            print(f'      Top by entropy: {sorted_weights}')
            print()

    if disagree_both_wrong:
        print(f'  === DISAGREE BUT BOTH WRONG: {len(disagree_both_wrong)} ===')
        for r in disagree_both_wrong:
            print(f'    {r["id"]}: expected={r["expected"]}')
            print(f'      Entropy picked: {r["entropy_pick"]}')
            print(f'      Majority picked: {r["majority_pick"]}')
            sorted_votes = sorted(r['vote_dist'].items(), key=lambda x: -x[1])[:5]
            print(f'      Top by votes: {sorted_votes}')
            print()

    # Summary table
    print(f'  === FULL TABLE ===')
    print(f'  {"ID":<8} {"Expected":>8} {"Entropy":>8} {"Majority":>8} {"Flip":<15} {"TopVote":<20}')
    print(f'  {"---":<8} {"---":>8} {"---":>8} {"---":>8} {"---":<15} {"---":<20}')
    for r in results:
        top_vote = sorted(r['vote_dist'].items(), key=lambda x: -x[1])[:2] if r['vote_dist'] else []
        top_str = ', '.join(f'{a}x{v}' for a, v in top_vote)
        if len(top_str) > 18:
            top_str = top_str[:18] + '..'
        e_mark = 'OK' if r['entropy_correct'] else 'FAIL'
        m_mark = 'OK' if r['majority_correct'] else 'FAIL'
        print(f'  {r["id"]:<8} {str(r["expected"]):>8} {str(r["entropy_pick"]):>8} {str(r["majority_pick"]):>8} {r["flip"]:<15} {top_str:<20}')

    print(f'\n  Entropy: {entropy_total}/{total} | Majority: {majority_total}/{total} | Delta: {majority_total - entropy_total:+d}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'Usage: {sys.argv[0]} <diagnostic.log>')
        sys.exit(1)

    logfile = sys.argv[1]
    problems = parse_log(logfile)
    results = simulate_voting(problems)
    print_report(results)
