#!/usr/bin/env python3
"""Analyze code errors from diagnostic.log — what types, when, and why."""

import re
import json
from collections import defaultdict, Counter

LOG_PATH = "output/v21/diagnostic.log"


def extract_errors(path):
    with open(path, 'r') as f:
        lines = f.readlines()

    errors = []
    current_problem = None
    current_attempt = None
    current_tier = None

    for i, line in enumerate(lines):
        # Track tier
        tier_m = re.search(r'(REFERENCE PROBLEMS|FIXED \d+ DIAGNOSTIC|RANDOM \d+|COMPREHENSIVE BENCHMARK)', line)
        if tier_m:
            current_tier = tier_m.group(1).strip()

        # Track problem
        prob_m = re.search(r'Problem id=(\w+)', line)
        if prob_m:
            current_problem = prob_m.group(1)

        # Track attempt
        att_m = re.search(r'ATTEMPT\s+(\d+)\s+\|', line)
        if att_m:
            current_attempt = int(att_m.group(1))

        # Find Traceback lines (the error type header)
        if 'Traceback (most recent call last)' in line:
            # Look ahead for the actual error message (usually 1-20 lines after)
            error_type = None
            error_msg = None
            error_line_num = i

            for j in range(i + 1, min(i + 30, len(lines))):
                err_m = re.match(
                    r'\s*>\s*(NameError|TypeError|ValueError|SyntaxError|ImportError|'
                    r'ModuleNotFoundError|ZeroDivisionError|OverflowError|MemoryError|'
                    r'RecursionError|KeyboardInterrupt|TimeoutError|AttributeError|'
                    r'KeyError|IndexError|StopIteration|RuntimeError|FileNotFoundError|'
                    r'OSError|AssertionError|NotImplementedError|UnboundLocalError):\s*(.*)',
                    lines[j]
                )
                if err_m:
                    error_type = err_m.group(1)
                    error_msg = err_m.group(2).strip()
                    break
                # Also check for bare error type without > prefix
                err_m2 = re.match(
                    r'\s*(NameError|TypeError|ValueError|SyntaxError|ImportError|'
                    r'ModuleNotFoundError|ZeroDivisionError|OverflowError|MemoryError|'
                    r'RecursionError|KeyboardInterrupt|TimeoutError|AttributeError|'
                    r'KeyError|IndexError|StopIteration|RuntimeError):\s*(.*)',
                    lines[j]
                )
                if err_m2:
                    error_type = err_m2.group(1)
                    error_msg = err_m2.group(2).strip()
                    break

            if error_type:
                # Get 2 lines of context before traceback for the code
                context_before = []
                for k in range(max(0, i - 5), i):
                    if lines[k].strip() and '|' in lines[k]:
                        context_before.append(lines[k].rstrip())

                errors.append({
                    'line': i + 1,
                    'problem_id': current_problem,
                    'attempt': current_attempt,
                    'tier': current_tier,
                    'error_type': error_type,
                    'error_msg': error_msg,
                    'full_msg': f"{error_type}: {error_msg}",
                })

    return errors


def categorize_error(err):
    """Assign a root cause category to each error."""
    t = err['error_type']
    m = err['error_msg']

    # NameError subcategories
    if t == 'NameError':
        if 'is not defined' in m:
            # Check if it's referencing a function from a previous cell
            return 'cross-cell-reference', 'Model defined function in earlier code cell, references it in new cell (sandbox resets between cells)'
        return 'undefined-variable', 'Variable/function used before definition'

    # TypeError subcategories
    if t == 'TypeError':
        if "unsupported operand type(s) for ** or pow(): 'int', 'Zero', 'int'" in m:
            return 'sympy-int-mix', "Model passes sympy Integer('Zero') to Python's pow(base,exp,mod) — sympy objects don't work with 3-arg pow"
        if "'simple' is an invalid keyword argument" in m or "'a' is an invalid keyword argument" in m:
            return 'hallucinated-api', 'Model hallucinates function keyword arguments that do not exist'
        if "'NoneType'" in m:
            return 'none-propagation', 'Function returned None unexpectedly, model used result in arithmetic'
        if "unsupported operand type" in m:
            return 'type-mismatch', 'Arithmetic on incompatible types (e.g., float and NoneType)'
        return 'type-error-other', m[:80]

    # ValueError subcategories
    if t == 'ValueError':
        if 'integer string conversion' in m or '4300 digits' in m:
            return 'bigint-str-limit', 'Python 3.11+ limits int→str conversion to 4300 digits; model tries to print huge numbers'
        return 'value-error-other', m[:80]

    # ImportError
    if t in ('ImportError', 'ModuleNotFoundError'):
        if 'crt' in m:
            return 'wrong-import-path', "Model imports sympy.ntheory.modular.crt as 'from sympy import crt' — wrong import path"
        if 'valuation' in m:
            return 'wrong-import-path', "Model imports non-existent 'valuation' from sympy"
        return 'missing-module', m[:80]

    # OverflowError
    if t == 'OverflowError':
        if 'int too large to convert to float' in m:
            return 'bigint-float-overflow', 'Model converts huge integer to float, exceeds float64 range'
        return 'overflow-other', m[:80]

    # AttributeError
    if t == 'AttributeError':
        return 'wrong-attribute', 'Model calls method/attribute that does not exist on the object'

    # KeyError
    if t == 'KeyError':
        return 'key-error', 'Dictionary key does not exist'

    # IndexError
    if t == 'IndexError':
        return 'index-error', 'List index out of range'

    # TimeoutError / KeyboardInterrupt
    if t in ('TimeoutError', 'KeyboardInterrupt'):
        return 'timeout', 'Code execution exceeded time limit'

    # RecursionError
    if t == 'RecursionError':
        return 'recursion-limit', 'Infinite recursion or stack overflow'

    return 'other', f'{t}: {m[:80]}'


def main():
    errors = extract_errors(LOG_PATH)
    print(f"Total errors with tracebacks found: {len(errors)}\n")

    # Categorize
    for err in errors:
        cat, desc = categorize_error(err)
        err['category'] = cat
        err['category_desc'] = desc

    # ===== ERROR TYPE DISTRIBUTION =====
    print("=" * 100)
    print("  ERROR TYPE DISTRIBUTION")
    print("=" * 100)

    type_counts = Counter(e['error_type'] for e in errors)
    for t, c in type_counts.most_common():
        pct = 100 * c / len(errors)
        print(f"  {t:<25} {c:>4} ({pct:>5.1f}%)")

    # ===== ROOT CAUSE CATEGORIES =====
    print("\n" + "=" * 100)
    print("  ROOT CAUSE CATEGORIES")
    print("=" * 100)

    cat_counts = Counter(e['category'] for e in errors)
    for cat, c in cat_counts.most_common():
        pct = 100 * c / len(errors)
        desc = next(e['category_desc'] for e in errors if e['category'] == cat)
        print(f"\n  [{c:>3}x] ({pct:>5.1f}%) {cat}")
        print(f"         {desc}")

        # Show example error messages (deduplicated)
        msgs = set()
        for e in errors:
            if e['category'] == cat:
                msgs.add(e['error_msg'][:120])
        for msg in list(msgs)[:3]:
            print(f"         Example: {msg}")

    # ===== ERRORS BY PROBLEM =====
    print("\n\n" + "=" * 100)
    print("  ERRORS BY PROBLEM (problems with errors)")
    print("=" * 100)

    by_problem = defaultdict(list)
    for e in errors:
        by_problem[e['problem_id']].append(e)

    for pid, errs in sorted(by_problem.items(), key=lambda x: len(x[1]), reverse=True):
        cats = Counter(e['category'] for e in errs)
        tier = errs[0]['tier']
        print(f"\n  {pid} ({tier}) — {len(errs)} errors")
        for cat, c in cats.most_common():
            print(f"    {cat}: {c}x")

    # ===== WHEN DO ERRORS HAPPEN? (attempt distribution) =====
    print("\n\n" + "=" * 100)
    print("  WHEN DO ERRORS HAPPEN? (by attempt number)")
    print("=" * 100)

    by_attempt = Counter(e['attempt'] for e in errors if e['attempt'])
    for att in sorted(by_attempt.keys()):
        bar = "█" * by_attempt[att]
        print(f"  Attempt {att}: {by_attempt[att]:>3} errors  {bar}")

    # ===== ERRORS BY TIER =====
    print("\n\n" + "=" * 100)
    print("  ERRORS BY TIER")
    print("=" * 100)

    by_tier = defaultdict(list)
    for e in errors:
        by_tier[e['tier'] or 'Unknown'].append(e)

    for tier, errs in by_tier.items():
        cats = Counter(e['category'] for e in errs)
        print(f"\n  {tier}: {len(errs)} errors")
        for cat, c in cats.most_common(5):
            print(f"    {cat}: {c}x")

    # ===== REPEATED ERRORS (same error in multiple attempts of same problem) =====
    print("\n\n" + "=" * 100)
    print("  REPEATED ERRORS (same root cause across attempts of same problem)")
    print("=" * 100)
    print("  These indicate the model keeps hitting the same wall and not learning from feedback.")

    for pid, errs in sorted(by_problem.items(), key=lambda x: len(x[1]), reverse=True):
        if len(errs) < 3:
            continue
        # Group by category
        cat_attempts = defaultdict(list)
        for e in errs:
            cat_attempts[e['category']].append(e['attempt'])

        for cat, atts in cat_attempts.items():
            if len(atts) >= 2:
                print(f"  {pid}: '{cat}' in attempts {atts}")

    # ===== THE BIG PICTURE =====
    print("\n\n" + "=" * 100)
    print("  THE BIG PICTURE — WHY ERRORS HAPPEN")
    print("=" * 100)

    print(f"""
  Total errors: {len(errors)} across {len(by_problem)} problems

  TOP ROOT CAUSES:
""")

    # Group into meta-categories
    meta = {
        'Sandbox isolation (cross-cell state loss)': ['cross-cell-reference', 'undefined-variable'],
        'Sympy/Python type mixing': ['sympy-int-mix', 'type-mismatch', 'none-propagation', 'type-error-other'],
        'Large number handling': ['bigint-str-limit', 'bigint-float-overflow', 'overflow-other'],
        'Hallucinated APIs': ['hallucinated-api', 'wrong-import-path', 'wrong-attribute', 'missing-module'],
        'Timeout / compute limits': ['timeout', 'recursion-limit'],
        'Logic errors': ['key-error', 'index-error', 'value-error-other'],
        'Other': ['other'],
    }

    for meta_name, cats in meta.items():
        count = sum(cat_counts.get(c, 0) for c in cats)
        if count > 0:
            pct = 100 * count / len(errors)
            print(f"  {count:>3} ({pct:>5.1f}%)  {meta_name}")
            for c in cats:
                if cat_counts.get(c, 0) > 0:
                    print(f"              └─ {c}: {cat_counts[c]}x")

    # Save
    output = {
        'total_errors': len(errors),
        'problems_with_errors': len(by_problem),
        'type_distribution': dict(type_counts),
        'category_distribution': dict(cat_counts),
        'by_problem': {pid: len(errs) for pid, errs in by_problem.items()},
        'by_attempt': dict(by_attempt),
        'errors': [
            {k: v for k, v in e.items()}
            for e in errors
        ]
    }

    with open("diagnostics/v21/error_analysis.json", 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n\n  Saved to diagnostics/v21/error_analysis.json")


if __name__ == '__main__':
    main()
