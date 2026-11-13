# BoolFlux checkpoint

Branch `boolflux-2026-11-13` (worktree `~/xcr-boolflux`), from `main` a6ef62d with the local
`nonlinear-extension` branch merged in. `main`, `nonlinear-extension` and the other branches are
unchanged. Nothing is pushed. Campaign outputs: `~/xs-campaigns/2026-11-13-boolflux/` (outside
the repository); claimed circuits are in `results/` with `results/MANIFEST.json`.

## State (2026-11-13, after the baseline correction)

- **Baseline**: NIST usnistgov/Circuits pinned at e6ac0d03f4816927f1b0e676996e4d075ab8d1c0
  (`nonlinear/nist/`, 191 files, all verified by boolcirc and the independent verifier). The
  earlier pin 0876577 had 46 forward circuits in `aes-sbox/`; e6ac0d0 has 78 (102 forward files
  in all), including 159@GD10, 148@11, 141@12, 133@13, 127@14.
- **Results** (LEDGER.md, rechecked by an independent audit, audit/AUDIT.md + run-final.log):
  - sanity: majority 4/1 AND, full adder 5/1 AND (minimum sizes), GF(2^4) multiplication
    16 -> 9 AND (= bilinear complexity; needs the skeleton level), GF(2^4) inversion 5 AND (MC 5).
  - 23 small S-boxes, BGC and GC kept separate: all equal the best published value except Midori
    Sb1 BGC (+1); optimal where the published value is SAT-proved (Piccolo, PRIDE, RECTANGLE GC);
    none beaten. Ascon 16 (BGC) / 15 (GC) equal ZH23's upper bounds.
  - AES: Boyar-Peralta 113 -> 108 (improves its start only). 12 (A, AD, G, GD) tuples new on the
    e6ac0d0 set; fewest gates at GD <= 13, 14, 18, 19: 131, 126, 110, 108 (published 133, 127,
    116, 116). The earlier claims at GD 11 and 12 and 13 of the 18 "new" points are withdrawn.
- **Errors found and fixed in this pass**: chi3 target bit order (re-run, old files in
  `results/_superseded/`), header tallies that called `XNOR t a 0` a NOT, stale ledger rows,
  the boolcirc name parser for NIST's `-xxn` names.

## Open

- NIST targets (A <= 27, G <= 100, G <= 110 at GD <= 14) and the record (103 / 104) untouched.
- In-place AND-skeleton moves for good AES circuits (resynthesis loses 40-50 gates).
- Inverse AES S-box frontier, GE models, other 8-bit S-boxes: not run.
- Papers not read (CITATIONS.md, "papers to request"): Maximov-Ekdahl 2019, Chudnovsky 1988,
  Barbulescu et al. 2012, Knuth TAOCP 7.1.2, Zajac-Jokay 2014, Mirwald-Schnorr 1992.
