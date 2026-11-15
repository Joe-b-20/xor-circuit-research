#!/usr/bin/env python3
"""X2: save archive records as NCFF + JSON sidecar into a found/ dir and run aes_check.py on them.
    python3 save_found.py OUTDIR CAMPAIGN:ID [CAMPAIGN:ID ...]"""
import json, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from boolflux.hub.common import core, MODEL, metrics   # noqa: E402
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
chk = Path(__file__).resolve().parents[2] / 'campaigns' / 'aes_check.py'
for spec in sys.argv[2:]:
    camp, i = spec.rsplit(':', 1); camp = Path(camp)
    r = json.loads((camp / 'archive' / (i + '.json')).read_text())
    c = core.from_kernel((camp / 'archive' / (i + '.bfx')).read_text(), i); m = metrics(c)
    base = 'aes-sbox-a%d-ad%d-g%d-gd%d-%s' % (m[0], m[1], m[2], m[3], i)
    f = out / (base + '.circ.txt'); f.write_text(core.write_ncff(c, MODEL))
    p = subprocess.run([sys.executable, str(chk), str(f), '--json', str(out / (base + '.aes_check.json'))], capture_output=True, text=True)
    side = {'id': i, 'metrics': list(m), 'campaign': str(camp), 'operator': r['operator'], 'parents': r['parents'], 'seed': r.get('seed'),
            'run_id': r.get('run_id'), 'code_version': r.get('code_version'), 'operator_settings': r.get('operator_settings'),
            'aes_check_ok': p.returncode == 0, 'saved_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    (out / (base + '.json')).write_text(json.dumps(side, indent=1, default=str))
    print(base, 'aes_check', 'OK' if p.returncode == 0 else 'FAIL'); print(p.stdout[-600:])
