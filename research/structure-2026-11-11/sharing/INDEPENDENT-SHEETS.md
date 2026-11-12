# Sheets with disjoint windows cannot share profitably

Main agent, 2026-11-12. Status: **proved by hand; confirmed by an independent machine review**
(`../tenth-gate/review/REVIEW.md`, part B: every step sound, nothing to repair). Not a human review and
not a formal verification. No computer check is used. It contains a second, self-contained proof of the ten-gate sheet
lemma (the case r = 1), independent of `../tenth-gate/PROOF.md` Step 4.

## 1. Statement

**Local family problem.** Let b_1, .., b_r ("own blocks") and a set F of further inputs ("free part") be
given, each b_j with four inputs. *Base signals:* the 4r unit vectors of the own blocks, and EVERY vector
supported on F (zero and vectors meeting several blocks of F included), all at no cost. A local circuit
is a sequence of gates, each the XOR of two operands among base signals and earlier gates; nothing is
assumed distinct or nonzero. Targets: t_(j,c) = (E_c on b_j) + q_(j,c), j = 1..r, c = 0..3, where q_(j,c)
is supported on F and the free parts satisfy:

    (H)  a sum of q_(j,c) over a set I of pairs (j,c) is zero only if, for every j, I contains none or
         all four of the pairs (j, 0..3).

(For q_(j,c) = s_c placed on a block a_j of F, with distinct a_j, (H) holds because the s_c have rank 3
with the single relation s_0 + s_1 + s_2 + s_3 = 0.)

**Theorem 1 (independent sheets).** A local circuit that contains gates with the 4r target values has at
least 10r gates.

**Theorem 2 (consequence for circuits).** Let C be any circuit computing the rotation model Q_m or
MixColumns, and J a set of r sheets such that (i) the windows {j-1, j}, j in J, are pairwise disjoint,
and (ii) no output of a sheet of J has a nonzero part on the own block of another sheet of J. Then at
least 10r gates of C are ancestors of (or equal to) an output gate of a sheet of J and nonzero on the own
block of some sheet of J.

In words: among sheets with disjoint windows, one gate may serve several sheets, but the family as a
whole still needs ten gates per sheet. Double service between such sheets is always fully compensated.

*Condition (ii)* holds for every set of pairwise non-adjacent sheets of Q_m. For MixColumns it fails
when J contains sheet 7 together with sheet 1, 3 or 4 (their reduction term lies on block 7); e.g.
J = {0, 2, 4, 6} and J = {1, 3, 5} satisfy (i) and (ii), and for these (H) holds (check below).

## 2. Proof of Theorem 1

**Step 0 (cleaning).** Fix a gate for each target; delete the gates that are not one of them or an
ancestor of one. A gate whose two operands are free has a free value: delete it and let its readers read
that free vector; repeat. Now each gate has at most one free operand; the gates with exactly one are the
*entry gates* eps_1..eps_tau.

**Step 1 (formal inputs).** Replace the free operand of eps_i by a new input z_i, read only by eps_i.
This is an ordinary circuit on the 4r + tau inputs with the same K gates. Each gate g has a formal mask
(beta(g) | n(g)), n(g) in F_2^tau; its value is beta(g) + Phi n(g) for the linear map Phi sending the
i-th unit vector to the free operand of eps_i. For the target gates, beta = E_c on b_j and
Phi l_(j,c) = q_(j,c), where l_(j,c) = n of that gate.

**Step 2 (exports).** Index the coordinates of F_2^(4r) by the pairs (j,c) and let zeta_i be the vector
whose (j,c) coordinate is the i-th coordinate of l_(j,c). If the l_(j,c) over a set I sum to zero, so do
the q_(j,c), so by (H) I is a union of whole groups. Hence the left kernel of the matrix with rows l_(j,c)
lies in the span of the r group indicators, and its column space contains their orthogonal complement:

    (*)   span(zeta_1, .., zeta_tau) contains DE := the vectors of even weight on every group.

**Step 3 (mirror).** Transpose the circuit of Step 1 (PROOF Lemma 3.1; every signal is read at least
once, the target gates have a terminal use, the z_i are read once). The result T is a circuit on the 4r
inputs w_(j,c) with (2K + 4r) - (4r + tau + K) = K - tau gates in which every adjoint is the mask of a
signal. The adjoint of the unit (j,c) of b_j lists the targets containing it: the three other targets of
group j. So T computes the 4r triple-sums E_c(w^(j)), and the adjoint of z_i, which is that of eps_i, is
zeta_i. So:

    K = |T| + tau, where T is a circuit on 4r inputs in r groups of four computing the four triple-sums
    of each group, and tau of its signals (inputs, outputs or other gates; repetitions allowed) have
    masks spanning a space that contains DE.

**Step 4 (parity in the mirror).** Call a signal of T odd or even by the weight of its mask over all 4r
inputs. Inputs and outputs are odd. By the partition lemma (PROOF Lemmas 2.1 and 2.2, which hold for
every circuit with odd inputs): the even signals span the space of vectors even on every block of a
partition P of the inputs, with c blocks; the number of odd+odd gates is at least 4r - c; every odd signal
is congruent to an input modulo that space, so it has a block; every output is odd on exactly one block.
The 4r outputs are distinct odd non-input vectors, hence 4r distinct odd gates. So

    |T| >= 4r + (4r - c) = 8r - c.                                                              (1)

*Shape of a group.* The four inputs of group j meet the blocks in a pattern (4), (2,2) or (3,1): for
(2,1,1) the triple-sum omitting one input of the pair is odd on three blocks, for (1,1,1,1) every
triple-sum is. Call a group *split* if it meets two blocks, and let Gamma be the multigraph on the blocks
with one edge per split group. Let V be the set of blocks of positive degree and kappa the number of
connected components of Gamma on V. Every block contains an input; if it is not in V that input belongs
to an unsplit group, which lies in that single block. With sigma split groups, |V| <= sigma + kappa, so

    c <= |V| + (r - sigma) <= r + kappa.                                                        (2)

*Exports.* Let beta_P send a vector to its vector of block parities (in F_2^c); its kernel is the even
span. On the even vectors of a split group it takes the values 0 and (the sum of the two blocks of the
group); on an unsplit group it is 0. So beta_P(DE) is the span of the edge vectors of Gamma: dimension
|V| - kappa, and every block of V occurs in it. An even export has beta_P = 0; an odd export has beta_P =
the unit vector of its block. Let Z be the span of the exports and o the number of blocks that contain
an odd export. Then beta_P(Z) is the full coordinate space of those o blocks; it contains beta_P(DE), so
o >= |V|. And

    tau >= dim Z = o + dim(Z and ker beta_P) >= o + dim(DE and ker beta_P)
         = o + 3r - (|V| - kappa) >= 3r + kappa.                                                (3)

**Step 5.** K = |T| + tau >= (8r - c) + (3r + kappa) = 10r + (r + kappa - c) >= 10r by (1), (3), (2). QED

*Remark (r = 1).* This is the ten-gate lemma: kappa = 0 gives c <= 1, |T| >= 7, tau >= 3 (seven mirrored
gates and three entries); kappa = 1 gives c <= 2, |T| >= 6, tau >= 4.

## 3. Proof of Theorem 2

Set to zero every input outside the windows of J. By (3.1) of RECORD.md and conditions (i), (ii), the
outputs of a sheet j of J become (E_c on block j) + (a vector supported on the blocks j'-1, j' in J): the
latter blocks form the free part F. For Q_m the free part of output (j,c) is s_c on block j-1 and (H)
holds. For MixColumns and J = {0,2,4,6} the free parts are s_c on block 7 (sheet 0), on 1 (sheet 2), on 3
and 7 (sheet 4), on 5 (sheet 6); a vanishing sum restricted to blocks 1, 3, 5 forces whole groups for
sheets 2, 4, 6, and then block 7 forces a whole group for sheet 0: (H). For J = {1,3,5} blocks 6 and 7 are
zero and the free parts are s_c on blocks 0, 2, 4: (H).
Let A be the gates that are output gates of J or ancestors of one, and D the gates of A that are nonzero
on some own block of J. After the restriction a gate of A outside D has a value supported on F, hence
free; an input is a unit of an own block or free. So every gate of D is the sum of two values each of
which is free, a unit of an own block, or the value of an earlier gate of D: a local circuit of the
family problem containing the 4r targets (each is nonzero on its own block). By Theorem 1, |D| >= 10r. QED

## 4. What this does and does not say about sharing

- It is a statement about ALL circuits, with no monotonicity hypothesis: a gate nonzero on the own
  blocks of several sheets of J and feeding all of them is counted once, and the count is still 10r.
  So double service among sheets with disjoint windows never produces a net saving for that family.
- It does not bound the whole circuit by 10m: the sheets of Q_m split into two such families (even and
  odd sheets, for even m), each needing 5m gates, and a gate may belong to both families' sets. A circuit
  with fewer than 10m gates must contain a gate that is nonzero on an even block and on an odd block and
  is an ancestor of an even sheet and of an odd sheet.
- For m = 3 no two sheets have disjoint windows, so the theorem is empty there, consistent with the
  28-gate circuit.
- For MixColumns: at least 40 gates serve sheets 0, 2, 4, 6 (on blocks 0, 2, 4, 6), at least 30 serve
  sheets 1, 3, 5 (on blocks 1, 3, 5), at least 10 serve sheet 7 (on block 7). Inside each group nothing is
  counted twice, but the three sets can overlap, so this is not a total of 80; and each set may contain
  gates charged to no single sheet of its group. It concerns the original 80 charges, not the augmented
  83 argument.
- What remains is sharing between sheets whose windows overlap. The smallest instance is two adjacent
  sheets j, j+1 with block j-1 free ("the pair problem"): is its minimum 20?
