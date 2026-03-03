#!/usr/bin/env python3
"""
Problem Ordering Analysis for AIMO3 v23
========================================
Analyzes the 17 wrong problems in the context of problem ordering:
- When were they solved (early/middle/late)?
- Were late problems more likely to fail?
- Did time pressure cause failures?
- Were Val Bench failures concentrated at the end?

Usage: python3 log_exploration/problem_ordering_analysis.py output/v23/diagnostic.log [--output output/v23/last_problems_analysis.md]
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


# ── 17 wrong problem IDs from v23 analysis ──────────────────────────────────
WRONG_IDS = {
    '86e8e5', '1ec970', '21fb4e', '23586c', '26bee3', '29714f', '3980cd',
    '3b88b3', '414a5b', '673b29', '89c921', '9010d9', 'a824c1', 'a9dbc8',
    'ae2add', 'aff75c', 'dbbfe8',
}

BUDGET_MINUTES = 300.0


def fmt_time(s):
    """Format seconds as Xm Ys or Xs."""
    if s >= 60:
        m = int(s // 60)
        sec = s - m * 60
        return f"{m}m {sec:.0f}s"
    return f"{s:.1f}s"


def fmt_min(s):
    """Format seconds as minutes with 1 decimal."""
    return f"{s / 60:.1f}"


def mean(vals):
    return sum(vals) / len(vals) if vals else 0


def median(vals):
    if not vals:
        return 0
    s = sorted(vals)
    n = len(s)
    if n % 2 == 0:
        return (s[n // 2 - 1] + s[n // 2]) / 2
    return s[n // 2]


def stdev(vals):
    if len(vals) < 2:
        return 0
    m = mean(vals)
    return (sum((x - m) ** 2 for x in vals) / (len(vals) - 1)) ** 0.5


def analyze(problems):
    """Run all ordering analyses and return markdown report."""
    lines = []

    def out(s=""):
        lines.append(s)

    # ── Build chronological order ────────────────────────────────────────────
    # Problems are in parse order = log order = chronological order
    cumulative_time = 0.0
    problem_order = []
    for i, p in enumerate(problems):
        start_time = cumulative_time
        end_time = cumulative_time + p.wall_time
        problem_order.append({
            'idx': i + 1,
            'pid': p.problem_id,
            'batch': p.batch_name,
            'batch_idx': p.batch_idx,
            'batch_total': p.batch_total,
            'wall_time': p.wall_time,
            'start_min': start_time / 60,
            'end_min': end_time / 60,
            'correct': p.correct,
            'predicted': p.predicted,
            'expected': p.expected,
            'attempts': len(p.attempts),
            'early_stop': p.early_stop,
            'total_answered': p.total_answered,
            'errors': p.total_errors,
            'is_wrong': p.problem_id in WRONG_IDS,
            'problem': p,
        })
        cumulative_time = end_time

    total_runtime_min = cumulative_time / 60

    out("# V23 Problem Ordering Analysis — 17 Wrong Problems")
    out()
    out(f"**Total entries**: {len(problems)} (97 expected — some problems run twice for dual-run)")
    out(f"**Total runtime**: {total_runtime_min:.1f} min (budget: {BUDGET_MINUTES:.0f} min)")
    out(f"**Over budget by**: {total_runtime_min - BUDGET_MINUTES:.1f} min")
    out()

    # ══════════════════════════════════════════════════════════════════════════
    # Q1: What ORDER were the 17 wrong problems solved in?
    # ══════════════════════════════════════════════════════════════════════════
    out("## 1. Problem Order — Where Each Wrong Problem Fell")
    out()
    out("| # | Problem ID | Batch | Wall Time | Start (min) | End (min) | Correct | Early Stop | Attempts |")
    out("|---|-----------|-------|-----------|-------------|-----------|---------|------------|----------|")

    wrong_entries = [e for e in problem_order if e['is_wrong']]
    for e in wrong_entries:
        status = "WRONG"
        es = "Yes" if e['early_stop'] else "No"
        out(f"| {e['idx']}/{len(problems)} | {e['pid']} | {e['batch'][:20]} | {fmt_time(e['wall_time'])} | {e['start_min']:.1f} | {e['end_min']:.1f} | {status} | {es} | {e['attempts']} |")

    out()

    # Classify into thirds
    n = len(problems)
    third = n / 3
    early_wrong = [e for e in wrong_entries if e['idx'] <= third]
    mid_wrong = [e for e in wrong_entries if third < e['idx'] <= 2 * third]
    late_wrong = [e for e in wrong_entries if e['idx'] > 2 * third]

    out(f"**Distribution across run thirds** (each third = ~{third:.0f} problems):")
    out(f"- Early (1-{int(third)}): {len(early_wrong)} wrong")
    out(f"- Middle ({int(third)+1}-{int(2*third)}): {len(mid_wrong)} wrong")
    out(f"- Late ({int(2*third)+1}-{n}): {len(late_wrong)} wrong")
    out()

    # ══════════════════════════════════════════════════════════════════════════
    # Q2: Were any in the LAST batch / near time limit?
    # ══════════════════════════════════════════════════════════════════════════
    out("## 2. Problems Near the Time Limit")
    out()

    over_budget = [e for e in problem_order if e['start_min'] >= BUDGET_MINUTES]
    near_budget = [e for e in problem_order if BUDGET_MINUTES - 30 <= e['start_min'] < BUDGET_MINUTES]

    out(f"**Problems that STARTED after 300 min budget**: {len(over_budget)}")
    if over_budget:
        for e in over_budget:
            w = " ** WRONG **" if e['is_wrong'] else ""
            out(f"  - #{e['idx']} {e['pid']} — started at {e['start_min']:.1f} min, ended {e['end_min']:.1f} min{w}")
    out()

    out(f"**Problems that started in last 30 min of budget (270-300 min)**: {len(near_budget)}")
    if near_budget:
        for e in near_budget:
            w = " ** WRONG **" if e['is_wrong'] else ""
            out(f"  - #{e['idx']} {e['pid']} — started at {e['start_min']:.1f} min, ended {e['end_min']:.1f} min{w}")
    out()

    # Last 10 problems
    out("### Last 10 Problems in the Run")
    out()
    out("| # | Problem ID | Batch | Start (min) | End (min) | Correct? | Wall Time |")
    out("|---|-----------|-------|-------------|-----------|----------|-----------|")
    for e in problem_order[-10:]:
        status = "CORRECT" if e['correct'] else "**WRONG**"
        out(f"| {e['idx']} | {e['pid']} | {e['batch'][:20]} | {e['start_min']:.1f} | {e['end_min']:.1f} | {status} | {fmt_time(e['wall_time'])} |")
    out()

    wrong_in_last10 = sum(1 for e in problem_order[-10:] if e['is_wrong'])
    correct_in_last10 = sum(1 for e in problem_order[-10:] if e['correct'])
    out(f"**Last 10 accuracy**: {correct_in_last10}/10 ({correct_in_last10*10}%)")
    out()

    # ══════════════════════════════════════════════════════════════════════════
    # Q3: Per-problem timing comparison
    # ══════════════════════════════════════════════════════════════════════════
    out("## 3. Timing Comparison: Wrong vs Correct Problems")
    out()

    correct_times = [e['wall_time'] for e in problem_order if e['correct']]
    wrong_times = [e['wall_time'] for e in problem_order if e['is_wrong']]

    out("| Metric | Correct Problems | Wrong Problems |")
    out("|--------|-----------------|----------------|")
    out(f"| Count | {len(correct_times)} | {len(wrong_times)} |")
    out(f"| Mean time | {fmt_time(mean(correct_times))} | {fmt_time(mean(wrong_times))} |")
    out(f"| Median time | {fmt_time(median(correct_times))} | {fmt_time(median(wrong_times))} |")
    out(f"| Std dev | {fmt_time(stdev(correct_times))} | {fmt_time(stdev(wrong_times))} |")
    out(f"| Min | {fmt_time(min(correct_times) if correct_times else 0)} | {fmt_time(min(wrong_times) if wrong_times else 0)} |")
    out(f"| Max | {fmt_time(max(correct_times) if correct_times else 0)} | {fmt_time(max(wrong_times) if wrong_times else 0)} |")
    out(f"| Total | {fmt_min(sum(correct_times))} min | {fmt_min(sum(wrong_times))} min |")
    out()

    out("### Per-Problem Timing Detail (17 Wrong)")
    out()
    out("| Problem ID | Wall Time | Attempts | Answered | Errors | Early Stop | Batch |")
    out("|-----------|-----------|----------|----------|--------|------------|-------|")
    for e in sorted(wrong_entries, key=lambda x: x['wall_time'], reverse=True):
        es = "Yes" if e['early_stop'] else "No"
        out(f"| {e['pid']} | {fmt_time(e['wall_time'])} | {e['attempts']} | {e['total_answered']} | {e['errors']} | {es} | {e['batch'][:20]} |")
    out()

    # ══════════════════════════════════════════════════════════════════════════
    # Q4: Attempt counts — were they cut short?
    # ══════════════════════════════════════════════════════════════════════════
    out("## 4. Attempt Count Analysis — Were Problems Cut Short?")
    out()

    correct_attempts = [e['attempts'] for e in problem_order if e['correct']]
    wrong_attempts = [e['attempts'] for e in problem_order if e['is_wrong']]

    out("| Metric | Correct Problems | Wrong Problems |")
    out("|--------|-----------------|----------------|")
    out(f"| Mean attempts | {mean(correct_attempts):.1f} | {mean(wrong_attempts):.1f} |")
    out(f"| Median attempts | {median(correct_attempts):.0f} | {median(wrong_attempts):.0f} |")
    out(f"| Early stop rate | {sum(1 for e in problem_order if e['correct'] and e['early_stop'])}/{len(correct_times)} ({sum(1 for e in problem_order if e['correct'] and e['early_stop'])/max(len(correct_times),1)*100:.0f}%) | {sum(1 for e in problem_order if e['is_wrong'] and e['early_stop'])}/{len(wrong_times)} ({sum(1 for e in problem_order if e['is_wrong'] and e['early_stop'])/max(len(wrong_times),1)*100:.0f}%) |")
    out()

    # Check for abnormally low attempt counts (possible time cutoff)
    out("### Problems with Very Few Attempts (Possible Time Cutoff)")
    out()
    max_attempts_in_run = max(e['attempts'] for e in problem_order) if problem_order else 0
    low_attempt = [e for e in wrong_entries if e['attempts'] < 5]
    if low_attempt:
        out(f"Max attempts seen in run: {max_attempts_in_run}")
        out()
        for e in low_attempt:
            out(f"- {e['pid']}: only {e['attempts']} attempts (started at {e['start_min']:.1f} min)")
    else:
        out(f"All 17 wrong problems had >= 5 attempts. Max in run: {max_attempts_in_run}")
    out()

    # ══════════════════════════════════════════════════════════════════════════
    # Q5: Truncated/incomplete attempts
    # ══════════════════════════════════════════════════════════════════════════
    out("## 5. Truncated or Incomplete Attempts")
    out()

    # For each wrong problem, check if any attempts seem abnormally short
    all_attempt_times = []
    all_attempt_turns = []
    for e in problem_order:
        p = e['problem']
        for att in p.attempts:
            all_attempt_times.append(att.time_s)
            all_attempt_turns.append(len(att.turns))

    avg_att_time = mean(all_attempt_times)
    avg_att_turns = mean(all_attempt_turns)

    out(f"**Baseline**: Average attempt time = {fmt_time(avg_att_time)}, Average turns per attempt = {avg_att_turns:.1f}")
    out()
    out("### Wrong Problems — Attempt Details")
    out()

    for e in wrong_entries:
        p = e['problem']
        att_times = [a.time_s for a in p.attempts]
        att_turns = [len(a.turns) for a in p.attempts]
        att_nones = sum(1 for a in p.attempts if a.is_none)

        short_attempts = sum(1 for t in att_times if t < avg_att_time * 0.25)

        # Check for last attempt being abnormally short (possible cutoff)
        last_att_time = att_times[-1] if att_times else 0
        last_att_short = last_att_time < avg_att_time * 0.25 if att_times else False

        truncation_flag = ""
        if last_att_short:
            truncation_flag = " [LAST ATT SHORT]"
        if short_attempts > len(att_times) * 0.5:
            truncation_flag += " [MANY SHORT]"

        out(f"**{e['pid']}** (#{e['idx']}, started {e['start_min']:.1f} min):{truncation_flag}")
        out(f"  - {len(p.attempts)} attempts, {att_nones} Nones, avg time {fmt_time(mean(att_times))}, avg turns {mean(att_turns):.1f}")
        if att_times:
            out(f"  - Attempt times: [{', '.join(fmt_time(t) for t in att_times)}]")
            out(f"  - Attempt turns: [{', '.join(str(len(a.turns)) for a in p.attempts)}]")
        out()

    # ══════════════════════════════════════════════════════════════════════════
    # Q6: Correlation — order vs correctness
    # ══════════════════════════════════════════════════════════════════════════
    out("## 6. Order vs Correctness — Are Later Problems Less Accurate?")
    out()

    # Divide into quintiles
    quintile_size = len(problem_order) / 5
    out("### Accuracy by Quintile (run position)")
    out()
    out("| Quintile | Problems | Correct | Wrong | Accuracy | Avg Time |")
    out("|----------|----------|---------|-------|----------|----------|")

    for q in range(5):
        start_idx = int(q * quintile_size)
        end_idx = int((q + 1) * quintile_size)
        qprobs = problem_order[start_idx:end_idx]
        qcorrect = sum(1 for e in qprobs if e['correct'])
        qwrong = sum(1 for e in qprobs if not e['correct'])
        qacc = qcorrect / len(qprobs) * 100 if qprobs else 0
        qavg_time = mean([e['wall_time'] for e in qprobs]) if qprobs else 0
        label = f"Q{q+1} (#{start_idx+1}-{end_idx})"
        out(f"| {label} | {len(qprobs)} | {qcorrect} | {qwrong} | {qacc:.0f}% | {fmt_time(qavg_time)} |")
    out()

    # Rolling window accuracy (window of 10)
    out("### Rolling Accuracy (window=10)")
    out()
    out("| Window | Problems | Correct | Accuracy | Cumul Time |")
    out("|--------|----------|---------|----------|------------|")
    window = 10
    for start in range(0, len(problem_order), window):
        end = min(start + window, len(problem_order))
        wprobs = problem_order[start:end]
        wcorrect = sum(1 for e in wprobs if e['correct'])
        wacc = wcorrect / len(wprobs) * 100 if wprobs else 0
        cumul = wprobs[-1]['end_min'] if wprobs else 0
        out(f"| #{start+1}-{end} | {len(wprobs)} | {wcorrect} | {wacc:.0f}% | {cumul:.1f} min |")
    out()

    # ══════════════════════════════════════════════════════════════════════════
    # Q7: Cumulative runtime timeline
    # ══════════════════════════════════════════════════════════════════════════
    out("## 7. Cumulative Runtime Timeline — All Problems")
    out()
    out("Each problem plotted against the 300 min budget. Wrong problems marked with `***`.")
    out()
    out("```")
    out(f"{'#':>3} {'PID':>8} {'Batch':<20} {'Start':>8} {'End':>8} {'Wall':>8} {'Status':>10}  Timeline (5min=|)")
    out("-" * 110)

    for e in problem_order:
        status = "CORRECT" if e['correct'] else "***WRONG"
        # ASCII timeline: each | = 5 minutes
        bar_start = int(e['start_min'] / 5)
        bar_end = int(e['end_min'] / 5)
        bar_len = max(bar_end - bar_start, 1)

        # Budget marker at 300/5 = 60 chars
        budget_pos = int(BUDGET_MINUTES / 5)

        timeline = [' '] * max(budget_pos + 5, bar_end + 2)
        timeline[budget_pos] = '|'  # budget line

        char = '#' if not e['correct'] else '='
        for j in range(bar_start, min(bar_end + 1, len(timeline))):
            timeline[j] = char

        timeline_str = ''.join(timeline[:budget_pos + 5])

        out(f"{e['idx']:>3} {e['pid']:>8} {e['batch'][:20]:<20} {e['start_min']:>7.1f}m {e['end_min']:>7.1f}m {e['wall_time']:>7.0f}s {status:>10}  {timeline_str}")

    out("```")
    out()
    out(f"Legend: `=` = correct problem time span, `#` = wrong problem, `|` at position 60 = 300 min budget")
    out()

    # ══════════════════════════════════════════════════════════════════════════
    # Q8: Val Bench batch analysis — were failures at the end?
    # ══════════════════════════════════════════════════════════════════════════
    out("## 8. Val Bench Batch — Were Failures Concentrated at the End?")
    out()

    val_bench = [e for e in problem_order if 'val' in e['batch'].lower() or 'bench' in e['batch'].lower()]
    if not val_bench:
        # Try to identify Val Bench by batch_total = 70
        val_bench = [e for e in problem_order if e['batch_total'] == 70]
    if not val_bench:
        # Fallback: look for the big batch
        from collections import Counter
        batch_counts = Counter(e['batch'] for e in problem_order)
        biggest_batch = batch_counts.most_common(1)[0][0] if batch_counts else ""
        val_bench = [e for e in problem_order if e['batch'] == biggest_batch]
        out(f"Note: Could not identify 'Val Bench' by name, using largest batch: '{biggest_batch}' ({len(val_bench)} problems)")
        out()

    if val_bench:
        vb_correct = sum(1 for e in val_bench if e['correct'])
        vb_wrong = sum(1 for e in val_bench if not e['correct'])
        out(f"**Val Bench total**: {len(val_bench)} problems, {vb_correct} correct, {vb_wrong} wrong")
        out()

        # Split Val Bench into quarters
        vb_quarter = len(val_bench) / 4
        out("### Val Bench Accuracy by Quarter (within batch)")
        out()
        out("| Quarter | Problems | Correct | Wrong | Accuracy | Time Range (min) |")
        out("|---------|----------|---------|-------|----------|------------------|")

        for q in range(4):
            start_idx = int(q * vb_quarter)
            end_idx = int((q + 1) * vb_quarter)
            qprobs = val_bench[start_idx:end_idx]
            qcorrect = sum(1 for e in qprobs if e['correct'])
            qwrong = sum(1 for e in qprobs if not e['correct'])
            qacc = qcorrect / len(qprobs) * 100 if qprobs else 0
            time_range = f"{qprobs[0]['start_min']:.0f}-{qprobs[-1]['end_min']:.0f}" if qprobs else "-"
            out(f"| Q{q+1} ({start_idx+1}-{end_idx}) | {len(qprobs)} | {qcorrect} | {qwrong} | {qacc:.0f}% | {time_range} |")
        out()

        # Show specific wrong Val Bench problems with position
        vb_wrong_list = [e for e in val_bench if not e['correct']]
        out(f"### Val Bench Wrong Problems — Positions Within Batch")
        out()
        out("| Batch Pos | Global # | Problem ID | Start (min) | End (min) | Wall Time | Attempts |")
        out("|-----------|----------|-----------|-------------|-----------|-----------|----------|")
        for i, e in enumerate(val_bench):
            if not e['correct']:
                out(f"| {i+1}/{len(val_bench)} | #{e['idx']} | {e['pid']} | {e['start_min']:.1f} | {e['end_min']:.1f} | {fmt_time(e['wall_time'])} | {e['attempts']} |")
        out()

        # Were more failures at the end of Val Bench?
        first_half_wrong = sum(1 for i, e in enumerate(val_bench) if i < len(val_bench) / 2 and not e['correct'])
        second_half_wrong = sum(1 for i, e in enumerate(val_bench) if i >= len(val_bench) / 2 and not e['correct'])
        first_half_total = len([e for i, e in enumerate(val_bench) if i < len(val_bench) / 2])
        second_half_total = len([e for i, e in enumerate(val_bench) if i >= len(val_bench) / 2])

        out(f"**First half**: {first_half_wrong}/{first_half_total} wrong ({first_half_wrong/max(first_half_total,1)*100:.0f}%)")
        out(f"**Second half**: {second_half_wrong}/{second_half_total} wrong ({second_half_wrong/max(second_half_total,1)*100:.0f}%)")
        out()

    # ══════════════════════════════════════════════════════════════════════════
    # Q9: DOUBLE-RUN RETRY impact — critical structural insight
    # ══════════════════════════════════════════════════════════════════════════
    out("## 9. DOUBLE-RUN RETRY Batch — Critical Structural Insight")
    out()
    out("**The DOUBLE-RUN RETRY batch re-runs the same problems that were already wrong.**")
    out("This means 15-17 of the 'late run' entries are NOT new failures — they are")
    out("second attempts at problems that already failed in their first batch.")
    out()

    retry_entries = [e for e in problem_order if 'retry' in e['batch'].lower() or 'double' in e['batch'].lower()]
    non_retry = [e for e in problem_order if 'retry' not in e['batch'].lower() and 'double' not in e['batch'].lower()]

    out(f"**DOUBLE-RUN RETRY batch**: {len(retry_entries)} entries, {sum(1 for e in retry_entries if e['correct'])} correct, {sum(1 for e in retry_entries if not e['correct'])} wrong")
    out(f"**Non-retry entries**: {len(non_retry)} entries, {sum(1 for e in non_retry if e['correct'])} correct, {sum(1 for e in non_retry if not e['correct'])} wrong")
    out()

    # Compare first-run vs retry performance for the same problems
    first_run = {}
    retry_run = {}
    for e in problem_order:
        pid = e['pid']
        if 'retry' in e['batch'].lower() or 'double' in e['batch'].lower():
            retry_run[pid] = e
        elif pid not in first_run:
            first_run[pid] = e

    out("### First Run vs Retry — Same Problem Comparison")
    out()
    out("| Problem ID | First Batch | First Result | First Time | Retry Result | Retry Time | Changed? |")
    out("|-----------|-------------|--------------|------------|--------------|------------|----------|")

    for pid in sorted(retry_run.keys()):
        if pid in first_run:
            fr = first_run[pid]
            rr = retry_run[pid]
            fr_res = "CORRECT" if fr['correct'] else "WRONG"
            rr_res = "CORRECT" if rr['correct'] else "WRONG"
            changed = "YES" if fr['correct'] != rr['correct'] else "No"
            out(f"| {pid} | {fr['batch'][:20]} | {fr_res} | {fmt_time(fr['wall_time'])} | {rr_res} | {fmt_time(rr['wall_time'])} | {changed} |")
    out()

    flipped_to_correct = sum(1 for pid in retry_run if pid in first_run and not first_run[pid]['correct'] and retry_run[pid]['correct'])
    flipped_to_wrong = sum(1 for pid in retry_run if pid in first_run and first_run[pid]['correct'] and not retry_run[pid]['correct'])
    stayed_wrong = sum(1 for pid in retry_run if pid in first_run and not first_run[pid]['correct'] and not retry_run[pid]['correct'])
    stayed_correct = sum(1 for pid in retry_run if pid in first_run and first_run[pid]['correct'] and retry_run[pid]['correct'])

    out(f"**Stayed correct**: {stayed_correct}")
    out(f"**Flipped to correct (retry helped)**: {flipped_to_correct}")
    out(f"**Stayed wrong (retry useless)**: {stayed_wrong}")
    out(f"**Flipped to wrong (retry hurt)**: {flipped_to_wrong}")
    out()

    # Recalculate Q6 excluding retry batch
    out("### Q6 Corrected — Order vs Correctness (Excluding DOUBLE-RUN RETRY)")
    out()
    out("| Quintile | Problems | Correct | Wrong | Accuracy |")
    out("|----------|----------|---------|-------|----------|")

    nr_quintile = len(non_retry) / 5
    for q in range(5):
        start_idx = int(q * nr_quintile)
        end_idx = int((q + 1) * nr_quintile)
        qprobs = non_retry[start_idx:end_idx]
        qcorrect = sum(1 for e in qprobs if e['correct'])
        qwrong = sum(1 for e in qprobs if not e['correct'])
        qacc = qcorrect / len(qprobs) * 100 if qprobs else 0
        label = f"Q{q+1} (#{start_idx+1}-{end_idx})"
        out(f"| {label} | {len(qprobs)} | {qcorrect} | {qwrong} | {qacc:.0f}% |")
    out()

    out("(This is the real test — without the retry batch artificially inflating late failures.)")
    out()

    # ══════════════════════════════════════════════════════════════════════════
    # Q10: Were DOUBLE-RUN retries affected by time pressure or vLLM degradation?
    # ══════════════════════════════════════════════════════════════════════════
    out("## 10. Retry Batch — Were Retries Hurt by Time Pressure or Model Degradation?")
    out()

    # Compare answer distributions between first and retry
    for pid in sorted(retry_run.keys()):
        if pid in first_run:
            fr_p = first_run[pid]['problem']
            rr_p = retry_run[pid]['problem']

            fr_nones = sum(1 for a in fr_p.attempts if a.is_none)
            rr_nones = sum(1 for a in rr_p.attempts if a.is_none)
            fr_errors = fr_p.total_errors
            rr_errors = rr_p.total_errors
            fr_answered = fr_p.total_answered
            rr_answered = rr_p.total_answered

            degradation = ""
            if rr_nones > fr_nones + 3:
                degradation += " [MORE NONES]"
            if rr_errors > fr_errors * 1.5 and fr_errors > 0:
                degradation += " [MORE ERRORS]"
            if rr_answered < fr_answered - 3:
                degradation += " [FEWER ANSWERS]"

            if degradation:
                out(f"**{pid}**:{degradation}")
                out(f"  - First: {fr_answered} answered, {fr_nones} Nones, {fr_errors} errors, {fmt_time(first_run[pid]['wall_time'])}")
                out(f"  - Retry: {rr_answered} answered, {rr_nones} Nones, {rr_errors} errors, {fmt_time(retry_run[pid]['wall_time'])}")
                out()

    # Aggregate comparison
    fr_total_nones = sum(sum(1 for a in first_run[pid]['problem'].attempts if a.is_none) for pid in retry_run if pid in first_run)
    rr_total_nones = sum(sum(1 for a in retry_run[pid]['problem'].attempts if a.is_none) for pid in retry_run)
    fr_total_answered = sum(first_run[pid]['problem'].total_answered for pid in retry_run if pid in first_run)
    rr_total_answered = sum(retry_run[pid]['problem'].total_answered for pid in retry_run)

    out(f"**Aggregate (across all retried problems)**:")
    out(f"  - First run: {fr_total_answered} total answered, {fr_total_nones} total Nones")
    out(f"  - Retry:     {rr_total_answered} total answered, {rr_total_nones} total Nones")
    out(f"  - None increase: {rr_total_nones - fr_total_nones:+d} ({(rr_total_nones - fr_total_nones) / max(fr_total_nones, 1) * 100:+.0f}%)")
    out()

    # ══════════════════════════════════════════════════════════════════════════
    # Summary & Key Findings
    # ══════════════════════════════════════════════════════════════════════════
    out("## 11. Summary & Key Findings")
    out()

    # Recalculate using only first-run entries
    first_run_wrong = [e for e in non_retry if e['is_wrong']]
    first_run_correct = [e for e in non_retry if e['correct']]

    out("### Stats (First-Run Only — Excluding DOUBLE-RUN RETRY)")
    out()

    # Check if wrong problems cluster late
    wrong_positions = [e['idx'] for e in first_run_wrong]
    correct_positions = [e['idx'] for e in first_run_correct]
    avg_wrong_pos = mean(wrong_positions) if wrong_positions else 0
    avg_all_pos = mean([e['idx'] for e in non_retry])

    # Time-based clustering
    wrong_start_times = [e['start_min'] for e in wrong_entries]
    all_start_times = [e['start_min'] for e in problem_order]
    avg_wrong_start = mean(wrong_start_times)
    avg_all_start = mean(all_start_times)

    out(f"1. **Average position of wrong problems**: #{avg_wrong_pos:.1f} (vs overall avg #{avg_all_pos:.1f})")
    if avg_wrong_pos > avg_all_pos:
        out(f"   -> Wrong problems are biased toward LATER in the run (by {avg_wrong_pos - avg_all_pos:.1f} positions)")
    else:
        out(f"   -> Wrong problems are NOT biased toward late positions")
    out()

    out(f"2. **Average start time of wrong problems**: {avg_wrong_start:.1f} min (vs overall avg {avg_all_start:.1f} min)")
    out()

    # Over-budget problems
    wrong_over_budget = [e for e in wrong_entries if e['start_min'] >= BUDGET_MINUTES]
    wrong_near_budget = [e for e in wrong_entries if e['start_min'] >= BUDGET_MINUTES - 30]
    out(f"3. **Wrong problems starting after 300 min**: {len(wrong_over_budget)}")
    out(f"   **Wrong problems starting after 270 min**: {len(wrong_near_budget)}")
    out()

    # Attempt comparison
    out(f"4. **Attempt counts**: Wrong problems avg {mean(wrong_attempts):.1f} attempts vs correct avg {mean(correct_attempts):.1f}")
    cut_short = [e for e in wrong_entries if e['attempts'] < 5]
    out(f"   **Cut short (< 5 attempts)**: {len(cut_short)} problems")
    out()

    # Timing comparison
    out(f"5. **Timing**: Wrong problems avg {fmt_time(mean(wrong_times))} vs correct avg {fmt_time(mean(correct_times))}")
    if mean(wrong_times) > mean(correct_times) * 1.2:
        out(f"   -> Wrong problems took {mean(wrong_times)/mean(correct_times):.1f}x longer (harder, more attempts)")
    elif mean(wrong_times) < mean(correct_times) * 0.8:
        out(f"   -> Wrong problems were FASTER (possible early stop on wrong consensus)")
    else:
        out(f"   -> Similar timing between wrong and correct")
    out()

    # Batch-specific
    batch_wrong = {}
    for e in problem_order:
        b = e['batch']
        if b not in batch_wrong:
            batch_wrong[b] = {'total': 0, 'wrong': 0}
        batch_wrong[b]['total'] += 1
        if not e['correct']:
            batch_wrong[b]['wrong'] += 1

    out("6. **Failure rate by batch**:")
    for b, d in sorted(batch_wrong.items(), key=lambda x: x[1]['wrong'], reverse=True):
        if d['wrong'] > 0:
            out(f"   - {b}: {d['wrong']}/{d['total']} wrong ({d['wrong']/d['total']*100:.0f}%)")
    out()

    # Final verdict on time pressure
    out("### Verdict: Did Time Pressure Cause Failures?")
    out()
    if len(wrong_over_budget) > 0:
        out(f"**YES (partially)**: {len(wrong_over_budget)} wrong problem(s) started AFTER the 300 min budget.")
        for e in wrong_over_budget:
            out(f"  - {e['pid']}: started at {e['start_min']:.1f} min")
    elif len(wrong_near_budget) > 3:
        out(f"**LIKELY**: {len(wrong_near_budget)} wrong problems started in the last 30 min of the budget, suggesting time pressure.")
    else:
        out("**NO**: Wrong problems are distributed throughout the run, not concentrated at the end.")
        out("The failures are more likely due to problem difficulty and model limitations, not time pressure.")
    out()

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Problem ordering analysis for v23 wrong problems')
    parser.add_argument('logfile', help='Path to diagnostic.log')
    parser.add_argument('--output', '-o', default=None, help='Output markdown file (default: stdout)')
    args = parser.parse_args()

    problems = parse_log(args.logfile)
    report = analyze(problems)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report written to {args.output}")
        print(f"Parsed {len(problems)} problems from {args.logfile}")
    else:
        print(report)


if __name__ == '__main__':
    main()
