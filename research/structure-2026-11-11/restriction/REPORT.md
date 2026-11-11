# Restriction, gate elimination and connectivity for MixColumns

Report of the delegated investigation (model: Opus, 2026-11-11), saved by the main agent from the
investigator's final message because the investigator could not write this file itself. Not yet
reviewed by a second party except where the record (`../RECORD.md`, section 5) says so. Scripts are in
this directory.

**Notation.** C is a normalized circuit (PROOF Lemma 1.1) with signal masks w_s. fo(s) is the number of
gates that use s as an operand; d_s = fo(s) + [s is an output]. C_M = {(u, Mu)} is the code of M. E_P is
the space of vectors of even weight on every block of a partition P of the inputs. c(x) is the largest
number of disjoint nonzero codewords summing to (x, Mx), and c_M = c(1).

**Facts (`facts.py`).** Rows of M have weight 5 or 7 (20 of weight 5); columns have weight 5 or 11;
M.1 = 1. Words of weight 6/8: 84/276 for M and 60/248 for M^T, so both codes have distance 6. Minimum
row distance is 4, with 20 pairs at distance 4, and their differences are all distinct. The 8 bit
families are fixed by M. F1 (PROOF, computer-verified there, not re-verified here): c_M = 8 for M and M^T.

## Summary

- Strongest proved bound from these tools: **L(M) >= 57** (uses F1), i.e. the parity 56 plus one.
  The "plus one" is just y + h >= 1; PROOF already proves far more by other means.
- Class version: for M with all rows odd, d(C_M) >= d and d(C_{M^T}) >= d', L(M) >= n + m - floor((n+m)/d)
  + floor((d'-4)/2); 55 for n = m = 32, d = d' = 6.
- Pure gate elimination: 38 (about 1.2 n). Connectivity alone: 35.
- Restriction at a preserved point is the parity count done step by step (Proposition ID); it cannot be
  a second method.
- No single evaluation point beats 56 (Proposition P1). Two points jointly force no extra gates
  (Proposition MP).

## 1. The restriction lemma

**Lemma R (quotient lemma). Proved.** Let W be a subspace of F_2^n and pi the quotient map. Gate g is
*dead mod W* if pi(w_g) = 0 or pi(w_g) = pi(w_s) for some earlier signal s. Let D_W be the number of dead
gates and L_W(M) the least number of additions needed to compute every pi(r_j) from pi(e_1), ..., pi(e_n).
Then G >= L_W(M) + D_W. Restricting the inputs to a subspace U is the case W = U^perp.
*Proof.* Walk through C keeping, for each value v, rho(v) = the earliest live signal carrying v. If
g = a + b is live then pi(w_a) != 0 (otherwise pi(w_g) = pi(w_b) repeats an earlier value), likewise b.
Emit rho(pi w_a) + rho(pi w_b). Dead gates emit nothing. Every target is 0 or carried by rho. QED

**Lemma R2 (when the residual is an ordinary problem). Proved.** (a) Zero restriction
W = span{e_i : i in Z}: the residual is M with the columns Z deleted. (b) Merges along a forest
(W = span{e_i + e_j}): the residual is MP, P with one column per block. (c) Substitution along the first
gate g = x_i + a that uses x_i: a does not depend on x_i, and G - D >= L(M with x_i := a). (d) General W:
one first pays for building the non-basis quotient inputs.

**Lemma R3 (which gates die). Proved, except (vi), observed.** (i) A gate whose mask is in W dies; so
does a gate with an operand whose mask is in W. (ii) For W = <lambda>: D = #{g : w_g + lambda in {0} or an
earlier mask} exactly. (iii) x_i := 0 kills at least fo(x_i); merging or substituting along g kills at
least 1 + fo(g). (iv) If the number of distinct nonzero non-unit rows drops by l, at least l gates
carrying outputs die. (v) If the columns of M are distinct and no row is a unit vector, one operand of the
first gate has fan-out >= 2 (otherwise both input columns equal the set of outputs reachable from that
gate). If all rows are odd, the first gate (mask weight 2) is not an output, so it has a user, and merging
its operands kills >= 2. (vi) Nothing forces 3 kills: in the recorded 88 every x_i := 0 kills at most 2
(27 inputs of fan-out 2, 5 of fan-out 1) and the best single restriction kills 6; for the 89 and 97 the
figures are 3/6 and 4/6.

**Lemma R\* (transposed form). Proved.** M square with no zero rows or columns, C^T the raw transpose,
Q a k x n 0/1 matrix with at most one 1 per column and no zero row, QM without zero rows or columns.
Then G >= L(QM) - (n - k) + D_Q(C^T), where D_Q counts the gates of C^T that die under z = Q^T y. If each
accumulation tree is associated freely, D_Q >= sum over v of [(d_v - 1) - (nu_v - 1)_+], nu_v the number
of distinct nonzero vectors occurring an odd number of times among the restricted contributions at v.
M^T satisfies every hypothesis of section 2, so eliminating on the output side gives the same numbers.

**Lemma P (parity at any point is a restriction). Proved.** #(odd+odd gates at x) >= wt(x) - c(x) and
#(gates odd at x) >= #(distinct non-unit rows live at x); so G >= wt(x) + wt(Mx) - c(x). Restricted to
W = x^perp every gate dies; Lemma P splits these deaths into "die as zero" and "die as a copy of an input".

**Proposition P1 (no single point beats 56). Proved; the value at x = 1 uses F1.**
max over x of [wt(x) + wt(Mx) - c(x)] = 56, reached at x = 1.
*Proof.* At x = 1: 64 - 8. For any other x != 0 the complementary codeword (1 + x, M(1 + x)) has weight
w' >= 6, so wt(x) + wt(Mx) = 64 - w'. The code shortened to supp(x, Mx) has dimension >= 32 - w'. If that
is >= 2 there is a codeword w != 0, (x, Mx) inside the support, and w and (x, Mx) + w are disjoint and
nonzero: c(x) >= 2 and the bound is <= 64 - 6 - 2 = 56. If w' >= 31 the bound is <= 33. QED

## 2. Gate elimination

How long each needed property survives (w = least row weight = 5, delta = least row distance = 4):

| Property | Needed for | Survives deletions | Survives merges | MixColumns |
|---|---|---|---|---|
| Distinct columns | 2 kills per zero restriction | forever | forever (M injective) | forever |
| No unit row | 2 kills; counting outputs | w - 2 | floor((w-3)/2) | 3 deletions / 1 merge |
| Distinct rows | counting outputs | delta - 1 | floor((delta-2)/2) | 3 deletions / 1 merge |
| Rows odd at the point 1 | parity base; first gate not an output | no | forever | merges only |
| c <= c_M | parity base | no | forever (lifting) | 8 |

**Theorem GE (pure gate elimination). Proved.** If the columns of M are distinct and every row has weight
>= w, then L(M) >= 2(w - 1) + min over |D| = w - 1 of N_2(M[:, D^c]), N_2 = number of distinct rows of
weight >= 2. For MixColumns: 8 + 30 = 38.
*Obstruction.* Delete x7, x8, x15, x16; then y0 = x24, an input. The residual's first gate can be
x24 + x_j with both inputs of fan-out 1 and the gate an output; then every restriction kills only 1 gate.

**Theorem EP (elimination + parity). Proved; the MixColumns number uses F1.** If all rows are odd with
weight >= w and row distance >= delta, and s = min(floor((w-3)/2), floor((delta-2)/2)), then
L(M) >= n + m - c_M + s. For MixColumns s = 1, giving 57.
*Proof.* Let N = MP for a partition of the inputs into blocks and Phi(N) = #blocks + #distinct non-unit
rows - c_M. (A) L(N) >= Phi(N): Lemma P at 1; a partition into codewords of N lifts to one of M, so
c(N, 1) <= c_M. (B) The first gate of a minimal circuit for N is not an output (even weight), so it has a
user; if merging its two blocks loses no row then L(N) >= 2 + L(N') and Phi(N') = Phi(N) - 1. Each merge
lowers a row weight and a row distance by at most 2, so the first s merges lose no row. QED
*Direct check.* A user of the first gate g_1 is g_1 + c. If c is even the user is an even+even gate
(y >= 1). If c is odd the user is odd: a helper (h >= 1), or an output, in which case c = output + g_1 is
a helper (not an input, since the output would have weight <= 3; not an output, since row distance >= 4).
*Obstruction to s >= 2.* The first gate can be x7 + x15 (inside one bit family, c stays 8). Then y0 has
weight 3, the next first gate can be x8 + x16, which turns y0 into the input x24: the merge gate and its
only user die, one row is lost, gain 0. All 20 weight-5 rows and all 20 distance-4 pairs admit such pairs.

**Answers.** Pure elimination gives about 1.2 n (38); with parity about 1.78 n (57). In XOR circuits an
elimination step kills 2 in general; 3 would need a first-layer gate of fan-out >= 2, which nothing
forces. It exceeds 56 by exactly 1 and does not approach 75.

## 3. Connectivity

Requirement R: for all input sets S and output sets T there are at least rank M[T, S] vertex-disjoint
S-T paths (Jukna-Sergeev Observation 3.21, read in source).

**Proposition C1. Proved.** Any fan-in-2 graph meeting R for M has >= 35 gates (outputs are distinct
gates; the cone of the first output contains no other output and reaches >= 5 inputs, so >= 3 further
gates).

**Observed.** R is close to a superconcentrator requirement: for random k-element S and T the mean
shortfall from full rank is 0.8 / 1.4 / 2.1 / 2.5 / 1.9 / 1.2 / 1.0 for k = 1 / 2 / 4 / 8 / 16 / 24 / 28
(`rankstats.py`). The recorded 88-gate graph meets every tested requirement and no single gate deletion
with rewiring survives the tests (`connectivity.py`).

**Open.** Neither a graph with far fewer than 75 gates meeting R nor a proof of more than 35 was found.
Connectivity is blind to cancellation.

## 4. Literature

| Result | Statement as found | Source | How verified | Applies to a 32 x 32 M? |
|---|---|---|---|---|
| Chashkin 1994 | Explicit n x n matrix needs 3n - o(n) fan-in-2 XOR gates; with m outputs 2n + m - o(n). Method: the Hamming parity-check matrix forces n - o(n) gates of fan-out >= 2, then padding. | Discrete Math. Appl. 4(3):229-257 | Secondary: Golovnev-Kulikov-Williams arXiv 1811.04828 (read); Sergeev's 2024 slides (read). Original not read. | No: specific block structure, asymptotic |
| Sergeev 2025 | Explicit n x n matrix with L >= 5n - o(n); circulant and Sierpinski matrices 3n - o(n). Main theorem (slides): B in GF(2)^(n x m), m <= n, no row of weight 1, any 2k rows independent with 2k >= 6 implies L*(B) >= n + (2k-4)/(2k-1) n^(1-1/k) - m, L* <= L. Keywords include "Sidon set". | Math. Notes 118(4):848-862 | Abstract on Math-Net.ru read; theorem from the author's 2024 slides (read); restated in arXiv 2607.28598 (read). Paper not read. | Gives L(M) >= 24 |
| Jukna-Sergeev 2013 | Nothing superlinear known for XOR circuits of unbounded depth. Obs. 3.21: every node cut >= rank. | FnT TCS 9(1):1-123 | Read in source | Obs. 3.21 is R |
| Lev-Valiant 1983 | Every N-superconcentrator has >= (5 - o(1))N edges | TCS 22(3):233-251 | Secondary: Alon-Capalbo 2002 (read) | Only asymptotic; R is not a full superconcentrator |
| Find-Golovnev-Hirsch-Kulikov 2016 | (3 + 1/86)n - o(n) for affine dispersers, full binary basis | FOCS 2016 | Abstract read | No: single-output non-linear functions |
| Li-Yang 2022 | 3.1n - o(n) for affine dispersers | STOC 2022 | Secondary | No |
| Golovnev-Hirsch-Knop-Kulikov 2018 | A formalization of gate elimination cannot exceed about 5n | JCSS 96:107-119 | Secondary | Only as a ceiling |
| Boyar-Find 2014 | Cancellation-free circuits: tight n log n for the Sierpinski matrix | arXiv 1305.3041 | Abstract read | No: cancellation is allowed here |

None of these gives more than about 32 for a 32 x 32 matrix like M.

## 5. Synthesis

**Proposition ID (merge-sequence identity). Proved; numbers observed with `kills.py`.** Start from
singleton blocks; repeatedly merge the two blocks A, B of the first gate still live mod E_P (its value is
e_A + e_B), until no gate is live. Every gate dies exactly once; at step s, D_s >= 1 + l_s (l_s rows
lost); there are n - c_f steps, the l_s sum to m, and c_f <= c_M. Hence
G = n + m - c_f + sum over s of (D_s - 1 - l_s). c_f equals PROOF's block count, so the surplus is
(x - (32 - c)) + y + h: this is PROOF Lemma 1.2 followed over time. Observed surplus 32 / 33 / 40 on the
88 / 89 / 97-gate circuits.
*Consequence.* Applying parity to the residual and adding the dead gates is not a second method. It can
only add lower bounds on x - 24 + y + h; restriction supplies 1.

**Proposition MP (two points force no collisions). Proved.** Colour each signal by (w.1, w.x'). A gate is
a *collision* when its two operands have the same nonzero colour. If both colours (1,0) and (1,1) occur
among the inputs, every odd-weight vector can be computed with no collision gate. In the one-point case
every gate that makes progress is a collision, which is why parity works there and not here.
*Proof* by induction on the vector: an even vector of colour (0,1) is (odd) + (a (1,0) input); for an odd
vector remove one input of the suitable colour so that the remainder is even of colour (0,1); the
all-one-colour cases are handled by v = (g_1 + a) + (g_2 + ... + a). QED

## 6. Scripts and caveats

`common.py` (helpers), `facts.py`, `kills.py`, `rankstats.py`, `connectivity.py [seed]`; standard library,
each under 5 seconds, run under `ulimit -v 8000000`.
56 and 57 depend on F1 from PROOF. Statements about recorded circuits are observed. Literature rows
marked secondary were not read in the original papers.
