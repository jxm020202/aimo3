#!/usr/bin/env python3
"""
AIMO3 Temperature Effectiveness by Tier
=========================================
Breaks down temperature stats by competition tier to answer:
- Is 0.3 still the best temp for HARD problems?
- Does optimal temperature differ by difficulty tier?
- For Tier 0.5 (hard), what schedule would maximize score?

Usage:
    python log_exploration/temperature_by_tier.py <logfile>

Example:
    python log_exploration/temperature_by_tier.py output/v31/diagnostic.log
"""

import sys
import os
from collections import defaultdict, Counter
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def bucket_temp(t):
    """Round temperature to nearest 0.1 for bucketing."""
    if t is None:
        return None
    return round(t, 1)


def extract_tier(batch_name):
    """Extract a clean tier label from batch_name."""
    if not batch_name:
        return "TIER ? (unlabeled)"
    # Extract "TIER X" from strings like "TIER 0.5 — HISTORICAL HARD (2x)"
    bn = batch_name.strip()
    if "TIER" in bn.upper():
        # Return the full batch name as tier label for clarity
        return bn
    return bn


def deduplicate_problems(problems):
    """Merge dual-run entries: combine attempts from all runs of the same problem ID."""
    by_pid = defaultdict(list)
    for p in problems:
        by_pid[p.problem_id].append(p)

    merged = []
    for pid, entries in by_pid.items():
        base = entries[0]
        all_attempts = []
        for e in entries:
            all_attempts.extend(e.attempts)
        any_correct = any(e.correct for e in entries)

        from log_exploration.log_query import Problem
        m = Problem(
            problem_id=pid,
            batch_name=base.batch_name,
            batch_idx=base.batch_idx,
            batch_total=base.batch_total,
            problem_text=base.problem_text,
            budget=base.budget,
            deadline=base.deadline,
            predicted=base.predicted,
            expected=base.expected,
            correct=any_correct,
            wall_time=sum(e.wall_time for e in entries),
            total_answered=sum(e.total_answered for e in entries),
            total_attempts=sum(e.total_attempts for e in entries),
            total_code_calls=sum(e.total_code_calls for e in entries),
            total_errors=sum(e.total_errors for e in entries),
            total_tokens=sum(e.total_tokens for e in entries),
        )
        m.attempts = all_attempts
        merged_votes = Counter()
        for e in entries:
            for ans, cnt in e.votes.items():
                merged_votes[ans] += cnt
        m.votes = dict(merged_votes)
        merged.append(m)
    return sorted(merged, key=lambda p: p.problem_id)


def simulate_majority_vote(attempts, expected):
    """Given a list of attempts, majority-vote and return (predicted, is_correct)."""
    votes = Counter()
    for a in attempts:
        if a.answer is not None:
            votes[a.answer] += 1
    if votes:
        predicted = votes.most_common(1)[0][0]
        return predicted, (predicted == expected)
    return None, False


def analyze_tier(tier_name, tier_problems, temps_sorted, all_temps_sorted):
    """Full analysis for a single tier."""
    total_problems = len(tier_problems)
    correct_problems = sum(1 for p in tier_problems if p.correct)

    print(f"\n{'='*100}")
    print(f"  TIER: {tier_name}")
    print(f"  Problems: {total_problems} | Correct: {correct_problems}/{total_problems} "
          f"({correct_problems/total_problems*100:.1f}%)")
    print(f"{'='*100}")

    # Collect all attempts by temp
    by_temp = defaultdict(list)  # temp -> [(problem, attempt)]
    for p in tier_problems:
        for a in p.attempts:
            t = bucket_temp(a.temperature)
            if t is not None:
                by_temp[t].append((p, a))

    tier_temps = sorted(set(t for t in by_temp.keys()))

    # ── Per-Temperature Stats Table ──
    print(f"\n  {'Temp':>5} {'Total':>6} {'Correct':>8} {'Wrong':>6} {'None':>6} "
          f"{'RawAcc%':>8} {'Acc%':>7} {'None%':>7} {'AvgErr':>7} {'UniqueS':>8}")
    print(f"  {'─'*5} {'─'*6} {'─'*8} {'─'*6} {'─'*6} {'─'*8} {'─'*7} {'─'*7} {'─'*7} {'─'*8}")

    temp_stats = {}

    # Precompute: for each problem, which temps got it correct?
    prob_correct_temps = {}
    for p in tier_problems:
        correct_temps = set()
        for a in p.attempts:
            t = bucket_temp(a.temperature)
            if t is not None and a.answer is not None and a.answer == p.expected:
                correct_temps.add(t)
        prob_correct_temps[p.problem_id] = correct_temps

    # Unique solves: problems ONLY solved by this temp
    unique_by_temp = defaultdict(list)
    for pid, temps_set in prob_correct_temps.items():
        if len(temps_set) == 1:
            unique_by_temp[list(temps_set)[0]].append(pid)

    for t in tier_temps:
        pairs = by_temp[t]
        total = len(pairs)
        correct = sum(1 for p, a in pairs if a.answer is not None and a.answer == p.expected)
        wrong = sum(1 for p, a in pairs if a.answer is not None and a.answer != p.expected)
        nones = sum(1 for _, a in pairs if a.is_none)
        non_none = total - nones
        raw_acc = (correct / total * 100) if total > 0 else 0.0
        acc = (correct / non_none * 100) if non_none > 0 else 0.0
        none_rate = (nones / total * 100) if total > 0 else 0.0
        avg_errors = sum(a.errors for _, a in pairs) / total if total > 0 else 0.0
        unique_count = len(unique_by_temp.get(t, []))

        temp_stats[t] = {
            'total': total, 'correct': correct, 'wrong': wrong, 'nones': nones,
            'raw_acc': raw_acc, 'acc': acc, 'none_rate': none_rate,
            'avg_errors': avg_errors, 'unique_solves': unique_count,
            'non_none': non_none,
        }

        print(f"  {t:>5.1f} {total:>6} {correct:>8} {wrong:>6} {nones:>6} "
              f"{raw_acc:>7.1f}% {acc:>6.1f}% {none_rate:>6.1f}% {avg_errors:>7.2f} {unique_count:>8}")

    # ── Best Temperature for this Tier ──
    print(f"\n  BEST TEMPERATURE FOR THIS TIER:")
    if tier_temps:
        best_raw = max(tier_temps, key=lambda t: temp_stats[t]['raw_acc'])
        best_acc = max(tier_temps, key=lambda t: temp_stats[t]['acc'])
        lowest_none = min(tier_temps, key=lambda t: temp_stats[t]['none_rate'])
        most_unique = max(tier_temps, key=lambda t: temp_stats[t]['unique_solves'])
        lowest_err = min(tier_temps, key=lambda t: temp_stats[t]['avg_errors'])

        print(f"    Best raw accuracy:    temp={best_raw:.1f} ({temp_stats[best_raw]['raw_acc']:.1f}%)")
        print(f"    Best accuracy (excl None): temp={best_acc:.1f} ({temp_stats[best_acc]['acc']:.1f}%)")
        print(f"    Lowest None rate:     temp={lowest_none:.1f} ({temp_stats[lowest_none]['none_rate']:.1f}%)")
        print(f"    Most unique solves:   temp={most_unique:.1f} ({temp_stats[most_unique]['unique_solves']})")
        print(f"    Lowest avg errors:    temp={lowest_err:.1f} ({temp_stats[lowest_err]['avg_errors']:.2f})")

    # ── Unique Solves Detail ──
    print(f"\n  UNIQUE SOLVES (problems ONLY solved by this temp):")
    any_unique = False
    for t in tier_temps:
        pids = unique_by_temp.get(t, [])
        if pids:
            any_unique = True
            p_details = []
            for pid in pids:
                p = next(pp for pp in tier_problems if pp.problem_id == pid)
                status = "CORRECT overall" if p.correct else "WRONG overall (outvoted!)"
                p_details.append(f"{pid} ({status})")
            print(f"    Temp {t:.1f}: {len(pids)} unique → {', '.join(p_details)}")
    if not any_unique:
        print(f"    (none — all solvable problems are solved by multiple temps)")

    # ── Per-Problem Heat Map ──
    print(f"\n  PER-PROBLEM x TEMPERATURE MATRIX:")
    temp_hdrs = '  '.join(f'{t:>5.1f}' for t in tier_temps)
    print(f"    {'Problem':<10} {'Exp':>7} {'Pred':>7} {'OK':>4}  {temp_hdrs}")
    print(f"    {'─'*10} {'─'*7} {'─'*7} {'─'*4}  " + '  '.join('─'*5 for _ in tier_temps))

    for p in sorted(tier_problems, key=lambda x: (x.correct, x.problem_id)):
        exp = str(p.expected) if p.expected is not None else '?'
        pred = str(p.predicted) if p.predicted is not None else '?'
        ok = 'Y' if p.correct else 'N'
        cells = []
        for t in tier_temps:
            c = sum(1 for a in p.attempts if bucket_temp(a.temperature) == t
                    and a.answer is not None and a.answer == p.expected)
            n = sum(1 for a in p.attempts if bucket_temp(a.temperature) == t)
            none_c = sum(1 for a in p.attempts if bucket_temp(a.temperature) == t and a.is_none)
            if n == 0:
                cells.append('    -')
            elif c > 0:
                cells.append(f' {c}/{n:>2} ')
            elif none_c == n:
                cells.append(f' N/{n:>2} ')
            else:
                cells.append(f' 0/{n:>2} ')
        print(f"    {p.problem_id:<10} {exp:>7} {pred:>7} {ok:>4}  {'  '.join(cells)}")

    return temp_stats, unique_by_temp, prob_correct_temps


def simulate_schedules(tier_name, tier_problems, temps_sorted):
    """Simulate different temperature schedules for a tier and compare."""
    print(f"\n  SCHEDULE SIMULATIONS FOR {tier_name}:")
    print(f"  (What if we changed the temperature mix? Majority vote on subsets.)")

    # Define schedules to test (all sum to 16)
    schedules = {
        "Current [0.1x1, 0.3x5, 0.5x6, 0.7x4]": {0.1: 1, 0.3: 5, 0.5: 6, 0.7: 4},
        "All 0.1 x16":                             {0.1: 16},
        "All 0.3 x16":                             {0.3: 16},
        "All 0.5 x16":                             {0.5: 16},
        "All 0.7 x16":                             {0.7: 16},
        "Heavy 0.3: [0.1x1, 0.3x11, 0.5x4]":     {0.1: 1, 0.3: 11, 0.5: 4},
        "Heavy 0.3: [0.3x10, 0.5x6]":             {0.3: 10, 0.5: 6},
        "Heavy 0.3: [0.3x12, 0.5x4]":             {0.3: 12, 0.5: 4},
        "Heavy 0.5: [0.1x1, 0.3x3, 0.5x10, 0.7x2]": {0.1: 1, 0.3: 3, 0.5: 10, 0.7: 2},
        "Low only: [0.1x4, 0.3x12]":              {0.1: 4, 0.3: 12},
        "Low+mid: [0.1x2, 0.3x8, 0.5x6]":        {0.1: 2, 0.3: 8, 0.5: 6},
        "Balanced: [0.1x4, 0.3x4, 0.5x4, 0.7x4]": {0.1: 4, 0.3: 4, 0.5: 4, 0.7: 4},
        "No 0.7: [0.1x2, 0.3x6, 0.5x8]":         {0.1: 2, 0.3: 6, 0.5: 8},
    }

    results = {}
    for name, sched in schedules.items():
        correct_count = 0
        wrong_details = []
        for p in tier_problems:
            # Collect available attempts by temp
            attempts_by_temp = defaultdict(list)
            for a in p.attempts:
                t = bucket_temp(a.temperature)
                if t is not None:
                    attempts_by_temp[t].append(a)

            # Select attempts per schedule
            selected = []
            for t, count in sched.items():
                available = attempts_by_temp.get(t, [])
                selected.extend(available[:count])

            predicted, is_correct = simulate_majority_vote(selected, p.expected)
            if is_correct:
                correct_count += 1
            else:
                wrong_details.append(p.problem_id)

        results[name] = (correct_count, wrong_details)

    # Sort by score descending
    sorted_results = sorted(results.items(), key=lambda x: -x[1][0])

    # Find current score for delta
    current_key = "Current [0.1x1, 0.3x5, 0.5x6, 0.7x4]"
    current_score = results[current_key][0] if current_key in results else 0

    total = len(tier_problems)
    print(f"\n    {'Schedule':<55} {'Score':>8} {'Delta':>6}")
    print(f"    {'─'*55} {'─'*8} {'─'*6}")
    for name, (score, wrong) in sorted_results:
        delta = score - current_score
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        marker = " <<<" if name == current_key else ""
        print(f"    {name:<55} {score:>3}/{total:<3}  {delta_str:>5}{marker}")

    # Show gained/lost problems for best schedule vs current
    best_name, (best_score, best_wrong) = sorted_results[0]
    _, current_wrong = results[current_key]

    if best_name != current_key:
        gained = set(current_wrong) - set(best_wrong)
        lost = set(best_wrong) - set(current_wrong)
        if gained or lost:
            print(f"\n    Best schedule \"{best_name}\" vs Current:")
            if gained:
                for pid in sorted(gained):
                    p = next(pp for pp in tier_problems if pp.problem_id == pid)
                    print(f"      GAINED: {pid} (expected={p.expected})")
            if lost:
                for pid in sorted(lost):
                    p = next(pp for pp in tier_problems if pp.problem_id == pid)
                    print(f"      LOST:   {pid} (expected={p.expected})")

    return results


def cross_tier_summary(all_tier_stats, tiers_order, temps_sorted):
    """Cross-tier comparison: which temp is best per tier?"""
    print(f"\n\n{'='*100}")
    print(f"  CROSS-TIER TEMPERATURE COMPARISON")
    print(f"{'='*100}")

    # Table: rows = tiers, columns = temps, cells = raw accuracy
    print(f"\n  RAW ACCURACY (correct/total) BY TIER x TEMPERATURE:")
    temp_hdrs = ''.join(f'  {t:>7.1f}' for t in temps_sorted)
    print(f"    {'Tier':<50}{temp_hdrs}  {'Best':>8}")
    print(f"    {'─'*50}" + ''.join(f'  {"─"*7}' for _ in temps_sorted) + f'  {"─"*8}')

    for tier_name in tiers_order:
        stats = all_tier_stats.get(tier_name, {})
        cells = []
        best_t = None
        best_acc = -1
        for t in temps_sorted:
            s = stats.get(t, {})
            raw_acc = s.get('raw_acc', 0)
            cells.append(f'{raw_acc:>6.1f}%')
            if raw_acc > best_acc:
                best_acc = raw_acc
                best_t = t
        cell_str = '  '.join(cells)
        short_name = tier_name[:50]
        print(f"    {short_name:<50}  {cell_str}  {best_t:>7.1f}")

    # None rate comparison
    print(f"\n  NONE RATE BY TIER x TEMPERATURE:")
    temp_hdrs = ''.join(f'  {t:>7.1f}' for t in temps_sorted)
    print(f"    {'Tier':<50}{temp_hdrs}  {'Best':>8}")
    print(f"    {'─'*50}" + ''.join(f'  {"─"*7}' for _ in temps_sorted) + f'  {"─"*8}')

    for tier_name in tiers_order:
        stats = all_tier_stats.get(tier_name, {})
        cells = []
        best_t = None
        best_none = 101
        for t in temps_sorted:
            s = stats.get(t, {})
            none_rate = s.get('none_rate', 100)
            cells.append(f'{none_rate:>6.1f}%')
            if none_rate < best_none:
                best_none = none_rate
                best_t = t
        cell_str = '  '.join(cells)
        short_name = tier_name[:50]
        print(f"    {short_name:<50}  {cell_str}  {best_t:>7.1f}")

    # Unique solves comparison
    print(f"\n  UNIQUE SOLVES BY TIER x TEMPERATURE:")
    temp_hdrs = ''.join(f'  {t:>7.1f}' for t in temps_sorted)
    print(f"    {'Tier':<50}{temp_hdrs}  {'Best':>8}")
    print(f"    {'─'*50}" + ''.join(f'  {"─"*7}' for _ in temps_sorted) + f'  {"─"*8}')

    for tier_name in tiers_order:
        stats = all_tier_stats.get(tier_name, {})
        cells = []
        best_t = None
        best_uniq = -1
        for t in temps_sorted:
            s = stats.get(t, {})
            uniq = s.get('unique_solves', 0)
            cells.append(f'{uniq:>7}')
            if uniq > best_uniq:
                best_uniq = uniq
                best_t = t
        cell_str = '  '.join(cells)
        short_name = tier_name[:50]
        print(f"    {short_name:<50}  {cell_str}  {best_t:>7.1f}")

    # Error rate comparison
    print(f"\n  AVG ERRORS BY TIER x TEMPERATURE:")
    temp_hdrs = ''.join(f'  {t:>7.1f}' for t in temps_sorted)
    print(f"    {'Tier':<50}{temp_hdrs}  {'Best':>8}")
    print(f"    {'─'*50}" + ''.join(f'  {"─"*7}' for _ in temps_sorted) + f'  {"─"*8}')

    for tier_name in tiers_order:
        stats = all_tier_stats.get(tier_name, {})
        cells = []
        best_t = None
        best_err = 999
        for t in temps_sorted:
            s = stats.get(t, {})
            avg_err = s.get('avg_errors', 0)
            cells.append(f'{avg_err:>7.2f}')
            if avg_err < best_err:
                best_err = avg_err
                best_t = t
        cell_str = '  '.join(cells)
        short_name = tier_name[:50]
        print(f"    {short_name:<50}  {cell_str}  {best_t:>7.1f}")


def key_question_analysis(problems, tier_problems_by_name, temps_sorted):
    """Answer the key question: Is 0.3 the best for hard problems?"""
    print(f"\n\n{'='*100}")
    print(f"  KEY QUESTION: IS 0.3 THE BEST TEMP FOR HARD PROBLEMS?")
    print(f"{'='*100}")

    # Define hard = TIER 0.5 + unlabeled (Tier ?)
    hard_problems = []
    easy_problems = []
    for p in problems:
        tier = extract_tier(p.batch_name)
        if "TIER 2" in tier.upper():
            easy_problems.append(p)
        else:
            hard_problems.append(p)

    print(f"\n  Hard problems: {len(hard_problems)} (TIER 0.5 + unlabeled)")
    print(f"  Easy problems: {len(easy_problems)} (TIER 2)")

    # Per-temp accuracy for hard vs easy
    print(f"\n  {'':>12} {'───── HARD PROBLEMS ─────':>30}  {'───── EASY PROBLEMS ─────':>30}")
    print(f"  {'Temp':>5}  {'Corr':>5} {'Total':>6} {'Raw%':>6} {'None%':>6}  "
          f"{'Corr':>5} {'Total':>6} {'Raw%':>6} {'None%':>6}  {'Hard-Easy':>10}")
    print(f"  {'─'*5}  {'─'*5} {'─'*6} {'─'*6} {'─'*6}  {'─'*5} {'─'*6} {'─'*6} {'─'*6}  {'─'*10}")

    for t in temps_sorted:
        # Hard
        h_corr = h_total = h_none = 0
        for p in hard_problems:
            for a in p.attempts:
                if bucket_temp(a.temperature) == t:
                    h_total += 1
                    if a.answer is not None and a.answer == p.expected:
                        h_corr += 1
                    if a.is_none:
                        h_none += 1

        # Easy
        e_corr = e_total = e_none = 0
        for p in easy_problems:
            for a in p.attempts:
                if bucket_temp(a.temperature) == t:
                    e_total += 1
                    if a.answer is not None and a.answer == p.expected:
                        e_corr += 1
                    if a.is_none:
                        e_none += 1

        h_raw = (h_corr / h_total * 100) if h_total > 0 else 0
        e_raw = (e_corr / e_total * 100) if e_total > 0 else 0
        h_none_r = (h_none / h_total * 100) if h_total > 0 else 0
        e_none_r = (e_none / e_total * 100) if e_total > 0 else 0
        gap = h_raw - e_raw

        print(f"  {t:>5.1f}  {h_corr:>5} {h_total:>6} {h_raw:>5.1f}% {h_none_r:>5.1f}%  "
              f"{e_corr:>5} {e_total:>6} {e_raw:>5.1f}% {e_none_r:>5.1f}%  {gap:>+9.1f}%")

    # Problem-level: flat-temp solve count
    print(f"\n  FLAT-TEMP SIMULATION (how many problems each temp solves via at-least-one-correct):")
    print(f"\n    {'Temp':>5}  {'Hard Solved':>12}  {'Easy Solved':>12}  {'Total':>8}")
    print(f"    {'─'*5}  {'─'*12}  {'─'*12}  {'─'*8}")

    for t in temps_sorted:
        h_solved = 0
        for p in hard_problems:
            if any(bucket_temp(a.temperature) == t and a.answer is not None and a.answer == p.expected
                   for a in p.attempts):
                h_solved += 1

        e_solved = 0
        for p in easy_problems:
            if any(bucket_temp(a.temperature) == t and a.answer is not None and a.answer == p.expected
                   for a in p.attempts):
                e_solved += 1

        print(f"    {t:>5.1f}  {h_solved:>5}/{len(hard_problems):<5}  "
              f"{e_solved:>5}/{len(easy_problems):<5}  "
              f"{h_solved + e_solved:>3}/{len(hard_problems) + len(easy_problems)}")

    # Answer the key question
    print(f"\n  VERDICT:")
    # Compute best temp for hard by raw accuracy
    best_hard = {}
    for t in temps_sorted:
        h_corr = h_total = 0
        for p in hard_problems:
            for a in p.attempts:
                if bucket_temp(a.temperature) == t:
                    h_total += 1
                    if a.answer is not None and a.answer == p.expected:
                        h_corr += 1
        best_hard[t] = (h_corr / h_total * 100) if h_total > 0 else 0

    best_hard_temp = max(temps_sorted, key=lambda t: best_hard[t])
    print(f"    Best temp for HARD problems (raw accuracy): {best_hard_temp:.1f} ({best_hard[best_hard_temp]:.1f}%)")
    print(f"    All temps for hard: " + ", ".join(f"{t:.1f}={best_hard[t]:.1f}%" for t in temps_sorted))

    best_easy = {}
    for t in temps_sorted:
        e_corr = e_total = 0
        for p in easy_problems:
            for a in p.attempts:
                if bucket_temp(a.temperature) == t:
                    e_total += 1
                    if a.answer is not None and a.answer == p.expected:
                        e_corr += 1
        best_easy[t] = (e_corr / e_total * 100) if e_total > 0 else 0

    best_easy_temp = max(temps_sorted, key=lambda t: best_easy[t])
    print(f"    Best temp for EASY problems (raw accuracy): {best_easy_temp:.1f} ({best_easy[best_easy_temp]:.1f}%)")
    print(f"    All temps for easy: " + ", ".join(f"{t:.1f}={best_easy[t]:.1f}%" for t in temps_sorted))

    if best_hard_temp != best_easy_temp:
        print(f"\n    >>> DIFFERENT optimal temps! Hard={best_hard_temp:.1f}, Easy={best_easy_temp:.1f}")
        print(f"    >>> Consider tier-specific temperature schedules.")
    else:
        print(f"\n    >>> Same optimal temp ({best_hard_temp:.1f}) for both hard and easy.")


def tier_1_deep_dive(tier_name, tier_problems, temps_sorted):
    """
    Special deep dive for the hardest tier.
    Simulates many schedule variants and finds the optimal.
    """
    total = len(tier_problems)
    correct = sum(1 for p in tier_problems if p.correct)

    print(f"\n\n{'='*100}")
    print(f"  DEEP DIVE: {tier_name}")
    print(f"  Current: {correct}/{total} correct")
    print(f"{'='*100}")

    # Exhaustive schedule search: all ways to allocate 16 attempts across 4 temps
    # Try increments of 2 for efficiency
    print(f"\n  EXHAUSTIVE SCHEDULE SEARCH (allocate 16 attempts across temps, step=1):")
    print(f"  (Only showing top 20 and bottom 5 schedules)\n")

    all_schedules = []
    # Generate all combinations that sum to 16
    for n01 in range(0, 17):
        for n03 in range(0, 17 - n01):
            for n05 in range(0, 17 - n01 - n03):
                n07 = 16 - n01 - n03 - n05
                sched = {}
                if n01 > 0:
                    sched[0.1] = n01
                if n03 > 0:
                    sched[0.3] = n03
                if n05 > 0:
                    sched[0.5] = n05
                if n07 > 0:
                    sched[0.7] = n07

                correct_count = 0
                for p in tier_problems:
                    attempts_by_temp = defaultdict(list)
                    for a in p.attempts:
                        t = bucket_temp(a.temperature)
                        if t is not None:
                            attempts_by_temp[t].append(a)

                    selected = []
                    for t, count in sched.items():
                        available = attempts_by_temp.get(t, [])
                        selected.extend(available[:count])

                    _, is_correct = simulate_majority_vote(selected, p.expected)
                    if is_correct:
                        correct_count += 1

                label = f"0.1x{n01} 0.3x{n03} 0.5x{n05} 0.7x{n07}"
                all_schedules.append((correct_count, label, sched))

    # Sort by score descending
    all_schedules.sort(key=lambda x: -x[0])

    # Show top 20
    print(f"    {'Rank':>5} {'Schedule':<35} {'Score':>8}")
    print(f"    {'─'*5} {'─'*35} {'─'*8}")
    for i, (score, label, _) in enumerate(all_schedules[:20]):
        marker = " <<<" if label == f"0.1x1 0.3x5 0.5x6 0.7x4" else ""
        print(f"    {i+1:>5} {label:<35} {score:>3}/{total}{marker}")

    print(f"    {'...':>5}")
    # Show bottom 5
    for i, (score, label, _) in enumerate(all_schedules[-5:]):
        rank = len(all_schedules) - 5 + i + 1
        print(f"    {rank:>5} {label:<35} {score:>3}/{total}")

    # Best schedule
    best_score, best_label, best_sched = all_schedules[0]
    current_label = f"0.1x1 0.3x5 0.5x6 0.7x4"
    current_score = next(s for s, l, _ in all_schedules if l == current_label)

    print(f"\n  RESULT:")
    print(f"    Current schedule [{current_label}]: {current_score}/{total}")
    print(f"    Best schedule    [{best_label}]: {best_score}/{total}")
    if best_score > current_score:
        print(f"    Improvement: +{best_score - current_score} problems!")

        # Which problems change?
        # Recompute current vs best
        for label_name, sched in [(current_label, {0.1: 1, 0.3: 5, 0.5: 6, 0.7: 4}),
                                   (best_label, best_sched)]:
            pass  # We'll compare below

        current_correct_pids = set()
        best_correct_pids = set()

        for p in tier_problems:
            attempts_by_temp = defaultdict(list)
            for a in p.attempts:
                t = bucket_temp(a.temperature)
                if t is not None:
                    attempts_by_temp[t].append(a)

            # Current
            selected = []
            for t, count in {0.1: 1, 0.3: 5, 0.5: 6, 0.7: 4}.items():
                selected.extend(attempts_by_temp.get(t, [])[:count])
            _, ok = simulate_majority_vote(selected, p.expected)
            if ok:
                current_correct_pids.add(p.problem_id)

            # Best
            selected = []
            for t, count in best_sched.items():
                selected.extend(attempts_by_temp.get(t, [])[:count])
            _, ok = simulate_majority_vote(selected, p.expected)
            if ok:
                best_correct_pids.add(p.problem_id)

        gained = best_correct_pids - current_correct_pids
        lost = current_correct_pids - best_correct_pids
        if gained:
            print(f"    GAINED: {sorted(gained)}")
            for pid in sorted(gained):
                p = next(pp for pp in tier_problems if pp.problem_id == pid)
                print(f"      {pid}: expected={p.expected}")
        if lost:
            print(f"    LOST: {sorted(lost)}")
            for pid in sorted(lost):
                p = next(pp for pp in tier_problems if pp.problem_id == pid)
                print(f"      {pid}: expected={p.expected}")
    elif best_score == current_score:
        # Count how many schedules tie for best
        tie_count = sum(1 for s, _, _ in all_schedules if s == best_score)
        print(f"    Current schedule is already optimal (or tied — {tie_count} schedules score {best_score}/{total})")
    else:
        print(f"    Current is better than best? (shouldn't happen)")

    # Specifically answer: would all-0.3 do better?
    print(f"\n  SPECIFIC QUESTION: Would all-0.3 do better than current mix?")
    all03_score = next(s for s, l, _ in all_schedules if l == f"0.1x0 0.3x16 0.5x0 0.7x0")
    print(f"    All-0.3 (16x): {all03_score}/{total}")
    print(f"    Current mix:   {current_score}/{total}")
    if all03_score > current_score:
        print(f"    >>> YES, all-0.3 gains +{all03_score - current_score}!")
    elif all03_score == current_score:
        print(f"    >>> TIED. All-0.3 = current. Simpler but no gain.")
    else:
        print(f"    >>> NO. All-0.3 loses {current_score - all03_score} problem(s).")


def main():
    if '--help' in sys.argv or len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0 if '--help' in sys.argv else 1)

    logfile = sys.argv[1]
    if not os.path.exists(logfile):
        print(f"Error: {logfile} not found")
        sys.exit(1)

    print(f"{'='*100}")
    print(f"  TEMPERATURE EFFECTIVENESS BY TIER — {logfile}")
    print(f"{'='*100}")

    problems_raw = parse_log(logfile)
    problems = deduplicate_problems(problems_raw)

    total = len(problems)
    correct = sum(1 for p in problems if p.correct)
    print(f"\n  Total problems (deduplicated): {total}")
    print(f"  Overall score: {correct}/{total} ({correct/total*100:.1f}%)")

    # Find all temps
    temps_all = set()
    for p in problems:
        for a in p.attempts:
            t = bucket_temp(a.temperature)
            if t is not None:
                temps_all.add(t)
    temps_sorted = sorted(temps_all)
    print(f"  Temperatures: {temps_sorted}")

    # Group by tier
    tier_groups = defaultdict(list)
    for p in problems:
        tier = extract_tier(p.batch_name)
        tier_groups[tier].append(p)

    tiers_order = sorted(tier_groups.keys())
    print(f"  Tiers found: {len(tiers_order)}")
    for tier_name in tiers_order:
        t_probs = tier_groups[tier_name]
        t_correct = sum(1 for p in t_probs if p.correct)
        print(f"    - {tier_name}: {len(t_probs)} problems ({t_correct}/{len(t_probs)} correct)")

    # Per-tier analysis
    all_tier_stats = {}
    for tier_name in tiers_order:
        tier_probs = tier_groups[tier_name]
        stats, unique, prob_temps = analyze_tier(tier_name, tier_probs, temps_sorted, temps_sorted)
        all_tier_stats[tier_name] = stats

        # Simulate schedules for each tier
        simulate_schedules(tier_name, tier_probs, temps_sorted)

    # Cross-tier comparison
    cross_tier_summary(all_tier_stats, tiers_order, temps_sorted)

    # Key question analysis
    key_question_analysis(problems, tier_groups, temps_sorted)

    # Deep dive: hardest tier (TIER 0.5)
    hard_tier_name = None
    for tier_name in tiers_order:
        if "TIER 0.5" in tier_name.upper() or "HISTORICAL HARD" in tier_name.upper():
            hard_tier_name = tier_name
            break

    if hard_tier_name:
        tier_1_deep_dive(hard_tier_name, tier_groups[hard_tier_name], temps_sorted)

    # Also deep dive unlabeled (Tier ?) if it exists
    for tier_name in tiers_order:
        if "unlabeled" in tier_name.lower() or "?" in tier_name:
            if len(tier_groups[tier_name]) >= 2:
                tier_1_deep_dive(tier_name, tier_groups[tier_name], temps_sorted)

    # Final summary
    print(f"\n\n{'='*100}")
    print(f"  FINAL SUMMARY")
    print(f"{'='*100}")
    print(f"\n  Overall: {correct}/{total} ({correct/total*100:.1f}%)")
    print(f"\n  Per-tier breakdown:")
    for tier_name in tiers_order:
        t_probs = tier_groups[tier_name]
        t_correct = sum(1 for p in t_probs if p.correct)
        # Find best temp for this tier
        stats = all_tier_stats[tier_name]
        if stats:
            best_t = max(stats.keys(), key=lambda t: stats[t]['raw_acc'])
            print(f"    {tier_name}:")
            print(f"      Score: {t_correct}/{len(t_probs)} | Best temp: {best_t:.1f} (raw={stats[best_t]['raw_acc']:.1f}%)")
        else:
            print(f"    {tier_name}: {t_correct}/{len(t_probs)}")

    print()


if __name__ == '__main__':
    main()
