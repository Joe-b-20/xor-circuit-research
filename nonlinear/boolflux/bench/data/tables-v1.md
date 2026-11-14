391 runs, 0 with errors, 382 verified

## Linear maps: XORFlux v8 vs XOR-only BoolFlux (same start, same CPU, 120 s each)

Target = the repository's best known circuit at that cap (XORFlux records, hours of search).

| map | cap | start | tool | final G (median, best, worst) | reach best known | reach best+2 | best-so-far median at 5/15/60/120 s | peak RSS MB | start-up s |
|---|---|---|---|---|---|---|---|---|---|
| joltik | 4 | naive | boolflux-v1 | 45, 44, 47 | 1/5, median 17.1 s | 4/5, median 10.2 s | 47/46/45/45 | 2.5 | 0.9 |
| joltik | 4 | naive | xorflux | 45, 45, 47 | 0/5, median - s | 4/5, median 7.5 s | 48/46/46/45 | 27.0 | 1.4 |
| joltik | 4 | nist | boolflux-v1 | 45, 45, 45 | 0/5, median - s | 5/5, median 0.3 s | 45/45/45/45 | 2.5 | 0.0 |
| joltik | 4 | nist | xorflux | 45, 45, 45 | 0/5, median - s | 5/5, median 4.1 s | 46/46/45/45 | 27.2 | 0.8 |
| joltik | none | naive | boolflux-v1 | 43, 43, 45 | 0/5, median - s | 4/5, median 35.4 s | 47/45/44/43 | 2.5 | 0.9 |
| joltik | none | naive | xorflux | 44, 42, 44 | 1/5, median 44.8 s | 5/5, median 10.0 s | 47/44/44/44 | 26.9 | 1.5 |
| joltik | none | nist | boolflux-v1 | 44, 44, 44 | 0/5, median - s | 5/5, median 0.0 s | 44/44/44/44 | 2.3 | 0.0 |
| joltik | none | nist | xorflux | 43, 42, 44 | 1/5, median 41.5 s | 5/5, median 0.0 s | 44/44/44/43 | 26.6 | 0.6 |
| klsw17-m-4x4-gf16 | 4 | naive | boolflux-v1 | 36, 36, 36 | 5/5, median 1.4 s | 5/5, median 0.5 s | 36/36/36/36 | 2.5 | 1.0 |
| klsw17-m-4x4-gf16 | 4 | naive | xorflux | 36, 36, 36 | 5/5, median 4.2 s | 5/5, median 1.4 s | 36/36/36/36 | 25.8 | 1.5 |
| klsw17-m-4x4-gf16 | 4 | nist | boolflux-v1 | 36, 36, 36 | 5/5, median 1.4 s | 5/5, median 0.5 s | 36/36/36/36 | 2.5 | 0.0 |
| klsw17-m-4x4-gf16 | 4 | nist | xorflux | 36, 36, 36 | 5/5, median 5.3 s | 5/5, median 0.9 s | 37/36/36/36 | 25.8 | 0.7 |
| klsw17-m-4x4-gf16 | none | naive | boolflux-v1 | 32, 32, 32 | 5/5, median 0.7 s | 5/5, median 0.3 s | 32/32/32/32 | 2.5 | 0.9 |
| klsw17-m-4x4-gf16 | none | naive | xorflux | 32, 32, 32 | 5/5, median 2.3 s | 5/5, median 1.6 s | 32/32/32/32 | 25.8 | 1.3 |
| klsw17-m-4x4-gf16 | none | nist | boolflux-v1 | 32, 32, 32 | 5/5, median 0.7 s | 5/5, median 0.1 s | 32/32/32/32 | 2.5 | 0.0 |
| klsw17-m-4x4-gf16 | none | nist | xorflux | 32, 32, 32 | 5/5, median 1.0 s | 5/5, median 0.3 s | 32/32/32/32 | 25.5 | 0.5 |
| small-scale-aes | 4 | naive | boolflux-v1 | 44, 44, 45 | 4/5, median 42.9 s | 5/5, median 1.8 s | 46/46/44/44 | 2.3 | 0.8 |
| small-scale-aes | 4 | naive | xorflux | 44, 44, 45 | 4/5, median 73.9 s | 5/5, median 2.8 s | 46/45/45/44 | 27.0 | 1.5 |
| small-scale-aes | 4 | nist | boolflux-v1 | 44, 44, 45 | 4/5, median 16.8 s | 5/5, median 0.1 s | 45/45/44/44 | 2.5 | 0.0 |
| small-scale-aes | 4 | nist | xorflux | 44, 44, 44 | 5/5, median 77.5 s | 5/5, median 1.9 s | 46/45/45/44 | 27.0 | 0.7 |
| small-scale-aes | none | naive | boolflux-v1 | 43, 42, 43 | 2/5, median 93.5 s | 5/5, median 9.8 s | 45/44/43/43 | 2.5 | 0.8 |
| small-scale-aes | none | naive | xorflux | 43, 42, 43 | 2/5, median 71.8 s | 5/5, median 5.3 s | 45/43/43/43 | 26.7 | 1.4 |
| small-scale-aes | none | nist | boolflux-v1 | 43, 43, 43 | 0/5, median - s | 5/5, median 0.0 s | 43/43/43/43 | 2.5 | 0.0 |
| small-scale-aes | none | nist | xorflux | 42, 42, 43 | 3/5, median 20.7 s | 5/5, median 0.0 s | 43/43/42/42 | 26.2 | 0.5 |

## Small nonlinear targets from naive ANF starts (60 s each)

| target | config | runs | target | final cost/G (median, best) | A median | reach target | best-so-far median at checkpoints | overhead s (start, skel, synth) | peak RSS MB |
|---|---|---|---|---|---|---|---|---|---|
| ascon | full v1 | 5 | BGC <= 16 (best published) | 16.0, 16.0 | 5 | 5/5, median 2.0 s | 1s:35.0 / 5s:16.0 / 15s:16.0 / 30s:16.0 / 60s:16.0 | 0.0, 12.0, 0.0 | 2.5 |
| ascon | gate v1 | 5 | BGC <= 16 (best published) | 16.0, 16.0 | 5 | 5/5, median 0.1 s | 1s:16.0 / 5s:16.0 / 15s:16.0 / 30s:16.0 / 60s:16.0 | 0.0, 0, 0 | 2.5 |
| gf16-mul | full v1 | 5 | A <= 9 (bilinear complexity) | 32.0, 31.0 | 9 | 3/5, median 12.0 s | 1s:34.0 / 5s:34.0 / 15s:31.0 / 30s:31.0 / 60s:31.0 | 0.0, 12.0, 0.0 | 2.5 |
| gf16-mul | gate v1 | 5 | A <= 9 (bilinear complexity) | 29.0, 29.0 | 12 | 0/5, median - s | 1s:31.0 / 5s:31.0 / 15s:31.0 / 30s:30.0 / 60s:29.0 | 0.0, 0, 0 | 2.5 |
| present | full v1 | 5 | BGC <= 14 (best published) | 14.0, 14.0 | 4 | 5/5, median 2.2 s | 1s:32.0 / 5s:14.0 / 15s:14.0 / 30s:14.0 / 60s:14.0 | 0.0, 12.1, 0.0 | 2.5 |
| present | gate v1 | 5 | BGC <= 14 (best published) | 14.0, 14.0 | 4 | 5/5, median 1.5 s | 1s:16.0 / 5s:14.0 / 15s:14.0 / 30s:14.0 / 60s:14.0 | 0.0, 0, 0 | 2.5 |
| prince | full v1 | 5 | BGC <= 16 (best published) | 16.0, 16.0 | 7 | 3/5, median 32.4 s | 1s:35.0 / 5s:18.0 / 15s:17.0 / 30s:17.0 / 60s:16.0 | 0.0, 12.0, 0.0 | 2.5 |
| prince | gate v1 | 5 | BGC <= 16 (best published) | 17.0, 16.0 | 8 | 2/5, median 16.0 s | 1s:19.0 / 5s:19.0 / 15s:18.0 / 30s:17.0 / 60s:17.0 | 0.0, 0, 0 | 2.5 |
| rectangle | full v1 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 2.0 s | 1s:27.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 12.0, 0.0 | 2.5 |
| rectangle | gate v1 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 0.0 s | 1s:12.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 0, 0 | 2.5 |

## AES S-box (NIST model)

| target | config | runs | target | final cost/G (median, best) | A median | reach target | best-so-far median at checkpoints | overhead s (start, skel, synth) | peak RSS MB |
|---|---|---|---|---|---|---|---|---|---|
(an unverified run = no circuit within the caps by the end of the budget)

| aes-a36g142 | full v1 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 134.0, 131.0 | 36 | 1/5, median 39.4 s | 1s:142.0 / 5s:142.0 / 15s:136.0 / 30s:134.0 / 60s:134.0 / 120s:134.0 | 0.0, 24.0, 0.3 | 3.1 |
| aes-a36g142 | gate v1 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 133.0, 131.0 | 36 | 2/5, median 51.8 s | 1s:139.0 / 5s:137.0 / 15s:134.0 / 30s:134.0 / 60s:133.0 / 120s:133.0 | 0.0, 0, 0 | 3.1 |
| aes-anf | full v1 | 3 | G <= 600 | 729.0, 728.0 | 212 | 0/3, median - s | 1s:1247.0 / 5s:1247.0 / 15s:1247.0 / 30s:743.0 / 60s:734.0 / 120s:732.0 / 300s:729.0 | 0.0, 60.2, 24.6 | 3.4 |
| aes-anf | gate v1 | 3 | G <= 600 | 768.0, 756.0 | 291 | 0/3, median - s | 1s:1119.0 / 5s:1060.0 / 15s:957.0 / 30s:904.0 / 60s:851.0 / 120s:796.0 / 300s:768.0 | 0.0, 0, 0 | 3.4 |
| aes-g104 | full v1 | 5 | G <= 103 | 104.0, 104.0 | 32 | 0/5, median - s | 1s:104.0 / 5s:104.0 / 15s:104.0 / 30s:104.0 / 60s:104.0 / 120s:104.0 | 0.0, 24.1, 0.2 | 3.3 |
| aes-g104 | gate v1 | 5 | G <= 103 | 104.0, 103.0 | 32 | 1/5, median 110.4 s | 1s:104.0 / 5s:104.0 / 15s:104.0 / 30s:104.0 / 60s:104.0 / 120s:104.0 | 0.0, 0, 0 | 3.3 |
| aes-gd14repair | full v1 | 5 (5 failed) | GD <= 14 and G <= 126 (below published 127) | -, - | - | 0/5, median - s | 1s:- / 5s:- / 15s:- / 30s:- / 60s:- / 120s:- | 0.0, 24.1, 0.2 | 3.3 |
| aes-gd14repair | gate v1 | 5 (4 failed) | GD <= 14 and G <= 126 (below published 127) | 129.0, 129.0 | 40 | 0/5, median - s | 1s:- / 5s:- / 15s:- / 30s:- / 60s:- / 120s:129.0 | 0.0, 0, 0 | 3.3 |

## Gate-kernel ablations (gate config, one mechanism off)

| target | config | runs | target | final cost/G (median, best) | A median | reach target | best-so-far median at checkpoints | overhead s (start, skel, synth) | peak RSS MB |
|---|---|---|---|---|---|---|---|---|---|
| aes | no-anneal v1 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 134.0, 134.0 | 36 | 0/5, median - s | 1s:139.0 / 5s:136.0 / 15s:134.0 / 30s:134.0 / 60s:134.0 / 120s:134.0 | 0.0, 0, 0 | 2.8 |
| aes | no-fraig v1 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 133.0, 133.0 | 36 | 0/5, median - s | 1s:141.0 / 5s:137.0 / 15s:136.0 / 30s:134.0 / 60s:133.0 / 120s:133.0 | 0.0, 0, 0 | 3.1 |
| aes | no-neutral v1 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 136.0, 134.0 | 36 | 0/5, median - s | 1s:142.0 / 5s:141.0 / 15s:139.0 / 30s:138.0 / 60s:137.0 / 120s:136.0 | 0.0, 0, 0 | 3.1 |
| aes | no-odc v1 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 133.0, 132.0 | 36 | 1/5, median 28.0 s | 1s:140.0 / 5s:136.0 / 15s:135.0 / 30s:133.0 / 60s:133.0 / 120s:133.0 | 0.0, 0, 0 | 3.1 |
| aes | no-restart v1 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 133.0, 131.0 | 36 | 2/5, median 32.4 s | 1s:139.0 / 5s:136.0 / 15s:134.0 / 30s:133.0 / 60s:133.0 / 120s:133.0 | 0.0, 0, 0 | 3.1 |
| aes | no-resub2+3 v1 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 141.0, 141.0 | 36 | 0/5, median - s | 1s:141.0 / 5s:141.0 / 15s:141.0 / 30s:141.0 / 60s:141.0 / 120s:141.0 | 0.0, 0, 0 | 2.8 |
| aes | no-resub3 v1 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 137.0, 135.0 | 36 | 0/5, median - s | 1s:140.0 / 5s:137.0 / 15s:137.0 / 30s:137.0 / 60s:137.0 / 120s:137.0 | 0.0, 0, 0 | 3.1 |
| gf16-mul | no-anneal v1 | 5 | A <= 9 (bilinear complexity) | 30.0, 30.0 | 15 | 0/5, median - s | 1s:31.0 / 5s:30.0 / 15s:30.0 / 30s:30.0 / 60s:30.0 | 0.0, 0, 0 | 2.2 |
| gf16-mul | no-fraig v1 | 5 | A <= 9 (bilinear complexity) | 30.0, 29.0 | 12 | 0/5, median - s | 1s:31.0 / 5s:30.0 / 15s:30.0 / 30s:30.0 / 60s:29.0 | 0.0, 0, 0 | 2.5 |
| gf16-mul | no-neutral v1 | 5 | A <= 9 (bilinear complexity) | 30.0, 29.0 | 12 | 0/5, median - s | 1s:31.0 / 5s:31.0 / 15s:31.0 / 30s:30.0 / 60s:30.0 | 0.0, 0, 0 | 2.7 |
| gf16-mul | no-odc v1 | 5 | A <= 9 (bilinear complexity) | 29.0, 29.0 | 12 | 0/5, median - s | 1s:31.0 / 5s:30.0 / 15s:29.0 / 30s:29.0 / 60s:29.0 | 0.0, 0, 0 | 2.5 |
| gf16-mul | no-restart v1 | 5 | A <= 9 (bilinear complexity) | 30.0, 29.0 | 14 | 0/5, median - s | 1s:31.0 / 5s:31.0 / 15s:30.0 / 30s:30.0 / 60s:30.0 | 0.0, 0, 0 | 2.5 |
| gf16-mul | no-resub2+3 v1 | 5 | A <= 9 (bilinear complexity) | 34.0, 34.0 | 16 | 0/5, median - s | 1s:34.0 / 5s:34.0 / 15s:34.0 / 30s:34.0 / 60s:34.0 | 0.0, 0, 0 | 2.2 |
| gf16-mul | no-resub3 v1 | 5 | A <= 9 (bilinear complexity) | 29.0, 29.0 | 12 | 0/5, median - s | 1s:31.0 / 5s:31.0 / 15s:30.0 / 30s:30.0 / 60s:29.0 | 0.0, 0, 0 | 2.5 |
| present | no-anneal v1 | 5 | BGC <= 14 (best published) | 15.0, 14.0 | 5 | 2/5, median 0.1 s | 1s:19.0 / 5s:15.0 / 15s:15.0 / 30s:15.0 / 60s:15.0 | 0.0, 0, 0 | 2.2 |
| present | no-fraig v1 | 5 | BGC <= 14 (best published) | 14.0, 14.0 | 4 | 5/5, median 0.2 s | 1s:14.0 / 5s:14.0 / 15s:14.0 / 30s:14.0 / 60s:14.0 | 0.0, 0, 0 | 2.5 |
| present | no-neutral v1 | 5 | BGC <= 14 (best published) | 14.0, 14.0 | 4 | 5/5, median 0.6 s | 1s:14.0 / 5s:14.0 / 15s:14.0 / 30s:14.0 / 60s:14.0 | 0.0, 0, 0 | 2.5 |
| present | no-odc v1 | 5 | BGC <= 14 (best published) | 14.0, 14.0 | 4 | 5/5, median 0.8 s | 1s:14.0 / 5s:14.0 / 15s:14.0 / 30s:14.0 / 60s:14.0 | 0.0, 0, 0 | 2.5 |
| present | no-restart v1 | 5 | BGC <= 14 (best published) | 14.0, 14.0 | 4 | 5/5, median 1.0 s | 1s:14.0 / 5s:14.0 / 15s:14.0 / 30s:14.0 / 60s:14.0 | 0.0, 0, 0 | 2.5 |
| present | no-resub2+3 v1 | 5 | BGC <= 14 (best published) | 27.0, 23.0 | 9 | 0/5, median - s | 1s:27.0 / 5s:27.0 / 15s:27.0 / 30s:27.0 / 60s:27.0 | 0.0, 0, 0 | 2.2 |
| present | no-resub3 v1 | 5 | BGC <= 14 (best published) | 14.0, 14.0 | 4 | 5/5, median 1.3 s | 1s:15.0 / 5s:14.0 / 15s:14.0 / 30s:14.0 / 60s:14.0 | 0.0, 0, 0 | 2.5 |
| rectangle | no-anneal v1 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 4/5, median 0.0 s | 1s:12.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 0, 0 | 2.2 |
| rectangle | no-fraig v1 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 0.0 s | 1s:12.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 0, 0 | 2.5 |
| rectangle | no-neutral v1 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 0.0 s | 1s:12.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 0, 0 | 2.5 |
| rectangle | no-odc v1 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 0.0 s | 1s:12.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 0, 0 | 2.5 |
| rectangle | no-restart v1 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 0.0 s | 1s:12.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 0, 0 | 2.3 |
| rectangle | no-resub2+3 v1 | 5 | BGC <= 12 (best published) | 25.0, 21.0 | 8 | 0/5, median - s | 1s:25.0 / 5s:25.0 / 15s:25.0 / 30s:25.0 / 60s:25.0 | 0.0, 0, 0 | 2.2 |
| rectangle | no-resub3 v1 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 0.0 s | 1s:12.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 0, 0 | 2.5 |

## Skeleton-level ablations (full config)

| target | config | runs | target | final cost/G (median, best) | A median | reach target | best-so-far median at checkpoints | overhead s (start, skel, synth) | peak RSS MB |
|---|---|---|---|---|---|---|---|---|---|
| aes | no-merge v1 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 133.0, 131.0 | 36 | 2/5, median 32.0 s | 1s:142.0 / 5s:142.0 / 15s:134.0 / 30s:133.0 / 60s:133.0 / 120s:133.0 | 0.0, 24.0, 0.3 | 3.1 |
| aes | seeded-only v1 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 133.0, 131.0 | 36 | 2/5, median 31.5 s | 1s:142.0 / 5s:142.0 / 15s:134.0 / 30s:133.0 / 60s:133.0 / 120s:133.0 | 0.0, 24.0, 0.1 | 3.1 |
| aes | unseeded v1 | 5 | G <= 132 (below every published circuit within A36 AD4 GD13) | 133.0, 131.0 | 36 | 2/5, median 85.8 s | 1s:142.0 / 5s:142.0 / 15s:142.0 / 30s:142.0 / 60s:133.0 / 120s:133.0 | 0.0, 24.0, 0.2 | 3.1 |
| gf16-mul | no-merge v1 | 5 | A <= 9 (bilinear complexity) | 32.0, 31.0 | 9 | 3/5, median 12.1 s | 1s:34.0 / 5s:33.0 / 15s:32.0 / 30s:32.0 / 60s:32.0 | 0.0, 12.1, 0.0 | 2.7 |
| gf16-mul | seeded-only v1 | 5 | A <= 9 (bilinear complexity) | 32.0, 31.0 | 9 | 4/5, median 32.1 s | 1s:34.0 / 5s:34.0 / 15s:32.0 / 30s:32.0 / 60s:32.0 | 0.0, 12.0, 0.0 | 2.7 |
| gf16-mul | unseeded v1 | 5 | A <= 9 (bilinear complexity) | 32.0, 31.0 | 9 | 3/5, median 12.0 s | 1s:34.0 / 5s:34.0 / 15s:33.0 / 30s:32.0 / 60s:31.0 | 0.0, 12.0, 0.0 | 2.7 |
| rectangle | no-merge v1 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 2.0 s | 1s:27.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 12.0, 0.0 | 2.5 |
| rectangle | seeded-only v1 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 2.0 s | 1s:27.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 12.0, 0.0 | 2.5 |
| rectangle | unseeded v1 | 5 | BGC <= 12 (best published) | 12.0, 12.0 | 4 | 5/5, median 2.0 s | 1s:27.0 / 5s:12.0 / 15s:12.0 / 30s:12.0 / 60s:12.0 | 0.0, 12.0, 0.0 | 2.5 |

