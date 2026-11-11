"""Write Q_m (or Q_T) as a .mat.txt file readable by search/xorflux:  python3 gen_mat.py m OUT [j:k,j:k,...]

Row r = output (c, j) with r = 4j + c; column i = input (c, j) with i = 4j + c.  The optional third
argument adds entries T[j][k] = 1 to the shift.
"""
import sys

import qm


def main():
    m = int(sys.argv[1])
    T = qm.shift_T(m)
    if len(sys.argv) > 3:
        for item in sys.argv[3].split(","):
            j, k = map(int, item.split(":"))
            T[j] ^= 1 << k
    R = qm.rows_T(T)
    n = 4 * m
    with open(sys.argv[2], "w", newline="\n") as f:
        f.write("1\n")
        f.write(f"{n} {n}\n")
        for r in R:
            f.write(" ".join(str((r >> i) & 1) for i in range(n)) + "\n")


if __name__ == "__main__":
    main()
