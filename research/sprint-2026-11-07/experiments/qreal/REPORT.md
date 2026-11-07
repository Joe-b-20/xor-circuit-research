# Realizability of the G = 75 survivors: hub helpers, full-helper geometry, dark-label split

qreal agent report, 2026-11-07 (about 2.5 hours). Working directory `~/xs-campaigns/2026-11-07-sprint/qreal/`. The git
repository, `lb76/pkg_copy/`, `qbound/` and `qcheck/` were read only; `qbound/qb_lp.py` was copied to `qr_lp.py` and
extended; the package's `lp_regen.py` and `stress.py` are imported unchanged. One python process at a time under
`nice -n 8`; the longest run was a full G = 75 scan with case splits (135 s); total compute about 25 minutes.

Labels: **[proved]** (proof written here; package lemmas and finite facts F2-F14 used as black boxes),
**[finite-checked]** (computed exactly by a script in this directory, with a second method or a transpose check),
**[measured]** (script output on the LP model or on known circuits), **[derived]** (arithmetic from proved statements,
not re-verified independently), **[conjecture]**, **[guess]**.

**The lower bound remains L(M) >= 75.** Nothing below is a bound of 76: every scan leaves survivors (996 oriented claims
after all accepted rows), and no certificate-style coverage of G = 75 was produced here. The bound would move only if
the survivors reached 0 with complete, independently checked certificate coverage, which is not the case.

## 0. Results in ten lines

1. **Finite fact H1 (hub capacity) [finite-checked]:** for every odd non-boundary value h at most **4** jointly
   independent full values f have h + f equal to a boundary-pair value (M and M^T alike); at most 2 unless h is a
   repeated value with exactly two triple representations (8 values of M, 20 of M^T attain 4).
2. **Row HUB [proved]:** for every helper i with r_i <= 2, `u_i <= 4 + (q - A)`, `A = sum_{r=3} u` (the missing labels
   that meet a full helper). Exact case split on A (each case Farkas-certifiable). On top of qbound's G\*+N1: claims
   **1,313 -> 1,256** (693 M, 563 M^T), LP-feasible keys 681 -> 585 (q = 6: 151 -> 104, q = 7: 61 -> 15). [measured]
3. **Dark-label case split (Task c) [proved rows, measured effect]:** the package's quotient rows (L13)-(L18) with the
   q_D terms retained, plus bright/dark occurrence budgets and the y_2 = y2d + y2m decomposition, as an exact split on
   q_D = 0..q, in both orientations: claims **1,256 -> 996** (504 M, 492 M^T), keys 585 -> 381 (q = 1: 57 -> 2,
   q = 2: 30 -> 2, q = 3: 57 -> 14). The M^T q = 1 cluster and the n_3 = 9 configuration of M are gone.
4. **Lemma O1 (chronology of full helpers) [proved]:** every full helper defines, through its represented edges that
   are not its own defining gate, at least two distinct outputs, each in the corresponding triple; distinct across full
   helpers. On the 316 circuits every one of the 324 full helpers defines exactly 2. [measured] Negative finite result:
   the induced output-assignment condition never bounds n_3 (flow-feasible independent 10-sets exist for M, 14 for M^T).
5. **Full-value geometry (Task a) [finite-checked, partly]:** independent sets of full values cannot be enumerated
   (more than 6 million 10-sets through one value); exact maximum boundary covers C(m) = 9, 18, 27, 35, 42 (M) and
   9, 18, 27, 36, 43 (M^T) for m <= 5, lower bounds beyond. The boundary-degree row `9 n_3 + 64 - C(n_3) <= sum_B d_v`
   is vacuous at G = 75 with the valid bound C(m) <= C(5) + 9(m-5). The label budget `3 n_3 + ... <= x + y - q` cannot be
   sharpened by counting: a non-full anchored helper may share a label with a full helper (section 3).
6. **Finite fact FM [finite-checked]:** at a label l = f + c (f full) rank(C_l) is 3 for 80 % of the 4,640 (M) /
   6,496 (M^T) such labels, at most 7 (M; only the four F11 labels) / 6 (M^T); rows FM7/FM9 are valid but add nothing
   at G = 75 (996 / 381 unchanged). [measured]
7. **Two-phase identity (Task e) [derived]:** on the eventual tail `s_e + s_o + E_B,e + E_B,o = budget`; 511 of the 996
   surviving claims have shortfall 0, so on their tails both phases sit exactly at the proved minimum s and every
   boundary vertex has degree <= 2 in both phases. No local row lower-bounds E_B (the full helpers' excess X(S) is 0 on
   every real phase and can be 0 for hypothetical sets), so (e) adds no exclusion without geometry of the non-full
   helpers.
8. All new facts and rows: **0 violations** on the 13 controls and 303 real circuits, 1,264 phases (`qr_circ.py`);
   the q_D-retained rows are tight (slack 0) on real M^T phases, as G\* is. [measured]
9. **Cumulative: 1,508 -> 1,313 (qbound) -> 996 claims (504 M, 492 M^T); keys 1,134 -> 681 -> 381.** Survivors by
   shortfall 0/1/2/3: 511/337/109/39; keys by q: 1:2 2:2 3:14 4:54 5:163 6:93 7:11 8:41 10:1. [measured]
10. What remains (section 6): q = 4..8 configurations with five or six (3,1,0) helpers and anchored hubs carrying 3-4
    full-met labels, and M^T q = 1, z = 4-5 phases with 7-8 full helpers. The finite search that would decide the first
    family is small and is specified in section 6.

## 1. Task (b): hub helpers

### 1.1 Finite fact H1 [finite-checked] (`hub.py`, `hub.log`, `hub_cap_{M,Mt}.json`)

For an odd value h not in B let `N(h) = { f full : h + f is a boundary-pair value }` and let `cap(h)` be the largest size
of a subset S of N(h) whose 3|S| relation vectors `H_f + T` (T over the three triples of f) are linearly independent
(equivalently the 2|S| six-set differences are independent; this implies pairwise non-adjacency, F4). Only h in f + PV
can have cap > 0: 128,068 odd non-boundary values for M, 177,412 for M^T.

| | M | M^T |
|---|---|---|
| N(h) size histogram | 1: 114,060; 2: 1,280; 3: 10,992; 4: 444; 5: 100; 6: 672; 8: 260; 9: 160; 11: 88; 12: 4; 15: 8 | 1: 157,472; 2: 2,352; 3: 14,432; 4: 892; 5: 192; 6: 1,344; 8: 308; 9: 224; 11: 172; 12: 4; 15: 20 |
| cap histogram, all h | 1: 125,128; 2: 2,840; 3: 92; 4: 8 | 1: 172,060; 2: 5,156; 3: 176; 4: 20 |
| cap histogram, triple values | 1: 10,984; 2: 1,496; 3: 92; 4: 8 | 1: 14,236; 2: 2,708; 3: 176; 4: 20 |
| max cap: one representation / two / full values / non-triple values | 2 / 4 / 2 / 2 | 2 / 4 / 2 / 2 |
| **kappa_0 (any h), kappa_1 (triple values)** | **4, 4** | **4, 4** |

Extremal example (M): h = 0x80800080 with S = {0x181, 0x80c0, 0x404020, 0x80400080}; the eight M values of cap 4 are
weight-3 repeated values. Self-checks: the maximum is exact (exhaustive descent over the subsets of N(h), |N(h)| <= 15);
second method: for 20,000 witnesses the 3|S| relation vectors with explicit helper coordinates have full rank (0
failures); the pairs h + f of a witness are pairwise disjoint (a shared element would make two f adjacent); M and M^T
agree in kappa. Run time 13 s.

### 1.2 Lemma H1 and row HUB [proved]

**Lemma H1.** In every normalized circuit of either orientation, for every helper i with r_i <= 2 the number of missing
labels at i that have an H-B edge at a full helper is at most cap(h_i) <= 4. Consequently, with `A = sum_{r=3} u_i`,

    u_i <= 4 + (q - A)   for every helper i with r_i <= 2.

*Proof.* Let l be a missing label at i (edge i-b, l = h_i + b) that also meets a full helper f (edge f-c, l = f + c).
Then h_i + f = b + c is a boundary-pair value, so f lies in N(h_i). Two distinct missing labels at i meet distinct full
helpers: if both met f, then i and f would share two missing labels, against Lemma 4.6. The full helpers of a circuit
have jointly independent relations (Lemma 4.4), so the full helpers met by i's missing labels form an independent
subset of N(h_i), of size <= cap(h_i) <= 4 (H1). Every missing label meets at most one full helper (Lemma 4.5), so
exactly A labels meet one and the other missing labels at i are among the q - A that meet none. []

Needs only normalization and F2-F4 (through Lemmas 4.1, 4.4-4.6): valid on every phase and control.

**Exact case split.** For q >= 5: either `A <= 4` (no restriction) or `A = q - d` with d in {0, ..., q - 5}, and then every
type (r, u, v) with r <= 2 and u > 4 + d has n = 0. A key is excluded iff all q - 3 cases are LP-infeasible; each
infeasible case has an ordinary Farkas certificate (package rows + G\* + N1 + the equality A = q - d, over the reduced
column set). For q <= 4 the row is vacuous. **Linear aggregate (weaker):** the non-full-met labels at non-full helpers
are H-B incidences of the q - A labels meeting no full helper, each with <= 4 + 2 f_l occurrences ((3.2) as in (L10)):
`sum_{r<3} (u - 4)_+ n + 4A + 2 sum f_min n <= 4q + 2F`.

### 1.3 Effect at G = 75 [measured] (`scan_hub.log`, `scan_GstarN1HUB_q0_g75.json`)

| variant | surviving claims (M, M^T) | LP-feasible keys (of 1,134) | keys by q |
|---|---|---|---|
| package rows (reproduced) | 1,508 (846, 662) | 1,134 | 0:31 1:323 2:40 3:146 4:119 5:205 6:153 7:61 8:54 10:2 |
| G\* + N1 (qbound, reproduced) | 1,313 (724, 589) | 681 | 1:57 2:30 3:57 4:72 5:197 6:151 7:61 8:54 10:2 |
| + HUB linear | 1,307 (718, 589) | 676 | 6:149 7:60 8:52, rest unchanged |
| **+ HUB case split** | **1,256 (693, 563)** | **585** | 1:57 2:30 3:57 4:72 5:197 **6:104 7:15 8:51** 10:2 |

What dies: the q = 6, 7 vertices with an unanchored hub (0,6,0)/(1,5,0)/(1,6,0) and L6 tight (key (10,6,6,6,0,M)
survives HUB only through A <= 5 and dies with the dark split below). What survives at q = 5: A = 5 still allows every
non-full helper u <= 4, which the (1,4,0), (2,3,0), (1,3,0) helpers of the M^T q = 5 vertices use.

### 1.4 Circuit check [measured]

On all 1,264 phases no missing label meets a full helper at all (A = 0 everywhere: real full helpers, n_3 <= 4, carry
only represented edges), so H1 is consistent with but not exercised by the circuits; `u_i <= 4 + q - A` holds with
slack >= 4 + q - u_max >= 8. The actual-mask check `#full-met <= cap(h_i)` passes trivially (0 <= cap).

## 2. Lemma O1: chronology of full helpers [proved]

**Lemma O1.** Let f be a full helper with represented edges f-a_j, labels l_j and B-B edges b_j-c_j
(T_j = {a_j, b_j, c_j}, j = 1, 2, 3). Each edge f-a_j whose gate is not the defining gate of f defines an output in T_j:
either the gate's result is a_j (an output defined by this gate), or it is l_j, and then the B-B gate of l_j has result
b_j or c_j, an output. At least two of the three edges are not f's defining gate, so f defines >= 2 outputs in two
different triples, and the outputs so defined by all full helpers are pairwise distinct.

*Proof.* The gate of edge f-a_j has equation {f, a_j, l_j}; its result is f, a_j or l_j, and f is the result of exactly
one gate. A boundary signal that is a gate result is an output. If the result is l_j, the B-B gate {b_j, c_j, l_j} of the
represented label l_j cannot have result l_j (each signal is the result of exactly one gate, Lemma 1.1), so its result is
b_j or c_j, an output in P_{l_j} subset T_j. Distinctness: an output is determined by its defining gate; gates
{f, a_j, l_j} differ for distinct (f, j); gates {b_j, c_j, l_j} differ for distinct labels and the labels of full helpers
are pairwise distinct (N1); the two kinds differ (one helper operand versus two boundary signals). []

Consequences. (i) A full value with fewer than two triples containing an output is never a full helper: vacuous, every
full value has 2 or 3 such triples (M: 60 / 20; M^T: 84 / 28; all 60 resp. 84 weight-3 values have their all-input
triple as the forced defining edge). (ii) For the set S of full helpers the assignment (f, T_j) -> output in T_j, one per
triple, two per f, all distinct, exists: `flow(S) >= 2|S|`. Negative finite result (`fullgeo.py`): flow-feasible
jointly independent sets of the maximal size exist (M: 18,623 10-sets found within a 40,000-node cap; M^T: 18,602
14-sets), so (ii) never bounds n_3. (iii) `2 n_3 <= 32` (never active). Check on the 316 circuits: every full helper
defines exactly two outputs (histogram {2: 324}), all distinct, each in its triple; 0 violations.

## 3. Task (a): the full-helper label budget and the geometry of full-value sets

**Why the label budget cannot be sharpened by counting [proved].** N1 already says the 3 n_3 labels of the full helpers
are distinct. A non-full anchored helper i may share a represented label l with a full helper f: with f-a and i-a' both
of label l (B-B edge b-c), i = a' + b + c is a triple value adjacent to f (f + i = a + a'); for r_i = 1 the four relations
H_f + T_1, H_f + T_2, H_f + T_3, H_i + {a', b, c} are independent (new coordinate H_i), and the three gates {f, a, l},
{i, a', l}, {l, b, c} are distinct gate equations: nothing in Lemmas 4.1-4.6 forbids it. For r_i = 2 the shared label
needs sigma(P_l) >= 3 (Lemma S), which 246 of the 312 rich pairs of M satisfy. So the only count that the represented
labels must satisfy is `3 n_3 + (unshared labels of the other anchored helpers) <= x + y - q`, with no provable lower
bound on the unshared part; the 3^{n_3}-type enumeration proposed in qbound 8(a) would only re-derive N1.

**Boundary-degree budget [proved row, vacuous at G = 75].** Each full helper gives one H-B edge and one B-B edge per
triple; these 6 n_3 edges are distinct (N1), so `d_v >= mult_S(v)` for every boundary vertex (mult_S = number of
(f, triple) pairs containing v), and since every boundary vertex has degree >= 1,
`sum_v max(1, mult_S(v)) = 9 n_3 + 64 - cover(S) <= sum_B d_v = 2(x+y-q) + 32 + h - y + q - z` (Lemma 4.2), i.e.
**cover(S) >= 9 n_3 + 64 - sum_B d_v**. For the n_3 = 9 vertex of key (12,5,5,2,3,M) this needs cover >= 49.

**Finite data (`fullgeo.py`, `fullgeo_{M,Mt}.log`, `fullsets_{M,Mt}.json`) [finite-checked where marked exact].**
Supports supp(f) (9 elements) of compatible pairs overlap in 0 / 1 / 2 / 3 / 6 elements for 1,792 / 96 / 384 / 288 / 240
pairs (M) and 3,840 / 192 / 768 / 576 / 336 (M^T). Maximum cover over jointly independent m-sets, branch and bound with
a 25 s cap per m:

| m | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| C(m), M | 9 | 18 | 27 | 35 | 42 | >= 45 | >= 47 | >= 48 | >= 48 | >= 48 |
| C(m), M^T | 9 | 18 | 27 | 36 | 43 | >= 50 | >= 57 | >= 58 | >= 58 | >= 58 |

(m <= 5 exact; m >= 6 lower bounds only, the search timed out. M^T continues with >= 58 up to m = 12 and >= 60 for
m = 13, 14.) No five jointly independent full values of M have pairwise disjoint supports (C(5) = 42 < 45). A valid
upper bound for the row is C(m) <= C(5) + 9 (m - 5) (each further value adds <= 9), with which the boundary-degree row
reads `9 n_3 <= sum_B d_v - 64 + C(n_3)`, i.e. n_3 <= 11 for every surviving key (sum_B d_v is 90..100): vacuous. It would
bite only if C(9) <= 48 were proved; the lower bound found is already 48 (M), so at best n_3 = 9 would be excluded for
keys with sum_B d_v <= 96, and the n_3 = 9 key died anyway through the dark split (section 4). Not pursued further.
The enumeration itself is out of reach in python: the capped DFS found 6.1 million independent 10-sets containing one
fixed value before its 20-million-node cap (`count_only.py`).

**Finite fact FM [finite-checked] (`fullmet.py`, `fullmet.log`).** For every full value f and boundary element c, the
label l = f + c has rank(C_l) (F6) in {3: 3,696; 4: 692; 5: 140; 6: 108; 7: 4} over the 4,640 distinct such labels of M
and {3: 4,960; 4: 1,176; 5: 144; 6: 216} over the 6,496 of M^T (rank 3 is the three forms E_l + T + B_c of f itself).
Each full value has only 12-23 of its 64 labels with rank >= 4. **Rows FM7/FM9 [proved]:** at a missing label l met by
a full helper through f-c, `W_l + Y_l <= rank(C_l)` (proof of (L7)/(L7\*)) and `Z_l <= min(3, rank(C_l) - 1)` (proof of
(L15)); summing over the A full-met labels (distinct) and using 7 / 3 at the others,
`W + y_1 <= 7 (q - A) + top_full(A)` and `Z <= 3 (q - A) + top3_full(A)`, where top_full(A) = sum of the A largest ranks
= 7, 14, 21, 28, 34, 40, ... (M), 6A (M^T) and top3_full(A) = 3A; linearised exactly by their chord lines (concave).
Effect: none at G = 75 (the LP's labels take the few high-rank values). Qualitatively: a full-met label that also meets
an anchored helper with r >= 1 is one of 944 (M) / 1,536 (M^T) labels, and one of 252 / 360 if r >= 2 meets it.

## 4. Task (c): dark-label case split

### 4.1 Rows [proved]

Fix a phase and let d = q_D be its number of dark missing labels (no H-B edge at an anchored helper). With the aggregates
of PROOF section 10, qbound's y_0, y_1, y_2 (y -> y_2, +y_1 as in G\*) and rho = 32 - dim J (8 for M, 4 for M^T),
eps = 2 (M) / 0 (M^T), PROOF's proofs of (L13)-(L18) go through with the nonpositive q_D terms retained: from
`dk := sum_bright k_l >= rho - y_2 - z - D_0 + d` (Lemma 10.2 in the G\* form) and the per-label capacities
`W_l + Y_l <= 7 - 2 k_l`, `Z_l + k_l <= 3`, `Z + E + 3 n_act <= 3 (q - d)` (M^T) / `2Z + 2E + 3 dk <= 6 (q - d)` (M),
`W + A + 3 dk <= 7 (q - d)` (M^T), summed over the q - d bright labels:

    (L13d)  W + y_1 - 2 D_0        <= 2 y_2 + 2 z + 7 q - 2 rho - 9 d
    (L14d)  W + A + y_1 - 2 D_0    <= 2 y_2 + 2 z + 7 q - 2 rho + eps - 9 d
    (L15d)  Z - D_0                <= y_2 + z + 3 q - rho - 4 d
    (L17Md) 2 Z + 2 E - 3 D_0      <= 3 y_2 + 3 z + 6 q - 24 - 9 d            (M)
    (L17Td) Z + E - 3 D_0          <= 3 y_2 + 3 z + 3 q - 12 - 6 d            (M^T)
    (L18d)  W + A - 3 D_0          <= 3 y_2 + 3 z + 7 q - 12 - 10 d           (M^T)

and, from (3.2) (a missing label occurs in <= 4 + 2 f_l gate equations), with new nonnegative columns y2d (ee gates whose
single missing signal is dark), Fb and Fd (sum of f over bright / dark labels):

    sum_{r>=1} u n >= q - d                 every bright label has an H-B edge at an anchored helper
    sum_{r>=1} u n + y_1 <= 4 (q - d) + 2 Fb  anchored helpers' missing edges and kind-1 gates sit at bright labels
    y2d <= 4 d + 2 Fd                        a y2d gate is an occurrence of a dark label
    Fb + Fd + sum f_min n <= F;  y2d <= y_2;  y_2 - y2d <= C(q, 2)   (two missing labels lie together in <= 1 gate)
    y_1 + 2 y_2 - y2d + U + 2 sum f_min n <= 4 q + 2 F   ((I) with gates of >= 2 missing signals counted twice)
    d = q: Fb = 0;   d = 0: Fd = y2d = 0.

A key is excluded iff all q + 1 cases are LP-infeasible (combined with the HUB cases: at most (q + 1)(q - 3) LPs per
key; each infeasible case is Farkas-certifiable). For q = 1 this is qbound's split: bright (d = 0) forces y_2 = 0 (no
dark label, no pair of missing labels) and then (L17Td) gives z >= 3; dark (d = 1) forces W = y_1 = 0 and
`y_2 + z + D_0 >= 5` with `y_2 = y2d <= 4 + 2 Fd`, while D_0 <= 0 at q = 1 (every u <= 1 by (L5)).

### 4.2 Effect [measured] (`scan_dark.log`, `scan_GstarN1HUBDARKM_q0_g75.json`)

| variant | surviving claims (M, M^T) | keys | keys by q |
|---|---|---|---|
| G\* + N1 + HUB | 1,256 (693, 563) | 585 | 1:57 2:30 3:57 4:72 5:197 6:104 7:15 8:51 10:2 |
| **+ DARK split (both orientations)** | **996 (504, 492)** | **381** | **1:2 2:2 3:14 4:54 5:163 6:93 7:11 8:41 10:1** |
| + FM7/FM9 | 996 (504, 492) | 381 | unchanged |

Keys by orientation after the split: 194 M, 187 M^T. The M^T q = 1 cluster (57 keys) is reduced to (18,1,1,1,4,Mt) and
(19,0,0,1,5,Mt): the bright case needs z >= 3 and the dark case needs y + z + D_0 >= 5 with D_0 <= 0, so every q = 1 key
with y + z <= 4 and z <= 2 dies. The M n_3 = 9 key (12,5,5,2,3,M) and the hub key (10,6,6,6,0,M) are infeasible in every
case. Shortfall histogram of the 996 survivors: 0: 511, 1: 337, 2: 109, 3: 39 (before: 0..4).

### 4.3 Circuit check [measured]

On the 1,264 phases, with the actual q_D, y2d, y2m, Fb, Fd of each phase (`qr_circ.py`): minimum slacks (M / M^T):
L13d 24 / 0, L14d 26 / 0, L15d 14 / 0, L17Md 28 / -, L17Td - / 0, L18d - / 0, bright lower 2 / 0, bright capacity 9 / 0,
dark capacity 0 / 11, Fb + Fd + F_H <= F 9 / 8, y2m <= C(q,2) 21 / 18, (I') 32 / 37, Fb = 0 when d = q (2 phases) 0,
Fd = y2d = 0 when d = 0 (67 phases) 0: **no violation**; five of the rows are tight on real M^T phases. Real phases have
q_D = 0..8 (M), 3..7 (M^T), y2d up to 16, y2m up to 8.

## 5. Task (e): the two-phase identity [derived]

PROOF's Remark after Lemma 6.2 gives the exact form of (B): `2x' + h + y + F_H = 64 + q + z + e_1 + L_H + sum_B (wdeg_v - 1)/2`
with `(wdeg_v - 1)/2 + f_v = (d_v - 2)_+` per boundary vertex, i.e. the drift of Lemma 8.2 is the identity
`e(T(C)) - e(C) = s + 96 - G + x - 2x' + E_B + L_H` (bridge/REPORT.md). On the eventual tail the integer potential is
constant, so summing two consecutive steps (x alternating a, b; L_H = 0 by Lemma 7.4):

    s_e + s_o + E_B,e + E_B,o = a + b + 2G - 192 = budget      (exact on the eventual tail).

Consequences for a surviving claim with proved bounds k, l (shortfall sigma = budget - k - l): `E_B,e + E_B,o <= sigma`
and `s_e + s_o <= budget`. For the 511 claims with sigma = 0 every boundary vertex has degree <= 2 in both phases and
both phases sit exactly at s = k, s = l. To turn this into exclusions one needs lower bounds on E_B from the local
systems; the only one available is the full helpers' excess X(S) = sum_v (mult_S(v) - 2)_+, which is 0 on every real
phase and can be 0 for hypothetical sets (compatible pairs with disjoint supports abound), and the non-full helpers'
triples are not fixed by the type counts. So (e) is a coupling without a lever yet; what it does fix on a sigma = 0 tail
is combinatorially strong (exactly sum_B d_v - 64 boundary vertices of degree 2, the rest of degree 1, in each phase)
and should be used by any realizability enumeration of a concrete configuration (section 6). The joint two-phase LP
was not built.

## 6. Cumulative count, what remains, and why

**Cumulative [measured]:** 1,508 (package) -> 1,313 (qbound G\*+N1) -> 1,256 (+HUB) -> **996 (+DARK; +FM unchanged)**
oriented claims, 504 M-even and 492 M^T-even; LP-feasible keys 1,134 -> 681 -> 585 -> **381** (194 M, 187 M^T; by q
1:2 2:2 3:14 4:54 5:163 6:93 7:11 8:41 10:1). Survivors by h_e: 9: 24, 10: 154, 11: 238, 12: 225, 13: 165, 14: 106,
15: 57, 16: 22, 17: 5. The integer oracle (branch and bound) was not run on the final system.

**Remaining keys with q <= 3 (18):** (18,1,1,1,4,Mt), (19,0,0,1,5,Mt), (7,11,4,2,6,Mt), (7,12,3,2,5,Mt),
(9,10,1,3,2,Mt), (10,8,1,3,2,Mt), (11,6,1,3,2,Mt), (19,0,4,3,3,M), and the small-h keys (5,13,7,3,7), (5,14,6,3,6),
(5,14,7,3,6), (6,13,5,3,5), (6,13,6,3,5) in both orientations.

**Surviving configurations (LP vertices, `vertices_final.log`) [measured]:**
- M^T q = 5, e.g. (11,5,5,5,0,Mt): five (3,1,0) (A = 5, L6 tight) plus (1,3,0) / (1,4,0) / (2,3,0) / (2,2,0) helpers whose
  3-4 missing labels are all full-met, plus two or three (3,0,0); y_2 = 4..5 with q_D = 0 (all labels bright).
  M^T q = 5 holds 101 keys, M q = 5 62 keys; q = 4..8 together 362 of the 381 keys.
- M^T q = 1, z = 4-5: (19,0,0,1,5,Mt): seven to eight (3,0,0) (N1 tight: 3 n_3 <= 23), seven (2,0,1), three (2,1,0);
  (18,1,1,1,4,Mt): eight (3,0,0), five (2,0,1), three (2,1,0), (1,1,1), (0,1,2), y_0 = 1.
- M^T q = 2, small h: (7,11,4,2,6,Mt): (2,2,6) plus four to five full helpers of types (3,0,1)/(3,0,3)/(3,1,0)/(3,1,2),
  y_0 = 7, y_2 = y2d = 4 (one dark label carrying four ee gates).
- M q = 4-5: (13,4,4,4,1,M): four to six (3,0,0), three (3,1,0), (2,2,0)s and an unanchored (0,3,0); (12,4,4,5,1,Mt):
  (0,4,0) hubs with five (3,1,0).

**Why the count relaxation cannot see them, and the finite search that would.** The anchored hubs of the q = 5 family
need a helper value h_i with cap(h_i) >= 3: only 100 values of M and 196 of M^T (all repeated values with two
representations, section 1.1), each with an explicit list of at most C(|N(h)|, 3) <= C(15, 3) candidate witness sets of
full helpers; the hub's labels l_j = f_j + c_j must each admit the hub's own represented relation at the same label,
hence rank(C_{l_j}) >= 3 + r_i >= 4, which only 12-23 of each full value's 64 labels satisfy (FM); the five (3,1,0) must
be jointly independent with each other and with the hub's relation; each full helper must own two outputs in distinct
triples (O1); and on a shortfall-0 tail every boundary vertex has degree <= 2 (section 5). Enumerating (hub value,
witness set, label choice, hub triple) under these constraints is a search of at most a few hundred thousand cases per
orientation and would decide the q = 5 hub family exactly; it was not started for lack of time. The M^T q = 1, z = 4-5
family (7-8 full helpers, N1 tight) needs the realizability of 7-8 jointly independent full values whose 21-24 labels
are nearly all the represented labels of the phase, i.e. the label-sharing geometry of section 3 made concrete: a
search over independent 8-sets (there are millions) with the output assignment (O1), boundary degrees and the kind-0
six-set relations (L12\*) as filters. Neither search is a linear row; both are finite.

**Conditional statement.** If every one of the 996 surviving oriented claims were excluded by certified finite
statements of the above kind, together with Farkas certificates (two independent checkers) for the 6,420 claims the LP
rows now exclude and a coverage checker in the package's format, the bound would become 76. None of that is done; the
bound stands at 75.

## 7. Statements and labels

| statement | label |
|---|---|
| H1: cap(h) <= 4, histograms, refinement by representation count | [finite-checked] (`hub.py`; second method; M and M^T) |
| Lemma H1 / row HUB `u_i <= 4 + q - A` | [proved] (Lemmas 4.1, 4.4, 4.5, 4.6; F2-F4; H1) |
| HUB case split is exhaustive and each case certifiable | [proved] |
| HUB effect 1,313 -> 1,256 / 681 -> 585; linear 1,307 / 676 | [measured] |
| Lemma O1 (two outputs per full helper, distinct, in the triples) | [proved] (Lemma 1.1, N1) |
| flow-feasible maximal independent sets exist (10 for M, 14 for M^T) | [finite-checked] (lower bounds on counts; existence exact) |
| C(m) for m <= 5; lower bounds for m >= 6; overlap histograms; admissible values | [finite-checked] (exact where marked) |
| boundary-degree row `cover(S) >= 9 n_3 + 64 - sum_B d_v`; vacuous at G = 75 | [proved]; [derived] |
| label budget not sharpenable by counting (sharing possible) | [proved] |
| FM rank histograms, top tables; rows FM7/FM9 | [finite-checked]; [proved]; effect none [measured] |
| dark rows (L13d)-(L18d), occurrence budgets, y_2 decomposition, case split exhaustive | [proved] (PROOF proofs of L13-L18 with q_D kept, (3.2), Lemma 10.2) |
| DARK effect 1,256 -> 996 / 585 -> 381 | [measured] |
| 0 violations of every new fact / row on 1,264 phases; tightness | [measured] |
| two-phase identity on the eventual tail; sigma = 0 consequences | [derived] (PROOF Lemma 6.2 remark, Lemma 8.2, bridge (E)); not re-verified here |
| the two finite searches of section 6 decide the remaining families | [conjecture] (they are finite and necessary; whether they kill is open) |
| any bound beyond 75 | **not claimed** |

## 8. Files in `~/xs-campaigns/2026-11-07-sprint/qreal/`

`hub.py`, `hub.log`, `hub_cap_{M,Mt}.json` (H1); `qr_lp.py` (variants `Gstar`, `N1`, `HUB`, `HUBlin`, `DARK`/`DARKM`,
`FM`, `BDEG` (unused: needs exact C(m)), `INT`; modes `scan`, `vertex`), `run_scans.sh`, `run_dark.sh`, `run_final.sh`,
`run_vertices.sh`, `scan_hub.log`, `scan_dark.log`, `scan_final.log`, `scan_*_q0_g75.json`, `vertices_final.log`;
`fullsets.py` (definitions, flow), `fullsets2.py`, `count_only.py` (enumeration attempt, capped), `fullgeo.py`,
`fullgeo_{M,Mt}.log`, `fullsets_{M,Mt}.json`, `fullmet.py`, `fullmet.log`, `fullmet_{M,Mt}.json` (geometry);
`qr_circ.py`, `qr_circ.log`, `qr_circ.json` (316 circuits, 1,264 phases); `wait_geo.sh`, `run_after.sh`, `run_chain.sh`.