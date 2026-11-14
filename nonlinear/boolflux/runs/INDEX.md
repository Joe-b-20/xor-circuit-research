# Campaign folders

All of these are outside the repository, under `~/xs-campaigns/`. Descriptions come from the
folder contents, their `summary.json` commands, and the documents cited. "Results" means
circuits copied into [../results/](../results/).

## 2026-11-13-boolflux: first study (2026-11-13)

| folder | what |
|---|---|
| `sanity/` | first sanity runs (maj3, fulladd, GF(2^4) mult/inv) from before run snapshots existed; results in `results/_superseded/` |
| `sanity-2/` | the sanity cases re-run with snapshots ([../LEDGER.md](../LEDGER.md) section 1; `results/reports/sanity-2.md`) |
| `sb4/` | PRESENT `bgc` test run |
| `aes-anf-1/` | AES from the naive ANF start, `cli.py run --objective cost --iters 300000 --seeds 1-8` |
| `probe/`, `probe2/` | skeleton-level probes from NIST's 104@GD30 (`pipe --skel-share 1`) |
| `frontier-fwd-1/` | first per-circuit frontier runs (3 NIST circuits) |
| `frontier-fwd-2/` | the 46 forward circuits of pin 0876577 under their own caps (`campaigns/nist_frontier.sh`; LEDGER 3b; report `frontier-fwd-2.report.md`) |
| `frontier-fwd-3/` | the 32 forward circuits new in e6ac0d0, same protocol (LEDGER 3b) |
| `depth-2/`, `depth-3/`, `chain-1/` | gate-depth chains and repairs, GD 10-30 caps from NIST starts (`campaigns/depth_chain.sh`, `depth_frontier.sh`); failed attempts in `FAILED/` |
| `aes-starts/` | Boyar-Peralta 113 and naive ANF starts, with and without caps (LEDGER 3a) |
| `small-1/`, `small-2/`, `small-3/` | small S-boxes from naive starts; `small-2` is LEDGER section 2, `small-3` the chi3 re-run against the spec table |
| `focus/` | longer RECTANGLE and Midori Sb1 BGC runs (20 seeds x 5 rounds x 400,000 iterations, no change) |
| `repro/` | from-scratch re-runs of the 108@GD20 (`g109`) and 126@GD14 (`gd14`) results: identical gate lists |
| `traces/`, `repro-trace/` | move traces of the worked examples (bench/REPORT.md section 2) |
| `bench/` | method-and-performance benchmark rounds v1-v4 and plans (bench/REPORT.md, bench/REPRODUCE.md); `v3/A-aes-gd14repair-rebuild-s4-v3.json` is the run of the 124@GD14 result |
| `ext/` | Berkeley ABC build, genlibs, scripts and results (REPORT 4.4) |
| `xf-probe/` | an XORFlux probe run used for the linear-map comparison |
| `speed/`, `prof/` | kernel speed and gprof profile |
| `nist-e6ac0d0/`, `nist-import-test/` | the e6ac0d0 NIST import and its test |
| `papers/` | text of Zhang-Huang 2023 (ePrint 2023/1721) |
| `review-bundle/` | review bundle (`bench/make_bundle.sh`) and its `.tar.gz` |
| `pareto-final.json`, `pareto-final.md` | `campaigns/pareto_audit.py` output of that day |

## 2026-11-13-aes: AES push (2026-11-14)

| folder | what |
|---|---|
| `C/` | track C, fewer than 28 ANDs: `STATUS.md`, `logs/` (exhaustive `zdfs` runs, gamma sweeps still running at 17:30 UTC), `papers/`; `found/` empty (no circuit below 28) |
| `D/` | track D, SAT windows: `STATUS.md`, `t1-t4/` and `br1/` (window tests and early breathe runs on published 116/124/127/133), `bench/` (full vs incremental encoding), `fair/` (final breathe vs kernel-alone test, queue.log), `found/` (3 kernel-stage circuits) |
| `E/` | track E, joint AND/XOR: `STATUS.md`, `STATUS-live*.md`, `ab_final.json`; `smoke/` (chain and kick smoke tests), `screen1/`, `screen2/` (ejection-chain screens on a36), `arelax1/` (chains from A28 with the A cap relaxed to 30), `asmall1/` (chain vs control from published A29 starts), `sp1/` (join sweep, 4 shards), `polish1/` (polishes of joins vs parents), `memtest/`, `long1/` (splice and control arms, `log.jsonl`, `admitted/`, `frontier.json`), `low1/` (low-AND run), `found/` (+ `found/final/`) |
| `F/` | track F, low gate depth: `STATUS.md`, `e1/` (kernel from feasible starts), `inv/` (depth-3 inversion designs and splices), `bot/` (bottom transplants), `ab/` (A/B rounds 1-3; `ab-aborted/` an aborted first attempt), `rep/` (cap-repair baseline), `pool/`, `pool6/`, `starts/`, `snap/`, `snap-new/` (kernel snapshots), `test/`, `ad3/` (AD3 runs from 17:31 UTC, still running; `*-aborted-1731` the first attempts), `found/` |
| `main/` | main-track queue (`queue.py`, `queue.log`): `cli.py flow --config gate` convergence runs, 900 s x 4 seeds, `conv/<start>/` (10 of 28 starts done) |
| `noopAB/` | review-3 no-op filter A/B, plan v5 (bench/REPORT.md section 7) |
| `control/` | empty |
| `best/` | `best_table.py` output (`BEST.md` + NIST-named copies). Files from an 11:17 local run and the 12:26 local run sit side by side. `BEST.md` is the 12:26 one (38 rows; the 41-row current table comes from `best_table.py --out DIR`) |

## 2026-11-14-hub: hub architecture (started 2026-11-14, in progress)

| folder | what |
|---|---|
| `abhub/`, `abmem/`, `main/`, `seed.list` | first hub runs ([../hub/SPEC.md](../hub/SPEC.md)); written by the hub agent, not yet documented |
