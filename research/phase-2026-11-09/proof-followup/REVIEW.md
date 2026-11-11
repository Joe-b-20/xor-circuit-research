# Independent review of the M^T q = 3 pilot

Reviewer: a separate agent (Opus, high effort), 2026-11-11, working read-only on the pilot's files with
its own code (`~/xs-campaigns/2026-11-10-proof/review/`: `rgeo.py`, `rcheck.py`, `rsearch.py`, `t3*`, `t4*`,
logs). It imported none of the pilot's or the sprint's geometry modules. The text below is the reviewer's
report as returned to the main agent (the reviewer could not write the file itself); only this header was added.
About 50 CPU-minutes. Nothing here states or suggests a bound above 75.

**Summary of the reviewer.** No mismatch that would make an exclusion wrong. Open points: one leaf
mislabelled as a geometric exclusion (it rests on integrality of y2, proved exactly by the reviewer), a
pass-1 code bug that had no effect on stored results and is fixed, and a lemma (3.10) that is false as
stated for an anchored helper with r >= 2 and matters only for how survivors are completed.

## What was read, and when

- `pilot/results/`: 198 leaf files (pass 1), read from 14:53 UTC on 2026-11-11; produced by the code saved
  as `enum_q3_pass1_snapshot.py`.
- The pilot kept working during the review: `enum_q3.py` patched at 14:56 UTC; `results_final/` (pass 2)
  written from about 15:30 UTC. At 15:56 UTC it held 207 leaves: 78 excluded by step S (LP), 2 by step S
  (LP + MILP), 106 by step G, 21 surviving, 0 unresolved.
- `results/` was reviewed completely; every excluded and surviving leaf of the 15:56 `results_final/` was
  also checked, but not the pass-2 code itself.

## Findings, by severity

1. **No mismatch touching an exclusion.**
   - Planted objects: 312 valid objects built with the reviewer's own code; the pilot's step G reported
     every one up to rotation, in both the pass-1 and the current code; its step S, with the row filter
     disabled, produced every planted skeleton.
   - Skeleton lists: the reviewer's own skeleton enumeration matches the pilot's list exactly on all 207
     leaves. No excluded leaf in either result set has a skeleton the pilot missed.
   - Step-G exclusions: for every accepted skeleton of every step-G or LP + MILP exclusion, the reviewer's
     own exhaustive search finds no configuration satisfying R1-R7 (61 + 2 leaves in `results/`, 106 + 2
     in `results_final/`).
   - Witnesses: every stored witness (146 in `results/`, 379 in `results_final/`) passes the reviewer's
     R1-R7, LP (status 0) and MILP (status 0).
2. **Mislabelled leaf: (15,4,1,'Mt',3,1), A = 1, q_D = 0 in `results_final/`.** Labelled "step G
   (geometry)", but geometry does not exclude it: the skeleton
   `[[1,[0,1]],[1,[0,2]],[2,[1]],[2,[1]],[2,[2]],[2,[2]],[3,[0]]]` has a complete object satisfying R1-R7
   and the LP form of R8. The pilot removes it only through R8-int, on a 20 s MILP solver status. The
   reviewer proved the integer infeasibility exactly: branching on y2 (LP value 7/3) gives y2 <= 2 and
   y2 >= 3, both infeasible with exact integer Farkas certificates (`t_milp_branch.py`). The exclusion
   holds, but it rests on y2 being an integer (it counts gates). Three leaves of `results/` also used the
   MILP in the pilot's logic ((15,4,2) A = 2, (12,7,0) A = 1, (15,3,2) A = 1); none of their MILP-removed
   skeletons has a realization, so geometry alone excludes them.
3. **Pass-1 code bug, fixed by the pilot on 11-11, with no effect on stored results.**
   `enum_q3_pass1_snapshot.py:384`: in multi-segment skeletons the product phase placed in-segment r = 0,
   u >= 2 helpers a second time (the duplicate always fails R7: a possible false exclusion); lines 330-331:
   the internal stop `no_concrete_role` was reported as "done". Neither ever triggered (none of the 959
   skeleton entries is affected; at q = 3 the first cannot happen). Fixed in the current `enum_q3.py`.
4. **Lemma 3.10 is false as stated when the anchored helper k has r_k >= 2** (PILOT_SPEC.md section 3.10;
   section 5, bullet 1 depends on it). Counterexample: a lone full helper f carrying a full-met label
   counts as a free component; if another full helper f' has f + f' equal to a pair value, F4 makes the
   joint family dependent although it is independent without that component. Exclusions are unaffected
   (they only drop parts, which Lemma 3.8 makes sound). Stored witnesses are unaffected (each is a
   complete object verified directly).
5. **The pilot's R8 decisions are solver statuses; the reviewer added exact certificates.** Every LP
   infeasibility that the reviewer's independent re-derivation of step S relies on has an exact integer
   Farkas certificate: 2,485 decisions on the 78 step-S leaves, 10,161 on the other leaves of `results/`,
   10,054 + 3 x 194 on the excluded leaves of `results_final/`. All 849 leaves of the 66 keys that the
   pilot did not treat as open are exactly infeasible (`t_nonopen.log`). The pilot's own certificate files
   were not checked by the reviewer.
6. **Minor.** The `excluded_by` label does not record MILP use (how finding 2 was hidden); an assertion in
   `plan()` could crash (never fired); 9 open leaves had no file in `results/` (all 207 are in
   `results_final/`); a survivor is counted before its free parts are completed (no such case in the data).

## Mathematical review (task 1)

Every rule is a necessary condition of every normalized circuit of the leaf, and nothing restricts the
domain beyond what is proved.

Confirmed: Lemma 1.1' (a missing label is an even signal with no B-B edge; an H-B edge is a gate with
equation E_l + H_i + B_b; distinct incidences are distinct gates; assumes normalization, as the package
does); the ranges (D-l), (D-h), (D-b), (D-2), (D-shared); R1-R6 (R4 is Lemma 4.5 with D.8; the case matrix
removes only the HUB2 types and the types excluded by Lemma 7.4 or by v <= min(2z, h - 1)); R8 as a valid
relaxation and its monotone form on prefixes; R8-int (every column is a nonnegative integer: helper
counts, gate counts y0, y1, y2, y2d, and F_b, F_d as sums of integers); (B-1), (B-2), (B-3); Lemma J*
(pairwise distinct gates, both pivots invertible row operations followed by deletion of a row holding a
private coordinate, any spanning tree spans the same space); Lemmas 3.8 and 3.9; Lemma 4.1' (rotation;
rho(B) = B checked independently; no-rotation re-runs of two leaves gave the same result); the
completeness argument of section 7 (skeleton canonicalization, the monotone R8 prefix rule, deferred
riders, new roots for anchored roles touching no concrete slot, multi-segment products with caps giving
UNRESOLVED and never EXCLUDED, the "increasing mask" rule applied only to identical roles).

Gap: Lemma 3.10 (finding 4).

Assumptions the conclusion rests on: the rows of `check_combined75.matrix` hold for every phase [read,
not checked]; the phase is a normalized (minimum) circuit; the finite facts F2, F3, F6 (recomputed with
the reviewer's own parse, identical: F3 40,320 / 504 / 112; F6 rank histogram as in PROOF.md, 593,251
labels with a form); for the leaf of finding 2 only, y2 is an integer.

## Code against specification (task 2)

Bugs at snapshot lines 384 and 330-331 (finding 3). Confirmed: line 74 (R8 prunes only on status 2),
94-141 (step S), 279-291 and 323-324 (candidates and the identical-roles rule), 310 (root labels), 362-375
(new labels), 381-427 (segments, caps, products). R8-int at 609-614 removes skeletons and is load-bearing
in finding 2, but line 663 does not record it. No missed candidate, no unjustified symmetry break, no cap
counted as an exclusion, no pruning on a status other than 2.

## Independent computations (task 3)

Own geometry (boundary parse, pair table, triples, F6 ranks, highest-bit GF(2) basis); R1-R7 checked
with two different trees per label (a path and a star); LP and MILP with exact count rows. The search is
a static-order exhaustive search in which r = 0, u >= 2 helpers are placed as soon as they touch a concrete
label and may create labels, so there are no "segments"; R7 uses path trees.

- Witnesses: all 146 (`results/`) and 379 (`results_final/`) pass.
- Step-G exclusions: the 61 step-G leaves of `results/` fall into 16 distinct skeleton lists, 91
  skeletons; all 91 have no realization, nothing aborted; no-rotation re-runs agree (5.95 M and 2.97 M
  nodes). Pass 2: all 118 + 5 new skeletons have no realization. Surviving leaves: complete objects
  built independently, each passing R1-R7 with LP status 0 and MILP status 0, for (13,5,0) with A = 0, 1,
  2; (15,3,0), (15,4,1), (15,4,2), (15,4,3) with A = 0; (15,4,2) with A = 1. The reviewer's verdict never
  contradicts the pilot on 120 skeleton-leaf pairs (254 "no realization" against the pilot's done/0; 19
  "found" against its survivors).
- Planted objects: 300 random valid objects (211 with a helper carrying two labels, 8 with a full helper
  carrying two labels, 125 with a label with three or more carriers, 111 with r = 0, u >= 2 riders, 115
  multi-segment for the pilot, 206 with free components, 33 with A = 2, 104 with q_D = 1) plus 12 of the
  pilot's own skeleton shapes: 312 / 312 found by the current and the pass-1 code. On single-segment
  objects whose unguided runs completed, the object was among the stored survivors 11 / 11 times.

## Step-S exclusions (task 4)

A different decomposition from the pilot (count vectors, then label-set existence, then an exact
certificate for every infeasible LP). All 78 step-S leaves checked: none has a skeleton the pilot missed;
the only LP statuses seen are 0 and 2; 4 of the 12 leaves sampled first have LP-feasible count vectors
that admit no skeleton, so their exclusion is structural (R4-R6, Lemma 4.6), not by the LP. Exact
certificates for all 2,485 decisions.

## Overall statement of the reviewer

| Pilot class | Supported? | Grade and assumptions |
|---|---|---|
| EXCLUDED by step S (LP), 78 leaves | yes | independent implementation, exact certificates; assumes the case-system rows (read, not checked), R4-R6, Lemma 4.6, integer class counts |
| EXCLUDED by step G: 61 in `results/`, 106 in `results_final/` | yes | two independent implementations agree skeleton by skeleton; assumes the confirmed lemmas and F2/F3/F6; exception: (15,4,1) A = 1 in `results_final/` rests on R8-int (exact proof on y2), not geometry |
| EXCLUDED by step S (LP + MILP), 2 leaves | yes | geometric exclusions; the MILP is not needed |
| SURVIVING | yes, as local witnesses only | every witness re-verified; a witness is not a circuit |
| UNRESOLVED | nothing claimed | caps are never counted as exclusions |

At key level, a key whose open leaves are all excluded is excluded under the same assumptions, because
its other 849 leaves are exactly infeasible. The reviewer did not review which claims that changes.
