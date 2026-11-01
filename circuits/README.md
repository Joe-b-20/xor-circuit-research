# circuits

The smallest circuit our search found at each depth, for each map. We don't claim that any of
them is optimal or the best known: they are what the search reached in the time it ran.
Published or unpublished work may have smaller or shallower circuits for some of these maps,
NIST's own list among them (see the NIST column), and more search time would likely improve
many of them. The only lower bounds here are for AES MixColumns ([lower-bound-proofs/](../lower-bound-proofs/README.md)).

One folder per map:

```
<map>/
  <map>.mat.txt                    the map: NIST matrix format
  <map>-xor<G>-depth<D>.circ.txt   a circuit with G gates and depth D: NIST circuit file format
  logs/<map>-xor<G>-depth<D>/      how it was found
```

## Check

```bash
python3 circuits/check.py                 # every circuit
python3 circuits/check.py circuits/joltik # one map, or one file
```

`check.py` uses the standard library only and none of the search code. It checks that each
output equals its matrix row and that the gate count and depth match the file name.

## Conventions

- Gates are 2-input XOR (XNOR only where a map has output constants). Inputs have depth 0.
- In `<map>.mat.txt`, the line `1`, then `rows cols`, then one 0/1 row per output: row `i` is
  `y_i`, column `j` is `x_j`, counting from 0. An optional last line of `rows` 0/1 values gives
  output constants (`y_i = row_i·x ⊕ c_i`).
- Each circuit's header names the search version that found it, how its worker started and
  where its logs are. Versions are listed in [search/HISTORY.md](../search/HISTORY.md#versions); the time each
  search ran and the hardware are in [SEARCH-TIME.md](SEARCH-TIME.md).

## Logs

| File | Content |
|---|---|
| `found.json` | version, code, run, worker, time, start circuit, chain root, list of log files |
| `record.json` | the circuit as the search wrote it |
| `dossier.json` | the improvement that produced it: move trace, state before and after, replay data |
| `events.jsonl.gz`, `worker.log`, `discoveries.jsonl.gz` | the worker's log |
| `plan.json.gz`, `campaign.toml`, `config.json` | the run's frozen settings |
| `seed.json` | the circuit the worker started from |
| `checkpoint.json.gz` | the worker checkpoint, for the two circuits that exist only there (¹) |

Older versions wrote fewer files; each `found.json` lists what is there.

## Circuits

201 circuits for 59 maps, grouped as in NIST's [list of circuits](https://csrc.nist.gov/projects/circuit-complexity/list-of-circuits): [AES](#aes) · [16×16](#1616) · [32×32](#3232) · [64×64](#6464) · [128×128](#128128). Sizes are inputs × outputs; notes are [below the tables](#notes).

## AES

### AES MixColumns

[aes-mixcolumns](aes-mixcolumns/): 32 inputs, 32 outputs, 152 XORs computed directly.

| Depth | Gates | Found by | NIST | Logs |
|---:|---:|---|---:|---|
| 3 | [97](aes-mixcolumns/aes-mixcolumns-xor97-depth3.circ.txt) | v7, `anneal3` constructor ³ | [97](https://github.com/usnistgov/Circuits/blob/master/data/slp/aes/aes-mixcols/aes-mixcols-xor97-depth3.circ.txt) | [logs](aes-mixcolumns/logs/aes-mixcolumns-xor97-depth3/) |
| 4 | [89](aes-mixcolumns/aes-mixcolumns-xor89-depth4.circ.txt) | v8 | [90](https://github.com/usnistgov/Circuits/blob/master/data/slp/aes/aes-mixcols/aes-mixcols-xor90-depth4.circ.txt) | [logs](aes-mixcolumns/logs/aes-mixcolumns-xor89-depth4/) |
| 5 | [88](aes-mixcolumns/aes-mixcolumns-xor88-depth5.circ.txt) | v7 | [88](https://github.com/usnistgov/Circuits/blob/master/data/slp/aes/aes-mixcols/aes-mixcols-xor88-depth5.circ.txt) | [logs](aes-mixcolumns/logs/aes-mixcolumns-xor88-depth5/) |
| 6 | — |  | 92 |  |

### AES InvMixColumns

[aes-invmixcolumns](aes-invmixcolumns/): 32 inputs, 32 outputs, 440 XORs computed directly.

| Depth | Gates | Found by | NIST | Logs |
|---:|---:|---|---:|---|
| 5 | [168](aes-invmixcolumns/aes-invmixcolumns-xor168-depth5.circ.txt) | v4 + polish ¹ | [119](https://github.com/usnistgov/Circuits/blob/master/data/slp/aes/aes-invmixcols/aes-invmixcols-xor119-depth5.circ.txt) | [logs](aes-invmixcolumns/logs/aes-invmixcolumns-xor168-depth5/) |
| 6 | [104](aes-invmixcolumns/aes-invmixcolumns-xor104-depth6.circ.txt) | v8 ⁵ | [106](https://github.com/usnistgov/Circuits/blob/master/data/slp/aes/aes-invmixcols/aes-invmixcols-xor106-depth6.circ.txt) | [logs](aes-invmixcolumns/logs/aes-invmixcolumns-xor104-depth6/) |
| 7 | [101](aes-invmixcolumns/aes-invmixcolumns-xor101-depth7.circ.txt) | v7 | [102](https://github.com/usnistgov/Circuits/blob/master/data/slp/aes/aes-invmixcols/aes-invmixcols-xor102-depth7.circ.txt) | [logs](aes-invmixcolumns/logs/aes-invmixcolumns-xor101-depth7/) |
| 8 | [96](aes-invmixcolumns/aes-invmixcolumns-xor96-depth8.circ.txt) | v6 | 96 | [logs](aes-invmixcolumns/logs/aes-invmixcolumns-xor96-depth8/) |
| 9 | [94](aes-invmixcolumns/aes-invmixcolumns-xor94-depth9.circ.txt) | v7 | 95 | [logs](aes-invmixcolumns/logs/aes-invmixcolumns-xor94-depth9/) |
| 10 | [93](aes-invmixcolumns/aes-invmixcolumns-xor93-depth10.circ.txt) | v7 |  | [logs](aes-invmixcolumns/logs/aes-invmixcolumns-xor93-depth10/) |
| 11 | [92](aes-invmixcolumns/aes-invmixcolumns-xor92-depth11.circ.txt) | v7 |  | [logs](aes-invmixcolumns/logs/aes-invmixcolumns-xor92-depth11/) |
| 12 | [90](aes-invmixcolumns/aes-invmixcolumns-xor90-depth12.circ.txt) | v6 | 93 | [logs](aes-invmixcolumns/logs/aes-invmixcolumns-xor90-depth12/) |
| 13 | — |  | 92 |  |
| 15 | [89](aes-invmixcolumns/aes-invmixcolumns-xor89-depth15.circ.txt) | v6 | 91 | [logs](aes-invmixcolumns/logs/aes-invmixcolumns-xor89-depth15/) |
| 17 | [88](aes-invmixcolumns/aes-invmixcolumns-xor88-depth17.circ.txt) | v6 |  | [logs](aes-invmixcolumns/logs/aes-invmixcolumns-xor88-depth17/) |
| 20 | — |  | [90](https://github.com/usnistgov/Circuits/blob/master/data/slp/aes/aes-invmixcols/aes-invmixcols-xor90-depth20.circ.txt) |  |

### AES S-box bottom linear layer

[aes-sbox-bottom](aes-sbox-bottom/): 18 inputs, 8 outputs, 60 XORs computed directly.

| Depth | Gates | Found by | NIST | Logs |
|---:|---:|---|---:|---|
| 4 | [29](aes-sbox-bottom/aes-sbox-bottom-xor29-depth4.circ.txt) | v6 | 38 | [logs](aes-sbox-bottom/logs/aes-sbox-bottom-xor29-depth4/) |
| 5 | [28](aes-sbox-bottom/aes-sbox-bottom-xor28-depth5.circ.txt) | v6 | 28 | [logs](aes-sbox-bottom/logs/aes-sbox-bottom-xor28-depth5/) |

## 16×16

### Ciphers

| Map | Direct XOR | NIST | Ours (gates@depth) | Found by |
|---|---:|---|---|---|
| [fides-midori-mantis](fides-midori-mantis/) | 32 | 24@3 | [24@2](fides-midori-mantis/fides-midori-mantis-xor24-depth2.circ.txt) | v8 |
| [joltik](joltik/) | 72 | 44@7 | [46@3](joltik/joltik-xor46-depth3.circ.txt)¹³, [44@4](joltik/joltik-xor44-depth4.circ.txt), [43@6](joltik/joltik-xor43-depth6.circ.txt), [42@9](joltik/joltik-xor42-depth9.circ.txt) | v6 |
| [pride-l0](pride-l0/) | 32 | 24@4 | [24@2](pride-l0/pride-l0-xor24-depth2.circ.txt)⁶ | v8 |
| [prince-m0](prince-m0/) | 32 | 24@4 | [24@2](prince-m0/prince-m0-xor24-depth2.circ.txt) | v8 |
| [qarma64](qarma64/) | 32 | 24@8 | — |  |
| [skinny](skinny/) | 16 | 12@2 | — |  |
| [small-scale-aes](small-scale-aes/) | 72 | 43@5 | [44@4](small-scale-aes/small-scale-aes-xor44-depth4.circ.txt), [42@5](small-scale-aes/small-scale-aes-xor42-depth5.circ.txt) | v8 |

### MDS 4×4 over GF(2⁴)

| Map | Direct XOR | NIST | Ours (gates@depth) | Found by |
|---|---:|---|---|---|
| [bkl16-4x4-gf16](bkl16-4x4-gf16/) | 64 | 41@5 | [40@4](bkl16-4x4-gf16/bkl16-4x4-gf16-xor40-depth4.circ.txt) | v8 |
| [jpst17-4x4-gf16](jpst17-4x4-gf16/) | 61 | 40@6 | [41@4](jpst17-4x4-gf16/jpst17-4x4-gf16-xor41-depth4.circ.txt), [40@5](jpst17-4x4-gf16/jpst17-4x4-gf16-xor40-depth5.circ.txt), [39@6](jpst17-4x4-gf16/jpst17-4x4-gf16-xor39-depth6.circ.txt) | v8 |
| [jpst17-4x4-gf16-inv](jpst17-4x4-gf16-inv/) | 68 | 41@6 | [43@4](jpst17-4x4-gf16-inv/jpst17-4x4-gf16-inv-xor43-depth4.circ.txt), [41@5](jpst17-4x4-gf16-inv/jpst17-4x4-gf16-inv-xor41-depth5.circ.txt), [40@6](jpst17-4x4-gf16-inv/jpst17-4x4-gf16-inv-xor40-depth6.circ.txt) | v8 |
| [klsw17-m-4x4-gf16](klsw17-m-4x4-gf16/) | 92 | 36@8 | [36@4](klsw17-m-4x4-gf16/klsw17-m-4x4-gf16-xor36-depth4.circ.txt), [32@6](klsw17-m-4x4-gf16/klsw17-m-4x4-gf16-xor32-depth6.circ.txt) | v8 |
| [ls16-4x4-gf16](ls16-4x4-gf16/) | 60 | 44@4 | [43@3](ls16-4x4-gf16/ls16-4x4-gf16-xor43-depth3.circ.txt) | v8 |
| [lw16-4x4-gf16](lw16-4x4-gf16/) | 60 | 44@4 | [43@3](lw16-4x4-gf16/lw16-4x4-gf16-xor43-depth3.circ.txt) | v8 |
| [lw16-4x4-gf16-inv](lw16-4x4-gf16-inv/) | 72 | 44@6 | [44@4](lw16-4x4-gf16-inv/lw16-4x4-gf16-inv-xor44-depth4.circ.txt), [43@7](lw16-4x4-gf16-inv/lw16-4x4-gf16-inv-xor43-depth7.circ.txt), [42@9](lw16-4x4-gf16-inv/lw16-4x4-gf16-inv-xor42-depth9.circ.txt) | v8 |
| [skop15-4x4-gf16](skop15-4x4-gf16/) | 68 | 44@7 | [45@4](skop15-4x4-gf16/skop15-4x4-gf16-xor45-depth4.circ.txt), [43@5](skop15-4x4-gf16/skop15-4x4-gf16-xor43-depth5.circ.txt) | v8 |
| [skop15-4x4-gf16-inv](skop15-4x4-gf16-inv/) | 72 | 44@8 | [44@4](skop15-4x4-gf16-inv/skop15-4x4-gf16-inv-xor44-depth4.circ.txt), [43@7](skop15-4x4-gf16-inv/skop15-4x4-gf16-inv-xor43-depth7.circ.txt), [42@9](skop15-4x4-gf16-inv/skop15-4x4-gf16-inv-xor42-depth9.circ.txt) | v8 |
| [ss16-4x4-gf16](ss16-4x4-gf16/) | 58 | 41@5 | [40@4](ss16-4x4-gf16/ss16-4x4-gf16-xor40-depth4.circ.txt) | v8 |
| [ss16-4x4-gf16-inv](ss16-4x4-gf16-inv/) | 64 | 38@6 | [38@4](ss16-4x4-gf16-inv/ss16-4x4-gf16-inv-xor38-depth4.circ.txt), [37@5](ss16-4x4-gf16-inv/ss16-4x4-gf16-inv-xor37-depth5.circ.txt) | v8 |

## 32×32

### Ciphers

| Map | Direct XOR | NIST | Ours (gates@depth) | Found by |
|---|---:|---|---|---|
| [anubis-clefia-m0](anubis-clefia-m0/) | 184 | 98@9 | [95@5](anubis-clefia-m0/anubis-clefia-m0-xor95-depth5.circ.txt), [94@6](anubis-clefia-m0/anubis-clefia-m0-xor94-depth6.circ.txt), [93@7](anubis-clefia-m0/anubis-clefia-m0-xor93-depth7.circ.txt), [92@8](anubis-clefia-m0/anubis-clefia-m0-xor92-depth8.circ.txt) | v8 |
| [clefia-m1](clefia-m1/) | 208 | 103@10 | [113@4](clefia-m1/clefia-m1-xor113-depth4.circ.txt), [105@5](clefia-m1/clefia-m1-xor105-depth5.circ.txt), [103@6](clefia-m1/clefia-m1-xor103-depth6.circ.txt), [102@7](clefia-m1/clefia-m1-xor102-depth7.circ.txt), [101@8](clefia-m1/clefia-m1-xor101-depth8.circ.txt), [100@9](clefia-m1/clefia-m1-xor100-depth9.circ.txt), [99@10](clefia-m1/clefia-m1-xor99-depth10.circ.txt) | v8 |
| [fox-mu4](fox-mu4/) | 219 | 130@13 | [141@4](fox-mu4/fox-mu4-xor141-depth4.circ.txt), [128@5](fox-mu4/fox-mu4-xor128-depth5.circ.txt), [122@6](fox-mu4/fox-mu4-xor122-depth6.circ.txt), [121@7](fox-mu4/fox-mu4-xor121-depth7.circ.txt), [120@8](fox-mu4/fox-mu4-xor120-depth8.circ.txt), [119@9](fox-mu4/fox-mu4-xor119-depth9.circ.txt) | v2, v6, v7 |
| [qarma128](qarma128/) | 64 | 48@6 | — |  |
| [twofish](twofish/) | 327 | 111@8 | [141@4](twofish/twofish-xor141-depth4.circ.txt), [119@5](twofish/twofish-xor119-depth5.circ.txt), [109@7](twofish/twofish-xor109-depth7.circ.txt), [108@8](twofish/twofish-xor108-depth8.circ.txt), [107@10](twofish/twofish-xor107-depth10.circ.txt), [106@11](twofish/twofish-xor106-depth11.circ.txt) | v8 |
| [whirlwind-m0](whirlwind-m0/) | 488 | 183@14 | [187@6](whirlwind-m0/whirlwind-m0-xor187-depth6.circ.txt), [170@14](whirlwind-m0/whirlwind-m0-xor170-depth14.circ.txt), [165@15](whirlwind-m0/whirlwind-m0-xor165-depth15.circ.txt), [164@16](whirlwind-m0/whirlwind-m0-xor164-depth16.circ.txt), [163@19](whirlwind-m0/whirlwind-m0-xor163-depth19.circ.txt) | v8 |
| [whirlwind-m1](whirlwind-m1/) | 536 | 187@16 | [200@6](whirlwind-m1/whirlwind-m1-xor200-depth6.circ.txt), [185@13](whirlwind-m1/whirlwind-m1-xor185-depth13.circ.txt), [175@14](whirlwind-m1/whirlwind-m1-xor175-depth14.circ.txt), [172@15](whirlwind-m1/whirlwind-m1-xor172-depth15.circ.txt), [171@18](whirlwind-m1/whirlwind-m1-xor171-depth18.circ.txt), [170@19](whirlwind-m1/whirlwind-m1-xor170-depth19.circ.txt) | v8 |

### MDS 4×4 over GF(2⁸)

| Map | Direct XOR | NIST | Ours (gates@depth) | Found by |
|---|---:|---|---|---|
| [bkl16-4x4-gf256](bkl16-4x4-gf256/) | 136 | 107@6 | [102@4](bkl16-4x4-gf256/bkl16-4x4-gf256-xor102-depth4.circ.txt), [101@5](bkl16-4x4-gf256/bkl16-4x4-gf256-xor101-depth5.circ.txt) | v8 |
| [jpst17-4x4-gf256](jpst17-4x4-gf256/) | 122 | 82@7 | [82@4](jpst17-4x4-gf256/jpst17-4x4-gf256-xor82-depth4.circ.txt), [78@6](jpst17-4x4-gf256/jpst17-4x4-gf256-xor78-depth6.circ.txt) | v8 |
| [jpst17-4x4-gf256-inv](jpst17-4x4-gf256-inv/) | 136 | 83@6 | [94@3](jpst17-4x4-gf256-inv/jpst17-4x4-gf256-inv-xor94-depth3.circ.txt)⁴, [84@4](jpst17-4x4-gf256-inv/jpst17-4x4-gf256-inv-xor84-depth4.circ.txt)⁴, [82@5](jpst17-4x4-gf256-inv/jpst17-4x4-gf256-inv-xor82-depth5.circ.txt), [80@6](jpst17-4x4-gf256-inv/jpst17-4x4-gf256-inv-xor80-depth6.circ.txt) | v8 |
| [klsw17-m-4x4-gf256](klsw17-m-4x4-gf256/) | 184 | 72@7 | [72@4](klsw17-m-4x4-gf256/klsw17-m-4x4-gf256-xor72-depth4.circ.txt), [64@6](klsw17-m-4x4-gf256/klsw17-m-4x4-gf256-xor64-depth6.circ.txt) | v8 |
| [klsw17-m-4x4-gf256-inv](klsw17-m-4x4-gf256-inv/) | 128 | 78@5 | [76@4](klsw17-m-4x4-gf256-inv/klsw17-m-4x4-gf256-inv-xor76-depth4.circ.txt), [75@5](klsw17-m-4x4-gf256-inv/klsw17-m-4x4-gf256-inv-xor75-depth5.circ.txt), [74@6](klsw17-m-4x4-gf256-inv/klsw17-m-4x4-gf256-inv-xor74-depth6.circ.txt) | v8 |
| [ls16-4x4-gf256](ls16-4x4-gf256/) | 128 | 109@5 | [103@4](ls16-4x4-gf256/ls16-4x4-gf256-xor103-depth4.circ.txt) | v8 |
| [lw16-4x4-gf256](lw16-4x4-gf256/) | 106 | 100@6 | [102@3](lw16-4x4-gf256/lw16-4x4-gf256-xor102-depth3.circ.txt), [96@4](lw16-4x4-gf256/lw16-4x4-gf256-xor96-depth4.circ.txt) | v8 |
| [lw16-4x4-gf256-inv-circ](lw16-4x4-gf256-inv-circ/) | 132 | 89@7 | [86@4](lw16-4x4-gf256-inv-circ/lw16-4x4-gf256-inv-circ-xor86-depth4.circ.txt), [82@5](lw16-4x4-gf256-inv-circ/lw16-4x4-gf256-inv-circ-xor82-depth5.circ.txt), [81@10](lw16-4x4-gf256-inv-circ/lw16-4x4-gf256-inv-circ-xor81-depth10.circ.txt) | v8 |
| [lw16-4x4-gf256-inv-had](lw16-4x4-gf256-inv-had/) | 136 | 87@5 | [85@4](lw16-4x4-gf256-inv-had/lw16-4x4-gf256-inv-had-xor85-depth4.circ.txt), [84@5](lw16-4x4-gf256-inv-had/lw16-4x4-gf256-inv-had-xor84-depth5.circ.txt) | v8 |
| [skop15-4x4-gf256](skop15-4x4-gf256/) | 136 | 90@6 | [89@4](skop15-4x4-gf256/skop15-4x4-gf256-xor89-depth4.circ.txt), [88@6](skop15-4x4-gf256/skop15-4x4-gf256-xor88-depth6.circ.txt), [87@7](skop15-4x4-gf256/skop15-4x4-gf256-xor87-depth7.circ.txt) | v8 |
| [skop15-4x4-gf256-inv](skop15-4x4-gf256-inv/) | 144 | 91@6 | [90@4](skop15-4x4-gf256-inv/skop15-4x4-gf256-inv-xor90-depth4.circ.txt), [88@6](skop15-4x4-gf256-inv/skop15-4x4-gf256-inv-xor88-depth6.circ.txt), [86@7](skop15-4x4-gf256-inv/skop15-4x4-gf256-inv-xor86-depth7.circ.txt), [85@9](skop15-4x4-gf256-inv/skop15-4x4-gf256-inv-xor85-depth9.circ.txt) | v8 |
| [ss16-4x4-gf256](ss16-4x4-gf256/) | 123 | 104@6 | [98@4](ss16-4x4-gf256/ss16-4x4-gf256-xor98-depth4.circ.txt), [97@6](ss16-4x4-gf256/ss16-4x4-gf256-xor97-depth6.circ.txt) | v8 |
| [ss16-4x4-gf256-inv](ss16-4x4-gf256-inv/) | 160 | 93@8 | [92@5](ss16-4x4-gf256-inv/ss16-4x4-gf256-inv-xor92-depth5.circ.txt), [91@8](ss16-4x4-gf256-inv/ss16-4x4-gf256-inv-xor91-depth8.circ.txt), [90@9](ss16-4x4-gf256-inv/ss16-4x4-gf256-inv-xor90-depth9.circ.txt), [88@10](ss16-4x4-gf256-inv/ss16-4x4-gf256-inv-xor88-depth10.circ.txt) | v8 |

### MDS 8×8 over GF(2⁴)

| Map | Direct XOR | NIST | Ours (gates@depth) | Found by |
|---|---:|---|---|---|
| [klsw17-m-8x8-gf16-0x13](klsw17-m-8x8-gf16-0x13/) | 456 | 175@12 | [178@6](klsw17-m-8x8-gf16-0x13/klsw17-m-8x8-gf16-0x13-xor178-depth6.circ.txt), [171@9](klsw17-m-8x8-gf16-0x13/klsw17-m-8x8-gf16-0x13-xor171-depth9.circ.txt), [161@10](klsw17-m-8x8-gf16-0x13/klsw17-m-8x8-gf16-0x13-xor161-depth10.circ.txt) | v8 |
| [klsw17-m-8x8-gf16-0x13-inv](klsw17-m-8x8-gf16-0x13-inv/) | 540 | 176@12 | [191@6](klsw17-m-8x8-gf16-0x13-inv/klsw17-m-8x8-gf16-0x13-inv-xor191-depth6.circ.txt), [176@11](klsw17-m-8x8-gf16-0x13-inv/klsw17-m-8x8-gf16-0x13-inv-xor176-depth11.circ.txt), [163@12](klsw17-m-8x8-gf16-0x13-inv/klsw17-m-8x8-gf16-0x13-inv-xor163-depth12.circ.txt), [162@13](klsw17-m-8x8-gf16-0x13-inv/klsw17-m-8x8-gf16-0x13-inv-xor162-depth13.circ.txt) | v8 |
| [skop15-8x8-gf16](skop15-8x8-gf16/) | 432 | 170@19 | [361@4](skop15-8x8-gf16/skop15-8x8-gf16-xor361-depth4.circ.txt)³, [203@5](skop15-8x8-gf16/skop15-8x8-gf16-xor203-depth5.circ.txt), [149@12](skop15-8x8-gf16/skop15-8x8-gf16-xor149-depth12.circ.txt), [147@13](skop15-8x8-gf16/skop15-8x8-gf16-xor147-depth13.circ.txt), [146@14](skop15-8x8-gf16/skop15-8x8-gf16-xor146-depth14.circ.txt) | v8 |
| [skop15-8x8-gf16-inv](skop15-8x8-gf16-inv/) | 512 | 180@12 | [192@6](skop15-8x8-gf16-inv/skop15-8x8-gf16-inv-xor192-depth6.circ.txt), [163@10](skop15-8x8-gf16-inv/skop15-8x8-gf16-inv-xor163-depth10.circ.txt) | v8 |
| [ss17-8x8-gf16](ss17-8x8-gf16/) | 394 | 178@10 | [335@4](ss17-8x8-gf16/ss17-8x8-gf16-xor335-depth4.circ.txt), [194@5](ss17-8x8-gf16/ss17-8x8-gf16-xor194-depth5.circ.txt), [175@8](ss17-8x8-gf16/ss17-8x8-gf16-xor175-depth8.circ.txt), [174@9](ss17-8x8-gf16/ss17-8x8-gf16-xor174-depth9.circ.txt), [167@10](ss17-8x8-gf16/ss17-8x8-gf16-xor167-depth10.circ.txt), [166@11](ss17-8x8-gf16/ss17-8x8-gf16-xor166-depth11.circ.txt), [165@13](ss17-8x8-gf16/ss17-8x8-gf16-xor165-depth13.circ.txt) | v8 |

## 64×64

### Ciphers

| Map | Direct XOR | NIST | Ours (gates@depth) | Found by |
|---|---:|---|---|---|
| [fox-mu8](fox-mu8/) | 1257 | 540@14 | [1078@5](fox-mu8/fox-mu8-xor1078-depth5.circ.txt)², [605@6](fox-mu8/fox-mu8-xor605-depth6.circ.txt), [599@7](fox-mu8/fox-mu8-xor599-depth7.circ.txt)², [539@8](fox-mu8/fox-mu8-xor539-depth8.circ.txt)², [512@9](fox-mu8/fox-mu8-xor512-depth9.circ.txt), [506@10](fox-mu8/fox-mu8-xor506-depth10.circ.txt), [505@11](fox-mu8/fox-mu8-xor505-depth11.circ.txt) | v3, v6, v7 |
| [grostl](grostl/) | 1112 | 410@12 | [502@5](grostl/grostl-xor502-depth5.circ.txt), [455@8](grostl/grostl-xor455-depth8.circ.txt), [405@10](grostl/grostl-xor405-depth10.circ.txt), [368@11](grostl/grostl-xor368-depth11.circ.txt), [366@12](grostl/grostl-xor366-depth12.circ.txt), [362@13](grostl/grostl-xor362-depth13.circ.txt), [360@14](grostl/grostl-xor360-depth14.circ.txt), [358@15](grostl/grostl-xor358-depth15.circ.txt), [350@16](grostl/grostl-xor350-depth16.circ.txt) | v8 |
| [khazad](khazad/) | 1232 | 366@18 | [1055@5](khazad/khazad-xor1055-depth5.circ.txt)³, [478@6](khazad/khazad-xor478-depth6.circ.txt), [477@8](khazad/khazad-xor477-depth8.circ.txt), [460@9](khazad/khazad-xor460-depth9.circ.txt), [433@10](khazad/khazad-xor433-depth10.circ.txt), [432@11](khazad/khazad-xor432-depth11.circ.txt), [345@15](khazad/khazad-xor345-depth15.circ.txt) | v8 |
| [whirlpool-maelstrom](whirlpool-maelstrom/) | 840 | 425@11 | [759@5](whirlpool-maelstrom/whirlpool-maelstrom-xor759-depth5.circ.txt)³, [416@6](whirlpool-maelstrom/whirlpool-maelstrom-xor416-depth6.circ.txt), [395@8](whirlpool-maelstrom/whirlpool-maelstrom-xor395-depth8.circ.txt), [394@9](whirlpool-maelstrom/whirlpool-maelstrom-xor394-depth9.circ.txt) | v8 |

### MDS 8×8 over GF(2⁸)

| Map | Direct XOR | NIST | Ours (gates@depth) | Found by |
|---|---:|---|---|---|
| [bkl16-8x8-gf256](bkl16-8x8-gf256/) | 784 | 465@10 | [725@4](bkl16-8x8-gf256/bkl16-8x8-gf256-xor725-depth4.circ.txt)³, [494@5](bkl16-8x8-gf256/bkl16-8x8-gf256-xor494-depth5.circ.txt), [456@8](bkl16-8x8-gf256/bkl16-8x8-gf256-xor456-depth8.circ.txt), [443@9](bkl16-8x8-gf256/bkl16-8x8-gf256-xor443-depth9.circ.txt), [442@10](bkl16-8x8-gf256/bkl16-8x8-gf256-xor442-depth10.circ.txt) | v8 |
| [jpst17-8x8-gf256-inv](jpst17-8x8-gf256-inv/) | 1152 | 528@11 | [1027@5](jpst17-8x8-gf256-inv/jpst17-8x8-gf256-inv-xor1027-depth5.circ.txt)³, [641@6](jpst17-8x8-gf256-inv/jpst17-8x8-gf256-inv-xor641-depth6.circ.txt), [496@10](jpst17-8x8-gf256-inv/jpst17-8x8-gf256-inv-xor496-depth10.circ.txt), [493@11](jpst17-8x8-gf256-inv/jpst17-8x8-gf256-inv-xor493-depth11.circ.txt), [492@12](jpst17-8x8-gf256-inv/jpst17-8x8-gf256-inv-xor492-depth12.circ.txt) | v8 |
| [klsw17-m-8x8-gf256](klsw17-m-8x8-gf256/) | 912 | 364@11 | [347@6](klsw17-m-8x8-gf256/klsw17-m-8x8-gf256-xor347-depth6.circ.txt), [336@12](klsw17-m-8x8-gf256/klsw17-m-8x8-gf256-xor336-depth12.circ.txt), [329@13](klsw17-m-8x8-gf256/klsw17-m-8x8-gf256-xor329-depth13.circ.txt), [327@14](klsw17-m-8x8-gf256/klsw17-m-8x8-gf256-xor327-depth14.circ.txt), [326@15](klsw17-m-8x8-gf256/klsw17-m-8x8-gf256-xor326-depth15.circ.txt) | v8 |
| [klsw17-m-8x8-gf256-inv](klsw17-m-8x8-gf256-inv/) | 1080 | 368@12 | [490@6](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor490-depth6.circ.txt), [361@11](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor361-depth11.circ.txt), [346@12](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor346-depth12.circ.txt), [345@13](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor345-depth13.circ.txt), [331@14](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor331-depth14.circ.txt), [329@15](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor329-depth15.circ.txt), [325@16](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor325-depth16.circ.txt), [324@21](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor324-depth21.circ.txt) | v8 |
| [ls16-8x8-gf256](ls16-8x8-gf256/) | 688 | 427@9 | [411@5](ls16-8x8-gf256/ls16-8x8-gf256-xor411-depth5.circ.txt), [404@8](ls16-8x8-gf256/ls16-8x8-gf256-xor404-depth8.circ.txt) | v8 |
| [skop15-8x8-gf256](skop15-8x8-gf256/) | 768 | 445@8 | [712@5](skop15-8x8-gf256/skop15-8x8-gf256-xor712-depth5.circ.txt), [447@6](skop15-8x8-gf256/skop15-8x8-gf256-xor447-depth6.circ.txt), [418@8](skop15-8x8-gf256/skop15-8x8-gf256-xor418-depth8.circ.txt) | v8 |
| [skop15-8x8-gf256-inv](skop15-8x8-gf256-inv/) | 816 | 348@13 | [726@5](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor726-depth5.circ.txt), [408@6](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor408-depth6.circ.txt), [333@12](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor333-depth12.circ.txt), [331@13](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor331-depth13.circ.txt), [318@14](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor318-depth14.circ.txt) | v8 |
| [ss17-8x8-gf256](ss17-8x8-gf256/) | 680 | 418@9 | [418@5](ss17-8x8-gf256/ss17-8x8-gf256-xor418-depth5.circ.txt), [392@8](ss17-8x8-gf256/ss17-8x8-gf256-xor392-depth8.circ.txt) | v8 |

## 128×128

### Ciphers

| Map | Direct XOR | NIST | Ours (gates@depth) | Found by |
|---|---:|---|---|---|
| [aria](aria/) | 768 | 387@7 | [416@3](aria/aria-xor416-depth3.circ.txt)³, [384@4](aria/aria-xor384-depth4.circ.txt), [383@8](aria/aria-xor383-depth8.circ.txt), [382@10](aria/aria-xor382-depth10.circ.txt) | v8 |

## Notes

**Direct XOR**: the gates of computing each output on its own (row weight minus one,
summed), as in NIST's list. **NIST**: the map's circuits in NIST's
[repository](https://github.com/usnistgov/Circuits) as gates@depth (for AES MixColumns and
InvMixColumns, its [list of circuits](https://csrc.nist.gov/projects/circuit-complexity/list-of-circuits)).
A circuit at a lower depth also counts at every higher depth, so a depth with no circuit of
ours is covered by our circuits above it in the table.

¹ Recovered from a worker checkpoint: the run held this circuit but never wrote it as a
record, so there is no dossier for it.

² "+ polish": shrunk at its own depth by v8's polish (`search/xorflux/engine/polish.py`);
its logs keep the original circuit (`original-circuit.txt`) and `polish.json`.

³ Built by a constructor that starts a search chain, with no search move after it:
`naive` builds balanced XOR trees; `anneal3` is the depth-3 partition annealer
(`search/xorflux/moves/depth3.py`), a constructor made for depth 3 rather than part of the
general search. ⁴ Found by the search from an `anneal3` start.

⁵ Found on 2026-10-31 by a cap-6 worker that started from NIST's 107@6 (an earlier revision of
its 106@6); the chain restarted from another worker's 105@6, itself found from NIST's 106@6.
No earlier run had started from NIST's depth-5, -6 or -7 InvMixColumns circuits.

⁶ The fides-midori-mantis 24@2 circuit: the two maps have the same matrix.

How long each search ran, and on what hardware: [SEARCH-TIME.md](SEARCH-TIME.md).

The maps added from NIST's repository on 2026-10-30 were searched from NIST's circuits, and
only points that no NIST circuit matches with as few gates at no more depth are kept for
them. A map with "—" has no such point yet.

Two pairs of maps have the same matrix: pride-l0 and fides-midori-mantis, and
skop15-4x4-gf16-inv and joltik. Each folder lists what was searched under its own name, except
pride-l0, whose 24@2 is the circuit found for fides-midori-mantis (⁶).
