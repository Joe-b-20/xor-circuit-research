# qcert2: per-case certificates and proof addendum for the HUB and DARK splits at G = 75

qcert2 agent, 2026-11-07 (about 40 minutes of wall-clock work, under 6 minutes of compute). Working directory
`~/xs-campaigns/2026-11-07-sprint/qcert2/`. The git repository, `lb76/pkg_copy/`, `qcert/`, `qreal/`, `qrealcheck/`
and `qbound/` were read only; the package programs `certify75.py` and `lp_regen.py` were imported from the copy
unchanged; `stress.py`, the bridge's `profile_real.py` and qreal's `hub_cap_{M,Mt}.json` were copied into `qcert2/`
(`stress_pkg.py`, `profile_real_copy.py`, the two tables) and left unmodified. One python process at a time under
`nice -n 8` (the machine carried a load average of about 25 from other campaigns throughout).

Labels on every claim: **[proved]** (written proof in `PROOF_ADDENDUM_2.md`, package lemmas and finite facts as black
boxes), **[finite-checked]** (computed exactly by a program named here), **[certified]** (exact integer certificate
checked by two independently written programs), **[measured]** (LP status or circuit statistics; never a premise),
**[read, not checked]** (package or earlier-report statement relied on as is).

**No lower bound beyond 75 is claimed.** 996 of the 7,416 oriented claims at G = 75 remain open by LP status.

---

## 0. Summary

1. `PROOF_ADDENDUM_2.md` states and proves, in PROOF.md's notation and style: finite fact H1 stated exactly (B.2),
   Lemma H1 and the HUB case split with its exhaustiveness and soundness (B.2), Lemma D1 (the quotient rows (L13d)-(L18d)
   with the dark count retained, B.3), Lemma D2 (the occurrence budgets (O1)-(O7), B.4) and the dark-label split with
   its exhaustiveness (B.4), Lemma O1 (B.5), Lemma C1 (certificates persist under relaxation of the case) and the
   coverage definition (B.6), with every package lemma and finite fact cited per statement (B.7). [proved] / [finite-checked]
2. `CERTIFICATES_CASES75.json`: **4,523 exact integer Farkas certificates** at G = 75 for 2,460 keys, **2,497 of them
   per case** (each recording its hub case `A = a` / `A <= 4` and its dark case `q_D = d`): complete case coverage of
   **all 300 keys** that the batch-1 system leaves LP-feasible and the two splits exclude (the **681 -> 381** reduction;
   4,344 leaf cases), and complete coverage of **all 317 oriented claims** (220 with even phase M, 97 with M^T) that
   the two splits exclude and the batch-1 system does not (the **1,313 -> 996** reduction; 2,232 referenced keys,
   11,788 leaf cases). Largest weighted right-hand side -1; 192,917 column coefficients checked; 0 uncertified
   (key, case) pairs. [certified]
3. Two checkers: the generator's own exact check (package rows imported from `certify75.system`, case rows appended)
   and `check_cases75.py` (every row constant and coefficient written out by hand column by column, standard library
   only, the case tree enumerated independently, pinned expected counts). `crosscheck2.py` shows the two system
   definitions are identical matrices on all **23,593 (key, case) nodes** (50,459,644 coefficients) that the file and
   the coverage touch, and that every key and claim set equals the qbound / qreal / qrealcheck / qcert files. [certified]
4. Mutation tests (`mutate_cases.py`, all 4,523 certificates): 26,724 negated multipliers, 300 dropped case
   certificates and 317 dropped referenced certificates all rejected; 210 of 26,724 zeroed and 12,326 of 26,724
   incremented multipliers survive, each surviving vector re-verified as a valid certificate. [finite-checked]
5. `stress_ext2.py` (extends qcert's `stress_ext.py`, originals untouched): the batch-1, HUB and DARK rows with their
   per-label and per-helper strong forms and Lemma O1 on the 13 controls + 303 real circuits, 4 orbit steps each:
   **1,264 phases, 0 violations**; cap(h) recomputed by exhaustive search for all 977 distinct non-full helper masks met
   (20,745 helper checks) and identical to the H1 table; every one of the 324 full helpers met defines exactly 2 outputs
   (O1). The HUB row is consistent with but not exercised by circuits (A = 0 everywhere). [finite-checked]
6. `synthetic_hub.py`: synthetic **local helper configurations with A = 3** (192 for M at 8 hub values, 480 for M^T at
   20) on which the HUB row is exercised (slack 1) and its constant-2 mutation is violated; observation: A = 4 at one
   hub is never realizable (the gate equations of every cap-4 witness are dependent). Local configurations, not
   circuits. [finite-checked]
7. Open: **996 claims (504 M, 492 M^T) remain open at G = 75 by LP status; no bound improvement.** [measured]

---

## 1. What is certified: exact counts

All numbers are printed by `check_cases75.py` (pinned in its `EXPECTED` dictionary), by `gen_certs2.py` (`gen_certs2.log`)
and by `stats.py`; they agree.

| quantity | value | label |
|---|---:|---|
| admissible scalar states / oriented claims at G = 75 (PROOF.md section 11, rebuilt) | 3,708 / 7,416 | [finite-checked] |
| claims surviving the batch-1 system (package + qcert rows), reproduced | 1,313 (724 M, 589 M^T) | [measured] (LP) = qcert, qbound, qcheck |
| claims surviving batch-1 + HUB + DARK | 996 (504 M, 492 M^T) | [measured] (LP) = qreal, qrealcheck (identical sets and (k, l)) |
| **newly excluded oriented claims, complete coverage** | **317** (220 M, 97 M^T) | **[certified]** |
| how they fail the final test: k + l > budget / k > S_e / l > S_o | 260 / 43 / 14 | [finite-checked] |
| their shortfall `budget - (k + l)` under batch-1 was 0 / 1 / 2 | 260 / 36 / 21 | [finite-checked] |
| keys LP-feasible under batch-1 (qbound `scan_GstarN1` list, each re-found feasible) | 681 | [measured] |
| **of them killed by HUB + DARK (complete case coverage)** | **300** (204 M, 96 M^T; by q 1: 55, 2: 28, 3: 43, 4: 18, 5: 34, 6: 58, 7: 50, 8: 13, 10: 1) | **[certified]** |
| of them surviving | 381 (194 M, 187 M^T) = qreal's and qrealcheck's lists | [measured] |
| killed keys whose certificates use hub cases only / dark cases only / both | 96 / 144 / 60 | [finite-checked] |
| leaf cases of the 300 killed keys (all covered) | 4,344 | [certified] |
| keys referenced by the coverage of the 317 claims | 2,232 (72 of them among the 300) | [finite-checked] |
| of which excluded by the package rows alone / by batch-1 / only by a case split | 1,698 / 328 / 206 | [certified] |
| leaf cases of the referenced keys (all covered) | 11,788 | [certified] |
| direct (Lemma 10.3) references in the coverage | 620 | [finite-checked] |
| **keys with certificates / certificates** | **2,460 / 4,523** (1,698 package, 328 batch-1, 2,497 case) | **[certified]** |
| case certificates by case type: hub only / dark only / hub and dark | 428 / 876 / 1,193 | [certified] |
| hub cases certified: A = 5 / 6 / 7 / 8 / 9 / 10 / A <= 4 | 617 / 371 / 192 / 56 / 1 / 1 / 383 | [certified] |
| dark cases certified: q_D = 0 / 1 / 2 / 3 / 4 / 5 / 6 / 7 / 8 / 9 / 10 | 412 / 412 / 355 / 295 / 212 / 162 / 103 / 65 / 43 / 5 / 5 | [certified] |
| certificates per killed key (min / max / total) | 2 / 57 / 1,662 | |
| rows per certificate; multipliers total / nonzero / largest | 30-52; 172,294 / 26,724 / 25,002 | |
| column coefficients checked; largest weighted right-hand side | 192,917; -1 | [certified] |
| uncertified (key, case) pairs | 0 | |

**What "killed" means.** Each of the 300 keys has, for every leaf (hub case, dark case) of its tree, a certificate for
that leaf or for a case containing it (Lemma C1); that the batch-1 rows alone leave it feasible is an LP status
[measured], never a premise. The 134 further "case" keys lie outside the 681 list (the batch-1 scan stops at the first
feasible s of a claim and never visits them); they are needed for the coverage of the 317 claims.

**Which case rows the 2,497 case certificates use** (certificates with a nonzero multiplier on the row): (L15d) 1,136,
`Fd = y2d = 0` (d = 0) 412, (I') 372, `A = 5` 314, (L14d) 300, `A <= 4` 298, (L13d) 197, `y2m <= C(q,2)` 188, (L17Md)
182, F budget (O4) 181, `A = 6` 176, dark capacity (O3) 136, bright capacity (O2) 114, `Fb = 0` (d = q) 106, `A = 7` 64,
`A = 8` 32, bright lower (O1) 8, (L17Td) 3, `A = 9` 1, `A = 10` 1; (L18d) is never used. Among the batch-1 rows, N1 is
used by 868 certificates, (I) by 303, (L17-M\*) by 320. [finite-checked]

**On the claims' `lower_odd`.** As in the package driver, when the even phase alone kills a claim (k > S_e or k + l(h_o, V) > budget)
the odd bound is left at its trivial value l(h_o, V); the checker verifies both sides as stated (an empty coverage on
the odd side) and the final test. This is why 43 claims show a smaller `lower_odd` than under batch-1 while their k rose.

---

## 2. Files and verification commands

| file | purpose |
|---|---|
| `PROOF_ADDENDUM_2.md` | the mathematics (sections B.1-B.8) |
| `CERTIFICATES_CASES75.json` | `gates`, `kappa`, `system`, `cases`, `batch1_feasible_keys` (681), `killed_keys` (300), `surviving_keys` (381), `claims` (317: state, orientation, new `lower_even`/`lower_odd`, the batch-1 bounds), `certificates` (4,523: key, kind, `hub`, `dark`, weights), `uncertified` (empty), `counts` |
| `gen_certs2.py` | generator: two scans with the package driver `lp_regen.run` (feasibility = primal LP per case), Farkas LP per case (`min sum lambda`, HiGHS), rationalization with `fractions`, lcm scaling, gcd reduction, exact integer re-check; needs numpy/scipy |
| `check_cases75.py` | **independent checker**: hand-written rows, pure integers, case tree and coverage rebuilt; pinned expected counts; writes `CHECKED_CASES75.json` |
| `crosscheck2.py` | generator's and checker's matrices identical on every (key, case) node; key and claim sets equal the qbound / qreal / qrealcheck / qcert files |
| `mutate_cases.py` | mutation tests of the checker; writes `mutate_cases.json` |
| `stress_ext2.py` | rows and strong forms on 13 controls + 303 real circuits; writes `stress_ext2.json`, log `stress_ext2.log` |
| `synthetic_hub.py` | synthetic A >= 1 configurations; writes `synthetic_hub.json`, log `synthetic_hub.log` |
| `scan_cases75.json` | all 7,416 claims with (k, l, dead) under both systems; the 1,313 and 996 survivor lists |
| `stats.py`, `smoke.py` | statistics for this report; a smoke test of the generator on known keys |
| `stress_pkg.py`, `profile_real_copy.py`, `hub_cap_{M,Mt}.json` | unmodified copies of the package `stress.py`, the bridge reconstruction and qreal's H1 table |
| `run_all.sh`, `run_all.log` | the complete check and its output; `s00_setup.sh`, `s01_gen.out`, `s03_mutate.out` the drivers / outputs actually run |
| `SHA256SUMS.txt` | hashes of the static deliverables (not of the files the checks rewrite) |

**Commands** (from `qcert2/`; standard library suffices for everything except regeneration; measured times on the loaded machine):

```sh
python3 check_cases75.py CERTIFICATES_CASES75.json   # 3 s    -> "expected counts match ... INDEPENDENT CHECK PASSED"
python3 crosscheck2.py                               # 30 s   -> "systems identical on 23593 (key, case) nodes ... CROSSCHECK PASSED"
python3 mutate_cases.py 1                            # 24 s   -> "MUTATION TEST PASSED"
python3 stress_ext2.py                               # 36 s   -> "STRESS EXT2 PASSED: 316 circuits, 1264 phases, 0 violations ..."
python3 synthetic_hub.py                             # 12 s   -> "SYNTHETIC HUB CONTROL PASSED ..."
sha256sum -c SHA256SUMS.txt
sh run_all.sh                                        # all of the above, ends with "QCERT2 ALL CHECKS PASSED"
python3 gen_certs2.py                                # regeneration (numpy + scipy), 124 s: batch-1 scan 62 s, full scan 29 s (cached batch-1 LPs), 2,460 keys certified in 31 s
```

**The case systems and the two code paths.** For a key and a case (hub, dark) the system has the package rows
(`certify75.system`, unchanged), the batch-1 rows of qcert (same text and order), the hub rows (`A = a` as two
inequalities with the columns `r <= 2, u > 4 + q - a` removed; or `A <= 4`) and the dark rows ((L13d), (L14d), (L15d),
(L17Md) | (L17Td), (L18d), (O1), (O2), (O3), (O4), `y2d <= y2`, `y2 - y2d <= C(q,2)`, (O6), [`Fb = 0`], [`Fd + y2d = 0`])
with the extra columns y2d, Fb, Fd (PROOF_ADDENDUM_2.md B.6). The generator builds rows as functions of the types; the
checker lists every constant and every column literally and builds the dark constants in their derived form
`7(q-d) - 2(rho - z + d)` etc.; `crosscheck2.py` compares the matrices entry by entry. The certificate tree of a key
(`gen_certs2.certify_key`): package rows alone; else the batch-1 system; else per hub case the system without dark
rows, and only where that is feasible every dark case. Coverage (`check_cases75.covered`) enumerates every leaf of the
tree independently of how the certificates were produced.

**Mutation tests** (`mutate_cases.py 1`, 24 s, every certificate):

| mutation | count | rejected | note |
|---|---:|---:|---|
| negate one nonzero multiplier | 26,724 | 26,724 (100 %) | guaranteed (nonnegativity) |
| zero one nonzero multiplier | 26,724 | 26,514 (99.2 %) | the 210 survivors are valid certificates (redundant row); each re-verified |
| add 1 to one multiplier | 26,724 | 14,398 (53.9 %) | the 12,326 survivors are valid certificates; each re-verified |
| check against a neighbouring key (q+1, z+1, other orientation, h+1), same case | 18,092 | 13,336 (73.7 %) | |
| check against a neighbouring case (q_D +- 1 with the same row count; A +- 1; A = q <-> A <= 4) | 4,022 | 1,369 (34.0 %) | survivors are valid certificates of the neighbouring case by construction of the check |
| row constant +1 on one used row (checker's system) | 4,523 | 920 (20.3 %) | rejected iff the weighted right side reaches 0 |
| flip the sign of one used coefficient (checker's system) | 4,450 | 3,110 (69.9 %) | rejected iff a column sum turns negative |
| drop one case certificate of a killed key | 300 | 300 (100 %) | guaranteed (a leaf becomes uncovered: the tree has no redundant node) |
| drop one referenced certificate from a claim's coverage | 317 | 317 (100 %) | guaranteed (uncovered key) |
| claim `lower_even - 1` / `lower_odd - 1` | 317 / 317 | 303 / 317 | rejected iff the final test fails (14 claims hold by the other side) |
| claim `lower_even + 1` | 317 | 317 (100 %) | a key without complete coverage becomes referenced |

Every mutation the checker accepts was re-verified to be a genuine certificate / genuine coverage; every mutation that
must be rejected was rejected.

---

## 3. Stress test of the rows (`stress_ext2.py`) and the synthetic HUB control [finite-checked]

Circuits: the 13 package controls and the 303 real circuits of `bridge/profiles.json` (bridge reconstruction
`reconstruct(values, 'ymax')`, as in qcert, qbound, qcheck, qreal), orbit steps 0-3 with the package's `Circuit`,
`analyse`, `canonical_transpose`; the package's own rows re-asserted on every phase. 316 circuits, **1,264 phases**
(316 raw M, 316 canonical M, 632 canonical M^T), **0 violations**, 36 s. Recomputed on the way: rho_6 = 20 / 28, dim J =
24 / 28 (F9), F6's rank bound, S1's sigma histogram; the equality `U_l + V_l + ee_l = d_l + 1` asserted at every missing
label; cap(h_i) by exhaustive search for every non-full helper mask met (977 distinct masks, 20,745 helper checks), all
equal to the H1 table. Lemma O1: every one of the 324 full helpers met defines exactly 2 outputs, all distinct, each in
its triple.

Minimum slack (controls / real; raw M, canonical M, canonical M^T), selected rows:

| row | ctrl raw M | ctrl can. M | ctrl can. M^T | real raw M | real can. M | real can. M^T |
|---|---:|---:|---:|---:|---:|---:|
| HUB strong form `cap(h_i) - #full-met` / LP form `4 + q - A - u_i` | 0 / 8 | 0 / 13 | 0 / 8 | 0 / 10 | 0 / 12 | 0 / 11 |
| HUBlin | 52 | 72 | 64 | 60 | 68 | 64 |
| L13d / L14d / L15d | 25 / 27 / 15 | 24 / 26 / 14 | 0 / 0 / 0 | 24 / 26 / 15 | 26 / 28 / 16 | 10 / 10 / 4 |
| L17Md | 29 | 28 | | 30 | 32 | |
| L17Td / L18d | | | 0 / 0 | | | 4 / 12 |
| bright lower (O1) / bright capacity (O2) | 2 / 14 | 2 / 10 | 0 / 0 | 4 / 9 | 2 / 12 | 3 / 6 |
| dark capacity (O3) / F budget (O4) | 0 / 10 | 2 / 10 | 14 / 10 | 0 / 9 | 3 / 9 | 11 / 8 |
| `y2d <= y2` / `y2m <= C(q,2)` / (I') | 0 / 21 / 32 | 0 / 53 / 40 | 3 / 18 / 37 | 0 / 21 / 35 | 0 / 42 / 41 | 2 / 42 / 39 |
| per label: `4 + 2f_l - UA_l - Y_l` (bright) / `4 + 2f_l - ee1_l` (dark) | 1 / 2 | 1 / 1 | 1 / 2 | 0 / 2 | 0 / 1 | 0 / 2 |
| per label: `7 - 2k_l - W_l - Y_l` / `3 - k_l - Z_l` | 0 / 0 | 0 / 0 | 1 / 0 | 0 / 0 | 0 / 0 | 1 / 0 |
| dark labels: `W_l + Z_l + A_l + Y_l + UA_l = 0`; pairs of missing labels in <= 1 gate; O1 | 0 (equality) | 0 | 0 | 0 | 0 | 0 |
| G\*_J / N1 / (I) (batch-1, as in qcert) | 0 / 18 / 32 | 0 / 23 / 44 | 0 / 26 / 41 | 1 / 20 / 35 | 2 / 23 / 44 | 0 / 23 / 42 |

Rows tight on some phase: (L13d), (L14d), (L15d), (L17Td), (L18d), bright lower, bright capacity on 2 control M^T
phases each (where G\* with the F9 space is tight, as qreal and qrealcheck found); `Fd = y2d = 0` on 67 phases with
q_D = 0; `Fb = 0` on 2 phases with q_D = q; the HUB strong form on 1,247 helper phases (cap(h_i) = 0 = #full-met: no
full-met label anywhere). Ranges: q = 7..16 (no phase has q <= 6, so the small-q regime where the certificates act is
not exercised, as in qcert); q_D = 0..8 (M), 3..7 (M^T); A = 0 on every phase; y2d up to 16, y2m up to 8; helper masks
with cap(h) = 4 occur on real phases, with 0 full-met labels. The stress test is a positive control for the rows, not
evidence about the survivors.

**Synthetic control with A >= 1 (`synthetic_hub.py`, 12 s).** A *local helper configuration*, not a full circuit: a hub
helper i (mask h, r_i = 0) with m missing H-B edges whose labels are full-met by m full helpers f_n (each with its three
represented triples and one missing H-B edge), the pairs {b_n, c_n} = h + f_n; q = A = u_i = m inside the configuration.
Realizability requires the configuration's gate equations (3m represented relations + 2m missing-edge equations) to be
independent (proof of Lemma 4.4); H1's cap(h) only uses the 3m relations. Results, both orientations: the realizable
capacity m\*(h) has histogram M {1: 126,412, 2: 1,648, 3: 8}, M^T {1: 174,320, 2: 3,072, 3: 20} (H1's cap: M
{1: 125,128, 2: 2,840, 3: 92, 4: 8}, M^T {1: 172,060, 2: 5,156, 3: 176, 4: 20}, reproduced); **every one of the 1,152 (M) /
2,880 (M^T) cap-4 witness sets has dependent gate equations**, so A = 4 at one hub is never realizable; at m = 3 there are
**192 (M) / 480 (M^T) configurations** at the 8 / 20 cap-4 hub values, all with independent gate equations (rank 15),
distinct labels, disjoint pairs, pairwise non-adjacent full helpers (F4), on which the HUB row `u_i <= 4 + q - A` holds
with slack 1 and its mutation `u_i <= 3 + q - A` is violated, and Lemma H1's strong form has slack cap(h) - m = 1. (The
M^T histogram agrees with the qhub agent's independent C1 computation, `qhub/hub2.log`; the sharper capacity is theirs
to certify and is **not used** in any certificate here, which all rest on the proved constant 4.) The LP row is thus
exercised at A = 3 but never tight on a realizable local configuration.

---

## 4. What remains open

- **996 oriented claims (504 with even phase M, 492 with M^T) remain open at G = 75 by LP status [measured]; no
  bound improvement.** Their shortfall `budget - (k + l)` is 0 for 511, 1 for 337, 2 for 109, 3 for 39 claims; the
  survivor sets and (k, l) are identical to qreal's `scan_GstarN1HUBDARKM_q0_g75.json` and qrealcheck's
  `lp_qrc_scan_GstarN1HUBDARK.json` (`crosscheck2.py`).
- Of the 681 batch-1-feasible keys, 381 remain LP-feasible (by q 1: 2, 2: 2, 3: 14, 4: 54, 5: 163, 6: 93, 7: 11, 8: 41,
  10: 1), identical to qreal's and qrealcheck's lists. The complete key bookkeeping of the final scan (1,661 LP-feasible
  keys touched, 1,377 load-bearing) is qrealcheck's (section 9 there) [read, not checked here].
- Proposition 11.1's argument at G = 75 would need all 7,416 claims excluded: 195 (qcert) + 317 (here) of the 1,508
  claims that the package rows leave are now certified; 996 are not.
- Not done: certificates for the 1,377 load-bearing keys outside the two reductions above (not asked); the refined hub
  capacity (qhub); the integer oracle; the two finite searches of qreal section 6.

---

## 5. Trust ledger

**Relied on, not re-proved here [read, not checked]:**
- PROOF.md Lemmas 1.1, 1.2, 3.2/(3.2), 4.1-4.7, 10.1-10.4 and their proofs; in particular the per-label inequalities
  inside the proofs of (L13)-(L18) (F7, F9, F10, F11, F12 and the charging argument), which Lemma D1 re-sums with the
  dark count kept; Lemma 7.4 exactly where the package uses it (helper types with r + u + v >= 3).
- Addendum A (qcert): Lemma G\* (used by D1 through its lower bound on sum_bright k_l), Lemma N1 (used by O1), (L7\*),
  the kinds y_0, y_1, y_2, and the batch-1 rows of the system, with their certificates.
- Finite facts F2-F14 (package `finite_facts.py`; `verify_all.py` replayed by lb76). H1 itself is [finite-checked] by
  qreal, qrealcheck and (for the cap-4 values and the helper masks met) here.
- The scalar domain formulas of PROOF.md section 11 at G = 75 (lb76 report; the coverage checker applies them literally);
  the bridge reconstruction as a faithful gate list for the 303 real circuits.

**Proved in the addendum [proved]:** Lemma H1 and the exhaustiveness and soundness of the HUB split; Lemma D1
(L13d)-(L18d) relative to the package's proofs; Lemma D2 (O1)-(O7); the exhaustiveness and soundness of the DARK split;
Lemma O1; Lemma C1 (persistence of certificates under relaxation of the case) and the coverage definition.

**Finite-checked here [finite-checked]:** cap(h) for the cap-4 values (every 5-subset dependent) and for the 977 helper
masks met; the set identities 681 / 381 / 300 / 1,313 / 996 / 317 with the qbound, qreal, qrealcheck and qcert files;
the identity of the two system definitions on 23,593 case nodes; the mutation statistics; the zero-violation stress
result; the synthetic configurations and the non-realizability of A = 4 at one hub.

**Certified by the files [certified]:** for each of the 2,460 keys and each of its case nodes carrying a certificate, the
case system at G = 75 has no nonnegative real solution; for each of the 300 killed keys every leaf case is covered; for
each of the 317 claims every (q, z) below the stated k, l is excluded by (4.4), Lemma 10.3 or a covered key, and
`k > S_e or l > S_o or k + l > a + b + 2G - 192`.

**What follows on its own.** Granting the package lemmas and finite facts, Addendum A and the proofs of Addendum B: no
tail of the orbit at G = 75 has one of the 317 excluded (profile, orientation) pairs. Nothing about L(M) follows,
because 996 pairs remain.

---

## 6. Caveats

- As in the package and qcert, the bounds k, l of the 317 claims were produced by the package driver with our LP
  feasibility; the checker verifies only the infeasible side and the final test. A claim's k, l could be larger than
  found, never smaller.
- The HUB case `A <= 4` admits fractional A; the integer refinement changes no key set at G = 75 (qrealcheck) and is not
  used. The constant 4 of H1 is the proved one; the realizable capacity 3 observed by `synthetic_hub.py` (and by qhub)
  is not a premise of any certificate here.
- LP solver status decides only which keys and cases to attempt and the kind label of a certificate; no exclusion rests
  on it. The largest multiplier (25,002) comes from the rationalization of one LP vertex; all multipliers are exact
  integers checked as such.

---

## 7. Labels, in one table

| statement | label |
|---|---|
| Lemma H1; HUB split exhaustive and sound; Lemma D1; Lemma D2; DARK split exhaustive and sound; Lemma O1; Lemma C1 | [proved] (PROOF_ADDENDUM_2.md) |
| finite fact H1 (cap(h) <= 4; histograms) | [finite-checked] (qreal `hub.py`, qrealcheck `h1_check.py`; here `synthetic_hub.py`, `stress_ext2.py`) |
| 4,523 certificates; case coverage of 300 keys and 317 claims; largest rhs -1 | [certified] (`check_cases75.py`, `gen_certs2.py`) |
| the two system definitions coincide on 23,593 (key, case) nodes | [finite-checked] (`crosscheck2.py`) |
| 681 / 381 / 300 keys and 1,313 / 996 / 317 claims = the qbound / qreal / qrealcheck / qcert sets | [finite-checked] (`crosscheck2.py`) |
| batch-1 rows alone leave the 300 keys and 317 claims feasible; 996 / 381 remain | [measured] (LP status) |
| 0 violations on 1,264 phases; O1 on 324 full helpers; cap table = own search on 977 masks | [finite-checked] (positive control only) |
| synthetic A = 3 configurations; A = 4 at one hub never realizable | [finite-checked] (local configurations, not circuits) |
| package Lemmas 1.1-10.4, F2-F14, section 11 formulas at G = 75; Addendum A | [read, not checked] |
| any bound beyond 75 | **not claimed** |
