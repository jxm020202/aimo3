#!/usr/bin/env python3
"""
Build SQLite problem database from unified.json + reextracted patches.

Schema: problems(problem_id, category, topics, technique_summary, question, approach, expected_answer)
FTS5 index on topics, technique_summary, approach for full-text search.

Usage:
    python3 scripts/build_sqlite_db.py
"""

import json
import os
import sqlite3

DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'problem_db')
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'problem_db_upload')
INPUT = os.path.join(DB_DIR, 'unified.json')
PATCHES = os.path.join(DB_DIR, 'reextracted.json')
OUTPUT_DB = os.path.join(DB_DIR, 'problems.db')
OUTPUT_UPLOAD = os.path.join(UPLOAD_DIR, 'problems.db')

# Map old category names to standard ones
CATEGORY_MAP = {
    'unknown': 'combinatorics',
    'algebra': 'algebra',
    'geometry': 'geometry',
    'combinatorics': 'combinatorics',
    'number_theory': 'number_theory',
    'game_theory': 'combinatorics',
    'optimization': 'algebra',
}


def normalize_category(topics_list):
    """Pick the best single category from a list of topics."""
    for t in topics_list:
        t_lower = t.lower().strip()
        if t_lower in CATEGORY_MAP:
            return CATEGORY_MAP[t_lower]
    return 'algebra'


def transform_old_entry(p):
    """Transform an old-schema unified.json entry to the new schema."""
    topics_list = p.get('topics', [])
    if isinstance(topics_list, str):
        topics_list = [t.strip() for t in topics_list.split(',')]

    category = p.get('category', '') or normalize_category(topics_list)

    # Build topics string from skills or topics list
    skills = p.get('skills', '')
    topics_str = ', '.join(topics_list) if topics_list else category
    if skills:
        topics_str = skills  # skills field is more specific

    # Use existing fields if present, otherwise fall back to old schema
    approach = p.get('approach', '') or p.get('correct_approach', '') or p.get('wave2_hint', '') or ''
    technique_summary = p.get('technique_summary', '') or p.get('skills', '') or ', '.join(topics_list)

    return {
        'problem_id': p.get('problem_id', ''),
        'category': category,
        'topics': topics_str,
        'technique_summary': technique_summary[:400],
        'question': p.get('question', ''),
        'approach': approach,
        'expected_answer': p.get('expected_answer'),
    }


def build():
    # Load base data
    with open(INPUT) as f:
        raw_problems = json.load(f)

    # Transform to new schema
    problems = {}
    for p in raw_problems:
        entry = transform_old_entry(p)
        pid = entry['problem_id']
        # Skip entries with no approach (will be patched or dropped)
        if entry['approach'] or entry['question']:
            problems[pid] = entry

    # Apply patches (reextracted entries override old ones)
    if os.path.exists(PATCHES):
        with open(PATCHES) as f:
            patches = json.load(f)
        for p in patches:
            pid = p['problem_id']
            if pid in problems:
                # Merge: patch fields override, keep question from original if patch doesn't have it
                orig_q = problems[pid].get('question', '')
                problems[pid].update(p)
                if not problems[pid].get('question'):
                    problems[pid]['question'] = orig_q
            else:
                problems[pid] = p
        print(f'Applied {len(patches)} patches')

    # Filter: drop entries with empty approach AND empty question
    before = len(problems)
    problems = {pid: p for pid, p in problems.items()
                if p.get('approach') or p.get('question')}
    if before != len(problems):
        print(f'Dropped {before - len(problems)} empty entries')

    # Build SQLite DB
    for output_path in [OUTPUT_DB, OUTPUT_UPLOAD]:
        if os.path.exists(output_path):
            os.remove(output_path)

        conn = sqlite3.connect(output_path)
        cur = conn.cursor()

        cur.execute('''
            CREATE TABLE problems (
                problem_id TEXT PRIMARY KEY,
                category TEXT,
                topics TEXT,
                technique_summary TEXT,
                question TEXT,
                answer TEXT
            )
        ''')

        # FTS5 for search
        try:
            cur.execute('''
                CREATE VIRTUAL TABLE problems_fts USING fts5(
                    problem_id,
                    category,
                    topics,
                    technique_summary,
                    answer,
                    content=problems,
                    content_rowid=rowid
                )
            ''')
            has_fts = True
        except Exception:
            has_fts = False
            print(f'FTS5 not available for {output_path}')

        for p in problems.values():
            cur.execute('''
                INSERT INTO problems
                (problem_id, category, topics, technique_summary, question, answer)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                p.get('problem_id', ''),
                p.get('category', ''),
                p.get('topics', ''),
                p.get('technique_summary', ''),
                p.get('question', ''),
                p.get('approach', ''),  # unified.json uses 'approach', DB column is 'answer'
            ))

        if has_fts:
            cur.execute("INSERT INTO problems_fts(problems_fts) VALUES('rebuild')")

        conn.commit()

        # Verify
        count = cur.execute('SELECT COUNT(*) FROM problems').fetchone()[0]
        has_answer = cur.execute(
            'SELECT COUNT(*) FROM problems WHERE length(answer) > 50'
        ).fetchone()[0]
        print(f'{output_path}: {count} problems ({has_answer} with answer)')

        # Test queries
        if has_fts:
            for kw in ['geometry', 'combinatorics', 'recurrence']:
                rows = cur.execute(
                    "SELECT problem_id, technique_summary FROM problems_fts WHERE topics MATCH ? LIMIT 2",
                    (kw,)
                ).fetchall()
                print(f'  FTS "{kw}": {len(rows)} results')
                for r in rows:
                    print(f'    {r[0][:8]}: {r[1][:70]}')

        conn.close()
        print(f'  File size: {os.path.getsize(output_path) / 1024:.1f} KB')


if __name__ == '__main__':
    build()
