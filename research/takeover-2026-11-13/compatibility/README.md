# Actual supplier compatibility

2026-11-13, continuing reviewed commit `098e5d4` on `research-2026-11-13-structural`.
Hand proofs with independent machine reviews, not formal verification or human
certification. **The unrestricted interval remains 75 <= L(MixColumns) <= 88.**

## A consumer's required labels may span the right space but still be unavailable

The strongest new result is [Theorem S](INTERFACES.md). A ten-gate first sheet computing
`U_c=E_c(b)+s_c(a)`, with block `a` free, can supply at most **four distinct values in
any coset of the even diagonal** `D={v(b)+v(a): v even}`. Available values include its
gates, ordinary inputs, and every free vector, so this bounds actual supply rather
than just a list of charged gates.

The previous eleven-gate avoidance theorem forces five distinct supplier values in one
nonzero coset when the consumer uses no clean diagonal label. The new cap therefore
excludes that entire consumer class after any ten-gate first sheet. This is an actual
compatibility result, beyond the rank and geometric constraints of earlier passes.

The proof explains the obstruction. A crowded odd coset would leave only two even
physical gates. The four ordinary inputs and four required outputs have no relation
shorter than their total eight-term relation, so each even gate can participate in at
most two relevant pairs of odd values. A reduced circuit can use each three-value XOR
relation only once. There would be room for four non-entry gates, while the sheet needs
at least six. The even-coset case follows instead from first occurrences of own-block
masks and the required entry count. No family of circuits is enumerated.

The theorem also gives a sharper result when the producer's available clean-diagonal
span has dimension at most one: an eleven-gate consumer must use four distinct nonclean
values in one coset and one nonzero clean value. The concrete ten-gate diagonal supplier
from the preceding pass has no coset with four available values. It therefore cannot
extend to a joint 21-gate circuit under the no-feedback hypothesis. Other ten-gate
producers are not excluded by this producer-specific result.

## Unneeded free directions have an explicit gate cost

[QUOTIENT](QUOTIENT.md) proves a general entry-deletion principle. Let `D` span the
required free parts of a consumer's outputs. If a selected set of entry occurrences has
label span disjoint from `D`, project those labels to zero while fixing `D`. Each selected
entry gate becomes a wire. Thus

    K >= L_D + number of selected entry occurrences.

Repeated labels count by occurrences. In particular, if the actual entry-label span
has `c` dimensions beyond `D`, then `K>=L_D+c`. This is a structural reduction for any
ordinary input map with one entirely free vector space. For the four-triple sheet it
gives the sharp explicit bound `K>=10+c`, with matching constructions for every available
quotient dimension.

For eleven-gate sheets, the result and the transpose distinguish the four-entry and
five-entry mixed interfaces. Nonclean labels lie in a single coset and cannot repeat;
clean labels can repeat. Their actual repetitions are controlled by the parity vector
of the influence traces. An explicit eleven-gate example shows why label repetition
and trace repetition must be distinguished.

The same deletion argument shows that any hypothetical joint 21-gate circuit under
no-feedback must actually read only even labels from its free block `a`. Reading an odd
label costs at least a twenty-second gate in that class. This is not an unrestricted
MixColumns bound.

## Diagonal supply and controls

[DIAGONALS](DIAGONALS.md) gives a compact twelve-gate event-free construction for four
rows and three independent diagonals. Requiring all four pure-own triples as additional
available values raises the event-free minimum to exactly thirteen. The twelve-gate
construction avoids that requirement and shares mixed rows with diagonal production.
The general augmented-sheet minimum remains between eleven and twelve.

[CONTROLS](CONTROLS.md) preserves two failed shortcuts. A six-gate triple-sum mirror can
use overlapping even pairs whose span omits the all-ones vector. Also, an already known
ten-gate sheet supplies three independent pure even own-block values. Requiring a pure
even basis therefore does not by itself force another gate. Neither false inference is
used in the compatibility proofs.

## Remaining mathematical obligation

The joint 21-versus-22 gap remains open. The `(11,10)` split still asks whether eleven
first-side gates can supply three independent diagonal values. In the `(10,11)` split,
the wholly nonclean consumer is now excluded; mixed interfaces using actual clean
suppliers remain. The useful next step is a joint bound on clean-diagonal supply and
coset occupancy, or another relation-capacity argument that handles several populated
cosets. Counting their linear span alone would lose the new obstruction.

## Review and direct checks

Read the independent [supplier review](reviews/interfaces-review.md),
[entry-deletion and trace review](reviews/quotient-review.md), and
[diagonal-supply review](reviews/diagonals-review.md). The primary agent also reconstructed
the supplier's relation count independently. Review clarified the one-even-helper orbit
argument and the treatment of an even gate that is itself an entry.

Run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/takeover-2026-11-13/compatibility/check_compatibility.py
```

[Saved results](check-results.json) verify six specified constructions, including explicit
projections removing one or two gates, the repeated-clean-label interface, the twelve-
and thirteen-gate diagonal circuits, and both controls. The supplier cap and universal
lower bounds rely on hand arguments. No SAT, circuit search, exhaustive enumeration,
exact least-gate search, or computer-driven case elimination was run.
