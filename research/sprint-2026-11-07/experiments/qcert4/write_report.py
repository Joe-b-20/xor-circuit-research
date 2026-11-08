#!/usr/bin/env python3
"""qcert4: writes REPORT.md (the Write tool refuses report files; the coordinator asked for a python script)."""
from pathlib import Path
REPORT = r'''# qcert4: per-case certificates and proof addendum for the joint hub rows (Lemma J, finite fact J1, Lemma P, row LIM, exact hub split) at G = 75

qcert4 agent, 2026-11-08, 03:24-04:30 UTC. Working directory `~/xs-campaigns/2026-11-07-sprint/qcert4/`. Read only:
the repository, `lb76/pkg_copy/`, `qcert3/`, `qjoint/`, `qjointcheck/`, `qhubcheck/`, `bridge/` (no file outside
`qcert4/` was written; every run with `PYTHONDONTWRITEBYTECODE=1`, the `__pycache__` directories there are unchanged).
`qcert3/gen_certs3.py` and `qcert3/check_cases3.py` are imported from byte-identical copies (`gen_certs3_copy.py`,
`check_cases3_copy.py`, `cmp`-checked); the package programs `certify75.py`, `lp_regen.py`, `stress.py` and
`bridge/profile_real.py` are imported unchanged; `qjointcheck/jc_circ.py` / `jc_geo.py` are imported (read only) for the
synthetic phases. One python process at a time under `nice -n 8` (load average about 8 from other agents).

Labels: **[proved]** (written proof in `PROOF_ADDENDUM_4.md`; package lemmas, Addenda A-C and finite facts as black
boxes), **[finite-checked]** (computed exactly by a named program), **[certified]** (exact integer certificate checked by
two independently written programs), **[measured]** (LP status or circuit statistics; never a premise), **[read, not
checked]**.

**No lower bound beyond 75 is claimed. 686 of the 7,416 oriented claims at G = 75 remain open by LP status.**

---

## 0. Summary

1. `PROOF_ADDENDUM_4.md` (Addendum D), in package style: Lemma J, the independence of the joint gate-equation family
   F_joint, with the **spanning-tree statement** (t - 1 mixed vectors for t >= 3 hubs at one hub-only label; one per pair
   is dependent) (D.2); finite fact J1 stated exactly as (J1a) intersecting pairs at a common full value and (J1b)
   pair-value neighbours, with both implementations and their counts, and its consequence "two limit hubs never share a
   missing label" (D.3); Lemma P, rows P1-P5 (D.4); Lemma D5, the packing bound D(n) with a proof (Johnson count plus the
   even-leave parity step; D(0..12) = 0,0,0,1,1,2,4,7,8,12,13,17,20) (D.5); the per-row relaxation argument for the LP
   form in the exact hub case, with the concave term m(u - m) minimised at an endpoint (D.6); row LIM in its three
   cases (D.7); the exact integer split A = 0..q as the disjunction, exhaustive and sound, and its relation to batch 3
   (D.8); case systems, Lemma C1, coverage (D.9); every package lemma and finite fact cited per statement (D.10).
   [proved]
2. `CERTIFICATES_CASES75_B4.json`: **4,361 exact integer Farkas certificates for 1,307 keys** at G = 75, **3,506 of them
   per case**, each recording its hub case (A value) and its dark case (q_D or none): complete case coverage of **all 375
   keys** that are LP-feasible under the batch-3 systems and killed by the new ones (343 of the 1,437 keys of qcert3's
   lists, among them **all 163 of the 551 load-bearing keys** of the 551 -> 388 recount, plus 32 of the 242 batch-3-feasible
   keys the new scan touched outside those lists), 14,096 leaves; and complete coverage of **all 103 newly excluded
   oriented claims** (44 M, 59 M^T: the **789 -> 686** reduction; 980 referenced keys, 18,418 leaves). Largest weighted
   right side -1; 264,062 column coefficients; 0 uncertified (key, case) pairs. [certified]
3. **What rests on J1.** Certificates are sought without row LIM first. LIM is used by 78 certificates, **all in case
   (ii) a = q - 1** (so only J1's hub-only part (J1b) is load-bearing; (J1a) and LIM's Lemma-4.6 case (i) enter no
   certificate). **Without J1: 297 of the 375 killed keys and 65 of the 103 claims are covered**; 78 keys (M q = 4: 66;
   M^T q = 3: 12) and 38 claims rest on J1. The LP scan without LIM gives 724 survivors (65 excluded), in agreement.
   Five M^T q = 1 keys (12,5,F,1,4), F = 1..5, die by the **exact integer split alone** (no joint row). [certified]
4. Checkers: the generator's own exact check (`gen_certs4.py`: rows from `certify75.system` + gen_certs3 + closed-form
   joint rows) and **`check_cases4.py`** (standard library only; check_cases3's hand-written rows plus brute-force joint
   rows over the m-interval, the packing bound computed by its proof, its own case tree A = 0..q for every q, pinned
   expected counts). `crosscheck4.py`: the two system definitions are identical on **all 22,301 (key, case) nodes** of
   the 452 keys with case certificates (91,296,843 coefficients); survivors, (k, l), key sets equal qjoint's and
   qjointcheck's (both of its variants). [certified] / [finite-checked]
5. Mutation tests (`mutate4.py`, every certificate): 26,272 negated multipliers, 375 dropped case certificates and 103
   dropped referenced certificates all rejected; every zeroed / incremented multiplier that survives (146 / 10,340) is
   re-verified as a valid certificate; dropping any used joint row rejects 100 % of the certificates using it.
   [finite-checked]
6. Stress extension (`stress_ext4.py`): 13 controls + 303 real circuits, **1,264 phases, 0 violations** of P1-P5, H2,
   HUB2's deletion, J1, LIM (strong forms) and of both LP implementations (identical on every type met; each LP
   coefficient <= the helper's actual term on 20,745 helpers); qjointcheck's synthetic two-hub phases: **102,792 phases
   (11,912 realizable), 0 violations**, every J1-excluded phase dependent and caught by the LP row LIM. [finite-checked]
7. `CERTIFICATES_PARTIAL75_B4.json`: for the **1,304 surviving** batch-3-feasible keys every killed case is certified
   too: 22,586 certificates; **44,058 of their 47,987 leaves dead, 3,929 open** (LP-feasible). [certified] / [measured]
8. Open: **686 claims (372 M, 314 M^T) remain open at G = 75; no bound improvement.** [measured]

---

## 1. Exact counts

All numbers are printed by `check_cases4.py` (pinned in `EXPECTED`, written to `CHECKED_CASES75_B4.json`),
`gen_certs4.py` (`gen_certs4.log`, `s01_gen.out`), `gen_partial4.py` (`s04_partial.out`) and `stats4.py` /
`stats4b.py` (`s05_stats.out`, `s04_stats_b.out`); they agree.

| quantity | value | label |
|---|---:|---|
| admissible scalar states / oriented claims at G = 75 | 3,708 / 7,416 | [finite-checked] |
| claims surviving the batch-3 system (qcert3 `scan_cases3.json` = qhubcheck) | 789 (416 M, 373 M^T) | [measured] |
| claims surviving the new system (own scan, package driver `lp_regen.run`) | **686** (372 M, 314 M^T) = qjoint = qjointcheck, identical (k, l) | [measured] |
| **newly excluded claims, complete coverage** | **103** (44 M, 59 M^T) | **[certified]** |
| how they fail the final test: only k + l > budget / k > S_e / l > S_o | 86 / 10 / 7 | [finite-checked] |
| their batch-3 shortfall budget - (k + l) = 0 / 1 / 2 | 91 / 8 / 4 | [finite-checked] |
| which bound rose: even k / only odd l | 71 / 32 | [finite-checked] |
| bounds (k, l) monotone (new >= batch 3) on all 7,416 claims | yes | [finite-checked] |
| batch-3-feasible keys: qcert3 lists (859 scan-feasible + 1,177 surviving of the 1,713; union) | 1,437 (re-evaluated: all batch-3-feasible) | [measured] |
| + keys the new scan touched outside the lists that are batch-3-feasible (210 new-feasible, 32 not) | 242 (of 35,650 touched outside) | [measured] |
| **batch-3-feasible keys killed by the new system (complete case coverage)** | **375** (174 M, 201 M^T; by q 1: 5, 3: 12, 4: 246, 5: 12, 6: 23, 7: 23, 8: 40, 9: 11, 10: 3) | **[certified]** |
| of them in the 859 / in the 551 load-bearing / extra | 321 / **163** / 32 | [certified] |
| the 551 load-bearing: still feasible with P1-P5 only / with LIM | 452 / 388 (= qjoint, qjointcheck) | [measured] |
| batch-3-feasible keys surviving | 1,304 | [measured] |
| keys the new scan touched / LP-feasible / load-bearing | 36,573 / 814 / 483 (235 M, 248 M^T) (= qjoint, qjointcheck) | [measured] |
| leaf cases of the killed keys (all covered) | 14,096 | [certified] |
| keys referenced by the 103 claims / of them killed batch-3-feasible keys | 980 / 48 | [finite-checked] |
| referenced keys by kind: package / batch-1 / flat / case | 745 / 101 / 9 / 125 | [certified] |
| leaf cases of the referenced keys; certificate references / direct (Lemma 10.3) references | 18,418; 1,616 / 188 | [certified] |
| **certificates / keys** | **4,361 / 1,307** (745 package, 101 batch-1, 9 flat, 3,506 case) | **[certified]** |
| case certificates: whole hub case (A = a, none) / leaf (A = a, q_D = d) / dark only | 2,350 / 1,156 / 0 | [certified] |
| case certificates by A = 0..10 | 622 / 660 / 734 / 671 / 407 / 139 / 118 / 83 / 55 / 14 / 3 | [certified] |
| leaf certificates by q_D = 0..9 | 202 / 202 / 185 / 166 / 143 / 96 / 73 / 53 / 27 / 9 | [certified] |
| case certificates using P1 / P2 / P3 / P4f / P4h / P5 / LIM; using no joint row | 171 / 333 / 285 / 35 / 76 / 8 / 78; 2,677 | [certified] |
| killed keys with some certificate using P2 / P3 / LIM / P4h / P1 / P4f; using no joint row | 277 / 91 / 78 / 47 / 42 / 32; 5 | [finite-checked] |
| certificates using LIM in case (i) a <= q-2 / (ii) a = q-1 (J1b) / (iii) a = q (J1a) | 0 / **78** / 0 | [certified] |
| J1 certificates by (q, A) | (4, 3): 66 (M), (3, 2): 12 (M^T); all whole hub case | [certified] |
| **covered without J1**: killed keys / claims | **297 / 375; 65 / 103** | [certified] |
| LP scan without LIM: survivors / of the 789 excluded | 724 / 65 (20 M, 45 M^T) | [measured] |
| certificates using PK / FM rows | 98 / 26 | [certified] |
| rows per certificate; multipliers total / nonzero; median / largest of the per-certificate maxima | 31-74; 230,820 / 26,272; 12 / 15,707,997,621,521,517,408 | |
| uncertified (key, case) pairs | 0 | |
| partial file: surviving keys / certificates (whole hub case) / leaves / dead / open | 1,304 / 22,586 (3,963) / 47,987 / 44,058 / 3,929 | [certified] / [measured] |
| open leaves by A = 0..6; keys open only at A = 0; keys with exactly one open leaf | 480 / 782 / 1,091 / 997 / 412 / 137 / 30; 66; 366 | [measured] |

**What "killed" means.** Each of the 375 keys has, for every leaf (A = a, q_D = d) of its tree, a certificate for that
leaf, for (a, none) or for (none, none) (Lemma C1, D.9); that the batch-3 rows leave it feasible is LP status
[measured], never a premise. All 375 are killed by case certificates (none by a flat row: the flat rows are batch 3's).

---

## 2. Files and commands

| file | purpose |
|---|---|
| `PROOF_ADDENDUM_4.md` | the mathematics (D.1-D.12) |
| `CERTIFICATES_CASES75_B4.json` | `gates`, `hub_capacity`, `fm_hist`, `fm_top`, `packing_D3`, `system`, `cases`, `batch3_feasible_keys` (1,679) with sources and `batch3_feasible_extra_keys` (242), `killed_keys` (375), `surviving_keys` (1,304), `claims` (103: state, orientation, new and batch-3 bounds), `certificates` (4,361: key, kind, hub, A, qD, weights, joint_rows_used, uses_J1), `uncertified` (empty), `claims_excluded_without_LIM` (65), `counts` |
| `CERTIFICATES_PARTIAL75_B4.json` | 22,586 certificates for the killed cases of the 1,304 surviving keys; `open_leaves` per key |
| `gen_certs4.py` | generator: new scan with the package driver, batch-3 re-evaluation of the touched keys (`feasible_b3`, unmodified batch-3 system), J1-free-first certificate tree (`certify_key4`), exact re-check, no-LIM scan; needs numpy/scipy |
| `gen_partial4.py` | the partial certificates (whole tree of every surviving key) |
| `check_cases4.py` | **independent checker** (standard library): hand-written rows (check_cases3), brute-force joint rows, proved packing bound, own case tree, coverage of killed keys and claims, J1-free coverage, the partial file; pinned counts |
| `crosscheck4.py` | generator's and checker's matrices identical on every node; survivors, (k, l), key sets vs qcert3, qhubcheck, qjoint, qjointcheck |
| `mutate4.py` | mutation tests; writes `mutate4.json` |
| `stress_ext4.py` | circuits and synthetic two-hub phases; writes `stress_ext4.json` |
| `stats4.py`, `stats4b.py`, `rows_used.py` | statistics of this report; row names used by given keys' certificates |
| `scan_cases4.json`, `keysfull4.json` | all 7,416 claims with batch-3 and new (k, l, dead); 789 / 686 lists; the scan's 814 / 483 keys, the 388 / 452 recounts of the 551 |
| `gen_certs3_copy.py`, `check_cases3_copy.py` | byte-identical copies of qcert3's generator and independent checker |
| `run_all.sh`, `run_all.log`, `s05_*.out` | the complete check and its output; `s01_gen.out`, `s04_partial.out` the generator runs |
| `s01_gen_v1.out`, `s01_gen_v2.out`, `gen_certs4_v{1,2}.log`, `s04_partial_v1.out` | superseded runs (v1: LIM not avoided, 1,437 keys; v2: J1-free first, 1,437 keys); same survivors and claims, kept for the record |
| `write_report.py` | writes this file |
| `SHA256SUMS.txt` | hashes of the deliverables |

**Commands** (from `qcert4/`, `export PYTHONDONTWRITEBYTECODE=1`; times on the loaded machine, `run_all.log`):

```sh
python3 check_cases4.py                 # 58 s  -> "expected counts match ... PARTIAL CERTIFICATES CHECKED ... INDEPENDENT CHECK PASSED"
python3 crosscheck4.py                  # 92 s  -> "systems identical on 22301 (key, case) nodes ... CROSSCHECK PASSED"
python3 mutate4.py 1                    # 115 s -> "MUTATION TEST PASSED"
python3 stress_ext4.py                  # 36 s  -> "STRESS EXT4 PASSED : 316 circuits, 1264 phases, 0 violations; 102792 synthetic phases"
python3 stats4.py; python3 stats4b.py   # 1 s each
sha256sum -c SHA256SUMS.txt
sh run_all.sh                           # all of the above, ends with "QCERT4 ALL CHECKS PASSED"
python3 gen_certs4.py                   # regeneration (numpy + scipy), 492 s: scan 148 s, batch-3 re-evaluation 130 s,
                                        #   1,307 keys certified in 46 s, no-LIM scan 139 s
python3 gen_partial4.py                 # 203 s, 31,445 Farkas LPs
```

**The two code paths.** The generator appends to gen_certs3's `ext_system` (package rows from `certify75.system`,
batch-1, flat, hub A = a, dark) the joint rows in closed form (`joint_rows`, transcribed from `qjoint/qj_lp.py`:
`C(m_lb,2)`, `min(m_lb(u-m_lb), m_ub(u-m_ub))`, `C(u-m_ub,2)`, `[m_lb>=3]`, `[u-m_ub>=3]`, `r m_lb`, LIM; D(n) by the
closed formula; top from the pinned FM histogram). The checker takes check_cases3's hand-written matrix of the case
(every constant and column literal) and appends the joint rows computed as brute-force minima over the integer interval
`[max(0, u-(q-a)), min(u, 3-r)]`, limit types as "the interval is {3 - r}", D(n) by the proof of Lemma D5, top from
check_cases3's pinned rank list. Its case tree is its own (A = 0..q for every q; legal-case test; coverage over all
(q+1)^2 leaves). `crosscheck4.py` compares the two matrices entry by entry.

**J1-free first** (`certify_key4`): package rows; batch-1; flat; then per hub case A = a: (a, none) without LIM; else
every leaf (a, d) without LIM; if some leaf still needs LIM, (a, none) with LIM; else the leaves (without LIM where
possible). A certificate found without LIM is padded by 0 on the LIM row (the last row of a hub case) and re-verified
over the full case system. The field `uses_J1` marks LIM in a case A >= q - 1; the checker recomputes it and the
J1-free coverage.

---

## 3. Crosscheck [finite-checked]

`crosscheck4.py` (92 s): the generator's and the checker's systems are identical (row order, constants, column set,
coefficients) on all **22,301 nodes** -- (none, none), every (A = a, none), every leaf and every (none, d) -- of the 452
keys with case certificates (91,296,843 coefficients). Sets: the batch-3 survivors 789 = qcert3 `scan_cases3.json` =
qhubcheck `lp_qhc_scan_GstarN1HUB2DARKPKFM.json`; the new survivors 686 with identical (k, l) on all 686 = qjoint
`lp_qhc_scan_GstarN1HUB2DARKPKFMJOINTLIM.json` = qjointcheck's verbatim recount (same name) = qjointcheck's own-row
variant `..._JCLIM.json`; the 103 = the difference; the scan's 814 LP-feasible and 483 load-bearing keys = qjoint's and
both qjointcheck keysfull files; of qcert3's 551 load-bearing keys, the 388 still feasible = qjoint / qjointcheck
(JOINTLIM, JCLIM) and, without LIM, the 452 = qjoint / qjointcheck (JOINT, JC); the claims' batch-3 bounds = qcert3's;
the batch-3-feasible set = qcert3's lists + the 242 extra keys; every new-feasible key is in it; every killed key is
certified and none is LP-feasible; the 163 killed load-bearing keys are among the 375.

---

## 4. Mutation tests [finite-checked]

`mutate4.py 1` (115 s), every one of the 4,361 certificates:

| mutation | count | rejected | note |
|---|---:|---:|---|
| negate one nonzero multiplier | 26,272 | 26,272 (100 %) | guaranteed |
| zero one nonzero multiplier | 26,272 | 26,126 (99.4 %) | the 146 survivors re-verified as valid certificates |
| add 1 to one multiplier | 26,272 | 15,932 (60.6 %) | the 10,340 survivors re-verified as valid certificates |
| against a neighbouring key (q+1, z+1, other orientation, h+1), same case | 17,444 | 14,630 (83.9 %) | |
| against a neighbouring case (A +- 1 with the same LIM shape, q_D +- 1 with the same row count) | 6,026 | 1,170 (19.4 %) | survivors are valid there by construction of the check |
| one used row constant + 1 | 4,361 | 1,535 (35.2 %) | rejected iff the weighted right side reaches 0 |
| flip the sign of one used coefficient | 4,343 | 3,164 (72.9 %) | |
| **drop one used joint row** (P1 / P2 / P3 / P4f / P4h / P5 / LIM) | 171 / 333 / 285 / 35 / 76 / 8 / 78 | **100 % each** | every joint row a certificate uses is load-bearing for it |
| joint row constant + 1 (P1 / P2 / P3 / P4f / P4h / P5 / LIM) | as above | 41 / 27 / 50 / 9 / 17 / 2 / **45** | LIM + 1 = two limit hubs allowed (J1b dropped): 45 of the 78 J1 certificates fail |
| P4 constants replaced by the Johnson bound without the parity step | 53 | 7 (13.2 %) | the n = 5 mod 6 refinement is used |
| m-interval widened to min(u, 4 - r) (H2 weakened to H1's capacity) | 821 | 664 (80.9 %) | |
| case A = 0 / 1 certificate checked in batch 3's merged case A <= 1 without joint rows | 1,241 | 77 (6.2 %) | the exact split or a joint row is needed there |
| drop one case certificate of a killed key | 375 | 375 (100 %) | guaranteed (no redundant node) |
| drop one referenced certificate of a claim | 103 | 103 (100 %) | guaranteed |
| claim lower_even - 1 / lower_odd - 1 / lower_even + 1 | 103 / 103 / 103 | 96 / 103 / 103 | 7 claims hold by the odd side alone |

Every mutation that must be rejected was rejected; every accepted mutation was re-verified as a genuine certificate.

---

## 5. Stress extension [finite-checked; positive control only]

**Circuits** (`stress_ext4.py`, part A, 5 s): 13 package controls + 303 real circuits (`bridge/profiles.json`,
`reconstruct(values, 'ymax')`), orbit steps 0-3: **316 circuits, 1,264 phases**, q = 7..16, own odd-graph extraction
(q asserted equal to the package's `analyse`; Lemmas 4.1, 4.5 asserted on every phase). Per phase, with the phase's
A: strong forms P1-P5 with the actual m_i, H2, HUB2's column deletion, J1 (pairs of limit hubs sharing a label), LIM
(limit hubs carrying all hub-only labels); the LP rows of hub case A = a from **both** implementations (asserted
identical on every type met) with the phase's type counts; per helper (20,745), m_i in its type's interval and every LP
coefficient <= the helper's actual term. **0 violations.** Minimum slack (controls / real): P1 0 / 0, P2 0 / 0, P3 15 /
21, P4f 0 / 0, P4h 5 / 7, P5 0 / 0, H2 1 / 1, HUB2 7 / 7, J1 0 / 0, LIM 1 / 1; LP P3 21 / 21, LP P4h 7 / 7, LP LIM 1 / 1,
the other LP rows 0. A = 0 on every phase and no phase has a limit hub (as in batches 1-3): the rows are exercised
through the hub-only class only.

**Synthetic two-hub phases** (part B, 31 s): qjointcheck's builder `jc_circ.synthetic` on `jc_geo`'s limit
configurations, every kind (hub-only sharing, same full-met label, different labels at a shared full helper, sub-limit
(0,2)-(0,2) same-label pairs), at most 6,000 phases per kind: **102,792 phases, 11,912 with independent F_joint**. Every
realizable phase satisfies every strong and LP row (0 violations; P2, P3, P4h, H2, J1, LIM tight on some); every phase of
the J1-excluded kinds (both hubs at the limit, sharing a label) is dependent and violates the LP row LIM (0 not flagged);
no synthetic phase has a type outside the case's columns. Local configurations, not circuits.

---

## 6. The partial certificates of the surviving keys [certified] / [measured]

`gen_partial4.py` walks the whole case tree of each of the 1,304 surviving batch-3-feasible keys: 22,586 certificates
(3,963 for a whole hub case), 31,445 Farkas LPs, 0 failures, largest weighted right side -1. `check_cases4.py` checks
every certificate and that every one of the 47,987 leaves is either certified dead (44,058) or listed open (3,929),
never both, and that every surviving key has an open leaf. Open leaves by A: 0: 480, 1: 782, 2: 1,091, 3: 997, 4: 412,
5: 137, 6: 30; 66 surviving keys are open only at A = 0, 366 at exactly one leaf. The open leaves are LP-feasible by
HiGHS [measured]; nothing is excluded by this file. Joint rows used: LIM 1,586, P3 538, P1 170, P2 94, P4h 76, P4f 69,
P5 9 (LIM is not avoided in this file).

---

## 7. What remains open

- **686 oriented claims (372 M, 314 M^T) remain open at G = 75 by LP status [measured]; no bound improvement.** Their
  shortfall budget - (k + l) is 0 for 382, 1 for 221, 2 for 59, 3 for 24; set and (k, l) identical to qjoint's and
  qjointcheck's.
- Cumulative: 1,508 (package) -> 1,313 (batch 1) -> 996 (batch 2) -> 789 (batch 3) -> **686 (this batch)**; 195 + 317 +
  207 + 103 = 822 of the 1,508 claims the package rows leave are certified-excluded; 686 are not. Proposition 11.1's
  argument at G = 75 would need all of them.
- The scan's 814 LP-feasible / 483 load-bearing keys (by q 1: 3, 2: 58, 3: 80, 4: 64, 5: 147, 6: 89, 7: 27, 8: 15)
  have no certificate under this system (they are LP-feasible). The 101 load-bearing keys qjoint found LP-feasible but
  integer-infeasible (MILP oracle, status not recorded) are not certified: that needs a branch-and-bound certificate.
- 38 of the 103 excluded claims and 78 of the 375 killed keys rest on finite fact J1 (part J1b); J1 was not re-run in
  this batch (both implementations' logs were read).
- Whether a normalized circuit with A >= 1 exists is open; every measured phase has A = 0.

---

## 8. Trust ledger

**Relied on, not re-proved here [read, not checked]:** PROOF.md Lemmas 1.1, 4.1-4.7, 10.1-10.4, the proofs of (L7) /
(L9) per label, section 11; Addenda A (batch-1 rows, (L7\*)), B (DARK split, Lemma C1, coverage), C (H2, HUB2, PK, FM)
and the finite facts F2-F14, H2, FM as certified / checked there; **finite fact J1 as [finite-checked] by qjoint
(`qj_limit.py`) and qjointcheck (`jc_geo.py`, two modes)** -- logs read, programs not re-run; qcert3's lists as the
batch-3 LP status of the listed keys and claims; the bridge reconstruction as faithful gate lists; the exactness of
D(n, 3, 2) for all n (Spencer 1968; not needed).

**Proved in the addendum [proved]:** Lemma J with the spanning-tree statement; the consequence of J1 (no two limit hubs
share a missing label); Lemma P (P1-P5); Lemma D5; the LP forms of the hub case A = a (per-row relaxation, concave term
at an endpoint); row LIM in its three cases; the exact split's exhaustiveness and soundness; monotonicity w.r.t. batch
3; Lemma C1 for the new case systems.

**Finite-checked here:** the identity of the two system definitions on 22,301 nodes; the set identities with qcert3,
qhubcheck, qjoint, qjointcheck (686 / 103 / 814 / 483 / 388 / 452); batch-3 feasibility of the 1,437 listed keys
(re-evaluated) and of the 242 extra keys; the packing bound attained for n <= 7; the mutation statistics; the stress
results (1,264 phases, 102,792 synthetic phases).

**Certified by the files:** for each of the 1,307 keys and each case node carrying a certificate, the case system at
G = 75 has no nonnegative real solution; each of the 375 killed keys is covered in every leaf; for each of the 103
claims every (q, z) below the stated k, l is excluded by (4.4), Lemma 10.3 or a covered key, and k > S_e or l > S_o or
k + l > a + b + 2G - 192; 297 keys and 65 claims are covered without any certificate that uses J1; 44,058 leaves of the
surviving keys are dead.

**What follows on its own.** Granting the package, Addenda A-C, finite fact J1 and the proofs of Addendum D: no tail of
the orbit at G = 75 has one of the 103 excluded (profile, orientation) pairs (65 of them without J1). Nothing about L(M)
follows, because 686 pairs remain.

---

## 9. Caveats

- As in batches 1-3, the claims' bounds k, l come from the package driver with LP feasibility; the checker verifies the
  infeasible side and the final test only. A claim's k, l could be larger than found, never smaller.
- Two certificates have very large multipliers (largest 15,707,997,621,521,517,408; the next 41,139,491,049,195, then
  227,304); they come from the rationalization of LP vertices (denominators up to 10^12) and are exact integers checked
  as such; the median per-certificate maximum is 12.
- LP status decides which keys and cases are attempted, the extra 242 keys, the open leaves and the "without LIM"
  scan; no exclusion rests on it.
- The partial file does not avoid LIM; its J1 dependence is not separated.
- The run sequence: v1 (no LIM avoidance) and v2 (J1-free first, on qcert3's 1,437 keys) were superseded by the final
  run (J1-free first, 1,679 keys); all three give the same 686 survivors, the same 103 claims and the same killed keys
  on the common key set; only the final files are deliverables.
- The new rows are exercised by circuits only through the hub-only class (A = 0 everywhere); limit hubs and A >= 1 occur
  only in synthetic local configurations.

---

## 10. Labels, in one table

| statement | label |
|---|---|
| Lemma J (spanning trees); J1's consequence; Lemma P; Lemma D5; LP forms; row LIM; exact split; Lemma C1 | [proved] (PROOF_ADDENDUM_4.md) |
| finite fact J1 ((J1a), (J1b)) | [finite-checked] (qjoint `qj_limit.py`; qjointcheck `jc_geo.py`) [read here] |
| 4,361 certificates; coverage of 375 killed keys (163 load-bearing) and of 103 claims; largest rhs -1 | [certified] (`check_cases4.py`, `gen_certs4.py`) |
| 297 keys / 65 claims covered without J1; LIM only in case (ii); five keys killed by the split alone | [certified] |
| 22,586 partial certificates; 44,058 dead leaves of the surviving keys | [certified]; 3,929 open leaves [measured] |
| the two system definitions coincide on 22,301 case nodes | [finite-checked] (`crosscheck4.py`) |
| 686 / 103 claims, 814 / 483 scan keys, 388 / 452 recounts = qjoint and qjointcheck | [finite-checked] (`crosscheck4.py`) |
| 0 violations on 1,264 phases and 102,792 synthetic phases | [finite-checked] (positive control) |
| 686 claims remain open at G = 75 | [measured] |
| any bound beyond 75 | **not claimed** |
'''
out = Path(__file__).resolve().with_name('REPORT.md')
out.write_bytes(REPORT.replace('\r\n', '\n').encode('utf-8'))
print('wrote', out, len(REPORT), 'chars')
