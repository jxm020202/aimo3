#!/usr/bin/env python3
"""
Wave 1 Notes vs Problem DB Deep Analysis
==========================================
For each problem, cross-references the Wave 1 selected taxonomy against the
Problem DB to determine:
1. Was the right taxonomy selected?
2. Were the injected notes from the best-matching DB entry?
3. For WRONG problems: was there a better DB entry that could have helped?
4. For "no consensus" problems: what taxonomies almost made it?

Usage:
    python3 log_exploration/wave1_notes_vs_db.py output/shiv-latest-2/diagnostic.log [--db path/to/problems.db]
"""

import sys
import os
import re
import sqlite3
import argparse
from collections import defaultdict, Counter
from difflib import SequenceMatcher

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def load_db(db_path):
    """Load problem DB into memory structures."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    entries = []
    taxonomy_map = defaultdict(list)  # taxonomy -> list of entries
    category_map = defaultdict(list)  # category -> list of entries
    topic_map = defaultdict(list)     # category.topic -> list of entries

    rows = conn.execute(
        "SELECT id, category, topic, subtopic, taxonomy, triggers, technique, question, answer FROM problems"
    ).fetchall()

    for row in rows:
        entry = dict(row)
        entries.append(entry)
        tax = entry['taxonomy']
        if tax:
            taxonomy_map[tax].append(entry)
            parts = tax.split('.')
            if len(parts) >= 1:
                category_map[parts[0]].append(entry)
            if len(parts) >= 2:
                topic_map['.'.join(parts[:2])].append(entry)

    conn.close()
    return entries, taxonomy_map, category_map, topic_map


def parse_wave1_details(log_path):
    """Parse Wave 1 details from the log, including vote distributions,
    injected notes content, and problem text."""

    with open(log_path, 'r') as f:
        lines = f.readlines()

    problems = {}  # pid -> dict of wave1 info
    current_pid = None
    current_problem_text = None
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        # Match problem header
        pid_match = re.search(r'\[(\d+)/\d+\] Problem ([a-f0-9]+) \| Expected: (\d+)', stripped)
        if pid_match:
            current_pid = pid_match.group(2)
            expected = int(pid_match.group(3))
            order = int(pid_match.group(1))
            problems[current_pid] = {
                'order': order,
                'expected': expected,
                'problem_text': '',
                'wave1_votes': {},           # taxonomy -> vote count (non-basic only)
                'wave1_basic_votes': 0,      # basic.basic.basic votes
                'selected_taxonomies': [],
                'db_matches': [],            # (db_id, taxonomy)
                'notes_chars': 0,
                'no_consensus': False,
                'is_basic': False,
                'correct': None,
                'predicted': None,
                'injected_note_text': '',    # actual note text injected
                'all_classification_attempts': [],  # (taxonomy_str, conf, time)
            }
            i += 1
            continue

        # Match problem text
        if stripped.startswith('Problem:') and current_pid:
            problems[current_pid]['problem_text'] = stripped[len('Problem:'):].strip()
            i += 1
            continue

        # Classification attempt details
        ca_match = re.match(r'\s*Attempt \d+:\s*(.+?)\s*\(conf=([\d.]+),\s*turns=\d+,\s*time=([\d.]+)s\)', stripped)
        if ca_match and current_pid and current_pid in problems:
            tax_val = ca_match.group(1).strip()
            conf = float(ca_match.group(2))
            time_s = float(ca_match.group(3))
            problems[current_pid]['all_classification_attempts'].append((tax_val, conf, time_s))
            i += 1
            continue

        # Wave 1 taxonomy votes section
        if stripped == '=== WAVE 1 TAXONOMY VOTES ===' and current_pid:
            j = i + 1
            while j < len(lines):
                vline = lines[j].strip()
                if vline == '=== END VOTES ===':
                    break
                vote_match = re.match(r'\s*(.+?):\s*([\d.]+)\s*votes(.*)', vline)
                if vote_match:
                    tax_name = vote_match.group(1).strip()
                    vote_count = float(vote_match.group(2))
                    rest = vote_match.group(3).strip()

                    if 'basic.basic.basic' in tax_name:
                        problems[current_pid]['wave1_basic_votes'] = vote_count
                    else:
                        problems[current_pid]['wave1_votes'][tax_name] = vote_count

                    if '<-- SELECTED' in rest:
                        if 'basic.basic.basic' in tax_name:
                            problems[current_pid]['is_basic'] = True
                        else:
                            problems[current_pid]['selected_taxonomies'].append(tax_name)
                j += 1
            i = j + 1
            continue

        # No consensus
        if 'No taxonomy exceeded 1/3 threshold' in stripped and current_pid:
            problems[current_pid]['no_consensus'] = True
            i += 1
            continue

        # DB retrieval section
        if '=== WAVE 1 → DB RETRIEVAL' in stripped and current_pid:
            j = i + 1
            while j < len(lines):
                rline = lines[j].strip()
                if rline.startswith('=== END WAVE 1 RETRIEVAL'):
                    break
                # Match DB entry lines: "  - db_id [taxonomy]"
                db_match = re.match(r'\s*-\s*(\S+)\s*\[(.+?)\]', rline)
                if db_match:
                    problems[current_pid]['db_matches'].append(
                        (db_match.group(1), db_match.group(2))
                    )
                # Match notes chars
                notes_match = re.match(r'Notes:\s*(\d+)\s*chars', rline)
                if notes_match:
                    problems[current_pid]['notes_chars'] = int(notes_match.group(1))
                j += 1
            i = j + 1
            continue

        # Injected note text (between "=== USER PROMPT" and "=== END USER PROMPT ===")
        if stripped.startswith('=== USER PROMPT') and current_pid:
            note_lines = []
            in_expert_section = False
            j = i + 1
            while j < len(lines):
                pline = lines[j].rstrip()
                pstripped = pline.strip()
                if pstripped == '=== END USER PROMPT ===':
                    break
                if '[Our IMO expert has given tips' in pstripped:
                    in_expert_section = True
                    j += 1
                    continue
                if '[END EXPERT NOTES]' in pstripped:
                    in_expert_section = False
                    j += 1
                    continue
                if in_expert_section:
                    note_lines.append(pstripped)
                j += 1
            problems[current_pid]['injected_note_text'] = '\n'.join(note_lines).strip()
            i = j + 1
            continue

        # STATUS line
        status_match = re.match(r'\s*STATUS:\s*(CORRECT|WRONG)\s*\|\s*Predicted:\s*(\d+)\s*\|\s*Expected:\s*(\d+)', stripped)
        if status_match and current_pid:
            problems[current_pid]['correct'] = (status_match.group(1) == 'CORRECT')
            problems[current_pid]['predicted'] = int(status_match.group(2))
            i += 1
            continue

        i += 1

    return problems


def find_better_db_matches(problem_text, db_entries, taxonomy_map, category_map, topic_map, selected_taxonomies):
    """Given a problem text and what was selected, find potentially better DB matches."""

    # Strategy: look at all DB entries and find ones whose question text is most similar
    # to our problem text, or whose triggers/technique seem relevant

    candidates = []
    problem_lower = problem_text.lower()

    # Extract keywords from problem text
    keywords = set(re.findall(r'\b[a-z]{4,}\b', problem_lower))

    for entry in db_entries:
        tax = entry['taxonomy'] or ''
        if tax in selected_taxonomies:
            continue  # Already selected

        score = 0
        reasons = []

        # Check triggers overlap
        triggers = (entry.get('triggers') or '').lower()
        trigger_words = set(re.findall(r'\b[a-z]{4,}\b', triggers))
        trigger_overlap = keywords & trigger_words
        if trigger_overlap:
            score += len(trigger_overlap) * 2
            reasons.append(f"trigger overlap: {', '.join(list(trigger_overlap)[:5])}")

        # Check technique overlap
        technique = (entry.get('technique') or '').lower()
        tech_words = set(re.findall(r'\b[a-z]{4,}\b', technique))
        tech_overlap = keywords & tech_words
        if tech_overlap:
            score += len(tech_overlap)
            reasons.append(f"technique overlap: {', '.join(list(tech_overlap)[:5])}")

        # Check question similarity
        question = (entry.get('question') or '').lower()
        q_words = set(re.findall(r'\b[a-z]{4,}\b', question))
        q_overlap = keywords & q_words
        if q_overlap:
            score += len(q_overlap)
            reasons.append(f"question overlap: {', '.join(list(q_overlap)[:5])}")

        # Use sequence matcher for question similarity
        ratio = SequenceMatcher(None, problem_lower[:200], question[:200]).ratio()
        if ratio > 0.3:
            score += int(ratio * 10)
            reasons.append(f"text similarity: {ratio:.2f}")

        if score > 3:
            candidates.append({
                'db_id': entry['id'],
                'taxonomy': tax,
                'score': score,
                'reasons': reasons,
                'triggers': (entry.get('triggers') or '')[:80],
                'technique': (entry.get('technique') or '')[:80],
            })

    candidates.sort(key=lambda x: -x['score'])
    return candidates[:5]


def taxonomy_distance(tax1, tax2):
    """Compute distance between two taxonomies (0=exact, 1=same topic, 2=same category, 3=different)."""
    if tax1 == tax2:
        return 0
    parts1 = tax1.split('.')
    parts2 = tax2.split('.')
    if len(parts1) >= 2 and len(parts2) >= 2 and '.'.join(parts1[:2]) == '.'.join(parts2[:2]):
        return 1  # Same category.topic
    if parts1[0] == parts2[0]:
        return 2  # Same category
    return 3  # Different category


def main():
    parser = argparse.ArgumentParser(description='Wave 1 Notes vs DB deep analysis')
    parser.add_argument('log_file', help='Path to diagnostic.log')
    parser.add_argument('--db', default='data/problem_db/problems.db', help='Path to problems.db')
    parser.add_argument('--wrong-only', action='store_true', help='Only show wrong problems')
    args = parser.parse_args()

    # Load data
    print("Loading problem DB...")
    db_entries, taxonomy_map, category_map, topic_map = load_db(args.db)
    print(f"  DB: {len(db_entries)} entries, {len(taxonomy_map)} unique taxonomies")

    print("Parsing log file...")
    log_problems = parse_wave1_details(args.log_file)
    print(f"  Log: {len(log_problems)} problems")

    # Also parse via standard parser for cross-reference
    parsed = parse_log(args.log_file)
    parsed_map = {p.problem_id: p for p in parsed}

    # ============================================================
    # SECTION 1: Overall Summary
    # ============================================================
    print("\n" + "=" * 80)
    print("  WAVE 1 NOTES vs PROBLEM DB — CROSS-REFERENCE ANALYSIS")
    print("=" * 80)

    correct_count = sum(1 for p in log_problems.values() if p['correct'])
    wrong_count = sum(1 for p in log_problems.values() if p['correct'] is False)

    notes_injected = sum(1 for p in log_problems.values() if p['notes_chars'] > 0)
    no_consensus = sum(1 for p in log_problems.values() if p['no_consensus'])
    basic_only = sum(1 for p in log_problems.values() if p['is_basic'] and not p['selected_taxonomies'])

    print(f"\n  Score: {correct_count}/{correct_count + wrong_count}")
    print(f"  Notes injected: {notes_injected}/{len(log_problems)} problems")
    print(f"  No consensus (no notes): {no_consensus}")
    print(f"  Basic-only (no expert notes): {basic_only}")

    # Correctness by notes status
    with_notes_correct = sum(1 for p in log_problems.values() if p['notes_chars'] > 0 and p['correct'])
    with_notes_wrong = sum(1 for p in log_problems.values() if p['notes_chars'] > 0 and p['correct'] is False)
    without_notes_correct = sum(1 for p in log_problems.values() if p['notes_chars'] == 0 and p['correct'])
    without_notes_wrong = sum(1 for p in log_problems.values() if p['notes_chars'] == 0 and p['correct'] is False)

    print(f"\n  Correctness by notes status:")
    with_total = with_notes_correct + with_notes_wrong
    without_total = without_notes_correct + without_notes_wrong
    print(f"    With notes:    {with_notes_correct}/{with_total} correct ({100*with_notes_correct/max(with_total,1):.1f}%)")
    print(f"    Without notes: {without_notes_correct}/{without_total} correct ({100*without_notes_correct/max(without_total,1):.1f}%)")

    # ============================================================
    # SECTION 2: Taxonomy exists in DB?
    # ============================================================
    print(f"\n{'=' * 80}")
    print("  TAXONOMY SELECTION vs DB COVERAGE")
    print(f"{'=' * 80}")

    all_selected = []
    in_db = 0
    not_in_db = 0
    not_in_db_list = []

    for pid, info in sorted(log_problems.items(), key=lambda x: x[1]['order']):
        for tax in info['selected_taxonomies']:
            all_selected.append(tax)
            if tax in taxonomy_map:
                in_db += 1
            else:
                not_in_db += 1
                not_in_db_list.append((pid, tax, info['correct']))

    print(f"\n  Total taxonomy selections: {len(all_selected)} (across {notes_injected} problems with consensus)")
    print(f"  Found in DB: {in_db} ({100*in_db/max(len(all_selected),1):.1f}%)")
    print(f"  NOT in DB:   {not_in_db} ({100*not_in_db/max(len(all_selected),1):.1f}%)")

    if not_in_db_list:
        print(f"\n  Taxonomies selected but NOT in DB:")
        for pid, tax, correct in not_in_db_list:
            status = "CORRECT" if correct else "WRONG" if correct is False else "???"
            # Find closest DB taxonomy
            best_dist = 999
            closest = "none"
            for db_tax in taxonomy_map.keys():
                d = taxonomy_distance(tax, db_tax)
                if d < best_dist:
                    best_dist = d
                    closest = db_tax
            print(f"    {pid} [{status:>7}] {tax}")
            if best_dist <= 2:
                dist_label = ["exact", "same topic", "same category", "different"][best_dist]
                print(f"      -> closest DB: {closest} ({dist_label})")

    # ============================================================
    # SECTION 3: Per-problem breakdown for ALL problems
    # ============================================================
    print(f"\n{'=' * 80}")
    print("  PER-PROBLEM WAVE 1 ANALYSIS")
    print(f"{'=' * 80}")

    # Sort by order
    sorted_problems = sorted(log_problems.items(), key=lambda x: x[1]['order'])

    for pid, info in sorted_problems:
        if args.wrong_only and info['correct'] is not False:
            continue

        status = "CORRECT" if info['correct'] else "WRONG" if info['correct'] is False else "???"
        marker = " ***" if info['correct'] is False else ""

        print(f"\n{'─' * 70}")
        print(f"  [{info['order']:>2}/50] Problem {pid} | {status} | Expected: {info['expected']} | Predicted: {info.get('predicted', '?')}{marker}")
        print(f"{'─' * 70}")

        # Problem text (truncated)
        ptext = info['problem_text']
        if len(ptext) > 120:
            ptext = ptext[:120] + "..."
        print(f"  Q: {ptext}")

        # Wave 1 result
        if info['is_basic']:
            print(f"  Wave 1: BASIC (no expert notes)")
        elif info['no_consensus']:
            print(f"  Wave 1: NO CONSENSUS (no notes injected)")
            # Show what the top candidates were
            if info['wave1_votes']:
                total_nonbasic = sum(info['wave1_votes'].values())
                threshold = total_nonbasic / 3  # 1/3 threshold (of non-basic votes? or total attempts?)
                print(f"    Top vote candidates (needed >{threshold:.1f} for selection):")
                for tax, votes in sorted(info['wave1_votes'].items(), key=lambda x: -x[1])[:5]:
                    in_db_str = "IN DB" if tax in taxonomy_map else "NOT IN DB"
                    print(f"      {votes:>5.1f} votes: {tax} [{in_db_str}]")
                if info['wave1_basic_votes'] > 0:
                    print(f"      {info['wave1_basic_votes']:>5.1f} votes: basic.basic.basic (ignored, <50%)")
        else:
            print(f"  Wave 1 selected: {', '.join(info['selected_taxonomies'])}")
            for tax in info['selected_taxonomies']:
                if tax in taxonomy_map:
                    entries = taxonomy_map[tax]
                    print(f"    {tax}: {len(entries)} DB match(es)")
                    for e in entries:
                        trig = (e.get('triggers') or '')[:70]
                        print(f"      [{e['id']}] triggers: {trig}")
                else:
                    print(f"    {tax}: NOT IN DB")
                    # Find close matches
                    parts = tax.split('.')
                    if len(parts) >= 2:
                        topic_key = '.'.join(parts[:2])
                        if topic_key in topic_map:
                            close = [e['taxonomy'] for e in topic_map[topic_key]]
                            unique_close = list(set(close))[:5]
                            print(f"      Same topic ({topic_key}): {', '.join(unique_close)}")

            # Show other vote candidates that were NOT selected
            unselected = {t: v for t, v in info['wave1_votes'].items() if t not in info['selected_taxonomies']}
            if unselected:
                print(f"    Other candidates (not selected):")
                for tax, votes in sorted(unselected.items(), key=lambda x: -x[1])[:3]:
                    in_db_str = "IN DB" if tax in taxonomy_map else "NOT IN DB"
                    print(f"      {votes:>5.1f} votes: {tax} [{in_db_str}]")

        # DB matches & notes
        if info['db_matches']:
            print(f"  DB entries used: {len(info['db_matches'])} ({info['notes_chars']} chars)")
            for db_id, tax in info['db_matches']:
                print(f"    - {db_id} [{tax}]")

        # For WRONG problems, do deeper analysis
        if info['correct'] is False:
            print(f"\n  >>> WRONG PROBLEM DEEP ANALYSIS <<<")
            print(f"  Predicted: {info['predicted']} | Expected: {info['expected']}")

            # Check if there's a better DB entry
            if info['problem_text']:
                better = find_better_db_matches(
                    info['problem_text'], db_entries, taxonomy_map,
                    category_map, topic_map, info['selected_taxonomies']
                )
                if better:
                    print(f"  Potentially better DB matches (by text similarity):")
                    for b in better[:3]:
                        print(f"    score={b['score']:>2}: {b['taxonomy']} [{b['db_id']}]")
                        print(f"      reasons: {'; '.join(b['reasons'][:3])}")
                        if b['triggers']:
                            print(f"      triggers: {b['triggers']}")
                else:
                    print(f"  No obviously better DB matches found by text similarity.")

            # Show the note text that was injected
            if info['injected_note_text']:
                note_preview = info['injected_note_text'][:300]
                if len(info['injected_note_text']) > 300:
                    note_preview += "..."
                print(f"  Injected notes preview:")
                for nline in note_preview.split('\n'):
                    print(f"    | {nline}")
            else:
                print(f"  NO NOTES INJECTED")

    # ============================================================
    # SECTION 4: WRONG problems summary
    # ============================================================
    print(f"\n{'=' * 80}")
    print("  WRONG PROBLEMS — NOTES QUALITY SUMMARY")
    print(f"{'=' * 80}")

    wrong_problems = [(pid, info) for pid, info in sorted_problems if info['correct'] is False]

    print(f"\n  {'#':>2}  {'PID':<8} {'Pred':>6} {'Exp':>6} {'Notes?':<10} {'Selected Taxonomy':<50} {'In DB?'}")
    print(f"  {'─'*2}  {'─'*8} {'─'*6} {'─'*6} {'─'*10} {'─'*50} {'─'*6}")

    for pid, info in wrong_problems:
        notes_status = f"{info['notes_chars']} ch" if info['notes_chars'] > 0 else "NONE"
        if info['no_consensus']:
            notes_status = "no cons."
        elif info['is_basic']:
            notes_status = "basic"

        tax_str = ', '.join(info['selected_taxonomies'])[:50] if info['selected_taxonomies'] else '(none)'

        in_db = 'YES' if all(t in taxonomy_map for t in info['selected_taxonomies']) else 'NO' if info['selected_taxonomies'] else '-'

        print(f"  {info['order']:>2}  {pid:<8} {info.get('predicted', '?'):>6} {info['expected']:>6} {notes_status:<10} {tax_str:<50} {in_db}")

    # ============================================================
    # SECTION 5: Classification for NO CONSENSUS problems
    # ============================================================
    print(f"\n{'=' * 80}")
    print("  NO CONSENSUS PROBLEMS — VOTE DISTRIBUTION ANALYSIS")
    print(f"{'=' * 80}")

    no_consensus_problems = [(pid, info) for pid, info in sorted_problems if info['no_consensus']]

    for pid, info in no_consensus_problems:
        status = "CORRECT" if info['correct'] else "WRONG" if info['correct'] is False else "???"
        marker = " ***" if info['correct'] is False else ""

        print(f"\n  [{info['order']:>2}] {pid} [{status}]{marker}")
        ptext = info['problem_text']
        if len(ptext) > 100:
            ptext = ptext[:100] + "..."
        print(f"  Q: {ptext}")

        # Count total valid (non-None) classification attempts
        valid_attempts = [(t, c, tm) for t, c, tm in info['all_classification_attempts']
                         if t != 'None' and t != 'taxonomy' and 'basic' not in t.lower()]
        total_valid = len(valid_attempts)

        # Compute what the 1/3 threshold would be
        # The threshold is 1/3 of total (non-basic) valid votes
        all_nonbasic_votes = sum(info['wave1_votes'].values())
        threshold = all_nonbasic_votes / 3 if all_nonbasic_votes > 0 else 0

        print(f"  Total non-basic votes: {all_nonbasic_votes:.0f} | 1/3 threshold: {threshold:.1f}")
        if info['wave1_basic_votes']:
            print(f"  basic.basic.basic: {info['wave1_basic_votes']:.0f} votes (ignored)")

        if info['wave1_votes']:
            print(f"  Vote distribution:")
            for tax, votes in sorted(info['wave1_votes'].items(), key=lambda x: -x[1]):
                in_db_str = "IN DB" if tax in taxonomy_map else "NOT IN DB"
                gap = votes - threshold
                gap_str = f"(need {-gap:.1f} more)" if gap < 0 else f"(above by {gap:.1f})"
                print(f"    {votes:>5.1f}: {tax:<55} [{in_db_str}] {gap_str}")

            # Would any of the top candidates have helped?
            top_tax = max(info['wave1_votes'], key=info['wave1_votes'].get)
            if top_tax in taxonomy_map:
                entries = taxonomy_map[top_tax]
                for e in entries:
                    tech = (e.get('technique') or '')[:100]
                    print(f"  If we had used top candidate '{top_tax}':")
                    print(f"    technique: {tech}")
        else:
            print(f"  No non-basic taxonomy votes at all!")

    # ============================================================
    # SECTION 6: Reuse analysis — same DB entry for multiple problems
    # ============================================================
    print(f"\n{'=' * 80}")
    print("  DB ENTRY REUSE — SAME ENTRY INJECTED FOR MULTIPLE PROBLEMS")
    print(f"{'=' * 80}")

    db_entry_usage = defaultdict(list)  # (db_id, taxonomy) -> list of (pid, correct)
    for pid, info in sorted_problems:
        for db_id, tax in info['db_matches']:
            db_entry_usage[(db_id, tax)].append((pid, info['correct']))

    reused = {k: v for k, v in db_entry_usage.items() if len(v) > 1}
    if reused:
        for (db_id, tax), usages in sorted(reused.items(), key=lambda x: -len(x[1])):
            correct_of_reused = sum(1 for _, c in usages if c)
            print(f"\n  {db_id} [{tax}] — used {len(usages)} times ({correct_of_reused} correct)")
            for pid, correct in usages:
                status = "CORRECT" if correct else "WRONG" if correct is False else "???"
                print(f"    {pid} [{status}]")
    else:
        print("\n  No DB entries were reused for multiple problems.")

    # ============================================================
    # SECTION 7: Taxonomy accuracy
    # ============================================================
    print(f"\n{'=' * 80}")
    print("  TAXONOMY ACCURACY — CORRECTNESS RATE BY SELECTED TAXONOMY")
    print(f"{'=' * 80}")

    tax_stats = defaultdict(lambda: {'correct': 0, 'wrong': 0, 'problems': []})
    for pid, info in sorted_problems:
        for tax in info['selected_taxonomies']:
            tax_root = '.'.join(tax.split('.')[:2])
            if info['correct']:
                tax_stats[tax_root]['correct'] += 1
            elif info['correct'] is False:
                tax_stats[tax_root]['wrong'] += 1
            tax_stats[tax_root]['problems'].append((pid, info['correct']))

    print(f"\n  {'Category.Topic':<50} {'Correct':>7} {'Wrong':>5} {'Rate':>6}")
    print(f"  {'─'*50} {'─'*7} {'─'*5} {'─'*6}")
    for tax_root, stats in sorted(tax_stats.items(), key=lambda x: -(x[1]['correct'] + x[1]['wrong'])):
        total = stats['correct'] + stats['wrong']
        rate = 100 * stats['correct'] / total if total > 0 else 0
        marker = " <<<" if stats['wrong'] > 0 and rate < 50 else ""
        print(f"  {tax_root:<50} {stats['correct']:>7} {stats['wrong']:>5} {rate:>5.0f}%{marker}")

    # ============================================================
    # SECTION 8: Missed opportunities — DB entries that COULD match wrong problems
    # ============================================================
    print(f"\n{'=' * 80}")
    print("  MISSED OPPORTUNITIES — WRONG PROBLEMS vs ENTIRE DB")
    print(f"{'=' * 80}")

    for pid, info in wrong_problems:
        print(f"\n  [{info['order']:>2}] {pid} | Predicted: {info['predicted']} | Expected: {info['expected']}")
        ptext = info['problem_text']
        if len(ptext) > 120:
            ptext = ptext[:120] + "..."
        print(f"  Q: {ptext}")

        # What was selected
        if info['selected_taxonomies']:
            print(f"  Selected: {', '.join(info['selected_taxonomies'])}")
        elif info['no_consensus']:
            print(f"  Selected: NONE (no consensus)")
            if info['wave1_votes']:
                top3 = sorted(info['wave1_votes'].items(), key=lambda x: -x[1])[:3]
                print(f"  Top candidates: {', '.join(f'{t} ({v:.0f}v)' for t, v in top3)}")
        elif info['is_basic']:
            print(f"  Selected: basic.basic.basic")

        # Search for ALL DB entries where the technique or question might be relevant
        print(f"  Best DB matches by keyword overlap:")
        candidates = find_better_db_matches(
            info['problem_text'], db_entries, taxonomy_map,
            category_map, topic_map, []  # Don't exclude anything
        )

        for c in candidates[:5]:
            was_selected = c['taxonomy'] in info['selected_taxonomies']
            sel_marker = " [WAS SELECTED]" if was_selected else ""
            was_db_match = any(c['db_id'] == m[0] for m in info['db_matches'])
            match_marker = " [WAS INJECTED]" if was_db_match else ""
            print(f"    score={c['score']:>2}: {c['taxonomy']} [{c['db_id']}]{sel_marker}{match_marker}")
            print(f"      reasons: {'; '.join(c['reasons'][:3])}")

    # ============================================================
    # SECTION 9: Stats summary
    # ============================================================
    print(f"\n{'=' * 80}")
    print("  FINAL SUMMARY")
    print(f"{'=' * 80}")

    wrong_with_notes = sum(1 for _, info in wrong_problems if info['notes_chars'] > 0)
    wrong_no_consensus = sum(1 for _, info in wrong_problems if info['no_consensus'])
    wrong_basic = sum(1 for _, info in wrong_problems if info['is_basic'])
    wrong_notes_but_bad = sum(1 for _, info in wrong_problems
                              if info['notes_chars'] > 0 and
                              any(t not in taxonomy_map for t in info['selected_taxonomies']))

    print(f"\n  Wrong problems breakdown:")
    print(f"    Total wrong: {len(wrong_problems)}")
    print(f"    With notes injected: {wrong_with_notes}")
    print(f"    No consensus (no notes): {wrong_no_consensus}")
    print(f"    Basic only (no notes): {wrong_basic}")
    print(f"    Notes injected but taxonomy NOT in DB: {wrong_notes_but_bad}")

    # Per wrong problem: diagnosis
    print(f"\n  Per-problem diagnosis:")
    for pid, info in wrong_problems:
        if info['no_consensus']:
            diagnosis = "NO CONSENSUS — model couldn't agree on classification"
        elif info['is_basic']:
            diagnosis = "BASIC — classified as too easy, no expert notes"
        elif not info['selected_taxonomies']:
            diagnosis = "NO TAXONOMY SELECTED (unknown reason)"
        elif all(t in taxonomy_map for t in info['selected_taxonomies']):
            diagnosis = "TAXONOMY IN DB — notes injected but problem still wrong (notes may be wrong-topic or insufficient)"
        else:
            missing = [t for t in info['selected_taxonomies'] if t not in taxonomy_map]
            diagnosis = f"TAXONOMY NOT IN DB: {', '.join(missing)}"

        print(f"    {pid} [{info['order']:>2}]: {diagnosis}")


if __name__ == '__main__':
    main()
