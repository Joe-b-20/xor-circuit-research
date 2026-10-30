# AES MixColumns: an unrestricted 75-gate lower bound

**Joe Bachir · Review package · 23 October 2026**

Every two-input XOR circuit computing one 32-bit AES forward MixColumns column has at least 75
gates. Depth, fan-out, cancellation, intermediate values, and output reuse are unrestricted; every
gate counts. With the included 88-gate circuits, 75 ≤ L(M) ≤ 88. Neither end is claimed tight.

## Read

- [PROOF.pdf](PROOF.pdf) / [PROOF.md](PROOF.md): the mathematical note.
- [VERIFICATION.md](VERIFICATION.md): what each check does and the expected results.
- [PROVENANCE.md](PROVENANCE.md): pinned public source, authorship, review status.
  [EDITORIAL_CHANGES.md](EDITORIAL_CHANGES.md): exposition changes from the published note.

## Check

Python 3.10+, standard library only. From this directory:

```sh
python3 verify_all.py
```

It checks source hashes, runs the original checkers in a temporary copy, and ends with
`ALL CHECKS PASSED: 484 + 4,057 exact certificates; complete coverage; 13 circuit controls.`
Logs go to `verification/run_<timestamp>/`, and `verification/latest_summary.json` is overwritten.
Do not use `-O`; the checkers rely on assertions.

## How the proof works

The starting point is the parity of every signal's coefficient mask. Writing $x$ for odd-plus-odd gates,
$y$ for even-plus-even gates, and $h$ for odd non-output gates gives $G=32+x+y+h$.
Fixed-matrix facts and an odd-signal graph constrain helper sharing. Exact circuit transposition then
allows the argument to follow an indefinite sequence of minimum circuits while preserving the gate count.
A bounded integer potential must increase along every possible low-gate sequence. Finite enumeration
and exact nonnegative integer multiplier certificates cover the remaining count profiles at 73 and 74
gates and supply the contradiction.

The local systems are necessary conditions for arbitrary circuits. Helpers are not restricted to a
chosen bank of values. Floating-point optimization was used to discover multipliers; verification checks
their arithmetic exactly and does not trust an optimizer's infeasibility status.

| Final exclusion | Scalar profiles | Oriented claims | Exact certificates | Helper-type coefficients |
|---|---:|---:|---:|---:|
| No 73-gate optimum | 262 | 524 | 484 | 13,819 |
| No 74-gate optimum | 1,102 | 2,204 | 4,057 | 163,599 |

## Package map

| Path | Purpose |
|---|---|
| `source/lower_bounds/checks/` | Original exact programs, certificates, and finite-fact data |
| `source/lower_bounds/PROOF_NOTE_75.md` | The unchanged published note |
| `source/matrix.txt`, `source/matrix.sha256` | Exact 32-by-32 binary map |
| `source/verify.py`, `source/circuits/`, `source/bounds.json` | Circuit checks and the 13 control circuits |
| `verification/` | 2026-10-23 run logs and summaries |
| `provenance/source_hashes.json` | Pinned-source Git blobs and SHA-256 values |
| `typeset/` | LaTeX source of the PDF |
| `SHA256SUMS.txt` | Hashes of this directory's files; `provenance/zip-edition-SHA256SUMS.txt` is the original ZIP's manifest |
| `LICENSE`, `source/LICENSE` | Original MIT license |

## Review status

The checkers establish finite facts, certificate arithmetic, and coverage. Expert review is still
needed for the unrestricted circuit-to-graph reduction, transposition and the inverse-association
lemma, the local inequalities, and the bounded-potential argument. The proof was developed with
language-model assistance; it has had no human peer review and is not formalized.
