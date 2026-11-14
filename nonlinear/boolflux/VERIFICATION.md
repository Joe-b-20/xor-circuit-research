# How a BoolFlux result is verified

A circuit counts as a result only after it has been evaluated on every input by two programs
that share no code, both have agreed on every metric, and its place against NIST's published
circuits has been computed from those metrics, not from file names. This page explains each
step and how to repeat all of them with one command.

## One command

```bash
taskset -c 0 python3 nonlinear/boolflux/campaigns/verify_all.py            # about 70 s on one CPU
taskset -c 0 python3 nonlinear/boolflux/campaigns/verify_all.py --json OUT.json --no-campaigns
```

[`campaigns/verify_all.py`](campaigns/verify_all.py) checks four groups and prints one summary
table. It exits with status 1 if anything fails. It writes only a temporary folder and the
optional JSON file.

| group | what is checked |
|---|---|
| `results` | every `results/<target>/*.circ.txt` with `cli.verify_file`, under the target, model and caps in its `.summary.json`, plus its sha256 against [results/MANIFEST.json](results/MANIFEST.json) |
| `nist-format` | every `results/nist-format/*.circ.txt` (AES copies with explicit NOT gates) with `aes_check.check`, and the whole folder with `nonlinear/check.py` |
| `campaigns` | every circuit in `~/xs-campaigns/2026-11-13-aes/*/found/**`, `best/`, `main/**/best.circ.txt` and track E's `admitted/` pools (`--campaigns DIR ...` for other folders, `--no-campaigns` to skip). Kernel `.bfx` files are converted in the temporary folder. Campaign folders are only read |
| `nist` | the pinned reference: sha256 of every file against `nonlinear/nist/MANIFEST.json`, and `nonlinear/check.py nonlinear/nist` |

At the end it lists the AES `(A, AD, G, GD)` tuples of ours that no pinned circuit dominates,
and the subset that no other circuit of ours strictly dominates.

Run on 2026-11-14 at 18:07 UTC (CPU 0, 72 s):

| group | checked | passed | failed |
|---|---:|---:|---:|
| results | 138 | 138 | 0 (manifest sha256: 138 match) |
| nist-format | 86 | 86 | 0 (boolcirc: 86 files, 0 failing) |
| campaigns | 237 | 237 | 0 (220 of them new on the pinned set) |
| nist pin 3d80774 | 207 files | sha256 all match | boolcirc: 204 circuit files, 0 failing |

That run found 130 distinct AES tuples of ours, 83 of them not dominated by the pinned set, and
41 of those not dominated by another circuit of ours. `best_table.py`, `pareto_audit.py` and the
`aes_pareto` field of MANIFEST.json gave the same 41. Campaign folders that are still being
written change the `campaigns` counts.

## 1. Inside the search

- The gate kernel ([kernel/bfx.c](kernel/bfx.c)) keeps the complete truth table of every signal
  (`2^n` bits; 4 machine words for an 8-bit S-box). Every candidate replacement is checked on all
  inputs before it can be accepted: the new signal must equal the old one on the old signal's
  care set (the inputs where it can change an output). The kernel also re-simulates the whole
  circuit against the start circuit's function, and it aborts if any output differs. This is a
  guard against kernel bugs. It is not counted as one of the two verifiers.
- The skeleton kernel ([kernel/skel.c](kernel/skel.c)) accepts an AND-skeleton move only if
  Gaussian elimination over the complete truth tables shows that every output is still in the
  span.

## 2. The two verifiers

Every saved circuit passes `cli.verify_file`
([cli.py](cli.py), `verify_file`, called by `run`, `pipe`, `flow`, `verify` and
`campaigns/manifest.py`):

| | `core` ([core.py](core.py)) | `independent/verify.py` ([independent/](independent/README.md)) |
|---|---|---|
| evaluation | bitsliced: one big integer per signal over all `2^n` inputs | one input at a time, gates on Python ints 0/1 |
| AES table | `targets.aes_sbox()`: inversion in GF(2^8) mod 0x11B, then the affine map with 0x63 | its own FIPS-197 code, self-checked (S(00)=63 ...) and checked for being a permutation |
| other targets | `targets.py` and `benchmarks/sboxes.json` | reads the same spec table file itself (`--table`), or a `.fn.json` written from `targets.py` for the built-in functions (maj3, fulladd, gf16-mul, gf16-inv) |
| parsing | `read_ncff` | its own parser: single assignment, operands defined earlier, inputs never assigned, every output assigned |
| metrics | G, A, GD, AD, cost, counts by type | the same, computed separately |
| also | | library check against the model's gate list, caps (`--max-GD/AD/A`) |

A circuit passes when both programs accept the function, every gate type is in the model's
library, the caps hold, and G, A, GD, AD, cost and the per-type counts are equal in both. If
the metrics differ, `independent_ok` is set to false.

The independent verifier was written from a specification and imports nothing from
`nonlinear/boolcirc`, `nonlinear/boolflux` or `search/` ([independent/README.md](independent/README.md)).
Its 36 unit tests pass (`python3 -m unittest discover -s nonlinear/boolflux/independent`, 6 s).

AES circuits have two more checks:

- **boolcirc** (`nonlinear/check.py`) is a third implementation. It verifies the NIST-format
  copy of each AES result in [results/nist-format/](results/nist-format/), twice: from the gate
  list and from the AND skeleton, under both bit orders. It also recomputes the metrics written
  in the NIST-style file name. `campaigns/manifest.py` runs it on every manifest run.
- **audit/audit.py** is a fourth evaluator with its own counter. It was written for the
  independent audit of 2026-11-13 ([audit/AUDIT.md](audit/AUDIT.md)). It covers the result set of
  that day only. It was not re-run on the AES-push results.

## 3. Gate library and counting rules (NIST model)

The AES results use the model `nist` ([models/nist.json](models/nist.json)), which counts the
way NIST's collection does (`nonlinear/nist/aes-sbox/NIST-README.md`):

| rule | BoolFlux `nist` | NIST collection |
|---|---|---|
| gate library | AND, XOR, XNOR, NOT, each cost 1 | AND, XOR, XNOR, and NOT in 2 of the 104 forward circuits |
| G | every gate, NOT included | every gate, NOT included (`XXN = XX + #NOT`) |
| A | AND gates | #AND |
| GD | longest input-to-output path, inputs at 0, every gate +1 (NOT too) | gate depth |
| AD | most AND gates on any path | AND depth |
| NOT | written `XNOR t a 0` in our files: one gate, one level, listed as XNOR. The NIST-format copies write it as `NOT` and use NIST's `-xxnX-Y-Z` names | `NOT` |
| BUF | `BUF y x` is written when an output equals an input or another output. It is free, has depth 0 and is excluded from G in every counter. `verify_file` drops BUF from the counts it compares (review 3, M5). No result in `results/` has a BUF line | not used |
| inversions | no free inverted inputs or outputs, no OR/NAND/NOR in `nist` | none |
| bit order | msb/msb: input `x0` is the most significant bit of the input byte, output `y0` the most significant bit of the output | msb/msb (`nonlinear/nist/MANIFEST.json`, `bit_order`) |

Other models (`bgc`, `gc6`, `gc`, `xag`, `xor`) are in [models/](models/). The small-S-box tables
keep BGC and GC separate, because they are different libraries ([LEDGER.md](LEDGER.md), section 2).

## 4. The pinned reference

`nonlinear/nist/` is a verbatim copy of usnistgov/Circuits `data/slp/aes` at commit
**3d807741f937d29d3bef4f32f142ccda0cda9070** ([../nist/PIN.md](../nist/PIN.md),
[../nist/MANIFEST.json](../nist/MANIFEST.json): 207 files, each with its sha256 and its upstream
URL). On 2026-11-14 upstream HEAD was this commit. `nonlinear/nist/refresh.py` re-checks the pin
and re-pins it (`--repin`). The earlier pins were 0876577 and e6ac0d0 ([HISTORY.md](HISTORY.md)).

The **published set** used for dominance is every forward AES S-box circuit in the pin:
`aes-sbox/*.circ.txt` (80), `sbox/aes-sbox-fwd-*` (21) and `old-2020/aes-sbox-fwd-*.slp` (3). That
makes 104 circuits with 92 distinct `(A, AD, G, GD)` tuples. Their metrics come from the
independent verifier, not from the file names, and each must compute the AES S-box
(`aes_check.published()` asserts it). `aes-invsbox/` and `aes-sbox-sel/` (a 9-to-8-bit function
that selects the forward or inverse S-box) are other functions and are not compared.

## 5. Dominance

All comparisons are on `(A, AD, G, GD)`, where lower is better in every coordinate.

- **[campaigns/aes_check.py](campaigns/aes_check.py)** `FILE ...` runs both verifiers with the
  NIST library. It then lists `dominated_by`, the published circuits with all four metrics `<=`.
  Equality counts as dominated, so a circuit equal to a published one is not new. `new_point`
  means that list is empty. It also prints the published best G at the circuit's GD cap, at its A
  cap, at its (A, GD) caps and at its (A, AD, GD) caps, with the gain.
- **[campaigns/best_table.py](campaigns/best_table.py)** `[--out DIR] [--md FILE]` collects the
  candidates: `results/aes`, each track's `found/`, `main/**/best.circ.txt`, and track E's
  admitted pools. For each tuple it keeps the first circuit, and it keeps a tuple when no
  published circuit dominates it and no other candidate strictly dominates it. It re-verifies
  every survivor, copies it to DIR under a NIST-style name, and prints NIST-style tables. By
  default DIR is `~/xs-campaigns/2026-11-13-aes/best`. Pass `--out` to write somewhere else.
- **[campaigns/pareto_audit.py](campaigns/pareto_audit.py)** `[--json OUT]` applies the same rule
  to `results/aes` alone. It reports every result, the published circuits that dominate it and
  ours that dominate it, and the smallest G at each gate-depth cap.
- **[campaigns/manifest.py](campaigns/manifest.py)** writes the same status into each AES entry
  of MANIFEST.json (`pinned_set`: `new_point`, `dominated_by`, `superseded_by_ours`, the
  published best at the same caps). The top-level `aes_pareto` lists the surviving tuples.

A claim such as "fewest gates at GD <= 14" means that the smallest G among our verified circuits
with GD <= 14 is below the smallest G among the 104 published ones with GD <= 14, with A and AD
free.

## 6. Provenance of a result

[results/MANIFEST.json](results/MANIFEST.json) has one entry per result file: sha256, target and
its definition, model with gates and costs, objective, caps, start (for a NIST start: the
earliest pin it was taken from and whether it is byte-identical at 3d80774), command, seeds,
iterations, rounds, code hash, wall time, metrics, the verifier verdicts, and:

- `mechanism`, `parents` (the full lineage for track E's pool circuits, up to NIST or BoolFlux
  input files), `time_to_result_s`, `run_record` and `code_version`;
- `reproduction`, which takes one of these values:
  - *deterministic command*: every job ended on its iteration budget, so re-running the command
    gives the same circuit.
  - *reproduced*: re-run from scratch, with an identical gate list. This holds for two results.
    Also on 2026-11-14, with `--iters 20000 --seeds 7 --set skip_noop=0`, the current code
    re-ran `a32-ad5-g109-gd20 -> 108` bit for bit.
  - *deterministic construction* (track E joins).
  - *one-off*: a time-budgeted run, verified but not bit-reproducible.

The curated AES-push circuits keep their campaign sidecar as `*.campaign.json`. The
`strategies/` code was not committed when they were curated, so `code_version` records the
sha256 of the strategy scripts as they were at curation, and the commit of the kernel copy
they ran.

```bash
taskset -c 0 python3 nonlinear/boolflux/campaigns/curate_aes.py --dry-run   # what would be added to results/aes
taskset -c 0 python3 nonlinear/boolflux/campaigns/curate_aes.py             # add new Pareto points with sidecars
taskset -c 0 python3 nonlinear/boolflux/campaigns/manifest.py               # MANIFEST.json + nist-format/ + boolcirc check
```

Results that are found to be wrong, or that were made for a wrong target, move to
`results/_superseded/` with a note in its README. Results that are only dominated stay in
`results/<target>/`, and their manifest entries say what dominates them.
