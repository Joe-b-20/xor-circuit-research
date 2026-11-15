# Review 5: hub (`nonlinear/boolflux/hub/`), agent C3, 2026-11-15

C3 stopped at a usage limit with H21 (cleanup before admission) half done (`common.clean`,
`Archive.reclean_legacy` and an opt-in `clean_first`, uncommitted, not called by the scheduler, no
tests) and H22 (kernel_bin temp name) not started. Agent C23 finished both with tests (03:00-05:30
UTC); see H21 and H22 below.

Scope: SPEC.md, archive.py, common.py, funcbank.py, join.py, joinplus.py, ops.py, scheduler.py,
op_*.py, trb_impl.py, compare.py, compare2.py, snapshot.py, status.py, after_ab.py, ops/*.py, tests/.
Evidence: the records of the 2026-11-14 campaign (`~/xs-campaigns/2026-11-14-hub/long`, 6134 jobs,
56 CPU-h, 2311 archived circuits) read with `~/xs-campaigns/2026-11-15-study/C3/audit.py`,
`audit2.py` and the new `hub/lineage.py`. Labels: [C] = counted on those records or proved by a
test; [H] = judgement.

Tests: `hub/tests/test_review5_hub.py` (32 tests; the finding number is in each docstring).
Commits on `boolflux-review5`: 9ef5530 (fixes + tests), 15dc579 (lineage tool), c8a41e1 (subclass
compatibility), and the documentation commit that adds this file.

## What the campaign records say about the old code [C]

| check | result |
|---|---|
| every archived circuit re-verified (two verifiers), id = content hash, metrics = record | 2311 / 2311 |
| `pub_new` against the pinned NIST set (same rule as `aes_check` `new_point`) | 2311 / 2311 agree |
| cells: member of the right cell, one G per cell, at most 4, cell minimum = minimum over records | 0 problems in 455 cells |
| front from cells = front over all records | equal (85 tuples, 311 ids) |
| two jobs on one CPU at the same time | 0 pairs; CPUs 17-19 ran 196 jobs (the stale-list incident) |
| operator exit codes | all 0; no job without `record.json` |
| job length against `--seconds` | at most 15 s over |
| records with operator, parents, seed, code version, settings | all operator-made records |
| records whose run file is found in the campaign itself, with the circuit in its outcome | 1333 of 2311 (H3) |
| the same found when `abhub/runs` is searched too | 2311 of 2311 |
| structures stored more than once (same DAG, other gate order) | 450 groups, 1204 circuits; 230 of 290 multi-member cells (H2) |
| run numbers used twice | 24 (H3) |
| identical (operator, target, seed) jobs | 12 (H19) |
| join jobs | 3907; partner list = 300 front ids in every one; 3221 without a candidate, 426 with duplicates only (H8) |

So admission, verification, cells, front and `pub_new` did what the spec says. The defects are in
what was rewarded and targeted, in duplicates, in lineage naming, and in robustness.

## Findings

Severity: **high** = wrong results, lost or ambiguous lineage, jobs on foreign CPUs, or a large share
of the CPU time misdirected; **medium** = a failure that needs an unlucky event, or measurable waste;
**low** = cosmetic or small.

| # | sev | finding | where (old code, f9fe6f7) | fix | test |
|---|---|---|---|---|---|
| H1 | medium | `cells.json` was trusted when present. A crash between writing a record and `cells.json` lost the circuit from its cell for good; a cell id without a record raised KeyError in every reader; a damaged record file was skipped silently. | archive.py:33-47 | Cells are always replayed from the records in admission order (`rebuild_cells`); `cells.json` and the new `index.jsonl` are caches; unreadable files are listed in `load_errors` and logged; `.bfx` and record written atomically. archive.py:57-104 | `test_cells_rebuilt_from_records` |
| H2 | high | "K = 4 distinct structures per cell" was K distinct texts. [C] 230 of 290 multi-member cells held the same DAG in another gate order; 1204 of 2311 circuits belong to 450 such groups. They filled the cells, the target pool (311 ids for 85 tuples) and the join partner list. | archive.py:104, common.py:49 | `common.structure_key` (invariant under gate order and operand order of symmetric gates; dead gates count); `admit` returns `duplicate-structure`; record field `skey`; old archives deduplicated in their cells at the scheduler's start (`dedupe_legacy`, 429 members dropped on a copy of `long`, no file deleted). common.py:52, archive.py:87, 196, 219 | `test_structural_duplicate_not_admitted` |
| H3 | high (publication) | Run ids `r<number>-<op>` were not unique. (a) The number was the count of run files, so after a restart that left killed jobs without a run file the numbers repeated (24 in `long`); with the same operator the job directory would have been reused, old candidate files included. (b) The `long` archive was started from `abhub`'s: 978 records name runs of `abhub`, and 590 of those names also exist in `long/runs` for other jobs. A reader following `run_id` gets the wrong run. | scheduler.py:61, 193-195 | Run id = `<campaign uid>.r<number>-<op>`, uid in `campaign.json`; number continues after the highest in `runs/` and `jobs/`; a job directory is never reused, and `ops.main` refuses a directory that holds candidates; one scheduler per directory (`scheduler.lock`). New tool `hub/lineage.py CAMPAIGN [--also OTHER]` checks every record (file hash, operator, parents, seed, code version, settings, run file whose outcome lists the circuit). [C] `lineage.py long --also abhub`: 2311 of 2311 complete, so the old archive's lineage is recoverable; `long` alone: 978 gaps. scheduler.py:118-146, 429-467; lineage.py | `test_run_ids_unique_and_one_scheduler_per_campaign`, `test_finish_lineage_and_failures`, `test_lineage_audit` |
| H4 | high | CPUs. (a) The list was given twice (xsrun pinning and `--cpus`) and nothing compared them: the incident of 00:19 UTC ran 196 jobs on CPUs 17-19. (b) `control.json` `"cpus"` could only add, never remove, and was read after the first jobs had been launched. (c) A repeated number in `--cpus` put two jobs on one CPU. | scheduler.py:94-96, 254-271 | `--cpus` defaults to the affinity of the scheduler process; an explicit list outside it is refused unless `--cpu-allow` confirms; `--cpu-allow` is the hard limit for `control.json`, whose `"cpus"` is now the exact set (shrinks, grows, refusals logged); control is read before the first launch; lists are sets; `cpus.json` shows the active set. `after_ab.py` updated to the exact-set meaning. scheduler.py:65-78, 174-215, 572-600 | `test_cpu_list_parsing_and_limits`, `test_control_cpus_is_the_exact_set` |
| H5 | high | `Archive.gain` gave 8 ("lowers A") whenever some archived point was no worse on the other three coordinates, which a higher-A circuit with fewer gates almost always is. [C, L1] 51 of 75 front admissions scored 8 although all were fewer gates under the same caps. The bandit reward was close to an admission count. | archive.py:88-97 | `gain_mode='value'` (default): 8 / 4 for an (A, AD) reach, 1 for a GD reach inside (A, AD), else 0.5 per gate saved (max 3) against the best G in the cap box; 0 for dominated tuples (the 0.01 for cell-only admissions is gone). `--gain legacy` keeps the old rule. archive.py:165-194 | `test_value_gain` |
| H6 | medium | `control.json` was applied key by key: scripts and generators were registered, then an unknown op aborted the rest without a log of what had been applied; the file's mtime was stored before parsing, so a file read half-written was never read again; `scripts` / `generators` changed module globals; an exception in `control()` or `ingest()` (a file that vanished between glob and stat) ended the scheduler. | scheduler.py:67-102, 104-120 | `apply_control` validates everything, then applies; parse errors are retried; per-scheduler `scripts` / `generators`; `near_gap` and `tuple_caps` added; `control()` cannot end the loop. scheduler.py:217-289, 583-588 | `test_control_is_validated_as_a_whole` |
| H7 | high | Attempts were counted per circuit id and a tuple had up to 4 ids, so old tuples took 4 times the jobs while new ones waited. [C, L1] polish yields 2.31 / 0.92 / 0.00 / 0.56 / 0.26 front admissions per CPU-h on attempts 1 / 2 / 3 / 4 / 5+ of a tuple, pull 2.08 / 2.19 / 1.29 / 0.00 / 0.19; attempts 4+ cost 12.8 CPU-h for 3 admissions; 28/5/127/22 got no polish or pull in 3.4 h. | scheduler.py:172-185 | `--target-mode tuple` (default): attempts per (A, AD, G, GD); `--tuple-caps polish=2,pull=3`; `fresh_target`: a front tuple without its first polish / pull gets it before the bandit chooses (A <= 31 first, newest first); when all are capped, least-attempted first. Counts are restored from `stats.jsonl` / run files at a restart. `--target-mode id` is the old rule. scheduler.py:380-427, 148-172 | `test_targets_by_tuple_with_caps_and_fresh_first` |
| H8 | high | Join. Partners = (front ids + other cell minima)[:300]; the front had 283-311 ids, so the list was the front, the same in every job, and generator / nursery circuits never got a slot. The join of X with a fixed partner list is deterministic, yet each front target was joined up to 16 times. [C] 3907 jobs, 5.2 CPU-h; [C, L1] repeat joins: 3471 jobs, 4.65 CPU-h, 2 admissions. | ops.py:92-116, scheduler.py:172 | `--join-mode incremental` (default): partners = every cell member admitted after `--since`, oldest first; the job reports `joined_through`; the scheduler keeps the mark per target (also across restarts) and offers a target to join only when the archive has later admissions. A pass cut by time continues where it stopped. `--join-mode legacy` and `op_join` without `--since` keep the old pool. ops.py:100-146, scheduler.py:418-420, 448-450, 549-551 | `test_one_join_pass_per_target_and_archive_state` |
| H8b | medium | osc ran without an A cap (`{'A': None, ...}`), so it could trade ANDs for gates, against the value order. | ops/f_ops.py:44 | A cap = the input's; `--caps=-,AD,GD` gives the old behaviour. ops/f_ops.py:46 | `test_pull_caps_stay_positive_and_osc_keeps_the_and_cap` |
| H9 | high (publication) | `code_version` hashed `hub/*.py` and `kernel/bfx.c` only. Edits to `hub/ops/` (gen_skel, osc, linres and their libraries), `core.py`, `objective.py` or the verifier did not change the recorded version; no dirty flag; an empty commit string when git failed. The operator script path was not recorded, so a script registered through `control.json` from outside the hub left no trace of its content. | common.py:91-101 | Hash over hub, hub/ops (py, c, designs), kernel, core, objective, targets, skeleton, verifier, aes_check, the NIST model; `<commit>[-dirty]+<hash>`; every record and run file carries `script` and `script_sha`, `scheduler_version`, `kernel_bin`. common.py:128-165, scheduler.py:509-516 | `test_code_version_covers_operators_and_package`, `test_finish_lineage_and_failures` |
| H10 | low | Every operator job read every record file (2311 small files now; grows with the archive). | archive.py:33-40 | `index.jsonl`: one read; files missing from it are read singly; the scheduler rewrites it when incomplete. archive.py:57-72, 100 | `test_index_is_a_cache_of_the_records` |
| H11 | low | The front was recomputed from all cells (quadratic) after every admission and in every operator's `would_place` loop. | archive.py:70-74, 127 | Sorted single pass (`pareto`), and an O(front) update on admission. archive.py:33-39, 210-217 | `test_incremental_front_equals_recomputation` |
| H12 | medium | A candidate that was not a well-formed circuit (forward reference, wrong shape, cut file) raised inside `finish`; the exception was logged, but the job's other candidates were dropped and no run file was written. | common.py:57-76, scheduler.py:211-225 | `verify` and `admit` return a rejection for any malformed circuit; `finish` handles each candidate on its own and always writes the run file. common.py:79-113, archive.py:227-230, scheduler.py:518-534 | `test_malformed_circuit_is_rejected_not_raised`, `test_finish_lineage_and_failures` |
| H13 | medium | The scheduler kept every admitted circuit object for the whole run (`self.circ`), and the bandit history without bound. | archive.py:126, scheduler.py:229 | LRU of 512 circuits; history cut to the window; function bank written at most once a minute instead of every 10 admissions. archive.py:106-117, scheduler.py:536-538 | `test_circuit_cache_is_bounded` |
| H14 | medium | Failure handling. An operator that died left candidates that were admitted with `code_version` and settings empty; no operator ever returned a non-zero code for a failed kernel (a kernel exit 2 or 3 looked like "no candidate"); an operator whose script was broken would be relaunched every 0.5 s for ever; `--caps` with the wrong number of fields was a traceback. | scheduler.py:204-241, ops.py:45-69, 141-166 | CLI contract in SPEC.md: exit 0 with `cand_ids`, exit 1 with `error` in `record.json`, exit 2 for a bad command line; kernel failure and timeout raise `OpError`; run file `status` ok / failed / timeout / stopped; verified candidates of a failed job are admitted with the lineage completed from the launch and `job_status` set; candidates not listed in `cand_ids` are refused; 5 failures in a row suspend the operator for 10 minutes. scheduler.py:477-561, ops.py:47-78, 171-223 | `test_finish_lineage_and_failures`, `test_cli_contract` |
| H15 | medium | No time limit on a job: a hung operator held its CPU for ever and the scheduler never ended (`while running`). Jobs started just before the end ran their full length. A stop by systemd wrote no `end` event (1 `end` for 5 `start` in `long`) and did not save the function bank. | scheduler.py:188-202, 252-276 | Jobs run in their own process group and are killed after 2 x seconds + 120 s; a job's seconds are cut to the time left (none is started with under 5 s); SIGTERM / SIGINT stop the jobs, write their run files, the bank, the front and the `end` event. scheduler.py:435-436, 468-475, 572-615 | `test_stuck_job_is_killed_with_its_children`, `test_sigterm_ends_the_campaign_cleanly`, `test_launch_falls_back_cuts_to_the_end_and_never_reuses_a_job_dir` |
| H16 | low (publication) | Seeds and ingested circuits carried only a file path: no content hash, and the JSON sidecar of the agent that found the circuit was not kept. Unreadable ingest files were skipped without a log. | scheduler.py:104-141 | `source_info`: `file_sha`, `sidecar`; `ingest-error` / `ingest-reject` events. scheduler.py:290-322 | `test_ingest_never_fatal_and_keeps_the_sidecar` |
| H17 | low | `ops._kernel` rebuilt the kernel weights and `lex` by hand, a second definition next to `objective.weights`, without key validation. The cost table (AND, XOR, XNOR, NOT = 1) and the caps agree with the archive's G and cells [C, test]. | ops.py:47-56 | `objective.weights` / `objective.parse` are used. ops.py:50-51, 198 | `test_cli_contract` |
| H18 | low | linres scanned the whole function bank (13185 functions, a Gaussian reduction each) in every rebuild try, although the result depends only on the layer. | ops/op_linres.py:96-100 | Cached per layer. ops/op_linres.py:97-105 | `test_linres_scans_the_bank_once_per_layer` |
| H19 | low | A restart with the same `--seed` replayed the same choices (12 identical jobs) and started the bandit and the attempt counts from nothing. | scheduler.py:53, 58-59 | RNG seeded with (seed, last run number); history, attempts and join marks restored from `stats.jsonl`. scheduler.py:102, 148-172 | `test_finish_lineage_and_failures` (part 6) |
| H20 | low | When the bandit's best operator had no free target the CPU stayed idle and the same choice was made again half a second later. `ad3_share` was undone when the near pool replaced the pool. Front, run files and the lock-free `cells.json` tmp name were not written atomically. | scheduler.py:172-185, 238, 250 | Fallback to the other operators by score; AD3 filter applied after the near choice; atomic writes with per-process tmp names. scheduler.py:406-447 | `test_launch_falls_back_cuts_to_the_end_and_never_reuses_a_job_dir` |
| H21 | high | [C, C1's finding, recounted] 172 of 2311 archived circuits of `long` hold a structurally duplicate AND (same operation, same operands), so their true A is one lower: 1b706c348e80 is recorded 30/4/144/17 and is 29/4/143/17. Candidates were admitted as the operators wrote them (join and trb outputs carried the copies). | archive.py:admit, scheduler.py:finish | `common.clean` (C3): identical gates merged in topological order (operand order ignored for symmetric gates, merges propagate), then dead gates dropped; the function is unchanged. `Archive.admit(clean_first=True)` (default; C23): the archive stores, measures, verifies and places the cleaned circuit; `operator_settings` keeps `cleaned_from` (id of the text as given) and `raw_metrics`. `finish` records `cleaned_metrics` in the run outcome, gives the function bank the stored circuit and renews caps with the cleaned tuple. `Scheduler.reclean` at every start (once per record, `archive/cleaned.json`): an old record whose cleaned metrics differ is logged (`legacy-clean`: id, recorded, cleaned, status, new id) and its cleaned circuit admitted as a new record, operator `clean`, parent = the old record; old record files are not rewritten. | `test_clean_merges_identical_gates_and_drops_dead_ones`, `test_candidates_are_cleaned_before_admission`, `test_finish_admits_the_cleaned_candidate`, `test_legacy_records_are_cleaned_once_with_lineage`, `test_the_reported_example_of_the_long_campaign` |
| H22 | medium | `ops.kernel_bin` compiled into `ARCHIVE/bin/bfx-<hash>.tmp`, one name for every builder: two operators that found the binary missing (first jobs after a kernel change) wrote the same file and could rename the other's half-written binary into place. | ops.py:34-44 | `mkstemp` in the bin folder (a name per build), `chmod 755`, `os.replace`; a failed build removes its file. (`cli.build_kernel`, same pattern: PYTHON.md P25.) | `test_kernel_bin_unique_temporary_and_atomic_rename` |

## H21 on the `long` archive (C23, a copy, read-only on the original)

[C, `~/xs-campaigns/2026-11-15-study/C23/C23-count-clean.py` and `reclean_copy.py` on a copy of
`~/xs-campaigns/2026-11-14-hub/long/archive`]: 2311 records; 172 change under cleanup, all by exactly
one AND (G by 1 or 2); none changes only in G. `reclean_legacy` on the copy: 93 cleaned circuits are new
records, 65 are `duplicate-structure` and 14 `duplicate` of circuits already archived (the operators had
found the clean version too); no new front tuple, no front tuple lost, gain 0 for all. The lowest cleaned
tuples are A28 ones (28/4/134/24, 28/5/126/30, 28/5/130/20, 28/5/132/20), all dominated by the front.
First start on `long`: about 19 s wall (8 s CPU) on the shared CPU 12, then nothing on later starts.

## Tuple-cap renewal (follow-up, behind a flag)

`--cap-renew box` (default `never`), `--cap-renew-max N` (default 3). When a circuit is admitted with
gain > 0 (a new front tuple q), every front tuple t whose cap box contains q (q.A <= t.A, q.AD <= t.AD,
q.GD <= t.GD; q then has more gates than t) gets its caps renewed for every capped operator: the jobs
counted against the cap restart from zero, at most N times per (operator, tuple). `Scheduler.renew_caps`,
event `cap-renew`; test `test_cap_renewal_by_front_change_in_the_cap_box`.

- [H] Why this trigger: a capped tuple is one where polish / pull stopped paying. A new front tuple under
  the same caps is the only signal in the archive that this region moved again. It is a re-exploration
  budget, not a change of what polish computes: polish and pull read only their target.
- [C] Cost bound: one renewal gives a tuple cap(polish) + cap(pull) = 5 jobs (7.5 CPU-min at 90 s). A new
  low point lies in the box of every front tuple with larger A, AD and GD, so one admission can renew
  many tuples; N bounds the total at N x 5 jobs per tuple.
- Not measured: no campaign has run with it. Renewals are kept in memory only; after a restart the counts
  restored from `stats.jsonl` are the totals, so every old tuple is capped again until the next renewal.
- For an A/B: arm 1 `--cap-renew never`, arm 2 `--cap-renew box`, same archive snapshot and seeds.

## For X2 (goal scheduler on this code; details and patch in `review5/X2-COMPAT.md`)

Checked: your `hub/scheduler_goal.py` of 02:36 UTC (md5 07960129, the version that launches through
`super().launch` with the `S.SCRIPTS` swap and `strategies/X2/op_goal.py`), on the review 5 hub, on a copy
of the long archive.

- **Unchanged, it runs but the goal layer has no effect** [C]: 4 jobs, 4 `goal-compat-warning`. Two causes.
  (1) The base `launch` now serves `fresh_target` (front tuples without a first polish / pull) before it
  calls `choose_op` / `choose_target`, so your pick is not asked for while such tuples exist. (2) The base
  reads `self.scripts[op]`, not `S.SCRIPTS[op]`, so the swap to `op_goal.py` does nothing and no job gets
  `X2_CAPS` / `X2_OBJECTIVE`.
- **Fix: `review5/x2-compat.patch`** (86 diff lines). Goal jobs call the new
  `Scheduler.start_job(cpu, op, why, tid, extra=['--objective', ..., '--caps=A,AD,GD'], env=...)`; the
  generic share stays `super().launch`. With it: F pull, C gpull under kernel caps 28/5/19, D pull, G polish
  under 44/4/11, one generic `fresh` job, no warning, run ids with the campaign uid.
- Also in the patch: `o in self.scripts` in `choose_goal_op`; the `_fix_gjoin_parents` call removed (the
  base records join parents for every operator that lists `joins` per candidate).
- Base changes made for you: `tkey` in the base is now `target_key`; options your `_Args` answers with
  `None` get the base defaults (without that the scheduler stopped at start with `gain_mode None`).
- Not exercised by the smoke runs: `goal_met`, rewards for new records, `gjoin` (no admission occurred).
- If you edit the file again, regenerate the patch with `x2compat/make_patched.py` (see X2-COMPAT.md).

## Not changed (for the coordinator to decide)

1. [H] **Nursery slack is inherited without end.** A circuit made from a generator-made circuit is
   admitted with the 40-gate slack, and so are its descendants (`operator_settings.nursery`); 453 of
   2311 records. It is how a new structure gets polished towards the front, but nothing ends it once
   the line has stopped improving. No evidence either way was collected; left as it is.
2. [C] **Jobs are not replayable bit for bit.** The kernel and the generators stop on wall time, so
   seed + settings + code version identify a run but do not reproduce its result. The circuit itself
   and its verification are the reproducible artefacts. A fixed iteration budget (`iters`, which the
   kernel accepts) would make polish / pull replayable; not done, because it changes job lengths.
3. [H] **Tuple caps and the bandit** (see also "Tuple-cap renewal" above). With `polish=2,pull=3` and the history restored, most old tuples
   of `long` are at their cap from the first minute. Polish and pull then run only on new tuples, and
   the CPU goes to join (first full pass per target, then only new partners), trb, osc and gen_skel,
   which have no cap unless one is set (`--tuple-caps polish=2,pull=3,osc=1,trb=2`). When every
   operator is capped everywhere the least-attempted tuples get jobs again (`choice: over-cap` in
   the run file). Whether the caps should renew after N admissions is open.
4. `hub/scheduler_goal.py` (X2, not in this worktree): run against this code, see "For X2" above and
   `review5/X2-COMPAT.md`.
5. join.py, joinplus.py, trb_impl.py: read line by line; no defect found. Their outputs are exact by
   construction and verified on admission (0 rejections in 5767 candidates of `long`).
6. compare.py, compare2.py, status.py: read; they work with the new run ids. `snapshot.py` now also
   writes `index.jsonl`.

## How to run the overnight hub on this code

    xsrun E 0-19 hub-night LOG -- python3 nonlinear/boolflux/hub/scheduler.py \
        --dir ~/xs-campaigns/2026-11-14-hub/long --hours H --seed 9 --nursery 0.3 \
        --ops polish,pull,join,trb,osc,gen_skel

`--cpus` is not needed (the xsrun list is used). The first start on the old archive does the one-off structure keys, cell deduplication (event
`cells-deduplicated`), the H21 cleanup of old records (events `legacy-clean`, `legacy-cleaned`; 172
records, 93 new `clean` records) and index, and reads the 6134 old run files for the attempt counts (not timed on
a free CPU). Old
behaviour for an A/B arm: `--gain legacy --target-mode id --join-mode legacy --tuple-caps ''`.
