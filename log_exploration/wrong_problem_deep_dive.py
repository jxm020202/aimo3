#!/usr/bin/env python3
"""
Wrong Problem Deep Dive — Full analysis of all 17 wrong problems from v23.
===========================================================================
For each wrong problem (across all runs if dual-run), produces:
  1. Vote table with correct answer marked
  2. Per-attempt detail table (attempt#, temp, answer, entropy, code_calls, errors, time)
  3. Whether correct answer was found, by which attempts and temps
  4. None rate
  5. Classification (Outvoted / Never found / Confident wrong / Scattered)
  6. Temperature pattern for correct finds
  7. Code calls vs no-code comparison
  8. Entropy signal analysis

Usage:
    python3 log_exploration/wrong_problem_deep_dive.py output/v23/diagnostic.log
    python3 log_exploration/wrong_problem_deep_dive.py output/v23/diagnostic.log -o output/v23/wrong_problems_deep_dive.md
    python3 log_exploration/wrong_problem_deep_dive.py output/v23/diagnostic.log --problem 21fb4e
"""

import sys
import os
import argparse
from collections import Counter, defaultdict
from io import StringIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


# ── Helpers ─────────────────────────────────────────────────────────────────

def fmt_time(s):
    if s >= 3600:
        return f"{s/3600:.1f}h"
    if s >= 60:
        return f"{s/60:.1f}m"
    return f"{s:.1f}s"


def fmt_answer(ans):
    return str(ans) if ans is not None else "None"


def classify_problem(expected, all_attempts, vote_counts):
    """Classify a wrong problem into one of 4 categories."""
    answers = [a.answer for a in all_attempts if a.answer is not None]
    correct_found = expected in answers
    correct_count = answers.count(expected)
    unique_answers = len(set(answers))
    total_with_answer = len(answers)

    if not correct_found:
        # Check if most votes go to a single wrong answer
        if vote_counts:
            top_answer, top_count = vote_counts.most_common(1)[0]
            if top_count >= 5:
                return "Confident wrong"
        if unique_answers >= 5:
            return "Scattered"
        return "Never found"
    else:
        return "Outvoted"


def make_table(headers, rows, alignments=None):
    """Make a markdown table. alignments: list of 'l', 'r', 'c'."""
    if not rows:
        return "(no data)\n"
    col_widths = [len(h) for h in headers]
    str_rows = []
    for row in rows:
        sr = [str(c) for c in row]
        str_rows.append(sr)
        for j, c in enumerate(sr):
            col_widths[j] = max(col_widths[j], len(c))

    if alignments is None:
        alignments = ['l'] * len(headers)

    lines = []
    # Header
    hdr = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
    lines.append(hdr)
    # Separator
    sep_parts = []
    for i, a in enumerate(alignments):
        w = col_widths[i]
        if a == 'r':
            sep_parts.append("-" * (w - 1) + ":")
        elif a == 'c':
            sep_parts.append(":" + "-" * (w - 2) + ":")
        else:
            sep_parts.append("-" * w)
    lines.append("| " + " | ".join(sep_parts) + " |")
    # Rows
    for sr in str_rows:
        parts = []
        for j, c in enumerate(sr):
            if alignments[j] == 'r':
                parts.append(c.rjust(col_widths[j]))
            else:
                parts.append(c.ljust(col_widths[j]))
        lines.append("| " + " | ".join(parts) + " |")
    return "\n".join(lines) + "\n"


# ── Per-problem analysis ───────────────────────────────────────────────────

def analyze_problem(problem_id, expected, all_entries, out):
    """Full analysis of a single wrong problem across all runs."""
    # Combine all attempts across all runs
    all_attempts = []
    for run_idx, entry in enumerate(all_entries):
        for a in entry.attempts:
            a._run_idx = run_idx + 1  # tag with run number
            all_attempts.append(a)

    total_attempts = len(all_attempts)
    none_attempts = [a for a in all_attempts if a.answer is None]
    answered_attempts = [a for a in all_attempts if a.answer is not None]
    correct_attempts = [a for a in all_attempts if a.answer == expected]
    wrong_attempts = [a for a in answered_attempts if a.answer != expected]

    # Build combined vote counts
    vote_counts = Counter()
    for a in answered_attempts:
        vote_counts[a.answer] += 1

    # Classification
    classification = classify_problem(expected, all_attempts, vote_counts)

    # Predicted (from first wrong entry, or first entry if all wrong)
    wrong_entries = [e for e in all_entries if not e.correct]
    predicted = wrong_entries[0].predicted if wrong_entries else all_entries[0].predicted

    out.write(f"\n{'=' * 80}\n")
    out.write(f"## Problem `{problem_id}` — Expected: **{expected}**, Predicted: **{predicted}**\n")
    out.write(f"{'=' * 80}\n\n")

    # Summary line
    num_runs = len(all_entries)
    out.write(f"- **Runs**: {num_runs} ({'dual-run' if num_runs > 1 else 'single run'}), "
              f"**{total_attempts}** total attempts\n")
    out.write(f"- **Classification**: **{classification}**\n")
    out.write(f"- **None rate**: {len(none_attempts)}/{total_attempts} "
              f"({100*len(none_attempts)/total_attempts:.0f}%)\n")
    correct_found = expected in [a.answer for a in all_attempts]
    if correct_found:
        out.write(f"- **Correct answer found**: YES — in {len(correct_attempts)} attempt(s)\n")
        temps_for_correct = [a.temperature for a in correct_attempts if a.temperature is not None]
        if temps_for_correct:
            temp_counts = Counter(temps_for_correct)
            temp_strs = [f"{t:.1f} ({c}x)" if c > 1 else f"{t:.1f}" for t, c in sorted(temp_counts.items())]
            out.write(f"- **Temps that found correct**: {', '.join(temp_strs)}\n")
        runs_for_correct = sorted(set(a._run_idx for a in correct_attempts))
        out.write(f"- **Run(s) that found correct**: {', '.join(str(r) for r in runs_for_correct)}\n")
    else:
        out.write(f"- **Correct answer found**: NO — never appeared in any attempt\n")
    out.write("\n")

    # ── 1. Vote Table ──
    out.write("### Vote Distribution\n\n")
    vote_rows = []
    for answer, count in vote_counts.most_common():
        marker = " **(CORRECT)**" if answer == expected else ""
        pct = 100 * count / len(answered_attempts) if answered_attempts else 0
        vote_rows.append((str(answer) + marker, str(count), f"{pct:.0f}%"))
    none_count = len(none_attempts)
    if none_count:
        pct = 100 * none_count / total_attempts
        vote_rows.append((f"None", str(none_count), f"{pct:.0f}%"))

    out.write(make_table(
        ["Answer", "Votes", "% of answered"],
        vote_rows,
        ['l', 'r', 'r']
    ))
    out.write("\n")

    # ── 2. Per-Attempt Detail (per run) ──
    for run_idx, entry in enumerate(all_entries):
        run_label = f"Run {run_idx + 1}" if num_runs > 1 else "Attempts"
        out.write(f"### {run_label} — Per-Attempt Detail\n\n")
        out.write(f"Predicted: {entry.predicted}, Early stop: {entry.early_stop}, "
                  f"Votes: {dict(entry.votes)}\n\n")

        att_rows = []
        for a in entry.attempts:
            ans_str = fmt_answer(a.answer)
            if a.answer == expected:
                ans_str += " **[C]**"
            elif a.answer is not None and a.answer != expected:
                ans_str += ""
            temp_str = f"{a.temperature:.1f}" if a.temperature is not None else "?"
            att_rows.append((
                str(a.attempt_num),
                temp_str,
                ans_str,
                f"{a.entropy:.3f}",
                str(a.code_calls),
                str(a.errors),
                fmt_time(a.time_s),
                str(a.tokens),
            ))

        out.write(make_table(
            ["Att#", "Temp", "Answer", "Entropy", "Code", "Errors", "Time", "Tokens"],
            att_rows,
            ['r', 'r', 'l', 'r', 'r', 'r', 'r', 'r']
        ))
        out.write("\n")

    # ── 3-6. Correct answer analysis ──
    out.write("### Correct Answer Analysis\n\n")
    if correct_found:
        out.write(f"Correct answer **{expected}** was found by **{len(correct_attempts)}** "
                  f"of **{total_attempts}** attempts ({100*len(correct_attempts)/total_attempts:.0f}%).\n\n")
        out.write("Attempts that found correct:\n\n")
        corr_rows = []
        for a in correct_attempts:
            temp_str = f"{a.temperature:.1f}" if a.temperature is not None else "?"
            corr_rows.append((
                f"Run {a._run_idx}", str(a.attempt_num), temp_str,
                f"{a.entropy:.3f}", str(a.code_calls), str(a.errors), fmt_time(a.time_s)
            ))
        out.write(make_table(
            ["Run", "Att#", "Temp", "Entropy", "Code", "Errors", "Time"],
            corr_rows,
            ['l', 'r', 'r', 'r', 'r', 'r', 'r']
        ))

        # Why it lost the vote
        winner = vote_counts.most_common(1)[0] if vote_counts else (None, 0)
        out.write(f"\n**Why it lost**: Correct got {vote_counts.get(expected, 0)} vote(s) "
                  f"vs winner `{winner[0]}` with {winner[1]} vote(s).\n")
    else:
        out.write(f"Correct answer **{expected}** was **NEVER** found in any of the "
                  f"{total_attempts} attempts across {len(all_entries)} run(s).\n")
        # Show closest answers
        if answered_attempts:
            distances = [(a.answer, abs(a.answer - expected)) for a in answered_attempts]
            distances.sort(key=lambda x: x[1])
            closest = distances[0]
            out.write(f"\nClosest answer: **{closest[0]}** (off by {closest[1]})\n")
    out.write("\n")

    # ── 7. Code calls vs no-code ──
    out.write("### Code Calls vs No-Code Analysis\n\n")
    with_code = [a for a in all_attempts if a.code_calls > 0]
    no_code = [a for a in all_attempts if a.code_calls == 0]
    code_correct = [a for a in with_code if a.answer == expected]
    no_code_correct = [a for a in no_code if a.answer == expected]
    code_answered = [a for a in with_code if a.answer is not None]
    no_code_answered = [a for a in no_code if a.answer is not None]
    code_none = [a for a in with_code if a.answer is None]
    no_code_none = [a for a in no_code if a.answer is None]

    code_rows = []
    if with_code:
        code_rows.append((
            f"With code ({len(with_code)})",
            f"{len(code_answered)} ({100*len(code_answered)/len(with_code):.0f}%)",
            f"{len(code_none)} ({100*len(code_none)/len(with_code):.0f}%)",
            f"{len(code_correct)} ({100*len(code_correct)/len(with_code):.0f}%)",
            f"{sum(a.code_calls for a in with_code)/len(with_code):.1f}",
        ))
    if no_code:
        code_rows.append((
            f"No code ({len(no_code)})",
            f"{len(no_code_answered)} ({100*len(no_code_answered)/len(no_code):.0f}%)",
            f"{len(no_code_none)} ({100*len(no_code_none)/len(no_code):.0f}%)",
            f"{len(no_code_correct)} ({100*len(no_code_correct)/len(no_code):.0f}%)",
            "0",
        ))

    if code_rows:
        out.write(make_table(
            ["Group", "Answered", "None", "Correct", "Avg code calls"],
            code_rows,
            ['l', 'r', 'r', 'r', 'r']
        ))
    else:
        out.write("(no data)\n")
    out.write("\n")

    # ── 8. Entropy signal ──
    out.write("### Entropy Signal\n\n")
    if correct_attempts and wrong_attempts:
        avg_correct_entropy = sum(a.entropy for a in correct_attempts) / len(correct_attempts)
        avg_wrong_entropy = sum(a.entropy for a in wrong_attempts) / len(wrong_attempts)
        avg_none_entropy = (sum(a.entropy for a in none_attempts) / len(none_attempts)) if none_attempts else 0
        out.write(f"- Correct attempts avg entropy: **{avg_correct_entropy:.3f}**\n")
        out.write(f"- Wrong attempts avg entropy: **{avg_wrong_entropy:.3f}**\n")
        if none_attempts:
            out.write(f"- None attempts avg entropy: **{avg_none_entropy:.3f}**\n")
        if avg_correct_entropy < avg_wrong_entropy:
            out.write(f"- Signal: **Correct has LOWER entropy** (diff: {avg_wrong_entropy - avg_correct_entropy:.3f}) "
                      f"-- entropy weighting WOULD help\n")
        else:
            out.write(f"- Signal: Correct has HIGHER entropy (diff: {avg_correct_entropy - avg_wrong_entropy:.3f}) "
                      f"-- entropy weighting would NOT help\n")
    elif correct_attempts:
        avg_correct_entropy = sum(a.entropy for a in correct_attempts) / len(correct_attempts)
        out.write(f"- Correct attempts avg entropy: **{avg_correct_entropy:.3f}** (no wrong attempts to compare)\n")
    else:
        if answered_attempts:
            avg_answered_entropy = sum(a.entropy for a in answered_attempts) / len(answered_attempts)
            out.write(f"- No correct attempts found. Wrong attempts avg entropy: **{avg_answered_entropy:.3f}**\n")
        else:
            out.write(f"- No answered attempts to analyze.\n")
    out.write("\n")

    return {
        'problem_id': problem_id,
        'expected': expected,
        'predicted': predicted,
        'classification': classification,
        'correct_found': correct_found,
        'correct_count': len(correct_attempts),
        'total_attempts': total_attempts,
        'none_count': len(none_attempts),
        'none_rate': len(none_attempts) / total_attempts if total_attempts > 0 else 0,
        'unique_answers': len(vote_counts),
        'num_runs': len(all_entries),
        'temps_correct': sorted(set(a.temperature for a in correct_attempts if a.temperature is not None)),
        'avg_correct_entropy': (sum(a.entropy for a in correct_attempts) / len(correct_attempts)) if correct_attempts else None,
        'avg_wrong_entropy': (sum(a.entropy for a in wrong_attempts) / len(wrong_attempts)) if wrong_attempts else None,
        'code_calls_correct': len([a for a in correct_attempts if a.code_calls > 0]),
        'code_calls_wrong': len([a for a in wrong_attempts if a.code_calls > 0]),
    }


# ── Cross-problem summary ─────────────────────────────────────────────────

def write_summary(results, out):
    """Write cross-problem summary tables."""
    out.write(f"\n{'=' * 80}\n")
    out.write("# Cross-Problem Summary\n")
    out.write(f"{'=' * 80}\n\n")

    # Classification breakdown
    out.write("## Classification Breakdown\n\n")
    class_counts = Counter(r['classification'] for r in results)
    class_rows = []
    for cls, cnt in class_counts.most_common():
        pids = [r['problem_id'] for r in results if r['classification'] == cls]
        class_rows.append((cls, str(cnt), ", ".join(pids)))
    out.write(make_table(
        ["Classification", "Count", "Problem IDs"],
        class_rows,
        ['l', 'r', 'l']
    ))
    out.write("\n")

    # Master table
    out.write("## Master Table — All 17 Wrong Problems\n\n")
    master_rows = []
    for r in sorted(results, key=lambda x: x['classification']):
        correct_str = f"YES ({r['correct_count']})" if r['correct_found'] else "NO"
        temps_str = ", ".join(f"{t:.1f}" for t in r['temps_correct']) if r['temps_correct'] else "-"
        none_pct = f"{100*r['none_rate']:.0f}%"
        master_rows.append((
            f"`{r['problem_id']}`",
            str(r['expected']),
            str(r['predicted']),
            r['classification'],
            correct_str,
            f"{r['none_count']}/{r['total_attempts']}",
            none_pct,
            str(r['unique_answers']),
            temps_str,
        ))
    out.write(make_table(
        ["Problem", "Expected", "Predicted", "Class", "Correct Found?", "Nones", "None%", "Unique Ans", "Temps (correct)"],
        master_rows,
        ['l', 'r', 'r', 'l', 'l', 'r', 'r', 'r', 'l']
    ))
    out.write("\n")

    # Temperature pattern for correct finds
    out.write("## Temperature Pattern for Correct Finds\n\n")
    temp_finds = Counter()
    temp_totals = Counter()
    for r in results:
        for t in r['temps_correct']:
            temp_finds[t] += 1
    # Count total attempts at each temp across all wrong problems
    # (We'll use the results data)
    out.write("Which temperatures found the correct answer (across all 17 wrong problems):\n\n")
    if temp_finds:
        temp_rows = []
        for t in sorted(temp_finds.keys()):
            temp_rows.append((f"{t:.1f}", str(temp_finds[t])))
        out.write(make_table(
            ["Temperature", "# correct finds"],
            temp_rows,
            ['r', 'r']
        ))
    else:
        out.write("No correct answers found at any temperature for the wrong problems.\n")
    out.write("\n")

    # Entropy signal summary
    out.write("## Entropy Signal Summary\n\n")
    out.write("For problems where correct was found (outvoted), does correct have lower entropy?\n\n")
    entropy_rows = []
    for r in results:
        if r['correct_found'] and r['avg_correct_entropy'] is not None and r['avg_wrong_entropy'] is not None:
            diff = r['avg_wrong_entropy'] - r['avg_correct_entropy']
            signal = "LOWER (good)" if diff > 0 else "HIGHER (bad)"
            entropy_rows.append((
                f"`{r['problem_id']}`",
                f"{r['avg_correct_entropy']:.3f}",
                f"{r['avg_wrong_entropy']:.3f}",
                f"{diff:+.3f}",
                signal,
            ))
    if entropy_rows:
        out.write(make_table(
            ["Problem", "Correct Entropy", "Wrong Entropy", "Diff", "Signal"],
            entropy_rows,
            ['l', 'r', 'r', 'r', 'l']
        ))
        lower_count = sum(1 for r in entropy_rows if "LOWER" in r[4])
        out.write(f"\n**{lower_count}/{len(entropy_rows)}** outvoted problems have correct answers with lower entropy.\n")
    else:
        out.write("No outvoted problems with both correct and wrong attempts to compare.\n")
    out.write("\n")

    # Code usage summary
    out.write("## Code Usage — Correct vs Wrong\n\n")
    total_correct_with_code = sum(r['code_calls_correct'] for r in results)
    total_correct = sum(r['correct_count'] for r in results)
    total_wrong_with_code = sum(r['code_calls_wrong'] for r in results)
    if total_correct:
        pct = 100 * total_correct_with_code / total_correct
        out.write(f"- Correct attempts using code: **{total_correct_with_code}/{total_correct}** ({pct:.0f}%)\n")
    else:
        out.write("- No correct attempts found.\n")
    out.write("\n")

    # Actionable summary
    out.write("## Actionable Summary\n\n")
    outvoted = [r for r in results if r['classification'] == 'Outvoted']
    never_found = [r for r in results if r['classification'] == 'Never found']
    confident = [r for r in results if r['classification'] == 'Confident wrong']
    scattered = [r for r in results if r['classification'] == 'Scattered']

    if outvoted:
        out.write(f"### Outvoted ({len(outvoted)} problems) — Fixable with better voting\n\n")
        for r in outvoted:
            out.write(f"- `{r['problem_id']}`: correct found {r['correct_count']}x, "
                      f"but predicted {r['predicted']} instead of {r['expected']}\n")
        out.write("\n")

    if confident:
        out.write(f"### Confident Wrong ({len(confident)} problems) — Need strategy diversity\n\n")
        for r in confident:
            out.write(f"- `{r['problem_id']}`: model consistently says {r['predicted']}, "
                      f"correct is {r['expected']}\n")
        out.write("\n")

    if never_found:
        out.write(f"### Never Found ({len(never_found)} problems) — Need stronger model/reasoning\n\n")
        for r in never_found:
            out.write(f"- `{r['problem_id']}`: expected {r['expected']}, "
                      f"never appeared in {r['total_attempts']} attempts\n")
        out.write("\n")

    if scattered:
        out.write(f"### Scattered ({len(scattered)} problems) — No consensus, high variance\n\n")
        for r in scattered:
            out.write(f"- `{r['problem_id']}`: {r['unique_answers']} unique answers, "
                      f"none dominant\n")
        out.write("\n")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Deep dive into all wrong problems from a run")
    parser.add_argument("logfile", help="Path to diagnostic.log")
    parser.add_argument("-o", "--output", help="Save report to file (markdown)")
    parser.add_argument("--problem", help="Only analyze one specific problem ID")
    args = parser.parse_args()

    problems = parse_log(args.logfile)

    # The 17 wrong problem IDs and their expected answers
    WRONG_PROBLEMS = {
        '86e8e5': 8687,
        '1ec970': 8700,
        '21fb4e': 16,
        '23586c': 386,
        '26bee3': 108,
        '29714f': 297,
        '3980cd': 46,
        '3b88b3': 979,
        '414a5b': 42,
        '673b29': 3,
        '89c921': 29800,
        '9010d9': 10320,
        'a824c1': 24,
        'a9dbc8': 15744,
        'ae2add': 24931,
        'aff75c': 3571,
        'dbbfe8': 22,
    }

    if args.problem:
        if args.problem not in WRONG_PROBLEMS:
            print(f"Error: {args.problem} not in wrong problems list")
            print(f"Available: {', '.join(sorted(WRONG_PROBLEMS.keys()))}")
            sys.exit(1)
        WRONG_PROBLEMS = {args.problem: WRONG_PROBLEMS[args.problem]}

    # Group all entries by problem_id
    entries_by_pid = defaultdict(list)
    for p in problems:
        if p.problem_id in WRONG_PROBLEMS:
            entries_by_pid[p.problem_id].append(p)

    # Build output
    out = StringIO()
    out.write("# Wrong Problems Deep Dive — v23\n\n")
    out.write(f"**Log**: `{args.logfile}`\n")
    out.write(f"**Total wrong problems**: {len(WRONG_PROBLEMS)}\n")
    out.write(f"**Analysis**: Full vote tables, per-attempt detail, classification, "
              f"temperature patterns, entropy signals\n\n")

    # Table of contents
    out.write("## Table of Contents\n\n")
    for pid in sorted(WRONG_PROBLEMS.keys()):
        expected = WRONG_PROBLEMS[pid]
        entries = entries_by_pid.get(pid, [])
        num_runs = len(entries)
        out.write(f"- [{pid} (expected {expected})](#problem-{pid}--expected-{expected}-predicted-"
                  f"{entries[0].predicted if entries else '?'})\n")
    out.write("- [Cross-Problem Summary](#cross-problem-summary)\n")
    out.write("\n---\n")

    # Analyze each problem
    results = []
    for pid in sorted(WRONG_PROBLEMS.keys()):
        expected = WRONG_PROBLEMS[pid]
        entries = entries_by_pid.get(pid, [])
        if not entries:
            out.write(f"\n## Problem `{pid}` — NOT FOUND IN LOG\n\n")
            continue
        result = analyze_problem(pid, expected, entries, out)
        results.append(result)
        out.write("---\n")

    # Cross-problem summary
    write_summary(results, out)

    # Output
    report = out.getvalue()
    if args.output:
        os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else '.', exist_ok=True)
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.output}")
        print(f"  {len(results)} problems analyzed")
        print(f"  {sum(r['correct_count'] for r in results)} total correct attempts found")
        outvoted = sum(1 for r in results if r['classification'] == 'Outvoted')
        print(f"  {outvoted} outvoted (fixable with better voting)")
    else:
        print(report)


if __name__ == "__main__":
    main()
