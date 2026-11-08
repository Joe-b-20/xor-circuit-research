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

## Measurement tables (analysis.out, from analyze_exp2.py)

```
workers 8; common log end t = 7077 s
  q0-00: rows 20895, 88 entries 6917, departures 6917, distinct ids 6840, rows below 88 0, helpers per state [56]
  q0-01: rows 22608, 88 entries 9309, departures 9308, distinct ids 8606, rows below 88 0, helpers per state [56]
  q1-00: rows 13940, 88 entries 3584, departures 3583, distinct ids 3367, rows below 88 0, helpers per state [56]
  q1-01: rows 20412, 88 entries 4205, departures 4205, distinct ids 3675, rows below 88 0, helpers per state [56]
  q2-00: rows 17464, 88 entries 4137, departures 4136, distinct ids 4091, rows below 88 0, helpers per state [56]
  q2-01: rows 18126, 88 entries 3529, departures 3528, distinct ids 3232, rows below 88 0, helpers per state [56]
  q3-00: rows 20444, 88 entries 6987, departures 6987, distinct ids 6814, rows below 88 0, helpers per state [56]
  q3-01: rows 19759, 88 entries 7349, departures 7348, distinct ids 7334, rows below 88 0, helpers per state [56]

(a) same-start pair distance of current 88 states, every 5 min (helper Jaccard, min over rotations)
  t(min)     5    10    15    20    25    30    35    40    45    50    55    60    65    70    75    80    85    90    95   100   105   110   115
  q0-00/q0-01   0.58  0.65  0.68  0.67  0.68  0.70  0.65  0.67  0.80  0.77  0.80  0.82  0.83  0.82  0.76  0.78  0.78  0.80  0.76  0.77  0.77  0.76  0.77
  q1-00/q1-01   0.60  0.67  0.70  0.81  0.83  0.86  0.82  0.82  0.83  0.74  0.82  0.76  0.85  0.85  0.85  0.85  0.85  0.85  0.85  0.85  0.85  0.85  0.85
  q2-00/q2-01   0.38  0.58  0.78  0.67  0.63  0.73  0.73  0.71  0.73  0.81  0.76  0.62  0.73  0.73  0.55  0.68  0.63  0.67  0.67  0.91  0.88  0.91  0.88
  q3-00/q3-01   0.25  0.70  0.62  0.65  0.51  0.35  0.44  0.63  0.70  0.71  0.71  0.74  0.74  0.81  0.85  0.78  0.82  0.81  0.56  0.63  0.65  0.83  0.85
(b) distance of each chain's current state to its own start
  q0-00         0.56  0.65  0.62  0.62  0.62  0.62  0.62  0.62  0.76  0.77  0.77  0.76  0.78  0.77  0.76  0.78  0.77  0.78  0.76  0.76  0.77  0.76  0.77
  q0-01         0.30  0.30  0.44  0.51  0.38  0.49  0.47  0.49  0.44  0.42  0.51  0.47  0.44  0.47  0.38  0.30  0.28  0.30  0.38  0.33  0.35  0.33  0.42
  q1-00         0.42  0.53  0.55  0.76  0.83  0.83  0.81  0.78  0.76  0.76  0.78  0.78  0.78  0.78  0.78  0.78  0.78  0.78  0.78  0.78  0.78  0.78  0.70
  q1-01         0.67  0.65  0.73  0.74  0.74  0.71  0.65  0.63  0.68  0.68  0.68  0.60  0.80  0.80  0.80  0.80  0.80  0.80  0.80  0.80  0.80  0.80  0.80
  q2-00         0.38  0.40  0.71  0.74  0.74  0.74  0.77  0.77  0.74  0.82  0.82  0.76  0.82  0.78  0.74  0.82  0.73  0.63  0.63  0.63  0.63  0.63  0.89
  q2-01         0.25  0.56  0.47  0.51  0.51  0.30  0.44  0.40  0.42  0.42  0.55  0.55  0.55  0.55  0.55  0.55  0.55  0.55  0.55  0.67  0.67  0.65  0.65
  q3-00         0.30  0.68  0.74  0.78  0.73  0.73  0.77  0.73  0.70  0.58  0.68  0.71  0.73  0.58  0.76  0.82  0.81  0.82  0.73  0.73  0.74  0.82  0.85
  q3-01         0.35  0.25  0.56  0.63  0.73  0.73  0.71  0.80  0.76  0.73  0.74  0.73  0.77  0.74  0.77  0.80  0.74  0.74  0.77  0.71  0.73  0.55  0.58
cross-seed current-state distance (median / min over the 24 cross pairs)
  median        0.85  0.85  0.86  0.86  0.87  0.85  0.86  0.83  0.87  0.84  0.87  0.86  0.86  0.87  0.86  0.85  0.86  0.86  0.87  0.87  0.87  0.86  0.87
  min           0.73  0.76  0.71  0.74  0.80  0.78  0.77  0.74  0.80  0.63  0.68  0.74  0.74  0.62  0.74  0.74  0.73  0.73  0.73  0.74  0.74  0.71  0.73
  seed-to-seed distances (cross groups): min 0.796 median 0.851

(c) minimum distance between visited states (thinned to 1 state / 5 s per chain: q0-00 1050, q0-01 1273, q1-00 533, q1-01 584, q2-00 638, q2-01 494, q3-00 1091, q3-01 1153)
  per-15-min-window minimum distance, windows 1..8
  q0-00/q1-00   0.76  0.78  0.82  0.82     -     -     -  0.87  slope +0.0151 rho +0.97
  q0-00/q1-01   0.74  0.76  0.76  0.77  0.81     -     -     -  slope +0.0148 rho +0.97
  q0-00/q2-00   0.74  0.85  0.85  0.78  0.78  0.78     -  0.83  slope +0.0034 rho +0.06
  q0-00/q2-01   0.71  0.74  0.76  0.82     -     -  0.78  0.80  slope +0.0099 rho +0.83
  q0-00/q3-00   0.81  0.83  0.83  0.81  0.81  0.76  0.86  0.78  slope -0.0035 rho -0.28
  q0-00/q3-01   0.78  0.82  0.77  0.81  0.74  0.82  0.82  0.81  slope +0.0032 rho +0.27
  q0-01/q1-00   0.81  0.78  0.81  0.86     -     -     -  0.86  slope +0.0094 rho +0.79
  q0-01/q1-01   0.82  0.78  0.83  0.74  0.70     -     -     -  slope -0.0288 rho -0.70
  q0-01/q2-00   0.80  0.85  0.80  0.81  0.83  0.85     -  0.85  slope +0.0060 rho +0.60
  q0-01/q2-01   0.78  0.81  0.80  0.82     -     -  0.77  0.77  slope -0.0043 rho -0.46
  q0-01/q3-00   0.80  0.81  0.82  0.83  0.85  0.83  0.83  0.77  slope -0.0001 rho +0.20
  q0-01/q3-01   0.82  0.83  0.74  0.71  0.76  0.73  0.82  0.82  slope -0.0007 rho -0.12
  q1-00/q2-00   0.56  0.74  0.76  0.76     -     -     -  0.80  slope +0.0239 rho +0.97
  q1-00/q2-01   0.56  0.55  0.77  0.85     -     -     -  0.81  slope +0.0375 rho +0.80
  q1-00/q3-00   0.78  0.78  0.74  0.68     -     -     -  0.70  slope -0.0133 rho -0.87
  q1-00/q3-01   0.78  0.78  0.76  0.83     -     -     -  0.71  slope -0.0093 rho -0.36
  q1-01/q2-00   0.70  0.77  0.74  0.73  0.80     -     -     -  slope +0.0154 rho +0.60
  q1-01/q2-01   0.68  0.74  0.74  0.65     -     -     -     -  slope -0.0095 rho -0.32
  q1-01/q3-00   0.78  0.81  0.81  0.81  0.87     -     -     -  slope +0.0172 rho +0.89
  q1-01/q3-01   0.78  0.82  0.78  0.70  0.81     -     -     -  slope -0.0072 rho -0.10
  q2-00/q3-00   0.55  0.70  0.62  0.53  0.55  0.76     -  0.83  slope +0.0314 rho +0.50
  q2-00/q3-01   0.53  0.70  0.62  0.68  0.68  0.68     -  0.85  slope +0.0333 rho +0.59
  q2-01/q3-00   0.70  0.68  0.74  0.68     -     -  0.85  0.73  slope +0.0133 rho +0.43
  q2-01/q3-01   0.71  0.74  0.76  0.73     -     -  0.82  0.86  slope +0.0192 rho +0.83
  min over 24 cross pairs  0.53  0.55  0.62  0.53  0.55  0.68  0.77  0.70  slope +0.0302 rho +0.80
  median over cross pairs  0.77  0.78  0.76  0.78  0.80  0.77  0.82  0.81  slope +0.0060 rho +0.63
  per-pair slopes: median +0.0077, 9 of 24 negative
  same-start pairs, per-window minimum distance (time-aligned windows)
  q0-00/q0-01   0.00  0.63  0.60  0.71  0.70  0.68  0.70  0.71
  q1-00/q1-01   0.00  0.53  0.73  0.67     -     -     -     -
  q2-00/q2-01   0.00  0.53  0.60  0.55     -     -     -  0.85
  q3-00/q3-01   0.00  0.19  0.07  0.56  0.60  0.74  0.40  0.74
  cumulative minimum (all states up to window end) vs time-shuffled control, min over cross pairs
  actual    0.53  0.53  0.38  0.38  0.38  0.38  0.38  0.38
  shuffled  0.42  0.40  0.39  0.39  0.38  0.38  0.38  0.38
  mean (actual - shuffled) over cross pairs +0.053 +0.047 +0.030 +0.006 +0.003 +0.004 +0.003 +0.000  (> 0: later states closer than earlier ones = approach)
  overall min cross-seed distance 0.377; per cross pair min: median 0.675
  overall min same-start (any times) q0-00/q0-01 0.000, q1-00/q1-01 0.000, q2-00/q2-01 0.000, q3-00/q3-01 0.000

(c) shared v3 nodes vs the null (N_eff = 1.3e5)
  up to t = 3600 s (missing sigs 0); distinct v3 per chain {'q0-00': 879, 'q0-01': 573, 'q1-00': 912, 'q1-01': 149, 'q2-00': 804, 'q2-01': 898, 'q3-00': 2107, 'q3-01': 2833}
    cross: P = 26,639,798, expected 204.92 (95 % [176.9, 233.0]), M = 0 pair incidences / 0 nodes; per pair {}
    same: P = 7,321,527, expected 56.32 (95 % [41.6, 71.0]), M = 192 pair incidences / 192 nodes; per pair {'q0-00/q0-01': 0, 'q1-00/q1-01': 4, 'q2-00/q2-01': 55, 'q3-00/q3-01': 133}
    shared exact-state ids: cross 0, same-start 5
  up to t = 7077 s (missing sigs 0); distinct v3 per chain {'q0-00': 1831, 'q0-01': 1160, 'q1-00': 1040, 'q1-01': 165, 'q2-00': 1330, 'q2-01': 906, 'q3-00': 2430, 'q3-01': 5219}
    cross: P = 62,184,779, expected 478.34 (95 % [435.5, 521.2]), M = 0 pair incidences / 0 nodes; per pair {}
    same: P = 16,168,633, expected 124.37 (95 % [102.5, 146.2]), M = 277 pair incidences / 277 nodes; per pair {'q0-00/q0-01': 0, 'q1-00/q1-01': 4, 'q2-00/q2-01': 55, 'q3-00/q3-01': 218}
    shared exact-state ids: cross 0, same-start 5

same-start shared v3 nodes by 15-min window in which the node became shared (incl. start node)
  q0-00/q0-01      1     0     0     0     0     0     0     0
  q1-00/q1-01      1     4     0     0     0     0     0     0
  q2-00/q2-01     56     0     0     0     0     0     0     0
  q3-00/q3-01     85     7    42     0     0     0    46    39

calibration (added at interim): helper distance quantiles [min, p10, med, p90, max]
  same v3 node, two same-start chains (n = 281): [0.0, 0.069, 0.133, 0.194, 0.222]
  consecutive entries of one chain (n = 2474): [0.0, 0.102, 0.194, 0.25, 0.507]

(d) exact tests (pes_lib.compress, 60 s cap): {"shared_same": {"yes": 69, "timeout": 73}, "hop": {"yes": 99, "no": 1}, "hop_v3_changed": {"False": 57, "True": 43}, "hop_v3_changed_and_yes": {"False": 57, "True": 42}, "hop_v3_changed_and_no": {"True": 1}}
  hop sample: worker q1-00, t 601-695 s, 100 hops; departure==entry exact state 12; median |xv ^ entry| 6
  plateau sizes met: [(2187, '[3, 3, 3, 3, 3, 3, 3]'), (8019, '[33, 3, 3, 3, 3, 3]'), (54675, '[15, 15, 3, 3, 3, 3, 3]'), (105705, '[87, 15, 3, 3, 3, 3]'), (120285, '[33, 15, 3, 3, 3, 3, 3]')]
```

## Appendix: the pre-registered design (DESIGN.md, verbatim)

### exp2 design (pre-registered 2026-11-08 ~03:33 UTC, written before launch)

Question left open by exp1: cross-seed chains shared 0 v3 nodes in 1 h against 23.7 expected under
independent wandering on N_eff = 1.3e5 nodes; same-start pairs re-met all hour. Are the seed
regions DISCONNECTED or merely FAR APART, and do same-start chains drift apart over time?

#### Run

* Engine: the translog copy `translog/xorflux-translog/xorflux` (v8 in the repo untouched), plus
  the exp2 change `translog.departure` (`patch_departure.py`, `departure.diff`, default off):
  on every accepted exit from <= 88 gates the step row also carries `xid`/`xv`, the identity and
  sorted values of the 88 state left, computed from the proposal journal's net changes
  (before = after - added + removed). Smoke (60 s, 2 workers, `runs-smoke/`): 117 of 117 exits
  carry an 88-value `xv`; median |xv ^ entry state| = 10 (the neutral walk moved), median
  |xv ^ 89 state| = 3.
* `E2.toml` (from `make_toml.py`): exp1 / hunt D0 settings (v8 defaults, uncapped MixColumns,
  sharing off, `restart.enabled = false`, translog band 89 / id 88 / rotate 8 / values entry /
  values_gates 89) + `translog.departure = true`. 8 workers = 4 groups q0..q3 x 2, each group
  started on one hunt-D 88 record not used in exp1 (`seeds.json`, `pick_seeds.py`: roots and v3
  signatures distinct from exp1's and each other, four different (arm, worker) slots):
  q0 D4/free-00 anneal3#1935188101 d6, q1 DN/free-01 naive#4079938347 d5,
  q2 D0/free-02 naive#1611000713 d6, q3 D4/free-03 paar#2407742785 d6.
  Pairwise Jaccard distance of the four seeds (all 88 values, unrotated): 0.63-0.72.
* Duration: 2 h if launched by 03:38 UTC, else shortened so it ends by ~05:40 UTC (recorded in
  REPORT). `nice -n 8`, detached (`run.sh`, `driver.log`, `DONE`). No sampler (optional; the
  thread goes to the online tracker). One light analysis process (`track.py`, nice 8) runs
  alongside: it tails the eight logs, computes v3 signatures of new entry identities and writes
  5-minute snapshots.

#### Definitions

* State of a chain at time t: its most recent known 88 state = the later of the last entry row's
  `v` and the last departure row's `xv` at or before t (the chain may currently be at 89/90; its
  last 88 state is what is compared).
* Distance d(A, B) between two 88 states: Jaccard distance of the HELPER sets (the 88 values minus
  the 32 target rows, i.e. 56 helpers each), minimised over the 4 byte rotations of B (the
  MixColumns symmetry used for identities). d = 0 iff same state mod rotation.
* v3 node: `plateau_sig.sig_of` signature (exp1's node; splits exact plateaus, exp1 Q2).
* Visited set of a chain: all its entry states (`v`) and departure states (`xv`). For the
  cross-seed minimum distance the visited set is thinned to one state per 5 s of campaign clock
  per chain (first state in each 5 s bin), plus every snapshot state; exact computation on the
  thinned sets with sparse products.

#### Pre-registered measurements

(a) Same-start drift: for each pair q_i-00/q_i-01, d(current_a(t), current_b(t)) at t = 5, 10,
    ..., 120 min. Read: grows (monotone up), saturates (flat after some time at level L_i), or
    keeps returning to 0 (d = 0 or a shared v3 node at later snapshots).
(b) Wander: for each chain, d(current(t), start seed) at the same ticks; the maximum and the
    level at 1 h and 2 h.
(c) Cross-seed: shared v3 nodes between chains of different groups at 1 h and at the end, against
    the null M_exp = P / 1.3e5, P = sum over the 24 cross-seed chain pairs of
    (distinct v3 nodes of i) x (distinct v3 nodes of j) up to that time (Poisson 95 %).
    Same for the 4 same-start pairs (excluding the start node). And the minimum cross-seed
    distance: per 15-min window w (both chains' states in w) and cumulative (all states up to t),
    min over the 24 cross pairs and per pair; also the current-state cross distance at each tick.
(d) Exact plateau identity (`pes_lib.compress`, ~/xs-campaigns/2026-11-05-exit/pes/pes_lib.py,
    60 s per-call timeout, 30 min total budget, as exp1): for every shared v3 node (cross-seed
    first, then same-start), is the second chain's state a member of the first's exact plateau;
    and a sample of 100 consecutive (departure state xv, next entry state) hops of one chain
    (exact per-hop test now possible): is the next entry in the exact plateau of the departure
    state? Reported as yes / no / timeout counts.

#### Predictions (registered)

* DISCONNECTED predicts: the cross-seed minimum distance stays bounded away from 0 (per-window
  minimum has no downward trend and stays above the same-start saturation level), and the
  same-start distance saturates at a level L below the cross-seed distance.
* FAR APART predicts: the cross-seed minimum distance shrinks over time (per-window minimum trends
  down; cumulative minimum falls faster than sampling more states alone would give, judged against
  the same statistic computed on time-shuffled windows; ultimately shared nodes appear).
* Decision rule: trend = slope of the per-window cross-seed minimum (over the 8 windows, min over
  the 24 pairs, and the median over pairs of each pair's per-window minimum) by least squares and
  Spearman rho. "Shrinks" = median-pair slope < -0.01 per 15 min with rho < -0.5 or any
  cross-seed shared v3 node / exact meeting; "bounded" = no such trend and min cross-seed
  distance > same-start saturation level + 0.05.
* Caveat registered in advance: "bounded" over 2 h does not prove disconnection (far-apart regions
  with slow mixing look the same); it can only be read as "no approach at the 2 h scale". A
  meeting or a clear downward trend falsifies DISCONNECTED; nothing in 2 h can prove it.
