# The rotation model Q_m

Report of the delegated investigation of 2026-11-11, saved by the main agent from the investigator's
final message. Status words as in ../README.md. "SAT-certified" = decided by an exhaustive SAT run
(CaDiCaL via pysat) on a complete encoding; no proof certificate stored. No human review. The main agent
re-derived the proof of Theorem 3.5(a), re-checked the local lemma 3.4 with an independent encoding
(`../tools/local_lemma.py`) and recomputed the charges on the recorded MixColumns circuits
(`../tools/charges.py`); see `../RECORD.md` section 7 for what that check covers.

Notation. Input (c,j), c mod 4, j mod m; block j = inputs (.,j). s_c = e_c+e_(c+1), d_c = e_c+e_(c+2),
t = all four, E_c = t+e_c. "[j: v]" = v placed on block j. Sheet j = outputs
o(c,j) = [j: E_c] + [j-1: s_c].  N = 4m, G = N + x + y + h.

## 0. Summary

**Proved, all circuits.** L(Q_m) >= 7m - 1 + ceil(16m/11) for m >= 4 (33, 42, 50, 59, 67 for m = 4..8),
from the incidence and transposition lemmas of PROOF.md sections 1-4 plus the Q_m facts below.
Independently L(Q_m) >= 8m - 4 for m >= 3 by gate elimination.

**Proved given one SAT-certified 8-input lemma** (one sheet costs 10 gates even with every vector of the
previous block free). For every circuit, the sum over gates of mu(g) is >= 10m, where mu(g) counts the
sheets j such that g is nonzero on block j and is an ancestor of a sheet-j output. Hence every
block-monotone circuit has >= 10m gates for m >= 3, and 10m is the optimum in that class for m >= 4.

**Upper bound, proved.** L(Q_m) <= 10m for all m >= 4 (verified circuits; periods 4, 5, 6).

| m | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|
| lower (proved) | 14 | 24 | 33 | 42 | 50 | 59 | 67 |
| upper (verified circuit) | 16 | 28 | 40 | 50 | 60 | 70 | 80 |

**Counterexamples.** "10m" fails at m = 3: a 28-gate circuit with a 4-block partition, x = 8, not
block-monotone. "Removing a block kills 10 gates" is false: an 18-gate circuit for two blocks loses
exactly 8. The parity bound is 7m - 1, not 7m.

**Conjecture.** L(Q_m) = 10m for m >= 4.

**Extra terms (observed).** A diagonal term is free. One off-diagonal term costs +2 (m = 4, 6, 8).
Q_8 plus two block-7 terms gave 85. MixColumns is Q_8 plus three such terms, recorded at 88.

**Main obstacle.** A gate whose block component is later cancelled can serve two sheets, and every
10-per-sheet argument assigns gates to sheets. The tools that do not assign gates stop at 8.45m.

## 1. Basic facts

1.1 Algebra (proved). a = (y+y^2+y^3) + r(1+y) = 1 + r w + w^3, w = 1+y, w^4 = 0: a is a unit, Q_m is
invertible. Q_m^T = P Q_m P with P: (c,j) -> (-c,-j); all boundary facts hold for Q_m^T.

1.2 Identities (proved). Sum_c o(c,j) = t_j; o(c,j)+o(c+1,j) = [j: s_c]+[j-1: d_c];
o(c,j)+o(c+2,j) = [j: d_c]+[j-1: t]; o(c,j)+o(c+1,j)+o(c+2,j) = [j: e_(c+3)]+[j-1: s_(c+3)].
m = 2: Q_2 is the double map D_T with T[a] = {a+1,a+2} on Z_4 (checks.py (3)).

1.3 Relations (facts.py, facts_out.txt; all relations of weight <= 8).
 m = 2: min weight 4 (4 relations); 96 of weight 6; 54 of weight 8.
 m = 3: min 6; 72 of weight 6; 327 of weight 8.
 m = 4: min 6; 48 = 12m of weight 6; 268 of weight 8.
 m = 5..8: min 6; 12m of weight 6 (4m, 4m, 4m with 1, 2, 3 rows); 45m of weight 8.
Families (m >= 4): R'(c,j) = {o(c,j)} + its five units; R(c,j) = R'(c,j)+R'(c+1,j);
R''(c,j) = R'(c,j)+R'(c+1,j)+R'(c+2,j). Sidon for m >= 3. The weight-6 relations span the whole
4m-dimensional relation space (MixColumns: 20 of 32; the rank argument of PROOF.md section 9 has no
analogue). Proof for all m >= 4 by locality: rows of different cyclic runs of sheets have disjoint
supports, so a relation is a disjoint union of relations per run; weight <= 6 means <= 5 rows, so for
m >= 7 each run is a translate of a relation present at m = 7; m = 4..8 computed. Status: proved.

1.4 Triple multiplicity (facts.py). m = 2: up to 6; m = 3: up to 4; m >= 4: at most 3, exactly 16m
values with three representations:
  [j-1: e_b] + [j: s_a], b - a in {0,2,3}   (12m)       [j-1: E_(a+1)] + [j: s_a]   (4m).
The helpers of the 10m circuits (shape [j-1: s]+[j: e]) are not among these; they have two.

1.5 Partitions. Valid = every row odd on exactly one block.
Lemma 1.5a (proved; checks.py (1), m <= 40). Choose p_j in Z_4 with p_j - p_(j-1) in {1,2}. Blocks
L_j = block j minus (p_j,j), plus the pool {(p_j,j) : j}: valid, m+1 blocks.
Theorem 1.5b (proved, computer-assisted). m >= 3: at most m+1 blocks; m = 2: at most 4. Proof by a
transfer graph on block states (partition_bound.py: 371 valid triples; exact closed-walk maxima for
lengths <= 40). SAT (facts.py) agrees for m = 3..8.
Consequence: the parity bound is 7m - 1, not 7m; the 28-gate circuit of Q_3 has x = 8 = 3m - 1.

1.6 Ledger (proved). G = 2N + x + 2h + p - rho. With x = 3m + xi, "G >= 10m" <=> y + h + xi >= 3m.

## 2. Ground truth and constructions

2.1 m = 2: 14 <= L <= 16 (slp_sat.py: k = 12, 13 UNSAT; circuits/q2_16.txt). m = 3: 24 <= L <= 28
(circuits/q3_28.txt: x = 8, y = 4, h = 4, 4-block partition, not block-monotone). Run maps F_l (Q_m
restricted to l consecutive blocks): L(F_1) = 8, 16 <= L(F_2) <= 18.

2.2 Heuristic (search/xorflux quick, one core, 90-400 s): exactly 10m for m = 4, 5, 6, 7, 8, nothing
below. circuits/q4_40.txt .. q8_80.txt; all: x = 3m, y = m, h = 2m, p = 0, natural partition, masks on
<= 2 adjacent blocks, block-monotone. Per sheet: 3 pure producers of the own block, 2 helpers, 1
two-block sum used twice, 4 outputs.

2.3 Sheet schemes; L(Q_m) <= 10m for all m >= 4 (proved). A scheme P -> O: 10 gates over the inputs of
blocks a (previous), b (own) and three given even vectors P of a, computing the four outputs and three
even vectors O of b; pure if the O-gates depend only on inputs of b. Example {s1,d1,t} -> {s0,d0,d1}:
  s0(b), d0(b), d1(b) producers;  h1 = b3 + s1(a);  v = d1(a) + s0(b);  o_1 = d0(b) + h1;  o_2 = h1 + v;
  h2 = t(a) + o_1;  o_3 = d1(b) + h2;  o_0 = v + h2.
Chaining lemma (proved): bases S_0..S_(m-1) with pure schemes S_(j-1) -> S_j give a circuit for Q_m with
10m gates. walks.py: twelve pure schemes (circuits/schemes.json), closed walks
  W4 = (s1 d1 t, s0 d0 d1, s1 s3 d0, s0 s3 t)
  W5 = (s1 d1 t, s0 d0 d1, s1 s3 d0, s1 s3 d1, s0 s3 t)
  W6 = (s1 s3 d1, s1 s2 t, s3 d1 t, s2 d0 d1, s0 s2 d0, s0 d1 t)
giving closed walks of every length >= 4 except 7; q7_70.txt covers 7. Verified for 4 <= m <= 40.

2.4 No period 1 (SAT-certified). For every basis P (28) and rotation r there is no scheme
P -> rot^r(P) at 10 gates. Not excluded: symmetric circuits outside the scheme model.

## 3. Lower bounds (all circuits unless stated)

3.1 Parity (proved): x >= 3m - 1 (m >= 3).

3.2 Gate elimination: L(Q_m) >= 8m - 4 (proved).
Lemma E. Inputs V + W, masks (v,w). k_0 = number of gates a + b with v(a) = 0 or v(b) = 0 or
v(a) = v(b). Then L(F restricted to W = 0) <= G - k_0.
Lemma E'. With k entry gates (one local operand, the other not), the W-parts of all non-local signals
span dimension <= k.
Theorem. (a) L(F_l) >= L(F_(l-1)) + 8. (b) L(Q_m) >= L(F_(m-1)) + 4 >= 8m - 4, m >= 3.
The 8 is attained: checks.py (4) builds an 18-gate circuit for F_2 with exactly 8 killed gates.

3.3 Incidence + transposition: L(Q_m) >= 7m - 1 + ceil(16m/11), m >= 4 (proved given PROOF.md).
Y = max y over minimum circuits of both orientations, C with y = Y, F = y(T(C)) <= Y.
N + h - y + q - z = R + U, R <= 3h, U <= 4q + 2F_miss, so N <= 2h + y + z + 3q + 2F_miss;
q + z <= 3h + 2F_H + y - N; hence 4N <= 11h + 4y + 6F <= 11(h + Y); G >= 4m + (3m-1) + ceil(16m/11).
Extremal profile: Y = 0, 16m/11 helpers each with three represented edges; the system does not know
that labels cost gates.

3.4 Local lemma (SAT-certified). Any circuit over the 8 inputs of blocks a, b and all 11 vectors of
weight >= 2 on block a (free) computing [b: E_c] + [a: s_c], c = 0..3, has >= 10 gates.
free_prev.py --odd outputs: K = 4..9 UNSAT (K = 9: 67 s), K = 10 SAT. Only the 7 even vectors free: also
10. With [b: s_c] also required (last block of a run): 11.

3.5 Theorem (charges). mu(g) = #{j : g nonzero on block j and g ancestor-or-equal of an output gate of
sheet j}. (a) Every circuit, m >= 2: sum_g mu(g) >= 10m, so G >= 10m - sum_g (mu(g) - 1)+.
(b) Block-monotone (g ancestor of o => every block where g is nonzero is a block where o is nonzero),
m >= 3: mu <= 1, hence G >= 10m. With 2.3 the block-monotone optimum is exactly 10m for m >= 4.
Proof. (a) Fix j, a = j-1, b = j. A_j = ancestors-or-equal of the sheet-j output gates. Zero all inputs
outside a, b (outputs of sheet j unchanged). D = gates of A_j nonzero on b; keep the first D-gate of
each restricted value that is not a unit. Operands of a kept gate restrict to: a vector on a alone
(free), a unit of b, or a kept value. So the kept gates are a circuit over the base of 3.4 and
|D| >= 10. Sum over j. (b) mu(g) >= 2 forces j' = j-1 and j = j'-1, impossible for m >= 3.
Scope: (b) allows cancellation inside blocks, any fan-out, any partition; it excludes a gate with a
whole block component that is cancelled before an output. Counterexample without the hypothesis: m = 3,
28 gates, 17 violating gates, sum mu = 39, excess 11 (monotone.py). For m >= 4, a circuit with 10m - d
gates must contain gates of total excess >= d; whether that is possible is the open part.

3.6 Helper-free (proved): h = 0, m >= 3 => G >= 11m - 1.

3.7 Why the other ideas stop. Ledger: known linear facts give 16m/11 extras only. Restriction to two
adjacent blocks counting all gates: a gate is counted in up to three windows and the count falls below
7m; restricting only ancestors gives 3.5 and fails exactly on block-cancelling gates. Elimination: 8
per block, attained.

## 4. Extra terms (observed; heuristic upper bounds, verified circuits)

 Q_4 + T[1][1] (own block): 40 (+0)        Q_4 + T[1][3] (block j-2): 42 (+2), x 13, y 4, h 9
 Q_4 + T[1][2] (block j+1): 42 (+2)        Q_6 + T[2][0]: 62 (+2), x 18, y 6, h 14
 Q_8 + T[1][7]: 82 (+2), x 24, y 10, h 16  Q_8 + T[1][7],T[3][7]: 85 (+5), x 24, y 9, h 20
 Q_8 + T[1][7],T[3][7],T[4][7] = MixColumns (checks.py (6)): 88 recorded (+8).
A diagonal term is free: E_c + s_c = E_(c+1). One off-diagonal term cost 2 in every case; the second and
third terms on block 7 cost 3 each in these runs (one 420 s run each; 85 may not be optimal).
free3.py (SAT with all vectors of two previous blocks free) gave no result.

## 5. Conjecture, counterexamples, obstacle

Conjecture (m >= 4): L(Q_m) = 10m. For: proved upper bound; heuristic stalls at 10m for m = 4..8; exact
for block-monotone circuits; a sheet costs 10 with the whole previous block free. Against: false at
m = 3; (m+1)-block partitions and block cancellation exist for every m and were explored only by a
general heuristic.
Open step: the analogue of 3.4 for three consecutive blocks (two sheets, exits allowed).
Obstacle: every 10-per-sheet argument assigns gates to sheets; a block-cancelling gate can be assigned
to two. Parity, incidence and elimination stop at 7m - 1, 8.45m, 8m - 4.

## 6. Files

qm.py; facts.py (facts_out.txt); partition_bound.py; checks.py; slp_sat.py; run_sat.py; scheme_sat.py;
walks.py; free_prev.py; free3.py (no result); monotone.py; show.py; unfold.py; states.py; gen_mat.py,
run_quick.sh, collect.py (heuristic runs in runs/, 26 MB, not committed); scheme_graph.py (not run);
periodic_sat.py (no result); logs/. Circuits in circuits/ (text: "n k", then k lines "a b"; input index
4j + c). CPU: about 2.2 hours; largest single run 19.5 minutes (Q_2 SAT).
