"""Shared pieces of the parallel exact catalogue (catalogue_all.sh): paths, state of a sample,
plateau key (= hunt/plateaus.py key_of), exact membership under the 4 byte rotations, and the
known-product store (hunt/plateaus.json products + giants/pl_*.json + giants/catalogue/pl/*.json)."""
import glob, json, os, sys
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import pes_lib  # noqa: E402

SPRINT = "/home/joebachir20/xs-campaigns/2026-11-07-sprint"
HUNT = SPRINT + "/hunt"
G = SPRINT + "/giants"
CAT = os.environ.get("CAT_DIR", G + "/catalogue")   # override only for tests
PLDIR = CAT + "/pl"
SAMPLE_FILES = [HUNT + "/samples.jsonl", HUNT + "/samplesC/samples.jsonl", HUNT + "/samplesD/samples.jsonl"]
STOP = G + "/STOP"
_sp = None


def space():
    global _sp
    if _sp is None:
        _sp = pes_lib.make_space("mc", None)
    return _sp


def key_of(pl):
    sp = space()
    allv = sorted(pl.allv) if pl.kind == "product" else sorted(set().union(*pl.states))
    k = min(sp.rot(tuple(allv), s) if s else tuple(allv) for s in sp.shifts)
    return "p" + pes_lib.h64(k).to_bytes(8, "big").hex()


def state_of_values(values):
    """helper tuple (hkey) of an 88 sample, or None if it does not trim to 88 (as plateaus.py)."""
    sp = space()
    st = sp.state([v for v in values if v not in sp.tset])
    if st.count() != 88:
        return None
    return tuple(sp.hkey(st))


class Known:
    """Known plateaus; refresh() picks up pl files written by other shards since the last call."""

    def __init__(self, products_json=CAT + "/products.json"):
        self.pl = {}
        self.seen_files = set()
        if os.path.exists(products_json):
            for k, d in json.load(open(products_json)).items():
                self.pl[k] = pes_lib.Plateau.from_json(d)
        self.refresh()

    def refresh(self):
        for f in glob.glob(G + "/pl_*.json") + glob.glob(PLDIR + "/*.json"):
            if f in self.seen_files:
                continue
            try:
                d = json.load(open(f))
            except Exception:
                continue          # being written; next refresh
            self.seen_files.add(f)
            k = os.path.basename(f)[:-5]
            k = k[3:] if k.startswith("pl_") else k
            self.pl.setdefault(k, pes_lib.Plateau.from_json(d))

    def member(self, hk):
        sp = space()
        for s in sp.shifts:
            S = frozenset(sp.rot(tuple(hk), s)) if s else frozenset(hk)
            for k, p in self.pl.items():
                if p.contains(S):
                    return k, s
        return None, None


def done_ids():
    """ids with a result line in any shard file (idempotence)."""
    out = {}
    for f in glob.glob(CAT + "/shard_*.jsonl"):
        for line in open(f):
            try:
                r = json.loads(line)
            except Exception:
                continue          # torn last line of a killed shard
            out[r["id"]] = r
    return out
