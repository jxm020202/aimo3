#!/usr/bin/env python3
"""Analyze Wave 1 classification quality by temperature.

Parses Wave 1 classification blocks from the raw diagnostic log (NOT the
log_query parser, which only handles Wave 2) and breaks down taxonomy
agreement, None/timeout rates, and error patterns by temperature bucket.

Auto-detects the Wave 1 temp schedule from the notebook or accepts manual override.
Buckets temperatures into ranges for readable output.

Usage:
    python3 log_exploration/wave1_temp_taxonomy.py <diagnostic.log>
    python3 log_exploration/wave1_temp_taxonomy.py <diagnostic.log> --schedule 0.1:20,0.05-0.5:22
    python3 log_exploration/wave1_temp_taxonomy.py <diagnostic.log> --wrong-only
    python3 log_exploration/wave1_temp_taxonomy.py <diagnostic.log> --no-consensus-only
"""

import argparse
import re
import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def auto_detect_wave1_schedule():
    """Auto-detect Wave 1 temp schedule from the notebook CFG class.

    Reads notebooks/aimo3-solver.ipynb to find wave1_temp_schedule and
    wave1_attempts. Returns dict mapping attempt_number (1-based) -> temperature.
    """
    import json
    nb_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           'notebooks', 'aimo3-solver.ipynb')
    if not os.path.exists(nb_path):
        return None

    with open(nb_path) as f:
        nb = json.load(f)

    # Find the cell with wave1_temp_schedule
    for cell in nb['cells']:
        if cell['cell_type'] != 'code':
            continue
        source = ''.join(cell['source'])
        if 'wave1_temp_schedule' in source:
            # Extract the schedule by executing just that line
            local_ns = {}
            for line in source.split('\n'):
                stripped = line.strip()
                if stripped.startswith('wave1_temp_schedule'):
                    try:
                        exec(stripped, {'__builtins__': __builtins__}, local_ns)
                    except Exception:
                        pass
            if 'wave1_temp_schedule' in local_ns:
                schedule = local_ns['wave1_temp_schedule']
                return {i + 1: t for i, t in enumerate(schedule)}
    return None


def parse_temp_schedule(schedule_str):
    """Parse temperature schedule string like '0.1:20,linspace(0.05,0.5,22)'.

    Supports:
      - Simple: '0.1:20,0.3:10' -> 20 attempts at 0.1, 10 at 0.3
      - Linspace: '0.1:20,linspace(0.05,0.5,22)' -> 20 at 0.1, then 22 linspaced

    Returns dict mapping attempt_number (1-based) -> temperature.
    """
    temp_map = {}
    attempt = 1
    for part in schedule_str.split(','):
        part = part.strip()
        if part.startswith('linspace('):
            # Parse linspace(start, end, count)
            m = re.match(r'linspace\(([\d.]+)\s*,\s*([\d.]+)\s*,\s*(\d+)\)', part)
            if m:
                start, end, count = float(m.group(1)), float(m.group(2)), int(m.group(3))
                for i in range(count):
                    t = round(start + i * (end - start) / (count - 1), 4) if count > 1 else start
                    temp_map[attempt] = t
                    attempt += 1
            continue
        temp_s, count_s = part.split(':')
        temp = float(temp_s)
        count = int(count_s)
        for _ in range(count):
            temp_map[attempt] = temp
            attempt += 1
    return temp_map


def parse_wave1_blocks(logfile):
    """Parse Wave 1 classification blocks from raw diagnostic log.

    Returns list of dicts, one per problem, with:
      - pid, expected, problem_idx
      - attempts: list of {attempt_num, taxonomy, conf, turns, time}
      - selected_taxonomy: the SELECTED taxonomy or None
      - no_consensus: bool
      - taxonomy_votes: dict of taxonomy -> votes
      - basic_ignored: list of basic taxonomies that were ignored
    """
    results = []
    current = None

    with open(logfile) as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i]

        # Match problem header: [N/50] Problem PID | Expected: X
        m = re.match(r'\s*\[(\d+)/\d+\]\s+Problem\s+(\w+)\s+\|\s+Expected:\s+(\d+)', line)
        if m:
            current = {
                'problem_idx': int(m.group(1)),
                'pid': m.group(2),
                'expected': int(m.group(3)),
                'attempts': [],
                'selected_taxonomy': None,
                'selected_taxonomies': [],  # can have multiple SELECTED
                'no_consensus': False,
                'taxonomy_votes': {},
                'basic_ignored': [],
                'classification_failures': 0,
            }
            results.append(current)
            i += 1
            continue

        # Count "Classification failed" lines
        if current and 'Classification failed:' in line:
            current['classification_failures'] += 1

        # Match attempt line: Attempt N: taxonomy_name (conf=X, turns=N, time=Xs)
        if current:
            m2 = re.match(
                r'\s+Attempt\s+(\d+):\s+(.+?)\s+\(conf=([\d.]+),\s+turns=(\d+),\s+time=([\d.]+)s\)',
                line
            )
            if m2:
                att_num = int(m2.group(1))
                taxonomy = m2.group(2).strip()
                conf = float(m2.group(3))
                turns = int(m2.group(4))
                time_s = float(m2.group(5))
                current['attempts'].append({
                    'attempt_num': att_num,
                    'taxonomy': taxonomy,
                    'conf': conf,
                    'turns': turns,
                    'time': time_s,
                })

        # Match taxonomy votes block
        if current and '=== WAVE 1 TAXONOMY VOTES ===' in line:
            j = i + 1
            while j < len(lines) and '=== END VOTES ===' not in lines[j]:
                vm = re.match(
                    r'\s+(.+?):\s+([\d.]+)\s+votes(?:\s+<--\s+SELECTED(?:\s+\(>50%\))?)?(?:\s+\(below 50%, ignored\))?',
                    lines[j]
                )
                if vm:
                    tax_name = vm.group(1).strip()
                    votes = float(vm.group(2))
                    is_selected = '<-- SELECTED' in lines[j]
                    is_ignored = 'ignored' in lines[j]

                    current['taxonomy_votes'][tax_name] = votes
                    if is_selected:
                        current['selected_taxonomies'].append(tax_name)
                        if not current['selected_taxonomy']:
                            current['selected_taxonomy'] = tax_name
                    if is_ignored:
                        current['basic_ignored'].append(tax_name)
                j += 1
            i = j
            continue

        # Match no consensus
        if current and 'No taxonomy exceeded 1/3 threshold' in line:
            current['no_consensus'] = True

        i += 1

    return results


def parse_correctness(logfile):
    """Parse STATUS lines to get correctness per problem."""
    correctness = {}
    pid_order = []

    with open(logfile) as f:
        lines = f.readlines()

    current_pid = None
    for line in lines:
        m = re.match(r'\s*\[(\d+)/\d+\]\s+Problem\s+(\w+)', line)
        if m:
            current_pid = m.group(2)
            pid_order.append(current_pid)

        m2 = re.match(r'\s+STATUS:\s+(CORRECT|WRONG)\s+\|', line)
        if m2 and current_pid:
            correctness[current_pid] = m2.group(1) == 'CORRECT'

    return correctness


def get_temp_for_attempt(attempt_num, temp_map):
    """Get temperature for a given attempt number."""
    return temp_map.get(attempt_num, None)


def is_valid_taxonomy(tax):
    """Check if taxonomy is a real classification (not None, 'taxonomy', or garbage)."""
    if tax == 'None':
        return False
    if tax == 'taxonomy':
        return False
    # Filter garbage like '1000\cdot_p\text{_floor'
    if '\\' in tax or '{' in tax:
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Analyze Wave 1 classification quality by temperature bucket.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('logfile', help='Path to diagnostic.log')
    parser.add_argument('--schedule', default=None,
                        help='Temperature schedule as temp:count,... (default: auto-detect from notebook)')
    parser.add_argument('--wrong-only', action='store_true',
                        help='Only show analysis for WRONG problems')
    parser.add_argument('--no-consensus-only', action='store_true',
                        help='Only show analysis for no-consensus problems')
    args = parser.parse_args()

    if args.schedule:
        temp_map = parse_temp_schedule(args.schedule)
    else:
        temp_map = auto_detect_wave1_schedule()
        if temp_map is None:
            print("  ERROR: Could not auto-detect Wave 1 temp schedule from notebook.")
            print("  Use --schedule flag, e.g.: --schedule '0.1:20,linspace(0.05,0.5,22)'")
            sys.exit(1)

    # Bucket nearby temperatures for readable output (round to nearest 0.05)
    def bucket_temp(t):
        return round(round(t / 0.05) * 0.05, 2)

    raw_temps = sorted(set(temp_map.values()))
    bucketed_map = {att: bucket_temp(t) for att, t in temp_map.items()}
    temps_sorted = sorted(set(bucketed_map.values()))
    temp_labels = {t: f'temp={t:.2f}' for t in temps_sorted}

    print(f"  Raw schedule: {len(temp_map)} attempts, {len(raw_temps)} unique temps")
    print(f"  Range: {min(raw_temps):.3f} to {max(raw_temps):.3f}")
    print(f"  Bucketed into {len(temps_sorted)} groups (rounded to nearest 0.05)")

    # Use bucketed map for all analysis
    temp_map = bucketed_map

    # Build attempt ranges for display
    temp_ranges = {}
    for t in temps_sorted:
        atts = [a for a, tv in temp_map.items() if tv == t]
        temp_ranges[t] = (min(atts), max(atts))

    problems = parse_wave1_blocks(args.logfile)
    correctness = parse_correctness(args.logfile)

    if args.wrong_only:
        problems = [p for p in problems if not correctness.get(p['pid'], True)]
    if args.no_consensus_only:
        problems = [p for p in problems if p['no_consensus']]

    # ---- Per-temperature aggregates ----
    # For each temperature bucket, track:
    stats = {t: {
        'total_attempts': 0,       # how many attempts existed at this temp
        'none_count': 0,           # returned None (timeout)
        'taxonomy_literal': 0,     # returned 'taxonomy' (parse failure)
        'garbage': 0,              # returned garbage taxonomy
        'valid_count': 0,          # returned a real taxonomy
        'agree_with_selected': 0,  # agreed with SELECTED taxonomy
        'disagree_with_selected': 0,  # valid but different from selected
        'no_selected_valid': 0,    # valid but problem had no consensus (no selected)
        'basic_count': 0,          # returned basic.basic.basic
        'problems_contributed': 0, # problems where this temp had >= 1 attempt
    } for t in temps_sorted}

    # Per-problem detail for wrong/no-consensus
    problem_details = []

    for prob in problems:
        pid = prob['pid']
        selected = prob['selected_taxonomy']
        is_correct = correctness.get(pid, None)
        is_no_consensus = prob['no_consensus']

        # Track which temps contributed to this problem
        temps_seen = set()

        # Bucket attempts by temperature
        temp_attempts = defaultdict(list)
        for att in prob['attempts']:
            t = get_temp_for_attempt(att['attempt_num'], temp_map)
            if t is None:
                continue
            temp_attempts[t].append(att)
            temps_seen.add(t)

        for t in temps_seen:
            stats[t]['problems_contributed'] += 1

        for t in temps_sorted:
            for att in temp_attempts.get(t, []):
                stats[t]['total_attempts'] += 1
                tax = att['taxonomy']

                if tax == 'None':
                    stats[t]['none_count'] += 1
                elif tax == 'taxonomy':
                    stats[t]['taxonomy_literal'] += 1
                elif not is_valid_taxonomy(tax):
                    stats[t]['garbage'] += 1
                else:
                    stats[t]['valid_count'] += 1
                    if tax == 'basic.basic.basic':
                        stats[t]['basic_count'] += 1

                    if selected:
                        # Check if any of the selected taxonomies match
                        if tax in prob['selected_taxonomies']:
                            stats[t]['agree_with_selected'] += 1
                        else:
                            stats[t]['disagree_with_selected'] += 1
                    else:
                        stats[t]['no_selected_valid'] += 1

        # Collect per-problem detail
        detail = {
            'pid': pid,
            'idx': prob['problem_idx'],
            'correct': is_correct,
            'selected': selected,
            'selected_all': prob['selected_taxonomies'],
            'no_consensus': is_no_consensus,
            'votes': prob['taxonomy_votes'],
            'basic_ignored': prob['basic_ignored'],
            'failures': prob['classification_failures'],
            'temp_breakdown': {},
        }
        for t in temps_sorted:
            atts = temp_attempts.get(t, [])
            tax_counts = defaultdict(int)
            none_count = 0
            junk_count = 0
            for att in atts:
                tax = att['taxonomy']
                if tax == 'None':
                    none_count += 1
                elif not is_valid_taxonomy(tax):
                    junk_count += 1
                else:
                    tax_counts[tax] += 1
            detail['temp_breakdown'][t] = {
                'total': len(atts),
                'none': none_count,
                'junk': junk_count,
                'valid_taxes': dict(tax_counts),
            }
        problem_details.append(detail)

    # ===== PRINT REPORT =====

    print("=" * 90)
    print("  WAVE 1 CLASSIFICATION QUALITY BY TEMPERATURE")
    print("=" * 90)
    print()
    schedule_src = args.schedule if args.schedule else "auto-detected from notebook"
    print(f"  Temperature schedule: {schedule_src}")
    for t in temps_sorted:
        lo, hi = temp_ranges[t]
        count = sum(1 for tv in temp_map.values() if tv == t)
        print(f"    {temp_labels[t]:12s} -> {count} attempts/problem (att#{lo}-{hi})")
    print(f"\n  Problems analyzed: {len(problems)}")
    print()

    # ---- Summary table ----
    print("-" * 90)
    print(f"  {'Metric':<40s}", end="")
    for t in temps_sorted:
        print(f"  {temp_labels[t]:>14s}", end="")
    print()
    print("-" * 90)

    def print_row(label, getter, fmt='d', pct_of=None):
        print(f"  {label:<40s}", end="")
        for t in temps_sorted:
            val = getter(stats[t])
            if fmt == 'd':
                s = f"{val:>14d}"
            elif fmt == '.1f':
                s = f"{val:>14.1f}"
            elif fmt == 'pct':
                denom = pct_of(stats[t]) if callable(pct_of) else pct_of
                if denom and denom > 0:
                    s = f"{val/denom*100:>13.1f}%"
                else:
                    s = f"{'N/A':>14s}"
            print(s, end="")
        print()

    print_row("Total attempts", lambda s: s['total_attempts'])
    print_row("Problems contributed to", lambda s: s['problems_contributed'])
    print()
    print_row("None/timeout", lambda s: s['none_count'])
    print_row("  % of total", lambda s: s['none_count'], fmt='pct',
              pct_of=lambda s: s['total_attempts'])
    print_row("'taxonomy' literal (junk)", lambda s: s['taxonomy_literal'])
    print_row("Garbage taxonomy", lambda s: s['garbage'])
    print_row("  Total invalid", lambda s: s['none_count'] + s['taxonomy_literal'] + s['garbage'])
    print_row("  % invalid", lambda s: s['none_count'] + s['taxonomy_literal'] + s['garbage'],
              fmt='pct', pct_of=lambda s: s['total_attempts'])
    print()
    print_row("Valid taxonomy", lambda s: s['valid_count'])
    print_row("  % valid", lambda s: s['valid_count'], fmt='pct',
              pct_of=lambda s: s['total_attempts'])
    print_row("  basic.basic.basic", lambda s: s['basic_count'])
    print()
    print_row("Agrees with SELECTED", lambda s: s['agree_with_selected'])
    print_row("  % of valid (agreement rate)", lambda s: s['agree_with_selected'], fmt='pct',
              pct_of=lambda s: s['valid_count'])
    print_row("Disagrees with SELECTED", lambda s: s['disagree_with_selected'])
    print_row("  % of valid (disagreement)", lambda s: s['disagree_with_selected'], fmt='pct',
              pct_of=lambda s: s['valid_count'])
    print_row("Valid but no consensus", lambda s: s['no_selected_valid'])
    print("-" * 90)
    print()

    # ---- Average valid/invalid per problem ----
    print("-" * 90)
    print("  PER-PROBLEM AVERAGES (across all problems)")
    print("-" * 90)
    for t in temps_sorted:
        s = stats[t]
        n = s['problems_contributed'] or 1
        lo, hi = temp_ranges[t]
        max_possible = hi - lo + 1
        avg_attempts = s['total_attempts'] / n
        avg_valid = s['valid_count'] / n
        avg_none = s['none_count'] / n
        avg_junk = (s['taxonomy_literal'] + s['garbage']) / n
        print(f"  {temp_labels[t]:12s}: {avg_attempts:.1f}/{max_possible} attempts ran, "
              f"{avg_valid:.1f} valid, {avg_none:.1f} None, {avg_junk:.1f} junk")
    print()

    # ---- WRONG problems detail ----
    wrong_details = [d for d in problem_details if d['correct'] is False]
    if wrong_details:
        print("=" * 90)
        print(f"  WRONG PROBLEMS ({len(wrong_details)}) - Temperature breakdown")
        print("=" * 90)
        for d in wrong_details:
            sel_str = d['selected'] or '(no consensus)'
            print(f"\n  [{d['idx']}/50] Problem {d['pid']} | Selected: {sel_str}")
            if d['selected_all']:
                print(f"    All selected: {', '.join(d['selected_all'])}")
            if d['no_consensus']:
                print(f"    ** NO CONSENSUS **")
            if d['votes']:
                print(f"    Votes: {', '.join(f'{t}: {v:.1f}' for t, v in sorted(d['votes'].items(), key=lambda x: -x[1]))}")
            for t in temps_sorted:
                tb = d['temp_breakdown'][t]
                parts = []
                if tb['none']:
                    parts.append(f"{tb['none']} None")
                if tb['junk']:
                    parts.append(f"{tb['junk']} junk")
                for tax, cnt in sorted(tb['valid_taxes'].items(), key=lambda x: -x[1]):
                    marker = ""
                    if d['selected'] and tax == d['selected']:
                        marker = " [=SELECTED]"
                    elif d['selected'] and tax != d['selected']:
                        marker = " [DISAGREE]"
                    parts.append(f"{cnt} {tax}{marker}")
                total = tb['total']
                lo, hi = temp_ranges[t]
                missing = (hi - lo + 1) - total
                if missing > 0:
                    parts.append(f"{missing} missing/failed")
                print(f"    {temp_labels[t]:12s} ({total:2d} ran): {', '.join(parts) if parts else 'no data'}")
        print()

    # ---- No-consensus problems detail ----
    no_cons_details = [d for d in problem_details if d['no_consensus']]
    if no_cons_details:
        print("=" * 90)
        print(f"  NO-CONSENSUS PROBLEMS ({len(no_cons_details)}) - What each temperature preferred")
        print("=" * 90)
        for d in no_cons_details:
            already_shown = d['correct'] is False and not args.no_consensus_only
            label = " (also WRONG)" if d['correct'] is False else " (CORRECT despite no consensus)"
            print(f"\n  [{d['idx']}/50] Problem {d['pid']}{label}")
            if d['votes']:
                print(f"    Final votes: {', '.join(f'{t}: {v:.1f}' for t, v in sorted(d['votes'].items(), key=lambda x: -x[1]))}")
            if d['basic_ignored']:
                print(f"    basic ignored: {', '.join(d['basic_ignored'])}")

            for t in temps_sorted:
                tb = d['temp_breakdown'][t]
                parts = []
                if tb['none']:
                    parts.append(f"{tb['none']} None")
                if tb['junk']:
                    parts.append(f"{tb['junk']} junk")
                for tax, cnt in sorted(tb['valid_taxes'].items(), key=lambda x: -x[1]):
                    parts.append(f"{cnt}x {tax}")
                total = tb['total']
                lo, hi = temp_ranges[t]
                missing = (hi - lo + 1) - total
                if missing > 0:
                    parts.append(f"{missing} missing")
                print(f"    {temp_labels[t]:12s} ({total:2d} ran): {', '.join(parts) if parts else 'no data'}")
        print()

    # ---- Cross-temperature agreement analysis ----
    print("=" * 90)
    print("  CROSS-TEMPERATURE AGREEMENT")
    print("=" * 90)
    print()

    # For each pair of temperatures, how often do they agree on taxonomy?
    # Only consider problems where both temps produced at least 1 valid taxonomy
    if len(temps_sorted) > 1:
        for i_t, t1 in enumerate(temps_sorted):
            for t2 in temps_sorted[i_t + 1:]:
                agree = 0
                disagree = 0
                for d in problem_details:
                    tb1 = d['temp_breakdown'][t1]
                    tb2 = d['temp_breakdown'][t2]
                    taxes1 = set(tb1['valid_taxes'].keys()) - {'basic.basic.basic'}
                    taxes2 = set(tb2['valid_taxes'].keys()) - {'basic.basic.basic'}
                    if not taxes1 or not taxes2:
                        continue
                    # Get plurality taxonomy for each
                    top1 = max(tb1['valid_taxes'].items(), key=lambda x: x[1])[0]
                    top2 = max(tb2['valid_taxes'].items(), key=lambda x: x[1])[0]
                    if top1 == top2:
                        agree += 1
                    else:
                        disagree += 1
                total = agree + disagree
                if total > 0:
                    print(f"  {temp_labels[t1]} vs {temp_labels[t2]}: "
                          f"{agree}/{total} agree ({agree / total * 100:.1f}%), "
                          f"{disagree}/{total} disagree ({disagree / total * 100:.1f}%)")
        print()

    # ---- Confidence and timing by temperature ----
    print("=" * 90)
    print("  TIMING AND TURNS BY TEMPERATURE")
    print("=" * 90)
    print()

    for t in temps_sorted:
        valid_times = []
        none_times = []
        valid_turns = []
        none_turns = []
        for d in problem_details:
            for att in [a for a in d.get('_raw_attempts', [])]:
                pass  # We need raw data

        # Re-collect from problems directly
        all_valid_times = {t: [] for t in temps_sorted}
        all_none_times = {t: [] for t in temps_sorted}
        all_valid_turns = {t: [] for t in temps_sorted}

    for prob in problems:
        for att in prob['attempts']:
            t = get_temp_for_attempt(att['attempt_num'], temp_map)
            if t is None:
                continue
            if att['taxonomy'] == 'None':
                all_none_times[t].append(att['time'])
            elif is_valid_taxonomy(att['taxonomy']):
                all_valid_times[t].append(att['time'])
                all_valid_turns[t].append(att['turns'])

    for t in temps_sorted:
        vt = all_valid_times[t]
        nt = all_none_times[t]
        turns = all_valid_turns[t]
        print(f"  {temp_labels[t]}:")
        if vt:
            print(f"    Valid: avg {sum(vt) / len(vt):.1f}s, median {sorted(vt)[len(vt) // 2]:.1f}s, "
                  f"avg turns {sum(turns) / len(turns):.1f}")
        if nt:
            print(f"    None:  avg {sum(nt) / len(nt):.1f}s (always ~100s timeout)")
        print(f"    Valid/None split: {len(vt)} valid, {len(nt)} None")
        print()

    # ---- Summary insight ----
    print("=" * 90)
    print("  KEY INSIGHTS")
    print("=" * 90)
    print()

    best_valid_rate = None
    best_agree_rate = None
    for t in temps_sorted:
        s = stats[t]
        total = s['total_attempts'] or 1
        valid_rate = s['valid_count'] / total
        if s['valid_count'] > 0:
            agree_rate = s['agree_with_selected'] / s['valid_count']
        else:
            agree_rate = 0
        if best_valid_rate is None or valid_rate > best_valid_rate[1]:
            best_valid_rate = (t, valid_rate)
        if best_agree_rate is None or agree_rate > best_agree_rate[1]:
            best_agree_rate = (t, agree_rate)

    if best_valid_rate:
        print(f"  Highest valid taxonomy rate: {temp_labels[best_valid_rate[0]]} "
              f"({best_valid_rate[1] * 100:.1f}%)")
    if best_agree_rate:
        print(f"  Highest agreement with SELECTED: {temp_labels[best_agree_rate[0]]} "
              f"({best_agree_rate[1] * 100:.1f}%)")

    # Check if any temperature is mostly producing None
    for t in temps_sorted:
        s = stats[t]
        total = s['total_attempts'] or 1
        none_pct = s['none_count'] / total * 100
        if none_pct > 50:
            print(f"  WARNING: {temp_labels[t]} produces None {none_pct:.0f}% of the time")

    # Check taxonomy literal
    for t in temps_sorted:
        s = stats[t]
        if s['taxonomy_literal'] > 0:
            print(f"  NOTE: {temp_labels[t]} returns literal 'taxonomy' {s['taxonomy_literal']} times "
                  f"({s['taxonomy_literal'] / (s['total_attempts'] or 1) * 100:.1f}%)")

    print()


if __name__ == '__main__':
    main()
