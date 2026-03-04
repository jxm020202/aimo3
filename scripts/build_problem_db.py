#!/usr/bin/env python3
"""
Merge all topic-specific DB files into a unified problem database.

Reads from:
  data/problem_db/combinatorics.json
  data/problem_db/geometry.json
  data/problem_db/number_theory_algebra.json
  data/problem_db/problems.json (fallback for missing entries)
  data/problem_db/close_votes.json

Writes:
  data/problem_db/unified.json — merged, deduplicated, enriched
"""

import json
import os

DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'problem_db')

# Standard schema — every entry gets these fields
SCHEMA = {
    'problem_id': '',
    'question': '',
    'expected_answer': None,
    'topics': [],
    'skills': '',
    'failure_mode': '',
    'common_wrong_answers': [],
    'correct_rate': '',
    'why_wrong': '',
    'correct_approach': '',
    'wave2_hint': '',
    'versions_wrong': [],
    'risk_level': '',  # from close-vote analysis
}


def normalize_entry(entry, source_file):
    """Normalize an entry to the standard schema."""
    normalized = dict(SCHEMA)

    for key in SCHEMA:
        if key in entry:
            normalized[key] = entry[key]

    # Handle 'common_wrong_answer' (singular) from problems.json
    if 'common_wrong_answer' in entry and not normalized['common_wrong_answers']:
        cwa = entry['common_wrong_answer']
        if cwa is not None:
            normalized['common_wrong_answers'] = [cwa] if not isinstance(cwa, list) else cwa

    # Use 'approach' as fallback for 'correct_approach'
    if not normalized['correct_approach'] and 'approach' in entry:
        normalized['correct_approach'] = entry['approach']

    # Use 'what_correct_attempts_did' to enrich correct_approach
    if 'what_correct_attempts_did' in entry and entry['what_correct_attempts_did']:
        if normalized['correct_approach']:
            normalized['correct_approach'] += '\n\nWhat correct attempts did: ' + entry['what_correct_attempts_did']
        else:
            normalized['correct_approach'] = entry['what_correct_attempts_did']

    normalized['_source'] = source_file
    return normalized


def load_json(filename):
    path = os.path.join(DB_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # Some files have nested structure
        if 'problems' in data:
            return data['problems']
        if 'close_votes' in data:
            return data['close_votes']
        # Try to extract list from dict values
        for key, val in data.items():
            if isinstance(val, list) and val and isinstance(val[0], dict):
                return val
    return []


def merge():
    unified = {}  # keyed by problem_id

    # Priority 1: Deep-dive topic files (richest data)
    for filename in ['combinatorics.json', 'geometry.json', 'number_theory_algebra.json']:
        entries = load_json(filename)
        for entry in entries:
            pid = entry.get('problem_id', '')
            if pid:
                unified[pid] = normalize_entry(entry, filename)

    # Priority 2: Full DB extraction (fill gaps)
    entries = load_json('problems.json')
    for entry in entries:
        pid = entry.get('problem_id', '')
        if pid and pid not in unified:
            unified[pid] = normalize_entry(entry, 'problems.json')
        elif pid and pid in unified:
            # Merge missing fields from problems.json
            existing = unified[pid]
            norm = normalize_entry(entry, 'problems.json')
            for key in SCHEMA:
                if not existing[key] and norm[key]:
                    existing[key] = norm[key]

    # Priority 3: Close-vote data (enrich with risk levels)
    close_data = load_json('close_votes.json')
    for entry in close_data:
        pid = entry.get('problem_id', '')
        if not pid:
            continue
        if pid in unified:
            # Add close-vote info
            if 'risk_level' in entry:
                unified[pid]['risk_level'] = entry['risk_level']
            if 'why_close' in entry and not unified[pid]['why_wrong']:
                unified[pid]['why_wrong'] = entry['why_close']
            if 'vote_distribution' in entry:
                unified[pid]['vote_distribution'] = entry['vote_distribution']
        else:
            # Close-vote problem not in other sources — add it
            norm = normalize_entry(entry, 'close_votes.json')
            if 'why_close' in entry:
                norm['why_wrong'] = entry['why_close']
            norm['failure_mode'] = 'close_vote'
            unified[pid] = norm

    # Clean up: remove _source, ensure all fields present
    result = []
    for pid in sorted(unified.keys()):
        entry = unified[pid]
        entry.pop('_source', None)
        # Ensure topics is a list
        if isinstance(entry['topics'], str):
            entry['topics'] = [t.strip() for t in entry['topics'].split(',')]
        result.append(entry)

    return result


def main():
    result = merge()

    out_path = os.path.join(DB_DIR, 'unified.json')
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f'Unified DB: {len(result)} problems')
    print(f'Written to: {out_path}')

    # Summary
    by_mode = {}
    by_topic = {}
    has_question = 0
    has_approach = 0
    has_hint = 0

    for p in result:
        mode = p['failure_mode'] or 'unknown'
        by_mode[mode] = by_mode.get(mode, 0) + 1
        for t in p['topics']:
            by_topic[t] = by_topic.get(t, 0) + 1
        if p['question']:
            has_question += 1
        if p['correct_approach']:
            has_approach += 1
        if p['wave2_hint']:
            has_hint += 1

    print(f'\nBy failure mode:')
    for mode, count in sorted(by_mode.items(), key=lambda x: -x[1]):
        print(f'  {mode}: {count}')

    print(f'\nBy topic:')
    for topic, count in sorted(by_topic.items(), key=lambda x: -x[1]):
        print(f'  {topic}: {count}')

    print(f'\nCompleteness:')
    print(f'  Has question text: {has_question}/{len(result)}')
    print(f'  Has correct_approach: {has_approach}/{len(result)}')
    print(f'  Has wave2_hint: {has_hint}/{len(result)}')


if __name__ == '__main__':
    main()
