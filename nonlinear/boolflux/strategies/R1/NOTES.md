# R1: window exact resynthesis (hub operator `wres`), 2026-11-15

Code: `wres.py` (windows, Boolean relation, SAT synthesis, splice), `op_wres.py` (hub operator, common
CLI), `calib.py` (per-window calibration), `test_wres.py` (positive controls).
Data: `~/xs-campaigns/2026-11-15-study/R1/`.

## Method

1. **Window** W: a convex set of gates (closure W := W u (TFO(W) n TFI(W)) until stable), 3..maxg (9)
   gates, <= K (8) inputs, 1..4 outputs.  Strategies: `and` (an AND and its operand XOR trees, growth
   stops at ANDs with p 0.8), `pair` (two ANDs sharing an operand or an operand's operand), `reconv`
   (fan-in-only growth from a random gate = a cut cone), `crit` (growth along gate-depth-critical
   gates), `x` (random growth).  Depth modes always use `crit` with up to 30 picks.
2. **Deadlines.** Arrival (gate level, AND level) of window inputs is unchanged (convexity).  Required
   times of window outputs: backward pass with W's internal edges removed, caps D (gate depth) and DA
   (AND depth).  Everything outside W and TFO(W) must already meet the caps (checked; 'outside'
   otherwise); then a replacement meeting the output deadlines meets the caps for the whole circuit.
   Modes: `cost` (D, DA = the job caps = input's own GD, AD), `gd` (D = GD - 1), `ad` (DA = AD - 1).
3. **Care set / Boolean relation.**  For each of the 2^m output vectors v, simulate TFO(W) with the
   window outputs forced to v (all 256 inputs bit-parallel): ok_v(x) = every primary output correct.
   Projected to window-input patterns (allowed at pattern t = allowed at every x giving t).  This is
   the exact multi-output observability relation (the kernel uses single-signal ODCs); `--no-odc`
   keeps only the original output vector (controllability care set only).  Patterns allowing every
   vector are dropped.
4. **SAT** (pysat CaDiCaL 1.9.5, conflict budget per call): chain of <= r steps over {AND, XOR, XNOR}
   plus NOT as XNOR with a constant-0 node; seqcounter cardinality for AND count <= amax; order-encoded
   gate and AND levels with input arrivals and output deadlines; output selection per window output
   (window inputs allowed as wires, not for primary outputs fed by primary inputs); colex symmetry
   breaking between consecutive independent steps; patterns added lazily (CEGAR).  Query plan for
   objective with A before G: (aW - 1 ANDs, gW + 1 steps) with p 0.5, then (aW, gW - 1) [depth
   modes: (aW, gW)], each SAT result followed by r := (used steps) - 1 until UNSAT/unknown.
5. **Splice**: non-W gates outside TFO(W), then the chain, then TFO(W); dead gates removed (window
   input cones that lose their last reader die too); duplicate-function merge (kept if not worse);
   output tables compared with the input circuit on all 256 inputs.  Adopted if the objective key
   improves under the caps, or (p `--sideways` 0.3) equal key with a new structure; every adopted
   circuit the archive would place is a candidate.

## Results

### Positive controls [H]
- Full adder (sum, carry; 3 inputs): r=4/amax=1 UNSAT, r=5/amax=2 SAT (5 gates) - consistent with the
  known 5-gate XAG.
- 3-XOR detour injected into 8 front circuits (s = a^b replaced by ((a^d)^b)^d): the window on the 3
  detour gates is resynthesised to 1 gate in 5-13 ms, splice restores the original (A, AD, G, GD) in
  8/8 (with and without ODC).  Random windows (20 s/circuit) did not find the detour (0/6): the
  window hit rate on ~130-gate circuits is low.

### Calibration on the archive front (snapshot snapcal, ~00:15 UTC)
`calib.py`, one try_window per window, cost mode, budget 30000 conflicts, 10 s/window, seed 5;
CPUs 17/18 were shared with stray hub kernel jobs 00:19-00:25 (coordinator), so the times are slowed.

| run | windows | unsat | unknown | no window | improved | mean g / k / o / P |
|---|---|---|---|---|---|---|
| front, ODC relation (cal2-odc) | 156 | 107 | 35 | 14 | 0 | 5.1 / 5.7 / 3.6 / 49 |
| front, care set only (cal2-noodc) | 174 | 124 | 36 | 14 | 0 | 5.0 / 5.7 / 3.6 / 49 |
| non-front cell minima, ODC (cal3) | 77 | 38 | 32 | 6 | 1 | 5.8 / 6.2 / 3.5 / 64 |

- By window size (front, ODC): g = 3-4: 58/58 unsat; g = 5: 29 unsat, 5 unknown; g = 6: 16 / 10;
  g = 7: 4 / 7; g = 8-9: 0 / 13.  [C, per window]: an 'unsat' window is exactly optimal for its
  query: no chain with (aW, gW - 1) [and, where tried, (aW - 1, gW + 1)] over {AND, XOR, XNOR, NOT}
  realises its Boolean relation within the output deadlines.  This covers only those windows (with
  their fixed inputs/outputs), not the circuit.  [H]: front circuits look window-optimal up to ~6
  gates, consistent with the kernel's 0-3-gate ODC resubstitution covering that range.
- 78% of the window time went to 'unknown' queries (budget exhausted), mostly g >= 7 and the
  AND-reduction query (aW - 1 ANDs: 43 unsat, 28 unknown, 0 sat).  -> operator default budget 8000.
- The one improvement (cal3): non-front 32/6/105/33 -> 32/6/104/33 (8-gate window, 7 inputs,
  4 outputs, 1 AND; plan 0/9 unknown, 1/7 sat, 1/6 unknown).  Dominated by the front; shows only
  that the pipeline produces real savings.
- MFFC windows (single-output cones) are tiny here (61% have 3 gates): XOR sharing is heavy, so
  windows of useful size have 3-4 outputs.
- smoke1: op_wres 90 s on front 28/4/131/23: 62 windows (all modes), 0 candidates.

## Versions
- v1 (A/B ab1, frozen-ab1): as in Method; budget 8000, modes cost 0.55 / slack 0.25 / gd 0.15 / ad 0.05
  (slack = every zero-slack window output must get earlier at equal cost; adopted when the number of
  gate-depth-critical gates falls), sideways 0.3, all windows logged to JOBDIR/windows.jsonl.
- v2 (op_wres2.py = op_wres.py with --explore 0.7 --sideways 1.0 --polish-share 0.4 --npolish 2): cost
  windows that find nothing better also ask for an equal-cost alternative (aW, gW) (one SAT call);
  every new structure (set of gate functions differs) is adopted; the last 40% of the job polishes the
  final and one random adopted circuit with the gate kernel (hub ops._kernel, op_polish settings).
  If nothing was adopted the job keeps doing windows (no polish of the unchanged input).
  Single-allowed-vector patterns are encoded as units (fewer clauses; same constraints).

## A/B ab1 (v1), 00:25-01:26 UTC [H]
Snapshot ab1-snap (long @ t=1794702311 ~00:25 UTC; 2179 records, 438 cells, front 79), CPU 17 base /
CPU 18 test, 1 h each, seed 8, nursery 0.3, ad3_share 0.3, wres --seconds 60 (frozen-ab1).
`hub/compare2.py ab1-snap base=ab1-base:1 test=ab1-test:1 --check` (ab1-compare.json):

| arm | CPU-h | admissions | new frontier points | not dominated by other |
|---|---|---|---|---|
| base | 1.02 | 24 | 0 | 0 |
| base + wres | 1.01 | 14 | 0 | 0 |

- wres: 5 jobs, 293 CPU-s, 0 admissions, 583 windows (cost 162 unknown / 152 unsat; slack 105 / 73;
  gd 42 / 36; ad 8 / 1), not one SAT answer (no improvement, no equal-cost shallower alternative).
- Verdict: tie at 0 new points, no distinct new points -> NOT adopted.  Both arms found nothing new in
  1 CPU-h (earlier hub A/Bs had 1-2 points per arm-hour on older archive states; at this state 1-CPU
  arms find little).  The compare --check found no points to verify.

## A/B ab2 (v2 = op_wres2.py), 01:26-02:27 UTC [H]
Snapshot ab2-snap (long @ t=1794705986; 2299 records, 455 cells, front 85), otherwise as ab1; wres2
--seconds 60 (frozen-ab2).  `compare2.py ... --check` (ab2-compare.json):

| arm | CPU-h | admissions | new frontier points | not dominated by other |
|---|---|---|---|---|
| base | 1.01 | 15 | 0 | 0 |
| base + wres2 | 1.00 | 8 | 0 | 0 |

- wres2: 9 jobs, 524 CPU-s, 0 admissions; 524 windows: cost 123 unknown / 117 equal / 42 unsat, slack
  73 / 63 (unknown / unsat), gd 39 / 45, ad 12 / 10.  18 equal-cost alternative structures adopted
  (plateau moves); the 13 kernel polishes of them all returned the input metrics.
- Verdict: tie at 0, no distinct points -> NOT adopted.  Coordinator note (L1, [C] count): twenty
  1-CPU-h blocks of one configuration gave 0/1/2/4 front admissions in 11/5/3/1 blocks, so these
  A/Bs cannot separate configurations anyway; the fixed-target study below is the better measure.

## Fixed-target study on goal-near tuples (coordinator's measures), 02:27-02:56 UTC [H]
Snapshot goalsnap (long archive after the hub stopped; 2311 records, 85 front).  Targets: 25 front
circuits at the goal-near tuples 28/4/131/23, 28/4/133/20, 29/4/130/22, 28/5/127/22, 28/5/130/19,
32/4/116/20, 32/4/119/18, 33/4/108/19, 32/5/104/29, 35/3/140/25, 35/3/141/24, 48/4/151/11, 43/4/141/12
(two structures per tuple where available).
- (a) per-job improvement rate: 28 op_wres2 jobs of 60 s (1625 CPU-s, 1562 windows, 51 equal-cost
  structures adopted, 41 kernel polishes of them): 0 / 28 jobs strictly better under the target's own
  caps; 0 candidates at all.  (goal/jobs.jsonl)
- deep.py, windows 6-10 gates with >= 2 ANDs, 400k conflicts, then the A-only variant (deadlines from
  GD + 8, AD + 1 with p 0.3, up to gW + 3 steps, K 9, windows from 4 gates, 150k conflicts): 44
  windows, 45 queries unknown, 3 unsat, 0 sat (1190 s).  SAT cannot settle AND-reduction queries even
  for 4-gate 2-AND windows once the step count and the depth deadlines are loose.  -> replaced by the
  algebraic check mc1.py (next section).

## mc1: algebraic window AND removal (mc1.py), 02:48-03:05 UTC
Exact SAT could not settle AND-reduction queries, so the AND count is attacked algebraically.  Window W
(convex, 2-4 ANDs, <= 10 inputs, <= 16 gates, <= 6 outputs; seeds = an AND and 1-2 ANDs within two
steps, growth stops at further ANDs with p 0.8), outputs t_h on the controllability care set.
L = span(1, window inputs), R = span(t_h mod L), r = dim R (canonical reduction mod L).
- [C, per window and care set] any circuit with m ANDs over the window inputs has its outputs in
  L + span(q_1..q_m), so r > aW - 1 => no (aW - 1)-AND rebuild of that window exists ('rank').
- r <= aW - 1: every flat product a*b (a, b affine over the inputs; mod L the constants drop out) is
  enumerated (Gray code, <= 2^19 pairs); success if products with residues in R span R ('removed'),
  else 'no_flat' (exhaustive for flat products only; AND-of-AND rebuilds not covered).
- Hits rebuilt with depth-balanced XOR trees, spliced, merged, verified on all 256 inputs (AND depth
  may change).  ~5 ms per window.
- Positive control: AND(a,b) replaced by AND(a,b^d) ^ AND(a,d) in 5 front circuits: all 5 restored to
  the original metrics.

Runs on the whole archive (static after the hub stop; 2311 records): A <= 29 (322 circuits) 23 098
windows; A 30-35 (1516 circuits) 15 730 windows.  An earlier run (mc1v0, 2-AND windows only, non-
canonical reduction) found the first hit: join product 826bcab90d23 29/5/127/30 -> 28/5/125/27
(aes_check OK, dominated by NIST 28/5/124/27).
| set | windows | rank | no_flat | removed |
|---|---|---|---|---|
| A <= 29 | 20 070 (first count) | 19 423 | 628 | 19 |
| A 30-35 | 13 125 (first count) | 12 541 | 527 | 57 |
- Distinct A-1 results (all verified): 24 with A = 28 or 29, ~60 with A 32-34, e.g. 29/4/136/24 ->
  28/4/132/22 (4a9ce43fe1aa), 29/5/134/20 -> 28/5/130/20, 34/4/112/24 -> 33/4/108/21, 33/6/111/28 ->
  32/5/107/23.  Every one is dominated by the archive front or NIST [H, checked with judge_found.py].
- Source circuits are mostly seeds/ingests/join products, i.e. circuits whose AND count was never
  minimised locally; front circuits rarely have removable flat windows (bed0a1b6d571 30/4/132/21 ->
  29/5/140/22 and d707dd6a9da6 34/4/134/13 -> 33/4/138/15 are front sources, results dominated).
- Kernel polish (45 s, own caps) of the A = 28/29 results (polish_found.py, goal/pol29.log): the best
  28/4 ones reach 28/4/134/21 (two structures), 28/4/133/23, 28/4/134/22 - one gate and one level
  from the front (28/4/133/20, 28/4/132/22, 28/4/131/23); none new.
- Join products (jointest.py, 15 min, 424 joins of random front pairs): 61 (14%) had removable
  ANDs (up to 6 removed in a chain), only 1 became placeable (32/6/120/30 -> 31/6/117/29), none new.

## seq2: sequential 3 -> 2 AND check (seq2.py), 03:23-03:31 UTC
For mc1's 'no_flat' windows with aW = 3 and output rank r = 2: a 2-AND rebuild has outputs in
L + span(q1, q2); since r = m = 2, res(q1) lies in R, so q1 ranges over the (enumerated) flat products
with residue in R; q2 = (alpha + q1) * beta or (alpha + q1) * (beta + q1) (the other cases are symmetric
or flat); for fixed beta, q2 is affine in alpha, so one elimination per beta finds an alpha with q2 in
L + R and not in L + span(q1).  With mc1 this decides every 2-AND rebuild over the window inputs
[C per window and care set].  2-5 s per 10-input window.
- On the 186 such windows of the A <= 29 run: A = 28 circuits 23 windows -> all 'none' [C: no 2-AND
  rebuild of these windows]; A = 29: 53 of 163 rebuilt (verified), e.g. 29/5/131/20 -> 28/5/130/20,
  29/5/134/20 -> 28/5/131/20, 29/5/127/30 -> 28/5/126/27, 29/4/136/24 -> 28/4/133/22; all dominated by
  the archive front (28/5/130/19, 28/5/125/25, 28/4/132/22).
- [C, per window] on the A = 28 archive circuits (183 circuits, ~13 000 sampled windows with 2-4 ANDs,
  <= 10 inputs): every 2-AND window fails the rank test or the exhaustive flat 1-AND search; every
  3-AND window fails the rank test, the flat 2-AND search, or the sequential 2-AND search; 4-AND
  windows were checked by rank and flat 3-product search only (59 'no_flat' 4-AND windows open).
  This is not a lower bound on the circuits: windows are sampled, the care set is controllability-only
  (no observability don't-cares), and outputs must be reproduced exactly.

## Grind of the AND-removal results: two new A = 28 frontier points (03:21-04:04 UTC) [H method, results verified]
grind.py: rounds of the gate kernel (hub ops._kernel, op_polish settings, 60 s) on the best circuit of
a randomly chosen (A, AD, GD) cell of a pool, polish under own caps (p 0.5) or pull GD - 1/-2,
chaining every cell improvement.
- CPU 18, 43 min, seed 41, pool = 9 polished 28/4 mc1 results (from 29/4/136/24 4a9ce43fe1aa etc.):
  cells reached 28/4/134/19, 134/20, 139/18, 140/17, 145/16.
- CPU 17, 32 min, seed 42, pool = 28 distinct 28/5 mc1/seq2 results with G <= 140: 28/5/124/28,
  126/24, 126/25, 128/23, 130/19, 130/21, 130/22, 134/18.
- NEW (not dominated by the final hub archive goalsnap nor by the NIST pin; aes_check OK, "new Pareto
  point on pinned set: YES"):
  - **28/4/134/19** `~/xs-campaigns/2026-11-15-study/R1/found/r1-grind-28-4-134-19.bfx` (AND 28,
    XNOR 54, XOR 52), lineage: 4a9ce43fe1aa 29/4/136/24 -> mc1 2-AND->1 window -> 28/4/132/22 ->
    grind (pull, polish).  Front neighbours: 28/4/133/20, 28/4/135/18.  Goal B distance: G +4.
  - **28/5/126/24** `.../found/r1-grind-28-5-126-24.bfx` (AND 28, XNOR 45, XOR 53), lineage:
    826bcab90d23 29/5/127/30 (a join product) -> seq2 sequential 3->2 window -> grind polish.
    Front neighbours: 28/5/125/25, 28/5/127/22.  Goal C distance: GD +5.
- Interpretation [H]: the archive holds A = 29 circuits whose extra AND is locally redundant
  (mostly join products and seeds); removing it exactly gives new A = 28 structures that the
  kernel can then pull to new (G, GD) trade-offs.  The front A = 28 circuits themselves showed no
  removable windows.

## A/B ab3: base vs base + andrm (op_andrm.py as a generator), 04:04-05:05 UTC [H]
op_andrm.py: phase 1 (50% of 60 s) chains exact window AND removals (mc1 flat products, seq2 sequential
3->2), AD may rise by 1; phase 2 kernel polish of the reduced circuit under its own caps; candidates
placed with the generator slack.  Fixed-target smoke tests (40 s): 4a9ce43fe1aa 29/4/136/24 ->
28/4/143/23 -> polish 28/4/135/21; 826bcab90d23 29/5/127/30 -> 28/5/127/30 -> 28/5/126/28.
Snapshot ab3-snap (final long archive, 2311 records, front 85).  The test arm's control.json had a
quoting error (ab.sh GEN line) for its first ~40 s, fixed by hand; its first job ran with base ops.

| arm | CPU-h | admissions | new frontier points | not dominated by other |
|---|---|---|---|---|
| base | 1.00 | 23 | 0 | 0 |
| base + andrm | 1.01 | 4 | 0 | 0 |

- andrm: 8 jobs, 290 CPU-s, 0 admissions; 2 of 8 front targets had a removable window (33/4/112/16 ->
  32/5/113/19 -> polish 32/5/112/19; 32/4/119/18 -> 31/5/123/21 -> 31/5/119/21), both dominated.
  The scheduler gives andrm only front targets, whose ANDs are locally tight; the hits above came
  from non-front archive circuits.  Verdict: tie at 0 -> not adopted as a hub operator; the useful
  form is the archive-wide pipeline overnight.sh (QUEUE.md, R1 entry).

## Summary (R1, 2026-11-15 ~05:10 UTC)
- wres (SAT window resynthesis, exact on the multi-output Boolean relation, depth deadlines): correct
  (positive controls, every splice verified), but on this archive it found nothing: 0 / 1107 hub
  windows improved, 0 / 28 fixed-target jobs strictly better, A/Bs ab1 and ab2 0 vs 0.  Front windows
  up to ~6 gates are exactly optimal for their query [C per window]; 7-10-gate windows stay unknown
  at 8k-400k conflicts.  Not recommended for the hub.
- Exact window AND removal (mc1 rank test + exhaustive flat products, seq2 sequential 3->2) is cheap
  (5 ms / window) and finds verified A-1 rebuilds in many A = 29-35 archive circuits (join products,
  seeds), none in the A = 28 front (~13k windows, [C per window, care set only]).  As a hub operator
  (andrm, ab3) 0 vs 0: the scheduler only targets front circuits.
- The kernel grind of A-1 results produced two NEW verified A = 28 frontier points: 28/4/134/19 and
  28/5/126/24 (found/).  Suggested overnight: strategies/R1/overnight.sh on 2 CPUs (QUEUE.md).
