# Ledger: campaign 2026-11-15-targets

Generated 2026-11-16T13:19:47Z by `nonlinear/boolflux/campaigns/targets/ledger.py run` (3.3 s). Do not edit; rerun.

- NIST pin 3d807741f937d29d3bef4f32f142ccda0cda9070: 207 manifest files, all sha256 match. Comparison set: every forward AES S-box circuit in `nonlinear/nist/` (`aes_check.published()`: aes-sbox/, old-2020/, sbox/).
- Baseline ("known"): archive as of 2026-11-15T15:20:00Z (built 2026-11-15T15:34:56Z), 4162 files, 4162 verified AES S-box circuits.
- Second snapshot ("known-by-23:50"): archive and campaign found/ files as of 2026-11-15T23:50:00Z (built 2026-11-15T23:56:31Z), 4562 files, 4562 verified: the results of the 2026-11-15 campaign day. Night runs: `~/xs-campaigns/2026-11-16-night/*/found/`.
- Scanned: 4162 archive files, 614 campaign files; 4776 verified OK (all 256 inputs, two verifiers, NIST library); 0 checked this run; 0 archive files are not forward AES S-box circuits or fail.
- Rules (from TARGETS.json, recomputed every run): hard A <= ref A, AD <= ref AD on every recorded result (search states may exceed the caps, user 23:50 UTC). strict: G <= ref G, GD <= ref GD, one strictly smaller. tradeoff gates_for_depth: ref GD < GD <= GD_max and G <= ref G - 3; depth_for_gates: GD <= GD_max (< ref GD) and ref G < G <= ref G + 8; and_depth_for_gates: AD < ref AD, AD <= max(AD_targets), G or GD above ref (a circuit matching several kinds takes gates_for_depth first). Tradeoffs never dominate the reference. Notable: T03 G <= 123 at any GD; T05 G <= 102 at any GD.
- Status: known = tuple realised by a 15:20 baseline archive file; reproduced = campaign circuit structurally equal (hub.common.structure_key) or tuple-equal to a baseline circuit; known-by-23:50 = first realised by the 11-15 campaign (a file of the 23:50 snapshot; new against the archive); new = first realised after 23:50 (night runs). Evidence: every row is [C] for "this file computes the AES S-box with this (A, AD, G, GD)"; "new"/"dominated" are [C] relative to the scanned folders and the pinned set only.
- Search path ("path" columns): certified | reproduced-certified | not certified | unknown (COMPLIANCE-1820.md); **informational only** from 23:50 UTC (BRIEF2 decision 2): it never demotes a result.

## Summary

| target | reference | best strict (by G) | best strict (by GD) | best tradeoff | notable (any GD) | (G,GD) frontier points |
|---|---|---|---|---|---|---|
| T01 | 28/4/132/22 | 28/4/131/22 [known; reproduced by night:T01] | 28/4/132/20 [known; reproduced by night:T01] | - | - | 9 |
| T02 | 28/4/176/14 | 28/4/174/14 [known-by-23:50 (P2; new vs archive); reproduced by night:T02] | 28/4/174/14 [known-by-23:50 (P2; new vs archive); reproduced by night:T02] | - | - | 9 |
| T03 | 28/5/128/20 | - | - | - | G <= 123: none | 11 |
| T04 | 32/4/117/19 | 32/4/114/19 [known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05] | 32/4/117/17 [known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05] | gates_for_depth 32/4/112/21 [new (M4)] | - | 9 |
| T05 | 32/7/103/32 | 32/7/103/29 [new (night:T05)] | 32/7/103/29 [new (night:T05)] | and_depth_for_gates AD6 32/6/104/31 [known]; and_depth_for_gates AD5 32/5/104/29 [known]; and_depth_for_gates AD4 32/4/111/25 [known-by-23:50 (P5; new vs archive); reproduced by night:T05] | G <= 102: none | 11 |
| T06 | 34/4/139/13 | 34/4/134/13 [known] | 34/4/134/13 [known] | - | - | 9 |
| T07 | 35/3/139/27 | 35/3/138/23 [new (night:T07)] | 35/3/139/21 [new (night:T07)] | - | - | 11 |
| T08 | 35/3/183/13 | 35/3/165/13 [new (M3)] | 35/3/181/12 [known-by-23:50 (P6; new vs archive); reproduced by M3] | - | - | 11 |
| T09 | 45/4/141/12 | 38/4/135/12 [new (night:T09)] | 38/4/135/12 [new (night:T09)] | - | - | 11 |
| T10 | 59/4/159/10 | - | - | - | - | 12 |

## A <= 27

No verified circuit with A <= 27 in any scanned folder.

## Sidecar / verification issues (campaign found/ folders)

- **WARN** P3 `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkH1-s1-mix23-k1-a32-ad4-g112-gd22-b8095ec160.circ.txt`: sidecar missing fields: elapsed_s
- **WARN** P3 `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt`: sidecar missing fields: elapsed_s

## Search-path notes (informational only from 23:50 UTC; not rules)

- NOTE P3 `~/xs-campaigns/2026-11-15-targets/P3/found/p3-c115-p19a-a32-ad4-g116-gd19-20c5d2b662.circ.txt`: kernel stage with start 32/4/115/20 above its caps (GD 20 > cap 19) and no repair_keep; certified by a trace audit (rule 2): audit replay L2 reproduces this circuit gate-identically; all 58897 accepted kernel states have A <= 32, AD <= 4; start 115@20 certified by replay L1. runs/audit (strategies/P3/pdrive_replay.py with t
- NOTE P3 `~/xs-campaigns/2026-11-15-targets/P3/found/p3-c115-p19a-a32-ad4-g116-gd19-b49b2addfa.circ.txt`: kernel stage with start 32/4/115/20 above its caps (GD 20 > cap 19) and no repair_keep; certified by a trace audit (rule 2): same gates as ...-20c5d2b662 (only the comment line differs); certified by audit replay L2. runs/audit (strategies/P3/pdrive_replay.py with the original kernel bfx-593fa798f5, stage kernels given an u
- NOTE P3 `~/xs-campaigns/2026-11-15-targets/P3/found/p3-cj188-p21-a32-ad4-g115-gd20-098ecd13af.circ.txt`: kernel stage with start 32/4/114/23 above its caps (GD 23 > cap 21) and no repair_keep; certified by a trace audit (rule 2): audit replay L1 reproduces this circuit gate-identically; all 55310 accepted kernel states of the stage have A <= 32, AD <= 4; start (114@23) certified. runs/audit (strategies/P3/pdrive_replay.py with

## T01: reference 28/4/132/22 `aes-sbox-a28-ad4-g132-gd22-xx104-40.circ.txt`

Hard limits A <= 28, AD <= 4. Primary: G < 132 with GD <= 22. Ideal: G and GD both lower. Tradeoffs allowed: [{'kind': 'gates_for_depth', 'GD_max': 24}].

207 verified files within the hard limits, 121 distinct structures, 72 distinct tuples.

- Best strict (by G, then GD): **28/4/131/22** (strict), known; reproduced by night:T01, path: n/a (known), `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` (sha256 c7d85507e270)
  - source: archive:results-aes (archive); verification: ledger aes_check.check OK
  - pinned NIST dominating: none

- Best strict (by GD, then G): **28/4/132/20** (strict), known; reproduced by night:T01, path: n/a (known), `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` (sha256 1744039db84b)
  - source: archive:results-aes (archive); verification: ledger aes_check.check OK
  - pinned NIST dominating: none

- Best tradeoff: none


### (G, GD) Pareto frontier within the hard limits

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | other | -2 / +2 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | strict | -1 / +0 | known; reproduced by night:T01 | n/a (known) | none | 8 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | strict | +0 / -2 | known; reproduced by night:T01 | n/a (known) | none | 5 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | other | +1 / -3 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | other | +3 / -4 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | other | +6 / -5 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | other | +9 / -6 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | other | +21 / -7 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | other | +42 / -8 | known-by-23:50 (P2; new vs archive); reproduced by night:T02 | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/131/22 | strict | -1 / +0 | known; reproduced by night:T01 | n/a (known) | none | 8 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | strict | +0 / -2 | known; reproduced by night:T01 | n/a (known) | none | 5 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

none

### (A, AD, G, GD) Pareto frontier within the hard limits (9 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | other | -2 / +2 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | strict | -1 / +0 | known; reproduced by night:T01 | n/a (known) | none | 8 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | strict | +0 / -2 | known; reproduced by night:T01 | n/a (known) | none | 5 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | other | +1 / -3 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | other | +3 / -4 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | other | +6 / -5 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | other | +9 / -6 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | other | +21 / -7 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | other | +42 / -8 | known-by-23:50 (P2; new vs archive); reproduced by night:T02 | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |

Pinned NIST (G, GD) frontier within the same hard limits: 28/4/131/31 aes-sbox-a28-ad4-g131-gd31-xx103-43.circ.txt, 28/4/132/22 aes-sbox-a28-ad4-g132-gd22-xx104-40.circ.txt, 28/4/134/20 aes-sbox-a28-ad4-g134-gd20-xx106-41.circ.txt, 28/4/141/16 aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt, 28/4/153/15 aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt, 28/4/176/14 aes-sbox-a28-ad4-g176-gd14-xx148-25.circ.txt

## T02: reference 28/4/176/14 `aes-sbox-a28-ad4-g176-gd14-xx148-25.circ.txt`

Hard limits A <= 28, AD <= 4. Primary: GD < 14 with G <= 176; equally G < 176 with GD <= 14. Ideal: both. Tradeoffs allowed: none.

207 verified files within the hard limits, 121 distinct structures, 72 distinct tuples.

- Best strict (by G, then GD): **28/4/174/14** (strict), known-by-23:50 (P2; new vs archive); reproduced by night:T02, path: certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt), `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` (sha256 d833ee9711a7)
  - start: ~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a28-ad4-g175-gd14-xx147-68.circ.txt sha256 0d8760cc1198; method: strategies/F/fdrive.py mode mix (gate/osc/trb), stage 17 trb-bottom (timing-driven bottom-region rebuild + kernel), caps GD14 AD4 A28, kernel bfx-593fa798f5; seed: 1; elapsed: 2437.0 s
  - verification: OK   /home/joebachir20/xs-campaigns/2026-11-15-targets/P2/runs/t02mix1/snap-g174.circ.txt  A AD G GD = 28 4 174 14  counts {'AND': 28, 'XNOR': 70, 'XOR': 76}; ledger re-check OK
  - pinned NIST dominating: none

- Best tradeoff: none


### (G, GD) Pareto frontier within the hard limits

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | other | -46 / +10 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | other | -45 / +8 | known; reproduced by night:T01 | n/a (known) | none | 8 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | other | -44 / +6 | known; reproduced by night:T01 | n/a (known) | none | 5 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | other | -43 / +5 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | other | -41 / +4 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | other | -38 / +3 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | other | -35 / +2 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | other | -23 / +1 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | strict | -2 / +0 | known-by-23:50 (P2; new vs archive); reproduced by night:T02 | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/174/14 | strict | -2 / +0 | known-by-23:50 (P2; new vs archive); reproduced by night:T02 | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

none

### (A, AD, G, GD) Pareto frontier within the hard limits (9 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | other | -46 / +10 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | other | -45 / +8 | known; reproduced by night:T01 | n/a (known) | none | 8 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | other | -44 / +6 | known; reproduced by night:T01 | n/a (known) | none | 5 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | other | -43 / +5 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | other | -41 / +4 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | other | -38 / +3 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | other | -35 / +2 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | other | -23 / +1 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | strict | -2 / +0 | known-by-23:50 (P2; new vs archive); reproduced by night:T02 | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |

Pinned NIST (G, GD) frontier within the same hard limits: 28/4/131/31 aes-sbox-a28-ad4-g131-gd31-xx103-43.circ.txt, 28/4/132/22 aes-sbox-a28-ad4-g132-gd22-xx104-40.circ.txt, 28/4/134/20 aes-sbox-a28-ad4-g134-gd20-xx106-41.circ.txt, 28/4/141/16 aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt, 28/4/153/15 aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt, 28/4/176/14 aes-sbox-a28-ad4-g176-gd14-xx148-25.circ.txt

## T03: reference 28/5/128/20 `aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt`

Hard limits A <= 28, AD <= 5. Primary: G < 128 with GD <= 20; also GD < 20 with G <= 128. Ideal: both; no GD increase for minor gate savings. Tradeoffs allowed: [{'kind': 'gates_for_depth', 'GD_max': 22, 'note': 'user 23:50 UTC: let depth increase if it saves gates; +2 GD max, >=3 gates; also report G<=123 at any GD (beats pinned 124/27)'}].

659 verified files within the hard limits, 361 distinct structures, 214 distinct tuples.

- Best strict (by G, then GD): none

- Best tradeoff: none

- Notable (G <= 123 at any GD within the hard limits (BRIEF2 decision 4, user 23:50 UTC; beats the pinned 124/27)): none


### (G, GD) Pareto frontier within the hard limits

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/5/124/27 | other | -4 / +7 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt | 1 | `~/xs-campaigns/2026-11-14-hub/long/archive/104c1eda4172.bfx` |
| 28/5/125/24 | other | -3 / +4 | new (night:T03) | certified (~/xs-campaigns/2026-11-16-night/T03/found/conjpull-a28-ad5-g125-gd24-f244b8aa4f.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T03/found/conjpull-a28-ad5-g125-gd24-f244b8aa4f.circ.txt` |
| 28/5/126/23 | other | -2 / +3 | known; reproduced by night:T03 | n/a (known) | none | 2 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad5-g126-gd23-0c61a5821a27.bfx` |
| 28/5/127/22 | other | -1 / +2 | known; reproduced by night:T03 | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-genskel-g127-a28-gd22-ad5.circ.txt` |
| 28/5/128/20 | other | +0 / +0 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt | 1 | `~/xs-campaigns/2026-11-14-hub/long/archive/4096beef1bbf.bfx` |
| 28/5/129/19 | other | +1 / -1 | known-by-23:50 (P1; new vs archive) | unknown | none | 41 | `~/xs-campaigns/2026-11-15-targets/P1/found/P1-T03-a28-ad5-g129-gd19-ec51e03b02b5.circ.txt` |
| 28/5/133/18 | other | +5 / -2 | known; reproduced by night:T03 | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g133-a28-gd18-ad5.circ.txt` |
| 28/5/136/17 | other | +8 / -3 | known; reproduced by night:T03 | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-trb-g136-a28-gd17-ad5.circ.txt` |
| 28/4/141/16 | other | +13 / -4 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/5/150/15 | other | +22 / -5 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad5-g150-gd15-xx122-23.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/09fbfd47fda3.bfx` |
| 28/4/174/14 | other | +46 / -6 | known-by-23:50 (P2; new vs archive); reproduced by night:T02 | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

none

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

none

### (A, AD, G, GD) Pareto frontier within the hard limits (18 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | other | +2 / +4 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | other | +3 / +2 | known; reproduced by night:T01 | n/a (known) | none | 8 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | other | +4 / +0 | known; reproduced by night:T01 | n/a (known) | none | 5 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | other | +5 / -1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | other | +7 / -2 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | other | +10 / -3 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | other | +13 / -4 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | other | +25 / -5 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | other | +46 / -6 | known-by-23:50 (P2; new vs archive); reproduced by night:T02 | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |
| 28/5/124/27 | other | -4 / +7 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt | 1 | `~/xs-campaigns/2026-11-14-hub/long/archive/104c1eda4172.bfx` |
| 28/5/125/24 | other | -3 / +4 | new (night:T03) | certified (~/xs-campaigns/2026-11-16-night/T03/found/conjpull-a28-ad5-g125-gd24-f244b8aa4f.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T03/found/conjpull-a28-ad5-g125-gd24-f244b8aa4f.circ.txt` |
| 28/5/126/23 | other | -2 / +3 | known; reproduced by night:T03 | n/a (known) | none | 2 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad5-g126-gd23-0c61a5821a27.bfx` |
| 28/5/127/22 | other | -1 / +2 | known; reproduced by night:T03 | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-genskel-g127-a28-gd22-ad5.circ.txt` |
| 28/5/128/20 | other | +0 / +0 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt | 1 | `~/xs-campaigns/2026-11-14-hub/long/archive/4096beef1bbf.bfx` |
| 28/5/129/19 | other | +1 / -1 | known-by-23:50 (P1; new vs archive) | unknown | none | 41 | `~/xs-campaigns/2026-11-15-targets/P1/found/P1-T03-a28-ad5-g129-gd19-ec51e03b02b5.circ.txt` |
| 28/5/133/18 | other | +5 / -2 | known; reproduced by night:T03 | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g133-a28-gd18-ad5.circ.txt` |
| 28/5/136/17 | other | +8 / -3 | known; reproduced by night:T03 | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-trb-g136-a28-gd17-ad5.circ.txt` |
| 28/5/150/15 | other | +22 / -5 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad5-g150-gd15-xx122-23.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/09fbfd47fda3.bfx` |

Pinned NIST (G, GD) frontier within the same hard limits: 28/4/141/16 aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt, 28/4/176/14 aes-sbox-a28-ad4-g176-gd14-xx148-25.circ.txt, 28/5/124/27 aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt, 28/5/128/20 aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt, 28/5/150/15 aes-sbox-a28-ad5-g150-gd15-xx122-23.circ.txt

## T04: reference 32/4/117/19 `aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt`

Hard limits A <= 32, AD <= 4. Primary: G < 117 with GD <= 19. Ideal: both. Tradeoffs allowed: [{'kind': 'gates_for_depth', 'GD_max': 21}].

808 verified files within the hard limits, 585 distinct structures, 261 distinct tuples.

- Best strict (by G, then GD): **32/4/114/19** (strict), known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05, path: certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt), `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt` (sha256 73e77c68fca8)
  - start: ~/xs-campaigns/2026-11-15-targets/P3/runs/rkG1-stage2.circ.txt sha256 4644f69a984a; method: pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, kernel bfx-4dc199db, repair_keep 1; seed: 1031; elapsed: 361.0 s
  - verification: OK   /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/rkG1-s3-mix19-k1/best.circ.txt  A AD G GD = 32 4 114 19  counts {'AND': 32, 'XNOR': 37, 'XOR': 45}; ledger re-check OK
  - pinned NIST dominating: none

- Best strict (by GD, then G): **32/4/117/17** (strict), known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05, path: certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt), `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` (sha256 99c3bf2a3e36)
  - start: ~/xs-campaigns/2026-11-15-targets/P3/runs/rkK1-s2-mix17-k1/pareto/g118-gd17.circ.txt sha256 dddd01b7ade8; method: pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD17, kernel bfx-4dc199db, repair_keep 1; seed: 2212; elapsed: 600.0 s
  - verification: OK   /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/rkN1-s1-mix17-k2/best.circ.txt  A AD G GD = 32 4 117 17  counts {'AND': 32, 'XNOR': 39, 'XOR': 46}; ledger re-check OK
  - pinned NIST dominating: none

- Best tradeoff (gates_for_depth): **32/4/112/21** (tradeoff:gates_for_depth), new (M4), path: unknown, `~/xs-campaigns/2026-11-15-targets/M4/found/satlns-a32-ad4-g112-gd21-efda23263f.circ.txt` (sha256 efda23263f01)
  - start: ~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt sha256 6a349e2eb279; method: {'engine': 'campaigns/targets/ops/satlns.py (span-pooled SAT LNS, pysat glucose4; from strategies/P1/unionsat2.py v2.4)', 'mode': 'fast', 'operators': ['satlns', 'kernel-polish'], 'caps': {'A': 32, 'AD': 4, 'GD': 21}, 'objective': 'G under GD <= D (walk), A <= A cap in the model', 'how': 'step 1245 epoch 2 query F', 'model': {'circuits': 95, 'forms': 774, 'templates_pooled': 1612, 'templates': 7489, 'and_templates': 171, 'rot_templates': 309, 'D': 21, 'vars': 191046, 'clauses': 347005, 'sel': 7144, 't_build': 1.9, 'epoch': 2}, 'pool': {'span': '41-05b52913981bcf81', 'n_same_span_files': 96, 'n_pooled': 94, 'files_sample': ['/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt', '/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert113-r3-gate30-a32-ad4-g111-gd25-56b90bc378.circ.txt', '/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-certB-r2-gate30-a32-ad4-g111-gd25-5b118266a0.circ.txt', '/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-certB-r3-gate30-a32-ad4-g111-gd25-c682c9518b.circ.txt', '/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/found/p5-ad4rep-112-g32-s1-a32-ad4-g111-gd26-74604ea2c6.circ.txt', '/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/found/p5-ad4rep-112-g32-s2-a32-ad4-g111-gd26-67fd53ccb7.circ.txt', '/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/found/p5-ad4rep-112-g32-s3-a32-ad4-g111-gd26-a4d6a2dde1.circ.txt', '/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/found/p5-ad4rep-112-g32-s4-a32-ad4-g111-gd26-9b6a27c5d9.circ.txt', '/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/found/p5-ad4rep-112-g32-s5-a32-ad4-g111-gd26-60baa8d4ac.circ.txt', '/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert112c-r1-gate26-a32-ad4-g111-gd26-99fb8b899e.circ.txt', '/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert113-r2-gate30-a32-ad4-g111-gd26-162638ccbf.circ.txt', '/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert113-r2-mix26-a32-ad4-g111-gd26-05cc8d2448.circ.txt', '/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/found/p5-ad4rep-112-g32-s1-a32-ad4-g111-gd27-e32dbde99e.circ.txt', '/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/found/p5-ad4rep-112-g32-s4-a32-ad4-g111-gd28-27b136ee8c.circ.txt', '/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/found/p5-ad4rep-112-g32-s2-a32-ad4-g111-gd30-cb4d8cf4e2.circ.txt', '/home/joebachir20/xs-campaigns/2026-11-15-targets/P3/found/p3-rkH1-s1-mix23-k1-a32-ad4-g112-gd22-b8095ec160.circ.txt', '/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/found/p5-ad4rep-111-c24-s1-a32-ad4-g112-gd22-db1394c64b.circ.txt', '/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/found/p5-ad4rep-111-c24-s2-a32-ad4-g112-gd22-e9aef8c1c8.circ.txt', '/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/found/p5-ad4rep-111-c24-s5-a32-ad4-g112-gd22-2af2254f9b.circ.txt', '/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert112c-r1-mix22-a32-ad4-g112-gd22-125223cf3b.circ.txt'], 'before': None, 'exclude_better': False}}; seed: 23; elapsed: 584.2 s
  - verification: OK   /home/joebachir20/xs-campaigns/2026-11-15-targets/M4/runs/screen/r2-t04-d21/satlns-a32-ad4-g112-gd21-efda23263f.circ.txt  A AD G GD = 32 4 112 21  counts {'AND': 32, 'XNOR': 31, 'XOR': 49}; ledger re-check OK
  - pinned NIST dominating: none


### (G, GD) Pareto frontier within the hard limits

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 32/4/111/25 | other | -6 / +6 | known-by-23:50 (P5; new vs archive); reproduced by night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt` |
| 32/4/112/21 | tradeoff:gates_for_depth | -5 / +2 | new (M4) | unknown | none | 2 | `~/xs-campaigns/2026-11-15-targets/M4/found/satlns-a32-ad4-g112-gd21-efda23263f.circ.txt` |
| 32/4/113/20 | tradeoff:gates_for_depth | -4 / +1 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt) | none | 12 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt` |
| 32/4/114/19 | strict | -3 / +0 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt) | none | 17 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt` |
| 32/4/115/18 | strict | -2 / -1 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt` |
| 32/4/117/17 | strict | +0 / -2 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` |
| 32/4/119/16 | other | +2 / -3 | new (night:T04) | not certified (inherited from conjpull-a32-ad4-g117-gd17-b83f9deb89.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-16-night/T04/found/conjpull-a32-ad4-g119-gd16-3acd9d4790.circ.txt` |
| 32/4/125/15 | other | +8 / -4 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt` |
| 28/4/174/14 | other | +57 / -5 | known-by-23:50 (P2; new vs archive); reproduced by night:T02 | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 32/4/114/19 | strict | -3 / +0 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt) | none | 17 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt` |
| 32/4/115/18 | strict | -2 / -1 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt` |
| 32/4/117/17 | strict | +0 / -2 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` |

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 32/4/112/21 | tradeoff:gates_for_depth | -5 / +2 | new (M4) | unknown | none | 2 | `~/xs-campaigns/2026-11-15-targets/M4/found/satlns-a32-ad4-g112-gd21-efda23263f.circ.txt` |
| 32/4/113/20 | tradeoff:gates_for_depth | -4 / +1 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt) | none | 12 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt` |

### (A, AD, G, GD) Pareto frontier within the hard limits (23 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | other | +13 / +5 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | other | +14 / +3 | known; reproduced by night:T01 | n/a (known) | none | 8 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | other | +15 / +1 | known; reproduced by night:T01 | n/a (known) | none | 5 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | other | +16 / +0 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | other | +18 / -1 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | other | +21 / -2 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | other | +24 / -3 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | other | +36 / -4 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | other | +57 / -5 | known-by-23:50 (P2; new vs archive); reproduced by night:T02 | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |
| 29/4/128/23 | other | +11 / +4 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-X2-x2-g128-a29-gd23-ad4.circ.txt` |
| 29/4/129/19 | other | +12 / +0 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g129-gd19-xx100-56.circ.txt` |
| 29/4/131/17 | other | +14 / -2 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g131-gd17-xx102-61.circ.txt` |
| 29/4/135/16 | other | +18 / -3 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g135-gd16-xx106-50.circ.txt` |
| 29/4/141/15 | other | +24 / -4 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g141-gd15-xx112-56.circ.txt` |
| 30/4/138/15 | other | +21 / -4 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a30-ad4-g138-gd15-xx108-61.circ.txt` |
| 32/4/111/25 | other | -6 / +6 | known-by-23:50 (P5; new vs archive); reproduced by night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt` |
| 32/4/112/21 | tradeoff:gates_for_depth | -5 / +2 | new (M4) | unknown | none | 2 | `~/xs-campaigns/2026-11-15-targets/M4/found/satlns-a32-ad4-g112-gd21-efda23263f.circ.txt` |
| 32/4/113/20 | tradeoff:gates_for_depth | -4 / +1 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt) | none | 12 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt` |
| 32/4/114/19 | strict | -3 / +0 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt) | none | 17 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt` |
| 32/4/115/18 | strict | -2 / -1 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt` |
| 32/4/117/17 | strict | +0 / -2 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` |
| 32/4/119/16 | other | +2 / -3 | new (night:T04) | not certified (inherited from conjpull-a32-ad4-g117-gd17-b83f9deb89.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-16-night/T04/found/conjpull-a32-ad4-g119-gd16-3acd9d4790.circ.txt` |
| 32/4/125/15 | other | +8 / -4 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt` |

Pinned NIST (G, GD) frontier within the same hard limits: 28/4/176/14 aes-sbox-a28-ad4-g176-gd14-xx148-25.circ.txt, 32/4/117/19 aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt, 32/4/127/15 aes-sbox-a32-ad4-g127-gd15-xx95-7.circ.txt

## T05: reference 32/7/103/32 `aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt`

Hard limits A <= 32, AD <= 7. Primary: G < 103 with GD <= 32 (overall gate-count record); GD < 32 with G <= 103 also valued. Ideal: both. Tradeoffs allowed: [{'kind': 'and_depth_for_gates', 'AD_targets': [6, 5, 4], 'note': 'separate achievement: lower AND depth with G as close to 103 as possible; report best G (then GD) per AD'}, {'kind': 'gates_for_depth', 'GD_max': 999, 'note': 'user 23:50 UTC: let depth increase if it saves gates; any G<=102 at any GD is a new overall record; min_gate_gain 1: any G <= 102 counts (coordinator, per the user 23:50 UTC)', 'min_gate_gain': 1}].

2617 verified files within the hard limits, 1711 distinct structures, 886 distinct tuples.

- Best strict (by G, then GD): **32/7/103/29** (strict), new (night:T05), path: certified (~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad7-g103-gd29-8e51adc4e9.circ.txt), `~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad7-g103-gd29-8e51adc4e9.circ.txt` (sha256 8e51adc4e9c9)
  - start: ~/xcr-boolflux/nonlinear/nist/aes-sbox/aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt sha256 91b1b58b34d4; method: ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged kernel pulls g:34:300,t:32:300,m:32:360 (fdrive semantics; kernel bfx-94a75e2c18, repair_keep 1 unless a stage says rk0/rk1); search states may exceed caps, recorded circuits inside A<=32 AD<=7; seed: 775495; elapsed: 598.3 s
  - verification: OK   /home/joebachir20/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad7-g103-gd29-8e51adc4e9.circ.txt  A AD G GD = 32 7 103 29  counts {'AND': 32, 'XNOR': 25, 'XOR': 46}; ledger re-check OK
  - pinned NIST dominating: none

- Best tradeoff (and_depth_for_gates AD6): **32/6/104/31** (tradeoff:and_depth_for_gates), known, path: n/a (known), `~/xs-campaigns/2026-11-14-hub/long/archive/3f7a2fec7b7d.bfx` (sha256 22d5bef5cc55)
  - source: archive:hub-long (archive); verification: ledger aes_check.check OK
  - pinned NIST dominating: 1: 32/5/104/30 (aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt)

- Best tradeoff (and_depth_for_gates AD5): **32/5/104/29** (tradeoff:and_depth_for_gates), known, path: n/a (known), `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g104-a32-gd29-ad5.circ.txt` (sha256 9f893283b39b)
  - source: archive:results-aes (archive); verification: ledger aes_check.check OK
  - pinned NIST dominating: none

- Best tradeoff (and_depth_for_gates AD4): **32/4/111/25** (tradeoff:and_depth_for_gates), known-by-23:50 (P5; new vs archive); reproduced by night:T05, path: certified (~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt), `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt` (sha256 83ea45708af8)
  - start: ~/xs-campaigns/2026-11-15-targets/P5/starts/ad4-111-25-cert.circ.txt sha256 49d67b7b0ba7; method: p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, caps A<=32 AD<=4 GD<=30, kernel bfx-94a75e2c18 repair_keep 1; seed: 91; elapsed: 302 s
  - verification: OK /home/joebachir20/xs-campaigns/2026-11-15-targets/P5/runs/lin-cert111-r1-gate30/pareto/g111-gd25.circ.txt A AD G GD = 32 4 111 25 counts {'AND': 32, 'XNOR': 31, 'XOR': 48}; ledger re-check OK
  - pinned NIST dominating: none

- Notable (G <= 102 at any GD within the hard limits (BRIEF2 decision 4, user 23:50 UTC; a new overall gate-count record)): none


### (G, GD) Pareto frontier within the hard limits

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 32/7/103/29 | strict | +0 / -3 | new (night:T05) | certified (~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad7-g103-gd29-8e51adc4e9.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad7-g103-gd29-8e51adc4e9.circ.txt` |
| 32/7/104/26 | other | +1 / -6 | new (night:T05) | certified (~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad7-g104-gd26-8da775ecfd.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad7-g104-gd26-8da775ecfd.circ.txt` |
| 32/5/105/24 | tradeoff:and_depth_for_gates | +2 / -8 | new (night:T05) | certified (~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g105-gd24-48b9e7a153.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g105-gd24-48b9e7a153.circ.txt` |
| 32/5/106/21 | tradeoff:and_depth_for_gates | +3 / -11 | new (night:T05) | not certified (inherited from conjpull-a32-ad5-g106-gd22-b8eeb91ee6.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g106-gd21-31d6dc63b3.circ.txt` |
| 32/5/108/20 | tradeoff:and_depth_for_gates | +5 / -12 | known; reproduced by night:T05 | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad5-a32-g108-a32-gd20-ad5.circ.txt` |
| 32/5/110/19 | tradeoff:and_depth_for_gates | +7 / -13 | new (night:T05) | certified (~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g110-gd19-1655161739.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g110-gd19-1655161739.circ.txt` |
| 32/5/111/18 | tradeoff:and_depth_for_gates | +8 / -14 | new (night:T05) | not certified | none | 2 | `~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g111-gd18-67697bc8dd.circ.txt` |
| 32/5/115/17 | tradeoff:and_depth_for_gates | +12 / -15 | known; reproduced by night:T05 | n/a (known) | none | 7 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-pull-g115-a32-gd17-ad5.circ.txt` |
| 32/4/119/16 | tradeoff:and_depth_for_gates | +16 / -16 | new (night:T04) | not certified (inherited from conjpull-a32-ad4-g117-gd17-b83f9deb89.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-16-night/T04/found/conjpull-a32-ad4-g119-gd16-3acd9d4790.circ.txt` |
| 32/4/125/15 | tradeoff:and_depth_for_gates | +22 / -17 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt` |
| 28/4/174/14 | tradeoff:and_depth_for_gates | +71 / -18 | known-by-23:50 (P2; new vs archive); reproduced by night:T02 | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 32/7/103/29 | strict | +0 / -3 | new (night:T05) | certified (~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad7-g103-gd29-8e51adc4e9.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad7-g103-gd29-8e51adc4e9.circ.txt` |

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 32/4/111/25 | tradeoff:and_depth_for_gates | +8 / -7 | known-by-23:50 (P5; new vs archive); reproduced by night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt` |
| 32/4/112/21 | tradeoff:and_depth_for_gates | +9 / -11 | new (M4) | unknown | none | 2 | `~/xs-campaigns/2026-11-15-targets/M4/found/satlns-a32-ad4-g112-gd21-efda23263f.circ.txt` |
| 32/4/113/20 | tradeoff:and_depth_for_gates | +10 / -12 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt) | none | 12 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt` |
| 32/4/114/19 | tradeoff:and_depth_for_gates | +11 / -13 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt) | none | 17 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt` |
| 32/4/115/18 | tradeoff:and_depth_for_gates | +12 / -14 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt` |
| 32/4/117/17 | tradeoff:and_depth_for_gates | +14 / -15 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` |
| 32/4/119/16 | tradeoff:and_depth_for_gates | +16 / -16 | new (night:T04) | not certified (inherited from conjpull-a32-ad4-g117-gd17-b83f9deb89.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-16-night/T04/found/conjpull-a32-ad4-g119-gd16-3acd9d4790.circ.txt` |
| 32/4/125/15 | tradeoff:and_depth_for_gates | +22 / -17 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt` |
| 28/4/174/14 | tradeoff:and_depth_for_gates | +71 / -18 | known-by-23:50 (P2; new vs archive); reproduced by night:T02 | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |
| 32/5/104/29 | tradeoff:and_depth_for_gates | +1 / -3 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g104-a32-gd29-ad5.circ.txt` |
| 32/5/105/24 | tradeoff:and_depth_for_gates | +2 / -8 | new (night:T05) | certified (~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g105-gd24-48b9e7a153.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g105-gd24-48b9e7a153.circ.txt` |
| 32/5/106/21 | tradeoff:and_depth_for_gates | +3 / -11 | new (night:T05) | not certified (inherited from conjpull-a32-ad5-g106-gd22-b8eeb91ee6.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g106-gd21-31d6dc63b3.circ.txt` |
| 32/5/108/20 | tradeoff:and_depth_for_gates | +5 / -12 | known; reproduced by night:T05 | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad5-a32-g108-a32-gd20-ad5.circ.txt` |
| 32/5/110/19 | tradeoff:and_depth_for_gates | +7 / -13 | new (night:T05) | certified (~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g110-gd19-1655161739.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g110-gd19-1655161739.circ.txt` |
| 32/5/111/18 | tradeoff:and_depth_for_gates | +8 / -14 | new (night:T05) | not certified | none | 2 | `~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g111-gd18-67697bc8dd.circ.txt` |
| 32/5/115/17 | tradeoff:and_depth_for_gates | +12 / -15 | known; reproduced by night:T05 | n/a (known) | none | 7 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-pull-g115-a32-gd17-ad5.circ.txt` |

### (A, AD, G, GD) Pareto frontier within the hard limits (49 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | tradeoff:and_depth_for_gates | +27 / -8 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | tradeoff:and_depth_for_gates | +28 / -10 | known; reproduced by night:T01 | n/a (known) | none | 8 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | tradeoff:and_depth_for_gates | +29 / -12 | known; reproduced by night:T01 | n/a (known) | none | 5 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | tradeoff:and_depth_for_gates | +30 / -13 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | tradeoff:and_depth_for_gates | +32 / -14 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | tradeoff:and_depth_for_gates | +35 / -15 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | tradeoff:and_depth_for_gates | +38 / -16 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | tradeoff:and_depth_for_gates | +50 / -17 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | tradeoff:and_depth_for_gates | +71 / -18 | known-by-23:50 (P2; new vs archive); reproduced by night:T02 | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |
| 28/5/124/27 | tradeoff:and_depth_for_gates | +21 / -5 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt | 1 | `~/xs-campaigns/2026-11-14-hub/long/archive/104c1eda4172.bfx` |
| 28/5/125/24 | tradeoff:and_depth_for_gates | +22 / -8 | new (night:T03) | certified (~/xs-campaigns/2026-11-16-night/T03/found/conjpull-a28-ad5-g125-gd24-f244b8aa4f.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T03/found/conjpull-a28-ad5-g125-gd24-f244b8aa4f.circ.txt` |
| 28/5/126/23 | tradeoff:and_depth_for_gates | +23 / -9 | known; reproduced by night:T03 | n/a (known) | none | 2 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad5-g126-gd23-0c61a5821a27.bfx` |
| 28/5/127/22 | tradeoff:and_depth_for_gates | +24 / -10 | known; reproduced by night:T03 | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-genskel-g127-a28-gd22-ad5.circ.txt` |
| 28/5/128/20 | tradeoff:and_depth_for_gates | +25 / -12 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt | 1 | `~/xs-campaigns/2026-11-14-hub/long/archive/4096beef1bbf.bfx` |
| 28/5/129/19 | tradeoff:and_depth_for_gates | +26 / -13 | known-by-23:50 (P1; new vs archive) | unknown | none | 41 | `~/xs-campaigns/2026-11-15-targets/P1/found/P1-T03-a28-ad5-g129-gd19-ec51e03b02b5.circ.txt` |
| 28/5/133/18 | tradeoff:and_depth_for_gates | +30 / -14 | known; reproduced by night:T03 | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g133-a28-gd18-ad5.circ.txt` |
| 28/5/136/17 | tradeoff:and_depth_for_gates | +33 / -15 | known; reproduced by night:T03 | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-trb-g136-a28-gd17-ad5.circ.txt` |
| 28/5/150/15 | tradeoff:and_depth_for_gates | +47 / -17 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad5-g150-gd15-xx122-23.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/09fbfd47fda3.bfx` |
| 29/4/128/23 | tradeoff:and_depth_for_gates | +25 / -9 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-X2-x2-g128-a29-gd23-ad4.circ.txt` |
| 29/4/129/19 | tradeoff:and_depth_for_gates | +26 / -13 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g129-gd19-xx100-56.circ.txt` |
| 29/4/131/17 | tradeoff:and_depth_for_gates | +28 / -15 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g131-gd17-xx102-61.circ.txt` |
| 29/4/135/16 | tradeoff:and_depth_for_gates | +32 / -16 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g135-gd16-xx106-50.circ.txt` |
| 29/4/141/15 | tradeoff:and_depth_for_gates | +38 / -17 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g141-gd15-xx112-56.circ.txt` |
| 29/5/130/18 | tradeoff:and_depth_for_gates | +27 / -14 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad5-g130-gd18-xx101-43.circ.txt` |
| 30/4/138/15 | tradeoff:and_depth_for_gates | +35 / -17 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a30-ad4-g138-gd15-xx108-61.circ.txt` |
| 31/5/114/28 | tradeoff:and_depth_for_gates | +11 / -4 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g114-a31-gd28-ad5.circ.txt` |
| 31/5/115/24 | tradeoff:and_depth_for_gates | +12 / -8 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g115-a31-gd24-ad5.circ.txt` |
| 31/5/116/22 | tradeoff:and_depth_for_gates | +13 / -10 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-join-g116-a31-gd22-ad5.circ.txt` |
| 31/5/117/20 | tradeoff:and_depth_for_gates | +14 / -12 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g117-a31-gd20-ad5.circ.txt` |
| 31/5/118/19 | tradeoff:and_depth_for_gates | +15 / -13 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-join-g118-a31-gd19-ad5.circ.txt` |
| 31/5/121/18 | tradeoff:and_depth_for_gates | +18 / -14 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g121-a31-gd18-ad5.circ.txt` |
| 31/5/124/17 | tradeoff:and_depth_for_gates | +21 / -15 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-pull-g124-a31-gd17-ad5.circ.txt` |
| 32/4/111/25 | tradeoff:and_depth_for_gates | +8 / -7 | known-by-23:50 (P5; new vs archive); reproduced by night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt` |
| 32/4/112/21 | tradeoff:and_depth_for_gates | +9 / -11 | new (M4) | unknown | none | 2 | `~/xs-campaigns/2026-11-15-targets/M4/found/satlns-a32-ad4-g112-gd21-efda23263f.circ.txt` |
| 32/4/113/20 | tradeoff:and_depth_for_gates | +10 / -12 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt) | none | 12 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt` |
| 32/4/114/19 | tradeoff:and_depth_for_gates | +11 / -13 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt) | none | 17 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt` |
| 32/4/115/18 | tradeoff:and_depth_for_gates | +12 / -14 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt` |
| 32/4/117/17 | tradeoff:and_depth_for_gates | +14 / -15 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` |
| 32/4/119/16 | tradeoff:and_depth_for_gates | +16 / -16 | new (night:T04) | not certified (inherited from conjpull-a32-ad4-g117-gd17-b83f9deb89.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-16-night/T04/found/conjpull-a32-ad4-g119-gd16-3acd9d4790.circ.txt` |
| 32/4/125/15 | tradeoff:and_depth_for_gates | +22 / -17 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt` |
| 32/5/104/29 | tradeoff:and_depth_for_gates | +1 / -3 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g104-a32-gd29-ad5.circ.txt` |
| 32/5/105/24 | tradeoff:and_depth_for_gates | +2 / -8 | new (night:T05) | certified (~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g105-gd24-48b9e7a153.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g105-gd24-48b9e7a153.circ.txt` |
| 32/5/106/21 | tradeoff:and_depth_for_gates | +3 / -11 | new (night:T05) | not certified (inherited from conjpull-a32-ad5-g106-gd22-b8eeb91ee6.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g106-gd21-31d6dc63b3.circ.txt` |
| 32/5/108/20 | tradeoff:and_depth_for_gates | +5 / -12 | known; reproduced by night:T05 | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad5-a32-g108-a32-gd20-ad5.circ.txt` |
| 32/5/110/19 | tradeoff:and_depth_for_gates | +7 / -13 | new (night:T05) | certified (~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g110-gd19-1655161739.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g110-gd19-1655161739.circ.txt` |
| 32/5/111/18 | tradeoff:and_depth_for_gates | +8 / -14 | new (night:T05) | not certified | none | 2 | `~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g111-gd18-67697bc8dd.circ.txt` |
| 32/5/115/17 | tradeoff:and_depth_for_gates | +12 / -15 | known; reproduced by night:T05 | n/a (known) | none | 7 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-pull-g115-a32-gd17-ad5.circ.txt` |
| 32/7/103/29 | strict | +0 / -3 | new (night:T05) | certified (~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad7-g103-gd29-8e51adc4e9.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad7-g103-gd29-8e51adc4e9.circ.txt` |
| 32/7/104/26 | other | +1 / -6 | new (night:T05) | certified (~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad7-g104-gd26-8da775ecfd.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad7-g104-gd26-8da775ecfd.circ.txt` |

### Best per AND depth at A <= 32

| AD | best G (then GD) at AD = d | status | best G at AD <= d | best GD (then G) at AD = d | status | (G,GD) frontier at AD = d |
|---|---|---|---|---|---|---|
| 7 | 32/7/103/29 | new (night:T05) | 32/7/103/29 | 32/7/109/23 | known | 32/7/103/29, 32/7/104/26, 32/7/108/24, 32/7/109/23 |
| 6 | 32/6/104/31 | known | 32/5/104/29 | 31/6/124/19 | known | 32/6/104/31, 32/6/105/30, 32/6/106/27, 32/6/109/26, 32/6/110/25, 32/6/115/24, 32/6/120/20, 31/6/124/19 |
| 5 | 32/5/104/29 | known | 32/5/104/29 | 32/5/127/15 | known | 32/5/104/29, 32/5/105/24, 32/5/106/21, 32/5/108/20, 32/5/110/19, 32/5/111/18, 32/5/115/17, 32/5/120/16, 32/5/127/15 |
| 4 | 32/4/111/25 | known-by-23:50 (P5; new vs archive); reproduced by night:T05 | 32/4/111/25 | 28/4/174/14 | known-by-23:50 (P2; new vs archive); reproduced by night:T02 | 32/4/111/25, 32/4/112/21, 32/4/113/20, 32/4/114/19, 32/4/115/18, 32/4/117/17, 32/4/119/16, 32/4/125/15, 28/4/174/14 |
| 3 | - |  | - | - |  |  |
| 2 | - |  | - | - |  |  |
| 1 | - |  | - | - |  |  |

Pinned NIST (G, GD) frontier within the same hard limits: 28/4/176/14 aes-sbox-a28-ad4-g176-gd14-xx148-25.circ.txt, 32/4/117/19 aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt, 32/4/127/15 aes-sbox-a32-ad4-g127-gd15-xx95-7.circ.txt, 32/5/104/30 aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt, 32/5/105/26 aes-sbox-a32-ad5-g105-gd26-xx73-5.circ.txt, 32/5/107/22 aes-sbox-a32-ad5-g107-gd22-xx75-4.circ.txt, 32/5/109/20 aes-sbox-a32-ad5-g109-gd20-xx77-4.circ.txt, 32/5/122/16 aes-sbox-a32-ad5-g122-gd16-xx90-15.circ.txt, 32/5/127/15 aes-sbox-a32-ad5-g127-gd15-xx95-20.circ.txt, 32/7/103/32 aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt

## T06: reference 34/4/139/13 `aes-sbox-a34-ad4-g139-gd13-xx105-22.circ.txt`

Hard limits A <= 34, AD <= 4. Primary: GD < 13 with G <= 139; secondary G < 139 with GD <= 13. Ideal: both; depth is the main objective. Tradeoffs allowed: none.

1172 verified files within the hard limits, 843 distinct structures, 383 distinct tuples.

- Best strict (by G, then GD): **34/4/134/13** (strict), known, path: n/a (known), `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g134-a34-gd13-ad4.circ.txt` (sha256 2c217ef01ef7)
  - source: archive:results-aes (archive); verification: ledger aes_check.check OK
  - pinned NIST dominating: none

- Best tradeoff: none


### (G, GD) Pareto frontier within the hard limits

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 33/4/105/25 | other | -34 / +12 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/0f491596c734.bfx` |
| 33/4/106/22 | other | -33 / +9 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g106-gd22-xx73-5.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/26070040d746.bfx` |
| 33/4/107/20 | other | -32 / +7 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-pull-g107-a33-gd20-ad4.circ.txt` |
| 33/4/108/19 | other | -31 / +6 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt` |
| 33/4/110/18 | other | -29 / +5 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad4-a33-g110-a33-gd18-ad4.circ.txt` |
| 33/4/112/16 | other | -27 / +3 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g112-a33-gd16-ad4.circ.txt` |
| 33/4/115/15 | other | -24 / +2 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-join-g115-a33-gd15-ad4.circ.txt` |
| 34/4/122/14 | other | -17 / +1 | new (night:T06) | certified (~/xs-campaigns/2026-11-16-night/T06/found/conjpull-a34-ad4-g122-gd14-621f73cda5.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T06/found/conjpull-a34-ad4-g122-gd14-621f73cda5.circ.txt` |
| 34/4/134/13 | strict | -5 / +0 | known | n/a (known) | none | 3 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g134-a34-gd13-ad4.circ.txt` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 34/4/134/13 | strict | -5 / +0 | known | n/a (known) | none | 3 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g134-a34-gd13-ad4.circ.txt` |

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

none

### (A, AD, G, GD) Pareto frontier within the hard limits (33 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | other | -9 / +11 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | other | -8 / +9 | known; reproduced by night:T01 | n/a (known) | none | 8 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | other | -7 / +7 | known; reproduced by night:T01 | n/a (known) | none | 5 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | other | -6 / +6 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | other | -4 / +5 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | other | -1 / +4 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | other | +2 / +3 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | other | +14 / +2 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | other | +35 / +1 | known-by-23:50 (P2; new vs archive); reproduced by night:T02 | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |
| 29/4/128/23 | other | -11 / +10 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-X2-x2-g128-a29-gd23-ad4.circ.txt` |
| 29/4/129/19 | other | -10 / +6 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g129-gd19-xx100-56.circ.txt` |
| 29/4/131/17 | other | -8 / +4 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g131-gd17-xx102-61.circ.txt` |
| 29/4/135/16 | other | -4 / +3 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g135-gd16-xx106-50.circ.txt` |
| 29/4/141/15 | other | +2 / +2 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g141-gd15-xx112-56.circ.txt` |
| 30/4/138/15 | other | -1 / +2 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a30-ad4-g138-gd15-xx108-61.circ.txt` |
| 32/4/111/25 | other | -28 / +12 | known-by-23:50 (P5; new vs archive); reproduced by night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt` |
| 32/4/112/21 | other | -27 / +8 | new (M4) | unknown | none | 2 | `~/xs-campaigns/2026-11-15-targets/M4/found/satlns-a32-ad4-g112-gd21-efda23263f.circ.txt` |
| 32/4/113/20 | other | -26 / +7 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt) | none | 12 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt` |
| 32/4/114/19 | other | -25 / +6 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt) | none | 17 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt` |
| 32/4/115/18 | other | -24 / +5 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt` |
| 32/4/117/17 | other | -22 / +4 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` |
| 32/4/119/16 | other | -20 / +3 | new (night:T04) | not certified (inherited from conjpull-a32-ad4-g117-gd17-b83f9deb89.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-16-night/T04/found/conjpull-a32-ad4-g119-gd16-3acd9d4790.circ.txt` |
| 32/4/125/15 | other | -14 / +2 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt` |
| 33/4/105/25 | other | -34 / +12 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/0f491596c734.bfx` |
| 33/4/106/22 | other | -33 / +9 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g106-gd22-xx73-5.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/26070040d746.bfx` |
| 33/4/107/20 | other | -32 / +7 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-pull-g107-a33-gd20-ad4.circ.txt` |
| 33/4/108/19 | other | -31 / +6 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt` |
| 33/4/110/18 | other | -29 / +5 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad4-a33-g110-a33-gd18-ad4.circ.txt` |
| 33/4/112/16 | other | -27 / +3 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g112-a33-gd16-ad4.circ.txt` |
| 33/4/115/15 | other | -24 / +2 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-join-g115-a33-gd15-ad4.circ.txt` |
| 33/4/125/14 | other | -14 / +1 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g125-gd14-xx92-18.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/1317ec0f73e9.bfx` |
| 34/4/122/14 | other | -17 / +1 | new (night:T06) | certified (~/xs-campaigns/2026-11-16-night/T06/found/conjpull-a34-ad4-g122-gd14-621f73cda5.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T06/found/conjpull-a34-ad4-g122-gd14-621f73cda5.circ.txt` |
| 34/4/134/13 | strict | -5 / +0 | known | n/a (known) | none | 3 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g134-a34-gd13-ad4.circ.txt` |

Pinned NIST (G, GD) frontier within the same hard limits: 33/4/105/25 aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt, 33/4/106/22 aes-sbox-a33-ad4-g106-gd22-xx73-5.circ.txt, 33/4/108/20 aes-sbox-a33-ad4-g108-gd20-xx75-5.circ.txt, 33/4/116/15 aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt, 33/4/125/14 aes-sbox-a33-ad4-g125-gd14-xx92-18.circ.txt, 34/4/139/13 aes-sbox-a34-ad4-g139-gd13-xx105-22.circ.txt

## T07: reference 35/3/139/27 `aes-sbox-a35-ad3-g139-gd27-xx104-38.circ.txt`

Hard limits A <= 35, AD <= 3. Primary: G < 139 with GD <= 27. Ideal: both; AD 3 is optimal and preserved. Tradeoffs allowed: [{'kind': 'gates_for_depth', 'GD_max': 29}].

339 verified files within the hard limits, 251 distinct structures, 113 distinct tuples.

- Best strict (by G, then GD): **35/3/138/23** (strict), new (night:T07), path: certified (~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd23-3ed8aa97bd.circ.txt), `~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd23-3ed8aa97bd.circ.txt` (sha256 3ed8aa97bd6d)
  - start: ~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd24-f27addd959.circ.txt sha256 f27addd95971; method: ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged kernel pulls k:27:240 (fdrive semantics; kernel bfx-94a75e2c18, repair_keep 0 unless a stage says rk0/rk1); search states may exceed caps, recorded circuits inside A<=35 AD<=3; seed: 706888; elapsed: 231.0 s
  - verification: OK   /home/joebachir20/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd23-3ed8aa97bd.circ.txt  A AD G GD = 35 3 138 23  counts {'AND': 35, 'XNOR': 46, 'XOR': 57}; ledger re-check OK
  - pinned NIST dominating: none

- Best strict (by GD, then G): **35/3/139/21** (strict), new (night:T07), path: certified (~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd21-f71f0d11d1.circ.txt), `~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd21-f71f0d11d1.circ.txt` (sha256 f71f0d11d16a)
  - start: ~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd22-f26965830b.circ.txt sha256 f26965830b0b; method: ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged kernel pulls k:23:240 (fdrive semantics; kernel bfx-94a75e2c18, repair_keep 0 unless a stage says rk0/rk1); search states may exceed caps, recorded circuits inside A<=35 AD<=3; seed: 321738; elapsed: 226.5 s
  - verification: OK   /home/joebachir20/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd21-f71f0d11d1.circ.txt  A AD G GD = 35 3 139 21  counts {'AND': 35, 'XNOR': 50, 'XOR': 54}; ledger re-check OK
  - pinned NIST dominating: none

- Best tradeoff: none


### (G, GD) Pareto frontier within the hard limits

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 35/3/137/28 | other | -2 / +1 | known-by-23:50 (P6; new vs archive) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt` |
| 35/3/138/23 | strict | -1 / -4 | new (night:T07) | certified (~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd23-3ed8aa97bd.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd23-3ed8aa97bd.circ.txt` |
| 35/3/139/21 | strict | +0 / -6 | new (night:T07) | certified (~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd21-f71f0d11d1.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd21-f71f0d11d1.circ.txt` |
| 35/3/141/19 | other | +2 / -8 | known | n/a (known) | none | 5 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g141-gd19-xx106-46.circ.txt` |
| 35/3/143/18 | other | +4 / -9 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T3-t3-g143-a35-gd18-ad3.circ.txt` |
| 35/3/144/17 | other | +5 / -10 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g144-gd17-xx109-43.circ.txt` |
| 35/3/147/16 | other | +8 / -11 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g147-gd16-xx112-56.circ.txt` |
| 35/3/155/15 | other | +16 / -12 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g155-gd15-xx120-56.circ.txt` |
| 35/3/162/14 | other | +23 / -13 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-F-trb-g162-a35-gd14-ad3.circ.txt` |
| 35/3/165/13 | other | +26 / -14 | new (M3) | unknown | none | 2 | `~/xs-campaigns/2026-11-15-targets/M3/found/rebase-a35-ad3-g165-gd13-7e6507bb2b.circ.txt` |
| 35/3/181/12 | other | +42 / -15 | known-by-23:50 (P6; new vs archive); reproduced by M3 | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt) | none | 3 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 35/3/138/23 | strict | -1 / -4 | new (night:T07) | certified (~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd23-3ed8aa97bd.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd23-3ed8aa97bd.circ.txt` |
| 35/3/139/21 | strict | +0 / -6 | new (night:T07) | certified (~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd21-f71f0d11d1.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd21-f71f0d11d1.circ.txt` |

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

none

### (A, AD, G, GD) Pareto frontier within the hard limits (11 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 35/3/137/28 | other | -2 / +1 | known-by-23:50 (P6; new vs archive) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt` |
| 35/3/138/23 | strict | -1 / -4 | new (night:T07) | certified (~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd23-3ed8aa97bd.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd23-3ed8aa97bd.circ.txt` |
| 35/3/139/21 | strict | +0 / -6 | new (night:T07) | certified (~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd21-f71f0d11d1.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd21-f71f0d11d1.circ.txt` |
| 35/3/141/19 | other | +2 / -8 | known | n/a (known) | none | 5 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g141-gd19-xx106-46.circ.txt` |
| 35/3/143/18 | other | +4 / -9 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T3-t3-g143-a35-gd18-ad3.circ.txt` |
| 35/3/144/17 | other | +5 / -10 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g144-gd17-xx109-43.circ.txt` |
| 35/3/147/16 | other | +8 / -11 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g147-gd16-xx112-56.circ.txt` |
| 35/3/155/15 | other | +16 / -12 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g155-gd15-xx120-56.circ.txt` |
| 35/3/162/14 | other | +23 / -13 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-F-trb-g162-a35-gd14-ad3.circ.txt` |
| 35/3/165/13 | other | +26 / -14 | new (M3) | unknown | none | 2 | `~/xs-campaigns/2026-11-15-targets/M3/found/rebase-a35-ad3-g165-gd13-7e6507bb2b.circ.txt` |
| 35/3/181/12 | other | +42 / -15 | known-by-23:50 (P6; new vs archive); reproduced by M3 | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt) | none | 3 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt` |

Pinned NIST (G, GD) frontier within the same hard limits: 35/3/139/27 aes-sbox-a35-ad3-g139-gd27-xx104-38.circ.txt, 35/3/141/25 aes-sbox-a35-ad3-g141-gd25-xx106-37.circ.txt, 35/3/147/20 aes-sbox-a35-ad3-g147-gd20-xx112-36.circ.txt, 35/3/157/15 aes-sbox-a35-ad3-g157-gd15-xx122-31.circ.txt, 35/3/172/14 aes-sbox-a35-ad3-g172-gd14-xx137-30.circ.txt, 35/3/183/13 aes-sbox-a35-ad3-g183-gd13-xx148-29.circ.txt

## T08: reference 35/3/183/13 `aes-sbox-a35-ad3-g183-gd13-xx148-29.circ.txt`

Hard limits A <= 35, AD <= 3. Primary: GD <= 12, preferably with G <= 183; secondary G much lower with GD <= 13. Ideal: both. Tradeoffs allowed: [{'kind': 'depth_for_gates', 'GD_max': 12}].

339 verified files within the hard limits, 251 distinct structures, 113 distinct tuples.

- Best strict (by G, then GD): **35/3/165/13** (strict), new (M3), path: unknown, `~/xs-campaigns/2026-11-15-targets/M3/found/rebase-a35-ad3-g165-gd13-7e6507bb2b.circ.txt` (sha256 7e6507bb2b23)
  - start: ~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt sha256 cb0edda7231e; method: {'engine': 'ops/rebase.py: gbasis class re-basing + P6 hybrid build + capped gate kernel', 'operator': 'rebase'}; seed: 52; elapsed: 413.7 s
  - verification: OK   /home/joebachir20/xs-campaigns/2026-11-15-targets/M3/runs/screen/rb-t08c13c/rebase-a35-ad3-g165-gd13-7e6507bb2b.circ.txt  A AD G GD = 35 3 165 13  counts {'AND': 35, 'XNOR': 72, 'XOR': 58}; ledger re-check OK
  - pinned NIST dominating: none

- Best strict (by GD, then G): **35/3/181/12** (strict), known-by-23:50 (P6; new vs archive); reproduced by M3, path: certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt), `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt` (sha256 2adedf9e5cd9)
  - start: ~/xs-campaigns/2026-11-15-targets/P6/runs/pull12c/jobs/9552bd8ad634-r0-s0/start.bfx sha256 5eb67aab692c; method: P6 depth pull: 177@13 -> GF(4) one-point coordinate move (T3 gf4build keep2, points [14,25,180,72]; l3scan max Kraft 0.75 at cap 12) -> class re-basing + hybrid build --paar (204@12) -> gate kernel hub.ops._kernel caps A35 AD3 GD12, cost,gd, 240 s stage; seed: 397181; elapsed: 240.0 s
  - verification: OK   /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt  A AD G GD = 35 3 181 12  counts {'AND': 35, 'XNOR': 63, 'XOR': 83}; ledger re-check OK
  - pinned NIST dominating: none

- Best tradeoff: none


### (G, GD) Pareto frontier within the hard limits

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 35/3/137/28 | other | -46 / +15 | known-by-23:50 (P6; new vs archive) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt` |
| 35/3/138/23 | other | -45 / +10 | new (night:T07) | certified (~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd23-3ed8aa97bd.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd23-3ed8aa97bd.circ.txt` |
| 35/3/139/21 | other | -44 / +8 | new (night:T07) | certified (~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd21-f71f0d11d1.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd21-f71f0d11d1.circ.txt` |
| 35/3/141/19 | other | -42 / +6 | known | n/a (known) | none | 5 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g141-gd19-xx106-46.circ.txt` |
| 35/3/143/18 | other | -40 / +5 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T3-t3-g143-a35-gd18-ad3.circ.txt` |
| 35/3/144/17 | other | -39 / +4 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g144-gd17-xx109-43.circ.txt` |
| 35/3/147/16 | other | -36 / +3 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g147-gd16-xx112-56.circ.txt` |
| 35/3/155/15 | other | -28 / +2 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g155-gd15-xx120-56.circ.txt` |
| 35/3/162/14 | other | -21 / +1 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-F-trb-g162-a35-gd14-ad3.circ.txt` |
| 35/3/165/13 | strict | -18 / +0 | new (M3) | unknown | none | 2 | `~/xs-campaigns/2026-11-15-targets/M3/found/rebase-a35-ad3-g165-gd13-7e6507bb2b.circ.txt` |
| 35/3/181/12 | strict | -2 / -1 | known-by-23:50 (P6; new vs archive); reproduced by M3 | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt) | none | 3 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 35/3/165/13 | strict | -18 / +0 | new (M3) | unknown | none | 2 | `~/xs-campaigns/2026-11-15-targets/M3/found/rebase-a35-ad3-g165-gd13-7e6507bb2b.circ.txt` |
| 35/3/181/12 | strict | -2 / -1 | known-by-23:50 (P6; new vs archive); reproduced by M3 | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt) | none | 3 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt` |

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

none

### (A, AD, G, GD) Pareto frontier within the hard limits (11 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 35/3/137/28 | other | -46 / +15 | known-by-23:50 (P6; new vs archive) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt` |
| 35/3/138/23 | other | -45 / +10 | new (night:T07) | certified (~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd23-3ed8aa97bd.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd23-3ed8aa97bd.circ.txt` |
| 35/3/139/21 | other | -44 / +8 | new (night:T07) | certified (~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd21-f71f0d11d1.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd21-f71f0d11d1.circ.txt` |
| 35/3/141/19 | other | -42 / +6 | known | n/a (known) | none | 5 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g141-gd19-xx106-46.circ.txt` |
| 35/3/143/18 | other | -40 / +5 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T3-t3-g143-a35-gd18-ad3.circ.txt` |
| 35/3/144/17 | other | -39 / +4 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g144-gd17-xx109-43.circ.txt` |
| 35/3/147/16 | other | -36 / +3 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g147-gd16-xx112-56.circ.txt` |
| 35/3/155/15 | other | -28 / +2 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g155-gd15-xx120-56.circ.txt` |
| 35/3/162/14 | other | -21 / +1 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-F-trb-g162-a35-gd14-ad3.circ.txt` |
| 35/3/165/13 | strict | -18 / +0 | new (M3) | unknown | none | 2 | `~/xs-campaigns/2026-11-15-targets/M3/found/rebase-a35-ad3-g165-gd13-7e6507bb2b.circ.txt` |
| 35/3/181/12 | strict | -2 / -1 | known-by-23:50 (P6; new vs archive); reproduced by M3 | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt) | none | 3 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt` |

Pinned NIST (G, GD) frontier within the same hard limits: 35/3/139/27 aes-sbox-a35-ad3-g139-gd27-xx104-38.circ.txt, 35/3/141/25 aes-sbox-a35-ad3-g141-gd25-xx106-37.circ.txt, 35/3/147/20 aes-sbox-a35-ad3-g147-gd20-xx112-36.circ.txt, 35/3/157/15 aes-sbox-a35-ad3-g157-gd15-xx122-31.circ.txt, 35/3/172/14 aes-sbox-a35-ad3-g172-gd14-xx137-30.circ.txt, 35/3/183/13 aes-sbox-a35-ad3-g183-gd13-xx148-29.circ.txt

## T09: reference 45/4/141/12 `aes-sbox-a45-ad4-g141-gd12-xx96-25.circ.txt`

Hard limits A <= 45, AD <= 4. Primary: G < 141 with GD <= 12; equally GD <= 11 with G <= 141. Ideal: both. Tradeoffs allowed: [{'kind': 'depth_for_gates', 'GD_max': 11}].

2445 verified files within the hard limits, 1854 distinct structures, 924 distinct tuples.

- Best strict (by G, then GD): **38/4/135/12** (strict), new (night:T09), path: unknown, `~/xs-campaigns/2026-11-16-night/T09/found/bottom-a38-ad4-g135-gd12-ff41a311d8.circ.txt` (sha256 ff41a311d813)
  - start: ~/xs-campaigns/2026-11-16-night/T09/found/bottom-a39-ad4-g138-gd12-09d79a36df.circ.txt sha256 09d79a36df06; method: {'engine': 'ops/bottom.py: P7 bopt SA (rank-1 shared bottom, exact Kraft per output) + bbuild + A-capped gate kernel', 'operator': 'bottom'}; seed: 432999; elapsed: 514.4 s
  - verification: OK   /home/joebachir20/xs-campaigns/2026-11-16-night/T09/found/bottom-a38-ad4-g135-gd12-ff41a311d8.circ.txt  A AD G GD = 38 4 135 12  counts {'AND': 38, 'XNOR': 25, 'XOR': 72}; ledger re-check OK
  - pinned NIST dominating: none

- Best tradeoff: none


### (G, GD) Pareto frontier within the hard limits

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 33/4/105/25 | other | -36 / +13 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/0f491596c734.bfx` |
| 33/4/106/22 | other | -35 / +10 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g106-gd22-xx73-5.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/26070040d746.bfx` |
| 33/4/107/20 | other | -34 / +8 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-pull-g107-a33-gd20-ad4.circ.txt` |
| 33/4/108/19 | other | -33 / +7 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt` |
| 33/4/110/18 | other | -31 / +6 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad4-a33-g110-a33-gd18-ad4.circ.txt` |
| 33/4/112/16 | other | -29 / +4 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g112-a33-gd16-ad4.circ.txt` |
| 33/4/115/15 | other | -26 / +3 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-join-g115-a33-gd15-ad4.circ.txt` |
| 37/4/121/14 | other | -20 / +2 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-D-kernel-g121-a37-gd14-ad4.circ.txt` |
| 37/4/127/13 | other | -14 / +1 | new (night:T09) | not certified | none | 1 | `~/xs-campaigns/2026-11-16-night/T09/found/conjpull-a37-ad4-g127-gd13-00578f7482.circ.txt` |
| 38/4/135/12 | strict | -6 / +0 | new (night:T09) | unknown | none | 1 | `~/xs-campaigns/2026-11-16-night/T09/found/bottom-a38-ad4-g135-gd12-ff41a311d8.circ.txt` |
| 44/4/254/11 | other | +113 / -1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T4-t4-g254-a44-gd11-ad4.circ.txt` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 38/4/135/12 | strict | -6 / +0 | new (night:T09) | unknown | none | 1 | `~/xs-campaigns/2026-11-16-night/T09/found/bottom-a38-ad4-g135-gd12-ff41a311d8.circ.txt` |

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

none

### (A, AD, G, GD) Pareto frontier within the hard limits (54 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | other | -11 / +12 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | other | -10 / +10 | known; reproduced by night:T01 | n/a (known) | none | 8 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | other | -9 / +8 | known; reproduced by night:T01 | n/a (known) | none | 5 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | other | -8 / +7 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | other | -6 / +6 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | other | -3 / +5 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | other | +0 / +4 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | other | +12 / +3 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | other | +33 / +2 | known-by-23:50 (P2; new vs archive); reproduced by night:T02 | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |
| 29/4/128/23 | other | -13 / +11 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-X2-x2-g128-a29-gd23-ad4.circ.txt` |
| 29/4/129/19 | other | -12 / +7 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g129-gd19-xx100-56.circ.txt` |
| 29/4/131/17 | other | -10 / +5 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g131-gd17-xx102-61.circ.txt` |
| 29/4/135/16 | other | -6 / +4 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g135-gd16-xx106-50.circ.txt` |
| 29/4/141/15 | other | +0 / +3 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g141-gd15-xx112-56.circ.txt` |
| 30/4/138/15 | other | -3 / +3 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a30-ad4-g138-gd15-xx108-61.circ.txt` |
| 32/4/111/25 | other | -30 / +13 | known-by-23:50 (P5; new vs archive); reproduced by night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt` |
| 32/4/112/21 | other | -29 / +9 | new (M4) | unknown | none | 2 | `~/xs-campaigns/2026-11-15-targets/M4/found/satlns-a32-ad4-g112-gd21-efda23263f.circ.txt` |
| 32/4/113/20 | other | -28 / +8 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt) | none | 12 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt` |
| 32/4/114/19 | other | -27 / +7 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt) | none | 17 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt` |
| 32/4/115/18 | other | -26 / +6 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt` |
| 32/4/117/17 | other | -24 / +5 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` |
| 32/4/119/16 | other | -22 / +4 | new (night:T04) | not certified (inherited from conjpull-a32-ad4-g117-gd17-b83f9deb89.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-16-night/T04/found/conjpull-a32-ad4-g119-gd16-3acd9d4790.circ.txt` |
| 32/4/125/15 | other | -16 / +3 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt` |
| 33/4/105/25 | other | -36 / +13 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/0f491596c734.bfx` |
| 33/4/106/22 | other | -35 / +10 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g106-gd22-xx73-5.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/26070040d746.bfx` |
| 33/4/107/20 | other | -34 / +8 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-pull-g107-a33-gd20-ad4.circ.txt` |
| 33/4/108/19 | other | -33 / +7 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt` |
| 33/4/110/18 | other | -31 / +6 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad4-a33-g110-a33-gd18-ad4.circ.txt` |
| 33/4/112/16 | other | -29 / +4 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g112-a33-gd16-ad4.circ.txt` |
| 33/4/115/15 | other | -26 / +3 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-join-g115-a33-gd15-ad4.circ.txt` |
| 33/4/125/14 | other | -16 / +2 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g125-gd14-xx92-18.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/1317ec0f73e9.bfx` |
| 34/4/122/14 | other | -19 / +2 | new (night:T06) | certified (~/xs-campaigns/2026-11-16-night/T06/found/conjpull-a34-ad4-g122-gd14-621f73cda5.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T06/found/conjpull-a34-ad4-g122-gd14-621f73cda5.circ.txt` |
| 34/4/134/13 | other | -7 / +1 | known | n/a (known) | none | 3 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g134-a34-gd13-ad4.circ.txt` |
| 35/3/137/28 | other | -4 / +16 | known-by-23:50 (P6; new vs archive) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt` |
| 35/3/138/23 | other | -3 / +11 | new (night:T07) | certified (~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd23-3ed8aa97bd.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd23-3ed8aa97bd.circ.txt` |
| 35/3/139/21 | other | -2 / +9 | new (night:T07) | certified (~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd21-f71f0d11d1.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd21-f71f0d11d1.circ.txt` |
| 35/3/141/19 | other | +0 / +7 | known | n/a (known) | none | 5 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g141-gd19-xx106-46.circ.txt` |
| 35/3/143/18 | other | +2 / +6 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T3-t3-g143-a35-gd18-ad3.circ.txt` |
| 35/3/144/17 | other | +3 / +5 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g144-gd17-xx109-43.circ.txt` |
| 35/3/147/16 | other | +6 / +4 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g147-gd16-xx112-56.circ.txt` |
| 35/3/155/15 | other | +14 / +3 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g155-gd15-xx120-56.circ.txt` |
| 35/3/162/14 | other | +21 / +2 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-F-trb-g162-a35-gd14-ad3.circ.txt` |
| 35/3/165/13 | other | +24 / +1 | new (M3) | unknown | none | 2 | `~/xs-campaigns/2026-11-15-targets/M3/found/rebase-a35-ad3-g165-gd13-7e6507bb2b.circ.txt` |
| 35/3/181/12 | other | +40 / +0 | known-by-23:50 (P6; new vs archive); reproduced by M3 | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt) | none | 3 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt` |
| 35/4/133/13 | other | -8 / +1 | known | n/a (known) | none; equal tuple: aes-sbox-a35-ad4-g133-gd13-xx98-21.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/4a3bb5d58502.bfx` |
| 36/3/161/14 | other | +20 / +2 | known | n/a (known) | none | 3 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-osc-g161-a36-gd14-ad3.circ.txt` |
| 36/4/129/13 | other | -12 / +1 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g129-a36-gd13-ad4.circ.txt` |
| 37/3/160/14 | other | +19 / +2 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g160-a37-gd14-ad3.circ.txt` |
| 37/4/121/14 | other | -20 / +2 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-D-kernel-g121-a37-gd14-ad4.circ.txt` |
| 37/4/127/13 | other | -14 / +1 | new (night:T09) | not certified | none | 1 | `~/xs-campaigns/2026-11-16-night/T09/found/conjpull-a37-ad4-g127-gd13-00578f7482.circ.txt` |
| 38/4/135/12 | strict | -6 / +0 | new (night:T09) | unknown | none | 1 | `~/xs-campaigns/2026-11-16-night/T09/found/bottom-a38-ad4-g135-gd12-ff41a311d8.circ.txt` |
| 42/4/284/11 | other | +143 / -1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T4-t4-g284-a42-gd11-ad4.circ.txt` |
| 43/4/278/11 | other | +137 / -1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T4-t4-g278-a43-gd11-ad4.circ.txt` |
| 44/4/254/11 | other | +113 / -1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T4-t4-g254-a44-gd11-ad4.circ.txt` |

Pinned NIST (G, GD) frontier within the same hard limits: 33/4/105/25 aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt, 33/4/106/22 aes-sbox-a33-ad4-g106-gd22-xx73-5.circ.txt, 33/4/108/20 aes-sbox-a33-ad4-g108-gd20-xx75-5.circ.txt, 33/4/116/15 aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt, 33/4/125/14 aes-sbox-a33-ad4-g125-gd14-xx92-18.circ.txt, 35/4/133/13 aes-sbox-a35-ad4-g133-gd13-xx98-21.circ.txt, 45/4/141/12 aes-sbox-a45-ad4-g141-gd12-xx96-25.circ.txt

## T10: reference 59/4/159/10 `aes-sbox-a59-ad4-g159-gd10-xxn100-30-3.circ.txt`

Hard limits A <= 59, AD <= 4. Primary: G < 159 with GD <= 10; ambitious GD <= 9 preferably with G <= 159. Ideal: both; GD 10 is not a proven bound. Tradeoffs allowed: [{'kind': 'depth_for_gates', 'GD_max': 9}].

2578 verified files within the hard limits, 1959 distinct structures, 1005 distinct tuples.

- Best strict (by G, then GD): none

- Best tradeoff: none


### (G, GD) Pareto frontier within the hard limits

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 33/4/105/25 | other | -54 / +15 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/0f491596c734.bfx` |
| 33/4/106/22 | other | -53 / +12 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g106-gd22-xx73-5.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/26070040d746.bfx` |
| 33/4/107/20 | other | -52 / +10 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-pull-g107-a33-gd20-ad4.circ.txt` |
| 33/4/108/19 | other | -51 / +9 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt` |
| 33/4/110/18 | other | -49 / +8 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad4-a33-g110-a33-gd18-ad4.circ.txt` |
| 33/4/112/16 | other | -47 / +6 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g112-a33-gd16-ad4.circ.txt` |
| 33/4/115/15 | other | -44 / +5 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-join-g115-a33-gd15-ad4.circ.txt` |
| 37/4/121/14 | other | -38 / +4 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-D-kernel-g121-a37-gd14-ad4.circ.txt` |
| 37/4/127/13 | other | -32 / +3 | new (night:T09) | not certified | none | 1 | `~/xs-campaigns/2026-11-16-night/T09/found/conjpull-a37-ad4-g127-gd13-00578f7482.circ.txt` |
| 38/4/135/12 | other | -24 / +2 | new (night:T09) | unknown | none | 1 | `~/xs-campaigns/2026-11-16-night/T09/found/bottom-a38-ad4-g135-gd12-ff41a311d8.circ.txt` |
| 49/4/148/11 | other | -11 / +1 | known | n/a (known) | none; equal tuple: aes-sbox-a49-ad4-g148-gd11-xx99-23.circ.txt | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd11-ad4-a49-g148-a49-gd11-ad4.circ.txt` |
| 59/4/159/10 | other | +0 / +0 | known | n/a (known) | none; equal tuple: aes-sbox-a59-ad4-g159-gd10-xxn100-30-3.circ.txt | 3 | `~/xs-campaigns/2026-11-14-hub/long/archive/0ab3e1c5b961.bfx` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

none

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

none

### (A, AD, G, GD) Pareto frontier within the hard limits (59 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | other | -29 / +14 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | other | -28 / +12 | known; reproduced by night:T01 | n/a (known) | none | 8 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | other | -27 / +10 | known; reproduced by night:T01 | n/a (known) | none | 5 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | other | -26 / +9 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | other | -24 / +8 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | other | -21 / +7 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | other | -18 / +6 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | other | -6 / +5 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | other | +15 / +4 | known-by-23:50 (P2; new vs archive); reproduced by night:T02 | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |
| 29/4/128/23 | other | -31 / +13 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-X2-x2-g128-a29-gd23-ad4.circ.txt` |
| 29/4/129/19 | other | -30 / +9 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g129-gd19-xx100-56.circ.txt` |
| 29/4/131/17 | other | -28 / +7 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g131-gd17-xx102-61.circ.txt` |
| 29/4/135/16 | other | -24 / +6 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g135-gd16-xx106-50.circ.txt` |
| 29/4/141/15 | other | -18 / +5 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g141-gd15-xx112-56.circ.txt` |
| 30/4/138/15 | other | -21 / +5 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a30-ad4-g138-gd15-xx108-61.circ.txt` |
| 32/4/111/25 | other | -48 / +15 | known-by-23:50 (P5; new vs archive); reproduced by night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt` |
| 32/4/112/21 | other | -47 / +11 | new (M4) | unknown | none | 2 | `~/xs-campaigns/2026-11-15-targets/M4/found/satlns-a32-ad4-g112-gd21-efda23263f.circ.txt` |
| 32/4/113/20 | other | -46 / +10 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt) | none | 12 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt` |
| 32/4/114/19 | other | -45 / +9 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt) | none | 17 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt` |
| 32/4/115/18 | other | -44 / +8 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt` |
| 32/4/117/17 | other | -42 / +7 | known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05 | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt) | none | 5 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` |
| 32/4/119/16 | other | -40 / +6 | new (night:T04) | not certified (inherited from conjpull-a32-ad4-g117-gd17-b83f9deb89.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-16-night/T04/found/conjpull-a32-ad4-g119-gd16-3acd9d4790.circ.txt` |
| 32/4/125/15 | other | -34 / +5 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt` |
| 33/4/105/25 | other | -54 / +15 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/0f491596c734.bfx` |
| 33/4/106/22 | other | -53 / +12 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g106-gd22-xx73-5.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/26070040d746.bfx` |
| 33/4/107/20 | other | -52 / +10 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-pull-g107-a33-gd20-ad4.circ.txt` |
| 33/4/108/19 | other | -51 / +9 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt` |
| 33/4/110/18 | other | -49 / +8 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad4-a33-g110-a33-gd18-ad4.circ.txt` |
| 33/4/112/16 | other | -47 / +6 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g112-a33-gd16-ad4.circ.txt` |
| 33/4/115/15 | other | -44 / +5 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-join-g115-a33-gd15-ad4.circ.txt` |
| 33/4/125/14 | other | -34 / +4 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g125-gd14-xx92-18.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/1317ec0f73e9.bfx` |
| 34/4/122/14 | other | -37 / +4 | new (night:T06) | certified (~/xs-campaigns/2026-11-16-night/T06/found/conjpull-a34-ad4-g122-gd14-621f73cda5.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T06/found/conjpull-a34-ad4-g122-gd14-621f73cda5.circ.txt` |
| 34/4/134/13 | other | -25 / +3 | known | n/a (known) | none | 3 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g134-a34-gd13-ad4.circ.txt` |
| 35/3/137/28 | other | -22 / +18 | known-by-23:50 (P6; new vs archive) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt` |
| 35/3/138/23 | other | -21 / +13 | new (night:T07) | certified (~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd23-3ed8aa97bd.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd23-3ed8aa97bd.circ.txt` |
| 35/3/139/21 | other | -20 / +11 | new (night:T07) | certified (~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd21-f71f0d11d1.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd21-f71f0d11d1.circ.txt` |
| 35/3/141/19 | other | -18 / +9 | known | n/a (known) | none | 5 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g141-gd19-xx106-46.circ.txt` |
| 35/3/143/18 | other | -16 / +8 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T3-t3-g143-a35-gd18-ad3.circ.txt` |
| 35/3/144/17 | other | -15 / +7 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g144-gd17-xx109-43.circ.txt` |
| 35/3/147/16 | other | -12 / +6 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g147-gd16-xx112-56.circ.txt` |
| 35/3/155/15 | other | -4 / +5 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g155-gd15-xx120-56.circ.txt` |
| 35/3/162/14 | other | +3 / +4 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-F-trb-g162-a35-gd14-ad3.circ.txt` |
| 35/3/165/13 | other | +6 / +3 | new (M3) | unknown | none | 2 | `~/xs-campaigns/2026-11-15-targets/M3/found/rebase-a35-ad3-g165-gd13-7e6507bb2b.circ.txt` |
| 35/3/181/12 | other | +22 / +2 | known-by-23:50 (P6; new vs archive); reproduced by M3 | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt) | none | 3 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt` |
| 35/4/133/13 | other | -26 / +3 | known | n/a (known) | none; equal tuple: aes-sbox-a35-ad4-g133-gd13-xx98-21.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/4a3bb5d58502.bfx` |
| 36/3/161/14 | other | +2 / +4 | known | n/a (known) | none | 3 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-osc-g161-a36-gd14-ad3.circ.txt` |
| 36/4/129/13 | other | -30 / +3 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g129-a36-gd13-ad4.circ.txt` |
| 37/3/160/14 | other | +1 / +4 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g160-a37-gd14-ad3.circ.txt` |
| 37/4/121/14 | other | -38 / +4 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-D-kernel-g121-a37-gd14-ad4.circ.txt` |
| 37/4/127/13 | other | -32 / +3 | new (night:T09) | not certified | none | 1 | `~/xs-campaigns/2026-11-16-night/T09/found/conjpull-a37-ad4-g127-gd13-00578f7482.circ.txt` |
| 38/4/135/12 | other | -24 / +2 | new (night:T09) | unknown | none | 1 | `~/xs-campaigns/2026-11-16-night/T09/found/bottom-a38-ad4-g135-gd12-ff41a311d8.circ.txt` |
| 42/4/284/11 | other | +125 / +1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T4-t4-g284-a42-gd11-ad4.circ.txt` |
| 43/4/278/11 | other | +119 / +1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T4-t4-g278-a43-gd11-ad4.circ.txt` |
| 44/4/254/11 | other | +95 / +1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T4-t4-g254-a44-gd11-ad4.circ.txt` |
| 46/4/200/11 | other | +41 / +1 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a46-ad4-g200-gd11-xx154-63.circ.txt` |
| 47/4/186/11 | other | +27 / +1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T4-t4-g186-a47-gd11-ad4.circ.txt` |
| 48/4/151/11 | other | -8 / +1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g151-a48-gd11-ad4.circ.txt` |
| 49/4/148/11 | other | -11 / +1 | known | n/a (known) | none; equal tuple: aes-sbox-a49-ad4-g148-gd11-xx99-23.circ.txt | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd11-ad4-a49-g148-a49-gd11-ad4.circ.txt` |
| 59/4/159/10 | other | +0 / +0 | known | n/a (known) | none; equal tuple: aes-sbox-a59-ad4-g159-gd10-xxn100-30-3.circ.txt | 3 | `~/xs-campaigns/2026-11-14-hub/long/archive/0ab3e1c5b961.bfx` |

Pinned NIST (G, GD) frontier within the same hard limits: 33/4/105/25 aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt, 33/4/106/22 aes-sbox-a33-ad4-g106-gd22-xx73-5.circ.txt, 33/4/108/20 aes-sbox-a33-ad4-g108-gd20-xx75-5.circ.txt, 33/4/116/15 aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt, 33/4/125/14 aes-sbox-a33-ad4-g125-gd14-xx92-18.circ.txt, 35/4/133/13 aes-sbox-a35-ad4-g133-gd13-xx98-21.circ.txt, 45/4/141/12 aes-sbox-a45-ad4-g141-gd12-xx96-25.circ.txt, 49/4/148/11 aes-sbox-a49-ad4-g148-gd11-xx99-23.circ.txt, 59/4/159/10 aes-sbox-a59-ad4-g159-gd10-xxn100-30-3.circ.txt

## All campaign circuit files (614)

| agent | file | ok | A/AD/G/GD | target | status | path | seed | elapsed_s | method |
|---|---|---|---|---|---|---|---|---|---|
| M3 | `bottom-a41-ad4-g136-gd12-41a5a50d86.circ.txt` | OK | 41/4/136/12 | T09 | reproduced-known-by-23:50 | unknown | 7002 | 880.3 | {'engine': 'ops/bottom.py: P7 bopt SA (rank-1 shared bottom, exact Kraft per out |
| M3 | `bottom-a41-ad4-g137-gd12-5ac2181b5c.circ.txt` | OK | 41/4/137/12 | T09 | reproduced-known-by-23:50 | unknown | 7002 | 385.8 | {'engine': 'ops/bottom.py: P7 bopt SA (rank-1 shared bottom, exact Kraft per out |
| M3 | `rebase-a35-ad3-g165-gd13-7e6507bb2b.circ.txt` | OK | 35/3/165/13 | T08 | new | unknown | 52 | 413.7 | {'engine': 'ops/rebase.py: gbasis class re-basing + P6 hybrid build + capped gat |
| M3 | `rebase-a35-ad3-g167-gd13-6e861fc3c8.circ.txt` | OK | 35/3/167/13 | T08 | new | unknown | 41 | 489.4 | {'engine': 'ops/rebase.py: gbasis class re-basing + P6 hybrid build + capped gat |
| M3 | `rebase-a35-ad3-g181-gd12-63aaf33ed1.circ.txt` | OK | 35/3/181/12 | T08 | reproduced-known-by-23:50 | unknown | 31 | 468.9 | {'engine': 'ops/rebase.py: gbasis class re-basing + P6 hybrid build + capped gat |
| M3 | `rebase-a35-ad3-g181-gd12-abe131a677.circ.txt` | OK | 35/3/181/12 | T08 | reproduced-known-by-23:50 | unknown | 21 | 257.6 | {'engine': 'ops/rebase.py: gbasis class re-basing + P6 hybrid build + capped gat |
| M4 | `satlns-a32-ad4-g112-gd21-efda23263f.circ.txt` | OK | 32/4/112/21 | T04 | new | unknown | 23 | 584.2 | {'engine': 'campaigns/targets/ops/satlns.py (span-pooled SAT LNS, pysat glucose4 |
| P1 | `P1-T03-a28-ad5-g129-gd19-04c1f2de0543.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 337 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-15cf294dce41.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 306 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-182597994ba6.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 284 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-22a009ce455a.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 361 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-2bca397809b9.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 314 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-2e75bcd9ff9d.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 293 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-3128f33c96ca.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 463 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-36167d73d14f.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 436 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-3714500a3ba9.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 301 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-432a787aeaf2.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 244 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-438ed7f28c0b.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 283 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-4436561a4144.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 418 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-445304d0406e.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 437 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-4a3ef4c61095.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 346 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-5832ee7d6edb.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 355 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-6001a9a9b976.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 414 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-65280a926d2b.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 439 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-6fb1d29906a2.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 377 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-7327a44f9895.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 250 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-86c563534eef.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 278 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-8fe98f6d1cf6.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 383 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-a18cfce0dce1.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 330 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-b3fe2f6e3f5d.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 448 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-b8536ab17ef6.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 358 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-b94e853fc505.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 427 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-baa05182d857.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 327 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-bb726d78f2fe.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 321 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-bdf13f65c41f.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 340 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-c192be76787d.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 424 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-c4ff2fe1413e.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 420 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-c57b40b919c4.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 469 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-c6ad4ac8f023.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 364 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-cf6607647a0a.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 387 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-d0e026e8c4ad.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 440 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-d2ca9972aecf.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 403 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-d973cc3e5713.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 378 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-d9ea2f0eec0f.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 318 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-da61d52b387b.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 453 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-dc9cca09a667.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 370 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-dfc0717b1798.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 365 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-ec51e03b02b5.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 241 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-f04ad7f01ee8.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 428 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-f485696fb088.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 344 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-fcfb3b6c3efe.circ.txt` | OK | 28/5/129/19 | T03 | known-by-23:50 | unknown | 23 | not logged per step by this version (run total 900 s; step 350 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P2 | `t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` | OK | 28/4/174/14 | T02 | known-by-23:50 | certified | 1 | 2437.0 | strategies/F/fdrive.py mode mix (gate/osc/trb), stage 17 trb-bottom (timing-driv |
| P2 | `t02-a28-ad4-g174-gd14-t02mix1.circ.txt` | OK | 28/4/174/14 | T02 | known-by-23:50 | certified | 1 | 7202.0 | strategies/F/fdrive.py mode mix, caps GD14 AD4 A28, kernel bfx-593fa798f5 |
| P2 | `t06-a34-ad4-g134-gd14-t06bopt-s5.circ.txt` | OK | 34/4/134/14 | T06 | known-by-23:50 | certified | 5 | 1201.0 | strategies/P2/fdrive_p2.py mode gate, caps GD13 AD4 A34, kernel bfx-94a75e2c18,  |
| P2 | `t06-a34-ad4-g135-gd13-t06rs-c0011-g161.circ.txt` | OK | 34/4/135/13 | T06 | known-by-23:50 | certified | 611 | 1501.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g135-gd13-t06rs-c0022-g159.circ.txt` | OK | 34/4/135/13 | T06 | known-by-23:50 | certified | 622 | 1500.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g135-gd14-t06bopt-s6.circ.txt` | OK | 34/4/135/14 | T06 | reproduced | certified | 6 | 900.0 | strategies/P2/fdrive_p2.py mode gate, caps GD13 AD4 A34, kernel bfx-94a75e2c18,  |
| P2 | `t06-a34-ad4-g136-gd13-t06rs16trb52.circ.txt` | OK | 34/4/136/13 | T06 | known-by-23:50 | certified | 52 | 1801.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g136-gd13-t06rs5trb51.circ.txt` | OK | 34/4/136/13 | T06 | known-by-23:50 | certified | 51 | 1800.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g137-gd13-t06rs-c0010-g158.circ.txt` | OK | 34/4/137/13 | T06 | known-by-23:50 | certified | 610 | 1500.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g137-gd13-t06rs-c0021-g160.circ.txt` | OK | 34/4/137/13 | T06 | known-by-23:50 | certified | 621 | 1500.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g141-gd13-ev-t06a-p1.circ.txt` | OK | 34/4/141/13 | T06 | reproduced | certified | 901 | 900.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g141-gd13-t06rs-c0008-g168.circ.txt` | OK | 34/4/141/13 | T06 | reproduced | certified | 608 | 1500.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g141-gd13-t06rs-c0018-g167.circ.txt` | OK | 34/4/141/13 | T06 | reproduced | certified | 618 | 1501.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g142-gd13-ev-t06a-p2.circ.txt` | OK | 34/4/142/13 | T06 | reproduced | certified | 902 | 900.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g142-gd13-ev-t06b-p3.circ.txt` | OK | 34/4/142/13 | T06 | reproduced | certified | 903 | 899.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g143-gd13-ev-t06b-p2.circ.txt` | OK | 34/4/143/13 | T06 | known-by-23:50 | certified | 902 | 900.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g144-gd13-ev-t06a-p3.circ.txt` | OK | 34/4/144/13 | T06 | known-by-23:50 | certified | 903 | 900.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g146-gd13-ev-t06b-p1.circ.txt` | OK | 34/4/146/13 | T06 | known-by-23:50 | certified | 901 | 900.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P3 | `p3-c115-p19a-a32-ad4-g116-gd19-20c5d2b662.circ.txt` | OK | 32/4/116/19 | T04 | known-by-23:50 | certified | 2 | 145.0 | pdrive mix (gate/osc/trb) caps A32 AD4 GD19, stage 1 osc (kernel at cap 20, then |
| P3 | `p3-c115-p19a-a32-ad4-g116-gd19-b49b2addfa.circ.txt` | OK | 32/4/116/19 | T04 | known-by-23:50 | certified | 2 | 903.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-c116-m19-a32-ad4-g116-gd19-21ad562580.circ.txt` | OK | 32/4/116/19 | T04 | known-by-23:50 | certified | 4 | 901.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-cj188-p21-a32-ad4-g115-gd20-098ecd13af.circ.txt` | OK | 32/4/115/20 | T04 | known-by-23:50 | certified | 1 | 900.0 | pdrive mix (gate/osc/trb) caps A32 AD4 GD21 from the conjugate-derived 114@23; k |
| P3 | `p3-cj188c26-a32-ad4-g114-gd23-a114ea59bf.circ.txt` | OK | 32/4/114/23 | T04 | known-by-23:50 | certified | 1 | 300.0 | conjugate lam=188 k=0 of NIST-equivalent 117@19 (conj.py/mkconj.py: inputs x->18 |
| P3 | `p3-pipe-conj-116g20-l188-k0-m21-a32-ad4-g113-gd20-db41c24e64.circ.txt` | OK | 32/4/113/20 | T04 | known-by-23:50 | not certified | 2 | 362.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-pipe-conj-116g20-l188-k0-m21-a32-ad4-g113-gd21-197c32efc7.circ.txt` | OK | 32/4/113/21 | T04 | known-by-23:50 | not certified | 2 | 362.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-pipe116m19-a32-ad4-g114-gd19-a59961d7ad.circ.txt` | OK | 32/4/114/19 | T04 | known-by-23:50 | not certified | 3 | 102.0 | pdrive mix caps A32 AD4 GD19 (stage 1 osc repair, t=102 s); lineage: archive 116 |
| P3 | `p3-rkD1-s1-mix21-k2-a32-ad4-g115-gd19-d0eb6a2b7f.circ.txt` | OK | 32/4/115/19 | T04 | known-by-23:50 | certified | 612 | 601.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt` | OK | 32/4/113/20 | T04 | known-by-23:50 | certified | 1011 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkG1-s1-mix21-k2-a32-ad4-g113-gd20-3a9cfe0c28.circ.txt` | OK | 32/4/113/20 | T04 | known-by-23:50 | certified | 1012 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkG1-s1-mix21-k2-a32-ad4-g113-gd21-5f4aa69922.circ.txt` | OK | 32/4/113/21 | T04 | known-by-23:50 | certified | 1012 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkG1-s1-mix21-k2-a32-ad4-g114-gd20-b872c819ec.circ.txt` | OK | 32/4/114/20 | T04 | known-by-23:50 | certified | 1012 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt` | OK | 32/4/114/19 | T04 | known-by-23:50 | certified | 1031 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkG1-s3-mix19-k1-a32-ad4-g115-gd19-606196db63.circ.txt` | OK | 32/4/115/19 | T04 | known-by-23:50 | certified | 1031 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkH1-s1-mix23-k1-a32-ad4-g112-gd22-b8095ec160.circ.txt` | OK | 32/4/112/22 | T04 | known-by-23:50 | certified | 1211 | None | pdrive mode from command.txt, repair_keep 1, kernel bfx-4dc199db (run Pareto set |
| P3 | `p3-rkH1-s2-mix21-k1-a32-ad4-g113-gd20-c7e62edf3e.circ.txt` | OK | 32/4/113/20 | T04 | known-by-23:50 | certified | 1221 | 362.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkH1-s2-mix21-k1-a32-ad4-g114-gd20-b127c5cdb3.circ.txt` | OK | 32/4/114/20 | T04 | known-by-23:50 | certified | 1221 | 362.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkH1-s2-mix21-k2-a32-ad4-g113-gd20-43a7823916.circ.txt` | OK | 32/4/113/20 | T04 | known-by-23:50 | certified | 1222 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkH1-s2-mix21-k2-a32-ad4-g113-gd21-d24fdfaf04.circ.txt` | OK | 32/4/113/21 | T04 | known-by-23:50 | certified | 1222 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkH1-s2-mix21-k2-a32-ad4-g114-gd20-e308e0d115.circ.txt` | OK | 32/4/114/20 | T04 | known-by-23:50 | certified | 1222 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkH1-s3-mix19-k1-a32-ad4-g114-gd19-b9c4889e69.circ.txt` | OK | 32/4/114/19 | T04 | known-by-23:50 | certified | 1231 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkH1-s3-mix19-k1-a32-ad4-g115-gd19-85f4fe7b83.circ.txt` | OK | 32/4/115/19 | T04 | known-by-23:50 | certified | 1231 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt` | OK | 32/4/115/18 | T04 | known-by-23:50 | certified | 1411 | 601.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkI1-s1-mix19-k2-a32-ad4-g114-gd19-6f7a899655.circ.txt` | OK | 32/4/114/19 | T04 | known-by-23:50 | certified | 1412 | 602.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkI1-s1-mix19-k2-a32-ad4-g115-gd19-78ab830b2a.circ.txt` | OK | 32/4/115/19 | T04 | known-by-23:50 | certified | 1412 | 602.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkI1-s2-trb19-k1-a32-ad4-g114-gd19-2f2b76004a.circ.txt` | OK | 32/4/114/19 | T04 | known-by-23:50 | certified | 1421 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode trb, caps A32 AD4 GD19, k |
| P3 | `p3-rkI1-s2-trb19-k1-a32-ad4-g115-gd19-8f7b7784fd.circ.txt` | OK | 32/4/115/19 | T04 | known-by-23:50 | certified | 1421 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode trb, caps A32 AD4 GD19, k |
| P3 | `p3-rkI1-s2-trb19-k2-a32-ad4-g114-gd19-3905bb10d8.circ.txt` | OK | 32/4/114/19 | T04 | known-by-23:50 | certified | 1422 | 601.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode trb, caps A32 AD4 GD19, k |
| P3 | `p3-rkI2-s1-mix20-k1-a32-ad4-g114-gd19-02a1811220.circ.txt` | OK | 32/4/114/19 | T04 | known-by-23:50 | certified | 1511 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD20, k |
| P3 | `p3-rkI2-s2-mix19-k1-a32-ad4-g114-gd19-4989701195.circ.txt` | OK | 32/4/114/19 | T04 | known-by-23:50 | certified | 1521 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkI2-s2-mix19-k2-a32-ad4-g114-gd19-4dabf1a701.circ.txt` | OK | 32/4/114/19 | T04 | known-by-23:50 | certified | 1522 | 601.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkI2-s2-mix19-k2-a32-ad4-g115-gd19-d4730050d6.circ.txt` | OK | 32/4/115/19 | T04 | known-by-23:50 | certified | 1522 | 601.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkI2-s2-mix19-k2-a32-ad4-g116-gd18-4c14207d12.circ.txt` | OK | 32/4/116/18 | T04 | known-by-23:50 | certified | 1522 | 601.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkJ1-s1-mix22-k1-a32-ad4-g113-gd21-aa6f3862e2.circ.txt` | OK | 32/4/113/21 | T04 | known-by-23:50 | certified | 1611 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD22, k |
| P3 | `p3-rkJ1-s1-mix22-k2-a32-ad4-g113-gd21-a2579b1fc8.circ.txt` | OK | 32/4/113/21 | T04 | known-by-23:50 | certified | 1612 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD22, k |
| P3 | `p3-rkJ1-s1-mix22-k2-a32-ad4-g114-gd20-f14c7f9c8b.circ.txt` | OK | 32/4/114/20 | T04 | known-by-23:50 | certified | 1612 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD22, k |
| P3 | `p3-rkJ1-s2-mix21-k1-a32-ad4-g113-gd20-ac258dcf0e.circ.txt` | OK | 32/4/113/20 | T04 | known-by-23:50 | certified | 1621 | 362.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkJ1-s2-mix21-k2-a32-ad4-g113-gd20-af64e9cefd.circ.txt` | OK | 32/4/113/20 | T04 | known-by-23:50 | certified | 1622 | 362.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkJ2-s1-mix19-k3-a32-ad4-g114-gd19-c2e143d017.circ.txt` | OK | 32/4/114/19 | T04 | known-by-23:50 | certified | 1713 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkJ2-s1-mix19-k3-a32-ad4-g116-gd19-6456fcc25a.circ.txt` | OK | 32/4/116/19 | T04 | known-by-23:50 | certified | 1713 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkK1-s1-mix18-k2-a32-ad4-g115-gd18-470095b8a5.circ.txt` | OK | 32/4/115/18 | T04 | known-by-23:50 | certified | 1812 | 601.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD18, k |
| P3 | `p3-rkK1-s1-mix18-k2-a32-ad4-g116-gd18-05ce2bcafc.circ.txt` | OK | 32/4/116/18 | T04 | known-by-23:50 | certified | 1812 | 601.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD18, k |
| P3 | `p3-rkK1-s1-mix18-k2-a32-ad4-g117-gd18-918956ebb8.circ.txt` | OK | 32/4/117/18 | T04 | known-by-23:50 | certified | 1812 | 601.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD18, k |
| P3 | `p3-rkK2-s1-mix18-k1-a32-ad4-g116-gd18-b4bdf1d774.circ.txt` | OK | 32/4/116/18 | T04 | known-by-23:50 | certified | 1911 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD18, k |
| P3 | `p3-rkK2-s1-mix18-k2-a32-ad4-g115-gd18-6e4a77b404.circ.txt` | OK | 32/4/115/18 | T04 | known-by-23:50 | certified | 1912 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD18, k |
| P3 | `p3-rkK2-s1-mix18-k2-a32-ad4-g116-gd18-821f00754b.circ.txt` | OK | 32/4/116/18 | T04 | known-by-23:50 | certified | 1912 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD18, k |
| P3 | `p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` | OK | 32/4/117/17 | T04 | known-by-23:50 | certified | 2212 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD17, k |
| P3 | `p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt` | OK | 32/4/120/16 | T04 | known-by-23:50 | certified | 2222 | None | pdrive mode from command.txt, repair_keep 1, kernel bfx-4dc199db (run Pareto set |
| P3 | `p3-rkN2-s1-mix19-k1-a32-ad4-g114-gd19-74db6afcdf.circ.txt` | OK | 32/4/114/19 | T04 | known-by-23:50 | certified | 2311 | 900.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkN2-s1-mix19-k1-a32-ad4-g115-gd19-5c6820258d.circ.txt` | OK | 32/4/115/19 | T04 | known-by-23:50 | certified | 2311 | 900.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkN2-s1-mix19-k2-a32-ad4-g114-gd19-152d87bee9.circ.txt` | OK | 32/4/114/19 | T04 | known-by-23:50 | certified | 2312 | 900.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkN2-s1-mix19-k3-a32-ad4-g114-gd19-9402c8bbdb.circ.txt` | OK | 32/4/114/19 | T04 | known-by-23:50 | certified | 2313 | 900.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkN2-s1-mix19-k3-a32-ad4-g116-gd19-17cd03da14.circ.txt` | OK | 32/4/116/19 | T04 | known-by-23:50 | certified | 2313 | 900.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P4 | `p4-conj236-a32-ad7-g104-gd28.circ.txt` | OK | 32/7/104/28 | T05 | known-by-23:50 | certified | 236 | 602.0 | GF(2^8) conjugate lam 236 k 0 of NIST 103 (P3 mkconj.py: BP top + trb), then pdr |
| P4 | `p4-deep236-a32-ad7-g104-gd27.circ.txt` | OK | 32/7/104/27 | T05 | known-by-23:50 | certified | 2363 | <= 600 (saved from the running stage pareto/ at 18:49 UTC; lineage total ~2,400 s) | lineage: conjugate lam 236 of NIST 103 (mkconj) -> pdrive gate cap32 -> trb cap3 |
| P5 | `p5-ad4rep-111-c24-s1-a32-ad4-g112-gd22-db1394c64b.circ.txt` | OK | 32/4/112/22 | T05 | known-by-23:50 | certified | 701 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-111-c24-s1-a32-ad4-g112-gd23-f419cd7d01.circ.txt` | OK | 32/4/112/23 | T05 | known-by-23:50 | certified | 701 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-111-c24-s1-a32-ad4-g112-gd24-92aa29b493.circ.txt` | OK | 32/4/112/24 | T05 | known-by-23:50 | certified | 701 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-111-c24-s2-a32-ad4-g112-gd22-e9aef8c1c8.circ.txt` | OK | 32/4/112/22 | T05 | known-by-23:50 | certified | 702 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-111-c24-s2-a32-ad4-g112-gd23-af556a21af.circ.txt` | OK | 32/4/112/23 | T05 | known-by-23:50 | certified | 702 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-111-c24-s3-a32-ad4-g112-gd23-e40775065a.circ.txt` | OK | 32/4/112/23 | T05 | known-by-23:50 | certified | 703 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-111-c24-s3-a32-ad4-g112-gd24-90adf25722.circ.txt` | OK | 32/4/112/24 | T05 | known-by-23:50 | certified | 703 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-111-c24-s4-a32-ad4-g113-gd21-92dd4b99a3.circ.txt` | OK | 32/4/113/21 | T05 | known-by-23:50 | certified | 704 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-111-c24-s4-a32-ad4-g113-gd22-019c3ed87b.circ.txt` | OK | 32/4/113/22 | T05 | known-by-23:50 | certified | 704 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-111-c24-s5-a32-ad4-g112-gd22-2af2254f9b.circ.txt` | OK | 32/4/112/22 | T05 | known-by-23:50 | certified | 705 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-112-g32-s1-a32-ad4-g111-gd26-74604ea2c6.circ.txt` | OK | 32/4/111/26 | T05 | known-by-23:50 | certified | 801 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad4rep-112-g32-s1-a32-ad4-g111-gd27-e32dbde99e.circ.txt` | OK | 32/4/111/27 | T05 | known-by-23:50 | certified | 801 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad4rep-112-g32-s2-a32-ad4-g111-gd26-67fd53ccb7.circ.txt` | OK | 32/4/111/26 | T05 | known-by-23:50 | certified | 802 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad4rep-112-g32-s2-a32-ad4-g111-gd30-cb4d8cf4e2.circ.txt` | OK | 32/4/111/30 | T05 | known-by-23:50 | certified | 802 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad4rep-112-g32-s3-a32-ad4-g111-gd26-a4d6a2dde1.circ.txt` | OK | 32/4/111/26 | T05 | known-by-23:50 | certified | 803 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad4rep-112-g32-s4-a32-ad4-g111-gd26-9b6a27c5d9.circ.txt` | OK | 32/4/111/26 | T05 | known-by-23:50 | certified | 804 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad4rep-112-g32-s4-a32-ad4-g111-gd28-27b136ee8c.circ.txt` | OK | 32/4/111/28 | T05 | known-by-23:50 | certified | 804 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad4rep-112-g32-s5-a32-ad4-g111-gd26-60baa8d4ac.circ.txt` | OK | 32/4/111/26 | T05 | known-by-23:50 | certified | 805 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad5g-106-g30-s1-a32-ad5-g105-gd28-2996504ded.circ.txt` | OK | 32/5/105/28 | T05 | reproduced | certified | 901 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad5g-106-g30-s1-a32-ad5-g106-gd26-43cb5a4711.circ.txt` | OK | 32/5/106/26 | T05 | reproduced | certified | 901 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad5g-106-g30-s2-a32-ad5-g105-gd29-d57da9ed36.circ.txt` | OK | 32/5/105/29 | T05 | known-by-23:50 | certified | 902 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad5g-106-g30-s3-a32-ad5-g105-gd28-19c1107b17.circ.txt` | OK | 32/5/105/28 | T05 | reproduced | certified | 903 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad5g-106-g30-s4-a32-ad5-g105-gd28-192a683986.circ.txt` | OK | 32/5/105/28 | T05 | reproduced | certified | 904 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad5rep-a104-c28-s1-a32-ad5-g106-gd26-f8ef5abee4.circ.txt` | OK | 32/5/106/26 | T05 | reproduced | unknown | 601 | 400 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad5rep-a104-c28-s1-a32-ad5-g106-gd27-b303a86653.circ.txt` | OK | 32/5/106/27 | T05 | reproduced | unknown | 601 | 400 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad5rep-a104-c28-s1-a32-ad5-g108-gd25-fc27686f21.circ.txt` | OK | 32/5/108/25 | T05 | known-by-23:50 | unknown | 601 | 400 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad5rep-n104-c29-s1-a32-ad5-g106-gd26-8fedacd93f.circ.txt` | OK | 32/5/106/26 | T05 | reproduced | certified | 501 | 400 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp-ad5-104-29-cj188k0-g36-a32-ad5-g108-gd25-c10c60fc9a.circ.txt` | OK | 32/5/108/25 | T05 | known-by-23:50 | unknown | 1 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp-ad5-104-29-cj188k0-g36-a32-ad5-g108-gd26-17187178f9.circ.txt` | OK | 32/5/108/26 | T05 | known-by-23:50 | unknown | 1 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp-ad5-104-29-cj188k0-g36-a32-ad5-g108-gd27-47c7848099.circ.txt` | OK | 32/5/108/27 | T05 | reproduced | unknown | 1 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp-ad5-104-29-cj9k4-g36-a32-ad5-g108-gd23-a18ff2ca94.circ.txt` | OK | 32/5/108/23 | T05 | reproduced | unknown | 1 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp-ad5-104-29-cj9k4-g36-a32-ad5-g108-gd25-2c4cedb698.circ.txt` | OK | 32/5/108/25 | T05 | known-by-23:50 | unknown | 1 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp-ad5-104-29-cj9k4-m30-a32-ad5-g106-gd24-087ba23f48.circ.txt` | OK | 32/5/106/24 | T05 | reproduced | unknown | 2 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp-ad5-104-29-cj9k4-m30-a32-ad5-g106-gd26-092af29b76.circ.txt` | OK | 32/5/106/26 | T05 | reproduced | unknown | 2 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp-ad5-104-29-cj9k4-m30-a32-ad5-g107-gd26-a7eb465962.circ.txt` | OK | 32/5/107/26 | T05 | known-by-23:50 | unknown | 2 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp-ad5-104-29-cj9k4-m30-a32-ad5-g107-gd27-9bbc42a682.circ.txt` | OK | 32/5/107/27 | T05 | known-by-23:50 | unknown | 2 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp4-ad4-111-25-cert-id-m26-a32-ad4-g112-gd24-6e09c4e4d6.circ.txt` | OK | 32/4/112/24 | T05 | known-by-23:50 | certified | 2 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp4-ad4-111-25-cert-l2k0-g30-a32-ad4-g116-gd24-bc59f0cf8f.circ.txt` | OK | 32/4/116/24 | T05 | known-by-23:50 | certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-111-25-cert-l2k0-g30-a32-ad4-g116-gd25-1d33ad63c5.circ.txt` | OK | 32/4/116/25 | T05 | reproduced | certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-111-25-cert-l2k0-g30-a32-ad4-g116-gd26-31f4b1915f.circ.txt` | OK | 32/4/116/26 | T05 | known-by-23:50 | certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-113-20-p3-id-g30-a32-ad4-g112-gd24-1b0490fa03.circ.txt` | OK | 32/4/112/24 | T05 | known-by-23:50 | not certified | 1 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-113-20-p3-id-g30-a32-ad4-g112-gd25-d2e2ab17a6.circ.txt` | OK | 32/4/112/25 | T05 | known-by-23:50 | not certified | 1 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-113-20-p3-id-m26-a32-ad4-g113-gd23-05a04c3e3d.circ.txt` | OK | 32/4/113/23 | T05 | known-by-23:50 | not certified | 2 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp4-ad4-113-20-p3-l167k1-g30-a32-ad4-g116-gd27-d1003c3369.circ.txt` | OK | 32/4/116/27 | T05 | reproduced | not certified | 1 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-113-20-p3-l167k1-g30-a32-ad4-g117-gd24-1a6caf356f.circ.txt` | OK | 32/4/117/24 | T05 | known-by-23:50 | not certified | 1 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-113-20-p3-l2k0-g30-a32-ad4-g115-gd26-d5cd3afa3c.circ.txt` | OK | 32/4/115/26 | T05 | reproduced | not certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-113-20-p3-l2k0-g30-a32-ad4-g116-gd22-d198dea982.circ.txt` | OK | 32/4/116/22 | T05 | known-by-23:50 | not certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-113-20-p3-l2k0-g30-a32-ad4-g117-gd24-32e79e55c6.circ.txt` | OK | 32/4/117/24 | T05 | known-by-23:50 | not certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-113-20-p3-l2k0-m26-a32-ad4-g115-gd24-12d6ebc4b1.circ.txt` | OK | 32/4/115/24 | T05 | reproduced | not certified | 2 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp4-nist117-id-g30-a32-ad4-g115-gd26-39ad486bf9.circ.txt` | OK | 32/4/115/26 | T05 | reproduced | certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-nist117-id-g30-a32-ad4-g116-gd26-89efb38a5b.circ.txt` | OK | 32/4/116/26 | T05 | known-by-23:50 | certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-nist117-id-m26-a32-ad4-g119-gd23-ccd1334960.circ.txt` | OK | 32/4/119/23 | T05 | known-by-23:50 | certified | 2 | 404 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp4-nist117-l188k0-g30-a32-ad4-g115-gd23-308b85bc8d.circ.txt` | OK | 32/4/115/23 | T05 | reproduced | certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-nist117-l188k0-g30-a32-ad4-g115-gd27-e3ccddeaf0.circ.txt` | OK | 32/4/115/27 | T05 | reproduced | certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-nist117-l188k0-m26-a32-ad4-g113-gd23-ee6e6b7da3.circ.txt` | OK | 32/4/113/23 | T05 | known-by-23:50 | certified | 2 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp4-nist117-l188k0-m26-a32-ad4-g115-gd23-ae2d82fe1b.circ.txt` | OK | 32/4/115/23 | T05 | reproduced | certified | 2 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp4-nist117-l9k4-g30-a32-ad4-g118-gd23-ab456275fa.circ.txt` | OK | 32/4/118/23 | T05 | known-by-23:50 | certified | 1 | 304 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-nist117-l9k4-g30-a32-ad4-g118-gd27-3b6c8f5b3b.circ.txt` | OK | 32/4/118/27 | T05 | reproduced | certified | 1 | 304 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-ad4-113-20-p3-r1-gate30-a32-ad4-g112-gd24-23cedca220.circ.txt` | OK | 32/4/112/24 | T05 | known-by-23:50 | not certified | 11 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-ad4-113-20-p3-r2-gate30-a32-ad4-g111-gd25-8a6a18f6c7.circ.txt` | OK | 32/4/111/25 | T05 | known-by-23:50 | not certified | 13 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt` | OK | 32/4/111/25 | T05 | known-by-23:50 | certified | 91 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-cert112c-r1-gate26-a32-ad4-g111-gd26-99fb8b899e.circ.txt` | OK | 32/4/111/26 | T05 | known-by-23:50 | certified | 51 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-cert112c-r1-mix22-a32-ad4-g112-gd22-125223cf3b.circ.txt` | OK | 32/4/112/22 | T05 | known-by-23:50 | certified | 52 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-cert112c-r2-gate26-a32-ad4-g112-gd22-c9585d7a3f.circ.txt` | OK | 32/4/112/22 | T05 | known-by-23:50 | certified | 53 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-cert112c-r2-mix22-a32-ad4-g113-gd20-80065eed92.circ.txt` | OK | 32/4/113/20 | T05 | known-by-23:50 | certified | 54 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-cert112c-r3-mix22-a32-ad4-g113-gd21-7e4ed9b6a3.circ.txt` | OK | 32/4/113/21 | T05 | known-by-23:50 | certified | 56 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-cert113-r1-gate30-a32-ad4-g112-gd25-68cddda33a.circ.txt` | OK | 32/4/112/25 | T05 | known-by-23:50 | certified | 31 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-cert113-r1-mix26-a32-ad4-g112-gd22-6f3b39a3e3.circ.txt` | OK | 32/4/112/22 | T05 | known-by-23:50 | certified | 32 | 400 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-cert113-r1-mix26-a32-ad4-g112-gd24-dcc732f7d3.circ.txt` | OK | 32/4/112/24 | T05 | known-by-23:50 | certified | 32 | 400 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-cert113-r2-gate30-a32-ad4-g111-gd26-162638ccbf.circ.txt` | OK | 32/4/111/26 | T05 | known-by-23:50 | certified | 33 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-cert113-r2-gate30-a32-ad4-g112-gd22-f67c50c277.circ.txt` | OK | 32/4/112/22 | T05 | known-by-23:50 | certified | 33 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-cert113-r2-mix26-a32-ad4-g111-gd26-05cc8d2448.circ.txt` | OK | 32/4/111/26 | T05 | known-by-23:50 | certified | 34 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-cert113-r2-mix26-a32-ad4-g112-gd23-3dc99fae77.circ.txt` | OK | 32/4/112/23 | T05 | known-by-23:50 | certified | 34 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-cert113-r3-gate30-a32-ad4-g111-gd25-56b90bc378.circ.txt` | OK | 32/4/111/25 | T05 | known-by-23:50 | certified | 35 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-cert113-r3-mix26-a32-ad4-g113-gd23-55afdd7ee4.circ.txt` | OK | 32/4/113/23 | T05 | known-by-23:50 | certified | 36 | 400 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-certB-r1-gate30-a32-ad4-g113-gd25-de634303a1.circ.txt` | OK | 32/4/113/25 | T05 | known-by-23:50 | certified | 201 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-certB-r1-gate30-a32-ad4-g114-gd24-2f736d2878.circ.txt` | OK | 32/4/114/24 | T05 | known-by-23:50 | certified | 201 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-certB-r1-gate30-a32-ad4-g114-gd25-2105bd71e5.circ.txt` | OK | 32/4/114/25 | T05 | known-by-23:50 | certified | 201 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-certB-r1-mix26-a32-ad4-g112-gd23-dd155cc47a.circ.txt` | OK | 32/4/112/23 | T05 | known-by-23:50 | certified | 202 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-certB-r2-gate30-a32-ad4-g111-gd25-5b118266a0.circ.txt` | OK | 32/4/111/25 | T05 | known-by-23:50 | certified | 203 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-certB-r3-gate30-a32-ad4-g111-gd25-c682c9518b.circ.txt` | OK | 32/4/111/25 | T05 | known-by-23:50 | certified | 205 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-certC-r1-mix23-a32-ad4-g112-gd22-40eabf538f.circ.txt` | OK | 32/4/112/22 | T05 | known-by-23:50 | certified | 302 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-certC-r2-gate25-a32-ad4-g112-gd22-510475e940.circ.txt` | OK | 32/4/112/22 | T05 | known-by-23:50 | certified | 303 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-n104ad5-r1-gate32-a32-ad5-g104-gd30-377f53491e.circ.txt` | OK | 32/5/104/30 | T05 | reproduced | certified | 71 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-n104ad5-r1-gate32-a32-ad5-g104-gd30-4d499b80a0.circ.txt` | OK | 32/5/104/30 | T05 | reproduced | certified | 71 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-n104gd-r1-mix28-a32-ad5-g106-gd27-579c2291f2.circ.txt` | OK | 32/5/106/27 | T05 | reproduced | certified | 402 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-n104gd-r1-mix28-a32-ad5-g107-gd25-6af94a5574.circ.txt` | OK | 32/5/107/25 | T05 | known-by-23:50 | certified | 402 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P6 | `aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt` | OK | 35/3/137/28 | T07 | known-by-23:50 | certified | 1512 | 200.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt` | OK | 35/3/138/24 | T07 | known-by-23:50 | certified | 20378 | 240.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt` | OK | 35/3/139/23 | T07 | known-by-23:50 | certified | 3011 | 200.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g139-gd25-107a7c3b5078.circ.txt` | OK | 35/3/139/25 | T07 | known-by-23:50 | certified | 776 | 200.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g140-gd22-ecd3572a7c9b.circ.txt` | OK | 35/3/140/22 | T07 | known-by-23:50 | certified | 799 | 200.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt` | OK | 35/3/168/13 | T08 | known-by-23:50 | certified | 473407 | 240.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g169-gd13-e0c19be5de66.circ.txt` | OK | 35/3/169/13 | T08 | known-by-23:50 | certified | 623400 | 240.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g170-gd13-b418123e66e8.circ.txt` | OK | 35/3/170/13 | T08 | known-by-23:50 | certified | 2303 | 150.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g171-gd13-462cb948a761.circ.txt` | OK | 35/3/171/13 | T08 | known-by-23:50 | certified | 508711 | 240.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g172-gd13-ad319b23b367.circ.txt` | OK | 35/3/172/13 | T08 | known-by-23:50 | certified | 77 | 56.0 | gate kernel hub.ops._kernel (kern.py) caps A35 AD3 GD13, cost,gd, 120 s, from ou |
| P6 | `aes-sbox-a35-ad3-g175-gd13-9266803dcdb9.circ.txt` | OK | 35/3/175/13 | T08 | known-by-23:50 | certified | pullrun 131, kernel seed 733133 | 300.0 | P6 depth pull: parent 35/3/162/14 (best-1400) -> level-3 class re-basing (botbas |
| P6 | `aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt` | OK | 35/3/181/12 | T08 | known-by-23:50 | certified | 397181 | 240.0 | P6 depth pull: 177@13 -> GF(4) one-point coordinate move (T3 gf4build keep2, poi |
| P6 | `aes-sbox-a35-ad3-g187-gd12-b9da0aa0d74b.circ.txt` | OK | 35/3/187/12 | T08 | known-by-23:50 | certified | 228749 | 240.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g188-gd12-6fec90a391dc.circ.txt` | OK | 35/3/188/12 | T08 | known-by-23:50 | certified | 91543 | 240.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g189-gd12-cb8301fe7b08.circ.txt` | OK | 35/3/189/12 | T08 | known-by-23:50 | certified | 91543 | 240.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g200-gd12-257dddf4b764.circ.txt` | OK | 35/3/200/12 | T08 | known-by-23:50 | certified | 21 | 105.0 | P6 rebase+fresh build (246@12) then gate kernel hub.ops._kernel via kern.py, cap |
| P6 | `aes-sbox-a35-ad3-g246-gd12-b9fc15540ac5.circ.txt` | OK | 35/3/246/12 | T08 | known-by-23:50 | certified | 1 | 3.0 | P6 rebase: level-3 class re-basing (botbasis.py, max output Kraft 1.0 at cap 12) |
| P7 | `p7-t09-a39-ad4-g137-gd12-pol-LE-aes-nist-hub-pw3-s9004.circ.txt` | OK | 39/4/137/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 9004 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a39-ad4-g137-gd12-pol-LE-aes-sbox-a45-pw3-s9002.circ.txt` | OK | 39/4/137/12 | T09 | known-by-23:50 | certified | 9002 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a39-ad4-g138-gd12-build-LC-aes-sbox-a45-pw0-s7001-r2.circ.txt` | OK | 39/4/138/12 | T09 | known-by-23:50 | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py --refine2 (pairwise joint re-decomposition) fr |
| P7 | `p7-t09-a39-ad4-g138-gd12-build-LC-aes-sbox-a45-pw0-s7001.circ.txt` | OK | 39/4/138/12 | T09 | known-by-23:50 | certified | 7001 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a39-ad4-g138-gd12-build-LE-aes-sbox-a45-pw3-s9002.circ.txt` | OK | 39/4/138/12 | T09 | known-by-23:50 | certified | 9002 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a39-ad4-g138-gd12-pol-LA-aes-nist-hub-pw3-s1010.circ.txt` | OK | 39/4/138/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 1010 | 301.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a39-ad4-g138-gd12-pol-LC-aes-sbox-a45-pw3-s7008.circ.txt` | OK | 39/4/138/12 | T09 | known-by-23:50 | certified | 7008 | 301.8 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a39-ad4-g139-gd12-build-LC-aes-sbox-a45-pw3-s7008.circ.txt` | OK | 39/4/139/12 | T09 | known-by-23:50 | certified | 7008 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a39-ad4-g139-gd12-polgate-a39-minp48-pw4-s1.circ.txt` | OK | 39/4/139/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 5 | 501.8 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a39-ad4-g140-gd12-build-LE-aes-nist-hub-pw3-s9004.circ.txt` | OK | 39/4/140/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 9004 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a39-ad4-g140-gd12-pol-LA-aes-nist-hub-pw3-s1004.circ.txt` | OK | 39/4/140/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 1004 | 301.0 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a39-ad4-g140-gd12-pol-LE-aes-sbox-a45-pw0-s9007.circ.txt` | OK | 39/4/140/12 | T09 | known-by-23:50 | certified | 9007 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a39-ad4-g141-gd12-build-LA-aes-nist-hub-pw3-s1010.circ.txt` | OK | 39/4/141/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 1010 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a39-ad4-g141-gd12-build-minp48-pw4-s1.circ.txt` | OK | 39/4/141/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a39-ad4-g141-gd12-polgate-a39-minp48-pw4-s2.circ.txt` | OK | 39/4/141/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 5 | 501.9 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a39-ad4-g142-gd12-build-LC-aes-nist-hub-pw3-s7010.circ.txt` | OK | 39/4/142/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 7010 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a39-ad4-g142-gd12-build-LE-aes-sbox-a45-pw0-s9007.circ.txt` | OK | 39/4/142/12 | T09 | known-by-23:50 | certified | 9007 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a39-ad4-g142-gd12-build-minp48-pw4-s2.circ.txt` | OK | 39/4/142/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a39-ad4-g142-gd12-pol-LE-aes-nist-hub-pw3-s9022.circ.txt` | OK | 39/4/142/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 9022 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a39-ad4-g143-gd12-build-LE-aes-nist-hub-pw3-s9022.circ.txt` | OK | 39/4/143/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 9022 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a39-ad4-g143-gd12-build-minp48-pw2-s1.circ.txt` | OK | 39/4/143/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a39-ad4-g143-gd12-build-minp48-pw4-s3.circ.txt` | OK | 39/4/143/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3 | 0.0 | {'engine': 'strategies/P7/bopt.py --pw 4 + bbuild.py', 'plan': '/home/joebachir2 |
| P7 | `p7-t09-a39-ad4-g143-gd12-pol-LE-aes-nist-hub-pw3-s9016.circ.txt` | OK | 39/4/143/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 9016 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a39-ad4-g144-gd12-build-LA-aes-nist-hub-pw3-s1004.circ.txt` | OK | 39/4/144/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 1004 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a39-ad4-g144-gd12-build-LE-aes-nist-hub-pw3-s9016.circ.txt` | OK | 39/4/144/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 9016 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g137-gd12-pol-LD-aes-nist-hub-pw3-s3028.circ.txt` | OK | 40/4/137/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3028 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a40-ad4-g138-gd12-build-LD-p7-t09-a42-a-pw0-s3023.circ.txt` | OK | 40/4/138/12 | T09 | known-by-23:50 | certified | 3023 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g139-gd12-build-LD-aes-sbox-a45-pw3-s3002.circ.txt` | OK | 40/4/139/12 | T09 | known-by-23:50 | certified | 3002 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g139-gd12-build-minp-pw3-s3.circ.txt` | OK | 40/4/139/12 | T09 | known-by-23:50 | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a40-ad4-g139-gd12-build-t45-s60-ref.circ.txt` | OK | 40/4/139/12 | T09 | known-by-23:50 | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a40-ad4-g139-gd12-pol-LC-aes-nist-hub-pw3-s7004.circ.txt` | OK | 40/4/139/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 7004 | 300.6 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a40-ad4-g139-gd12-pol-LD-aes-nist-hub-pw0-s3021.circ.txt` | OK | 40/4/139/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3021 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a40-ad4-g140-gd12-pol-LD-aes-nist-hub-pw3-s3022.circ.txt` | OK | 40/4/140/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3022 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a40-ad4-g140-gd12-pol-LD-p7-t09-a42-a-pw3-s3012.circ.txt` | OK | 40/4/140/12 | T09 | known-by-23:50 | certified | 3012 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a40-ad4-g140-gd12-pol-LD-p7-t09-a42-a-pw3-s3018.circ.txt` | OK | 40/4/140/12 | T09 | known-by-23:50 | certified | 3018 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a40-ad4-g140-gd12-pol-LE-aes-nist-hub-pw0-s9015.circ.txt` | OK | 40/4/140/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 9015 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a40-ad4-g141-gd12-build-LC-aes-nist-hub-pw3-s7004.circ.txt` | OK | 40/4/141/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 7004 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g141-gd12-build-LD-aes-nist-hub-pw0-s3021.circ.txt` | OK | 40/4/141/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3021 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g141-gd12-build-LD-p7-t09-a42-a-pw3-s3012.circ.txt` | OK | 40/4/141/12 | T09 | known-by-23:50 | certified | 3012 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g141-gd12-build-LD-p7-t09-a42-a-pw3-s3018.circ.txt` | OK | 40/4/141/12 | T09 | known-by-23:50 | certified | 3018 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g141-gd12-build-minp-pw10-s3.circ.txt` | OK | 40/4/141/12 | T09 | known-by-23:50 | certified | 3 | 0.0 | {'engine': 'strategies/P7/bopt.py --pw 10 + bbuild.py', 'plan': '/home/joebachir |
| P7 | `p7-t09-a40-ad4-g141-gd12-pol-LD-aes-nist-hub-pw3-s3004.circ.txt` | OK | 40/4/141/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3004 | 300.7 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a40-ad4-g142-gd12-build-LD-aes-nist-hub-pw3-s3004.circ.txt` | OK | 40/4/142/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3004 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g142-gd12-build-LE-aes-nist-hub-pw0-s9015.circ.txt` | OK | 40/4/142/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 9015 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g142-gd12-pol-LD-aes-nist-hub-pw3-s3010.circ.txt` | OK | 40/4/142/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3010 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a40-ad4-g143-gd12-build-LD-aes-nist-hub-pw3-s3022.circ.txt` | OK | 40/4/143/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3022 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g143-gd12-build-LD-aes-nist-hub-pw3-s3028.circ.txt` | OK | 40/4/143/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3028 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g144-gd12-build-LD-aes-nist-hub-pw3-s3010.circ.txt` | OK | 40/4/144/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3010 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g144-gd12-build-minp48-pw2-s3.circ.txt` | OK | 40/4/144/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3 | 0.0 | {'engine': 'strategies/P7/bopt.py --pw 2 + bbuild.py', 'plan': '/home/joebachir2 |
| P7 | `p7-t09-a41-ad4-g136-gd12-pol-LE-p7-t09-a42-a-pw0-s9005.circ.txt` | OK | 41/4/136/12 | T09 | known-by-23:50 | certified | 9005 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g137-gd12-build-LE-p7-t09-a42-a-pw0-s9005.circ.txt` | OK | 41/4/137/12 | T09 | known-by-23:50 | certified | 9005 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g137-gd12-pol-LA-p7-t09-a42-a-pw0-s1011.circ.txt` | OK | 41/4/137/12 | T09 | known-by-23:50 | certified | 1011 | 301.3 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g137-gd12-pol-LC-aes-sbox-a45-pw3-s7002.circ.txt` | OK | 41/4/137/12 | T09 | known-by-23:50 | certified | 7002 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g137-gd12-pol-LD-p7-t09-a42-a-pw3-s3024.circ.txt` | OK | 41/4/137/12 | T09 | known-by-23:50 | certified | 3024 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g138-gd12-build-LC-aes-sbox-a45-pw3-s7002.circ.txt` | OK | 41/4/138/12 | T09 | known-by-23:50 | certified | 7002 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g138-gd12-build-minp-pw3-s1.circ.txt` | OK | 41/4/138/12 | T09 | known-by-23:50 | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a41-ad4-g138-gd12-build-minp-pw3-s2.circ.txt` | OK | 41/4/138/12 | T09 | known-by-23:50 | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a41-ad4-g138-gd12-pol-LA-p7-t09-a42-a-pw0-s1005.circ.txt` | OK | 41/4/138/12 | T09 | known-by-23:50 | certified | 1005 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g138-gd12-pol-LD-aes-sbox-a45-pw0-s3019.circ.txt` | OK | 41/4/138/12 | T09 | known-by-23:50 | certified | 3019 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g138-gd12-pol-LD-aes-sbox-a45-pw3-s3014.circ.txt` | OK | 41/4/138/12 | T09 | known-by-23:50 | certified | 3014 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g138-gd12-pol-LE-aes-sbox-a45-pw0-s9013.circ.txt` | OK | 41/4/138/12 | T09 | known-by-23:50 | certified | 9013 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g139-gd12-build-LA-p7-t09-a42-a-pw0-s1005.circ.txt` | OK | 41/4/139/12 | T09 | known-by-23:50 | certified | 1005 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g139-gd12-build-LC-p7-t09-a42-a-pw3-s7006.circ.txt` | OK | 41/4/139/12 | T09 | known-by-23:50 | certified | 7006 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g139-gd12-build-LD-aes-sbox-a45-pw3-s3014.circ.txt` | OK | 41/4/139/12 | T09 | known-by-23:50 | certified | 3014 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g139-gd12-build-LD-p7-t09-a42-a-pw3-s3024.circ.txt` | OK | 41/4/139/12 | T09 | known-by-23:50 | certified | 3024 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g139-gd12-build-LE-aes-sbox-a45-pw0-s9013.circ.txt` | OK | 41/4/139/12 | T09 | known-by-23:50 | certified | 9013 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g139-gd12-pol-LA-p7-t09-a42-a-pw3-s1006.circ.txt` | OK | 41/4/139/12 | T09 | known-by-23:50 | certified | 1006 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g139-gd12-pol-LD-aes-nist-hub-pw0-s3003.circ.txt` | OK | 41/4/139/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3003 | 301.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g139-gd12-pol-LD-aes-nist-hub-pw0-s3009.circ.txt` | OK | 41/4/139/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3009 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g139-gd12-pol-LD-aes-sbox-a45-pw3-s3026.circ.txt` | OK | 41/4/139/12 | T09 | known-by-23:50 | certified | 3026 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g140-gd12-build-LA-p7-t09-a42-a-pw0-s1011.circ.txt` | OK | 41/4/140/12 | T09 | known-by-23:50 | certified | 1011 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g140-gd12-build-LD-aes-nist-hub-pw0-s3009.circ.txt` | OK | 41/4/140/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3009 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g140-gd12-build-LD-p7-t09-a42-a-pw0-s3005.circ.txt` | OK | 41/4/140/12 | T09 | known-by-23:50 | certified | 3005 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g140-gd12-build-LD-p7-t09-a42-a-pw0-s3017.circ.txt` | OK | 41/4/140/12 | T09 | known-by-23:50 | certified | 3017 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g140-gd12-pol-LD-p7-t09-a42-a-pw3-s3030.circ.txt` | OK | 41/4/140/12 | T09 | known-by-23:50 | certified | 3030 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g141-gd12-build-LA-p7-t09-a42-a-pw3-s1006.circ.txt` | OK | 41/4/141/12 | T09 | known-by-23:50 | certified | 1006 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g141-gd12-build-LD-aes-nist-hub-pw0-s3003.circ.txt` | OK | 41/4/141/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3003 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g141-gd12-build-LD-aes-sbox-a45-pw0-s3019.circ.txt` | OK | 41/4/141/12 | T09 | known-by-23:50 | certified | 3019 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g141-gd12-build-LD-aes-sbox-a45-pw3-s3026.circ.txt` | OK | 41/4/141/12 | T09 | known-by-23:50 | certified | 3026 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g141-gd12-build-LD-p7-t09-a42-a-pw3-s3030.circ.txt` | OK | 41/4/141/12 | T09 | known-by-23:50 | certified | 3030 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g141-gd12-pol-LA-aes-nist-hub-pw0-s1003.circ.txt` | OK | 41/4/141/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 1003 | 300.9 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g141-gd12-pol-LA-aes-nist-hub-pw0-s1009.circ.txt` | OK | 41/4/141/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 1009 | 301.8 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g141-gd12-pol-LA-aes-sbox-a45-pw3-s1002.circ.txt` | OK | 41/4/141/12 | T09 | known-by-23:50 | certified | 1002 | 302.6 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g141-gd12-pol-LC-aes-nist-hub-pw0-s7009.circ.txt` | OK | 41/4/141/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 7009 | 300.7 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g142-gd12-build-LE-p7-t09-a42-a-pw3-s9012.circ.txt` | OK | 41/4/142/12 | T09 | known-by-23:50 | certified | 9012 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g142-gd12-pol-LE-p7-t09-a42-a-pw3-s9006.circ.txt` | OK | 41/4/142/12 | T09 | known-by-23:50 | certified | 9006 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g143-gd12-build-LA-aes-sbox-a45-pw3-s1002.circ.txt` | OK | 41/4/143/12 | T09 | known-by-23:50 | certified | 1002 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g143-gd12-build-LA-aes-sbox-a45-pw3-s1008.circ.txt` | OK | 41/4/143/12 | T09 | known-by-23:50 | certified | 1008 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g143-gd12-build-LC-aes-nist-hub-pw0-s7009.circ.txt` | OK | 41/4/143/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 7009 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g143-gd12-build-LE-aes-sbox-a45-pw3-s9020.circ.txt` | OK | 41/4/143/12 | T09 | known-by-23:50 | certified | 9020 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g143-gd12-pol-LE-aes-nist-hub-pw3-s9010.circ.txt` | OK | 41/4/143/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 9010 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g144-gd12-build-LA-aes-nist-hub-pw0-s1003.circ.txt` | OK | 41/4/144/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 1003 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g144-gd12-build-LE-aes-nist-hub-pw3-s9010.circ.txt` | OK | 41/4/144/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 9010 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g144-gd12-build-LE-p7-t09-a42-a-pw3-s9006.circ.txt` | OK | 41/4/144/12 | T09 | known-by-23:50 | certified | 9006 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g144-gd12-build-minp48-pw2-s2.circ.txt` | OK | 41/4/144/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 2 | 0.0 | {'engine': 'strategies/P7/bopt.py --pw 2 + bbuild.py', 'plan': '/home/joebachir2 |
| P7 | `p7-t09-a41-ad4-g144-gd12-pol-LD-aes-nist-hub-pw3-s3016.circ.txt` | OK | 41/4/144/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3016 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g145-gd12-build-LA-aes-nist-hub-pw0-s1009.circ.txt` | OK | 41/4/145/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 1009 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g145-gd12-build-LD-aes-nist-hub-pw3-s3016.circ.txt` | OK | 41/4/145/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3016 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g145-gd12-build-LE-p7-t09-a42-a-pw3-s9018.circ.txt` | OK | 41/4/145/12 | T09 | known-by-23:50 | certified | 9018 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g145-gd12-build-minp-pw10-s1.circ.txt` | OK | 41/4/145/12 | T09 | known-by-23:50 | certified | 1 | 0.0 | {'engine': 'strategies/P7/bopt.py --pw 10 + bbuild.py', 'plan': '/home/joebachir |
| P7 | `p7-t09-a41-ad4-g145-gd12-pol-LD-aes-nist-hub-pw0-s3015.circ.txt` | OK | 41/4/145/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3015 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g145-gd12-pol-LE-aes-nist-hub-pw0-s9021.circ.txt` | OK | 41/4/145/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 9021 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g146-gd12-build-minp-pw10-s2.circ.txt` | OK | 41/4/146/12 | T09 | known-by-23:50 | certified | 2 | 0.0 | {'engine': 'strategies/P7/bopt.py --pw 10 + bbuild.py', 'plan': '/home/joebachir |
| P7 | `p7-t09-a41-ad4-g147-gd12-build-LD-aes-nist-hub-pw0-s3015.circ.txt` | OK | 41/4/147/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3015 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g147-gd12-build-LE-aes-nist-hub-pw0-s9021.circ.txt` | OK | 41/4/147/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 9021 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g137-gd12-pol-LC-aes-sbox-a45-pw3-s7002-r2.circ.txt` | OK | 42/4/137/12 | T09 | known-by-23:50 | certified | 9 | 301.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g137-gd12-pol-n45q-s12-r2.circ.txt` | OK | 42/4/137/12 | T09 | known-by-23:50 | certified | 9 | 301.5 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g137-gd12-pol-n45q-s12-v3.circ.txt` | OK | 42/4/137/12 | T09 | known-by-23:50 | certified | 7 | 400.1 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a42-ad4-g137-gd12-pol-n45q-s12.circ.txt` | OK | 42/4/137/12 | T09 | known-by-23:50 | certified | 12 | 303.4 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a42-ad4-g138-gd12-build-n45q-s12-r2.circ.txt` | OK | 42/4/138/12 | T09 | known-by-23:50 | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py --refine2 (pairwise joint re-decomposition) fr |
| P7 | `p7-t09-a42-ad4-g138-gd12-build-n45q-s12-v3.circ.txt` | OK | 42/4/138/12 | T09 | known-by-23:50 | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py plan + bbuild.py (front-cone reuse only)', 'pl |
| P7 | `p7-t09-a42-ad4-g138-gd12-pol-LC-aes-sbox-a45-pw0-s7007.circ.txt` | OK | 42/4/138/12 | T09 | known-by-23:50 | certified | 7007 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g138-gd12-pol-LE-p7-t09-a42-a-pw0-s9017.circ.txt` | OK | 42/4/138/12 | T09 | known-by-23:50 | certified | 9017 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g139-gd12-build-LD-aes-sbox-a45-pw0-s3001.circ.txt` | OK | 42/4/139/12 | T09 | known-by-23:50 | certified | 3001 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g139-gd12-build-LE-p7-t09-a42-a-pw0-s9011.circ.txt` | OK | 42/4/139/12 | T09 | known-by-23:50 | certified | 9011 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g139-gd12-build-LE-p7-t09-a42-a-pw0-s9017.circ.txt` | OK | 42/4/139/12 | T09 | known-by-23:50 | certified | 9017 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g139-gd12-pol-LA-aes-sbox-a45-pw0-s1007.circ.txt` | OK | 42/4/139/12 | T09 | known-by-23:50 | certified | 1007 | 301.5 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g140-gd12-build-LA-aes-sbox-a45-pw0-s1007.circ.txt` | OK | 42/4/140/12 | T09 | known-by-23:50 | certified | 1007 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g140-gd12-build-LC-aes-sbox-a45-pw0-s7007.circ.txt` | OK | 42/4/140/12 | T09 | known-by-23:50 | certified | 7007 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g140-gd12-build-LC-aes-sbox-a45-pw3-s7002-r2.circ.txt` | OK | 42/4/140/12 | T09 | known-by-23:50 | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py --refine2 (pairwise joint re-decomposition) fr |
| P7 | `p7-t09-a42-ad4-g140-gd12-build-n45-s1-v3.circ.txt` | OK | 42/4/140/12 | T09 | known-by-23:50 | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py plan + bbuild.py (front-cone reuse only)', 'pl |
| P7 | `p7-t09-a42-ad4-g140-gd12-build-n45q-s14-v3.circ.txt` | OK | 42/4/140/12 | T09 | known-by-23:50 | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py plan + bbuild.py (front-cone reuse only)', 'pl |
| P7 | `p7-t09-a42-ad4-g140-gd12-pol-LD-aes-nist-hub-pw0-s3027.circ.txt` | OK | 42/4/140/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3027 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g140-gd12-pol-LE-aes-sbox-a45-pw0-s9001.circ.txt` | OK | 42/4/140/12 | T09 | known-by-23:50 | certified | 9001 | 300.4 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g140-gd12-pol-LE-aes-sbox-a45-pw3-s9014.circ.txt` | OK | 42/4/140/12 | T09 | known-by-23:50 | certified | 9014 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g141-gd12-build-LD-aes-nist-hub-pw0-s3027.circ.txt` | OK | 42/4/141/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 3027 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g141-gd12-build-LD-p7-t09-a42-a-pw0-s3011.circ.txt` | OK | 42/4/141/12 | T09 | known-by-23:50 | certified | 3011 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g141-gd12-build-LD-p7-t09-a42-a-pw0-s3029.circ.txt` | OK | 42/4/141/12 | T09 | known-by-23:50 | certified | 3029 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g141-gd12-build-LE-aes-sbox-a45-pw0-s9001.circ.txt` | OK | 42/4/141/12 | T09 | known-by-23:50 | certified | 9001 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g141-gd12-pol-LD-aes-sbox-a45-pw3-s3020.circ.txt` | OK | 42/4/141/12 | T09 | known-by-23:50 | certified | 3020 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g141-gd12-pol-LD-p7-t09-a42-a-pw3-s3006.circ.txt` | OK | 42/4/141/12 | T09 | known-by-23:50 | certified | 3006 | 300.6 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g141-gd12-pol-LE-aes-nist-hub-pw0-s9003.circ.txt` | OK | 42/4/141/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 9003 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g141-gd12-pol-LE-aes-nist-hub-pw0-s9009.circ.txt` | OK | 42/4/141/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 9009 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g141-gd12-pol-LE-aes-sbox-a45-pw3-s9008.circ.txt` | OK | 42/4/141/12 | T09 | known-by-23:50 | certified | 9008 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g142-gd12-build-LC-p7-t09-a42-a-pw0-s7005.circ.txt` | OK | 42/4/142/12 | T09 | known-by-23:50 | certified | 7005 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g142-gd12-build-LD-aes-sbox-a45-pw3-s3008.circ.txt` | OK | 42/4/142/12 | T09 | known-by-23:50 | certified | 3008 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g142-gd12-build-LD-aes-sbox-a45-pw3-s3020.circ.txt` | OK | 42/4/142/12 | T09 | known-by-23:50 | certified | 3020 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g142-gd12-build-LD-p7-t09-a42-a-pw3-s3006.circ.txt` | OK | 42/4/142/12 | T09 | known-by-23:50 | certified | 3006 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g142-gd12-build-LE-aes-sbox-a45-pw3-s9008.circ.txt` | OK | 42/4/142/12 | T09 | known-by-23:50 | certified | 9008 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g142-gd12-build-LE-aes-sbox-a45-pw3-s9014.circ.txt` | OK | 42/4/142/12 | T09 | known-by-23:50 | certified | 9014 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g143-gd12-bopt-n45q-s11.circ.txt` | OK | 42/4/143/12 | T09 | known-by-23:50 | certified | 11 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a42-ad4-g143-gd12-bopt-n45q-s12.circ.txt` | OK | 42/4/143/12 | T09 | known-by-23:50 | certified | 12 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a42-ad4-g143-gd12-bopt-n45q-s14.circ.txt` | OK | 42/4/143/12 | T09 | known-by-23:50 | certified | 14 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a42-ad4-g143-gd12-bopt-n45s1.circ.txt` | OK | 42/4/143/12 | T09 | known-by-23:50 | certified | 1 | 60.0 | {'engine': 'strategies/P7/bopt.py (shared rank-1 bottom, simulated annealing, ca |
| P7 | `p7-t09-a42-ad4-g143-gd12-build-LE-aes-nist-hub-pw0-s9003.circ.txt` | OK | 42/4/143/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 9003 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g143-gd12-build-x48-c12-a45-v3.circ.txt` | OK | 42/4/143/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py plan + bbuild.py (front-cone reuse only)', 'pl |
| P7 | `p7-t09-a42-ad4-g144-gd12-build-LE-aes-nist-hub-pw0-s9009.circ.txt` | OK | 42/4/144/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 9009 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g146-gd12-pol-LC-aes-nist-hub-pw0-s7003.circ.txt` | OK | 42/4/146/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 7003 | 302.3 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g148-gd12-build-LC-aes-nist-hub-pw0-s7003.circ.txt` | OK | 42/4/148/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 7003 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a43-ad4-g137-gd12-pol-LD-aes-sbox-a45-pw0-s3007.circ.txt` | OK | 43/4/137/12 | T09 | known-by-23:50 | certified | 3007 | 301.0 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a43-ad4-g138-gd12-build-LD-aes-sbox-a45-pw0-s3007.circ.txt` | OK | 43/4/138/12 | T09 | known-by-23:50 | certified | 3007 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a43-ad4-g138-gd12-pol-n45-s1-v3.circ.txt` | OK | 43/4/138/12 | T09 | known-by-23:50 | certified | 7 | 402.3 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a43-ad4-g139-gd12-bopt-n45s1-polish-snap.circ.txt` | OK | 43/4/139/12 | T09 | known-by-23:50 | certified | 1 | 105.0 | {'engine': 'strategies/F/fdrive.py gate mode + kernel bfx-593fa798f5 (snapshot o |
| P7 | `p7-t09-a43-ad4-g139-gd12-pol-n45q-s14-v3.circ.txt` | OK | 43/4/139/12 | T09 | known-by-23:50 | certified | 7 | 403.1 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a43-ad4-g139-gd12-pol-n45q-s14.circ.txt` | OK | 43/4/139/12 | T09 | known-by-23:50 | certified | 14 | 300.1 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a43-ad4-g139-gd12-t09-bopt-n45s1-g1.circ.txt` | OK | 43/4/139/12 | T09 | known-by-23:50 | certified | 1 | 1204.6 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a43-ad4-g140-gd12-build-LA-aes-sbox-a45-pw0-s1001.circ.txt` | OK | 43/4/140/12 | T09 | known-by-23:50 | certified | 1001 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a43-ad4-g140-gd12-pol-LD-aes-sbox-a45-pw0-s3025.circ.txt` | OK | 43/4/140/12 | T09 | known-by-23:50 | certified | 3025 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a43-ad4-g141-gd12-build-LB-aes-sbox-a45-pw0-s5001.circ.txt` | OK | 43/4/141/12 | T09 | reproduced | certified | 5001 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a43-ad4-g141-gd12-build-LD-aes-sbox-a45-pw0-s3025.circ.txt` | OK | 43/4/141/12 | T09 | reproduced | certified | 3025 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a43-ad4-g141-gd12-build-LE-aes-sbox-a45-pw0-s9019.circ.txt` | OK | 43/4/141/12 | T09 | reproduced | certified | 9019 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a43-ad4-g145-gd12-bopt-n45q-s13.circ.txt` | OK | 43/4/145/12 | T09 | known-by-23:50 | certified | 13 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a43-ad4-g145-gd12-pol-LD-aes-sbox-a45-pw0-s3013.circ.txt` | OK | 43/4/145/12 | T09 | known-by-23:50 | certified | 3013 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a43-ad4-g146-gd12-bopt-n45q-s15.circ.txt` | OK | 43/4/146/12 | T09 | known-by-23:50 | certified | 15 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a43-ad4-g148-gd12-bopt-h43q-s21.circ.txt` | OK | 43/4/148/12 | T09 | reproduced | certified | 21 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a43-ad4-g148-gd12-build-LD-aes-sbox-a45-pw0-s3013.circ.txt` | OK | 43/4/148/12 | T09 | reproduced | certified | 3013 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a44-ad4-g140-gd12-pol-n45q-s11.circ.txt` | OK | 44/4/140/12 | T09 | known-by-23:50 | certified | 11 | 301.8 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a44-ad4-g140-gd12-pol-x48-c12-a45-v3.circ.txt` | OK | 44/4/140/12 | T09 | known-by-23:50 | certified; construction from a donor outside the limits; all retained states within limits | 7 | 403.0 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a44-ad4-g145-gd12-bopt-n45r-s31.circ.txt` | OK | 44/4/145/12 | T09 | known-by-23:50 | certified | 31 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a45-ad4-g141-gd12-pol-n45q-s13.circ.txt` | OK | 45/4/141/12 | T09 | reproduced | certified | 13 | 300.2 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| Z1 | `z1g13-ctl-ad4a-g1-c8c7227f-s0-a28.circ.txt` | OK | 28/6/591/34 | Z | known-by-23:50 | certified | none (deterministic exhaustive search) | 29 | {'engine': 'H2 gen13 exact dense-subspace search (real model) via Z1 g13case.sh' |
| Z1 | `z1g13-ctl-ad4a-g1-c8c7227f-s1-a28.circ.txt` | OK | 28/6/585/33 | Z | known-by-23:50 | certified | none (deterministic exhaustive search) | 29 | {'engine': 'H2 gen13 exact dense-subspace search (real model) via Z1 g13case.sh' |
| Z1 | `z1g13-ctl-s9m6-semi-g1-c8c7227f-s0-a28.circ.txt` | OK | 28/4/528/27 | Z | known-by-23:50 | certified | none (deterministic exhaustive search) | 1002 | {'engine': 'H2 gen13 exact dense-subspace search (real model) via Z1 g13case.sh' |
| Z1 | `z1g13-m6-131-g1-c8c7227f-s0-a28.circ.txt` | OK | 28/4/541/26 | Z | known-by-23:50 | certified | none (deterministic exhaustive search) | 5 | {'engine': 'H2 gen13 exact dense-subspace search (real model) via Z1 g13case.sh' |
| Z1 | `z1g13-pa-g7-bc60c06b-s0-a28.circ.txt` | OK | 28/5/551/31 | Z | known-by-23:50 | certified | none (deterministic exhaustive search) | 4 | {'engine': 'H2 gen13 exact dense-subspace search (real model) via Z1 g13case.sh' |
| Z1 | `z1g13-pa-g7-bc60c06b-s1-a28.circ.txt` | OK | 28/5/563/29 | Z | known-by-23:50 | certified | none (deterministic exhaustive search) | 4 | {'engine': 'H2 gen13 exact dense-subspace search (real model) via Z1 g13case.sh' |
| Z1 | `z1g13-pb-g7-848cb620-s0-a28.circ.txt` | OK | 28/5/622/29 | Z | known-by-23:50 | certified | none (deterministic exhaustive search) | 4 | {'engine': 'H2 gen13 exact dense-subspace search (real model) via Z1 g13case.sh' |
| Z1 | `z1g13-pb-g7-848cb620-s1-a28.circ.txt` | OK | 28/5/593/31 | Z | known-by-23:50 | certified | none (deterministic exhaustive search) | 4 | {'engine': 'H2 gen13 exact dense-subspace search (real model) via Z1 g13case.sh' |
| night:T01 | `conjpull-a28-ad4-g131-gd22-bb99f3d4bd.circ.txt` | OK | 28/4/131/22 | T01 | reproduced | certified | 877210 | 627.7 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T01 | `conjpull-a28-ad4-g131-gd22-bdc87d0e1e.circ.txt` | OK | 28/4/131/22 | T01 | reproduced | certified | 249237 | 117.4 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T01 | `conjpull-a28-ad4-g132-gd20-cf3dc8cf78.circ.txt` | OK | 28/4/132/20 | T01 | reproduced | not certified (inherited from conjpull-a28-ad4-g133-gd20-fa515c4726.circ.txt) | 74192 | 228.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T01 | `conjpull-a28-ad4-g133-gd20-fa515c4726.circ.txt` | OK | 28/4/133/20 | T01 | reproduced | not certified | 625398 | 718.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T01 | `conjpull-a28-ad4-g133-gd21-3f69455ab7.circ.txt` | OK | 28/4/133/21 | T01 | reproduced | certified | 697862 | 221.0 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T01 | `conjpull-a28-ad4-g133-gd21-83e67054b4.circ.txt` | OK | 28/4/133/21 | T01 | reproduced | certified | 569331 | 445.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T01 | `conjpull-a28-ad4-g135-gd19-724013fd98.circ.txt` | OK | 28/4/135/19 | T01 | reproduced | not certified (inherited from conjpull-a28-ad4-g136-gd20-b9227e45bb.circ.txt) | 895795 | 653.7 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T01 | `conjpull-a28-ad4-g135-gd19-9e0bbd9727.circ.txt` | OK | 28/4/135/19 | T01 | reproduced | not certified (inherited from conjpull-a28-ad4-g136-gd19-6fc30e9a49.circ.txt) | 479161 | 142.7 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T01 | `conjpull-a28-ad4-g135-gd20-0a3799702c.circ.txt` | OK | 28/4/135/20 | T01 | new | not certified | 625398 | 453.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T01 | `conjpull-a28-ad4-g135-gd20-e3811aeb63.circ.txt` | OK | 28/4/135/20 | T01 | new | not certified (inherited from conjpull-a28-ad4-g136-gd20-b9227e45bb.circ.txt) | 895795 | 86.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T01 | `conjpull-a28-ad4-g136-gd18-f25a1d0d0d.circ.txt` | OK | 28/4/136/18 | T01 | reproduced | not certified (inherited from conjpull-a28-ad4-g143-gd19-9cc7c1b54b.circ.txt) | 765317 | 485.2 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T01 | `conjpull-a28-ad4-g136-gd19-6fc30e9a49.circ.txt` | OK | 28/4/136/19 | T01 | reproduced | not certified (inherited from conjpull-a28-ad4-g136-gd20-b9227e45bb.circ.txt) | 895795 | 444.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T01 | `conjpull-a28-ad4-g136-gd20-b9227e45bb.circ.txt` | OK | 28/4/136/20 | T01 | new | not certified | 625398 | 251.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T01 | `conjpull-a28-ad4-g138-gd18-881ca12884.circ.txt` | OK | 28/4/138/18 | T01 | new | not certified (inherited from conjpull-a28-ad4-g136-gd19-6fc30e9a49.circ.txt) | 479161 | 451.2 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T01 | `conjpull-a28-ad4-g138-gd18-8da2a1c175.circ.txt` | OK | 28/4/138/18 | T01 | new | not certified (inherited from conjpull-a28-ad4-g135-gd19-724013fd98.circ.txt) | 369087 | 477.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T01 | `conjpull-a28-ad4-g139-gd20-d66f659e66.circ.txt` | OK | 28/4/139/20 | T01 | new | not certified | 625398 | 147.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T01 | `conjpull-a28-ad4-g140-gd18-d726cd3290.circ.txt` | OK | 28/4/140/18 | T01 | new | not certified (inherited from conjpull-a28-ad4-g143-gd19-9cc7c1b54b.circ.txt) | 765317 | 442.8 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T01 | `conjpull-a28-ad4-g143-gd19-9cc7c1b54b.circ.txt` | OK | 28/4/143/19 | T01 | new | not certified (inherited from conjpull-a28-ad4-g136-gd20-b9227e45bb.circ.txt) | 765111 | 145.7 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T02 | `conjpull-a28-ad4-g152-gd17-086d0b09b3.circ.txt` | OK | 28/4/152/17 | T02 | new | certified | 847315 | 297.1 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T02 | `conjpull-a28-ad4-g152-gd17-addc8e35dd.circ.txt` | OK | 28/4/152/17 | T02 | new | certified | 661241 | 131.5 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T02 | `conjpull-a28-ad4-g155-gd16-3051a4f7d6.circ.txt` | OK | 28/4/155/16 | T02 | new | certified | 661241 | 383.7 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T02 | `conjpull-a28-ad4-g155-gd16-3a5022a572.circ.txt` | OK | 28/4/155/16 | T02 | new | not certified | 777444 | 345.2 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T02 | `conjpull-a28-ad4-g156-gd16-e76177fbe9.circ.txt` | OK | 28/4/156/16 | T02 | new | certified | 376361 | 384.1 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T02 | `conjpull-a28-ad4-g156-gd17-0de2515d87.circ.txt` | OK | 28/4/156/17 | T02 | new | certified | 705217 | 135.1 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T02 | `conjpull-a28-ad4-g160-gd15-7d95773afc.circ.txt` | OK | 28/4/160/15 | T02 | new | certified | 661241 | 551.0 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T02 | `conjpull-a28-ad4-g160-gd15-f2b6365456.circ.txt` | OK | 28/4/160/15 | T02 | new | certified | 189853 | 807.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T02 | `conjpull-a28-ad4-g161-gd15-85c2842ed5.circ.txt` | OK | 28/4/161/15 | T02 | new | certified | 189853 | 83.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T02 | `conjpull-a28-ad4-g161-gd15-a81ab8de4b.circ.txt` | OK | 28/4/161/15 | T02 | new | certified | 607485 | 189.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T02 | `conjpull-a28-ad4-g174-gd14-04e92693dc.circ.txt` | OK | 28/4/174/14 | T02 | reproduced-known-by-23:50 | not certified | 844225 | 348.8 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g125-gd24-7a2073a23b.circ.txt` | OK | 28/5/125/24 | T03 | new | not certified (inherited from conjpull-a28-ad5-g125-gd25-1f642d7931.circ.txt) | 466964 | 358.5 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g125-gd24-f244b8aa4f.circ.txt` | OK | 28/5/125/24 | T03 | new | certified | 21890 | 291.0 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g125-gd25-1f642d7931.circ.txt` | OK | 28/5/125/25 | T03 | reproduced | not certified | 521026 | 357.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g125-gd25-e3a4770f9a.circ.txt` | OK | 28/5/125/25 | T03 | reproduced | certified | 738740 | 639.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g126-gd23-14b498119b.circ.txt` | OK | 28/5/126/23 | T03 | reproduced | not certified | 256244 | 1015.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g126-gd24-ab0b956f79.circ.txt` | OK | 28/5/126/24 | T03 | reproduced | not certified | 154780 | 643.8 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g126-gd25-45d06d5d6b.circ.txt` | OK | 28/5/126/25 | T03 | new | not certified | 154780 | 350.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g127-gd22-796046d36c.circ.txt` | OK | 28/5/127/22 | T03 | reproduced | not certified (inherited from P1-T03-a28-ad5-g129-gd19-182597994ba6.circ.txt) | 338466 | 260.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g128-gd21-3469143bc1.circ.txt` | OK | 28/5/128/21 | T03 | new | not certified (inherited from P1-T03-a28-ad5-g129-gd19-04c1f2de0543.circ.txt) | 691660 | 228.0 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g128-gd21-d20fd9235a.circ.txt` | OK | 28/5/128/21 | T03 | new | certified | 158940 | 536.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g128-gd22-28ca4f34b3.circ.txt` | OK | 28/5/128/22 | T03 | new | not certified (inherited from P1-T03-a28-ad5-g129-gd19-182597994ba6.circ.txt) | 338466 | 131.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g128-gd22-950bbcc271.circ.txt` | OK | 28/5/128/22 | T03 | new | not certified (inherited from P1-T03-a28-ad5-g129-gd19-ec51e03b02b5.circ.txt) | 750360 | 200.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g129-gd20-c1494fb4ab.circ.txt` | OK | 28/5/129/20 | T03 | new | not certified | 689296 | 1059.0 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g131-gd19-1aeaa967a7.circ.txt` | OK | 28/5/131/19 | T03 | new | certified | 282577 | 1251.7 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g131-gd19-f07daa1964.circ.txt` | OK | 28/5/131/19 | T03 | new | not certified (inherited from conjpull-a28-ad5-g129-gd20-c1494fb4ab.circ.txt) | 766903 | 519.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g131-gd20-8509705505.circ.txt` | OK | 28/5/131/20 | T03 | new | certified | 282577 | 590.4 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g132-gd19-fee75cc846.circ.txt` | OK | 28/5/132/19 | T03 | reproduced | certified | 282577 | 1120.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g132-gd20-19d52e42c0.circ.txt` | OK | 28/5/132/20 | T03 | reproduced | certified | 282577 | 499.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g133-gd18-1e60ad1a10.circ.txt` | OK | 28/5/133/18 | T03 | reproduced | certified | 381521 | 458.1 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g133-gd18-25c7a240be.circ.txt` | OK | 28/5/133/18 | T03 | reproduced | certified | 121837 | 506.7 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g133-gd19-847ae8658b.circ.txt` | OK | 28/5/133/19 | T03 | new | certified | 282577 | 943.5 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g133-gd20-96dacb863b.circ.txt` | OK | 28/5/133/20 | T03 | new | certified | 282577 | 455.0 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g134-gd18-a8e33d4724.circ.txt` | OK | 28/5/134/18 | T03 | new | certified | 121837 | 457.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g135-gd18-219aa08856.circ.txt` | OK | 28/5/135/18 | T03 | new | certified | 193977 | 447.1 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g135-gd19-77c7251d37.circ.txt` | OK | 28/5/135/19 | T03 | new | certified | 282577 | 809.2 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g136-gd17-2d65935ac5.circ.txt` | OK | 28/5/136/17 | T03 | reproduced | certified | 193977 | 852.2 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g136-gd17-f9dfce77fa.circ.txt` | OK | 28/5/136/17 | T03 | reproduced | certified | 121837 | 818.2 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `conjpull-a28-ad5-g137-gd17-eda5295706.circ.txt` | OK | 28/5/137/17 | T03 | reproduced | certified | 193977 | 804.5 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T03 | `satlns-a28-ad5-g127-gd22-f012be9705.circ.txt` | OK | 28/5/127/22 | T03 | reproduced | unknown | 725371 | 8.1 | {'engine': 'campaigns/targets/ops/satlns.py (span-pooled SAT LNS, pysat glucose4 |
| night:T03 | `satlns-a28-ad5-g129-gd20-f3d57a4a60.circ.txt` | OK | 28/5/129/20 | T03 | new | unknown | 848231 | 882.3 | {'engine': 'campaigns/targets/ops/satlns.py (span-pooled SAT LNS, pysat glucose4 |
| night:T04 | `conjpull-a32-ad4-g112-gd24-af05e10621.circ.txt` | OK | 32/4/112/24 | T04 | reproduced-known-by-23:50 | certified | 186032 | 232.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g113-gd20-4ddf8b05f2.circ.txt` | OK | 32/4/113/20 | T04 | reproduced-known-by-23:50 | not certified | 580971 | 257.1 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g113-gd20-89eae58b52.circ.txt` | OK | 32/4/113/20 | T04 | reproduced-known-by-23:50 | not certified | 732012 | 409.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g113-gd21-14e59964f9.circ.txt` | OK | 32/4/113/21 | T04 | reproduced-known-by-23:50 | not certified | 186032 | 595.8 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g113-gd21-6d63dcc793.circ.txt` | OK | 32/4/113/21 | T04 | reproduced-known-by-23:50 | not certified | 214488 | 109.2 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g114-gd19-3c51554b08.circ.txt` | OK | 32/4/114/19 | T04 | reproduced-known-by-23:50 | not certified | 186032 | 751.8 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g114-gd19-6954306501.circ.txt` | OK | 32/4/114/19 | T04 | reproduced-known-by-23:50 | not certified | 214488 | 719.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g114-gd20-10a668b1de.circ.txt` | OK | 32/4/114/20 | T04 | reproduced-known-by-23:50 | not certified | 214488 | 263.5 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g114-gd20-b4dc740448.circ.txt` | OK | 32/4/114/20 | T04 | reproduced-known-by-23:50 | not certified | 186032 | 345.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g115-gd18-101cb7a301.circ.txt` | OK | 32/4/115/18 | T04 | reproduced-known-by-23:50 | not certified | 847898 | 236.4 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g115-gd18-b8f55f27a4.circ.txt` | OK | 32/4/115/18 | T04 | reproduced-known-by-23:50 | not certified (inherited from conjpull-a32-ad4-g114-gd19-319e88071e.circ.txt) | 694475 | 148.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g116-gd23-e4725da25b.circ.txt` | OK | 32/4/116/23 | T04 | reproduced | certified | 134991 | 95.8 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g117-gd17-718cdbb8f1.circ.txt` | OK | 32/4/117/17 | T04 | reproduced-known-by-23:50 | not certified (inherited from conjpull-a32-ad4-g114-gd19-319e88071e.circ.txt) | 694475 | 687.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g117-gd17-b83f9deb89.circ.txt` | OK | 32/4/117/17 | T04 | reproduced-known-by-23:50 | not certified (inherited from conjpull-a32-ad4-g115-gd18-e70681d2e6.circ.txt) | 423401 | 82.4 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g119-gd16-3acd9d4790.circ.txt` | OK | 32/4/119/16 | T04 | new | not certified (inherited from conjpull-a32-ad4-g117-gd17-b83f9deb89.circ.txt) | 247057 | 383.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g120-gd16-9e52835a5a.circ.txt` | OK | 32/4/120/16 | T04 | reproduced-known-by-23:50 | not certified (inherited from conjpull-a32-ad4-g115-gd18-e70681d2e6.circ.txt) | 423401 | 790.5 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g120-gd16-c19e3473dd.circ.txt` | OK | 32/4/120/16 | T04 | reproduced-known-by-23:50 | not certified (inherited from conjpull-a32-ad4-g117-gd17-6a8690aa13.circ.txt) | 604827 | 108.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g121-gd16-46eaff98b5.circ.txt` | OK | 32/4/121/16 | T04 | new | not certified (inherited from conjpull-a32-ad4-g117-gd17-6a8690aa13.circ.txt) | 264811 | 79.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g126-gd15-f5ce2b3861.circ.txt` | OK | 32/4/126/15 | T04 | reproduced | not certified (inherited from conjpull-a32-ad4-g120-gd16-b2ae237e4a.circ.txt) | 122635 | 493.4 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g127-gd15-1d4f94ae4b.circ.txt` | OK | 32/4/127/15 | T04 | reproduced | not certified (inherited from conjpull-a32-ad4-g132-gd15-5b52fa7706.circ.txt) | 596085 | 42.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g127-gd15-51a6aacaba.circ.txt` | OK | 32/4/127/15 | T04 | reproduced | not certified | 349254 | 1150.5 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g132-gd15-5b52fa7706.circ.txt` | OK | 32/4/132/15 | T04 | new | not certified (inherited from conjpull-a32-ad4-g120-gd16-b2ae237e4a.circ.txt) | 483837 | 1040.8 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `conjpull-a32-ad4-g139-gd15-c2c0567846.circ.txt` | OK | 32/4/139/15 | T04 | new | not certified (inherited from conjpull-a32-ad4-g120-gd16-b2ae237e4a.circ.txt) | 483837 | 958.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T04 | `satlns-a32-ad4-g112-gd21-21d271692e.circ.txt` | OK | 32/4/112/21 | T04 | new | unknown | 379394 | 697.3 | {'engine': 'campaigns/targets/ops/satlns.py (span-pooled SAT LNS, pysat glucose4 |
| night:T05 | `conjpull-a32-ad4-g111-gd25-1593dfe1d7.circ.txt` | OK | 32/4/111/25 | T05 | reproduced-known-by-23:50 | certified | 94435 | 347.1 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g111-gd25-fc45c9bcdf.circ.txt` | OK | 32/4/111/25 | T05 | reproduced-known-by-23:50 | certified | 265592 | 83.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g112-gd22-2cb236bb73.circ.txt` | OK | 32/4/112/22 | T05 | reproduced-known-by-23:50 | certified | 210962 | 229.5 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g112-gd22-e467f34ee4.circ.txt` | OK | 32/4/112/22 | T05 | reproduced-known-by-23:50 | certified | 94435 | 543.0 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g112-gd23-3644ccb018.circ.txt` | OK | 32/4/112/23 | T05 | reproduced-known-by-23:50 | certified | 210962 | 131.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g113-gd20-da3a1da1c0.circ.txt` | OK | 32/4/113/20 | T05 | reproduced-known-by-23:50 | certified | 320674 | 56.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g113-gd20-e71501eb08.circ.txt` | OK | 32/4/113/20 | T05 | reproduced-known-by-23:50 | not certified | 126848 | 1288.2 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g113-gd21-7b8f9b200b.circ.txt` | OK | 32/4/113/21 | T05 | reproduced-known-by-23:50 | certified | 94435 | 797.4 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g113-gd21-86822c6f8c.circ.txt` | OK | 32/4/113/21 | T05 | reproduced-known-by-23:50 | not certified | 126848 | 901.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g114-gd19-0149c2c9e2.circ.txt` | OK | 32/4/114/19 | T05 | reproduced-known-by-23:50 | not certified (inherited from conjpull-a32-ad4-g115-gd18-e70681d2e6.circ.txt) | 180324 | 39.4 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g114-gd19-319e88071e.circ.txt` | OK | 32/4/114/19 | T05 | reproduced-known-by-23:50 | not certified | 320674 | 471.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g115-gd18-e70681d2e6.circ.txt` | OK | 32/4/115/18 | T05 | reproduced-known-by-23:50 | not certified | 484510 | 553.0 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g116-gd18-7804359769.circ.txt` | OK | 32/4/116/18 | T05 | reproduced-known-by-23:50 | not certified (inherited from conjpull-a32-ad4-g114-gd19-319e88071e.circ.txt) | 419125 | 445.4 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g116-gd18-eec38e0031.circ.txt` | OK | 32/4/116/18 | T05 | reproduced-known-by-23:50 | not certified | 484510 | 436.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g116-gd24-6d52ea58d1.circ.txt` | OK | 32/4/116/24 | T05 | reproduced-known-by-23:50 | certified | 126848 | 131.8 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g117-gd17-6a8690aa13.circ.txt` | OK | 32/4/117/17 | T05 | reproduced-known-by-23:50 | not certified | 816202 | 455.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g117-gd17-f4fbea3974.circ.txt` | OK | 32/4/117/17 | T05 | reproduced-known-by-23:50 | not certified (inherited from conjpull-a32-ad5-g120-gd16-18a1f9c74d.circ.txt) | 850627 | 39.7 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g117-gd20-e7fcd2a92c.circ.txt` | OK | 32/4/117/20 | T05 | new | certified | 265592 | 130.1 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g119-gd17-4566f804a4.circ.txt` | OK | 32/4/119/17 | T05 | new | not certified | 510332 | 442.8 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g119-gd17-acdc99165a.circ.txt` | OK | 32/4/119/17 | T05 | new | not certified | 180324 | 436.7 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g120-gd16-30b5b6bdb5.circ.txt` | OK | 32/4/120/16 | T05 | reproduced-known-by-23:50 | not certified (inherited from conjpull-a32-ad4-g117-gd17-6a8690aa13.circ.txt) | 329109 | 547.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g120-gd16-b2ae237e4a.circ.txt` | OK | 32/4/120/16 | T05 | reproduced-known-by-23:50 | not certified (inherited from conjpull-a32-ad4-g119-gd17-acdc99165a.circ.txt) | 381303 | 456.8 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g121-gd16-c1b9e8bf66.circ.txt` | OK | 32/4/121/16 | T05 | new | not certified (inherited from conjpull-a32-ad4-g117-gd17-6a8690aa13.circ.txt) | 329109 | 433.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g125-gd19-e6c1bcba4b.circ.txt` | OK | 32/4/125/19 | T05 | new | certified | 248343 | 1159.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g127-gd15-e6bfc049c6.circ.txt` | OK | 32/4/127/15 | T05 | reproduced | not certified | 123448 | 718.8 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g127-gd15-ebd0874aeb.circ.txt` | OK | 32/4/127/15 | T05 | reproduced | not certified | 108434 | 96.0 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g129-gd15-3d67920175.circ.txt` | OK | 32/4/129/15 | T05 | new | not certified | 286768 | 716.7 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g131-gd15-979bef4f6e.circ.txt` | OK | 32/4/131/15 | T05 | new | not certified | 123448 | 517.2 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad4-g143-gd15-c26af851aa.circ.txt` | OK | 32/4/143/15 | T05 | new | not certified | 123448 | 440.1 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g105-gd24-48b9e7a153.circ.txt` | OK | 32/5/105/24 | T05 | new | certified | 610750 | 405.2 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g105-gd24-c29289eb8a.circ.txt` | OK | 32/5/105/24 | T05 | new | not certified | 485848 | 638.8 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g105-gd26-4d099bd5a2.circ.txt` | OK | 32/5/105/26 | T05 | reproduced | certified | 610750 | 157.0 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g106-gd21-12187a8683.circ.txt` | OK | 32/5/106/21 | T05 | new | not certified (inherited from conjpull-a32-ad5-g106-gd22-b8eeb91ee6.circ.txt) | 49720 | 100.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g106-gd21-31d6dc63b3.circ.txt` | OK | 32/5/106/21 | T05 | new | not certified (inherited from conjpull-a32-ad5-g106-gd23-ecfa537585.circ.txt) | 698471 | 462.8 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g106-gd22-b8eeb91ee6.circ.txt` | OK | 32/5/106/22 | T05 | new | not certified (inherited from conjpull-a32-ad5-g106-gd23-ecfa537585.circ.txt) | 698471 | 407.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g106-gd23-a860e1e57c.circ.txt` | OK | 32/5/106/23 | T05 | new | certified | 124640 | 257.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g106-gd23-ecfa537585.circ.txt` | OK | 32/5/106/23 | T05 | new | not certified | 610750 | 802.4 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g107-gd21-368743f57a.circ.txt` | OK | 32/5/107/21 | T05 | new | not certified | 610750 | 940.1 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g108-gd20-7f0dee10af.circ.txt` | OK | 32/5/108/20 | T05 | reproduced | certified | 164207 | 642.4 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g108-gd20-967cbf05a3.circ.txt` | OK | 32/5/108/20 | T05 | reproduced | not certified | 601652 | 346.2 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g108-gd21-08f2515957.circ.txt` | OK | 32/5/108/21 | T05 | reproduced | certified | 260897 | 869.1 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g109-gd20-c0cf52f533.circ.txt` | OK | 32/5/109/20 | T05 | reproduced | certified | 164207 | 200.7 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g109-gd20-fa8c2443d0.circ.txt` | OK | 32/5/109/20 | T05 | reproduced | certified | 796873 | 244.7 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g110-gd19-1655161739.circ.txt` | OK | 32/5/110/19 | T05 | new | certified | 467217 | 437.5 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g110-gd19-935ee6ece9.circ.txt` | OK | 32/5/110/19 | T05 | new | certified | 818151 | 599.0 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g111-gd18-67697bc8dd.circ.txt` | OK | 32/5/111/18 | T05 | new | not certified | 220532 | 324.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g111-gd18-6a1b3326e0.circ.txt` | OK | 32/5/111/18 | T05 | new | not certified (inherited from conjpull-a32-ad5-g112-gd18-6e730095f8.circ.txt) | 524647 | 404.2 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g111-gd19-83c4139bcd.circ.txt` | OK | 32/5/111/19 | T05 | reproduced | certified | 521585 | 439.5 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g112-gd18-6e730095f8.circ.txt` | OK | 32/5/112/18 | T05 | reproduced | not certified | 220532 | 93.5 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g112-gd19-b6409bbb87.circ.txt` | OK | 32/5/112/19 | T05 | reproduced | certified | 35591 | 440.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g112-gd20-8084b74946.circ.txt` | OK | 32/5/112/20 | T05 | new | not certified (inherited from conjpull-a32-ad5-g107-gd21-368743f57a.circ.txt) | 872183 | 171.4 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g113-gd18-7ae54b503d.circ.txt` | OK | 32/5/113/18 | T05 | new | not certified | 627088 | 684.1 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g114-gd18-ad949d7e0b.circ.txt` | OK | 32/5/114/18 | T05 | reproduced | not certified | 627088 | 450.1 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g115-gd17-035f5e523f.circ.txt` | OK | 32/5/115/17 | T05 | reproduced | not certified | 220532 | 510.1 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g115-gd17-732921756f.circ.txt` | OK | 32/5/115/17 | T05 | reproduced | not certified | 491336 | 436.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g116-gd17-3830fec62d.circ.txt` | OK | 32/5/116/17 | T05 | reproduced | not certified | 575032 | 438.2 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad5-g120-gd16-18a1f9c74d.circ.txt` | OK | 32/5/120/16 | T05 | new | not certified (inherited from conjpull-a32-ad4-g117-gd17-6a8690aa13.circ.txt) | 367325 | 438.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad7-g103-gd29-8e51adc4e9.circ.txt` | OK | 32/7/103/29 | T05 | new | certified | 775495 | 598.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad7-g103-gd29-a5a3b45c24.circ.txt` | OK | 32/7/103/29 | T05 | new | certified | 17104 | 401.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad7-g104-gd26-8da775ecfd.circ.txt` | OK | 32/7/104/26 | T05 | new | certified | 423171 | 346.2 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad7-g104-gd26-e5b559df19.circ.txt` | OK | 32/7/104/26 | T05 | new | certified | 507127 | 361.8 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad7-g104-gd27-e9b689c745.circ.txt` | OK | 32/7/104/27 | T05 | reproduced-known-by-23:50 | certified | 507127 | 291.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad7-g104-gd28-12d31fa287.circ.txt` | OK | 32/7/104/28 | T05 | reproduced-known-by-23:50 | certified | 716222 | 237.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T05 | `conjpull-a32-ad7-g110-gd25-5cd534e555.circ.txt` | OK | 32/7/110/25 | T05 | new | certified | 423171 | 381.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T06 | `conjpull-a34-ad4-g120-gd15-714f1bebc2.circ.txt` | OK | 34/4/120/15 | T06 | reproduced | certified | 746967 | 83.5 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T06 | `conjpull-a34-ad4-g120-gd15-a2dd4c4f6c.circ.txt` | OK | 34/4/120/15 | T06 | reproduced | certified | 117841 | 45.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T06 | `conjpull-a34-ad4-g121-gd15-2471b7918a.circ.txt` | OK | 34/4/121/15 | T06 | new | certified | 709673 | 45.2 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T06 | `conjpull-a34-ad4-g121-gd15-4b9e9dc1c0.circ.txt` | OK | 34/4/121/15 | T06 | new | certified | 578079 | 43.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T06 | `conjpull-a34-ad4-g122-gd14-621f73cda5.circ.txt` | OK | 34/4/122/14 | T06 | new | certified | 756285 | 39.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T06 | `conjpull-a34-ad4-g122-gd14-713123129a.circ.txt` | OK | 34/4/122/14 | T06 | new | certified | 433291 | 200.2 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T06 | `conjpull-a34-ad4-g123-gd14-f16a32f201.circ.txt` | OK | 34/4/123/14 | T06 | new | certified | 433291 | 181.0 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T06 | `conjpull-a34-ad4-g123-gd14-fbcc906e79.circ.txt` | OK | 34/4/123/14 | T06 | new | not certified | 301145 | 474.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T06 | `conjpull-a34-ad4-g124-gd14-7993ea6c2b.circ.txt` | OK | 34/4/124/14 | T06 | new | certified | 301145 | 79.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T06 | `conjpull-a34-ad4-g124-gd14-92cce7e9a7.circ.txt` | OK | 34/4/124/14 | T06 | new | certified | 721813 | 47.1 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T06 | `conjpull-a34-ad4-g135-gd13-a0a8550834.circ.txt` | OK | 34/4/135/13 | T06 | reproduced-known-by-23:50 | certified | 333132 | 151.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g138-gd23-3ed8aa97bd.circ.txt` | OK | 35/3/138/23 | T07 | new | certified | 706888 | 231.0 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g138-gd23-d35585217b.circ.txt` | OK | 35/3/138/23 | T07 | new | certified | 49660 | 231.0 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g138-gd24-f27addd959.circ.txt` | OK | 35/3/138/24 | T07 | reproduced-known-by-23:50 | certified | 422916 | 230.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g138-gd25-100ac31173.circ.txt` | OK | 35/3/138/25 | T07 | new | certified | 224805 | 230.1 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g138-gd27-e6fe456151.circ.txt` | OK | 35/3/138/27 | T07 | new | certified | 98506 | 230.2 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g139-gd21-f71f0d11d1.circ.txt` | OK | 35/3/139/21 | T07 | new | certified | 321738 | 226.5 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g139-gd22-b20acdff4e.circ.txt` | OK | 35/3/139/22 | T07 | new | certified | 462997 | 227.1 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g139-gd22-f26965830b.circ.txt` | OK | 35/3/139/22 | T07 | new | certified | 380340 | 227.1 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g140-gd21-584de85b56.circ.txt` | OK | 35/3/140/21 | T07 | new | certified | 632360 | 224.8 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g140-gd21-fea2cdb6c5.circ.txt` | OK | 35/3/140/21 | T07 | new | certified | 117375 | 224.7 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g140-gd22-d0747cc30c.circ.txt` | OK | 35/3/140/22 | T07 | reproduced-known-by-23:50 | certified | 201905 | 230.2 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g140-gd22-ffa02a7805.circ.txt` | OK | 35/3/140/22 | T07 | reproduced-known-by-23:50 | certified | 777531 | 384.5 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g140-gd23-4e20783566.circ.txt` | OK | 35/3/140/23 | T07 | new | certified | 631863 | 231.5 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g141-gd20-ac1dac8dd7.circ.txt` | OK | 35/3/141/20 | T07 | reproduced | certified | 832213 | 565.0 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g141-gd22-78cb7d33c6.circ.txt` | OK | 35/3/141/22 | T07 | new | certified | 655995 | 576.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g141-gd23-1a9b46ee8c.circ.txt` | OK | 35/3/141/23 | T07 | new | certified | 220244 | 384.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g141-gd24-5c3eafb67d.circ.txt` | OK | 35/3/141/24 | T07 | reproduced | certified | 56229 | 270.4 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g142-gd22-c7fa59f6e8.circ.txt` | OK | 35/3/142/22 | T07 | reproduced | certified | 262867 | 275.8 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g142-gd24-a5ea59fc80.circ.txt` | OK | 35/3/142/24 | T07 | reproduced | certified | 655995 | 191.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T07 | `conjpull-a35-ad3-g143-gd24-2edade45a8.circ.txt` | OK | 35/3/143/24 | T07 | new | certified | 796221 | 191.9 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T08 | `rebase-a35-ad3-g165-gd13-c1848d8fa7.circ.txt` | OK | 35/3/165/13 | T08 | new | unknown | 17292 | 208.1 | {'engine': 'ops/rebase.py: gbasis class re-basing + P6 hybrid build + capped gat |
| night:T08 | `rebase-a35-ad3-g166-gd13-14aee760f9.circ.txt` | OK | 35/3/166/13 | T08 | new | unknown | 505694 | 209.7 | {'engine': 'ops/rebase.py: gbasis class re-basing + P6 hybrid build + capped gat |
| night:T08 | `rebase-a35-ad3-g166-gd13-93fbd33c14.circ.txt` | OK | 35/3/166/13 | T08 | new | unknown | 57640 | 209.4 | {'engine': 'ops/rebase.py: gbasis class re-basing + P6 hybrid build + capped gat |
| night:T08 | `rebase-a35-ad3-g189-gd12-e6d3f5de5b.circ.txt` | OK | 35/3/189/12 | T08 | reproduced-known-by-23:50 | unknown | 424251 | 539.2 | {'engine': 'ops/rebase.py: gbasis class re-basing + P6 hybrid build + capped gat |
| night:T08 | `rebase-a35-ad3-g193-gd12-576ceb1474.circ.txt` | OK | 35/3/193/12 | T08 | new | unknown | 831452 | 873.2 | {'engine': 'ops/rebase.py: gbasis class re-basing + P6 hybrid build + capped gat |
| night:T08 | `rebase-a35-ad3-g193-gd12-be3bce4c9c.circ.txt` | OK | 35/3/193/12 | T08 | new | unknown | 709247 | 821.2 | {'engine': 'ops/rebase.py: gbasis class re-basing + P6 hybrid build + capped gat |
| night:T08 | `rebase-a35-ad3-g195-gd12-59dc03f7b9.circ.txt` | OK | 35/3/195/12 | T08 | new | unknown | 831452 | 471.4 | {'engine': 'ops/rebase.py: gbasis class re-basing + P6 hybrid build + capped gat |
| night:T08 | `rebase-a35-ad3-g217-gd12-384025305a.circ.txt` | OK | 35/3/217/12 | T08 | new | unknown | 831452 | 242.3 | {'engine': 'ops/rebase.py: gbasis class re-basing + P6 hybrid build + capped gat |
| night:T09 | `bottom-a38-ad4-g135-gd12-ff41a311d8.circ.txt` | OK | 38/4/135/12 | T09 | new | unknown | 432999 | 514.4 | {'engine': 'ops/bottom.py: P7 bopt SA (rank-1 shared bottom, exact Kraft per out |
| night:T09 | `bottom-a38-ad4-g137-gd12-8ae80443cc.circ.txt` | OK | 38/4/137/12 | T09 | new | unknown | 419237 | 107.7 | {'engine': 'ops/bottom.py: P7 bopt SA (rank-1 shared bottom, exact Kraft per out |
| night:T09 | `bottom-a39-ad4-g135-gd12-518a30c4ba.circ.txt` | OK | 39/4/135/12 | T09 | new | unknown | 48694 | 388.9 | {'engine': 'ops/bottom.py: P7 bopt SA (rank-1 shared bottom, exact Kraft per out |
| night:T09 | `bottom-a39-ad4-g136-gd12-dd707c927d.circ.txt` | OK | 39/4/136/12 | T09 | new | unknown | 750849 | 885.4 | {'engine': 'ops/bottom.py: P7 bopt SA (rank-1 shared bottom, exact Kraft per out |
| night:T09 | `bottom-a39-ad4-g138-gd12-09d79a36df.circ.txt` | OK | 39/4/138/12 | T09 | reproduced-known-by-23:50 | unknown | 138919 | 503.5 | {'engine': 'ops/bottom.py: P7 bopt SA (rank-1 shared bottom, exact Kraft per out |
| night:T09 | `bottom-a40-ad4-g137-gd12-3e774357d4.circ.txt` | OK | 40/4/137/12 | T09 | reproduced-known-by-23:50 | unknown | 566822 | 784.4 | {'engine': 'ops/bottom.py: P7 bopt SA (rank-1 shared bottom, exact Kraft per out |
| night:T09 | `bottom-a40-ad4-g137-gd12-b43fdf35cc.circ.txt` | OK | 40/4/137/12 | T09 | reproduced-known-by-23:50 | unknown | 811366 | 410.8 | {'engine': 'ops/bottom.py: P7 bopt SA (rank-1 shared bottom, exact Kraft per out |
| night:T09 | `bottom-a40-ad4-g138-gd12-8af0fe9bad.circ.txt` | OK | 40/4/138/12 | T09 | reproduced-known-by-23:50 | unknown | 811366 | 123.7 | {'engine': 'ops/bottom.py: P7 bopt SA (rank-1 shared bottom, exact Kraft per out |
| night:T09 | `bottom-a40-ad4-g139-gd12-b0c4765434.circ.txt` | OK | 40/4/139/12 | T09 | reproduced-known-by-23:50 | unknown | 365419 | 111.8 | {'engine': 'ops/bottom.py: P7 bopt SA (rank-1 shared bottom, exact Kraft per out |
| night:T09 | `bottom-a40-ad4-g140-gd12-a89f5751c4.circ.txt` | OK | 40/4/140/12 | T09 | reproduced-known-by-23:50 | unknown | 566822 | 112.6 | {'engine': 'ops/bottom.py: P7 bopt SA (rank-1 shared bottom, exact Kraft per out |
| night:T09 | `bottom-a40-ad4-g142-gd12-977f372598.circ.txt` | OK | 40/4/142/12 | T09 | reproduced-known-by-23:50 | unknown | 750849 | 116.2 | {'engine': 'ops/bottom.py: P7 bopt SA (rank-1 shared bottom, exact Kraft per out |
| night:T09 | `bottom-a41-ad4-g142-gd12-3ad6635474.circ.txt` | OK | 41/4/142/12 | T09 | reproduced-known-by-23:50 | unknown | 778147 | 102.6 | {'engine': 'ops/bottom.py: P7 bopt SA (rank-1 shared bottom, exact Kraft per out |
| night:T09 | `bottom-a42-ad4-g139-gd12-3fef2e4c17.circ.txt` | OK | 42/4/139/12 | T09 | reproduced-known-by-23:50 | unknown | 762433 | 105.4 | {'engine': 'ops/bottom.py: P7 bopt SA (rank-1 shared bottom, exact Kraft per out |
| night:T09 | `conjpull-a37-ad4-g127-gd13-00578f7482.circ.txt` | OK | 37/4/127/13 | T09 | new | not certified | 75437 | 286.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T09 | `conjpull-a37-ad4-g128-gd13-154ff2873f.circ.txt` | OK | 37/4/128/13 | T09 | new | certified | 445762 | 42.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T09 | `conjpull-a37-ad4-g128-gd13-6171ffe598.circ.txt` | OK | 37/4/128/13 | T09 | new | certified | 584333 | 43.0 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T10 | `conjpull-a50-ad4-g149-gd11-67b30fc1d9.circ.txt` | OK | 50/4/149/11 | T10 | new | certified | 506178 | 45.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T10 | `conjpull-a50-ad4-g149-gd11-b92a5177a3.circ.txt` | OK | 50/4/149/11 | T10 | new | certified | 820975 | 52.8 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T10 | `conjpull-a51-ad4-g149-gd11-d06e3dc72e.circ.txt` | OK | 51/4/149/11 | T10 | new | certified | 847856 | 45.6 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:T10 | `conjpull-a53-ad4-g148-gd11-a3d037d32f.circ.txt` | OK | 53/4/148/11 | T10 | new | not certified | 820975 | 348.3 | ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged  |
| night:m2 | `bottom-a40-ad4-g136-gd12-3d3a3500dc.circ.txt` | OK | 40/4/136/12 | T09 | new | unknown | 5 | 82.6 | {'engine': 'ops/bottom.py: P7 bopt SA (rank-1 shared bottom, exact Kraft per out |
