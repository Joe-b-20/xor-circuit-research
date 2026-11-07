# Depth-3 MixColumns proof work: replay record (2026-11-07)

Working directory: `~/xs-campaigns/2026-11-07-sprint/d3replay/` (WSL Ubuntu 24.04, Python 3.12.3,
g++ 13.3.0, kernel 6.6.114 WSL2, 20 cores). Machine load during all runs: load average 24-26
(19 other processes). Every replay ran alone, under `nice -n 8` and `timeout`. Both packages were
copied into `d3replay/` first; the repository and the archive were only read.

Everything below was treated as unverified until replayed here. "Replayed here" means the named
program ran to completion in this directory on this machine and exited 0 with the stated output.

## 1. Package A: public depth-3 lower bound 93

Source: `~/xor-circuit-research/lower-bound-proofs/mixcolumns-lb93-depth3/` (repository edition of
29 Oct 2026), copied to `d3replay/A/lb93/`.

### Command

`verify_all.py` does not accept a `--full` flag (its argparse has only `--quick`,
`--check-package`, `--extract-source`); its default mode is the full replay and internally runs
`python3 -u verify_complete_92_exclusion.py --full` in a fresh temporary extraction. The command
prescribed by README/REPRODUCE and run here (`run_A.sh`, log `logs/A_run.log`):

    cd d3replay/A/lb93 && nice -n 8 timeout 2400 python3 verify_all.py

### Result

| Item | Value |
|---|---|
| Exit code | 0 |
| Wall time | 2,028 s (summary timestamps 22:33:47.5Z to 23:07:35.9Z; shell START/END agree) |
| `summary.json` `seconds` field | 2,077.639 (overstates its own timestamps by about 49 s; perf_counter artefact under WSL2) |
| Verdict | **PASS** (`Full proof verification: PASS`) |
| Run record | `A/lb93/verification/run_20261107T223347_544417Z/` (`summary.json`, `full_verification.log`, 15 `*_checks.json`) |
| Log SHA-256 | `985813c71295ca8ca043f3ad44f8d7e36362ae7498bc972cffbc90c4480828cd` |
| Source archive SHA-256 pinned by the inventory | `007792f8be74bba470ad534b6149cc1f8d6c1374acf34e02a880b67fbc3d229b` |

Replay counts next to the two prior audits:

| Quantity | This replay | Oct-23 audit (in package) | Nov-4 audit (`baseline_bounds.md`, "93 at depth three") |
|---|---:|---:|---:|
| Source-inventory entries hash-checked | **1,216** (+ 4 supplement files) | n/a (ran from source archive) | **1,222** |
| Status / lower bound / interval | PASS / 93 / [93, 97] | PASS / 93 / [93, 97] | PASS / 93 |
| `reused_completed_checks` / `source_certificate_checker_rerun` / `known97_rechecked` | false / true / true | false / true / true | false / true / true |
| Six-component partitions (forest + parent-price + Farkas; uncovered) | 275,354 (271,718 + 96 + 3,636; 0) | same | 275,354; 0 |
| Seven-component partitions (parent-price + pair-recipe + Farkas; uncovered) | 22,060 (18,404 + 2,840 + 816; 0) | same | 22,060; 0 |
| Eight-component branch (surviving; parent-price; pair-recipe) | 110,712; 1,552; 109,160 | same | 110,712 |
| Conditioned Farkas partition certificates | 1,113 PASS | 1,113 | 1,113 |
| Forest obstructions | 20,933 | 20,933 | 20,933 |
| Seven-component pair-recipe orbit representatives | 710 | 710 | 710 |
| Frozen source certificate | 16,868 rows / 61,673 variables; 8 local oracles, 1,312 consistency, 192 parent-forest, 58 parent-tree rows | same | (not itemised) |
| 97-gate control / 26-pair 100-gate control | satisfy all rows | same | 97-gate control reverified |
| Wall time | 2,028 s (loaded machine, nice 8) | 998.7 s | 962.1 s |

This run's `full_verification.log` (772 lines) and the Nov-4 audit's
`baseline_fresh_receipts/lb93/full_verification.log` (772 lines) are **identical after removing
timing lines** (filtered `diff`: 0 lines). Zero `FAIL`/`Traceback`/`error` lines in the log.

### Disagreements and notes for A

1. **1,216 vs 1,222 inventory entries** is an edition difference, not a proof-content difference.
   The Nov-4 audit replayed the 27-Oct "source-complete repair" edition
   (`audit_work/AES_MixColumns_Depth3_LB93_2026-10-23/.../REPAIR_2026-10-27.md`), whose inventory adds
   six `technical/inherited/` modules (`build_lp, certify, cuts, finite_facts, mcmatrix, model3`)
   recovered from the 2026-10-17 source ZIP. The repository edition keeps the 1,216-entry inventory
   (its `source_inventory.json` hash `fe4b1968...` equals the 23-Oct ZIP edition's) and instead stages
   four modules from `supplement/` (from `slp-plateau-search` commit `bdcf83be...`). All 1,216 common
   entries have identical hashes in both inventories; the six modules are the only extras.
2. **The four supplement modules differ from the archived originals by exactly one trailing blank line
   each** (`logs/supplement_diff.txt`: `build_lp.py` 8,015 vs 8,016 B, `cuts.py` 7,780 vs 7,781 B,
   `mcmatrix.py` 1,237 vs 1,238 B, `model3.py` 3,639 vs 3,640 B; `diff` shows one added empty last
   line). Semantically identical Python; the supplement README already says a byte match to the source
   ZIP "is not established". `certify.py` and `finite_facts.py` are absent from the repo edition and were
   not needed (the replay passed).
3. The wrapper writes its run directory inside the package copy (`A/lb93/verification/run_*`); the
   repository copy was not touched.

## 2. Package B: "MixColumns Ordinary Union Checkpoint" (2026-11-05)

Source: `~/xs-campaigns/2026-11-07-sprint/import/zip/research/MixColumns_Ordinary_Union_Checkpoint/`
(browsing tree) plus the archive manifests; archive source ID `S000001`
(`xor/MixColumns_Ordinary_Union_Checkpoint.zip`, SHA-256 `35a44893...`).

### Restoration (needed)

The browsing tree holds 472 files; `ordinary_completion/CHECKPOINT_MANIFEST.json` lists 480. Checking
the raw copy against that manifest (`check_B_manifest.py`): 471 ok, **9 missing**, 0 mismatched:

    normalization_contract/inputs/aes_forward.mat.txt
    ordinary_completion/RESUME.txt
    ordinary_completion/constructor_audit/constructor107_control_{2,5,8,9}.txt
    ordinary_completion/two_group_audit/upper_cross_independent_replay.json   (hash-checked by verify_checkpoint.py)
    structural_tradeoff/boundary/general_floor_replay.json
    structural_tradeoff/core_equality/exhaust_bank_union.cpp

Without restoration the default replay fails at its first step (receipt hash of
`upper_cross_independent_replay.json`). Restoration (`run_B_restore.sh`, log `logs/B_restore.log`):

    nice -n 8 timeout 1200 python3 -I import/zip/tools/restore_checkpoint.py --archive-root import/zip \
        --source S000001 --destination d3replay/B/restored --public-repo ~/xor-circuit-research

Result: `complete_regular_files`, 481 files restored, 0 missing or failed, 21 s. All nine files were
resolved from other occurrences inside the archive (deduplicated copies); `public_resolution_messages`
is empty, so the public repository was not actually consulted and nothing in it was touched.
Post-restoration manifest check: **480/480 ok, 0 missing, 0 mismatched** (extras: `RESTORE_README.md`,
`RESTORE_REPORT.json`, the manifest itself).

### What `ordinary_completion/verify_checkpoint.py` checks (read from the source)

Default mode runs these in order; a PASS requires every step:

| # | Step | Mechanism | Claim it bears on |
|---|---|---|---|
| 1 | `receipt_hashes(two_group_audit/audit_receipt.json)` | SHA-256 of 6 files (theorem note, audit note, two `.cpp`, two result JSONs) | two-group bound: integrity of the audited artefacts only |
| 2 | minimum-first receipt hashes | SHA-256 of `minimum_tau_probe.py` (author), the independently executed copy, its output, the audit note | 2,808-plan census: integrity only |
| 3 | `core_ranges()` | reads the 5 saved colored-search shards: statuses `INCOMPLETE`/`UNSAT_RANGE`, caps 17/16, no witness masks, contiguous ranges ending at 315, W leaves summed (49,683,204) | H0 = 16 => two original CC pairs: **saved** coverage, not rerun in default mode |
| 4 | `core_interface/check_constructor_model.py` | regenerates the 567-identity footprint input (rows 315 x 4 and 639 x 4) from first principles and compares | same: the search **input** is reproduced |
| 5 | `core_audit/check_coverage.py`, `check_provenance.py`, `check_search.py` | disjoint-coverage arithmetic over the fresh first-44 prefix plus 4 saved shards, with source/input hashes; mapping of three actual circuits into the model; recompiles `exhaust_colored.cpp` and compares it with brute-force Cartesian enumeration on 300 small queries | same: coverage bookkeeping, provenance controls, search-code sanity |
| 6 | compile and run `two_group/check_upper_cross_floors.cpp` | 7 exact integer bank exclusions (`one_cross_excludes6` ... `charge8_two_cross_both_endpoints_repeated_exclusion`), all 0 violations | two-group bound: its finite upper exclusions |
| 7 | compile and run `two_group_audit/check_compatibility_floors.cpp` | six confined comparison floors, status PASS | two-group bound: its finite comparison floors |
| 8 | `constructor_audit/replay.py` | compiles the unpruned `plain_oracle.cpp`; reconstructs the fixed-parent problem independently; confirms every component minimum for `known97` (28 pairs, 97 gates) and the relaxed forest (40 pairs, 107 gates); 1,000 differential small cases against the root solver; rejects a malformed incumbent | fixed-parent minima 97 / 107 |
| 9 | `boundary/check_boundary49_counterexample.py` | re-evaluates the 124-gate circuit on all 32 AES basis columns, depth 3, birth legality; runs the frozen global and joined certificate verifiers; recomputes the literal boundary set; asserts `actual_floor_left == 48` | 124-gate counterexample (floor 49 false) |
| 10 | `two_group/targeted_controls.py` | builds the two tight n5 = 2 companion alternatives inside full AES circuits and checks them | two-group bound: targeted controls |
| 11 | `boundary/minimum_tau_probe.py` | reruns the census; asserts `EXHAUSTED` and counts equal to the receipt (468 / 211,631,616 / 17,625,600 / 108 / **2,808**; tau 4: 324, 5: 1,764, 6: 720) | 2,808-plan census rerun |
| 12 | `boundary/replay_minimum_tau_control.py` | embeds the census's minimum-tree plan into the 97-gate circuit and checks frozen global and joined certificates (full-AES control, F34 = 7) | census graph/birth control |
| opt | `--full-core`: compile `exhaust_colored.cpp`, run roots 0..315 with caps 17/16; require `UNSAT_RANGE`, `completed_end == 315`, no witness | H0 = 16 => two original CC pairs: the exhaustive search itself (timed out here) |

Premises that are **text only** (no program checks them): `TWO_GROUP_UNION.md` (the reservation and
compatibility argument reducing the two-group theorem to the finite floors of steps 6, 7 and 10);
`CORE16_CC_PROOF.md` and `core_audit/AUDIT.md` (that every actual circuit maps into the footprint
relaxation, and the original-CC provenance before native-C normalization); `MINIMUM_TAU_PROOF.md`
(that the census filters are exactly the minimum-first equality case); the ledger definitions
(`a0, H0, L, F34` and `G = 47 + a0 + L + F34`); and all of ROOT_REVIEW section 4
(`L >= H0 + qCC + 18`, the scalar sufficient condition, the residual pattern
`H0 = 17, a0 = 13, qCC = 0, F34 = 1`), which is arithmetic composed from the above and is executed by
no script.

### Default replay

Command (`run_B.sh default`, log `logs/B_default.log`):

    cd d3replay/B/restored && nice -n 8 timeout 1800 python3 ordinary_completion/verify_checkpoint.py

Output:

    {"status": "PASS", "full_core_rerun": false,
     "core_saved_coverage": {"covered_W0_roots": 315, "complete_W_leaves": 49683204},
     "boundary_counterexample_left": 48, "global97_certified": false}

Exit code 0, **wall 49 s** (23:07:56Z to 23:08:45Z). No missing dependency after restoration (Python
3.12 and g++ 13 sufficed; SciPy not needed). Fresh `portable_replay.json`: two-group receipt hashes 6;
upper floors PASS (7 cases, 0 violations); compatibility floors PASS; fixed-parent oracle "independent
full exclusions and 1000 differential cases passed"; counterexample G = 124, depth 3, a0 = 13, H0 = 17,
L = 35, F34 = 29, original CC empty, left side 48, refuted floor 49, 32 direct AES basis checks;
targeted two-group controls PASS; minimum-first branch PASS with the counts above.

Files the default replay regenerated (compared with the archived copies by `compare_B.py`, timing and
node counts ignored): `boundary/minimum_tau_probe.json` (EXHAUSTED, equal), `constructor_audit/results.json`
(PASS, equal), `core_audit/search_checks.json` (PASS, equal), `portable_replay.json` (PASS; the archived
copy additionally carries a key `replayed_from_fresh_extraction` that the shipped script never writes,
so the archived receipt was not produced verbatim by this script). Side products: compiled binaries
`constructor_audit/plain_oracle` and `core_audit/exhaust_colored_fresh`, `__pycache__` directories.
The default run's `portable_replay.json` is kept in `logs/B_default_outputs/`.

### `--full-core` replay

Command (`run_B.sh fullcore`, log `logs/B_fullcore.log`), started 23:10:15Z:

    cd d3replay/B/restored && nice -n 8 timeout 1800 python3 ordinary_completion/verify_checkpoint.py --full-core

Result: **NOT COMPLETED. Exit code 124 (`timeout`), wall 1,752 s (23:10:15Z to 23:39:27Z).**
The default-mode steps reran, then the fresh `exhaust_colored.cpp` binary (`core footprints 17 0 315 0`,
single-threaded) was still inside its search when the 1,800 s cap expired; `verify_checkpoint.py` was
killed before writing a record, so `portable_replay.json` is still the default-run file and contains no
`core_fresh_full_exclusion`. No orphan process remained; the killed run's temp dir was removed.
Why it did not fit: the five saved shards (`core_interface/colored_*.json`) record 55.0 + 271.5 + 244.3
+ 233.4 + 216.5 = 1,020.8 s of CPU on the owner's machine; here one process at `nice -n 8` on a
load-25 box received well under a full core. A rerun needs an idle machine or a cap of at least 2,400 s,
or the shards run separately with the same binary (`core footprints.txt 17 <start> <end> 0`, e.g.
44-112, 112-180, 180-248, 248-315, 4-5 CPU-minutes each) and compared with the saved shard counters.
Consequence: the exhaustive 315-root colored search was **not** replayed here; only its saved coverage
and the default-mode controls (section "Default replay") are.

## 3. Scope statements (what is now verified by replay here)

### A. `93 <= C3` [replayed here]

Scope: depth <= 3 (inputs at depth 0, every output at depth at most 3), one 32-bit forward AES
MixColumns column, two-input XOR gates, otherwise unrestricted (sharing, fan-out, cancellation and
asymmetry allowed). Computer-assisted: the replay establishes that the package's finite checks and
exact certificate arithmetic pass (all 1,216 inventory hashes; the local, boundary and weighted-cluster
premises; `P >= 26`; the 16,868-row rational tradeoff `3P + 4T + 4Q >= 214`; complete six-, seven- and
eight-component partition regeneration; 1,113 Farkas certificates; 20,933 forest obstructions; 710
pair-recipe orbits; 1,552 + 109,160 eight-component exclusions; exact set-union coverage with 0
uncovered partitions; the 97-gate depth-3 witness). The mathematical reductions (lossless normal form,
completeness of the recipe model, universality of the inequalities, completeness of the enumerators)
were **read, not checked** here; the package itself says they need expert review. Upper bound 97 is
replayed; the optimum in [93, 97] is unresolved; nothing is claimed for depth > 3.

### B. Accepted local results of the Ordinary Union checkpoint

Replayed here in default mode (49 s, PASS):

- **124-gate counterexample** (boundary floor 49 is false): fully covered. The circuit is re-evaluated
  from raw gates against the AES matrix, depth and gate count recomputed, frozen certificate verifiers
  rerun, the literal left side 48 recomputed.
- **Fixed-parent minima 97 (known97) and 107 (nominal-95 forest)**: covered by an independent unpruned
  enumeration (`plain_oracle.cpp`) of every component plus 1,000 differential cases. As stated, it fixes
  the final parents and does not optimise them.
- **2,808-plan census** (minimum-first pure-tree case needs >= 4 tree components): the census was rerun
  to `EXHAUSTED` with identical counts (2,808 plans; tau >= 4 for all: 324 + 1,764 + 720) and its
  full-AES graph control rerun. Not covered: that the census's explicit filters coincide with the
  mathematical minimum-first case (text premise).
- **Two-group union bound** `|J5 u J6 u R56| >= 6 + beta(t) + |Z|`: its finite ingredients were rerun
  from source (7 upper-cross exclusions, six compatibility floors, two targeted companion controls) and
  the audited artefacts hash-checked. Not covered: the theorem's reduction to those finite floors
  (`TWO_GROUP_UNION.md`, audit text) is read only.
- **H0 = 16 => at least two original CC pairs**: in default mode covered only as saved evidence plus
  controls: the five saved shards' coverage of roots 0..315 and 49,683,204 W leaves re-added and
  structurally validated, the search input independently regenerated and matched, the first 44 roots'
  fresh prefix counters matched, the search binary recompiled and agreeing with brute force on 300 small
  queries, three actual circuits mapped into the model. The exhaustive 315-root search itself would be covered
  only by `--full-core`, which **timed out here** (section 2), so it is not replayed. Not covered either way: the model reduction (`CORE16_CC_PROOF.md`)
  that an actual circuit with H <= 16 and H + |K| <= 17 yields a feasible footprint selection.

Not replayed by anything here: the derived statement that in the four-borrowed-carrier branch only the
pattern `H0 = 17, a0 = 13, originalCC = 0, F34 = 1` remains (ROOT_REVIEW section 4), and, as the
checkpoint itself says, global 97@3 optimality (`global97_certified: false`).

## 4. Failures and disagreements

- A: PASS, exit 0. B default: PASS, exit 0. **B `--full-core`: did not finish (timeout 124 at 1,752 s wall; see section 2); the full 315-root core search remains unreplayed here.**
- A: inventory size 1,216 here versus 1,222 in the Nov-4 record is an edition difference (six
  `technical/inherited/` modules in the 27-Oct repaired inventory versus four `supplement/` modules
  here); the four supplement files differ from the archived originals by one trailing blank line each;
  `certify.py` and `finite_facts.py` are absent from the repo edition. Proof counts, statuses and the
  timing-filtered full log agree exactly with the Nov-4 run.
- A: `summary.json` `seconds` (2,077.6) exceeds the interval between its own timestamps (2,028.3 s).
- B: the browsing tree is not runnable as-is (9 deduplicated files); the archive's restoration helper
  fixes this from the archive alone. The archived `portable_replay.json` carries a key the shipped
  verifier does not write.

## 5. Files in `d3replay/`

- Scripts: `setup_copies.sh`, `run_A.sh`, `run_B_restore.sh`, `run_B.sh`, `wait_A.sh`, `wait_A2.sh`,
  `check_B_manifest.py`, `compare_B.py`, `inspect_B.sh`, `diff_supplement.sh`.
- Records: `logs/A_run.log` and `A/lb93/verification/run_20261107T223347_544417Z/` (A full record);
  `logs/B_restore.log`, `B/restored/RESTORE_REPORT.json`; `logs/B_default.log`,
  `logs/B_default_outputs/portable_replay.json`; `logs/B_fullcore.log`; `logs/B_inspect.txt`;
  `logs/supplement_diff.txt`.
- Working copies: `A/lb93/`, `B/ckpt_raw/`, `B/restored/` (repository and archive untouched).