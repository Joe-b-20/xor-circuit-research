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

## Status on 2026-11-15 (documentation audit, `strategies/L2/DOC-AUDIT.md`)

Resolved since the list above was written:

- Item 7: `strategies/C-G` were committed in 377b03f and the hub in 97abda7. The manifest still
  says "uncommitted, sha256 now" (see item 20).
- Items 10, 13: [DESIGN.md](DESIGN.md) was rewritten as the architecture as built; MECHANICS.md
  is still the pre-0659eb9 text and is marked so in DESIGN.md.
- Item 15, first half: track F's AD3 runs ended 22:50 UTC 11-14 and track C's sweeps were
  stopped at about 23:55 UTC. The re-curation itself is still to do.

Done in the audit's edit pass (README, HOW-IT-WORKS, HISTORY, USAGE, VERIFICATION, bench/REPORT):
the wrong and unsupported claims W1-W3, U1-U9 were reworded, stale statements were marked
"(updated after re-curation)" or corrected, and the gaps G1-G5, G7, G8 were written into the
text.

Still open, not editable in a documentation pass:

17. **Re-curation** (`curate_aes.py`, `manifest.py`, `verify_all.py`, `best_table.py`): every
    number marked "(updated after re-curation)" in README.md, HISTORY.md and VERIFICATION.md.
    The 41-tuple count and the depth-cap table predate the hub (61 rows in
    `~/xs-campaigns/2026-11-14-hub/best/BEST.md`) and track F's last AD3 results.
18. **MANIFEST.json, cap not met** (audit W4): two entries need `caps_met: false` and a
    mechanism text that says the result is the kernel's best infeasible state. Needs a field in
    `campaigns/manifest.py` / `curate_aes.py`.
19. **MANIFEST.json, `reproduction`** (audit U10): "deterministic command ... gives the same
    circuit" should add "with `--set skip_noop=0` on code after 7ae20c8, or with the run's own
    `src/` and `bin/` snapshot" (tested on 28/4/133/20; VERIFICATION.md section 6). The seven
    "deterministic construction ...; not re-run" entries can say "re-run 2026-11-15, identical"
    (`strategies/L2/rejoin.py`).
20. **MANIFEST.json, `code_version`**: cite 377b03f for the strategy scripts if their sha256
    still match; record the kernel binary hash per job for track E and track F results.
21. **MANIFEST.json, smaller gaps** (audit G6): null `within_job_s` for long1; 960 s in a 900 s
    job for the main-queue 175; "see cmd" seeds.
22. **`hub/SPEC.md`** (extends item 12): line 6-7 "34 frontier admissions in ~1 h vs 2 ... the
    only mechanism that lowered A on AES" (the A31 joins undercut their A32 parents; nothing
    lowered A below a published family minimum); line 82 says the generator and linres
    operators are "not implemented yet" (they exist in `hub/ops/`); the gain rule it defines is
    not a value signal (`strategies/L1/WHAT-WORKS.md` finding 1).
23. **`strategies/E/NOTES.md`**: its per-operator "gain per CPU-h" tables use that gain rule;
    line 44 does not say that the infeasible cap-A31 runs are where 32/5/104/29 came from.
    **`strategies/F/NOTES.md:148`**: "1/35" should be 2 of 35. **`strategies/D/README.md:79-89`,
    `D/STATUS.md`**: "~3,900" windows and "locally exact-optimal" (audit W2, U2).
    **`strategies/C/NOTES.md`, `C/STATUS.md`**: the finished gamma sweeps are not recorded.
    These belong to their tracks and were not edited.
24. **[runs/INDEX.md](runs/INDEX.md)**: lines 38, 41 ("still running") and 51 (hub "not yet
    documented"); the 2026-11-14-hub, 2026-11-14-G and 2026-11-15-study folders have no entries.
25. **[LEDGER.md](LEDGER.md) section 3 and [CHECKPOINT.md](CHECKPOINT.md)**: still against pin
    e6ac0d0 (item 11); README now labels both as historical.
26. **Tests**: the test counts in USAGE.md (33 and 36) were taken on 2026-11-14 and do not
    include `hub/tests/test_hub.py`. Recount when the code-review branch is merged.
