# Two adjacent sheets need twenty gates

Main agent, 2026-11-12. Status: **proved by hand; confirmed by an independent machine review**
(`review/REVIEW.md`: every step of the proof correct; one wording gap in the normalisation and five
over-statements in the informal section 5, all repaired below). Not a human review and not a formal
verification. No computation is used in the proof. Dependencies, all proved by hand
and machine-reviewed earlier: the ten-gate lemma and its mirror (`../tenth-gate/PROOF.md`, Steps 0-3),
and the mirror form of the pair problem with Lemma 3.1(a) of `../sharing/REPORT.md`
(reviewed in `../review-pair/REVIEW.md`).

## 1. Statement

**Pair problem.** Blocks a, b, b' with four inputs each. Base signals at no cost: the units of b and of
b', and every vector supported on a. Targets: (E_c on b) + (s_c on a) and (E_c on b') + (s_c on b),
c = 0..3. A local circuit is a sequence of XOR gates on base signals and earlier gates.

**Theorem.** A local circuit containing the eight targets has at least 20 gates. (20 is attained.)

**Consequence for circuits** (by the translation checked in the review of the 19 bound): in every
circuit for the rotation model Q_m, m >= 3, and for MixColumns on the sheet pairs (1,2), (2,3), (3,4),
(4,5), (5,6), (6,7), (7,0), at least 20 gates are ancestors of an output of the pair and nonzero on one
of the pair's two own blocks. The pair (0,1) of MixColumns is not covered.

So two adjacent sheets, with the first neighbour free, cannot share at a net gain.

## 2. Mirror form and notation (from sharing/REPORT.md section 3; reviewed)

K = |T| + tau, where T is a circuit on the inputs w_0..w_3, w'_0..w'_3 that contains the vectors

    A_i = (E_i | p_i),   B_i = (0 | E_i),   i = 0..3,   p_i = u_(i-1) + u_i,

(first part over the w, second part over the w'; u_k is the unit vector of w'_k; E_i is the sum of the
three units other than the i-th), and tau of its signals span a space containing Even(w) + 0.

Take T with |T| + tau minimal. Then no gate is zero and no two signals (inputs or gates) have the same
value. Otherwise: a gate equal to an earlier signal is deleted and its readers read that signal; a zero
gate is deleted (and dropped from the list of exports if it is there), each reader 0 + x of it then
equals x and is deleted as a duplicate. Each step lowers |T| + tau and keeps the required vectors
(the A_i and B_i are nonzero).

Write a signal as (omega | s). For omega != 0 the *fibre* of omega is the set of signals with that
first part. A gate with omega != 0 is *first* if it is the earliest signal of its fibre (the inputs w_i
are the first signals of their fibres), otherwise a *duplicate*. f = number of first gates, D = number
of duplicates, N_0 = number of gates with omega = 0, so |T| = f + D + N_0. An *entry* is a gate a + pi
with omega(a) != 0 = omega(pi); its *label* is s(pi). Entries are duplicates. An *exit* is a gate x + y
with omega(x) = omega(y) != 0; it has omega = 0.

Known (reviewed): **(I)** f + tau >= 10. Also tau >= 3, and the B_i are four distinct gates with omega = 0.

Facts about the signals with omega = 0. They are the inputs w'_k (weight 1), the B_i (weight 3) and
N_0 - 4 further gates. **(E)** Every nonzero even vector that is the s-part of a signal with omega = 0
is the value of one of these further gates; so N_0 >= 4 + (number of distinct even labels).

## 3. The gates with omega != 0 form a sheet circuit

**Lemma A.** Take the w_i as the units of an own block and regard every vector (0 | s) as free. Then the
gates of T with omega != 0 are a local circuit in the sense of the ten-gate lemma, and it contains the
four targets (E_i | p_i) of that lemma (with a_c := u_(c-1), so that s_c = a_c + a_(c+1) = p_c).

*Proof.* A gate with omega != 0 has at least one operand with omega != 0; each operand is a unit w_i, an
earlier gate with omega != 0, or a signal with omega = 0, which is free. QED

Apply Steps 0-3 of the ten-gate proof to this local circuit. Cleaning keeps the A_i and their
ancestors among the gates with omega != 0: K_c <= f + D gates. Its entry gates are entries of T; call
them the *clean entries* g_1..g_t, g_j = a_j + pi_j, t = tau_c. Give g_j the formal input z_j in place of
pi_j; every signal v of the cleaned circuit gets a formal mask (omega(v) | n(v)), n(v) in F_2^t, and
s(v) = Phi n(v), where Phi sends the j-th unit vector to the label s(pi_j). With l_i = n(A_i) we have
Phi l_i = p_i. Let zeta_j in F_2^4 have i-th coordinate (l_i)_j. The mirror T* of the cleaned circuit is
a circuit on four inputs with

    |T*| = K_c - t                                                                           (II)

gates (for every order in which the contributions to an adjoint are summed), among whose signals are
the four triple-sums and every adjoint a(v); a(g_j) = a(z_j) = zeta_j; and a(v) is the sum of the
adjoints of the readers of v (plus one input of T* if v is one of the A_i).

Since the p_i span Even(w') and Phi l_i = p_i: the clean labels span a space Pi_c containing Even(w').

**Lemma B (four independent labels).** Suppose t = 4 and the labels s(pi_1..4) are a basis of F_2^4, with
o of them odd. Then every zeta_j has even weight, and the number of distinct nonzero vectors among
zeta_1..zeta_4 is 3 if o <= 2 and 4 if o >= 3. If o = 4, moreover, the zeta_j sum to zero, any three of
them are independent, and no zeta_j + zeta_k (j != k) is zero, a unit, a triple-sum or one of the zeta.

*Proof.* Phi is bijective, so l_i = Phi^(-1) p_i and (l_i)_j = lambda_j(p_i), where lambda_1..lambda_4 is
the basis of linear forms dual to the labels. The linear map Z: lambda -> (lambda(p_0), .., lambda(p_3))
has kernel {0, par}, par being the parity form (the forms vanishing on Even(w') = span of the p_i), and
its values have even weight because the p_i sum to zero. zeta_j = Z(lambda_j). Now par = sum of the
lambda_j over the odd labels. So zeta_j = 0 iff lambda_j = par iff the j-th label is the only odd one;
zeta_j = zeta_k (j != k) iff lambda_j + lambda_k = par iff the j-th and k-th labels are the only odd
ones. This gives the count. If o = 4, the sum of all zeta_j is Z(par) = 0; the image of Z has dimension
3 and is spanned by the four zeta_j, whose only relation is therefore the sum of all four; hence
zeta_j + zeta_k is nonzero, even, and equal to the sum of the other two zeta, which is not a zeta. QED

Distinct nonzero even vectors among the zeta_j are the values of distinct gates of T*, different from
the four gates carrying the triple-sums (odd). So in Lemma B, |T*| >= 7 (o <= 2) and |T*| >= 8 (o >= 3).

## 4. Proof of the theorem

Suppose K <= 19. By (I), D + N_0 <= 9.

**Step 1 (some clean label is odd).** If all clean labels are even, they span exactly Even(w'), so at
least three distinct even labels occur and N_0 >= 7 by (E); with D >= t >= 3 this gives D + N_0 >= 10.
So some clean label is odd, Pi_c = F_2^4, t >= 4, D >= 4 and N_0 <= 5.

**Step 2 (five or more clean entries).** If t >= 5 then D >= 5, so D = 5, N_0 = 4, and all five
duplicates are entries. This is configuration (X) below.

**Step 3 (four clean entries).** Let t = 4; the labels are a basis. By (E), N_0 >= 4 + (4 - o), so o >= 3.
By Lemma B and (II), f + D >= K_c >= 8 + 4 = 12. Hence

    K = (f + D) + N_0 + tau >= 12 + N_0 + 3.

If o = 3 then N_0 >= 5 and K >= 20. So o = 4, and K = 19 forces N_0 = 4, tau = 3, f + D = 12 = K_c and
|T*| = 8. Then every gate with omega != 0 is in the cleaned circuit, so every entry of T is a clean
entry: T has exactly four entries. By (I), f >= 7, so D <= 5: besides the four entries there is at most
one further duplicate h. This is configuration (Y) below.

In both configurations N_0 = 4: the gates with omega = 0 are exactly the B_i, and all signals with
omega = 0 are odd. A B_i (odd) is not the sum of two of them. Hence

    every B_i is an exit: B_i = x + y with x, y in one fibre and s(x) + s(y) = E_i,           (*)

and all labels are odd: units u_k, or E_l, the latter only for entries created after the gate B_l.

**Configuration (Y) is impossible.** T* has exactly 8 gates for every summation order, and by Lemma B
they carry 8 prescribed distinct vectors (four triple-sums, four zeta); so every signal of every such
T* is a unit, a triple-sum or a zeta.
- *No signal is the non-free operand of two entries.* If a_j = a_k = v, the adjoint a(v) has the
  contributions zeta_j and zeta_k; summing these two first (or, if there are no others, a(v) itself)
  puts zeta_j + zeta_k among the signals of T*, contradicting Lemma B.
- *No entry is the non-free operand of another entry.* If a_k = g_j, then zeta_j = a(g_j) is the sum of
  zeta_k and the other contributions; these are not empty (zeta_j != zeta_k) and their sum is
  zeta_j + zeta_k; summing them first (or the single one of them, which is an adjoint or an input of
  T*) again puts zeta_j + zeta_k among the signals of T*.
So the four entries are attached to four different signals that are not entries: first signals of
fibres, or h. A fibre therefore consists of its first signal r, at most one entry r + pi, and, for one
fibre only, h and at most one entry h + pi'. The sums of two signals of a fibre are: pi and pi', which
are values of existing signals and so not the value of a new gate; and the at most four cross sums
delta, delta + s(pi), delta + s(pi'), delta + s(pi) + s(pi'), where delta = s(r) + s(h). By (*) the four
B_i need four different sums, so these four are E_0..E_3 in some order. But the four cross sums add up to
zero and E_0 + E_1 + E_2 + E_3 = 1111. Contradiction.

**Configuration (X) is impossible.** Every duplicate is an entry, so each fibre is a tree: its first
signal is the root and each entry a + pi is joined to a by an edge labelled s(pi). There are five edges
in all. For x, y in one fibre, s(x) + s(y) is the sum of the labels on the path from x to y. By (*) each
B_i is given by a path P_i of the forest with label sum E_i, all of whose edges were created before B_i.
All labels are odd, so |P_i| is odd; |P_i| = 1 would make B_i equal to an existing signal. So |P_i| is 3
or 5, and the four edge sets P_i are different (their label sums are).

*Some |P_i| = 5.* Then the forest is one path with labels l_1..l_5 in order, and the other three B are
its three segments of length 3. Adding the four label sums: l_2 + l_4 = 1111, so {l_2, l_4} = {u_m, E_m}
for some m. By symmetry let l_4 = E_m, l_2 = u_m. The entry at position 4 was created after B_m, so the
segment of B_m avoids position 4: it is (1,2,3), and l_1 + l_3 = E_m + u_m = 1111, so
{l_1, l_3} = {u_q, E_q}. The segment (2,3,4) has sum 1111 + l_3, which must be a triple-sum: l_3 = u_q,
the sum is E_q, and l_1 = E_q; q != m since the segments have different sums. Now the entry at position
1 needs B_q first, B_q (the segment (2,3,4)) needs the entry at position 4, that entry needs B_m, and
B_m (the segment (1,2,3)) needs the entry at position 1: a cycle in time. Contradiction.

*All |P_i| = 3.* A forest with five edges has four different paths of three edges only if it is one of
two trees (count the paths by their middle edge: the number is the sum over edges xy of
(deg x - 1)(deg y - 1); the six trees with five edges give 3, 0, 3, 4, 3, 4, and a disconnected forest
at most 2):
- the double star (an edge m whose two ends carry two leaves each): its four paths are (leaf, m, leaf);
  every edge lies on an even number of them, so the four label sums add to zero, not to 1111;
- the spider with legs of lengths 2, 2, 1 at a centre c: edges 1 = c-a, 2 = a-a', 3 = c-b, 4 = b-b',
  5 = c-d; the paths are {1,2,3}, {1,2,5}, {1,3,4}, {3,4,5}. Adding the four label sums gives
  l_1 + l_3 = 1111, so {l_1, l_3} = {u_m, E_m}; by the symmetry of the two long legs let l_1 = E_m,
  l_3 = u_m. Edge 1 was created after B_m, so B_m is the path {3,4,5}: u_m + l_4 + l_5 = E_m, hence
  {l_4, l_5} = {u_q, E_q}, and q != m (otherwise an edge of the path of B_m carries the label E_m). The
  edge labelled E_q (edge 4 or 5) was created after B_q, whose path avoids that edge and therefore
  contains edge 1; edge 1 needs B_m, whose path contains edges 4 and 5. A cycle in time.
Contradiction.

So K >= 20. QED

## 5. What is counted, where sharing reduces the count, and what compensates

In the mirror the two sheets appear as two groups of four variables, and a gate is counted in one of
three ways:
1. gates that bring a new first part: with the exports they are the first sheet's own cost, at
   least 10 (inequality (I));
2. gates that repeat a first part: at least one per entry, an entry being the place where a vector of
   the second group is added in;
3. gates with no first part: the second sheet's triple-sums and whatever even vectors are used as
   entry labels (fact (E)).
Without sharing, the second and third groups are the second sheet's own cost with the entry labels as
its exports: three even labels and seven gates, or four labels and six gates, 10 in all.

**Where sharing reduces the count.** An exit: a vector of the second group obtained in ONE gate as the
difference of two signals with the same first part. It is the sum of the labels along the path between
them, so along a path of three entries a triple-sum costs one gate instead of two, and the third group can
shrink from six or seven gates to four: every label is then a unit or a triple-sum, i.e. odd, and no
even vector of the second group is ever built. On the second sheet's side alone this is a saving of one
or two gates.

**Why additional work appears.** The gates of groups 1 and 2 together are themselves a circuit for the
first sheet with the second group free (Lemma A), and its mirror T* must show, as separate even signals,
which of the A_i each entry influences. With four independent labels, a trace vanishes only when
exactly one label is odd and two traces coincide only when exactly two are odd (Lemma B); with three or
four odd labels there are four distinct even traces, so T* has eight gates instead of six or seven and
groups 1 and 2 together have at least 12 gates instead of 10. That repays the saving except in one
exactly tight situation. There the mirror T* is so rigid that entries cannot be stacked on one another
or on a common signal; the only sums left for an exit are the four cross sums through a single
non-entry duplicate, and these add up to zero while the four triple-sums add up to 1111. With five
entries the fifth entry is itself the repayment, and the remaining configurations fail either by the
same parity (the double star) or by the order in time in which labels and exits would have to be
created (the path and the spider).

In primal terms (transposing back; a description, not a separately proved statement): the second sheet
may obtain a vector on the first sheet's block as the difference of two of its own signals instead of
asking the first sheet to compute it. When all the borrowed vectors are odd, the first sheet's own
computation has to contain four distinct even vectors, any three independent and summing to zero (for
unit labels these are the four adjacent pair-sums of its block; for other odd labels they are another
such set), which is the eight-gate form of its computation rather than the six- or seven-gate form.
What the proof shows is that the total never drops below 20; it does not isolate a threshold at which
an exit "starts to pay".

## 6. Limits

- The theorem concerns the pair with the first neighbour free and nothing else. It does not give ten
  gates per sheet for a chain of three or more adjacent sheets (proved only for level-monotone mirrors),
  nor anything for the ring: with three positions every pair of the 28-gate circuit costs 23 or 24, yet
  the whole costs 28 < 30. The saving there is not located in any pair.
- The final contradictions use the specific targets (the four triple-sums, whose sum is 1111, and the
  four adjacent pair-sums). The argument is not a general theorem about two parts with overlapping
  windows.
