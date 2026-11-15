# P4: T05 gate-record half (A <= 32, AD <= 7, GD <= 32; goal G <= 102)

Campaign 2026-11-15-targets, track P, CPU 15 (+7, 8 from ~18:30). Code here; data in
`~/xs-campaigns/2026-11-15-targets/P4/` (`runs/`, `found/`). Reference: NIST
`aes-sbox-a32-ad7-g103-gd32-xx71-10` (pin 3d80774) = 32 AND + 61 XOR + 10 XNOR.
Labels: [C] = exact within the stated case only; [H] = heuristic / empirical.

**Summary.** No circuit below 103 gates.  The 103's linear layers are each exactly optimal for
its AND skeleton: top 18 at GD 32 (17 without a depth limit), pre-inversion 15, inversion block
13 XOR, bottom 25 (exact, by the transposition principle), and the joint bound
top + pre + inversion + bottom >= 71 holds at any depth (case S, section 2.6; also for every
4-input basis of the inversion interface), and over all 19,683 per-pair operand choices and
2,040 scaled-Frobenius variants.  GD < 32 at 103 is excluded in case S (all 6 18-gate inversion
blocks, earliest pre, optimal bottom).  Empirically (kernel on GF(2^8) conjugates, coordinator
tip) the lineages stop at 104 (best 32/7/104/27, new Pareto point, not a T05 class).  A 102 therefore needs a different inversion interface,
a different GF(2^4) / GF(2^2) representation, or a non-tower layout.

## 1. Anatomy of the 103 (facts, `layers.py`, `circ.py`)

Symbolic decomposition (every XOR signal = XOR of atoms x0..x7, a1..a32, plus a constant):
- **top**: 18 XOR gates, x-linear only.  They compute the 15 non-trivial AND operands of the
  9 level-1 ANDs (pairs (g_i, g'_i); 3 more operands are the inputs x0, x2, x7) plus 3 helpers
  t1 = x1+x4, t2 = x0+x5, t5 = x3+x5 (t2, t5 are also read by the middle).
- the **same 9 pairs** are reused by the 18 output ANDs: each inverse-side signal f_k multiplies
  both members of one pair (a13/a14 = t36 * {t16, x2}, ...).  Each top form is read by exactly one
  level-1 AND and one output AND.
- **pre-inversion**: 15 XOR gates from a1..a9 (+ x-linear injections) to the 4 inversion inputs
  t30, t31, t32, t33.  Product parts P30 = a1+a5+a6+a8, P31 = a1+a3+a5+a7, P32 = a1+..+a5+a8,
  P33 = a1+a3+a4+a9; x-parts X30 = x0+x1, X31 = x0+x5, X32 = x0+x1+x3+x4+x5, X33 = x4+x6+x7.
  10 gates merge product signals, 5 gates inject an x-linear top signal (t2, t5, x4, t15, t6) into a
  leaf product (t13, t20, t21, t23, t24).
- **inversion**: 5 ANDs (a10, a11, a12, a15, a18, one per AND level 2..6) + 8 XOR core + 5 XOR
  Karatsuba sums -> the 9 signals t36, t39, t40, t41..t46 read by the output ANDs.
- **bottom**: 25 XOR gates, 8 outputs from the 18 output products only (8 x 18 matrix in
  `runs/layers103/bottom.mat.txt`).
- 71 = 18 + 15 + 13 + 25.  Timing: the critical path runs top -> a5/a6/a8 -> pre -> the serial
  inversion chain (a10 -> a11 -> a12 -> a15 -> a18) -> a31/a32 (level 22) -> the serial output chain
  y7 -> t61 -> t62 -> y3 -> t63 -> y0 -> y1 (level 32).  The top forms t1..t18 have zero slack.
- the 9 level-1 products and the 8 inputs (and 1) are linearly independent as functions (rank 18),
  so every signal's (product part, x part) decomposition is unique.

## 2. Exact layer tests (fixed AND gates)

### 2.1 Top layer [C]
`topenum.py`: if a top layer has (#forms + H) gates, its value set is the forms plus H helpers;
feasibility and earliest levels of a value set are order-independent (closure fixpoint), so
"can the 15 forms be computed in 15 + H gates within the deadlines" is decided exactly by
enumerating helper sets.  Deadlines: required times of the forms from the fixed rest of the 103 at
GD 32 (`block.required`).
- H = 1, 2: **0 feasible sets at GD 32**.  So with every other gate of the 103 fixed, the top
  needs 18 gates. [C]  (sanity: the 103's own helper triple is feasible; without deadlines 17
  two-helper sets exist, all containing x1+x4; XORFlux also finds 17-gate tops, depth 9-12.)
- Lateness of the 17 two-helper tops (`toplate.py`, runs/toplate-h2.jsonl): every one is late
  by >= 2 levels on some form; best {x1+x4, x0+x5}: t12, t16, t17, t18 late by 2 (so a 102 by a
  17-gate top needs about 2 levels recovered elsewhere).

### 2.2 Pre-inversion [C]
`preinj.py`, `prebasis.py`.  Projection argument: deleting the x-parts turns the layer into an XOR
circuit for P30..P33 over a1..a9 (gates fed by an x-linear signal become copies), so
pre >= amin + (number of injection gates).  X = R S (R = 0/1 reach matrix of the injection points
to the 4 targets), rank X = 4, so >= 4 injections, and with exactly 4 the injected values are
forced by the 4 reach vectors.
- amin = 10 (SAT: 8, 9 steps UNSAT; 10 SAT).  Also by the transposition principle:
  amin(P) = amin(P^T) + 9 - 4 and P^T has 9 distinct non-zero columns, at most 4 of them unit
  vectors, so amin >= 10 for **every** basis of the inversion inputs.
- 4 injections with values in the 103's top values (26 signals): **0 of 15 reach-vector bases**
  work for t30..t33, and 0 for **any of the 840 bases** of span(t30..t33) (`prebasis.py`).
  With 5 injections the 103's own pattern is found (sanity).
- => pre-inversion >= 15 for every choice of the 4 inversion inputs within span(t30..t33)+1,
  when the injected signals are among the 103's top values; any other x-linear signal costs an
  extra top gate. [C, that case: same 9 level-1 ANDs]

- Reach vectors and transposition (`prereach.py`): the reach vector of a node or edge of a
  product-part circuit is a value carried by the transposed circuit.  For a 10-gate circuit the
  transposed one has exactly 5 gates, which must be the 5 non-unit columns of P^T, so the only
  reach vectors available are the units and the 9 columns {1111, 0100, 1110, 1100, 0111, 0001,
  0010, 0101, 1000} (bit order t30, t31, t32, t33).  Sanity: the 103's 5 injection points have
  reach 1111, 1100, 0001, 1000, 0101, all in that set.

### 2.2b 17-gate tops (no deadlines) [C]
The route "17-gate top + 15-gate pre" (= 102 at some GD) needs a 5-injection pattern.  For each of
the 17 two-helper tops, with Avail = inputs + forms + helpers (`good5.py`, any reach vectors):
16 tops admit no 5-injection pattern at all; only {x1+x4, x0+x5} admits one, and only with reach
vectors {0001, 0100, 1000, 1101, 1110} (exhaustive list, 1 pattern).  1101 = {t30, t32, t33} is
not a column of P^T, so no 10-gate product-part circuit provides it.  => over every 17-gate top,
the pre-inversion (targets t30..t33) needs >= 16 gates, total >= 103. [C, case: same 9 level-1
ANDs, inversion inputs t30..t33, injected values from that top]  (The direct SAT check of the
same question, `prenew.py` 15 steps, did not finish in 6 min and was stopped.)
`prereach.py top17` repeats this over all 840 inversion-input bases: 0 of 17 tops x 840 bases
admit a pre-inversion of <= 15 gates (runs/prereach/top17.jsonl). [C]

### 2.2d Top + pre-inversion jointly at GD 32 [C]
`prereach.py top18` and `relaxc.py`: every 18-gate top (15 forms + 3 helpers, exhaustive) meeting
the deadlines, with a pre-inversion of 14 = amin + 4 gates for some inversion-input basis.  A
14-gate pre needs a basis of V = span X inside Avail (the same V for every basis M).
- 103 deadlines at GD 32: 16 tops, cover rank <= 2: 0 x 840 bases. (runs/prereach/top18.jsonl)
- relaxed deadlines (a level-1 AND only has to reach the pre targets that contain it:
  level <= min req(t_j) - 1; output ANDs keep the 103's times): 17-gate tops: 0 feasible;
  18-gate tops: 111 feasible, cover rank histogram {0: 82, 1: 27, 2: 2}, none 4.
=> **top + pre-inversion >= 33 gates at GD <= 32** [C, case: the 103's 9 level-1 ANDs (same
operand pairs), inversion inputs = any basis of span(t30..t33) + constants, injected x-signals
from the top, inversion / output ANDs / bottom timing as in the 103].
Also: the AD5 104@29 (its own level-1 ANDs and pre targets t25, t33, t39, t42) over its 11
17-gate tops meeting its GD 32 deadlines x 840 bases: no pre of <= 15, so no 103 at AD5 by
re-injecting its pre [C, same kind of case] (runs/prereach/c104-top17-gd32.jsonl).

### 2.2c Per-pair operand choices (3^9) [C for the top, H for the bottom]
For pair (g, g') the level-1 AND can be g g' (A), g (g+g') = a + g (B) or g' (g+g') = a + g' (C);
the output ANDs then use the same two forms (bottom columns change by a column operation) and the
pre x-parts shift (`pairscan.py`).  Of 19,683 choices, 1,322 have rank X' = 3 or cover the
x-part span by forms; 67 were selected (rank 3 with cover >= 2, or 15 forms covering V).
- top at GD 32 deadlines, 18 gates (`topenum.c`, exhaustive 3-helper sets): feasible only for
  the 103's own choice; 0 feasible sets for each of the first 28 other selected choices (the
  remaining 39 were not run).  The 103's choice: 16 feasible helper triples, but Avail meets
  V = span X in rank <= 2, so no 4-injection pre over any of them. [C]
- bottom XORFlux 30 s on 8 rank-3 choices: 27-29 gates (vs 25). [H]
So changing operand pairs costs >= 1 top gate and (where tried) >= 2 bottom gates.

**Exact version over all 19,683 choices (GD free)** [C]: `pairexact.py` (bottom exact by
transposition + closure, helpers <= 2, else bound nt + 3 + n - 8; runs/pairexact-h2.jsonl:
the exact bottom ranges 24..29, 24 for 4 choices, 25 for 170), then `stage2.py` (top exact =
forms + least feasible helper count, pre >= 10 + rank X' (+1 unless some feasible top has
rank(Avail meet V) >= rank X'); runs/stage2-gd99.jsonl, 21,772 enumerator calls): only 4 choices
reach top + pre + bottom <= 57: 000000000 (the 103), 021021210, 100000000, 120000010.  Each was
refined by the exact pattern search over all 840 inversion-input bases (`choicepre.py`): no
pre of the needed size (14 for 021021210 with its 18-gate tops; 15 for the 17-gate tops of the
other three).  => **every operand-pair choice has top + pre + bottom >= 58, i.e. G >= 103 at any
GD**, with the 103's inversion block. [C, case: per-pair choices A/B/C as defined above]

### 2.3 Bottom: exactly 25 [C]
Transposition principle (exact for XOR circuits with cancellation, no zero rows / columns):
XOR(M) = XOR(M^T) + (#columns - #rows).  M = the 8 x 18 bottom matrix, so XOR(M) = XOR(M^T) + 10,
and M^T computes the 18 columns (8-bit vectors over y0..y7) from the 8 unit vectors.  4 columns
are units (a14, a22, a26, a30), 14 are distinct non-units, so M^T needs 14 + H gates, H helpers.
Exhaustive closure (`minh.c` / `topenum.c`): H = 0 infeasible, H = 1 feasible with exactly one
helper (0b10111111).  So **the 103's bottom needs exactly 25 XOR gates** (no depth limit), and by
the projection argument every circuit using these 18 output products has >= 25 gates whose
value involves an output product. [C, case: these 18 output ANDs]  (XORFlux v8, 300 s: 25 too;
uniform depth caps: 26@8, 27@6 in 150 s [H].)

All 25-gate bottoms and their timing (`bottomT.py`) [C]: the transposed circuit's value set is
forced (units + 14 columns + 191), and only 4 DAG realisations of it exist.  Transposing each
and arranging every multi-input XOR node optimally for the 103's product arrival times
(join the two earliest signals first), the best latest output level is 32 (levels
32, 31, 28, 29, 32, 29, 25, 26 for y0..y7; the 103 has 31, 32, ...).  So with the 103's top,
pre-inversion and inversion timing, no 25-gate bottom gives GD < 32.  Also exact: the last
12 bottom gates (t59, y7, t60, t61, t62, y2, y3, y5, t63, y0, y4, y1) cannot be replaced by 12
XOR gates meeting GD 31 (`linwin.py`, UNSAT in 700 s).

### 2.5 GD 31 at 103 [C, cases]
- top: no 18-gate top meets the GD-31 deadlines of the fixed rest (`topc.py`, 0 sets).
- bottom: no 25-gate bottom finishes by 31 with the 103's arrivals (above).
So a 103 at GD <= 31 in this skeleton needs a faster pre-inversion / inversion at equal cost.

### 2.3b The scaled-Frobenius family (2,040 skeletons with the 103's inversion block) [C]
`family.py`, `famtop.py`.  S(x) = A x^-1 + c; with y = L x, L(x) = lambda x^(2^k) (lambda in
GF(2^8)*, k = 0..7), x^-1 = N y^-1, N(z) = (lambda z)^(2^(8-k)).  Running the 103 on y instead of
x keeps the inversion block, the 9 + 18 AND structure and the product parts P, and changes the
top forms to g o L, the pre x-parts to X o L (rank stays 4, so pre >= 14, and 14 needs
Avail meet V of rank 4), and the bottom to T M with T = A N A^-1.  For all 2,040 (lambda, k):
bottom exact (transposition + closure, helpers <= 3 where needed), top exact without depth limit
(helper sets <= 2-3 where needed).  Bound top + pre + bottom >= 58 for every member, met only by
the identity (17-18 + 15-16 + 25).  Closest others: (236, 0): 16 forms, bottom 25, top >= 19;
(133, 4): top 17, bottom 27; seven members with bottom 27-28 have top > nforms + 1.
=> no 102 in this family at any GD (with the 13-XOR inversion block). [C, that family]

### 2.4 Inversion block: no 17-gate block [C, P5's skeleton model]
P5's exhaustive skeleton search (`strategies/P5/invskel.py`, frozen copy sha256 9222a181...,
spec `inv103_d5.json` = inputs t30..t33, the 9 output forms with their constants, exactly 5 ANDs,
AND depth <= 5 inside the block, i.e. AD <= 7 overall) with `--maxcost 17`: 142,693 nodes,
**0 leaves**, 1,484 s (runs/inv17/run.log, 16:45-17:10 UTC).  Model: every AND operand is an affine
form of inputs, constant and earlier ANDs; cost = 5 ANDs + number of distinct required
non-trivial forms (each needs its own gate), used as a lower bound for pruning, so 0 leaves means
no block of <= 17 gates.  Sanity: with the 103's first two ANDs as prefix and maxcost 18 it finds
6 cost-18 skeletons, among them the 103's own (L5 = aeb0 & b4cc = t40 * t36).
Case: inputs exactly t30..t33.  **Every input basis** [C, same model]: the relaxation with all 15
non-zero linear forms of t30..t33 free (`run_allM_v2.sh`, 2 shards, CPUs 8 and 7, 17:57-20:38 UTC,
891,797 + 857,061 nodes) keeps 48 skeletons of relaxed cost 17; re-costed for each of the 840
4-input bases (`evalkeep.py`; lower bound 5 + number of distinct required non-bare forms) every one
needs >= 18 gates in every basis (runs/inv17/evalkeep_allM.jsonl).  A real block with inputs M t of
<= 17 gates would be a relaxed leaf of cost <= 17, so **no 17-gate block exists for any 4-input
basis of span(t30..t33)**.  (Not covered: blocks that read more than 4 linear inputs.)
My own truth-table SAT encodings (`exact.py`, `exact2.py`) did not finish a 13-step sanity in 300 s.

All 18-gate blocks (`runs/inv17/m18_chain.sh`, same model, maxcost 18; 554,965 nodes, 2,112
leaves, 7,321 s, 18:16-19:38 UTC): **exactly 6 skeletons cost 18**, all sharing the 103's first
three ANDs (L1 aaaa&cccc, L2 7878&ff00, L3 0f77&2d2d) and differing in L4 (661e / 99e1) and L5.
[C, P5 model, inputs t30..t33, AND depth <= 5]  Spliced into the 103 (P5's builder, frozen copy)
and with the bottom re-timed optimally (`rebottom.py`, all 25-gate bottoms): GD 32, 33, 32, 33,
34, 33 (runs/inv17/rebottom18/).  Exact timing (`blocktime.py`): in an 18-gate realisation every
required form is one XOR of two values of the skeleton's value set, so the closure fixpoint gives
the earliest level of every block output; with the block inputs at the elementwise-earliest levels
any 15-gate pre over any 18-gate top can deliver (t30..t33 = 9, 8, 9, 9; `preT.py --tops all`,
runs/preT-min-all.jsonl) and the optimal 25-gate bottom, the best GD over the 6 skeletons is
**32** (runs/inv17/blocktime-9899.jsonl).  => **no 103 at GD < 32 in case S** [C, P5's cost model for
the block; 17-gate tops cannot meet even the relaxed GD-32 deadlines].

### 2.6 Conclusion for the 103 skeleton [C, case S]
Case S: the 103's 9 level-1 ANDs and 18 output ANDs (same operand functions), an inversion block
with inputs t30..t33 and the 103's 9 output forms.  (Injected x-signals are top values by the
class partition; a gate whose product parts cancel only re-routes x-parts already injected; it
costs a gate plus an injection and cannot beat the direct pattern bounds.)
Then XOR count = top + pre + inversion + bottom >= 33 + 13 + 25 = 71 at ANY gate depth
(top + pre >= 33: sections 2.2b-2.2d, GD-free version: all 4,119 18-gate tops have
rank(Avail meet V) <= 3, so pre >= 15; all 17-gate tops force pre >= 16), so **G >= 103 in case S,
and the 103 is optimal there**.  For GD < 32 at G = 103 in case S: no 18-gate top meets GD-31
deadlines with the 103's pre; no 15-gate pre meets GD-31 inversion-input deadlines over any
18-gate top at all (`preT.py --tops all`: 4,119 tops, 35 (top, injection solution) pairs x 6
transposed realisations, best: t30 late by 1; runs/preT-gd31-all.jsonl); 17-gate tops miss even
the relaxed GD-32 deadlines (relaxc H=2: 0); no 25-gate bottom finishes by 31 (2.3).  So GD < 32
at G = 103 in case S needs an inversion block with different timing (m18 chain, see STATUS).
Extensions proved: all 19,683 operand-pair choices (2.2c), complemented operands (N9 in
NEGATIVES.md), the 2,040 scaled-Frobenius skeletons (2.3b).  Not covered: other
inversion-input bases for the block (prepared: run_allM.sh), GF(2^4)/GF(2^2)-level basis
changes (they change the inversion block), and circuits outside the 9 + 5 + 18 tower layout.

## 3. Runs log
(see STATUS.md)

## 3b. GF(2^8) conjugates + kernel (coordinator tip, after P3) [H]
The conjugates x -> lam x are the k = 0 members of the family in 2.3b: their skeletons satisfy the
same exact bound (top + pre + bottom >= 58 with the inversion block kept), but the kernel may
change AND operands, so this is an empirical test outside case S.  Tools: copies of P3's conj.py,
bottom.py, mkconj.py, pdrive.py in this folder (headers give the P3 sha); pdrive copy has
repair_keep 1 added (COMPLIANCE-1820).  `runs/conj/conjrun.sh START TAG LAMBDAS` = mkconj (BP top +
trb), pdrive gate 300 s, pdrive trb 300 s, caps A32 AD7 GD32 (starts inside all caps, so no state
leaves A/AD; kernel bfx-593fa798f5 for these stages).  lam chosen by the exact family score
(236: 16 forms + bottom 25; 93; 176; 188 = P3's).
- lam 236: start 114@27 -> gate 32/6/106/27 -> trb **32/7/104/28** (new Pareto point on the pinned set,
  not a T05 class: G 104) found/p4-conj236-a32-ad7-g104-gd28 (path_certified true).
- lam 93: 117@28 -> 107@32 -> 107@28.  lam 176: 115@30 -> 105@27 -> 104@29.  lam 188: 112@27 ->
  105@29 (the first lam 176 trb / lam 188 runs failed at 18:18 because the old kernel rejects the
  repair_keep key; rerun with bfx-94a75e2c18; failed dirs kept in runs/conj/failed-oldkernel/).
- 104@AD5 (archive, 29) conjugates: lam 236: 112@30 (AD5) -> 107@25 -> 106@27; lam 93: 115@27 ->
  108@30 -> 108@29; lam 1 (control, no conjugation): 104@29 -> 104@29.
- deepen of the lam 236 lineage (r1-r3, 10 min stages): 104@28 -> **104@27** (r2 mix, saved
  found/p4-deep236-a32-ad7-g104-gd27, new Pareto point on the pinned set), then flat for 20 min.
  [H] reading: the conjugate lineages settle at 104, which is the exact floor of their skeletons
  plus one (2.3b: lam 236 has top >= 19), so the kernel did not leave the skeleton family.
- more lambdas of the 103 (gate 300 s + trb 300 s each): 2: 107@27; 24: 105@27; 123: 106@28;
  141: 106@31; 88: 106@26; 92: 106@29.  104@AD5 conjugates: 176: 105@26 (= NIST 105@26);
  188: 107@28; 2: 107@26; 24: 106@29; 186: 106@28.
- deepen of the lam 176 lineage (104@29, 4 rounds x 2 stages x 600 s, repair_keep 1): 104@27 at
  r1, then flat to the end (21:36).
Total: 13 conjugates of the 103, 8 of the 104@AD5, ~5 CPU-h; nothing below 104 at AD <= 7. [H]
`deepen.sh` continues a lineage: mix --cap 31 --relax 1 (osc at cap 32, so every retained state has
GD <= 32) and gate --cap 32, kernel bfx-94a75e2c18 with repair_keep 1.

## 4. What a 102 would need, and the next research step (proposal)
Within the 9 + 5 + 18 tower layout the gate count splits exactly into
top + pre + inversion + bottom (+ 32 ANDs), and every term now has an exact (or exhaustive)
evaluator: top = closure enumeration over helper sets (`topenum.c`, with or without deadlines),
bottom = transposition + closure (`minh.c`), pre = transposition (amin) + injection patterns
(`prereach.py`), inversion = P5's skeleton search (`invskel.py`).  So any alternative skeleton
can be scored exactly in seconds to minutes, except the inversion term.
The skeletons that are not yet covered are the other rank-9 decompositions of the norm
x -> x^17 (the 9 level-1 ANDs; [C] 9 is the minimum, track C) paired with rank-18 decompositions
of (delta, x) -> delta x^16 that share the 18 x-side forms (as the 103 does), i.e. other
GF(2^4)/GF(2^2) representations and other Karatsuba-type form sets.  Proposal: enumerate those
decompositions up to symmetry, score top + pre + bottom exactly with the tools above, and run the
inversion search only for skeletons whose top + pre + bottom <= 57.  A 102 exists in that family
only if some skeleton reaches top + pre + bottom + inversion XOR <= 70.
