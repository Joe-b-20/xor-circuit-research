# Target-campaign ledger (campaign 2026-11-15-targets)

`ledger.py` keeps the result book of the ten targeted campaigns against NIST AES S-box circuits
(T01..T10, `~/xs-campaigns/2026-11-15-targets/TARGETS.json`) and of the 27-AND agent (Z).
It does no search.

```bash
cd ~/xcr-boolflux
python3 nonlinear/boolflux/campaigns/targets/ledger.py baseline   # once; refuses to overwrite (--force)
python3 nonlinear/boolflux/campaigns/targets/ledger.py run        # any time; idempotent
~/xs-campaigns/2026-11-15-targets/L0/run_ledger.sh run             # the same on CPU 1 under xsfg, with a log
python3 nonlinear/boolflux/campaigns/targets/ledger.py curate     # plan: new campaign points -> results/targets/<ID>/
python3 nonlinear/boolflux/campaigns/targets/ledger.py curate --apply   # copy them (circuit, sidecar, logs/<name>/)
```

`curate` reads the last LEDGER.json and copies every campaign circuit on a target's strict,
tradeoff, notable or (G, GD) frontier list that the 15:20 archive does not realise (era
`campaign-11-15` or `new`; bfx written as NCFF), with its sidecar, `logs/<name>/found.json`,
`aes_check.json` and a filled `REPRODUCE.md`. A source circuit already curated for that target
(same sha256) is not copied again. The file copied for a tuple is the ledger's representative:
among the campaign files of the tuple, one with a certified search path wins the tie, then the
earliest (coordinator 2026-11-16, DOCS-TODO 32.1); a curated entry of the same tuple from another
file is replaced (found.json `replaces`; git history keeps the old files).
`--apply` then refreshes every curated entry (idempotent):
- sidecar `results/targets/<ID>/*.json`: corrections from `corrections.json` (curated copy only;
  the replaced value is kept as `<field>_original`; the agents' files are never changed), and the
  class fields of the folder's target: `class` (strict / tradeoff / other), `class_kind` (the
  tradeoff kind or null), `class_target`, `notable` (T03, T05) and `class_rule`; a different class
  written by the agent is kept as `class_agent`;
- circuit: header comments `Not a NIST-issued circuit` / `Found by` / `Started from` / `Logs`
  (comments only; the file is re-verified with aes_check before it replaces the old one);
- `logs/<name>/`: `start.circ.txt` (the start, copied when it is not a file of this repository;
  .bfx converted to NCFF; verified), `command.sh` (the recorded command, repository paths as
  `$REPO`, other paths `$HOME/...`), `REPRODUCE.md` (repository-relative paths, a reproduction
  statement), `aes_check.json`, `found.json` (current ledger status, class, start record).

### Phase 2 (2026-11-16, L1)

```bash
python3 nonlinear/boolflux/campaigns/targets/ledger.py snapshot   # once: "known-by-23:50" (built 23:56 UTC)
bash nonlinear/boolflux/campaigns/targets/morning.sh              # 13:30-14:00 UTC: ledger, curate, record, manifest, BEST.md, verify, tests
bash nonlinear/boolflux/campaigns/targets/morning.sh --dry-run    # the same on a copy of the worktree (nothing here changes)
```

- Night runs: `~/xs-campaigns/2026-11-16-night/<run>/found/` are scanned as campaign files
  (group `night:<run>`), with the same sidecar audit.
- Second snapshot `L0/baseline/known-by-2350.json`: every archive and campaign found/ file with
  mtime <= 2026-11-15 23:50 UTC (4562 files, 400 of them campaign files). A point's status is
  `known` (15:20 archive), `known-by-23:50 (<agent>; new vs archive)` (the 11-15 campaign) or
  `new (<group>)` (after 23:50: the night); JSON field `era` = archive / campaign-11-15 / new.
- Path certification is informational only (user 23:50 UTC): shown in the `path` columns, never
  used to qualify or demote a result; the kernel-cap, start-outside-limits and donor items are
  listed under "Search-path notes" (levels INFO / NOTE), not as warnings.
- Notable lines (user 23:50 UTC): T03 any G <= 123, T05 any G <= 102, at any GD within the hard
  limits (`NOTABLE_DEFAULT`; TARGETS.json `notable_G_max` overrides). T03 `gates_for_depth`
  GD <= 22 and T05 `gates_for_depth` GD_max 999 come from TARGETS.json; with
  `min_gate_gain_for_depth_cost` 3 the T05 tradeoff class needs G <= 100, so G 101-102 at GD > 32
  shows as "notable" only (a tradeoff entry may set its own `min_gate_gain`). A circuit matching
  several tradeoff kinds takes `gates_for_depth` first.
- `LEDGER_OUT=DIR` writes LEDGER.md / LEDGER.json / history to DIR instead of the campaign folder
  (used by the dry run); `run --strict` exits 1 when an issue has level FAIL.

## What a run does

1. Reads `TARGETS.json` (references, hard limits, tradeoff rules, `min_gate_gain_for_depth_cost`,
   `max_gate_cost_for_depth_gain`). Nothing about the targets is hard-coded, so a threshold the
   user changes there is used on the next run.
2. Scans circuit files (`*.circ.txt`, `*.bfx`):
   - campaign: `~/xs-campaigns/2026-11-15-targets/<agent>/found/**` with the sidecar
     `<name>.json` next to each circuit;
   - archive: `~/xs-campaigns/2026-11-15-study/best-1400/`, `~/xs-campaigns/2026-11-14-hub/long/archive/*.bfx`
     (read with `core.from_kernel`), `nonlinear/boolflux/results/aes/**`, and every
     `~/xs-campaigns/2026-11-15-study/**/found/**`.
3. Verifies every file with `campaigns/aes_check.py`'s `check()`: boolflux.core and the
   independent verifier (`independent/verify.py`) on all 256 inputs, metrics must agree, gates in
   {AND, XOR, XNOR, NOT}, NIST counting (every gate counts, NOT included; BUF lines free).
   Results are cached in `L0/cache/verify.json` by the sha256 of the file bytes; the cache is
   dropped when the verifier code changes (fingerprint of aes_check.py, core.py, targets.py,
   independent/verify.py, hub/common.py). A re-run checks only new or changed files.
4. Per target, over every verified circuit with A <= ref A and AD <= ref AD:
   - class: **strict** (G <= ref G, GD <= ref GD, one strictly smaller); **tradeoff:<kind>** (a
     move listed under the target's `tradeoffs`); **other**. Kinds:
     `gates_for_depth` (ref GD < GD <= GD_max and G <= ref G - min_gate_gain_for_depth_cost),
     `depth_for_gates` (GD <= GD_max < ref GD and ref G < G <= ref G + max_gate_cost_for_depth_gain),
     `and_depth_for_gates` (AD < ref AD, AD <= max(AD_targets), G or GD above the reference; T05);
     a tradeoff circuit that some strict circuit dominates (in (G, GD); for the AND-depth kind in
     (AD, G, GD)) is dropped from the tradeoff lists;
   - the (G, GD) Pareto frontier and the (A, AD, G, GD) Pareto frontier, the strict and tradeoff
     Pareto sets, best strict by G and by GD, best tradeoff per kind;
   - for every listed point: the difference to the reference, the pinned NIST circuits that
     dominate it (all four <=, tuple different) and those with an equal tuple, compared with
     every forward AES S-box circuit of the pin (`aes_check.published()`: `aes-sbox/`,
     `old-2020/`, `sbox/`), and the pinned (G, GD) frontier inside the same hard limits;
   - provenance (below), start / method / seed / elapsed / verification from the sidecar;
   - T05 (`and_depth_for_gates`): best G (then GD) and best GD (then G) per AND depth 7..1.
5. Lists every verified circuit with A <= 27 in all scanned folders.
6. Audits the campaign sidecars: file fails verification, sidecar tuple differs from the
   verified one, hard limit of the sidecar's target violated (FAIL); missing sidecar, missing
   fields of the brief's list (target, A AD G GD, start {path, sha256}, method, command, seed,
   elapsed_s, code, aes_check, utc), start file missing or with another sha256, sidecar
   without circuit (WARN).
7. Writes `~/xs-campaigns/2026-11-15-targets/LEDGER.md` and `LEDGER.json` atomically, a copy of
   the JSON in `L0/history/`, and prints a `CHANGE` line for every strict or tradeoff Pareto
   point that is not known and was not in the previous run.

## Provenance

The baseline (`L0/baseline/baseline.json`, built 2026-11-15 before campaign results arrived)
holds every archive circuit file whose mtime is <= 2026-11-15 15:20 UTC (hub archive: the
record's `t_admit`), with its sha256, tuple and structural key (`hub.common.structure_key`:
the circuit as a DAG, invariant under gate order and operand order of symmetric gates).
`L0/baseline/filelist-*.tsv` is the raw listing (path, mtime, size) taken at 15:22:51 UTC.

- **known**: the tuple is realised by a baseline file;
- **reproduced**: a campaign circuit whose structure, or else whose tuple, equals a baseline
  circuit (the ledger names that file);
- **new**: neither. An archive file written after the cut-off that is not known is shown as
  "new (archive after cut-off: <folder>)".

## Search-path certification (COMPLIANCE-1820.md, 18:20-23:50 UTC; informational only since)

Kept as a record. Since 2026-11-15 23:50 UTC (user, BRIEF2 decision 2) search states may exceed
the A, AD, G and GD caps as long as the recorded result is within the hard limits; the items
below are computed and shown, but no longer qualify a result ("claim" is always empty) and are
reported as INFO / NOTE.

The hard A/AD limits hold for retained search states, not only results; a kernel stage that
starts above a cap without `repair_keep 1` may pass through states outside A/AD.

- Each campaign file gets `path`: sidecar `path_certified` true -> **certified**, false ->
  **not certified**, missing or anything else -> **unknown**; a file named in the sidecar
  `reproduces` (path, basename, stem or sha256) of a certified file whose tuple is all <= its
  own -> **reproduced-certified (by FILE)**. Archive files are starts: **n/a**.
- A ledger point takes the best path of its campaign files; a known tuple is **n/a (known)**.
  A strict or tradeoff point with no certified campaign file is shown as
  "strict (within limits; search path not certified)" (same for tradeoffs). The summary has a
  column "best strict, certified path or known".
- FLAG: method / command / lineage name a kernel stage (kernel, fdrive, bfx, hub/, scheduler,
  op_polish/trb/pull), the sidecar never mentions `repair_keep`, and the start (verified) is
  above a cap of the stage (caps from method.caps / caps / --cap, --cap-gd, --cap-a, --cap-ad;
  A/AD default to the target's limits), or the start tuple is unknown. Also says so when the
  sidecar claims path_certified true. If the sidecar is path_certified true and its path_note
  documents a trace audit (trace / replay / "accepted kernel states", compliance rule 2), the
  item is a NOTE instead of a FLAG.
- WARN: a start outside the target's A/AD limits (rule 1), unless the sidecar has
  `donor_outside_limits: <file>` and a builder statement (non-empty string in one of
  `donor_note`, `donor_statement`, `builder_statement`, `retained_states`, `intermediate_states`, `statement`)
  that no complete circuit held, retained or output exceeded the limits (Ruling 18:45). Such a file
  shows "construction from a donor outside the limits; all retained states within limits" in its
  path; a donor without the statement is a WARN and shows "builder statement MISSING".
- Lineage (coordinator 18:50): a file whose own run is certified but whose start is a campaign
  file (path or sha256) without an effective certification is "not certified (inherited from
  START)"; it becomes certified automatically once that ancestor is certified or
  reproduced-certified. Archive starts do not affect it. Computed to a fixpoint over the
  `reproduces` links.
- A path that becomes certified is reported as a change ("NEWLY CERTIFIED").

## Evidence

Each row "file F computes the AES S-box with (A, AD, G, GD)" is [C] (exhaustive over 256 inputs,
two verifiers). "new", "dominated by" and frontier statements are [C] only relative to the
scanned folders and the pinned NIST set; they are not lower bounds and say nothing about
unpublished or other published work.

## Documentation for publication

See [DOCS-PLAN.md](DOCS-PLAN.md): the `results/targets/` layout, the sidecar and reproduction
templates (`SIDECAR-TEMPLATE.json`, `REPRODUCE-TEMPLATE.md`), and the sections the coordinator
should merge into README / HISTORY / VERIFICATION.
