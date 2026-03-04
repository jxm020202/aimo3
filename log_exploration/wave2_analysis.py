#!/usr/bin/env python3
"""
Wave 2 Starter Notes Analysis
==============================
Analyzes consistently wrong problems from v23 and v31 to identify:
- Problem topic/type
- Approaches tried by the model
- Why they failed
- What might work instead

Usage:
    python3 log_exploration/wave2_analysis.py output/v23/diagnostic.log output/v31/diagnostic.log
"""

import sys
import re
from collections import Counter, defaultdict

sys.path.insert(0, '.')
from log_exploration.log_query import parse_log


def classify_topic(problem_text):
    """Classify problem into topic based on text content."""
    text = problem_text.lower() if problem_text else ""

    geo_kw = ['triangle', 'circle', 'angle', 'perpendicular', 'tangent', 'inscribed',
              'circumscribed', 'polygon', 'quadrilateral', 'area', 'perimeter',
              'circumcircle', 'incircle', 'midpoint', 'bisector', 'parallel',
              'equilateral', 'hexagon', 'pentagon', 'rectangle', 'square grid',
              'convex', 'diameter', 'chord', 'collinear', 'concyclic', 'observer',
              'lattice point']

    nt_kw = ['divisor', 'prime', 'gcd', 'lcm', 'modulo', 'remainder', 'congruent',
             'coprime', 'factorial', 'divides', 'divisible',
             'digit', 'sum of digits', 'number of positive', 'perfect square',
             'perfect cube', 'norwegian', 'euler', 'fermat', 'complex numbers',
             'root of unity']

    comb_kw = ['permutation', 'ways', 'arrange', 'select', 'choose',
               'subset', 'count', 'board', 'tile', 'domino',
               'coloring', 'colour', 'color', 'path', 'walk', 'game', 'player',
               'coin', 'flip', 'probability', 'expected', 'blackboard',
               'chessboard', 'placement', 'configuration', 'dice', 'maze',
               'marked', 'graph', 'simple graph', 'vertex']

    alg_kw = ['polynomial', 'equation', 'root', 'function', 'inequality',
              'maximum', 'minimum', 'recurrence',
              'real number', 'coefficient', 'degree', 'evaluate',
              'expression', 'formula', 'grid of cells']

    scores = {
        'geometry': sum(1 for kw in geo_kw if kw in text),
        'number_theory': sum(1 for kw in nt_kw if kw in text),
        'combinatorics': sum(1 for kw in comb_kw if kw in text),
        'algebra': sum(1 for kw in alg_kw if kw in text),
    }

    if max(scores.values()) == 0:
        return 'unknown'
    return max(scores, key=scores.get)


def classify_strategy(attempt):
    """Classify what strategy an attempt used based on code content."""
    strategies = []
    all_code = ""
    for turn in attempt.turns:
        if turn.code:
            all_code += turn.code + "\n"

    if not all_code:
        return ['pure_reasoning']

    code_lower = all_code.lower()

    if any(kw in code_lower for kw in ['brute', 'itertools', 'combinations(', 'permutations(', 'product(']):
        strategies.append('brute_force')
    if 'for ' in code_lower and 'range(' in code_lower:
        strategies.append('enumeration')
    if any(kw in code_lower for kw in ['sympy', 'solve(', 'symbols(', 'simplify', 'factor(']):
        strategies.append('symbolic_computation')
    if any(kw in code_lower for kw in ['numpy', 'scipy', 'matrix', 'linalg']):
        strategies.append('numerical')
    if any(kw in code_lower for kw in ['@cache', '@lru_cache', 'functools', 'memo']):
        strategies.append('dynamic_programming')
    if any(kw in code_lower for kw in ['backtrack', 'dfs(', 'bfs(', 'def search']):
        strategies.append('search_algorithm')
    if 'z3' in code_lower or 'Solver()' in code_lower:
        strategies.append('constraint_solver')
    if any(kw in code_lower for kw in ['mod ', '% ', 'pow(', 'gcd(', 'lcm(', 'isprime', 'sieve', 'factorize']):
        strategies.append('number_theory_tools')
    if any(kw in code_lower for kw in ['random', 'sample(', 'monte']):
        strategies.append('monte_carlo')
    if any(kw in code_lower for kw in ['ilp', 'milp', 'pulp', 'ortools', 'linear_prog']):
        strategies.append('optimization_solver')

    return strategies if strategies else ['basic_computation']


def classify_failure(attempt, expected):
    """Classify why an attempt failed."""
    reasons = []

    if attempt.answer is None or attempt.is_none:
        # Check turns for timeout evidence
        has_timeout = False
        for turn in attempt.turns:
            if turn.is_error and turn.output and 'timeout' in str(turn.output).lower():
                has_timeout = True
            if turn.is_error and turn.output and 'time' in str(turn.output).lower():
                has_timeout = True
        if has_timeout:
            reasons.append('timeout')
        elif attempt.errors > 3:
            reasons.append('too_many_errors')
        elif attempt.errors > 0:
            reasons.append('code_error')
        else:
            reasons.append('no_answer_extracted')
        return reasons

    # Got a wrong answer
    try:
        pred = int(str(attempt.answer))
        exp = int(str(expected))
        diff = abs(pred - exp)

        if diff <= 3:
            reasons.append('off_by_small')
        if pred != 0 and exp != 0:
            ratio = pred / exp
            if abs(ratio - 2.0) < 0.01 or abs(ratio - 0.5) < 0.01:
                reasons.append('factor_of_2_error')
            if abs(ratio - 3.0) < 0.01 or abs(ratio - 1/3) < 0.01:
                reasons.append('factor_of_3_error')
    except (ValueError, TypeError, ZeroDivisionError):
        pass

    # Check for errors during computation
    error_turns = sum(1 for t in attempt.turns if t.is_error)
    if error_turns > 3:
        reasons.append('many_errors_before_answer')

    # Check for timeout in turns
    for turn in attempt.turns:
        if turn.is_error and turn.output and 'timeout' in str(turn.output).lower():
            reasons.append('partial_timeout')
            break

    if not reasons:
        reasons.append('wrong_approach')

    return reasons


def extract_key_reasoning(attempts, expected, max_attempts=5):
    """Extract reasoning snippets from correct and wrong attempts."""
    correct_snippets = []
    wrong_snippets = []

    for att in attempts[:max_attempts]:
        for turn in att.turns[:3]:
            if not turn.reasoning_text:
                continue
            text = turn.reasoning_text[:500]
            if str(att.answer) == str(expected):
                correct_snippets.append(text[:200])
            else:
                wrong_snippets.append(text[:200])

    return correct_snippets[:3], wrong_snippets[:3]


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 log_exploration/wave2_analysis.py <v23_log> <v31_log>")
        sys.exit(1)

    v23 = parse_log(sys.argv[1])
    v31 = parse_log(sys.argv[2])

    v23_map = {p.problem_id: p for p in v23}
    v31_map = {p.problem_id: p for p in v31}

    v23_wrong = {p.problem_id for p in v23 if not p.correct}
    v31_wrong = {p.problem_id for p in v31 if not p.correct}
    both_wrong = v23_wrong & v31_wrong

    print(f"V23 wrong: {len(v23_wrong)}, V31 wrong: {len(v31_wrong)}, Both wrong: {len(both_wrong)}")

    by_topic = defaultdict(list)

    for pid in sorted(both_wrong):
        p31 = v31_map.get(pid)
        p23 = v23_map.get(pid)
        if not p31 and not p23:
            continue

        primary = p31 or p23
        problem_text = primary.problem_text or ''
        if not problem_text:
            for a in primary.attempts:
                for t in a.turns:
                    if t.reasoning_text and len(t.reasoning_text) > 50:
                        problem_text = t.reasoning_text[:2000]
                        break
                if problem_text:
                    break

        topic = classify_topic(problem_text)
        expected = primary.expected

        # Analyze all attempts from both versions
        strategies_correct = Counter()
        strategies_wrong = Counter()
        strategies_none = Counter()
        failure_modes = Counter()
        wrong_answers = Counter()

        for version, prob in [('v23', p23), ('v31', p31)]:
            if not prob:
                continue
            for att in prob.attempts:
                strats = classify_strategy(att)

                if att.answer is not None and str(att.answer) == str(expected):
                    for s in strats:
                        strategies_correct[s] += 1
                elif att.answer is None or att.is_none:
                    for s in strats:
                        strategies_none[s] += 1
                    for f in classify_failure(att, expected):
                        failure_modes[f] += 1
                else:
                    for s in strats:
                        strategies_wrong[s] += 1
                    for f in classify_failure(att, expected):
                        failure_modes[f] += 1
                    if att.answer is not None:
                        wrong_answers[str(att.answer)] += 1

        correct_v23 = sum(1 for a in p23.attempts if str(a.answer) == str(p23.expected)) if p23 else 0
        correct_v31 = sum(1 for a in p31.attempts if str(a.answer) == str(p31.expected)) if p31 else 0

        info = {
            'pid': pid,
            'topic': topic,
            'problem_text': problem_text[:300],
            'expected': expected,
            'v23_pred': p23.predicted if p23 else '?',
            'v31_pred': p31.predicted if p31 else '?',
            'correct_v23': correct_v23,
            'correct_v31': correct_v31,
            'total_v23': len(p23.attempts) if p23 else 0,
            'total_v31': len(p31.attempts) if p31 else 0,
            'strategies_correct': strategies_correct,
            'strategies_wrong': strategies_wrong,
            'strategies_none': strategies_none,
            'failure_modes': failure_modes,
            'wrong_answers': wrong_answers.most_common(5),
            'v31_votes': dict(p31.votes) if p31 and p31.votes else {},
            'v23_votes': dict(p23.votes) if p23 and p23.votes else {},
        }
        by_topic[topic].append(info)

    # Print results
    for topic, problems in sorted(by_topic.items()):
        print(f"\n{'='*80}")
        print(f"TOPIC: {topic.upper()} ({len(problems)} problems)")
        print(f"{'='*80}")

        for info in problems:
            print(f"\n  --- Problem {info['pid']} (expected={info['expected']}) ---")
            print(f"  Text: {info['problem_text'][:200]}...")
            print(f"  V23: pred={info['v23_pred']}, correct={info['correct_v23']}/{info['total_v23']}")
            print(f"  V31: pred={info['v31_pred']}, correct={info['correct_v31']}/{info['total_v31']}")
            print(f"  Top wrong answers: {info['wrong_answers']}")
            print(f"  Failure modes: {dict(info['failure_modes'])}")

            if info['strategies_correct']:
                print(f"  WINNING strategies: {dict(info['strategies_correct'])}")
            print(f"  LOSING strategies: {dict(info['strategies_wrong'])}")
            if info['strategies_none']:
                print(f"  NONE strategies: {dict(info['strategies_none'])}")

        # Topic aggregates
        all_fail = Counter()
        all_strat_w = Counter()
        all_strat_c = Counter()
        outvoted = 0
        for info in problems:
            all_fail.update(info['failure_modes'])
            all_strat_w.update(info['strategies_wrong'])
            all_strat_c.update(info['strategies_correct'])
            if info['correct_v23'] > 0 or info['correct_v31'] > 0:
                outvoted += 1

        print(f"\n  === TOPIC AGGREGATE ===")
        print(f"  Problems with >=1 correct attempt (outvoted): {outvoted}/{len(problems)}")
        print(f"  Top failure modes: {all_fail.most_common(5)}")
        print(f"  Failing strategies: {all_strat_w.most_common(5)}")
        if all_strat_c:
            print(f"  Working strategies: {all_strat_c.most_common(5)}")


if __name__ == '__main__':
    main()
