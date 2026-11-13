# XOR structural research: checkpoint, 2026-11-13

Research branch: `research-2026-11-13-structural`. Current continuation follows reviewed
commit `098e5d4`; see [actual supplier compatibility](compatibility/README.md).
Verified base: `e89b8a25f69195266f1e24e815cb96c7526a3511` on local and remote
`phase-2026-11-09`. The original worktree, the other research worktree, and untracked
`search/proposals/` were preserved. Our worktree is under this chat's `work/xor-structural`.

**Unchanged: 75 <= L(MixColumns) <= 88.** No claim that 88 is optimal.
Results have hand proofs and independent machine review, not formal verification or
human certification. Local and conditional bounds are not unrestricted bounds.

## Read next

1. [Current summary and judgment](compatibility/README.md).
2. [Producer coset cap and joint consequences](compatibility/INTERFACES.md).
3. [General entry deletion and mixed interfaces](compatibility/QUOTIENT.md),
   [diagonal supply](compatibility/DIAGONALS.md), and [controls](compatibility/CONTROLS.md).
4. [Previous pass](row-cost/README.md): exact local costs, source saturation,
   completion geometry, and the eleven-gate avoidance theorem.
5. [Earlier continuation](continuation/README.md): [sparse sharing](continuation/SPARSE.md),
   [affine completion theorem](continuation/AFFINE.md), [internal events](continuation/INTERNAL.md).
6. [First-pass summary](SUMMARY.md), [H/HR](directions/independent.md),
   [joint reconstruction](directions/JOINT.md), [projection repair](directions/PROJECTION.md),
   [foundational review](reviews/foundations-audit.md).

Reviews are linked from each pass's summary. The [historical checkpoint](../structure-2026-11-11/CHECKPOINT.md)
and [record](../structure-2026-11-11/RECORD.md) remain the earlier research trail.

## New results and their limits

- **Actual supplier cap.** Any ten-gate first sheet supplies at most four distinct values
  in each coset of the clean even diagonal D, including inputs and free values. The proof
  combines parity, first occurrences, and an injective count of possible XOR relations.
  The five-value all-nonclean eleven-gate consumer therefore cannot follow it.
- **Rank-one clean supply.** If a ten-gate producer's available clean-diagonal span has
  rank at most one, an eleven-gate consumer would require four distinct nonclean values
  in one coset and one nonzero clean value. The previous explicit ten-gate diagonal
  supplier has no coset of size four, so that particular producer cannot extend to a
  joint 21. Other producers and mixed interfaces remain open.
- **General entry deletion.** If selected entry occurrences have label span disjoint
  from the target free-part span D, projecting that span to zero removes all those gates.
  Thus `K>=L_D+|I|`, including repeated occurrences, and in particular `K>=L_D+c` for
  quotient rank c. For four-triple sheets this is the sharp explicit `K>=10+c`.
  Mixed eleven-gate trace structures are classified by four or five entries; nonclean
  labels cannot repeat, but clean labels can. Any hypothetical no-feedback joint 21
  must actually read only even free-a labels.
- **Diagonal interface.** A compact event-free twelve-gate circuit supplies four rows
  and three independent diagonals. Requiring all four pure-own triples as well gives
  exact event-free cost thirteen. The unconstrained augmented cost remains 11 or 12.
  Controls: two even helpers need not span all-ones, and a ten-gate sheet can supply a
  rank-three pure-even basis. Neither condition alone forces a further gate.

## Earlier results that constrain future claims

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

Seek a joint bound on clean-diagonal supply and coset occupancy, or extend the relation
count to several populated cosets. Linear span alone loses the actual-supply obstruction.
The joint 0/1 problem still needs both: exclude three independent diagonal suppliers in
eleven first-side gates, and exclude the remaining mixed eleven-gate consumer interfaces
after a ten-gate producer. The entirely nonclean branch is now excluded. No improved
unrestricted MixColumns lower bound is established.

## Method and reproducibility

No SAT, exhaustive enumeration, exact least-gate search, heuristic circuit search, or
computer-driven case elimination was run. Universal claims rely on hand proofs.
[Current checks](compatibility/check-results.json) evaluate six specified constructions:
one-/two-direction deletion, repeated clean labels, diagonal circuits, and both controls.
[Previous checks](row-cost/README.md#review-and-direct-verification) cover local costs,
the 188/184 comparison, the 145-gate witness, and the two original interface circuits.
[Earlier checks](checks/README.md) and [continuation checks](continuation/check-results.json)
remain reproducible; three small external circuit fixtures are saved in the repository.

The Windows-backed checkout reports executable-bit differences; use Git with
`-c core.filemode=false`. Shared repository config was not changed. Stage only intended
research paths, and preserve other worktrees and `search/proposals/`.
