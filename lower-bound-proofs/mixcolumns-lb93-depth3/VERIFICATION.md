# Verification report

**Result: PASS.** The complete inherited verification was rerun on
23 October 2026, including the earlier finite premises. It confirmed
the depth-three lower bound of **93 gates**, the **97-gate** upper-bound
construction, and **zero uncovered cases** in the final exclusion.

## Command and runtime

The executed command was:

```bash
python3 verify_complete_92_exclusion.py --full
```

It ran from a fresh extraction of the corrected source archive and exited
with code zero. Elapsed time was approximately **16 minutes 39 seconds**
(998.749 seconds). The environment used Python 3.12.14 and g++ 13.3.0 on
64-bit Linux. Verification needs no numerical optimization package or
network access.

The full technical dependency set included in this standalone package was
then checked against the files actually audited: **all 1,186 technical files
were byte-identical**, with matching SHA-256 hashes. Compressing those files
into `technical.tar.xz` does not change the proof inputs. The package wrapper adds
integrity checking, safe extraction, an isolated temporary working directory,
and result capture.

The complete log and fresh machine-readable records are in:

`verification/fresh_audit_2026-10-23/`

The summary is `summary.json`; the detailed execution log is
`full_verification.log`. Log SHA-256:

```text
76dcd41677d3848c47bb2e456bc8dff26c6137ba47b169e4d1ef34f976b642e2
```

## What was freshly checked

| Check | Result |
|---|---|
| AES target reconstruction, local support facts, and construction controls | PASS |
| Boundary-pair finite case table and weighted cluster minima | PASS |
| Pair-graph component bound and complete proof of `P >= 26` | PASS |
| All finite premises of the 16,868-row frozen source certificate | PASS |
| Exact tradeoff `4H - P >= 214`, including the full coefficient correction | PASS |
| Eight-component partition generation, tree prices, and pair exclusions | PASS |
| All 17 single-component certificates | PASS |
| Complete six- and seven-component partition regeneration | PASS |
| All retained conditional parent-tree prices | PASS |
| All 1,113 exact partition Farkas certificates | PASS |
| All 20,933 forest obstructions in the final replay | PASS |
| All 710 seven-component pair-recipe representatives | PASS |
| Exact final coverage union and 97-gate/depth-three witness | PASS |

The full source-certificate replay checked eight local price certificates,
1,312 construction-consistency rows, 192 parent-forest rows, 58 label-priced
tree rows, 22 recipe-coupled cluster rows, and 28 edge-priced tree rows, in
addition to the foundational rows. Both the 97-gate control and the included
100-gate control with exactly 26 pairs satisfied all regenerated rows using
their actual ancestries.

## Final coverage

| Components | Partition universe | Disjoint exclusion accounting | Uncovered |
|---|---:|---|---:|
| 6 | 275,354 | 271,718 forest + 3,636 Farkas | 0 |
| 7 | 22,060 | 18,404 parent-price + 2,840 pair-recipe + 816 Farkas | 0 |
| 8 | 110,712 | 1,552 parent-price + 109,160 pair-recipe | 0 |

Another 96 six-component partitions have parent-price exclusions that
overlap the Farkas exclusions; they were checked but are not added again.
The final checker operates on canonical partition sets and verifies the
union's coverage, rather than merely adding reported counts.

For the six- and seven-component universes, fresh independent Python
regeneration matched the complete archived C++-generated partition sets.
For the eight-component branch, the full fresh partition generation and
complete exclusion passed; the original separate Python/C++ cross-check
record is also preserved as `verification/original_corrected_partition_crosscheck.json`.

All finite searches used as exclusions completed. No timeout, incomplete
search, or `UNKNOWN` result was interpreted as a contradiction.

## Evidence that this was a complete replay

The fresh final result records:

```json
{
  "status": "PASS",
  "new_lower_bound": 93,
  "known97_rechecked": true,
  "reused_completed_checks": false,
  "source_certificate_checker_rerun": true,
  "exact_optimum": "UNRESOLVED"
}
```

Some inherited result fields describe earlier lemmas as "previously verified"
because those strings are part of the original checker. In this run, the
`--full` command did rerun those finite premises; the separate fresh stage
records and the detailed log show their successful replay.

The package's 26 retained Python modules also passed syntax and import
checks, which did not detect four inherited modules missing from
`technical.tar.xz`; those are supplied from `supplement/` (see
`supplement/README.md`). The wrapper rejects optimized Python mode, which
would disable the assertions used by the proof checkers. Integrity and packaging checks are
separate from the mathematical proof replay.

## Review boundary

This report establishes that the supplied exact finite checks and certificate
arithmetic passed in the stated environment. The normal-form argument,
validity of the inequalities, completeness of the enumerators, and their
implementations are provided for independent mathematical and software
review. The report is not an external referee opinion or a proof-assistant
formalization.

The supported interval is **93 through 97** at depth at most three. It does
not establish which of those five gate counts is optimal, and it gives no
93-gate lower bound for circuits of greater depth.
