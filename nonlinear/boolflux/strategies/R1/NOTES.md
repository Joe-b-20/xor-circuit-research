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
