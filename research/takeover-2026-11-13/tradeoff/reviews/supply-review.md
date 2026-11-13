# Review of the clean-rank and coset-population tradeoff

2026-11-13. Independent machine proof review of [SUPPLY](../SUPPLY.md). No circuit or configuration search was run.

## Even own parity

Four available values in an even residue class have distinct own projections. If all four had nonzero own projections, their first appearances and the four own triples would require eight non-entry gates, leaving fewer than three entries. Thus there is one free value and three physical values in the class. Their own fibres and the triple fibres force seven distinct first-occurrence gates, leaving exactly three entries and no other non-entry gate. The three labels are independent because their span contains the three-dimensional target free space. Any clean gate must use one of the three known even fibres, since another nonunit fibre would again exceed the gate budget.

Within any of these three fibres, each gate after its first occurrence is an entry reading an earlier node of the same fibre. The resulting labelled edges form a rooted tree. A clean gate and the given nonzero-residue value in its fibre have difference equal to the pure free residue mask. That difference is the sum of entry labels along their tree path. In two different fibres these would be disjoint nonempty sets of the three independent entry occurrences, with equal sums. This is impossible. The proof does not require the supplied four values to be simultaneously usable at any particular gate time.

## Odd own parity

A four-value odd residue class contains its unique named value and three odd non-output gates. The ten-gate budget and two-even-gate necessity give either eight odd and two even gates or seven odd and three even gates.

With two even gates, two independent clean values would use both. The fifth-value exclusion leaves the last odd helper in a different residue. A residue-zero translation has at most two matches in the four-node class. The sole pair in the additional two-node class has only one sum and contributes at most one more relation across both even values. Thus there are at most five relations, and there is no even-only relation. This cannot account for six non-entry gates.

With three even gates, all three odd helpers are in the four-node class. If every even gate is clean, all available relations are supported on these four odd nodes and the three even nodes. Their actual values span at least three dimensions because the two independent clean values have even own parity and an odd node is independent of them. Their formal relation space has dimension at most four. The latest-result pivot argument bounds the non-entry count by this dimension, again below six.

If exactly two even gates are clean, there is no even-only relation, since the third even value has nonzero residue. Each clean value has at most two odd pairs, all within the four-node class. The nonclean value has at most one pair crossing from that class to its unique possible outside named endpoint, and at most one wholly named pair. To reach six independent equations, both clean translations would have to realize two pairs each. Their two matchings cover all four odd nodes. The four corresponding formal equations sum to zero: each odd node occurs twice and each clean coordinate occurs twice. They cannot all be physical gate equations. This completes the odd case.

## Interface consequences

The stated rank-one and rank-two alternatives follow. Rank one requires four distinct nonclean labels in a single saturated coset plus one clean label. Rank two and the tradeoff leave two or three distinct nonclean labels. The four-entry branch requires two independent clean labels directly. In the five-entry branch, two nonclean labels with clean span at most one would give total rank at most three. Three nonclean labels with only rank-one clean supply would give the previously excluded dependent clean pair and three distinct even traces. Thus the remaining interfaces need two independent actual clean values. The differences of nonclean suppliers may contribute to the clean span algebraically, without being required as separate physical gates.

No argument in the proof excludes either remaining resource pattern universally or resolves the separate \((11,10)\) split.
