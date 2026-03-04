#!/usr/bin/env python3
"""
Deep dive into 6 specific problems from v32 to understand reasoning failures.
Outputs detailed attempt-by-attempt analysis for each problem.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log

TARGET_PIDS = ["23586c", "a824c1", "1ec970", "3b88b3", "a9dbc8", "86e8e5"]

def analyze_problem(problem):
    pid = problem.problem_id
    print(f"\n{'='*100}")
    print(f"PROBLEM {pid}")
    print(f"Expected: {problem.expected}  |  Predicted: {problem.predicted}  |  Correct: {problem.correct}")
    print(f"Wall time: {problem.wall_time:.0f}s  |  Attempts: {len(problem.attempts)}")

    # Vote distribution
    votes = {}
    for att in problem.attempts:
        ans = att.answer
        votes[ans] = votes.get(ans, 0) + 1
    print(f"Vote distribution: {dict(sorted(votes.items(), key=lambda x: -x[1]))}")
    print(f"{'='*100}")

    for att in problem.attempts:
        print(f"\n--- Attempt {att.attempt_num} | Temp: {att.temperature} | Answer: {att.answer} | Turns: {len(att.turns)} | Time: {att.time_s:.0f}s ---")
        correct_mark = " *** CORRECT ***" if str(att.answer) == str(problem.expected) else ""
        print(f"    Answer: {att.answer}{correct_mark}")

        for turn in att.turns:
            # Print reasoning summary (first 500 chars)
            if turn.reasoning_text:
                reasoning_preview = turn.reasoning_text[:2000].replace('\n', '\n    ')
                print(f"  Turn {turn.turn_num} REASONING ({len(turn.reasoning_text)} chars):")
                print(f"    {reasoning_preview}")
                if len(turn.reasoning_text) > 2000:
                    # Also show last 1000 chars (conclusion)
                    conclusion = turn.reasoning_text[-1500:].replace('\n', '\n    ')
                    print(f"    [...{len(turn.reasoning_text)-3500} chars omitted...]")
                    print(f"    {conclusion}")
            if turn.code:
                code_preview = turn.code[:1500].replace('\n', '\n    ')
                print(f"  Turn {turn.turn_num} CODE ({len(turn.code)} chars):")
                print(f"    {code_preview}")
                if len(turn.code) > 1500:
                    print(f"    [...{len(turn.code)-1500} chars omitted...]")
            if turn.output:
                out_preview = turn.output[:1000].replace('\n', '\n    ')
                print(f"  Turn {turn.turn_num} OUTPUT ({len(turn.output)} chars):")
                print(f"    {out_preview}")
            if turn.is_error:
                print(f"  Turn {turn.turn_num} *** ERROR ***")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 six_problem_deep_dive.py <logfile> [problem_id]")
        sys.exit(1)

    logfile = sys.argv[1]
    # Optional: analyze only one problem
    single_pid = sys.argv[2] if len(sys.argv) > 2 else None

    problems = parse_log(logfile)

    targets = [single_pid] if single_pid else TARGET_PIDS

    for pid in targets:
        matching = [p for p in problems if p.problem_id.startswith(pid)]
        if matching:
            analyze_problem(matching[0])
        else:
            print(f"\nWARNING: Problem {pid} not found in log")

if __name__ == "__main__":
    main()
