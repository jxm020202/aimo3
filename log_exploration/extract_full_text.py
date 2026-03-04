#!/usr/bin/env python3
"""Extract full problem text from raw logs for specified problem IDs."""
import sys, re, json

PIDS = ['dbbfe8', 'a824c1', '673b29', '414a5b', 'a9dbc8', '9010d9']
LOGFILES = ['output/v31/diagnostic.log', 'output/v23/diagnostic.log']

results = {}

for logfile in LOGFILES:
    with open(logfile, 'r', errors='replace') as f:
        content = f.read()
    for pid in PIDS:
        if pid in results:
            continue
        pattern = rf'\[\d+/\d+\]\s*Problem\s+(?:id=)?{pid}'
        match = re.search(pattern, content)
        if not match:
            continue
        start_pos = match.start()
        section = content[start_pos:start_pos+10000]
        prob_start = section.find('Problem:')
        if prob_start == -1:
            continue
        text_start = prob_start + len('Problem:')
        remaining = section[text_start:]
        end_markers = ['Budget:', 'Expected:', 'ATTEMPT ', '--- ']
        end_pos = len(remaining)
        for marker in end_markers:
            pos = remaining.find(marker)
            if pos != -1 and pos < end_pos:
                end_pos = pos
        raw_text = remaining[:end_pos].strip()
        raw_text = re.sub(r'\n\s*', ' ', raw_text)
        raw_text = re.sub(r'\s+', ' ', raw_text)
        if len(raw_text) > 50:
            results[pid] = raw_text

# Output as JSON
with open('data/problem_db/full_texts.json', 'w') as f:
    json.dump(results, f, indent=2)

for pid, text in results.items():
    print(f"=== {pid} ===")
    print(text[:500])
    print()
