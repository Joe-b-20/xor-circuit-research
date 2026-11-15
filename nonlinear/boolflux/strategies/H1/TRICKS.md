# Catalogue of the tricks in the known low-AND AES S-box circuits (agent H1)

Input for H2 / H3. Labels: [C] computed exactly on the named files (tools and data in NOTES.md),
[P] proved (argument given or cited from strategies/C), [H] heuristic / estimate. Savings are
relative to Boyar-Peralta 32 = 9 (stage 1) + 5 (GF(16) inversion) + 18 (last layer).

## 0. One picture that covers every known circuit [C, 63 files from 3 independent designs; later A28s (spangen: 11 members + a non-member pair; X1b g158: 12 + a pair) break the 13-member pattern, NOTES 10.2]

Every known circuit with <= 32 ANDs is  S1 (l products of x-linear forms, span contains V_N)
-> MID (m ANDs on functions of N) -> LAST (k products of operands
c + Tr(Ax) + Tr_K(t N) + Tr_K(s n)), with outputs = LAST part + S1 part ("x-junk") + MID part
("N-junk") + affine. The only freedom used so far is WHAT the last layer is and WHICH junk it
leaves. Last-layer members are grouped by the "row" / class zeta = s^3 in mu_5, i.e. by the
point of the projective line P^1(GF(4)) that the GF(4)-linear functional of n defines (GF(16) is a
2-dim GF(4)-space; its GF(4)-functionals up to GF(4)* are 5 points) [P: a member's n-part
Tr_K(s n) and Tr_K(w s n) give the same GF(4)-functional up to scaling; zeta = s^3 identifies s up
to mu_3 = GF(4)*]. Karatsuba over GF(4) uses 3 of the 5 points. Members per class [C,
`decomp_all.json`]:

| design | l + m + k | members per zeta-class (row) | member type | x-junk Jx | N-junk J0 |
|---|---|---|---|---|---|
| BP (NIST A32 AD5/AD7) | 9+5+18 | (6,6,6) bilinear Tr(sn)Tr(Ax) | bilinear | 0 | 0 |
| BP+row (NIST A32 AD4, hub A31) | 9+6+17 / 9+5+17 | 12 bilinear + one 5-member mixed row | not GF(4)-norm (A'/A = g^145) | 2, junk = 2 S1 products (rank 2) | 0 |
| umizame (NIST A29 / A30) | 9+5+15 / 9+6+15 | (5,5,5) | GF(4)-norm, gamma = 0 | 2-3, every junk class has a rank-4 form | 0 |
| A28 AD5 (NIST, hub) | 10+5+13 | (5,3,5) or (5,4,4) | GF(4)-norm, gamma != 0 | 3, three classes of min rank 6 | 0 |
| A28 AD4 (NIST, hub) | 9+6+13 | (3,4,4,2) or (4,4,3,2): 4 classes | GF(4)-norm, gamma != 0 | 2 | 1 (needs 6-AND middle) |
| hub A29/A30 | 10+6+13, 10+7+13 | as AD5 | as AD5 | 3 | 0 |

## 1. The tricks

**T1. Tower / norm reduction** (all). x^-1 = n * x^16 with N = x^17 in GF(16). Cost structure
l + m + k. Optimal pieces in their own model: V_N needs exactly 9 level-1 products [C, track C,
exhaustive: 7 and 8 impossible]; GF(16) inversion needs 5 [C, track C SAT]. Saving: baseline.

**T2. Karatsuba over GF(4)** (all). Each GF(16) product = 3 GF(4) products ("rows"), GF(4)
product = 3 ANDs: 9 per GF(16) product, which is the bilinear rank [Barbulescu et al. 2012].
Stage 1 = the product L*R (3 rows x 3). Last layer = Q*L and Q*R (3 rows x 2 products x 3).
Saving 0 (it is how 32 is reached), but rows are the unit every later trick works on.

**T3. Additive leakage / junk absorption** (all but BP). Last-layer products are allowed to carry
extra quadratic-in-x terms (absorbed by S1 products added to the outputs) and extra functions of
N (absorbed by MID products, n, N). Saving 0 by itself; it is the enabler of T4-T6. Cost model:
the junk must lie in span(S1) (x-junk) and span(MID, N, n) (N-junk); if not, l or m grows.

**T4. umizame triple identity** (A29). For a, b, c in GF(4): {ab, bc, ca} in 3 early + 5 late =
8 ANDs instead of 9, the late 5 being GF(4)-norm members (gamma = 0) whose x-junk lies in the span
of the 3 early products. Applied per row: -1 per row, -3 in total -> 29 [C: 9+5+15, Jx = 3 inside
the 9 S1 products]. Requirements: the early products of each row must be exactly the bilinear
products tau(W^j a) tau(W^j b) that stage 1 computes anyway (true for the Karatsuba S1).

**T4'. Non-norm 5-member row** (NIST A32 AD4, hub A31). One row done with 5 mixed members
(types n|x+n and x+n|x+n, not GF(4)-norm) whose junk consists of 2 S1 products themselves.
-1 -> 31 (with a 5-AND middle). [C] Same saving as T4 per row, different identity.

**T5. gamma-shifted GF(4)-norm layer** (A28). 13 members N_{GF(4)}(Lambda(x) + G(n + gamma N)),
gamma != 0 (one gamma per file: g^17, g^34, g^187, g^204), classes (5,3,5) [C]: one row needs only 3
late members. Mechanism [H]: the n-block equations (2.2 (i)-(ii)) do not involve gamma, so gamma
can only help through the junk: it shifts each output's x^9-junk by gamma b_j, which lets fewer
members leave an acceptable junk. -5 in the
last layer, but [C]: AD5's junk U (dim 7) is not 9-coverable -> l = 10 (+1); AD4's junk is
9-coverable but its N-junk is outside the 30 5-AND classes -> m = 6 (+1). Net -4 -> 28.

**T6. 6-AND depth-2 middle** (AD4 files). m = 6 instead of 5 buys depth 4 and two extra
N-functions (in some files one coordinate of the GF(4) norm x^85). In A28 AD4 it absorbs T5's
N-junk; in umizame-A30 and hub A29/A30 it is pure depth cost (+1).

**T7. Inexact inverse** (hub a29-ad4-g130). The middle computes n except at N = 0 (3 of 4
coordinates of n exact), the last layer repairs the point x = 0 (operands carry [N != 0]).
Saving 0 [C], but it shows the middle target need not be n itself.

## 2. Pairwise compatibility and combined estimates

Notation: a design is (l, m, k); a 27 needs l + m + k = 27, so (9, 5, 13) or (9, 6, 12),
(10, 5, 12), or anything outside the skeleton.

| pair | combined design | count | status | exactly what must be true |
|---|---|---|---|---|
| T4 x T4' | rows done by either 5-member identity | 29 | known level (no gain) | - |
| T4 x T5 | 13-member gamma-type layer whose junk is absorbed like umizame's | **27** = 9+5+13 | OPEN | (i) 13 last members with operands in span(1, x, N, n); (ii) U = V_N + x-junk lies in the span of 9 level-1 products (the stage 1 itself); [H] necessary in practice: every junk class mod V_N has a rank-4 (or rank-2) representative - all 1702 13-member layers G evaluated and all A28 layers have a class of min rank 6 and are non-coverable; (iii) N-junk inside one of G's 30 5-AND classes; (iv) grade-0 residue absorbed. Excluded so far [C]: A28 layers and their cand13 neighbourhood; 13-layers keeping >= 10 umizame members over umizame's prefix (keep.py); [H] G's walks from A28 starts. Not excluded: gamma = 0 layers with 13 members (classes like (5,3,5) without gamma), gamma != 0 layers with low-rank junk, non-norm members. |
| T5 x T6 | AD4 type | 28 | known | - |
| T4 x T6 | umizame + 6-AND middle | 30 | known (A30) | - |
| T5 with 4-member rows (2 norm ANDs per GF(4) product) | rows (4,4,4) = 12 | 9+5+12 = 26 needs junk 6 | IMPOSSIBLE with l = 9 [P, C/NOTES 6: l >= 4 + J + rho2 >= 11] -> 28 at best (11+5+12) | - |
| T4 rows x 4-member rows | rows (4,4,5) = 13 | 27 | EXCLUDED [C, H2 normspan.py: V_N + two rows' norm forms + third row's early products has dim 11 > 9] (earlier [H] reason: c5-rank) | a 9-product level-1 cover W of V_N with rho2 = 1 containing the 4 within-row norm forms N(a_i), N(b_i) of the two 4-rows (each is a single rank-2 product, so they could be S1 products themselves), plus the umizame row's 3 early products in W. Decidable by SAT (C's stage1.py + c5-rank constraint) or cover lemma for a fixed choice. |
| T4 rows x (4,5,5) | 14 | 28 | no gain | - |
| T5's 3-member row x T4 rows | classes (5,3,5) with gamma = 0 | 27 | OPEN | the A28 3-member row works only with gamma != 0 in all files; need a gamma = 0 variant or a junk-coverable gamma variant (same conditions as T4 x T5) |
| T7 x anything | inexact middle | +0 | - | only useful if a middle "target" other than n is cheaper than 5 (no: G's 30 classes are for n plus one function; a different target function of N could have a different MC - not computed) |
| T3 with stage-1 depth 2 | N (or the S1 junk) computed with 2 AND levels | ? | NOT EXPLORED | every exact stage-1 bound (9) is for one AND level; a 2-level stage 1 could cover V_N + junk with <= 8 ANDs only if level-2 products help - nothing known either way |

### 2.0 Update 02:50 UTC (NOTES 7): what the 9+5+13 target now requires

* **gamma = 0 is dead for <= 13 members** [P, 1275-member model (all last ANDs GF(4)-norm members); NOTES 7.2 Theorem 1, from checked spectral facts +
  H2's parity lemma]: a GF(4)-norm layer with operands x + n only and a 5-AND middle needs
  k >= 14 members (k >= 15 with <= 4 classes; umizame's 15 is optimal there). So "umizame junk
  placement" can only be combined with a short row if gamma != 0, as in A28.
* **12 members (gamma != 0) only in one rigid shape** [P, 1275-member model, Theorem 2]: all 5 classes, row
  sizes with sum(n_P - 1) = 7 and n_P <= 3, all row z-values in cosets of one 2-dim D inside a
  <= 4-dim Z, free class f of Pi(gamma) of size 1 or 2, cosets: row f in D, paired classes in a
  common coset each. Shape "(4,4,4) on 3 classes" is impossible. Not enumerated (too large for
  this session) - an explicit, small algebraic case for H2.
* (4,4,5) rows: now excluded [C, H2 normspan.py: dim 11 > 9].
* Fast exact testers: `nfast.py` (no truth tables, microseconds; n-block + parity + x-junk,
  reproduces all published layers) and `cond27.py` (truth tables + exact 9-cover test).
* Exhaustive one-swap neighbourhoods of all 6 distinct A28 layers (any gamma, stage 1 free): no
  27 [C, 1275-member model, NOTES 7.3]
* 14 -> 13 for 30 new 9+5+14 / 10+5+13 circuits and 12+1 / 11+2 for the AD4 layers: no 27
  [C, case: prefix FIXED, replacements with operands in O2; chains and re-chosen stage 1 open;
  NOTES 8, 9, 10.2]. All cover tests used were exact enumeration (NOTES 10.1).; two-swap neighbourhoods: layer g124 pairs 0-20 done, the rest queued
  (QUEUE.md "H1-b").

### 2.1 The T4 x T5 question in track C's coordinates (most concrete 27 target)

Members (z, zeta) of C's model (validated: every umizame and A28 product is one [C, zcheck.py]).
For a k-member layer S over E: Z = span{z_m}, rank pi(S) = rank of S modulo E + T; T in
span(E + S) forces rank pi(S) <= k - 8. Known layers [C, zrank.py]:

| layer | k | dim Z | rank pi | excess = rank - dim Z |
|---|---|---|---|---|
| A28 AD5 / AD4 (all 30 files) | 13 | 5 | 5 | 0 |
| umizame (6 files) | 15 | 4 | 7 | 3 |

A 27 with 13 members over a 9 + 5 prefix needs rank pi <= 5, i.e. (dim Z, excess) in
{(5,0), (4,0..1), (3,0..2), (2,0..3)}. Coverage (gamma common to all members):
* (2, any): **none** [C, `zdfs2.py`, exhaustive in this case, 80 runs] over umizame E (k=13),
  A28-AD5 E (k=12), A28-AD4 E (k=12), AD4-L + AD5-inv (k=13), umizame-L + AD5-inv (k=13), all 16
  gamma values (NOTES section 6). So an umizame-like layer keeping excess 3 cannot be squeezed
  to 13 over these prefixes.
* (3,0), (3,1), (4,0) over umizame's E, gamma none, k = 13: **none** [C, C's zdfs/zdfs3 run by
  H1, NOTES 6]; over AD5/AD4 E with k = 12 done by C (none). gamma != 0 over umizame's E and the
  other 9 + 5 prefixes: queued for overnight (QUEUE.md, H1 section).
* (4,1), (3,2), (5,0) over 9 + 5 prefixes: NOT covered (the A28 layers are (5,0) but over 10+5 /
  9+6 prefixes). An umizame-like 13 (two rows of 5 sharing z-points, one short row) would most
  likely sit at excess 1-2: this is the uncovered zone to search next.
* Members with different gamma (or independent N-part) in one layer: not covered anywhere.

### 2.2 Formula sheet for a GF(4)-norm last layer (for H2's constructions)

Member m = (z_m, zeta_m), Y_m = z_m / zeta_m, class P = zeta (row). Output j uses members with
coefficients c_jm (unique). Then [C, `nblock_check.py`, umizame and A28 AD5]:
(i) sum_m c_jm Y_m = b_j (= coefficient of x^239 in output j; the 8 b_j form a basis of F);
(ii) sum_m c_jm z_m = 0 (the class-47 / f_11 component cancels; this also kills C's f_4 term).
Junk ([H]: from C's [P, V] member spectra, normalisations not re-verified by H1): x-junk of output
j = (sum_P zeta_P^-1 sum_{m in P} c_jm Y_m^3 , gamma b_j + sum_P zeta_P^-1 sum_{m in P} c_jm Y_m^18)
in the (x^3, x^9) classes, must lie in span(S1) mod V_N; N-junk = sum_P eps_{P,j} Tr_K(zeta_P v^3)
with eps_{P,j} = parity of the class-P members used by output j, must lie in the middle's span.
(i)-(ii) do not involve gamma: gamma enters only the junk (it shifts the x^9-junk by gamma b_j and
the N-junk through v = n + gamma N).
**gamma is not free [C, `gamma_twin.py`]:** keeping the member indices (z, zeta) and changing
gamma keeps (i)-(ii) but the minimal x-junk jumps from 3 (own gamma) to 8 (every other of the 16
values) for both A28 AD5 (own g^17) and umizame (own none) - consistent with the shift gamma b_j
of the x^9-junk, which is independent across the 8 outputs. So for a candidate member set the
right gamma is forced by the x^9-junk equations; H2 can solve for gamma instead of enumerating it.
**Observed [C]:** umizame has eps_{P,j} = 0 for every row and output ("even rows": its N-junk is
identically 0); A28 AD5 (g124) has odd parities in 5 of 8 outputs (its N-junk is absorbed by the
middle's extra function). A 27 design can therefore choose between paying with parities (needs
the N-junk in one of the 30 5-AND classes) or keeping rows even (umizame's choice).

## 3. Things no known circuit does (so all exact results are silent on them) [C on 63 files]

* An AND whose operands mix an x-linear form with a middle product (other than N, n), or with an
  S1 product beyond N: never.
* An output bit finished before the last AND level: never (output rank in E_L is 0 below the top).
* A middle that is not a function of N, or a last layer whose operands are not in
  aff(x) + span(N, n) (+ the [x = 0] indicator in one hub file): never.
* Use of the GF(4) norm x^85 as the reduction (x^-1 = x^84 (x^85)^2 with GF(4) inversion free):
  never; x^85 appears only as a by-product of 6-AND middles.
* Last-layer products whose operands contain degree-2 S1 terms other than N (cubic or quartic
  "partial products" in x): never.
These are the regions a <= 27 search outside the model would have to enter; H3's general-model
SAT and H4's representations are the only current probes there.

## 4. Lower bounds to keep in mind

MC(AES S-box) >= 13 [P, NOTES section 4]; the published literature claims a better (unknown to us)
bound in Jeon-Baek-Kim, IEEE TC 2024 [H]; no bound near 27 is known. Every "27 impossible"
statement of ours is restricted to the three-stage skeleton and further to the cases listed in
NOTES section 4.1.
