# Editorial changes for the October 23 edition

The original public review draft is version 1.1, dated October 2, 2026, with Git blob
`cd97b9e2fbc5c017e8420504640d19e6c31e5242`. Its text remains unchanged at
`source/lower_bounds/PROOF_NOTE_75.md`.

The submitted `PROOF.md` uses the same theorem, numbered lemmas, finite facts, local inequalities,
certificate datasets, and mathematical argument. No new lower bound or mathematical strengthening is claimed.

## Exposition clarifications

- **Normalization, Lemma 1.1:** Zero-valued gates are removed by propagating
  $0\oplus u=u$ through their uses. The argument does not assume an earlier zero signal exists.
- **Cancellation, section 0:** Cancellation is described as overlapping input contributions disappearing
  under XOR. A cancellation need not make the result smaller than either operand.
- **Full-helper adjacency, Lemma 4.5:** The prohibited case is XOR equal to a boundary-pair value,
  hence adjacency through a represented label. Missing-label helper-to-helper edges are still allowed
  and are treated by the subsequent arguments.
- **Partition count, Corollary 2.3:** A partition into more than nine disjoint codewords can be merged
  into a nine-part partition. The finite exclusion of nine parts therefore also excludes larger counts.
- **Canonical accumulation, Lemma 3.2:** "The only possible odd-valued gate is the root" makes the
  even-result case explicit; then there is no odd-valued gate.
- **Origin identity, Lemma 7.3:** A compressed cross-reference is restated as "by Lemma 7.1";
  the adjoint is taken in the first transpose and its origin mask is in the original circuit.
- **Finite-fact heading:** The dark-label and short-relation-rank heading now explicitly includes
  F13-F14, matching the verification table.

None of these clarifications alters the executable certificate systems.

Two further definition clarifications make the original intended scope explicit: a full value has three
distinct boundary-triple representations of the same value (a repeated value has at least two); and
the missing-label intersection lemma concerns labels on H-B edges, as counted by the helper parameter $u$.

This edition is a revision of the existing review draft, not a new peer-reviewed publication.
