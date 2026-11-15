# QUEUE review and CPU allocation for the 07:00 UTC launch (L1b, 06:00 UTC)

Scope: every entry in `~/xs-campaigns/2026-11-15-study/QUEUE.md` as of 05:55 UTC (25 entries, 604 lines).
I vetted each for unattended safety by reading its scripts, and I ranked the entries by tonight's evidence
(`TONIGHT.md`, pass 2). Labels: [C] = read in the script or counted in the logs; [H] = judgement.
Nothing was launched or edited outside strategies/L1.

## 1. Safety vetting

Columns: mem = memory cap; pin = CPU pinning; stop = what ends the job; check = automatic aes_check;
side = JSON sidecar; fix = what must be done at launch.

| entry | mem | pin | stop | check | side | fix at launch |
|---|---|---|---|---|---|---|
| COORD long5 (review5 hub) | xsrun XS_MEM | xsrun affinity; review5 `--cpus` defaults to it and refuses CPUs outside it | `--hours`; review5 kills a job after 2 x s + 120 s and handles SIGTERM | two verifiers at admission; aes_check at curation | records | flags, see 3 |
| L1 focus / base | 3G per arm | xsrun + same `--cpus` list | `--hours`, then harvest + eval | harvest.py at the end (aes_check + sidecar) | yes | stop with systemctl, then run `STEPS="harvest eval"` (the harvest is lost otherwise). Seeds come only from the long archive, so set SEEDLIST to include tonight's found/ |
| X2 goal arm | 3G, track X (slice uncapped) | xsrun + `--cpus` | `--hours`, harvest | at admission for goal hits; harvest at the end | yes | `goal_job.sh` has no exec bit; the entry already calls it with `bash`. Tested only up to 0.9 CPU-h per arm |
| T1 (screen, workers, Bdeep) | 2-3G | xsrun | `--hours` | goal hits and (v3.3) new front points, written at admission | yes (+ .check.json) | none. v3.3 harvests killed jobs (the 28/4/131/22 lesson). Run `frontcollect.py` once at the end |
| R1 overnight.sh | 2G | xsrun + `taskset -c CPU`: the CPU argument must equal the xsrun CPU | HOURS loop, stops after the running cycle | grind.py: aes_check before writing found/ | yes | uses `hub.common.metrics` (present in review5) and snapshot.py of the live long archive (race-free per R1) |
| T4 polish_job.sh | 1G | xsrun | `--seconds` 21600 | only at the END of the job | yes, only at the end | if stopped early, aes_check `run-TAG/best.circ.txt` by hand (the entry says so). Uses kernel binary long/bin/bfx-593fa798f5; it must still exist after the review5 merge |
| T3 (F loop), T3-b (low-GD) | 1G, track T | xsrun | `--hours 10` | target hits only (sidecar); other new points stay in the pool | target hits only | copy bfx-* into qlow/bin first (entry says so). The pool needs a manual aes_check sweep in the morning |
| T2 launch_t2.sh | 1G per walk | the script calls xsrun itself, one unit per CPU | `--total-s` | inside walk_q.py for goal hits | yes | run the script directly, NOT under xsrun (it launches its own units, all on track H) |
| H1 zdfs, H1-b swap2, H1-c fixk, H1-d t14 | XS_MEM 1G | xsrun | zdfs 6 h timeout; swap2, fixk and t14 have none (chunks 30-80 s, 10 min per circuit) | n/a: a hit is a candidate layer, built by hand | log only | `fixk_all.sh` has no exec bit: call it with `bash`. No runner exists for "sequential on 1 CPU": use `bash -c 'for ...; do ...; done'` |
| H2 qworker / qsemi / qall2 (incl. MAIN) | 1G / 2G / 6G | xsrun | gen13 1800 s, gen13c 3600-10800 s; rprep and rvd unbounded | rvd.py: **fixed by H2 since 03:30** (parents[2], fields aes_check, aes_check_ok); I re-read the line at 05:55 | yes | qall2 (tier 3) measured RSS 2.9 GB plus prep 2.0 GB and is not finished end to end; it needs a slice of its own (see 1.1) |
| H3 job.sh (a28, a29, c14, x1, deep) | 1G | xsrun | none (maxenums / maxstates bound the work; nv 34 windows take ~4.5 h) | yes (chainbatch / deep2 `--verify`, correct path) | yes | `job.sh` has no exec bit: call it with `bash`. The entry text says to call it directly, which fails |
| H3b sweep_job.sh | 1G | xsrun | none | yes (deep2_sweep, recursive descent only after aes_check OK) | yes | none |
| X1b queue_x1b.sh | 1G | xsrun | `--hours` | yes, into found/ | yes | the exec bit is now set (05:55). Shards share pool/ and spans files by design |
| X3b x3b_night.py | 2G | xsrun | 3600-s timeout per window; ends by itself | yes, for builds | yes | none |
| X3 small fields | inner xsfg 2G (nested scope) | `taskset -c CPU`: the CPU argument must equal the xsrun CPU | per-run timeout | n/a (not AES) | n/a | drop (see 2) |
| H4 ad3night.sh | default 4G | xsrun | HOURS loop of 30-min walks | yes (ad3found) | yes | none |
| L2 cgamma | 1G | xsrun | 4 h timeout each | n/a (candidate layer) | log | needs a sequential runner, like H1 |

### 1.1 One problem for the whole launch: track slice memory [C]
`xs-H.slice` has MemoryMax 7G for ALL H-track jobs together. So do xs-R, -E, -C, -D, -F, -G and
-main; xs-T and xs-X have no cap of their own; xs.slice has 24G. Most entries use track H. The caps
the entries name for H jobs add up to far more than 7G. Measured RSS adds up to about 3-5 GB in
the allocation below, so it fits, but one large job (H2 qall2, 3-5 GB) would push the H slice
over and the OOM killer would pick a victim among unrelated jobs. Rules for launch-0700.sh:
- give each heavy family its own track: hub E, R1 R, T1 and T3 T, X1b and X2 X, the exact searches H;
- never put H2 qall2 into a shared slice (I do not allocate it, see 2).

### 1.2 Uniform launch wrapper (recommended)
Several jobs have no time limit of their own (H3, H1-b/c/d, H2 loops). Prefix every command with
`timeout 11h45m` so all CPUs are free at ~18:50. Jobs that write results only at the end (T4, L1/X2
harvest) need their final step after the stop: run their `harvest` / aes_check lines from the
morning checklist.

## 2. Allocation of 20 CPUs, 07:00 - ~19:00 UTC (about 240 CPU-h)

Value order A >> AD >> G >> GD; goal A (27) outweighs everything else. Tonight's evidence
(TONIGHT.md):
- No method made a 27 or lowered A on any front circuit at A <= 31.
- The only new A28 structures are the X1b 9|1|2|2|14 family and H2's 9|5|14 layers, 162 new A28
  spans in all. Every exact 28 -> 27 test on them so far is negative, but only a small part of their
  windows has been tested.
- Goal B moved once (T1 `deep`). R1's AND-removal + grind route gave 3 A28 front points in about
  2 CPU-h, the best measured yield of A28 front points per CPU-h tonight (n = 3).
- The generic hub operators gave 1 front point in about 8 CPU-h of A/B arms. In the hub era the rate
  was 1.14 per CPU-h, and almost all of those points had A >= 33.

| # | job | CPUs | track | expected value [H] and why |
|---|---|---|---|---|
| 1 | H3 c14: full-operand slack-1 windows of the two 9+5+14 A28s (expensive first; pairs already done are skipped) | 3 | H | goal A. Exact and new: these windows exist only in the new families. The entry asks for ~40 CPU-h; 3 x 12 h is about 36 |
| 2 | H2 MAIN tier 1 (T1a: 200 H4 covers x 16 gamma, ~9 CPU-h; then T1b: Karatsuba covers) | 2 | H | goal A. The most distinct exact cases per CPU-h (10 s per case); a hit is a circuit directly; aes_check is now wired in |
| 3 | X3b stage-1-free window re-solve of all 9+5+14 layers, `--ov` | 2 | H | goal A. Covers every built 9+5+14 file (~60) and all windows up to k = 5; ends by itself after ~12 h on 2 CPUs |
| 4 | H1-d 14 -> 13 exact test of every 9+5+14 circuit (t14_all.sh) | 1 | H | goal A. About 10 min per circuit; 70+ circuits fill the night |
| 5 | X1b walk + new-U filter (queue_x1b.sh) | 2 | X | goal A, indirectly: the only generator of new A28 U families (the 9+5+14 family came from its first iteration). Phase 2 tonight made 0 A reductions in 46 runs, so its value is supply for the morning's exact tests, not 27s themselves |
| 6 | T1: Bdeep1 (goal-B deep recipe), screen (rest of the H2/X1b builds + hybrid joins), B1 worker | 3 | T | goal B: the only recipe that moved a box tonight (n = 1); the new-space hybrids gave 28/4/134/19 |
| 7 | R1 overnight.sh (mc1 + seq2 + grind cycles), seeds 71 and 72 | 2 | R | goals B and C: 3 A28 front points in ~2 CPU-h. It feeds on A29 join products, which the hub below supplies |
| 8 | COORD long5 on review5 with L1's settings (see 3) | 3 | E | feeder and ingest: new A29 join products for R1, a home for every found/ dir. Not expected to move a goal box (0 since 22:20 UTC on 11-14) |
| 9 | T4 polish job 1 (lowest-G A42 GD11, gate, 6 h), then job 5 (42/4/230/12) on the same CPU | 1 | H | goal G: the only circuits inside G's A/AD/GD caps. G is 145 over the cap, and the gain rate has fallen to 4-11 gates per hour |
| 10 | T3-b low-GD AD3 loop, CAP 19 | 1 | T | A35 AD3 front points (4 tonight on 2 CPUs). Not a goal; goal F stays at 2 |
| | **total** | **20** | | |

Not allocated, in the order I would add them if a CPU frees up or a job ends early:
1. H3b deep2 sweep (1 SAT in 128 windows tonight, an A29 -> A28 into an old span; 32 A28 windows UNSAT).
2. H1-b + H1-c + L2 + H1 zdfs on one CPU, sequentially (~30 CPU-h of exact [C] closures on old prefixes; no hit expected).
3. H3 a28 / a29 / x1 / deep (95 + 40 + 65 CPU-h; about 400 slack-1 windows UNSAT tonight).
4. H2 tiers 2-3. Tier 3 only alone in a slice with XS_MEM=6G (see 1.1).
5. T4 jobs 2-4.

Dropped:
- T2: 0 improvements in about 120 jobs (T2's own words: "low expected yield").
- X3 small fields: no AES output.
- H4: about 70k junk spaces tested exactly, none coverable.
- T3 F loop: T3 calls it "low expected yield".
- The L1 base twin and the X2 goal arm: X2's own estimate is that 4 CPUs x 10 h per arm can see only 2x
  differences, and tonight's arms showed 1 front point per configuration. On these 8-12 CPUs a third
  hub arm buys a comparison, not progress.

### 2.1 The new A-reducing methods against the generic hub
- **R2 aslack**: 2 admitted A reductions, both at A >= 36. 0 on A <= 35 front circuits (39 fixed-target
  jobs, 0.65 CPU-h). The A descents for goals G and F produced nothing that is not dominated. Its A/B
  was 1 vs 0 front points in 1 CPU-h per arm, which L1's noise table cannot separate (11 of 20
  same-configuration blocks give 0). R2 wrote no queue entry. Do not register it in long5. If a CPU is
  spare, use it for the goal G window only.
- **H3 deep2 windows**: 1 SAT in 128 windows. The result has an old span, so the step is a
  re-derivation of a known structure. The A28 windows were all UNSAT (32). It ranks after the
  new-family exact tests (items 1-4 of the allocation), which cover the only structures nobody had
  tested before tonight.
- **X1b walks**: they made no A reduction (0 of 46 runs from A28/A29), but they are the source of the new
  U families. 2 CPUs; their output gets tested in the morning.
- **R1 AND removal**: the one A-reducing route that produced front points, and only after a kernel
  grind on redundant join products. 2 CPUs, fed by the hub.
- **Generic hub**: 1 front point in about 8 CPU-h tonight. 3 CPUs as feeder and archive, not the
  default home of idle CPUs.

## 3. Hub long5 settings on review5 (if the coordinator keeps the COORD entry)
```
XS_MEM=3G xsrun E <3 CPUs> hub-night LOG -- python3 nonlinear/boolflux/hub/scheduler.py \
  --dir ~/xs-campaigns/2026-11-14-hub/long --hours 11.7 --seed 9 --nursery 0.5 \
  --ops pull,pull,gen_skel,gen_skel,polish,trb,join --eps 1.0 \
  --tuple-caps polish=2,pull=3,trb=1,gen_skel=2 --cap-renew box
```
with `control.json` `"ad3_share": 0.0`, plus ingest of the found/ dirs: L1/found/rescued, T1/found/front,
T1/found/newspace, R1/found, T3/found, T3/lowgd/found, T4/found, X2/found/ab, R2/found, X1/found,
X1/x1b/c29/found, H3/found, strategies/H2/found.
- osc is dropped: L1 finding 9, 4 front points in 9.5 CPU-h.
- ad3_share is 0: L1 section 5.
- `--eps 1.0` with the doubled entries gives L1's fixed shares. The review5 value gain is untested as a
  bandit reward at scale.
- `--tuple-caps` extends review5's default to trb and gen_skel (HUB.md "Not changed" 3).
- `--cap-renew box` gives renewed jobs to old tuples when a new low point lands in their box. It is
  behind a flag and has never run, so it is [H].
- The first start on the old archive deduplicates the cells and reads 6134 old run files. This has not
  been timed on a free CPU, so allow a few minutes before the first job.

## 4. Morning checklist (results that are not written automatically)
- T4: aes_check `T4/queue/run-*/best.circ.txt` of any job stopped before its end.
- T3, T3-b: new pool entries, `ls T3/lowgd/pool | sort -t- -k4`, against BEST.md, then aes_check.
- T1: `frontcollect.py` as in the entry.
- L1 / X2 arms, if they run after all: `STEPS="harvest eval"` after a stop.
- Exact searches: `grep -l CANDIDATE`, `grep '"SAT"'`, `grep "covering [1-9]"`, `grep BUILT`, `grep TARGET` over
  the listed logs. Each grep is named in its QUEUE.md entry.
- Then rerun `strategies/L1/l1b_score.py` (after `tonight.py`) with the new directories added to AGENTS / the scan.
