#!/usr/bin/env python3
"""Time distribution grouped by topic, correct/wrong, and other dimensions.

Sections:
1. Per-topic: correct vs wrong time stats
2. Per-topic: attempt-level time (correct answer vs wrong answer vs None)
3. Time efficiency: time-per-correct-vote by topic
4. Slowest/fastest problems by topic
5. Time budget utilization by topic
6. Cross-tabulation: topic x status x time bucket
7. "Time wasted" by topic (time on wrong problems)
8. Per-problem detail sorted by topic then time

Usage:
    python3 log_exploration/time_by_topic_status.py output/shiv-latest-2/diagnostic.log
"""

import sys
import os
import math
from collections import defaultdict, Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from log_exploration.log_query import parse_log
from log_exploration.topic_analysis import classify_problem


def percentiles(values, pcts=(10, 25, 50, 75, 90)):
    if not values:
        return {}
    s = sorted(values)
    n = len(s)
    result = {}
    for p in pcts:
        k = (p / 100) * (n - 1)
        f, c = math.floor(k), math.ceil(k)
        result[p] = s[f] if f == c else s[f] * (c - k) + s[c] * (k - f)
    return result


def fmt(s):
    if s >= 3600: return f"{s/3600:.1f}h"
    if s >= 60: return f"{s/60:.1f}m"
    return f"{s:.0f}s"


def get_primary_topic(problem):
    matches = classify_problem(problem.problem_text)
    return matches[0][0] if matches else "Other"


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <diagnostic.log>")
        sys.exit(1)

    problems = parse_log(sys.argv[1])
    n = len(problems)
    total_correct = sum(1 for p in problems if p.correct)

    # Classify
    topic_map = {}
    for p in problems:
        topic_map[p.problem_id] = get_primary_topic(p)

    all_topics = sorted(set(topic_map.values()))

    # ═══════════════════════════════════════════════════════════════
    # Section 1: Per-topic problem-level time (correct vs wrong)
    # ═══════════════════════════════════════════════════════════════
    print("=" * 90)
    print(f"  TIME BY TOPIC & STATUS — {n} problems, {total_correct}/{n} correct")
    print("=" * 90)

    print(f"\n  SECTION 1: PROBLEM WALL TIME BY TOPIC (correct vs wrong)")
    print(f"  {'─'*85}")
    print(f"  {'Topic':<25} {'N':>3} {'C':>3} {'W':>3} {'C_mean':>7} {'C_med':>6} {'W_mean':>7} {'W_med':>6} {'Total':>7}")
    print(f"  {'─'*25} {'─'*3} {'─'*3} {'─'*3} {'─'*7} {'─'*6} {'─'*7} {'─'*6} {'─'*7}")

    topic_data = {}
    for topic in all_topics:
        tp = [p for p in problems if topic_map[p.problem_id] == topic]
        correct_p = [p for p in tp if p.correct]
        wrong_p = [p for p in tp if not p.correct]
        ct = [p.wall_time for p in correct_p if p.wall_time]
        wt = [p.wall_time for p in wrong_p if p.wall_time]
        total_t = sum(p.wall_time for p in tp if p.wall_time)

        topic_data[topic] = {'problems': tp, 'correct': correct_p, 'wrong': wrong_p,
                             'correct_times': ct, 'wrong_times': wt, 'total_time': total_t}

        c_mean = f"{sum(ct)/len(ct):.0f}s" if ct else "  --"
        c_med = f"{sorted(ct)[len(ct)//2]:.0f}s" if ct else " --"
        w_mean = f"{sum(wt)/len(wt):.0f}s" if wt else "  --"
        w_med = f"{sorted(wt)[len(wt)//2]:.0f}s" if wt else " --"

        print(f"  {topic:<25} {len(tp):>3} {len(correct_p):>3} {len(wrong_p):>3} "
              f"{c_mean:>7} {c_med:>6} {w_mean:>7} {w_med:>6} {fmt(total_t):>7}")

    # Totals
    all_ct = [p.wall_time for p in problems if p.correct and p.wall_time]
    all_wt = [p.wall_time for p in problems if not p.correct and p.wall_time]
    print(f"  {'─'*85}")
    c_mean = f"{sum(all_ct)/len(all_ct):.0f}s" if all_ct else "--"
    w_mean = f"{sum(all_wt)/len(all_wt):.0f}s" if all_wt else "--"
    total_all = sum(p.wall_time for p in problems if p.wall_time)
    print(f"  {'ALL':<25} {n:>3} {total_correct:>3} {n-total_correct:>3} "
          f"{c_mean:>7} {'':>6} {w_mean:>7} {'':>6} {fmt(total_all):>7}")

    # ═══════════════════════════════════════════════════════════════
    # Section 2: Per-topic attempt-level time breakdown
    # ═══════════════════════════════════════════════════════════════
    print(f"\n  SECTION 2: ATTEMPT TIME BY TOPIC (correct_answer vs wrong_answer vs None)")
    print(f"  {'─'*90}")
    print(f"  {'Topic':<25} {'CorrectAns':>10} {'c_mean':>7} {'WrongAns':>10} {'w_mean':>7} {'Nones':>7} {'n_mean':>7} {'TotalAtt':>8}")
    print(f"  {'─'*25} {'─'*10} {'─'*7} {'─'*10} {'─'*7} {'─'*7} {'─'*7} {'─'*8}")

    for topic in all_topics:
        td = topic_data[topic]
        c_times, w_times, n_times = [], [], []
        total_att = 0
        for p in td['problems']:
            for a in p.attempts:
                total_att += 1
                if a.answer is None:
                    n_times.append(a.time_s)
                elif p.expected is not None and str(a.answer) == str(p.expected):
                    c_times.append(a.time_s)
                else:
                    w_times.append(a.time_s)

        cm = f"{sum(c_times)/len(c_times):.0f}s" if c_times else " --"
        wm = f"{sum(w_times)/len(w_times):.0f}s" if w_times else " --"
        nm = f"{sum(n_times)/len(n_times):.0f}s" if n_times else " --"
        print(f"  {topic:<25} {len(c_times):>10} {cm:>7} {len(w_times):>10} {wm:>7} "
              f"{len(n_times):>7} {nm:>7} {total_att:>8}")

    # ═══════════════════════════════════════════════════════════════
    # Section 3: Time efficiency — seconds per correct vote
    # ═══════════════════════════════════════════════════════════════
    print(f"\n  SECTION 3: TIME EFFICIENCY — seconds per correct vote by topic")
    print(f"  {'─'*75}")
    print(f"  {'Topic':<25} {'TotalTime':>10} {'CorrectVotes':>12} {'Sec/Vote':>10} {'Accuracy':>10}")
    print(f"  {'─'*25} {'─'*10} {'─'*12} {'─'*10} {'─'*10}")

    for topic in all_topics:
        td = topic_data[topic]
        total_time = td['total_time']
        correct_votes = 0
        total_votes = 0
        for p in td['problems']:
            for a in p.attempts:
                if a.answer is not None:
                    total_votes += 1
                    if p.expected is not None and str(a.answer) == str(p.expected):
                        correct_votes += 1
        spv = f"{total_time/correct_votes:.1f}s" if correct_votes > 0 else "inf"
        acc = f"{correct_votes*100/total_votes:.0f}%" if total_votes > 0 else "--"
        print(f"  {topic:<25} {fmt(total_time):>10} {correct_votes:>12} {spv:>10} {acc:>10}")

    # ═══════════════════════════════════════════════════════════════
    # Section 4: Slowest and fastest problems by topic
    # ═══════════════════════════════════════════════════════════════
    print(f"\n  SECTION 4: SLOWEST & FASTEST PROBLEMS BY TOPIC")
    print(f"  {'─'*90}")

    for topic in all_topics:
        td = topic_data[topic]
        sorted_p = sorted(td['problems'], key=lambda p: p.wall_time, reverse=True)
        print(f"\n  {topic} ({len(td['problems'])} problems, {len(td['correct'])}/{len(td['problems'])} correct):")

        # Show top 3 slowest and 3 fastest
        show_n = min(3, len(sorted_p))
        print(f"    Slowest:")
        for p in sorted_p[:show_n]:
            status = "OK" if p.correct else "WRONG"
            votes = Counter(a.answer for a in p.attempts if a.answer is not None)
            top_v = votes.most_common(1)[0][1] if votes else 0
            n_none = sum(1 for a in p.attempts if a.answer is None)
            print(f"      {p.problem_id[:8]}: {fmt(p.wall_time):>6} [{status:5s}] top_votes={top_v}, nones={n_none}")

        print(f"    Fastest:")
        for p in sorted_p[-show_n:]:
            status = "OK" if p.correct else "WRONG"
            votes = Counter(a.answer for a in p.attempts if a.answer is not None)
            top_v = votes.most_common(1)[0][1] if votes else 0
            print(f"      {p.problem_id[:8]}: {fmt(p.wall_time):>6} [{status:5s}] top_votes={top_v}")

    # ═══════════════════════════════════════════════════════════════
    # Section 5: Time bucket cross-tabulation
    # ═══════════════════════════════════════════════════════════════
    print(f"\n  SECTION 5: TIME BUCKET × TOPIC × STATUS")
    print(f"  {'─'*90}")

    buckets = [(0, 120, "<2min"), (120, 240, "2-4min"), (240, 360, "4-6min"),
               (360, 480, "6-8min"), (480, 9999, "8min+")]

    header = f"  {'Topic':<25}"
    for _, _, label in buckets:
        header += f" {label+'-C':>7} {label+'-W':>7}"
    print(header)
    print(f"  {'─'*25}" + f" {'─'*7} {'─'*7}" * len(buckets))

    for topic in all_topics:
        td = topic_data[topic]
        row = f"  {topic:<25}"
        for lo, hi, _ in buckets:
            c = sum(1 for p in td['correct'] if lo <= p.wall_time < hi)
            w = sum(1 for p in td['wrong'] if lo <= p.wall_time < hi)
            row += f" {c:>7} {w:>7}"
        print(row)

    # Totals row
    row = f"  {'TOTAL':<25}"
    for lo, hi, _ in buckets:
        c = sum(1 for p in problems if p.correct and lo <= p.wall_time < hi)
        w = sum(1 for p in problems if not p.correct and lo <= p.wall_time < hi)
        row += f" {c:>7} {w:>7}"
    print(f"  {'─'*25}" + f" {'─'*7} {'─'*7}" * len(buckets))
    print(row)

    # ═══════════════════════════════════════════════════════════════
    # Section 6: Time wasted by topic
    # ═══════════════════════════════════════════════════════════════
    print(f"\n  SECTION 6: TIME WASTED BY TOPIC (time on wrong problems)")
    print(f"  {'─'*80}")
    print(f"  {'Topic':<25} {'Wrong':>5} {'WastedTime':>10} {'%ofTopic':>8} {'%ofTotal':>8}")
    print(f"  {'─'*25} {'─'*5} {'─'*10} {'─'*8} {'─'*8}")

    for topic in all_topics:
        td = topic_data[topic]
        wasted = sum(p.wall_time for p in td['wrong'] if p.wall_time)
        pct_topic = wasted * 100 / td['total_time'] if td['total_time'] > 0 else 0
        pct_total = wasted * 100 / total_all if total_all > 0 else 0
        print(f"  {topic:<25} {len(td['wrong']):>5} {fmt(wasted):>10} {pct_topic:>7.1f}% {pct_total:>7.1f}%")

    total_wasted = sum(p.wall_time for p in problems if not p.correct and p.wall_time)
    print(f"  {'─'*80}")
    print(f"  {'TOTAL':<25} {n-total_correct:>5} {fmt(total_wasted):>10} "
          f"{total_wasted*100/total_all:>7.1f}% {total_wasted*100/total_all:>7.1f}%")

    # ═══════════════════════════════════════════════════════════════
    # Section 7: Per-problem detail (grouped by topic, sorted by time)
    # ═══════════════════════════════════════════════════════════════
    print(f"\n  SECTION 7: ALL PROBLEMS (grouped by topic, sorted by wall time desc)")
    print(f"  {'─'*100}")

    for topic in all_topics:
        td = topic_data[topic]
        sorted_p = sorted(td['problems'], key=lambda p: p.wall_time, reverse=True)
        print(f"\n  ── {topic} ({len(td['correct'])}/{len(td['problems'])} correct) ──")
        print(f"  {'PID':<10} {'Wall':>6} {'Status':<6} {'Pred':>7} {'Exp':>7} {'TopV':>5} {'Nones':>5} "
              f"{'AvgAtt':>7} {'Errors':>6} {'P50att':>7}")
        print(f"  {'─'*10} {'─'*6} {'─'*6} {'─'*7} {'─'*7} {'─'*5} {'─'*5} {'─'*7} {'─'*6} {'─'*7}")

        for p in sorted_p:
            status = "OK" if p.correct else "WRONG"
            votes = Counter(a.answer for a in p.attempts if a.answer is not None)
            top_v = votes.most_common(1)[0][1] if votes else 0
            n_none = sum(1 for a in p.attempts if a.answer is None)
            att_times = [a.time_s for a in p.attempts if a.time_s > 0]
            avg_att = sum(att_times) / len(att_times) if att_times else 0
            med_att = sorted(att_times)[len(att_times)//2] if att_times else 0
            n_errors = sum(1 for a in p.attempts for t in a.turns if t.is_error)
            print(f"  {p.problem_id[:8]:<10} {fmt(p.wall_time):>6} {status:<6} {p.predicted:>7} {p.expected:>7} "
                  f"{top_v:>5} {n_none:>5} {fmt(avg_att):>7} {n_errors:>6} {fmt(med_att):>7}")

    # ═══════════════════════════════════════════════════════════════
    # Section 8: Summary insights
    # ═══════════════════════════════════════════════════════════════
    print(f"\n  SECTION 8: INSIGHTS")
    print(f"  {'─'*80}")

    # Which topic wastes most time?
    worst_topic = max(all_topics, key=lambda t: sum(p.wall_time for p in topic_data[t]['wrong'] if p.wall_time))
    worst_wasted = sum(p.wall_time for p in topic_data[worst_topic]['wrong'] if p.wall_time)
    print(f"  Most time wasted: {worst_topic} ({fmt(worst_wasted)} on {len(topic_data[worst_topic]['wrong'])} wrong problems)")

    # Which topic has best accuracy?
    best_topic = max(all_topics, key=lambda t: len(topic_data[t]['correct'])/max(len(topic_data[t]['problems']),1))
    bt = topic_data[best_topic]
    print(f"  Best accuracy: {best_topic} ({len(bt['correct'])}/{len(bt['problems'])})")

    # Wrong problems take longer?
    if all_ct and all_wt:
        print(f"  Correct problems: mean={sum(all_ct)/len(all_ct):.0f}s, Wrong: mean={sum(all_wt)/len(all_wt):.0f}s "
              f"({'wrong take longer' if sum(all_wt)/len(all_wt) > sum(all_ct)/len(all_ct) else 'correct take longer'})")

    # Fastest wrong problem (maybe timeout issue?)
    wrong_sorted = sorted([p for p in problems if not p.correct], key=lambda p: p.wall_time)
    if wrong_sorted:
        fastest_wrong = wrong_sorted[0]
        print(f"  Fastest wrong: {fastest_wrong.problem_id[:8]} ({fmt(fastest_wrong.wall_time)}) — "
              f"topic={topic_map[fastest_wrong.problem_id]}, pred={fastest_wrong.predicted}, exp={fastest_wrong.expected}")

    # Slowest correct problem
    correct_sorted = sorted([p for p in problems if p.correct], key=lambda p: p.wall_time, reverse=True)
    if correct_sorted:
        slowest_correct = correct_sorted[0]
        print(f"  Slowest correct: {slowest_correct.problem_id[:8]} ({fmt(slowest_correct.wall_time)}) — "
              f"topic={topic_map[slowest_correct.problem_id]}")

    print(f"\n{'='*90}")


if __name__ == '__main__':
    main()
