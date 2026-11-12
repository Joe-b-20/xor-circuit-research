# What was learned (structural study, started 2026-11-11)

A reader's guide to `RECORD.md`. Nothing here changes the published statement 75 <= L(MixColumns) <= 88.
Everything was produced with language-model assistance; reviews are machine reviews by a second model
instance, not human reviews and not formal verification.

## The picture

A circuit for MixColumns can be looked at in three ways, and each way sees a different part of the cost.

1. **As values at one input point (parity).** Signals of odd weight are the ones equal to 1 at the
   all-ones input. This forces 32 output gates and 24 gates that span the even signals: 56. In the
   formulations analysed here nothing of this kind does better: the single-point bound
   wt(x) + wt(Mx) - c(x) is largest at the all-ones point; restricting along the first live gate
   reproduces the same count step by step; pure gate elimination (zeroing or merging inputs and counting
   dead gates) stalls at 57; and a two-point colour count forces no further gate (RECORD 1, 5). Other
   uses of several points or of restrictions were not analysed and are not excluded.

2. **As a system of 3-term equations (the published 75 argument).** Counting how the equations can share
   signals, given that the 64 boundary vectors have no relation of weight below 6, pushes 56 to 75. The
   published argument, as audited, never uses the order of the gates essentially. Its premises
   therefore hold for every *cyclic system*, a set of 3-term relations that determines all values but
   need not be executable gate by gate; such systems can be strictly smaller than any circuit (smallest
   example: 6 against 7, for a 5-input map; this is a gap for that example, not for MixColumns), and
   their minimum is the same for a map and its inverse. A framework whose premises hold for all cyclic
   systems cannot prove more than the cyclic minimum; this is a statement about those premises, not a
   limitation of linear algebra, rank or counting in general. Whether the cyclic minimum of MixColumns
   is below 88 is unknown. The transfer of 75 to inverse MixColumns is conditional on the published
   proof and on the repaired audit, and is not a published statement (RECORD 6).

3. **As eight sheets, one per bit position.** Output (c, j) is "the other three inputs of position
   j" plus "the adjacent pair c, c+1 of position j-1", plus the same pair at position 7 for j = 1, 3, 4
   (RECORD 3). Setting all inputs outside two adjacent positions to zero leaves a single sheet with its
   neighbour free, and that costs 10 gates (proved by hand: mirrored, each "entry" from the neighbour
   must appear as an even signal of a circuit for four triple-sums, and six gates leave room for only
   two). So every circuit has, for each sheet, 10 gates on that
   sheet's own position that are ancestors of its outputs: 80 charges in all (RECORD 7). A circuit with
   fewer than 80 gates must use one gate for two sheets ("double service"). Circuits that never carry a
   whole-position component which is later cancelled (block-monotone circuits; the class contains all
   cancellation-free circuits) need at least 80 by this count, and at least 83 by an augmented count
   that adds, for one sheet with a reduction term, the gates living on its two neighbouring positions
   (RECORD 9). The 80 and the 83 are different arguments: a statement about the 80 charges does not
   automatically cover the augmented family. Since 2026-11-12 the same decomposition gives 84 for
   block-monotone circuits, because sheets 0 and 1 together need 21 gates in that class (RECORD 17).

The recorded 88 has, as a total, 8 gates more than the 80-gate circuits of the rotation-invariant model
without the three field-reduction terms; adding the terms one at a time gave 82, 85, 88 in short
heuristic runs. These are observed totals. They do not establish an unavoidable eight-gate overhead.

## Results by status

**Proved (complete argument in the record or the reports):**
- Evaluation bound G >= wt(x) + wt(Mx) - c(x); no point beats 56; the analysed forms of restriction
  reproduce parity; a two-point colour count forces nothing (RECORD 1, 5).
- Exact savings identity G = 2n + x - S and what a saving must consist of (RECORD 2).
- Row formula in the sheet language; the families Q_T and D_T (RECORD 3).
- Cyclic systems: L_cyc < L occurs; invariance under inverse, transpose, re-encoding. Leaf property:
  a value set with a SPECIFIED basis of triples is a circuit on those triples iff every nonempty subset
  of the basis contains a non-input element lying in exactly one member; a value set is a circuit set
  iff SOME basis of triples has this property (RECORD 6).
- Double maps D_T for reduced T (zero diagonal after the normalisation, no zero row, no zero column;
  without this the statements fail, e.g. T = 0 is the identity map with no gates): L >= 3m; zero extra
  cost iff T is a sum of arc blocks; helper-free circuits need 3m + delta gates (RECORD 8).
- Rotation model: L(Q_m) <= 10m for m >= 4; all-circuit lower bounds 7m - 1 + ceil(16m/11) (rotation/)
  and 9m - 7 (RECORD 16, from chains of adjacent sheets; larger from m = 13 on).
- The ten-gate sheet lemma, by hand (RECORD 10; two different proofs, both machine-reviewed). Until
  2026-11-12 it rested on finite computation; it no longer does. Consequently, with no computation:
  the charge theorem (at least 10 charged gates per sheet in every MixColumns circuit, RECORD 7); every
  block-monotone MixColumns circuit has at least 80 gates (RECORD 7) and at least 83 (RECORD 9; the
  three-term sheet costs at least 13, also by hand); a sheet with nothing free costs exactly 12.
- Sheets with pairwise disjoint windows cannot share at a net gain: in every circuit, any such family
  of r sheets is served by at least 10r gates, even if single gates serve several of them (RECORD 11).
- Sheets 0 and 1 of MixColumns with position 7 free (RECORD 17; delegated, machine-reviewed): at least
  20 gates in every circuit; at least 21 when nothing feeding sheet 0 touches sheet 1's own position,
  which holds in block-monotone circuits. Hence every block-monotone MixColumns circuit has at least
  84 gates (30 + 21 + 33; previously 83). A restricted class; the bound for all circuits stays 75. The
  eleven-gate lemma this rests on, formerly only computed, is now proved by hand.
- Two adjacent sheets cannot share at a net gain either: with the first neighbour free, the pair needs
  20 gates in every circuit (RECORD 15; by hand, machine-reviewed). For MixColumns this covers the pairs
  (1,2) to (7,0), not the pair (0,1).

**Computer-assisted (each rests on a finite computation, named in the record, until a mathematical
proof replaces it):**
- L(M2) = 26 for the half-size quotient of MixColumns (RECORD 8).
- The upper bounds and "no period-1 scheme" statements for the rotation model (rotation/).
- The published 75 itself (finite facts and certificates of the published proof; unchanged here).

**Conditional:** the published argument proves L_cyc(MixColumns) >= 75 and hence L(InvMixColumns) >= 75
(conditional on the published proof; audit machine-reviewed with three repaired gaps).

**Conjectured:**
- The two joint local values of RECORD 9 are 22 and 36. If so, block-monotone circuits need 88 (an
  implication; the converse is not shown).
- L(Q_m) = 10m for m >= 4.
- eps(T) >= max(delta(T), delta(T^T)) for double maps with reduced T.

**Disproved (each with its counterexample in the record):**
- "Helpers never save" (h + y >= n).
- "The eight-block partition is the bit positions"; "an optimal circuit uses the natural partition".
- "2.5 n for the rotation model at every size" (false at three positions: 28 against 30).
- "All known 88s avoid cross-position cancellation": 77 % of the public corpus contain a gate that
  cancels a whole position. All circuits of that corpus have 88 gates with or without such a gate;
  this shows that those circuits gain nothing from it, not that nothing can be gained.
- "An 87 cannot be block-monotone" (an over-reading of the 83 bound; with RECORD 17 the excluded range
  is 83 and below, still not 87).

## The open questions that now carry the problem

1. **Double service.** When can sharing intermediate values across parts of a linear map reduce the
   size, and what forces a compensating cost? What is known now (RECORD 11-13):
   - In general it CAN pay even for unrelated parts: by a known counting argument (fast matrix
     multiplication), n copies of a generic large matrix are cheaper together than apart. No small or
     explicit example is known; any example needs both parts with at least four helper gates.
   - For sheets with disjoint windows it never gives a net gain (proved, all circuits).
   - For two adjacent sheets it never gives a net gain: every circuit spends at least 20 gates on such
     a pair (RECORD 15; machine-reviewed). The one mechanism that could undercut 20 is an "exit" (a
     vector of one sheet obtained in a single gate as the difference of two signals of the other); it
     saves gates on one sheet only by making all borrowed vectors odd, and then the other sheet's own
     computation needs four separate even vectors, 12 gates instead of 10.
   - For three positions, where every pair of windows overlaps, it gains 2 gates (28 = 30 + 9 over-charge
     - 11 double charges); no pair of that circuit is cheap (23, 24, 24), the saving is a wrap-around
     effect: given an expensive pair, the third sheet costs only 4 or 5 more gates.
   - For a chain of l adjacent sheets every circuit spends at least 9l + 2 gates (RECORD 16; by hand,
     given the pair theorem; the general statement not separately reviewed), against 10l attained. So a
     chain can share at a net gain of at most one gate per sheet beyond the second. For the rotation
     model this gives L(Q_m) >= 9m - 7, better than the earlier bound from m = 13 on.
   - Open: the tenth gate per sheet in chains of three or more (proved only when the mirror is
     level-monotone; the pair proof closes its tight case by a rigidity that is lost one level up),
     the ring with four or more positions, and the triangles of MixColumns, including the pair of
     sheets 0 and 1.
   - The 80-charge inequality has an order-free twin valid for all cyclic systems, with membership in
     a derivation in place of ancestry (RECORD 13, machine-reviewed). An argument using only those
     inequalities cannot exceed the cyclic minimum. The ancestor-based refinements (block-monotone
     bounds as stated, the 83) are not covered by this. The wiring of the recorded best circuits is
     unique, so their sharing is a property of the value set.
2. **Two joint local problems** (sheets 0, 1 with position 7 free: between 20 and 22 for all circuits,
   21 or 22 for block-monotone ones; sheets 7, 3, 4 with positions 6 and 2 free: between 33 and 36),
   kept as test cases for arguments about shared costs.
3. **Is the cyclic minimum of MixColumns 88?**
4. (Closed 2026-11-12: the tenth gate of the local lemma is proved by hand, RECORD 10.)

## Computation actually performed in this study

The old G = 75 case-elimination campaign (SAT on configurations, the 280 open claims, the q = 4
enumeration) was not continued. The following finite computations were run, all on small objects, and
the record says where a statement rests on one:
- Exact optima of small maps by SAT (pysat/CaDiCaL): the isolated sheet and the local sheet lemma
  (several encodings), the rotation model with two positions (12 and 13 gates impossible), sheet
  schemes and their chaining (including 28 unsatisfiable period-1 instances), double maps with m = 3 and
  some with m = 4, a few joint local problems (several left undecided by timeouts).
- Exhaustive searches: all 2^26 target sets on 5 inputs and exact values on 6 and 7 inputs for cyclic
  systems; double maps with m <= 4 and ten with m = 5; the 8-block case of M2; the ten-gate lemma
  (48.5 million nodes).
- Heuristic search with the repository's engine, minutes per run, on rotation models with 4 to 8
  positions and with one to three extra terms.
- Read-only statistics on the public 88-gate corpus and on recorded circuits.
From 2026-11-12 on, by instruction, no further SAT or exhaustive computation is run in this phase;
existing results are used as facts with their status.
