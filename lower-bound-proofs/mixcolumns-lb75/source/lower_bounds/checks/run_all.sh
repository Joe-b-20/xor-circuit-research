#!/bin/sh
# Runs every check of this folder and FAILS LOUDLY if any check fails.
#   sh run_all.sh            Python 3 standard library only (about 2 minutes on one core)
#   sh run_all.sh --with-lp  also runs the optional LP cross-check lp_regen.py (needs numpy and scipy)
# Each script's full output goes to logs/<script>.log; the last lines are echoed on success and the
# whole log on failure. The stress and LP reports are validated explicitly (their scripts also exit
# nonzero on failure since version 1.1). This validates process outcomes and reports; it does not
# certify the mathematics, which is sections 1-11 of the proof note.
set -eu
unset PYTHONOPTIMIZE 2>/dev/null || true     # the checkers use assertions; -O would silence them
cd "$(dirname "$0")" || exit 1
with_lp=0
case "${1-}" in
    "") ;;
    --with-lp) with_lp=1 ;;
    *) printf 'Usage: sh run_all.sh [--with-lp]\n' >&2; exit 2 ;;
esac
[ "$#" -le 1 ] || { printf 'Usage: sh run_all.sh [--with-lp]\n' >&2; exit 2; }
mkdir -p logs
run() {
    script=$1; log=logs/${script%.py}.log
    printf '\n=== %s\n' "$script"
    if python3 "$script" > "$log" 2>&1; then
        tail -n 6 "$log"
    else
        status=$?
        cat "$log"
        printf '\nFAILED: %s exited with status %s (full log above)\n' "$script" "$status" >&2
        exit 1
    fi
}
for s in finite_facts.py check72.py check73.py check_dark_source.py certify74.py independent74.py \
         certify75.py independent75.py stress.py; do
    run "$s"
done
# Validate the stress report explicitly: a nonempty failure list or an empty circuit collection fails.
python3 - <<'PY'
import json
from pathlib import Path
report = json.loads(Path('stress.json').read_text())
count = report.get('circuits')
if type(count) is not int or count <= 0 or report.get('failures') != []:
    raise SystemExit('FAILED: the stress test reported failures or tested no circuits: ' + repr({'circuits': count, 'failures': report.get('failures')}))
print(f'Stress report accepted: {count} circuits, no failures.')
PY
if [ "$with_lp" -eq 1 ]; then
    run lp_regen.py
    python3 - <<'PY'
import json
from pathlib import Path
report = json.loads(Path('lp_regen_74.json').read_text())
expected = {'G74_states': 1102, 'G74_claims': 2204, 'G74_survivors': 0, 'identical_claims': 2204,
            'mine_below_certified': 0, 'certified_but_feasible_in_mine': 0, 'unknown_lp': []}
errors = {k: {'expected': v, 'actual': report.get(k)} for k, v in expected.items() if report.get(k) != v}
if errors:
    raise SystemExit('FAILED: the LP cross-check report does not match the version 1.1 expectations: ' + repr(errors))
print('LP cross-check report matches the expectations: 0 survivors, 2,204 identical claims.')
PY
fi
printf '\nALL CHECKS PASSED (%s)\n' "$([ "$with_lp" -eq 1 ] && echo 'standard-library checks + LP cross-check' || echo 'standard-library checks')"
