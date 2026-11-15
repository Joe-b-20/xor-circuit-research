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
**73 `(A, AD, G, GD)` tuples** are new on that set and not dominated by another result of ours
(`results/MANIFEST.json`, `aes_pareto`; the same 73 from `verify_all.py`). This is the curation
of 2026-11-15 06:53 UTC (commit cb8fd56). It added the hub runs, track F's last AD3 runs and the
study phase: MANIFEST.json now has 194 entries (142 of them AES), all verified.
[results/BEST.md](results/BEST.md) is the curated table: one row per tuple, with the published
best within the same caps. It has 29/4/130/22 where MANIFEST.json and `verify_all.py` have
29/4/129/22, a hub circuit curated after BEST.md was written ([DOCS-TODO.md](DOCS-TODO.md)
item 27). Fewest gates at a gate-depth cap, with A and AD free (BEST.md):

| GD <= | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 29 |
|---|---|---|---|---|---|---|---|---|---|---|
| published | 133 | 125 | 116 | 116 | 116 | 116 | 116 | 108 | 108 | 105 |
| BoolFlux | **129** | **121** | **115** | **112** | **112** | **110** | **108** | **107** | **107** | **104** |

Also new (BEST.md): circuits with 29-31 ANDs at GD 15-28 (every published circuit with
29 <= A <= 31 has G >= 137), A28 circuits at GD 14-25, AD3 circuits at GD 13-25, and A42-A48
circuits at GD 11-12, where no published circuit exists within the same caps. The NIST targets
A < 28, G < 103 and about 110 at GD <= 14 are **not** reached.

**2026-11-15 study phase** (00:10-06:45 UTC; 15 study agents and the review-5 agents, see
[HISTORY.md](HISTORY.md)). No circuit with 27 ANDs was found. Every exhaustive "no 27" result of
the phase holds only in its stated case (a fixed stage-1 span or prefix, a fixed pool of
last-layer products, one gamma). None is a general bound. The only general lower bound is 13
ANDs [P] (`strategies/H1/NOTES.md` sections 4 and 9, `strategies/X3/NOTES.md` section 8). Found:

- new A28 frontier points 28/4/131/22 and 28/4/132/20 (T1), 28/4/133/19, 28/5/126/24 and
  28/5/136/17 (R1; 126/24 also by T1, 136/17 also by the hub), and 28/5/133/18, a hub join from
  the long run of 2026-11-14 that entered the manifest at this curation
  (`strategies/T1/NOTES.md` section 5, `strategies/R1/NOTES.md` summary);
- a new A28 AND structure, **9 + 5 + 14** (9 stage-1 ANDs, a 5-AND inversion, 14 last-layer
  ANDs; the published A28 families are 10 + 5 + 13 and 9 + 6 + 13). X1b reached it with a walk from
  NIST a28-ad5-g128-gd20 (28/5/158/27). H2's exact layer search found 69 such last layers over the
  stage-1 span of NIST a28-ad4-g131, and 69 each over those of g141 and g176. Its lowest G so far
  is 156 (28/5/156/28), so it is not on the frontier. In 25 built 9 + 5 + 14 circuits, with each
  one's prefix fixed, neither dropping one last-layer member nor replacing two or three of them by
  one fewer gives 13 [C, that case] (`strategies/X1/NOTES.md` section 8,
  `strategies/H2/NOTES.md` sections 5.6 and 5.8, `strategies/H1/NOTES.md` section 9);
- a GD-11 staircase down to 42 ANDs: 47/4/186/11, 46/4/203/11, 44/4/254/11, 43/4/278/11 and
  42/4/284/11, plus 42/4/230/12. The bottom products are rank-2 products whose junk is shared
  between outputs. Before, ours was 48/4/151/11 and the published 49/4/148/11. The goal G <= 140 at
  A <= 44 was not reached (`strategies/T4/NOTES.md`);
- AND depth 3: 35/3/142/19 and 35/3/143/18, from GF(4)-coordinate moves at level 3 and level-1
  product exchanges, replacing 144@20, 145@19 and 146@18 (`strategies/T3/NOTES.md` sections 11, 15
  and 16).

How to read these results:

- No circuit has fewer than 28 ANDs. The A28 results of the AES push are published A28 circuits
  re-timed by the gate kernel (same ANDs per level). In the hub, all 230 archived A28 circuits lie
  in the 6 AND spans of the NIST seeds (`strategies/L1/WHAT-WORKS.md` finding 4). The A29 and A30
  results are A28 and A29 circuits in which a depth repair or pull ended one AND above its cap
  (L1 finding 5). The A31 results of the AES push are joins of two A32 circuits
  (`strategies/L2/WHAT-WORKED-BEFORE.md`).
- Of the 79 manifest entries behind the 73 tuples, 72 are one-off time-budgeted jobs (every hub
  and study result among them) that were not repeated, 4 are deterministic joins and 3 are
  deterministic commands (MANIFEST.json `reproducibility`). Track E's 30 recorded joins were re-run
  with identical output on 2026-11-15. 28/4/133/20 (now dominated by 28/4/133/19 and 28/4/132/20)
  has an iteration-budgeted command. Re-run on 2026-11-15, it gives the identical gate list with
  the binary kept in its run folder, and with today's code when `--set skip_noop=0` is added; with
  today's defaults the same command stays at 134 ([VERIFICATION.md](VERIFICATION.md) section 6,
  MANIFEST.json `reproduction`).

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
| `review/`, `review2/`, `review3/`, `review4/`, `review5/`, `audit/` | independent reviews and audit with their scripts |
| `tests/` | regression tests |

The reference NIST circuits are in `nonlinear/nist/` ([PIN.md](../nist/PIN.md)).
