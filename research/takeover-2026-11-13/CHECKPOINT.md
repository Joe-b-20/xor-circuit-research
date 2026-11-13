# XOR structural research: checkpoint, 2026-11-13

Branch: `research-2026-11-13-structural`. Current phase: [feedback](feedback/README.md),
continuing reviewed commit `edbe77f`. Verified original base:
`e89b8a25f69195266f1e24e815cb96c7526a3511` on `phase-2026-11-09`.
Other branches/worktrees and untracked `search/proposals/` are preserved.
Our worktree is this chat's `work/xor-structural`.

**New:** total feedback savings bounded by entry rank, sharp through rank four;
a return-rank cost bound; restrictions on possible feedback in the joint problem.
**Unchanged:** unrestricted `75 <= L(MixColumns) <= 88`; block-monotone lower bound
85; exact no-feedback joint minimum 22. No optimality claim about 88.
Hand proofs and independent machine reviews are not formal verification or human certification.

## Read next

1. [Current results and judgment](feedback/README.md), [general repair theorem](feedback/GENERAL_REPAIR.md),
   [return-rank cost](feedback/FEEDBACK_RANK.md).
2. [Ten-gate consumer and ternary return](feedback/RANK_THREE.md),
   [mirror restrictions](feedback/MIRROR_EXITS.md), [one-exit separation](feedback/ONE_EXIT.md).
3. [Augmented minimum twelve](augmented/PROOF.md),
   [joint 22 / block-monotone 85](augmented/CONSEQUENCES.md).
4. [Ten-gate supplier closure](crossing/README.md), [rank-one and even confinement](frontier/README.md),
   [tradeoffs](tradeoff/README.md), [compatibility](compatibility/README.md), [row costs](row-cost/README.md).
5. [Takeover history](SUMMARY.md), [earlier continuation](continuation/README.md),
   historical [record](../structure-2026-11-11/RECORD.md),
   [checkpoint](../structure-2026-11-11/CHECKPOINT.md), and
   [visible-event account](../structure-2026-11-11/visible/VISIBLE.md).

## Current proved results and limits

- **General repair.** If actual consumer entry labels lie in a `d`-dimensional source
  space, all source-side values can be replayed without consumer feedback for at most
  `h(d)=2^ceil(d/2)+2^floor(d/2)-d-2` extra gates in total. Two growing basis groups
  supply every return as a sum of two physical values. The construction preserves
  chronological availability; zero is free. Allowances at ranks 0 through 4 are
  `0,0,0,1,2`, with exact full-circuit separations attaining one and two.
- **Returned directions cost entries.** If `D` spans required consumer source parts,
  `F` spans returned values, and `L_D` is consumer cost with `D` free, then
  `K>=L_D+dim((F+D)/D)`. For the joint problem `L_D=10`; returning `k` first-sheet
  rows directly as exits needs at least `10+k` consumer gates.
- **Ten-gate consumer.** All actual entries lie in rank-three `D`. Repair and augmented
  minimum twelve force at least eleven source-side gates. At joint total 21 an exit
  must require the sum of three independent available diagonal values; no one-gate
  replacement or compensating saving can remove its one-gate premium. This necessary
  condition does not prove such a consumer exists or exclude larger consumer budgets.
- **General free-feedback normalization is false.** A rectangular eight-output map
  has exact minima 21 unrestricted and 22 without feedback, despite independent
  weight-five rows, boundary distance six, small blocks, and small windows. It is
  not the MixColumns map. A one-bit cancelled block can carry useful feedback.
- **Mirror restriction.** Below joint budget 22, an exit must feed a second-group
  target in the mirror. With three exports, at least thirteen gates have nonzero
  first part, leaving only four or five zero-first-part gates. This is unresolved.

## Next direction and retained constraints

Determine whether an optimal ten-gate consumer can realize the required ternary
return while supplying all four own-triple targets. Track original physical values
and readers. Double transposition preserves the map but has not been shown to
preserve the particular cancelling operand pairs; the attempted shortcut is unproved.
Eventual entry availability is insufficient for a causal exit argument.

The augmented minimum twelve holds for every independent diagonal basis; attainment
is shown for one. It gives joint minimum 22 when first-sheet output cones avoid the
consumer block. Disjoint charges give `22+13+5*10=85` in the block-monotone class,
which includes event-free circuits. Arbitrary feedback remains outside that result.
Generic event-free repairs may use baseline 85, but historical charged-slack formulas
cannot all be updated by numerical substitution. HR and affine completion still
need sharing control before adding physical components. Hidden-gate count alone
cannot bound savings; the recorded sparse family refutes that approach.

## Checks and repository discipline

[Current reviews](feedback/README.md#review-and-verification) and
[direct checks](feedback/check-results.json) are saved. Six specified constructions
are evaluated; no SAT, circuit enumeration, exact search, or computer-driven case
elimination was used. Universal statements have hand proofs.

Use Git with `-c core.filemode=false` in this Windows-backed checkout. Shared config
is unchanged. Stage only intended research files and preserve other worktrees.
