# Compatibility of the two sides at a MixColumns cut

Delegated investigation, phase 6 (2026-11-12), separate model instance (Opus, high effort); saved by the main
agent from its final message, lightly condensed. Review status in RECORD 21. proved = hand argument
(investigator's); check = program output on existing circuits or explicit constructions. No SAT, no
enumeration. Scripts: clib.py, cutstats.py, waste.py, join.py, corpus.py, anatomy.py, rw.py, lowwaste.py.
Nothing changes 75 <= L <= 88.

**Review (`../../review-compat/REVIEW.md`).** Props 1-4, K_7 >= 60 (given Theorem 16.1) and the restriction cap
are correct. Prop 1 bounds exit-free circuits only (L_ef,b is an upper bound on L). The exit counterexample below
is not reduced; a reduced one: x = u + l1, y = x + l2, exit s = y + u = l1 + l2, the far side building l2 only as
s + l1. Prop 2's phi half is backed by a check (an automorphism fixing W_7 gives phi(Lambda') >= 32 > 30);
"Lambda itself is the smallest description" is informal. Prop 4: read "every unit-reading gate". "Does not beat
O's 72" compares a lower bound with a cap of another template. The low-waste circuits verify (waste 5 or 6).

## 1. Formulation

T a reduced MixColumns circuit, b a primal block; v = (omega | s), omega the block-b part, s the far part;
L_b = gates with omega != 0, P = gates with omega = 0; exit = P-gate with a level operand; entry = L_b gate
with exactly one far operand; Lambda = set of DISTINCT far operand values (labels); S_near = {s(r)} for the
rows nonzero on b; R_far = the far rows; W_b = span S_near.
**Prop 1 (exact join for cuts with no exit; proved).** With no exit at b, the far inputs and P are closed under
taking operands, so P is a standalone far circuit containing R_far and Lambda, and L_b is a circuit on
U_b together with Lambda (U_b = block-b units) computing the near rows, every gate nonzero on b, each label use
counted. Conversely any far circuit F whose signals include Lambda, followed by any such near circuit N, is a
valid circuit of size |N| + |F|. Hence

    L_ef,b(MC) = min over Lambda of [nu_b(Lambda) + phi_b(Lambda)],   phi_b(Lambda) = L(R_far together with Lambda),

L_ef,b = least size of a circuit with no exit at b. "Lambda among the signals of F" is necessary and
sufficient; no ordering issue arises.
**With exits (proved).** The interface becomes (Lambda, S, precedence); joining is possible exactly when the
combined precedence (label before entry, entry before exit, exit before the far gates and labels depending on
it) is acyclic. Set data alone is not enough: near side x = u + lambda, exit x + u = lambda, where the far side
obtains lambda only from that exit: the set conditions hold, no circuit exists.
**Prop 2 (what nu sees; proved).** nu_b(Lambda) depends only on the linear relations between Lambda and S_near:
a linear isomorphism of span(Lambda, S_near) fixing S_near pointwise and mapping Lambda to Lambda' gives
nu(Lambda) = nu(Lambda') (apply id + A to every near signal; every near far part lies in span Lambda). phi needs
the actual vectors (sketch: Lambda = all far units and Lambda' = A(units) with A fixing W_b have the same type,
but phi(units) = L(R_far) while phi(Lambda') >= the number of non-unit values in Lambda' and R_far). So the
full label set Lambda (22 to 27 vectors at block 7) is a sufficient exact description; its necessity has not
been established (phase-7 correction).

## 2. Bounds on nu and phi; the coupling

**Prop 3 (one-block bounds on nu; proved).** nu_b(Lambda) >= 8 + max(dim W_b, |Lambda|) (f >= 8: eight
distinct non-unit required omegas; e >= dim W_b: the span of U_b and the L_b values grows only at entries,
by at most 1 each, and must reach dimension 4 + dim W_b; e >= |Lambda|). Block 7: nu >= 27; block 2: nu >= 15.
Upper bounds 28 and 16 with Lambda = S_near (8 first gates on the units, then one entry per row).
**Prop 4 (the coupling is the restriction; proved).** pi_far sets block b to zero. A gate is *wasted* if its
pi_far value is 0, a far unit, or equal to another gate's pi_far value; w_b(T) = |T| minus the number of
distinct new pi_far values (order-independent). Identity |T| = R_b(T) + w_b(T); the non-wasted gates, rewired,
compute MC with block b zeroed, so R_b(T) >= K_b := L(MC with block b zeroed). w_b >= 4: every L_b gate reading
a block-b unit is wasted (its pi_far value copies its other operand's); the omegas of L_b lie in the span of
these unit-readers' omegas, and E_0..E_3 span F_2^4, so there are at least 4. Split form: with Delta(Lambda)
the straight-line cost of S_near from Lambda as free inputs, nu(Lambda) >= 4 + Delta(Lambda) and
phi(Lambda) >= K_b - Delta(Lambda) (a far circuit for R_far and Lambda followed by Delta gates computes the
restricted map). Consequences: phi(Lambda) - phi(empty) >= K_b - L(R_far) - Delta(Lambda);
min over Lambda of [nu + phi] >= K_b + 4; |T| >= K_b + 4 for every circuit, with or without exits.
**The tradeoff, and why it closes nothing.** Delta is the whole tradeoff (the part of the restricted
computation done on the near side); cheap labels raise Delta, and Delta cancels in the sum. With Lambda fixed,
the interface adds nothing beyond K_b plus near-side waste: ordinary gate elimination on block b.
**Beats the separate canonical bound at block 7 (proved, given Theorem 16.1).** K_7 >= 60 (M_6 >= 56 for sheets
1..6 with block 0 free, RECORD 16, plus the four outputs E_c(0), on block 0 alone, not among the counted gates),
so min over Lambda of (nu + phi) >= 64, while nu_min <= 28 and phi_min = L(R_far) <= 30 (one ten-gate sheet,
2, and the pair 5, 6): nu_min + phi_min <= 58 < 64 (margin >= 6). Does NOT beat Obstruction O's 72 at block 7;
64 < 75.
**Obstruction for the restriction form (check).** Any bound K_b + (waste lower bound valid for all circuits)
is at most K_b + w_min. min R observed (upper bound on K_b): 77 at blocks 0-6 (88s), 69 at block 7 (recorded
89) (rw.py, every 5th kste circuit plus the three recorded). w_min <= 6 at every block: explicit 158-166-gate
circuits, verified to compute MixColumns and reduced, with waste 5 or 6 (lowwaste.py). So this form proves at
most 83 at blocks 0-6 and 75 at block 7; it cannot reach 88 at a single cut. Going further needs a coupling
between R_b(T) and w_b(T) (low waste forcing a large restricted part); none proved. Observed at block 4: min R
(77) and min w (11) occur in the same circuit (circuits_1 line 1): no tradeoff visible in the sample.

## 3. Computations

Block 7 (check; cutstats.py, waste.py, anatomy.py; all five have 0 exits at block 7):

| circuit | f | h | e | L_7 | P | distinct labels (rank) | units / row-parts / other | label-only P gates | waste (f, e, h) | R |
|---|---|---|---|---|---|---|---|---|---|---|
| 88 | 10 | 8 | 28 | 46 | 42 | 24 (22) | 8 / 2 / 14 | 5 | 17 (6, 11, 0) | 71 |
| 89 | 10 | 6 | 30 | 46 | 43 | 26 (22) | 7 / 3 / 16 | 7 | 20 (7, 13, 0) | 69 |
| 97 | 8 | 0 | 32 | 40 | 57 | 27 (23) | 5 / 3 / 19 | 21 | 23 (6, 17, 0) | 74 |
| c3:13114 | 10 | 14 | 23 | 47 | 41 | 22 (22) | 8 / 2 / 12 | 3 | 17 (8, 8, 1) | 71 |
| c3:15380 | 10 | 10 | 29 | 49 | 39 | 25 (23) | 12 / 1 / 12 | 3 | 16 (7, 7, 2) | 72 |

dim W_7 = 19, span Lambda contains W_7, |S_near| = 20. Corpus every 10th (1,893 circuits, all 88): |L_7| 42-50,
|P| 38-46, e 23-32, distinct labels 22-27, near1 = f + h 15-24 (1,338 at 20), far1 = |P| + e 64-73, waste 14-18;
the (|L_7|, |P|) pairs lie on |L_7| + |P| = 88 from (42, 46) to (50, 38); exits at block 7: none in 1,774,
one in 108, two in 11. No label is a far row; most labels are far units or P-gates that are ancestors of far
rows (5-12 per circuit); the extra ones are label-only P-gates (97: 21; the 88s: 3-7).
Block 2:

| circuit | L_2 | P | f | h | e | distinct labels | waste | R |
|---|---|---|---|---|---|---|---|---|
| 88 | 19 | 69 | 9 | 0 | 10 | 10 | 11 | 77 |
| 89 | 17 | 72 | 9 | 0 | 8 | 8 | 11 | 78 |
| 97 | 21 | 76 | 8 | 1 | 12 | 11 | 13 | 84 |
| c3:13114 | 18 | 70 | 10 | 0 | 8 | 8 | 10 | 78 |
| c3:15380 | 21 | 67 | 9 | 0 | 12 | 12 | 10 | 78 |

dim W_2 = 7; only 15380 has an exit at block 2 (one); the near side is nearly rigid (h = 0 in four of five), so
no near/far tradeoff there; the {1,2,7} exit affects the restricted map, which Prop 4 covers without an exit
hypothesis.
**Why the near-8 and far-64 arrangements do not combine (check, join.py).** Different entry counts: the 97
reaches near1 = 8 with e = 32, the 13114 reaches far1 = 64 with e = 23; adding the baselines counts 23 entries
where the 97's near side needs 32. Missing labels: of the 97's 27 labels, 19 are not signals of the 13114's 41
far gates: lower bound for the joined circuit 8 + 32 + 41 + 19 = 100, greedy completion 105 (verified);
reverse join 47 + 57 + 9 = 113; every ordered pair of the five circuits joins to at least 96. Fibre shapes:
the 97's s_c fibres are paths of 8 entries with no h-gates (9 signals carrying 4 rows), its 19 "other" labels
include two-block vectors on {2,3}, {0,1}, {3,4} built only as labels; the 13114's s_c fibres use 2-4 h-gates
each plus 12 signals in helper fibres (non-required omegas such as unit omegas carrying far parts) whose
pairwise sums build the rows; its labels are mostly units and single-block vectors. Restriction accounting
(waste + restricted work on the near side + on the far side): 97: 23 + 17 + 57 = 97; 13114: 17 + 30 + 41 = 88;
the far side's 16-gate saving is paid by 13 more gates of near-side restricted work (Delta 17 -> 30), offset by
6 less waste. Delta is exactly what separate minimisation drops.

## 4. Status

Proved: Prop 1 and the exit/acyclicity condition with its counterexample; Prop 2; Prop 3; the identity
|T| = R_b + w_b with R_b >= K_b, w_b >= 4, and its split forms; given Theorem 16.1, K_7 >= 60 and the coupled
bound >= 64 beating the separate canonical bound (<= 58). Check: the tables; every join >= 96; K_b <= 77
(blocks 0-6), K_7 <= 69; w_min <= 6 at every block; hence the restriction form caps at 83 (75 at block 7).
Open: exact nu_min (27 or 28); whether low waste forces a large restricted part (the missing coupling any
single-cut argument would need beyond K_b + 4).
