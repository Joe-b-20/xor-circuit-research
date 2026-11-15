# Documentation audit against the run records (agent L2, 2026-11-15)

Files audited, at commit f9fe6f7: `README.md`, `HOW-IT-WORKS.md`, `HISTORY.md`, `bench/REPORT.md`,
`results/MANIFEST.json` (all under `nonlinear/boolflux/`). Each finding gives file:line, what the
record shows, and the statement that the record supports. [C] = recounted from files by the
scripts in this directory. [H] = my reading. Classes: **wrong** (contradicted by a record),
**unsupported** (no record, or wider than its evidence), **stale** (true when written, overtaken
since), **gap** (true but omits something a reader needs).

"Stale" below is mostly one event: the documentation pass ended at 17:54 UTC on 2026-11-14 and
the hub, the F AD3 runs and the track C sweeps finished after it. One re-curation
(`curate_aes.py`, `manifest.py`, `verify_all.py`, `best_table.py`) and one edit pass would clear
all of those. The wrong and unsupported items need a decision on wording.

**Applied 2026-11-15.** The W, U, S and G items that concern README.md, HOW-IT-WORKS.md, HISTORY.md,
USAGE.md, VERIFICATION.md and bench/REPORT.md were written into those files after this audit (list in
DOCS-TODO.md, "Status on 2026-11-15"). The line numbers below are those of commit f9fe6f7, before the
edits. MANIFEST.json items (W4, U10, S12, G6) are open.

## 1. Checked and correct [C]

* Pin 3d80774: `aes_check.published()` returns 104 forward circuits (92 distinct tuples).
  README.md:34-35.
* The manifest's 41 tuples: recomputed from its 82 distinct AES tuples against the pinned set
  (47 new on the pin, 41 after removing those dominated by ours). All 86 AES files match their
  sha256. README.md:36, HISTORY.md:197.
* "Every published circuit with A <= 31 has G >= 124": the minimum is 28/5/124/27. README.md:45-46,
  HISTORY.md:162-163.
* Mechanism split 20 / 7 / 4 / 6 / 3 / 1 / 1 (42 circuits, 41 tuples) and "11 polishes have a
  join in their lineage". HISTORY.md:199-201.
* Track E final A/B: 41 admissions and 17 frontier points against 4 and 3, 4.7 CPU-h each; low1
  5.9 CPU-h. HISTORY.md:164-168, HOW-IT-WORKS.md:109-110.
* Main queue: 10 of 28 starts, one gain, nine unchanged. HISTORY.md:190-193.
* Benchmark: 1,056 runs (391 + 434 + 131 + 100 JSON files in v1-v4); medians 633 / 749 / 739 on
  naive AES; depth repair 2 of 35. HISTORY.md:94-114, REPORT.md:17-19, 35-37, 171.
* Commit times in the HISTORY timeline that I converted (4958999, 13d5cb8, 417e449, 0659eb9).

## 2. Wrong

| # | where | claim | record | supported statement |
|---|---|---|---|---|
| W1 | HOW-IT-WORKS.md:95-97 | "Every published AES circuit computes the same intermediate functions. After 9-11 level-1 ANDs, the GF(2^4) norm N = x^17 lies in its linear span, and the inversion block's outputs follow." | `strategies/E/analyze_stages.py` on the pinned set (101 circuits it loads; output `~/xs-campaigns/2026-11-15-study/L2/stages.out`): the N part holds: level-1 signals span N in all 101 (9-11 level-1 ANDs in 99 circuits, 17 and 18 in A59 and A60). The inversion part does not: signals spanning N^-1 exist in 54 circuits (all 53 of A32-A53 with AD >= 4, and one A29). They are absent in all 14 A28, 14 of 15 A29, the 4 A30, the 13 AD3 circuits (A35, A46, A47) and A59 / A60. `strategies/F/NOTES.md:157` says the same for AD3 | "Every pinned circuit spans N = x^17 with its level-1 ANDs. The Boyar-Peralta family (A32-A53, AD >= 4) then computes N^-1 as explicit signals after 15-21 ANDs, which is why fronts and backs of that family can be joined there. The A28-A30 and AD3 circuits have no such signals: their later ANDs read forms that mix x with functions of N." This is `strategies/E/NOTES.md:19-22` |
| W2 | HISTORY.md:140-142; also `strategies/D/README.md:79-81`, `D/STATUS.md` | "0 of about 3,900 windows ... on published 103, 116, 124 (A28), 127, 133 and our 108@19, 124@14, 131@13. About 60 % were UNSAT and 40 % ran over a 30k-conflict budget." | `D/t1`, `t3`, `t4` logs: 3,062 windows, 3,337 SAT calls, 0 SAT, 2,399 UNSAT (72 %), 938 unknown (28 %). The 60 / 40 split holds for t1 alone (1,027 / 599). No log exists for NIST 103. t3 (our three circuits) was cut by the outage after 180 windows | "0 of 3,062 recorded windows (3,337 SAT calls: 72 % UNSAT, 28 % over the 30k-conflict budget) on published 116, 124 (A28), 127, 133 and, for 180 of them, our 108@19, 124@14, 131@13." Same change at HISTORY.md:221 |
| W3 | HOW-IT-WORKS.md:85-86 | "the gate level alone stops at 14 (LEDGER section 1)" | LEDGER.md:60 is one 17 s run (14 ANDs). REPORT.md:158 has the gate kernel at a median of 12 ANDs in 60 s (5 seeds, `a,cost`) | "the gate level alone reached 14 ANDs in the ledger run and 12 in the 60 s benchmark runs; 9 needs the skeleton moves" |
| W4 | MANIFEST.json, entries `aes-nist-E-polish-g104-a32-gd29-ad5` and `aes-nist-E-pull-g135-a29-gd17-ad5`, field `mechanism` | "polish: gate kernel ... under caps {'A': 31, ...}" and "depth pull ... (A cap = parent's, AD free)" | the stored circuits have A 32 and A 29: both jobs ended **without meeting their A cap** (kernel logs `E/polish1/A31-parent1-s1.log`, objective 1000104; `E/low1/run/polish/688e861dabceaeab-p3-gd17.log`). `job_caps` shows the cap, `caps` is empty, nothing says "not met" | add `caps_met: false` and say in the mechanism that the result is the kernel's best infeasible state. HISTORY.md:167-168 and `strategies/E/NOTES.md:66-67` do say it for the A29 point; nothing says it for 32/5/104/29 |

## 3. Unsupported (wider than the evidence)

| # | where | claim | what the evidence covers | supported statement |
|---|---|---|---|---|
| U1 | HISTORY.md:135-136 | "No 12-member GF(4)-norm last layer exists over the three fixed front spans tested [C]. That rules out 27 (and 26) only within that family." | `strategies/C/NOTES.md:159-168`: exhaustive only for the cases dim Z = rank = 4 and dim Z = 3, with one fixed gamma per front. Listed there as not covered: dim Z = 2, other gammas, members with an independent N-part, non-GF(4)-norm members, other stage-1 covers | "... over the three fixed front spans, for one gamma each and the cases dim Z = rank = 4 and dim Z = 3 [C]. That excludes 27 and 26 only in those cases of that family." (Later work: the gamma sweep finished 10 / 11 of 16 gammas with 0 hits; H1 reports dim Z <= 2 closed.) |
| U2 | HISTORY.md:147-148; `strategies/D/README.md:88-89` | "Conclusion: these circuits are locally exact-optimal for windows of that size." | windows were sampled at random, not enumerated, and 28 % of the SAT calls were undecided | "No sampled window of 4-9 gates (5-12 in one cut-mode run) could be replaced by a smaller one; 28 % were undecided at 30k conflicts." [H] It also needs the sentence that the encoding looked for fewer gates, not for fewer ANDs at more gates |
| U3 | HOW-IT-WORKS.md:107-108 | "the gate kernel cannot remove an AND from the A32 parents (0 of 8 polishes did)" | 8 runs: 2 starts x 2 seeds x 2 cap sets, 240 s, objective `cost,gd` (`E/polish1`) | "did not in 8 runs of 240 s (two A32 starts, objective cost,gd)" |
| U4 | HISTORY.md:133 | "Every last-layer AND of the A28 circuits is a GF(4) norm." | `strategies/C/NOTES.md:31-39`: checked on two files (a28-ad5-g124, a28-ad4-g131-gd31). The pin has 14 A28 files | "of the two A28 circuits examined" (H1's TRICKS.md may now cover more; cite it if so) |
| U5 | HISTORY.md:153-155 | M1: "no gain from A28 124 at cap A 30/31 or from 104 at cap A31" | `E/arelax1`: one seed, 300 s per arm. For N:104 at cap A31 only the control arm has a result file; the chain arm's run has no JSON (the outage) | add "(one seed, 300 s; the chain arm on N:104 did not finish)" |
| U6 | HISTORY.md:172-174 | "For every frontier circuit, the depth reached by rebuilding every XOR form optimally equals the circuit's GD." | `strategies/F/NOTES.md:16-23`: six circuits | "for the six circuits analysed (116@15, 127@14, 124@14, 131@13, 133@13, 141@12)" |
| U7 | HOW-IT-WORKS.md:59 | "With an iteration budget, the whole run is deterministic for a given seed." | re-run and found identical for two results on 2026-11-13 (108@20, 126@14), before the no-op filter existed. Review 2 found replay deterministic only with `skip_noop 0`. Not re-tested with today's kernel (my second run was stopped to free CPU 12) | add "for a given seed and code version" and cite a test at the release commit |
| U8 | REPORT.md:94-95 | "one worker process per physical core (CPUs 0,2,...,14)" | the i7-13700H has 6 performance cores (2 threads) and 8 efficiency cores; "10 cores x 2 threads" is WSL's synthetic view. [H] CPUs 12 and 14 are then efficiency cores, not second physical cores of the same kind | "one worker per even-numbered WSL CPU; pairs that are compared ran on the same CPU" (the pairing is what makes the comparisons fair) |
| U9 | HISTORY.md:181-182 | "0 of 9 for the other arms" | `strategies/F/NOTES.md:118-124`: gate-old 0/3, gate-new 0/3, osc 0/3, mix 0/1 | "0 of 10" |
| U10 | MANIFEST.json, 47 entries with `reproduction: "deterministic command: every job ended on its iteration budget, so the command gives the same circuit"` | the command reproduces the circuit | Tested here on the entry that matters most, 28/4/133/20: the manifest's command with seed 5, run at f9fe6f7 (code 91246b4809fd), ends its 100,000 iterations at **134 gates with no improvement**; the 2026-11-13 run (code b0e56ecb18fe) reached 133 at iteration 56,529. With `--set skip_noop=0` added, f9fe6f7 gives the identical gate list: the no-op filter (default since 7ae20c8) changes the trajectory, as USAGE.md already says for the 108 replay. Section 7 has the test with the run's own binary | "deterministic for its seed, settings and code: with later code add `--set skip_noop=0`, or use the run's own `src/` and `bin/` snapshot. Re-run and confirmed for 3 of 49" |

## 4. Stale

| # | where | claim | now |
|---|---|---|---|
| S1 | README.md:36-38, 40-43; HISTORY.md:197-206 | 41 new tuples; table of fewest gates per depth cap | The manifest was last curated 17:54 UTC 11-14. `~/xs-campaigns/2026-11-14-hub/best/BEST.md` has 61 rows. Changed cells: GD <= 16 113 -> **112** (33/4/112/16); GD <= 17 112 -> 112 (the GD16 circuit); new column GD <= 20: published 108, ours **107** (33/4/107/20); GD <= 21 is then the same circuit. 129, 121, 115, 110, 108 and 104 stand |
| S2 | README.md:45-46 | "circuits with 29 and 31 ANDs at GD 16-28 ..., A28 circuits at GD 14-25, AD3 circuits at GD 13-25" | also A30 circuits (30/4/139/16, 30/4/130/20), A29 at AD4 (29/4/148/15, 140/16, 130/22), 28/5/127/22, 28/5/130/19, 28/4/131/23 |
| S3 | README.md:66 | "`strategies/C,D,E,F/` AES-push track code with NOTES (not yet committed)" | committed in 377b03f (C-G) and f9fe6f7 (H, R). Track D has README.md, not NOTES.md. G, H1-H4, R1-R2 and the token-phase directories are missing from the row |
| S4 | README.md:13, 67; HOW-IT-WORKS.md:121-136; HISTORY.md:226-231; runs/INDEX.md:51 | the hub is "in progress", "no result on this page comes from it", "later linres and generators", "not yet documented" | built and measured (97abda7, f9fe6f7; `strategies/E/NOTES.md:75-138`): hub 8 new points against 2 in the first A/B; osc and gen_skel adopted; linres measured and not adopted; long3 16 new points in 30.1 CPU-h |
| S5 | README.md:68 | reviews listed: review, review2, review3, audit | `review4/` exists (f8a26e3) and changed the kernel's acceptance step |
| S6 | HISTORY.md:12-14 | strategy code and hub "had not been committed" | committed (S3, S4) |
| S7 | HISTORY.md:39, 136, 185-186; runs/INDEX.md:38, 41 | track C's runs and F's AD3 runs "still running" | F ad3b ended 22:50 UTC with 35/3/177/13, 35/3/162/14, 35/3/142/22, 40/3/172/13, 39/3/156/15. C's gamma sweeps were stopped about 23:55 UTC with 0 hits in every finished gamma. None of this is in the manifest; `C/STATUS.md` and `strategies/C/NOTES.md` still list the sweeps as running |
| S8 | HISTORY.md:74-78 | six of the first twelve tuples "are still on the Pareto front" | 32/4/122/18 is now dominated by 32/4/121/17 and 32/4/119/18. The other five stand in the hub table |
| S9 | HISTORY.md:40 | curation at "17:40-17:47" | every `curated_utc` in the manifest is 17:54 |
| S10 | REPORT.md:33-34, 173, 183-186 | the 124@GD14 A38 point is "new", "not dominated by any of the 102 published circuits and 3 gates below the best published G at GD <= 14 (127)" | written against pin e6ac0d0. At 3d80774 (104 circuits) the published best at GD <= 14 is 125 (A33), and the 124 is strictly dominated by our 37/4/121/14. REPORT section 7 corrects other numbers but not this |
| S11 | README.md:17, 21 | LEDGER.md and CHECKPOINT.md are linked as current pages | both are against pin e6ac0d0 (LEDGER has a banner, CHECKPOINT has none); DOCS-TODO.md item 11 |
| S12 | MANIFEST.json `aes_pareto` | 41 tuples | at least these are superseded by circuits that exist with aes_check output but are not in the manifest: 35/3/180/13 (by 177), 35/3/163/14 (by 162), 40/3/174/13 (by 172), 35/3/143/23 (by 142@21), 31/5/115/28 (by 114@28), 31/5/123/18 (by 121@18), 29/5/135/17 (by 134@17), 33/4/113/16 and 112/17 (by 112@16), 33/4/107/21 (by 107@20), 32/4/122/18, 32/4/115/24 (by 115@22), 28/4/131/25 (by 131@23), 43/4/142/12 (by 141@12) |
| S13 | `strategies/F/NOTES.md:148` | "116@GD15 ... repairs in 1/35 runs of 120 s" | 2 of 35 after review 3 (REPORT.md:277) |
| S14 | DOCS-TODO.md item 7 | strategies untracked | resolved by 377b03f; the manifest's `code_version` still says "uncommitted, sha256 now" |

## 5. Gaps (true, but a reader of the published text would be misled)

| # | where | gap |
|---|---|---|
| G1 | HOW-IT-WORKS.md:54-58 | "A feasible state is never left for an infeasible one, so a cap can never be traded for a lower objective." True from a feasible state. Not said: (a) while a start is being repaired, excess on one cap can be exchanged for excess on another (an A28 circuit became A29 under cap A28 while its depth was repaired); (b) a run that never becomes feasible still writes its best infeasible circuit, and the track E drivers admitted such circuits by their metrics. Two of the 41 tuples arose that way (W4) |
| G2 | README.md:45-48, HISTORY.md:208-211 | "one-off" is stated, but not how the A <= 31 results split: every A28 and A29 result of the push is one time-budgeted kernel job that was never repeated; the A31 results are deterministic joins plus one-off polishes. The only A <= 31 result with a deterministic command is 28/4/133/20, on pre-review-3 code |
| G3 | HISTORY.md:164-168, HOW-IT-WORKS.md:109-110 | the 17-against-3 A/B is reported without the caveat that all 26 join admissions came in the first 8.6 minutes of 2.3 hours (14 of the 17 points are those joins or polishes of them); after that the arm is a polish arm with better starts. [H] The measured effect is "new starts", not sustained join yield |
| G4 | HISTORY.md:138-149 | track D is reported as a failed mechanism. Not said: its objective was gate count at fixed caps. No window run ever asked for one AND fewer at a free gate count |
| G5 | HISTORY.md:116-119, README.md:46-47 | the push's stated goals include A < 28. Not said: no kernel, window or chain run before the hub had an AND-first objective or an A cap below its start's A (all recorded AES summaries are `cost`, `cost,gd` or `gd,cost`), apart from the 8 polish1 runs with cap A31 |
| G6 | MANIFEST.json | (a) `time_to_result_s.within_job_s` is null for the 10 long1 polish entries; (b) `aes-nist-main-flow-g175-a28-gd14-ad4`: `within_job_s` 960.2 exceeds `job_budget_s` 900; (c) two F entries have `seeds: ["see cmd"]`; (d) track F's kernel is identified by a 4-byte hash prefix; (e) 36 entries: `code_version` is a hash taken at curation, not at run time |
| G7 | HISTORY.md:34, REPORT.md:94 | CPU-hours are compared across tracks as if CPUs were equal. [H] CPUs 12-19 are probably efficiency cores (U8); low1, D's fair test, the main queue, tracks C and G ran there |
| G8 | HISTORY.md:7 | "converted from the repository's -0500 timestamps": 4958999 is -0400 (its listed UTC time is right) |

## 6. Other documents noticed in passing

* `strategies/D/README.md:79-89` and `D/STATUS.md`: W2 and U2 originate here.
* `~/xs-campaigns/2026-11-13-aes/best/BEST.md`: section title "Fewer ANDs than any published
  circuit except A = 28 (29 <= A <= 31)" is wrong (the pin has 15 A29 and 4 A30 circuits);
  DOCS-TODO.md item 1. The hub's BEST.md has the corrected title.
* `hub/SPEC.md` "34 frontier admissions in ~1 h vs 2": DOCS-TODO.md item 12, still open.
* `strategies/E/NOTES.md:44`: "from the A32 parents it never reaches A <= 31 (0/8 feasible)" is
  correct; it does not say that those infeasible runs are where 32/5/104/29 came from.

## 7. Tests run for this audit (details in `NOTES.md`)

* [C] Joins: the first A31 join and all 29 join admissions of long1 and low1 were rebuilt from
  their recorded parents and cut levels (`rejoin.py`): 30 of 30 identical. The seven manifest
  entries "deterministic construction ...; not re-run" can be changed to "re-run 2026-11-15,
  identical".
* [C] 28/4/133/20: the run's own binary with a copy of its cfg gives the byte-identical circuit
  (133 at iteration 56,529). The manifest's command at f9fe6f7 with seed 5 ends at 134 with the default settings and
  gives the identical gate list with `--set skip_noop=0` (U10).
* [C, n = 3 per arm] 32/5/104/29: a paired probe shows that its unmet A31 cap is incidental
  (W4 stands as a record defect; the mechanism is the released depth cap).
