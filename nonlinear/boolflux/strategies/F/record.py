#!/usr/bin/env python3
"""Record a found circuit: copy to found/ as NCFF, run aes_check, write a JSON sidecar.

    python3 record.py CIRC NAME --start FILE --command "..." --seed S --config "..." --time T [--note "..."]
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core   # noqa: E402

FOUND = Path.home() / 'xs-campaigns/2026-11-13-aes/F/found'
CHECK = HERE.parents[1] / 'campaigns' / 'aes_check.py'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circ'); ap.add_argument('name')
    ap.add_argument('--start', default=''); ap.add_argument('--command', default='')
    ap.add_argument('--seed', default=''); ap.add_argument('--config', default='')
    ap.add_argument('--time', default=''); ap.add_argument('--note', default='')
    ap.add_argument('--mechanism', default='')
    a = ap.parse_args()
    FOUND.mkdir(parents=True, exist_ok=True)
    p = Path(a.circ)
    c = core.from_kernel(p.read_text()) if p.suffix == '.bfx' else core.read_ncff(str(p))
    model = core.Model.load(str(core.MODELS / 'nist.json'))
    m = c.metrics(model)
    stem = '%s-g%d-a%d-gd%d-ad%d' % (a.name, m['G'], m['A'], m['GD'], m['AD'])
    out = FOUND / (stem + '.circ.txt')
    out.write_text(core.write_ncff(c, model, comments=['track F: %s' % a.name]), encoding='utf-8')
    r = subprocess.run([sys.executable, str(CHECK), str(out), '--json', str(FOUND / (stem + '.check.json'))],
                       capture_output=True, text=True, cwd=str(HERE.parents[3]))
    (FOUND / (stem + '.check.txt')).write_text(r.stdout + r.stderr, encoding='utf-8')
    side = {'file': str(out), 'metrics': {k: m[k] for k in ('G', 'A', 'GD', 'AD')}, 'source': str(p),
            'start': a.start, 'command': a.command, 'seed': a.seed, 'config': a.config,
            'time_to_result_s': a.time, 'mechanism': a.mechanism, 'note': a.note,
            'recorded_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'check_exit': r.returncode}
    (FOUND / (stem + '.json')).write_text(json.dumps(side, indent=1) + '\n', encoding='utf-8')
    print(r.stdout[-1500:])
    print('recorded', out, 'check exit', r.returncode)


if __name__ == '__main__':
    main()
