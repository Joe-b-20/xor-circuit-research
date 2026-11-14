# XOR structural research: checkpoint, 2026-11-13

Branch: `research-2026-11-13-structural`. Current [four-diagonal continuation](feedback/FOUR_DIAGONAL_FRONTIER.md)
follows reviewed commit `4adbf01`. Original verified base:
`e89b8a25f69195266f1e24e815cb96c7526a3511` on `phase-2026-11-09`.
Other worktrees and `search/proposals/` are preserved. Our worktree is this chat's
`work/xor-structural`.

**New:** four first-sheet rows plus diagonals `c,d,c+d,e` need thirteen source gates,
for independent `c,d,e`. This closes the four-entry mixed eleven-consumer case at 22.
Any eleven-consumer candidate below 22 has five mixed entries, all eleven gates in
relaxed consumer target cones, and original physical clean rank at most two.
**Still open:** that five-entry class, larger consumer budgets, and the full joint minimum.
**Retained:** ten-consumer joint minimum 22 with feedback, no-feedback joint minimum 22,
block-monotone MixColumns lower bound 85, unrestricted `75<=L<=88`.
No assumption that 88 is optimal. Hand proofs and independent machine reviews are
not formal verification or human certification.

## Read next

1. [Current results, judgment, and frontier](feedback/FOUR_DIAGONAL_FRONTIER.md).
2. [Four-diagonal proof](feedback/FOUR_DIAGONALS.md),
   [four-entry closure and target-cone correction](feedback/FOUR_ENTRY_CLOSURE.md),
   [rank-four physical supply](feedback/RANK_FOUR_SUPPLY.md).
3. [Collision and causal-return theorem](feedback/ENTRY_RETURN_RIGIDITY.md),
   [diagonal confinement](feedback/DIAGONAL_CONFINEMENT.md),
   [entry/trace geometry](compatibility/QUOTIENT.md).
4. [Five diagonals and ten-consumer bound](feedback/FIVE_DIAGONALS.md),
   [rank-three replay](feedback/RANK_THREE.md), [augmented minimum twelve](augmented/PROOF.md),
   [joint and block-monotone consequences](augmented/CONSEQUENCES.md).
5. [General repair](feedback/GENERAL_REPAIR.md), [helper-value obstruction](feedback/SIDON_REPAIR.md),
   [takeover history](SUMMARY.md), historical [record](../structure-2026-11-11/RECORD.md),
   [checkpoint](../structure-2026-11-11/CHECKPOINT.md), and
   [visible account](../structure-2026-11-11/visible/VISIBLE.md).

## Current proved results

- Four diagonals containing a triangle plus an independent value require thirteen
  source gates together with the four first rows. The bound allows arbitrary
  cancellation and is attained for one prescribed choice, not asserted for every basis.
- Two clean and two nonclean actual entry labels forming a rank-four basis force
  at least eleven source gates. With eleven consumer gates the minimum for this
  subclass is 22, attained by a specified event-free `(11,11)` construction.
- At eleven consumer gates, a joint total below 22 forces five mixed entries and all
  eleven gates in the relaxed target cones. An exit-only extra gate is handled
  separately; the previous automatic use of target-trimmed geometry was too broad.
- For any rank-four actual entry span containing `D`, three independent original
  physical clean values force at least eleven source gates. Thus the remaining
  below-22 eleven-consumer class has physical clean rank at most two.
- Every projected physical collision counts: `K>=L_D+delta_C` for `C` disjoint from
  required source space `D`. At eleven gates a nonclean difference has at most one
  physical pair. Direct return/re-entry of a new nonclean label is impossible;
  indirect feedback that changes the label is still allowed.
- All actual entries in `D` force source cost twelve at any consumer budget. A
  target-preserving free-block projection gives the same bound for entries in
  `D+<h>` with ordinary source part even and free part odd. At eleven consumer
  gates these classes require total at least 23.

## Next mathematical direction

Study the five-entry interface's unique label relation and unique trace relation
alongside chronological replay. A source replay that creates a pair sum may recover
its cost by bypassing that value's later original production. Seek a forced credit
or a forced additional physical diagonal; do not assume a clean virtual difference
is already supplied. Collision accounting offers a separate way to charge a missing
clean direction returned by the consumer. Larger consumer budgets remain separate.

## Earlier results and limits

Three independent diagonals plus the first rows require twelve source gates; five
nonzero distinct diagonals require thirteen. The latter closes every ten-consumer
joint circuit at 22 via rank-three replay. A specified ten-gate consumer nevertheless
permits a local ternary return; a later-label credit illustrates why one expensive
exit need not increase total replay cost.

General replay costs at most `h(d)=2^ceil(d/2)+2^floor(d/2)-d-2`, sharp through rank
four. A fixed Sidon family forces `Omega(2^(d/3))` extra source gates even offline;
this is a source-value-preservation bound, not an exponential full-circuit gap.
Adaptive online repair matches the upper asymptotic order; fixed prefixes have exact
full-circuit saving `d-2`. Keep these metrics distinct.

Generic event-free repairs may use baseline 85, but historical charged-slack formulas
retain their own hypotheses. HR/affine completion require sharing control, and the
sparse family refutes savings bounds from hidden-gate count alone.

## Verification and repository discipline

The current summary links independent reviews and checks of two specified attaining
constructions. Universal arguments are hand proofs; no SAT, circuit enumeration,
exact search, or computer-driven case elimination was used. Use Git with
`-c core.filemode=false`; shared config is unchanged. Stage only intended research
files and preserve other worktrees.
