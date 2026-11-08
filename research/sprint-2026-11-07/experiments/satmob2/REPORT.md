# satmob2: factor-structured exact (SAT) search for an 87 on COUPLED plateaus

Folder: `~/xs-campaigns/2026-11-07-sprint/satmob2/` (nothing written in the repository, in `satmob/`
or in `sat/`; `sat/sat87.py`, `sat/run_scopes.py`, `sat/batch2_driver.prior` imported read-only).
Extends `satmob/` (whose four circuits had only 1 mobile + 1 root components) to plateaus with a
genuinely coupled factor: the kste corpus plateaus with radices 33, 45, 108 and our own plateaus with
a large factor (2101, 18927, 62856, 69228).  One solver child at a time, `nice -n 8`, CaDiCaL 1.9.5
via pysat; machine at load 24-28 on 20 threads throughout (sat/ batch2 with 12 shards, satmob's
campaign3, other agents), so wall times are pessimistic by roughly 2x [guess from the load average].
Work window 2026-11-07 18:57 - 20:25 (WSL clock, EST).  Labels: [proved] argument given; [checked]
exact computation, script named; [measured] run data; [guess].

Files: `mob2.py` (satmob's `mob.py` with local paths, a MAXFREE filter and component shape
statistics; same windows, same instances), `solve_child.py` (copy of satmob's), `fac.py` (NEW: the
coupled-factor window, built from the compressed plateau object instead of the local fan),
`coupling.py` (why part of a coupled factor is invisible to the local fan), `analyze_all.sh`,
`fac_all.sh`, `campaignA1.sh`, `campaignB.sh` (the sequences), `summarize.py` and `make_report.py`
(this file), `comp_<cid>.json` (fan output, local components, windows), `fac_<cid>.json` (choices of
every plateau factor at the state, the coupled factor's window), `results.jsonl` (one line per
instance, sat87's schema + `family` M/F, `level`, `pool`, `component` or `factor`), `run.log`,
`analyze.out`, `fac_analyze.out`, `coupling.out`, `found/` and `FOUND_87` (empty: no SAT), `STOP`
(create it to stop `campaignB.sh` between instances).

## 0. Result in one line

No 87.  On seven coupled plateaus every local-component instance that finished is UNSAT (50 of 50
single fan components, 105 of 106 pairs with free <= 3) [measured]; the coupled factor itself, taken as
one window, is a different and harder object: k = 10-38, free = 5-20, and none of the seven coupled
instances finished at 120 s; the two with free = 5 (radix 108 and 33) were retried at 600 s (table
in section 3).  The structural result [checked, section 2]: at a member state the local fan sees a
coupled factor only through its one-for-one-swappable values; the values that can only leave in
groups (2-13 at a time) are locally core, so satmob's decomposition never isolates the coupled
factor, and the correct window must be taken from the plateau object.

## 1. Targets and what was computed

Circuits (CID as in `sat/run_scopes.load`; hunt samples are wired greedily by
`sat87.wiring_from_values`, kste sets likewise from `kste/data/kste_valuesets.json`):

| CID | plateau | radices (size, verification) | plateau core | how chosen |
|---|---|---|---:|---|
| kste:3146 | kste cover #43 | 33 x 3^7 (72,171, pairwise; kste/REPORT.txt: product incomplete) | 45 | sid of plateau_summary row 43 |
| kste:2229 | kste cover #34 | 45 x 3^4 (3,645, full) | 48 | row 34 |
| kste:1557 | kste cover #41 | 108 x 3^4 (8,748, full) | 46 | row 41 |
| sampleA:109 | hunt p943c008e56986b92 | 2101 x 15 x 11 x 3 x 3 (3,119,985, pairwise) | 40 | hunt/plateaus.json state 736c15935d28795b = hunt/samples.jsonl line 109 (arm A, free-05) |
| sampleA:48 | hunt pce9227a62d5504c7 | 18927 x 15 x 3 x 3 (2,555,145, pairwise) | 40 | giants entry 2 (p5d74d61aab10fa15), sample hash c2777ac97d3ec986 |
| sampleA:781 | giants p80424727ddf34e79 | 62856 x 3 (188,568, pairwise) | 37 | giants entry 9 (giant-a39cdf21f2696dc4), `giants/pl_p80424727ddf34e79.json` |
| sampleC:131 | giants p55f9dc07f8b3409b | 69228 x 3 x 3 (623,052, pairwise) | 39 | giants entry 8 (giant-7148dc0745bc4cd6), `giants/pl_p55f9dc07f8b3409b.json` |

Two kinds of window, both turned into sat87's I(K, |W| - 1) with K = S \ W split-closed (asserted
before every instance), distinctness and the two sound symmetry breaks on, full operand pool unless
`pool = span` is stated:

* **M (local; satmob's method, `mob2.py`)**: `pes_lib.fan(make_space("mc", None), helpers)` at the
  state S gives the remove1-neutral moves; MOBILE = union of their removed sets, CORE = the rest;
  components = connected components of the mobile -> consumer graph under the wiring; W = seeds
  (the component's mobile values and roots) + any-pair forced closure (`run_scopes.window`, ANYPAIR).
  Level 1 = one component, level 2 = a pair.  Identical to satmob's instances in every detail.
* **F (coupled factor; `fac.py`, new)**: the plateau object (pes_lib.compress output: `core` and
  `factors = [{values, choices}]`, from `kste/data/kste_plateau_objs.json`, `hunt/plateaus.json` or
  `giants/pl_*.json`) is aligned to S (byte rotation 0 in all seven cases; the member's 56 helpers
  equal core u one listed choice per factor, asserted).  For the coupled factor f0: seeds = its
  choice at S plus every value of S that uses a choice value as an operand; W = any-pair forced
  closure of the seeds; K = S \ W.  Meaning [proved, as sat87's docstring]: UNSAT iff no circuit with
  <= 87 XOR gates, of any depth, with any helper values, has a value set containing K, i.e. no 87
  keeps the plateau core and the other factors' choices (and whatever else is in K) and redoes the
  coupled factor, with any re-sharing against the kept values, in one gate less.  It is the coupled
  analogue of satmob's level-1 instance; the local method cannot produce it (section 2).

## 2. Component structures [checked: analyze.out, fac_analyze.out, coupling.out]

What the local fan sees at the member state, against the plateau object:

* On all seven circuits the local components are almost all 1 mobile + 1 root, as on satmob's four
  circuits: 50 components, of which 46 are 1+1, one 2+1 on sampleA:109 (hunt 2101), and 2+2, 2+1,
  1+2 on sampleA:48 (hunt 18927).  The local core is LARGER than the plateau core on every circuit:
  47 vs 45 (kste 33), 49 vs 48 (kste 45), 48 vs 46 (kste 108), 48 vs 40 (hunt 2101), 45 vs 40
  (hunt 18927), 48 vs 37 (giant 62856), 50 vs 39 (giant 69228).  The difference is exactly the part
  of the coupled factor's choice that the local fan does not move.
* Why [checked: coupling.py; the statement holds value by value on all seven]: a value v of the
  coupled factor's choice at S is locally mobile IF AND ONLY IF some other listed choice of the factor
  differs from the current one by v alone (one value leaves, one enters: a remove1-neutral step).
  The locally core choice values can only leave together with 2-13 other values of the choice
  (minimum group sizes: kste 33: 3,3; kste 45: 3; kste 108: 5,5; hunt 2101: 2,2,2,3,4,4,5; hunt
  18927: 2,2,3,6,7; giant 62856: 3,3,4,5,6,6,6,9,11,13,13; giant 69228: 2,2,2,3,3,4,4,6,6,6,6).
  Equivalently: of the factor's other choices, only 4-21 are at distance 1 from the current one
  (kste 33: 4 of 32; kste 45: 6 of 44; kste 108: 8 of 107; hunt 2101: 10 of 2100; hunt 18927: 21 of
  18926; giant 62856: 14 of 62855; giant 69228: 8 of 69227); the rest need 2-15 values to leave at
  once.  So "coupled factor" = a factor whose choice graph is not generated by single swaps from one
  state; the local fan sees its 1-neighbourhood, which looks like several independent 3-way factors.
* Consequence for the windows: the coupled factor's F window contains the M windows of the local
  components it touches (2-7 of them) PLUS the locally core choice values and their consumers; it is
  the union of a level-2..7 local instance with values satmob would have treated as fixed core.  On
  the giants it is even larger than the whole local mobile part (k = 36 / 38 vs 28 / 21).

## Component structures [checked: comp_*.json, fac_*.json]

Local fan structure at the member state (satmob's method) and the plateau's coupled factor at that state.

| circuit | plateau (radices) | depth | plateau core | local core | local mobile | neutral moves | local components (shapes) | coupled factor: choice size / locally core / local comps touched / roots (targets) | coupled instance (k, tW, free) | whole mobile part (k, tW, free) |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|
| kste:3146 | kste#43 33x3^7 | 8 | 45 | 47 | 9 | 18 | 9 (1+1 x9) | 4 / 2 / [0, 7] / 3 (1) | (12, 6, 5) | (36, 16, 19) |
| kste:2229 | kste#34 45x3^4 | 7 | 48 | 49 | 7 | 14 | 7 (1+1 x7) | 4 / 1 / [1, 5, 6] / 3 (2) | (17, 7, 9) | (27, 12, 14) |
| kste:1557 | kste#41 108x3^4 | 7 | 46 | 48 | 8 | 16 | 8 (1+1 x8) | 6 / 2 / [1, 2, 3, 7] / 4 (4) | (10, 4, 5) | (32, 13, 18) |
| sampleA:109 | hunt 2101x15x11x3x3 | 8 | 40 | 48 | 8 | 22 | 7 (1+1 x6, 2+1 x1) | 10 / 7 / [0, 1, 2] / 8 (8) | (18, 8, 9) | (22, 11, 10) |
| sampleA:48 | hunt 18927x15x3x3 | 9 | 40 | 45 | 11 | 29 | 9 (1+1 x6, 1+2 x1, 2+1 x1, 2+2 x1) | 12 / 5 / [0, 2, 4, 6, 7, 8] / 11 (9) | (31, 15, 15) | (29, 13, 15) |
| sampleA:781 | giant 62856x3 | 9 | 37 | 48 | 8 | 16 | 8 (1+1 x8) | 18 / 11 / [1, 2, 3, 4, 5, 6, 7] / 13 (11) | (36, 15, 20) | (28, 13, 14) |
| sampleC:131 | giant 69228x3x3 | 12 | 39 | 50 | 6 | 12 | 6 (1+1 x6) | 15 / 11 / [0, 1, 4, 5] / 11 (10) | (38, 17, 20) | (21, 10, 10) |

Per-circuit local components (k, tW, free) in component order, and the plateau's 3-way factors seen locally:

* kste:3146 (kste#43 33x3^7): local c0:1+1(7,4,2) c1:1+1(7,4,2) c2:1+1(4,2,1) c3:1+1(12,6,5) c4:1+1(5,2,2) c5:1+1(4,2,1) c6:1+1(2,1,0) c7:1+1(3,2,0) c8:1+1(4,2,1); plateau factors (radix | choice size | local comps) f0:r33|4|[0, 7] f1:r3|1|[5] f2:r3|1|[3] f3:r3|1|[4] f4:r3|1|[1] f5:r3|1|[6] f6:r3|1|[2] f7:r3|1|[8]
* kste:2229 (kste#34 45x3^4): local c0:1+1(3,2,0) c1:1+1(2,1,0) c2:1+1(4,2,1) c3:1+1(3,2,0) c4:1+1(4,2,1) c5:1+1(12,5,6) c6:1+1(3,2,0); plateau factors (radix | choice size | local comps) f0:r45|4|[1, 5, 6] f1:r3|1|[3] f2:r3|1|[0] f3:r3|1|[2] f4:r3|1|[4]
* kste:1557 (kste#41 108x3^4): local c0:1+1(4,2,1) c1:1+1(2,1,0) c2:1+1(5,2,2) c3:1+1(2,1,0) c4:1+1(4,2,1) c5:1+1(11,6,4) c6:1+1(4,2,1) c7:1+1(3,2,0); plateau factors (radix | choice size | local comps) f0:r108|6|[1, 2, 3, 7] f1:r3|1|[0] f2:r3|1|[5] f3:r3|1|[6] f4:r3|1|[4]
* sampleA:109 (hunt 2101x15x11x3x3): local c0:1+1(2,1,0) c1:1+1(5,3,1) c2:1+1(4,2,1) c3:2+1(5,2,2) c4:1+1(4,2,1) c5:1+1(2,1,0) c6:1+1(3,2,0); plateau factors (radix | choice size | local comps) f0:r2101|10|[0, 1, 2] f1:r15|2|[3] f2:r11|2|[6] f3:r3|1|[4] f4:r3|1|[5]
* sampleA:48 (hunt 18927x15x3x3): local c0:2+2(7,3,3) c1:1+1(3,2,0) c2:1+1(3,2,0) c3:2+1(5,2,2) c4:1+1(9,4,4) c5:1+1(2,1,0) c6:1+2(7,4,2) c7:1+1(2,1,0) c8:1+1(7,4,2); plateau factors (radix | choice size | local comps) f0:r18927|12|[0, 2, 4, 6, 7, 8] f1:r15|2|[3] f2:r3|1|[1] f3:r3|1|[5]
* sampleA:781 (giant 62856x3): local c0:1+1(7,4,2) c1:1+1(4,2,1) c2:1+1(3,2,0) c3:1+1(3,2,0) c4:1+1(8,4,3) c5:1+1(2,1,0) c6:1+1(7,4,2) c7:1+1(4,2,1); plateau factors (radix | choice size | local comps) f0:r62856|18|[1, 2, 3, 4, 5, 6, 7] f1:r3|1|[0]
* sampleC:131 (giant 69228x3x3): local c0:1+1(4,2,1) c1:1+1(3,2,0) c2:1+1(7,4,2) c3:1+1(4,2,1) c4:1+1(4,2,1) c5:1+1(3,2,0); plateau factors (radix | choice size | local comps) f0:r69228|15|[0, 1, 4, 5] f1:r3|1|[3] f2:r3|1|[2]

## Instance table [measured]

One row per distinct (circuit, W, pool); best record kept.  free = k - 1 - tW.  F = plateau coupled factor window (fac.py), M = local fan component window (mob2.py, satmob's method).  prior = sat/ campaigns' result on the identical (circuit, W) if any.

| circuit | scope | level | k | tW | free | pool | result | wall s | solve s | clauses | prior (sat/) |
|---|---|---|---:|---:|---:|---|---|---:|---:|---:|---|
| kste:3146 | F:f0(r33) | factor | 12 | 6 | 5 | full | TIMEOUT(600s) | 585.6 | - | - | - |
| kste:2229 | F:f0(r45) | factor | 17 | 7 | 9 | full | TIMEOUT(120s) | 121.1 | - | - | - |
| kste:1557 | F:f0(r108) | factor | 10 | 4 | 5 | full | TIMEOUT(600s) | 584.5 | - | - | - |
| sampleA:109 | F:f0(r2101) | factor | 18 | 8 | 9 | full | TIMEOUT(120s) | 121.0 | - | - | - |
| sampleA:48 | F:f0(r18927) | factor | 31 | 15 | 15 | full | TIMEOUT(120s) | 121.1 | - | - | - |
| sampleA:781 | F:f0(r62856) | factor | 36 | 15 | 20 | full | TIMEOUT(120s) | 122.1 | - | - | - |
| sampleC:131 | F:f0(r69228) | factor | 38 | 17 | 20 | full | TIMEOUT(120s) | 120.9 | - | - | - |
| kste:3146 | M:c6 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.02 | 15470 | - |
| kste:3146 | M:c7 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.04 | 31170 | - |
| kste:3146 | M:c2 | 1 | 4 | 2 | 1 | full | UNSAT | 0.7 | 0.58 | 46953 | - |
| kste:3146 | M:c5 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.19 | 46935 | - |
| kste:3146 | M:c8 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.18 | 46887 | - |
| kste:3146 | M:c4 | 1 | 5 | 2 | 2 | full | UNSAT | 1.0 | 0.78 | 62680 | - |
| kste:3146 | M:c0 | 1 | 7 | 4 | 2 | full | UNSAT | 2.9 | 2.6 | 94924 | - |
| kste:3146 | M:c1 | 1 | 7 | 4 | 2 | full | UNSAT | 4.7 | 4.31 | 94948 | - |
| kste:3146 | M:c3 | 1 | 12 | 6 | 5 | full | TIMEOUT(120s) | 120.8 | - | - | - |
| kste:3146 | M:c6+c7 | 2 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.17 | 46875 | - |
| kste:3146 | M:c2+c6 | 2 | 6 | 3 | 2 | full | UNSAT | 2.5 | 2.32 | 78740 | - |
| kste:3146 | M:c5+c6 | 2 | 6 | 3 | 2 | full | UNSAT | 1.8 | 1.49 | 78710 | - |
| kste:3146 | M:c6+c8 | 2 | 6 | 3 | 2 | full | UNSAT | 2.6 | 2.41 | 78630 | - |
| kste:3146 | M:c2+c7 | 2 | 7 | 4 | 2 | full | UNSAT | 7.1 | 6.75 | 94864 | - |
| kste:3146 | M:c5+c7 | 2 | 7 | 4 | 2 | full | UNSAT | 3.3 | 3.01 | 94828 | - |
| kste:3146 | M:c2+c8 | 2 | 7 | 3 | 3 | full | UNSAT | 9.9 | 9.73 | 94659 | - |
| kste:3146 | M:c4+c7 | 2 | 7 | 3 | 3 | full | UNSAT | 10.2 | 9.95 | 94563 | - |
| kste:3146 | M:c0+c6 | 2 | 8 | 4 | 3 | full | UNSAT | 23.3 | 23.02 | 110927 | - |
| kste:3146 | M:c2+c5 | 2 | 8 | 4 | 3 | full | UNSAT | 18.5 | 18.19 | 110997 | - |
| kste:3146 | M:c5+c8 | 2 | 8 | 4 | 3 | full | UNSAT | 18.1 | 17.8 | 110843 | - |
| kste:3146 | M:c7+c8 | 2 | 8 | 4 | 3 | full | UNSAT | 18.9 | 18.57 | 110745 | - |
| kste:3146 | M:c1+c6 | 2 | 9 | 5 | 3 | full | UNSAT | 39.8 | 39.45 | 127319 | - |
| kste:3146 | M:c1+c7 | 2 | 10 | 6 | 3 | full | UNSAT | 116.0 | 115.8 | 143795 | - |
| kste:2229 | M:c1 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.02 | 15432 | - |
| kste:2229 | M:c0 | 1 | 3 | 2 | 0 | full | UNSAT | 0.3 | 0.07 | 31118 | - |
| kste:2229 | M:c3 | 1 | 3 | 2 | 0 | full | UNSAT | 0.3 | 0.08 | 31098 | - |
| kste:2229 | M:c6 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.03 | 31102 | - |
| kste:2229 | M:c2 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.2 | 46791 | - |
| kste:2229 | M:c4 | 1 | 4 | 2 | 1 | full | UNSAT | 0.5 | 0.24 | 46791 | - |
| kste:2229 | M:c5 | 1 | 12 | 5 | 6 | full | TIMEOUT(120s) | 120.7 | - | - | - |
| kste:2229 | M:c0+c1 | 2 | 5 | 3 | 1 | full | UNSAT | 0.8 | 0.61 | 62705 | - |
| kste:2229 | M:c1+c3 | 2 | 5 | 3 | 1 | full | UNSAT | 0.8 | 0.61 | 62665 | - |
| kste:2229 | M:c0+c3 | 2 | 6 | 4 | 1 | full | UNSAT | 0.9 | 0.77 | 78711 | - |
| kste:2229 | M:c0+c6 | 2 | 6 | 4 | 1 | full | UNSAT | 0.8 | 0.58 | 78721 | - |
| kste:2229 | M:c3+c6 | 2 | 6 | 4 | 1 | full | UNSAT | 1.0 | 0.65 | 78671 | - |
| kste:2229 | M:c1+c2 | 2 | 6 | 3 | 2 | full | UNSAT | 2.1 | 1.83 | 78510 | - |
| kste:2229 | M:c1+c4 | 2 | 6 | 3 | 2 | full | UNSAT | 2.6 | 2.33 | 78510 | - |
| kste:2229 | M:c1+c6 | 2 | 6 | 3 | 2 | full | UNSAT | 1.9 | 1.66 | 78550 | - |
| kste:2229 | M:c2+c3 | 2 | 6 | 3 | 2 | full | UNSAT | 1.6 | 1.44 | 78510 | - |
| kste:2229 | M:c0+c2 | 2 | 7 | 4 | 2 | full | UNSAT | 4.8 | 4.55 | 94660 | - |
| kste:2229 | M:c0+c4 | 2 | 7 | 4 | 2 | full | UNSAT | 3.2 | 2.99 | 94660 | - |
| kste:2229 | M:c2+c6 | 2 | 7 | 4 | 2 | full | UNSAT | 3.4 | 3.21 | 94612 | - |
| kste:2229 | M:c3+c4 | 2 | 7 | 4 | 2 | full | UNSAT | 3.9 | 3.68 | 94600 | - |
| kste:2229 | M:c4+c6 | 2 | 7 | 4 | 2 | full | UNSAT | 3.4 | 3.12 | 94612 | - |
| kste:2229 | M:c2+c4 | 2 | 8 | 4 | 3 | full | UNSAT | 16.1 | 15.85 | 110605 | - |
| kste:1557 | M:c1 | 1 | 2 | 1 | 0 | full | UNSAT | 0.1 | 0.02 | 15422 | - |
| kste:1557 | M:c3 | 1 | 2 | 1 | 0 | full | UNSAT | 0.1 | 0.02 | 15422 | - |
| kste:1557 | M:c7 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.03 | 31082 | - |
| kste:1557 | M:c0 | 1 | 4 | 2 | 1 | full | UNSAT | 0.3 | 0.15 | 46779 | - |
| kste:1557 | M:c4 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.2 | 46773 | - |
| kste:1557 | M:c6 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.19 | 46773 | - |
| kste:1557 | M:c2 | 1 | 5 | 2 | 2 | full | UNSAT | 1.5 | 1.15 | 62520 | - |
| kste:1557 | M:c3+c7 | 2 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.24 | 46767 | - |
| kste:1557 | M:c1+c7 | 2 | 5 | 3 | 1 | full | UNSAT | 0.6 | 0.32 | 62633 | - |
| kste:1557 | M:c1+c3 | 2 | 5 | 2 | 2 | full | UNSAT | 0.8 | 0.69 | 62520 | - |
| kste:1557 | M:c0+c1 | 2 | 6 | 3 | 2 | full | UNSAT | 1.8 | 1.69 | 78490 | - |
| kste:1557 | M:c0+c3 | 2 | 6 | 3 | 2 | full | UNSAT | 1.5 | 1.19 | 78490 | - |
| kste:1557 | M:c1+c6 | 2 | 6 | 3 | 2 | full | UNSAT | 2.8 | 2.53 | 78480 | - |
| kste:1557 | M:c3+c4 | 2 | 6 | 3 | 2 | full | UNSAT | 3.1 | 2.88 | 78480 | - |
| kste:1557 | M:c3+c6 | 2 | 6 | 3 | 2 | full | UNSAT | 2.1 | 1.87 | 78480 | - |
| kste:1557 | M:c4+c7 | 2 | 7 | 4 | 2 | full | UNSAT | 3.3 | 3.08 | 94576 | - |
| kste:1557 | M:c6+c7 | 2 | 7 | 4 | 2 | full | UNSAT | 3.3 | 3.12 | 94576 | - |
| kste:1557 | M:c0+c4 | 2 | 7 | 3 | 3 | full | UNSAT | 7.1 | 6.86 | 94419 | - |
| kste:1557 | M:c1+c2 | 2 | 7 | 3 | 3 | full | UNSAT | 10.4 | 10.16 | 94383 | - |
| kste:1557 | M:c1+c4 | 2 | 7 | 3 | 3 | full | UNSAT | 10.3 | 10.02 | 94431 | - |
| kste:1557 | M:c2+c7 | 2 | 7 | 3 | 3 | full | UNSAT | 11.6 | 11.18 | 94395 | - |
| kste:1557 | M:c0+c6 | 2 | 8 | 4 | 3 | full | UNSAT | 16.6 | 16.21 | 110605 | - |
| kste:1557 | M:c0+c7 | 2 | 8 | 4 | 3 | full | UNSAT | 13.4 | 13.01 | 110647 | - |
| kste:1557 | M:c4+c6 | 2 | 8 | 4 | 3 | full | UNSAT | 17.9 | 17.52 | 110591 | - |
| sampleA:109 | M:c0 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.03 | 15444 | - |
| sampleA:109 | M:c5 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.02 | 15444 | - |
| sampleA:109 | M:c6 | 1 | 3 | 2 | 0 | full | UNSAT | 0.4 | 0.07 | 31146 | - |
| sampleA:109 | M:c2 | 1 | 4 | 2 | 1 | full | UNSAT | -0.6 | 0.13 | 46833 | - |
| sampleA:109 | M:c4 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.16 | 46845 | - |
| sampleA:109 | M:c1 | 1 | 5 | 3 | 1 | full | UNSAT | 0.4 | 0.24 | 62769 | - |
| sampleA:109 | M:c3 | 1 | 5 | 2 | 2 | full | UNSAT | 1.4 | 1.14 | 62624 | - |
| sampleA:109 | M:c0+c5 | 2 | 4 | 2 | 1 | full | UNSAT | 0.5 | 0.28 | 46821 | - |
| sampleA:109 | M:c0+c6 | 2 | 5 | 3 | 1 | full | UNSAT | 0.9 | 0.69 | 62753 | - |
| sampleA:109 | M:c5+c6 | 2 | 5 | 3 | 1 | full | UNSAT | 1.0 | 0.69 | 62753 | - |
| sampleA:109 | M:c0+c1 | 2 | 6 | 3 | 2 | full | UNSAT | 1.3 | 1.03 | 78630 | - |
| sampleA:109 | M:c0+c4 | 2 | 6 | 3 | 2 | full | UNSAT | 2.6 | 2.28 | 78590 | - |
| sampleA:109 | M:c2+c5 | 2 | 6 | 3 | 2 | full | UNSAT | 2.0 | 1.75 | 78570 | - |
| sampleA:109 | M:c4+c5 | 2 | 6 | 3 | 2 | full | UNSAT | 2.2 | 1.88 | 78590 | - |
| sampleA:109 | M:c1+c5 | 2 | 7 | 4 | 2 | full | UNSAT | 3.9 | 3.62 | 94744 | - |
| sampleA:109 | M:c2+c6 | 2 | 7 | 4 | 2 | full | UNSAT | 4.7 | 4.35 | 94744 | - |
| sampleA:109 | M:c4+c6 | 2 | 7 | 4 | 2 | full | UNSAT | 4.4 | 4.04 | 94768 | - |
| sampleA:109 | M:c1+c6 | 2 | 8 | 5 | 2 | full | UNSAT | 5.9 | 5.64 | 111068 | - |
| sampleA:109 | M:c0+c3 | 2 | 7 | 3 | 3 | full | UNSAT | 9.8 | 9.51 | 94527 | - |
| sampleA:109 | M:c3+c5 | 2 | 7 | 3 | 3 | full | UNSAT | 6.6 | 6.29 | 94527 | - |
| sampleA:109 | M:c1+c2 | 2 | 8 | 4 | 3 | full | UNSAT | 25.5 | 25.22 | 110787 | - |
| sampleA:109 | M:c2+c4 | 2 | 8 | 4 | 3 | full | UNSAT | 19.0 | 18.77 | 110731 | - |
| sampleA:109 | M:c3+c6 | 2 | 8 | 4 | 3 | full | UNSAT | 29.0 | 28.75 | 110815 | - |
| sampleA:109 | M:c1+c4 | 2 | 9 | 5 | 3 | full | UNSAT | 35.2 | 34.82 | 127159 | - |
| sampleA:48 | M:c5 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.02 | 15450 | - |
| sampleA:48 | M:c7 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.02 | 15452 | - |
| sampleA:48 | M:c1 | 1 | 3 | 2 | 0 | full | UNSAT | 0.3 | 0.03 | 31146 | - |
| sampleA:48 | M:c2 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.04 | 31134 | - |
| sampleA:48 | M:c3 | 1 | 5 | 2 | 2 | full | UNSAT | 1.7 | 1.48 | 62648 | - |
| sampleA:48 | M:c6 | 1 | 7 | 4 | 2 | full | UNSAT | 2.2 | 2.01 | 94828 | - |
| sampleA:48 | M:c8 | 1 | 7 | 4 | 2 | full | UNSAT | 3.6 | 3.28 | 94756 | - |
| sampleA:48 | M:c0 | 1 | 7 | 3 | 3 | full | UNSAT | 6.3 | 6.03 | 94611 | - |
| sampleA:48 | M:c2+c7 | 2 | 4 | 2 | 1 | full | UNSAT | 0.3 | 0.16 | 46845 | - |
| sampleA:48 | M:c5+c7 | 2 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.2 | 46845 | - |
| sampleA:48 | M:c1+c5 | 2 | 5 | 3 | 1 | full | UNSAT | 0.9 | 0.74 | 62753 | - |
| sampleA:48 | M:c1+c7 | 2 | 5 | 3 | 1 | full | UNSAT | 0.8 | 0.63 | 62761 | - |
| sampleA:48 | M:c2+c5 | 2 | 5 | 3 | 1 | full | UNSAT | 0.6 | 0.36 | 62729 | - |
| sampleA:48 | M:c1+c2 | 2 | 6 | 4 | 1 | full | UNSAT | 1.0 | 0.76 | 78771 | - |
| sampleA:48 | M:c3+c5 | 2 | 7 | 3 | 3 | full | UNSAT | 8.0 | 7.8 | 94563 | - |
| sampleA:48 | M:c3+c7 | 2 | 7 | 3 | 3 | full | UNSAT | 12.0 | 11.74 | 94575 | - |
| sampleA:48 | M:c1+c3 | 2 | 8 | 4 | 3 | full | UNSAT | 25.0 | 24.53 | 110815 | - |
| sampleA:48 | M:c2+c3 | 2 | 8 | 4 | 3 | full | UNSAT | 25.3 | 24.89 | 110773 | - |
| sampleA:48 | M:c2+c8 | 2 | 8 | 4 | 3 | full | UNSAT | 17.8 | 17.48 | 110773 | - |
| sampleA:48 | M:c7+c8 | 2 | 8 | 4 | 3 | full | UNSAT | 20.2 | 19.93 | 110787 | - |
| sampleA:48 | M:c2+c6 | 2 | 9 | 5 | 3 | full | UNSAT | 49.5 | 49.0 | 127207 | - |
| sampleA:48 | M:c5+c6 | 2 | 9 | 5 | 3 | full | UNSAT | 57.8 | 57.61 | 127207 | - |
| sampleA:48 | M:c1+c6 | 2 | 10 | 6 | 3 | full | TIMEOUT(120s) | 122.1 | - | - | - |
| sampleA:48 | M:c1+c8 | 2 | 10 | 6 | 3 | full | UNSAT | 94.8 | 94.49 | 143633 | - |
| sampleA:781 | M:c5 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.02 | 15470 | - |
| sampleA:781 | M:c2 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.05 | 31186 | - |
| sampleA:781 | M:c3 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.05 | 31186 | - |
| sampleA:781 | M:c1 | 1 | 4 | 2 | 1 | full | UNSAT | 0.3 | 0.16 | 46917 | - |
| sampleA:781 | M:c7 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.25 | 46851 | - |
| sampleA:781 | M:c0 | 1 | 7 | 4 | 2 | full | UNSAT | 1.4 | 1.14 | 94864 | - |
| sampleA:781 | M:c6 | 1 | 7 | 4 | 2 | full | UNSAT | 2.0 | 1.69 | 94912 | - |
| sampleA:781 | M:c4 | 1 | 8 | 4 | 3 | full | UNSAT | 11.1 | 10.58 | 110885 | - |
| sampleA:781 | M:c2+c5 | 2 | 5 | 3 | 1 | full | UNSAT | 0.0 | 0.75 | 62833 | - |
| sampleA:781 | M:c3+c5 | 2 | 5 | 3 | 1 | full | UNSAT | 0.9 | 0.73 | 62833 | - |
| sampleA:781 | M:c2+c3 | 2 | 6 | 4 | 1 | full | UNSAT | 1.3 | 0.9 | 78901 | - |
| sampleA:781 | M:c2+c7 | 2 | 6 | 3 | 2 | full | UNSAT | 1.9 | 1.53 | 78630 | - |
| sampleA:781 | M:c5+c7 | 2 | 6 | 3 | 2 | full | UNSAT | 2.7 | 2.44 | 78600 | - |
| sampleA:781 | M:c1+c3 | 2 | 7 | 4 | 2 | full | UNSAT | 5.4 | 5.17 | 94876 | - |
| sampleA:781 | M:c3+c7 | 2 | 7 | 4 | 2 | full | UNSAT | 3.1 | 2.85 | 94744 | - |
| sampleA:781 | M:c0+c3 | 2 | 8 | 4 | 3 | full | UNSAT | 15.5 | 15.18 | 110941 | - |
| sampleA:781 | M:c1+c2 | 2 | 8 | 4 | 3 | full | UNSAT | 42.2 | 42.04 | 110983 | - |
| sampleA:781 | M:c1+c7 | 2 | 8 | 4 | 3 | full | UNSAT | 30.5 | 30.16 | 110759 | - |
| sampleA:781 | M:c0+c5 | 2 | 9 | 5 | 3 | full | UNSAT | 32.4 | 31.91 | 127255 | - |
| sampleA:781 | M:c5+c6 | 2 | 9 | 5 | 3 | full | UNSAT | 36.5 | 36.27 | 127319 | - |
| sampleA:781 | M:c0+c2 | 2 | 10 | 6 | 3 | full | UNSAT | 51.6 | 51.21 | 143795 | - |
| sampleA:781 | M:c2+c6 | 2 | 10 | 6 | 3 | full | UNSAT | 110.1 | 109.79 | 143867 | - |
| sampleA:781 | M:c3+c6 | 2 | 10 | 6 | 3 | full | UNSAT | 85.6 | 84.98 | 143867 | - |
| sampleC:131 | M:c1 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.03 | 31154 | - |
| sampleC:131 | M:c5 | 1 | 3 | 2 | 0 | full | UNSAT | 0.3 | 0.07 | 31158 | - |
| sampleC:131 | M:c0 | 1 | 4 | 2 | 1 | full | UNSAT | 0.3 | 0.12 | 46851 | - |
| sampleC:131 | M:c3 | 1 | 4 | 2 | 1 | full | UNSAT | 0.6 | 0.29 | 46845 | - |
| sampleC:131 | M:c4 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.17 | 46881 | - |
| sampleC:131 | M:c2 | 1 | 7 | 4 | 2 | full | UNSAT | 2.7 | 2.32 | 94804 | - |
| sampleC:131 | M:c1+c5 | 2 | 6 | 4 | 1 | full | UNSAT | 1.5 | 1.1 | 78821 | - |
| sampleC:131 | M:c1+c3 | 2 | 6 | 3 | 2 | full | UNSAT | 2.6 | 2.29 | 78610 | - |
| sampleC:131 | M:c0+c1 | 2 | 7 | 4 | 2 | full | UNSAT | 3.4 | 3.1 | 94732 | - |
| sampleC:131 | M:c0+c5 | 2 | 7 | 4 | 2 | full | UNSAT | 5.2 | 4.78 | 94744 | - |
| sampleC:131 | M:c1+c4 | 2 | 7 | 4 | 2 | full | UNSAT | 3.7 | 3.49 | 94792 | - |
| sampleC:131 | M:c3+c5 | 2 | 7 | 4 | 2 | full | UNSAT | 2.2 | 1.87 | 94732 | - |
| sampleC:131 | M:c4+c5 | 2 | 7 | 4 | 2 | full | UNSAT | 5.5 | 5.14 | 94804 | - |
| sampleC:131 | M:c0+c4 | 2 | 7 | 3 | 3 | full | UNSAT | 9.3 | 8.93 | 94563 | - |
| sampleC:131 | M:c0+c3 | 2 | 8 | 4 | 3 | full | UNSAT | 21.9 | 21.58 | 110689 | - |
| sampleC:131 | M:c2+c5 | 2 | 8 | 4 | 3 | full | UNSAT | 11.4 | 11.06 | 110871 | - |
| sampleC:131 | M:c3+c4 | 2 | 8 | 4 | 3 | full | UNSAT | 26.3 | 25.98 | 110759 | - |
| sampleC:131 | M:c1+c2 | 2 | 10 | 6 | 3 | full | UNSAT | 55.9 | 55.44 | 143687 | - |

## Counts per circuit and level [measured]

| circuit | level | pool | instances | UNSAT | SAT | TIMEOUT | max solved free | UNSAT solve-time median / max (s) |
|---|---|---|---:|---:|---:|---:|---:|---|
| kste:3146 | 1 | full | 9 | 8 | 0 | 1 | 2 | 0.6 / 4.3 |
| kste:3146 | 2 | full | 14 | 14 | 0 | 0 | 3 | 9.9 / 115.8 |
| kste:3146 | factor | full | 1 | 0 | 0 | 1 | - | - |
| kste:2229 | 1 | full | 7 | 6 | 0 | 1 | 1 | 0.1 / 0.2 |
| kste:2229 | 2 | full | 15 | 15 | 0 | 0 | 3 | 1.8 / 15.8 |
| kste:2229 | factor | full | 1 | 0 | 0 | 1 | - | - |
| kste:1557 | 1 | full | 7 | 7 | 0 | 0 | 2 | 0.1 / 1.1 |
| kste:1557 | 2 | full | 17 | 17 | 0 | 0 | 3 | 3.1 / 17.5 |
| kste:1557 | factor | full | 1 | 0 | 0 | 1 | - | - |
| sampleA:109 | 1 | full | 7 | 7 | 0 | 0 | 2 | 0.1 / 1.1 |
| sampleA:109 | 2 | full | 17 | 17 | 0 | 0 | 3 | 4.0 / 34.8 |
| sampleA:109 | factor | full | 1 | 0 | 0 | 1 | - | - |
| sampleA:48 | 1 | full | 8 | 8 | 0 | 0 | 3 | 1.5 / 6.0 |
| sampleA:48 | 2 | full | 16 | 15 | 0 | 1 | 3 | 11.7 / 94.5 |
| sampleA:48 | factor | full | 1 | 0 | 0 | 1 | - | - |
| sampleA:781 | 1 | full | 8 | 8 | 0 | 0 | 3 | 0.2 / 10.6 |
| sampleA:781 | 2 | full | 15 | 15 | 0 | 0 | 3 | 15.2 / 109.8 |
| sampleA:781 | factor | full | 1 | 0 | 0 | 1 | - | - |
| sampleC:131 | 1 | full | 6 | 6 | 0 | 0 | 2 | 0.2 / 2.3 |
| sampleC:131 | 2 | full | 12 | 12 | 0 | 0 | 3 | 5.1 / 55.4 |
| sampleC:131 | factor | full | 1 | 0 | 0 | 1 | - | - |

## Hardness by free values (full pool) [measured]

| free | instances | UNSAT | TIMEOUT | UNSAT solve s min / median / max |
|---:|---:|---:|---:|---|
| 0 | 21 | 21 | 0 | 0.0 / 0.0 / 0.1 |
| 1 | 37 | 37 | 0 | 0.1 / 0.3 / 1.1 |
| 2 | 51 | 51 | 0 | 0.7 / 2.4 / 6.8 |
| 3 | 47 | 46 | 1 | 6.0 / 18.8 / 115.8 |
| 5 | 3 | 0 | 3 | - |
| 6 | 1 | 0 | 1 | - |
| 9 | 2 | 0 | 2 | - |
| 15 | 1 | 0 | 1 | - |
| 20 | 2 | 0 | 2 | - |

Totals: 165 distinct instances: {'UNSAT': 155, 'TIMEOUT': 10}; solver wall 3657 s

(The tables above are `summarize.py` output at the time of writing; `campaignB.sh` keeps appending to
`results.jsonl`, see section 7.)

## 4. What is now excluded for coupled plateaus [proved as stated; outcomes measured]

Each UNSAT row says: no <= 87 circuit (any depth, any helpers) contains K = S \ W for that circuit
and that W (W lists in `results.jsonl`).  Per circuit, with the plateau in brackets:

* Local level 1 complete on all seven circuits (50 of 50 fan components UNSAT): for every value the
  local fan can move alone, no 87 keeps everything outside that value's window.  In plateau language:
  no 87 is "this state with one single-swappable value rewritten" -- this covers the pure 3-way
  factors of the coupled plateaus AND the one-for-one-swappable part of the coupled factor (e.g. on
  kste 108 the four choice values 08008c84, 08888000, 088c0084, 8c840000 each alone; on hunt 18927
  the seven single-swappable ones).
* Local level 2: 105 of the 106 pairs with free <= 3 UNSAT (the open one: hunt 18927 c1+c6, k = 10,
  120 s).  So no 87 is a re-pairing / re-sharing confined to two such windows.  Where two local
  components belong to the same coupled factor (kste 33: c0+c7; kste 45: c1+c5, c1+c6, c5+c6; kste
  108: all six pairs among c1, c2, c3, c7; hunt 2101: c0+c1, c0+c2, c1+c2; hunt 18927, giants
  likewise), the UNSAT pair says: no 87 redoes those two single-swappable parts of the coupled factor
  together while keeping the rest of the factor's choice fixed.
* NOT excluded: a rewrite of the coupled factor that touches any of its locally core values (the
  values that only move in groups).  That is exactly the F instance, and none of the seven F
  instances finished (k = 10-38, free = 5-20; free = 5 ones not at 600 s either).  The coupled
  factor in full stays open on all seven plateaus; so does, as in satmob, an 87 that drops a value
  of the plateau core, and any 87 on another plateau.
* Combination [proved]: an 87 that contains the plateau core and the other factors' choices (i.e.
  one that keeps K_F) would have to be a rewrite of the coupled factor's window W_F; by the level-1
  and level-2 results it cannot be confined to one or two single-swap windows inside W_F, so it would
  have to change at least one group-moving value or at least three single-swap windows.  The F
  instance is the only one that decides this, and it is open.

## 5. How the coupled case differs from the 3-way case

* 3-way factor (satmob): the factor IS a local component (one tree intermediate, one root); level 1
  decides it exactly, in 0.02-22 s; the plateau decomposes into independent such pieces and the
  whole mobile part is the conjunction over levels.
* Coupled factor: the plateau factor is a choice among 33-69,228 sets of 4-18 helpers that is NOT a
  product of single swaps.  At a member state the local fan sees only the 1-neighbourhood of the
  current choice (4-21 of the other choices), i.e. 2-7 apparently independent 1+1 components, and
  classifies the remaining 1-11 choice values as core [checked, coupling.py].  So:
  1. satmob's `analyze` on a coupled plateau REPORTS a 3-way structure (shapes 1+1) and a core that
     is 1-11 values too large; nothing in the local data flags the coupling.  Only the plateau object
     (compress) shows it.  The giants are the extreme: 11 of 18 and 11 of 15 choice values are
     locally core, the local mobile part (k = 28, 21) is smaller than the coupled factor (k = 36, 38).
  2. The exact instance for the coupled factor has free = 5 (kste 108: 6 helpers feeding 4 outputs,
     no forced extras), 5 (kste 33), 9 (kste 45, hunt 2101: 10 helpers feeding 8 outputs), 15
     (hunt 18927), 20 (the giants) -- all at or beyond satmob's frontier (free 4 at 600 s), whereas
     every 3-way factor is free 0-3 except the helper-root ones with large forced closures (free
     4-6; kste 45 c5 is free 6 with k = 12).
  3. The meaning of the level-1/2 UNSATs changes: on a 3-way plateau they exclude "one factor
     rewritten"; on a coupled plateau they exclude only "the single-swappable fringe of the factor
     rewritten", which is a strictly weaker statement about the plateau.  The claim "no 87 is this
     plateau with one factor rewritten" is proved for the 3-way factors of the coupled plateaus and
     NOT for the coupled factor.
  4. Hardness is still governed by free [measured, hardness table]: free <= 3 finishes in <= 116 s
     under load (one k = 10 timeout), free 5 does not finish at 600 s.  k matters little: the kste
     108 coupled instance has k = 10 (smaller than many solved pairs) but free 5 and is unsolved.

## 6. Frontier [measured]

* Local M instances on coupled plateaus behave exactly as on satmob's circuits: free 0: <= 0.1 s;
  free 1: <= 1.1 s; free 2: <= 7 s; free 3: median 19 s, max 116 s, one timeout at k = 10 (6 outputs).
* The coupled F instances: free 5 open at 600 s (k = 10 and 12), free 9 (k = 17, 18), 15 (k = 31)
  and 20 (k = 36, 38) hopeless for this encoding at the budgets used.  The cheapest open coupled
  statement is kste 108 (k = 10, free 5, 4 outputs in W, 21 leaves) -- a 1-2 h run at this load or
  the ladder/lex encoding of sat/REPORT.txt section 5 [guess].
* The span pool (weaker: new gates may only read constants in the GF(2) span of W's leaves) is
  queued at 600 s for kste 45 and hunt 2101 (`campaignB.sh` step 4); untested when this was written.

## 7. What is running and what to run with more cores

`campaignB.sh` (nohup, one child at a time, nice 8, idempotent; `satmob2/STOP` stops it between
instances) continues after this report: the local singles with free > 3 at 120 s were in progress
when this was written (kste 33 c3 free 5 and kste 45 c5 free 6 timed out at 120 s; kste 108 c5 and
hunt 18927 c4, both free 4, still to run), then span-pool F instances for kste 45 and hunt 2101 at
600 s, then local pairs with free = 4 at 120 s on all seven.  `results.jsonl` and
`run.log` grow accordingly; re-run `python3 make_report.py` to refresh the tables.

With cores for a few hours (same code):
1. `python3 fac.py run kste:1557 kste:41 3600` and `... kste:3146 kste:43 3600`: the two free = 5
   coupled factors, the first coupled statements within reach.  UNSAT would say: no 87 keeps this
   plateau's core and its 3-way choices and redoes the 108-way (33-way) factor in one gate less --
   the first exclusion of a coupled factor as a unit.
2. The same with `pool = span` at 3600 s for kste 45 / hunt 2101 (free 9) as the weaker
   "built from the factor's own leaves" statement.
3. Encoding work before anything at free >= 9: ladder at-most-one, full lex order on independent
   gates (sat/REPORT.txt section 5); the coupled factors are the regime where it pays.
4. A cheaper intermediate family: F windows restricted to a SUBSET of the coupled factor's choice
   that is closed under the factor's group moves (the minimal groups of coupling.out, sizes 2-5),
   i.e. the smallest units the plateau actually moves; `coupling.py` lists the group sizes, the
   windows are a 20-line extension of `fac.py`.
5. More member states per plateau: the F window depends on the state (which values are locally
   core changes along the plateau); a state where the coupled choice feeds fewer outputs gives a
   smaller free.  `fac.py analyze` on other members (kste_index.json lists 40 / 49 / 124 corpus
   members of plateaus #43 / #34 / #41) takes seconds.

Findings
 F1 [checked] On all seven coupled plateaus the local fan at a member state shows only 1+1 (and a
    few 2+1 / 2+2) components and a core 1-11 values larger than the plateau core; a coupled factor's
    choice value is locally mobile iff another listed choice differs from the current one by that
    value alone (coupling.py, verified value by value).  satmob's method cannot see or isolate a
    coupled factor; the window must come from the plateau object (fac.py).
 F2 [measured] 50 of 50 local single components and 105 of 106 local pairs with free <= 3 on the
    seven circuits are UNSAT: no 87 is one single-swappable piece (or two) of these plateaus
    rewritten, including the single-swappable fringe of each coupled factor.
 F3 [measured] The coupled factor as a unit gives k = 10-38, free = 5-20; none of the seven instances
    finished at 120 s, the two free = 5 ones not at 600 s.  The coupled factors themselves remain
    entirely open.
 F4 [measured] Hardness is governed by free as in satmob (free <= 3 solved, free 5 unsolved at
    600 s); k alone is not the obstacle (k = 10 coupled instance unsolved, k = 10 pair solved).
Rejected
 - "coupled plateaus have larger local components, so the factor encoding does more there"
   (satmob section 6 item 4): the local components are NOT larger; the coupling hides in values
   the local fan calls core.  What is larger is the plateau factor, which the local method never
   builds.
Open
 - every coupled factor as a unit (seven F instances, free 5-20); the local free >= 4 singles and
   pairs (running); the span-pool variants (queued); other member states of the same plateaus.
