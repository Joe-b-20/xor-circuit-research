# Transition log prototype (translog) -- sprint 2026-11-07, measurement instrument for F11/R2/F14

Status: EXPERIMENTAL, built and tested outside the repo. The frozen v8 engine in
`~/xor-circuit-research/search/xorflux` is untouched (repo HEAD dda7f915, clean).

## Deliverables (all under `~/xs-campaigns/2026-11-07-sprint/translog/`)

| path | what |
|---|---|
| `translog.diff` | `diff -ruN -x __pycache__ ~/xor-circuit-research/search/xorflux xorflux-translog/xorflux` (277 lines: 1 new module, 3 small edits) |
| `xorflux-translog/xorflux/` | the modified copy (run it as `python3 xorflux-translog/xorflux run X.toml --out DIR`; `translog/circuits` is a symlink to the repo's catalogue because `core/target.py` takes the repo root two levels above the package) |
| `xorflux-translog/xorflux/engine/translog.py` | the logger (new file, knob section `translog`) |
| `patch_translog.py`, `fix2.py`, `setup.sh` | reproduce the copy from the repo: `setup.sh`, `patch_translog.py` (anchored edits of loop.py / worker.py / registry.py), `fix2.py` (the `values_gates` knob added after the test) |
| `T0.toml`, `T1.toml`, `run.sh` | the 20-minute test (T0 log off, T1 log on, concurrent, `nice -n 8`, one worker each, hunt D0 settings, plus `hunt/sampler.py` at 30 s over both) |
| `runs/T0`, `runs/T1`, `samples/samples.jsonl` | the test's run directories and the sampler's records; the log is `runs/T1/workers/free-00/translog.jsonl` (2,714 rows, 1.0 MB) |
| `analyze.py` -> `analysis.json`, `analyze.out` | state-level analysis + overhead + sampler pairing |
| `plateau_sig.py` -> `plateau_sig.out`, `runs/T1/.../translog.plateaus.json` | plateau-level view with the sprint's cheap v3 signature (hunt/sig.py logic) |
| `within_stay.py` -> `within_stay.out` | is the v3 signature constant along an 88 stay? (it is not: see caveat) |
| `bench_identity.py` | microbenchmark of the per-row cost |
| `T0w.toml`, `T1w.toml`, `run_w.sh`, `runs-w/` | a second 5-min pair with `scheduler.cost = "work"` (meant to be replayable; it was not: see overhead) |

## What the engine logs (format)

`<worker dir>/translog.jsonl`, one JSON object per line, written by the engine itself
(`engine/translog.py`, hooked in `engine/loop.py`):

```
{"k":"open","worker":"free-00","t":0.418,"w":1794096325.355,"band_gates":89,"id_gates":88,"rotate_bits":8,"values":"entry","values_gates":88,"n_inputs":32}
{"k":"chain","it":0,"t":0.451,"w":1794096325.388,"p":null,"g":88,"d":6,"m":"seed","c":1,"id":"5a2e7baf263e6d38","v":[1028,8224,...]}
{"k":"step","it":14,"t":0.6,"w":...,"p":88,"g":89,"d":8,"m":"walk.expand","c":1}
{"k":"step","it":447,"t":2.1,"w":...,"p":89,"g":88,"d":7,"m":"walk.remove1","c":1,"id":"9c1f...","v":[...]}
...
{"k":"close","t":1200.624,"w":...,"rows":2714,"entries":869,"seconds":0.555}
```

* `k`: `open` once per engine start/resume (knobs, clocks); `step`: an accepted proposal changed
  the gate count and the count before or after is <= `translog.band_gates` (89); `chain`: a chain
  began (seed/root start, restart, resume: the state was replaced wholesale, always written);
  `close` at a clean stop (row and entry counts, self-timed seconds spent in the module).
* `it` engine step counter; `t` campaign clock in seconds (the same `recorder.now()` clock that
  chain.json's `t` carries, so sampler records pair on `t`); `w` wall time; `p` gates before;
  `g` gates after; `d` depth after; `m` move name (chain rows: source); `c` engine chain number.
* Rows with `g <= translog.id_gates` (88) carry `id`: blake2b-64 of the sorted non-input values,
  minimal over rotations of the input masks by `translog.rotate_bits` (8 = byte rotation; the
  target rows are checked to be invariant at start, else rotation is disabled with an event), and
  `v`: the sorted non-input values (= chain.json's `chain_values`), by `translog.values`
  (`entry` every such row, `new` first time an identity is seen, `never`).
* `translog.values_gates` (added after the test, default = id_gates): rows with `g` up to this
  value also carry `v` without an identity. Set to 89 to keep the 89 state right after every
  exit from 88; its 88 exit state is one of its 88-subsets (for `walk.expand` exits, 86 % of
  them, exactly one value was added), so the before/after plateau question of an excursion can
  be settled exactly offline.
* Transitions below 88 are logged like any other (with identity and values); there were none.
* Writes are buffered, flushed from the engine's periodic check (every 64 steps, ~50 ms) and at
  checkpoints; closed by the worker after `recorder.close`. Hot path: one attribute compare per
  step (`g1 != tl.g`), placed after the proposal's own timing so the scheduler's per-move cost
  (`scheduler.cost = seconds`) does not see the logging. Nothing touches the RNG.
* Epoch events gain `"translog": {"rows", "entries", "seconds"}`.

Knobs (`[set]` in the campaign TOML): `translog.enabled` (false), `band_gates` (89), `id_gates`
(88), `rotate_bits` (0; use 8 for MixColumns/InvMixColumns), `values` (entry), `values_gates`
(null = id_gates), `file` (translog.jsonl). Unit tests of the copy (engine loop, worker, plan,
profiles) pass; partial test schemas without the section leave the logger off.

## Overhead

Conditions: load average 25-28 on 20 cores (the user's other campaigns), both arms `nice -n 8`,
concurrent, same 88@6 seed circuit and rng seed, 20 min. The trajectories diverge within
seconds (`scheduler.cost = seconds` charges measured time), so the arms are statistically, not
step-wise, paired.

| | T0 (off) | T1 (on) | T1/T0 |
|---|---|---|---|
| steps in 1,200 s | 1,520,547 | 1,532,481 | |
| steps / wall second | 1,266.6 | 1,276.5 | 1.008 |
| CPU seconds | 939.6 | 943.7 | |
| steps / CPU second | 1,618.4 | 1,623.8 | 1.003 |
| mean cost of walk.remove1 (us), 1.48-1.50 M proposals | 610 | 609 | |
| time spent inside the logger (self-timed, rows only) | | 0.555 s = 0.06 % of CPU | |
| log size | | 1,012,925 B (3 MB per worker-hour at values <= 88; about double with `values_gates = 89`) | |

No slowdown is resolvable: the logging arm came out 0.3-0.8 % faster, i.e. the difference is
inside the run-to-run noise of a loaded machine. The analytic cost agrees: an entry row costs
~160 us (sorted 13 + rotation-canonical identity 125 + json 21; `bench_identity.py`), an exit row
~9 us, and the test produced 2.26 rows/s, so ~0.02 % of a second plus the per-step compare.
The second pair (`runs-w/`, 5 min, `scheduler.cost = work`) was meant to give identical
trajectories and a step-exact CPU comparison; the trajectories were not identical (96,212 vs
100,529 steps, different work) so it only shows the same thing more noisily (T1 10 % faster per
CPU second). Verdict: the instrument does not distort the search at the measured transition
rate; a worker at 88 writes ~2-3 rows per second.

## The 20-minute test (T1, one uncapped MixColumns worker on the 88+89 band)

The worker started on hunt D0's record `g88-d6-0f7bfd6b155e8d61` (the incumbent stall allowance
of 2 x 900 s keeps it on one chain for 20 min; a descent from a root would reach 88 in 20 min
only about half the time at D0's 1.7 arrivals per worker-hour). One chain, no restart, no
state below 88 (0 rows), 2,713 transitions (2.26/s): 88->89 868, 89->88 868, 89->90 488,
90->89 488; nothing above 90 touched the band.

* **Entries into 88: 869** (43.4 per minute, 2,600 per hour), 868 of them by an accepted
  proposal (845 `walk.remove1`, 19 `lns.rebuild`, 2 `walk.expand`, 1 each translate/repair).
  Exits from 88: 747 `walk.expand`, 72 `lns.rebuild`, 35 `depth.repair`, 9 `structural.cores`,
  5 `structural.translate`.
* **Distinct 88 identities (exact state modulo byte rotation): 866 of 869.** Two identities
  recur: one immediate return (88->89->88 undoing itself), two returns after other states
  (after 9 entries / 10 s and after 100 entries / 75 s). Exact-state recurrence is essentially
  nil: the neutral walk inside a stay changes the state (median 7 values replaced between
  consecutive entries, Jaccard distance 0.147, q1 0.108, q3 0.167).
* **88 stays**: median 697 steps / 0.49 s (q1 0.22 s, q3 1.13 s, max 6,355 steps / 5.1 s).
  Time share: 56 % at 88, 34 % at 89, 10 % at 90. Depth at entry: 6 (118), 7 (415), 8 (335),
  9 (1).
* **89 excursions (868): median 24 steps / 0.019 s** (q1 0.007 s, q3 0.071 s, p90 0.375 s,
  mean 0.61 s, max 191,714 steps / 163 s). **99.65 % are shorter than 30 s, 97.4 % shorter than
  2 s.** 770 excursions stayed at 89, 98 reached 90. One excursion returned to the very state
  it left.
* **What a 30 s sampler sees.** Simulated ticks every 30 s (40 ticks): 97.6 % of 88 stays and
  98.5 % of excursions contain no tick. The real sampler running alongside (`hunt/sampler.py`,
  30 s, both arms) recorded 36 state changes for T1 in 20 min: 25 distinct 88 states and 11
  at 89; those 25 samples fall in 25 different stays, i.e. 2.9 % of the 869 stays, and none of
  them equals its stay's entry state (the walk had moved on). Consecutive distinct 88 samples,
  the hunt's "hop" count, give 21-24 per 20 min (63-72 per hour) against 868 real re-entries:
  the sampler undercounts 88 entries by a factor ~35 and F11's "~44 hops per chain-hour" is a
  property of the sampler, not of the walk.
* **Departure rate discrepancy.** F11 inferred "~12 departures to 89 per second [guess]" from the
  ledgers' ~24 accepted non-neutral moves per second. Measured directly: 0.72 departures from 88
  per second at 1,276 steps/s (about 1/s at D0's 1,750 steps/s) plus 0.4 89->90 per second.
  The ledger figure counts something else; the guess is off by an order of magnitude and
  F11's "~12/s" sentence should be corrected.
* **Plateau level (cheap v3 signature, `plateau_sig.py`, 33 ms per state).** The 869 entry
  states carry 366 distinct signatures (1,100 per hour); as consecutive runs, 609 plateau
  visits (1,830 per hour), entries per visit median 1 (max 153); 608 hops between distinct
  signatures with excursion median 0.02 s, 99.5 % under 30 s, and only 11 of 608 containing a
  30 s tick; 243 revisits of an earlier signature (99 signatures visited more than once, 7
  A-B-A). The sampler's 25 states give 20 signatures, 12 of them among the log's 366.
  **Caveat that matters:** `within_stay.py` compares each sampled mid-stay state with the entry
  state of the same 88 stay (same contiguous stretch at 88, connected by accepted neutral
  moves): 18 of 25 have a *different* v3 signature after 3-10 values were replaced in under
  2 s. So either the v3 signature is not constant on a plateau under the engine's full neutral
  move set (lns.rebuild and friends accepted at 88 move between remove1-closures), or the
  sprint's plateau notion (remove1 fan closure, exact products) is finer than the walk's
  neutral components. Either way the signature counts above are upper bounds and F11's graph
  nodes are finer than neutral components. The exact numbers in this log are states, stays and
  excursions; plateau identity must be settled offline with the exact catalogue (compress) on
  the logged values, which is what `values_gates = 89` was added for (entry and exit states of
  every excursion). No logged entry state has a remove1 down-exit (0 of 869, consistent with
  F11's 0 of 1,869).

## Proposed experiment: 1 hour, 12 workers, paired with the 30 s sampler

Question: how many distinct 88 plateaus does a chain visit per hour, and do chains' trails
meet when the whole trail is seen (not 3 % of it)?

Design (`hunt/D0.toml` settings = v8 defaults, uncapped MixColumns, `sharing = off`, plus
`translog.enabled = true`, `rotate_bits = 8`, `values = "entry"`, `values_gates = 89`,
`band_gates = 89`, `id_gates = 88`; `restart.enabled = false` so each worker is one persistent
chain for the hour; `duration = "1h"`, `count = 12`, `nice -n 8`; `hunt/sampler.py RUNS
samples.jsonl 30 89` alongside, exactly as in hunt D):

* Seeds: 6 distinct 88 records of hunt D (different v3 signatures, different roots, e.g. one per
  worker of D0/D4/DN), each given to TWO workers with different rng seeds (the plan cycles seeds
  over workers; list each file twice or run six 2-worker groups). The same-start pairs are the
  positive control: they start on one plateau and the log shows when (steps, seconds, entries)
  they are last on a common plateau and whether they ever re-meet; the 15 cross pairs test
  meetings between trails from different regions.
* Expected volume (from this test): ~2,600 entries, ~870 excursions and ~1,100 v3 signatures
  per worker-hour; ~6 MB of log per worker; 12 workers -> ~31,000 entry states, ~2 h of
  single-core exact catalogue work at 33 ms per v3 signature (plus compress for exact
  identity), which is parallelisable.
* Analysis, pre-registered:
  1. Per worker: entries/h, excursion distribution, stays, exact-state recurrences (`analyze.py`).
  2. Plateau identity: v3 signature on every entry state, then exact identity (compress) for
     (a) every pair of consecutive entries whose excursion was < 2 s (is a 2-step 88->89->88
     hop a plateau change or an internal move done in two steps?) using the exit 89 state and
     the next entry state, and (b) every cross-worker v3 coincidence. This fixes the plateau
     notion that F11's numbers need and gives the true visits per chain-hour.
  3. Connectivity: with complete trails, P = sum over worker pairs of (visits_i x visits_j) is
     known exactly; count M = distinct plateaus entered by two workers (same-start pairs after
     their separation point, and cross pairs separately). Decision as in F14 Q1: M inside the
     Poisson interval of P / N_eff with N_eff = 1.3e5 (R2 null model) -> one pool sparsely
     wandered; M far above -> hubs / a small connected region; M far below -> local trails.
     Same-start pairs re-meeting after separation much more often than cross pairs -> locality.
  4. Sampler calibration: run F11's graph construction on the paired samples of the same hour
     and report hops/h, meetings and "no 89 sample" fraction next to the log's truth, so every
     F11/F14 number gets a correction factor.
* Cost: 12 cores for 1 h on the shared machine (the campaign is the same as hunt D0 with
  restarts off), ~75 MB of logs, ~2-3 h of offline cataloguing.

## Caveats

* The test started on an 88 seed, in burst phase first (400 proposals), under `nice -n 8` on a
  machine with load 25-28; absolute rates (1,276 steps/s) are below D0's 1,749.
* The 20-minute run used the pre-`values_gates` build (values at <= 88 only); the knob was
  added afterwards and verified by the 75 s smoke run (`runs-smoke/`, 77 rows with id+values
  at 88, 111 rows with values at 89, tests pass); the diff is of the final code.
* `scheduler.cost = work` does not make two runs replay each other (something else in the
  stack is time dependent), so a step-exact overhead comparison was not obtained; the
  statistical one and the self-timing agree that the cost is below 0.1 %.
