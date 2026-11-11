#!/usr/bin/env python3
"""controls_bf2.py -- brute-force comparison, memory-bounded (replaces the aborted full-domain control_bruteforce).

Sub-case: two hubs of type (r,u) = (2,2) sharing exactly one label, nothing else (A = 0).
Sub-domain D (defined on the OBJECT, independently of either program, rotation-closed):
   (i)  the shared label lies in LSET = the rotation closure of {h + b : h in M40, b in B}, M40 = every 15th of the sorted
        M^T values with at least two boundary triples (40 masks; not orbit representatives);
   (ii) both private labels have Hamming weight <= PMAX.
naive : nested loops over ALL masks with >= 2 triples for hub 1, all pairs of its triples, all ends, hub 2 = shared label +
        end, its triple pairs, its private end; (i), (ii) are tested on the values; R7 by ONE full rank computation
        (geo_q3.rank_hi) per complete configuration; nothing imported from enum_q3.
pruned: enum_q3.Realizer on the skeleton [(2,{0,1}), (2,{0,2})], root filter (i) and label filter (ii) through the guide
        hooks, once without the rotation reduction and once with it (survivors expanded by the four rotations).
Every surviving configuration is written as one canonical line to a file (streamed); the three files are compared by
`sort -u | sha256sum` and line counts.  No set of configurations is held in memory.
"""
import sys, json, time, itertools, subprocess, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import geo_q3
PMAX = 2          # (PMAX = 6 gave 33.6M naive lines; aborted and reduced)
OUTDIR = HERE / "bf2"


def domain(geo):
    rep = sorted(h for h, T in geo.trip.items() if len(T) >= 2)
    M40 = rep[::15][:40]
    L = set()
    for h in M40:
        for b in geo.B:
            l = h ^ b
            for _ in range(4):
                L.add(l); l = geo_q3.rot(l)
    return M40, L


def line(h1, R1, labs1, h2, R2, labs2):
    a = "%x;%s;%s" % (h1, ",".join("%x" % t for t in sorted(R1)), ",".join("%x" % l for l in sorted(labs1)))
    b = "%x;%s;%s" % (h2, ",".join("%x" % t for t in sorted(R2)), ",".join("%x" % l for l in sorted(labs2)))
    return "|".join(sorted((a, b)))


def naive(geo, LSET, fn):
    B = geo.B; Bset = geo.Bset; Bidx = geo.Bidx
    rep = {h: T for h, T in geo.trip.items() if len(T) >= 2}
    H1 = 1 << 64; H2 = 1 << 65; n = 0; n_rank = 0
    pc = lambda x: bin(x).count("1")
    with open(fn, "w") as f:
        for h1, T1 in rep.items():
            for R1 in itertools.combinations(T1, 2):
                for b1 in B:
                    l1 = h1 ^ b1
                    if l1 not in LSET: continue
                    for b2 in B:
                        if b2 == b1: continue
                        h2 = l1 ^ b2
                        if h2 in Bset or h2 == h1 or h2 not in rep: continue
                        for R2 in itertools.combinations(rep[h2], 2):
                            vecs = [T | H1 for T in R1] + [T | H2 for T in R2] + [H1 | H2 | (1 << Bidx[b1]) | (1 << Bidx[b2])]
                            for b1p in B:
                                if b1p == b1: continue
                                l2 = h1 ^ b1p
                                if pc(l2) > PMAX or l2 == l1: continue
                                for b2p in B:
                                    if b2p == b2: continue
                                    l3 = h2 ^ b2p
                                    if pc(l3) > PMAX or l3 == l1 or l3 == l2: continue
                                    n_rank += 1
                                    if geo_q3.rank_hi(vecs) == 5:
                                        f.write(line(h1, R1, (l1, l2), h2, R2, (l1, l3)) + "\n"); n += 1
    return n, n_rank


class DomGuide:
    def __init__(self, LSET): self.L = LSET
    def ok_root(self, s, l): return l in self.L
    def ok_label(self, s, l): return bin(l).count("1") <= PMAX
    def ok_mask(self, role, h): return True
    def ok_helper(self, role, h, R): return True


def rot_triple(geo, T):
    return sum(1 << geo.Bidx[geo_q3.rot(geo.B[k])] for k in range(64) if T >> k & 1)


def pruned(geo, LSET, fn, sym):
    import enum_q3 as E
    skel = dict(roles=[[2, [0, 1]], [2, [0, 2]]], status=["B", "B", "B"], W=[4, 2, 2], counts={"2,2": 2})
    pl = E.plan(skel, sym_first_root=sym)
    f = open(fn, "w"); cnt = [0]

    class Sink(list):
        def append(self, snap):
            hs = [(h, tuple(R), [snap["labels"][s] for s in pl["roles"][i][1]]) for h, R, ends, i in snap["helpers"]]
            for _ in range(4 if sym else 1):
                f.write(line(hs[0][0], hs[0][1], hs[0][2], hs[1][0], hs[1][1], hs[1][2]) + "\n"); cnt[0] += 1
                hs = [(geo_q3.rot(h), tuple(rot_triple(geo, T) for T in R), [geo_q3.rot(l) for l in L]) for h, R, L in hs]
    R = E.Realizer(geo, pl, pl["order"], max_store=1, max_survivors=None, guide=DomGuide(LSET))
    R.survivors = Sink(); R.run(); f.close()
    return cnt[0], dict(R.stats)


def digest(fn):
    out = subprocess.run("sort -u %s | tee %s.sorted | sha256sum; wc -l < %s.sorted" % (fn, fn, fn), shell=True, capture_output=True, text=True).stdout.split()
    return out[0], int(out[-1])


if __name__ == "__main__":
    import enum_q3 as E
    t0 = time.time(); OUTDIR.mkdir(exist_ok=True)
    geo = E.build_geo()
    M40, LSET = domain(geo)
    res = dict(M40=[hex(h) for h in M40], LSET_size=len(LSET), PMAX=PMAX)
    c0 = time.process_time(); n, nr = naive(geo, LSET, OUTDIR / "naive.txt"); res["naive"] = dict(lines=n, rank_tests=nr, cpu=round(time.process_time() - c0, 1))
    print("naive", res["naive"], flush=True)
    for sym in (False, True):
        c0 = time.process_time(); n, st = pruned(geo, LSET, OUTDIR / ("pruned_%s.txt" % ("sym" if sym else "nosym")), sym)
        res["pruned_sym" if sym else "pruned_nosym"] = dict(lines=n, stats=st, cpu=round(time.process_time() - c0, 1))
        print("pruned sym=%s" % sym, res["pruned_sym" if sym else "pruned_nosym"], flush=True)
    for name in ("naive", "pruned_nosym", "pruned_sym"):
        h, c = digest(OUTDIR / (name + ".txt")); res[name]["sha256_sorted_unique"] = h; res[name]["distinct"] = c
    res["passed"] = (res["naive"]["sha256_sorted_unique"] == res["pruned_nosym"]["sha256_sorted_unique"] == res["pruned_sym"]["sha256_sorted_unique"] and res["naive"]["distinct"] > 0)
    res["seconds"] = round(time.time() - t0)
    json.dump(res, open(HERE / "controls_bf2.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "M40"}, indent=1))
