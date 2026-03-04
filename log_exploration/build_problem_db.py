#!/usr/bin/env python3
"""
Build a structured problem database from AIMO3 diagnostic logs.

Extracts all wrong problems and close-vote problems from v23 and v31,
with full problem text, topic tags, failure analysis, and approach hints.

Usage:
    python3 log_exploration/build_problem_db.py
"""

import sys
import os
import re
import json
import csv
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


# ── Full problem text extraction (bypasses 300-char truncation) ──────────────

def extract_full_problem_texts(filepath: str) -> dict:
    """Extract full problem texts from raw log, keyed by problem_id."""
    with open(filepath, 'r', errors='replace') as f:
        content = f.read()

    lines = content.split('\n')
    texts = {}
    current_pid = None
    in_problem_text = False
    text_buf = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect problem header
        prob_match = re.match(r'\s*\[(\d+)/(\d+)\]\s*Problem\s+(?:id=)?(\w+)', stripped)
        if prob_match:
            # Save previous if collecting
            if current_pid and text_buf:
                full_text = ' '.join(text_buf).strip()
                if current_pid not in texts or len(full_text) > len(texts.get(current_pid, '')):
                    texts[current_pid] = full_text
            current_pid = prob_match.group(3)
            in_problem_text = False
            text_buf = []
            continue

        # Detect problem text start
        if stripped.startswith('Problem:') and current_pid:
            in_problem_text = True
            text_buf = [stripped[8:].strip()]
            continue

        # Continue collecting problem text (multi-line)
        if in_problem_text and current_pid:
            # Stop conditions: Budget line, ATTEMPT line, blank line after content, or other structural markers
            if (stripped.startswith('Budget:') or
                stripped.startswith('ATTEMPT ') or
                stripped.startswith('--- Attempt') or
                stripped.startswith('STATUS:') or
                stripped.startswith('Final Answer:') or
                stripped.startswith('Predicted:') or
                stripped.startswith('Votes:') or
                stripped.startswith('[') and re.match(r'\[\d+/\d+\]', stripped) or
                stripped == ''):
                if text_buf:
                    full_text = ' '.join(text_buf).strip()
                    if current_pid not in texts or len(full_text) > len(texts.get(current_pid, '')):
                        texts[current_pid] = full_text
                in_problem_text = False
                text_buf = []
            else:
                text_buf.append(stripped)

    # Don't forget last one
    if current_pid and text_buf:
        full_text = ' '.join(text_buf).strip()
        if current_pid not in texts or len(full_text) > len(texts.get(current_pid, '')):
            texts[current_pid] = full_text

    return texts


def load_val_bench_texts(base_dir: str) -> dict:
    """Load full problem texts from the val bench CSV."""
    csv_path = os.path.join(base_dir, 'data/available/aimo3-val-bench/aimo3_val.csv')
    texts = {}
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row.get('id', '')
                problem = row.get('problem', '')
                if pid and problem:
                    texts[pid] = problem
    return texts


def load_hard_benchmark_texts(base_dir: str) -> dict:
    """Load full problem texts from the hard benchmark CSV."""
    csv_path = os.path.join(base_dir, 'data/available/hard_benchmark_30.csv')
    texts = {}
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row.get('id', '')
                problem = row.get('problem', row.get('question', ''))
                if pid and problem:
                    texts[pid] = problem
    return texts


def extract_problem_text_from_conversation(filepath: str, problem_id: str) -> str:
    """Extract problem text from the conversation/reasoning of the first attempt.

    The system prompt sent to the model contains the full problem text.
    Look for it in the reasoning of Turn 1 of Attempt 1.
    """
    with open(filepath, 'r', errors='replace') as f:
        content = f.read()

    lines = content.split('\n')
    found_problem = False
    found_attempt = False
    in_reasoning = False
    reasoning_buf = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Find the problem section
        if re.match(rf'\s*\[(\d+)/(\d+)\]\s*Problem\s+(?:id=)?{problem_id}', stripped):
            found_problem = True
            continue

        if not found_problem:
            continue

        # Next problem starts — we're done
        if re.match(r'\s*\[(\d+)/(\d+)\]\s*Problem\s+(?:id=)?(\w+)', stripped) and found_problem:
            break

        # Find first attempt's reasoning
        if 'ATTEMPT 1' in stripped or '--- Attempt 1' in stripped or '--- Attempt  1' in stripped:
            found_attempt = True
            continue

        if found_attempt and (stripped.startswith('REASONING (') or stripped.startswith('[Turn ')):
            in_reasoning = True
            reasoning_buf = []
            continue

        if in_reasoning:
            # Stop at code block or next section
            if stripped.startswith('CODE:') or stripped.startswith('OUTPUT:') or stripped.startswith('ATTEMPT ') or stripped.startswith('--- Attempt'):
                break
            reasoning_buf.append(stripped)

    # Search reasoning for problem text patterns
    full_reasoning = '\n'.join(reasoning_buf)

    # Look for the problem text in reasoning — it's usually quoted
    # The model often repeats the problem statement
    return full_reasoning[:5000] if reasoning_buf else ""


# ── Topic classification ─────────────────────────────────────────────────────

def classify_topics(problem_text: str, problem_id: str) -> list:
    """Classify problem into topic tags based on text content."""
    text = problem_text.lower()
    topics = []

    # Number theory
    nt_keywords = ['divisor', 'prime', 'modulo', 'gcd', 'lcm', 'remainder', 'congruent',
                   'coprime', 'euler', 'fermat', 'norwegian', 'divisible', 'factors',
                   'roots of unity', 'complex number', 'cyclotomic', 'multiplicative']
    if any(kw in text for kw in nt_keywords):
        topics.append('number_theory')

    # Combinatorics
    comb_keywords = ['board', 'grid', 'game', 'player', 'dice', 'domino', 'tile', 'coin',
                     'maze', 'graph', 'vertex', 'vertices', 'edge', 'color', 'path',
                     'placement', 'counting', 'arrange', 'permutation', 'combination',
                     'sequence', 'subset', 'ways', 'choose', 'select', 'cards', 'balls',
                     'boxes', 'distribute', 'bijection', 'marked', 'cells', 'adjacent',
                     'walk', 'flip', 'column', 'row']
    if any(kw in text for kw in comb_keywords):
        topics.append('combinatorics')

    # Geometry
    geom_keywords = ['polygon', 'circle', 'angle', 'triangle', 'bisector', 'perpendicular',
                     'convex', 'diagonal', 'lattice point', 'observer', 'viewing',
                     'constructib', 'compass', 'straightedge', 'inscribed', 'circumscribed',
                     'tangent', 'parallel', 'distance', 'area', 'perimeter', 'chord',
                     'trapezoid', 'isosceles']
    if any(kw in text for kw in geom_keywords):
        topics.append('geometry')

    # Algebra
    alg_keywords = ['function', 'equation', 'inequality', 'polynomial', 'recurrence',
                    'maximize', 'minimize', 'maximum', 'minimum', 'optimal', 'sum',
                    'product', 'floor', 'ceiling', 'real number', 'positive integer',
                    'sequence', 'series', 'limit', 'continuous', 'differentiable']
    if any(kw in text for kw in alg_keywords):
        topics.append('algebra')

    # Optimization
    opt_keywords = ['maximize', 'minimize', 'maximum', 'minimum', 'optimal', 'largest',
                    'smallest', 'greatest', 'least', 'extremal', 'bound']
    if any(kw in text for kw in opt_keywords):
        topics.append('optimization')

    # Game theory
    game_keywords = ['game', 'player', 'strategy', 'win', 'lose', 'turn', 'move',
                     'alice', 'bob', 'opponent', 'optimal play', 'minimax']
    if any(kw in text for kw in game_keywords):
        topics.append('game_theory')

    # Graph theory
    graph_keywords = ['graph', 'vertex', 'vertices', 'edge', 'degree', 'connected',
                      'path', 'cycle', 'tree', 'matching', 'coloring', 'chromatic',
                      'clique', 'independent set', 'bipartite', 'neighbor']
    if any(kw in text for kw in graph_keywords):
        topics.append('graph_theory')

    # Probability
    prob_keywords = ['probability', 'expected', 'random', 'dice', 'fair', 'independently',
                     'distribution', 'uniform', 'bernoulli']
    if any(kw in text for kw in prob_keywords):
        topics.append('probability')

    # Additional catch-all patterns
    if 'integer' in text and ('a_1' in text or 'a_2' in text or 'a_{' in text):
        if 'algebra' not in topics:
            topics.append('algebra')
    if 'complex' in text and ('z^' in text or 'z^{' in text):
        if 'algebra' not in topics:
            topics.append('algebra')
        if 'number_theory' not in topics:
            topics.append('number_theory')
    if 'satisfying' in text and ('leq' in text or '\\leq' in text):
        if 'algebra' not in topics:
            topics.append('algebra')
    if 'stones' in text or 'chess' in text or 'piece' in text:
        if 'combinatorics' not in topics:
            topics.append('combinatorics')

    if not topics:
        topics.append('unknown')

    # Apply per-problem topic overrides
    topic_overrides = {
        '89c921': ['algebra', 'optimization'],
        '32690e': ['algebra', 'number_theory'],
        'dbbfe8': ['combinatorics', 'optimization'],
        'a824c1': ['combinatorics', 'geometry', 'optimization'],
        '673b29': ['combinatorics', 'game_theory'],
        '23586c': ['geometry', 'number_theory'],
        '3b88b3': ['algebra', 'optimization'],
        '414a5b': ['probability', 'combinatorics'],
        'a9dbc8': ['combinatorics', 'probability'],
        '9010d9': ['graph_theory', 'combinatorics', 'optimization'],
        '3980cd': ['number_theory', 'algebra'],
        '86e8e5': ['number_theory'],
        '1ec970': ['geometry', 'combinatorics', 'optimization'],
        'ae2add': ['geometry', 'combinatorics', 'number_theory'],
        'aff75c': ['combinatorics', 'optimization', 'algebra'],
        '29714f': ['algebra', 'combinatorics'],
        '26bee3': ['geometry', 'combinatorics', 'graph_theory'],
        '21fb4e': ['combinatorics', 'game_theory', 'optimization'],
        '76aef9': ['game_theory', 'number_theory', 'combinatorics'],
        'c19295': ['combinatorics', 'optimization'],
        '581a58': ['combinatorics', 'number_theory'],
        'dd7f5e': ['algebra', 'number_theory'],
        '27cec1': ['algebra', 'optimization'],
        '19570e': ['combinatorics', 'graph_theory'],
        '485d27': ['combinatorics', 'optimization'],
        '53de2d': ['algebra', 'number_theory'],
        '1363c5': ['geometry', 'combinatorics'],
        'cbbc1b': ['algebra', 'optimization'],
    }
    pid_prefix = problem_id[:6] if len(problem_id) >= 6 else problem_id
    if pid_prefix in topic_overrides:
        topics = topic_overrides[pid_prefix]

    return list(set(topics))


# ── Failure mode classification ──────────────────────────────────────────────

def classify_failure(problem, all_attempts_across_versions: list) -> str:
    """Classify the failure mode based on attempt patterns."""
    pid = problem.problem_id
    expected = problem.expected

    # Count how many attempts got the right answer across all versions
    correct_count = sum(1 for a in all_attempts_across_versions if a.answer == expected)
    total_count = len(all_attempts_across_versions)

    if correct_count == 0:
        # Check if ALL attempts gave the same wrong answer
        non_none_answers = [a.answer for a in all_attempts_across_versions if a.answer is not None]
        if non_none_answers:
            most_common = Counter(non_none_answers).most_common(1)[0]
            if most_common[1] == len(non_none_answers):
                return 'wrong_formula'  # Systematic error — same wrong answer every time
            if most_common[1] >= len(non_none_answers) * 0.7:
                return 'wrong_formula'  # Strong convergence to wrong answer

        # Check for timeout-dominated
        timeout_count = sum(1 for a in all_attempts_across_versions if a.is_none)
        if timeout_count >= total_count * 0.5:
            return 'timeout'

        return 'never_correct'

    if correct_count <= 3:
        # Got it sometimes but outvoted
        return 'outvoted'

    if correct_count <= total_count * 0.3:
        return 'outvoted'

    return 'outvoted'


# ── Known problem data from wave2_starter_notes.md ───────────────────────────

KNOWN_PROBLEMS = {
    'dbbfe8': {
        'expected_answer': 22,
        'skills': 'domino tiling on 7x7 board, proving minimum via mutual blocking, lower bound arguments',
        'failure_mode': 'brute_force_fail',
        'common_wrong_answer': 8,
        'approach': 'Dominos must block EACH OTHER, not just touch walls. Prove a lower bound via counting argument first, then construct a matching configuration. Never trust computer search that says "found k" without proving k is minimal. Answer is 22, not 8.',
    },
    'a824c1': {
        'expected_answer': 24,
        'skills': 'bishop coverage on 13x13 board, diagonal line covering, set cover optimization',
        'failure_mode': 'never_correct',
        'common_wrong_answer': 13,
        'approach': 'Bishop covers BOTH diagonals simultaneously. Need to hit all 49 diagonal lines on a 13x13 board. One bishop per row is NOT sufficient because bishops threaten both directions. Answer is 24, not 13. Prove lower bound via diagonal counting.',
    },
    '673b29': {
        'expected_answer': 3,
        'skills': 'maze traversal strategy, binary search on columns, logarithmic complexity arguments',
        'failure_mode': 'wrong_formula',
        'common_wrong_answer': 3032,
        'approach': 'The maze answer is logarithmic (3), NOT linear (3032). Use binary-search strategy on columns. 15/16 attempts pure-reason to 3032 without code verification. ALWAYS simulate small cases first. The model confuses the number of columns with the answer.',
    },
    '23586c': {
        'expected_answer': 386,
        'skills': 'geometric constructibility, compass and straightedge with m-section, affine operations on constructible numbers',
        'failure_mode': 'never_correct',
        'common_wrong_answer': 773,
        'approach': 'Not just 105-divisibility. The centroid constructibility condition is more nuanced than "prime factors of 735 divide m". Affine combinations with m-section create richer constructibility. Answer is 386, not 773 (which is roughly 2x). Consider what denominators can be built.',
    },
    '3b88b3': {
        'expected_answer': 979,
        'skills': 'constrained optimization with floor function, critical point analysis, boundary case checking',
        'failure_mode': 'wrong_formula',
        'common_wrong_answer': 982,
        'approach': 'ALL attempts derive f(k)=k^2/sqrt(k^2-1) which gives S=982. This satisfies Monte Carlo but is WRONG — it finds a local max, not global. Check ALL boundary cases: z=0, x=0, y=0, and all KKT conditions. True floor(S)=979. A clean integer from optimization is suspicious.',
    },
    '414a5b': {
        'expected_answer': 42,
        'skills': 'dice probability, conditional computation for specific parameter value, careful problem reading',
        'failure_mode': 'misread_problem',
        'common_wrong_answer': 95,
        'approach': 'Problem asks for 216*p when n=2 SPECIFICALLY, not the overall optimal probability. Model computes overall optimal (95/216) when problem asks specifically for the n=2 case (42/216). Re-read the problem: what EXACTLY is being asked for?',
    },
    'a9dbc8': {
        'expected_answer': 15744,
        'skills': 'coin flipping walk, boundary counting, inclusion/exclusion of endpoints',
        'failure_mode': 'off_by_one',
        'common_wrong_answer': 15743,
        'approach': 'Off-by-1 in walk/flip count. Model consistently gets 15743 instead of 15744. Boundary condition error — miscounting whether first/last move is included. Test formula on small cases (n=3, n=5, n=7) before extrapolating to n=7873.',
    },
    '9010d9': {
        'expected_answer': 10320,
        'skills': 'graph theory, private neighbor condition, extremal graph theory',
        'failure_mode': 'wrong_formula',
        'common_wrong_answer': 6400,
        'approach': 'Max edges where each vertex has a private neighbor. Model defaults to Turan-like n^2/4=6400 but the private neighbor constraint changes the structure. Answer is 10320. Need to carefully construct the extremal graph satisfying the private neighbor property.',
    },
    '3980cd': {
        'expected_answer': 46,
        'skills': 'cyclotomic polynomials, roots of unity products, deep number theory',
        'failure_mode': 'outvoted',
        'common_wrong_answer': 642,
        'approach': 'Product of (r_k^e + 1) = 1 for e=1..m with 645 complex numbers. Model gets 642 (=645-3) — wrong structural guess. Real answer is 46 (mod 848). Requires deep number theory about cyclotomic polynomials. NOT a simple "count prime factors" problem.',
    },
    '86e8e5': {
        'expected_answer': 8687,
        'skills': 'n-Norwegian numbers, divisor sum properties, extended computation with many turns',
        'failure_mode': 'outvoted',
        'common_wrong_answer': None,  # scattered
        'approach': 'n-Norwegian = three divisors summing to n. Requires computing over huge ranges. Attempts get wildly scattered wrong answers — no consensus. Correct attempts used 100+ turns of extended computation. The correct approach uses number-theoretic properties of divisor sums.',
    },
    '1ec970': {
        'expected_answer': 8700,
        'skills': 'viewing angle geometry, constrained observer placement, non-trivial extremal bound',
        'failure_mode': 'never_correct',
        'common_wrong_answer': 9900,
        'approach': '100 observers with 100-degree viewing angles. Model claims 9900=100*99 (all pairs see each other) but this is wrong. The answer 8700 < 9900 means some pairs CANNOT see each other under the constraint. "Each observer has a viewing angle" likely means fixed direction, not choosable.',
    },
    'ae2add': {
        'expected_answer': 24931,
        'skills': 'lattice point selection, isosceles trapezoid avoidance, point set construction',
        'failure_mode': 'wrong_formula',
        'common_wrong_answer': 19945,
        'approach': 'Lattice points avoiding isosceles trapezoids. Model gets 19945=2*9973-1, but answer is 24931~=2.5*9973. The construction allows more points than the model thinks — each row can have ~2.5 points on average. Wrong approach: treating horizontal and vertical constraints independently.',
    },
    'aff75c': {
        'expected_answer': 3571,
        'skills': 'grid filling optimization, adjacent sum maximization, averaging/parity arguments',
        'failure_mode': 'outvoted',
        'common_wrong_answer': 3600,
        'approach': '60x60 grid with 1..3600, maximize minimum adjacent sum S. Model gets 3600 (too optimistic) or timeout. Answer 3571 = 3600-29 requires clever arrangement theory. Think checkerboard: alternate high/low values. Use averaging argument over all adjacencies.',
    },
    '29714f': {
        'expected_answer': 297,
        'skills': 'functional equation enumeration, domain counting, 3-fold symmetric structure',
        'failure_mode': 'outvoted',
        'common_wrong_answer': 99,
        'approach': 'g: NxN->N with g(0,0)=0 and recursive structure. Model gets 99 (expected 297=3*99) — consistent factor-of-3 error. Likely misinterprets the domain or counts only 1/3 of function values. Enumerate g(x,y) for small x,y. Check if recurrence generates 3-fold symmetric structure.',
    },
    '26bee3': {
        'expected_answer': 108,
        'skills': 'directed diagonals on grid, graph modeling of grid geometry, extremal counting',
        'failure_mode': 'outvoted',
        'common_wrong_answer': 97,
        'approach': 'Directed diagonals in 16x16 grid. Model gets various wrong answers (97, 136, 256). Answer is 108 = 4*27 or 12*9. Model the problem as a directed graph on grid diagonals. Draw small cases (4x4, 8x8) and look for the pattern. The answer factors nicely.',
    },
    '89c921': {
        'expected_answer': 29800,
        'skills': 'quadratic form minimization over integer sequences, telescoping sums, consecutive difference analysis',
        'failure_mode': 'outvoted',
        'common_wrong_answer': 39601,
        'approach': 'Minimize f = sum(a_i^2) - sum(a_i*a_{i+2}) for non-decreasing integers from 1 to 199. Model gets 39601=199^2 which is a Turan-type bound, but the shifted product term changes the structure. Think about the sum as related to consecutive differences. Answer 29800 = 199*150 - something. Careful algebraic manipulation needed.',
    },
    '21fb4e': {
        'expected_answer': 16,
        'skills': 'five-in-a-row blocking on 9x9 board, extremal combinatorics, constructive placement',
        'failure_mode': 'outvoted',
        'common_wrong_answer': 17,
        'approach': 'Minimum black stones to block all possible five-in-a-row on 9x9 board. Model gets 17 but answer is 16. Need to find an efficient blocking configuration. Count all lines of 5 (horizontal, vertical, diagonal) and find minimum hitting set. Off-by-one in the counting of required blockers.',
    },
    # Close-vote problems — at risk of flipping wrong
    '76aef9': {
        'expected_answer': 8,
        'skills': 'number replacement game, game theory, Sprague-Grundy analysis, invariant finding',
        'failure_mode': 'close_vote',
        'common_wrong_answer': 999,
        'approach': 'Game where players replace numbers on blackboard (1997 copies of 1). Close vote between 8 and 999. The game likely has a Sprague-Grundy value or invariant. Need to verify small cases to determine the correct answer.',
    },
    'dd7f5e': {
        'expected_answer': 160,
        'skills': 'functional analysis, integer sequences with finite support, composition of functions',
        'failure_mode': 'close_vote',
        'common_wrong_answer': 80,
        'approach': 'Functions Z->Z with finitely many non-zero values. Close vote between 160, 44, and 80. Need careful counting of the function space under the given constraints. Multiple wrong approaches give different answers.',
    },
    '19570e': {
        'expected_answer': 224,
        'skills': 'icosahedron edge labeling, graph automorphisms, Burnside lemma',
        'failure_mode': 'close_vote',
        'common_wrong_answer': 3,
        'approach': 'Labeling 30 edges of regular icosahedron. Close vote between 224 and 3. Need Burnside/Polya counting with the icosahedral symmetry group (order 60). Model sometimes confuses edge labelings with vertex colorings.',
    },
    '27cec1': {
        'expected_answer': 2304,
        'skills': 'minimax optimization of chained reciprocal expressions, AM-GM inequality chains',
        'failure_mode': 'close_vote',
        'common_wrong_answer': 2,
        'approach': 'Minimize max of x_1, 1/x_1+x_2, ..., chained expressions with 2025 variables. Answer 2304 = 48^2. Requires careful application of AM-GM or convexity arguments on the chain structure. Some attempts give trivially small answers.',
    },
    '32690e': {
        'expected_answer': 4050,
        'skills': 'complex polynomial root counting, argument principle, Rouche theorem',
        'failure_mode': 'close_vote',
        'common_wrong_answer': 4051,
        'approach': 'Count non-real roots of z^4051 + z^4050 + 5 = 0. Answer is 4050 (not 4051). One real root exists, so non-real count = 4051-1 = 4050. Off-by-one between total degree and non-real count. Need to verify that exactly one real root exists.',
    },
    '485d27': {
        'expected_answer': 29,
        'skills': 'coin placement on grid, pigeonhole principle, extremal board size',
        'failure_mode': 'close_vote',
        'common_wrong_answer': 3,
        'approach': 'Place 471 coins on nxn board with adjacency constraints. Answer is n=29. Close vote between 29 and 3. Need to find the minimum n such that 471 coins can be placed under the constraints. Pigeonhole or packing argument.',
    },
    '581a58': {
        'expected_answer': 18,
        'skills': 'exam scoring combinatorics, multiple choice constraint satisfaction',
        'failure_mode': 'close_vote',
        'common_wrong_answer': 0,
        'approach': 'n students, 6 questions with 3 options each, constraint on response patterns. Answer is 18. Close vote between 18 and 0. Need careful counting under the given constraints. Zero is wrong — it would mean no students can take the exam.',
    },
    'c19295': {
        'expected_answer': 48,
        'skills': 'chessboard piece placement, attacking constraints, extremal combinatorics',
        'failure_mode': 'close_vote',
        'common_wrong_answer': 18,
        'approach': '15x15 chessboard with n pieces, each attacking exactly one other. Answer is 48. Very close vote (48 vs 18 vs 36). Need to maximize n under the "exactly one attacker" constraint. Think about pairing pieces and maximizing coverage.',
    },
    '53de2d': {
        'expected_answer': 576,
        'skills': 'integer pair counting, quadratic form constraints, lattice point enumeration',
        'failure_mode': 'close_vote',
        'common_wrong_answer': 484,
        'approach': 'Count integer pairs (a,b) with a^2+b^2 <= 19 and existence of real x,y satisfying constraints. Answer is 576. Close vote between 576, 2, and 24. Need to enumerate the feasible lattice points carefully.',
    },
    'cbbc1b': {
        'expected_answer': 96,
        'skills': 'sequence optimization, ratio maximization under ordering and sum constraints',
        'failure_mode': 'close_vote',
        'common_wrong_answer': 432,
        'approach': 'Maximize ratio involving ordered reals x_1<=...<=x_9 summing to 1. Answer is 96. Close vote between 96 and 432. Need careful optimization — the maximum may occur at a boundary where some variables coincide.',
    },
    '1363c5': {
        'expected_answer': 10211,
        'skills': 'rectangle subdivision counting, combinatorial geometry, rectangle perimeter analysis',
        'failure_mode': 'close_vote',
        'common_wrong_answer': 10123,
        'approach': 'Rectangle divided into 2024 small rectangles with side-parallel constraints. Answer is 10211. Close vote between 10211, 10123, and 10124. The exact count depends on careful treatment of boundary cases in the subdivision structure.',
    },
}


# ── Main builder ─────────────────────────────────────────────────────────────

def build_problem_db():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    v23_log = os.path.join(base_dir, 'output/v23/diagnostic.log')
    v31_log = os.path.join(base_dir, 'output/v31/diagnostic.log')

    print("Parsing v23 log...")
    v23_problems = parse_log(v23_log)
    print(f"  Found {len(v23_problems)} problems")

    print("Parsing v31 log...")
    v31_problems = parse_log(v31_log)
    print(f"  Found {len(v31_problems)} problems")

    print("\nExtracting full problem texts from raw logs...")
    v23_texts = extract_full_problem_texts(v23_log)
    v31_texts = extract_full_problem_texts(v31_log)

    # Load val bench and hard benchmark as authoritative sources
    vb_texts = load_val_bench_texts(base_dir)
    hb_texts = load_hard_benchmark_texts(base_dir)
    print(f"  Val bench: {len(vb_texts)} problems, Hard benchmark: {len(hb_texts)} problems")

    # Merge texts — prefer val bench > hard benchmark > longest log version
    all_texts = {}
    for pid, text in v23_texts.items():
        if pid not in all_texts or len(text) > len(all_texts[pid]):
            all_texts[pid] = text
    for pid, text in v31_texts.items():
        if pid not in all_texts or len(text) > len(all_texts[pid]):
            all_texts[pid] = text
    # Override with benchmark sources (they have full, untruncated text)
    for pid, text in hb_texts.items():
        if text and (pid not in all_texts or len(text) > len(all_texts[pid])):
            all_texts[pid] = text
    for pid, text in vb_texts.items():
        if text and (pid not in all_texts or len(text) > len(all_texts[pid])):
            all_texts[pid] = text

    print(f"  Extracted texts for {len(all_texts)} unique problems")

    # Build per-problem data combining both versions
    # Key: problem_id (first 6 chars)
    problem_data = {}  # pid -> {v23: [Problem...], v31: [Problem...]}

    for p in v23_problems:
        pid = p.problem_id[:6]
        if pid not in problem_data:
            problem_data[pid] = {'v23': [], 'v31': [], 'expected': None}
        problem_data[pid]['v23'].append(p)
        if p.expected is not None:
            problem_data[pid]['expected'] = p.expected

    for p in v31_problems:
        pid = p.problem_id[:6]
        if pid not in problem_data:
            problem_data[pid] = {'v23': [], 'v31': [], 'expected': None}
        problem_data[pid]['v31'].append(p)
        if p.expected is not None:
            problem_data[pid]['expected'] = p.expected

    print(f"\nTotal unique problems (6-char ID): {len(problem_data)}")

    # Identify problems to include:
    # 1. Wrong in v23 or v31
    # 2. Close vote (correct but margin <= 2)
    db_entries = []

    for pid, data in sorted(problem_data.items()):
        all_probs = data['v23'] + data['v31']
        expected = data['expected']

        # Check if wrong in any version
        wrong_versions = []
        close_vote_versions = []

        for ver, probs in [('v23', data['v23']), ('v31', data['v31'])]:
            for p in probs:
                if not p.correct:
                    if ver not in wrong_versions:
                        wrong_versions.append(ver)
                elif p.correct and p.votes:
                    sorted_votes = sorted(p.votes.values(), reverse=True)
                    if len(sorted_votes) >= 2:
                        margin = sorted_votes[0] - sorted_votes[1]
                        if margin <= 2:
                            if ver not in close_vote_versions:
                                close_vote_versions.append(ver)

        if not wrong_versions and not close_vote_versions:
            continue

        # Get all attempts across all instances
        all_attempts = []
        for p in all_probs:
            all_attempts.extend(p.attempts)

        # Get full problem text
        full_pid = all_probs[0].problem_id
        question = all_texts.get(full_pid, '')
        # Also try 6-char prefix
        if not question:
            for k, v in all_texts.items():
                if k.startswith(pid):
                    question = v
                    break

        if not question:
            question = all_probs[0].problem_text  # Fallback to truncated

        # Count correct attempts
        correct_attempts = sum(1 for a in all_attempts if a.answer == expected)
        total_attempts = len(all_attempts)

        # Most common wrong answer
        non_none_wrong = [a.answer for a in all_attempts if a.answer is not None and a.answer != expected]
        if non_none_wrong:
            common_wrong = Counter(non_none_wrong).most_common(1)[0][0]
        else:
            common_wrong = None

        # Topic classification
        topics = classify_topics(question, pid)

        # Failure mode
        is_wrong = len(wrong_versions) > 0
        is_close = len(close_vote_versions) > 0 and not is_wrong

        # Use known data if available
        known = KNOWN_PROBLEMS.get(pid, {})

        if is_wrong:
            failure_mode = known.get('failure_mode', classify_failure(all_probs[0], all_attempts))
        else:
            failure_mode = 'close_vote'

        skills = known.get('skills', '')
        approach = known.get('approach', '')

        if known.get('common_wrong_answer') is not None:
            common_wrong = known['common_wrong_answer']

        if known.get('expected_answer') is not None:
            expected = known['expected_answer']

        # Override topics with known data enrichment
        if pid in KNOWN_PROBLEMS:
            # Merge in any additional topic from known hints
            pass

        entry = {
            'problem_id': pid,
            'question': question,
            'expected_answer': expected,
            'topics': topics,
            'skills': skills,
            'failure_mode': failure_mode,
            'common_wrong_answer': common_wrong,
            'approach': approach,
            'versions_wrong': wrong_versions if wrong_versions else close_vote_versions,
            'correct_rate': f"{correct_attempts}/{total_attempts}",
            'is_close_vote_only': is_close and not is_wrong,
        }

        db_entries.append(entry)

    print(f"\nProblems for DB: {len(db_entries)}")
    print(f"  Wrong problems: {sum(1 for e in db_entries if not e['is_close_vote_only'])}")
    print(f"  Close-vote only: {sum(1 for e in db_entries if e['is_close_vote_only'])}")

    return db_entries


def enrich_topics_and_skills(entries):
    """Second pass: enrich entries that lack skills/approach using problem text analysis."""
    for entry in entries:
        pid = entry['problem_id']
        text = entry['question'].lower()

        # Auto-generate skills if missing
        if not entry['skills']:
            skill_parts = []
            if 'grid' in text or 'board' in text:
                skill_parts.append('grid/board analysis')
            if 'graph' in text or 'vertex' in text or 'edge' in text:
                skill_parts.append('graph theory')
            if 'maximiz' in text or 'minimiz' in text or 'maximum' in text or 'minimum' in text:
                skill_parts.append('optimization')
            if 'prime' in text or 'divisor' in text or 'divides' in text:
                skill_parts.append('number theory')
            if 'polynomial' in text or 'function' in text or 'equation' in text:
                skill_parts.append('algebraic manipulation')
            if 'triangle' in text or 'circle' in text or 'angle' in text:
                skill_parts.append('geometric reasoning')
            if 'probability' in text or 'expected' in text or 'random' in text:
                skill_parts.append('probability computation')
            if 'sequence' in text or 'recurrence' in text:
                skill_parts.append('sequence analysis')
            if 'count' in text or 'how many' in text or 'number of' in text:
                skill_parts.append('counting')
            if 'permutation' in text or 'arrangement' in text:
                skill_parts.append('permutation enumeration')
            entry['skills'] = ', '.join(skill_parts) if skill_parts else 'mathematical reasoning'

        # Auto-generate approach if missing
        if not entry['approach']:
            parts = []
            if entry['failure_mode'] == 'timeout':
                parts.append('Model times out on brute force. Need mathematical insight to reduce computation.')
            elif entry['failure_mode'] == 'wrong_formula':
                parts.append(f'Model consistently gets {entry["common_wrong_answer"]} instead of {entry["expected_answer"]}. Systematic error in derivation.')
            elif entry['failure_mode'] == 'outvoted':
                parts.append(f'Correct answer {entry["expected_answer"]} appears in some attempts but is outvoted by {entry["common_wrong_answer"]}.')
            elif entry['failure_mode'] == 'close_vote':
                parts.append(f'Problem barely passed with close vote margin. At risk of flipping wrong in future runs.')
            elif entry['failure_mode'] == 'never_correct':
                parts.append(f'No attempt across any version found the correct answer {entry["expected_answer"]}. Fundamentally different approach needed.')

            cr_parts = entry['correct_rate'].split('/')
            if cr_parts[0] == '0':
                parts.append('Zero correct attempts — model needs a completely different strategy.')

            entry['approach'] = ' '.join(parts) if parts else 'Requires further analysis.'

    return entries


def write_outputs(entries):
    """Write JSON and CSV output files."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(base_dir, 'data', 'problem_db')
    os.makedirs(out_dir, exist_ok=True)

    # Clean up entries for output (remove internal field)
    output_entries = []
    for e in entries:
        out = dict(e)
        del out['is_close_vote_only']
        output_entries.append(out)

    # JSON
    json_path = os.path.join(out_dir, 'problems.json')
    with open(json_path, 'w') as f:
        json.dump(output_entries, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {json_path}")

    # CSV
    csv_path = os.path.join(out_dir, 'problems.csv')
    fieldnames = ['problem_id', 'question', 'expected_answer', 'topics', 'skills',
                  'failure_mode', 'common_wrong_answer', 'approach', 'versions_wrong', 'correct_rate']
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for e in output_entries:
            row = dict(e)
            row['topics'] = '|'.join(row['topics'])
            row['versions_wrong'] = '|'.join(row['versions_wrong'])
            writer.writerow(row)
    print(f"Wrote {csv_path}")

    return json_path, csv_path


def print_summary(entries):
    """Print summary statistics."""
    print("\n" + "="*70)
    print("PROBLEM DATABASE SUMMARY")
    print("="*70)

    print(f"\nTotal problems: {len(entries)}")

    # By failure mode
    print("\nBy failure mode:")
    mode_counts = Counter(e['failure_mode'] for e in entries)
    for mode, count in mode_counts.most_common():
        pids = [e['problem_id'] for e in entries if e['failure_mode'] == mode]
        print(f"  {mode:20s}: {count:2d} — {', '.join(pids)}")

    # By topic
    print("\nBy topic:")
    topic_counts = Counter()
    for e in entries:
        for t in e['topics']:
            topic_counts[t] += 1
    for topic, count in topic_counts.most_common():
        print(f"  {topic:20s}: {count}")

    # By version
    print("\nBy version:")
    v23_only = sum(1 for e in entries if e['versions_wrong'] == ['v23'])
    v31_only = sum(1 for e in entries if e['versions_wrong'] == ['v31'])
    both = sum(1 for e in entries if 'v23' in e['versions_wrong'] and 'v31' in e['versions_wrong'])
    print(f"  v23 only: {v23_only}")
    print(f"  v31 only: {v31_only}")
    print(f"  Both:     {both}")

    # Problems with empty question text
    empty_q = sum(1 for e in entries if len(e['question']) < 50)
    if empty_q:
        print(f"\n*** WARNING: {empty_q} problems have short/empty question text ***")
        for e in entries:
            if len(e['question']) < 50:
                print(f"    {e['problem_id']}: '{e['question'][:80]}'")

    # Quick table
    print("\n" + "-"*110)
    print(f"{'PID':8s} {'Expected':>8s} {'Wrong Ans':>9s} {'Rate':>8s} {'Mode':18s} {'Versions':12s} {'Topics'}")
    print("-"*110)
    for e in sorted(entries, key=lambda x: x['failure_mode']):
        topics_str = ', '.join(e['topics'])[:30]
        versions_str = ', '.join(e['versions_wrong'])
        common_wrong = str(e['common_wrong_answer']) if e['common_wrong_answer'] is not None else 'scattered'
        print(f"{e['problem_id']:8s} {e['expected_answer']:>8d} {common_wrong:>9s} {e['correct_rate']:>8s} {e['failure_mode']:18s} {versions_str:12s} {topics_str}")


if __name__ == '__main__':
    entries = build_problem_db()
    entries = enrich_topics_and_skills(entries)
    write_outputs(entries)
    print_summary(entries)
