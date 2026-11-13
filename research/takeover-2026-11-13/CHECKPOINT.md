# XOR structural research: checkpoint, 2026-11-13

Branch: `research-2026-11-13-structural`. Current continuation follows reviewed commit
`1fffbd0`; see [current results and judgment](frontier/README.md).
Verified original base: `e89b8a25f69195266f1e24e815cb96c7526a3511`, local and remote
`phase-2026-11-09`. The original and other research worktrees, including untracked
`search/proposals/`, are preserved. Our worktree is this chat's `work/xor-structural`.

**Unchanged: 75 <= L(MixColumns) <= 88.** No claim that 88 is optimal.
Hand proofs and independent machine reviews are not formal verification or human
certification. The local joint 0/1 interval under its stated hypothesis remains 21 to 22.

## Read next

1. [Current summary](frontier/README.md), [rank-one exclusion](frontier/RANK_ONE.md),
   and [rank-two even-direction confinement](frontier/EVEN_ESCAPE.md).
2. [Projection-tree normal form](frontier/PROJECTION_TREE.md),
   [preliminary rank-two/odd-ancestry constraints](frontier/RANK_TWO.md), and
   [restricted exact twelve-gate diagonal interface](frontier/AUGMENTED.md).
3. [Previous tradeoff pass](tradeoff/README.md): coupled coset/clean supply, physical
   relation rank, supplier profiles, causal span, and the two-diagonal ten-gate control.
4. [Compatibility](compatibility/README.md): entry deletion, coset cap, mixed traces.
   [Row costs](row-cost/README.md): exact local costs and completion geometry.
5. [Earlier continuation](continuation/README.md) and [first-pass summary](SUMMARY.md).
   The historical [checkpoint](../structure-2026-11-11/CHECKPOINT.md),
   [record](../structure-2026-11-11/RECORD.md), and
   [visible-event account](../structure-2026-11-11/visible/VISIBLE.md) remain the trail.

Independent reviews are linked from each pass's summary.

## New proved results

- **Rank one is excluded.** A fixed ten-gate first-sheet producer with clean-diagonal
  rank at most one requires at least twelve consumer-bearing gates. Four nonclean
  values in one diagonal coset cannot complete the required rank three together with
  its one clean direction. Under the first-sheet no-feedback hypothesis, the joint
  cost is at least 22, even allowing one additional supplier to be a consumer-block exit.
- **Rank two confines even intermediates.** If a ten-gate producer supplies two
  independent clean diagonals, every physical even gate has its own mask in those
  same two directions. Thus no even coset supplies the missing direction through
  differences. The contrary rank-three-own hypothesis forces seven non-entry
  equations; short named relations and alternating cycles prevent all seven.
- **Tree normal form.** A ten-gate producer with three independent even own directions
  has exactly seven first occurrences and three independent entries. Projecting away
  the free block gives a cube spanning tree. Its physical even values are independent;
  its non-entry odd graph is a forest, becoming a tree when odd-entry edges are added.
  This hypothesis is possible in general, but incompatible with clean rank two.
- **Restricted augmented optimum twelve.** Four rows and three selected cycle-pair
  diagonals need twelve gates in an event-free circuit with no additional mixed
  intermediates. The bound is attained. An eleven-gate event-free solution for these
  diagonals would need an auxiliary mixed value. Arbitrary diagonal bases and
  unrestricted cancellation remain outside this theorem.

## Remaining mathematical obligation

A hypothetical joint 21 with a ten-gate first-sheet cone must use clean rank exactly
two and two or three nonclean labels from an **odd** diagonal coset. All even own masks
lie in the clean own span W_b. A completing odd coset would need two available nodes
of the same residue whose own masks lie in different classes modulo W_b. Odd ancestry
preserves those classes, but free entries could still create a crossing in residue.
Determine whether the required outputs and entry budget permit it. No such crossing
has been constructed or excluded.

The other joint split still needs an eleven-gate source-only supplier of three
independent diagonals. Its minimum remains 11 or 12. The previous causal-span argument
justifies that source-only reduction even with a possible consumer-block exit.

## Constraints retained from earlier work

Actual clean rank at ten gates is at most two and is attained. Four values in a nonzero
coset force clean rank at most one. Entry deletion gives `K>=L_D+c` for quotient rank c;
cheap mixed interfaces use just one nonclean quotient signature. Physical gate equations
must be independent, with graph relation rank
`|O|-components+dim(even-only relations + colours(cycle space))`.

The sparse family shows two hidden gates can support unbounded savings, even with the
recorded weight/window restrictions. HR and affine-completion bounds apply only to
physical components and cannot be summed without controlling sharing. The projection
repair is one-sided; a five-gate counterexample refutes its converse. Reconstructed
10/13 sheet lemmas, 83/84 block-monotone bounds, Theorem V and joint repair retain their
stated hypotheses. None gives a new unrestricted MixColumns bound.

## Method and reproducibility

No SAT, exhaustive enumeration, exact least-gate search, heuristic circuit search, or
computer-driven case elimination was used. Universal results have hand proofs.
The [current direct check](frontier/check_tree.py) verifies the three graphs of one
specified ten-gate control; [results](frontier/check-results.json) are saved. Previous
construction checks and reviews remain linked from their pass summaries.

The Windows-backed checkout reports executable-bit differences; use Git with
`-c core.filemode=false`. Shared repository config is unchanged. Stage only intended
research paths and preserve other worktrees and `search/proposals/`.
