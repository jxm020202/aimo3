#!/usr/bin/env python3
"""
Extract detailed information about combinatorics problems from diagnostic logs.
Builds a problem database for Wave 2 prompt injection.

Usage:
    python3 log_exploration/extract_combinatorics_db.py
"""

import sys
import os
import re
import json
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log

# Known combinatorics problems
COMBO_PROBLEMS = {
    'dbbfe8': {'answer': 22, 'topics': ['combinatorics', 'optimization', 'tiling']},
    'a824c1': {'answer': 24, 'topics': ['combinatorics', 'optimization', 'board_coverage']},
    '673b29': {'answer': 3, 'topics': ['combinatorics', 'game_theory', 'maze']},
    '414a5b': {'answer': 42, 'topics': ['combinatorics', 'probability', 'dice']},
    'a9dbc8': {'answer': 15744, 'topics': ['combinatorics', 'probability', 'random_walk']},
    '9010d9': {'answer': 10320, 'topics': ['combinatorics', 'graph_theory', 'extremal']},
}


def extract_full_question(problem, log_filepath):
    """Extract the FULL question text from the raw log file.

    The parser only stores first 300 chars of problem_text.
    We need to go to the raw log and extract the full conversation content from the first attempt.
    """
    # Strategy: find the problem header in the raw log, then look for the question text
    # in the first attempt's first turn reasoning (which contains the full problem)

    # First, check if problem_text is useful
    short_text = problem.problem_text if problem.problem_text else ""

    # The full question is usually in the first turn's reasoning of the first attempt
    # because the model receives the problem text as part of its prompt
    # Let's search the raw log for the problem section

    with open(log_filepath, 'r', errors='replace') as f:
        content = f.read()

    # Find the problem header
    # Pattern: [N/M] Problem id=XXXX or [N/M] Problem XXXX
    pid = problem.problem_id
    pattern = rf'\[\d+/\d+\]\s*Problem\s+(?:id=)?{pid}'
    match = re.search(pattern, content)
    if not match:
        return short_text

    start_pos = match.start()

    # Now look for "Problem:" line which contains the problem text
    # Search in the next ~5000 chars
    section = content[start_pos:start_pos + 50000]

    # Look for problem text after "Problem:" header
    prob_match = re.search(r'Problem:\s*(.+?)(?=\n\s*Budget:|\n\s*Expected:|\n\s*ATTEMPT\s+\d+)', section, re.DOTALL)
    if prob_match:
        text = prob_match.group(1).strip()
        # Clean up the text
        text = re.sub(r'\n\s+', ' ', text)
        if len(text) > 100:
            return text

    # Fallback: look in the first attempt's reasoning for the problem statement
    # The model often repeats the problem in its first reasoning turn
    if problem.attempts:
        first_attempt = problem.attempts[0]
        if first_attempt.turns:
            first_reasoning = first_attempt.turns[0].reasoning_text
            if first_reasoning and len(first_reasoning) > 200:
                # Try to find the problem statement in the reasoning
                # Look for "Problem:" or the problem text pattern
                lines = first_reasoning[:5000]
                return lines[:2000]  # Return first part of reasoning as context

    return short_text


def extract_full_question_from_raw(pid, log_filepath):
    """More aggressive extraction: scan raw log for the full problem text."""
    with open(log_filepath, 'r', errors='replace') as f:
        content = f.read()

    # Find the problem section
    pattern = rf'\[\d+/\d+\]\s*Problem\s+(?:id=)?{pid}'
    match = re.search(pattern, content)
    if not match:
        return ""

    start_pos = match.start()
    # Get a large section after the problem header
    section = content[start_pos:start_pos + 100000]

    # Look for "Problem:" line - may be multiline
    prob_start = section.find('Problem:')
    if prob_start == -1:
        return ""

    # The problem text continues until we hit Budget: or Expected: or ATTEMPT
    text_start = prob_start + len('Problem:')
    remaining = section[text_start:]

    # Find the end marker
    end_markers = ['\nBudget:', '\nExpected:', '\nATTEMPT ', '\n---']
    end_pos = len(remaining)
    for marker in end_markers:
        pos = remaining.find(marker)
        if pos != -1 and pos < end_pos:
            end_pos = pos

    raw_text = remaining[:end_pos].strip()
    # Clean up whitespace
    raw_text = re.sub(r'\n\s*', ' ', raw_text)
    raw_text = re.sub(r'\s+', ' ', raw_text)

    return raw_text


def analyze_attempt_approaches(attempt, pid):
    """Analyze what approach an attempt used based on its reasoning and code."""
    approaches = []
    keywords_found = []

    all_reasoning = ""
    all_code = ""
    all_output = ""

    for turn in attempt.turns:
        all_reasoning += " " + (turn.reasoning_text or "")
        all_code += "\n" + (turn.code or "")
        all_output += "\n" + (turn.output or "")

    total_reasoning_len = len(all_reasoning)
    total_code_len = len(all_code.strip())

    # Check for specific approaches
    if 'brute' in all_reasoning.lower() or 'brute' in all_code.lower():
        approaches.append('brute_force')
    if 'binary search' in all_reasoning.lower() or 'binary_search' in all_code.lower():
        approaches.append('binary_search')
    if 'dp' in all_code.lower() or 'dynamic programming' in all_reasoning.lower():
        approaches.append('dynamic_programming')
    if 'backtrack' in all_code.lower() or 'backtrack' in all_reasoning.lower():
        approaches.append('backtracking')
    if 'graph' in all_code.lower() or 'networkx' in all_code.lower():
        approaches.append('graph_theory')
    if 'greedy' in all_reasoning.lower():
        approaches.append('greedy')
    if 'lower bound' in all_reasoning.lower() or 'upper bound' in all_reasoning.lower():
        approaches.append('bound_argument')
    if 'pulp' in all_code.lower() or 'ortools' in all_code.lower() or 'milp' in all_code.lower():
        approaches.append('ilp_solver')
    if 'itertools' in all_code.lower():
        approaches.append('enumeration')
    if 'simulation' in all_reasoning.lower() or 'simulate' in all_code.lower():
        approaches.append('simulation')
    if 'probability' in all_reasoning.lower() or 'P(' in all_reasoning or 'expected' in all_reasoning.lower():
        approaches.append('probability')
    if 'recursive' in all_reasoning.lower() or 'recursion' in all_reasoning.lower():
        approaches.append('recursion')
    if 'formula' in all_reasoning.lower() or 'closed form' in all_reasoning.lower():
        approaches.append('closed_form')
    if 'domino' in all_reasoning.lower() or 'tiling' in all_reasoning.lower():
        approaches.append('tiling')
    if 'diagonal' in all_reasoning.lower() or 'bishop' in all_reasoning.lower():
        approaches.append('diagonal_coverage')
    if 'random walk' in all_reasoning.lower() or 'coin flip' in all_reasoning.lower():
        approaches.append('random_walk')
    if total_reasoning_len > 10000 and total_code_len < 500:
        approaches.append('pure_reasoning')

    return {
        'approaches': approaches,
        'reasoning_len': total_reasoning_len,
        'code_len': total_code_len,
        'num_turns': len(attempt.turns),
        'num_errors': attempt.errors,
    }


def analyze_problem(pid, info, v23_problems, v31_problems):
    """Build a detailed database entry for one combinatorics problem."""
    expected = info['answer']
    topics = info['topics']

    # Find the problem in both logs
    p23 = next((p for p in v23_problems if p.problem_id == pid), None)
    p31 = next((p for p in v31_problems if p.problem_id == pid), None)

    if not p23 and not p31:
        print(f"  WARNING: {pid} not found in either log!")
        return None

    # Extract full question text
    question = ""
    if p23:
        question = extract_full_question_from_raw(pid, 'output/v23/diagnostic.log')
    if not question and p31:
        question = extract_full_question_from_raw(pid, 'output/v31/diagnostic.log')
    if not question:
        question = (p23 or p31).problem_text

    # Collect all attempts across both versions
    all_attempts = []
    versions_wrong = []

    for version, prob in [('v23', p23), ('v31', p31)]:
        if not prob:
            continue
        if not prob.correct:
            versions_wrong.append(version)
        for att in prob.attempts:
            all_attempts.append({
                'version': version,
                'attempt_num': att.attempt_num,
                'answer': att.answer,
                'is_correct': att.answer == expected if att.answer is not None else False,
                'is_none': att.is_none,
                'temperature': att.temperature,
                'analysis': analyze_attempt_approaches(att, pid),
                'attempt_obj': att,
            })

    # Count answers
    answer_counts = Counter()
    correct_count = 0
    total_with_answer = 0
    total_attempts = len(all_attempts)

    for att in all_attempts:
        if att['answer'] is not None:
            answer_counts[att['answer']] += 1
            total_with_answer += 1
            if att['is_correct']:
                correct_count += 1

    # Get common wrong answers
    wrong_answers = {k: v for k, v in answer_counts.items() if k != expected}
    common_wrong = sorted(wrong_answers.items(), key=lambda x: -x[1])[:5]

    # Analyze correct vs wrong attempts
    correct_attempts = [a for a in all_attempts if a['is_correct']]
    wrong_attempts = [a for a in all_attempts if a['answer'] is not None and not a['is_correct']]
    none_attempts = [a for a in all_attempts if a['is_none']]

    # What did correct attempts do differently?
    correct_approaches = Counter()
    wrong_approaches = Counter()

    for att in correct_attempts:
        for approach in att['analysis']['approaches']:
            correct_approaches[approach] += 1

    for att in wrong_attempts:
        for approach in att['analysis']['approaches']:
            wrong_approaches[approach] += 1

    # Detailed analysis of correct attempts
    correct_detail = []
    for att in correct_attempts[:5]:  # Up to 5 examples
        detail = {
            'version': att['version'],
            'attempt': att['attempt_num'],
            'approaches': att['analysis']['approaches'],
            'reasoning_len': att['analysis']['reasoning_len'],
            'code_len': att['analysis']['code_len'],
            'num_turns': att['analysis']['num_turns'],
            'temperature': att['temperature'],
        }
        correct_detail.append(detail)

    # Analyze wrong attempts for failure patterns
    wrong_detail = []
    for att in wrong_attempts[:5]:
        detail = {
            'version': att['version'],
            'attempt': att['attempt_num'],
            'answer': att['answer'],
            'approaches': att['analysis']['approaches'],
            'reasoning_len': att['analysis']['reasoning_len'],
            'code_len': att['analysis']['code_len'],
            'num_turns': att['analysis']['num_turns'],
        }
        wrong_detail.append(detail)

    # Compute stats
    avg_correct_reasoning = sum(a['analysis']['reasoning_len'] for a in correct_attempts) / max(len(correct_attempts), 1)
    avg_wrong_reasoning = sum(a['analysis']['reasoning_len'] for a in wrong_attempts) / max(len(wrong_attempts), 1)
    avg_correct_code = sum(a['analysis']['code_len'] for a in correct_attempts) / max(len(correct_attempts), 1)
    avg_wrong_code = sum(a['analysis']['code_len'] for a in wrong_attempts) / max(len(wrong_attempts), 1)
    avg_correct_turns = sum(a['analysis']['num_turns'] for a in correct_attempts) / max(len(correct_attempts), 1)
    avg_wrong_turns = sum(a['analysis']['num_turns'] for a in wrong_attempts) / max(len(wrong_attempts), 1)

    print(f"\n{'='*70}")
    print(f"  Problem {pid} | Expected: {expected} | Correct: {correct_count}/{total_attempts}")
    print(f"  Question: {question[:150]}...")
    print(f"  Versions wrong: {versions_wrong}")
    print(f"  Answer distribution: {dict(answer_counts.most_common(8))}")
    print(f"  Correct approach stats: reasoning={avg_correct_reasoning:.0f} code={avg_correct_code:.0f} turns={avg_correct_turns:.1f}")
    print(f"  Wrong approach stats:   reasoning={avg_wrong_reasoning:.0f} code={avg_wrong_code:.0f} turns={avg_wrong_turns:.1f}")
    print(f"  Correct approaches: {dict(correct_approaches)}")
    print(f"  Wrong approaches:   {dict(wrong_approaches)}")

    return {
        'problem_id': pid,
        'question': question,
        'expected_answer': expected,
        'topics': topics,
        'answer_distribution': {str(k): v for k, v in answer_counts.most_common(10)},
        'correct_count': correct_count,
        'total_attempts': total_attempts,
        'common_wrong': common_wrong,
        'versions_wrong': versions_wrong,
        'correct_detail': correct_detail,
        'wrong_detail': wrong_detail,
        'correct_approaches': dict(correct_approaches),
        'wrong_approaches': dict(wrong_approaches),
        'avg_correct_reasoning': avg_correct_reasoning,
        'avg_wrong_reasoning': avg_wrong_reasoning,
        'avg_correct_code': avg_correct_code,
        'avg_wrong_code': avg_wrong_code,
        'avg_correct_turns': avg_correct_turns,
        'avg_wrong_turns': avg_wrong_turns,
        'none_count': len(none_attempts),
    }


def get_reasoning_snippets(problem, expected, log_filepath, max_correct=3, max_wrong=3):
    """Extract key reasoning snippets from correct and wrong attempts."""
    correct_snippets = []
    wrong_snippets = []

    if not problem:
        return correct_snippets, wrong_snippets

    for att in problem.attempts:
        if att.answer is None:
            continue

        is_correct = att.answer == expected

        # Get the last turn's reasoning (usually has the conclusion)
        last_reasoning = ""
        first_reasoning = ""
        code_snippets = []

        for turn in att.turns:
            if turn.reasoning_text:
                if not first_reasoning:
                    first_reasoning = turn.reasoning_text[:2000]
                last_reasoning = turn.reasoning_text[-2000:]
            if turn.code:
                code_snippets.append(turn.code[:1000])

        snippet = {
            'attempt': att.attempt_num,
            'answer': att.answer,
            'temperature': att.temperature,
            'num_turns': len(att.turns),
            'first_reasoning_preview': first_reasoning[:1500],
            'last_reasoning_preview': last_reasoning[:1500],
            'code_preview': code_snippets[0][:1000] if code_snippets else "",
        }

        if is_correct and len(correct_snippets) < max_correct:
            correct_snippets.append(snippet)
        elif not is_correct and len(wrong_snippets) < max_wrong:
            wrong_snippets.append(snippet)

    return correct_snippets, wrong_snippets


def main():
    os.chdir('/Users/intern/Desktop/sideprojects/aimo3')

    print("Parsing v23 log...")
    v23_problems = parse_log('output/v23/diagnostic.log')
    print(f"  Parsed {len(v23_problems)} problems from v23")

    print("Parsing v31 log...")
    v31_problems = parse_log('output/v31/diagnostic.log')
    print(f"  Parsed {len(v31_problems)} problems from v31")

    # Analyze each combinatorics problem
    results = {}
    for pid, info in COMBO_PROBLEMS.items():
        result = analyze_problem(pid, info, v23_problems, v31_problems)
        if result:
            results[pid] = result

    # Also get reasoning snippets for deeper analysis
    print("\n\nExtracting reasoning snippets...")
    for pid in COMBO_PROBLEMS:
        expected = COMBO_PROBLEMS[pid]['answer']
        p23 = next((p for p in v23_problems if p.problem_id == pid), None)
        p31 = next((p for p in v31_problems if p.problem_id == pid), None)

        c_snips23, w_snips23 = get_reasoning_snippets(p23, expected, 'output/v23/diagnostic.log')
        c_snips31, w_snips31 = get_reasoning_snippets(p31, expected, 'output/v31/diagnostic.log')

        if pid in results:
            results[pid]['correct_snippets'] = c_snips23 + c_snips31
            results[pid]['wrong_snippets'] = w_snips23 + w_snips31

    # Save raw analysis data
    with open('data/problem_db/combinatorics_raw.json', 'w') as f:
        # Need to serialize, remove attempt_obj
        serializable = {}
        for pid, r in results.items():
            s = dict(r)
            s.pop('correct_detail', None)
            s.pop('wrong_detail', None)
            serializable[pid] = s
        json.dump(serializable, f, indent=2, default=str)

    print(f"\nRaw analysis saved to data/problem_db/combinatorics_raw.json")
    print(f"Now review the snippets to build final database entries.")


if __name__ == '__main__':
    main()
