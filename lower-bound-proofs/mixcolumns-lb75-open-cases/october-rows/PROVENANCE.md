# Provenance of the October 2026 row documents

**Author:** Joe Bachir. **Dates:** 22-23 October 2026 (campaigns push5 and push6).
**Status:** unpublished working documents. The row definitions that the certificates use are
`model_full_cuts.py` of push5 and push6 (`push5/global_chronology/model_full_cuts.py`,
`push6/global_chronology/model_full_cuts.py`).

The files below are copied verbatim from the author's archive
`AES_DEPTH4_LOWER_BOUND_ATTEMPT_2026-10-23/AES_EXACT_MASK_SHARING_PUSH6_2026-10-23/`, as imported into
`~/xs-campaigns/2026-11-07-sprint/import/zip/research/`, and keep their paths inside it. Every file's
size and SHA-256 equal the archive's own manifest `MANIFEST_SHA256.json` (checkpoint
`AES_EXACT_MASK_SHARING_PUSH6_2026-10-23`, model version `push6-core-rounded-overload-p-capacity-v4`).
The documents were developed with language-model agents under the author's direction, like the rest of
the archive. The file set is the one named by `ROW_INVENTORY.md`, plus the two
`SCAN_AND_CERTIFICATE_STATUS.txt` files and `push5/global_chronology/FULL_HELPER_CYCLE_CUT.txt`.

| File (archive path) | Bytes | SHA-256 |
|---|---:|---|
| `push5/global_chronology/model_full_cuts.py` | 3,841 | `6df99c1b86543ac0e58504ef5b10795cd2b45e9383ff8764f9632f528008ab1f` |
| `push5/global_chronology/HH_DEGREE_REALIZABILITY.txt` | 2,371 | `5a1afc6222b2aa5436153c19e6c0fc734abfa050641d8a6b95050cbdbb47f863` |
| `push5/global_chronology/FULL_HELPER_CYCLE_CUT.txt` | 10,871 | `8e13a9c3acff95081d33b7dfa3233d9f1bd0b7f33d21ba914217478b0909b8b0` |
| `push5/global_chronology/SCAN_AND_CERTIFICATE_STATUS.txt` | 13,108 | `492ccde5284cb37eca0c7114c64f32efedb32f25c764ddec47abade831e2f283` |
| `push5/odd_spine/FULL_HELPER_LABEL_OWNERSHIP_INDEPENDENT.txt` | 12,431 | `eafad6ef897a2622c19d1909e04b6561a521d1452d8146ec063670aa914d07d7` |
| `push5/odd_spine/EXCEPTIONAL_LABEL_LOGIC_INDEPENDENT_AUDIT.txt` | 13,907 | `fd2daddc632d37f310771513427a64cdd8c721f882e237d4552c75458a3c7e58` |
| `push5/even_frontier/EE_QUOTIENT_CHARGE_THEOREM.txt` | 21,965 | `b2e8117cbd97bc410a30daf5ca075c981f5029c03096fd742dd14657b4179051` |
| `push6/global_chronology/model_full_cuts.py` | 4,852 | `be8ad588b6ef4b0ee2cac3ee36db61f6d901f68f0dcf28df793a07e4f3f4cadf` |
| `push6/global_chronology/REPEATED_CONTACT_CORE_PROOF.txt` | 8,232 | `842229ab1dd18bbd21dd434df12186d51ed1ebccd109400c8aa9f0f08acd2a99` |
| `push6/global_chronology/ROUNDED_CLASS_CORE_PROOF.txt` | 5,693 | `5eb9c90a230b38c6d3a1d3708beded82d0163e13e2d962d1f0494c4ebf0a31cc` |
| `push6/global_chronology/P_COUPLED_RESOURCE_ROWS.txt` | 5,188 | `486fc94a38f73dc078659a618669ac426893d2d884a223f67470d5b8587dd55d` |
| `push6/global_chronology/SCAN_AND_CERTIFICATE_STATUS.txt` | 10,931 | `e15c58030806b2a2f9028bd9fb6c185db36ae3e08e67c4eeb2d109662816cb1b` |
| `push6/root/LOCALIZED_SHARING_THEOREM.txt` | 5,177 | `1aa4ebd2d44bf9c011a69fa3d4084bab9aaa54cf947e146fc6b1573a98b0b6b6` |
| `push6/even_frontier/HH_EXCEPTIONAL_LABEL_BUDGET.txt` | 10,353 | `f473f4931ac4733c4dfcff48e3c489c290bdb675d3880d0d28422777ceab8bcb` |
| `push6/even_frontier/HH_LABEL_MATCHING_REFINEMENTS.txt` | 10,652 | `32fa78dec3946366ccea29a945408362697afe9f5d4b00712e1f56edf7fa4984` |
| `push6/even_frontier/FULL_PAIR_HH_ZERO_QUOTIENT.txt` | 7,802 | `987077b978d62c4897bb98bb07e705e86a78deec3302ea89bcf351a347425de0` |
| `push6/odd_spine/PUSH6_INDEPENDENT_LOGIC_AUDIT.txt` | 17,965 | `df1cabab96218c762cb44e15715a620e1d084ec4cfd72f9b81937b09bf9d6687` |

The two `model_full_cuts.py` files import programs that are not in this folder, among them the
package's `certify75.py`. The archive copy lacks that file, but the archive manifest records its
SHA-256 as `11f36227e4e5487ba9e83816f7ca2f23808daf08747975ec580f2d7c6a82b0eb`, which equals the
package's. These files are records of the row definitions and are not run from here. The checker
`../checkers/check_combined75.py` transcribes the rows independently, and both audits found that
transcription identical to these generators.

`ROW_INVENTORY.md` was written by the recon audit agent on 2026-11-09. It is copied verbatim from
`~/xs-campaigns/2026-11-09-phase/recon/ROW_INVENTORY.md` (SHA-256
`1816ceedad1798c1906ba1e8b80dcd72cec8625c105afb81d66210b7f44aff55`). Its "not recomputed by me" labels
on the facts F1, F2, F3 and F5 describe the recon agent's own code. The recon-check agent later
recomputed those facts with its own code, and that program is `../checkers/finite_facts_october.py`.
The archive paths in the inventory are relative to the archive root, which is this folder's layout.
