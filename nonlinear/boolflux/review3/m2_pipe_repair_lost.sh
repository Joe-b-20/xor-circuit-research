#!/bin/bash
# review3 M2 (two bugs in cli.py `pipe` under caps that the start violates):
#  (a) cli.py:426-428 crash: after a round with no feasible job, `best` is None and the round
#      report dereferences it (TypeError) -> pipe cannot do depth repair at all.
#  (b) cli.py:411-423: only feasible job results enter the next pool; with none feasible the
#      pool stays [original start], so the repair restarts from scratch every round (`run`,
#      cli.py:256-268, carries the penalised best).  Shown with (a) patched out in memory only.
set -e
cd ~/xcr-boolflux
R=nonlinear/boolflux/review3/tmp/m2
rm -rf $R; mkdir -p $R
ST=nonlinear/nist/aes-sbox/aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt
COMMON="--target aes --model nist --start $ST --objective cost,gd --cap-gd 14 --iters 2000 --seeds 1-2 --jobs 2 --rounds 2"
echo "== (a) pipe, unmodified"
taskset -c 18,19 python3 nonlinear/boolflux/cli.py pipe $COMMON --skel-share 0 --out $R/pipe 2>&1 | tail -1 || true
ls $R/pipe | grep -c '^r1-' | sed 's/^/   round-1 files written: /'
echo "== (b) pipe with only the round report guarded (in-memory patch), and run"
taskset -c 18,19 python3 - $COMMON --skel-share 0 --out $R/pipe-b <<'EOF' 2>&1 | tail -1 || true
import inspect, sys, textwrap
sys.path.insert(0, 'nonlinear/boolflux'); sys.argv = ['cli.py', 'pipe'] + sys.argv[1:]
import cli
src = textwrap.dedent(inspect.getsource(cli.cmd_pipe))
old = "bm = best[2]['metrics'] if best else None"
assert old in src
src = src.replace(old, "bm = best[2]['metrics'] if best else res[0][0]['metrics']")
exec(compile(src, cli.__file__, 'exec'), cli.__dict__)
cli.main(sys.argv[1:])
EOF
taskset -c 18,19 python3 nonlinear/boolflux/cli.py run $COMMON --out $R/run 2>&1 | tail -1 || true
for d in pipe-b run; do
  echo "-- $d: round-0 result vs round-1 start (penalised objective)"
  grep -h '^final' $R/$d/r0-s1.log | cut -d' ' -f1-15 | sed 's/^/   r0-s1 /'
  grep -h '^start' $R/$d/r1-s1.log | sed 's/^/   r1-s1 /'
  cmp -s $R/$d/r1-s1.start.bfx $R/$d/r0-s1.start.bfx && echo "   r1-s1 start == original start: repair progress lost" \
                                                     || echo "   r1-s1 start != original start: progress kept"
done
