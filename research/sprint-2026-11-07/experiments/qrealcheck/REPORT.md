# Adversarial check of the qreal claims (H1, HUB, dark split, O1) — findings

qrealcheck agent, 2026-11-07 ~23:00-23:50 UTC. Read: `qcheck/REPORT.md`, `qreal/REPORT.md`, `qbound/REPORT.md`,
`lower-bound-proofs/mixcolumns-lb75/PROOF.md` (sections 1-4, 10, 12), `qreal/qr_lp.py`, `hub.py`, `qr_circ.py`, the
qreal logs and scan files, `qcheck/lp_indep.py`, `ff_check.py`, `circ_check.py`, the package's `lp_regen.py` and
`stress.Circuit`. Everything outside `qrealcheck/` was read only (the recount ran a verbatim copy of `qr_lp.py` whose
only change is the output directory, see `qr_lp_recount.diff`). One python process at a time under `nice -n 10`; total
compute about 14 minutes on a machine with load average 25.

## Verdicts

| claim | verdict |
|---|---|
| Finite fact H1: cap(h) <= 4 for every odd non-boundary h, both orientations; histograms; cap 4 only at 2-representation values | **CONFIRMED** by independent recomputation (`h1_check.py`): identical N(h) and cap histograms, all 128,068 / 177,412 per-value caps identical to `hub_cap_{M,Mt}.json`, kappa_0 = kappa_1 = 4 |
| Lemma H1: `u_i <= 4 + (q - A)` for every helper with r <= 2 | **CONFIRMED** (every step checked; uses Lemmas 4.1, 4.4, 4.5, 4.6 and H1 only) |
| HUB case split in `qr_lp.py` (A = q - d, d = 0..q-5, plus A <= 4): exhaustive, each case a valid relaxation | **CONFIRMED**; the refined integer split A = a, a = 0..q gives the same 585 keys |
| (L13d)-(L18d) with the q_D terms (-9d, -9d, -4d, -9d / -6d, -10d) | **CONFIRMED** (re-derived from Lemma 10.2 / (G*) and the per-label bounds of the (L13)-(L18) proofs) |
| bright/dark occurrence budgets, y2d / Fb / Fd, `y_2 - y2d <= C(q,2)`, (I') with multi-missing gates counted twice, d = q / d = 0 rows | **CONFIRMED** |
| dark split q_D = 0..q exhaustive; every case's system a relaxation of the true constraints | **CONFIRMED** |
| Lemma O1 (>= 2 distinct outputs per full helper, in its triples, distinct across full helpers) | **CONFIRMED** (proof checked; 92 full helpers on 384 phases define exactly 2 each, all distinct) |
| LP recount 1,256 (693 M, 563 M^T) / 585 keys and 996 (504, 492) / 381 keys | **REPRODUCED** with the unchanged `qr_lp.py` rows and, independently, with `lp_qrc.py`: identical survivor sets, identical (k, ell), identical key sets |
| 0 violations of the new rows on real circuits | **CONFIRMED** on 96 circuits / 384 phases with own code, strong per-label and per-helper forms included |

No gap and no counterexample was found in the mathematics. One substantive bookkeeping issue (sections 8-9): the
"keys" statistic (585 / 381) counts only the 1,134 baseline keys; the final scan actually rests on **1,377
load-bearing LP-feasible keys** (264 of them with q <= 3, against the "18" of qreal section 6), and two of the
configurations named there lie outside the 381. Cosmetic: `run_final.sh` has a mangled `$k` (the vertices in
`vertices_final.log` come from `run_vertices.sh`, which is fine). No lower bound beyond 75 is claimed by qreal and
none is confirmed here.

## 1. Definitions (as used by PROOF.md / qreal and by my scripts)

Boundary B: the 32 unit vectors and the 32 rows of M (orientation M) or columns of M (M^T), read from
`circuits/aes-mixcolumns/aes-mixcolumns.mat.txt` (rows of weight 5/7, columns 5/11; identical to the package's
`stress.BOUNDARY`). *Boundary-pair value*: XOR of two distinct boundary masks (2,016 distinct values, F2).
*Full value*: an odd value with exactly three boundary-triple representations (F3/F4: 80 for M, 112 for M^T); a full
helper (r = 3) has a full value as mask (Lemma 4.4 + F3). *Jointly independent* (set S of full values): the 3|S| formal
vectors H_f + T (T over the three triples of f, H_f a coordinate private to f) are linearly independent, which is what
Lemma 4.4 forces for the full helpers of one circuit. N(h) = { f full : h + f is a pair value }; cap(h) = largest
jointly independent subset of N(h). Anchored (r >= 1), full (r = 3), bright/dark missing label (has / has not an H-B
edge at an anchored helper), q_D, h_0, U_0, D_0 = U_0 - h_0, kind-0 / kind-1 / y_2 even+even gates, k_l = dim((K_l + J)/J)
with J as in F9 (dim 24 for M, 28 for M^T; rho = 32 - dim J = 8 / 4), all exactly as in PROOF.md and qbound.
y2d = even+even gates whose single missing signal is dark, y2m = y_2 - y2d = gates with >= 2 missing signals.

## 2. (1) Finite fact H1 — independent recomputation (`h1_check.py`, `h1_check.log`, `h1_cap_{M,Mt}.json`, 16 s)

Method: N(h) for all h = f + p (f full, p pair value, h not in B); cap(h) by an exhaustive branch-and-bound DFS
over N(h) with an incremental GF(2) basis on the 3|S| relation vectors with explicit helper coordinates (not hub.py's
six-set-line shortcut, whose equivalence with the 3|S| notion I also tested: 0 mismatches on 3,000 random subsets);
second method: for every h with |N(h)| > cap(h) all subsets of size cap(h) + 1 are dependent (12,968 / 18,068 values
tested, 0 failures); every witness re-verified (rank, pairwise non-adjacency = F4, distinct pairs h + f).

| | M | M^T |
|---|---|---|
| odd non-boundary h with N(h) nonempty | 128,068 | 177,412 |
| N(h) histogram | 1: 114,060; 2: 1,280; 3: 10,992; 4: 444; 5: 100; 6: 672; 8: 260; 9: 160; 11: 88; 12: 4; 15: 8 | 1: 157,472; 2: 2,352; 3: 14,432; 4: 892; 5: 192; 6: 1,344; 8: 308; 9: 224; 11: 172; 12: 4; 15: 20 |
| cap histogram, all h | 1: 125,128; 2: 2,840; 3: 92; 4: 8 | 1: 172,060; 2: 5,156; 3: 176; 4: 20 |
| cap histogram, triple values | 1: 10,984; 2: 1,496; 3: 92; 4: 8 | 1: 14,236; 2: 2,708; 3: 176; 4: 20 |
| max cap by number of triple representations of h: 0 / 1 / 2 / 3 | 2 / 2 / 4 / 2 | 2 / 2 / 4 / 2 |
| kappa_0, kappa_1 | 4, 4 | 4, 4 |

Identical to qreal 1.1 in every entry; all per-value caps agree with `hub_cap_{M,Mt}.json` (0 differences). The eight M
values of cap 4 are 0x404040, 0x808080, 0x40004040, 0x40400040, 0x40404000, 0x80008080, 0x80800080, 0x80808000 (qreal's
0x80800080 among them); M^T has 20. Values with cap > 2 that are not 2-representation values: none. **CONFIRMED.**

## 3. (2) Lemma H1 and the HUB row

**Proof, step by step.** Let i have r_i <= 2 and let l be a missing label at i (edge i-b) with an H-B edge f-c at a
full helper f. (a) h_i + b = l = f + c, so h_i + f = b + c; b != c since b = c would give h_i = f, two distinct signals
with one mask (Lemma 1.1); so h_i + f is a pair value and f is in N(h_i) (f's mask is a full value by Lemma 4.4 + F3;
h_i is odd and not in B). (b) Two distinct missing labels at i cannot both meet the same f: i and f would carry two
common missing labels on H-B edges, against Lemma 4.6 (i != f since r_i < 3). (c) The full helpers met are therefore in
bijection with an independent subset of N(h_i) (Lemma 4.4 gives independence of all represented relations of the
circuit, in particular of this subfamily), of size <= cap(h_i) <= 4 (H1). (d) Every missing label meets at most one full
helper (Lemma 4.5), and no full helper carries one label twice (matching, Lemma 4.1), so A = sum_{r=3} u_i is exactly
the number of labels with an H-B edge at a full helper; the other missing labels at i are among the q - A remaining
ones. Hence u_i <= cap(h_i) + (q - A) <= 4 + (q - A). Needs normalization and F2-F4 only. **CONFIRMED.**

**Case split (`qr_lp.py cases()/build()`).** A ranges over 0..q (L6). For q <= 4 the row is vacuous (u <= q <= 4 + q - A)
and no split is made. For q >= 5 the cases are A = q - d, d = 0..q-5 (i.e. A = 5..q; `range(0, q - KAPPA)`), each adding
the equality `sum_{r=3} u n = q - d` and deleting every column (r < 3, u > 4 + d), and the case A <= 4, which adds the
row `sum_{r=3} u n <= 4` and deletes nothing (vacuous bound). Union of cases = {0..q}: exhaustive. In the case
A = q - d the true phase satisfies the equality and has no helper of a deleted type; in the case A <= 4 it satisfies the
row: each case's system is the base system plus rows valid for that case, i.e. a relaxation. A key is declared
infeasible only when all q - 3 cases are LP-infeasible, which is the correct disjunction. The DARK pre-check in
`feasible()` (hub cases without the dark rows and columns) is a valid shortcut (projection of the full system). The
'A <= 4' case admits fractional A; my integer refinement A = a, a = 0..q (variant `HUBX`) leaves the same 585 keys, so
nothing is lost there. The linear aggregate `HUBlin` is a valid consequence (each non-full-met label at a non-full
helper is an occurrence of one of the q - A labels, each with <= 4 + 2 f_l occurrences) and weaker, as stated.

## 4. (3) The dark-label split

**(L13d)-(L18d).** With dk = sum_bright k_l, (G*) with the F9 space J (qbound proved (G*) for every J containing R_6)
gives dk >= rho - y_2 - z - D_0 + q_D. At a dark label W_l = Z_l = A_l = Y_l = 0 (its H-B-incident helpers have r = 0;
full helpers are anchored; kind-1 labels are bright by definition), so W, Z, A, y_1 are sums over the q - q_D bright
labels. Per bright label: W_l + Y_l <= rank(C_l) (L7*) <= 7 - 2k_l (F9); W_l + Y_l + A_l + 2k_l <= 7 + ex_l with
sum ex_l <= eps (A_l = 1 forces k_l = 0 by F10 and rank <= 6 except F11's four M labels, at most two met at once);
Z_l + k_l <= 3 (proof of (L15)); the charging argument of the (L17) proof gives Z + E + 3 n_act <= 3(q - q_D) with
n_act >= dk/2 (M, k_l <= 2) or >= dk (M^T); for M^T W_l + A_l + 3k_l <= 7. Summing and substituting the lower bound on
dk (its coefficient is negative, so substitution is valid):

    W + y_1 <= 7(q-d) - 2dk          =>  W + y_1 - 2D_0 <= 2y_2 + 2z + 7q - 2rho - 9d
    W + A + y_1 <= 7(q-d) + eps - 2dk =>  W + A + y_1 - 2D_0 <= 2y_2 + 2z + 7q - 2rho + eps - 9d
    Z <= 3(q-d) - dk                 =>  Z - D_0 <= y_2 + z + 3q - rho - 4d
    M:  2Z + 2E + 3dk <= 6(q-d)      =>  2Z + 2E - 3D_0 <= 3y_2 + 3z + 6q - 24 - 9d
    Mt: Z + E + 3dk <= 3(q-d)        =>  Z + E - 3D_0 <= 3y_2 + 3z + 3q - 12 - 6d
    Mt: W + A + 3dk <= 7(q-d)        =>  W + A - 3D_0 <= 3y_2 + 3z + 7q - 12 - 10d

exactly the coefficients claimed and implemented (`dark_rows()`: constants `Yc(.) = 0` with aux `y2: -2/-1/-3`,
`y1: +1` in L13d/L14d). PROOF.md's own proofs already carry these q_D terms and drop them only in the last line, so
the re-derivation is a one-line change per row. **CONFIRMED.** ((L18d) could carry `+ y_1` as well — qcheck's remark —
still not claimed.)

**Occurrence budgets.** A missing label l occurs in exactly d_l + 1 gate equations (defining gate + d_l uses, no
terminal), and d_l + 1 <= 4 + 2f_l by (3.2); the equations containing an even signal have two odd signals (an edge of
label l) or none (an even+even gate), so U_l + V_l + ee_l = d_l + 1 (verified per label on every phase).
(i) every bright label has an H-B edge at an anchored helper: sum_{r>=1} u n >= q - d. (ii) H-B edges of anchored
helpers with missing labels and kind-1 gates sit at bright labels: sum_{r>=1} u n + y_1 <= sum_bright (4 + 2f_l) =
4(q - d) + 2Fb. (iii) y2d <= sum_dark (d_l + 1) <= 4d + 2Fd. (iv) Fb + Fd + sum f_min n <= Fb + Fd + F_H <= F (bright
labels, dark labels, helpers are disjoint signal sets). (v) y2d <= y_2 by definition. (vi) y2m <= C(q, 2): two gate
equations sharing two signals are equal (the third is their XOR) and two gates with one equation are excluded by
normalization (Lemma 4.1's argument), so a pair of missing labels lies in at most one gate; map each y2m gate to one of
its pairs, injective. (vii) sum_l ee_l = sum_gates #(missing signals) >= y_1 + y2d + 2 y2m, so with sum_l U_l = U:
y_1 + y2d + 2y2m + U <= 4q + 2F_miss <= 4q + 2(F - F_H); replacing F_H by sum f_min n <= F_H weakens it; with
y2m = y_2 - y2d this is `y_1 + 2y_2 - y2d + U + 2 sum f_min n <= 4q + 2F` as implemented. (viii) d = q: no bright label,
Fb = 0; d = 0: Fd = y2d = 0. All **CONFIRMED**; the LP rows match these statements coefficient by coefficient.

**Split.** q_D is an integer in 0..q; `cases()` enumerates d = 0..q for both orientations under `DARKM` (the scan used
`GstarN1HUBDARKM`); each case adds rows valid when q_D = d exactly, so the disjunction is exhaustive and each case is a
relaxation. Combined with HUB: at most (q - 3)(q + 1) LPs per key, as stated. The q = 1 reasoning of qreal 4.1 checks
out: d = 0 forces y2d = 0 and y2m <= 0, so y_2 = 0, and (L17Td) reads 0 <= Z + E - 3D_0 <= 3z - 9 (D_0 <= 0 since u <= 1);
d = 1 forces Fb = 0, hence sum_{r>=1} u n = y_1 = 0, and (L15d) gives y_2 + z + D_0 >= 5. Every q = 1 key with
y + z <= 4 and z <= 2 is dead; the two survivors (18,1,1,1,4,Mt), (19,0,0,1,5,Mt) satisfy the rule (`analyze.py`).

## 5. (4) Lemma O1

The gate of a represented edge f-a_j has equation {f, a_j, l_j}; its result is one of the three. f is the result of
exactly one gate, so at most one of f's three represented edges is its defining gate. If the result is a_j, a boundary
signal that is a gate result is an output (inputs are not results). If the result is l_j, the B-B gate {b_j, c_j, l_j}
of the represented label l_j has a result other than l_j (one producer per signal), hence b_j or c_j, an output in
P_{l_j}. Both outputs lie in T_j = {a_j, b_j, c_j}. Distinctness: outputs are results of gates, so distinct gates give
distinct outputs; {f, a_j, l_j} are distinct gates for distinct (f, j) (the helper identifies f, a_j identifies j);
{b_j, c_j, l_j} are distinct for distinct labels, and the represented labels of all full helpers are pairwise distinct
(N1, confirmed by qcheck); a gate with a helper operand differs from a gate with two boundary operands. **CONFIRMED.**
Circuits: 92 full helpers on 384 phases, each defines exactly 2 outputs, all distinct, each in its triple (own code).
O1 enters no LP row; the flow/assignment consequence is a finite fact I did not re-run (not asked).

## 6. (5) LP recount and independent implementation

Recount with the unchanged rows (`qr_lp_recount.py` = `qreal/qr_lp.py` with only the output directory changed,
`qr_lp_recount.log`): `GstarN1HUB`: survivors **1,256 (M 693, M^T 563)**, 585 of the 1,134 baseline keys still
feasible (by q 1:57 2:30 3:57 4:72 5:197 6:104 7:15 8:51 10:2), 100 s; `GstarN1HUBDARKM`: survivors **996 (504, 492)**,
**381** keys (1:2 2:2 3:14 4:54 5:163 6:93 7:11 8:41 10:1), shortfall 0/1/2/3 = 511/337/109/39, 150 s. Survivor sets and
key sets identical to `qreal/scan_*.json` (symmetric differences 0).

Independent implementation `lp_qrc.py` (base rows from qcheck's `lp_indep.py`, HUB / HUBX / DARK rows written from
the statements above as column dictionaries, own case enumeration): keys `GstarN1HUB` 585, `GstarN1HUBX` 585,
`GstarN1HUBDARK` 381, `GstarN1HUBXDARK` 381, each set identical to qreal's; full scans (`lp_qrc_scan.log`) 1,256 and 996
survivors with identical (state, orientation) sets and identical bounds (k, ell) on every survivor. By q <= 3 the
381 keys are exactly the 18 listed in qreal section 6 (`analyze.py`); (12,5,5,2,3,M) and (10,6,6,6,0,M) are infeasible.

## 7. (6) Circuit re-check (`circ_qrc.py`, `circ_qrc.log`, `circ_qrc.json`, 14 s)

96 circuits (13 package controls, 3 repo circuits, 40 real 88s from `bridge/profiles.json` spread over the list with the
`ymax` reconstruction, 40 random-order reconstructions of 20 of them), 4 orbit steps each: 384 phases (192 per
orientation), q = 7..16. Own odd graph, labels, types, bright/dark, kinds, adjoints and f_v (cross-checked against
`analyse()`), own cap(h) by DFS for the actual helper masks, own J of F9 and k_l. Checked: per helper
#full-met labels <= cap(h_i) <= 4 and u_i <= 4 + q - A (strong and LP forms); O1 per full helper; per label
U_l + V_l + ee_l = d_l + 1 <= 4 + 2f_l, bright labels have an anchored H-B edge, UA_l + Y_l <= 4 + 2f_l, W_l + Y_l <=
rank(C_l) <= 7 - 2k_l, Z_l + k_l <= 3, dark labels have UA_l = Y_l = 0; no pair of missing labels in two gates; the
aggregate rows (G*) with the F9 J, L13d, L14d, L15d, L17Md / L17Td, L18d, bright lower, bright capacity, dark capacity,
Fb + Fd + F_H <= F, y2m <= C(q,2), (I'), d = q / d = 0 rows, HUBlin. **0 violations, 0 assertion failures.**
Minimum slacks (M / M^T): L13d 24 / 0, L14d 26 / 0, L15d 14 / 0, L17 28 / 0, L18d - / 0, bright lower 2 / 0, bright
capacity 10 / 0, dark capacity 0 / 11, (I') 32 / 37, y2m 21 / 18, HUB 8 / 8 (A = 0 on every phase, so HUB is consistent
with but not exercised by circuits, as qreal says); (G*) with the F9 space is tight on 4 M and 18 M^T phases, so the
dark rows with their -9d / -6d terms are as sharp as the elimination allows. Real helper masks with cap(h) = 4 do occur
(M^T phases), with 0 full-met labels. Phase ranges agree with qreal 4.3 (q_D 0..8 M, 3..7 M^T; y2d <= 16; y2m <= 8).

## 8. Remarks and small discrepancies (no effect on the verdicts)

1. **The "keys" statistic is restricted to the 1,134 baseline keys.** `scan()` reports `keys_still_feasible` only
   among the baseline-feasible keys, but a stronger system pushes `first_s` to larger s and touches keys the baseline
   scan never evaluated. Two of the "surviving configurations" of qreal section 6, (13,4,4,4,1,M) and (12,4,4,5,1,Mt),
   are LP-feasible in the final system (their vertices are in `vertices_final.log`) but are neither in the 381 nor in
   the 1,134 (nor in the baseline's 15,742 infeasible keys: never touched); qreal's text treats the 381 as "the"
   surviving keys. The complete feasible and load-bearing key sets of the final scan are in section 9.
2. `run_final.sh` runs `qr_lp.py vertex GstarN1HUBDARKMFM` with the key arguments mangled away (the `$k` problem); the
   vertices actually come from `run_vertices.sh`, which is correct. Cosmetic.
3. (L18d) admits `+ y_1` for free (qcheck's remark, still unclaimed). The HUB 'A <= 4' case could be stated as the
   integer cases A = 0..4; no effect at G = 75.
4. qreal 1.1 says cap "at most 2 unless h is a repeated value with exactly two triple representations": confirmed
   literally (values with 0, 1 or 3 representations have cap <= 2). The LP uses 4 for every helper; since the LP has no
   handle on the representation count of a helper's mask, no sharpening is available at the type level.

## 9. Complete key sets of the final scan (`keys_full.py`, `keys_full.log`, `keys_full.json`)

A recording wrapper around my `feasible()` during the full `GstarN1HUBDARK` scan (same 996 survivors). The scan touches
**37,795 keys; 1,661 are LP-feasible** (793 M, 868 M^T; by q 1:2 2:159 3:210 4:347 5:447 6:266 7:123 8:100 9:6 10:1),
of which only 329 are in the baseline list of 1,134 (the 381 of qreal are the baseline keys that are feasible whether
or not the final scan touches them; 52 of them are not touched at all). **Load-bearing keys** — feasible at s = k on
the even phase or at s = ell on the odd phase of a surviving claim, i.e. the configurations a 76 proof would actually
have to exclude — number **1,377** (654 M, 723 M^T; only 194 in the baseline list): by q 2:80 3:184 4:321 5:361 6:244
7:122 8:60 9:5; by z 0:655 1:418 2:203 3:75 4:21 5:5; by h 9:26 10:152 11:269 12:235 13:234 14:193 15:153 16:88 17:27;
by y 0:157 1:167 2:187 3:257 4:198 5:145 6:122 7:81 8:52 9:11. Consequences for qreal section 6: "remaining keys with
q <= 3 (18)" should read **264 load-bearing keys with q <= 3** (q = 2: 7 M + 73 M^T; q = 3: 21 M + 163 M^T, e.g.
(16,2,2,3,0,Mt), (15,0,0,3,3,Mt), (11,3,4,3,5,M)); no q = 1 key is load-bearing ((18,1,1,1,4,Mt) and (19,0,0,1,5,Mt) are
feasible but no survivor rests on them, so "the q = 1 cluster is gone" holds in the strong sense); (13,4,4,4,1,M) is
load-bearing; (12,4,4,5,1,Mt) is LP-feasible in isolation (its vertices are genuine) but is not touched by the scan and
bears no survivor. The survivor count 996 and every verdict above are unaffected; only the "keys" bookkeeping and the
"what remains" description of qreal section 6 are too narrow. (`keys_full.json` lists both sets.)

## 10. What a referee would still want

1. Farkas certificates for every case of every excluded key (up to (q-3)(q+1) per key for q >= 5), in the package
   format extended by the case rows (`A = q - d` as an equality, the deleted columns, the q_D-indexed constants), with
   two independent checkers and mutation tests; a coverage checker that enumerates the cases itself.
2. The HUB row is supported only by the finite fact and the lemma; no known circuit has a full helper with a missing
   H-B edge (A = 0 everywhere), so the row is untested by circuits. A synthetic normalized circuit with A >= 1 (or a
   proof that none exists at small q) would be worth having.
3. Lemma H1 and the dark rows written in package style (statement, family, the pivot order for (G*) with the F9 J,
   the per-label inequalities and their finite facts F9-F11), and the strong per-label forms added to `stress.py`.
4. The key statistic of remark 8.1 replaced by the load-bearing keys of the survivors (section 9).
5. Small-q evidence: q <= 6 never occurs in a known circuit; every surviving claim lives at q <= 10.
6. The integer oracle and the two finite searches of qreal section 6 remain unrun; nothing here moves the bound.

## Files in `~/xs-campaigns/2026-11-07-sprint/qrealcheck/`

`h1_check.py`, `h1_check.log`, `h1_cap_{M,Mt}.json` (H1); `lp_qrc.py`, `lp_qrc_keys.log`, `lp_qrc_keys2.log`,
`lp_qrc_keys_*.json`, `lp_qrc_scan.log`, `lp_qrc_scan_*.json` (independent LP); `qr_lp_recount.py`, `qr_lp_recount.diff`,
`qr_lp_recount.log`, `scan_GstarN1HUB_q0_g75.json`, `scan_GstarN1HUBDARKM_q0_g75.json` (recount); `circ_qrc.py`,
`circ_qrc.log`, `circ_qrc.json` (circuits); `analyze.py` (survivor statements); `keys_full.py`, `keys_full.log`,
`keys_full.json`; `run_all.sh`, `progress.log`.
