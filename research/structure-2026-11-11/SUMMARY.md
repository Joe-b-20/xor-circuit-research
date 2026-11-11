# What was learned (structural study, 2026-11-11)

A reader's guide to `RECORD.md`. Nothing here changes the published statement 75 <= L(MixColumns) <= 88.
Everything was produced with language-model assistance; reviews are machine reviews by a second model
instance, not human reviews and not formal verification.

## The picture

A circuit for MixColumns can be looked at in three ways, and each way sees a different part of the cost.

1. **As values at one input point (parity).** Signals of odd weight are the ones equal to 1 at the
   all-ones input. This forces 32 output gates and 24 gates that span the even signals: 56. It is the
   best any single evaluation point can do, restriction and gate elimination are the same count followed
   over time, and two points jointly force nothing more (RECORD 1, 5). This view cannot see why
   translation vectors are hard to reuse.

2. **As a system of 3-term equations (the published 75 argument).** Counting how the equations can share
   signals, given that the 64 boundary vectors have no relation of weight below 6, pushes 56 to 75. This
   view never uses the order of the gates. It therefore bounds a weaker object, a *cyclic system*, which
   can be strictly smaller than any circuit (smallest example: 6 against 7), and which is the same for a
   map and its inverse. Consequences: the published argument also gives 75 for inverse MixColumns
   (conditional on that argument); and no argument of this kind can be expected to reach 88 unless
   cyclic systems for MixColumns happen to need 88 as well, which is unknown (RECORD 6).

3. **As eight sheets, one per bit position (new).** Output (c, j) is "the other three inputs of position
   j" plus "the adjacent pair c, c+1 of position j-1", plus the same pair at position 7 for j = 1, 3, 4
   (RECORD 3). Setting all inputs outside two adjacent positions to zero leaves a single sheet with its
   neighbour free, and that costs 10 gates (a computer-checked 8-input fact). So every circuit has, for
   each sheet, 10 gates on that sheet's own position feeding its outputs: 80 charges in all (RECORD 7).
   A circuit with fewer than 80 gates must use one gate for two sheets, which requires a whole-position
   component that is cancelled later. Circuits that never do this (block-monotone circuits, a class that
   contains all cancellation-free circuits) need at least 83 gates (RECORD 9).

The recorded 88 reads, as a total, 80 for the eight sheets plus 8 for the three field-reduction terms;
the rotation-invariant model without those terms has explicit 80-gate circuits (RECORD 7, rotation/).

## Results by status

**Proved (complete argument in the record or the reports):**
- Evaluation bound G >= wt(x) + wt(Mx) - c(x); no point beats 56; restriction reproduces parity; two
  points force nothing (RECORD 1, 5).
- Exact savings identity G = 2n + x - S and what a saving must consist of (RECORD 2).
- Row formula in the sheet language; the families Q_T and D_T (RECORD 3).
- Cyclic systems: L_cyc < L occurs; invariance under inverse, transpose, re-encoding; the leaf property
  characterises circuits (RECORD 6).
- Double maps: zero extra cost iff the matrix is a sum of arc blocks; helper-free circuits need
  3m + delta gates (RECORD 8).
- Rotation model: L(Q_m) <= 10m for m >= 4; all-circuit lower bound 7m - 1 + ceil(16m/11) (rotation/).

**Proved with a small computer-checked fact (stated each time):**
- Charge theorem: at least 10 charged gates per sheet in every MixColumns circuit (RECORD 7).
- Every block-monotone MixColumns circuit has at least 80 gates (RECORD 7), indeed at least 83 (RECORD 9).
- L(M2) = 26 for the half-size quotient of MixColumns (RECORD 8).

**Conditional:** the published argument proves L_cyc(MixColumns) >= 75 and hence L(InvMixColumns) >= 75
(conditional on the published proof; audit machine-reviewed with three repaired gaps).

**Conjectured:**
- 88 is optimal among block-monotone circuits (equivalently the two joint local values are 22 and 36).
- L(Q_m) = 10m for m >= 4.
- eps(T) >= max(delta(T), delta(T^T)) for double maps.

**Disproved (each with its counterexample in the record):**
- "Helpers never save" (h + y >= n).
- "The eight-block partition is the bit positions"; "an optimal circuit uses the natural partition".
- "2.5 n for the rotation model at every size" (false at three positions).
- "All known 88s avoid cross-position cancellation" (77 % of the public corpus contain one gate that
  cancels a whole position, always involving positions 1, 2, 7; none of them gains a gate from it).
- "An 87 cannot be block-monotone" (my own over-reading of the 83 bound, caught by review: only 82 and
  below are excluded).
- Several intermediate claims of mine, found by the reviews and corrected in place.

## The open questions that now carry the problem

1. **Double service.** Can one gate usefully carry components of two unrelated sheets? The public corpus
   shows three shapes in which circuits already do it (a gate living on positions that no sheet uses
   together; a cancellation around positions 1, 2, 7; an exit onto two positions), and none gains a gate.
   For the rotation model with four or more positions, circuits whose gates stay inside sheet supports
   and whose exits are simple cannot gain (proved); no such statement is proved for MixColumns. A proof
   that double service never pays would lift 83 (and, with question 2, 88) from block-monotone circuits
   to all circuits. This is a direct-sum question.
2. **Two joint local problems** (sheets 0, 1 with position 7 free: between 20 and 22; sheets 7, 3, 4 with
   positions 6 and 2 free: between 33 and 36). If they are 22 and 36, block-monotone circuits need 88.
3. **Is the cyclic minimum of MixColumns 88?** If it is smaller, the published style of argument can never
   prove optimality, and time order is indispensable.
4. **The tenth gate of the local lemma by hand** (nine are proved by hand).

## What was not done

No SAT campaign, no case enumeration at G = 75, no search for an 87. The old queue (280 open claims,
q = 4 enumeration) was not touched. Heuristic runs were short and only on small models.
