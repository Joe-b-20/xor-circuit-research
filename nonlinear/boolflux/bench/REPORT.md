# BoolFlux: method and performance (local review, 2026-11-13)

Branch `boolflux-2026-11-13`, nothing published. How the code works is in
[MECHANICS.md](MECHANICS.md) (reused / replaced / new, state, candidates, correctness, acceptance,
repair, restarts, coordination, with file and line references); reproduction in
[REPRODUCE.md](REPRODUCE.md). Independent reviews: `review/REVIEW.md` (kernels, earlier) and
`review2/REVIEW2.md` (this round's changes, benchmark fairness, this method description).

## 1. Summary

**Demonstrated**
- The search changes nonlinear structure, not only XOR layers: worked traces below show ANDs
  removed (majority: 3 -> 1), AND operands rewired and AND functions replaced on a real AES
  improvement, with every intermediate circuit exactly equivalent.
- Small S-boxes from a naive ANF start reach the best published bitslice/gate counts in about
  0-2 s per seed (PRESENT 14, RECTANGLE 12, ASCON 16; PRINCE 16 in 1-4 of 5 seeds in 60 s).
- On AES from a naive start, global XOR-layer resynthesis (rebuild from the AND skeleton with
  Paar's heuristic) is the mechanism that pays: median 633 gates in 300 s vs 749 for local search
  only and 739 when skeleton moves are added.
- XOR-only BoolFlux in exact linear mode is competitive with XORFlux v8 on 16-input linear maps
  (same start, same CPU, 120 s): equal at depth 4 and on klsw17, faster to easy targets, and
  significantly behind on two uncapped cases from the NIST start (section 4.1).
- Against Berkeley ABC (unit-area genlibs, matched budgets) BoolFlux is clearly better in these
  gate-count models on every target (section 4.4).
- Fixed in this round, with before/after measurements: the 31-72-gate AES rebuild penalty (an
  unchanged skeleton now rebuilds to exactly the parent), no-op neutral moves (the first filter
  missed most of them; see section 7), exact linear mode
  (107x faster on 16-input linear maps), start construction (3.3 s -> 0.6 s), Paar speed, and
  four benchmark-driver faults found by the reviewer.

**Limitations**
- On good AES circuits the gate search gives 1-3 gates in 120 s and the skeleton stage contributes
  nothing (its output is the input skeleton in 11 of 12 AES cases). One benchmark run produced a
  new published-set point (124 gates at GD 14, A38, section 4.3).
- Depth repair is slow: 116@GD15 -> GD 14 reached GD 14 in 2 of 35 runs of 120 s (129 gates in v1,
  124 gates in v3; only the 124 is below the published 127); the earlier success needed 3 rounds x
  300,000 iterations x 8 seeds.
- Complete truth tables limit BoolFlux to 16 inputs (linear mode is exact only for XOR-only
  libraries); per-candidate re-simulation makes it slow on 1,000+ gate circuits (1,150 it/s).
- Five seeds per cell (fifteen where expanded): differences of one gate are often within seed noise.
- The no-op filter, which the traces motivated, has no measurable quality effect, also after it was
  repaired (section 7: the first version missed most no-ops).

**Hypotheses (not established)**
- An in-place skeleton move (swap one AND and repair its XOR fan-out locally) would make
  AND-structure moves useful on good AES circuits.
- Interleaving Paar resynthesis into long gate runs would improve naive starts further.
- XORFlux's advantage on uncapped linear maps comes from its LNS and long plateau walks, which
  BoolFlux's at-most-3-gate replacements do not reproduce.

## 2. Worked traces

(Files in the bundle `traces/`; produced by the kernel's `tracemoves` log and
`bench/show_trace.py`; every before/after pair verified on all inputs.)

**Majority of 3 (xag, objective AND count then gates; naive start 5 gates, 3 AND).**
- it 7, `resub3`, target `s5 = XOR(AND(x0,x2), AND(x1,x2))`, care set 8/8, MFFC 3 gates: replaced
  by `AND(x2, XOR(x0,x1))` (2 gates; found by the level-2 "op2 root" search, distributivity):
  5 gates/3 AND -> 4/2.
- it 227 (after an annealing step back to 5 gates/2 AND), `resub3`, target `s4 = AND(x0,x1)`,
  care set **4/8**: on those 4 inputs it equals `x1`, so it is replaced by `XOR(XOR(x1,x0),x0)`,
  which the rebuild's function merging collapses to the input `x1`; the XOR logic re-routes to
  `((x1^x2) & (x0^x1)) ^ x1`: 4 gates/1 AND (the optimum, MC 1).

**AES, NIST a32-ad5-g109-gd20 -> 108 (one move, seed 7, it 19189).** The target
`s105 = XNOR(s103, s104)` with its 3-gate MFFC (an XNOR, an XOR reading an AND output, an XNOR)
is replaced by `XNOR(XOR(s73, s101), s83)`: the AND gates are untouched; their outputs are
recombined by a cheaper XOR cone. A deterministic replay reproduces the move exactly.

**AES, NIST a36-ad4-g142-gd13 -> 131 (10 improving moves, seed 3).** 8 moves are XOR-cone
recombinations; it 6014 rewires an AND (`s65 = AND(s52, s64)` matters on 136/256 inputs and becomes
`AND(s59, s52)`, freeing one XOR); it 57644 replaces a 3-gate cone that contained an AND by
`AND(XOR(s6, s89), s73)`, a new AND function. Of the 43,958 accepted moves, 38,099 left the circuit
unchanged up to gate renumbering (no-ops the first `skip_noop` filter missed; review 3 M4). Of the
10,850 that targeted an AND gate 10,521 were such no-ops, and of the 15,710 that inserted an AND
15,131 re-created the same AND: 579 accepted moves actually changed AND structure. The AND count
stays at its cap (36).

## 3. Rebuild penalty (skeleton -> gates)

| accepted skeleton moves | rebuild from forms only | rebuild seeded with the parent (new) |
|---|---|---|
| 0 | +31 to +72 gates (104 -> 152, 131 -> 203, 142 -> 173) | **+0** (exact) |
| 1-4 | +31 to +70 | +2 to +40 |
| 25-90 | +54 to +112 | +45 to +100 |

The systematic part was the rebuild algorithm (forms rebuilt greedily from scratch lose the
parent's sharing), not the AND moves; the seeded rebuild removes it. What remains is intrinsic to
changing an AND's function: every XOR cone that combined its output must be rebuilt. On AES no
skeleton move lowers K + 0.02 E, so the skeleton kernel almost always returns its input.

## 4. Benchmarks

Machine: Intel i7-13700H (WSL2 shows 10 cores x 2 threads), one worker process per physical core
(CPUs 0,2,...,14) pinned with `sched_setaffinity`; all of a run's work (Python driver included) on
its CPU; linear-map pairs run back to back on the same CPU. Seeds 1-5 and budgets fixed before
running; seeds 6-15 added only for the two unclear comparisons. Time = wall seconds since the
search started; start construction is reported separately; final circuits verified by both
verifiers outside the budget. Rounds: **v1** = kernel at 3a71f0f; **v2** = no-op filter, fast
starts (all BoolFlux and XORFlux runs repeated); **v3** = corrected driver for the full
configuration (repair progress kept, variant choice by feasibility, round-matched adaptive
skeleton share); **v4** = 10 extra seeds for the unclear comparisons.

Precisely: v1 ran code 19480fc with `skip_noop 0` (fast starts and seeded rebuild already in, old
Paar); v2 ran 1fc02c3 with `skip_noop 1` plus the `rebuild` configuration; v3 and v4 ran 154ded8.
Per-run data (trajectory, final circuit, overhead, memory, CPU) and the tables are in the bundle
(`data/`); `bench/analyze.py` and `bench/pooled.py` regenerate the tables.

### 4.1 Linear maps: XOR-only BoolFlux vs XORFlux v8

Three 16-input maps (BoolFlux keeps complete truth tables, so 16 inputs is its limit), depth cap 4
or none, two starts (the naive per-row XOR tree, 72/72/92 gates; NIST's published circuit), 120 s
per run, model `xor`. BoolFlux runs the gate kernel in exact linear mode (`linear 1`). Paired by
seed and round, same CPU, back to back (rounds v1, v2 and, for the uncapped cases, v4 seeds 6-15).

| map | cap | start | pairs | BoolFlux better / equal / XORFlux better (G, then GD) | sign test p | median G BoolFlux | median G XORFlux |
|---|---|---|---|---|---|---|---|
| joltik | 4 | naive | 10 | 6 / 3 / 1 | 0.13 | 45 | 45 |
| joltik | 4 | NIST | 10 | 2 / 8 / 0 | 0.50 | 45 | 45 |
| joltik | none | naive | 20 | 6 / 4 / 10 | 0.45 | 43 | 43 |
| joltik | none | NIST | 20 | 3 / 5 / 12 | **0.035** | 44 | 43 |
| klsw17-m-4x4-gf16 | 4 / none | both | 40 | 0 / 40 / 0 | 1 | 36 / 32 | 36 / 32 |
| small-scale-aes | 4 | naive | 10 | 2 / 7 / 1 | 1 | 44 | 44 |
| small-scale-aes | 4 | NIST | 10 | 1 / 7 / 2 | 1 | 44 | 44 |
| small-scale-aes | none | naive | 20 | 4 / 4 / 12 | 0.08 | 43 | 42 |
| small-scale-aes | none | NIST | 20 | 2 / 6 / 12 | **0.013** | 43 | 42 |

Targets = the repository's best known circuits (44@4, 42 uncapped for joltik and
small-scale-aes; 36@4, 32 for klsw17), found by XORFlux campaigns of hours.

- **Quality**: equal at depth 4 and on klsw17; XORFlux is better on the two harder uncapped cases
  (significantly from the NIST start). Neither tool reached joltik's best known 44@4 more than
  2/5 times in 120 s.
- **Time to target** (v2, median over the runs that reached it): klsw17 36@4 0.4 s vs 2.0 s;
  small-scale-aes 44@4 from naive 43 s (5/5) vs 32 s (4/5); best+2 targets are reached by both
  in 0-20 s; uncapped small-scale-aes 42: BoolFlux 1/5 (95 s) vs XORFlux 5/5 (34 s).
- **Speed**: BoolFlux's kernel does ~20,000 iterations/s on joltik in linear mode and ~190/s with
  full 65,536-pattern simulation (107x); the benchmark uses linear mode.
- **Memory**: XORFlux's process ~27 MB; BoolFlux's kernel 2.5 MB plus its Python driver ~22 MB:
  the same order (the earlier "10x" reading counted only the kernel; review2 C1).
- **Overhead**: start construction 0.24-0.34 s (both tools get the same start; BoolFlux before
  the start-construction fix took 3.3 s on 16 inputs), XORFlux start-up ~0.5 s, BoolFlux kernel
  start-up 6 ms; verification of the final circuit (outside the budget) ~2 s (65,536 inputs).

### 4.2 Small nonlinear targets from naive starts (60 s, seeds 1-5)

Configurations: `gate` = gate kernel only; `full` = rounds of 10 s: skeleton kernel (20 % of the
round; adaptive and round-matched in v3) + rebuild (seeded and from forms, best kept) + gate kernel;
`rebuild` = the same with zero skeleton iterations (rebuild of the unchanged skeleton + gate kernel).
v2 numbers (v3 full/rebuild in brackets where different).

| target (model) | target value | gate: final median, reached, median time | full | rebuild |
|---|---|---|---|---|
| PRESENT (bgc) | 14 (best published) | 14, 5/5, 0.4 s | 14, 5/5, 2.1 s | 14, 5/5, 0.2 s |
| RECTANGLE (bgc) | 12 (best published; opt in [11,12]) | 12, 5/5, 0.0 s | 12, 5/5, 2.0 s | 12, 5/5, 0.0 s |
| ASCON (bgc) | 16 (best published; opt in [12,16]) | 16, 5/5, 0.0 s | 16, 5/5, 2.0 s | 16, 5/5, 0.1 s |
| PRINCE (bgc) | 16 (best published, heuristic) | 17, 2/5, 21 s | 16, 4/5, 39 s (v3: 17, 1/5) | 16, 4/5, 33 s (v3: 17, 2/5) |
| GF(2^4) mult (xag, AND count first) | A = 9 (bilinear complexity) | A 12, G 29, 0/5 | A 10 (v3: 9), G 31, 2/5 (v3: 3/5), 7-12 s | A 15, G 30, 0/5 |

- On 4-bit S-boxes the gate kernel alone reaches the published bests almost immediately; the
  skeleton stage only delays (it runs first).
- GF(2^4) multiplication needs the skeleton moves to reduce ANDs (rebuild only: 0/5; with moves:
  2-4/5 in 60 s, counted from the final circuits; review 3 M3); gate-only finds fewer total gates (29) but with 12 ANDs.
- PRINCE: 1-4 of 5 seeds reach 16 in 60 s depending on round and configuration; no configuration
  is reliably better at n = 5.

### 4.3 AES S-box (NIST model)

| start (budget) | target | gate | full | rebuild |
|---|---|---|---|---|
| naive ANF, 1247 G (300 s, 3 seeds) | - | median 749 (v1 768), A 288 | 739 (v1 729, v3 758), A 214 | **633** (v3 637, best 615), A 223 |
| NIST a36-ad4-g142-gd13 under its caps (120 s) | <= 132 (below every published circuit within A36 AD4 GD13) | 133-134; 2/5 (v1), 0/5 (v2); 10 more seeds (15 in all: v1/v2 s1-5 + v4 s6-15, mixing code 19480fc and 154ded8): 2/15 (skip_noop 0), 1/15 (skip_noop 1) | 134; 0-1/5 | 134; 0/5 |
| NIST a33-ad4-g116-gd15, cap GD <= 14 (120 s) | GD <= 14 and G <= 126 | 0/5 (v1: 1/5 feasible, at 129 gates; v2: none feasible) | 0/5 (none feasible) | v3: **1/5, 124 gates** at 119 s |
| NIST a32-ad5-g104-gd30, no cap (120 s) | <= 103 | v1: 1/5 reached 103 (A33 AD7 GD33; dominated by NIST's 103@GD32) | 0/5 | 0/5 |

- From the naive start the decisive mechanism is the XOR-layer resynthesis: rebuilding the
  unchanged skeleton with Paar's heuristic takes the 1247-gate ANF circuit (1128 after the kernel's
  start clean-up, review 3 m3) to ~683 gates in 5-10 s (first rebuild; 8-13 s of rebuild per run), more than 300 s of local search achieves (749); skeleton moves on top make it worse
  (739-758), because each move changes AND functions and the rebuild cost of that dominates.
- On good AES circuits the gains in 120 s are 1-3 gates and come from the gate kernel; the
  skeleton stage returns its input (11/12 cases) and only costs time (24 s per 120 s run with the
  fixed share, 12 s with the adaptive share).
- The GD <= 14 repair from 116@GD15 succeeded once (rebuild configuration, v3, seed 4): 124 gates,
  A38 AD4, verified by both verifiers, not dominated by any of the 102 published circuits and 3
  gates below the best published G at GD <= 14 (127). It is a time-budgeted run (not
  bit-reproducible); it is in `results/aes/` with its provenance.

### 4.4 External comparator: Berkeley ABC

ABC commit `0587b343c45b8bd6dddd866fe4ac8e55e9cbda05`, unit-area genlibs matching our models,
flows `dc2/resyn2/compress2rs`, `&deepsyn`, `&eslim` and five mappers, same budgets, CPUs 16-19,
every result verified (`bench/abc/ABC.md`).

| target (model) | ABC best | BoolFlux (60 s / 300 s, naive start) |
|---|---|---|
| PRESENT (bgc / gc6) | 24 / 20 | 14 / 13 |
| RECTANGLE (bgc / gc6) | 16 / 12 | 12 / 11 |
| ASCON (bgc / gc6) | 18 / 16 | 16 / 15 |
| PRINCE (bgc / gc6) | 24 / 19 | 16 / 15 |
| GF(2^4) mult (xag / nist) | 37 / 36 | 29-32 |
| AES from the table (nist) | 1224 (still improving at 300 s) | 633 median (rebuild), 749 (gate) |
| AES from NIST's 104 (nist) | 110 | 104 (no worse than the start; 103 at higher depth once) |

ABC optimises AIG nodes and then maps to the library, so it does not optimise our gate count
directly; the comparison shows that a standard logic-synthesis flow is not a substitute here, not
that BoolFlux is a better general synthesiser.

### 4.5 Ablations (gate kernel, one mechanism off; v1 and v2 agree within one gate)

| mechanism off | PRESENT (14) | RECTANGLE (12) | GF(2^4) mult (A, G) | AES a36 (median G, 120 s) |
|---|---|---|---|---|
| none (baseline) | 14, 5/5 | 12, 5/5 | A 12, G 29 | 133-134 |
| 2- and 3-gate replacements | **27**, 0/5 | **25**, 0/5 | A 16, G 34 | **141** |
| 3-gate replacements | 14, 5/5 | 12, 5/5 | A 12, G 29 | **137** |
| plateau (neutral) moves | 14 | 12 | A 12, G 30 | **136** |
| annealing (uphill moves) | **15**, 2/5 | 12, 4/5 | **A 15**, G 30 | 134 |
| care sets (ODC) | 14 | 12 | A 12, G 29 | 133-134 |
| restarts | 14 | 12 | A 14-15, G 30 | 133-134 |
| function merging (fraig) | 14 | 12 | A 12, G 29 | 133 |

Skeleton level (full configuration): without the merge move GF(2^4) still reaches 9 ANDs (3/5),
through swaps and deletions; seeded vs unseeded rebuild makes no difference on these targets
(the seeded rebuild matters when the input skeleton is kept, section 3).

### 4.6 Speed, memory, overhead

| target (start) | gates | kernel iterations/s | kernel RSS |
|---|---|---|---|
| PRESENT (naive) | 32 | 58,000 | 2.5 MB |
| GF(2^4) mult (naive) | 34 | 15,000 | 2.5 MB |
| AES (NIST a36 g142) | 142 | 3,800 | 3.1 MB |
| AES (naive ANF) | 1247 | 1,150 | 3.4 MB |
| joltik (linear mode / full simulation) | 72 | 20,400 / 190 | 2.5 / 29 MB |

Profile (gprof, AES a36, 20,000 iterations): building the per-move table of one-gate values 25 %,
candidate search 15 %, care-set equality checks 12 % (650 M calls, mostly the sampled
nonlinear-root scans), rebuild 3 %: the time goes into candidate generation.
Overheads (medians): start construction 0-0.3 s; skeleton extraction < 1 ms; rebuild 0.01-0.2 s per
round (AES ANF ~1-3 s); kernel start-up 5-30 ms; final verification 0.05-2 s (outside budgets).
Python driver ~22 MB (up to ~55 MB on AES ANF rebuilds).

## 5. Weaknesses found and what was done

| weakness (evidence) | fix | effect (measured) |
|---|---|---|
| rebuild from forms loses the parent's XOR sharing: +31 to +72 gates with no skeleton change | seeded rebuild (`synthesize(parent=)`) | unchanged skeleton rebuilds exactly (+0); after 1 move +0 to +19 |
| skeleton kernel returns the input on AES, its 20 % share is wasted | adaptive share (v3) | skeleton time 24 s -> 12 s per 120 s run; AES results unchanged (134) |
| repair progress discarded between rounds (review2 M1) | keep the last circuit while nothing is feasible (v3) | GD<=14 repair: 0/5 -> 1/5 in the rebuild configuration (124 gates) |
| neutral moves that rebuild the identical circuit (trace) | `skip_noop` (structural test from review 3) | first version missed 81-87 % of no-ops (review 3 M4); repaired filter: no measurable quality effect (section 7) |
| full truth tables make XOR-only searches slow (190 it/s at 16 inputs) | exact linear mode | 107x faster; competitive with XORFlux |
| start construction 3.3 s and verification ~20 s at 16 inputs | bitset Moebius, Gray-code tables, string-based conversions | 0.3 s and ~2 s |
| Paar recount per substitution | incremental pair counts (identical output, review2: 5,082 cases) | 1.2-2.6x on rebuilds |
| benchmark driver: GIL contention across threads, kernel-only memory figure, medians over feasible runs only, unmatched rebuild rounds | one pinned process per CPU; driver memory measured; counts shown; round-matched rounds | (reporting fixes) |


## 6. Review bundle

`~/xs-campaigns/2026-11-13-boolflux/review-bundle/boolflux-review-bundle/` (and `.tar.gz` next to
it), built by `bench/make_bundle.sh`: `src/` (the package at the bundle's commit), `configs/` (plans,
models, kernel defaults), `traces/` (rendered traces, move logs, before/after circuits), `data/`
(every run's JSON and final circuit, tables v1-v3, pooled comparison, rebuild-penalty data),
`abc/` (comparator scripts, genlibs, circuits, results), this report, MECHANICS.md, REPRODUCE.md.

## 7. Review 3 corrections (2026-11-14)

An independent audit of objectives, incumbents, worker selection, clean-up costs, BUF accounting,
timing, logging and these numbers (`review3/REVIEW3.md`, with reproductions and a resolution
table; regression tests in `tests/test_review3.py`) found six major and twelve minor problems.
None made a saved circuit wrong. Effects on this report:

- Tables v1-v4 regenerated from the same run data: success now counts the final verified
  circuit (rebuild-stage gains were missing from trajectories), and "best" columns use each run's
  objective. Changed cells: GF(2^4) mult unseeded 3/5 -> 4/5 (v2) and 2/5 -> 3/5 (v3); `a,cost`
  rows now show the best circuit by (A, cost).
- Section 2's trace statistics: 38,099 of 43,958 accepted moves were renumbered no-ops; 579 changed
  AND structure.
- Depth repair 116@GD15 -> GD 14: 2 of 35 runs reached GD 14 (129 and 124 gates), not 1.
- The no-op filter compared raw gate lists, but `rebuild` renumbers gates, so most no-ops passed.
  The structural test now rejects them all (0 renumbered no-ops accepted on maj3, PRESENT, AES).
  Repeated A/B with the repaired kernel (plan `bench/plans/plan-v5-noop-ab.json`; NIST a36-ad4-g142-gd13
  under its caps, 120 s, seeds 1-15, the two arms of a seed on the same CPU):

  | skip_noop | median G | best | G <= 132 | paired vs the other arm |
  |---|---|---|---|---|
  | 0 | 133 | 131 | 2/15 (at 36 s, 76 s) | |
  | 1 | 133 | 133 | 0/15 | 4 better, 5 worse, 6 equal (sign test p = 1) |

  Still no measurable effect; the default stays 1 (it removes wasted evaluations), and the
  difference in G <= 132 counts (2/15 vs 0/15) is within noise (Fisher p ~ 0.48).
- Ranking is now exactly lexicographic and feasibility-first everywhere (kernel `lex`, cli,
  workflow, analyze), so `pipe` and `flow` keep repair progress; `cli.py flow` reproduces the
  benchmark workflows (REPRODUCE.md).

