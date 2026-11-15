# H4: other representations of GF(2^8) inversion -- notes

Evidence labels: [C] proved or exhaustive / exact SAT within the case stated in the same line;
[P] short proof written here (also a [C] in the brief's sense, case stated); [H] heuristic or
empirical. "Construction [C]" = a circuit was built and verified; the count is exact for that
construction only, never a lower bound.

Notation: F = GF(2^8) (0x11B), K = GF(16) = {y^16 = y}, Q = GF(4) = {0, 1, w, w^2}, w = 3^85.
N = x^17 = N_{F/K}(x), N4 = x^85 = N_{F/Q}(x) = N_{K/Q}(N) = N^5, s = Frobenius x -> x^4
(generator of Gal(F/Q)), P = x^84 = s(x) s^2(x) s^3(x) (the Q-adjugate).
Data: ~/xs-campaigns/2026-11-15-study/H4/. Code: this directory.

## 0. Tools

* `h4lib.py`: symbolic circuits over F. A value is a bundle {wire: constant in F}; GF(2)-linear
  maps (Frobenius, constant multiples, basis changes) act on the constants and cost nothing;
  XOR networks are only materialised for AND operands and outputs. Towers F/K/Q/GF(2) with
  normal or polynomial basis per level; Karatsuba product per level, norms with one subfield
  product, scalar products, subfield projection; NCFF export. Validated [C]: plain tower
  inversion = 36 ANDs (9 + 9 + 18) and with a SAT-found 5-AND GF(16) inverse = 32 ANDs
  (Boyar-Peralta structure) for all 8 normal/polynomial basis combinations; both pass
  aes_check (val-tower-naive / val-tower-kinv5 .circ.txt in the data dir).
* `chm.py`: exact MC of small vectorial functions (Courtois-Hulme-Mourouzis encoding).
* `cover1.py`, `run_cover.py`: level-1 quadratic complexity of a set of quadratic forms in
  formal variables (k products, output combination free, products sorted lexicographically).
* `d_tower.py`, `d_routes.py`: the designs below, built and checked.
* `ad3_struct.py`: operand-span analysis of AND-depth-3 circuits.
* `ad3sat.py`: joint SAT for AND levels 1 and 2 of the GF(4)-norm route (truth-table exact).
* `ad3_ops.py` (operand decomposition), `ad3fix.py` (level-2 SA over a fixed level 1),
  `ad3mem.py` (level-2 SA minimising junk), `ad3walk.py` (plateau walk + exact cover of every
  junk space), `cover_exact.py` / `cover_s2.py` (exact level-1 cover tests, cover lemma, s <= 2,
  with a free space), `ad3cov.py`, `ad3drop.py`, `ad3_llay.py` / `ad3_llay2.py` / `llay2all.sh`
  (hand states to track G's llay.c), `gen_l1.py` (9-product norm covers from many tower bases),
  `ad3build.py` (levels -> NCFF), `ad3found.py` (build + aes_check + found/ with sidecar),
  `ad3night.sh` (unattended runner, QUEUE.md), `queue.sh` (appendable job queue).

## Summary
* Representation changes (polynomial, basis, GF(4)^4 vs GF(16)^2, normal/polynomial) cannot
  change any AND count [P]; only the algorithm (bracketing of x^-1 = x^16 N^4 N4^2) matters.
* The non-tower constructions tried (hybrid K-coordinates 41, GF(4)-norm via tower cofactor 42,
  pure GF(4) adjugate 64, its variant with N4 = x * P 75, Itoh-Tsujii 108; all with generic
  Karatsuba products) give 41-108 ANDs [C, constructions verified]. This is a statement about
  these constructions only, not about non-tower designs in general.
* The GF(4)-norm route is the AND-depth-3 route, and the AD3 frontier (35 = 11 | 12 | 12) is
  exactly it [C, operand spans of all 8 published A35]. Its level 3 has bilinear rank 12 [P];
  its level 2, in the member family of the published circuits, needs >= 12 [C]; level 1 needs
  >= 9 (track C) and 11 for every level 2 found. 34 at AD3: not found (~70k junk spaces exactly
  tested, all need >= 11 or more level-1 products) [H overall, C per space].

## 1. What a "representation" can and cannot change [P]

* Every choice of field representation (defining polynomial, polynomial / normal / mixed basis
  per tower level, GF(4)^4 vs GF(16)^2 coordinates) is a GF(2)-linear bijection of the 8 input
  and 8 output bits (and of intermediate subfield coordinates). Linear maps cost no AND. Hence
  for any fixed *algorithm* (sequence of products of linear forms) the AND count is the same in
  every representation; a representation only changes which algorithms are easy to write down.
  The objects that matter are basis-free: the spans of the operand forms. Confirmed on the
  builds: all 8 basis combinations give identical AND counts for every design (d_tower.py,
  d_routes.py).
* Inversion through a subfield L of F with [F:L] = d: x^-1 = adj_L(x) * N_L(x)^-1, with
  N_L(x) = x^((2^8-1)/(|L|-1)) and adj_L(x) = x^((2^8-1)/(|L|-1) - 1) = product of the d-1
  nontrivial conjugates of x over L, a form of degree d-1 over L. Only L = K (d = 2) has a
  linear cofactor (x^16). For L = Q (d = 4) the cofactor P = x^84 is an F-valued cubic; for
  L = GF(2) it is x^254 itself.
* Every factorisation of P = s(x) s^2(x) s^3(x) into two factors pairs either s(x) with s^3(x)
  (giving s(x) s^3(x) = N^4, i.e. P = x^16 N^4: the GF(16) norm comes back) or two adjacent
  conjugates (s(x) s^2(x) = (x^5)^4: then P = s(x) * s^2(x^5), a product of a linear and an
  F-valued quadratic, a full F x F multiplication). There is no third option (3 factors, the
  pairing is determined by which factor is left alone).

## 2. Designs built (all verified with aes_check; files route-*.circ.txt in the data dir)

| design | formula | stages (ANDs) | A | AD | G |
|---|---|---|---:|---:|---:|
| tower naive | x^16 * N^4 * N4^2 | 9 + (3 + 6) + 18 | 36 | 4 | 234 |
| tower, 5-AND K-inverse (BP) | x^16 * inv16(N) | 9 + 5 + 18 | 32 | 6 | 294 |
| GF(4)-norm via tower cofactor | (x^16 N^4) * N4^2 | 9 + 3 + 18 + 12 | 42 | **3** | 266 |
| GF(4)-norm, pure (no x^17) | x^5 by Q-coords; P = s(x) s^2(x^5); N4 = N_{F/K}(x^5) | 18 + 27 + 9(-2 dead) + 12 | 64 | 3 | 659 |
| GF(4)-norm, N4 = x * P | as above, N4 from a full product | | 75 | 4 | 765 |
| Itoh-Tsujii | (x^127)^2, chain x^3, x^7, x^63, x^127, Karatsuba 27 each | 4 x 27 | 108 | 4 | 1450 |
| hybrid K-coordinates | coordinate 0: x^16 n; coordinate 1: (c1(x^16) N^4) N4^2 | 9 + 5 + 3 + 9 + 9 + 6 | 41 | 6 | 411 |

All counts are constructions [C for the construction]; the generic Karatsuba F-multiplication
(27) is not optimal, but the pure-Q and Itoh-Tsujii routes are far above 30 even with the best
known GF(2^8) multiplication, so they were not refined.

Key observation: the GF(4)-norm route via the tower cofactor has AND depth 3:
level 1 = N, level 2 = {N4 = N^5, P = x^16 N^4} (both products of span(1, x, N) forms),
level 3 = P * N4^2. This is the only route here with AD 3.

## 3. The AD-3 frontier is the GF(4)-norm route [C, operand spans checked on 256 points]

All 8 published A35 AD3 circuits (NIST pin) have AND levels 11 | 12 | 12, and (`ad3_struct.py`
on aes-sbox-a35-ad3-g139-gd27): N in span(1, x, L1); every level-2 operand in span(1, x, N);
x^84 and N4 in span(1, x, L1, L2); every level-3 AND = (form in span(1, x, N, x^84, N4)) with
one operand in span(1, x^84 [+x]) and the other in span(1, N4): i.e. exactly
level 3 = P * N4^2 (12 products), level 2 = P and N4 (12 products, with x-quadratic junk
absorbed by 2 extra level-1 products), level 1 = N + 2 junk (11).
So "A at AD3" (published best 35, ours 35) is a question about this representation.

* Level 3 in the bilinear model: the map (P, m) -> P m, P in F = Q^4, m in Q, has bilinear rank
  exactly 12 [P]: write T = m0 (x) I + m1 (x) Om (slices: multiplication by 1 and by w); any
  rank decomposition groups its terms by the m-form (m0, m1 or m0+m1):
  T = m0 (x) A0 + m1 (x) A1 + (m0+m1) (x) A2, so A0 = I - A2, A1 = Om - A2 and the length is
  rk(I - A2) + rk(Om - A2) + rk(A2) >= max(16 - r, 8 + r) >= 12 (r = rk A2; the second bound
  uses rk(I - A2) + rk(Om - A2) >= rk(I - Om) = 8, since I - Om = multiplication by w^2).

### 3.1 Which factorisations fit AND depth 3 [P]
A level-3 AND multiplies two functions of degree <= 4 (each AND at most doubles the degree).
For x^-1 = u * v with v = N^a in K (a in Z/15) and u = x^(254 - 17a): deg v = 2 wt(a),
deg u = wt(254 - 17a) (binary weights). Both <= 4 exactly for a in {5, 6, 9, 10, 12}:
| a | v | u | last block |
|---|---|---|---|
| 10 | N4^2 = N^10 in Q | x^84 = x^16 N^4 | GF(4)-scalar x F (bilinear rank 12) |
| 5 | N4 in Q | x^169 = x^33 N^8 | GF(4)-scalar x F (12) |
| 6, 9, 12 | N^6, N^9, N^12 in K | x^152, x^101, x^50 | GF(16)-scalar x F (two GF(16) products) |
For a = 10 the member bilinear part pairs x N^4 (class 69, the target) with its Gal(K/Q)
partner x N (class 9), which collapses to an x-quadratic (absorbable by level 1). For a = 6, 12
the partner of x N^8 / x N^2 is x N^2 / x N^8 (classes 35 / 137, cubic, not absorbable); for
a = 5 the F-operand x^33 is itself quadratic. So a = 10 (the published A35 structure) is the
natural AD3 route; the others were not built.


## 4. Levels 1 + 2 of the AD3 route

Targets of level 2: P (8 coordinates; equivalently P^16 = x N^4, Frobenius is free) and N4 (2).
Function-level facts [P, distinct cyclotomic classes are linearly independent as functions]:
products of span(1, x, N) forms split into x*x (classes 3, 5, 9, 17; class 17 = V_N = N, free),
x*N (classes 9, 35, 69, 137; the class-9 part {Tr(b x N)} = {Tr(b x^18)} collapses to
x-quadratics, i.e. it is x-quadratic junk), N*N (classes 51 = N^3 and 85 = N4). P lies in class
69 (P^16 = x N^4 = x^69).

### 4.1 Plain SAT is too slow
* `ad3sat.py` (joint L1 + L2, exact): (11, 12) not solved in 25 min (the published A35 is a
  solution), so negative runs would mean nothing; abandoned. `ad3j.py` (L2 + J free junk forms)
  and `ad3sat.py --fix-l1` (L2 over the A35 level 1, k2 = 12, known SAT): not solved in 100 s.
* Formal-variable relaxation (`run_cover.py padj`: x, N independent variables, all x- and
  N-quadratic junk and the class-9 collapse free): P alone needs >= 6 level-2 products
  (k = 5 UNSAT in 9 s [C, that relaxation]); k = 8 SAT; k = 6, 7 open (100 s). With N4 as a
  target and N-junk not free (padj_n4) k = 8..10 not solved in 30 s each.
* Track G's llay.c (exact coordinate descent) on L1 + L2 from scratch: stuck at deficit 9 in 90 s
  (the needle problem G describes).

### 4.2 The member family (structure of the published A35) [C, checked on 256 points]
`ad3_ops.py` on the A35 level 2: 9 of the 12 ANDs are GF(4)-norm members
z0 * z1, z = Tr_{F/Q}(lam x) + gamma(N) (x-parts of the two operands in ratio w or w^2) with ONE
fixed Q-valued N-functional gamma (N-parts in a 2-dim space); the other 3 are pure N-products
(N4 = N^5: its two forms need exactly 3 products as forms in N [C, run_cover nkq: k=2 UNSAT,
k=3 SAT]). Of the 210 ordered pairs gamma = (g0, g1) of N-forms, exactly 15 make the members
able to produce P at all (`T in span(all members, all N-products) + x-quadratics`); they are the
Q-linear functionals Tr_{K/Q}(mu N), mu in K*, one orbit under x -> a x [C].
Bilinear part of a member: Tr(lam nu x N^4) + Tr(lam nu^4 x N) [P]: one P-direction plus a
class-9 junk form; plus x-junk N(Tr_{F/Q}(lam x)) (classes 3, 9) and N-junk N(gamma) (class 51).

### 4.3 Accounting in the member family [P unless marked]
With members + N-products at level 2 (k + p ANDs) and level 3 = P * m (12):
* members never contribute N4 (their N-junk N(gamma) is class 51, N4 is class 85), so N4 comes
  only from N-products: p >= 3 [C].
* the x-junk of a combination is the sum of the members' x-junks
  (C(lam) + N(Tr_{F/Q}(lam x)), classes 3 and 9); with k members and 8 target directions,
  J = rank(x-junks) - (number of kernel combinations whose junk is pure x-quadratic).
* level 1 must cover V_N + U (U = the junk, dim J): l1 >= max(9, 4 + J).
* section 4.4: k + p >= 12 [C]. So total = l1 + (k + p) + 12 >= l1 + 24; 34 needs
  l1 = 10 with k + p = 12, i.e. (k, p) = (9, 3) or (8, 4), or l1 = 9 with k + p = 13.

### 4.4 Level 2 needs >= 12 ANDs in the member family [C]
Family: level-2 ANDs are members z0 z1, z = Tr_{F/Q}(lam x) + gamma(N) (gamma one of the 15 good
Q-functionals of N; 5 classes up to Q* scaling, N(g gamma) = N(gamma)), or products of two
N-forms. Claim: k + p >= 12.
* k >= 8: modulo x-quadratics, N-quadratics and span(1, x, N) the 8 P-directions come only from
  the members' bilinear parts.
* N4 needs p >= 3 (its two forms need 3 rank-2 N-forms [C]); members never contribute class 85.
* If k = 8 the members' P-parts are a basis, so as the target runs over the P-directions its
  member set S runs over ALL nonempty subsets; the N-junk sum_{j in S} N(gamma_j) must be
  cancelled by the N-products, so every N(gamma_j) lies in their span. Exhaustive [C]: of the
  C(35,3) triples of the 35 distinct N-products (mod span(1, x, N)) exactly 10 span N4, and none
  of them contains N(gamma) for any of the 15 good gamma (sums of 2, 3 or 5 class values do
  occur, but single ones are needed). Hence k = 8 forces p >= 4.
So l2 >= 12 and an AD3 circuit of this shape has >= l1 + 12 + 12 ANDs; the published 35 has
l1 = 11. A 34 needs l1 = 10 with (k, p) = (9, 3) or (8, 4). The k = 8, p = 3 walk
(`ad3walk.py --drop 1`) indeed never reached a feasible state in 1.37 M steps (consistent).

### 4.5 Searches (all [H] unless marked; results only constructive)
* `ad3fix.py` (SA over members + N-products over a FIXED level 1, score = exact deficit):
  - A35 level 1 (11), k = 9, p = 3: deficit 0 found in < 30 s (re-finds the A35 accounting); built
    with `ad3build.py` (my level 2 + Karatsuba level 3): ad3val.circ.txt, aes_check OK,
    A 35 AD 3 (G 516, XORs not optimised) [C for the construction]. Validates the AD3 pipeline.
  - A35 level 1, k = 8, p = 3 (would be 34): best deficit 1 in 5 x 60 s; track G's llay (exact
    re-choice over all products of span(x, N), general products allowed) from that state: stays
    at deficit 1 (90 s). A35 level 1, k = 9, p = 2: best deficit 1.
  - AD4 (a28-ad4-g131) level 1 (9), k = 9, p = 3 (would be 33): deficit 3-5.
* `ad3mem.py` (SA over members + N-products minimising the junk J, then exact level-1 cover of
  V_N + U with `cover_exact.py`, cover lemma, l1 - dim <= 1): single gamma, k = 9, p = 3:
  J = 5 reached quickly (dim V_N + U = 9) but cover(9) and cover(10) both impossible for the
  states checked [C for those U].

* AD5 (a28-ad5-g124) level 1 (10), k = 9, p = 3: deficit 3 in all 5 restarts (60 s each).
* Screen over generated 9-product level-1 covers (`gen_l1.py`: Karatsuba norm formulas in 216
  random tower bases -> 200 distinct junk spaces W): k = 10, p = 3 (would be 34): deficits 3-5
  on the first 14 covers (15 s each) -> stopped; K-route level-1 junk spaces do not fit the
  member junk. [H]
* The level 2 found over the A35 level 1 (ad3fix_val.jsonl line 2) needs only J = 4 junk
  dimensions (dim V_N + U = 8), and every single A35 level-1 product is redundant for the level-2
  junk (deficit stays 0 when one is dropped with N kept free) -- but N itself needs all 11 of
  them. Exact cover of V_N + U (`ad3cov.py`, `cover_s2.py`: cover lemma with bucket pruning):
  9 products impossible (s = 1), 10 impossible (s = 2: r0 = 0, bucket sizes <= 4, only 9 planes
  pass the size test, none covers) [C for this U]. So this level 2 needs 11 level-1 products ->
  35, like the A35.
* Pool over the A35 level 1 (`ad3fix.py --all`, 40 restarts x 30 s, pool_a35.jsonl): many
  distinct zero-deficit level 2s (9 members + 3 N-products; the members use gamma, w gamma,
  w^2 gamma, i.e. effectively one gamma). ALL of them need the same junk space: V_N + U is one
  fixed 8-dim space (J = 4) [C, computed for every solution], and that space needs 11 level-1
  products (9 and 10 impossible, exact) [C]. So with the A35 level 1, member level 2s give
  exactly 35; a 34 needs a level 2 whose junk space is not inside the A35 level-1 span.
* `ad3walk.py` (plateau walk over member states with J <= jmax, exact cover test of every new
  junk space; no level 1 fixed): from a pool state, k = 9, p = 3, jmax 5, 80 s: 613 distinct junk
  spaces, all J = 5, d = 9, none coverable by <= 10 products [C for each of those spaces].

* Both levels movable, general products (track G's llay.c with 10 stage-1 slots, N required,
  + 12 layer slots over span(x, N), exact slot re-choice; `ad3_llay2.py`, `llay2all.sh`):
  started from pool solutions with one A35 level-1 product dropped (would be 34): best deficit 1
  in every 120 s run (validation: the undropped state is read back at deficit 0). [H]
* `ad3walk.py` from a pool state with jmax 4 (k = 9, p = 3), 600 s: 841k steps, 19.6k accepted
  moves, but only ONE junk space V_N + U ever (J = 4, d = 8; the A35 one, needs 11). The J = 4
  plateau around the A35 structure is rigid. [H]
* `ad3walk.py` jmax 6 (k = 9, p = 3), 600 s: 8884 distinct junk spaces (6 with J = 5, d = 9;
  8878 with J = 6, d = 10); none is covered by <= 10 level-1 products [C for each space,
  cover lemma]. So no 34 = 10 + 9 + 3 + 12 among them.
* `ad3walk.py` k = 10 (one member added), jmax 6, target l1 = 9 (would be 9 + 10 + 3 + 12 = 34),
  600 s: 47916 distinct junk spaces (33 with d = 9, 47883 with d = 10), none covered by 9
  products [C for each]; J never dropped below 5.

* `ad3walk.py` k = 10, jmax 5, target l1 = 9, 600 s: 6018 junk spaces (4 with d = 8, 6014 with
  d = 9), none covered by 9 products [C for each].

* (k, p) = (8, 4): `ad3walk.py --drop 1 --addn 1` from pool states never reached a feasible state
  (the descent fails); `ad3mem.py --k 8 --p 4` finds feasible states quickly (J = 5 or 6) but
  for the 4 checked, V_N + U needs > 10 level-1 products [C each] (ad3mem84.jsonl).
* Night-runner test (`ad3night.sh`, 2 h on CPU 16 from 03:20 UTC, night_test/): see the end of
  this file.

## 5. Exact sub-block minima (each only for the stated block and model)
| block | model | result | tool |
|---|---|---|---|
| N -> N4 = N^5 (GF(16) -> GF(4)) | any depth (CHM SAT) | MC = 3 (k=2 UNSAT, k=3 SAT) [C] | chm.py via blocks.small_circuit |
| same | one level, forms in N | 3 (k=2 UNSAT) [C] | run_cover nkq |
| (P, m) -> P m, P in F, m in GF(4) | bilinear | rank 12 [P, section 3] | - |
| same | one level, formal P, m, junk must cancel | k = 11 and 12 not decided in 300-900 s | run_cover qscal |
| (x, n) -> x n, x in F, n in GF(16) | one level, formal | k = 11, 12 not decided in 300 s | run_cover kscal |
| P^16 = x N^4 alone, x and N formal, all x-/N-quadratic junk and class 9 free | one level | >= 6 (k = 5 UNSAT 9 s) [C], 8 SAT | run_cover padj |
| GF(16) inversion | any depth | 5 (known, track C) | - |

## 6. Why no other representation helps at 27-30 (accounting, [H] unless marked)
* Every K-route circuit (published 28s) and the Q-route evaluate the same trilinear quantity
  x^-1 = x^16 * N^4 * N4^2 (x-linear, N-linear, N4-linear), differing only in the bracketing:
  K-route x^16 * (N^4 N4^2) = x^16 * n: the N (x) N4 part is packed into n (GF(16) inverse,
  5 ANDs in total, of which N4 alone needs 3 [C]) and the last layer is GF(16)-scalar x F
  (13 GF(4)-norm members in the A28s). Q-route (x^16 N^4) * N4^2 = P * m: the x (x) N part is
  packed into P (8 dims, 9 members + junk at level 2) and the last layer is GF(4)-scalar x F
  (12, bilinear rank 12 [P]). Packing N (x) N4 is much cheaper (4 K-valued dims for ~2 extra
  ANDs) than packing x (x) N (8 F-valued dims for ~9), so the Q-route loses ~7 ANDs and wins one
  AND level. The routes through GF(2) (Itoh-Tsujii, x^254 as a product of conjugates) and the
  pure GF(4) adjugate need general F x F products (bilinear rank of GF(2^8) multiplication >= 15
  trivially, ~22-24 known) and are far above (constructions 108 and 64).
* Output splitting (some coordinates via the K-route, others via the Q-route) cannot share the
  expensive parts: each output functional is Tr_K(n L_b(x)) (K-route) or Tr_Q(m L'_b(P))
  (Q-route); the hybrid built (one K-coordinate each way) costs 41 [C construction].
* Hence the constructions and the accounting here give no candidate below the K-route's 28 (no
  general claim); the value of the GF(4)-norm route is at AND depth 3, where the frontier sits (35).

## 7. For H2 (and others): the 200 generated level-1 covers
`~/xs-campaigns/2026-11-15-study/H4/covers200.json`: 200 distinct 9-product level-1 sets, each
spanning V_N (N = x^17, checked) plus a 5-dim junk space W, from Karatsuba norm formulas in 216
random tower bases (`gen_l1.py`), deduplicated by W. Per cover: `ops_xmasks` (operand masks
over the input-byte bits, bit j = coefficient of bit j of x), `ops_tables_hex` (truth tables),
tower kinds and generators. The same sets as individual files: H4/l1/l1_NNN.json (`l1ops`).
Caveat: many are images of each other under x -> a x^(2^i) (not reduced by symmetry).

## 8. Night-runner test (ad3night.sh, CPU 16, 03:20-05:21 UTC, night_test/walks.log)
Each walk 30 min; every new junk space V_N + U tested exactly (cover lemma) [C per space]:
| walk | (k, p), target l1 (total 34) | distinct junk spaces | (J, d) | coverable |
|---|---|---|---|---|
| 1 | (9, 3), l1 <= 10 | 32568 | 57 x (5, 9), 32511 x (6, 10) | none |
| 2 | (8, 4), l1 <= 10 (start: ad3mem84 state) | 32604 | 27 x (5, 9), 32577 x (6, 10) | none |
| 3 | (10, 3), l1 <= 9 | 175627 | 126 x (5, 9), 175501 x (6, 10) | none |
| 4 | (9, 3), l1 <= 10 | (ends 05:21, see walks.log) | | |
Total over the day: ~320k distinct member-family junk spaces, none admits a 34 at AD3. [H] that
34 is absent from this family; the overnight spec in QUEUE.md is accordingly low priority.
