# How BoolFlux came to be

BoolFlux was written on 2026-11-13 and developed over the following three days, on top of
groundwork laid on 2026-10-31. This page tells that path: what each stage tried, what failed and
with what numbers, and which decisions the failures led to. BoolFlux has no version numbers yet;
the code in [boolflux/](boolflux/) is the current state.

**Sources.** Unmarked claims can be checked in this repository: the circuits and their logs in
[circuits/](../../circuits/README.md), NIST's circuits in [seeds/](seeds/), and the code. Claims
marked † come from run records and development notes that are not part of this repository.
Circuits named here are in [circuits/aes-sbox/](../../circuits/aes-sbox/) unless a later
circuit of ours dominates them (38/4/124/14, 28/4/175/14, 31/5/119/20, 28/5/126/24,
35/3/142/19); those are in the campaign archive (not published).
Tuples are written A/AD/G/GD (ANDs, AND depth, gates, gate depth), all for the AES S-box under
NIST's counting unless stated.

## Contents

- [Timeline](#timeline)
- [Groundwork (October 31)](#groundwork-october-31)
- [Stages](#stages)
- [Three NIST pins](#three-nist-pins)
- [Failed experiments and dead ends](#failed-experiments-and-dead-ends)
- [Exact results inside stated cases](#exact-results-inside-stated-cases)
- [Decisions that shaped BoolFlux](#decisions-that-shaped-boolflux)
- [Compute](#compute)

## Timeline

| Dates (2026) | Stage | Best new results |
|---|---|---|
| Oct 31 | NIST's AES S-box circuits imported verbatim; `boolcirc`: NIST's metrics, truth-table checks, the AND skeleton | — |
| Nov 13 | first BoolFlux: gate kernel, skeleton kernel, models, CLI, independent verifier; three reviews | 23 small S-boxes at the published counts; GF(2⁴) multiplication with 9 ANDs |
| Nov 13–14 | method-and-performance study: benchmarks, ablations, a comparison with ABC | 38/4/124/14 |
| Nov 14 | AES push: exact AND-count analysis, SAT windows, joins, low depth | the first A31 circuits; 37/4/121/14; 28/4/175/14 |
| Nov 14–15 | the hub: shared archive, operators, scheduler | 33/4/112/16, 33/4/107/20; the 29/4 and 30/4 families |
| Nov 15 | structure study: algebra of the low-AND circuits, window redesigns, goal-directed runs | 28/4/131/22, 28/4/132/20; 42–47 ANDs at GD 11; 35/3/142/19 |
| Nov 15–16 | runs against ten named NIST circuits; four methods around the kernel | 32/4/114/19, 32/7/103/29, 35/3/138/23, 35/3/181/12, 38/4/135/12, 28/4/174/14 |

## Groundwork (October 31)

Before any search, the S-box circuits of NIST's
[circuit repository](https://github.com/usnistgov/Circuits/tree/master/data/slp/aes) were copied
byte for byte with a manifest, and a standard-library package, `boolcirc`, was written to read
them with full gate semantics, verify them by truth table (once from the gate list, once from the
AND skeleton) and recompute NIST's four metrics. Its counting conventions reproduce NIST's file
names and header tallies for every file ([README.md](README.md#nists-metrics)). That gave the
target to measure against before there was anything to measure.

## Stages

**Nov 13: the first BoolFlux.** The gate kernel kept XORFlux's working ideas (one chain that
never leaves the space of correct circuits, a remove-and-repair main move, neutral plateau
moves, restarts from the best) on a new core: complete truth tables, exact care sets, and 0 to 3
new gates of any two-input type ([HOW-IT-WORKS.md](HOW-IT-WORKS.md)). The skeleton kernel came
with it, for moves of several ANDs at once. Sanity cases: majority of 3 in 4 gates with 1 AND,
the full adder in 5 with 1, GF(2⁴) inversion with 5 ANDs, and GF(2⁴) multiplication from 16
ANDs to 9 (the bilinear complexity), which the gate level alone did not reach (14). 23 small
S-boxes from naive starts each reached the best published BGC or GC count, except Midori Sb1
BGC (one gate more); none beat a published count. On AES, Boyar–Peralta's 113 went to 108 and
a naive ANF of 1,247 gates to 717, both still dominated by NIST's circuits †.

Three reviews and an independent audit ran the same day and the next †:

| Review | Main findings | Fix |
|---|---|---|
| 1: kernels, ≈1,700 randomized runs | the cap penalty was not lexicographic, so a feasible best could be replaced by an infeasible one; caps and metrics checked by one implementation; the recorded hash did not pin the binary | feasibility-first ranking; the independent verifier checks caps and must agree on every metric; each run keeps its sources and binaries |
| 2: benchmark fairness | memory compared XORFlux's whole process with BoolFlux's kernel alone; repair progress lost between rounds; medians over successful runs only | measured the same way; progress kept; all runs counted |
| 3: objectives, selection, logs | `run` dropped the third objective key; `pipe` lost repairs; the no-op filter missed 81–87 % of no-ops; BUF lines failed correct circuits | one ranking everywhere (`objective.py`), repairs kept, structural no-op test, BUF excluded from counts |
| audit: own evaluator and counter | the chi3 table was bit-reversed; header tallies wrong | the chi3 circuits withdrawn, tallies fixed |

No review found a saved circuit that computes the wrong function.

**Nov 13–14: the method study** ([boolflux/bench/REPORT.md](boolflux/bench/REPORT.md), with
its plans, scripts and commands to rerun it). Four benchmark rounds on matched pinned CPUs, a
no-op A/B, ablations, a comparison with Berkeley ABC and profiling. On AES from a naive start,
the mechanism that paid was XOR-layer resynthesis from the AND skeleton: a median of 633 gates in
300 s, against 749 for local search alone. Rebuilding a circuit from its skeleton cost 31–72
gates even when nothing changed; seeding the rebuild with the parent made that exact. On good AES
circuits the skeleton search returned its input in 11 of 12 cases. ABC was worse on every target
in these gate-count models (from NIST's 104: ABC 110, BoolFlux 104). One benchmark run gave
38/4/124/14.

**Nov 14: the AES push.** Four lines of work, each with its own CPUs †:

- *Fewer than 28 ANDs, exactly.* No circuit below 28. Exact facts about the published A28
  structure, each in its case ([below](#exact-results-inside-stated-cases)).
- *SAT resynthesis of windows* at fixed caps: 0 of 3,062 windows of 4–9 gates improved, 28 % of
  the calls undecided. The encoding never asked for one AND fewer at a free gate count.
- *Joint AND/XOR moves.* Ejection chains and skeleton kicks lost to the control (median 135
  against 133; one skeleton move cost 12–42 gates on an A28 circuit). Joins at the stage
  interface worked: a sweep over 150 circuits gave 20 new Pareto points, among them the first
  A31 circuit, 31/5/119/20, the front of one A32 circuit on the back of another. In the final
  A/B, join + polish gave 17 frontier points and polish alone 3 in the same 4.7 CPU-h; all 26 join
  admissions came in the first 8.6 minutes.
- *Low gate depth.* For six published circuits, rebuilding every XOR form optimally gives the
  circuit's own GD, so lower depth needs other AND functions. A timing-driven rebuild of one XOR
  region gave 37/4/121/14; the kernel gave 28/4/175/14 from NIST's 28/4/176/14.

**Nov 14–15: the hub.** One shared archive for all operators, cells per (A, AD, GD), a bandit
scheduler ([HOW-IT-WORKS.md](HOW-IT-WORKS.md#the-hub)). It ran 65.9 CPU-h and 7,231 jobs †. All 80
frontier admissions were fewer gates under the same caps; none lowered the smallest A or AD of a
class. 138 polishes of seed circuits gave nothing: mature circuits are fixed points of the
kernel. The new 29/4 and 30/4 families came from pulls that ended one AND above their cap. The
scheduler's gain scored 51 of 75 admissions as "lowers A" because a circuit with more ANDs and
fewer gates always exists to compare with, so it was not a measure of value; and twenty identical
1-CPU-hour blocks gave 0, 1, 2 and 4 admissions in 11, 5, 3 and 1 blocks, so the 1-CPU-hour A/Bs
that chose the operators (`osc`, `gen_skel`) decided nothing.

**Nov 15: the structure study.** The low-AND circuits share one three-stage skeleton: products
spanning `N = x^17`, a GF(2⁴) inversion on functions of N, and a last layer †. A search for 27
ANDs found none. Under the maps `x -> c x^(2^i)` all A28 first-stage spans fall into one class,
so a 9 + 5 + 14 split of the 28 ANDs, found by a walk from NIST's 28/5/128/20, is one family with
the published AND-depth-4 design up to that symmetry; its circuits have at least 156 gates.
Window AND removal with a kernel grind gave 28/4/133/19 and 28/5/126/24; GD pulls, long deep
runs and joins gave 28/4/131/22 and 28/4/132/20; rank-2 products whose junk is shared between
outputs gave a GD-11 staircase down to 42 ANDs (42/4/284/11); GF(4)-coordinate moves at level 3
gave 35/3/142/19 and 35/3/143/18.

**Nov 15–16: ten NIST circuits as references.** Ten circuits of NIST's collection were chosen as
references, each with its AND count and AND depth as hard limits on every recorded result
(search states may pass above them). Four methods, each handing the kernel a start it had not
seen, made the new points ([HOW-IT-WORKS.md](HOW-IT-WORKS.md#moves-around-the-kernel)):

| Reference | Ours | Method |
|---|---|---|
| 28/4/176/14 | 28/4/174/14 | kernel stages with timing-driven rebuilds of the bottom |
| 32/4/117/19 | 32/4/114/19, 32/4/115/18, 32/4/117/17 | GF(2⁸) conjugation and staged pulls |
| 32/7/103/32 | 32/7/103/29 | conjugation and staged pulls |
| 35/3/139/27 | 35/3/138/23, 35/3/139/21 | conjugation and staged pulls |
| 35/3/183/13 | 35/3/165/13, 35/3/181/12 | re-basing of the level-3 product classes |
| 45/4/141/12 | 38/4/135/12 | shared-bottom rebuild |

Conjugate lineages took 15–40 CPU-minutes and then stopped improving †. For the references
28/4/132/22, 28/5/128/20, 34/4/139/13 and 59/4/159/10 nothing better inside their limits was
found than what the archive already held; the span-pooled SAT LNS gave one new point near the
second, 28/5/129/19. In the second day the four methods became operators with one interface
and ran for 11 hours, one reference at a time on 20 CPUs.

## Three NIST pins

Every comparison is against one pinned commit of NIST's repository, with metrics recomputed from
the files. The pin moved twice:

| Pin | Date | Forward AES S-box circuits | What changed for us |
|---|---|---:|---|
| 0876577 | Oct 29 | 70 (46 in `aes-sbox/`) | the first claims: 18 points new, fewest gates at GD ≤ 11 to 14, 18, 19 |
| e6ac0d0 | Nov 13 | 102 | NIST had published 32 more forward circuits, among them 159@10, 148@11, 141@12, 133@13, 127@14: 13 of the 18 points and the GD 11 and 12 claims withdrawn; 12 tuples new |
| 3d80774 | Nov 14 | 104 | two more forward circuits; one of our tuples, 34/4/139/13, now equals NIST's |

That correction is why every result is checked against a pinned set by `aes_check.py` before it
is reported, and why [seeds/](seeds/) records the pin.

## Failed experiments and dead ends

| When (2026) | What was tried | What happened |
|---|---|---|
| Nov 13–14 | skeleton moves to save gates on good AES circuits | input returned in 11 of 12 benchmark cases; one move costs 12–42 gates on an A28 circuit |
| Nov 13–14 | the no-op filter as a quality gain | median 133 in both arms, sign test p = 1 (kept: it saves evaluations) |
| Nov 14 | depth repair by the kernel alone | GD 14 → 13 in 2 of 35 runs, GD 13 → 12 in 0 of 10 |
| Nov 14 | SAT windows at fixed caps | 0 of 3,062 windows improved, 28 % undecided |
| Nov 14 | ejection chains, skeleton kicks | median 135 against 133 for the control |
| Nov 14 | AND distribution, union-graph mapping, exact-function splices for depth | no depth gain; 169–176-gate covers |
| Nov 14 | per-layer linear resynthesis | each layer returned at its size |
| Nov 14 | generic basis search for a product set | solves 4-bit cases, 0 of 7 on 8-bit covers |
| Nov 14–15 | kernel polish of mature circuits at their own caps | 0 changes in 52 polishes of published A28 circuits; 0 of 138 hub polishes of seeds |
| Nov 14–15 | repeated joins on one target in the hub | 3,471 jobs, 3 frontier admissions |
| Nov 14–15 | `osc` in the hub | 347 jobs, 9.5 CPU-h, 4 frontier admissions |
| Nov 15 | SAT window resynthesis on hub circuits | 0 of 1,107 windows improved |
| Nov 15 | non-tower constructions of GF(2⁸) inversion | 41–108 ANDs |
| Nov 15 | AND merge, split and flip walks toward 27 ANDs | no 27, and no A29 → A28, in 97 walks |
| Nov 15 | a goal-directed hub scheduler | no difference from the generic one in a 4-arm A/B of 0.9 CPU-h per arm |
| Nov 15–16 | conjugation on A28 starts | the identity is the best basis of every A28 start; 9 pipelines ended 5–9 gates above the archive |
| Nov 15–16 | conjugation for depth | no conjugate's skeleton depth bound is below the original's |
| Nov 15–16 | kernel and conjugates for fewer than 103 gates | 21 lineages settle at 104 |
| Nov 15–16 | generic SAT for bottom tensor rank, Brent equations, 4-input inversion | no answer in 2–18 minutes, not even for known solutions |
| Nov 16 | the 11-hour runs on the A28 and GD-10 references | no point beyond the archive |

All † except the Nov 13–14 rows ([boolflux/bench/REPORT.md](boolflux/bench/REPORT.md)) and where a circuit is named.

## Exact results inside stated cases

These were settled exactly, each inside the case stated. **None is a lower bound for the AES
S-box**: circuits outside the case are not covered. The only general bound used here is that
the AES S-box needs at least 13 ANDs †.

| Result | Case |
|---|---|
| `N = x^17` in one AND level needs exactly 9 ANDs | one level of products of affine forms in x |
| the GF(2⁴) inversion needs exactly 5 ANDs | as a function of N's 4 coordinates |
| no 12-member GF(4)-norm last layer | over three fixed published first stages, one gamma each, dim Z = rank = 4 and dim Z = 3 |
| no 13-member last layer with a 5-AND middle, no 12-member one with the 6-AND middle | over the one class of A28 first-stage spans, member model |
| no circuit with fewer than 103 gates | NIST's 32/7/103/32 with its own 9 first-level and 18 last-level ANDs, and any inversion block reading 4 linear inputs |
| GD 13 at A28 and GD 12 at A34 need other AND functions | the skeleton depth bound of every archived circuit with those A at AD 4, and of all 2,040 conjugates of 28/4/174/14 and 34/4/134/13 |
| the gate count at GD 10 is fixed | in the architecture of NIST's 59/4/159/10 |

All † (the computations are in development notes not part of this repository).

## Decisions that shaped BoolFlux

| Decision | Evidence | Since |
|---|---|---|
| complete truth tables and exact care sets, never an approximate state | no review or audit found a saved circuit with the wrong function | Nov 13 |
| feasibility first, then the keys in order, the same ranking everywhere | review 1 and review 3 | Nov 13–14 |
| two verifiers with no shared code, then placement against a pinned set | the 0876577 → e6ac0d0 correction withdrew 13 of 18 claimed points | Nov 13 |
| a run keeps its sources and binaries; settings are part of the record | a later default (the no-op filter) changes the random trajectory, so an old command alone no longer replays | Nov 13 |
| skeleton rebuild seeded with the parent | 31–72-gate penalty → 0 | Nov 13 |
| skeleton moves for AND reduction on small functions only | GF(2⁴) multiplication needs them; on AES they cost gates | Nov 14 |
| joins as an operator; their value is new starts, not steady yield | 17 against 3 frontier points, all join admissions in the first minutes | Nov 14 |
| give the kernel new starts rather than more time | mature circuits are fixed points; conjugates, re-based classes and rebuilt bottoms made every new point of Nov 15–16 | Nov 15 |
| A/B arms of at least 8 CPU-hours, judged by frontier admissions per AND class | 1-CPU-hour blocks of one configuration gave 0 to 4 admissions | Nov 15 |
| restricted exhaustive results are never stated as bounds | every exact negative above holds only in its case | Nov 15 |

## Compute

| Stage | Compute |
|---|---|
| Nov 13–14 benchmark study | 1,056 runs of 60–300 s on pinned CPUs † |
| Nov 14 hub | 65.9 CPU-h, 7,231 jobs † |
| Nov 16 runs on the references | 20 CPUs, 02:04–13:19 UTC (≈ 225 CPU-h) † |

The machine is the laptop of [search/linear/HISTORY.md](../linear/HISTORY.md#compute): an Intel
Core i7-13700H (14 cores, 20 hardware threads, 64 GB) under WSL2. Time-budgeted jobs on its
CPUs 12–19 do fewer iterations, so times across CPUs are not comparable.
