# Chain of three: the open-end route (Lemma R, Theorem A, the residual gap)

Delegated investigation, 2026-11-12 (phase 3), separate model instance (Opus, high effort); saved by the
main agent from its final message. Machine work; review status in `../../RECORD.md` section 18. No SAT, no
enumeration; `q3_mirror.py` is a check on the recorded Q_3 circuit.

**Review (`../../review-compose/REVIEW.md`).** Skip-exit lemma, Lemma R, Corollary R, Theorem A and
Proposition H: correct as proved. Corrections: the (Y')/(Z') split used below comes from the unreviewed
chain/REPORT section 3; the reviewer re-derived every part that is used (and showed the fifth pure gate of
(Z') is forced even), but not (Y')'s "all four labels units", which is unused. "R, a 20-gate pair circuit"
means |R| + tau = 20. The Remark's P_2 <= 18 is unchecked. (G2) needs, besides what is written: a length-1
path along the delta edge (C_i = delta) is possible; if delta is even the tree list must be redone; the
double-star parity argument still applies; paths through delta come after h.

**Outcome.** M_3 is not decided. Proved: Lemma R (every length: a first sheet in its cheapest form can hand
nothing back across the open cut, so an exit across cut 1 costs the first sheet at least one extra gate)
and Theorem A (l = 3: a 29 must contain an exit of the adjacent kind X12; exits jumping from sheet 1
straight to sheet 3 cannot produce the saving). A 29 is reduced to two residual configurations.

## 1. Notation

Level of a nonzero mirror vector = least k with a nonzero part on w^k. Exit of type X_jm: x + y with x, y of
level j agreeing on w^j and the gate of level m > j. Exits across cut k are the X_jm with j <= k < m; in
MC_3 the types are X12, X13 (crosses both cuts), X23. T optimal, reduced. Counts: a (level 1, first at
cut 1), b (level 1, duplicate at cut 1, first at cut 2), c (level 1, duplicate at both cuts), d (level 2,
first at cut 2), e' (level 2, duplicate at cut 2), n (level 3). So f1 = a, D1 = b + c, f2 = a + b + d,
D2 = c + e', N2 = n. e1 = number of cut-1 entries (<= b + c); Lambda_1 = span of cut-1 labels, containing
Even(w^2) + 0 and the s-parts of all level-1 signals; L_j = the level-j gates.
Facts used (reviewed earlier): (F1) a + tau >= 10; (F2) f2 + tau >= 20; (F3) c + e' + n >= 9, so K = 29
forces f2 + tau = 20 and c + e' + n = 9, i.e. (Y') or (Z'); (F4) Proposition 1 of `../FRAMEWORK.md`: no
exit across cut 1 gives K >= 30.

**Skip-exit lemma [proved, any l].** An X1m gate (m >= 3) has an operand that is a level-1 gate and a
duplicate at cut m-1. *Proof.* Its operands are two distinct level-1 signals in one fibre at cut m-1; the
later one is not that fibre's first signal, and two inputs never share a fibre. For l = 3: an X13 gate
forces c >= 1.

## 2. Lemma R: the rigid open end [proved, every l >= 2]

**Lemma R.** If L1 has exactly ten gates, three of them duplicates at cut 1, then T has no exit across
cut 1.
*Proof.* (1) e1 >= 3 since Lambda_1 contains a 3-dimensional space, so the three duplicates are entries
whose labels are a basis of Even(w^2) + 0. (2) L1 is a local circuit for sheet 1 (pair Lemma A); by the
ten-gate lemma cleaning leaves at least 10 gates, so nothing is removed and t = 3; the mirror T*_1 has
7 gates and the traces zeta_1..3 are independent even vectors (Step 2). (3) For every summation order T*_1
has 7 gates carrying 7 prescribed distinct non-input values (four triple-sums, three zeta), so each gate
carries one of them. (4) For j != k, zeta_j + zeta_k is even, nonzero and not a zeta, so not a signal of
T*_1. (5) The two arguments of configuration (Y) in pair/PROOF go through verbatim: no signal is the
non-free operand of two entries, no entry the non-free operand of another. (6) Every cut-1 duplicate is an
entry, in the fibre of its non-free operand, so each fibre is its first signal r plus at most one entry
r + pi. (7) An exit across cut 1 adds two signals of one fibre; its value is the value of pi, a repeated
value. Contradiction.

**Corollary R [proved, every l].** If an optimal MC_l circuit has an exit across cut 1, then
(f1 + tau) + D1 >= 14, against the standard 10 + 3 = 13.
*Proof.* If D1 >= 4 use (F1). If D1 = 3, |L1| = f1 + 3 >= 10 with equality excluded by Lemma R, so
f1 >= 8 and the total is at least 8 + 3 + 3.

## 3. Theorem A [proved, l = 3]

**Theorem A.** Every MC_3 circuit with |T| + tau = 29 contains an X12 gate; equivalently, an MC_3 circuit
without X12 gates has K >= 30.
*Proof.* Assume K = 29 and no X12.
(i) L2 is a sheet-local circuit: a level-2 gate cannot have exactly one level-1 operand (it would be level
1), and two level-1 operands would make it an X12. So L2 (d + e' gates) is a local circuit for sheet 2
(own units w^2, every vector on w^3 free) containing the B_i; the ten-gate machinery and Lemma B apply:
clean entries t_M <= e', clean labels span a space containing Even(w^3), |T*_M| = K_(M,c) - t_M with
K_(M,c) <= d + e'.
(ii) d + e1 >= 10: by (i) a level-2 first gate at cut 2 has two level-2 operands with different w^2-parts
(a level-3 operand would leave it in the other operand's fibre); replacing operands by fibre roots gives a
circuit on w^2 of d gates containing E_i(w^2) and every w^2-part of a level-2 signal, among them the
w^2-parts of the cut-1 labels, which span a space containing Even(w^2): an MC_1 circuit with at most e1
exports.
(iii) Fact (E) for level 3: distinct nonzero even clean L2-labels are distinct level-3 gates, different
from the C_i.
Count: K_P := d + e' + n + e1; K = (a + tau) + (b + c - e1) + K_P >= 10 + K_P, so K_P <= 19 and
e' + n <= 9. Run Steps 1-3 of the pair proof with (f, D, N_0, tau) := (d, e', n, e1):
- all clean labels even: n >= 7, e' >= 3, e' + n >= 10, impossible;
- t_M = 4: labels a basis with o odd, n >= 8 - o, so K_P >= (|T*_M| + 4) + n + e1 >= 7 + 4 + 6 + 3 = 20
  (o <= 2), 8 + 4 + 5 + 3 = 20 (o = 3), 16 + e1 (o = 4); only o = 4 with e1 = 3 survives;
- t_M >= 5: forces e' = 5, n = 4, K_P = 19.
Survivors: e1 = 3: Lambda_1 = Even(w^2) + 0, every level-1 signal has zero w^3-part, an X13 would be
zero. t_M >= 5: 29 = K >= (a + tau) + K_P forces c + e' + n = 9 by (F3), so c = 0 and the skip-exit lemma
excludes X13. Either way there is no exit across cut 1 and (F4) gives K >= 30. Contradiction.
*Meaning.* For three sheets a saving needs the first sheet to give the NEXT sheet's level a vector by
cancellation; a skip exit needs a first-sheet duplicate at both cuts, and a tight closed end has no room.

## 4. The case where R has no exit [proved reduction]

R = the projection of T onto groups 1-2 (Lemma 1 at cut 2), a 20-gate pair circuit when K = 29.
**Proposition H.** If K = 29 and R has no exit (every X12 gate is a duplicate at cut 2), then (Y') holds
and the unique X12 gate is the non-entry duplicate h; a + tau = 10, c = 0, e' = 5; b = e1 >= 4,
d = 10 - e1; the four C_i are X23 exits in level-2 fibres.
*Proof.* (1) Proposition 1 for R: a + tau = b + d = 10. (2) In (Z') every cut-2 duplicate is an entry, so
by Theorem A we are in (Y') and the X12 is h. (3) With r the first signal of h's cut-2 fibre and
delta = h + r (a vector on w^3), replacing h by the entry r + delta makes L2 a sheet-local circuit L^2
with the same gates; its labels are odd (in (Y') the level-3 signals are units and C's) except delta, so
t_M >= 4. (4) t_M = 4: o >= 3, d + e' >= 12, 29 >= 10 + e1 + 12 + 4, so e1 = D1 = 3, then a = 7 and
Lemma R forbids h. (5) t_M = 5: c + e' = 5 gives e' = 5, c = 0; d + e1 >= 10 and b >= e1 give b = e1;
e1 = 3 is excluded by Lemma R as in (4); with c = 0 there is no X13.

## 5. The exact remaining gap for l = 3

A 29 exists only in one of:
- (G1) R (a 20-gate pair circuit) has an exit across its cut; Corollary R applied to R gives
  a + tau + b >= 14, hence d <= 6;
- (G2) the setting of Proposition H: the far pair L^2 with L3 is exactly configuration (X) of the pair
  proof (five entries, N_0 = 4, every C_i an exit along a forest path) except that the edge r-h carries a
  label delta that is not a value of T, so the label and time-order steps of (X) do not apply to it.

**Why the open-end route stops here.** An X12 value is an extra base vector for sheet 2, and both far-side
bounds used in Theorem A then fail by about one gate (example: with 1111 on w^2 supplied by one exit,
E_i(w^2) = 1111 + u_i takes 4 gates, and with unit exports d + e1 = 9 instead of 10; in L2's mirror the
unit adjoints become units and the ten-gate count no longer applies). The first sheet's charge depends on
the parity type of its labels (1 by Corollary R; 2 by Lemma B with unit labels), the far-side gain on the
exit's value; nothing in M_1, M_2 and Lemma B relates the two. "Exits from one sheet save at most Lemma
B's charge" would need a statement about the second sheet with an extra base vector at its open end:
a two-sided statement.

**Remark [proved, elementary].** Killing w^1 maps T to a circuit for sheets 2-3 containing all four
p_i(w^2), so at least P_2 gates have a new nonzero (w^2, w^3)-part, 17 <= P_2 <= 18 (P_2 the least size of
such a circuit). This bound is immune to exits but credits the far side with parts carried by sheet-1
signals; its slack lands on the same 4E-pair object (L18) that the closed-end route reaches. Both
peelings meet at that object.

## 6. Length l

General (proved): the skip-exit lemma, Lemma R, Corollary R. Without X12, L2 is a sheet-local circuit, and
the gates of level >= 2 form an MC_(l-1) circuit (exports = cut-1 labels) apart from X1m intrusions
(m >= 3), each needing a first-sheet duplicate at cut m-1. Specific to l = 3: Theorem A uses that the far
part is a pair (Steps 1-3 of the pair proof isolate the configurations where intrusions matter) and
tightness at the closed cut (c = 0). For l >= 4 both would need M_(l-1) = 10(l-1) in a form locating the
configurations open to skip intrusions, plus tightness at cut m-1; neither exists. Conjectural: "a chain
saving needs adjacent exits at the open end".

## 7. The ring Q_3

Lemma R needs the export boundary (three exports force three even labels and the rigid 7-gate mirror). The
mirror of Q_m has no exports, and each group's projection must contain eight prescribed vectors (the E_i
and p_i), so the "ten gates, three entries" form does not exist. Theorem A also needs a closed end and a
pair-shaped far part; in Q_3 the complement of one group is an arc whose last required vectors involve the
removed group. *Check* (`q3_mirror.py`): the mirror of the recorded 28-gate circuit has 28 gates and the
expected unit adjoints; cutting off each single group gives 1, 1 and 2 exits, all nonzero on the next
group in cyclic order, i.e. of the adjacent X12 kind. So the ring saves with exactly the exits Theorem A
does not exclude, and has no end to stop them.
