# Sharing between sheets with overlapping windows

Report of the delegated investigation of 2026-11-12, saved by the main agent from the investigator's
final message. Machine work; hand proofs unreviewed at the time of saving (review status in
`../RECORD.md` section 14). No SAT and no circuit search were run; programs inspect existing circuits or
verify hand designs. Dependency: the r = 1 case of INDEPENDENT-SHEETS.md Theorem 1 ("a circuit on four
inputs containing the four triple-sums, with tau signals spanning the even vectors, has |T| + tau >= 10").

**Corrections from the independent review (`../review-pair/REVIEW.md`), to be read with the text.**
Theorem 3.3 (the pair problem needs at least 19) is confirmed. **Proposition 4.1 is wrong as stated and
its bound is unproved** (a gate can reach the previous sheet the long way round through forward exits;
explicit 49-gate example). The "proved reductions" for a hypothetical 19 are partly unproved (see the
review for which sentences). Theorem 3.4 is correct once its induction is stated for mirror-form
circuits. Lemma 1.1 holds only for the sheet whose window misses the other sheet's own block. Sections 2
and 6 were reproduced independently.

## 0. Summary

**Strongest result (overlapping windows, all circuits).** For the pair problem (sheets j, j+1, block j-1
free, nothing else free) the minimum is at least 19; the upper bound is 20. As a statement about
circuits: in every circuit for Q_m (m >= 3), and for MixColumns on the pairs (1,2), (2,3), (3,4), (4,5),
(5,6), (6,7), (7,0), at least 19 gates are ancestors of an output of the pair and nonzero on one of its
two own blocks. No monotonicity is assumed. The pair (0,1) is not covered.

**Second result (path, restricted class).** If the mirror of a run of l consecutive sheets is
level-monotone (no gate cancels the leading group of both operands), the run needs at least 10 l gates.
Every recorded 10m circuit lies in the class on every run tested; the 28-gate Q_3 circuit violates it on
every pair.

**Not proved.** Pair = 20 (two residual configurations, section 3). The unconditional path statement.

**Observed (existing circuits only).** The pair count is at least 20 in all 19,356 MixColumns circuits on
all seven pairs, and equals 20 somewhere on five of them (this includes the non-monotone circuits). It is
20 on every pair of the recorded Q_m circuits (m = 4..8, 12), and 23, 24, 24 for Q_3.

**Q_3.** 28 = 30 + 9 (over-charge) - 11 (double charges), with no uncharged gate.

**Attempts to build savings: all failed, with accounts** (section 5).

## 1. Formulation

A map has parts (sheets) P_i, each with an own block B_i and a window W_i containing B_i. A local lemma
gives lambda_i: computing the restricted part from the units of B_i with W_i \ B_i free costs at least
lambda_i. For any circuit, D_i = gates that are ancestors of P_i and nonzero on B_i has |D_i| >= lambda_i.
With mu(g) = #{i : g in D_i}:

    G = sum of lambda_i + over + unch - excess,
    over = sum of (|D_i| - lambda_i),  unch = #{mu = 0},  excess = sum of (mu - 1)+.

This is an identity. "Sharing pays" means excess > over + unch. A compensation theorem for a class is the
inequality excess <= over + unch on that class.

**Lemma 1.1 (partner; proved, Q_m, m >= 3, all circuits).** If mu(g) >= 2 with sheets j != j', then on
every path from g to an output of one of the two sheets, the component of g on the own block of the other
sheet is cancelled, and the cancelling gate c = p + q has a second operand q carrying the identical
component on that block. Consequence: cancelling only non-own components never double-serves; a double
service needs an own-block cancellation and a partner.

**Proposition 1.2 (direct sums; proved, non-constructive).** There are matrices on disjoint inputs whose
direct sum is cheaper than the sum (Strassen's identities with one factor fixed, against counting). So
"gates new on both sides are compensated by gates new on neither" is false in general; any compensation
law must use the specific parts. (See ../direct-sum/REPORT.md for the literature.)

## 2. The Q_3 circuit

Source: q3_read.py, q3_read_out.txt.
- Supports: {0}: 1 gate, {1}: 1, {0,1}: 9, {1,2}: 8, {0,2}: 9. (The standard 10m circuits have 3-4
  single-block and 6-7 two-block gates per sheet.)
- Gates with mu = 2 (eleven, none higher): g4, g6 in window {0,1}, charged to sheets 1 and 0; g5, g8, g10
  in window {1,2}, charged to sheets 2 and 1; g3, OUT(3,0), g12, g14, OUT(2,0), g19 in window {2,0},
  charged to sheets 0 and 2. Every one is a two-block gate of window {j-1, j} borrowed by sheet j-1, the
  owner of its other block.
- Charges: |D_0| = 12 = 9 own-window + 1 single + 2 borrowed; |D_1| = 13 = 9 + 1 + 3; |D_2| = 14 =
  8 + 0 + 6. Over-charge 2 + 3 + 4 = 9, uncharged 0, excess 11. So G = 30 + 9 + 0 - 11 = 28.
- Cancelling gates (four, all triangles): OUT(3,0) = g6 + g8 cancels block 1; OUT(0,1) = g12 + g10 cancels
  block 2; OUT(1,2) = g15 + g14 and g23 = g17 + g19 cancel block 0. Three of the four are outputs: one
  gate is at once an output, the entry of the previous block's part, and the cancellation.
- Pairs: the pair counts are 23, 24, 24, so no pair is below 20. The saving is not visible in any pair
  problem; it is a wrap-around effect.

**Lemma 2.1 (transfer; proved).** Let u, v have supports {i,j}, {j,k} and equal j-parts. Then u + v has
support {i,k}. This is a window exactly when m = 3. For m >= 4 a chain of such transfers reaches a window
only by backtracking or after m - 2 gates, of which m - 3 produce vectors lying in no window.

**Observed (lift; a count under a lifting model, lifted circuits not written out).** Lifting the Q_3
circuit to 6 or 9 positions forces 7 gates to exist in two lift classes: 70 and 105 gates, against 60
and 90.

**Correction to a remark of the main agent.** A vector on blocks j-1, j+1 is not automatically
uncharged: its mu can be 0, 1 or 2. What Lemma 2.1 supports is weaker: for m >= 4 each transfer produces
at least one gate outside every window.

## 3. The pair problem

**Mirror form.** K = |T| + tau. T is a circuit on w_0..w_3, w'_0..w'_3 containing
A_i = E_i(w) + w'_(i-1) + w'_i and B_i = E_i(w'); tau of its signals span a space containing Even(w) + 0.
(mirror.py builds T from an existing circuit; K - tau = |T| was checked on all examples.)

**Definitions.** Write a signal as (omega | s). For omega != 0 the fibre Phi_omega is the set of signals
with first part omega. A gate with omega != 0 is *first* if it is the earliest signal of its fibre,
otherwise a *duplicate*. Let f_w, D, N_0 be the numbers of first gates, duplicates, and gates with
omega = 0; |T| = f_w + D + N_0. An *entry* is a gate a + pi with omega(pi) = 0 != omega(a); tau' is their
number.

**Lemma 3.1 (proved).** (a) f_w + tau >= 10. (b) D >= tau' >= 3, and the s-part of every signal with
omega != 0 lies in the span Pi of the s(pi) over entries. (c) N_0 >= 4. (d) If tau' = 3 then N_0 >= 7.
*Proof.* (a) A first gate has both operands with omega != 0 in other fibres. Keeping one gate per fibre
gives a circuit on w with f_w gates whose masks are the occurring first parts; it contains the E_i(w),
and the projections of the exports span Even(w). Apply the r = 1 theorem. (b) An entry repeats the first
part of a, so it is a duplicate; the span statement is by induction over gates; the s-parts of the A_i
span Even(w'), of dimension 3. (c) The B_i are four distinct gates with omega = 0. (d) Three vectors
spanning a space containing Even(w') form a basis of it, so the three pi are distinct signals with
omega = 0 and nonzero even s; they are not inputs (odd s) and not B_i (odd). QED

So K = (f_w + tau) + D + N_0 >= 10 + D + N_0: 20 if tau' = 3, and at least 18 otherwise.

**Lemma 3.2 (proved).** D = tau' = 4 together with N_0 = 4 is impossible.
*Proof.* The signals with omega = 0 are the w'_k and the four B_i; no two of them sum to a vector of
weight 3, so each B_i = g + g' with g, g' in one fibre. Every non-first element of a fibre is an entry
attached to an earlier element of the same fibre, so fibres are trees with four edges in total, labelled
by s(pi), and s(g) + s(g') is the label sum along the tree path. Let B_d be the earliest B: its path uses
only unit labels, so it consists of exactly three edges labelled by the units other than w'_d. Pi must
contain a vector with coordinate d; a label B_l with l != d would need a path sum with coordinate d
before any such label exists; so the fourth label is w'_d. Then each B_l is a 3-edge path formed by the
three edges other than the one labelled w'_l; a tree with four edges has at most two 3-edge paths. QED

**Theorem 3.3 (proved by hand, given the r = 1 theorem).** The pair problem needs at least 19 gates.
*Proof.* K <= 18 forces tau' >= 4 and D + N_0 <= 8, hence D = 4 = tau' and N_0 = 4, contradicting 3.2. QED
(For MixColumns, pair_corpus.py checks against the matrix that exactly the pairs (1,2), ..., (6,7), (7,0)
restrict to the pair problem.)

**What a 19 would have to be (proved reductions).** f_w + tau = 10, so the first sheet's own mirror is
optimal (7 gates with three even exports, or 6 gates with tau = 4); tau' >= 4; and one of:
- **(R1)** N_0 = 5, D = tau' = 4: the gates with omega = 0 are the B_i and one even P. Checked only
  briefly: at least three of the four entries are unit-labelled and form a path in one fibre, and at
  least one of the B_i or P is a T-exit.
- **(R2)** N_0 = 4, D = 5: all four B_i are T-exits; exactly four duplicates are entries, labelled by the
  four units; the fifth is a non-entry duplicate (five entries are excluded by a tree argument like 3.2).
In both, the symmetric decomposition by second part gives K = tau + N_10 + f_w' + D' with f_w' >= 8 and
D' >= 4, so at most one second part beyond the four B_i and the four cyclic pair-sums occurs anywhere in
T. (R1) and (R2) are not closed.

Primal meaning of a T-exit: a signal on which no sheet-j target formally depends, but which is read by
ancestors of sheet j, its contributions cancelling.

**Observed.** Minimum pair count 20 over all existing circuits. Standard circuits have
(K, tau, |T|, f_w, D, N_0, tau') = (20, 3, 17, 7, 3, 7, 3) and no exits. Conjecture: the pair problem is 20.

**Theorem 3.4 (level-monotone mirrors; proved).** For a run of l sheets with first neighbour free, let
the level of a mirror vector be the first group where it is nonzero. If, for some order of accumulating
readers, every nonzero gate g = a + b of T has level(g) = min(level a, level b), then K >= 10 l.
*Proof.* Delete zero gates. Induct on l. Level-monotonicity makes the gates of level >= 2 a circuit T_2
on the remaining groups, itself level-monotone, containing the required vectors of the shorter run. By
3.1(b) the entry operands are at most tau' of its signals and span a space containing
Even(second group) + 0. So |T_2| + tau' >= 10(l - 1), and K >= (f_w + tau) + tau' + |T_2| >= 10 l. QED
*Scope.* pathstats.py finds no exits on every run tested of the recorded Q_4, Q_5, Q_7, Q_8 circuits
(l = 2, 3, 4, 7), and 1-2 exits on every pair of Q_3. The class is not comparable with block-monotone
circuits in general. For Q_m it gives 10(m - 1).

## 4. Window-local circuits

**Class (W1).** For every gate, the supports of both operands lie in one common window. Trimmed
block-monotone circuits satisfy it for m >= 3. The four triangle gates of Q_3 are exactly its violations
there.

**Proposition 4.1 (proved, m >= 3).** In a (W1) circuit a gate has mu = 2 only if it lies on {j, j+1} and
reaches sheet j through a backward exit: a block-j gate h = u + v with u, v on {j, j+1} having equal
(j+1)-parts, and h serving sheet j. Let H_j be the set of values of such exits on block j. Then

    G >= 10m - sum over j of (L(H_j) - |H_j|) >= 10m - 2 #{j : H_j nonempty},

where L(H) is the least number of XORs computing H from the four units of the block.
*Proof.* Replace each such exit by an honest computation from the units; no gate then has mu >= 2, and
the charge theorem applies. For any set of non-unit vectors of F_2^4, two complementary pair-sums suffice
as extra gates, so L(H) <= |H| + 2. QED
So a (W1) circuit below 10m needs backward-exit values that are not self-generating: 1111, or a weight-3
vector with no pair inside it among the exit values.

**MixColumns, keeping the two arguments apart.** 80: G >= 80 - excess for all circuits. 83: Theorem 9.1
applies to every circuit, so |F_3| >= 13 always and G >= 83 - (number of extra family memberships). In
the eleven inspected non-monotone circuits the union of the eight families has 84 to 88 gates, with 0 to
6 gates in two families.

## 5. Attempts to build savings

- **Design A (verified; m = 4, 5, 8; designs.py).** Per sheet: pure gates s0, s2, d0, t = s0 + s2; then
  u1 = t(b) + s0(a), u2 = t(b) + s2(a), and six more two-block gates: 12 gates per sheet. Charges 11 per
  sheet, one uncharged gate, excess 0. The intended saving was the exit u1 + u2 = [previous block: t]; it
  replaces the gate t = s0 + s2 one for one, and it makes t of block j depend on t of block j+1 around
  the cycle, which is not a circuit.
- **Lift of Q_3.** 70 and 105 gates (section 2).
- **MixColumns through {1,2,7}.** This is what the corpus circuits do. For one corpus circuit by hand:
  the route [1:e2 2:d0], [1:s1 2:d0], [1:E3 2:d0], then + [2:d0 7:s3] = [1:E3 7:s3] uses 4 gates; the
  monotone route uses 4 gates plus [7:s3] if it is absent. The three {1,2} gates are charged to sheets 1
  and 2 (excess 3); the compensation is sheet 2 at charge 11, sheet 1 at 13, and the partner uncharged.
  Total 88.
- **Pair.** By 3.3 at most one gate can be saved, and only in configurations (R1) or (R2). None found.

## 6. Corpus inspection (corpus_inspect.py)

Eleven circuits (the first corpus circuit of each of nine cancellation patterns and two hunt records).
All satisfy 88 = 80 + over + unch - excess (e.g. 80 + 10 + 1 - 3; 80 + 5 + 6 - 3; the hunt records
80 + 12 + 2 - 6 and 80 + 12 + 1 - 5). In the seven inspected corpus circuits with excess (always 3) the
mu >= 2 gates have the same shape: three gates [1:x 2:v] with x a unit, then a pair, then E_c of block 1,
v an even vector of block 2, charged to sheets 1 and 2; the partner is [2:v 7:s_c] or a wider gate,
uncharged. Each of the eleven value sets has a sheet with two outputs not derivable from values inside
that sheet's support, so none has a block-monotone wiring. This establishes only that these circuits pay
for each double service by over-charge and uncharged partners.

## 7. Files

mirror.py; pathstats.py, run_pathstats.sh, pathstats_out.txt; pair_corpus.py, pair_corpus_out.txt;
family_check.py, family_check_out.txt; q3_read.py, q3_read_out.txt; corpus_inspect.py,
corpus_inspect_out.txt; designs.py, designs_out.txt.
