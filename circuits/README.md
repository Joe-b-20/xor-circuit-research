# circuits

XOR circuits for linear maps, found by XORFlux, and AND/XOR circuits for the AES S-box and its
inverse, found by BoolFlux ([search/](../search/README.md)). For each linear map: the smallest
circuit our search found at each depth. For the S-box and its inverse: every circuit of ours that
no NIST circuit matches or beats.
We don't claim that any of them is optimal or the best known: they are what the search reached
in the time it ran. Published or unpublished work may have smaller or shallower circuits for some
of these functions, NIST's own list among them (see the NIST column), and more search time would
likely improve many of them. The only lower bounds here are for AES MixColumns ([lower-bound-proofs/](../lower-bound-proofs/README.md)).

One folder per map or function:

```
<map>/
  <map>.mat.txt                    the map: NIST matrix format
  <map>-xor<G>-depth<D>.circ.txt   a circuit with G gates and depth D: NIST circuit file format
  logs/<map>-xor<G>-depth<D>/      how it was found
aes-sbox/
  aes-sbox-a<A>-ad<AD>-g<G>-gd<GD>-xx<X>-<Y>.circ.txt
                                   a Boolean circuit: NIST's circuit file format and file name
  logs/aes-sbox-a<A>-...-<Y>/      how it was found
aes-invsbox/                       the same for the inverse S-box
  logs/_runtime/                   the run-time inverse layer its search used
```

## Check

```bash
python3 circuits/check.py                   # every circuit, linear and Boolean
python3 circuits/check.py circuits/joltik   # one map, or one file
python3 circuits/check.py circuits/aes-sbox # the S-box circuits
python3 circuits/check.py circuits/aes-invsbox # the inverse S-box circuits
```

`check.py` uses the standard library only and none of the search code; its library for Boolean
circuits is [boolcirc/](boolcirc/). For a linear map it
checks that each output equals its matrix row and that the gate count and depth match the file
name. For a Boolean circuit it computes the complete truth table twice, from the gate list and
from its AND skeleton, compares it with the S-box or its inverse computed from FIPS 197's definition, and checks
A, AD, G, GD, X and Y against the file name and the tallies in the header. By default it also
checks NIST's own S-box circuits in [search/nonlinear/seeds/](../search/nonlinear/seeds/).

## Conventions

- Linear maps: gates are 2-input XOR (XNOR only where a map has output constants). Inputs have depth 0.
- In `<map>.mat.txt`, the line `1`, then `rows cols`, then one 0/1 row per output: row `i` is
  `y_i`, column `j` is `x_j`, counting from 0. An optional last line of `rows` 0/1 values gives
  output constants (`y_i = row_i·x ⊕ c_i`).
- Boolean circuits: gates AND, XOR, XNOR and NOT, counted as NIST counts them (below). Inputs are
  `U0:U7` and outputs `S0:S7`, as in NIST's files: `U0` is the most significant bit of the input byte
  and `S0` of the output byte (the inverse S-box: `x0:x7` and `y0:y7`, as in NIST's inverse files).
- Each circuit's header names the search that found it (the XORFlux version, or the BoolFlux
  method), how its run started and where its logs are. XORFlux versions are listed in
  [search/linear/HISTORY.md](../search/linear/HISTORY.md#versions); the time each
  XORFlux search ran and the hardware are in [SEARCH-TIME.md](SEARCH-TIME.md).
- Paths in logs recorded before the restructure of 2026-11-16 are the old ones: `search/xorflux/`,
  `search/campaigns/`, `search/seeds/` and `search/versions/` are now under `search/linear/`;
  `nonlinear/boolflux/` is `search/nonlinear/boolflux/` (its `campaigns/targets/ops/` is `ops/`, and
  `campaigns/aes_check.py` is `aes_check.py`), `nonlinear/nist/` is `search/nonlinear/seeds/` and
  `nonlinear/boolcirc/` is `circuits/boolcirc/`. A BoolFlux path a log names that is no longer in the
  tree (`nonlinear/boolflux/strategies/`, `nonlinear/boolflux/results/`) is in commit `e657298`.

## Logs

Linear maps:

| File | Content |
|---|---|
| `found.json` | version, code, run, worker, time, start circuit, chain root, list of log files |
| `record.json` | the circuit as the search wrote it |
| `dossier.json` | the improvement that produced it: move trace, state before and after, replay data |
| `events.jsonl.gz`, `worker.log`, `discoveries.jsonl.gz` | the worker's log |
| `plan.json.gz`, `campaign.toml`, `config.json` | the run's frozen settings |
| `seed.json` | the circuit the worker started from |
| `checkpoint.json.gz` | the worker checkpoint, for the circuit that exists only there (¹) |

Older versions wrote fewer files; each `found.json` lists what is there.

Boolean circuits:

| File | Content |
|---|---|
| `found.json` | method and operator, start circuit, chain root, parameters, seed, time, command, code (commit of the run, the public commit that has its exact code, file paths), reproducibility, where the circuit was first recorded; a field recovered later names its source |
| `verification.json` | both truth-table checks, the metrics, and the comparison with every NIST circuit of the pin |
| `start.circ.txt` | the circuit the run started from, when it is ours (`front.circ.txt` and `back.circ.txt` for a join), in NIST's format |
| `run-start.circ.txt`, `input.bfx`, `input.json` | the start file exactly as the run read it, for a replay |
| `run.json`, `job-record.json`, `circuit.json` | hub runs: the scheduler's run record (command, settings, outcome), the operator's record, the circuit's archive record |
| `kernel.cfg`, `kernel.log.gz` | the gate kernel's settings and trace |
| `events.jsonl.gz`, `control.json` | hub runs: the hub's event log and its control file as at the end of the run |
| `result.json`, `<op>.log.gz`, `<op>.jsonl.gz`, `plan.json.gz`, `runner.log`, `job.out` | operator runs (conjugation, re-basing, shared bottom, SAT LNS): the job's result and log, the campaign plan, the runner's lines for the job |
| `summary.json`, `r0-s<S>.cfg`, `r0-s<S>.log.gz` | `cli.py run`: the run summary, each seed's kernel settings and log |
| `run-sidecar.json`, `log.jsonl.gz`, `frontier.json`, `jobs.jsonl.gz`, `loop.jsonl.gz`, … | other drivers: the record written next to the circuit, the driver's log |
| `hub-lineage.json.gz`, `hub-events.jsonl.gz`, `conjpull.log.gz`, `conj-job.json.gz` | inverse S-box runs ([below](#aes-inverse-s-box)) |

`found.json` lists the files of each circuit. Paths in them are rewritten: `<checkout>` is the
repository at the commit of the run, `<campaign archive>` the campaign archive (not published)
and `<home>` the home folder of the machine that ran it.
Every circuit is verified independently ([Check](#check)); [REPRODUCE.md](REPRODUCE.md) has tested
replay instructions for six of them. For the others, `found.json` says what was recorded and what
was not: most BoolFlux runs were time-budgeted and are not bit-reproducible.

## Circuits

208 circuits for 59 maps, grouped as in NIST's [list of circuits](https://csrc.nist.gov/projects/circuit-complexity/list-of-circuits): [AES](#aes) · [16×16](#1616) · [32×32](#3232) · [64×64](#6464) · [128×128](#128128); and 74 circuits for the [AES S-box](#aes-s-box) and 45 for the [AES inverse S-box](#aes-inverse-s-box), at the top of the AES section. Sizes are inputs × outputs; notes are [below the tables](#notes).

## AES

### AES S-box

[aes-sbox](aes-sbox/): 8 inputs, 8 outputs; circuits of AND, XOR, XNOR and NOT gates in NIST's
file format and naming (`aes-sbox-aA-adAD-gG-gdGD-xxX-Y`). As NIST counts them: A is the number
of AND gates, AD the AND depth (most ANDs on any input-to-output path), G the number of gates
(every gate, a NOT included) and GD the gate depth (inputs at depth 0; a NOT counts a level);
X = #XOR + #XNOR, Y = #XNOR.

Which circuits are here: every circuit of ours for which no NIST circuit of the same function has
A, AD, G and GD all at most ours, one per (A, AD, G, GD), and none that another of ours matches
or beats. We compared with all 104 forward S-box circuits of NIST's repository at commit
`3d807741` (its folders `aes-sbox/`, `sbox/` and `old-2020/`, mirrored in
[search/nonlinear/seeds/](../search/nonlinear/seeds/)). Every AES S-box circuit on NIST's
[list of circuits](https://csrc.nist.gov/projects/circuit-complexity/list-of-circuits) (page
updated 2026-11-05, checked 2026-11-16) is in the repository at that commit. **NIST**: NIST's fewest gates among its
circuits with A, AD and GD at most ours, linked to that file; — where it has none.
Rows are sorted as NIST sorts its tables: by A, then AD, then G, then GD, in
groups close to NIST's.

The inverse S-box (`aes-invsbox/`) has [its own section](#aes-inverse-s-box), below. We have no
circuits for the S-box with a direction bit that selects the S-box or its inverse
(`aes-sbox-sel/`). NIST lists no small (4- and 5-bit) S-boxes;
BoolFlux's runs on them found nothing better than the published circuits
([search/nonlinear/](../search/nonlinear/README.md)) and are not listed here.

#### #AND = 28

| A | AD | G | GD | Found by | NIST | Logs |
|---:|---:|---:|---:|---|---:|---|
| 28 | 4 | [130](aes-sbox/aes-sbox-a28-ad4-g130-gd24-xx102-45.circ.txt) | 24 | [gate kernel @ 924b4c0](https://github.com/Joe-b-20/xor-circuit-research/blob/924b4c0f7f1fc1bd2e6ca4adbe9974d42468d60f/nonlinear/boolflux/strategies/T1/t1run.py) | [132](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g132-gd22-xx104-40.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a28-ad4-g130-gd24-xx102-45/) |
| 28 | 4 | [131](aes-sbox/aes-sbox-a28-ad4-g131-gd22-xx103-52.circ.txt) | 22 | [gate kernel @ d961083](https://github.com/Joe-b-20/xor-circuit-research/tree/d961083c97330ea269d4f86fb0d55618cec72c32/nonlinear/boolflux) | [132](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g132-gd22-xx104-40.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a28-ad4-g131-gd22-xx103-52/) |
| 28 | 4 | [132](aes-sbox/aes-sbox-a28-ad4-g132-gd20-xx104-56.circ.txt) | 20 | [gate kernel @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/strategies/T1/t1run.py) | [134](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g134-gd20-xx106-41.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a28-ad4-g132-gd20-xx104-56/) |
| 28 | 4 | [133](aes-sbox/aes-sbox-a28-ad4-g133-gd19-xx105-55.circ.txt) | 19 | [gate kernel @ f9fe6f7](https://github.com/Joe-b-20/xor-circuit-research/tree/f9fe6f7db5b57ec8d3802ac18fbca2905486bde0/nonlinear/boolflux) | [141](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a28-ad4-g133-gd19-xx105-55/) |
| 28 | 4 | [135](aes-sbox/aes-sbox-a28-ad4-g135-gd18-xx107-55.circ.txt) | 18 | [gate kernel @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/strategies/E/low.sh) | [141](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a28-ad4-g135-gd18-xx107-55/) |
| 28 | 4 | [138](aes-sbox/aes-sbox-a28-ad4-g138-gd17-xx110-61.circ.txt) | 17 | [gate kernel @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/strategies/E/low.sh) | [141](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a28-ad4-g138-gd17-xx110-61/) |
| 28 | 4 | [174](aes-sbox/aes-sbox-a28-ad4-g174-gd14-xx146-80.circ.txt) | 14 | [conjugation @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/conjpull.py) | [176](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g176-gd14-xx148-25.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a28-ad4-g174-gd14-xx146-80/) |
| 28 | 5 | [125](aes-sbox/aes-sbox-a28-ad5-g125-gd24-xx97-50.circ.txt) | 24 | [conjugation @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/conjpull.py) | [128](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a28-ad5-g125-gd24-xx97-50/) |
| 28 | 5 | [126](aes-sbox/aes-sbox-a28-ad5-g126-gd23-xx98-58.circ.txt) | 23 | [conjugation @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/conjpull.py) | [128](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a28-ad5-g126-gd23-xx98-58/) |
| 28 | 5 | [127](aes-sbox/aes-sbox-a28-ad5-g127-gd22-xx99-48.circ.txt) | 22 | [skeleton kick (hub) @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/hub/ops/gen_skel.py) | [128](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a28-ad5-g127-gd22-xx99-48/) |
| 28 | 5 | [129](aes-sbox/aes-sbox-a28-ad5-g129-gd19-xx101-56.circ.txt) | 19 | [SAT LNS @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/strategies/P1/unionsat2.py) | [141](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a28-ad5-g129-gd19-xx101-56/) |
| 28 | 5 | [133](aes-sbox/aes-sbox-a28-ad5-g133-gd18-xx105-51.circ.txt) | 18 | [depth pull (hub) @ 97abda7](https://github.com/Joe-b-20/xor-circuit-research/blob/97abda77475b990ee0df77957807dfd718cb3c17/nonlinear/boolflux/hub/op_pull.py) | [141](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a28-ad5-g133-gd18-xx105-51/) |
| 28 | 5 | [136](aes-sbox/aes-sbox-a28-ad5-g136-gd17-xx108-60.circ.txt) | 17 | [depth pull @ f9fe6f7](https://github.com/Joe-b-20/xor-circuit-research/tree/f9fe6f7db5b57ec8d3802ac18fbca2905486bde0/nonlinear/boolflux) | [141](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a28-ad5-g136-gd17-xx108-60/) |

#### 29 ≤ #AND ≤ 31

| A | AD | G | GD | Found by | NIST | Logs |
|---:|---:|---:|---:|---|---:|---|
| 29 | 4 | [128](aes-sbox/aes-sbox-a29-ad4-g128-gd23-xx99-51.circ.txt) | 23 | [gate kernel @ f9fe6f7](https://github.com/Joe-b-20/xor-circuit-research/tree/f9fe6f7db5b57ec8d3802ac18fbca2905486bde0/nonlinear/boolflux) | [132](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g132-gd22-xx104-40.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a29-ad4-g128-gd23-xx99-51/) |
| 29 | 4 | [129](aes-sbox/aes-sbox-a29-ad4-g129-gd19-xx100-56.circ.txt) | 19 | [depth pull (hub) @ 8922cac](https://github.com/Joe-b-20/xor-circuit-research/blob/8922cacae4d4314968c5ce9baa740dea7aa38935/nonlinear/boolflux/hub/op_pull.py) | [141](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a29-ad4-g129-gd19-xx100-56/) |
| 29 | 4 | [131](aes-sbox/aes-sbox-a29-ad4-g131-gd17-xx102-64.circ.txt) | 17 | [depth pull (hub) @ 8922cac](https://github.com/Joe-b-20/xor-circuit-research/blob/8922cacae4d4314968c5ce9baa740dea7aa38935/nonlinear/boolflux/hub/op_pull.py) | [141](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a29-ad4-g131-gd17-xx102-64/) |
| 29 | 4 | [135](aes-sbox/aes-sbox-a29-ad4-g135-gd16-xx106-51.circ.txt) | 16 | [gate kernel (hub) @ 8922cac](https://github.com/Joe-b-20/xor-circuit-research/blob/8922cacae4d4314968c5ce9baa740dea7aa38935/nonlinear/boolflux/hub/op_polish.py) | [141](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a29-ad4-g135-gd16-xx106-51/) |
| 29 | 4 | [141](aes-sbox/aes-sbox-a29-ad4-g141-gd15-xx112-58.circ.txt) | 15 | [gate kernel (hub) @ 924b4c0](https://github.com/Joe-b-20/xor-circuit-research/blob/924b4c0f7f1fc1bd2e6ca4adbe9974d42468d60f/nonlinear/boolflux/hub/op_polish.py) | [153](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a29-ad4-g141-gd15-xx112-58/) |
| 29 | 5 | [130](aes-sbox/aes-sbox-a29-ad5-g130-gd18-xx101-53.circ.txt) | 18 | [gate kernel (hub) @ 924b4c0](https://github.com/Joe-b-20/xor-circuit-research/blob/924b4c0f7f1fc1bd2e6ca4adbe9974d42468d60f/nonlinear/boolflux/hub/op_polish.py) | [141](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a29-ad5-g130-gd18-xx101-53/) |
| 30 | 4 | [138](aes-sbox/aes-sbox-a30-ad4-g138-gd15-xx108-64.circ.txt) | 15 | [depth pull (hub) @ 924b4c0](https://github.com/Joe-b-20/xor-circuit-research/blob/924b4c0f7f1fc1bd2e6ca4adbe9974d42468d60f/nonlinear/boolflux/hub/op_pull.py) | [153](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a30-ad4-g138-gd15-xx108-64/) |
| 31 | 5 | [114](aes-sbox/aes-sbox-a31-ad5-g114-gd28-xx83-18.circ.txt) | 28 | [join (hub) @ 97abda7](https://github.com/Joe-b-20/xor-circuit-research/blob/97abda77475b990ee0df77957807dfd718cb3c17/nonlinear/boolflux/hub/op_join.py) | [124](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a31-ad5-g114-gd28-xx83-18/) |
| 31 | 5 | [115](aes-sbox/aes-sbox-a31-ad5-g115-gd24-xx84-29.circ.txt) | 24 | [gate kernel (hub) @ 97abda7](https://github.com/Joe-b-20/xor-circuit-research/blob/97abda77475b990ee0df77957807dfd718cb3c17/nonlinear/boolflux/hub/op_polish.py) | [128](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a31-ad5-g115-gd24-xx84-29/) |
| 31 | 5 | [116](aes-sbox/aes-sbox-a31-ad5-g116-gd22-xx85-6.circ.txt) | 22 | [join @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/strategies/E/long.sh) | [128](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a31-ad5-g116-gd22-xx85-6/) |
| 31 | 5 | [117](aes-sbox/aes-sbox-a31-ad5-g117-gd20-xx86-24.circ.txt) | 20 | [join @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/strategies/E/erun.py) | [128](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a31-ad5-g117-gd20-xx86-24/) |
| 31 | 5 | [118](aes-sbox/aes-sbox-a31-ad5-g118-gd19-xx87-39.circ.txt) | 19 | [join @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/strategies/E/low.sh) | [141](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a31-ad5-g118-gd19-xx87-39/) |
| 31 | 5 | [121](aes-sbox/aes-sbox-a31-ad5-g121-gd18-xx90-33.circ.txt) | 18 | [gate kernel (hub) @ 97abda7](https://github.com/Joe-b-20/xor-circuit-research/blob/97abda77475b990ee0df77957807dfd718cb3c17/nonlinear/boolflux/hub/op_polish.py) | [141](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a31-ad5-g121-gd18-xx90-33/) |
| 31 | 5 | [124](aes-sbox/aes-sbox-a31-ad5-g124-gd17-xx93-35.circ.txt) | 17 | [gate kernel @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/strategies/E/low.sh) | [141](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a31-ad5-g124-gd17-xx93-35/) |

#### 32 ≤ #AND ≤ 37, AND depth ≥ 4

| A | AD | G | GD | Found by | NIST | Logs |
|---:|---:|---:|---:|---|---:|---|
| 32 | 4 | [111](aes-sbox/aes-sbox-a32-ad4-g111-gd25-xx79-30.circ.txt) | 25 | [conjugation @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/conjpull.py) | [117](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a32-ad4-g111-gd25-xx79-30/) |
| 32 | 4 | [112](aes-sbox/aes-sbox-a32-ad4-g112-gd21-xx80-33.circ.txt) | 21 | [SAT LNS @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/satlns.py) | [117](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a32-ad4-g112-gd21-xx80-33/) |
| 32 | 4 | [113](aes-sbox/aes-sbox-a32-ad4-g113-gd20-xx81-36.circ.txt) | 20 | [conjugation @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/conjpull.py) | [117](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a32-ad4-g113-gd20-xx81-36/) |
| 32 | 4 | [114](aes-sbox/aes-sbox-a32-ad4-g114-gd19-xx82-45.circ.txt) | 19 | [conjugation @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/conjpull.py) | [117](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a32-ad4-g114-gd19-xx82-45/) |
| 32 | 4 | [115](aes-sbox/aes-sbox-a32-ad4-g115-gd18-xx83-35.circ.txt) | 18 | [conjugation @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/conjpull.py) | [127](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a32-ad4-g127-gd15-xx95-7.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a32-ad4-g115-gd18-xx83-35/) |
| 32 | 4 | [117](aes-sbox/aes-sbox-a32-ad4-g117-gd17-xx85-35.circ.txt) | 17 | [conjugation @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/conjpull.py) | [127](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a32-ad4-g127-gd15-xx95-7.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a32-ad4-g117-gd17-xx85-35/) |
| 32 | 4 | [119](aes-sbox/aes-sbox-a32-ad4-g119-gd16-xx87-37.circ.txt) | 16 | [conjugation @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/conjpull.py) | [127](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a32-ad4-g127-gd15-xx95-7.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a32-ad4-g119-gd16-xx87-37/) |
| 32 | 4 | [125](aes-sbox/aes-sbox-a32-ad4-g125-gd15-xx93-37.circ.txt) | 15 | [gate kernel @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/strategies/E/long.sh) | [127](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a32-ad4-g127-gd15-xx95-7.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a32-ad4-g125-gd15-xx93-37/) |
| 32 | 5 | [104](aes-sbox/aes-sbox-a32-ad5-g104-gd29-xx72-23.circ.txt) | 29 | [gate kernel @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/strategies/E/erun.py) | [105](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a32-ad5-g105-gd26-xx73-5.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a32-ad5-g104-gd29-xx72-23/) |
| 32 | 5 | [105](aes-sbox/aes-sbox-a32-ad5-g105-gd24-xx73-24.circ.txt) | 24 | [conjugation @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/conjpull.py) | [107](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a32-ad5-g107-gd22-xx75-4.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a32-ad5-g105-gd24-xx73-24/) |
| 32 | 5 | [106](aes-sbox/aes-sbox-a32-ad5-g106-gd21-xx74-28.circ.txt) | 21 | [conjugation @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/conjpull.py) | [109](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a32-ad5-g109-gd20-xx77-4.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a32-ad5-g106-gd21-xx74-28/) |
| 32 | 5 | [108](aes-sbox/aes-sbox-a32-ad5-g108-gd20-xx76-35.circ.txt) | 20 | [gate kernel @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/cli.py) | [109](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a32-ad5-g109-gd20-xx77-4.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a32-ad5-g108-gd20-xx76-35/) |
| 32 | 5 | [110](aes-sbox/aes-sbox-a32-ad5-g110-gd19-xx78-31.circ.txt) | 19 | [conjugation @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/conjpull.py) | [117](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a32-ad5-g110-gd19-xx78-31/) |
| 32 | 5 | [111](aes-sbox/aes-sbox-a32-ad5-g111-gd18-xx79-34.circ.txt) | 18 | [conjugation @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/conjpull.py) | [122](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a32-ad5-g122-gd16-xx90-15.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a32-ad5-g111-gd18-xx79-34/) |
| 32 | 5 | [115](aes-sbox/aes-sbox-a32-ad5-g115-gd17-xx83-31.circ.txt) | 17 | [depth pull (hub) @ 97abda7](https://github.com/Joe-b-20/xor-circuit-research/blob/97abda77475b990ee0df77957807dfd718cb3c17/nonlinear/boolflux/hub/op_pull.py) | [122](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a32-ad5-g122-gd16-xx90-15.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a32-ad5-g115-gd17-xx83-31/) |
| 32 | 7 | [103](aes-sbox/aes-sbox-a32-ad7-g103-gd29-xx71-25.circ.txt) | 29 | [conjugation @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/conjpull.py) | [105](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a32-ad5-g105-gd26-xx73-5.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a32-ad7-g103-gd29-xx71-25/) |
| 32 | 7 | [104](aes-sbox/aes-sbox-a32-ad7-g104-gd26-xx72-31.circ.txt) | 26 | [conjugation @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/conjpull.py) | [105](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a32-ad5-g105-gd26-xx73-5.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a32-ad7-g104-gd26-xx72-31/) |
| 33 | 4 | [107](aes-sbox/aes-sbox-a33-ad4-g107-gd20-xx74-26.circ.txt) | 20 | [depth pull (hub) @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/hub/op_pull.py) | [108](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a33-ad4-g108-gd20-xx75-5.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a33-ad4-g107-gd20-xx74-26/) |
| 33 | 4 | [108](aes-sbox/aes-sbox-a33-ad4-g108-gd19-xx75-22.circ.txt) | 19 | [gate kernel @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/cli.py) | [116](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a33-ad4-g108-gd19-xx75-22/) |
| 33 | 4 | [110](aes-sbox/aes-sbox-a33-ad4-g110-gd18-xx77-26.circ.txt) | 18 | [gate kernel @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/cli.py) | [116](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a33-ad4-g110-gd18-xx77-26/) |
| 33 | 4 | [112](aes-sbox/aes-sbox-a33-ad4-g112-gd16-xx79-28.circ.txt) | 16 | [gate kernel (hub) @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/hub/op_polish.py) | [116](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a33-ad4-g112-gd16-xx79-28/) |
| 33 | 4 | [115](aes-sbox/aes-sbox-a33-ad4-g115-gd15-xx82-19.circ.txt) | 15 | [join @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/strategies/E/low.sh) | [116](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a33-ad4-g115-gd15-xx82-19/) |
| 34 | 4 | [122](aes-sbox/aes-sbox-a34-ad4-g122-gd14-xx88-38.circ.txt) | 14 | [conjugation @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/conjpull.py) | [125](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a33-ad4-g125-gd14-xx92-18.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a34-ad4-g122-gd14-xx88-38/) |
| 34 | 4 | [134](aes-sbox/aes-sbox-a34-ad4-g134-gd13-xx100-51.circ.txt) | 13 | [gate kernel (hub) @ 97abda7](https://github.com/Joe-b-20/xor-circuit-research/blob/97abda77475b990ee0df77957807dfd718cb3c17/nonlinear/boolflux/hub/op_polish.py) | [139](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a34-ad4-g139-gd13-xx105-22.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a34-ad4-g134-gd13-xx100-51/) |
| 36 | 4 | [129](aes-sbox/aes-sbox-a36-ad4-g129-gd13-xx93-40.circ.txt) | 13 | [gate kernel @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/strategies/E/long.sh) | [133](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a35-ad4-g133-gd13-xx98-21.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a36-ad4-g129-gd13-xx93-40/) |
| 37 | 4 | [121](aes-sbox/aes-sbox-a37-ad4-g121-gd14-xx84-36.circ.txt) | 14 | [gate kernel @ 0659eb9](https://github.com/Joe-b-20/xor-circuit-research/blob/0659eb9bad3b663afba6bc2bc4da45c9a2177848/nonlinear/boolflux/kernel/bfx.c) | [125](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a33-ad4-g125-gd14-xx92-18.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a37-ad4-g121-gd14-xx84-36/) |
| 37 | 4 | [127](aes-sbox/aes-sbox-a37-ad4-g127-gd13-xx90-41.circ.txt) | 13 | [conjugation @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/conjpull.py) | [133](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a35-ad4-g133-gd13-xx98-21.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a37-ad4-g127-gd13-xx90-41/) |

#### AND depth 3

| A | AD | G | GD | Found by | NIST | Logs |
|---:|---:|---:|---:|---|---:|---|
| 35 | 3 | [137](aes-sbox/aes-sbox-a35-ad3-g137-gd28-xx102-47.circ.txt) | 28 | [re-basing @ 8922cac](https://github.com/Joe-b-20/xor-circuit-research/tree/8922cacae4d4314968c5ce9baa740dea7aa38935/nonlinear/boolflux) | [139](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a35-ad3-g139-gd27-xx104-38.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a35-ad3-g137-gd28-xx102-47/) |
| 35 | 3 | [138](aes-sbox/aes-sbox-a35-ad3-g138-gd23-xx103-46.circ.txt) | 23 | [conjugation @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/conjpull.py) | [147](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a35-ad3-g147-gd20-xx112-36.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a35-ad3-g138-gd23-xx103-46/) |
| 35 | 3 | [139](aes-sbox/aes-sbox-a35-ad3-g139-gd21-xx104-50.circ.txt) | 21 | [conjugation @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/conjpull.py) | [147](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a35-ad3-g147-gd20-xx112-36.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a35-ad3-g139-gd21-xx104-50/) |
| 35 | 3 | [141](aes-sbox/aes-sbox-a35-ad3-g141-gd19-xx106-46.circ.txt) | 19 | [product exchange @ d961083](https://github.com/Joe-b-20/xor-circuit-research/blob/d961083c97330ea269d4f86fb0d55618cec72c32/nonlinear/boolflux/strategies/T3/gf4loop.py) | [157](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a35-ad3-g157-gd15-xx122-31.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a35-ad3-g141-gd19-xx106-46/) |
| 35 | 3 | [143](aes-sbox/aes-sbox-a35-ad3-g143-gd18-xx108-49.circ.txt) | 18 | [product exchange @ f9fe6f7](https://github.com/Joe-b-20/xor-circuit-research/tree/f9fe6f7db5b57ec8d3802ac18fbca2905486bde0/nonlinear/boolflux) | [157](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a35-ad3-g157-gd15-xx122-31.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a35-ad3-g143-gd18-xx108-49/) |
| 35 | 3 | [144](aes-sbox/aes-sbox-a35-ad3-g144-gd17-xx109-48.circ.txt) | 17 | [depth pull (hub) @ 8922cac](https://github.com/Joe-b-20/xor-circuit-research/blob/8922cacae4d4314968c5ce9baa740dea7aa38935/nonlinear/boolflux/hub/op_pull.py) | [157](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a35-ad3-g157-gd15-xx122-31.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a35-ad3-g144-gd17-xx109-48/) |
| 35 | 3 | [147](aes-sbox/aes-sbox-a35-ad3-g147-gd16-xx112-60.circ.txt) | 16 | [depth pull (hub) @ 8922cac](https://github.com/Joe-b-20/xor-circuit-research/blob/8922cacae4d4314968c5ce9baa740dea7aa38935/nonlinear/boolflux/hub/op_pull.py) | [157](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a35-ad3-g157-gd15-xx122-31.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a35-ad3-g147-gd16-xx112-60/) |
| 35 | 3 | [155](aes-sbox/aes-sbox-a35-ad3-g155-gd15-xx120-56.circ.txt) | 15 | [depth pull (hub) @ 8922cac](https://github.com/Joe-b-20/xor-circuit-research/blob/8922cacae4d4314968c5ce9baa740dea7aa38935/nonlinear/boolflux/hub/op_pull.py) | [157](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a35-ad3-g157-gd15-xx122-31.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a35-ad3-g155-gd15-xx120-56/) |
| 35 | 3 | [162](aes-sbox/aes-sbox-a35-ad3-g162-gd14-xx127-61.circ.txt) | 14 | [region rebuild @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/strategies/F/fdrive.py) | [172](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a35-ad3-g172-gd14-xx137-30.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a35-ad3-g162-gd14-xx127-61/) |
| 35 | 3 | [165](aes-sbox/aes-sbox-a35-ad3-g165-gd13-xx130-60.circ.txt) | 13 | [re-basing @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/rebase.py) | [183](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a35-ad3-g183-gd13-xx148-29.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a35-ad3-g165-gd13-xx130-60/) |
| 35 | 3 | [181](aes-sbox/aes-sbox-a35-ad3-g181-gd12-xx146-80.circ.txt) | 12 | [re-basing @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/rebase.py) | — | [logs](aes-sbox/logs/aes-sbox-a35-ad3-g181-gd12-xx146-80/) |
| 36 | 3 | [161](aes-sbox/aes-sbox-a36-ad3-g161-gd14-xx125-57.circ.txt) | 14 | [cap oscillation (hub) @ 97abda7](https://github.com/Joe-b-20/xor-circuit-research/blob/97abda77475b990ee0df77957807dfd718cb3c17/nonlinear/boolflux/hub/archive.py) | [172](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a35-ad3-g172-gd14-xx137-30.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a36-ad3-g161-gd14-xx125-57/) |
| 37 | 3 | [160](aes-sbox/aes-sbox-a37-ad3-g160-gd14-xx123-52.circ.txt) | 14 | [join (hub) @ 97abda7](https://github.com/Joe-b-20/xor-circuit-research/blob/97abda77475b990ee0df77957807dfd718cb3c17/nonlinear/boolflux/hub/op_join.py) | [172](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-sbox/aes-sbox-a35-ad3-g172-gd14-xx137-30.circ.txt) | [logs](aes-sbox/logs/aes-sbox-a37-ad3-g160-gd14-xx123-52/) |

#### #AND ≥ 38

| A | AD | G | GD | Found by | NIST | Logs |
|---:|---:|---:|---:|---|---:|---|
| 38 | 4 | [135](aes-sbox/aes-sbox-a38-ad4-g135-gd12-xx97-25.circ.txt) | 12 | [shared-bottom rebuild @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/campaigns/targets/ops/bottom.py) | — | [logs](aes-sbox/logs/aes-sbox-a38-ad4-g135-gd12-xx97-25/) |
| 42 | 4 | [284](aes-sbox/aes-sbox-a42-ad4-g284-gd11-xx242-114.circ.txt) | 11 | [gate kernel @ d961083](https://github.com/Joe-b-20/xor-circuit-research/blob/d961083c97330ea269d4f86fb0d55618cec72c32/nonlinear/boolflux/strategies/F/fdrive.py) | — | [logs](aes-sbox/logs/aes-sbox-a42-ad4-g284-gd11-xx242-114/) |
| 43 | 4 | [278](aes-sbox/aes-sbox-a43-ad4-g278-gd11-xx235-123.circ.txt) | 11 | [gate kernel @ d961083](https://github.com/Joe-b-20/xor-circuit-research/blob/d961083c97330ea269d4f86fb0d55618cec72c32/nonlinear/boolflux/strategies/F/fdrive.py) | — | [logs](aes-sbox/logs/aes-sbox-a43-ad4-g278-gd11-xx235-123/) |
| 44 | 4 | [254](aes-sbox/aes-sbox-a44-ad4-g254-gd11-xx210-122.circ.txt) | 11 | [gate kernel @ d961083](https://github.com/Joe-b-20/xor-circuit-research/blob/d961083c97330ea269d4f86fb0d55618cec72c32/nonlinear/boolflux/strategies/F/fdrive.py) | — | [logs](aes-sbox/logs/aes-sbox-a44-ad4-g254-gd11-xx210-122/) |
| 46 | 4 | [200](aes-sbox/aes-sbox-a46-ad4-g200-gd11-xx154-73.circ.txt) | 11 | [gate kernel (hub) @ 8922cac](https://github.com/Joe-b-20/xor-circuit-research/blob/8922cacae4d4314968c5ce9baa740dea7aa38935/nonlinear/boolflux/hub/op_polish.py) | — | [logs](aes-sbox/logs/aes-sbox-a46-ad4-g200-gd11-xx154-73/) |
| 47 | 4 | [186](aes-sbox/aes-sbox-a47-ad4-g186-gd11-xx139-70.circ.txt) | 11 | [gate kernel @ d961083](https://github.com/Joe-b-20/xor-circuit-research/blob/d961083c97330ea269d4f86fb0d55618cec72c32/nonlinear/boolflux/strategies/F/fdrive.py) | — | [logs](aes-sbox/logs/aes-sbox-a47-ad4-g186-gd11-xx139-70/) |
| 48 | 4 | [151](aes-sbox/aes-sbox-a48-ad4-g151-gd11-xx103-47.circ.txt) | 11 | [gate kernel @ e657298](https://github.com/Joe-b-20/xor-circuit-research/blob/e6572989734e1106785c89c6e6d99b01ae681402/nonlinear/boolflux/strategies/E/memetic.py) | — | [logs](aes-sbox/logs/aes-sbox-a48-ad4-g151-gd11-xx103-47/) |

**Found by** (all BoolFlux; each entry links to the code its `found.json` names, at the commit
shown; how the methods work is in
[search/nonlinear/HOW-IT-WORKS.md](../search/nonlinear/HOW-IT-WORKS.md#moves-around-the-kernel)):
*gate kernel*, the gate-replacement search under caps on A, AD and GD; *depth pull*, the kernel
with one cap lowered; *cap oscillation*, a cap relaxed, then restored; *region rebuild*, a
timing-driven rebuild of one XOR region; *skeleton kick*, a change of the AND skeleton followed
by a short kernel polish; *join*, the front of one circuit and the back of another, met at a
shared interface function; *conjugation*, a GF(2⁸) conjugate of the start followed by staged
kernel pulls; *re-basing*, of the level-3 product classes (AND depth 3); *shared-bottom rebuild*;
*SAT LNS*, the span-pooled SAT neighbourhood search; *product exchange*, level-1 AND products
exchanged within their span, then the kernel. "(hub)": the operator ran in the
[hub](../search/nonlinear/HOW-IT-WORKS.md#the-hub), the shared archive that schedules the
operators. Each `found.json` names the start: 9 runs started from a NIST circuit and 2 joins had
a NIST parent; 56 runs started from circuits of ours (in `logs/`), most of them descended from
NIST's; for 7 the start was an intermediate circuit the run did not keep.

The commit shown is the run's own when the linked file is in it, and otherwise `e657298`, where
`found.json` records the paths (the file was uncommitted when the run started). Most runs had
uncommitted changes, which `found.json` says, so the linked code can differ from what ran. Where
`found.json` names no file, the link is to the BoolFlux folder at the run's commit.

### AES inverse S-box

[aes-invsbox](aes-invsbox/): 8 inputs, 8 outputs; the inverse of the AES S-box, in NIST's file
format and naming (`aes-invsbox-aA-adAD-gG-gdGD-xxX-Y`; with N NOT gates, `-xxnL-Y-N` and
L = X + N, as NIST names them), counted as for the S-box. Inputs are `x0:x7` and outputs `y0:y7`,
as in NIST's inverse files (`x0` and `y0` are the most significant bits).

Which circuits are here: the same rule as for the S-box, against all 91 inverse S-box circuits of
NIST's repository at commit `3d807741` (its folders `aes-invsbox/`, `sbox/` (`aes-sbox-inv-*`) and
`old-2020/` (`aes-sbox-rev-*`)). **NIST**: NIST's fewest gates among its circuits with A, AD and GD
at most ours. Rows are sorted by A, then AD, then G, then GD.

These 45 circuits are from one BoolFlux run, 2026-11-16 16:14-21:03 UTC (planned for 12 hours,
stopped after about 5; finished), seeded with NIST's 91 inverse circuits: the hub (gate
kernel, depth pull, join, region rebuild)
and conjugation jobs from the 33 points of NIST's inverse Pareto front. 21 of those 33 points are
dominated by one of ours (as good in all four metrics and better in at least one); at the other 12
the run found only circuits equal to NIST's, which are not listed. Where the run
found several circuits with the same (A, AD, G, GD), the one here is the first it found.

They are the first circuits here published with the run's own logs. Each `logs/<name>/` has
`found.json` (start circuit, the exact command and environment, seed, time, code),
`verification.json`, `start.circ.txt` where the start is ours (`front.circ.txt` and
`back.circ.txt` for a join), and the run's logs for that circuit: for a hub circuit,
`hub-lineage.json.gz` (every circuit of its lineage back to NIST's, with its hub record, the job's
run record, kernel settings and kernel log) and `hub-events.jsonl.gz`; for a conjugation job,
`conjpull.log.gz` and `conj-job.json.gz`. Paths in them are written `<checkout>`, `<campaign archive>` and
`<home>`, which `found.json` explains. The search ran BoolFlux at commit `c0fb67d`, without uncommitted
changes, with a run-time layer for the inverse (BoolFlux was then written for the forward S-box
only), published in [aes-invsbox/logs/_runtime/](aes-invsbox/logs/_runtime/): `shim/` points
BoolFlux's S-box checks (both verifiers) and its NIST comparison set at the inverse, and
`bin/invconjpull.py` runs `ops/conjpull.py` with inverse conjugates; `bin/launch.sh` started the
run.

#### #AND = 28

| A | AD | G | GD | Found by | NIST | Logs |
|---:|---:|---:|---:|---|---:|---|
| 28 | 4 | [132](aes-invsbox/aes-invsbox-a28-ad4-g132-gd22-xx104-60.circ.txt) | 22 | [gate kernel (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [135](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a28-ad4-g135-gd20-xx107-35.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a28-ad4-g132-gd22-xx104-60/) |
| 28 | 4 | [134](aes-invsbox/aes-invsbox-a28-ad4-g134-gd20-xx106-58.circ.txt) | 20 | [conjugation @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/ops/conjpull.py) | [135](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a28-ad4-g135-gd20-xx107-35.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a28-ad4-g134-gd20-xx106-58/) |
| 28 | 4 | [135](aes-invsbox/aes-invsbox-a28-ad4-g135-gd19-xx107-53.circ.txt) | 19 | [conjugation @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/ops/conjpull.py) | [140](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a28-ad4-g140-gd19-xx112-30.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a28-ad4-g135-gd19-xx107-53/) |
| 28 | 4 | [136](aes-invsbox/aes-invsbox-a28-ad4-g136-gd18-xx108-56.circ.txt) | 18 | [conjugation @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/ops/conjpull.py) | [150](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a28-ad4-g150-gd16-xx122-27.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a28-ad4-g136-gd18-xx108-56/) |
| 28 | 4 | [137](aes-invsbox/aes-invsbox-a28-ad4-g137-gd17-xx109-69.circ.txt) | 17 | [conjugation @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/ops/conjpull.py) | [150](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a28-ad4-g150-gd16-xx122-27.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a28-ad4-g137-gd17-xx109-69/) |
| 28 | 4 | [143](aes-invsbox/aes-invsbox-a28-ad4-g143-gd16-xxn115-59-1.circ.txt) | 16 | [conjugation @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/ops/conjpull.py) | [150](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a28-ad4-g150-gd16-xx122-27.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a28-ad4-g143-gd16-xxn115-59-1/) |
| 28 | 4 | [154](aes-invsbox/aes-invsbox-a28-ad4-g154-gd15-xx126-61.circ.txt) | 15 | [depth pull (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [156](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a28-ad4-g156-gd15-xx128-28.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a28-ad4-g154-gd15-xx126-61/) |
| 28 | 5 | [127](aes-invsbox/aes-invsbox-a28-ad5-g127-gd25-xx99-28.circ.txt) | 25 | [join (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/join.py) | [129](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a28-ad5-g129-gd22-xx101-30.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a28-ad5-g127-gd25-xx99-28/) |
| 28 | 5 | [128](aes-invsbox/aes-invsbox-a28-ad5-g128-gd24-xx100-28.circ.txt) | 24 | [region rebuild (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/trb_impl.py) | [129](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a28-ad5-g129-gd22-xx101-30.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a28-ad5-g128-gd24-xx100-28/) |
| 28 | 5 | [130](aes-invsbox/aes-invsbox-a28-ad5-g130-gd21-xx102-49.circ.txt) | 21 | [depth pull (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [131](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a28-ad5-g131-gd20-xx103-29.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a28-ad5-g130-gd21-xx102-49/) |
| 28 | 5 | [134](aes-invsbox/aes-invsbox-a28-ad5-g134-gd18-xx106-54.circ.txt) | 18 | [gate kernel (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [147](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a28-ad5-g147-gd16-xx119-25.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a28-ad5-g134-gd18-xx106-54/) |

#### 29 ≤ #AND ≤ 31

| A | AD | G | GD | Found by | NIST | Logs |
|---:|---:|---:|---:|---|---:|---|
| 31 | 5 | [119](aes-invsbox/aes-invsbox-a31-ad5-g119-gd22-xx88-28.circ.txt) | 22 | [gate kernel (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [129](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a28-ad5-g129-gd22-xx101-30.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a31-ad5-g119-gd22-xx88-28/) |
| 31 | 5 | [120](aes-invsbox/aes-invsbox-a31-ad5-g120-gd21-xx89-36.circ.txt) | 21 | [gate kernel (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [131](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a28-ad5-g131-gd20-xx103-29.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a31-ad5-g120-gd21-xx89-36/) |
| 31 | 5 | [121](aes-invsbox/aes-invsbox-a31-ad5-g121-gd20-xx90-35.circ.txt) | 20 | [join (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/join.py) | [131](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a28-ad5-g131-gd20-xx103-29.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a31-ad5-g121-gd20-xx90-35/) |
| 31 | 5 | [122](aes-invsbox/aes-invsbox-a31-ad5-g122-gd19-xx91-40.circ.txt) | 19 | [gate kernel (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [132](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a28-ad5-g132-gd19-xx104-23.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a31-ad5-g122-gd19-xx91-40/) |
| 31 | 5 | [127](aes-invsbox/aes-invsbox-a31-ad5-g127-gd18-xx96-38.circ.txt) | 18 | [depth pull (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [147](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a28-ad5-g147-gd16-xx119-25.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a31-ad5-g127-gd18-xx96-38/) |
| 31 | 5 | [131](aes-invsbox/aes-invsbox-a31-ad5-g131-gd17-xx100-33.circ.txt) | 17 | [depth pull (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [147](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a28-ad5-g147-gd16-xx119-25.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a31-ad5-g131-gd17-xx100-33/) |
| 31 | 6 | [117](aes-invsbox/aes-invsbox-a31-ad6-g117-gd25-xx86-47.circ.txt) | 25 | [gate kernel (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [129](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a28-ad5-g129-gd22-xx101-30.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a31-ad6-g117-gd25-xx86-47/) |

#### 32 ≤ #AND ≤ 37, AND depth ≥ 4

| A | AD | G | GD | Found by | NIST | Logs |
|---:|---:|---:|---:|---|---:|---|
| 32 | 4 | [118](aes-invsbox/aes-invsbox-a32-ad4-g118-gd19-xx86-40.circ.txt) | 19 | [gate kernel (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [128](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a32-ad4-g128-gd16-xx96-11.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a32-ad4-g118-gd19-xx86-40/) |
| 32 | 4 | [119](aes-invsbox/aes-invsbox-a32-ad4-g119-gd18-xx87-33.circ.txt) | 18 | [conjugation @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/ops/conjpull.py) | [128](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a32-ad4-g128-gd16-xx96-11.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a32-ad4-g119-gd18-xx87-33/) |
| 32 | 4 | [120](aes-invsbox/aes-invsbox-a32-ad4-g120-gd17-xx88-31.circ.txt) | 17 | [join (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/join.py) | [128](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a32-ad4-g128-gd16-xx96-11.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a32-ad4-g120-gd17-xx88-31/) |
| 32 | 4 | [123](aes-invsbox/aes-invsbox-a32-ad4-g123-gd16-xx91-46.circ.txt) | 16 | [conjugation @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/ops/conjpull.py) | [128](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a32-ad4-g128-gd16-xx96-11.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a32-ad4-g123-gd16-xx91-46/) |
| 32 | 4 | [131](aes-invsbox/aes-invsbox-a32-ad4-g131-gd15-xxn99-29-1.circ.txt) | 15 | [depth pull (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [135](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a32-ad4-g135-gd15-xx103-11.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a32-ad4-g131-gd15-xxn99-29-1/) |
| 32 | 5 | [107](aes-invsbox/aes-invsbox-a32-ad5-g107-gd22-xx75-24.circ.txt) | 22 | [conjugation @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/ops/conjpull.py) | [110](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a32-ad5-g110-gd20-xx78-7.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a32-ad5-g107-gd22-xx75-24/) |
| 32 | 5 | [108](aes-invsbox/aes-invsbox-a32-ad5-g108-gd21-xx76-27.circ.txt) | 21 | [join (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/join.py) | [110](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a32-ad5-g110-gd20-xx78-7.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a32-ad5-g108-gd21-xx76-27/) |
| 32 | 5 | [109](aes-invsbox/aes-invsbox-a32-ad5-g109-gd20-xx77-28.circ.txt) | 20 | [conjugation @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/ops/conjpull.py) | [110](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a32-ad5-g110-gd20-xx78-7.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a32-ad5-g109-gd20-xx77-28/) |
| 32 | 5 | [111](aes-invsbox/aes-invsbox-a32-ad5-g111-gd19-xx79-31.circ.txt) | 19 | [conjugation @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/ops/conjpull.py) | [125](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a32-ad5-g125-gd15-xx93-21.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a32-ad5-g111-gd19-xx79-31/) |
| 32 | 5 | [113](aes-invsbox/aes-invsbox-a32-ad5-g113-gd18-xx81-38.circ.txt) | 18 | [depth pull (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [125](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a32-ad5-g125-gd15-xx93-21.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a32-ad5-g113-gd18-xx81-38/) |
| 32 | 5 | [116](aes-invsbox/aes-invsbox-a32-ad5-g116-gd17-xx84-37.circ.txt) | 17 | [depth pull (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [125](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a32-ad5-g125-gd15-xx93-21.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a32-ad5-g116-gd17-xx84-37/) |
| 32 | 5 | [121](aes-invsbox/aes-invsbox-a32-ad5-g121-gd16-xx89-44.circ.txt) | 16 | [conjugation @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/ops/conjpull.py) | [125](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a32-ad5-g125-gd15-xx93-21.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a32-ad5-g121-gd16-xx89-44/) |
| 32 | 5 | [124](aes-invsbox/aes-invsbox-a32-ad5-g124-gd15-xxn92-38-1.circ.txt) | 15 | [gate kernel (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [125](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a32-ad5-g125-gd15-xx93-21.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a32-ad5-g124-gd15-xxn92-38-1/) |
| 33 | 4 | [109](aes-invsbox/aes-invsbox-a33-ad4-g109-gd19-xx76-26.circ.txt) | 19 | [gate kernel (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [114](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a33-ad4-g114-gd18-xx81-11.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a33-ad4-g109-gd19-xx76-26/) |
| 33 | 4 | [110](aes-invsbox/aes-invsbox-a33-ad4-g110-gd18-xx77-12.circ.txt) | 18 | [join (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/join.py) | [114](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a33-ad4-g114-gd18-xx81-11.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a33-ad4-g110-gd18-xx77-12/) |
| 33 | 4 | [111](aes-invsbox/aes-invsbox-a33-ad4-g111-gd17-xx78-30.circ.txt) | 17 | [gate kernel (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [118](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a33-ad4-g118-gd15-xx85-9.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a33-ad4-g111-gd17-xx78-30/) |
| 33 | 4 | [114](aes-invsbox/aes-invsbox-a33-ad4-g114-gd16-xx81-36.circ.txt) | 16 | [join (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/join.py) | [118](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a33-ad4-g118-gd15-xx85-9.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a33-ad4-g114-gd16-xx81-36/) |
| 33 | 4 | [117](aes-invsbox/aes-invsbox-a33-ad4-g117-gd15-xx84-18.circ.txt) | 15 | [join (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/join.py) | [118](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a33-ad4-g118-gd15-xx85-9.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a33-ad4-g117-gd15-xx84-18/) |
| 33 | 4 | [122](aes-invsbox/aes-invsbox-a33-ad4-g122-gd14-xx89-40.circ.txt) | 14 | [gate kernel (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [123](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a33-ad4-g123-gd14-xx90-16.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a33-ad4-g122-gd14-xx89-40/) |
| 34 | 4 | [131](aes-invsbox/aes-invsbox-a34-ad4-g131-gd13-xx97-43.circ.txt) | 13 | [gate kernel (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [134](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a34-ad4-g134-gd13-xx100-23.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a34-ad4-g131-gd13-xx97-43/) |

#### AND depth 3

| A | AD | G | GD | Found by | NIST | Logs |
|---:|---:|---:|---:|---|---:|---|
| 35 | 3 | [144](aes-invsbox/aes-invsbox-a35-ad3-g144-gd21-xx109-44.circ.txt) | 21 | [gate kernel (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [154](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a35-ad3-g154-gd20-xx119-30.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a35-ad3-g144-gd21-xx109-44/) |
| 35 | 3 | [145](aes-invsbox/aes-invsbox-a35-ad3-g145-gd20-xx110-51.circ.txt) | 20 | [depth pull (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [154](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a35-ad3-g154-gd20-xx119-30.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a35-ad3-g145-gd20-xx110-51/) |
| 35 | 3 | [146](aes-invsbox/aes-invsbox-a35-ad3-g146-gd19-xx111-42.circ.txt) | 19 | [region rebuild (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/trb_impl.py) | [157](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a35-ad3-g157-gd15-xx122-27.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a35-ad3-g146-gd19-xx111-42/) |
| 35 | 3 | [147](aes-invsbox/aes-invsbox-a35-ad3-g147-gd18-xx112-62.circ.txt) | 18 | [depth pull (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [157](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a35-ad3-g157-gd15-xx122-27.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a35-ad3-g147-gd18-xx112-62/) |
| 35 | 3 | [149](aes-invsbox/aes-invsbox-a35-ad3-g149-gd17-xx114-54.circ.txt) | 17 | [conjugation @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/ops/conjpull.py) | [157](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a35-ad3-g157-gd15-xx122-27.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a35-ad3-g149-gd17-xx114-54/) |
| 35 | 3 | [152](aes-invsbox/aes-invsbox-a35-ad3-g152-gd15-xx117-56.circ.txt) | 15 | [gate kernel (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [157](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a35-ad3-g157-gd15-xx122-27.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a35-ad3-g152-gd15-xx117-56/) |
| 35 | 3 | [154](aes-invsbox/aes-invsbox-a35-ad3-g154-gd14-xx119-55.circ.txt) | 14 | [depth pull (hub) @ c0fb67d](https://github.com/Joe-b-20/xor-circuit-research/blob/c0fb67d08e227c91e8ade9fa0a47ff0e46ba7210/search/nonlinear/boolflux/hub/ops.py) | [190](https://github.com/usnistgov/Circuits/blob/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes/aes-invsbox/aes-invsbox-a35-ad3-g190-gd14-xx155-27.circ.txt) | [logs](aes-invsbox/logs/aes-invsbox-a35-ad3-g154-gd14-xx119-55/) |

**Found by**: as for the S-box; each entry links to the code at `c0fb67d`, which ran with
`logs/_runtime/`. 16 runs started from a NIST circuit (named in `found.json`); the other
29 from circuits of the same run, all descended from NIST's.

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
| 5 | [118](aes-invmixcolumns/aes-invmixcolumns-xor118-depth5.circ.txt) | v9 prototype ⁷ | [119](https://github.com/usnistgov/Circuits/blob/master/data/slp/aes/aes-invmixcols/aes-invmixcols-xor119-depth5.circ.txt) | [logs](aes-invmixcolumns/logs/aes-invmixcolumns-xor118-depth5/) |
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
| [small-scale-aes](small-scale-aes/) | 72 | 43@5 | [63@3](small-scale-aes/small-scale-aes-xor63-depth3.circ.txt), [44@4](small-scale-aes/small-scale-aes-xor44-depth4.circ.txt), [42@5](small-scale-aes/small-scale-aes-xor42-depth5.circ.txt) | v8 |

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
| [anubis-clefia-m0](anubis-clefia-m0/) | 184 | 98@9 | [95@5](anubis-clefia-m0/anubis-clefia-m0-xor95-depth5.circ.txt), [92@6](anubis-clefia-m0/anubis-clefia-m0-xor92-depth6.circ.txt), [91@8](anubis-clefia-m0/anubis-clefia-m0-xor91-depth8.circ.txt) | v8 |
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
| [jpst17-4x4-gf256](jpst17-4x4-gf256/) | 122 | 82@7 | [82@4](jpst17-4x4-gf256/jpst17-4x4-gf256-xor82-depth4.circ.txt), [80@5](jpst17-4x4-gf256/jpst17-4x4-gf256-xor80-depth5.circ.txt), [78@6](jpst17-4x4-gf256/jpst17-4x4-gf256-xor78-depth6.circ.txt) | v8 |
| [jpst17-4x4-gf256-inv](jpst17-4x4-gf256-inv/) | 136 | 83@6 | [94@3](jpst17-4x4-gf256-inv/jpst17-4x4-gf256-inv-xor94-depth3.circ.txt)⁴, [84@4](jpst17-4x4-gf256-inv/jpst17-4x4-gf256-inv-xor84-depth4.circ.txt)⁴, [82@5](jpst17-4x4-gf256-inv/jpst17-4x4-gf256-inv-xor82-depth5.circ.txt), [80@6](jpst17-4x4-gf256-inv/jpst17-4x4-gf256-inv-xor80-depth6.circ.txt) | v8 |
| [klsw17-m-4x4-gf256](klsw17-m-4x4-gf256/) | 184 | 72@7 | [72@4](klsw17-m-4x4-gf256/klsw17-m-4x4-gf256-xor72-depth4.circ.txt), [64@6](klsw17-m-4x4-gf256/klsw17-m-4x4-gf256-xor64-depth6.circ.txt) | v8 |
| [klsw17-m-4x4-gf256-inv](klsw17-m-4x4-gf256-inv/) | 128 | 78@5 | [76@4](klsw17-m-4x4-gf256-inv/klsw17-m-4x4-gf256-inv-xor76-depth4.circ.txt), [75@5](klsw17-m-4x4-gf256-inv/klsw17-m-4x4-gf256-inv-xor75-depth5.circ.txt), [74@6](klsw17-m-4x4-gf256-inv/klsw17-m-4x4-gf256-inv-xor74-depth6.circ.txt) | v8 |
| [ls16-4x4-gf256](ls16-4x4-gf256/) | 128 | 109@5 | [103@4](ls16-4x4-gf256/ls16-4x4-gf256-xor103-depth4.circ.txt) | v8 |
| [lw16-4x4-gf256](lw16-4x4-gf256/) | 106 | 100@6 | [102@3](lw16-4x4-gf256/lw16-4x4-gf256-xor102-depth3.circ.txt), [96@4](lw16-4x4-gf256/lw16-4x4-gf256-xor96-depth4.circ.txt) | v8 |
| [lw16-4x4-gf256-inv-circ](lw16-4x4-gf256-inv-circ/) | 132 | 89@7 | [126@3](lw16-4x4-gf256-inv-circ/lw16-4x4-gf256-inv-circ-xor126-depth3.circ.txt), [86@4](lw16-4x4-gf256-inv-circ/lw16-4x4-gf256-inv-circ-xor86-depth4.circ.txt), [82@5](lw16-4x4-gf256-inv-circ/lw16-4x4-gf256-inv-circ-xor82-depth5.circ.txt), [81@10](lw16-4x4-gf256-inv-circ/lw16-4x4-gf256-inv-circ-xor81-depth10.circ.txt) | v8 |
| [lw16-4x4-gf256-inv-had](lw16-4x4-gf256-inv-had/) | 136 | 87@5 | [85@4](lw16-4x4-gf256-inv-had/lw16-4x4-gf256-inv-had-xor85-depth4.circ.txt), [84@5](lw16-4x4-gf256-inv-had/lw16-4x4-gf256-inv-had-xor84-depth5.circ.txt) | v8 |
| [skop15-4x4-gf256](skop15-4x4-gf256/) | 136 | 90@6 | [89@4](skop15-4x4-gf256/skop15-4x4-gf256-xor89-depth4.circ.txt), [88@6](skop15-4x4-gf256/skop15-4x4-gf256-xor88-depth6.circ.txt), [87@7](skop15-4x4-gf256/skop15-4x4-gf256-xor87-depth7.circ.txt) | v8 |
| [skop15-4x4-gf256-inv](skop15-4x4-gf256-inv/) | 144 | 91@6 | [90@4](skop15-4x4-gf256-inv/skop15-4x4-gf256-inv-xor90-depth4.circ.txt), [89@5](skop15-4x4-gf256-inv/skop15-4x4-gf256-inv-xor89-depth5.circ.txt), [88@6](skop15-4x4-gf256-inv/skop15-4x4-gf256-inv-xor88-depth6.circ.txt), [86@7](skop15-4x4-gf256-inv/skop15-4x4-gf256-inv-xor86-depth7.circ.txt), [85@9](skop15-4x4-gf256-inv/skop15-4x4-gf256-inv-xor85-depth9.circ.txt) | v8 |
| [ss16-4x4-gf256](ss16-4x4-gf256/) | 123 | 104@6 | [103@3](ss16-4x4-gf256/ss16-4x4-gf256-xor103-depth3.circ.txt), [98@4](ss16-4x4-gf256/ss16-4x4-gf256-xor98-depth4.circ.txt), [96@5](ss16-4x4-gf256/ss16-4x4-gf256-xor96-depth5.circ.txt) | v8 |
| [ss16-4x4-gf256-inv](ss16-4x4-gf256-inv/) | 160 | 93@8 | [92@5](ss16-4x4-gf256-inv/ss16-4x4-gf256-inv-xor92-depth5.circ.txt), [91@8](ss16-4x4-gf256-inv/ss16-4x4-gf256-inv-xor91-depth8.circ.txt), [90@9](ss16-4x4-gf256-inv/ss16-4x4-gf256-inv-xor90-depth9.circ.txt), [88@10](ss16-4x4-gf256-inv/ss16-4x4-gf256-inv-xor88-depth10.circ.txt) | v8 |

### MDS 8×8 over GF(2⁴)

| Map | Direct XOR | NIST | Ours (gates@depth) | Found by |
|---|---:|---|---|---|
| [klsw17-m-8x8-gf16-0x13](klsw17-m-8x8-gf16-0x13/) | 456 | 175@12 | [178@6](klsw17-m-8x8-gf16-0x13/klsw17-m-8x8-gf16-0x13-xor178-depth6.circ.txt), [171@9](klsw17-m-8x8-gf16-0x13/klsw17-m-8x8-gf16-0x13-xor171-depth9.circ.txt), [161@10](klsw17-m-8x8-gf16-0x13/klsw17-m-8x8-gf16-0x13-xor161-depth10.circ.txt) | v8 |
| [klsw17-m-8x8-gf16-0x13-inv](klsw17-m-8x8-gf16-0x13-inv/) | 540 | 176@12 | [191@6](klsw17-m-8x8-gf16-0x13-inv/klsw17-m-8x8-gf16-0x13-inv-xor191-depth6.circ.txt), [164@10](klsw17-m-8x8-gf16-0x13-inv/klsw17-m-8x8-gf16-0x13-inv-xor164-depth10.circ.txt), [163@11](klsw17-m-8x8-gf16-0x13-inv/klsw17-m-8x8-gf16-0x13-inv-xor163-depth11.circ.txt), [162@13](klsw17-m-8x8-gf16-0x13-inv/klsw17-m-8x8-gf16-0x13-inv-xor162-depth13.circ.txt) | v8 |
| [skop15-8x8-gf16](skop15-8x8-gf16/) | 432 | 170@19 | [361@4](skop15-8x8-gf16/skop15-8x8-gf16-xor361-depth4.circ.txt)³, [203@5](skop15-8x8-gf16/skop15-8x8-gf16-xor203-depth5.circ.txt), [196@7](skop15-8x8-gf16/skop15-8x8-gf16-xor196-depth7.circ.txt), [174@8](skop15-8x8-gf16/skop15-8x8-gf16-xor174-depth8.circ.txt), [166@9](skop15-8x8-gf16/skop15-8x8-gf16-xor166-depth9.circ.txt), [158@10](skop15-8x8-gf16/skop15-8x8-gf16-xor158-depth10.circ.txt), [157@11](skop15-8x8-gf16/skop15-8x8-gf16-xor157-depth11.circ.txt), [149@12](skop15-8x8-gf16/skop15-8x8-gf16-xor149-depth12.circ.txt), [147@13](skop15-8x8-gf16/skop15-8x8-gf16-xor147-depth13.circ.txt), [146@14](skop15-8x8-gf16/skop15-8x8-gf16-xor146-depth14.circ.txt) | v8 |
| [skop15-8x8-gf16-inv](skop15-8x8-gf16-inv/) | 512 | 180@12 | [192@6](skop15-8x8-gf16-inv/skop15-8x8-gf16-inv-xor192-depth6.circ.txt), [163@10](skop15-8x8-gf16-inv/skop15-8x8-gf16-inv-xor163-depth10.circ.txt) | v8 |
| [ss17-8x8-gf16](ss17-8x8-gf16/) | 394 | 178@10 | [335@4](ss17-8x8-gf16/ss17-8x8-gf16-xor335-depth4.circ.txt), [194@5](ss17-8x8-gf16/ss17-8x8-gf16-xor194-depth5.circ.txt), [174@8](ss17-8x8-gf16/ss17-8x8-gf16-xor174-depth8.circ.txt), [164@9](ss17-8x8-gf16/ss17-8x8-gf16-xor164-depth9.circ.txt), [161@10](ss17-8x8-gf16/ss17-8x8-gf16-xor161-depth10.circ.txt), [160@11](ss17-8x8-gf16/ss17-8x8-gf16-xor160-depth11.circ.txt) | v8 |

## 64×64

### Ciphers

| Map | Direct XOR | NIST | Ours (gates@depth) | Found by |
|---|---:|---|---|---|
| [fox-mu8](fox-mu8/) | 1257 | 540@14 | [1078@5](fox-mu8/fox-mu8-xor1078-depth5.circ.txt)², [605@6](fox-mu8/fox-mu8-xor605-depth6.circ.txt), [599@7](fox-mu8/fox-mu8-xor599-depth7.circ.txt)², [539@8](fox-mu8/fox-mu8-xor539-depth8.circ.txt)², [512@9](fox-mu8/fox-mu8-xor512-depth9.circ.txt), [502@10](fox-mu8/fox-mu8-xor502-depth10.circ.txt), [500@11](fox-mu8/fox-mu8-xor500-depth11.circ.txt) | v3, v6, v7, v8 |
| [grostl](grostl/) | 1112 | 410@12 | [502@5](grostl/grostl-xor502-depth5.circ.txt), [455@8](grostl/grostl-xor455-depth8.circ.txt), [404@10](grostl/grostl-xor404-depth10.circ.txt), [364@11](grostl/grostl-xor364-depth11.circ.txt), [362@13](grostl/grostl-xor362-depth13.circ.txt), [360@14](grostl/grostl-xor360-depth14.circ.txt), [349@15](grostl/grostl-xor349-depth15.circ.txt) | v8 |
| [khazad](khazad/) | 1232 | 366@18 | [1055@5](khazad/khazad-xor1055-depth5.circ.txt)³, [478@6](khazad/khazad-xor478-depth6.circ.txt), [477@8](khazad/khazad-xor477-depth8.circ.txt), [460@9](khazad/khazad-xor460-depth9.circ.txt), [433@10](khazad/khazad-xor433-depth10.circ.txt), [432@11](khazad/khazad-xor432-depth11.circ.txt), [344@14](khazad/khazad-xor344-depth14.circ.txt), [340@15](khazad/khazad-xor340-depth15.circ.txt) | v8 |
| [whirlpool-maelstrom](whirlpool-maelstrom/) | 840 | 425@11 | [759@5](whirlpool-maelstrom/whirlpool-maelstrom-xor759-depth5.circ.txt)³, [416@6](whirlpool-maelstrom/whirlpool-maelstrom-xor416-depth6.circ.txt), [395@8](whirlpool-maelstrom/whirlpool-maelstrom-xor395-depth8.circ.txt), [391@9](whirlpool-maelstrom/whirlpool-maelstrom-xor391-depth9.circ.txt), [390@10](whirlpool-maelstrom/whirlpool-maelstrom-xor390-depth10.circ.txt) | v8 |

### MDS 8×8 over GF(2⁸)

| Map | Direct XOR | NIST | Ours (gates@depth) | Found by |
|---|---:|---|---|---|
| [bkl16-8x8-gf256](bkl16-8x8-gf256/) | 784 | 465@10 | [725@4](bkl16-8x8-gf256/bkl16-8x8-gf256-xor725-depth4.circ.txt)³, [494@5](bkl16-8x8-gf256/bkl16-8x8-gf256-xor494-depth5.circ.txt), [456@8](bkl16-8x8-gf256/bkl16-8x8-gf256-xor456-depth8.circ.txt), [439@9](bkl16-8x8-gf256/bkl16-8x8-gf256-xor439-depth9.circ.txt) | v8 |
| [jpst17-8x8-gf256-inv](jpst17-8x8-gf256-inv/) | 1152 | 528@11 | [1027@5](jpst17-8x8-gf256-inv/jpst17-8x8-gf256-inv-xor1027-depth5.circ.txt)³, [641@6](jpst17-8x8-gf256-inv/jpst17-8x8-gf256-inv-xor641-depth6.circ.txt), [494@10](jpst17-8x8-gf256-inv/jpst17-8x8-gf256-inv-xor494-depth10.circ.txt), [493@11](jpst17-8x8-gf256-inv/jpst17-8x8-gf256-inv-xor493-depth11.circ.txt), [492@12](jpst17-8x8-gf256-inv/jpst17-8x8-gf256-inv-xor492-depth12.circ.txt) | v8 |
| [klsw17-m-8x8-gf256](klsw17-m-8x8-gf256/) | 912 | 364@11 | [347@6](klsw17-m-8x8-gf256/klsw17-m-8x8-gf256-xor347-depth6.circ.txt), [346@8](klsw17-m-8x8-gf256/klsw17-m-8x8-gf256-xor346-depth8.circ.txt), [327@9](klsw17-m-8x8-gf256/klsw17-m-8x8-gf256-xor327-depth9.circ.txt), [321@10](klsw17-m-8x8-gf256/klsw17-m-8x8-gf256-xor321-depth10.circ.txt) | v8 |
| [klsw17-m-8x8-gf256-inv](klsw17-m-8x8-gf256-inv/) | 1080 | 368@12 | [868@5](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor868-depth5.circ.txt), [490@6](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor490-depth6.circ.txt), [338@11](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor338-depth11.circ.txt), [327@12](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor327-depth12.circ.txt), [326@13](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor326-depth13.circ.txt), [325@16](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor325-depth16.circ.txt), [324@21](klsw17-m-8x8-gf256-inv/klsw17-m-8x8-gf256-inv-xor324-depth21.circ.txt) | v8 |
| [ls16-8x8-gf256](ls16-8x8-gf256/) | 688 | 427@9 | [411@5](ls16-8x8-gf256/ls16-8x8-gf256-xor411-depth5.circ.txt), [403@8](ls16-8x8-gf256/ls16-8x8-gf256-xor403-depth8.circ.txt) | v8 |
| [skop15-8x8-gf256](skop15-8x8-gf256/) | 768 | 445@8 | [712@5](skop15-8x8-gf256/skop15-8x8-gf256-xor712-depth5.circ.txt), [447@6](skop15-8x8-gf256/skop15-8x8-gf256-xor447-depth6.circ.txt), [417@8](skop15-8x8-gf256/skop15-8x8-gf256-xor417-depth8.circ.txt), [416@9](skop15-8x8-gf256/skop15-8x8-gf256-xor416-depth9.circ.txt) | v8 |
| [skop15-8x8-gf256-inv](skop15-8x8-gf256-inv/) | 816 | 348@13 | [726@5](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor726-depth5.circ.txt), [408@6](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor408-depth6.circ.txt), [323@12](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor323-depth12.circ.txt), [322@13](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor322-depth13.circ.txt), [318@14](skop15-8x8-gf256-inv/skop15-8x8-gf256-inv-xor318-depth14.circ.txt) | v8 |
| [ss17-8x8-gf256](ss17-8x8-gf256/) | 680 | 418@9 | [418@5](ss17-8x8-gf256/ss17-8x8-gf256-xor418-depth5.circ.txt), [390@8](ss17-8x8-gf256/ss17-8x8-gf256-xor390-depth8.circ.txt), [389@10](ss17-8x8-gf256/ss17-8x8-gf256-xor389-depth10.circ.txt) | v8 |

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

² "+ polish": shrunk at its own depth by v8's polish (`search/linear/xorflux/engine/polish.py`);
its logs keep the original circuit (`original-circuit.txt`) and `polish.json`.

³ Built by a constructor that starts a search chain, with no search move after it:
`naive` builds balanced XOR trees; `anneal3` is the depth-3 partition annealer
(`search/linear/xorflux/moves/depth3.py`), a constructor made for depth 3 rather than part of the
general search. ⁴ Found by the search from an `anneal3` start.

⁵ Found on 2026-10-31 by a cap-6 worker that started from NIST's 107@6 (an earlier revision of
its 106@6); the chain restarted from another worker's 105@6, itself found from NIST's 106@6.
No earlier run had started from NIST's depth-5, -6 or -7 InvMixColumns circuits.

⁶ The fides-midori-mantis 24@2 circuit: the two maps have the same matrix.

⁷ Found on 2026-11-02, after 42.3 h, by the adopt side of an A/B test of proposed v9
changes, run from our 168@5 only (NIST's 119@5 was not a seed; on helper values the two
circuits are 0.83 apart). The prototype is v8 plus adopt-on-improve (a worker restarts from
a strictly better circuit of its group as soon as one is pooled), archive sampling past the
record cap, and a log-only diversity watcher; `v9-prototype.diff` in the logs applies to
v8. One worker reached 119@5 from a shared 120@5; another adopted it 4.5 s later and removed
one more gate 2.3 s after that. Both dossiers are in the logs and replay exactly. It
replaces our v4 168@5.

How long each search ran, and on what hardware: [SEARCH-TIME.md](SEARCH-TIME.md).

The maps added from NIST's repository on 2026-10-30 were searched from NIST's circuits, and
only points that no NIST circuit matches with as few gates at no more depth are kept for
them. A map with "—" has no such point yet.

Two pairs of maps have the same matrix: pride-l0 and fides-midori-mantis, and
skop15-4x4-gf16-inv and joltik. Each folder lists what was searched under its own name, except
pride-l0, whose 24@2 is the circuit found for fides-midori-mantis (⁶).
