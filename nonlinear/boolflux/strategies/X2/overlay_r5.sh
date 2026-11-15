#!/bin/bash
# X2 (after C3's x2compat/overlay.sh): build X2/r5tree = the boolflux-review5 package (symlinks) + the CURRENT
# main-tree hub/scheduler_goal.py, hub/goals.py and strategies/X2 (copies); neither worktree is touched.
set -e
R=~/xcr-review5/nonlinear; M=~/xcr-boolflux/nonlinear
T=/home/joebachir20/xs-campaigns/2026-11-15-study/X2/r5tree; rm -rf "$T"; mkdir -p "$T/nonlinear/boolflux/hub" "$T/nonlinear/boolflux/strategies"
for f in "$R"/boolflux/*; do b=$(basename "$f"); case $b in hub|strategies|__pycache__) ;; *) ln -s "$f" "$T/nonlinear/boolflux/$b";; esac; done
for f in "$R"/boolflux/hub/*; do b=$(basename "$f"); [ "$b" = __pycache__ ] || ln -s "$f" "$T/nonlinear/boolflux/hub/$b"; done
ln -s "$R/nist" "$T/nonlinear/nist"
rm -f "$T/nonlinear/boolflux/hub/scheduler_goal.py" "$T/nonlinear/boolflux/hub/goals.py"
cp "$M/boolflux/hub/scheduler_goal.py" "$M/boolflux/hub/goals.py" "$T/nonlinear/boolflux/hub/"
cp -r "$M/boolflux/strategies/X2" "$T/nonlinear/boolflux/strategies/X2"; rm -rf "$T/nonlinear/boolflux/strategies/X2/__pycache__"
echo "$T/nonlinear/boolflux/hub/scheduler_goal.py"
