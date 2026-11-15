"""Check: every nonzero GF(2)-combination of the AES S-box output bits has algebraic degree 7
(input to the [P] bound MC >= 13 in NOTES.md section 4)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xag
from xag import gf
SBOX = [0] * 256
for p in range(256):
    b = gf.INV[p]; s = 0x63
    for i in range(5):
        s ^= b; b = ((b << 1) | (b >> 7)) & 0xFF
    SBOX[p] = s
bits = [gf.bit_table(SBOX, k) for k in range(8)]
degs = {}
for m in range(1, 256):
    t = 0
    for k in range(8):
        if m >> k & 1: t ^= bits[k]
    d = xag.anf_degree(t); degs[d] = degs.get(d, 0) + 1
print("degree histogram of the 255 nonzero output combinations:", degs)
