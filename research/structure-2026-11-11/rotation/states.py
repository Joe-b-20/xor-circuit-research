"""Print, for a circuit of Q_m, the even gates supported on a single block ("pure vectors"), block by block.

usage: python3 states.py m FILE
"""
import sys

import qm

NAMES = {0b0011: "s0", 0b0110: "s1", 0b1100: "s2", 0b1001: "s3", 0b0101: "d0", 0b1010: "d1", 0b1111: "t"}


def main():
    m = int(sys.argv[1])
    n, gates = qm.read_circuit(sys.argv[2])
    vals = qm.masks(n, gates)
    per = {j: [] for j in range(m)}
    for v in vals[n:]:
        blocks = [j for j in range(m) if (v >> (4 * j)) & 15]
        if len(blocks) == 1 and qm.popcount(v) % 2 == 0:
            per[blocks[0]].append(NAMES[(v >> (4 * blocks[0])) & 15])
    print(" | ".join(f"{j}: {','.join(sorted(per[j]))}" for j in range(m)))


if __name__ == "__main__":
    main()
