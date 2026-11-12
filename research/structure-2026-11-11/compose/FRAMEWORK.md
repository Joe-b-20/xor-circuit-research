# How chain computations compose: cuts, exits and boundary types

Main agent (Opus 5.5), 2026-11-12, phase 3 of the structural study. Status of each statement is given
in brackets. "Proved" means a complete hand argument written here by the main agent; independent
machine review is pending unless stated. No computation is used.

## 0. Objects

**Mirror chain MC_l** (`../chain/REPORT.md` section 1, from transposing the chain of l sheets with block
j-1 free). A circuit T on l groups w^1..w^l of four inputs must contain

    R^k_i = E_i(w^k) + p_i(w^(k+1))   (k < l),     R^l_i = E_i(w^l),     p_i = u_(i-1) + u_i,

and tau of its signals must span a space containing Even(w^1) + 0. Cost K = |T| + tau; M_l is the
minimum, and M_l is also the minimum size of a local circuit for the chain of l sheets. Take T optimal,
hence reduced (no zero gate, no repeated value).

**The same number read the other way (proved, a reindexing).** Reverse the groups (y^k = w^(l+1-k)).
Then M_l is the least |T| + tau for a circuit on y^1..y^l containing E_i(y^1) and
E_i(y^k) + p_i(y^(k-1)) (k >= 2), with tau signals spanning Even(y^l) + 0. This is a chain whose first
sheet has no neighbour (closed end) and whose last sheet must *export* vectors spanning the even space of
its block, one unit of cost per exported signal (open end). So the primal chain (free neighbour on the
left, nothing after the right) and this chain (nothing before the left, an open right end) have the same
cost: a free neighbour is dual to an export obligation. Below, "open end" means group w^1 = y^l, "closed
end" means w^l = y^1.

**Cut k** (1 <= k < l). For a signal v write omega_k(v) for its part on w^1..w^k and s(v) for the rest.
As in `../pair/PROOF.md`: fibres, first gates (f), duplicates (D), pure gates (N, omega_k = 0), entries
(a duplicate a + pi with omega_k(pi) = 0; label s(pi)), and **exits across cut k**: pure gates x + y with
omega_k(x) = omega_k(y) != 0.

## 1. Exit-free cuts are additive [proved]

**Proposition 1.** If an optimal T for MC_l has no exit across cut k, then M_l >= M_k + M_(l-k).

*Proof.* (a) f + tau >= M_k: chain/REPORT Lemma 1 for an arbitrary cut. A first gate is not an entry
(an entry keeps the omega of its non-pure operand) and not an exit, so its operands have nonzero,
different omega; replacing each operand by the first signal of its fibre gives a circuit R of f gates on
w^1..w^k whose signals include every occurring omega, in particular omega_k(R^j_i) = R^j_i (j < k) and
omega_k(R^k_i) = E_i(w^k). The omega-parts of the exports are signals of R or zero and still span a space
containing Even(w^1) + 0. So R with these exports is an MC_k circuit.
(b) D + N >= M_(l-k). Without exits, a pure gate has two pure operands, so the pure gates form a circuit
P on w^(k+1)..w^l; it contains R^(k+1)..R^l. Every gate with omega_k != 0 is a sum of two such signals or
an entry, so by induction its s-part lies in the span of the labels; s(R^k_i) = p_i(w^(k+1)), so the
labels span a space containing Even(w^(k+1)) + 0. The labels are signals of P, so P with the e labels as
exports is an MC_(l-k) circuit: N + e >= M_(l-k). Entries are distinct duplicates: D >= e.
Add (a) and (b). QED

**Corollary 2.** Suppose M_j = 10 j for j < l but M_l < 10 l. Then every optimal circuit for MC_l has an
exit across every one of its l - 1 cuts, and M_l = 10 l - 1 (by chain/REPORT Theorem 1, independently
reviewed in `../review-chain/`). For l = 3: a 29 needs exits across both cuts. (Proposition 1 and this
corollary: machine-reviewed, `../review-compose/REVIEW.md`; the proof never uses optimality, so every
exit-free circuit costs at least M_k + M_(l-k).)

**What this says.** The minimum costs M_k are the only information needed about the two parts of a chain
as long as no gate of the later part hands a pure vector back across the cut. Everything a
composition theorem has to control is concentrated in the exits.

## 2. What an exit is, and what flows across a cut [proved descriptions, from the definitions]

Across cut k two things flow, in opposite directions.
- **Labels** go from the far side (pure, groups > k) to the near side: an entry adds a pure signal to a
  signal of groups <= k. The labels must span Even(w^(k+1)) + 0. A label that is an input or a required
  vector of the far side costs the far side nothing extra; any other label is a further gate there (in
  the pair: "N_0 >= 4 + number of even labels", fact (E) of pair/PROOF).
- **Exits** go back: two signals of one fibre differ by a pure vector, and one gate makes that vector
  available on the far side. Its value lies in the span of the labels and is never 0 or a single label
  (either would repeat a value). When every duplicate of the fibre is an entry, the value is the sum of the
  labels along the path between the two signals; with non-entry duplicates it can combine labels of other
  fibres (review counterexample: entries x = w0 + u1, y = w1 + u2, non-entry duplicate h = x + y in the
  fibre of r = w0 + w1, exit r + h = u1 + u2). An exit gives the far side, for one gate, a combination of
  several of its own labels. [Corrected after review.]

In primal terms (transposing): the mirror groups are the sheets. A mirror gate is a partial sum of the
adjoints of the readers of one primal signal v (a fan-out branch of v; which partial sums occur depends on
the summation order chosen in the transposition). An exit is such a partial sum whose omega vanishes
although its two parts do not: two branches of v influence the outputs of sheets <= k identically, so
their joint influence there cancels, while they still influence sheets > k. This is double service across
the cut in the derivation sense of RECORD 13. Cancellation-free circuits have no exits in any summation
order (the readers' adjoints have disjoint supports). Block-monotone circuits CAN have exits: the reviewer
built a valid block-monotone pair circuit (r1 = x0 + x1, r2 = x0 + x2, r1 + r2 cancelling x0 inside block
b1) in which summing adj(r1) and adj(r2) first gives an exit across cut 1 (`../review-compose/
bm_exit_check.py`). An earlier version of this paragraph said block-monotone circuits have none; that was
false.

**Why the minimum cost of the shorter chain is not enough.** In the pair proof the compensation for exits
is Lemma B: when the labels are a basis with three or four labels outside Even(w') (odd labels), the
near side's own mirror needs four distinct even traces, and its part costs at least 12 instead of 10. That
uses information the number M_1 = 10 does not carry: how the near side's cost depends on the *parity
type* of the labels it receives. At cut l - 1 of a longer chain (peeling the closed end, as chain/REPORT
does), the near side is the chain of l - 1 sheets, and the corresponding information is how M_(l-1)
changes when its labels are odd. Lemma A and Lemma B of the pair proof transfer (the omega != 0 gates of
the near side form a local circuit with the far side free, and its mirror T* is again a mirror chain of
length l - 1, now with the four traces as exports): if three or four of four independent labels are odd,
T* is an MC_(l-1) circuit whose exports must include FOUR DISTINCT NONZERO PURE EVEN vectors (z | 0..0).
Call this the **4E boundary**. For l = 2 it is a single sheet with four distinct even signals: rigid, 8
gates. For l = 3 it is the pair with a 4E boundary, whose value is open (chain/REPORT: at least 17
gates, conjectured 18).

So the near side must be described by at least two numbers, its cost with the standard export boundary
(M) and its cost with the 4E boundary (call it N_k: the least |T| for MC_k containing four distinct
nonzero pure even vectors on w^1; N_1 = 8, 17 <= N_2 <= ?). And the bound in the pair proof needs, in
its tightest case, more than both numbers: the rigidity of the 8-gate T*, i.e. the complete list of its
signals. That is what does not survive one level up.

## 3. The two ends are different, and the two peelings use different ends [observations proved; the two "forms" at the end are programmes, not stated theorems]

(Results obtained along the open-end route since this section was written: `prove3/REPORT.md`, Lemma R,
Corollary R and Theorem A, machine-reviewed; see RECORD 18.) For "pure" in the 4E boundary an unstated step
is needed: injectivity of the label map forces the trace coordinates of groups below l - 1 to vanish, so
each trace lives on one group (review). N_2 >= 17 follows directly from M_2 = 20 by using three of the four
even vectors as exports.

- Peeling the closed end (cut l - 1; chain/REPORT) leaves a long near side (l - 1 sheets) and a single far
  sheet. Its bound f + tau >= M_(l-1) uses the near side's left boundary (exports) and forgets its right
  boundary (the labels and exits at the cut); the double-mirror bound f + D >= |T*| + t uses the right
  boundary and forgets the exports. Neither sees both ends of the near side.
- Peeling the open end (cut 1) leaves a single sheet as near side, at every length. Its bound f + tau >= 10
  and its double-mirror bound (Lemma B, generalised: "odd" now means outside Even(w^2) + 0) concern one
  sheet, whose mirror is rigid in the tight case. The far side is now the long part: an MC_(l-1) circuit
  that receives exits. The open question moves to the far side: how much can exits (sums of labels along
  fibre paths of ONE sheet) save an MC_(l-1) circuit whose exports are those labels?

A uniform proof of M_l = 10 l by induction would follow from either of:
- (closed-end form) a two-sided statement about MC_(l-1) bounding f + D + tau jointly when the labels at
  its right end are odd, i.e. the cost of a chain with a 4E boundary at one end AND standard exports at
  the other; or
- (open-end form) a far-side lemma: exits supplied by a single sheet save an MC_(l-1) circuit at most as
  much as Lemma B charges that sheet.
For l = 2 the two forms coincide with the pair proof.

## 4. Rings and MixColumns: which boundary appears where [proved reductions; values open]

- **Ring.** The mirror of Q_m has the required vectors R^k_i = E_i(w^k) + p_i(w^(k+1)) with cyclic
  indices and no exports. Cut it into an arc S = groups k..k+r-1 (omega = part on S) and the far arc S^c.
  Then R^(k-1)_i, a vector of the far arc's last sheet, has omega = p_i(w^k) != 0, so the projection of
  the first gates must contain the four SPECIFIC even vectors p_0(w^k)..p_3(w^k): the near arc gets a 4E
  boundary with prescribed vectors at its left end (closed at its right end). The far arc gets the
  standard export boundary at its left end (labels spanning Even(w^(k+r)) + 0, from s(R^(k+r-1)_i)), and at
  its right end a second label obligation: s(R^(k-1)_i) = E_i(w^(k-1)), so the labels must also span all
  of F_2^4 on the far arc's last group (units of that group do this at no gate cost, but each needs an
  entry: at least 3 + 4 = 7 entries in all when the far arc has at least two groups; when it is a single
  group the two obligations fall on the same group and only F_2^4, at least 4 entries, is forced). So the boundary types of a ring cut are different from those
  of an open chain on both sides, and bounds for open chains (M_l) do not transfer: the additional argument
  needed is the cost of arcs with these ends, together with control of exits across both interfaces.
  Consistent with Q_3: its pairs cost 23 and 24 > 20, no pair bound is violated, and the exit-free bound
  from S = one group is far below 28 (8 rigid first gates + 7 entries + the far arc), so it says nothing
  against the 28. [Reduction proved; no value computed.]
- **MixColumns.** Besides the ring structure (8 positions), the reduction terms give sheets 1, 3, 4 a
  second neighbour (block 7); in the mirror their export space becomes the diagonal (J_01, RECORD 17), a
  third boundary type, and the window graph has triangles, through which an exit can land inside a window
  (the Q_3 mechanism). Each of these needs its own interface lemma; none follows from chain results.
