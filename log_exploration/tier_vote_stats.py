#!/usr/bin/env python3
"""
Tier-wise voting stats: correct, wrong, unique correct, outvoted.

Usage:
    python3 log_exploration/tier_vote_stats.py <diagnostic.log>
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log_exploration.log_query import parse_log
from collections import Counter


def analyze(logfile):
    problems = parse_log(logfile)

    # Deduplicate
    seen = set()
    unique = []
    for p in problems:
        if p.problem_id not in seen:
            seen.add(p.problem_id)
            unique.append(p)
    problems = unique

    # Group by tier
    tiers = {}
    for p in problems:
        batch = getattr(p, 'batch_name', '') or 'Unlabeled (Tier 0)'
        tiers.setdefault(batch, []).append(p)

    # Also make a combined <2 group
    hard_problems = []
    easy_problems = []
    for p in problems:
        batch = getattr(p, 'batch_name', '') or ''
        if 'TIER 2' in batch or 'VAL BENCH' in batch:
            easy_problems.append(p)
        else:
            hard_problems.append(p)

    all_groups = list(tiers.items())
    all_groups.append(('--- COMBINED: Tier <2 (Hard) ---', hard_problems))
    all_groups.append(('--- COMBINED: Tier 2 (Easy) ---', easy_problems))
    all_groups.append(('--- ALL ---', problems))

    print(f"{'='*100}")
    print(f"  TIER-WISE VOTING STATS")
    print(f"{'='*100}")

    for tier_name, tier_problems in all_groups:
        print(f"\n  {'─'*96}")
        print(f"  {tier_name} ({len(tier_problems)} problems)")
        print(f"  {'─'*96}")

        correct_count = 0
        wrong_count = 0
        outvoted = []  # correct answer existed but lost vote
        unanimous_wrong = []
        no_correct_in_votes = []

        # Per-temperature stats
        temp_stats = {}  # temp -> {correct, wrong, none, total}

        for p in tier_problems:
            votes = Counter()
            none_count = 0
            per_temp = {}

            for a in p.attempts:
                temp = getattr(a, 'temperature', None)
                if temp not in per_temp:
                    per_temp[temp] = {'correct': 0, 'wrong': 0, 'none': 0, 'total': 0}
                per_temp[temp]['total'] += 1

                if a.answer is not None:
                    votes[a.answer] += 1
                    if a.answer == p.expected:
                        per_temp[temp]['correct'] += 1
                    else:
                        per_temp[temp]['wrong'] += 1
                else:
                    none_count += 1
                    per_temp[temp]['none'] += 1

            for temp, stats in per_temp.items():
                if temp not in temp_stats:
                    temp_stats[temp] = {'correct': 0, 'wrong': 0, 'none': 0, 'total': 0}
                for k in ['correct', 'wrong', 'none', 'total']:
                    temp_stats[temp][k] += stats[k]

            if not votes:
                wrong_count += 1
                no_correct_in_votes.append(p)
                continue

            winner, top_count = votes.most_common(1)[0]
            total_answered = sum(votes.values())
            unique_answers = len(votes)
            correct_votes = votes.get(p.expected, 0)
            has_correct = p.expected in votes

            if winner == p.expected:
                correct_count += 1
            else:
                wrong_count += 1
                if has_correct:
                    outvoted.append({
                        'id': p.problem_id,
                        'expected': p.expected,
                        'predicted': winner,
                        'top_votes': top_count,
                        'correct_votes': correct_votes,
                        'unique': unique_answers,
                        'nones': none_count,
                        'total': len(p.attempts),
                        'votes': dict(votes.most_common(5)),
                    })
                else:
                    no_correct_in_votes.append(p)
                    if unique_answers == 1:
                        unanimous_wrong.append({
                            'id': p.problem_id,
                            'expected': p.expected,
                            'predicted': winner,
                            'top_votes': top_count,
                            'nones': none_count,
                        })

        print(f"  Correct: {correct_count}/{len(tier_problems)} ({correct_count/len(tier_problems)*100:.1f}%)")
        print(f"  Wrong:   {wrong_count}/{len(tier_problems)}")
        print(f"    - Outvoted (correct in votes but lost):    {len(outvoted)}")
        print(f"    - No correct in any vote:                  {len(no_correct_in_votes)}")
        print(f"    - Unanimous wrong (all same wrong answer): {len(unanimous_wrong)}")

        # Per-temp breakdown
        if temp_stats:
            print(f"\n  Per-temperature attempt stats:")
            print(f"  {'Temp':>6} {'Total':>7} {'Correct':>8} {'Wrong':>7} {'None':>6} {'Acc%':>7} {'None%':>7}")
            for temp in sorted(temp_stats.keys(), key=lambda x: x if x is not None else -1):
                s = temp_stats[temp]
                acc = s['correct'] / s['total'] * 100 if s['total'] > 0 else 0
                none_pct = s['none'] / s['total'] * 100 if s['total'] > 0 else 0
                print(f"  {temp if temp is not None else '?':>6} {s['total']:>7} {s['correct']:>8} {s['wrong']:>7} "
                      f"{s['none']:>6} {acc:>6.1f}% {none_pct:>6.1f}%")

        # Unique correct per temp
        print(f"\n  Unique correct per temperature (problems solved by ONLY that temp):")
        temp_solved = {}  # temp -> set of problem_ids solved
        for p in tier_problems:
            for a in p.attempts:
                temp = getattr(a, 'temperature', None)
                if a.answer == p.expected:
                    temp_solved.setdefault(temp, set()).add(p.problem_id)

        all_temps = sorted(temp_solved.keys(), key=lambda x: x if x is not None else -1)
        for temp in all_temps:
            solved_by_this = temp_solved[temp]
            solved_by_others = set()
            for other_temp in all_temps:
                if other_temp != temp:
                    solved_by_others |= temp_solved.get(other_temp, set())
            unique_only = solved_by_this - solved_by_others
            print(f"  Temp {temp}: {len(solved_by_this)} problems solved, "
                  f"{len(unique_only)} unique → {', '.join(sorted(unique_only)) if unique_only else '(none)'}")

        # Outvoted details
        if outvoted:
            print(f"\n  Outvoted problems (correct answer existed but lost):")
            print(f"  {'ID':<10} {'Exp':>7} {'Pred':>7} {'TopV':>5} {'CorrV':>6} {'Uniq':>5} {'None':>5} {'Top Votes'}")
            for o in sorted(outvoted, key=lambda x: x['correct_votes'], reverse=True):
                top_str = str(o['votes'])
                if len(top_str) > 35:
                    top_str = top_str[:35] + '..'
                print(f"  {o['id']:<10} {o['expected']:>7} {o['predicted']:>7} {o['top_votes']:>5} "
                      f"{o['correct_votes']:>6} {o['unique']:>5} {o['nones']:>5} {top_str}")

        # Unanimous wrong details
        if unanimous_wrong:
            print(f"\n  Unanimous wrong (all non-None attempts give same wrong answer):")
            for u in unanimous_wrong:
                print(f"  {u['id']}: all say {u['predicted']} ({u['top_votes']} votes, {u['nones']} Nones), expected {u['expected']}")

        # No correct details
        if no_correct_in_votes and not unanimous_wrong:
            pass  # already covered above
        elif no_correct_in_votes:
            non_unanimous = [p for p in no_correct_in_votes if p not in [x for x in tier_problems if hasattr(p, '_unanimous')]]
            # Just list them
            scattered = []
            for p in no_correct_in_votes:
                votes = Counter()
                for a in p.attempts:
                    if a.answer is not None:
                        votes[a.answer] += 1
                if len(votes) > 1:
                    scattered.append((p.problem_id, p.expected, dict(votes.most_common(5))))
            if scattered:
                print(f"\n  Scattered wrong (multiple wrong answers, no correct):")
                for pid, exp, v in scattered:
                    print(f"  {pid}: expected {exp}, votes={v}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <diagnostic.log>")
        sys.exit(1)

    analyze(sys.argv[1])
