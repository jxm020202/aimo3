#!/usr/bin/env python3
"""Comprehensive single-run summary: score, errors, temps, wave1, reruns, NameErrors, simulations.

Usage: python3 log_exploration/run_summary.py <diagnostic.log>
"""
import sys, re
from collections import Counter
sys.path.insert(0, '.')
from log_exploration.log_query import parse_log


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <diagnostic.log>")
        sys.exit(1)

    log_path = sys.argv[1]
    problems = parse_log(log_path)
    n = len(problems)
    correct = sum(1 for p in problems if p.correct)
    wrong_probs = [p for p in problems if not p.correct]
    all_attempts = [a for p in problems for a in p.attempts]
    total_att = len(all_attempts)

    print(f"{'='*72}")
    print(f"  RUN SUMMARY — {log_path}")
    print(f"{'='*72}")

    # --- Score ---
    print(f"\n  Score: {correct}/{n} ({correct*100/n:.0f}%)")
    print(f"  Wrong: {n - correct} problems")

    # --- Attempts ---
    nones = sum(1 for a in all_attempts if a.answer is None)
    errors = sum(1 for a in all_attempts for t in a.turns if t.is_error)
    print(f"\n  Attempts: {total_att} | Nones: {nones} ({nones*100/total_att:.0f}%) | Errors: {errors}")

    # --- Timing ---
    wall_times = [p.wall_time for p in problems if p.wall_time]
    if wall_times:
        total_min = sum(wall_times) / 60
        print(f"  Total time: {total_min:.1f} min | Per-problem: median={sorted(wall_times)[len(wall_times)//2]:.0f}s, max={max(wall_times):.0f}s")

    # --- Reruns ---
    reruns = [p for p in problems if len(p.attempts) > 32]
    rerun_candidates = []
    for p in problems:
        votes = Counter(a.answer for a in p.attempts if a.answer is not None)
        if votes:
            top_votes = votes.most_common(1)[0][1]
            if top_votes < 11:
                rerun_candidates.append((p, top_votes))
    print(f"\n  Reruns triggered: {len(reruns)}")
    print(f"  Would-rerun (top_votes < 11): {len(rerun_candidates)} problems")
    for p, tv in rerun_candidates:
        status = "CORRECT" if p.correct else "WRONG"
        print(f"    {p.problem_id}: top_votes={tv} ({status}) pred={p.predicted}")

    # --- Wrong problems ---
    print(f"\n  {'─'*72}")
    print(f"  WRONG PROBLEMS ({len(wrong_probs)})")
    print(f"  {'─'*72}")
    for p in wrong_probs:
        votes = Counter(a.answer for a in p.attempts if a.answer is not None)
        top_ans, top_v = votes.most_common(1)[0] if votes else (None, 0)
        correct_found = any(a.answer == p.expected for a in p.attempts)
        correct_votes = votes.get(p.expected, 0)
        diff = abs(p.predicted - p.expected) if p.predicted is not None and p.expected is not None else None
        tag = "OUTVOTED" if correct_found else ("CLOSE" if diff and diff < 50 else "UNSOLVED")
        ne = sum(1 for a in p.attempts for t in a.turns if t.is_error and 'NameError' in (t.output or ''))
        print(f"  [{tag:8s}] {p.problem_id}: pred={p.predicted}, exp={p.expected}, diff={diff}, "
              f"top_votes={top_v}, correct_votes={correct_votes}, NameErr={ne}")

    # --- NameError breakdown ---
    print(f"\n  {'─'*72}")
    print(f"  TOP NAMEERRORS")
    print(f"  {'─'*72}")
    name_errors = Counter()
    for p in problems:
        for a in p.attempts:
            for t in a.turns:
                if t.is_error and t.output and 'NameError' in t.output:
                    m = re.search(r"name '(\w+)' is not defined", t.output)
                    if m:
                        name_errors[m.group(1)] += 1
    for name, count in name_errors.most_common(15):
        print(f"    {name:30s}: {count}")
    print(f"  Total distinct: {len(name_errors)}, total count: {sum(name_errors.values())}")

    # Fixed aliases check
    fixed = {'np', 'sp', 'random', 'time', 'nx'}
    still_broken = {k: v for k, v in name_errors.items() if k in fixed}
    if still_broken:
        print(f"  v36-fixed aliases STILL broken: {still_broken}")
    else:
        print(f"  v36-fixed aliases (np/sp/random/time/nx): all 0 — fix confirmed")

    # --- Temperature distribution ---
    print(f"\n  {'─'*72}")
    print(f"  TEMPERATURE DISTRIBUTION")
    print(f"  {'─'*72}")
    temp_stats = {}
    for a in all_attempts:
        t = round(a.temperature, 3) if a.temperature else 'None'
        if t not in temp_stats:
            temp_stats[t] = {'total': 0, 'correct': 0, 'none': 0, 'wrong': 0}
        temp_stats[t]['total'] += 1
        if a.answer is None:
            temp_stats[t]['none'] += 1
        # We don't know per-attempt correctness easily, so just count answers
    for t in sorted(temp_stats.keys(), key=lambda x: (isinstance(x, str), x)):
        s = temp_stats[t]
        print(f"    temp={t}: {s['total']:4d} attempts, {s['none']:3d} Nones ({s['none']*100/s['total']:.0f}%)")

    # --- Reduced-attempt simulation ---
    print(f"\n  {'─'*72}")
    print(f"  REDUCED-ATTEMPT SIMULATION")
    print(f"  {'─'*72}")
    for n_att in [8, 12, 16, 20, 24, 28, 32]:
        sim_correct = 0
        for p in problems:
            atts = p.attempts[:n_att]
            votes = Counter(a.answer for a in atts if a.answer is not None)
            if votes:
                predicted = votes.most_common(1)[0][0]
                if predicted == p.expected:
                    sim_correct += 1
        print(f"    {n_att:2d} attempts: {sim_correct}/{n} ({sim_correct*100/n:.0f}%)")

    # --- Outvoted analysis ---
    outvoted = []
    for p in wrong_probs:
        if any(a.answer == p.expected for a in p.attempts):
            outvoted.append(p)
    if outvoted:
        print(f"\n  {'─'*72}")
        print(f"  OUTVOTED PROBLEMS ({len(outvoted)}) — correct found but lost vote")
        print(f"  {'─'*72}")
        for p in outvoted:
            votes = Counter(a.answer for a in p.attempts if a.answer is not None)
            correct_v = votes.get(p.expected, 0)
            winner, winner_v = votes.most_common(1)[0]
            correct_atts = [a for a in p.attempts if a.answer == p.expected]
            print(f"    {p.problem_id}: correct got {correct_v} votes vs winner {winner}={winner_v}")
            for a in correct_atts:
                print(f"      Att#{a.attempt_num}: temp={a.temperature}, entropy={a.entropy:.3f}, time={a.time_s:.0f}s")

    print(f"\n{'='*72}")


if __name__ == '__main__':
    main()
