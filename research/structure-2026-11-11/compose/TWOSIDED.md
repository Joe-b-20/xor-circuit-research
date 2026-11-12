# Supplying a value across a cut, and what the receiver can gain: definitions and first theorem

Main agent (Opus 5.5), phase 4, 2026-11-12. Statements carry their status. "Proved" = complete hand
argument here; independent machine review pending unless stated (see RECORD 19).

## 0. The setting (from `FRAMEWORK.md`, `prove3/REPORT.md`)

Mirror chain MC_l: a circuit T on groups w^1..w^l (four inputs each) containing
R^k_i = E_i(w^k) + p_i(w^(k+1)) (k < l) and R^l_i = E_i(w^l), with tau of its signals spanning a space
containing Even(w^1) + 0; cost(T) = |T| + tau; M_l = min cost; M_l is also the least size of a local
circuit for the chain of l sheets with the first neighbour free (duality, review-chain gap 1a). T is
*reduced* if no gate is zero and no two signals are equal; an optimal T is reduced, and every lower bound
below is stated for reduced T (reduction never increases the cost).

**The open cut.** Cut 1 separates group 1 from groups 2..l. For a signal v write v = (omega | s), omega
on w^1, s on w^2..w^l. *Level-1* signals have omega != 0; *far* signals have omega = 0.
- Level-1 gates L1: first gates (f1: new omega), *entries* (e1: a level-1 signal plus a far signal pi;
  its *label* is s(pi)), other duplicates (h1: two level-1 operands, omega not new). D1 = e1 + h1.
- Far gates P: both operands far (*ordinary* far gates), or both operands level 1 with equal omega
  (*exits*; value s(x) + s(y)). A gate with one level-1 and one far operand is level 1 (an entry). So P is
  exactly the ordinary far gates plus the exits across cut 1.
- Lambda = the multiset of labels (one per entry), V = span(Lambda). Since s(R^1_i) = p_i(w^2), and every
  level-1 signal's s-part is a sum of labels of entries among its ancestors (induction),
  V contains Even(w^2) + 0. A label is *even* if it lies in Even(w^2) + 0, *odd* otherwise (for l = 2 this
  is ordinary parity).

**Exact split (identity).** cost(T) = near1 + far1 with

    near1 := f1 + h1 + tau,        far1 := |P| + e1.

The entries are booked to the far side: they are the far side's export cost, exactly as tau is the export
cost of MC_(l-1). Known: near1 >= 10 ((F1): f1 + tau >= 10, Lemma 1 at cut 1), and, if P has no exit,
far1 >= M_(l-1) (the far gates are then an MC_(l-1) circuit with the e1 labels as exports;
Proposition 18.1).

## 1. The two problems, completely

**(F) The receiving problem: a far chain with supplied values.** Data: l - 1 >= 1 groups w^2..w^l; a list
of label signals and a finite set S of *supplied* vectors on w^2..w^l.
- Inputs (free): the units of w^2..w^l.
- Supplied values: each s in S is available only from the moment its *supply gate* is placed, and each
  supply gate costs one gate. (In T the supply gates are the exits; there is no other way for a value to
  enter.)
- Compatibility (from T): each s in S is nonzero, is not the value of an earlier signal, and lies in the
  span of the labels of entries placed before its supply gate; more precisely s = Phi(c_s) where c_s is
  the formal difference n(x) + n(y) of the two level-1 operands (section 3), a nonzero vector of formal
  label coordinates supported on entries that are ancestors of x or y. Support: s has zero w^2-part (a
  "skip" value, X1m with m >= 3) exactly when the w^2-parts of the labels in its formal support cancel;
  this can happen with labels that all have nonzero w^2-parts (review: lambda_1 = u, lambda_2 = u + v with
  u a w^2 unit and v on w^3; two entries on one signal r give the exit v). Parity: s is even (in
  Even(w^2) + 0) whenever all labels in its support are even. [Corrected after review.]
- Required: R^2..R^l (all four of each) and the label signals, which must be signals of the far circuit
  (inputs, ordinary far gates or supply gates) whose span contains Even(w^2) + 0.
- Cost: number of far gates (ordinary + supply) + number of entries e1 (one per label use).
- Staging is essential. A static relaxation (S available from the start) is NOT used below: Lemma 2.1
  needs every label signal used to replace an exit to precede that exit; statically a label could be
  computed from the supplied value and the replacement would become circular. [Corrected after review.]

**(N) The supplying problem: one sheet that hands values back.** Data: an abstract label list
Lambda = (lambda_1..lambda_t) (vectors of some space U containing a copy of Even(F_2^4), with span
containing Even + 0), and a set S of required exit values.
- Inputs (free): the units of w^1; base: each lambda_j may be added once, as an entry (entries cost 0 in
  near1; they were booked to (F)).
- Required: the four vectors (E_i(w^1) | p_i) with p_i the adjacent pair-sums of the Even part; tau
  export signals whose w^1-parts span Even(w^1) (cost 1 each; in T they may be far signals or have U-parts
  that cancel); for each s in S two signals with equal w^1-part whose U-parts differ by s.
- (N) is a relaxation, not an equivalent problem: in T a label is available to the near side only once its
  far signal exists, and that signal may itself depend on exits; (N) drops this interleaving.
- Cost: near1 = f1 + h1 + tau (first gates, non-entry duplicates, exports).
For l = 2 this is the pair proof's "first sheet with the second group free"; for every l it is the same
one-sheet problem, with U = the far space and "even" = Even(w^2) + 0.

**How the model follows from an actual circuit.** For a reduced MC_l circuit T, its level-1 gates with
their entries form an instance of (N) with Lambda = its labels and S = its exit values, of cost near1; its
far gates form an instance of (F) of cost far1; cost(T) = near1 + far1 exactly. Conversely the two
instances interlock only through Lambda (far signals read by the near side) and S (near differences read
by the far side), with the staging above.

## 2. The receiver's gain is bounded by the cost of computing the supplied values from the labels

**Lemma 2.1 (honest replacement; proved, every l; machine-reviewed, `../review-twosided/REVIEW.md`).** For
a reduced MC_l circuit, let S be its set of exit values across cut 1 and Lambda its labels. Define
L_near(S) as the least number of XOR gates in a straight-line computation that produces each exit value s
using only label values of entries placed BEFORE the exit of s and values computed earlier in it; exits
whose values are themselves used as labels are replaced earlier, in time order, so no value is used
before it is computed. (A definition allowing "the label signals" in any order is circular: an exit later
used as a label could be computed from itself at cost 0.) Then L_near(S) >= |S| (each s is nonzero,
distinct and not an earlier value) and

    far1 >= M_(l-1) - beta,        beta := L_near(S) - |S| >= 0.

*Proof.* Go through P in order; replace each exit gate, value s, by gates that compute s from label
signals placed before it (they exist: s lies in the span of the labels of entries that are ancestors of
its operands, and each such label's signal precedes its entry, which precedes the exit). The result P'
has only ordinary far gates, contains R^2..R^l and every label signal (labels that were exit values are
now computed honestly), so P' with the e1 labels as exports is an MC_(l-1) circuit:
|P'| + e1 >= M_(l-1). Doing the replacements jointly costs at most L_near(S) gates instead of |S|. QED
*Remark.* beta is an upper bound on the receiver's gain measured against the labels only; the receiver's
own other signals can make the honest replacement cheaper, so the true gain can be smaller. The bound
counts all exits jointly (shared intermediate sums are counted once), as the user asked.

**Why counting supplied values is not enough (the all-ones example).** With the four units of w^2 as
labels (all odd, free for the far side), the single supplied value 1111 on w^2 has L_near = 3 (three
additions of units), so beta = 2; the actual gain on the four triple-sums is 6 - (4 + 1) = 1 (beta is only
the bound). With labels a basis of the even space it depends on the basis: for {1100, 0011, 0110}, 1111 is
a sum of two labels (beta = 0); for {1100, 1010, 1001} it is the sum of all three (beta = 1). [Corrected
after review.] The gain of one value depends on how it sits in the
span of the labels, not on its number; and the cost of the labels to the supplier depends on their parity
type (Lemma B charges two gates for three or four odd labels among four independent ones).

## 3. The supplier's side: the formal picture

Give each entry a formal input z_j (as in tenth-gate/PROOF Step 1); every level-1 signal v gets a formal
mask (omega(v) | n(v)), n(v) in F_2^(e1), and s(v) = Phi(n(v)) with Phi(z_j) = lambda_j. An exit x + y
supplies s = Phi(c) with c = n(x) + n(y). So the supplier's level-1 gates together with its exits form an
ordinary circuit C' on the inputs (w^1, z) that computes the four formal targets (E_i | l_i) AND, in one
gate each, the pure formal vectors c_s (zero w^1-part). The receiver's honest alternative computes the
same Phi(c_s) from the labels at cost L_Lambda(S) >= (formal cost of the c_s from the z) if Phi is
injective. So the compensation question becomes a question about ONE circuit:

> How cheaply can a circuit for one sheet's four targets also expose, as differences of two of its
> signals, formal label combinations c that would be expensive to compute directly?

## 4. The case of three entries composes at every length

**Theorem 4.1 (proved; every l >= 2; machine-reviewed with one step added, `../review-twosided/`).** Every reduced MC_l circuit with exactly three
entries at cut 1 has cost at least 10 + M_(l-1).
*Proof.* e1 = 3 and V contains the 3-dimensional Even(w^2) + 0, so the labels are a basis of it and
V = Even(w^2) + 0. Every exit value lies in V and is nonzero. It is not a label: it differs from every
other signal pi_j (reduced), and the exit gate g cannot itself be the label signal of an entry j, since
entry j would then come after g and not be an ancestor of its operands, so lambda_j = s(g) would lie in the
span of the other two labels, contradicting independence (step added after review). So it is a sum of
two labels or of all three; exit values are distinct, so at most one exit has the value
lambda_1 + lambda_2 + lambda_3, and its honest replacement costs at most 2 gates; a two-label sum costs 1.
By Lemma 2.1, far1 >= M_(l-1) - 1, and far1 >= M_(l-1) if no exit has the three-label value or there is no
exit at all. Near side: if there is no exit, Proposition 18.1 gives the bound. If there is an exit and
h1 >= 1, near1 = (f1 + tau) + h1 >= 11. If h1 = 0, then D1 = 3; the level-1 gates are a local circuit for
sheet 1 (pair Lemma A) and so number at least 10 (ten-gate lemma); exactly 10 would forbid every exit
(Lemma R, prove3 section 2; its proof uses only rigidity and the absence of repeated values, so it
applies to every reduced T); so f1 + 3 >= 11, f1 >= 8 and near1 >= 8 + tau >= 11 (tau >= 3). In all cases
cost = near1 + far1 >= 11 + M_(l-1) - 1. QED
*What it says.* When the first sheet takes the cheapest kind of labels (three even ones), handing values
back can gain the receiver at most one gate, and it always costs the supplier one: the composition is
exactly additive, at every length, whatever the far chain looks like. Exits with skip values (X1m, m >= 3)
cannot occur here (V has zero part beyond w^2).
**Consequence (proved).** A reduced MC_l circuit of cost below 10 + M_(l-1) has at least four entries at
cut 1 and an exit across cut 1. For l = 3: a 29 has e1 >= 4. Hence the residual configuration (G1) of
prove3 reduces to e1 >= 4; (G2) already has e1 = b >= 4.

## 5. The proposed theorem, and why it would give ten per sheet at every length

**Conjecture SB (supply-benefit inequality for one sheet).** For every instance of (N) realised by a
reduced circuit (labels Lambda with e1 >= 4 entries, exit values S),

    near1 - 10 >= L_near(S) - |S|,

with L_near defined from the near side alone (labels of entries placed before each exit; section 2). In
this form SB is a statement about one sheet and its exit positions; with a static L it would be too weak for
Lemma 2.1, and with the far side's label order it would depend on the far circuit. [Restated after review.]

(Weaker variants that also suffice for a given far side: replace L_Lambda(S) by the honest cost from the
receiver's actual signals.)
**Implication (proved; reviewed).** If SB (with L_near) holds for every reduced instance with e1 >= 4, then
every reduced MC_l circuit has cost >= 10 + M_(l-1): for e1 = 3 by Theorem 4.1, for e1 >= 4 by
near1 + far1 >= (10 + beta) + (M_(l-1) - beta). Optimal circuits are reduced, so M_l >= 10 + M_(l-1); with
M_1 = 10 and the upper bound M_l <= 10 l (RECORD 16), M_l = 10 l for every l. The induction is explicit: SB
concerns one sheet (problem (N) depends on l only through the abstract label space U), and Lemma 2.1 holds
for any far chain. In particular M_3 = 30; SB would exclude (G1) and (G2) (sufficient, not equivalent).
**Status.** Open. Known instances: SB holds when e1 = 3 (Theorem 4.1) and when S is empty (near1 >= 10).
It is not known whether SB is true; a counterexample to SB need not give a 29 (the receiver must also be
able to use the values, and beta overstates the gain), so a counterexample would show only that the
proof must use the receiver's structure as well, i.e. that the composition depends on BOTH sides beyond
(Lambda, S). That would itself answer the user's question about what information a compositional proof
must retain.

## 6. The closed-end formulation, and why "18" does not settle M_3 by itself

**4E boundary.** N_2 := the least |T| (no export cost counted) over circuits T on two groups of four
inputs, written (y | x), that contain (E_j(y) | q_j(x)) and (0 | E_j(x)) for j = 0..3 (q_j the adjacent
pair-sums of x) and FOUR DISTINCT NONZERO vectors (z | 0) with z of even weight (pure on the group y that
carries the exports). It is an MC_2 circuit whose export condition "tau signals spanning Even(y) + 0" is
replaced by "four distinct nonzero pure even signals", with no tau added. This is the object L18 of
chain/REPORT section 4. Known: N_1 = 8 (one group); 17 <= N_2 (from M_2 = 20 with three of the four
vectors as exports; review-compose).
**Where it arises.** At the closed cut (cut l - 1) with four independent labels of which at least three are
odd, the double mirror T* of the near part is an MC_(l-1) circuit with a 4E boundary (generalised Lemma B;
review-compose), and f + D >= |T*| + 4.
**Reduction for l = 3 (proved from chain/REPORT section 3 as re-derived in review-compose).** A 29 is
(Z') or (Y') at the closed end. (Z'): tau = 3, D = 4, N = 5, f = 17 = |T*|, so N_2 >= 18 excludes it.
(Y'): D = 5, N = 4, f + tau = 20, |T*| <= 21 - tau if h is clean, so N_2 >= 18 excludes tau = 4 and an
unclean h, but NOT tau = 3 with h clean and |T*| = 18. So a lower bound of 18 does not settle M_3 through
this reduction (not shown: that 18 together with Theorem A and Proposition H cannot close (Y')); one would
need N_2 >= 19 (false? unknown) or a joint statement using the near part's left exports and its right
labels at once. The open-end target SB (section 5) is the better-founded target: it is about one rigid
sheet, it is uniform in l, and Theorem 4.1 is its first proved case.
