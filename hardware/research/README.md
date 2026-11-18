# Searching for physically better circuits

XORFlux and BoolFlux optimize abstract counts: #AND (A), AND depth (AD), #gates (G) and gate depth
(GD). This study asks whether they could search for better hardware directly. It looks at what
the counts miss, whether circuits with the same counts differ after placement and routing, and
whether a cheap score can tell which one is better before any synthesis.

It runs the unchanged [hardware benchmark](../README.md), with the same tools, libraries,
constraints, flows and equivalence checks, on 1,457 circuits:
- the 340 published and NIST circuits;
- 937 drawn from every circuit file of our search runs;
- 180 more picked by a prospective test.

Repeated runs separate structure from noise. Every physical number here is a model: OpenROAD's
placement and routing and OpenSTA's timing and power on Nangate45 and SKY130HD, typical corner,
with the benchmark's constraints. We don't claim the findings hold for other libraries, cells,
corners, constraints or tools.

## Results

| | Structure kept (`preserve`: one cell per gate) | Structure resynthesized (`free`, `free-area`: Yosys + ABC) |
|---|---|---|
| Do circuits with the same (A, AD, G, GD) differ physically? | **yes**: routed delay by a median 5.6% (Nangate45) and 6.5% (SKY130), up to 20% and 27%; the circuit explains 58–99% of a run's delay variance against placement noise | **partly**: by a median 11–14%, beyond noise in 15–27 of 40 groups; but the circuit explains a median of only 18–42% of a run's delay variance against statement-order noise |
| Are logically worse circuits physically better? | **often**: in 9–15% of dominated pairs for G < 400 (delay, area, power); 19–28% for delay with the larger circuits, 11–24% without the pairs whose jobs have electrical violations | **more often**: 16–38% for G < 400 |
| Does a cheap score from the circuit file predict it? | **yes**: within-group ranking ρ 0.39–0.90 on held-out circuits; it calls 80–100% of the inversions; prospective top 10 faster than the random 10 in 11 of 12 pool × library tests, significantly in 8 | **no**: the tested file-derived scores did not reliably predict the within-group ranking after resynthesis (ρ −0.32 to +0.45, mostly near 0; for G < 400 they call delay inversions at chance, 47–58%); prospective top 10 significantly faster in 1 of 24 |
| What does predict it? | the score: a load-aware longest path from the Liberty tables, about 1 ms per circuit | **little can**: synthesis and timing before placement predict the routed delay of the same synthesis run (within-group ρ 0.83–0.97), but that of other RTL statement orders only with ρ 0.28–0.47, about what a whole routed run of the same orders achieves (0.30–0.46). Cost: a median 1.0 s of CPU per circuit, library and flow and order (a whole job: 15.1 s of wall time at 19 parallel jobs) |

Dominated pairs are pairs where one circuit is at least as good as the other in A, AD, G and GD and
better in one. They are counted only when the physical difference is beyond noise. With the
structure kept, most delay inversions among all circuits involve the 41 large machine-synthesised
S-boxes (G ≥ 400), and many of those rest on jobs whose critical path has a slew or capacitance
violation (Electrical checks below): without the pairs that involve a violating job, the shares
fall from 19% to 11% (SKY130) and from 28% to 24% (Nangate45). Per library, flow and measure: [results/TABLES.md](results/TABLES.md), "Dominance
inversions beyond noise".

**After resynthesis, the statement order matters more than the structure.** Within a metric class,
the circuits' routed delays after Yosys + ABC differ less than one circuit's delay differs
between RTL statement orders (2–3.5%; 3–13 times the placement noise): the circuit explains a
median of 18–42% of a run's delay variance. So a
resynthesized ranking from one run, of any kind, predicts another order's ranking only weakly
([results/SEEDED.md](results/SEEDED.md), "Does the synthesis-stage delay of some orders predict
the routed delay of others?"). Across circuits of different counts the same predictors work well
(ρ 0.88–0.98 on the 36 balanced circuits).

**Why the counts mislead.**
- **Area.** Every gate counts 1, but an inverter costs a third of an XOR2 and an AND2 two thirds
  (Nangate45: 0.53, 1.06, 1.60 µm²). Fewer ANDs at the same G means more XORs and a larger circuit.
- **Delay.** XOR2 is the slowest cell, and a gate's delay grows with the load it drives. Gate depth
  counts neither.

**Exact comparisons.** Each was tested in all 6 library × flow configurations on a balanced set
of repeats: 6 statement orders × 3 placement settings for the free flows, the 6 order means being
the units, and 6 placement settings for preserve. "Holds" counts configurations with a one-sided
Welch p < 0.05 after Holm correction over the 132 tests of the 22 repeated pair-measures (19
pairs). These tests are of the logically worse circuit being better:

| Logically worse circuit | Beats | Measure | Holds (Welch, Holm) | Gain | Why |
|---|---|---|---:|---:|---|
| S-box 57/9/152/36 (`aes-sbox-a57-ad9-g152-gd36-hb2092f6d0c4adc01`) | NIST 30/4/147/36 (`aes-sbox-a30-ad4-g147-gd36-xx117-13`) | ADP | 6 of 6 | 46–55% | 59 XOR/XNOR against 117 at the same depth: 1.51 against 2.64 ns (Nangate45, preserve) |
| S-box 68/13/176/37 (`aes-sbox-a68-ad13-g176-gd37-hdd064a2dd98cf1eb`) | S-box 28/5/172/27 (`aes-sbox-a28-ad5-g172-gd27-hb9d61cfc26a4a3bb`) | area | 6 of 6 | 22–45% | 50 of its gates are inverters, 58 XORs against 144 |
| inverse S-box 54/4/144/16 (`aes-invsbox-a54-ad4-g144-gd16-h2d9970ea050c359`) | ours 28/4/143/16 (`aes-invsbox-a28-ad4-g143-gd16-xxn115-59-1`) | power | 6 of 6 | 6–30% | ANDs instead of XORs |
| MixColumns 117@6 (`aes-mixcolumns-xor117-depth6-hac7ce23fbc1f9bb9`) | MixColumns 95@6 (`aes-mixcolumns-xor95-depth6-hfca2934f2afadbfa`) | delay | 6 of 6 | 16–32% | most outputs shallow and lightly loaded |
| InvMixColumns 351@7 (`aes-invmixcolumns-xor351-depth7-h7711bf97e4bcf`) | InvMixColumns 113@7 (`aes-invmixcolumns-xor113-depth7-h5e49d90bd57a4`) | delay | 6 of 6 | 8–35% | the same, with three times the gates |
| direction-select S-box 36/6/241/26 (`aes-sbox-sel-a36-ad6-g241-gd26-hcb958a27654d38`) | NIST 36/6/191/26 (`aes-sbox-sel-a36-ad6-g191-gd26-xx155-31`) | delay | 6 of 6 | 9–17% | |
| inverse S-box 31/5/138/20 (`aes-invsbox-a31-ad5-g138-gd20-h18e16082a70397f`) | NIST 28/4/135/20 (`aes-invsbox-a28-ad4-g135-gd20-xx107-35`) | ADP | 3 of 6 | 4–17% | a less loaded critical path; with the structure kept only (exploratory after resynthesis) |

- **Six of them** hold in all six configurations after Holm.
  - **As one claim.** Each also holds as a single "all six" claim (the largest of its six p,
    Holm over the 22 pair-measures): adjusted p ≤ 0.024, both with Welch tests and with exact
    permutation tests.
  - **Without the selection runs.** They still hold in all six when the runs that chose them are
    left out: order 0 for the free flows, the base run for preserve. Adjusted "all six" p is
    0.0003–0.019.
  - **Fresh runs only.** With only the runs made after the balanced set was chosen (orders 3–5,
    placements 4–5), the same six hold in all six configurations on the raw tests. These tests (2
    or 3 units a side) are mostly too small to pass Holm: "all six" passes for two of them.
- **The inverse S-box pair** holds with the structure kept and on SKY130 free-area.
  - **The other three resynthesized configurations** pass the raw tests only (Holm p 0.08–0.25).
  - **"All six".** That claim is not supported (Holm p 0.13 Welch, 0.056 permutation; 0.39 without
    the selection runs).
  - **The first version.** The study's first version reported it as holding in all six. That rested
    on order 0 counted four times among six pooled runs.
- **Coverage.** Four of the seven beat a NIST circuit or a published circuit of ours.
- **Electrical violations.** Five rows are free of them in every job.
  - NIST's 28/4/135/20 has one overloaded net in 3 of its 88 jobs: statement order 3, Nangate45
    free, off the worst path.
  - The power row's winner has one overloaded net on Nangate45 free, at ×1.40 its capacitance
    limit and on the worst path. OpenSTA then extrapolates that cell's delay, slew and internal
    power beyond the Liberty tables, and the cells it drives see the extrapolated slew.

Of the 19 apparent inversions that got repeated runs (the base run's largest; units as above):

| Configurations where the inversion holds | Pairs, raw Welch or permutation | Pairs, Welch with Holm over 132 | Pairs, Welch with Holm, selection runs left out |
|---|---:|---:|---:|
| 6 of 6 | 10 | 8 | 7 |
| 5 of 6 | 4 | 4 | 3 |
| 4 of 6 | 4 (all power) | 3 | 3 |
| 3 of 6 | 0 | 3 | 4 |
| 2 of 6 | 1 | 1 | 2 |

All 19 pairs got the balanced repeats. Per pair and configuration, with the permutation tests
(Holm within each pair-measure) and the fresh-data tests: [results/SEEDED.md](results/SEEDED.md).

**Published circuits are rarely the physically best of their own metric class.** These are single
base runs; within these groups no member has an electrical violation.
- **NIST's MixColumns 88@5** ranks 1 of 10 in routed delay in all four preserve and free-area
  configurations. Ours, with the same counts, ranks between 2nd and 9th, 2.4–7.4% slower.
- **Our S-box 32/4/114/19** ranks 6 of 9 (Nangate45) and 8 of 9 (SKY130) with the structure kept,
  and 7 of 9 on both after area-oriented synthesis. There the best circuit with its counts is
  9–12% faster (ours is 10–14% slower).
- **How firm.** The preserve-flow ranks are far beyond placement noise. The free-area ranks are
  single runs.
  - **MixColumns 88@5.** Ours is 5.2% and 7.4% slower, at or below the size of the
    statement-order noise (delay thresholds 8.0% and 7.2%): unconfirmed.
  - **S-box 32/4/114/19.** Ours is 10.2% and 13.8% slower, beyond the thresholds, but in one run
    each.

With the structure kept, the archives already hold these physically better circuits, at no gate
cost.

**On SKY130, XOR/XNOR polarity changes power when the structure is kept.** Within groups,
preserve-flow power tracks the XNOR count (ρ +0.66) and the XOR count (ρ −0.65). XNOR2 costs more
power than XOR2 there, and the polarity is a free choice in both searches. After resynthesis the
effect is gone (about ±0.08), and on Nangate45 it is small (±0.13).

**The benchmark's first pair, repeated.** BoolFlux 40/4/134/12 against NIST 45/4/141/12, on 6
statement orders × 3 placement settings (free flows: mean ± sd of the 6 order means) and 6
placement settings (preserve); Welch tests, Holm over the pair's 24 tests:
- **Structure kept.** Ours is better in all four measures on both libraries: routed delay
  0.828 ± 0.002 against 0.867 ± 0.003 ns (Nangate45), 3.597 ± 0.029 against 3.974 ± 0.028 ns
  (SKY130).
- **Free-area.** Ours is smaller and lower in power on both libraries, and has the lower ADP on
  SKY130 (Holm p < 0.05). Its delay advantage (Nangate45 0.784 ± 0.022 against 0.866 ± 0.086 ns,
  SKY130 3.59 ± 0.11 against 4.18 ± 0.35 ns) does not survive the correction.
- **Free.** Every difference is within synthesis noise on both libraries, including the
  benchmark's single-run losses. Nangate45 delay 0.697 ± 0.028 against 0.724 ± 0.027 ns. SKY130
  area 1,466 ± 159 against 1,334 ± 82 µm² (ours 9.9% larger, p 0.11; the single run had 18.7%).
  The study's first version reported the SKY130 area loss as persisting; that rested on order 0
  counted four times among six pooled runs.

All tables: [results/TABLES.md](results/TABLES.md) (noise, groups, inversions, synthesis,
agreement between configurations, prediction, the prospective test),
[results/SEEDED.md](results/SEEDED.md) (the repeated runs) and
[results/ELECTRICAL.md](results/ELECTRICAL.md) (electrical checks). Every job's numbers:
[results/table.csv](results/table.csv), [results/seeds.csv](results/seeds.csv).

## What this means for XORFlux and BoolFlux

1. **Add a physical cost next to the counts.** Use library-weighted area and the load-aware
   longest path of [features.py](features.py): 4 cells × 2 parameters per library, read from the
   Liberty tables.
   - For circuits implemented as written, it ranks circuits with the same counts. Use it as a
     tie-break or as a Pareto dimension.
   - An incremental version only needs to update arrival times in the fanout cone of a rewrite.
   - Expected gain from selection alone, in this setting: the score's top 10 had an observed
     median routed delay 2–11% below the random 10 in the 8 significant pool × library tests
     (structure kept, Nangate45 and SKY130).
2. **Stop counting NOT like XOR.** Report NOT separately and treat XOR/XNOR polarity as free (for
   SKY130 power, prefer XOR). Give gate depth gate-type weights, or use the score's longest path
   in its place.
3. **For circuits that will be resynthesized, rank with synthesis in the loop.**
   - Keep G and GD as the search objective; across held-out circuits of a function they still
     rank the resynthesized delay with ρ 0.54–0.93 (lowest for the S-box on Nangate45, 0.54–0.63;
     test sets of 5–41 circuits).
   - Yosys + ABC + timing before placement costs a median 1.0 s of CPU per circuit, library and
     flow ([results/timing.json](results/timing.json)). It is as informative as a whole job, but
     within a metric class one run predicts another statement order's ranking only weakly.
   - So rank on the mean over several orders of the RTL statements. The order alone moves the
     result by 2–3.5%, 3–13 times the placement noise. Each order costs the same again: 2.9 s for
     three, 4.8 s for five. Expect it to separate circuits whose differences exceed that noise,
     not to rank close ones.
   - For the linear maps, much of the cost is the benchmark's switching simulation, which power
     needs and timing does not.
4. **Keep many structurally different circuits per metric key.** The routed-delay spread inside
   a key is a median 5.6–14%, up to 27% with the structure kept and 46% after resynthesis. The
   archives already hold thousands of structures for some keys (5,852 for MixColumns 90@4).
5. **Treat physical wins below about 7–10% in delay (8–13% in ADP) in a resynthesized flow as
   unconfirmed until repeated over several statement orders.** This includes the benchmark's own
   single-run free-flow comparisons.
6. **Keep #AND and AND depth for what they measure.** They are useful proxies for the nonlinear
   cost in masking and multi-party-computation settings where the AND gates dominate (randomness,
   communication, rounds). They are not complete costs there, not evidence of security, and not a
   proxy for the area of an unmasked CMOS circuit. If physical cost becomes a target, give it its
   own objective rather than reordering A, AD, G, GD.

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

**Jobs** ([manifest.py](manifest.py) lists every one).
- **Settings.** The benchmark's own: Nangate45 and SKY130HD; the preserve, free and free-area flows;
  placement, routing, extraction.
- **Checks.** Simulation (all inputs for the S-boxes) and a formal proof at the RTL, mapped and
  routed stages, plus 0 routing DRC errors.
- **Totals.** 12,203 new jobs, all passed: 6,647 base and 5,556 repeated (3,540 seeded, 2,016
  balanced). With the benchmark's own 2,040 jobs of the 340 published and NIST circuits, the study
  uses 14,243.
- **Exceptions, listed in [lists/extra.txt](lists/extra.txt).** The 41 circuits with G ≥ 400 run
  on Nangate45 and SKY130 preserve only, except 3 that also finished SKY130 free-area. Two
  InvMixColumns 118@5 circuits got repeats while the seeds were being tested.
- **Harness.** [harness.py](harness.py) and [run.py](run.py) change no setting of the benchmark.
  They read candidate files, write to their own build folder and add the noise of the repeats.

**Noise** ([seeded.py](seeded.py)). Each run is a cell (O, P): RTL statement order O and placement
setting P, both 0 in the benchmark.

| Source | What changes | Delay CV |
|---|---|---:|
| Placement setting | RePlAce's parameters around their defaults. Instance order and pin seeds alone leave this OpenROAD's output byte-identical. | 0.2–0.7% |
| Statement order (free flows) | The RTL statements shuffled before Yosys and ABC. Area moves too (CV 0.5–2.4%). | 2–3.5% |

- **The seeded repeats.** 136 circuits, chosen by a fixed rule ([select_seeds.py](select_seeds.py)):
  whole same-metric groups, the first pair, and the largest apparent inversions. The largest
  inversions are the apparent wins most likely to be noise. The groups include their
  prospective-test members: 19 of the 29 in MixColumns 90@4. Placement settings 1–3 on order 0, and
  for the free flows orders 1 and 2 with one placement setting each.
- **Units.** A free-flow circuit's runs are nested: placements within statement orders. The test
  units are therefore the order means, each order weighted equally. A preserve circuit has one
  netlist, so its units are the runs.
- **The balanced follow-up.** The circuits of the claims that rest on repeats, 36 of them
  ([lists/balanced.txt](lists/balanced.txt)), got 6 orders × 3 placement settings (free flows)
  and 6 placement settings (preserve). Order variance is 89–100% of a single free-flow run's
  variance.
- **Thresholds.** A difference counts as beyond noise when it exceeds 2√2 × the single-run CV of
  its library, flow and measure (the median over circuits, corrected for the bias of small-sample
  standard deviations). For a group's range, the threshold is the 95% quantile of the range of
  that many noise-only copies.

**Features and scores** ([features.py](features.py)). Computed from the circuit file alone, in a
median of about 1 ms per circuit for all of them on both libraries (1.1–1.4 ms in repeated
measurements; [results/timing.json](results/timing.json)):
- **Counts:** A, AD, G, GD and the gate-type counts.
- **Fanout and input load.**
- **Output-depth balance and slack.**
- **Operand imbalance, reconvergence and sharing.**
- **Three zero-fit scores per library:**
  - a load-aware longest path: each gate costs intrinsic + slope × load, both fitted from the cell's
    Liberty delay tables, load being the input capacitance of its fanout cells;
  - the sum of cell areas;
  - a switching estimate: toggle probability × load, the toggle probability exact from the truth
    table (S-boxes) or 1/2 (linear maps).

Mapped-netlist features (cell mix, depth in cells, a canonical netlist hash) and wiring come from
the job outputs ([collect.py](collect.py)), for explanation only.

**Power.** The benchmark's: OpenSTA after routing with zero-delay switching activity, exact for
the S-boxes (all inputs simulated) and estimated from 65,570 simulated inputs for the 32-bit linear
maps. Glitches are excluded.

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
   benchmarked: 180 circuits ([screen.json](screen.json)), single runs.
4. **Tests.** One-sided Mann-Whitney of top against random, Holm-corrected over all 144 tests
   (6 pools × 2 libraries × 3 flows × 4 measures). "8 of 12" counts the 6 pools × 2 libraries of
   preserve-flow delay with Holm p < 0.05 (adjusted p 0.013–0.028). "2–11%" is the observed change
   of the median routed delay of the top 10 against the random 10 in those 8 (1.95–10.6%).
5. **Electrical.** None of the 1,080 screen jobs has a slew or capacitance violation.

**Screening cost** ([screen_cost.py](screen_cost.py), [timing.py](timing.py)). The resynthesized
ranking needs Yosys + ABC and then OpenSTA's timing of the mapped netlist with the input buffers:
the benchmark's own steps up to its first timing report.
- **Cost.** On 60 circuits (G < 400), both libraries and both free flows, 4 at a time on an
  otherwise idle 20-core machine: a median 0.98 s of CPU (p10–p90 0.6–2.7 s; 1.1 s wall). Of
  that, 0.42 s is Yosys and ABC and 0.32 s OpenROAD. The first measurement, under full load, gave
  1.8 s. The first version of this study quoted 0.75 s, which was Yosys alone.
- **Check.** Its delay equals the jobs' synthesis-stage delay in all 400 jobs compared.
- **Several orders.** k statement orders cost k times as much (measured for k = 1, 3, 5 on 20
  circuits: 1.0, 2.9 and 4.8 s).
- **Not included.** The equivalence checks.

**Electrical checks** ([electrical.py](electrical.py), [results/ELECTRICAL.md](results/ELECTRICAL.md)).
The benchmark repairs nothing, so the netlists keep the slew and capacitance violations synthesis
gives them. OpenSTA's reports were parsed for every job and stage. These are not routing DRC errors,
which are 0 in every job. No fanout limit is set in either library.
- **G < 400.** At most 2% of jobs in any configuration have a violation, almost always on one net,
  at most ×1.6 the limit.
- **G ≥ 400.** Violations are common: 39 of 41 Nangate45 free-area jobs and 35 of 41 SKY130
  preserve jobs, mostly on the critical path, up to ×1.85.
- **Delay numbers.** A violation means OpenSTA extrapolated beyond the Liberty tables, so those
  numbers are less reliable.
- **Claims.** The highlighted ones are checked in ELECTRICAL.md, "Claims check": first pair, the
  59 benchmark pairs, the exact comparisons, the published circuits' groups, the screen, the
  groups and the inversions.
  - **Inversion shares.** Only those of the larger circuits change materially (see Results).
  - **Group ranges.** Two change without their violating members: S-box 32/4/115/18 (Nangate45
    free) from 24.8% to 17.0%, and direction-select 36/6/194/37 (Nangate45 preserve) from 6.9% to
    2.2%.

## Limitations

- **Tools and conditions.**
  - One OpenROAD build (March 2024), the typical corner only.
  - No power grid, no timing repair, buffering or sizing in placement and routing (and therefore
    the electrical violations above).
  - Fixed 40% utilisation; X1 cells in the preserve flow.
- **Power.** It is zero-delay power: glitches are not counted, which favours deep circuits. For
  the linear maps the switching probabilities are sampled, not exact.
- **Large circuits.** The 41 with G ≥ 400 (mostly machine-synthesised S-boxes) ran on Nangate45
  and SKY130 preserve only (3 of them also SKY130 free-area): their SKY130 free-flow routing takes
  30–60 min per job. Their delay inversions rest mostly on jobs with electrical violations.
- **Noise model.** The seeds are perturbations, not replicas, and synthesis noise covers
  statement order only. The thresholds use median CVs, so some circuits are noisier than the
  threshold assumes.
- **Statistics.**
  - **Corrected.** The prospective test and the repeated comparisons are Holm-corrected; the other
    tables show distributions.
  - **Exploratory.** Tests that rest on 3 statement orders (the same-metric groups' ICCs and
    variance shares) are exploratory: 3 order means give Welch 2–4 degrees of freedom. The groups'
    ranges and the beyond-noise counts come from single base runs against the noise thresholds. The structure shares
    (58–99%, 18–42%) come from the 8 repeated groups, not all 40.
  - **Selection.** The repeated pairs were chosen from the base run, and the balanced set after the
    first repeats; SEEDED.md repeats every test without those runs.
- **Hash version.** The sample was drawn with a first structure hash that did not fold constant
  operands; the candidate names carry those hashes. The 4 candidates that copied published circuits
  under the folded hash are marked in `results/table.csv` (`dup_of`) and left out of every analysis.
- **Hash collisions.** The hash can still merge two DAGs that differ only in which of two identical
  duplicate gates feeds a consumer, when their fanouts agree.
- **Pool.** Only circuit files of this machine. Gzipped BoolFlux event logs were not parsed. The
  inverse and direction-select S-boxes have small same-metric groups (at most 20 and 7
  structures), so no prospective pools.
- **Fingerprints.** They cover the Liberty files, which every run checks against pinned
  checksums. They do not cover the LEF, technology and RC files, which only the ORFS commit
  installed by `hardware/tools/install.sh` pins. They also assume the tools are deterministic;
  240 jobs rerun from scratch were identical.
- **Seed selection.** [select_seeds.py](select_seeds.py) ran once, on the base run before the 41
  larger circuits had finished; [lists/seeds.txt](lists/seeds.txt) is that choice. The balanced
  follow-up was chosen after the seeded results, for the claims they bore on.

## Reproducibility

**Jobs.** [manifest.py](manifest.py) defines every job of the published results, in four stages:
- `baseline`: the benchmark's 2,040;
- `base`: 6,647;
- `repeats`: 3,540;
- `balanced`: 2,016.

The list files in [lists/](lists/) and the exceptions in [lists/extra.txt](lists/extra.txt) feed
it.
- **What makes a result current.** It needs a `metrics.json` (written only when every check
  passed) whose fingerprint matches the current benchmark code, tools, circuit and library. For a
  research job the fingerprint also covers [harness.py](harness.py)'s SHA-256 and the variant's
  effective settings: statement order, placement parameters, pin and instance-order seeds, and
  the OpenROAD script.
- **Collection.** [collect.py](collect.py) checks the whole manifest first. It stops with exit
  status 1, writing nothing, if a job is missing or stale. It collects only manifest jobs.
- **Failures.** [run.py](run.py) exits with status 1 when a preparation or a job fails.

**Revalidation.** The first version's research jobs had fingerprints without the harness
([revalidate.py](revalidate.py), [results/revalidation.json](results/revalidation.json)).
- **Comparison.** For each cached job, the script reran Yosys and ABC and compared their netlist,
  the RTL, the synthesis and OpenROAD scripts and the constraints byte for byte with what the
  current harness gives.
- **Re-stamped.** 10,185 of the 10,187 jobs matched and were re-stamped, keeping their numbers.
- **Rerun.** 2 jobs (`synth1` repeats of the two InvMixColumns 118@5 seed-test circuits,
  Nangate45 free) had been made by an earlier harness whose placement seed changed only the pin
  seed. They were rerun; their numbers moved by at most 0.5%. Their old folders are kept under
  `build/_superseded/`.
- **From scratch.** Two seeded draws of 120 jobs each (G < 400) were rerun from scratch in a
  separate folder. The first was from the base and repeats stages, the second from all three
  research stages. All 240 reproduced every compared number exactly: area, cells, delay after
  placement and routing, ADP, power and wire length.
- **Exit status.** `revalidate.py` exits with status 1 while jobs await a rerun.

## Run

```bash
bash hardware/research/run_all.sh
```

**Requirements.**
- `hardware/tools/install.sh`: Yosys, ABC, OpenROAD and the two libraries.
- Python 3.10 or later with numpy and scipy, for analyze.py, seeded.py and electrical.py; the
  rest needs the standard library only.

**Time.** About 6 hours on 19 cores if nothing is cached.

**Steps.** In order, each stopping the script on a failure:
1. the benchmark's 340 circuits;
2. the base run, then its check (`manifest.py --stage baseline,base`);
3. the repeats and the balanced repeats;
4. collect.py, analyze.py, seeded.py, tables.py, electrical.py, timing.py. They write to a
   staging folder (`HWRESEARCH_RESULTS`), which is copied into `results/` only when all have
   succeeded.

**Committed inputs.** The inventory, the sample and the prospective pools need the local campaign
archives. They were run once, and their outputs are committed: `candidates/`, `sample.json`,
`screen.json`, `lists/`, `inventory/summary*.json`. A fresh checkout therefore starts from the
benchmark jobs.

**Choosing the seeds again.** `select_seeds.py` ran once, and
[lists/seeds.txt](lists/seeds.txt) is its record. That choice cannot be rerun exactly from the
final data. Its inputs were the base run before the 41 larger circuits had finished, with noise
thresholds from the two seed-test circuits, and the final data holds neither state.

The rule can be rerun on the complete base run:
`collect.py --stage baseline,base --out DIR`, `analyze.py --res DIR`, then
`select_seeds.py --res DIR --out DIR/lists`. Without repeats there are no noise thresholds, so it
then picks the groups and the first pair but no inversions.

**Screening cost.** `timing.py --measure-screen 60 --subset 20 --orders 5` remeasures the cost of
the screening procedure, in about 12 minutes on 4 cores.

**Build outputs.** Netlists, DEF, SPEF, reports and logs (7 GB) go to `hardware/research/build/`
and are not committed.

**Tests.** The structure hash, failed-run exit status, missing and stale results, and cache
invalidation by the harness and the variant settings:

```bash
python3 -m unittest discover -s hardware/research/tests -t hardware/research
```

## Files

| Path | What is in it |
|---|---|
| [run_all.sh](run_all.sh) | the whole study, in order |
| [manifest.py](manifest.py), [lists/](lists/) | every expected job: the lists of each run, [extra.txt](lists/extra.txt) (exceptions) and [balanced.txt](lists/balanced.txt) |
| [inventory.py](inventory.py), [inventory/](inventory/) | the inventory and its summaries (the pools are local only) |
| [sample.py](sample.py), [sample.json](sample.json), [candidates/](candidates/) | the sample: every candidate, its source files and provenance |
| [screen.py](screen.py), [screen.json](screen.json), [candidates/screen/](candidates/screen/) | the prospective test: pools, scores, picks |
| [select_seeds.py](select_seeds.py) | the rule that chose the seeded repeats |
| [harness.py](harness.py), [run.py](run.py) | running the unchanged benchmark, with statement-order and placement seeds and research fingerprints |
| [revalidate.py](revalidate.py) | revalidating cached jobs after a harness change, and rerunning a sample from scratch |
| [features.py](features.py) | features and scores from the circuit file |
| [collect.py](collect.py), [analyze.py](analyze.py), [seeded.py](seeded.py), [tables.py](tables.py) | the data, the analyses, the tables |
| [electrical.py](electrical.py) | the electrical checks of every job |
| [screen_cost.py](screen_cost.py), [timing.py](timing.py) | the scores' and the screening procedure's cost |
| [results/](results/) | every job (`table.csv`, `seeds.csv`), the analyses (`analysis.json`, `seeded.json`, `electrical.json`, `timing.json`, `screen_cost.json`), their tables (`TABLES.md`, `SEEDED.md`, `ELECTRICAL.md`), the violating reports (`electrical.csv`) and the revalidation record (`revalidation.json`) |
| [tests/](tests/) | tests of the structure hash and of the pipeline |
