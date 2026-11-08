#!/usr/bin/env python3
"""qcert2: SYNTHETIC controls with A >= 1 for Lemma H1 / row HUB  (local helper configurations, NOT circuits).

No known circuit has a missing label meeting a full helper (A = 0 on all 1,264 phases), so the HUB row is never
exercised by real circuits.  This script builds LOCAL HELPER CONFIGURATIONS: a hub helper i (mask h, r_i = 0) with
m missing H-B edges i-b_n whose labels l_n = h + b_n are full-met: l_n = f_n + c_n for a full helper f_n with its three
represented triples (represented edges + B-B edges) and the missing H-B edge f_n-c_n; {b_n, c_n} = P_n is the boundary
pair with XOR h + f_n (F2).  It is NOT a full normalized circuit (no gate list, no (h, y, F, z), no normalization
check); only the local statements can be evaluated on it: the per-helper form m <= cap(h) of Lemma H1 and the local
form u_i <= 4 + (q - A) of row HUB with q = A = u_i = m counted inside the configuration (slack 4 - m).

Realizability of a configuration (necessary condition, from the proof of Lemma 4.4): its gate equations
   H_f + T (3 per full helper, references added), H_i + B_b + E_l, H_f + B_c + E_l (one pair per full-met label)
must be linearly independent (5m vectors); since each E_l is private to its pair this holds iff the 4m vectors
   H_f + T (3m)  and  H_i + H_f + B_b + B_c (m)
are independent.  Finite fact H1 bounds m by the independence of the 3m vectors H_f + T alone; the 4m-condition is
stronger (it is condition C1 of the qhub agent's refinement, which is NOT used in the certificates of this directory).

Computed here, both orientations:
  (1) cap(h) (the H1 notion) for every odd non-boundary h with |N(h)| >= 2, and the realizable capacity
      m*(h) = largest |S| with the 4|S| vectors independent (m*(h) <= cap(h)); histograms of both;
  (2) for every h with cap(h) = 4 and every 4-witness S: the 4m-family is dependent (rank 14 of 16), i.e. a hub
      with four full-met labels is not realizable, so u_i <= 4 + q - A is not tight on any realizable local
      configuration; the largest realizable m* per orientation is reported;
  (3) the synthetic configurations at m = m*_max (every (h, S) attaining it): labels distinct, pairs disjoint,
      witnesses pairwise non-adjacent (F4), the 5m gate-equation vectors independent, m <= cap(h) (Lemma H1 strong
      form, slack cap(h) - m), u_i = m <= 4 + (q - A) = 4 (row HUB, slack 4 - m), the mutated row u_i <= (m - 1) + (q - A)
      violated (the configuration exercises the row at level m), HUBlin's local form (u - 4)_+ + 4A <= 4q holds.
Writes synthetic_hub.json.   usage: python3 synthetic_hub.py
"""
import sys, json, itertools, time
from collections import defaultdict, Counter
from pathlib import Path
HERE = Path.home() / 'xs-campaigns/2026-11-07-sprint/qcert2'
sys.path.insert(0, str(HERE))
from stress_pkg import BOUNDARY, PAIRVALS   # noqa: E402  (package stress.py, copied unchanged)
KAPPA = 4


def rank2(vectors):
    piv = {}
    for v in vectors:
        while v:
            hb = v.bit_length() - 1
            if hb in piv: v ^= piv[hb]
            else: piv[hb] = v; break
    return len(piv)


def analyse(ori):
    t0 = time.time()
    B = BOUNDARY[ori]; Bset = set(B); PV = PAIRVALS[ori]
    trip = defaultdict(list)
    for i, j, k in itertools.combinations(range(64), 3):
        trip[B[i] ^ B[j] ^ B[k]].append((1 << i) | (1 << j) | (1 << k))
    full = {v: ts for v, ts in trip.items() if len(ts) == 3}
    pair_of = {}
    for i, j in itertools.combinations(range(64), 2): pair_of[B[i] ^ B[j]] = (i, j)
    assert len(pair_of) == 2016                                           # F2
    HUBBIT = 1 << 70
    def rel(S): return [t | (1 << (64 + n)) for n, f in enumerate(S) for t in full[f]]
    def indep3(S): return rank2(rel(S)) == 3 * len(S)
    def indep4(h, S):
        vs = rel(S)
        for n, f in enumerate(S):
            i, j = pair_of[h ^ f]; vs.append((1 << i) | (1 << j) | (1 << (64 + n)) | HUBBIT)
        return rank2(vs) == 4 * len(S)
    N = defaultdict(set)
    for f in full:
        for p in PV: N[f ^ p].add(f)
    N = {h: sorted(fs) for h, fs in N.items() if h not in Bset}
    cap = {}; mstar = {}; cap4_fail = 0; cap4_wit = 0
    for h, fs in N.items():
        if len(fs) == 1: cap[h] = 1; mstar[h] = 1; continue      # one full helper: both families trivially independent
        c = 0
        for size in range(min(len(fs), KAPPA + 1), 0, -1):
            if any(indep3(S) for S in itertools.combinations(fs, size)): c = size; break
        assert c <= KAPPA, ('finite fact H1 violated', hex(h))
        cap[h] = c
        m = 0
        for size in range(c, 0, -1):
            if any(indep4(h, S) for S in itertools.combinations(fs, size)): m = size; break
        mstar[h] = m
        if c == 4:
            for S in itertools.combinations(fs, 4):
                if indep3(S):
                    cap4_wit += 1
                    if not indep4(h, S): cap4_fail += 1
    hist_cap = Counter(cap.values()); hist_m = Counter(mstar.values()); mmax = max(mstar.values())
    print(f'{ori}: odd non-boundary h with N(h) nonempty: {len(N)}; cap histogram {dict(sorted(hist_cap.items()))} (finite fact H1); '
          f'realizable m* histogram {dict(sorted(hist_m.items()))}; m*_max = {mmax}; cap-4 witness sets {cap4_wit}, of which '
          f'{cap4_fail} fail the 4m independence (all: {cap4_fail == cap4_wit}); {time.time()-t0:.1f}s', flush=True)
    # (3) the synthetic configurations at m = mmax
    configs = 0; records = []; hubs_at_max = [h for h in N if mstar[h] == mmax]
    for h in hubs_at_max:
        fs = N[h]
        for S in itertools.combinations(fs, mmax):
            if not indep4(h, S): continue
            labels = []; pairs = []; vecs = rel(S)
            for n, f in enumerate(S):
                i, j = pair_of[h ^ f]; b, c = B[i], B[j]           # hub end b = B[i], full-helper end c = B[j]
                l = h ^ b; assert l == f ^ c, 'label of the hub edge is not the label of the full edge'
                assert bin(l).count('1') % 2 == 0, 'label must be even'
                labels.append(l); pairs.append((i, j))
                vecs.append((1 << i) | HUBBIT | (1 << (80 + n)))            # H_i + B_b + E_l
                vecs.append((1 << j) | (1 << (64 + n)) | (1 << (80 + n)))   # H_f + B_c + E_l
            assert len(set(labels)) == mmax, 'labels of the hub not distinct'
            assert all(not (set(p1) & set(p2)) for p1, p2 in itertools.combinations(pairs, 2)), 'pairs not disjoint'
            assert all((f1 ^ f2) not in PV for f1, f2 in itertools.combinations(S, 2)), 'two witnesses adjacent (F4)'
            assert rank2(vecs) == 5 * mmax, 'gate equations of the configuration dependent'
            q = A = u_i = m_i = mmax
            assert m_i <= cap[h] and u_i <= KAPPA + (q - A), 'Lemma H1 violated by the synthetic configuration'
            assert not (u_i <= (m_i - 1) + (q - A)), 'the mutated row (constant m - 1) must be violated'
            assert max(0, u_i - KAPPA) + 4 * A <= 4 * q, 'HUBlin local form violated'
            configs += 1
            if len(records) < 3:
                records.append(dict(ori=ori, hub=hex(h), triples_of_hub=len(trip.get(h, [])), cap_hub=cap[h], m=mmax,
                                    full_helpers=[hex(f) for f in S], pairs=[[hex(B[i]), hex(B[j])] for i, j in pairs],
                                    labels=[hex(l) for l in labels], hub_edges=[hex(B[i]) for i, j in pairs], full_edges=[hex(B[j]) for i, j in pairs],
                                    q=q, A=A, u_hub=u_i, HUB_slack=KAPPA + q - A - u_i, H1_strong_slack=cap[h] - m_i, N_h=[hex(f) for f in fs]))
    print(f'{ori}: {configs} synthetic configurations with m = {mmax} full-met labels at the hub ({len(hubs_at_max)} hub values): '
          f'gate equations independent (rank {5*mmax}), labels distinct, pairs disjoint, witnesses non-adjacent; Lemma H1 strong form slack '
          f'cap(h) - m in {sorted({cap[h] - mmax for h in hubs_at_max})}; row HUB local form u_i <= 4 + q - A with slack {KAPPA - mmax}; '
          f'the constant-(m-1) mutation violated; {time.time()-t0:.1f}s', flush=True)
    return dict(values=len(N), cap_hist=dict(sorted(hist_cap.items())), mstar_hist=dict(sorted(hist_m.items())), mstar_max=mmax,
                cap4_witness_sets=cap4_wit, cap4_witness_sets_failing_4m=cap4_fail, configurations_at_max=configs,
                hub_values_at_max=len(hubs_at_max), examples=records)


if __name__ == '__main__':
    out = {ori: analyse(ori) for ori in ('M', 'Mt')}
    json.dump(out, open(HERE / 'synthetic_hub.json', 'w'), indent=1)
    print('example (M):', json.dumps(out['M']['examples'][0]))
    print('SYNTHETIC HUB CONTROL PASSED (local helper configurations with A = m >= 1, not full circuits)')
