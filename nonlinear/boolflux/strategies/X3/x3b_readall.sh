#!/bin/bash
# X3b: dump STATUS.md of the study agents and the headings / mtimes of their NOTES.md
cd ~/xcr-boolflux/nonlinear/boolflux/strategies
for a in H1 H2 H3 H4 X1 R1 R2; do
  echo "=== $a  NOTES mtime $(date -u -r $a/NOTES.md +%H:%M) STATUS mtime $(date -u -r $a/STATUS.md +%H:%M)"
  cat $a/STATUS.md
  echo "--- headings"; grep -n "^#" $a/NOTES.md
done
