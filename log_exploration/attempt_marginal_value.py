#!/usr/bin/env python3
"""
Attempt Marginal Value Analysis for AIMO3 Solver
==================================================
Answers: Did going from 8 to 16 attempts actually help?

Analyses:
1. First-correct-attempt distribution across 1-16
2. Problems whose first correct answer is in attempts 9-16 (would be lost with 8)
3. Minimum attempts needed to win majority vote for each correct problem
4. Simulated score at 8 vs 12 vs 16 attempts (truncation, not bootstrap)
5. Marginal value of each additional attempt

Usage:
    python3 log_exploration/attempt_marginal_value.py output/v23/diagnostic.log [--v22 output/v22/diagnostic.log] [-o output/v23/attempt_value_analysis.md]
"""

import sys
import os
import argparse
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


# ── Helpers ──────────────────────────────────────────────────────────────────

def deduplicate_problems(problems):
    """Deduplicate by problem_id, keeping the LAST occurrence (latest batch).
    Returns (deduped_list, dup_count)."""
    seen = {}
    for p in problems:
        if p.expected is None:
            continue
        seen[p.problem_id] = p  # last one wins
    return list(seen.values()), len(problems) - len(seen)


def mean(vals):
    return sum(vals) / len(vals) if vals else 0


def majority_vote(attempts, max_n=None):
    """Return the majority-vote winner from attempts 1..max_n (non-None only)."""
    votes = defaultdict(int)
    for a in attempts:
        if max_n is not None and a.attempt_num > max_n:
            continue
        if a.answer is not None:
            votes[a.answer] += 1
    if not votes:
        return None
    return max(votes, key=votes.get)


def vote_counts(attempts, max_n=None):
    """Return {answer: count} for attempts 1..max_n."""
    votes = defaultdict(int)
    for a in attempts:
        if max_n is not None and a.attempt_num > max_n:
            continue
        if a.answer is not None:
            votes[a.answer] += 1
    return dict(votes)


def sorted_attempts(problem):
    """Return attempts sorted by attempt_num."""
    return sorted(problem.attempts, key=lambda a: a.attempt_num)


# ── Analysis 1: First Correct Attempt Distribution ──────────────────────────

def analyze_first_correct(problems):
    """For each problem, at which attempt number was the correct answer first found?"""
    lines = []
    lines.append("## 1. First Correct Attempt Distribution")
    lines.append("")

    max_att = max((a.attempt_num for p in problems for a in p.attempts), default=16)
    total = sum(1 for p in problems if p.expected is not None)

    first_correct = {}  # pid -> attempt_num or None
    for p in problems:
        if p.expected is None:
            continue
        found_at = None
        for a in sorted_attempts(p):
            if a.answer == p.expected:
                found_at = a.attempt_num
                break
        first_correct[p.problem_id] = found_at

    # Distribution table
    dist = Counter(v for v in first_correct.values() if v is not None)
    never_found = sum(1 for v in first_correct.values() if v is None)

    lines.append(f"Total problems with expected answers: **{total}**")
    lines.append(f"Problems where correct answer was NEVER found: **{never_found}**")
    lines.append(f"Problems where correct answer was found at least once: **{total - never_found}**")
    lines.append("")
    lines.append("| Attempt # | First Found | % of Total | Cumulative | Cum % |")
    lines.append("|-----------|-------------|------------|------------|-------|")

    cumulative = 0
    for n in range(1, max_att + 1):
        count = dist.get(n, 0)
        cumulative += count
        pct = 100 * count / total if total else 0
        cum_pct = 100 * cumulative / total if total else 0
        bar = "#" * count
        lines.append(f"| {n:>9} | {count:>11} | {pct:>9.1f}% | {cumulative:>10} | {cum_pct:>4.1f}% | {bar}")

    lines.append(f"| {'Never':>9} | {never_found:>11} | {100*never_found/total if total else 0:>9.1f}% | | |")
    lines.append("")

    # Highlight: attempt 1 capture rate
    if dist.get(1, 0) > 0:
        found_total = total - never_found
        lines.append(f"**{dist[1]}/{found_total}** problems that have a correct answer find it on attempt 1 "
                      f"({100*dist[1]/found_total:.0f}%).")
    lines.append("")

    return lines, first_correct


# ── Analysis 2: Problems Only Found in Attempts 9-16 ────────────────────────

def analyze_9_16_exclusives(problems, first_correct):
    """Problems whose first correct answer is in attempts 9-16."""
    lines = []
    lines.append("## 2. Problems Requiring >8 Attempts to Find Correct Answer")
    lines.append("")

    late_finds = []
    for p in problems:
        if p.expected is None:
            continue
        fc = first_correct.get(p.problem_id)
        if fc is not None and fc > 8:
            late_finds.append((p, fc))

    if not late_finds:
        lines.append("**No problems** had their first correct answer in attempts 9-16.")
        lines.append("Going from 8 to 16 attempts did NOT discover any new correct answers.")
    else:
        lines.append(f"**{len(late_finds)} problem(s)** had their first correct answer in attempts 9-16:")
        lines.append("")
        lines.append("| Problem ID | First Correct At | Expected | Predicted (vote) | Final Correct? |")
        lines.append("|------------|-----------------|----------|-----------------|----------------|")
        for p, fc in late_finds:
            ok = "YES" if p.correct else "NO"
            lines.append(f"| {p.problem_id} | Attempt {fc} | {p.expected} | {p.predicted} | {ok} |")
        lines.append("")
        lines.append(f"These {len(late_finds)} problems would have had **zero** correct attempts with only 8 tries.")

    lines.append("")

    # Also: problems where correct answer EXISTS in 1-8 but also in 9-16
    bonus_problems = []
    for p in problems:
        if p.expected is None:
            continue
        fc = first_correct.get(p.problem_id)
        if fc is not None and fc <= 8:
            # Count correct in 9-16
            late_correct = sum(1 for a in p.attempts if a.attempt_num > 8 and a.answer == p.expected)
            early_correct = sum(1 for a in p.attempts if a.attempt_num <= 8 and a.answer == p.expected)
            if late_correct > 0:
                bonus_problems.append((p, early_correct, late_correct))

    if bonus_problems:
        lines.append(f"### Additional correct votes from attempts 9-16")
        lines.append(f"**{len(bonus_problems)} problems** had correct answers in BOTH halves:")
        lines.append("")
        lines.append("| Problem ID | Correct in 1-8 | Correct in 9-16 | Total Correct | Total Attempts |")
        lines.append("|------------|---------------|----------------|---------------|----------------|")
        for p, early, late in bonus_problems:
            total_att = len(p.attempts)
            lines.append(f"| {p.problem_id} | {early} | {late} | {early+late} | {total_att} |")
        lines.append("")

    return lines, late_finds


# ── Analysis 3: Minimum Attempts to Win Majority Vote ───────────────────────

def analyze_min_attempts_for_vote(problems):
    """For correct problems, what's the minimum N such that truncating to N attempts still gives the correct majority vote?"""
    lines = []
    lines.append("## 3. Minimum Attempts Needed to Win Majority Vote")
    lines.append("")
    lines.append("For each problem that is CORRECT in v23, what is the smallest N such that "
                 "majority vote over attempts 1..N gives the correct answer?")
    lines.append("")

    max_att = max((a.attempt_num for p in problems for a in p.attempts), default=16)
    total_with_expected = sum(1 for p in problems if p.expected is not None)

    min_n_data = []  # (problem_id, min_n, expected, vote_margin_at_min_n)
    would_lose_at = defaultdict(list)  # N -> problems that would be lost if capped at N

    for p in problems:
        if p.expected is None or not p.correct:
            continue

        # Find minimum N where majority vote = expected
        min_n = None
        for n in range(1, max_att + 1):
            winner = majority_vote(p.attempts, max_n=n)
            if winner == p.expected:
                min_n = n
                break

        if min_n is not None:
            # Also check: at what cap N does this problem STOP being correct?
            # (it might flip at some intermediate N then flip back)
            vc = vote_counts(p.attempts, max_n=min_n)
            margin = vc.get(p.expected, 0) - max((v for k, v in vc.items() if k != p.expected), default=0)
            min_n_data.append((p.problem_id, min_n, p.expected, margin))
        else:
            # Correct overall but never correct at any truncation? Shouldn't happen.
            min_n_data.append((p.problem_id, None, p.expected, 0))

    # Distribution of min_n
    min_n_dist = Counter(n for _, n, _, _ in min_n_data if n is not None)

    lines.append("| Min Attempts | Problems | Cum Problems | Notes |")
    lines.append("|-------------|----------|-------------|-------|")
    cumulative = 0
    for n in range(1, max_att + 1):
        count = min_n_dist.get(n, 0)
        cumulative += count
        note = ""
        if n == 8:
            note = "<-- v22 cap"
        elif n == 12:
            note = "<-- mid option"
        elif n == 16:
            note = "<-- v23 cap"
        lines.append(f"| {n:>11} | {count:>8} | {cumulative:>11} | {note} |")
    lines.append("")

    # Problems that REQUIRE >8 attempts to win the vote
    need_more_than_8 = [(pid, mn, exp, mg) for pid, mn, exp, mg in min_n_data if mn is not None and mn > 8]
    lines.append(f"**{len(need_more_than_8)} problem(s)** require more than 8 attempts to win the majority vote:")
    if need_more_than_8:
        lines.append("")
        lines.append("| Problem ID | Min N Needed | Expected | Margin at Min N |")
        lines.append("|------------|-------------|----------|-----------------|")
        for pid, mn, exp, mg in need_more_than_8:
            lines.append(f"| {pid} | {mn} | {exp} | +{mg} |")
    lines.append("")

    # Fragile problems: correct at 16, wrong at some smaller N
    lines.append("### Vote Stability Check")
    lines.append("Problems that are correct at N=16 but WRONG at some intermediate N:")
    lines.append("")

    fragile = []
    for p in problems:
        if p.expected is None or not p.correct:
            continue
        wrong_at = []
        for n in range(1, max_att + 1):
            winner = majority_vote(p.attempts, max_n=n)
            if winner is not None and winner != p.expected:
                wrong_at.append(n)
        if wrong_at:
            fragile.append((p.problem_id, wrong_at, p.expected))

    if fragile:
        lines.append("| Problem ID | Wrong at N= | Expected |")
        lines.append("|------------|------------|----------|")
        for pid, wrong_ns, exp in fragile:
            ns_str = ", ".join(str(n) for n in wrong_ns)
            lines.append(f"| {pid} | {ns_str} | {exp} |")
    else:
        lines.append("None found -- all correct problems maintain their vote lead at every truncation point.")
    lines.append("")

    return lines, min_n_data


# ── Analysis 4: Score Simulation at 8 / 12 / 16 ────────────────────────────

def analyze_score_simulation(problems):
    """Simulate score by truncating attempts at various caps."""
    lines = []
    lines.append("## 4. Score Simulation: 8 vs 12 vs 16 Attempts")
    lines.append("")
    lines.append("Using v23 data, truncate to first N attempts and compute majority vote score.")
    lines.append("")

    max_att = max((a.attempt_num for p in problems for a in p.attempts), default=16)
    total = sum(1 for p in problems if p.expected is not None)

    # Also simulate early stop at various thresholds
    lines.append("### Simple Truncation (no early stop)")
    lines.append("")
    lines.append("| Max Attempts | Score | Accuracy | Delta vs 16 | Delta vs 8 |")
    lines.append("|-------------|-------|----------|-------------|------------|")

    scores = {}
    problem_results = {}  # cap -> {pid: correct_bool}
    for cap in range(1, max_att + 1):
        score = 0
        results = {}
        for p in problems:
            if p.expected is None:
                continue
            winner = majority_vote(p.attempts, max_n=cap)
            is_correct = (winner == p.expected)
            if is_correct:
                score += 1
            results[p.problem_id] = is_correct
        scores[cap] = score
        problem_results[cap] = results

    score_at_8 = scores.get(8, 0)
    score_at_16 = scores.get(max_att, 0)

    for cap in range(1, max_att + 1):
        s = scores[cap]
        acc = 100 * s / total if total else 0
        d16 = s - score_at_16
        d8 = s - score_at_8
        d16_str = f"+{d16}" if d16 > 0 else str(d16)
        d8_str = f"+{d8}" if d8 > 0 else str(d8)
        highlight = ""
        if cap in (8, 12, 16):
            highlight = " **"
        lines.append(f"| {cap:>11}{highlight} | {s}/{total} | {acc:>7.1f}% | {d16_str:>11} | {d8_str:>10} |")

    lines.append("")

    # Key comparison
    lines.append(f"### Key Comparison")
    lines.append(f"- **8 attempts**: {scores.get(8,0)}/{total} ({100*scores.get(8,0)/total:.1f}%)")
    lines.append(f"- **12 attempts**: {scores.get(12,0)}/{total} ({100*scores.get(12,0)/total:.1f}%)")
    lines.append(f"- **16 attempts**: {scores.get(max_att,0)}/{total} ({100*scores.get(max_att,0)/total:.1f}%)")
    lines.append("")

    # Which problems flip between 8 and 16?
    if 8 in problem_results and max_att in problem_results:
        gained = []
        lost = []
        for pid in problem_results[8]:
            at_8 = problem_results[8][pid]
            at_16 = problem_results[max_att][pid]
            if not at_8 and at_16:
                gained.append(pid)
            elif at_8 and not at_16:
                lost.append(pid)

        lines.append(f"### Problems that CHANGE between 8 and 16 attempts")
        lines.append("")
        if gained:
            lines.append(f"**Gained** (wrong@8, correct@16): {len(gained)} problems")
            for pid in gained:
                p = next(p for p in problems if p.problem_id == pid)
                vc8 = vote_counts(p.attempts, max_n=8)
                vc16 = vote_counts(p.attempts, max_n=max_att)
                lines.append(f"  - `{pid}`: expected={p.expected}, votes@8={dict(vc8)}, votes@16={dict(vc16)}")
        else:
            lines.append("**No problems gained** by going from 8 to 16 attempts.")
        lines.append("")

        if lost:
            lines.append(f"**Lost** (correct@8, wrong@16): {len(lost)} problems")
            for pid in lost:
                p = next(p for p in problems if p.problem_id == pid)
                vc8 = vote_counts(p.attempts, max_n=8)
                vc16 = vote_counts(p.attempts, max_n=max_att)
                lines.append(f"  - `{pid}`: expected={p.expected}, votes@8={dict(vc8)}, votes@16={dict(vc16)}")
        else:
            lines.append("**No problems lost** by going from 8 to 16 attempts.")
        lines.append("")

    # Early stop simulation at ES=3,4,5 with various caps
    lines.append("### With Early Stop (ES=N matching answers triggers stop)")
    lines.append("")
    lines.append("| Cap | ES=3 | ES=4 | ES=5 | No ES |")
    lines.append("|-----|------|------|------|-------|")

    for cap in [8, 10, 12, 14, 16]:
        es_scores = {}
        for es_threshold in [3, 4, 5, None]:
            score = 0
            for p in problems:
                if p.expected is None:
                    continue
                # Simulate early stop: run attempts in order, stop when threshold reached
                seen_attempts = []
                votes = defaultdict(int)
                best_count = 0
                for a in sorted_attempts(p):
                    if a.attempt_num > cap:
                        break
                    seen_attempts.append(a)
                    if a.answer is not None:
                        votes[a.answer] += 1
                        if votes[a.answer] > best_count:
                            best_count = votes[a.answer]
                    if es_threshold is not None and best_count >= es_threshold:
                        break
                # Use majority vote on seen attempts (consistent tie-breaking)
                winner = majority_vote(seen_attempts)
                if winner == p.expected:
                    score += 1
            es_scores[es_threshold] = score
        lines.append(f"| {cap:>3} | {es_scores[3]}/{total} | {es_scores[4]}/{total} | {es_scores[5]}/{total} | {es_scores[None]}/{total} |")

    lines.append("")

    return lines, scores, problem_results


# ── Analysis 5: Marginal Value of Each Attempt ──────────────────────────────

def analyze_marginal_value(problems, scores, problem_results):
    """What's the marginal value of each additional attempt?"""
    lines = []
    lines.append("## 5. Marginal Value of Each Additional Attempt")
    lines.append("")
    lines.append("How many NEW problems does attempt N make correct (that attempts 1..N-1 could not)?")
    lines.append("")

    max_att = max((a.attempt_num for p in problems for a in p.attempts), default=16)
    total = sum(1 for p in problems if p.expected is not None)

    # Marginal = score(N) - score(N-1)
    lines.append("| Attempt N | Score at N | Marginal (+) | Marginal (-) | Net | Problems Flipped |")
    lines.append("|-----------|-----------|-------------|-------------|-----|-----------------|")

    prev_score = 0
    for n in range(1, max_att + 1):
        s = scores.get(n, 0)
        if n == 1:
            marginal = s
            lines.append(f"| {n:>9} | {s}/{total} | +{marginal} | -0 | +{marginal} | (baseline) |")
            prev_score = s
            continue

        # Find which problems flip
        gained_pids = []
        lost_pids = []
        for pid in problem_results.get(n, {}):
            curr = problem_results[n].get(pid, False)
            prev = problem_results[n - 1].get(pid, False)
            if curr and not prev:
                gained_pids.append(pid)
            elif not curr and prev:
                lost_pids.append(pid)

        net = len(gained_pids) - len(lost_pids)
        flipped = []
        for pid in gained_pids:
            flipped.append(f"+{pid}")
        for pid in lost_pids:
            flipped.append(f"-{pid}")

        flip_str = ", ".join(flipped) if flipped else "-"
        lines.append(f"| {n:>9} | {s}/{total} | +{len(gained_pids)} | -{len(lost_pids)} | {'+' if net >= 0 else ''}{net} | {flip_str} |")
        prev_score = s

    lines.append("")

    # Cumulative unique-problem analysis: which problems can ONLY be solved with N+ attempts?
    lines.append("### First-Ever-Solvable-At Analysis")
    lines.append("")
    lines.append("At which attempt cap N does each problem FIRST become solvable (majority vote correct)?")
    lines.append("")

    first_solvable = {}
    for p in problems:
        if p.expected is None:
            continue
        for n in range(1, max_att + 1):
            if problem_results.get(n, {}).get(p.problem_id, False):
                first_solvable[p.problem_id] = n
                break

    dist = Counter(first_solvable.values())
    never_solvable = total - len(first_solvable)

    lines.append("| First Solvable At | Count | Cumulative | Problem IDs |")
    lines.append("|-------------------|-------|------------|-------------|")
    cum = 0
    for n in range(1, max_att + 1):
        count = dist.get(n, 0)
        cum += count
        pids = [pid for pid, fs_n in first_solvable.items() if fs_n == n]
        pids_str = ", ".join(pids) if pids else "-"
        lines.append(f"| {n:>17} | {count:>5} | {cum:>10} | {pids_str} |")

    lines.append(f"| {'Never':>17} | {never_solvable:>5} | | |")
    lines.append("")

    # Summary: diminishing returns
    lines.append("### Diminishing Returns Summary")
    lines.append("")
    s1 = scores.get(1, 0)
    s4 = scores.get(4, 0)
    s8 = scores.get(8, 0)
    s12 = scores.get(12, 0)
    s16 = scores.get(max_att, 0)
    def _fmt_delta(v):
        return f"+{v}" if v >= 0 else str(v)

    lines.append(f"| Range | Attempts Used | Problems Gained | Per-Attempt Yield |")
    lines.append(f"|-------|--------------|----------------|-------------------|")
    lines.append(f"| 1-4   | 4            | {_fmt_delta(s4 - s1)} | {(s4 - s1) / 4:.2f}/attempt |")
    lines.append(f"| 5-8   | 4            | {_fmt_delta(s8 - s4)} | {(s8 - s4) / 4:.2f}/attempt |")
    lines.append(f"| 9-12  | 4            | {_fmt_delta(s12 - s8)} | {(s12 - s8) / 4:.2f}/attempt |")
    lines.append(f"| 13-16 | 4            | {_fmt_delta(s16 - s12)} | {(s16 - s12) / 4:.2f}/attempt |")
    lines.append(f"| **1-8 total** | 8 | **{s8}** | {s8/8:.2f}/attempt |")
    lines.append(f"| **9-16 total** | 8 | **{_fmt_delta(s16 - s8)}** | {(s16 - s8)/8:.2f}/attempt |")
    lines.append("")

    return lines


# ── v22 comparison (optional) ───────────────────────────────────────────────

def analyze_v22_comparison(v23_problems, v22_problems):
    """Compare v22 (8 attempts) vs v23 (16 attempts) on shared problems."""
    lines = []
    lines.append("## 6. v22 vs v23 Comparison (Shared Problems)")
    lines.append("")

    # Find shared problems
    v22_by_id = {p.problem_id: p for p in v22_problems if p.expected is not None}
    v23_by_id = {p.problem_id: p for p in v23_problems if p.expected is not None}
    shared = set(v22_by_id.keys()) & set(v23_by_id.keys())

    if not shared:
        lines.append("No shared problems between v22 and v23.")
        return lines

    lines.append(f"Shared problems: **{len(shared)}**")
    lines.append("")

    v22_correct = sum(1 for pid in shared if v22_by_id[pid].correct)
    v23_correct = sum(1 for pid in shared if v23_by_id[pid].correct)

    # v23 truncated to 8 attempts on shared problems
    v23_at_8 = 0
    for pid in shared:
        p = v23_by_id[pid]
        winner = majority_vote(p.attempts, max_n=8)
        if winner == p.expected:
            v23_at_8 += 1

    lines.append(f"| Run | Score (shared) | Config |")
    lines.append(f"|-----|---------------|--------|")
    lines.append(f"| v22 (actual, 8 att) | {v22_correct}/{len(shared)} | 8 att, ES=3, flat temp=0.5 |")
    lines.append(f"| v23 @ 8 att (simulated) | {v23_at_8}/{len(shared)} | 16 att truncated to 8, ES=5, temp schedule |")
    lines.append(f"| v23 (actual, 16 att) | {v23_correct}/{len(shared)} | 16 att, ES=5, temp schedule |")
    lines.append("")

    # Problem-by-problem diff
    flipped = []
    for pid in sorted(shared):
        v22_ok = v22_by_id[pid].correct
        v23_ok = v23_by_id[pid].correct
        v23_8_winner = majority_vote(v23_by_id[pid].attempts, max_n=8)
        v23_8_ok = (v23_8_winner == v23_by_id[pid].expected)

        if v22_ok != v23_ok or v22_ok != v23_8_ok:
            flipped.append((pid, v22_ok, v23_8_ok, v23_ok))

    if flipped:
        lines.append("### Problems that changed between runs")
        lines.append("")
        lines.append("| Problem ID | v22 (8att) | v23@8att | v23 (16att) | Expected |")
        lines.append("|------------|-----------|---------|------------|----------|")
        for pid, v22_ok, v23_8_ok, v23_ok in flipped:
            exp = v22_by_id[pid].expected
            lines.append(f"| {pid} | {'OK' if v22_ok else 'WRONG'} | {'OK' if v23_8_ok else 'WRONG'} | {'OK' if v23_ok else 'WRONG'} | {exp} |")
        lines.append("")
    else:
        lines.append("All shared problems have the same outcome across all three configurations.")
        lines.append("")

    return lines


# ── Executive Summary ───────────────────────────────────────────────────────

def write_executive_summary(problems, scores, first_correct, late_finds, min_n_data, problem_results):
    """Write the top-level summary."""
    lines = []
    max_att = max((a.attempt_num for p in problems for a in p.attempts), default=16)
    total = sum(1 for p in problems if p.expected is not None)

    lines.append("# Attempt Marginal Value Analysis: v23 (16 attempts)")
    lines.append("")
    lines.append("**Question**: Did going from 8 to 16 attempts per problem actually help?")
    lines.append("")
    lines.append(f"> Note: {total} unique problems after deduplication (last batch wins for problems "
                 "appearing in multiple batches: VAL BENCH, PRIORITY DEBUG, DOUBLE-RUN RETRY).")
    lines.append("")

    s8 = scores.get(8, 0)
    s16 = scores.get(max_att, 0)
    delta = s16 - s8

    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Score at 8 attempts | **{s8}/{total}** ({100*s8/total:.1f}%) |")
    lines.append(f"| Score at 16 attempts | **{s16}/{total}** ({100*s16/total:.1f}%) |")
    lines.append(f"| Net gain from attempts 9-16 | **{'+' if delta >= 0 else ''}{delta}** problems |")
    lines.append(f"| Problems first found correct in 9-16 | **{len(late_finds)}** |")

    # Problems requiring >8 to win vote
    need_more_8 = sum(1 for _, mn, _, _ in min_n_data if mn is not None and mn > 8)
    lines.append(f"| Problems requiring >8 att to win vote | **{need_more_8}** |")

    # Cost: rough time estimate
    time_1_8 = []
    time_9_16 = []
    for p in problems:
        for a in p.attempts:
            if a.attempt_num <= 8:
                time_1_8.append(a.time_s)
            else:
                time_9_16.append(a.time_s)
    total_time_9_16 = sum(time_9_16) / 60  # minutes
    lines.append(f"| Time spent on attempts 9-16 | **{total_time_9_16:.0f} min** |")
    if delta > 0:
        lines.append(f"| Cost per gained problem | **{total_time_9_16/delta:.0f} min** |")
    elif delta == 0:
        lines.append(f"| Cost per gained problem | **inf** (no gain) |")
    lines.append("")

    # Verdict
    lines.append("### Verdict")
    lines.append("")
    if delta > 2:
        lines.append(f"Going to 16 attempts was **clearly worth it**: +{delta} problems.")
    elif delta > 0:
        lines.append(f"Going to 16 attempts provided **marginal benefit**: +{delta} problem(s). "
                      f"The extra {total_time_9_16:.0f} minutes may not justify the gain.")
    elif delta == 0:
        lines.append(f"Going to 16 attempts provided **NO benefit** on the final score. "
                      f"The extra {total_time_9_16:.0f} minutes were entirely wasted.")
    else:
        lines.append(f"Going to 16 attempts was **actively harmful**: {delta} problems lost! "
                      f"More attempts added noise that outvoted correct answers.")
    lines.append("")

    # Optimal attempt count suggestion
    best_score = max(scores.values())
    best_caps = [n for n, s in scores.items() if s == best_score]
    min_optimal = min(best_caps)
    lines.append(f"**Optimal attempt count**: {min_optimal} attempts achieves the maximum score of {best_score}/{total}.")
    lines.append("")

    return lines


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Attempt marginal value analysis for AIMO3")
    parser.add_argument("logfile", help="Path to v23 diagnostic.log")
    parser.add_argument("--v22", help="Path to v22 diagnostic.log for comparison", default=None)
    parser.add_argument("-o", "--output", help="Output markdown file",
                        default="output/v23/attempt_value_analysis.md")
    args = parser.parse_args()

    if not os.path.exists(args.logfile):
        print(f"Error: File not found: {args.logfile}")
        sys.exit(1)

    print(f"Parsing {args.logfile}...")
    raw_problems = parse_log(args.logfile)
    print(f"Parsed {len(raw_problems)} problem instances.")

    # Deduplicate: some problems appear in multiple batches (VAL BENCH + DOUBLE-RUN RETRY).
    # Keep the LAST occurrence per problem_id (retries override originals).
    problems, dup_count = deduplicate_problems(raw_problems)
    print(f"After dedup: {len(problems)} unique problems ({dup_count} duplicates removed).")

    # Run all analyses
    all_lines = []

    # Executive summary placeholder (written after analyses)
    section1, first_correct = analyze_first_correct(problems)
    section2, late_finds = analyze_9_16_exclusives(problems, first_correct)
    section3, min_n_data = analyze_min_attempts_for_vote(problems)
    section4, scores, problem_results = analyze_score_simulation(problems)
    section5 = analyze_marginal_value(problems, scores, problem_results)

    # Executive summary (needs results from above)
    summary = write_executive_summary(problems, scores, first_correct, late_finds, min_n_data, problem_results)

    all_lines.extend(summary)
    all_lines.append("---")
    all_lines.append("")
    all_lines.extend(section1)
    all_lines.extend(section2)
    all_lines.extend(section3)
    all_lines.extend(section4)
    all_lines.extend(section5)

    # Optional v22 comparison
    if args.v22:
        if os.path.exists(args.v22):
            print(f"Parsing v22 log: {args.v22}...")
            v22_raw = parse_log(args.v22)
            v22_problems, v22_dups = deduplicate_problems(v22_raw)
            print(f"Parsed {len(v22_raw)} v22 instances, {len(v22_problems)} unique ({v22_dups} dups removed).")
            section6 = analyze_v22_comparison(problems, v22_problems)
            all_lines.extend(section6)
        else:
            print(f"Warning: v22 log not found: {args.v22}")

    # Write output
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    content = "\n".join(all_lines)

    with open(args.output, "w") as f:
        f.write(content)
    print(f"\nAnalysis written to: {args.output}")

    # Also print to stdout
    print("\n" + "=" * 80)
    print(content)


if __name__ == "__main__":
    main()
