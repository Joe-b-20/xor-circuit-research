#!/usr/bin/env python3
"""Check the pinned NIST AES S-box reference collection against a clone of usnistgov/Circuits.

usage: refresh.py CLONE [--import-sel]

CLONE is a clone of https://github.com/usnistgov/Circuits (blobs may be lazily fetched).
For every file in MANIFEST.json the git blob hash of the local copy must equal the blob at the
pinned commit, and every S-box file upstream (aes-sbox, aes-invsbox, sbox, old-2020 S-box SLPs,
aes-sbox-sel) must be present locally. --import-sel copies aes-sbox-sel into nist/ and adds it to
the manifest. Writes PIN.md with the result.
"""
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = 'data/slp/aes'
FOLDERS = ['aes-sbox', 'aes-invsbox', 'sbox', 'old-2020', 'aes-sbox-sel']


def git(clone, *args):
    return subprocess.run(['git', '-C', str(clone), *args], check=True, capture_output=True).stdout


def blob_hash(data):
    return hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()


def main():
    clone = Path(sys.argv[1])
    import_sel = '--import-sel' in sys.argv
    man = json.loads((HERE / 'MANIFEST.json').read_text())
    pin = man['commit']
    head = git(clone, 'rev-parse', 'HEAD').decode().strip()
    upstream = {}
    for line in git(clone, 'ls-tree', '-r', pin, BASE).decode().splitlines():
        meta, path = line.split('\t')
        upstream[path] = meta.split()[2]
    bad, checked = [], 0
    for f in man['files']:
        local = HERE / f['folder'] / f['file']
        data = local.read_bytes()
        if hashlib.sha256(data).hexdigest() != f['sha256']:
            bad.append(f'{local}: sha256 differs from manifest')
        if upstream.get(f['nist_path']) != blob_hash(data):
            bad.append(f'{local}: differs from upstream {f["nist_path"]} at {pin[:7]}')
        checked += 1
    have = {f['nist_path'] for f in man['files']}
    missing = []
    for path in sorted(upstream):
        folder = path[len(BASE) + 1:].split('/')[0]
        if folder not in FOLDERS or path in have:
            continue
        name = path.rsplit('/', 1)[1]
        if folder == 'old-2020' and not name.startswith('aes-sbox'):
            continue  # full-cipher SLPs, not S-box circuits
        missing.append(path)
    added = []
    if import_sel:
        for path in [p for p in missing if '/aes-sbox-sel/' in p]:
            data = git(clone, 'show', f'{pin}:{path}')
            name = path.rsplit('/', 1)[1]
            if name == 'README.md':
                name = 'NIST-README.md'
            (HERE / 'aes-sbox-sel').mkdir(exist_ok=True)
            (HERE / 'aes-sbox-sel' / name).write_bytes(data)
            man['files'].append({
                'folder': 'aes-sbox-sel', 'file': name, 'nist_path': path,
                'url': f'https://github.com/usnistgov/Circuits/blob/{pin}/{path}',
                'sha256': hashlib.sha256(data).hexdigest()})
            added.append(path)
        (HERE / 'MANIFEST.json').write_text(json.dumps(man, indent=1) + '\n')
        missing = [p for p in missing if p not in added]
    today = datetime.date.today().isoformat()
    lines = [
        '# NIST reference pin', '',
        f'- Repository: https://github.com/usnistgov/Circuits, pinned commit `{pin}`.',
        f'- Checked {today}: upstream HEAD is `{head}`'
        + (' (the pin is current).' if head == pin else ' (NEWER THAN THE PIN).'),
        f'- {checked} pinned files compared by git blob hash with the pinned commit: '
        + ('all identical.' if not bad else f'{len(bad)} DIFFER.'),
        f'- S-box folders checked for completeness: {", ".join(FOLDERS)} (old-2020: S-box SLPs only).',
        f'- Added in this check: {len(added)} files' + (f' ({", ".join(sorted({p.split("/")[3] for p in added}))})' if added else '') + '.',
        f'- Upstream S-box files still missing locally: {len(missing)}.',
    ]
    lines += [f'  - {b}' for b in bad + missing]
    (HERE / 'PIN.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    return 1 if bad or missing else 0


if __name__ == '__main__':
    sys.exit(main())
