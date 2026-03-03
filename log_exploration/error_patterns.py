#!/usr/bin/env python3
"""
Error Patterns — Root Cause Analysis
======================================
For each error type, extract the actual offending code and root cause.
Groups errors by ROOT CAUSE, not just Python exception type.

Usage: python3 log_exploration/error_patterns.py output/v22/diagnostic.log
"""

import sys
import os
import re
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def extract_error_detail(output):
    """Extract detailed error info from traceback output."""
    lines = output.strip().split('\n')

    # Find the actual error line (usually last non-empty line or line with Error)
    error_line = ''
    traceback_code = ''

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Look for the final error message
        if re.match(r'^(NameError|TypeError|ValueError|IndexError|KeyError|AttributeError|'
                     r'ZeroDivisionError|OverflowError|MemoryError|RecursionError|'
                     r'SyntaxError|ImportError|ModuleNotFoundError|RuntimeError|'
                     r'StopIteration|AssertionError|TimeoutError):', stripped):
            error_line = stripped
        # Also capture the offending code line (line above "^" marker or after "-->")
        if stripped.startswith('----> ') or stripped.startswith('--->'):
            traceback_code = stripped.lstrip('--> ').strip()
        # Lines with just code in traceback frames
        if i > 0 and lines[i-1].strip().startswith('File '):
            traceback_code = stripped

    # Fallback: last line often IS the error
    if not error_line:
        for line in reversed(lines):
            s = line.strip()
            if s and not s.startswith('File ') and not s.startswith('Traceback'):
                error_line = s
                break

    return error_line, traceback_code


def classify_root_cause(error_type, error_line, code, output):
    """Classify the root cause beyond just Python error type."""
    el = error_line.lower()
    code_lower = code.lower() if code else ''
    output_lower = output.lower()

    # NameError subcategories
    if error_type == 'NameError':
        # Extract what name was undefined
        name_match = re.search(r"name '(\w+)' is not defined", error_line)
        var_name = name_match.group(1) if name_match else '?'

        if re.search(r'(sympy|sp\.|Symbol|solve|Eq|simplify|expand)', code):
            return f'NameError:sympy_not_imported ({var_name})'
        if re.search(r'(numpy|np\.)', code):
            return f'NameError:numpy_not_imported ({var_name})'
        if re.search(r'(itertools|combinations|permutations)', code):
            return f'NameError:itertools_not_imported ({var_name})'
        if var_name[0].isupper():
            return f'NameError:class_or_func_undefined ({var_name})'
        return f'NameError:variable_undefined ({var_name})'

    # TypeError subcategories
    if error_type == 'TypeError':
        if 'unsupported operand' in el:
            return 'TypeError:arithmetic_type_mismatch'
        if 'not subscriptable' in el:
            return 'TypeError:not_subscriptable'
        if 'not iterable' in el:
            return 'TypeError:not_iterable'
        if 'not callable' in el:
            return 'TypeError:not_callable'
        if 'argument' in el and ('expected' in el or 'got' in el or 'takes' in el):
            return 'TypeError:wrong_argument_count'
        if 'cannot' in el and 'int' in el:
            return 'TypeError:sympy_to_python_conversion'
        if 'comparison' in el or 'not supported between' in el:
            return 'TypeError:comparison_type_mismatch'
        return f'TypeError:other'

    # ValueError subcategories
    if error_type == 'ValueError':
        if 'too many values to unpack' in el or 'not enough values' in el:
            return 'ValueError:unpacking_mismatch'
        if 'math domain' in el:
            return 'ValueError:math_domain_error'
        if 'invalid literal' in el:
            return 'ValueError:invalid_literal'
        if 'base' in el or 'radix' in el:
            return 'ValueError:base_conversion'
        return 'ValueError:constraint_violation'

    # Timeout
    if error_type == 'Timeout':
        if 'recursion' in output_lower or 'recursive' in code_lower:
            return 'Timeout:infinite_recursion'
        if 'while' in code_lower:
            return 'Timeout:infinite_loop'
        if any(w in code_lower for w in ['combinations', 'permutations', 'product', 'itertools']):
            return 'Timeout:combinatorial_explosion'
        if 'sympy' in code_lower or 'solve' in code_lower:
            return 'Timeout:symbolic_computation'
        return 'Timeout:computation_too_slow'

    # ImportError
    if error_type == 'ImportError':
        mod_match = re.search(r"No module named '(\w+)'", error_line)
        mod = mod_match.group(1) if mod_match else '?'
        return f'ImportError:module_not_available ({mod})'

    # AttributeError
    if error_type == 'AttributeError':
        attr_match = re.search(r"'(\w+)' object has no attribute '(\w+)'", error_line)
        if attr_match:
            obj_type = attr_match.group(1)
            attr_name = attr_match.group(2)
            return f'AttributeError:{obj_type}.{attr_name}'
        return 'AttributeError:wrong_method_or_property'

    # IndexError
    if error_type == 'IndexError':
        return 'IndexError:out_of_range'

    # ZeroDivisionError
    if error_type == 'ZeroDivisionError':
        if 'modulo' in el or '%' in code:
            return 'ZeroDivisionError:modulo_by_zero'
        return 'ZeroDivisionError:division_by_zero'

    # SyntaxError
    if error_type == 'SyntaxError':
        if 'unexpected EOF' in el or 'incomplete' in el:
            return 'SyntaxError:incomplete_code'
        if 'invalid syntax' in el:
            return 'SyntaxError:invalid_syntax'
        return 'SyntaxError:other'

    # OverflowError
    if error_type == 'OverflowError':
        return 'OverflowError:number_too_large'

    # MemoryError
    if error_type == 'MemoryError':
        return 'MemoryError:out_of_memory'

    # RecursionError
    if error_type == 'RecursionError':
        return 'RecursionError:max_depth_exceeded'

    return f'{error_type}:unclassified'


def classify_error_type(output):
    """Get the base Python error type from output."""
    patterns = [
        (r'NameError', 'NameError'),
        (r'TypeError', 'TypeError'),
        (r'ValueError', 'ValueError'),
        (r'IndexError', 'IndexError'),
        (r'KeyError', 'KeyError'),
        (r'AttributeError', 'AttributeError'),
        (r'ZeroDivisionError', 'ZeroDivisionError'),
        (r'OverflowError', 'OverflowError'),
        (r'MemoryError', 'MemoryError'),
        (r'RecursionError', 'RecursionError'),
        (r'TimeoutError|timed?\s*out|execution.*time', 'Timeout'),
        (r'SyntaxError', 'SyntaxError'),
        (r'ImportError|ModuleNotFoundError', 'ImportError'),
        (r'RuntimeError', 'RuntimeError'),
        (r'StopIteration', 'StopIteration'),
        (r'AssertionError', 'AssertionError'),
    ]
    for pat, label in patterns:
        if re.search(pat, output, re.IGNORECASE):
            return label
    return 'Other'


def analyze_error_patterns(problems):
    """Deep root cause analysis of every error."""
    print("=" * 90)
    print("ERROR ROOT CAUSE ANALYSIS")
    print("=" * 90)

    # Collect all errors with full context
    errors = []  # (error_type, root_cause, error_line, code_snippet, problem_id, attempt, turn)

    for prob in problems:
        for att in prob.attempts:
            for turn in att.turns:
                if not turn.is_error:
                    continue
                error_type = classify_error_type(turn.output)
                error_line, traceback_code = extract_error_detail(turn.output)
                root_cause = classify_root_cause(error_type, error_line, turn.code, turn.output)

                # Get a short code snippet (first meaningful line)
                code_snippet = ''
                if turn.code:
                    for cline in turn.code.split('\n'):
                        cs = cline.strip()
                        if cs and not cs.startswith('#') and not cs.startswith('import'):
                            code_snippet = cs[:80]
                            break

                errors.append((
                    error_type, root_cause, error_line[:120],
                    code_snippet, prob.problem_id, att.attempt_num, turn.turn_num
                ))

    if not errors:
        print("\n  No errors found in the log.")
        return

    # ── 1. Error type distribution ──
    print(f"\n{'─' * 70}")
    print("1. ERROR TYPE DISTRIBUTION")
    print(f"{'─' * 70}")

    type_counts = Counter(e[0] for e in errors)
    total = len(errors)

    print(f"\n  Total errors: {total}\n")
    print(f"  {'Error Type':<22} {'Count':>6} {'%':>7}")
    print(f"  {'─'*22} {'─'*6} {'─'*7}")
    for etype, count in type_counts.most_common():
        print(f"  {etype:<22} {count:>6} {100*count/total:>6.1f}%")

    # ── 2. Root cause breakdown ──
    print(f"\n{'─' * 70}")
    print("2. ROOT CAUSE BREAKDOWN")
    print(f"{'─' * 70}")

    root_counts = Counter(e[1] for e in errors)

    print(f"\n  {'Root Cause':<52} {'Count':>6} {'%':>7}")
    print(f"  {'─'*52} {'─'*6} {'─'*7}")
    for cause, count in root_counts.most_common():
        print(f"  {cause:<52} {count:>6} {100*count/total:>6.1f}%")

    # ── 3. NameError deep dive ──
    print(f"\n{'─' * 70}")
    print("3. NAMEERROR DEEP DIVE — Undefined Variables/Functions")
    print(f"{'─' * 70}")

    name_errors = [e for e in errors if e[0] == 'NameError']
    if name_errors:
        # Extract the undefined name
        undefined_names = Counter()
        for e in name_errors:
            match = re.search(r"\((\w+)\)", e[1])
            if match:
                undefined_names[match.group(1)] += 1

        print(f"\n  Most frequently undefined names:")
        print(f"  {'Name':<30} {'Count':>6}")
        print(f"  {'─'*30} {'─'*6}")
        for name, count in undefined_names.most_common(15):
            print(f"  {name:<30} {count:>6}")

        # Check if name was defined in a previous turn that errored
        print(f"\n  Cross-cell dependency analysis:")
        cross_cell = 0
        for prob in problems:
            for att in prob.attempts:
                defined_in_errored = set()
                for turn in att.turns:
                    if turn.is_error and turn.code:
                        # Find variable assignments in errored code
                        for m in re.finditer(r'^(\w+)\s*=', turn.code, re.MULTILINE):
                            defined_in_errored.add(m.group(1))
                    elif turn.is_error:
                        # Check if this NameError references something from errored cell
                        match = re.search(r"name '(\w+)' is not defined", turn.output)
                        if match and match.group(1) in defined_in_errored:
                            cross_cell += 1

        print(f"  Variables undefined because defined in previously-errored cell: {cross_cell}")
        if cross_cell > 0:
            print(f"  -> These are cascade errors: fixing the root error would fix downstream NameErrors")
    else:
        print("\n  No NameErrors found.")

    # ── 4. TypeError deep dive ──
    print(f"\n{'─' * 70}")
    print("4. TYPEERROR DEEP DIVE — Type Mixing Issues")
    print(f"{'─' * 70}")

    type_errors = [e for e in errors if e[0] == 'TypeError']
    if type_errors:
        # Check for sympy vs python type issues
        sympy_related = sum(1 for e in type_errors if 'sympy' in e[1].lower() or 'sympy' in (e[3] or '').lower())
        print(f"\n  Total TypeErrors: {len(type_errors)}")
        print(f"  Sympy-related:    {sympy_related}")
        print(f"  Other:            {len(type_errors) - sympy_related}")

        print(f"\n  Error messages:")
        # Show unique error messages
        unique_msgs = Counter(e[2] for e in type_errors)
        for msg, count in unique_msgs.most_common(10):
            print(f"    [{count}x] {msg}")
    else:
        print("\n  No TypeErrors found.")

    # ── 5. ValueError deep dive ──
    print(f"\n{'─' * 70}")
    print("5. VALUEERROR DEEP DIVE — Constraint Violations")
    print(f"{'─' * 70}")

    val_errors = [e for e in errors if e[0] == 'ValueError']
    if val_errors:
        unique_msgs = Counter(e[2] for e in val_errors)
        print(f"\n  Total ValueErrors: {len(val_errors)}")
        print(f"\n  Error messages:")
        for msg, count in unique_msgs.most_common(10):
            print(f"    [{count}x] {msg}")
    else:
        print("\n  No ValueErrors found.")

    # ── 6. Timeout analysis ──
    print(f"\n{'─' * 70}")
    print("6. TIMEOUT ANALYSIS")
    print(f"{'─' * 70}")

    timeouts = [e for e in errors if e[0] == 'Timeout']
    if timeouts:
        timeout_causes = Counter(e[1] for e in timeouts)
        print(f"\n  Total timeouts: {len(timeouts)}")
        print(f"\n  {'Cause':<40} {'Count':>6}")
        print(f"  {'─'*40} {'─'*6}")
        for cause, count in timeout_causes.most_common():
            print(f"  {cause:<40} {count:>6}")
    else:
        print("\n  No timeouts found.")

    # ── 7. Offending code samples ──
    print(f"\n{'─' * 70}")
    print("7. SAMPLE OFFENDING CODE (by root cause, first example)")
    print(f"{'─' * 70}")

    seen_causes = set()
    for e in sorted(errors, key=lambda x: x[1]):
        cause = e[1]
        if cause in seen_causes:
            continue
        seen_causes.add(cause)
        print(f"\n  [{cause}]")
        print(f"    Problem: {e[4]}, Attempt {e[5]}, Turn {e[6]}")
        if e[3]:
            print(f"    Code:    {e[3]}")
        print(f"    Error:   {e[2]}")

    # ── 8. Actionable summary ──
    print(f"\n{'=' * 90}")
    print("ACTIONABLE SUMMARY — PROMPT/CONFIG FIXES")
    print("=" * 90)

    # Group root causes by actionability
    print(f"\n  Top root causes and suggested fixes:\n")
    for cause, count in root_counts.most_common(10):
        pct = 100 * count / total
        print(f"  [{count}x, {pct:.0f}%] {cause}")

        # Suggest fix
        if 'not_imported' in cause:
            print(f"    FIX: Add to sandbox preamble or prompt: 'Always import libraries at the top'")
        elif 'variable_undefined' in cause:
            print(f"    FIX: Prompt: 'Define all variables before use. If a previous code cell errored,")
            print(f"           re-define needed variables.'")
        elif 'sympy_to_python' in cause or 'arithmetic_type' in cause:
            print(f"    FIX: Prompt: 'When using sympy, convert results with int() or float() before")
            print(f"           arithmetic with Python numbers.'")
        elif 'Timeout' in cause:
            print(f"    FIX: Prompt: 'Avoid brute force on large search spaces. Estimate complexity first.'")
        elif 'combinatorial_explosion' in cause:
            print(f"    FIX: Prompt: 'Check itertools output size before iterating: prefer mathematical")
            print(f"           formulas over enumeration when possible.'")
        elif 'out_of_range' in cause:
            print(f"    FIX: Prompt: 'Check list/array lengths before indexing.'")
        elif 'SyntaxError' in cause:
            print(f"    FIX: Likely truncated generation. Increase max_tokens or adjust code structure.")
        elif 'MemoryError' in cause or 'out_of_memory' in cause:
            print(f"    FIX: Prompt: 'Avoid creating large lists/arrays. Use generators and math.'")
        elif 'cascade' in cause.lower() or 'cross_cell' in cause.lower():
            print(f"    FIX: Sandbox: Re-run errored cells or reset state between attempts.")
        else:
            print(f"    FIX: Review specific instances for pattern.")
        print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 log_exploration/error_patterns.py <diagnostic.log>")
        sys.exit(1)

    problems = parse_log(sys.argv[1])
    analyze_error_patterns(problems)


if __name__ == '__main__':
    main()
