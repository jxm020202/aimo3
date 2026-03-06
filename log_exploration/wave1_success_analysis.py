#!/usr/bin/env python3
"""
Wave 1 Success Analysis: Did classification + DB notes injection help?

Analyzes:
1. How many problems got Wave 1 notes vs no consensus
2. Correctness rate: notes vs no notes
3. Deep dive on wrong problems and close calls
4. Taxonomy patterns and DB coverage

Usage:
    python3 log_exploration/wave1_success_analysis.py output/shiv-latest/diagnostic.log
"""

import sys
import re
import os
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def parse_wave1_sections(logfile):
    """Parse all Wave 1 classification sections from diagnostic log."""
    sections = {}
    current_problem = None
    current_expected = None
    current_section = None

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
                'taxonomies': [],
                'budget': '',
                'no_consensus': False,
                'notes_injected': False,
                'study_notes_chars': 0,
            }

        if current_section:
            if 'Budget:' in line and 'Attempts:' in line:
                current_section['budget'] = line.strip()

            # Attempt line
            m = re.search(r'Attempt \d+: (.+?) \(conf=([\d.]+), turns=(\d+), time=([\d.]+)s\)', line)
            if m:
                current_section['attempts'].append({
                    'taxonomy': m.group(1) if m.group(1) != 'None' else None,
                    'conf': float(m.group(2)),
                    'turns': int(m.group(3)),
                    'time': float(m.group(4)),
                })

            # Selected taxonomies
            if 'Taxonomies:' in line:
                m2 = re.search(r"Taxonomies: \[(.+?)\]", line)
                if m2:
                    current_section['taxonomies'] = [t.strip().strip("'\"") for t in m2.group(1).split(',')]
                    current_section['notes_injected'] = True

            if 'NO CONSENSUS' in line:
                current_section['no_consensus'] = True

            # Check for study notes size
            m3 = re.search(r'STUDY_NOTES.*?(\d+)\s*chars', line)
            if m3:
                current_section['study_notes_chars'] = int(m3.group(1))

            if 'END WAVE 1 RETRIEVAL' in line or 'END WAVE 1' in line:
                if current_section['problem']:
                    sections[current_section['problem']] = current_section
                current_section = None

    # Capture last section
    if current_section and current_section.get('problem') and current_section['attempts']:
        sections[current_section['problem']] = current_section

    return sections


def parse_study_notes_from_prompts(logfile):
    """Look for [STUDY NOTES] or expert notes in the actual prompt/reasoning text."""
    notes_by_problem = {}
    current_problem = None

    for line in open(logfile, errors='replace'):
        m = re.search(r'Problem (\w+) \| Expected: (\d+)', line)
        if m:
            current_problem = m.group(1)

        if current_problem:
            if 'IMO expert' in line or 'STUDY_NOTES' in line or 'EXPERT NOTES' in line or 'Our IMO expert' in line:
                if current_problem not in notes_by_problem:
                    notes_by_problem[current_problem] = []
                notes_by_problem[current_problem].append(line.strip()[:200])

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
                if t:
                    votes[t] += conf
    total = len(attempts)
    threshold = total * 0.5
    sorted_votes = sorted(votes.items(), key=lambda x: x[1], reverse=True)
    selected = [tax for tax, v in sorted_votes if v > threshold]
    return selected, sorted_votes, threshold


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 wave1_success_analysis.py <logfile>")
        sys.exit(1)

    logfile = sys.argv[1]

    print(f"Parsing {logfile}...")
    problems = parse_log(logfile)
    print(f"Parsed {len(problems)} problems\n")

    # Build lookup
    prob_lookup = {p.problem_id: p for p in problems}

    # Parse Wave 1 sections
    wave1 = parse_wave1_sections(logfile)
    print(f"Found {len(wave1)} Wave 1 sections\n")

    # Parse study notes evidence
    notes_evidence = parse_study_notes_from_prompts(logfile)

    # ── 1. OVERALL WAVE 1 COVERAGE ──
    print("=" * 80)
    print("  1. WAVE 1 COVERAGE: Notes Injected vs No Consensus")
    print("=" * 80)

    got_notes = []
    no_notes = []
    basic_classified = []  # basic.basic.basic = effectively no useful notes

    for pid, w in wave1.items():
        selected, _, _ = compute_taxonomy_votes(w['attempts'])
        if selected and not all(t == 'basic.basic.basic' for t in selected):
            got_notes.append(pid)
        elif selected and all(t == 'basic.basic.basic' for t in selected):
            basic_classified.append(pid)
        else:
            no_notes.append(pid)

    # Problems not in wave1 at all
    no_wave1 = [p.problem_id for p in problems if p.problem_id not in wave1]

    print(f"\n  Got meaningful taxonomy + notes:  {len(got_notes)}/50")
    print(f"  Classified as basic.basic.basic:  {len(basic_classified)}/50 (no DB entry)")
    print(f"  No consensus (fallback warning):  {len(no_notes)}/50")
    print(f"  No Wave 1 at all:                 {len(no_wave1)}/50")

    # ── 2. CORRECTNESS: NOTES vs NO NOTES ──
    print(f"\n{'=' * 80}")
    print("  2. CORRECTNESS RATE: Notes vs No Notes")
    print("=" * 80)

    def score_group(pids, label):
        correct = sum(1 for pid in pids if pid in prob_lookup and prob_lookup[pid].correct)
        total = len(pids)
        pct = (correct / total * 100) if total else 0
        wrong_pids = [pid[:6] for pid in pids if pid in prob_lookup and not prob_lookup[pid].correct]
        print(f"\n  {label}: {correct}/{total} ({pct:.1f}%)")
        if wrong_pids:
            print(f"    Wrong: {', '.join(wrong_pids)}")
        return correct, total

    c1, t1 = score_group(got_notes, "Got meaningful notes")
    c2, t2 = score_group(basic_classified, "Classified basic (no DB notes)")
    c3, t3 = score_group(no_notes, "No consensus (fallback warning)")

    # ── 3. DETAILED TABLE ──
    print(f"\n{'=' * 80}")
    print("  3. PER-PROBLEM WAVE 1 DETAIL")
    print("=" * 80)
    print(f"\n  {'PID':8s} {'Correct':8s} {'Notes?':22s} {'Top Taxonomy':45s} {'Conf%':6s} {'W1 Time':8s}")
    print(f"  {'-'*8} {'-'*8} {'-'*22} {'-'*45} {'-'*6} {'-'*8}")

    for p in problems:
        pid = p.problem_id
        correct_str = "YES" if p.correct else "WRONG"
        w = wave1.get(pid)
        if not w:
            print(f"  {pid[:8]:8s} {correct_str:8s} {'(no wave1)':22s}")
            continue

        selected, sorted_votes, _ = compute_taxonomy_votes(w['attempts'])
        top_tax = sorted_votes[0][0] if sorted_votes else '(none)'
        top_pct = (sorted_votes[0][1] / len(w['attempts']) * 100) if sorted_votes else 0
        avg_time = sum(a['time'] for a in w['attempts']) / max(len(w['attempts']), 1)

        if selected and not all(t == 'basic.basic.basic' for t in selected):
            notes_str = f"NOTES ({', '.join(s[:15] for s in selected[:2])})"
        elif selected and all(t == 'basic.basic.basic' for t in selected):
            notes_str = "basic (no DB)"
        else:
            notes_str = "NO CONSENSUS"

        marker = " <--" if not p.correct else ""
        print(f"  {pid[:8]:8s} {correct_str:8s} {notes_str:22s} {top_tax[:45]:45s} {top_pct:5.0f}% {avg_time:6.1f}s{marker}")

    # ── 4. WRONG PROBLEMS DEEP DIVE ──
    wrong_pids = ['25e584', 'eee8f4', '3f0a92', '3980cd', '1ec970', '7c78ab', 'a9dbc8', '414a5b']
    print(f"\n{'=' * 80}")
    print("  4. WRONG PROBLEMS: Wave 1 Deep Dive")
    print("=" * 80)

    for wpid in wrong_pids:
        # Find full pid
        full_pid = None
        for p in problems:
            if p.problem_id.startswith(wpid):
                full_pid = p.problem_id
                break
        if not full_pid:
            print(f"\n  {wpid}: NOT FOUND in log")
            continue

        p = prob_lookup[full_pid]
        w = wave1.get(full_pid)

        print(f"\n  {'─' * 76}")
        print(f"  {wpid} | Expected: {p.expected} | Predicted: {p.predicted} | Votes: {p.votes}")

        if not w:
            print(f"  Wave 1: NO DATA")
            continue

        selected, sorted_votes, threshold = compute_taxonomy_votes(w['attempts'])

        if selected and not all(t == 'basic.basic.basic' for t in selected):
            print(f"  Wave 1: GOT NOTES | Taxonomies: {selected}")
        elif selected and all(t == 'basic.basic.basic' for t in selected):
            print(f"  Wave 1: Classified as BASIC (no useful DB notes)")
        else:
            print(f"  Wave 1: NO CONSENSUS (fallback warning injected)")

        # Show top votes
        print(f"  Top taxonomy votes (threshold: >{threshold:.1f}):")
        for tax, v in sorted_votes[:5]:
            pct = v / len(w['attempts']) * 100
            marker = " <-- SELECTED" if tax in selected else ""
            print(f"    {tax}: {v:.1f} ({pct:.0f}%){marker}")

        # Show note evidence from prompts
        if full_pid in notes_evidence:
            print(f"  Evidence of notes in prompts: {len(notes_evidence[full_pid])} mentions")
            for ev in notes_evidence[full_pid][:3]:
                print(f"    {ev[:120]}")

        # Analysis
        # Check if correct answer appeared in attempts
        correct_attempts = [a for a in p.attempts if a.answer == p.expected]
        wrong_majority = [a for a in p.attempts if a.answer == p.predicted]
        none_attempts = [a for a in p.attempts if a.answer is None]

        print(f"  Attempt breakdown: {len(correct_attempts)} correct, {len(wrong_majority)} majority-wrong, {len(none_attempts)} None")
        if correct_attempts:
            print(f"  ** Correct answer WAS found ({len(correct_attempts)} attempts) but outvoted **")

    # ── 5. CLOSE CALLS ──
    close_pids = ['d4b03c', '4e5a01']
    print(f"\n{'=' * 80}")
    print("  5. CLOSE CALLS: Wave 1 Impact")
    print("=" * 80)

    for cpid in close_pids:
        full_pid = None
        for p in problems:
            if p.problem_id.startswith(cpid):
                full_pid = p.problem_id
                break
        if not full_pid:
            print(f"\n  {cpid}: NOT FOUND")
            continue

        p = prob_lookup[full_pid]
        w = wave1.get(full_pid)

        print(f"\n  {'─' * 76}")
        print(f"  {cpid} | Expected: {p.expected} | Predicted: {p.predicted} | Correct: {p.correct} | Votes: {p.votes}")

        if not w:
            print(f"  Wave 1: NO DATA")
            continue

        selected, sorted_votes, threshold = compute_taxonomy_votes(w['attempts'])
        if selected and not all(t == 'basic.basic.basic' for t in selected):
            print(f"  Wave 1: GOT NOTES | Taxonomies: {selected}")
        else:
            print(f"  Wave 1: NO CONSENSUS")

        print(f"  Top taxonomy votes:")
        for tax, v in sorted_votes[:4]:
            pct = v / len(w['attempts']) * 100
            print(f"    {tax}: {v:.1f} ({pct:.0f}%)")

        # Vote margin analysis
        correct_count = sum(1 for a in p.attempts if a.answer == p.expected)
        pred_count = sum(1 for a in p.attempts if a.answer == p.predicted)
        none_count = sum(1 for a in p.attempts if a.answer is None)
        print(f"  Vote margin: {correct_count} correct vs {pred_count} predicted | {none_count} None")

    # ── 6. TAXONOMY PATTERN SUMMARY ──
    print(f"\n{'=' * 80}")
    print("  6. TAXONOMY PATTERN SUMMARY")
    print("=" * 80)

    # Count categories
    category_counts = defaultdict(lambda: {'total': 0, 'correct': 0, 'has_notes': 0})
    for pid, w in wave1.items():
        selected, sorted_votes, _ = compute_taxonomy_votes(w['attempts'])
        top_cat = sorted_votes[0][0].split('.')[0] if sorted_votes else 'unknown'
        p = prob_lookup.get(pid)
        if not p:
            continue
        category_counts[top_cat]['total'] += 1
        if p.correct:
            category_counts[top_cat]['correct'] += 1
        if selected and not all(t == 'basic.basic.basic' for t in selected):
            category_counts[top_cat]['has_notes'] += 1

    print(f"\n  {'Category':30s} {'Total':6s} {'Correct':8s} {'Rate':6s} {'Got Notes':10s}")
    print(f"  {'-'*30} {'-'*6} {'-'*8} {'-'*6} {'-'*10}")
    for cat in sorted(category_counts.keys()):
        c = category_counts[cat]
        rate = (c['correct'] / c['total'] * 100) if c['total'] else 0
        print(f"  {cat:30s} {c['total']:6d} {c['correct']:8d} {rate:5.0f}% {c['has_notes']:10d}")

    # ── 7. WAVE 1 TIME COST ──
    print(f"\n{'=' * 80}")
    print("  7. WAVE 1 TIME COST")
    print("=" * 80)

    total_w1_time = 0
    w1_times = []
    for pid, w in wave1.items():
        max_time = max((a['time'] for a in w['attempts']), default=0)
        avg_time = sum(a['time'] for a in w['attempts']) / max(len(w['attempts']), 1)
        total_w1_time += max_time  # parallel, so max matters
        w1_times.append((pid[:6], max_time, avg_time, len(w['attempts'])))

    w1_times.sort(key=lambda x: x[1], reverse=True)
    print(f"\n  Total Wave 1 wall time (sum of max per problem): {total_w1_time:.0f}s ({total_w1_time/60:.1f} min)")
    print(f"  Average Wave 1 max time per problem: {total_w1_time/len(wave1):.1f}s")
    print(f"\n  Slowest Wave 1 classifications:")
    for pid, mx, avg, n in w1_times[:10]:
        print(f"    {pid}: max={mx:.1f}s, avg={avg:.1f}s, attempts={n}")

    # ── 8. CONSENSUS QUALITY SUMMARY ──
    print(f"\n{'=' * 80}")
    print("  8. SUMMARY")
    print("=" * 80)

    notes_correct = sum(1 for pid in got_notes if pid in prob_lookup and prob_lookup[pid].correct)
    notes_total = len(got_notes)
    no_notes_correct = sum(1 for pid in (no_notes + basic_classified) if pid in prob_lookup and prob_lookup[pid].correct)
    no_notes_total = len(no_notes) + len(basic_classified)

    print(f"""
  Problems with meaningful taxonomy notes:  {notes_total} ({notes_correct}/{notes_total} correct = {notes_correct/notes_total*100:.0f}%)
  Problems without notes (no consensus/basic): {no_notes_total} ({no_notes_correct}/{no_notes_total} correct = {no_notes_correct/no_notes_total*100:.0f}%)

  Wave 1 consensus rate: {notes_total}/50 = {notes_total/50*100:.0f}%

  Key findings:
  - Notes injection does NOT clearly correlate with higher accuracy
  - No consensus problems: the classifier simply doesn't converge when
    the problem doesn't map cleanly to a DB taxonomy
  - Many "no consensus" problems are genuinely harder (T2/novel)
  - Wave 1 time cost: {total_w1_time/60:.1f} minutes across all 50 problems
  """)

    # ── WRONG PROBLEMS: Notes vs No Notes breakdown ──
    wrong_with_notes = [pid[:6] for pid in got_notes if pid in prob_lookup and not prob_lookup[pid].correct]
    wrong_no_notes = [pid[:6] for pid in (no_notes + basic_classified) if pid in prob_lookup and not prob_lookup[pid].correct]
    print(f"  Wrong problems WITH notes:    {wrong_with_notes}")
    print(f"  Wrong problems WITHOUT notes: {wrong_no_notes}")


if __name__ == '__main__':
    main()
