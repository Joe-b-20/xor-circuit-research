# Documentation and code mismatches found while writing the docs (2026-11-14)

These were found during the documentation pass. The code named here was not changed, because
other agents are working on it. Each item says where the mismatch is.

## Code or tool behaviour

Review 5 (2026-11-15, `review5/PYTHON.md`) resolved items 1 to 5 in the code: the category title
is computed from the pinned set (1); `best_table.py` has one row per tuple, counts and lists the
other distinct circuits in `BEST.json`, lists stale files and removes them with `--clean` (2);
`aes_check.py` writes nothing for a `.bfx` input, not even a temporary folder (3); every `cli.py`
command and option has help text and `verify` takes `--cap-*` (4); the docstring example writes
outside the repository (5). Items 6 to 9 are unchanged by that review.

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
- Item 15: track F's AD3 runs ended 22:50 UTC 11-14 and track C's sweeps were stopped at about
  23:55 UTC. The re-curation was done on 2026-11-15 (06:53 UTC, commit cb8fd56; item 17).

Done in the audit's edit pass (README, HOW-IT-WORKS, HISTORY, USAGE, VERIFICATION, bench/REPORT):
the wrong and unsupported claims W1-W3, U1-U9 were reworded, stale statements were marked
"(updated after re-curation)" or corrected, and the gaps G1-G5, G7, G8 were written into the
text. The "(updated after re-curation)" marks were replaced in the pass below.

## Status after the re-curation (2026-11-15, documentation pass after cb8fd56)

Resolved:

- **Item 17, re-curation.** Done in cb8fd56: MANIFEST.json has 194 entries, all verified;
  `verify_all.py` (06:57 UTC) found 186 distinct AES tuples of ours, 139 not dominated by the pin
  and 73 Pareto among ours; `results/BEST.md` is the curated table. This pass replaced every
  "(updated after re-curation)" placeholder with those numbers, marked "(re-curated 2026-11-15)":
  README.md (result count, depth-cap table, the "also new" line, a study-phase paragraph),
  HISTORY.md (introduction, timeline rows for track F's AD3 runs and the study phase, the six
  earlier points, track F, where the results stand, the hub, a new study-phase section),
  HOW-IT-WORKS.md (hub note) and VERIFICATION.md (the verify_all run, `code_version`, caps not
  met).
- **Item 18, cap not met.** Review 5 P22 (4191e08): `caps_met` on every entry and "CAPS NOT MET
  by this job" in the mechanism. Seven entries have `caps_met: false`.
- **Item 20, first half.** Review 5 P23: `code_version_commit_check` compares the curation-time
  script hashes with 377b03f (37 entries, all identical).
- **Item 19, first half.** Review 5 P21: the `reproducibility` record and the generated
  `reproduction` text ("deterministic with the run's own snapshot ...").

Still open:

19. **MANIFEST.json, joins** (second half of the old item): the seven "deterministic construction
    ..." entries still end "not re-run" (three of them without the splice2 sentence), although
    `strategies/L2/rejoin.py` rebuilt them identically on 2026-11-15.
20. **MANIFEST.json, kernel binary per job** for track E and track F results (second half of the
    old item; not checked in this pass).
21. **MANIFEST.json, smaller gaps** (audit G6): null `within_job_s` for long1; 960 s in a 900 s
    job for the main-queue 175 (still recorded so at cb8fd56); "see cmd" seeds.
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
    Line 45 also describes `best/BEST.md` as 38 rows against a 41-row table; the curated table is
    now `results/BEST.md` (73 rows).
26. **Tests**: the test counts in USAGE.md (33 and 36) were taken on 2026-11-14 and do not
    include `hub/tests/test_hub.py`. Review 5 is merged (924b4c0) and the message of cb8fd56
    reports "Suite 86 OK"; USAGE.md was not recounted in this pass.
27. **`results/BEST.md`, one stale row.** It lists 29/4/130/22 (`aes-sbox-a29-ad4-g130-gd22`)
    where MANIFEST.json `aes_pareto` and `verify_all.py` have 29/4/129/22
    (`aes-nist-hub-trb-g129-a29-gd22-ad4`, curated 06:53 UTC). BEST.md is byte-identical to
    `~/xs-campaigns/2026-11-15-study/best/BEST.md`, written at 06:51 UTC. The other 72 rows match.
    Rerun `best_table.py` and copy its BEST.md to `results/` (one CPU; not done in this pass,
    because the CPUs belong to the overnight queue).
28. **`verify_all.py` after the final manifest.** The recorded run (06:57 UTC) came before the
    `manifest.py` run that wrote the committed MANIFEST.json (06:59 UTC), so it matched 138 of the
    194 sha256 against the manifest, reported 56 as absent, and checked 124 nist-format files
    instead of 142. Rerun it once (VERIFICATION.md, "One command"). Its default `campaigns` roots do
    not include `~/xs-campaigns/2026-11-14-hub/` or `2026-11-15-study/`; those circuits are checked
    only through `results/aes`.
29. **Overnight queue** (launched 06:47 UTC, `launch-0700.sh`; HISTORY.md, study phase): its
    results are in no document yet. After it ends, the morning checklist of
    `strategies/L1/QUEUE-REVIEW.md` section 4, then `curate_aes.py`, `manifest.py`,
    `verify_all.py` and `best_table.py`, then README.md, HISTORY.md and VERIFICATION.md.
