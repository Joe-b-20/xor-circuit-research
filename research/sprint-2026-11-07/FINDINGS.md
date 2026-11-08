# Sprint 2026-11-07: findings

Each entry: observation, mechanism (plain words), prediction that could be wrong, test, what
survived, limits. Tags: [proved] [checked] [measured] [cited] [guess]. Scripts are named; raw
data lives in `~/xs-campaigns/2026-11-07-sprint/`.

## F1. Descending to 88 on MixColumns is cheap; the difficulty is entirely below 88 [measured; counts corrected by R: 11 of 12 first chains at 88 by 25 min, median 414 s; the July comparison spans a ~20x faster engine and says nothing about iterations]

- Observation (hunt, first 25 min, 12 fresh-root chains, v8 uncapped): every chain reached <= 89
  within 10-162 s of its root; 4 of 12 reached 88 within 50-216 s. (`hunt/descents.py`)
- Compare: July 2026 engine, every 88 within 3,855 s of its root, median 2,234 s (restart.root_seconds
  doc string). The v5+ incremental kernel changed the picture: 88 is minutes away from any root.
- Prediction: with hours of such descents, the number of distinct 88 plateaus reached will tell
  whether the 88 level is a small finite set (saturating curve) or vast (linear growth).
- Status: open; curve to be read from `hunt/plateaus.py`.

## F2. A 3-way plateau factor is the pairing choice of an unshared 3-input XOR tree [checked: 424/424 factors on 52 plateaus, then 1,425/1,425 over 264 plateaus (R)]

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

## F6. Restarting 300 s after the chain stops improving gives 2.1x more arrivals at 88 per worker-hour than v8's defaults (2.4x at the 2 h snapshot; R) [measured, hunt A/B, full 5 h]

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
- Cheap identity (13:35-14:00 UTC, `hunt/sig.py`, `hunt/sig2.py`, logs `sig.log`, `sig2.log`):
  one remove1 fan per state, identity = the state plus every value a neutral move can add (the
  1-step closure's value set), modulo rotation. Validated on the 479 catalogued states: it
  never merges distinct exact plateaus (1 merge of 375) but SPLITS 59 of 230 exact plateaus
  into 2 signatures (46 with the core-only variant, 47 with a 2-step closure; 13-14 of the split
  ones are coupled products > 1e5 states, the rest ordinary products whose members see
  different fans). So the signature count is an upper bound on distinct plateaus, inflated by
  at most 1.63x (375/230) and more on the large coupled plateaus that arm C favours.
  Applied to all 1,869 sampled 88 states: A 620 states -> 497 signatures (30 per delivered
  worker-hour), B 475 -> 400 (14; B spends less time at 88 by design), C 774 -> 706 (39);
  new-signature rate per sampled state A 0.80, B 0.84, C 0.91; discovery curves linear to the
  end in every arm (no saturation); 5 signatures of 1,600 seen by more than one worker.
  Reading: C delivers 1.3x the distinct signatures of A per worker-hour, but since its
  plateaus split more, the true ratio of distinct cores lies somewhere between ~0.8 and 1.3:
  the F8 prediction stays UNDECIDED. Hunt D (concurrent, shared first roots) plus this
  identity is the next reading; an exact identity for coupled products is the missing tool.

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
- Rescored (review3) on the 5 further maps the sweep covered that `crossmap/predict.csv` had
  predictions for, with the caveat that the sweep gave 1 worker-hour instead of the predicted 4 x 1 h:
  grostl 355 (349-359) at depth 12 -> 364@11 (miss, different protocol); jpst17-8x8-gf256-inv 483
  (479-487) -> 494@10 (miss); skop15-8x8-gf256-inv 325 (321-327) -> 322@13 (hit); klsw17-m-8x8-gf256
  342 (340-344) -> 321@10 (beaten); klsw17-m-8x8-gf16-0x13-inv 160 (158-161) -> 163@11 (miss). Rule
  score over 10: 2 hits, 2 beaten, 6 misses. F4's "no 16x16 map gains a gate" was never tested.

## F10. Sweep: the 12 remaining maps over 8x8 matrices, 1 worker-hour each at NIST's depth, seeded from our best at the cap and from NIST's circuit (sw1 12:52-13:52, sw2 13:58-15:05 UTC) [measured]

  | map | cap | ours at <= cap before | after 1 worker-hour | gates gained at <= cap |
  |---|---:|---:|---|---:|
  | grostl | 16 | 350@16 | 349@15 | 1 |
  | khazad | 18 | 345@15 | 344@15 (pt2's 340@15 already better) | 1 |
  | whirlpool-maelstrom | 11 | 394@9 | **391@9**, 390@10 | 4 |
  | fox-mu8 | 14 | 505@11 | **502@10**, 500@11 (pt2 found 500@11 too) | 5 |
  | jpst17-8x8-gf256-inv | 11 | 493@11 | 494@10 (beats 496@10; nothing at 11) | 0 |
  | bkl16-8x8-gf256 | 10 | 442@10 | **439@9** | 3 |
  | klsw17-m-8x8-gf256 | 11 | 347@6 | **321@10**, 327@9, 346@8 | 26 |
  | skop15-8x8-gf256 | 8 | 418@8 | 417@8, 416@9 | 1 |
  | skop15-8x8-gf256-inv | 13 | 331@13 | **322@13**, 323@12 | 9 |
  | ss17-8x8-gf256 | 9 | 392@8 | 390@8, 389@10 | 2 |
  | ls16-8x8-gf256 | 9 | 404@8 | 403@8 | 1 |
  | klsw17-m-8x8-gf16-0x13-inv | 12 | 163@12 | 163@11, 164@10 | 0 (depth only) |

- 10 of 12 maps gained gates at or below NIST's depth in one worker-hour (4 of 12 by 3 or more);
  the two that did not still produced a shallower circuit. With X1, pt1 and pt2 this makes 16 of
  19 one-to-four-worker-hour trials on maps over 8x8 matrices that gained gates at NIST's
  depth, against 1 of 6 on 4x4 maps (F7, F9). The coarse statement in F9 holds on fresh maps
  [measured, 12 maps].
- The largest gain, klsw17-m-8x8-gf256 347@6 -> 321@10, is a depth-budget effect: our earlier
  circuits for that map were at depth 6 and at depths 12-15 (336@12 ... 326@15); nobody had
  searched depth 9-11, and one worker-hour there beat every deeper circuit we had. The same
  pattern (gates minimum at a middle depth, not at the deepest) shows in skop15-8x8-gf256-inv
  (322@13 vs 318@14 and 333@12 before) and grostl (349@15 vs 350@16). Conjecture, testable on
  the next big map: the first worker-hour at an unsearched depth 1-2 above the shallowest
  good circuit gains more than another hour at an already-searched depth.
- Records above the cap (416@9 with cap 8, 389@10 with cap 9, 390@10 with cap 11) are kept by
  the engine as any-depth bests; they are listed because they beat what we had at that depth.
- Harvest (15:05-15:15 UTC): 44 circuits added, 37 dominated ones removed, 208 circuits for 59
  maps, all verified by circuits/check.py; commits d281a78 and 5edcd1a. The harvest script had
  dropped a point recorded by two runs with the same gates@depth (fox-mu8 500@11, pt2 and sw1),
  since each record "dominated" the other; fixed in `harvest_sprint.py` [implementation].

## F11. The 88 level as the walk sees it: a sparse sample of chain trails (8 meetings, as independent wandering on ~1e5 nodes predicts); no down-exit at any of 1,869 sampled states (graph agent, `graph/REPORT.txt`; corrected by review 2) [measured]

Nodes = cheap plateau identities (v3 signatures merged by exact key where catalogued: 1,600
signatures -> 1,454 nodes, an upper bound on exact plateaus, ~900-1,000 [guess]); directed edges =
consecutive 88 nodes visited by one chain (hunt arms A, B, C: 4,807 samples at 30 s, 146 chains
with an 88 sample, 1,462 visits, 1,418 hops).

- Graph: 139 weakly connected components; 133 are one chain's own trail; 8 of 1,454 nodes
  (0.55 %) were entered by two chains, 3 of them the three largest catalogued plateaus (0.8-3.4 M
  states), the only hub-like feature. Degree 2 for 1,122 nodes, 1 for 248; degree > 2 comes from
  a chain stepping back to a node it left 2-17 hops earlier (102 of 1,418 hops, 7.2 %). 93 % of
  visited nodes were never revisited by anything.
- Hops: ~44 node-visits per chain-hour pooled (A median 34/h, C 56/h; B is cut by its 300 s
  rule), a SAMPLER property (F30: the real re-entry rate is ~2,600 per chain-hour; the sampler sees
  ~3 % of stays), a floor by a factor of ~35: 68 % of hops between distinct nodes (59 % even between exactly catalogued,
  provably distinct plateaus) show no 89 sample, i.e. the excursion was shorter than 30 s. The
  engine's ledgers count ~24 accepted non-neutral moves per second during 88 stays; the in-engine
  log (F30) measures 0.72 departures from 88 per second, so the earlier "~12 per second [guess]" was
  wrong; 39-45 % of sampled instants after a chain's first
  88 are at 89. The walk lives on the 88+89 band and dips into 88 nodes. A hop changes a median
  30 % of the helper set modulo rotation (q1 25 %, q3 40 %) against 16 % for 30 s of neutral
  walking inside a node: neighbouring plateaus share ~70 % of their core; the reviewer's 31-38 %
  reproduces.
- Down-exits: none. 0 samples, records or engine events below 88 in any arm; `pes_lib.fan` on
  all 1,869 sampled 88 states gives 0 states with a down move (8-44 neutral moves each by
  `review2/fans.py`, 10-28 by `graph/graph.py`'s count, mode 16 in both;
  the TOPK = 16 candidate cut never bound, so the check is exhaustive for remove1 at those
  states [review 2, `review2/fans.py`]). For the catalogued plateaus the statement is exhaustive
  for every member of the 155 plateaus of <= 2e4 states and for the fanned members (seed and
  factor-local closures) of the other 127.
- Landings are not special: first 88 nodes (146 chains, 146 distinct nodes) and later nodes have
  the same size median (6,561 states) and depth median (8); only 2 first nodes were ever entered by
  another chain. Later visits drift deeper (tail to depth 16 in arm C).
- Reading (corrected, R2): the 8 cross-chain meetings among 1,462 visits are exactly what 146
  chains wandering INDEPENDENTLY over ~1.3e5 effective nodes would produce (null model,
  `review2/nullmodel.py`: 387 meetings expected if only the 1,454 seen nodes existed, 127 at
  7,300, 10.4 at 1e5; hunt D at 2.4 h gives the same 1.3e5 out of sample). So "disjoint trails"
  is the sampling-sparsity consequence of the level's size (F12), not a second fact, and the
  sampled graph carries no information about connectivity: isolated trails and one connected web
  sampled at 1 % fit equally. What stands: at every sampled 88 state the remove1 move has no
  down-step [measured, exhaustive, re-run by review 2 on all 1,869 states], and the level holds
  1-2 orders of magnitude more plateaus than the walk has sampled [estimated]. Whether some
  unsampled 88 state has a down-step, or a path through 89+ reaches 87, is open; this data does
  not bear on it. "Hops are local so a chain stays in its neighbourhood" stays a [guess]: 30 %
  change per hop at 44+ hops per hour turns the helper set over completely within hours.
- What 30 s sampling cannot see: departures to 89 shorter than an interval, hence the true number
  of plateau changes per hour, and whether chains pass through common nodes between samples.

## F12. How many 88 plateaus: at least ~2,500, probably ~1e5 (estimate agent, `estimate/REPORT.txt`) [estimated]

Landings are counted per chain (one root until a restart; a chain visits a median 4 plateaus
through 89 states, up to 22), on the exact catalogue (40 chains, 212 exact plateaus after dropping
18 giant entries whose identity is unreliable) and on the cheap signatures (146 chains, 1,600
signatures).

- Landing probability is not uniform [measured]: equal probability is rejected (permutation
  p = 5e-5); the 3 exact repeats are the plateaus ranked 1, 4 and 9 by size (3.4e6, 3.1e6, 8.2e5
  states) and amount to ~2 independent events (two are neighbours of one family). The 5
  signature repeats were all checked exactly and are genuine cross-chain repeats at sizes 6,561,
  2,187, 2,187, 265,356 and 40,338, so small plateaus do repeat. For plateaus whose factors are
  all 3-way the signature is an exact identity (94 of 94). Shared first roots across arms created
  no repeat. Fit landing ∝ size^alpha: catalogue alone alpha = 1.34 [0.55, 3.25]; with the small
  signature repeats alpha ≈ 0.75-1.0 (roughly proportional to size) [estimated from ~6 coincidences].
- Counts [estimated]: Chao2 on exact plateaus 7,300 [1,600, 21,000] (a floor under
  heterogeneity); effective number of equally likely plateaus 7,300 [2,500, 35,500], so N >= ~2,500
  for any landing distribution; plateaus below 1e5 states alone: 0 coincidences in 15,188 chain
  pairs, N >= ~4,100; plateaus >= 1e5: ~180 [64, 900]. Size-weighted model: alpha 0.5 / 0.75 /
  1.0 / 1.34 gives 22k / 79k / 400k / 5.3M (upper ends unbounded). Sample coverage 0.029: ~97 % of
  landing probability is on plateaus never seen. Signature companion: Chao2 254k [110k, 588k],
  ~156k after the 1.63x over-split, an overstatement since big plateaus split 2.2-2.3x.
- Verdict (with review 2's conditions): a few hundred large plateaus take most of the visits; the
  long tail of small ones makes up most of the count; plausibly 3e4-5e5 exact 88 plateaus (the
  central 1e5 moves by an order of magnitude either way depending on the 18 excluded giant
  entries' true sizes and on the effort ratio behind the signature alpha), floor >= ~2,500 at
  95 % assuming only independent, exchangeable chains (a chain-pair analysis gives >= 3,041; the
  node-level meeting count implies >= ~3e4 even after a generous over-splitting correction).
  "Landing probability" is really a VISIT exponent (landing or hop). The search cannot enumerate
  the level.
- Giants resolved (giants agent, 19:50 UTC, `giants/REPORT.txt`): the 18 giant entries all failed
  the same way in `plateaus.py` (factor phase hit 180 s on one large coupled factor of 3e3-7e4
  choices, fallback closure stopped at 1 state). With closure_limit 3e5 and 900 s, 10 of 18 are
  resolved exactly: 5 are members of already-catalogued plateaus (1.2e5-2.6e6 states, each visited
  by the same chain only), 3 are new plateaus (93,474 = 3462x3^3; 623,052 = 69228x3^2; 188,568 =
  62856x3), so 8 distinct plateaus, none shared across chains; 8 entries stay unresolved (one
  >= 41,214 states, seven not compressed for lack of wall time; all seven are provably outside the
  267 known products). Corrected estimates [estimated]: Chao2 7,518 [2,703, 21,653]; D2 7,537
  [2,579, 36,548]; chain-pair N_eff 11,306 [3,130, 93,353]; alpha 1.37 [0.55, 3.30]; size-weighted
  totals 22,867 / 81,773 / 412,972 at alpha 0.5 / 0.75 / 1.0. Adding the 8 unresolved as separate
  single-chain plateaus of 3e4-3e6 states moves alpha within 1.12-1.45. The review's alpha = 0.5
  scenario needed giants of ~1e7 states; the resolved ones are all <= 2.6e6, so it is no longer
  realistic. "Plausibly 3e4-5e5" survives (upper end to ~7e5 only if all 8 unresolved are distinct
  ~3e6 plateaus); the remaining uncertainty is alpha, not the giants, and the R2 caveat is dropped.
- Next measurement (no new search): the exact catalogue on the remaining ~1,390 sampled 88
  states takes chains from 40 to 146 and chain pairs from 22k to 1.27M, expected ~100
  coincidences instead of 3, pinning alpha and N; ~1-2 min per state single-threaded (a day on one
  core, hours on several), fixing the giants' identity in the same pass.

## F13. Scoped exact search for an 87 around our 88 circuits: 43 refutations, 8 timeouts, no 87 (sat agent, `sat/REPORT.txt`, `sat/sat87.py`) [measured]

- Reconciled SAT count at 22:30 UTC (`sat/results*.jsonl`, 37 circuits): 2,073 instances, 2,057
  UNSAT, 0 SAT, 16 timeouts (hardest UNSAT k = 12); one-seed windows k <= 10, output blocks k <= 12,
  1,084 two-seed windows k <= 9 on the repo circuit; batch2's 12 shards continue on 20 further
  circuits. The union of removed values over refuted windows covers 81 of the repo circuit's 88
  values (72-74 for the other circuits). Earlier counts in this section (43, 153, 1,117) are dated
  snapshots. Confirming hardness data: stage 3 k = 9, free = 4 at 50-140 s; stage 2 k = 11, free =
  2-3 at 185-450 s. Status at the shutdown of 21:41 UTC: 1,122 instances in the first batch; relaunched
  21:46 together with batch2. Earlier status (16:50 UTC):
    family          UNSAT  SAT  TIMEOUT  other  hardest solved k
    stage1/A          131    0        0      0  8
    stage1/C           22    0        2      0  12
    total 155 instances: UNSAT 153, SAT 0, TIMEOUT 2, wall 1.9 h; hardest UNSAT k overall: 12
- Formulation (value-set form): keep a subset K of an 88 circuit's values such that inputs ∪ K is
  split-closed (every kept value is the XOR of two earlier ones); remove W, k = |W|; ask CaDiCaL
  (via pysat) for m = k-1 new gates, each the XOR of two distinct available values, such that every
  output not in K is a new gate. Proved: the instance is SAT iff some split-closed value set
  containing K ∪ outputs has at most |K| + m values. So UNSAT at m = k-1 proves that NO circuit
  with <= 87 gates, of any depth and any helper values, contains K. No pool restriction (kste's
  scoped refutations restrict the candidate pool), no wiring assumption; strictly stronger than
  remove1 flatness on the same window. Encoding validated: m = k is SAT and the decoded circuit
  re-verifies as 88@5. Review 2 re-derived the soundness (the equivalence rests on a fresh-split
  padding lemma, not on duplicates; the operand ladder and the consecutive-gate lex break are
  sound; UNSAT does not depend on the pruning constraints: 4 windows re-solved UNSAT under all
  four (distinct, symbreak) settings). "Contains K" means value containment in any wiring.
- Outcomes on three structurally different 88 circuits (repo 88@5; two hunt states with different
  cores, depth 12 and 8): 51 instances, 43 UNSAT, 8 timeouts (60-120 s), 0 SAT. Repo circuit:
  all 27 one-seed windows (a value's upward closure plus dead helpers) with k = 4..8 UNSAT in
  0.2-49 s; k = 9-10 timed out; all 8 half-byte output blocks (k = 4-9) and bytes 2-3 (k = 8, 9)
  UNSAT, bytes 0-1 (k = 11, 13) timed out. The union of refuted windows covers 73 of the repo
  circuit's 88 values: every <= 87 circuit misses at least one value of each of 37 kept sets of
  79-84 values. The plateau's mobile part is not a local window (its closure forces k = 21-32)
  and was not refuted.
- Frontier at 60 s on a loaded machine: k <= 8 for helper windows, k <= 9 for output blocks;
  instances are small (6k variables, 128k clauses at k = 9), so the barrier is search. Hardness
  was first read as tracking the number of free (non-output) new values rather than k; the
  running batch refutes that strong form (free = 1 climbs from 0.6 s at k = 4-5 to 1,257 s at
  k = 12): both k and the free count matter [measured, review 2].
- What this does and does not say: an 87, if it exists, shares no refuted 79-84-value kept set
  with these three circuits; it may still share a smaller part, or lie near another plateau. The
  machinery (one core, exact, strictly stronger than the walk's view) is the right instrument for
  the "exact or structural methods" route; the recommended continuation is a longer single-core
  batch (k = 9-10 windows at 900 s, byte blocks at 1,800 s, two-seed windows) across more cores.

## I. Interpretation, tightened (2026-11-07 17:40 UTC, on the owner's five points)

**I.1 The resistance at 88.** What is established: (a) at every one of 1,869 sampled 88 states
the complete remove1 neighbourhood (remove any one helper, repair with one exact value) contains
no state with fewer gates [checked, exhaustive per state, F11]; (b) for the 88 plateaus whose +1
band PES explored (mc24: 49 plateaus; kste1: 19 compressed so far), every RESOLVED +1 exit
descent ends on the home plateau or on another 88 plateau, and none ends below 88; but 56 % of
the +1 descents (kste1 final at 21:41 UTC, killed at 13.2 h: 24,475 of 43,113 = 56.8 %, with
22 of 119 compressed plateaus' +1 passes complete, 1,117 "new" landings, 0 lower states; mc24: +1
pass complete on 37 of 49 plateaus, 51,443 of 79,786 = 64 % unresolved pooled) were CUT at the
descent's state bound before landing anywhere and are unresolved [measured; `pes-kste/pes/
pes2_tasks.py: classify`; the bound `cfg.bound_plus1` = 400 visited states, which cuts exactly the
long descents]; the +2 band was descended only partially (mc24: 38,748 descents on 37 plateaus, 87 %
unresolved, 0 lower; 24,284 LNS rebuilds, 40 % unresolved, 0 lower; the archive's Barrier-Tree
plateau: 0 of 13,212 classes, `import/zip/guides/BARRIER_TREE_FINDINGS.md`); (c) the scoped SAT refutations (F13) exclude every <= 87 circuit containing any of ~2,060 kept sets of
76-84 values of 37 different 88 circuits (22:30 UTC).
What this adds beyond the stopping condition of polishing: polishing stops when its OWN move
finds nothing in the time it tried; (a) is the exhaustive statement for that move at every
sampled state, (b) extends it one level up for a minority of the exits, (c) replaces "no single
move" by "no circuit at all" for the refuted windows. What it does NOT establish: that heuristic
search cannot find an 87. Paths through 89 that the bound cut (the majority), paths through
90 or higher, moves that change three or more values at once, and starting regions nobody has
sampled (97 % of the landing probability, F12) are all open. The earlier wording "every +1 exit
goes home or to another 88" was an overstatement and is corrected in UNDERSTANDING and
CHECKPOINT: it holds for the resolved exits only.

**I.2 The role of exact methods.** One verified 87 proves existence whatever finds it; the
local search, the SAT batch and any constructor are equally valid routes to that. Proving that
no 87 exists needs an argument over the whole class of unrestricted XOR circuits; exact
computation contributes pieces of such an argument only with their scope attached: the F13
refutations are statements about circuits containing a specific kept set, the owner's 75 bound
is a full-class statement (replayed and audited, see I.6), and nothing in between exists yet.

**I.3 The plateau counts.** Definition used throughout: a plateau is a connected component of
the graph whose vertices are 88-gate value sets and whose edges are remove1-neutral moves
(remove one helper, add one exact value, gate count unchanged, no depth restriction). Exact
plateaus are computed by closure (PES `compress`, complete enumeration of the component, hashed
canonically modulo the Z4 byte rotation), so two exact keys are distinct components by
construction [checked]. The cheap identity (v3 = canonical value set of the 1-step neutral
closure) never merged two exact plateaus in 230 tests but splits coupled ones (1.63x), so
signature counts are upper bounds [measured]. Count reconciliation (22:00 UTC): 215 exact sprint plateaus + 52 pre-sprint = 267 products; 8 giant
keys unresolved (2-8 plateaus); hunt D's 2,445 states not yet catalogued; "230" = 212 exact + 18 giant
keys, "282" = 230 + 52 keys (5 duplicates), "<= 225" = 230 minus the 5 duplicates; 1,454 nodes /
1,600 signatures are the cheap identity's upper bounds. The 1.63x over-split was measured on the
early, mostly small catalogued states and rises to 2.2-2.3x on coupled plateaus, which arms C and
DN favour, so signature rates for those arms are the least reliable. The plateau definition is
relative to the move set and depth cap. Non-overlap between sampled walks (F11: 139
components for 146 chains at 30 s sampling) is an observation about where chains were seen,
NOT a proof of disconnection: chains hop through 89 states that the sampler mostly misses, and
components would merge if two chains ever passed through one node between samples. The
population estimate (F12) assumes independent chains, a landing probability proportional to
size^alpha with alpha fitted from about six coincidences, and unseen plateaus resembling the seen
small ones; the part free of assumptions on the landing distribution (it still assumes independent,
exchangeable chains) is the floor (effective number >= ~2,500 at 95 %, conservative: the
node-level meetings imply >= ~3e4), its model part is the order of magnitude (3e4-5e5).

**I.4 The SAT exclusions (F13), stated exactly.** Fixed: a kept set K of values from one
specific 88 circuit, chosen so that inputs ∪ K is split-closed (79-84 of its 88 values). Free:
everything else: the k-1 new values may be any 32-bit masks, computed in any order and at any
depth, with any fan-out, from any two available values; no layout, no helper bank, no
cancellation assumption, no pool restriction. Restriction imposed by the encoding: circuits are
taken as value sets (lossless for linear maps, since depth and gates are functions of the set),
gates are 2-input XORs (XNOR/constants are irrelevant for a linear map), and the new gates must
all be distinct from each other and from K (sound: duplicates never help). An UNSAT instance
therefore excludes exactly the circuits with <= 87 gates whose value set contains K; it says
nothing about circuits missing even one value of K. Union over the repo circuit's 37 refuted
windows: any 87 differs from that circuit in at least one value of each of 37 sets of 79-84
values. POWER CAVEAT (F29): the archive's identical instrument returned UNSAT on 17 of 17 control
windows around circuits with a provably smaller circuit, because improvements sit at mask distance
~42; until the sprint's own slack-1 control (R0, running) says otherwise, these refutations are
theorems about kept sets, not evidence against 87. Over all refuted windows (22:30 UTC) the union of
removed values covers 81 of the repo
circuit's 88 values and 72-74 of each other circuit's. The 1,084 two-seed windows (k <= 9, repo) are
the first non-local statements (pairs of corners). The 16 timeouts are open windows. None of this
bears on 87s away from these 37 circuits. Advance: it turns a "no move" fact into a "no circuit"
fact for each window, at seconds per window; the frontier is k = 12 at 600-1,300 s and the running
campaigns push it.

**I.5 The cross-map pattern.** Observation [measured, F7/F9/F10; denominators itemised there]: 16 of
20 one-to-four-worker-hour trials on maps over 8x8 matrices (X1 2/3, pt 4/5, sweep 10/12) gained at
least one gate at NIST's depth, about 10 of 20 at least three (the run-to-run spread); 2 of 7 on 4x4
maps gained one gate. The sweep's seeds were our best at the cap plus NIST's, so explanations (i) and
(ii) below are confounded by design; (iv) is a measurement caveat, not a mechanism.
Candidate explanations: (i) the large maps are compute-limited (their circuits had received
few worker-hours at that depth); (ii) differences in starting-circuit quality (seeds were our
best at the cap plus NIST's; several 8x8 maps' best were at other depths, so the cap band had
never been searched, e.g. klsw17-m-8x8-gf256 347@6 -> 321@10); (iii) 4x4 maps already sat at
the floor the search can reach (X1: fresh roots reach the repo best within the hour on every
4x4 map); (iv) run-to-run spread (~3 gates on 64x64 maps, ~1 on 4x4) makes 1-3-gate gains on
large maps indistinguishable from repeats. F25 (23:50 UTC) separates them on the existing run data: (ii) is excluded as a general mechanism,
(iii) is supported for 4x4 maps, prior worker-hours were equal across classes so (i) is untestable
in its literal form, and the gains follow a log-decaying curve from ordinary one-hour endpoints.
Before F25 the text read: (i)-(iii) are not separated by the present data: all
three predict the observation. Distinguishing tests: a second worker-hour on each sweep map
from its new best (if (i), gains continue at a similar rate; if (ii), they stop once the band
is searched); a 4x4 map given a depth band it was never searched at (if (ii), it gains too);
and repeats of the same hour from the same seed to size (iv). None of these can run while the
machine is full; they are the first compute to spend when threads free up.

**I.6 Bounds, with scope (75 replayed here in 137 s and 93 replayed here in 2,028 s, F16/F24; arguments
read, not checked; the 2026-11-04 audit was the owner's own; the owner's latest depth-3 checkpoint
passes its default replay, its full core search was not completed here). Inverse: also 88-gate unrestricted
constructions at depths 19 and 33 in the archive; 118@5 optimality open. Conditional / unverified
results with scope: odd-helper theorems (h <= 2 => G >= 90 [read; h = 0, 1 proofs absent]); "<= 1
outside value => >= 84" [read]; kste pool-restricted refutations (F3); the Barrier-Tree partial exits.**
Unrestricted XOR circuits for forward MixColumns: 75 <= C <= 88 (75: the owner's computer-
assisted proof, public in the repo, fresh replay 52 s and mathematical audit on 2026-11-04 with
no substantive gap; 88: verified construction). Depth at most 3: 93 <= C3 <= 97 (93: proof,
replay 962 s, audited; 97: verified construction; the proposed 97 optimality proof is OPEN per
the owner's latest checkpoint of 2026-11-05 and corrected in several places). Depth 4: 89 is a
verified construction; no proved lower bound beyond the unrestricted 75 is recorded as
established. Inverse: depth >= 5 is established (output weights 19 vs depth-4 support <= 16);
118@5 is a construction. These are the strongest justified starting bounds; any improvement
must be new relative to them. Relative to the published literature (F19) the 75 and the 93 are
already new: the best published unrestricted lower bound for this matrix is 32. A claim of 87
impossibility is open: neither search failures nor the available identities prove it (owner's
status guide).

## F14. Hunt D (depth window 2 / 4 / none, 4 MixColumns workers each, same first roots; planned 13 h from 15:06 UTC, KILLED at 21:41 UTC (6.6 h wall, 6.4 h per worker; the Windows share was lost at ~20:45, the Linux processes ran until the shutdown at 21:41): predictions registered at 2.4 h, scored on the data to 21:41 [measured]

Predictions written at 17:35 UTC (the 2.4 h snapshot below was seen; nothing later):
- P1 (from hunt C, F8): DN (no window) reaches 88 at least 1.2x as often per worker-hour as D0.
  At 2.4 h: D0 1.74, D4 1.63, DN 1.51 arrivals per worker-hour (15/14/13 chains): P1 is
  already behind; if the 13 h totals keep DN/D0 below 1.2 it is refuted and hunt C's 1.94 vs
  1.51 was noise, as the review said.
- P2 (from the F8 mechanism, "the window limits migration through 89"): DN visits more DISTINCT
  88 plateaus per worker-hour than D0 (cheap identity v3, upper bound). At 2.4 h: D0 20.8, D4
  28.2, DN 27.4 per worker-hour (199/270/262 signatures from 272/344/280 states); per worker
  (same first roots) DN > D0 on 3 of 4 workers, D0 > DN on free-00 (100 vs 40). Prediction: the
  13 h ratio DN/D0 is >= 1.2 and holds on at least 3 of 4 paired workers.
- P3: the 88 states DN and D4 land on are deeper than D0's (window off = depth free). At 2.4 h
  the modal depth is 8 in all arms but DN/D4 have tails to 13-14 and D0 stops at 11.
  Prediction: the fraction of 88 states at depth >= 10 is at least twice D0's in DN.
- P4 (from F11): chains of different arms share almost no plateau even with the same first
  root: at 2.4 h 2 signatures of 729 are shared, both between D0/free-02 and D4/free-03
  (different roots). Prediction: fewer than 2 % of signatures are shared across arms at 13 h.
- P5: no arm produces an 87 (0 of 729 states below 88 so far). A single 87 refutes this and
  is harvested at once.
Registered by review 2 at 17:40 UTC (seen: the 2.4 h snapshot, nothing later):
- Q1 (tests F11's reading): with P = cross-chain distinct-node incidence pairs over all D chains
  at 13 h and M = v3 nodes entered by >= 2 chains, M = P / 1.3e5 within the Poisson 95 % interval
  (P ~ 6e6 -> M ~ 46, [33, 61]). Below: genuine locality of trails; above: hubs; inside: one pool
  sparsely sampled.
- Q2: P / M at 13 h lies in [5e4, 3e5].
- Q3: among D's shared v3 nodes that are exactly catalogued, at least half have >= 1e5 states; the
  first-landing plateaus of D's chains are pairwise distinct (<= 1 repeat among ~200 chains).
- Q4: `pes_lib.fan` on every sampled 88 state of D: 0 down moves, 0 TOPK binds.
- Q5: for 10 random D 88 states, every one-seed window with k <= 8 is UNSAT within 60 s and every
  byte block with free <= 1 and k <= 10 within 120 s (a SAT is an 87; a different timeout pattern
  shows the frontier is circuit-dependent).
Interim at 5.2 h (20:20 UTC; 20 worker-hours per arm; not a decision): arrivals per worker-hour D0
1.50, D4 1.70, DN 1.75 (30/34/35 chains; DN/D0 = 1.17, P1 undecided); distinct v3 per worker-hour
D0 24.1, D4 25.7, DN 25.6 (P2 ratio 1.06, below 1.2; per worker DN > D0 on 3 of 4, D0's free-00
alone has 209 vs 114); share of 88 states at depth >= 10: D0 3 %, D4 20 %, DN 31 % (P3 on track);
5 of 1,579 signatures shared across arms (0.3 %, P4 on track); 0 states below 88 (P5). Null model
(Q1/Q2): 1,235,293 cross-chain pairs, 6 shared nodes, N_eff ~ 2.1e5; at 1.3e5 the expectation is
9.5 (Poisson P(<= 6) ~ 0.17): inside, no evidence of locality or hubs so far.
FINAL (15:06-21:41 UTC, 25.5 worker-hours per arm; data on disk complete to 21:41):
- Arrivals at 88 per worker-hour: D0 1.49 (38 chains), D4 1.69 (43), DN 1.80 (46). DN/D0 = 1.21:
  P1 is met at the threshold, but the Poisson rate-ratio interval on 38 vs 46 arrivals is about
  0.8-1.9, so the effect is not established; D4 sits between. Time from root to 88: medians 360 /
  435 / 462 s (no speed-up). Restart reasons: all stall timers.
- Distinct 88 plateaus (v3) per worker-hour: D0 24.5, D4 26.8, DN 26.0 (652 / 712 / 693 signatures
  from 856 / 855 / 734 states). DN/D0 = 1.06: P2 (>= 1.2) is REFUTED; per paired worker DN > D0 on
  3 of 4 (free-00 alone: D0 260 vs DN 168), D4 > D0 on 3 of 4.
- Depth: share of 88 states at depth >= 10: D0 2.5 %, D4 19.9 %, DN 27.5 %: P3 CONFIRMED (>= 2x).
- Cross-arm sharing: 7 of 2,050 signatures (0.34 %): P4 confirmed. No state below 88 in 2,445
  sampled 88 states and 0 records below g88: P5 confirmed.
- Null model (Q1, Q2): 2,095,065 cross-chain incidence pairs, 10 shared nodes, N_eff ~ 2.1e5;
  expectation at 1.3e5 is 16.1 (Poisson 95 % ~ [9, 25]): inside, at the low edge. Q1 does not
  reject the one-pool reading; a mild deficit of meetings is compatible with the data but not
  established. Q2 (P/M in [5e4, 3e5]) holds. Q3 needs the exact catalogue (running). Q4 CONFIRMED:
  `pes_lib.fan` on all 2,445 sampled D 88 states: 0 states with a down move, 0 TOPK binds, neutral
  moves 8/16/40 (min/median/max) [measured, `q4.sh`]. Q5 is stage 1 of the SAT campaign batch2
  (running since 21:46): stage 1 complete at 22:15 UTC, all 479 windows (one-seed k <= 8 at 60 s, byte
  blocks free <= 1, k <= 10 at 120 s) on the 10 hunt D states UNSAT, 0 timeouts: Q5 CONFIRMED (the
  frontier is not circuit-dependent at these sizes) [measured, `sat/batch_summary.py batch2`].
- Reading: removing the depth window changes WHERE chains land (much deeper 88 plateaus) more
  than how often they arrive or how many distinct plateaus they visit per worker-hour. The
  analogue-benchmark gain (F8) did not reproduce as an arrival-rate gain on MixColumns in 25
  worker-hours per arm. The capped test (hunt E) never ran.
Analysis scripts: `hunt/descents.py hunt/runsD`, `hunt/sigD.py runsD samplesD/samples.jsonl 13`,
`review2/dnull.py`.

## F15. Why 89@4 is unusual (q89 agent, `q89/REPORT.md`; own census of every raw record) [measured / derived / argued, separated]

(1) Properties shared by the recorded 89@4 circuits [measured]. 526 record files -> 90 distinct value
sets -> 81 modulo byte rotation. All have the per-depth profile 26/22/29/12. The 81 are exactly one
cap-4 remove1 plateau L0 (closure complete at 81; 8 neutral moves per state; 0 down moves); the other 9
are one-byte rotations of L0 members produced by the foundation searches' validation runs (which pin
the first layer rotated by one byte). The archive's "81 circuits, 53-value core" claim is confirmed: 53
constant helpers; 12 variable level-2 values forming 4 slots x 3 choices with all 81 combinations
present; each slot is the re-pairing of a 3-leaf tree (two level-1 pairs + one input) under a fixed
weight-5 helper. For contrast, 90@4: 13,141 records, 5,798 distinct states, 183 distinct first layers
with 21-26 gates; none has the 89's first layer (max overlap 24). The archive statement "no 90@4 had
more than 25 first-layer gates" is FALSE on the full data (72 distinct 90@4 states have 26).
(2) Properties required of every 89@4 circuit [proved/derived]. Depth 4 forces outputs to levels 3-4
and G = 32 + h1 + h2 + h3 (no helper at level 4); support arithmetic gives only h1 >~ 7-10, so 26
first-layer gates is NOT forced (depth-4 circuits at 90/91 exist with 19-26 first-layer gates); the
question is open. The cap is what makes the pocket "sealed": cap-4 fans are subsets of uncapped fans
[proved]; measured, each L0 state has 8 neutral moves at cap 4 versus 15 at cap 5 or none, and the
closure is 81 (complete) versus >= 3,096 / >= 6,117 after 1,500 expansions. The engine's depth window
is inactive at cap 4 (slack 0), so "one step up and fall back" is a plateau/move-set property under the
cap, not a window artefact. No proved depth-4 lower bound above the unrestricted 75 exists (the archive's
depth-4 pushes say so themselves); the July RECORD_89 is a depth-10 circuit.
(3) Behaviour caused by the procedure [measured]. Premise correction: v8 did not reach 89@4 from
NIST's 90@4 in minutes; the repo's found.json and HISTORY say it came from the July 91@4 at 914 s, and
the adopt side that moved to NIST's 90@4 never left 90. Every 89@4 record traces to TWO entry events:
control mc-cap4-01 (July lineage, 914 s) and v9c mc-cap4-04 (2026-11-04, 6,881 s, after a stall
restart onto a shelf 90@4 whose first layer already equalled the 89's), then spread to 10 workers in
13 s by adopt. Catchment = carrying the 26-pair first layer: walks move it one pair at a time and the
path from NIST's set costs +2..+4 gates. Uncapped, L0 is not a trap: all 4 mc87 `from89` workers seeded
with the 89 reached 88 (depth 6-9) within 131-640 s, their 88s keeping only 17-19 of the 26 pairs. The
2026-11-06 study's statements are restated with their move classes; its over-reach was the "funnel"
wording, the envelope-vs-real-Expand gap, BFS stopping at the first <= 89 state, and the budget guess
at k = 5, 6.
- What is unusual: one family, found twice in >10,000 core-hours, whose first layer no 90@4 shares, on a
  small (81) plateau because the cap removes half the neutral moves. Candidate explanations: (a) the
  family is the unique 89@4 up to rotation [open; nothing proves it]; (b) the first layer is a narrow
  gate that the walk crosses only one pair at a time, so entry is rare but not exceptional (two entries
  by two different routes) [supported by the catchment measurement]; (c) depth-4 feasibility is tight at
  89 so the plateau structure is smaller than at 88 uncapped [measured for L0].
- Predictions: P1 (a post-hoc check on existing mc87 data, not a test on fresh evidence): uncapped exits
  from L0 reach 88 keeping <= 19 of the 26 pairs. P2 (testable in ~10 min on the foundations' (26,22,30,12) traps): every 90@4 with the
  89's exact first layer lies in its +1 band D1. P3 (~1 core-hour): pinning the 89's first layer at cap
  5 completes to 89, not 88. P4 (2 h run): arrivals from NIST pass through a 90@4 carrying a rotation of
  the 89's first layer, equally across the four rotations.
- Transfer to the unrestricted 87 question: plateau = product of re-pairings; first-layer motion one
  pair at a time; records clustering into few entry events. Depth-4 only: the small plateau, the
  immobile first layer, the single family.
- P2 TESTED and FALSIFIED (18:40 UTC, `q89/s16_p2.py`): 12 distinct 90@4 states carry the 89's exact
  26-pair first layer (none is a run record; all are pinned-completion outputs of the foundation
  studies); 0 of 12 lie in L0's +1 band (0 in B1 of 16,173 states; no direct remove1 step down;
  bounded descents of 5,000 states reach no <= 89 state; one is provably outside, trapped in a
  9-state 90-plateau). Eleven share one alternative level-2/3 realisation over x0, x1, x7-x9,
  x15-x17, x23-x25, x31 that costs one gate more. So the first layer is necessary (all data) but
  not sufficient for the 89 family: the same first layer supports at least two 90-level families
  not connected to L0 under the capped moves. This matches the 6:4 split of pinned completions and
  the 840 s the v9c arrival still needed after landing on a first-layer-equal 90 [measured].
- Independent check (q89check, 23:30 UTC, `q89check/REPORT.md`): claims (1), (2), (3) CONFIRMED with
  own code (526 files -> 90 -> 81 mod rotation; closure 81 complete, 8 neutral moves, 0 down, 53-value
  core, 4 x 3 slots, reproduced both with pes_lib at cap 4 and with an independent value-set model;
  90@4: 5,798 states, first layers {21: 4, 22: 161, 23: 4,075, 24: 1,277, 25: 209, 26: 72}, none equal
  to the 89's under any rotation). P2 corrected in scope: scanning every g = 90, d = 4 best event in
  the pinned-completion logs gives 26 distinct 90@4 states with the 89's first layer (not 12); of
  the 26, 1 is in B1, 3 have a direct remove1 step into L0 and 11 descend to L0 by bounded remove1
  BFS (all among the 18 transient states of runs that ended at 89), 4 sit in 9-state 90-pockets, 11
  were cut at 3,000. The 8 run-final traps (the population P2 was about) all fail to connect, so
  "necessary but not sufficient" stands; the wording "no 90@4 over this first layer connects to
  L0" would be false (11 of 26 on disk are in L0's remove1 basin). The >= 3,096 / >= 6,117 closures
  are budget-dependent lower bounds, and "plateau = 81" is about single-value repairs.

## F16. The unrestricted lower bound 75 and what 76 would take (lb76 agent, xhigh effort, `lb76/REPORT.md`) [replayed / derived / read]

- The shipped 75 proof replays: ALL CHECKS PASSED, 484 + 4,057 exact certificates, complete coverage,
  13 circuit controls, 137 s under nice on the loaded machine [replayed]. Scope: unrestricted
  straight-line circuits of 2-input XOR gates computing one MixColumns column (32x32); depth, fan-out,
  cancellation, intermediate values unrestricted; every gate counts. Architecture in plain terms (the
  report's section 1): lossless normalization of a minimum circuit; gates split by parity of mask
  weight (G = 32 + x + y + h, x >= 24 from a finite fact); canonical transposition and a potential
  e(C) that must drift by >= 1 per two-step cycle unless the "tail" profile is excluded; for each
  scalar profile and orientation a local linear system (L1)-(L23) on helper-type counts whose
  infeasibility is certified by integer Farkas vectors; coverage by k + l > budget with budget =
  a + b + 2G - 192.
- Where 74 enters [derived]: nowhere in the rows or lemmas; only through the scalar domain, two
  fan-out caps and the drift budget, which grows by exactly 2 per extra gate. At G = 74 the exclusion
  is razor-thin: 1,307 of 2,204 oriented claims are closed only by k + l > budget with margin exactly 1.
- At G = 75 with the package's own rows [replayed, 49 s]: 3,708 scalar states, 7,416 oriented claims,
  1,508 SURVIVE (1,134 local systems stay LP-feasible); at G = 76: 4,549 of 13,634. So regenerating
  certificates at 75 is minutes of compute and provably insufficient: strength, not cost, is the
  obstacle. The archive's five later campaigns (30 Sep to 24 Oct) added ~15 new row families and got
  the survivors from 1,508 to 509 (push6, whose 698 + 301 exact exclusions replayed here), all ending
  with exact, often integral helper-type witnesses: the count relaxation is intrinsically too coarse;
  the missing content is realizability of masks, labels and chronology.
- The claimed 76 of 29-30 Sep exists only as a one-page status note (`bound_76_status.md`): same
  skeleton (3,708/7,416 domain), ~20 new inequality families, a 772-case realizability split, 50,048
  + 2,445 certificates, a 948 MB package "kept by the author", no human review. It cannot be
  reconstructed or judged from the note. Decisive action: locate that package and audit it; its
  verifier (claimed ~6 min on 8 cores) and the checks in the report's section 9 say what "verified"
  must mean.
- Odd-helper parity theorems [read, not checked; proofs for h = 0, 1 and the needed zip are absent from
  the archive; checkers not run]: in the same unrestricted model, h = 0 odd non-output helpers => G >=
  92, h = 1 => 91, h = 2 => 90 (23 Sep theorem), hence any circuit with <= 89 gates has >= 3 odd
  helpers; the upper half h <= G - 56 follows from x >= 24 [derived]. (The inventory's "exactly two
  => >= 88" is the older figure that the 23 Sep theorem strengthened to 90.) Not a lever for 76: all survivors
  at 75 have 8-19 odd helpers per phase and the h-general form of the accounting is already Lemma 4.4.
  Our own 88 circuits have 16-24 odd non-output helpers (mode 20; 2,821 sampled states, `oddhelpers.py`)
  [measured], far inside the window, so these theorems do not constrain the circuits the search sees.
- The 88-level knowledge (plateaus as products of 3-input-tree pairings; G = 108 + delta - S with the
  sharing cap open) offers no proof lever for 76 [guess]: a 76 by that route needs a universal
  S - delta <= 32, unrelated to the parity/potential machinery.
- Go/no-go: regenerate at 75 with shipped rows: no-go (baseline only); locate and audit the Sep package:
  go, conditional on the package existing (the only route to 76 within weeks); new universal rows to 0
  survivors: no-go within a sprint; odd-helper accounting and 88-level identity: no-go for 76.

## F17. Where real 88 circuits live in the 75 proof's space (bridge agent, high effort, `bridge/REPORT.md`) [measured with the package's own code]

- Corpus: 200 sampled 88s (distinct mod rotation, from hunt A/B/C/D), 100 kste 88s, the repo 88@5,
  89@4 and 97@3 (true gate lists). A value set determines the gate list almost uniquely for 88s (35
  of 40 unique under full acyclic enumeration, alternatives move x, y, q, z, F by <= 1), but the
  controls are more ambiguous than the bridge's min-depth family counted (89@4: 15 reconstructions
  spanning x 24-26, y 12-14; 97@3: 16) [bridgecheck]. The side claim "every weight-2 value is a
  represented label" is false (fails in 21 of the 303 circuits' own data); harmless downstream. All 303 circuits x 6 orbit phases pass every package
  assertion; no row (L1)-(L23) is violated [measured].
- Corrected by the independent check (`bridgecheck/REPORT.md`): the orbit's scalar profile (x, y, h,
  s, F, E_B, e) is 2-periodic from the first transpose in 303/303 circuits, but the circuits
  themselves are not (C_1 = C_3 in 17 of 40) and (q, z, types) only from step 2; what the identity
  needs, e(C_{j+2}) = e(C_j), holds in every case. The identity s_e + s_o = a + b + 2G - 192 - E_B -
  L_H (E_B = sum over the 64 boundary signals of max(0, d_v - 2), L_H = 0 at canonical phases) is
  the package's exact form of Lemma 8.2 and holds for EVERY circuit of every gate count (the 97@3
  has margin -36): the drift step has no slack at any G. What is specific to real 88s is only that
  E_B is small (0-7; 12 of 200 hunt circuits at 0), i.e. Lemma 8.2 loses 0-7 units on them
  [derived + verified 40/40 and 303/303]. So "the drift mechanism saturates at real 88s" was
  over-read: the missing content is entirely in the local rows (provable k + l of ~1-2 against a
  true budget - E_B of 28-33 on real circuits); E_B is not a variable of the local systems and
  cannot become a row, and E_B <= 7 transfers nothing to a hypothetical 87.
- Real 88 tail profiles: a 24-26, b 24-27, Y 14-19, V 10-17, h_e 13-17, h_o 14-20, q 10-16, z 0-7,
  s 12-18 per phase; even phase M^T in 72 % (94 % of kste). The 1,508 survivors at G = 75 have Y <=
  11, V <= 8, q <= 10: disjoint from real circuits in Y and V. Real helpers are 85-90 % of types
  (2,1,0), (2,0,1), (1,2,0), (1,1,1) with odd-graph degree exactly 3; the r = 0 / r = 3 / high-u
  columns the survivor LPs rely on are nearly empty in real circuits.
- Row slacks: nothing is tight. Minimum slack over 1,515 canonical phases is 10 (rows L4, L6, L12,
  Lemma 10.3); q-scaling rows have slack 40-140. Only Lemma 7.4 (helper degree >= 3) is tight. So no
  existing row can be sharpened by real-circuit evidence and none is contradicted.
- Hypotheses: (a) "any <= 89 circuit has >= 3 odd non-output helpers": real 88s have 16-23 (13-20 in
  canonical transposes), confirmed with 10+ to spare. (b) the plateau structure (F2) does not show up
  in the proof's coordinates: all weight-2 values are represented B-B labels (13-20 per circuit,
  55-80 % of represented labels) but they are rigid (median 0, max 2 removed by any neutral move);
  the 8-30 neutral moves swap one weight-3..7 helper for another of similar weight.
- Candidate inequalities [conjecture, consistent with 316 circuits incl. the 13 controls; none
  proved]: q >= 7 per canonical phase would cut 1,017 of the 1,134 LP-feasible keys at G = 75 (SCORED by
  F18: not provable in the framework, since q is forced only through q + z = sum d_v + y - 32; a
  [guess], probably false on hypothetical tails); E_B <= 7 and x <= 26 hold for minimum circuits seen but are
  broken by the 97@3. Every other simple combination tried is broken by a control circuit.
- What this changes: proof work should not expect the 75 machinery's rows to tighten toward 88; the
  gap between the survivors' profiles (small Y, V, q) and real circuits (large Y, V, q) says the
  missing content is exactly realizability of low-Y, low-V, low-q profiles, consistent with F16's
  reading of the October campaigns. For the search, the proof's coordinates give no new move or
  predictor: the mobile part of a plateau is invisible to them.

## F18. New universal inequalities for the 75 proof's local systems: survivors at G = 75 cut from 1,508 to 1,313 (qbound agent, xhigh; `qbound/REPORT.md`; CONFIRMED by `qcheck/REPORT.md`) [proved as checked; no bound improvement claimed]

- Survivor table for hypothetical rows q >= c (package LP model at G = 75, 1,508 baseline claims): c =
  1..8 kills 0 / 11 / 76 / 332 / 676 / 1,026 / 1,305 / 1,466; q + z >= 9 per phase kills all 1,508
  [measured]. No q >= c is provable in the framework: q is forced only through q + z = sum_H d_v + y -
  32, and real circuits have q >= 10 because they have y >= 10 and h >= 13, not by a label obstruction
  [proved identity + measured]. So the bridge's q >= 7 conjecture is a [guess], probably false on
  hypothetical tails.
- Lemma N1 [claimed proved from Lemmas 4.1, 4.5 / F4]: 3 n_3 <= x + y - q (the represented edges of
  "full" helpers, type r = 3, carry pairwise distinct labels). The LP's small-q survivors were built
  from 7-13 full helpers per phase (real circuits have 0-3); N1 alone cuts feasible keys 1,134 -> 755
  and claims 1,508 -> 1,355.
- Family G* [claimed proved by extending Lemma 10.2's elimination with the even+even gate equations
  whose signals are represented (kind 0) or have one bright missing signal (kind 1)]: y -> y_2 in rows
  (L13)-(L20), (L22); plus (L12*) sum (r-1)_+ + y_0 <= rho_6, (L7*) W + y_1 <= 7q, (I) y_1 + y_2 + U +
  2F_H <= 4q + 2F, and (Q0) q = 0 => z >= 12 + h_0 on M. G* alone: 1,508 -> 1,477; with N1: 1,313
  claims (724 M, 589 M^T), 681 keys; with integrality of the local systems as a branch-and-bound
  oracle (not certificates): 1,167 claims, 497 keys.
- Lemma S (rich labels) [claimed proved] + finite fact S1 [finite-checked]: at a represented label with
  boundary pair P, sum over helpers meeting it of (r_i - 1)_+ <= sigma(P), the rank of weight-6
  zero-sum boundary sets through P; sigma = 0 for 1,704 of 2,016 pairs (M), 1,590 (M^T); so every
  represented label at an r >= 2 helper is one of 312 (M) / 426 (M^T) rich pairs. Adds nothing to the
  LP at 75; a strong structural restriction for any realizability search.
- Negative finite fact: the largest set of full values with independent relations has exactly rho_6/2
  elements (10 on M, 14 on M^T), so L12 is tight as a rank statement [finite-checked].
- Controls: zero violations of any new row on the 13 package controls (52 phases) and 303 real circuits
  (1,212 phases); (G*) with J = R_6 and (L12*) are TIGHT (slack 0) on some real phases, unlike every
  package row (slack >= 10): they cannot be sharpened further without breaking a real circuit
  [measured].
- What survives and why: configurations with 7-10 full helpers using nearly every even signal as a
  label (q = 1-3), and at q = 5-6 five or six (3,1,0) helpers plus an unanchored hub carrying 4-6
  missing labels; both are realizability questions the count relaxation cannot see; five finite
  searches that would decide them are listed (report section 8).
- Status: CONFIRMED by an independent checker (qcheck agent, xhigh, `qcheck/REPORT.md`): every
  lemma (N1, G*, L7*, L12*, I, Q0, the y -> y_2 and W -> W + y_1 substitutions, Lemma S) verified
  step by step against PROOF.md with two wording remarks and no gap; finite facts S1 and N3max
  recomputed independently; 559 circuits / 2,236 phases with an independent implementation: 0
  violations, (G*) tight on 112 phases; LP recount reproduced 1,313 / 681 with the rows implemented
  as stated; the checker's own independent LP implementation (`qcheck/lp_indep.py`, run 21:48 UTC)
  gives identical key sets (1,134 / 755 / 1,051 / 681, symmetric difference 0) and 1,313 survivors.
  Not a bound improvement: 1,313 claims remain open at 75 by LP status. CERTIFIED (qcert agent,
  xhigh, 23:10 UTC, `qcert/`): `PROOF_ADDENDUM.md` writes the lemmas in the package's notation
  (family listed, independence before the row operations, weight-0 case, rank-nullity, row-by-row
  facts for y -> y_2, wording fixes); `CERTIFICATES_EXT75.json` holds 1,772 exact integer Farkas
  certificates (666 using the new rows, 1,106 package-row ones the package lacks at G = 75) with
  complete coverage of the 195 newly excluded claims (122 M, 73 M^T; 453 killed keys), largest
  weighted rhs -1; the independent hand-written checker `check_ext75.py` (stdlib, rows re-derived)
  passes in 1 s and its matrices equal the generator's on all 2,562 touched keys; mutation tests
  reject every negated multiplier (7,225), dropped certificate (195) and loosened claim (390);
  `stress_ext.py` evaluates every new row on 1,264 phases of 316 circuits: 0 violations. Remaining
  open at 75 by LP status: 1,313 claims / 681 keys (shortfall 0: 565, 1: 515, 2: 183, 3: 50). The
  uncertified integer-oracle figure (1,167) is not a result. Trust ledger: package Lemmas 1.1-10.4
  and F2-F14 [read, not checked]; everything new [proved] / [finite-checked] / [certified].

## F19. Literature status of the MixColumns bounds (lit2 agent, web; `lit2/REPORT.md`) [cited; PDFs behind Cloudflare not read]

- J. Jean, "88-XOR Implementation of the AES MixColumns Matrix", IACR ePrint 2026/1481 (received
  2026-07-20): abstract read; the PDF could not be fetched (bot check). Prior counts cited there:
  94 / 92 / 91 / 89 (the 89 is Sun-Yang-Li, ePrint 2025/1493). A later arXiv note (Pandey, 2609.20873)
  describes it as a two-page note whose circuit was found with AI assistance, with no lower bound, no
  optimality claim and no verification procedure; 87 is not discussed; depth is not stated (7 by our
  own earlier inference). Priority for the count 88 is Jean's.
- Lower bounds: the best PUBLISHED unrestricted XOR-count lower bound for the fixed MixColumns
  matrix is the counting bound 32; Pandey (Sept 2026) states that no lower bound of any kind is
  published for it. Bounds in the 60s exist only in other models (sequential-XOR >= 67 for any 4x4
  MDS over GL(8, F2), Venkateswarlu-Kesarwani-Sarkar ToSC 2022; 8n+2, Wang et al. 2023; word-level
  fan-in-2 superconcentrator bounds, Lee-Park-Son ASIACRYPT 2026) and do not transfer to general
  XOR circuits. So the owner's unrestricted 75 and depth-3 93 are new relative to the literature by
  a wide margin [found online: explicit statement of absence]. The kste "UNSAT at <= 87" is scoped
  to a 1,607-signal pool and its depth-floor premise (max row weight 5) is wrong: 12 rows have
  weight 7 [computed].
- Upper bounds by depth (published): depth 3: 103 (2021), 102 (2023), 99 (Shi-Feng-Xu ToSC 2023);
  depth 4: 97 (Osvik-Canright 2024); depth 5: 94 (Osvik-Canright); depth 6: 92 (Maximov 2019; Xiang
  et al. 2020); depth 7: 91 (Lin et al. 2021), 88 (Jean, inferred); depth unstated: 89 (2025). The
  NIST circuit list carries 97@3, 90@4, 88@5 uncredited (files dated 2026-08). Verdicts: 88 at any
  depth is not new (Jean); 88@5 is in no paper but public uncredited at NIST and in kste; 89@4 not
  found in print; 97@3 beats every paper (99) and ties the uncredited NIST entry (possibly ours).
  No 2025-2026 paper below 88 was found.
- Structure: nothing published on plateaus, counts of optimal circuits or "no 87" arguments; the
  nearest techniques are Pandey's DRAT-certified exact XOR pipelines (n = 6..9) and Lee-Park-Son's
  word-level superconcentrator bounds (a bit-level analogue would be new work).
- To confirm by hand: download Jean's and Osvik-Canright's PDFs (depth and method of the 88; the
  94@5 / 97@4 figures).

## F20. Odd-helper theorems verified and the lost cases re-proved: any MixColumns circuit with <= 89 gates has at least 3 odd non-output helpers (oddh agent, high; `oddh/REPORT.md`) [replayed + finite-checked + proved here]

Model: the 75 proof's unrestricted model (2-input XOR circuits for one column; h = odd-weight
computed values that are neither inputs nor outputs).
- h = 2 => G >= 90 (the owner's 23 Sep theorem): restated in plain terms (G = 34 + x + y; the mixed
  gate rows give y >= 34 + p - r with p the hidden even values and r the rank of four-term relations
  among the 66 odd values, so G >= 92 + p - r; r <= 6 by enumerating the 3,592,052 candidate helper
  pairs; the cases p = 0..3 closed by quotient-rank ledgers and 174,180 triangle checks). The three
  archive checkers compile and PASS (160 s, 14 s, 84 s) with outputs identical to the stored results;
  every finite fact was recomputed independently from the repo's matrix in plain Python (Sidon 2,016;
  triple multiplicities 40,704 / 360 / 80; rank histogram over the full 3,592,052-pair domain
  113,892 / 3,444,740 / 30,572 / 2,848 with max r = 6; quad capacities 2,046 / 291 / 36; single-helper
  d-table), all matching. General-h form of the ledger: G >= 88 + 2h + p - r and H >= 12 + h + p - d
  [proved]. Premises still [read, not checked]: F1 (x >= 24, in the 75 package) and the 88 controls.
- h = 0 => G >= 92 and h = 1 => G >= 91: the archive had lost these proofs; complete derivations are
  given (h = 0: r = 0 by Sidon, p <= 2 impossible, p = 3 excluded by 1,360 triangles of joint rank
  <= 7 vs 15 required, so p >= 4; h = 1: r <= 3, p = 0..2 excluded by the d-table, p = 3 forces a full
  helper and G = 90, excluded over the 20 rotation orbits of full values) [proved + finite-checked,
  single implementation run once].
- Consequence [proved given F1]: any circuit with <= 89 gates has >= 3 odd helpers; an 87 has 3 <= h
  <= 31 and needs four-term rank r >= 7 + p among its odd values. Our 88s have 16-24 (F16), so this
  constrains hypothetical small-h circuits, not the ones the search sees.
- h = 3 => G >= 89 is NOT proved: the p = 0 domain is infinite and the finite r >= 7 domain at p >= 1
  has > 1.1e8 survivors; 5.3e8 structured triples enumerated in C++ (312 s) give max r = 9 (universal
  bound r <= 12). A real proof is a day or two of code plus CPU-hours to days [estimated].

## F21. Realizability rows: survivors at G = 75 cut further, 1,313 -> 996 claims (qreal agent, xhigh; `qreal/REPORT.md`; CONFIRMED by `qrealcheck/REPORT.md`; CERTIFIED by `qcert2/`) [proved as checked and certified; no bound improvement]

- Hub helpers (task b) [finite-checked + claimed proved]: H1: for every odd non-boundary value h, at
  most 4 jointly independent full values f have h + f equal to a boundary-pair value (M and M^T; <= 2
  unless h is a two-representation repeated value; exact exhaustive maximum, second-method rank check,
  transposes agree). Lemma H1: for every helper with r <= 2, u_i <= 4 + (q - A) where A = sum over
  full helpers of u (cites Lemmas 4.4-4.6, F2-F4); implemented as an exact case split on A. Effect:
  681 -> 585 keys, 1,313 -> 1,256 claims; kills the q = 6, 7 unanchored-hub vertices.
- Dark-label split (task c) [claimed proved rows]: rows (L13)-(L18) re-derived keeping the q_D terms,
  bright/dark occurrence budgets with new columns, y_2 - y2d <= C(q, 2), and (I) with multi-missing
  gates counted twice; exact split q_D = 0..q. Effect: 1,256 -> 996 claims (504 M, 492 M^T), 381 keys
  (q: 1:2, 2:2, 3:14, 4:54, 5:163, 6:93, 7:11, 8:41, 10:1); the M^T q = 1 cluster falls from 57 keys to
  2; the M n_3 = 9 key and the hub key die in every case.
- Full-helper geometry (task a): mostly negative. Lemma O1 [claimed proved]: every full helper defines
  >= 2 distinct outputs through its non-defining represented edges (all 324 real full helpers define
  exactly 2) but flow-feasible independent 10-/14-sets exist, so it never bounds n_3; the label budget
  cannot be sharpened by counting; a boundary-degree row is vacuous at 75; the full-set enumeration is
  infeasible (> 6 M independent 10-sets through one value). FM: rank(C_l) at labels l = f + c is 3
  for 80 % of them [finite-checked]; rows FM7/FM9 valid, add nothing.
- Two-phase identity (task e) [derived]: on the eventual tail s_e + s_o + E_B,e + E_B,o = budget
  exactly; 511 surviving claims have shortfall 0, forcing boundary degree <= 2 everywhere in both
  phases; no row lower-bounds E_B yet; the joint LP was not built.
- Controls: 0 violations of any new fact or row on 13 controls + 303 real circuits (1,264 phases;
  `qr_circ.py`). Shortfall of the 996: 0: 511, 1: 337, 2: 109, 3: 39.
- What remains: 362 of 381 keys have q = 4..8: five or six (3,1,0) helpers with anchored hubs carrying
  3-4 full-met labels (hub value among only 100 M / 196 M^T values with cap >= 3), plus M^T q = 1,
  z = 4-5 phases with 7-8 full helpers. The report specifies the finite realizability search that would
  decide the hub family (hub value x witness set x label choice x hub triple, filtered by
  independence, FM ranks, O1, degree <= 2); the qhub agent is running it. The integer oracle was not
  run on the final system. The bound is 75; 996 claims survive by LP status.
- Independent check (qrealcheck, xhigh, 23:50 UTC): H1 recomputed with own code (identical per-value
  caps for all 128,068 / 177,412 values; cap 4 only at two-representation values); Lemma H1, the
  HUB split, the dark rows (L13d)-(L18d) with their coefficients, the occurrence budgets, the
  q_D split and Lemma O1 CONFIRMED step by step; LP recount 1,256 / 585 and 996 / 381 reproduced
  both with the unchanged rows and with an independent implementation (identical survivor sets and
  (k, l) values); 96 circuits / 384 phases with own code: 0 violations, (G*) with the F9 space tight
  on 22 phases. Bookkeeping correction: qreal's "keys" count only the 1,134 baseline keys; over
  every key the final scan evaluates, 1,661 are LP-feasible and 1,377 load-bearing (654 M, 723 M^T;
  by q: 2: 80, 3: 184, 4: 321, 5: 361, 6: 244, 7: 122, 8: 60, 9: 5), so "remaining keys with q <= 3"
  is 264 load-bearing keys, not 18; the 996 survivor count is unaffected. HUB is unexercised by any
  known circuit (A = 0 everywhere).
- CERTIFIED (qcert2 agent, xhigh, 00:10 UTC, `qcert2/`): `PROOF_ADDENDUM_2.md` writes H1, Lemma H1
  with the HUB split (exhaustive since A is an integer in 0..q), the dark rows (L13d)-(L18d) re-derived
  from G*, the occurrence budgets, (I'), Lemma O1 and a lemma that certificates persist under case
  relaxation, in package style with every lemma cited; `CERTIFICATES_CASES75.json` holds 4,523 exact
  integer Farkas certificates (2,460 keys, 2,497 per case; each recording its hub case and q_D) with
  complete case coverage of all 300 killed keys (681 -> 381; 4,344 leaf cases) and all 317 newly
  excluded claims (1,313 -> 996; 11,788 leaves), largest weighted rhs -1, 192,917 coefficients; the
  independent stdlib checker `check_cases75.py` (own rows, own case tree) passes in 3 s;
  `crosscheck2.py` shows both system definitions identical on 23,593 (key, case) nodes and all key and
  claim sets identical to qbound / qreal / qrealcheck / qcert; mutation tests: 26,724 negated
  multipliers, 300 dropped cases and 317 dropped certificates all rejected. `stress_ext2.py`: 1,264
  phases, 0 violations; `synthetic_hub.py` builds local configurations with A = 3 that exercise the
  HUB row (slack 1). Observation recorded, not used: at every cap-4 hub value the 4-witness sets have
  dependent gate equations once the missing-edge equations are included, consistent with qhub's
  capacity 3 (F27); the certificates rest on the proved constant 4.

## F22. Depth-4 lower bound: nothing above 75 in general; proved layer facts and scoped exact results around the 89@4 family (d4bound agent, xhigh; `d4bound/REPORT.md`) [proved / finite-checked / SAT-scoped, as marked]

Scope: circuits of depth <= 4 (every gate a 2-input XOR, outputs any gate), one MixColumns column.
- Best justified bound at depth <= 4: 75, the unrestricted package; the archive's depth-4 pushes also
  prove nothing above 75, and their named obstacle (the 75 proof's transposition/stabilisation does
  not preserve depth, Lemma 3.1 accumulation trees) is confirmed [proved / archive].
- Proved for every depth-4 circuit: a lossless normal form with layer grammar (level 1 = input
  pairs, level 2 = triples/quartets over pairs, level 3 = weights 3-8, level-4 gates are outputs,
  every output at level 3 or 4; G = 32 + p + h2 + h3); p + b >= 24 (pairs plus level-3 odd+odd-born
  even helpers; from lb75 Lemmas 2.1/2.2 + F1, which need neither minimality nor depth), hence
  G >= 56 + h2 + (h3 - b); a level-4 output can avoid a level-3 helper operand only as "cyclically
  adjacent same-bit weight-5 output at level 3 plus a quartet" (exactly 20 output pairs, finite-
  checked), so every weight-7 output at level 4 uses a level-3 helper; exact pair-free parent covers
  (CP-SAT optimal): all 32 outputs at level 3 need >= 25 level-2 masks, the 20 weight-5 >= 10, the 12
  weight-7 >= 15, so any depth-4 circuit with all weight-7 outputs at level 3 has h2 >= 15. The
  unconditional yield is only G >= 57: the grammar prices neither level-3 helper fan-out nor the
  level-2 bank behind level-4 outputs (the obstacle, stated).
- SAT-scoped theorems (model completeness for each scope proved; Z4-transportable): A: weight-2 set
  = the 89's 26 pairs and level-2 gates = its 22 => min h2 + h3 = 31 => G >= 89; B: same pairs,
  level-2 any subset of the 81-family's 30-value pool => G >= 89; D: pairs any subset of the 26,
  level-2 from the pool => min |L1| + |L2| + |H3| = 57 => G >= 89. C: pairs fixed, level-2 completely
  free (1,060 candidates, 189,027 level-3 masks, 886k-variable LP): UNRESOLVED (CP-SAT bound 0 in
  900 s; LP timed out). So 88 is not excluded over the 89's first layer alone; it is excluded over the
  first layer plus the family's level-2 vocabulary. This is the exact-method counterpart of F15 (the
  first layer is necessary for the family, not sufficient).
- Route C (depth-3-style recipe enumeration) is infeasible unconditioned: last-gate split space
  1,123,414 (weight 5) / 592,114 (weight 7) per output vs 285 / 35 at depth 3 [finite-checked].
- Known 89 census [finite-checked]: p = 26, h2 = 22 (13 triples, 9 quartets), h3 = 9 (6 odd weight 5,
  3 even weight 6), b = 0; all weight-5 outputs at level 3, all weight-7 at level 4, each level-3
  helper feeds exactly 2 level-4 outputs, no output reuse.
- Next: close scope C with the valid cuts and branching on the level of the 6 weight-7 outputs that
  can be at level 3 over the 89's pairs (the other 6 never can); then per recorded first layer /
  single-pair exchanges; a full depth-4 bound needs conditioning on the pair-graph partition as the
  depth-3 proof does. Conjecture [weak support]: D4 = 89.
- Scope C follow-up (d4c agent, xhigh, 01:10 UTC, `d4c/REPORT.md`): still OPEN. An exact CP-SAT model
  of scope C in strict normal form (1,060 level-2 candidates, 188,557 level-3 masks; the earlier
  scope-C model was a relaxation since weight-2 masks are pairs in normal form; witness -> circuit ->
  check.py verifier tested on the 89) with proved cuts. New exact facts over the 89's pairs P89
  [finite-checked / CP-SAT optimal]: PC(W5) = 16 (the 89's 22 level-2 gates are a minimum parent
  cover of the 20 weight-5 outputs plus 6 extras used only by helpers; 31 = 16 + 6 + 9); the six
  weight-7 outputs that can never sit at level 3 need >= 6 helpers even with every level-2 mask free;
  helper-free level-4 recipes exist only for two output pairs; a weight-7 output is served by a single
  helper only through 1,707 specific masks. So an 88 over P89, if any, saves its gate in the
  level-2/helper coupling. Closed [SAT-scoped]: over the 89's level pattern (20 weight-5 outputs at
  level 3, 12 weight-7 at level 4) no circuit WITHOUT a two-helper output recipe has <= 88 gates (core
  bound 31 reached in 276 s): an 88 over P89 with that pattern must use a "helper + helper" level-4
  output. Open with bounds: the pattern-free case >= 25 (climbing), the full scope without two-helper
  recipes >= 25, |L2| = 24 at bound 30 after 900 s (the decisive call), several families not run.
  Methodological finding: every CP-SAT call given a hard upper bound stalled at its propagation
  bound while pure core minimisation climbed steadily and closed the sub-scope; about half the
  branch budget was spent before this was understood. Continuation: rerun the open branches as pure
  minimisation with the helper universe restricted to the never-level-3 fan set, on a free machine
  (hours). D4 >= 75 stands; the statements remain about circuits whose weight-2 set is exactly P89.

## F23. SAT on the plateau's mobile part: no 87 is a one-factor or small two-factor rewrite of four 88 plateaus (satmob agent, high; `satmob/REPORT.md`) [measured; exclusions proved as stated by the sat87 encoding]

- Structure [checked, pes_lib.fan on the repo 88@5 and 5 hunt states; no down moves]: cores 47-50
  values, mobile 6-9; the mobile -> consumer graph splits into components that are ALL "1 mobile
  helper + 1 root" (one 2 + 1 component on one circuit): exactly F2's 3-way factors, seen from the SAT
  side. Roots are outputs (14 of 43) or core helpers (29 of 43). Per-factor windows: output root ->
  k = 2-3 removed values, free = 0; helper root -> k = 4-12, free = 1-5. The whole mobile part forces
  k = 21-32, free 10-17, and is reached only as the conjunction over all levels.
- Instances are exactly sat87's I(K, |W| - 1) (full pool, distinctness, sound symmetry breaks), so
  UNSAT means "no <= 87 circuit of any depth or wiring contains K" [proved by reuse of F13's
  encoding]; sanity: m = k is SAT and decodes to a verified 88@5.
- Results [measured, one nice-8 child at a time, 120 s then 600 s retries; 94 distinct instances: 72
  UNSAT, 22 timeouts, 0 SAT]: level 1: 26 of 26 single factors UNSAT on 4 circuits; level 2: 44 of 44
  factor pairs with free <= 3 UNSAT; free = 4: 3 UNSAT (84-187 s), 14 timeouts; free >= 5: 8 timeouts.
  Hardness tracks free = k - 1 - t_W here.
- What is excluded beyond the window families: for these four plateaus, no 87 is "the plateau with
  one factor rewritten" (any new values, any re-sharing with the kept set), nor a two-factor
  re-pairing/re-sharing with <= 3 free values. Not excluded: the open free >= 4 pairs, three or more
  factors at once, the whole mobile part, 87s that drop a core value, and other plateaus.
- Frontier: free <= 3 in <= 71 s; free = 4 needs 600 s or more; free >= 5 untouched. A continuing
  campaign (`satmob/campaign3.sh`, one process, idempotent, `satmob/STOP` to end) runs the remaining
  600 s retries, two more circuits, repo triples and the whole mobile part (full, then span pool).
  With more cores: all free 4-7 pairs at 1,800 s (~40 instances) would complete level 2 and give the
  statement "an 87 keeping the core touches >= 3 factor windows"; then the kste coupled plateaus
  (radices 33/45/108), where components are genuinely larger.

## F24. The owner's depth-3 proofs replayed here (d3replay agent, high; `d3replay/REPORT.md`) [replayed; reductions read, not checked]

- Public depth-3 lower bound 93 (`lower-bound-proofs/mixcolumns-lb93-depth3/verify_all.py`, whose
  default mode is the full replay): PASS, exit 0, 2,028 s wall on the loaded machine. Counts: 1,216
  inventory hashes (+4 supplement); six-component partitions 275,354 (271,718 forest + 96 + 3,636
  Farkas, 0 uncovered), seven-component 22,060 (0 uncovered), eight-component 110,712 (1,552
  parent-price + 109,160 pair-recipe); 1,113 Farkas certificates; 20,933 forest obstructions; 710
  orbit representatives; the 97-gate control re-checked; no cached-only mode. The 772-line log equals
  the 2026-11-04 audit's log after removing timing lines. The audit's "1,222 inventory entries" is an
  edition difference (the 27-Oct repair edition adds six inherited modules; the repo edition stages
  four of them from `supplement/`, differing from the archived originals by one trailing blank line
  each). Scope: depth <= 3, one column, 2-input XOR, otherwise unrestricted; computer-assisted; the
  mathematical reductions (lossless normal form, recipe-model completeness, universality of the
  inequalities, enumerator completeness) read, not checked; optimum in [93, 97].
- The owner's latest depth-3 checkpoint (Ordinary Union, 2026-11-05): restoration needed (472 of 480
  manifest files in the browsing tree; `restore_checkpoint.py` restored 481 files from occurrences
  inside the archive, 480/480 manifest check). Default replay: PASS in 49 s (status PASS, 315 W0 roots
  covered, 49,683,204 complete W leaves, boundary counterexample left side 48, `global97_certified:
  false`); regenerated records equal the archived ones ignoring timing. `--full-core` (the complete
  315-root colored core search) timed out at 1,752 s single-threaded under load (the saved shards
  total 1,021 CPU-s on the owner's machine): not replayed here. Covered by the default replay: the
  124-gate counterexample (fully), the fixed-parent minima 97 / 107 (independent unpruned enumeration
  + 1,000 differential cases), the 2,808-plan census (identical counts), and the finite ingredients
  of the two-group union bound (reduction text read only). Not covered: the exhaustive core search
  behind "H0 = 16 => two original CC pairs", the model reduction in CORE16_CC_PROOF.md, the derived
  residual pattern (17, 13, 0, 1), and global 97@3 (open by the checkpoint's own statement).
- Together with F16 (75 replayed) and F20 (odd-helper checkers replayed): every bound the sprint
  quotes as established has now been machine-replayed here; what remains "read, not checked" is the
  mathematics of the reductions, in every case.

## F25. The 8x8-vs-4x4 gain pattern, explanations separated on existing data (xmapsep agent, high; `xmapsep/REPORT.md`, tables in `xmapsep/table.md`, `table2.md`) [measured; reading tagged]

- Observation reproduced from the 27 trials' run directories (one bookkeeping change: sw1 khazad is
  343@16 under cap 18, gain 2). Honest count after the spread: 7-9 of 20 8x8-matrix trials gained more
  than same-seed repeats differ (1-3 gates on 64x64 maps; 0-1 on 4x4), 0 of 7 4x4 trials.
- (i) prior worker-hours: both classes had the same prior search (median 2 worker-hours per map, 0 at
  exactly NIST's depth for 21 of 27 trials, same 2026-10-30 protocol); gain is uncorrelated with prior
  hours (rho 0.00 within 8x8) and the size effect is unchanged after partialling them out (rho
  +0.63..+0.67, p < 0.001). The literal form is untestable with no variance in the predictor and
  excluded as the class explanation; 4x4 maps did have ~3.7x the prior iterations per seed gate
  (faster engine), collinear with size.
- (ii) unsearched depth band: EXCLUDED as a general mechanism. Seed depth slack does not predict gain
  (gain >= 3: 5 of 10 with slack vs 5 of 10 without; rho -0.04); three of the four largest gains came
  from seeds at the cap with our circuits at the result depth; the "4x4 map at an unsearched band" test
  has effectively run three times (slack 2, 1, 1: gains 0, 0, 1). The one fitting trial (klsw17-m-8x8-
  gf256 347@6 -> 321@10) is a weak-comparison-point effect: the map went from 4.7 % to 11.8 % below
  NIST, the ordinary 10-12 % that NIST-seeded chains reach on other 8x8 maps in 1-4 worker-hours; within
  8x8, relative gain vs the pre-trial gap below NIST has rho -0.60 (p 0.005).
- (iii) 4x4 maps at the floor: SUPPORTED. On all 5 X1 4x4 maps the fresh root, NIST's circuit and ours
  end within 0-1 gate; the fresh root reaches the repo count in 20-216 s and nothing follows; all 7 4x4
  trials made their last drop within the first 31 % of the run (median 2 %). On the 3 X1 8x8 maps the
  three starts end at different numbers (grostl 582 / 364 / 366; klsw17-inv 398 / 327 / 346).
- Within-run shape: 8x8 trials: 3 still improving at the end, 7 slowing, 8 plateaued, 2 no drop; 4x4:
  all plateaued; rho(gain, lateness of last drop) +0.71. Every curve decelerates: 165 gates removed in
  the first half of the 8x8 runs, 27 in the second half, 5 in the final quarter; the 2 h pt runs' second
  hour gave about a quarter of the first.
- Reading [guess on these measurements]: the 8x8 pre-trial circuits were ordinary one-hour endpoints of
  chains that mostly ran at other depths; each trial is a 2nd-5th worker-hour on a log-decaying curve;
  "compute-limited" is true only in the sense that the curve has not flattened; "unsearched band" is
  needed for no trial; prior-optimization differences and the floor explain the class split.
- Most informative run (12 threads, 1 h): the six sw2 maps twice, from the new bests and as exact
  repeats of sw2 with a different RNG seed; the predictions of each reading are listed in the report.

## F26. The sharing identity G = 108 + delta - S cannot give a bound above 75 (sharing agent, xhigh; `sharing/REPORT.md`) [proved / finite-checked / measured, as marked]

- The identity made exact [proved]: with C_g the cone of group g's four output gates (group = bit j of
  the four output bytes), k(v) the number of cones containing gate v, S = sum_v (k(v) - 1), delta =
  sum_g (|C_g| - m_g) and D the dead gates, G = 108 + delta - S + |D| for every circuit; delta >= 0 needs
  only that the m_g are exact minima; block disjointness is not needed. Read with S = "gates used by
  >= 2 groups" it is false whenever some k(v) >= 3 (every real circuit has k = 5 gates). It is a
  tautology: S - delta = 108 - G, so "S <= c + delta" IS "G >= 108 - c". The archive's (delta, S) =
  (25, 36) is the repo 97@3 (108 + 25 - 36 = 97), not the 88; the 88@5 gives (21, 41).
- Group minima 12,16,12,16,16,12,12,12 re-proved independently [proved + finite-checked]: two
  isomorphism types (A: 8 support inputs, weight-5 rows; B: 12 inputs, weight-7); lower bounds by the
  transposition identity C(A) = C(A^T) + n - m plus one gate per distinct non-basis column; upper
  bounds by explicit verified circuits. (The sprint's value-set SAT could not even finish the 8-input
  11-gate UNSAT: the proof carries it.)
- Measurements on 4,314 distinct sampled 88s and the repo circuits [measured]: S 37-64 (median 43),
  delta 17-44 (median 23), S - delta = 20 always, no dead gates, NO group ever realised minimally
  (delta_g >= 1 for all g in all circuits, >= 3 for the type-B groups 1, 3, 4); k-distribution 62 % /
  33 % / 3.3 % for k = 1 / 2 / 5 (the k = 5 gates are bit-7 input pairs shared by five groups); 95 %
  of shared gates have masks inside every user's support, 5 % are cancellation sharing; every cone is
  irredundant (the extra gates are not "minimum circuit plus helpers").
- Proved structure: |union of cones over K| >= m_K, so |C_g ∩ C_h| <= s_gh + delta_g + delta_h; a
  defect-free group's cone lies inside its support, so defect-free groups share only masks in the
  support intersection (nothing across the 13 disjoint pairs); inside-support circuits have k(v) <= 5
  with equality only on 11 masks; support-disjoint families are exact direct sums (m_{2,4,6} = 40).
- Sub-map minima [finite-checked, closure-deficiency DFS on the transposed map]: exact m_{1,3} =
  m_{1,4} = 32 and six pairs at 28 = 12 + 16 despite sharing four inputs (zero sharing potential);
  bounds for the others; total pairwise sharing potential <= 24 (21 of 28 pairs have zero). A
  hypothetical defect-free circuit would need G >= 84, but with defects the same computation gives only
  G >= 84 - 6 delta: vacuous.
- Verdict: no bound above 75 by this route, and not in principle at the pairwise level: every cap on
  sharing has the form "shared <= potential + defects" and cancels against the identity's + delta;
  defects are free (17-44 in every known 88) and one defective bit-7 pair buys four units of S. The
  proved constraints on an 87 (S = 21 + delta; sum |C_g| = 108 + delta; the sub-map inequalities;
  defect-paid sharing across zero-potential pairs) are satisfied by every 88 the search produces, so
  they filter nothing. Heuristic facts [measured / conjecture]: an 87 resembling the 88s has delta >= 14
  and S >= 35; one not resembling them would need a minimally realised group or cross-support
  cancellation, both unobserved.

## F27. Hub capacity is exactly 3 - r; with two packing rows the survivors at G = 75 fall 996 -> 789 (qhub agent, xhigh; `qhub/REPORT.md`; CONFIRMED by `qhubcheck/REPORT.md`) [proved as checked; certificates in progress; no bound improvement]

- The finite search qreal proposed was run in full: every odd non-boundary hub value h (128,068 M /
  177,412 M^T), every r in {0, 1, 2}, every set R of represented triples and every subset S of the
  full values f with h + f a boundary pair, under three conditions: C1 [claimed proved]: the family
  {H_f + T (3 per f)} ∪ {H_i + T (r)} ∪ {H_i + H_f + P_f (1 per f)} is independent in any circuit
  containing the configuration (gate-equation argument of Lemma 4.4) - qreal's H1 used only the 3m
  vectors H_f + T; C3: Lemma O1's output assignment; X: the configuration's minimal boundary-degree
  excess (a lower bound on E_B) for shortfall 0..3.
- Finite fact H2 [finite-checked, two implementations with identical histograms]: the capacity is
  exactly 3 - r in both orientations (K_0, K_1, K_2 = 3, 2, 1) versus H1's uniform 4; the degree
  budget and O1 never lower the maximum, which is attained with X = 0 by explicit realizable local
  configurations (8 of 20 hub values at r = 0, 16 of 24 at r = 1, 12 of 24 at r = 2), so no further
  per-hub condition can tighten it.
- Lemma H2 [claimed proved]: every helper has r_i + m_i <= 3. Row HUB2: u_i <= (3 - r_i) + (q - A) for
  r_i <= 2, exact case split on A. Rows PK4 / PK5 [claimed proved, Lemma 10.4's packing argument at
  q = 4, 5]: N_3 <= 1; N_3 + 2 N_4 <= 2.
- Effect [measured, `qh_lp.py`; qreal's 996 / 381 reproduced first]: HUB2: 996 -> 863 claims (454 M,
  409 M^T), keys 381 -> 166 (the M^T q = 5 cluster 101 -> 4; q = 2 and 13 of 14 q = 3 keys die); +
  PK4/PK5: 863 -> 789 (416 M, 373 M^T), keys 166 -> 116 (q: 1: 2, 3: 1, 4: 33, 5: 11, 6: 31, 7: 7,
  8: 30, 10: 1; only 53 load-bearing); shortfall 0 / 1 / 2 / 3: 426 / 270 / 69 / 24.
- Circuit check [measured]: 13 controls + 303 real circuits, 1,264 phases, 0 violations (m_i = 0 and
  A = 0 everywhere, HUB2 slack >= 7; the underlying independence holds on all phases; a first version
  of the check had a bug, fixed before reporting).
- What remains: an M q = 6 block, the M q = 4/5 blocks, M^T q = 7-8 small-h keys, in every case every
  hub exactly on the H2 limit with L5/L23 tight; and three q <= 3 keys H2 does not touch. The report
  specifies two finite searches (joint hub systems over a fixed set of full helpers; the M^T q = 1
  family of 7-8 full helpers); neither was run. The bound stays 75: 789 claims survive by LP status.
- Independent check (qhubcheck, xhigh, 00:55 UTC): C1 CONFIRMED step by step; H2 CONFIRMED by a
  third implementation (identical histograms, K_r = 3 - r, witnesses and X = 0 confirmed); Lemma H2 /
  HUB2 and its case split CONFIRMED (integer refinement changes nothing); PK4 CONFIRMED; PK5
  CONFIRMED as implemented (n_3 + 2 n_4 + 2 n_5 <= 2 with n_j = #{u = j}) but WRONG as written in
  qhub's notation (a lone u = 4 helper would give 3 > 2): a notation slip, corrected here; the
  recounts 996 / 381, 863 / 166, 789 / 116 reproduced verbatim (byte-identical scan files) and
  independently, with the correction that the FM7/FM9 rows ARE part of every qhub variant (contrary
  to its text) and kill one baseline key under HUB2 (167 / 117 keys without them; the survivor
  counts 863 / 789 are FM-independent; FM's tables recomputed and valid); 212 real phases: 0
  violations with m_i = A = 0 everywhere; synthetic m = 1..3 configurations exercise the rows and
  the m = 4 mutations are rejected. Bookkeeping: the final scan leaves 859 LP-feasible and 551
  load-bearing keys (qhub's 116 / 53 are the baseline-restricted parts).

## F28. What transfers to Inverse MixColumns (invtransfer agent, high; `invtransfer/REPORT.md`) [checked / measured / guess, as marked]

Data: 799 inverse 118@5 record files -> 510 distinct cap-5 states (adopt 158, the 6 h star walk 640,
repo 1); no other campaign ever recorded a 118 (inv-star from scratch 124; v9c/v9d 125-128; w500 129).
- Plateau = exact Cartesian product: TRANSFERS [checked]: all 56 plateaus are products (48 fully
  closed, 8 pairwise), the same 56 the 2026-11-05 views agent found. "3-way factor = re-pairing of an
  unshared 3-input tree" DOES NOT transfer: it is the MixColumns special case. The repo plateau 200 =
  5 x 5 x 2 x 2 x 2 (core 80 of 86) has one coupled 5-block made of two genuine 3-input trees coupled
  by a core value; its free K5 is a weight-10 level-4 consumer choosing among 5 fixed weight-4
  partners; its K2s are 4-input trees with one shared half. Across 219 factors (134 K2, 21 K5, 8 K7,
  coupled 43 x 5 / 6 x 14 / 7 x 19) every single-value factor has the generalised form "one consumer,
  choice of partner among fixed available values"; none XOR to zero.
- No remove1 down-step: TRANSFERS [checked]: 0 down moves at all 510 states (exhaustive, 0 binds) and
  inside the 48 fully closed plateaus; neutral moves 4-20 (mode 9; MC 8-44, mode 16); cores 63-79 of 86.
- Distinct plateaus: 56 exact (123 cheap-identity classes, 2.2x over-split). The "vast level" DOES NOT
  transfer on this data: everything recorded at 118 is ONE lineage (one discovery event in adopt
  inv-cap5-01 after 40.5 h at 120, spread by adopt copying, then the star walk seeded with the repo 118:
  55 plateaus within helper distance 0.36); nothing reached 118 twice, so no capture-recapture is
  possible [measured]. A second, independent 119@5 family exists in 2026-10-31-long sharing only 11-12
  of the 118 family's 17 fixed first-layer pairs.
- Odd helpers and sharing identity: 118@5 circuits have 23-27 odd non-output helpers of 86; the
  inverse 88@17 (repo) 21 of 56, the archive's 88@33 18 of 56. G = 228 + delta - S + dead holds on all
  521 circuits (118@5: S 157-166, delta 47-56, S - delta = 110 always; the 88s: S 212 / 278, delta 72 /
  138); random rewirings move S and delta by +-40 but never S - delta. F20's bound is MC-specific.
- First layer: PARTLY transfers [measured]: 24-25 level-1 pairs, 17 common to all 510 states, 35 ever
  used, 105 distinct level-1 sets (Jaccard 0.75), matching the 2026-11-06 layout report (17 / 35 /
  0.74). The sprint's inherited "InvMC 118@5 has 23 level-1 sets" is reproduced by no count: treat as
  unsourced (corrected in UNDERSTANDING 7 and CHECKPOINT 2). Unlike 89@4 (frozen first layer, mobile
  slots at level 2), 39 of 56 inverse plateaus move level-1 pairs inside the plateau.
- Reading [guess]: the inverse bottom looks like 89@4 (one family found once, rigid first layer, small
  product plateaus), not like MC 88 (~1e5 plateaus, every chain new); the vast level is specific to
  MC at 88, plausibly a depth-slack effect (InvMC 118@5, MC 97@3 and 89@4 sit at or one above the
  minimum depth; uncapped MC 88 does not). The inverse's unrestricted 88 matches the forward's 88 in
  gate and helper count while every structural number differs (group floors 228 vs 108, sharing
  212-278 vs 41), suggesting "88 on both maps" is the search's reach rather than a shared wall; a
  cheap test is an uncapped campaign on the inverse from its 88@17 (never run).

## F29. The archive's 87 attempts against the sprint's SAT scopes, and the missing power control (arch87 agent, opus; `arch87/REPORT.md`) [archive claims with their own labels; one control fact changes how F13/F23 are read]

- The owner's August `fence_sat` asked the same order-free value-set question as sat87 (frozen core +
  k-mask window). On 17 windows of 89-97-gate circuits where a smaller circuit provably exists it
  returned UNSAT on all 17; the owner's verdict was "likelihood ratio ~ 1.00". The archive's other
  exact -1 window solvers over all 2^32 masks (mutant_satrepair k = 5-10, 6,472 UNSAT; xor_encoding
  k = 10-13; band_hunt to n = 11; downstep 20,893 decisions) also found 0 SAT on the August 88s. The
  stated reason: in the controls, improving moves sat at mask distance min 3, median 42, max 48;
  below k ~ 25 there is "no viable operating point" [archive]. The sprint has run no slack-1 power
  control (the m = k check, which re-finds the 88, is not one). So F13 and F23 are correct theorems
  whose weight as evidence about 87's existence is unmeasured and, if the archive's control
  transfers, close to nil at k <= 12. This caveat is now attached to F13, F23 and I.4.
- Twenty-two attempt families are tabulated (space, result in the owner's labels, why it stopped,
  relation to the sprint's scopes S1-S4, untried idea): neighbourhood certificates, fence_sat, exact -1
  windows, convex sub-blocks, alphabet rungs and pools (including union_sat, the archive's only large
  negative with a WORKING power control: floor 88 over 348,405 unions of two 88s while the same test
  finds 88s in 0.77 % of 89∪89 unions), one-target-short trims (0 of 1,630,797 complete), value-pool
  MILPs, k-foreign census (four-foreign complete around canonical_00: any circuit with <= 55 helpers
  needs >= 5 helpers outside it; five-foreign 81.9 % done), four-exterior, pricing LP (>= 84 only),
  blank exact instances (all UNKNOWN; cannot re-find known 88s), restricted classes, the demand-flow
  backbone (1,291 open triples), the 18-pair foundation, local moves, engines and learning, partial-
  circuit repair (candidate D: 87 gates computing 31 outputs, y19 missing; "rewiring D within 87
  gates remains a different question"), grammars, identities, the exit search, transposes.
- Ranked untried exact formulations with costs: R0 power control (2-6 core-hours; prerequisite); R1
  large windows only (queued in satmob); R2 r-outside as one SAT per (pool, r); R3 the demand-flow
  frontier (1,540 instances at k = 8); R4 near-miss anchors (candidate D; the 18-pair state); R5
  finish the five-foreign census with sat87; R6 band_hunt's frontier on our plateaus; R7
  class-conditional large windows; R8 the 75/76 partial circuits. Not recommended: blank instances.
- Strongest conditional negatives in the archive, with scope: four-foreign complete (exhaustive at
  k <= 5 around canonical_00), four-exterior (any 87 containing x7+x23 needs >= 5 quotient values
  outside a 114-value pool), free-closer (<= 1 mask outside the region alphabets), value pools (HiGHS
  status only), PLX3 (plane-local layer free), union_sat, one-target-short corpus, odd helpers (F20),
  depth >= 4 for any 87 (from D3 >= 93).

## F30. In-engine 88 <-> 89 transition logging: the sampler saw 3 % of stays; a chain enters 88 ~2,600 times per hour (translog agent, high; `translog/REPORT.md`, `translog/translog.diff`) [measured; prototype, experimental code kept apart from v8]

- Instrument: a copy of the v8 engine with a logger (one module + four small hooks; `translog.diff`,
  277 lines; unit tests pass) that records every accepted gate-count change within the 88-89 band,
  with a rotation-canonical identity hash of each 88 entry state and optionally its values. Overhead
  under identical load: steps per wall-second 1.008x, per CPU-second 1.003x, logger self-time 0.06 %
  (entry row ~160 us at 2.3 rows/s): not resolvable. ~3 MB per worker-hour.
- 20-minute test (one uncapped MixColumns worker from a hunt D 88@6 record, one chain, sampler at 30 s
  alongside): 869 entries into 88 (43 per minute, ~2,600 per hour), 866 distinct identities of 869 (3
  recurrences: 1 immediate return, 2 after 10 s and 75 s); consecutive entries differ by a median 7
  values. 868 excursions to 89: median 24 steps / 0.019 s, 99.65 % shorter than 30 s, 97.4 % shorter
  than 2 s, max 163 s; 770 stayed at 89, 98 reached 90; time share 56 % at 88, 34 % at 89, 10 % at 90;
  88 stays median 0.49 s. Nothing below 88; 0 of 869 entry states has a remove1 down-exit.
- Sampler calibration: the 30 s sampler caught 25 of 869 stays (2.9 %) and 11 at 89; its "hop" count
  for the period (21-24, i.e. 63-72 per hour) against 868 real re-entries means F11's "~44 plateau
  changes per chain-hour (floor)" is a sampler property that undercounts by ~35x. Measured departures
  from 88: 0.72 per second (~1 per second at D0's step rate), not the "~12 per second [guess]" inferred
  from the ledgers in F11 (corrected there).
- Identity caveat: 18 of 25 sampled mid-stay states carry a DIFFERENT cheap v3 signature from their
  own stay's entry state (3-10 values replaced inside one contiguous 88 stay), so v3 is not constant
  along the walk's neutral components: F11's graph nodes and the signature-based plateau counts (F12
  upper bounds, F14 "distinct plateaus per worker-hour") are finer than neutral components by an
  unknown factor; exact identity needs the exact catalogue offline on the logged values (the
  `values_gates = 89` knob keeps the 89 state right after each exit for the plateau-before/after
  test). v3 signatures of the 609 logged visits: 366 distinct (~1,100 per hour), 243 revisits.
- Proposed 1 h / 12-worker experiment (pre-registered analysis in the report): D0 settings with the
  logger, restarts off, 6 distinct hunt D 88 records each given to two workers (same-start pairs as
  the positive control for meeting/separation, 15 cross pairs), sampler alongside; ~31k entry states;
  exact plateau identity of consecutive < 2 s hops and of every cross-worker coincidence; the R2 null
  model on exact P and M; sampler correction factors for every F11/F14 number. This is the experiment
  that would decide the connectivity question (UNDERSTANDING 8).

## F31. SAT on coupled plateaus: the remove1 fan cannot see a coupled factor; its windows start at free 5 and none finished (satmob2 agent, high; `satmob2/REPORT.md`) [checked / measured; no 87]

- Targets: seven coupled plateaus with member states located by sample hash: kste #43 (33 x 3^7), #34
  (45 x 3^4), #41 (108 x 3^4), hunt p943c008e (2,101 x 15 x 11 x 3 x 3), hunt pce9227a (18,927 x 15 x
  3 x 3), giants p8042472 (62,856 x 3), giants p55f9dc0 (69,228 x 3 x 3); plateau cores 37-48 values.
- Key structural finding [checked, `coupling.py`]: a coupled-factor choice value is locally mobile
  under remove1 iff some other listed choice differs from the current one by that value alone; the
  rest only leave in groups of 2-13 values, so the fan calls them core (local core 1-11 values larger
  than the plateau core; only 4-21 of a factor's other choices are at distance 1, e.g. 10 of 2,100,
  14 of 62,855). Consequently satmob's decomposition on a coupled plateau silently reports 1 + 1
  components (46 of 50 here) and F23's expectation that coupled plateaus would show larger local
  components is wrong; the coupled factor's window must be built from the compressed plateau object
  (`fac.py`: the factor's choice at S plus its consumers, any-pair forced closure; same sat87
  semantics).
- Instances [measured; one nice-8 child, 120 s then 600 s]: 165 distinct, 155 UNSAT, 10 timeouts, 0
  SAT. Local (satmob-style): level 1 50 of 50 UNSAT; level 2 pairs with free <= 3: 105 of 106 UNSAT.
  Coupled-factor windows: k = 10-38 removed values, free 5-20 (kste 108: k = 10, free 5; kste 33:
  k = 12, free 5; kste 45: k = 17, free 9; 2,101: k = 18, free 9; 18,927: k = 31, free 15; 62,856:
  k = 36, free 20; 69,228: k = 38, free 20): all seven TIMEOUT at 120 s, the two free-5 ones also at
  600 s. Hardness by free: 0: <= 0.1 s, 1: <= 1.1 s, 2: <= 7 s, 3: <= 116 s, >= 5 unsolved.
- What is excluded on the seven plateaus: no 87 is the state with one single-swappable value
  rewritten, nor two such windows together with free <= 3 (this covers the pure 3-way factors and the
  single-swappable fringe of each coupled factor). Not excluded: any rewrite touching a group-moving
  value of a coupled factor, i.e. the coupled factor as a unit: in the 3-way case "one factor
  rewritten" is decided exactly at level 1 in seconds; in the coupled case the exact instance starts
  at free 5 and is at or beyond the frontier (free 4 at 600 s). Cheapest open coupled statement: kste
  108 (k = 10, free 5), a 1-2 h run or the ladder/lex encoding; windows on the factor's minimal move
  groups (sizes 2-5) are the next lever. A continuing campaign (`satmob2/campaignB.sh`, one child,
  idempotent, `satmob2/STOP`) runs the free-4 singles, span-pool variants and free-4 pairs.

## R3. Corrections from the third round of independent checks (bridgecheck, q89check, qrealcheck, d3replay; 23:00 UTC onward)

- F15 (q89check): census and plateau CONFIRMED with independent code; P2's population corrected (26
  first-layer-equal 90@4 states on disk, 11 of them in the family's remove1 basin; the 8 run-final
  traps are not). Applied in F15 and UNDERSTANDING 7.
- F13/F23/I.4 (arch87): the archive's fence_sat power control (17 of 17 UNSAT on windows that
  provably contained an improvement) means the sprint's window refutations have unmeasured, probably
  negligible, evidential weight about 87 at k <= 12; a power control (R0) is running; the "advance"
  wording in I.4 is qualified accordingly.
- F11/F14 (translog, F30): the sampler-based hop rate (~44 per chain-hour) undercounts real 88
  re-entries (~2,600 per chain-hour) by ~35x; "~12 departures per second" was a wrong guess (0.72 per
  second measured); the cheap v3 identity changes within a single 88 stay, so signature-based node
  and plateau counts are finer than neutral components. Applied in F11, F14 and UNDERSTANDING 4.
- F23 (satmob2, F31): the mobile-part decomposition by remove1 fans does not see coupled factors;
  on coupled plateaus its level-1/2 UNSATs are a strictly weaker statement than on 3-way plateaus,
  and the expectation of larger local components there was wrong.
- F27 (qhubcheck): C1, H2, Lemma H2 / HUB2, PK4 / PK5 CONFIRMED; PK5's written formula and the FM
  remark corrected; load-bearing keys are 551, not 53. Applied in F27.
- F21 (qrealcheck): all lemmas and rows CONFIRMED, LP reproduced independently; key bookkeeping
  corrected (1,377 load-bearing keys, 264 with q <= 3). Applied in F21.
- F17 (bridgecheck): numbers CONFIRMED (0 row violations, min slack 10, tail profiles, E_B 0-7, h
  16-23, weight-2 rigidity); interpretation corrected: margin = -(E_B + L_H) <= 0 for every circuit
  of every gate count, so nothing "saturates" specifically at 88; reconstruction ambiguity of the
  controls under-counted; "weight-2 values are represented labels" false. Applied in F17 and
  UNDERSTANDING 8.

## R2. Corrections from the second adversarial review (F11-F13, I; `review2/REPORT.txt`, ~17:15-17:45 UTC)

- F11 "disjoint trails" BLOCKED as a conclusion: the 8 cross-chain meetings equal the independent-
  wandering expectation for ~1.3e5 effective nodes (null model); the graph says nothing about
  connectivity. Survived: 0 remove1 down-exits at all 1,869 states (recomputed), hop locality,
  the ~44/h floor. Wording fixed in F11, UNDERSTANDING 4 and 8.
- F12 WEAKENED (caveat since resolved, see the F12 giants bullet): the alpha fit and the 1e5 centre
  were conditional on excluding 18 giant entries of unknown size (alpha 1.35 -> 0.95 or 0.50 if they
  were large singletons; they are <= 2.6e6 states and unshared) and on the effort ratio
  behind the signature alpha (HT 79k-400k). The floor is not "distribution-free": it assumes
  independent, exchangeable chains (17 of 40 catalogued chains share 6 first roots; no same-root
  pair shared a plateau). Chao2/D2 reproduce exactly; the chain-pair floor is >= 3,041.
- F13 SURVIVED on soundness (equivalence via fresh splits, symmetry breaks, UNSAT independent of
  pruning); its "hardness tracks free values not k" prediction is refuted in strong form; counts
  updated from the batch.
- I.1/UNDERSTANDING: five sentences that could be read as "87 is unreachable by heuristic search"
  were replaced (F11 reading, UNDERSTANDING 4 x2, F11 title, UNDERSTANDING 8); mc24 unresolved is
  58-66 % per completed plateau, 60-64 % pooled (kste1 56 % correct).
- Hindsight: F11-F13 had no pre-registered predictions; F14 P1-P5 and Q1-Q5 are the pre-registered
  tests for hunt D. Next measurements adopted: re-run compress on the 18 giant seeds with larger
  limits (identity + size), exact catalogue of all sampled states, Q1-Q5 at 04:10 UTC.

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
