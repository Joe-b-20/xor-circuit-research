#!/usr/bin/env python3
"""Writes exp1/REPORT.md from analysis.json (tables) plus the written-up answers."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tables as T  # noqa: E402

E = T.E
A = T.A

TEXT = f"""# exp1: one hour, 12 MixColumns workers with the transition log, paired with the 30 s sampler

Pre-registered in `translog/REPORT.md` ("Proposed experiment"); run exactly as registered.
Run 00:41:19-01:39:18 UTC 2026-11-08 (campaign clock t = 0..3600 s per worker), `exp1/E1.toml`:
hunt D0 settings (v8 defaults, uncapped MixColumns, sharing off) + `translog` on (band 89, id 88,
rotate 8, values entry, values_gates 89) + `restart.enabled = false`; six 2-worker groups p0..p5,
each pair started on one of six hunt-D0 88 records with distinct v3 signatures and distinct
roots (`seeds.json`); `nice -n 8`; `hunt/sampler.py` at 30 s alongside (`samples/samples.jsonl`,
1,139 records). Machine load 24-26 on 20 cores throughout (the catalogue's 6 workers and
solver children stayed). All 12 workers stopped cleanly at t = 3600 s on their first chain,
4.50-5.43 M steps each (1,251-1,509 steps/s), worker best 88 everywhere (p0-00 improved its
depth to 88@5); **no state below 88 in any log** (24,950 entries into 88, 0 rows below).
Logs: `runs/E1/workers/*/translog.jsonl`, 1.1-8.5 MB each, 70 MB total.

Analysis: `analyze_exp1.py` (one process, nice 8; 01:40:39-02:12:20 UTC) -> `analysis.json`,
`analysis.out`, `exact.jsonl`; v3 signatures from `sigcache.py` (24,001 states cached during the
run, rest computed inline); tables by `tables.py`; this file by `make_report_exp1.py`.
Exact cataloguing (`pes_lib.compress`, 60 s hard cap per call, 30 min total): 1,860 s used,
**14 of 144 cross-worker v3 coincidences** (5 resolved exactly, 9 timed out) and **42 of 24,427
sub-2 s hops** (40 compressed, 2 timed out) were covered -- see Q2 for what that bought.

## Q1. Per-worker entries, excursions, stays [measured]

{T.q1_table()}

Pooled: **24,950 entries into 88 in 12 worker-hours** (per worker 135-3,855; median 2,371 per
hour), 23,495 distinct exact-state identities (94 %); excursions 24,938, **median 24 steps /
0.017 s**, **99.79 % shorter than 30 s, 97.95 % shorter than 2 s**; the longest excursion was
2,965 s (p4-01, which spent 84 % of its hour at 90 gates). 88 stays median 0.43-0.53 s. The time
at 88 varies from 3 % (p5-01, 68 % at 89) to 71 % (p1-00): the same engine on different 88
seeds behaves very differently, see Q2. Exact-state recurrences exist (1,130 entries on
re-entered identities, concentrated in p2-00, p3-01, p5-00 whose plateaus are small, see Q2);
they confirm the walk does come back to exact states on small plateaus.

## Q2. Plateau identity [measured at v3 level; exact where catalogued]

v3 signature per entry (`hunt/sig.py` logic; constant on an exact product plateau only, an
upper bound on exact plateaus):

{T.q2_table()}

Pooled: 24,950 entries carry **3,300 distinct v3 signatures across all workers**; 12,184
consecutive-entry runs ("visits"); per worker **16-2,816 visits per hour (median 962) and
7-2,214 distinct signatures per hour (median 127)**. Two regimes by seed, not by engine: p0-01,
p1-00, p1-01, p2-00, p5-00 hop through hundreds to thousands of signatures with one entry per
visit, while p2-01, p3-00, p3-01, p4-01 sit on 2-25 signatures with 18-139 entries per visit
(large plateaus; their long 89 excursions, median 0.9-2.3 s, are also different). 0 of the
24,950 entry states has a remove1 down-exit in its fan.

Exact identity (compress), what the 30 min bought:
* (b) **All 144 v3 coincidences are within same-start pairs; 0 are between groups** (Q3). The 5
  resolved ones are exact meetings (the second worker's state is a member of the first's exact
  plateau; products of 3,645-120,285 states, radices [45,3,3,3,3], [33,15,3^5], ...); 9 timed out
  at 60 s (larger plateaus). No exact "different" among resolved coincidences.
* (a) Sub-2 s hops: 40 compressed. The planned exit-state reconstruction FAILED by design: a
  trimmed 89-gate state has no realizable 88-subset (every value is live), so the 88 exit state
  is not recoverable from the logged 89 values (`values_gates = 89` does not do what the design
  assumed; the engine would have to log the 88 key at departure -- noted for the instrument).
  What was tested instead, exactly: **is the entry state of the stay BEFORE the excursion a
  member of the exact plateau of the entry state AFTER it? 39 of 40 yes, 1 no** (p0-00, a
  0.63 s excursion). Of the 39, **15 had a different v3 signature** before and after: the
  v3 signature splits exact plateaus (as `translog/within_stay.py` and `estimate/sigcheck.py`
  found). So a 20 ms 88->89->88 hop is, in 39 of 40 tested cases, a plateau-internal move done
  in two steps, and the v3 "hops" and "visits" above over-count plateau changes by the split
  factor. Exact plateaus met in the sample: 2,187 (3^7), 6,561 (3^8), 3,645, 10,206, 15,309,
  24,057, 72,171 ([99,3^6]), 105,705, 889,380 states.

Consequence for F11: the graph's nodes (v3) are finer than exact plateaus and much finer than
the walk's neutral components; "~44 hops per chain-hour" measured ~2 % of the entries and the
entries themselves mostly do not change the exact plateau. The true number of distinct exact
plateaus per chain-hour is between the exact-state picture (thousands of states) and the
"small region" picture of Q3; this run bounds it above by 7-2,214 v3 signatures per hour per
worker and shows that even the v3 count is an over-estimate of plateau changes.

## Q3. Connectivity: P and M against the R2 null model (N_eff = 1.3e5) [measured at v3 level]

{T.q3_table()}

Same-start pairs (positive control):

{T.same_start_table()}

Reading, pre-registered decision rule applied:
* **Cross pairs (different seeds): M = 0 shared v3 nodes among 60 pairs where independent
  wandering on 1.3e5 nodes predicts 23.7 (95 % [14, 33]) -> "below: local trails".** With P =
  3.09e6 and zero meetings, independent wandering would need N_eff >= 1e6 (Poisson, 95 %).
* **Same-start pairs: 138 shared nodes (excluding the start node) against 5.2 expected (95 %
  [0.7, 9.7]) -> far above.** The two hopping pairs (p0, p1) share 65 and 59 signatures with 64
  and 57 re-meetings after both had left the start; p5 shares 12 (11 re-meetings); the three
  pairs on large plateaus share 0-1 because they have 2-33 nodes in total. Under the null a
  pair's sharing rate gives N_eff ~ P_pair / M_pair ~ 5e3: a chain's hour-long trail stays in a
  region of a few thousand v3 nodes around its start.
* Answer to the connectivity question as the walk sees it: **trails are local**. Chains from
  the same 88 state keep meeting for the whole hour; chains from different 88 states never meet
  in an hour (0 of 3.1 M node pairs), where F11/R2's "one pool of ~1.3e5 nodes sparsely
  wandered" predicted ~24 meetings. The 8 meetings among 146 chains in hunt A-C are therefore
  not a sample of one pool; 17 of those 40 catalogued chains shared first roots (R2), and the
  present data say shared ancestry is what produces meetings.
* Granularity caveat: v3 splits exact plateaus (Q2), so two chains on one exact plateau can show
  different v3 nodes; that biases M downward for cross pairs. It cannot explain the contrast:
  same-start pairs at the same granularity produce 138 meetings, and N_eff = 1.3e5 was itself
  derived from v3 nodes. An exact-identity version of M needs the catalogue of the 3,300
  signatures (~3,300 x compress, several hours), not done here.

Top cross pairs (all zero): {json.dumps(A["Q3"]["cross_pair_detail"][:4])}

## Q4. Sampler calibration [measured]

{T.q4_table()}

Pooled: the 30 s sampler recorded 557 distinct 88 states and 545 "hops" (consecutive distinct
88 samples) in 12 worker-hours, **416 of them (76 %) with no 89 sample in between (F11's 68 %
reproduced)**; it saw 306 of the 3,300 v3 signatures (9 %) and 4 cross-worker shared nodes (all
same-start; log: 144). Correction factors from this hour: **log entries / sampler hops = 46x,
log v3 visits / sampler hops = 22x, distinct v3 in the log / distinct v3 sampled = 11x**; per
worker the sampler's hops/h (1-93, median ~55) say nothing about the regime (p3-01 on 25
signatures gave 76 hops/h, p0-00 on 240 gave 39). The sampler's "no 89 sample" fraction is a
property of the 30 s period against 0.02 s excursions, not of the plateau structure. Every
F11/F14 rate built on samples (hops/h, visits/h, meetings) should be read as a ~2-5 % sample
of the trail with the biases above.

## What this settles and what it does not

* Settled: the walk on the 88 level is a dense, local, two-step shuffle: ~25 k entries into 88
  per 12 worker-hours, 98 % of excursions under 2 s, almost all returning to the same exact
  plateau; a chain's hour stays in a seed-dependent region (same-seed pairs meet 138 times,
  different-seed pairs 0 times against 24 expected under the independent-wandering null). No
  down-exit anywhere (0 of 24,950 entry states, 0 rows below 88).
* Not settled: the exact-plateau count per chain-hour (needs the exact catalogue of the 3,300
  signatures, or a cheaper signature that is constant on exact plateaus); whether the regions
  of different seeds are disconnected or merely far apart at the hour scale (longer runs, or
  the same design with 2-3 h); the exit-state logging for an exact per-hop test (log the 88 key
  at departure in the engine; the 89 values do not determine it).

## Files

`E1.toml`, `seeds.json`, `pick_seeds.py`, `make_toml.py`, `run.sh`, `driver.log`, `E1.run.log`,
`runs/E1/` (12 worker dirs with `translog.jsonl`), `samples/samples.jsonl`, `sigcache.py` +
`sigcache.json`, `analyze_exp1.py` (+ `fix_analyze*.py`), `analysis.json`, `analysis.out`,
`exact.jsonl`, `tables.py`, `debug_cands.py` (the exit-subset failure), `status.sh`.
"""

open(os.path.join(E, "REPORT.md"), "w").write(TEXT)
print("exp1/REPORT.md written", len(TEXT))
