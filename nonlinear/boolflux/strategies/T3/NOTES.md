# T3: targeted search for goal F (A <= 35 / AD 3 / G <= 138 / GD <= 26), 2026-11-15 from 01:33 UTC

CPUs 6-7. Data: `~/xs-campaigns/2026-11-15-study/T3/`. Code: this directory. Verification of every
circuit: hub.common.verify (core + independent verifier, NIST library), aes_check.py for anything reported.

Starting point: min G over all known AD3 A<=35 circuits is 139 (NIST 139@GD27, 139@GD31); at GD<=26
the best is 140@25 (ours), 141@25 (NIST). Goal F therefore needs a G below every known AD3 circuit.

## 1. Structure of the AD3 circuits (facts, measured)

- `regions.py`: XOR gates per AND-level region. NIST 139@27: [20, 41, 28, 15] (top, after level 1,
  after level 2, bottom); 139@31 [20, 40, 29, 15]; 141@25 [20, 41, 28, 17]; ours 140@25 [20, 41, 28, 16];
  142@21 [21, 43, 27, 16]. Regions 0-2 are almost identical across the frontier; the GD trade-off is
  paid mostly in the bottom and region 1.
- `decode.py`: all published AD3 circuits (139@27, 139@31, 141@25, 157@15, 183@13) use the same 3
  level-3 Q operands, each used by 4 products, and level-2 ANDs whose N-parts lie in a 2-dim space.
- **GF(4) reading** (`gf4check.py`, [C] checked exactly on 139@27): x^-1 = x^170 * x^84 with
  x^170 = Delta^-1 in GF(4) (Delta = x^85 = norm to GF(4)) and x^84 = N^4 x^16 (N = x^17). Every level-3
  product is Q_w R_c with Q_w = Tr(w x^170) (3 distinct functions, the 3 nonzero functionals of a GF(4)
  element) and R_c = Tr(c x^84) exactly (not only on supp Q); all 255 functions Tr(c x^84) lie in
  S = span{signals of AND level <= 2} (dim 32). The 12 R's are c in C_a = rho^a L (a = 0, 1, 2; rho a
  primitive GF(4) element, L a 4-dim GF(2)-subspace, here L = span{28, 144, 14, 72} for one class):
  level 3 is "GF(4) scalar times GF(256) vector" with Karatsuba per GF(4)-coordinate.
- **12 products are minimal for this product form** [C, for products Tr(w x^170) Tr(c x^84) whose span
  must contain the 8 outputs]: with classes C_1, C_2, C_3 (spans of the c's paired with each of the 3
  Q's) the outputs are in the span iff for every z: (z, rho z) in C1 x 0 + 0 x C2 + diag(C3); this forces
  C1 + C3 = C2 + C3 = C1 + C2 = GF(256), so d1 + d2 + d3 >= 12.

## 2. Exact operand re-choice (idea 4): rigid [C]

`pairs.py`: for each AND g = AND(a, b) with product P and S = span of signals of lower AND level, the
set of all pairs (a', b') in S x S with a'b' = P is computed exactly (a' in an affine subspace A', b' in an
affine subspace per a'). Result on NIST 139@27, all 35 ANDs: dim A' = 2, i.e. A' = {1, a, b, a+b+1}: only
the trivial XNOR identities AND(a, b) = AND(a, XNOR(a, b)) exist [C, for each fixed product and fixed S].
So the level-3 operands cannot be re-chosen with the same products; any gain must change products.

## 3. Product exchange at level 3 with output compensation (`prodswap.py`)

Replace P_i by P' = a'b' with P' = P_i mod (S + other products) (exact linear condition for fixed a').
On 139@27 with a' = existing signal or XOR of two: 6-7 a' per product admit a solution, every
materialised exchange costs +2 or more before polishing. Not pursued further (no cheap exchanges).

## 4. GF(4)-coordinate choice at level 3 (`gf4search.py`, `gf4build.py`)

Freedom: L (equivalently 4 GF(4)-independent GF(4)-points l_1..l_4 of GF(256), C(85,4) = 2.0M
quadruples), and the per-class bases. Every choice is admissible-checked exactly (outputs in the span
of the 12 products). Price model: greedy nearest-first SLP over the signals of AND level <= 1 plus the
level-2 ANDs (region-2 rebuilt) + Paar for the bottom 8 x 12 matrix. Calibration on 139@27: the model
prices the published choice at 34 + 15 (actual region 2 = 28, bottom 15).
- **The admissible class triples are exactly the scaled ones** [C, derivation; for 12 products of the form
  Tr(w x^170) Tr(c x^84)]: write Delta' = d1 th1 + d2 th2 (dual basis), Q1 = d1, Q2 = d2, Q3 = d1 + d2; an
  output Tr(e Delta' V) = d1 Tr(e th1 V) + d2 Tr(e th2 V) needs, for every z, some c3 in C3 with
  z - c3 in C1 and sigma z - c3 in C2 (sigma = th2/th1). A linear section f: z -> c3 exists; dim C1 <= 4
  forces ker(id - f) >= 4, i.e. f = id on C3, and likewise f = sigma on sigma^-1 C3; hence
  C1 = sigma C3, C2 = sigma^2 C3 with C3 cap sigma C3 = 0. Remaining freedom: L = C3 and an independent
  basis of each class (aligned bases {sigma^a l_i} give the triple relation R_l + R_{sigma l} = R_{sigma^2 l},
  used 4 times in the published region 2).
- Region 2 of NIST 139@27 (`region2.py`): Q's cost 4 XORs (from the 3 pure-N level-2 ANDs), the 12 R's
  cost 24: 8 "entries" (20 XORs) + 4 triple closures.
- Bottom price (Paar) over 2,000 random admissible quadruples (`bottomscan.py`): 17-30, mode 23-24; the
  published choice has 15 (Paar 15, actual 15), the best seen in the ranked search also 15. The published
  coordinate choice is near the best for the bottom [H].

## 5. Level-2 product exchange: rigid as well

`prodswap.py --level 2` on 139@27 (a' = existing signal or XOR of two, b' cheap, exact span
condition P' = P_i mod (S1 + other level-2 ANDs)): only the trivial a' (a, b, a+b) admit solutions,
all exchanges cost +2..+4 [C for these move sizes: single-product exchanges keeping the span].

## 6. GF(4)-coordinate move + kernel (first measurements, [H], 1 seed each)

Source NIST 139@27 (A35 AD3), new quadruple, region 2 kept (keep2) or rebuilt (fresh), kernel polish
100 s caps (35, 3, -), objective cost,gd:
| choice | built | after 100 s |
|---|---|---|
| published (fresh rebuild, control) | 156@29 | 147@27 |
| 11,22,57,110 fresh | 157@26 | 143@27 |
| 11,22,57,110 keep2 | 148@26 | **142@24** |
| 11,57,101,114 keep2 / fresh | 154@27 / 169@27 | 144@27 / 143@28 |
pipe1 (80 s per choice, 9 choices from the ranked list, keep2): 141@26, 141@28 (x2), 142@29, 143@27 ...
chain1 (t3polish on the 142@24 etc., cap GD 26, 240 s): 142@24 -> **142@22** in the 2nd run (equal to
the best known 142@22). So the move produces frontier-quality AD3 circuits with a different level 3
within minutes; none below 139 so far.

## 7. One-point neighbourhood of the published coordinate choice (`nbscan.py`, `nb2.py`)

Replace one of the 4 GF(4)-points (published L = span{28, 144, 14, 72} for the class of Q(w=2)) by any
of the 255 field elements, region <= 2 kept (keep2), new R's added greedily, bottom by Paar:
765 distinct circuits in 19 s. Built G: 140 for the 9 variants that are scalings of the current points
(same R set, other Q pairing; the rebuild costs +1 over the source), then 143 (+4) for the best real
changes; two-point changes from the 6 best per index: 146 at best (+7). Same picture for the sources
140@25, 141@24, 142@21 (+3 for the best one-point change).
Kernel polish 90 s, caps (35, 3, -), objective cost,gd, 1 seed each:
- control (published choice, rebuilt, 140@27): 140@27, no improvement;
- one-point changes: 140@29, 140@30, 140@30, 140@29, 141@26, 141@28, 142@27, 142@29 (x2).
So alternative coordinate choices reach the same G as the rebuilt published choice under equal
treatment [H, n = 1 seed]. Deep G-first chains from them: section 8.

## 8. Level 2 is rigid against single-product exchanges [C]

- `drop2.py` (139@27): removing any one level-2 AND loses 1-8 of the needed level-<=2 functions
  (3 Q's + the 8-dim space Tr(c x^84)); span(S1 + the 9 mixed level-2 ANDs) contains no N-quadratic
  form beyond S1 (dim 0), so the pure-N ANDs cannot be fed by the junk of the mixed ones: no AND can be
  dropped this way (no A34 AD3 from this structure) [C, for this circuit's other ANDs fixed].
- Hence, for every level-2 AND, a replacement P' must satisfy P' = P_i mod (S1 + other level-2 ANDs).
  `l2swap.py`: with a' = l(N) + s(x) (+ const) over all 8192 such forms and b' anywhere in S1, the only
  solutions with b' of the same form are the trivial ones (a, b, a + b and complements) for all 12
  level-2 ANDs [C, for that operand form]. `prodswap.py --level 2` with a' = any existing level-<=1
  signal or XOR of two: also trivial only.
- Consequence: a different level 2 needs at least two products changed together (like the level-3
  coordinate move, which changes 3 products per GF(4)-point).

## 9. Which coordinate choice do the frontier circuits use?

All three published A35 AD3 circuits (139@27, 139@31, 141@25) and every hub/F circuit in the T3 pool
that descends from them (140@25 x5, 141@24, 142@21, ...) use the same 4 GF(4)-points
(orbits of 28, 144, 14, 72). Circuits with other points made tonight (all verified):
140@26 and 140@29 (1 point changed), 141@25/141@28 (1), 141@26 (2), 142@22 (2), 142@24/26 (1).
These are the first known A35 AD3 circuits with a different level-3 coordinate choice; none is
better than the published-choice frontier (140@25 dominates 140@26).

## 10. Hub operator

`hub/ops/t3_gf4move.py` (common hub CLI; registers `gf4move`): one-point (p 0.7) or random 4-point
choice, keep2 rebuild (p 0.8), kernel polish for the rest of the budget under (A, AD, GD + 2) or --caps.
Smoke test: 139@27, 20 s -> 1 candidate (145@25 built, no kernel gain in 17 s). Not A/B-tested in
the hub. Note: picking the replacement point at random gives +8..+13 before polishing; gf4loop.py
(from 03:15) instead builds all 255 replacements of one index (~13 s) and picks among the 6 cheapest
real changes (+3..+5).

## 11. Level 1 is NOT rigid: span-preserving level-1 product exchanges (`l1swap.py`, `l1move.py`)

Exhaustive over all pairs of x-linear forms (a', b'): pairs with a'b' = P_i mod (affine + the other 10
level-1 ANDs), i.e. S1 = span{1, x, A1} unchanged, so every level >= 2 function is unchanged [C]:
NIST 139@27 has 6-18 such pairs per level-1 AND (3 of them the trivial XNOR forms). Materialised
(operands from level-0 signals with <= 2 extra XORs, compensation P' + other A1 + affine fed to the
old consumers, dead gates removed): 139@27 -> 409 distinct circuits, 5 at G 139 (dG 0), 15 at 140;
140@25 -> 6 at 140@25 (dG 0), 15 at 141. These equal-G moves (a plateau of level-1 structures the
kernel cannot reach: it never changes an AND's function) are used as op "l1" in gf4loop.py from
03:22 UTC (1-3 steps, then a kernel polish).
- Level-1 plateau (`l1bfs.py`, BFS over dG <= 0 exchanges): closed components of 10 circuits
  (139@27) and 17 circuits (140@25), all at the source's (G, GD); no exchange lowers G.

## 12. Level 2 is rigid against two-product exchanges too [C]

`l2pair.py` (139@27): for every pair (i, j) of level-2 ANDs (66 pairs), W = S1 + the other 10; new
products must represent two different nonzero classes of {P_i, P_j, P_i + P_j} mod W. With both
operands of the form c + l(N) + s(x) (exhaustive over a', b' solved linearly), the number of new
products (P' not in P_i + S1 or P_j + S1) is 0 for every pair and class [C, for this operand form and
the other 10 level-2 ANDs fixed]. (A first run counted operand-complement variants as new; fixed,
the buggy log is kept as l2pair139-buggyfilter.log.)

## 13. Region-1 Boyar-Peralta re-synthesis (`bp1.py`) - weaker than the published layer

Exact coordinates (19 bits: x and the 11 level-1 ANDs), base = inputs + region-0 signals + level-1 ANDs,
targets = 24 level-2 operands + 4 region-1 signals read above. BP with random ties, 1 restart: 44 XORs
for the published operand pairs, vs 41 in the circuit. Per-region SLP heuristics do not beat these
layers (consistent with track F's linres result); operand-pair re-choice with BP was therefore not
pursued (each BP run ~60 CPU-s in numpy).

## 14. No A34 by sharing the pure-N level-2 ANDs with the mixed ones [C, restricted case]

The 3 Q forms Q_v = Tr_{4/2}(v N^5) (v in GF(4)*) have symplectic rank 4; the published circuits build
them as p_a + p_b from 3 rank-2 pure-N products. The only N-quadratic junk a mixed level-2 AND
(alpha + s)(beta + t) with alpha, beta in the T-plane can contribute is tau1 tau2 (rank 2, unique mod
linear terms). `a34rank.py`: rank(Q_v + tau1 tau2) = 4 for all three v, so tau1 tau2 cannot be one of
the three rank-2 forms; and with 2 pure-N products p1, p2: the 2-dim Q-space inside span{p1, p2, tau1
tau2} would contain a Q in span{p1, p2} (necessarily p1 + p2) and another Q_a with Q_a + tau1 tau2 in
{p1, p2, p1 + p2}, i.e. of rank 2 or equal to a Q - both impossible. Hence in this family (N-parts of
the mixed products in the T-plane, Q's from level-2 N-quadratic parts) level 2 needs >= 3 pure-N ANDs
besides the mixed ones, and 11 + 12 + 12 cannot become 11 + 11 + 12 this way. Not a general bound.
- Kernel polish (110 s, caps 35/3/26, cost,gd) of 8 of the 17 members of the 140@25 level-1 plateau:
  140@25 in 8/8, no improvement at all (t_last None) [H]; batch stopped (l1/l1pol.log).

## 15. New AD3 frontier point: 35/3/142/20 (04:09 UTC, aes_check OK, new Pareto point on the pin)

`~/xs-campaigns/2026-11-15-study/T3/found/aes-sbox-a35-ad3-g142-gd20-25c6b601e491.circ.txt` (+ .json).
Best known before at GD <= 20 with A35 AD3: 144@20 (hub), published 147@20. It also dominates the
known 142@21 and 142@22. Lineage (every step verified): NIST 139@27 -> GF(4) coordinate move (points
11,22,57,110, keep2) + kernel 100 s -> 142@24 -> kernel chain (cap GD 26) -> 142@22 (new choice, 2 points
changed) -> GF(4) one-point move (57,110,22,55) + kernel 150 s (cap GD 22) -> 143@21 -> level-1 product
exchange walk (2 steps, l1move.py, G unchanged) + kernel 150 s (caps 35/3/21, cost,gd) -> 142@20.
Both new operators are in the lineage; the low-GD loop (gf4loop.py --gd 21, seeds 142@21/22, 144@20,
145@19) found it in its 10th step (~30 min, 1 CPU). [H]: one success, no A/B.
- 04:40 UTC: **35/3/144/19** (aes_check OK, new Pareto point; best known at GD 19: 145@19): plain kernel
  polish 240 s at caps (35, 3, 19) of the 142@20 above (lowgd2 run, seed 77).
  File `T3/found/aes-sbox-a35-ad3-g144-gd19-3eb6e68c6f1c.circ.txt`.
- 05:07 UTC: **35/3/142/19** (aes_check OK, new Pareto point; dominates 142@20 and 144@19): level-1
  exchange walk (2 steps, s42) on a 142@20 of the lowgd pool + kernel 150 s at caps (35, 3, 19)
  (lowgd3 run, seed 88). File `T3/found/aes-sbox-a35-ad3-g142-gd19-724d37c6a122.circ.txt`.
  Observation [H]: in the low-GD band (GD 19-22, less optimised than GD 25-27) the l1 walk + kernel
  repeatedly finds lower G or GD; at GD 25-27 it found nothing in ~20 steps.
- 05:30 UTC: **35/3/144/18** (aes_check OK, new Pareto point; best known at GD 18: 146@18): level-1
  exchange walk (3 steps) on a 144@19 of the pool + kernel 150 s at caps (35, 3, 19) (lowgd2, seed 77).
  File `T3/found/aes-sbox-a35-ad3-g144-gd18-52abeab6324f.circ.txt`.
- ~06:05 UTC: **35/3/143/18** (aes_check OK, new Pareto point; supersedes 144@18): level-1 walk (3 steps)
  on a 144@19 + kernel at caps (35, 3, 18) (lowgd4, seed 99). File
  `T3/found/aes-sbox-a35-ad3-g143-gd18-53d3d6a7b117.circ.txt`.

## 16. Final state (06:10 UTC; all T3 jobs stopped)

Goal F (G <= 138 at GD <= 26): **not reached**. Best at GD <= 26 is still 140@25 (known). Over all GD
the minimum G is 139 (NIST 139@27); nothing below it was found.
New A35 AD3 frontier points (all in T3/found/, aes_check OK, new on pin 3d80774):
  142@19, 142@20, 143@18 (plus 144@19 and 144@18, which these dominate). Before tonight the best
  were 144@20, 145@19 and 146@18.
Pool minima (lowgd pool): GD17 148, GD18 143, GD19 142, GD20-22 142.
What worked: the GF(4)-coordinate move (new level-3 choices) to leave the published basin, then
level-1 exchange walks + kernel polishes in the low-GD band. What did not: any kernel-only polishing
of the GD 24-27 frontier (0 gains in ~40 runs), joins between different coordinate choices, global
(4-point) coordinate changes (+8..+15 before polish), BP region re-synthesis.
