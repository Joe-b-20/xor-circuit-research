# Independent review of the five-diagonal obstruction

2026-11-13. Reviewed the saved `../FIVE_DIAGONALS.md`, using the existing physical relation-rank theorem, A12, and chronological rank-three replay. No circuit search, enumeration, or machine case list was used.

**Conclusion: the thirteen-gate source lower bound and the unrestricted joint corollary for exactly ten consumer-bearing gates are sound. No substantive gap found.** The proof does not need to forbid local ternary exits or assume that first-sheet ancestors avoid the consumer block.

## The source lower bound

Five distinct nonzero diagonal values have five distinct nonzero even own masks, disjoint from the four odd target triples and the ordinary input units. These give nine different first-occurrence gates. Entry gates repeat an earlier own mask, so the rank-three row-label requirement needs three additional gates. At size at most twelve, equality is forced: exactly twelve gates and three entries. Their labels span the three-dimensional even free space, so all computed free parts are even without a further parity assumption.

Five distinct nonzero elements of the three-dimensional binary diagonal space span it, since a two-dimensional subspace has only three nonzero elements. Thus `D` is contained in `V=span H`, and the kernel of `rho` on `V` is exactly `D`. The equality `dim V=3+r` follows.

The physical node count is `|O|+|H|=16`. Nine independent actual non-entry equations and the general relation-rank theorem give

    9 <= 13-c-r,       c+r<=4.

All eight odd residues occur at named nodes. Since every odd-pair edge changes residue by an element of `rho(V)`, at least `2^(3-r)` components occur. Values `r=0,1` violate the preceding inequality, so `r>=2`.

At least two physical even values must have nonzero residue to span this image. Together with at least five clean values this requires at least seven even gates, leaving at most one odd helper besides the four rows. Both remaining relation estimates are valid:

* With no helper, at most three even values are nonclean. Each has at most one named-pair representation; clean values have none. Odd-pair rank is at most three, and even-only rank is at most `|H|-dim V<=3`.
* With one helper, seven even gates consist of exactly five clean and two nonclean values. All clean pairs together contribute at most one equation, since the helper has only one possible same-residue named partner. Each nonclean value has at most one named pair and one helper pair. Odd-pair rank is at most five, and even-only rank is at most two.

The respective total bounds six and seven are strictly below nine. These arguments allow dependencies among even values and allow whole-block cancellations. They do not assume a specific diagonal basis or enumerate source circuits.

## Applying source replay to feedback

With exactly ten consumer-bearing gates, the existing entry-deletion theorem confines every actual entry label to the rank-three diagonal `D`, and the consumer target parts force those labels to span `D`. Treating zero-consumer operands as free is a legitimate relaxation even when their physical producers were exits. The chronological replay preserves those actual source values, including any whose original computation used feedback.

If all source values can be replayed without overhead, at most eleven source-side gates would supply the four first-sheet rows and three independent diagonals, contradicting A12. If the exceptional rank-three replay step occurs, the three currently available independent diagonal values, its new pair sum, and its ternary return are five distinct nonzero physical diagonal values. Their distinctness follows directly from independence of the three old values. All five can be retained as designated outputs of the completed source-only replay without adding gates.

The replay has at most `G_0+1<=12` gates and still supplies all four first-sheet rows. The five-diagonal source lemma therefore contradicts it. Any later coincidence with a source value can only reduce the replay count; it cannot invalidate the contradiction or remove a designated value already supplied.

Thus `G_0>=12` when the consumer-bearing count is ten, giving total cost at least twenty-two. The recorded twelve-source-plus-ten-consumer construction attains that count in this class. The qualification about the consumer-bearing count is essential: the argument does not exclude a cheaper circuit having eleven or more consumer-bearing gates and a smaller zero-consumer part.

## Witness compatibility and editorial check

The explicitly checked early ternary-return consumer is compatible with the theorem. It supplies a local hard exit from three labels, but does not also supply the first-sheet rows within the disputed source budget. Its later-label cancellation also distinguishes local replacement cost from total replay cost.

At review time the final link in `FIVE_DIAGONALS.md` names `TERNARY_EXIT.md`, while the saved construction note is `TERNARY_CONSUMER.md`. Align that link during integration. This is an editorial link issue only.
