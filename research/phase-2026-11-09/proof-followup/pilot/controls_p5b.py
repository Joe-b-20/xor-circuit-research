#!/usr/bin/env python3
"""controls_p5b.py -- supplement to P5: planted TRIANGLES (three helpers with u = 2 pairwise sharing the three labels), a
shape that no 3-label sub-configuration of a real phase has, and that the leaves' LP solutions and the pilot's witnesses use.

Construction (independent of enum_q3): helpers X, Y, Z with labels {l0,l1}, {l1,l2}, {l0,l2}.  With ends x0, x1 (X), y1, y2
(Y), z0, z2 (Z):  h_X + h_Z = x0 + z0,  h_X + h_Y = x1 + y1,  h_Y + h_Z = y2 + z2, so x0 + z0 + x1 + y1 + y2 + z2 = 0: the six
ends form a zero-sum boundary set of weight 6 (they are distinct in the objects planted here).  For every weight-6 zero-sum
word (found from the triple table: two disjoint triples with equal XOR) and every assignment of its six elements to
(x0, z0 | x1, y1 | y2, z2), every mask h_X such that h_X, h_Y = h_X + x1 + y1, h_Z = h_X + x0 + z0 are all triple values
gives a candidate; triples are chosen at random (r = 1 or 2 where available); optionally a fourth hub with u = 1, r = 2 on
one label.  A candidate is accepted iff verify_q3 passes R1-R7.  Each accepted object goes through controls_p5.check_object
(step S with the object's counts, step G guided, and step G unguided for the first ones).
"""
import sys, json, time, itertools, random
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import geo_q3, verify_q3 as V, controls_q3 as C, controls_p5 as P5

if __name__ == "__main__":
    t0 = time.time(); rng = random.Random(7); geo = P5.make_geo("Mt")
    B = geo.B; TV = geo.trip
    words = set()
    for h, T in TV.items():
        for a, b in itertools.combinations(T, 2):
            if not (a & b): words.add(a | b)
    words = sorted(words)
    print("weight-6 zero-sum words from the triple table:", len(words), flush=True)
    objs = []; tries = 0; kinds = Counter()
    tv_list = list(TV)
    while len(objs) < 240 and tries < 4000:
        tries += 1
        w = rng.choice(words); el = [B[i] for i in range(64) if w >> i & 1]; rng.shuffle(el)
        x0, z0, x1, y1, y2, z2 = el
        p1 = x1 ^ y1; p0 = x0 ^ z0
        cands = [h for h in tv_list if (h ^ p1) in TV and (h ^ p0) in TV]
        rng.shuffle(cands)
        for hX in cands[:2]:
            hY = hX ^ p1; hZ = hX ^ p0
            l0 = hX ^ x0; l1 = hX ^ x1; l2 = hY ^ y2
            if (hZ ^ l0) != z0 or (hZ ^ l2) != z2 or (hY ^ l1) != y1: continue
            hs = []
            for h, L in ((hX, [0, 1]), (hY, [1, 2]), (hZ, [0, 2])):
                T = TV[h]; r = min(len(T), rng.choice((1, 2))); hs.append((h, r, rng.sample(T, r), L))
            variant = "triangle"
            if rng.random() < 0.5:                 # a fourth hub: u = 1, r = 2 on one label
                s = rng.randrange(3); l = (l0, l1, l2)[s]
                extra = [(l ^ b, TV[l ^ b]) for b in B if (l ^ b) not in geo.Bset and len(TV.get(l ^ b, ())) >= 2 and (l ^ b) not in (hX, hY, hZ)]
                if extra:
                    h4, T4 = rng.choice(extra); hs2 = hs + [(h4, 2, rng.sample(T4, 2), [s])]
                    o2 = C.obj_from_parts(geo, [(l, st) for l, st in zip((l0, l1, l2), C.statuses(hs2, 3))], hs2)
                    if V.verify(o2, geo, lp_check=False)["all"][0]: objs.append(o2); kinds["triangle+hub"] += 1; continue
            o = C.obj_from_parts(geo, [(l, st) for l, st in zip((l0, l1, l2), C.statuses(hs, 3))], hs)
            if V.verify(o, geo, lp_check=False)["all"][0]: objs.append(o); kinds[variant] += 1
    print("planted triangles accepted by verify_q3:", len(objs), dict(kinds), "tries", tries, f"{time.time()-t0:.0f}s", flush=True)
    res = []; miss = []; feat = Counter(); ung = Counter(); rcount = Counter()
    for n, o in enumerate(objs):
        r = P5.check_object(geo, o, unguided=(n < 60), cap=15.0)
        for f in r["features"]: feat[f] += 1
        rcount[tuple(sorted(hp["r"] for hp in o["helpers"]))] += 1
        if "U" in r: ung[str(r["U"])] += 1
        if not r["S"] or r["kind"] != "constrained" or not r["G"] or r.get("U") is False: miss.append((o, {k: v for k, v in r.items()}))
        res.append({k: v for k, v in r.items() if k != "skel"} | {"roles": r["skel"]["roles"]})
    summ = dict(objects=len(objs), kinds=dict(kinds), r_profiles={str(k): v for k, v in rcount.items()}, feature_counts=dict(feat), misses=len(miss), unguided=dict(ung),
                passed=(len(objs) >= 100 and not miss), seconds=round(time.time() - t0))
    json.dump(dict(summary=summ, results=res, misses=miss[:20]), open(HERE / "controls_p5b.json", "w"))
    print(json.dumps(summ, indent=1))
    for o, r in miss[:5]: print("MISS", r["skel"], r.get("statuses"), json.dumps(o))
