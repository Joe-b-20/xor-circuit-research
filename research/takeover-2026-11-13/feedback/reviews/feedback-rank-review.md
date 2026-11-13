# Independent review of feedback rank bounds and causal repair

2026-11-13. Reviewed the saved `../FEEDBACK_RANK.md` against the existing [entry-deletion lemma](../../compatibility/QUOTIENT.md). The argument is a hand proof using causal span and linear projection. No circuit search or configuration enumeration was used.

**Conclusion: Theorem FX and its stated two-sheet consequences are sound.** The lower bound charges the rank of all returned values modulo the required target-label space; it does not charge each exit separately.

## Chronological span and the entry-deletion premise

Consumer coordinate inputs have zero source part. A consumer-bearing gate either adds an actually available source label to an earlier consumer-bearing value or adds two consumer-bearing values. Induction therefore places its source part in the span of actual labels already read. At an exit, the equal consumer parts cancel, leaving a source value in that same earlier span. Earlier exits may later become labels, but cannot create a direction outside that span. Thus the span `F` of all exits is contained in the full actual entry-label span `U`.

The required consumer outputs also have source parts in `U`, so their span `D` is contained in `U`. Granting all actual zero-consumer operands freely and keeping the consumer-bearing gates gives a valid consumer circuit with `K` counted gates. This is precisely the ordinary/nonzero-part model of the existing entry-deletion lemma. No assumption that all suppliers were originally computed before all consumer gates is needed for this relaxation.

The lemma supplies the substantive cost step

    K >= L_D + dim(U/D).

Its proof chooses actual entry occurrences whose quotient images form a basis, projects the free label space onto `D` while killing those labels, and bypasses the corresponding gates. This review relies explicitly on that proved projection lemma; chronological span alone would not give the gate lower bound.

Since `F` is contained in `U` and `D` is contained in `U`, the quotient `(F+D)/D` is a subspace of `U/D`. The claimed inequality follows. Repeated entry labels and repeated returned directions do not invalidate the argument: quotient dimension, rather than an occurrence count, is used here.

## The first-sheet rows are independent quotient directions

For the two-sheet model, the existing local sheet theorem gives `L_D=10`, with `D` the rank-three even diagonal space. A circuit with `10+c` consumer-bearing gates can therefore return an exit span whose image modulo `D` has rank at most `c`.

The residue of `U_i=(E_i,s_i)` is `E_(i+1)`. The four triple masks form the columns of `I+J`; over `F_2` in dimension four, `J^2=0`, so `(I+J)^2=I`. They are independent. Since `rho` kills every vector in `D`, a linear combination of selected `U_i` lying in `D` must have all coefficients zero. Thus any `k` selected first-sheet rows produced directly as exits contribute rank `k` to `(F+D)/D`, giving `K>=10+k`.

The examples of ten, eleven, and fourteen consumer-bearing gates are accurate consequences of this inequality. The final scope restriction is necessary and correctly stated: an output can have feedback among its ancestors without itself being an exit, and the theorem does not assign that output's quotient direction to `F` in such a situation. No unrestricted joint bound of twenty-two follows from FX alone.

## General repair: the saved two-group proof

I also line-reviewed the revised `../GENERAL_REPAIR.md`, whose main bound is

    h(d)=2^ceil(d/2)+2^floor(d/2)-d-2.

**Theorem FR is sound, including rank growth during replay.** The basis is chosen from physically available values of `D`; its elements are never moved between groups. Initial basis elements are original source inputs or free values. A later independent basis element can appear at an ordinary source-side gate, but not at an exit, because exits lie in the span of earlier entry values. Thus no basis element is borrowed from the future or created by an uncharged virtual combination.

When a new element joins a group of dimension `k`, the old nonzero group sums are already physical values. Computing the new element plus each old group sum takes at most `2^k-1` extra gates and completes the enlarged group. These additions do not increase the total rank. Every exit lies in the direct sum of the two current group spans and is therefore one XOR of two physically available group sums, allowing zero as stipulated. Its final XOR uses the original exit's one-gate allowance. Ordinary source gates likewise use at most their original allowance.

The completion costs of a group with final size `k` sum to `2^k-1-k`. Alternating the assignment keeps the two sizes balanced after every rank increase without any later rebalancing. Their total final cost is exactly the displayed upper-bound expression at the actual final rank. The monotonicity increment `h(r+1)-h(r)=2^floor(r/2)-1` is correct, including ranks zero through two, so replacing the actual final rank by the upper bound `d` is valid.

After source replay, all original source-side values are available. Replaying the original consumer-bearing gates in order preserves their values because every source operand and every earlier consumer-bearing predecessor is supplied. This proves the full no-feedback bound as well as the source-only bound; it does not merely repair the requested exits in isolation.

## Retained density and potential argument

The weaker alternative proof is also correct. For a missing nonzero `t`, both `S` and `S+t` avoid `0,t`; cardinality at least half the span therefore forces an intersection and a two-operand representation. If no such representation exists, some nonzero pair sum must be absent, because otherwise `S union {0}` would already be a subspace.

Each extra intermediate is added at fixed rank while the potential is positive, so it spends exactly one potential unit. The original exit's final gate is not charged as extra and can only decrease the potential. A newly supplied independent `D` value raises the rank by one and increases the potential by at most `2^(r-1)-1`; the zero-to-one transition has no increase. Initial potential is at most `f(r_initial)`, and telescoping gives `f(d)`. Source values outside `D` do not disturb this invariant. The argument is therefore valid without assuming an initial basis of the eventual entry space.

## Sharpness and scope of the repair theorem

The rank-three example has four distinct non-input targets and attains four gates. In a no-feedback realization its source parity needs two gates, while its three distinct consumer-bearing outputs require three disjoint target gates. The minimum is five. The rank-four example similarly has unrestricted minimum five and no-feedback minimum seven: the four-input source parity needs three source gates, disjoint from the four consumer-bearing target gates. The displayed separate source/consumer constructions attain both lower bounds. Thus the allowances at ranks three and four are sharp for full circuits, not just for an isolated exit-replacement routine.

The statement correctly avoids sharpness claims at higher ranks and claims no literature novelty. Its joint-problem specialization remains conditional on exactly ten consumer-bearing gates; neither general repair nor the rank tax alone establishes an unrestricted twenty-two-gate joint minimum.
