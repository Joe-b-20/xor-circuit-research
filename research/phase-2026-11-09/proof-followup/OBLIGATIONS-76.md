# What a bound of 76 would require, and where each obligation stands

Phase 2026-11-09, proof follow-up, 2026-11-11. **The lower bound is 75.** This file is an accounting of
obligations, not a claim. A statement "L(M) >= 76" needs all of: (i) the framework of the 75 proof
applied validly at G = 75, (ii) every oriented claim of the G = 75 domain excluded by valid necessary
conditions, (iii) every exclusion checked independently. Tags: [proved], [certified] (exact integer
certificates, two programs), [finite-checked], [measured] (solver status), [read, not checked].

## 1. The domain, by identifier

The final test of PROOF.md section 11 at G = 75 ranges over 3,708 scalar states and 7,416 oriented
claims. `scope/domain_accounting.py` and `package75/check_pkg75.py` enumerate the domain themselves and
compare claim identifiers (state tuple, orientation), not totals:

| set | claims | status of the exclusion | where |
|---|---:|---|---|
| excluded by the package rows (L1)-(L23) alone | 5,908 | **[certified] as of 2026-11-11**: 15,742 exact Farkas certificates, complete key coverage, largest weighted right side -1 (section 2) | `package75/` |
| sprint batch 1 (Addendum A) | 195 | [certified] | published folder, `certificates/CERTIFICATES_EXT75.json` |
| sprint batch 2 (Addendum B) | 317 | [certified] | `CERTIFICATES_CASES75.json` |
| sprint batch 3 (Addendum C) | 207 | [certified] | `CERTIFICATES_CASES75_B3.json` |
| sprint batch 4 (Addendum D) | 103 | [certified]; 38 of them only through finite fact J1 | `CERTIFICATES_CASES75_B4.json` |
| sprint + October rows combined | 406 | [certified], J1-free | `combined/CERTIFICATES_COMBINED75.json` |
| open | 280 | LP status [measured] | `scope/coverage_manifest.json` |
| **total** | **7,416** | the seven sets are pairwise disjoint and their union is the domain [checked by identifier] | |

"Certified" means: for each claim, every local system below its stated bounds (k, l) has an exact
nonnegative-integer certificate (or is excluded directly by (4.4) or Lemma 10.3), and the final test
fails at (k, l). It certifies the arithmetic and the coverage, not the lemmas behind the rows.

## 2. The package's 5,908 exclusions at G = 75 (new today)

The package ships certificates for G = 74 only; at G = 75 these 5,908 claims were excluded by LP
status. `package75/gen_pkg75.py` repeats the package's generator on the G = 75 domain (the local
systems `certify75.system(key)` do not depend on G): 15,742 certificates, 0 uncertified keys, 21 s.
`package75/check_pkg75.py` (standard library; rows re-typed from the lb76 transcription `lp_regen.rows_for`,
not from the generator's `certify75.system`; own domain enumeration) verifies every certificate exactly
(827,190 column coefficients), the coverage of every excluded claim (33,536 certificate references),
the failure of the final test, and the identifier accounting above. Mutation tests: a zeroed weight, a
dropped referenced certificate (5 of 5), a loosened bound, an open claim marked excluded and a dropped
claim are all rejected. Regenerating these certificates removes a mechanical gap only; it does not by
itself connect the package's argument to G = 75 (section 3).

## 3. Inherited lemmas: what must hold at G = 75 [read, not checked]

PROOF.md proves "L(M) is not 73 and not 74" (Proposition 11.1) and words sections 10-11 for "G is 73
or 74". The extension uses the same chain at G = 75. Each link below is used as a black box by the
sprint addenda, the October rows and everything in this folder; none has had a fresh mathematical
review at G = 75. The sprint's lb76 report read them and judged that they "carry over verbatim; no
premise has to be re-proved for G = 75, only applied"; that is one agent's reading.

| link | statement used | how G enters | needed review |
|---|---|---|---|
| Lemma 1.1, sections 2-4 | normalization; x >= 24; odd graph; Lemmas 4.1, 4.4-4.7; finite facts F1-F14 | not at all | none specific to 75; the package's own review status applies |
| Sections 6-8 | origin identity; Lemma 7.4 (r + u + v >= 3 in a canonical transpose); potential e; Lemmas 8.2, 8.3 | 8.2 and 8.3 contain G explicitly (`s + 96 - G + x - 2x'`; drift `k + l + 192 - 2G - a - b`) | that a MINIMUM circuit with 75 gates has the orbit of canonical transposes with the same properties (uses L(M) >= 75, now proved, in place of L(M) >= 73/74) |
| Lemma 9.1 | the tail: y constant on even phases, nondecreasing on odd ones; fixed count profiles | through h_e = G - 32 - a - Y, h_o = G - 32 - b - V | that the steady regime argument does not use G <= 74 |
| Section 11, scalar domain | admissible profiles; caps S_e, S_o with the Lemma 8.2 terms; lower bounds l(h, y) | ranges of a, b, Y, V; the two caps; the budget a + b + 2G - 192 | that the caps "at G = 74 also" hold at G = 75 by the same derivation |
| Lemma 10.1, rows (L1)-(L23) | every phase of the tail satisfies its local system over types with r + u + v >= 3 | the rows contain no G; the column set uses Lemma 7.4 | that no row's proof uses G <= 74 (section 10 opens with "From now on G is 73 or 74") |
| Lemma 10.3, (4.4) | direct exclusions (q = 0 cases; incidence test) | none in the code | as for 10.1 |
| Proposition 11.1 | if every oriented claim fails the final test, e is unbounded, contradiction | budget | the proof text with G = 75 |

Obligation O1: an independent mathematical review of exactly these links at G = 75, by someone other
than the agents that produced the extension. Until then every exclusion at G = 75 is conditional on
"the framework applies at G = 75".

## 4. Dependencies of the certified exclusions beyond the package

| exclusions | rest on | review status |
|---|---|---|
| 822 (sprint) | Addenda A-D: N1, G*, (L7*), (L12*), (I), (Q0), S, H1, D1, D2, O1, C1, H2, HUB2, PK4/PK5, FM7/FM9, J, P1-P5, D(n), LIM, the exact splits on A and q_D; finite facts S1, H1, H2, FM, J1 | each lemma checked step by step by a second language-model agent; finite facts by two or more programs; no human review; 38 claims need J1 |
| 406 (combined) | the above plus the October rows (push5 P5.1-P5.8, push6 R1-R6, B1-B6, D) and their finite facts (census 440/616, core 20/28, classes, contact pairs, dim R10 = 29, archive F1-F3, F5) | proofs are the author's working documents, followed by two audit agents; finite facts recomputed by `verify_all.py`; no human review |
| 5,908 (package rows) | (L1)-(L23) only | the package's own review status |

Obligation O2: human or formal review of the addenda and the October rows.

## 5. The 280 open claims

See [MANIFEST.md](MANIFEST.md). Closing them means excluding, for each claim, every LP-feasible key of
one of its ladders up to the level where the final test fails: 4,223 keys and 68,153 open leaves stand
in the ladders in total, of which 1,637 leaves are integer-infeasible [measured]. No hub-case
enumeration covers them (88 claims live on A = 0 configurations). Obligation O3: exclusions for all of
them by valid necessary conditions, each certified or finite-checked by two implementations.

The pilot ([PILOT.md](PILOT.md)) tests one route on the smallest family (M^T, q = 3). Its exclusions
are at [finite-checked] or [measured] grade and do not change the count of open claims in this file
until they are certified and reviewed.

## 6. What is NOT an obligation any more, and what stays unresolved

- The M^T q = 1 and M q = 2 enumerations: no live key (MANIFEST section 5).
- The 101 MILP-classified keys of the sprint: unresolved, never used, none at a first level.
- The September "76 extension" package: not in the archive; not judged.

## 7. Summary

| obligation | state |
|---|---|
| O0 domain accounted by identifier | done [checked] |
| O0' certificates for the package-row exclusions at G = 75 | done [certified], 2026-11-11 |
| O1 the framework applies at G = 75 | open: read by one agent, not independently reviewed |
| O2 review of Addenda A-D and the October rows | language-model review only |
| O3 the 280 open claims | open |
| bound | **75** |
