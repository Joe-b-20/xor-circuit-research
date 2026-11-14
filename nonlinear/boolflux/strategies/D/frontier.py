"""List the pinned NIST forward AES S-box circuits: best G per GD cap, A28 circuits, Pareto set."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'campaigns'))
import aes_check  # noqa: E402

pub = aes_check.published()
NIST = aes_check.NIST


def path_of(name):
    for sub in ('aes-sbox', 'old-2020', 'sbox'):
        p = NIST / sub / name
        if p.exists():
            return p
    return None


if __name__ == '__main__':
    for gd in range(9, 40):
        c = [(u, n) for u, n in pub if u[3] <= gd]
        if c:
            u, n = min(c, key=lambda x: (x[0][2], x[0]))
            print('GD<=%d best G %d  A AD G GD %s  %s' % (gd, u[2], u, path_of(n)))
    print('pareto:')
    for u, n in sorted(pub):
        if not any(all(a <= b for a, b in zip(v, u)) and v != u for v, _ in pub):
            print('  ', u, path_of(n))
