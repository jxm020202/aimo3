#!/usr/bin/env python3
"""
Deep extraction of question text and reasoning for NT/Algebra problems.
Extracts full problem text from the first turn of each problem.
"""

import sys
import os
import json
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log

TARGET_PIDS = ['3980cd', '86e8e5', '3b88b3', '29714f', 'aff75c']


def extract_question_from_reasoning(prob):
    """Extract the full question text from the first turn's reasoning."""
    if not prob.attempts:
        return ""
    att = prob.attempts[0]
    if not att.turns:
        return ""

    text = att.turns[0].reasoning_text
    if not text:
        return ""

    # The problem text is typically at the start of the first turn reasoning
    # Return the full first turn reasoning (up to 5000 chars) for manual extraction
    return text[:5000]


def analyze_correct_vs_wrong(prob, expected):
    """Detailed comparison of correct vs wrong attempts."""
    correct_approaches = []
    wrong_approaches = []

    for att in prob.attempts:
        all_code = "\n".join(t.code for t in att.turns if t.code)
        all_reasoning = "\n".join(t.reasoning_text for t in att.turns if t.reasoning_text)
        all_output = "\n".join(t.output for t in att.turns if t.output)

        info = {
            'attempt': att.attempt_num,
            'answer': att.answer,
            'temp': att.temperature,
            'turns': len(att.turns),
            'code_calls': att.code_calls,
            'errors': att.errors,
            'time_s': round(att.time_s, 1),
            'code_length': len(all_code),
            'reasoning_length': len(all_reasoning),
        }

        # Detect key strategies
        strategies = []
        code_lower = all_code.lower()
        reason_lower = all_reasoning.lower()

        # Number theory strategies
        if 'cyclotomic' in code_lower or 'cyclotomic' in reason_lower:
            strategies.append('cyclotomic')
        if 'primitive_root' in code_lower or 'primitive root' in reason_lower:
            strategies.append('primitive_root')
        if 'roots of unity' in reason_lower or 'root of unity' in reason_lower:
            strategies.append('roots_of_unity')
        if 'crt' in code_lower or 'chinese remainder' in reason_lower:
            strategies.append('CRT')
        if 'euler' in reason_lower:
            strategies.append('euler')
        if 'norwegian' in reason_lower:
            strategies.append('norwegian')
        if 'divisor' in code_lower:
            strategies.append('divisor_computation')
        if 'factorint' in code_lower or 'factor(' in code_lower:
            strategies.append('factorization')

        # Algebra strategies
        if 'lagrange' in reason_lower:
            strategies.append('lagrange')
        if 'kkt' in reason_lower:
            strategies.append('KKT')
        if 'gradient' in reason_lower or 'gradient' in code_lower:
            strategies.append('gradient')
        if 'floor(' in code_lower or 'floor' in reason_lower:
            strategies.append('floor_function')
        if 'boundary' in reason_lower:
            strategies.append('boundary_analysis')
        if 'checkerboard' in reason_lower or 'checkerboard' in code_lower:
            strategies.append('checkerboard')
        if 'simulated_annealing' in code_lower or 'annealing' in reason_lower:
            strategies.append('simulated_annealing')
        if 'recurrence' in reason_lower or 'recursive' in code_lower:
            strategies.append('recurrence')
        if 'brute' in reason_lower or 'enumerate' in reason_lower:
            strategies.append('brute_force')
        if 'monte_carlo' in code_lower or 'random' in code_lower:
            strategies.append('monte_carlo')
        if 'optimize' in code_lower or 'minimize' in code_lower:
            strategies.append('scipy_optimize')
        if 'sympy' in code_lower:
            strategies.append('sympy')
        if 'Fraction' in all_code:
            strategies.append('exact_arithmetic')

        info['strategies'] = strategies

        if att.answer == expected:
            correct_approaches.append(info)
        elif att.answer is not None:
            wrong_approaches.append(info)

    return correct_approaches, wrong_approaches


def get_final_answer_reasoning(prob, expected, correct=True, max_samples=3):
    """Get the reasoning from last few turns of correct/wrong attempts."""
    samples = []

    for att in prob.attempts:
        if correct and att.answer == expected:
            pass
        elif not correct and att.answer is not None and att.answer != expected:
            pass
        else:
            continue

        if len(samples) >= max_samples:
            break

        # Get the last 5 turns
        last_turns = att.turns[-5:] if len(att.turns) > 5 else att.turns
        turns_text = []
        for t in last_turns:
            parts = []
            if t.reasoning_text:
                parts.append(f"REASONING: {t.reasoning_text[:800]}")
            if t.code:
                parts.append(f"CODE: {t.code[:500]}")
            if t.output:
                parts.append(f"OUTPUT: {t.output[:300]}")
            turns_text.append(f"[Turn {t.turn_num}]\n" + "\n".join(parts))

        samples.append({
            'attempt': att.attempt_num,
            'answer': att.answer,
            'temp': att.temperature,
            'turns': len(att.turns),
            'last_turns': "\n---\n".join(turns_text)
        })

    return samples


def main():
    os.chdir('/Users/intern/Desktop/sideprojects/aimo3')

    print("Parsing logs...")
    v23 = parse_log('output/v23/diagnostic.log')
    v31 = parse_log('output/v31/diagnostic.log')

    # Index by problem_id
    v23_idx = {p.problem_id: p for p in v23}
    v31_idx = {p.problem_id: p for p in v31}

    results = {}

    for pid in TARGET_PIDS:
        results[pid] = {'v23': None, 'v31': None}

        for ver_name, idx in [('v23', v23_idx), ('v31', v31_idx)]:
            if pid not in idx:
                print(f"  {pid} not in {ver_name}")
                continue

            prob = idx[pid]
            expected = prob.expected

            print(f"\n{'='*80}")
            print(f"Problem {pid} ({ver_name}) — Expected: {expected}, Predicted: {prob.predicted}, Correct: {prob.correct}")
            print(f"{'='*80}")

            # 1. Full question text
            question = extract_question_from_reasoning(prob)
            print(f"\n--- QUESTION TEXT (first 1500 chars of first turn) ---")
            print(question[:1500])

            # 2. Vote distribution
            print(f"\n--- VOTES ---")
            print(f"  {prob.votes}")

            # 3. Correct vs wrong attempts
            correct_approaches, wrong_approaches = analyze_correct_vs_wrong(prob, expected)

            print(f"\n--- CORRECT ATTEMPTS ({len(correct_approaches)}) ---")
            for ca in correct_approaches:
                print(f"  Att {ca['attempt']}: temp={ca['temp']}, turns={ca['turns']}, "
                      f"code_calls={ca['code_calls']}, errors={ca['errors']}, "
                      f"time={ca['time_s']}s, strategies={ca['strategies']}")

            print(f"\n--- WRONG ATTEMPTS ({len(wrong_approaches)}) ---")
            ans_counter = Counter(wa['answer'] for wa in wrong_approaches)
            print(f"  Answer distribution: {dict(ans_counter.most_common(10))}")
            for wa in wrong_approaches[:5]:
                print(f"  Att {wa['attempt']}: answer={wa['answer']}, temp={wa['temp']}, "
                      f"turns={wa['turns']}, strategies={wa['strategies']}")

            # 4. Get detailed reasoning from correct attempts
            if correct_approaches:
                print(f"\n--- CORRECT ATTEMPT REASONING SAMPLES ---")
                samples = get_final_answer_reasoning(prob, expected, correct=True, max_samples=2)
                for s in samples:
                    print(f"\n  [Attempt {s['attempt']}, answer={s['answer']}, temp={s['temp']}, turns={s['turns']}]")
                    for line in s['last_turns'].split('\n')[:30]:
                        print(f"    {line[:150]}")

            # 5. Get detailed reasoning from wrong attempts (most common wrong answer)
            if wrong_approaches:
                print(f"\n--- WRONG ATTEMPT REASONING SAMPLES ---")
                samples = get_final_answer_reasoning(prob, expected, correct=False, max_samples=2)
                for s in samples:
                    print(f"\n  [Attempt {s['attempt']}, answer={s['answer']}, temp={s['temp']}, turns={s['turns']}]")
                    for line in s['last_turns'].split('\n')[:20]:
                        print(f"    {line[:150]}")

            results[pid][ver_name] = {
                'predicted': prob.predicted,
                'expected': expected,
                'correct': prob.correct,
                'votes': dict(prob.votes) if prob.votes else {},
                'correct_count': len(correct_approaches),
                'wrong_count': len(wrong_approaches),
                'none_count': sum(1 for a in prob.attempts if a.is_none),
            }

    # Save results summary
    with open('data/problem_db/_deep_analysis.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n\nDeep analysis saved to data/problem_db/_deep_analysis.json")


if __name__ == '__main__':
    main()
