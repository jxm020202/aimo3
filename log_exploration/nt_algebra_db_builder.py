#!/usr/bin/env python3
"""
Build detailed problem database entries for Number Theory and Algebra problems.
Parses v23 and v31 diagnostic logs and extracts:
- Full question text
- Approach analysis per attempt
- Common wrong answers
- What correct attempts did differently
- Failure modes

Usage:
    python3 log_exploration/nt_algebra_db_builder.py
"""

import sys
import os
import json
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log

# Known NT/Algebra problems from wave2_starter_notes.md
TARGET_PROBLEMS = {
    # Number Theory
    '3980cd': {'expected': 46, 'category': 'number_theory', 'topics_hint': ['roots of unity', 'cyclotomic polynomials']},
    '86e8e5': {'expected': 8687, 'category': 'number_theory', 'topics_hint': ['Norwegian numbers', 'divisor sums']},
    # Algebra
    '3b88b3': {'expected': 979, 'category': 'algebra', 'topics_hint': ['optimization', 'floor function']},
    '29714f': {'expected': 297, 'category': 'algebra', 'topics_hint': ['functional equation']},
    'aff75c': {'expected': 3571, 'category': 'algebra', 'topics_hint': ['grid optimization']},
}


def extract_full_question(problems_list, pid):
    """Extract the full question text from conversation turns for a problem."""
    for prob in problems_list:
        if prob.problem_id == pid:
            # First check the problem_text field
            if prob.problem_text and len(prob.problem_text) > 50:
                return prob.problem_text

            # Otherwise search in reasoning/turn content of first attempt
            if prob.attempts:
                att = prob.attempts[0]
                if att.turns:
                    # The question is usually in the first turn's reasoning or as part of the prompt
                    first_turn = att.turns[0]
                    text = first_turn.reasoning_text
                    # Look for the problem statement pattern
                    return text[:2000] if text else ""
    return ""


def analyze_attempt_approaches(attempt):
    """Analyze what approach an attempt used based on its code and reasoning."""
    approaches = []
    all_code = ""
    all_reasoning = ""

    for turn in attempt.turns:
        if turn.code:
            all_code += turn.code + "\n"
        if turn.reasoning_text:
            all_reasoning += turn.reasoning_text + "\n"

    # Detect approaches from code
    if 'sympy' in all_code:
        approaches.append('sympy')
    if 'numpy' in all_code or 'np.' in all_code:
        approaches.append('numpy')
    if 'scipy' in all_code:
        approaches.append('scipy')
    if 'itertools' in all_code:
        approaches.append('itertools')
    if 'brute' in all_code.lower() or 'enumerate' in all_code.lower():
        approaches.append('brute_force')
    if 'lagrange' in all_code.lower() or 'lagrange' in all_reasoning.lower():
        approaches.append('lagrange_multipliers')
    if 'cyclotomic' in all_code.lower() or 'cyclotomic' in all_reasoning.lower():
        approaches.append('cyclotomic')
    if 'divisor' in all_code.lower() or 'divisors' in all_code.lower():
        approaches.append('divisor_analysis')
    if 'root' in all_code.lower() and 'unity' in all_reasoning.lower():
        approaches.append('roots_of_unity')
    if 'norwegian' in all_reasoning.lower():
        approaches.append('norwegian_analysis')
    if 'recurrence' in all_reasoning.lower() or 'recurrence' in all_code.lower():
        approaches.append('recurrence')
    if 'dynamic' in all_code.lower() or 'dp[' in all_code or 'dp =' in all_code:
        approaches.append('dynamic_programming')
    if 'optimize' in all_code.lower() or 'minimize' in all_code.lower() or 'maximize' in all_code.lower():
        approaches.append('optimization')
    if 'floor' in all_code.lower():
        approaches.append('floor_function')
    if 'monte_carlo' in all_code.lower() or 'random' in all_code.lower():
        approaches.append('monte_carlo')
    if 'grid' in all_code.lower() or 'grid' in all_reasoning.lower():
        approaches.append('grid_search')
    if not all_code.strip():
        approaches.append('pure_reasoning')

    return list(set(approaches))


def get_attempt_summary(attempt):
    """Get a brief summary of an attempt."""
    return {
        'attempt_num': attempt.attempt_num,
        'answer': attempt.answer,
        'temperature': attempt.temperature,
        'turns': len(attempt.turns),
        'errors': attempt.errors,
        'code_calls': attempt.code_calls,
        'time_s': round(attempt.time_s, 1),
        'approaches': analyze_attempt_approaches(attempt),
        'is_none': attempt.is_none,
    }


def analyze_problem_across_versions(pid, info, v23_problems, v31_problems):
    """Analyze a problem across both v23 and v31."""
    expected = info['expected']

    entry = {
        'problem_id': pid,
        'question': '',
        'expected_answer': expected,
        'topics': [],
        'skills': '',
        'failure_mode': '',
        'common_wrong_answers': [],
        'correct_rate': '',
        'why_wrong': '',
        'correct_approach': '',
        'what_correct_attempts_did': '',
        'versions_wrong': [],
    }

    # Collect data from both versions
    all_answers = Counter()
    correct_attempts_details = []
    wrong_attempts_details = []
    total_attempts = 0
    total_correct = 0
    question_texts = []
    versions_data = {}

    for version_name, problems_list in [('v23', v23_problems), ('v31', v31_problems)]:
        prob = None
        for p in problems_list:
            if p.problem_id == pid:
                prob = p
                break

        if prob is None:
            continue

        version_info = {
            'predicted': prob.predicted,
            'expected': prob.expected,
            'correct': prob.correct,
            'wall_time': round(prob.wall_time, 1),
            'num_attempts': len(prob.attempts),
            'votes': dict(prob.votes) if prob.votes else {},
        }
        versions_data[version_name] = version_info

        if not prob.correct:
            entry['versions_wrong'].append(version_name)

        # Extract question text
        qt = extract_full_question([prob], pid)
        if qt:
            question_texts.append(qt)

        for att in prob.attempts:
            total_attempts += 1
            if att.answer is not None:
                all_answers[att.answer] += 1
                if att.answer == expected:
                    total_correct += 1
                    correct_attempts_details.append({
                        'version': version_name,
                        **get_attempt_summary(att)
                    })
                else:
                    wrong_attempts_details.append({
                        'version': version_name,
                        **get_attempt_summary(att)
                    })
            else:
                wrong_attempts_details.append({
                    'version': version_name,
                    **get_attempt_summary(att)
                })

    # Fill in the entry
    entry['question'] = max(question_texts, key=len) if question_texts else ''
    entry['correct_rate'] = f"{total_correct}/{total_attempts}"

    # Common wrong answers (exclude correct answer)
    wrong_answers = {k: v for k, v in all_answers.items() if k != expected}
    entry['common_wrong_answers'] = [
        {'answer': ans, 'count': cnt}
        for ans, cnt in sorted(wrong_answers.items(), key=lambda x: -x[1])[:10]
    ]

    # Version details
    entry['version_details'] = versions_data

    # Attempt details for correct ones
    entry['correct_attempt_details'] = correct_attempts_details[:5]
    entry['wrong_attempt_sample'] = wrong_attempts_details[:5]

    return entry


def extract_reasoning_snippets(problems_list, pid, expected_answer, max_attempts=3):
    """Extract key reasoning snippets from correct and wrong attempts."""
    correct_snippets = []
    wrong_snippets = []

    for prob in problems_list:
        if prob.problem_id != pid:
            continue

        for att in prob.attempts:
            if att.answer == expected_answer and len(correct_snippets) < max_attempts:
                # Get last few turns (the breakthrough)
                snippet = ""
                for turn in att.turns[-3:]:
                    if turn.reasoning_text:
                        snippet += f"[Turn {turn.turn_num} reasoning]: {turn.reasoning_text[:500]}\n"
                    if turn.code:
                        snippet += f"[Turn {turn.turn_num} code]: {turn.code[:500]}\n"
                    if turn.output:
                        snippet += f"[Turn {turn.turn_num} output]: {turn.output[:300]}\n"
                correct_snippets.append({
                    'attempt': att.attempt_num,
                    'temperature': att.temperature,
                    'turns': len(att.turns),
                    'final_turns_snippet': snippet[:2000]
                })

            elif att.answer is not None and att.answer != expected_answer and len(wrong_snippets) < max_attempts:
                # Get the turns where they commit to wrong answer
                snippet = ""
                for turn in att.turns[-2:]:
                    if turn.reasoning_text:
                        snippet += f"[Turn {turn.turn_num} reasoning]: {turn.reasoning_text[:500]}\n"
                    if turn.code:
                        snippet += f"[Turn {turn.turn_num} code]: {turn.code[:500]}\n"
                    if turn.output:
                        snippet += f"[Turn {turn.turn_num} output]: {turn.output[:300]}\n"
                wrong_snippets.append({
                    'attempt': att.attempt_num,
                    'answer': att.answer,
                    'temperature': att.temperature,
                    'turns': len(att.turns),
                    'final_turns_snippet': snippet[:2000]
                })

    return correct_snippets, wrong_snippets


def main():
    v23_path = 'output/v23/diagnostic.log'
    v31_path = 'output/v31/diagnostic.log'

    print("Parsing v23 log...")
    v23_problems = parse_log(v23_path)
    print(f"  -> {len(v23_problems)} problems parsed")

    print("Parsing v31 log...")
    v31_problems = parse_log(v31_path)
    print(f"  -> {len(v31_problems)} problems parsed")

    # Also find close-vote problems in NT/algebra topics
    # First, let's find ALL wrong or close-vote problems
    all_problem_ids = set()
    close_vote_pids = []

    for prob in v23_problems + v31_problems:
        all_problem_ids.add(prob.problem_id)
        if prob.problem_id in TARGET_PROBLEMS:
            continue
        # Check for close votes - correct answer appeared but wasn't majority
        if not prob.correct and prob.votes:
            if prob.expected is not None and str(prob.expected) in prob.votes:
                close_vote_pids.append(prob.problem_id)

    print(f"\nTarget NT/Algebra problems: {list(TARGET_PROBLEMS.keys())}")
    print(f"Close-vote problems (correct answer appeared, lost vote): {close_vote_pids}")

    # Build entries for target problems
    entries = []

    for pid, info in TARGET_PROBLEMS.items():
        print(f"\n{'='*60}")
        print(f"Analyzing {pid} (expected={info['expected']}, {info['category']})")
        print(f"{'='*60}")

        entry = analyze_problem_across_versions(pid, info, v23_problems, v31_problems)

        # Get reasoning snippets
        correct_snips_v23, wrong_snips_v23 = extract_reasoning_snippets(v23_problems, pid, info['expected'])
        correct_snips_v31, wrong_snips_v31 = extract_reasoning_snippets(v31_problems, pid, info['expected'])

        all_correct_snips = correct_snips_v23 + correct_snips_v31
        all_wrong_snips = wrong_snips_v23 + wrong_snips_v31

        print(f"  Correct rate: {entry['correct_rate']}")
        print(f"  Versions wrong: {entry['versions_wrong']}")
        print(f"  Common wrong answers: {entry['common_wrong_answers'][:5]}")
        print(f"  Question preview: {entry['question'][:100]}...")
        print(f"  Correct attempt count: {len(all_correct_snips)}")
        print(f"  Wrong attempt count: {len(all_wrong_snips)}")

        # Print correct attempt snippets
        if all_correct_snips:
            print(f"\n  --- CORRECT ATTEMPTS REASONING ---")
            for s in all_correct_snips[:2]:
                print(f"  [Attempt {s['attempt']}, temp={s['temperature']}, turns={s['turns']}]")
                for line in s['final_turns_snippet'].split('\n')[:10]:
                    print(f"    {line[:120]}")

        # Print wrong attempt snippets
        if all_wrong_snips:
            print(f"\n  --- WRONG ATTEMPTS REASONING ---")
            for s in all_wrong_snips[:2]:
                print(f"  [Attempt {s['attempt']}, answer={s['answer']}, temp={s['temperature']}, turns={s['turns']}]")
                for line in s['final_turns_snippet'].split('\n')[:10]:
                    print(f"    {line[:120]}")

        # Save reasoning snippets to entry for later reference
        entry['_correct_reasoning_samples'] = all_correct_snips[:3]
        entry['_wrong_reasoning_samples'] = all_wrong_snips[:3]

        entries.append(entry)

    # Output all entries as JSON for reference
    output_path = 'data/problem_db/_raw_analysis.json'
    with open(output_path, 'w') as f:
        json.dump(entries, f, indent=2, default=str)
    print(f"\n\nRaw analysis saved to {output_path}")

    return entries


if __name__ == '__main__':
    os.chdir('/Users/intern/Desktop/sideprojects/aimo3')
    main()
