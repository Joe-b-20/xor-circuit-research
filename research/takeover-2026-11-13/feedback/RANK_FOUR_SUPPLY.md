# Rank-four entries and three physical clean directions

2026-11-13. Hand proof by chronological replay and the prescribed-diagonal bounds. No circuit search or family checks.

In the unrestricted joint 0/1-sheet model, let \(D\) be the three-dimensional clean diagonal on source blocks \(b,a\), with \(a\) free. Suppose the actual entry labels read by consumer-bearing gates span a four-dimensional space \(U\supset D\). If the original source-side values include three independent physical clean diagonals, then there are at least eleven source-side gates.

## Replay with a prescribed pairing

Select a basis of \(U\) greedily in the order of actual entry-label occurrences. Thus the basis elements selected before any given time span all entry labels read by that time. Fix any partition of the four basis elements into two pairs. Replay source-side gates chronologically. An exit has source value in the span of the prior actual entry labels, by the [causal span invariant](GENERAL_REPAIR.md). Its representation in the chosen basis therefore uses only basis elements already supplied at that point.

For either pair, compute its sum by one extra gate on the first need for both elements in an exit expression, unless that sum is already available. The two group values then supply the exit in at most one XOR. Reproduce ordinary source gates from their already supplied operands, bypassing values already available. Append either unused pair sum after replay so that both sums are physically supplied. The resulting source-only circuit contains every original source value and both pair sums, using at most \(G_0+2\) gates if the original circuit had \(G_0\) source gates.

If a chosen pair sum is itself an original source value, this replay costs at most \(G_0+1\). When the original occurrence comes first, its value is already available for pair completion. When pair completion comes first, the original gate can later be bypassed. The same reasoning works for a base value. This count concerns physical masks and holds for arbitrary interleaving of source-side and consumer-bearing gates.

Assume toward a contradiction \(G_0\le10\) and let \(a_1,a_2,a_3\) be three independent original physical clean diagonals. Each paired replay preserves those diagonals and the four source rows. Thus no pair sum from any pairing can be an original source value, since the saving just described would contradict [A12](../augmented/PROOF.md) with an at-most-eleven-gate augmented supplier.

## Pairing by quotient class

There are one through four nonclean basis elements, since the quotient \(U/D\) has dimension one.

- **One nonclean element.** Pair two clean basis elements together. Their sum and those two elements form a clean triangle. The third clean basis element is independent of that triangle. Replay supplies these four values in at most twelve source gates, contrary to the [clean-triangle bound](FOUR_DIAGONALS.md).
- **Two or four nonclean elements.** Pair elements of like quotient class. Both pair sums are clean, and they are distinct nonzero values by basis independence. As neither is an original value, replay supplies these two in addition to \(a_1,a_2,a_3\). The [five-diagonal bound](FIVE_DIAGONALS.md) excludes the resulting twelve-gate budget.
- **Three nonclean elements.** Their three pair sums are the nonzero elements of a two-dimensional subspace \(W\subset D\), by basis independence. Each occurs as one of the sums for a possible pairing. None can be an original value, by the saving argument. Therefore \(a_1,a_2,a_3\) lie in the complementary affine coset \(D\setminus W\). The sum \(a_1+a_2\) is one of the three available choices of nonclean pair sum. Make that pairing. Its replay supplies the triangle \(a_1,a_2,a_1+a_2\) and the independent \(a_3\) in at most twelve gates, again contrary to the clean-triangle bound.

Every possible quotient composition leads to a contradiction. Hence \(G_0\ge11\).

## Consequence for the remaining joint profiles

An eleven-gate consumer with rank-four actual entry span in a joint circuit of total at most 21 must have source-side physical clean span of dimension at most two. A rank condition on the entry span does not by itself ensure the relevant diagonals occur as physical values. In particular this result does not exclude a rank-four interface whose clean directions arise partly from differences of nonclean values.
