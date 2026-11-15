# Documentation plan for campaign 2026-11-15-targets (for the coordinator)

L0 added files only; no existing BoolFlux doc was changed. The model is XORFlux's standard in
the main repository (`~/xor-circuit-research`): `search/README.md` (index page + table of pages),
`search/HOW-IT-WORKS.md`, `search/USAGE.md`, `search/HISTORY.md` (timeline, versions, failed
experiments, decisions), `circuits/README.md` (one folder per map, circuit named by its numbers,
`logs/<name>/found.json` + run files, a results table per map with the NIST column),
`circuits/SEARCH-TIME.md` (hardware and time per result), `circuits/check.py` (standalone check).

## Added by L0 (uncommitted, in this worktree)

| File | What |
|---|---|
| `campaigns/targets/ledger.py` | the ledger (baseline + run) |
| `campaigns/targets/README.md` | what the ledger does, rules, provenance, evidence |
| `campaigns/targets/SIDECAR-TEMPLATE.json` | sidecar schema for every saved circuit (brief's fields + run record) |
| `campaigns/targets/REPRODUCE-TEMPLATE.md` | per-circuit reproduction page |
| `campaigns/targets/DOCS-PLAN.md` | this file |
| `results/targets/README.md` | layout of the curated per-target folders |
| `results/targets/TARGETS.md` | campaign page skeleton (sections 1-8) |

The XORFlux equivalents: results/targets/<ID>/ = circuits/<map>/; logs/<name>/found.json and
REPRODUCE.md = circuits/<map>/logs/<name>/; TARGETS.md sections 3 and 7 = circuits/README.md
tables and SEARCH-TIME.md; section 5 = HISTORY.md "Failed experiments".

## To merge into existing docs (coordinator; suggested text in brackets)

- `README.md`, section "Results so far": one paragraph + a 10-row table (target, reference,
  best strict, best tradeoff, status) from the final LEDGER.md summary, linking
  `results/targets/TARGETS.md`. Section "Folders": rows for `results/targets/` and
  `campaigns/targets/` and for `strategies/P1..P7, Z1/`.
- `HISTORY.md`: a section "The targeted campaigns (2026-11-15, 15:30-23:45 UTC)": request in one
  sentence, agents and CPUs, per-target outcome in one line each, failed approaches, decisions;
  a timeline row.
- `VERIFICATION.md`: in section 1 ("One command"), add the ledger command; in section 5
  (Dominance), the target classes strict / tradeoff (tradeoffs never dominate) and "dominated by
  pinned" = all four <= with a different tuple, against `aes_check.published()`; in section 6
  (Provenance), the known / reproduced / new rule with the 15:20 UTC baseline and
  structure_key, and the sidecar fields the ledger checks.
- `USAGE.md`: two lines on `ledger.py baseline|run`.
- `results/MANIFEST.json`: curated target circuits get entries like results/aes (run
  `campaigns/manifest.py` after copying; the manifest's `reproduction` vocabulary is the one in
  REPRODUCE-TEMPLATE.md).

## Curation steps at the end (coordinator)

1. `ledger.py run`; resolve every FAIL in its "issues" section.
2. For each target, copy the non-known frontier / strict / tradeoff circuits and sidecars into
   `results/targets/<ID>/` under the naming rule, with `logs/<name>/` (found.json, REPRODUCE.md,
   aes_check.json, command.sh, logs).
3. Copy the final LEDGER.md / LEDGER.json into `results/targets/`, fill TARGETS.md.
4. `aes_check.py` on `results/targets/*/*.circ.txt`; merge the doc sections above; commit.
