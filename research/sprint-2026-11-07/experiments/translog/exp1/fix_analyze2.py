#!/usr/bin/env python3
"""Fix 2 for analyze_exp1.py: a hard per-compress timeout (SIGALRM, default 60 s; compress's own
time_limit is loose: one 265k-state product took 350 s), a plateau cache keyed by v3 signature
with a membership check before reuse, and 40 % of the exact budget for coincidences."""
from pathlib import Path
p = Path.home() / "xs-campaigns/2026-11-07-sprint/translog/exp1/analyze_exp1.py"
t = p.read_text()
edits = [
    ('import glob\nimport json\nimport os\nimport random\n',
     'import glob\nimport json\nimport os\nimport random\nimport signal\n'),
    ('MAX_HOPS = int(sys.argv[2]) if len(sys.argv) > 2 else 400\n',
     'MAX_HOPS = int(sys.argv[2]) if len(sys.argv) > 2 else 400\n'
     'PER_CALL = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0\n\n\n'
     'class CompressTimeout(Exception):\n    pass\n\n\n'
     'def _alarm(signum, frame):\n    raise CompressTimeout()\n\n\n'
     'signal.signal(signal.SIGALRM, _alarm)\n'),
    ('def compress_state(values, time_limit=120):\n'
     '    hk = hk_of(values)\n'
     '    if hk is None:\n'
     '        return None, {"error": "not an 88 state"}\n'
     '    pl, info = pes_lib.compress(sp, hk, verify_limit=20000, closure_limit=3000, time_limit=time_limit)\n',
     'PL_CACHE = {}   # v3 signature -> list of (Plateau, info) already computed\n\n\n'
     'def compress_state(values, time_limit=None, sig=None):\n'
     '    hk = hk_of(values)\n'
     '    if hk is None:\n'
     '        return None, {"error": "not an 88 state"}\n'
     '    if sig is not None:\n'
     '        for pl0, info0 in PL_CACHE.get(sig, ()):\n'
     '            if member(pl0, values):\n'
     '                return pl0, {**info0, "cached": True}\n'
     '    time_limit = time_limit or PER_CALL\n'
     '    signal.alarm(int(time_limit) + 5)\n'
     '    try:\n'
     '        pl, info = pes_lib.compress(sp, hk, verify_limit=20000, closure_limit=3000, time_limit=time_limit)\n'
     '    except CompressTimeout:\n'
     '        return None, {"error": "timeout", "seconds": time_limit}\n'
     '    finally:\n'
     '        signal.alarm(0)\n'),
    ('    return pl, {"kind": pl.kind, "size": pl.size(), "radices": pl.radices() if pl.kind == "product" else None,\n'
     '                "verified": info.get("verified"), "note": info.get("note"), "seconds": info.get("seconds"),\n'
     '                "inexact": bool(inexact), "downs": len(info.get("downs") or [])}\n',
     '    out = {"kind": pl.kind, "size": pl.size(), "radices": pl.radices() if pl.kind == "product" else None,\n'
     '           "verified": info.get("verified"), "note": info.get("note"), "seconds": info.get("seconds"),\n'
     '           "inexact": bool(inexact), "downs": len(info.get("downs") or [])}\n'
     '    if sig is not None:\n'
     '        PL_CACHE.setdefault(sig, []).append((pl, out))\n'
     '    return pl, out\n'),
    # coincidences: 40 % of the budget, timeouts counted
    ('    if exact_time_left() < 0.4 * EXACT_CAP:\n        break\n    ws = sorted(ws)\n',
     '    if exact_time_left() < 0.6 * EXACT_CAP:\n        break\n    ws = sorted(ws)\n'),
    ('    try:\n        pl, info = compress_state(e0["v"])\n    except Exception as exc:  # noqa: BLE001\n'
     '        Q2b["errors"] += 1\n        exact_log.write(json.dumps({"item": "coincidence", "sig": s, "error": str(exc)}) + "\\n")\n'
     '        continue\n    if pl is None:\n        Q2b["errors"] += 1\n        continue\n',
     '    try:\n        pl, info = compress_state(e0["v"], sig=s)\n    except Exception as exc:  # noqa: BLE001\n'
     '        Q2b["errors"] += 1\n        exact_log.write(json.dumps({"item": "coincidence", "sig": s, "error": str(exc)}) + "\\n")\n'
     '        continue\n    if pl is None:\n'
     '        Q2b["timeouts"] = Q2b.get("timeouts", 0) + (info.get("error") == "timeout")\n'
     '        Q2b["errors"] += info.get("error") != "timeout"\n'
     '        exact_log.write(json.dumps({"item": "coincidence", "sig": s, "workers": ws, "outcome": info.get("error")}) + "\\n")\n'
     '        continue\n'),
    ('    try:\n        pl, info = compress_state(e2["v"])\n    except Exception as exc:  # noqa: BLE001\n'
     '        Q2a["errors"] += 1\n        continue\n    if pl is None:\n        Q2a["errors"] += 1\n        continue\n',
     '    try:\n        pl, info = compress_state(e2["v"], sig=e2["sig"])\n    except Exception as exc:  # noqa: BLE001\n'
     '        Q2a["errors"] += 1\n        continue\n    if pl is None:\n'
     '        Q2a["timeouts"] = Q2a.get("timeouts", 0) + (info.get("error") == "timeout")\n'
     '        Q2a["errors"] += info.get("error") != "timeout"\n'
     '        exact_log.write(json.dumps({"item": "hop", "worker": w, "it_exit": xr["it"], "outcome": info.get("error"),\n'
     '                                    "v3_same": e1["sig"] == e2["sig"]}) + "\\n")\n'
     '        continue\n'),
]
for old, new in edits:
    assert t.count(old) == 1, old[:80]
    t = t.replace(old, new)
p.write_text(t)
print("fix2 applied")
