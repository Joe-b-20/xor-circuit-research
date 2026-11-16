# BoolFlux

**BoolFlux: search for small circuits of complete Boolean functions.** It looks for circuits
with few gates, few AND gates or low depth for S-boxes and other functions of up to about 16
inputs, over a gate library and cost model you choose, with hard caps on gate depth, AND depth
and AND count. Its moves change which AND gates exist and what they read, not only the XOR
layers around them. It needs Python 3.11 or newer (standard library only) and gcc.

The code is in [`boolflux/`](boolflux/). It has no version numbers yet and is still being
developed. Its circuits are in [circuits/](../../circuits/README.md), next to NIST's. Each is
verified independently; [REPRODUCE.md](../../circuits/REPRODUCE.md) replays six of them from
public commits, and each circuit's `found.json` says what its run recorded.

| Page | What is in it |
|---|---|
| [HOW-IT-WORKS.md](HOW-IT-WORKS.md) | the method: truth tables, the gate move, acceptance, the AND skeleton, the moves around the kernel, the hub |
| [USAGE.md](USAGE.md) | how to run it: commands, targets, models, caps, settings, checking AES circuits, output |
| [HISTORY.md](HISTORY.md) | how it came to be: each stage, the failed experiments, the decisions they led to |
| [boolflux/DESIGN.md](boolflux/DESIGN.md) | developer reference: formats, the kernels, interfaces, the evidence behind the defaults |
| [boolflux/independent/README.md](boolflux/independent/README.md) | the second verifier, which shares no code with BoolFlux |

```bash
python3 search/nonlinear/boolflux/cli.py list                            # targets, models, objective keys
python3 search/nonlinear/boolflux/cli.py run --target maj3 --model xag --objective a,cost \
    --iters 3000 --seeds 1 --jobs 1 --out OUT/maj3                     # majority of 3: 4 gates, 1 AND
```

Run every command from the repository root.

| Folder | Content |
|---|---|
| [boolflux/](boolflux/) | the code: C kernels, Python layer, hub, method scripts, tests |
| [seeds/](seeds/) | NIST's AES S-box circuits, verbatim, with a manifest and the pin; the importer |
| [campaigns/](campaigns/) | scripts of the small-S-box and depth campaigns |

## NIST's metrics

NIST names every circuit `<base>-aA-adAD-gG-gdGD-xxX-Y`. BoolFlux and
[circuits/check.py](../../circuits/check.py) count the same way:

| | Meaning | Convention |
|---|---|---|
| A | number of AND gates | NAND, OR and NOR would count as ANDs; NIST's files use none |
| AD | AND depth | most AND gates on any input-to-output path |
| G | number of gates | every gate, a NOT included |
| GD | gate depth | longest path in gates, inputs at depth 0; a NOT counts one level |
| X | #XOR + #XNOR | in the `-xxnX-Y-Z` names, X = XOR + XNOR + NOT |
| Y | #XNOR | |

NIST's files write a NOT as `XNOR t U 0`, a two-input gate with the constant `0`. With these
conventions the metrics of all 204 circuit files in [seeds/](seeds/) match their names and
the per-level tallies in NIST's headers. Bit order is msb/msb: input `x0` (NIST's `U0`) is bit 7
of the input byte, output `y0` (`S0`) bit 7 of the output byte.
