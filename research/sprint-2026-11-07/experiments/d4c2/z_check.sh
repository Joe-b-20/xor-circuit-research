#!/bin/bash
# z_check.sh -- earlier PowerShell one-liners passed  s/\r$//  to sed with the backslash eaten, i.e. they ran
# sed 's/r$//' (drop a trailing r).  Find any line that lost its trailing r: diff the copies against the d4c
# originals, and list lines of my own files that end in a letter typical of a truncated word ending in r.
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
echo "== diff c2_model.py e2_model.py (only intended edits expected)"
diff ../d4c/c2_model.py e2_model.py | grep -E '^[<>]' | grep -v -E '^>' | head -40
echo "== removed/changed original lines in e5_verify"
diff ../d4c/c5_verify.py e5_verify.py | grep -E '^<' | head
echo "== c2 lines ending in r (would have been truncated)"
grep -n -E 'r$' ../d4c/c2_model.py ../d4c/c5_verify.py ../d4c/c3_run.py | head
echo "== lines in d4c2 files ending in e/o/a/u (candidates for lost r)"
grep -n -E '(numbe|orde|othe|ove|afte|eithe|neve|whethe|helpe|solve|unde|fo|o|pe|pai|filte|header|ca|ve|t|ou)$' e2_model.py e3_run.py e5_verify.py r3.sh r4.sh z_status.sh z_int.sh | head -40
