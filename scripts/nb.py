#!/usr/bin/env python3
"""Notebook cell helper — read/write/list cells in aimo3-solver.ipynb.

Usage:
    python3 scripts/nb.py list                    # Show all cells (index, type, first line)
    python3 scripts/nb.py read CELL_INDEX         # Print cell source to stdout
    python3 scripts/nb.py write CELL_INDEX FILE   # Replace cell source from FILE
    python3 scripts/nb.py diff CELL_INDEX FILE    # Show diff between current cell and FILE
"""

import json
import sys
import os
import difflib

NB_PATH = os.path.join(os.path.dirname(__file__), '..', 'notebooks', 'aimo3-solver.ipynb')


def load_nb():
    with open(NB_PATH) as f:
        return json.load(f)


def save_nb(nb):
    with open(NB_PATH, 'w') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write('\n')


def cmd_list(nb):
    for i, cell in enumerate(nb['cells']):
        src = ''.join(cell['source'])
        first_line = src.split('\n')[0][:70]
        print(f"  {i:>2}  {cell['cell_type']:<8}  {first_line}")


def cmd_read(nb, idx):
    src = ''.join(nb['cells'][idx]['source'])
    sys.stdout.write(src)
    if not src.endswith('\n'):
        sys.stdout.write('\n')


def cmd_write(nb, idx, filepath):
    with open(filepath) as f:
        new_source = f.read()
    # Notebook stores source as list of lines (each ending with \n except possibly last)
    lines = new_source.split('\n')
    source_list = [line + '\n' for line in lines[:-1]]
    if lines[-1]:  # last line non-empty
        source_list.append(lines[-1])
    nb['cells'][idx]['source'] = source_list
    save_nb(nb)
    print(f"Cell {idx} updated ({len(new_source)} chars, {len(source_list)} lines)")


def cmd_diff(nb, idx, filepath):
    current = ''.join(nb['cells'][idx]['source']).splitlines(keepends=True)
    with open(filepath) as f:
        proposed = f.read().splitlines(keepends=True)
    diff = difflib.unified_diff(current, proposed, fromfile=f'cell[{idx}]', tofile=filepath)
    sys.stdout.writelines(diff)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    nb = load_nb()
    cmd = sys.argv[1]

    if cmd == 'list':
        cmd_list(nb)
    elif cmd == 'read' and len(sys.argv) >= 3:
        cmd_read(nb, int(sys.argv[2]))
    elif cmd == 'write' and len(sys.argv) >= 4:
        cmd_write(nb, int(sys.argv[2]), sys.argv[3])
    elif cmd == 'diff' and len(sys.argv) >= 4:
        cmd_diff(nb, int(sys.argv[2]), sys.argv[3])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
