# BoolFlux

**BoolFlux: search for small circuits of complete Boolean functions.** BoolFlux optimises
circuits for S-boxes and other functions of up to about 16 inputs over a configurable gate
library and cost model, with lexicographic objectives and hard caps on gate depth, AND depth and
AND count. It is the nonlinear sibling of XORFlux (`search/`, unchanged). Its moves can change
which AND/OR/... gates exist, what they read, and how many there are, not only the XOR layers
around a fixed AND structure. It needs Python 3.11+ (standard library only) and gcc. Nothing is
published yet. The work is on the local branch `boolflux-2026-11-13`.

| Page | What is in it |
|---|---|
| [HOW-IT-WORKS.md](HOW-IT-WORKS.md) | the method: truth tables, the gate move with care sets, feasibility-first acceptance, the skeleton level, joins, the hub (in progress) |
| [USAGE.md](USAGE.md) | every command with tested examples, targets, models, settings, output |
| [VERIFICATION.md](VERIFICATION.md) | how a result is verified, counting rules against NIST's, the pinned reference, dominance, one-command re-verification |
| [HISTORY.md](HISTORY.md) | dated history: reviews and fixes, the method study, the AES push with its failed experiments |
| [LEDGER.md](LEDGER.md) | the 2026-11-13 results with commands (sanity cases, small S-boxes, AES against pin e6ac0d0) |
| [results/MANIFEST.json](results/MANIFEST.json) | every reported circuit: sha256, metrics, start/parents, mechanism, command or run record, code version, seed, time to result, reproduction status, pinned-set status |
| [runs/](runs/README.md) | run-record convention and the index of campaign folders |
| [bench/](bench/REPORT.md) | method-and-performance study, mechanics, reproduction |
| [DESIGN.md](DESIGN.md), [CHECKPOINT.md](CHECKPOINT.md) | design notes and state of 2026-11-13 |

```bash
python3 nonlinear/boolflux/cli.py run --target maj3 --model xag --objective a,cost \
    --iters 3000 --seeds 1 --jobs 1 --out OUT/maj3                     # majority of 3: 4 gates, 1 AND
python3 nonlinear/boolflux/cli.py verify FILE.circ.txt --target aes --model nist
taskset -c 0 python3 nonlinear/boolflux/campaigns/verify_all.py        # re-verify every circuit we report
```

Run every command from the repository root.

## Results so far

AES S-box under NIST's accounting (AND, XOR, XNOR, NOT, each counted), against the 104 forward
circuits of usnistgov/Circuits at **3d80774**. Every circuit passed both verifiers.
**41 `(A, AD, G, GD)` tuples** are new on that set and not dominated by another result of ours
(`results/MANIFEST.json`, `aes_pareto`; the same 41 from `best_table.py`, `pareto_audit.py` and
`verify_all.py`, 2026-11-14). Fewest gates at a gate-depth cap, with A and AD free:

| GD <= | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 21 | 29 |
|---|---|---|---|---|---|---|---|---|---|
| published | 133 | 125 | 116 | 116 | 116 | 116 | 116 | 108 | 105 |
| BoolFlux | **129** | **121** | **115** | **113** | **112** | **110** | **108** | **107** | **104** |

Also new: circuits with 29 and 31 ANDs at GD 16-28 (every published circuit with A <= 31 has
G >= 124), A28 circuits at GD 14-25, and AD3 circuits at GD 13-25 (MANIFEST.json). The NIST
targets A < 28, G < 103 and about 110 at GD <= 14 are **not** reached. Most AES-push results come
from one-off time-budgeted runs ([HISTORY.md](HISTORY.md), MANIFEST.json `reproduction`).

Small S-boxes (23, from naive starts): each equals the best published BGC or GC value, except
Midori Sb1 BGC, which is one gate worse. None beats a published value. They are optimal where
the published value is SAT-proved ([LEDGER.md](LEDGER.md) section 2). GF(2^4) multiplication:
16 -> 9 ANDs.

## Folders

| Folder | Content |
|---|---|
| [kernel/](kernel/) | gate kernel `bfx.c`, AND-skeleton kernel `skel.c` |
| `cli.py`, `workflow.py`, `objective.py`, `core.py`, `skeleton.py`, `starts.py`, `targets.py` | CLI, time-sliced workflows, ranking, circuits and verification, skeleton synthesis, naive starts, targets |
| [models/](models/) | gate libraries and costs (`nist`, `bgc`, `gc6`, `gc`, `xag`, `xor`) |
| [independent/](independent/README.md) | the independent verifier (no shared code) |
| [campaigns/](campaigns/) | campaign scripts; `aes_check.py`, `best_table.py`, `pareto_audit.py`, `curate_aes.py`, `manifest.py`, `verify_all.py` |
| [results/](results/) | verified circuits with sidecars; `nist-format/` copies; `_superseded/` withdrawn ones |
| [benchmarks/](benchmarks/) | S-box tables with sources, literature, proof citations |
| `strategies/C,D,E,F/` | AES-push track code with NOTES (not yet committed) |
| [hub/](hub/SPEC.md) | shared-archive architecture, **in progress** |
| `review/`, `review2/`, `review3/`, `audit/` | independent reviews and audit with their scripts |
| `tests/` | regression tests |

The reference NIST circuits are in `nonlinear/nist/` ([PIN.md](../nist/PIN.md)).
