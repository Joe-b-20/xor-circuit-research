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
   neighbour free, and that costs 10 gates. So every circuit has, for each sheet, 10 gates on that
   sheet's own position that are ancestors of its outputs: 80 charges in all (RECORD 7). A circuit with
   fewer than 80 gates must use one gate for two sheets ("double service"). Circuits that never carry a
   whole-position component which is later cancelled (block-monotone circuits; the class contains all
   cancellation-free circuits) need at least 80 by this count, and at least 83 by an augmented count
   that adds, for one sheet with a reduction term, the gates living on its two neighbouring positions
   (RECORD 9). The 80 and the 83 are different arguments: a statement about the 80 charges does not
   automatically cover the augmented family.

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
- Rotation model: L(Q_m) <= 10m for m >= 4; all-circuit lower bound 7m - 1 + ceil(16m/11) (rotation/).
- A sheet with nothing free costs exactly 12 (by transposition; tenth-gate/PROOF.md, under review).

**Computer-assisted (each rests on a finite computation, named in the record, until a mathematical
proof replaces it):**
- The ten-gate sheet lemma (exhaustive search certificate `review-charges/lemma_exh.c`, plus SAT runs).
  A hand proof is proposed in `tenth-gate/PROOF.md` and is under independent review; until that review
  is in, the lemma and everything below it stay computer-assisted. By hand alone only 9 is established,
  which would give 12 for the three-term sheet and 75 for block-monotone circuits.
- Charge theorem: at least 10 charged gates per sheet in every MixColumns circuit (RECORD 7).
- Every block-monotone MixColumns circuit has at least 80 gates (RECORD 7) and at least 83 (RECORD 9).
- L(M2) = 26 for the half-size quotient of MixColumns (RECORD 8).

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
- "An 87 cannot be block-monotone" (an over-reading of the 83 bound: only 82 and below are excluded).

## The open questions that now carry the problem

1. **Double service.** When can sharing intermediate values across parts of a linear map reduce the
   size, and what forces a compensating cost? The three-position rotation model shows it can help.
   For MixColumns and for four or more positions nothing is decided.
2. **Two joint local problems** (sheets 0, 1 with position 7 free: between 20 and 22; sheets 7, 3, 4 with
   positions 6 and 2 free: between 33 and 36), kept as test cases for arguments about shared costs.
3. **Is the cyclic minimum of MixColumns 88?**
4. **The tenth gate of the local lemma by hand** (proposed proof under review).

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
