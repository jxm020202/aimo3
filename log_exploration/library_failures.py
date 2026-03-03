#!/usr/bin/env python3
"""
Library Failure Analysis for AIMO3 Solver
==========================================
Per-library error analysis: error counts, error types, failing functions,
and hallucinated API calls.

Usage:
    python3 log_exploration/library_failures.py <logfile>
    python3 log_exploration/library_failures.py <logfile> sympy
    python3 log_exploration/library_failures.py <logfile> math --top 30

Options:
    library     Optional: filter to show only errors for this library
    --top N     Number of top results (default: 20)
    --help      Show this help
"""

import sys
import os
import re
import argparse
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def print_section(title):
    print(f"\n{'=' * 72}")
    print(f"  {title}")
    print(f"{'=' * 72}")


def extract_imports(code):
    """Extract imported libraries from code."""
    imports = set()
    for line in code.split('\n'):
        line = line.strip()
        m = re.match(r'^import\s+(\w+)', line)
        if m:
            imports.add(m.group(1))
        m = re.match(r'^from\s+(\w+)', line)
        if m:
            imports.add(m.group(1))
    return imports


def extract_function_calls(code):
    """Extract module.function() calls."""
    calls = []
    for m in re.finditer(r'(\w+)\.(\w+)\s*\(', code):
        module = m.group(1)
        func = m.group(2)
        if module in ('np',):
            module = 'numpy'
        elif module in ('sp',):
            module = 'sympy'
        calls.append((module, func))
    return calls


def classify_error(output):
    """Classify error type from output text."""
    if not output:
        return "unknown"
    for pattern, etype in [
        (r'NameError', 'NameError'),
        (r'TypeError', 'TypeError'),
        (r'ValueError', 'ValueError'),
        (r'AttributeError', 'AttributeError'),
        (r'ImportError|ModuleNotFoundError', 'ImportError'),
        (r'IndexError', 'IndexError'),
        (r'KeyError', 'KeyError'),
        (r'ZeroDivisionError', 'ZeroDivisionError'),
        (r'OverflowError', 'OverflowError'),
        (r'RecursionError', 'RecursionError'),
        (r'MemoryError', 'MemoryError'),
        (r'TimeoutError|Timed? ?out', 'Timeout'),
        (r'SyntaxError', 'SyntaxError'),
        (r'RuntimeError', 'RuntimeError'),
    ]:
        if re.search(pattern, output, re.IGNORECASE):
            return etype
    return "other"


def analyze_errors_by_library(problems, library_filter, top_n):
    """For each library: error count, error types, failing functions."""
    print_section(f"ERROR ANALYSIS BY LIBRARY{' (' + library_filter + ')' if library_filter else ''}")

    lib_errors = defaultdict(lambda: {
        "error_count": 0,
        "total_uses": 0,
        "error_types": Counter(),
        "failing_functions": Counter(),
        "error_examples": [],
    })

    for p in problems:
        for a in p.attempts:
            for t in a.turns:
                if not t.code.strip():
                    continue
                libs = extract_imports(t.code)
                calls = extract_function_calls(t.code)

                for lib in libs:
                    if library_filter and lib != library_filter:
                        continue
                    lib_errors[lib]["total_uses"] += 1
                    if t.is_error:
                        lib_errors[lib]["error_count"] += 1
                        error_type = classify_error(t.output)
                        lib_errors[lib]["error_types"][error_type] += 1
                        if len(lib_errors[lib]["error_examples"]) < 3:
                            lib_errors[lib]["error_examples"].append({
                                "problem": p.problem_id,
                                "attempt": a.attempt_num,
                                "turn": t.turn_num,
                                "error_type": error_type,
                                "output_preview": t.output[:200] if t.output else "",
                            })

                # Track failing functions
                if t.is_error:
                    for module, func in calls:
                        if library_filter and module != library_filter:
                            continue
                        lib_errors[module]["failing_functions"][func] += 1

    # Sort by error count
    sorted_libs = sorted(lib_errors.items(), key=lambda x: -x[1]["error_count"])
    if not library_filter:
        sorted_libs = sorted_libs[:top_n]

    print(f"\n  {'Library':<20} {'Errors':>7} {'Total Uses':>11} {'Error Rate':>11}")
    print(f"  {'─' * 20} {'─' * 7} {'─' * 11} {'─' * 11}")
    for lib, data in sorted_libs:
        rate = 100 * data["error_count"] / data["total_uses"] if data["total_uses"] > 0 else 0
        print(f"  {lib:<20} {data['error_count']:>7} {data['total_uses']:>11} {rate:>10.1f}%")

    # Detailed per-library analysis
    for lib, data in sorted_libs:
        if data["error_count"] == 0:
            continue

        print(f"\n  --- {lib} ---")

        # Error types
        if data["error_types"]:
            print(f"  Error Types:")
            for etype, count in data["error_types"].most_common(10):
                print(f"    {etype}: {count}")

        # Failing functions
        if data["failing_functions"]:
            print(f"  Failing Functions:")
            for func, count in data["failing_functions"].most_common(10):
                print(f"    {lib}.{func}: {count} errors")

        # Examples
        if data["error_examples"]:
            print(f"  Error Examples:")
            for ex in data["error_examples"]:
                print(f"    Problem {ex['problem']} Att#{ex['attempt']} Turn#{ex['turn']} [{ex['error_type']}]")
                if ex["output_preview"]:
                    # Show just the error line
                    for line in ex["output_preview"].split('\n'):
                        if 'Error' in line or 'error' in line:
                            print(f"      {line.strip()[:100]}")
                            break


def analyze_hallucinated_apis(problems, library_filter, top_n):
    """Find hallucinated API calls (functions that might not exist)."""
    print_section("POTENTIAL HALLUCINATED API CALLS")

    # Known valid functions for common libraries
    known_functions = {
        'math': {'sqrt', 'floor', 'ceil', 'log', 'log2', 'log10', 'exp', 'pow', 'sin', 'cos', 'tan',
                 'gcd', 'lcm', 'factorial', 'comb', 'perm', 'isqrt', 'prod', 'fsum', 'inf', 'pi', 'e',
                 'copysign', 'fabs', 'fmod', 'frexp', 'ldexp', 'modf', 'trunc', 'isfinite', 'isinf', 'isnan',
                 'asin', 'acos', 'atan', 'atan2', 'sinh', 'cosh', 'tanh', 'degrees', 'radians',
                 'gamma', 'lgamma', 'erf', 'erfc'},
        'itertools': {'combinations', 'permutations', 'product', 'chain', 'count', 'cycle', 'repeat',
                      'accumulate', 'compress', 'dropwhile', 'takewhile', 'groupby', 'islice',
                      'starmap', 'zip_longest', 'combinations_with_replacement', 'filterfalse',
                      'tee', 'pairwise'},
        'functools': {'reduce', 'lru_cache', 'cache', 'partial', 'wraps', 'total_ordering', 'cmp_to_key'},
        'collections': {'Counter', 'defaultdict', 'OrderedDict', 'deque', 'namedtuple', 'ChainMap'},
    }

    suspect_calls = Counter()
    suspect_errors = defaultdict(list)

    for p in problems:
        for a in p.attempts:
            for t in a.turns:
                if not t.code.strip():
                    continue
                calls = extract_function_calls(t.code)
                for module, func in calls:
                    if library_filter and module != library_filter:
                        continue
                    if module in known_functions and func not in known_functions[module]:
                        key = f"{module}.{func}"
                        suspect_calls[key] += 1
                        if t.is_error and len(suspect_errors[key]) < 2:
                            suspect_errors[key].append({
                                "problem": p.problem_id,
                                "error": classify_error(t.output),
                            })

    if suspect_calls:
        print(f"\n  Functions NOT in known API (may be hallucinated):")
        print(f"  {'Function':<30} {'Count':>6} {'Caused Error?':>14}")
        print(f"  {'─' * 30} {'─' * 6} {'─' * 14}")
        for func, count in suspect_calls.most_common(top_n):
            errors = suspect_errors.get(func, [])
            err_str = f"Yes ({len(errors)}x)" if errors else "No"
            print(f"  {func:<30} {count:>6} {err_str:>14}")
    else:
        print(f"\n  No obvious hallucinated API calls detected.")

    print(f"\n  NOTE: This only checks against a limited known function list.")
    print(f"  sympy has thousands of functions and is NOT checked for hallucinations.")


def analyze_import_errors(problems, top_n):
    """Find ImportError / ModuleNotFoundError patterns."""
    print_section("IMPORT ERRORS")

    import_errors = Counter()

    for p in problems:
        for a in p.attempts:
            for t in a.turns:
                if t.is_error and t.output:
                    if 'ModuleNotFoundError' in t.output or 'ImportError' in t.output:
                        # Extract the module name
                        m = re.search(r"No module named '(\w+(?:\.\w+)*)'", t.output)
                        if m:
                            import_errors[m.group(1)] += 1
                        else:
                            m = re.search(r"cannot import name '(\w+)'", t.output)
                            if m:
                                import_errors[f"(name) {m.group(1)}"] += 1
                            else:
                                import_errors["(unknown)"] += 1

    if import_errors:
        print(f"\n  {'Module/Name':<30} {'Error Count':>12}")
        print(f"  {'─' * 30} {'─' * 12}")
        for mod, count in import_errors.most_common(top_n):
            print(f"  {mod:<30} {count:>12}")
    else:
        print(f"\n  No import errors found.")


def print_actionable_insights(problems):
    print_section("ACTIONABLE INSIGHTS")

    # Count error turns by library
    lib_error_counts = Counter()
    lib_total_counts = Counter()
    for p in problems:
        for a in p.attempts:
            for t in a.turns:
                if t.code.strip():
                    libs = extract_imports(t.code)
                    for lib in libs:
                        lib_total_counts[lib] += 1
                        if t.is_error:
                            lib_error_counts[lib] += 1

    worst_libs = []
    for lib, total in lib_total_counts.items():
        if total >= 10:
            rate = lib_error_counts.get(lib, 0) / total
            worst_libs.append((lib, rate, lib_error_counts.get(lib, 0), total))
    worst_libs.sort(key=lambda x: -x[1])

    print(f"""
  1. ERROR-PRONE LIBRARIES: {', '.join(f'{l[0]} ({100*l[1]:.0f}%)' for l in worst_libs[:5]) if worst_libs else 'None identified'}
     These libraries have the highest error rates when used.
     RECOMMENDATION: Add usage examples or constraints in the system prompt.

  2. HALLUCINATED APIS: The model sometimes calls functions that don't exist
     in standard library APIs. This is common with sympy (huge API surface).
     RECOMMENDATION: Consider adding a 'library cheat sheet' to the prompt
     with correct function names for commonly needed operations.

  3. IMPORT ERRORS: If the model tries to import unavailable libraries,
     add them to the available package list or add a prompt hint about
     which libraries are available in the execution environment.
""")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze library-specific errors in AIMO3 solver logs.",
        usage="python3 log_exploration/library_failures.py <logfile> [library] [options]"
    )
    parser.add_argument("logfile", help="Path to diagnostic.log")
    parser.add_argument("library", nargs="?", default=None, help="Optional: filter to specific library")
    parser.add_argument("--top", type=int, default=20, help="Number of top results (default: 20)")

    args = parser.parse_args()

    if not os.path.exists(args.logfile):
        print(f"Error: File not found: {args.logfile}")
        sys.exit(1)

    print(f"Parsing {args.logfile}...")
    problems = parse_log(args.logfile)
    print(f"Parsed {len(problems)} problems.")

    analyze_errors_by_library(problems, args.library, args.top)
    analyze_hallucinated_apis(problems, args.library, args.top)
    analyze_import_errors(problems, args.top)
    print_actionable_insights(problems)


if __name__ == "__main__":
    main()
