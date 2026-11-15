# H2: algebraic constructions for the AES S-box -- notes

Labels: [C] = exhaustive/proved within the stated case only; [H] = heuristic/empirical.
Notation: x in F = GF(256) (FIPS poly), K = GF(16) subfield, Q = GF(4) = {0,1,w,w^2}, w = g^85, g = 3.
N = x^17, n = N^-1, x^-1 = x^16 n. Tr_Q: GF(4)->GF(2) trace.

## 0. Umizame 29 (read in full: umizame/paper/paper.tex)
Canright all-normal tower, H = L Y^16 + R Y, D = LR + WZ(L+R)^2 (norm), Q = D^-1 (BMP 5 ANDs),
H^-1 = RQ Y^16 + QL Y. Each GF(16) product is Karatsuba over GF(4) with three rows
(L0,R0,Q0), (WL1,WR1,WQ1), (L0+WL1, R0+WR1, Q0+WQ1). Per row (a,b,c): ab from 3 early ANDs
p1..p3 = tau(r a) tau(r b) (r = 1, W, W^2), then bc, ca from 5 late ANDs (cells
e_{r,t} = (tau(ra)+tau(tb)+tau(Wc)) (tau(Wra)+tau(Wtb)+tau(c)), two sheared). 3*(3+5)+5 = 29.
The late cells are exactly the "GF(4)-norm members" of strategies/C (x-part ratio w, c-part ratio w^2).

## 1. Row problem (row_problem.py) [C, row model]
Model: a, b in GF(4) early, c in GF(4) late, independent variables (64 points). Free: affine,
p1..p3. Least number of extra products (any affine operands in a, b, c) giving bc and ca:
**5** (16 optimal spans, all need 5 c-dependent products). With c0*c1 also free: still 5 (one
span uses 4 late + 1 early). Without the p's: 6. So umizame's 5 late per row is optimal for an
isolated row; any gain must come from cross-row sharing (A28 has a 3-member class).

## 2. One-product completion of AD4 level-1 + AD5 inversion + AD4 last layer (fix1*.py) [C]
AD4 level-1 (9) + AD5 inversion (5) + AD4 last layer (13) misses exactly 1 output dimension
(as G found). All single products l*m closing it, with l, m in O = span(1, x, N, n) (17 dims)
or O2 = O + the 5 AD5 inversion products (18 dims), for all 11 AD4 files: 232-588 solutions,
**every one is a product of two functions of N** (a 6th middle AND = the AD4 structure 9|6|13).
No 9|5|14 arises this way.

## 3. Structure of the GF(4)-norm family (relax.py, gf4bil.py, enum_s*.py)
Member (A, s), A in F*, s in K*: [Tr(Ax) + Tr_K(s v)] * [Tr(wAx) + Tr_K(w^2 s v)]
= N_Q(Lam + G^2) + affine, Lam = Tr_{F/Q}(Ax), G = Tr_{K/Q}(s v)
= Lam^3 (x-junk) + G^3 (v-junk) + Tr_Q(Lam G) (bilinear, GF(4)-rank 1) + affine.
(A, s) ~ (wA, w^2 s): 1275 distinct members. v-junk depends only on the class of s mod GF(4)* (5 classes).
Target bits Tr(b x^16 v) (+ Tr(b gamma x^33) when v = n + gamma N) are traces of GF(4)-BILINEAR
forms; their bilinear parts form a 4-dim GF(4)-space T (8 GF(2) dims) with no rank-1 element.

**Pure bilinear minimum** [C, family, junk ignored]: least k with T in the GF(2)-span of k member
bilinear parts: one GF(16) product: 5; x^16 v (two copies sharing v): **10** (10200 spans S,
each containing exactly 15 members; 40 orbits under x -> a x).
Spans S of dim d >= T spanned by members: d=11: 96900 (35 members each), d=12: 200770 (75),
d=13: 97155 (155).

**10-member layers** (junk10.py) [C, relaxed model v independent, gamma = 0, the 10 members a basis
of a 10-dim S]: every one of the 40 x 243 (orbit, basis) cases has x-junk J_x = 8 (mod V_N) and
v-junk J_v = 4. Dead end at gamma = 0.

**v-junk parity** (vjunk.py) [C]: v-junk of a target combination = sum over classes of
parity_zeta * N_zeta(v). Pulled back by v = n + gamma N, the parity vectors whose junk is free
(in span(1, N, n)): gamma = 0: only {0, all-five}; gamma != 0 (15 values, 5 groups of 3): a 3-dim
space, e.g. gamma = 1: pi_1 = pi_4 and pi_2 = pi_3 (class 0 free). No nonzero junk combination
lands in any of the 30 classes achievable as the extra dimension of a 5-AND middle. So with a
5-AND middle every target's class-parity vector must be free.
Consequence for gamma = 0 (umizame): every target uses an even number of members of each class
-> +1 member per class over the bilinear count (umizame 3 x (4+1) = 15 vs Karatsuba 3 x 4 = 12).

## 4. Relaxed tower model (tower.py, tsearch.py, jsat.py, tbuild.py)
Canright all-normal tower exactly as in umizame's paper; points (L, R, v), L, R in GF(16) early,
v in GF(16) late and INDEPENDENT (4096 points). Late variable v = Q + gamma D (Q = D^-1), so
targets are the coordinates of R(v + gamma D), (v + gamma D)L (exact identities in (L, R, v) are
valid for the real circuit). Free: affine, the chosen early products, and v-quadratics g with
g(Q + gamma D) in span(1, D, BMP's 5 products) (as functions of D). Middle = BMP 5 ANDs.
Validation [C]: tbuild.py rebuilds umizame from (9 p's, BMP, 15 cells) -> aes_check OK, A = 29
(H2/umi.circ.txt). jsat (gamma 0, umizame p's, row-local members, K = 15) SAT.
Tower class parities (tparity.py): umizame rows = classes 0, 1, 2. gamma in {6, 11, 13}: row 1
free, rows 0 and 2 paired; {7, 9, 14}: row 0 free, rows 1, 2 even (paired with unused classes);
{5, 10, 15}: rows 0, 1 paired, row 2 even; {4, 8, 12}: rows 1, 2 paired, row 0 even;
{1, 2, 3}: row 2 free, rows 0, 1 even. (Only {6, 11, 13} gives "one free row + two paired rows".)

**Exact results (CaDiCaL via jsat.py; cover.c enumeration agrees on gamma 6, K 12-13):**
- umizame's 9 p's + BMP + row-local members (lam in span_GF4{a_r, b_r}, mu = c_r; 45 members):
  no last layer with K = 13 or K = 14, for every gamma in GF(16) [C, this model] (32 UNSAT runs, ~2 s each).
  So the "umizame + gamma" idea (free one row's parity) gives neither 27 nor a 9|5|14 here.
- [C] span check (normspan.py): dim(V_N + N(a_r), N(b_r) for two rows) = 8; adding the third
  row's 3 p's gives 11 > 9, so no 9-cover contains two rows' norm forms and the third row's p's.
