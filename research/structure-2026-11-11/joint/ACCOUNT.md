# Several restrictions of one circuit: accounting, delivery, sharing (phase 7)

Main agent (Opus 5.5), 2026-11-12. Status words: **proved** = hand argument given here (main agent; machine
review in `review/REVIEW.md`, not human review); **check** = program output on explicit circuits (scripts in
this directory; read-only corpus scans or verification of explicit constructions; no SAT, no search,
no exhaustive enumeration); **conjecture**. Nothing here changes 75 <= L(MixColumns) <= 88.

Notation. Inputs x_(c,b) = bit b of byte c (wire 8c + b); block b = the four inputs of bit position b; V_b =
vectors supported on block b; B(v) = set of blocks where v is nonzero; a value is *pure-b* if it is a nonzero
element of V_b. Sheet j = the four rows (c, j); window(j) = B(row) = {j, j-1} plus 7 for j in {1, 3, 4}
(window(0) = {0, 7}). C is a circuit of G two-input XOR gates computing MixColumns; it is *reduced*: gate values
are distinct, nonzero and not inputs. (Normal form, justified: deleting a gate whose value is zero, an input or
an earlier value, and redirecting its readers, keeps a valid circuit and lowers G; so every lower bound may
assume reduced circuits. Nothing else is normalised.) Sigma = {0} u inputs u gate values, |Sigma| = G + 33.

## 1. The restriction accounting, precisely

For a set B of blocks, pi_B zeroes the blocks of B. Process the gates in circuit order; gate g is **removed**
if pi_B(g) equals pi_B of 0, of an input, or of an earlier gate, and **retained** otherwise. Three removal
categories: (Z) pi_B(g) = 0 (g lies in the span of the blocks of B); (I) pi_B(g) is a surviving input;
(D) pi_B(g) = pi_B(h) for an earlier gate h. D_B(C) = number removed, S_B(C) = G - D_B(C) = number retained.
The retained gates, each rewired to the first producers of its operands' images, form a circuit for
M_B = MixColumns with B zeroed; a retained gate may still be **dead** there (not an ancestor of a restricted
output; a fourth category); U_B = S_B - dead_B >= K_B := L(M_B). Meanings kept explicit: S_B(C) and U_B(C) are
counts in this particular circuit, not L(M_B); a removed gate may be essential to C; the categories need
different arguments (Z and I are visible in g and its operands, D may involve unrelated gates).

**J1 (value-set formula; proved).** D_B(C) = |Sigma| - |pi_B(Sigma)| - 4|B|.
*Proof.* pi_B(Sigma) consists of 0, the 32 - 4|B| surviving inputs (distinct, nonzero), and one new image per
retained gate; so |pi_B(Sigma)| = 33 - 4|B| + S_B, and |Sigma| = 33 + G. QED
Consequence: D_B and S_B depend only on the value set Sigma, not on the wiring or the order; the split into
categories, the dead count and the attribution of a removal to a particular gate do depend on them.

**J2 (one block: local and nonlocal removal; proved).** Let P_b = gates with pure-b value, R_b = gates not in
V_b with an operand in V_b ("readers"), L_b = P_b u R_b. Every gate of L_b is removed at b, so
D_b = |L_b| + N_b with N_b >= 0 ("nonlocal" removals: pi_b(g) = pi_b(h) with g - h in V_b although neither g
nor its operands lie in V_b).
*Proof.* g in V_b: category Z. g = a + c with c in V_b: pi_b(g) = pi_b(a), a earlier: category I or D. QED
A reader has exactly one operand in V_b (two would put g in V_b). lambda(g) := #{b : g in L_b} <= 2 for every
gate (a non-pure gate has two operands; a pure-b gate with a pure-c operand, c != b, has its other operand on
{b, c}).

**J3 (two blocks: the overlap; proved).** For blocks b != c, D_bc = D_b + D_c - O_bc with
    O_bc = sum over the fibres F of pi_bc on Sigma of (n_F - r_F - s_F + 1),
n_F = |F|, r_F (s_F) = number of distinct block-b (block-c) parts in F.
*Proof.* Within F the classes of pi_b are the distinct c-parts, so F contributes n_F - s_F collisions to
|Sigma| - |pi_b Sigma|, n_F - r_F to the c count and n_F - 1 to the joint count; apply J1. QED
Mechanism. Put the points of F as edges of the bipartite graph (b-parts) x (c-parts): n - r - s + 1 = (cycle
rank) - (components - 1). A positive term needs a cycle, the smallest being a rectangle {s, s + u, s + v,
s + u + v}, u in V_b, v in V_c; the user's example {0, x_b, x_c, x_b + x_c} is one (the gate x_b + x_c is removed
at b alone and at c alone, counted twice in D_b + D_c and once in D_bc). A negative term is a fibre that falls
apart: two signals differing on both blocks with nothing in between, removed jointly but at neither block
alone. Heuristically (fibre terms also come from nonlocal coincidences, and terms can be negative), the
double-counted gates are the lambda = 2 gates (a pure-b operand and a pure-c operand, or a
pure-b gate reading a pure-c value). In the corpus the overlaps are small and of both signs (adjacent pairs of
the recorded 88: -2, 1, -1, 0, 1, 0, 1, -1; check, jstats.py).

**J4 (all eight blocks; proved).** With lambda_k = #{g : lambda(g) = k}, N = sum_b N_b:
    sum_b D_b = G + lambda_2 - lambda_0 + N,        7G = sum_b U_b + lambda_2 - lambda_0 + N + sum_b dead_b.
*Proof.* sum_b |L_b| = sum_g lambda(g) = lambda_1 + 2 lambda_2 = G - lambda_0 + lambda_2; add N; then
sum_b U_b = 8G - sum_b D_b - sum_b dead_b. QED
Consequences. (a) J4 is exactly the sum of the eight one-block identities G = U_b + |L_b| + N_b + dead_b
(lambda_2 - lambda_0 = sum_b |L_b| - G), so by itself it adds no information beyond the single blocks (it does
not rule out a new structural relationship among its terms, which would be new content): 7G >= sum_b K_b +
lambda_2 - lambda_0 is the average of G >= K_b + |L_b|, and any average of single-block bounds is at most the
best one. (Review fix: an earlier draft called lambda_2 - lambda_0 "new content".) The joint information lies in
J3's pair and higher overlaps, not in the eight-block sum. For scale: W* below has 263 gates, lambda_0 = 196,
lambda_2 = 1. (b) Removal is monotone in B (images equal under pi_B stay equal under further zeroing), so
zeroing blocks one at a time in any order gives G = sum of the successive removal counts, each gate removed
exactly once: gate elimination. Every D_B is a sum of increments along a chain; linear combinations of the D_B
(such as J3's overlap) are signed combinations of increments.

**J5 (where the difficulty goes; check).** Bounds of the form "L >= K_B + delta_B, delta_B a lower bound on D_B
valid for every circuit" are at most cap_B = min_C U_B(C) + min_W D_B(W) over explicit circuits. With the
recorded 88/89/97, every 100th kste circuit, the low-waste circuits of review-compat, W* (prefix chain, 263
gates) and new constructions lowwasteB.py (carriers: each block of B delivered on the "diagonal" with a block
outside B; 152-229 gates, all verified and reduced) (caps.py, lowwasteB.py):
| \|B\| | largest cap (sample-dependent: "at most") | all caps < 88 | least-D_B witnesses |
|---|---|---|---|
| 1 | 83 (82 on the reviewer's larger sample) | yes | constructions / lw, waste 5-6 |
| 2 | 85 | yes | constructions (own D_B 11-28) |
| 3 | 88 at B = {4,5,6} | no | constructions for 46 of 56 triples; at {4,5,6} the recorded 88 itself (D = 31) |
| 4 | 87 | yes, narrowly | corpus 88s for all 70 sets |
So for |B| = 1, 2 and 4 every form of this kind is capped below 88 by explicit circuits (at |B| = 4 narrowly,
by corpus 88s); at |B| = 3 one set, {4,5,6}, is not capped below 88 by the known circuits. Not being capped
by the known witnesses does not show that a waste bound restricted to <= 87-gate circuits is needed, only that
these witnesses do not exclude a universal one (at B = all blocks, D_B = G is the original problem). These caps constrain universal (all-circuit) waste bounds; they say nothing
about bounds proved only for optimal circuits or circuits with at most 87 gates (the constructions have
152-263 gates).

**What cheap circuits look like under restriction (check, readers.py, jscan.py; recorded 88/89/97 and every
25th kste circuit, 763 circuits, all 88-97 gates).** Removal is local up to coincidences: N = sum_b N_b is 0-6
per circuit (mostly 2); dead gates 0-1. So for these circuits the eight restricted computations are obtained,
up to a few coincidences, by deleting one block's pure gates and short-circuiting its readers. sum_b D_b - G is
-5..16 (mostly -2): "every gate is removed at about one block" is not a law even for 88s.

## 2. How block content reaches the outputs: the reader identity

For a gate g let rho(g) in F_2^32 (indexed by the rows) be the parity of the number of directed paths from g to
each output node. For a pure-b signal p define omega'(p) in F_2^4: omega'(x_(c,b)) = e_c and, for a pure-b
gate p = a + a', the sum of omega' over its pure-b operands (paths that stay inside the pure-b signals).

**J6 (reader identity; proved; verified on every circuit examined, readers.py).** For every circuit computing
MixColumns, every block b and every unit k,
    column (k, b) of M = sum over g in R_b with omega'(p_b(g))_k = 1 of rho(g),
p_b(g) the pure-b operand of g. Equivalently M restricted to block b's columns = sum over g in R_b of
rho(g) omega'(p_b(g))^T, a sum of |R_b| rank-one matrices.
*Proof.* The (row r, column (k,b)) entry of M is the parity of the number of paths from x_(k,b) to r. Rows are
not pure (each row meets two or three blocks), so every such path leaves the set of pure-b signals; split it at
its first edge (p -> g) leaving that set: g is in R_b and p = p_b(g); the prefix stays among pure-b signals
(parity omega'(p)_k), the suffix is any path from g to r (parity rho(g)_r). QED

**J7 (group-rank bound; proved).** For any partition Gamma of the rows,
    |R_b| >= sum over groups gamma of rank(M_b restricted to gamma) - sum over g in R_b of (t(g) - 1)^+,
t(g) = number of groups (among those where M_b is nonzero) that rho(g) meets.
*Proof.* Restricted to gamma, the identity is a sum of rank-one terms, one for each g with rho(g) nonzero on
gamma; so rank_gamma <= #{g : rho(g) meets gamma}; sum over gamma. QED
With Gamma = sheets: the block-b columns meet sheets b (parts E_c, rank 4) and b+1 (parts s_c, rank 3), and at
block 7 also sheets 0, 1, 3, 4: the sheet ranks are 7 at b < 7 and 4 + 4 x 3 = 16 at b = 7, 65 in all. Alone, J6
gives only |R_b| >= 4 (rank of M_b); the content of J7 is that readers below the sheet-rank sum must serve
several sheets at once ("shared delivery").

## 3. Which computations can share gates

**J8 (sharing in block-monotone circuits; proved).** Call C block-monotone if B(a + c) = B(a) u B(c) for every
gate (no whole block is ever cancelled). In a block-monotone MixColumns circuit every gate that is an ancestor
of rows of two different sheets is either pure (one block), or has support {0, 7} and is an ancestor of
exactly sheets 0 and 1, or has support {3, 7} and is an ancestor of exactly sheets 3 and 4.
*Proof.* Along a path supports only grow, so an ancestor of a sheet-j row has support inside window(j); a gate
serving sheets j and k has support inside window(j) n window(k). Among the 28 pairs of windows only
{0,1} (intersection {0, 7}) and {3,4} (intersection {3, 7}) meet in two blocks; three windows never meet in two
blocks. QED
*Corollaries (proved).* In block-monotone circuits: shared delivery (J7) happens only at blocks 0, 3, 7 and only
between sheets 0, 1 or 3, 4; hence |R_b| >= 7 for b in {1, 2, 4, 5, 6}, |R_7| >= 4 + 3 + 3 = 10 (groups
{7}, {0,1}, {3,4}), |R_0|, |R_3| >= 4. (No double service: a gate charged to two sheets must be nonzero on both
own blocks, which no window intersection allows; this is the known 80 count's mechanism.)

**J9 (exit lemma, every circuit; proved).** If g is an ancestor of a row of sheet j and c is a block of B(g)
outside window(j), every path from g to a row of sheet j contains a gate whose two operands have equal nonzero
block-c parts (an exit at c). *Proof.* Take the last vertex of the path whose support contains c. QED
Equivalently: a gate with an exit-free path to a row of sheet j and one to a row of sheet k has support inside
window(j) n window(k). (A pure-b gate likewise serves without cancellation only sheets whose window contains b.)

**Census (check, share.py, readers.py; the same 763 circuits).** All 148 block-monotone circuits share
multi-block gates only as J8 allows, and every one uses both reduction pairs ({0,7} for sheets 0,1; {3,7} for
3,4). Of the 615 non-monotone circuits, 598 have exactly four gates shared outside a window intersection: three
gates on {1, 2} serving sheets 1 and 2 and one gate on {2, 7} serving sheets 1 and 3 (the triangle of
compose/tri: the {1,2} chain and the partner [2:s 7:s], with block 2 cancelled at the exit into sheet 1); 16
have none; one has a variant ({1,2} serving 2, 3 and {1,7} serving 1, 3). The census counts gates on two or more
blocks; the review adds that in every triangle circuit one PURE block-2 gate also serves sheet 1, whose window
lacks block 2 (exit-mediated sharing by a pure gate; none in monotone circuits). Reviewer's independent sample
(every 23rd circuit, 826): 172 monotone as J8 allows; 620 of 654 non-monotone show exactly the triangle pattern,
34 none, no variant. Shared delivery (J7) has exactly the
types block 0 / sheets {0,1}, block 3 / {3,4}, block 7 / {0,1} and {3,4} (all circuits), block 7 / {1,3} and
block 1 / {1,2} (the triangle circuits), and block 2 / {2,3} once. Contrast (check): the low-waste circuit lw7
(160 gates) reaches waste 6 at block 7 by delivering four diagonal units [2:u 7:u] to all five sheets that meet
block 7, which needs block 2 cancelled for four of them; its waste at block 2 is 52.

## 4. Mechanism, in words

The eight one-block restrictions of a cheap circuit are not eight independent computations: up to a few
coincidences each is the circuit with one block's pure gates deleted and their readers short-circuited (J2,
census), and their joint behaviour is bookkeeping of those deletions (J3, J4). What constrains the combinations
is sharing between sheets. A pure block-b value can be shared without cancellation by the sheets whose windows
contain b. A multi-block value can be shared
without cancellation only inside a window intersection, and for MixColumns there are exactly two such
intersections, {0, 7} for sheets 0, 1 and {3, 7} for sheets 3, 4, both created by the reduction term: the same
vector family s_c on block 7 is needed by sheets 0, 1, 3 and 4, and only adjacent pairs of them can share its
delivery for free (J8). Everything else needs an exit (J9). In the sampled 88-97 circuits the sharing that uses
an exit is the triangle (plus one variant circuit in the main agent's sample): block-7 content delivered to sheets 1 and 3 through sheet 3's gate [2:s 7:s] and
the {1,2} chain, block 2 cancelled at the exit into sheet 1. Lowering the removal count at one block below the
window-local rank (J7) requires such cross-window delivery, and the low-waste constructions show its price
(the carrier block's waste and size).

## 5. Triage of the candidate couplings (section 3 of the user's request)

| candidate | property beyond the identity | outcome |
|---|---|---|
| sum_b D_b >= G (each gate removed once on average) | a conservation law | false in the corpus (86 < 88); with it one would still need the K_b |
| at least 8 charged gates of sheet j removed at block j | charges tied to restriction | 6-10 (mostly 8) in the six cheap circuits examined (jstats.py), false in general (lw4: 5) |
| low waste at b forces a large restricted part | single-block tradeoff | mechanism now explicit (J6-J9: shared delivery, exits); no inequality |
| joint waste at two blocks | joint universal bound | capped at 85 by constructions (J5): cannot reach 88 |
| all eight blocks together | joint bound | is averaging of the single blocks (J4; lambda_2 - lambda_0 = sum_b \|L_b\| - G) |
Each candidate was compared with the earlier counts: parity (56) uses one evaluation point, unrelated to block
restrictions; gate elimination (57; K_7 + 4 = 64) is J4(c); the 80 count uses window restrictions and controls
doubly charged gates; J8 classifies every shared gate of a block-monotone circuit, not only the doubly charged
ones, and J6-J7 add the delivery structure that the charge count does not see; the published 75 counts 3-term relations and
is order-free, as J1's quantities are (J1 depends on the value set only).

## 6. Strongest statements, conjecture, next direction

(Phase 8 continues this section in `../cancel/CANCEL.md`: Theorem K, the cancellation chase, and the girth
conjecture; the next direction below was carried out there.)

Strongest exact statements: J1-J3 (exact accounting of several restrictions of one circuit; J4 is their
eight-block sum), J6-J7 (reader identity and group-rank bound, all circuits), J8-J9 (classification of shared
gates in block-monotone circuits; cancellation needed otherwise). Limitation: J4 and J5 (the eight-block sum is
an average of single blocks; block-zeroing forms with waste bounds valid for all circuits are capped at 83 for
one block, 85 for two and 87 for four by explicit circuits; at three blocks the set {4,5,6} is not capped).

**REFUTED in phase 9 (cancel/SUPERPOSITION.md: a reduced, fully live MixColumns circuit with 66 distinct charged gates).** **Conjecture (charge form; holds on every sampled circuit; no proof mechanism yet).** In every MixColumns
circuit the distinct charged gates number at least 80: |F_0 u ... u F_7| >= 80, equivalently
sum_j (|F_j| - 10) >= sum_g (m(g) - 1)^+, with F_j = ancestors of sheet j nonzero on block j and m(g) = number of
sheets charging g. This would give L >= 80. On the reviewer's 826 sampled circuits the least value found was 82; the phase-8 review found 81 (circuits_3.txt
line 7651, also in the main stride-25 sample), so the least known value is 81.
What is known: double service needs an exit (J8, J9: a doubly charged gate must be nonzero on both own blocks,
which no window intersection allows); this is NOT a cost for the exit. The pair theorems (RECORD 15, 17) bound
P(j, j+1) (ancestors of either sheet nonzero on either own block), not the F-form, and in the F-form pairs do
gain: |F_1 u F_2| = 19 < 20 in 166 of the 826 sampled circuits, e.g. circuits_2.txt line 783 (|F_1| = |F_2| = 11,
three double charges; the slack comes from F_0 +1, F_3 +2, F_4 +1 and 5 uncharged gates). So the compensation
for exit-mediated double service is in general not inside the pair. (In circuits_2.txt line 20, with this
definition |F_j| = 11, 12, 11, 11, 13, 10, 10, 10 and |F_1 u F_2| = 20: there the pair's own over-charges cover
the three double charges, and the line refutes only the P-form principle "P(1,2) >= 20 + double charges",
21 < 23. compose/tri's F_3 = 14 used an enlarged F_3.) The rotation model with three positions does gain 2 gates
by wrap-around sharing (28 against 30; 11 double charges against 9 over-charges; SHARING.md section 1,
sharing/REPORT.md), so a proof must use a property of MixColumns' windows that the 3-ring lacks.
Missing argument: a cost for exit-mediated sharing that may be paid outside the pair, by the sheets that supply
the cancelled block's partner (sheet 3 in the triangle) or by neighbouring sheets (sheets 0, 3, 4 in line 783).

**Single best next direction.** The cost of exit-mediated sharing in its realised form, the triangle (with the
pure block-2 gate the review added): account, in the sampled triangle circuits where |F_1 u F_2| = 19, where the
missing charge reappears (the F_0, F_3, F_4 over-charges and the uncharged gates of line 783), and prove that it
must, following the cancelled block-2 component with J9 to the sheet-3 partner. Evidence: the triangle is the
dominant cross-window sharing pattern: the only one in 598 of 615 sampled non-monotone circuits (main sample,
which also contains one variant circuit) and in 620 of 654 (the reviewer's different selection from the same
corpus); a frequency, not a normal form;
pair-local accounting fails on it in both the P-form (line 20) and the F-form (line 783); the open pair lemma of
compose/tri is its first step.
