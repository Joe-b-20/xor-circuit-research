# Reproduce the depth-three lower bound

## Complete verification

Requirements: Python 3.10 or later and a C++17 compiler available as `g++`.
Only Python's standard library is used. No solver, Python package download,
or network access is needed for verification.

Extract the complete package into a writable directory and run:

```bash
python3 verify_all.py
```

The wrapper unpacks the losslessly compressed `technical.tar.xz` into a
temporary directory and verifies the SHA-256 hashes of every original
technical source, certificate, and supporting note. The archive contains
only the exact source paths listed in the inventory; links, unexpected files,
and duplicate entries are rejected. It then runs:

```bash
python3 verify_complete_92_exclusion.py --full
```

The original technical files remain unchanged. Full output and fresh JSON
records are saved under a new `verification/run_<timestamp>/` directory.
The wrapper exits with code zero only if the complete verification passes.
Its summary must report `PASS`, lower bound 93, zero uncovered partitions,
`source_certificate_checker_rerun: true`, and
`reused_completed_checks: false`.

Run Python normally, without `-O` or `PYTHONOPTIMIZE`; the checkers use
assertions, and the wrapper rejects optimized mode.

## Inspect the original source without running the proof

The compressed tree does not modify any original source or certificate
bytes. Python unpacks it using its standard
library; no separate archive utility is required.

To create a readable source tree:

```bash
python3 verify_all.py --extract-source review_sources
```

Choose a new directory name. The command refuses to overwrite an existing
directory. The files appear in `review_sources/technical/` and every original
hash is checked. All `technical/` references in the proof refer to this tree.

For an integrity-only check with automatic temporary extraction:

```bash
python3 verify_all.py --check-package
```

These two modes need no C++ compiler and do not rerun the proof. The default
command without flags remains the complete verification route.

## What a complete run establishes

1. The exact AES matrix and the depth-three normal-form ingredients.
2. The local boundary table and exact weighted cluster inequalities.
3. The pair-graph component bound and the complete proof that at least 26
   normalized pairs are needed.
4. All finite premises and exact arithmetic for the 16,868-row source
   certificate, then the tradeoff `4H-P >= 214`.
5. The complete eight-component branch, including all parent-tree prices
   and all remaining pair-recipe exclusions.
6. All 17 single-component certificates, complete six- and seven-component
   partition regeneration, and their parent-tree prices.
7. All 1,113 exact partition Farkas certificates.
8. All 20,933 forest obstructions used for the six-component branch and
   the 710 rotation representatives of the seven-component pair exclusions.
9. Exact set-union coverage with no uncovered partition and direct checking
   of the 97-gate, depth-three construction.

An unresolved or capped finite search is not counted as an exclusion. The
checkers require the relevant searches to finish.

## Evidence directories

`verification/original_*.json` are the records in the source archive, not
claims that a new run has occurred. The 2026-10-23 audit is in
`verification/fresh_audit_2026-10-23/`; new runs receive their own
timestamped directory.

`verification/source_inventory.json` records the provenance and exact
SHA-256 of each retained archived file. The presentation and wrapper are
new material; they do not change the mathematical certificate data.

## Reading order

Start with the main proof PDF or `PROOF.md`. Read the original supporting
notes in `source_notes/` for the detailed boundary case proof, complete
weighted charge table, and original finite-checking arguments. Their
historical global bounds are superseded by the main proof; their stated
local lemmas are the premises retained here.

The following inherited flags are deliberately not used by the package's
default command:

- Omitting `--full` skips the rerun of earlier finite premises.
- `--reuse-checked-results` combines existing results rather than rerunning
  the component checks.
- `--skip-finite-checks` and similar flags in individual modules are not
  complete verification commands.

## Computational status

Passing these checks establishes the specified finite statements and exact
certificate arithmetic, together with the mathematical reductions explained
in the proof. It does not amount to external peer review or a formal proof
in a proof assistant. The still possible total gate counts are 93 through
97; this package does not resolve their optimum.
