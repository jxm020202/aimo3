#!/usr/bin/env python3
"""
v33 Time Breakdown — Per-problem wall clock analysis with rerun detection.

Shows:
- Each problem ID, first-pass time, whether it was rerun, rerun time, total time
- Batch boundaries and cumulative elapsed time
- Summary: total first-pass time, total rerun time, problems rerun count, time accounting

Usage:
    python3 log_exploration/v33_time_breakdown.py output/v33/diagnostic.log
"""

import re
import sys
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProblemTiming:
    problem_id: str
    expected: Optional[int] = None
    predicted: Optional[int] = None
    correct: bool = False
    batch: str = ""
    budget_s: float = 0.0
    deadline_epoch: float = 0.0
    wall_time_s: float = 0.0  # Total time reported by STATUS line
    first_pass_votes: Optional[float] = None
    rerun: bool = False
    rerun_budget_s: float = 0.0
    rerun_votes_before: Optional[float] = None
    rerun_votes_after: Optional[float] = None
    num_attempts_first: int = 0
    num_attempts_rerun: int = 0
    num_attempts_total: int = 0
    # Computed from deadlines
    start_epoch: float = 0.0
    status_line_time_s: float = 0.0
    batch_elapsed_after: float = 0.0  # "Elapsed: Ns" line after this problem


def parse_v33_timing(logfile: str) -> tuple[list[ProblemTiming], dict]:
    """Parse v33 diagnostic log for per-problem timing with rerun details."""

    with open(logfile) as f:
        lines = f.readlines()

    problems = []
    current = None
    batches = {}
    current_batch = ""

    # Regex patterns
    re_batch = re.compile(r'BATCH: (.+?) \((\d+) problems\)')
    re_batch_complete = re.compile(r'BATCH COMPLETE: (.+)')
    re_problem = re.compile(r'\[\d+/\d+\] Problem (\w+) \| Expected: (\d+)')
    re_budget = re.compile(r'Budget: ([\d.]+) seconds \| Deadline: ([\d.]+)')
    re_final_answer = re.compile(r'Final Answer: (\S+) \(votes: ([\d.]+)\)')
    re_status = re.compile(r'STATUS: (CORRECT|WRONG) \| Predicted: (\d+) \| Expected: (\d+) \| Time: ([\d.]+)s')
    re_low_conf = re.compile(r'Low confidence \(([\d.]+) votes\)\. Rerunning with (\d+)s budget')
    re_rerun_complete = re.compile(r'Rerun complete: (\d+) new results, (\d+) total')
    re_elapsed = re.compile(r'Running: \d+/\d+ .* Elapsed: (\d+)s')
    re_batch_score = re.compile(r'Score: (\d+)/(\d+)')
    re_batch_time = re.compile(r'Time: (\d+)s')
    re_votes_line = re.compile(r'Votes: \{(.+?)\} \| Answers: (\d+)')

    final_answers_seen = 0  # Track multiple Final Answer lines per problem

    for i, line in enumerate(lines):
        line = line.rstrip('\n')

        # Batch start
        bm = re_batch.search(line)
        if bm:
            current_batch = bm.group(1)
            continue

        # Problem start
        pm = re_problem.search(line)
        if pm:
            if current:
                problems.append(current)
            current = ProblemTiming(
                problem_id=pm.group(1),
                expected=int(pm.group(2)),
                batch=current_batch,
            )
            final_answers_seen = 0
            continue

        # Budget / Deadline
        bud = re_budget.search(line)
        if bud and current:
            current.budget_s = float(bud.group(1))
            current.deadline_epoch = float(bud.group(2))
            current.start_epoch = current.deadline_epoch - current.budget_s
            continue

        # Final Answer (can appear multiple times: first pass, then after rerun)
        fa = re_final_answer.search(line)
        if fa and current:
            final_answers_seen += 1
            votes = float(fa.group(2))
            if final_answers_seen == 1:
                current.first_pass_votes = votes
            elif final_answers_seen == 2:
                # This is the post-rerun answer
                current.rerun_votes_after = votes
            continue

        # Low confidence rerun trigger
        lc = re_low_conf.search(line)
        if lc and current:
            current.rerun = True
            current.rerun_votes_before = float(lc.group(1))
            current.rerun_budget_s = float(lc.group(2))
            continue

        # Rerun complete
        rc = re_rerun_complete.search(line)
        if rc and current:
            current.num_attempts_rerun = int(rc.group(1))
            current.num_attempts_total = int(rc.group(2))
            current.num_attempts_first = current.num_attempts_total - current.num_attempts_rerun
            continue

        # STATUS line (total wall time)
        sm = re_status.search(line)
        if sm and current:
            current.correct = (sm.group(1) == 'CORRECT')
            current.predicted = int(sm.group(2))
            current.wall_time_s = float(sm.group(4))
            continue

        # Votes line (for attempt counts when no rerun)
        vm = re_votes_line.search(line)
        if vm and current and not current.rerun:
            current.num_attempts_total = int(vm.group(2))
            current.num_attempts_first = current.num_attempts_total
            continue

        # Elapsed line (after each problem completes)
        em = re_elapsed.search(line)
        if em and current:
            current.batch_elapsed_after = float(em.group(1))
            continue

    # Don't forget the last problem
    if current:
        problems.append(current)

    return problems, batches


def compute_inter_problem_gaps(problems: list[ProblemTiming]):
    """Use deadline epochs to compute actual elapsed times between problems."""
    for i, p in enumerate(problems):
        if i == 0:
            p._prev_end_epoch = p.start_epoch
        else:
            p._prev_end_epoch = problems[i - 1].start_epoch + problems[i - 1].wall_time_s


def print_report(problems: list[ProblemTiming]):
    total_wall = sum(p.wall_time_s for p in problems)
    rerun_problems = [p for p in problems if p.rerun]
    correct_problems = [p for p in problems if p.correct]

    # Header
    print("=" * 110)
    print("  v33 TIME BREAKDOWN — Per-Problem Analysis")
    print("=" * 110)
    print(f"\n  Total problems: {len(problems)}")
    print(f"  Total correct: {len(correct_problems)}/{len(problems)} ({len(correct_problems)/len(problems)*100:.1f}%)")
    print(f"  Total wall time (sum of STATUS times): {total_wall:.0f}s ({total_wall/60:.1f} min)")
    print(f"  Final summary says: 8029s (133.8 min)")
    print()

    # Per-problem table
    print("  " + "-" * 106)
    print(f"  {'#':>3} {'ID':<8} {'Batch':<28} {'OK':>3} {'Wall':>6} {'Budget':>7} {'Util%':>6} {'1st Votes':>10} {'Rerun?':>7} {'Att':>4}")
    print("  " + "-" * 106)

    batch_subtotals = {}
    prev_batch = None

    for idx, p in enumerate(problems):
        # Batch separator
        if p.batch != prev_batch:
            if prev_batch is not None:
                # Print batch subtotal
                bt = batch_subtotals.get(prev_batch, [])
                bt_time = sum(x.wall_time_s for x in bt)
                bt_correct = sum(1 for x in bt if x.correct)
                print(f"  {'':>3} {'':8} {'── Subtotal':28} {'':>3} {bt_time:>5.0f}s {'':>7} {'':>6} {'':>10} {'':>7} {'':>4}")
                print()
            prev_batch = p.batch

        if p.batch not in batch_subtotals:
            batch_subtotals[p.batch] = []
        batch_subtotals[p.batch].append(p)

        ok = "Y" if p.correct else "N"
        util = (p.wall_time_s / p.budget_s * 100) if p.budget_s > 0 else 0
        first_votes = f"{p.first_pass_votes:.1f}" if p.first_pass_votes is not None else "-"
        rerun_str = "YES" if p.rerun else ""
        att_str = f"{p.num_attempts_total}" if p.num_attempts_total else "16"

        print(f"  {idx+1:>3} {p.problem_id:<8} {p.batch:<28} {ok:>3} {p.wall_time_s:>5.0f}s {p.budget_s:>6.0f}s {util:>5.1f}% {first_votes:>10} {rerun_str:>7} {att_str:>4}")

    # Final batch subtotal
    if prev_batch:
        bt = batch_subtotals.get(prev_batch, [])
        bt_time = sum(x.wall_time_s for x in bt)
        print(f"  {'':>3} {'':8} {'── Subtotal':28} {'':>3} {bt_time:>5.0f}s")

    print("  " + "-" * 106)
    print(f"  {'':>3} {'TOTAL':<8} {'':28} {'':>3} {total_wall:>5.0f}s")

    # Rerun details
    print("\n" + "=" * 110)
    print("  RERUN ANALYSIS")
    print("=" * 110)
    print(f"\n  Problems that triggered reruns: {len(rerun_problems)}/{len(problems)}")
    print()

    if rerun_problems:
        print(f"  {'ID':<8} {'1st Votes':>10} {'Rerun Budget':>13} {'Post Votes':>11} {'Changed?':>9} {'Total Wall':>11} {'1st Att':>8} {'Re Att':>7} {'Tot Att':>8} {'OK':>3}")
        print("  " + "-" * 98)

        for p in rerun_problems:
            votes_before = f"{p.rerun_votes_before:.1f}" if p.rerun_votes_before is not None else "-"
            votes_after = f"{p.rerun_votes_after:.1f}" if p.rerun_votes_after is not None else "-"
            # Did the rerun change the answer?
            changed = "?"
            if p.first_pass_votes is not None and p.rerun_votes_after is not None:
                changed = "YES" if abs(p.rerun_votes_after - p.first_pass_votes) > 0.5 else "no"
            ok = "Y" if p.correct else "N"

            print(f"  {p.problem_id:<8} {votes_before:>10} {p.rerun_budget_s:>12.0f}s {votes_after:>11} {changed:>9} {p.wall_time_s:>10.0f}s {p.num_attempts_first:>8} {p.num_attempts_rerun:>7} {p.num_attempts_total:>8} {ok:>3}")

        total_rerun_wall = sum(p.wall_time_s for p in rerun_problems)
        rerun_correct = sum(1 for p in rerun_problems if p.correct)
        print(f"\n  Total wall time for rerun problems: {total_rerun_wall:.0f}s ({total_rerun_wall/60:.1f} min)")
        print(f"  Rerun problems correct: {rerun_correct}/{len(rerun_problems)}")
    else:
        print("  No reruns detected.")

    # Time accounting
    print("\n" + "=" * 110)
    print("  TIME ACCOUNTING")
    print("=" * 110)

    # Compute estimated rerun overhead
    # The wall_time_s in STATUS includes both first-pass and rerun
    # For rerun problems, budget is 400s each pass, so max 800s total
    # But we can estimate: non-rerun problems have ~400s max
    # Rerun problems that hit ~800s spent ~400s on each pass

    non_rerun_time = sum(p.wall_time_s for p in problems if not p.rerun)
    rerun_total_time = sum(p.wall_time_s for p in problems if p.rerun)

    # For rerun problems, estimate first-pass vs rerun time
    # If budget is 400s and total wall is ~800s, roughly half was each
    # But for problems that finished faster in first pass, rerun adds ~400s

    print(f"\n  Non-rerun problems: {len(problems) - len(rerun_problems)}")
    print(f"  Non-rerun total time: {non_rerun_time:.0f}s ({non_rerun_time/60:.1f} min)")
    print(f"\n  Rerun problems: {len(rerun_problems)}")
    print(f"  Rerun total time: {rerun_total_time:.0f}s ({rerun_total_time/60:.1f} min)")

    # Estimated first-pass time for rerun problems
    # Since they each get 400s budget for first pass, and then rerun with another 400s:
    # total_wall = first_pass_time + rerun_time
    # We know each pass has 400s budget, and reruns always do 16 new attempts
    # We can estimate first pass used close to budget since low confidence usually means
    # the model tried hard (many attempts used full time)
    # But actually for some problems first pass might be quick if all 16 attempts finish fast

    print(f"\n  Sum of all problem wall times: {total_wall:.0f}s ({total_wall/60:.1f} min)")
    print(f"  Reported total time: 8029s (133.8 min)")
    print(f"  Difference (overhead/gaps): {8029 - total_wall:.0f}s ({(8029 - total_wall)/60:.1f} min)")

    # Sequential time analysis using Elapsed markers
    # The Elapsed field shows cumulative time within each batch
    print("\n  Batch-level time from 'Elapsed' markers:")
    batch_elapsed = {}
    for p in problems:
        if p.batch not in batch_elapsed:
            batch_elapsed[p.batch] = {'first_elapsed': 0, 'last_elapsed': 0, 'count': 0}
        if batch_elapsed[p.batch]['count'] == 0:
            batch_elapsed[p.batch]['first_elapsed'] = p.batch_elapsed_after
        batch_elapsed[p.batch]['last_elapsed'] = p.batch_elapsed_after
        batch_elapsed[p.batch]['count'] += 1

    total_batch_elapsed = 0
    for batch_name, info in batch_elapsed.items():
        batch_time = info['last_elapsed']
        total_batch_elapsed += batch_time
        probs_in_batch = [p for p in problems if p.batch == batch_name]
        sum_wall = sum(p.wall_time_s for p in probs_in_batch)
        print(f"    {batch_name}: {info['count']} problems, batch elapsed={batch_time}s ({batch_time/60:.1f} min), sum(wall)={sum_wall:.0f}s")

    # Key insight: problems are SEQUENTIAL (one at a time)
    # Elapsed is cumulative within each batch
    print(f"\n  Total batch elapsed times: {total_batch_elapsed}s ({total_batch_elapsed/60:.1f} min)")

    # Per-batch problem timing using consecutive Elapsed values
    print("\n" + "=" * 110)
    print("  SEQUENTIAL TIMING (from Elapsed deltas)")
    print("=" * 110)
    print()
    print(f"  {'#':>3} {'ID':<8} {'Batch':<28} {'OK':>3} {'Status Time':>12} {'Elapsed After':>14} {'Delta':>7} {'Rerun':>6}")
    print("  " + "-" * 90)

    prev_elapsed = 0
    prev_batch = None
    for idx, p in enumerate(problems):
        if p.batch != prev_batch:
            prev_elapsed = 0
            prev_batch = p.batch
            if idx > 0:
                print()

        delta = p.batch_elapsed_after - prev_elapsed if p.batch_elapsed_after > 0 else 0
        ok = "Y" if p.correct else "N"
        rerun_str = "RE" if p.rerun else ""
        print(f"  {idx+1:>3} {p.problem_id:<8} {p.batch:<28} {ok:>3} {p.wall_time_s:>11.0f}s {p.batch_elapsed_after:>13.0f}s {delta:>6.0f}s {rerun_str:>6}")
        prev_elapsed = p.batch_elapsed_after

    # Why only 19 problems?
    print("\n" + "=" * 110)
    print("  WHY ONLY 19 PROBLEMS?")
    print("=" * 110)
    print(f"""
  The log shows:
  - Tier 0:   2 problems (sanity check) → ran both
  - Tier 0.5: 2 problems (86e8e5 x2)   → ran both  (historical hard, run twice)
  - Tier 1:  15 problems                → ran all 15
  - Tier 2:   0 problems                → NONE queued

  Total: 2 + 2 + 15 + 0 = 19 problems

  The Tier 2 batch says "0 unseen problems" — the TEST_TIER=2 setting caused
  tier selection logic to queue 0 Tier 2 problems. The manifest lists 31 unseen
  Tier 2 problems but none were actually queued for processing.

  Time breakdown:
  - Tier 0 batch time:   {sum(p.wall_time_s for p in problems if p.batch.startswith('TIER 0 —')):.0f}s ({sum(p.wall_time_s for p in problems if p.batch.startswith('TIER 0 —'))/60:.1f} min)
  - Tier 0.5 batch time: {sum(p.wall_time_s for p in problems if '0.5' in p.batch):.0f}s ({sum(p.wall_time_s for p in problems if '0.5' in p.batch)/60:.1f} min)
  - Tier 1 batch time:   {sum(p.wall_time_s for p in problems if p.batch.startswith('TIER 1')):.0f}s ({sum(p.wall_time_s for p in problems if p.batch.startswith('TIER 1'))/60:.1f} min)

  6 of 19 problems triggered reruns, adding ~400s each.

  Rerun problems that hit ~800s wall time:
""")

    for p in rerun_problems:
        print(f"    {p.problem_id}: {p.wall_time_s:.0f}s (budget was {p.budget_s:.0f}s, rerun added {p.rerun_budget_s:.0f}s)")

    # Time budget analysis
    non_rerun_wall = sum(p.wall_time_s for p in problems if not p.rerun)
    rerun_wall = sum(p.wall_time_s for p in rerun_problems)
    # If no reruns, estimate how fast things would have been
    # Rerun problems without rerun would have used ~budget time or less
    # Approximate: first-pass took roughly (wall_time - ~400) for rerun problems
    est_no_rerun = 0
    for p in rerun_problems:
        # Very rough: if wall_time ~800, first pass ~400
        # If wall_time < budget, no rerun would have been same
        est_first_pass = min(p.wall_time_s, p.budget_s)  # Can't be more than budget
        est_no_rerun += est_first_pass

    print(f"\n  Estimated time WITHOUT reruns: {non_rerun_wall + est_no_rerun:.0f}s ({(non_rerun_wall + est_no_rerun)/60:.1f} min)")
    print(f"  Actual time WITH reruns:       {total_wall:.0f}s ({total_wall/60:.1f} min)")
    print(f"  Estimated rerun overhead:      {total_wall - non_rerun_wall - est_no_rerun:.0f}s ({(total_wall - non_rerun_wall - est_no_rerun)/60:.1f} min)")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 log_exploration/v33_time_breakdown.py <diagnostic.log>")
        sys.exit(1)

    logfile = sys.argv[1]
    problems, batches = parse_v33_timing(logfile)
    print_report(problems)


if __name__ == '__main__':
    main()
