# AES MixColumns: the open cases of the 75-gate proof at G = 75

**Review package · 9 November 2026 · from the sprint of 7-8 November 2026**

**The lower bound stays 75.** This folder does not prove that 75 gates are impossible, and it
proves no bound above 75. It records a partial result inside the machinery of the
[75-gate proof](../mixcolumns-lb75/): of the 1,508 "oriented claims" that the proof's own inequality
rows leave open at G = 75, four batches of new rows, each proved in a written addendum and certified by
exact integer certificates, exclude 822. The open claims at G = 75 fall
1,508 -> 1,313 -> 996 -> 789 -> 686. With the author's October 2026 rows (push5/push6) added and
validated, 280 claims remain open (section below). Any one claim that remains open is enough to stop
the argument, so a smaller number of open claims is not a bound increase. Nothing here bears on whether a
circuit with 87 gates or fewer exists.

## Read

- [`PROOF_ADDENDUM.md`](addenda/PROOF_ADDENDUM.md) (Addendum A, batch 1),
  [`PROOF_ADDENDUM_2.md`](addenda/PROOF_ADDENDUM_2.md) (Addendum B, batch 2),
  [`PROOF_ADDENDUM_3.md`](addenda/PROOF_ADDENDUM_3.md) (Addendum C, batch 3),
  [`PROOF_ADDENDUM_4.md`](addenda/PROOF_ADDENDUM_4.md) (Addendum D, batch 4): the mathematics, in the
  notation of [`PROOF.md`](../mixcolumns-lb75/PROOF.md). Each file is the sprint's text unchanged
  except for one added first line that records where it came from.
- [`october-rows/`](october-rows/): the author's October 2026 working documents behind the push5/push6
  rows, verbatim, with [`ROW_INVENTORY.md`](october-rows/ROW_INVENTORY.md) and
  [`PROVENANCE.md`](october-rows/PROVENANCE.md).
- [PROVENANCE.md](PROVENANCE.md): sources, agents, dates and hashes.
  [checkers/CHANGES.md](checkers/CHANGES.md): the only edits made to the checkers.

## Check

Python 3.10+, standard library only. From the repository root:

```sh
python3 lower-bound-proofs/mixcolumns-lb75-open-cases/verify_all.py
```

It checks the SHA-256 of the certificate and checker files and works in a temporary copy. It runs the
four sprint checkers in order, then the independent checker of the combined certificates
(`checkers/check_combined75.py`), then the recomputation of the finite facts behind the October rows
(`checkers/finite_facts_october.py`). For each stage it checks the exit status, the stage's own pinned
counts and the key fields of its report. The finite-fact output must also equal the recorded run
`checkers/finite_facts_october.recorded.json`. Finally it checks across the five certificate files
that the excluded claims are pairwise disjoint. Logs go to `verification/run_<timestamp>/` (not
tracked). It ends with

```text
ALL CHECKS PASSED: 1,772 + 4,523 + 4,950 + 4,361 + 4,653 (+43) exact certificates; open claims at G = 75: 1,508 -> 1,313 -> 996 -> 789 -> 686 (sprint rows) -> 280 (with the October rows); finite facts of the October rows recomputed; the bound stays 75.
```

It took 85 s on 2026-11-09 on a machine under a load of about 20. The finite facts took 53 s, the
combined checker 11 s, and the four sprint checkers 0.7-8.9 s each (0.3-3.8 s on an idle machine). Do
not use `-O`: the checkers rely on assertions, and the wrapper refuses to run optimized.

## What the 75 proof leaves open at G = 75, and why

The 75 proof excludes a 74-gate minimum by showing that every one of 2,204 oriented claims (1,102
scalar profiles, two orientations) fails a final test, using local linear systems (L1)-(L23) on helper
type counts and exact Farkas certificates (PROOF.md, sections 10-11). The rows and lemmas do not
mention 74. The gate count G enters only through the scalar domain, two fan-out caps and the drift
budget `a + b + 2G - 192`, and that budget grows by 2 for each extra gate. At G = 74 the margin is
already thin: 1,307 of the 2,204 claims close only through `k + l > budget`, each with margin exactly 1.

At G = 75 there are 3,708 scalar states and 7,416 oriented claims. With the package's rows, the
package's own LP model leaves **1,508 claims open** (846 with even phase M, 662 with M<sup>T</sup>;
1,134 local systems stay LP-feasible). This is an LP measurement [measured], not a certified figure.
The package ships certificates for G = 74 only. A proof of 76 would therefore need certificates for all
7,416 claims at G = 75, including the 5,908 that the package rows exclude only by LP status today. The
certificate files here contain package-row certificates only where the coverage of the 822 newly
excluded claims needs them.

## What the four batches add

Each batch adds rows that every normalized circuit satisfies, proves them in an addendum that uses
the package's lemmas and finite facts as black boxes, and certifies the newly excluded claims with
exact integer Farkas certificates. Two programs check each batch: the generator's exact check and a
separately written standard-library checker with its own rows. The second program is the one included
here.

**Batch 1, Addendum A (`PROOF_ADDENDUM.md`).** Lemma N1: the represented edges of full helpers carry
pairwise distinct labels, so `3 n_3 <= x + y - q`. Lemma G\* extends the elimination of Lemma 10.2
with the short even+even gate equations. This gives `y -> y_2` in the quotient rows and the new rows
(L7\*), (L12\*), (I) and (Q0). Lemma S, with finite fact S1, restricts the labels of helpers with
r >= 2 to "rich" boundary pairs. It is structural and kills nothing at G = 75.

**Batch 2, Addendum B (`PROOF_ADDENDUM_2.md`).** Finite fact H1 and Lemma H1 bound a hub helper:
with A the number of missing labels that meet a full helper, every helper with r <= 2 has
`u_i <= 4 + (q - A)`. This is used as an exact case split on A. The dark-label split re-derives the
quotient rows (L13)-(L18) with the dark count `q_D` kept (Lemma D1) and adds occurrence budgets
(Lemma D2), split exactly over `q_D = 0..q`. Lemma O1 (every full helper defines at least two distinct
outputs) is proved but never bounds the number of full helpers.

**Batch 3, Addendum C (`PROOF_ADDENDUM_3.md`).** Finite fact H2: under the independence condition
(C1), a hub's capacity is exactly `3 - r`, not 4. Lemma H2 and row HUB2, `u_i <= (3 - r_i) + (q - A)`,
replace H1. The packing rows PK4 and PK5 apply Lemma 10.4's argument at q = 4, 5. Rows FM7 and FM9
come from finite fact FM, the ranks of the labels a full helper can meet.

**Batch 4, Addendum D (`PROOF_ADDENDUM_4.md`).** Lemma J: the gate-equation families of several hubs
are jointly independent, with a spanning tree of mixed vectors at a shared hub-only label. By finite
fact J1, two limit hubs (r + m = 3) never share a missing label. Lemma P gives five label-class rows
P1-P5 in each exact hub case A = a, using the packing bound D(n) proved there. Row LIM rests on J1.
The hub split becomes the exact integer split A = 0..q for every q.

| Batch | Addendum | Open before | Newly excluded (M / M<sup>T</sup>) | Open after | Exact certificates | Per-case certificates | Coefficients checked |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | A | 1,508 | 195 (122 / 73) | 1,313 | 1,772 | n/a | 53,917 |
| 2 | B | 1,313 | 317 (220 / 97) | 996 | 4,523 | 2,497 | 192,917 |
| 3 | C | 996 | 207 (88 / 119) | 789 | 4,950 | 2,925 | 251,213 |
| 4 | D | 789 | 103 (44 / 59) | 686 | 4,361 | 3,506 | 264,062 |

Each certificate file can be checked on its own: it contains every certificate that its claims'
coverage needs, including package-row and earlier-batch certificates. In every file the largest
weighted right-hand side is -1. The 195 + 317 + 207 + 103 = 822 excluded claims are pairwise disjoint,
and `verify_all.py` checks this.

The "open before / after" columns are LP-status counts that the generators recorded [measured].
`verify_all.py` checks that they chain consistently (before minus excluded equals after), but it does
not certify them. The certified content is the exclusion of the 822 claims. Within batch 3, HUB2 alone
gives 996 -> 863, and PK4/PK5 then give 789.

## What rests on finite fact J1

Row LIM enters 78 of the 4,361 batch-4 certificates, all in the hub case a = q - 1. Only the hub-only
part (J1b) of J1 therefore carries weight. Without J1, 297 of the 375 keys killed in batch 4 and 65
of its 103 claims are still covered. **38 of the 103 batch-4 claims rest on J1.** J1 was
finite-checked by two implementations: qjoint `qj_limit.py`, and qjointcheck `jc_geo.py` in two modes
without the Lemma-4.6 pre-skips, with identical configuration counts. Neither program is in this
folder, and the batch-4 certification read their logs without re-running them. `check_cases4.py`
checks the counts `certificates_using_J1 = 78`, `claims_covered_without_J1 = 65` and
`killed_keys_covered_without_J1 = 297`.

The combined state below adds no dependence on J1. Its 406 exclusions are certified without row LIM,
and its LP count of 280 is the same without LIM. The 38 batch-4 claims above are still certified only
through J1: they have not been re-certified with the October rows and without LIM.

## Trust ledger

| Statement | Status |
|---|---|
| Package Lemmas 1.1-10.4, Propositions 8.4, 9.2, 11.1, finite facts F1-F14 | Relied on as black boxes [read, not checked by the sprint]; the package's own `verify_all.py` replays its finite facts and certificates |
| Lemmas and rows of Addenda A-D (N1, G\*, (L7\*), (L12\*), (I), (Q0), S, H1, D1, D2, O1, C1, H2, HUB2, PK4/PK5, FM7/FM9, J, P1-P5, D(n), LIM, the exact splits) | Proved in the addenda; each confirmed step by step by a separate checking agent (qcheck, qrealcheck, qhubcheck, qjointcheck) [proved; language-model review only] |
| Finite facts S1, H1, H2, FM, J1 | Finite-checked by two or more programs in the sprint folders; their values enter the checkers here as written-out constants and are not recomputed by `verify_all.py` [finite-checked elsewhere] |
| 1,772 + 4,523 + 4,950 + 4,361 certificates; coverage of the killed keys and of the 822 claims | Exact integer arithmetic, replayed by `verify_all.py` [certified] |
| October rows (push5 P5.1-P5.8; push6 resources R1-R6, budgets B1-B6, divisor rows D) | Proved in the author's October 2026 working documents ([`october-rows/`](october-rows/)); each proof followed step by step by two agents (recon, recon-check), independently, with no gap found [proof followed; language-model review only] |
| Finite facts of the October rows (census 440 / 616, core 20 / 28, classes, contact pairs, dim R10(M<sup>T</sup>) = 29, the archive's facts F1, F2, F3, F5) | Recomputed by `checkers/finite_facts_october.py` in every `verify_all.py` run [finite-checked here]; also by the archive's own audits (replayed by recon) and, for the census facts, by recon's code |
| 4,653 + 43 combined certificates; coverage of the 406 further claims | Exact integer arithmetic, replayed by `verify_all.py` with `checkers/check_combined75.py`, which transcribes the October rows itself [certified] |
| 1,508 / 1,313 / 996 / 789 / 686 / 280 open; keys still LP-feasible | LP status [measured]; 509, 686 and 280 reproduced by two independent scans; never a premise |
| Zero violations of the new rows on real circuits | Positive controls run once (below), not a proof |

An LP solver's status is never a premise. An optimizer was used only to find multipliers, and every
multiplier is checked exactly. A time limit is not a result: a case that timed out is open.

## What remains open

This section describes the sprint rows alone. With the October rows added, 280 claims remain open;
see the section on the October 2026 campaigns below.

**686 oriented claims (372 M, 314 M<sup>T</sup>) remain open at G = 75 by LP status.** Their shortfall
`budget - (k + l)` is 0 for 382 of them, 1 for 221, 2 for 59 and 3 for 24. The final scan has 814
LP-feasible keys, 483 of them load-bearing.

The survivors are of four kinds. First, q = 5-6 keys whose configurations have limit hubs together
with sub-limit partners, or no hub that is forced to meet a full helper. Second, q = 2-3 keys with
many full helpers. Third, M<sup>T</sup> keys with small h and q = 7-8. Fourth, 101 keys that are
LP-feasible but were found integer-infeasible (see below).

The fourth kind is not certified, and it is a measurement. The 101 keys come from the 551
load-bearing keys before batch 4, classified by a MILP oracle with a 20 s limit whose status was not
recorded, so a timeout may have been counted as "infeasible". Excluding them would need
branch-and-bound certificates. How many of the 101 survive batch 4 is not recorded.

Two finite label-sharing enumerations were specified and not run: M<sup>T</sup> q = 1 with 7-8 full
helpers, and M q = 2 with ten.

The batch-4 generator also produced 22,586 certificates for killed cases of surviving keys
(`CERTIFICATES_PARTIAL75_B4.json`, 7.5 MB). They exclude no claim and are not included here, so the
checker's optional `partial_*` counts are not replayed.

## Positive controls and other checks (run once, not portable)

Each batch's folder holds further evidence that cannot run from this repository. The stress
extensions (`stress_ext.py`, `stress_ext2.py`, `stress_ext3.py`, `stress_ext4.py`) import the package
copy, the bridge reconstruction and the 303 real circuits from `~/xs-campaigns/2026-11-07-sprint/`.
The cross-checks need the generators and, through them, NumPy/SciPy.

| Batch | Stress extension (13 controls + 303 real circuits) | Mutation tests (all rejected) | Generator vs checker matrices |
|---|---|---|---|
| 1 | 1,264 phases, 0 violations | 7,225 negated multipliers, 195 dropped certificates, 390 loosened claims | identical on 2,562 keys |
| 2 | 1,264 phases, 0 violations | 26,724 negated, 300 dropped cases, 317 dropped certificates | identical on 23,593 nodes |
| 3 | 1,264 phases, 0 violations; 1,897 synthetic maximal configurations | 28,530 negated, 348 dropped case certificates, 207 dropped referenced certificates | identical on 24,790 nodes |
| 4 | 1,264 phases, 0 violations; 102,792 synthetic two-hub phases | 26,272 negated, 375 dropped case certificates, 103 dropped referenced certificates | identical on 22,301 nodes |

The recorded outputs are in the sprint's experiment folders, `research/sprint-2026-11-07/experiments/qcert*/`
on the branch `sprint-2026-11-07-linear-maps` (`stress_ext*.json`, `mutate*.json`, `s0*_*.out`,
`run_all.log`), together with the batch reports (`REPORT.md`) that the addenda cite. They are positive
controls: real circuits satisfy the rows. They are not a substitute for the proofs.

The October rows were checked the same way, twice, with two transcriptions: recon's `stress_push.py`,
recorded in [`combined/measurement/stress_push.json`](combined/measurement/stress_push.json), and
recon-check's `stress_mine.py`. Both found 0 violations on 1,264 phases of 316 circuits, with each
circuit's own G in the constants that contain x. Every known phase has A = 0 and q >= 7, so the region
where the combined certificates work (A > 0, q <= 6) is not exercised by any real circuit.

## Relation to the October 2026 campaigns (push5/push6, 509 open claims)

The author's October campaigns push5 and push6 (22-23 October 2026) attacked the same 1,508 open claims with different rows, and left 509 open (1,508 -> 810 -> 509, with exact certificates that the sprint replayed). The rows come from a complete census of "repeated" helpers (helpers with two or three represented incidences; they can take only 440 values for M and 616 for M^T, their output anchors lie in a core of 20 / 28 outputs, and each belongs to one output-bit class), from birth-ownership counting over those helpers, from the count p of "repeated-bright" missing labels coupled to the H-H structure of M^T (the "exceptional label" theorems), and from rounded class rows. Their proofs are the author's working documents, copied verbatim to [`october-rows/`](october-rows/) with their provenance; the row definitions the certificates use are `model_full_cuts.py` of push5 and push6 there ([`october-rows/push5/global_chronology/model_full_cuts.py`](october-rows/push5/global_chronology/model_full_cuts.py), [`october-rows/push6/global_chronology/model_full_cuts.py`](october-rows/push6/global_chronology/model_full_cuts.py)). [`october-rows/ROW_INVENTORY.md`](october-rows/ROW_INVENTORY.md) lists every row with its statement, proof file, finite facts and status.

Reconciliation (9 November 2026, two independent audits). Both campaigns use the same scalar domain (3,708 states, 7,416 oriented claims), the same key convention (h, y, F, orientation, q, z), the same helper types (r, u, v) with the same meanings, and the same package base rows (the `certify75.py` the October code imports is the package's, by SHA-256). The only row both have is Lemma N1 (push5's "distinct represented labels" row). Every October row is stated on the type counts alone, so it can be appended to every case system of the sprint's batch 4 with zero coefficients on the auxiliary columns; the combined systems are still relaxations of every normalized circuit. Each row's written proof was followed step by step by two agents, independently, with no gap and no mismatch between the proved statement and the coded coefficients, constants (q - 1 for M^T with z <= 2; q - 2 for M^T with z = 0 and q <= 6) and scopes found. Every finite fact the proofs cite was recomputed by two independent standard-library programs, one of which is included here and run by `verify_all.py` ([`checkers/finite_facts_october.py`](checkers/finite_facts_october.py); the archive's facts F1, F2, F3, F5 are not the package's F1-F14). All rows hold with zero violations on the 1,264 real-circuit phases (positive control; the configurations the rows bite on, A > 0 and q <= 6, occur in no known circuit).

Result [measured, LP status]: sprint rows alone 686 open claims; October rows alone 509 (reproduced exactly, with the archive's bounds); intersection 419; **combined 280 (148 M, 132 M^T)**. 139 claims die only in the combination. Ablations: sprint + push5 only 400, sprint + push6 only 282; sprint rows plus only the October rows whose finite facts need no large enumeration, 581. The 406 claims excluded beyond the sprint's 686 are **[certified]**: 4,653 exact integer Farkas certificates over 3,863 keys (plus 43 that re-cover the 4 claims whose coverage touched the one certificate using row LIM), largest weighted right-hand side -1, verified by the generator's matrix and by the independently written checker [`checkers/check_combined75.py`](checkers/check_combined75.py) (its own transcription of the October rows, the repository's sprint checkers for the sprint rows). Nothing in these 406 exclusions rests on finite fact J1, and the combined LP count is 280 with or without row LIM; the 38 batch-4 claims of the sprint chain that rest on J1 keep their batch-4 certificates.

What remains: 229 load-bearing keys with q = 3..9 (87 at q = 5) and z <= 4; of their 9,432 case leaves 572 are LP-feasible, concentrated at hub cases A = 2..4 (380 of 572) and at no dark label (481 of 572; 340 leaves have both): aggregate profiles in which two to four missing labels meet full helpers and no label is dark, a region no real circuit occupies. 196 of the 280 open claims have shortfall 0. **The lower bound stays 75.** Only zero open claims would feed the proof's final argument; the 280 are counts of what the local LP relaxations do not exclude, and an exact (integer, graph-aware) treatment could only lower them.

The certificates and the two checker programs are in [`combined/`](combined/) and [`checkers/`](checkers/). The LP scans and stress controls that produced the counts above are kept in [`combined/measurement/`](combined/measurement/) as records. They need SciPy and the sprint generators, and `verify_all.py` does not run them.

## Folder map

| Path | Purpose |
|---|---|
| `addenda/` | Addenda A-D, verbatim plus one provenance line each |
| `certificates/` | The four certificate files, byte-identical to the sprint's |
| `checkers/` | `check_ext75.py`, `check_cases75.py`, `check_cases3.py`, `check_cases4.py`, `check_combined75.py` (path edits only, see `CHANGES.md`); `check_cases3_copy.py`, the unmodified copy that `check_cases4.py` imports; `finite_facts_october.py` (unchanged, renamed) and its recorded output `finite_facts_october.recorded.json` |
| `combined/` | The combined certificates `CERTIFICATES_COMBINED75.json` (4,653) and `CERTIFICATES_COMBINED75_J1FREE_ADDENDUM.json` (43), byte-identical to the audit's |
| `combined/measurement/` | LP-status measurements and stress controls (`push_rows.py`, `combined_scan.py`, `scan.py`, `compare_scans.json`, `scan_leaves.json`, `stress_push.json`); they need SciPy and the sprint generators and are **not run by `verify_all.py`** (see its `README.md`) |
| `october-rows/` | The author's October 2026 documents behind the push5/push6 rows, verbatim, in their archive layout; `ROW_INVENTORY.md`; `PROVENANCE.md` |
| `verify_all.py` | Runs the five checkers, the finite-fact recomputation and the cross-file checks |
| `PROVENANCE.md`, `SHA256SUMS.txt` | Sources and hashes of this folder's files |

## Review status

The checkers replay the certificate arithmetic and the case and claim coverage, and one program
recomputes the finite facts behind the October rows. They do not check the arguments. Those include
that the new rows hold in every normalized circuit, the independence lemmas behind H2 and J, the
elimination arguments behind the October exceptional-label rows, the exhaustiveness of the case splits,
the soundness of appending the October rows to the sprint's case systems, and the package's own
reductions. Those arguments are for expert review. The sprint work and the October documents were
developed with language-model agents under the author's direction. Every sprint lemma was checked by a
second agent, and every October row's proof was followed by two audit agents. There has been no human
peer review and no formalization. **The lower bound stays 75. With the sprint rows 686 claims remain
open at G = 75; with the October rows added, 280.**
