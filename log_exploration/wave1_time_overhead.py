#!/usr/bin/env python3
"""Analyze Wave 1 time overhead: how much time does classification add per problem,
and is it worth it? Compares problems with/without notes injection.

Usage: python3 log_exploration/wave1_time_overhead.py <diagnostic.log>
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

    # Parse Wave 1 data from raw log
    with open(log_path) as f:
        content = f.read()

    # Extract per-problem Wave 1 timing
    # Pattern: "WAVE 1: CLASSIFICATION" followed by attempt lines with time=Xs
    wave1_sections = re.split(r'──+\n\s+\[\d+/\d+\] Problem (\w+)', content)

    problem_wave1 = {}
    for i in range(1, len(wave1_sections), 2):
        pid = wave1_sections[i]
        section = wave1_sections[i + 1] if i + 1 < len(wave1_sections) else ""

        # Find Wave 1 attempt times
        wave1_match = re.search(r'WAVE 1: CLASSIFICATION.*?Budget: (\d+)s', section)
        if not wave1_match:
            continue

        attempt_times = [float(m.group(1)) for m in re.finditer(r'time=([0-9.]+)s\)', section.split('WAVE 2')[0] if 'WAVE 2' in section else section[:5000])]

        # Wave 1 is parallel, so wall time = max attempt time
        if attempt_times:
            wave1_wall = max(attempt_times)
            wave1_mean = sum(attempt_times) / len(attempt_times)
            n_timeout = sum(1 for t in attempt_times if t > 95)
            notes_injected = 'Notes injected:' in section.split('WAVE 2')[0] if 'WAVE 2' in section else 'Notes injected:' in section[:5000]
            # Check for "no notes injected" or "No taxonomy"
            if 'no notes injected' in section[:5000].lower() or 'No taxonomy exceeded' in section[:5000]:
                notes_injected = False
            elif 'Notes injected' in section[:5000]:
                notes_injected = True
            else:
                notes_injected = None  # can't tell

            problem_wave1[pid] = {
                'wall_time': wave1_wall,
                'mean_time': wave1_mean,
                'n_attempts': len(attempt_times),
                'n_timeout': n_timeout,
                'notes_injected': notes_injected,
            }

    print(f"{'='*72}")
    print(f"  WAVE 1 TIME OVERHEAD ANALYSIS")
    print(f"{'='*72}")
    print(f"  Problems with Wave 1 data: {len(problem_wave1)}/{len(problems)}")

    if not problem_wave1:
        print("  No Wave 1 data found in log.")
        return

    # Overall stats
    wall_times = [d['wall_time'] for d in problem_wave1.values()]
    total_wall = sum(wall_times)
    total_timeout = sum(d['n_timeout'] for d in problem_wave1.values())
    total_attempts = sum(d['n_attempts'] for d in problem_wave1.values())

    print(f"\n  Wave 1 wall time per problem:")
    print(f"    Min: {min(wall_times):.1f}s")
    print(f"    Max: {max(wall_times):.1f}s")
    print(f"    Mean: {sum(wall_times)/len(wall_times):.1f}s")
    print(f"    Median: {sorted(wall_times)[len(wall_times)//2]:.1f}s")
    print(f"    Total: {total_wall:.0f}s ({total_wall/60:.1f}min)")
    print(f"\n  Wave 1 timeouts: {total_timeout}/{total_attempts} ({total_timeout*100/total_attempts:.0f}%)")

    # Impact on total runtime
    total_problem_time = sum(p.wall_time for p in problems if p.wall_time)
    print(f"\n  Total run time (problems): {total_problem_time:.0f}s ({total_problem_time/60:.1f}min)")
    print(f"  Wave 1 overhead: ~{total_wall:.0f}s ({total_wall/60:.1f}min)")
    print(f"  Wave 1 as % of total: {total_wall*100/total_problem_time:.1f}%")
    print(f"  Without Wave 1: ~{(total_problem_time - total_wall)/60:.0f}min")

    # Notes injected vs not
    notes_yes = {pid: d for pid, d in problem_wave1.items() if d['notes_injected'] is True}
    notes_no = {pid: d for pid, d in problem_wave1.items() if d['notes_injected'] is False}

    print(f"\n  {'─'*72}")
    print(f"  NOTES INJECTED vs NOT")
    print(f"  {'─'*72}")
    print(f"  With notes: {len(notes_yes)} problems")
    print(f"  Without notes: {len(notes_no)} problems")

    # Correctness comparison
    pid_to_problem = {p.problem_id: p for p in problems}
    if notes_yes:
        correct_with = sum(1 for pid in notes_yes if pid in pid_to_problem and pid_to_problem[pid].correct)
        print(f"  With notes accuracy: {correct_with}/{len(notes_yes)} ({correct_with*100/len(notes_yes):.0f}%)")
    if notes_no:
        correct_without = sum(1 for pid in notes_no if pid in pid_to_problem and pid_to_problem[pid].correct)
        print(f"  Without notes accuracy: {correct_without}/{len(notes_no)} ({correct_without*100/len(notes_no):.0f}%)")

    # Per-problem detail
    print(f"\n  {'─'*72}")
    print(f"  PER-PROBLEM WAVE 1 DETAIL")
    print(f"  {'─'*72}")
    print(f"  {'PID':8s} {'W1 Wall':>8s} {'W1 Mean':>8s} {'Att':>4s} {'T/O':>4s} {'Notes':>6s} {'Correct':>8s}")
    print(f"  {'─'*8} {'─'*8} {'─'*8} {'─'*4} {'─'*4} {'─'*6} {'─'*8}")

    for p in problems:
        d = problem_wave1.get(p.problem_id)
        if d:
            notes = 'YES' if d['notes_injected'] else ('NO' if d['notes_injected'] is False else '?')
            correct = 'OK' if p.correct else 'WRONG'
            print(f"  {p.problem_id:8s} {d['wall_time']:7.1f}s {d['mean_time']:7.1f}s {d['n_attempts']:4d} {d['n_timeout']:4d} {notes:>6s} {correct:>8s}")

    # Time saved if we reduce Wave 1 budget
    print(f"\n  {'─'*72}")
    print(f"  WAVE 1 BUDGET REDUCTION SIMULATION")
    print(f"  {'─'*72}")
    for budget in [100, 80, 60, 40, 20]:
        # Simulate: wall time = min(actual_wall, budget)
        sim_wall = sum(min(d['wall_time'], budget) for d in problem_wave1.values())
        saved = total_wall - sim_wall
        print(f"  Budget {budget}s: wall={sim_wall:.0f}s ({sim_wall/60:.1f}min), saved={saved:.0f}s ({saved/60:.1f}min)")


if __name__ == '__main__':
    main()
