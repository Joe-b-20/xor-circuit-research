# Independent review of diagonal confinement

2026-11-13. Reviewed the saved `../DIAGONAL_CONFINEMENT.md` against chronological rank-three replay, A12, the five-diagonal lower bound, and the entry-deletion theorem. This is a hand review; no circuit search or case enumeration was used.

**Conclusion: both the arbitrary-consumer-budget all-clean theorem and the stated parity-projection extension are sound. No substantive gap found.**

## The source bound does not depend on consumer gate count

When every actual entry lies in `D`, induction through consumer-bearing gates puts each source part in the span of earlier actual entries, regardless of the number of such gates. The required consumer source parts span `D`, so the actual entries span it. A nonzero diagonal cannot be a source coordinate input or a wholly free `a` value; three independent physical source-side values are therefore present.

If `G_0<=11`, rank-three replay preserves the four first-sheet rows and these actual labels using at most `G_0+1` source-only gates. If the replay needs no overhead, A12 excludes its cost at most eleven. If its exceptional step occurs, the earlier independent diagonal basis, the new pair sum, and the returned triple sum are five distinct nonzero diagonal values retained in a replay of at most twelve gates. The five-diagonal theorem excludes that possibility. Neither argument uses the consumer budget `K`.

Thus `G_0>=12` is valid even if source rows have consumer-bearing ancestors. Combining it with the existing local sheet bound `K>=10` gives total at least twenty-two in this class. The cited twelve-source-plus-ten-consumer construction attains the source bound.

## The displayed projection is an allowed source transformation

For `h=beta(b)+alpha(a)` with even `beta` and odd `alpha`, the mask `sigma=alpha+beta` is odd. The map

    P(x)=x+parity(x) sigma

is linear over `F_2`. It fixes every even mask and sends `alpha` to `beta`. Therefore it fixes each required adjacent-pair `a` mask, fixes the diagonal space `D` pointwise, and maps `h` to the clean diagonal `(beta,beta)`. Every actual entry in `D+<h>` maps into `D`.

Only the `a` components are transformed. Ordinary `b` and `z` inputs remain available with their original values; transformed `a`-only values remain free. All required rows are unchanged, and the ordinary consumer part of every physical gate is unchanged. Applying the transformation to the original wiring is consequently a valid circuit construction, even with feedback or whole-block cancellation.

Removing projected zero, free, or duplicate values can only reduce the source count. The all-clean theorem applies to the transformed circuit, giving at least twelve source gates there and hence at least twelve in the original. Since the original count is used for the final total, `K=11` indeed gives at least twenty-three original gates, even if normalization of the projected consumer removes a gate.

## Scope

The parity condition is an explicit sufficient condition on the one possible nonclean quotient direction. Adding a vector of `D` does not change either component parity, so the condition is independent of the chosen representative of that quotient class. The proof does not handle an arbitrary nonclean direction, and the note correctly leaves those directions unresolved.

The final generalization states the necessary availability conditions for a source transformation: required outputs and consumer coordinates are preserved, transformed ordinary inputs remain available without added computation, and transformed free values stay free. Under these conditions, and with the stated source-count condition, applying the all-clean theorem is legitimate. No unrestricted twenty-two-gate joint bound follows from the cases proved here alone.
