# AES MixColumns: a 93-gate lower bound at depth three

**Joe Bachir · Review package · 23 October 2026**

Every two-input XOR circuit computing one 32-bit AES forward MixColumns column, with inputs at
depth zero and output depth at most three, uses at least 93 gates. Sharing, fan-out, cancellation,
and asymmetry are unrestricted. With the included 97-gate depth-three circuit, 93 ≤ D₃ ≤ 97; the
minimum in that interval is unresolved, and nothing here bounds circuits of greater depth.

## Read

- [PROOF.pdf](PROOF.pdf) / [PROOF.md](PROOF.md): the mathematical note.
- [REPRODUCE.md](REPRODUCE.md): what the full run checks. [VERIFICATION.md](VERIFICATION.md): the 2026-10-23 audit.
- [PROVENANCE.md](PROVENANCE.md): source archive, corrections, authorship, review status.

## Check

Python 3.10+ (standard library only) and `g++` with C++17. From this directory:

```sh
python3 verify_all.py                 # complete replay, single-threaded (see below for time)
python3 verify_all.py --quick         # hashes + first five finite stages, seconds; not a proof replay
python3 verify_all.py --check-package # hashes only
python3 verify_all.py --extract-source review_sources   # readable technical/ tree
```

The wrapper unpacks `technical.tar.xz` into a temporary directory, checks every recorded hash,
adds the four modules in [supplement/](supplement/README.md), and runs
`verify_complete_92_exclusion.py --full`. A full run writes `verification/run_<timestamp>/`.
It took 16 min 39 s in the 2026-10-23 audit (`verification/fresh_audit_2026-10-23/`) and
22.5 min from a fresh copy of this edition on 2026-10-29. Do not use `-O`; the checkers rely on assertions.

## Proof route

The depth bound gives a complete normal form with pair, triple, and quartet helpers, including
every permitted cancelling final-parent recipe. If a circuit used at most 92 gates, the checked
inequalities `P ≥ 26` and `4(P+T+Q) − P ≥ 214` would force exactly 26 pair helpers and 34 triple/quartet
helpers. Parity then leaves six, seven, or eight connected components in the pair graph.

| Pair-graph components | Complete partition universe | How the branch closes |
|---|---:|---|
| 6 | 275,354 | Forest obstructions and exact conditioned Farkas certificates |
| 7 | 22,060 | Parent-tree prices, complete pair-recipe searches, and exact conditioned Farkas certificates |
| 8 | 110,712 | Parent-tree prices and complete pair-recipe exclusions; surviving structures require at least 96 gates |

The conditioned certificate collection has 1,113 representatives: 909 for the six-component
case and 204 for the seven-component case. Their rotations are used only after verifying the
matrix symmetry; no symmetry restriction is imposed on an unknown circuit.

## Package map

| Path | Purpose |
|---|---|
| `technical.tar.xz` | Unchanged original programs, certificates, partition sets, exact matrix, and 97-gate witness |
| `supplement/` | Four inherited modules missing from the original tar, with hashes and their MIT notice |
| `source_notes/` | Original supporting arguments and the documented enumeration correction, byte-identical to the 17 October archive and hash-checked by `verify_all.py`; their global bounds are superseded, and some mention files that are not included |
| `verification/` | Fresh audit results, labelled historical records, and `source_inventory.json` (SHA-256 of every retained original file) |
| `typeset/` | LaTeX source of the PDF |
| `SHA256SUMS.txt` | Hashes of this directory's files; `provenance/zip-edition-SHA256SUMS.txt` is the original ZIP's manifest |

Paths beginning with `technical/` in the proof and notes refer to the unpacked tree.

## Review status

AI-assisted research draft. The finite calculations and certificate arithmetic are reproducible;
the universal reductions and the claim that the finite cases cover every allowed circuit need expert
review. Program acceptance is not peer review or proof-assistant formalization.
