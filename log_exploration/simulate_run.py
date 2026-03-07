#!/usr/bin/env python3
"""End-to-end simulation of the AIMO3 pipeline using historical log data.

Replays a full 50-problem run through the current budget/config logic to find
bugs before burning an H100 run. Uses real timing data from a previous log.

Usage:
    python3 log_exploration/simulate_run.py output/shiv-latest-3/diagnostic.log
    python3 log_exploration/simulate_run.py output/shiv-latest-3/diagnostic.log --problems 10
    python3 log_exploration/simulate_run.py output/shiv-latest-3/diagnostic.log --verbose
"""
import sys
import argparse
from collections import Counter
from log_exploration.log_query import parse_log


# ─── Current CFG values (mirror cell 8) ───
CFG = {
    'notebook_limit': 17400,
    'problem_timeout': 450,
    'rerun_timeout': 600,
    'reserved_per_problem': 150,
    'wave1_total_budget': 6000,
    'wave1_timeout': 100,
    'wave1_attempts': 42,
    'attempts': 24,
    'workers': 24,
}

RERUN_THRESHOLD_FRAC = 1 / 3  # math.ceil(attempts / 3)


def extract_problem_data(problems):
    """Extract timing/result data from parsed log problems."""
    data = []
    for p in problems:
        w1_wall = p.wave1_time / 42 if p.wave1_time else 0
        is_rerun = len(p.attempts) > 48
        n_attempts = len(p.attempts)

        # Separate R1 and rerun timing
        if is_rerun:
            r1_time = min(p.wall_time, p.budget + 30)
            r2_time = max(0, p.wall_time - r1_time)
        else:
            r1_time = p.wall_time
            r2_time = 0

        # Count answers/nones for rerun trigger simulation
        # Use first `attempts` worth (or 48 from the old config)
        first_round = p.attempts[:48]  # v37 had 48 agents
        votes = Counter(a.answer for a in first_round if a.answer is not None)
        top_votes = votes.most_common(1)[0][1] if votes else 0
        n_nones_r1 = sum(1 for a in first_round if a.answer is None)

        # Wave 1 classification data
        taxonomies = p.wave1_taxonomies if hasattr(p, 'wave1_taxonomies') else []
        is_basic = p.is_basic if hasattr(p, 'is_basic') else False
        notes_chars = p.wave1_notes_chars if hasattr(p, 'wave1_notes_chars') else 0

        # Simulate difficulty (new feature — use heuristic from old logs)
        # basic → easy, has taxonomy+notes → medium, no taxonomy/no notes → hard
        if is_basic:
            sim_difficulty = 'easy'
        elif taxonomies and notes_chars > 0:
            sim_difficulty = 'medium'
        else:
            sim_difficulty = 'hard'

        data.append({
            'pid': p.problem_id,
            'w1_wall': w1_wall,
            'r1_time': r1_time,
            'r2_time': r2_time,
            'total_wall': p.wall_time,
            'is_rerun': is_rerun,
            'correct': p.correct,
            'actual_budget': p.budget,
            'predicted': p.predicted,
            'expected': p.expected,
            'top_votes_r1': top_votes,
            'n_nones_r1': n_nones_r1,
            'n_attempts': n_attempts,
            'taxonomies': taxonomies,
            'is_basic': is_basic,
            'notes_chars': notes_chars,
            'difficulty': sim_difficulty,
        })
    return data


def simulate(data, cfg, verbose=False):
    """Simulate the full pipeline with current config."""
    notebook_limit = cfg['notebook_limit']
    problem_timeout = cfg['problem_timeout']
    rerun_timeout = cfg['rerun_timeout']
    reserved_per_problem = cfg['reserved_per_problem']
    wave1_total_budget = cfg['wave1_total_budget']
    wave1_timeout = cfg['wave1_timeout']
    attempts = cfg['attempts']

    import math
    rerun_threshold = math.ceil(attempts * RERUN_THRESHOLD_FRAC)

    elapsed = 0.0
    wave1_spent = 0.0
    problems_remaining = len(data)
    n_problems = len(data)

    issues = []
    results = []

    for i, d in enumerate(data):
        prob = {'idx': i + 1, 'pid': d['pid'], 'correct': d['correct']}

        # ── Wave 1 Classification ──
        prob['taxonomies'] = d['taxonomies']
        prob['difficulty'] = d['difficulty']
        prob['notes_chars'] = d['notes_chars']
        prob['is_basic'] = d['is_basic']
        # effort set after budget calc below

        # ── Wave 1 Budget ──
        w1_pool_remaining = wave1_total_budget - wave1_spent
        if w1_pool_remaining <= 30:
            w1_budget = 0
            prob['w1_skipped'] = True
            issues.append(f"#{i+1} {d['pid']}: Wave 1 SKIPPED (pool exhausted: {w1_pool_remaining:.0f}s left)")
        else:
            w1_budget = min(w1_pool_remaining / max(1, problems_remaining), wave1_timeout)
            w1_budget = max(w1_budget, 30)
            prob['w1_skipped'] = False

        # Simulate W1 time (use actual, capped at budget)
        w1_actual = min(d['w1_wall'], w1_budget) if w1_budget > 0 else 0
        wave1_spent += w1_actual
        elapsed += w1_actual
        prob['w1_budget'] = w1_budget
        prob['w1_actual'] = w1_actual
        prob['w1_pool_after'] = wave1_total_budget - wave1_spent

        # Check: W1 actual exceeds budget?
        if d['w1_wall'] > w1_budget and w1_budget > 0:
            issues.append(f"#{i+1} {d['pid']}: Wave 1 would overshoot budget ({d['w1_wall']:.0f}s actual > {w1_budget:.0f}s budget)")

        # ── Wave 2 Budget ──
        time_left = notebook_limit - elapsed
        w1_pool_left = max(0, wave1_total_budget - wave1_spent)
        w1_per_est = min(wave1_timeout, w1_pool_left / max(1, problems_remaining))
        reserved = max(0, problems_remaining - 1) * (reserved_per_problem + w1_per_est)
        w2_budget = time_left - reserved
        w2_budget = min(w2_budget, problem_timeout)
        w2_budget = max(w2_budget, 30)

        prob['w2_budget'] = w2_budget
        prob['reserved'] = reserved
        prob['time_left_pre_w2'] = time_left

        # Effort: budget override <=250 → MEDIUM, else difficulty-based
        if w2_budget <= 250:
            prob['effort'] = 'MED'
            prob['effort_reason'] = 'budget'
        elif d['difficulty'] == 'hard':
            prob['effort'] = 'HIGH'
            prob['effort_reason'] = 'hard'
        else:
            prob['effort'] = 'MED'
            prob['effort_reason'] = d['difficulty']

        # Check: time truly out?
        if time_left <= 0:
            issues.append(f"#{i+1} {d['pid']}: OUT OF TIME — would return 0 (elapsed={elapsed:.0f}s > limit={notebook_limit}s)")
            prob['effort'] = prob.get('effort', 'MED')
            prob['w2_actual'] = 0
            prob['rr_budget'] = 0
            prob['rr_actual'] = 0
            prob['rr_fired'] = False
            prob['rr_skipped'] = False
            problems_remaining -= 1
            results.append(prob)
            continue

        # Simulate W2 R1 time
        # Scale actual time: if old budget was 400 and new is less, time might be proportionally less
        # But for simulation, use min(actual, new_budget + 30s overshoot)
        r1_actual = min(d['r1_time'], w2_budget + 30)
        elapsed += r1_actual
        prob['w2_actual'] = r1_actual

        # Check: budget starved?
        if w2_budget <= 30:
            issues.append(f"#{i+1} {d['pid']}: STARVED — only {w2_budget:.0f}s Wave 2 budget")
        elif w2_budget < reserved_per_problem:
            issues.append(f"#{i+1} {d['pid']}: TIGHT — only {w2_budget:.0f}s Wave 2 budget (< reserved_per_problem)")

        # ── Rerun Check ──
        # Simulate: would rerun trigger with new config?
        # Use old data's top_votes but scale to new attempt count
        # Since we can't perfectly simulate 24 vs 48 agents, use a heuristic:
        # If problem reran with 48 agents, it likely would with 24 too (fewer votes = lower threshold)
        would_rerun = d['is_rerun']  # use historical rerun decision as proxy

        prob['rr_fired'] = False
        prob['rr_skipped'] = False
        prob['rr_budget'] = 0
        prob['rr_actual'] = 0

        if would_rerun:
            time_left_rr = notebook_limit - elapsed
            w1_pool_left_rr = max(0, wave1_total_budget - wave1_spent)
            w1_per_est_rr = min(wave1_timeout, w1_pool_left_rr / max(1, problems_remaining))
            reserved_rr = max(0, problems_remaining) * (reserved_per_problem + w1_per_est_rr)
            rr_budget = time_left_rr - reserved_rr
            rr_budget = min(rr_budget, rerun_timeout)
            prob['rr_budget'] = rr_budget

            if rr_budget > reserved_per_problem:
                rr_actual = min(d['r2_time'], rr_budget + 30)
                elapsed += rr_actual
                prob['rr_fired'] = True
                prob['rr_actual'] = rr_actual
            else:
                prob['rr_skipped'] = True
                issues.append(f"#{i+1} {d['pid']}: Rerun SKIPPED (budget={rr_budget:.0f}s < reserved={reserved_per_problem}s)")

        problems_remaining -= 1
        prob['elapsed_after'] = elapsed
        prob['time_remaining'] = notebook_limit - elapsed
        results.append(prob)

    return results, issues


def print_report(results, issues, cfg, data, verbose=False):
    """Print the simulation report."""
    n = len(results)
    import math
    rerun_threshold = math.ceil(cfg['attempts'] * RERUN_THRESHOLD_FRAC)

    print(f'\n{"="*140}')
    print(f'  END-TO-END SIMULATION — {n} problems')
    print(f'  Config: attempts={cfg["attempts"]} w1_pool={cfg["wave1_total_budget"]}s w1_cap={cfg["wave1_timeout"]}s '
          f'reserve={cfg["reserved_per_problem"]}s timeout={cfg["problem_timeout"]}s rerun_timeout={cfg["rerun_timeout"]}s limit={cfg["notebook_limit"]}s '
          f'rerun_thr={rerun_threshold}')
    print(f'{"="*140}')

    # Header
    print(f'\n{"#":>3} {"PID":<8} {"Diff":>4} {"Eff":>4} {"Tax":<30} '
          f'{"W1bud":>6} {"W1act":>6} {"W1pool":>7} {"W2bud":>7} {"W2act":>6} '
          f'{"RR":>4} {"RRbud":>7} {"RRact":>6} {"Elapsed":>8} {"Left":>7} {"OK":>3} {"Issues":<20}')
    print(f'{"─"*3} {"─"*8} {"─"*4} {"─"*4} {"─"*30} '
          f'{"─"*6} {"─"*6} {"─"*7} {"─"*7} {"─"*6} '
          f'{"─"*4} {"─"*7} {"─"*6} {"─"*8} {"─"*7} {"─"*3} {"─"*20}')

    for r in results:
        rr_str = ''
        if r['rr_fired']:
            rr_str = 'YES'
        elif r['rr_skipped']:
            rr_str = 'SKIP'

        row_issues = []
        if r.get('w1_skipped'):
            row_issues.append('W1-SKIP')
        if r['w2_budget'] <= 30:
            row_issues.append('STARVED')
        elif r['w2_budget'] < cfg['reserved_per_problem']:
            row_issues.append('TIGHT')
        if r['rr_skipped']:
            row_issues.append('RR-SKIP')
        if r.get('time_remaining', 99999) < 0:
            row_issues.append('OVERTIME')

        issue_str = ', '.join(row_issues)
        marker = ' ***' if row_issues else ''

        # Taxonomy display (truncate to fit)
        tax_list = r.get('taxonomies', [])
        if tax_list:
            tax_str = ', '.join(t.split('.')[-1] for t in tax_list[:2])
        elif r.get('is_basic'):
            tax_str = 'basic'
        elif r.get('w1_skipped'):
            tax_str = '(skipped)'
        else:
            tax_str = '(no consensus)'
        if len(tax_str) > 28:
            tax_str = tax_str[:26] + '..'

        diff_str = r.get('difficulty', '?')[:3].upper()
        eff_str = r.get('effort', '?')

        print(f'{r["idx"]:>3} {r["pid"]:<8} {diff_str:>4} {eff_str:>4} {tax_str:<30} '
              f'{r["w1_budget"]:>5.0f}s {r["w1_actual"]:>5.0f}s {r["w1_pool_after"]:>6.0f}s '
              f'{r["w2_budget"]:>6.0f}s {r["w2_actual"]:>5.0f}s {rr_str:>4} {r["rr_budget"]:>6.0f}s {r["rr_actual"]:>5.0f}s '
              f'{r["elapsed_after"]:>7.0f}s {r["time_remaining"]:>6.0f}s '
              f'{("Y" if r["correct"] else "N"):>3} {issue_str}{marker}')

    # ── Summary ──
    print(f'\n{"="*140}')
    print(f'  SUMMARY')
    print(f'{"="*140}')

    final = results[-1] if results else None
    w1_total = sum(r['w1_actual'] for r in results)
    w2_budgets = [r['w2_budget'] for r in results]
    starved = sum(1 for r in results if r['w2_budget'] <= 30)
    tight = sum(1 for r in results if 30 < r['w2_budget'] < cfg['reserved_per_problem'])
    rr_fired = sum(1 for r in results if r['rr_fired'])
    rr_skipped = sum(1 for r in results if r['rr_skipped'])
    w1_skipped = sum(1 for r in results if r.get('w1_skipped'))
    correct = sum(1 for r in results if r['correct'])

    print(f'  Score: {correct}/{n}')
    print(f'  Total elapsed: {final["elapsed_after"]:.0f}s ({final["elapsed_after"]/60:.0f} min) / {cfg["notebook_limit"]}s ({cfg["notebook_limit"]/60:.0f} min)')
    print(f'  Time remaining: {final["time_remaining"]:.0f}s ({final["time_remaining"]/60:.0f} min)')
    print()

    # Difficulty / Effort breakdown
    diff_counts = Counter(r.get('difficulty', '?') for r in results)
    eff_counts = Counter(r.get('effort', '?') for r in results)
    print(f'  Difficulty distribution: {dict(diff_counts)}')
    print(f'  Effort distribution: {dict(eff_counts)}')
    for diff in ['easy', 'medium', 'hard']:
        diff_problems = [r for r in results if r.get('difficulty') == diff]
        if diff_problems:
            diff_correct = sum(1 for r in diff_problems if r['correct'])
            print(f'    {diff.upper():>6}: {diff_correct}/{len(diff_problems)} correct, effort={diff_problems[0].get("effort", "?")}')
    print()
    print(f'  Wave 1:')
    print(f'    Total used: {w1_total:.0f}/{cfg["wave1_total_budget"]}s ({w1_total/cfg["wave1_total_budget"]*100:.0f}%)')
    print(f'    Skipped: {w1_skipped} problems')
    has_tax = sum(1 for r in results if r.get('taxonomies'))
    no_tax = sum(1 for r in results if not r.get('taxonomies') and not r.get('w1_skipped'))
    print(f'    With taxonomy: {has_tax} | No consensus: {no_tax} | Skipped: {w1_skipped}')
    print()
    print(f'  Wave 2 budget distribution:')
    print(f'    Starved (<=30s): {starved}')
    print(f'    Tight (<{cfg["reserved_per_problem"]}s): {tight}')
    print(f'    OK (>={cfg["reserved_per_problem"]}s): {n - starved - tight}')
    if w2_budgets:
        print(f'    Min: {min(w2_budgets):.0f}s  Max: {max(w2_budgets):.0f}s  Median: {sorted(w2_budgets)[len(w2_budgets)//2]:.0f}s')
    print()
    print(f'  Reruns:')
    print(f'    Fired: {rr_fired}')
    print(f'    Skipped (budget too low): {rr_skipped}')
    rr_time = sum(r['rr_actual'] for r in results)
    print(f'    Total rerun time: {rr_time:.0f}s ({rr_time/60:.0f} min)')

    # ── Issues ──
    if issues:
        print(f'\n{"="*140}')
        print(f'  ISSUES DETECTED ({len(issues)})')
        print(f'{"="*140}')
        for issue in issues:
            print(f'  ! {issue}')
    else:
        print(f'\n  No issues detected.')

    # ── Sanity Checks ──
    print(f'\n{"="*140}')
    print(f'  SANITY CHECKS')
    print(f'{"="*140}')

    checks = []

    # Check 1: No overtime
    if final and final['time_remaining'] < 0:
        checks.append(('FAIL', f'Overtime by {-final["time_remaining"]:.0f}s'))
    else:
        checks.append(('PASS', f'Finished with {final["time_remaining"]:.0f}s remaining'))

    # Check 2: No starved problems
    if starved > 0:
        checks.append(('FAIL', f'{starved} problems starved to <=30s'))
    else:
        checks.append(('PASS', 'No starved problems'))

    # Check 3: Wave 1 pool not exhausted
    final_pool = results[-1]['w1_pool_after'] if results else cfg['wave1_total_budget']
    if final_pool <= 30:
        checks.append(('WARN', f'Wave 1 pool exhausted ({final_pool:.0f}s left)'))
    else:
        checks.append(('PASS', f'Wave 1 pool has {final_pool:.0f}s remaining'))

    # Check 4: All problems got at least reserved_per_problem budget
    under_reserve = sum(1 for r in results if r['w2_budget'] < cfg['reserved_per_problem'])
    if under_reserve > 0:
        checks.append(('WARN', f'{under_reserve} problems got less than reserved_per_problem ({cfg["reserved_per_problem"]}s)'))
    else:
        checks.append(('PASS', f'All problems got >= {cfg["reserved_per_problem"]}s budget'))

    # Check 5: Reruns that were skipped — were they needed?
    rr_skipped_correct = sum(1 for r, d in zip(results, data) if r['rr_skipped'] and d['correct'])
    rr_skipped_wrong = sum(1 for r, d in zip(results, data) if r['rr_skipped'] and not d['correct'])
    if rr_skipped > 0:
        checks.append(('INFO', f'Skipped reruns: {rr_skipped_correct} were correct anyway, {rr_skipped_wrong} were wrong (might have helped)'))

    # Check 6: Time utilization
    utilization = final['elapsed_after'] / cfg['notebook_limit'] * 100 if final else 0
    if utilization < 70:
        checks.append(('WARN', f'Low time utilization: {utilization:.0f}% — budget may be too conservative'))
    elif utilization > 95:
        checks.append(('WARN', f'Very high utilization: {utilization:.0f}% — tight, may overtime with variance'))
    else:
        checks.append(('PASS', f'Time utilization: {utilization:.0f}%'))

    for status, msg in checks:
        icon = {'PASS': 'OK', 'FAIL': '!!', 'WARN': '??', 'INFO': '--'}[status]
        print(f'  [{icon}] {msg}')

    print(f'\n{"="*140}')


def main():
    parser = argparse.ArgumentParser(description='End-to-end pipeline simulation')
    parser.add_argument('logfile', help='Path to diagnostic.log')
    parser.add_argument('--problems', type=int, default=50, help='Number of problems to simulate (default: 50)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose per-problem output')
    parser.add_argument('--attempts', type=int, default=None, help='Override attempts count')
    parser.add_argument('--wave1-pool', type=int, default=None, help='Override wave1_total_budget')
    parser.add_argument('--reserve', type=int, default=None, help='Override reserved_per_problem')
    parser.add_argument('--timeout', type=int, default=None, help='Override problem_timeout')
    parser.add_argument('--limit', type=int, default=None, help='Override notebook_limit')
    args = parser.parse_args()

    cfg = dict(CFG)
    if args.attempts is not None:
        cfg['attempts'] = args.attempts
    if args.wave1_pool is not None:
        cfg['wave1_total_budget'] = args.wave1_pool
    if args.reserve is not None:
        cfg['reserved_per_problem'] = args.reserve
    if args.timeout is not None:
        cfg['problem_timeout'] = args.timeout
    if args.limit is not None:
        cfg['notebook_limit'] = args.limit

    problems = parse_log(args.logfile)
    if len(problems) == 0:
        print('No problems found in log.')
        sys.exit(1)

    data = extract_problem_data(problems[:args.problems])
    results, issues = simulate(data, cfg, verbose=args.verbose)
    print_report(results, issues, cfg, data, verbose=args.verbose)


if __name__ == '__main__':
    main()
