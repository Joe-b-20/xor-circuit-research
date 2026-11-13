# Independent review of the three-entry exclusion and its baseline

2026-11-13. Reviewed `../THREE_ENTRIES.md` and the normalization, relation inequalities, ten-gate baseline, and parity projection in `../PROOF.md`. This is an independent hand review; no circuit search, enumeration, or machine case list was used.

**Conclusion: the three-entry exclusion is sound, and the new baseline makes the combined proof independent of the older augmented lower-bound argument. No substantive gap found.** Together with the separately reviewed four-entry exclusion and the specified twelve-gate construction, these arguments establish the claimed local minimum of twelve for supplying some independent even diagonal basis, with the lower bound valid for every prescribed basis.

## Entry parity and the residue-rank reduction

With exactly three entries, their labels must span the required rank-three even free-part space. Their span has dimension at most three, so it equals that even space and each label is even. This does not depend on the later eleven-gate parity-projection argument.

The three required independent clean values span all of `D`, and the kernel of `rho` on the relevant even-free-part space is exactly `D`. Thus `dim V=3+r` is an equality, not merely a lower bound. The physical counts `|H|=7-A` and `|O|=8+A` give the stated inequality `c+r<=4`. The eight named residues occupy all eight odd masks, so reduction modulo an `r`-dimensional even residue space forces `c>=2^(3-r)`. This excludes `r=0,1` and gives `A<=2`.

The unique nonzero relation among the eight named values is their all-eight sum. The free parts of the rows are the four cycle edges, whose only nonempty dependence uses all four; their own sum is then the sum of all four ordinary inputs. The short named-relation and pair-uniqueness properties used later follow.

## Zero and one helper

With no helper, at least three of the seven even values are clean and have no named-pair representation. The at-most-four other values each have at most one. The rank deficiency of the even values is at most two, bounding the actual even-only gates by two. The resulting total of six is below the eight needed non-entry gates.

With one helper, collective clean-pair capacity is at most one. Every doubled nonclean value expresses the helper as a sum of three distinct named values, and all such triples coincide because two different triples would give a named relation of size at most six. The two formal equations for each doubled value have the same sum. Hence `d` doubled values contribute rank at most `d+1`, yielding total odd-pair rank at most five. The even-coordinate evaluation kernel has dimension at most one, so even-only relations can add at most one further dimension. The contradiction with eight independent actual equations is valid even if the physical even values are dependent.

## Two helpers and the six-edge requirement

With two helpers, five even values have rank `3+r>=5`; consequently `r=2`, all five values are independent, exactly three are clean, and the two remaining residue vectors are independent. There are no even-only relations.

The graph-component inequality gives `c<=2`. Since its two residue cosets each already contain four named residues, both cosets must be connected. Identifying all physical nodes at a common residue maps either connected coset to a connected graph on four distinct residue vertices. Clean edges become loops; only nonclean edges can join different vertices. A connected four-vertex graph requires at least three non-loop edges, so at least three actual available nonclean pair edges are necessary in each coset. Parallel edges or multiple physical representatives of one residue do not invalidate this lower bound. Across the two disjoint cosets at least six nonclean pairs are required.

Each nonclean translation can have at most three pairs: one named pair and at most one using each helper. A helper-to-helper pair consumes both helpers and cannot coexist with another pair using either of them, so it cannot evade that bound. Reaching six requires both colors to have three pairs.

For one three-pair value `k=p+q=x+n=y+m`, the four named values are distinct. The two helpers have the unique named expansions `{p,q,n}` and `{p,q,m}`. A second three-pair value would require its named pair in both sets, whose intersection is exactly `{p,q}`. It would therefore equal `k`, contradicting distinct physical values. This proves the key impossibility without a list of circuit shapes.

## Independent ten-gate baseline and parity projection

The short baseline in `PROOF.md` is correct. Seven distinct required non-input own masks plus three entries already force ten gates. At ten, exactly three entries give even labels directly. The relation inequalities force even-value rank at least five and at most one odd helper. With no helper there are at most three named-pair gates and one even-only gate; with one helper, the five even values are independent and admit at most one collective clean pair plus four nonclean pairs. Both are strictly below seven required non-entry gates.

For an eleven-gate candidate with an odd entry label `alpha`, the linear projection of the free block onto its even subspace along `alpha` fixes all seven required values and kills that actual entry. Its nonfree operand retains the same nonzero own mask, so that gate becomes a bypassable wire. Projecting and normalizing gives at most ten gates, contradicting the independently proved baseline. Therefore the parity restriction used by the four-entry proof is justified without invoking the historical augmented theorem.

## Scope

The reviewed arguments allow arbitrary internal cancellation and mixed auxiliary values. They do not need the diagonals to lie in the row ancestor cones. Exactly three and four entries exhaust an eleven-gate candidate because the labels must span rank three and the seven required distinct own masks need first occurrences. Attainment is supplied by the independently checked twelve-gate witness for one diagonal basis; the lower bound applies to every independent even basis.

I also read `../CONSEQUENCES.md`. Its deduction of joint cost twenty-two preserves the no-consumer-block-ancestry hypothesis, and its disjoint charged-family count uses `22+13+5*10=85` only in the stated block-monotone class. Taking the already reviewed local ten/thirteen bounds and ten-gate supplier closure as premises, these deductions have no additional gap. They do not assert an unrestricted MixColumns lower bound of eighty-five.
