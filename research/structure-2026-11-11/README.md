# Structural study of linear XOR circuits (started 2026-11-11)

Branch `phase-2026-11-09`. This directory replaces the earlier proof-work plan (SAT, enumeration,
case elimination at G = 75). Nothing here continues that queue. The published bound stays 75; the
best construction stays 88; optimality is open.

Aim: understand what forces XOR circuits to have unavoidable cost, with AES MixColumns as the
central example, and obtain arguments that cover whole families of circuits by one reason.

- `SUMMARY.md`: a short reader's guide: the picture, results by status, the open questions.
- `RECORD.md`: the research record. Proved statements, conjectures, counterexamples, failed ideas
  and unresolved dependencies, kept apart, each with its status.
- `SHARING.md`: the second phase (from 2026-11-12) in one place: when sharing intermediate values
  between sheets can and cannot reduce the size, what compensates, and what is open.
- `CHECKPOINT.md`: where phase 3 stopped and what to do next.
- `compose/` (phase 3, from 2026-11-12): how chain computations compose. `FRAMEWORK.md` (exit-free cuts
  are additive; what flows across a cut), `prove3/` (Lemma R, Theorem A for three sheets), `build29/`
  (constructive attempts, two-pair inequality). Reviews: `review-compose/`, `review-chain/`,
  `review-joint01b/`; gate order: `causal-pair/`.
- `tools/`: small standard-library scripts that examine recorded circuits or check algebra. They
  search nothing and prove nothing by themselves.
- Hand proofs by the main agent, each with its review: `tenth-gate/` (the ten-gate sheet lemma),
  `sharing/INDEPENDENT-SHEETS.md` (sheets with disjoint windows), `pair/` (two adjacent sheets need
  twenty gates).
- One sub-directory per delegated investigation, each with its own `REPORT.md` and scripts:
  `restriction/` (restriction, gate elimination, connectivity, literature), `cyclic/` (cyclic systems
  versus circuits, audit of the published proof), `rotation/` (the rotation model, the charge theorem,
  `REPORT-PART2.md` for MixColumns), `double-map/` (the two-point quotient), `direct-sum/` (sharing
  between unrelated parts, literature), `causal/` (does the order of gates enter), `sharing/`
  (overlapping windows, the three-position circuit), `chain/` (chains of adjacent sheets), `joint01/`
  (MixColumns sheets 0 and 1 with block 7 free, a test case).
- `review-record/`, `review-cyclic/`, `review-charges/`, `review-83/`, `review-phase2/`, `review-pair/`,
  and the `review/` sub-directories: independent machine reviews, each by a model instance that did not
  write the reviewed text.
- In the second phase no SAT and no exhaustive computation was run; programs only evaluate given
  circuits, check small algebraic lemmas, or test inequalities on recorded and perturbed circuits.

Status words used throughout: **proved** (complete argument written here), **conditional** (proved
given a named hypothesis), **conjectured**, **observed** (seen on recorded circuits or small cases;
not a statement about all circuits), **disproved**. Reviews by language models are called machine
reviews; none is a human review or a formal verification.
