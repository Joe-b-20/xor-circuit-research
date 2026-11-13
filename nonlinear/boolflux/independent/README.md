# Independent circuit verifier

`verify.py` is a second-opinion checker for Boolean circuit files (a subset of
NIST's NCFF and of NIST's 2020 `.slp` format). It is written from a written
specification only and imports nothing from `nonlinear/boolcirc`,
`nonlinear/boolflux` or `search/`. It uses only the Python 3.12 standard library.

## What is checked

1. **Structure** (the first circuit in the file; a note is printed if there are more):
   distinct input names; every wire assigned exactly once; inputs never assigned;
   every operand is an input, the constant `0`/`1`, or a wire assigned on an
   earlier line; every declared output assigned; known gate name; correct arity.
   Outputs may be used as operands later.
2. **Function**: exhaustive. For each input integer `x` in `0..2^n-1` the gates are
   evaluated one at a time on Python ints 0/1 and the outputs are compared with
   `table[x]`. The first mismatch `(x, expected, got)` is reported.
3. **Metrics**: `G` (gate lines excluding BUF), per-type counts, `A` (AND, NAND, OR,
   NOR, ANDN, ORN), `GD` (gate depth), `AD` (AND depth: only nonlinear gates add 1),
   `XX` (XOR+XNOR), `dead` (non-BUF gates outside every output's cone).
   With `--model`: library check (a gate type not listed under `gates` is a
   failure), `cost` (sum of per-type costs; BUF is free), and `WD` (weighted depth)
   when the model has `depth_weights`.
4. **Assertions**: `--expect-X N` / `--max-X N` for X in G, A, GD, AD, WD, cost.

## Conventions

- Gates: `XOR XNOR AND NAND OR NOR` (2 operands), `ANDN o a b` = a AND NOT b,
  `ORN o a b` = a OR NOT b (the second operand is complemented), `NOT o a`,
  `BUF o a` (free, depth passes through). Gate names are case-insensitive.
- Comments start at `%` or `#`. Lines before `begin circuit` are ignored, as are
  unknown header lines. `GateSyntax`, if present, must be `GateName Output Inputs`.
- Ranges `x0:x7` expand in the written direction (`x7:x0` = x7 ... x0).
- Bit order `msb/msb` (default): the i-th declared input is bit n-1-i of `x`, the
  j-th declared output is bit m-1-j of `table[x]`. `--in-order lsb` /
  `--out-order lsb` / `--order lsb` make the i-th wire bit i. `--any-order` tries all
  four pairs and reports which ones match.
- The AES S-box is computed here from FIPS-197 (inverse in GF(2^8) mod 0x11B, then
  the affine map with c = 0x63) and self-checked.

## How to run

From the repository root (in WSL):

```
python3 nonlinear/boolflux/independent/verify.py nonlinear/nist/aes-sbox/*.circ.txt --aes
python3 nonlinear/boolflux/independent/verify.py nonlinear/nist/aes-invsbox/*.circ.txt --aes-inv
python3 nonlinear/boolflux/independent/verify.py FILE --table sboxes.json --name NAME --model model.json --json
python3 nonlinear/boolflux/independent/verify.py FILE --fn fn.json --any-order --expect-G 104 --max-AD 5
python3 -m unittest discover -s nonlinear/boolflux/independent -v
```

Function files: `--table` takes `{"sboxes": [{"name", "n", "m", "table"}, ...]}`,
`--fn` takes one `{"n", "m", "table"}` object. A model is
`{"name": ..., "gates": {"AND": 1, "XOR": 1, ...}, "depth_weights": {...}}`
(the `depth_weights` key is optional; types it does not list weigh 1).

Exit status: 0 if every file passes, 1 if any fails, 2 for a bad function table or
model file. Importable functions: `parse_circuit`, `parse_file`, `check_function`,
`compute_metrics`, `verify_file`, `verify_text`, `aes_sbox`, `aes_inv_sbox`,
`load_table`, `load_fn`, `load_model`.
