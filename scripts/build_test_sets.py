"""
Build test CSVs in competition format (id, problem) + answer files for scoring.

Creates two test sets:
  - data/test_fixed_50.csv  + data/test_fixed_50_answers.csv  (deterministic benchmark)
  - data/test_random_50.csv + data/test_random_50_answers.csv  (random sample, different each run)

Fixed 50 composition:
  - 10 reference problems (AIMO3-level, known difficulty)
  - 15 hardest AIME problems (2020-2024, problem numbers 11-15)
  - 25 AIME+IMO problems (sampled with fixed seed for reproducibility)

Usage:
  python scripts/build_test_sets.py          # builds both
  python scripts/build_test_sets.py --fixed   # fixed only
  python scripts/build_test_sets.py --random  # random only
"""

import csv
import hashlib
import random
import sys
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

REFERENCE_CSV = os.path.join(DATA_DIR, 'reference.csv')
AIME_CSV = os.path.join(DATA_DIR, 'test_sets', 'aime-problem-set-1983-2024', 'AIME_Dataset_1983_2024.csv')
AIME_IMO_CSV = os.path.join(DATA_DIR, 'test_sets', 'math-problems-with-answers-aime-imo', 'valid_data.csv')


def short_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:6]


def load_reference():
    with open(REFERENCE_CSV) as f:
        reader = csv.DictReader(f)
        return [{'id': r['id'], 'problem': r['problem'], 'answer': int(r['answer'])} for r in reader]


def load_aime():
    with open(AIME_CSV) as f:
        reader = csv.DictReader(f)
        out = []
        for r in reader:
            ans = r['Answer'].strip()
            if not ans.isdigit():
                continue
            out.append({
                'id': short_id(r['Question']),
                'problem': r['Question'],
                'answer': int(ans),
                'year': int(r['Year']),
                'number': int(r['Problem Number']),
            })
        return out


def load_aime_imo():
    with open(AIME_IMO_CSV) as f:
        reader = csv.DictReader(f)
        out = []
        for r in reader:
            ans = r['answer'].strip()
            if not ans.isdigit():
                continue
            a = int(ans)
            if a < 0 or a > 99999:
                continue
            out.append({
                'id': short_id(r['problem']),
                'problem': r['problem'],
                'answer': a,
            })
        return out


def write_test_csv(problems, prefix):
    test_path = os.path.join(DATA_DIR, f'{prefix}.csv')
    answers_path = os.path.join(DATA_DIR, f'{prefix}_answers.csv')

    with open(test_path, 'w', newline='') as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(['id', 'problem'])
        for p in problems:
            w.writerow([p['id'], p['problem']])

    with open(answers_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['id', 'answer'])
        for p in problems:
            w.writerow([p['id'], p['answer']])

    print(f'  {test_path} ({len(problems)} problems)')
    print(f'  {answers_path}')


def build_fixed():
    print('Building fixed 50...')
    ref = load_reference()  # 10
    aime = load_aime()
    aime_imo = load_aime_imo()

    # 15 hardest AIME: recent years, high problem numbers
    hard_aime = [p for p in aime if p['year'] >= 2020 and p['number'] >= 11]
    hard_aime.sort(key=lambda x: (x['year'], x['number']), reverse=True)
    hard_aime = hard_aime[:15]

    # 25 from AIME+IMO (exclude any that overlap with AIME set by problem text hash)
    aime_ids = {p['id'] for p in hard_aime}
    ref_ids = {p['id'] for p in ref}
    pool = [p for p in aime_imo if p['id'] not in aime_ids and p['id'] not in ref_ids]
    rng = random.Random(42)
    selected_imo = rng.sample(pool, min(25, len(pool)))

    problems = ref + hard_aime + selected_imo
    print(f'  {len(ref)} reference + {len(hard_aime)} hard AIME + {len(selected_imo)} AIME+IMO')
    write_test_csv(problems, 'test_fixed_50')


def build_random():
    print('Building random 50...')
    ref = load_reference()
    aime = load_aime()
    aime_imo = load_aime_imo()

    all_problems = ref + aime + aime_imo
    # Deduplicate by id
    seen = set()
    unique = []
    for p in all_problems:
        if p['id'] not in seen:
            seen.add(p['id'])
            unique.append(p)

    selected = random.sample(unique, min(50, len(unique)))
    write_test_csv(selected, 'test_random_50')


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or '--fixed' in args:
        build_fixed()
    if not args or '--random' in args:
        build_random()
    print('Done.')
