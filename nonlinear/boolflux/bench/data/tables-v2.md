434 runs, 0 with errors, 419 verified

## Linear maps: XORFlux v8 vs XOR-only BoolFlux (same start, same CPU, 120 s each)

Target = the repository's best known circuit at that cap (XORFlux records, hours of search).

Memory: XORFlux = its whole Python process; BoolFlux = C kernel / Python driver (measured from v3 on; about 20 MB in the driver, review2 C1), so the whole-tool memory of both is of the same order.

| map | cap | start | tool | final G (median, best, worst) | reach best known | reach best+2 | best-so-far median at 5/15/60/120 s | peak RSS MB (XORFlux: process; BoolFlux: kernel) | start-up s |
|---|---|---|---|---|---|---|---|---|---|
| joltik | 4 | naive | boolflux-v2 | 45, 44, 45 | 2/5, median 56.3 s | 5/5, median 10.9 s | 47/46/45/45 | 2.5 | 0.8 |
| joltik | 4 | naive | xorflux | 45, 45, 46 | 0/5, median - s | 5/5, median 18.9 s | 49/47/46/45 | 27.3 | 1.5 |
| joltik | 4 | nist | boolflux-v2 | 45, 44, 45 | 1/5, median 47.8 s | 5/5, median 0.3 s | 46/45/45/45 | 2.5 | 0.0 |
| joltik | 4 | nist | xorflux | 45, 45, 46 | 0/5, median - s | 5/5, median 3.9 s | 46/45/45/45 | 27.0 | 0.8 |
| joltik | none | naive | boolflux-v2 | 44, 42, 45 | 1/5, median 73.5 s | 3/5, median 6.7 s | 46/45/44/44 | 2.5 | 0.7 |
| joltik | none | naive | xorflux | 42, 42, 44 | 3/5, median 68.0 s | 5/5, median 21.6 s | 46/45/43/42 | 26.9 | 1.5 |
| joltik | none | nist | boolflux-v2 | 44, 43, 44 | 0/5, median - s | 5/5, median 0.0 s | 44/44/44/44 | 2.5 | 0.0 |
| joltik | none | nist | xorflux | 44, 42, 44 | 1/5, median 101.4 s | 5/5, median 0.0 s | 44/44/44/44 | 26.9 | 0.6 |
| klsw17-m-4x4-gf16 | 4 | naive | boolflux-v2 | 36, 36, 36 | 5/5, median 0.4 s | 5/5, median 0.2 s | 36/36/36/36 | 2.5 | 0.7 |
| klsw17-m-4x4-gf16 | 4 | naive | xorflux | 36, 36, 36 | 5/5, median 2.0 s | 5/5, median 1.4 s | 36/36/36/36 | 25.8 | 1.1 |
| klsw17-m-4x4-gf16 | 4 | nist | boolflux-v2 | 36, 36, 36 | 5/5, median 2.3 s | 5/5, median 0.4 s | 36/36/36/36 | 2.5 | 0.0 |
| klsw17-m-4x4-gf16 | 4 | nist | xorflux | 36, 36, 36 | 5/5, median 2.9 s | 5/5, median 0.8 s | 36/36/36/36 | 25.8 | 0.5 |
| klsw17-m-4x4-gf16 | none | naive | boolflux-v2 | 32, 32, 32 | 5/5, median 0.4 s | 5/5, median 0.2 s | 32/32/32/32 | 2.3 | 0.6 |
| klsw17-m-4x4-gf16 | none | naive | xorflux | 32, 32, 32 | 5/5, median 1.4 s | 5/5, median 1.1 s | 32/32/32/32 | 25.8 | 0.9 |
| klsw17-m-4x4-gf16 | none | nist | boolflux-v2 | 32, 32, 32 | 5/5, median 0.3 s | 5/5, median 0.1 s | 32/32/32/32 | 2.5 | 0.0 |
| klsw17-m-4x4-gf16 | none | nist | xorflux | 32, 32, 32 | 5/5, median 0.7 s | 5/5, median 0.2 s | 32/32/32/32 | 25.6 | 0.4 |
| small-scale-aes | 4 | naive | boolflux-v2 | 44, 44, 44 | 5/5, median 43.0 s | 5/5, median 0.6 s | 46/45/44/44 | 2.5 | 0.8 |
| small-scale-aes | 4 | naive | xorflux | 44, 44, 45 | 4/5, median 32.1 s | 5/5, median 5.4 s | 47/45/44/44 | 27.3 | 1.3 |
| small-scale-aes | 4 | nist | boolflux-v2 | 44, 44, 45 | 4/5, median 17.9 s | 5/5, median 0.0 s | 45/45/44/44 | 2.5 | 0.0 |
| small-scale-aes | 4 | nist | xorflux | 44, 44, 45 | 4/5, median 46.3 s | 5/5, median 1.2 s | 46/46/44/44 | 27.0 | 0.6 |
| small-scale-aes | none | naive | boolflux-v2 | 43, 42, 43 | 1/5, median 94.7 s | 5/5, median 5.2 s | 45/44/43/43 | 2.5 | 0.7 |
| small-scale-aes | none | naive | xorflux | 42, 42, 42 | 5/5, median 34.4 s | 5/5, median 4.6 s | 44/43/42/42 | 26.7 | 1.3 |
| small-scale-aes | none | nist | boolflux-v2 | 43, 42, 43 | 2/5, median 50.3 s | 5/5, median 0.0 s | 43/43/43/43 | 2.5 | 0.0 |
| small-scale-aes | none | nist | xorflux | 43, 42, 43 | 2/5, median 64.1 s | 5/5, median 0.0 s | 43/43/43/43 | 26.6 | 0.4 |

## Small nonlinear targets from naive ANF starts (60 s each)

| target | config | runs | target | final cost/G (median, best) | A median | reach target | best-so-far median at checkpoints | overhead s (start, skel, synth) | peak RSS MB kernel / driver |
|---|---|---|---|---|---|---|---|---|---|
| ascon | full v2 | 5 | BGC <= 16 (best published) | 16.0, 16.0 | 5 | 5/5, median 2.0 s | 1s:35.0 / 5s:16.0 / 15s:16.0 / 30s:16.0 / 60s:16.0 | 0.0, 12.0, 0.0 | 2.5 / - (0/5) |
| ascon | gate v2 | 5 | BGC <= 16 (best published) | 16.0, 16.0 | 5 | 5/5, median 0.0 s | 1s:16.0 / 5s:16.0 / 15s:16.0 / 30s:16.0 / 60s:16.0 | 0.0, 0, 0 | 2.5 / - (0/5) |
| ascon | rebuild v2 | 5 | BGC <= 16 (best published) | 16.0, 16.0 | 5 | 5/5, median 0.1 s | 1s:16.0 / 5s:16.0 / 15s:16.0 / 30s:16.0 / 60s:16.0 | 0.0, 0.0, 0.0 | 2.5 / - (0/5) |
| gf16-mul | full v2 | 5 | A <= 9 (bilinear complexity) | 31.0, 31.0 | 10 | 2/5, median 7.0 s | 1s:34.0 / 5s:32.0 / 15s:31.0 / 30s:31.0 / 60s:31.0 | 0.0, 12.0, 0.0 | 2.7 / - (0/5) |
| gf16-mul | gate v2 | 5 | A <= 9 (bilinear complexity) | 29.0, 29.0 | 12 | 0/5, median - s | 1s:31.0 / 5s:31.0 / 15s:30.0 / 30s:30.0 / 60s:29.0 | 0.0, 0, 0 | 2.3 / - (0/5) |
| gf16-mul | rebuild v2 | 5 | A <= 9 (bilinear complexity) | 30.0, 29.0 | 15 | 0/5, median - s | 1s:34.0 / 5s:34.0 / 15s:34.0 / 30s:34.0 / 60s:30.0 | 0.0, 0.0, 0.0 | 2.5 / - (0/5) |
| present | full v2 | 5 | BGC <= 14 (best published) | 14.0, 14.0 | 4 | 5/5, median 2.1 s | 1s:32.0 / 5s:14.0 / 15s:14.0 / 30s:14.0 / 60s:14.0 | 0.0, 12.0, 0.0 | 2.5 / - (0/5) |
| present | gate v2 | 5 | BGC <= 14 (best published) | 14.0, 14.0 | 4 | 5/5, median 0.4 s | 1s:14.0 / 5s:14.0 / 15s:14.0 / 30s:14.0 / 60s:14.0 | 0.0, 0, 0 | 2.5 / - (0/5) |
| present | rebuild v2 | 5 | BGC <= 14 (best published) | 14.0, 14.0 | 4 | 5/5, median 0.2 s | 1s:14.0 / 5s:14.0 / 15s:14.0 / 30s:14.0 / 60s:14.0 | 0.0, 0.0, 0.0 | 2.5 / - (0/5) |
| prince | full v2 | 5 | BGC <= 16 (best published) | 16.0, 16.0 | 7 | 4/5, median 38.8 s | 1s:35.0 / 5s:18.0 / 15s:17.0 / 30s:17.0 / 60s:16.0 | 0.0, 12.0, 0.0 | 2.5 / - (0/5) |
| prince | gate v2 | 5 | BGC <= 16 (best published) | 17.0, 16.0 | 7 | 2/5, median 21.0 s | 1s:19.0 / 5s:18.0 / 15s:17.0 / 30s:17.0 / 60s:17.0 | 0.0, 0, 0 | 2.5 / - (0/5) |
| prince | rebuild v2 | 5 | BGC <= 16 (best published) | 16.0, 16.0 | 7 | 4/5, median 33.2 s | 1s:18.0 / 5s:18.0 / 15s:17.0 / 30s:17.0 / 60s:16.0 | 0.0, 0.0, 0.0 | 2.5 / - (0/5) |
| rectangle | full v2 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 2.0 s | 1s:27.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 12.0, 0.0 | 2.5 / - (0/5) |
| rectangle | gate v2 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 0.0 s | 1s:12.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 0, 0 | 2.5 / - (0/5) |
| rectangle | rebuild v2 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 0.0 s | 1s:12.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 0.0, 0.0 | 2.5 / - (0/5) |

## AES S-box (NIST model)

| target | config | runs | target | final cost/G (median, best) | A median | reach target | best-so-far median at checkpoints | overhead s (start, skel, synth) | peak RSS MB kernel / driver |
|---|---|---|---|---|---|---|---|---|---|
(an unverified run = no circuit within the caps by the end of the budget)

| aes-a36g142 | full v2 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 134.0, 133.0 | 36 | 0/5, median - s | 1s:142.0 / 5s:142.0 / 15s:135.0 / 30s:135.0 / 60s:134.0 / 120s:134.0 | 0.0, 24.0, 0.2 | 3.1 / - (0/5) |
| aes-a36g142 | gate v2 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 134.0, 133.0 | 36 | 0/5, median - s | 1s:140.0 / 5s:136.0 / 15s:135.0 / 30s:134.0 / 60s:134.0 / 120s:134.0 | 0.0, 0, 0 | 3.1 / - (0/5) |
| aes-a36g142 | rebuild v2 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 134.0, 134.0 | 36 | 0/5, median - s | 1s:140.0 / 5s:135.0 / 15s:135.0 / 30s:134.0 / 60s:134.0 / 120s:134.0 | 0.0, 0.0, 0.2 | 3.1 / - (0/5) |
| aes-anf | full v2 | 3 | G <= 600 | 739.0, 732.0 | 214 | 0/3, median - s | 1s:1247.0 / 5s:1247.0 / 15s:1247.0 / 30s:765.0 / 60s:757.0 / 120s:757.0 / 300s:739.0 | 0.0, 60.2, 14.1 | 3.4 / - (0/3) |
| aes-anf | gate v2 | 3 | G <= 600 | 749.0, 741.0 | 288 | 0/3, median - s | 1s:1120.0 / 5s:1054.0 / 15s:944.0 / 30s:885.0 / 60s:821.0 / 120s:788.0 / 300s:749.0 | 0.0, 0, 0 | 3.4 / - (0/3) |
| aes-anf | rebuild v2 | 3 | G <= 600 | 633.0, 630.0 | 223 | 0/3, median - s | 1s:1247.0 / 5s:1247.0 / 15s:676.0 / 30s:672.0 / 60s:665.0 / 120s:653.0 / 300s:633.0 | 0.0, 0.0, 12.9 | 3.4 / - (0/3) |
| aes-g104 | full v2 | 5 | G <= 103 | 104.0, 104.0 | 32 | 0/5, median - s | 1s:104.0 / 5s:104.0 / 15s:104.0 / 30s:104.0 / 60s:104.0 / 120s:104.0 | 0.0, 24.0, 0.2 | 3.3 / - (0/5) |
| aes-g104 | gate v2 | 5 | G <= 103 | 104.0, 104.0 | 32 | 0/5, median - s | 1s:104.0 / 5s:104.0 / 15s:104.0 / 30s:104.0 / 60s:104.0 / 120s:104.0 | 0.0, 0, 0 | 3.3 / - (0/5) |
| aes-g104 | rebuild v2 | 5 | G <= 103 | 104.0, 104.0 | 32 | 0/5, median - s | 1s:104.0 / 5s:104.0 / 15s:104.0 / 30s:104.0 / 60s:104.0 / 120s:104.0 | 0.0, 0.0, 0.2 | 3.3 / - (0/5) |
| aes-gd14repair | full v2 | 5 (5 failed) | GD <= 14 and G <= 126 (below published 127) | - (0/0), - | - (0/0) | 0/5, median - s | 1s:- (0/5) / 5s:- (0/5) / 15s:- (0/5) / 30s:- (0/5) / 60s:- (0/5) / 120s:- (0/5) | 0.0, 24.0, 0.1 | 3.3 / - (0/5) |
| aes-gd14repair | gate v2 | 5 (5 failed) | GD <= 14 and G <= 126 (below published 127) | - (0/0), - | - (0/0) | 0/5, median - s | 1s:- (0/5) / 5s:- (0/5) / 15s:- (0/5) / 30s:- (0/5) / 60s:- (0/5) / 120s:- (0/5) | 0.0, 0, 0 | 3.3 / - (0/5) |
| aes-gd14repair | rebuild v2 | 5 (5 failed) | GD <= 14 and G <= 126 (below published 127) | - (0/0), - | - (0/0) | 0/5, median - s | 1s:- (0/5) / 5s:- (0/5) / 15s:- (0/5) / 30s:- (0/5) / 60s:- (0/5) / 120s:- (0/5) | 0.0, 0.0, 0.2 | 3.3 / - (0/5) |

## Gate-kernel ablations (gate config, one mechanism off)

| target | config | runs | target | final cost/G (median, best) | A median | reach target | best-so-far median at checkpoints | overhead s (start, skel, synth) | peak RSS MB kernel / driver |
|---|---|---|---|---|---|---|---|---|---|
| aes | no-anneal v2 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 134.0, 134.0 | 36 | 0/5, median - s | 1s:137.0 / 5s:136.0 / 15s:135.0 / 30s:134.0 / 60s:134.0 / 120s:134.0 | 0.0, 0, 0 | 2.8 / - (0/5) |
| aes | no-fraig v2 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 133.0, 133.0 | 36 | 0/5, median - s | 1s:139.0 / 5s:136.0 / 15s:135.0 / 30s:134.0 / 60s:133.0 / 120s:133.0 | 0.0, 0, 0 | 3.1 / - (0/5) |
| aes | no-neutral v2 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 136.0, 134.0 | 36 | 0/5, median - s | 1s:142.0 / 5s:141.0 / 15s:138.0 / 30s:138.0 / 60s:136.0 / 120s:136.0 | 0.0, 0, 0 | 3.1 / - (0/5) |
| aes | no-odc v2 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 134.0, 133.0 | 36 | 0/5, median - s | 1s:140.0 / 5s:137.0 / 15s:135.0 / 30s:134.0 / 60s:134.0 / 120s:134.0 | 0.0, 0, 0 | 3.1 / - (0/5) |
| aes | no-restart v2 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 134.0, 134.0 | 36 | 0/5, median - s | 1s:138.0 / 5s:135.0 / 15s:135.0 / 30s:134.0 / 60s:134.0 / 120s:134.0 | 0.0, 0, 0 | 3.1 / - (0/5) |
| aes | no-resub2+3 v2 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 141.0, 141.0 | 36 | 0/5, median - s | 1s:141.0 / 5s:141.0 / 15s:141.0 / 30s:141.0 / 60s:141.0 / 120s:141.0 | 0.0, 0, 0 | 2.8 / - (0/5) |
| aes | no-resub3 v2 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 137.0, 134.0 | 36 | 0/5, median - s | 1s:140.0 / 5s:137.0 / 15s:137.0 / 30s:137.0 / 60s:137.0 / 120s:137.0 | 0.0, 0, 0 | 3.0 / - (0/5) |
| gf16-mul | no-anneal v2 | 5 | A <= 9 (bilinear complexity) | 30.0, 30.0 | 15 | 0/5, median - s | 1s:31.0 / 5s:30.0 / 15s:30.0 / 30s:30.0 / 60s:30.0 | 0.0, 0, 0 | 2.2 / - (0/5) |
| gf16-mul | no-fraig v2 | 5 | A <= 9 (bilinear complexity) | 29.0, 30.0 | 12 | 0/5, median - s | 1s:31.0 / 5s:30.0 / 15s:30.0 / 30s:30.0 / 60s:29.0 | 0.0, 0, 0 | 2.7 / - (0/5) |
| gf16-mul | no-neutral v2 | 5 | A <= 9 (bilinear complexity) | 30.0, 31.0 | 12 | 0/5, median - s | 1s:31.0 / 5s:31.0 / 15s:31.0 / 30s:30.0 / 60s:30.0 | 0.0, 0, 0 | 2.5 / - (0/5) |
| gf16-mul | no-odc v2 | 5 | A <= 9 (bilinear complexity) | 29.0, 30.0 | 12 | 0/5, median - s | 1s:31.0 / 5s:31.0 / 15s:30.0 / 30s:30.0 / 60s:29.0 | 0.0, 0, 0 | 2.5 / - (0/5) |
| gf16-mul | no-restart v2 | 5 | A <= 9 (bilinear complexity) | 30.0, 30.0 | 15 | 0/5, median - s | 1s:31.0 / 5s:31.0 / 15s:31.0 / 30s:30.0 / 60s:30.0 | 0.0, 0, 0 | 2.5 / - (0/5) |
| gf16-mul | no-resub2+3 v2 | 5 | A <= 9 (bilinear complexity) | 34.0, 34.0 | 16 | 0/5, median - s | 1s:34.0 / 5s:34.0 / 15s:34.0 / 30s:34.0 / 60s:34.0 | 0.0, 0, 0 | 2.2 / - (0/5) |
| gf16-mul | no-resub3 v2 | 5 | A <= 9 (bilinear complexity) | 29.0, 29.0 | 12 | 0/5, median - s | 1s:31.0 / 5s:31.0 / 15s:30.0 / 30s:29.0 / 60s:29.0 | 0.0, 0, 0 | 2.5 / - (0/5) |
| present | no-anneal v2 | 5 | BGC <= 14 (best published) | 15.0, 14.0 | 5 | 2/5, median 0.4 s | 1s:15.0 / 5s:15.0 / 15s:15.0 / 30s:15.0 / 60s:15.0 | 0.0, 0, 0 | 2.2 / - (0/5) |
| present | no-fraig v2 | 5 | BGC <= 14 (best published) | 14.0, 14.0 | 4 | 5/5, median 0.6 s | 1s:14.0 / 5s:14.0 / 15s:14.0 / 30s:14.0 / 60s:14.0 | 0.0, 0, 0 | 2.5 / - (0/5) |
| present | no-neutral v2 | 5 | BGC <= 14 (best published) | 14.0, 14.0 | 4 | 5/5, median 0.6 s | 1s:14.0 / 5s:14.0 / 15s:14.0 / 30s:14.0 / 60s:14.0 | 0.0, 0, 0 | 2.5 / - (0/5) |
| present | no-odc v2 | 5 | BGC <= 14 (best published) | 14.0, 14.0 | 4 | 5/5, median 0.5 s | 1s:14.0 / 5s:14.0 / 15s:14.0 / 30s:14.0 / 60s:14.0 | 0.0, 0, 0 | 2.5 / - (0/5) |
| present | no-restart v2 | 5 | BGC <= 14 (best published) | 14.0, 14.0 | 4 | 5/5, median 0.4 s | 1s:14.0 / 5s:14.0 / 15s:14.0 / 30s:14.0 / 60s:14.0 | 0.0, 0, 0 | 2.5 / - (0/5) |
| present | no-resub2+3 v2 | 5 | BGC <= 14 (best published) | 27.0, 23.0 | 9 | 0/5, median - s | 1s:27.0 / 5s:27.0 / 15s:27.0 / 30s:27.0 / 60s:27.0 | 0.0, 0, 0 | 2.2 / - (0/5) |
| present | no-resub3 v2 | 5 | BGC <= 14 (best published) | 14.0, 14.0 | 4 | 5/5, median 0.5 s | 1s:14.0 / 5s:14.0 / 15s:14.0 / 30s:14.0 / 60s:14.0 | 0.0, 0, 0 | 2.5 / - (0/5) |
| rectangle | no-anneal v2 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 4/5, median 0.0 s | 1s:12.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 0, 0 | 2.2 / - (0/5) |
| rectangle | no-fraig v2 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 0.0 s | 1s:12.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 0, 0 | 2.5 / - (0/5) |
| rectangle | no-neutral v2 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 0.0 s | 1s:12.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 0, 0 | 2.3 / - (0/5) |
| rectangle | no-odc v2 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 0.0 s | 1s:12.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 0, 0 | 2.5 / - (0/5) |
| rectangle | no-restart v2 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 0.0 s | 1s:12.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 0, 0 | 2.5 / - (0/5) |
| rectangle | no-resub2+3 v2 | 5 | BGC <= 12 (best published) | 25.0, 21.0 | 8 | 0/5, median - s | 1s:25.0 / 5s:25.0 / 15s:25.0 / 30s:25.0 / 60s:25.0 | 0.0, 0, 0 | 2.2 / - (0/5) |
| rectangle | no-resub3 v2 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 0.0 s | 1s:12.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 0, 0 | 2.5 / - (0/5) |

## Skeleton-level ablations (full config)

| target | config | runs | target | final cost/G (median, best) | A median | reach target | best-so-far median at checkpoints | overhead s (start, skel, synth) | peak RSS MB kernel / driver |
|---|---|---|---|---|---|---|---|---|---|
| aes | no-merge v2 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 134.0, 133.0 | 36 | 0/5, median - s | 1s:142.0 / 5s:142.0 / 15s:135.0 / 30s:134.0 / 60s:134.0 / 120s:134.0 | 0.0, 24.0, 0.2 | 3.1 / - (0/5) |
| aes | seeded-only v2 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 134.0, 133.0 | 36 | 0/5, median - s | 1s:142.0 / 5s:142.0 / 15s:135.0 / 30s:134.0 / 60s:134.0 / 120s:134.0 | 0.0, 24.0, 0.0 | 3.1 / - (0/5) |
| aes | unseeded v2 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 134.0, 132.0 | 36 | 1/5, median 20.2 s | 1s:142.0 / 5s:142.0 / 15s:142.0 / 30s:136.0 / 60s:134.0 / 120s:134.0 | 0.0, 24.0, 0.1 | 3.1 / - (0/5) |
| gf16-mul | no-merge v2 | 5 | A <= 9 (bilinear complexity) | 33.0, 32.0 | 9 | 3/5, median 12.0 s | 1s:34.0 / 5s:31.0 / 15s:32.0 / 30s:33.0 / 60s:33.0 | 0.0, 12.0, 0.0 | 2.7 / - (0/5) |
| gf16-mul | seeded-only v2 | 5 | A <= 9 (bilinear complexity) | 31.0, 31.0 | 9 | 3/5, median 12.0 s | 1s:34.0 / 5s:32.0 / 15s:31.0 / 30s:31.0 / 60s:31.0 | 0.0, 12.0, 0.0 | 2.7 / - (0/5) |
| gf16-mul | unseeded v2 | 5 | A <= 9 (bilinear complexity) | 32.0, 31.0 | 9 | 4/5, median 12.0 s (1: no time) | 1s:34.0 / 5s:32.0 / 15s:31.0 / 30s:31.0 / 60s:31.0 | 0.0, 12.4, 0.0 | 2.7 / - (0/5) |
| rectangle | no-merge v2 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 2.0 s | 1s:27.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 12.0, 0.0 | 2.5 / - (0/5) |
| rectangle | seeded-only v2 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 2.0 s | 1s:27.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 12.0, 0.0 | 2.5 / - (0/5) |
| rectangle | unseeded v2 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 2.0 s | 1s:27.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 12.4, 0.0 | 2.5 / - (0/5) |

