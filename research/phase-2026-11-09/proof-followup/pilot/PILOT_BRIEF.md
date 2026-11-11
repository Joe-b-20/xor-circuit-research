# Pilot brief: complete local realizability enumeration for the M^T q = 3 block at G = 75

Written by the main agent, 2026-11-10. Work folder for the pilot: `~/xs-campaigns/2026-11-10-proof/pilot/`
(create it). Repository: `~/xor-circuit-research` (branch `phase-2026-11-09`; do not commit; the main
agent commits). Nothing in this pilot may be described as a bound above 75.

## 0. What is being decided, and why this family

The 75-gate MixColumns proof framework leaves 280 oriented claims open at G = 75 by LP status
(`lower-bound-proofs/mixcolumns-lb75-open-cases/README.md`, section "Relation to the October 2026
campaigns"). A claim is kept open by LP-feasible local systems ("keys" `(h, y, F, ori, q, z)`), each
split into leaves `(A = a, q_D = d)` (exact hub case and dark case; Addenda B-D). Scope measurements of
today (`../scope/`, read `../scope/coverage_manifest.json` and `../scope/ladders.json` when present):

- excluding every leaf with A >= 2 would leave 119 claims open; excluding every leaf with A >= 1 would
  leave 88 open (A = 0 configurations, no hub meets a full helper). So any hub-only route is incomplete;
  the pilot must decide leaves of all A, including A = 0.
- per-pair finite facts give nothing: two anchored hubs (r = 1 or 2) with no full-met label CAN share a
  hub-only label with the Lemma-J family independent, in thousands of mask pairs
  (`../scope/share_pairs.py`, `share_pairs.json`). The obstruction, if any, is joint over the whole
  configuration of helpers that carry missing labels.
- The M^T q = 3 block is the smallest family that supports live claims: 21 first-layer keys
  `(h, y, F, 'Mt', 3, z)` (list: `scan_leaves.json` keys with ori Mt and q = 3; their open leaves have
  A in {0, 1, 2}, q_D in {0, 1}); killing the whole q = 3 M^T block (66 LP-feasible keys including those
  behind the first layer) closes 8 of the 280 claims (`../scope/hypo_kill_Mt3.json`). With q = 3 there
  are only three missing labels and three label pairs, so a COMPLETE enumeration of the label
  configurations is small. The integer solutions of the leaves (`../scope/leaves_int.json`, field
  `distinct_solutions`) show the shapes the LP admits: e.g. two (1,2,v) hubs and one (2,2,0) hub
  forming a triangle on the three labels, plus four to six (2,1,v) hubs and (0,2,v) hubs; these are
  only samples, NOT the domain.

Deliverable: for every open leaf of every q = 3 M^T key in the ladders (first layer and behind), either
EXCLUDED (empty enumeration, with the completeness argument written) or SURVIVING (explicit witnesses).
If time remains and the method is sound, the M^T q = 4 block (26 first-layer keys, 17 claims) next.

## 1. Mathematics you must write before running anything (`pilot/PILOT_SPEC.md`)

Use the notation of `lower-bound-proofs/mixcolumns-lb75/PROOF.md` (sections 4, 10, 11) and the addenda
`lower-bound-proofs/mixcolumns-lb75-open-cases/addenda/PROOF_ADDENDUM{,_2,_3,_4}.md`. Read B.1
(definitions, dark labels: Lemma 10.2 of PROOF.md: a missing label is dark iff it has no H-B edge at an
anchored helper, i.e. all its carriers have r = 0), C.1-C.4 (full values, pair values, N(h), the family
F(h,R,S), finite fact H2, condition (C1)), D.1-D.3 (label classes, limit hubs, sharing, Lemma J, J1),
D.8 (the exact split). The geometry primitives are in
`~/xs-campaigns/2026-11-07-sprint/qjointcheck/jc_geo.py` (own boundary parse from the repository
matrix, triples, pair values, full values, N(h), GF(2) rank; reuse them). The exact case-system rows of
a leaf are `check_combined75.matrix(key, ('eq', a), d)` in
`lower-bound-proofs/mixcolumns-lb75-open-cases/checkers/` (returns b and labelled columns: type
columns `(r, u, v)` and auxiliary columns).

Specify precisely:

1. **The object.** A *label configuration* for a key K = (h, y, F, ori, q, z) and leaf (a, d): the q
   missing labels (even values); every helper with u >= 1: its mask (odd value not in B), its r
   represented triples (a subset of the triples of its mask; r = 3 means full helper, all three), its
   label set L_i (|L_i| = u_i), and for each label the boundary element b = mask + label, which must lie
   in B; the full-met labels (carried by a full helper; exactly A = a of them, each at exactly one full
   helper, Lemma 4.5); the dark labels (all carriers r = 0; exactly d of them). Helpers with u = 0 are
   not part of the object. State what the object does NOT contain (v, the H-H edges; the even gates;
   chronology) and why every normalized circuit in the leaf induces exactly one such object.
2. **Allowed ranges.** Masks: for r >= 1 the mask has >= r triples (Lemma 4.4); for r = 0 any odd value
   not in B. Labels: a label carried by hubs k, k' forces h_k + h_k' to be a pair value (D.1); a label
   carried by a hub k and a full helper f forces h_k + f to be a pair value with f in N(h_k) ((C1)(a)).
   Multiplicities: the number of helpers with u >= 1 and the total number of label incidences are
   bounded by rows of the key's system (e.g. the even-signal fanout row sum u + 2 f <= 4q + 2F, the
   label rows (L7)/(L7*), the type ranges of the leaf after HUB2's column removal, u <= (3 - r) + (q - a)):
   derive explicit finite bounds from the rows for THIS key and leaf; the enumeration must respect
   exactly these, no tighter.
3. **Every pruning rule, with its lemma.** At least: Lemma 4.1 (a helper carries each label once; a
   label's carriers are distinct helpers), 4.5, 4.6 (|L_i ∩ L_j| <= 1), Lemma J (the joint family of all
   helpers in the configuration: full helpers' three triples, hubs' represented triples, for each
   full-met label the vectors H_k + H_f + P(h_k + f) for its hub carriers, for each hub-only label a
   spanning tree of mixed vectors H_k + H_k' + P(h_k + h_k') over its carriers; independent). State
   that independence is hereditary (sub-configurations of a valid configuration are valid), which is
   what makes depth-first pruning complete. Then the LP filter: the configuration fixes, for every
   (r, u) with u >= 1, the number of helpers of that (r, u); the leaf's case system with these counts
   imposed (sum over v of n_(r,u,v) = count) must stay LP-feasible (a relaxation of the circuit's
   type vector; v is free). Optionally FM/(L7) per-label rank conditions. Every rule must be a NECESSARY
   condition for a normalized circuit; cite the lemma; do not use any statement that only holds for
   our known circuits.
4. **Symmetry.** The byte rotation (rotate the four bytes of a 32-bit mask) maps B to B for both
   orientations (checked today). Prove in two lines that it maps normalized circuits of a key to
   normalized circuits of the same key and leaf (it permutes inputs and outputs compatibly with the
   byte-circulant map), so orbit representatives suffice for the first anchored mask. Use no other
   symmetry without proof.
5. **Unanchored components.** Hubs with r = 0 and m = 0 have masks constrained only through the labels
   they share. Say exactly how the enumeration treats a label carried only by r = 0 hubs (a dark label):
   its value is free; the mixed vectors of a tree of such hubs are independent for every choice of
   values (the H coordinates alone are independent); cycles impose formal cancellation conditions. Make
   the enumeration complete for them (free parameters stay symbolic, or are enumerated over the 64
   boundary elements once one incident mask is fixed) or restrict the claim accordingly and say so.
6. **The exact conclusion of an empty result.** "No normalized circuit of orientation ori with key K and
   (A, q_D) = (a, d) exists at G = 75", hence the leaf is excluded (D.8); with all leaves of a key
   excluded, the key is excluded; which claims this bears on comes from `../scope/ladders.json`
   (a key's exclusion raises the first feasible level of a claim only when it is the last feasible key
   at that level). Say explicitly that the enumeration represents LOCAL configurations satisfying
   necessary conditions, not complete circuits: an empty enumeration is an impossibility result; a
   surviving configuration is NOT a circuit.
7. **Completeness argument.** Why every hypothetical 75-gate circuit in the leaf induces an object that
   the enumeration visits (or prunes only by a rule it would have failed). This is the heart of the
   deliverable; write it as a proof.

## 2. The program (`pilot/enum_q3.py` or similar)

- Exact arithmetic throughout (GF(2) ranks on python ints; LP filter via scipy HiGHS is a relaxation and
  may only PRUNE when the LP is infeasible with status 2; any other status counts as "not pruned").
- Depth-first over configurations with the pruning rules of section 1, in an order you justify.
- Record, per leaf, the number of nodes pruned by each rule (so an empty result can be inspected) and
  the first few pruned configurations at the deepest level reached.
- For a surviving configuration: output the full witness (masks, triples, labels, boundary elements,
  which labels are full-met / dark) and re-verify it against EVERY rule with a separate verification
  function; also report whether it extends to an integer type vector of the leaf's case system (MILP
  with the configuration's (r, u) counts imposed; status recorded).
- Estimate the search size before running (count the root choices and the branching per level from
  the finite tables) and write it down; set a budget of at most 4 CPU-hours in total for the q = 3
  block; stop and report if the estimate exceeds it.

## 3. Controls (run and record before trusting any empty result)

Positive controls (valid objects must survive every filter):
- Real circuits: extract the label configuration of real phases (A = 0, q >= 7) with the sprint's
  phase extraction (`~/xs-campaigns/2026-11-07-sprint/qjoint/qj_circ.py` reuses
  `qhub/qh_circ.py`'s extraction of types, missing labels and m_i; the circuits and bridge are under
  `~/xs-campaigns/2026-11-07-sprint/`), and check that every rule of section 1 accepts them, and also
  accepts every sub-configuration obtained by keeping any 3 of their labels (hereditary).
- Synthetic: two anchored hubs sharing a hub-only label from the independent witnesses in
  `../scope/share_pairs.json` (fields `witnesses`) must be accepted; the realizable limit-hub pairs of
  Addendum D (two limit hubs sharing a full helper at different labels) must be accepted.
Negative controls (invalid objects must be rejected, by the named rule):
- Two limit hubs sharing a label (finite fact J1: reproduce "0 independent" on the J1a / J1b families
  with your primitives), a helper carrying a label twice, two hubs sharing two labels (4.6), a
  configuration with 4 - r full helpers at one hub (H2), a configuration whose imposed (r, u) counts
  violate a row of the case system.
- Brute force: for the smallest sub-case (configurations with at most two hubs with u >= 2 and no
  u = 1 helpers) enumerate by an independent, deliberately naive program and compare counts of
  surviving configurations with the pruned search.
Record every control's result in the report; a failed control stops the pilot.

## 4. Report (`pilot/REPORT.md`)

Sections: (1) specification summary and completeness argument (or pointer to PILOT_SPEC.md); (2) search
size estimate and actual node counts; (3) controls; (4) per-leaf results table (key, a, d, integer
status from `leaves_int.json`, enumeration result, nodes, pruning histogram); (5) witnesses, if any, with
their verification and what additional compatibility condition they would still have to satisfy;
(6) which claims change status if the excluded leaves are accepted (from ladders.json: a claim closes
only when all keys at a level die; list the keys that would need to die for each affected claim);
(7) what is proved [proved], what is finite-checked by one implementation [finite-checked], what is
measured [measured]; (8) whether extending to q = 4 is justified and the size estimate. Evidence tags
on every claim. No statement about a bound above 75. Do not spawn subagents. Do not run anything
longer than the budget; use `nice -n 10`. Keep the machine's existing processes untouched.
