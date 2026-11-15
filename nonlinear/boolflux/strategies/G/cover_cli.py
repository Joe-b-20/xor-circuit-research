"""Stage-1 cover by SAT in a separate process (so that a wall-clock limit can kill it).

usage: python3 cover_cli.py IN.json OUT.json      IN: {"U": [hex tables], "l": l}
OUT: {"sat": true/false, "pairs": [[hex, hex], ...]}
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / 'C'))
import gf      # noqa: E402
import qmc     # noqa: E402

ONES = (1 << 256) - 1


def main():
    d = json.loads(Path(sys.argv[1]).read_text())
    U = [int(h, 16) for h in d['U']]
    l = d['l']
    O = list(gf.X); E = [ONES] + list(gf.X)
    f, LMC, meta = qmc.encode(O, E, U, l)
    ok, model, dt = qmc.solve(f)
    out = {'sat': ok, 'secs': round(dt, 1)}
    if ok:
        prods, cmat = qmc.decode(model, LMC, O)
        pairs = []
        for lv, mv in prods:
            a = 0; b = 0
            for i in range(8):
                if lv[i]: a ^= gf.X[i]
                if mv[i]: b ^= gf.X[i]
            pairs.append(['%x' % a, '%x' % b])
        out['pairs'] = pairs
    Path(sys.argv[2]).write_text(json.dumps(out))


if __name__ == '__main__':
    main()
