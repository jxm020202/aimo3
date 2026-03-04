#!/usr/bin/env python3
"""
Deep dive into the 'other' timeout category (46% of all timeouts).
What are these cells doing?
"""

import sys
import os
import re
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def classify_other(code):
    """More granular classification for 'other' category cells."""
    code_lower = code.lower()
    lines = code.strip().split('\n')

    # Function call that wraps long computation
    if re.search(r'^\w+\(', code.strip()) and len(lines) <= 3:
        return 'function_call_wrapper'

    # Just a print or expression
    if len(lines) <= 2 and ('print(' in code or re.match(r'^[\w\.\[\]]+$', code.strip())):
        return 'print_or_expression'

    # Single function definition
    if code.strip().startswith('def '):
        func_body = '\n'.join(lines[1:])
        if 'for ' in func_body:
            if func_body.count('for ') >= 2:
                return 'func_with_nested_loops'
            return 'func_with_single_loop'
        if 'while ' in func_body:
            return 'func_with_while'
        if re.search(r'\brecur|@lru_cache|@cache', code):
            return 'func_recursive'
        return 'func_other'

    # Class definition
    if code.strip().startswith('class '):
        return 'class_definition'

    # Assignment + computation
    if re.search(r'^\w+\s*=', code.strip()):
        if 'for ' in code:
            return 'assignment_with_loop'
        return 'assignment_computation'

    # Import + computation
    if code.strip().startswith(('import ', 'from ')):
        return 'import_then_compute'

    return 'truly_other'


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 timeout_other_category.py <diagnostic.log>")
        sys.exit(1)

    logfile = sys.argv[1]
    problems = parse_log(logfile)

    # Collect 'other' timeout cells (same logic as timeout_code_samples.py)
    other_cells = []
    for prob in problems:
        for att in prob.attempts:
            for turn in att.turns:
                if not (turn.is_error and 'timed out' in turn.output.lower()):
                    continue
                code = turn.code
                code_lower = code.lower()

                # Same exclusion logic
                is_classified = False
                if re.search(r'range\(\s*\d{5,}\)', code):
                    is_classified = True
                elif 'itertools.product' in code or 'itertools.permutations' in code or 'itertools.combinations' in code:
                    is_classified = True
                elif '.solve(' in code and ('sympy' in code_lower or 'sp.' in code_lower):
                    is_classified = True
                elif '.simplify(' in code and ('sympy' in code_lower or 'sp.' in code_lower):
                    is_classified = True
                elif '.expand(' in code and ('sympy' in code_lower or 'sp.' in code_lower):
                    is_classified = True
                elif '.integrate(' in code:
                    is_classified = True
                elif 'milp(' in code:
                    is_classified = True
                elif 'linprog(' in code:
                    is_classified = True
                elif re.search(r'while\s+True|while\s+1\b', code):
                    is_classified = True
                elif 'random.' in code_lower and ('for' in code_lower or 'while' in code_lower):
                    is_classified = True
                elif 'lru_cache' in code or '@cache' in code:
                    is_classified = True
                elif code.count('for ') >= 3:
                    is_classified = True
                elif code.count('for ') >= 2:
                    is_classified = True
                elif code.count('for ') >= 1:
                    is_classified = True

                if not is_classified:
                    other_cells.append({
                        'pid': prob.problem_id,
                        'att': att.attempt_num,
                        'turn': turn.turn_num,
                        'code': code,
                    })

    print(f"'Other' timeout cells (no loops, no itertools, no sympy/scipy): {len(other_cells)}\n")

    # Sub-classify
    sub_cats = Counter()
    sub_examples = defaultdict(list)
    for cell in other_cells:
        cat = classify_other(cell['code'])
        sub_cats[cat] += 1
        if len(sub_examples[cat]) < 3:
            sub_examples[cat].append(cell)

    print("=" * 80)
    print("SUB-CLASSIFICATION OF 'OTHER' TIMEOUTS")
    print("=" * 80)

    print(f"\n  {'Category':<30} {'Count':>8}")
    print(f"  {'─'*30} {'─'*8}")
    for cat, count in sub_cats.most_common():
        print(f"  {cat:<30} {count:>8}")

    # Show examples
    print("\n" + "=" * 80)
    print("EXAMPLES FROM EACH SUB-CATEGORY")
    print("=" * 80)

    for cat, cells in sorted(sub_examples.items()):
        print(f"\n  ── {cat} ({sub_cats[cat]} total) ──")
        for cell in cells:
            code_lines = cell['code'].split('\n')[:10]
            code_preview = '\n    '.join(code_lines)
            print(f"  [{cell['pid']} A{cell['att']} T{cell['turn']}]")
            print(f"    {code_preview}")
            print()

    # ── Now classify ALL timeout cells more precisely ──
    print("=" * 80)
    print("COMPLETE RE-CLASSIFICATION OF ALL TIMEOUT CELLS")
    print("=" * 80)

    all_cats = Counter()
    for prob in problems:
        for att in prob.attempts:
            for turn in att.turns:
                if not (turn.is_error and 'timed out' in turn.output.lower()):
                    continue
                code = turn.code
                code_lower = code.lower()
                lines = code.strip().split('\n')

                # Priority classification
                if re.search(r'range\(\s*\d{6,}\)', code):
                    all_cats['giant_range(1M+)'] += 1
                elif 'milp(' in code:
                    all_cats['scipy.milp'] += 1
                elif '.solve(' in code and ('sympy' in code_lower or 'sp.' in code_lower):
                    all_cats['sympy.solve'] += 1
                elif '.simplify(' in code and ('sympy' in code_lower or 'sp.' in code_lower):
                    all_cats['sympy.simplify'] += 1
                elif '.expand(' in code and ('sympy' in code_lower or 'sp.' in code_lower):
                    all_cats['sympy.expand'] += 1
                elif 'itertools.product' in code:
                    all_cats['itertools.product'] += 1
                elif 'itertools.permutations' in code or 'itertools.combinations' in code:
                    all_cats['itertools.comb/perm'] += 1
                elif 'random.' in code_lower and code.count('for ') >= 1:
                    all_cats['monte_carlo'] += 1
                elif code.count('for ') >= 3:
                    all_cats['3+ nested for-loops'] += 1
                elif code.count('for ') >= 2:
                    all_cats['2 nested for-loops'] += 1
                elif code.count('for ') >= 1:
                    # Check: is it a comprehension or a real loop?
                    if re.search(r'for\s+\w+\s+in\s+sp\.primerange|for\s+\w+\s+in\s+range', code):
                        all_cats['single loop (range/prime)'] += 1
                    else:
                        all_cats['single loop (other)'] += 1
                elif re.match(r'^\w+\(', code.strip()) and len(lines) <= 3:
                    all_cats['function_call_only'] += 1
                elif code.strip().startswith('def '):
                    all_cats['function_def_no_loop'] += 1
                else:
                    all_cats['misc'] += 1

    total = sum(all_cats.values())
    print(f"\n  Total: {total}\n")
    print(f"  {'Category':<30} {'Count':>8} {'%':>8}")
    print(f"  {'─'*30} {'─'*8} {'─'*8}")
    for cat, count in all_cats.most_common():
        print(f"  {cat:<30} {count:>8} {count/total*100:>7.1f}%")


if __name__ == '__main__':
    main()
