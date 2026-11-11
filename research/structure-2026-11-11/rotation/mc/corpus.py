"""Corpus check: block-monotonicity and charges of known 88-gate MixColumns circuits (read-only on ~/xs-campaigns).

usage: python3 corpus.py [--limit N]        writes corpus_out.txt-style summary to stdout

Sources:
  kste      ~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor/circuits_{1,2,3,depth5}.txt
            (one circuit per line as operand pairs; wiring as given; only lines computing MixColumns with 88 gates)
  hunt_r    ~/xs-campaigns/2026-11-07-sprint/hunt/runs/*/workers/*/records/g88-*.json   (wiring as given)
  repo      circuits/aes-mixcolumns/*.circ.txt                                           (wiring as given)
  hunt_s    ~/xs-campaigns/2026-11-07-sprint/hunt/samples.jsonl, states with 88 gates (value sets only)
For circuits with wiring: mc.analyse.  For every value set (all sources): the block-support patterns and
whether a support-closed wiring exists (mc.support_closed_wiring), which implies a block-monotone wiring.
Nothing from the external repository is executed; lines are parsed with a regular expression.
"""
import glob
import json
import os
import sys
from collections import Counter

import mc

HOME = os.path.expanduser("~")
KSTE = os.path.join(HOME, "xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor")
HUNT = os.path.join(HOME, "xs-campaigns/2026-11-07-sprint/hunt")
REPO = os.path.join(mc.HERE, "..", "..", "..", "..", "circuits", "aes-mixcolumns")
SHEET_PATTERNS = {"".join(map(str, sorted(s2))) for s in mc.SHEET_SUPPORT
                  for s2 in [frozenset(x) for x in __import__("itertools").chain.from_iterable(
                      __import__("itertools").combinations(sorted(s), r) for r in range(1, len(s) + 1))]}


def summarise(name, rows):
    print(f"== {name}: {len(rows)} circuits with wiring")
    if not rows:
        return
    mono = [r for r in rows if r["monotone"]]
    non = [r for r in rows if not r["monotone"]]
    print(f"   block-monotone: {len(mono)}   not block-monotone: {len(non)}")
    print("   gate counts:", dict(Counter(r["G"] for r in rows)))
    for label, sub in (("monotone", mono), ("non-monotone", non)):
        if not sub:
            continue
        print(f"   [{label}] sum mu:", dict(sorted(Counter(r["sum_mu"] for r in sub).items())),
              " uncharged:", dict(sorted(Counter(r["uncharged"] for r in sub).items())),
              " excess:", dict(sorted(Counter(r["excess"] for r in sub).items())))
        print(f"   [{label}] violating gates:", dict(sorted(Counter(r["violating"] for r in sub).items())))
        print(f"   [{label}] charges per sheet, most common:", Counter(tuple(r["charges"]) for r in sub).most_common(8))
        print(f"   [{label}] min charge per sheet:", [min(r["charges"][j] for r in sub) for j in range(8)],
              " max:", [max(r["charges"][j] for r in sub) for j in range(8)])
        print(f"   [{label}] G01:", dict(sorted(Counter(r["G01"] for r in sub).items())),
              " G34:", dict(sorted(Counter(r["G34"] for r in sub).items())),
              " G01+G34:", dict(sorted(Counter(r["G01"] + r["G34"] for r in sub).items())))
        print(f"   [{label}] G347:", dict(sorted(Counter(r["G347"] for r in sub).items())),
              " G34 + pure-7 gates not serving sheet 7:", dict(sorted(Counter(r["G34"] + r["pure7_not_sheet7"] for r in sub).items())),
              " charge2+charge5+charge6+G01+G347:",
              dict(sorted(Counter(r["charges"][2] + r["charges"][5] + r["charges"][6] + r["G01"] + r["G347"] for r in sub).items())))
        print(f"   [{label}] pure block-7 gates:", dict(sorted(Counter(r["pure7"] for r in sub).items())),
              " of which not serving sheet 7:", dict(sorted(Counter(r["pure7_not_sheet7"] for r in sub).items())),
              " gates on {2,7}:", dict(sorted(Counter(r["M27"] for r in sub).items())))
        print(f"   [{label}] (G01, G34, charge2, charge5, charge6, charge7, other uncharged) most common:",
              Counter((r["G01"], r["G34"], r["charges"][2], r["charges"][5], r["charges"][6], r["charges"][7],
                       r["G"] - r["G01"] - r["G34"] - r["charges"][2] - r["charges"][5] - r["charges"][6] - r["charges"][7])
                      for r in sub).most_common(8))
        up = Counter()
        for r in sub:
            up.update(r["uncharged_patterns"])
        print(f"   [{label}] support patterns of uncharged gates (total over circuits):", dict(sorted(up.items())))
    bad = Counter()
    for r in rows:
        for p, k in r["patterns"].items():
            if p not in SHEET_PATTERNS:
                bad[p] += 1
    print("   circuits containing a gate whose support lies in no sheet support, by pattern:", dict(sorted(bad.items())))


def main():
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    # repo
    rows = []
    for f in sorted(glob.glob(os.path.join(REPO, "*.circ.txt"))):
        r = mc.analyse(mc.parse_ncff(f))
        r["src"] = os.path.basename(f)
        rows.append(r)
        print(os.path.basename(f), {k: v for k, v in r.items() if k not in ("patterns", "src")})
    # kste
    krows, valuesets = [], {}
    nlines = nbad = 0
    for fn in ("circuits_1.txt", "circuits_2.txt", "circuits_3.txt", "circuits_depth5.txt"):
        p = os.path.join(KSTE, fn)
        if not os.path.exists(p):
            print("missing", p)
            continue
        for line in open(p):
            if not line.strip():
                continue
            nlines += 1
            if limit and nlines > limit:
                break
            gates = mc.parse_pairs(line)
            r = mc.analyse(gates) if len(gates) == 88 else None
            if r is None or r["distinct"] != 88 or r["dead"]:
                nbad += 1
                continue
            krows.append(r)
            vals = [1 << i for i in range(32)]
            for a, b in gates:
                vals.append(vals[a] ^ vals[b])
            valuesets.setdefault(tuple(sorted(vals[32:])), "kste")
    print(f"kste: {nlines} lines read, {nbad} not valid trimmed 88-gate MixColumns circuits")
    summarise("kste (wiring as published)", krows)
    # hunt records
    hrows = []
    for f in sorted(glob.glob(os.path.join(HUNT, "runs/*/workers/*/records/g88-*.json"))):
        if f.endswith(".verification.json"):
            continue
        c = json.load(open(f))
        gates = [tuple(g) for g in c["gates"]]
        r = mc.analyse(gates)
        if r is None:
            continue
        hrows.append(r)
        vals = [1 << i for i in range(32)]
        for a, b in gates:
            vals.append(vals[a] ^ vals[b])
        valuesets.setdefault(tuple(sorted(set(vals[32:]))), "hunt_r")
    summarise("hunt records (wiring as recorded)", hrows)
    # hunt samples (value sets)
    ns = 0
    sp = os.path.join(HUNT, "samples.jsonl")
    if os.path.exists(sp):
        for line in open(sp):
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("gates") == 88:
                vs = tuple(sorted(set(rec["values"])))
                if len(vs) == 88 and all(t in vs for t in mc.TARGETS):
                    ns += 1
                    valuesets.setdefault(vs, "hunt_s")
    print(f"hunt samples with 88 gates: {ns}")
    # value-set level
    print(f"== distinct value sets over all sources: {len(valuesets)}  (by first source: {dict(Counter(valuesets.values()))})")
    closed = Counter()
    nonsheet = Counter()
    klass = Counter()
    for vs, src in valuesets.items():
        pats = {"".join(map(str, sorted(mc.blocks(v)))) for v in vs}
        ns_p = sorted(p for p in pats if p not in SHEET_PATTERNS)
        ok = (not ns_p) and mc.support_closed_wiring(vs)
        closed[(src, ok)] += 1
        if ns_p:
            nonsheet[(src, ",".join(ns_p))] += 1
            klass[(src, "no monotone wiring: a value lies in no sheet support")] += 1
        elif ok:
            klass[(src, "monotone wiring exists (support-closed)")] += 1
        elif not mc.sheets_derivable(vs):
            klass[(src, "no monotone wiring: some sheet not derivable inside its support")] += 1
        else:
            klass[(src, "undecided by these tests")] += 1
    print("   classification of value sets:")
    for k, v in sorted(klass.items()):
        print("      ", k, v)
    print("   value sets admitting a support-closed (hence block-monotone) wiring, by source:", dict(sorted(closed.items())))
    print("   value sets containing a value whose support lies in no sheet support, by source and patterns:")
    for k, v in sorted(nonsheet.items(), key=lambda kv: -kv[1])[:20]:
        print("      ", k, v)


if __name__ == "__main__":
    main()
