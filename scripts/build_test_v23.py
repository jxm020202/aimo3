"""
Build v23 test CSVs from the 347-problem aimo3-val-bench dataset.

Output:
  data/active/test_problems.csv  (id, problem) — QUOTE_ALL
  data/active/test_answers.csv   (id, answer)

Composition (Tier 2 — Val Bench, ~70 new unseen problems):
  - Filter: answer in 0-99999, no overlap with reference/hard_benchmark/priority/at-risk
  - Priority: BeyondAIME > AMO-Bench > IMO-AnswerBench
  - Deterministic ordering: sort by source priority then by id
  - Cap at 70 problems

Tier 0 (priority debug) and Tier 1 (at-risk) are embedded in the notebook, not here.

Usage:
  python scripts/build_test_v23.py
"""

import csv
import os
import sys

# ---- Paths ----
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(SCRIPT_DIR, '..')
DATA_DIR = os.path.join(PROJECT_DIR, 'data')

VAL_BENCH_CSV = os.path.join(DATA_DIR, 'available', 'aimo3-val-bench', 'aimo3_val.csv')
REFERENCE_CSV = os.path.join(DATA_DIR, 'active', 'reference.csv')
HARD_BENCH_CSV = os.path.join(DATA_DIR, 'available', 'hard_benchmark_30.csv')

OUT_PROBLEMS = os.path.join(DATA_DIR, 'active', 'test_problems.csv')
OUT_ANSWERS = os.path.join(DATA_DIR, 'active', 'test_answers.csv')

MAX_PROBLEMS = 70

# IDs embedded in notebook (Tier 0 + Tier 1) — exclude from CSV
PRIORITY_IDS = {'86e8e5', '76aef9'}
AT_RISK_IDS = {'424e18', 'dd7f5e', 'b4ec47', '2d282e', '8fea51', '269012'}
NOTEBOOK_EMBEDDED_IDS = PRIORITY_IDS | AT_RISK_IDS

# Source priority order (lower = higher priority)
SOURCE_PRIORITY = {
    'BeyondAIME': 0,
    'AMO-Bench': 1,
    'IMO-AnswerBench': 2,
}


def load_exclude_ids():
    """Collect all IDs to exclude from the CSV."""
    exclude = set(NOTEBOOK_EMBEDDED_IDS)

    # Reference problems
    if os.path.isfile(REFERENCE_CSV):
        with open(REFERENCE_CSV) as f:
            for row in csv.DictReader(f):
                exclude.add(row['id'])
    else:
        print(f'WARNING: reference.csv not found at {REFERENCE_CSV}')

    # Hard benchmark problems (exclude by ID since val bench contains them)
    if os.path.isfile(HARD_BENCH_CSV):
        with open(HARD_BENCH_CSV) as f:
            for row in csv.DictReader(f):
                exclude.add(row['id'])
    else:
        print(f'WARNING: hard_benchmark_30.csv not found at {HARD_BENCH_CSV}')

    return exclude


def load_val_bench(exclude_ids):
    """Load and filter val bench problems."""
    if not os.path.isfile(VAL_BENCH_CSV):
        print(f'ERROR: Val bench CSV not found at {VAL_BENCH_CSV}')
        sys.exit(1)

    problems = []
    stats = {
        'total': 0,
        'skipped_answer': 0,
        'skipped_overlap': 0,
        'skipped_answer_ids': [],
        'skipped_overlap_ids': [],
        'by_source': {},
    }

    with open(VAL_BENCH_CSV) as f:
        for row in csv.DictReader(f):
            stats['total'] += 1
            pid = row['id']
            answer = int(row['answer'])
            source = row['source']

            # Filter 1: answer range
            if answer < 0 or answer > 99999:
                stats['skipped_answer'] += 1
                stats['skipped_answer_ids'].append(pid)
                continue

            # Filter 2: overlap
            if pid in exclude_ids:
                stats['skipped_overlap'] += 1
                stats['skipped_overlap_ids'].append(pid)
                continue

            problems.append({
                'id': pid,
                'problem': row['problem'],
                'answer': answer,
                'source': source,
            })

            stats['by_source'][source] = stats['by_source'].get(source, 0) + 1

    return problems, stats


def select_problems(problems, max_count):
    """Select up to max_count problems, prioritizing by source."""
    # Sort: source priority (BeyondAIME first), then by id for determinism
    problems.sort(key=lambda p: (SOURCE_PRIORITY.get(p['source'], 99), p['id']))

    selected = problems[:max_count]

    # Stats on what was selected
    sel_by_source = {}
    for p in selected:
        src = p['source']
        sel_by_source[src] = sel_by_source.get(src, 0) + 1

    return selected, sel_by_source


def write_csvs(problems):
    """Write output CSVs."""
    os.makedirs(os.path.dirname(OUT_PROBLEMS), exist_ok=True)

    with open(OUT_PROBLEMS, 'w', newline='') as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(['id', 'problem'])
        for p in problems:
            w.writerow([p['id'], p['problem']])

    with open(OUT_ANSWERS, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['id', 'answer'])
        for p in problems:
            w.writerow([p['id'], p['answer']])


def main():
    print('=' * 60)
    print('  build_test_v23.py — Val Bench test set builder')
    print('=' * 60)

    # Step 1: Collect exclusion IDs
    exclude_ids = load_exclude_ids()
    print(f'\nExclusion IDs: {len(exclude_ids)} total')
    print(f'  Priority (Tier 0): {sorted(PRIORITY_IDS)}')
    print(f'  At-risk (Tier 1):  {sorted(AT_RISK_IDS)}')
    print(f'  Reference:         {len(exclude_ids - NOTEBOOK_EMBEDDED_IDS - AT_RISK_IDS)} IDs')

    # Step 2: Load and filter val bench
    problems, stats = load_val_bench(exclude_ids)
    print(f'\nVal Bench: {stats["total"]} total problems')
    print(f'  Skipped (answer > 99999): {stats["skipped_answer"]}')
    print(f'  Skipped (overlap):        {stats["skipped_overlap"]}')
    print(f'  Remaining:                {len(problems)}')
    print(f'  By source:')
    for src in sorted(stats['by_source'], key=lambda s: SOURCE_PRIORITY.get(s, 99)):
        print(f'    {src}: {stats["by_source"][src]}')

    # Step 3: Select up to MAX_PROBLEMS
    selected, sel_by_source = select_problems(problems, MAX_PROBLEMS)
    print(f'\nSelected: {len(selected)} problems (cap={MAX_PROBLEMS})')
    print(f'  By source:')
    for src in sorted(sel_by_source, key=lambda s: SOURCE_PRIORITY.get(s, 99)):
        print(f'    {src}: {sel_by_source[src]}')

    # Step 4: Write CSVs
    write_csvs(selected)
    print(f'\nOutput:')
    print(f'  {OUT_PROBLEMS} ({len(selected)} problems)')
    print(f'  {OUT_ANSWERS}')

    # Step 5: Summary
    print(f'\n{"=" * 60}')
    print(f'  v23 Test Framework Summary')
    print(f'{"=" * 60}')
    print(f'  Tier 0 (Priority Debug): 2 problems x2 = 4 slots (in notebook)')
    print(f'  Tier 1 (At-Risk):        6 problems (in notebook)')
    print(f'  Tier 2 (Val Bench CSV):  {len(selected)} problems')
    print(f'  Total unique problems:   {2 + 6 + len(selected)}')
    print(f'  Total problem slots:     {4 + 6 + len(selected)}')
    print(f'{"=" * 60}')


if __name__ == '__main__':
    main()
