#!/bin/bash
# review3 M6: skip_noop (bfx.c:734) compares the rebuilt candidate with the current circuit by
# memcmp of the gate list; rebuild() renumbers gates (DFS order, symmetric operands sorted by the
# new numbers), so a candidate that is the current circuit up to renumbering passes the filter
# and is accepted as a "neutral" move.  bfx_instr (review3/kernel/make_instr.py) is bfx.c plus a
# renumbering-invariant structural hash; its search is identical (checked below: same
# improvement sequence by iteration and same final circuit).
set -e
cd ~/xcr-boolflux
K=nonlinear/boolflux/review3/kernel; R=nonlinear/boolflux/review3/tmp/m6
rm -rf $R; mkdir -p $R
python3 $K/make_instr.py > /dev/null && gcc -O2 -o $K/bfx_instr $K/bfx_instr.c -lm
gcc -O2 -o $R/bfx nonlinear/boolflux/kernel/bfx.c -lm
python3 - $R <<'EOF'
import sys, argparse
from pathlib import Path
R = Path(sys.argv[1]); sys.path.insert(0, 'nonlinear'); sys.path.insert(0, 'nonlinear/boolflux')
from boolflux import core, starts, targets
import cli
cases = [('maj3', 'xag', 'a,cost', 'anf', {}, 400),
         ('present', 'bgc', 'cost', 'anf', {}, 3000),
         ('aes', 'nist', 'cost,gd', 'nonlinear/nist/aes-sbox/aes-sbox-a36-ad4-g142-gd13-xx106-19.circ.txt',
          {'cap_a': 36, 'cap_ad': 4, 'cap_gd': 13}, 3000)]
for t, mn, obj, st, caps, iters in cases:
    m = core.Model.load(mn); n, mm, tab, _ = targets.load(t)
    c = starts.anf(n, mm, tab, m.ops()) if st == 'anf' else core.read_ncff(st)
    (R / (t + '.bfx')).write_text(core.to_kernel(c))
    a = argparse.Namespace(objective=obj, cap_gd=caps.get('cap_gd'), cap_ad=caps.get('cap_ad'),
                           cap_a=caps.get('cap_a'), seconds=600, iters=iters)
    cli.kernel_config(R / (t + '.cfg'), str(R / (t + '.bfx')), str(R / (t + '.out')), m, a, 1, {'skip_noop': 1})
EOF
bests() { awk '/^best/ {print $5, $7, $9, $11, $13, $15, $17}' "$1"; }
for t in maj3 present aes; do
  taskset -c 18 $R/bfx $R/$t.cfg > $R/$t.plain; cp $R/$t.out $R/$t.out.plain
  taskset -c 18 $K/bfx_instr $R/$t.cfg > $R/$t.instr
  same=NO; cmp -s <(bests $R/$t.plain) <(bests $R/$t.instr) && cmp -s $R/$t.out $R/$t.out.plain && same=yes
  echo "$t: $(grep noop_candidates $R/$t.instr); accepted moves that are the current circuit renumbered: $(grep review3 $R/$t.instr | cut -d' ' -f2-) (search identical to bfx: $same)"
done
