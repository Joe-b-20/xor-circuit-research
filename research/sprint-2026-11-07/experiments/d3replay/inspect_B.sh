#!/bin/bash
# Dump headers of the sub-checkers that verify_checkpoint.py invokes (read-only).
R=/home/joebachir20/xs-campaigns/2026-11-07-sprint/d3replay/B/restored/ordinary_completion
cd "$R" || exit 9
for f in boundary/check_boundary49_counterexample.py constructor_audit/replay.py two_group/targeted_controls.py core_interface/check_constructor_model.py core_audit/check_coverage.py core_audit/check_provenance.py core_audit/check_search.py boundary/minimum_tau_probe.py boundary/replay_minimum_tau_control.py; do
  echo "=================== $f  [lines: $(wc -l < "$f")]"
  head -${HEADN:-50} "$f"
done
echo "=================== RESTORE_REPORT public resolution"
python3 -I - <<'PY'
import json
r = json.load(open("/home/joebachir20/xs-campaigns/2026-11-07-sprint/d3replay/B/restored/RESTORE_REPORT.json"))
print("public_resolution_messages:", r.get("public_resolution_messages"))
print("status:", r.get("status"), "count:", r.get("restored_file_count"), "missing:", r.get("missing_or_failed_count"))
keys = set()
for f in r["restored_files"]:
    keys.update(f.keys())
print("record keys:", sorted(keys))
missing9 = ["normalization_contract/inputs/aes_forward.mat.txt","ordinary_completion/RESUME.txt",
 "ordinary_completion/constructor_audit/constructor107_control_2.txt","ordinary_completion/constructor_audit/constructor107_control_5.txt",
 "ordinary_completion/constructor_audit/constructor107_control_8.txt","ordinary_completion/constructor_audit/constructor107_control_9.txt",
 "ordinary_completion/two_group_audit/upper_cross_independent_replay.json","structural_tradeoff/boundary/general_floor_replay.json",
 "structural_tradeoff/core_equality/exhaust_bank_union.cpp"]
for f in r["restored_files"]:
    if f["member"] in missing9:
        print("dedup-restored:", {k: v for k, v in f.items() if k != "content_sha256"})
PY
