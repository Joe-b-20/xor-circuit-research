# Realizability of the G = 75 hub family: finite fact H2 (r + m <= 3), row HUB2, packing rows, survivor recount

qhub agent report, 2026-11-07 (about 2 hours). Working directory `~/xs-campaigns/2026-11-07-sprint/qhub/`. Read only:
the git repository, `lb76/pkg_copy/`, `qbound/`, `qreal/`, `qcert/`, `qrealcheck/`, `bridge/`. `qreal/qr_lp.py` was
copied to `qh_lp.py` and extended (`make_qh_lp.py`, `patch2_qh_lp.py` are the exact patches); the package's
`lp_regen.py` and `stress.py` are imported unchanged. One python process at a time under `nice -n 8`, every
enumeration under `timeout`; the longest run was a G = 75 scan with case splits (325 s); total compute about
30 minutes.

Labels: **[proved]** (proof written here; package lemmas and finite facts used as black boxes), **[finite-checked]**
(computed exactly by a script in this directory, with a second independent implementation), **[measured]** (script
output on the LP model or on known circuits), **[derived]** (arithmetic from proved statements, not re-verified
independently), **[conjecture]**.

**The lower bound remains L(M) >= 75.** Nothing below is a bound of 76: every scan leaves survivors (789 oriented
claims after all rows accepted here), and no certificate-style coverage of G = 75 was produced. The bound would move
only if the survivors reached 0 with complete, independently checked certificate coverage (two checkers, package
format), which is not the case.

## 0. Results in ten lines

1. **Finite fact H2 [finite-checked]:** for every odd non-boundary value h of either orientation and every r in
   {0, 1, 2}, at most **3 - r** full values f in N(h) = {f full : h + f is a boundary-pair value} can be met at
   missing labels by a helper of value h carrying r represented relations, once the hub's own relations and the
   mixed relations h + f = b + c are added to the independence test (qreal's H1 tested the full helpers' relations
   alone and found 4). Exhaustive over all 128,068 (M) / 177,412 (M^T) hub values x every choice of the r
   triples x every subset of N(h); a second implementation (`hub2_check.py`: separate elimination code, no DFS
   pruning) gives identical histograms and 0 violations.
2. **Lemma H2 [proved]:** in every normalized circuit every helper i satisfies `r_i + m_i <= 3`, m_i = the number
   of its missing labels that have an H-B edge at a full helper (r_i = 3: Lemma 4.5; r_i <= 2: the family of
   section 2 is independent by the gate-equation argument of Lemma 4.4, and H2 bounds its size).
3. **Row HUB2 [proved]:** `u_i <= (3 - r_i) + (q - A)` for every helper with r_i <= 2, A = sum_{r=3} u; exact case
   split on A = q - d (d = 0..q-2) plus A <= 1, each case an ordinary Farkas-certifiable LP. It replaces qreal's
   HUB (`u_i <= 4 + q - A`).
4. **Effect [measured]:** on the qreal system (G\* + N1 + HUB + DARK + FM: 996 claims / 381 keys, reproduced exactly
   first): claims **996 -> 863** (454 M-even, 409 M^T-even), LP-feasible keys **381 -> 166** (129 M, 37 M^T). The
   M^T q = 5 cluster (101 keys) is reduced to 4, M q = 5 from 62 to 36, q = 2 and 13 of the 14 q = 3 keys die.
5. **Packing rows PK4, PK5 [proved]** (Lemma 10.4's argument at q = 4, 5: `N_3 <= 1` at q = 4, `N_3 + 2 N_4 <= 2`
   at q = 5, N_j = #{u >= j}): claims **863 -> 789** (416 M, 373 M^T), keys **166 -> 116** (81 M, 35 M^T; by q:
   1:2 3:1 4:33 5:11 6:31 7:7 8:30 10:1). The linear aggregate HUB2L adds nothing (789 / 116).
6. **Degree budget and Lemma O1 do not sharpen H2 [finite-checked]:** the maxima 3 - r are attained by hub
   configurations of boundary excess X = 0 (8 hub values of M and 20 of M^T for r = 0; 16 / 24 for r = 1;
   12 / 24 for r = 2) that admit the O1 output assignment. So the per-hub conditions listed in qreal section 6
   cannot push the hub capacity below 3 - r; explicit realizable local configurations are listed in section 3.3.
7. **Circuit check [measured]:** on the 13 controls and 303 real circuits (1,264 phases) every helper has m_i = 0
   (A = 0 on every phase), so H2 and HUB2 hold (row slack >= 7); the independence behind them (all represented
   relations plus t_l - 1 mixed vectors per missing label met by t_l helpers) holds on all 1,264 phases.
8. What survives (section 6): a block of 81 M keys with h = 14..19, y <= 4, q = 4..6, z <= 2 (full helpers of
   type (3, 0, 0) with (2, 1, 0)/(1, 1, 1)/(0, 2, 1) helpers and A < q), the M^T q = 7..8 small-h keys with
   hubs (0, 5, 0)/(1, 4, 0)/(2, 3, 0) at A = q - 2 (exactly H2's limit), and the q <= 3 keys (18,1,1,1,4,Mt),
   (19,0,0,1,5,Mt), (19,0,4,3,3,M). Only 53 of the 116 keys are load-bearing (feasible at a claim's k or ell).
9. The finite searches that would decide them are specified in section 7 (joint hub systems over a fixed set of
   full helpers at A >= q - 2; the M^T q = 1, z = 4-5 family of 7-8 full helpers); neither was run here.
10. **Cumulative: 1,508 (package) -> 1,313 (qbound) -> 996 (qreal) -> 863 (HUB2) -> 789 (PK) oriented claims;
    keys 1,134 -> 681 -> 381 -> 166 -> 116.** Shortfall histogram of the 789: 0: 426, 1: 270, 2: 69, 3: 24.
    The bound stays 75.

## 1. The configurations the surviving LP vertices required

`qreal/vertices_final.log` (reproducible with `qh_lp.py vertex ... GstarN1HUBDARKMFM`) shows the pattern behind 362
of qreal's 381 keys: five or six full helpers of type (3, 1, 0) with `A = sum_{r=3} u = q` (L6 tight: every missing
label is met by exactly one full helper), plus non-full "hub" helpers whose u missing labels are therefore all
full-met: types (1, 3, 0), (1, 4, 0), (2, 3, 0), (2, 2, 0) at M^T q = 5, (0, 3, 0), (2, 2, 0) at M q = 4-5,
(0, 4, 0) at M^T q = 5, (0, 6, 0)/(1, 5, 0) at M q = 6. qreal's row HUB bounds the full-met labels at a hub by
cap(h) <= 4 (fact H1), which these vertices respect.

**What a full-met label forces.** Let i be a helper with value h and type (r, u, v), r <= 2, and let l be a missing
label at i, edge i-b, l = h + b, that also has an H-B edge f-c at a full helper f, l = f + c. Then h + f = b + c is a
boundary-pair value, its pair P = {b, c} is determined by F2, and f lies in N(h). Distinct full-met labels at i meet
distinct full helpers (Lemma 4.6: two helpers share at most one missing label), the pairs P are pairwise disjoint (a
shared element would make two full helpers adjacent, Lemma 4.5), and the full helpers are jointly independent
(Lemma 4.4).

## 2. The conditions enumerated

For a candidate configuration (h, R, S) -- hub value h; R = the r triple representations of h used by its
represented edges (an r-subset of the F3 triples of h, distinct by Lemma 4.4; r <= 2 because a helper meeting a full
helper at a missing label is not full, Lemma 4.5); S = {f_1, ..., f_m} subset of N(h) with pairs P_j = pair(h + f_j)
-- the following were tested.

**C1, independence [proved].** The family

    F(h, R, S) = { H_f + T : f in S, T a triple of f }  u  { H_i + T : T in R }  u  { H_i + H_f + B_b + B_c : f in S, {b, c} = P_f }

is linearly independent in any normalized circuit containing the configuration. *Proof.* The B-B reference equations
E_l + B_b + B_c of the represented labels involved, the represented H-B equations H_f + B_a + E_l of the f's and of i,
and the two missing H-B equations H_i + B_{b_j} + E_{l_j}, H_{f_j} + B_{c_j} + E_{l_j} of every full-met label are
distinct gate equations, hence linearly independent as formal vectors (the latest result signal of a nonempty
combination cannot cancel; proof of Lemma 4.4). Add each reference to the H-B equations carrying its label
(invertible); E_l then occurs only in the reference, which can be deleted. Add the hub's missing equation of l_j to
f_j's (invertible): E_{l_j} then occurs only in the hub's equation, which can be deleted. What remains is F. Invertible
row operations, and deleting a row that holds a private coordinate, preserve independence. [] F does not depend on
which end of P_j is the hub's neighbour. The independence of the label forms E_l + T + B_c, E_l + T_i + B_b at l_j
(qreal's FM condition rank(C_{l_j}) >= 3 + r) is a consequence of C1, so FM was not applied separately. H1 of qreal
is the special case of C1 that keeps only the 3m vectors H_f + T.

**C3, Lemma O1 [proved in qreal section 2].** Each full helper owns two outputs in two distinct triples, the hub owns
r - 1 outputs in distinct represented triples, all owned outputs distinct: tested as a flow problem (`maxflow_o1`).

**X, boundary excess [proved lower bound; its use on a tail is derived].** The configuration's own edges -- for each
(f, T): the H-B edge at the apex and the B-B edge of the other two elements of T; the hub's r such pairs; the 2m
missing H-B edges at the ends of the P_j -- give every boundary vertex a degree deg(v) <= d_v (the odd-graph degree
of a boundary vertex is its fan-out d_v with the terminal use), so `E_B = sum_B (d_v - 2)_+ >= X := min over apex
choices of sum_B (deg(v) - 2)_+` (two triples sharing a pair may share its B-B edge; `excess()` minimizes over the
apex choices of the triples involved exactly when at most 7 triples overlap, and uses a valid under-count otherwise).
On the eventual tail, the exact identity of PROOF's Remark after Lemma 6.2 with Lemma 8.1 gives
`e(C_{j+2}) - e(C_j) = s_j + s_{j+1} + E_B,j + E_B,j+1 - budget` (L_H = 0 by Lemma 7.4; bridge/REPORT.md, qreal
section 5); e is bounded, so infinitely many consecutive pairs satisfy `E_B,e + E_B,o <= budget - s_e - s_o <= sigma`
(the claim's shortfall, 0..3 on the survivors), and a configuration with X > sigma cannot occur on the phases of
such a pair, which is all the exclusion argument uses. X was tabulated for sigma = 0, 1, 2, 3 and unrestricted.

**Not enumerated.** The apex ("label") choices beyond their effect on X: N1-distinctness of the labels and the
missing/represented consistency of the l_j only restrict apex choices (3 per triple) and never bind in the
configurations that matter (section 3.3); the transpose phase's own odd graph; global conditions (other hubs, the
remaining helpers). These are the subject of section 7.

**Search space and cost.** For each orientation: every odd non-boundary h with N(h) nonempty (128,068 / 177,412;
other values have m = 0 trivially), every r in {0, 1, 2} with r <= #triples(h) (r = 1: 12,580 / 17,140 hub values;
r = 2: 440 / 616), every R (<= 3 choices), every subset S of N(h) (|N(h)| <= 15) by depth-first extension (C1 is
hereditary: F(h, R, S) is a subfamily of F(h, R, S')), computing X and O1 for every independent S. Run time 27 s (M)
+ 44 s (M^T). `hub2_check.py` recomputes the maximum with a separate elimination routine over *all* subsets of
N(h) (no pruning) for |N(h)| <= 11 and all subsets of size <= 5 - r otherwise: identical histograms, 0 violations,
16 s.

## 3. Finite fact H2 [finite-checked] (`hub2.py`, `hub2.log`, `hub2_{M,Mt}.json`, `hub2_check.py`, `hub2_check.log`)

### 3.1 Capacity under C1 (+ O1)

cap_r(h) = the largest |S| such that F(h, R, S) is independent for some R of size r.

| orientation, r | hub values | cap histogram (C1) | with O1 | max = K_r |
|---|---|---|---|---|
| M, r = 0 | 128,068 | 1: 126,412; 2: 1,648; 3: 8 | identical | **3** |
| M, r = 1 | 12,580 | 0: 11,392; 1: 1,124; 2: 64 | identical | **2** |
| M, r = 2 | 440 | 0: 428; 1: 12 | identical | **1** |
| M^T, r = 0 | 177,412 | 1: 174,320; 2: 3,072; 3: 20 | identical | **3** |
| M^T, r = 1 | 17,140 | 0: 15,216; 1: 1,804; 2: 120 | identical | **2** |
| M^T, r = 2 | 616 | 0: 592; 1: 24 | identical | **1** |

So **K_r = 3 - r** in both orientations: H1's kappa = 4 is never attained once the hub's own relations and the mixed
relations are included (H1's cap-4 witnesses, weight-3 repeated values, become dependent with the mixed vectors),
and an anchored hub loses one full-met label per represented edge. For r = 1 most hub values have cap 0: a triple
value h = f + b + c is typically a one-swap of a triple T = {c, d, e} of f (h = {d, e, b}), and then
H_f + T, H_i + {d, e, b}, H_i + H_f + {b, c} sum to zero -- in gate terms, the six equations of
{i, d, l}, {e, b, l}, {i, b, l_j}, {f, c, l_j}, {f, d, l'}, {c, e, l'} would be dependent.

### 3.2 Degree budget

| orientation, r | cap histogram with X <= 0 | X <= 1, 2, 3 | K_r(sigma = 0..3) |
|---|---|---|---|
| M, 0 | 1: 126,508; 2: 1,552; 3: 8 | = C1 | 3, 3, 3, 3 |
| M, 1 | 0: 11,392; 1: 1,172; 2: 16 | = C1 | 2, 2, 2, 2 |
| M, 2 | 0: 428; 1: 12 | = C1 | 1, 1, 1, 1 |
| M^T, 0 | 1: 174,512; 2: 2,880; 3: 20 | = C1 | 3, 3, 3, 3 |
| M^T, 1 | 0: 15,216; 1: 1,900; 2: 24 | = C1 | 2, 2, 2, 2 |
| M^T, 2 | 0: 592; 1: 24 | = C1 | 1, 1, 1, 1 |

The degree budget of a shortfall-0 tail moves a few hundred hub values one step down (r = 1: 64 -> 16 values of
cap 2 for M, 120 -> 24 for M^T) but never the maximum, so no claim-level (shortfall-dependent) version of the row
was needed; the O1 assignment never fails on an independent configuration.

### 3.3 Realizable local configurations: the per-hub relaxation cannot be tightened below 3 - r

Explicit witnesses with X = 0 and an O1 assignment (`extract.log`; `hub2_{ori}.json` fields `witnesses_sigma0`;
values in hex over the boundary masks):

| ori, r | hub value h | R (hub triples as 64-bit boundary masks) | S (full values) |
|---|---|---|---|
| M, 0 | 0x80800080 | - | 0x181, 0x406000, 0x80800040 |
| M, 0 | 0x40404000 | - | 0x2030, 0x20404000, 0x80004080 |
| M, 1 | 0x2020200 | 0x2020200 | 0x181, 0x4000204 |
| M, 1 | 0x80800080 | 0x80800080 | 0x181, 0x404020 |
| M, 2 | 0x80800080 | 0x80800080, 0x800000404000 | 0x181 |
| M^T, 0 | 0x2020200 | - | 0x301, 0x60200, 0x4080004 |
| M^T, 0 | 0x20202 | - | 0x602, 0x1000003, 0x4040800 |
| M^T, 1 | 0x2020200 | 0x204000004 | 0x301, 0x60200 |
| M^T, 2 | 0x2020200 | 0x204000004, 0x2020200 | 0x301 |

(8 / 20 hub values attain 3 at r = 0 with X = 0; 16 / 24 attain 2 at r = 1; 12 / 24 attain 1 at r = 2.) These
satisfy every condition of section 2 (C1, O1, X = 0, apex choices consistent); whether they extend to a whole phase
is the joint question of section 7. They show that no further *per-hub* condition of the kinds listed can lower the
capacity below 3 - r: the count relaxation is not killable per hub beyond H2.

## 4. Lemma H2, row HUB2, HUB2L, PK4, PK5 [proved]

**Lemma H2.** In every normalized circuit of either orientation, every helper i satisfies

    r_i + m_i <= 3,      m_i = #{ missing labels at i with an H-B edge at a full helper }.

*Proof.* r_i = 3: m_i = 0 by Lemma 4.5 (a missing label meets at most one full helper). r_i <= 2: let the full-met
labels at i be l_1..l_m with full helpers f_1..f_m, distinct by Lemma 4.6, and let R be the r_i triples of i's
represented relations (distinct triples of h_i, Lemma 4.4). Then S = {f_j} subset of N(h_i) (section 1),
F(h_i, R, S) is independent (C1), and H2 (exhaustive over every h, R, S) gives m <= 3 - r_i. []

**Row HUB2.** With A = sum_{r=3} u_i (the number of full-met labels: exactly one full helper each, Lemma 4.5), every
helper with r_i <= 2 has its u_i - m_i other missing labels among the q - A labels that meet no full helper, so

    u_i <= (3 - r_i) + (q - A)      for every helper with r_i <= 2.

Exact case split: A = q - d for d = 0, ..., q - 2 (then every type (r, u, v) with r <= 2 and u > 3 - r + d has n = 0),
or A <= 1 (no restriction: u <= q <= 3 - r + q - 1 for r <= 2). A key is excluded iff all q cases are LP-infeasible;
each infeasible case has an ordinary Farkas certificate over the reduced column set (package rows + G\* + N1 + dark
rows + the equality A = q - d). Combined with the dark split: at most q (q + 1) LPs per key.

**Linear aggregate HUB2L (weaker).** In the case A = q - d: m_i >= u_i - d for every non-full helper; the (non-full
helper, full-met label) incidences at a full-met label l number at most 3 + 2 f_l ((3.2): l occurs in <= 4 + 2 f_l
gate equations, one of them the full helper's edge); summing over the A full-met labels and using F_miss + F_H <= F:
`sum_{r<3} (u - d)_+ n + 2 sum f_min n <= 3 (q - d) + 2F`.

**Packing rows PK4, PK5.** Lemma 10.4's argument: the missing-label sets of the helpers with u >= 3 are subsets of a
q-set pairwise intersecting in at most one element (Lemma 4.6). q = 4: two 3-subsets of a 4-set share two elements,
so `N_3 <= 1`. q = 5: three 3-sets pairwise sharing <= 1 element need six points; a 4- or 5-set shares >= 2 elements
with every other set of size >= 3; so `N_3 + 2 N_4 <= 2` (N_j = #{u >= j}). The package states (L23) for q = 6, 7
only; these two are the same lemma at q = 4, 5.

## 5. Effect at G = 75 [measured] (`scan1.log`, `scan2.log`, `scan_*_q0_g75.json`, `extract.log`)

| variant (cumulative) | surviving claims (M, M^T) | LP-feasible keys (of 1,134) | keys by q |
|---|---|---|---|
| package rows (qreal, reproduced there) | 1,508 (846, 662) | 1,134 | 0:31 1:323 2:40 3:146 4:119 5:205 6:153 7:61 8:54 10:2 |
| G\* + N1 + HUB + DARK + FM (qreal; reproduced here, 146 s) | 996 (504, 492) | 381 (194 M, 187 M^T) | 1:2 2:2 3:14 4:54 5:163 6:93 7:11 8:41 10:1 |
| **HUB2 in place of HUB** | **863 (454, 409)** | **166 (129 M, 37 M^T)** | 1:2 3:1 4:54 5:40 6:31 7:7 8:30 10:1 |
| **+ PK4, PK5** | **789 (416, 373)** | **116 (81 M, 35 M^T)** | 1:2 3:1 4:33 5:11 6:31 7:7 8:30 10:1 |
| + HUB2L | 789 (416, 373) | 116 | unchanged |

Shortfall histograms: 863 survivors 0: 454, 1: 295, 2: 88, 3: 26; 789 survivors 0: 426, 1: 270, 2: 69, 3: 24.
Keys by (q, z) after PK: (1,4) 1, (1,5) 1, (3,3) 1, (4,0) 12, (4,1) 19, (4,2) 2, (5,0) 8, (5,1) 2, (5,2) 1, (6,0) 20,
(6,1) 11, (7,0) 3, (7,1) 4, (8,0) 20, (8,1) 9, (8,2) 1, (10,0) 1; by h: 6: 5, 7: 10, 8: 5, 9: 6, 10: 12, 11: 1,
12: 3, 13: 1, 14: 20, 15: 10, 16: 13, 17: 13, 18: 14, 19: 3.

What dies under HUB2: every key whose vertices needed anchored hubs with 2-4 full-met labels or unanchored hubs with
4-6: the M^T q = 5 cluster (101 -> 4 keys), M q = 5 (62 -> 36), the q = 2 keys (7,11,4,2,6,Mt), (7,12,3,2,5,Mt) and
13 of the 14 q = 3 keys ((5,13,7,3,7), (5,14,6,3,6), (5,14,7,3,6), (6,13,5,3,5), (6,13,6,3,5) in both orientations,
(9,10,1,3,2,Mt), (10,8,1,3,2,Mt), (11,6,1,3,2,Mt)), whose (1,3,0)/(2,2,0)/(2,3,0) helpers sat at A = q. PK4/PK5 then
remove 21 M q = 4 keys and 27 q = 5 keys (two or more u >= 3 hubs on four or five labels). Of the 116 keys only 53
are load-bearing (feasible at some claim's k on the even side or ell on the odd side): M q = 4: 15, q = 5: 1,
q = 6: 26, q = 8: 2; M^T q = 4: 1, q = 5: 2, q = 6: 1, q = 7: 3, q = 8: 2. The most used: (14,1,1,6,0,M) (6 claims),
(16,3,3,4,0,M), (16,2,2,4,1,M), (11,5,0,5,1,Mt), (15,0,0,6,0,M), (12,3,1,4,2,Mt), (14,0,0,6,1,M), (9,5,4,8,0,Mt)
(4 each).

## 6. What remains [measured] (`vertices_hub2.log`, `vertices_final_qhub.log`)

**The M q = 6 block (30 keys, 26 load-bearing; e.g. (14,1,1,6,0,M), (15,0,0,6,0,M)), vertices under the final
variant.** Case A = q (d = 0) is infeasible for every key of the block; the vertices live in the cases A = 5 and
A = 4 (d = 1, 2) and all have the same shape: four or five (3, 1, 0) (A = 4..5), three to four (0, 3, 0) hubs
(L23 `N_3 <= 4` tight), three to four (2, 2, 0), one to three (3, 0, 0), q_D = 0, y_2 <= 1; e.g.
`(0,3,0):3.667 (2,2,0):4 (3,0,0):1.333 (3,1,0):5 y1:0.333 y2:0.667` and `(0,3,0):4 (2,1,0):1 (2,2,0):3 (3,0,0):2
(3,1,0):5` (L5 tight: 4 x 3 + 3 x 1 = 15 = C(6, 2)). Every hub sits exactly on H2's limit: a (0, 3, 0) with 2-3
full-met labels, a (2, 2, 0) with one full-met label (its r = 2 allows no second) plus the single non-full-met
label; A = q is dead because then the (2, 2, 0)s would carry two full-met labels. The integer structure is a
6-point configuration with four 3-sets pairwise meeting in one point (the (0, 3, 0)s) and three or four 2-sets (the
(2, 2, 0)s), one label met by no full helper.

**The M q = 4 block (32 keys, 15 load-bearing; h = 14..18, y <= 4, z <= 2) and the M q = 5 keys (9).** Not
dumped under the final variant (the vertex run stopped after the two q = 6 keys); from qreal's (13,4,4,4,1,M) vertex
and the key counts, the HUB2-only versions used two or three u >= 3 hubs on four or five labels, which PK4/PK5
removed (54 -> 33 and 40 -> 11 keys); what is left must sit at one (q = 4) or two (q = 5) u >= 3 hubs with
(1, 2, 0)/(2, 1, 1)/(1, 1, 1) helpers and A <= q - 1 [derived from the rows, not dumped].

**M^T q = 7-8, small h (28 keys; e.g. (10,2,10,8,0,Mt), (9,5,4,8,0,Mt)).** Feasible only in the case A = q - 2:
`(0,5,0):0.5 (1,4,0):1.5 (2,3,0):4 (3,1,0):2 (3,2,0):2 y2:2` -- a (0, 5, 0) with three full-met labels, (1, 4, 0)s
with two, (2, 3, 0)s with one, i.e. every hub again at `r + m = 3` with the two non-full-met labels filling up
to u; L5 tight (sum C(u, 2) = 28 = C(8, 2)).

**q <= 3 (3 keys).** (19,0,0,1,5,Mt) and (18,1,1,1,4,Mt) are unchanged from qreal (seven to eight (3, 0, 0), seven
(2, 0, 1), three (2, 1, 0), N1 tight; A = 0, so H2 is silent). (19,0,4,3,3,M) survives only in the case A <= 1:
`(0,2,1):3 (1,1,1):3 (2,1,0):6 (3,0,0):7` (L12\*, L17-M, N1, L5 tight).

In every surviving vertex with q >= 4 the hubs are at the H2 limit and L5 (or L23/PK) is tight: the next
restriction must be joint (section 7a), not per hub.

## 7. The finite searches that would decide the remaining families [conjecture: finite and necessary; whether they kill is open]

(a) **Joint hub systems at q = 4..8 with A >= q - 2.** With A = q every hub's labels are full-met, so all hubs of the
phase sit on the same set S of q full helpers; every hub value lies in an intersection of sets f_j + PV (for u >= 2
these are the 2- and 4-subsets of B with XOR f_j + f_k: a handful per pair); two hubs share at most one label (Lemma
4.6); PK4/PK5 (and L23) bound the u >= 3 hubs; and the whole family -- all represented relations plus one mixed vector
per (hub, full-met label) and t_l - 1 per missing label met by t_l helpers -- must be independent (the argument of
C1 verbatim; it holds on all 1,264 real phases, `qh_circ.py`). With A = q - 1 or q - 2 one or two labels are
hub-only, and the same mixed vectors apply among the hubs sharing them. Enumerate: jointly independent q-sets of
full values (C(80, 4) = 1.6 M candidates for M before independence filtering), per set the candidate hubs from the
pair intersections, then the integer type vectors of the local system (the INT oracle of qbound/qreal gives integer
feasibility; its solutions are the targets). A matter of hours in optimized code, not of the two hours here.

(b) **M^T q = 1, z = 4-5 ((19,0,0,1,5,Mt), (18,1,1,1,4,Mt)).** Seven or eight jointly independent full values with N1
tight (21-24 of the 23-24 represented labels), the ~12 remaining anchored helpers of r = 2 sharing labels with them
(Lemma S: at a shared label 2 + 1 per r = 2 helper <= sigma(P) <= 5, so every such label is one of the 426 rich pairs
of M^T), y = 0 or 1 (every even signal is an odd+odd result and, with F = 0 or 1, every label occurs in <= 4 gate
equations), Lemma O1 (>= 14 + 12 owned outputs of 32) and, on shortfall-0 tails, sum_B d_v = 93 - U with every
d_v in {1, 2}. A search over independent 7-sets with these filters was not started (qreal measured millions of
independent 10-sets through one value).

(c) **(19,0,4,3,3,M)** survives only in the case A <= 1 with seven (3,0,0), six (2,1,0), three (1,1,1) and three
(0,2,1) helpers (`vertices_hub2.log`): three missing labels shared pairwise by the (0,2,1) hubs and met by the six
(2,1,0); the mixed vectors of (a) among these nine helpers are the finite question.

## 8. Statements and labels

| statement | label |
|---|---|
| C1: independence of F(h, R, S) in any normalized circuit containing the configuration | [proved] (Lemma 1.1 / proof of Lemma 4.4, Lemma 4.1) |
| H2: cap_r(h) <= 3 - r for every h, both orientations; histograms; maxima attained with X = 0 | [finite-checked] (`hub2.py`; second implementation `hub2_check.py`; M and M^T agree) |
| K_r(sigma) = 3 - r for sigma = 0..3; O1 never binding | [finite-checked] |
| Lemma H2: r_i + m_i <= 3 | [proved] (Lemmas 4.4, 4.5, 4.6 + C1 + H2) |
| Row HUB2, its exact case split, Farkas-certifiability of each case | [proved] |
| HUB2L, PK4, PK5 | [proved] ((3.2), Lemma 4.5, Lemma 4.6 / Lemma 10.4's argument) |
| X <= E_B for any phase containing the configuration | [proved] |
| E_B,e + E_B,o <= shortfall on infinitely many tail pairs | [derived] (PROOF Remark after Lemma 6.2, Lemmas 8.1, 7.4; the identity is asserted by `stress.py` on every phase) |
| effects 996 -> 863 -> 789 claims, 381 -> 166 -> 116 keys; HUB2L adds nothing | [measured] |
| reproduction of qreal's 996 / 381 with `qh_lp.py` | [measured] |
| 0 violations of H2 / HUB2 / the mixed-vector independence on 1,264 phases (m_i = 0 everywhere) | [measured] |
| the searches of section 7 decide the remaining families | [conjecture] |
| any bound beyond 75 | **not claimed** |

## 9. Files in `~/xs-campaigns/2026-11-07-sprint/qhub/`

`hub2.py`, `hub2.log`, `hub2_{M,Mt}.json` (H2 search; per-h capacities, X by m, witnesses); `hub2_check.py`,
`hub2_check.log`, `hub2_check.json` (second method); `make_qh_lp.py`, `patch2_qh_lp.py`, `qh_lp.py` (qreal's
`qr_lp.py` plus variants `HUB2`, `HUB2L`, `PK`); `run_scan1.sh`, `run_scan2.sh`, `run_scan3.sh`, `scan1.log`,
`scan2.log`, `scan3.log`; `scan_GstarN1HUBDARKMFM_q0_g75.json` (reproduction), `scan_GstarN1HUB2DARKMFM_q0_g75.json`,
`scan_GstarN1HUB2DARKMFMPK_q0_g75.json`, `scan_GstarN1HUB2LDARKMFMPK_q0_g75.json`; `vertices_hub2.log`, `vert2.py`,
`vertices_final_qhub.log`; `extract.py`, `extract.log`; `qh_circ.py`, `qh_circ.log`, `qh_circ.json` (316 circuits,
1,264 phases).
