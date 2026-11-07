# Sprint 2026-11-07: living checkpoint

Owner: autonomous research sprint (Claude), started 2026-11-07 03:00 UTC, hard stop ~2026-11-08
06:00 UTC. Branch `sprint-2026-11-07-linear-maps`. Raw data: `~/xs-campaigns/2026-11-07-sprint/`
(agent brief `BRIEF.md` there). Findings are collected in [FINDINGS.md](FINDINGS.md) as they
are established; this file is the state of play. Evidence tags: [proved] [checked] [measured]
[cited] [guess].

## 1. State of code and experiments

- Baseline search: repo v8 (`search/xorflux`), unchanged. Prototypes v9a-f, v10 live outside the
  repo in `~/xs-campaigns/v9-proto`, `v10-proto` (read-only this sprint unless a change is kept).
- Machine: 20 threads, 31 GB. No other jobs were running at the start (the user stopped everything
  at 02:19 UTC).
- **Hunt A/B** (launched 03:16 UTC, 8 h, repo v8, AES MixColumns uncapped, fresh roots only, no
  sharing, 6 + 6 workers): `hunt/runs/A` = v8 defaults; `hunt/runs/B` = stall 300 s and
  incumbent_factor 1 (restart sooner once at the bottom). Chain states of at most 89 gates are
  sampled every 30 s by `hunt/sampler.py` into `hunt/samples.jsonl`; `hunt/descents.py` gives
  the descent statistics; `hunt/plateaus.py` identifies the 88 plateaus reached (PES compression,
  modulo byte rotation) and writes `hunt/plateaus.json`, flagging any remove1 down-exit.
  Purpose: (a) the discovery curve of distinct 88 plateaus against worker-hours (does the set of
  88 plateaus saturate?), (b) B's hypothesis that time at a sealed 88 plateau is wasted, (c) an
  87 lottery with every descent.
- **Agents** (started 03:35 UTC): `crossmap/` (map properties vs search outcomes over the 59 maps,
  with a falsifiable ranking of maps for further gain), `bench/` (benchmark of small maps with
  exact optima from SAT, plus `run_bench.py` harness for engine variants), `lit/` (literature:
  best known MixColumns counts, bounds, methods, exact-optimality results).

## 2. What was already known at the start (inherited; see the sources before trusting)

- A circuit is exactly its value set; plateaus (remove1-neutral closures) are exact Cartesian
  products of small independent factors: MC 88@5 = 3^7, MC 89@4 = 3^4, InvMC 118@5 = 5·5·2·2·2
  [checked, 2026-11-05-views/plateau, 2026-11-05-exit]. A 3-way factor is a 3-input XOR tree
  whose intermediate is unshared [guess, to be checked this sprint].
- remove1 never leaves an 88 (or 118) plateau downward [checked]. +1 exits from 49 MC 88 plateaus
  go home or join other 88 plateaus at ceiling 89 (groups of 16/16/7/2); no 87 from +1 or partial
  +2/lns passes (PES mc24, ~19 h) [checked/measured].
- MC 89@4 is one level-1 set (one family up to rotation); every 90@4 ever visited sits on a
  different level-1 set; one pair swapped costs ~+3 [measured]. InvMC 118@5 has 23 level-1 sets.
- Waits are time in dead rooms; drops are big moves landing in rich rooms; no local predictor of a
  productive state was found among ~20 candidates; copying walkers onto the newest best is the
  strongest lever on InvMC descents [measured, 2026-11-03-waits].
- Implementation: no-op remove1 calls take ~35 % of proposal CPU; depth.repair is a no-op at the
  minimum depth; star-memory blocking 67-92 % [measured, v10-proto].
- More workers than threads add no compute [measured, 2026-11-06-layout].
- Compute history: >10,000 core-hours on MixColumns since June; no 87. Lower bound 75 [proof in
  repo, not peer reviewed].

## 3. New findings this sprint (summary; details in FINDINGS.md)

- 03:40 UTC, hunt first 25 min [measured, descents.py]: from fresh roots, uncapped, v8 reaches
  <= 89 in every chain within 10-162 s and 88 in 4 of 12 chains within 50-216 s. This is far
  faster than the July figure (every 88 within 3,855 s of its root, median 2,234 s): descending
  to 88 is cheap; the whole difficulty is below 88.

- 03:30 UTC [checked, `hunt/factors.py`, `hunt/pes_plateaus_check.py`]: every 3-way plateau
  factor is the pairing choice of an unshared 3-input XOR tree (424/424 across 52 known 88
  plateaus): walking an 88 plateau re-spells the same circuit. The 52 plateaus use only 303
  helper values modulo rotation (F2).
- 03:30 UTC [cited, lit agent]: 88 is published (Jean, ePrint 2026/1481, July 2026); nothing
  below 88 anywhere. github.com/kste/mixcolumns_xor: 18,938 88-XOR circuits and an unreviewed
  "88 barrier" argument with scoped SAT refutations of 87; agent `kste/` is comparing their corpus
  and scopes with our plateaus (F3).

- 05:30-06:00 UTC: kste corpus = 49 plateaus, no overlap with our region, 87 refutations
  scoped (F3); hunt at 2 h: B 2.4x arrivals at 88 per worker-hour (F6) but A finds at least as
  many distinct plateaus because chains migrate between 88 plateaus through 89 (F5 update);
  76 new plateaus, 0 landings on the 52 known ones, vocabulary 303 -> 643 (F5). Bench agent:
  69 proved-optimum maps, v8 solves all; the reliability instrument is circulant(2,3,1,1) over
  GF(16) (14/20 in 120 s); engine-variant A/B delegated to it (starts 06:20).

- 08:30-13:05 UTC: X1 (F7): 8x8-matrix maps gain several gates per worker-hour at NIST's depth
  from NIST seeds (grostl 364@11, klsw17-inv 327@12); 4x4 maps do not. Bench (F8): only
  depth_window=none has an established effect (0.46x iterations on small-scale-aes). Hunt C
  (depth_window none on MC): 88 % of chains reach 88, 1.94 arrivals/worker-h (A 1.51), chains
  land on huge coupled products that the plateau instrument cannot compress in time, so the
  "more distinct plateaus" prediction stays untested. pt1/pt2 (F9): crossmap's numeric rule
  scored 1 hit, 1 beaten, 3 over-predictions; the surviving predictor is matrix size. kste1
  PES on kste's 49 plateaus: 8 plateaus' +1 passes complete, 56 joins, 0 lower states at
  4.6 h. Catalogue: 479 usable states -> <= 225 new 88 plateaus (giants double-counted),
  3 repeats (2 across arms) on the largest plateaus, none on the 52 pre-sprint ones (which
  sit at depth 5-7; the hunt's mostly at 7-10). See FINDINGS R for the review's corrections.
- 13:30 UTC: adversarial review (`review/REPORT.txt`) corrected F1 counts, F5 "zero
  overlap" (3 repeats; catalogue covers ~18 worker-hours, not 60), F6 (2.1x, not 2.4x), F8
  (hunt C vs A inside noise; bench effect is success-rate on 2 of 3 maps, speed on 1), F9
  (8x8 generalisation is 4 of 5). All recorded in FINDINGS R; sig.py relaunched.
- 15:05-15:15 UTC: sweep (F10): 10 of 12 maps over 8x8 matrices gained gates at NIST's depth
  in one worker-hour each (klsw17-m-8x8-gf256 347@6 -> 321@10, skop15-8x8-gf256-inv 331 ->
  322@13, fox-mu8 505 -> 500@11, whirlpool-maelstrom 394 -> 391@9, bkl16 442@10 -> 439@9);
  16 of 19 8x8-map trials this sprint gained gates vs 1 of 6 on 4x4 maps. Harvested: 44
  circuits added, 37 removed, 208 circuits (commits d281a78, 5edcd1a; harvest bug fixed).
  Hunt D started 15:06 (D0/D4/DN, same first roots), ends ~04:06 UTC 11-08.
- 15:50 UTC, graph agent (F11): the 88 level as sampled is 146 disjoint chain trails (139
  components, 8 of 1,454 nodes shared by two chains), 0 down-exits in 1,869 states, hops
  change ~30 % of helpers, ~44 plateau changes per chain-hour is a floor (68 % of hops have no
  89 sample; the walk lives on the 88+89 band).

## 4. Rejected explanations and failed approaches (this sprint)

- "Time at a sealed 88 plateau is pure repeated work" (my reading of F2): wrong as a statement
  about the chain. remove1 re-spells, but the chain leaves the plateau through +1 states every
  1-2 minutes and lands on new 88 plateaus (F5 update). Restarting sooner (F6) buys arrivals,
  not distinct cores.
- "The 88 level is a small set of families" (implicit in earlier work that kept finding the
  same 49-63 plateaus from the same seeds): wrong; fresh descents never land on known plateaus.
- "Zero overlap, zero repeats between independent descents" (my F5/F8 wording): overstated;
  3 repeats exist, on the largest plateaus, as a basin-size argument predicts (review, FINDINGS R).
- "depth_window=none halves the iterations on all three analogues": on two of them it is a
  success-rate effect (seeds the default never solves); per-seed speed-up only on mc_gf16.
- kste's "88-XOR barrier": not a proof; its floors are corpus minima and its SAT scopes do not
  contain our circuits (F3).

## 5. Unresolved questions (ranked by how much they would change what we do)

1. Does the set of MC 88 plateaus saturate under repeated independent descents? After ~225
   catalogued plateaus from ~18 worker-hours with 3 repeats (all on the largest plateaus) the
   answer is "not at this scale": the 88 level is far larger than any sample we can take, so an 87 reachable from some
   88 plateau cannot be excluded by sampling. Next: a cheap plateau identity (core hash) to
   measure the rate from all 1,900 sampled states, and the C-vs-A distinct-plateau question.
2. What is the barrier height from the 88 level to any 87, if one exists? (PES: > +1 from 49
   plateaus; +2 partial.)
3. Which map properties predict the search's gap to the optimum (bench + crossmap).
4. Is the "3-way factor = unshared 3-input tree" reading of the plateau products right, and does
   the number of factors predict anything (exits, descents)?

## 6. Active jobs and how to inspect them

| Job | Cores | Started (UTC) | Ends | Inspect |
|---|---|---|---|---|
| hunt A | 6 | 03:16 | stopped 06:16 | `hunt/runs/A`; `hunt/descents.py hunt/runs` |
| hunt B | 6 | 03:16 | stopped ~08:25 by predtest/driver.sh | `hunt/runs/B` |
| sampler + plateau catalogue | ~1 | 03:25 | with hunt | `hunt/samples.jsonl`, `hunt/plateaus.json`, `hunt/plateaus.log`, `hunt/chains.log` |
| X1 fresh vs NIST (x1a, x1b) | 8 | 06:16 | ~08:25 | `x1/runs/x1a`, `x1/runs/x1b`, `x1/driver.log` |
| bench engine-variant A/B (agent) | <=6 | 06:20 | ~09:30 | `bench/REPORT.txt` section "Engine variants" |
| kste1: PES +1 pass on 22 kste 3-way plateaus (+#0) | 8 | ~08:25 | ~00:25 (11-08) | `pes-kste/runs/kste1/status.txt`, `FOUND_*`, `records/`; stop: `pes-kste/pes/stop2.sh kste1` |
| predtest pt1, pt2 | 6, 8 | 08:28, 10:39 | done 12:52 | `predtest/runs/pt{1,2}`, `predtest/driver.log` |
| hunt C (A with depth_window none) | 6 | 08:30 | done 11:30 | `hunt/runs/C`; sampler `hunt/samplesC/samples.jsonl`; catalogue via `hunt/plateaus.py .` then `hunt/chains_plateaus.py .` |
| bench replication: default vs depth_window none, same window (agent) | 6 | 11:48 | done 13:12 | `bench/REPORT.txt` section 12 |
| sweep sw1, sw2 (12 maps over 8x8 matrices, 1 worker-hour each at NIST's depth) | 6 | 12:52 | done 15:05, harvested | `sweep/runs/sw{1,2}`, `sweep/driver.log`; FINDINGS F10 |
| agents crossmap, lit, kste, pes-kste, bench | - | - | done | `*/REPORT.txt` |
| agents (15:30-15:50 start, ~1-1.5 h each, 1 thread): estimate (size-weighted capture-recapture count of 88 plateaus), graph (88-plateau transition graph from chain hops), sat (scoped SAT search for an 87 around our 88 cores) | 1-3 | 15:30 | ~17:30 | `estimate/REPORT.txt`, `graph/REPORT.txt` (done 15:50, F11), `sat/REPORT.txt` (+ `sat/found/` if anything) |
| hunt D: D0 (default), D4 (depth_window 4), DN (none), 4 workers each, MC uncapped, fresh roots | 12 | 15:06 | ~04:06 (11-08) | `hunt/runsD/{D0,D4,DN}`, `hunt/driverD.log`, sampler `hunt/samplesD/samples.jsonl`; identity: `hunt/sig.py` (cheap, validated against `plateaus.json`); descents: `hunt/descents.py hunt/runsD` |
| sig.py / sig2.py cheap identity over all 1,869 hunt 88 states | 1 | 13:32 | done 13:40 | `hunt/sig2.log`, `hunt/sigs2.json` (FINDINGS F8 addendum) |
| hunt E: cap-5 MixColumns, E0 default vs EN depth_window none, 4+4 workers, 2.5 h (review point "depth") | 8 | after kste1 ends (~01:00 11-08) | ~03:40 | `hunt/runsE/{E0,EN}`, `hunt/driverE.log`, sampler `hunt/samplesE/samples.jsonl`; `hunt/descents.py hunt/runsE` |

Harvest recipe (done 15:15 for x1a, x1b, pt1, pt2, sw1, sw2; repeat for hunt D/E if they produce a repo-worthy circuit, e.g. any 87): from the repo root, `python3 ~/xs-campaigns/2026-11-07-sprint/harvest_sprint.py RUN_DIR...` (dry run), `--apply`, `python3 circuits/check.py`, `python3 ~/xs-campaigns/2026-11-07-sprint/tables_update.py --write` (add the run dirs to its RUN_DIRS first; it appends run rows for runs with adds, so delete a duplicated run row), then hand-edit the README count line (keep "59 maps") and the SEARCH-TIME "Together:" paragraph, commit. `search/proposals/` is the user's untracked draft from 2026-10-31; leave it.

## 7. Next actions

1. Hunt D (15:06 -> ~04:06 UTC 11-08): check every ~2-3 h with `python3 hunt/descents.py hunt/runsD`
   (arrivals at 88 per worker-hour, depth of 88 bests, any 87) and the cheap identity on
   `hunt/samplesD/samples.jsonl` (adapt `hunt/sig2.py`: distinct v3 signatures per arm, shared
   first roots across arms give a paired comparison). Any 87: verify (`circuits/check.py` after
   `circuits/add.py`), harvest, commit at once.
2. kste1: check status every ~2 h; ends ~00:30 UTC 11-08; record the outcome in F3/F5.
3. Hunt E (~01:00-03:40 UTC): time to 90@5/89@5/88@5 per chain and arrivals per worker-hour,
   E0 vs EN; record in F8 (depth-capped case of the depth-window effect).
4. ~03:30 UTC: mid-run hunt D analysis written into FINDINGS (new F11) and UNDERSTANDING;
   ~04:10: final hunt D numbers.
5. By 05:00 UTC 11-08: final UNDERSTANDING.md, FINDINGS.md, this checkpoint (rejected
   explanations, open questions, next experiments), memory note, copy hunt D/E analysis scripts
   into `research/sprint-2026-11-07/experiments/hunt/`, commit, closing report.
