# Twelve consumer gates: structural restrictions and the remaining obstruction

2026-11-14, continuing reviewed commit `cfab8f6`. The arguments below have independent machine reviews, not formal verification or human certification. They use chronological linear algebra, gate relations, and specified constructions; no circuit search, enumeration, or computer-driven case elimination was used.

The earlier phase proved joint minimum 22 for exactly ten or eleven consumer-bearing gates, even with feedback. This phase does **not** close the twelve-consumer case. It supplies general equality and replay theorems, a stronger source bound, and necessary conditions for that next case. The unrestricted MixColumns interval remains `75<=L<=88`; the block-monotone lower bound remains 85.

## General results

**Equality in quotient cost determines all projected collisions.** Let actual entry labels span `U`, target source parts span `D subset U`, and let `L_D` be the consumer minimum with `D` free. If `K=L_D+dim(U/D)`, choose any actual quotient basis and let `C` span its full labels. The physical consumer nodes with equal values modulo `C` are exactly the connected components of the selected entry-edge forest. Any additional collision would permit an extra deletion and violate `L_D`.

It follows that every actual nonclean label has exactly one physical difference pair, its own entry edge. It cannot occur at another entry or be newly supplied by an exit. Returns in the chosen complement are sums along selected entry paths, with all labels read earlier. This permits indirect feedback through changed values; it does not make every return belong to one complement. See [SATURATED_QUOTIENT](SATURATED_QUOTIENT.md).

**Gates outside the relaxed output cones must be quotient coloops.** At the same equality, an outside gate must be selected in every actual quotient basis: otherwise projection leaves a dead paid gate in a minimum consumer. Thus it is an entry whose quotient direction is absent from the span of all other entry occurrences. There are at most `dim(U/D)` such gates. This keeps feedback-only gates in the accounting instead of assuming output-cone trimming. See [SATURATED_TAILS](SATURATED_TAILS.md).

**Every target subspace has a chronological replay complement.** Choose actual entry representatives greedily modulo `D`, and let `C` span them. Every entry-prefix span splits under `U=D direct-sum C`. Credited replay consequently completes both groups while preserving all original source values for at most

    G_0 + (2^dim(D)-1-m_D) + (2^dim(C)-1-m_C),

where `m_D,m_C` count their nonzero values already physically present in the original source. This works for any target subspace and arbitrary entry order. It charges missing physical values, rather than virtual span directions. See [FULL_DIAGONAL_SUPPLY](FULL_DIAGONAL_SUPPLY.md).

## New source bounds

For the two-sheet source rows and rank-three clean diagonal `D`:

- [Rank-four source floor](RANK_FOUR_SOURCE_FLOOR.md): if the actual entry space has rank at most four, then `G_0>=10`, at any consumer budget. At rank four, two physical clean directions give the stronger `G_0>=11`; one gives `G_0>=10`. The zero-clean case uses the six-value coset cap to confine useful feedback to a single three-term return.
- [Full-diagonal supplier](FULL_DIAGONAL_SUPPLY.md): supplying the four source rows and all seven nonzero diagonal values requires at least fifteen source gates. No fifteen-gate attaining construction is claimed. At fourteen gates, own-mask first occurrences and source entry rank exhaust the budget; physical odd-pair and even-only relation ranks then cannot support the required independent gate equations.
- At entry rank five, the chronological complement has rank two. Completing it and `D` gives `G_0>=5+m_D+m_C>=7+m_D`. This controls the number of original physical clean values, not just their span rank.

## What any twelve-consumer candidate below 22 must satisfy

Write its total as `G_0+K<=21` with `K=12`. Quotient deletion gives entry rank at most five; the new source floor excludes rank at most four. Thus

    G_0<=9,       dim U=5,       dim(U/D)=2.

The consumer saturates quotient cost, so the collision and coloop theorems apply globally. The full-diagonal replay bound implies `m_D<=2`. If `m_D=2`, necessarily `G_0=9`, and the sum of the two greedy quotient representatives is absent from the original physical source-value set.

There is **at most one consumer-bearing gate outside the relaxed output cones**. Two would leave a ten-gate target consumer requiring three independent physically supplied clean labels, contradicting `m_D<=2`. If one outside gate survives, it is an entry and must support at least two distinct, nonredundant returns. A single return can be reassociated to move that entry back to the source without increasing the total, contradicting the already closed eleven-consumer case. This one-tail case remains open.

If all twelve consumer gates lie in the relaxed output cones, let `tau` count actual entry occurrences. Entry rank requires `tau>=5`; the ordinary triple minimum requires `12-tau>=6`. Hence only `tau=5` or `tau=6` remains. [TWELVE_ENTRY_WIRES](TWELVE_ENTRY_WIRES.md) gives:

- **Six entries.** The ordinary circuit and literal mirror have six gates. Trace rank is four. The actual-label map has one relation, exactly the indicator of the odd trace positions; the two-dimensional relation space on the traces equals the quotient-signature row space. The six-gate wire restrictions survive, but repeated traces and a repeated clean label have not been excluded. If all traces are odd and pairwise distinct, replay has zero overhead and the candidate is excluded.
- **Five entries.** The actual labels are independent. The seven-gate mirror has exactly three independent even trace values, with multiplicities `(3,1,1)` or `(2,2,1)`. Different trace classes cannot meet in an entry tree. A surviving candidate has exactly one ordinary-mask fibre with two entry-tree roots, all other fibres have one root, and it must use a nonredundant exit connecting the two components of that fibre. All exits confined to individual components would permit a replay contradicting the existing source bounds.

These two entry-count descriptions require the target-cone hypothesis. They are not a complete classification of the global twelve-gate problem. In particular, the one-tail case must be handled separately.

## A limitation that changes the next step

A fixed seven-gate ordinary circuit computes `p=x0+x1`, `q=x2+x3`, `t=p+q`, and the four outputs `t+xi`. The distinct even wires `p->t` and `q->t` both have ordinary derivative `(1,1,1,1)`. Thus the even-wire separation theorem genuinely fails once a seventh ordinary gate is allowed. It cannot be extended by changing an entry count in the earlier proof.

The most promising local task is to understand the cost of returns between different entry-tree roots, or several returns sharing the unique outside entry. Both are concrete ways in which the consumer can return a value that is not a path sum inside one previously controlled tree. A reusable theorem charging that shared work would be more valuable than a long subdivision of six-entry trace patterns. The equality theorem and chronological complement are useful beyond MixColumns regardless of whether this next case closes.

## Review

Independent reviews cover [rank-four supply](reviews/rank-four-source-floor-review.md), [full-diagonal supply and complement replay](reviews/full-diagonal-supply-review.md), [saturated collisions](reviews/saturated-quotient-review.md), [outside-cone gates](reviews/saturated-tails-review.md), and [the wire reductions and counterexample](reviews/twelve-entry-wire-review.md). A [final scope audit](reviews/twelve-frontier-review.md) checked this synthesis against those notes. The primary agent also checked the arguments and their scope. These are mathematical hand arguments subjected to machine review, with no claim of formal verification or literature novelty.
