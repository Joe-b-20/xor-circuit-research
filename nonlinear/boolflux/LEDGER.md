# BoolFlux benchmark ledger

Every circuit listed here is in [results/](results/) (NCFF, with a `.summary.json` holding the
command, settings, code hash, seeds and per-job metrics) and passed both verifiers: `core`
(bitsliced, against `targets.py` / `benchmarks/sboxes.json`) and `independent/verify.py`
(per-input exhaustive evaluation, own AES and table code, own metrics, library and cap checks;
the two metric computations must agree). Machine: Intel Core i7-13700H, 20 logical CPUs,
WSL2 Ubuntu, gcc -O2, Python 3.12. Times are wall-clock seconds for the whole command; CPU s
is the sum over jobs. Full per-run tables: [results/reports/](results/reports/).

**Gate libraries and costs** ([models/](models/)): `nist` = AND, XOR, XNOR, NOT (NOT written
as `XNOR t a 0`), each 1 — NIST's accounting, so G equals NIST's G; `bgc` = AND, OR, XOR, NOT,
each 1 (bitslice gate complexity, Stoffelen 2016); `gc6` = AND, OR, XOR, XNOR, NAND, NOR, NOT,
each 1 (gate complexity as in Stoffelen 2016 / Zhang-Huang 2023); `xag` = AND, XOR, NOT.
**Metrics**: G gates (NOT counted), A nonlinear gates, GD gate depth (inputs at 0, every gate
+1), AD AND depth. Objectives are lexicographic (`cost,gd` = cost, then GD).

**Two kinds of claim.** *Improves its start*: the search was given that circuit and returned a
better one under the same model and caps. *New on the published set*: no published circuit we
know of is at least as good on every compared metric. Only the second beats published work,
and only relative to the sources in [benchmarks/LITERATURE.md](benchmarks/LITERATURE.md).

## 1. Known-improvable sanity cases (naive ANF starts)

| function | model, objective | start (ANF) | result | known | time |
|---|---|---|---|---|---|
| majority of 3 | xag, a,cost | 5 gates, 3 AND | **4 gates, 1 AND** (AND 1, XOR 3) | 4, MC 1: optimal | 0.2 s |
| full adder | xag, a,cost | 7 gates, 3 AND | **5 gates, 1 AND** (AND 1, XOR 4) | 5, MC 1: optimal | 0.3 s |
| GF(2^4) multiplication | xag, a,cost, pipe (skeleton + gates) | 34 gates, 16 AND (schoolbook) | **32 gates, 9 AND** (AND 9, XOR 23) | 9 AND = bilinear rank (minimum) | 82 s |
| GF(2^4) multiplication | xag, a,cost, gate level only | 34, 16 AND | 30 gates, **14 AND** | - | 17 s |
| GF(2^4) inversion (mod x^4+x+1) | xag, a,cost, pipe | 33, 10 AND | **17 gates, 5 AND** | MC 5; 16 gates (5 AND + 11 XOR) published, basis not checked | 15 s |
| GF(2^4) inversion | xag, cost, pipe | 33, 10 AND | **15 gates**, 6 AND (AND 6, XOR 9) | 15 gates with 2-input gates claimed (ME19 slides, secondary) | 14 s |

The GF(2^4) multiplier is the nonlinear sanity check: reaching 9 ANDs requires replacing pairs
of products by one product of sums (Karatsuba), which the gate level alone does not find (14);
the skeleton level's merge move does. Commands: `results/reports/sanity-2.md`.

## 2. Small S-boxes from naive starts

`pipe --start anf --objective cost --iters 100000 --skel-iters 2000 --seeds 1-8 --rounds 3`,
15-32 s each (`campaigns/small_sboxes.sh`, CONFIGS="bgc:cost gc6:cost"). Published values from
[benchmarks/LITERATURE.md](benchmarks/LITERATURE.md); "opt" = proved optimal by SAT, a range
[l, u] = SAT lower/upper bound (Sto16, ZH23).

| S-box | ANF start (bgc) | **BGC ours** | BGC published | **GC6 ours** | GC published |
|---|---|---|---|---|---|
| PRESENT / LED | 32 | 14 | 14 | 13 | - |
| GIFT | 22 | 11 | 11 | 10 | 10 (spec) |
| SKINNY-64 | 30 | 11 | 11 | 8 | 8 (spec) |
| PRINCE | 35 | 16 | 16 | 15 | - |
| Midori Sb0 | 29 | 13 | 13 | 12 | - |
| Midori Sb1 | 35 | 16 | **15** (Sov23) | 15 | - |
| Piccolo | 31 | 10 | 10 opt | 8 | 8 opt |
| RECTANGLE | 27 | 12 | 12, opt in [11, 12] | 11 | 11 opt |
| KLEIN | 38 | 17 | 17 | 15 | - |
| Noekeon | 28 | 12 | 12 | 10 | - |
| PRIDE | 17 | 8 | 8 opt | 8 | 8 opt |
| Serpent S0..S7 | 32-38 | 14 14 13 15 15 15 14 16 | 14 14 13 15 15 15 14 16 (Sov23) | 13 13 12 15 13 14 13 14 | - |
| PRINTcipher (3-bit) | 9 | 6 | - | 6 | - |
| chi (3-bit) | 9 | 7 | - | 7 | - |
| Ascon (5-bit) | 35 | 16 | 16, opt in [12, 16] (ZH23) | 15 | 15, opt in [12, 15] (ZH23) |
| Keccak chi (5-bit) | 15 | 13 | 13, opt in [12, 13] | 13 | 13, opt in [11, 13] |

Every BGC and GC result equals the best published value except Midori Sb1 BGC (one gate more).
No small S-box result beats a published one. (Our wider `gc` model, which also allows ANDN and
ORN, reaches e.g. Keccak chi with 10 gates; that is a different gate library and is not
compared with GC.) Per-run details: `results/reports/small-2.md`.

## 3. AES S-box (FIPS-197), NIST model

### 3a. Improving starting implementations

| start | caps | result | gates by type | time (CPU) |
|---|---|---|---|---|
| naive ANF: 1247 G, A246, GD14, AD6 | - | **717 G**, A264, GD50, AD19 | AND 264, XOR 258, XNOR 194, NOT 1 | 510 s (4005 s) |
| Boyar-Peralta 113 (NIST `aes-sbox-fwd-g113-a32-d27-ad6`): A32 AD6 GD27 | - | **108 G**, A33, AD5, GD26 | AND 33, XOR 54, XNOR 21 | 246 s (1939 s) |
| Boyar-Peralta 113 | AD<=6, GD<=27 | **108 G**, A33, AD5, GD23 | AND 33, XOR 45, XNOR 30 | 223 s (1721 s) |

`campaigns/aes_starts.sh OUT 300000 1-8 8 2`. The 108-gate circuits improve the classic
113-gate circuit by 5 gates, but NIST's 2026 circuits (104 G, A32 AD5 GD30; 108 G, A33 AD4
GD20) are already better, so these are not new on the published set. From the naive ANF the
search does not find the tower-field structure (717 vs ~104).

### 3b. Every published NIST circuit, under its own caps

For each of the 46 forward circuits in `nonlinear/nist/aes-sbox/`: start from it, caps A <= A0,
AD <= AD0, GD <= GD0, objective `cost,gd`, `--iters 100000 --seeds 1-8`
(`campaigns/nist_frontier.sh OUT aes-sbox 100000 1-8 8`, about 3 min per circuit). **33 of 46
improved** (fewer gates, or the same gates at lower depth); **18 results are new on NIST's
published set** (no published circuit has A, AD, G and GD all <=). Full table:
[results/reports/aes-nist-frontier.md](results/reports/aes-nist-frontier.md). Selected:

| NIST start (A AD G GD) | result (A AD G GD) | new on published set |
|---|---|---|
| a32-ad5-g109-gd20 (32 5 109 20) | **32 5 108 20** | yes |
| a32-ad5-g131-gd15 (32 5 131 15) | **32 5 129 15** | yes |
| a28-ad4-g154-gd15 (28 4 154 15) | **28 4 153 15** | yes |
| a28-ad4-g177-gd14 (28 4 177 14) | **28 4 176 14** | yes |
| a28-ad4-g131-gd32 (28 4 131 32) | **28 4 131 26** | yes |
| a33-ad4-g110-gd20 (33 4 110 20) | **33 4 110 18** | yes |
| a36-ad4-g137-gd14 (36 4 137 14) | **36 4 134 14** | yes |
| a39-ad4-g148-gd13 (39 4 148 13) | **39 4 137 13** | yes |
| a45-ad4-g151-gd12 (45 4 151 12) | **45 4 146 12** | yes |
| a49-ad4-g164-gd11 (49 4 164 11) | **49 4 150 11** | yes |
| a30-ad4-g205-gd15 (30 4 205 15) | 30 4 181 15 | no (dominated by a28-ad4-g154-gd15) |
| a46-ad3-g250-gd15 (46 3 250 15) | 46 3 207 15 | no (dominated by a35-ad3-g157-gd15) |
| a32-ad5-g104-gd30, a32-ad7-g103-gd32, a33-ad4-g105-gd25 | unchanged | - |

The searches change nonlinear structure as well as XOR layers: under the depth-only caps of
3c the AND count of the 14-level circuit rises from 33 to 41 while G falls.

### 3c. Fewest gates at a gate-depth cap (A and AD free)

Published best = the smallest G among all 49 NIST forward circuits (2020 and 2026) with
GD <= cap. Ours = the best verified result in `results/aes/` with GD <= cap.

| GD <= | published best G | **ours** | ours: A, AD, GD; gates by type | from |
|---|---|---|---|---|
| 11 | 157 (A51 AD4) | **150** | A49 AD4 GD11 | NIST a49-ad4-g164-gd11, 3b |
| 12 | 151 (A45 AD4) | **146** | A45 AD4 GD12; AND 45 XOR 55 XNOR 46 | NIST a45-ad4-g151-gd12, 3b and 3c |
| 13 | 148 (A38 AD4) | **137** | A39 AD4 GD13 | NIST a39-ad4-g148-gd13, 3b |
| 14 | 137 (A36 AD4) | **126** | A41 AD4 GD14; AND 41 XOR 45 XNOR 40 | NIST a33-ad4-g116-gd15 repaired to GD 14 |
| 18 | 116 (A33 AD4) | **110** | A33 AD4 GD18 | NIST a33-ad4-g110-gd20, 3b |
| 19 | 116 (A33 AD4) | **108** | A33 AD4 GD19 | NIST a33-ad4-g108-gd20, 3b |
| 15-17, 20-32 | 116 / 108 / 105 / 104 / 103 | not improved | | |
| 10 | none published (min GD 11) | not reached | | GD-10 repair failed |

GD <= 14 command (3 rounds, 8 seeds, 300000 iterations, 460 s wall, 3558 CPU s):

```bash
python3 nonlinear/boolflux/cli.py run --target aes --model nist \
  --start nonlinear/nist/aes-sbox/aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt \
  --objective cost,gd --cap-gd 14 --iters 300000 --seeds 1-8 --jobs 8 --rounds 3 --out OUT
```

NIST's open target "G <= 110 with GD <= 14" is not reached (126). The global record G = 104
(GD 30) and the open targets A <= 27 and G <= 100 are not improved.

## 4. Reproduction

Runs that end on their iteration budget are deterministic. Checked: the 3b run for
a32-ad5-g109-gd20 (`cli.py run ... --cap-a 32 --cap-ad 5 --cap-gd 20 --iters 100000 --seeds 1-8`)
re-run from scratch gives a byte-identical gate list. Each run directory keeps the sources it
ran (`src/`) and the binaries built from them (`bin/`); `summary.json` has the hash, the exact
command, every job's kernel seed (`seed + 1000 * round`), and the iteration of each improvement.
The commands in `results/*/*.summary.json` write to the campaign folder
`~/xs-campaigns/2026-11-13-boolflux/...`; any `--out` works.
