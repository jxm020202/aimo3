```
# GPU Timing & Utilization Analysis — v23
# Log: output/v23/diagnostic.log
# Problems: 97, Attempts: 1552
# Run time: 313.5 min, Target: 300 min

==============================================================================
  1. PER-PROBLEM TIMING DISTRIBUTION
==============================================================================

  Total problems: 97
  Total wall time (sum): 5.2h

  Metric                    Value
  ---                         ---
  Min                       11.2s
  P10                       37.6s
  P25                        1.2m
  Median                     2.6m
  Mean                       3.2m
  P75                        4.7m
  P90                        5.5m
  P95                        7.0m
  Max                       15.4m
  Stdev                      2.7m

  Wall Time Histogram:
     <1min | ################# (17)
    1-2min | ####################### (23)
    2-3min | ############# (13)
    3-4min | ########### (11)
    4-5min | ############ (12)
    5-7min | ################ (16)
   7-10min | # (1)
    10min+ | #### (4)

  Top 15 Time Hogs:
  Rank Problem        Time   OK  Att   ES
   --- ---             ---  ---  ---  ---
     1 c19295        15.4m    Y   16    N
     2 86e8e5        13.5m    Y   16    N
     3 86e8e5        11.9m    N   16    N
     4 aff75c        10.2m    N   16    N
     5 dbbfe8         7.9m    N   16    Y
     6 9bfdb0         6.8m    Y   16    Y
     7 ba89f9         6.5m    Y   16    Y
     8 a9dbc8         6.5m    N   16    Y
     9 aff75c         5.9m    N   16    N
    10 ae2add         5.5m    N   16    N
    11 86e8e5         5.5m    N   16    N
    12 26bee3         5.5m    N   16    N
    13 dbbfe8         5.5m    N   16    N
    14 a9dbc8         5.5m    N   16    N
    15 21fb4e         5.5m    N   16    N

  Correct vs Wrong Problem Timing:
  Category         Count     Mean   Median      P90      Total
  ---                ---      ---      ---      ---        ---
  Correct             65     2.6m     2.0m     4.8m       2.8h
  Wrong               32     4.5m     4.9m     6.4m       2.4h

==============================================================================
  2. PER-ATTEMPT TIMING DISTRIBUTION
==============================================================================

  Total attempts with timing: 1552
  Sum of attempt times: 63.5h

  Metric                    Value
  ---                         ---
  Min                        2.4s
  P10                       26.9s
  P25                       47.2s
  Median                     1.8m
  Mean                       2.5m
  P75                        3.7m
  P90                        5.0m
  P95                        5.8m
  Max                       15.4m

  Attempt Duration Histogram:
       <5s | #### (4)
     5-10s | ################## (18)
    10-20s | ############################################################## (62)
    20-30s | ################################################################################... (106)
    30-45s | ################################################################################... (183)
    45-60s | ################################################################################... (117)
    60-90s | ################################################################################... (182)
   90-120s | ################################################################################... (174)
     120s+ | ################################################################################... (706)

  Timing by Attempt Number:
   Att#  Count     Mean   Median      P90
    ---    ---      ---      ---      ---
      1     97     2.5m     2.0m     5.0m
      2     97     2.5m     1.8m     5.1m
      3     97     2.4m     1.9m     5.0m
      4     97     2.4m     1.8m     5.0m
      5     97     2.5m     1.7m     5.1m
      6     97     2.5m     1.8m     5.1m
      7     97     2.5m     1.7m     5.0m
      8     97     2.6m     1.7m     5.2m
      9     97     2.5m     1.8m     5.0m
     10     97     2.2m     1.8m     4.7m
     11     97     2.3m     1.7m     5.0m
     12     97     2.4m     1.7m     5.0m
     13     97     2.4m     1.8m     5.1m
     14     97     2.3m     1.7m     5.0m
     15     97     2.5m     1.7m     5.0m
     16     97     2.8m     2.0m     5.5m

==============================================================================
  3. TIME SPENT BY ATTEMPT OUTCOME (None / Correct / Wrong)
==============================================================================

  Outcome               Count     Mean   Median      P90      Total   % Time
  ---                     ---      ---      ---      ---        ---      ---
  Correct Answer          337     1.7m     1.2m     3.7m       9.7h    15.3%
  Wrong Answer            296     3.2m     2.6m     7.1m      16.0h    25.2%
  None (no answer)        919     2.5m     1.9m     5.0m      37.8h    59.5%
  ---                     ---                                   ---      ---
  TOTAL                  1552                                 63.5h   100.0%

  None attempts average 2.5m, correct average 1.7m.
  None/Correct time ratio: 1.43x

  Time on WRONG problems (32 problems): 2.4h
  Problem        Time  Att  None  Predicted   Expected
  ---             ---  ---   ---        ---        ---
  86e8e5        11.9m   16     1      96985       8687
  aff75c        10.2m   16     0       3600       3571
  dbbfe8         7.9m   16     6          8         22
  a9dbc8         6.5m   16     8      15743      15744
  aff75c         5.9m   16    12       3165       3571
  ae2add         5.5m   16     7      19945      24931
  86e8e5         5.5m   16    14      40958       8687
  26bee3         5.5m   16    11        136        108
  dbbfe8         5.5m   16    12          8         22
  a9dbc8         5.5m   16    12          2      15744
  21fb4e         5.5m   16    10         17         16
  1ec970         5.5m   16    14       9900       8700
  1ec970         5.4m   16    11       5000       8700
  21fb4e         5.4m   16     8         17         16
  26bee3         5.2m   16    10         97        108
  29714f         5.0m   16     8         99        297
  3980cd         4.8m   16     8        642         46
  3980cd         4.7m   16     6        642         46
  a824c1         4.4m   16     9         13         24
  29714f         4.0m   16     8         99        297
  a824c1         3.8m   16     8         13         24
  9010d9         3.3m   16    11       6400      10320
  89c921         3.1m   16    11      39601      29800
  ae2add         2.7m   16     9      19945      24931
  9010d9         2.3m   16    10       6400      10320
  3b88b3         1.9m   16    11        982        979
  3b88b3         1.7m   16    11        982        979
  23586c         1.3m   16    11        773        386
  673b29         1.3m   16    10       3032          3
  414a5b         1.2m   16     9         95         42
  673b29        41.7s   16    10       3032          3
  23586c        36.0s   16     9        773        386

==============================================================================
  4. EARLY STOP ANALYSIS
==============================================================================

  Early-stopped: 82/97 (84.5%)
  Not early-stopped: 15/97 (15.5%)

  Attempts per Problem (Early-Stopped vs Not):
  Category                   Count   Mean  Min  Max Median
  ---                          ---    ---  ---  ---    ---
  Early-stopped                 82   16.0   16   16     16
  Not early-stopped             15   16.0   16   16     16

  Distribution of Attempt Counts:
   #Attempts  #Problems     ES    !ES
         ---        ---    ---    ---
          16         97     82     15

  Time consumed by early-stopped problems: 3.4h
  Time consumed by non-early-stopped problems: 1.8h
  Avg time per attempt (non-ES): 27.7s
  Hypothetical if ES problems ran 16: 10.1h
  Time saved by early stop: ~6.7h

  Correctness:
  Early-stopped: 62/82 correct (75.6%)
  Not early-stopped: 3/15 correct (20.0%)

  Early Stop Threshold Simulation (# matching answers to trigger):
   Threshold  ES Problems    Score   Time Saved
         ---          ---      ---          ---
           3           90    62/97        25.8h
           4           86    64/97        15.4h
           5           82    64/97         7.6h
           6            6    64/97        12.5m
           7            1    64/97         0.0s

==============================================================================
  5. TOKEN USAGE PER ATTEMPT
==============================================================================

  Overall Token Stats (1552 attempts):
  Metric                    Value
  ---                         ---
  Min                         201
  P25                        3.4K
  Median                     7.2K
  Mean                       9.2K
  P75                       13.3K
  P90                       19.2K
  Max                       48.5K
  Total                     14.3M

  Tokens by Outcome:
  Outcome               Count       Mean     Median        P90        Total      %
  ---                     ---        ---        ---        ---          ---    ---
  Correct                 337       7.2K       5.2K      15.6K         2.4M  16.9%
  Wrong                   296      12.3K      10.2K      24.5K         3.6M  25.5%
  None                    919       9.0K       7.0K      19.1K         8.2M  57.6%

  Token Throughput (tokens/second) by Outcome:
  Correct: mean=74/s, median=75/s
  Wrong: mean=69/s, median=73/s
  None: mean=65/s, median=70/s

  Success Rate by Token Bucket:
  Bucket      Total  Correct     Rate
  ---           ---      ---      ---
  <500            4        0     0.0%
  500-1K         17       16    94.1%
  1-2K           49       39    79.6%
  2-4K          110       78    70.9%
  4-8K          160       92    57.5%
  8-16K         186       79    42.5%
  16K+          107       33    30.8%

==============================================================================
  6. PARALLELISM ANALYSIS (16 workers, 16 attempts/problem)
==============================================================================

  Configuration: 16 workers, problems processed in parallel batches
  Total wall time (from run): 313.5 min (from user context)
  Sum of problem wall times: 5.2h
  Sum of all attempt times: 63.5h
  Total attempts: 1552

  Per-Problem: Wall Time vs Sum of Attempt Times
  (If attempts run in parallel, wall_time ~ max(attempt_times))

  Problem        Wall   Sum(att)   Max(att)  Wall/Sum  Wall/Max  #Att
  ---             ---        ---        ---       ---       ---   ---
  3cf8bf        37.3s       9.1m      37.1s      0.07      1.01    16
  d6f389        39.7s       3.0m      39.5s      0.22      1.01    16
  32690e        21.9s       4.3m      21.8s      0.09      1.00    16
  12a146        22.8s       5.7m      22.7s      0.07      1.00    16
  481584        28.3s       7.1m      28.2s      0.07      1.00    16
  ...
  aff75c        10.2m       1.8h      10.2m      0.09      1.00    16
  bad5bf         2.3m      23.3m       2.3m      0.10      1.00    16
  c19295        15.4m       1.5h      15.4m      0.17      1.00    16
  c4d8d5         2.0m      20.8m       2.0m      0.10      1.00    16
  1ec970         5.5m       1.3h       5.5m      0.07      1.00    16

  Wall/Max(attempt) ratio stats:
    Mean:   1.00
    Median: 1.00
    Min:    1.00
    Max:    1.01

  >> Wall time closely tracks max attempt time.
     Attempts are running in parallel effectively.

  Effective parallelism: 12.2x
  (Sum of attempt times / Sum of wall times)
  Theoretical max with 16 workers: 16.0x
  Utilization: 75.9%

  GPU Utilization Estimate (based on 313.5 min run, 16 workers):
    Total GPU-minutes available: 5016 min
    Total GPU-minutes used:      3810 min
    GPU utilization:             76.0%
    Idle GPU-minutes:            1206 min

  Sequential processing estimate:
    97 problem-entries processed
    Average wall time per problem: 3.2m
    Sum of wall times: 5.2h
    Run overhead (run time - sum wall): -1.1s
    Overhead as % of run: -0.0%

==============================================================================
  7. TIME BUDGET ANALYSIS
==============================================================================

  Run Statistics:
    Problem-entries (with retries): 97
    Unique problems:                78
    Total run time:                 5.2h (313.5 min)
    Target budget:                  5.0h (300 min)
    OVER BUDGET BY:                 13.5m (13.5 min)

  Per-Problem Averages:
    Per problem-entry:    3.2m
    Per unique problem:   4.0m
    Budget per problem (at 300 min target, 80 problems): 3.8m
    Budget per problem (at 300 min target, 110 problems): 2.7m

  Budget Utilization (problems with budget data):
    Mean utilization: 43.1%
    Median utilization: 26.7%
    Over-budget problems: 13/97

  Budget Breakdown:
    Correct problems: 2.8h (54.1%)
    Wrong problems:   2.4h (45.9%)
    Early-stopped:    3.4h (64.6%)
    Full-run:         1.8h (35.4%)

  Savings Needed to Hit 300 min:
    Must save: 13.5m (13.5 min)
    That's 4.3% of current run time

  Potential Savings Levers:
    a) Eliminate all None attempts: save 37.8h compute
    b) Drop wrong problems (if detectable): save 2.4h
    c) ES problems avg 16 attempts — already saving time

  Scale Projection (80 -> 110 problems):
    At current per-problem avg (3.2m): 5.9h (356 min)
    vs 300 min target: OVER by 55.5m

==============================================================================
  8. REDUCED-ATTEMPT SIMULATION (12 vs 16 attempts)
==============================================================================

  Simulating different max-attempt counts:
  (Uses first N attempts by attempt_num, applies majority voting)

   Max Att      Score      Compute      Savings  % Saved     ES@4     ES@5
       ---        ---          ---          ---      ---      ---      ---
         6    61/97        23.9h        39.6h    62.3%        6        1
         8    63/97        32.1h        31.3h    49.4%       17        1
        10    63/97        39.8h        23.7h    37.4%       41        9
        12    63/97        47.3h        16.2h    25.4%       64       22
        14    62/97        55.0h         8.5h    13.4%       83       53
        16    64/97        63.5h         0.0s     0.0%       86       82

  Problems that Change Score (16 -> 12 attempts):
  Problem      @16   @12 Votes@16                       Votes@12                      
  ---          ---   --- ---                            ---                           
  76aef9        OK WRONG {999: 4, 1: 2, 8: 5, 1997: 2}  {999: 4, 1: 2, 8: 3, 1997: 1} 
  aff75c     WRONG    OK {3540: 1, 3571: 3, 3600: 4, 3599: 2, 3658: 1, 3601: 2, 1802: 1, 3543: 1, 2774: 1} {3540: 1, 3571: 3, 3600: 3, 3599: 2, 3658: 1, 3601: 1, 1802: 1}
  414a5b        OK WRONG {216: 1, 95: 4, 42: 5, 6: 1, 23: 3} {216: 1, 95: 3, 42: 3, 6: 1, 23: 3}

  Time Savings Estimate (12 vs 16 attempts):
    Compute at 16: 63.5h
    Compute at 12: 47.3h
    Savings:       16.2h (25.4%)

  Wall Time Savings (max-of-parallel, per-problem sum):
    Wall at 16 (estimated): 5.2h
    Wall at 12 (estimated): 5.0h
    Wall savings:           16.2m
    Note: Actual wall time also depends on batch scheduling overhead

==============================================================================
  SUMMARY & RECOMMENDATIONS
==============================================================================

  KEY FINDINGS:

  1. OVER BUDGET: Run took 313.5 min vs 300 min target (13.5 min over).
     Must save 13.5 min (4.3%) to fit.

  2. NONE WASTE: 919/1552 attempts (59%) returned None,
     consuming 37.8h of compute. Eliminating would reclaim significant budget.

  3. WRONG PROBLEMS: 32 problems answered wrong, consuming 2.4h.
     These can't easily be detected early, but dominate the tail.

  4. EARLY STOP: 82/97 problems (85%) early-stopped.
     ES is already working well for easy problems.

  RECOMMENDATIONS:

  a) REDUCE TO 12 ATTEMPTS: Likely same score, saves ~25% compute.
     Combined with ES=4 (already planned), this should bring under 300 min.

  b) TIGHTER EARLY STOP (ES=4): Already implemented. Saves time without
     losing score based on v23 data.

  c) REDUCE NONE RATE: Each None attempt wastes compute. Better extraction
     and error recovery are the biggest single optimization lever.

  d) ADAPTIVE ATTEMPTS: Easy problems (ES within 6 attempts) don't need 16.
     Hard problems (no convergence) might benefit from MORE attempts.
     Consider: 8 attempts for easy batch, 16 for hard batch.

  e) SCALE WARNING: At 110 problems (competition), current approach needs
     ~356 min. Must get per-problem avg under 164s for 110.

```
