"""P4: exact top minimum (no deadline) and Avail-meet-V cover for given (lambda, k) of the family.

    python3 famtop.py CIRC HMAX lam:k [lam:k ...]
"""
import json
import subprocess
import sys
from pathlib import Path

import family
import pairscan

HERE = Path(__file__).resolve().parent


def forms_for(path, lam, k):
    gates, s, lvl1, pairs, X, P = pairscan.setup(path)
    L = lambda x: family.gmul(lam, family.gpow(x, 1 << k)) if x else 0
    LT = family.transpose(family.lin_matrix(L))
    forms = [family.apply_rows(LT, g) for pr in pairs for g in pr]
    Xn = [family.apply_rows(LT, v) for v in X]
    return forms, Xn


def main():
    path, hmax = sys.argv[1], int(sys.argv[2])
    for arg in sys.argv[3:]:
        lam, k = map(int, arg.split(':'))
        forms, Xn = forms_for(path, lam, k)
        nontriv = sorted({f for f in forms if bin(f).count('1') > 1})
        res = None
        for H in range(0, hmax + 1):
            inp = [str(len(nontriv))] + [f'{m} 99' for m in nontriv] + [str(H), str(len(Xn))] + [str(v) for v in Xn]
            r = subprocess.run([str(HERE / 'topenum_c')], input='\n'.join(inp) + '\n', capture_output=True, text=True)
            lines = [l for l in r.stdout.splitlines() if l.strip()]
            if lines:
                covers = [int(l.split('|')[2].split()[1]) if H else 0 for l in lines]
                res = dict(lam=lam, k=k, nforms=len(nontriv), top=len(nontriv) + H, H=H, sets=len(lines),
                           best_cover=max(covers), sample=lines[:5])
                break
        print(json.dumps(res or dict(lam=lam, k=k, nforms=len(nontriv), top='>' + str(len(nontriv) + hmax))), flush=True)


if __name__ == '__main__':
    main()
