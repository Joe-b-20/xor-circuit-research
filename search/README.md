# Search

Two searches found the circuits in [circuits/](../circuits/README.md). **XORFlux** looks for
XOR circuits with few gates, then low depth, for GF(2) linear maps of any size. **BoolFlux**
looks for circuits of complete Boolean functions, such as S-boxes, with AND gates and a gate
library of your choice: few gates, few ANDs or low depth, under hard caps. XORFlux needs Python
3.11 or newer and nothing else; BoolFlux also needs gcc.

| Folder | Search | For | Docs |
|---|---|---|---|
| [linear/](linear/README.md) | XORFlux | linear maps (matrices over GF(2)), 2-input XOR gates | [how it works](linear/HOW-IT-WORKS.md), [usage](linear/USAGE.md), [history](linear/HISTORY.md), [design](linear/xorflux/DESIGN.md) |
| [nonlinear/](nonlinear/README.md) | BoolFlux | Boolean functions of up to about 16 inputs, any 2-input gates | [how it works](nonlinear/HOW-IT-WORKS.md), [usage](nonlinear/USAGE.md), [history](nonlinear/HISTORY.md), [design](nonlinear/boolflux/DESIGN.md) |

```bash
python3 search/linear/xorflux quick aes-mixcolumns --seconds 60          # XORFlux: one worker, one minute
python3 search/nonlinear/boolflux/cli.py run --target present --model bgc --objective cost \
    --iters 20000 --seeds 1 --jobs 1 --out OUT/present                   # BoolFlux: the PRESENT S-box
```

Run every command from the repository root. The two searches share no code. Each writes
circuits in NIST's file format; [circuits/check.py](../circuits/check.py) checks them without
either search's code.
