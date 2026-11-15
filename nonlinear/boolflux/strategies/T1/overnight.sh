#!/bin/bash
# T1 overnight (QUEUE.md "T1"): one job per CPU, all memory-capped through xsrun by the caller.
#   overnight.sh screen HOURS      : screen the H2/X1b new-AND-space builds (skips the 9 done at 03:26-04:04),
#                                    then hybrid joins of everything screened, then a goal-C t1run worker
#   overnight.sh worker GOAL SEED HOURS : t1run v3.2 worker on the hybrid / front pools (goal B or C)
set -u
T=/home/joebachir20/xs-campaigns/2026-11-15-study/T1
O=$T/overnight
S=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/T1
mkdir -p $O/run/shared-ns
cp -n $T/run1/shared-ns/*.bfx $O/run/shared-ns/ 2>/dev/null
EXTRA="--extra $T/hyb1 --extra $O/hyb2 --extra $T/h2pol-s59/pool --extra $T/h2pol-s59b/pool --extra $T/found/front --extra $T/found/newspace"
case "$1" in
  screen)
    H=$2
    SCREEN_SKIP=$T/screen1/screen.jsonl python3 $S/screen.py $O/screen 4.5 /home/joebachir20/xs-campaigns/2026-11-15-study/H2/builds-for-T1.txt
    python3 $S/hybjoin.py $O/hyb2 $T/found/newspace
    python3 $S/t1run.py --goal C --seed 7001 --hours $(python3 -c "print(max(0.5, $H - 5.2))") --data $O/run --name ons-screen \
      --shared shared-ns --no-hub --admax 6 --gslack 40 --gdslack 15 --ops gfree,pullD,osc,trb,skel,join,deep,polish $EXTRA
    ;;
  worker)
    python3 $S/t1run.py --goal $2 --seed $3 --hours $4 --data $O/run --name ons-$2-$3 \
      --shared shared-ns --no-hub --admax 5 --gslack 40 --gdslack 15 --ops gfree,pullD,osc,trb,skel,join,deep,polish $EXTRA
    ;;
esac
