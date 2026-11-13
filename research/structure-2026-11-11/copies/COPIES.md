# Cancellation copies and gate cost: a feasibility study (phase 10)

Main agent (Opus 5.5), 2026-11-12. The question (user's): can the cancellation-copy measure proposed at the end
of phase 9 be given a valid, nontrivial connection to gate cost? Status words: **proved** = hand argument here;
**check** = direct construction and evaluation of the specified circuits, or ordinary linear algebra on them
(`copyrank.py`, `cutid.py`; outputs in `copyrank_out.txt`, `cutid_out.txt`). No SAT, no exhaustive or
finite-family check, no case enumeration, no least-gate search (by the main agent or the reviewer). Machine
review: `review/REVIEW.md` (not human review, not formal verification). Nothing here changes
75 <= L(MixColumns) <= 88.

## 0. Verdict

The copy measure, read as "copies cost gates", does not measure computation. Under every precise version of a
rank-of-copies measure examined here (section 2, plus the per-recipient baselines found by the reviewer), one of
the following happens.
- A linear baseline that frees the inputs (or the outputs) makes it zero (C1).
- Its rank is carried by the cancelling gates themselves, so it is dominated by counting gates (C2, C3).
- If the gates it is charged to are the partners instead, their capacity is quadratic (C4): k partner gates
  can carry copies of rank k(k-1)/2.
- Deciding which copies are "needed elsewhere" needs the actual circuit, which is the unknown optimum (C5).

The reason is structural. In matrix terms, a removal requirement is a zero-cell equation that every correct
factorisation at a cut satisfies automatically (Theorem F, Corollary Z), so bounds that depend only on the
terms' sum at one cut cannot see it. In node terms, a copy is a property of a pair of operands, not of a gate.
The formulation is therefore left. What survives is:
- the first-exit identity, which contains the phase-7 reader identity J6;
- a sound connection of the opposite shape, found by the reviewer from results already in the record
  (Proposition V): a circuit with no whole-block cancellation is block-monotone and needs at least 84 gates,
  so cancellation is what buys any saving below 84, and the charge deficit R lies in the ancestor cones of
  the cancelling gates;
- a sound conditioning inequality (Proposition R), whose use as a route to bounds has a ceiling (section 8).

## 1. Objects kept apart

Inputs X are the unit vectors of V = F_2^n, and V is partitioned into blocks. pi_S keeps the coordinates of the
blocks in S and zeroes the rest.
- **Signal value** val(v) in V of a node v (an input or a gate).
- **Projected component** pi_S(val(v)): a vector, not a node. One node has one value but many components.
- **Occurrence**: a pair (path P from a node h to an output o, gate e on P) at which a component of h is
  cancelled. One node lies on many paths.
- **Requirement of a recipient**: an output o of sheet j requires only a support condition, pi_c(val(o)) = 0
  for the blocks c outside W_j. It requires no particular node.
- **Physical gate**: a node e with its two operands. Only physical gates are counted by G.

## 2. The candidate, precisely

**Events and copies.** Let e = a + b be a gate. Its *cancelled blocks* are
C(e) = {c : pi_c(a) != 0 and pi_c(e) = 0}; then pi_c(b) = pi_c(a) (Lemma S1). If C(e) is nonempty, e is an
*event*, and its copy is kappa(e) = pi_C(e)(val(a)), a vector of V. Different recipients' projections are
represented as subvectors of the one space V. A variant charges one copy per (event, block); another, the
*recipient form*, sets u(h, j) = pi_(outside W_j)(val(h)) for each node h that is an ancestor of rows of two or
more sheets and each such sheet j (the phase-9 wording).

**Measure.** Q(C; N) = dim(span{kappa(e)} + N) - dim N, for a baseline subspace N of "free" or "needed
elsewhere" values.
- Q0: N = 0.
- QX: N = span(X), the inputs (free by definition of the model).
- QY: N = span(Y), the outputs.
- Staged: N_e = span of the values available before e.
- Q2: a combinatorial (non-linear) baseline that drops every event having an input or an output operand.
  Inputs are free, and output gates are already paid by |Y|.

**Reuse.** A node that is an operand of several events contributes all of their copies. The rank does not by
itself prevent double counting; C4 measures exactly how much it fails to.

## 3. Status theorems

**C1 (linear baselines are vacuous; proved).** For every linear map P and every stage of every circuit, the span
of P(available values) is P(V), because the inputs are available from the start and gates take sums. So any
rank of available values is constant along the circuit: a gate increases no rank. Hence QX = 0 and every staged
version is 0. QY = 0 whenever the outputs span V, which holds for MixColumns (invertible) and Q_3.
*Check:* QX = 0 on every example, and QY = 0 on Q_3 and every MixColumns circuit.
So the global linear readings of "free" or "needed for other outputs" (span X, span Y, staged) give zero,
for the ring, for the triangle and for the superposition witness alike. A per-recipient baseline is not zero
(reviewer: for each sheet j, the copies of events that are ancestors-or-self of sheet-j rows, modulo the other
sheets' rows; sum over j: Q_3 6, triangle lines 1, witness 22, r88 and r89 0), but it is at most the sum over
events of the number of sheets they reach, so C2 and C3 apply to it unchanged.

**C2 (copy rank is carried by the cancelling gates; proved).** There is one copy per event gate, so
Q0 <= min(n, number of event gates). When the events are output gates, Q0 adds nothing to |Y|. The per-(event, block) variant of section 2 is
bounded by min(n, sum of |C(e)|), at most eight times the number of events (witness: sum 180, rank 32); the
conclusion is the same.
*Check:* in the superposition witness all 32 events are the output gates y = H_c + r, and Q0 = 32 = |Y|. The
witness's 489 non-output gates contribute nothing to the copy rank. The phase-9 intuition ("high-rank copies
paid by the remainders") was wrong: the rank sits on the 32 output gates.

**C3 (no inequality from Q0; proved by construction; check).** Let P_k = x_1 + ... + x_k be computed as a chain
and S = P_n. For every n >= 3 there is a reduced circuit with:
- outputs: the prefixes P_2, ..., P_n and S + x_i for i < n;
- every gate an output, so G = |Y| = 2n - 2;
- Q0 = n - 1.
The copies are the coordinates x_i, carried by input partners. So no inequality G >= |Y \ X| + c Q0 with c > 0
holds. (This refutes only the shape "copies cost extra gates"; the opposite shape is in section 8.) (copyrank.py, chain n = 8: G = |Y| = 14, Q0 = 7.)

**C4 (partners have quadratic capacity; proved; sharp).** Let N_2 be the gates that are not outputs (inputs
are never gates). For reduced circuits:
- Q2 <= min(n, k(k-1)/2), where k = |N_2|.
- Each counted event has both operands in N_2.
- Two gates with the same operand pair would have equal values, so a reduced circuit has at most one gate per
  pair.

Since G >= |Y \ X| + |N_2|, this gives G - |Y \ X| >= (1 + sqrt(1 + 8 Q2)) / 2 when Q2 > 0. The inequality is
valid and sharp, but weak. For MixColumns (Q2 <= 32) it gives at most 9 gates beyond |Y|, and Q2 = 0 in r88,
r89 and in every circuit with no whole-block cancellation. (Not in every block-monotone circuit in RECORD 7's
ancestor sense: the reviewer rebuilt one output of r88 into a reduced 94-gate circuit that is block-monotone in
that sense and has Q2 = 2.) The rank bound does not need reducedness; the pair count does.

*Sharpness (construction; check).* Take one coordinate e_ij for every pair i < j of {1..k} (k >= 5), and let a_i
be the sum of the k - 1 coordinates containing i.
- Build a_i as x_first + v_i, where v_i is a chain whose prefixes are declared outputs.
- Output a_i + a_j for every pair: it cancels exactly the coordinate e_ij, so its copy is e_ij.
- The only non-output gates are the k gates a_i, so G = |Y| + k, while Q2 = k(k-1)/2.
- Measured with copyrank.py: Q2 = 10, 15, 28 for k = 5, 6, 8.
- k = 4 is excluded because the a_i sum to 0, so a_0 + a_1 = a_2 + a_3 and the circuit is not reduced.
The user's sanity check (p = x + y supplying the copies x and y) is the same phenomenon at its smallest size.

Why it fails: a copy is the agreement of two operands on a set of blocks, so it is a property of a pair of
nodes. There are quadratically many pairs and linearly many gates. Charging one partner gate per independent
projected component over-counts by that factor. The recipient form shows the same thing for one node: H_c alone
has eight outside-window projections of rank 8 (copyrank.py, node 65 of the witness).

**C5 (the requirement is a coset, the partner a node; proved).** For a gate e = a + b:
- b = e + a, so the partner is determined by the gate and its other operand.
- Lemma S1's condition pi_C(b) = pi_C(a) follows from that and from the support of e.
- The condition alone defines a coset, pi_C(b) = pi_C(a) with b free elsewhere, which contains b = a (giving
  e = 0).

So the recipient's requirement forces no node. The existence of b is forced only because the circuit chose the
gate e. "The copy must be supplied" therefore means "the node b exists". Whether its cost is "already paid
elsewhere" can be decided only relative to the actual circuit:
- serving another output does not mean its cost is paid by an independent bound;
- lying in the span of available values does not mean it is available without gates;
- being an eventual output does not mean it is available when needed;
- belonging to one optimal circuit does not make it necessary in every circuit.
A version that exempts such nodes hides the unknown optimum in the exemption.

## 4. Why removal is invisible to single-cut rank bounds: the first-exit identity

For a node v and an output node o, let rho(v)_o be the parity of the directed paths from v to o (the trivial
path counts when v = o).

**Theorem F (first-exit identity; proved; check).** Let A be a node set, and K a set of columns whose inputs lie
in A. For p in A, let val_A(p) be the parity vector of the paths from inputs to p that use only nodes of A. Then
the columns K of the matrix M are

    M_K = sum over edges (p -> g) with p in A, g not in A, of rho(g) val_A(p)|_K^T
          + sum over output nodes o in A of e_o val_A(o)|_K^T.

*Proof.* Every path from an input in K to an output starts in A. Either it stays in A, ending at an output node
of A, or it leaves A at a unique first edge (p -> g). The prefix is a path inside A and the suffix is any path
from g. Take parities. QED

If A contains X and is closed under ancestors, then val_A = val. cutid.py checks this case at every prefix cut
of r88 (89 cuts) and of the block-order witness (522 cuts), with no failure. J6 (the phase-7 reader identity) is
exactly the case where A is the set of pure-b signals and K is block b (then val_A = omega', and the output sum
is empty because no row is pure); J7 is a corollary of J6. The reviewer checked the identity also on random
sets that are not ancestor-closed, on the J6 sets, on outputs with readers and on an input that is an output.

**Corollary Z (zero cells carry no requirement; proved).** Call (sheet j, block c) with c outside W_j a zero
cell: the rows of sheet j are 0 on block c. Restricted to a zero cell, the terms of Theorem F at any cut sum to
0. This is the matrix analogue of Lemma S1 (an analogy, not a derivation): the "copy" is a linear dependency
among rank-one terms.

Every family of rank-one terms that sums to M satisfies all zero-cell equations automatically. So these
equations add nothing to any bound derived from the terms' sum: rank, the group-rank bound J7, or any function
of the cell sums. Moreover, the least number of rank-one terms summing to M_K is rank M_K (32 for all columns, 4
for one block) whatever the zero pattern, and J7 with sharing allowed has the same minimum. A cancellation
requirement can always be met by having no terms on the zero cell, so it costs nothing at a single cut. The
scope is exactly that: bounds depending only on the term sum at one cut. Families of cuts and ancestry
arguments can see removal (Proposition V, section 8). Its cost, when there is one, is the cost
of the specific terms the circuit chose, that is, of computing the val(p) below the cut and distributing the
rho(g) above it.

## 5. What one consistent definition says on the examples (check, copyrank.py)

| circuit | G | \|Y\| | non-output gates | events (at outputs) | Q0 | QX / QY | Q2 | largest partner capacity | recipient form: rank (one node) |
|---|---|---|---|---|---|---|---|---|---|
| sanity (p = x + y) | 5 | 2 | 3 | 2 (2) | 2 | 0 / 2 | 2 | 2 | - |
| chain, n = 8 | 14 | 14 | 0 | 7 (7) | 7 | 0 / 0 | 0 | 7 | - |
| pairs, k = 5, 6, 8 | 25, 39, 76 | 20, 33, 68 | 5, 6, 8 | 10, 15, 28 (all) | 10, 15, 28 | 0 / 1 | 10, 15, 28 | 4, 5, 7 | - |
| Q_3 (q3_28) | 28 | 12 | 16 | 4 (3) | 4 | 0 / 0 | 4 | 1 | 8 (2) |
| MixColumns r88, r89 | 88, 89 | 32 | 56, 57 | 0 | 0 | 0 / 0 | 0 | 0 | 0 |
| triangle circuits (5 corpus lines) | 88 | 32 | 56 | 1-2 (0-1) | 1-2 | 0 / 0 | 1 | 1 | 2 (1) |
| witness (block, wire order) | 521, 616 | 32 | 489, 584 | 32 (32) | 32 | 0 / 0 | 32 | 8 | 32 (8) |

The five corpus lines are circuits_3.txt lines 1451, 3001, 7451 and 7651, and circuits_2.txt line 783; lines
1451 and 3001 also have a {0, 7} exit. (QY = 1 or 2 in the synthetic rows only because their outputs do not span
V.)

**Against the phase-9 intuition** (ring 0, triangle 1, witness high):
- Without a baseline, the ring has 4 independent copies, not zero.
- The triangle circuits have 1 (lines 7451, 7651, 783: one exit) or 2 (lines 1451, 3001: a second, {0, 7},
  exit); the 1 agrees only where there is one exit.
- The witness has 32, the rank of labels on its 32 output gates.
- With the only linear "needed for outputs" baseline, all three are 0.
The intuition separated the examples only through the undefined exemption.

## 6. Comparison with earlier arguments

- **Reader identity and group-rank bound (J6, J7).** J6 is an instance of Theorem F, and J7 a corollary of J6. They are sound because
  their terms are indexed by physical edges, and the multiplicity t(g) of a term across sheets is charged
  explicitly. That is the correct treatment of "one physical object, several recipient projections". The copy
  candidate has no such identity: copies are not summands of any prescribed matrix, and on the zero cells,
  where they live, the prescribed sum is 0 (Corollary Z).
- **Restriction bounds (J1-J5).** (Corrected by the reviewer.) ACCOUNT's D_c zeroes block c, and an event
  gate is never lost there (0 of 180 (event, block) pairs in the witness, 0 of 7 in the corpus lines, 0 of 4
  in Q_3). It is lost when only block c is kept, a restriction in which every gate that is zero on c is lost.
  So copies are a small sub-count of a very large loss count, and the restriction framework gives them no
  separate weight.
- **Interface compatibility (phase 6, |T| = R_b + w_b, single-cut cap 83).** Theorem F is the linear-algebra
  core of a cut interface. Corollary Z says that the interface's zero-cell part carries no rank requirement,
  consistent with the single-cut caps.
- **The charge identity G = 80 + E - R + U.** No copy quantity bounds U from below:
  - Q_3 has U = 0 but Q0 = 4;
  - the witness has U of about 455 but Q0 = 32, carried by outputs.
  The one valid copy inequality, C4, is a disguised count of non-output gates; it is not a constraint
  independent of the identity.

## 7. Decision

The copy formulation ("copies cost gates", measured by a rank) is left. Mapped onto the user's failure tests:
- **Becomes zero after correctly treating free values:** C1.
- **Counts several projections of one gate as separate computations:** the recipient form (H_c: 8) and the
  pair capacity (C4).
- **Requires an unknown optimal subcircuit as an oracle:** C5.
- **Its valid remnant reproduces an existing bound:** C2 and C4 reduce to counting gates.
No further exemption is proposed.

## 8. What survives, and the next direction

**The reusable explanation.** Removing unwanted components is not an operation with a cost of its own:
- as a requirement, it is a zero-cell equation that every correct factorisation satisfies automatically
  (Corollary Z);
- as a "copy", it is a property of an operand pair (C4), determined by the gate (C5).
Its cost is the cost of the partner nodes that the circuit chose, and that is a circuit cost of a different
linear problem: computing the partners y + h.

**Proposition R (conditioning; proved).** For every circuit C and every set H of values that C computes,

    G(C) >= |H \ X| + L(Y | X u H),

where L(Y | S) is the least number of gates that compute Y when the values of S are given free.
*Proof.* At least |H \ X| gates of C have values in H (values are distinct). Delete them and read their values
as free inputs: the remaining gates compute Y. QED

This is the oracle-free form of the user's question: once the shared values H are fixed, the remainders and all
their sharing are whatever the cheapest completion uses. It holds for every circuit that computes H, and it
combines globally because the gates computing H and the others are disjoint. It is a tautology for H = {} and
says nothing until L(Y | X u H) is bounded below. **Ceiling (reviewer).** Free values never raise cost, so
L(Y | X u H) <= L(Y): a bound T for circuits containing H needs L(Y | X u H) >= T - |H \ X|, which already
implies the unconditional L(MixColumns) >= T - |H \ X|. For the four byte parities (|H \ X| = 4), 80 would
need L >= 76, a new unconditional bound; and relative charges are vacuous there (with H_c free each row is one
gate from free values on its window, so charges give 4 per sheet). Proposition R also credits only |H \ X|
gates, not the cost of computing H. So the H_c case is not easier than the main problem.

**Proposition V (no cancellation, no saving below 84; reviewer, from RECORD 7, 9 and 17; proved).** If a
MixColumns circuit has no event (no gate cancels a whole block component of its operands), then
G >= 84. Equivalently, every MixColumns circuit with at most 83 gates contains a whole-block cancellation.
*Proof.* Always B(a + b) is inside B(a) u B(b); a block of B(a) u B(b) missing from B(a + b) has
pi_c(a) = pi_c(b) != 0, which makes a + b an event. With no event, block supports grow along every edge, so
every ancestor's support lies inside each descendant's: the circuit is block-monotone in RECORD 7's sense, and
Corollary 17.4 (with Theorem 9.2, hand-proved local lemma, machine review only) gives 84. QED The converse fails
(the 94-gate example under C4).
**Localisation (J9 with the window inspection of Corollary 7.2; proved; checked on 8 circuits by the
reviewer).** Every gate with mu(g) >= 2 is a proper ancestor of an event gate: g has sheets j != j', one own
block (say j') lies outside W_j, and by J9 every path from g to a sheet-j row contains a gate cancelling block j',
which is not g itself. Hence the deficit R = sum (mu(g) - 1)^+ lies in the ancestor cone of the events, and
G >= 80 - sum over g in Anc(events) of (mu(g) - 1)^+.
These are the sound cancellation-to-cost statements that exist. Neither is new mathematics (they restate the
block-monotone theorems and J9 in event language), but they have the shape C1-C5 did not examine: cancellations
buy savings below a no-cancellation bound, rather than copies costing gates. The cone can be large (15-16 gates
in the triangle 88s, 489 in the witness), and the bound through R alone is vacuous for the witness (R = 154),
so a quantitative form must not go through R alone.

**Next direction (justified by C1-C5, Corollary Z and Proposition V).** Rank-of-copies measures and single-cut
rank bounds are provably blind to removal; charges are not (Proposition V). The better-justified direction is
the savings shape, because its base case is proved: extend Proposition V from "no event" to "few events of
the observed types", that is, bound how much one whole-block cancellation can save below 84. The observed types
in near-88 circuits are the triangle's block-2 cancellation at a sheet-1 output and the {0, 7} exit; examined
circuits have 0-2 events. A first target: every MixColumns circuit with exactly one event, of the triangle
type, has at least 84 - s gates, with s stated and proved by hand. The statement is local, oracle-free and
precise now. Its known weakness is the many-event regime (the witness has 32 events), which needs another
argument; the examined circuits (all >= 88 gates) say nothing about the size of the saving. Proposition R is
kept as a correct inequality, not as the next route (ceiling above). Any dichotomy with a "superposition class"
requires that class to be defined first.

## 9. Scope corrections applied in this phase (brief; no broad audit)

- The 66/66 example refutes the specified transposition convention (one fixed chain rule), not every
  transposition strategy.
- "Some transposition has >= 80 charged gates" is sufficient for G >= 80; the converse is not established, so
  equivalence is not claimed.
- The unwanted part of H_c outside a MixColumns window occupies 5 or 6 blocks; the full remainder occupies 7.
- Hypothesis H is what the charge count needs. Reducedness and full liveness are verified only for the two fixed
  orders; other orders need dead-gate pruning, which removes only uncharged gates, or a further argument.
- A partner used or charged elsewhere does not thereby have zero marginal cost (Q_3 wording).
- Summary sentences were synchronised on:
  - confinement (a support condition; K forces a non-confined or escaping partner, not an uncharged one);
  - the "exactly 10" lower half, now hand-supported.
The files changed are SUPERPOSITION.md, RECORD.md (section 24), SUMMARY.md, CHECKPOINT.md and
joint/FINITE_AUDIT.md.

## 10. Review status

`review/REVIEW.md` (machine review with its own code; not human review, not formal verification; no search).
Verdicts: C5, Theorem F, the table and Proposition R CORRECT; C1-C4, Corollary Z and the verdict wording CORRECT
WITH FIXES; the J1-J5 comparison WRONG (convention clash). All fixes are applied above: the per-recipient
baselines (C1), the (event, block) bound (C2), n >= 3 (C3), the block-monotone sentence (C4), rank M_K and
single-cut scope (Corollary Z), the triangle counts (section 5), J7 as a corollary and the restriction bullet
(section 6), Proposition V with the cone localisation and the ceiling of Proposition R (section 8), and the
change of next direction. The reviewer's measurements reproduce every table entry.
