# One sheet supplying values to a receiver: SB' is false; SB* and Omega2

Delegated investigation, phase 4 (2026-11-12), separate model instance (Opus, high effort); saved by the
main agent from its final message, lightly condensed. Review status in RECORD 19. No SAT; every
circuit below was written by hand and checked as a single fixed object, the checkers computing
L_near by a small exact (Dijkstra) search on that object (see `../../joint/FINITE_AUDIT.md`; the values
used have one-line hand bounds there) (`mcheck.py 3` from ../sb,
`sbcheck.py`, `ncheck.py`). Files: ncheck.py, sbcheck.py, sbx5.txt, sbx5_formal.txt, sbx5_mc3.txt,
t_o2_formal.txt.

**Review (`../../review-sb2/REVIEW.md`).** No proved statement is wrong; the counterexample was verified with
an independent evaluator. Repairs: Lemma Q' needs a different proof (greedy basis in time order, then
Lemma Q); the Path Lemma's distinctness claim has a gap in general but its use in (3,8,0) survives ("a
length-3 path contains labels 1 and 2"); in section 4, equal traces are necessary but not sufficient for a
free stack, and "each non-free adjacency consumes a spare" holds only in settings like (3,8,0); in section 5,
Omega1's beta = 2 can also come from three weight-3 exits, and chi = 6 needs that no other exit adds an even
value; the shallow e1 >= 5 residual is only e1 = 5 with near1 = 10, h1 = 0, sigma = 1, beta = 2.

| Item | Status |
|---|---|
| SB' as a one-sheet inequality | false (verified counterexample; needs l >= 3, e1 = 5) |
| Lemma 2.1* (receiver may export its own replacement values) | proved, every l |
| SB* (repaired target) => M_l = 10 l | proved, same induction |
| SB* for e1 = 4, o = 2 (all of Omega2) | proved |
| SB' in the Omega2 sub-case (tau, f1, h1) = (3, 8, 0) | proved (Path Lemma) |
| Lemma H: a(h) is odd in form (4,6,1) | proved |
| Lemma Q': beta <= 2 whenever dim V <= 4 (with timing) | proved |
| Omega1 (o in {3,4}, e1 = 4, near1 = 11) | open: the one e1 = 4 case left |
| e1 >= 5 with an odd label | open in general |
| "formal part determined by its w^1-part up to the stacked odd pair" | false as stated; harmless |

## 1. Lemma 2.1* (proved, every l)

Take any replacement R of the exits (gates computing each exit value, in time order, from earlier labels
and earlier R-values). tau_R := least number of elements of Lambda together with val(R) spanning
Even(w^2) + 0; chi := min over R of (|R| - |S| + tau_R). Then **far1 >= M_(l-1) + e1 - chi.**
*Proof.* P' = P with the exits replaced has |P| - |S| + |R| ordinary far gates and contains R^2..R^l, every
label signal and every R-value; exporting tau_R of these values makes P' an MC_(l-1) circuit, so
|P'| + tau_R >= M_(l-1). Add e1. QED
Since tau_R <= tau_min, chi <= beta + tau_min, so chi - e1 <= beta - sigma: Lemma 2.1' is the special case.
**SB\*: near1 - 10 >= chi - e1** (weaker than SB'). It implies cost >= 10 + M_(l-1), and M_l = 10 l by the
induction of TWOSIDED section 5.
*What this answers:* paying honestly for a supplied value also builds intermediate sums, and those sums
can be the receiver's cheap exports; the receiver's gain and its export economy are coupled, and the span
of the labels alone is the wrong measure.

## 2. SB' is false (verified)

`sbx5.txt` (near side) and `sbx5_mc3.txt` (a full reduced MC_3 circuit with a deliberately plain far side).
Near side: first gates P1 = w0+w2, P2 = w1+w2, P3 = w0+w3 (the three exports, tau = 3), A3 = P1+n2,
A0 = P2+gC, Q = A3+gC, A1 = Q+n4, A2 = P3+n4. Entries: a chain n1 = w1+lambda1, n2 = n1+lambda2,
n3 = n2+lambda3, n4 = n3+lambda4, plus gC = w3+lambda5. Labels (w^2 part | w^3 part): lambda1 = (u2|a),
lambda2 = (u3|a), lambda3 = (u1|b), lambda4 = (u3|b), lambda5 = (u0+u3|0), a, b units of w^3; independent.
Exit: w1 + n4 = lambda1+lambda2+lambda3+lambda4 = (u1+u2 | 0). Checked: reduced, all required vectors,
exports valid; f1 = 8, h1 = 0, near1 = 11, e1 = 5, tau_min = 5, sigma = 0, L_near = 3, beta = 2. SB' false.
**Mechanism.** zeta_1 = zeta_2 and zeta_3 = zeta_4: each pair is a *free stack*, two deep labels whose sum
(lambda1+lambda2 = u2+u3, lambda3+lambda4 = u1+u3) is shallow, behaving like one even label at no cost in
T*. One spare T* gate (near1 = 11) links the two pairs into one path of four labels.
**SB\* holds here:** R = {lambda1+lambda2, lambda3+lambda4, exit}; then lambda1+lambda2, lambda3+lambda4,
lambda5 are three exports, chi <= 2 + 3 = e1, and by Lemma 2.1* the far side gains nothing (far1 >= 20).

## 3. Omega

The literal conjecture is false: in the tight o = 2 mirror (`../sb/tight_o2.txt`, formal version
`t_o2_formal.txt`), signals i2 and i3 have equal w^1-part but formal parts differing by z4, a single label
value, which reducedness forbids as an exit, so harmless. Salvageable form: every same-fibre difference is
a single label or lambda1 + lambda2 (not needed once SB* is used).
**Theorem O2 (proved, every l).** SB* holds for every instance with e1 = 4 and o = 2; this closes Omega2.
*Proof.* V = span(Lambda) has dimension 4; E := Even(w^2) + 0 is a hyperplane of V containing lambda3,
lambda4 but not lambda1, lambda2, so lambda1 + lambda2 lies in E. By Lemma Q', beta <= 2. If some exit has
formal c with c1 = c2 = 1, its value lies in E outside span(lambda3, lambda4), so it, lambda3 and lambda4
span E: tau_R <= 3 and chi <= beta + 3 <= 5. Otherwise every exit contains at most one of lambda1,
lambda2, so every exit of weight >= 3 contains lambda3 + lambda4; one auxiliary at the first such exit makes
all later ones cost 1: beta <= 1, chi <= 1 + 4 = 5. Either way chi - e1 <= 1; near1 >= 11 gives SB*; if
near1 = 10, S2 gives beta = 0. QED
**Path Lemma (proved, every l; gives SB' in sub-case (3,8,0)).** Assume h1 = 0 and the clean labels
independent. A tree adjacency on an exit path (labels j, k meeting at a vertex v, as siblings or as a stack)
is free only if zeta_j = zeta_k and it is a stack whose lower entry has no other level-1 reader. Every other
adjacency forces, in some summation order, a T* gate of value zeta_j + zeta_k (even, for independent
labels). Two non-free adjacencies at distinct vertices of one path force two distinct such gates in one
order (coinciding gates would need a common level-1 reader of two signals in one fibre, which would be an
exit). In (3,8,0), |T*| = 8 against 7 required values and the only free pair is {1,2}; so every exit path
has length <= 3, and a length-3 path contains lambda1 + lambda2: beta <= 1 = near1 - 10.
**Lemma H (proved).** In (4,6,1) replace h by the entry r_F + Phi(delta); the ten-gate machinery forces the
new mirror T*' to have exactly 6 gates (room for two even signals); the new traces are
zeta'_j = zeta_j + delta_j a(h) and zeta'_5 = a(h); if a(h) were even they would include three distinct
even values; so a(h) is odd. Principle: h is an entry whose label Phi(delta) is computed on the near side;
exits through h are tree paths through that edge; such a label is dependent, so adjacency sums can be odd
and coincide with required E-values, which makes them free (why the Path Lemma fails when h1 = 1).
**Omega1 (open).** o in {3,4}, f1 = 7, h1 = 1, tau = 3, |T*| = 8 tight. A weight-4 exit gives chi = 6 (its
auxiliary pairs yield only one (o = 3) or two (o = 4) independent even vectors). Closing it needs beta <= 1
from rigidity; Lemma H only gives |T*'| = 7 here.

## 4. Span type versus supplier charge

- **Lemma Q' (proved, timing included).** If dim V <= 4 then beta <= 2; if V = E, beta <= 1. (While the
  available labels span <= 3 dimensions at most one auxiliary is needed (S1); when a fourth independent
  label arrives the vectors still costing 2 are x + b4 with x in {b1+b3, b2+b3}, and one auxiliary b3+b4
  covers both; starting in dimension 4, Lemma Q's two complementary pairs cover everything.) For shallow
  labels (dim V <= 4) with e1 >= 5 and an odd label, sigma >= 1; for e1 >= 6, sigma >= 2 >= beta and SB'
  holds; for e1 = 5, SB' fails only if near1 = 10, h1 = 0, sigma = 1, beta = 2, with at least two stacked
  entries.
- **Span type determines sigma and the free adjacencies (proved, independent labels).** zeta_j = 0 exactly
  when lambda_j lies outside supp(E) (such an entry is unclean or costs a zero gate); tau_min = |supp E|,
  so sigma = e1 - |supp E|. The clean traces satisfy t - 3 independent relations (Lemma B when t = 4);
  relations of support 2 (equal traces) are the free stacks; relations of support 3 make the sum another
  required trace.
- **Supplier charge (h1 = 0):** near1 - 10 >= (spare T* gates) + (zeta - 3) + (tau - 3), zeta = number of
  distinct nonzero traces; each non-free adjacency on an exit path consumes a spare.
- **Deep labels.** When dim V >= 5 (possible only for l >= 3), beta is not bounded by the span: one exit can
  save up to dim V - 2. Section 2 is the resulting failure of SB'.

## 5. M_3 = 30 does not close

Proved dependencies: ten-gate lemma, pair theorem, Lemma R, Theorem A, Proposition H, Theorem 4.1, Lemma
2.1*, S1, S2, Theorem O2. A 29 is reduced to: (1) Omega1 with beta = 2 and chi = 6 (a far side would need
far1 = M_2 - 2 = 18: an MC_2 circuit with the four labels as exports in which the supplied weight-4 value
would cost 3 gates honestly); (2) e1 >= 5 with an odd label, under SB* (for deep labels still
unconstrained; for sbx5-type deep stacks Lemma 2.1* gives far1 >= 20). No circuit realising either was
found.
**Uniformity in l:** Lemma 2.1*, SB* => M_l = 10 l, Theorem O2, the Path Lemma, Lemma H and the span/sigma
statements are one-sheet statements with U abstract, valid for every l; Lemma Q' needs dim V <= 4
(automatic for e1 = 4). **Ring (28 < 30):** nothing applies (Lemma 2.1* needs the replaced far side to be an
MC_(l-1) circuit with an open export end; (F1) needs the export obligation; Q_3 has adjacent-kind exits at
every cut).

## 6. Doubts about sb/REPORT

"SB' for one sheet => M_l = 10 l" cannot work in general (sbx5 is a reduced instance where SB' fails);
Theorems S2 and 4.1 stand, and SB' implies SB* there. The tight-mirror conjecture is false as worded.
Agrees with the review corrections (1)-(5). A bug in the investigator's own checker was fixed (an exit's
available labels must include the entry that is its later operand: comparison <=, not <).
