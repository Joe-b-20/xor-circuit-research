# Provenance and scope

## Source proof

This package presents Joe Bachir's computer-assisted investigation of the
depth-three XOR complexity of one AES forward MixColumns column. The claim
offered for review is a lower bound of **93 gates**, with a verified
**97-gate, depth-three** construction supplied as an upper-bound control.
The exact optimum remains unresolved.

The mathematical proof sources, certificate data, and checker programs are
retained from the corrected archive:

`AES_DEPTH3_LOWER_BOUND_93_2026-10-17.zip`

Source archive SHA-256:

```text
007792f8be74bba470ad534b6149cc1f8d6c1374acf34e02a880b67fbc3d229b
```

The review presentation and package were prepared on **23 October 2026**
with AI assistance. The verification described in `VERIFICATION.md` is a
fresh computational replay of the supplied proof checks; it is not an
external referee report or proof-assistant formalization.

## Retained and newly prepared material

The archived technical programs and certificate files have not been edited.
The package retains the dependency set for the full proof command,
including all 1,113 partition certificates, all 17 single-component
certificates, the frozen 16,868-row source certificate, partition data,
forest obstructions, parent prices, and construction controls, except four
inherited modules that are added from `supplement/` (see below). The technical
subtree is distributed as `technical.tar.xz`; the verification wrapper
extracts it using only Python's standard library and checks the original
bytes before running it.

The main proof narrative, reproduction guide, this provenance note, the
verification report, and the package wrapper are newly prepared presentation
and review material. The wrapper controls integrity checking, safe extraction,
temporary working copies, and result capture; it does not alter the proof's
mathematical reductions or certificate arithmetic.

`verification/source_inventory.json` records every retained archived file's
source entry and SHA-256. It contains 1,216 entries: 1,186 technical files,
14 original supporting proof notes, and 16 original verification records.
These retained files were checked byte-for-byte against the source archive.

The large historical discovery corpus, numerical optimization inputs,
intermediate searches, and obsolete progress logs have been omitted. No
discovery optimizer or network access is required for proof verification.

## Correction history

The former recursive component-partition enumerator applied a next-choice
average-weight bound to candidates that would be selected at later depths.
That could omit later, heavier component words. The corrected version applies
the bound only to the next choice and keeps the full compatible candidate set
for recursion.

This correction changes the eight-component subcase used in the pair-count
proof from 800 to **2,848** partitions. It changes the main eight-component
universe from 104,548 to **110,712** partitions. All additional cases are
covered by the corrected proof. The repaired original checkers and the full
case sets are included, along with the original correction notice in
`source_notes/ENUMERATION_CORRECTION.txt`.

The source notes preserve the historical weaker global bounds stated when
individual local lemmas were first proved. Those historical status statements
are superseded by the main proof's final interval **93 through 97**. The local
lemmas and their exact finite checks remain the dependencies used here.

## Meaning of the claims

The lower bound applies to all circuits in the stated depth-three model,
with arbitrary cancellation, fan-out, sharing, and asymmetry. The finite
helper universe is exhaustive because of the depth-three normal form; it is
not a bank restricted to previously found circuits.

The result is not a 93-gate construction, a proof of 97-gate optimality, or
a lower bound of 93 for greater depths.

## Repository edition (29 October 2026)

The 2026-10-23 ZIP (`AES_MixColumns_Depth3_LB93_2026-10-23.zip`, SHA-256
`9e9e365c0ade4a3449222bdfed107c304ca4e3e63bb3c6f3f8fa1215e17ee90e`, 60
files) was unpacked here; all files are byte-identical to it except:

- `technical.tar.xz` lacks four inherited modules; they are added from
  `supplement/` (see `supplement/README.md`); the tar is unchanged.
- `verify_all.py` stages `supplement/` and adds `--quick`.
- `README.md` was shortened; this section was added to `PROVENANCE.md`.
- Wording for readers was edited in `README.md`, `PROVENANCE.md`,
  `REPRODUCE.md` and `VERIFICATION.md` (2026-10-30). The proof, the source
  notes and every checked file are unchanged.
- `SHA256SUMS.txt` was regenerated. The ZIP's own manifest is kept unchanged
  as `provenance/zip-edition-SHA256SUMS.txt`.
