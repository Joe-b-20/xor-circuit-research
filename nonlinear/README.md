# nonlinear

Boolean circuits with AND gates: the AES S-box and its inverse, NIST's circuits for them, and
the ground for extending the search beyond linear maps. The linear search, XORFlux v8 in
[search/](../search/README.md), is untouched by anything here and stays the baseline.

| What | Where |
|---|---|
| NIST's AES S-box and inverse S-box circuits, verbatim, with a manifest | [nist/](nist/) |
| `boolcirc`, a standard-library package: circuit files with full gate semantics, truth-table verification, NIST's metrics, GF(2) linear algebra, the AND skeleton | [boolcirc/](boolcirc/) |
| the checker: every circuit against its function, twice, plus its metrics against its name and NIST's header | [check.py](check.py) |
| the importer that wrote `nist/` (pinned to one NIST commit) | [tools/import_nist.py](tools/import_nist.py) |
| the mathematical representation and the constraints on AND inputs and outputs | [THEORY.md](THEORY.md) |
| BoolFlux: the optimizer for complete Boolean functions over configurable gate libraries, its results and ledger | [boolflux/](boolflux/README.md) |

```bash
python3 nonlinear/check.py                                        # every circuit in nist/ (and circuits/)
python3 nonlinear/check.py nonlinear/nist/aes-sbox                # one folder or file
python3 -m unittest discover -s nonlinear/boolcirc/tests -t nonlinear
```

## NIST's circuits

`nist/` holds the 191 circuit files of `data/slp/aes/{aes-sbox, aes-invsbox, sbox, old-2020}`
of NIST's [circuit repository](https://github.com/usnistgov/Circuits) at commit
`e6ac0d03f4816927f1b0e676996e4d075ab8d1c0` (2026-11-13; first imported at 0876577, 2026-10-29), byte for byte, with each folder's
NIST `README.md` kept as `NIST-README.md`. `nist/MANIFEST.json` records for every file its NIST
path and URL at that commit, SHA-256 and size, and what the checker established: its metrics,
whether its file name and NIST's header tallies agree with them (they all do), and the bit
order under which it equals FIPS-197 (for every file: input `U0`/`x0` is bit 7 of the input byte
and output `S0`/`y0` bit 7 of the output byte, written `msb/msb`). The files are NIST's data
under NIST's terms, and some are external contributions that keep their authors' rights; see
[NOTICE](../NOTICE).

The two circuits the extension is to be measured against, both from `nist/aes-sbox/`:

| Circuit | A | AD | G | GD | XOR | XNOR | What it is best at |
|---|---:|---:|---:|---:|---:|---:|---|
| `aes-sbox-a32-ad5-g104-gd30-xx72-5` | 32 | 5 | 104 | 30 | 67 | 5 | fewest gates at AND depth 5 (NIST, 2026-10) |
| `aes-sbox-a28-ad5-g124-gd27-xx96-26` | 28 | 5 | 124 | 27 | 70 | 26 | fewest ANDs (contributed by Milad Nasr, 2026-09; 10 + 5 + 13 ANDs in a tower-field structure) |

NIST's open targets for the S-box are A ≤ 27, G ≤ 100, and G ≤ 110 with GD ≤ 14.

## Metrics

NIST names every circuit `<base>-aA-adAD-gG-gdGD-xxX-Y`; the four metrics NIST tracks and the
two extra numbers are:

| | Meaning | Convention used here |
|---|---|---|
| A | number of AND gates (multiplicative size) | NAND, OR and NOR would count as ANDs; NIST's files use none |
| AD | AND depth | most AND gates on any input-to-output path |
| G | number of gates | every gate, a NOT included |
| GD | gate depth | longest path in gates, inputs at depth 0; a NOT counts one level |
| X | #XOR + #XNOR | |
| Y | #XNOR | |

NIST's pages do not say how a NOT counts; its files avoid the question by writing a NOT as
`XNOR t U 0`, a two-input gate with the literal constant `0`, and that is how `boolcirc` reads
it (nothing is rewritten on input). The conventions above reproduce NIST's own numbers in all
191 files: the file names (including the -xxnX-Y-Z names, X = XOR+XNOR+NOT, used from e6ac0d0 on) and the per-level tallies NIST writes in every 2026 header.

## Verification

`check.py` verifies a circuit by complete truth table, twice and independently: once by
replaying its gate list (`boolcirc.truth`), once from its AND skeleton (`boolcirc.skeleton`:
every wire as an affine form over the inputs and the AND outputs, evaluated with the AND outputs
as new variables). Both are compared with the function computed from FIPS-197's definition
(inversion in GF(2⁸) modulo x⁸+x⁴+x³+x+1, then the affine map with constant 0x63), under both
input and both output bit orders; a circuit passes when some order matches, and the order is
reported. For other functions, a `*.fn.json` value table in the circuit's folder names the
target.
