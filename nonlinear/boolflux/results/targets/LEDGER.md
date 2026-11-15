# Ledger: campaign 2026-11-15-targets

Generated 2026-11-15T23:17:52Z by `nonlinear/boolflux/campaigns/targets/ledger.py run` (3.6 s). Do not edit; rerun.

- NIST pin 3d807741f937d29d3bef4f32f142ccda0cda9070: 207 manifest files, all sha256 match. Comparison set: every forward AES S-box circuit in `nonlinear/nist/` (`aes_check.published()`: aes-sbox/, old-2020/, sbox/).
- Baseline ("known"): archive as of 2026-11-15T15:20:00Z (built 2026-11-15T15:34:56Z), 4162 files, 4162 verified AES S-box circuits.
- Scanned: 4162 archive files, 398 campaign files; 4560 verified OK (all 256 inputs, two verifiers, NIST library); 0 checked this run; 0 archive files are not forward AES S-box circuits or fail.
- Rules (from TARGETS.json, recomputed every run): hard A <= ref A, AD <= ref AD. strict: G <= ref G, GD <= ref GD, one strictly smaller. tradeoff gates_for_depth: ref GD < GD <= GD_max and G <= ref G - 3; depth_for_gates: GD <= GD_max (< ref GD) and ref G < G <= ref G + 8; and_depth_for_gates: AD < ref AD, AD <= max(AD_targets), G or GD above ref. Tradeoffs never dominate the reference.
- Status: known = tuple realised by a baseline archive file; reproduced = campaign circuit structurally equal (hub.common.structure_key) or tuple-equal to a baseline circuit; new = neither. Evidence: every row is [C] for "this file computes the AES S-box with this (A, AD, G, GD)"; "new"/"dominated" are [C] relative to the scanned folders and the pinned set only.

## Summary

"path" = search-path certification (COMPLIANCE-1820.md): certified | reproduced-certified (by FILE) | not certified | unknown (sidecar path_certified missing); n/a = archive start, not a campaign result. A strict or tradeoff point without a certified campaign file is a result "within limits; search path not certified".

| target | reference | best strict (by G) | best strict (by GD) | best strict, certified path or known | best tradeoff | (G,GD) frontier points |
|---|---|---|---|---|---|---|
| T01 | 28/4/132/22 | 28/4/131/22 [known; path n/a (known)] | 28/4/132/20 [known; path n/a (known)] | 28/4/131/22 [known; path n/a (known)] | - | 9 |
| T02 | 28/4/176/14 | 28/4/174/14 [new (P2); path certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt)] | 28/4/174/14 [new (P2); path certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt)] | 28/4/174/14 [new (P2); path certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt)] | - | 9 |
| T03 | 28/5/128/20 | - | - | - | - | 11 |
| T04 | 32/4/117/19 | 32/4/114/19 [new (P3); path certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt)] | 32/4/117/17 [new (P3); path certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt)] | 32/4/114/19 [new (P3); path certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt)] | gates_for_depth 32/4/113/20 [new (P3); path certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt)] | 9 |
| T05 | 32/7/103/32 | - | - | - | and_depth_for_gates AD6 32/6/104/31 [known; path n/a (known)]; and_depth_for_gates AD5 32/5/104/29 [known; path n/a (known)]; and_depth_for_gates AD4 32/4/111/25 [new (P5); path certified (~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt)] | 12 |
| T06 | 34/4/139/13 | 34/4/134/13 [known; path n/a (known)] | 34/4/134/13 [known; path n/a (known)] | 34/4/134/13 [known; path n/a (known)] | - | 9 |
| T07 | 35/3/139/27 | 35/3/138/24 [new (P6); path certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt)] | 35/3/139/23 [new (P6); path certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt)] | 35/3/138/24 [new (P6); path certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt)] | - | 12 |
| T08 | 35/3/183/13 | 35/3/168/13 [new (P6); path certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt)] | 35/3/181/12 [new (P6); path certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt)] | 35/3/168/13 [new (P6); path certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt)] | - | 12 |
| T09 | 45/4/141/12 | 41/4/136/12 [new (P7); path certified (~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a41-ad4-g136-gd12-pol-LE-p7-t09-a42-a-pw0-s9005.circ.txt)] | 41/4/136/12 [new (P7); path certified (~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a41-ad4-g136-gd12-pol-LE-p7-t09-a42-a-pw0-s9005.circ.txt)] | 41/4/136/12 [new (P7); path certified (~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a41-ad4-g136-gd12-pol-LE-p7-t09-a42-a-pw0-s9005.circ.txt)] | - | 11 |
| T10 | 59/4/159/10 | - | - | - | - | 12 |

## A <= 27

No verified circuit with A <= 27 in any scanned folder.

## Sidecar / verification issues (campaign found/ folders)

- **NOTE** P3 `~/xs-campaigns/2026-11-15-targets/P3/found/p3-c115-p19a-a32-ad4-g116-gd19-20c5d2b662.circ.txt`: kernel stage with start 32/4/115/20 above its caps (GD 20 > cap 19) and no repair_keep; certified by a trace audit (rule 2): audit replay L2 reproduces this circuit gate-identically; all 58897 accepted kernel states have A <= 32, AD <= 4; start 115@20 certified by replay L1. runs/audit (strategies/P3/pdrive_replay.py with t
- **NOTE** P3 `~/xs-campaigns/2026-11-15-targets/P3/found/p3-c115-p19a-a32-ad4-g116-gd19-b49b2addfa.circ.txt`: kernel stage with start 32/4/115/20 above its caps (GD 20 > cap 19) and no repair_keep; certified by a trace audit (rule 2): same gates as ...-20c5d2b662 (only the comment line differs); certified by audit replay L2. runs/audit (strategies/P3/pdrive_replay.py with the original kernel bfx-593fa798f5, stage kernels given an u
- **NOTE** P3 `~/xs-campaigns/2026-11-15-targets/P3/found/p3-cj188-p21-a32-ad4-g115-gd20-098ecd13af.circ.txt`: kernel stage with start 32/4/114/23 above its caps (GD 23 > cap 21) and no repair_keep; certified by a trace audit (rule 2): audit replay L1 reproduces this circuit gate-identically; all 55310 accepted kernel states of the stage have A <= 32, AD <= 4; start (114@23) certified. runs/audit (strategies/P3/pdrive_replay.py with
- **WARN** P3 `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkH1-s1-mix23-k1-a32-ad4-g112-gd22-b8095ec160.circ.txt`: sidecar missing fields: elapsed_s
- **WARN** P3 `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt`: sidecar missing fields: elapsed_s

## T01: reference 28/4/132/22 `aes-sbox-a28-ad4-g132-gd22-xx104-40.circ.txt`

Hard limits A <= 28, AD <= 4. Primary: G < 132 with GD <= 22. Ideal: G and GD both lower. Tradeoffs allowed: [{'kind': 'gates_for_depth', 'GD_max': 24}].

178 verified files within the hard limits, 92 distinct structures, 60 distinct tuples.

- Best strict (by G, then GD): **28/4/131/22** (strict), known, path: n/a (known), `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` (sha256 c7d85507e270)
  - source: archive:results-aes (archive); verification: ledger aes_check.check OK
  - pinned NIST dominating: none

- Best strict (by GD, then G): **28/4/132/20** (strict), known, path: n/a (known), `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` (sha256 1744039db84b)
  - source: archive:results-aes (archive); verification: ledger aes_check.check OK
  - pinned NIST dominating: none

- Best tradeoff: none


### (G, GD) Pareto frontier within the hard limits

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | other | -2 / +2 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | strict | -1 / +0 | known | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | strict | +0 / -2 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | other | +1 / -3 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | other | +3 / -4 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | other | +6 / -5 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | other | +9 / -6 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | other | +21 / -7 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | other | +42 / -8 | new (P2) | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/131/22 | strict | -1 / +0 | known | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | strict | +0 / -2 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

none

### (A, AD, G, GD) Pareto frontier within the hard limits (9 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | other | -2 / +2 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | strict | -1 / +0 | known | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | strict | +0 / -2 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | other | +1 / -3 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | other | +3 / -4 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | other | +6 / -5 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | other | +9 / -6 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | other | +21 / -7 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | other | +42 / -8 | new (P2) | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |

Pinned NIST (G, GD) frontier within the same hard limits: 28/4/131/31 aes-sbox-a28-ad4-g131-gd31-xx103-43.circ.txt, 28/4/132/22 aes-sbox-a28-ad4-g132-gd22-xx104-40.circ.txt, 28/4/134/20 aes-sbox-a28-ad4-g134-gd20-xx106-41.circ.txt, 28/4/141/16 aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt, 28/4/153/15 aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt, 28/4/176/14 aes-sbox-a28-ad4-g176-gd14-xx148-25.circ.txt

## T02: reference 28/4/176/14 `aes-sbox-a28-ad4-g176-gd14-xx148-25.circ.txt`

Hard limits A <= 28, AD <= 4. Primary: GD < 14 with G <= 176; equally G < 176 with GD <= 14. Ideal: both. Tradeoffs allowed: none.

178 verified files within the hard limits, 92 distinct structures, 60 distinct tuples.

- Best strict (by G, then GD): **28/4/174/14** (strict), new (P2), path: certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt), `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` (sha256 d833ee9711a7)
  - start: ~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a28-ad4-g175-gd14-xx147-68.circ.txt sha256 0d8760cc1198; method: strategies/F/fdrive.py mode mix (gate/osc/trb), stage 17 trb-bottom (timing-driven bottom-region rebuild + kernel), caps GD14 AD4 A28, kernel bfx-593fa798f5; seed: 1; elapsed: 2437.0 s
  - verification: OK   /home/joebachir20/xs-campaigns/2026-11-15-targets/P2/runs/t02mix1/snap-g174.circ.txt  A AD G GD = 28 4 174 14  counts {'AND': 28, 'XNOR': 70, 'XOR': 76}; ledger re-check OK
  - pinned NIST dominating: none

- Best tradeoff: none


### (G, GD) Pareto frontier within the hard limits

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | other | -46 / +10 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | other | -45 / +8 | known | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | other | -44 / +6 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | other | -43 / +5 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | other | -41 / +4 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | other | -38 / +3 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | other | -35 / +2 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | other | -23 / +1 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | strict | -2 / +0 | new (P2) | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/174/14 | strict | -2 / +0 | new (P2) | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

none

### (A, AD, G, GD) Pareto frontier within the hard limits (9 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | other | -46 / +10 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | other | -45 / +8 | known | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | other | -44 / +6 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | other | -43 / +5 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | other | -41 / +4 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | other | -38 / +3 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | other | -35 / +2 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | other | -23 / +1 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | strict | -2 / +0 | new (P2) | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |

Pinned NIST (G, GD) frontier within the same hard limits: 28/4/131/31 aes-sbox-a28-ad4-g131-gd31-xx103-43.circ.txt, 28/4/132/22 aes-sbox-a28-ad4-g132-gd22-xx104-40.circ.txt, 28/4/134/20 aes-sbox-a28-ad4-g134-gd20-xx106-41.circ.txt, 28/4/141/16 aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt, 28/4/153/15 aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt, 28/4/176/14 aes-sbox-a28-ad4-g176-gd14-xx148-25.circ.txt

## T03: reference 28/5/128/20 `aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt`

Hard limits A <= 28, AD <= 5. Primary: G < 128 with GD <= 20; also GD < 20 with G <= 128. Ideal: both; no GD increase for minor gate savings. Tradeoffs allowed: none.

600 verified files within the hard limits, 302 distinct structures, 190 distinct tuples.

- Best strict (by G, then GD): none

- Best tradeoff: none


### (G, GD) Pareto frontier within the hard limits

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/5/124/27 | other | -4 / +7 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt | 1 | `~/xs-campaigns/2026-11-14-hub/long/archive/104c1eda4172.bfx` |
| 28/5/125/25 | other | -3 / +5 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-pull-g125-a28-gd25-ad5.circ.txt` |
| 28/5/126/23 | other | -2 / +3 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad5-g126-gd23-0c61a5821a27.bfx` |
| 28/5/127/22 | other | -1 / +2 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-genskel-g127-a28-gd22-ad5.circ.txt` |
| 28/5/128/20 | other | +0 / +0 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt | 1 | `~/xs-campaigns/2026-11-14-hub/long/archive/4096beef1bbf.bfx` |
| 28/5/129/19 | other | +1 / -1 | new (P1) | unknown | none | 41 | `~/xs-campaigns/2026-11-15-targets/P1/found/P1-T03-a28-ad5-g129-gd19-ec51e03b02b5.circ.txt` |
| 28/5/133/18 | other | +5 / -2 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g133-a28-gd18-ad5.circ.txt` |
| 28/5/136/17 | other | +8 / -3 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-trb-g136-a28-gd17-ad5.circ.txt` |
| 28/4/141/16 | other | +13 / -4 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/5/150/15 | other | +22 / -5 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad5-g150-gd15-xx122-23.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/09fbfd47fda3.bfx` |
| 28/4/174/14 | other | +46 / -6 | new (P2) | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

none

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

none

### (A, AD, G, GD) Pareto frontier within the hard limits (18 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | other | +2 / +4 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | other | +3 / +2 | known | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | other | +4 / +0 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | other | +5 / -1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | other | +7 / -2 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | other | +10 / -3 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | other | +13 / -4 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | other | +25 / -5 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | other | +46 / -6 | new (P2) | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |
| 28/5/124/27 | other | -4 / +7 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt | 1 | `~/xs-campaigns/2026-11-14-hub/long/archive/104c1eda4172.bfx` |
| 28/5/125/25 | other | -3 / +5 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-pull-g125-a28-gd25-ad5.circ.txt` |
| 28/5/126/23 | other | -2 / +3 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad5-g126-gd23-0c61a5821a27.bfx` |
| 28/5/127/22 | other | -1 / +2 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-genskel-g127-a28-gd22-ad5.circ.txt` |
| 28/5/128/20 | other | +0 / +0 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt | 1 | `~/xs-campaigns/2026-11-14-hub/long/archive/4096beef1bbf.bfx` |
| 28/5/129/19 | other | +1 / -1 | new (P1) | unknown | none | 41 | `~/xs-campaigns/2026-11-15-targets/P1/found/P1-T03-a28-ad5-g129-gd19-ec51e03b02b5.circ.txt` |
| 28/5/133/18 | other | +5 / -2 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g133-a28-gd18-ad5.circ.txt` |
| 28/5/136/17 | other | +8 / -3 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-trb-g136-a28-gd17-ad5.circ.txt` |
| 28/5/150/15 | other | +22 / -5 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad5-g150-gd15-xx122-23.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/09fbfd47fda3.bfx` |

Pinned NIST (G, GD) frontier within the same hard limits: 28/4/141/16 aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt, 28/4/176/14 aes-sbox-a28-ad4-g176-gd14-xx148-25.circ.txt, 28/5/124/27 aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt, 28/5/128/20 aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt, 28/5/150/15 aes-sbox-a28-ad5-g150-gd15-xx122-23.circ.txt

## T04: reference 32/4/117/19 `aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt`

Hard limits A <= 32, AD <= 4. Primary: G < 117 with GD <= 19. Ideal: both. Tradeoffs allowed: [{'kind': 'gates_for_depth', 'GD_max': 21}].

725 verified files within the hard limits, 502 distinct structures, 238 distinct tuples.

- Best strict (by G, then GD): **32/4/114/19** (strict), new (P3), path: certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt), `~/xs-campaigns/2026-11-15-targets/P3/found/p3-pipe116m19-a32-ad4-g114-gd19-a59961d7ad.circ.txt` (sha256 a59961d7ad8b)
  - start: ~/xs-campaigns/2026-11-15-targets/P3/runs/pipe-conj-116g20-l188-k0-m21/stage2.circ.txt sha256 db41c24e6409; method: pdrive mix caps A32 AD4 GD19 (stage 1 osc repair, t=102 s); lineage: archive 116@20 a43e1ae3d73f -> conjugate lam=188 k=0 (conj.py/mkconj.py) -> pdrive gate cap24 240 s (114@24) -> pdrive mix cap21 (113@20) -> this; kernel bfx-593fa798f5; seed: 3; elapsed: 102.0 s
  - verification: OK   snap-g114-gd19.circ.txt  A AD G GD = 32 4 114 19  counts {'AND': 32, 'XNOR': 41, 'XOR': 41}; ledger re-check OK
  - pinned NIST dominating: none

- Best strict (by GD, then G): **32/4/117/17** (strict), new (P3), path: certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt), `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` (sha256 99c3bf2a3e36)
  - start: ~/xs-campaigns/2026-11-15-targets/P3/runs/rkK1-s2-mix17-k1/pareto/g118-gd17.circ.txt sha256 dddd01b7ade8; method: pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD17, kernel bfx-4dc199db, repair_keep 1; seed: 2212; elapsed: 600.0 s
  - verification: OK   /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/rkN1-s1-mix17-k2/best.circ.txt  A AD G GD = 32 4 117 17  counts {'AND': 32, 'XNOR': 39, 'XOR': 46}; ledger re-check OK
  - pinned NIST dominating: none

- Best tradeoff (gates_for_depth): **32/4/113/20** (tradeoff:gates_for_depth), new (P3), path: certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt), `~/xs-campaigns/2026-11-15-targets/P3/found/p3-pipe-conj-116g20-l188-k0-m21-a32-ad4-g113-gd20-db41c24e64.circ.txt` (sha256 db41c24e6409)
  - start: ~/xs-campaigns/2026-11-15-targets/P3/runs/pipe-conj-116g20-l188-k0-g24/stage1.circ.txt sha256 26e4e09ee8bb; method: pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, kernel bfx-593fa798f5; seed: 2; elapsed: 362.0 s
  - verification: OK   /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/pipe-conj-116g20-l188-k0-m21/best.circ.txt  A AD G GD = 32 4 113 20  counts {'AND': 32, 'XNOR': 38, 'XOR': 43}; ledger re-check OK
  - pinned NIST dominating: none


### (G, GD) Pareto frontier within the hard limits

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 32/4/111/25 | other | -6 / +6 | new (P5) | certified (~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt) | none | 3 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-ad4-113-20-p3-r2-gate30-a32-ad4-g111-gd25-8a6a18f6c7.circ.txt` |
| 32/4/112/22 | other | -5 / +3 | new (P5) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkH1-s1-mix23-k1-a32-ad4-g112-gd22-b8095ec160.circ.txt) | none | 7 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert113-r1-mix26-a32-ad4-g112-gd22-6f3b39a3e3.circ.txt` |
| 32/4/113/20 | tradeoff:gates_for_depth | -4 / +1 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt) | none | 8 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-pipe-conj-116g20-l188-k0-m21-a32-ad4-g113-gd20-db41c24e64.circ.txt` |
| 32/4/114/19 | strict | -3 / +0 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt) | none | 13 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-pipe116m19-a32-ad4-g114-gd19-a59961d7ad.circ.txt` |
| 32/4/115/18 | strict | -2 / -1 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt` |
| 32/4/117/17 | strict | +0 / -2 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` |
| 32/4/120/16 | other | +3 / -3 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt` |
| 32/4/125/15 | other | +8 / -4 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt` |
| 28/4/174/14 | other | +57 / -5 | new (P2) | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 32/4/114/19 | strict | -3 / +0 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt) | none | 13 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-pipe116m19-a32-ad4-g114-gd19-a59961d7ad.circ.txt` |
| 32/4/115/18 | strict | -2 / -1 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt` |
| 32/4/117/17 | strict | +0 / -2 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` |

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 32/4/113/20 | tradeoff:gates_for_depth | -4 / +1 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt) | none | 8 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-pipe-conj-116g20-l188-k0-m21-a32-ad4-g113-gd20-db41c24e64.circ.txt` |

### (A, AD, G, GD) Pareto frontier within the hard limits (23 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | other | +13 / +5 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | other | +14 / +3 | known | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | other | +15 / +1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | other | +16 / +0 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | other | +18 / -1 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | other | +21 / -2 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | other | +24 / -3 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | other | +36 / -4 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | other | +57 / -5 | new (P2) | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |
| 29/4/128/23 | other | +11 / +4 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-X2-x2-g128-a29-gd23-ad4.circ.txt` |
| 29/4/129/19 | other | +12 / +0 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g129-gd19-xx100-56.circ.txt` |
| 29/4/131/17 | other | +14 / -2 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g131-gd17-xx102-61.circ.txt` |
| 29/4/135/16 | other | +18 / -3 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g135-gd16-xx106-50.circ.txt` |
| 29/4/141/15 | other | +24 / -4 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g141-gd15-xx112-56.circ.txt` |
| 30/4/138/15 | other | +21 / -4 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a30-ad4-g138-gd15-xx108-61.circ.txt` |
| 32/4/111/25 | other | -6 / +6 | new (P5) | certified (~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt) | none | 3 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-ad4-113-20-p3-r2-gate30-a32-ad4-g111-gd25-8a6a18f6c7.circ.txt` |
| 32/4/112/22 | other | -5 / +3 | new (P5) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkH1-s1-mix23-k1-a32-ad4-g112-gd22-b8095ec160.circ.txt) | none | 7 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert113-r1-mix26-a32-ad4-g112-gd22-6f3b39a3e3.circ.txt` |
| 32/4/113/20 | tradeoff:gates_for_depth | -4 / +1 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt) | none | 8 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-pipe-conj-116g20-l188-k0-m21-a32-ad4-g113-gd20-db41c24e64.circ.txt` |
| 32/4/114/19 | strict | -3 / +0 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt) | none | 13 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-pipe116m19-a32-ad4-g114-gd19-a59961d7ad.circ.txt` |
| 32/4/115/18 | strict | -2 / -1 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt` |
| 32/4/117/17 | strict | +0 / -2 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` |
| 32/4/120/16 | other | +3 / -3 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt` |
| 32/4/125/15 | other | +8 / -4 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt` |

Pinned NIST (G, GD) frontier within the same hard limits: 28/4/176/14 aes-sbox-a28-ad4-g176-gd14-xx148-25.circ.txt, 32/4/117/19 aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt, 32/4/127/15 aes-sbox-a32-ad4-g127-gd15-xx95-7.circ.txt

## T05: reference 32/7/103/32 `aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt`

Hard limits A <= 32, AD <= 7. Primary: G < 103 with GD <= 32 (overall gate-count record); GD < 32 with G <= 103 also valued. Ideal: both. Tradeoffs allowed: [{'kind': 'and_depth_for_gates', 'AD_targets': [6, 5, 4], 'note': 'separate achievement: lower AND depth with G as close to 103 as possible; report best G (then GD) per AD'}].

2469 verified files within the hard limits, 1563 distinct structures, 838 distinct tuples.

- Best strict (by G, then GD): none

- Best tradeoff (and_depth_for_gates AD6): **32/6/104/31** (tradeoff:and_depth_for_gates), known, path: n/a (known), `~/xs-campaigns/2026-11-14-hub/long/archive/3f7a2fec7b7d.bfx` (sha256 22d5bef5cc55)
  - source: archive:hub-long (archive); verification: ledger aes_check.check OK
  - pinned NIST dominating: 1: 32/5/104/30 (aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt)

- Best tradeoff (and_depth_for_gates AD5): **32/5/104/29** (tradeoff:and_depth_for_gates), known, path: n/a (known), `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g104-a32-gd29-ad5.circ.txt` (sha256 9f893283b39b)
  - source: archive:results-aes (archive); verification: ledger aes_check.check OK
  - pinned NIST dominating: none

- Best tradeoff (and_depth_for_gates AD4): **32/4/111/25** (tradeoff:and_depth_for_gates), new (P5), path: certified (~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt), `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-ad4-113-20-p3-r2-gate30-a32-ad4-g111-gd25-8a6a18f6c7.circ.txt` (sha256 f6b703f6452a)
  - start: ~/xs-campaigns/2026-11-15-targets/P5/runs/lin-ad4-113-20-p3-r1-mix26/next.circ.txt sha256 86db983a7ce4; method: p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, caps A<=32 AD<=4 GD<=30, kernel bfx-94a75e2c18 repair_keep 1; seed: 13; elapsed: 301 s
  - verification: OK /home/joebachir20/xs-campaigns/2026-11-15-targets/P5/runs/lin-ad4-113-20-p3-r2-gate30/best.circ.txt A AD G GD = 32 4 111 25 counts {'AND': 32, 'XNOR': 35, 'XOR': 44}; ledger re-check OK
  - pinned NIST dominating: none


### (G, GD) Pareto frontier within the hard limits

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 32/7/103/32 | other | +0 / +0 | known | n/a (known) | none; equal tuple: aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/3bc535e2b2ad.bfx` |
| 32/7/104/27 | other | +1 / -5 | new (P4) | certified (~/xs-campaigns/2026-11-15-targets/P4/found/p4-deep236-a32-ad7-g104-gd27.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P4/found/p4-deep236-a32-ad7-g104-gd27.circ.txt` |
| 32/5/105/26 | tradeoff:and_depth_for_gates | +2 / -6 | known | n/a (known) | none; equal tuple: aes-sbox-a32-ad5-g105-gd26-xx73-5.circ.txt | 6 | `~/xs-campaigns/2026-11-15-study/C1/found/3650890d9708-ad.bfx` |
| 32/5/106/24 | tradeoff:and_depth_for_gates | +3 / -8 | known; reproduced by P5 | n/a (known) | none | 9 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g106-a32-gd24-ad5.circ.txt` |
| 32/5/107/22 | tradeoff:and_depth_for_gates | +4 / -10 | known | n/a (known) | none; equal tuple: aes-sbox-a32-ad5-g107-gd22-xx75-4.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/4b894ed953be.bfx` |
| 32/5/108/20 | tradeoff:and_depth_for_gates | +5 / -12 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad5-a32-g108-a32-gd20-ad5.circ.txt` |
| 32/5/111/19 | tradeoff:and_depth_for_gates | +8 / -13 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g111-a32-gd19-ad5.circ.txt` |
| 32/5/112/18 | tradeoff:and_depth_for_gates | +9 / -14 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g112-a32-gd18-ad5.circ.txt` |
| 32/5/115/17 | tradeoff:and_depth_for_gates | +12 / -15 | known | n/a (known) | none | 5 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-pull-g115-a32-gd17-ad5.circ.txt` |
| 32/4/120/16 | tradeoff:and_depth_for_gates | +17 / -16 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt` |
| 32/4/125/15 | tradeoff:and_depth_for_gates | +22 / -17 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt` |
| 28/4/174/14 | tradeoff:and_depth_for_gates | +71 / -18 | new (P2) | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

none

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 32/4/111/25 | tradeoff:and_depth_for_gates | +8 / -7 | new (P5) | certified (~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt) | none | 3 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-ad4-113-20-p3-r2-gate30-a32-ad4-g111-gd25-8a6a18f6c7.circ.txt` |
| 32/4/112/22 | tradeoff:and_depth_for_gates | +9 / -10 | new (P5) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkH1-s1-mix23-k1-a32-ad4-g112-gd22-b8095ec160.circ.txt) | none | 7 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert113-r1-mix26-a32-ad4-g112-gd22-6f3b39a3e3.circ.txt` |
| 32/4/113/20 | tradeoff:and_depth_for_gates | +10 / -12 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt) | none | 8 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-pipe-conj-116g20-l188-k0-m21-a32-ad4-g113-gd20-db41c24e64.circ.txt` |
| 32/4/114/19 | tradeoff:and_depth_for_gates | +11 / -13 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt) | none | 13 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-pipe116m19-a32-ad4-g114-gd19-a59961d7ad.circ.txt` |
| 32/4/115/18 | tradeoff:and_depth_for_gates | +12 / -14 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt` |
| 32/4/117/17 | tradeoff:and_depth_for_gates | +14 / -15 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` |
| 32/4/120/16 | tradeoff:and_depth_for_gates | +17 / -16 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt` |
| 32/4/125/15 | tradeoff:and_depth_for_gates | +22 / -17 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt` |
| 28/4/174/14 | tradeoff:and_depth_for_gates | +71 / -18 | new (P2) | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |
| 32/5/104/29 | tradeoff:and_depth_for_gates | +1 / -3 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g104-a32-gd29-ad5.circ.txt` |
| 32/5/105/26 | tradeoff:and_depth_for_gates | +2 / -6 | known | n/a (known) | none; equal tuple: aes-sbox-a32-ad5-g105-gd26-xx73-5.circ.txt | 6 | `~/xs-campaigns/2026-11-15-study/C1/found/3650890d9708-ad.bfx` |
| 32/5/106/24 | tradeoff:and_depth_for_gates | +3 / -8 | known; reproduced by P5 | n/a (known) | none | 9 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g106-a32-gd24-ad5.circ.txt` |
| 32/5/107/22 | tradeoff:and_depth_for_gates | +4 / -10 | known | n/a (known) | none; equal tuple: aes-sbox-a32-ad5-g107-gd22-xx75-4.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/4b894ed953be.bfx` |
| 32/5/108/20 | tradeoff:and_depth_for_gates | +5 / -12 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad5-a32-g108-a32-gd20-ad5.circ.txt` |
| 32/5/111/19 | tradeoff:and_depth_for_gates | +8 / -13 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g111-a32-gd19-ad5.circ.txt` |
| 32/5/112/18 | tradeoff:and_depth_for_gates | +9 / -14 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g112-a32-gd18-ad5.circ.txt` |
| 32/5/115/17 | tradeoff:and_depth_for_gates | +12 / -15 | known | n/a (known) | none | 5 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-pull-g115-a32-gd17-ad5.circ.txt` |

### (A, AD, G, GD) Pareto frontier within the hard limits (50 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | tradeoff:and_depth_for_gates | +27 / -8 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | tradeoff:and_depth_for_gates | +28 / -10 | known | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | tradeoff:and_depth_for_gates | +29 / -12 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | tradeoff:and_depth_for_gates | +30 / -13 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | tradeoff:and_depth_for_gates | +32 / -14 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | tradeoff:and_depth_for_gates | +35 / -15 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | tradeoff:and_depth_for_gates | +38 / -16 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | tradeoff:and_depth_for_gates | +50 / -17 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | tradeoff:and_depth_for_gates | +71 / -18 | new (P2) | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |
| 28/5/124/27 | tradeoff:and_depth_for_gates | +21 / -5 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt | 1 | `~/xs-campaigns/2026-11-14-hub/long/archive/104c1eda4172.bfx` |
| 28/5/125/25 | tradeoff:and_depth_for_gates | +22 / -7 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-pull-g125-a28-gd25-ad5.circ.txt` |
| 28/5/126/23 | tradeoff:and_depth_for_gates | +23 / -9 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad5-g126-gd23-0c61a5821a27.bfx` |
| 28/5/127/22 | tradeoff:and_depth_for_gates | +24 / -10 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-genskel-g127-a28-gd22-ad5.circ.txt` |
| 28/5/128/20 | tradeoff:and_depth_for_gates | +25 / -12 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt | 1 | `~/xs-campaigns/2026-11-14-hub/long/archive/4096beef1bbf.bfx` |
| 28/5/129/19 | tradeoff:and_depth_for_gates (within limits; search path not certified) | +26 / -13 | new (P1) | unknown | none | 41 | `~/xs-campaigns/2026-11-15-targets/P1/found/P1-T03-a28-ad5-g129-gd19-ec51e03b02b5.circ.txt` |
| 28/5/133/18 | tradeoff:and_depth_for_gates | +30 / -14 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g133-a28-gd18-ad5.circ.txt` |
| 28/5/136/17 | tradeoff:and_depth_for_gates | +33 / -15 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-trb-g136-a28-gd17-ad5.circ.txt` |
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
| 32/4/111/25 | tradeoff:and_depth_for_gates | +8 / -7 | new (P5) | certified (~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt) | none | 3 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-ad4-113-20-p3-r2-gate30-a32-ad4-g111-gd25-8a6a18f6c7.circ.txt` |
| 32/4/112/22 | tradeoff:and_depth_for_gates | +9 / -10 | new (P5) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkH1-s1-mix23-k1-a32-ad4-g112-gd22-b8095ec160.circ.txt) | none | 7 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert113-r1-mix26-a32-ad4-g112-gd22-6f3b39a3e3.circ.txt` |
| 32/4/113/20 | tradeoff:and_depth_for_gates | +10 / -12 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt) | none | 8 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-pipe-conj-116g20-l188-k0-m21-a32-ad4-g113-gd20-db41c24e64.circ.txt` |
| 32/4/114/19 | tradeoff:and_depth_for_gates | +11 / -13 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt) | none | 13 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-pipe116m19-a32-ad4-g114-gd19-a59961d7ad.circ.txt` |
| 32/4/115/18 | tradeoff:and_depth_for_gates | +12 / -14 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt` |
| 32/4/117/17 | tradeoff:and_depth_for_gates | +14 / -15 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` |
| 32/4/120/16 | tradeoff:and_depth_for_gates | +17 / -16 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt` |
| 32/4/125/15 | tradeoff:and_depth_for_gates | +22 / -17 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt` |
| 32/5/104/29 | tradeoff:and_depth_for_gates | +1 / -3 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g104-a32-gd29-ad5.circ.txt` |
| 32/5/105/26 | tradeoff:and_depth_for_gates | +2 / -6 | known | n/a (known) | none; equal tuple: aes-sbox-a32-ad5-g105-gd26-xx73-5.circ.txt | 6 | `~/xs-campaigns/2026-11-15-study/C1/found/3650890d9708-ad.bfx` |
| 32/5/106/24 | tradeoff:and_depth_for_gates | +3 / -8 | known; reproduced by P5 | n/a (known) | none | 9 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g106-a32-gd24-ad5.circ.txt` |
| 32/5/107/22 | tradeoff:and_depth_for_gates | +4 / -10 | known | n/a (known) | none; equal tuple: aes-sbox-a32-ad5-g107-gd22-xx75-4.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/4b894ed953be.bfx` |
| 32/5/108/20 | tradeoff:and_depth_for_gates | +5 / -12 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad5-a32-g108-a32-gd20-ad5.circ.txt` |
| 32/5/111/19 | tradeoff:and_depth_for_gates | +8 / -13 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g111-a32-gd19-ad5.circ.txt` |
| 32/5/112/18 | tradeoff:and_depth_for_gates | +9 / -14 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g112-a32-gd18-ad5.circ.txt` |
| 32/5/115/17 | tradeoff:and_depth_for_gates | +12 / -15 | known | n/a (known) | none | 5 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-pull-g115-a32-gd17-ad5.circ.txt` |
| 32/7/103/32 | other | +0 / +0 | known | n/a (known) | none; equal tuple: aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/3bc535e2b2ad.bfx` |
| 32/7/104/27 | other | +1 / -5 | new (P4) | certified (~/xs-campaigns/2026-11-15-targets/P4/found/p4-deep236-a32-ad7-g104-gd27.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P4/found/p4-deep236-a32-ad7-g104-gd27.circ.txt` |

### Best per AND depth at A <= 32

| AD | best G (then GD) at AD = d | status | best G at AD <= d | best GD (then G) at AD = d | status | (G,GD) frontier at AD = d |
|---|---|---|---|---|---|---|
| 7 | 32/7/103/32 | known | 32/7/103/32 | 32/7/109/23 | known | 32/7/103/32, 32/7/104/27, 32/7/108/24, 32/7/109/23 |
| 6 | 32/6/104/31 | known | 32/5/104/29 | 31/6/124/19 | known | 32/6/104/31, 32/6/105/30, 32/6/106/27, 32/6/109/26, 32/6/110/25, 32/6/115/24, 32/6/120/20, 31/6/124/19 |
| 5 | 32/5/104/29 | known | 32/5/104/29 | 32/5/127/15 | known | 32/5/104/29, 32/5/105/26, 32/5/106/24, 32/5/107/22, 32/5/108/20, 32/5/111/19, 32/5/112/18, 32/5/115/17, 32/5/122/16, 32/5/127/15 |
| 4 | 32/4/111/25 | new (P5) | 32/4/111/25 | 28/4/174/14 | new (P2) | 32/4/111/25, 32/4/112/22, 32/4/113/20, 32/4/114/19, 32/4/115/18, 32/4/117/17, 32/4/120/16, 32/4/125/15, 28/4/174/14 |
| 3 | - |  | - | - |  |  |
| 2 | - |  | - | - |  |  |
| 1 | - |  | - | - |  |  |

Pinned NIST (G, GD) frontier within the same hard limits: 28/4/176/14 aes-sbox-a28-ad4-g176-gd14-xx148-25.circ.txt, 32/4/117/19 aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt, 32/4/127/15 aes-sbox-a32-ad4-g127-gd15-xx95-7.circ.txt, 32/5/104/30 aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt, 32/5/105/26 aes-sbox-a32-ad5-g105-gd26-xx73-5.circ.txt, 32/5/107/22 aes-sbox-a32-ad5-g107-gd22-xx75-4.circ.txt, 32/5/109/20 aes-sbox-a32-ad5-g109-gd20-xx77-4.circ.txt, 32/5/122/16 aes-sbox-a32-ad5-g122-gd16-xx90-15.circ.txt, 32/5/127/15 aes-sbox-a32-ad5-g127-gd15-xx95-20.circ.txt, 32/7/103/32 aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt

## T06: reference 34/4/139/13 `aes-sbox-a34-ad4-g139-gd13-xx105-22.circ.txt`

Hard limits A <= 34, AD <= 4. Primary: GD < 13 with G <= 139; secondary G < 139 with GD <= 13. Ideal: both; depth is the main objective. Tradeoffs allowed: none.

1076 verified files within the hard limits, 747 distinct structures, 355 distinct tuples.

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
| 33/4/125/14 | other | -14 / +1 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g125-gd14-xx92-18.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/1317ec0f73e9.bfx` |
| 34/4/134/13 | strict | -5 / +0 | known | n/a (known) | none | 3 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g134-a34-gd13-ad4.circ.txt` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 34/4/134/13 | strict | -5 / +0 | known | n/a (known) | none | 3 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g134-a34-gd13-ad4.circ.txt` |

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

none

### (A, AD, G, GD) Pareto frontier within the hard limits (32 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | other | -9 / +11 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | other | -8 / +9 | known | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | other | -7 / +7 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | other | -6 / +6 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | other | -4 / +5 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | other | -1 / +4 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | other | +2 / +3 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | other | +14 / +2 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | other | +35 / +1 | new (P2) | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |
| 29/4/128/23 | other | -11 / +10 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-X2-x2-g128-a29-gd23-ad4.circ.txt` |
| 29/4/129/19 | other | -10 / +6 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g129-gd19-xx100-56.circ.txt` |
| 29/4/131/17 | other | -8 / +4 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g131-gd17-xx102-61.circ.txt` |
| 29/4/135/16 | other | -4 / +3 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g135-gd16-xx106-50.circ.txt` |
| 29/4/141/15 | other | +2 / +2 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g141-gd15-xx112-56.circ.txt` |
| 30/4/138/15 | other | -1 / +2 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a30-ad4-g138-gd15-xx108-61.circ.txt` |
| 32/4/111/25 | other | -28 / +12 | new (P5) | certified (~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt) | none | 3 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-ad4-113-20-p3-r2-gate30-a32-ad4-g111-gd25-8a6a18f6c7.circ.txt` |
| 32/4/112/22 | other | -27 / +9 | new (P5) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkH1-s1-mix23-k1-a32-ad4-g112-gd22-b8095ec160.circ.txt) | none | 7 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert113-r1-mix26-a32-ad4-g112-gd22-6f3b39a3e3.circ.txt` |
| 32/4/113/20 | other | -26 / +7 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt) | none | 8 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-pipe-conj-116g20-l188-k0-m21-a32-ad4-g113-gd20-db41c24e64.circ.txt` |
| 32/4/114/19 | other | -25 / +6 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt) | none | 13 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-pipe116m19-a32-ad4-g114-gd19-a59961d7ad.circ.txt` |
| 32/4/115/18 | other | -24 / +5 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt` |
| 32/4/117/17 | other | -22 / +4 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` |
| 32/4/120/16 | other | -19 / +3 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt` |
| 32/4/125/15 | other | -14 / +2 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt` |
| 33/4/105/25 | other | -34 / +12 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/0f491596c734.bfx` |
| 33/4/106/22 | other | -33 / +9 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g106-gd22-xx73-5.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/26070040d746.bfx` |
| 33/4/107/20 | other | -32 / +7 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-pull-g107-a33-gd20-ad4.circ.txt` |
| 33/4/108/19 | other | -31 / +6 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt` |
| 33/4/110/18 | other | -29 / +5 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad4-a33-g110-a33-gd18-ad4.circ.txt` |
| 33/4/112/16 | other | -27 / +3 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g112-a33-gd16-ad4.circ.txt` |
| 33/4/115/15 | other | -24 / +2 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-join-g115-a33-gd15-ad4.circ.txt` |
| 33/4/125/14 | other | -14 / +1 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g125-gd14-xx92-18.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/1317ec0f73e9.bfx` |
| 34/4/134/13 | strict | -5 / +0 | known | n/a (known) | none | 3 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g134-a34-gd13-ad4.circ.txt` |

Pinned NIST (G, GD) frontier within the same hard limits: 33/4/105/25 aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt, 33/4/106/22 aes-sbox-a33-ad4-g106-gd22-xx73-5.circ.txt, 33/4/108/20 aes-sbox-a33-ad4-g108-gd20-xx75-5.circ.txt, 33/4/116/15 aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt, 33/4/125/14 aes-sbox-a33-ad4-g125-gd14-xx92-18.circ.txt, 34/4/139/13 aes-sbox-a34-ad4-g139-gd13-xx105-22.circ.txt

## T07: reference 35/3/139/27 `aes-sbox-a35-ad3-g139-gd27-xx104-38.circ.txt`

Hard limits A <= 35, AD <= 3. Primary: G < 139 with GD <= 27. Ideal: both; AD 3 is optimal and preserved. Tradeoffs allowed: [{'kind': 'gates_for_depth', 'GD_max': 29}].

307 verified files within the hard limits, 219 distinct structures, 97 distinct tuples.

- Best strict (by G, then GD): **35/3/138/24** (strict), new (P6), path: certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt), `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt` (sha256 889ecc282bb4)
  - start: ~/xs-campaigns/2026-11-15-targets/P6/runs/polish139c/c27-sd20378/jobs/s0/start.bfx sha256 ce9dd41997e7; method: P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel hub.ops._kernel caps A35 AD3 GD27 objective cost,gd, 240.0 s stage; seed: 20378; elapsed: 240.0 s
  - verification: OK   /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt  A AD G GD = 35 3 138 24  counts {'AND': 35, 'XNOR': 49, 'XOR': 54}; ledger re-check OK
  - pinned NIST dominating: none

- Best strict (by GD, then G): **35/3/139/23** (strict), new (P6), path: certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt), `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt` (sha256 858474bed78d)
  - start: ~/xs-campaigns/2026-11-15-targets/P6/runs/c3-140/x-250-4-b/jobs/s1/start.bfx sha256 9546d678ecc0; method: P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel hub.ops._kernel caps A35 AD3 GD27 objective cost,gd, 200.0 s stage; seed: 3011; elapsed: 200.0 s
  - verification: OK   /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt  A AD G GD = 35 3 139 23  counts {'AND': 35, 'XNOR': 44, 'XOR': 60}; ledger re-check OK
  - pinned NIST dominating: none

- Best tradeoff: none


### (G, GD) Pareto frontier within the hard limits

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 35/3/137/28 | other | -2 / +1 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt` |
| 35/3/138/24 | strict | -1 / -3 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt` |
| 35/3/139/23 | strict | +0 / -4 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt` |
| 35/3/140/22 | other | +1 / -5 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g140-gd22-ecd3572a7c9b.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g140-gd22-ecd3572a7c9b.circ.txt` |
| 35/3/141/19 | other | +2 / -8 | known | n/a (known) | none | 5 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g141-gd19-xx106-46.circ.txt` |
| 35/3/143/18 | other | +4 / -9 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T3-t3-g143-a35-gd18-ad3.circ.txt` |
| 35/3/144/17 | other | +5 / -10 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g144-gd17-xx109-43.circ.txt` |
| 35/3/147/16 | other | +8 / -11 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g147-gd16-xx112-56.circ.txt` |
| 35/3/155/15 | other | +16 / -12 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g155-gd15-xx120-56.circ.txt` |
| 35/3/162/14 | other | +23 / -13 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-F-trb-g162-a35-gd14-ad3.circ.txt` |
| 35/3/168/13 | other | +29 / -14 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt` |
| 35/3/181/12 | other | +42 / -15 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 35/3/138/24 | strict | -1 / -3 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt` |
| 35/3/139/23 | strict | +0 / -4 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt` |

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

none

### (A, AD, G, GD) Pareto frontier within the hard limits (12 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 35/3/137/28 | other | -2 / +1 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt` |
| 35/3/138/24 | strict | -1 / -3 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt` |
| 35/3/139/23 | strict | +0 / -4 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt` |
| 35/3/140/22 | other | +1 / -5 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g140-gd22-ecd3572a7c9b.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g140-gd22-ecd3572a7c9b.circ.txt` |
| 35/3/141/19 | other | +2 / -8 | known | n/a (known) | none | 5 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g141-gd19-xx106-46.circ.txt` |
| 35/3/143/18 | other | +4 / -9 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T3-t3-g143-a35-gd18-ad3.circ.txt` |
| 35/3/144/17 | other | +5 / -10 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g144-gd17-xx109-43.circ.txt` |
| 35/3/147/16 | other | +8 / -11 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g147-gd16-xx112-56.circ.txt` |
| 35/3/155/15 | other | +16 / -12 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g155-gd15-xx120-56.circ.txt` |
| 35/3/162/14 | other | +23 / -13 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-F-trb-g162-a35-gd14-ad3.circ.txt` |
| 35/3/168/13 | other | +29 / -14 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt` |
| 35/3/181/12 | other | +42 / -15 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt` |

Pinned NIST (G, GD) frontier within the same hard limits: 35/3/139/27 aes-sbox-a35-ad3-g139-gd27-xx104-38.circ.txt, 35/3/141/25 aes-sbox-a35-ad3-g141-gd25-xx106-37.circ.txt, 35/3/147/20 aes-sbox-a35-ad3-g147-gd20-xx112-36.circ.txt, 35/3/157/15 aes-sbox-a35-ad3-g157-gd15-xx122-31.circ.txt, 35/3/172/14 aes-sbox-a35-ad3-g172-gd14-xx137-30.circ.txt, 35/3/183/13 aes-sbox-a35-ad3-g183-gd13-xx148-29.circ.txt

## T08: reference 35/3/183/13 `aes-sbox-a35-ad3-g183-gd13-xx148-29.circ.txt`

Hard limits A <= 35, AD <= 3. Primary: GD <= 12, preferably with G <= 183; secondary G much lower with GD <= 13. Ideal: both. Tradeoffs allowed: [{'kind': 'depth_for_gates', 'GD_max': 12}].

307 verified files within the hard limits, 219 distinct structures, 97 distinct tuples.

- Best strict (by G, then GD): **35/3/168/13** (strict), new (P6), path: certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt), `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt` (sha256 cb0edda7231e)
  - start: ~/xs-campaigns/2026-11-15-targets/P6/runs/pull13c/jobs/66d51b7384e4-r2-s0/start.bfx sha256 2bab2df73bd1; method: P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel hub.ops._kernel caps A35 AD3 GD13 objective cost,gd, 240.0 s stage; seed: 473407; elapsed: 240.0 s
  - verification: OK   /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt  A AD G GD = 35 3 168 13  counts {'AND': 35, 'XNOR': 75, 'XOR': 58}; ledger re-check OK
  - pinned NIST dominating: none

- Best strict (by GD, then G): **35/3/181/12** (strict), new (P6), path: certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt), `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt` (sha256 2adedf9e5cd9)
  - start: ~/xs-campaigns/2026-11-15-targets/P6/runs/pull12c/jobs/9552bd8ad634-r0-s0/start.bfx sha256 5eb67aab692c; method: P6 depth pull: 177@13 -> GF(4) one-point coordinate move (T3 gf4build keep2, points [14,25,180,72]; l3scan max Kraft 0.75 at cap 12) -> class re-basing + hybrid build --paar (204@12) -> gate kernel hub.ops._kernel caps A35 AD3 GD12, cost,gd, 240 s stage; seed: 397181; elapsed: 240.0 s
  - verification: OK   /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt  A AD G GD = 35 3 181 12  counts {'AND': 35, 'XNOR': 63, 'XOR': 83}; ledger re-check OK
  - pinned NIST dominating: none

- Best tradeoff: none


### (G, GD) Pareto frontier within the hard limits

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 35/3/137/28 | other | -46 / +15 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt` |
| 35/3/138/24 | other | -45 / +11 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt` |
| 35/3/139/23 | other | -44 / +10 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt` |
| 35/3/140/22 | other | -43 / +9 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g140-gd22-ecd3572a7c9b.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g140-gd22-ecd3572a7c9b.circ.txt` |
| 35/3/141/19 | other | -42 / +6 | known | n/a (known) | none | 5 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g141-gd19-xx106-46.circ.txt` |
| 35/3/143/18 | other | -40 / +5 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T3-t3-g143-a35-gd18-ad3.circ.txt` |
| 35/3/144/17 | other | -39 / +4 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g144-gd17-xx109-43.circ.txt` |
| 35/3/147/16 | other | -36 / +3 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g147-gd16-xx112-56.circ.txt` |
| 35/3/155/15 | other | -28 / +2 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g155-gd15-xx120-56.circ.txt` |
| 35/3/162/14 | other | -21 / +1 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-F-trb-g162-a35-gd14-ad3.circ.txt` |
| 35/3/168/13 | strict | -15 / +0 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt` |
| 35/3/181/12 | strict | -2 / -1 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 35/3/168/13 | strict | -15 / +0 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt` |
| 35/3/181/12 | strict | -2 / -1 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt` |

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

none

### (A, AD, G, GD) Pareto frontier within the hard limits (12 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 35/3/137/28 | other | -46 / +15 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt` |
| 35/3/138/24 | other | -45 / +11 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt` |
| 35/3/139/23 | other | -44 / +10 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt` |
| 35/3/140/22 | other | -43 / +9 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g140-gd22-ecd3572a7c9b.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g140-gd22-ecd3572a7c9b.circ.txt` |
| 35/3/141/19 | other | -42 / +6 | known | n/a (known) | none | 5 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g141-gd19-xx106-46.circ.txt` |
| 35/3/143/18 | other | -40 / +5 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T3-t3-g143-a35-gd18-ad3.circ.txt` |
| 35/3/144/17 | other | -39 / +4 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g144-gd17-xx109-43.circ.txt` |
| 35/3/147/16 | other | -36 / +3 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g147-gd16-xx112-56.circ.txt` |
| 35/3/155/15 | other | -28 / +2 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g155-gd15-xx120-56.circ.txt` |
| 35/3/162/14 | other | -21 / +1 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-F-trb-g162-a35-gd14-ad3.circ.txt` |
| 35/3/168/13 | strict | -15 / +0 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt` |
| 35/3/181/12 | strict | -2 / -1 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt` |

Pinned NIST (G, GD) frontier within the same hard limits: 35/3/139/27 aes-sbox-a35-ad3-g139-gd27-xx104-38.circ.txt, 35/3/141/25 aes-sbox-a35-ad3-g141-gd25-xx106-37.circ.txt, 35/3/147/20 aes-sbox-a35-ad3-g147-gd20-xx112-36.circ.txt, 35/3/157/15 aes-sbox-a35-ad3-g157-gd15-xx122-31.circ.txt, 35/3/172/14 aes-sbox-a35-ad3-g172-gd14-xx137-30.circ.txt, 35/3/183/13 aes-sbox-a35-ad3-g183-gd13-xx148-29.circ.txt

## T09: reference 45/4/141/12 `aes-sbox-a45-ad4-g141-gd12-xx96-25.circ.txt`

Hard limits A <= 45, AD <= 4. Primary: G < 141 with GD <= 12; equally GD <= 11 with G <= 141. Ideal: both. Tradeoffs allowed: [{'kind': 'depth_for_gates', 'GD_max': 11}].

2298 verified files within the hard limits, 1707 distinct structures, 873 distinct tuples.

- Best strict (by G, then GD): **41/4/136/12** (strict), new (P7), path: certified (~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a41-ad4-g136-gd12-pol-LE-p7-t09-a42-a-pw0-s9005.circ.txt), `~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a41-ad4-g136-gd12-pol-LE-p7-t09-a42-a-pw0-s9005.circ.txt` (sha256 86fdc7cea4ae)
  - start: ~/xs-campaigns/2026-11-15-targets/P7/runs/bopt/LE-p7-t09-a42-a-pw0-s9005.circ.txt sha256 8ebaa9a54a76; method: {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', 'caps': {'GD': 12, 'AD': 4, 'A': 41}, 'lex': 'default (cost, gd)', 'run_dir': '/home/joebachir20/xs-campaigns/2026-11-15-targets/P7/runs/pol-LE-p7-t09-a42-a-pw0-s9005'}; seed: 9005; elapsed: 300.2 s
  - verification: OK   /home/joebachir20/xs-campaigns/2026-11-15-targets/P7/runs/pol-LE-p7-t09-a42-a-pw0-s9005/best.circ.txt  A AD G GD = 41 4 136 12  counts {'AND': 41, 'XNOR': 51, 'XOR': 44}; ledger re-check OK
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
| 36/4/129/13 | other | -12 / +1 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g129-a36-gd13-ad4.circ.txt` |
| 41/4/136/12 | strict | -5 / +0 | new (P7) | certified (~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a41-ad4-g136-gd12-pol-LE-p7-t09-a42-a-pw0-s9005.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a41-ad4-g136-gd12-pol-LE-p7-t09-a42-a-pw0-s9005.circ.txt` |
| 44/4/254/11 | other | +113 / -1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T4-t4-g254-a44-gd11-ad4.circ.txt` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 41/4/136/12 | strict | -5 / +0 | new (P7) | certified (~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a41-ad4-g136-gd12-pol-LE-p7-t09-a42-a-pw0-s9005.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a41-ad4-g136-gd12-pol-LE-p7-t09-a42-a-pw0-s9005.circ.txt` |

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

none

### (A, AD, G, GD) Pareto frontier within the hard limits (55 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | other | -11 / +12 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | other | -10 / +10 | known | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | other | -9 / +8 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | other | -8 / +7 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | other | -6 / +6 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | other | -3 / +5 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | other | +0 / +4 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | other | +12 / +3 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | other | +33 / +2 | new (P2) | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |
| 29/4/128/23 | other | -13 / +11 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-X2-x2-g128-a29-gd23-ad4.circ.txt` |
| 29/4/129/19 | other | -12 / +7 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g129-gd19-xx100-56.circ.txt` |
| 29/4/131/17 | other | -10 / +5 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g131-gd17-xx102-61.circ.txt` |
| 29/4/135/16 | other | -6 / +4 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g135-gd16-xx106-50.circ.txt` |
| 29/4/141/15 | other | +0 / +3 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g141-gd15-xx112-56.circ.txt` |
| 30/4/138/15 | other | -3 / +3 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a30-ad4-g138-gd15-xx108-61.circ.txt` |
| 32/4/111/25 | other | -30 / +13 | new (P5) | certified (~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt) | none | 3 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-ad4-113-20-p3-r2-gate30-a32-ad4-g111-gd25-8a6a18f6c7.circ.txt` |
| 32/4/112/22 | other | -29 / +10 | new (P5) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkH1-s1-mix23-k1-a32-ad4-g112-gd22-b8095ec160.circ.txt) | none | 7 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert113-r1-mix26-a32-ad4-g112-gd22-6f3b39a3e3.circ.txt` |
| 32/4/113/20 | other | -28 / +8 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt) | none | 8 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-pipe-conj-116g20-l188-k0-m21-a32-ad4-g113-gd20-db41c24e64.circ.txt` |
| 32/4/114/19 | other | -27 / +7 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt) | none | 13 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-pipe116m19-a32-ad4-g114-gd19-a59961d7ad.circ.txt` |
| 32/4/115/18 | other | -26 / +6 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt` |
| 32/4/117/17 | other | -24 / +5 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` |
| 32/4/120/16 | other | -21 / +4 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt` |
| 32/4/125/15 | other | -16 / +3 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt` |
| 33/4/105/25 | other | -36 / +13 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/0f491596c734.bfx` |
| 33/4/106/22 | other | -35 / +10 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g106-gd22-xx73-5.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/26070040d746.bfx` |
| 33/4/107/20 | other | -34 / +8 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-pull-g107-a33-gd20-ad4.circ.txt` |
| 33/4/108/19 | other | -33 / +7 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt` |
| 33/4/110/18 | other | -31 / +6 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad4-a33-g110-a33-gd18-ad4.circ.txt` |
| 33/4/112/16 | other | -29 / +4 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g112-a33-gd16-ad4.circ.txt` |
| 33/4/115/15 | other | -26 / +3 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-join-g115-a33-gd15-ad4.circ.txt` |
| 33/4/125/14 | other | -16 / +2 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g125-gd14-xx92-18.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/1317ec0f73e9.bfx` |
| 34/4/134/13 | other | -7 / +1 | known | n/a (known) | none | 3 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g134-a34-gd13-ad4.circ.txt` |
| 35/3/137/28 | other | -4 / +16 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt` |
| 35/3/138/24 | other | -3 / +12 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt` |
| 35/3/139/23 | other | -2 / +11 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt` |
| 35/3/140/22 | other | -1 / +10 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g140-gd22-ecd3572a7c9b.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g140-gd22-ecd3572a7c9b.circ.txt` |
| 35/3/141/19 | other | +0 / +7 | known | n/a (known) | none | 5 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g141-gd19-xx106-46.circ.txt` |
| 35/3/143/18 | other | +2 / +6 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T3-t3-g143-a35-gd18-ad3.circ.txt` |
| 35/3/144/17 | other | +3 / +5 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g144-gd17-xx109-43.circ.txt` |
| 35/3/147/16 | other | +6 / +4 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g147-gd16-xx112-56.circ.txt` |
| 35/3/155/15 | other | +14 / +3 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g155-gd15-xx120-56.circ.txt` |
| 35/3/162/14 | other | +21 / +2 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-F-trb-g162-a35-gd14-ad3.circ.txt` |
| 35/3/168/13 | other | +27 / +1 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt` |
| 35/3/181/12 | other | +40 / +0 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt` |
| 35/4/123/14 | other | -18 / +2 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g123-a35-gd14-ad4.circ.txt` |
| 35/4/133/13 | other | -8 / +1 | known | n/a (known) | none; equal tuple: aes-sbox-a35-ad4-g133-gd13-xx98-21.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/4a3bb5d58502.bfx` |
| 36/3/161/14 | other | +20 / +2 | known | n/a (known) | none | 3 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-osc-g161-a36-gd14-ad3.circ.txt` |
| 36/4/129/13 | other | -12 / +1 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g129-a36-gd13-ad4.circ.txt` |
| 37/3/160/14 | other | +19 / +2 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g160-a37-gd14-ad3.circ.txt` |
| 37/4/121/14 | other | -20 / +2 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-D-kernel-g121-a37-gd14-ad4.circ.txt` |
| 39/4/137/12 | strict | -4 / +0 | new (P7) | certified (~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a39-ad4-g137-gd12-pol-LE-aes-nist-hub-pw3-s9004.circ.txt); construction from a donor outside the limits; all retained states within limits | none | 2 | `~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a39-ad4-g137-gd12-pol-LE-aes-sbox-a45-pw3-s9002.circ.txt` |
| 41/4/136/12 | strict | -5 / +0 | new (P7) | certified (~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a41-ad4-g136-gd12-pol-LE-p7-t09-a42-a-pw0-s9005.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a41-ad4-g136-gd12-pol-LE-p7-t09-a42-a-pw0-s9005.circ.txt` |
| 42/4/284/11 | other | +143 / -1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T4-t4-g284-a42-gd11-ad4.circ.txt` |
| 43/4/278/11 | other | +137 / -1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T4-t4-g278-a43-gd11-ad4.circ.txt` |
| 44/4/254/11 | other | +113 / -1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T4-t4-g254-a44-gd11-ad4.circ.txt` |

Pinned NIST (G, GD) frontier within the same hard limits: 33/4/105/25 aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt, 33/4/106/22 aes-sbox-a33-ad4-g106-gd22-xx73-5.circ.txt, 33/4/108/20 aes-sbox-a33-ad4-g108-gd20-xx75-5.circ.txt, 33/4/116/15 aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt, 33/4/125/14 aes-sbox-a33-ad4-g125-gd14-xx92-18.circ.txt, 35/4/133/13 aes-sbox-a35-ad4-g133-gd13-xx98-21.circ.txt, 45/4/141/12 aes-sbox-a45-ad4-g141-gd12-xx96-25.circ.txt

## T10: reference 59/4/159/10 `aes-sbox-a59-ad4-g159-gd10-xxn100-30-3.circ.txt`

Hard limits A <= 59, AD <= 4. Primary: G < 159 with GD <= 10; ambitious GD <= 9 preferably with G <= 159. Ideal: both; GD 10 is not a proven bound. Tradeoffs allowed: [{'kind': 'depth_for_gates', 'GD_max': 9}].

2427 verified files within the hard limits, 1808 distinct structures, 951 distinct tuples.

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
| 36/4/129/13 | other | -30 / +3 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g129-a36-gd13-ad4.circ.txt` |
| 41/4/136/12 | other | -23 / +2 | new (P7) | certified (~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a41-ad4-g136-gd12-pol-LE-p7-t09-a42-a-pw0-s9005.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a41-ad4-g136-gd12-pol-LE-p7-t09-a42-a-pw0-s9005.circ.txt` |
| 49/4/148/11 | other | -11 / +1 | known | n/a (known) | none; equal tuple: aes-sbox-a49-ad4-g148-gd11-xx99-23.circ.txt | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd11-ad4-a49-g148-a49-gd11-ad4.circ.txt` |
| 59/4/159/10 | other | +0 / +0 | known | n/a (known) | none; equal tuple: aes-sbox-a59-ad4-g159-gd10-xxn100-30-3.circ.txt | 3 | `~/xs-campaigns/2026-11-14-hub/long/archive/0ab3e1c5b961.bfx` |

### Strict improvements (Pareto in G, GD; smallest A, AD shown)

none

### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)

none

### (A, AD, G, GD) Pareto frontier within the hard limits (60 points)

| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |
|---|---|---|---|---|---|---|---|
| 28/4/130/24 | other | -29 / +14 | known | n/a (known) | none | 1 | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | other | -28 / +12 | known | n/a (known) | none | 6 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt` |
| 28/4/132/20 | other | -27 / +10 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt` |
| 28/4/133/19 | other | -26 / +9 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt` |
| 28/4/135/18 | other | -24 / +8 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt` |
| 28/4/138/17 | other | -21 / +7 | known | n/a (known) | none | 1 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt` |
| 28/4/141/16 | other | -18 / +6 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | 2 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | other | -6 / +5 | known | n/a (known) | none; equal tuple: aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt` |
| 28/4/174/14 | other | +15 / +4 | new (P2) | certified (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` |
| 29/4/128/23 | other | -31 / +13 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-X2-x2-g128-a29-gd23-ad4.circ.txt` |
| 29/4/129/19 | other | -30 / +9 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g129-gd19-xx100-56.circ.txt` |
| 29/4/131/17 | other | -28 / +7 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g131-gd17-xx102-61.circ.txt` |
| 29/4/135/16 | other | -24 / +6 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g135-gd16-xx106-50.circ.txt` |
| 29/4/141/15 | other | -18 / +5 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a29-ad4-g141-gd15-xx112-56.circ.txt` |
| 30/4/138/15 | other | -21 / +5 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a30-ad4-g138-gd15-xx108-61.circ.txt` |
| 32/4/111/25 | other | -48 / +15 | new (P5) | certified (~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt) | none | 3 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-ad4-113-20-p3-r2-gate30-a32-ad4-g111-gd25-8a6a18f6c7.circ.txt` |
| 32/4/112/22 | other | -47 / +12 | new (P5) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkH1-s1-mix23-k1-a32-ad4-g112-gd22-b8095ec160.circ.txt) | none | 7 | `~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert113-r1-mix26-a32-ad4-g112-gd22-6f3b39a3e3.circ.txt` |
| 32/4/113/20 | other | -46 / +10 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt) | none | 8 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-pipe-conj-116g20-l188-k0-m21-a32-ad4-g113-gd20-db41c24e64.circ.txt` |
| 32/4/114/19 | other | -45 / +9 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt) | none | 13 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-pipe116m19-a32-ad4-g114-gd19-a59961d7ad.circ.txt` |
| 32/4/115/18 | other | -44 / +8 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt) | none | 2 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt` |
| 32/4/117/17 | other | -42 / +7 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` |
| 32/4/120/16 | other | -39 / +6 | new (P3) | certified (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt` |
| 32/4/125/15 | other | -34 / +5 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt` |
| 33/4/105/25 | other | -54 / +15 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/0f491596c734.bfx` |
| 33/4/106/22 | other | -53 / +12 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g106-gd22-xx73-5.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/26070040d746.bfx` |
| 33/4/107/20 | other | -52 / +10 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-pull-g107-a33-gd20-ad4.circ.txt` |
| 33/4/108/19 | other | -51 / +9 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt` |
| 33/4/110/18 | other | -49 / +8 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd20-ad4-a33-g110-a33-gd18-ad4.circ.txt` |
| 33/4/112/16 | other | -47 / +6 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g112-a33-gd16-ad4.circ.txt` |
| 33/4/115/15 | other | -44 / +5 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-join-g115-a33-gd15-ad4.circ.txt` |
| 33/4/125/14 | other | -34 / +4 | known | n/a (known) | none; equal tuple: aes-sbox-a33-ad4-g125-gd14-xx92-18.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/1317ec0f73e9.bfx` |
| 34/4/134/13 | other | -25 / +3 | known | n/a (known) | none | 3 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g134-a34-gd13-ad4.circ.txt` |
| 35/3/137/28 | other | -22 / +18 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt` |
| 35/3/138/24 | other | -21 / +14 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt` |
| 35/3/139/23 | other | -20 / +13 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt` |
| 35/3/140/22 | other | -19 / +12 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g140-gd22-ecd3572a7c9b.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g140-gd22-ecd3572a7c9b.circ.txt` |
| 35/3/141/19 | other | -18 / +9 | known | n/a (known) | none | 5 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g141-gd19-xx106-46.circ.txt` |
| 35/3/143/18 | other | -16 / +8 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T3-t3-g143-a35-gd18-ad3.circ.txt` |
| 35/3/144/17 | other | -15 / +7 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g144-gd17-xx109-43.circ.txt` |
| 35/3/147/16 | other | -12 / +6 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g147-gd16-xx112-56.circ.txt` |
| 35/3/155/15 | other | -4 / +5 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g155-gd15-xx120-56.circ.txt` |
| 35/3/162/14 | other | +3 / +4 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-F-trb-g162-a35-gd14-ad3.circ.txt` |
| 35/3/168/13 | other | +9 / +3 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt` |
| 35/3/181/12 | other | +22 / +2 | new (P6) | certified (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt` |
| 35/4/123/14 | other | -36 / +4 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g123-a35-gd14-ad4.circ.txt` |
| 35/4/133/13 | other | -26 / +3 | known | n/a (known) | none; equal tuple: aes-sbox-a35-ad4-g133-gd13-xx98-21.circ.txt | 4 | `~/xs-campaigns/2026-11-14-hub/long/archive/4a3bb5d58502.bfx` |
| 36/3/161/14 | other | +2 / +4 | known | n/a (known) | none | 3 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-osc-g161-a36-gd14-ad3.circ.txt` |
| 36/4/129/13 | other | -30 / +3 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g129-a36-gd13-ad4.circ.txt` |
| 37/3/160/14 | other | +1 / +4 | known | n/a (known) | none | 2 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g160-a37-gd14-ad3.circ.txt` |
| 37/4/121/14 | other | -38 / +4 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-D-kernel-g121-a37-gd14-ad4.circ.txt` |
| 39/4/137/12 | other | -22 / +2 | new (P7) | certified (~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a39-ad4-g137-gd12-pol-LE-aes-nist-hub-pw3-s9004.circ.txt); construction from a donor outside the limits; all retained states within limits | none | 2 | `~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a39-ad4-g137-gd12-pol-LE-aes-sbox-a45-pw3-s9002.circ.txt` |
| 41/4/136/12 | other | -23 / +2 | new (P7) | certified (~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a41-ad4-g136-gd12-pol-LE-p7-t09-a42-a-pw0-s9005.circ.txt) | none | 1 | `~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a41-ad4-g136-gd12-pol-LE-p7-t09-a42-a-pw0-s9005.circ.txt` |
| 42/4/284/11 | other | +125 / +1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T4-t4-g284-a42-gd11-ad4.circ.txt` |
| 43/4/278/11 | other | +119 / +1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T4-t4-g278-a43-gd11-ad4.circ.txt` |
| 44/4/254/11 | other | +95 / +1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T4-t4-g254-a44-gd11-ad4.circ.txt` |
| 46/4/200/11 | other | +41 / +1 | known | n/a (known) | none | 4 | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a46-ad4-g200-gd11-xx154-63.circ.txt` |
| 47/4/186/11 | other | +27 / +1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-T4-t4-g186-a47-gd11-ad4.circ.txt` |
| 48/4/151/11 | other | -8 / +1 | known | n/a (known) | none | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-join-g151-a48-gd11-ad4.circ.txt` |
| 49/4/148/11 | other | -11 / +1 | known | n/a (known) | none; equal tuple: aes-sbox-a49-ad4-g148-gd11-xx99-23.circ.txt | 4 | `~/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd11-ad4-a49-g148-a49-gd11-ad4.circ.txt` |
| 59/4/159/10 | other | +0 / +0 | known | n/a (known) | none; equal tuple: aes-sbox-a59-ad4-g159-gd10-xxn100-30-3.circ.txt | 3 | `~/xs-campaigns/2026-11-14-hub/long/archive/0ab3e1c5b961.bfx` |

Pinned NIST (G, GD) frontier within the same hard limits: 33/4/105/25 aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt, 33/4/106/22 aes-sbox-a33-ad4-g106-gd22-xx73-5.circ.txt, 33/4/108/20 aes-sbox-a33-ad4-g108-gd20-xx75-5.circ.txt, 33/4/116/15 aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt, 33/4/125/14 aes-sbox-a33-ad4-g125-gd14-xx92-18.circ.txt, 35/4/133/13 aes-sbox-a35-ad4-g133-gd13-xx98-21.circ.txt, 45/4/141/12 aes-sbox-a45-ad4-g141-gd12-xx96-25.circ.txt, 49/4/148/11 aes-sbox-a49-ad4-g148-gd11-xx99-23.circ.txt, 59/4/159/10 aes-sbox-a59-ad4-g159-gd10-xxn100-30-3.circ.txt

## All campaign circuit files (398)

| agent | file | ok | A/AD/G/GD | target | status | path | seed | elapsed_s | method |
|---|---|---|---|---|---|---|---|---|---|
| P1 | `P1-T03-a28-ad5-g129-gd19-04c1f2de0543.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 337 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-15cf294dce41.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 306 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-182597994ba6.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 284 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-22a009ce455a.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 361 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-2bca397809b9.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 314 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-2e75bcd9ff9d.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 293 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-3128f33c96ca.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 463 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-36167d73d14f.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 436 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-3714500a3ba9.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 301 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-432a787aeaf2.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 244 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-438ed7f28c0b.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 283 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-4436561a4144.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 418 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-445304d0406e.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 437 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-4a3ef4c61095.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 346 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-5832ee7d6edb.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 355 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-6001a9a9b976.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 414 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-65280a926d2b.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 439 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-6fb1d29906a2.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 377 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-7327a44f9895.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 250 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-86c563534eef.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 278 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-8fe98f6d1cf6.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 383 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-a18cfce0dce1.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 330 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-b3fe2f6e3f5d.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 448 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-b8536ab17ef6.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 358 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-b94e853fc505.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 427 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-baa05182d857.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 327 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-bb726d78f2fe.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 321 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-bdf13f65c41f.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 340 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-c192be76787d.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 424 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-c4ff2fe1413e.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 420 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-c57b40b919c4.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 469 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-c6ad4ac8f023.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 364 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-cf6607647a0a.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 387 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-d0e026e8c4ad.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 440 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-d2ca9972aecf.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 403 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-d973cc3e5713.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 378 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-d9ea2f0eec0f.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 318 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-da61d52b387b.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 453 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-dc9cca09a667.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 370 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-dfc0717b1798.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 365 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-ec51e03b02b5.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 241 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-f04ad7f01ee8.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 428 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-f485696fb088.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 344 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P1 | `P1-T03-a28-ad5-g129-gd19-fcfb3b6c3efe.circ.txt` | OK | 28/5/129/19 | T03 | new | unknown | 23 | not logged per step by this version (run total 900 s; step 350 of 480) | {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': |
| P2 | `t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt` | OK | 28/4/174/14 | T02 | new | certified | 1 | 2437.0 | strategies/F/fdrive.py mode mix (gate/osc/trb), stage 17 trb-bottom (timing-driv |
| P2 | `t02-a28-ad4-g174-gd14-t02mix1.circ.txt` | OK | 28/4/174/14 | T02 | new | certified | 1 | 7202.0 | strategies/F/fdrive.py mode mix, caps GD14 AD4 A28, kernel bfx-593fa798f5 |
| P2 | `t06-a34-ad4-g134-gd14-t06bopt-s5.circ.txt` | OK | 34/4/134/14 | T06 | new | certified | 5 | 1201.0 | strategies/P2/fdrive_p2.py mode gate, caps GD13 AD4 A34, kernel bfx-94a75e2c18,  |
| P2 | `t06-a34-ad4-g135-gd13-t06rs-c0011-g161.circ.txt` | OK | 34/4/135/13 | T06 | new | certified | 611 | 1501.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g135-gd13-t06rs-c0022-g159.circ.txt` | OK | 34/4/135/13 | T06 | new | certified | 622 | 1500.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g135-gd14-t06bopt-s6.circ.txt` | OK | 34/4/135/14 | T06 | reproduced | certified | 6 | 900.0 | strategies/P2/fdrive_p2.py mode gate, caps GD13 AD4 A34, kernel bfx-94a75e2c18,  |
| P2 | `t06-a34-ad4-g136-gd13-t06rs16trb52.circ.txt` | OK | 34/4/136/13 | T06 | new | certified | 52 | 1801.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g136-gd13-t06rs5trb51.circ.txt` | OK | 34/4/136/13 | T06 | new | certified | 51 | 1800.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g137-gd13-t06rs-c0010-g158.circ.txt` | OK | 34/4/137/13 | T06 | new | certified | 610 | 1500.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g137-gd13-t06rs-c0021-g160.circ.txt` | OK | 34/4/137/13 | T06 | new | certified | 621 | 1500.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g141-gd13-ev-t06a-p1.circ.txt` | OK | 34/4/141/13 | T06 | reproduced | certified | 901 | 900.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g141-gd13-t06rs-c0008-g168.circ.txt` | OK | 34/4/141/13 | T06 | reproduced | certified | 608 | 1500.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g141-gd13-t06rs-c0018-g167.circ.txt` | OK | 34/4/141/13 | T06 | reproduced | certified | 618 | 1501.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g142-gd13-ev-t06a-p2.circ.txt` | OK | 34/4/142/13 | T06 | reproduced | certified | 902 | 900.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g143-gd13-ev-t06b-p2.circ.txt` | OK | 34/4/143/13 | T06 | new | certified | 902 | 900.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P2 | `t06-a34-ad4-g146-gd13-ev-t06b-p1.circ.txt` | OK | 34/4/146/13 | T06 | new | certified | 901 | 900.0 | strategies/P2/fdrive_p2.py mode trb, caps GD13 AD4 A34, kernel bfx-94a75e2c18, r |
| P3 | `p3-c115-p19a-a32-ad4-g116-gd19-20c5d2b662.circ.txt` | OK | 32/4/116/19 | T04 | new | certified | 2 | 145.0 | pdrive mix (gate/osc/trb) caps A32 AD4 GD19, stage 1 osc (kernel at cap 20, then |
| P3 | `p3-c115-p19a-a32-ad4-g116-gd19-b49b2addfa.circ.txt` | OK | 32/4/116/19 | T04 | new | certified | 2 | 903.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-c116-m19-a32-ad4-g116-gd19-21ad562580.circ.txt` | OK | 32/4/116/19 | T04 | new | certified | 4 | 901.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-cj188-p21-a32-ad4-g115-gd20-098ecd13af.circ.txt` | OK | 32/4/115/20 | T04 | new | certified | 1 | 900.0 | pdrive mix (gate/osc/trb) caps A32 AD4 GD21 from the conjugate-derived 114@23; k |
| P3 | `p3-cj188c26-a32-ad4-g114-gd23-a114ea59bf.circ.txt` | OK | 32/4/114/23 | T04 | new | certified | 1 | 300.0 | conjugate lam=188 k=0 of NIST-equivalent 117@19 (conj.py/mkconj.py: inputs x->18 |
| P3 | `p3-pipe-conj-116g20-l188-k0-m21-a32-ad4-g113-gd20-db41c24e64.circ.txt` | OK | 32/4/113/20 | T04 | new | not certified | 2 | 362.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-pipe-conj-116g20-l188-k0-m21-a32-ad4-g113-gd21-197c32efc7.circ.txt` | OK | 32/4/113/21 | T04 | new | not certified | 2 | 362.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-pipe116m19-a32-ad4-g114-gd19-a59961d7ad.circ.txt` | OK | 32/4/114/19 | T04 | new | not certified | 3 | 102.0 | pdrive mix caps A32 AD4 GD19 (stage 1 osc repair, t=102 s); lineage: archive 116 |
| P3 | `p3-rkD1-s1-mix21-k2-a32-ad4-g115-gd19-d0eb6a2b7f.circ.txt` | OK | 32/4/115/19 | T04 | new | certified | 612 | 601.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt` | OK | 32/4/113/20 | T04 | new | certified | 1011 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkG1-s1-mix21-k2-a32-ad4-g113-gd20-3a9cfe0c28.circ.txt` | OK | 32/4/113/20 | T04 | new | certified | 1012 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkG1-s1-mix21-k2-a32-ad4-g113-gd21-5f4aa69922.circ.txt` | OK | 32/4/113/21 | T04 | new | certified | 1012 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkG1-s1-mix21-k2-a32-ad4-g114-gd20-b872c819ec.circ.txt` | OK | 32/4/114/20 | T04 | new | certified | 1012 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt` | OK | 32/4/114/19 | T04 | new | certified | 1031 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkG1-s3-mix19-k1-a32-ad4-g115-gd19-606196db63.circ.txt` | OK | 32/4/115/19 | T04 | new | certified | 1031 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkH1-s1-mix23-k1-a32-ad4-g112-gd22-b8095ec160.circ.txt` | OK | 32/4/112/22 | T04 | new | certified | 1211 | None | pdrive mode from command.txt, repair_keep 1, kernel bfx-4dc199db (run Pareto set |
| P3 | `p3-rkH1-s2-mix21-k1-a32-ad4-g113-gd20-c7e62edf3e.circ.txt` | OK | 32/4/113/20 | T04 | new | certified | 1221 | 362.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkH1-s2-mix21-k1-a32-ad4-g114-gd20-b127c5cdb3.circ.txt` | OK | 32/4/114/20 | T04 | new | certified | 1221 | 362.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkH1-s2-mix21-k2-a32-ad4-g113-gd20-43a7823916.circ.txt` | OK | 32/4/113/20 | T04 | new | certified | 1222 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkH1-s2-mix21-k2-a32-ad4-g113-gd21-d24fdfaf04.circ.txt` | OK | 32/4/113/21 | T04 | new | certified | 1222 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkH1-s2-mix21-k2-a32-ad4-g114-gd20-e308e0d115.circ.txt` | OK | 32/4/114/20 | T04 | new | certified | 1222 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkH1-s3-mix19-k1-a32-ad4-g114-gd19-b9c4889e69.circ.txt` | OK | 32/4/114/19 | T04 | new | certified | 1231 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkH1-s3-mix19-k1-a32-ad4-g115-gd19-85f4fe7b83.circ.txt` | OK | 32/4/115/19 | T04 | new | certified | 1231 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkI1-s1-mix19-k1-a32-ad4-g115-gd18-b8154f67b2.circ.txt` | OK | 32/4/115/18 | T04 | new | certified | 1411 | 601.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkI1-s1-mix19-k2-a32-ad4-g114-gd19-6f7a899655.circ.txt` | OK | 32/4/114/19 | T04 | new | certified | 1412 | 602.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkI1-s1-mix19-k2-a32-ad4-g115-gd19-78ab830b2a.circ.txt` | OK | 32/4/115/19 | T04 | new | certified | 1412 | 602.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkI1-s2-trb19-k1-a32-ad4-g114-gd19-2f2b76004a.circ.txt` | OK | 32/4/114/19 | T04 | new | certified | 1421 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode trb, caps A32 AD4 GD19, k |
| P3 | `p3-rkI1-s2-trb19-k1-a32-ad4-g115-gd19-8f7b7784fd.circ.txt` | OK | 32/4/115/19 | T04 | new | certified | 1421 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode trb, caps A32 AD4 GD19, k |
| P3 | `p3-rkI1-s2-trb19-k2-a32-ad4-g114-gd19-3905bb10d8.circ.txt` | OK | 32/4/114/19 | T04 | new | certified | 1422 | 601.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode trb, caps A32 AD4 GD19, k |
| P3 | `p3-rkI2-s1-mix20-k1-a32-ad4-g114-gd19-02a1811220.circ.txt` | OK | 32/4/114/19 | T04 | new | certified | 1511 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD20, k |
| P3 | `p3-rkI2-s2-mix19-k1-a32-ad4-g114-gd19-4989701195.circ.txt` | OK | 32/4/114/19 | T04 | new | certified | 1521 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkI2-s2-mix19-k2-a32-ad4-g114-gd19-4dabf1a701.circ.txt` | OK | 32/4/114/19 | T04 | new | certified | 1522 | 601.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkI2-s2-mix19-k2-a32-ad4-g115-gd19-d4730050d6.circ.txt` | OK | 32/4/115/19 | T04 | new | certified | 1522 | 601.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkI2-s2-mix19-k2-a32-ad4-g116-gd18-4c14207d12.circ.txt` | OK | 32/4/116/18 | T04 | new | certified | 1522 | 601.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkJ1-s1-mix22-k1-a32-ad4-g113-gd21-aa6f3862e2.circ.txt` | OK | 32/4/113/21 | T04 | new | certified | 1611 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD22, k |
| P3 | `p3-rkJ1-s1-mix22-k2-a32-ad4-g113-gd21-a2579b1fc8.circ.txt` | OK | 32/4/113/21 | T04 | new | certified | 1612 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD22, k |
| P3 | `p3-rkJ1-s1-mix22-k2-a32-ad4-g114-gd20-f14c7f9c8b.circ.txt` | OK | 32/4/114/20 | T04 | new | certified | 1612 | 361.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD22, k |
| P3 | `p3-rkJ1-s2-mix21-k1-a32-ad4-g113-gd20-ac258dcf0e.circ.txt` | OK | 32/4/113/20 | T04 | new | certified | 1621 | 362.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkJ1-s2-mix21-k2-a32-ad4-g113-gd20-af64e9cefd.circ.txt` | OK | 32/4/113/20 | T04 | new | certified | 1622 | 362.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, k |
| P3 | `p3-rkJ2-s1-mix19-k3-a32-ad4-g114-gd19-c2e143d017.circ.txt` | OK | 32/4/114/19 | T04 | new | certified | 1713 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkJ2-s1-mix19-k3-a32-ad4-g116-gd19-6456fcc25a.circ.txt` | OK | 32/4/116/19 | T04 | new | certified | 1713 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkK1-s1-mix18-k2-a32-ad4-g115-gd18-470095b8a5.circ.txt` | OK | 32/4/115/18 | T04 | new | certified | 1812 | 601.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD18, k |
| P3 | `p3-rkK1-s1-mix18-k2-a32-ad4-g116-gd18-05ce2bcafc.circ.txt` | OK | 32/4/116/18 | T04 | new | certified | 1812 | 601.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD18, k |
| P3 | `p3-rkK1-s1-mix18-k2-a32-ad4-g117-gd18-918956ebb8.circ.txt` | OK | 32/4/117/18 | T04 | new | certified | 1812 | 601.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD18, k |
| P3 | `p3-rkK2-s1-mix18-k1-a32-ad4-g116-gd18-b4bdf1d774.circ.txt` | OK | 32/4/116/18 | T04 | new | certified | 1911 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD18, k |
| P3 | `p3-rkK2-s1-mix18-k2-a32-ad4-g115-gd18-6e4a77b404.circ.txt` | OK | 32/4/115/18 | T04 | new | certified | 1912 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD18, k |
| P3 | `p3-rkK2-s1-mix18-k2-a32-ad4-g116-gd18-821f00754b.circ.txt` | OK | 32/4/116/18 | T04 | new | certified | 1912 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD18, k |
| P3 | `p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt` | OK | 32/4/117/17 | T04 | new | certified | 2212 | 600.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD17, k |
| P3 | `p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt` | OK | 32/4/120/16 | T04 | new | certified | 2222 | None | pdrive mode from command.txt, repair_keep 1, kernel bfx-4dc199db (run Pareto set |
| P3 | `p3-rkN2-s1-mix19-k1-a32-ad4-g114-gd19-74db6afcdf.circ.txt` | OK | 32/4/114/19 | T04 | new | certified | 2311 | 900.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkN2-s1-mix19-k1-a32-ad4-g115-gd19-5c6820258d.circ.txt` | OK | 32/4/115/19 | T04 | new | certified | 2311 | 900.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkN2-s1-mix19-k2-a32-ad4-g114-gd19-152d87bee9.circ.txt` | OK | 32/4/114/19 | T04 | new | certified | 2312 | 900.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkN2-s1-mix19-k3-a32-ad4-g114-gd19-9402c8bbdb.circ.txt` | OK | 32/4/114/19 | T04 | new | certified | 2313 | 900.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P3 | `p3-rkN2-s1-mix19-k3-a32-ad4-g116-gd19-17cd03da14.circ.txt` | OK | 32/4/116/19 | T04 | new | certified | 2313 | 900.0 | pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD19, k |
| P4 | `p4-conj236-a32-ad7-g104-gd28.circ.txt` | OK | 32/7/104/28 | T05 | new | certified | 236 | 602.0 | GF(2^8) conjugate lam 236 k 0 of NIST 103 (P3 mkconj.py: BP top + trb), then pdr |
| P4 | `p4-deep236-a32-ad7-g104-gd27.circ.txt` | OK | 32/7/104/27 | T05 | new | certified | 2363 | <= 600 (saved from the running stage pareto/ at 18:49 UTC; lineage total ~2,400 s) | lineage: conjugate lam 236 of NIST 103 (mkconj) -> pdrive gate cap32 -> trb cap3 |
| P5 | `p5-ad4rep-111-c24-s1-a32-ad4-g112-gd22-db1394c64b.circ.txt` | OK | 32/4/112/22 | T05 | new | certified | 701 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-111-c24-s1-a32-ad4-g112-gd23-f419cd7d01.circ.txt` | OK | 32/4/112/23 | T05 | new | certified | 701 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-111-c24-s1-a32-ad4-g112-gd24-92aa29b493.circ.txt` | OK | 32/4/112/24 | T05 | new | certified | 701 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-111-c24-s2-a32-ad4-g112-gd22-e9aef8c1c8.circ.txt` | OK | 32/4/112/22 | T05 | new | certified | 702 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-111-c24-s2-a32-ad4-g112-gd23-af556a21af.circ.txt` | OK | 32/4/112/23 | T05 | new | certified | 702 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-111-c24-s3-a32-ad4-g112-gd23-e40775065a.circ.txt` | OK | 32/4/112/23 | T05 | new | certified | 703 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-111-c24-s3-a32-ad4-g112-gd24-90adf25722.circ.txt` | OK | 32/4/112/24 | T05 | new | certified | 703 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-111-c24-s4-a32-ad4-g113-gd21-92dd4b99a3.circ.txt` | OK | 32/4/113/21 | T05 | new | certified | 704 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-111-c24-s4-a32-ad4-g113-gd22-019c3ed87b.circ.txt` | OK | 32/4/113/22 | T05 | new | certified | 704 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-111-c24-s5-a32-ad4-g112-gd22-2af2254f9b.circ.txt` | OK | 32/4/112/22 | T05 | new | certified | 705 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad4rep-112-g32-s1-a32-ad4-g111-gd26-74604ea2c6.circ.txt` | OK | 32/4/111/26 | T05 | new | certified | 801 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad4rep-112-g32-s1-a32-ad4-g111-gd27-e32dbde99e.circ.txt` | OK | 32/4/111/27 | T05 | new | certified | 801 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad4rep-112-g32-s2-a32-ad4-g111-gd26-67fd53ccb7.circ.txt` | OK | 32/4/111/26 | T05 | new | certified | 802 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad4rep-112-g32-s2-a32-ad4-g111-gd30-cb4d8cf4e2.circ.txt` | OK | 32/4/111/30 | T05 | new | certified | 802 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad4rep-112-g32-s3-a32-ad4-g111-gd26-a4d6a2dde1.circ.txt` | OK | 32/4/111/26 | T05 | new | certified | 803 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad4rep-112-g32-s4-a32-ad4-g111-gd26-9b6a27c5d9.circ.txt` | OK | 32/4/111/26 | T05 | new | certified | 804 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad4rep-112-g32-s4-a32-ad4-g111-gd28-27b136ee8c.circ.txt` | OK | 32/4/111/28 | T05 | new | certified | 804 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad4rep-112-g32-s5-a32-ad4-g111-gd26-60baa8d4ac.circ.txt` | OK | 32/4/111/26 | T05 | new | certified | 805 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad5g-106-g30-s1-a32-ad5-g105-gd28-2996504ded.circ.txt` | OK | 32/5/105/28 | T05 | reproduced | certified | 901 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad5g-106-g30-s1-a32-ad5-g106-gd26-43cb5a4711.circ.txt` | OK | 32/5/106/26 | T05 | reproduced | certified | 901 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad5g-106-g30-s2-a32-ad5-g105-gd29-d57da9ed36.circ.txt` | OK | 32/5/105/29 | T05 | new | certified | 902 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad5g-106-g30-s3-a32-ad5-g105-gd28-19c1107b17.circ.txt` | OK | 32/5/105/28 | T05 | reproduced | certified | 903 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad5g-106-g30-s4-a32-ad5-g105-gd28-192a683986.circ.txt` | OK | 32/5/105/28 | T05 | reproduced | certified | 904 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-ad5rep-a104-c28-s1-a32-ad5-g106-gd26-f8ef5abee4.circ.txt` | OK | 32/5/106/26 | T05 | reproduced | unknown | 601 | 400 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad5rep-a104-c28-s1-a32-ad5-g106-gd27-b303a86653.circ.txt` | OK | 32/5/106/27 | T05 | reproduced | unknown | 601 | 400 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad5rep-a104-c28-s1-a32-ad5-g108-gd25-fc27686f21.circ.txt` | OK | 32/5/108/25 | T05 | new | unknown | 601 | 400 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-ad5rep-n104-c29-s1-a32-ad5-g106-gd26-8fedacd93f.circ.txt` | OK | 32/5/106/26 | T05 | reproduced | certified | 501 | 400 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp-ad5-104-29-cj188k0-g36-a32-ad5-g108-gd25-c10c60fc9a.circ.txt` | OK | 32/5/108/25 | T05 | new | unknown | 1 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp-ad5-104-29-cj188k0-g36-a32-ad5-g108-gd26-17187178f9.circ.txt` | OK | 32/5/108/26 | T05 | new | unknown | 1 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp-ad5-104-29-cj188k0-g36-a32-ad5-g108-gd27-47c7848099.circ.txt` | OK | 32/5/108/27 | T05 | reproduced | unknown | 1 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp-ad5-104-29-cj9k4-g36-a32-ad5-g108-gd23-a18ff2ca94.circ.txt` | OK | 32/5/108/23 | T05 | reproduced | unknown | 1 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp-ad5-104-29-cj9k4-g36-a32-ad5-g108-gd25-2c4cedb698.circ.txt` | OK | 32/5/108/25 | T05 | new | unknown | 1 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp-ad5-104-29-cj9k4-m30-a32-ad5-g106-gd24-087ba23f48.circ.txt` | OK | 32/5/106/24 | T05 | reproduced | unknown | 2 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp-ad5-104-29-cj9k4-m30-a32-ad5-g106-gd26-092af29b76.circ.txt` | OK | 32/5/106/26 | T05 | reproduced | unknown | 2 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp-ad5-104-29-cj9k4-m30-a32-ad5-g107-gd26-a7eb465962.circ.txt` | OK | 32/5/107/26 | T05 | new | unknown | 2 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp-ad5-104-29-cj9k4-m30-a32-ad5-g107-gd27-9bbc42a682.circ.txt` | OK | 32/5/107/27 | T05 | new | unknown | 2 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp4-ad4-111-25-cert-id-m26-a32-ad4-g112-gd24-6e09c4e4d6.circ.txt` | OK | 32/4/112/24 | T05 | new | certified | 2 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp4-ad4-111-25-cert-l2k0-g30-a32-ad4-g116-gd24-bc59f0cf8f.circ.txt` | OK | 32/4/116/24 | T05 | new | certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-111-25-cert-l2k0-g30-a32-ad4-g116-gd25-1d33ad63c5.circ.txt` | OK | 32/4/116/25 | T05 | reproduced | certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-111-25-cert-l2k0-g30-a32-ad4-g116-gd26-31f4b1915f.circ.txt` | OK | 32/4/116/26 | T05 | new | certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-113-20-p3-id-g30-a32-ad4-g112-gd24-1b0490fa03.circ.txt` | OK | 32/4/112/24 | T05 | new | not certified | 1 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-113-20-p3-id-g30-a32-ad4-g112-gd25-d2e2ab17a6.circ.txt` | OK | 32/4/112/25 | T05 | new | not certified | 1 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-113-20-p3-id-m26-a32-ad4-g113-gd23-05a04c3e3d.circ.txt` | OK | 32/4/113/23 | T05 | new | not certified | 2 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp4-ad4-113-20-p3-l167k1-g30-a32-ad4-g116-gd27-d1003c3369.circ.txt` | OK | 32/4/116/27 | T05 | reproduced | not certified | 1 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-113-20-p3-l167k1-g30-a32-ad4-g117-gd24-1a6caf356f.circ.txt` | OK | 32/4/117/24 | T05 | new | not certified | 1 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-113-20-p3-l2k0-g30-a32-ad4-g115-gd26-d5cd3afa3c.circ.txt` | OK | 32/4/115/26 | T05 | reproduced | not certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-113-20-p3-l2k0-g30-a32-ad4-g116-gd22-d198dea982.circ.txt` | OK | 32/4/116/22 | T05 | new | not certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-113-20-p3-l2k0-g30-a32-ad4-g117-gd24-32e79e55c6.circ.txt` | OK | 32/4/117/24 | T05 | new | not certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-ad4-113-20-p3-l2k0-m26-a32-ad4-g115-gd24-12d6ebc4b1.circ.txt` | OK | 32/4/115/24 | T05 | reproduced | not certified | 2 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp4-nist117-id-g30-a32-ad4-g115-gd26-39ad486bf9.circ.txt` | OK | 32/4/115/26 | T05 | reproduced | certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-nist117-id-g30-a32-ad4-g116-gd26-89efb38a5b.circ.txt` | OK | 32/4/116/26 | T05 | new | certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-nist117-id-m26-a32-ad4-g119-gd23-ccd1334960.circ.txt` | OK | 32/4/119/23 | T05 | new | certified | 2 | 404 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp4-nist117-l188k0-g30-a32-ad4-g115-gd23-308b85bc8d.circ.txt` | OK | 32/4/115/23 | T05 | reproduced | certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-nist117-l188k0-g30-a32-ad4-g115-gd27-e3ccddeaf0.circ.txt` | OK | 32/4/115/27 | T05 | reproduced | certified | 1 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-nist117-l188k0-m26-a32-ad4-g113-gd23-ee6e6b7da3.circ.txt` | OK | 32/4/113/23 | T05 | new | certified | 2 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp4-nist117-l188k0-m26-a32-ad4-g115-gd23-ae2d82fe1b.circ.txt` | OK | 32/4/115/23 | T05 | reproduced | certified | 2 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-cp4-nist117-l9k4-g30-a32-ad4-g118-gd23-ab456275fa.circ.txt` | OK | 32/4/118/23 | T05 | new | certified | 1 | 304 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-cp4-nist117-l9k4-g30-a32-ad4-g118-gd27-3b6c8f5b3b.circ.txt` | OK | 32/4/118/27 | T05 | reproduced | certified | 1 | 304 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-ad4-113-20-p3-r1-gate30-a32-ad4-g112-gd24-23cedca220.circ.txt` | OK | 32/4/112/24 | T05 | new | not certified | 11 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-ad4-113-20-p3-r2-gate30-a32-ad4-g111-gd25-8a6a18f6c7.circ.txt` | OK | 32/4/111/25 | T05 | new | not certified | 13 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt` | OK | 32/4/111/25 | T05 | new | certified | 91 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-cert112c-r1-gate26-a32-ad4-g111-gd26-99fb8b899e.circ.txt` | OK | 32/4/111/26 | T05 | new | certified | 51 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-cert112c-r1-mix22-a32-ad4-g112-gd22-125223cf3b.circ.txt` | OK | 32/4/112/22 | T05 | new | certified | 52 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-cert112c-r2-gate26-a32-ad4-g112-gd22-c9585d7a3f.circ.txt` | OK | 32/4/112/22 | T05 | new | certified | 53 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-cert112c-r2-mix22-a32-ad4-g113-gd20-80065eed92.circ.txt` | OK | 32/4/113/20 | T05 | new | certified | 54 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-cert112c-r3-mix22-a32-ad4-g113-gd21-7e4ed9b6a3.circ.txt` | OK | 32/4/113/21 | T05 | new | certified | 56 | 402 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-cert113-r1-gate30-a32-ad4-g112-gd25-68cddda33a.circ.txt` | OK | 32/4/112/25 | T05 | new | certified | 31 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-cert113-r1-mix26-a32-ad4-g112-gd22-6f3b39a3e3.circ.txt` | OK | 32/4/112/22 | T05 | new | certified | 32 | 400 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-cert113-r1-mix26-a32-ad4-g112-gd24-dcc732f7d3.circ.txt` | OK | 32/4/112/24 | T05 | new | certified | 32 | 400 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-cert113-r2-gate30-a32-ad4-g111-gd26-162638ccbf.circ.txt` | OK | 32/4/111/26 | T05 | new | certified | 33 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-cert113-r2-gate30-a32-ad4-g112-gd22-f67c50c277.circ.txt` | OK | 32/4/112/22 | T05 | new | certified | 33 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-cert113-r2-mix26-a32-ad4-g111-gd26-05cc8d2448.circ.txt` | OK | 32/4/111/26 | T05 | new | certified | 34 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-cert113-r2-mix26-a32-ad4-g112-gd23-3dc99fae77.circ.txt` | OK | 32/4/112/23 | T05 | new | certified | 34 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-cert113-r3-gate30-a32-ad4-g111-gd25-56b90bc378.circ.txt` | OK | 32/4/111/25 | T05 | new | certified | 35 | 302 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-cert113-r3-mix26-a32-ad4-g113-gd23-55afdd7ee4.circ.txt` | OK | 32/4/113/23 | T05 | new | certified | 36 | 400 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-certB-r1-gate30-a32-ad4-g113-gd25-de634303a1.circ.txt` | OK | 32/4/113/25 | T05 | new | certified | 201 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-certB-r1-gate30-a32-ad4-g114-gd24-2f736d2878.circ.txt` | OK | 32/4/114/24 | T05 | new | certified | 201 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-certB-r1-gate30-a32-ad4-g114-gd25-2105bd71e5.circ.txt` | OK | 32/4/114/25 | T05 | new | certified | 201 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-certB-r1-mix26-a32-ad4-g112-gd23-dd155cc47a.circ.txt` | OK | 32/4/112/23 | T05 | new | certified | 202 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-certB-r2-gate30-a32-ad4-g111-gd25-5b118266a0.circ.txt` | OK | 32/4/111/25 | T05 | new | certified | 203 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-certB-r3-gate30-a32-ad4-g111-gd25-c682c9518b.circ.txt` | OK | 32/4/111/25 | T05 | new | certified | 205 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-certC-r1-mix23-a32-ad4-g112-gd22-40eabf538f.circ.txt` | OK | 32/4/112/22 | T05 | new | certified | 302 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-certC-r2-gate25-a32-ad4-g112-gd22-510475e940.circ.txt` | OK | 32/4/112/22 | T05 | new | certified | 303 | 300 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-n104ad5-r1-gate32-a32-ad5-g104-gd30-377f53491e.circ.txt` | OK | 32/5/104/30 | T05 | reproduced | certified | 71 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-n104ad5-r1-gate32-a32-ad5-g104-gd30-4d499b80a0.circ.txt` | OK | 32/5/104/30 | T05 | reproduced | certified | 71 | 301 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, ca |
| P5 | `p5-lin-n104gd-r1-mix28-a32-ad5-g106-gd27-579c2291f2.circ.txt` | OK | 32/5/106/27 | T05 | reproduced | certified | 402 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P5 | `p5-lin-n104gd-r1-mix28-a32-ad5-g107-gd25-6af94a5574.circ.txt` | OK | 32/5/107/25 | T05 | new | certified | 402 | 401 | p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, cap |
| P6 | `aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt` | OK | 35/3/137/28 | T07 | new | certified | 1512 | 200.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt` | OK | 35/3/138/24 | T07 | new | certified | 20378 | 240.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt` | OK | 35/3/139/23 | T07 | new | certified | 3011 | 200.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g139-gd25-107a7c3b5078.circ.txt` | OK | 35/3/139/25 | T07 | new | certified | 776 | 200.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g140-gd22-ecd3572a7c9b.circ.txt` | OK | 35/3/140/22 | T07 | new | certified | 799 | 200.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt` | OK | 35/3/168/13 | T08 | new | certified | 473407 | 240.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g169-gd13-e0c19be5de66.circ.txt` | OK | 35/3/169/13 | T08 | new | certified | 623400 | 240.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g170-gd13-b418123e66e8.circ.txt` | OK | 35/3/170/13 | T08 | new | certified | 2303 | 150.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g171-gd13-462cb948a761.circ.txt` | OK | 35/3/171/13 | T08 | new | certified | 508711 | 240.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g172-gd13-ad319b23b367.circ.txt` | OK | 35/3/172/13 | T08 | new | certified | 77 | 56.0 | gate kernel hub.ops._kernel (kern.py) caps A35 AD3 GD13, cost,gd, 120 s, from ou |
| P6 | `aes-sbox-a35-ad3-g175-gd13-9266803dcdb9.circ.txt` | OK | 35/3/175/13 | T08 | new | certified | pullrun 131, kernel seed 733133 | 300.0 | P6 depth pull: parent 35/3/162/14 (best-1400) -> level-3 class re-basing (botbas |
| P6 | `aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt` | OK | 35/3/181/12 | T08 | new | certified | 397181 | 240.0 | P6 depth pull: 177@13 -> GF(4) one-point coordinate move (T3 gf4build keep2, poi |
| P6 | `aes-sbox-a35-ad3-g187-gd12-b9da0aa0d74b.circ.txt` | OK | 35/3/187/12 | T08 | new | certified | 228749 | 240.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g188-gd12-6fec90a391dc.circ.txt` | OK | 35/3/188/12 | T08 | new | certified | 91543 | 240.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g189-gd12-cb8301fe7b08.circ.txt` | OK | 35/3/189/12 | T08 | new | certified | 91543 | 240.0 | P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel |
| P6 | `aes-sbox-a35-ad3-g200-gd12-257dddf4b764.circ.txt` | OK | 35/3/200/12 | T08 | new | certified | 21 | 105.0 | P6 rebase+fresh build (246@12) then gate kernel hub.ops._kernel via kern.py, cap |
| P6 | `aes-sbox-a35-ad3-g246-gd12-b9fc15540ac5.circ.txt` | OK | 35/3/246/12 | T08 | new | certified | 1 | 3.0 | P6 rebase: level-3 class re-basing (botbasis.py, max output Kraft 1.0 at cap 12) |
| P7 | `p7-t09-a39-ad4-g137-gd12-pol-LE-aes-nist-hub-pw3-s9004.circ.txt` | OK | 39/4/137/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 9004 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a39-ad4-g137-gd12-pol-LE-aes-sbox-a45-pw3-s9002.circ.txt` | OK | 39/4/137/12 | T09 | new | certified | 9002 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a39-ad4-g138-gd12-build-LC-aes-sbox-a45-pw0-s7001-r2.circ.txt` | OK | 39/4/138/12 | T09 | new | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py --refine2 (pairwise joint re-decomposition) fr |
| P7 | `p7-t09-a39-ad4-g138-gd12-build-LC-aes-sbox-a45-pw0-s7001.circ.txt` | OK | 39/4/138/12 | T09 | new | certified | 7001 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a39-ad4-g138-gd12-build-LE-aes-sbox-a45-pw3-s9002.circ.txt` | OK | 39/4/138/12 | T09 | new | certified | 9002 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a39-ad4-g138-gd12-pol-LA-aes-nist-hub-pw3-s1010.circ.txt` | OK | 39/4/138/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 1010 | 301.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a39-ad4-g138-gd12-pol-LC-aes-sbox-a45-pw3-s7008.circ.txt` | OK | 39/4/138/12 | T09 | new | certified | 7008 | 301.8 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a39-ad4-g139-gd12-build-LC-aes-sbox-a45-pw3-s7008.circ.txt` | OK | 39/4/139/12 | T09 | new | certified | 7008 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a39-ad4-g139-gd12-polgate-a39-minp48-pw4-s1.circ.txt` | OK | 39/4/139/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 5 | 501.8 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a39-ad4-g140-gd12-build-LE-aes-nist-hub-pw3-s9004.circ.txt` | OK | 39/4/140/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 9004 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a39-ad4-g140-gd12-pol-LA-aes-nist-hub-pw3-s1004.circ.txt` | OK | 39/4/140/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 1004 | 301.0 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a39-ad4-g140-gd12-pol-LE-aes-sbox-a45-pw0-s9007.circ.txt` | OK | 39/4/140/12 | T09 | new | certified | 9007 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a39-ad4-g141-gd12-build-LA-aes-nist-hub-pw3-s1010.circ.txt` | OK | 39/4/141/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 1010 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a39-ad4-g141-gd12-build-minp48-pw4-s1.circ.txt` | OK | 39/4/141/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a39-ad4-g141-gd12-polgate-a39-minp48-pw4-s2.circ.txt` | OK | 39/4/141/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 5 | 501.9 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a39-ad4-g142-gd12-build-LC-aes-nist-hub-pw3-s7010.circ.txt` | OK | 39/4/142/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 7010 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a39-ad4-g142-gd12-build-LE-aes-sbox-a45-pw0-s9007.circ.txt` | OK | 39/4/142/12 | T09 | new | certified | 9007 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a39-ad4-g142-gd12-build-minp48-pw4-s2.circ.txt` | OK | 39/4/142/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a39-ad4-g142-gd12-pol-LE-aes-nist-hub-pw3-s9022.circ.txt` | OK | 39/4/142/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 9022 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a39-ad4-g143-gd12-build-LE-aes-nist-hub-pw3-s9022.circ.txt` | OK | 39/4/143/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 9022 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a39-ad4-g143-gd12-build-minp48-pw2-s1.circ.txt` | OK | 39/4/143/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a39-ad4-g143-gd12-build-minp48-pw4-s3.circ.txt` | OK | 39/4/143/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3 | 0.0 | {'engine': 'strategies/P7/bopt.py --pw 4 + bbuild.py', 'plan': '/home/joebachir2 |
| P7 | `p7-t09-a39-ad4-g143-gd12-pol-LE-aes-nist-hub-pw3-s9016.circ.txt` | OK | 39/4/143/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 9016 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a39-ad4-g144-gd12-build-LA-aes-nist-hub-pw3-s1004.circ.txt` | OK | 39/4/144/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 1004 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a39-ad4-g144-gd12-build-LE-aes-nist-hub-pw3-s9016.circ.txt` | OK | 39/4/144/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 9016 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g137-gd12-pol-LD-aes-nist-hub-pw3-s3028.circ.txt` | OK | 40/4/137/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3028 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a40-ad4-g138-gd12-build-LD-p7-t09-a42-a-pw0-s3023.circ.txt` | OK | 40/4/138/12 | T09 | new | certified | 3023 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g139-gd12-build-LD-aes-sbox-a45-pw3-s3002.circ.txt` | OK | 40/4/139/12 | T09 | new | certified | 3002 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g139-gd12-build-minp-pw3-s3.circ.txt` | OK | 40/4/139/12 | T09 | new | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a40-ad4-g139-gd12-build-t45-s60-ref.circ.txt` | OK | 40/4/139/12 | T09 | new | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a40-ad4-g139-gd12-pol-LC-aes-nist-hub-pw3-s7004.circ.txt` | OK | 40/4/139/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 7004 | 300.6 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a40-ad4-g139-gd12-pol-LD-aes-nist-hub-pw0-s3021.circ.txt` | OK | 40/4/139/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3021 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a40-ad4-g140-gd12-pol-LD-aes-nist-hub-pw3-s3022.circ.txt` | OK | 40/4/140/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3022 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a40-ad4-g140-gd12-pol-LD-p7-t09-a42-a-pw3-s3012.circ.txt` | OK | 40/4/140/12 | T09 | new | certified | 3012 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a40-ad4-g140-gd12-pol-LD-p7-t09-a42-a-pw3-s3018.circ.txt` | OK | 40/4/140/12 | T09 | new | certified | 3018 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a40-ad4-g140-gd12-pol-LE-aes-nist-hub-pw0-s9015.circ.txt` | OK | 40/4/140/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 9015 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a40-ad4-g141-gd12-build-LC-aes-nist-hub-pw3-s7004.circ.txt` | OK | 40/4/141/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 7004 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g141-gd12-build-LD-aes-nist-hub-pw0-s3021.circ.txt` | OK | 40/4/141/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3021 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g141-gd12-build-LD-p7-t09-a42-a-pw3-s3012.circ.txt` | OK | 40/4/141/12 | T09 | new | certified | 3012 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g141-gd12-build-LD-p7-t09-a42-a-pw3-s3018.circ.txt` | OK | 40/4/141/12 | T09 | new | certified | 3018 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g141-gd12-build-minp-pw10-s3.circ.txt` | OK | 40/4/141/12 | T09 | new | certified | 3 | 0.0 | {'engine': 'strategies/P7/bopt.py --pw 10 + bbuild.py', 'plan': '/home/joebachir |
| P7 | `p7-t09-a40-ad4-g141-gd12-pol-LD-aes-nist-hub-pw3-s3004.circ.txt` | OK | 40/4/141/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3004 | 300.7 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a40-ad4-g142-gd12-build-LD-aes-nist-hub-pw3-s3004.circ.txt` | OK | 40/4/142/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3004 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g142-gd12-build-LE-aes-nist-hub-pw0-s9015.circ.txt` | OK | 40/4/142/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 9015 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g142-gd12-pol-LD-aes-nist-hub-pw3-s3010.circ.txt` | OK | 40/4/142/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3010 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a40-ad4-g143-gd12-build-LD-aes-nist-hub-pw3-s3022.circ.txt` | OK | 40/4/143/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3022 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g143-gd12-build-LD-aes-nist-hub-pw3-s3028.circ.txt` | OK | 40/4/143/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3028 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g144-gd12-build-LD-aes-nist-hub-pw3-s3010.circ.txt` | OK | 40/4/144/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3010 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a40-ad4-g144-gd12-build-minp48-pw2-s3.circ.txt` | OK | 40/4/144/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3 | 0.0 | {'engine': 'strategies/P7/bopt.py --pw 2 + bbuild.py', 'plan': '/home/joebachir2 |
| P7 | `p7-t09-a41-ad4-g136-gd12-pol-LE-p7-t09-a42-a-pw0-s9005.circ.txt` | OK | 41/4/136/12 | T09 | new | certified | 9005 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g137-gd12-build-LE-p7-t09-a42-a-pw0-s9005.circ.txt` | OK | 41/4/137/12 | T09 | new | certified | 9005 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g137-gd12-pol-LA-p7-t09-a42-a-pw0-s1011.circ.txt` | OK | 41/4/137/12 | T09 | new | certified | 1011 | 301.3 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g137-gd12-pol-LC-aes-sbox-a45-pw3-s7002.circ.txt` | OK | 41/4/137/12 | T09 | new | certified | 7002 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g137-gd12-pol-LD-p7-t09-a42-a-pw3-s3024.circ.txt` | OK | 41/4/137/12 | T09 | new | certified | 3024 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g138-gd12-build-LC-aes-sbox-a45-pw3-s7002.circ.txt` | OK | 41/4/138/12 | T09 | new | certified | 7002 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g138-gd12-build-minp-pw3-s1.circ.txt` | OK | 41/4/138/12 | T09 | new | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a41-ad4-g138-gd12-build-minp-pw3-s2.circ.txt` | OK | 41/4/138/12 | T09 | new | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a41-ad4-g138-gd12-pol-LA-p7-t09-a42-a-pw0-s1005.circ.txt` | OK | 41/4/138/12 | T09 | new | certified | 1005 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g138-gd12-pol-LD-aes-sbox-a45-pw0-s3019.circ.txt` | OK | 41/4/138/12 | T09 | new | certified | 3019 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g138-gd12-pol-LD-aes-sbox-a45-pw3-s3014.circ.txt` | OK | 41/4/138/12 | T09 | new | certified | 3014 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g138-gd12-pol-LE-aes-sbox-a45-pw0-s9013.circ.txt` | OK | 41/4/138/12 | T09 | new | certified | 9013 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g139-gd12-build-LA-p7-t09-a42-a-pw0-s1005.circ.txt` | OK | 41/4/139/12 | T09 | new | certified | 1005 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g139-gd12-build-LC-p7-t09-a42-a-pw3-s7006.circ.txt` | OK | 41/4/139/12 | T09 | new | certified | 7006 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g139-gd12-build-LD-aes-sbox-a45-pw3-s3014.circ.txt` | OK | 41/4/139/12 | T09 | new | certified | 3014 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g139-gd12-build-LD-p7-t09-a42-a-pw3-s3024.circ.txt` | OK | 41/4/139/12 | T09 | new | certified | 3024 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g139-gd12-build-LE-aes-sbox-a45-pw0-s9013.circ.txt` | OK | 41/4/139/12 | T09 | new | certified | 9013 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g139-gd12-pol-LA-p7-t09-a42-a-pw3-s1006.circ.txt` | OK | 41/4/139/12 | T09 | new | certified | 1006 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g139-gd12-pol-LD-aes-nist-hub-pw0-s3003.circ.txt` | OK | 41/4/139/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3003 | 301.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g139-gd12-pol-LD-aes-nist-hub-pw0-s3009.circ.txt` | OK | 41/4/139/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3009 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g139-gd12-pol-LD-aes-sbox-a45-pw3-s3026.circ.txt` | OK | 41/4/139/12 | T09 | new | certified | 3026 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g140-gd12-build-LA-p7-t09-a42-a-pw0-s1011.circ.txt` | OK | 41/4/140/12 | T09 | new | certified | 1011 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g140-gd12-build-LD-aes-nist-hub-pw0-s3009.circ.txt` | OK | 41/4/140/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3009 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g140-gd12-build-LD-p7-t09-a42-a-pw0-s3005.circ.txt` | OK | 41/4/140/12 | T09 | new | certified | 3005 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g140-gd12-build-LD-p7-t09-a42-a-pw0-s3017.circ.txt` | OK | 41/4/140/12 | T09 | new | certified | 3017 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g140-gd12-pol-LD-p7-t09-a42-a-pw3-s3030.circ.txt` | OK | 41/4/140/12 | T09 | new | certified | 3030 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g141-gd12-build-LA-p7-t09-a42-a-pw3-s1006.circ.txt` | OK | 41/4/141/12 | T09 | new | certified | 1006 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g141-gd12-build-LD-aes-nist-hub-pw0-s3003.circ.txt` | OK | 41/4/141/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3003 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g141-gd12-build-LD-aes-sbox-a45-pw0-s3019.circ.txt` | OK | 41/4/141/12 | T09 | new | certified | 3019 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g141-gd12-build-LD-aes-sbox-a45-pw3-s3026.circ.txt` | OK | 41/4/141/12 | T09 | new | certified | 3026 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g141-gd12-build-LD-p7-t09-a42-a-pw3-s3030.circ.txt` | OK | 41/4/141/12 | T09 | new | certified | 3030 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g141-gd12-pol-LA-aes-nist-hub-pw0-s1003.circ.txt` | OK | 41/4/141/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 1003 | 300.9 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g141-gd12-pol-LA-aes-nist-hub-pw0-s1009.circ.txt` | OK | 41/4/141/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 1009 | 301.8 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g141-gd12-pol-LA-aes-sbox-a45-pw3-s1002.circ.txt` | OK | 41/4/141/12 | T09 | new | certified | 1002 | 302.6 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g141-gd12-pol-LC-aes-nist-hub-pw0-s7009.circ.txt` | OK | 41/4/141/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 7009 | 300.7 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g142-gd12-build-LE-p7-t09-a42-a-pw3-s9012.circ.txt` | OK | 41/4/142/12 | T09 | new | certified | 9012 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g142-gd12-pol-LE-p7-t09-a42-a-pw3-s9006.circ.txt` | OK | 41/4/142/12 | T09 | new | certified | 9006 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g143-gd12-build-LA-aes-sbox-a45-pw3-s1002.circ.txt` | OK | 41/4/143/12 | T09 | new | certified | 1002 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g143-gd12-build-LA-aes-sbox-a45-pw3-s1008.circ.txt` | OK | 41/4/143/12 | T09 | new | certified | 1008 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g143-gd12-build-LC-aes-nist-hub-pw0-s7009.circ.txt` | OK | 41/4/143/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 7009 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g143-gd12-build-LE-aes-sbox-a45-pw3-s9020.circ.txt` | OK | 41/4/143/12 | T09 | new | certified | 9020 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g143-gd12-pol-LE-aes-nist-hub-pw3-s9010.circ.txt` | OK | 41/4/143/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 9010 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g144-gd12-build-LA-aes-nist-hub-pw0-s1003.circ.txt` | OK | 41/4/144/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 1003 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g144-gd12-build-LE-aes-nist-hub-pw3-s9010.circ.txt` | OK | 41/4/144/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 9010 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g144-gd12-build-LE-p7-t09-a42-a-pw3-s9006.circ.txt` | OK | 41/4/144/12 | T09 | new | certified | 9006 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g144-gd12-build-minp48-pw2-s2.circ.txt` | OK | 41/4/144/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 2 | 0.0 | {'engine': 'strategies/P7/bopt.py --pw 2 + bbuild.py', 'plan': '/home/joebachir2 |
| P7 | `p7-t09-a41-ad4-g144-gd12-pol-LD-aes-nist-hub-pw3-s3016.circ.txt` | OK | 41/4/144/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3016 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g145-gd12-build-LA-aes-nist-hub-pw0-s1009.circ.txt` | OK | 41/4/145/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 1009 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g145-gd12-build-LD-aes-nist-hub-pw3-s3016.circ.txt` | OK | 41/4/145/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3016 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g145-gd12-build-LE-p7-t09-a42-a-pw3-s9018.circ.txt` | OK | 41/4/145/12 | T09 | new | certified | 9018 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g145-gd12-build-minp-pw10-s1.circ.txt` | OK | 41/4/145/12 | T09 | new | certified | 1 | 0.0 | {'engine': 'strategies/P7/bopt.py --pw 10 + bbuild.py', 'plan': '/home/joebachir |
| P7 | `p7-t09-a41-ad4-g145-gd12-pol-LD-aes-nist-hub-pw0-s3015.circ.txt` | OK | 41/4/145/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3015 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g145-gd12-pol-LE-aes-nist-hub-pw0-s9021.circ.txt` | OK | 41/4/145/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 9021 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a41-ad4-g146-gd12-build-minp-pw10-s2.circ.txt` | OK | 41/4/146/12 | T09 | new | certified | 2 | 0.0 | {'engine': 'strategies/P7/bopt.py --pw 10 + bbuild.py', 'plan': '/home/joebachir |
| P7 | `p7-t09-a41-ad4-g147-gd12-build-LD-aes-nist-hub-pw0-s3015.circ.txt` | OK | 41/4/147/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3015 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a41-ad4-g147-gd12-build-LE-aes-nist-hub-pw0-s9021.circ.txt` | OK | 41/4/147/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 9021 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g137-gd12-pol-LC-aes-sbox-a45-pw3-s7002-r2.circ.txt` | OK | 42/4/137/12 | T09 | new | certified | 9 | 301.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g137-gd12-pol-n45q-s12-r2.circ.txt` | OK | 42/4/137/12 | T09 | new | certified | 9 | 301.5 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g137-gd12-pol-n45q-s12-v3.circ.txt` | OK | 42/4/137/12 | T09 | new | certified | 7 | 400.1 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a42-ad4-g137-gd12-pol-n45q-s12.circ.txt` | OK | 42/4/137/12 | T09 | new | certified | 12 | 303.4 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a42-ad4-g138-gd12-build-n45q-s12-r2.circ.txt` | OK | 42/4/138/12 | T09 | new | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py --refine2 (pairwise joint re-decomposition) fr |
| P7 | `p7-t09-a42-ad4-g138-gd12-build-n45q-s12-v3.circ.txt` | OK | 42/4/138/12 | T09 | new | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py plan + bbuild.py (front-cone reuse only)', 'pl |
| P7 | `p7-t09-a42-ad4-g138-gd12-pol-LC-aes-sbox-a45-pw0-s7007.circ.txt` | OK | 42/4/138/12 | T09 | new | certified | 7007 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g138-gd12-pol-LE-p7-t09-a42-a-pw0-s9017.circ.txt` | OK | 42/4/138/12 | T09 | new | certified | 9017 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g139-gd12-build-LD-aes-sbox-a45-pw0-s3001.circ.txt` | OK | 42/4/139/12 | T09 | new | certified | 3001 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g139-gd12-build-LE-p7-t09-a42-a-pw0-s9011.circ.txt` | OK | 42/4/139/12 | T09 | new | certified | 9011 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g139-gd12-build-LE-p7-t09-a42-a-pw0-s9017.circ.txt` | OK | 42/4/139/12 | T09 | new | certified | 9017 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g139-gd12-pol-LA-aes-sbox-a45-pw0-s1007.circ.txt` | OK | 42/4/139/12 | T09 | new | certified | 1007 | 301.5 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g140-gd12-build-LA-aes-sbox-a45-pw0-s1007.circ.txt` | OK | 42/4/140/12 | T09 | new | certified | 1007 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g140-gd12-build-LC-aes-sbox-a45-pw0-s7007.circ.txt` | OK | 42/4/140/12 | T09 | new | certified | 7007 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g140-gd12-build-LC-aes-sbox-a45-pw3-s7002-r2.circ.txt` | OK | 42/4/140/12 | T09 | new | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py --refine2 (pairwise joint re-decomposition) fr |
| P7 | `p7-t09-a42-ad4-g140-gd12-build-n45-s1-v3.circ.txt` | OK | 42/4/140/12 | T09 | new | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py plan + bbuild.py (front-cone reuse only)', 'pl |
| P7 | `p7-t09-a42-ad4-g140-gd12-build-n45q-s14-v3.circ.txt` | OK | 42/4/140/12 | T09 | new | certified | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py plan + bbuild.py (front-cone reuse only)', 'pl |
| P7 | `p7-t09-a42-ad4-g140-gd12-pol-LD-aes-nist-hub-pw0-s3027.circ.txt` | OK | 42/4/140/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3027 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g140-gd12-pol-LE-aes-sbox-a45-pw0-s9001.circ.txt` | OK | 42/4/140/12 | T09 | new | certified | 9001 | 300.4 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g140-gd12-pol-LE-aes-sbox-a45-pw3-s9014.circ.txt` | OK | 42/4/140/12 | T09 | new | certified | 9014 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g141-gd12-build-LD-aes-nist-hub-pw0-s3027.circ.txt` | OK | 42/4/141/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 3027 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g141-gd12-build-LD-p7-t09-a42-a-pw0-s3011.circ.txt` | OK | 42/4/141/12 | T09 | new | certified | 3011 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g141-gd12-build-LD-p7-t09-a42-a-pw0-s3029.circ.txt` | OK | 42/4/141/12 | T09 | new | certified | 3029 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g141-gd12-build-LE-aes-sbox-a45-pw0-s9001.circ.txt` | OK | 42/4/141/12 | T09 | new | certified | 9001 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g141-gd12-pol-LD-aes-sbox-a45-pw3-s3020.circ.txt` | OK | 42/4/141/12 | T09 | new | certified | 3020 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g141-gd12-pol-LD-p7-t09-a42-a-pw3-s3006.circ.txt` | OK | 42/4/141/12 | T09 | new | certified | 3006 | 300.6 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g141-gd12-pol-LE-aes-nist-hub-pw0-s9003.circ.txt` | OK | 42/4/141/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 9003 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g141-gd12-pol-LE-aes-nist-hub-pw0-s9009.circ.txt` | OK | 42/4/141/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 9009 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g141-gd12-pol-LE-aes-sbox-a45-pw3-s9008.circ.txt` | OK | 42/4/141/12 | T09 | new | certified | 9008 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g142-gd12-build-LC-p7-t09-a42-a-pw0-s7005.circ.txt` | OK | 42/4/142/12 | T09 | new | certified | 7005 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g142-gd12-build-LD-aes-sbox-a45-pw3-s3008.circ.txt` | OK | 42/4/142/12 | T09 | new | certified | 3008 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g142-gd12-build-LD-aes-sbox-a45-pw3-s3020.circ.txt` | OK | 42/4/142/12 | T09 | new | certified | 3020 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g142-gd12-build-LD-p7-t09-a42-a-pw3-s3006.circ.txt` | OK | 42/4/142/12 | T09 | new | certified | 3006 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g142-gd12-build-LE-aes-sbox-a45-pw3-s9008.circ.txt` | OK | 42/4/142/12 | T09 | new | certified | 9008 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g142-gd12-build-LE-aes-sbox-a45-pw3-s9014.circ.txt` | OK | 42/4/142/12 | T09 | new | certified | 9014 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g143-gd12-bopt-n45q-s11.circ.txt` | OK | 42/4/143/12 | T09 | new | certified | 11 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a42-ad4-g143-gd12-bopt-n45q-s12.circ.txt` | OK | 42/4/143/12 | T09 | new | certified | 12 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a42-ad4-g143-gd12-bopt-n45q-s14.circ.txt` | OK | 42/4/143/12 | T09 | new | certified | 14 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a42-ad4-g143-gd12-bopt-n45s1.circ.txt` | OK | 42/4/143/12 | T09 | new | certified | 1 | 60.0 | {'engine': 'strategies/P7/bopt.py (shared rank-1 bottom, simulated annealing, ca |
| P7 | `p7-t09-a42-ad4-g143-gd12-build-LE-aes-nist-hub-pw0-s9003.circ.txt` | OK | 42/4/143/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 9003 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g143-gd12-build-x48-c12-a45-v3.circ.txt` | OK | 42/4/143/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 0 | 0.0 | {'engine': 'strategies/P7/bopt.py plan + bbuild.py (front-cone reuse only)', 'pl |
| P7 | `p7-t09-a42-ad4-g144-gd12-build-LE-aes-nist-hub-pw0-s9009.circ.txt` | OK | 42/4/144/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 9009 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a42-ad4-g146-gd12-pol-LC-aes-nist-hub-pw0-s7003.circ.txt` | OK | 42/4/146/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 7003 | 302.3 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a42-ad4-g148-gd12-build-LC-aes-nist-hub-pw0-s7003.circ.txt` | OK | 42/4/148/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 7003 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a43-ad4-g137-gd12-pol-LD-aes-sbox-a45-pw0-s3007.circ.txt` | OK | 43/4/137/12 | T09 | new | certified | 3007 | 301.0 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a43-ad4-g138-gd12-build-LD-aes-sbox-a45-pw0-s3007.circ.txt` | OK | 43/4/138/12 | T09 | new | certified | 3007 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a43-ad4-g138-gd12-pol-n45-s1-v3.circ.txt` | OK | 43/4/138/12 | T09 | new | certified | 7 | 402.3 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a43-ad4-g139-gd12-bopt-n45s1-polish-snap.circ.txt` | OK | 43/4/139/12 | T09 | new | certified | 1 | 105.0 | {'engine': 'strategies/F/fdrive.py gate mode + kernel bfx-593fa798f5 (snapshot o |
| P7 | `p7-t09-a43-ad4-g139-gd12-pol-n45q-s14-v3.circ.txt` | OK | 43/4/139/12 | T09 | new | certified | 7 | 403.1 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a43-ad4-g139-gd12-pol-n45q-s14.circ.txt` | OK | 43/4/139/12 | T09 | new | certified | 14 | 300.1 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a43-ad4-g139-gd12-t09-bopt-n45s1-g1.circ.txt` | OK | 43/4/139/12 | T09 | new | certified | 1 | 1204.6 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a43-ad4-g140-gd12-build-LA-aes-sbox-a45-pw0-s1001.circ.txt` | OK | 43/4/140/12 | T09 | new | certified | 1001 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a43-ad4-g140-gd12-pol-LD-aes-sbox-a45-pw0-s3025.circ.txt` | OK | 43/4/140/12 | T09 | new | certified | 3025 | 300.1 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a43-ad4-g141-gd12-build-LB-aes-sbox-a45-pw0-s5001.circ.txt` | OK | 43/4/141/12 | T09 | reproduced | certified | 5001 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a43-ad4-g141-gd12-build-LD-aes-sbox-a45-pw0-s3025.circ.txt` | OK | 43/4/141/12 | T09 | reproduced | certified | 3025 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a43-ad4-g141-gd12-build-LE-aes-sbox-a45-pw0-s9019.circ.txt` | OK | 43/4/141/12 | T09 | reproduced | certified | 9019 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a43-ad4-g145-gd12-bopt-n45q-s13.circ.txt` | OK | 43/4/145/12 | T09 | new | certified | 13 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a43-ad4-g145-gd12-pol-LD-aes-sbox-a45-pw0-s3013.circ.txt` | OK | 43/4/145/12 | T09 | new | certified | 3013 | 300.2 | {'engine': 'strategies/P7/fdrive_p7.py + kernel bfx-94a75e2c18', 'mode': 'gate', |
| P7 | `p7-t09-a43-ad4-g146-gd12-bopt-n45q-s15.circ.txt` | OK | 43/4/146/12 | T09 | new | certified | 15 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a43-ad4-g148-gd12-bopt-h43q-s21.circ.txt` | OK | 43/4/148/12 | T09 | reproduced | certified | 21 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a43-ad4-g148-gd12-build-LD-aes-sbox-a45-pw0-s3013.circ.txt` | OK | 43/4/148/12 | T09 | reproduced | certified | 3013 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py (pipeline loop)', 'plan': '/home/j |
| P7 | `p7-t09-a44-ad4-g140-gd12-pol-n45q-s11.circ.txt` | OK | 44/4/140/12 | T09 | new | certified | 11 | 301.8 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a44-ad4-g140-gd12-pol-x48-c12-a45-v3.circ.txt` | OK | 44/4/140/12 | T09 | new | certified; construction from a donor outside the limits; all retained states within limits | 7 | 403.0 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| P7 | `p7-t09-a44-ad4-g145-gd12-bopt-n45r-s31.circ.txt` | OK | 44/4/145/12 | T09 | new | certified | 31 | 0.0 | {'engine': 'strategies/P7/bopt.py + bbuild.py', 'plan': '/home/joebachir20/xs-ca |
| P7 | `p7-t09-a45-ad4-g141-gd12-pol-n45q-s13.circ.txt` | OK | 45/4/141/12 | T09 | reproduced | certified | 13 | 300.2 | {'engine': 'strategies/F/fdrive.py + kernel bfx-593fa798f5', 'mode': 'gate', 'ca |
| Z1 | `z1g13-ctl-ad4a-g1-c8c7227f-s0-a28.circ.txt` | OK | 28/6/591/34 | Z | new | certified | none (deterministic exhaustive search) | 29 | {'engine': 'H2 gen13 exact dense-subspace search (real model) via Z1 g13case.sh' |
| Z1 | `z1g13-ctl-ad4a-g1-c8c7227f-s1-a28.circ.txt` | OK | 28/6/585/33 | Z | new | certified | none (deterministic exhaustive search) | 29 | {'engine': 'H2 gen13 exact dense-subspace search (real model) via Z1 g13case.sh' |
| Z1 | `z1g13-ctl-s9m6-semi-g1-c8c7227f-s0-a28.circ.txt` | OK | 28/4/528/27 | Z | new | certified | none (deterministic exhaustive search) | 1002 | {'engine': 'H2 gen13 exact dense-subspace search (real model) via Z1 g13case.sh' |
| Z1 | `z1g13-m6-131-g1-c8c7227f-s0-a28.circ.txt` | OK | 28/4/541/26 | Z | new | certified | none (deterministic exhaustive search) | 5 | {'engine': 'H2 gen13 exact dense-subspace search (real model) via Z1 g13case.sh' |
| Z1 | `z1g13-pa-g7-bc60c06b-s0-a28.circ.txt` | OK | 28/5/551/31 | Z | new | certified | none (deterministic exhaustive search) | 4 | {'engine': 'H2 gen13 exact dense-subspace search (real model) via Z1 g13case.sh' |
| Z1 | `z1g13-pa-g7-bc60c06b-s1-a28.circ.txt` | OK | 28/5/563/29 | Z | new | certified | none (deterministic exhaustive search) | 4 | {'engine': 'H2 gen13 exact dense-subspace search (real model) via Z1 g13case.sh' |
| Z1 | `z1g13-pb-g7-848cb620-s0-a28.circ.txt` | OK | 28/5/622/29 | Z | new | certified | none (deterministic exhaustive search) | 4 | {'engine': 'H2 gen13 exact dense-subspace search (real model) via Z1 g13case.sh' |
| Z1 | `z1g13-pb-g7-848cb620-s1-a28.circ.txt` | OK | 28/5/593/31 | Z | new | certified | none (deterministic exhaustive search) | 4 | {'engine': 'H2 gen13 exact dense-subspace search (real model) via Z1 g13case.sh' |
