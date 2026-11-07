#!/usr/bin/env python3
"""Check every qreal fact and row on the 13 package controls and the 303 real circuits (4 orbit steps each,
1,264 phases), with the package's own Circuit / analyse / canonical_transpose.

Per phase:
  H1 (hub.py): for every helper i with r_i < 3, the number of its missing labels that meet a full helper is
      <= cap(h_i) (actual mask, hub_cap_{ori}.json) <= 4, and u_i <= 4 + q - A, A = sum_{r=3} u = #labels meeting
      a full helper (also checked: each missing label meets <= 1 full helper).
  O1 (chronology): every full helper has exactly one defining gate; each of its represented edges that is not the
      defining gate defines an output lying in that edge's triple (U1: the label is the gate's result and the
      label's B-B gate defines an output of the pair; U2: the apex is the result and is an output); the outputs
      so defined are distinct across full helpers; count >= 2 per full helper.
  BD/BX (fullsets.py): d_v >= mult_S(v) for all boundary v (S = full helpers), sum_B d_v = 2 #BB + #HB,
      E_B >= X(S), cover(S) >= 9 n3 + 64 - sum_B d_v.
  DARK rows: with the phase's actual q_D, y2d, y2m, Fb, Fd: every row of qr_lp.dark_rows() holds (min slack).
  HUBlin row.
usage: python3 qr_circ.py [N_REAL]
"""
import sys, json, glob, itertools, time
from collections import Counter, defaultdict
from math import comb
from pathlib import Path
SPRINT = Path.home()/'xs-campaigns/2026-11-07-sprint'
sys.path.insert(0, str(SPRINT/'lb76/pkg_copy/source/lower_bounds/checks'))
sys.path.insert(0, str(SPRINT/'bridge'))
from stress import Circuit, BOUNDARY, parity  # noqa: E402
from profile_real import reconstruct  # noqa: E402
OUT = SPRINT/'qreal'
RHO6 = {'M': 20, 'Mt': 28}; RESERVE = {'M': 8, 'Mt': 4}; KAPPA = 4
CAP = {o: {int(k): v for k, v in json.load(open(OUT/f'hub_cap_{o}.json'))['cap'].items()} for o in ('M', 'Mt')}

TAB = {}
def tables(ori):
    if ori in TAB: return TAB[ori]
    B = BOUNDARY[ori]; idx = {b: i for i, b in enumerate(B)}
    TAB[ori] = dict(B=B, idx=idx)
    return TAB[ori]

def phase_facts(C, I):
    ori = C.ori; T = tables(ori); B = I['B']; H = set(I['H']); Hs = I['H']
    edges = []                                    # (p, q, label, result)
    for k, (a, b) in enumerate(C.gates):
        s = 32 + k
        if C.odd[a] and C.odd[b]: edges.append((a, b, s, s))
        elif C.odd[a] != C.odd[b]:
            o, e = (a, b) if C.odd[a] else (b, a); edges.append((o, s, e, s))
    evens = [v for v in range(32, C.n) if not C.odd[v]]
    bb = {}
    for p, q_, e, res in edges:
        if p in B and q_ in B: bb[e] = (p, q_, res)
    missing = {e for e in evens if e not in bb}
    hedges = {v: [] for v in H}
    for p, q_, e, res in edges:
        for v in (p, q_):
            if v in H: hedges[v].append((q_ if v == p else p, e, res))
    typ = {}
    for v in H:
        r = sum(1 for o, e, _ in hedges[v] if o in B and e in bb)
        u = sum(1 for o, e, _ in hedges[v] if o in B and e in missing)
        vv = sum(1 for o, e, _ in hedges[v] if o in H)
        typ[v] = (r, u, vv)
    full = [v for v in H if typ[v][0] == 3]
    q = I['q']; z = I['z']; y = I['y']; F = I['F']
    # ---- H1 hub fact
    fullmet = Counter()
    for v in full:
        for o, e, _ in hedges[v]:
            if o in B and e in missing: fullmet[e] += 1
    assert all(c == 1 for c in fullmet.values()), 'a missing label meets two full helpers'
    A = sum(typ[v][1] for v in full); assert A == len(fullmet)
    hub_viol = 0; hub_max = 0; hub_cap_slack = 10 ** 9
    for v in H:
        if typ[v][0] == 3: continue
        fm = sum(1 for o, e, _ in hedges[v] if o in B and e in missing and e in fullmet)
        cap = CAP[ori].get(C.mask[v], 0)
        hub_max = max(hub_max, fm)
        if fm > cap or fm > KAPPA or typ[v][1] > KAPPA + q - A: hub_viol += 1
        hub_cap_slack = min(hub_cap_slack, cap - fm)
    # ---- O1 chronology of full helpers
    owned = []; o1_viol = 0; per_full_outputs = []
    for v in full:
        defining = [(o, e, res) for o, e, res in hedges[v] if res == v]
        if len(defining) != 1: o1_viol += 1
        outs = []
        for o, e, res in hedges[v]:
            if not (o in B and e in bb): continue
            if res == v: continue                         # the defining gate of v
            b1, b2, res2 = bb[e]
            tri = {o, b1, b2}
            if res == e:                                  # U1: label defined here; its B-B gate must define an output of the pair
                if res2 not in (b1, b2) or res2 not in C.out_index: o1_viol += 1; continue
                outs.append(res2)
            elif res == o:                                # U2: the apex is defined here and is an output
                if o not in C.out_index: o1_viol += 1; continue
                outs.append(o)
            else: o1_viol += 1
            if outs and outs[-1] not in tri: o1_viol += 1
        per_full_outputs.append(len(outs)); owned += outs
        if len(outs) < 2: o1_viol += 1
    if len(owned) != len(set(owned)): o1_viol += 1
    # ---- BD / BX boundary degrees
    mult = Counter()
    for v in full:
        for o, e, _ in hedges[v]:
            if o in B and e in bb:
                b1, b2, _ = bb[e]
                for w in (o, b1, b2): mult[w] += 1
    dB = sum(C.d[v] for v in B)
    assert dB == 2 * len(bb) + (32 + len(H) - y + q - z)
    bd_viol = sum(1 for w in B if C.d[w] < mult[w])
    X = sum(max(0, m - 2) for m in mult.values()); cover = len(mult)
    bx_slack = I['E_B'] - X
    cover_slack = cover - (9 * len(full) + 64 - dB)
    # ---- DARK rows with the actual q_D
    anchored = {v for v in H if typ[v][0] >= 1}
    bright = {e for v in anchored for o, e, _ in hedges[v] if o in B and e in missing}
    dark = missing - bright; qD = len(dark)
    y0 = y1 = y2 = y2d = y2m = 0
    for k, (a, b) in enumerate(C.gates):
        s = 32 + k
        if not C.odd[a] and not C.odd[b]:
            miss = [e for e in (a, b, s) if e in missing]
            if not miss: y0 += 1
            elif len(miss) == 1 and miss[0] in bright: y1 += 1
            else:
                y2 += 1
                if len(miss) == 1: y2d += 1
                else: y2m += 1
    f = I['f']
    Fb = sum(f[e] for e in bright); Fd = sum(f[e] for e in dark); F_H = I['F_H']
    W = sum(typ[v][0] * typ[v][1] for v in H); Aful = A
    Z = sum(max(0, typ[v][0] - 1) * typ[v][1] for v in H)
    E = sum(max(0, typ[v][1] - 2) for v in full)
    D0 = sum(typ[v][1] - 1 for v in H if typ[v][0] == 0)
    U = sum(typ[v][1] for v in H); U1 = sum(typ[v][1] for v in anchored)
    rho = RESERVE[ori]; eps = 2 if ori == 'M' else 0; d = qD
    rows = {
        'L13d': 2 * y2 + 2 * z + 7 * q - 2 * rho - 9 * d - (W + y1 - 2 * D0),
        'L14d': 2 * y2 + 2 * z + 7 * q - 2 * rho + eps - 9 * d - (W + Aful + y1 - 2 * D0),
        'L15d': y2 + z + 3 * q - rho - 4 * d - (Z - D0),
        'bright_lower': U1 - (q - d),
        'bright_cap': 4 * (q - d) + 2 * Fb - (U1 + y1),
        'dark_cap': 4 * d + 2 * Fd - y2d,
        'FbFd': F - Fb - Fd - F_H,
        'y2m_pairs': comb(q, 2) - y2m,
        "I'": 4 * q + 2 * F - (y1 + 2 * y2 - y2d + U + 2 * F_H),
        'HUBlin': 4 * q + 2 * F - (sum(max(0, typ[v][1] - KAPPA) for v in H if typ[v][0] < 3) + 4 * Aful + 2 * F_H),
    }
    if ori == 'M': rows['L17Md'] = 3 * y2 + 3 * z + 6 * q - 24 - 9 * d - (2 * Z + 2 * E - 3 * D0)
    else:
        rows['L17Td'] = 3 * y2 + 3 * z + 3 * q - 12 - 6 * d - (Z + E - 3 * D0)
        rows['L18d'] = 3 * y2 + 3 * z + 7 * q - 12 - 10 * d - (W + Aful - 3 * D0)
    if d == q: rows['Fb0'] = -Fb
    if d == 0: rows['Fd0'] = -Fd - y2d
    return dict(ori=ori, q=q, z=z, y=y, F=F, n3=len(full), A=A, qD=qD, hub_viol=hub_viol, hub_max=hub_max, hub_cap_slack=hub_cap_slack,
                o1_viol=o1_viol, per_full_outputs=per_full_outputs, bd_viol=bd_viol, X=X, E_B=I['E_B'], bx_slack=bx_slack,
                cover=cover, cover_slack=cover_slack, y0=y0, y1=y1, y2=y2, y2d=y2d, y2m=y2m, Fb=Fb, Fd=Fd, rows=rows)

def orbit(gates, steps=4):
    C = Circuit(gates, 'M'); recs = []
    for step in range(steps):
        I = C.analyse()
        rec = dict(step=step); rec.update(phase_facts(C, I)); recs.append(rec)
        if step + 1 < steps: C, _ = C.canonical_transpose(I)
    return recs

def main():
    nreal = int(sys.argv[1]) if len(sys.argv) > 1 else 10 ** 9
    t0 = time.time(); out = []
    for fn in sorted(glob.glob(str(SPRINT/'lb76/pkg_copy/source/circuits/*.json'))):
        dd = json.load(open(fn)); g = dd['gates'] if isinstance(dd, dict) else dd
        out.append(dict(tag='ctrl:' + Path(fn).name, phases=orbit(g)))
    print('controls done', f'{time.time()-t0:.0f}s', flush=True)
    d = json.load(open(SPRINT/'bridge/profiles.json'))
    for i, r in enumerate([r for r in d['results'] if 'error' not in r][:nreal]):
        gates, order, info = reconstruct(r['values'], 'ymax', 0, True)
        out.append(dict(tag=r['tag'], phases=orbit(gates)))
        if (i + 1) % 100 == 0: print(i + 1, 'real done', f'{time.time()-t0:.0f}s', flush=True)
    json.dump(out, open(OUT/'qr_circ.json', 'w'), indent=0)
    ph = [p for r in out for p in r['phases']]
    print(f'\n{len(out)} circuits, {len(ph)} phases ({sum(1 for p in ph if p["step"] >= 1)} canonical)')
    for key in ('hub_viol', 'o1_viol', 'bd_viol'):
        print(f'  {key}: total {sum(p[key] for p in ph)} (must be 0)')
    for key in ('hub_max', 'hub_cap_slack', 'bx_slack', 'cover_slack', 'n3', 'A', 'qD', 'y2d', 'y2m', 'Fb', 'Fd', 'X', 'E_B'):
        for ori in ('M', 'Mt'):
            v = [p[key] for p in ph if p['ori'] == ori]
            print(f'  {key:14s} {ori:2s}: min {min(v):3d} median {sorted(v)[len(v)//2]:3d} max {max(v):3d}')
    pf = [n for p in ph for n in p['per_full_outputs']]
    print(f'  outputs defined per full helper (must be >= 2): histogram {dict(sorted(Counter(pf).items()))}')
    names = sorted({k for p in ph for k in p['rows']})
    for nm in names:
        for ori in ('M', 'Mt'):
            v = [p['rows'][nm] for p in ph if p['ori'] == ori and nm in p['rows']]
            if v: print(f'  row {nm:13s} {ori:2s}: min slack {min(v):3d} (n={len(v)}) {"VIOLATION" if min(v) < 0 else "ok"}')
    print(f'total {time.time()-t0:.0f}s')

if __name__ == '__main__':
    main()
