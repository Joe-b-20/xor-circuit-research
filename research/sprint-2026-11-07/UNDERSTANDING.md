# Linear maps and the XORFlux search: what we understand (sprint 2026-11-07)

Status: DRAFT, updated during the sprint (last 15:40 UTC; an adversarial re-derivation of
F1-F9 is folded in, see FINDINGS R). Every statement carries an evidence
tag: [proved] [checked] [measured] [cited] [guess]. Four kinds of object are kept apart: the
MAP (the matrix), the CIRCUIT (a value set), the SEARCH PROCEDURE (moves, acceptance,
restarts, sharing) and the IMPLEMENTATION (cost per step). F-numbers refer to
[FINDINGS.md](FINDINGS.md); inherited results name their source folder under `~/xs-campaigns/`.

## 1. The objects

- A circuit for a map M is exactly a set S of values (GF(2) masks) in which every output and
  every helper is the XOR of two earlier members; gates = |S|; depth is a function of S alone
  [proved, 2026-11-05-visual]. Two circuits with the same S are the same point. "Gate order",
  "which pair is summed first" and names are labels.
- Symmetries of the map act on S: for MixColumns the byte rotation Z4 and nothing else among bit
  permutations [checked, 2026-11-05-space]. Counts and distances are taken modulo it.
- A plateau is the set of circuits reachable from S by the walk's neutral remove-one moves. At
  the bottom of every landscape we have looked at it is an exact Cartesian product of small
  independent factors [checked, 2026-11-05-views/plateau; 2026-11-05-exit]. Each 3-way factor
  is the pairing choice of an unshared 3-input XOR tree (F2) [checked on 52 + 44 MixColumns 88
  plateaus and the kste corpus]. Larger coupled factors (15, 33, 54, 108, 477, 2101, 18927
  choices) are blocks of trees that share values.
- Consequence: a plateau is ONE circuit in many spellings. Walking it changes nothing about
  the circuit's structure. The structural object is the plateau's core (the values no neutral
  move touches; 40-49 of the 56 helpers at MC 88).

## 2. What the search procedure does, and which of its decisions the evidence supports

- Moves. `walk.remove1` (remove a helper, repair with one exact value; never uphill) made 89 %
  of all gates ever won below NIST across 59 maps, `lns.rebuild` 9 %, `walk.expand` 1 %,
  structural moves 0.3 % for 4.6 % of CPU (F4) [measured]. Near a good circuit remove1 and LNS
  win in proportion to their CPU; expand is the efficient move only while descending from a bad
  root [measured, crossmap].
- What remove1 can and cannot do. At a plateau it re-spells (F2). An improving remove1 step
  exists only when the leftovers of several users of a value coincide in one buildable value
  [derived + measured on 927 steps, 2026-11-02-why]. At the bottom of MixColumns no such step
  exists from any of ~100 plateaus examined [checked, PES; kste agent].
- Acceptance. Neutral moves kept; uphill +1 while cost <= chain best + 2; a depth window of 2
  above the chain best [from code]. This lets a chain at 88 climb to 89 and fall into a
  different 88 plateau: an A-arm chain visited 6+ distinct 88 plateaus in 30 min (F5 data).
  The window is the one acceptance knob with an established effect: removing it makes the
  search succeed far more often within the budget on two MixColumns analogues (0.65 -> 0.97,
  0.62 -> 1.00) and faster per seed on the third (0.59x iterations) (F8, replicated
  concurrently, 3 maps x 40 seeds). On MixColumns itself hunt C's 88 % vs 81 % of chains
  reaching 88 and 1.94 vs 1.51 arrivals per worker-hour are inside the noise (rate ratio
  1.29, interval ~0.8-2.2); hunt D (3 arms, same first roots, 13 h) is the controlled test.
- Restarts. v8 restarts a chain 900 s after its last improvement, 1,800 s while it holds the
  worker best. On MixColumns uncapped from fresh roots, restarting after 300 s gives 2.1x more
  arrivals at 88 per worker-hour (3.15 vs 1.51, full 5 h; 2.15x per iteration) at the price
  of abandoning half the chains at 89 (F6) [measured]. Whether that is "better" depends on the objective (sampling many plateaus:
  yes; finishing a given descent: no).
- Sharing / copying. On InvMixColumns descents, copying every worker onto the newest best is
  the strongest lever found (2026-11-03-waits; 2026-11-04-12h copy-only arm) [measured]; it
  collapses diversity, which is exactly what a discovery objective does not want.
- Roots. From a constructor root (naive, Paar, BP, anneal3) 77-85 % of chains reach <= 89
  within 3 minutes and all within 11; 11 of 12 first chains were at 88 by 25 minutes (median
  414 s) (F1, R) [measured, 6 roots x 2 walks]. In the small-map benchmark the
  first root is already optimal in 15-56 % of runs depending on the constructor [measured,
  bench].

## 3. Where it succeeds and why

- Cross-map: the search beat NIST on 53 of 59 maps, by 2-15 %, almost always within 1-2
  worker-hours (F4). What predicts the gain, after controlling for circuit size: heavy rows
  (more shared sub-sums for remove1 coincidences to find) and how much sharing greedy
  constructors leave behind (base/direct); plus NIST's depth slack, which is a property of the
  baseline [measured, crossmap]. The numeric extrapolation built on this (gain per ln(time)
  from each map's late slope) did NOT survive the prediction tests: 1 hit, 1 beaten, 3
  over-predictions on 5 maps (F9). What held is coarser: maps over 8x8 matrices gain several
  gates per worker-hour at NIST's depth whatever their property profile (16 of 19 trials on
  the sweep's 12 maps plus X1/pt's; F10), maps over 4x4 matrices at NIST's depth gain 0-1
  (1 of 6; F7, F9) [measured]. Where the gain comes from, on the one map that gained 26
  gates (klsw17-m-8x8-gf256 347@6 -> 321@10): a depth band nobody had searched; the gates
  minimum of several maps sits at a middle depth, not the deepest searched (F10) [measured,
  3 maps; mechanism conjectured].
- Small maps with proved optima (69 maps, 6-16 inputs, 5-34 gates): v8 reaches the optimum in
  1,380 of 1,380 runs within 60 s, median 3 iterations [measured, bench]. The minima form ONE
  plateau under the real moves in all 15 fully enumerated maps; the fragmentation seen earlier
  came from depth caps [checked, bench]. Difficulty (iterations to optimum) tracks the gap
  between the Paar count and the optimum (rho +0.85 across families) and the number of helpers
  [measured, bench].
- The one small family where v8 fails: circulant(2,3,1,1) over GF(16) (16 inputs, reference
  42; apparently the repo's small-scale-aes), 14 of 20 runs in 120 s [measured, bench]. This is
  the usable reliability instrument for engine variants.

## 4. Where it fails or stalls and why

- MixColumns at 88. Descent is cheap; the whole difficulty is below 88 (F1). The 88 level is
  vast: about 18 worker-hours of catalogued descents gave <= 225 distinct plateaus with 3
  repeats, all three on the largest plateaus (0.8-3.4 M states; landing probability grows
  roughly in proportion to plateau size, so the small ones are under-sampled; capture-recapture
  on chains gives at least ~2,500 plateaus (assuming independent chains; node-level meetings
  suggest >= 3e4) and plausibly 3e4-5e5, with ~97 % of the visit probability on plateaus never
  seen) (F5, F12, R2) [estimated]. The 52 pre-sprint plateaus sit at depth
  5-7, the hunt's mostly at 7-10, so "no overlap" with them is mostly a different depth
  stratum. Every RESOLVED +1 exit from every plateau checked (49 by PES mc24, 19 so far in
  kste1) goes home or to another 88, but 56 % of the +1 descents were cut at their state
  bound before landing and are unresolved, and the +2 band is essentially unexplored (I.1). The transition graph of the 88 level, drawn from 146
  chains' hops (F11): 139 components, 133 of them a single chain's trail, 8 nodes of 1,454
  entered by two chains, 0 down-exits in 1,869 sampled states; hops change ~30 % of the
  helpers; the 8 cross-chain meetings among 1,462 visits are what independent wandering over
  ~1e5 effective nodes predicts (null model, review 2), so the sampled graph says nothing about
  whether the neighbourhoods connect [measured + model]. The walk lives on the 88+89 band (39-45 % of sampled instants at
  89, ~12 departures to 89 per second [guess from ledgers]); 30 s sampling sees a floor of ~44
  plateau changes per chain-hour. So the search's failure
  below 88 is not slowness or bad decisions: its move set has no down-step from any 88 core
  found so far, and the number of cores is far beyond what sampling can exhaust. This is
  resistance to the tested moves under the tested conditions, not a proof that heuristic
  search cannot find 87 (FINDINGS I.1 states exactly what is and is not established).
- Whether an 87 exists is therefore a global question about the map (lower bound 75, no
  published proof of 88; the kste "barrier" argument is scoped to known circuits, F3). More
  local search time can settle it only by finding an 87, at a rate this data cannot estimate
  (97 % of the landing mass is on unseen plateaus); only exact or structural methods can settle
  it negatively. First step taken (F13):
  a SAT formulation that, for a kept subset K of an 88 circuit, decides whether ANY circuit
  with <= 87 gates contains K (no depth, pool or wiring restriction); 43 such sets of 79-84
  values on three circuits are refuted in seconds, windows of 9-10 removed values are the
  60 s frontier [measured].
- Waits on InvMixColumns descents are time in dead rooms (small sealed plateaus) until a large
  move lands in a rich one; no local score predicts which state is productive
  [measured, 2026-11-03-waits]. The present sprint's structural reading says why: a room is one
  circuit, and "productive" is a property of the circuit's +1 neighbourhood, which the walk does
  not see.
- Depth caps change the landscape qualitatively (which minima exist, whether they connect):
  MC 89@4 is a single isolated level-1 family [measured, 2026-11-02-why]; in the small analogues
  a cap turns one plateau into several [checked, groundtruth, bench].

## 5. What makes it slow: implementation versus procedure

- Implementation: about 35 % of proposal CPU is remove1 calls that return nothing; depth.repair
  is a provable no-op at the minimum depth; star-memory blocking 67-92 % in the star runs
  [measured, v10-proto]. Iteration rate falls with circuit size and is the best single
  predictor of "still improving at the end of the hour" after size (F4).
- Procedure: at the bottom a chain re-spells one circuit (F2) and hops between 88 plateaus
  through 89 states; none of that time can produce an 87 unless a core with a down-exit exists
  in reach. On the small maps the engine's own restart timer never fires (runs end in seconds).
- Repeated work: at MC 88 the plateau (2,187 states) is covered in minutes and re-walked for
  the rest of the stay [measured, 2026-11-03-waits speed/anatomy]; the star memory showed 67-92 %
  of moves blocked as revisits.

## 6. What properties of a map matter

- Established across the 59 maps (F4): circuit size. Max/mean row weight and the sharing left
  by greedy constructors (base/direct) correlate with the gain but at +0.92 with each other
  and with little residual variation after size: [in-sample] until tested on fresh maps.
  Not predictive after size: field, matrix dimension, inverse,
  involutory, circulant/dyadic. On the small proved maps: Paar gap to the optimum and helper
  count predict iterations to optimum; number of inputs does not [measured, bench].
- MixColumns is mid-class in every measured property; its outcome is explained by its baseline
  (NIST's 88 is the best published circuit, reached independently by our fresh roots), not by a
  measured property (F4). X1 confirmed the reading on the 32x32 class: a single fresh-root
  worker reaches the repo's best (or better: ss16-4x4-gf256 96@5) within the hour on every
  32x32 map tried, and 89@5 / 88 uncapped on MixColumns; the seeded gains over NIST there are
  the baseline's slack, which is zero for MixColumns (F7). On 64x64 maps one worker-hour from a
  fresh root is far from the frontier, but one NIST-seeded worker-hour beat the repo's circuits
  on two maps (grostl 364@11, klsw17-m-8x8-gf256-inv 327@12), and the sweep then beat the
  repo's circuits on 10 of 12 further 8x8-matrix maps in one worker-hour each (F10): those
  maps are compute-limited, not search-limited [measured gains; the reading is a guess with
  n = 1 per cell].
- Search knobs (F8): on the reliability benchmark only removing the depth window had an
  established effect (half the iterations to the reference on small-scale-aes, deeper
  circuits, 10-40 % more CPU per iteration); stall timers, LNS and expand weights showed
  nothing beyond load noise. The concurrent replication (F8, 3 maps x 40 seeds) established
  0.43-0.50x iterations on all three analogues and a higher success rate within 120 s on two
  (0.65 -> 0.97, 0.62 -> 1.00). Mechanism (tested on MixColumns by hunt C, F8): the window is
  what limits a chain's migration between 88 plateaus through 89 states; without it chains
  reach 88 more often and land on much larger coupled plateaus. Whether that yields more
  DISTINCT 88 plateaus per worker-hour is open (the exact catalogue could not keep up with C;
  the cheap identity `hunt/sig.py` and hunt D are the answer).
- What differs between small analogues and MixColumns is not "recipes per value" (similar) but
  the share of all values one XOR away from the current set: 0.4-0.96 at <= 9 bits, ~1.5e-6
  for MixColumns [measured, bench]. That is why single-plateau connectivity and 100 % success at
  small sizes should not be assumed to transfer.

## 7. What transfers and what is specific

- Transfers: the plateau-as-product structure (MC, InvMC, small analogues); remove1 as the
  winning move on every map class; descents being cheap relative to the bottom; copying as
  the lever for descents (InvMC) versus restarts for discovery (MC).
- Specific: the level-1 foundation effect (MC at depth 4: the only known 89@4 family, 81 circuits
  = 4 slots x 3 re-pairings over a 53-value core, carries one 26-pair first layer that none of
  5,798 distinct 90@4 states shares; the walk moves a first layer one pair at a time, so entry is
  rare (two entry events in >10,000 core-hours) but uncapped the family is no trap (F15); 26
  first-layer gates is not proved necessary; InvMC has 23 level-1 sets in its 118 family); the MixColumns 88 vocabulary (303 values mod rotation over 52
  plateaus, growing by ~6 per new plateau).

## 8. What remains unexplained

- Whether an 87 exists (75 <= optimum <= 88). No local evidence can decide it; the exact
  scoped route (F13) can grow: longer limits, two-seed windows, more circuits, and an encoding
  for the factor-structured mobile part.
- Why the 88 cores are so numerous and (on the resolved exits) sealed at +1: is it a counting consequence
  of 32 weight-5/7 outputs over a 56-helper budget, or a property of the circulant structure?
  The bit-slice block floors (3, 20, 10, 24, 10, 16) hold for every known 88 but are not proved.
- The exact per-depth picture: 88 exists at depth 5 and 89 at depth 4; whether 88@4 exists.
- A predictor of which fresh root reaches 88 (none found; constructor type is a weak one).
- Whether removing the depth window buys distinct 88 plateaus or only faster re-arrival at
  ones of the same kind (hunt D, 3 arms, same first roots, 13 h, ends ~04:06 UTC 11-08), and
  whether it helps at all under a depth cap (hunt E, cap 5, ~01:00-03:40 UTC).
- How many 88 plateaus there are, more precisely than "1e5, floor 2,500" (F12): the exact
  catalogue on the remaining ~1,390 sampled states (a day of one core) would give ~100
  coincidences and pin the size exponent.
- Whether the 88 cores form one connected graph under the +1 band: as sampled at 30 s they do
  not (F11: 139 components for 146 chains); finer sampling (every ~1 s, or logging every
  88 <-> 89 transition in the engine) is needed to see whether trails meet between samples.
  No core with a down-exit has been seen anywhere (0 of 1,869 sampled states, exhaustive remove1;
  0 at any fanned member of the 282 catalogued plateaus, every member for the 155 of <= 2e4 states).
- Why the gates minimum of a map sits at a middle depth (F10: klsw17-m-8x8-gf256 321@10 beats
  everything at depth 12-15; grostl 349@15 vs 350@16): a budget effect of the depth window, a
  property of the map, or under-search of the deeper band.
