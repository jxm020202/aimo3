#!/usr/bin/env python3
"""
Wave 1+2 Pipeline Simulation: Trace the full prompt assembly.

Matches the current notebook code (cell 8 CFG, cell 9 ProblemDB, cell 14 AIMO3Solver).

Usage:
    # Show what gets injected for a taxonomy
    python3 log_exploration/wave1_simulation.py --taxonomy algebra.functions.grid_coloring

    # Show full Wave 2 prompt for a problem ID (looks up in val bench CSV)
    python3 log_exploration/wave1_simulation.py --problem 29714f

    # Show Wave 1 classifier input (taxonomy tree + problem)
    python3 log_exploration/wave1_simulation.py --wave1 29714f

    # Show all taxonomies in a category (with triggers + technique)
    python3 log_exploration/wave1_simulation.py --list algebra

    # Show Wave 1 classification results from a diagnostic log
    python3 log_exploration/wave1_simulation.py --log output/shiv-v12/diagnostic.log

    # Dry-run: show exactly what Wave 2 agent sees (system + developer + user)
    python3 log_exploration/wave1_simulation.py --dry-run --taxonomy algebra.functions.grid_coloring

    # Show taxonomy tree (what Wave 1 classifier sees as MCQ options)
    python3 log_exploration/wave1_simulation.py --tree

    # Simulate _build_taxonomy_injection for a Vboxed guess
    python3 log_exploration/wave1_simulation.py --inject algebra.functions.grid_coloring
"""

import argparse
import csv
import os
import re
import sqlite3
import sys
from collections import defaultdict

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'data', 'problem_db_upload', 'problems.db')
VAL_CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'data', 'available', 'aimo3-val-bench', 'aimo3_val.csv')


def load_db():
    if not os.path.exists(DB_PATH):
        print(f'ERROR: DB not found at {DB_PATH}')
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Replicates ProblemDB methods from cell 9 ──

def get_taxonomy_tree(conn) -> str:
    """Replicate ProblemDB.get_taxonomy_tree() — returns all taxonomy paths with triggers + technique."""
    rows = conn.execute(
        'SELECT DISTINCT category, taxonomy, triggers, technique FROM problems ORDER BY category, taxonomy'
    ).fetchall()

    tree = defaultdict(list)
    for cat, tax, triggers, technique in rows:
        tree[cat].append(f'  {tax} — {triggers} | {technique}')

    parts = []
    for cat in sorted(tree.keys()):
        parts.append(f'{cat}/')
        parts.extend(tree[cat])
    return '\n'.join(parts)


def format_notes(matches, max_chars=4000):
    """Replicate ProblemDB.format_notes() from cell 9."""
    if not matches:
        return ''

    parts = []
    total = 0
    for m in matches:
        tax = m['taxonomy'] if isinstance(m, dict) else m['taxonomy']
        note = (
            f'--- [{tax}] ---\n'
            f'Triggers: {m["triggers"]}\n'
            f'Technique: {m["technique"]}\n'
            f'Question: {m["question"]}\n'
            f'Answer: {m["answer"]}'
        )
        if total + len(note) > max_chars:
            break
        parts.append(note)
        total += len(note)

    if not parts:
        return ''

    header = '[Our IMO expert has given tips and tricks for this problem.]\n\n'
    footer = (
        '\n\n[END EXPERT NOTES]\n\n'
        'Our IMO expert has also shared his special notes database. '
        'If you are stuck or want more hints, query it:\n'
        'import sqlite3; db = sqlite3.connect("/kaggle/input/aimo3-problem-db/problems.db")\n'
        'Schema: id, category, topic, subtopic, taxonomy, triggers, technique, question, answer\n'
        'db.execute("SELECT taxonomy, triggers, technique FROM problems WHERE category=?", (CATEGORY,)).fetchall()\n'
        'Find the closest match, then read the full approach:\n'
        'db.execute("SELECT technique, question, answer FROM problems WHERE taxonomy=?", (TAX,)).fetchone()'
    )
    return header + '\n\n'.join(parts) + footer


# ── Replicates _select_taxonomy from cell 14 ──

def select_taxonomy(results: list) -> list[str]:
    """Replicate AIMO3Solver._select_taxonomy() — confidence-weighted, 50% threshold."""
    votes = defaultdict(float)

    for r in results:
        tax = r.get('taxonomy')
        conf = r.get('conf', 1.0)
        if tax:
            # Handle comma-separated multiple taxonomies
            for t in tax.split(','):
                t = t.strip()
                if t:
                    votes[t] += conf

    total_attempts = len(results)
    threshold = total_attempts * 0.5  # >50% of attempts

    sorted_votes = sorted(votes.items(), key=lambda x: x[1], reverse=True)

    selected = [tax for tax, v in sorted_votes if v > threshold]

    print(f'\n=== TAXONOMY VOTES (threshold: >{threshold:.1f} of {total_attempts}) ===')
    for tax, v in sorted_votes[:8]:
        marker = ' <-- SELECTED' if tax in selected else ''
        pct = v / total_attempts * 100 if total_attempts else 0
        print(f'  {tax}: {v:.1f} weighted votes ({pct:.0f}%){marker}')

    if not selected:
        print(f'  ** NO CONSENSUS — nothing exceeds 50% threshold **')
    print(f'=== END VOTES ===\n')

    return selected


# ── Replicates _build_taxonomy_injection from cell 14 ──

def build_taxonomy_injection(conn, taxonomy: str) -> str:
    """Replicate AIMO3Solver._build_taxonomy_injection() — the Vbox→injection flow."""
    if '.' not in taxonomy:
        # Category-only guess → return all subtopics
        rows = conn.execute(
            'SELECT DISTINCT taxonomy, triggers FROM problems WHERE category = ? ORDER BY taxonomy',
            (taxonomy,)
        ).fetchall()

        if not rows:
            return (
                f'No taxonomy paths found for category "{taxonomy}". '
                f'Available categories: algebra, combinatorics, geometry, number_theory. '
                f'Try again with \\Vboxed{{category}}.'
            )

        options = '\n'.join(f'  {r["taxonomy"]} — {r["triggers"]}' for r in rows)
        return (
            f'Category: {taxonomy}\n'
            f'Available taxonomy paths:\n{options}\n\n'
            f'Pick the best match. Output \\Vboxed{{category.topic.subtopic}} with the full path.'
        )
    else:
        # Full taxonomy path → query DB, return content
        rows = conn.execute('SELECT * FROM problems WHERE taxonomy = ?', (taxonomy,)).fetchall()
        if not rows:
            # Try partial match on category.topic
            parts = taxonomy.split('.')
            if len(parts) >= 2:
                rows = conn.execute(
                    'SELECT * FROM problems WHERE category = ? AND topic = ?',
                    (parts[0], parts[1])
                ).fetchall()

        if rows:
            notes = format_notes(rows)
            pid = rows[0]['id']
            return (
                f'Option: {taxonomy} | id: {pid}\n'
                f'Matching entries: {len(rows)}\n\n'
                f'{notes}\n\n'
                f'Does this match? Confirm with \\boxed{{{taxonomy} : {pid}}}. '
                f'To add more picks, use \\Vboxed{{other.path}} to see another entry.'
            )
        else:
            return (
                f'No problems found for "{taxonomy}". '
                f'Try a different path with \\Vboxed{{category.topic.subtopic}}.'
            )


# ── Commands ──

def cmd_taxonomy(args):
    """Show what gets injected for a given taxonomy."""
    db = load_db()
    rows = db.execute('SELECT * FROM problems WHERE taxonomy = ?', (args.taxonomy,)).fetchall()
    if not rows:
        rows = db.execute('SELECT * FROM problems WHERE taxonomy LIKE ?', (f'%{args.taxonomy}%',)).fetchall()
        if rows:
            print(f'No exact match for "{args.taxonomy}". Partial matches:')
            for r in rows:
                print(f'  {r["taxonomy"]}')
            return
        print(f'No matches for "{args.taxonomy}"')
        return

    notes = format_notes(rows)
    print(f'=== INJECTED NOTES ({len(notes)} chars, {len(rows)} matches) ===\n')
    print(notes)
    print(f'\n=== END ===')


def cmd_problem(args):
    """Show full Wave 2 prompt for a problem ID."""
    problem_text = None
    if os.path.exists(VAL_CSV):
        with open(VAL_CSV) as f:
            for row in csv.DictReader(f):
                if row['id'] == args.problem:
                    problem_text = row['problem']
                    print(f'Problem: {args.problem} | Category: {row["category"]} | Answer: {row["answer"]}')
                    break

    if not problem_text:
        print(f'Problem {args.problem} not found in val CSV')
        return

    db = load_db()
    db_row = db.execute('SELECT taxonomy FROM problems WHERE id = ?', (args.problem,)).fetchone()
    if db_row:
        taxonomy = db_row['taxonomy']
        print(f'DB taxonomy: {taxonomy} (exact match — hardcoded path)')
    else:
        print(f'Not in DB — Wave 1 would classify it')
        taxonomy = None

    if taxonomy:
        rows = db.execute('SELECT * FROM problems WHERE taxonomy = ?', (taxonomy,)).fetchall()
        notes = format_notes(rows)
    else:
        notes = ''

    preference_prompt = '(preference_prompt omitted for brevity)'
    if notes:
        user_input = f'{notes}\n\n{problem_text} {preference_prompt}'
    else:
        user_input = f'{problem_text} {preference_prompt}'

    print(f'\n=== FULL WAVE 2 USER MESSAGE ({len(user_input)} chars) ===\n')
    print(user_input)
    print(f'\n=== END ===')


def cmd_wave1(args):
    """Show full Wave 1 classifier input for a problem ID.
    Replicates classify_problem() from cell 14."""
    problem_text = None
    if os.path.exists(VAL_CSV):
        with open(VAL_CSV) as f:
            for row in csv.DictReader(f):
                if row['id'] == args.wave1:
                    problem_text = row['problem']
                    print(f'Problem: {args.wave1} | Category: {row["category"]} | Answer: {row["answer"]}')
                    break

    if not problem_text:
        print(f'Problem {args.wave1} not found in val CSV')
        return

    db = load_db()
    tree = get_taxonomy_tree(db)

    # This is exactly what classify_problem() builds
    classifier_input = (
        f'[TAXONOMY TREE — All available classification paths]\n{tree}\n[END TAXONOMY TREE]\n\n'
        f'Classify this problem:\n{problem_text}'
    )

    # Wave 1 system prompt from cell 8
    wave1_system = (
        'You are an IMO specialist. A math problem is shown below along with a list of taxonomy options.\n'
        'Each option has a taxonomy path, trigger keywords, and a technique summary.\n\n'
        'This is a multiple choice question. Pick 1 to 4 options that best match the problem.\n\n'
        'STEP 1: Read the problem. Pick the best matching taxonomy. '
        'Output \\Vboxed{category.topic.subtopic}\n'
        'You MUST use \\Vboxed first — never go straight to \\boxed.\n\n'
        'STEP 2: You will see the full database entry for your choice, including its id. '
        'Confirm with \\boxed{taxonomy : id}. '
        'To add more picks, use \\Vboxed{other.path} to see its entry too.\n'
        'Repeat until you have 1-4 confirmed picks, then output final \\boxed{a.b.c : id1, x.y.z : id2}\n\n'
        'Rules:\n'
        '- Pick 1-4 options. More is better if multiple topics apply.\n'
        '- You MUST include the id from the DB entry to confirm: \\boxed{taxonomy : id}\n'
        '- Pick from the list. Do not invent taxonomy paths.\n'
        '- Do NOT solve the problem. Only classify it.\n'
        '- Be concise.\n'
    )

    tree_lines = tree.count('\n') + 1
    total_entries = sum(1 for line in tree.split('\n') if line.startswith('  '))

    print(f'\n{"="*70}')
    print(f'  WAVE 1 CLASSIFIER — MESSAGE STRUCTURE')
    print(f'{"="*70}')
    print(f'\n--- SYSTEM ({len(wave1_system)} chars) ---')
    print(wave1_system)
    print(f'\n--- USER ({len(classifier_input)} chars, {tree_lines} tree lines, {total_entries} taxonomy entries) ---')
    print(classifier_input[:500])
    print(f'\n... ({len(classifier_input) - 500} more chars) ...')
    print(f'\n{"="*70}')
    print(f'  WAVE 1 MULTI-TURN FLOW')
    print(f'{"="*70}')
    print(f'Turn 1: Model reads tree + problem, outputs \\Vboxed{{taxonomy}}')
    print(f'Turn 2: Host injects DB entry (via _build_taxonomy_injection). Model confirms \\boxed{{taxonomy : id}}')
    print(f'Turn 3+: (optional) Model picks more with \\Vboxed{{other}}, host injects again')
    print(f'Max turns: 6 | Temperature: 0.1 | ReasoningEffort: HIGH')
    print(f'\nExample injection for a Vbox guess:')

    # Show example injection for a random taxonomy
    example_tax = db.execute('SELECT taxonomy FROM problems LIMIT 1').fetchone()
    if example_tax:
        print(f'\n  \\Vboxed{{{example_tax["taxonomy"]}}} →')
        injection = build_taxonomy_injection(db, example_tax['taxonomy'])
        for line in injection.split('\n')[:10]:
            print(f'  | {line}')
        if injection.count('\n') > 10:
            print(f'  | ... ({injection.count(chr(10)) - 10} more lines)')


def cmd_list(args):
    """List all taxonomies in a category with triggers + technique."""
    db = load_db()
    rows = db.execute(
        'SELECT taxonomy, triggers, technique FROM problems WHERE category = ? ORDER BY taxonomy',
        (args.list,)
    ).fetchall()
    print(f'{args.list}: {len(rows)} entries\n')
    for r in rows:
        tech_preview = r['technique'][:60] + '...' if len(r['technique']) > 60 else r['technique']
        print(f'  {r["taxonomy"]}')
        print(f'    triggers: {r["triggers"][:80]}')
        print(f'    technique: {tech_preview}')


def cmd_tree(args):
    """Show the full taxonomy tree (what Wave 1 model sees as MCQ options)."""
    db = load_db()
    tree = get_taxonomy_tree(db)
    total_entries = sum(1 for line in tree.split('\n') if line.startswith('  '))
    print(f'=== TAXONOMY TREE ({total_entries} entries, {len(tree)} chars) ===\n')
    print(tree)
    print(f'\n=== END TREE ===')


def cmd_inject(args):
    """Simulate _build_taxonomy_injection for a Vboxed guess."""
    db = load_db()
    injection = build_taxonomy_injection(db, args.inject)
    print(f'=== INJECTION FOR \\Vboxed{{{args.inject}}} ({len(injection)} chars) ===\n')
    print(injection)
    print(f'\n=== END INJECTION ===')


def cmd_log(args):
    """Parse Wave 1 classification results from diagnostic log.
    Uses confidence-weighted voting with 50% threshold (matches cell 14)."""
    if not os.path.exists(args.log):
        print(f'Log not found: {args.log}')
        return

    current_problem = None
    current_expected = None
    wave1_sections = []
    current_section = None

    for line in open(args.log):
        # Match problem header: "Problem abc123 | Expected: 42"
        m = re.search(r'Problem (\w+) \| Expected: (\d+)', line)
        if m:
            current_problem = m.group(1)
            current_expected = m.group(2)

        if 'WAVE 1: CLASSIFICATION' in line:
            current_section = {
                'problem': current_problem,
                'expected': current_expected,
                'attempts': [],
                'taxonomies': [],
                'budget': '',
                'no_consensus': False,
            }

        if current_section:
            if 'Budget:' in line and 'Attempts:' in line:
                current_section['budget'] = line.strip()

            # "Attempt 1: some.taxonomy (conf=1.0, turns=2, time=5.3s)"
            m = re.search(r'Attempt \d+: (.+?) \(conf=([\d.]+), turns=(\d+), time=([\d.]+)s\)', line)
            if m:
                current_section['attempts'].append({
                    'taxonomy': m.group(1) if m.group(1) != 'None' else None,
                    'conf': float(m.group(2)),
                    'turns': int(m.group(3)),
                    'time': float(m.group(4)),
                })

            # "Taxonomies: ['geo.thing', 'alg.thing']"
            if 'Taxonomies:' in line:
                m2 = re.search(r"Taxonomies: \[(.+?)\]", line)
                if m2:
                    current_section['taxonomies'] = [t.strip().strip("'\"") for t in m2.group(1).split(',')]

            if 'NO CONSENSUS' in line:
                current_section['no_consensus'] = True

            if 'END WAVE 1 RETRIEVAL' in line or 'END WAVE 1' in line:
                wave1_sections.append(current_section)
                current_section = None

    # Also capture sections that never hit END marker
    if current_section and current_section['attempts']:
        wave1_sections.append(current_section)

    if not wave1_sections:
        print('No Wave 1 sections found in log')
        return

    print(f'Found {len(wave1_sections)} Wave 1 classifications\n')

    for s in wave1_sections:
        valid_attempts = [a for a in s['attempts'] if a['taxonomy']]
        null_attempts = len(s['attempts']) - len(valid_attempts)
        avg_turns = sum(a['turns'] for a in s['attempts']) / max(len(s['attempts']), 1)
        avg_time = sum(a['time'] for a in s['attempts']) / max(len(s['attempts']), 1)
        max_time = max((a['time'] for a in s['attempts']), default=0)

        print(f'--- {s["problem"]} (expected: {s["expected"]}) ---')
        print(f'  {s["budget"]}')
        print(f'  Attempts: {len(s["attempts"])} ({null_attempts} null) | Avg turns: {avg_turns:.1f} | Avg time: {avg_time:.1f}s | Max: {max_time:.1f}s')

        if s['no_consensus']:
            print(f'  ** NO CONSENSUS — fallback warning injected **')
        elif s['taxonomies']:
            print(f'  Selected: {s["taxonomies"]}')

        # Replicate _select_taxonomy voting logic
        selected = select_taxonomy(s['attempts'])

        # Verify selected matches what log says
        if s['taxonomies'] and set(selected) != set(s['taxonomies']):
            print(f'  !! MISMATCH: log says {s["taxonomies"]}, simulation says {selected}')

        print()


def cmd_dry_run(args):
    """Show the complete 3-message structure the Wave 2 agent sees."""
    system_prompt = (
        'You are an IMO specialist competing in a timed exam. '
        'Your goal is to find the correct integer answer (0-99999) through rigorous reasoning.\n\n'
        '... (full system_prompt from cell 8 CFG.system_prompt — ~1500 chars)'
    )

    developer_msg = (
        'Expert notes may be included at the start of the problem text. '
        'If present, read them carefully — they highlight common traps and effective approaches. '
        'Use them to guide your strategy but verify everything independently.'
    )

    db = load_db()
    rows = db.execute('SELECT * FROM problems WHERE taxonomy = ?', (args.taxonomy,)).fetchall()
    notes = format_notes(rows)

    problem_text = '<PROBLEM TEXT WOULD GO HERE>'

    if notes:
        user_input = f'{notes}\n\n{problem_text}'
    else:
        user_input = problem_text

    print('=' * 70)
    print('  MESSAGE 1: SYSTEM')
    print('=' * 70)
    print(system_prompt)
    print()
    print('=' * 70)
    print('  MESSAGE 2: DEVELOPER')
    print('=' * 70)
    print(developer_msg)
    print()
    print('=' * 70)
    print(f'  MESSAGE 3: USER ({len(user_input)} chars)')
    print('=' * 70)
    print(user_input)


def main():
    parser = argparse.ArgumentParser(description='Wave 1+2 Pipeline Simulation')
    parser.add_argument('--taxonomy', '-t', help='Show injected notes for a taxonomy')
    parser.add_argument('--problem', '-p', help='Show full Wave 2 prompt for a problem ID')
    parser.add_argument('--wave1', '-w', help='Show full Wave 1 classifier input for a problem ID')
    parser.add_argument('--list', '-l', help='List all taxonomies in a category')
    parser.add_argument('--tree', action='store_true', help='Show full taxonomy tree')
    parser.add_argument('--inject', help='Simulate _build_taxonomy_injection for a Vboxed guess')
    parser.add_argument('--log', help='Parse Wave 1 results from diagnostic log')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Show full Wave 2 3-message structure')

    args = parser.parse_args()

    if args.log:
        cmd_log(args)
    elif args.tree:
        cmd_tree(args)
    elif args.inject:
        cmd_inject(args)
    elif args.wave1:
        cmd_wave1(args)
    elif args.list:
        cmd_list(args)
    elif args.problem:
        cmd_problem(args)
    elif args.taxonomy:
        if args.dry_run:
            cmd_dry_run(args)
        else:
            cmd_taxonomy(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
