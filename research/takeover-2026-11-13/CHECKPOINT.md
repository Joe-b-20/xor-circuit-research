# XOR structural research: checkpoint, 2026-11-14

Branch: `research-2026-11-13-structural`. This phase continues reviewed commit
`cfab8f6`. Original verified base: `e89b8a25f69195266f1e24e815cb96c7526a3511`
on `phase-2026-11-09`. Other worktrees and `search/proposals/` are preserved.
Our worktree is this chat's `work/xor-structural`.

**New:** equality in quotient cost identifies every projected physical collision
with a selected entry-tree path. Nonclean actual labels have unique physical pairs
and cannot be newly returned. Gates outside the relaxed output cones must belong to
every quotient basis. A greedy chronological complement gives a general replay bound
that credits original physical values.

**New source bounds:** entry rank at most four forces at least ten source gates,
at any consumer budget. Four source rows plus all seven nonzero clean diagonal values
require at least fifteen gates; attainment is not claimed.

**Twelve-consumer frontier:** below total 22, the entry span must have rank five,
with two nonclean quotient directions and at most two original physical clean values.
There is at most one consumer-bearing gate outside the output cones, and it must
support at least two distinct useful returns. If every gate lies in those cones,
only five or six entries remain, with the restrictions below. This case is open.

**Retained:** joint minimum 22 for exactly ten or eleven consumer gates; no-feedback
joint minimum 22; block-monotone MixColumns lower bound 85; unrestricted `75<=L<=88`.
No assumption that 88 is optimal. All new universal results are hand arguments with
independent machine reviews, not formal verification or human certification.

## Read next

1. [Current results, exact scope, and research judgment](feedback/TWELVE_CONSUMER_FRONTIER.md).
2. [Saturated quotient collisions](feedback/SATURATED_QUOTIENT.md) and
   [outside-cone coloop theorem](feedback/SATURATED_TAILS.md).
3. [Rank-four source floor](feedback/RANK_FOUR_SOURCE_FLOOR.md), its
   [physical-clean supply lemma](feedback/RANK_FOUR_TWO_CLEAN.md), and
   [full-diagonal supply with chronological complement replay](feedback/FULL_DIAGONAL_SUPPLY.md).
4. [Twelve-consumer wire restrictions and seven-gate counterexample](feedback/TWELVE_ENTRY_WIRES.md).
5. [Previous eleven-consumer closure](feedback/ELEVEN_CONSUMER_CLOSED.md),
   [credited replay](feedback/CREDITED_REPLAY.md),
   [entry deletion](compatibility/QUOTIENT.md),
   [augmented minimum twelve](augmented/PROOF.md), and
   [no-feedback/block-monotone consequences](augmented/CONSEQUENCES.md).
6. [Takeover history](SUMMARY.md), historical [record](../structure-2026-11-11/RECORD.md),
   [checkpoint](../structure-2026-11-11/CHECKPOINT.md), and
   [visible account](../structure-2026-11-11/visible/VISIBLE.md).

## Current mechanisms and unresolved cases

- For `K=L_D+c`, any actual quotient basis supplies a `c`-edge forest. Its components
  exactly equal the full-value cosets modulo the selected label span. This holds for
  all physical consumer nodes, including gates used only for exits.
- For any `D subset U`, greedy actual quotient representatives span `C` so every
  entry-prefix splits under `U=D direct-sum C`. Replay completes both groups for
  `G0+(2^dim(D)-1-m_D)+(2^dim(C)-1-m_C)`, counting original physical group values.
  At entry rank five the new supplier bound gives `G0>=5+m_D+m_C>=7+m_D`.
- A global twelve-consumer candidate below 22 has at most one outside-cone entry.
  A single useful return through it can be reassociated into the source; multiple
  returns may share it, and their cost is unresolved.
- With all twelve gates in the output cones, six entries leave a six-gate mirror.
  Trace rank is four; the unique actual-label relation is the odd-trace indicator.
  Odd, pairwise distinct traces are excluded, but repeated traces remain open.
- With all twelve gates in the output cones, five independent entries give three
  independent even trace classes, of sizes `(3,1,1)` or `(2,2,1)`. There is exactly
  one ordinary fibre with two entry-tree roots, and some nonredundant exit must join
  its two components. This crossing-return case remains open.
- A specified seven-gate ordinary circuit has distinct even wires with the same
  ordinary derivative. The previous six-gate separation theorem cannot be extended
  without a new hypothesis. Do not apply target-live classifications to the tail case.

## Next direction and verification

Seek a structural charge for returns crossing distinct entry-tree components, or for
multiple returns sharing the single outside entry. Both identify work absent from a
single-tree replay. Avoid a campaign of trace-pattern case elimination. Larger consumer
budgets and the unrestricted joint minimum remain open.

Reviews are linked from the current frontier. No search or new numerical campaign was
used. Use Git with `-c core.filemode=false`; shared config is unchanged. Stage only
intended research files and preserve other worktrees.
