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

Phase 2: steps 1-4 (and curate_aes, manifest, BEST.md, verify_all, tests) are one command,
`bash nonlinear/boolflux/campaigns/targets/morning.sh` (below).

## Additions by L1 (2026-11-16, phase 2) for D1 and the coordinator

Files changed or added by L1 (uncommitted): `campaigns/targets/ledger.py` (phase-2 rules),
`campaigns/targets/morning.sh` (new), `campaigns/targets/README.md` (section "Phase 2"; the
certification section marked informational), `campaigns/best_table.py` (EXTRA: targets and night
found/ folders), `campaigns/curate_aes.py` (tracks `targets-<agent>`, `night-<run>`,
`describe_targets()`), `tests/test_review5_py.py` (test_p12 covers the two new tracks).

Suggested text (D1 decides where it goes):

- `USAGE.md`, "Checking and placing AES circuits": add
  `bash nonlinear/boolflux/campaigns/targets/morning.sh [--dry-run [DIR]]   # ledger, curation, manifest, BEST.md, verify_all, tests`
  and `python3 nonlinear/boolflux/campaigns/targets/ledger.py run | curate [--apply] | snapshot`.
- `VERIFICATION.md`, section 6 (Provenance): "The target ledger labels a point `known` when a
  file of the archive as of 2026-11-15 15:20 UTC realises its tuple, `known-by-23:50` when a
  file of the second snapshot (archive and campaign found/ files as of 23:50 UTC) does (the
  results of the 2026-11-15 campaign day, new against the archive), and `new` otherwise (the
  2026-11-16 night runs). Search-path certification (COMPLIANCE-1820.md) is recorded per file
  but, by the user's decision of 23:50 UTC, is informational: the hard limits A <= ref A and
  AD <= ref AD apply to recorded results; search states may exceed caps."
- `results/targets/README.md`: (1) curated sidecars carry `class`, `class_kind`,
  `class_target`, `class_rule` and, for T03 / T05, `notable`; `class_agent` keeps a class the
  agent wrote (often for another target: one circuit appears under every target whose limits it
  meets); (2) the campaign record now also lists `BRIEF2.md`, and `night-2026-11-16/` holds the
  night folder's top-level *.md / *.json; (3) `Z/`, `T06/` and `.gz` logs exist only when a
  campaign point needs them (D2's note 5): write "when present".
- `results/targets/TARGETS.md` section 2: the T03 (GD <= 22, >= 3 gates) and T05 (any GD)
  gates-for-depth tradeoffs and the notable lines T03 G <= 123 / T05 G <= 102 (user 23:50
  UTC); with min_gate_gain_for_depth_cost = 3 the T05 tradeoff class needs G <= 100.
- `results/MANIFEST.json`: entries from the target campaign are
  `results/aes/aes-nist-targets-<agent>-t<NN>-g..-a..-gd..-ad...circ.txt` (night runs:
  `aes-nist-night-<run>-t<NN>-...`), `caps` = the target's hard limits (A, AD), the campaign
  sidecar copied as `.campaign.json`.
- DOCS-TODO 32 (coordinator 00:1x UTC), handled in code, for D1 to mark done after the morning
  run: 32.1 the curated file of a tuple is the certified one (ledger representative; curate_aes
  prefers a path_certified sidecar within a track); 32.2 `campaigns/targets/corrections.json`
  corrects the 138/24 method in the curated sidecar and the results/aes mechanism
  (`method_corrected_by`), P6's own file untouched; other P6 sidecars were not re-checked by L1;
  32.4 curated circuits get the four header comment lines; 32.5 `logs/<name>/start.circ.txt`,
  `command.sh` and a rewritten REPRODUCE.md; item 4 of the coordinator: verify_all.py has a
  `targets` section (results/targets/*/*.circ.txt); item 5: morning.sh step f2 fails unless
  BEST.json rows == MANIFEST.json aes_pareto (curate_aes adds the five A29 hub rows).
- `results/BEST.md` is regenerated by morning.sh after curate_aes, so its rows cite the curated
  `results/aes` files (`best_table.py --out ~/xs-campaigns/2026-11-15-targets/L1/best --md results/BEST.md`).
