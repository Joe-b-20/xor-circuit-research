# Superposition: a refutation of the distinct-charge conjecture, and what removal costs (phase 9)

Main agent (Opus 5.5), 2026-11-12. The construction is the user's (hand construction, circuit, generator and
verifier were described as attached; the attachment was not available in this session, so the circuit was
rebuilt from the description and verified here). Status words: **proved** (hand argument; machine review in
`witness/review/REVIEW.md`, not human review), **check** (direct evaluation of the specified circuits; no SAT,
no search, no enumeration, no least-gate computation). Nothing here changes 75 <= L(MixColumns) <= 88.

## 1. The counterexample (proved; verified)

Construction (MixColumns; x_(c,j) = bit j of byte c, block j = the four x_(c,j)):
1. z_c = XOR of x_(c,0), ..., x_(c,7) (a chain, 7 gates per byte: 28 gates).
2. H_c = XOR of the other three z (6 gates: a = z0 + z1, b = z2 + z3, H_0 = z1 + b, H_1 = z0 + b, H_2 = a + z3,
   H_3 = a + z2). On every block j, the part of H_c is E_c(j): H_c carries the own-block part of output (c, j)
   for all eight sheets at once.
3. For each output y_(c,j): r_(c,j) = H_c + y_(c,j) has zero part on block j; build it as a chain of input sums
   in a fixed order, reusing a value already present; then y_(c,j) = H_c + r_(c,j).

**Proposition S.** For any fixed order of the remainder sums such that no value created or reused in step 3
before an output equals an output value (hypothesis H; it holds for the two orders used here and is verified by
the reviewer; without it the count can rise: the reviewer built orders giving 69 and 86), the circuit computes MixColumns and exactly 66 of its gates are charged to some sheet (F_j = ancestors of sheet j's rows nonzero on block j):
the 34 gates of steps 1-2 and the 32 outputs.
*Proof of the charge count.* A gate of z_c's chain feeds the three H_(c') with c' != c, and each H feeds the
eight outputs y_(c',0..7); so every global gate (steps 1-2) is an ancestor of rows of all eight sheets, and it is
nonzero on some block j: charged. Every output is nonzero on its own block. Every gate created before the outputs
adds two values with disjoint input supports (a chain step adds an input not yet in the accumulator; the z and H
steps join disjoint bytes), so along such gates supports only grow, and every ancestor of a node has support
inside that node's support; this survives reuse, because by H a reused node is itself such a gate or a global
(not an output), and each output y_(c',k) is built as H_(c') + r_(c',k). The
ancestors of y_(c',k) are H_(c') with its ancestors and r_(c',k) with its ancestors; the latter all have support
inside supp(r_(c',k)), which misses block k. So a remainder gate (created in step 3, not an output, not reused
from step 1) is charged to no sheet. QED Hypothesis H is what the charge count needs. Reducedness, full liveness and "no intermediate equals a
target" are verified only for the two fixed orders used here (witness/build_witness.py asserts them); for an
arbitrary order satisfying H, full liveness needs dead-gate pruning or a further argument (pruning removes only
gates that are ancestors of no output, hence charged to no sheet, so it leaves the count 66 unchanged).
**Check (witness/build_witness.py).** Distinct charged 66 (34 + 32), E = 140, R = 154, |F_j| = 38, 38, 34,
30, 26, 22, 18, 14. G depends on the order of the remainder sums: 616 (inputs by wire), 521 (by block); the
user reports 604 for its order. U = G - 66. G is irrelevant to the refutation. U >= 455 is not a lower bound over orders (the reviewer has an order with
U = 446); in every order tried G >= 515, so the witness says nothing about near-minimal circuits.
**Rotation model (check).** The same construction for Q_m (m = 4, 5, 6, 8) gives 8m + 2 distinct charged gates
(34, 42, 50, 66; hand count 4(m - 1) + 6 global + 4m outputs), with G = 141, 218, 307, 521.

**What is refuted.** (i) The distinct-charge conjecture of phase 7 (|union F_j| >= 80 for every MixColumns
circuit) and Conjecture G of phase 8 for MixColumns (girth 4): 66 < 80. (ii) For Q_m, m >= 4, the strong form
|union F_j| >= 10m (Q_4: 34 < 40). Both conjectures quantified over every circuit; the witness is reduced and
fully live, so ordinary reducedness does not repair them. **Not refuted:** a total lower bound G >= 80 (or
L(Q_4) = 40); E + U >= R holds here with a large margin; distinct-charge statements restricted by size or by U
(the witness is far from minimal); the known circuits and 75 <= L <= 88 are unchanged.

**Consequence (proved): a limitation of charge-union arguments.** Any lower bound on |union_j F_j| valid for all
MixColumns circuits is at most 66, below the published 75; for Q_m at most 8m + 2. So no UNCONDITIONAL lower bound on the distinct
charged gates (one valid for every circuit) can improve the current bound; a charge argument must either bound the
uncharged work U (the work of separating shared values) or use a hypothesis on the circuit (size, structure)
with a structural role.

## 2. Theorem K survives, and what it does not say

Theorem K (cancel/CANCEL.md) is untouched: in the witness every global gate g charged to sheets j, k reaches
y_(c,j) through the single exit y_(c,j) = H_c + r_(c,j), which cancels the blocks of H_c outside W_j; the
off-path operand r_(c,j) occupies seven blocks and is confined to no MixColumns window (no own block l of r has
B(r) inside W_l). K permits exactly this ("non-confined or escaping partner") and bounds nothing about its cost.
Corrections of interpretation (applied in CANCEL.md):
- *Confinement is a support condition.* "Confined with own block l" does not imply membership in F_l; that
  needs ancestry of a sheet-l row.
- *One-chase-exit closures in MixColumns need a non-confined or escaping partner*, not an uncharged one: a
  non-confined partner may be charged through other paths (here r is uncharged, but nothing forces that).
- *The chase-exit count is per selected pair of paths from one shared gate*, not a count of distinct expenses:
  in the witness one exit (an output gate, the only exit on these paths) closes the cancellations of all 34
globals towards that output (on paths that enter the output through r's chain the off-path operand is H_c,
also non-confined; when k lies in W_j there is no chase exit on that side).
So K organises which partner configurations can occur; it contributes no constraint on their cost or on how
often one partner or exit is reused. It is a classification, not a gate-count argument.
Sheet-system repair (CANCEL.md section 0, Lemma W): the ten-gate premise needs each window to contain a non-own
block (a sheet with W_j = {j} is a bare E-sheet and costs fewer than 10), and Lemma W's projection must keep j and
an actual non-own block n_j of W_j (for MixColumns and Q_m, n_j = j - 1), not assume j - 1 is present.

## 3. What removal costs: three mechanisms side by side

**Lemma S1 (removal copies the unwanted part; proved).** If e = a + a' is a gate whose support misses a block c
present in a (c cancelled), then a' has the same nonzero c-part as a. In particular if an output y = h + r with
h shared, then r agrees with h on every block of h outside W(y): the remainder carries a second copy of the
unwanted component. (Immediate from e's c-part being 0.)
The three diagnostic examples differ in where that second copy comes from and how often it is reused.

| example | shared value | unwanted part | where its copy lives | reuse | charge balance |
|---|---|---|---|---|---|
| Q_3 (28 gates) | gates charged to two sheets | the third block | the third sheet's own charged work (Theorem K, one exit; gamma = 3) | 4 exits for 11 double charges | E 9, R 11, U 0: saves 2 in G |
| MixColumns triangle (88) | the {1,2} chain (3 gates) | block 2 | one uncharged partner [2:s 7:s], label-type work of sheet 3 | one partner, one exit for all 3 | E >= R in every sampled circuit |
| superposition (521-616) | H_c (all 8 own blocks) | 5 or 6 blocks per output (H_c outside W_j; the full remainder r occupies 7) | 32 uncharged remainders | prefix reuse among remainders | E 140, R 154, U 455-550 (orders used) |

So the charged deficit R - E can be real and large (14 for MixColumns, 2m - 2 for Q_m), but in the
superposition witness it is paid many times over by the uncharged remainders. In Q_3 the copy is already present as another sheet's charged work; that a partner is used or charged elsewhere
does not by itself show that its marginal cost is zero (Q_3 is the only one of the three whose total G falls
below 10 per sheet, a fact about the whole circuit, not a cost attribution).

**The dual accounting (proved identity; check).** For a fully live circuit with every input used,
G = sum over all nodes v (inputs and gates) of (d(v) - 1), where d(v) = number of gates reading v plus 1 if v is
an output. (Sum of d is 2G + 32; there are G + 32 nodes.) This is the gate count of the transposed circuit C^T
(each node with d terms becomes d - 1 XOR gates), which computes M^T with G(C^T) = G(C) (the raw transpose; it
need not be reduced). It charges reuse (fan-out) instead of content; in the witness the inputs are read up to 22
times by the remainder chains.

**Two-sided charging fails (check, reviewer-corrected).** M^T is a sheet system (windows {b, b+1}, plus
{0, 1, 3, 4} for b = 7; directed girth 4). The distinct charged count of a transpose depends on the order of the
XOR chains: for the block-order witness, 495 (chains in reader order), 66 (reverse order; still 66 after
removing duplicate values), 231-339 (random orders); for the wire-order witness 608, 72, 303-389; the recorded
88/89 give 82-87 for their transposes. So the block-order witness C and its reverse-order transpose C^T both have
66 distinct charged gates: a circuit "superposed on both sides" exists, and the question "does every circuit
satisfy max(|union F(C)|, |union F(C^T)|) >= 80 for a fixed transposition rule" is answered negatively for that convention (the transpose built by one fixed chain rule, here reverse reader
order); other transposition strategies are not ruled out. The variant "some transposition of C has at least
80 charged gates" is sufficient for G >= 80 (every transposition of C has G(C) gates, at least its charged
ones); the reverse implication is not established, so the two are not shown to be equivalent. An earlier draft's sentence "the work uncharged on one side is charged on the other"
was an artefact of the reader chain order and is withdrawn. Conclusion: the fixed-rule transposition tested does not repair the charge framework; charging remains a
content count that superposition can defeat on either side of that convention.

## 4. Scope, gap, next direction

Proved: Proposition S (under H) and its consequences (refutations; the cap 66 on unconditional charge-union
bounds); Lemma S1; the dual identity. Checks: the numbers above, for the specified circuits only. Refuted by an
explicit pair: two-sided charging for one fixed transposition rule (not every transposition strategy). Theorem K: retained, reinterpreted as a
classification. Not established: any lower bound on U in terms of R - E, or any inequality that combines reuse
of partners, exits or remainders into a cost.
What remains between the charge framework and a total bound is the separation work: G = 80 + (E - R) + U with
E - R = -14 in the witness and no lower bound on E - R known in general, and U unbounded above;
a cost principle must bound U from below in terms of how much shared content is cancelled, allowing reuse.
**Next direction proposed in phase 9 (examined and abandoned in phase 10: `../copies/COPIES.md`; the
intuitions below about the three examples were not borne out by one consistent definition).** Leave content charging (and its transpose) and count the copies that
cancellation forces. By Lemma S1, removing a shared value's part on blocks outside an output's window requires a
second copy of that part; for one shared value h serving t sheets the required copies u_j = h restricted outside
W_j are t vectors whose span depends on the windows (it can be small: with coinciding windows, as in Q_2, they
coincide; in the witness it is large). A copy-rank
statement of the form "the gates that produce these copies, wherever they sit and however they are reused, number
at least the rank of the copies that are not already values needed for other outputs" would combine globally (a
rank is not double counted when one partner serves several cancellations) and would separate the three examples:
in Q_3 the copies are other sheets' required values (no extra rank), in the triangle one copy serves three
double charges (rank 1), in the superposition witness the copies have high rank and are paid by the remainders.
Its first test is whether "already needed for other outputs" can be defined so that the rank count is a lower
bound on gates, not a restatement of G >= 80.

## 5. Review status

`witness/review/REVIEW.md` (machine review, own code and own construction, not human review): witness circuits
CORRECT (both orders: union 66, E 140, R 154; G 616, 521); order-independence of 66 needs hypothesis H (orders
violating it give 69, 86); Proposition S CORRECT WITH FIXES (H made explicit); Q_m CORRECT (8m + 2);
"at most 66" CORRECT for unconditional bounds; Theorem K compatibility CORRECT WITH FIXES; Lemma S1, the dual
identity CORRECT; transposition numbers depend on chain order (reverse order gives 66 on the transpose), so the
"uncharged on one side is charged on the other" reading was WRONG and is withdrawn; fixes applied above.
