#!/usr/bin/env python3
"""static dep/merge candidates over an archive: python3 t_patch.py CAMPAIGN [front|cells|all]"""
import sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import x1lib as X, x1patch as XP
from boolflux.hub.common import metrics, sbox, leq
from boolflux.hub.archive import Archive
ar = Archive(sys.argv[1]); which = sys.argv[2] if len(sys.argv) > 2 else "front"
if which == "front": ids = ar.front_ids()
elif which == "cells": ids = [i for v in ar.cells.values() for i in v[:1]]
else: ids = list(ar.rec)
t0 = time.time(); nh = 0; place = 0
for i in ids:
    c = ar.circuit(i); m = metrics(c)
    try:
        cs = XP.static_candidates(c)
    except Exception as e:
        print(i, m, "ERROR", repr(e)); continue
    if not cs: continue
    nh += 1
    res = []
    for nc, d in cs:
        ok = tuple(nc.value_table()) == sbox()
        mm = metrics(nc)
        res.append((mm, d["kind"], ok, ar.would_place(mm), round(ar.gain(mm), 2)))
    res.sort()
    place += any(r[3] for r in res)
    print(i, m, "->", len(res), "cands; best", res[:3], "placeable", sum(r[3] for r in res), "allok", all(r[2] for r in res), flush=True)
print("circuits", len(ids), "with candidates", nh, "with placeable", place, "time %.1f" % (time.time() - t0))
