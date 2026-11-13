# Independent review: four-entry augmented supplier

Hand review of `../FOUR_ENTRIES.md`, its entry-parity normalization, and the referenced formal relation-rank and two-helper matching arguments. No SAT, exhaustive enumeration, exact-gate search, or computer-driven case elimination was used. This is not formal verification.

## Verdict

The proof correctly excludes a normalized eleven-gate augmented supplier with exactly four actual free-entry gates, for arbitrary independent even diagonal masks and with whole-block cancellation permitted. It depends on the earlier eleven-gate even-entry-label restriction and the stated named-node relation and formal relation-rank lemmas. It does not by itself exclude the separate three-entry branch.

## Normalization, parity, and physical counts

Under the established entry-deletion bound, an eleven-gate augmented candidate can use only even free labels. Remove free-only, zero, duplicate and dead paid values without increasing cost; each remaining gate has nonzero own part and each gate with a free operand is an entry. An entry repeats its earlier nonfree operand's own projection.

The four target triples and the three distinct nonzero even own masks of the independent diagonal values require seven first occurrences beyond the input units. Four entry gates are distinct from these first occurrences, so the eleven-gate budget forces equality. There are exactly three distinct nonzero even own masks and they are independent. Any physical even gate has one of these masks, and no three such masks, allowing repetition, can sum to zero. Thus there is no non-entry equation involving three physical even values. Exactly three physical even values are clean: the required diagonal values, one for each even own mask; a further clean value with the same own mask would be a duplicate. If `A` is the number of odd non-output gates, then `|H|=7-A`, `|O|=8+A`, and exactly seven physical non-entry equations must be independent by latest-result pivots.

The four ordinary units and four row targets have the eight different odd `rho=beta+alpha` residues. Their only nonzero relation is their all-eight sum, so distinct named pairs have different nonzero sums and any two three-element named sets with equal sums are identical. These facts support the matching bounds below; they do not require entry labels or physical even values to be independent.

## Helper populations

Since the three required clean diagonals span `D`, the kernel of `rho` on `V=span H` is exactly `D`. Writing `r=dim rho(V)`, the formal relation-rank inequality gives `7<=12-c-r`, where `c` is the number of components of the available odd-pair graph. If `r=0`, the eight named residues are separated, so `c>=8`, impossible. Also `3+r<=7-A`, giving `A<=3`.

For `A=0`, four nonclean values have at most one wholly named pair each and the clean values have none, so at most four non-entry relations exist.

For `A=1`, at most one clean pair uses the helper, because it must pair with the unique named node of the same residue. Each of the three nonclean values has at most one wholly named and one helper-to-named pair. Whenever `j` nonclean values have both representations, each pair of their formal equations sums to the same nonzero formal vector `[helper]+[n_1]+[n_2]+[n_3]`: the three-element named set is the same by the absence of short named relations. Those `2j` equations therefore have rank at most `j+1`. Adding the remaining `3-j` single nonclean equations and at most one clean equation yields rank at most five, or at most four when `j=0`. This argument does not assume independent nonclean even values.

For `A=2`, the three independent clean diagonal values have at most two odd-pair representations collectively. If the two helpers have different residues, each can match only its unique same-residue named node. If they have the same residue, three available pairs among the two helpers and the named node would have three distinct sums adding to zero, impossible for the independent clean values. Each of the two nonclean values has at most three pairs. If one has three, named-pair uniqueness and the short-relation argument bound the other by two; when it has two, the matching lemma gives an alternating four-cycle of physical relations whose formal sum is zero. Therefore the available relation rank is at most six even in the saturated count of seven. Full independence of all five even values is not assumed.

For `A=3`, the even values are the three independent clean diagonals and one nonclean value `k`, so the four full even values are independent. Every odd-pair edge preserves a residue or toggles `rho(k)`, producing at least four residue-pair components, each with two named nodes. The relation-rank bound forces exactly four, so each class must be connected and must contain a `k` edge. Translation by nonzero `k` is a matching: there is at most one wholly named `k` pair and at most one pair per helper, hence exactly four pairs, one in each class. The three helper classes each need a clean edge to attach the remaining named node. Their four named-pair sums are `k,k+h_i,k+h_j,k+h_m`; named-pair uniqueness forces the three clean colours to be distinct. Summing the pairs sums all eight named nodes to zero and yields `h_1+h_2+h_3=0`, contradicting their independence.

These symbolic population bounds exhaust the possibilities allowed by `A<=3`; no candidate circuits or finite gate families are enumerated. The conclusion is exactly the stated four-entry exclusion.
