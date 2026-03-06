#!/usr/bin/env python3
"""Analyze NameError impact: which names cause errors, which affect wrong problems,
and what the score impact would be if we added them to init.

Usage: python3 log_exploration/nameerror_impact.py <diagnostic.log>
"""
import sys, re
from collections import Counter
sys.path.insert(0, '.')
from log_exploration.log_query import parse_log


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <diagnostic.log>")
        sys.exit(1)

    problems = parse_log(sys.argv[1])

    # Collect all NameErrors
    name_errors = Counter()
    name_by_problem = {}  # name -> {pid: count}
    for p in problems:
        for a in p.attempts:
            for t in a.turns:
                if t.is_error and t.output and 'NameError' in t.output:
                    m = re.search(r"name '(\w+)' is not defined", t.output)
                    if m:
                        name = m.group(1)
                        name_errors[name] += 1
                        name_by_problem.setdefault(name, Counter())[p.problem_id] += 1

    total_ne = sum(name_errors.values())
    print(f"{'='*72}")
    print(f"  NAMEERROR IMPACT ANALYSIS")
    print(f"{'='*72}")
    print(f"  Total NameErrors: {total_ne}")
    print(f"  Distinct names: {len(name_errors)}")

    # Categorize: stdlib import vs variable undefined
    import_fixes = {
        'Fraction': 'from fractions import Fraction',
        'deque': 'from collections import deque',
        'defaultdict': 'from collections import defaultdict',
        'Counter': 'from collections import Counter',
        'combinations': 'from itertools import combinations',
        'permutations': 'from itertools import permutations',
        'product': 'from itertools import product',
        'chain': 'from itertools import chain',
        'gcd': 'from math import gcd',
        'lcm': 'from math import lcm',
        'ceil': 'from math import ceil',
        'floor': 'from math import floor',
        'log': 'from math import log',
        'sqrt': 'from math import sqrt',
        'reduce': 'from functools import reduce',
        'lru_cache': 'from functools import lru_cache',
        'cache': 'from functools import cache',
        'deepcopy': 'from copy import deepcopy',
    }

    # v36 fixed aliases
    v36_fixed = {'np', 'sp', 'random', 'time', 'nx'}

    print(f"\n  {'─'*72}")
    print(f"  TOP 20 NAMEERRORS + FIX CLASSIFICATION")
    print(f"  {'─'*72}")
    print(f"  {'Name':30s} {'Count':>6s} {'Fix':40s} {'Wrong probs'}")
    print(f"  {'─'*30} {'─'*6} {'─'*40} {'─'*20}")

    wrong_pids = {p.problem_id for p in problems if not p.correct}

    for name, count in name_errors.most_common(20):
        if name in v36_fixed:
            fix = f"FIXED in v36 (alias)"
        elif name in import_fixes:
            fix = import_fixes[name]
        else:
            fix = "variable_undefined (code bug)"

        # Which wrong problems are affected?
        affected_wrong = []
        for pid, cnt in name_by_problem[name].items():
            if pid in wrong_pids:
                affected_wrong.append(f"{pid}({cnt})")

        wrong_str = ', '.join(affected_wrong) if affected_wrong else '-'
        print(f"  {name:30s} {count:6d} {fix:40s} {wrong_str}")

    # Fixable summary
    print(f"\n  {'─'*72}")
    print(f"  FIXABLE BY ADDING TO INIT")
    print(f"  {'─'*72}")
    fixable_count = 0
    for name, count in name_errors.most_common():
        if name in import_fixes:
            fixable_count += count
            affected_wrong = [(pid, cnt) for pid, cnt in name_by_problem[name].items() if pid in wrong_pids]
            if affected_wrong:
                print(f"  {name:20s}: {count:4d} errors, affects wrong: {', '.join(f'{p}({c})' for p, c in affected_wrong)}")
                print(f"    Fix: {import_fixes[name]}")

    print(f"\n  Fixable NameErrors: {fixable_count}/{total_ne} ({fixable_count*100/total_ne:.0f}%)")
    print(f"  Remaining: {total_ne - fixable_count} (model code bugs, not fixable by init)")


if __name__ == '__main__':
    main()
