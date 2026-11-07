# Sprint 2026-11-07: findings

Each entry: observation, mechanism (plain words), prediction that could be wrong, test, what
survived, limits. Tags: [proved] [checked] [measured] [cited] [guess]. Scripts are named; raw
data lives in `~/xs-campaigns/2026-11-07-sprint/`.

## F1. Descending to 88 on MixColumns is cheap; the difficulty is entirely below 88 [measured]

- Observation (hunt, first 25 min, 12 fresh-root chains, v8 uncapped): every chain reached <= 89
  within 10-162 s of its root; 4 of 12 reached 88 within 50-216 s. (`hunt/descents.py`)
- Compare: July 2026 engine, every 88 within 3,855 s of its root, median 2,234 s (restart.root_seconds
  doc string). The v5+ incremental kernel changed the picture: 88 is minutes away from any root.
- Prediction: with hours of such descents, the number of distinct 88 plateaus reached will tell
  whether the 88 level is a small finite set (saturating curve) or vast (linear growth).
- Status: open; curve to be read from `hunt/plateaus.py`.

## F2. A 3-way plateau factor is the pairing choice of an unshared 3-input XOR tree [checked on one circuit]

- Observation: the repo 88@5's remove1 plateau is a product of 7 factors with 3 choices each
  (2,187 states) [checked, PES compress]. For a 3-input XOR s = a ^ b ^ c the intermediate can be
  a^b, a^c or b^c; those three values XOR to zero and each is used only by s.
- Prediction: in every factor the three choice values XOR to zero. Test: `hunt/factors.py` on the
  repo 88@5: 7 of 7 factors satisfy it [checked].
- Consequence: walking an 88 plateau is re-pairing seven 3-input trees. It can never change the
  circuit's structure; the 2,187 states are one circuit in seven interchangeable spellings. A
  plateau walk at the bottom is therefore pure repeated work, and the only genuine moves out are
  the +1 / +2 edits of the 49-value core (which PES explored).
- Extended to all stored PES plateaus (`hunt/pes_plateaus_check.py`, 68 files, 52 distinct 88
  plateaus modulo rotation): 424 of 424 three-way factors XOR to zero [checked]. Radices: 32
  plateaus are 3^7; 13 are 33·3^5, 3 are 45·3^4, 1 is 108·3^4, 2 are 3^6, 1 is 12933·3^2: the
  non-3 factors are coupled blocks where several trees share values.
- Vocabulary: the union of helper values over the 52 plateaus is 524 raw values = 303 modulo
  byte rotation (popcount 2: 54, 3: 99, 4: 111, 5: 98, 6: 86, 7: 45, 8+: 31). The 88 level
  speaks a small language [checked]. Whether new plateaus found by the hunt add words to it is a
  sharper novelty measure than plateau counts (to be tracked).
- Limits: the "unshared" part is inferred from the product structure (if the intermediate had
  another consumer, re-pairing would change that consumer's recipe and the factor would not be
  independent).

## F4. Across 59 maps: size and row weight predict gain over NIST; MixColumns is ordinary in every map property and an outlier only in outcome [measured, crossmap agent]

- Data: all 59 maps, properties computed from the matrices (`crossmap/props.py`), outcomes from
  circuits/ and the finder logs (`crossmap/outcomes.py`, `analyze2.py`). Protocol confound: 49
  "batch" maps had 1 NIST-seeded uncapped worker + 1 low-cap worker for 30-60 min; correlations
  below are on those 49 with partial rank correlation on log(NIST gates).
- Survives size control: max row weight (+0.63), mean row weight (+0.58), base/direct (-0.64:
  more sharing left by greedy constructors = more gain), NIST's depth slack above the minimum
  (+0.49, a property of the baseline). Does not survive: field size, matrix dimension, inverse,
  involutory, circulant/dyadic. Plateau width of the final state goes with LESS gain (-0.42).
- Mechanism offered [guess]: a remove1 improvement exists when several users of a value have
  leftovers that coincide in one buildable value; heavy rows have more common sub-sums, so more
  coincidences to find and more left behind by greedy baselines.
- Saturation: 16x16 maps saturate in under a minute, 32x32 maps over 4x4 matrices in ~5 min,
  8x8-matrix maps keep gaining ~1-2 % of NIST's gates per unit of ln(time) all hour.
- Moves: walk.remove1 made 89 % of the gates won below NIST, lns.rebuild 9 %, expand 1 %,
  structural 0.3 % (structural moves used 4.6 % of CPU).
- MixColumns: density, row weights, constructor gap all mid-class; every other 32x32 map over a
  4x4 GF(2^8) matrix gained 3.3-11 % over NIST in 1-2 worker-hours, MixColumns 0 % at depth 5 in
  >100 worker-hours. Reading: NIST's 88 is a literature-optimised point that our fresh-root
  search independently reaches and stops at (a BASELINE effect, not a map property). This is
  consistent with the plateau findings (F1, F2) but does not by itself say whether 88 is optimal.
- Falsifiable predictions recorded in `crossmap/predict.csv` (e.g. skop15-8x8-gf16 146 -> 140 at
  depth 19 in 1 h on 4 workers; no 16x16 map gains a gate). Discriminating experiment X1 (fresh
  roots vs NIST seeds at NIST's depth, 8 maps) prepared in `x1/x1.toml`, to run when cores free.

## F5. The 88 level is vast: nearly every independent descent lands on a new plateau [measured, provisional]

- Observation (hunt, first ~45 min, `hunt/plateaus.py`): 13 arrivals at 88 (41 sampled states)
  fell into 12 distinct plateaus modulo rotation; the one repeat was the same worker's chain.
  Shapes: 7 x 3^7 (2,187 states), one 3^8, one 33·15·3^5 (120,285), one 18927·15·3^2
  (2.56 M), two giants whose closure did not finish in 10-18 minutes (depth 9). The public kste
  corpus (F3) has 17,462 isomorphism classes of 88-gate circuits.
- Mechanism [guess]: the 88 level consists of a very large number of distinct cores (sets of
  49 or so values); each is reachable from a sizeable basin of roots, and the walk never
  leaves it downward. Sampling plateaus by descents at ~2 per worker-hour cannot exhaust it.
- Prediction (to test as the hunt continues): the discovery curve (distinct plateaus against
  arrivals) stays close to the diagonal for the whole 8 h; overlap with the 52 pre-sprint
  plateaus stays near zero.
- UPDATE 06:00 UTC (`hunt/plateaus.py`, `hunt/chains_plateaus.py`, `hunt/vocab_curve.py`;
  224 sampled 88 states catalogued, time-capped): **76 new plateaus** (A 48, B 28), **0 of 224
  states on any of the 52 pre-sprint plateaus**; every chain's first 88 state was a plateau no
  other chain had reached (15 of 15). The vocabulary grew from 303 to 643 values modulo rotation
  (340 new words over 76 plateaus, 28 of which added none). Shapes: 49 x 3^7, 13 x 33·3^5,
  11 x 3^8, 10 x 15·3^5, 4 x 3^6, plus coupled products up to 3.4 M states and 3 giants.
- UPDATE 06:50 UTC: 344 states catalogued -> 107 new plateaus (A 72, B 35), still 0 on the 52
  pre-sprint plateaus; 20 of 20 chains' first 88 states on 20 distinct plateaus; vocabulary
  303 -> 783 (480 new words over 107 plateaus, 48 adding none). Discovery curve: diagonal.
- UPDATE 08:40 UTC: 419 states -> 137 new plateaus (A 86, B 51), 0 on the 52 pre-sprint
  plateaus, 25 of 25 chains' first 88 states distinct; vocabulary 303 -> 895 (592 new words,
  66 of 137 plateaus adding none).
- CORRECTION to F2's consequence and to F6's reading: a chain at 88 is not stuck re-spelling
  one circuit. Through +1 steps (acceptance allows cost <= chain best + 2) it hops between 88
  plateaus about once every 1-2 minutes: an A-arm chain visited 17 distinct plateaus in 24 min,
  another 14 in 23 min; B chains visited 2-6 in their 5 min. So for DISCOVERY of distinct 88
  cores the long stay of arm A is productive (48 plateaus from 6 chains versus 28 from 9 chains
  in B's catalogued part), and F6's "arrivals per worker-hour" is the wrong currency: the right
  one is distinct plateaus per worker-hour, where A is at least as good. Re-spelling (F2) is
  still what remove1 does; the migration is done by expand/LNS plus the +1 acceptance band.
- Consequence for the 87 question: whether an 87 exists is a global question about the map,
  not something more descents can settle by sampling; the useful tools are exact (SAT over a
  structured family, lower-bound arguments) rather than more local search. The search question
  "what determines reaching better circuits" has, on MixColumns, the answer "a down-exit from
  some 88 core, and none of the ~65 cores examined by +1 edits has one".

## F6. Restarting 300 s after the chain stops improving gives 2.4x more arrivals at 88 per worker-hour than v8's defaults [measured, hunt A/B at 2 h]

- Setup: v8, MixColumns uncapped, fresh roots only, no sharing, 6 workers per arm, 12.1
  worker-hours each (`hunt/A.toml`, `hunt/B.toml`; `hunt/descents.py`, chains from restart
  events and epochs). A = defaults (stall 900 s, doubled to 1,800 s while the chain holds the
  worker best); B = stall 300 s, incumbent_factor 1.
- Result at 2 h:

  | arm | chains | reached 88 | arrivals at 88 per worker-h | median root->88 | stay at 88 before restart |
  |---|---:|---:|---:|---:|---:|
  | A | 23 | 17 (74 %) | 1.40 | 240 s | 1,800 s |
  | B | 88 | 41 (47 %) | 3.39 | 240 s | 300 s |

- Final (A stopped at 3 h, B at 5.2 h): A 31 chains, 25 reached 88 (81 %), 1.51 arrivals per
  worker-hour; B 209 chains, 90 reached 88 (43 %), 3.15 per worker-hour, median root->88
  234 s in both. Root constructor does not predict reaching 88 in B: bp 16/38, naive 31/77,
  anneal3 23/54, paar 20/40 [measured].
- Prediction stated before the run (B >= 1.5x arrivals per worker-hour): confirmed. The cost: B
  gives up on 53 % of chains at 89 that A would have carried to 88 (A's slowest arrival took
  1,200 s; B restarts 300 s after the last improvement). Per-chain success falls, arrivals rise.
- What this is and is not: a "better search decision" for the objective "sample many
  independent 88 arrivals" (discovery, lottery). It says nothing about finding an 87, and the
  fairer discovery measure is distinct plateaus per worker-hour, because an A chain hops between
  88 plateaus during its 30 min at the bottom (see F5 update when the catalogue is in).
- Scope: MixColumns uncapped from fresh roots. The benchmark harness (bench/) is where the same
  knob will be judged on maps with known optima.

## F7. X1: fresh roots versus NIST seeds at NIST's depth (half 1 of 2) [measured, provisional]

- Setup: v8, 1 worker per arm, 1 h, no sharing, cap = NIST's depth (`x1/x1a.toml`,
  `x1/analyze.py`). W = (NIST - fresh)/NIST measures how far a fresh root gets on its own.

  | map | cap | NIST | repo best <= cap | fresh (1 h) | NIST-seeded (1 h) | W | seeded gain |
  |---|---:|---:|---:|---|---|---:|---:|
  | grostl | 12 | 410 | 366 | 582@12 | **364@11** | -0.42 | 0.112 |
  | klsw17-m-8x8-gf256-inv | 12 | 368 | 346 | 398@12 | **327@12** | -0.08 | 0.111 |
  | lw16-4x4-gf256-inv-circ | 7 | 89 | 82 | 82@5 | 82@5 | 0.079 | 0.079 |
  | skop15-8x8-gf16 | 19 | 170 | 146 | 157@11 | 151@13 | 0.076 | 0.112 |

- Half 2 (x1b, 08:25 UTC):

  | map | cap | NIST | repo best <= cap | fresh (1 h) | NIST-seeded (1 h) | W | seeded gain |
  |---|---:|---:|---:|---|---|---:|---:|
  | aes-mixcolumns | 5 | 88 | 88 | 89@5 | 88@5 (seed) | -0.011 | 0 |
  | jpst17-4x4-gf256 | 7 | 82 | 78 | 78@6 | 78@6 | 0.049 | 0.049 |
  | ss16-4x4-gf256 | 6 | 104 | 97 | **96@5** | 97@5 | 0.077 | 0.067 |
  | small-scale-aes | 5 | 43 | 42 | 42@5 | 42@5 | 0.023 | 0.023 |

- Reading: on 32x32 maps a fresh root reaches our best in minutes (W = seeded gain), as on
  MixColumns (89@5 in 1 h from one fresh root at cap 5; uncapped it is 88 in minutes, F1).
  ss16-4x4-gf256 96@5 is a new circuit (repo 97@6 / 98@4). On the 64x64 maps one worker-hour from a fresh root is far from the frontier
  (W < 0), yet a NIST-seeded worker gains 11 % in the hour and, on two maps, beat the repo's
  circuits: grostl 364@11 (repo 366@12) and klsw17-m-8x8-gf256-inv 327@12 (repo 346@12).
  These are new circuits to harvest after verification (`circuits/check.py`).
- What this says about MixColumns: the "baseline effect" reading (F4) holds for the 32x32
  class: fresh roots reach the NIST/literature level in minutes there and the seeded gains are
  the baseline's slack. On MixColumns that slack is zero because the baseline is the best
  published circuit.
- What it says about the repo: the big maps (8x8 matrices) were under-searched; the crossmap
  prediction (klsw17-m-8x8-gf256-inv 346 -> 335 in 4 worker-hours) was beaten by one
  worker-hour (327). Prediction direction right, magnitude too timid.

## F8. Engine variants on the reliability benchmark: only removing the depth window has an established effect [measured, bench agent]

- Instrument: the two MixColumns analogues where v8 is not 100 % reliable in 120 s: mc_gf16 =
  the repo's small-scale-aes (16 inputs, reference 42 = our 42@5, NIST 43@5) and mc_gf8b
  (circulant(2,3,1,1) over GF(8), other polynomial, reference 29, ours). 69 proved-optimum maps
  are all solved by v8 in seconds (1,380/1,380), so they measure iterations only.
  (`bench/REPORT.txt` sections 0 and 11, `bench/results/variants_*.csv`.)
- Variants on v8 (`quick`, single worker, 40 seeds where time allowed): stall 20 s, stall 60 s,
  LNS weight x2, expand weight x3, depth_window=none, v10-proto.
- Established: `engine.depth_window=none` reaches the reference in 0.46x the iterations
  (interval 0.24-0.80) on mc_gf16 in a same-window replication; on the 13-map hard set 0.89x
  (0.70-1.11, not established). Its circuits are deeper (42 at depth 9-11 versus 8) and each
  iteration costs 10-40 % more CPU. Success-rate differences are NOT established for any
  variant: the machine-load confound (success within a wall-clock budget moved by up to 0.4
  between time windows for the same knobs) is larger than any knob effect. v10-proto was worse
  than depth_window=none in its window and not established against default.
- Not established either way: stall 20/60 s, LNS x2, expand x3.
- Replication (bench agent, 11:48-13:12 UTC, both arms concurrent, 3 processes each, seeds
  0-39, 120 s per run, machine load 20-23; `bench/REPORT.txt` section 12,
  `bench/results/variants_r12*`): depth_window=none reaches the reference in 0.43-0.50x the
  iterations on all three maps (mc_gf16 0.46 [0.22-0.82]; mc_gf16_p1f, a circulant(2,3,1,1)
  over GF(16) with row weights 5/7 like MixColumns, 0.50; mc_gf8b 0.43); fewer iterations in
  28 of 40 seed pairs on each map (sign test p 0.005-0.017). Success within 120 s: established
  higher on mc_gf8b (0.65 -> 0.97) and mc_gf16_p1f (0.62 -> 1.00), not on small-scale-aes
  (0.68 -> 0.82, interval -0.04..+0.33). Costs: up to 28 % slower iterations, circuits about one
  level deeper (median 9-11 vs 8-10). depth_window 4 and 6 (20 seeds, mc_gf16 only): 0.90 vs
  0.65 success, median iterations 54k/34k vs 95k; suggestive, not established. All uncapped;
  a wider window trades depth for gates, so depth-capped targets may not benefit.
  Status of the knob: the one search-procedure change this sprint with an established effect
  on the MixColumns analogues, consistent with hunt C on MixColumns itself (88 % vs 81 % of
  chains reaching 88, 1.94 vs 1.51 arrivals per worker-hour; one run each, not a controlled
  comparison because C ran alongside different jobs than A).
- Reading, tied to F5: the depth window (2 levels above the chain best) limits which +1 states
  a chain may pass through; on MixColumns those +1 states are how a chain migrates between 88
  plateaus. Prediction: hunt arm C (A with depth_window none) finds more distinct 88 plateaus
  per worker-hour than A, at deeper depths. Scheduled after X1 (`hunt/C.toml`).
- Arm C result, descents (3 h, 18 worker-hours, 08:30-11:30 UTC, alongside kste1 and pt1/pt2):
  40 chains, 35 reached 88 (88 %; A 81 %), 1.94 arrivals per worker-hour (A 1.51), median
  root->88 300 s (A 240 s); 88 depths 6-8 (A 5-9), so "deeper" did not happen. Catalogue
  (partial, first 79 C states): 25 new plateaus, none shared with any other arm or the 52
  pre-sprint ones; C chains land more often on large coupled products (0.4-3.4 M states) than
  A/B chains did; per-chain migration rate is like A's (one chain: 11 plateaus in 13.5 min).
  Overall catalogue at 12:30 UTC: 644 states -> 225 new plateaus, zero overlap anywhere.
- Arm C catalogue, final (13:05 UTC): the plateau instrument cannot keep up with C. Of C's
  774 sampled 88 states only 59 were catalogued (A: 285 of 620, B: 135 of 475) because C's
  chains sit on coupled products of 10^5-3.4x10^6 states whose compression takes the full
  180 s cap each. Catalogued: 30 plateaus first seen by C (3 giants, 9 of size > 10^5), all
  new, 6 of 6 first-88 plateaus distinct, 0 landings on any other arm's or pre-sprint plateau.
  Per catalogued state C yields 0.51 new plateaus and A 0.41, but the samples are the earliest
  states of each arm and not the same fraction, so the F8 prediction ("more distinct plateaus
  per worker-hour") is NOT tested; what is measured is more 88 arrivals per worker-hour
  (1.94 vs 1.51), more 88 sample-states per worker-hour (43 vs 34), and a different kind of
  landing (large coupled products). Settling it needs a cheaper plateau identity (hash of the
  remove1-neutral core without enumerating factors), left as a next experiment.

## F9. Testing the crossmap predictions (pt1, 3 maps x 2 workers x 2 h, seeds = our best at the cap + NIST's) [measured]

  | map | cap | before | predicted (range) | after 4 worker-h | verdict |
  |---|---:|---:|---|---|---|
  | ss17-8x8-gf16 | 10 | 167 | 161 (157-163) | **161@10** (+160@11) | hit |
  | klsw17-m-8x8-gf256-inv | 12 | 346 | 335 (329-339) | 330@12 (X1: 327@12 in 1 worker-h) | beaten |
  | skop15-8x8-gf16 | 19 | 146 | 140 (136-142) | 146@14 (no gain) | miss |
  | skop15-4x4-gf256-inv | 6 | 88 | 85 (83-86) | 88@6 (no gain; new 89@5) | miss |
  | anubis-clefia-m0 | 9 | 92 | 89 (87-90) | 91@8 (+92@6) | miss (gain 1 of 3) |
  | khazad | 18 | 345 | none (rank A/B disagree) | **340@15**, 344@14 | gain 5 |
  | fox-mu8 | 14 | 505 | none (rank A/B disagree) | **500@11**, 504@10 | gain 5 |

- The rule (gain per ln(time) extrapolated from each map's own late-run slope) got the direction
  right on the two maps whose circuits were the least worked (one NIST-seeded hour each) and
  missed on the map that already had 2 worker-hours at that cap and a 14.1 % gain. Reading: the
  log-time slope decays faster than the rule assumed once the easy gains are taken; two more
  maps (pt2) will say whether that holds. New circuits: ss17-8x8-gf16 161@10 and 160@11.
- pt2 (12:52 UTC): the two 4x4 maps with a numeric prediction both missed low (0 and 1 gate
  of the predicted 3): the log-time rule over-predicts for small maps whose circuits are close
  to NIST's and already had hours of search. The two 8x8 "disagreement" maps each gained 5
  gates in 4 worker-hours. Score of the rule over 5 numeric predictions: 1 hit, 1 beaten,
  3 misses (all misses are over-predictions). Surviving, weaker statement [measured, 7 maps]:
  maps over 8x8 matrices gain several gates per worker-hour at NIST's depth whatever their
  property profile; 4x4 maps at NIST's depth gain 0-1. Size, not the rule's slope, is the
  predictor that held. New circuits: anubis-clefia-m0 91@8/92@6, khazad 340@15/344@14,
  fox-mu8 500@11/504@10, skop15-4x4-gf256-inv 89@5.

## R. Corrections from the adversarial review (review agent, 13:20-13:30 UTC; `review/REPORT.txt`, scripts `review/*.py`)

An independent agent re-derived the F1-F9 numbers from the raw data. What it changed:

- F1: by 25 min, 11 of the 12 first chains were at 88 (median 414 s), not 4 of 12 (that was
  the state at ~4 min). root->89 in 13-162 s stands. All hunt arms (A, B, C) start from the SAME
  six constructor roots (shared campaign seed), so "12 independent descents" are 6 roots x 2
  walks. The comparison with July's 2,234 s median spans an engine ~20x faster per step: it
  says nothing about iterations; "the kernel changed the picture" is a [guess].
- UNDERSTANDING 2 "any root reaches <= 89 in under 3 min": 77-85 % do; all within 7-11 min.
- F5: the catalogue covers only the earliest states (A worker-clock 332-4,893 s, B 148-4,888 s,
  C 91-1,021 s: about 18 worker-hours, not 60). Giants were keyed by their seed state and so
  could never be re-found; 5 of 18 giant/closure entries are duplicates of later product
  plateaus (230 -> <= 225). Repeats DO exist: 3 catalogued plateaus were reached by two chains,
  2 of them across arms (A free-05 / C free-00, different roots), all on the largest plateaus
  (0.8-3.4 M states); no 3^7 plateau was ever re-found. 29 pairs of plateaus differ by exactly
  2 values each (adjacent cores); at Jaccard 0.9 the 282 entries collapse to 232 components.
  The pre-sprint plateaus sit at depth 5-7 and the hunt's mostly at 7-10, so "zero overlap with
  the 52 known" is largely a different depth stratum (18 hunt plateaus at depth <= 6 are the
  comparable sample). "The 88 level is far larger than any sample" stands; "zero overlap,
  zero repeats" does not.
- F5 update (hops): consecutive plateaus along a chain differ by a median 31-38 % of values;
  only 6-13 % of hops are 2-value re-pairings: the hops are real changes of core. Confirmed.
- F2: 1,425 of 1,425 single-value 3-choice factors over 264 product plateaus XOR to zero.
- F6: on the full data B/A = 2.1x arrivals per worker-hour (3.15 vs 1.51; 2.15x per
  iteration), not 2.4x (the 2 h snapshot). Iterations per worker-hour were within 4 % across
  arms A/B/C despite changing co-tenants, so per-worker-hour rates are fair. B's per-chain
  median root->88 is censored by its own 300 s rule and is not comparable with A's.
- F8 hunt C vs A: 35/40 vs 25/31 chains and 1.94 vs 1.51 arrivals per worker-hour is a rate
  ratio of 1.29 with a Poisson interval of roughly 0.8-2.2 (Fisher p ~ 0.5): inside the noise,
  not merely "not controlled". The shared roots allowed a paired reading that was not used.
- F8 bench: the sign tests and McNemar are correct (failures counted as infinite, which is
  conservative). But restricted to seeds BOTH arms solved, the per-seed iteration ratio is 0.59
  on mc_gf16 (22 pairs) and 0.93-0.98 on mc_gf8b and p1f: on two of the three maps "half the
  iterations" is the default's failures pulling its median to infinity, i.e. a success-rate
  effect, not a speed-up on seeds both solve. Corrected statement: depth_window=none succeeds
  far more often within the budget on mc_gf8b and p1f (0.65 -> 0.97, 0.62 -> 1.00) and is
  faster per seed on mc_gf16 only. All uncapped; for the per-depth record table it may be a
  loss, and no capped test exists.
- F9: the score (1 hit, 1 beaten, 3 misses) is right and rule B / the khazad-fox-mu8 test were
  fixed before the runs (not hindsight). But over the 7 tested maps Spearman of realised gain
  with size (k) is only +0.56, and skop15-8x8-gf16 gained 0 in 4 worker-hours, so "8x8 maps
  gain several gates whatever their profile" is 4 of 5. Run-to-run spread is ~3 gates on
  64x64 maps and ~1 gate on 4x4 maps at NIST's depth, so predictions and gains of 1-3 gates
  are not distinguishable from repeats of the same search.
- F4: rw_max and log(direct) correlate at +0.92 across the 49 batch maps; the row-weight
  partial (+0.41) rests on little residual variation and was never tested on fresh evidence:
  tag it [in-sample]. F7 X1 numbers reproduce; n = 1 per cell; "compute-limited, not
  search-limited" is a [guess].
- Missed by the sprint, now adopted as next experiments: (1) landing probability scales with
  plateau size, so arm C (which lands on huge coupled products) may find FEWER distinct cores
  per worker-hour than A: a size-weighted capture-recapture estimate over all sampled states is
  the right instrument (sig.py, relaunched 13:32 UTC); (2) the 88 level is a connected graph
  of cores under the +1 band, and whether an 87 is reachable is a property of that graph
  (down-exits, distance from where descents land), not of its node count: draw it from the
  sampled transitions; (3) use the shared first roots of hunt D as a paired design.

## F3. Context from the literature and a public corpus (lit agent, 2026-11-07) [cited]

- 88 XOR is now published: J. Jean, ePrint 2026/1481 (July 2026); earlier 97 (2017), 95, 94,
  92 (2019-20), 91 (2021), 89 (Sun-Yang-Li 2025). Nothing below 88 is claimed anywhere found.
  So 87 would be a new record; 88 is a tie with the literature and NIST.
- github.com/kste/mixcolumns_xor holds 18,938 88-XOR MixColumns circuits (17,462 isomorphism
  classes claimed) and a README arguing an "88-XOR barrier" from a bit-slice block decomposition
  plus SAT/MITM refutations of 87 in stated scopes (73 "double-optimal" circuits; sub-DAGs; a
  1,607-signal pool; a tropical DP). None of the refutations is a general proof; the scopes are
  circuit classes around known 88s.
- kste agent results (2026-11-07 05:20 UTC, `kste/REPORT.txt`, own parser and checker) [checked]:
  - all 18,938 published circuits are exact 88-gate MixColumns circuits (same bit convention
    as ours); 17,462 distinct value sets, 17,337 modulo rotation; depths 5-12.
  - they lie on only **49 plateaus** (remove1 closures as products); one plateau of 60·3^6
    states holds 64 % of the corpus; the 47 circuits of circuits_1.txt each seed a plateau and
    the rest are walks around them. The 46 depth-5 circuits lie on 2 plateaus, one of which is
    our `mc88_other44`. Overall overlap with us: 2 of their plateaus touched by our runs; our
    repo 88@5, NIST's 88@5 and 536 of 539 live hunt states are on none of theirs.
  - the README's "1,607-signal pool" cannot be reproduced (their helpers give 1,073 values,
    1,702 closed under rotation); 315 of 389 hunt samples use helpers outside even that pool,
    so their "UNSAT at <= 87 on the pool" does not cover our region.
  - the six block "floors" (3, 20, 10, 24, 10, 16) are exactly the corpus minima under one
    reading (classify each value by the input bit positions it touches); all our 88s respect
    them too (a regularity of known 88s, not a proof). Read as sub-maps of output bits, SAT gives
    only weaker bounds (>= 9, 12, 13 on three blocks; the claimed values timed out).
  - no encodings, logs or proofs are in the repo; none of the four refutations can be rerun.
  - J. Jean's PDF could not be fetched (bot check); depth and method unknown.
  - Conclusion: 87 remains open; the public evidence is "many 88s, all sealed at +1", the
    same picture as ours, from an independent generator in a largely different region.
