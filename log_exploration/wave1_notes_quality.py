#!/usr/bin/env python3
"""
Wave 1 Notes Quality & Accuracy Analysis.

For each of 50 problems:
1. Did it get notes? (STUDY NOTES injection)
2. What taxonomy was assigned by Wave 1?
3. Was there a DB match?
4. Were the notes relevant/helpful?
5. Categorize: GOOD_NOTES, WRONG_NOTES, NO_MATCH, NO_NOTES, BASIC_LABEL

Cross-references with results (correct/wrong) and close calls.

Usage:
    python3 log_exploration/wave1_notes_quality.py output/shiv-latest/diagnostic.log
"""

import sys
import re
import os
import csv
import sqlite3
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'data', 'problem_db', 'problems.db')
VAL_CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'data', 'available', 'aimo3-val-bench', 'aimo3_val.csv')


def load_val_problems():
    """Load val bench problems for category info."""
    problems = {}
    if os.path.exists(VAL_CSV):
        with open(VAL_CSV) as f:
            for row in csv.DictReader(f):
                problems[row['id']] = {
                    'category': row.get('category', ''),
                    'answer': row.get('answer', ''),
                    'problem_text': row.get('problem', '')[:200],
                }
    return problems


def load_db_taxonomies():
    """Load all taxonomy entries from problems.db with their content."""
    if not os.path.exists(DB_PATH):
        print(f"ERROR: DB not found at {DB_PATH}")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        'SELECT id, category, topic, subtopic, taxonomy, triggers, technique, question, answer FROM problems'
    ).fetchall()

    db_entries = {}
    for r in rows:
        db_entries[r['taxonomy']] = {
            'id': r['id'],
            'category': r['category'],
            'topic': r['topic'],
            'subtopic': r['subtopic'],
            'triggers': r['triggers'] or '',
            'technique': r['technique'] or '',
            'question': (r['question'] or '')[:200],
            'answer': (r['answer'] or '')[:200],
        }
    conn.close()
    return db_entries


def parse_wave1_full(logfile):
    """Parse Wave 1 sections with full detail including actual notes injected."""
    sections = {}
    current_problem = None
    current_expected = None
    current_section = None
    capture_notes = False
    notes_buffer = []

    for line in open(logfile, errors='replace'):
        # Match problem header
        m = re.search(r'Problem (\w+) \| Expected: (\d+)', line)
        if m:
            current_problem = m.group(1)
            current_expected = m.group(2)

        if 'WAVE 1: CLASSIFICATION' in line:
            current_section = {
                'problem': current_problem,
                'expected': current_expected,
                'attempts': [],
                'taxonomies_selected': [],
                'no_consensus': False,
                'notes_chars': 0,
                'db_matches': 0,
                'raw_taxonomies': [],  # all attempt taxonomies for voting analysis
            }

        if current_section:
            if 'Budget:' in line and 'Attempts:' in line:
                current_section['budget'] = line.strip()

            # Attempt taxonomy
            m = re.search(r'Attempt \d+: (.+?) \(conf=([\d.]+), turns=(\d+), time=([\d.]+)s\)', line)
            if m:
                tax = m.group(1) if m.group(1) != 'None' else None
                current_section['attempts'].append({
                    'taxonomy': tax,
                    'conf': float(m.group(2)),
                    'turns': int(m.group(3)),
                    'time': float(m.group(4)),
                })
                if tax:
                    current_section['raw_taxonomies'].append(tax)

            # Selected taxonomies
            if 'Taxonomies:' in line:
                m2 = re.search(r"Taxonomies: \[(.+?)\]", line)
                if m2:
                    taxes = [t.strip().strip("'\"") for t in m2.group(1).split(',')]
                    current_section['taxonomies_selected'] = taxes

            if 'NO CONSENSUS' in line:
                current_section['no_consensus'] = True

            # DB match count
            m3 = re.search(r'Total matches: (\d+)', line)
            if m3:
                current_section['db_matches'] = int(m3.group(1))

            # Notes size
            m4 = re.search(r'Notes: (\d+) chars', line)
            if m4:
                current_section['notes_chars'] = int(m4.group(1))

            if 'END WAVE 1 RETRIEVAL' in line or 'END WAVE 1' in line:
                if current_section['problem']:
                    sections[current_section['problem']] = current_section
                current_section = None

    # Capture last section
    if current_section and current_section.get('problem') and current_section['attempts']:
        sections[current_section['problem']] = current_section

    return sections


def parse_injected_notes(logfile):
    """Parse what notes were actually injected into the user prompt for each problem."""
    notes_by_problem = {}
    current_problem = None
    in_user_prompt = False
    has_expert_notes = False
    expert_note_lines = []

    for line in open(logfile, errors='replace'):
        m = re.search(r'Problem (\w+) \| Expected: (\d+)', line)
        if m:
            if current_problem and has_expert_notes:
                notes_by_problem[current_problem] = '\n'.join(expert_note_lines)
            current_problem = m.group(1)
            in_user_prompt = False
            has_expert_notes = False
            expert_note_lines = []

        if '=== USER PROMPT' in line:
            in_user_prompt = True
            expert_note_lines = []
            continue

        if '=== END USER PROMPT' in line:
            in_user_prompt = False
            continue

        if in_user_prompt:
            if '[Our IMO expert has given tips and tricks' in line:
                has_expert_notes = True
            if has_expert_notes and '[END EXPERT NOTES]' not in line:
                expert_note_lines.append(line.rstrip())
            if '[END EXPERT NOTES]' in line:
                # Capture everything up to END EXPERT NOTES
                pass

        # Also capture the "could not classify" warning
        if in_user_prompt and 'could not confidently classify' in line:
            if current_problem:
                notes_by_problem[current_problem] = 'NO_CONSENSUS_WARNING'

    # Last problem
    if current_problem and has_expert_notes:
        notes_by_problem[current_problem] = '\n'.join(expert_note_lines)

    return notes_by_problem


def compute_taxonomy_votes(attempts):
    """Replicate _select_taxonomy voting logic."""
    votes = defaultdict(float)
    for a in attempts:
        tax = a.get('taxonomy')
        conf = a.get('conf', 1.0)
        if tax:
            for t in tax.split(','):
                t = t.strip()
                if t and t != 'taxonomy':
                    votes[t] += conf
    total = len(attempts)
    threshold = total * 0.5
    sorted_votes = sorted(votes.items(), key=lambda x: x[1], reverse=True)
    selected = [tax for tax, v in sorted_votes if v > threshold]
    return selected, sorted_votes, threshold


def classify_notes_quality(w1_section, db_entries, val_info, problem_result):
    """
    Classify each problem's notes into:
    - GOOD_NOTES: Got relevant, helpful notes
    - WRONG_NOTES: Got notes but wrong topic / irrelevant
    - NO_MATCH: Classified correctly but no DB entry
    - NO_NOTES: No classification or notes injection happened
    - BASIC_LABEL: Got a taxonomy label but DB entry was stub/generic
    """
    if not w1_section:
        return 'NO_NOTES', None, 'No Wave 1 section found'

    selected, sorted_votes, _ = compute_taxonomy_votes(w1_section['attempts'])
    top_taxonomy = sorted_votes[0][0] if sorted_votes else None

    # Filter out junk taxonomies
    if top_taxonomy in ('taxonomy', 'basic.basic.basic', 'a.b.c', 'x.y.z'):
        clean_votes = [(t, v) for t, v in sorted_votes if t not in ('taxonomy', 'basic.basic.basic', 'a.b.c', 'x.y.z')]
        if clean_votes:
            top_taxonomy = clean_votes[0][0]

    if w1_section['no_consensus'] or not selected:
        # No consensus - check if top taxonomy was close
        if top_taxonomy and top_taxonomy not in ('taxonomy', 'basic.basic.basic'):
            # Had a reasonable top taxonomy but didn't pass threshold
            if top_taxonomy in db_entries:
                return 'NO_NOTES', top_taxonomy, f'No consensus (top={top_taxonomy}, had DB match but threshold not met)'
            else:
                return 'NO_NOTES', top_taxonomy, f'No consensus (top={top_taxonomy}, no DB entry either)'
        return 'NO_NOTES', top_taxonomy, 'No consensus, no clear taxonomy'

    # Has selected taxonomies - check quality
    selected_clean = [t for t in selected if t not in ('basic.basic.basic', 'taxonomy', 'a.b.c', 'x.y.z')]

    if not selected_clean:
        if any(t == 'basic.basic.basic' for t in selected):
            return 'BASIC_LABEL', 'basic.basic.basic', 'Classified as basic - no useful technique'
        return 'NO_NOTES', top_taxonomy, 'Selected junk taxonomies only'

    # Check DB matches
    primary_tax = selected_clean[0]
    if primary_tax not in db_entries:
        # Check partial match
        parts = primary_tax.split('.')
        partial_matches = [t for t in db_entries if t.startswith(f'{parts[0]}.{parts[1]}') if len(parts) >= 2]
        if partial_matches:
            return 'NO_MATCH', primary_tax, f'Classified as {primary_tax}, partial DB matches exist: {partial_matches[:3]}'
        return 'NO_MATCH', primary_tax, f'Classified as {primary_tax}, NO DB entry'

    # Has DB match - evaluate relevance
    db_entry = db_entries[primary_tax]
    val_category = val_info.get('category', '') if val_info else ''

    # Check if DB entry category matches problem category
    tax_category = primary_tax.split('.')[0] if '.' in primary_tax else primary_tax

    # Check if technique is substantive vs stub
    technique = db_entry.get('technique', '')
    if len(technique) < 50:
        return 'BASIC_LABEL', primary_tax, f'DB entry exists but technique is stub ({len(technique)} chars)'

    # Check category alignment
    if val_category and tax_category != val_category:
        # Cross-category: might be valid (e.g., algebra.number_theory_crossover)
        if 'crossover' in primary_tax:
            pass  # OK, crossover is intentional
        else:
            # Check if topic keywords appear in problem text
            problem_text = val_info.get('problem_text', '') if val_info else ''
            triggers = db_entry.get('triggers', '').lower()
            trigger_words = [w.strip() for w in triggers.split(',')]
            matches = sum(1 for tw in trigger_words if tw and tw in problem_text.lower())
            if matches == 0:
                return 'WRONG_NOTES', primary_tax, f'Category mismatch: problem={val_category}, notes={tax_category}, no trigger overlap'

    return 'GOOD_NOTES', primary_tax, f'DB match with substantive technique ({len(technique)} chars)'


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 wave1_notes_quality.py <logfile>")
        sys.exit(1)

    logfile = sys.argv[1]

    print(f"Parsing {logfile}...")
    problems = parse_log(logfile)
    print(f"Parsed {len(problems)} problems")

    prob_lookup = {p.problem_id: p for p in problems}

    # Load supporting data
    val_problems = load_val_problems()
    db_entries = load_db_taxonomies()
    wave1 = parse_wave1_full(logfile)
    injected = parse_injected_notes(logfile)

    print(f"Wave 1 sections: {len(wave1)}")
    print(f"DB taxonomies: {len(db_entries)}")
    print(f"Val problems: {len(val_problems)}")
    print(f"Problems with injected notes: {len([v for v in injected.values() if v != 'NO_CONSENSUS_WARNING'])}")

    # ── Classify each problem ──
    results = []
    for p in problems:
        pid = p.problem_id
        w1 = wave1.get(pid)
        val = val_problems.get(pid)

        category, taxonomy, reason = classify_notes_quality(w1, db_entries, val, p)

        # Get vote details
        if w1:
            selected, sorted_votes, threshold = compute_taxonomy_votes(w1['attempts'])
            top_vote_pct = (sorted_votes[0][1] / len(w1['attempts']) * 100) if sorted_votes else 0
            n_attempts = len(w1['attempts'])
        else:
            selected = []
            sorted_votes = []
            top_vote_pct = 0
            n_attempts = 0

        # Check if problem's actual answer DB entry exists (self-match)
        self_in_db = pid in [e['id'] for e in db_entries.values()]

        # Check notes injection
        had_expert_notes = pid in injected and injected[pid] != 'NO_CONSENSUS_WARNING'
        had_warning = pid in injected and injected[pid] == 'NO_CONSENSUS_WARNING'

        results.append({
            'pid': pid,
            'correct': p.correct,
            'expected': p.expected,
            'predicted': p.predicted,
            'val_category': val.get('category', '?') if val else '?',
            'category': category,
            'taxonomy': taxonomy,
            'reason': reason,
            'top_vote_pct': top_vote_pct,
            'n_attempts': n_attempts,
            'had_expert_notes': had_expert_notes,
            'had_warning': had_warning,
            'self_in_db': self_in_db,
            'notes_chars': w1.get('notes_chars', 0) if w1 else 0,
            'db_matches': w1.get('db_matches', 0) if w1 else 0,
            'votes': p.votes,
        })

    # ═══════════════════════════════════════════════════════════════
    # 1. SUMMARY TABLE
    # ═══════════════════════════════════════════════════════════════
    print(f"\n{'='*140}")
    print(f"  WAVE 1 NOTES QUALITY — ALL 50 PROBLEMS")
    print(f"{'='*140}")
    print(f"{'#':>3} {'PID':8s} {'Result':7s} {'Category':12s} {'Val Cat':12s} {'Taxonomy':50s} {'Vote%':6s} {'Notes':7s} {'Chars':6s}")
    print(f"{'─'*3} {'─'*8} {'─'*7} {'─'*12} {'─'*12} {'─'*50} {'─'*6} {'─'*7} {'─'*6}")

    for i, r in enumerate(results, 1):
        result_str = "OK" if r['correct'] else "WRONG"
        tax_str = (r['taxonomy'] or '-')[:50]
        notes_str = "YES" if r['had_expert_notes'] else ("WARN" if r['had_warning'] else "NO")
        marker = " <--" if not r['correct'] else ""

        print(f"{i:3d} {r['pid'][:8]:8s} {result_str:7s} {r['category']:12s} {r['val_category']:12s} {tax_str:50s} {r['top_vote_pct']:5.0f}% {notes_str:7s} {r['notes_chars']:6d}{marker}")

    # ═══════════════════════════════════════════════════════════════
    # 2. COUNTS PER CATEGORY
    # ═══════════════════════════════════════════════════════════════
    print(f"\n{'='*80}")
    print(f"  CATEGORY COUNTS")
    print(f"{'='*80}")

    cat_counts = defaultdict(lambda: {'total': 0, 'correct': 0})
    for r in results:
        cat_counts[r['category']]['total'] += 1
        if r['correct']:
            cat_counts[r['category']]['correct'] += 1

    for cat in ['GOOD_NOTES', 'WRONG_NOTES', 'NO_MATCH', 'NO_NOTES', 'BASIC_LABEL']:
        c = cat_counts.get(cat, {'total': 0, 'correct': 0})
        rate = (c['correct'] / c['total'] * 100) if c['total'] else 0
        wrong_pids = [r['pid'][:6] for r in results if r['category'] == cat and not r['correct']]
        wrong_str = f"  Wrong: {', '.join(wrong_pids)}" if wrong_pids else ""
        print(f"  {cat:15s}: {c['total']:3d} problems ({c['correct']}/{c['total']} correct = {rate:.0f}%){wrong_str}")

    # ═══════════════════════════════════════════════════════════════
    # 3. WRONG PROBLEMS: Notes Impact Analysis
    # ═══════════════════════════════════════════════════════════════
    print(f"\n{'='*120}")
    print(f"  WRONG PROBLEMS (8): Notes Impact Analysis")
    print(f"{'='*120}")

    wrong_results = [r for r in results if not r['correct']]
    for r in wrong_results:
        print(f"\n  {'─'*116}")
        print(f"  {r['pid'][:8]} | Expected: {r['expected']} | Predicted: {r['predicted']} | Val: {r['val_category']}")
        print(f"  Notes category: {r['category']}")
        print(f"  Top taxonomy: {r['taxonomy']} ({r['top_vote_pct']:.0f}% vote)")
        print(f"  Reason: {r['reason']}")
        print(f"  Expert notes injected: {r['had_expert_notes']} | Warning: {r['had_warning']} | Notes chars: {r['notes_chars']}")
        print(f"  Votes: {r['votes']}")

        # Analysis of whether notes helped or hurt
        if r['category'] == 'WRONG_NOTES':
            print(f"  ** NOTES LIKELY HURT: Wrong topic notes may have misled the model **")
        elif r['category'] == 'NO_NOTES':
            print(f"  ** NO NOTES: Would notes have helped? Top taxonomy was {r['taxonomy']} **")
            # Check what taxonomy SHOULD have been
            w1 = wave1.get(r['pid'])
            if w1:
                _, sorted_votes, _ = compute_taxonomy_votes(w1['attempts'])
                print(f"  All taxonomy votes:")
                for tax, v in sorted_votes[:6]:
                    in_db = "IN DB" if tax in db_entries else "NOT IN DB"
                    print(f"    {tax}: {v:.1f} ({in_db})")
        elif r['category'] == 'GOOD_NOTES':
            print(f"  ** HAD GOOD NOTES but still wrong — notes weren't sufficient **")

    # ═══════════════════════════════════════════════════════════════
    # 4. CLOSE CALLS: Notes Impact
    # ═══════════════════════════════════════════════════════════════
    print(f"\n{'='*120}")
    print(f"  CLOSE CALLS: Notes Impact")
    print(f"{'='*120}")

    close_pids_prefix = ['d4b03c', '4e5a01', '2e2ccb', '485d27']
    for prefix in close_pids_prefix:
        for r in results:
            if r['pid'].startswith(prefix):
                p = prob_lookup[r['pid']]
                # Compute vote margin
                vote_counts = {}
                for att in p.attempts:
                    if att.answer is not None:
                        vote_counts[att.answer] = vote_counts.get(att.answer, 0) + 1
                sorted_vc = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
                margin = sorted_vc[0][1] - sorted_vc[1][1] if len(sorted_vc) > 1 else sorted_vc[0][1]

                print(f"\n  {r['pid'][:8]} | {'CORRECT' if r['correct'] else 'WRONG'} | Margin: {margin} votes")
                print(f"  Notes: {r['category']} | Taxonomy: {r['taxonomy']}")
                print(f"  Expert notes: {r['had_expert_notes']} | Chars: {r['notes_chars']}")
                print(f"  Top votes: {sorted_vc[:4]}")
                break

    # ═══════════════════════════════════════════════════════════════
    # 5. MISSING DB TAXONOMIES
    # ═══════════════════════════════════════════════════════════════
    print(f"\n{'='*120}")
    print(f"  MISSING DB TAXONOMIES (taxonomies Wave 1 tried to use but not in DB)")
    print(f"{'='*120}")

    missing_taxonomies = defaultdict(list)
    for r in results:
        if r['category'] in ('NO_MATCH', 'NO_NOTES'):
            w1 = wave1.get(r['pid'])
            if w1:
                _, sorted_votes, _ = compute_taxonomy_votes(w1['attempts'])
                for tax, v in sorted_votes:
                    if tax not in db_entries and tax not in ('taxonomy', 'basic.basic.basic', 'a.b.c', 'x.y.z') and '.' in tax:
                        pct = v / len(w1['attempts']) * 100
                        if pct >= 10:  # At least 10% of votes
                            missing_taxonomies[tax].append({
                                'pid': r['pid'][:6],
                                'correct': r['correct'],
                                'vote_pct': pct,
                            })

    print(f"\n  {'Taxonomy':55s} {'Problems':30s} {'All Correct?':12s}")
    print(f"  {'─'*55} {'─'*30} {'─'*12}")
    for tax in sorted(missing_taxonomies.keys()):
        probs = missing_taxonomies[tax]
        prob_str = ', '.join(f"{p['pid']}({'OK' if p['correct'] else 'WRONG'})" for p in probs)
        all_correct = all(p['correct'] for p in probs)
        print(f"  {tax:55s} {prob_str:30s} {'YES' if all_correct else 'NO <--'}")

    # ═══════════════════════════════════════════════════════════════
    # 6. WRONG_NOTES RECOMMENDATIONS
    # ═══════════════════════════════════════════════════════════════
    print(f"\n{'='*120}")
    print(f"  WRONG_NOTES PROBLEMS: What Notes SHOULD Have Been")
    print(f"{'='*120}")

    for r in results:
        if r['category'] == 'WRONG_NOTES':
            print(f"\n  {r['pid'][:8]} | Val category: {r['val_category']} | Expected: {r['expected']}")
            print(f"  GOT: {r['taxonomy']}")
            # Look at what the problem actually was
            val = val_problems.get(r['pid'])
            if val:
                print(f"  Problem: {val.get('problem_text', '')[:150]}")
            # Check what taxonomy votes existed
            w1 = wave1.get(r['pid'])
            if w1:
                _, sorted_votes, _ = compute_taxonomy_votes(w1['attempts'])
                print(f"  All votes:")
                for tax, v in sorted_votes[:8]:
                    in_db = "IN DB" if tax in db_entries else "NOT IN DB"
                    pct = v / len(w1['attempts']) * 100
                    print(f"    {tax}: {v:.1f} ({pct:.0f}%) [{in_db}]")
            # Suggest what it should have been
            if val:
                val_cat = val.get('category', '')
                matching_db = [t for t in db_entries if t.startswith(val_cat + '.')]
                print(f"  DB entries in {val_cat} category: {len(matching_db)}")

    # ═══════════════════════════════════════════════════════════════
    # 7. PROBLEMS WHERE NOTES HELPED MOST (correct + had notes)
    # ═══════════════════════════════════════════════════════════════
    print(f"\n{'='*120}")
    print(f"  NOTES IMPACT SUMMARY")
    print(f"{'='*120}")

    notes_helped = [r for r in results if r['category'] == 'GOOD_NOTES' and r['correct']]
    notes_hurt = [r for r in results if r['category'] == 'WRONG_NOTES' and not r['correct']]
    notes_didnt_help = [r for r in results if r['category'] == 'GOOD_NOTES' and not r['correct']]

    print(f"\n  GOOD_NOTES + CORRECT (notes likely helped): {len(notes_helped)} problems")
    for r in notes_helped:
        print(f"    {r['pid'][:8]} | {r['taxonomy']:50s} | {r['notes_chars']} chars")

    print(f"\n  WRONG_NOTES + WRONG (notes may have hurt):  {len(notes_hurt)} problems")
    for r in notes_hurt:
        print(f"    {r['pid'][:8]} | {r['taxonomy']:50s} | Needed: {r['val_category']}")

    print(f"\n  GOOD_NOTES + WRONG (notes weren't enough):  {len(notes_didnt_help)} problems")
    for r in notes_didnt_help:
        print(f"    {r['pid'][:8]} | {r['taxonomy']:50s} | Expected: {r['expected']}")

    no_notes_wrong = [r for r in results if r['category'] in ('NO_NOTES', 'NO_MATCH') and not r['correct']]
    print(f"\n  NO_NOTES/NO_MATCH + WRONG (might've helped): {len(no_notes_wrong)} problems")
    for r in no_notes_wrong:
        print(f"    {r['pid'][:8]} | Top: {r['taxonomy']:45s} | Val: {r['val_category']}")

    # ═══════════════════════════════════════════════════════════════
    # 8. OVERALL STATS
    # ═══════════════════════════════════════════════════════════════
    print(f"\n{'='*80}")
    print(f"  OVERALL STATISTICS")
    print(f"{'='*80}")

    total = len(results)
    total_correct = sum(1 for r in results if r['correct'])

    got_notes = sum(1 for r in results if r['had_expert_notes'])
    got_warning = sum(1 for r in results if r['had_warning'])
    got_nothing = sum(1 for r in results if not r['had_expert_notes'] and not r['had_warning'])

    notes_correct = sum(1 for r in results if r['had_expert_notes'] and r['correct'])
    warn_correct = sum(1 for r in results if r['had_warning'] and r['correct'])
    nothing_correct = sum(1 for r in results if not r['had_expert_notes'] and not r['had_warning'] and r['correct'])

    print(f"""
  Total: {total_correct}/{total} correct ({total_correct/total*100:.0f}%)

  Expert notes injected:     {got_notes:3d} ({notes_correct}/{got_notes} correct = {notes_correct/got_notes*100:.0f}%)
  Warning injected:          {got_warning:3d} ({warn_correct}/{got_warning} correct = {warn_correct/got_warning*100:.0f}%)
  No injection at all:       {got_nothing:3d} ({nothing_correct}/{got_nothing if got_nothing else 1} correct = {nothing_correct/(got_nothing if got_nothing else 1)*100:.0f}%)

  Quality breakdown:
    GOOD_NOTES:  {cat_counts.get('GOOD_NOTES', {'total':0})['total']:3d} (relevant DB entry with substantive technique)
    WRONG_NOTES: {cat_counts.get('WRONG_NOTES', {'total':0})['total']:3d} (DB match but wrong topic for this problem)
    NO_MATCH:    {cat_counts.get('NO_MATCH', {'total':0})['total']:3d} (classified taxonomy not in DB)
    NO_NOTES:    {cat_counts.get('NO_NOTES', {'total':0})['total']:3d} (no consensus / classifier failed)
    BASIC_LABEL: {cat_counts.get('BASIC_LABEL', {'total':0})['total']:3d} (classified as basic / stub technique)
    """)


if __name__ == '__main__':
    main()
