# Provenance and review status

**Author:** Joe Bachir. **Packaged:** 9 November 2026, from the sprint of 7-8 November 2026.
**Relies on:** the 75-gate review package [`../mixcolumns-lb75/`](../mixcolumns-lb75/), unchanged,
whose `SHA256SUMS.txt` still verifies.

The mathematics and the programs were produced by language-model agents working under the author's
direction during the sprint. For each batch, one agent found the rows, a second agent checked them, and
a third wrote the addendum and produced and checked the certificates:

| Batch | Rows found by | Checked by | Addendum, certificates and checker by | Date (as in the addendum) | Sprint commit |
|---|---|---|---|---|---|
| 1 | qbound | qcheck | qcert | 2026-11-07 | `62af646e3612caeb4e8727ead36323c49e7eab44` |
| 2 | qreal | qrealcheck | qcert2 | 2026-11-07 | `a4d055aeb74dad6240cb33e8fa1540b4f1591b13` |
| 3 | qhub | qhubcheck | qcert3 | 2026-11-08 | `d351a6f5536d812954146da62421f6c15939370f` |
| 4 | qjoint | qjointcheck | qcert4 | 2026-11-08 | `61f8bdd922797438d36bd88c75dc14c371055fb3` |

The agents worked in `~/xs-campaigns/2026-11-07-sprint/qcert*/` on the author's machine. Their folders
were committed to the branch `sprint-2026-11-07-linear-maps` of this repository (the commits above, which
are also on `phase-2026-11-09`) under `research/sprint-2026-11-07/experiments/qcert*/`. That branch holds
the original experiment folders, including generators, reports, logs, cross-checks, mutation and stress
tests. The sprint's summary of each batch is `research/sprint-2026-11-07/FINDINGS.md`, sections F18,
F21, F27, F32 and F36. Section F16 and the lb76 report record what the 75 proof leaves open at G = 75.
The copies in the repository and in `~/xs-campaigns` were compared byte for byte on 2026-11-09, and
they agree for every file taken here.

## What was copied, and how

| Here | Source under `research/sprint-2026-11-07/experiments/` | SHA-256 of the source | Treatment |
|---|---|---|---|
| `certificates/CERTIFICATES_EXT75.json` | `qcert/CERTIFICATES_EXT75.json` | `68df54a7581a9760e4946c9e603f38bf8f2b8372d739e3c376daa846b722daf7` | byte-identical |
| `certificates/CERTIFICATES_CASES75.json` | `qcert2/CERTIFICATES_CASES75.json` | `19bad1fec5e718abcc03bd078252a3ebc2ff03866545ddadc7494d0f2ed10dca` | byte-identical |
| `certificates/CERTIFICATES_CASES75_B3.json` | `qcert3/CERTIFICATES_CASES75_B3.json` | `567b1778e0210602c9df976940471356ce04a58bcc1b3094942443cf4985b9ac` | byte-identical |
| `certificates/CERTIFICATES_CASES75_B4.json` | `qcert4/CERTIFICATES_CASES75_B4.json` | `70d2bc30353d9b24d72c0afa89e1d97d5126c57fadd0fd060b067268d1708ca0` | byte-identical |
| `addenda/PROOF_ADDENDUM.md` | `qcert/PROOF_ADDENDUM.md` | `18f60e7c2480ee42b87e361286194ad41357083d9bfba3be130822449dfeccd3` | one provenance line prepended |
| `addenda/PROOF_ADDENDUM_2.md` | `qcert2/PROOF_ADDENDUM_2.md` | `cee6517fe004fa324eb47b2a73bed3dc01cb397a8f2b5ae5741fc2752db9c008` | one provenance line prepended |
| `addenda/PROOF_ADDENDUM_3.md` | `qcert3/PROOF_ADDENDUM_3.md` | `096f4c60f59f2641ae7cceea4c35ffe1f6b8e36d22037b7e262b11b261c0630c` | one provenance line prepended |
| `addenda/PROOF_ADDENDUM_4.md` | `qcert4/PROOF_ADDENDUM_4.md` | `a5edecd30920bb540927964a227de8cb4e419d3ca0662ae1c6e35f75c949a07a` | one provenance line prepended |
| `checkers/check_ext75.py`, `check_cases75.py`, `check_cases3.py`, `check_cases4.py` | `qcert/`, `qcert2/`, `qcert3/`, `qcert4/` | see `checkers/CHANGES.md` | default certificate path only |
| `checkers/check_cases3_copy.py` | `qcert4/check_cases3_copy.py` (= `qcert3/check_cases3.py`) | `9319b103e1f6c7a4cbff28214cd1e1ed9b80c38d9470adde55f7ee8412b8f8ec` | byte-identical |

Each source hash above also matches the `SHA256SUMS.txt` of its source folder. To recover an addendum
exactly, remove its first line:

```sh
tail -n +2 addenda/PROOF_ADDENDUM_4.md | sha256sum   # a5edecd3...a07a
```

The addenda cite their batch reports (`REPORT.md`) and sibling folders (`qcert/`, `qjoint/`, ...) by
paths relative to the sprint's experiment folder. Those files are on the sprint branch, not in this
folder.

Each source folder's `SHA256SUMS.txt` lists one file that its repository copy does not contain:
`qcert/gen_certs.log`, `qcert3/s01_gen.out`, and `qcert4/CERTIFICATES_PARTIAL75_B4.json` (7.5 MB; it
excludes no claim). These files exist only in `~/xs-campaigns/2026-11-07-sprint/`. Every other listed
file verifies.

`README.md`, `PROVENANCE.md`, `checkers/CHANGES.md`, `verify_all.py`, `SHA256SUMS.txt`,
`combined/measurement/README.md` and `october-rows/PROVENANCE.md` were written for this package on
9 November 2026. `verify_all.py` follows the pattern of
`../mixcolumns-lb75/verify_all.py`.

## Combined state with the October 2026 rows (added 9 November 2026)

**October sources.** The push5/push6 rows are the author's (Joe Bachir) campaigns of 22-23 October
2026. They are unpublished working documents from the archive
`AES_DEPTH4_LOWER_BOUND_ATTEMPT_2026-10-23/AES_EXACT_MASK_SHARING_PUSH6_2026-10-23/`, imported into
`~/xs-campaigns/2026-11-07-sprint/import/zip/research/`. The documents the rows rest on are copied
verbatim to `october-rows/`, and every file matches the archive's `MANIFEST_SHA256.json`. Hashes are in
[`october-rows/PROVENANCE.md`](october-rows/PROVENANCE.md).

**Audits.** Two language-model audit agents worked on 2026-11-09, one after the other and
independently:

| Agent | Working directory | What it did |
|---|---|---|
| recon | `~/xs-campaigns/2026-11-09-phase/recon/` | Compared the conventions of the two campaigns. Followed every October row's proof. Recomputed the census and contact-pair facts with its own code and replayed the archive's own audits of F1, F2, F3, F5. Transcribed the rows (`push_rows.py`). Ran the LP scans (`combined_scan.py`: 686 / 509 / 419 / 280 and the ablations). Generated the 4,653 + 43 certificates and checked them against two matrix constructions. Wrote `ROW_INVENTORY.md` |
| recon-check | `~/xs-campaigns/2026-11-09-phase/recon-check/` | Wrote the independent checker `check_combined75.py`, with its own push-row transcription and the repository's sprint checkers; it passed twice. Reproduced 686 / 509 / 280 with its own LP scan (`scan.py`), and also the original campaign scans. Followed the proofs of every row the certificates use. Recomputed every finite fact behind the October rows (`finite_facts_check.py`). Repeated the real-circuit stress test with its own transcription |

**Files taken from the audits.**

| Here | Source | SHA-256 | Treatment |
|---|---|---|---|
| `combined/CERTIFICATES_COMBINED75.json` | `recon/CERTIFICATES_COMBINED75.json` | `9fc00ae3af30f6199c70720cb7b0c5a0b0cf86d7bcb6ee88c8b3ea140383edee` | byte-identical (matches `recon/SHA256SUMS.txt`) |
| `combined/CERTIFICATES_COMBINED75_J1FREE_ADDENDUM.json` | `recon/CERTIFICATES_COMBINED75_J1FREE_ADDENDUM.json` | `089a140177e82e1c0b19695f415b3a6d3f9ccabf93ba48c6dd434056f30c6d07` | byte-identical (matches `recon/SHA256SUMS.txt`) |
| `checkers/check_combined75.py` | `recon-check/check_combined75.py` | `d39893d4f11ce08b7a95e96f2f792b1bc906d9cd5aeb94ef2ffe6bc7398bcfd5` (original) | path edits, lines 32-34 (`checkers/CHANGES.md`) |
| `checkers/finite_facts_october.py` | `recon-check/finite_facts_check.py` | `c7d9bc075edf4a4bb38e285486fcc86adee91f9de599ea9bb068f1b9b531ee68` | renamed, byte-identical |
| `checkers/finite_facts_october.recorded.json` | `recon-check/finite_facts_check.json` | `a5deae2157f7941d99824686e59673caa42c13116455f4b67fe7b64a2f311357` | renamed, byte-identical |
| `combined/measurement/push_rows.py`, `combined_scan.py`, `compare_scans.json`, `scan_leaves.json`, `stress_push.json` | `recon/` | as in `recon/SHA256SUMS.txt` | byte-identical; records, not run |
| `combined/measurement/scan.py` | `recon-check/scan.py` | in `SHA256SUMS.txt` here | byte-identical; record, not run |
| `october-rows/ROW_INVENTORY.md` | `recon/ROW_INVENTORY.md` | `1816ceedad1798c1906ba1e8b80dcd72cec8625c105afb81d66210b7f44aff55` | byte-identical |

The two audit reports (`recon/REPORT.md`, `recon-check/REPORT.md`) and the audits' other files stay in
those directories and are not part of this folder.

## Review status

The finite computations replayed by `verify_all.py` are the certificate arithmetic and the case and
claim coverage of the four batches and of the combined certificates, and the finite facts behind the
October rows. The arguments of Addenda A-D and of the October documents were checked only by
language-model agents. The package lemmas and finite facts they use as black boxes were [read, not checked] by the
sprint. The finite facts S1, H1, H2, FM and J1 were computed by sprint programs that are not part of
this folder. No human referee has read this material, and nothing is formalized. **No lower bound
beyond 75 is claimed.**

## License

Covered by the repository's license (`../../LICENSE`).
