# BoolFlux benchmark ledger

> **2026-11-14:** this ledger is the 2026-11-13 study, against NIST pin e6ac0d0. Sections 1 and 2
> still hold. For AES, the current status against pin 3d80774 (41 Pareto tuples, including the
> AES-push results) is in [results/MANIFEST.json](results/MANIFEST.json) (`aes_pareto`,
> `pinned_set`), [README.md](README.md) and [HISTORY.md](HISTORY.md). Of the 12 tuples in
> section 3b, 34/4/139/13 now equals a published circuit, and five are dominated by later
> results of ours.

Corrected 2026-11-13 against NIST's repository usnistgov/Circuits at commit
**e6ac0d03f4816927f1b0e676996e4d075ab8d1c0** (imported verbatim into `nonlinear/nist/`, 191
files, all verified; `nonlinear/nist/MANIFEST.json`). An earlier version of this ledger compared
with commit 0876577 (46 forward circuits in `aes-sbox/`) and claimed improvements that the newer
NIST circuits now beat; those claims are withdrawn below.

**Verification of every claimed circuit.** [results/MANIFEST.json](results/MANIFEST.json) lists
each circuit with its sha256, target and its definition, model (permitted gates and costs),
objective, caps, starting circuit (path, sha256, the NIST commit it was taken from — all 35 NIST
starts are byte-identical at e6ac0d0), command, seeds, iterations, rounds, code hash and time.
Each passed (1) `core` (bitsliced, against `targets.py` / `benchmarks/sboxes.json`) and (2)
`independent/verify.py` (exhaustive per-input evaluation, own AES and table code, library check,
cap check; its G, A, GD, AD, cost and counts must equal core's). AES circuits were also exported
in NIST's format to [results/nist-format/](results/nist-format/) (explicit NOT gates, NIST names
`aes-sbox-aA-adAD-gG-gdGD-xxX-Y`) and pass (3) `nonlinear/check.py` (boolcirc, the counter that
reproduces all 191 NIST file names). (4) An independent audit with its own evaluator and counter
([audit/AUDIT.md](audit/AUDIT.md), `audit/audit.py`) recounted every file, re-ran on the final
result set (`audit/run-final.log`) and agrees with everything below.

Machine: Intel Core i7-13700H, 20 logical CPUs, WSL2 Ubuntu, gcc -O2, Python 3.12. Runs that end
on their iteration budget are deterministic; two were re-run from scratch and gave identical gate
lists (3b's a32-ad5-g109-gd20 run and 3c's GD <= 14 run). Each run directory keeps its source
snapshot and binaries. Of the 101 claimed circuits, 98 come from snapshot b0e56ecb18fe and 3 from
8336425daeeb (the committed sources); the two differ only in `core.py` (a header comment) and
`targets.py` (removal of a mislabelled built-in chi), which change no search on any other target.
Four earlier sanity circuits made before snapshots
existed, and two chi3 circuits made for a bit-reversed chi (wrong target name), are kept in
`results/_superseded/` and not claimed.

**Models** ([models/](models/)): `nist` = AND, XOR, XNOR, NOT, each 1 (NOT counted as a gate and
a depth level, as NIST counts it; written `XNOR t a 0` in our files, `NOT` in the NIST-format
copies; no OR/NAND, no free inversions, no BUF in any AES result). `bgc` = AND, OR, XOR, NOT, each
1 (bitslice gate complexity, Stoffelen 2016 Sect. 3). `gc6` = AND, OR, XOR, XNOR, NAND, NOR, NOT,
each 1 (gate complexity as in Stoffelen 2016 and Zhang-Huang 2023, Table 2 and Remark 2; our
wider `gc`, which adds ANDN/ORN, is a different library and is not compared). `xag` = AND, XOR,
NOT. Metrics: G gates, A nonlinear gates, GD gate depth (inputs 0, every gate +1), AD AND depth.

**Claims.** *Improves its start*: under the same model and caps the search returned a better
circuit than the one it was given. *New on the published set*: no circuit of the pinned baseline
has all compared metrics <= ours, and no other result of ours strictly dominates it (identical
tuples counted once). Proof sources for "optimal" are in
[benchmarks/CITATIONS.md](benchmarks/CITATIONS.md); everything else is an upper bound.

## 1. Known-improvable sanity cases (naive ANF starts, xag)

| function | start (ANF) | result | known (source) | time |
|---|---|---|---|---|
| majority of 3 | 5 gates, 3 AND | **4 gates, 1 AND** (AND 1, XOR 3) | 4 is the minimum over all 2-input gates (our exhaustive search, benchmarks/LITERATURE.md Sect. 6); MC 1 | 0.2 s |
| full adder | 7 gates, 3 AND | **5 gates, 1 AND** (AND 1, XOR 4) | 5 is the minimum over all 2-input gates (Kulikov, DATE 2018, Sect. III; our exhaustive search); MC 1 | 0.3 s |
| GF(2^4) multiplication, mod x^4+x+1 (pipe) | 34 gates, 16 AND (schoolbook) | **32 gates, 9 AND** (AND 9, XOR 23) | 9 = bilinear complexity mu_2(4) (Chudnovsky-Chudnovsky 1988, Ex. 3.2; Ballet et al. 2021, Table 1): minimum for bilinear circuits. Our ANDs may mix both inputs; whether fewer ANDs suffice in unrestricted circuits is open as far as we know | 82 s |
| GF(2^4) multiplication, gate level only | 34, 16 AND | 30 gates, 14 AND | - | 17 s |
| GF(2^4) inversion, mod x^4+x+1 (pipe, a,cost) | 33, 10 AND | **17 gates, 5 AND** | MC 5 is proved and basis-independent (Boyar-Matthews-Peralta 2013, Sect. 2.1). BMP's 16-gate circuit (5 AND + 11 XOR, Fig. 2) uses Canright's normal-basis tower field, not comparable gate for gate | 15 s |
| GF(2^4) inversion (pipe, cost) | 33, 10 AND | **15 gates**, 6 AND | Maximov-Ekdahl's slides report 15 "conventional" gates, depth 3; paper, basis and gate set not read | 14 s |

The GF(2^4) multiplier is the nonlinear sanity check: 9 ANDs require replacing pairs of products
by one product of sums (Karatsuba), which the gate level alone does not find (14); the skeleton
merge move does. Reproduction: `results/reports/sanity-2.md`.

## 2. Small S-boxes from naive starts (bgc and gc6 kept separate)

`pipe --start anf --objective cost --iters 100000 --skel-iters 2000 --seeds 1-8 --rounds 3`
(`campaigns/small_sboxes.sh`, CONFIGS="bgc:cost gc6:cost"), 15-32 s each. Published values:
**SAT** = proved optimal; **[l, u]** = UNSAT at l-1 and SAT at u (Zhang-Huang 2023 Sect. 6), so u
is the best published circuit; **UB** = upper bound only (heuristic or designer circuit).
Sources: Sto16 = Stoffelen FSE 2016; ZH23 = Zhang-Huang ePrint 2023/1721; Sov23 = Sovyn et al.
2023, Table 7 (heuristic); spec = the cipher's specification.

| S-box | ANF start (bgc) | **BGC ours** | BGC published | **GC ours** (gc6) | GC published |
|---|---|---|---|---|---|
| PRESENT / LED | 32 | 14 | 14 UB (CHM11 Fig. 1, Sov23) | 13 | - |
| GIFT | 22 | 11 | 11 UB (Sov23, spec) | 10 | 10 UB (spec) |
| SKINNY-64 | 30 | 11 | 11 UB (Sov23) | 8 | 8 UB (spec) |
| PRINCE | 35 | 16 | 16 UB (Sov23) | 15 | - |
| Midori Sb0 | 29 | 13 | 13 UB (Sov23) | 12 | - |
| Midori Sb1 | 35 | 16 | **15** UB (Sov23) | 15 | - |
| Piccolo | 31 | 10 | 10 SAT (Sto16 T3, ZH23 T3) | 8 | 8 SAT (Sto16 T5, ZH23 T4) |
| RECTANGLE | 27 | 12 | [11, 12] (ZH23 T10) | 11 | 11 SAT (ZH23 T11) |
| KLEIN | 38 | 17 | 17 UB (Sov23) | 15 | - |
| Noekeon | 28 | 12 | 12 UB (Sov23) | 10 | - |
| PRIDE (= Prost) | 17 | 8 | 8 SAT (Sto16 T3) | 8 | 8 SAT (Sto16 T5) |
| Serpent S0..S7 | 32-38 | 14 14 13 15 15 15 14 16 | 14 14 13 15 15 15 14 16 UB (Sov23) | 13 13 12 15 13 14 13 14 | - |
| PRINTcipher (3-bit) | 9 | 6 | - | 6 | - |
| chi (3-bit, spec table) | 9 | 7 | - | 7 | - |
| Ascon (5-bit) | 35 | 16 | [12, 16] (ZH23 T10) | 15 | [12, 15] (ZH23 T11) |
| Keccak chi (5-bit) | 15 | 13 | [12, 13] (ZH23 T10; Sto16 <= 13) | 13 | [11, 13] (ZH23 T11) |

Every BGC and GC result equals the best published value, except Midori Sb1 BGC (one more). Where
the published value is SAT-proved (Piccolo, PRIDE, RECTANGLE GC) ours is therefore optimal by that
proof; elsewhere ours equals an upper bound. **No small S-box result beats a published one.**
Longer runs on RECTANGLE BGC and Midori Sb1 BGC (20 seeds x 5 rounds x 400000 iterations) did not
change them. Reproduction: `results/reports/small-2.md`, chi3 in `small-3`.

## 3. AES S-box (FIPS-197), NIST model, baseline e6ac0d0

The baseline is NIST's 102 forward AES S-box circuits at e6ac0d0 (`aes-sbox/` 78,
`old-2020/aes-sbox-fwd-*` 3, `sbox/aes-sbox-fwd-*` 21; 90 distinct (A, AD, G, GD) tuples), with
metrics recomputed from the files. Script: `campaigns/pareto_audit.py`.

### 3a. Improving starting implementations

| start | caps | result | gates by type (as written) | time (CPU) |
|---|---|---|---|---|
| naive ANF: 1247 G, A246, GD14, AD6 | - | **717 G**, A264, GD50, AD19 | AND 264, XOR 258, XNOR 195 | 510 s (4005 s) |
| Boyar-Peralta 113 (`old-2020/aes-sbox-fwd-g113-a32-d27-ad6.slp`): A32 AD6 GD27 | - | **108 G**, A33, AD5, GD26 | AND 33, XOR 54, XNOR 21 | 246 s (1939 s) |
| Boyar-Peralta 113 | AD<=6, GD<=27 | **108 G**, A33, AD5, GD23 | AND 33, XOR 45, XNOR 30 | 223 s (1721 s) |

`campaigns/aes_starts.sh OUT 300000 1-8 8 2`. These improve their starts only: NIST's circuits
(104 G at A32 AD5 GD30; 106 G at A33 AD4 GD22) dominate them.

### 3b. New points on NIST's published (A, AD, G, GD) set

Every one of NIST's 78 `aes-sbox/` circuits was searched under its own caps (A <= A0, AD <= AD0,
GD <= GD0), objective `cost,gd`, `--iters 100000 --seeds 1-8` (`campaigns/nist_frontier.sh OUT
aes-sbox 100000 1-8 8`; 46 circuits of the old pin in run `frontier-fwd-2`, the 32 added by
e6ac0d0 in `frontier-fwd-3`; 37-68 s wall each on 8 CPUs). 48 of the 78 got fewer gates, or the
same gates at a lower depth. Of the 49 AES result files (46 distinct tuples), **12 tuples survive**
(13 files): no published circuit has all four metrics <=, and no other result dominates them:

| A AD G GD | start (NIST, e6ac0d0) | caps | nearest published circuits (why they do not dominate) | NIST-format file |
|---|---|---|---|---|
| 36 4 **131** 13 | a36-ad4-g142-gd13 | A36 AD4 GD13 | a35-ad4-g133-gd13 (G 133) | aes-sbox-a36-ad4-g131-gd13-xx95-42 |
| 34 4 **139** 13 | a34-ad4-g140-gd13 | A34 AD4 GD13 | a35-ad4-g133-gd13 (A 35), a34-ad4-g140-gd13 (G 140) | aes-sbox-a34-ad4-g139-gd13-xx105-42 |
| 38 4 **124** 14 | a33-ad4-g116-gd15, repaired to GD 14 (benchmark run, see below) | GD14 | a33-ad4-g127-gd14 (G 127) | aes-sbox-a38-ad4-g124-gd14-xx86-37 |
| 35 3 **167** 14 | a35-ad3-g172-gd14 | A35 AD3 GD14 | a35-ad3-g172-gd14 (G 172) | aes-sbox-a35-ad3-g167-gd14-xx132-58 |
| 32 4 **126** 15 | a32-ad4-g127-gd15 | A32 AD4 GD15 | a32-ad4-g127-gd15 (G 127), a33-ad4-g116-gd15 (A 33) | aes-sbox-a32-ad4-g126-gd15-xx94-32 |
| 33 4 **110** 18 | a33-ad4-g110-gd20 | A33 AD4 GD20 | a33-ad4-g116-gd15 (G 116), a33-ad4-g110-gd20 (GD 20) | aes-sbox-a33-ad4-g110-gd18-xx77-26 |
| 32 4 **122** 18 | a32-ad4-g137-gd18 | A32 AD4 GD18 | a32-ad4-g127-gd15 (G 127), a32-ad4-g117-gd19 (GD 19) | aes-sbox-a32-ad4-g122-gd18-xx90-39 |
| 33 4 **108** 19 | a33-ad4-g108-gd20 | A33 AD4 GD20 | a33-ad4-g108-gd20 (GD 20) | aes-sbox-a33-ad4-g108-gd19-xx75-22 |
| 32 5 **108** 20 | a32-ad5-g109-gd20 | A32 AD5 GD20 | a32-ad5-g107-gd22 (GD 22), a32-ad5-g109-gd20 (G 109) | aes-sbox-a32-ad5-g108-gd20-xx76-35 |
| 28 4 **133** 20 | a28-ad4-g134-gd20 | A28 AD4 GD20 | a28-ad4-g134-gd20 (G 134) | aes-sbox-a28-ad4-g133-gd20-xx105-55 |
| 35 3 **144** 20 | a35-ad3-g148-gd20 | A35 AD3 GD20 | a35-ad3-g147-gd20 (G 147) | aes-sbox-a35-ad3-g144-gd20-xx109-56 |
| 28 4 **131** 26 | a28-ad4-g131-gd32 and a28-ad4-g131-gd36 (two different circuits) | A28 AD4 GD32 / GD36 | a28-ad4-g131-gd31 (GD 31), a28-ad4-g132-gd22 (G 132) | aes-sbox-a28-ad4-g131-gd26-xx103-{50,46} |

Withdrawn from the previous ledger (dominated or equalled at e6ac0d0): 150@11 and 152@11 (NIST
a49-ad4-g148-gd11), 146@12 (a45-ad4-g141-gd12), 137@13 and 138@13 (a35-ad4-g133-gd13),
134@14 (a33-ad4-g127-gd14), 129@15 (a32-ad4-g127-gd15), 28-4-153-15 and 28-4-176-14 and
28-4-132-22 and 35-3-139-27 (equal to NIST tuples), and the rest of the old "18 new". The full
table, including every dominated result and which circuits dominate it, is
`results/reports/aes-pareto-e6ac0d0.md`.

### 3c. Fewest gates at a gate-depth cap (A and AD free)

Published best = smallest G among the 102 baseline circuits with GD <= cap.

| GD <= | published best (A AD G GD) | **ours** (A AD G GD) | margin |
|---|---|---|---|
| 13 | 35 4 133 13 | **36 4 131 13** | -2 gates |
| 14 | 33 4 127 14 | **38 4 124 14** | -3 gates (5 more ANDs) |
| 18 | 33 4 116 15 | **33 4 110 18** | -6 gates |
| 19 | 33 4 116 15 | **33 4 108 19** | -8 gates |
| 10 / 11 / 12 | 159 / 148 / 141 | not better (best: none at 10, 150, 146) | |
| 15-17 / 20-21 / 22-24 / 25-29 / 30-31 / 32-40 | 116 / 108 / 106 / 105 / 104 / 103 | not better (108 at 20 ties) | |

The 14-level circuit shows the search changing nonlinear structure: from NIST's 33-AND depth-15
circuit it trades depth for ANDs (38) while cutting gates. NIST's open targets (A <= 27, G <= 100,
G <= 110 at GD <= 14) and the overall record (103 at GD 32, 104 at GD 30) are not reached.

GD <= 14: the 124-gate circuit (A38) came from a time-budgeted run of the method-and-performance
benchmark (`bench/bench.py`, plan v3, run `A-aes-gd14repair-rebuild-s4-v3`: NIST a33-ad4-g116-gd15,
cap GD <= 14, rebuild-only full configuration, 120 s, seed 4); it is verified but not
bit-reproducible; 2 of the 35 such 120 s runs reached GD 14 and only this one went below 127
(`bench/REPORT.md`, 4.3). It dominates
the earlier reproducible 126-gate circuit (A41), which this command gives
(300000 iterations, 8 seeds, 3 rounds; 460 s wall, 3558 CPU s):

```bash
python3 nonlinear/boolflux/cli.py run --target aes --model nist \
  --start nonlinear/nist/aes-sbox/aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt \
  --objective cost,gd --cap-gd 14 --iters 300000 --seeds 1-8 --jobs 8 --rounds 3 --out OUT
```

GD <= 13 (the 3b run from a36-ad4-g142-gd13, 46 s wall):

```bash
python3 nonlinear/boolflux/cli.py run --target aes --model nist \
  --start nonlinear/nist/aes-sbox/aes-sbox-a36-ad4-g142-gd13-xx106-19.circ.txt \
  --objective cost,gd --cap-a 36 --cap-ad 4 --cap-gd 13 --iters 100000 --seeds 1-8 --jobs 8 --out OUT
```

Every other command is in `results/MANIFEST.json` (`command`; its `--out` points to the campaign
folder `~/xs-campaigns/2026-11-13-boolflux/`, any folder works).
