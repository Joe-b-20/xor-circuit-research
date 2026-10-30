# Provenance and review status

**Author:** Joe Bachir.  
**Underlying note:** *A computer-assisted lower bound of 75 two-input XOR gates for AES MixColumns*,
review draft 1.1, October 2, 2026.  
**Package edition:** October 23, 2026.

The argument was developed with large-language-model assistance under the author's direction.
The review history described in the underlying note consists of programs and machine reviewers.
No independent human referee or proof-assistant formalization is claimed.

## Pinned public source

- Repository: <https://github.com/Joe-b-20/aes-mixcolumns-xor-circuits>
- Observed and retrieved commit: `8b4feb52a8924d3eb6d72314f67a2f38b6988eb8`.
- Original note's Git blob: `cd97b9e2fbc5c017e8420504640d19e6c31e5242`.
- Pinned note: <https://github.com/Joe-b-20/aes-mixcolumns-xor-circuits/blob/8b4feb52a8924d3eb6d72314f67a2f38b6988eb8/lower_bounds/PROOF_NOTE_75.md>.
- `CERTIFICATES74.json` Git blob: `d2edf06209f4fbdd5b84a20bcf240c9e58abf11a`.
- `CERTIFICATES75.json` Git blob: `a51f38fc7fcca1e21cda11b92c7e9e096998a5b7`.

Every retrieved file was checked against its Git blob identity. The proof inputs and programs included
in the clean package are additionally listed with SHA-256 values in `provenance/source_hashes.json`.
The verifier runs the checkers in a temporary copy and saves their regenerated JSON reports and logs
separately from the pinned input files. `source/bounds.json` is retained unchanged solely as the original
circuit verifier's record and hash metadata. Its historical commentary describes that frozen repository
snapshot; it is not an updated frontier statement or a premise of the lower-bound proof.

## Relationship to previous archives

An earlier archive (22 September 2026, not included) holds the historical chain of proof notes.
The public October 2 note consolidates that chain into one complete argument with a flat set of checkers.
The exposition clarifications applied in this edition are listed in `EDITORIAL_CHANGES.md`. No result from an unrelated restricted search or an
unpublished stronger bound is used here.

## Fresh reproducibility work for this edition

The complete finite-fact and certificate suite was rerun on October 23, 2026. This includes both final
exclusion datasets: 484 certificates for excluding 73-gate optima and 4,057 for excluding 74-gate optima,
each checked by the original and separately implemented verifiers. The fixed-matrix finite facts,
coverage domains, earlier scalar exclusions, dark-label source data, and stress controls were also rerun.
All 13 included circuit controls were checked against a fresh construction of the AES map and against
the original record hashes. The exact transcripts accompany the package.

These executions reproduce the finite computations. They do not certify the written mathematical
reductions automatically; those are the intended subject of expert review.

## License

The original repository material is redistributed under its included MIT license, retained at
`LICENSE` and `source/LICENSE`. The new formatting and verification wrapper are included
under the same license.

## Repository edition (29 October 2026)

The October 23 ZIP (`AES_MixColumns_Unrestricted_LB75_2026-10-23.zip`, SHA-256
`a60697a6bbf1963c551585ae8c9551a26fe8753abb596dcb8eb940ac4239b2e3`, 91 files) was unpacked here.
All files are byte-identical to it except: `README.md` was shortened, this section was added,
wording for readers was edited in `PROVENANCE.md`, `EDITORIAL_CHANGES.md` and `VERIFICATION.md`
(2026-10-30; the proof, the source and every checked file are unchanged), and `SHA256SUMS.txt` was
regenerated without `verification/latest_summary.json`, which every run rewrites. The ZIP's own manifest is kept unchanged as
`provenance/zip-edition-SHA256SUMS.txt`.
