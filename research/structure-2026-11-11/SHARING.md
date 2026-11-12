# Shared computation between the sheets: the state of the argument (2026-11-12)

A synthesis of `RECORD.md` sections 7, 9-17. It changes nothing in the published statement
75 <= L(MixColumns) <= 88. All proofs are hand proofs produced with language-model assistance; "reviewed"
means a machine review by a second model instance, not a human review and not a formal verification.
Each claim carries its status; the detailed arguments are in the files named.

## 1. The question and the bookkeeping

A map is cut into parts (for MixColumns and the rotation model Q_m: the sheets, one per bit position).
Sheet j has an own block j and a window (blocks j-1, j; for MixColumns sheets 1, 3, 4 also block 7).
Computing one sheet alone, with the rest of its window free, costs lambda = 10 gates (13 for a
three-term sheet); proved by hand, reviewed (RECORD 10).

For any circuit let D_j be the gates that are ancestors of an output of sheet j and nonzero on block j.
Then |D_j| >= lambda_j for every circuit (RECORD 7), and

    G = sum of lambda_j + over + unch - excess                    (an identity, not a bound)

with over = sum of (|D_j| - lambda_j), unch = gates charged to no sheet, excess = sum over gates of
(number of sheets charging it - 1). Sharing gives a net gain exactly when excess > over + unch. A
"compensation theorem" for a family of sheets is a proof that this cannot happen inside the family.

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
| chain of l adjacent sheets | at least 9 l + 2 | as above, peeling the last sheet | the same exits at each level | only 9 of the 10 gates per further sheet are shown | proved given the pair theorem; general statement not separately reviewed (RECORD 16) |

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
  (proved), conjecturally none;
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
  five-entry case, uses the order in which gates are created ("a cycle in time"). Whether the pair
  bound of 20 also holds for cyclic systems has not been examined; the remark only records that this
  proof, unlike the earlier counting arguments, is not visibly order-free.
- **Rigidity is not inductive.** The pair proof gets its last gate from a tight case in which a small
  mirror circuit is completely determined. One level up the corresponding circuit has room, and the
  same residual configurations return with one unit less slack. A proof of ten gates per sheet for
  chains needs a statement that carries a condition at both ends of the chain (`chain/REPORT.md`).

## 8. Open problems, in the order in which they would change the picture

1. Ten gates per sheet for a chain of three (M_3 = 30), or a 29-gate chain.
2. The ring with four positions: is L(Q_4) = 40? The proved range is 33..40.
3. Sheets 0 and 1 of MixColumns with block 7 free: 20, 21 or 22.
4. Any bound for MixColumns as a whole that uses the pair and chain results; none is known, and the
   public bound stays 75.
