"""Import NIST's AES S-box circuit files into nonlinear/nist/, verbatim, with a manifest.

    python3 nonlinear/tools/import_nist.py --commit SHA [--source DIR] [--dest nonlinear/nist]

Copies the circuit files of ``data/slp/aes/{aes-sbox,aes-invsbox,sbox,old-2020}`` of
https://github.com/usnistgov/Circuits at the given commit (from a local copy with the same
layout, ``--source``, or downloaded from raw.githubusercontent.com) and writes
``MANIFEST.json``: for every file its NIST path, URL at that commit, SHA-256 and size, and
what this repository's checker established about it (metrics, the bit order under which it
equals FIPS-197).  Each folder's NIST ``README.md`` is kept as ``NIST-README.md``.
Files are byte-identical copies: nothing is reformatted.  Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
NONLINEAR = HERE.parent
sys.path.insert(0, str(NONLINEAR))

from boolcirc import metrics as M, ncff, truth  # noqa: E402

REPO = 'usnistgov/Circuits'
BASE = 'data/slp/aes'
FOLDERS = {'aes-sbox': ('aes-sbox',), 'aes-invsbox': ('aes-invsbox',), 'sbox': ('aes-sbox-',),
           'old-2020': ('aes-sbox-',)}
SUFFIXES = ('.circ.txt', '.ncff.txt', '.slp')


def listing(commit, folder):
    url = 'https://api.github.com/repos/%s/contents/%s/%s?ref=%s' % (REPO, BASE, folder, commit)
    with urllib.request.urlopen(url) as r:
        return [e['name'] for e in json.load(r) if e['type'] == 'file']


def fetch(commit, folder, name):
    url = 'https://raw.githubusercontent.com/%s/%s/%s/%s/%s' % (REPO, commit, BASE, folder, name)
    with urllib.request.urlopen(url) as r:
        return r.read()


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--commit', required=True, help='commit of usnistgov/Circuits')
    ap.add_argument('--source', help='local copy of data/slp/aes/ (else download)')
    ap.add_argument('--dest', default=str(NONLINEAR / 'nist'))
    args = ap.parse_args(argv)
    dest = pathlib.Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    manifest = {'repository': 'https://github.com/' + REPO, 'commit': args.commit,
                'base_path': BASE, 'terms': 'https://www.nist.gov/open/license',
                'bit_order': "'msb/msb': file input i is bit 7-i of the byte, same for outputs",
                'files': []}
    fns = {'aes-sbox': truth.aes_sbox(), 'aes-invsbox': truth.aes_inv_sbox()}
    for folder, prefixes in FOLDERS.items():
        if args.source:
            names = sorted(p.name for p in (pathlib.Path(args.source) / folder).iterdir())
        else:
            names = sorted(listing(args.commit, folder))
        out_dir = dest / folder
        out_dir.mkdir(exist_ok=True)
        for name in names:
            keep = name == 'README.md' or (name.endswith(SUFFIXES) and name.startswith(prefixes))
            if not keep:
                continue
            data = (pathlib.Path(args.source) / folder / name).read_bytes() if args.source \
                else fetch(args.commit, folder, name)
            target = out_dir / ('NIST-README.md' if name == 'README.md' else name)
            target.write_bytes(data)
            entry = {'folder': folder, 'file': target.name, 'nist_path': '%s/%s/%s' % (BASE, folder, name),
                     'url': 'https://github.com/%s/blob/%s/%s/%s/%s' % (REPO, args.commit, BASE, folder, name),
                     'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
            if name != 'README.md':
                c = ncff.parse(data.decode('utf-8'), name)[0]
                m = M.metrics(c)
                low = name.lower()
                fn = fns['aes-invsbox'] if low.startswith(('aes-invsbox', 'aes-sbox-inv', 'aes-sbox-rev')) \
                    else fns['aes-sbox']
                orders = truth.match(c, fn)
                if not orders:
                    raise SystemExit('%s does not compute %s' % (name, fn.name))
                entry.update({'circuit': c.name, 'function': fn.name,
                              'bit_orders': ['%s/%s' % o for o in orders],
                              'A': m.and_count, 'AD': m.and_depth, 'G': m.gates, 'GD': m.gate_depth,
                              'XOR': m.xor, 'XNOR': m.xnor,
                              'name_matches_metrics': not M.check_name(name, m),
                              'header_matches_metrics': not M.check_tallies(c, m)})
            manifest['files'].append(entry)
            print('%-12s %s' % (folder, target.name))
    (dest / 'MANIFEST.json').write_text(json.dumps(manifest, indent=1) + '\n')
    n = sum('circuit' in e for e in manifest['files'])
    print('%d circuit files, %d entries -> %s' % (n, len(manifest['files']), dest / 'MANIFEST.json'))


if __name__ == '__main__':
    main(sys.argv[1:])
