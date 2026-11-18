# Searching for physically better circuits

XORFlux and BoolFlux optimize abstract counts: #AND (A), AND depth (AD), #gates (G) and gate depth
(GD). This study asks whether they could search for better hardware directly. It looks at what
the counts miss, whether circuits with the same counts differ in silicon, and whether a cheap
score can tell which one is better before any synthesis.

It runs the unchanged [hardware benchmark](../README.md), with the same tools, libraries,
constraints, flows and equivalence checks, on 1,457 circuits:
- the 340 published and NIST circuits;
- 937 drawn from every circuit file of our search runs;
- 180 more picked by a prospective test.

Repeated runs separate structure from noise. We don't claim the findings hold for other
libraries, corners or tools than the ones stated here.

## Results

| | Structure kept (`preserve`: one cell per gate) | Structure resynthesized (`free`, `free-area`: Yosys + ABC) |
|---|---|---|
| Do circuits with the same (A, AD, G, GD) differ physically? | **yes**: routed delay by a median 5.6% (Nangate45) and 6.5% (SKY130), up to 20% and 27%; structure explains 58–99% of the delay variance against noise | **yes**: by a median 11–14%; beyond noise in 22–30 of 40 groups |
| Are logically worse circuits physically better? | **often**: in 9–15% of dominated pairs for G < 400 (delay, area, power); 20–28% for delay with the larger circuits | **more often**: 17–38% for G < 400 |
| Does a cheap score from the circuit file predict it? | **yes**: within-group ranking ρ 0.39–0.90 on held-out circuits; it calls 80–100% of the inversions; prospective top 10 faster than the random 10 in 11 of 12 pools, significantly (by 2–11%) in 8 | **no**: within-group ρ −0.32 to +0.45, mostly near 0; for G < 400 it calls delay inversions at chance (45–54%); prospective top 10 significantly faster in 1 of 24 |
| What does predict it? | the score: a load-aware longest path from the Liberty tables, a median 1.2 ms per circuit | synthesis and timing before placement: within-group ρ 0.85–0.92, a median 0.75 s per circuit (a whole job: 15.1 s) |

Dominated pairs are pairs where one circuit is at least as good as the other in A, AD, G and GD and
better in one. They are counted only when the physical difference is beyond noise; with the
structure kept, most delay inversions among all circuits involve the 41 large machine-synthesised
S-boxes (G ≥ 400). Per library, flow and measure: [results/TABLES.md](results/TABLES.md),
"Dominance inversions beyond noise".

**Why the counts mislead.**
- **Area.** Every gate counts 1, but an inverter costs a third of an XOR2 and an AND2 two thirds
  (Nangate45: 0.53, 1.06, 1.60 µm²). Fewer ANDs at the same G means more XORs and a larger circuit.
- **Delay.** XOR2 is the slowest cell, and a gate's delay grows with the load it drives. Gate depth
  counts neither.

**Exact comparisons.** Each holds in all 6 library × flow configurations (mean of 4–6 repeated
runs, Welch p < 0.05):

| Logically worse circuit | Beats | Measure | Gain over the 6 configurations | Why |
|---|---|---|---:|---|
| S-box 57/9/152/36 (`aes-sbox-a57-ad9-g152-gd36-hb2092f6d0c4adc01`) | NIST 30/4/147/36 (`aes-sbox-a30-ad4-g147-gd36-xx117-13`) | ADP | 46–55% | 59 XOR/XNOR against 117 at the same depth: 1.51 against 2.64 ns (Nangate45, preserve) |
| S-box 68/13/176/37 (`aes-sbox-a68-ad13-g176-gd37-hdd064a2dd98cf1eb`) | S-box 28/5/172/27 (`aes-sbox-a28-ad5-g172-gd27-hb9d61cfc26a4a3bb`) | area | 22–44% | 50 of its gates are inverters, 58 XORs against 144 |
| inverse S-box 31/5/138/20 (`aes-invsbox-a31-ad5-g138-gd20-h18e16082a70397f`) | NIST 28/4/135/20 (`aes-invsbox-a28-ad4-g135-gd20-xx107-35`) | ADP | 5–20% | a less loaded critical path |
| inverse S-box 54/4/144/16 (`aes-invsbox-a54-ad4-g144-gd16-h2d9970ea050c359`) | ours 28/4/143/16 (`aes-invsbox-a28-ad4-g143-gd16-xxn115-59-1`) | power | 5–33% | ANDs instead of XORs |
| MixColumns 117@6 (`aes-mixcolumns-xor117-depth6-hac7ce23fbc1f9bb9`) | MixColumns 95@6 (`aes-mixcolumns-xor95-depth6-hfca2934f2afadbfa`) | delay | 18–34% | most outputs shallow and lightly loaded |
| InvMixColumns 351@7 (`aes-invmixcolumns-xor351-depth7-h7711bf97e4bcf`) | InvMixColumns 113@7 (`aes-invmixcolumns-xor113-depth7-h5e49d90bd57a4`) | delay | 9–37% | the same, with three times the gates |
| direction-select S-box 36/6/241/26 (`aes-sbox-sel-a36-ad6-g241-gd26-hcb958a27654d38`) | NIST 36/6/191/26 (`aes-sbox-sel-a36-ad6-g191-gd26-xx155-31`) | delay | 7–16% | |

Four of these beat a NIST circuit or a published circuit of ours. Of the 19 apparent inversions
that got repeated runs:

| Configurations where the inversion holds | Pairs |
|---|---:|
| 6 of 6 | 9 |
| 5 of 6 | 4 |
| 4 of 6 (all power) | 5 |
| 2 of 6 | 1 |

**Published circuits are rarely the physically best of their own metric class.**
- **NIST's MixColumns 88@5** ranks 1 of 10 in routed delay in all four preserve and free-area
  configurations. Ours, with the same counts, ranks between 2nd and 9th, 2.4–7.4% slower.
- **Our S-box 32/4/114/19** ranks 6 of 9 (Nangate45) and 8 of 9 (SKY130) with the structure kept,
  and 7 of 9 on both after area-oriented synthesis. There the best circuit with its counts is
  9–12% faster (ours is 10–14% slower).

The archives already hold these physically better circuits, at no gate cost.

**On SKY130, XOR/XNOR polarity changes power when the structure is kept.** Within groups,
preserve-flow power tracks the XNOR count (ρ +0.66) and the XOR count (ρ −0.65). XNOR2 costs more
power than XOR2 there, and the polarity is a free choice in both searches. After resynthesis the
effect is gone (about ±0.08), and on Nangate45 it is small (±0.13).

**The benchmark's first pair, repeated.** BoolFlux 40/4/134/12 against NIST 45/4/141/12:
- **Free-flow delay.** The losses in the benchmark's single runs are within synthesis noise:
  Nangate45 0.721 ± 0.037 against 0.734 ± 0.017 ns, SKY130 3.47 ± 0.21 against 3.42 ± 0.18 ns.
- **Free-flow area on SKY130.** Its loss persists: 1,492 ± 144 against 1,316 ± 74 µm², about 13%.
- **Structure kept.** Its advantage is robust: 0.829 ± 0.002 against 0.867 ± 0.004 ns
  (Nangate45).

All tables: [results/TABLES.md](results/TABLES.md) (noise, groups, inversions, synthesis,
agreement between configurations, prediction, the prospective test) and
[results/SEEDED.md](results/SEEDED.md) (the repeated runs). Every job's numbers:
[results/table.csv](results/table.csv), [results/seeds.csv](results/seeds.csv).

## What this means for XORFlux and BoolFlux

1. **Add a physical cost next to the counts.** Use library-weighted area and the load-aware
   longest path of [features.py](features.py): 4 cells × 2 parameters per library, read from the
   Liberty tables.
   - For circuits implemented as written, it ranks circuits with the same counts. Use it as a
     tie-break or as a Pareto dimension.
   - An incremental version only needs to update arrival times in the fanout cone of a rewrite.
   - Expected gain from selection alone: 2–11% routed delay at no gate cost, in 8 of the 12
     pools tested.
2. **Stop counting NOT like XOR.** Report NOT separately and treat XOR/XNOR polarity as free (for
   SKY130 power, prefer XOR). Give gate depth gate-type weights, or use the score's longest path
   in its place.
3. **For circuits that will be resynthesized, rank with synthesis in the loop.**
   - Keep G and GD as the search objective; across circuits of a function they still rank the
     resynthesized delay with ρ 0.54–0.93 (lowest for the S-box).
   - Re-rank the archive's circuits with the same counts by Yosys + ABC + timing, about 1 s each.
   - Take the median over 3 or more orders of the RTL statements: the order alone moves the
     result by 2–3%.
4. **Keep many structurally different circuits per metric key.** The routed-delay spread inside
   a key is a median 5.6–14%, up to 27% with the structure kept and 46% after resynthesis. The
   archives already hold thousands of structures for some keys (5,852 for MixColumns 90@4).
5. **Treat physical wins below about 7% in a resynthesized flow as unconfirmed until repeated.**
   This includes the benchmark's own single-run free-flow comparisons.
6. **Keep #AND for what it measures.** It is the right cost for masking and multi-party
   computation, not a proxy for the area of an unmasked CMOS circuit. If physical cost becomes a
   target, give it its own objective rather than reordering A, AD, G, GD.

## Method

**Inventory** ([inventory.py](inventory.py)).
- **Scope.** Every circuit file of our search runs on this machine: 625,204 files from campaign
  archives, worktrees and checkouts, in NIST's format or XORFlux's record format (624,083 when the
  sample was drawn, a day earlier).
- **Verification.** Each was checked against FIPS 197 or its matrix, with no tie to the
  benchmark's checker.
- **Deduplication.** Files were merged by a canonical hash of the gate DAG, not by their counts.
  The hash ignores names and gate order and folds constant operands (`XNOR t a 0` is `NOT t a`).
  Different topologies with equal counts stay apart.

| Function | Distinct structures | Metric keys |
|---|---:|---:|
| InvMixColumns | 313,963 | 431 |
| MixColumns | 64,407 | 381 |
| S-box | 9,108 | 2,894 |
| inverse S-box | 3,819 | 1,990 |
| S-box with direction bit | 2,730 | 1,880 |

They range from the frontier to far behind it, up to 2,557 gates. Summary:
[inventory/summary.json](inventory/summary.json).

**Sample** ([sample.py](sample.py), seed 20261118). 941 candidates drawn, 937 after removing 4
duplicates (Limitations):
- 278 in 40 *same-metric groups*: per function the 8 keys with at least 5 structures, published
  and NIST keys first, up to 8 structures each;
- 659 spread over the whole metric space: cells of (A, AD, GD, G decile) visited in turn.

The candidates are in [candidates/](candidates/), with each one's source files and provenance in
[sample.json](sample.json).

**Jobs.**
- **Settings.** The benchmark's own: Nangate45 and SKY130HD; the preserve, free and free-area flows;
  placement, routing, extraction.
- **Checks.** Exhaustive simulation (S-boxes) and a formal proof at the RTL, mapped and routed
  stages, plus 0 DRC errors.
- **Totals.** 10,187 jobs (6,647 base, 3,540 repeated); all of them passed. The harness
  ([harness.py](harness.py), [run.py](run.py)) changes no setting. It only reads candidate files
  and writes to its own build folder.

**Noise.** 136 circuits got repeated runs, chosen by a fixed rule ([select_seeds.py](select_seeds.py)):
whole same-metric groups, the first pair, and the largest apparent inversions. The largest
inversions are the apparent wins most likely to be noise. The groups include their
prospective-test members: 19 of the 29 in MixColumns 90@4. Two more circuits (InvMixColumns 118@5)
got repeated runs while the seeds were being tested, so the repeated runs cover 138.

| Seed type | What changes | Delay CV |
|---|---|---:|
| Placement, 3 seeds | RePlAce's parameters around their defaults. Instance order and pin seeds alone leave this OpenROAD's output byte-identical. | 0.2–0.7% |
| Synthesis, 2 seeds | RTL statements shuffled (free flows). Area moves too: median CV 0.5–3.2%, 90th percentile up to 8%. | 2–3% |

A difference counts as beyond noise when it exceeds 2√2 × the median CV of its library, flow and
measure. For a group's range, the threshold is the 95% quantile of the range of that many
noise-only copies.

**Features and scores** ([features.py](features.py)). Computed from the circuit file alone, in a
median 1.2 ms per circuit for all of them on both libraries ([results/timing.json](results/timing.json)):
- **Counts:** A, AD, G, GD and the gate-type counts.
- **Fanout and input load.**
- **Output-depth balance and slack.**
- **Operand imbalance, reconvergence and sharing.**
- **Three zero-fit scores per library:**
  - a load-aware longest path: each gate costs intrinsic + slope × load, both fitted from the cell's
    Liberty delay tables, load being the input capacitance of its fanout cells;
  - the sum of cell areas;
  - a switching estimate: toggle probability × load, the toggle probability exact from the truth
    table.

Mapped-netlist features (cell mix, depth in cells, a canonical netlist hash) and wiring come from
the job outputs ([collect.py](collect.py)), for explanation only.

**Prediction** ([analyze.py](analyze.py)). Held out by a hash split, with each same-metric group
kept whole on one side. The comparisons:
- the counts;
- the zero-fit scores;
- a ridge model on 28 features;
- the same ridge model trained on four functions and tested on the fifth.

The ridge model ranks worse than the zero-fit score within groups (ρ 0.11–0.57): it learns the
differences between groups. Fanout, reconvergence, sharing and balance statistics on their own
track delay weakly (|ρ| < 0.3).

**Prospective test** ([screen.py](screen.py)).
1. **Pools.** The 2 largest same-metric pools of each function that has pools of at least 200
   structures (MixColumns 90@4 and 91@4, InvMixColumns 132@5 and 130@5, S-box 28/5/129/19 and
   28/4/132/21), minus every circuit already benchmarked.
2. **Scoring.** All 64,876 structures in them were scored with the longest-path score for
   Nangate45, fixed before any of them was benchmarked.
3. **Picks.** The 10 best-scored, 10 worst-scored and 10 random structures of each pool were
   benchmarked: 180 circuits ([screen.json](screen.json)).
4. **Tests.** One-sided Mann-Whitney, Holm-corrected over all 144 tests (6 pools × 2 libraries ×
   3 flows × 4 measures).

## Limitations

- **Tools and conditions.**
  - One OpenROAD build (March 2024), the typical corner only.
  - No power grid, no timing repair or sizing in placement and routing.
  - Fixed 40% utilisation; X1 cells in the preserve flow.
- **Power.** It is zero-delay power: glitches are not counted, which favours deep circuits.
- **Large circuits.** The 41 with G ≥ 400 (mostly machine-synthesised S-boxes) ran on Nangate45
  and SKY130 preserve only (3 of them also SKY130 free-area): their SKY130 free-flow routing takes
  30–60 min per job.
- **Noise model.** The seeds are perturbations, not replicas, and synthesis noise covers statement
  order only. The thresholds use median CVs, so some circuits are noisier than the threshold assumes.
- **Hash version.** The sample was drawn with a first structure hash that did not fold constant
  operands; the candidate names carry those hashes. The 4 candidates that copied published circuits
  under the folded hash are marked in `results/table.csv` (`dup_of`) and left out of every analysis.
- **Hash collisions.** The hash can still merge two DAGs that differ only in which of two identical
  duplicate gates feeds a consumer, when their fanouts agree.
- **Pool.** Only circuit files of this machine. Gzipped BoolFlux event logs were not parsed. The
  inverse and direction-select S-boxes have small same-metric groups (at most 20 and 7
  structures), so no prospective pools.
- **Seed selection.** [select_seeds.py](select_seeds.py) ran once, on the base run before the 41
  larger circuits had finished; [lists/seeds.txt](lists/seeds.txt) is that choice.
- **Statistics.** Only the prospective test is corrected for multiple comparisons. The other
  tables show distributions.

## Run

```bash
bash hardware/research/run_all.sh
```

It takes about 5 hours on 19 cores, after `hardware/tools/install.sh`. The inventory, the sample
and the prospective pools need the local campaign archives. They were run once, and their outputs
are committed (`candidates/`, `sample.json`, `screen.json`, `lists/`, `inventory/summary*.json`),
so a fresh checkout starts from the benchmark jobs. Build outputs (netlists, DEF, SPEF, reports,
logs; 5.9 GB) go to `hardware/research/build/` and are not committed. Tests of the structure hash:

```bash
python3 -m unittest discover -s hardware/research/tests -t hardware/research
```

## Files

| Path | What is in it |
|---|---|
| [run_all.sh](run_all.sh) | the whole study, in order |
| [inventory.py](inventory.py), [inventory/](inventory/) | the inventory and its summaries (the pools are local only) |
| [sample.py](sample.py), [sample.json](sample.json), [candidates/](candidates/) | the sample: every candidate, its source files and provenance |
| [screen.py](screen.py), [screen.json](screen.json), [candidates/screen/](candidates/screen/) | the prospective test: pools, scores, picks |
| [select_seeds.py](select_seeds.py), [lists/](lists/) | the circuits of each run |
| [harness.py](harness.py), [run.py](run.py) | running the unchanged benchmark, with optional noise seeds |
| [features.py](features.py) | features and scores from the circuit file |
| [collect.py](collect.py), [analyze.py](analyze.py), [seeded.py](seeded.py), [tables.py](tables.py), [timing.py](timing.py) | the data, the analyses, the tables, the scores' cost |
| [results/](results/) | every job (`table.csv`, `seeds.csv`), the analyses (`analysis.json`, `seeded.json`, `timing.json`) and their tables (`TABLES.md`, `SEEDED.md`) |
| [tests/](tests/) | tests of the structure hash |
