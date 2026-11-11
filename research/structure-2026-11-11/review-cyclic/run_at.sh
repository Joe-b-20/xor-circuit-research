#!/bin/bash
# Theorem C(iii) spot check: L_cyc of the transpose of Example 3's A (A^T has a unit row, so 6 non-unit targets)
cd ~/xor-circuit-research/research/structure-2026-11-11/review-cyclic || exit 1
ulimit -v 8000000
python3 - <<'EOF' > at_targets.txt
def vec(s): return sum(1 << i for i, ch in enumerate(s) if ch == '1')
A = [vec(s) for s in ['1110101', '1101101', '0111000', '1001001', '0101111', '1100100', '1011101']]
n = 7
AT = [sum(((A[i] >> j) & 1) << i for i in range(n)) for j in range(n)]
print(' '.join(map(str, AT)))
EOF
/usr/bin/time -f "%U s user" ./lmin 7 4 -1 $(cat at_targets.txt)
