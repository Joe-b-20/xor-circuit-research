#!/usr/bin/env python3
"""Scan Track-E batch directories for circuits that are new Pareto points on the pinned NIST set (or beat
a published best G at their GD / A caps); write each as NCFF + JSON sidecar + checker output into found/.

    python3 harvest.py DIR [DIR ...]
"""
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import core, load, metrics, correct, MODEL, PKG   # noqa: E402
sys.path.insert(0, str(PKG / 'campaigns'))
import aes_check   # noqa: E402

FOUND = Path.home() / 'xs-campaigns/2026-11-13-aes/E/found'


def main():
    FOUND.mkdir(parents=True, exist_ok=True)
    seen = {p.read_text() for p in FOUND.glob('*.bfx')}
    pub = aes_check.published()
    for d in sys.argv[1:]:
        for jf in sorted(Path(d).glob('*.json')):
            if jf.name == 'plan.json': continue
            rec = json.loads(jf.read_text())
            bf = jf.with_name(rec['tag'] + '.best.bfx')
            if not bf.exists(): continue
            c = core.from_kernel(bf.read_text(), rec['tag'])
            if not correct(c): print('WRONG', bf); continue
            A, AD, G, GD = t = metrics(c)
            dom = [n for (u, n) in pub if all(a <= b for a, b in zip(u, t))]
            if dom: continue
            kt = core.to_kernel(c)
            if kt in seen: continue
            seen.add(kt)
            name = 'E-a%d-ad%d-g%d-gd%d-%s' % (A, AD, G, GD, rec['tag'])
            (FOUND / (name + '.bfx')).write_text(kt)
            nf = FOUND / (name + '.circ.txt')
            c.name = name
            nf.write_text(core.write_ncff(c, MODEL, comments=['Track E (joint AND/XOR search) result',
                                                              'start %s seed %s arm %s' % (rec['start'], rec['seed'], rec['arm'])]))
            chk = subprocess.run([sys.executable, str(PKG / 'campaigns' / 'aes_check.py'), str(nf)], capture_output=True, text=True)
            (FOUND / (name + '.check.txt')).write_text(chk.stdout + chk.stderr)
            side = {k: rec.get(k) for k in ('tag', 'arm', 'start', 'start_metrics', 'seed', 'seconds', 'caps', 'objective',
                                            'config', 'command', 'improvements', 'stats')}
            side['source_dir'] = str(d); side['metrics'] = t
            side['time_to_result_s'] = rec['improvements'][-1]['t'] if rec.get('improvements') else None
            (FOUND / (name + '.json')).write_text(json.dumps(side, indent=1) + '\n')
            print('NEW', name, chk.stdout.strip().splitlines()[:2])


if __name__ == '__main__':
    main()
