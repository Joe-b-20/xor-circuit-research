# Shared computation between the sheets: the state of the argument (2026-11-12)

A synthesis of `RECORD.md` sections 7, 9-17. It changes nothing in the published statement
75 <= L(MixColumns) <= 88. All proofs are hand proofs produced with language-model assistance; "reviewed"
means a machine review by a second model instance, not a human review and not a formal verification.
Each claim carries its status; the detailed arguments are in the files named.

## 1. The question and the bookkeeping

A map is cut into parts (for MixColumns and the rotation model Q_m: the sheets, one per bit position).
Sheet j has an own block j and a window (blocks j-1, j; for MixColumns sheets 1, 3, 4 also block 7).
Computing one sheet alone, with the rest of its window free, costs 10 gates (proved by hand, reviewed,
RECORD 10); a three-term sheet with its two neighbour blocks free separately but not jointly costs 13
(RECORD 9.1).

**The counted families must be fixed before any identity is used** (corrected in phase 3, 2026-11-12; the
earlier text set lambda = 13 for a three-term sheet while counting D_j, which is false). "Ancestor" refers
to wires and includes the output gates themselves; "nonzero on a block" refers to the gate's value.
1. **Ordinary charges (the 80).** D_j = gates that are ancestors of an output of sheet j and nonzero on
   block j. |D_j| >= 10 for EVERY sheet of every circuit, three-term sheets included (RECORD 7). The
   baseline is 10 for every sheet; a three-term sheet can have |D_j| = 10 exactly (RECORD 9: tight
   13-gate local solutions with three mixed-neighbour gates occur), so no 13 may be attached to D_j.
2. **The augmented family (the 83).** F_3 = D_3 together with the ancestors of sheet 3's outputs that
   are zero on block 3 and nonzero on both block 2 and block 7. |F_3| >= 13 in every circuit (restrict to
   blocks 2, 3, 7 and apply RECORD 9.1; the extra gates are the M-gates there). The extra gates need not
   belong to any D_j. Only sheet 3 is augmented: the mixed gates of sheet 1 (blocks 0 and 7) and of
   sheet 4 (blocks 3 and 7) can lie in D_0 and D_3 even in block-monotone circuits, which is why the
   analogous augmentation of sheets 1 and 4 gives nothing. The 83 = 7 x 10 + 13 uses D_j (j != 3) and F_3,
   which are pairwise disjoint in block-monotone circuits.
3. **The grouped families (the 84).** G_256 = D_2, D_5, D_6 together (at least 30 in block-monotone
   circuits, where the three are disjoint; for all circuits only the pair bound 20 for sheets 5, 6 and
   the bound 10 for sheet 2 are known, and they may overlap); G_01 = the gates that are ancestors of an
   output of sheet 0 or sheet 1 and nonzero on block 0 or block 1 (at least 20 in every circuit, at least
   21 in block-monotone circuits, RECORD 17); G_734 = D_7 together with D_4 and F_3 (at least 33 in
   block-monotone circuits, where the three are disjoint). In block-monotone circuits the three groups are
   pairwise disjoint (each gate's
   support lies in the support of a sheet it serves, and the inspection of RECORD 7.2 applies), so
   30 + 21 + 33 = 84. G_01 contains, besides D_0 and D_1, sheet-1 ancestors that are nonzero on block 0
   but are not ancestors of sheet 0; these belong to no D_j.
For any families P_j with proved lower bounds lambda_j (|P_j| >= lambda_j in the class considered):

    G = sum of lambda_j + over + unch - excess                    (an identity, not a bound)

with over = sum of (|P_j| - lambda_j) >= 0, unch = gates in no P_j, excess = sum over gates of max(number of
families containing it - 1, 0), so that a gate in no family contributes 0, not -1 (corrected in phase 4;
RECORD 14 has the correct form). Sharing gives a net gain relative to these families exactly when
excess > over + unch. A "compensation theorem" for a class of circuits is a proof that this cannot
happen inside the class. Results for one choice of families (for example the 80 charges) do not carry
over to another (the augmented 83 or the grouped 84) without a separate argument.

## 2. What a shared gate has to do

A gate charged to two sheets is nonzero on both own blocks and feeds both. On its way to an output of
either sheet, its component on the other sheet's own block must disappear, and it can only disappear
against an identical component of another signal (proved for the sheet whose window misses the other
sheet's own block; RECORD 14, reviewed with that restriction). So every profitable sharing between
sheets is a cancellation of a whole own-block component. Two consequences:
- circuits that never cancel a whole block component (block-monotone circuits, which include all
  cancellation-free circuits) have excess = 0 and need at least 80 gates; a separate argument with
  augmented families gives 83 for them (RECORD 9; the 80 and the 83 are different arguments), and 84
  with section 6 below;
- in the transposed ("mirror") picture the same event is an *exit*: a vector of one sheet's group of
  variables obtained in a single gate as the difference of two signals that agree on another group.
  All the results below are statements about what exits can and cannot buy.

## 3. Where sharing is fully compensated (all circuits, no monotonicity assumed)

| Family of sheets | Result | What is counted | Where sharing lowers the count | What compensates | Status |
|---|---|---|---|---|---|
| r sheets with pairwise disjoint windows | at least 10 r | mirror gates (8r - c, c = classes of a parity partition) plus exports (3r + kappa) | groups of variables split over two parity classes lower the mirror count by at most kappa, the number of connected clusters of split groups (c <= r + kappa) | each cluster forces one more export (3r + kappa) | proved, reviewed (RECORD 11) |
| two adjacent sheets, first neighbour free | at least 20 | new first parts with exports (10); repeats, one per entry; gates of the second group (triple-sums and even labels) | an exit makes a triple-sum of the second group in one gate, so no even vector of that group is built (4 gates instead of 6 or 7) | all borrowed vectors are then odd, and the first sheet's own mirror needs four separate even traces: 12 gates instead of 10; the last unit by rigidity and parity | proved, reviewed (RECORD 15) |
| chain of l adjacent sheets | at least 9 l + 2 | as above, peeling the last sheet | the same exits at each level | only 9 of the 10 gates per further sheet are shown | proved given the pair theorem; machine-reviewed in phase 3 (RECORD 16) |

The pair theorem applies to the MixColumns pairs (1,2), .., (7,0) and to every adjacent pair of the
rotation model. The chain bound gives L(Q_m) >= 9m - 7.

## 4. Where sharing pays

- **In general it can** (RECORD 12; literature, with stated verification levels): for unrelated parts
  on disjoint inputs, a counting argument with fast matrix multiplication shows that a direct sum can
  be cheaper than the sum of its parts. No small or explicit example is known, and any example needs at
  least four helper gates in both parts.
- **Three positions** (RECORD 14; reproduced by the reviewer): the 28-gate circuit for Q_3 has
  28 = 30 + 9 - 11: eleven double charges against nine units of over-charge. Every pair of its sheets
  costs 23 or 24, well above 20; the third sheet then costs only 4 or 5 further gates. The saving is
  not located in any pair: it needs the three windows to close up, so that the sum of two vectors on
  blocks {i, j} and {j, k} with equal j-parts lands again in a window. That happens for m = 3 only.
  Whether 28 is optimal for Q_3 is not known (the proved range is 24..28).

## 5. The pattern, and what it does not yet say

The overlap pattern of the windows decides what is known:
- no overlap: no gain (proved);
- a path of two: no gain (proved); a longer path: a gain of at most one gate per further sheet
  (proved), conjecturally none. Since phase 3 (RECORD 18): a cut with no exit across it is additive
  (a circuit with no exit across cut k costs at least M_k + M_(l-k)), so a SHORTEST-length counterexample
  to 10 per sheet saves exactly one gate and has an exit across every cut; at the open end any exit
  costs the first sheet a gate (Lemma R); for three sheets only an adjacent exit (sheet 1 handing sheet 2
  a vector by cancellation) can produce a saving, and two residual configurations remain;
- a cycle of three: a gain of two is realised;
- a cycle of four or more (the rotation model with m >= 4), and the MixColumns pattern (an 8-cycle
  with the three extra windows through block 7): open. Nothing above bounds these as a whole; the
  families that are covered (non-adjacent sheets, adjacent pairs, runs avoiding the reduction terms)
  can overlap in their charged gates.

This is not a proof that sharing never helps for MixColumns, and it is not offered as one. In
particular it is NOT established that every circuit can be made block-monotone at no cost, nor that
the observed totals 80, 82, 85, 88 reflect an unavoidable overhead.

## 6. A reduction term on a shared block: the test case of sheets 0 and 1

MixColumns sheets 0 and 1 with block 7 free differ from the pair problem in one respect: sheet 1 also
needs the pair-sums on the free block. In the mirror only the export condition changes: the exports
must span a space containing the diagonal {(e | e)} instead of {(e | 0)} (`joint01/REPORT.md`;
delegated, reviewed). Known (RECORD 17):
- at least 20 for all circuits (the pair proof carries over), at most 22;
- at least 21 when nothing feeding sheet 0 touches sheet 1's own block, which holds in block-monotone
  circuits; so block-monotone MixColumns circuits need at least 84 gates;
- the reason for the extra gate in that class: a diagonal vector is not the sum of two inputs or
  targets of sheet 0, so it needs an auxiliary gate, and a sheet-0 circuit containing three independent
  diagonal vectors needs eleven gates, not ten (by hand; previously only computed). Either sheet 0 pays
  the eleventh gate or the vector is built outside both sheets' ten.
For arbitrary circuits 20 is not excluded; the remaining configurations all contain an exit or a
triple-sum built from one even vector. This is kept as a test of the method, not as a route to the
bound, and it does not establish an unavoidable overhead for the reduction terms.

## 7. Two remarks on method

- **Order of gates.** The 80-charge inequality has a twin that holds for all cyclic systems (RECORD
  13), so by itself it cannot exceed the cyclic minimum. The proof of the pair theorem, in its
  five-entry case, uses the order in which gates are created ("a cycle in time"). Phase 3
  (`causal-pair/REPORT.md`, reviewed in `review-causal-pair/`): the time-cycle step can be replaced by
  F_2 dependence ONLY for configurations already known to have the forest-plus-exits shape; without order,
  entries and exits are the same kind of relation and fibres need not be forests, so the pair theorem is
  not shown to be order-free, and the cyclic minimum is untouched. The non-executable borrowing loops
  examined there failed only for their particular wirings: the same value sets admit executable wirings of
  the same size. They establish no extra cost of executability and are retired as evidence (phase 5). Other
  uses of order remain open, to be pursued only from a concrete new obstruction.
- **Rigidity is not inductive.** The pair proof gets its last gate from a tight case in which a small
  mirror circuit is completely determined. One level up the corresponding circuit has room, and the
  same residual configurations return with one unit less slack. A proof of ten gates per sheet for
  chains needs a statement that carries a condition at both ends of the chain (`chain/REPORT.md`).
  Phase 3 made this precise (RECORD 18): the open end (free neighbour) is rigid at every length (Lemma R),
  and what is missing is the cost of a chain that receives one extra base vector, by an exit, at its open
  end. Proving M_3 = 30 would give only M_l >= 9 l + 3; ten per sheet for every l needs a uniform form of
  that missing statement.

## 8. Supplying versus receiving across a cut (phase 4, RECORD 19)

At the open cut of a chain the cost splits exactly into what the first sheet does (near1) and what the
rest does including one unit per label it hands over (far1). A value handed back by an exit can save the
receiver at most what it would cost to compute that value honestly from earlier labels, and the honest
computation also builds sums the receiver can reuse as exports (Lemma 2.1*). Proved (reviewed):
- if the first sheet uses exactly three entries, or if all its labels are even, the cut is additive at
  every length (Theorems 19.1, 19.2);
- with four entries, additivity holds except in one residual configuration (Omega1);
- the natural inequality "supplier's extra cost >= receiver's gain" is FALSE in its first two forms (SB,
  SB'): the first fails because unused entries can be piled up, the second because two pairs of "deep"
  labels with equal traces cost the supplier nothing; the repaired form SB* (gain measured after the
  receiver reuses the intermediate sums as exports) holds in every case checked and would give ten gates
  per sheet for every chain.
Phase 5 (RECORD 20): with independent clean labels, the supplier's transposed computation pays two gates
per exit and three spare gates for an exit needing four label types; this proves SB* for one exit, for
near1 = 10, and for four entries. Obstruction O: for MixColumns (and rings) any cut argument with
interface-independent baselines cannot exceed the sum of those baselines, which verified circuits put
below 88 at every cut.
What the interface must record, as learned from these counterexamples: the span of the labels (dimension,
intersection with the even space), the trace relations among the supplier's entries (free stacks), and
which intermediate sums the receiver can reuse as exports. A single number per side is not enough.

## 9. Open problems, in the order in which they would change the picture

1. SB* for one sheet (RECORD 19, 20): it would give ten gates per sheet for every chain. Open: several exits
   together carrying four or more types, and dependent clean labels with five or more entries. The chain
   of three (M_3 = 30 or 29): a 29 needs e1 >= 5, near1 >= 11 and two exits, or dependent labels.
1a. For MixColumns: a cut argument that carries the interface type (typed baselines), or an all-cuts
   argument (discharging from the charge theorem); Obstruction O rules out untyped single-cut arguments.
2. The ring with four positions: is L(Q_4) = 40? The proved range is 33..40.
3. Sheets 0 and 1 of MixColumns with block 7 free: 20, 21 or 22.
4. Any bound for MixColumns as a whole that uses the pair and chain results; none is known, and the
   public bound stays 75.
