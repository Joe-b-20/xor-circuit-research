# Second check of joint01 Theorem A (L >= 11) and of the abbreviated RECORD 17.2

Independent machine check, 2026-11-12 (phase 3), prompted by the user's example of an auxiliary gate
serving two required vectors. Separate model instance (Opus); saved by the main agent from its final
message. Not a human review. `chk_b.py` checks finite parity facts over all 28 even bases; it is a check,
and the hand arguments below are given alongside.

**Verdict.** Theorem A is correct; the example does not break it. The full proof (joint01/REPORT.md
section 4, F3: "besides an entry in its own fibre, an aux serves at most one required gate with a named
partner") already counts the example. The abbreviated wording in RECORD 17.2 drops the qualifiers the proof
depends on and is false as written. Theorem 17.3, J_01 >= 21 under its hypothesis, and the block-monotone
MixColumns bound 84 stand.

**Coordinates.** REPORT convention: first part over the own units w, second over the free coordinates;
A_i = (E_i | p_i), p_i = u_(i-1) + u_i. The user's A_0 = (0111 | 1100) uses the reflected (primal)
indexing; under c -> -c the matching aux is h = (E_0 | 1111): h + w_0 = X(1111) and
h + (0 | p_0 + 1111) = A_0. w_0 is an own unit, a named partner.

**How the proof handles it.** A_0 = h + (0 | s) is in h's fibre, so it is a required entry and h is the
aux first gate of that fibre (one of the "p aux first gates"); X(1111) = h + w_0 is h's single
named-partner service. A free-partner service always lands in the aux's own fibre; each fibre holds one
target; required entries are counted by p; only required first gates are charged against named services
and aux + aux sums. Check: for every basis and every aux value, at most one named representation and at
most one required vector in the aux's own fibre.

**Steps.**
- Seven first gates plus three entries: correct (S minimal: no gate with first part 0, no equal values,
  every gate an ancestor; at least 3 entries, at least 7 first gates in distinct non-unit fibres; so
  exactly, labels a basis of the even space, each read once).
- Every required gate reads an aux: correct (a required first gate cannot read a free vector; by N it is
  not the sum of two named vectors).
- N, F2, F3 by hand (the REPORT cites only the 28-basis check):
  N: first-part weights (3 for A, even for X) and second parts; E_i + p_i = 1111 + u_(i-1) has weight 3;
  p_i + p_j is never u_i + u_j; p_i + p_(i+2) = 1111; the v_m are independent.
  F2: a relation sum_I A_i + sum_M X_m = 0 gives u_I + u_(I-1) = 0 on the parts, so I and then M are
  empty; differences of two required vectors with second part 0 occur only as A_i + X(p_i) =
  (1111 + u_(i-1) | 0), weight 3, never a unit or even.
  F3: two representations give a relation among required vectors, or R + R' = (pair | 0) (excluded by F2),
  or three required vectors summing to (unit | 0), which fails (A_i + A_j + A_k = (u_l | p_l); other
  triples have the wrong parity or weight). A pure pair has no representation (every required vector has
  a nonzero second part). Unstated step: a representation beta = R + R' supplies only one service, since
  R and R' cannot both be built from each other.
- Count over p: correct (p aux first gates, 3 - p aux entries, 7 - p required first gates, at most 3 + 2).
- p = 2: correct; the parenthetical omits why beta cannot be w + free, gamma + free or X(pi) + free (the
  only aux entry, 3 - p = 1, is gamma itself).
- p = 3: correct; gate lists complete; aux entries cannot occur (3 - p = 0).

**Gaps (wording only).** (1) minimality as the reason for "no first part 0, no equal values"; (2) the
aux-entry exclusion in p = 2; (3) one service per representation; (4) the hand proofs of N, F2, F3.

**Corrected short statement for RECORD 17.2.** "Neither a target nor a diagonal vector is the sum of two
inputs or required vectors, so each required vector reads an auxiliary gate. Besides carrying the one
required vector that may lie in its own fibre (an entry: aux plus free vector), an auxiliary gate can
serve at most one required vector whose other operand is an own unit or another required vector, and a
pure pair-sum can serve none of this kind. Ten gates leave three auxiliary gates; when at most one
required vector is an entry they cannot serve the other six or more, and the cases with two or three
entries fail on the order in which the gates can be built." For p = 2 and p = 3 the count alone allows
exactly enough services; those cases close only by the order arguments.
