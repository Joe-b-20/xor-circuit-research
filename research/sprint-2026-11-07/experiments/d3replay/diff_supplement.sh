#!/bin/bash
# Byte-compare the repo edition's supplement/inherited modules with the archived
# originals (Nov-4 audit copy, hashes equal to the 27-Oct repaired inventory).
S=/home/joebachir20/xs-campaigns/2026-11-07-sprint/d3replay/A/lb93/supplement/inherited
O=/home/joebachir20/xs-campaigns/2026-11-07-sprint/import/zip/research/XOR_Adversarial_Audit_2026-11-04/technical/inherited
for f in build_lp.py cuts.py mcmatrix.py model3.py; do
  echo "=== $f  supplement=$(stat -c %s "$S/$f") B  original=$(stat -c %s "$O/$f") B"
  diff "$S/$f" "$O/$f" > /tmp/d3diff.txt; rc=$?
  echo "diff rc=$rc  (0=identical text, 1=differs)"; head -6 /tmp/d3diff.txt
  cmp "$S/$f" "$O/$f"
  echo -n "supplement tail bytes: "; tail -c 4 "$S/$f" | xxd -p
  echo -n "original   tail bytes: "; tail -c 4 "$O/$f" | xxd -p
  echo -n "ignoring trailing newline, sha256 equal: "
  if [ "$(sed -e '$a\' "$S/$f" | sha256sum)" = "$(sed -e '$a\' "$O/$f" | sha256sum)" ]; then echo yes; else echo no; fi
done
rm -f /tmp/d3diff.txt
