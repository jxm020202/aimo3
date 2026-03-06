#!/usr/bin/env python3
"""Analyze Wave 1 classification and notes injection for all problems.

Shows taxonomy consensus, notes injected, and highlights failures where
notes were missing or classification was wrong.

Usage:
    python3 log_exploration/wave1_analysis.py <diagnostic.log>
    python3 log_exploration/wave1_analysis.py <diagnostic.log> --wrong-only
    python3 log_exploration/wave1_analysis.py <diagnostic.log> --problem <pid>
    python3 log_exploration/wave1_analysis.py <diagnostic.log> --threshold-sim 0.35
"""

import sys, re, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log_exploration.log_query import parse_log


def parse_wave1_blocks(logfile):
    """Parse Wave 1 classification blocks from raw log."""
    results = {}
    current_pid = None
    current_problem_text = None

    with open(logfile) as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i]

        # Match problem header
        m = re.match(r'\s*\[\d+/\d+\]\s+Problem\s+(\w+)\s+\|\s+Expected:\s+(\d+)', line)
        if m:
            current_pid = m.group(1)
            expected = int(m.group(2))
            # Read problem text (next non-blank line after separator)
            j = i + 1
            while j < len(lines) and lines[j].strip() in ('', '─' * 70, '─' * 66):
                j += 1
            prob_lines = []
            while j < len(lines) and 'WAVE 1: CLASSIFICATION' not in lines[j]:
                prob_lines.append(lines[j].rstrip())
                j += 1
            current_problem_text = '\n'.join(prob_lines).strip()
            # Get problem text (first 150 chars)
            prob_preview = re.sub(r'\s+', ' ', current_problem_text)[:150]

            results[current_pid] = {
                'expected': expected,
                'problem_preview': prob_preview,
                'taxonomy_votes': {},
                'selected': None,
                'notes_injected': False,
                'notes_chars': 0,
                'db_matches': 0,
                'db_entries': [],
                'no_consensus': False,
                'classification_attempts': [],
            }
            i = j
            continue

        # Match classification attempt
        if current_pid and re.match(r'\s+Attempt\s+\d+:', line):
            m2 = re.match(r'\s+Attempt\s+(\d+):\s+(.+?)\s+\(conf=([\d.]+)', line)
            if m2:
                att_num = int(m2.group(1))
                tax = m2.group(2).strip()
                conf = float(m2.group(3))
                results[current_pid]['classification_attempts'].append({
                    'attempt': att_num, 'taxonomy': tax, 'confidence': conf
                })

        # Match taxonomy votes
        if current_pid and '=== WAVE 1 TAXONOMY VOTES ===' in line:
            j = i + 1
            while j < len(lines) and '=== END VOTES ===' not in lines[j]:
                vm = re.match(r'\s+(.+?):\s+([\d.]+)\s+votes(?:\s+<--\s+SELECTED)?', lines[j])
                if vm:
                    tax_name = vm.group(1).strip()
                    votes = float(vm.group(2))
                    selected = '<-- SELECTED' in lines[j]
                    results[current_pid]['taxonomy_votes'][tax_name] = votes
                    if selected:
                        results[current_pid]['selected'] = tax_name
                j += 1

        # Match no consensus
        if current_pid and 'NO CONSENSUS' in line:
            results[current_pid]['no_consensus'] = True

        # Match DB retrieval
        if current_pid and 'WAVE 1 → DB RETRIEVAL' in line:
            j = i + 1
            while j < len(lines) and '=== END WAVE 1 RETRIEVAL ===' not in lines[j]:
                tm = re.match(r'Total matches:\s+(\d+)', lines[j])
                if tm:
                    results[current_pid]['db_matches'] = int(tm.group(1))
                nm = re.match(r'Notes:\s+(\d+)\s+chars', lines[j])
                if nm:
                    results[current_pid]['notes_chars'] = int(nm.group(1))
                    results[current_pid]['notes_injected'] = True
                em = re.match(r'\s+-\s+(\S+)\s+\[(.+?)\]', lines[j])
                if em:
                    results[current_pid]['db_entries'].append({
                        'id': em.group(1), 'taxonomy': em.group(2)
                    })
                j += 1

        i += 1

    return results


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    logfile = sys.argv[1]
    wrong_only = '--wrong-only' in sys.argv
    specific_pid = None
    if '--problem' in sys.argv:
        specific_pid = sys.argv[sys.argv.index('--problem') + 1]

    # Parse structured data for correctness info
    problems = parse_log(logfile)
    correct_map = {p.problem_id: p.correct for p in problems}
    predicted_map = {p.problem_id: p.predicted for p in problems}
    votes_map = {p.problem_id: p.votes for p in problems}

    # Parse Wave 1 blocks
    wave1 = parse_wave1_blocks(logfile)

    if specific_pid:
        if specific_pid in wave1:
            w = wave1[specific_pid]
            print(f"\n  Problem {specific_pid} | Expected: {w['expected']}")
            print(f"  Predicted: {predicted_map.get(specific_pid, '?')} | Correct: {correct_map.get(specific_pid, '?')}")
            print(f"  Problem: {w['problem_preview']}")
            print()
            print(f"  Classification attempts: {len(w['classification_attempts'])}")
            for a in w['classification_attempts']:
                print(f"    Att {a['attempt']:2d}: {a['taxonomy']} (conf={a['confidence']})")
            print()
            print(f"  Taxonomy votes:")
            total_votes = sum(w['taxonomy_votes'].values())
            for tax, v in sorted(w['taxonomy_votes'].items(), key=lambda x: -x[1]):
                pct = v / total_votes * 100 if total_votes else 0
                sel = " <-- SELECTED" if tax == w['selected'] else ""
                print(f"    {tax:<50} {v:5.1f} ({pct:4.1f}%){sel}")
            print()
            if w['notes_injected']:
                print(f"  Notes: YES ({w['notes_chars']} chars, {w['db_matches']} DB matches)")
                for e in w['db_entries']:
                    print(f"    - {e['id']} [{e['taxonomy']}]")
            elif w['no_consensus']:
                print(f"  Notes: NO (no consensus)")
            else:
                print(f"  Notes: NO")
            print()
        else:
            print(f"Problem {specific_pid} not found in Wave 1 data")
        return

    # Summary
    total = len(wave1)
    got_notes = sum(1 for w in wave1.values() if w['notes_injected'])
    no_consensus = sum(1 for w in wave1.values() if w['no_consensus'])

    print(f"\n  Wave 1 Classification Summary")
    print(f"  {'='*60}")
    print(f"  Total problems:     {total}")
    print(f"  Notes injected:     {got_notes} ({got_notes/total*100:.0f}%)")
    print(f"  No consensus:       {no_consensus} ({no_consensus/total*100:.0f}%)")
    print()

    # Junk vote analysis
    junk_patterns = ['basic.basic.basic', 'taxonomy', 'a.b.c', 'x.y.z']
    junk_count = 0
    for w in wave1.values():
        for tax in w['taxonomy_votes']:
            if any(p in tax for p in junk_patterns):
                junk_count += 1
                break
    print(f"  Problems with junk votes: {junk_count}")

    # Near-miss threshold analysis
    print(f"\n  Consensus Threshold Analysis (what if we lowered it?)")
    print(f"  {'─'*60}")
    for threshold in [0.50, 0.45, 0.40, 0.35, 0.30]:
        would_get_notes = 0
        for w in wave1.values():
            total_votes = sum(w['taxonomy_votes'].values())
            if total_votes == 0:
                continue
            top_tax = max(w['taxonomy_votes'].items(), key=lambda x: x[1])
            top_pct = top_tax[1] / total_votes
            if top_pct >= threshold and top_tax[0] not in ('taxonomy', 'basic.basic.basic', 'a.b.c', 'x.y.z'):
                would_get_notes += 1
        print(f"    Threshold {threshold:.0%}: {would_get_notes}/{total} problems get notes")

    # Wrong problems detail
    wrong_pids = [pid for pid, correct in correct_map.items() if not correct]
    if wrong_only:
        pids_to_show = wrong_pids
    else:
        pids_to_show = sorted(wave1.keys(), key=lambda p: (correct_map.get(p, True), p))

    if wrong_only or not specific_pid:
        print(f"\n  {'WRONG' if wrong_only else 'ALL'} Problems — Wave 1 Detail")
        print(f"  {'─'*90}")
        header = f"  {'PID':<8} {'Correct':>7} {'Pred':>10} {'Exp':>10} {'Top Taxonomy':<40} {'%':>5} {'Notes':>5}"
        print(header)
        print(f"  {'─'*90}")

        for pid in pids_to_show:
            if pid not in wave1:
                continue
            w = wave1[pid]
            is_correct = correct_map.get(pid, '?')
            pred = predicted_map.get(pid, '?')

            total_votes = sum(w['taxonomy_votes'].values())
            if total_votes > 0:
                top_tax, top_v = max(w['taxonomy_votes'].items(), key=lambda x: x[1])
                top_pct = top_v / total_votes * 100
            else:
                top_tax, top_pct = 'N/A', 0

            notes = 'YES' if w['notes_injected'] else 'NO'

            if wrong_only or not is_correct:
                print(f"  {pid:<8} {'OK' if is_correct else 'FAIL':>7} {str(pred):>10} {w['expected']:>10} {top_tax:<40} {top_pct:4.0f}% {notes:>5}")

        # Wrong-specific insights
        if wrong_only:
            print(f"\n  Failure Classification:")
            print(f"  {'─'*60}")
            no_notes_wrong = [pid for pid in wrong_pids if pid in wave1 and not wave1[pid]['notes_injected']]
            has_notes_wrong = [pid for pid in wrong_pids if pid in wave1 and wave1[pid]['notes_injected']]
            print(f"    Wrong + NO notes:  {len(no_notes_wrong)} — {', '.join(no_notes_wrong)}")
            print(f"    Wrong + HAS notes: {len(has_notes_wrong)} — {', '.join(has_notes_wrong)}")

            # Near-miss analysis for wrong problems
            print(f"\n  Near-Miss Wrong Problems (top taxonomy close to 50%):")
            for pid in wrong_pids:
                if pid not in wave1:
                    continue
                w = wave1[pid]
                total_votes = sum(w['taxonomy_votes'].values())
                if total_votes == 0:
                    continue
                top_tax, top_v = max(w['taxonomy_votes'].items(), key=lambda x: x[1])
                top_pct = top_v / total_votes * 100
                if 30 <= top_pct < 50 and top_tax not in ('taxonomy', 'basic.basic.basic'):
                    print(f"    {pid}: {top_tax} at {top_pct:.1f}% ({top_v:.0f}/{total_votes:.0f} votes)")

    print()


if __name__ == '__main__':
    main()
