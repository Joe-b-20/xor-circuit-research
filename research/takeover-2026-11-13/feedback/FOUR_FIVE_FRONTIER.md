# The four- and five-nonclean label profiles

2026-11-13. Hand deductions about actual label values and their chronological availability. No circuit search or finite-family checks. The profiles below remain open at total cost at most 21.

## Label geometries allowed by the trace constraints

Consider eleven consumer-bearing gates with five actual entry occurrences. Let \(D\) be the three-dimensional clean diagonal and \(U\) the four-dimensional entry span. The [five-entry trace theorem](../compatibility/QUOTIENT.md#five-entries-and-six-mirrored-gates) gives a unique relation on the labels whose support is exactly the odd trace positions. Suppose there are four or five nonclean labels. They are distinct, and the clean label in the four-nonclean case is nonzero. Thus all five labels are distinct.

With four nonclean labels, an even number of their traces are odd, and at most two traces in the whole list are even. If exactly two nonclean traces are odd, the other two use both even trace values, so the clean trace must be odd. If all four nonclean traces are odd, the clean trace can be even or odd under these parity and rank constraints. This yields the following algebraic profiles:

- **Four nonclean labels with a four-term relation.** The four form an affine plane \(q+W\), where \(W\subset D\) has dimension two. The clean label \(h\) is outside \(\operatorname{span}(q+W)\).
- **Four nonclean labels with a three-term relation.** The unique relation is \(n_1+n_2+c=0\), where \(c\) is the clean label. The nonclean labels \(n_1,n_2,n_3,n_4\) form a basis of \(U\).
- **Four nonclean labels with a five-term relation.** All five traces are odd, and the clean label is \(n_1+n_2+n_3+n_4\). The nonclean labels again form a basis of \(U\). The trace constraints alone do not exclude this profile; no consumer realization is asserted here.
- **Five nonclean labels.** The unique relation uses four of them, by [the all-nonclean interface theorem](ENTRY_RETURN_RIGIDITY.md#a-further-restriction-in-the-all-nonclean-five-entry-interface). Those four form an affine plane \(q+W\) and the fifth \(h\) is outside its linear span.

The odd-trace support is the relation of the entry **labels**. The separate relation on the **traces** has support on the nonclean labels, so in the five-term profile it only requires the four nonclean traces to sum to zero. It does not require all five traces to sum to zero.

## Cost-preserving replay before the outside-plane label is read

In either affine-plane profile, consider exits strictly before the first actual read of \(h\). By the causal entry-span invariant, such an exit belongs to the span of the plane labels already read.

With at most two previously read plane labels, each value in their span is already supplied or is one XOR away. With at least three, their pair sums cover the entire two-dimensional \(W\). The nonclean points of \(\operatorname{span}(q+W)\) are exactly the four plane labels. A nonredundant exit cannot equal any such label: the [collision theorem](ENTRY_RETURN_RIGIDITY.md) excludes returning an actual nonclean entry label at the eleven-gate consumer budget. Therefore every exit before the first read of \(h\) can be replayed at cost at most its original one gate. This conclusion makes no assumption about when the source gate supplying \(h\) itself occurs.

## Replay for the three-term relation

Suppose the labels satisfy \(c=n_1+n_2\), with \(n_1,n_2,n_3,n_4\) independent. Split \(U\) as the direct sum of their first and second pair spans. In the first span the three nonzero values are exactly the three actual labels \(n_1,n_2,c\). As soon as two of them have been physically supplied, the third costs at most one XOR. If needed before its original source gate, that XOR can be paid by bypassing the original gate when it is reached. If the value is originally supplied first, there is no extra gate. Thus completing the first group costs no net extra work. In the second group only the pair sum \(p=n_3+n_4\) might need one extra gate. Compute it when first needed, or append it after replay. Until both labels arrive, every exit expression uses only the earlier portion of that group, by entry-span chronology and the direct-sum decomposition.

Every exit therefore uses at most one XOR from physically available group values, with total replay cost at most \(G_0+1\). The replay preserves the four source rows and supplies independent clean values \(c,p\). Append the clean pair sum \(n_1+n_3\), which is independent of \(c,p\) because the four \(n_i\) are a basis. The resulting augmented source supplier costs at most \(G_0+2\). By [A12](../augmented/PROOF.md), \(G_0\ge10\).

In fact \(G_0\le10\) forces the original physical clean span to have rank exactly one. To prove this, suppose an original clean \(v\) is independent of \(c\), and write \(f=n_1+n_3\).

- If \(v\notin\langle c,p\rangle\), replay and append \(c+p\). The four clean values \(c,p,c+p,v\) give a triangle and independent fourth at cost at most \(G_0+2\).
- If \(v=c+p\), replay and append \(f\). The same triangle \(c,p,c+p\) and independent \(f\) are available within \(G_0+2\).
- If \(v=p\), the second group is also entirely made of original values, so it can be completed early at net zero cost, just as the first group. Append \(c+p\) and \(f\) to this cost-preserving replay, again giving the four values within \(G_0+2\).

The [clean-triangle lower bound](FOUR_DIAGONALS.md) requires thirteen source gates in each case, a contradiction. Thus \(c\) spans the nonzero physical clean values of any candidate in this profile with \(G_0\le10\). Together with the preceding augmented count, such a candidate has exactly ten source gates and clean rank one. The argument does not exclude that case.
