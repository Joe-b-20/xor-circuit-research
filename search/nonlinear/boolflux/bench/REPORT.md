# BoolFlux benchmark study (2026-11-13/14)

A matched-budget study of BoolFlux's mechanisms, made before the hub and the AES push
([HISTORY.md](../../HISTORY.md)). It compares XOR-only BoolFlux with XORFlux v8 on linear maps,
BoolFlux's configurations on small S-boxes and on the AES S-box, one mechanism switched off at a
time, and Berkeley ABC. How the search works is in [HOW-IT-WORKS.md](../../HOW-IT-WORKS.md).

## Setup

- **Machine**: the laptop of [circuits/SEARCH-TIME.md](../../../../circuits/SEARCH-TIME.md#hardware)
  (i7-13700H, WSL2). One worker process per CPU, pinned with `sched_setaffinity` (CPUs
  0, 2, ..., 14; ABC on 16–19). WSL's CPU topology is synthetic, so some of these CPUs may be
  efficiency cores: absolute times are not comparable across CPUs. Paired comparisons ran both
  arms back to back on the same CPU.
- **Runs**: seeds 1–5 and budgets fixed in the plan before running; seeds 6–15 added only for
  the comparisons that were unclear at n = 5. Time is wall time since the search started; start
  construction is reported separately. Every final circuit was checked by both verifiers,
  outside the budget.
- **Configurations**: `gate` = the gate kernel only; `full` = rounds of 10 s of skeleton kernel
  (20 % of the round, or an adaptive share), rebuild and gate kernel; `rebuild` = `full` with
  zero skeleton iterations (the unchanged skeleton is rebuilt, then the gate kernel).
- **Rounds**: v1 ran commit 19480fc (no-op filter off), v2 ran 1fc02c3 (no-op filter on), v3
  and v4 ran 154ded8 (repair progress kept between rounds, adaptive skeleton share; v4 = seeds
  6–15). The no-op A/B ran on the code with the structural no-op test.

## Results

### Linear maps: XOR-only BoolFlux vs XORFlux v8

Three 16-input maps (16 inputs is BoolFlux's limit), depth cap 4 or none, from the naive XOR
tree or from NIST's circuit, 120 s per run, pairs by seed on the same CPU. BoolFlux runs in exact
linear mode.

| Map | Cap | Start | Pairs | BoolFlux better / equal / XORFlux better | Sign test p | Median G BoolFlux | Median G XORFlux |
|---|---|---|---:|---|---:|---:|---:|
| joltik | 4 | naive | 10 | 6 / 3 / 1 | 0.13 | 45 | 45 |
| joltik | 4 | NIST | 10 | 2 / 8 / 0 | 0.50 | 45 | 45 |
| joltik | none | naive | 20 | 6 / 4 / 10 | 0.45 | 43 | 43 |
| joltik | none | NIST | 20 | 3 / 5 / 12 | **0.035** | 44 | 43 |
| klsw17-m-4x4-gf16 | 4 / none | both | 40 | 0 / 40 / 0 | 1 | 36 / 32 | 36 / 32 |
| small-scale-aes | 4 | naive | 10 | 2 / 7 / 1 | 1 | 44 | 44 |
| small-scale-aes | 4 | NIST | 10 | 1 / 7 / 2 | 1 | 44 | 44 |
| small-scale-aes | none | naive | 20 | 4 / 4 / 12 | 0.08 | 43 | 42 |
| small-scale-aes | none | NIST | 20 | 2 / 6 / 12 | **0.013** | 43 | 42 |

Equal at depth 4 and on klsw17; XORFlux is better on the two harder uncapped cases, significantly
from the NIST start. BoolFlux reaches easy targets faster (klsw17 36@4: 0.4 s against 2.0 s);
uncapped small-scale-aes 42 was reached in 1 of 5 runs by BoolFlux (95 s) and 5 of 5 by XORFlux
(median 34 s). Linear mode does 20,000 iterations/s on joltik against 190/s with full 65,536-input
simulation. Memory is of the same order (XORFlux 27 MB; BoolFlux kernel 2.5 MB plus a 22 MB
Python driver).

### Small targets from a naive start (60 s, seeds 1–5)

The best published counts in these libraries are in
[benchmarks/LITERATURE.md](../benchmarks/LITERATURE.md).

| Target (library) | Target value | gate: median, reached, median time | full | rebuild |
|---|---|---|---|---|
| PRESENT (BGC) | 14, best published | 14, 5/5, 0.4 s | 14, 5/5, 2.1 s | 14, 5/5, 0.2 s |
| RECTANGLE (BGC) | 12, best published | 12, 5/5, 0.0 s | 12, 5/5, 2.0 s | 12, 5/5, 0.0 s |
| ASCON (BGC) | 16, best published | 16, 5/5, 0.0 s | 16, 5/5, 2.0 s | 16, 5/5, 0.1 s |
| PRINCE (BGC) | 16, best published | 17, 2/5, 21 s | 16, 4/5, 39 s | 16, 4/5, 33 s |
| GF(2⁴) multiplication (AND count first) | 9 ANDs, the bilinear complexity | A 12, G 29, 0/5 | A 10, G 31, 2/5 | A 15, G 30, 0/5 |

v2 numbers. In v3, PRINCE reached 16 in 1/5 (full) and 2/5 (rebuild), and GF(2⁴)
multiplication reached 9 ANDs in 3/5 (full). On 4-bit S-boxes the gate kernel alone reaches the
best published counts at once. GF(2⁴) multiplication needs the skeleton moves to remove ANDs;
the gate kernel alone finds fewer gates (29) with 12 ANDs.

### AES S-box (NIST library)

Circuits are written A/AD/G/GD.

| Start (budget) | Target | gate | full | rebuild |
|---|---|---|---|---|
| naive ANF, 1,247 gates (300 s, 3 seeds) | | median 749, A 288 | 739, A 214 | **633** (best 615), A 223 |
| NIST 36/4/142/13 under its caps (120 s) | ≤ 132 | median 133; 2 of 15 runs (no-op filter off), 1 of 15 (on) | 134; 0–1 of 5 | 134; 0 of 5 |
| NIST 33/4/116/15, cap GD ≤ 14 (120 s) | GD ≤ 14, G ≤ 126 | 0 of 5 | 0 of 5 | **1 of 5: 124 gates** at 119 s |
| NIST 32/5/104/30, no cap (120 s) | ≤ 103 | 1 of 5 (33/7/103/33) | 0 of 5 | 0 of 5 |

From the naive start, rebuilding the unchanged AND skeleton with Paar's heuristic takes the ANF
circuit to about 683 gates in 5–10 s, more than 300 s of local search achieves; skeleton moves
on top make it worse, because each changes AND functions and the XOR cones around them must be
rebuilt. On good AES circuits 120 s gives 1–3 gates, all from the gate kernel; the skeleton
stage returned its input in 11 of 12 cases. The 124-gate circuit is 38/4/124/14: no NIST circuit
dominates it, neither at the pin of the time (e6ac0d0) nor at the current one (3d80774, best at
GD ≤ 14: 33/4/125/14). Our later
[37/4/121/14](../../../../circuits/aes-sbox/aes-sbox-a37-ad4-g121-gd14-xx84-36.circ.txt), found
from it, does. The 103-gate circuit is dominated by NIST's 32/7/103/32.

### Berkeley ABC

ABC commit `0587b343c45b8bd6dddd866fe4ac8e55e9cbda05`, unit-area cell libraries matching ours
([abc/genlib/](abc/genlib/)), the flows `dc2; resyn2; compress2rs`, `&deepsyn` and `&eslim`
(seeds 1–5), each followed by five mappers, the same budgets (60 s, AES 300 s), every result
verified exhaustively.

| Target (library) | ABC best | BoolFlux (naive start, 60 s / 300 s) |
|---|---|---|
| PRESENT (BGC / GC) | 24 / 20 | 14 / 13 |
| RECTANGLE (BGC / GC) | 16 / 12 | 12 / 11 |
| ASCON (BGC / GC) | 18 / 16 | 16 / 15 |
| PRINCE (BGC / GC) | 24 / 19 | 16 / 15 |
| GF(2⁴) multiplication (AND/XOR / NIST) | 37 / 36 | 29–32 |
| AES from the table (NIST) | 1,224, still improving at 300 s | 633 median (rebuild) |
| AES from NIST's 32/5/104/30 (NIST) | 110 | 104 |

ABC minimises AIG nodes and then maps to the library, so it does not optimise gate count
directly; the round trip through an AIG alone turned NIST's 104 into 110. A standard
logic-synthesis flow is not a substitute here; this does not make BoolFlux a better general
synthesiser.

### One mechanism off (gate kernel)

| Off | PRESENT (14) | RECTANGLE (12) | GF(2⁴) mult. (A, G) | AES 36/4/142/13 (median G) |
|---|---|---|---|---|
| nothing | 14, 5/5 | 12, 5/5 | 12, 29 | 133–134 |
| 2- and 3-gate replacements | **27**, 0/5 | **25**, 0/5 | 16, 34 | **141** |
| 3-gate replacements | 14, 5/5 | 12, 5/5 | 12, 29 | **137** |
| neutral (plateau) moves | 14 | 12 | 12, 30 | **136** |
| annealing | **15**, 2/5 | 12, 4/5 | **15**, 30 | 134 |
| care sets | 14 | 12 | 12, 29 | 133–134 |
| restarts | 14 | 12 | 14–15, 30 | 133–134 |
| function merging | 14 | 12 | 12, 29 | 133 |

Multi-gate replacements, neutral moves and annealing carry the search; care sets, restarts and
merging show no effect on these targets at n = 5. Without the skeleton's merge move GF(2⁴)
multiplication still reaches 9 ANDs (3/5), through swaps and deletions.

### Rebuild penalty

| Accepted skeleton moves | Rebuild from the forms alone | Rebuild seeded with the parent |
|---|---|---|
| 0 | +31 to +72 gates (104 → 152, 131 → 203, 142 → 173) | **+0** |
| 1–4 | +31 to +70 | +2 to +40 |
| 25–90 | +54 to +112 | +45 to +100 |

The penalty came from the rebuild (greedy from scratch loses the parent's XOR sharing), not
from the AND moves; seeding with the parent removed it. What remains is intrinsic: changing an
AND's function forces every XOR cone that uses its output to be rebuilt.

### Moves that change nothing

In a traced AES run (36/4/142/13 → 131, 10 improving moves) 38,099 of 43,958 accepted moves left
the circuit unchanged up to gate renumbering, and only 579 changed the AND structure. The filter
added for these (`skip_noop`, a structural test) was then compared on 36/4/142/13 under its
caps, 120 s, seeds 1–15, both arms of a seed on the same CPU:

| skip_noop | Median G | Best | G ≤ 132 | Paired against the other arm |
|---|---:|---:|---|---|
| 0 | 133 | 131 | 2 of 15 | |
| 1 | 133 | 133 | 0 of 15 | 4 better, 5 worse, 6 equal (sign test p = 1) |

No measurable effect (Fisher p ≈ 0.48 for 2/15 against 0/15). The default stays 1 because it
saves evaluations.

### Speed

| Target (start) | Gates | Kernel iterations/s | Kernel memory |
|---|---:|---:|---:|
| PRESENT (naive) | 32 | 58,000 | 2.5 MB |
| GF(2⁴) multiplication (naive) | 34 | 15,000 | 2.5 MB |
| AES (NIST 36/4/142/13) | 142 | 3,800 | 3.1 MB |
| AES (naive ANF) | 1,247 | 1,150 | 3.4 MB |

On AES most of the time goes into generating candidates (the per-move table of one-gate values
25 %, candidate search 15 %, care-set checks 12 %); the rebuild takes 3 %.

## What it means

- The gate kernel changes nonlinear structure too: in the traces it removes ANDs (majority of
  3: from 3 ANDs to 1, the optimum), rewires AND operands and replaces AND functions, every step
  exactly equivalent.
- On small S-boxes it reaches the best published counts in seconds. On AES from a naive start
  the XOR-layer rebuild is what pays; on good AES circuits the gains are small and come from the
  gate kernel, and moves on the AND skeleton, as made here, do not pay (each costs a rebuild).
- XOR-only, it matches XORFlux at depth 4 and falls behind on long uncapped searches.
- Five seeds per cell: differences of one gate are often noise.

## Rerunning

Commands from the repository root (Python 3.11+, gcc). Runs are time-budgeted, so they are not
bit-reproducible, and today's code runs the plans with today's defaults (`workflow.py`).

```bash
B=search/nonlinear/boolflux/bench
# plans v1-v3 are regenerated exactly by make_plan.py; v4 and the no-op A/B are in plans/
python3 $B/make_plan.py OUT/plan-v2.json --tag v2
python3 $B/bench.py OUT/plan-v2.json OUT/v2 --cpus 0,2,4,6,8,10,12,14
python3 $B/bench.py $B/plans/plan-v4.json OUT/v4 --cpus 0,2,4,6,8,10,12,14
python3 $B/bench.py $B/plans/plan-v5-noop-ab.json OUT/v5 --cpus 0,17,18,19
python3 $B/analyze.py OUT/v2 > OUT/tables-v2.md        # tables; pooled.py pools rounds
python3 $B/rebuild_penalty.py OUT/rebuild_penalty.json

# a worked trace (majority of 3): every accepted move, with circuits before and after
python3 search/nonlinear/boolflux/cli.py run --target maj3 --model xag --objective a,cost --iters 3000 \
    --seeds 1 --jobs 1 --out OUT/maj3 --set tracemoves=OUT/maj3/moves.txt --set skip_noop=0
python3 $B/show_trace.py OUT/maj3/moves.txt

# one configuration from the normal CLI: the GD <= 14 repair that gave 38/4/124/14
python3 search/nonlinear/boolflux/cli.py flow --target aes --model nist \
    --start search/nonlinear/seeds/aes-sbox/aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt \
    --objective cost,gd --cap-gd 14 --config full --skel-set iters=0 --adaptive --seconds 120 \
    --seeds 4 --out OUT/repair
```

ABC: build ABC at the commit above in `EXT/abc-src/`, copy [abc/scripts/](abc/scripts/) and
[abc/genlib/](abc/genlib/) into `EXT/`, then

```bash
python3 EXT/scripts/make_targets.py search/nonlinear/boolflux/benchmarks/sboxes.json EXT/targets
python3 EXT/scripts/netconv.py ncff2blif \
    search/nonlinear/seeds/aes-sbox/aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt EXT/targets/aes-nist104.blif
python3 EXT/scripts/run_all.py EXT . all       # 132 runs, about 50 min on CPUs 16-19
python3 EXT/scripts/collect.py EXT EXT/abc_results.json EXT/table.md
```
