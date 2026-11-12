# Trying to refute SB*: no counterexample; single-exit SB* and Omega1 proved

Delegated adversarial investigation, phase 5 (2026-11-12), separate model instance (Opus, high effort);
saved by the main agent from its final message, lightly condensed. Review status in RECORD 20. No SAT, no
search. Files: `near.py` (one-sheet evaluator: f1, h1, e1, tau, near1, targets, exports, near-side
reducedness, formal parts, traces, every same-fibre pair), `omega1_t.txt`.

**Review (`../../review-p/REVIEW.md`).** P2, P3 correct (P3 confirmed sharp by a finite check); P1, P4 correct
UNDER THE INDEPENDENCE ASSUMPTION, which restricts the class (it excludes dangle2, the 6+4 ten-gate form,
and most of l = 2); P1 needs a per-component count; P2's "exactly when q >= 4" only for J = all labels; P5
correct for e1 = 4 (dependent labels with e1 = 4 span E and are covered by S1). The consequence below must
read: a 29 needs e1 >= 5, near1 >= 11 and two exits, OR has dependent clean labels. Finite check: with
dependent labels and four unit types, q = 4 fits at near1 = 11, where P2 allows chi up to e1 + 2: the natural
place to look for a counterexample to SB*.

**Outcome.** SB* not refuted; none of the outcomes (1)-(4) of the brief is established. Proved by hand
(investigator; review in RECORD 20): P1 (near1 = 10), P4 (every instance with exactly one exit), P5 (Omega1,
hence every e1 = 4 instance). Throughout, the clean labels are assumed INDEPENDENT.

## Constructions (checked)
`omega1_t.txt`: a hand-built Omega1-shaped supplier (transposing an 8-gate mirror): f1 = 7, h1 = 1, tau = 3,
near1 = 11, e1 = 4; labels u0, u0+u3, u0+u1+u2, u1 (o = 3, rank 4); gates a = w0+w2, b = w2+w3, c = w0+w1
(exports), e12 = w3+L12, e03 = w1+L03, e23 = e12+L23, K = a+e12, T1 = K+L13, T0 = b+e03, T2 = c+e23,
h = T1+e23, T3 = h+e03; zetas 0110, 1001, 0011, 0101; every same-fibre pair has formal weight <= 2; the exit
a + h gives u0+u2. Shows Omega1 is non-empty but its exits are weak (a check).

## Notation
Clean labels independent; the type of label j is zeta_j, read as a linear form on E; E-elements are the label
sets {j : <c, zeta_j> = 1}; for an exit with formal support J, q = number of distinct nonzero types in J.

## Results (proved by the investigator)
**P1. near1 = 10 (every l, any number of exits): chi <= e1 - 1, so SB* holds with one to spare.**
Independence makes every zeta even; |T*| = clean first gates <= 7 and T* needs the 4 triple sums plus 3 even
zetas spanning, so near1 = 10 forces tau = 3, f1 = 7, h1 = 0, a tight 7-gate T*, zetas in an even basis
{A, B, C}. Tightness gives: no adjoint zero; two clean entries cannot read the same signal; a clean entry may
stack on another only if the zetas are equal and the lower entry has no other reader (free stack); so each
fibre holds at most one clean chain, all of one zeta, hanging from its root, and the targets see only the
chain's total sigma_k, so E lies in span(sigma_k). Replacement: in each fibre with exits, prefix sums from the
top of the union U_k of its exit paths: |R_k| - |S_k| <= e_k - 2; U_k meets the clean chain in one contiguous
segment, whose sum is an R-value. Exports: the clean labels outside every U_k plus one segment sum per fibre;
these span every sigma_k, hence E. Total chi <= e1 - d_out - 2K + K_c <= e1 - 1. This also rules out the most
natural attack (all entries on one exit path, which would give chi = e1 + 1).
**P2. A type bound for one exit.** chi <= e1 + q - 2 (a tree first summing each type-atom of J; export the
atom sums and the clean labels outside J). Laminar lemma: a read-once computation contains three independent
E-elements only if the types form a basis (refine a laminar triple into three pairwise disjoint E-elements;
then every type is a dual-basis vector). Hence if J is all the labels and q >= 4, every R with |R| = e1 - 1 is
a tree with tau_R >= 4, and chi >= e1 + 2: a single exit violates SB* at near1 = 11 exactly when q >= 4.
**P3. Mirror lemma.** No circuit on inputs W0..W3 and X contains the four E_c(W), k distinct vectors Z_j + X
(Z_j even, nonzero, distinct; k >= 4, or k = 3 with the Z_j spanning) and at most two other gates. Case split
on the two extra gates: both without X: every Z_j lies in span{H1, H2} (3 nonzero vectors) or spans only 2
dimensions; both with X: the first is forced to be X + W_a and the reachable E's close up short of four; one
of each: only {W+H, E+H, V, V+H} can produce E's, and with H a pair, the all-sum, a target part or a sum of
target parts, two of the E's can only be made from each other.
**P4. Consequence (every l, any number of exits): every exit satisfies q <= f1 + h1 - 5, and SB* holds for
every instance with exactly one exit, at every near1.** Clean with respect to the targets and one exit; by
the mirror identity (`../sb/REPORT.md` section 5) its mirror T** has at most f1 + h1 + 2 gates and contains
E_c and Z_j + c_j X; q <= (distinct zetas) <= |T*| - 4 <= f1 + h1 - 4, and P3 rules out equality. With P2:
chi - e1 <= q - 2 <= near1 - tau - 7 <= near1 - 10.
**P5. Omega1 is closed; SB* holds for every e1 = 4 instance** (with S1, S2, O2, Lemma Q and the review-sb
repair for (3,8,0)). A weight-4 exit is impossible by P4 (cleaning with respect to that one exit suffices).
o = 4: the (Y) rigidity leaves exits only among the four cross sums delta + {0, j, k, jk}; any three include
two differing in one label, so three weight-3 exits are impossible and beta <= 1. o = 3: lambda_4 lies in E;
every set of three or four weight-3 exits has an R with |R| - |S| = 2 and tau_R = 3 (the four triples checked
by hand), so chi <= 5 = e1 + 1. Consequence: a 29 for l = 3 needs e1 >= 5, near1 >= 11 (P1) and at least two
exits (P4).

## Mechanisms tried, and why each fails
1. Entries booked elsewhere (dangling stacks): each extra label raises the surplus by at most 1 and costs 1 in
   e1: net -2 per stack.
2. Free stacks of deep labels with equal traces: they add entries but no new types; the receiver rebuilds
   each stack total (an old even-type label) as an export; chi - e1 <= 0 (the sbx5 mechanism, not amplifiable).
3. One long exit path through all entries: blocked at near1 = 10 by P1's rigidity; at near1 = 11 with h1 = 0
   adjacent clean labels on a path must have zetas related in T* (equal or summing to a zeta), so a path's
   types lie on a line or are one type: q <= 3.
4. Exits through h with delta gathered by first gates: every design exceeds f1 = 7 or is what P3 forbids (a
   10-gate mirror cannot hold four types next to one exit).
5. Changing the export basis / exporting R-values: credited in chi; P2 says when it fails (four types), P3
   that four types are unaffordable to the supplier.
6. Staging: only makes R harder; every bound uses R-gates placed just before their exit.
**What this teaches.** The supplier's mirror pays exactly 2 gates per exit and must hold Z_j + c_j X.
Exposing an exit that needs four types costs the supplier in its mirror what it would save the receiver: the
transposition principle, not span counting.

## Open (precise)
- Several exits with e1 >= 5 and deep labels, each exit with q <= 3 but together four types (test case: two
  disjoint exits of types {a,b,c} and {a,b,d}; T** has 12 gates, not excluded by counting; tau_R <= 6 only an
  upper bound).
- Dependent clean labels at near1 = 10 or 11 (zetas need not be even; P1-P4 do not apply).
- near1 >= 12 with several exits.
No correction term was added.
