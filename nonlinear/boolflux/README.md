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
| [HOW-IT-WORKS.md](HOW-IT-WORKS.md) | the method: truth tables, the gate move with care sets, feasibility-first acceptance, the skeleton level, joins, the hub |
| [USAGE.md](USAGE.md) | every command with tested examples, targets, models, settings, output |
| [VERIFICATION.md](VERIFICATION.md) | how a result is verified, counting rules against NIST's, the pinned reference, dominance, one-command re-verification |
| [HISTORY.md](HISTORY.md) | dated history: reviews and fixes, the method study, the AES push with its failed experiments |
| [LEDGER.md](LEDGER.md) | the 2026-11-13 results with commands (sanity cases, small S-boxes, AES against the earlier pin e6ac0d0; its AES section is superseded by MANIFEST.json) |
| [results/MANIFEST.json](results/MANIFEST.json) | every reported circuit: sha256, metrics, start/parents, mechanism, command or run record, code version, seed, time to result, reproduction status, pinned-set status |
| [runs/](runs/README.md) | run-record convention and the index of campaign folders |
| [bench/](bench/REPORT.md) | method-and-performance study, mechanics, reproduction |
| [DESIGN.md](DESIGN.md) | architecture as built (kernel, Python layer, workflows, hub, campaign tools) and what was measured to work and not to work |
| [CHECKPOINT.md](CHECKPOINT.md) | state of 2026-11-13, against the earlier pin e6ac0d0 (historical) |

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
`verify_all.py`). This count is the curation of 2026-11-14 17:54 UTC, before the hub runs and
before track F's AD3 runs ended; the number, the table and the list below are **to be updated
after re-curation**. Fewest gates at a gate-depth cap, with A and AD free:

| GD <= | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 21 | 29 |
|---|---|---|---|---|---|---|---|---|---|
| published | 133 | 125 | 116 | 116 | 116 | 116 | 116 | 108 | 105 |
| BoolFlux | **129** | **121** | **115** | **113** | **112** | **110** | **108** | **107** | **104** |

Also new: circuits with 29 and 31 ANDs at GD 16-28 (every published circuit with A <= 31 has
G >= 124), A28 circuits at GD 14-25, and AD3 circuits at GD 13-25 (MANIFEST.json). The NIST
targets A < 28, G < 103 and about 110 at GD <= 14 are **not** reached.

How to read these results:

- No AND count below a family's published minimum was reached. The A28 results are published
  A28 circuits re-timed by the gate kernel (same ANDs per level). The A29 results are A28
  circuits in which a depth repair ended one AND above its cap. The A31 results are joins of two
  A32 circuits (`strategies/L2/WHAT-WORKED-BEFORE.md`).
- Every A28 and A29 result of the AES push is a one-off time-budgeted kernel job that was never
  repeated. The joins are deterministic and were re-run with identical output on 2026-11-15
  (30 of 30). 28/4/133/20 has an iteration-budgeted command. Re-run on 2026-11-15, it gives the
  identical gate list with the binary kept in its run folder, and with today's code when
  `--set skip_noop=0` is added; with today's defaults the same command stays at 134
  ([VERIFICATION.md](VERIFICATION.md) section 6, MANIFEST.json `reproduction`).

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
| `strategies/C,D,E,F,G/` | AES-push track code with notes (`NOTES.md`; track D: `README.md`), committed in 377b03f |
| `strategies/H1-H4, R1-R2, T1-T4, X1-X3, L1, L2/` | 2026-11-15 study: structure and algebra (H), window redesigns (R), goal-directed runs (T, X), log analysis (L1: hub era, L2: before the hub and the documentation audit) |
| [hub/](hub/SPEC.md) | shared archive, operators and scheduler (built 2026-11-14; what was measured is in [DESIGN.md](DESIGN.md)) |
| `review/`, `review2/`, `review3/`, `review4/`, `audit/` | independent reviews and audit with their scripts |
| `tests/` | regression tests |

The reference NIST circuits are in `nonlinear/nist/` ([PIN.md](../nist/PIN.md)).
