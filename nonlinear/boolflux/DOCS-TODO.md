# Documentation and code mismatches found while writing the docs (2026-11-14)

These were found during the documentation pass. The code named here was not changed, because
other agents are working on it. Each item says where the mismatch is.

## Code or tool behaviour

1. **`campaigns/best_table.py` category title.** "Fewer ANDs than any published circuit except
   A = 28 (29 <= A <= 31)" is wrong. The pinned set has A29 and A30 forward circuits
   (`nist/sbox/aes-sbox-fwd-a29-*`, `-a30-*`). The dominance computation itself includes them.
2. **`best_table.py` default output** is `~/xs-campaigns/2026-11-13-aes/best/`, and it never
   removes files. That folder mixes files from an 11:17 and a 12:26 (local) run, and `BEST.md`
   (38 rows) is older than the current 41-row result. It also keeps only the first circuit per
   tuple, so the two different 121@GD14 circuits (tracks D and F) appear once.
3. **`campaigns/aes_check.py` `load()`** writes `FILE.check.circ.txt` next to every `.bfx` it
   checks, which means it writes into campaign folders. `verify_all.py` avoids this by converting
   in a temporary folder.
4. **`cli.py -h`**: `run`, `verify` and `start` have no help strings (only `pipe` and `flow` do).
   `verify` cannot check caps.
5. **`cli.py` docstring** example `--out nonlinear/boolflux/runs/present-bgc` writes run output
   into the repository, against [runs/README.md](runs/README.md). `.gitignore` has no rule for run
   folders under `runs/`.
6. **`kernel/bfx.c:85`** comment "zeroed padding: skip_noop memcmp" describes the old no-op test.
   Review 3 replaced it with a structural test.
7. **Uncommitted code behind curated results.** The 36 AES-push circuits in `results/aes/` came
   from `strategies/C,D,E,F/`, which is untracked. Their `code_version` records the scripts'
   sha256 at curation time (17:40 UTC), not necessarily what ran. Committing `strategies/`
   would pin it.
8. **Track E long1 admissions** record no time within the polish job (low1's do). The manifest
   gives only `since_run_start_s` for them.
9. **First test run**: `unittest discover -s nonlinear/boolflux/tests` gave 1 error on the first
   of two runs on CPU 0. The second run was clean (33 tests OK, 108 s). It was not investigated,
   and other agents were active at the time.

## Documents that are now stale

10. **[bench/MECHANICS.md](bench/MECHANICS.md)** predates 0659eb9. Section 2 says `cli.py` does not
    set the linear mode, but it is now automatic for XOR-only models (`workflow.is_linear`).
    Section 4 describes acceptance by weighted penalty, but ranking is now `lex`
    (`objective.rank`). Section 4 describes `skip_noop` as a gate-for-gate comparison, but it is
    now a structural test.
11. **[LEDGER.md](LEDGER.md) section 3 and [CHECKPOINT.md](CHECKPOINT.md)** are against pin
    e6ac0d0 (12 tuples, 131@13, 124@14). At 3d80774 one of the 12 equals a published circuit and
    five are dominated by later results (HISTORY.md). A banner was added to LEDGER.md.
    CHECKPOINT.md was not changed.
12. **[hub/SPEC.md](hub/SPEC.md)** cites "34 frontier admissions in ~1 h vs 2 for polishing
    alone". The final track E A/B (`strategies/E/NOTES.md`) has 41 vs 4 admissions and 17 vs 3
    frontier points in 4.7 CPU-h each. The SPEC also continues to change.
13. **[DESIGN.md](DESIGN.md)** verification section names `campaigns/collect.py` only. The
    manifest, curation and `verify_all.py` tools are not mentioned.
14. **[audit/AUDIT.md](audit/AUDIT.md)** covers the 2026-11-13 set. `audit.py` was not re-run on
    the AES-push results.

## To redo when campaigns finish

15. Track F's AD3 runs (`F/ad3/`, from 17:31 UTC) and track C's exhaustive runs were still
    running at curation (17:40 UTC). Run `curate_aes.py`, `manifest.py` and `verify_all.py`
    again afterwards. If a new point dominates one of the curated circuits, the dominated one
    stays, and its manifest entry shows `superseded_by_ours`.
16. `manifest.py` now records, for each NIST start, the earliest pin it was taken from. The 17
    starts that were new in e6ac0d0 were labelled 0876577, with sha256 null, before. Only the
    `start` field of existing entries changed.
