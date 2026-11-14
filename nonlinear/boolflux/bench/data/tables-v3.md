131 runs, 0 with errors, 122 verified

## Linear maps: XORFlux v8 vs XOR-only BoolFlux (same start, same CPU, 120 s each)

Target = the repository's best known circuit at that cap (XORFlux records, hours of search).

Memory: XORFlux = its whole Python process; BoolFlux = C kernel / Python driver (measured from v3 on; about 20 MB in the driver, review2 C1), so the whole-tool memory of both is of the same order.

| map | cap | start | tool | final G (median, best, worst) | reach best known | reach best+2 | best-so-far median at 5/15/60/120 s | peak RSS MB (XORFlux: process; BoolFlux: kernel) | start-up s |
|---|---|---|---|---|---|---|---|---|---|

## Small nonlinear targets from naive ANF starts (60 s each)

| target | config | runs | target | final cost/G (median, best) | A median | reach target | best-so-far median at checkpoints | overhead s (start, skel, synth) | peak RSS MB kernel / driver |
|---|---|---|---|---|---|---|---|---|---|
| ascon | full v3 | 5 | BGC <= 16 (best published) | 16.0, 16.0 | 5 | 5/5, median 2.0 s | 1s:35.0 / 5s:16.0 / 15s:16.0 / 30s:16.0 / 60s:16.0 | 0.0, 7.0, 0.0 | 2.5 / 45.6 |
| ascon | rebuild v3 | 5 | BGC <= 16 (best published) | 16.0, 16.0 | 5 | 5/5, median 0.1 s | 1s:16.0 / 5s:16.0 / 15s:16.0 / 30s:16.0 / 60s:16.0 | 0.0, 0.0, 0.0 | 2.5 / 45.6 |
| gf16-mul | full v3 | 5 | A <= 9 (bilinear complexity) | 32.0, 31.0 | 9 | 3/5, median 11.5 s | 1s:34.0 / 5s:32.0 / 15s:32.0 / 30s:32.0 / 60s:32.0 | 0.0, 7.0, 0.0 | 2.7 / 22.0 |
| gf16-mul | rebuild v3 | 5 | A <= 9 (bilinear complexity) | 30.0, 29.0 | 15 | 0/5, median - s | 1s:34.0 / 5s:34.0 / 15s:34.0 / 30s:34.0 / 60s:30.0 | 0.0, 0.0, 0.0 | 2.5 / 22.0 |
| present | full v3 | 5 | BGC <= 14 (best published) | 14.0, 14.0 | 4 | 5/5, median 2.1 s | 1s:32.0 / 5s:14.0 / 15s:14.0 / 30s:14.0 / 60s:14.0 | 0.0, 7.0, 0.0 | 2.5 / 46.6 |
| present | rebuild v3 | 5 | BGC <= 14 (best published) | 14.0, 14.0 | 4 | 5/5, median 0.2 s | 1s:14.0 / 5s:14.0 / 15s:14.0 / 30s:14.0 / 60s:14.0 | 0.0, 0.0, 0.0 | 2.5 / 46.6 |
| prince | full v3 | 5 | BGC <= 16 (best published) | 17.0, 16.0 | 7 | 1/5, median 29.4 s | 1s:35.0 / 5s:17.0 / 15s:17.0 / 30s:17.0 / 60s:17.0 | 0.0, 7.0, 0.0 | 2.5 / 21.9 |
| prince | rebuild v3 | 5 | BGC <= 16 (best published) | 17.0, 16.0 | 7 | 2/5, median 23.0 s | 1s:18.0 / 5s:18.0 / 15s:18.0 / 30s:17.0 / 60s:17.0 | 0.0, 0.0, 0.0 | 2.5 / 21.9 |
| rectangle | full v3 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 2.0 s | 1s:27.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 7.0, 0.0 | 2.5 / 21.8 |
| rectangle | rebuild v3 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 0.0 s | 1s:12.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 0.0, 0.0 | 2.5 / 21.9 |

## AES S-box (NIST model)

| target | config | runs | target | final cost/G (median, best) | A median | reach target | best-so-far median at checkpoints | overhead s (start, skel, synth) | peak RSS MB kernel / driver |
|---|---|---|---|---|---|---|---|---|---|
(an unverified run = no circuit within the caps by the end of the budget)

| aes-a36g142 | full v3 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 134.0, 133.0 | 36 | 0/5, median - s | 1s:142.0 / 5s:142.0 / 15s:135.0 / 30s:134.0 / 60s:134.0 / 120s:134.0 | 0.0, 11.7, 0.2 | 3.1 / 21.5 |
| aes-a36g142 | rebuild v3 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 134.0, 133.0 | 36 | 0/5, median - s | 1s:138.0 / 5s:135.0 / 15s:135.0 / 30s:134.0 / 60s:134.0 / 120s:134.0 | 0.0, 0.0, 0.2 | 3.1 / 21.6 |
| aes-anf | full v3 | 3 | G <= 600 | 758.0, 742.0 | 217 | 0/3, median - s | 1s:1247.0 / 5s:1247.0 / 15s:1247.0 / 30s:767.0 / 60s:763.0 / 120s:763.0 / 300s:758.0 | 0.0, 35.4, 11.1 | 3.4 / 47.1 |
| aes-anf | rebuild v3 | 3 | G <= 600 | 637.0, 615.0 | 223 | 0/3, median - s | 1s:1247.0 / 5s:1247.0 / 15s:673.0 / 30s:672.0 / 60s:658.0 / 120s:651.0 / 300s:637.0 | 0.0, 0.0, 9.1 | 3.4 / 54.3 |
| aes-g104 | full v3 | 5 | G <= 103 | 104.0, 104.0 | 32 | 0/5, median - s | 1s:104.0 / 5s:104.0 / 15s:104.0 / 30s:104.0 / 60s:104.0 / 120s:104.0 | 0.0, 11.8, 0.2 | 3.3 / 21.7 |
| aes-g104 | rebuild v3 | 5 | G <= 103 | 104.0, 104.0 | 32 | 0/5, median - s | 1s:104.0 / 5s:104.0 / 15s:104.0 / 30s:104.0 / 60s:104.0 / 120s:104.0 | 0.0, 0.0, 0.2 | 3.3 / 21.7 |
| aes-gd14repair | full v3 | 5 (5 failed) | GD <= 14 and G <= 126 (below published 127) | - (0/0), - | - (0/0) | 0/5, median - s | 1s:- (0/5) / 5s:- (0/5) / 15s:- (0/5) / 30s:- (0/5) / 60s:- (0/5) / 120s:- (0/5) | 0.0, 11.4, 0.2 | 3.3 / 21.6 |
| aes-gd14repair | rebuild v3 | 5 (4 failed) | GD <= 14 and G <= 126 (below published 127) | 124.0, 124.0 | 38 | 1/5, median 118.7 s | 1s:- (0/5) / 5s:- (0/5) / 15s:- (0/5) / 30s:- (0/5) / 60s:- (0/5) / 120s:124.0 (1/5) | 0.0, 0.0, 0.2 | 3.3 / 21.7 |

## Gate-kernel ablations (gate config, one mechanism off)

| target | config | runs | target | final cost/G (median, best) | A median | reach target | best-so-far median at checkpoints | overhead s (start, skel, synth) | peak RSS MB kernel / driver |
|---|---|---|---|---|---|---|---|---|---|

## Skeleton-level ablations (full config)

| target | config | runs | target | final cost/G (median, best) | A median | reach target | best-so-far median at checkpoints | overhead s (start, skel, synth) | peak RSS MB kernel / driver |
|---|---|---|---|---|---|---|---|---|---|
| aes | no-merge v3 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 134.0, 133.0 | 36 | 0/5, median - s | 1s:142.0 / 5s:142.0 / 15s:135.0 / 30s:134.0 / 60s:134.0 / 120s:134.0 | 0.0, 11.8, 0.2 | 3.1 / 45.4 |
| aes | seeded-only v3 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 134.0, 133.0 | 36 | 0/5, median - s | 1s:142.0 / 5s:142.0 / 15s:135.0 / 30s:134.0 / 60s:134.0 / 120s:134.0 | 0.0, 11.8, 0.1 | 3.1 / 44.5 |
| aes | unseeded v3 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 134.0, 133.0 | 36 | 0/5, median - s | 1s:142.0 / 5s:142.0 / 15s:135.0 / 30s:134.0 / 60s:134.0 / 120s:134.0 | 0.0, 11.8, 0.1 | 3.1 / 21.9 |
| gf16-mul | no-merge v3 | 5 | A <= 9 (bilinear complexity) | 33.0, 32.0 | 9 | 3/5, median 12.0 s | 1s:34.0 / 5s:34.0 / 15s:33.0 / 30s:33.0 / 60s:33.0 | 0.0, 7.6, 0.0 | 2.7 / 22.1 |
| gf16-mul | seeded-only v3 | 5 | A <= 9 (bilinear complexity) | 31.0, 31.0 | 9 | 3/5, median 12.0 s | 1s:34.0 / 5s:32.0 / 15s:32.0 / 30s:31.0 / 60s:31.0 | 0.0, 6.0, 0.0 | 2.7 / 22.0 |
| gf16-mul | unseeded v3 | 5 | A <= 9 (bilinear complexity) | 31.0, 31.0 | 9 | 3/5, median 7.9 s (1: no time) | 1s:34.0 / 5s:32.0 / 15s:32.0 / 30s:31.0 / 60s:31.0 | 0.0, 7.1, 0.0 | 2.7 / 43.7 |
| rectangle | no-merge v3 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 2.0 s | 1s:27.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 7.0, 0.0 | 2.5 / 22.0 |
| rectangle | seeded-only v3 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 2.0 s | 1s:27.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 7.0, 0.0 | 2.5 / 22.0 |
| rectangle | unseeded v3 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 2.0 s | 1s:27.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 7.0, 0.0 | 2.5 / 43.7 |

