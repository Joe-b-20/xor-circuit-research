# Independent review: six odd-own entries

2026-11-14. Independent machine review of [ODD_ONLY_SIX_ENTRIES.md](../ODD_ONLY_SIX_ENTRIES.md). This is an argument audit, not formal verification or human certification. No search or enumeration was used.

**Verdict:** the source-population argument passes, including the separate zero-even-value branch, the causal first production of the all-four mask, and the final disjoint helper counts. The conclusion concerns source-own parity, not trace parity.

The free-coordinate projection is injective on the rank-five entry span and preserves ordinary source and consumer masks. Thus the six odd-own entries stay nonzero and distinct. Normalizing source values does not delete these consumer entry occurrences. Physical counts are correctly recomputed in the projected circuit. Its residue plane contains two odd residues, while the eight named values have all eight odd residues exactly once, so exactly two named values lie in `U`.

Every odd-own entry is nonclean. Saturated unique-pair rigidity prevents an exit from first supplying any of the six actual labels. The other four labels beyond the two possible named values must be odd helpers, giving `A_o>=4` and `|H|<=1` under the nine-gate source budget.

If `H` is empty, at most seven odd physical source values lie in `U`, and six are the protected actual labels. Hence there is at most one value available for a useful odd exit. Ordinary source operations without a nonfree even value can only preserve an odd operand's own mask. Each of the four first triple-own occurrences must therefore be a new odd exit, a contradiction. This closes the potential `A_o=5,H=0` population before equality is assumed.

With `H={w}`, equality forces exactly four odd helpers, all in `U`, and exactly six odd physical values in `U`, precisely the six actual labels. No odd exit can introduce a new value. Induction therefore confines odd own masks to coordinate units and their translates by `p=beta(w)`. A pair mask yields only two triples; producing all four forces `p=J`.

Before the first supply of `w`, every odd own mask is a unit. An ordinary XOR of two such values has own mask zero or a pair, and no free addition can introduce `J`. Thus `w` is first supplied by an exit and belongs to `U`. Its earlier actual unit-own entry labels must span `J`, requiring all four unit directions. Only the `i` named coordinate inputs in `U` can cover those directions without odd helpers, so at least `4-i` unit-own helpers precede `w`.

There are `2+i` required rows outside `U`, and none can be an exit. A direct production by adding `w` can use neither a helper, since both summands would belong to `U`, nor another row, since a triple plus `J` is a unit. It must be `w+b_j`. Named-pair uniqueness permits this for at most one outside row. Every other outside row needs an earlier odd helper with its own triple mask before a free addition. Distinct required triple masks require distinct such helpers, at least `1+i` in total.

These triple-own helpers are different physical values from the earlier unit-own helpers. The sum of the lower bounds is five, contradicting the four-helper budget. All count and causality steps are therefore justified. The proof neither transfers old physical credits through the projection nor imposes an unstated restriction on nominal free values.

The added parity-count corollary also passes. Applying ordinary source parity to each target-source equation gives `Zp=0` for the indicator `p` of odd-own entries. The even-entry source floor makes `p` nonzero, while the theorem reviewed above excludes weight six. A weight-one kernel vector would be a zero trace column, impossible because the tight six-gate mirror contains no zero signal. Hence the number of odd-own entry occurrences is between two and five, independently of the trace vectors' own parities.
