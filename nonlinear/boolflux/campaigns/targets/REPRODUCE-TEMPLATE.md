# Reproduce <name> (<ID>, A/AD/G/GD = <A>/<AD>/<G>/<GD>)

Template: copy to `results/targets/<ID>/logs/<name>/REPRODUCE.md` and fill every `<...>` from
the circuit's sidecar (`SIDECAR-TEMPLATE.json` fields in brackets). Run every command from the
repository root.

## Check the circuit (no search code involved in the second verifier)

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/<ID>/<name>.circ.txt
```

Expected: `OK ... A AD G GD = <A> <AD> <G> <GD>` [aes_check]. sha256 of the file: `<sha256>`.

## What it is measured against

- Target <ID>: NIST `<ref file>` (pin 3d807741f937d29d3bef4f32f142ccda0cda9070), <rA>/<rAD>/<rG>/<rGD>.
  Hard limits A <= <rA>, AD <= <rAD>.
- Class: <strict | tradeoff:<kind> | other> (recomputed by `campaigns/targets/ledger.py` from
  TARGETS.json; a tradeoff never dominates the reference).
- Pinned circuits that dominate it: <none | list>. Provenance: <known | reproduced (same as ...) | new>.

## How it was found

- Start [start]: `<path>` (sha256 `<sha256>`, <kind>, tuple <tuple>). Lineage [lineage]: <...>.
- Method [method]: <engine>, mode <mode>, operators <chain>, caps A <= <a>, AD <= <ad>, GD <= <gd>.
- Code [code]: commit `<git>` plus <clean | uncommitted diff sha256 ...>; kernel `<path>`
  sha256 `<...>`.
- Seed [seed]: <seed>. Found after [elapsed_s] <s> s of a <job_wall_s> s job on CPU <cpu>
  (machine: see the hardware table in results/targets/TARGETS.md).
- Run record [run_dir, logs]: `logs/<name>/` holds <run.log, config.json, ...>.

## Re-run

```bash
<command, exactly as in the sidecar, with ~ expanded; output directory changed to a new one>
```

Reproduction class [reproduction]: <deterministic command | deterministic construction |
reproduced | one-off>. For a one-off (time-budgeted) run the command gives a run of the same
kind, not necessarily the same circuit; say so, and say whether a re-run was tried and what it gave.
