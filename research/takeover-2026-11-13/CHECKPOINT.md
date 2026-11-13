# XOR structural research: checkpoint, 2026-11-13

Branch: `research-2026-11-13-structural`. Current continuation follows reviewed commit
`a7ff345`; see [current results and judgment](crossing/README.md).
Verified original base: `e89b8a25f69195266f1e24e815cb96c7526a3511`, local and remote
`phase-2026-11-09`. The original and other research worktrees, including untracked
`search/proposals/`, are preserved. Our worktree is this chat's `work/xor-structural`.

**Unchanged: 75 <= L(MixColumns) <= 88.** No claim that 88 is optimal.
Hand proofs and independent machine reviews are not formal verification or human
certification. The general joint 0/1 interval under its hypothesis remains 21 to 22.

## Read next

1. [Current summary](crossing/README.md),
   [supplier closure and the joint ten-cone theorem](crossing/ODD_CLOSURE.md).
2. [Universal rank-two normal form](crossing/NORMAL_FORM.md),
   [three-coordinate causal origin](crossing/THREE_COORDINATES.md).
3. [Restricted augmented bound for every diagonal basis](frontier/AUGMENTED.md),
   [the mixed-auxiliary obstruction](crossing/AUXILIARY.md).
4. [Previous frontier](frontier/README.md): rank-one exclusion and even confinement.
   [Tradeoffs](tradeoff/README.md): relation rank, profiles, causal span, constructions.
5. [Compatibility](compatibility/README.md), [row costs](row-cost/README.md),
   [earlier continuation](continuation/README.md), [first-pass summary](SUMMARY.md).
   Historical [checkpoint](../structure-2026-11-11/CHECKPOINT.md),
   [record](../structure-2026-11-11/RECORD.md), and
   [visible-event account](../structure-2026-11-11/visible/VISIBLE.md) remain the trail.

Independent reviews are linked from each pass's summary.

## New proved results

- **The ten-gate producer branch is closed.** Every fixed ten-gate first-sheet producer
  requires at least twelve consumer-bearing gates. Under no feedback to first-sheet
  target ancestors, a joint circuit whose first-sheet ancestor cone has ten gates
  needs at least 22 in total. A matching circuit exists in this class. The bound allows
  the one additional supplier at the 21 boundary to be a consumer-block exit.
- **Complete diagonal-difference confinement at rank two.** Every difference of two
  available values in one diagonal coset belongs to the producer's existing clean
  span W. The earlier even-coset result is now joined by an odd-coset exclusion. One
  extra gate cannot enlarge the clean span. Rank-one supply was already excluded.
- **Universal rank-two normal form.** Exactly two odd helpers, four independent physical
  even values, and four entries occur. Two entries are even; each own class has one odd
  entry and one helper. The even-entry labels form the rank-two residue plane; both
  odd-entry labels lie outside it. Projected class trees lift to five-node trees.
  A crossing would leave at most one clean pair, and the remaining required relations
  contain an alternating four-cycle, preventing six independent gate equations.
- **Broader augmented obstruction.** For every three independent even diagonals, an
  event-free circuit with no extra mixed intermediates needs at least twelve gates.
  Twelve is attained for one basis, not claimed for every prescribed basis. If two
  selected diagonals are non-cycle masks and all diagonals feed rows, a sole extra
  mixed intermediate is also impossible; at least two would be needed.

## Remaining mathematical obligation

Any hypothetical joint 21 must now have **eleven gates inside the first-sheet row
ancestor cone**, already containing three independent clean diagonals, followed by ten
consumer-bearing gates. There is no spare supplier outside that cone. Equivalently,
any eleven-gate augmented supplier must use each designated diagonal to compute a row.
Its minimum remains 11 or 12; the unrestricted joint minimum remains 21 or 22.

The strongest next task is to combine this row ancestry with the cost of mixed
intermediates. The seven required augmented values are independent, so any one extra
mixed value can mediate at most one physical relation between two required nodes.
Pure-own ancestry helps when event-freeness is assumed; unrestricted cancellation must
be handled separately. No claim that an eleven-gate augmented circuit is impossible
has been made.

## Constraints retained from earlier work

Actual clean rank at ten gates is at most two and is attained. Four values in a nonzero
coset force clean rank at most one. Entry deletion gives `K>=L_D+c` for quotient rank c.
Physical gate equations must be independent, with available relation rank
`|O|-components+dim(even-only relations + colours(cycle space))`.

The sparse family shows two hidden gates can support unbounded savings under the
recorded weight/window restrictions. HR and affine-completion bounds count physical
components and require sharing control before summing. Projection repair is one-sided.
Reconstructed 10/13 sheet lemmas, 83/84 block-monotone bounds, Theorem V and joint repair
retain their stated hypotheses. None gives a new unrestricted MixColumns bound here.

## Method and reproducibility

No SAT, exhaustive enumeration, exact least-gate search, heuristic circuit search, or
computer-driven case elimination was used. Universal results have hand proofs.
The [current direct check](crossing/check_normal_form.py) evaluates one specified
producer's entry structure and class trees; [results](crossing/check-results.json) are
saved. Prior construction checks and reviews remain linked from their summaries.

The Windows-backed checkout reports executable-bit differences; use Git with
`-c core.filemode=false`. Shared repository config is unchanged. Stage only intended
research paths and preserve other worktrees and `search/proposals/`.
