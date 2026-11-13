# XOR structural research: checkpoint, 2026-11-13

Research branch: `research-2026-11-13-structural`. Current continuation follows reviewed
commit `4f4d918`; see [coupled supply tradeoffs](tradeoff/README.md).
Verified base: `e89b8a25f69195266f1e24e815cb96c7526a3511` on local and remote
`phase-2026-11-09`. The original worktree, the other research worktree, and untracked
`search/proposals/` were preserved. Our worktree is under this chat's `work/xor-structural`.

**Unchanged: 75 <= L(MixColumns) <= 88.** No claim that 88 is optimal.
Results have hand proofs and independent machine review, not formal verification or
human certification. Local and conditional bounds are not unrestricted bounds.

## Read next

1. [Current summary and judgment](tradeoff/README.md).
2. [Coupled clean-rank/coset theorem](tradeoff/SUPPLY.md) and
   [physical relation rank](tradeoff/RELATIONS.md).
3. [Supplier-profile deficiency and causal span](tradeoff/SUPPLY_PROFILE.md),
   [two-diagonal producer and exact fixed-producer 22](tradeoff/EXPORTS.md).
4. [Previous pass](row-cost/README.md): exact local costs, source saturation,
   completion geometry, and the eleven-gate avoidance theorem.
5. [Previous supplier work](compatibility/README.md): coset cap, entry deletion, mixed
   interfaces, and diagonal controls. [Earlier continuation](continuation/README.md): [sparse sharing](continuation/SPARSE.md),
   [affine completion theorem](continuation/AFFINE.md), [internal events](continuation/INTERNAL.md).
6. [First-pass summary](SUMMARY.md), [H/HR](directions/independent.md),
   [joint reconstruction](directions/JOINT.md), [projection repair](directions/PROJECTION.md),
   [foundational review](reviews/foundations-audit.md).

Reviews are linked from each pass's summary. The [historical checkpoint](../structure-2026-11-11/CHECKPOINT.md)
and [record](../structure-2026-11-11/RECORD.md) remain the earlier research trail.

## New results and their limits

- **Coupled supply.** Four available values in one nonzero clean-diagonal coset of a
  ten-gate producer force clean-diagonal rank at most one. Equivalently, clean rank two
  forces every nonzero coset to have at most three values. The proof uses independent
  entry paths in the even case and independence of physical gate equations in the odd case.
- **Relation rank.** Non-entry gate equations are independent on formal physical nodes.
  Their number is at most the rank of all available three-value relations. For the
  graph of odd values with edges coloured by physical even sums, that rank is
  `|O|-components+dim(Z+colour(cycle space))`, with Z the even-only relation span.
  In particular `entries>=components+rank(even values)-ordinary input count`.
- **Actual clean capacity is two.** A new event-free ten-gate producer supplies two
  independent clean diagonals. The earlier lower bound for three makes rank two the
  exact maximum at ten gates. This particular producer has exact joint completion cost
  22, even with a possible consumer-block exit; a matching circuit is directly checked.
- **Profile and causality.** Let W span actual clean suppliers and Delta_C span differences
  in one supplied coset. If W and every `W+Delta_C` are proper in D, a fixed-supplier
  consumer costs at least `L_D+2`. Separately, an exit from a consumer that has read only
  W cannot create the first clean direction outside W. This makes the (11,10) reduction
  to an actual source-only augmented supplier valid even when feedback was allowed.

## Earlier results that constrain future claims

Every ten-gate supplier has at most four values per diagonal coset. The wholly nonclean
eleven-gate consumer is therefore excluded. Entry deletion gives `K>=L_D+|I|` for a set
of occurrences whose label span is disjoint from D, hence the sharp four-triple bound
`K>=10+c`. Eleven-gate mixed interfaces use one nonclean quotient signature, with no
repeated nonclean labels. A hypothetical no-feedback joint 21 uses only even free-a labels.

The previous pass gives exact one-sheet cost `3f+7` with only free neighbors and
`4p+3f+8` with ordinary neighbors present; a source-saturation theorem for alternative
four-row variants; and sharp completion geometry. A 145-gate MixColumns witness has four
sheet-5 events and only three hidden gates, with its parity partner retained in sheet 6.
Thus a forced partner is not automatically extra hidden cost. The eleven-gate avoidance
theorem remains valid; this pass proves that its five labels cannot fit a ten-gate producer.

The sparse family costs `13r+3` versus event-free optimum `15r+2` with just two hidden
gates, despite weights 5/7, boundary distance 6 and small blocks/windows. It disproves
any universal fixed multiple of hidden work as a bound on savings under those hypotheses.
It is rectangular with one row per own-block family, not MixColumns.

The global affine-completion bound is `h>=dim K-dim Delta`, or `dim K+1` with no actual
local partner; only physical components may be summed. It can be zero. Actual MixColumns
controls have one hidden gate shared across windows (156 gates), or one internal event
and no hidden gates (149 gates). These expensive witnesses do not constrain optimal cost.

The reconstructed 10/13 sheet lemmas, 83/84 block-monotone bounds, Theorem V, joint repair,
H/HR, and simultaneous projection repair remain available with their stated hypotheses.
The projection repair is one-sided; an optimal five-gate example refutes its converse.
The 66-distinct-charge counterexample still refutes unconditional distinct-charge counting.

## Next mathematical obligation

The coupled bound is now proved. Remaining mixed patterns: clean rank one with four
nonclean labels in one coset and one clean label; or clean rank two with two/three
nonclean labels and two independent actual clean suppliers. Determine whether either
can occur at ten producer gates, using relation rank and actual entry labels together.
The other joint split still needs three independent diagonal suppliers in eleven
source-side gates; the augmented minimum remains 11 or 12. No improved unrestricted
MixColumns lower bound is established.

## Method and reproducibility

No SAT, exhaustive enumeration, exact least-gate search, heuristic circuit search, or
computer-driven case elimination was run. Universal claims rely on hand proofs.
[Current checks](tradeoff/README.md#reviews-and-direct-checks) evaluate the ten-/22-gate
construction, two specified relation graphs, and the fixed producer's supply profile.
[Previous checks](compatibility/check-results.json) cover six fixed compatibility constructions.
[Previous checks](row-cost/README.md#review-and-direct-verification) cover local costs,
the 188/184 comparison, the 145-gate witness, and the two original interface circuits.
[Earlier checks](checks/README.md) and [continuation checks](continuation/check-results.json)
remain reproducible; three small external circuit fixtures are saved in the repository.

The Windows-backed checkout reports executable-bit differences; use Git with
`-c core.filemode=false`. Shared repository config was not changed. Stage only intended
research paths, and preserve other worktrees and `search/proposals/`.
