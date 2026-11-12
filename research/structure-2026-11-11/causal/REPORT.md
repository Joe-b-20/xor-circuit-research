# Wirings, order-free charges, scheduling

Report of the delegated investigation of 2026-11-12, saved by the main agent from the investigator's
final message. Machine work, no human review, nothing formalised, and no second machine review yet. No
SAT and no search over circuits or systems; scripts inspect recorded circuits or test proved statements
on designed objects, which proves nothing universal. Status words as in ../README.md.

## 0. Conventions

E is the set of inputs; S contains E and consists of distinct nonzero vectors; P(S) is the set of its
collinear triples; G = |S \ E|. Blocks, sheets, E_c, s_c as in RECORD 3; S_j is the block support of
sheet j. Two sheets j != j' are *adjacent* if j' is in S_j or j is in S_j'. For Q_m this is the m-cycle;
for MixColumns the 8-cycle plus the chords 1-7, 3-7, 4-7. A family J of sheets is *independent* if no two
members are adjacent. MixColumns has 37 independent families; the largest is {0,2,4,6}.

## 1. Wirings

### Lemma 1.1 (a basis has at most one wiring). Proved.

Let T be a set of G triples of S. A *result map* is an injective map tau from S \ E to T with v in tau(v).
If some result map is acyclic (no directed cycle in "other two members of tau(v) -> v"), it is the only
result map on T, acyclic or not. Hence the wirings of S are in bijection with the executable G-subsets T
of P(S), and each such T is a basis of R(S).
*Reason.* A triangular matrix has one transversal.
*Proof.* Let v_1..v_G be a topological order for tau. Then tau(v_i) contains no v_k with k > i. So v_G
lies only in tau(v_G), and any result map sends v_G there. Downward induction: v_i lies only in tau(v_i)
and in some tau(v_k) with k > i, which are already used; injectivity forces tau'(v_i) = tau(v_i). QED
*Relevance.* "Which member of each triple is the result" is not a choice. Ancestry, charges and
block-monotonicity are functions of the basis T. The only freedom is the choice of T inside P(S).

### Lemma 1.2 (first element; set form of the leaf property). Proved.

S is a circuit set iff every nonempty X inside S \ E contains an element v that lies in the closure of E
inside (S \ X) + {v}. In a circuit, the first-created element of X is such a v, and none of its ancestors
lies in X.

### 1.3 The Q_3 value set (inspection of one object; q3_wirings_out.txt, q3_ideals_out.txt)

S has 12 inputs and 28 other vectors. It has exactly 28 collinear triples, the gate triples. So R(S) has
a single triple basis and, by Lemma 1.1, a single wiring, the recorded one. It is not block-monotone by
inspection: OUT(1,2) = [1:s1 2:E1] lies in one triple only, with g14 = [0:s0 2:E1] and g15 = [0:s0 1:s1],
both nonzero on block 0.

| | sheet 0 | sheet 1 | sheet 2 | sum | excess |
|---|---|---|---|---|---|
| wire charges | 12 | 13 | 14 | 39 | 11 |
| dual charges (section 3) | 12 | 12 | 13 | 37 | 9 |

Eleven gates have mu = 2 and none has mu = 3. Dependency structure: a trunk of 8 gates serving all three
sheets (the ancestors-or-equal of g12 = [0:s0 2:s3]), a branch of 4 gates serving sheets 0 and 2, a
branch of 5 serving sheets 1 and 2, and leaves of 3, 3 and 5 gates: 8 + 4 + 5 + 3 + 3 + 5 = 28. Each
sheet's local circuit has the minimal mirrored part (6) and many entries (6, 7, 8, against 3 entries plus
7 in the 10m circuits): each sheet is individually wasteful (12, 13, 14) and the saving is entirely
overlap. Because the wiring is unique, the order is forced by S: OUT(3,0) precedes every output except
OUT(1,1), OUT(2,2); there is a forced relay OUT(3,0) < OUT(0,1) < OUT(1,2).

### Lemma 1.3 (cancellation partner). Proved; trivial.

If g is an ancestor of o, g is nonzero on block k and o is zero on k, then every wire path from g to o
contains a gate c = a + b with a on the path, a and b nonzero on k with equal k-components, and c zero
on k. The partner b is created before c and is an ancestor of o.

### Lemma 1.4 (block-monotone circuits keep sheets apart; Q_m, m >= 3). Proved.

In a block-monotone circuit: A_j and A_j' are disjoint for non-adjacent sheets; the common ancestors of
sheets j and j+1 are gates supported on block j alone; no output is an ancestor of an output of another
sheet. All three fail in the Q_3 circuit.

### 1.5 The main agent's remark, tested

- True part: G depends on S only; charges depend on the basis. By Lemma 1.1 there is no further
  orientation freedom.
- Observed (triple_count_out.txt): |P(S)| = G, hence a unique wiring, for every recorded best circuit of
  Q_m with m = 3..8, 12, 20, for the Q_T variants at 40, 42, 62, 82, 85, and for MixColumns 88@5.
  Exceptions: Q_2 at 16 gates (4 extra triples), MixColumns 89 and 97 (2 each), InvMixColumns 88 (1).
- **Disproved:** "profitable sharing is exactly the case where the part-by-part orientation exists but
  is not executable". By Theorem 3.2, if G < 10m then no basis, executable or not, is free of doubly
  charged triples; the part-by-part system does not exist even as a cyclic system.
- The converse also fails (observed earlier, rotation/mc/corpus_out.txt): 4,176 value sets of 88-gate
  corpus circuits have no block-monotone wiring, and none has fewer than 88 gates.
- Is the saving tied to an ordering constraint? In the Q_3 object, yes (the forced relay). As a general
  lemma, no: what is general is order-free (Theorems 3.2, 3.4) plus the trivial Lemma 1.3.

## 2. The local lemma without gate order

### 2.1 Definitions

Fix a space V, a subspace F (free vectors) and base vectors b_1..b_p independent modulo F. A **local
system** of size K has unknowns y_1..y_K and K equations; each equation is a set of one, two or three
variables (base variables or unknowns) with a right-hand side phi in F, and phi = 0 when there are three
variables; the K x K incidence matrix on the unknowns is invertible over F_2. It has a unique value map.
A local circuit of RECORD 7 (gates of free value discarded) is such a system with a triangular matrix.

### Proposition 2.1 (values). Proved.

With F = 0 and base = the units of F_2^n: the units together with the distinct nonzero values form a
cyclic set, of size at most the number of three-variable equations.

### Lemma 2.2 (parity structure of a cyclic set). Proved.

Let S* be cyclic in F_2^r. Join two odd elements when their sum is in S*. Then the components correspond
to a partition of the coordinates into blocks; an odd element has odd weight on the block of its
component and even weight on the others; the even elements span exactly the vectors even on every block.

### Lemma 2.3 (duality inequality). Proved.

Let a local system of size K contain targets t_c = beta_c + alpha_c (c = 1..r), beta_c in span(b),
alpha_c in F. Let P be the r x p matrix of the beta_c, p' the number of its nonzero columns, and
Omega = {x : sum of x_c alpha_c = 0}. Then there are a cyclic set S* in F_2^r and vectors
zeta_1..zeta_tau in S* + {0} with: (1) every nonzero column of P is in S*; (2) span(zeta) contains the
orthogonal complement of Omega; (3) K >= tau + (|S*| - r) + (p' - r).
*Proof sketch as given.* Step 0: delete one-variable equations and non-target unknowns lying in exactly
one equation. Step 1: replace the right-hand side of the i-th two-variable equation by a formal input
z_i. Step 2: the left kernel of the matrix of the n(g_c) lies in Omega. Step 3: the dual is obtained by
linear algebra (U = Sel N_y^(-1)); its stars are split into three-variable equations, numbering
K - tau + r - p''; Proposition 2.1 gives S*. QED

### Theorem 2.4 (joint local lemma: k unrelated sheets cost 10k). Proved by hand; unreviewed here.

Base b_(i,c), i = 1..k, c = 0..3; targets t_(i,c) = (sum over c' != c of b_(i,c')) + alpha_(i,c) with
alpha in F; assume that sum of x_(i,c) alpha_(i,c) = 0 forces every x_i to be 0000 or 1111. Then every
local system containing the 4k targets has K >= 10k. The quantifier is over all local systems,
executable or not; in particular the local cyclic minimum of RECORD 7 is 10.
*Proof.* Lemma 2.3 with r = p' = 4k gives K >= tau + |S*| - 4k, where S* contains the 4k odd vectors
E_c(w^(i)) and span(zeta) contains EE, the vectors even on every quad (dim 3k). By Lemma 2.2 every quad
meets at most two blocks. Write S* minus the units as 4k targets + the even set V_ev + h helpers. A zeta
is 0, a "free odd" (a unit or target, pure in one quad), an even element, or a helper. Let I be the set
of quads hosting a free odd zeta. (a) Quad parities of the free odd zetas contain |I| unit vectors and EE
lies in the kernel, so tau >= 3k + |I|. (b) X = span(V_ev + helper zetas) projects onto the even spaces
of the quads outside I, and the kernel of that projection on X contains the within-block-even vectors
supported on the I-quads, of dimension >= 2|I|; so |V_ev| + h >= 3k - |I|. Total
K >= (3k + |I|) + 4k + (3k - |I|) = 10k. QED
(This is the same statement as ../sharing/INDEPENDENT-SHEETS.md Theorem 1, found independently, with a
different count and extended to non-executable systems.)

### 2.5 Audit of tenth-gate/PROOF.md

No error in the lemma. The order is used in three places, none essential (Step 0: cleaning by degree;
Step 3: linear-algebra dual; Step 4: a cyclic S* in F_2^4 with at most one even element has at most 4
triples but needs 5). Error found in "A general form": a term |B| - r is missing (since repaired). The
sheet with nothing free also has cyclic minimum 12.

## 3. Charge theorems

### Proposition 3.1 (derivations). Proved.

L_cyc(M) is the least number of collinear triples whose span contains, for every row o, the formal vector
[o] + sum of [e_i] over i in o.

### Definitions

For a based cyclic system (S, T) and an output o: T_o is the unique subset of T whose sum has non-input
part [o] (in a circuit, t is in T_o iff the number of wire paths from the result of t to o is odd). A
triple is *live* on a set of blocks if at least two of its members are nonzero there. Lam_J(T) is the set
of t in T that lie in T_o for some output o of a sheet in J and are live on the blocks J. mu*(t) is the
number of j with t in Lam_{j}.

### Theorem 3.2 (cyclic charge theorem). Proved given Theorem 2.4.

Let M be Q_m (m >= 3) or MixColumns. For every cyclic system S of M, every triple basis T of R(S) and
every independent family J: |Lam_J(T)| >= 10|J|.
*Reason.* Projecting a derivation of the outputs of J onto their blocks is a local system.

### Corollary 3.3. Proved.

(a) |T| >= 10m - sum of (mu* - 1)+; for MixColumns, 80 - ... (b) Call (S, T) dual-block-monotone if t in
T_o implies that all members of t are supported inside the support of o; every block-monotone circuit
is. For such systems the Lam_j are pairwise disjoint, so block-monotone cyclic systems need 10m triples,
and 80 for MixColumns. (c) Unconditionally |T| >= 10 floor(m/2); for MixColumns, 40.
*Tests.* All recorded circuits; 75 based cyclic systems that are not executable (one vector added to the
Q_3 value set, random bases) and 3,600 other bases: no violation.
*Relevance.* The charge inequality is not where causality enters: it has an order-free twin. A premise
set that holds for all cyclic systems cannot prove more than L_cyc.

### Theorem 3.4 (joint charges, all circuits, all wirings). Proved given Theorem 2.4.

In every circuit for Q_m (m >= 3) or MixColumns and for every independent J, the gates that are
ancestors-or-equal of an output gate of a sheet in J and nonzero on some block of J number at least
10|J|. (For |J| = 1 this is RECORD 7.1.)

### Corollary 3.5 (compensation; colourings). Proved.

(a) Let D_j be the single charged sets, exc_J the sum of (mu_J - 1)+, and F_J the "foreign carriers":
gates of D_J in no D_j (such a gate serves a sheet of J, is zero on that sheet's block, is nonzero on
another block of J, and does not serve that block's sheet). Then
exc_J <= sum over j in J of (|D_j| - 10) + |F_J|.
(b) For a partition of the sheets into independent families (two classes for even m, three for odd
m >= 5), G >= 10m - sum over gates of (nu(g) - 1)+, where nu counts the classes charging g.
(c) If some proper colouring makes, for every gate, either its blocks or its served sheets
monochromatic, then G >= 10m. This contains the block-monotone case for m >= 4; for m = 3 it is vacuous,
which is exactly where the 28 lives.

## 4. Rings

### Proposition 4.1. Proved given Lemmas A, S and Theorem C of double-map/REPORT (unreviewed).

For reduced T: L_cyc(D_T) = 3m iff delta(T) = 0 iff L(D_T) = 3m. Consequence: step 4 of double-map
Theorem C is not a scheduling argument; it uses only "the leaves sum to zero round the cycle and the w's
are independent". Theorem C shows no gap between cyclic and causal.

### 4.2 Rotation model

Feedback round the ring cannot lower any Lam_j, because the bound already grants the whole neighbour
block for free, cyclically and jointly for independent sheets. A cyclic system below 10m needs doubly
charged triples exactly as a circuit does. None constructed, none excluded. Whether L_cyc(Q_m) < 10m or
L_cyc(Q_m) < L(Q_m) is open; L_cyc(Q_3) <= 28.

### 4.3 M2 (remark)

Steps 1-3 of double-map Theorem D are order-free; for the pair partition, step 4 is too. Status: proved
for the pair partition only, so L_cyc(M2) is 25 or 26.

## 5. Scheduling

### Lemma 5.1 (what the arguments instantiate). Proved.

Lemma 1.2: in any circuit, every nonempty set X of non-input signals has a member none of whose ancestors
is in X. "The first output of a sheet" is X = that sheet's outputs; "a label exists before the gate that
uses it" is acyclicity of the unique result map.

### Proposition 5.2 (ideals add nothing to charges). Proved.

For an order ideal I and a set X of outputs in I, the charged set of X lies in the ancestors of X, which
lie in I. So the inequalities obtained from all ideals are exactly those indexed by sets X of outputs,
and each has an order-free twin. Causality could only enter through a bound on the wire excess that fails
for the dual excess. None is known.

### Remark 5.3

With the neighbour free, the first 1, 2, 3, 4 outputs of a sheet need 3, 5, 8, 10 gates.

## 6. Qualifications

- The Q_3 saving says nothing about m >= 4 or MixColumns. Theorem 3.4 shows the Q_3 mechanism needs all
  sheets pairwise adjacent.
- Theorems 3.2 and 3.3 make the premises of the charge framework true for all cyclic systems. That
  framework cannot exceed L_cyc(MixColumns), which is at most 88 and unknown. This is a statement about
  these premises.
- L(InvMixColumns) >= 75 remains conditional on the published proof and its repaired audit.
- The 83 bound (RECORD 9) was not examined for an order-free twin.
- Two adjacent sheets were not bounded by 20.

## 7. Files

q3_wirings.py (run_q3.sh), q3_ideals.py, triple_count.py (run_triples.sh), dual_charges.py (run_dual.sh),
mirror_check.py (run_mirror.sh), cyclic_bases_check.py (run_bases.sh), cyclic_loop_check.py
(run_loops.sh), with their *_out.txt outputs. Single core, a few minutes in total.
