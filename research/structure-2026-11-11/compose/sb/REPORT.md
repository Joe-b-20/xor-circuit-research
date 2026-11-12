# The supply-benefit inequality: SB fails trivially, SB' and what is proved

Delegated investigation, phase 4 (2026-11-12), separate model instance (Opus, high effort); saved by the
main agent from its final message, lightly condensed. Review status in RECORD 19. Uses the corrected
L_near (exits in time order; each value computed from labels of entries placed before its exit and
earlier replacement values). No SAT. The scripts verify explicit circuits (`mcheck.py`) and list
signals of fixed mirrors (`tscan.py`); `mcheck.py` also computes L_near by a small exact search on the given circuit (disclosed in
`../../joint/FINITE_AUDIT.md`; the values used have one-line hand bounds there). Files: mcheck.py, dangle2.txt, tight_o2.txt, tscan.py, t1-t3.txt.

## 1. SB as stated is false (checked)

Entries cost nothing in near1, so the near side can pile up entries that feed no target.
Construction (`dangle2.txt`, MC_2): first sheet with near1 = 10: pure x = w0+w1, y = w2+w3, z = w1+w2
(the three exports); F3 = x+w2, F2 = x+w3, F1 = y+w0, F0 = y+w1 (7 first gates). Dangling stack:
d1 = w0+u0, d2 = d1+u1, d3 = d2+u2, then the exit B3 = d3+w0 = u0+u1+u2 = E_3(w^2). Rest: four entries
A_i = F_i + p_i after the exit; the far side builds p0..p3 and B0..B2. `mcheck.py`: reduced, all required
vectors, valid export span. Cost 25, near1 = 10, e1 = 7, one exit with L_near = 2, so beta = 1 >
near1 - 10 = 0: SB fails at every length (the near part is one sheet). Not a real saving: the receiver pays
3 entries plus 1 exit for a value it could compute in 2 gates. Lemma 2.1 hides this because it charges
every entry as an export of MC_(l-1).

## 2. Repair (proved, every l)

tau_min(Lambda) = least number of labels whose span contains Even(w^2) + 0 (>= 3); sigma = e1 - tau_min.
**Lemma 2.1'.** far1 >= M_(l-1) - beta + sigma, beta = L_near(S) - |S|.
*Proof.* Replace every exit in time order by gates computing its value from earlier labels and earlier
replacement values: |P'| <= |P| - |S| + L_near(S), and P' contains R^2..R^l and every label signal. Take
tau_min label signals spanning Even(w^2) + 0 as exports: |P'| + tau_min >= M_(l-1). Add e1. QED
**SB':** near1 - 10 >= beta - sigma.
If SB' holds for one sheet, every reduced MC_l circuit has cost >= 10 + M_(l-1), giving M_l = 10 l by the
induction of TWOSIDED section 5. A circuit below 10 + M_(l-1) needs near1 - 10 < beta - sigma, and Lemma
2.1' must then be nearly tight.

## 3. All labels even (proved, every l, every e1)

**Theorem S1.** If every label lies in Even(w^2) + 0, then beta <= 1; hence SB' holds for e1 >= 4, and
Theorem 4.1 covers e1 = 3.
*Proof.* The span of the labels available at any moment has dimension <= 3. In dimension 1 no exit is
possible; in dimension 2 every nonzero vector is a label or a sum of two labels; in dimension 3, with at
least 4 distinct available values every nonzero vector is one of them or a sum of two; with exactly 3 (a
basis b1, b2, b3) only b1 + b2 + b3 costs 2, and once it is computed (reusable) or a fourth value arrives,
every later vector costs at most 1. So beta <= 1. For e1 >= 4, sigma >= 1 and near1 >= 10 by (F1). QED
*What matters:* only that the labels saturate a 3-dimensional space.

## 4. e1 = 4: SB' holds except one residual case (proved)

**Lemma Q.** For four independent labels, beta <= 2.
*Proof.* At the first request of weight >= 3, compute one pair lambda_a + lambda_b from it; later compute
the complementary pair lambda_c + lambda_d using only labels already present. With these two pairs every
vector costs at most one more gate. QED
Four labels spanning a space containing Even(w^2) + 0 either span exactly it (S1 applies) or are
independent. o = number of labels outside Even(w^2) + 0; tau_min = 3 if o = 1, 4 if o >= 2. t = clean
entries, K_c = |T*| + t.
Facts: (a) tau = 3 implies f1 >= 7 (the three exports must be pure, even, independent; a 6-gate projection
has only two even signals, tenth-gate Step 4); (b) in a tight T* (gate count = number of prescribed
distinct values) no adjoint is 0 (else some summation order has a zero gate, or a chain of single readers
ends at a node whose contributions sum to 0); (c) generalised Lemma B (reviewed); (d) the (Y)/Lemma R
rigidity arguments: entries cannot be stacked unless the rest-sum is a T* value or empty; (e) if h1 = 0
every fibre is a tree of entries, exits are path sums, and beta <= number of entries attached to entries
(prefix sums along each path, all of whose labels precede the exit).
**Theorem S2.** SB' holds for e1 = 4 in every case except near1 = 11, o >= 2, beta = 2.
*Proof.* o = 1 (sigma = 1, need beta <= near1 - 9): if t = 3 the odd entry is unclean; at near1 = 10,
|L1| = 11, K_c = 10: the rigid 3-entry form (Lemma R) with h1 = 0; the dangling entry gives paths of length
at most 2, beta = 0. If t = 4, Lemma B gives a zero zeta and |T*| >= 7; near1 = 10 forces |T*| = 7, tight,
contradicting (b). For near1 >= 11, Lemma Q. o = 2 (sigma = 0): at near1 = 10, (a) gives f1 = 7, h1 = 0,
|T*| = 7 tight with zetas A, A, B, C (A, B, C independent); by (d) the only possible stack is the odd pair,
so exits are lambda_1 + lambda_2 and beta = 0; for near1 >= 12, Lemma Q. o >= 3 (sigma = 0): |T*| >= 8
forces near1 >= 11; at near1 = 11, tau = 3, f1 + h1 = 8, T* rigid; if h1 = 0 fibres are {r, r + pi}, no
exit; for near1 >= 12, Lemma Q. QED
**Residual case Omega (open):** near1 = 11, o >= 2, beta = 2. Omega1: o >= 3, f1 = 7, h1 = 1, tau = 3,
|T*| = 8 rigid; exit values among the cross sums delta, delta + lambda, delta + lambda', delta + lambda +
lambda' through h; beta = 2 needs essentially delta = lambda_1 + .. + lambda_4. Omega2: o = 2 with either
tau = 4, f1 = 6, h1 = 1 (|T*| = 7 tight) or tau = 3, f1 + h1 = 8.
Evidence on Omega2 (checks): `tight_o2.txt` is a verified near side in the first form with near1 = 11,
o = 2; its only usable exit is lambda_1 + lambda_2 (beta = 0). `tscan.py` lists every primal signal over
all summation orders of one fixed tight T* and every pair with equal w^1-part; on three hand-chosen tight
o = 2 mirrors the largest label difference was z1 + z2 (beta = 0). Conjecture: in a tight T* the formal part
is a function of the w^1-part up to the stacked odd pair, which would close Omega2.

## 5. Several exits jointly

L_near is one joint computation; Lemma 2.1', S1, S2 and Q bound the joint beta; no per-exit charges are
added. Mirror identity (proved count): clean the near circuit with respect to its targets and its m exit
gates, exits included; its mirror T** has inputs W0..W3, X1..Xm and contains E_c(W) and
zeta_j + sum_s delta^s_j X_s; its size is the number of kept non-entry near gates plus 2m (each exit adds
exactly two summation gates). Used only as a count it is a relaxation and not sharp (with three even
labels it would allow a two-label exit that Lemma R forbids).

## 6. For l = 3

A 29 needs near1 - 10 < beta - sigma. (G2) with e1 = b = 4 is excluded: Proposition H gives c = 0, so
h1 = 0 and near1 = a + tau = 10, and Theorem S2 gives cost >= 30. Any 29 with e1 = 4 lies in Omega with
beta = 2 exactly, and its far side must reach far1 = 18 = M_2 - 2 (Lemma 2.1' with equality: an optimal
MC_2 circuit exporting the four labels in which the exit value costs 3 gates honestly). None found; the
natural one with units on w^2 receiving 1111 is at least 19 unless it passes a saving on across cut 2.
Still open: (G1) and (G2) with e1 >= 5 and some odd label, and Omega.

## 7. Every length, and the ring

Every l: Lemma 2.1', SB' => M_l = 10 l, Theorem S1, Lemma Q, Theorem S2 (one sheet; "odd" = outside
Even(w^2) + 0), the mirror identity. Specific to l = 3: only the use of Proposition H in section 6. Q_3
ring: none apply; problem (N) and (F1) rest on the export obligation at an open end, and in a ring cut the
far arc's last required vectors involve the cut group, so honest replacement gives no MC_(l-1) circuit.
