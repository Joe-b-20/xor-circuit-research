# Berkeley ABC as an external comparator (2026-11-13)

Every count below is the gate count of an ABC-mapped netlist after conversion to NCFF. Each
one was checked exhaustively by `independent/verify.py` against the target table, using the
cost model as the gate library. All checks passed. No BUF, constant cell or dead gate appears
in any reported netlist.

## Setup

- **ABC source**: https://github.com/berkeley-abc/abc, shallow clone, commit
  `0587b343c45b8bd6dddd866fe4ac8e55e9cbda05` (2026-11-13, "Improvements to sprove").
  The binary reports "UC Berkeley, ABC 1.01".
- **Build**: built in user space with
  `taskset -c 16-19 make ABC_USE_NO_READLINE=1 ABC_USE_PIC=1 -j4 abc`, using
  gcc 13.3.0 and the Makefile's default `OPTFLAGS = -g -O`. No system packages were installed.
- **Work area**: `~/xs-campaigns/2026-11-13-boolflux/ext/`. It holds `abc-src/`,
  `targets/`, `genlib/`, `scripts/`, every run directory in `results/`, and `run_all.log`.
- **CPU pinning**: every ABC process ran pinned to one of CPUs 16-19, with at most 4 at once.
  `run_all.py` gives slot i the CPU 16+i.
- **Files in this directory**:
  - `scripts/` (`make_targets.py`, `netconv.py`, `abc_run.py`, `run_all.py`, `collect.py`)
  - `genlib/`
  - `circuits/`: the best verified netlist per target/model
  - `abc_results.json`: every run, plus the best result per target/model

### Gate libraries (genlib)

Every gate has area 1 and delay 1 in every library.

| file | cells |
|---|---|
| `bgc.genlib` | AND2, OR2, XOR2, INV |
| `gc6.genlib` | AND2, OR2, XOR2, XNOR2, NAND2, NOR2, INV |
| `nist.genlib` | AND2, XOR2, XNOR2, INV |
| `xag.genlib` | AND2, XOR2, INV |

Each library also contains ZERO, ONE and BUF (area 1). They are there because ABC requires them:
`amap` stops with "Cannot find buffer gate", and `read_library` warns without a BUF. None of
them was used in any reported result. `netconv.py` would turn a constant into an explicit
XOR/XNOR gate and report any BUF it kept; neither case occurred.

### Targets

The targets come from `make_targets.py`, which reads `benchmarks/sboxes.json`.

- **Bit order**: msb/msb. Input x0 is the MSB of x, and output y0 is the MSB of the table value.
- **Naive start**: a BLIF with one `.names` per output that lists every on-set minterm. This is
  the full truth table, with no structure.
- **gf16-mul**: a = x>>4, b = x&15, output a*b mod x^4+x+1. Spot checks: 2*3=6, 8*8=12, 15*15=10.
- **AES**: the table in `sboxes.json`. Its circuits are checked with `verify.py --aes`, the FIPS-197
  S-box computed by verify.py itself.
- **AES warm start**: `aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt`, converted to BLIF with
  `netconv.py ncff2blif`. ABC `cec` reports it equivalent to the table.

## Flows (exact scripts)

Each run is one budgeted sequence of ABC processes (`abc_run.py`). The state carried between
steps is one AIG file. Every step ends with the same mapping portfolio, and each mapper starts
from a fresh `&r cur_k.aig`:

```
m1: &put; map -a
m2: &put; dch -f; map -a
m3: &put; dch -f; amap
m4: &dch -f; &nf -p; &put
m5: &nf -p -k; &put        # XOR/MUX coarsening; aborts on most inputs (see below), so it runs last
```

Every script begins with `source abc-src/abc.rc; read_library <lib>.genlib;`, so the standard
`resyn2`/`compress2rs` aliases are available.

- **Step 0 (all flows)**: `read_blif <start>; strash; &get -n; &w cur_0.aig`, then the portfolio.
- **classic** (deterministic, run once): each step does
  `read_blif <best mapped netlist so far>; strash; dc2; resyn2; compress2rs; dc2; &get -n; &w cur_k.aig`.
  The run stops after 3 steps in a row with no improvement (it converges in 2 to 11 s).
- **deepsyn** (seeds 1..5): each step does
  `&r cur_{k-1}.aig; &deepsyn -T <chunk> -S (20*seed+k)%101; &w cur_k.aig`.
  The chunk is 5 s for small targets and 25 s for AES.
- **eslim** (seeds 1..5): step 1 first runs `&put; dc2; resyn2; &get -n`. Each step then does
  `&eslim -x -t -f -Z 1000*seed+k -T <chunk> -V 0` (eSLIM: SAT-based exact-synthesis local
  improvement, with XOR gates allowed). The chunk is 10 s for small targets and 50 s for AES.

**Budget**: 60 s wall per run for the 4-bit and 5-bit S-boxes and gf16-mul, 300 s for AES. It is
enforced by `timeout -s KILL <remaining>` around every ABC process.

**Timing and memory**:
- Time to best is the mtime of the winning mapped BLIF minus the run start, so it includes the
  driver's overhead.
- Peak memory is the maximum "Maximum resident set size" that `/usr/bin/time -v` reports across a
  run's processes.

The whole matrix (132 runs) took 50 min of wall time on 4 CPUs.

## Results (best verified count per target/model)

"nonlin" is the number of AND/OR/NAND/NOR gates. GD is gate depth and AD is AND depth. Times are
in seconds.

| target | model | best G | flow (seed) | counts | GD | AD | nonlin | t to best | per-seed best (classic / deepsyn 1-5 / eslim 1-5) |
|---|---|---|---|---|---|---|---|---|---|
| present | bgc | **24** | deepsyn (3) | AND6 OR9 XOR4 NOT5 | 5 | 4 | 15 | 5.8 | 28 / 24 24 24 24 24 / 24 24 24 24 24 |
| present | gc6 | **20** | deepsyn (2) | AND5 NAND2 NOR5 OR3 XOR4 NOT1 | 5 | 4 | 15 | 5.8 | 24 / 20 x5 / 20 x5 |
| rectangle | bgc | **16** | eslim (4) | AND2 OR6 XOR5 NOT3 | 9 | 4 | 8 | 32.5 | 23 / 27 x5 / 24 27 27 16 17 |
| rectangle | gc6 | **12** | eslim (4) | AND1 NAND1 NOR1 OR1 XOR2 XNOR5 NOT1 | 5 | 2 | 4 | 32.1 | 22 / 24 x5 / 21 18 24 12 15 |
| ascon | bgc | **18** | eslim (1) | AND1 OR4 XOR11 NOT2 | 5 | 1 | 5 | 58.3 | 25 / 25 x5 / 18 19 18 25 19 |
| ascon | gc6 | **16** | eslim (1) | AND1 NAND1 NOR2 OR2 XOR2 XNOR7 NOT1 | 4 | 2 | 6 | 53.7 | 22 / 22 x5 / 16 17 18 22 19 |
| prince | bgc | **24** | step 0 (any flow) | AND10 OR9 NOT5 | 6 | 4 | 19 | 0.1 | 24 / 24 x5 / 24 x5 |
| prince | gc6 | **19** | deepsyn (3) | AND3 NAND7 NOR2 OR6 NOT1 | 5 | 4 | 18 | 5.7 | 20 / 19 x5 / 19 x5 |
| gf16-mul | xag | **37** | eslim (1) | AND18 XOR14 NOT5 | 5 | 2 | 18 | 42.9 | 125 / 44 42 42 56 56 / 37 148 45 39 37 |
| gf16-mul | nist | **36** | eslim (3) | AND18 XOR13 XNOR1 NOT4 | 6 | 2 | 18 | 32.1 | 130 / 44 41 41 56 56 / 36 146 36 39 36 |
| aes (naive) | nist | **1224** | deepsyn (1) | AND707 XOR3 XNOR14 NOT500 | 25 | 14 | 707 | 297.8 | 1597 / 1224 1273 1289 1289 1307 / 1384 1345 1395 1364 1358 |
| aes (warm, NIST 104) | nist | **110** | step 0 (any flow) | AND32 XOR29 XNOR48 NOT1 | 30 | 5 | 32 | 0.1-0.2 | 110 / 110 x5 / 110 x5 |

- **Total time**: classic runs took 2 to 11 s. Every deepsyn and eslim run used its full
  budget (60 s or 300 s).
- **Peak RSS**: 20 to 30 MB in every run.
- **Per run and per flow**: `abc_results.json` (`runs`) has every run's counts, depth,
  time to best, number of steps and RSS. `results/table.md` in the work area has a per-flow
  table.

### AES warm start

- **Round-trip loss**: ABC cannot return the 104-gate input at 104 gates. `strash` breaks each
  XOR into 3 AND nodes (248 AIG nodes), and remapping gives the following on step 0:

  | mapper | gates |
  |---|---|
  | m1 | 130 |
  | m2 | 122 |
  | m3 | 128 |
  | m4 | 131 |
  | m5 (`&nf -k`, XOR coarsening) | 110 |

  The 110 keeps the AND count (32) and AND depth (5).
- **No later improvement**: none of the 5 deepsyn seeds or 5 eslim seeds improved on 110 in
  300 s each. Their AIG-level optimisation makes the remapped netlist larger. The classic flow
  converged at 110 in 2.5 s.
- **Side probe** (deterministic, interactive, not part of the matrix): the 104-node network,
  read as a logic network without strash, was left at 104 nodes by all of these:
  `mfs -a -W 30 -D 50 -M 0`, `mfs2 -a ...`, and `&if -K 2 -a; &mfs -a -W 30`.
- **Conclusion**: ABC's don't-care resubstitution finds nothing to remove, and its mapping
  pipeline adds 6 gates.

### AES from the function

From the truth table, ABC's best is 1224 gates (deepsyn seed 1, still improving at 298 s). That
is about 12 times the NIST circuit. ABC's AIG flows do not find the tower-field (GF(2^4)-based)
structure, and 500 of the 1224 gates are inverters.

## Caveats on comparability

- **ABC does not optimise our cost**:
  - deepsyn, eslim, dc2 and resyn2 minimise AIG node count, in which an XOR costs 3 nodes and
    inverters are free.
  - The mappers then pick a minimum-area cover of that fixed AIG structure (with choices for
    `dch`/`&dch`). Area = our gate count only because every cell has area 1.
  - Gate count is therefore optimised only indirectly. Inverters appear because the mapper has
    to make up for complemented AIG edges, for example 5 of 24 gates in present/bgc.
  - `eslim -x` allows XOR during its local synthesis, but the result is exported as an AIG.
- **Steps are separate processes**: mapping happens only at step boundaries. Each process
  re-reads the library and rebuilds supergates, which costs well under 1 s and is included in
  all times.
- **Same step 0 in every flow**: that is why prince/bgc and the AES warm start show identical
  results across flows and seeds.
- **deepsyn seeds**: on the 4-bit S-boxes all 5 seeds gave the same count. Different seeds
  reach the same AIG on such small functions.
- **`&nf -p -k` (m5) is fragile**: it hit `giaNf.c:1330 Nf_ManCutMatch: Assertion ... failed`
  in 869 of 1340 steps (m5 wrote a netlist in 377; the rest were budget-killed earlier). Because it runs last, the crash only drops its own result; m1-m4
  were always written first. The remaining non-zero exits (96) are budget kills of a run's last
  step, which is expected.
- **No use of `twoexact` / `lutexact`**: ABC's exact-synthesis commands work on a single output
  and synthesise over all 2-input functions, which is a different basis from these libraries.
- **Seeds are not interchangeable**: `-S`/`-Z` choose ABC-internal random streams. The seed
  numbers here are not comparable with our optimiser's seeds.
- **Wall-clock dependence**: deepsyn and eslim stop on internal timeouts, so a re-run with the
  same seed can differ slightly.
