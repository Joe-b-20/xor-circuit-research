#!/usr/bin/env python3
"""Hub operator and_merge: algebraic AND removal (library: hub/ops/and_merge_lib/).

    python3 hub/ops/and_merge.py --archive DIR --in ID --seed S --seconds T --out JOBDIR [--caps A,AD,GD]

Works on the product program of a circuit (atoms = 1, inputs, AND outputs; every linear signal is an
affine form over the atoms):
  dep    a product whose truth table is an XOR of other atoms is replaced by an XOR tree (-1 AND);
  merge  two ANDs read by exactly the same forms and sharing an operand direction become one AND.
Both are exact identities, found by linear algebra on the 256-row tables / the forms; the rest of the
circuit is kept (local patch), chains of reductions are followed, and the reduced circuits are polished
by the gate kernel under (A', AD and GD of the source) - the kernel repairs the gate depth if the patch
raised it.

Target choice: the scheduler only offers Pareto-front circuits, but the reductions mostly sit in new,
not yet polished members (joins, generators).  So besides --in the job scans archive members it has not
seen (scan record ARCHIVE/and_merge_scanned.json: id -> its static reductions, if any), newest first, and works on the
hits.  The true source of every candidate is in record.json (info.sources); the scheduler records the
--in circuit as the parent.
Every candidate is checked on all 256 inputs here; the hub verifies and admits.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

OPS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(OPS_DIR.parents[1].parent))
sys.path.insert(0, str(OPS_DIR / 'and_merge_lib'))
from boolflux.hub import ops as HO                          # noqa: E402
from boolflux.hub.common import core, metrics, sbox          # noqa: E402
import patches as XP                                         # noqa: E402

SCAN_SHARE = 0.35         # of the job's seconds spent scanning unseen archive members
MAX_POLISH = 2            # reduced circuits polished per job
MIN_POLISH_S = 12.0
OPTIMISM = 4              # a hit is worked on if it would place after the polish removed this many gates
MAX_ATT = 6               # polish attempts per hit
BEAM = 6
MAX_A = 80                # larger circuits are not scanned (one 264-AND archive member cost minutes)
CHAIN_S = 8.0             # time limit of one reduction chain


def reduce_chain(c, rounds=6):
    """follow static reductions to a fixpoint (beam); returns [(circuit, [kinds])] with fewer ANDs than c"""
    out = {}; level = [(c, [])]; t0 = time.time()
    if sum(1 for g in c.gates if g[0] == 8) > MAX_A: return []
    for _ in range(rounds):
        nxt = {}
        for cc, hist in level:
            if time.time() - t0 > CHAIN_S: break
            try:
                cs = XP.static_candidates(cc)
            except Exception:
                continue
            for nc, d in cs:
                if tuple(nc.value_table()) != sbox(): continue
                k = core.to_kernel(nc)
                if k not in out and k not in nxt: nxt[k] = (nc, hist + [d['kind']])
        if not nxt: break
        out.update(nxt)
        level = sorted(nxt.values(), key=lambda x: (metrics(x[0])[0], metrics(x[0])[1], metrics(x[0])[3], metrics(x[0])[2]))[:BEAM]
    return list(out.values())


def _scan_record(path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _save(path, d):
    tmp = path.with_suffix('.tmp%d' % os.getpid())
    tmp.write_text(json.dumps(d)); os.replace(tmp, path)


def _hyp(ar, e, opt=0):
    # gain if the best reduction were repaired to the source depths at its current G (minus opt gates)
    m0 = e["m0"]
    return max(ar.gain((m[0], m0[1], m[2] - opt, m0[3])) for m in e["best"])


def op_and_merge(ar, args, rng, out):
    t0 = time.time(); T = args.seconds
    lp = Path(args.archive) / "and_merge_scanned.json"
    led = _scan_record(lp)                      # id -> 0 (no reduction) | {m0, best: [metrics], kinds, att}
    unseen = [i for i in ar.rec if i not in led and i != args.inp]
    unseen.sort(key=lambda i: -ar.rec[i]["t_admit"])
    cands = {}; scanned = 0; new_hits = []; fresh = {}
    for i in ([args.inp] if args.inp not in led else []) + unseen:
        if scanned and time.time() - t0 > SCAN_SHARE * T: break
        c = ar.circuit(i); scanned += 1
        try:
            red = reduce_chain(c)
        except Exception:
            red = []
        if not red: led[i] = 0; continue
        ms = sorted((metrics(nc), core.to_kernel(nc)) for nc, hist in red)
        amin = ms[0][0][0]
        led[i] = {"m0": list(metrics(c)), "best": [list(m) for m, k in ms if m[0] == amin][:6], "kinds": red[0][1], "att": 0}
        new_hits.append(i); fresh[i] = red
        for nc, hist in red:
            if ar.would_place(metrics(nc)): cands[core.to_kernel(nc)] = nc
    # work list: hits with the largest hypothetical gain, fewest polish attempts first
    hits = [(i, e) for i, e in led.items() if e and i in ar.rec]
    rng.shuffle(hits)
    scored = [(_hyp(ar, e), _hyp(ar, e, OPTIMISM), i, e) for i, e in hits]
    scored = [x for x in scored if x[1] > 0 and x[3]["att"] < MAX_ATT]
    scored.sort(key=lambda x: (-x[0], x[3]["att"], -x[1]))
    work = []; seen_m = set()
    for g0, g1, i, e in scored:          # one circuit per source cell and job
        if tuple(e["m0"]) in seen_m: continue
        seen_m.add(tuple(e["m0"])); work.append((i, e))
        if len(work) >= MAX_POLISH: break
    polished = []
    for n, (i, e) in enumerate(work):
        left = T - (time.time() - t0); per = left / (len(work) - n)
        if per < MIN_POLISH_S: break
        c = ar.circuit(i); m0 = metrics(c)
        red = fresh.get(i) or reduce_chain(c)
        if not red: continue
        ms = sorted(((metrics(nc), core.to_kernel(nc), nc) for nc, hist in red), key=lambda x: x[0][:1] + (max(0, x[0][1] - m0[1]), max(0, x[0][3] - m0[3]), x[0][2]))
        pick = ms[:3]
        m, k, nc = pick[rng.randrange(len(pick))] if e["att"] else pick[0]
        caps = {"A": m[0], "AD": m0[1], "GD": m0[3]}
        e["att"] += 1
        sd = out / ("polish%d" % n); sd.mkdir(exist_ok=True)
        cs, info = HO._kernel(nc, caps, args.objective, args.seed + n, max(1.0, per - 1.0), sd, args.archive)
        for pc in cs:
            if tuple(pc.value_table()) != sbox(): continue
            pm = metrics(pc)
            polished.append({"source": i, "source_metrics": list(m0), "start": list(m), "caps": caps, "result": list(pm),
                             "kinds": e["kinds"]})
            if ar.would_place(pm): cands[core.to_kernel(pc)] = pc
    led2 = _scan_record(lp); led2.update(led); _save(lp, led2)
    cl = sorted(cands.values(), key=lambda x: (-ar.gain(metrics(x)), metrics(x)))
    return cl[:args.max_cands], {"scanned": scanned, "scan_record": len(led), "new_hits": new_hits[:50],
                                 "hits_total": len(hits), "polished": polished}


HO.OPS['and_merge'] = op_and_merge

if __name__ == '__main__':
    sys.exit(HO.main('and_merge'))
