# qcert: package-grade certificates and proof addendum for the new rows at G = 75

qcert agent, 2026-11-07 (about 40 minutes of wall-clock work, 14 minutes of compute). Working directory
`~/xs-campaigns/2026-11-07-sprint/qcert/`. The git repository and `lb76/pkg_copy/` were read only; the package
programs `certify75.py` and `lp_regen.py` were imported from the copy unchanged, `stress.py` and the bridge's
`profile_real.py` were copied into `qcert/` (`stress_pkg.py`, `profile_real_copy.py`) and left unmodified. One
python process at a time under `nice -n 8`.

Labels on every claim: **[proved]** (written proof in `PROOF_ADDENDUM.md`, package lemmas and finite facts as black
boxes), **[finite-checked]** (computed exactly by a program named here), **[certified]** (exact integer certificate
checked by two independently written programs), **[measured]** (LP status or circuit statistics; never a premise),
**[read, not checked]** (package or earlier-report statement relied on as is).

**No lower bound beyond 75 is claimed.** 1,313 of the 7,416 oriented claims at G = 75 remain open.

---

## 0. Summary

1. `PROOF_ADDENDUM.md` states and proves, in PROOF.md's notation and style, Lemma N1, Lemma G\* (family listed,
   independence established first, three invertible operations, weight-0 case, rank-nullity step written out),
   (L7\*), (L12\*), (I), (Q0), the row-by-row justification of `y -> y_2` with the facts each row uses, Lemma S with
   finite fact S1 and Corollary S2, the normalization-only statement, and corrects the four wording points raised by
   qcheck. [proved] / [finite-checked]
2. `CERTIFICATES_EXT75.json`: **1,772 exact integer Farkas certificates** at G = 75 for the extended local system
   (package rows (L1)-(L23) unchanged + the new rows): **666 use the new rows** (every one of the **453** keys that
   the package rows leave LP-feasible and the extended system kills, plus 213 further keys that only the extended
   coverage reaches) and **1,106 use the package rows only**; together they give **complete coverage of the 195
   oriented claims** (122 with even phase M, 73 with M^T) that the extended system excludes and the package rows do
   not. Largest weighted right-hand side -1; 53,917 column coefficients checked. [certified]
3. Two checkers: the generator's own exact check (package rows imported from `certify75.system`) and
   `check_ext75.py` (every row constant and coefficient written out by hand, standard library only, coverage
   domain rebuilt from PROOF.md section 11 at G = 75). `crosscheck.py` shows the two system definitions are
   identical matrices on all 2,562 keys the file touches. Pinned expected counts. [certified]
4. Mutation tests (`mutate_test.py`): 7,225 negated multipliers, 195 dropped referenced certificates, 195 `k+1`
   and 195 `l-1` claim mutations: all rejected; 68 of 7,225 zeroed multipliers survive and each surviving vector is
   itself a valid certificate. [finite-checked]
5. `stress_ext.py` (an extension of the package's `stress.py`, original untouched): every new row and the per-label
   strong forms on the 13 control circuits and the 303 real circuits of `bridge/profiles.json`, 4 orbit steps
   each (raw circuit + 3 canonical transposes), **1,264 phases, 0 violations**; rho_6, dim J (F9), F6's rank bound and
   the sigma histogram S1 are recomputed on the way. [finite-checked]
6. Open: 1,313 claims (724 M, 589 M^T) by LP status, 681 LP-feasible keys; the integer-oracle figure 1,167 of the
   qbound report is not certified and is not quoted as a result. [measured]

---

## 1. What is certified: exact counts

All numbers below are printed by `check_ext75.py` (pinned in its `EXPECTED` dictionary) and by `gen_certs.py`;
the two agree.

| quantity | value | label |
|---|---:|---|
| admissible scalar states at G = 75 (PROOF.md section 11 formulas, rebuilt independently) | 3,708 | [finite-checked] |
| oriented claims | 7,416 | [finite-checked] |
| claims surviving the package rows (L1)-(L23) at G = 75 | 1,508 (846 M, 662 M^T) | [measured] (LP) |
| claims surviving the extended system | 1,313 (724 M, 589 M^T) | [measured] (LP) |
| **newly excluded oriented claims, with complete coverage** | **195** (122 M, 73 M^T) | **[certified]** |
| local keys the package rows leave LP-feasible (lb76 `g75_keys.json`, re-found) | 1,134 | [measured] |
| keys among them killed by the extended system | **453** (M 133, M^T 320; by q: 0: 31, 1: 266, 2: 10, 3: 89, 4: 47, 5: 8, 6: 2) | **[certified]** infeasible |
| keys referenced by the coverage of the 195 claims | 1,459 | [finite-checked] |
| of which infeasible only with the new rows ("new") | 353 (140 among the 453; 213 never visited by the package-row scan) | [certified] |
| of which infeasible with the package rows alone ("package") | 1,106 | [certified] |
| **certificates in the file** | **1,772 = 666 new + 1,106 package** (666 = 453 + 213) | **[certified]** |
| certificate references in coverage / direct (Lemma 10.3) references | 2,158 / 567 | [finite-checked] |
| helper-type and y-column coefficients checked | 53,917 | [certified] |
| largest weighted right-hand side | -1 | [certified] |
| multipliers (total / nonzero / largest) | 58,307 / 7,225 / 1,854 | [certified] |
| rows per certificate | 30 to 37 | |
| certificates that fail to rationalize | 0 | |

**What "killed by the extended system" means.** Each of the 453 keys has a certificate with at least one nonzero
multiplier on a new row; that the package rows alone leave it feasible is an LP status (the complement of a
certificate) and is [measured], not a premise. The same holds for the "new" kind in general.

**Why 1,106 package-row certificates are in the file.** The package ships certificates for G = 74 only. Complete
coverage of a claim at G = 75 needs a certificate for every (q, z) below the new k, l, most of which are already
infeasible with (L1)-(L23); those certificates (multipliers zero on every new row, visibly independent of the new
lemmas) are generated here so that the 195 claims are checkable without any LP. 213 of the 666 "new" certificates
are for keys the package-row scan never visited (it stops at the first feasible s; the extended scan goes further).

**How the 195 claims are excluded** (final test of PROOF.md section 11, with the new k, l): `k + l > a + b + 2G - 192`
for 143 claims, `k > S_e` for 38, `l > S_o` for 14. Under the package rows their shortfall `budget - (k + l)` was 0
(117 claims), 1 (62) or 2 (16). [finite-checked]

**Which new rows the 666 new certificates use** (number of certificates with a nonzero multiplier on the row):
N1 587, (I) 104, (L12\*) 66, (L17-MT\*) 40, (L17-M\*) 33, (Q0) 31, the y-split equality 29, (L19\*) 16, (L7\*) 10,
(L15\*) 5, (L14\*) 1, (L13\*) 1. (N1) is the workhorse; (L18\*), (L20\*), (L22\*) are never used at G = 75. [finite-checked]

**The G-dependent constant.** (N1)'s constant is `G - 32 - h - q`. The certificate file records `"gates": 75` once;
both checkers rebuild the constant from it. A "new" certificate that uses (N1) is therefore a statement about its key
*at G = 75*; a "package" certificate, like the package's own, is valid for its key at every G.

---

## 2. Files and verification commands

| file | purpose |
|---|---|
| `PROOF_ADDENDUM.md` | the mathematics (sections A.1-A.9) |
| `CERTIFICATES_EXT75.json` | `gates`, `system` (row order), `claims` (195: state, orientation, new `lower_even`/`lower_odd`, and the package-row bounds), `killed_keys` (453), `certificates` (1,772: key, kind, weights), `counts` |
| `gen_certs.py` | generator: two scans with the package driver `lp_regen.run` (feasibility = primal LP on each system), Farkas LP (`min sum lambda`, HiGHS), rationalization with `fractions` (`limit_denominator` 10^3..10^12), lcm scaling, gcd reduction, exact integer re-check; needs numpy/scipy |
| `check_ext75.py` | **independent checker**: hand-written rows, pure integers, coverage domain rebuilt; pinned expected counts; writes `CHECKED_EXT75.json` |
| `crosscheck.py` | generator's and checker's matrices identical on every touched key; key and claim sets equal qbound's and qcheck's files |
| `mutate_test.py` | mutation tests of the checker; writes `mutate_test.json` |
| `stress_ext.py` | new rows on 13 controls + 303 real circuits; writes `stress_ext.json`, log in `stress_ext.log` |
| `scan_ext75.json` | all 7,416 claims with (k, l, dead) under both systems; the 1,508 and 1,313 survivor lists |
| `stress_pkg.py`, `profile_real_copy.py` | unmodified copies of the package `stress.py` and the bridge reconstruction |
| `run_all.sh` | the complete check (below); `s00`-`s05` are the shell drivers actually run, `*.out` their outputs |
| `SHA256SUMS.txt` | hashes of the static deliverables (not of the files the checks rewrite) |

**Commands** (from `qcert/`; standard library suffices for everything except regeneration):

```sh
python3 check_ext75.py CERTIFICATES_EXT75.json   # ~1 s   -> "expected counts match ... INDEPENDENT CHECK PASSED"
python3 crosscheck.py                            # ~3 s   -> "systems identical on 2562 keys ... CROSSCHECK PASSED"
python3 stress_ext.py                            # ~15 s  -> "STRESS EXT PASSED: 316 circuits, 1264 phases, 0 violations of the new rows"
python3 mutate_test.py 1                         # ~8 min -> "MUTATION TEST PASSED"
sha256sum -c SHA256SUMS.txt
sh run_all.sh                                    # all of the above, ends with "QCERT ALL CHECKS PASSED"
python3 gen_certs.py                             # regeneration (numpy + scipy), ~2 min, rewrites CERTIFICATES_EXT75.json and scan_ext75.json
```

**Two code paths.** The generator builds the package rows by calling the package's `certify75.system(key)` and appends
the new rows as lambda-functions over the types; the checker lists every right-hand side and every column coefficient
literally (as `independent75.py` does), including the three `y`-columns, and enumerates the type domain itself.
`crosscheck.py` compares the two matrices entry by entry on the 2,562 keys touched by the certificates and the coverage
(certified, direct or (4.4)-excluded): identical. Both checkers verify `lambda >= 0` integer, `lambda^T A >= 0` per
column, `lambda^T b < 0`, and the checker verifies coverage and the final test per claim.

**Mutation tests** (`mutate_test.py 1`, 8 min):

| mutation | count | rejected | note |
|---|---:|---:|---|
| negate one nonzero multiplier | 7,225 | 7,225 (100 %) | guaranteed (nonnegativity) |
| zero one nonzero multiplier | 7,225 | 7,157 (99.1 %) | the 68 survivors are valid certificates (redundant row); each re-verified |
| add 1 to one multiplier | 7,225 | 4,870 (67.4 %) | survivors are valid certificates by construction of the check |
| check against a neighbouring key (q+1, z+1, other orientation, h+1) | 7,088 | 5,065 (71.5 %) | |
| row constant +1 on one used row (checker's system) | 1,772 | 364 (20.5 %) | rejected iff the weighted right side reaches 0 |
| flip the sign of one used coefficient (checker's system) | 1,678 | 1,247 (74.3 %) | rejected iff a column sum turns negative |
| drop one referenced certificate from the file | 195 | 195 (100 %) | guaranteed (uncovered key) |
| claim `lower_even - 1` / `lower_odd - 1` | 195 / 195 | 181 / 195 | rejected iff the final test fails (14 claims hold by the other side) |
| claim `lower_even + 1` | 195 | 195 (100 %) | a key without certificate becomes referenced |

Every mutation the checker accepts was re-verified to be a genuine certificate / genuine coverage, so the checker
has no false acceptances in these families; every mutation that must be rejected was rejected.

---

## 3. Stress test of the new rows (`stress_ext.py`) [finite-checked]

Circuits: the 13 package controls (`pkg_copy/source/circuits/`) and the 303 real circuits of `bridge/profiles.json`
(reconstructed with the bridge's `reconstruct(values, 'ymax')`, as in the qbound and qcheck runs); orbit steps 0-3 with
the package's `Circuit`, `analyse`, `canonical_transpose`; the package's own rows re-asserted on every phase
(`check_rows`). 316 circuits, **1,264 phases** (316 raw M, 316 canonical M, 632 canonical M^T), **0 violations**, 12 s.
Tables recomputed from the matrix on the way: rho_6 = 20 / 28, dim J = 24 / 28 (F9), max rank(C_l) = 7 (F6),
sigma histogram M {0: 1704, 2: 66, 3: 228, 4: 6, 5: 12}, M^T {0: 1590, 2: 78, 3: 312, 4: 12, 5: 24} (S1); for every
bright label met, rank(C_l) + 2 k_l <= 7 (F9). Each kind-0 gate was verified to reduce to a weight-6 element of R_6 and
each kind-1 gate to a 2- or 4-form of its bright label (the two reductions of Operation 1 in Lemma G\*).

Minimum slack (controls / real; raw M, canonical M, canonical M^T):

| row | controls raw M | ctrl can. M | ctrl can. M^T | real raw M | real can. M | real can. M^T |
|---|---:|---:|---:|---:|---:|---:|
| N1 | 18 | 23 | 26 | 20 | 23 | 23 |
| L7\* (aggregate) / per label `rank(C_l) - W_l - Y_l` | 30 / 0 | 50 / 0 | 49 / 0 | 24 / 0 | 45 / 0 | 47 / 0 |
| L12\* | 0 | 0 | 0 | 7 | 7 | 6 |
| G\* with J = R_6 | 1 | 0 | 0 | 2 | 1 | 0 |
| G\* with the F9 space J | 0 | 0 | 0 | 1 | 2 | 0 |
| (I) (aggregate) / per missing label `4 + 2f_l - (U_l + V_l + ee_l)` | 32 / 1 | 44 / 1 | 41 / 1 | 35 / 0 | 44 / 0 | 42 / 0 |
| L13\* / per bright label `7 - 2k_l - W_l - Y_l` | 26 / 0 | 48 / 0 | 63 / 1 | 24 / 0 | 49 / 0 | 56 / 1 |
| L14\* / `sum ex_l <= eps` slack | 28 / 2 | 50 / 2 | 63 / 0 | 26 / 2 | 51 / 2 | 56 / 0 |
| L15\* | 19 | 28 | 28 | 15 | 27 | 26 |
| L17-M\* | 36 | 50 | | 30 | 55 | |
| L17-MT\* / L18\* / L19\* / L20\* | | | 42 / 70 / 4 / 13 | | | 33 / 65 / 3 / 9 |
| Lemma S per represented label / S2 poor labels at r >= 2 helpers | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| S2 aggregate `top(x+y-q) - 6n_3 - 2n_2` | 74 | 80 | 100 | 73 | 81 | 85 |

Rows tight (slack 0) on some phase: (G\*) with J = R_6 on 1 control M, 8 control M^T and 12 real M^T phases; (G\*)
with the F9 space J on 4 control M, 8 control M^T, 12 real M^T phases; (L12\*) on 2 + 2 control phases; the per-label
forms of (L7\*), (L13\*), (L14\*), (I) and Lemma S on many labels. Ranges: n_3 = 0..4 (controls), 0..1 (real M),
0..3 (real M^T); y_0 up to 20, y_1 up to 16, y_2 up to 16; h_0 up to 5; q_D up to 8. **No phase has q <= 6**
(q = 7..16), so (Q0), (L22\*) and the small-q regime where the certificates act are not exercised by any known circuit:
the stress test is a positive control for the rows, not evidence about the survivors.

---

## 4. What remains open

- **1,313 oriented claims** (724 with even phase M, 589 with M^T) survive the extended system by LP status [measured];
  their shortfall `budget - (k + l)` is 0 for 565, 1 for 515, 2 for 183, 3 for 50 claims. **681 local keys** stay
  LP-feasible (by q: 1: 57, 2: 30, 3: 57, 4: 72, 5: 197, 6: 151, 7: 61, 8: 54, 10: 2), agreeing with qbound's
  `scan_GstarN1_q0_g75.json` and qcheck's `lp_indep_*` files key for key (`crosscheck.py`).
- The qbound integer-oracle figure (1,167 claims, 497 keys by branch-and-bound) is **not certified** and is not
  quoted as a result here.
- **No bound improvement**: Proposition 11.1's argument at G = 75 would need all 7,416 claims excluded; 195 of the
  1,508 missing ones are now certified, 1,313 are not.
- Not done (free or cheap strengthenings noted in the addendum): (L18) with `W -> W + y_1`; the exact `y_1 = y_2 = 0`
  at q = 0; the dark-label case split, integrality certificates and the two-phase boundary fan-out constraint of
  qbound section 8.

---

## 5. Trust ledger: what a reader must still trust, and what these files prove on their own

**Relied on, not re-proved here [read, not checked]:**
- PROOF.md Lemmas 1.1, 1.2, 3.2/(3.2), 4.1-4.7, 10.1-10.4 and their proofs; in particular the independence of the
  gate equations and of the represented relations (Lemma 4.4), Lemma 4.5 (F4), and the eliminations in the proofs of
  (L13)-(L22), which the starred rows modify at one step each. Lemma 7.4 is used exactly where the package uses it:
  the restriction of the helper types to r + u + v >= 3.
- Finite facts F2-F14 (recomputed by the package's `finite_facts.py`; `verify_all.py` replayed clean by the lb76 agent
  on 2026-11-07, 137.5 s). `stress_ext.py` recomputes rho_6, dim J, max rank(C_l) and, for the labels it meets,
  rank(C_l) + 2k_l <= 7; it does not recompute F4, F7, F8, F10-F13.
- The scalar domain formulas of PROOF.md section 11 (admissibility, S_e, S_o, Lemma 8.2 caps, budget) carry over to
  G = 75 unchanged (lb76 report, section 1; the coverage checker applies them literally).
- The bridge's reconstruction `reconstruct(values, 'ymax')` as a faithful gate list for the 303 real circuits (bridge
  report; the package's own assertions pass on every phase).

**Proved in the addendum [proved]:** Lemma N1; Lemma G\* for every J containing R_6; (L7\*), (L12\*), (I), (Q0);
(L13\*)-(L15\*), (L17\*), (L18\*), (L19\*), (L20\*), (L22\*) relative to the package's proofs; Lemma S and Corollary S2;
that every new row needs only normalization (section A.7).

**Finite-checked here [finite-checked]:** S1 (sigma histogram, no sigma = 1); rho_6, dim J, F6's bound; the two
Operation-1 reductions on 1,264 phases; the 453 / 195 / 1,313 / 681 set identities with the qbound and qcheck files;
the mutation statistics; the zero-violation stress result.

**Certified by the files [certified]:** for each of the 1,772 keys, the extended local system (rows of section A.6 at
G = 75) has no nonnegative real solution; for each of the 195 oriented claims, every (q, z) below the stated k, l is
excluded by (4.4), Lemma 10.3 or a certificate, and `k > S_e or l > S_o or k + l > a + b + 2G - 192`.

**What follows on its own.** Granting the package lemmas and finite facts and the addendum's proofs: no tail of the
orbit at G = 75 has one of the 195 excluded (profile, orientation) pairs. Nothing about L(M) follows, because 1,313
pairs remain.

---

## 6. Caveats

- The bounds k, l of the 195 claims were produced by the package driver `lp_regen.run` with our LP feasibility; as in
  the package, the checker verifies only the infeasible side (coverage below k, l) and the final test. A claim's k, l
  could be larger than what we found (if some key we called feasible is not), never smaller.
- `gen_certs.log` was truncated by an import side effect during the first `crosscheck.py` run and restored from the
  captured stdout `s01_gen.out` (identical lines); the side effect is fixed in `gen_certs.py`.
- LP solver status is used only to decide which keys to attempt and to classify "new" versus "package"; no exclusion
  rests on it.

---

## 7. Labels, in one table

| statement | label |
|---|---|
| Lemmas N1, G\*, S; (L7\*), (L12\*), (I), (Q0); y -> y_2 rows | [proved] (PROOF_ADDENDUM.md) |
| S1 histogram; rho_6 = 20/28; dim J = 24/28; rank(C_l) <= 7 | [finite-checked] (`stress_ext.py`; also qbound, qcheck, package) |
| 1,772 certificates; coverage of 195 claims; largest rhs -1 | [certified] (`check_ext75.py`, `gen_certs.py`) |
| the two system definitions coincide on 2,562 keys | [finite-checked] (`crosscheck.py`) |
| 453 killed keys / 195 claims = qbound's and qcheck's sets | [finite-checked] (`crosscheck.py`) |
| package rows alone leave the 453 keys and 1,508 claims feasible; 1,313 / 681 remain | [measured] (LP status) |
| 0 violations on 1,264 phases; tightness and ranges | [finite-checked] (positive control only) |
| package Lemmas 1.1-10.4, F2-F14, section 11 formulas at G = 75 | [read, not checked] (replayed by lb76) |
| integer-oracle 1,167 / 497 | not certified; not quoted as a result |
| any bound beyond 75 | **not claimed** |
