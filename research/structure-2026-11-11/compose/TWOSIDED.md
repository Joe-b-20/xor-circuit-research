# Supplying a value across a cut, and what the receiver can gain

Main agent (Opus 5.5), phases 4-5, 2026-11-12. Statements carry their status. "Proved" = complete hand
argument; "reviewed" = independent machine review (not human review). **Current state: section 5 onward.**
The comparison conjectures SB and SB' are REFUTED (section 5.1, 5.2); the current conjecture is SB* (5.3);
sections 6-8 say what kind of statement it is, why it would compose, and where local repairs stop.

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
*Superseded as the best bound* by Lemma 2.1' (`sb/`) and Lemma 5.3.1 below, which also credit unused
labels and reusable intermediate sums. *Remark.* beta is an upper bound on the receiver's gain measured against the labels only; the receiver's
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

## 5. Current state of the comparison (consolidated in phase 5; supersedes the earlier section 5)

**Read this first.** The current conjecture is SB* (5.3). SB (5.1) and SB' (5.2) are REFUTED by verified
circuits and must not be used as targets. Reviews: `../review-sb/`, `../review-sb2/`.

Notation for one instance (the level-1 gates of a reduced MC_l circuit with their entries and exits):
Lambda = (lambda_1..lambda_e1) the labels in entry order; S = the exit values across cut 1, each with its
position in time; E = Even(w^2) + 0 (a fixed 3-dimensional subspace of the far space: vectors that are
zero on w^3..w^l and have EVEN HAMMING WEIGHT ON w^2; "even label" means membership in E, which is not
Hamming parity of the whole label: (u0 | a) with a a unit of w^3 has weight 2 but is not in E).
A *replacement* R is a straight-line list of XOR gates, placed in time, that ends with each exit value at
its exit's position, each gate reading only label values of entries placed before that position and earlier
values of R. L_near(S) = least |R|. beta = L_near(S) - |S| >= 0. tau_min = fewest labels whose span contains
E; sigma = e1 - tau_min >= 0. For a replacement R, tau_R = fewest elements of (labels) together with (values
of R) whose span contains E; chi = min over replacements R of (|R| - |S| + tau_R).

### 5.1 SB (refuted)

*Statement:* near1 - 10 >= beta. *Counterexample* (`sb/dangle2.txt`, MC_2, verified by `sb/mcheck.py` and
independently by `review-sb/ev.py`). Gates (g1_c = units of w^1 = w_c, g2_c = units of w^2 = u_c):
- first sheet, first gates: x = w0+w1, y = w2+w3, z = w1+w2 (the three exports), F3 = x+w2 = E_3,
  F2 = x+w3 = E_2, F1 = y+w0 = E_1, F0 = y+w1 = E_0 (7 first gates);
- a dangling stack of entries d1 = w0+u0, d2 = d1+u1, d3 = d2+u2, and the exit B3 = d3+w0 = u0+u1+u2
  = E_3(w^2) (placed before the remaining entries);
- far gates p0 = u3+u0, p1 = u0+u1, p2 = u1+u2, p3 = u2+u3, B0 = p2+u3, B1 = p3+u0, B2 = p1+u3;
- entries A_i = F_i + p_i (i = 0..3).
Counts: 22 gates + tau 3 = cost 25; f1 = 7, h1 = 0, tau = 3: near1 = 10; entries 7 (labels u0, u1, u2, then
p0..p3): e1 = 7; far gates 7 ordinary + 1 exit: |P| = 8, far1 = 15. The exit costs 2 honestly (u0+u1, then
+u2): beta = 1 > near1 - 10 = 0. *Why it is not a saving:* the receiver pays three entries (booked in far1)
and one exit gate for a value it could build in two gates; SB compared the supplier with an inflated
receiver bound (Lemma 2.1 charges every entry as an export).

### 5.2 SB' (refuted)

*Statement:* near1 - 10 >= beta - sigma (credit the receiver for labels beyond the tau_min it needs as
exports; Lemma 2.1': far1 >= M_(l-1) - beta + sigma). In dangle2: tau_min = 3 (p0, p1, p2), sigma = 4,
beta - sigma = -3 <= 0: SB' holds there.
*Counterexample* (`sb2/sbx5_mc3.txt`, MC_3, verified by `sb/mcheck.py 3` and independently by
`review-sb2/ev2.py`). g3_c = units of w^3 = a_c. Gates:
- far labels: L1 = u2+a0, L2 = u3+a0, L3 = u1+a1, L4 = u3+a1, L5 = u0+u3 (L1..L4 are "deep": nonzero on
  w^3; only L5 is in E);
- entries (a chain and one more): n1 = w1+L1, n2 = n1+L2, n3 = n2+L3, n4 = n3+L4, gC = w3+L5;
- first gates: P1 = w0+w2, P2 = w1+w2, P3 = w0+w3 (the exports), A3 = P1+n2, A0 = P2+gC, Q = A3+gC,
  A1 = Q+n4, A2 = P3+n4 (check of s-parts: A3 has L1+L2 = u2+u3 = p_3; A0 has L5 = p_0; A1 has
  L3+L4+L5 = u0+u1 = p_1; A2 has L1+L2+L3+L4 = u1+u2 = p_2);
- the exit X = w1 + n4 = L1+L2+L3+L4 = (u1+u2 | 0);
- a deliberately plain far side: a = a0+a1, b = a2+a3, C3 = a+a2, C2 = a+a3, C1 = b+a0, C0 = b+a1,
  c = u0+u1, d = u2+u3, e3 = c+u2, e2 = c+u3, e1 = d+u0, e0 = d+u1, q0 = a3+a0, q2 = a1+a2, B0 = e0+q0,
  B1 = e1+a, B2 = e2+q2, B3 = e3+b.
Counts: f1 = 8 (P1, P2, P3, A3, A0, Q, A1, A2), h1 = 0, tau = 3: near1 = 11; e1 = 5; |P| = 24 (5 labels,
the exit, 18 others), far1 = 29; cost 40. Labels independent, span of dimension 5; the only labels in E are
L5, so tau_min = 5 and sigma = 0; L_near(X) = 3 (L1+L2, L3+L4, sum), beta = 2 > near1 - 10 = 1: SB' fails.
(The full circuit costs 40, far above 30: this refutes the abstract supplying-side bound, not 10 per sheet.)
*Mechanism:* the traces satisfy zeta_1 = zeta_2 and zeta_3 = zeta_4 ("free stacks"): two pairs of deep
labels whose sums L1+L2 = u2+u3 and L3+L4 = u1+u3 lie in E, each pair acting like one even label at no cost
to the supplier; one spare mirror gate links the pairs into one fibre path of four labels.

### 5.3 SB* (current conjecture) and the export-reuse correction

**Lemma 5.3.1 (reconstruction bound, proved every l, reviewed; = Lemma 2.1* of `sb2/`).**
far1 >= M_(l-1) + e1 - chi.
*Proof.* Take a replacement R; delete the exit gates and insert R (each R-gate just before the exit it
serves, which is possible because it reads only values placed earlier). The result P' has
|P'| = |P| - |S| + |R| gates, none of them an exit, and contains R^2..R^l, every label signal and every value
of R. Choose tau_R elements of (labels) together with (values of R) spanning E as exports: P' with these
exports is an MC_(l-1) circuit, so |P'| + tau_R >= M_(l-1). Hence far1 = |P| + e1 >= M_(l-1) + e1 -
(|R| - |S| + tau_R); minimise over R. QED
**The export-reuse correction, precisely.** Lemma 2.1' used as exports only labels (tau_min of them);
5.3.1 may also export values that the reconstruction itself builds. Since tau_R <= tau_min,
chi - e1 <= beta - sigma; the correction is the amount tau_min - tau_R, credited only for a replacement that
actually builds those values, and only once (each R-value is one gate of P').
**Conjecture SB*.** For every instance arising from a reduced MC_l circuit (any l, any e1 >= 4):

    near1 - 10 >= chi - e1.

*In dangle2:* chi = 4 (R = {u0+u1, B3}, |R| - |S| = 1; tau_R = 3), chi - e1 = -3 <= 0. *In sbx5:*
R = {L1+L2, L3+L4, X}: |R| - |S| = 2; L5, L1+L2, L3+L4 span E, so tau_R = 3; chi = 5 (the reviewer showed 5 is
exact), chi - e1 = 0 <= near1 - 10 = 1: SB* holds. *Why the comparison changes:* rebuilding X honestly
produces exactly the two shallow even vectors L1+L2 and L3+L4, which the receiver can export instead of the
four deep labels L1..L4; the two extra reconstruction gates are repaid by two fewer exports
(Lemma 5.3.1 gives far1 >= 20 + 5 - 5 = 20, so this supplier cannot help any receiver).

## 6. What kind of statement SB* is

**What determines each term.** near1 = f1 + h1 + tau: the supplying sheet's level-1 gates and its exports.
e1, Lambda (as abstract vectors with entry times), S (with exit times): the interface. chi: a finite
minimisation over straight-line computations on the interface data only (labels, staging, exit values, and
the fixed subspace E); it does NOT involve the receiving circuit. The baseline 10 is M_1. So SB* contains no
receiving circuit and no optimisation over receiving chains; M_(l-1) does not occur in it.
**What it quantifies over.** All supplying sheets that occur in reduced MC_l circuits, for every l. As an
abstract statement it is stronger to require it for the relaxation (N) (TWOSIDED section 1): a circuit on
the units of w^1 in which each entry adds an abstract label (a formal input read once), containing the four
targets (E_i | p_i), tau exports whose w^1-parts span Even(w^1), and exits (pairs of signals with equal
w^1-part); label space U of any dimension (the labels of an MC_l circuit span at most min(e1, 4(l-1))
dimensions; for l >= 3 they may be deep), any e1, any number of simultaneous exits, any staging; "reduced"
meaning only what is visible on the near side (no zero gate, no repeated near value, exit values nonzero,
distinct and not equal to a label value). The relaxation drops that labels may depend on exits through the
receiver (TWOSIDED section 1), so it is a sufficient, not an equivalent, form.
**Normalisation.** The only restriction used in the implication is "reduced", and only for optimal
circuits, which are reduced; no restriction to productive or minimal interfaces is used. (Cleaning is used
inside proofs of special cases, never as a hypothesis of SB*.)
**Is it simpler than the original problem?** Partly. It removes the receiving chain and the length l
entirely, and its right side is computable from the interface. But it is itself a lower-bound statement for
a family of one-sheet circuits whose interface is unbounded (any number of entries, labels of any
dimension, many exits), and chi is a straight-line-program minimum on that interface. By the mirror identity
of `sb/REPORT.md` section 5 it is equivalent to lower bounds for small mirrored maps with an unbounded set of
extra coordinates. So it reorganises the global problem into a one-sheet problem; it does not make it
finite.

## 7. Why SB* would compose, and the induction for SB*

Write the two inequalities side by side for a reduced MC_l circuit with e1 >= 4:

    supplier (SB*):          near1 >= 10 + (chi - e1)
    receiver (Lemma 5.3.1):  far1  >= M_(l-1) - (chi - e1)

and add: cost >= 10 + M_(l-1). What cancels is the single quantity chi - e1: the receiver's possible gain is
measured by the one best replacement R (chosen once, used for every exit at the same time), net of the
labels it no longer needs to export. Crediting: each value of R is one gate of P' and may serve once as an
export in the MC_(l-1) bound; R's gates are counted in |R| once, the deleted exits in |S| once, the entries
once in e1 (far1) and nowhere in near1. Simultaneous exits share R (chi is a minimum over joint
replacements, not a sum of per-exit charges). Label obligations: the labels remain signals of P'; the
MC_(l-1) bound charges only the tau_R chosen exports; the other labels' entries remain in e1, which is
exactly the credit in -e1. Availability: every R-gate reads values placed before its exit (definition of a
replacement), and exports in MC_(l-1) carry no timing condition.
**Theorem 7.1 (proved, given the cited results).** If SB* holds for every instance arising from a reduced
MC_l circuit with e1 >= 4, for every l, then M_l = 10 l for every l >= 1.
*Proof.* Induction on l; M_1 = 10. For l >= 2 take an optimal, hence reduced, T. If no exit crosses cut 1,
Proposition 18.1 gives cost >= M_1 + M_(l-1). If e1 = 3, Theorem 4.1. If e1 >= 4, add the two inequalities
above. So M_l >= 10 + M_(l-1) >= 10 l, and M_l <= 10 l (RECORD 16). QED
**Sufficient, not necessary; what a failure of SB* means (corrected in phase 6).** For a reduced MC_l
circuit T with e1 >= 4 write

    delta := (chi - e1) - (near1 - 10)     (positive exactly when SB* fails for T's supplier),
    epsilon := far1 - [M_(l-1) - (chi - e1)] >= 0     (the receiver's slack above Lemma 5.3.1).

Then, identically, cost(T) = near1 + far1 = 10 + M_(l-1) - delta + epsilon. So T beats the baseline
10 + M_(l-1) exactly when epsilon < delta. An earlier sentence here said a cheap chain "must attain Lemma
5.3.1 with equality"; that is too strong: equality (epsilon = 0) is forced only when delta = 1 (integers). In
general a failure of SB* with deficit delta leaves room for receiver slack up to delta - 1.
Two different objects must be kept apart. The receiver WITH exits is the far part P of T (cost far1). The
object to which Lemma 5.3.1 compares it is the RECONSTRUCTED ordinary far chain P' (P with the exits
replaced by R, exporting tau_R of the labels and R-values), an MC_(l-1) circuit of cost
|P'| + tau_R = far1 - e1 + (|R| - |S|) + tau_R. epsilon >= 0 measures how far P' (with that export choice and
the best R) lies above M_(l-1); it is a statement about P', not about P. A counterexample to SB* therefore
supports an actual cheaper chain only together with a reconstructed far chain P' within delta - 1 of
M_(l-1). No equivalence between SB* and ten per sheet is claimed. The hypothesis of Theorem 7.1 can be weakened to "SB* for
the suppliers of OPTIMAL MC_l circuits" (review-p), which matters for Obstruction O (RECORD 20).

## 8. The reconstruction principle, and where local repairs stand (inequality proved; assessment heuristic)

**Definitions (made precise in phase 6).** Fix T, its labels (as far signal VALUES) and its exits. For a set
Y of far vectors, J(Y) := the least number of gates of an ordinary circuit on the units of w^2..w^l (no exits,
no supplied values) whose signals include R^2..R^l, every label value, and every vector of Y; no export cost
is counted in J. J_0 := J(empty set). For a replacement R, J(R) := J(val R). Then (proved, reviewed)

    |P| >= J(R) - (|R| - |S|)    for every replacement R,

since P' (P with exits replaced by R) is such a circuit with |P| - |S| + |R| gates. Equivalently
J_0 - |P| <= (|R| - |S|) - (J(R) - J_0). This is an UPPER BOUND on the receiver's gain J_0 - |P| over its own
exit-free optimum, valid for every R; no R is shown to attain it (P' need not be optimal for J(R)).
**What it does not say.** It gives no necessary condition for profitable supply. In particular the earlier
wording "a supplied value can pay only if its intermediate sums are of little use to the receiver" does not
follow and is withdrawn. Example (the user's): to supply t = a + b + c + d from labels a, b, c, d, the
replacement p = a+b, q = c+d, t = p+q has surplus |R| - |S| = 2 whether the receiver needs only t or all of
p, q, t; under these definitions J(R) - J_0 can be 0 in both situations (if t, or p, q, t, are signals of
some optimal exit-free receiver anyway), so the bound is the same, while the actual benefit of supplying t
differs. The inequality, its slack, and SB*'s explicit export-basis credit (Lemma 5.3.1: crediting
R-values only as exports, through tau_R) are three different things. Lemma 2.1 gives no credit, Lemma 2.1'
credits unused labels, Lemma 5.3.1 credits R-values usable as exports; none of them is J(R) itself.
*Assessment (heuristic, corrected after review).* An earlier version said SB* is "the last form of the
comparison that can be stated from the interface alone". That is wrong as a mathematical claim: the least far
cost phi(I) compatible with an interface I is itself a function of the interface, and
near1 >= 10 + (M_(l-1) - phi(I)) would be the sharpest interface-only supplier inequality; and within the
computable family a constant supplier baseline A = min(near1 + e1 - chi) can replace 10. What is defensible:
SB* is the last refinement in which the correction is a straight-line minimum over labels and reconstruction
values with a constant baseline; going further means computing phi(I), i.e. solving receiving problems.

## 9. Proved classes and their common mechanism

Separate results, each with its hypotheses (all reviewed):
- Theorem 4.1 (exactly three entries at cut 1; every l): cost >= 10 + M_(l-1). Depends on Lemma R, the
  ten-gate lemma, Lemma 2.1.
- Theorem S1 (`sb/` section 3; every label in E; any e1 >= 4; every l): beta <= 1 <= sigma, so SB' and SB*
  hold.
- Theorem S2 (`sb/` section 4 with the review-sb repairs; e1 = 4, outside Omega): SB' holds.
- Theorem O2 (`sb2/` section 3; e1 = 4, exactly two labels outside E; every near1): SB* holds.
- Lemma Q / Q' (dim span <= 4: beta <= 2) and the Path Lemma (sub-case (3,8,0)).
- (phase 5, `refute/`, reviewed in `review-p/`; ALL UNDER THE HYPOTHESIS THAT THE CLEAN LABELS ARE
  INDEPENDENT, which excludes e.g. dangle2 and the 6+4 ten-gate form) P1: near1 = 10 gives chi <= e1 - 1,
  every l, any number of exits; P4: SB* holds for every instance with exactly one exit, every near1; P3 (the
  mirror lemma behind P4: four triple-sums plus four exit-shifted even vectors need three spare gates, sharp).
- P5: SB* holds for every instance with e1 = 4 (independent labels by P1-P4 and O2; dependent labels with
  e1 = 4 span exactly E and are covered by S1). Omega1 is closed.
**Clean labels (definition, phase 6).** Cleaning is Step 0 of tenth-gate/PROOF applied to the level-1 gates:
keep the gates that carry a target (E_i | p_i) or are ancestors of one; remove a gate whose two operands are
both far (it is a far gate) or whose value is free; entries that survive are the *clean entries*, their labels
the *clean labels*; the other entries (for example dangling stacks feeding only exits) are *unclean*.
Cleaning never increases f1 + h1, keeps every target and its ancestors and the traces zeta of the clean
entries, and is used only INSIDE proofs (to read off T* and the traces); every theorem is stated for the
original circuit T, its full e1 and its full label set. Unclean entries are not discarded by any theorem:
they enter through sigma (each unclean entry raises e1 without raising tau_min). In P4 the cleaning is done
with respect to the targets AND the one exit considered, so the exit and its sources are kept. The hypothesis
"clean labels independent" of P1 and P4 is a hypothesis on T, not a normalisation; it excludes for example
dangle2 and every supplier in the 6+4 ten-gate form.
**What the finite checks of `review-p/` did.** p3check.py: an exhaustive run over all value sets on the five
inputs W0..W3, X with at most two or three further gates; P3 itself has a hand proof (case split), the run
confirms it and supplies the explicit witnesses showing three further gates suffice (sharpness).
p3unit.py: an exhaustive small run giving the least number of gates holding E_c and W_c + X for the four unit
types (exactly 10); the upper bound is an explicit circuit, the lower bound rests on that run. p5o3.py: an
exhaustive run over sets of three or four weight-3 exits for four abstract independent labels (one in E),
every label and exit order, computing chi exactly; P5's o = 3 case was also checked by hand. No solver was
used. These are small exhaustive computations on five-input objects, labelled as checks; no theorem of the
record depends on them except the sharpness remark and the "exactly 10" figure.
**Scope of the new results, restated.** P1 (near1 = 10) and P4 (one exit) assume independent clean labels; P5
(four entries) also covers dependent labels by a separate argument (S1); dependent labels with five or more
entries are open; separate one-exit bounds are NOT added for several exits (P4 cleans with respect to one
exit; exits sharing computation are open).
**Common mechanism (two levels).** (i) Span level: in the classes S1, O2, Q, the label span meets E so that at
most one or two vectors need an auxiliary sum, and the supplier's cheapest forms are rigid enough (Lemma R,
Lemma B, tight mirrors) that exposing them costs the spare gate. (ii) Transposition level (P3, P4): in the
supplier's mirror every exit costs exactly two gates and must carry the exit's label types as vectors
Z_j + X; an exit whose rebuilding would need four types (the only way a single exit can beat SB*) needs three
spare mirror gates, which is exactly the supplier's extra cost. The compensation is a property of the
supplier's transposed computation, not of span counting.
**Remaining scope of SB*.** e1 = 4: none (P5). e1 >= 5: with independent clean labels, open only for SEVERAL
exits whose types together exceed three (test: two disjoint exits of types {a,b,c} and {a,b,d}) and for
near1 >= 12 with several exits; with DEPENDENT clean labels (traces may be odd; P1-P4 do not apply), open,
and a finite check shows where P4's argument breaks: four unit types fit a 10-gate T** at near1 = 11, where
P2 allows chi up to e1 + 2. "SB* holds wherever checked" means the proved classes above and, as checks
only, the inspected circuits; the checks are not evidence for arbitrary length. For l = 3: a 29 needs e1 >= 5,
near1 >= 11 and at least two exits, OR dependent clean labels.

### Historical note (superseded)
Earlier versions of this file proposed SB as "the proposed theorem" with the implication via Lemma 2.1; that
implication is correct as an implication but its hypothesis is false (5.1). The induction for SB* is
Theorem 7.1, not the earlier one.

## 10. The closed-end formulation, and why "18" does not settle M_3 by itself

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
labels at once. The open-end target (now SB*, section 5.3) is the better-founded target: it is about one rigid
sheet, it is uniform in l, and Theorem 4.1 is its first proved case.
