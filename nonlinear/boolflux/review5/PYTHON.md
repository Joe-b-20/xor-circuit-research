# BoolFlux review 5, Python package (agent C2; finished by C23)

C2 stopped at a usage limit while writing the tests for the reproducibility changes (P20-P24),
with P17-P24 uncommitted and P25 (atomic kernel builds) and P26 (kernel seeds, N5 below) not yet
started. Agent C23 checked and committed C2's changes, wrote P25 and P26 with tests, and finished
this file (2026-11-15, 03:00-05:30 UTC).

Worktree `~/xcr-review5`, branch `boolflux-review5` (from f9fe6f7), local commits only. Scope:
`core.py`, `objective.py`, `workflow.py`, `cli.py`, `starts.py`, `targets.py`, `skeleton.py`,
`independent/`, `campaigns/*.py`, `bench/*.py`. The kernel (C1) and `hub/` (C3) are other
agents' files and were only read. Jobs ran on CPU 12 under `xsfg H` (the CPU is shared, so wall
times below are not meaningful; CPU times are given where they matter).

Regression tests: `tests/test_review5_py.py` (38 tests, about 30 s of CPU). Full suite:
see "Tests" at the end. Evidence labels: [C] = checked exhaustively within the stated case,
[H] = measured or observed on the stated data.

Line numbers refer to the files at f9fe6f7 (before the fixes).

## Summary

| # | severity | where (f9fe6f7) | finding | fix | test |
|---|---|---|---|---|---|
| P12 | **major** | `campaigns/curate_aes.py:71-76`, `:263-271`, `:252-253` | `curate_aes.py` stops with `ValueError` on the first hub archive file. It has been unusable since `best_table.candidates()` lists the hub archives (the `--dry-run` in USAGE.md fails too) | hub files get the track `hub` and a provenance rule built from the archive sidecars and run records; a circuit without provenance is listed (exit 1), the rest is curated | `test_p12_*` |
| P19 | **major** | `cli.py:122-125` | `cli.py verify` (and `verify_file`) reports FAIL, "metrics differ", for every file that writes a NOT as `NOT t a` under the NIST model, although all numbers agree: only core's counts were folded NOT -> XNOR. The 6 of our 86 `results/nist-format/` files that contain a NOT fail this way | both sides are compared with NOT counted as XNOR when the model writes NOT as `XNOR t a 0` | `test_p19_*` |
| P3 | major (latent) | `core.py:274-280`, `:292`, `:305` | `write_ncff` names internal wires `t1, t2, ...` without looking at the input/output names. A circuit whose inputs or outputs are called `t<k>` is written as a file that reads back as a different circuit (or does not read). No pinned NIST file and no result has such names [C: 426 files round-trip] | the prefix is extended (`t_`, `t__`) until no declared name matches; duplicate or `0`/`1` names are refused | `test_p3_*`, `test_roundtrip_of_the_pinned_set` |
| P11 | major (usability, DOCS-TODO 2) | `campaigns/best_table.py:56-60`, `:62`, `:73-76`, `:46-47` | one circuit per tuple and the others dropped without trace; unreadable candidates skipped silently (`except: continue`); a tuple whose first circuit fails verification vanishes from the table; stale files of earlier runs stay in DIR; the category title says published 29..31-AND circuits have G >= 124 (it is 137; 124 is an A28 circuit); all-pairs dominance; no `-h` | see P11 below | `test_p11_*` |
| P10 | performance | `campaigns/aes_check.py:33-43` | every `aes_check.py` call re-verifies the 104 pinned circuits with the per-input evaluator: 9.5 s before the first candidate is looked at [H] | result cached, keyed by the bytes of the pinned files and of `verify.py`; `BOOLFLUX_NO_CACHE=1` and `verify_all.py` recompute | `test_p10_*` |
| P4 | minor | `core.py:218-262` | `read_ncff`: a wire assigned twice silently takes the later definition; an undefined operand, an unknown gate or a missing `Inputs:` line gives `KeyError`/`TypeError`; a file with two circuits is read as one; commas, zero-padded ranges (`x00:x07`) and declarations on two lines are read differently from `independent/verify.py` | `ValueError` naming the line; first circuit only; declarations read as the independent reader does | `test_p4_*` |
| P5 | minor | `core.py:193-198` | `from_kernel` accepts any numbers: a negative operand indexes from the end of the signal list (a different circuit, no error), a truncated file gives `IndexError` | structure check, `ValueError` | `test_p5_*` |
| P2 | minor | `campaigns/aes_check.py:65-69` | a BUF line counts as a gate type outside {AND, XOR, XNOR, NOT}: a correct file with BUF outputs FAILs. (`cli.verify_file` was fixed for this in review 3, `aes_check` was not) | BUF excluded from the library check; core's own op list is checked as well | `test_p2_*` |
| P1 | minor | `campaigns/aes_check.py:46-54` | independence of the two verifiers: see P1 below. One real point: a `.bfx` input left a temporary folder per call (`mkdtemp`, never removed) | the independent verifier gets the NCFF text in memory | `test_p1_*` |
| P7 | minor (DOCS-TODO 4, 5) | `cli.py:553-601`, `:174-190`, `:327`, `:500`, `:531-540` | no help text for `run`, `verify`, `start` and most options; `verify` cannot check caps and stops at the first unreadable file; unknown target = `KeyError` traceback; `--seeds a-b`, `--set novalue` = traceback; `run --rounds 0` = `NameError`; `flow --set skel.X=..` reaches the gate kernel, which stops every job with "unknown key" | see P7 below | `test_p7_*` |
| P13 | minor | `campaigns/curate_aes.py:270-282` | the same gate list found under two tracks (a track F circuit that the hub ingested) would be curated twice, as two result files | selection by distinct gate list; the first track in candidate order owns the circuit | `test_p13_*` |
| P14 | minor (latent) | `campaigns/manifest.py:188-190` | two results with the same tuple and gate counts get the same NIST-style name; the second overwrites the first in `nist-format/` and both manifest entries point at one file. No collision among the 86 current files [C] | a different circuit gets `-v2`, ...; identical gate lists in two result files are reported (`duplicate_circuits`, `same_circuit_as`) | `test_p14_*` |
| P15 | minor | `campaigns/collect.py:46-50`, `:67`, `:3`, `:33` | `improved` uses the weighted sum (1, 1e-4, 1e-8), not the lexicographic rank of review 3; `--copy` overwrites an existing results file of the same name; `--label TEXT` is documented but TEXT is taken as a run folder | `objective.rank`; no overwrite; option removed from the docstring | `test_p15_*` |
| P16 | minor | `campaigns/aes_check.py:91-95`, `verify_all.py:127`, `bench/*.py` | `aes_check.py` with no file exits 0 in silence and one malformed file ends the whole call with a traceback; `verify_all.py -h` starts the full 70 s run; `manifest.py`, `curate_aes.py`, `collect.py` and the six bench tools give `IndexError` or run on `-h` | usage text, exit status 0 for `-h` and 2 for a usage error; a bad file is a FAIL row | `test_p16_*` |
| P17 | minor (latent) | `skeleton.py:44-59` | a skeleton with more basis positions than the kernel's 512 (or more than 480 ANDs) is written with the high bits cut off, without a word. Largest case in the measured workflows: the AES ANF start, 1 + 8 + 246 positions, so nothing was cut so far | `ValueError` | `test_p17_*` |
| P18 | performance | `core.py:92-93`, `:117-126` | `metrics()` rebuilds the model's cost table for every gate; `input_tables(n)` runs its 2^n-step loop on every evaluation | cost table once per call; input tables cached per n: `metrics` 405 -> 254 us, `value_table` 970 -> 599 us on a 131-gate AES circuit [H: CPU time on a shared CPU, `review5/py_timing.py`] | `test_p18_*` |
| P20 | minor | `campaigns/manifest.py:74-75` | a start circuit outside the repository (a campaign pool file) is labelled `BoolFlux result`: `REPO / <absolute path>` is the absolute path, so the first test is true for any existing file. 7 manifest entries (track E joins with a pool start); their sha256 was right | relative paths only; MANIFEST.json regenerated (those 7 entries now say `campaign circuit (outside the repository)`) | `test_p20_*` |
| P25 | minor | `cli.py:45-49`, `:61-62` | `build_kernel` and `snapshot` ran gcc with `-o` on the final binary: a process that starts `kernel/bfx` while another rebuilds it can run a half-written file, and two builders write the same file | `compile_kernel`: gcc writes a temporary file of its own (`mkstemp` in the target folder), then `os.replace`; a failed build leaves nothing | `test_p25_*` |
| P26 | minor (reproducibility) | `cli.py:276`, `:309`, `:426`; `workflow.py:158`, `:188` | kernel seeds: `run`/`pipe` seed + 1000 x round, so (seed 1, round 1) = (seed 1001, round 0); `flow` and the benchmark seed x 1000 + round, so (1, 1000) = (2, 0) (1000 rounds of 10 s is under 3 h); two formulas for one thing | one function `workflow.kernel_seed(seed, round, scheme)`: `v2` = seed + round x 2^32, one-to-one for 0 <= seed, round < 2^32 (u64 kernel seed), = seed in round 0, so single-round `run` commands keep their seeds. `--seed-scheme legacy` (run, pipe, flow; bench plans `seed_scheme: legacy-flow`) restores the old formulas; `summary.json` records `seed_scheme` | `test_p26_*` |
| P8 | minor | `core.py:157-169` | a model file with `not_as` misspelt (`xnor0`) is taken as `NOT` | refused | `test_p8_*` |
| P9 | none (checked) | `objective.py:40-92`, `kernel/bfx.c:131-190` | kernel and Python agree on G, A, GD, AD, cost, cap excess and summed path excess under GD, AD and A caps [H: 40 random circuits, 5 cap sets]; the review-4 twin script had no A cap and was not a test | test only | `test_p9_*` |
| P6 | none (checked) | `core.py:83-98`, `:265-307`, `independent/verify.py:493-549` | NIST conventions: NOT is a gate and a level; written `XNOR t a 0` under the NIST model; BUF is no gate and no level; A = ANDs; msb/msb bit order; constant folds on reading [C: on the cases of the test] | test only | `test_p6_*` |

Nothing shipped is wrong because of these: every result file verifies as before, and the Pareto set
that `best_table.py` selects is the same rule applied to the same candidates. `results/MANIFEST.json`
was regenerated twice on the unchanged result set: in bece408 (one new key, `duplicate_circuits`,
empty) and in 4191e08 (format only, see "Reproducibility check").

## Major

### P12. `curate_aes.py` cannot run with hub archives among the candidates

- **Where.** `track_of` (`curate_aes.py:71-76`) calls `Path(f).relative_to(C)` with
  `C = ~/xs-campaigns/2026-11-13-aes`. `best_table.EXTRA` (added in the hub phase) puts every
  `~/xs-campaigns/2026-11-14-hub/*/archive/*.bfx` into `candidates()`. `main` (`:271`) calls
  `track_of` for every candidate, outside the `try`.
- **Reproduction.** `python3 nonlinear/boolflux/campaigns/curate_aes.py --dry-run` at f9fe6f7:
  `ValueError: '.../2026-11-14-hub/ab2base/archive/001e65c1d4e4.bfx' is not in the subpath of
  '.../2026-11-13-aes'` (`review5/py_curate_dry_run_before.txt`).
- **Also.** `describe` (`:252-253`) raises for any track without a rule, which ends the run after
  some circuits are already written.
- **Fix.** `track_of` returns `hub` for hub archives and `other` for anything else.
  `describe_hub` builds the summary that `manifest.py` reads from the archive's own sidecar
  (`<id>.json`: operator, settings, seed, run id, code version, times) and the campaign's run
  record (`runs/<run_id>.json`: the exact command). Lineage: `hub_lineage` follows `parents`
  through the sidecars, at most 4 levels and 40 nodes; what is cut is named in
  `parents_not_expanded`, and seed/ingest nodes carry the file they came from. A circuit whose
  provenance cannot be built is listed as `NO PROVENANCE, not curated`, the others are written,
  and the exit status is 1. An existing result file is never overwritten.
- **State.** The dry run now completes: 67 Pareto tuples, 25 already in `results/aes`,
  45 circuits to add (`review5/py_curate_dry_run_after.txt`). **The real run was not made**: it
  writes 45 result files and is the coordinator's decision. After it, `manifest.py` and
  `verify_all.py` must be run (USAGE.md).

### P19. `cli.py verify` fails every file with an explicit NOT under the NIST model

- **Where.** `verify_file` (`cli.py:122-125`): core's counts are folded (`NOT` -> `XNOR`) when
  the model has `not_as: XNOR0`, because core reads `XNOR t a 0` as a NOT while the independent
  verifier counts what is written. The independent counts were not folded. So a file that
  spells the gate `NOT t a` (NIST's own 2026 files with `xxn` names, and the 6 of our 86
  `results/nist-format/` copies that contain a NOT) has core counts `{XNOR: n+1}` against independent `{NOT: 1,
  XNOR: n}`.
- **Reproduction.** `python3 nonlinear/boolflux/cli.py verify
  nonlinear/boolflux/results/nist-format/aes-sbox-a264-ad19-g717-gd50-xxn453-194-1.circ.txt
  --target aes --model nist` gave `FAIL ... core=True indep=False lib=True` at f9fe6f7.
- **Who was affected.** `cli.py verify` by hand, and any `run`/`pipe`/`flow` whose model is
  `nist` and whose best circuit is read from a file with explicit NOTs (none: `write_best`
  writes `XNOR t a 0`). `manifest.py` and `verify_all.py` check `nist-format/` with
  `aes_check.check`, which compares only A, AD, G, GD, so they did not show it.
- **Fix.** Both count tables are folded before the comparison. Costs agree because
  `Model.load` already requires cost[NOT] = cost[XNOR] for such models.

### P3. `write_ncff` wire names can collide

- **Where.** `core.py:274-280`: `nm = 't%d' % k` for every gate that is not the first driver of
  an output.
- **What happens.** With inputs `t1, t2` (or an output `t3`), the first internal gate is also
  called `t1`. The file then defines an input again. The old `read_ncff` took the later
  definition silently, so `read_ncff(write_ncff(c))` was a different circuit; the independent
  verifier rejects the file ("input is assigned").
- **Reach.** Names come from the file a start was read from (`cli.py start`, `make_start`).
  `run`/`pipe`/`flow`, `best_table.py` and `curate_aes.py` rename to `x<i>`/`y<j>` first. No
  pinned NIST circuit and no result has a `t<k>` input or output: all 426 circuit files under
  `nonlinear/nist/` and `results/` round-trip exactly with their own names, through NCFF (both
  NOT spellings) and through `.bfx` [C, `review5/py_roundtrip.py`].
- **Fix.** The prefix grows (`t_1`, `t__1`) until no declared name has the form prefix+digits.
  Output for circuits without such names is byte-identical to before.

### P11. `best_table.py`: one row per tuple, nothing dropped, speed

- **One row per tuple.** The table keeps one row per (A, AD, G, GD), as before. The row's
  circuit is the first in candidate order (results/aes, the campaign tracks, the hub archives).
  New: the column `other` gives the number of further distinct circuits (different gate list)
  at the tuple, and `DIR/BEST.json` lists every distinct circuit of every table tuple with its
  first source file and the number of files that hold it. On the current candidates: 16,720
  files, 2,676 distinct file contents, 2,530 distinct circuits, 1,014 distinct tuples, 348 not
  dominated by the pinned set, 67 table rows, 268 distinct circuits on those rows [H].
- **Nothing dropped silently.** Unreadable candidates are counted in the table's last line,
  listed in `BEST.json` and printed (10 at most) on stderr; currently 0. If the first circuit
  of a tuple fails verification, the next distinct circuit is tried; a tuple with no verifying
  circuit is named in the table and the exit status is 1 (it used to disappear).
- **Stale files.** Circuit files in DIR that follow the tool's own naming and are not in the
  table are listed; `--clean` removes them. Nothing else in DIR is touched.
- **Title.** "published circuits here have G >= 124" was wrong for 29 <= A <= 31: the pinned
  set's smallest such circuit has G = 137 (29/5/137/32). The number is now computed. Categories
  for A < 28 and AD <= 2 were added so that such a circuit, if one is ever found, appears.
- **Speed.** Where the time went [H, `review5/py_prof_best_table.py`, CPU 12]: glob 0.8 s;
  reading all files 1.0 s; parsing and measuring all 16,720 files about 23 s; `published()`
  9.5 s; then one `aes_check.check` per row. The reported 10 minutes cannot be reproduced from
  these numbers on a free CPU; on a CPU shared by several agents the same run takes several
  times longer (this review's `manifest.py` run: 65 s of CPU in 5.5 min of wall time). Changes:
  byte-identical files are parsed once (the snapshot archives repeat most ids: 16,720 -> 2,676
  parses), the Pareto front is one pass against the front found so far, and `published()` is
  cached (P10). Whole run: 12 s of CPU including the one-time 9.5 s for the cache.

## Reproducibility records (coordinator request after L2's audit)

L2 (`strategies/L2/WHAT-WORKED-BEFORE.md` section 4, `DOC-AUDIT.md` U10, W4, G6) found three gaps
in what `manifest.py` and `curate_aes.py` record. All three are fixed in `manifest.py`, which
derives the fields at manifest time, so the 36 curated sidecars written on 2026-11-14 are not
rewritten.

| # | L2 finding | where (f9fe6f7) | fix | test |
|---|---|---|---|---|
| P21 | 47 AES entries (99 with the other targets) say "deterministic command: ... so the command gives the same circuit". True only with the code that ran: 28/4/133/20 replays byte for byte with its own binary and ends at 134 with the code of f9fe6f7 | `manifest.py:128-137` | new `reproducibility` record per entry: `class` (deterministic / one-off / construction / unknown), `code_at_run` (the run's `code_sha256_12`, its `src/` + `bin/` snapshot, sha256 of the binary), `head_same_source` (snapshot compared with the current source file by file, with the list of changed files), earlier re-runs with the code they used, and `checked` (below). The `reproduction` sentence is generated from it: "deterministic with the run's own snapshot (...)", then either "source unchanged, so the command gives the same circuit at the current code" or "the source has changed since (files), so the command at the current code is NOT known to give this circuit" | `test_p21_*` |
| P24 | no way to test the claim | - | `manifest.py --check-repro N [--seed S] [--only TEXT] [--mode snapshot\|head\|both]` re-runs the winning kernel job of N sampled deterministic entries: `snapshot` = `RUN/bin/bfx` on the job's own config and start; `head` = the kernel compiled from the current source with the config `cli.kernel_config` writes today (objective, caps, iterations, kernel seed, the command's `--set`). It prints IDENTICAL / DIFFERENT / ERROR per entry and mode, keeps the results in `results/REPRO-CHECK.json`, and the next `manifest.py` run copies them into the entries and the `reproduction` text. Exit status 1 if any check is not identical | `test_p24_*` |
| P23 | all 36 curated AES-push entries cite script hashes taken at curation time ("uncommitted, sha256 now"), not at run time | `curate_aes.py:61-64`, `manifest.py:180-183` | `code_version_recorded` says which it is ("script hashes taken at curation time (UTC), not at run time: the campaign did not record a code version per job", or "at run time" for hub sidecars and `cli.py` snapshots); `code_version_commit_check` compares every curation-time hash with the file in 377b03f, the commit that archived `strategies/` 14 minutes later. New hub entries (P12) carry the archive's run-time `code_version` | `test_p23_*` |
| P22 | two entries say "under caps" / "A cap = parent's" although the job never met its A cap (32/5/104/29 under cap A31; 29/5/135/17 under cap A28) | `curate_aes.py:289-293` | `caps_met` on every entry (metrics against `job_caps`, else `caps`); when false the mechanism ends with "CAPS NOT MET by this job (cap A 31, circuit A 32): the circuit is the best state of a run that never came within its caps". `curate_aes.py` writes the same sentence for future curations | `test_p22_*` |

What the regenerated manifest says and what was re-run is in "Reproducibility check" below.

## Reproducibility check

`review5/py_repro_check.sh` (output `review5/py_repro_check.txt`, results `results/REPRO-CHECK.json`),
run by C2 on CPU 12 from 02:30 to 02:58 UTC: the winning job of 28/4/133/20 and of 4 entries sampled
with `--seed 1` among the 101 deterministic entries with a run record, each replayed with its run's
own binary (`snapshot`) and with the kernel built from the review tree at that time (`head`, code
54147098ffda) [H: these 5 entries only]:

| entry | snapshot | head |
|---|---|---|
| aes 28/4/133/20 (`cost_gd`, code b0e56ecb18fe) | identical | 28/4/134/20 |
| aes 36/4/134/14 (code b0e56ecb18fe) | identical | 36/4/135/14 |
| aes 34/4/141/13 (code 8336425daeeb) | identical | same metrics, another gate list |
| piccolo 4/2/8/4 | identical | same metrics, another gate list |
| serpent_s7 6/4/16/10 | identical | 6/6/16/14 |

So the snapshots replay byte for byte, and the current code does not reproduce the recorded circuits
(the kernel and package source changed between those runs and the review tree; which change moves
each trajectory was not traced). L2's reading is confirmed on 5 of 5: "deterministic" holds for the run's own snapshot only.

The regenerated `results/MANIFEST.json` (C2, 02:59 UTC, committed in 4191e08) is a format change
only [C: compared entry by entry with the version before]: the same 138 entries (files, sha256,
metrics, verification unchanged); new keys `reproducibility` (138), `caps_met` (138),
`code_version_recorded` (36), `code_version_commit_check` (35); `reproduction` rewritten from the
record in 101 entries (5 with the checks above); `CAPS NOT MET` appended to 2 mechanisms (the two
track E jobs of P22); start kind corrected in 7 entries (P20). Every deterministic entry has
`head_same_source: false`, so no entry claims that the current code gives its circuit. The
`source_files_changed_since` lists were computed before P26 changed `cli.py` and `workflow.py`
(both were already listed as changed for most runs); the coordinator's next `manifest.py` run in the
main tree recomputes them.

## Minor and checked

### P1. Independence of the two verifiers in `aes_check`

Checked by reading both sides and by tests:

- `independent/verify.py` imports only the standard library (test: its import list is exactly
  `argparse, json, math, re, sys, dataclasses`).
- For a `.circ.txt` input each side parses the file's bytes with its own reader, evaluates
  with its own code (core: bitsliced truth tables; verify: one input at a time) and compares
  with its own S-box table (`targets.aes_sbox`, `verify.aes_sbox`, both computed from FIPS-197;
  the second is self-checked against three known values and for being a permutation). The
  metrics (A, AD, G, GD) of the two sides must be equal.
- A wrong circuit (one XOR turned into XNOR) is rejected by each side on its own: `core_ok`
  False and `independent_ok` False [C on that case].
- The one shared path is deliberate and now documented in the module docstring: a kernel
  `.bfx` file has a single reader (`core.from_kernel`), and the independent verifier checks
  core's NCFF rendering of what core read. A bug in `from_kernel` could therefore not be seen
  by comparing the two, but it cannot produce a false OK either: the independent verifier still
  proves that the rendered circuit computes the S-box with the stated metrics, and that
  rendering is what `best_table.py` and `curate_aes.py` publish. `from_kernel` now checks the
  structure it reads (P5).
- The library check used the independent side's counts only; it now also checks core's op
  list, so an op code without a name cannot slip through on one side.
- Differences between the two readers that remain, all on the safe side (the file fails):
  `XOR t a 0` and `XNOR t a 1` are wires for core and gates for verify (G differs, so
  `metrics_agree` is False); `BUF y 1` (constant output) is legal for verify and an error for
  core.

### P7. `cli.py` help, defaults, messages

- Every command (`run`, `pipe`, `flow`, `verify`, `start`, new `list`) has a one-line help and
  a description; every option has help text with its default; the epilog explains the metrics,
  the ranking and the exit status. The `flow` description names the settings of the measured
  workflows (gate; rebuild + gate = `--config full --skel-set iters=0 --adaptive`; repair under
  a cap). The docstring example writes to `~/xs-campaigns/DATE-NAME/...` (DOCS-TODO 5).
- **Defaults are unchanged** and pinned by `test_p7_defaults_are_the_measured_ones` (run: iters
  200000, seconds 3600, seeds 1-8, rounds 1, pool 4; pipe: iters 100000, skel-iters 20000,
  rounds 3, skel-share 0.5; flow: config gate, round-s 10, seeds 1-4; kernel defaults
  `workflow.DEFAULTS`).
- `verify`: `--cap-gd/--cap-ad/--cap-a` (checked by the independent verifier's `--max-*` and
  by `objective.feasible`), `.bfx` input, a second line with the reason on FAIL, an unreadable
  file is a FAIL row and the other files are still checked. Without caps the output line is as
  before.
- One-line messages, before any run folder is created: unknown target (with the list),
  unknown objective key, `--rounds 0`. `--seeds` and `--set` are parsed with messages
  (`'8-1'`, `'a-b'`, `''`, `novalue`). `flow --set skel.X` / `synth.X` is refused with a pointer
  to `--skel-set` / `--no-seeded`.
- `list` prints the targets (with n -> m and source), the stock models and the objective keys.

### P10. `published()` cache

`~/.cache/boolflux/published-<hash>.json` (or `$XDG_CACHE_HOME`), written atomically. The hash
covers the name and bytes of every pinned forward AES file and the bytes of
`independent/verify.py`, so a hit is the output of the identical computation; a damaged cache
file is recomputed. `verify_all.py` sets `BOOLFLUX_NO_CACHE=1`, so "re-verify everything" still
re-verifies the pinned set. First call 9.5 s, later calls 0.02 s [H].

### Checked and found correct (no change)

- `objective.rank` = (feasible flag, total cap excess, summed path excess, keys in order) and
  the kernel's `mcmp` (`bfx.c:183-189`) use the same order; `objective.excess` = the kernel's
  `viol`; `objective.path_excess` = the kernel's `vsum` (P9 test, with A caps).
- `workflow.check_sets` (review 4) still guards every `--set` path (`run`, `pipe`, `flow`,
  bench `set`); `skel_set` is not checked by design.
- `starts.anf` and `anf_coeffs` (Moebius transform on bit sets), `targets.load('map:...')`,
  `tables_from_values`, `value_table` bit order: consistent with `verify.py` on every pinned
  file and on the test cases.
- `skeleton.py` extraction, file format and the three rebuild variants: every rebuilt circuit
  is checked against the target before it is used (`workflow.py:174`, `cli.py:366`).
- `manifest.py`: a result without `.summary.json` stops the run with an error (not silent);
  `superseded_by_ours` and `aes_pareto` use the stated rule; regenerating the manifest changed
  nothing but the new key.
- `verify_all.py`: sections and counts as documented; campaign `.bfx` files are converted in a
  temporary folder that is removed.
- `bench/analyze.py`, `pooled.py` (sign test), `make_plan.py`: read; no defect found.
- `independent/verify.py`: structural rules (single assignment, operands defined earlier,
  inputs never assigned), per-input evaluation, metrics (BUF free and depth-transparent, G
  without BUF, cost by `math.fsum`), caps (`--max-*`): read line by line; no defect found and
  no change made. Its own tests (`independent/test_verify.py`) were not touched.
- The kernel default `skip_noop 1` is what the benchmark plans set explicitly, so `cli.py flow`
  without `--set` runs the measured gate workflow; the hub's polish/pull jobs write the same
  kernel settings as `flow --config gate` with the same objective and caps (compared on a hub
  run record, `long/runs/r05114-pull.json`).

## Not changed (open points)

| # | where | what | why left |
|---|---|---|---|
| N1 | `objective.py:52`, `bfx.c:172-175` | Python compares costs after rounding to 9 decimals, the kernel with a relative tolerance 1e-9 (1 + abs(x) + abs(y)). Two costs within about 1e-7 of each other at cost 100 are equal for the kernel and can differ for Python | only fractional-cost models; every stock model has unit costs; changing the rounding changes ranks recorded in old run data |
| N2 | `cli.py:88-91` | `verify_independent` writes `<file>.fn.json` next to the checked file for built-in targets other than AES (gf16-mul, maj3, ...) | documented in VERIFICATION.md and AUDIT.md; run folders keep it as part of the record |
| N3 | `verify_all.py:47` | the default campaign list is `2026-11-13-aes` only; hub `best/` and archives are checked only with `--campaigns ~/xs-campaigns/2026-11-14-hub` (best/ and found/), archives not at all | 2,676 distinct archive circuits would add minutes to a 70 s tool; the hub verifies on admission (C3's scope) |
| N4 | `best_table.py` default `--out` | still `~/xs-campaigns/2026-11-13-aes/best/` although the current table lives in `2026-11-14-hub/best/` | a documented default (USAGE.md); pass `--out` |
| N6 | `starts.py:50` | a target with a constant output bit raises `ValueError('constant output not supported')` as a traceback | no target has one |
| N7 | `campaigns/depth_report.py:22-30`, `frontier_report.py`, `pareto_audit.py:37-44` | three more copies of "the published forward AES set" and of the dominance test; `depth_report` reads metrics from file names and leaves out `nist/sbox/` | checked: at pin 3d80774 the 21 `sbox/` circuits change no "best G at GD <= d" value [C, d = 10..39]; not documented workflows; left to keep this change small |
| N8 | `bench/show_trace.py:35` | `by_function` sorts the two operand tables, so ANDN(a,b) and ANDN(b,a) look the same in the diff | display only |
| N9 | `campaigns/curate_aes.py` rules for tracks C-F and main | hard-coded per campaign (launch commands, kernel versions) | history of one campaign; not generalisable without that campaign's conventions |

## Tests

`python3 -m unittest nonlinear/boolflux/tests/test_review5_py.py`: 38 tests, OK (76 s wall, 33 s CPU, CPU 12, 03:10 UTC). `hub/tests/test_hub.py` + `test_review5_hub.py`: 36 tests, OK after `test_hub.test_cell_keeps_min_g` was adapted to cleaning on admission (H21: its dead-gate "worse" circuit is now admitted with `clean_first=False`).

Full suite `python3 -m unittest discover -s nonlinear/boolflux/tests` (from the repository
root), at 6ce0adf (code identical to the final commit), CPU 12, 03:14 UTC: 86 tests, OK (4 min wall, 3 min CPU). Hub, from `nonlinear/`: `python3 -m unittest boolflux.hub.tests.test_hub boolflux.hub.tests.test_review5_hub`: 36 tests, OK (26 s).

Helper scripts kept in `review5/`: `py_roundtrip.py` (all 426 circuit files through both
formats), `py_prof_best_table.py` (where the old best_table spent its time), `py_timing.py`
(P18). Outputs: `py_curate_dry_run_before.txt`, `py_curate_dry_run_after.txt`.

## Commits (local, branch `boolflux-review5`)

C2 (P1-P3, P5, P7-P16): 9a485e3, 601b896, 9f58ae1, cf0f940, bece408, 6e68a86. Committed by C23
from C2's uncommitted work: 4e96076 (P4, P17, P18), 7370f8d (P19), 4191e08 (P20-P24, MANIFEST.json,
REPRO-CHECK.json). C23: 3fab92c (P25, P26), and the commit with the tests, this file and the docs.
