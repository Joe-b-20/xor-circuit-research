# BoolFlux checkpoint

Branch `boolflux-2026-11-13` (worktree `~/xcr-boolflux`), from `main` a6ef62d with the local
`nonlinear-extension` branch (NIST AES S-box circuits, `boolcirc`) merged in. `main`,
`nonlinear-extension` and the other branches are unchanged. Nothing is pushed. Campaign
outputs: `~/xs-campaigns/2026-11-13-boolflux/` (outside the repository); verified circuits are
copied to `results/`.

## State (2026-11-13, end of the first session)

- **Built**: gate-level kernel (exact care-set resubstitution with 0-3 new gates of any
  two-input type, caps on GD/AD/A with a penalised repair mode, annealing, restarts),
  AND-skeleton kernel (swap/merge/split/perturb, exact span checks), skeleton extraction and
  three synthesis variants, `cli.py run|pipe|verify|start`, models nist/bgc/gc6/gc/xag, 28 S-box
  tables with sources, literature notes, independent verifier, unit tests (10 + 36), campaign
  scripts, collectors. Every run snapshots its sources and binaries.
- **Review**: independent review with ~2,200 fuzz cases found no wrong-function path; its three
  major findings (feasibility not lexicographic, caps/metrics not checked independently,
  binaries not pinned) are fixed (review/REVIEW.md, Resolution).
- **Results** (LEDGER.md): sanity cases reach known optima (GF(2^4) multiplication 16 -> 9
  AND needs the skeleton level); 23 small S-boxes from naive starts equal the best published
  BGC/GC except Midori Sb1 (+1), beat none; AES: Boyar-Peralta 113 -> 108; 33 of 46 NIST
  circuits improved under their own caps, 18 new points on NIST's published set; fewest gates
  at GD <= 11, 12, 13, 14, 18, 19 below the published best (150, 146, 137, 126, 110, 108 vs
  157, 151, 148, 137, 116, 116).

## Open

- Global AES records untouched: G 104 (GD 30), NIST targets A <= 27, G <= 100, G <= 110 at
  GD <= 14 (we have 126). GD <= 10 not reached.
- Skeleton moves on AES lose 40-50 gates in resynthesis (greedy/Paar), which the gate level
  only partly recovers (104 -> 152 -> 106); an in-place leaf swap that keeps the existing linear
  layers would make AND-structure moves useful on good AES circuits.
- Not run: the inverse AES S-box frontier (the 44 NIST inverse circuits are imported), GE area
  models, 8-bit S-boxes other than AES (tables for SKINNY-128, SM4, Camellia are in sboxes.json).
- Review minor items left: m1 (gdw.* only in the kernel), m2, m10, m11 (rejected loudly).
