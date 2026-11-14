# Eleven consumer gates: collisions and the remaining return

2026-11-13, continuing reviewed commit `6801e98`. Structural hand proofs with independent
machine review, not formal verification or human certification. No circuit search or
computer-driven case elimination was used.

The eleven-gate consumer case is still open. This pass proves a general projection
bound on physical value collisions, extends diagonal confinement to every consumer
budget, and narrows the four-entry mixed case to one specific kind of return and
source supply. The unrestricted MixColumns interval remains **75 to 88**; the
block-monotone lower bound remains **85**.

## Projection pays for every merged physical value

[The collision theorem](ENTRY_RETURN_RIGIDITY.md) applies to any linear consumer.
Let `D` span the source parts required by its outputs, `L_D` be their minimum cost
with `D` free, and `U` span the actual entry labels. Choose a source subspace `C`
inside `U` and disjoint from `D`. Group all physical consumer gates and ordinary
consumer inputs by their full value modulo `C`. If

    delta_C = sum over occupied classes (class size - 1),

then the consumer gate count satisfies

    K >= L_D + delta_C.

Projection onto `D` along a complement containing `C` makes each class equal. Keep
its earliest representative and bypass the rest. No class contains two ordinary
inputs, so all discarded nodes are paid gates. The argument counts overlapping
collisions together and keeps gates used only by exits; it needs no source-first
assumption.

At `K=L_D+1`, every nonclean difference has at most one physical pair. If the difference
is an actual entry label, the entry edge already occupies that pair. A later exit
returning the label merely recomputes something that was supplied before the entry.
More generally, a return cannot be read verbatim as a later nonclean entry: the return
and the later entry would yield two distinct deletions. This still permits indirect
feedback that changes the returned value before re-entry.

For an eleven-gate all-nonclean five-entry interface, the five labels occupy an affine
plane plus one point of its complementary plane. Nonredundant nonclean exits are
confined to the other three points. Clean returns remain a separate possibility.

## Clean entries force twelve source gates at any consumer budget

[Diagonal confinement](DIAGONAL_CONFINEMENT.md) extends the preceding ten-consumer
argument: whenever all actual entries lie in the clean diagonal `D`, the source
side needs at least twelve gates, regardless of the number of consumer gates.
Rank-three repair either costs no extra gate, contradicting the augmented minimum
at an eleven-gate source budget, or creates five physical diagonal values, whose
source cost is at least thirteen. Thus an eleven-gate consumer with only clean
entries needs at least 23 total gates.

A concrete nonclean class has the same bound. If entries lie in `D+<h>` with the
ordinary source part of `h` even and its free-block part odd, a target-preserving
projection on the free block sends all entries into `D` without increasing source
cost. The original source still needs twelve gates. This does not cover the other
parity classes of the nonclean direction.

## The four-entry mixed case has a precise source obligation

[The four-entry reduction](FOUR_ENTRY_FEEDBACK.md) starts with the known eleven-gate
interface geometry: two clean labels `c,d` and two nonclean labels `n,m` form a basis,
with `e=n+m` completing `c,d` to a basis of `D`. Put `p=c+d`.

A chronological source replay needs at most the two additional physical values `e,p`:
every return splits into a value from each of the groups `{c,d}` and `{n,m}`. Add `e`
after replay if it was never needed, to obtain three independent physical diagonals.
The augmented minimum twelve then forces at least ten original source gates.

Consequently, at a hypothetical joint total of at most 21:

- The source has exactly ten gates.
- Its only original nonzero diagonal values are `c,d`. If `e` or `p` were original,
  their later bypass would save a repair gate. Any other diagonal would make five
  physical diagonals available in the twelve-gate replay, which is impossible.
- Every nonredundant exit is nonclean, and at least one returns `n+c+d` or `m+c+d`.
  Otherwise replay would need no intermediate, and adding `e` would give an
  impossible eleven-gate augmented supplier.

Projecting away the other nonclean label converts this necessary return to a ternary
return in a ten-gate, three-entry consumer. Its equal-own operands must lie in the
unique own-mask fibre with two non-entry roots; all other fibres have one root. This
is an exact structural reduction, not a proof that the remaining configuration can
or cannot be realized.

## Judgment and next questions

The useful mechanism is the joint count of original physical values and repair values.
A single nonclean direction is not a free credit: its entry already uses its allowed
collision, and a useful return must arrive elsewhere and often change before reuse.

For the four-entry branch, a particularly concrete source question remains: can twelve
source gates supply the four first-sheet rows and the four diagonals `c,d,c+d,e`, where
`c,d,e` are independent? A thirteen-gate lower bound would exclude this branch; the
current five-diagonal theorem does not establish it. No claim about this four-value
problem is made here. Alternatively one can investigate the required two-root ternary
pair directly. The five-entry mixed consumer needs its own further argument, as do
larger consumer budgets in the unrestricted joint problem.

Independent reviews cover [collision and causal return](reviews/entry-return-rigidity-review.md),
[diagonal confinement](reviews/diagonal-confinement-review.md), and
[the four-entry reduction](reviews/four-entry-feedback-review.md). The primary agent
checked the projections, physical-node deletions, chronological pair completion,
and the distinction between necessary conditions and exclusions. No new numerical
search or construction test is part of these universal proofs.
