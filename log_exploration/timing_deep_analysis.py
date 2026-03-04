#!/usr/bin/env python3
"""
Deep timing analysis for AIMO3 diagnostic logs.
Covers: right vs wrong distributions, time buckets, topic analysis,
wave simulation, wasted time, and attempt-level patterns.

Usage:
    python3 log_exploration/timing_deep_analysis.py output/v31/diagnostic.log
    python3 log_exploration/timing_deep_analysis.py output/v23/diagnostic.log
"""

import sys
import os
import re
from collections import Counter, defaultdict
from statistics import mean, median, stdev

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def percentile(data, p):
    if not data:
        return 0
    s = sorted(data)
    k = (len(s) - 1) * p / 100
    f = int(k)
    c = f + 1 if f + 1 < len(s) else f
    return s[f] + (k - f) * (s[c] - s[f])


def fmt(seconds):
    if seconds < 60:
        return f"{seconds:.0f}s"
    return f"{seconds/60:.1f}m"


# ── Topic classification ────────────────────────────────────────────────────

TOPIC_KEYWORDS = {
    "Number Theory": [
        r"prime", r"divis", r"modular", r"modulo", r"\bmod\b", r"congruen",
        r"\bgcd\b", r"\blcm\b", r"euler", r"fermat", r"coprime", r"residue",
        r"diophantine", r"factor", r"digit", r"multiple", r"remainder",
        r"perfect\s+(square|number|power)",
    ],
    "Algebra": [
        r"polynomial", r"equation", r"function", r"\broots?\b", r"inequalit",
        r"sequence", r"series", r"coefficient", r"quadratic", r"cubic",
        r"linear", r"recurren", r"sum\b", r"product", r"minimum", r"maximum",
        r"real\s+number", r"integer.*satisf", r"solve", r"expression",
        r"floor", r"ceil",
    ],
    "Combinatorics": [
        r"count", r"permut", r"combin", r"arrange", r"\bways\b", r"choose",
        r"path", r"binomial", r"selection", r"pigeonhole", r"inclusion",
        r"catalan", r"colou?ring", r"subset", r"partition", r"distribut",
        r"board", r"grid", r"tile", r"tiling", r"domino", r"place",
        r"chessboard", r"distinct",
    ],
    "Geometry": [
        r"triangle", r"circle", r"angle", r"\barea\b", r"perimeter",
        r"polygon", r"coordinate", r"distance", r"point", r"line\b",
        r"parallel", r"perpendicular", r"tangent", r"inscribe", r"circumscri",
        r"convex", r"hexagon", r"pentagon", r"rectangle",
        r"ellipse", r"diameter", r"radius", r"midpoint", r"vertex", r"vertices",
    ],
}


def classify_topic(problem):
    text = (problem.problem_text or "").lower()
    if problem.attempts:
        for turn in problem.attempts[0].turns[:2]:
            if turn.reasoning_text:
                text += " " + turn.reasoning_text[:2000].lower()
    scores = {}
    for topic, patterns in TOPIC_KEYWORDS.items():
        count = sum(len(re.findall(p, text)) for p in patterns)
        if count > 0:
            scores[topic] = count
    return max(scores, key=scores.get) if scores else "Other"


def classify_attempt(a, p):
    if a.is_none or a.answer is None:
        return "none"
    if p.expected is not None and a.answer == p.expected:
        return "correct"
    return "wrong"


# ═══════════════════════════════════════════════════════════════════════════════
# SECTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def section_overview(problems):
    print("=" * 80)
    print("  1. OVERALL TIMING STATS")
    print("=" * 80)

    att_times = [a.time_s for p in problems for a in p.attempts if a.time_s > 0]
    wall_times = [p.wall_time for p in problems if p.wall_time > 0]

    correct = sum(1 for p in problems if p.correct)
    print(f"\n  Score: {correct}/{len(problems)} ({100*correct/len(problems):.1f}%)")
    print(f"  Total problems: {len(problems)}")
    print(f"  Total attempts: {sum(len(p.attempts) for p in problems)}")
    print(f"  Total wall time: {fmt(sum(wall_times))}")

    print(f"\n  Per-Attempt Time:")
    print(f"    Mean: {fmt(mean(att_times))}  Median: {fmt(median(att_times))}")
    print(f"    P25: {fmt(percentile(att_times, 25))}  P75: {fmt(percentile(att_times, 75))}  P90: {fmt(percentile(att_times, 90))}")

    print(f"\n  Per-Problem Wall Time:")
    print(f"    Mean: {fmt(mean(wall_times))}  Median: {fmt(median(wall_times))}")
    print(f"    P25: {fmt(percentile(wall_times, 25))}  P75: {fmt(percentile(wall_times, 75))}  P90: {fmt(percentile(wall_times, 90))}")


def section_right_vs_wrong(problems):
    print(f"\n{'=' * 80}")
    print("  2. RIGHT vs WRONG vs NONE TIMING")
    print("=" * 80)

    correct_att, wrong_att, none_att = [], [], []
    correct_wall, wrong_wall = [], []

    for p in problems:
        (correct_wall if p.correct else wrong_wall).append(p.wall_time)
        for a in p.attempts:
            if a.time_s <= 0:
                continue
            cat = classify_attempt(a, p)
            {"correct": correct_att, "wrong": wrong_att, "none": none_att}[cat].append(a.time_s)

    print(f"\n  Per-Problem Wall Time:")
    print(f"    {'Category':<22} {'N':>5} {'Mean':>8} {'Median':>8} {'P25':>8} {'P75':>8} {'P90':>8}")
    print(f"    {'-'*70}")
    for label, data in [("CORRECT problems", correct_wall), ("WRONG problems", wrong_wall)]:
        if data:
            print(f"    {label:<22} {len(data):>5} {fmt(mean(data)):>8} {fmt(median(data)):>8} {fmt(percentile(data,25)):>8} {fmt(percentile(data,75)):>8} {fmt(percentile(data,90)):>8}")
    if correct_wall and wrong_wall:
        print(f"\n    Wrong problems take {mean(wrong_wall)/mean(correct_wall):.2f}x the time of correct ones")

    print(f"\n  Per-Attempt Time:")
    print(f"    {'Category':<22} {'N':>5} {'Mean':>8} {'Median':>8} {'P25':>8} {'P75':>8} {'P90':>8}")
    print(f"    {'-'*70}")
    for label, data in [("Correct attempts", correct_att), ("Wrong attempts", wrong_att), ("None attempts", none_att)]:
        if data:
            print(f"    {label:<22} {len(data):>5} {fmt(mean(data)):>8} {fmt(median(data)):>8} {fmt(percentile(data,25)):>8} {fmt(percentile(data,75)):>8} {fmt(percentile(data,90)):>8}")


def section_time_buckets(problems):
    print(f"\n{'=' * 80}")
    print("  3. TIME BUCKETS — Accuracy by Duration")
    print("=" * 80)

    buckets = [(0,30,"<30s"), (30,60,"30-60s"), (60,120,"1-2min"), (120,300,"2-5min"), (300,600,"5-10min"), (600,float('inf'),"10min+")]
    data = {l: {"correct":0, "wrong":0, "none":0} for _,_,l in buckets}

    total_att = 0
    for p in problems:
        for a in p.attempts:
            if a.time_s <= 0:
                continue
            total_att += 1
            cat = classify_attempt(a, p)
            for lo, hi, label in buckets:
                if lo <= a.time_s < hi:
                    data[label][cat] += 1
                    break

    print(f"\n  {'Bucket':<10} {'Total':>6} {'%All':>6} {'Corr':>6} {'Wrong':>6} {'None':>6} {'Acc%':>7} {'Acc(ex-None)':>12}")
    print(f"  {'-'*65}")
    for _, _, label in buckets:
        d = data[label]
        t = d["correct"] + d["wrong"] + d["none"]
        if t == 0:
            continue
        acc = 100 * d["correct"] / t
        answered = d["correct"] + d["wrong"]
        acc_ex = 100 * d["correct"] / answered if answered else 0
        print(f"  {label:<10} {t:>6} {100*t/total_att:>5.1f}% {d['correct']:>6} {d['wrong']:>6} {d['none']:>6} {acc:>6.1f}% {acc_ex:>11.1f}%")


def section_by_topic(problems):
    print(f"\n{'=' * 80}")
    print("  4. TIMING BY TOPIC")
    print("=" * 80)

    topic_data = defaultdict(lambda: {"n":0, "correct":0, "wall":[], "right_att":[], "wrong_att":[], "pids":[]})

    for p in problems:
        topic = classify_topic(p)
        td = topic_data[topic]
        td["n"] += 1
        td["pids"].append(p.problem_id)
        if p.correct:
            td["correct"] += 1
        td["wall"].append(p.wall_time)
        for a in p.attempts:
            if a.time_s <= 0:
                continue
            if p.correct:
                td["right_att"].append(a.time_s)
            else:
                td["wrong_att"].append(a.time_s)

    print(f"\n  {'Topic':<18} {'N':>4} {'Corr':>5} {'Acc%':>6} {'AvgWall':>8} {'MedWall':>8} {'AvgAtt(R)':>10} {'AvgAtt(W)':>10} {'Ratio':>7}")
    print(f"  {'-'*85}")
    for topic in sorted(topic_data, key=lambda t: topic_data[t]["n"], reverse=True):
        td = topic_data[topic]
        acc = 100 * td["correct"] / td["n"]
        aw = mean(td["wall"]) if td["wall"] else 0
        mw = median(td["wall"]) if td["wall"] else 0
        ar = mean(td["right_att"]) if td["right_att"] else 0
        awr = mean(td["wrong_att"]) if td["wrong_att"] else 0
        ratio = awr / ar if ar > 0 and awr > 0 else 0
        ratio_s = f"{ratio:.1f}x" if ratio > 0 else "N/A"
        print(f"  {topic:<18} {td['n']:>4} {td['correct']:>5} {acc:>5.1f}% {fmt(aw):>8} {fmt(mw):>8} {fmt(ar):>10} {fmt(awr):>10} {ratio_s:>7}")

    # Wrong problems per topic
    print(f"\n  Wrong problems by topic:")
    for topic in sorted(topic_data, key=lambda t: topic_data[t]["n"], reverse=True):
        td = topic_data[topic]
        wrong = [pid for pid in td["pids"] if not next(p for p in problems if p.problem_id == pid).correct]
        if wrong:
            print(f"    {topic}: {', '.join(wrong)}")

    return topic_data


def section_wave_simulation(problems):
    print(f"\n{'=' * 80}")
    print("  5. WAVE SIMULATION — First 6 Attempts, Consensus >= 4")
    print("=" * 80)

    full_correct = sum(1 for p in problems if p.correct)
    w1_correct = 0
    easy = []
    hard = []

    for p in problems:
        attempts_w1 = p.attempts[:6]
        answers = [a.answer for a in attempts_w1 if a.answer is not None]
        votes = Counter(answers)
        times = [a.time_s for a in attempts_w1 if a.time_s > 0]
        w1_time = max(times) if times else 0

        if votes and votes.most_common(1)[0][1] >= 4:
            w1_answer = votes.most_common(1)[0][0]
            is_right = w1_answer == p.expected
            if is_right:
                w1_correct += 1
            easy.append((p, w1_answer, is_right, w1_time, votes))
        else:
            hard.append((p, votes, w1_time))

    print(f"\n  Full-16 score:     {full_correct}/{len(problems)}")
    print(f"  Wave-1 score:      {w1_correct}/{len(problems)}")
    print(f"  Gap:               {full_correct - w1_correct}")
    print(f"  Easy consensus:    {len(easy)} problems")
    print(f"  Need Wave 2:       {len(hard)} problems")

    w1_total = sum(max(a.time_s for a in p.attempts[:6] if a.time_s > 0) if any(a.time_s > 0 for a in p.attempts[:6]) else 0 for p in problems)
    full_total = sum(p.wall_time for p in problems)
    print(f"\n  Wave 1 time (max of 6 per problem): {fmt(w1_total)}")
    print(f"  Full-16 wall time:                   {fmt(full_total)}")
    print(f"  Time saved (wave-1-only):            {fmt(full_total - w1_total)}")

    # Easy consensus detail
    print(f"\n  --- Easy Consensus ({len(easy)}) ---")
    print(f"  {'PID':<10} {'W1 Ans':>8} {'Exp':>8} {'OK?':<6} {'W1 Time':>8} {'Votes'}")
    print(f"  {'-'*65}")
    easy_wrong = []
    for p, ans, ok, t, v in sorted(easy, key=lambda x: x[0].problem_id):
        vote_s = ", ".join(f"{a}x{c}" for a, c in v.most_common())
        mark = "RIGHT" if ok else "WRONG"
        print(f"  {p.problem_id:<10} {ans:>8} {p.expected:>8} {mark:<6} {fmt(t):>8} {vote_s}")
        if not ok:
            easy_wrong.append(p.problem_id)
    if easy_wrong:
        print(f"\n  WARNING: {len(easy_wrong)} wrong consensus: {', '.join(easy_wrong)}")

    # Hard no-consensus detail
    print(f"\n  --- Need Wave 2 ({len(hard)}) ---")
    print(f"  {'PID':<10} {'Exp':>8} {'Full OK?':<9} {'W1 Time':>8} {'W1 Votes'}")
    print(f"  {'-'*65}")
    hard_full_right = 0
    for p, v, t in sorted(hard, key=lambda x: x[0].problem_id):
        full_ok = "RIGHT" if p.correct else "WRONG"
        if p.correct:
            hard_full_right += 1
        vote_s = ", ".join(f"{a}x{c}" for a, c in v.most_common()) if v else "(all None)"
        print(f"  {p.problem_id:<10} {p.expected:>8} {full_ok:<9} {fmt(t):>8} {vote_s}")

    print(f"\n  Hard problems full-16 got right: {hard_full_right} (these NEED Wave 2)")
    print(f"  Hard problems full-16 also wrong: {len(hard) - hard_full_right}")

    return easy, hard


def section_wasted_time(problems):
    print(f"\n{'=' * 80}")
    print("  6. WASTED TIME ANALYSIS")
    print("=" * 80)

    total_t = 0
    correct_t = 0
    wrong_t = 0
    none_t = 0

    for p in problems:
        for a in p.attempts:
            t = a.time_s if a.time_s > 0 else 0
            total_t += t
            cat = classify_attempt(a, p)
            if cat == "correct":
                correct_t += t
            elif cat == "wrong":
                wrong_t += t
            else:
                none_t += t

    wasted = wrong_t + none_t
    print(f"\n  {'Category':<25} {'Time':>10} {'%':>7}")
    print(f"  {'-'*45}")
    print(f"  {'Correct attempts':<25} {fmt(correct_t):>10} {100*correct_t/total_t:>6.1f}%")
    print(f"  {'Wrong attempts':<25} {fmt(wrong_t):>10} {100*wrong_t/total_t:>6.1f}%")
    print(f"  {'None attempts':<25} {fmt(none_t):>10} {100*none_t/total_t:>6.1f}%")
    print(f"  {'-'*45}")
    print(f"  {'WASTED (wrong+none)':<25} {fmt(wasted):>10} {100*wasted/total_t:>6.1f}%")

    # Wrong problems total wall time
    wrong_wall = sum(p.wall_time for p in problems if not p.correct)
    total_wall = sum(p.wall_time for p in problems)
    print(f"\n  Time on wrong problems (wall): {fmt(wrong_wall)} ({100*wrong_wall/total_wall:.1f}% of total)")

    # Top wasted problems
    print(f"\n  Top 10 most wasteful problems (wrong+none attempt time):")
    print(f"  {'PID':<10} {'OK?':<6} {'Wall':>8} {'Wasted':>8} {'Waste%':>7}")
    print(f"  {'-'*45}")
    waste_per_prob = []
    for p in problems:
        w = sum(a.time_s for a in p.attempts if a.time_s > 0 and classify_attempt(a, p) != "correct")
        waste_per_prob.append((p.problem_id, p.correct, p.wall_time, w))
    waste_per_prob.sort(key=lambda x: -x[3])
    for pid, ok, wall, w in waste_per_prob[:10]:
        pct = 100 * w / wall if wall > 0 else 0
        print(f"  {pid:<10} {'OK' if ok else 'WRONG':<6} {fmt(wall):>8} {fmt(w):>8} {pct:>6.1f}%")


def section_attempt_number(problems):
    print(f"\n{'=' * 80}")
    print("  7. ATTEMPT NUMBER vs ACCURACY")
    print("=" * 80)

    max_att = max(len(p.attempts) for p in problems)
    print(f"\n  {'Att#':>5} {'Total':>6} {'Corr':>6} {'Wrong':>6} {'None':>6} {'Acc%':>7} {'MeanT':>8}")
    print(f"  {'-'*55}")

    for i in range(max_att):
        c = w = n = 0
        times = []
        for p in problems:
            if i < len(p.attempts):
                a = p.attempts[i]
                cat = classify_attempt(a, p)
                if cat == "correct":
                    c += 1
                elif cat == "wrong":
                    w += 1
                else:
                    n += 1
                if a.time_s > 0:
                    times.append(a.time_s)
        total = c + w + n
        if total == 0:
            continue
        acc = 100 * c / total
        mt = mean(times) if times else 0
        print(f"  {i+1:>5} {total:>6} {c:>6} {w:>6} {n:>6} {acc:>6.1f}% {fmt(mt):>8}")

    # Unique correct answers by attempt number
    print(f"\n  Unique correct answers (first appearance) by attempt #:")
    seen = {}
    for p in problems:
        if not p.correct:
            continue
        for i, a in enumerate(p.attempts):
            if a.answer == p.expected and p.problem_id not in seen:
                seen[p.problem_id] = i + 1
                break
    att_counts = Counter(seen.values())
    for att_num in sorted(att_counts):
        print(f"    Attempt {att_num}: {att_counts[att_num]} problems first solved here")


def section_per_problem(problems):
    print(f"\n{'=' * 80}")
    print("  8. PER-PROBLEM WALL TIME (sorted descending)")
    print("=" * 80)

    total = sum(p.wall_time for p in problems)
    cum = 0
    print(f"\n  {'#':>3} {'PID':<10} {'Wall':>8} {'%Tot':>6} {'Cum%':>6} {'OK?':<6} {'Pred':>8} {'Exp':>8} {'Nones':>6} {'Errs':>5} {'Topic':<16}")
    print(f"  {'-'*100}")
    for i, p in enumerate(sorted(problems, key=lambda x: x.wall_time, reverse=True), 1):
        cum += p.wall_time
        nones = sum(1 for a in p.attempts if a.is_none)
        errs = sum(a.errors for a in p.attempts)
        topic = classify_topic(p)
        ok = "OK" if p.correct else "WRONG"
        print(f"  {i:>3} {p.problem_id:<10} {fmt(p.wall_time):>8} {100*p.wall_time/total:>5.1f}% {100*cum/total:>5.1f}% {ok:<6} {str(p.predicted):>8} {str(p.expected):>8} {nones:>6} {errs:>5} {topic:<16}")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} <diagnostic.log>")
        sys.exit(1)

    logfile = sys.argv[1]
    problems = parse_log(logfile)
    print(f"Parsed {len(problems)} problems from {logfile}\n")

    section_overview(problems)
    section_right_vs_wrong(problems)
    section_time_buckets(problems)
    section_by_topic(problems)
    section_wave_simulation(problems)
    section_wasted_time(problems)
    section_attempt_number(problems)
    section_per_problem(problems)

    print(f"\n{'=' * 80}")
    print("  ANALYSIS COMPLETE")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
