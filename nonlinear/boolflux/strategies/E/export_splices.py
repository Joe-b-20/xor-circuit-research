#!/usr/bin/env python3
"""Export splice2 results that are Pareto-new against the pinned NIST set; mark whether they are also new
against the team's unpublished results (results/aes, F/found, E/found).  For the frontier of the new
ones (non-dominated among themselves), write NCFF + JSON sidecar + aes_check output to found/.

    python3 export_splices.py SPLICEDIR [--all-new]
"""
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import core, load, metrics, correct, MODEL, PKG   # noqa: E402
sys.path.insert(0, str(PKG / 'campaigns'))
import aes_check   # noqa: E402

FOUND = Path.home() / 'xs-campaigns/2026-11-13-aes/E/found'


def team_points():
    pts = []
    fs = list((PKG / 'results' / 'aes').glob('*.circ.txt')) + list(Path.home().glob('xs-campaigns/2026-11-13-aes/*/found/*.circ.txt'))
    for f in fs:
        try:
            c = load(f)
            if correct(c): pts.append((metrics(c), f.name))
        except Exception:
            pass
    return pts


def dom(pts, m):
    return [n for (u, n) in pts if all(a <= b for a, b in zip(u, m))]


def main():
    d = Path(sys.argv[1])
    rows = []
    for f in d.glob('shard*/splices.json'): rows += json.loads(f.read_text())
    pub = list(aes_check.published())
    team = team_points()
    new = {}
    for r in rows:
        m = tuple(r['metrics'])
        if r['need'] != 0 or m in new: continue
        if dom(pub, m): continue
        new[m] = r
    # frontier among the new ones + team
    allp = [(m, 'splice') for m in new] + team + pub
    front = [m for m in new if not [u for (u, n) in allp if u != m and all(a <= b for a, b in zip(u, m))]]
    print('pub-new splices: %d distinct tuples; non-dominated vs pub+team+other splices: %d' % (len(new), len(front)))
    FOUND.mkdir(parents=True, exist_ok=True)
    for m in sorted(front, key=lambda t: (t[0], t[2])):
        r = new[m]
        cand = next(d.glob('shard*/cands/%s.bfx' % r['h']))
        c = core.from_kernel(cand.read_text(), 'splice')
        assert correct(c) and tuple(metrics(c)) == m
        name = 'E-splice-a%d-ad%d-g%d-gd%d' % m[:1] + () if False else 'E-splice-a%d-ad%d-g%d-gd%d' % (m[0], m[1], m[2], m[3])
        c.name = name
        nf = FOUND / (name + '.circ.txt')
        nf.write_text(core.write_ncff(c, MODEL, comments=[
            'Track E stage transplant: front of %s (AND levels <= %d) + back of %s (above AND level %d), %d interface gates' % (
                r['X'], r['LX'], r['Y'], r['LY'], r['interface'])]))
        (FOUND / (name + '.bfx')).write_text(core.to_kernel(c))
        chk = subprocess.run([sys.executable, str(PKG / 'campaigns' / 'aes_check.py'), str(nf)], capture_output=True, text=True)
        (FOUND / (name + '.check.txt')).write_text(chk.stdout + chk.stderr)
        side = {'mechanism': 'splice2 (stage transplant, linear interface)', 'front': r['X'], 'LX': r['LX'], 'back': r['Y'],
                'LY': r['LY'], 'interface_gates': r['interface'], 'metrics': m, 'source': str(d),
                'command': 'python3 strategies/E/splice2.py %s --shard i/4 files.list' % d, 'seed': None,
                'time_to_result_s': 'enumeration of all pairs: ~50 s per shard (4 shards)',
                'dominated_by_team': dom(team, m)}
        (FOUND / (name + '.json')).write_text(json.dumps(side, indent=1) + '\n')
        ok = chk.stdout.splitlines()[:2]
        print(m, r['X'][:40], '<-', r['Y'][:40], 'LX', r['LX'], 'LY', r['LY'], '|', ' / '.join(x.strip() for x in ok))


if __name__ == '__main__':
    main()
