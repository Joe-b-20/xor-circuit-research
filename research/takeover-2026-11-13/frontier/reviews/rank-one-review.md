# Review of the rank-one supplier exclusion

2026-11-13. Independent machine proof review of [RANK_ONE](../RANK_ONE.md). No circuit search or family checks were run.

## Even own parity

A four-value even coset necessarily contains its one free value and three gates with distinct nonzero even own masks. The first occurrences of these masks and of the four own triples leave exactly three entries. Thus every repeated own mask comes from an entry, and the entry labels form a basis of the even free space. The clean value \(h\) must use one of the three even fibres, so its direction lies in the difference span of the four-value coset. Completing \(D\) therefore forces the three even own masks to be independent.

The three even fibre roots have independent own projections. In each fibre an entry adds its independent free label, and that label is also the difference of its endpoint gate values. Thus the span of the physical even values is the direct sum of the span of the three roots and the span of the even-fibre entry labels. Its rank equals the number of physical even gates. In particular there are no even-only relations.

With no odd helper, every odd pair is named. The clean value has no named pair and each of the other five even values has at most one, fewer than the seven relations needed. With two odd helpers, every possible odd edge preserves residue or adds the one nonzero even residue \(e\). The eight named residues occupy four groups modulo \(\langle e\rangle\). The odd graph therefore has at least four components, and its ten odd nodes give relation rank at most six by the zero even kernel.

With one odd helper \(x\), the three residue-\(e\) even values have at most three named pairs and one helper pair in total. The latter bound follows because the helper's opposite residue determines a unique named endpoint, which then fixes the even sum. The clean even value has at most one pair, using \(x\). The remaining even value has at most two pairs, one named and one involving \(x\). Reaching seven relations requires equality in each count. The named endpoint of the clean pair and that of the residue-\(e\) helper pair form a named residue-\(e\) pair of sum \(h+g_j\). This sum differs from every \(g_i\), by independence of the five physical even values. Hence it is the fourth pair in the residue-\(e\) matching. The sum of the four pair sums is the total of the eight named values, which is zero. Cancelling \(g_j\) gives a relation among \(h\) and the two other \(g_i\), contradicting independence.

## Odd own parity

A four-value odd coset \(B\) contains one named value and three helpers. If two pairs in \(B\) summed to the clean value \(h\), the pairs would be disjoint and together would make a four-point affine plane whose difference span contains \(h\). That span has dimension two and would not complete \(D\) together with \(h\). Thus the clean direction has at most one pair inside \(B\) under the claimed completion condition.

With four odd helpers, the one outside \(B\) creates one additional residue class of size two. The clean even value has at most one pair in each of these two classes. The nonclean even value has at most two pairs touching the crowded classes. If its residue matches those two classes together, the smaller class has size two. Otherwise each crowded class can only match a singleton. There is at most one additional wholly named pair. With only two even values no even-only relation exists, so the five-pair bound is below the six non-entry gates required.

With three odd helpers, there is no other crowded residue. The clean value has at most one pair and the two nonclean values at most two each. Six non-entry gates would require all five pairs and the one even-only relation \(h+k+l=0\). The nonclean values have the same residue. Their crossing pairs therefore use the same outside named endpoint \(n\), with distinct endpoints \(x,y\) inside \(B\). The even-only relation gives \(h=x+y\), so the clean pair is exactly this pair. The three odd-pair equations and the even-only equation sum to zero as formal node equations. They cannot all be executed, because actual non-entry equations are independent by their latest-result pivots. The six-gate requirement is impossible.

## Consumer and feedback scope

The previously established rank-one interface condition requires four distinct nonclean labels in a single coset plus one nonzero clean label. Their span can contain \(D\) only if the clean direction and the coset differences complete \(D\). The preceding proof excludes that possibility. Clean rank zero already lacks the necessary clean label.

With one extra supplier-side gate, at most ten consumer-bearing gates remain. All their used labels must then be clean by the quotient-rank bound. The additional gate supplies at most one new independent clean value, including when it is a consumer-block exit. Starting from rank at most one leaves the required rank-three span unavailable. With at least two extra supplier-side gates the ten-gate consumer minimum already gives 22. The scope is the class containing the prescribed ten-gate first-side computation under the no-feedback hypothesis. Rank-two suppliers and the general eleven-gate augmented supplier remain open.
