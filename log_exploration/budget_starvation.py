#!/usr/bin/env python3
"""Analyze budget starvation: which problems got starved by reruns eating time."""
import sys
import re
from collections import Counter
from log_exploration.log_query import parse_log


def analyze_starvation(logfile):
    problems = parse_log(logfile)

    # Extract all Wave 2 budgets and rerun markers in order
    budgets = []
    rerun_markers = []
    with open(logfile) as f:
        content = f.read()

    for m in re.finditer(r'Budget: ([\d.]+) seconds', content):
        budgets.append(float(m.group(1)))

    # Count reruns by looking at attempt counts
    rerun_count = sum(1 for p in problems if len(p.attempts) > 48)

    print(f'{"="*70}')
    print(f'  BUDGET STARVATION ANALYSIS — {logfile}')
    print(f'{"="*70}\n')

    # Budget distribution
    starved = sum(1 for b in budgets if b <= 30)
    tight = sum(1 for b in budgets if 30 < b < 150)
    ok = sum(1 for b in budgets if b >= 150)

    print(f'Total Wave 2 runs: {len(budgets)} ({len(problems)} problems + reruns)')
    print(f'Reruns triggered: {rerun_count}')
    print(f'')
    print(f'Budget distribution:')
    print(f'  Starved (<=30s):  {starved:>3} ({starved/len(budgets)*100:.0f}%)')
    print(f'  Tight (30-150s):  {tight:>3} ({tight/len(budgets)*100:.0f}%)')
    print(f'  OK (>=150s):      {ok:>3} ({ok/len(budgets)*100:.0f}%)')

    # Per-problem view with budget
    print(f'\n{"─"*70}')
    print(f'  PER-PROBLEM BUDGET vs OUTCOME')
    print(f'{"─"*70}')
    print(f'{"#":>3} {"Budget":>8} {"Att":>4} {"Nones":>6} {"None%":>6} {"Pred":>8} {"Exp":>8} {"OK":>4}')

    for i, (b, p) in enumerate(zip(budgets[:len(problems)], problems)):
        nones = sum(1 for a in p.attempts if a.answer is None)
        total = len(p.attempts)
        none_pct = nones / total * 100
        status = 'Y' if p.correct else 'N'
        marker = ' ***' if b <= 30 else ''
        print(f'{i+1:>3} {b:>7.0f}s {total:>4} {nones:>6} {none_pct:>5.0f}% {str(p.predicted):>8} {str(p.expected):>8} {status:>4}{marker}')

    # Starved problems: how did they do?
    print(f'\n{"─"*70}')
    print(f'  STARVED PROBLEMS (<=30s budget)')
    print(f'{"─"*70}')

    starved_problems = [(i, b, p) for i, (b, p) in enumerate(zip(budgets[:len(problems)], problems)) if b <= 30]
    starved_correct = sum(1 for _, _, p in starved_problems if p.correct)
    starved_total = len(starved_problems)

    if starved_problems:
        print(f'Score: {starved_correct}/{starved_total} ({starved_correct/starved_total*100:.0f}%)')
        print(f'')
        for i, b, p in starved_problems:
            nones = sum(1 for a in p.attempts if a.answer is None)
            status = 'OK' if p.correct else 'WRONG'
            print(f'  #{i+1} {p.problem_id} [{status}]: {b:.0f}s budget, {nones}/{len(p.attempts)} Nones, pred={p.predicted} exp={p.expected}')
    else:
        print('  No starved problems.')

    # Non-starved problems
    non_starved = [(i, b, p) for i, (b, p) in enumerate(zip(budgets[:len(problems)], problems)) if b > 30]
    ns_correct = sum(1 for _, _, p in non_starved if p.correct)
    ns_total = len(non_starved)

    print(f'\n{"─"*70}')
    print(f'  NON-STARVED vs STARVED COMPARISON')
    print(f'{"─"*70}')
    print(f'Non-starved (>30s): {ns_correct}/{ns_total} ({ns_correct/ns_total*100:.0f}%)')
    if starved_total:
        print(f'Starved (<=30s):    {starved_correct}/{starved_total} ({starved_correct/starved_total*100:.0f}%)')

    # None rates
    ns_nones = sum(1 for _, _, p in non_starved for a in p.attempts if a.answer is None)
    ns_attempts = sum(len(p.attempts) for _, _, p in non_starved)
    st_nones = sum(1 for _, _, p in starved_problems for a in p.attempts if a.answer is None)
    st_attempts = sum(len(p.attempts) for _, _, p in starved_problems)

    print(f'\nNone rates:')
    print(f'  Non-starved: {ns_nones}/{ns_attempts} ({ns_nones/max(ns_attempts,1)*100:.0f}%)')
    if st_attempts:
        print(f'  Starved:     {st_nones}/{st_attempts} ({st_nones/max(st_attempts,1)*100:.0f}%)')

    # Time stolen by reruns
    print(f'\n{"─"*70}')
    print(f'  RERUN TIME COST')
    print(f'{"─"*70}')
    rerun_problems = [p for p in problems if len(p.attempts) > 48]
    rerun_time = sum(p.wall_time for p in rerun_problems if p.wall_time)
    first_round_time = sum(min(p.wall_time, 500) for p in rerun_problems if p.wall_time)  # estimate R1 portion
    rerun_overhead = rerun_time - first_round_time
    print(f'Problems that reran: {len(rerun_problems)}')
    print(f'Total wall time for rerun problems: {rerun_time:.0f}s ({rerun_time/60:.0f} min)')
    print(f'Estimated rerun overhead: {rerun_overhead:.0f}s ({rerun_overhead/60:.0f} min)')

    # What-if: no reruns
    print(f'\n{"─"*70}')
    print(f'  WHAT-IF: NO RERUNS')
    print(f'{"─"*70}')
    correct_r1_only = 0
    for p in problems:
        r1 = p.attempts[:48]
        votes = Counter(a.answer for a in r1 if a.answer is not None)
        if votes:
            top_ans = votes.most_common(1)[0][0]
            if top_ans == p.expected:
                correct_r1_only += 1
    print(f'Score with R1 only (no reruns): {correct_r1_only}/50')
    print(f'Score with reruns (actual):     {sum(1 for p in problems if p.correct)}/50')
    print(f'Reruns gained: +{sum(1 for p in problems if p.correct) - correct_r1_only} problems')
    if starved_total:
        print(f'But starved {starved_total} problems to <=30s budget')

    print(f'\n{"="*70}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'Usage: python3 {sys.argv[0]} <logfile>')
        sys.exit(1)
    analyze_starvation(sys.argv[1])
