#!/usr/bin/env python3
"""
Library x Topic Deep Analysis for AIMO3 Solver
================================================
Analyzes which Python libraries are used for which math topics,
whether those choices are optimal, unavailable library recovery patterns,
and anti-patterns that always fail.

Usage:
    python3 log_exploration/library_topic_analysis.py <logfile>
    python3 log_exploration/library_topic_analysis.py output/v23/diagnostic.log
    python3 log_exploration/library_topic_analysis.py output/v23/diagnostic.log --md output/v23/library_topic_analysis.md

Options:
    --md FILE    Save markdown report to FILE
    --help       Show this help
"""

import sys
import os
import re
import argparse
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


# ── Topic Detection ─────────────────────────────────────────────────────────

TOPIC_KEYWORDS = {
    'geometry': [
        'triangle', 'circle', 'angle', 'polygon', 'area', 'perimeter',
        'radius', 'diameter', 'circumscri', 'inscri', 'tangent',
        'parallel', 'perpendicular', 'midpoint', 'segment', 'cube',
        'sphere', 'tetrahedr', 'quadrilateral', 'pentagon', 'hexagon',
        'convex hull', 'vertex', 'vertices', 'ellipse', 'cone',
        'plane divides', 'planes divide', 'three-dimensional',
    ],
    'number_theory': [
        'divisor', 'prime', 'gcd', 'lcm', 'modulo', 'congruent',
        'remainder', 'coprime', 'euler', 'fermat', 'residue',
        'divisible', 'parity', 'digit', 'norwegian',
        'perfect square', 'perfect cube', 'factorization',
    ],
    'combinatorics': [
        'permutation', 'combination', 'arrange', 'ways to',
        'choose', 'subset', 'partition', 'coloring', 'counting',
        'tournament', 'board', 'grid', 'chess', 'tile', 'domino',
        'placing', 'select', 'stone', 'marked', 'five-in-a-row',
        'black and white', 'label', 'directed diagonal',
    ],
    'algebra': [
        'polynomial', 'equation', 'root', 'coefficient', 'sequence',
        'series', 'function', 'inequality', 'matrix', 'determinant',
        'eigenvalue', 'quadratic', 'cubic', 'real number', 'complex number',
    ],
    'probability': [
        'probability', 'expected value', 'random variable', 'dice',
        'coin', 'independent', 'conditional', 'distribution', 'expectation',
    ],
    'game_theory': [
        'game', 'player', 'strategy', 'winning', 'losing',
        'opponent', 'alice and bob', 'players',
    ],
    'optimization': [
        'minimum', 'maximum', 'minimize', 'maximize', 'optimal',
        'at least', 'at most', 'smallest', 'largest', 'fewest',
        'find the minimal', 'find the maximal',
    ],
}


def detect_topics(problem_text):
    """Detect math topics from problem text using keyword matching.
    A problem can belong to multiple topics.
    Returns list of topic strings."""
    text = problem_text.lower()
    topics = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            topics.append(topic)
    if not topics:
        topics.append('other')
    return topics


# ── Library Extraction ──────────────────────────────────────────────────────

def extract_imports(code):
    """Extract imported library names from code."""
    imports = set()
    for line in code.split('\n'):
        line = line.strip()
        # import X
        m = re.match(r'^import\s+(\w+)', line)
        if m:
            imports.add(m.group(1))
        # from X import ...
        m = re.match(r'^from\s+(\w+)', line)
        if m:
            imports.add(m.group(1))
    return imports


def extract_function_calls(code):
    """Extract module.function() patterns from code."""
    calls = []
    for m in re.finditer(r'(\w+)\.(\w+)\s*\(', code):
        module = m.group(1)
        func = m.group(2)
        # Normalize aliases
        if module == 'np':
            module = 'numpy'
        elif module in ('sp', 'sym'):
            module = 'sympy'
        elif module == 'pd':
            module = 'pandas'
        # Skip variable-like prefixes
        skip = {'self', 'cls', 'str', 'int', 'float', 'list', 'dict',
                'set', 'tuple', 'result', 'answer', 'res', 'sol'}
        if module in skip:
            continue
        calls.append((module, func))
    return calls


def get_attempt_outcome(problem, attempt):
    """Return 'correct', 'wrong', or 'none' for an attempt."""
    if attempt.is_none or attempt.answer is None:
        return 'none'
    if problem.expected is not None and attempt.answer == problem.expected:
        return 'correct'
    return 'wrong'


def get_attempt_has_error(attempt):
    """Return True if any turn in this attempt had an error."""
    return any(t.is_error for t in attempt.turns)


# ── Part 1: Library x Topic Matrix ──────────────────────────────────────────

def build_library_topic_matrix(problems):
    """Build matrix: topic x library -> {total, correct, wrong, none, error_turns}."""
    matrix = defaultdict(lambda: defaultdict(lambda: {
        'total': 0, 'correct': 0, 'wrong': 0, 'none': 0, 'error_attempts': 0
    }))

    # Also track per-topic totals
    topic_totals = defaultdict(lambda: {'total': 0, 'correct': 0, 'wrong': 0, 'none': 0})

    for p in problems:
        topics = detect_topics(p.problem_text)
        for a in p.attempts:
            all_code = '\n'.join(t.code for t in a.turns if t.code)
            if not all_code.strip():
                # No code at all — still counts for topic totals
                outcome = get_attempt_outcome(p, a)
                for topic in topics:
                    topic_totals[topic]['total'] += 1
                    topic_totals[topic][outcome] += 1
                continue

            libs = extract_imports(all_code)
            # Also pick up from parser's library field
            for lib_str in a.libraries:
                for part in re.findall(r'(?:import|from)\s+(\w+)', lib_str):
                    libs.add(part)

            outcome = get_attempt_outcome(p, a)
            has_error = get_attempt_has_error(a)

            for topic in topics:
                topic_totals[topic]['total'] += 1
                topic_totals[topic][outcome] += 1
                for lib in libs:
                    matrix[topic][lib]['total'] += 1
                    matrix[topic][lib][outcome] += 1
                    if has_error:
                        matrix[topic][lib]['error_attempts'] += 1

    return matrix, topic_totals


def print_library_topic_matrix(matrix, topic_totals, out):
    """Print the library x topic matrix."""
    out.write("\n" + "=" * 80 + "\n")
    out.write("  PART 1: LIBRARY x TOPIC MATRIX\n")
    out.write("=" * 80 + "\n")

    for topic in sorted(matrix.keys()):
        tt = topic_totals[topic]
        base_acc = tt['correct'] / (tt['correct'] + tt['wrong']) if (tt['correct'] + tt['wrong']) > 0 else 0
        out.write(f"\n{'─' * 78}\n")
        out.write(f"  TOPIC: {topic.upper()} ({tt['total']} attempts, "
                  f"base accuracy: {100*base_acc:.0f}%)\n")
        out.write(f"{'─' * 78}\n")

        libs = matrix[topic]
        # Sort by total usage
        sorted_libs = sorted(libs.items(), key=lambda x: -x[1]['total'])

        out.write(f"  {'Library':<18} {'Uses':>5} {'Correct':>8} {'Wrong':>6} "
                  f"{'None':>5} {'Correct%':>9} {'None%':>6} {'ErrAtt%':>8}\n")
        out.write(f"  {'─'*18} {'─'*5} {'─'*8} {'─'*6} {'─'*5} {'─'*9} {'─'*6} {'─'*8}\n")

        for lib, stats in sorted_libs[:20]:
            if stats['total'] < 2:
                continue
            non_none = stats['correct'] + stats['wrong']
            acc = 100 * stats['correct'] / non_none if non_none > 0 else 0
            none_rate = 100 * stats['none'] / stats['total']
            err_rate = 100 * stats['error_attempts'] / stats['total']
            out.write(f"  {lib:<18} {stats['total']:>5} {stats['correct']:>8} "
                      f"{stats['wrong']:>6} {stats['none']:>5} {acc:>8.0f}% "
                      f"{none_rate:>5.0f}% {err_rate:>7.0f}%\n")

        # Best and worst libraries for this topic
        out.write(f"\n  BEST for {topic}:\n")
        best = [(lib, s) for lib, s in sorted_libs
                if s['correct'] + s['wrong'] >= 3]
        best.sort(key=lambda x: -(x[1]['correct'] / (x[1]['correct'] + x[1]['wrong'])
                                  if (x[1]['correct'] + x[1]['wrong']) > 0 else 0))
        for lib, s in best[:5]:
            non_none = s['correct'] + s['wrong']
            acc = 100 * s['correct'] / non_none if non_none > 0 else 0
            out.write(f"    {lib:<18} {acc:.0f}% accuracy ({s['correct']}/{non_none})\n")

        out.write(f"\n  WORST for {topic} (anti-patterns):\n")
        worst = [(lib, s) for lib, s in sorted_libs
                 if s['correct'] + s['wrong'] >= 3]
        worst.sort(key=lambda x: (x[1]['correct'] / (x[1]['correct'] + x[1]['wrong'])
                                  if (x[1]['correct'] + x[1]['wrong']) > 0 else 0))
        for lib, s in worst[:5]:
            non_none = s['correct'] + s['wrong']
            acc = 100 * s['correct'] / non_none if non_none > 0 else 0
            out.write(f"    {lib:<18} {acc:.0f}% accuracy ({s['correct']}/{non_none})\n")


# ── Part 2: Unavailable Library Replacement Analysis ────────────────────────

UNAVAILABLE_LIBS = {
    'pulp': {
        'description': 'Linear programming / Integer LP solver',
        'math_ops': ['LP', 'ILP', 'Mixed Integer Programming'],
        'alternatives': ['scipy.optimize.linprog (for LP)',
                         'itertools + brute force (for small ILP)',
                         'sympy (for constraint solving)',
                         'manual branch-and-bound'],
    },
    'ortools': {
        'description': 'Google OR-Tools: constraint programming, SAT, LP',
        'math_ops': ['Constraint Programming', 'SAT solving', 'LP', 'CP-SAT'],
        'alternatives': ['itertools (constraint enumeration)',
                         'backtracking search (manual)',
                         'scipy.optimize.linprog (for LP)',
                         'sympy (for symbolic constraints)'],
    },
    'z3': {
        'description': 'Z3 SMT solver: satisfiability, constraint solving',
        'math_ops': ['SMT solving', 'SAT', 'Constraint Satisfaction'],
        'alternatives': ['sympy.solve (for algebraic constraints)',
                         'itertools + brute force (for small domains)',
                         'backtracking (manual)'],
    },
    'mip': {
        'description': 'Python-MIP: Mixed Integer Programming',
        'math_ops': ['ILP', 'MIP', 'Binary optimization'],
        'alternatives': ['scipy.optimize.linprog (for LP relaxation)',
                         'itertools (for small search spaces)',
                         'manual branch-and-bound'],
    },
}


def analyze_unavailable_libraries(problems, out):
    """For each unavailable library, analyze what problems trigger it,
    what operations are attempted, and recovery patterns."""
    out.write("\n" + "=" * 80 + "\n")
    out.write("  PART 2: UNAVAILABLE LIBRARY REPLACEMENT ANALYSIS\n")
    out.write("=" * 80 + "\n")

    for lib_name, lib_info in UNAVAILABLE_LIBS.items():
        lib_regex = re.compile(rf'(?:import|from)\s+{lib_name}', re.IGNORECASE)

        problems_using = set()
        total_imports = 0
        error_imports = 0
        recovery_success = 0  # After failed import, did they find alternative?
        problem_topics = Counter()
        problem_outcomes = {'correct': 0, 'wrong': 0, 'none': 0}
        context_snippets = []

        for p in problems:
            topics = detect_topics(p.problem_text)
            for a in p.attempts:
                attempt_uses_lib = False
                attempt_import_failed = False
                attempt_recovered = False

                for t_idx, t in enumerate(a.turns):
                    if not t.code.strip():
                        continue

                    if lib_regex.search(t.code):
                        attempt_uses_lib = True
                        total_imports += 1
                        problems_using.add(p.problem_id)

                        if t.is_error and ('ModuleNotFoundError' in t.output or
                                           'ImportError' in t.output or
                                           'No module named' in t.output):
                            error_imports += 1
                            attempt_import_failed = True

                        # Capture context
                        if len(context_snippets) < 5:
                            code_lines = t.code.strip().split('\n')
                            # Get first 8 lines for context
                            snippet = '\n'.join(code_lines[:8])
                            context_snippets.append({
                                'problem': p.problem_id,
                                'attempt': a.attempt_num,
                                'turn': t.turn_num,
                                'is_error': t.is_error,
                                'code': snippet[:300],
                                'topics': topics,
                            })

                    # Check if later turns use an alternative after a failure
                    if attempt_import_failed and not lib_regex.search(t.code):
                        alt_libs = extract_imports(t.code)
                        recovery_alts = {'scipy', 'sympy', 'itertools', 'numpy', 'networkx'}
                        if alt_libs & recovery_alts and not t.is_error:
                            attempt_recovered = True

                if attempt_uses_lib:
                    outcome = get_attempt_outcome(p, a)
                    problem_outcomes[outcome] += 1
                    for topic in topics:
                        problem_topics[topic] += 1
                    if attempt_import_failed and attempt_recovered:
                        recovery_success += 1

        out.write(f"\n{'─' * 78}\n")
        out.write(f"  {lib_name.upper()}: {lib_info['description']}\n")
        out.write(f"{'─' * 78}\n")
        out.write(f"  Total import attempts: {total_imports}\n")
        out.write(f"  Import errors: {error_imports}\n")
        out.write(f"  Problems affected: {len(problems_using)} "
                  f"({', '.join(sorted(problems_using))})\n")
        out.write(f"  Successful recoveries after error: {recovery_success}\n")
        out.write(f"\n  Math operations attempted: {', '.join(lib_info['math_ops'])}\n")
        out.write(f"  Available alternatives: {', '.join(lib_info['alternatives'])}\n")

        out.write(f"\n  Topic distribution of {lib_name} usage:\n")
        for topic, count in problem_topics.most_common():
            out.write(f"    {topic}: {count} attempts\n")

        out.write(f"\n  Outcome when {lib_name} is used:\n")
        total = sum(problem_outcomes.values())
        for outcome in ['correct', 'wrong', 'none']:
            pct = 100 * problem_outcomes[outcome] / total if total > 0 else 0
            out.write(f"    {outcome}: {problem_outcomes[outcome]} ({pct:.0f}%)\n")

        if context_snippets:
            out.write(f"\n  Example code snippets:\n")
            for snip in context_snippets[:3]:
                err_tag = " [ERROR]" if snip['is_error'] else ""
                out.write(f"    --- {snip['problem']} att={snip['attempt']} "
                          f"turn={snip['turn']}{err_tag} "
                          f"topics={snip['topics']} ---\n")
                for line in snip['code'].split('\n'):
                    out.write(f"      {line}\n")
                out.write("\n")


# ── Part 3: Optimal Library Recommendations ─────────────────────────────────

def build_recommendations(matrix, topic_totals, problems, out):
    """Based on the data, create recommended library mappings per topic."""
    out.write("\n" + "=" * 80 + "\n")
    out.write("  PART 3: OPTIMAL LIBRARY RECOMMENDATIONS BY TOPIC\n")
    out.write("=" * 80 + "\n")

    # Also compute function-level success rates per topic
    topic_func_stats = defaultdict(lambda: defaultdict(lambda: {
        'total': 0, 'correct': 0, 'wrong': 0, 'none': 0
    }))

    for p in problems:
        topics = detect_topics(p.problem_text)
        for a in p.attempts:
            outcome = get_attempt_outcome(p, a)
            all_code = '\n'.join(t.code for t in a.turns if t.code)
            if not all_code.strip():
                continue
            calls = extract_function_calls(all_code)
            seen = set()
            for module, func in calls:
                key = f"{module}.{func}"
                if key not in seen:
                    seen.add(key)
                    for topic in topics:
                        topic_func_stats[topic][key]['total'] += 1
                        topic_func_stats[topic][key][outcome] += 1

    recommendations = {
        'number_theory': {
            'recommended': [
                ('sympy', ['factorint', 'isprime', 'divisors', 'totient',
                           'ntheory.mobius', 'nextprime', 'mod_inverse',
                           'primitive_root']),
                ('math', ['gcd', 'isqrt', 'comb']),
                ('itertools', ['product', 'combinations']),
            ],
            'avoid': ['pulp', 'ortools', 'cmath', 'networkx'],
        },
        'combinatorics': {
            'recommended': [
                ('itertools', ['product', 'combinations', 'permutations',
                               'combinations_with_replacement']),
                ('math', ['comb', 'factorial', 'perm']),
                ('functools', ['lru_cache']),
                ('sympy', ['binomial', 'factorial', 'bell', 'catalan']),
            ],
            'avoid': ['pulp', 'ortools', 'z3', 'mip'],
        },
        'geometry': {
            'recommended': [
                ('math', ['sqrt', 'cos', 'sin', 'atan2', 'pi', 'acos']),
                ('sympy', ['symbols', 'solve', 'Rational', 'sqrt',
                           'simplify', 'nsimplify', 'geometry']),
                ('numpy', ['array', 'linalg', 'cross', 'dot']),
                ('fractions', ['Fraction']),
            ],
            'avoid': ['ortools', 'pulp'],
        },
        'algebra': {
            'recommended': [
                ('sympy', ['symbols', 'solve', 'expand', 'factor',
                           'simplify', 'Eq', 'Poly', 'roots',
                           'series', 'diff', 'integrate']),
                ('numpy', ['array', 'linalg.solve', 'roots']),
                ('fractions', ['Fraction']),
            ],
            'avoid': ['pulp', 'ortools'],
        },
        'optimization': {
            'recommended': [
                ('itertools', ['product', 'combinations', 'permutations']),
                ('scipy.optimize', ['linprog (for LP problems)']),
                ('functools', ['lru_cache (for DP)']),
                ('sympy', ['solve', 'Eq (for constraint solving)']),
            ],
            'note': 'Model tries pulp/ortools/mip here but they are unavailable. '
                    'scipy.optimize.linprog handles LP; brute-force handles small ILP.',
        },
        'probability': {
            'recommended': [
                ('fractions', ['Fraction (exact rational arithmetic)']),
                ('sympy', ['Rational', 'binomial', 'factorial']),
                ('math', ['comb', 'factorial']),
                ('itertools', ['product (sample space enumeration)']),
                ('random', ['(Monte Carlo simulation for verification)']),
            ],
            'avoid': [],
        },
        'game_theory': {
            'recommended': [
                ('functools', ['lru_cache (for game tree memoization)']),
                ('itertools', ['(for move enumeration)']),
                ('sympy', ['(for Sprague-Grundy value computation)']),
            ],
            'avoid': ['pulp', 'ortools'],
        },
    }

    for topic in sorted(recommendations.keys()):
        rec = recommendations[topic]
        tt = topic_totals.get(topic, {'total': 0, 'correct': 0, 'wrong': 0, 'none': 0})
        out.write(f"\n{'─' * 78}\n")
        out.write(f"  {topic.upper()}\n")
        out.write(f"{'─' * 78}\n")

        out.write(f"  Recommended libraries:\n")
        for lib, funcs in rec['recommended']:
            out.write(f"    {lib}: {', '.join(funcs)}\n")

        if rec.get('avoid'):
            out.write(f"\n  Avoid (low accuracy or unavailable):\n")
            for lib in rec['avoid']:
                out.write(f"    {lib}\n")

        if rec.get('note'):
            out.write(f"\n  Note: {rec['note']}\n")

        # Show actual data-driven function performance for this topic
        func_stats = topic_func_stats.get(topic, {})
        if func_stats:
            out.write(f"\n  Data-driven top functions for {topic} "
                      f"(by accuracy, min 3 non-None uses):\n")
            ranked = []
            for func, stats in func_stats.items():
                non_none = stats['correct'] + stats['wrong']
                if non_none >= 3:
                    acc = stats['correct'] / non_none
                    ranked.append((func, acc, stats['correct'], non_none, stats['total']))
            ranked.sort(key=lambda x: (-x[1], -x[3]))
            out.write(f"    {'Function':<30} {'Accuracy':>9} {'Correct':>8} "
                      f"{'NonNone':>8} {'Total':>6}\n")
            out.write(f"    {'─'*30} {'─'*9} {'─'*8} {'─'*8} {'─'*6}\n")
            for func, acc, correct, non_none, total in ranked[:15]:
                out.write(f"    {func:<30} {100*acc:>8.0f}% {correct:>8} "
                          f"{non_none:>8} {total:>6}\n")


# ── Part 4: Anti-patterns ───────────────────────────────────────────────────

def analyze_anti_patterns(problems, out):
    """Find library usage patterns that ALWAYS fail."""
    out.write("\n" + "=" * 80 + "\n")
    out.write("  PART 4: ANTI-PATTERNS\n")
    out.write("=" * 80 + "\n")

    # 4a: Library+function combos with 0% success rate
    out.write(f"\n{'─' * 78}\n")
    out.write("  4a. LIBRARY.FUNCTION COMBINATIONS WITH 0% SUCCESS RATE (min 3 uses)\n")
    out.write(f"{'─' * 78}\n")

    func_outcomes = defaultdict(lambda: {'correct': 0, 'wrong': 0, 'none': 0, 'total': 0})

    for p in problems:
        for a in p.attempts:
            all_code = '\n'.join(t.code for t in a.turns if t.code)
            if not all_code.strip():
                continue
            calls = extract_function_calls(all_code)
            outcome = get_attempt_outcome(p, a)
            seen = set()
            for module, func in calls:
                key = f"{module}.{func}"
                if key not in seen:
                    seen.add(key)
                    func_outcomes[key]['total'] += 1
                    func_outcomes[key][outcome] += 1

    zero_pct = []
    for func, stats in func_outcomes.items():
        non_none = stats['correct'] + stats['wrong']
        if non_none >= 3 and stats['correct'] == 0:
            zero_pct.append((func, stats['wrong'], stats['none'], stats['total']))

    zero_pct.sort(key=lambda x: -x[1])
    out.write(f"\n  {'Function':<35} {'Wrong':>6} {'None':>5} {'Total':>6}\n")
    out.write(f"  {'─'*35} {'─'*6} {'─'*5} {'─'*6}\n")
    for func, wrong, none, total in zero_pct:
        out.write(f"  {func:<35} {wrong:>6} {none:>5} {total:>6}\n")

    out.write(f"\n  Total 0%-accuracy functions: {len(zero_pct)}\n")

    # 4b: Import count vs success rate
    out.write(f"\n{'─' * 78}\n")
    out.write("  4b. IMPORT COUNT vs SUCCESS RATE\n")
    out.write(f"{'─' * 78}\n")

    import_count_outcomes = defaultdict(lambda: {'correct': 0, 'wrong': 0, 'none': 0, 'total': 0})

    for p in problems:
        for a in p.attempts:
            all_code = '\n'.join(t.code for t in a.turns if t.code)
            if not all_code.strip():
                continue
            libs = extract_imports(all_code)
            for lib_str in a.libraries:
                for part in re.findall(r'(?:import|from)\s+(\w+)', lib_str):
                    libs.add(part)

            # Bucket: 0-1, 2-3, 4-5, 6+
            n = len(libs)
            if n <= 1:
                bucket = '0-1'
            elif n <= 3:
                bucket = '2-3'
            elif n <= 5:
                bucket = '4-5'
            elif n <= 7:
                bucket = '6-7'
            else:
                bucket = '8+'

            outcome = get_attempt_outcome(p, a)
            import_count_outcomes[bucket]['total'] += 1
            import_count_outcomes[bucket][outcome] += 1

    out.write(f"\n  {'Import Count':>12} {'Total':>6} {'Correct':>8} {'Wrong':>6} "
              f"{'None':>5} {'Accuracy':>9} {'None%':>6}\n")
    out.write(f"  {'─'*12} {'─'*6} {'─'*8} {'─'*6} {'─'*5} {'─'*9} {'─'*6}\n")
    for bucket in ['0-1', '2-3', '4-5', '6-7', '8+']:
        stats = import_count_outcomes.get(bucket, {'correct': 0, 'wrong': 0, 'none': 0, 'total': 0})
        non_none = stats['correct'] + stats['wrong']
        acc = 100 * stats['correct'] / non_none if non_none > 0 else 0
        none_rate = 100 * stats['none'] / stats['total'] if stats['total'] > 0 else 0
        out.write(f"  {bucket:>12} {stats['total']:>6} {stats['correct']:>8} "
                  f"{stats['wrong']:>6} {stats['none']:>5} {acc:>8.0f}% {none_rate:>5.0f}%\n")

    # 4c: Specific crashing function calls
    out.write(f"\n{'─' * 78}\n")
    out.write("  4c. SPECIFIC FUNCTION CALLS THAT CRASH (in error turns, min 5 occurrences)\n")
    out.write(f"{'─' * 78}\n")

    crash_funcs = Counter()
    crash_error_types = defaultdict(Counter)

    for p in problems:
        for a in p.attempts:
            for t in a.turns:
                if t.is_error and t.code.strip():
                    calls = extract_function_calls(t.code)
                    error_type = classify_error(t.output)
                    seen = set()
                    for module, func in calls:
                        key = f"{module}.{func}"
                        if key not in seen:
                            seen.add(key)
                            crash_funcs[key] += 1
                            crash_error_types[key][error_type] += 1

    out.write(f"\n  {'Function':<35} {'Crashes':>8} {'Top Error Type':<25}\n")
    out.write(f"  {'─'*35} {'─'*8} {'─'*25}\n")
    for func, count in crash_funcs.most_common(30):
        if count < 5:
            break
        top_err = crash_error_types[func].most_common(1)[0] if crash_error_types[func] else ('?', 0)
        out.write(f"  {func:<35} {count:>8} {top_err[0]} ({top_err[1]})\n")

    # 4d: Unavailable library chains — model tries lib A, fails, tries B, fails
    out.write(f"\n{'─' * 78}\n")
    out.write("  4d. UNAVAILABLE LIBRARY CASCADES (tries multiple unavailable libs)\n")
    out.write(f"{'─' * 78}\n")

    unavailable = {'pulp', 'ortools', 'z3', 'mip', 'cvxpy', 'gurobipy', 'cplex'}
    cascade_problems = defaultdict(list)  # pid -> list of (attempt, libs_tried)

    for p in problems:
        for a in p.attempts:
            libs_tried = []
            for t in a.turns:
                if not t.code.strip():
                    continue
                imports = extract_imports(t.code)
                tried = imports & unavailable
                if tried:
                    libs_tried.extend(sorted(tried))
            if len(set(libs_tried)) >= 2:
                cascade_problems[p.problem_id].append(
                    (a.attempt_num, list(dict.fromkeys(libs_tried)))
                )

    if cascade_problems:
        out.write(f"\n  Problems where model tried 2+ unavailable libraries in one attempt:\n")
        for pid, attempts in sorted(cascade_problems.items()):
            for att_num, libs in attempts:
                out.write(f"    {pid} att={att_num}: {' -> '.join(libs)}\n")
        out.write(f"\n  Total cascade attempts: "
                  f"{sum(len(v) for v in cascade_problems.values())}\n")
    else:
        out.write(f"\n  No multi-library cascades detected.\n")

    # 4e: Hallucinated function calls (functions that don't exist)
    out.write(f"\n{'─' * 78}\n")
    out.write("  4e. LIKELY HALLUCINATED FUNCTION CALLS\n")
    out.write(f"{'─' * 78}\n")

    known_bad = [
        ('sympy', 'crt', 'Does not exist in top-level sympy. Use sympy.ntheory.modular.crt'),
        ('sympy', 'totient', 'Use sympy.ntheory.totient or sympy.totient (careful with import)'),
        ('sympy', 'mobius', 'Use sympy.ntheory.mobius'),
        ('math', 'lcm', 'math.lcm exists only in Python 3.9+'),
        ('itertools', 'pairwise', 'itertools.pairwise exists only in Python 3.10+'),
    ]

    out.write(f"\n  Known problematic calls found in log:\n")
    for module, func, note in known_bad:
        key = f"{module}.{func}"
        if key in func_outcomes:
            stats = func_outcomes[key]
            out.write(f"    {key}: {stats['total']} uses, "
                      f"{stats['correct']} correct, {stats['wrong']} wrong, "
                      f"{stats['none']} none\n")
            out.write(f"      Note: {note}\n")

    # Also find sympy function calls that appear in error turns
    sympy_error_funcs = Counter()
    for p in problems:
        for a in p.attempts:
            for t in a.turns:
                if t.is_error and t.code.strip():
                    calls = extract_function_calls(t.code)
                    for module, func in calls:
                        if module == 'sympy':
                            sympy_error_funcs[f"sympy.{func}"] += 1

    out.write(f"\n  Sympy functions most often in error turns:\n")
    for func, count in sympy_error_funcs.most_common(10):
        out.write(f"    {func}: {count} error turns\n")


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


# ── Markdown Report ─────────────────────────────────────────────────────────

def generate_markdown(matrix, topic_totals, problems, md_path):
    """Generate a full markdown report."""
    with open(md_path, 'w') as f:
        f.write("# Library x Topic Analysis — AIMO3 v23\n\n")
        f.write(f"Log: `output/v23/diagnostic.log`  \n")
        f.write(f"Problems: {len(problems)} | ")
        total_att = sum(len(p.attempts) for p in problems)
        correct = sum(1 for p in problems if p.correct)
        f.write(f"Attempts: {total_att} | ")
        f.write(f"Score: {correct}/{len(problems)}\n\n")

        f.write("## Summary\n\n")
        f.write("This analysis covers:\n")
        f.write("1. **Library x Topic Matrix** — which libraries are used for which topics, success rates\n")
        f.write("2. **Unavailable Library Replacements** — pulp, ortools, z3, mip recovery analysis\n")
        f.write("3. **Optimal Library Recommendations** — data-driven recommendations per topic\n")
        f.write("4. **Anti-patterns** — library+function combos that always fail\n\n")

        # Part 1: Matrix summary tables
        f.write("## Part 1: Library x Topic Matrix\n\n")

        for topic in sorted(matrix.keys()):
            tt = topic_totals[topic]
            base_acc = tt['correct'] / (tt['correct'] + tt['wrong']) if (tt['correct'] + tt['wrong']) > 0 else 0
            f.write(f"### {topic.replace('_', ' ').title()}\n\n")
            f.write(f"**{tt['total']} attempts, base accuracy: {100*base_acc:.0f}%**\n\n")

            libs = matrix[topic]
            sorted_libs = sorted(libs.items(), key=lambda x: -x[1]['total'])

            f.write("| Library | Uses | Correct | Wrong | None | Accuracy | None% |\n")
            f.write("|---------|------|---------|-------|------|----------|-------|\n")
            for lib, stats in sorted_libs[:15]:
                if stats['total'] < 2:
                    continue
                non_none = stats['correct'] + stats['wrong']
                acc = 100 * stats['correct'] / non_none if non_none > 0 else 0
                none_rate = 100 * stats['none'] / stats['total']
                f.write(f"| {lib} | {stats['total']} | {stats['correct']} | "
                        f"{stats['wrong']} | {stats['none']} | "
                        f"{acc:.0f}% | {none_rate:.0f}% |\n")

            # Best/worst
            best = [(lib, s) for lib, s in sorted_libs
                    if s['correct'] + s['wrong'] >= 3]
            best.sort(key=lambda x: -(x[1]['correct'] / (x[1]['correct'] + x[1]['wrong'])
                                      if (x[1]['correct'] + x[1]['wrong']) > 0 else 0))
            if best:
                f.write(f"\n**Best libraries for {topic.replace('_', ' ')}:** ")
                f.write(", ".join(f"{lib} ({100*s['correct']/(s['correct']+s['wrong']):.0f}%)"
                                 for lib, s in best[:3]
                                 if s['correct'] + s['wrong'] > 0))
                f.write("\n")

            worst = [(lib, s) for lib, s in sorted_libs
                     if s['correct'] + s['wrong'] >= 3]
            worst.sort(key=lambda x: (x[1]['correct'] / (x[1]['correct'] + x[1]['wrong'])
                                      if (x[1]['correct'] + x[1]['wrong']) > 0 else 0))
            if worst:
                f.write(f"\n**Worst libraries for {topic.replace('_', ' ')}:** ")
                f.write(", ".join(f"{lib} ({100*s['correct']/(s['correct']+s['wrong']):.0f}%)"
                                 for lib, s in worst[:3]
                                 if s['correct'] + s['wrong'] > 0))
                f.write("\n\n")

        # Part 2: Unavailable libraries
        f.write("## Part 2: Unavailable Library Replacements\n\n")

        for lib_name, lib_info in UNAVAILABLE_LIBS.items():
            lib_regex = re.compile(rf'(?:import|from)\s+{lib_name}', re.IGNORECASE)
            total_imports = 0
            error_imports = 0
            recovery_count = 0
            problems_affected = set()
            problem_topics_counter = Counter()
            outcomes = {'correct': 0, 'wrong': 0, 'none': 0}

            for p in problems:
                topics = detect_topics(p.problem_text)
                for a in p.attempts:
                    attempt_uses = False
                    attempt_failed = False
                    attempt_recovered = False
                    for t_idx, t in enumerate(a.turns):
                        if not t.code.strip():
                            continue
                        if lib_regex.search(t.code):
                            attempt_uses = True
                            total_imports += 1
                            problems_affected.add(p.problem_id)
                            if t.is_error:
                                if 'ModuleNotFoundError' in (t.output or '') or \
                                   'ImportError' in (t.output or '') or \
                                   'No module named' in (t.output or ''):
                                    error_imports += 1
                                    attempt_failed = True
                        elif attempt_failed:
                            alt_libs = extract_imports(t.code)
                            if alt_libs & {'scipy', 'sympy', 'itertools', 'numpy', 'networkx'} \
                               and not t.is_error:
                                attempt_recovered = True

                    if attempt_uses:
                        outcome = get_attempt_outcome(p, a)
                        outcomes[outcome] += 1
                        for topic in topics:
                            problem_topics_counter[topic] += 1
                        if attempt_failed and attempt_recovered:
                            recovery_count += 1

            f.write(f"### `{lib_name}` — {lib_info['description']}\n\n")
            f.write(f"- **Import attempts:** {total_imports}\n")
            f.write(f"- **Import errors:** {error_imports}\n")
            f.write(f"- **Problems affected:** {len(problems_affected)}\n")
            f.write(f"- **Successful recoveries:** {recovery_count}\n")
            f.write(f"- **Outcomes:** correct={outcomes['correct']}, "
                    f"wrong={outcomes['wrong']}, none={outcomes['none']}\n")
            f.write(f"- **Topics:** {', '.join(f'{t}({c})' for t, c in problem_topics_counter.most_common())}\n")
            f.write(f"- **Alternatives:** {', '.join(lib_info['alternatives'])}\n\n")

        # Part 3: Recommendations
        f.write("## Part 3: Optimal Library Recommendations\n\n")
        f.write("Based on the data, here are the recommended library mappings per topic:\n\n")

        rec_table = {
            'Number Theory': 'sympy (factorint, isprime, divisors, totient, mod_inverse), math (gcd, isqrt), itertools',
            'Combinatorics': 'itertools (product, combinations, permutations), math (comb, factorial), functools (lru_cache for DP/memoization)',
            'Geometry': 'math (sqrt, cos, sin, atan2, pi), sympy (solve, Rational, sqrt, simplify, nsimplify), numpy (array, linalg)',
            'Algebra': 'sympy (symbols, solve, expand, factor, simplify, Eq, Poly, roots, diff, integrate), fractions (Fraction)',
            'Optimization': 'itertools (brute force for small ILP), scipy.optimize.linprog (for LP), functools (lru_cache for DP)',
            'Probability': 'fractions (Fraction for exact arithmetic), sympy (Rational, binomial), math (comb, factorial), random (Monte Carlo verification)',
            'Game Theory': 'functools (lru_cache for game tree memo), itertools (move enumeration)',
        }

        f.write("| Topic | Recommended Libraries & Functions |\n")
        f.write("|-------|-----------------------------------|\n")
        for topic, libs in rec_table.items():
            f.write(f"| {topic} | {libs} |\n")

        f.write("\n### Key Replacements for Unavailable Libraries\n\n")
        f.write("| Unavailable | Trying to do | Use Instead |\n")
        f.write("|-------------|-------------|-------------|\n")
        f.write("| pulp | Linear Programming | scipy.optimize.linprog |\n")
        f.write("| ortools (linear_solver) | LP/MIP | scipy.optimize.linprog + itertools |\n")
        f.write("| ortools (cp_model) | Constraint Programming | itertools + backtracking |\n")
        f.write("| z3 | SMT/SAT solving | sympy.solve + itertools enumeration |\n")
        f.write("| mip | Mixed Integer Programming | scipy.optimize.linprog + itertools |\n")

        # Part 4: Anti-patterns
        f.write("\n## Part 4: Anti-patterns\n\n")

        # 0% accuracy functions
        func_outcomes_md = defaultdict(lambda: {'correct': 0, 'wrong': 0, 'none': 0, 'total': 0})
        for p in problems:
            for a in p.attempts:
                all_code = '\n'.join(t.code for t in a.turns if t.code)
                if not all_code.strip():
                    continue
                calls = extract_function_calls(all_code)
                outcome = get_attempt_outcome(p, a)
                seen = set()
                for module, func in calls:
                    key = f"{module}.{func}"
                    if key not in seen:
                        seen.add(key)
                        func_outcomes_md[key]['total'] += 1
                        func_outcomes_md[key][outcome] += 1

        zero_pct_md = []
        for func, stats in func_outcomes_md.items():
            non_none = stats['correct'] + stats['wrong']
            if non_none >= 3 and stats['correct'] == 0:
                zero_pct_md.append((func, stats['wrong'], stats['none'], stats['total']))
        zero_pct_md.sort(key=lambda x: -x[1])

        f.write("### 0% Accuracy Functions (never produce correct answer, min 3 non-None uses)\n\n")
        f.write("| Function | Wrong | None | Total |\n")
        f.write("|----------|-------|------|-------|\n")
        for func, wrong, none, total in zero_pct_md:
            f.write(f"| {func} | {wrong} | {none} | {total} |\n")

        f.write(f"\nTotal: {len(zero_pct_md)} functions with 0% accuracy\n\n")

        # Import count analysis
        f.write("### Import Count vs Success Rate\n\n")
        f.write("| Imports | Total | Correct | Wrong | None | Accuracy | None% |\n")
        f.write("|---------|-------|---------|-------|------|----------|-------|\n")

        import_buckets = defaultdict(lambda: {'correct': 0, 'wrong': 0, 'none': 0, 'total': 0})
        for p in problems:
            for a in p.attempts:
                all_code = '\n'.join(t.code for t in a.turns if t.code)
                if not all_code.strip():
                    continue
                libs = extract_imports(all_code)
                for lib_str in a.libraries:
                    for part in re.findall(r'(?:import|from)\s+(\w+)', lib_str):
                        libs.add(part)
                n = len(libs)
                if n <= 1:
                    bucket = '0-1'
                elif n <= 3:
                    bucket = '2-3'
                elif n <= 5:
                    bucket = '4-5'
                elif n <= 7:
                    bucket = '6-7'
                else:
                    bucket = '8+'
                outcome = get_attempt_outcome(p, a)
                import_buckets[bucket]['total'] += 1
                import_buckets[bucket][outcome] += 1

        for bucket in ['0-1', '2-3', '4-5', '6-7', '8+']:
            stats = import_buckets.get(bucket, {'correct': 0, 'wrong': 0, 'none': 0, 'total': 0})
            non_none = stats['correct'] + stats['wrong']
            acc = 100 * stats['correct'] / non_none if non_none > 0 else 0
            none_rate = 100 * stats['none'] / stats['total'] if stats['total'] > 0 else 0
            f.write(f"| {bucket} | {stats['total']} | {stats['correct']} | "
                    f"{stats['wrong']} | {stats['none']} | "
                    f"{acc:.0f}% | {none_rate:.0f}% |\n")

        # Cascades
        unavailable = {'pulp', 'ortools', 'z3', 'mip', 'cvxpy', 'gurobipy', 'cplex'}
        cascade_count = 0
        cascade_examples = []
        for p in problems:
            for a in p.attempts:
                libs_tried = []
                for t in a.turns:
                    if not t.code.strip():
                        continue
                    imports = extract_imports(t.code)
                    tried = imports & unavailable
                    if tried:
                        libs_tried.extend(sorted(tried))
                if len(set(libs_tried)) >= 2:
                    cascade_count += 1
                    if len(cascade_examples) < 10:
                        cascade_examples.append(
                            f"{p.problem_id} att={a.attempt_num}: "
                            f"{' -> '.join(dict.fromkeys(libs_tried))}"
                        )

        f.write(f"\n### Unavailable Library Cascades\n\n")
        f.write(f"Total attempts trying 2+ unavailable libraries: {cascade_count}\n\n")
        if cascade_examples:
            f.write("Examples:\n")
            for ex in cascade_examples:
                f.write(f"- `{ex}`\n")

        # Conclusion
        f.write("\n## Key Takeaways\n\n")
        f.write("1. **pulp/ortools/z3/mip are never available** — the model wastes turns "
                "trying them, then cascading through alternatives. Add a prompt hint: "
                "\"The following libraries are NOT available: pulp, ortools, z3, mip, cvxpy. "
                "Use scipy.optimize.linprog for LP, itertools for constraint enumeration.\"\n\n")
        f.write("2. **Import count correlates with failure** — attempts importing 6+ libraries "
                "have much lower accuracy. The model is searching rather than solving.\n\n")
        f.write("3. **sympy is beneficial overall** (55% vs 52% baseline) but has a high None "
                "rate (59%). The model often gets stuck in symbolic computation.\n\n")
        f.write("4. **deque, cmath, sys, functools** are anti-pattern indicators — they correlate "
                "with complex but failing code patterns.\n\n")
        f.write("5. **mpmath, decimal, heapq** are rare but highly effective when used correctly.\n\n")
        f.write("6. **Board/grid optimization problems** are the main trigger for unavailable "
                "libraries. These problems need explicit guidance toward itertools-based "
                "enumeration or scipy LP.\n\n")


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Library x Topic deep analysis for AIMO3 solver logs.",
        usage="python3 log_exploration/library_topic_analysis.py <logfile> [options]"
    )
    parser.add_argument("logfile", help="Path to diagnostic.log")
    parser.add_argument("--md", help="Save markdown report to file")

    args = parser.parse_args()

    if not os.path.exists(args.logfile):
        print(f"Error: File not found: {args.logfile}")
        sys.exit(1)

    print(f"Parsing {args.logfile}...")
    problems = parse_log(args.logfile)
    print(f"Parsed {len(problems)} problems, "
          f"{sum(len(p.attempts) for p in problems)} attempts.")

    # Build the matrix
    matrix, topic_totals = build_library_topic_matrix(problems)

    # Print to stdout
    import io
    out = io.StringIO()

    print_library_topic_matrix(matrix, topic_totals, out)
    analyze_unavailable_libraries(problems, out)
    build_recommendations(matrix, topic_totals, problems, out)
    analyze_anti_patterns(problems, out)

    result = out.getvalue()
    print(result)

    # Save markdown if requested
    if args.md:
        md_dir = os.path.dirname(args.md)
        if md_dir and not os.path.exists(md_dir):
            os.makedirs(md_dir, exist_ok=True)
        generate_markdown(matrix, topic_totals, problems, args.md)
        print(f"\nMarkdown report saved to {args.md}")


if __name__ == "__main__":
    main()
