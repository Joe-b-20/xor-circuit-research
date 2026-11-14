100 runs, 0 with errors, 100 verified

## Linear maps: XORFlux v8 vs XOR-only BoolFlux (same start, same CPU, 120 s each)

Target = the repository's best known circuit at that cap (XORFlux records, hours of search).

Memory: XORFlux = its whole Python process; BoolFlux = C kernel / Python driver (measured from v3 on; about 20 MB in the driver, review2 C1), so the whole-tool memory of both is of the same order.

| map | cap | start | tool | final G (median, best, worst) | reach best known | reach best+2 | best-so-far median at 5/15/60/120 s | peak RSS MB (XORFlux: process; BoolFlux: kernel) | start-up s |
|---|---|---|---|---|---|---|---|---|---|
| joltik | none | naive | boolflux-v2 | 43.0, 42, 44 | 1/10, median 18.8 s | 10/10, median 6.7 s | 45.0/44.0/43.0/43.0 | 2.5 | 0.6 |
| joltik | none | naive | xorflux | 43.0, 42, 45 | 2/10, median 75.5 s | 9/10, median 8.6 s | 46.0/44.5/43.5/43.0 | 27.0 | -0.5 |
| joltik | none | nist | boolflux-v2 | 44.0, 43, 44 | 0/10, median - s | 10/10, median 0.0 s | 44.0/44.0/44.0/44.0 | 2.4 | 0.0 |
| joltik | none | nist | xorflux | 43.0, 42, 44 | 3/10, median 100.6 s | 10/10, median 0.0 s | 44.0/44.0/44.0/43.0 | 26.9 | -1.7 |
| small-scale-aes | none | naive | boolflux-v2 | 42.5, 42, 43 | 5/10, median 42.3 s | 10/10, median 3.4 s | 44.0/44.0/43.0/42.5 | 2.5 | 0.6 |
| small-scale-aes | none | naive | xorflux | 42.0, 42, 43 | 8/10, median 34.5 s | 10/10, median 4.3 s | 44.0/43.0/42.5/42.0 | 27.1 | -1.1 |
| small-scale-aes | none | nist | boolflux-v2 | 43.0, 42, 43 | 1/10, median 79.1 s | 10/10, median 0.0 s | 43.0/43.0/43.0/43.0 | 2.5 | 0.0 |
| small-scale-aes | none | nist | xorflux | 42.0, 42, 43 | 7/10, median 42.9 s | 10/10, median 0.0 s | 43.0/43.0/42.0/42.0 | 26.5 | -1.9 |

## Small nonlinear targets from naive ANF starts (60 s each)

| target | config | runs | target | final cost/G (median, best) | A median | reach target | best-so-far median at checkpoints | overhead s (start, skel, synth) | peak RSS MB kernel / driver |
|---|---|---|---|---|---|---|---|---|---|

## AES S-box (NIST model)

| target | config | runs | target | final cost/G (median, best) | A median | reach target | best-so-far median at checkpoints | overhead s (start, skel, synth) | peak RSS MB kernel / driver |
|---|---|---|---|---|---|---|---|---|---|
(an unverified run = no circuit within the caps by the end of the budget)

| aes-a36g142 | gate v1 | 10 | G <= 132 (below every published circuit within A36 AD4 GD13) | 133.5, 133.0 | 36.0 | 0/10, median - s | 1s:138.0 / 5s:135.0 / 15s:134.0 / 30s:134.0 / 60s:133.5 / 120s:133.5 | 0.0, 0.0, 0.0 | 3.1 / 26.8 |
| aes-a36g142 | gate v2 | 10 | G <= 132 (below every published circuit within A36 AD4 GD13) | 133.0, 131.0 | 36.0 | 1/10, median 29.9 s | 1s:138.0 / 5s:136.0 / 15s:135.0 / 30s:134.0 / 60s:134.0 / 120s:133.0 | 0.0, 0.0, 0.0 | 3.1 / 26.5 |

## Gate-kernel ablations (gate config, one mechanism off)

| target | config | runs | target | final cost/G (median, best) | A median | reach target | best-so-far median at checkpoints | overhead s (start, skel, synth) | peak RSS MB kernel / driver |
|---|---|---|---|---|---|---|---|---|---|

## Skeleton-level ablations (full config)

| target | config | runs | target | final cost/G (median, best) | A median | reach target | best-so-far median at checkpoints | overhead s (start, skel, synth) | peak RSS MB kernel / driver |
|---|---|---|---|---|---|---|---|---|---|

