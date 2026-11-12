# What survives when the open end is removed (rings, and the hypotheses MixColumns would need)

Delegated investigation, phase 4 (2026-11-12), separate model instance (Opus, medium effort); saved by the
main agent from its final message, lightly condensed. Machine work, NOT independently reviewed. Scripts
(checks, no search): `ring_cuts.py` (transposes a recorded circuit in both summation orders, splits the
cost at every arc cut, reports exits and label counts), `label_types.py` (labels at single-group cuts by
their parts on the two neighbouring groups), `run_all.sh`.

**Headline.** The open-chain theory does not carry over to rings as it stands. Lemma 2.1 (honest
replacement) survives unchanged; Lemma R, Theorem 4.1 and type-independent additivity of exit-free cuts do
not, and the reason is structural, not exits alone.

## 1. Split, honest replacement, and what fails

Setting: RQ_m = mirror of Q_m, a reduced circuit T on w^0..w^(m-1) (indices mod m) containing
R^k_i = E_i(w^k) + p_i(w^(k+1)); no exports; cost |T| (transposition preserves the gate count; checked on
every recorded circuit). Cut out G = w^k (omega = part on w^k); x = w^(k+1), y = w^(k-1).
- **1.1 Split (identity).** |T| = near + far, near := f + h, far := |P| + e (TWOSIDED section 0 with
  tau = 0).
- **1.2 Near side (proved).** f >= 8 (omega takes the eight distinct non-unit values E_i(w^k) and
  p_i(w^k)). The labels span V containing W := Even(x) + F_2^4(y), dimension 7 for m >= 3, so e >= 7 and
  |L_k| = f + h + e >= 15 (chain: near1 >= 10, |L1| >= 10). The export obligation is replaced by four
  prescribed even vectors inside the near side plus a second label interface at y. For an arc of r groups
  the near side is the 4E object with prescribed vectors p_i(w^k): N^p_r >= N_r and N^p_r >= M_r - 3.
- **1.3 Far side (proved).** Without exits P is a "double-label" chain DL_l on the l = m - r far groups
  (labels spanning Even(first far group) + F_2^4(last far group), cost |P| + e). Projecting out the last
  far group gives an MC_(l-1) circuit with at most e - 4 exports, so DL_l >= M_(l-1) + 4 (l >= 2),
  DL_1 >= 4. An exit-free arc cut gives only |T| >= M_r + M_(m-r-1) + 1 (about 10m - 9).
- **1.4 Honest replacement for rings (proved; same proof as Lemma 2.1, which uses neither the export
  boundary nor the closed end).** far >= DL - beta, beta = L(S) - |S|. New: if every exit value is
  supported on a single group, computing them honestly from that group's units costs at most |S| + 2 per
  group (helpers u0+u1 and u2+u3 put every vector of F_2^4 within one gate of units and helpers), so
  beta <= 2 per receiving group, whatever the labels.
- **1.5 What fails.**
  - Lemma R needs the export boundary (the tight count |L1| = 10 with D1 = 3 = dim Even, and the rigid
    7-gate mirror). In the ring the least |L_k| (nu) satisfies only 15 <= nu <= 16 (16 observed in the
    recorded Q_4, Q_5, Q_8); the "rigid" form f = 8, e = 7 is not known to exist and occurs in no recorded
    circuit. "Near at its minimum implies no exit" is false: in Q_3 groups 0 and 1 have f = 8, h = 0 and
    one exit each (check); the supplier pays through extra entries (e = 9-10), booked to the far side.
  - Theorem 4.1 needs both ends (3-dimensional label space: an exit gains at most 1; far value M_(l-1)). A
    cheapest-kind ring group (e = 7 = dim W) can have an exit equal to a sum of up to 7 labels (beta <= 5
    per exit), and an exit forces no supplier charge (with h = 0 one fibre with two entries suffices).
  - Type-independent additivity fails at m = 4 (explicit checked objects): single group: near can be 8
    (Q_3 groups are valid near instances) and DL_3 <= 30 (far part of group 0 in q4_40): 38 < 40; arcs of
    2: N^p_2 <= 19 (Q_3) and DL_2 <= 20 (Q_4): 39; arcs of 3: 29 (Q_4) + DL_1 <= 7 (Q_3): 36. In the chain,
    Proposition 1 sums to the truth; in the ring the label interface must be carried as a variable even
    when there are no exits.
  - No ring Theorem 4.1 for m >= 4 follows from these ingredients.

## 2. Triangles: Q_3 versus m >= 4

- **2.1 Where an exit lands (proved, elementary).** If every mirror gate lies in a window {j, j+1}
  ("window-local"), an exit across group k sums signals of {k-1, k} and {k, k+1}, so its value lies on
  {k-1, k+1}. For m >= 4 that is no window: the exit lands on one neighbour, gain at most 2 per side (1.4).
  For m = 3 it is the window of R^(k+1): an exit can hand the far side a two-group vector inside one of its
  required windows. Checks: all 4 exits of Q_3 (both orders) have values on both neighbours (honest cost
  3-5 labels or more); Q_3 has no exits across its 2-group arc cuts; q4_40, walk_q4_40, q5_50,
  walk_q5_50, q6_60, q8_80 are window-local in the mirror with no exit across any arc cut, either order.
- **2.2 A theorem for triangle-free rings would need:** (T1) control of gates outside every window
  ("the long way round"; excluded only by hypothesis so far); (T2) control of exits whose value is not the
  sum of two far signals (primal Lemma II.7 assumes these away: window-local and exits sums of two
  block-local signals give 10m); (T3) a coupled near/far statement or a summation rule needing no end
  (1.5: needed even without exits). Only II.7 (restricted class) exists; the mirror-exit class and the
  primal block-monotone class differ (FRAMEWORK section 2).
- **2.3 Extra hypotheses for MixColumns:** (a) block 7: a unit of primal block 7 feeds sheets 7, 0, 1, 3, 4,
  so its mirror vector is supported on up to five groups, giving a 5-group window and many more
  triangles than the four primal ones of RECORD 9; 2.1 fails inside it (derived from RECORD 7's matrix
  description, not machine-checked); (b) groups 1, 3, 4 get a third prescribed omega-family and a third
  label interface; (c) the diagonal obligations of J_01 (RECORD 17) tie two groups, so labels cannot split
  into pure x and pure y, forcing mixed labels and mixed exits; (d) the cross-window triangle {1,2,7}
  (77 % of the kste corpus) needs its own interface lemma of the Q_3 kind. None follows from a
  triangle-free ring theorem.
- **2.4 Interface-type pattern (observed only).** In q4_40 and q5_50 every label at every single-group cut
  is pure (3 pure even labels on x, 4 pure labels on y); in all 9 cuts f = 11 - o_y (o_y = number of odd
  y-labels, observed 1 or 2), the extra first gates carrying even helper vectors (1111, 0101, 1010).
  Suggests a ring version of Lemma B (near cost depends on label parity type); unproved, and cannot be
  linear down to o_y = 4.

## 3. Checks on recorded circuits

| Circuit | Cut | f | e | h | exits | near / far |
|---|---|---|---|---|---|---|
| Q_3 28 | single groups | 8 | 9-10 | 0, 0, 1 | 1, 1, 2 | 8-9 / 19-20 |
| Q_3 28 | 2-group arcs | 19-21 | 6-8 | 0-1 | 0 | 19-21 / 7-9 |
| Q_4 40 (both files) | single groups | 9-10 | 7 | 0 | 0 | 9-10 / 30-31 |
| Q_4 40 (both files) | arcs of 2 / 3 | | | | 0 | 19-20 / 20-21 and 29-30 / 10-11 |
Q_3: label rank 8 (whole far space), labels mixed, every exit lands on both neighbours. Q_4: label rank 7,
labels pure on x and on y. Q_5, Q_6, Q_8 (10m): as Q_4, no exits across any cut.

## 4. Assessment and proposed formulations (programmes)

The open-chain proof depends on its open end twice: the export boundary makes the supplier rigid (Lemma
R), the closed end gives the receiver a known value M_(l-1). Neither exists in a ring; only Lemma 2.1, the
exact split, the projection bounds and the reduction to 4E-type objects carry over. So the cut theory as
it stands is chain theory, not general theory.
- **(A) Interface-typed values.** For each cut, least near and far costs nu(tau), phi(tau) for a given
  label interface type tau (purity on x and y, odd counts, mixedness); exit-free statement
  min_tau [nu(tau) + phi(tau)] >= 10m; exits paid by 1.4 plus a supplier lemma per type. 2.4 is a first
  data point; a two-sided statement from the start.
- **(B) End-free discharging.** Use Theorem 7.1 (every sheet charged 10, all circuits, no end) and
  G = 10m + over + unch - excess; prove excess <= over + unch by local rules around each double-charged
  gate; the chain lemmas (Lemma R / Corollary R: supplier pays 1; Lemma B: 2 with odd labels) become local
  rules, and triangle-freeness (2.1) is what makes the rules local. Q_3 (28 = 30 + 9 - 11) is where a local
  rule must fail. Recommended as the main line for rings and MixColumns (no base case to lose).

**Statuses.** Proved, unreviewed: 1.1-1.4, 2.1, the inequalities in 1.5. Checks: section 3, the Q_3
statement in 1.5. Observed: 2.4. Open: nu (15 or 16), N^p_2 (17-19), DL_l, all of section 4.
