#!/usr/bin/env python3
"""
Load OlympiadBench math problems from HuggingFace and match against AIMO3 val bench.
Outputs:
  /tmp/olympiadbench_matches.json - problems matching our val bench
  /tmp/olympiadbench_all_math.json - all math problems with numeric answers (max 500)
"""

import json
import csv
import re
import sys
from collections import Counter
from datasets import load_dataset

def normalize_text(text):
    """Normalize text for matching: lowercase, collapse whitespace, strip."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text.strip().lower())
    return text

def main():
    # ---- Step 1: Load all math configs ----
    math_configs = [
        'OE_TO_maths_en_COMP',
        'OE_TO_maths_zh_CEE',
        'OE_TO_maths_zh_COMP',
        'OE_MM_maths_en_COMP',
        'OE_MM_maths_zh_CEE',
        'OE_MM_maths_zh_COMP',
        'TP_TO_maths_en_COMP',
        'TP_TO_maths_zh_CEE',
        'TP_TO_maths_zh_COMP',
        'TP_MM_maths_en_COMP',
    ]

    all_math = []
    for config in math_configs:
        print(f"Loading {config}...", flush=True)
        try:
            ds = load_dataset('Hothan/OlympiadBench', config)
            for row in ds['train']:
                entry = {
                    'id': row['id'],
                    'question': row['question'],
                    'solution': row['solution'],
                    'final_answer': row['final_answer'],
                    'answer_type': row['answer_type'],
                    'subfield': row['subfield'],
                    'subject': row['subject'],
                    'language': row['language'],
                    'modality': row['modality'],
                    'difficulty': row['difficulty'],
                    'question_type': row['question_type'],
                    'unit': row['unit'],
                    'is_multiple_answer': row['is_multiple_answer'],
                    'config': config,
                }
                all_math.append(entry)
            print(f"  -> {len(ds['train'])} problems", flush=True)
        except Exception as e:
            print(f"  ERROR loading {config}: {e}", flush=True)

    print(f"\nTotal math problems loaded: {len(all_math)}")

    # Stats
    print("\nBy answer_type:")
    for at, count in Counter(e['answer_type'] for e in all_math).most_common():
        print(f"  {at}: {count}")

    print("\nBy language:")
    for lang, count in Counter(e['language'] for e in all_math).most_common():
        print(f"  {lang}: {count}")

    print("\nBy subfield:")
    for sf, count in Counter(e['subfield'] for e in all_math).most_common():
        print(f"  {sf}: {count}")

    print("\nBy question_type:")
    for qt, count in Counter(e['question_type'] for e in all_math).most_common():
        print(f"  {qt}: {count}")

    # ---- Step 2: Load val bench ----
    val_path = '/Users/intern/Desktop/sideprojects/aimo3/data/available/aimo3-val-bench/aimo3_val.csv'
    val_problems = []
    try:
        with open(val_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                val_problems.append(row)
        print(f"\nLoaded {len(val_problems)} val bench problems")
        print(f"Val bench columns: {list(val_problems[0].keys()) if val_problems else 'empty'}")
    except Exception as e:
        print(f"\nERROR loading val bench: {e}")
        val_problems = []

    # ---- Step 3: Match using first 80 chars ----
    # Build lookup from val bench
    val_lookup = {}
    for vp in val_problems:
        # Try 'problem' or 'question' field
        text = vp.get('problem', '') or vp.get('question', '') or vp.get('Problem', '') or vp.get('Question', '')
        if text:
            key = normalize_text(text)[:80]
            val_lookup[key] = vp

    print(f"\nVal bench lookup keys: {len(val_lookup)}")
    if val_lookup:
        sample_key = list(val_lookup.keys())[0]
        print(f"Sample val key (first 80): '{sample_key[:80]}'")

    # Match OlympiadBench against val bench
    matches = []
    for entry in all_math:
        q = entry.get('question', '')
        if not q:
            continue
        key = normalize_text(q)[:80]
        if key in val_lookup:
            match_entry = {
                'olympiad_id': entry['id'],
                'olympiad_question': entry['question'][:500],
                'olympiad_answer': entry['final_answer'],
                'olympiad_solution': entry['solution'][:1000] if entry['solution'] else None,
                'olympiad_subfield': entry['subfield'],
                'val_problem': val_lookup[key],
                'match_key': key,
            }
            matches.append(match_entry)

    print(f"\nMatches found: {len(matches)}")
    for m in matches[:5]:
        print(f"  ID {m['olympiad_id']}: {m['match_key'][:60]}...")

    # Also try partial matching (first 40 chars) for more coverage
    val_lookup_short = {}
    for vp in val_problems:
        text = vp.get('problem', '') or vp.get('question', '') or vp.get('Problem', '') or vp.get('Question', '')
        if text:
            key = normalize_text(text)[:40]
            if key not in val_lookup_short:
                val_lookup_short[key] = vp

    extra_matches = []
    matched_ids = {m['olympiad_id'] for m in matches}
    for entry in all_math:
        if entry['id'] in matched_ids:
            continue
        q = entry.get('question', '')
        if not q:
            continue
        key = normalize_text(q)[:40]
        if key in val_lookup_short:
            match_entry = {
                'olympiad_id': entry['id'],
                'olympiad_question': entry['question'][:500],
                'olympiad_answer': entry['final_answer'],
                'olympiad_solution': entry['solution'][:1000] if entry['solution'] else None,
                'olympiad_subfield': entry['subfield'],
                'val_problem': val_lookup_short[key],
                'match_key_short': key,
            }
            extra_matches.append(match_entry)

    print(f"Extra matches (40-char): {len(extra_matches)}")
    all_matches = matches + extra_matches
    print(f"Total matches: {len(all_matches)}")

    # ---- Step 4: Save matches ----
    with open('/tmp/olympiadbench_matches.json', 'w') as f:
        json.dump(all_matches, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(all_matches)} matches to /tmp/olympiadbench_matches.json")

    # ---- Step 5: Save all math with numeric answers (max 500) ----
    # Filter: numeric answer type, has solution, has answer
    numeric_math = []
    for entry in all_math:
        # Only numeric answers (not proofs/theorem-proof type)
        if entry['question_type'] != 'Open-ended':
            continue
        if entry['answer_type'] not in ('Numerical', 'Expression', 'Equation'):
            continue
        if not entry['final_answer']:
            continue
        if not entry['solution']:
            continue

        # Prefer English problems, but include Chinese too
        clean_entry = {
            'id': entry['id'],
            'question': entry['question'],
            'solution': entry['solution'],
            'final_answer': entry['final_answer'],
            'answer_type': entry['answer_type'],
            'subfield': entry['subfield'],
            'language': entry['language'],
            'modality': entry['modality'],
            'difficulty': entry['difficulty'],
            'config': entry['config'],
        }
        numeric_math.append(clean_entry)

    print(f"\nNumeric/expression math problems with solutions: {len(numeric_math)}")
    print("By subfield:")
    for sf, count in Counter(e['subfield'] for e in numeric_math).most_common():
        print(f"  {sf}: {count}")
    print("By language:")
    for lang, count in Counter(e['language'] for e in numeric_math).most_common():
        print(f"  {lang}: {count}")

    # Prioritize English competition problems, then Chinese
    def sort_key(e):
        lang_score = 0 if e['language'] == 'English' else 1
        diff_score = 0 if e['difficulty'] == 'Competition' else 1
        return (lang_score, diff_score, e['id'])

    numeric_math.sort(key=sort_key)

    # Cap at 500
    capped = numeric_math[:500]
    with open('/tmp/olympiadbench_all_math.json', 'w') as f:
        json.dump(capped, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(capped)} problems to /tmp/olympiadbench_all_math.json")

    # Summary
    print("\n=== SUMMARY ===")
    print(f"Total math problems in OlympiadBench: {len(all_math)}")
    print(f"Numeric/solvable (non-proof) with solutions: {len(numeric_math)}")
    print(f"Matches with val bench: {len(all_matches)}")
    print(f"Saved to /tmp/olympiadbench_matches.json and /tmp/olympiadbench_all_math.json")

if __name__ == '__main__':
    main()
