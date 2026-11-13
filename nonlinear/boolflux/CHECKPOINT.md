# BoolFlux checkpoint

Branch `boolflux-2026-11-13` (worktree `~/xcr-boolflux`), from `main` a6ef62d with the local
`nonlinear-extension` branch (NIST AES S-box circuits, `boolcirc`) merged in. Nothing pushed.
Experiment outputs: `~/xs-campaigns/2026-11-13-boolflux/` (not in the repository; the circuits
worth keeping are copied into `nonlinear/boolflux/results/`).

## State (2026-11-13)

- Built: gate-level kernel `kernel/bfx.c` (exact care-set resubstitution, 0-3 new gates, any
  two-input library, caps on GD/AD/A, annealing), skeleton kernel `kernel/skel.c` (AND
  swap/merge/split/perturb with exact span checks), `cli.py run|pipe|verify|start`, cost models
  `models/`, targets `targets.py` + `benchmarks/sboxes.json`, naive ANF starts, independent
  verifier `independent/verify.py` (36 tests).
- Sanity: majority 5 gates/3 AND -> 4 gates/1 AND (optimal); GF(2^4) multiplication 16 AND
  (schoolbook) -> 9 AND (Karatsuba-type, the known minimum), 31 gates.
- Running: AES forward NIST frontier campaign (each published circuit under its own caps).

## Next

See LEDGER.md for every measured result.
