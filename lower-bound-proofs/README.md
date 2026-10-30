# Lower-bound proofs

Two computer-assisted lower bounds for one 32-bit AES forward MixColumns column (the 32×32
binary matrix over GF(2)), counting two-input XOR gates.

| Proof | Statement | Model | Check (from repo root) | Time |
|---|---|---|---|---|
| [mixcolumns-lb75](mixcolumns-lb75/) | Every circuit has ≥ 75 gates (with an 88-gate circuit: 75 ≤ L ≤ 88) | No depth or fan-out limit; cancellation allowed | `python3 lower-bound-proofs/mixcolumns-lb75/verify_all.py` | ~1.5 min |
| [mixcolumns-lb93-depth3](mixcolumns-lb93-depth3/) | Every circuit of depth ≤ 3 has ≥ 93 gates (with a 97-gate circuit: 93 ≤ D₃ ≤ 97) | Inputs at depth 0, outputs at depth ≤ 3; cancellation allowed | `python3 lower-bound-proofs/mixcolumns-lb93-depth3/verify_all.py` | 17–23 min |
| | quick check: hashes and first five finite stages, not a proof replay | | `python3 lower-bound-proofs/mixcolumns-lb93-depth3/verify_all.py --quick` | ~10 s |

Needs Python 3.10+ (standard library only); the depth-3 proof also needs `g++` with C++17. Both
checks are single-threaded. Do not run with `-O`. Neither proof determines the optimum, and the 93
bound says nothing about depth > 3.

Each folder holds the full text (`PROOF.md`, `PROOF.pdf`), the checkers and data, and its
provenance (`PROVENANCE.md`). Licenses: `mixcolumns-lb75/LICENSE` (MIT); the depth-3 package
has no license file of its own, only `supplement/LICENSE` (MIT) for its four added modules.

The depth-3 full check took 22.5 min from a fresh copy on 2026-10-29 (16 min 39 s in the
2026-10-23 audit). The proofs were developed with language-model assistance and have not had
human peer review; the checks replay the finite computations, not the mathematical reductions.
