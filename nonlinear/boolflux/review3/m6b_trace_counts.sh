#!/bin/bash
# review3 M6b: the REPORT section 2 trace statistics (AES a36 -> 131, seed 3, 57644 iterations,
# skip_noop 0: "43,958 accepted moves (mostly neutral), 10,850 targeted an AND gate and 15,710
# inserted one") counted with the renumbering-invariant check of bfx_instr: how many of those
# accepted moves leave the circuit structurally unchanged.
set -e
cd ~/xcr-boolflux
K=nonlinear/boolflux/review3/kernel; R=nonlinear/boolflux/review3/tmp/m6b
rm -rf $R; mkdir -p $R
python3 $K/make_instr.py > /dev/null && gcc -O2 -o $K/bfx_instr $K/bfx_instr.c -lm
python3 - $R <<'EOF'
import sys, argparse
from pathlib import Path
R = Path(sys.argv[1]); sys.path.insert(0, 'nonlinear'); sys.path.insert(0, 'nonlinear/boolflux')
from boolflux import core
import cli
m = core.Model.load('nist')
c = core.read_ncff('nonlinear/nist/aes-sbox/aes-sbox-a36-ad4-g142-gd13-xx106-19.circ.txt')
(R / 'start.bfx').write_text(core.to_kernel(c))
a = argparse.Namespace(objective='cost,gd', cap_gd=13, cap_ad=4, cap_a=36, seconds=3600, iters=57644)
cli.kernel_config(R / 'k.cfg', str(R / 'start.bfx'), str(R / 'best.bfx'), m, a, 3,
                  {'skip_noop': '0', 'tracemoves': str(R / 'moves.txt')})
EOF
taskset -c 18 $K/bfx_instr $R/k.cfg > $R/k.log
grep '^final' $R/k.log; grep review3 $R/k.log
python3 - $R/moves.txt <<'EOF'
import re, sys
acc = tgt_and = ins_and = iso = iso_tgt = iso_ins = 0
for ln in open(sys.argv[1]):
    acc += 1
    i = ' review3_iso 1' in ln
    iso += i
    t = re.search(r'target s\d+=(\w+)\(', ln).group(1) == 'AND'
    new = ln.split('| new', 1)[1].split('root', 1)[0]
    n = '=AND(' in new
    tgt_and += t; ins_and += n; iso_tgt += t and i; iso_ins += n and i
print('accepted %d (structurally unchanged %d); targeted an AND %d (unchanged %d); inserted an AND %d (unchanged %d)'
      % (acc, iso, tgt_and, iso_tgt, ins_and, iso_ins))
EOF
