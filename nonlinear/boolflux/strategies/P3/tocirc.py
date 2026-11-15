"""Convert archive .bfx (or .circ.txt) files to verified NCFF starts: tocirc.py OUTDIR FILE...
Prints name, metrics and sha256 of each written start."""
import hashlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from boolflux import core, targets  # noqa
MODEL = core.Model.load('nist')
AES = targets.aes_sbox()
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
for f in sys.argv[2:]:
    p = Path(f)
    c = core.from_kernel(p.read_text()) if p.suffix == '.bfx' else core.read_ncff(str(p))
    assert c.value_table() == AES, f
    m = c.metrics(MODEL)
    name = 'a%d-ad%d-g%d-gd%d-%s.circ.txt' % (m['A'], m['AD'], m['G'], m['GD'], p.name.split('.')[0][:12])
    txt = core.write_ncff(c, MODEL, comments=['P3 start converted from ' + str(p)])
    (out / name).write_text(txt)
    print(name, m['A'], m['AD'], m['G'], m['GD'], hashlib.sha256(txt.encode()).hexdigest())
