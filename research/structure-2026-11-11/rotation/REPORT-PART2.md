# Part II. MixColumns: block-monotone bounds, double-serving gates, corpus check

Follow-up of 2026-11-11 by the same delegated investigator, saved by the main agent from its final
message. Files: rotation/mc/. Status words as in part I (REPORT.md). "SAT" = exhaustive CaDiCaL run on a
complete encoding, no certificate stored. CPU used: about 1.6 hours; no run above 25 minutes. The main
agent re-derived the proofs of II.1 and II.2; an independent machine review is recorded in
`../RECORD.md` section 9 when available.

**Corrections from the independent review (`../review-83/REVIEW.md`), to be read with the text below.**
II.1 and II.2 are confirmed. In II.6 and II.8 item 3, "the only places where a gate can serve two sheets"
and "exactly one cross-sheet cancellation, always on the triangle {1,2,7}" are overstated: only 4,264 of
the 14,638 non-monotone kste circuits are window-local; the others contain a gate lying in no sheet
support, and two hunt records break monotonicity through an exit onto blocks {3,7} with no {1,2,7}
cancellation. Lemma II.7 is proved for Q_m, m >= 4, only. The 83 bound excludes block-monotone circuits
with at most 82 gates, not an 87.

Notation. Block j = inputs (., j), j = 0..7. Sheet j = outputs (c, j) = [j: E_c] + [j-1: s_c] (+ [7: s_c]
for j = 1, 3, 4; sheet 0 = [0: E_c] + [7: s_c]). Sheet supports: S_0 = {7,0}, S_1 = {0,1,7}, S_2 = {1,2},
S_3 = {2,3,7}, S_4 = {3,4,7}, S_5 = {4,5}, S_6 = {5,6}, S_7 = {6,7}. anc(j) = gates that are
ancestors-or-equal of an output gate of sheet j. A gate "serves" sheet j if it is in anc(j).

## II.0 Summary

**Strongest proved statement.** Every block-monotone MixColumns circuit has at least 83 gates (hand
proof on top of the computer-checked 10-gate sheet lemma 3.4).

**Observed.** In all 4,541 block-monotone 88-gate circuits with wiring (4,300 kste, 241 hunt records) the
three parts of the decomposition II.2 are exactly 30, 22, 36. Conjecture: J_01 = 22 and J_347 = 36, which
would give 88 for block-monotone circuits.

**Not all known 88s are block-monotone.** 14,638 of the 18,938 kste circuits and 174 of 415 hunt records
are not. Every non-monotone kste circuit contains exactly one cross-sheet cancellation, always on the
block triangle {1,2,7}. All are still 88.

## II.1 The three-term sheet costs exactly 13 (proved by hand, given Lemma 3.4)

Model. Blocks a, k, b. Base: the 12 inputs and every vector supported on a alone or on k alone (free).
All gates count. Targets: T_c = [b: E_c] + [a: s_c] + [k: s_c], c = 0..3.
Theorem II.1. The minimum is 13.
Proof of >= 13. Discard gates equal to free vectors. Type B = nonzero on b; type M = zero on b, nonzero on
a and on k. A B-gate has both operands nonzero on b, or exactly one operand zero on b ("entry"); that
operand is supported on a alone (class E_a), on k alone (E_k), or is an M-gate (E_M).
(1) #B >= 10 + |E_k|. Set k := 0. Keep, for each restricted mask of a B-gate that is not a unit, the first
B-gate carrying it. A kept gate has operands restricting to a vector on a (free in Lemma 3.4; an M-gate
restricts to one), a unit of b, or a kept value. An E_k gate repeats its other operand, so it is not kept.
The kept gates compute [b: E_c] + [a: s_c], so there are >= 10. Symmetrically #B >= 10 + |E_a|.
(2) For every signal nonzero on b, its (a,k)-part lies in W = A + K + M', where A, K, M' are spanned by the
(a,k)-parts of the E_a, E_k, E_M operands (induction over gates). The targets have (a,k)-parts (s_c, s_c),
so projecting to a: 3 <= dim A + s, and to k: 3 <= dim K + s, with s = number of distinct M-gates used.
(3) Total >= #B + #M >= 10 + max(dim A, dim K) + s >= 10 + (3 - s)+ + s >= 13.
Upper bound: three gates D_x = [a: x] + [k: x] for x in {s1, d1, t}, then the ten gates of the scheme
{s1,d1,t} -> {s0,d0,d1} with D_x in place of x (three_term.py: verified).

## II.2 Decomposition of block-monotone circuits (proved)

Let C be block-monotone with every gate serving some output. Define
  A_j  (j = 2, 5, 6): gates of anc(j) nonzero on block j;
  G01  : gates of anc(0) or anc(1) not supported on block 7 alone;
  G347 : gates of anc(7), anc(3) or anc(4) not supported on block 6 alone or block 2 alone.
Theorem II.2. These five sets are pairwise disjoint, |A_j| >= 10, |G01| >= J_01, |G347| >= J_347, so
G >= 30 + J_01 + J_347, where
  J_01  = least number of gates of a block-monotone circuit over the inputs of blocks 7, 0, 1 with every
          vector of block 7 free, computing sheets 0 and 1;
  J_347 = the same for sheets 7, 3, 4 over the inputs of blocks 6, 7, 2, 3, 4 with every vector of block 6
          and every vector of block 2 free.
Proof. Disjointness: a gate in two of the sets is supported in the intersection of two sheet supports from
different groups; these intersections are {7}, {6}, {2}, {1} or empty, and such gates are excluded or
fail "nonzero on block j". Each set is closed under operands up to free vectors, so it is a local circuit.
Bounds proved by hand (given 3.4):
  J_01 >= 20: ten gates nonzero on block 0 serving sheet 0, ten nonzero on block 1.
  J_347 >= 33: ten for sheet 7, thirteen for sheet 3 (Theorem II.1 with a = 2, k = 7), ten nonzero on 4.
Corollary II.3 (proved given 3.4). Every block-monotone MixColumns circuit has at least 83 gates.

## II.3 What the corpora say about the local values (observed)

corpus.py, over all block-monotone circuits with wiring (4,300 kste, 241 hunt records):
|A_2| = |A_5| = |A_6| = 10, |G01| = 22, |G347| = 36 in every one: 30 + 22 + 36 = 88, with equality.
Charge of sheet 7 = 10 in every one. Gates of anc(3) or anc(4) not supported on block 2 alone or block 7
alone: 26 in 3,414 circuits, 25 in 1,127; in the latter there is exactly one block-7 gate that does not
serve sheet 7. So J_01 <= 22, J_347 <= 36, and a split "sheets 0,1 = 22, sheets 3,4 = 26 with block 7
free" cannot be proved, because 25 occurs: the block-7 vectors must be paid for inside the same local
problem as sheet 7.
Where 88 = 80 + 8 sits in monotone circuits: sheet 1 costs 12 next to a 10-gate sheet 0 (it borrows one
two-block gate), sheets 3 and 4 cost 13 each.

## II.4 What a sheet can lend to a three-term neighbour (proved lemma; SAT side results)

Sheet 0 on blocks a = 7, b = 0. For v = (u on a | x on b) let delta(v) = u + phi(x), phi linear with
phi(e_c) = s_c. Then ker delta = span of the four outputs, and delta([a: sigma] + [b: sigma]) = rot(sigma)
for even sigma.
Lemma II.4. Let M be the span of the two-block gates of a circuit computing sheet 0 and Delta = delta(M).
The diagonal vector of sigma lies in M iff rot(sigma) lies in Delta.
SAT results (three_term.py diag, qa_sat.py, qa_probe.py): no 10-gate sheet circuit contains the three
diagonal gates of a basis of the even space (8 instances UNSAT); there is a 10-gate sheet circuit with
four two-block gates whose span contains the whole diagonal space (SAT), so linear algebra alone does not
exclude J_01 = 20; for the first three such circuits sheet 1 cannot be completed with 10 gates (UNSAT).
Joint SAT for J_01 = 20 undecided after 25 CPU-minutes. Status: 20 <= J_01 <= 22.

## II.5 Lemma 3.4 by hand: 9 of the 10 gates (proved)

Entry gates = gates with an operand supported on a. Set a := 0: entry gates repeat their other operand;
the other gates with distinct non-unit masks compute E_0..E_3 on block b from its four inputs, which needs
6 gates (two even gates are needed). The a-parts of all gates lie in the span of the entry operands and
the outputs' a-parts s_c have rank 3: >= 3 entry gates. The tenth gate rests on the computer check.
sheet_alone.py: the four outputs of a sheet as an 8-input map with nothing free need >= 11 gates (SAT).

## II.6 Double-serving gates

Q_3, 28 gates (q3_mechanism.py). There are exactly four block-cancelling gates (a block of an operand
absent from the result):
  OUT(3,0) = [0:E3 1:s2] + [1:s2 2:s3]        cancels block 1
  OUT(0,1) = [0:s0 2:s3] + [1:E0 2:s3]        cancels block 2
  OUT(1,2) = [0:s0 1:s1] + [0:s0 2:E1]        cancels block 0
  g23      = [0:E2 1:E3] + [0:E2 2:E0]        cancels block 0
Each adds a gate living in window {i,j} to a gate living in window {j,k} and lands in window {i,k}; for
m = 3 the three windows are the three sheets. The mechanism is the triangle, i.e. m = 3 wrapping, not the
4-block partition.

Block graph. Join two blocks if they lie in a common sheet support. Call a circuit window-local if every
gate's support lies in some sheet support.
Lemma II.6 (proved). In a window-local circuit let g = a + b cancel a block. Either supp(g) is inside
supp(a) or inside supp(b) (exit-like), or there are blocks i in supp(a)\supp(b), k in supp(b)\supp(a),
j in both and cancelled, with {i,j}, {j,k}, {i,k} each inside a sheet support: a triangle of the block
graph.
Lemma II.7 (proved). Let C be a window-local circuit for Q_m, m >= 4, in which every exit gate p equals
v + v' for two earlier signals v, v' supported on the block of p. Then G >= 10m. (Rewire each exit as
p = v + v'; the circuit becomes block-monotone.)
Consequence. A circuit for Q_m, m >= 4, with fewer than 10m gates must contain a gate whose support lies
in no sheet window, or an exit whose vector is the XOR of at least three block-local signals and of no
two. Whether this can happen is open. Evidence against: heuristic runs at m = 4 (four seeds, up to 16.5
million steps) and m = 5 (two seeds) all end at exactly 10m with monotone circuits; the same engine finds
the triangle circuits for Q_3 and for MixColumns.

MixColumns. The block graph is the 8-cycle plus the chords 1-7, 2-7, 3-7, 4-7. Triangles {0,1,7},
{2,3,7}, {3,4,7} lie inside one sheet support; exactly one triangle does not: {1,2,7}. violations.py over
the 14,638 non-monotone kste circuits: one block-cancelling gate in 14,003, two in 613, three in 22; every
circuit contains exactly one cross-window cancellation, always on the triangle {1,2,7}. Typical instance:
[1:E3 2:d0] + [2:d0 7:s3] = [1:E3 7:s3]: a point of sheet 1 carried through window {1,2} meets a {2,7}
vector of the three-term sheet 3 and becomes a point of sheet 1 with its block-7 term. So the Q_3
mechanism exists in MixColumns and is used by 77% of the published circuits, but every one of them still
has 88 gates. Q_4 + T[1][3] (triangle {1,2,3}) has its best known circuit non-monotone (42); whether a
monotone 42 exists there is unknown. An 87 for MixColumns through the triangle is not excluded by
anything proved here.

## II.7 Corpus check (corpus.py, corpus_out.txt; read-only)

  kste (18,938 valid 88-gate circuits): block-monotone 4,300; not 14,638.
     monotone: sum of mu 82..88, uncharged gates 6..0, excess 0; charges between
        [10,10,10,11,10,10,10,10] and [11,12,10,15,13,10,10,10].
     non-monotone: sum of mu 84..93, excess 3 in 14,599 circuits, violating gates 5 or 6.
  hunt records (415): monotone 241, not 174; same pattern.
  repository 88, 89, 97: monotone.
  Minimum charge of any sheet over all 19,356 circuits: 10, as the theorem requires.

## II.8 Open, in order of value

1. J_01 in {20, 21, 22} and J_347 in [33, 36]. Proving 22 and 36 gives 88 for block-monotone circuits.
2. The tenth gate of Lemma 3.4 by hand.
3. Exits with three or more terms for Q_m, m >= 4, and the triangle {1,2,7} for MixColumns: the only
   places where a gate can serve two sheets in a window-local circuit.

Files (rotation/mc/): mc.py, corpus.py, violations.py, q3_mechanism.py, qt_monotone.py, three_term.py,
qa_sat.py, qa_probe.py, j01_sat.py, j01_c2.py (not run), sheet_alone.py, logs/.
