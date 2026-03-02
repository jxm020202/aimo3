"""
Score solver output against known answers.

Usage:
  python scripts/evaluate.py output/submission.csv data/test_fixed_50_answers.csv

Output:
  Per-problem results + total score (mimics Kaggle's double-run scoring if run twice).
"""

import csv
import sys


def load_csv(path):
    with open(path) as f:
        return {r['id']: int(r['answer']) for r in csv.DictReader(f)}


def evaluate(submission_path, answers_path):
    answers = load_csv(answers_path)
    submission = load_csv(submission_path)

    correct = 0
    wrong = 0
    missing = 0

    print(f'{"ID":>8}  {"Submitted":>10}  {"Expected":>10}  {"Result":>6}')
    print('-' * 45)

    for pid, expected in answers.items():
        if pid not in submission:
            print(f'{pid:>8}  {"MISSING":>10}  {expected:>10}  {"MISS":>6}')
            missing += 1
            continue

        submitted = submission[pid]
        ok = submitted == expected
        tag = 'OK' if ok else 'WRONG'
        print(f'{pid:>8}  {submitted:>10}  {expected:>10}  {tag:>6}')
        if ok:
            correct += 1
        else:
            wrong += 1

    total = correct + wrong + missing
    print('-' * 45)
    print(f'Score: {correct}/{total}  ({correct/total*100:.1f}%)')
    print(f'  Correct: {correct}  Wrong: {wrong}  Missing: {missing}')

    return correct, total


def compare_runs(sub1_path, sub2_path, answers_path):
    """Simulate Kaggle double-run scoring."""
    answers = load_csv(answers_path)
    sub1 = load_csv(sub1_path)
    sub2 = load_csv(sub2_path)

    score = 0.0
    for pid, expected in answers.items():
        r1 = sub1.get(pid) == expected
        r2 = sub2.get(pid) == expected
        if r1 and r2:
            score += 1.0
        elif r1 or r2:
            score += 0.5

    total = len(answers)
    print(f'\nDouble-run score: {score}/{total}  ({score/total*100:.1f}%)')
    return score, total


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python evaluate.py <submission.csv> <answers.csv> [submission2.csv]')
        sys.exit(1)

    evaluate(sys.argv[1], sys.argv[2])

    if len(sys.argv) >= 4:
        compare_runs(sys.argv[1], sys.argv[3], sys.argv[2])
