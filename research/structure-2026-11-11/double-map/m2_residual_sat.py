"""Cross-check of the residual case in the proof of L(M2) >= 26 (REPORT.md, Theorem D, step 4).

usage: python3 m2_residual_sat.py [mask_hex ...]      default: 8088 040c  (H = u3 + w7 and H = u3 + w2)

Question decided by SAT: is there a 25-gate circuit for M2 with exactly 8 odd+odd gates, no even+even gate,
and one helper whose mask is the given H?  (17 odd gates with known masks: the 16 outputs and H.)
The hand argument says no.  This is a check of that argument, not a replacement.
"""
import sys
import time

import dmap
import geom
import sat2


def main():
    masks = [int(a, 16) for a in sys.argv[1:]] or [0x8088, 0x040C]
    T = geom.m2_T()
    m = len(T)
    rows = dmap.dmap_rows(T)
    for H in masks:
        t0 = time.time()
        res, circ = sat2.solve(rows + [H], 2 * m, 25, m, x_range=(8, 8), y_range=(0, 0))
        print(f"H={H:04x}: 25 gates with profile (x,y,h)=(8,0,1): {'SAT' if res else 'UNSAT'} ({time.time() - t0:.1f}s)", flush=True)
        if res:
            print("  circuit:", circ)


if __name__ == "__main__":
    main()
