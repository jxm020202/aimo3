#!/usr/bin/env python3
"""Read entire notebook as Python, with cell markers. Usage: python3 scripts/read_nb.py [notebook_path]"""
import json, sys

path = sys.argv[1] if len(sys.argv) > 1 else 'notebooks/aimo3-solver.ipynb'
nb = json.loads(open(path).read())

for i, cell in enumerate(nb['cells']):
    kind = cell['cell_type']
    src = ''.join(cell['source'])
    preview = src[:60].replace('\n', ' ')
    print(f'# ===== CELL {i} ({kind}) — {preview} =====')
    print(src)
    print()
