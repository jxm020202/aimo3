#!/usr/bin/env python3
"""
AIMO3 Deep Temperature Analysis
=================================
Goes beyond flat stats to analyze per-problem, per-temp behavior:
unique solvers, outvoted correct answers, near-misses, diversity contribution,
and simulated schedule comparison.

Usage:
    python log_exploration/temperature_deep_analysis.py <logfile> [--output <file>]

Outputs: Full markdown report (stdout or --output file)
"""

import sys
import os
from collections import defaultdict, Counter
from io import StringIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def bucket_temp(t):
    if t is None:
        return None
    return round(t, 1)


def deduplicate_problems(problems):
    """Merge dual-run entries: combine attempts from all runs of the same problem ID."""
    by_pid = defaultdict(list)
    for p in problems:
        by_pid[p.problem_id].append(p)

    merged = []
    for pid, entries in by_pid.items():
        # Use first entry as base, combine all attempts
        base = entries[0]
        all_attempts = []
        for e in entries:
            all_attempts.extend(e.attempts)
        # Determine if ANY run was correct
        any_correct = any(e.correct for e in entries)
        # Build merged problem
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
        # Merge votes
        merged_votes = Counter()
        for e in entries:
            for ans, cnt in e.votes.items():
                merged_votes[ans] += cnt
        m.votes = dict(merged_votes)
        merged.append(m)
    return sorted(merged, key=lambda p: p.problem_id)


def run_analysis(logfile, output_file=None):
    problems_raw = parse_log(logfile)
    problems = deduplicate_problems(problems_raw)

    out = StringIO()

    def pr(*args, **kwargs):
        print(*args, file=out, **kwargs)

    temps_all = set()
    for p in problems:
        for a in p.attempts:
            t = bucket_temp(a.temperature)
            if t is not None:
                temps_all.add(t)
    temps_sorted = sorted(temps_all)

    total_problems = len(problems)
    correct_problems = [p for p in problems if p.correct]
    wrong_problems = [p for p in problems if not p.correct]
    total_correct = len(correct_problems)
    total_wrong = len(wrong_problems)

    pr("# Deep Temperature Analysis — v23")
    pr()
    pr(f"**Log**: `{logfile}`")
    pr(f"**Problems**: {total_problems} ({total_correct} correct, {total_wrong} wrong)")
    pr(f"**Temperature schedule**: {temps_sorted}")
    pr(f"**Attempts per problem**: 16 (across dual-runs: up to 32)")
    pr()

    # ─────────────────────────────────────────────────────────────────────
    # 1. PER-TEMP ACCURACY ON HARD PROBLEMS
    # ─────────────────────────────────────────────────────────────────────
    pr("## 1. Per-Temp Accuracy on HARD Problems")
    pr()
    pr("Hard = overall result was WRONG or had >70% None rate.")
    pr()

    # Identify hard problems
    hard_pids = set()
    for p in problems:
        none_rate = sum(1 for a in p.attempts if a.is_none) / max(len(p.attempts), 1)
        if not p.correct or none_rate > 0.70:
            hard_pids.add(p.problem_id)

    hard_problems = [p for p in problems if p.problem_id in hard_pids]

    pr(f"Hard problems identified: {len(hard_problems)} / {total_problems}")
    pr()
    pr("| Temp | Attempts | Correct | Wrong | None | Accuracy% | None% |")
    pr("|------|----------|---------|-------|------|-----------|-------|")

    for t in temps_sorted:
        total = correct = wrong = nones = 0
        for p in hard_problems:
            for a in p.attempts:
                if bucket_temp(a.temperature) == t:
                    total += 1
                    if a.answer is not None and a.answer == p.expected:
                        correct += 1
                    elif a.answer is not None:
                        wrong += 1
                    else:
                        nones += 1
        non_none = total - nones
        acc = (correct / non_none * 100) if non_none > 0 else 0.0
        none_pct = (nones / total * 100) if total > 0 else 0.0
        pr(f"| {t:.1f} | {total} | {correct} | {wrong} | {nones} | {acc:.1f} | {none_pct:.1f} |")
    pr()

    # ─────────────────────────────────────────────────────────────────────
    # 2. CORRECT-BUT-OUTVOTED MATRIX
    # ─────────────────────────────────────────────────────────────────────
    pr("## 2. Correct-But-Outvoted Matrix (Wrong Problems)")
    pr()
    pr("For each wrong problem: which temps found the correct answer?")
    pr()

    # Header
    temp_hdrs = " | ".join(f"{t:.1f}" for t in temps_sorted)
    pr(f"| Problem | Expected | Predicted | {temp_hdrs} | Total Correct |")
    sep = " | ".join("---" for _ in temps_sorted)
    pr(f"|---------|----------|-----------|{sep}|---------------|")

    for p in sorted(wrong_problems, key=lambda x: x.problem_id):
        cells = []
        total_corr = 0
        for t in temps_sorted:
            c = 0
            n = 0
            none_c = 0
            for a in p.attempts:
                if bucket_temp(a.temperature) == t:
                    n += 1
                    if a.answer is not None and a.answer == p.expected:
                        c += 1
                    elif a.is_none:
                        none_c += 1
            total_corr += c
            if n == 0:
                cells.append("-")
            elif c > 0:
                cells.append(f"**{c}/{n}**")
            elif none_c == n:
                cells.append(f"N/{n}")
            else:
                cells.append(f"0/{n}")
        cell_str = " | ".join(cells)
        exp = p.expected if p.expected is not None else "?"
        pred = p.predicted if p.predicted is not None else "?"
        pr(f"| {p.problem_id} | {exp} | {pred} | {cell_str} | {total_corr} |")

    pr()
    pr("Legend: **bold** = found correct answer. `N/x` = all None. `0/x` = answered but wrong.")
    pr()

    # ─────────────────────────────────────────────────────────────────────
    # 3. UNIQUE SOLVERS
    # ─────────────────────────────────────────────────────────────────────
    pr("## 3. Unique Solvers")
    pr()
    pr("Problems where ONLY one specific temp found the correct answer (no other temp did).")
    pr()

    # Build: for each problem, which temps got at least one correct?
    prob_correct_temps = {}
    for p in problems:
        correct_temps = set()
        for a in p.attempts:
            t = bucket_temp(a.temperature)
            if t is not None and a.answer is not None and a.answer == p.expected:
                correct_temps.add(t)
        prob_correct_temps[p.problem_id] = correct_temps

    unique_by_temp = defaultdict(list)
    for pid, temps_set in prob_correct_temps.items():
        if len(temps_set) == 1:
            the_temp = list(temps_set)[0]
            p = next(pp for pp in problems if pp.problem_id == pid)
            unique_by_temp[the_temp].append(p)

    any_unique = False
    for t in temps_sorted:
        pids = unique_by_temp.get(t, [])
        if pids:
            any_unique = True
            pr(f"**Temp {t:.1f}**: {len(pids)} unique solves")
            for p in pids:
                status = "CORRECT overall" if p.correct else "WRONG overall (outvoted!)"
                pr(f"  - `{p.problem_id}` (expected={p.expected}) — {status}")
            pr()

    if not any_unique:
        pr("No problems with unique-temperature-only solves.")
        pr()

    # Summary
    pr("**Unique solver summary:**")
    pr()
    pr("| Temp | Unique Solves | Of Which Outvoted |")
    pr("|------|---------------|-------------------|")
    for t in temps_sorted:
        pids = unique_by_temp.get(t, [])
        outvoted = sum(1 for p in pids if not p.correct)
        pr(f"| {t:.1f} | {len(pids)} | {outvoted} |")
    pr()

    # ─────────────────────────────────────────────────────────────────────
    # 4. NEAR-MISS BY TEMP
    # ─────────────────────────────────────────────────────────────────────
    pr("## 4. Near-Miss Analysis by Temperature")
    pr()
    pr("Problems where predicted is off-by-small (<=5). Which temps got exact vs near-miss?")
    pr()

    near_miss_problems = []
    for p in wrong_problems:
        if p.predicted is not None and p.expected is not None:
            diff = abs(p.predicted - p.expected)
            if diff <= 50:
                near_miss_problems.append(p)

    if not near_miss_problems:
        pr("No near-miss problems found (all diffs > 50).")
        pr()
    else:
        for p in sorted(near_miss_problems, key=lambda x: x.problem_id):
            pr(f"### `{p.problem_id}` — Expected: {p.expected}, Predicted: {p.predicted} (diff={abs(p.predicted - p.expected)})")
            pr()

            # Collect all answers by temp
            for t in temps_sorted:
                answers = []
                for a in p.attempts:
                    if bucket_temp(a.temperature) == t:
                        if a.answer is not None:
                            diff = abs(a.answer - p.expected)
                            tag = "EXACT" if diff == 0 else f"off-by-{diff}"
                            answers.append(f"{a.answer} ({tag})")
                        else:
                            answers.append("None")
                if answers:
                    pr(f"- **Temp {t:.1f}**: {', '.join(answers)}")
            pr()

    # ─────────────────────────────────────────────────────────────────────
    # 5. FIRST-CORRECT BY TEMP
    # ─────────────────────────────────────────────────────────────────────
    pr("## 5. First-Correct by Temperature")
    pr()
    pr("For each correct problem: which temp FIRST found the correct answer?")
    pr()

    first_correct_temp = Counter()
    first_correct_details = []
    for p in problems:
        if not any(a.answer is not None and a.answer == p.expected for a in p.attempts):
            continue
        # Find first correct attempt by attempt_num
        first = None
        for a in sorted(p.attempts, key=lambda x: x.attempt_num):
            if a.answer is not None and a.answer == p.expected:
                first = a
                break
        if first:
            t = bucket_temp(first.temperature)
            if t is not None:
                first_correct_temp[t] += 1
                first_correct_details.append((p.problem_id, t, first.attempt_num))

    pr("| Temp | Times First-Correct | Percentage |")
    pr("|------|---------------------|------------|")
    total_first = sum(first_correct_temp.values())
    for t in temps_sorted:
        cnt = first_correct_temp.get(t, 0)
        pct = (cnt / total_first * 100) if total_first > 0 else 0.0
        pr(f"| {t:.1f} | {cnt} | {pct:.1f}% |")
    pr()

    pr("**Interpretation**: Lower temps run first in the schedule (attempt 1 is temp=0.1).")
    pr("First-correct reflects both schedule position AND inherent accuracy.")
    pr()

    # Show breakdown by attempt number
    pr("First-correct by attempt number:")
    pr()
    attempt_to_temp = {}
    # Typical v23 schedule: [0.1, 0.3, 0.3, 0.3, 0.3, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.7, 0.7, 0.7, 0.7, 0.9]
    for p_id, t, att_num in sorted(first_correct_details, key=lambda x: x[2]):
        attempt_to_temp.setdefault(att_num, Counter())[t] += 1

    pr("| Attempt# | Temp | Count |")
    pr("|----------|------|-------|")
    for att_num in sorted(attempt_to_temp.keys()):
        for t, cnt in sorted(attempt_to_temp[att_num].items()):
            pr(f"| {att_num} | {t:.1f} | {cnt} |")
    pr()

    # ─────────────────────────────────────────────────────────────────────
    # 6. DIVERSITY CONTRIBUTION
    # ─────────────────────────────────────────────────────────────────────
    pr("## 6. Diversity Contribution")
    pr()
    pr("For each temp: how many unique correct problem-answers does it contribute")
    pr("that would NOT exist with just temp=0.5?")
    pr()

    # Problems solvable by 0.5
    solved_by_05 = set()
    for p in problems:
        for a in p.attempts:
            if bucket_temp(a.temperature) == 0.5 and a.answer is not None and a.answer == p.expected:
                solved_by_05.add(p.problem_id)
                break

    pr(f"Problems solved by temp=0.5 alone: {len(solved_by_05)}")
    pr()

    pr("| Temp | Problems Solved | Unique vs 0.5 | Marginal Value |")
    pr("|------|-----------------|---------------|----------------|")

    for t in temps_sorted:
        solved_by_t = set()
        for p in problems:
            for a in p.attempts:
                if bucket_temp(a.temperature) == t and a.answer is not None and a.answer == p.expected:
                    solved_by_t.add(p.problem_id)
                    break
        unique = solved_by_t - solved_by_05
        pr(f"| {t:.1f} | {len(solved_by_t)} | {len(unique)} | {sorted(unique) if unique else 'none'} |")
    pr()

    # Also check: what does the UNION of all non-0.5 temps add?
    solved_by_non_05 = set()
    for p in problems:
        for a in p.attempts:
            t = bucket_temp(a.temperature)
            if t is not None and t != 0.5 and a.answer is not None and a.answer == p.expected:
                solved_by_non_05.add(p.problem_id)
                break
    union_extra = solved_by_non_05 - solved_by_05
    pr(f"**Union of all non-0.5 temps adds {len(union_extra)} problems beyond 0.5**: {sorted(union_extra)}")
    pr()

    # ─────────────────────────────────────────────────────────────────────
    # 7. SIMULATED SCHEDULES
    # ─────────────────────────────────────────────────────────────────────
    pr("## 7. Simulated Schedules")
    pr()
    pr("We simulate different temperature schedules by subsetting available attempts.")
    pr("For each schedule, we take up to N attempts at each temp from the available pool,")
    pr("then majority-vote to determine the answer.")
    pr()

    schedules = {
        "Flat 0.5 x16":             {0.5: 16},
        "Flat 0.3 x16":             {0.3: 16},
        "0.3x8 + 0.5x8":           {0.3: 8, 0.5: 8},
        "0.1x2 + 0.3x6 + 0.5x8":  {0.1: 2, 0.3: 6, 0.5: 8},
        "0.3x6 + 0.5x6 + 0.7x4":  {0.3: 6, 0.5: 6, 0.7: 4},
        "Current [0.1,0.3x4,0.5x6,0.7x4,0.9]": {0.1: 1, 0.3: 4, 0.5: 6, 0.7: 4, 0.9: 1},
        "Heavy low: 0.1x4 + 0.3x8 + 0.5x4": {0.1: 4, 0.3: 8, 0.5: 4},
        "Conservative: 0.1x2 + 0.3x8 + 0.5x6": {0.1: 2, 0.3: 8, 0.5: 6},
    }

    def simulate_schedule(problems, schedule):
        """Simulate a schedule: subset attempts, majority vote, return score."""
        correct_count = 0
        details = []
        for p in problems:
            # Collect attempts by temp
            attempts_by_temp = defaultdict(list)
            for a in p.attempts:
                t = bucket_temp(a.temperature)
                if t is not None:
                    attempts_by_temp[t].append(a)

            # Subset according to schedule
            selected = []
            for t, count in schedule.items():
                available = attempts_by_temp.get(t, [])
                selected.extend(available[:count])

            # Majority vote on non-None answers
            votes = Counter()
            for a in selected:
                if a.answer is not None:
                    votes[a.answer] += 1

            if votes:
                predicted = votes.most_common(1)[0][0]
                is_correct = (predicted == p.expected)
            else:
                predicted = None
                is_correct = False

            if is_correct:
                correct_count += 1
            details.append((p.problem_id, is_correct, predicted, p.expected))

        return correct_count, details

    pr("| Schedule | Score | Correct | Wrong | Delta vs Current |")
    pr("|----------|-------|---------|-------|------------------|")

    current_key = "Current [0.1,0.3x4,0.5x6,0.7x4,0.9]"
    current_score = None
    schedule_scores = {}

    for name, sched in schedules.items():
        score, details = simulate_schedule(problems, sched)
        schedule_scores[name] = (score, details)
        if name == current_key:
            current_score = score

    for name, (score, details) in schedule_scores.items():
        delta = score - current_score if current_score is not None else 0
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        pr(f"| {name} | **{score}/{total_problems}** | {score} | {total_problems - score} | {delta_str} |")
    pr()

    # Show which problems differ between schedules
    pr("### Schedule Comparison Details")
    pr()
    pr("Problems where schedules DISAGREE (correct in one, wrong in another):")
    pr()

    # Compare each schedule to current
    _, current_details = schedule_scores[current_key]
    current_correct_pids = set(pid for pid, ok, _, _ in current_details if ok)

    for name, (score, details) in schedule_scores.items():
        if name == current_key:
            continue
        other_correct_pids = set(pid for pid, ok, _, _ in details if ok)
        gained = other_correct_pids - current_correct_pids
        lost = current_correct_pids - other_correct_pids
        if gained or lost:
            pr(f"**{name}** vs Current:")
            if gained:
                gained_details = [(pid, next((d[2], d[3]) for d in details if d[0] == pid)) for pid in sorted(gained)]
                for pid, (pred, exp) in gained_details:
                    pr(f"  - GAINED: `{pid}` (expected={exp})")
            if lost:
                lost_details = [(pid, next((d[2], d[3]) for d in details if d[0] == pid)) for pid in sorted(lost)]
                for pid, (pred, exp) in lost_details:
                    pr(f"  - LOST: `{pid}` (expected={exp})")
            pr()

    # ─────────────────────────────────────────────────────────────────────
    # 8. ERROR RATE BY TEMP
    # ─────────────────────────────────────────────────────────────────────
    pr("## 8. Error Rate by Temperature")
    pr()
    pr("Which temps produce the most code execution errors? Does low temp = cleaner code?")
    pr()

    pr("| Temp | Attempts | Total Errors | Avg Errors | Error-Free% | Correct When Error-Free | Correct When Errors |")
    pr("|------|----------|--------------|------------|-------------|------------------------|---------------------|")

    for t in temps_sorted:
        total = 0
        total_errors = 0
        error_free = 0
        correct_ef = 0  # correct when error-free
        correct_we = 0  # correct when has errors
        has_errors = 0

        for p in problems:
            for a in p.attempts:
                if bucket_temp(a.temperature) == t:
                    total += 1
                    total_errors += a.errors
                    is_correct = (a.answer is not None and a.answer == p.expected)
                    if a.errors == 0:
                        error_free += 1
                        if is_correct:
                            correct_ef += 1
                    else:
                        has_errors += 1
                        if is_correct:
                            correct_we += 1

        ef_pct = (error_free / total * 100) if total > 0 else 0
        avg_err = total_errors / total if total > 0 else 0
        corr_ef_pct = (correct_ef / error_free * 100) if error_free > 0 else 0
        corr_we_pct = (correct_we / has_errors * 100) if has_errors > 0 else 0

        pr(f"| {t:.1f} | {total} | {total_errors} | {avg_err:.2f} | {ef_pct:.1f}% | {corr_ef_pct:.1f}% ({correct_ef}/{error_free}) | {corr_we_pct:.1f}% ({correct_we}/{has_errors}) |")
    pr()

    # Also break down error TYPES by temp
    pr("### Error Type Distribution by Temp")
    pr()

    import re
    error_types_by_temp = defaultdict(lambda: Counter())
    for p in problems:
        for a in p.attempts:
            t = bucket_temp(a.temperature)
            if t is None:
                continue
            for turn in a.turns:
                if turn.is_error and turn.output:
                    # Extract error type from traceback
                    err_match = re.search(r'(\w+Error|\w+Exception|Timeout|MemoryError)', turn.output)
                    if err_match:
                        error_types_by_temp[t][err_match.group(1)] += 1
                    else:
                        error_types_by_temp[t]['Other'] += 1

    # Get all error types
    all_err_types = set()
    for c in error_types_by_temp.values():
        all_err_types.update(c.keys())
    top_err_types = sorted(all_err_types, key=lambda e: sum(error_types_by_temp[t][e] for t in temps_sorted), reverse=True)[:8]

    if top_err_types:
        err_hdrs = " | ".join(top_err_types)
        pr(f"| Temp | {err_hdrs} |")
        err_sep = " | ".join("---" for _ in top_err_types)
        pr(f"|------|{err_sep}|")

        for t in temps_sorted:
            cells = [str(error_types_by_temp[t].get(e, 0)) for e in top_err_types]
            pr(f"| {t:.1f} | {' | '.join(cells)} |")
        pr()

    # ─────────────────────────────────────────────────────────────────────
    # 9. ADDITIONAL: PER-PROBLEM HEAT MAP (compact)
    # ─────────────────────────────────────────────────────────────────────
    pr("## 9. Full Problem x Temperature Heat Map")
    pr()
    pr("Compact view: for each problem and temp, shows `C`=correct, `W`=wrong, `N`=None, `.`=no attempt.")
    pr("Shaded row = overall WRONG.")
    pr()

    temp_hdrs = " | ".join(f"{t:.1f}" for t in temps_sorted)
    pr(f"| Problem | Exp | Result | {temp_hdrs} |")
    sep = " | ".join("---" for _ in temps_sorted)
    pr(f"|---------|-----|--------|{sep}|")

    for p in sorted(problems, key=lambda x: (x.correct, x.problem_id)):
        cells = []
        for t in temps_sorted:
            c_count = 0
            w_count = 0
            n_count = 0
            for a in p.attempts:
                if bucket_temp(a.temperature) == t:
                    if a.answer is not None and a.answer == p.expected:
                        c_count += 1
                    elif a.is_none:
                        n_count += 1
                    else:
                        w_count += 1
            if c_count + w_count + n_count == 0:
                cells.append(".")
            else:
                parts = []
                if c_count > 0:
                    parts.append(f"{c_count}C")
                if w_count > 0:
                    parts.append(f"{w_count}W")
                if n_count > 0:
                    parts.append(f"{n_count}N")
                cells.append("/".join(parts))

        result = "OK" if p.correct else "**WRONG**"
        cell_str = " | ".join(cells)
        pr(f"| {p.problem_id} | {p.expected} | {result} | {cell_str} |")
    pr()

    # ─────────────────────────────────────────────────────────────────────
    # 10. KEY FINDINGS
    # ─────────────────────────────────────────────────────────────────────
    pr("## 10. Key Findings & Recommendations")
    pr()

    # Best flat temp
    best_flat_score = 0
    best_flat_temp = None
    for t in temps_sorted:
        solved = set()
        for p in problems:
            for a in p.attempts:
                if bucket_temp(a.temperature) == t and a.answer is not None and a.answer == p.expected:
                    solved.add(p.problem_id)
                    break
        if len(solved) > best_flat_score:
            best_flat_score = len(solved)
            best_flat_temp = t

    # Current schedule score
    cs, _ = schedule_scores[current_key]

    pr(f"1. **Best single temperature**: {best_flat_temp} (solves {best_flat_score}/{total_problems})")
    pr(f"2. **Current schedule**: solves {cs}/{total_problems}")
    pr()

    # Analyze temp 0.9
    solved_only_09 = set()
    for p in problems:
        solved_by_others = False
        solved_by_09 = False
        for a in p.attempts:
            t = bucket_temp(a.temperature)
            if a.answer is not None and a.answer == p.expected:
                if t == 0.9:
                    solved_by_09 = True
                else:
                    solved_by_others = True
        if solved_by_09 and not solved_by_others:
            solved_only_09.add(p.problem_id)

    pr(f"3. **Temp 0.9 unique value**: solves {len(solved_only_09)} problems that no other temp solves → {'DROP' if len(solved_only_09) == 0 else 'KEEP'}")
    pr()

    solved_only_01 = set()
    for p in problems:
        solved_by_others = False
        solved_by_01 = False
        for a in p.attempts:
            t = bucket_temp(a.temperature)
            if a.answer is not None and a.answer == p.expected:
                if t == 0.1:
                    solved_by_01 = True
                else:
                    solved_by_others = True
        if solved_by_01 and not solved_by_others:
            solved_only_01.add(p.problem_id)

    pr(f"4. **Temp 0.1 unique value**: solves {len(solved_only_01)} problems that no other temp solves → {'DROP' if len(solved_only_01) == 0 else 'KEEP'}")
    if solved_only_01:
        for pid in sorted(solved_only_01):
            pr(f"   - `{pid}`")
    pr()

    # Schedule recommendation
    best_sched_name = max(schedule_scores.keys(), key=lambda k: schedule_scores[k][0])
    best_sched_score = schedule_scores[best_sched_name][0]
    pr(f"5. **Best simulated schedule**: \"{best_sched_name}\" → {best_sched_score}/{total_problems}")
    if best_sched_score > cs:
        pr(f"   This is +{best_sched_score - cs} over current schedule!")
    elif best_sched_score == cs:
        pr(f"   Ties with current. Simpler schedule may be preferable.")
    pr()

    # Outvoted potential
    outvoted_count = 0
    for p in wrong_problems:
        has_correct = any(a.answer is not None and a.answer == p.expected for a in p.attempts)
        if has_correct:
            outvoted_count += 1
    pr(f"6. **Outvoted correct answers**: {outvoted_count}/{total_wrong} wrong problems had the correct answer in at least one attempt")
    pr(f"   These represent the gap between \"can solve\" and \"does solve\" — voting/aggregation improvements matter here.")
    pr()

    # Near-miss
    near_miss_count = sum(1 for p in wrong_problems if p.predicted and p.expected and abs(p.predicted - p.expected) <= 5)
    pr(f"7. **Near-miss (off-by-<=5)**: {near_miss_count} wrong problems. These may benefit from answer refinement/self-check.")
    pr()

    report = out.getvalue()

    # Output
    if output_file:
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(report)
        print(f"Report saved to: {output_file}")

    print(report)
    return report


def main():
    if '--help' in sys.argv or len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0 if '--help' in sys.argv else 1)

    logfile = sys.argv[1]
    output_file = None

    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]

    if not os.path.exists(logfile):
        print(f"Error: {logfile} not found")
        sys.exit(1)

    run_analysis(logfile, output_file)


if __name__ == '__main__':
    main()
