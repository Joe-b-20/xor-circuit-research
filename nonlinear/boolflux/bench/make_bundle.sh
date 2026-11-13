#!/usr/bin/env bash
# Build the local review bundle (nothing is published): source at the current commit, configs,
# traces, benchmark data and tables, ABC comparator, reports, reproduction commands.
#   usage: make_bundle.sh OUTDIR     (writes OUTDIR/boolflux-review-bundle/ and a .tar.gz next to it)
set -euo pipefail
OUT=$1; C=$HOME/xs-campaigns/2026-11-13-boolflux
cd "$(dirname "$0")/../../.."
D=$OUT/boolflux-review-bundle; rm -rf "$D"; mkdir -p "$D"/{src,configs,traces,data,abc}
git archive HEAD nonlinear/boolflux nonlinear/nist/MANIFEST.json | tar -x -C "$D/src"
git log -1 --format='%H %ci %s' > "$D/src/COMMIT.txt"
cp nonlinear/boolflux/bench/REPORT.md nonlinear/boolflux/bench/MECHANICS.md "$D/"
cp nonlinear/boolflux/bench/REPRODUCE.md "$D/" 2>/dev/null || true
cp $C/bench/plan-v1.json $C/bench/plan-v2.json "$D/configs/"
cp -r nonlinear/boolflux/models "$D/configs/models"
python3 - "$D/configs/kernel-defaults.json" <<'EOF'
import json, sys
sys.path.insert(0, 'nonlinear/boolflux'); sys.path.insert(0, 'nonlinear')
import cli
json.dump({'gate_kernel_defaults': cli.DEFAULTS, 'skeleton_kernel_defaults': cli.SKEL_DEFAULTS}, open(sys.argv[1], 'w'), indent=1)
EOF
for t in maj3-trace.txt aes109-trace.txt aes142-trace.txt; do cp $C/traces/$t "$D/traces/"; done
cp $C/traces/maj3/moves.txt "$D/traces/maj3-moves.txt"; cp $C/traces/maj3/moves.txt.it* "$D/traces/" 2>/dev/null || true
for x in aes109 aes142; do
  gzip -c $C/traces/$x/moves.txt > "$D/traces/$x-moves.txt.gz"
  for f in $C/traces/$x/moves.txt.it*; do cp "$f" "$D/traces/$x-$(basename "$f" | sed 's/moves.txt.//')"; done
done
for v in v1 v2; do
  [ -d $C/bench/$v ] || continue
  mkdir -p "$D/data/$v"; cp $C/bench/$v/*.json "$D/data/$v/"
  cp $C/bench/tables-$v.md "$D/data/" 2>/dev/null || true
  # the final circuit of every run (verified) next to its run file
  mkdir -p "$D/data/$v-circuits"
  python3 - $C/bench/$v "$D/data/$v-circuits" <<'EOF'
import json, shutil, sys
from pathlib import Path
for f in Path(sys.argv[1]).glob('*.json'):
    r = json.loads(f.read_text())
    if r.get('final_file') and Path(r['final_file']).exists():
        shutil.copy(r['final_file'], Path(sys.argv[2]) / (r['run']['label'] + '.circ.txt'))
EOF
done
cp $C/bench/rebuild_penalty.json "$D/data/"
cp -r nonlinear/boolflux/bench/abc/* "$D/abc/"
(cd "$OUT" && tar -czf boolflux-review-bundle.tar.gz boolflux-review-bundle)
du -sh "$D" "$OUT/boolflux-review-bundle.tar.gz"
