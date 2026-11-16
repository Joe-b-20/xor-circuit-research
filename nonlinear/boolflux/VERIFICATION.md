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

For the targeted campaigns of 2026-11-15/16 (section 7):

```bash
python3 nonlinear/boolflux/campaigns/targets/ledger.py run      # verify, classify, compare, audit; seconds with a warm cache
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/*/*.circ.txt
bash nonlinear/boolflux/campaigns/targets/morning.sh              # ledger, curation, manifest, BEST.md, verify_all, tests (USAGE.md)
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

Run on 2026-11-15 at 06:57 UTC, during the re-curation (150 s; log
`~/xs-campaigns/2026-11-15-study/best/verify_all.log`):

| group | checked | passed | failed |
|---|---:|---:|---:|
| results | 194 | 194 | 0 (manifest sha256: 138 match, 56 not yet in the manifest, see below) |
| nist-format | 124 | 124 | 0 (boolcirc: 124 files, 0 failing) |
| campaigns | 244 | 244 | 0 (227 of them new on the pinned set, per file; root `~/xs-campaigns/2026-11-13-aes`) |
| nist pin 3d80774 | 207 files | sha256 all match | boolcirc: 204 circuit files, 0 failing; forward set 104 circuits, 92 distinct tuples |

That run found **186 distinct AES tuples of ours, 139 of them not dominated by the pinned set,
and 73 of those not dominated by another circuit of ours**. The `aes_pareto` field of
MANIFEST.json lists the same 73. [results/BEST.md](results/BEST.md) was regenerated in 8922cac
with the overnight hub archive included, so it has rows that are not in the manifest yet
([DOCS-TODO.md](DOCS-TODO.md) item 27). The
hub's and the study agents' circuits are counted through `results/aes`, where the re-curation put
them; their campaign folders are not among the default `campaigns` roots.

The run came between two `manifest.py` runs. The first (06:54 UTC) stopped with a TypeError on
an entry without a start file, before writing the manifest. That is why 56 of the 194 result
files were not in the manifest yet and `nist-format` had 124 files. The second (06:59 UTC) wrote
the committed MANIFEST.json: 194 entries, 0 failing verification, and the boolcirc check of
`results/nist-format/` passed on 142 circuit files with 0 failing (`best/manifest2.log`).
`verify_all.py` was rerun on that final manifest at about 07:30 UTC (commit message of 8922cac):
194 of 194 manifest sha256 match, 142 nist-format files OK, all groups OK.

The previous run (2026-11-14 18:07 UTC, before the hub and the study phase) checked 138 results,
86 nist-format files and 237 campaign circuits and found 130 / 83 / 41 tuples. Campaign folders
that are still being written change the `campaigns` counts.

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
  - *deterministic command*: every job ended on its iteration budget, so the run is
    deterministic for its seed, settings and code. (Corrected 2026-11-15.) These 47 entries
    are runs of 2026-11-13 (code b0e56ecb18fe for all but one of the 49 entries of this kind and
    the next), before the no-op filter became the default (7ae20c8). With later
    code the recorded command needs `--set skip_noop=0`, or the `src/` and `bin/` snapshot of
    the run folder. Checked on 28/4/133/20 (seed 5, 100,000 iterations; outputs in
    `~/xs-campaigns/2026-11-15-study/L2/det_old`, `det3`, `det1`): the run's own binary gives
    the byte-identical circuit; code f9fe6f7 with `--set skip_noop=0` gives the identical gate
    list (133 at iteration 56,529); code f9fe6f7 with the default settings ends at 134 with no
    improvement. The other 46 entries were not re-run.
  - *reproduced*: re-run from scratch, with an identical gate list. This holds for two results.
    Also on 2026-11-14, with `--iters 20000 --seeds 7 --set skip_noop=0`, the current code
    re-ran `a32-ad5-g109-gd20 -> 108` bit for bit.
  - *deterministic construction* (track E joins). The entries say "not re-run"; on 2026-11-15
    the first A31 join and all 29 join admissions of the long1 and low1 runs were rebuilt from
    their recorded parents and cut levels and are identical (`strategies/L2/rejoin.py`).
  - *one-off*: a time-budgeted run, verified but not bit-reproducible. Every A28 and A29 result
    of the AES push is of this kind and none was repeated.

The curated AES-push circuits keep their campaign sidecar as `*.campaign.json`. The
`strategies/` code was not committed when they were curated, so `code_version` records the
sha256 of the strategy scripts as they were at curation (17:54 UTC), not at run time, and the
commit of the kernel copy they ran. The scripts were committed 14 minutes later in 377b03f.
(Re-curated 2026-11-15.) Since review 5 (P23) each such entry says so in
`code_version_recorded`, and `code_version_commit_check` compares every curation-time hash with
the file in 377b03f: 37 entries, 124 script hashes, all "identical to commit 377b03f". The 36 hub
entries carry the hub's run-time code version (git commit plus a hash of uncommitted changes).

Known gaps in the provenance records, from the audit of 2026-11-15
(`strategies/L2/DOC-AUDIT.md`, `strategies/L2/WHAT-WORKED-BEFORE.md` section 4):

- Two entries are circuits that do not meet the A cap of the job that made them:
  `aes-nist-E-polish-g104-a32-gd29-ad5` (job cap A31, circuit A32) and
  `aes-nist-E-pull-g135-a29-gd17-ad5` (job cap A28, circuit A29). Both circuits are correct and
  verified; they are the kernel's best infeasible state. (Re-curated 2026-11-15.) Review 5 (P22)
  added `caps_met` to every entry and a "CAPS NOT MET by this job" sentence to the mechanism.
  Seven entries now have `caps_met: false`: these two and five hub pulls (32/5/115/17,
  30/4/130/20, 29/4/132/19, 35/3/141/24, 29/4/146/15).
- The 10 polish entries of track E's long1 run have no time within the job
  (`time_to_result_s.within_job_s` is null) and no caps in their lineage records.
- In track E's memetic driver the kernel seed of a job is the pool member's polish counter
  (1, 2, ...), so a seed is meaningful only together with the start circuit's hash.
- `aes-nist-main-flow-g175-a28-gd14-ad4` records a result time of 960 s in a 900 s job; two
  track F entries give their seed as "see cmd"; track F's kernel is named by a hash prefix.
- Track D's window statistics cannot be rebuilt in full: the surviving logs hold 3,062 windows.
- Time-budgeted jobs ran on CPUs of probably different speed (CPUs 12-19 of the machine are
  likely efficiency cores), and the memetic polishes did not record iteration counts.

```bash
taskset -c 0 python3 nonlinear/boolflux/campaigns/curate_aes.py --dry-run   # what would be added to results/aes
taskset -c 0 python3 nonlinear/boolflux/campaigns/curate_aes.py             # add new Pareto points with sidecars
taskset -c 0 python3 nonlinear/boolflux/campaigns/manifest.py               # MANIFEST.json + nist-format/ + boolcirc check
```

Results that are found to be wrong, or that were made for a wrong target, move to
`results/_superseded/` with a note in its README. Results that are only dominated stay in
`results/<target>/`, and their manifest entries say what dominates them.

## 7. Targeted campaigns (2026-11-15/16)

The ten targeted campaigns ([results/targets/TARGETS.md](results/targets/TARGETS.md)) use the
same verifiers and the same pinned set, and add a ledger that classifies every circuit against
its target. The ledger is [`campaigns/targets/ledger.py`](campaigns/targets/ledger.py); what it
does in detail is in [campaigns/targets/README.md](campaigns/targets/README.md). It does no search.

**What is checked.** Every circuit file in every campaign `found/` folder
(`~/xs-campaigns/2026-11-15-targets/<agent>/found/**`) and in the archive (best-1400, the hub
archive, `results/aes/`, the study `found/` folders) goes through `aes_check.check`: `core` and
`independent/verify.py` on all 256 inputs, the two metric computations equal, gates in {AND,
XOR, XNOR, NOT}, NIST counting (section 3). Results are cached by the sha256 of the file bytes;
the cache is dropped when any verifier file changes. Each campaign circuit also carries the
`aes_check` OK line its agent recorded when saving it. Ledger of 2026-11-15 23:17 UTC: 4,162
archive and 398 campaign files, 4,560 verified, 0 failing. Morning ledger (2026-11-16 13:19 UTC, code d9507dd): 4,162 archive and 614 campaign files (11-15 agents, phase-2 agents and the night's `found/` folders), 4,776 verified, 0 failing; issues 0 FAIL, 2 WARN, 3 NOTE.

**How a circuit is classified** (per target, from TARGETS.json on every run, so a threshold the
user changes takes effect on the next run):

| class | condition (always inside the hard limits A <= ref A, AD <= ref AD) |
|---|---|
| strict | G <= ref G and GD <= ref GD, one strictly smaller |
| tradeoff `gates_for_depth` | ref GD < GD <= GD_max and G <= ref G - 3 |
| tradeoff `depth_for_gates` | GD <= GD_max < ref GD and ref G < G <= ref G + 8 |
| tradeoff `and_depth_for_gates` (T05) | AD < ref AD, AD <= max(AD targets), G or GD above the reference |
| other | anything else inside the limits; kept if it is on a frontier |

A tradeoff that some strict circuit dominates is dropped from the tradeoff lists, and no
tradeoff is called dominating. Per target the ledger keeps the (G, GD) Pareto frontier, the
(A, AD, G, GD) Pareto frontier, and the strict and tradeoff Pareto sets; for T05 also the best G
and the best GD per AND depth 7..1. The rules of 2026-11-15 23:50 UTC enter through
TARGETS.json: T03 `gates_for_depth` with GD_max 22 (so 20 < GD <= 22 and G <= 125), and T05
`gates_for_depth` with GD_max 999 (any GD above 32 with G <= 100, since the gain threshold is 3
gates). The user's "any G <= 123" (T03) and "any G <= 102" (T05) are separate **notable** lines
at any GD inside the hard limits, so a T05 circuit with 101 or 102 gates at GD > 32 is notable
(a new overall gate record) without being a tradeoff in the ledger's sense. A circuit that
matches several tradeoff kinds is listed under `gates_for_depth`.
(Checked on 2026-11-16 against `ledger.py` sha256 be594f85360b..., `classify()`: the conditions above, gates_for_depth before depth_for_gates before and_depth_for_gates, thresholds from TARGETS.json; a tradeoff is dropped when a strict point dominates it in (G, GD), for the AND-depth kind in (AD, G, GD); T05's per-AD best G / best GD for AD 7..1.)

**Comparison with the pinned set.** Each listed point is compared with its reference and with
every forward AES S-box circuit of the pin (`aes_check.published()`, section 4): the ledger names
the pinned circuits that dominate it (all four metrics <=, tuple different) and those with an
equal tuple, and gives the pinned (G, GD) frontier inside the same hard limits. On every run it
also checks the sha256 of all 207 pinned files against `nonlinear/nist/MANIFEST.json`.

**Provenance.** The baseline is every archive file with mtime (hub: admission time) at or
before 2026-11-15 15:20 UTC, frozen in `~/xs-campaigns/2026-11-15-targets/L0/baseline/` with
sha256, tuple and structural key (`hub.common.structure_key`: the circuit as a DAG, invariant
under gate order and the operand order of symmetric gates). *Known*: the tuple is realised by a
baseline file. *Reproduced*: a campaign circuit structurally equal to, or with the tuple of, a
baseline circuit. *New*: neither. From phase 2 (L1, 2026-11-16) a second snapshot,
`L0/baseline/known-by-2350.json` (every archive and campaign `found/` file with mtime at or
before 2026-11-15 23:50 UTC: 4,562 files, 400 of them campaign files), splits "new" by era: a
point is `known` (the 15:20 archive), `known-by-23:50 (<agent>; new vs archive)` (a result of the
2026-11-15 campaign day) or `new (<group>)` (the night runs); LEDGER.json field `era` =
archive / campaign-11-15 / new. In the morning ledger the results of 2026-11-15 therefore show
as `known-by-23:50`; they are still new against the archive and the pin. "New" and "dominated"
are [C] relative to the scanned folders and the pinned set only; they say nothing about
unpublished or other published work.

**Sidecars.** Every campaign circuit has a JSON sidecar (`campaigns/targets/SIDECAR-TEMPLATE.json`)
with target, A AD G GD, start (path and sha256), method, exact command, seed, elapsed time, code
(git sha and kernel binary sha256), the aes_check line and the time. The ledger reports FAIL when
a file fails verification, the sidecar's tuple differs from the verified one, or the target's
hard limits are broken; WARN for a missing sidecar or field, or a start file that is missing or
has another sha256. The sidecar's free-text `method` is not checked against the `command`; in
at least one P6 sidecar (35/3/138/24) the two disagree, and the command is the right one.

**Search-path certification (2026-11-15 18:20-23:50 UTC).** While the user's rule covered
retained search states, each sidecar also carried `path_certified` (true when no kernel stage
of its lineage started above a cap without `repair_keep 1`, or a traced replay showed every
accepted state inside A/AD), and the ledger propagated it along lineages and `reproduces` links,
flagged kernel stages that started above a cap, and handled construction donors outside the
limits (the donor ruling, [results/targets/COMPLIANCE-1820.md](results/targets/COMPLIANCE-1820.md)).
At 23:17 UTC every new strict and tradeoff point had a certified campaign file. Since 23:50 UTC
certification is informational and does not decide whether a result counts
([results/targets/TARGETS.md](results/targets/TARGETS.md) section 2.1).

**Curation.** `ledger.py curate` (dry run) and `curate --apply` copy every campaign circuit on a
target's strict, tradeoff or (G, GD) frontier list that is not "known" into
`results/targets/<ID>/`, under the name `aes-sbox-a<A>-ad<AD>-g<G>-gd<GD>-<ID>-<agent>-<k>`, with
its sidecar and `logs/<name>/` (`found.json`, `aes_check.json`, `REPRODUCE.md`). One circuit can
be copied under several targets (28/4/174/14 is within the limits of T01-T05); its class for each
target is in LEDGER.md. Each curated sidecar gets the class of its folder's target (`class`,
`class_kind`, `class_target`, `class_rule`, and `notable` for T03 / T05); a different class the
agent wrote stays as `class_agent`. A source circuit already curated for a target is not copied
again. `morning.sh` then curates the same circuits into `results/aes/` and MANIFEST.json
(`aes-nist-targets-<agent>-t<NN>-...`, caps = the target's A and AD). At the 23:17 UTC state they
are not yet in `results/MANIFEST.json`.
Morning run 2026-11-16 13:23 UTC: all steps OK, 199 s in total (log `~/xs-campaigns/2026-11-15-targets/L1/morning-20261116T131944Z/`). `ledger.py curate --apply`: 28 files planned (6 replace an entry of the same tuple); refreshed 57 curated entries (sidecar class fields and corrections, circuit header, logs); 0 failed verification. `curate_aes.py`: 74 Pareto tuples (best_table rule), 37 already in results/aes, 53 circuits to add; circuits written 53. `manifest.py`: 247 entries, 0 failing verification; nist-format check: 195 circuit file(s), 0 failing. BEST.md vs MANIFEST.json: BEST.md rows 74, MANIFEST aes_pareto 74, MANIFEST AES entries 170 tuples.

**Reproduction** of the target results uses the vocabulary of section 6; every new result is a
one-off time-budgeted run, with the exceptions listed in TARGETS.md section 8 (exact traced
replays of four P3 kernel stages, deterministic constructions of P6 and P7, tuples reproduced by
independent lineages).
