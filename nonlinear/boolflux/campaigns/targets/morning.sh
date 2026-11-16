#!/bin/bash
# Morning curation and verification of the targeted campaign (2026-11-15) and the night runs
# (2026-11-16), one command, for 13:30-14:00 UTC after all runs have stopped.  L1, 2026-11-16.
#
#   bash nonlinear/boolflux/campaigns/targets/morning.sh              # real run, in this worktree
#   bash nonlinear/boolflux/campaigns/targets/morning.sh --dry-run [DIR]
#        same steps on a copy of the worktree in DIR (default ~/xs-campaigns/2026-11-15-targets/L1/dryrun-<stamp>);
#        the worktree, the campaign's LEDGER.md/json and results/ are not touched
#
# Environment: MORNING_CPU (default 18; any free CPU), XS_MEM (default 4G), MORNING_TESTS=0 skips the
# unit tests.  Never commits, never pushes.  Steps (each logged in LOG/<step>.log, timed):
#   a  ledger.py run                        LEDGER.md/json (campaign folder; dry run: DIR/ledger)
#   b  ledger.py curate --apply             new campaign/night frontier points -> results/targets/<ID>/ (the ledger's
#                                           representative file: certified search path wins a tie; a curated entry of
#                                           the same tuple from another file is replaced); every entry refreshed: class
#                                           fields, corrections.json, header comments, logs/<name>/ start.circ.txt,
#                                           command.sh, REPRODUCE.md, aes_check.json, found.json
#   c  campaign record                      LEDGER.md/json, BRIEF*.md, COMPLIANCE-1820.md, QUEUE.md, TARGETS.json,
#                                           USER-REQUEST.md -> results/targets/; night folder *.md/*.json -> results/targets/night-2026-11-16/
#   e1 curate_aes.py                        new Pareto points (best_table rule) -> results/aes/ with provenance
#   e2 manifest.py                          results/MANIFEST.json + results/nist-format/
#   d  best_table.py --md results/BEST.md   after e, so the rows cite the curated results/aes files
#   f1 verify_all.py                        results + nist-format + results/targets/*/*.circ.txt + campaigns
#                                           (2026-11-13-aes, 2026-11-15-targets, night) + nist pin
#   f2 BEST.md vs MANIFEST.json             BEST.json rows == MANIFEST aes_pareto (fails otherwise)
#   f3 unittest discover nonlinear/boolflux/tests
# Exit status: 0 if every step passed, 1 otherwise (all steps still run unless a prerequisite failed).
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=$(cd "$HERE/../../../.." && pwd)
CAMP=${LEDGER_CAMPAIGN:-$HOME/xs-campaigns/2026-11-15-targets}
NIGHT=${LEDGER_NIGHT:-$HOME/xs-campaigns/2026-11-16-night}
GUARD=$HOME/xs-campaigns/guard/xsfg
CPU=${MORNING_CPU:-18}
export XS_MEM=${XS_MEM:-4G}
export GIT_OPTIONAL_LOCKS=0                 # never let a git status in a copy rewrite the shared index
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
T0=$(date +%s)

if [ "${1:-}" = "--dry-run" ]; then
  DIR=${2:-$CAMP/L1/dryrun-$STAMP}
  mkdir -p "$DIR"
  echo "dry run: copying $REPO -> $DIR/repo"
  rsync -a --delete --exclude '__pycache__' "$REPO/" "$DIR/repo/" || { echo "copy failed"; exit 1; }
  echo "copy: $(( $(date +%s) - T0 )) s"
  MORNING_COPY_S=$(( $(date +%s) - T0 )) MORNING_DRY=1 LEDGER_OUT="$DIR/ledger" MORNING_LOG="$DIR/log" \
    MORNING_BEST_OUT="$DIR/best" bash "$DIR/repo/nonlinear/boolflux/campaigns/targets/morning.sh" --in-copy
  rc=$?
  echo "dry run finished (exit $rc) in $(( $(date +%s) - T0 )) s; copy left in $DIR (delete it when done)"
  exit $rc
fi

DRY=${MORNING_DRY:-0}
LOG=${MORNING_LOG:-$CAMP/L1/morning-$STAMP}
LOUT=${LEDGER_OUT:-$CAMP}
BEST_OUT=${MORNING_BEST_OUT:-$CAMP/L1/best}
PKG=$REPO/nonlinear/boolflux
RT=$PKG/results/targets
mkdir -p "$LOG" "$LOUT" "$BEST_OUT"
export LEDGER_OUT=$LOUT LEDGER_CAMPAIGN=$CAMP LEDGER_NIGHT=$NIGHT
cd "$REPO" || exit 1

declare -a NAMES STATUS SECS
FAILED=0
run() {                                     # run NAME CMD...: guarded, pinned, logged, timed
  local name=$1; shift
  local t=$(date +%s)
  echo "=== [$name] $*" | tee -a "$LOG/morning.log"
  "$GUARD" P -- taskset -c "$CPU" "$@" > "$LOG/$name.log" 2>&1
  local rc=$?
  local dt=$(( $(date +%s) - t ))
  NAMES+=("$name"); SECS+=("$dt")
  if [ $rc -eq 0 ]; then STATUS+=("ok"); else STATUS+=("FAIL($rc)"); FAILED=1; fi
  echo "    exit $rc, $dt s, log $LOG/$name.log" | tee -a "$LOG/morning.log"
  tail -3 "$LOG/$name.log" | sed 's/^/    | /'
  return $rc
}
skip() { NAMES+=("$1"); SECS+=(0); STATUS+=("SKIPPED ($2)"); FAILED=1; echo "=== [$1] skipped: $2"; }

echo "morning.sh $( [ "$DRY" = 1 ] && echo DRY RUN ) $(date -u +%FT%TZ) repo $REPO (git $(git rev-parse --short HEAD 2>/dev/null)) cpu $CPU log $LOG"

# a: ledger
if run a-ledger python3 "$PKG/campaigns/targets/ledger.py" run; then
  LEDGER_OK=1
  NFAIL=$(grep -o '([0-9]* FAIL' "$LOG/a-ledger.log" | grep -o '[0-9]*' | head -1)
  if [ "${NFAIL:-0}" != 0 ]; then
    NAMES+=("a-ledger-issues"); SECS+=(0); STATUS+=("FAIL ($NFAIL FAIL issues in LEDGER.md)"); FAILED=1
  fi
else
  LEDGER_OK=0
fi

# b: curate into results/targets (+ class fields)
if [ $LEDGER_OK = 1 ]; then
  run b-curate python3 "$PKG/campaigns/targets/ledger.py" curate --apply
else
  skip b-curate "ledger failed"
fi

# c: campaign record
if [ $LEDGER_OK = 1 ]; then
  rec() {
    set -e
    cp "$LOUT/LEDGER.md" "$LOUT/LEDGER.json" "$RT/"
    for f in BRIEF.md BRIEF2.md COMPLIANCE-1820.md QUEUE.md TARGETS.json USER-REQUEST.md; do
      if [ -f "$CAMP/$f" ]; then cp "$CAMP/$f" "$RT/$f"; echo "copied $f"; else echo "absent: $CAMP/$f"; fi
    done
    if [ -d "$NIGHT" ]; then
      mkdir -p "$RT/night-2026-11-16"
      find "$NIGHT" -maxdepth 1 -type f \( -name '*.md' -o -name '*.json' \) -size -2M -exec cp -v {} "$RT/night-2026-11-16/" \;
    else
      echo "no night folder $NIGHT"
    fi
    echo "record copied into $RT"
  }
  NAMES+=("c-record"); t=$(date +%s)
  if ( rec ) > "$LOG/c-record.log" 2>&1; then STATUS+=("ok"); else STATUS+=("FAIL"); FAILED=1; fi
  SECS+=($(( $(date +%s) - t ))); echo "=== [c-record] ${STATUS[-1]}"; tail -2 "$LOG/c-record.log" | sed 's/^/    | /'
else
  skip c-record "ledger failed"
fi

# e: curated manifest (results/aes + MANIFEST.json), then d: BEST.md
run e1-curate-aes python3 "$PKG/campaigns/curate_aes.py"
run e2-manifest python3 "$PKG/campaigns/manifest.py"
run d-best-table python3 "$PKG/campaigns/best_table.py" --out "$BEST_OUT" --md "$PKG/results/BEST.md" --clean

# f: verification and tests
CAMPS=("$HOME/xs-campaigns/2026-11-13-aes" "$CAMP")
[ -d "$NIGHT" ] && CAMPS+=("$NIGHT")
AGREE='
import json, sys
best = {tuple(r["tuple_A_AD_G_GD"]) for r in json.load(open(sys.argv[1]))["rows"] if r.get("file")}
man = json.load(open(sys.argv[2]))
par = {tuple(t) for t in man["aes_pareto"]["tuples_A_AD_G_GD"]}
files = {tuple(e["pinned_set"]["tuple_A_AD_G_GD"]) for e in man["entries"] if "pinned_set" in e}
fmt = lambda s: ", ".join("%d/%d/%d/%d" % t for t in sorted(s)) or "none"
print("BEST.md rows %d, MANIFEST aes_pareto %d, MANIFEST AES entries %d tuples" % (len(best), len(par), len(files)))
print("in BEST.md, not in MANIFEST.json (no curated file):", fmt(best - files))
print("in BEST.md, not in aes_pareto:", fmt(best - par))
print("in aes_pareto, not in BEST.md:", fmt(par - best))
sys.exit(0 if best == par else 1)'
run f1-verify-all python3 "$PKG/campaigns/verify_all.py" --json "$LOG/verify_all.json" --quiet --campaigns "${CAMPS[@]}"
run f2-best-vs-manifest python3 -c "$AGREE" "$BEST_OUT/BEST.json" "$PKG/results/MANIFEST.json"
if [ "${MORNING_TESTS:-1}" != 0 ]; then
  run f3-tests python3 -m unittest discover -s nonlinear/boolflux/tests -t nonlinear
else
  skip f3-tests "MORNING_TESTS=0"
fi

# summary
TOTAL=$(( $(date +%s) - T0 + ${MORNING_COPY_S:-0} ))
{
echo
echo "================ morning.sh summary $( [ "$DRY" = 1 ] && echo '(DRY RUN on a copy)' ) $(date -u +%FT%TZ) ================"
for i in "${!NAMES[@]}"; do printf '  %-22s %-40s %5s s\n' "${NAMES[$i]}" "${STATUS[$i]}" "${SECS[$i]}"; done
echo "  total ${TOTAL} s$( [ -n "${MORNING_COPY_S:-}" ] && echo " (incl. ${MORNING_COPY_S} s copy)" )"
echo
echo "--- ledger ($LOUT/LEDGER.md)"
grep -m1 '^ledger:' "$LOG/a-ledger.log"
grep '^CHANGE\|^FAIL\|^NOTE' "$LOG/a-ledger.log" | head -40
awk '/^## Summary/{p=1;next} /^## /{p=0} p' "$LOUT/LEDGER.md" | grep '^| T' | cut -c1-260
echo "--- curate (results/targets)"; grep -E 'files planned|refreshed|copied |HEADER NOT' "$LOG/b-curate.log" 2>/dev/null | tail -30
echo "--- curate_aes (results/aes)"; grep -E 'Pareto tuples|NO PROVENANCE|NOT WRITTEN|could not be read' "$LOG/e1-curate-aes.log" | head
grep -c ' <- ' "$LOG/e1-curate-aes.log" | sed 's/^/    circuits written: /'
echo "--- manifest"; tail -2 "$LOG/e2-manifest.log"
echo "--- best_table"; grep '^Candidates' "$LOG/d-best-table.log"
echo "--- verify_all"; grep -E '^(results|nist-format|targets|campaigns) |^RESULT|^FAIL|^AES tuples' "$LOG/f1-verify-all.log"
echo "--- BEST.md vs MANIFEST.json"; cat "$LOG/f2-best-vs-manifest.log"
echo "--- tests"; grep -E '^Ran |^OK|^FAILED' "$LOG/f3-tests.log" 2>/dev/null
echo "--- files changed under nonlinear/boolflux/results (git status, not committed)"
git status --short --untracked-files=all -- nonlinear/boolflux/results | awk '{print $1}' | sort | uniq -c
git status --short -- nonlinear/boolflux/results | head -15
echo
if [ $FAILED = 0 ]; then echo "MORNING: ALL OK"; else echo "MORNING: FAILURES (see the steps above and $LOG)"; fi
} | tee "$LOG/SUMMARY.txt"
exit $FAILED
