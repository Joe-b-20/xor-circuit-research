# exp2: are the 88 seed regions disconnected or far apart? (2 h, 8 MixColumns workers, departure keys logged)

Pre-registered in `exp2/DESIGN.md` (written 03:31 UTC before launch, verbatim in the appendix); run as
registered except where noted under "Deviations". Run 03:31:24-05:25:34 UTC 2026-11-08 (6,849 s wall;
campaign clock t = 0..7,200 s per worker, the engine's `duration = 120m`), `exp2/E2.toml`: exp1 / hunt D0
settings + `translog.departure = true`, restarts off, `nice -n 8`, 8 workers = 4 same-start pairs q0..q3 on
four hunt-D 88 records not used in exp1 (`seeds.json`: q0 D4/free-00 anneal3#1935188101, q1 DN/free-01
naive#4079938347, q2 D0/free-02 naive#1611000713, q3 D4/free-03 paar#2407742785; seed-to-seed helper
distance 0.80-0.87). All 8 workers ran their first chain for the full 2 h (10.6-12.4 M steps each), worker
best 88 everywhere, **0 rows below 88 in 46,017 entries into 88**. One analysis process (`track.py`, nice 8)
ran alongside: v3 signatures of all 46,017 entries (0 missing) and 5,410 s of exact cataloguing.

Instrument change: `translog.departure` (`patch_departure.py`, `departure.diff`, 62 lines, knob default off,
v8 in the repo untouched): every exit from 88 now carries `xid`/`xv`, the 88 state left, computed from the
proposal journal's net changes. Every exit row carries it (entries minus departures = 0 or 1 per worker,
the chain being at 88 when the clock stopped). This fixes exp1's failed exit-state reconstruction and gave
the exact per-hop test in (d).

Distance: Jaccard distance of the 56-value helper sets (88 values minus the 32 targets), min over the 4 byte
rotations. **Scale (calibration, added at the 30 min interim, not pre-registered): two states on the same v3
node have d <= 0.222 (n = 281, median 0.133); consecutive entries of one chain median 0.194, p90 0.25; two
unrelated states ~0.85 (cross-seed current-state median 0.83-0.87 throughout, seeds 0.80-0.87).** The metric
saturates near 0.85, which matters for reading (a)-(c).

## Results per measurement [measured]

**(a) Same-start drift.** Current-state distance of the two chains of a pair, 5 min -> 60 min -> 115 min:
q0 0.58 -> 0.82 -> 0.77; q1 0.60 -> 0.76 -> 0.85; q2 0.38 -> 0.62 -> 0.88; q3 0.25 -> 0.74 -> 0.85. It
**grows within 20-45 min and saturates at 0.77-0.91, the cross-seed level** (cross median 0.86-0.87 at the
same ticks). It does not keep returning to 0 in 3 of 4 pairs: new shared v3 nodes per 15-min window (incl.
the start node) q0 1,0,0,...; q1 1,4,0,...; q2 56,0,0,...; q3 85,7,42,0,0,0,46,39. So q0, q1, q2 stopped
meeting after 0-30 min and never re-met in the remaining 90+ min; only q3 (high 88 share, 60-68 %) kept
re-meeting to the end (218 shared nodes).

**(b) Wander.** Distance of each chain's current state to its own start: 0.25-0.67 at 5 min, 0.47-0.83 at
60 min, 0.42-0.89 at 115 min. Six of eight chains reach 0.73-0.89 (the unrelated-state level) within
15-25 min; q0-01 stays at 0.28-0.51 all 2 h (it hovers near its start), q2-01 at 0.40-0.67. Four chains
spent long stretches off 88 (longest excursions 3,708 s q1-00, 3,406 s q1-01, 2,651 s q2-01, 1,565 s q2-00;
88 time share 28-36 %), during which their current 88 state is frozen (flat rows in the table).

**(c) Cross-seed.** Shared v3 nodes between chains of different groups: **0 at 1 h (P = 2.66e7, null
expectation 205, 95 % [177, 233]) and 0 at 2 h (P = 6.22e7, expected 478, [436, 521])**; 0 shared exact
states. With M = 0, independent wandering would need N_eff >= P/3 = 2e7 nodes (95 %), 160x the R2 value of
1.3e5. Same-start pairs (start node excluded): 192 at 1 h (expected 56) and 277 at 2 h (expected 124), 218
of the 277 from q3. Minimum cross-seed distance between visited states (thinned, 1 state per 5 s, 494-1,273
per chain): per 15-min window, min over the 24 cross pairs 0.53, 0.55, 0.62, 0.53, 0.55, 0.68, 0.77, 0.70
(slope +0.030 per window, rho +0.80); median over pairs 0.77 ... 0.81 (slope +0.006, rho +0.63); per-pair
slopes median +0.008, 9 of 24 negative, none below -0.03. Cumulative (any times) minimum 0.53 -> 0.377
(reached by window 3, then constant); the time-shuffled control gives 0.42 -> 0.38, i.e. sampling more
states explains the drop, and the actual-minus-shuffled gap (+0.05 -> 0) says the closest cross pairs are
NOT concentrated late. **The closest any two cross-seed states ever came is 0.377, above the same-node
scale (<= 0.222).** The current-state cross minimum is 0.62-0.80 at every tick.

**(d) Exact identity (pes_lib.compress, 60 s cap).** Cross-seed shared nodes: none to test. **Per-hop test
with the new departure keys, 100 consecutive (departure state, next entry) hops of q1-00 (t = 601-695 s):
99 of 100 next entries are in the exact plateau of the state the chain left, 1 not**; 43 of the 100 change
the v3 signature (42 of them still on the same exact plateau); 12 return to the exact departure state;
median |xv ^ entry| = 6 values. Plateaus met: products of 2,187 (3^7), 8,019, 54,675, 105,705 and 120,285
states. Same-start shared nodes: 69 exact meetings (second chain's state in the first's exact plateau),
0 different, 73 timeouts (budget exhausted before the remaining 137 queued nodes were tried).

## Verdict per prediction

* **FAR APART ("the cross-seed minimum distance shrinks over time"): not supported.** No cross meeting in
  2 h (0 vs 478 expected), the per-window cross minimum trends UP (+0.030 per 15 min, rho +0.80; median
  pair +0.006), the registered "shrinks" criterion (median-pair slope < -0.01 with rho < -0.5, or any
  meeting) is not met, and the cumulative minimum's drop is matched by the shuffled control.
* **DISCONNECTED, clause 1 ("cross-seed minimum stays bounded away from 0"): supported** at the 2 h scale:
  minimum ever 0.377, per-window minima 0.53-0.77, all above the same-node scale 0.22.
* **DISCONNECTED, clause 2 ("same-start distance saturates below the cross-seed distance"): not
  supported.** Same-start pairs saturate at 0.77-0.91 within 20-45 min, the same level as cross-seed pairs
  (0.83-0.87); the registered "bounded" rule (min cross > same-start saturation + 0.05) fails because the
  cross per-window minimum (0.53-0.77) lies BELOW the same-start saturation level.
* **Reading.** Neither registered picture fits. Chains do not live in fixed seed regions that keep
  same-start chains together: 3 of 4 same-start pairs drift to the unrelated-state distance in under an
  hour and stop meeting, just as cross-seed pairs never meet. What exp1 called "local trails" is a short
  memory of the start (tens of minutes), not membership of a region; after it, a chain is as unrelated to
  its twin as to a chain from another seed, at least in helper distance. The 0-of-478 cross result and the
  post-separation silence of same-start pairs both say the walk explores a space far larger than
  N_eff = 1.3e5 (>= 2e7 v3 nodes under the independent-wandering null), so with 2 h chains "disconnected"
  cannot be told from "too large to revisit"; a meeting test at this scale is uninformative, and helper
  distance cannot see structure beyond its ~0.85 ceiling. The hop test confirms exp1 exactly: 99 % of
  88->89->88 hops stay on the same exact plateau, so plateau changes are rare events inside a dense shuffle.

## Deviations and caveats

* Campaign clock 7,200 s against 6,849 s wall (the engine's clock, as in exp1); analysis to t = 7,077 s
  (the earliest last-88 row over the eight logs).
* Not pre-registered, added at the 30 min interim: the distance calibration (same-node and consecutive
  distances), new same-start meetings per window, and `shares.py` (time shares, longest excursions).
* (d) budget: 5,410 s of exact time; 73 same-start compress calls timed out at 60 s and 137 queued shared
  nodes were not tried; no cross-seed node existed to test.
* "Bounded over 2 h" does not prove disconnection (registered caveat). Helper Jaccard is coarse: two
  members of one exact plateau of 1e5 states can differ in it; the 0.22 same-node bound is empirical
  (n = 281 same-start coincidences), not a theorem.
* The current state of a chain sitting at 89/90 for up to an hour is its last 88 state (4 chains), which
  flattens (a)/(b) over those stretches.

## Files (all under `~/xs-campaigns/2026-11-07-sprint/translog/exp2/`)

`DESIGN.md` (pre-registration), `patch_departure.py` + `departure.diff` (engine change, applied to
`../xorflux-translog/`; `loop.py.orig`, `translog.py.orig` are the pre-patch copies), `check_smoke.py` +
`runs-smoke/` (60 s smoke), `pick_seeds.py` -> `seeds.json`, `make_toml.py` -> `E2.toml`, `run.sh`,
`driver.log`, `E2.run.log`, `runs/E2/workers/*/translog.jsonl` (the logs), `track.py` / `track.sh` /
`track.log` (online signatures + exact work) -> `sigcache.json`, `exact.jsonl`, `track_status.json`,
`analyze_exp2.py` -> `analysis.json`, `analysis.out`, `shares.py` -> `shares.out`, `make_report_exp2.py` +
`report_head.md` -> this file.