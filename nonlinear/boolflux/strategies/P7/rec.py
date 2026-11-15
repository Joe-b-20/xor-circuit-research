#!/usr/bin/env python3
"""P7: record a constructed circuit into P7/found with a full sidecar (p7job.record).

    rec.py TARGET CIRCUIT START NAME 'METHOD' 'COMMAND' SEED ELAPSED CAP_A CAP_AD CAP_GD
"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import p7job  # noqa: E402

t, circ, start, name, method, command, seed, el, ca, cad, cgd = sys.argv[1:12]
ok, m, line = p7job.record(t, circ, Path(start).resolve(), json.loads(method) if method.startswith('{') else {'engine': method},
                           command, int(seed), float(el), name, caps=(int(ca), int(cad), int(cgd)))
print(ok, m, line)
