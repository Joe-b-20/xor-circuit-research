"""per cut: least far among circuits with no exit at that cut (and least far overall), witnesses."""
import sys, os, glob, json
import olib
HOME = os.path.expanduser("~/xor-circuit-research")
KSTE = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor")

def sources():
    for f in ("xor88-depth5", "xor89-depth4", "xor97-depth3"):
        p = HOME + "/circuits/aes-mixcolumns/aes-mixcolumns-%s.circ.txt" % f
        yield "circuits/aes-mixcolumns/" + os.path.basename(p), 0, olib.parse_ncff(p)
    rot = HOME + "/research/structure-2026-11-11/rotation"
    for p in sorted(glob.glob(rot + "/**/*", recursive=True)):
        if not os.path.isfile(p) or not (p.endswith(".ncff") or p.endswith(".txt")):
            continue
        try:
            txt = open(p, errors="replace").read(200000)
        except Exception:
            continue
        if "XOR " not in txt or "x31" not in txt:
            continue
        try:
            g = olib.parse_ncff(p)
        except Exception:
            continue
        if g:
            yield os.path.relpath(p, HOME), 0, g
    for fn in ("circuits_1.txt", "circuits_2.txt", "circuits_3.txt", "circuits_depth5.txt"):
        for ln, line in enumerate(open(os.path.join(KSTE, fn)), 1):
            if line.strip():
                yield "kste/" + fn, ln, olib.parse_pairs(line)

WP = [olib.W_info(olib.ROWS, olib.PBLOCK[b]) for b in range(8)]
WM = [olib.W_info(olib.MROWS, olib.MBLOCK[k]) for k in range(8)]
