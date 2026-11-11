# Pilot report: complete local realizability enumeration, M^T q = 3 block at G = 75

Proof agent, 2026-11-10 / 2026-11-11. Work folder `~/xs-campaigns/2026-11-10-proof/pilot/`. **Final results:
`results_final/` (per-leaf JSON), `RESULTS_TABLE.md` (one row per leaf), `farkas_final/` and `farkas_final.json`,
`claims_final.json`.** `results/` is the first run (2026-11-10), kept for the record and superseded.

**The lower bound stays 75.** Nothing here proves or suggests a bound above 75: 272 of the 280 open claims at G = 75 stay
open by LP status even if every exclusion below is accepted, and one open claim is enough to stop the argument.

Tags: **[proved]** (written proof, package lemmas and finite facts as black boxes), **[certified]** (exact integer
certificate checked in exact arithmetic), **[finite-checked]** (exhaustive program named), **[measured]** (solver status),
**[read, not checked]**.

## 0. Result in one paragraph

The block has 66 LP-feasible keys (h, y, F, 'Mt', 3, z) with 207 open leaves (A, q_D) [measured, `lp_bounds.py`]. Only 21 of
these keys (48 open leaves) lie on the ladder of one of the 280 open claims (`../scope/ladders.json`); the other 45 keys
(159 leaves) are on no ladder. Outcome of the enumeration of PILOT_SPEC.md: **186 leaves EXCLUDED, 21 SURVIVING, 0
UNRESOLVED.** All 48 leaves of the 21 ladder keys are EXCLUDED, so all 21 ladder keys are excluded (4 at grade
[certified], 15 [finite-checked], 2 [measured]); the 21 SURVIVING leaves all belong to 14 keys that are on no ladder. If
the exclusions were accepted, the 8 claims that depend on the block would close (7 of them without any [measured] step);
272 claims would remain open. One error that could have produced a false exclusion was found in the enumerator and
corrected before the second pass; it changed no result (section 3.4).

## 1. Specification and completeness argument

`PILOT_SPEC.md` (written before any enumeration; section 11 is an addendum of 2026-11-11). Object: the label configuration
of a phase (three missing labels; every helper with u >= 1 with mask, represented triples, label set; ends b = mask +
label; statuses full-met / hub-only / dark). Rules, each a necessary condition of a normalized circuit: R1 (Lemma 1.1),
R2 (4.1), R3 (4.4, F3), R4 (4.5, D.8), R5 (4.6), R6 (10.2, B.4), R7 (Lemma J*: the joint family of the whole
configuration is independent; proved in the spec, it contains Lemma J of D.2, (C1), H2, J1/LIM, F4, (L7) per label as
sub-statements), R8 (the leaf's combined case system of `check_combined75.matrix` with the configuration's (r,u) counts
imposed is LP-feasible), R8-int (the same with integrality). Completeness (spec section 7): every hypothetical circuit of
the leaf induces an object; its skeleton is produced by step S; a rotation of the object is reached by step G unless a
rule it satisfies prunes it, which cannot happen (R7 is hereditary, Lemma 3.8); helpers with r = 0, u = 1 and components
with at most one anchored helper and acyclic incidence are provably unconstrained (Lemmas 3.9, 3.10) and are not branched
over. Symmetry used: the byte rotation only (Lemma 4.1'; rho(B) = B [finite-checked], `geo_q3.py`).

Not complete / restrictions of the conclusion: the rows of the case systems are [read, not checked]; R8-int rests on MILP
solver status [measured]; the enumeration is one implementation (section 7 lists what each grade rests on).

## 2. Search size: estimate and actual

Estimate written before the run (`estimate.log`, per leaf and skeleton: root choices times branching per level from the
finite tables, without R7): upper bound 2.3e30 nodes, refined estimate 8.7e14. Both ignore R7 and the dead-role test and
were useless for budgeting; the run was therefore capped per skeleton and calibrated on six leaves (`calib*.log`).

Actual (final): step S 256,180 nodes; 2,790 LP-feasible skeletons, 2,480 after R8-int (808 distinct up to the key, since
step G does not depend on the key); step G 4.43e8 nodes over the leaves (each distinct skeleton enumerated once and
shared). Pruning, step S: LP monotone 1,120,237, LP exact 126,033 (31,490 distinct LP decisions "infeasible"), R5 518,082,
(B-1) 34,547, R4 256; R8-int removed 310 skeletons. Step G: R7 1.45e9, rank filter (D-l) 2.16e9, role without candidate
1.63e8, product phase R7 1.63e8 and R1 7.8e7, label clash 1.3e6. Skeleton outcomes in the final files: 2,128 done, 352
capped / timed out / not run -- all of the latter in leaves that are SURVIVING through another skeleton (no leaf is
UNRESOLVED). Per-leaf node counts and pruning histograms: `RESULTS_TABLE.md`; first pruned configurations at the deepest
level recorded per skeleton: field `deepest_pruned` of the leaf files (the recorder keeps only the first prunes at the
running maximal depth, so these samples are shallow).

CPU: first run 2,793 s; second pass 5,791 s (step S 114, rounds A/B 4,759, round C 111, round D 368, round E 435; within
the 2 CPU-hours allowed for it); Farkas certificates 810 s; controls P5 849 s + 910 s, bounded brute force 30 s (plus
about 700 s for an attempt with a too large sub-domain, aborted); day-1 calibrations, estimates and controls about 2,100 s,
and about one CPU-hour lost in the full-domain brute force that ran out of memory. Total about 5.5 CPU-hours, of which
2.4 for the enumeration itself (the brief's budget for the block was 4). All at nice 10; from 2026-11-11 every process
under `ulimit -v 8000000`, at most 8 in parallel.

## 3. Controls

### 3.1 Rules accept valid objects, reject invalid ones (2026-11-10; `controls_q3.py`, `verify_q3.py`) [finite-checked]

| control | outcome |
|---|---|
| P1 real circuits: 316 circuits, 1,264 phases (A = 0, q = 7..16), 17,342 carriers; every phase object and every 3-label sub-configuration (344,432) against R1-R7 | 0 failures |
| P2 two anchored hubs sharing a hub-only label (`share_pairs.json` witnesses, both label choices) | 30 / 30 accepted |
| P3 two limit hubs sharing a full helper at different labels (D.3 examples) | 5 / 5 accepted |
| P4 counts of an integer solution of `leaves_int.json` | accepted by R8 and R8-int |
| N1 finite fact J1 reproduced with the rule checker: J1b 208,272 pairs, J1a 14,816 pairs | all rejected by R7 (0 independent) |
| N2 helper carrying a label twice; N3 two hubs sharing two labels | rejected by R2; by R5 |
| N4 4 - r full helpers at a limit hub (H2), 14,976 objects | all rejected by R7 |
| N5 counts violating a row (a full-met label in case A = 0) | rejected by R8 |

### 3.2 P5, search-level positive control (2026-11-11; `controls_p5.py`, `controls_p5b.py`) [finite-checked]

Objects that do not come from the enumerator, each validated by `verify_q3` (R1-R7), then: (S) step S, with the LP
replaced by the object's own counts, must produce its skeleton; (G) step G on that skeleton, R8 and R8-int off, guided to
the object (the guide only discards branches that differ from the target; every rule of the search still runs on the
path), must return its constrained part exactly for one of the four rotations; (U) for a sample, the unguided complete
search must contain it.

- 9,651 objects: 9,124 hereditary 3-label sub-configurations of real phases (both orientations, each searched with its own
  geometry; chosen to cover 2,614 distinct skeleton shapes; 60,299 sub-configurations with two or more dark labels were
  skipped as outside the enumerator's domain, every leaf of the block having q_D <= 1) and 527 planted M^T objects with
  full-met labels (75 limit hubs with three full helpers, 152 sub-configurations of two limit hubs sharing a full helper
  at different labels, 150 with A = 1 and 150 with A = 2 mixing a full-met and a shared hub-only label).
- 9,026 of them have a constrained part (2,476 distinct shapes; 625 are free-only and test only step S). **Misses: step S
  0, step G 0.** Unguided: 80 run, 33 complete and all 33 contain the object, 47 hit the 10 s cap (inconclusive).
- Shapes covered (number of constrained objects): one / two / three segments 4,045 / 3,989 / 992; a label with three or
  more constrained carriers 5,269; a helper with u = 2: 3,699, with u = 3: 254; r = 0 helpers with u >= 2 in the
  constrained part 821; r = 0, u = 1 riders 2,663; a dark label 3,253; a free component beside a constrained one 5,866;
  A = 1 / 2 / 3: 150 / 150 / 227; a full helper with u = 2: 59.
- Triangles (three u = 2 helpers pairwise sharing the three labels) do not occur in real phases; `controls_p5b.py` plants
  240 of them from the weight-6 zero-sum boundary words (construction independent of the enumerator): **0 misses** for
  (S) and guided (G); their 60 unguided runs all hit the 15 s cap (inconclusive).
- Not covered: triangles with two or three r = 2 hubs (222 of the planted ones have r = (1,1,1), 16 one r = 2 hub) -- the
  shape of several witnesses of section 5; objects with a full-met label AND a dark label; objects with two or more dark
  labels (outside the domain); full-met objects other than those derived from limit configurations; and the unguided
  check is conclusive on 33 objects only. The label-indexed join used in rounds D and E has its own validation (3.4).

A first run of P5 flagged every object in (S); the cause was the control comparing tuples with lists
(`controls_p5_run1.log`); corrected, rerun in full.

### 3.3 Brute-force comparison, memory-bounded (`controls_bf2.py`) [finite-checked]

Sub-case: two (2,2) hubs sharing one label and nothing else. Sub-domain defined on the object: shared label in the
rotation closure of {h + b : h in 40 fixed two-triple masks, b in B} (8,126 labels), both private labels of weight <= 2.
The naive program (nested loops over all 616 two-triple masks, all triple pairs and ends, one full rank computation per
complete configuration, nothing imported from the enumerator) and the pruned search without and with the rotation
reduction (survivors expanded by the four rotations) each stream their canonical lines to a file; `sort -u | sha256sum`:
**95,858 distinct configurations, identical SHA-256 (aab7b047...) in all three.** (The full-domain version of 2026-11-10
held everything in memory and was killed at 28 GB; a first bounded attempt with weight <= 6 produced 33.6 million lines
and was stopped; its partial output files, 4.7 GB written by this agent the same hour, were removed.)

### 3.4 Errors found in the enumerator, and the validation of the join

1. **Product phase placed some helpers twice** (multi-segment skeletons: r = 0, u >= 2 helpers already placed inside a
   segment were placed again in the product phase). This could turn a realizable skeleton into "no combination", i.e. a
   false exclusion. Found by reading the code before P5 was written; fixed (`patch_20261111.py`; first-run code kept as
   `enum_q3_pass1_snapshot.py`). The second pass reused a first-run outcome only where the error could not act (single
   segment, or no such helper, or a segment with no realization); the one affected skeleton was re-run and its outcome
   did not change. P5's guided step G runs on the corrected code and covers 4,981 multi-segment objects.
2. **The per-leaf record of the first run lost the list of skeletons** (bookkeeping only; rebuilt in the second pass, whose
   step S agrees with the first run on all 198 leaves it had completed: 0 mismatches).
3. **Join (rounds D, E; `pass2d_q3.py`).** For multi-segment skeletons whose plain product of segment realizations was
   capped, the segment realizations are indexed by label values and label combinations for which a deferred r = 0 helper
   has no possible mask ((D-b), (D-2), R1) are skipped before the product; the rest goes through the unchanged product
   code. Validation: V1, 36 skeletons decided by the plain product, same verdict (all 36 "no realization", so V1 tests
   agreement on empty results only); V2, 445 real-phase objects with several segments and a deferred helper, guided: all
   reached. **Three exclusions rest on the join**: (16,0,1..3,'Mt',3,3) at (A, q_D) = (0,0), each through two skeletons
   (rounds D and E; 3.3 and 61 million combinations exhausted). Two skeletons found realizable by the join have verified
   witnesses.

## 4. Per-leaf results

`RESULTS_TABLE.md` has all 207 rows (key, A, q_D, layer, integer status of the leaf's case system from `ladders.json`,
result, how excluded, grade, skeleton counts, nodes, LP certificates, pruning histograms). Summary:

| (A, q_D) | open leaves | on ladder keys | EXCLUDED | SURVIVING | UNRESOLVED |
|---|---|---|---|---|---|
| (0, 0) | 48 | 20 | 34 | 14 | 0 |
| (0, 1) | 21 | 1 | 21 | 0 | 0 |
| (1, 0) | 49 | 15 | 43 | 6 | 0 |
| (1, 1) | 30 | 2 | 30 | 0 | 0 |
| (2, 0) | 34 | 8 | 33 | 1 | 0 |
| (2, 1) | 25 | 2 | 25 | 0 | 0 |
| all | 207 | 48 | 186 | 21 | 0 |

Grades of the 186 exclusions: 103 [finite-checked], 78 [certified], 3 [measured] (MILP used), 2 [measured].


How the 186 exclusions were obtained: 78 by step S with LP prunes only (no skeleton passes R4-R6, (B-1), R8); 2 by step S
with R8-int ((12,7,0,'Mt',3,1) and (15,3,2,'Mt',3,1), both at (A, q_D) = (1,0): the only LP-feasible skeletons, two
each, have no integer solution by MILP status); 106 by step G (every remaining skeleton has no realization), of which 3
also used R8-int to remove other skeletons ((15,2,1) (0,0); (15,4,1) (1,0); (15,4,2) (2,0)).

The 48 open leaves of the 21 ladder keys (all EXCLUDED):

| key | A | q_D | int | excluded by | grade | skeletons LP / after R8-int | step-S nodes | step-G nodes | LP certificates |
|---|---|---|---|---|---|---|---|---|---|
| (12, 5, 0, 'Mt', 3, 3) | 1 | 0 | feasible | step G (geometry) | [finite-checked] | 2 / 2 | 38 | 60412 | 56/56 |
| (12, 5, 0, 'Mt', 3, 3) | 1 | 1 | feasible | step S (LP) | [certified] | 0 / 0 | 14 | 0 | 44/44 |
| (12, 5, 0, 'Mt', 3, 3) | 2 | 0 | feasible | step G (geometry) | [finite-checked] | 2 / 2 | 124 | 35470 | 103/103 |
| (12, 5, 0, 'Mt', 3, 3) | 2 | 1 | feasible | step S (LP) | [certified] | 0 / 0 | 40 | 0 | 79/79 |
| (12, 5, 1, 'Mt', 3, 3) | 0 | 0 | feasible | step G (geometry) | [finite-checked] | 1 / 1 | 8 | 1330953 | 22/22 |
| (12, 5, 1, 'Mt', 3, 3) | 0 | 1 | feasible | step S (LP) | [certified] | 0 / 0 | 2 | 0 | 11/11 |
| (12, 5, 1, 'Mt', 3, 3) | 1 | 0 | feasible | step G (geometry) | [finite-checked] | 2 / 2 | 62 | 60412 | 77/77 |
| (12, 5, 1, 'Mt', 3, 3) | 1 | 1 | feasible | step S (LP) | [certified] | 0 / 0 | 14 | 0 | 44/44 |
| (12, 5, 1, 'Mt', 3, 3) | 2 | 0 | feasible | step G (geometry) | [finite-checked] | 5 / 5 | 184 | 3351093 | 133/133 |
| (12, 5, 1, 'Mt', 3, 3) | 2 | 1 | feasible | step S (LP) | [certified] | 0 / 0 | 40 | 0 | 79/79 |
| (15, 1, 0, 'Mt', 3, 3) | 0 | 0 | feasible | step G (geometry) | [finite-checked] | 4 / 4 | 518 | 875226 | 128/128 |
| (15, 1, 1, 'Mt', 3, 3) | 0 | 0 | feasible | step G (geometry) | [finite-checked] | 9 / 9 | 1002 | 4653719 | 210/210 |
| (15, 1, 1, 'Mt', 3, 3) | 1 | 0 | feasible | step G (geometry) | [finite-checked] | 12 / 12 | 2013 | 286376 | 305/305 |
| (15, 1, 1, 'Mt', 3, 3) | 2 | 0 | feasible | step G (geometry) | [finite-checked] | 4 / 4 | 1877 | 1254 | 244/244 |
| (15, 1, 2, 'Mt', 3, 3) | 0 | 0 | feasible | step G (geometry) | [finite-checked] | 9 / 9 | 1002 | 4653719 | 210/210 |
| (15, 1, 2, 'Mt', 3, 3) | 1 | 0 | feasible | step G (geometry) | [finite-checked] | 12 / 12 | 2013 | 286376 | 305/305 |
| (15, 1, 2, 'Mt', 3, 3) | 2 | 0 | feasible | step G (geometry) | [finite-checked] | 4 / 4 | 2021 | 1254 | 267/267 |
| (15, 1, 3, 'Mt', 3, 3) | 0 | 0 | feasible | step G (geometry) | [finite-checked] | 9 / 9 | 1002 | 4653719 | 210/210 |
| (15, 1, 3, 'Mt', 3, 3) | 1 | 0 | feasible | step G (geometry) | [finite-checked] | 12 / 12 | 2013 | 286376 | 305/305 |
| (15, 1, 3, 'Mt', 3, 3) | 2 | 0 | feasible | step G (geometry) | [finite-checked] | 4 / 4 | 2021 | 1254 | 267/267 |
| (15, 2, 1, 'Mt', 3, 2) | 0 | 0 | feasible | step G (geometry) | [measured] (MILP used) | 7 / 4 | 630 | 875226 | 159/159 |
| (15, 2, 2, 'Mt', 3, 2) | 0 | 0 | feasible | step G (geometry) | [finite-checked] | 7 / 7 | 630 | 4571629 | 159/159 |
| (15, 2, 2, 'Mt', 3, 2) | 1 | 0 | feasible | step G (geometry) | [finite-checked] | 2 / 2 | 422 | 260598 | 153/153 |
| (15, 2, 3, 'Mt', 3, 2) | 0 | 0 | feasible | step G (geometry) | [finite-checked] | 7 / 7 | 630 | 4571629 | 159/159 |
| (15, 2, 3, 'Mt', 3, 2) | 1 | 0 | feasible | step G (geometry) | [finite-checked] | 2 / 2 | 422 | 260598 | 153/153 |
| (15, 2, 4, 'Mt', 3, 2) | 0 | 0 | feasible | step G (geometry) | [finite-checked] | 7 / 7 | 630 | 4571629 | 159/159 |
| (15, 2, 4, 'Mt', 3, 2) | 1 | 0 | feasible | step G (geometry) | [finite-checked] | 2 / 2 | 422 | 260598 | 153/153 |
| (15, 3, 2, 'Mt', 3, 1) | 0 | 0 | feasible | step G (geometry) | [finite-checked] | 7 / 7 | 630 | 4571629 | 159/159 |
| (15, 3, 2, 'Mt', 3, 1) | 1 | 0 | infeasible | step S (LP + MILP) | [measured] | 2 / 0 | 422 | 0 | 153/153 |
| (15, 3, 3, 'Mt', 3, 1) | 0 | 0 | feasible | step G (geometry) | [finite-checked] | 7 / 7 | 630 | 4571629 | 159/159 |
| (15, 3, 3, 'Mt', 3, 1) | 1 | 0 | feasible | step G (geometry) | [finite-checked] | 2 / 2 | 422 | 260598 | 153/153 |
| (15, 3, 4, 'Mt', 3, 1) | 0 | 0 | feasible | step G (geometry) | [finite-checked] | 7 / 7 | 630 | 4571629 | 159/159 |
| (15, 3, 4, 'Mt', 3, 1) | 1 | 0 | feasible | step G (geometry) | [finite-checked] | 2 / 2 | 422 | 260598 | 153/153 |
| (16, 0, 0, 'Mt', 3, 3) | 0 | 0 | feasible | step G (geometry) | [finite-checked] | 6 / 6 | 1416 | 160859 | 199/199 |
| (16, 0, 0, 'Mt', 3, 3) | 1 | 0 | feasible | step G (geometry) | [finite-checked] | 11 / 11 | 2868 | 126747 | 356/356 |
| (16, 0, 1, 'Mt', 3, 3) | 0 | 0 | feasible | step G (geometry) | [finite-checked] | 16 / 16 | 3945 | 672687 | 369/369 |
| (16, 0, 1, 'Mt', 3, 3) | 1 | 0 | feasible | step G (geometry) | [finite-checked] | 53 / 53 | 9357 | 1240382 | 584/584 |
| (16, 0, 1, 'Mt', 3, 3) | 2 | 0 | feasible | step G (geometry) | [finite-checked] | 8 / 8 | 4704 | 16816 | 320/320 |
| (16, 0, 2, 'Mt', 3, 3) | 0 | 0 | feasible | step G (geometry) | [finite-checked] | 16 / 16 | 3945 | 672687 | 369/369 |
| (16, 0, 2, 'Mt', 3, 3) | 1 | 0 | feasible | step G (geometry) | [finite-checked] | 56 / 56 | 9439 | 1240889 | 606/606 |
| (16, 0, 2, 'Mt', 3, 3) | 2 | 0 | feasible | step G (geometry) | [finite-checked] | 15 / 15 | 10241 | 41487 | 498/498 |
| (16, 0, 3, 'Mt', 3, 3) | 0 | 0 | feasible | step G (geometry) | [finite-checked] | 16 / 16 | 3945 | 672687 | 369/369 |
| (16, 0, 3, 'Mt', 3, 3) | 1 | 0 | feasible | step G (geometry) | [finite-checked] | 56 / 56 | 9439 | 1240889 | 606/606 |
| (16, 0, 3, 'Mt', 3, 3) | 2 | 0 | feasible | step G (geometry) | [finite-checked] | 15 / 15 | 10241 | 41487 | 498/498 |
| (16, 1, 3, 'Mt', 3, 2) | 0 | 0 | infeasible | step S (LP) | [certified] | 0 / 0 | 348 | 0 | 104/104 |
| (16, 2, 2, 'Mt', 3, 1) | 0 | 0 | infeasible | step S (LP) | [certified] | 0 / 0 | 348 | 0 | 104/104 |
| (16, 2, 3, 'Mt', 3, 1) | 0 | 0 | infeasible | step S (LP) | [certified] | 0 / 0 | 348 | 0 | 104/104 |
| (16, 2, 4, 'Mt', 3, 1) | 0 | 0 | infeasible | step S (LP) | [certified] | 0 / 0 | 348 | 0 | 104/104 |


Of these 48 leaves, 43 are integer-feasible as case systems (`ladders.json` [measured]) and 5 integer-infeasible; the
enumeration excludes all of them.

## 5. Witnesses (the 21 SURVIVING leaves)

| key | A | q_D | skeletons after R8-int | done | with a realization | not decided (cap) | witnesses stored | verified | MILP-feasible counts |
|---|---|---|---|---|---|---|---|---|---|
| (13, 5, 0, 'Mt', 3, 2) | 0 | 0 | 5 | 3 | 1 | 2 | 5 | 5 | 5 |
| (13, 5, 0, 'Mt', 3, 2) | 1 | 0 | 23 | 23 | 6 | 0 | 30 | 30 | 30 |
| (13, 5, 0, 'Mt', 3, 2) | 2 | 0 | 16 | 14 | 1 | 2 | 5 | 5 | 5 |
| (15, 3, 0, 'Mt', 3, 2) | 0 | 0 | 26 | 20 | 3 | 6 | 7 | 7 | 7 |
| (15, 4, 0, 'Mt', 3, 1) | 0 | 0 | 10 | 8 | 1 | 2 | 1 | 1 | 1 |
| (15, 4, 1, 'Mt', 3, 1) | 0 | 0 | 29 | 23 | 4 | 6 | 12 | 12 | 12 |
| (15, 4, 2, 'Mt', 3, 1) | 0 | 0 | 107 | 86 | 11 | 21 | 47 | 47 | 47 |
| (15, 4, 2, 'Mt', 3, 1) | 1 | 0 | 88 | 77 | 1 | 11 | 5 | 5 | 5 |
| (15, 4, 3, 'Mt', 3, 1) | 0 | 0 | 116 | 94 | 11 | 22 | 47 | 47 | 47 |
| (15, 4, 3, 'Mt', 3, 1) | 1 | 0 | 121 | 109 | 1 | 12 | 5 | 5 | 5 |
| (15, 4, 4, 'Mt', 3, 1) | 0 | 0 | 116 | 94 | 11 | 22 | 47 | 47 | 47 |
| (15, 4, 4, 'Mt', 3, 1) | 1 | 0 | 121 | 109 | 1 | 12 | 5 | 5 | 5 |
| (16, 2, 0, 'Mt', 3, 2) | 0 | 0 | 74 | 56 | 4 | 18 | 8 | 8 | 8 |
| (16, 3, 0, 'Mt', 3, 1) | 0 | 0 | 22 | 15 | 1 | 7 | 1 | 1 | 1 |
| (16, 3, 1, 'Mt', 3, 1) | 0 | 0 | 53 | 41 | 2 | 12 | 6 | 6 | 6 |
| (16, 3, 2, 'Mt', 3, 1) | 0 | 0 | 174 | 130 | 15 | 44 | 67 | 67 | 67 |
| (16, 3, 2, 'Mt', 3, 1) | 1 | 0 | 61 | 57 | 1 | 4 | 5 | 5 | 5 |
| (16, 3, 3, 'Mt', 3, 1) | 0 | 0 | 226 | 168 | 15 | 58 | 67 | 67 | 67 |
| (16, 3, 3, 'Mt', 3, 1) | 1 | 0 | 112 | 105 | 1 | 7 | 5 | 5 | 5 |
| (18, 1, 0, 'Mt', 3, 2) | 0 | 0 | 43 | 20 | 2 | 23 | 2 | 2 | 2 |
| (18, 1, 1, 'Mt', 3, 2) | 0 | 0 | 222 | 161 | 2 | 61 | 2 | 2 | 2 |


All 21 leaves belong to keys that are on no ladder of the 280 open claims. 379 witnesses are stored
(`results_final/leaf_*.json`, field `witnesses`); every one passes `verify_q3` (R1-R8, both rank routines, a fresh LP) and
**every one has MILP-feasible counts** (status 0, the integer solution re-checked exactly against every row). 27 distinct
(skeleton, A, q_D) shapes have realizations; the survivors per skeleton were capped at 200, so no total count is given.

Example (leaf (13,5,0,'Mt',3,2), A = 0, q_D = 0; skeleton (1,{0,1}), (2,{0,2}), (2,{1,2}), (2,{2}): a triangle plus one hub):

| helper | r | labels | ends | triples (64-bit boundary subsets) |
|---|---|---|---|---|
| 0x20204 | 2 | l0, l2 | 0x1, 0x2 | 0x20204, 0x2020000040000 |
| 0x2020206 | 2 | l1, l2 | 0x1010203, 0x2000000 | 0x204000002, 0x20000000600 |
| 0x1000104 | 1 | l0, l1 | 0x1020301, 0x2030101 | 0x1000104 |
| 0x4040004 | 2 | l2 | 0x4060202 | 0x4040004, 0x40000000808 |

labels l0 = 0x20205, l1 = 0x3030005, l2 = 0x20206 (all bright hub-only); joint family of 11 vectors, rank 11 by both
routines; counts (2,2): 2, (1,2): 1, (2,1): 1; an integer solution of the leaf's case system with these counts:
n(1,2,1) = 1, n(2,1,1) = 1, n(2,2,0) = 2, n(3,0,0) = 7, n(3,0,1) = 2, y0 = 2, y1 = 1, y2 = 2.

What the witnesses show: for these leaves the necessary conditions used here -- the rows of the combined case system with
integer counts, Lemmas 4.1, 4.5, 4.6, and the independence of the joint gate-equation family of ALL helpers with u >= 1
(Lemma J*, which contains H2, J1/LIM and the per-label rank conditions) -- are simultaneously satisfiable. So no argument
built only from these conditions can exclude those leaves; the obstruction sought in the brief ("joint over the whole
configuration of helpers that carry missing labels") does not exist for them at this level.

What they are not: **local objects, not circuits.** Not represented, hence not checked: the helpers with u = 0 (7 to 9 full
helpers in the integer solutions: their masks, and their independence together with the configuration, Lemma 4.4); the H-H
edges and the v_i (the MILP gives a v-distribution, not a matching with labels; F8, (L11), (L19)-(L20) per form); the
even+even gates (only the counts y0, y1, y2, y2d); the represented labels as gates (references, Lemma N1, Lemma O1); the
gate order (chronology, acyclicity); Lemma 7.4 per helper; the other phase of the orbit and the drift argument. Whether any
witness extends to a circuit is open; nothing is claimed about it.

## 6. Claims (`claims_final.py`, `claims_final.json`; bookkeeping on LP status [measured])

31 of the 280 open claims have a block key on a ladder; 8 close when the whole block dies (validation of the bookkeeping:
280 -> 272, as `hypo_kill_Mt3.json`). Each of the 8 depends on a single block key at its live level, and no other key
stands at that level:

| claim (a, b, Y, V, he, ho, le, lo, Se, So, budget), orientation, (k, l) | block key | grade of the key's exclusion | leaves of the key |
|---|---|---|---|
| (25,26,2,2,16,15,0,0,8,5,9) Mt (4,5) | (16,2,2,'Mt',3,1) | [certified] | (0,0) step S, LP |
| (26,25,2,2,15,16,0,0,5,8,9) M (5,4) | (16,2,2,'Mt',3,1) | [certified] | same |
| (26,25,3,2,14,16,1,0,5,9,9) M (5,4) | (16,2,3,'Mt',3,1) | [certified] | (0,0) step S, LP |
| (26,25,4,2,13,16,2,0,5,10,9) M (5,4) | (16,2,4,'Mt',3,1) | [certified] | (0,0) step S, LP |
| (25,26,3,3,15,14,0,1,9,6,9) Mt (4,5) | (15,3,3,'Mt',3,1) | [finite-checked] | (0,0) and (1,0) step G |
| (26,25,3,3,14,15,1,0,6,9,9) M (5,4) | (15,3,3,'Mt',3,1) | [finite-checked] | same |
| (26,25,4,3,13,15,2,0,6,10,9) M (5,4) | (15,3,4,'Mt',3,1) | [finite-checked] | (0,0) and (1,0) step G |
| (25,26,3,2,15,15,0,0,8,6,9) Mt (4,5) | (15,3,2,'Mt',3,1) | [measured] | (0,0) step G [finite-checked]; (1,0) step S with R8-int [measured] |

If every exclusion were accepted: 272 claims open (all 8 closed). Accepting only [certified] and [finite-checked]
exclusions: 273 open (7 closed); the eighth needs the leaf (15,3,2,'Mt',3,1) (A, q_D) = (1,0), whose two LP-feasible
skeletons are removed by MILP status only. **No leaf stands in the way of the 8 claims any more**; what stands between
them and a certificate is listed in section 7. The other 23 claims touching block keys keep other feasible keys at their
levels: none closes and no level (k, l) moves. All 21 ladder keys of the block are excluded: (12,5,0), (12,5,1), (15,1,0..3),
(15,2,2..4), (15,3,3), (15,3,4), (16,0,0..3) [finite-checked]; (16,1,3), (16,2,2..4) [certified]; (15,2,1), (15,3,2)
[measured] (first three numbers of the key; all (.., 'Mt', 3, z)).

## 7. What is proved, certified, finite-checked, measured

| statement | status |
|---|---|
| Lemma J*, hereditary lemma, free-rider and free-component lemmas, rotation lemma, completeness argument (PILOT_SPEC.md 3, 4, 7, 11.1) | [proved], written by this agent, not reviewed |
| F2, F3, F6 for M^T; rho(B) = B | [finite-checked] (`geo_q3.py`; equal to PROOF.md Appendix A) |
| every LP decision "infeasible" of step S: 31,490 decisions over the 207 leaves | [certified]: 31,490 exact integer Farkas certificates, 0 failures (`farkas_run.py`, `farkas_final/`); certificate and check written by the same agent, one checker |
| the 78 exclusions by step S with LP prunes only (among them 4 ladder keys, 4 of the 8 claims) | [certified] LP prunes inside a case enumeration that is [finite-checked] (`enum_q3.skeleton_enum`: R4, R5, R6, (B-1)); step S reproduced identically in two runs; P5 (S): 9,891 objects, 0 misses |
| the 103 exclusions by step G without R8-int | [finite-checked] (`enum_q3.py` step G, one implementation; LP prunes certified); three of them, (16,0,1..3) (0,0), also rest on the join of `pass2d_q3.py` |
| the 5 exclusions using R8-int (2 by step S, 3 by step G) | [measured] (HiGHS MILP status 2, no certificate) |
| the 21 SURVIVING leaves | witnesses checked by `verify_q3` [finite-checked]; integer extension of the counts [measured] (MILP status 0, solution re-checked exactly) |
| the rows of the case systems (package, Addenda A-D, October rows), Lemma 7.4's type restriction | [read, not checked] |
| LP feasibility of the keys and leaves outside this enumeration (which leaves are open, the ladders, the 280) | [measured] (scope folder) |
| claims that would close (8, or 7 without [measured] steps) | bookkeeping on the above; not a certificate; 272 claims open |
| any bound above 75 | **not claimed** |

What an exclusion at grade [finite-checked] still rests on: one implementation of the search (validated by P1-P5, the
bounded brute force and the join's V1/V2, not by a second implementation); the rank routine (two implementations agree on
every accepted object and control; the search itself uses one); the proofs of PILOT_SPEC.md (unreviewed); the rows
[read, not checked].

## 8. Extension to q = 4

The method works on q = 3: every leaf was decided, the exclusions on the ladder keys are certified or finite-checked
except two, and the survivors show where the conditions used are exhausted. Extending to the M^T q = 4 block (26
first-layer keys, 17 claims) is justified in principle but not with this implementation and a comparable budget:

- size: four labels and six label pairs; roles (r, L) with L in 15 subsets instead of 7; W is spread over four labels, so
  root sets come from rank >= 3 or 4 (9,407 / 1,729 labels) instead of rank >= 5..7 (456 / 222 / 6), and there is one more
  level of label assignment. From the q = 3 costs (808 distinct skeletons, 2.4 CPU-hours, the heaviest single skeletons
  2 to 7 minutes) a rough factor is 5 to 10 in skeletons and 10 to 50 per skeleton: of the order of 100 to 1,000
  CPU-hours in Python [estimate from measured q = 3 costs, not measured for q = 4]. A first step costing minutes would be
  step S alone for q = 4 (skeleton counts and how many leaves fall to certified LP prunes: 78 of 207 did at q = 3).
- prerequisites: step G in compiled code or with precomputed per-label candidate tables; the label-indexed join as the
  default for multi-segment skeletons, with P5-type controls built for q = 4 before the run; exact certificates for
  R8-int (or avoiding it); a second, independent implementation of step G for the leaves that matter, since q = 3 produced
  one real completeness error in the first version; the triangle-with-r = 2 shapes added to the planted controls.
- expectation: survivors are to be expected for q = 4 as well (at q = 3, 21 leaves survive with integer-feasible counts); the question worth asking first is
  the same as here: which q = 4 keys are on ladders, and do the survivors avoid them.
