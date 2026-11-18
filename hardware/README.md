# hardware

Standard-cell benchmarks of our circuits against NIST's: every BoolFlux circuit for the AES S-box,
its inverse and the S-box with a direction bit, XORFlux's AES MixColumns and InvMixColumns
circuits, and NIST's circuits for the same functions. Each circuit is turned into Verilog,
synthesized with Yosys and ABC, placed and routed with OpenROAD on two open standard-cell libraries
(Nangate45 and SKY130HD), and measured with OpenSTA's models: cell area, critical-path delay,
area-delay product and power. Every netlist is checked equivalent to the function it should
compute, at every stage.

The gate counts of the circuit files (#AND, AND depth, #gates, gate depth) are abstract measures;
these benchmarks show what they become in cells and wires, as modeled after placement and
routing. We don't claim the numbers rank the circuits in general: they depend on the library and
its cells, the corner, the constraints and the flow, all stated here.

[research/](research/README.md) uses the same benchmark on 1,457 circuits, mostly from all our
search runs, to ask what the counts miss and how the searches could look for better hardware
directly (summary [below](#research-searching-for-physically-better-circuits)).

## Results

**The first pair**, the inverse S-box: BoolFlux 40/4/134/12 against NIST 45/4/141/12
(#AND / AND depth / #gates / gate depth). NIST's numbers, then ours (bold where ours is smaller),
and the change:

| Library | Flow | Area µm² | Routed delay ns | ADP µm²·ns | Power µW |
|---|---|---|---|---|---|
| Nangate45 | preserve | 201.1 → **192.6** (-4.2%) | 0.865 → **0.827** (-4.4%) | 174 → **159** (-8.4%) | 42.8 → **41.1** (-4.0%) |
| Nangate45 | free | 245.8 → 248.4 (+1.1%) | 0.722 → 0.742 (+2.7%) | 178 → 184 (+3.8%) | 57.0 → 57.5 (+0.9%) |
| Nangate45 | free-area | 188.9 → **183.0** (-3.1%) | 0.834 → **0.794** (-4.8%) | 158 → **145** (-7.7%) | 43.0 → **41.2** (-4.2%) |
| SKY130HD | preserve | 1122.3 → **1073.5** (-4.3%) | 3.938 → **3.597** (-8.6%) | 4419 → **3862** (-12.6%) | 167.0 → **163.0** (-2.4%) |
| SKY130HD | free | 1322.5 → 1570.3 (+18.7%) | 3.316 → 3.533 (+6.6%) | 4385 → 5548 (+26.5%) | 214.1 → 253.9 (+18.6%) |
| SKY130HD | free-area | 1007.2 → **963.4** (-4.3%) | 4.355 → **3.468** (-20.4%) | 4386 → **3341** (-23.8%) | 173.7 → **165.4** (-4.8%) |

**All 59 pairs** (forward, inverse and direction-select S-boxes, MixColumns, InvMixColumns; each
NIST circuit of NIST's front against a circuit of ours at least as good in all four counts, see
Method): in how many pairs ours is smaller, faster or lower, and the median change against NIST.

| Library | Flow | Pairs | Area: ours smaller | median | Routed delay: ours faster | median | ADP: ours lower | median | Power: ours lower | median |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nangate45 | preserve | 59 | 53 | -2.4% | 47 | -4.5% | 56 | -7.3% | 52 | -2.2% |
| Nangate45 | free | 59 | 33 | -3.0% | 36 | -2.0% | 36 | -6.7% | 33 | -3.0% |
| Nangate45 | free-area | 59 | 46 | -1.9% | 37 | -4.5% | 44 | -6.3% | 43 | -1.7% |
| SKY130HD | preserve | 59 | 53 | -2.4% | 44 | -3.2% | 51 | -6.8% | 26 | +0.5% |
| SKY130HD | free | 59 | 37 | -1.6% | 40 | -4.5% | 40 | -5.9% | 36 | -1.3% |
| SKY130HD | free-area | 59 | 43 | -2.3% | 40 | -3.1% | 42 | -5.7% | 43 | -2.1% |

When the structure is kept (preserve), our circuits are smaller in 53 of the 59 pairs on both
libraries and have the lower area-delay product in 56 (Nangate45) and 51 (SKY130HD). When ABC
restructures the circuit (free, free-area), the median change stays negative but the advantage is
less consistent (ours smaller in 33 to 46 of the 59): the result then depends on ABC's heuristics
as much as on the starting circuit (for the first pair on SKY130HD, ABC's delay-oriented sizing
made ours 19% larger in this run; over 6 statement orders the difference is within noise).
Differences of a few percent in one pair mean
little: circuits with the same counts (our MixColumns 88@5 and 97@3 against NIST's) differ by
1.5-4.5% in routed delay in the preserve flow and by up to 27% after free synthesis. Power is
zero-delay power (glitches not counted); with the structure kept it follows area on Nangate45 and
is even on SKY130HD (median +0.5%).

Every number above comes from one run per job. Repeated runs in [research/](research/README.md)
measure the noise:
- **Placement.** Placement parameters move routed delay by 0.2–0.7%.
- **Synthesis.** Reordering the RTL statements moves the free flows by 2–3.5%.
- **The first pair.** Over 6 statement orders × 3 placement settings (free flows; mean ± sd of
  the order means) and 6 placement settings (preserve):
  - **Free flow.** Its losses above are within that noise on both libraries: Nangate45 delay
    0.697 ± 0.028 against 0.724 ± 0.027 ns, SKY130 area 1,466 ± 159 against 1,334 ± 82 µm².
  - **Preserve.** Its advantage holds in every measure on both libraries, e.g. Nangate45 delay
    0.828 ± 0.002 against 0.867 ± 0.003 ns.
  - **Free-area.** So do its area and power advantages.

**Electrical checks.** The flow repairs no slew or capacitance violations, so a few netlists keep
the ones synthesis gave them.
- **Benchmark jobs.** 14 of the 2,040 have one after routing, mostly a single overloaded net.
- **Pairs.** 2 of the 354 pair comparisons involve one, neither on the worst path.
- **First pair.** It has none in the benchmark runs. Over the repeats, NIST's circuit has one
  overloaded net in 3 of its 88 jobs (one statement order, Nangate45 free).

These are OpenSTA's checks against the Liberty limits, not routing DRC errors, which are 0 in
every job. Per job: the `drv_*` columns of results.csv; by type:
[research/results/ELECTRICAL.md](research/results/ELECTRICAL.md).

Every pair, flow and library, the smallest area, delay and ADP over all circuits of each set, and
every job's numbers: [results/RESULTS.md](results/RESULTS.md), [results/results.csv](results/results.csv).
NIST's circuits of gate depth 10 (S-box and inverse) have the lowest delay of all; we have none at
that depth.

## Research: searching for physically better circuits

[research/](research/README.md) runs this benchmark, unchanged, on 1,457 circuits:
- the 340 above;
- 937 drawn from 394,027 distinct circuits in every circuit file of our search runs;
- 180 picked by a prospective test.

It ran 12,203 new jobs (6,647 base runs, 5,556 repeated runs to measure noise), 14,243 with the
benchmark's own 2,040 above. Its findings, for these two libraries, the typical corner and the
benchmark's constraints:
- **Same counts, different hardware.** Circuits with identical (A, AD, G, GD) differ in routed
  delay by a median 5.6–6.5% when the structure is kept, and 11–14% after resynthesis.
- **Worse counts, often better hardware.** The counts weigh an inverter, an AND and an XOR alike
  and ignore load. Among circuits with fewer than 400 gates, logically worse ones are physically
  better in 9–15% of dominated pairs with the structure kept, and 16–38% after resynthesis.
  - **With the larger S-boxes.** Including the larger machine-synthesised ones gives up to 28% and
    44% for delay.
  - **Their electrical violations.** Many of their jobs have slew or capacitance violations on the
    critical path; without those jobs the preserve-flow shares fall to 11–24%.
- **A cheap score predicts it when the structure is kept.** A load-aware longest path from the
  Liberty tables (about 1 ms per circuit) ranks circuits with equal counts on held-out data.
  - **Prospective test.** Its top 10 picks were significantly faster than 10 random picks in 8 of
    12 pool × library tests (6 pools, 2 libraries; Holm-corrected over 144 tests).
  - **Gain.** Their median routed delay was 2–11% lower.
- **Resynthesis hides it, from the file and largely from everything else.** After resynthesis
  the tested file-derived scores did not reliably predict the ranking within a metric class.
  - **Same run.** Synthesis and timing before placement (about 1 s of CPU per circuit, library and
    flow) predict the routed delay of the same synthesis run.
  - **Other orders.** Another RTL statement order's delay they predict only weakly (ρ 0.28–0.47).
    A whole routed run of the same orders does about as well: within a class, the order moves
    delay more than the structure does.
- **Published circuits are rarely the best of their metric class.** Physically better ones with
  the same counts are already in the archives (with the structure kept; after resynthesis these
  are single runs, partly within noise).

- **Repeated comparisons.** Six of seven highlighted comparisons of a logically worse circuit
  beating a better one hold in all six configurations after Holm correction, over 6 statement
  orders (6 placement settings with the structure kept). The seventh holds in 3.

It ends with recommendations for new XORFlux and BoolFlux objectives.

## Method

**Circuits.** A circuit file of NIST's format becomes Verilog with one operator per gate
(`hwbench/verilog.py`). NIST writes NOT as `XNOR t a 0`; that becomes one inverter. The reference
function never comes from a circuit: the S-boxes are computed from FIPS 197's definition
(`circuits/boolcirc/truth.py`), the linear maps from their matrix files.

**Flows** (`hwbench/flow.py`; the same tool versions, libraries, constraints and scripts for every
circuit):

| Flow | Synthesis |
|---|---|
| preserve | every gate of the file becomes one 2-input cell of drive 1 (AND2, XOR2, XNOR2, INV for NOT); no logic optimisation; the cell counts are asserted |
| free | Yosys `synth -flatten`, then ABC to the whole library with Yosys's default script (delay-oriented `&nf`, then buffering and sizing) |
| free-area | the same with the mapper's delay target relaxed (`&nf -R 1000`) and no sizing: area-oriented |

Then, for every flow: one buffer after each input port (`buffer_ports -inputs`, skipped where
synthesis already put one), floorplan at 40% utilisation, ORFS tracks and tap cells, pins and
global placement in ORFS's order, detailed placement, global and detailed routing (0 DRC errors
required), extraction with OpenRCX. No timing repair, resizing or buffering beyond the input
buffers, so the routed cells are the synthesized cells (checked). No power grid is built.

**Measures.** Area: the logic cells' area from the Liberty file (no taps, no input buffers).
Delay: OpenSTA's worst input-to-output path; inputs driven by the library's X1 buffer, 3.898 fF
(Nangate45) or 5 fF (SKY130, ORFS's values) on each output; after synthesis without wires, after
placement with estimated wires, after routing with the extracted parasitics. ADP: area x routed
delay. Power: OpenSTA after routing, at 100 MHz with a new uniformly random input every cycle; the
switching activity of each net is set from simulation (a net that is 1 for a fraction p of the
inputs toggles with probability 2p(1-p)): exact for the S-boxes, whose inputs are all simulated,
and estimated from the 65,570 simulated inputs for the 32-bit linear maps. It is zero-delay power:
glitches are not counted, which favours circuits with a large gate depth. Typical corner only
(Nangate45 typical, SKY130 tt 25 °C 1.80 V). Electrical limits: OpenSTA's max slew, capacitance and
fanout checks after each stage are reported, not repaired (no fanout limit is set).

**Checks** (a job reports nothing unless all pass):

| Stage | Simulation | Formal |
|---|---|---|
| RTL | Icarus Verilog against the reference table | Yosys miter, ABC `&cec` |
| mapped netlist | every cell through its Liberty function (`hwbench/netlist.py`) | Yosys miter with the cells read from the Liberty file, ABC `&cec` |
| routed netlist | the same | the same; and 0 DRC errors after detailed routing |

Simulation covers all 2^n inputs for the S-boxes (256, 512 with the direction bit) and 65,536
random inputs plus the unit vectors for the 32-bit linear maps. The tests check that the checks
are not vacuous: a one-gate mutation of the RTL or of a mapped netlist fails both.

**Pairs.** For each NIST circuit that no other NIST circuit of the same function matches or beats
in all four of A, AD, G and GD, the circuit of ours compared with it is, among ours that are at
least as good in all four, the one with the fewest gates (`hwbench/pairs.py`).

## Run

```bash
hardware/tools/install.sh
```

```bash
python3 hardware/bench.py run --suite first-pair
```

```bash
python3 hardware/bench.py run --suite all
```

```bash
python3 hardware/bench.py table
```

```bash
python3 -m unittest discover -s hardware/tests -t hardware
```

`install.sh` needs no root: it puts micromamba, two environments built from the lock files in
[tools/](tools/) and the two platforms of
[OpenROAD-flow-scripts](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts) at commit
`90b19ec` into `~/.local/hwbench` (`HWBENCH_TOOLS` to move it), and checks the Liberty files
against [tools/platforms.sha256](tools/platforms.sha256). `run` takes suites
([suites/](suites/)) or circuit files and folders, `-p nangate45,sky130hd`, `-f preserve,free,free-area`
and `-j` parallel jobs (default: all cores); each job's files (Verilog, Yosys and OpenROAD
scripts and logs, timing and power reports, netlists, DEF, SPEF, `metrics.json`) go to
`hardware/build/<circuit>/<library>/<flow>/`. A job is rerun when its circuit file, the benchmark's
code, the library or the tool versions change, and `run` exits with status 1 if any job fails. `table` writes [results/](results/). The whole suite (340
circuits, 2,040 jobs) took 30 minutes on 19 cores.

Tools: Yosys 0.71 with its ABC, Icarus Verilog 12.0, OpenROAD 2.0-12381-g01bba3695 (the litex-hub
build of March 2024; newer builds are not packaged for installation without root). Runs are
deterministic: a second installation from the lock files gave identical results.

## Files

| Path | What is in it |
|---|---|
| [bench.py](bench.py) | the command line |
| [hwbench/](hwbench/) | the benchmark: circuit loading, Verilog, Liberty reader and netlist simulator, flows, pairs, tables |
| [suites/](suites/) | lists of circuit files and folders |
| [nist/](nist/README.md) | NIST's AES MixColumns and InvMixColumns circuits (NIST's S-box circuits are in [search/nonlinear/seeds/](../search/nonlinear/seeds/)) |
| [tools/](tools/) | the installer, lock files, Liberty checksums |
| [tests/](tests/) | unit tests, and tests with the tools (skipped without them) |
| [results/](results/RESULTS.md) | every job's numbers (`results.csv`) and the tables |
| [research/](research/README.md) | the study of what the counts miss physically, and how to search for it |
