# BoolFlux

An optimizer for circuits of complete Boolean functions (S-boxes and other small functions)
over a configurable gate library, with configurable costs, objectives and constraints. It is
the nonlinear extension of XORFlux (`search/xorflux`, unchanged): the search can change the
nonlinear structure (which AND/OR/NAND/... gates exist, their operands and their number), not
only the XOR layers around a fixed AND skeleton.

| What | Where |
|---|---|
| method, representation, verification | [DESIGN.md](DESIGN.md) |
| measured results, with commands | [LEDGER.md](LEDGER.md) |
| current state and open items | [CHECKPOINT.md](CHECKPOINT.md) |
| gate-level search kernel (C) | [kernel/bfx.c](kernel/bfx.c) |
| AND-skeleton search kernel (C) | [kernel/skel.c](kernel/skel.c) |
| cost models (gate library + costs) | [models/](models/) |
| S-box tables with sources, published results | [benchmarks/](benchmarks/) |
| independent verifier (no shared code) | [independent/](independent/) |
| independent correctness review, fuzzers | [review/REVIEW.md](review/REVIEW.md) |
| verified result circuits (NCFF), their provenance and NIST-format copies | [results/](results/), [results/MANIFEST.json](results/MANIFEST.json), [results/nist-format/](results/nist-format/) |
| proof sources for optimality claims | [benchmarks/CITATIONS.md](benchmarks/CITATIONS.md) |
| independent audit of all claims | [audit/AUDIT.md](audit/AUDIT.md) |
| campaign scripts and reports | [campaigns/](campaigns/) |

Python 3.11+ (standard library only) and a C compiler (gcc). Run from the repository root.

```bash
# a search: target, model (gate library + costs), objective (lexicographic), caps
python3 nonlinear/boolflux/cli.py run --target aes --model nist \
    --start nonlinear/nist/aes-sbox/aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt \
    --objective cost,gd --cap-gd 14 --iters 300000 --seeds 1-8 --rounds 3 --out runs/aes-gd14

# skeleton search + synthesis + gate search in rounds (small functions, naive start)
python3 nonlinear/boolflux/cli.py pipe --target ascon --model bgc --start anf --objective cost \
    --iters 100000 --skel-iters 2000 --seeds 1-8 --rounds 3 --out runs/ascon-bgc

# check any circuit file with both verifiers
python3 nonlinear/boolflux/cli.py verify FILE.circ.txt --target aes --model nist

python3 -m unittest discover -s nonlinear/boolflux/tests -t nonlinear
python3 -m unittest discover -s nonlinear/boolflux/independent
```

- **Targets**: `aes`, `aes-inv` (computed from FIPS-197), every S-box in
  `benchmarks/sboxes.json` (present, gift, skinny64, prince, midori_sb0/1, piccolo, rectangle,
  klein, noekeon, pride, serpent_s0..s7, printcipher, chi3, ascon, keccak_chi5, skinny128,
  sm4, camellia_s1), and `maj3`, `fulladd`, `gf16-mul`, `gf16-inv`.
- **Models**: `nist` (AND, XOR, XNOR, NOT; NOT written as `XNOR t a 0`, each 1: NIST's
  accounting), `bgc` (AND, OR, XOR, NOT: bitslice gate complexity), `gc6` (AND, OR, XOR, XNOR,
  NAND, NOR, NOT: the gate complexity of Stoffelen 2016 and Zhang-Huang 2023), `gc` (every
  two-input gate including ANDN/ORN, and NOT; wider than the literature GC), `xag` (AND, XOR, NOT). A model is a JSON file of allowed gates and their costs
  (fractional costs such as GE areas work).
- **Objective** keys: `cost`, `g` (gate count), `a` (nonlinear gates), `gd` (gate depth), `ad`
  (AND depth), up to three, lexicographic. **Caps**: `--cap-gd`, `--cap-ad`, `--cap-a`; a start
  that violates them is repaired first.
- **Bit order**: input `x0` is the most significant bit of the input integer, output `y0` the
  most significant bit of the output (NIST's AES convention).
- Every run directory holds `summary.json` (command, settings, code hash, every job's seed,
  improvements with iteration numbers, wall time), the code snapshot it ran (`src/`, `bin/`)
  and `best.circ.txt`. A run whose iteration budget ends it is deterministic: the same command
  gives the same circuit.
