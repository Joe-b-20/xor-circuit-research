#!/usr/bin/env python3
"""List files the B replay regenerated (manifest mismatches, non-cache extras) and
compare each regenerated JSON record with the archived copy, ignoring timing fields."""
import hashlib, json
from pathlib import Path

D = Path("/home/joebachir20/xs-campaigns/2026-11-07-sprint/d3replay")
RESTORED, RAW = D / "B/restored", D / "B/ckpt_raw"
man = json.loads((RESTORED / "ordinary_completion/CHECKPOINT_MANIFEST.json").read_text())["file_sha256"]
mismatch = [rel for rel, sha in man.items()
            if (RESTORED / rel).is_file() and hashlib.sha256((RESTORED / rel).read_bytes()).hexdigest() != sha]
present = {str(p.relative_to(RESTORED)).replace("\\", "/") for p in RESTORED.rglob("*") if p.is_file()}
extra = sorted(p for p in present - set(man) if "__pycache__" not in p)
print("REGENERATED (hash differs from manifest):")
for m in mismatch:
    print("  ", m)
print("EXTRA (non-cache):", extra)

TIMING = ("second", "elapsed", "time", "nodes", "sha256", "started", "finished")
def strip(x):
    if isinstance(x, dict):
        return {k: strip(v) for k, v in x.items() if not any(t in k.lower() for t in TIMING)}
    if isinstance(x, list):
        return [strip(v) for v in x]
    return x

print("COMPARISON regenerated vs archived (ignoring timing/node/hash fields):")
for rel in mismatch:
    a_path, b_path = RESTORED / rel, RAW / rel
    if not b_path.is_file():
        print("  ", rel, ": archived copy absent in browsing tree (dedup) ; status", end=" ")
        try:
            print(json.loads(a_path.read_text()).get("status"))
        except Exception:
            print("(not json)")
        continue
    if rel.endswith(".json"):
        a, b = json.loads(a_path.read_text()), json.loads(b_path.read_text())
        same = strip(a) == strip(b)
        print("  ", rel, ": status", a.get("status") if isinstance(a, dict) else "-", "| equal_ignoring_timing:", same)
        if not same and isinstance(a, dict) and isinstance(b, dict):
            diff = [k for k in set(a) | set(b) if strip(a.get(k)) != strip(b.get(k))]
            print("      differing keys:", diff[:12])
    else:
        print("  ", rel, ": byte-equal:", a_path.read_bytes() == b_path.read_bytes())
