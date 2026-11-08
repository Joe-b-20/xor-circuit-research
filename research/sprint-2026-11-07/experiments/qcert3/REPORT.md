# qcert3: per-case certificates and proof addendum for the HUB2 (finite fact H2), PK and FM rows at G = 75

qcert3 agent, 2026-11-08 (about 50 minutes of wall-clock work, under 15 minutes of compute). Working directory
`~/xs-campaigns/2026-11-07-sprint/qcert3/`. The git repository, `lb76/pkg_copy/`, `qcert/`, `qcert2/`, `qreal/`,
`qrealcheck/`, `qhub/`, `qhubcheck/`, `qbound/` and `bridge/` were read only; the package programs `certify75.py` and
`lp_regen.py` were imported from the copy unchanged; the package `stress.py`, the bridge reconstruction and qreal's
H1 table were taken from qcert2's unmodified copies (`stress_pkg.py`, `profile_real_copy.py`, `hub_cap_{M,Mt}.json`).
One python process at a time under `nice -n 8` (load average about 29 from other campaigns throughout).

Labels on every claim: **[proved]** (written proof in `PROOF_ADDENDUM_3.md`, package lemmas and finite facts as black
boxes), **[finite-checked]** (computed exactly by a program named here), **[certified]** (exact integer certificate
checked by two independently written programs), **[measured]** (LP status or circuit statistics; never a premise),
**[read, not checked]** (package or earlier-report statement relied on as is).

**No lower bound beyond 75 is claimed. 789 of the 7,416 oriented claims at G = 75 remain open by LP status.**

---

## 0. Summary

1. `PROOF_ADDENDUM_3.md` (Addendum C) states and proves, in PROOF.md's notation: finite fact H2 stated exactly with its
   histograms and the enumeration it rests on (C.2); condition (C1) with the gate-equation family listed and the two
   pivot steps written out (C.3); Lemma H2 `r_i + m_i <= 3` (C.4); row HUB2 `u_i <= (3 - r_i) + (q - A)` with the
   exact case split `A = 2..q` / `A <= 1` (no split for q <= 1), its exhaustiveness and soundness (C.4); Lemma PK:
   PK4 `n_3 + n_4 <= 1` at q = 4 and PK5 `n_3 + 2 n_4 + 2 n_5 <= 2` at q = 5 with `n_j = #{u = j}`, derived from
   Lemma 4.6 / the premise of Lemma 10.4, and the qhub report's notation slip recorded (C.5); finite fact FM with its
   rank histograms and top tables, Lemma FM (rows FM7, FM9) with the chord linearisation (C.6); the case systems,
   Lemma C1 of Addendum B re-applied, the coverage (C.7); every package lemma and finite fact cited per statement (C.8).
   [proved] / [finite-checked]
2. `CERTIFICATES_CASES75_B3.json`: **4,950 exact integer Farkas certificates** at G = 75 for 2,471 keys, **2,925 of them
   per case** (each recording its hub case `A = a` / `A <= 1` and its dark case `q_D = d`): complete case coverage of
   **all 536 keys** that were LP-feasible under the batch-2 system -- the 381 baseline keys of qcert2 together with
   qrealcheck's complete list of 1,661 batch-2-feasible keys of its scan (union 1,713) -- and are infeasible under the
   full system, among them **all 265 keys of the baseline 381 -> 116 reduction**; 14,312 leaf cases; and complete
   coverage of **all 207 oriented claims** (88 with even phase M, 119 with M^T) that the full system excludes and the
   batch-2 system does not (the **996 -> 789** reduction; 2,054 referenced keys, 27,153 leaf cases). Largest weighted
   right-hand side -1; 251,213 column coefficients checked; 0 uncertified (key, case) pairs. [certified]
3. Two checkers: the generator's own exact check (`gen_certs3.py`, package rows imported from `certify75.system`, all
   other rows appended) and `check_cases3.py` (every row constant and coefficient written out by hand column by column,
   standard library only, its own case tree, pinned expected counts). `crosscheck3.py` shows the two system definitions
   are identical matrices on all **24,790 (key, case) nodes** (79,835,060 coefficients) of the killed keys and of the
   keys with case certificates, and that every key and claim set equals the qcert2 / qreal / qrealcheck / qhub /
   qhubcheck files, with identical (k, l) on every survivor. [certified] / [finite-checked]
4. Mutation tests (`mutate3.py`, all 4,950 certificates): 28,530 negated multipliers, 348 dropped case certificates
   and 207 dropped referenced certificates all rejected; 211 of 28,530 zeroed and 10,339 of 28,530 incremented
   multipliers survive, each re-verified as a valid certificate; weakening the HUB2 column deletion to Lemma H1's
   rejects 1,050 of the 2,361 certificates in a case `A = a` (they genuinely rest on the sharper capacity). [finite-checked]
5. `stress_ext3.py` (extends qcert2's `stress_ext2.py`, originals untouched): H2, HUB2, PK4/PK5/L23, FM7/FM9 with their
   per-helper and per-label strong forms on the 13 controls + 303 real circuits, 4 orbit steps each: **1,264 phases, 0
   violations**; `cap_{R_i}(h_i)` recomputed by exhaustive search for all 20,745 non-full helpers met (1,077 distinct
   (mask, R) pairs) and equal to qhub's H2 table in every case; `A = 0` and `m_i = 0` on every phase, so H2 / HUB2 are
   consistent with but not exercised by circuits; on qhub's **synthetic maximal configurations** (all 592 (M) + 1,296
   (M^T) maximal (h, R, S) at the attaining hub values, re-enumerated and equal in number to qhubcheck's, plus the
   nine explicit witnesses) every check passes: gate equations independent, the two pivot steps return exactly
   F(h, R, S), H2 tight, HUB2 slack 0, its constant-(2 - r) mutation violated; the 1,152 / 2,880 H1 cap-4 witness sets
   are flagged. [finite-checked]
6. Finite facts recomputed here: FM (`fm_tab3.py`, own matrix parse and elimination: histograms and top tables identical
   to qreal's and qhubcheck's) and H2 (`h2_tab3.py`, fourth implementation: histograms identical, 0 violations, per-value
   capacities identical to qhub's table; section 3). [finite-checked]
7. Open: **789 claims (416 M, 373 M^T) remain open at G = 75 by LP status; no bound improvement.** [measured]

---

## 1. What is certified: exact counts

All numbers are printed by `check_cases3.py` (pinned in its `EXPECTED` dictionary), by `gen_certs3.py` (`gen_certs3.log`)
and by `stats3.py` (`s04_stats.out`); they agree.

| quantity | value | label |
|---|---:|---|
| admissible scalar states / oriented claims at G = 75 (PROOF.md section 11, rebuilt) | 3,708 / 7,416 | [finite-checked] |
| claims surviving the batch-2 system (package + batch 1 + HUB + DARK), read from qcert2 | 996 (504 M, 492 M^T) | [measured] = qcert2, qreal, qrealcheck, qhub's reproduction |
| claims surviving the full system (+ HUB2 in place of HUB, + PK4/PK5, + FM7/FM9), own scan | 789 (416 M, 373 M^T) | [measured] (LP) = qhub, qhubcheck (identical sets and (k, l)) |
| **newly excluded oriented claims, complete coverage** | **207** (88 M, 119 M^T) | **[certified]** |
| how they fail the final test: k + l > budget / k > S_e / l > S_o | 163 / 24 / 20 | [finite-checked] |
| their shortfall `budget - (k + l)` under batch-2 was 0 / 1 / 2 / 3 | 172 / 26 / 8 / 1 | [finite-checked] |
| which bound rose: even k / odd l | 131 / 76 | [finite-checked] |
| bounds (k, l) monotone (full >= batch-2) on all 7,416 claims | yes | [finite-checked] |
| baseline keys LP-feasible under batch-2 (qcert2 `surviving_keys` = qreal = qrealcheck) | 381 | [read, not checked] |
| **of them killed by the full system (complete case coverage)** | **265** (113 M, 152 M^T; by q 2: 2, 3: 13, 4: 21, 5: 152, 6: 62, 7: 4, 8: 11) | **[certified]** |
| of them surviving | 116 (81 M, 35 M^T; by q 1: 2, 3: 1, 4: 33, 5: 11, 6: 31, 7: 7, 8: 30, 10: 1) = qhub's and qhubcheck's lists | [measured] |
| complete batch-2-feasible key list of qrealcheck's scan (`keys_full.json`) | 1,661 (329 in the baseline 1,134) | [read, not checked] |
| union of the two lists | 1,713 | [finite-checked] |
| **of them killed by the full system (complete case coverage)** | **536** (261 M, 275 M^T; by q 2: 77, 3: 55, 4: 68, 5: 234, 6: 77, 7: 14, 8: 11) | **[certified]** |
| of them surviving | 1,177 | [measured] |
| keys the full scan touched / LP-feasible / load-bearing | 36,655 / 859 (419 M, 440 M^T) / 551 (271 M, 280 M^T; 53 in the baseline) | [measured] = qhubcheck |
| LP-feasible by q | 1: 5, 2: 107, 3: 106, 4: 299, 5: 82, 6: 121, 7: 64, 8: 70, 9: 4, 10: 1 | [measured] = qhubcheck |
| load-bearing by q | 1: 2, 2: 62, 3: 95, 4: 175, 5: 66, 6: 93, 7: 37, 8: 20, 9: 1 | [measured] = qhubcheck |
| killed keys whose certificates use hub cases only / dark cases only / both (case keys) | 272 / 0 / 76 | [finite-checked] |
| killed keys by certificate kind: case / flat (PK or FM row, no case) | 348 / 188 (baseline: 93 / 172) | [finite-checked] |
| leaf cases of the 536 killed keys (all covered) | 14,312 | [certified] |
| keys referenced by the coverage of the 207 claims | 2,054 (119 of them among the 536; 53 among the 265) | [finite-checked] |
| of which excluded by the package rows alone / by batch-1 / by a flat row / only by a case split | 1,615 / 220 / 43 / 176 | [certified] |
| leaf cases of the referenced keys (all covered) | 27,153 | [certified] |
| direct (Lemma 10.3) references / certificate references in the coverage | 401 / 3,353 | [finite-checked] |
| **keys with certificates / certificates** | **2,471 / 4,950** (1,615 package, 220 batch-1, 190 flat, 2,925 case) | **[certified]** |
| case certificates by case type: hub only / dark only / hub and dark | 1,611 / 14 / 1,300 | [certified] |
| hub cases certified: A = 2 / 3 / 4 / 5 / 6 / 7 / 8 / A <= 1 | 642 / 705 / 508 / 334 / 128 / 32 / 12 / 550 | [certified] |
| dark cases certified: q_D = 0 / 1 / 2 / 3 / 4 / 5 / 6 / 7 / 8 | 238 / 238 / 231 / 215 / 176 / 126 / 60 / 24 / 6 | [certified] |
| certificates using a PK row / an FM7 row (none needs an FM9 row) | 540 / 47 | [certified] |
| certificates per killed key (min / max / total; baseline total) | 1 / 35 / 2,481; 798 | |
| rows per certificate; multipliers total / nonzero / largest | 31-67; 222,030 / 28,530 / 7,935 | |
| column coefficients checked; largest weighted right-hand side | 251,213; -1 | [certified] |
| uncertified (key, case) pairs | 0 | |

**What "killed" means.** Each of the 536 keys has, for every leaf (hub case, dark case) of its tree, a certificate for
that leaf or for a case containing it (Lemma C1 of Addendum B, C.7); that the batch-2 rows leave it feasible is an LP
status of qcert2 / qrealcheck [read], never a premise. The kind "flat" is new in this batch: a certificate over the
(none, none) system using PK4, PK5 or an FM7 row; 188 of the 536 killed keys (172 of the 265 baseline ones) need no
case split once PK / FM are present -- these are the q = 4, 5 keys of qhub's "PK4/PK5 remove 21 M q = 4 keys and 27
q = 5 keys" together with the keys for which the HUB2 column deletions alone are not needed once PK5 is present (471
certificates use PK5, 69 PK4; both rows enter case certificates as well).

**Which rows the 3,115 case + flat certificates use** (nonzero multiplier): `HUB2 A = a` 1,485, `HUB2 A <= 1` 453,
(L15d) 871, PK5 471, N1 330, (I') 292, `Fd = y2d = 0` (d = 0) 238, (L17-M\*) 213, (I) 197, (L14d) 196, F budget (O4)
118, (L17Md) 103, dark capacity (O3) 95, (L12\*) 74, PK4 69, (L17-Mt\*) 59, (L13d) 54, `y2m <= C(q,2)` 48, FM7 47,
bright capacity (O2) 41, (L15\*) 36, `Fb = 0` (d = q) 35, (L20\*) 8, bright lower (O1) 6; (L18d), (L17Td), (L19\*) and the
FM9 chords are never used. Among the package rows the most used are L2 (3,079), L1 (2,997), L5 (2,236), L3 (1,874),
L17 (687), L6 (548), L16 (484), L23 (475 + 216). [finite-checked]

**On the claims' `lower_odd`.** As in the package driver, when the even phase alone kills a claim the odd bound is left
at its trivial value; the checker verifies both sides as stated and the final test. 20 of the 207 claims are killed on
the odd side alone (l > S_o), 24 on the even side alone.

---

## 2. Files and verification commands

| file | purpose |
|---|---|
| `PROOF_ADDENDUM_3.md` | the mathematics (sections C.1-C.9) |
| `CERTIFICATES_CASES75_B3.json` | `gates`, `hub_capacity`, `fm_hist`, `fm_top`, `fm_top3`, `system`, `cases`, `baseline_keys` (381), `batch2_feasible_keys` (1,713), `killed_keys` (536), `surviving_keys` (1,177), `baseline_killed_keys` (265), `baseline_surviving_keys` (116), `claims` (207: state, orientation, new `lower_even`/`lower_odd`, the batch-2 bounds), `certificates` (4,950: key, kind, `hub`, `dark`, weights), `uncertified` (empty), `counts` |
| `gen_certs3.py` | generator: the full-system scan with the package driver `lp_regen.run` (feasibility = primal LP per case), Farkas LP per case (`min sum lambda`, HiGHS), rationalization with `fractions`, lcm scaling, gcd reduction, exact integer re-check; needs numpy/scipy |
| `check_cases3.py` | **independent checker**: hand-written rows, pure integers, case tree and coverage rebuilt; pinned expected counts; writes `CHECKED_CASES75_B3.json` |
| `crosscheck3.py` | generator's and checker's matrices identical on every (key, case) node; key and claim sets equal the qcert2 / qreal / qrealcheck / qhub / qhubcheck files |
| `mutate3.py` | mutation tests of the checker; writes `mutate3.json` |
| `stress_ext3.py` | rows and strong forms on 13 controls + 303 real circuits and on the synthetic maximal configurations; writes `stress_ext3.json` |
| `fm_tab3.py`, `h2_tab3.py` | own recomputations of finite facts FM and H2; write `fm_tab3.json`, `h2_tab3.json`; logs `s02_fm.out`, `h2_tab3.log` |
| `scan_cases3.json` | all 7,416 claims with (k, l, dead) under the batch-2 (qcert2) and the full system; the 996 and 789 survivor lists with (k, l) |
| `keysfull3.json` | the complete key bookkeeping of the scan: 36,655 touched, the 859 LP-feasible and 551 load-bearing keys |
| `stats3.py`, `s04_stats.out` | statistics for this report |
| `stress_pkg.py`, `profile_real_copy.py`, `hub_cap_{M,Mt}.json`, `check_cases75_b2_copy.py` | unmodified copies (package `stress.py`, bridge reconstruction, qreal's H1 table, qcert2's checker, from which the hand-written package / batch-1 / DARK rows are reused verbatim) |
| `run_all.sh`, `run_all.log` | the complete check and its output; `s01_gen.out`, `s02_*.out`, `s03_stress.out` the drivers' outputs actually run |
| `SHA256SUMS.txt` | hashes of the static deliverables (not of the files the checks rewrite) |

**Commands** (from `qcert3/`; standard library suffices for everything except regeneration, `crosscheck3.py` and
`stress_ext3.py`, which import the package copy; measured times on the loaded machine, `run_all.log`):

```sh
python3 check_cases3.py CERTIFICATES_CASES75_B3.json   # 8 s    -> "expected counts match ... INDEPENDENT CHECK PASSED"
python3 fm_tab3.py                                      # 1 s    -> "FM TABLES RECOMPUTED: identical to qreal and qhubcheck ..."
python3 crosscheck3.py                                  # 88 s   -> "systems identical on 24790 (key, case) nodes ... CROSSCHECK PASSED"
python3 mutate3.py 1                                    # 87 s   -> "MUTATION TEST PASSED"
python3 stress_ext3.py                                  # 40 s   -> "STRESS EXT3 PASSED: 316 circuits, 1264 phases, 0 violations ..."
python3 h2_tab3.py                                      # 29 s -> "H2 RECOMPUTED: histograms identical ..."
sha256sum -c SHA256SUMS.txt
sh run_all.sh                                           # all of the above except h2_tab3.py, ends with "QCERT3 ALL CHECKS PASSED"
python3 gen_certs3.py                                   # regeneration (numpy + scipy), 183 s: full scan 123 s, 2,471 keys certified in 50 s
```

**The case systems and the two code paths.** For a key and a case (hub, dark) the system has the package rows
(`certify75.system`, unchanged), the batch-1 rows of qcert (same text and order), the flat batch-3 rows ([q = 4: PK4]
[q = 5: PK5], then the chord rows FM7(a0), FM9(a0) for a0 = 0..q-1), the hub rows (`A = a` as two inequalities with the
columns `r <= 2, u > 3 - r + q - a` removed; or `A <= 1`) and the dark rows of Addendum B with the extra columns y2d,
Fb, Fd (PROOF_ADDENDUM_3.md C.7). The generator builds rows as functions of the types and takes the FM tables from the
pinned histogram (asserted equal to qreal's and qhubcheck's files); the checker lists every constant and every column
literally, builds the FM chord constants from the pinned rank list in the derived form `7 (q - a0) + top(a0) + (7 - s) a0`
and the dark constants as `7(q-d) - 2(rho - z + d)` etc.; `crosscheck3.py` compares the matrices entry by entry. The
certificate tree of a key (`gen_certs3.certify_key`): package rows alone; else the batch-1 system; else the flat system;
else per hub case the system without dark rows, and only where that is feasible every dark case. Coverage
(`check_cases3.covered`) enumerates every leaf of the tree independently of how the certificates were produced.

**Mutation tests** (`mutate3.py 1`, 87 s, every certificate):

| mutation | count | rejected | note |
|---|---:|---:|---|
| negate one nonzero multiplier | 28,530 | 28,530 (100 %) | guaranteed (nonnegativity) |
| zero one nonzero multiplier | 28,530 | 28,319 (99.3 %) | the 211 survivors are valid certificates (redundant row); each re-verified |
| add 1 to one multiplier | 28,530 | 18,191 (63.8 %) | the 10,339 survivors are valid certificates; each re-verified |
| check against a neighbouring key (q+1, z+1, other orientation, h+1), same case | 19,800 | 16,018 (80.9 %) | |
| check against a neighbouring case (q_D +- 1 with the same row count; A +- 1; A = 2 <-> A <= 1) | 6,030 | 2,547 (42.2 %) | survivors are valid certificates of the neighbouring case by construction of the check |
| row constant +1 on one used row (checker's system) | 4,950 | 1,583 (32.0 %) | rejected iff the weighted right side reaches 0 |
| flip the sign of one used coefficient (checker's system) | 4,898 | 3,473 (70.9 %) | rejected iff a column sum turns negative |
| HUB2 column deletion weakened to Lemma H1's (`u > 4 + q - a`), certificate re-checked over the larger column set | 2,361 | 1,050 (44.5 %) | the rejected ones rest on H2's sharper capacity |
| PK4 / PK5 constant + 1 | 540 | 294 (54.4 %) | |
| FM7 chord constants + 1 (the finite fact weakened by one rank) | 47 | 5 (10.6 %) | FM7 is nearly redundant with (L7\*) + L6 |
| drop one case certificate of a killed key | 348 | 348 (100 %) | guaranteed (a leaf becomes uncovered: the tree has no redundant node) |
| drop one referenced certificate from a claim's coverage | 207 | 207 (100 %) | guaranteed (uncovered key) |
| claim `lower_even - 1` / `lower_odd - 1` | 207 / 207 | 187 / 207 | rejected iff the final test fails (20 claims hold by the odd side) |
| claim `lower_even + 1` | 207 | 207 (100 %) | a key without complete coverage becomes referenced |

Every mutation the checker accepts was re-verified to be a genuine certificate / genuine coverage; every mutation that
must be rejected was rejected.

---

## 3. Finite facts recomputed; stress test of the rows; synthetic configurations [finite-checked]

**Finite fact FM (`fm_tab3.py`, 1 s per orientation).** Own matrix parse from `circuits/aes-mixcolumns/aes-mixcolumns.mat.txt`,
own fully-reduced GF(2) elimination, forms over all 2,016 pairs and 635,376 4-subsets: F3 histograms 40,704 / 360 / 80
and 40,320 / 504 / 112; 80 / 112 full values; 4,640 / 6,496 distinct labels f + c; rank(C_l) histograms
{3: 3,696, 4: 692, 5: 140, 6: 108, 7: 4} (M) and {3: 4,960, 4: 1,176, 5: 144, 6: 216} (M^T); the three forms T (+/-) {c}
of f verified present with rank-2 differences at every (f, c); top = 0, 7, 14, 21, 28, 34, 40, ... (M), 6A (M^T),
top3 = 3A; per full value 12-23 labels of rank >= 4. Identical to `qreal/fullmet_{M,Mt}.json` and
`qhubcheck/fm_tab_{M,Mt}.json`.

**Finite fact H2 (`h2_tab3.py`, 29 s).** Fourth implementation (after qhub's `hub2.py`, `hub2_check.py` and qhubcheck's
`h2_check.py`): own boundary parse, N(h) from the pair values, depth-first extension of S with the rank recomputed from
scratch at every node by the fully reduced elimination of `fm_tab3.py` (no incremental basis, no undo, no size cap).
Result (`h2_tab3.log`, 12 s for M, 17 s for M^T): |N(h)| histograms as in B.2; cap_r histograms M {1: 126,412, 2: 1,648,
3: 8} / {0: 11,392, 1: 1,124, 2: 64} / {0: 428, 1: 12} and M^T {1: 174,320, 2: 3,072, 3: 20} / {0: 15,216, 1: 1,804,
2: 120} / {0: 592, 1: 24} for r = 0 / 1 / 2, identical to the qhub / qhubcheck tables; attaining counts 8 / 64 / 12 and
20 / 120 / 24; **0 violations of cap_r <= 3 - r**; H1's histogram {1: 125,128, 2: 2,840, 3: 92, 4: 8} / {1: 172,060,
2: 5,156, 3: 176, 4: 20} reproduced with the 3|S| vectors alone; the per-value capacities identical to
`qhub/hub2_{M,Mt}.json` on all 141,088 (M) / 195,168 (M^T) pairs (r, h).

**Stress test (`stress_ext3.py`, 40 s).** Circuits: the 13 package controls and the 303 real circuits of
`bridge/profiles.json` (bridge reconstruction `reconstruct(values, 'ymax')`), orbit steps 0-3 with the package's
`Circuit`, `analyse`, `canonical_transpose`; the package's own rows re-asserted on every phase; everything of
`stress_ext2.py` re-evaluated (batch-1, HUB, DARK rows, per-label forms, O1, cap(h) of H1 by own search = table on 977
masks). 316 circuits, **1,264 phases** (316 raw M, 316 canonical M, 632 canonical M^T), q = 7..16, **0 violations**.
New in this batch, per phase: m_i for every helper (full-met labels at i met by a full helper other than i), H2
`3 - r_i - m_i >= 0`, H2 strong form `cap_{R_i}(h_i) - m_i >= 0` with cap recomputed by exhaustive search over S for the
helper's actual represented triples R_i (20,745 helper checks, 1,077 distinct (mask, R) pairs; every value <= qhub's
table entry, and equal to it in all 20,745 cases), HUB2 `(3 - r_i) + (q - A) - u_i`, PK4 / PK5 / L23 by u-histogram,
FM7 / FM9 with the phase's A and all 2q chord rows, per label `Z_l <= min(3, rank(C_l) - 1)` (bright) and
`rank(C_l) >= 3` at full-met labels, Lemma 4.6 as a pairwise check.

Minimum slack (controls / real; raw M, canonical M, canonical M^T), selected rows:

| row | ctrl raw M | ctrl can. M | ctrl can. M^T | real raw M | real can. M | real can. M^T |
|---|---:|---:|---:|---:|---:|---:|
| H2 `3 - r_i - m_i` (0 at every full helper) | 0 | 0 | 0 | 0 | 0 | 0 |
| H2 strong `cap_{R_i}(h_i) - m_i` (0 at hubs of capacity 0) | 0 | 0 | 0 | 0 | 0 | 0 |
| HUB2 `(3 - r) + q - A - u` | 7 | 11 | 7 | 7 | 10 | 10 |
| HUB (H1) `4 + q - A - u` | 8 | 13 | 8 | 10 | 12 | 11 |
| FM7 (= FM7 chords) / FM9 (= FM9 chords) | 30 / 19 | 50 / 30 | 49 / 21 | 24 / 15 | 45 / 24 | 47 / 21 |
| FM9 per label `min(3, rank - 1) - Z_l` | 0 | 0 | 0 | 0 | 0 | 0 |
| L23 (q = 7; 4 phases) | 12 | | 10 | 14 | | |
| N1 / (I) / G\*_J (batch 1, as in qcert2) | 18 / 32 / 0 | 23 / 44 / 0 | 26 / 41 / 0 | 20 / 35 / 1 | 23 / 44 / 2 | 23 / 42 / 0 |
| L13d / L14d / L15d (as in qcert2) | 25 / 27 / 15 | 24 / 26 / 14 | 0 / 0 / 0 | 24 / 26 / 15 | 26 / 28 / 16 | 10 / 10 / 4 |

Ranges: A = 0 on every phase, hence m_i = 0 at every helper and `hub_fullmet_max = 0`; the largest C1 capacity of an
unanchored helper met is 1 (M) / 2 (M^T) while H1's cap reaches 4; helpers with u >= 3 per phase at most 2; no phase has
q <= 6, so PK4 / PK5 are not exercised and L23 only at q = 7. The stress test is a positive control for the rows, not
evidence about the survivors.

**Synthetic maximal configurations (`stress_ext3.py`, part B, 2 s).** From qhub's `hub2_{M,Mt}.json` capacity table the
hub values attaining 3 - r (M: 8 / 64 / 12; M^T: 20 / 120 / 24 for r = 0 / 1 / 2) and, re-enumerated here, every maximal
(h, R, S) with |S| = 3 - r and F(h, R, S) independent: **M 192 / 352 / 48, M^T 480 / 720 / 96** (identical to qhubcheck's
`n_maximal_configs`), plus the nine explicit witnesses of qhub section 3.3. On each: membership (h odd, not in B, S in
N(h), R triples of h), F(h, R, S) independent of rank 4m + r; the gate equations of the local configuration (references,
represented H-B equations, the two missing H-B equations per full-met label) independent, their rank = #references + m +
rank F, and the two pivot steps of C.3 return exactly F(h, R, S); pairs P_f disjoint; full helpers pairwise non-adjacent;
labels distinct, even, and of rank >= 3 + r; Lemma H2 with equality; HUB2 at q = A = m with slack 0; the
constant-(2 - r) mutation violated: **1,897 configurations, all passed**. Mutation: all 1,152 (M) / 2,880 (M^T) H1 cap-4
witness sets (r = 0, m = 4) give a dependent C1 family and dependent gate equations and are flagged (r + m = 4 > 3).
Local configurations, not circuits.

---

## 4. What remains open

- **789 oriented claims (416 with even phase M, 373 with M^T) remain open at G = 75 by LP status [measured]; no
  bound improvement.** Their shortfall `budget - (k + l)` is 0 for 426, 1 for 270, 2 for 69, 3 for 24 claims; the
  survivor set and every (k, l) are identical to qhub's `scan_GstarN1HUB2DARKMFMPK_q0_g75.json` and qhubcheck's
  `lp_qhc_scan_GstarN1HUB2DARKPKFM.json` (`crosscheck3.py`).
- Of the 381 baseline keys, 116 remain LP-feasible (by q 1: 2, 3: 1, 4: 33, 5: 11, 6: 31, 7: 7, 8: 30, 10: 1; 81 M, 35
  M^T), identical to qhub's and qhubcheck's lists; over the complete scan 859 keys are LP-feasible and 551 load-bearing
  (53 of them in the baseline: qhub's "53"), identical to qhubcheck's `lp_qhc_keysfull_GstarN1HUB2DARKPKFM.json`.
  The structure of the survivors (hubs at the H2 limit with L5 / L23 / PK tight; the M q = 4, 6 blocks, the M^T q = 7-8
  small-h keys, the three q <= 3 keys) is qhub's section 6 [read, not checked here].
- Cumulative: 1,508 (package) -> 1,313 (batch 1, qcert) -> 996 (batch 2, qcert2) -> **789 (this batch)** oriented claims;
  195 + 317 + 207 = 719 of the 1,508 claims the package rows leave are now certified-excluded; 789 are not.
  Proposition 11.1's argument at G = 75 would need all of them.
- Not done: certificates for the 551 load-bearing keys (they are LP-feasible, so none exists under this system); the
  finite searches of qhub section 7; the integer oracle; a normalized circuit with A >= 1 or a proof that none exists at
  small q.

---

## 5. Trust ledger

**Relied on, not re-proved here [read, not checked]:**
- PROOF.md Lemmas 1.1, 1.2, 3.2/(3.2), 4.1-4.7, 10.1-10.4 and their proofs; in particular the proofs of (L7) and (L9)
  (the per-label forms E_l + T + B_b are independent in C_l; Z_l <= 3 through F7), which Lemma FM re-uses per label;
  Lemma 7.4 exactly where the package uses it (helper types with r + u + v >= 3).
- Addendum A (qcert): Lemma G\*, Lemma N1, (L7\*) per label (used by FM7), the kinds y_0, y_1, y_2, the batch-1 rows;
  Addendum B (qcert2): Lemmas D1, D2 and the DARK split (the dark rows are taken over unchanged), Lemma C1 (persistence),
  the coverage definition.
- Finite facts F2-F14 (package `finite_facts.py`; `verify_all.py` replayed by lb76). H1 is [finite-checked] by qreal,
  qrealcheck, qcert2 and here; H2 by qhub (two programs), qhubcheck and here; FM by qreal, qhubcheck and here.
- The scalar domain formulas of PROOF.md section 11 at G = 75 (lb76 report; the coverage checker applies them literally);
  the bridge reconstruction as a faithful gate list for the 303 real circuits; qcert2's 996 / 381 and qrealcheck's 1,661
  as the batch-2 LP status of the claims and keys (the sets, not the exclusions, are premises of the bookkeeping).

**Proved in the addendum [proved]:** condition (C1) (the gate-equation family and the two pivot steps); Lemma H2; row
HUB2 and the exhaustiveness and soundness of its split; Lemma PK (PK4, PK5); Lemma FM (FM7, FM9) and the chord
linearisation; Lemma C1 of Addendum B for the new case systems.

**Finite-checked here [finite-checked]:** finite fact FM (own program); finite fact H2 (own program: histograms,
attaining counts, per-value capacities); cap_{R_i}(h_i) for the 1,077 (mask, R) pairs met and cap(h) for the 977 masks;
the set identities 996 / 789 / 207, 381 / 116 / 265, 1,661 / 1,713 / 536, 859 / 551 with the qcert2, qreal, qrealcheck,
qhub and qhubcheck files; the identity of the two system definitions on 24,790 case nodes; the mutation statistics; the
zero-violation stress result; the 1,897 synthetic maximal configurations and the flagged cap-4 sets.

**Certified by the files [certified]:** for each of the 2,471 keys and each of its case nodes carrying a certificate, the
case system at G = 75 has no nonnegative real solution; for each of the 536 killed keys every leaf case is covered; for
each of the 207 claims every (q, z) below the stated k, l is excluded by (4.4), Lemma 10.3 or a covered key, and
`k > S_e or l > S_o or k + l > a + b + 2G - 192`.

**What follows on its own.** Granting the package lemmas and finite facts, Addenda A and B and the proofs of Addendum C:
no tail of the orbit at G = 75 has one of the 207 excluded (profile, orientation) pairs. Nothing about L(M) follows,
because 789 pairs remain.

---

## 6. Caveats

- As in the package, qcert and qcert2, the bounds k, l of the 207 claims were produced by the package driver with our LP
  feasibility; the checker verifies only the infeasible side and the final test. A claim's k, l could be larger than
  found, never smaller.
- The HUB2 case `A <= 1` admits fractional A; the integer refinement changes no key set at G = 75 (qhubcheck, variant
  HUB2X) and is not used. The capacity 3 - r of H2 is the finite fact as stated (independence of F(h, R, S) alone);
  the further conditions of the qhub report (O1 assignment, degree excess) enter no row.
- FM7 is nearly redundant at G = 75 (47 certificates use it; weakening its constant by one keeps 42 of them valid); it
  is kept because qhub's and qhubcheck's LPs carry it and one baseline key (9,6,8,7,0,M^T) dies only with it
  (qhubcheck section 5). FM9 coincides with (L9) and is never needed.
- LP solver status decides only which keys and cases to attempt and the kind label of a certificate; no exclusion rests
  on it. The largest multiplier (7,935) comes from the rationalization of one LP vertex; all multipliers are exact
  integers checked as such.
- The two text corrections of qhubcheck are carried into the addendum: PK5 is stated with n_j = #{u = j}; FM7 / FM9 are
  rows of the system (not "not applied") and load-bearing for one baseline key.

---

## 7. Labels, in one table

| statement | label |
|---|---|
| Condition (C1); Lemma H2; HUB2 split exhaustive and sound; Lemma PK; Lemma FM and the chord rows; Lemma C1 re-applied | [proved] (PROOF_ADDENDUM_3.md) |
| finite fact H2 (cap_r(h) <= 3 - r; histograms; attaining values) | [finite-checked] (qhub `hub2.py`, `hub2_check.py`; qhubcheck `h2_check.py`; here `h2_tab3.py`, `stress_ext3.py`) |
| finite fact FM (rank histograms of the labels f + c; top tables) | [finite-checked] (qreal `fullmet.py`; qhubcheck `fm_check.py`; here `fm_tab3.py`) |
| 4,950 certificates; case coverage of 536 keys (265 baseline) and 207 claims; largest rhs -1 | [certified] (`check_cases3.py`, `gen_certs3.py`) |
| the two system definitions coincide on 24,790 (key, case) nodes | [finite-checked] (`crosscheck3.py`) |
| 996 / 789 / 207 claims, 381 / 116 / 265 and 1,713 / 536 keys, 859 / 551 scan keys = the qcert2 / qreal / qrealcheck / qhub / qhubcheck sets | [finite-checked] (`crosscheck3.py`) |
| batch-2 rows alone leave the 536 keys and 207 claims feasible; 789 / 116 remain | [measured] (LP status) |
| 0 violations on 1,264 phases; C1 capacities = qhub table on 20,745 helpers; 1,897 synthetic configurations pass | [finite-checked] (positive control only) |
| package Lemmas 1.1-10.4, F2-F14, section 11 formulas at G = 75; Addenda A, B | [read, not checked] |
| any bound beyond 75 | **not claimed** |
