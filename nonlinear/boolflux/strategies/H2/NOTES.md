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

## 5. Exact dense-subspace search for K-member layers (gen13.c, d13prep.py, vd13.py) -- the main tool
Reformulation [P]: K members X with T_full in span(X) (mod free) <=> the images of X in V/T_full lie
in a (K-8)-dim subspace W' and the preimages have rank K. gen13 finds every (K-8)-dim W' containing
>= K member images: seeds = "quadrangles" img1+img2 = img3+img4 (pair-sum hashing); every K-set with
>= 9 distinct images (K = 13) has C(9,2) = 36 > 31 pair sums in a 5-dim space, so it contains one;
then one dimension at a time, keeping only extensions with weight >= w + ceil((K - w)/(2^{D-k} - 1))
(the 2^{D-k}-1 subspaces between B_k and W' partition W' \ B_k, so the best one reaches it). vd13.py
then checks rank (targets covered) for every candidate, minimises, builds and aes_checks.
Member images mod T_full coincide only in 2-4 pairs (never 0), so every 13-member layer has >= 9
distinct images: **gen13 is exhaustive for K = 13** in the relaxed tower model with the stated E,
gamma and the BMP middle, over ALL 1275 GF(4)-norm members.
Validation [C]: E = A28-AD5 level-1 (10 products), gamma' = 14 (real g^17 maps to tower index 14 by
gmap.py; a28tower.py identifies all 13 published members and checks the cover): 30 s, 7785 candidate
W', 97 distinct covering 13-member layers (the published one among them). Two built: found/
h2-ad5-g14-s2-a28.circ.txt, h2-ad5-g14-s9-a28.circ.txt, aes_check OK, A = 28, AD 6 (G ~ 510-530,
naive XOR chains; these are 10|5|13, i.e. NOT a new AND structure, but 97 alternative last layers).
(An earlier d13.c variant restricted to bilinear rank 13 had a bug: one member per image point; superseded.)
CaDiCaL (jsat.py) on the same problem with all 1275 members did not finish in 15 min (even SAT
instances), so the SAT route is only usable for small candidate sets.

### 5.1 Results with gen13 (relaxed tower model, BMP middle, all 1275 members, single gamma)
- **E = umizame's 9 products: no 13-member layer for any of the 16 gamma** [C, this model]
  (~25 s per gamma; 0-1 candidate subspaces, none of rank 13). So 9 + 5 + 13 = 27 is impossible over
  umizame's stage 1 with any single-gamma GF(4)-norm layer. (gamma 6/11/13 give identical counts,
  as do 1/2/3, 4/8/12, 5/10/15, 7/9/14: a symmetry of the umizame cover.)
- Note [C, vjunk.py]: the extra middle dimension of any 5-AND middle (G's 30 classes) never absorbs
  member v-junk, so for this member family the choice of 5-AND middle is irrelevant (BMP is WLOG).

### 5.2 Real-model version (rprep.py, rvd.py) and further runs
rprep.py builds the same search directly on the 256 inputs (free = span(1, x, early ANDs, middle ANDs);
candidates = members on v_g = n + g N for one or SEVERAL gammas g, optionally pure bilinear
products tau(lam) tau(mu(v)) ('bil'); middle = BMP or a published middle 'midfile:'). It is at
least as general as the relaxed model (it can use n N = 1). Validation [C]: over AD5's prefix,
gamma' = 14 it gives exactly the same 7785 candidates / 97 covering layers as the relaxed model.
Symmetry [P]: x -> w x (w in GF(4)*) maps v_g to w^-2 v_{w g} and fixes every published level-1
span tested (inv4.py: all 12 invariant) and every Karatsuba cover, so gamma can be taken up to
GF(4)* multiples: representatives 0, 1, 4, 5, 6, 7 (tower codes) [observed: identical counts within
the classes {1,2,3}, {4,8,12}, {5,10,15}, {6,11,13}, {7,9,14}].
Distinct published level-1 spans (l1spans.py): ten 9-product spans (AD4 x3, A29 x2, A30, A32 x2,
hub A34, hub A43) and two 10-product spans (AD5 x2).

### 5.3 Published covers, member model (real model, gen13, gamma reps 0 1 4 5 6 7) -- 02:36 UTC
All results below are **[C, 1275-member model]** (GF(4)-ratio members only, single gamma, BMP middle
(WLOG for members), stage 1 fixed to the named published level-1 span):
- K = 13 over each of the ten distinct published 9-product spans (AD4 x3, A29 x2, A30, A32 x2,
  hub A34, hub A43): no covering layer (0-3 candidate 5-dim subspaces per case, none of rank 13).
- K = 12 over both AD5 10-product spans: none (so no 10 + 5 + 12 there).
- K = 14 over umizame's span: none for any gamma (so not even a 9|5|14 = 28 there).

### 5.4 Semi-members (X3's redirect, 02:30 UTC)
rprep.py option `semi`: candidates = ALL 108,375 rank<=2 tensors of X3's bil_cosets2.txt (the
1275 members of the 5-cosets plus all 107,100 tensors of 2- and 3-cosets -- i.e. all three types
(K,K), (K,Q), (Q,K); neither ratio is restricted), each realised as (l1 + lam2(v))(l2 + lam1(v)),
v = n + gamma N (real coordinates; gamma_real from the tower code via gmap.py), x-junk free inside
the stage-1 span (so the x^5 spare dimensions are usable). Quotient dim 54-56 (fits gen13).
gen13 option `n0`: quadrangle seeds only from the first n0 candidates (the members), extension over
all candidates. Exhaustive for layers with >= 9 distinct member images (<= 4 semi-members, any mix);
layers with >= 5 semi-members need semi seeds (X3's compatibility classes mod M8 would make that
feasible; not done yet).
Speed: gen13 residue grouping now by hashing (6x faster; same 7785/97 on the AD5 validation).
fastrank.py: rank test of gen13 candidates from the full quotient coordinates (.full), validated
(97 covering of 7785 on AD5/g14). Pitfall (logged): two Python patches wrote literal newlines into
string literals ('\n' inside a bash heredoc fed to python); rprep.py was broken 02:45-03:05 and the
6-AND-middle runs (ad4a-m6, umi-m6) of chain3 all failed at prep -- to be rerun.

**Semi result 1 [C, all-108,375-tensor model, member-seeded]:** umizame's 9-span, gamma 6 (the
"one free row + two paired rows" class), K = 13: gen13 with seeds from member pairs and extension over
all 108,375 tensors: 50,661 candidate 5-dim subspaces, **none of rank 13**. Exhaustive for layers
whose member images have >= 9 distinct points (i.e. at most 4 semi-members); 17 min.
Running (03:07): class-seeded version (gen13c: seed pairs = member pairs + pairs of semi-members in
the same class mod M8, X3's semi_classes.tsv), same case -- [H] beyond the member-seeded part.

### 5.5 Stage 1 left free (x-junk free) [C, 1275-member model, umizame middle irrelevant]
With all x-quadratics free (rprep `xfree`; stage 1 unconstrained, BMP middle, gamma 6) the member
quotient is only 18-dim and allsub.c (exhaustive over all 4-dim subspaces of the 10-dim V/T_full)
finds covering 12-member layers in such numbers that the output passed 2 GB within minutes (killed,
file deleted). So with the x-junk ignored, 12-member layers are plentiful; everything is decided by
the x-junk / 9-cover condition. This is why the searches above fix the stage-1 span.

### 5.6 NEW STRUCTURE 28 = 9 | 5 | 14 (verified) [C for the search, V for the circuits]
Over AD4 a28-g131's 9 level-1 products with the BMP 5-AND middle (NOT AD4's 6-AND middle), gamma
tower code 1 (= real g^34, AD4's own gamma), gen13 K = 14 (real model, 1275 members): 4676
candidate 6-dim subspaces, **69 distinct covering 14-member layers**. Two built and verified:
found/h2-ad4a-g1-c8c7227f-s58-a28.circ.txt (A 28, AD 6, G 591, GD 34) and ...-s59-a28 (28/6/585/33),
aes_check OK. AND profile 9 | 1 | 2 | 1 | 1 | 14 (stage 1 | BMP | layer): neither 10|5|13 (AD5) nor
9|6|13 (AD4). The G is from naive XOR chains (no optimisation): hub material.
Over umizame's span the same K = 14 search gives nothing (5.1). K = 14 over the other published
9-spans is in the running chain4 (list3).

Bug fixed 03:20 (found by L1b): rvd.py / vd13.py called campaigns/aes_check.py via parents[1]
(non-existent path), so their sidecars lacked the check; now parents[2], an 'aes_check' field
in the JSON; all 5 existing found/ circuits re-checked by hand: OK.
All 69 AD4-span 9|5|14 layers built with distinct spans (rvd.py now skips layers whose member span
mod the prefix was already built): 69 circuits in found/ (A 28, AD 6, aes_check OK), list
~/xs-campaigns/2026-11-15-study/H2/builds-for-T1.txt; x1b_family on the first 10: 10 distinct product
spans, level profiles 9|1|2|1|5|10, 9|1|2|1|6|9, 9|1|2|1|7|8, 25-26 dims shared with AD4 g131,
16 with AD5 g124. T1 polished s59 to 28/5/157/31 and s58 to 28/6/161/31 (coordinator).
gen13 03:30: hash tables cleared per used slot only and allocated per depth (memory O(n) instead
of 9 x 4n), needed for the 2.3M-candidate singleton runs; validated again (7785 / 4676 candidates).
**Semi result 2 [H, incomplete]:** umizame span, gamma 6, class-seeded gen13c (2,089,705 seed pairs:
member pairs + same-class semi pairs) hit its 50-min cap (old slow binary) after 356,165 candidate
5-dim subspaces: none of rank 13. Not a complete case; rerun in the queue (qsemi.sh) with the faster binary.
Singleton-pair test (rprep semi all2, 2.3M candidates): the prep was started niced alongside other
jobs, reached 1.46 GB RSS after 32 min wall / 2.4 min CPU and was stopped (no result). The queue
entry (qall2.sh) is therefore untested at full size; memory estimate 3-5 GB.
Pitfall (twice): `pkill -f PATTERN` inside `bash -lc '...'` also kills the calling shell (the pattern is in
its own command line), as BRIEF-COMMON warns; use PIDs.
- [C, 1275-member model] K = 12 over each of the ten published 9-spans (gamma reps): none (no 26).
- 6-AND-middle option validated: AD4 L + AD4's 6-AND middle, gamma 1, K = 13 -> exactly 1 covering
  layer (AD4's own structure; built, not listed for T1).
**Semi result 3 [C, all-108,375-tensor model, member-seeded]:** AD4 g131 span, gamma 1 (the gamma of
its 69 fourteen-member layers), K = 13: 37,053 candidate subspaces, none of rank 13 (11 min).

## 6. Summary at 04:45 UTC (what H2 established; all [C] in the stated models only)
Positive: new AND structure 9 | 5 | 14 = 28 (69 layers over AD4's span, all built, polished by T1
to 28/5/157/31); 97 alternative 10|5|13 layers over AD5's prefix.
Exact negatives (fixed stage-1 span, BMP middle, one gamma; members: WLOG middle):
| stage 1 | pool | K | result |
|---|---|---|---|
| umizame 9-span | 1275 members | 13, 14 | none (all gamma) |
| 10 published 9-spans (AD4 x3, A29 x2, A30, A32 x2, hub A34/A43) | members | 12, 13 | none (gamma reps) |
| AD4 g131 9-span | members | 14 | 69 layers (new 28s) |
| AD5 10-spans (x2) | members | 12 | none |
| umizame 9-span, gamma 6 | +107,100 semi, member-seeded | 13 | none |
| AD4 g131, gamma 1 and 6 | +semi, member-seeded | 13 | none |
| umizame, gamma 6 | +semi, class-seeded | 13 | none in 356k candidates (capped: [H]) |
| umizame, gamma 6 | +semi +2.16M singletons, class-seeded | 13 | running, capped 40 min ([H]) |
Earlier pieces: row problem 5 late per row; pure-bilinear minimum 10 members (10200 spans);
10-member layers have (J_x, J_v) = (8, 4) at gamma 0; class-parity structure P_gamma; umizame cover +
row-local members: no 13/14.
Not covered: other stage-1 covers (queued: 200 H4 + 2100 Karatsuba covers), mixed gammas in one
layer (tooling exists: rprep GAMMAS comma list), products outside the rank<=2-tensor pools, deeper
stage 1, middles other than BMP for non-member pools.

### 5.7 Singleton pairs (X3b) -- validation run 04:30-05:10 UTC [H, capped]
umizame 9-span, gamma 6, candidates = 1275 members + 107,100 semi + 2,162,400 singleton-coset
tensors (2,270,775 distinct products; quotient dim 54; prep 3.5 min, 2.0 GB). gen13c class-seeded
(74,382,205 seed pairs: member pairs + same-class pairs mod M8), RSS 2.9 GB, capped at 40 min:
28,185 candidate 5-dim subspaces, **none of rank 13**. Incomplete (cap), so [H] only. Throughput
~12 candidates/s; a complete case needs hours -> tier 3 of the queue.

### 5.8 Last runs (05:10-06:15 UTC)
- Tier-1 slice [C, 1275-member model]: H4 covers l1_000 .. l1_011 (all 16 gamma each) and l1_012
  (gamma 0-5): 198 cases, no 13-member layer (log t1a-now/w0.log). (l1_000 has the same seed
  statistics as umizame's span.)
- K = 14 over the other published 9-spans, gamma 1 and 6 [C, members]: AD4 g141 span and AD4 g176
  span each give **69 covering 14-member layers at gamma 1** (more 9|5|14 = 28 families, on
  different stage-1 spans than g131); none at gamma 6; none for A29 x2, A30, A32 x2, hub A34, hub A43
  (gamma 1, 6). Builds of distinct spans appended to builds-for-T1.txt.
