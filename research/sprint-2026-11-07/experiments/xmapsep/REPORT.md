# xmapsep: separating the explanations of the 8x8-vs-4x4 gain pattern from existing data

Agent "xmapsep", 2026-11-07 (transcribed by the coordinator from the agent's final message; the agent
could not write this file. Tables 1 and 2 are in `table.md` and `table2.md` in this folder; all data
in `trials.csv`, `workers.csv`, `prior_wh.csv`, `stats.txt`, `series/`). No search was run; one python
process at nice 10. Tags: [measured] read from the files named; [guess] interpretation. The repo state
"before" every trial is `git ls-tree d281a78^ circuits`.

## 0. Summary

Observation (F7/F9/F10, I.5) reproduced from the run directories: 16 of 20 8x8-matrix trials gained
>= 1 gate at NIST's depth, 10 of 20 >= 3; 2 of 7 4x4 trials gained 1 [measured, `trials.csv`]. One
bookkeeping difference: sw1 khazad is 343@16 under cap 18 (gain 2) where F10 counted 344@15 (gain 1).

- (i) compute-limited / few prior worker-hours at that depth. Literal form: untestable and excluded
  as the class explanation. Both classes had the same prior search (median 2 worker-hours per map; 0
  hours at exactly NIST's depth for 21 of 27 trials, because the 2026-10-30 batch gave every map one
  uncapped + one low-capped worker-hour) [measured, `prior_wh.csv`]. rho(gain, prior h at cap) = 0.00
  within 8x8; the size effect is unchanged when prior hours are partialled out (rho +0.63..+0.67,
  p < 0.001) [measured, `stats.txt`]. The weak form ("8x8 maps have not reached the level the search
  reaches") is supported (sections 3, 4).
- (ii) unsearched depth band. Excluded as a general mechanism: seed depth slack does not predict gain
  (8x8, gain >= 3: 5/10 slack > 0 vs 5/10 slack = 0, rho -0.04); 9 of 10 slack > 0 trials gained 0-5;
  three of the four largest gains (klsw17-m-8x8-gf256-inv 19 and 16, skop15-8x8-gf256-inv 9) came from
  seeds at the cap with our circuits at the result depth; the "4x4 map at an unsearched band" test
  has effectively run three times (lw16-4x4-gf256-inv-circ slack 2, jpst17-4x4-gf256 slack 1, anubis
  slack 1: gains 0, 0, 1) [measured]. The one fitting trial (klsw17-m-8x8-gf256 347@6 -> 321@10) is a
  weak-comparison-point effect: vs NIST at the cap the map went 4.7 % -> 11.8 % below, the same
  10-12 % NIST-seeded chains reach on klsw17-m-8x8-gf256-inv (11.1 %) and grostl (11.2 %) in 1-4
  worker-hours [measured].
- (iii) 4x4 maps at the floor. Supported: on all 5 X1 4x4 maps fresh root, NIST's circuit and ours
  end within 0-1 gate; the fresh root reaches the repo number in 20-216 s, then nothing for the rest
  of the hour; all 7 4x4 trials made their last drop within the first 31 % of the run (median 2 %).
  On the 3 X1 8x8 maps the three starts end at different numbers (grostl 582/364/366;
  klsw17-m-8x8-gf256-inv 398/327/346; skop15-8x8-gf16 157@11/151@13/146@14) [measured, `workers.csv`].
- (iv) spread. Natural same-seed repeats differ by 1-3 gates on 64x64 maps, 0-1 on 4x4 [measured,
  section 5]. Seven of the sixteen 8x8 "gains" are 1-3 gates and indistinguishable from a repeat; 7-9
  (gains 5,5,5,6,9,16,19,26, khazad 2 borderline) are outside. "About 10 of 20 at least three" stands;
  "16 of 20" overstates what is above noise.
- What the data favour [guess on the measurements of sections 3-5]: the 8x8 pre-trial circuits were
  one-hour endpoints of chains that mostly ran at other depths (our any-depth best sits 1-9 depth
  levels from NIST's depth on 15 of 20 8x8 trials); each trial is a 2nd-5th worker-hour on a
  log-decaying curve (8x8 own-best drops: 165 gates in the first half of the runs, 27 in the second
  half, 5 in the final quarter; pt hour 2 gave 1, 2, 0, 4 gates after 5, 14, 5, 1 in hour 1); the gain
  is roughly (the 7-12 % below NIST that 1-4 wh reach) minus (what the batch hour had left at that
  depth): within 8x8, relative gain vs pre-trial gap below NIST rho -0.60, p 0.005. This is I.5's
  "prior-optimization differences" reading. "Compute-limited" is true only in the sense that the curve
  has not flattened; "unsearched band" is needed for no trial.

## 1. The 27 trials

See `table.md` (Table 1: run, map, matrix, cap, trial worker-hours, seeds, repo best <= cap, NIST,
result, gain at cap, gain anywhere, slack, nearest prior depth, prior worker-hours at cap / cap>= /
total, first improvement, first gain, last own drop, class) and `table2.md` (Table 2: depth drift of
the earlier search, gap below NIST before/after, own gain in first half / second half / final quarter,
last own drop fraction, class).

## 2. Prior search per map (what (i) has to work with)

- 21 of 27 trials: 0 prior worker-hours at exactly the cap. Exceptions: grostl x1a (4 h), small-scale-
  aes (6 h), pt1 skop15-8x8-gf16 and klsw17-m-8x8-gf256-inv (2 h = the x1a arms), sw1 khazad and
  fox-mu8 (4 h = pt2) [measured, `prior_wh.csv`].
- Prior worker-hours on the map at any cap: median 2 in both classes (8x8 range 2-214, fox-mu8's
  v3/v6/v7 history at depths 5-11; 4x4 range 0-7). Same 2026-10-30 protocol for both classes. Iterations
  do differ: 4x4 maps run 1,400-2,500 it/s vs 340-900 for 8x8, so per gate of the seed they had ~3.7x
  the prior iterations (median 35 vs 9.6 thousand per gate) [measured]; collinear with size by
  construction.
- Correlations [measured, `stats.txt`]: gain vs prior h at cap: all 27 rho +0.03 (p 0.89), 8x8 0.00;
  vs prior h any cap +0.29 (p 0.15), 8x8 +0.08; vs prior iterations per gate -0.17 / +0.01. 2x2 (8x8,
  gain >= 3 vs prior h at cap > 0): 2/5 vs 8/15, Fisher p = 1.0. Partial rank correlations gain ~
  inputs controlling for wh at cap, wh total, slack, iterations per gate: rho +0.63 to +0.67, all p <
  0.001; gain ~ 8x8 class +0.49 to +0.54. Reverse partials (gain ~ prior hours | size): +0.04 to +0.10.
- Caveat: with ~2 hours for everyone there is almost no variance in the predictor; "no correlation"
  means "not testable", not "no effect". The class comparison is the strong statement: equal prior
  hours, unequal gains.

## 3. Starting points and floors ((ii), (iii))

- Slack vs gain [measured]: 8x8 gain >= 3: slack > 0 5/10 vs slack = 0 5/10 (p = 1.0); gain >= 1:
  8/10 vs 8/10; rho -0.04. Result band with no prior circuit within +-1 depth: exactly one trial
  (klsw17-m-8x8-gf256, nearest 2).
- klsw17-m-8x8-gf256 re-read [measured + guess]: before, 347@6 was our best at <= 11, 4.7 % below
  NIST's 364@11, while the uncapped batch chain had drifted to 336@12...326@15. After 1 h from 347@6
  under cap 11: 321@10, 11.8 % below NIST; NIST-seeded 1-h chains reach 11.1 % and 11.2 % below NIST
  on two other maps. The 26 is the distance between a poor comparison point and the ordinary 1-hour
  level [guess]. Within 8x8, relative gain vs pre-trial gap below NIST rho -0.60 (p 0.005); post-trial
  gaps compress to 5.6-14.9 % (median 7.4 %) from 4.7-14.6 % (median 6.2 %).
- X1 fresh roots [measured]: 4x4 maps reach the repo count at 20 s (small-scale-aes 42@5), 37 s (ss16
  96@5, one below repo 97), 54 s (lw16 82@5), 216 s (jpst17 78@6); MixColumns fresh 89@5 at 243 s, never
  88. NIST-seeded arms stop at the same numbers. No 4x4 worker dropped again after 20 % of the hour.
  8x8: grostl fresh 582@12 (130 restarts, still dropping at 57 min) vs 364@11 vs repo 366@12; klsw17-m-
  8x8-gf256-inv 398@12 vs 327@12 vs 346@12; skop15-8x8-gf16 157@11 vs 151@13 vs 146@14. Three starts
  converge on 4x4 maps, not on 8x8: (iii) holds for 4x4, excluded for 8x8.
- NIST-seeded vs ours-seeded workers in pt (2 h each): a chain from NIST's 6-10 %-worse circuit ends
  within 3 gates of, or below, a chain from our best in 4 of 5 8x8 maps [measured]. Reading [guess]:
  our pre-trial 8x8 circuits are ordinary one-hour endpoints, not optimised points.

## 4. Within-run: still improving or plateaued?

- 8x8 (20): still improving 3 (klsw17-m-8x8-gf256 sw2, last drop at 96 % of the hour; klsw17-m-8x8-
  gf256-inv pt1, 92 %; fox-mu8 pt2, 75 %), slowing 7, plateaued 8, no drop 2 (depth-only results).
  4x4 (7): plateaued 6, no drop 1; last drops at 1-31 % of the run, median 2 % [measured].
- Gain and lateness go together: rho(gain, fraction at last drop) = +0.71 (p 1e-4).
- Every curve decelerates: over the 20 8x8 trials the seeded workers removed 165 gates in the first
  half of the runs, 27 in the second half, 5 in the final quarter. The 2-h pt runs are the I.5 "second
  worker-hour" test in within-run form: hour 2 gave 1, 2, 0, 4 gates after 5, 14, 5, 1 in hour 1.
  Neither "same rate" (pure (i)) nor "stops" (pure (ii)): about a quarter of the first hour.
- Time to first gain over the repo best is wide on 8x8 (0.1 min to 41 min); the biggest gainers found
  their first gate within a minute.

## 5. Spread between runs ((iv))

Same seed, independent runs: klsw17-m-8x8-gf256-inv from NIST 368@12: 327@12 (1 h) vs 330@12 (2 h);
khazad from ours 345@15: 342@16 (2 h) vs 343@16 (1 h); fox-mu8 from ours 505@11: 500@11 vs 500@11;
skop15-8x8-gf16 from NIST: 151@13 vs 146@14. 1-3 gates apart on 64x64 (the longer run is not the better
one in 2 of 3 pairs); different seeds same map: 2-8; 4x4 pairs: 0-1 apart [measured]. Honest count:
7-9 of 20 8x8 trials beyond the spread, 0 of 7 4x4.

## 6. Predictions for the I.5 runs; the most informative single run

Run 1 (second worker-hour per sweep map from its new best): literal (i): gains like the first hour;
(ii): ~0 everywhere; log-decay + prior-optimization: a quarter to a third of the first hour (median
0-1, 3-6 of 12 >= 1, klsw17-m-8x8-gf256 3-8 more, skop15-8x8-gf256-inv 1-3); (iv) alone: 1-3 gates on
about half the maps, uncorrelated with the first hour. Run 2 (4x4 map at an unsearched band): already
answered three times (gains 0, 0, 1); not worth threads. Run 3 (same-seed repeats): three 64x64 pairs
exist (1-3 apart). Most informative single run (12 threads, 1 h): the six sw2 maps twice, six workers
from the new bests and six exact repeats of sw2 from the old seeds with a different RNG seed; if only
one thread: klsw17-m-8x8-gf256 cap 11, 1 h from 321@10 (decay: 3-8; (ii): 0; (iv): +-2) and 1 h from
347@6 again.

## 7. Limits

Prior hours use planned durations; the v3 fox-mu8 caps are guessed; X1 trials are scored on the union
of both arms; pt on the union of two pull-sharing workers (sharing fired twice, on maps that gained
0-1). "Still improving" is read from drops of the best at <= cap; neutral walking without a drop is
invisible, and 1 h is a short window for a log-time process. n = 27 (20/7); p-values are for reading,
not deciding. The robust statements are qualitative: equal prior hours across classes; three starts
converging on 4x4 and not on 8x8; the slack 2x2 at 5/5 vs 5/5; the 165/27/5 deceleration; same-seed
repeats 1-3 gates apart.
