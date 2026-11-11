# The G = 75 domain: what is excluded, what is open, and what a bound of 76 would still require

**11 November 2026. The lower bound is 75.** This file is an accounting of obligations, not a claim.
A statement "L(M) >= 76" would need all of: (i) the framework of the [75 proof](../mixcolumns-lb75/)
applied validly at G = 75, (ii) every oriented claim of the G = 75 domain excluded by valid necessary
conditions, (iii) every exclusion checked independently. None of the three is complete.

Tags: [certified] exact integer certificates checked by a separately written program; [checked]
compared by identifier by `verify_all.py`; [measured] a solver status; [read, not checked].

## 1. The domain, by identifier

The final test of `PROOF.md` section 11 at G = 75 ranges over 3,708 scalar states and 7,416 oriented
claims. `package-rows-g75/check_pkg75.py` enumerates the domain itself, and `verify_all.py` compares
claim identifiers (state tuple, orientation), not totals:

| Set | Claims | Status of the exclusion | Where |
|---|---:|---|---|
| excluded by the package rows (L1)-(L23) alone | 5,908 | [certified] since 2026-11-11: 15,742 certificates | `package-rows-g75/` |
| sprint batch 1 (Addendum A) | 195 | [certified] | `certificates/CERTIFICATES_EXT75.json` |
| sprint batch 2 (Addendum B) | 317 | [certified] | `certificates/CERTIFICATES_CASES75.json` |
| sprint batch 3 (Addendum C) | 207 | [certified] | `certificates/CERTIFICATES_CASES75_B3.json` |
| sprint batch 4 (Addendum D) | 103 | [certified]; 38 of them only through finite fact J1 | `certificates/CERTIFICATES_CASES75_B4.json` |
| sprint rows and October rows combined | 406 | [certified], J1-free | `combined/CERTIFICATES_COMBINED75.json` |
| open | 280 | no certificate [checked]; LP-feasible under all published rows [measured] | `package-rows-g75/published_sets.json` |
| **total** | **7,416** | the seven sets are pairwise disjoint and their union is the domain [checked] | |

"Certified" means: for each claim, every local system below its stated bounds (k, l) has an exact
nonnegative-integer certificate or is excluded directly, and the final test fails at (k, l). It
certifies the arithmetic and the coverage, not the lemmas behind the rows.

## 2. Inherited lemmas: what must hold at G = 75 [read, not checked]

`PROOF.md` proves "L(M) is not 73 and not 74" (Proposition 11.1) and words sections 10-11 for "G is 73
or 74". Everything in this folder uses the same chain at G = 75, as a black box. The sprint's reading
was that the links carry over verbatim and only have to be applied; that is one agent's reading.

| Link | Statement used | How G enters | Review still needed |
|---|---|---|---|
| Lemma 1.1, sections 2-4 | normalization; x >= 24; odd graph; Lemmas 4.1, 4.4-4.7; finite facts F1-F14 | not at all | none specific to 75; the package's own review status applies |
| Sections 6-8 | origin identity; Lemma 7.4 (r + u + v >= 3 in a canonical transpose); potential e; Lemmas 8.2, 8.3 | 8.2 and 8.3 contain G explicitly | that a minimum circuit with 75 gates has the orbit of canonical transposes with the same properties (using L(M) >= 75 in place of L(M) >= 73 or 74) |
| Lemma 9.1 | the tail: y constant on even phases, nondecreasing on odd ones; fixed count profiles | through h_e = G - 32 - a - Y and h_o = G - 32 - b - V | that the steady-regime argument does not use G <= 74 |
| Section 11, scalar domain | admissible profiles; the caps S_e, S_o; the lower bounds l(h, y) | ranges of a, b, Y, V; the two caps; the budget a + b + 2G - 192 | that the caps hold at G = 75 by the same derivation |
| Lemma 10.1, rows (L1)-(L23) | every phase of the tail satisfies its local system over types with r + u + v >= 3 | the rows contain no G; the column set uses Lemma 7.4 | that no row's proof uses G <= 74 |
| Lemma 10.3, (4.4) | direct exclusions | none in the code | as for 10.1 |
| Proposition 11.1 | if every oriented claim fails the final test, e is unbounded, a contradiction | the budget | the proof text with G = 75 |

## 3. What the certified exclusions rest on beyond the package

| Exclusions | Rest on | Review status |
|---|---|---|
| 5,908 (package rows) | (L1)-(L23) only | the package's own review status |
| 822 (sprint) | Addenda A-D and their finite facts S1, H1, H2, FM, J1 | each lemma checked by a second language-model agent; finite facts by two or more programs; no human review; 38 claims need J1 |
| 406 (combined) | the above and the October rows (push5, push6) with their finite facts | the author's working documents, followed by two audit agents; finite facts recomputed by `verify_all.py`; no human review |

## 4. Obligations

| Obligation | State |
|---|---|
| O0 the domain accounted by identifier | done [checked] |
| O0' certificates for the package-row exclusions at G = 75 | done [certified], 2026-11-11 |
| O1 the framework applies at G = 75 (section 2) | open: read by one agent, not reviewed independently |
| O2 review of Addenda A-D and of the October rows | language-model review only |
| O3 the 280 open claims | open |
| bound | **75** |

## 5. Research in progress on the 280 claims (not part of this folder)

Unpublished work on the branch `phase-2026-11-09` (state of 2026-11-11 at the tag
`phase-2026-11-09-pilot-q3`, folder `research/phase-2026-11-09/proof-followup/`). It changes no count
here.

- **Scope** [measured]. Closing a claim means excluding every LP-feasible key of one of its ladders up
  to the level where the final test fails. The ladders of the 280 claims hold 4,223 keys and 68,153
  open case leaves; the 229 "load-bearing" keys reported earlier are only their first level. No
  enumeration of hub configurations covers them: if every leaf with A >= 2 were excluded, 119 claims
  would stay open; if every leaf with A >= 1 were, 88 would (they rest on A = 0 leaves, where no hub
  argument applies).
- **Pilot.** A complete enumeration of label configurations for one family (M<sup>T</sup>, q = 3; 207
  open leaves) excluded 186 leaves and found verified local witnesses for the other 21, with an
  independent review. 78 of the exclusions have exact certificates; the others are agreed by two
  implementations or rest on one. If accepted, 4 to 8 of the 280 claims would close. The exclusions
  rest on lemmas that have had language-model review only, and they are not packaged or counted here.
- The 101 keys that the sprint classified as integer-infeasible by an unrecorded solver status were
  never used as exclusions and stay unresolved. The two label-sharing enumerations the sprint
  specified (M<sup>T</sup> q = 1, M q = 2) address no key that is still live.
