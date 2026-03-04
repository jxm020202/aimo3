#!/usr/bin/env python3
"""
Find close-vote NT/algebra problems across v23 and v31 that aren't in the target list.
"""

import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log

TARGET_PIDS = {'3980cd', '86e8e5', '3b88b3', '29714f', 'aff75c'}

NT_KEYWORDS = ['divisor', 'prime', 'modulo', 'roots of unity', 'complex', 'gcd', 'lcm',
               'congruence', 'coprime', 'cyclotomic', 'euler', 'fermat', 'chinese remainder',
               'norwegian', 'product', 'multiplicative']
ALGEBRA_KEYWORDS = ['optimize', 'maximiz', 'minimiz', 'inequality', 'functional equation',
                    'recurrence', 'polynomial', 'sequence', 'grid', 'floor', 'ceil',
                    'function', 'non-negative', 'real number']


def classify_problem(prob):
    """Try to classify a problem as NT, algebra, or other based on question text and reasoning."""
    text = prob.problem_text.lower()
    if not text and prob.attempts:
        text = (prob.attempts[0].turns[0].reasoning_text[:1000] if prob.attempts and prob.attempts[0].turns else "").lower()

    nt_score = sum(1 for kw in NT_KEYWORDS if kw in text)
    alg_score = sum(1 for kw in ALGEBRA_KEYWORDS if kw in text)

    if nt_score > alg_score and nt_score >= 2:
        return 'number_theory', nt_score
    elif alg_score > nt_score and alg_score >= 2:
        return 'algebra', alg_score
    elif nt_score >= 1:
        return 'number_theory', nt_score
    elif alg_score >= 1:
        return 'algebra', alg_score
    return 'other', 0


def main():
    os.chdir('/Users/intern/Desktop/sideprojects/aimo3')

    v23 = parse_log('output/v23/diagnostic.log')
    v31 = parse_log('output/v31/diagnostic.log')

    # Find all wrong or close-vote problems
    all_probs = {}

    for version, problems in [('v23', v23), ('v31', v31)]:
        for prob in problems:
            pid = prob.problem_id
            if pid in TARGET_PIDS:
                continue

            if pid not in all_probs:
                all_probs[pid] = {
                    'versions': {},
                    'problem_text': prob.problem_text or '',
                }

            # Check votes
            votes = dict(prob.votes) if prob.votes else {}
            expected = prob.expected
            answer_counts = Counter(a.answer for a in prob.attempts if a.answer is not None)

            is_close_vote = False
            correct_found = False
            if expected is not None and expected in answer_counts:
                correct_found = True
                # Close vote: correct answer found but not predicted
                if not prob.correct:
                    is_close_vote = True

            all_probs[pid]['versions'][version] = {
                'correct': prob.correct,
                'predicted': prob.predicted,
                'expected': expected,
                'votes': votes,
                'is_close_vote': is_close_vote,
                'correct_found': correct_found,
                'answer_distribution': dict(answer_counts.most_common(5)),
                'total_attempts': len(prob.attempts),
                'correct_count': sum(1 for a in prob.attempts if a.answer == expected),
            }

            if not all_probs[pid]['problem_text'] and prob.problem_text:
                all_probs[pid]['problem_text'] = prob.problem_text

    # Now classify and find NT/algebra close votes or wrong
    print("=" * 80)
    print("WRONG OR CLOSE-VOTE NT/ALGEBRA PROBLEMS (NOT IN TARGET LIST)")
    print("=" * 80)

    for pid, info in sorted(all_probs.items()):
        # Check if wrong in any version
        wrong_in = [v for v, d in info['versions'].items() if not d['correct']]
        close_in = [v for v, d in info['versions'].items() if d['is_close_vote']]

        if not wrong_in:
            continue

        category, score = classify_problem_from_text(info['problem_text'])
        if category == 'other':
            # Try from first version's reasoning
            for ver in info['versions']:
                cat2, score2 = classify_problem_from_text(info['problem_text'])
                if cat2 != 'other':
                    category, score = cat2, score2
                    break

        if category in ('number_theory', 'algebra'):
            print(f"\n  {pid}: {category} (score={score})")
            print(f"    Text: {info['problem_text'][:200]}")
            for ver, d in info['versions'].items():
                print(f"    {ver}: correct={d['correct']}, predicted={d['predicted']}, "
                      f"expected={d['expected']}, close_vote={d['is_close_vote']}")
                print(f"          votes={d['votes']}, correct_count={d['correct_count']}/{d['total_attempts']}")
                print(f"          answers={d['answer_distribution']}")


def classify_problem_from_text(text):
    text = text.lower()
    nt_score = sum(1 for kw in NT_KEYWORDS if kw in text)
    alg_score = sum(1 for kw in ALGEBRA_KEYWORDS if kw in text)

    if nt_score > alg_score and nt_score >= 1:
        return 'number_theory', nt_score
    elif alg_score > nt_score and alg_score >= 1:
        return 'algebra', alg_score
    elif nt_score >= 1:
        return 'number_theory', nt_score
    elif alg_score >= 1:
        return 'algebra', alg_score
    return 'other', 0


if __name__ == '__main__':
    main()
