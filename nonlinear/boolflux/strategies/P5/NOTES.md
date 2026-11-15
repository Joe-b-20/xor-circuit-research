# P5: T05 AND-depth half (A <= 32, AD 6 / 5 / 4 / 3, G as close to 103 as possible)

Campaign 2026-11-15-targets, track P. Data: `~/xs-campaigns/2026-11-15-targets/P5/` (`specs/`,
`runs/`, `splice/`, `found/`). Reference: NIST `aes-sbox-a32-ad7-g103-gd32-xx71-10` (pin 3d80774).
Bars at start (LEDGER.md, coordinator 15:40): AD6 32/6/104/31, AD5 32/5/104/29, AD4 32/4/114/26;
AD3 at A <= 32 unknown.

## 0. Summary (best G, then GD, per AND depth at A <= 32; see the sections below)
- AD7: 103/32 (NIST; P4's half).
- AD6: 104 (dominated by the AD5 104/29).  **[C] no 103 at AD6 with the 103's top and bottom**
  (5-AND middle needs >= 21 paid gates at depth 4); any inversion-input basis: middle >= 19,
  so G >= 104 in P4's case S (section "Any inversion-input basis, depth 4").
- AD5: 104/29 (archive).  **[C] no 103 at AD5 with the 103's top and bottom**; with any
  inversion-input basis the middle needs >= 19, which with P4's top/pre/bottom bounds gives
  G >= 104 in P4's case S (caveats in the section).
- AD4: **111/25, 111/26, 112/22, 112/23, 113/20 (new or re-certified, certified lineages from
  NIST 117)**; bar was 113/20 (P3, uncertified) / 114/26 (archive).
- AD3: nothing at A <= 32; [C] impossible in the separated tower layout.
- Tools: invskel.py / invskel.c + cskel.py (exact inversion-middle skeleton search), blocksplice.py,
  splice_all.py, basisneed.py, lineage.sh / cjob.sh / rec.py (kernel lineages, recording).

## 1. Structure of the reference (facts, read from the files)

The 103 (AD7), NIST 104 (AD5), NIST 105 (A33, AD4) share the Boyar-Peralta tower layout:
top = 9 level-1 ANDs + linear forms (42 gates up to the four inversion inputs), middle = GF(2^4)
inversion + the 5 Karatsuba sums of its 4 outputs, bottom = 18 ANDs (each of 9 middle signals
times 2 top forms) + 25 linear gates. 103 = 42 + 18 (middle) + 43; NIST 104/AD5 = 42 + 19 + 43.

- 103 middle: 5 ANDs at relative AND levels 1,2,3,4,5 (chain), 8 linear + 5 sums = 18 gates.
- NIST 104 middle: 5 ANDs at levels 1,2,2,3,3, 14 linear = 19 gates.
- NIST 105 (A33) middle: 6 ANDs at levels 1,1,2,2,2,2 (depth 2).
- A32/AD4 circuits (NIST 117, ours 114) use a 6-AND depth-2 inversion and a 17-AND bottom that
  reuses a top product.

So: overall AD = 1 (top) + middle depth + 1 (bottom).  AD6 at 103 <=> a 5-AND middle of depth 4
costing 18 gates (with this top and bottom); AD5 at 103 <=> depth 3 at 18.

## 2. Exact skeleton search for the middle (`invskel.py`)

Model: inputs v0..v3 = t30, t31, t32, t33 of the 103 (tables from `invext.py`); targets = the 9
signals the 103 bottom multiplies (t36, t39, t40, t43 + sums t41, t42, t44, t45, t46); exactly 5
ANDs, each operand an affine form over inputs, constant and earlier ANDs; linear cost =
number of distinct required non-basis forms when each is one XOR/XNOR of two available signals
(exact for that case), else a greedy upper bound.  Pruning: rank argument (each AND lowers
dim((S+T)/S) by <= 1), cost lower bound (distinct forms) with `--maxcost`.

Results:
- **[C] depth 2: no 5-AND skeleton exists** (60 901 nodes, 0 leaves, `runs/skel_d2.log`).
  Case covered: any circuit over {AND, XOR, XNOR, NOT} with exactly 5 ANDs at AND depth <= 2
  computing GF(2^4) inversion (the search depends only on the span of the 4 outputs, so it
  covers every linear input/output basis).  Consequence: an A32 AD4 S-box cannot use the
  9 + 5 + 18 tower layout with a separate inversion block; it needs 6 inversion ANDs and a
  17-AND bottom (as NIST 117 / our 114) or a different layout.  Not a general bound on AD4 at
  A32.
- 103 prefix (a10, a11, a12 kept, last two ANDs free at depth <= 4): best middle 19 gates
  (7 skeletons), i.e. 104 at AD6 (= the archive bar) [C, within that prefix and cost model].
  Spliced into the 103 (`blocksplice.py`, staged builder): 7 circuits 32/6/104/32-33, aes_check
  OK (`splice/pre3_r*.circ.txt`); not better than the archive 104/31.

- Full depth-4 search, maxcost 18 (4 free inputs t30..t33), 15:52-16:51 UTC, 554 389 nodes,
  1 536 leaves passed the form-count bound, **0 with cost <= 18** (`runs/skel_d4_m18.log`).
  Caveat: in that run a leaf whose forms were not one-gate closable got a greedy upper bound,
  so a leaf with true cost #forms+1 could have been dropped; superseded by the d4p run below
  (exact up to one helper, proven bound otherwise).

### Model extensions and the C port (16:55-17:07)
- Paid inputs / boundary (`spec 'boundary'`, `*_d?p.json`): t32 = t27+t28 and t33 = t27+t29 are
  read only by the middle, so the honest budget is 20 gates with t32, t33 not free; boundary forms
  t27+t28, t27+t29, t28+t29 (and complements) cost one gate each; every subset U of them may be
  built up front (cost |U|).  U = {t32, t33} is exactly the 4-free-input model, so maxcost 20
  here covers maxcost 18 there.
- Leaf cost made exact up to one helper: kinds `exact` (one gate per form), `exact+1` (closable
  with one helper; all one-gate helpers tried), `lb+2` (neither, so cost >= #forms + 2, a proven
  bound).  A leaf is dropped only when its proven bound exceeds maxcost.
- `invskel.c` + `cskel.py`: C port of the same search (k = 4), 45x faster; checked against the
  Python on the 103 prefix test (identical cost multiset: 7 at 21, 66 at 22, 6 lb+2) and the
  depth-2 search (identical node count 60 901, 0 leaves).

### AD6 and AD5 at 103 in the 103 layout (decisive negatives, [C] in that case)
- **[C] depth 4, paid model, maxcost 20: 0 skeletons** (17:15-17:56, 13 347 253 nodes, 830 592
  leaves: 204 exact, 830 388 lb+2, none within 20; `runs/c_inv103_d4p_m20.log`).  Same case as
  the depth-3 result below.  So **no A32 AD6 circuit of 103 gates exists with the 103's top and
  bottom**; the best middle at depth 4 found is 21 (paid) = 104 total (the 7 cost-19 prefix
  skeletons, spliced: 32/6/104/32-33).  Together with depth 3: in the 103 layout every AND
  depth below 7 costs >= 104 gates.  The 103 gate is therefore tied to its 5-level inversion chain
  (with this top/bottom); a 103 or lower at AD <= 6 needs a different top, bottom or inversion
  input basis (P4 shows pre-inversion >= 15 for every basis with the 103's top values).

### Kernel runs on GF(2^8) conjugates (P3's method, files copied as p3_*.py)
- Screens (`p3_conj3.py`, proxy top BP + bottom Paar): AD5 104/29: identity 44, best other 47
  (lam 236 k0, lam 43 k4); AD6 104/31: identity 48, next 49 (lam 43 k4). [H] conjugation is not
  expected to help these two.
- cpipe1 (CPU 9, 17:57-18:19): AD5 104/29 conjugates lam 9 k4 (start 112@27) and lam 188 k0
  (113@29): gate cap GD36 300 s -> 108@23 / 108@25; mix cap 30 400 s (lam 9) -> 106@24, 106@26,
  107@26-27.  Nothing below the AD5 bar 104/29 or the archive 106/24.  Stopped at 18:19 for the
  compliance change (below); the AD6 conjugates were not run (AD6 at G 104 is dominated by the
  AD5 104/29 anyway).
- Compliance (18:20 note): from 18:19 every P5 kernel call uses kernel bfx-94a75e2c18 with
  `repair_keep 1` (p3_pdrive.py DEFAULTS), and P3's pdrive guard (best only inside A/AD caps).
  Earlier found/ files: gate stages started inside all caps (path_certified true); the m30 mix
  stage used osc repair without repair_keep (path_certified "unknown"); none of them is a strict
  or tradeoff result.

### AD4 at A <= 32, any GD (cpipe4.sh: conj3 screen -> per conjugate gate cap GD30 300 s ->
mix cap GD26 400 s; identity first)
- cp4a (CPU 9, from 18:17) on P3's 113/20 (`starts/ad4-113-20-p3.circ.txt`, sha256 db41c24e...):
  identity, gate cap 30, seed 1: **112@25 at 102 s, 112@24 at 302 s** [H, one run].
  `found/p5-cp4-ad4-113-20-p3-id-g30-a32-ad4-g112-gd24-1b0490fa03.circ.txt`, aes_check OK, new
  Pareto point on the pinned set; lowest G at A <= 32 AD4 (was 113/20).  Own stage: repair_keep 1,
  start inside A/AD and GD caps; **path_certified false (inherited from P3's 113/20, whose lineage
  had pull stages without repair_keep)**; to be rerun from a certified start.
  mix cap 26 from it: 112@24 (osc-repair), 113@23 (trb-bottom).
- cp4n (CPU 16, 18:28-18:57): a fully certified lineage of the same kind from the NIST 117@19
  itself (lams from P3's screen of the 117, copied): identity 115@26 (gate), 119@23 (mix);
  lam 188 k0: 115@23 / 115@27 (gate), **113@23** (mix); lam 9 k4: 118@23.  Conjugates of the 113/20
  (cp4a: lam 2k0 115@24-26, lam 167k1 116@27) were all worse than its identity.
- lin-cert113 (CPU 16, from 18:57; `lineage.sh`: rounds of gate cap 30 / mix cap 26 from the
  lineage best): from the certified 113/23: round 1 gate seed 31 -> 112@25 (162 s); mix seed 32 ->
  **112@24 and 112@22** (certified, aes_check OK, new Pareto points on the pinned set).
  `found/p5-lin-cert113-r1-mix26-a32-ad4-g112-gd22-6f3b39a3e3.circ.txt` (sidecar has the lineage).
  Whole path NIST 117 -> 112/22: ~23 CPU-minutes, every kernel stage repair_keep 1 and starting
  inside A32/AD4 [H: one lineage].
- lin-cert113 rounds 2-3: gate seed 33 -> **111@26** (19:14); mix -> 112@23; round 3 gate ->
  **111@25**, mix -> 113@23.  All certified.
- lin-cert112c (CPU 9, from 19:10, gate cap 26 / mix cap 22, from the 112/22): round 1 gate ->
  111@26 (another circuit); round 2 mix -> 113@20 (certified version of P3's tuple).
- The stopped uncertified lin112 (from P3's 113/20) had reached 111@25 at 19:08 (saved,
  path_certified false).

### Any inversion-input basis, depth 3 (AD5) (19:32-19:49, `invskel_c2`, `basisneed.py`)
- Relaxation (as P4-allM): all 15 non-zero linear forms of t30..t33 free, depth 3, maxcost 18:
  4 068 565 nodes, 453 888 leaves, **11 868 skeletons of cost 18** (8 160 exact, 3 708 exact+1)
  (`runs/c_inv103all_d3_m18.json`).  So the relaxation alone does not exclude AD5 at 103.
- `basisneed.py`: per skeleton, O = the pure-linear AND operands.  |O| = 4: 1 572, 5: 5 484,
  6: 4 812.  With |O| >= 5 any 4-form basis leaves >= 1 operand form to build: cost >= 19.  For the
  1 572 with |O| = 4 (independent), the exact cost with only B = O free: 19 (84) or 20 (1 488).
- **[C] With a basis B of span(t30..t33) delivered by the pre layer and every other linear form
  built by gates, a 5-AND depth-3 middle (exact 9 targets of the 103's bottom) costs >= 19.**
  This bounds the middle only.  The rest of the 103 is 18 (top) + 15 (pre) + 9 + 18 + 25.  P4
  (NOTES 2.2, 2.2b, 2.3): pre >= 15 for every inversion-input basis; every 17-gate top (no
  deadlines) forces pre >= 16 over all 840 bases; bottom = 25 exactly (transposition).  So in P4's
  case S (the 103's 9 level-1 ANDs and 18 output ANDs) top + pre >= 33 at any depth, and with this
  middle bound **an A32 AD5 circuit in case S has G >= 33 + 9 + 19 + 18 + 25 = 104** [C, case S,
  middle = 5 ANDs with the exact 9 targets, caveats below].  Not covered: a pre layer that delivers more than
  4 linear forms within its 15 gates (the 103's own boundary t27..t29 case is covered by the paid
  model, 0 at <= 20), other AND sets, complemented targets.
- Splicing the first 150 relaxed skeletons into the 103 (4 free inputs, extra forms by chains):
  32/5/106/31 at best (`runs/splice_all3.log`).

### Any inversion-input basis, depth 4 (AD6) (19:58-21:33)
- Relaxation, all 15 linear forms free, depth 4, maxcost 18: 12 573 781 nodes, 2 722 176 leaves,
  **25 998 kept: 48 at cost 17, 25 950 at 18** (`runs/c_inv103all_d4_m18.json`, 5 647 s).
- `basisneed.py`: |O| = 4: 4 944, 5: 11 826, 6: 9 228.  |O| = 4 with B = O: cost 19 (216 pairs)
  or 20 (4 536).  The 48 cost-17 skeletons all have |O| = 5; `basisneed5.py`: for each of their
  144 (skeleton, B in O) pairs the exact evaluation gives a proven bound >= 20 (no one-helper
  closure).  Every other (skeleton, basis) pair leaves >= 1 (cost 18) or >= 2 (cost 17) operand
  forms outside B.
- **[C] With a basis B delivered by the pre layer (other linear forms built by gates), a 5-AND
  depth-4 middle with the 103's 9 targets costs >= 19**, so in P4's case S an A32 AD6 circuit has
  G >= 104, same caveats as depth 3 (a pre delivering > 4 forms of span(t30..t33) in 15 gates;
  complemented targets; other AND sets / layouts).

### Late runs 19:45-22:52 (all repair_keep 1)
- AD4 lineages: lin-cert111 / lin-cert111w (caps 30/26, 36/30) and lin-certC (25/23) from the
  certified 111/25 and 112/22: plateau, re-found 111/25, 111/26, 112/22, 112/23, 113/20, 113/21.
  Fresh certified lineage lin-certB from the NIST 117 conjugate (lam 188): 113@25 -> 112@23 ->
  111@25 within 3 rounds (a second independent path to 111).  Conjugates of the 111/25
  (cp4c, lam 2 k0): 116 only.  Repeats ad4rep (mix cap 24 from 111/25; gate cap 32 from 112/22),
  5 seeds each: 111/26-30, 112/22-24, 113/21-22; nothing below 111 or 111 below GD 25. [H]
- AD5: lineage from NIST 104/30 drifts upward under cap 28 (106/27, 107/25); mix cap 29 / 28
  repairs of 104/30 and 104/29 lose 2 gates (106/26); gate cap 30 from a 106/26: 105/28, 105/29
  (dominated by NIST 105/26); gate cap 32 from NIST 104/30: 104/30 only.  The AD5 104 GD looks
  tight for the kernel [H].
- AD4 at 111 is a plateau for these operators in ~2.5 CPU-hours [H]; the overnight item P5-ad4lin
  uses more independent lineages from the NIST 117 conjugates.

### AD3 at A <= 32
In the separated tower layout (top AND level 1, middle, bottom one level) AD = 2 + middle depth,
so AD3 needs a depth-1 middle, impossible because every component of GF(2^4) inversion has
degree 3 [C, that layout].  An A <= 32 AD3 circuit would need a different (merged) structure;
published AD3 circuits use 35 ANDs.  Not attempted beyond this remark.

### Results of the exact searches (C port)
- **[C] depth 3, paid model, maxcost 20: 0 skeletons** (17:07-17:15, 4 138 165 nodes, 149 760
  leaves: 56 exact, 149 704 lb+2, none within 20; `runs/c_inv103_d3p_m20.log`).
  Case covered: the 103's top (everything up to t27..t31) and bottom (the 18 output ANDs and
  25 output XORs) fixed; a middle with exactly 5 ANDs over {AND, XOR, XNOR, NOT} reading
  t27..t31 (only through span(t30, t31, t27+t28, t27+t29)) and delivering the 9 signals the
  bottom reads.  Then the middle needs >= 21 gates at AND depth 3, so **no A32 AD5 circuit of
  103 gates exists in this layout; AD5 needs >= 104 here** (104 is known: NIST, ours 104/29).
  Not a general bound (other tops / bottoms / input bases / 6-AND middles are not covered).
  Also not covered: delivering a target complemented and absorbing the complement in the
  bottom ((~s)&p = s&p + p changes the bottom's linear layer); the model requires the exact
  9 tables.

Cost-model bug found and fixed 15:50: the first closure ignored levels (an AND operand could be
built from a later AND), so the first d4 run's leaf costs were optimistic; its LB pruning was
valid but it was restarted with the level-aware closure (stage l uses only signals of level
<= l; exact for the one-gate-per-form test).  The first builder (`blocksplice_v1.py`) built
operands greedily per AND and spent 24-25 gates where 19 suffice; replaced by the staged builder
that follows the same stages as the cost model (reproduces the 103 middle at 18 exactly).
