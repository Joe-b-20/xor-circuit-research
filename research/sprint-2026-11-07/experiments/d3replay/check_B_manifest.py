#!/usr/bin/env python3
"""Compare a checkpoint tree against ordinary_completion/CHECKPOINT_MANIFEST.json.
Usage: python3 -I check_B_manifest.py <checkpoint_root>
Reports missing, mismatched, extra files. Does not execute anything."""
import hashlib, json, sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
man = json.loads((root / "ordinary_completion/CHECKPOINT_MANIFEST.json").read_text())
expected = man["file_sha256"]
missing, mismatch, ok = [], [], 0
for rel, sha in expected.items():
    p = root / rel
    if not p.is_file():
        missing.append(rel)
        continue
    if hashlib.sha256(p.read_bytes()).hexdigest() != sha:
        mismatch.append(rel)
    else:
        ok += 1
present = {str(p.relative_to(root)).replace("\\", "/") for p in root.rglob("*") if p.is_file()}
extra = sorted(present - set(expected))
print(json.dumps({
    "root": str(root),
    "manifest_entries": len(expected),
    "ok": ok,
    "missing": len(missing),
    "mismatch": len(mismatch),
    "extra": len(extra),
    "missing_list": missing,
    "mismatch_list": mismatch,
    "extra_list": extra[:50],
    "manifest_keys": [k for k in man.keys() if k != "file_sha256"],
}, indent=2))
