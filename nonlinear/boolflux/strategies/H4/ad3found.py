"""Build + verify every FOUND record of ad3walk.py (level-1 operand masks over the x bits from the
exact cover, level-2 state), save verified circuits to strategies/H4/found/ with a JSON sidecar.
usage: ad3found.py WALK_JSONL [WORKDIR]"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import ad3mem as A
from ad3sat import XT
import ad3build

HERE = Path(__file__).resolve().parent
FOUND = HERE / 'found'
REPO = HERE.parents[3]


def main():
    walk = sys.argv[1]
    work = Path(sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(walk))
    FOUND.mkdir(exist_ok=True)
    donef = work / 'found_done.txt'
    done = set(donef.read_text().split()) if donef.exists() else set()
    for i, line in enumerate(open(walk).read().splitlines()):
        if str(i) in done: continue
        with open(donef, 'a') as fh: fh.write('%d' % i + chr(10))
        r = json.loads(line)
        if 'L1' not in r or 'state' not in r: continue
        ops = [['%x' % A.lin(l, XT), '%x' % A.lin(m, XT)] for l, m in r['L1']]
        l1json = work / ('found_l1_%d.json' % i)
        l1json.write_text(json.dumps({'l1ops': ops}))
        state = [tuple(m) if m[0] == 'n' else ('m', m[1], tuple(m[2])) for m in r['state']]
        out = work / ('found_%d.circ.txt' % i)
        ok, l12, m = ad3build.build(ad3build.level1_operands(str(l1json)), state, str(out),
                                    'H4 AD3 GF(4)-norm route, ad3walk record %d of %s' % (i, walk))
        if not ok: print('record', i, 'inverse FAILED'); continue
        res = subprocess.run([sys.executable, str(REPO / 'nonlinear/boolflux/campaigns/aes_check.py'), str(out)],
                             capture_output=True, text=True, cwd=str(REPO))
        print(res.stdout.splitlines()[0] if res.stdout else res.stderr[-300:])
        if res.returncode == 0 and os.environ.get('H4_NOSAVE') != '1':
            name = 'h4-ad3-a%d-ad%d-g%d-gd%d-%d.circ.txt' % (m['A'], m['AD'], m['G'], m['GD'], int(time.time()))
            (FOUND / name).write_text(out.read_text())
            (FOUND / (name + '.json')).write_text(json.dumps({
                'how': 'H4 AD3 GF(4)-norm route: level 1 from exact cover (cover_exact/cover_s2), level 2 '
                       'members + N-products from ad3walk.py, level 3 Karatsuba GF(4)-scalar x F',
                'record': r, 'source': walk, 'metrics': m, 'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'verified': 'campaigns/aes_check.py OK'}, indent=1))
            print('saved', FOUND / name)


if __name__ == '__main__':
    main()
