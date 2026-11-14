# XOR structural research: checkpoint, 2026-11-14

Branch: `research-2026-11-13-structural`. This phase continues reviewed commit
`8ab0b3e`. Original verified base: `e89b8a25f69195266f1e24e815cb96c7526a3511`
on `phase-2026-11-09`. Other worktrees and `search/proposals/` are preserved.
Our worktree is this chat's `work/xor-structural`.

**New reduction:** any joint circuit below 22 with exactly twelve consumer-bearing
gates must have all twelve in the relaxed target cones and exactly six entries.
Every outside-entry case and the target-live five-entry case are now excluded.
The twelve-consumer minimum itself remains open.

**New general mechanisms:** affine-tree transfer charges shared returns only for
missing translated intermediate values. Independent even mirror helpers force an
odd-value forest; cut equations make odd-wire source parts clean when extra source
ports are confined to even wires. With at most two ordinary readers per helper,
this yields entry chains with clean endpoints. Free-section replay completes an
ordinary-projection section without a separate prefix-splitting hypothesis.

**New source restriction:** all-even-own entries force at least ten source gates,
at any consumer budget. A rank-five candidate with at most nine source gates has
one even wholly free direction q and an odd-own entry h, with
`U=D direct-sum span{q,h}`. These statements constrain the entry span, not every
original physical source value.

**Retained:** joint minimum 22 for exactly ten or eleven consumer gates; no-feedback
minimum 22; full-diagonal supplier lower bound 15 (attainment not claimed);
block-monotone MixColumns lower bound 85; unrestricted `75<=L<=88`.
No assumption that 88 is optimal. Hand proofs have independent machine reviews,
not formal verification or human certification.

## Read next

1. [Current reduction, complete coverage, and judgment](feedback/SIX_ENTRY_FRONTIER.md).
2. [Affine-tree transfer](feedback/AFFINE_TREE_TRANSFER.md) and
   [general odd-forest / chain geometry](feedback/CHAIN_FIBRES.md).
3. [Five target-live entries are excluded](feedback/FIVE_ENTRY_TWELVE_CLOSED.md).
4. Outside-entry closure: [four-entry core](feedback/FOUR_ENTRY_TAIL_CLOSED.md),
   [core wire and triangle reductions](feedback/TAIL_CORE_REDUCTIONS.md),
   [two nonclean entries](feedback/TWO_NONCLEAN_TAIL_CLOSED.md), and
   [three-nonclean four-term relation](feedback/THREE_NONCLEAN_FOUR_TERM_TAIL_CLOSED.md).
5. [Even-entry source floor and residue-plane normal form](feedback/EVEN_ENTRY_SOURCE_FLOOR.md),
   [parity rank retraction](feedback/PARITY_RANK_RETRACTION.md), and
   [free-section replay](feedback/FREE_SECTION_REPLAY.md).
6. Supporting results: [six-entry identities](feedback/TWELVE_ENTRY_WIRES.md),
   [saturated collisions](feedback/SATURATED_QUOTIENT.md),
   [saturated tails](feedback/SATURATED_TAILS.md),
   [four-diagonal supplier](feedback/FOUR_DIAGONALS.md),
   [previous frontier](feedback/TWELVE_CONSUMER_FRONTIER.md).
7. [Takeover history](SUMMARY.md), historical [record](../structure-2026-11-11/RECORD.md),
   [checkpoint](../structure-2026-11-11/CHECKPOINT.md), and
   [visible account](../structure-2026-11-11/visible/VISIBLE.md).

## Why the new exclusions work

- A tail `v=u+h` with partners in one entry tree can be removed at total overhead
  at most `B-1`, where B counts missing physical translates on the connecting tree.
  Original values are advanced and credited; other feedback stays in place.
- The seven-gate mirror's three independent even helpers have reader counts
  `(2,1,1)`. Its odd-value graph is a tree. Cut equations force clean endpoints
  and a clean isolated root in a repeated fibre, limiting useful crossing returns.
- The difficult cases admit source-only replay with at most three extra gates.
  It retains a clean triangle and an independent clean direction: at source cost
  at most nine, that gives a forbidden supplier within twelve gates, below thirteen.
- The outside core has four or five entries. All clean/nonclean counts and allowed
  label-relation profiles are covered; see the explicit table in the current frontier.
- With all entries even-own, three even-rank increases and four first triple masks
  force seven independent odd-pair equations. A source budget below ten cannot
  provide them, unless all exits are redundant, which also contradicts local ten.

## Remaining frontier and next direction

A twelve-consumer candidate below 22 now has six entries, entry rank five, and trace
rank four. Its sole actual-label relation is the odd-trace indicator. The trace
relation space is the two-dimensional quotient-signature row space. At most two
nonzero physical clean values exist. Every nonclean actual label has a unique
physical difference pair. Repeated traces remain possible; all-odd, pairwise-distinct
traces are already excluded.

Use the six-gate mirror's two-component odd forest together with the source parity
restriction. Odd trace ports add terms to the cut equations, so the new clean-endpoint
argument cannot simply be reused. Internal merges with more readers may matter.
The six-entry case, larger consumer budgets, and the unrestricted joint minimum
remain open. Avoid turning this into a trace-pattern enumeration campaign.

Reviews are linked from the current frontier. No circuit search or numerical proof
campaign was used. Use Git with `-c core.filemode=false`; shared config is unchanged.
