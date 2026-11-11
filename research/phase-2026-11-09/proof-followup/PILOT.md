# Pilot: complete local enumeration for the M^T, q = 3 block at G = 75

Phase 2026-11-09, proof follow-up, 2026-11-10/11. Main-agent summary of the pilot and of its independent
review. Sources: [pilot/PILOT_SPEC.md](pilot/PILOT_SPEC.md) (specification and completeness argument, written
before the run), [pilot/PILOT_REPORT.md](pilot/PILOT_REPORT.md) (the proof agent's report),
[pilot/RESULTS_TABLE.md](pilot/RESULTS_TABLE.md) (one row per leaf), [REVIEW.md](REVIEW.md) (independent
reviewer, own code). **The lower bound stays 75**; with every pilot exclusion accepted 272 of the 280
claims are still open. Tags: [proved], [certified], [finite-checked], [measured], [read, not checked].

## 1. Why this family, and how it connects to the remaining claims

[MANIFEST.md](MANIFEST.md) shows that no hub-case enumeration covers the residual problem (119 claims
survive the exclusion of every A >= 2 leaf, 88 that of every A >= 1 leaf) and that per-pair sharing facts
give no row. The remaining kind of local argument is joint over ALL helpers that carry missing labels. The
M^T q = 3 block is the smallest family on which that can be done completely (three labels, three label
pairs) and it supports live claims: 66 LP-feasible keys with 207 open leaves `(A, q_D)`, `A <= 2`,
`q_D <= 1`; 21 of the keys (48 leaves) lie on a ladder of an open claim; closing the whole block closes 8
claims.

## 2. What is enumerated (short specification)

**Object.** For a key `K = (h, y, F, 'Mt', 3, z)` and leaf `(a, d)`: the *label configuration* of a phase is
the three missing labels (even values) and every helper with `u >= 1` (a *carrier*): its mask, its `r`
represented boundary triples, its label set; the boundary end of each incidence is `mask + label` and must
lie in B. A label is full-met if a full helper carries it (exactly `a` are), dark if no anchored helper
carries it (exactly `d` are). Not in the object: helpers with `u = 0`, the H-H edges and `v`, the even+even
gates, the chronology, the other phase.

**Ranges.** Masks of anchored carriers have at least `r` triples (40,936 / 616 / 112 values for
`r = 1 / 2 / 3`); unanchored carriers have any odd mask not in B; a carrier of a label `l` has one of the
64 masks `l + b`. Multiplicities are bounded only by the leaf's own case system with the configuration's
class counts imposed, nothing tighter.

**Rules (each a necessary condition of every normalized circuit of the leaf).** R1 distinct masks and
labels (Lemma 1.1); R2 one incidence per (helper, label) (4.1); R3 triples (4.4, F3); R4 full-met labels,
one full helper each, exactly `a` (4.5, D.8); R5 two carriers share at most one label (4.6); R6 exactly `d`
dark labels (10.2); **R7 (Lemma J\*)**: the joint family of the whole configuration is independent over
GF(2): every carrier's triple vectors `H_i + T` and, for every label, a spanning tree of mixed vectors
`H_i + H_i' + {b_i, b_i'}` over its carriers; R8: the leaf's case system with the class counts
`sum_v n_(r,u,v) = c_(r,u)` imposed for all `u >= 1` is LP-feasible; R8-int: it has an integer solution.
Lemma J\* generalises Lemma J of Addendum D to all carriers and contains (C1), H2, J1/LIM and the per-label
rank conditions as subfamilies.

**Pruning and symmetry.** R1-R7 are hereditary (a sub-configuration of a valid object is valid, Lemma 3.8),
which makes depth-first pruning complete; R8 is applied to prefixes in its monotone form (counts as lower
bounds) and exactly at complete skeletons. The only symmetry used is the byte rotation (order 4), which
maps B to B and normalized circuits of a leaf to normalized circuits of the same leaf. Unanchored
single-label carriers are not branched over (Lemma 3.9: they never enter a dependency).

**Two steps.** Step S enumerates *skeletons* (the statuses of the three labels and the multiset of roles
`(r, L)`) under R4-R6, the per-label rank bound and R8. Step G realizes each surviving skeleton with
concrete masks, triples and labels under R1-R7.

**What an empty result proves.** No normalized circuit of orientation M^T with key K and
`(A, q_D) = (a, d)` exists at G = 75, relative to: the rows of the case system [read, not checked], the
finite facts F2, F3, F6 [finite-checked, recomputed twice], the lemmas of the specification [proved;
reviewed by one independent agent], and the framework applying at G = 75 ([OBLIGATIONS-76.md](OBLIGATIONS-76.md), O1).
The enumeration ranges over LOCAL configurations satisfying necessary conditions, an over-approximation of
what circuits induce: an empty result is an impossibility result; a surviving configuration is NOT a
circuit.

**Completeness** (PILOT_SPEC.md section 7, with the addendum of section 11): a circuit of the leaf induces
an object satisfying R1-R8; its skeleton is one that step S visits; after a rotation its root label is an
orbit representative; every intermediate node on the path to it is a sub-object and therefore passes every
rule; so the search reaches it. The reviewer confirmed each step and the necessity of every rule.

**Erratum (reviewer's finding).** Lemma 3.10 of the specification (free components) is false as stated
when the component's anchored helper has `r >= 2` (counterexample: a lone full helper whose mask differs
from another full helper's by a pair value). It is used only to complete survivors with their unbranched
parts, never to exclude; every stored witness is a complete object verified directly, so no result
changes. The lemma should be restricted to components whose anchored helper has `r <= 1`.

## 3. Controls

| control | what it exercises | result |
|---|---|---|
| real circuits, rule level | all rules on 1,264 phases, 344,432 three-label sub-configurations | 0 rule failures |
| synthetic positives | independent sharing pairs (30), realizable limit-hub pairs (5) | all accepted |
| negatives | J1 (208,272 + 14,816 pairs), H2 over-capacity hubs (14,976), duplicate label, two shared labels, bad counts | all rejected by the named rule |
| planted objects, search level (pilot) | 9,651 valid objects not produced by the enumerator: 9,124 from real phases over 2,614 skeleton shapes, 527 built with A = 1..3; 240 planted triangles | 0 misses at skeleton level and in the guided search |
| planted objects (reviewer, own construction) | 312 valid objects incl. multi-label helpers, labels with three or more carriers, riders, A = 2, q_D = 1 | 312 / 312 found, by the first-run and the corrected code |
| brute force, memory-bounded | naive loops vs pruned search with and without rotation on a restricted domain | 95,858 configurations each, identical SHA-256 |
| independent re-enumeration (reviewer, own search design) | every accepted skeleton of every step-G exclusion | no realization found anywhere; no disagreement on 120 skeleton-leaf pairs |

The planted controls matter most: the earlier rule-level controls show that valid objects pass the
filters, the planted ones show that the SEARCH reaches valid objects. The A >= 1 machinery is exercised
only by constructed objects, since every real phase has A = 0. Not covered by any planted control:
triangles with two or three r = 2 hubs, and objects with both a full-met and a dark label.

One real completeness error was found by the pilot itself in its first-run code (in multi-segment
skeletons some unanchored two-label helpers were placed twice, which could give a false exclusion). It was
fixed before the second pass; the reviewer confirmed that it affected none of the stored results and
cannot occur at q = 3.

## 4. Outcome

All 207 open leaves are decided: **186 EXCLUDED, 21 SURVIVING, 0 UNRESOLVED.**

| how excluded | leaves | grade |
|---|---:|---|
| step S, LP prunes only | 78 | every LP prune has an exact integer Farkas certificate (31,490 by the pilot; the reviewer certified its own independent re-derivation); the skeleton enumeration agrees between two implementations on all 207 leaves |
| step G (geometry), no integer filter | 103 | [finite-checked], two independent implementations agree skeleton by skeleton |
| using the integer filter R8-int | 5 | pilot: MILP status only [measured]. Reviewer (`review/t_milp2.log`): for (12,7,0) and (15,3,2) at A = 1, (15,4,2) at A = 2 and (15,2,1) at A = 0 every skeleton removed by the MILP has no realization in its own search, so geometry excludes them (one implementation); (15,4,1) at A = 1 has one MILP-removed skeleton with a realization and is excluded only by integrality of y2, which the reviewer proved exactly (branch y2 <= 2 / y2 >= 3, two exact certificates) |

By `(A, q_D)`: excluded / surviving = 34 / 14 at (0,0); 21 / 0 at (0,1); 43 / 6 at (1,0); 30 / 0 at (1,1);
33 / 1 at (2,0); 25 / 0 at (2,1). Every leaf with a dark label is excluded.

All 48 leaves of the 21 ladder keys are excluded, so all 21 ladder keys are excluded under the stated
assumptions. The 21 surviving leaves belong to 14 keys that are on no ladder of the 280 claims.

## 5. Surviving local witnesses

379 witnesses are stored for the 21 surviving leaves (keys (13,5,0), (15,3,0), (15,4,0..4), (16,2,0),
(16,3,0..3), (18,1,0), (18,1,1), all `(.., 'Mt', 3, z)`; 14 leaves at A = 0, 6 at A = 1, 1 at A = 2; all
with `q_D = 0`). Every one passes both agents' independent checks of R1-R7 and has LP- and MILP-feasible
counts. Example, leaf (13,5,0,'Mt',3,2), A = 0: labels `0x20205`, `0x3030005`, `0x20206`; hubs `0x20204`
(r = 2), `0x2020206` (r = 2), `0x1000104` (r = 1) forming a triangle on the three labels, plus `0x4040004`
(r = 2) on the third; joint family of 11 vectors of rank 11.

- **Which obstruction they defeat.** The conjectured obstruction "joint independence over the whole
  configuration of label-carrying helpers, together with the rows with integer class counts" does not
  exclude these leaves: all of it is simultaneously satisfiable.
- **Local or extendable.** They satisfy only the local conditions listed in section 2. Whether any
  extends to a circuit is open and nothing is claimed.
- **What the model is missing.** The 7 to 9 full helpers with `u = 0` and their joint independence with
  the configuration (Lemma 4.4); the H-H edges and `v` as an actual labelled matching; the even+even gates
  beyond their counts; the represented labels as gates (references, N1, O1); the gate order; the other
  phase of the orbit and the drift argument.
- **Relevance.** None of the 21 surviving leaves is on a ladder of an open claim, so these witnesses do
  not block any of the 280 claims; they show where this kind of argument stops, on keys of the same block.

## 6. Effect on the remaining claims, with consistent definitions

The published state is unchanged: **280 open claims by LP status under the published rows**. The pilot's
exclusions are not part of the published certificate set. If they are accepted at the stated grades:

| accepted exclusions | claims closed | open |
|---|---:|---:|
| none (published rows) | 0 | 280 |
| step-S exclusions with certified LP prunes: keys (16,2,2), (16,2,3), (16,2,4) | 4 | 276 |
| plus step-G exclusions agreed by two implementations: keys (15,3,3), (15,3,4) | 7 | 273 |
| plus key (15,3,2), whose (1,0) leaf rests on a MILP status (pilot) or on the reviewer's geometric search alone (one implementation) | 8 | 272 |

The other 23 claims that touch block keys keep other feasible keys at their levels; none closes and no
level moves. Each of the 8 claims hangs on a single block key at its live level.

## 7. Structural content

- **Lemma J\*** [proved in the specification; confirmed by the reviewer]: the gate-equation family of ALL
  label carriers of a phase is independent. It replaces the separate hub statements (C1), H2, J, J1/LIM
  by one statement and applies for every q and both orientations.
- **The skeleton step is an integer argument that needs no geometry**: imposing integer class counts for
  the label-carrying helpers under Lemmas 4.5, 4.6 and the dark/full-met statuses excludes 78 of 207 leaves
  with exact certificates. It is orientation- and q-independent in form.
- **Negative result**: at q = 3 the joint local conditions are exhausted on 21 leaves; further progress on
  such leaves needs conditions outside the label configuration (section 5).

## 8. Is a larger enumeration justified?

- **Not the geometric search as implemented.** Extrapolated cost for the M^T q = 4 block is 100 to 1,000
  CPU-hours in Python [estimate, not measured], survivors are to be expected, and 88 of the 280 claims
  sit on A = 0 leaves at q = 6 to 9, far beyond what this search reaches.
- **Justified as the next bounded step: the skeleton step alone, block by block, starting with q = 4.** It
  costs minutes, produces exact certificates, and at q = 3 it decided 38 % of the leaves and 4 of the 8
  block-dependent claims. Its reach on the ladders is not known in advance; measure it before anything
  else. The related pure-integrality route (1,637 integer-infeasible ladder leaves, exact branch
  certificates as the reviewer produced for one leaf) is of the same kind.
- Any exclusion from either route should then be packaged like the published batches: certificates plus
  an independent checker, before the open count is changed.

Compute used: pilot about 5.5 CPU-hours (budget 4; one hour was lost to the brute-force control that ran
out of memory and took WSL down on 2026-11-10), review about 0.8 CPU-hours.
