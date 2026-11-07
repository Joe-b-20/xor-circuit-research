# Linear maps and the XORFlux search: what we understand (sprint 2026-11-07)

Status: final-pass draft, 2026-11-07 23:00 UTC. Three adversarial reviews are applied (FINDINGS R,
R2, review3); numbers are as of 22:30 UTC with their source named. Every statement carries an
evidence tag: [proved] [checked] [measured] [estimated] [cited] [guess]. Four kinds of object are
kept apart: the MAP (the matrix), the CIRCUIT (a value set), the SEARCH PROCEDURE (moves,
acceptance, restarts, sharing) and the IMPLEMENTATION (cost per step). F-numbers refer to
[FINDINGS.md](FINDINGS.md); inherited results name their source folder under `~/xs-campaigns/`;
`import/zip/...` paths are the owner's imported archive.

## 0. Vocabulary (used throughout)

- Value, helper, output: a value is a 32-bit GF(2) mask; outputs are the matrix rows; a helper is
  any computed value that is not an output. Inputs are the 32 unit masks.
- Depth of a value set S: the smallest number of levels in which S can be built, each value the XOR
  of two values of lower level (inputs are level 0); depth(S) = max over values. It depends on S
  only (minimum over orderings), so "88@12" and "88@8" are properties of value sets.
- remove1: remove one helper and repair with one exact value so that all outputs stay buildable;
  neutral if the gate count is unchanged, down if it drops. lns.rebuild: remove several values and
  rebuild. walk.expand: add a value. Structural moves: re-pair subtrees. Depth window: the engine
  rejects states whose depth exceeds the chain's best depth by more than 2 (none = no limit).
  Acceptance band: a state up to chain best + 2 gates is accepted (uphill moves come from expand and
  rebuild; remove1 never goes uphill).
- Chain: one root until the engine restarts the worker (stall timer 900 s, or 1,800 s while it
  holds the worker best). Arrival: a chain's first state at 88. Worker-hour: one worker for one hour.
- Plateau: a connected component of the graph on value sets with a fixed gate count whose edges are
  remove1-neutral moves. It is relative to the move set and the depth cap (a cap removes moves, so
  cap-4 plateaus are smaller). Core: the values no neutral move touches; mobile part: the rest.
  Factor: an independent block of the product structure; a 3-way factor is one 3-input XOR tree whose
  intermediate value is unshared (3 pairings). Coupled factor: a block of several trees that share
  values. Exact catalogue: plateaus closed completely by PES `compress` (exact size and identity);
  cheap identity (v3 signature): the canonical value set of the 1-step neutral closure, an upper
  bound on distinct plateaus (over-splits coupled ones by 1.6-2.3x, never merged two exact plateaus in
  230 tests).
- +1 band / +1 exit: a state one gate above a plateau reached by one move; a descent from it is
  resolved if it lands on an 88 plateau (home = the same, join = a known one, new = a new one) or is
  cut after 400 visited states (cfg.bound_plus1) and called unresolved. PES = plateau exit search
  (`2026-11-05-exit/pes`); mc24 = its 19 h run on 49 of our plateaus; kste1 = its run on the kste
  corpus's plateaus (killed at 13.2 h).
- Hunts: A (v8 defaults), B (restart after 300 s stall), C (A with depth window none), 03:16-11:30
  UTC; D0/D4/DN (window 2 / 4 / none, same first roots), 15:06-21:41 UTC; E (capped) never ran.
  X1, pt, sweep: fresh-roots-vs-NIST, prediction tests and the big-map sweep on other maps. bench:
  the small-map benchmark agent. crossmap: the 59-map property study. kste: github.com/kste/
  mixcolumns_xor (18,938 published 88s, 50 plateaus).
- Lower-bound proof coordinates (75 proof, `lb76/REPORT.md` section 1): x / y / h = odd+odd gates /
  even+even gates / odd helpers; q = missing labels, z = helper-helper edges of the odd graph, s =
  q + z; a / b / Y / V = x and y in the two phases of the canonical-transpose orbit; drift budget =
  a + b + 2G - 192; local rows (L1)-(L23) = the linear inequalities on helper-type counts.

## 1. The objects

- A circuit for a map M is exactly a set S of values in which every output and every helper is the
  XOR of two earlier members; gates = |S|; depth is a function of S alone [proved,
  2026-11-05-visual]. Two circuits with the same S are the same point; gate order and names are labels.
- Symmetries of the map act on S: for MixColumns the byte rotation Z4 and nothing else among bit
  permutations [checked, 2026-11-05-space: all 32! input permutations with output order free].
  Counts and distances are taken modulo it.
- Wherever a plateau's closure was completed (every plateau of <= 2e4 states: 155 hunt plateaus, the
  52 pre-sprint ones, InvMC 118@5 = 200 states, 22 of kste's 50) it is an exact Cartesian product of
  small independent factors [checked]; for the larger coupled plateaus the product form is checked
  at the seed and the factor-local closures only, and 8 giant entries were never closed [checked
  pairwise / open]. Each single-value 3-way factor is the pairing choice of an unshared 3-input XOR
  tree: 1,425 of 1,425 such factors over the 264 product plateaus catalogued by 13:30 UTC XOR to zero
  (F2, R) [checked]; kste's plateaus have the same shapes but their factors were not checked.
  Coupled factors (15, 33, 54, 108, 477, 2,101, 18,927, 62,856, 69,228 choices) are blocks of trees
  that share values.
- Consequence: a plateau is ONE circuit in many spellings. Walking it changes nothing about the
  circuit's structure. The structural object is the core: 47-49 of the 56 helpers on the 6 circuits
  used for SAT, down to ~40 at states with 44 neutral moves [measured, pes_lib.fan].

## 2. What the search procedure does, and which of its decisions the evidence supports

- Moves. remove1 made 89 % of all gates ever won below NIST across 59 maps, lns.rebuild 9 %,
  walk.expand 1 %, structural moves 0.3 % for 4.6 % of CPU [measured, crossmap finder logs, F4].
  Near a good circuit remove1 and LNS win in proportion to their CPU; expand is the efficient move
  only while descending from a bad root [measured, crossmap].
- What remove1 can and cannot do. At a plateau it re-spells (F2). An improving remove1 step exists
  only when the leftovers of several users of a value coincide in one buildable value [derived +
  measured on 927 steps, 2026-11-02-why]. At the bottom of MixColumns no improving remove1 step
  exists at any of 4,314 sampled 88 states (hunts A/B/C 1,869, hunt D 2,445; exhaustive per state,
  the candidate cut never bound; two independent runs), at every member of the 155 catalogued
  plateaus of <= 2e4 states and at the fanned members of the larger ones, nor on kste's 50 plateaus
  [checked, F11, F14 Q4, kste]. This is a statement about one move at sampled states, not about all
  88 circuits.
- Acceptance. Neutral moves kept; uphill to chain best + 2; depth window 2 [from code]. This lets a
  chain at 88 climb to 89 and fall into a different 88 plateau: A-arm chains visited 5-22 distinct
  catalogued 88 plateaus in 20-60 min of sampled life (hunt/chains.log; free-05 chain 0: 22 in
  2,430 s) [measured]. The window is the one acceptance knob tried on MixColumns, and the one knob
  with an established effect on the analogue benchmark: removing it raises success within a 120 s
  budget on two MixColumns analogues (0.65 -> 0.97, 0.62 -> 1.00; references are best-known counts,
  not proved optima) and iterations per solved seed on the third (0.59x) (F8, R; replicated
  concurrently, 3 maps x 40 seeds). On MixColumns itself hunt C's 88 % vs 81 % of chains reaching 88
  and 1.94 vs 1.51 arrivals per worker-hour were inside the noise (rate ratio 1.29, interval
  ~0.8-2.2). Hunt D (window 2 / 4 / none, same first roots, 25.5 worker-hours per arm before the
  machine failed; F14, pre-registered): first arrivals at 88 per worker-hour 1.49 / 1.69 / 1.80
  (38 / 43 / 46 events; ratio 1.21, Poisson interval ~0.8-1.9: not established), distinct plateaus
  (v3) per worker-hour 24.5 / 26.8 / 26.0 (ratio 1.06; the prediction >= 1.2 is refuted), but the
  no-window arm lands far deeper (27.5 % of its 88 states at depth >= 10 vs 2.5 %). The window
  changes where chains land, not how often or how widely [measured].
- Restarts. v8 restarts a chain 900 s after its last improvement, 1,800 s while it holds the worker
  best. On MixColumns uncapped from fresh roots, restarting after 300 s gives 2.1x more arrivals at
  88 per worker-hour (3.15 vs 1.51, full 5 h; 2.15x per iteration) at the price of abandoning half
  the chains at 89 (F6, R) [measured]; it does not give more distinct plateaus per worker-hour than
  long stays (F5). Neither is a lever below 88.
- Sharing / copying. On InvMixColumns descents, copying every worker onto the newest best is the
  strongest lever found (2026-11-03-waits; 2026-11-04-12h copy-only arm) [measured, InvMC]; it
  collapses diversity, which is exactly what a discovery objective does not want.
- Roots. From a constructor root (naive, Paar, BP, anneal3) 77-85 % of chains reach <= 89 within 3
  minutes and all within 11; 11 of 12 first chains were at 88 by 25 minutes (median 414 s) (F1, R)
  [measured, 6 roots x 2 walks]. In the small-map benchmark the first root is already optimal in
  15-56 % of runs depending on the constructor [measured, bench].

## 3. Where it succeeds and why

- Cross-map: the search has strictly fewer gates than NIST at some NIST depth on 53 of 59 maps,
  almost always within 1-2 worker-hours (F4; the 32x32 class gains 3.3-11 %) [measured, crossmap].
  What correlates with the gain after circuit size: heavy rows and the sharing greedy constructors
  leave behind (base/direct), which correlate +0.92 with each other, plus NIST's depth slack
  [in-sample, crossmap]. The numeric extrapolation built on this (gain per ln(time) from each map's
  late slope) did NOT survive the prediction tests: 1 hit, 1 beaten, 3 over-predictions on the 5 maps
  run for it (F9); rescored on the 5 further maps the sweep happened to cover, 2 hits, 2 beaten, 6
  misses of 10 [measured, with protocol caveats]. What held is coarser: in 16 of 20 one-to-four-
  worker-hour trials on maps over 8x8 matrices (X1 2/3, pt 4/5, sweep 10/12) the circuit at NIST's
  depth lost at least one gate, in about 10 of 20 at least three gates, which is the run-to-run spread
  on 64x64 maps (R); on 4x4 maps 2 of 7 trials gained one gate (F7, F9, F10) [measured]. Where the
  gain came from on the map that gained 26 gates (klsw17-m-8x8-gf256 347@6 -> 321@10): a depth band
  nobody had searched; the gates minimum of several maps sits at a middle depth, not the deepest
  searched (F10) [measured, 3 maps; mechanism conjectured]. Separated on the existing run data (F25): "unsearched depth band" is excluded as a general
  mechanism (seed slack does not predict gain; the 26-gate case is a weak-comparison-point effect); 4x4
  maps sit at the floor the search reaches (fresh root, NIST's circuit and ours converge within 0-1
  gate in minutes); both classes had equal prior worker-hours, and the 8x8 gains are the 2nd-5th hour
  of a log-decaying curve from ordinary one-hour endpoints (165 / 27 / 5 gates removed in the first
  half / second half / final quarter of the runs) [measured; reading tagged guess].
- Small maps with proved optima (69 maps, 6-16 inputs, 5-34 gates): v8 reaches the optimum in 1,380
  of 1,380 runs within 60 s, median 3 iterations [measured, bench]. The minima form ONE plateau under
  the real moves in all 15 fully enumerated maps; the fragmentation seen earlier came from depth caps
  [checked, bench]. Difficulty (iterations to optimum) tracks the gap between the Paar count and the
  optimum across families (rho +0.85) but not within the dense 8-bit family (+0.37, p 0.34), so it
  ranks families, not maps [measured, bench].
- The small maps where v8 is not reliable within 120 s are MixColumns analogues whose reference is a
  best-known count, not a proved optimum: mc_gf16 = the repo's small-scale-aes (reference 42, 14 of
  20 runs), mc_gf8b (reference 29, 0.65) and mc_gf16_p1f (0.62) [measured, bench]. They are the
  reliability instrument for engine variants.

## 4. Where it fails or stalls and why

- MixColumns at 88. Descent is cheap; the whole difficulty is below 88 (F1). The 88 level is vast.
  Catalogue as of 22:00 UTC: about 18 worker-hours of catalogued descents gave 215 exact sprint
  plateaus (+ 52 pre-sprint = 267 products; 8 giant entries unresolved, 2-8 plateaus; hunt D's 2,445
  states not yet catalogued; "282" in older notes counts keys, not plateaus) with 3 repeats, all on
  the largest plateaus (0.8-3.4 M states). Visit probability grows roughly in proportion to plateau
  size (a visit exponent fitted on ~6 coincidences), so small plateaus are under-sampled;
  capture-recapture on chains gives at least ~2,500-3,100 plateaus at 95 % assuming independent,
  exchangeable chains (node-level meetings imply >= ~3e4), plausibly 3e4-5e5, with ~97 % of the visit
  probability on plateaus never seen (F5, F12, R2) [estimated; the running exact catalogue of all
  sampled states tests the main assumption, that unseen plateaus resemble the seen small ones]. The
  52 pre-sprint plateaus sit at depth 5-7, the hunt's mostly at 7-10, so "no overlap" with them is
  mostly a different depth stratum.
- The +1 band. Every RESOLVED +1 exit from every plateau whose +1 pass completed (37 of 49 in PES
  mc24; 22 of the 119 kste plateaus compressed by kste1) goes home or to another 88 plateau; but 57 %
  (kste1, 24,475 of 43,113) to 64 % (mc24, pooled over 49 plateaus) of the +1 descents were cut at the
  400-state bound and are unresolved, and the bound cuts exactly the long descents, the ones that
  could reach another region. The +2 band was descended only partially (mc24: 38,748 descents on 37
  plateaus, 87 % unresolved, 0 lower; 24,284 LNS rebuilds, 40 % unresolved, 0 lower; the archive's
  Barrier-Tree plateau: 0 of 13,212 classes descended) [measured, status files].
- The transition graph of the 88 level, drawn from 146 chains' hops (F11): 139 components, 133 of
  them a single chain's trail, 8 nodes of 1,454 entered by two chains, 0 down-exits in 1,869 sampled
  states; hops change ~30 % of the helpers; the 8 cross-chain meetings among 1,462 visits are what
  independent wandering over ~1e5 effective nodes predicts (null model, R2; hunt D's 10 meetings in
  2.1 M pairs give the same 2e5), so the sampled graph says nothing about whether the neighbourhoods
  connect [measured + model]. The walk lives on the 88+89 band (39-45 % of sampled instants at 89, ~12
  departures to 89 per second [guess from ledgers]); 30 s sampling sees a floor of ~44 plateau changes
  per chain-hour.
- What this establishes about the failure below 88 is exactly this: the one-value move has no
  down-step at any sampled 88 state, and the level is far larger than any sample. What it does NOT
  establish: that heuristic search cannot find an 87. Paths through 89 that the bound cut (the
  majority), paths through 90 or higher, moves that change three or more values at once, other
  acceptance rules (wider band, longer stays; only the depth window was varied on MixColumns, F14)
  and the unsampled 97 % of the level are all open [measured + open] (FINDINGS I.1).
- Whether an 87 exists is a global question about the map: unrestricted lower bound 75 (the owner's
  computer-assisted proof: 2-input XOR circuits for one 32x32 column, cancellation and fan-out free;
  replayed here in 137 s, argument read, not checked; no published bound above the trivial 32, F19),
  no proof of 88; the kste "UNSAT at <= 87" is scoped to a pool of 1,073 values (1,702 under rotation)
  that 315 of 389 hunt samples leave (F3). More local search time can settle it only by finding an 87,
  at a rate this data cannot estimate; only exact or structural methods can settle it negatively.
  First step taken (F13, R2): a SAT formulation that, for a kept subset K of an 88 circuit, decides
  whether ANY circuit with <= 87 gates contains K (no depth, pool or wiring restriction; soundness
  independently confirmed). As of 22:30 UTC about 2,060 such kept sets of 76-84 values over 37
  circuits (repo 88@5, hunt A/C/D states, kste seeds; one-seed windows k <= 10, output blocks k <= 12,
  1,084 two-seed windows k <= 9 on the repo circuit) are refuted, 0 satisfiable, 16 timeouts; the
  union of removed values over the repo circuit's refuted windows covers 81 of its 88 values (72-74
  for the other circuits), so any 87 differs from each of these circuits in at least one value of
  each refuted kept set [measured, `sat/`]. On four plateaus the mobile part was also attacked: no 87 is a one-factor rewrite or a
  two-factor rewrite with <= 3 free values of those plateaus (F23). None of this bears on 87s away
  from these circuits.
- Waits on InvMixColumns descents are time in dead rooms (small sealed plateaus) until a large move
  lands in a rich one; no local score predicts which state is productive [measured, 2026-11-03-waits,
  InvMC]. A reading: a room is one circuit, and "productive" is a property of the circuit's +1
  neighbourhood, which the walk does not see [guess, untested].
- Depth caps change the landscape qualitatively (which minima exist, whether they connect): MC 89@4
  is a single cap-4 plateau of 81 circuits (F15; uniqueness of the family open); in the small
  analogues a cap turns one plateau into several [checked, groundtruth, bench].

## 5. What makes it slow: implementation versus procedure

- Implementation: about 35 % of proposal CPU is remove1 calls that return nothing; depth.repair is a
  provable no-op at the minimum depth; star-memory blocking 67-92 % in the star runs [measured,
  v10-proto]. Iteration rate falls with circuit size and is the best single predictor of "still
  improving at the end of the hour" after size (F4).
- Procedure: at the bottom a chain re-spells one circuit (F2) and hops between 88 plateaus through
  89 states; none of that time can produce an 87 unless a core with a down-exit exists in reach. On
  the small maps the engine's own restart timer never fires (runs end in seconds).
- Repeated work: on InvMC descents a walker covers its room (e.g. 216 circuits) in 1-5 CPU-minutes
  and re-walks it for many minutes [measured, 2026-11-03-waits, InvMC only]. On MC 88 the chain leaves
  a plateau every 1-2 minutes (F5, F11); the repeated work there is the re-spelling inside each short
  stay and the ~12 departures per second to 89 [guess from ledgers]; coverage of an MC plateau per
  stay was not measured. The star memory showed 67-92 % of moves blocked as revisits [measured].

## 6. What properties of a map matter

- Established across the 59 maps (F4): circuit size. Max/mean row weight and the sharing left by
  greedy constructors (base/direct) correlate with the gain but at +0.92 with each other and with
  little residual variation after size: [in-sample] until tested on fresh maps. Not predictive after
  size: field, matrix dimension, inverse, involutory, circulant/dyadic. On the small proved maps:
  Paar gap to the optimum and helper count predict iterations to optimum across families; number of
  inputs does not [measured, bench].
- MixColumns is mid-class in every measured property; its outcome is consistent with a baseline
  effect: NIST's 88 ties the best published count and fresh roots reach 88 gates (on other plateaus)
  within minutes, so there is no slack for the search to take [reading, consistent with F4/F7; not
  tested against an alternative]. X1 is consistent with the reading on the 32x32 class (one run per
  cell, R): a single fresh-root worker reaches the repo's best (or better: ss16-4x4-gf256 96@5) within
  the hour on every 32x32 map tried, and 89@5 / 88 uncapped on MixColumns. On 64x64 maps one
  worker-hour from a fresh root is far from the frontier, but one NIST-seeded worker-hour beat the
  repo's circuits on two maps (grostl 364@11, klsw17-m-8x8-gf256-inv 327@12), and the sweep then beat
  the repo's circuits on 10 of 12 further 8x8-matrix maps in one worker-hour each (F10) [measured
  gains]; "compute-limited, not search-limited" is a guess with n = 1 per cell.
- Search knobs (F8, R, F14): on the analogue benchmark removing the depth window is the one knob
  with an established effect, within a 120 s budget against best-known references: success rises on
  mc_gf8b and mc_gf16_p1f (0.65 -> 0.97, 0.62 -> 1.00) and iterations per solved seed fall on mc_gf16
  only (0.59x); stall timers, LNS and expand weights showed nothing beyond load noise. On MixColumns
  (hunt D, 25.5 worker-hours per arm, paired first roots) it buys neither arrivals (1.21, interval
  0.8-1.9) nor distinct plateaus (1.06; prediction >= 1.2 refuted), only deeper landings (27.5 % vs
  2.5 % of 88 states at depth >= 10). The proposed mechanism "the window limits migration through
  89" is not supported on MixColumns [measured].
- What differs between small analogues and MixColumns is not "recipes per value" (similar) but the
  share of all values one XOR away from the current set: 0.4-0.96 at <= 9 bits, ~1.5e-6 for
  MixColumns [measured, bench]. A reading: that is why single-plateau connectivity and 100 % success
  at small sizes should not be assumed to transfer [guess].

## 7. What transfers and what is specific

- Transfers: the plateau-as-product structure (MC, InvMC, small analogues, where closed); remove1 as
  the winning move on every map class; descents being cheap relative to the bottom; copying as the
  lever for descents (InvMC); restarts buying arrivals but not distinct plateaus (MC).
- Specific: the level-1 foundation effect (MC at depth 4: the only known 89@4 family, a cap-4 remove1
  plateau of 81 circuits = 4 slots x 3 re-pairings over a 53-value core, carries one 26-pair first
  layer that none of 5,798 distinct 90@4 states shares; the walk moves a first layer one pair at a
  time, so entry is rare (two entry events in all recorded cap-4 runs; the cap-4 core-hour total is
  not computed); the first layer is necessary but not sufficient (of 26 recorded 90@4 states carrying it, the
  8 that ended their runs at 90 do not connect to the family under remove1, while 11 transient
  ones do; q89check); uncapped the family is no trap (F15); 26 first-layer gates is not
  proved necessary; InvMC has 23 level-1 sets in its 118 family); the MixColumns 88 vocabulary (303
  helper values mod rotation over the 52 pre-sprint plateaus, growing by ~3-4 words per new plateau
  with more than half of new plateaus adding none: 303 -> 947 over 200 hunt plateaus, vocab.log).

## 8. What remains unexplained, and the bounds with their scope

- Whether an 87 exists. Unrestricted 2-input XOR circuits for one column: 75 <= C <= 88 (75: the
  owner's computer-assisted proof, replayed here, argument read, not checked; the published
  literature has no bound above 32, F19; 88: verified constructions, Jean's and ours). Depth <= 3:
  93 <= C3 <= 97 (owner's proof, replayed here in full, 2,028 s, F24; reductions read; 97@3
  optimality OPEN by the owner's latest checkpoint, whose default replay passes here). Depth
  <= 4: 89 is the best construction; no depth-4 bound above 75 in general (F22: proved layer facts
  give only G >= 57 unconditionally; over the 89's first layer plus its family's level-2 vocabulary,
  G >= 89 is SAT-proved; over the first layer alone, open). Inverse: depth >= 5 is proved
  (weight-19 outputs), 118@5 is a construction (optimality open), 88-gate unrestricted inverse
  constructions at depths 19 and 33 are recorded in the archive. Structural: any circuit with <= 89
  gates has >= 3 odd-weight non-output helpers (h = 0, 1, 2 cases proved / replayed here, F20; premise
  x >= 24 read). A claim of 87 impossibility is open.
  The 75 proof's rows leave 1,508 of 7,416 oriented claims open at G = 75, 1,313 with the sprint's two
  new row families (F18: proofs independently checked, 1,772 exact Farkas certificates with complete
  coverage of the 195 newly excluded claims, independent checker, mutation-tested) and 996 with
  the hub and dark-label rows of F21 (independently checked, no certificates yet); real 88 circuits violate no package row and leave every capacity row (L1)-(L23) slack >= 10
  (only Lemma 7.4 and two of the new rows are tight); the drift identity has no slack for any circuit
  of any gate count (margin = -(E_B + L_H) <= 0; real 88s lose only 0-7 units there), so the missing
  content is entirely in the local rows: realizability of low-Y/V/q profiles, not sharpening
  (F16-F18, bridgecheck). The exact scoped route (F13) can grow: k >= 11 helper windows, the plateau's mobile
  part, seeds from other plateaus.
- Why the 88 cores are so numerous and (on the resolved exits) sealed at +1: a counting consequence
  of 32 weight-5/7 outputs over a 56-helper budget, or a property of the circulant structure? (The
  group-sharing identity G = 108 + delta - S is an exact tautology and cannot bound G by itself: every
  known 88 pays 17-44 defect gates to share 37-64 units across the eight bit groups, no group is ever
  realised minimally, F26.) The
  bit-slice block floors (3, 20, 10, 24, 10, 16) hold for the kste corpus and ~1,000 of our 88s under
  one reading of "block" (kste/REPORT.txt) but are not proved; SAT on the sub-maps gives only >= 9,
  12, 13 on three blocks.
- The exact per-depth picture: 88 exists at depth 5 and 89 at depth 4; whether 88@4 exists.
- A predictor of which fresh root reaches 88 (none found; constructor type is a weak one).
- Whether removing the depth window helps under a depth cap (hunt E, cap 5, never ran).
- How many 88 plateaus there are, more precisely than "3e4-5e5, floor 2,500" (F12): the exact
  catalogue of all 3,845 sampled 88 states and the 8 unresolved giants (giants/catalogue_all.sh, 6
  workers since 21:45 UTC, ~1 core-day) would give ~100 coincidences and pin the size exponent.
- Whether the 88 cores form one connected graph under the +1 band: as sampled at 30 s the data cannot
  tell (F11, R2); finer sampling (every ~1 s, or logging every 88 <-> 89 transition in the engine) is
  needed. No core with a down-exit has been seen anywhere (0 of 4,314 sampled states, exhaustive
  remove1; 0 at any fanned member of the catalogued plateaus, every member for the 155 of <= 2e4
  states).
- Why the gates minimum of a map sits at a middle depth (F10: klsw17-m-8x8-gf256 321@10 beats
  everything at depth 12-15; grostl 349@15 vs 350@16): a budget effect of the depth window, a
  property of the map, or under-search of the deeper band.
- How fast the log-decaying gain curve on 8x8 maps flattens (F25: the second hour gives about a
  quarter of the first; the most informative run is the six sw2 maps twice, from the new bests and as
  seeded repeats).
