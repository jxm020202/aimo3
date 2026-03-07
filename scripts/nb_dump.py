#!/usr/bin/env python3
"""Dump entire notebook as a single readable Python file with cell markers.

Usage:
    python3 scripts/nb_dump.py                    # Print to stdout
    python3 scripts/nb_dump.py > /tmp/full.py     # Save to file
    python3 scripts/nb_dump.py --out /tmp/full.py # Same thing
"""

import json
import sys
import os

NB_PATH = os.path.join(os.path.dirname(__file__), '..', 'notebooks', 'aimo3-solver.ipynb')


def main():
    out = sys.stdout
    if '--out' in sys.argv:
        idx = sys.argv.index('--out')
        out = open(sys.argv[idx + 1], 'w')

    with open(NB_PATH) as f:
        nb = json.load(f)

    for i, cell in enumerate(nb['cells']):
        src = ''.join(cell['source'])
        ctype = cell['cell_type']
        first_line = src.split('\n')[0][:60]

        out.write(f'# {"="*75}\n')
        out.write(f'# CELL {i} ({ctype}) — {first_line}\n')
        out.write(f'# {"="*75}\n')

        if ctype == 'markdown':
            for line in src.split('\n'):
                out.write(f'# {line}\n')
        else:
            out.write(src)
            if not src.endswith('\n'):
                out.write('\n')

        out.write('\n')

    if out is not sys.stdout:
        out.close()
        print(f'Wrote {i + 1} cells to {sys.argv[sys.argv.index("--out") + 1]}', file=sys.stderr)


if __name__ == '__main__':
    main()
