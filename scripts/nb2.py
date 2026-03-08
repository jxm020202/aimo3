#!/usr/bin/env python3
"""Notebook cell helper for aimo3-no-wave1.ipynb"""
import json, sys, os

NB_PATH = os.path.join(os.path.dirname(__file__), '..', 'notebooks', 'aimo3-no-wave1.ipynb')

def load_nb():
    with open(NB_PATH) as f:
        return json.load(f)

def save_nb(nb):
    with open(NB_PATH, 'w') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write('\n')

def cmd_list(nb):
    for i, cell in enumerate(nb['cells']):
        src = ''.join(cell['source']).split('\n')[0][:70]
        print(f'  {i:2d}  {cell["cell_type"]:<10}{src}')

def cmd_read(nb, idx):
    cell = nb['cells'][int(idx)]
    print(''.join(cell['source']), end='')

def cmd_write(nb, idx, filepath):
    idx = int(idx)
    with open(filepath) as f:
        content = f.read()
    lines = content.split('\n')
    src = [line + '\n' for line in lines[:-1]]
    if lines[-1]:
        src.append(lines[-1])
    nb['cells'][idx]['source'] = src
    save_nb(nb)
    print(f'Cell {idx} updated ({len(content)} chars, {len(lines)} lines)')

if __name__ == '__main__':
    nb = load_nb()
    cmd = sys.argv[1]
    if cmd == 'list': cmd_list(nb)
    elif cmd == 'read': cmd_read(nb, sys.argv[2])
    elif cmd == 'write': cmd_write(nb, sys.argv[2], sys.argv[3])
