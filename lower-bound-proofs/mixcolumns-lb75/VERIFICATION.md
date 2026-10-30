# Reproducing the 75-gate lower-bound checks

## Requirements and complete command

- Python **3.10 or newer**.
- Standard library only for all required checks.
- No compiler, solver, network access, or external data.
- An extracted, writable copy of the complete package. The wrapper runs the original checkers in
  a temporary copy and writes fresh logs and reports under `verification/`; the supplied source
  and input files remain unchanged.

From the extracted package root:

```sh
python3 verify_all.py
```

On Windows: `py -3 verify_all.py`. The wrapper can also be invoked by absolute path from another directory.
Do not use Python's `-O` or `-OO` flags: the original checkers use assertions. The wrapper rejects an
optimized interpreter and removes `PYTHONOPTIMIZE` before starting the child checks.

Successful completion ends with:

```text
ALL CHECKS PASSED: 484 + 4,057 exact certificates; complete coverage; 13 circuit controls.
```

The runtime depends on the interpreter and processor; each run records its own in
`verification/run_<timestamp>/` and rewrites `verification/latest_summary.json`.

## What runs

| Stage | Purpose |
|---|---|
| Source integrity | Check the included fixed programs and input data against recorded SHA-256 values |
| `finite_facts.py` | Independently reconstruct every fixed-matrix fact F1-F14, including exhaustive short-word and label-capacity calculations |
| `check72.py` | Exclude gate counts 69, 70, 71 by the scalar two-step drift calculation |
| `check73.py` | Enumerate gate count 72; isolate its sole zero-drift tuple and reconstruct the rank-six obstruction |
| `check_dark_source.py` | Reconstruct the complete short boundary-relation source for the dark-label arguments |
| `certify74.py` | Check every exact certificate and coverage obligation excluding a 73-gate optimum |
| `independent74.py` | Rebuild the same coefficient formulas and coverage domain in a separate implementation |
| `certify75.py` | Check every exact certificate and coverage obligation excluding a 74-gate optimum |
| `independent75.py` | Rebuild those formulas and coverage in a separate implementation |
| `stress.py` | Test identities and inequality rows on 13 included circuit controls and canonical transposes |
| `source/verify.py` | Rebuild the AES map, verify all 32 outputs of each control circuit, and match record hashes |

The wrapper checks every child exit status and validates key output-report fields. It does not treat
silence, a time limit, or an optimizer's status as a proof.

## Exact certificate landmarks

| Quantity | Excludes $G=73$ | Excludes $G=74$ |
|---|---:|---:|
| Scalar profiles | 262 | 1,102 |
| Oriented claims | 524 | 2,204 |
| Local certificates supplied and checked | 484 | 4,057 |
| Helper-type coefficients checked | 13,819 | 163,599 |
| Certificate references in coverage | 1,456 | 9,604 |
| Distinct certificates referenced | 383 | 3,481 |
| Direct geometric references | 0 | 927 |
| Largest weighted right-hand side | -1 | -1 |

Every supplied multiplier is a nonnegative integer. Each checker rebuilds the inequality coefficients
and proves that the weighted left-hand coefficients are nonnegative while the weighted right-hand side
is strictly negative. The coverage procedure independently reconstructs the scalar domains and verifies
that no required local case is missing. Valid extra certificates not referenced by coverage are still checked.

## Selected finite-fact landmarks

| Fact | $M$ | $M^{\mathsf T}$ |
|---|---:|---:|
| Distinct boundary pair XORs | 2,016 | 2,016 |
| Maximum boundary triple multiplicity | 3 | 3 |
| Weight-six boundary relations | 60 | 84 |
| Rank of those relations | 20 | 28 |
| Nine-part partition search states | 1,485,213 | 91,485 |
| Nine-part final complement checks | 62,112 | 720 |
| Nine-part partitions found | 0 | 0 |

For the transpose boundary, the weight-eight and weight-ten relation spans both have rank 29, and
exactly 736 weight-twelve words are nonzero modulo that span. The complete finite-fact transcript
contains all label-capacity and quotient counts used in the mathematical note.

## Direct commands and optional cross-check

To use the original published runner, from `source/lower_bounds/`:

```sh
sh checks/run_all.sh
python3 ../verify.py
```

The POSIX shell runner is supplied for provenance; the top-level Python entry point is the portable
route and performs the complete required suite.

The optional LP cross-check requires NumPy and SciPy:

```sh
sh checks/run_all.sh --with-lp
```

It reconstructs the 74-gate count-profile exclusion with a separate numerical model. This optional
check is supplementary. Exact checking of the already supplied certificates is sufficient for the
finite arithmetic portion of the proof and needs no numerical package. The fresh audit
does not claim to have repeated every historical optional LP or large stress-corpus run.

## Scope of verification

Program acceptance establishes the fixed-matrix enumerations, integer certificate arithmetic,
coverage, and tested circuit identities. It does not automatically establish that the local inequalities
are necessary for every unrestricted circuit, that inverse transposition has the claimed property,
or that the bounded-potential proof is valid. Those mathematical steps are stated and proved in the note
for expert review. Stress tests are positive controls and are not a substitute for the universal argument.
