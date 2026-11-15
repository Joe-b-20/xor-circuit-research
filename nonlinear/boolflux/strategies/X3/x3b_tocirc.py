"""X3b: convert kernel .bfx files to NCFF .circ.txt (for H1's xag/decomp, which read NCFF).
usage: python3 x3b_tocirc.py OUTDIR FILE.bfx ..."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / 'xcr-boolflux/nonlinear/boolflux'))
import core
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
for f in sys.argv[2:]:
    c = core.from_kernel(Path(f).read_text(), Path(f).stem)
    t = core.write_ncff(c, comments=['converted by X3b from ' + f])
    (out / (Path(f).stem + '.circ.txt')).write_text(t)
    print('wrote', out / (Path(f).stem + '.circ.txt'))
