# XOR structural research: checkpoint, 2026-11-13

Branch: `research-2026-11-13-structural`. Current [feedback continuation](feedback/README.md)
follows reviewed commit `242ee0a`. Original verified base:
`e89b8a25f69195266f1e24e815cb96c7526a3511` on `phase-2026-11-09`.
Other worktrees and `search/proposals/` are preserved. Our worktree is this chat's
`work/xor-structural`.

**New:** joint minimum 22 with exactly ten consumer gates, allowing arbitrary feedback;
a general bound on extra intermediate values; an exponential source-preservation
repair lower bound. **Unchanged:** unrestricted MixColumns `75<=L<=88`, block-monotone
lower bound 85, exact no-feedback joint minimum 22. No claim that 88 is optimal.
These are hand proofs with independent machine review, not formal verification or
human certification.

## Read next

1. [Current results](feedback/README.md), [five-diagonal proof and joint consequence](feedback/FIVE_DIAGONALS.md).
2. [Actual ten-gate ternary return](feedback/TERNARY_CONSUMER.md),
   [general helper-value obstruction](feedback/SIDON_REPAIR.md).
3. [General repair](feedback/GENERAL_REPAIR.md), [rank-three replay](feedback/RANK_THREE.md),
   [returned-direction cost](feedback/FEEDBACK_RANK.md).
4. [Augmented minimum twelve](augmented/PROOF.md),
   [no-feedback joint 22 and block-monotone 85](augmented/CONSEQUENCES.md),
   [supplier closure](crossing/README.md).
5. [Takeover history](SUMMARY.md), historical [record](../structure-2026-11-11/RECORD.md),
   [checkpoint](../structure-2026-11-11/CHECKPOINT.md), and
   [visible account](../structure-2026-11-11/visible/VISIBLE.md).

## New proved results

- **Five diagonals require thirteen.** Four first-sheet rows plus five distinct nonzero
  diagonal values need at least thirteen source gates, with arbitrary cancellation.
  At twelve, nine first occurrences and three entries saturate the budget. Relation
  rank forces two nonclean even values and at most one odd helper; pair capacity is
  then too small. No thirteen-gate upper construction is asserted.
- **All ten-gate consumers require joint 22.** Their actual entry span is the clean
  rank-three diagonal. A hypothetical total 21 replays in at most twelve source
  gates. Zero overhead contradicts the augmented minimum twelve; positive overhead
  creates five physical diagonal values and contradicts the new thirteen-gate bound.
  The explicit no-feedback 22-gate circuit attains this consumer-budget minimum.
- **Local ternary returns exist.** A specified optimal ten-gate consumer admits an
  early three-label exit. Its four entry labels have a three-term relation. This
  corrects an attempted incomplete division of four-entry cases. Its later fourth
  label can repay the repair gate; it is not a joint 21 construction.
- **Targets with no short relations need helpers.** For `N` distinct nonzero non-input
  targets with no three- or four-term relation, put `R=d+A`, where `d` is the input
  count and `A` the auxiliary gate count. Then
  `N<=R+R(1+sqrt(4R-3))/4`, hence `A>=(4N/7)^(2/3)-d`.
  Target/non-target equations have unique pair differences; non-target pairs form a
  graph with no four-cycle.
- **Fixed-family repair lower bound.** `t_x=(x,x^3)` over `GF(2^k)` meets those hypotheses.
  In dimension `d=2k`, a fixed one-bit-consumer circuit with `G_0` source exits needs
  `G_0+Omega(2^(d/3))` gates in every source-only realization preserving its source
  outputs. This applies even offline. It does not compare full circuit optima.

## Next direction and retained results

The remaining unrestricted joint question involves at least eleven consumer-bearing
gates. At eleven, all exits together can have only one independent direction outside
clean `D`. Study whether that direction can reduce the source work enough to beat 22.
Do not reuse the no-feedback assumption implicitly or infer a source lower bound from
virtual diagonal combinations.

General feedback repair costs at most
`h(d)=2^ceil(d/2)+2^floor(d/2)-d-2` extra source gates, sharp through rank four.
The fixed-family lower exponent `d/3` differs from the upper `d/2`; adaptive online
repair has the upper asymptotic order. The full-circuit prefix saving is exactly `d-2`.
These three metrics must remain distinct.

[Entry matching](feedback/ENTRY_MATCHING.md) and [marked-wire duality](feedback/WIRE_DUALITY.md)
are secondary tools. The latter retains explicit XOR/copy wiring; abstract double
transposition alone does not identify internal nodes. The main joint proof avoids
classifying those internal cases.

The augmented minimum twelve holds for every independent diagonal basis, with an
upper construction for one basis. Disjoint charges give `22+13+5*10=85` only in the
block-monotone class. Generic event-free repairs may use 85; historical charged-slack
formulas require their own hypotheses. HR and affine completion still require sharing
control, and the sparse family still refutes savings bounds from hidden-gate count alone.

## Checks and repository discipline

Independent reviews and fixed-construction results are linked from the current summary.
No SAT, circuit enumeration, exact search, or computer-driven case elimination was used.
Use Git with `-c core.filemode=false` in this Windows-backed checkout. Shared config is
unchanged. Stage only intended research files and preserve other worktrees.
