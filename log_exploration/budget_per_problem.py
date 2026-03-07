#!/usr/bin/env python3
"""Per-problem breakdown: Wave 1 budget, Wave 2 budget, timing, result."""
import sys
import re
from collections import Counter
from log_exploration.log_query import parse_log


def analyze_budgets(logfile):
    problems = parse_log(logfile)

    with open(logfile) as f:
        content = f.read()

    # Wave 1 budgets: "Budget: Xs | Attempts: 42"
    w1_budgets = [float(m.group(1)) for m in re.finditer(r'Budget: ([\d.]+)s \| Attempts: 42', content)]

    # Wave 2 budgets: "Budget: X seconds"
    w2_budgets = [float(m.group(1)) for m in re.finditer(r'Budget: ([\d.]+) seconds', content)]

    print(f'{"="*110}')
    print(f'  PER-PROBLEM BUDGET & RESULT — {logfile}')
    print(f'{"="*110}\n')

    print(f'{"#":>3} {"PID":<8} {"W1 Bud":>7} {"W1 Time":>8} {"W2 Bud":>7} {"W2 Time":>8} {"Rerun?":>7} {"Total":>7} {"Att":>4} {"None%":>6} {"Pred":>6} {"Exp":>6} {"OK":>3}')
    print(f'{"─"*3} {"─"*8} {"─"*7} {"─"*8} {"─"*7} {"─"*8} {"─"*7} {"─"*7} {"─"*4} {"─"*6} {"─"*6} {"─"*6} {"─"*3}')

    w2_idx = 0
    starved_correct = 0
    starved_total = 0
    ok_correct = 0
    ok_total = 0

    for i, p in enumerate(problems):
        w1_bud = w1_budgets[i] if i < len(w1_budgets) else 0
        w1_time = p.wave1_time / 42 if p.wave1_time else 0

        w2_bud = w2_budgets[w2_idx] if w2_idx < len(w2_budgets) else 0
        w2_idx += 1

        reran = len(p.attempts) > 48
        if reran and w2_idx < len(w2_budgets):
            w2_idx += 1

        nones = sum(1 for a in p.attempts if a.answer is None)
        total = len(p.attempts)
        none_pct = nones / total * 100
        wall = p.wall_time or 0
        status = 'Y' if p.correct else 'N'
        rerun_str = 'YES' if reran else ''

        is_starved = w2_bud <= 30
        marker = ' ***' if is_starved else ''

        if is_starved:
            starved_total += 1
            starved_correct += int(p.correct)
        else:
            ok_total += 1
            ok_correct += int(p.correct)

        print(f'{i+1:>3} {p.problem_id:<8} {w1_bud:>6.0f}s {w1_time:>7.0f}s {w2_bud:>6.0f}s {wall:>7.0f}s {rerun_str:>7} {wall:>6.0f}s {total:>4} {none_pct:>5.0f}% {str(p.predicted):>6} {str(p.expected):>6} {status:>3}{marker}')

    total_correct = sum(1 for p in problems if p.correct)
    total_nones = sum(1 for p in problems for a in p.attempts if a.answer is None)
    total_attempts = sum(len(p.attempts) for p in problems)
    total_wall = sum(p.wall_time for p in problems if p.wall_time)

    print(f'\n{"─"*110}')
    print(f'Score: {total_correct}/50 | Nones: {total_nones}/{total_attempts} ({total_nones/total_attempts*100:.0f}%) | Total time: {total_wall/60:.0f} min')
    print(f'')
    print(f'Non-starved (>30s budget): {ok_correct}/{ok_total} ({ok_correct/max(ok_total,1)*100:.0f}%)')
    print(f'Starved (<=30s budget):    {starved_correct}/{starved_total} ({starved_correct/max(starved_total,1)*100:.0f}%)')
    print(f'{"="*110}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'Usage: python3 {sys.argv[0]} <logfile>')
        sys.exit(1)
    analyze_budgets(sys.argv[1])
