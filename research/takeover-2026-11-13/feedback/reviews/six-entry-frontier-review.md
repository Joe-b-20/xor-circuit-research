# Independent scope review of the six-entry frontier

2026-11-14. I independently audited [SIX_ENTRY_FRONTIER.md](../SIX_ENTRY_FRONTIER.md) against its structural notes, source bounds, complete tail coverage, and final review records. This is a scope and synthesis audit, not formal verification or human certification. No new research, circuit search, or enumeration was used.

**Verdict:** the reduction to six target-live entries is supported, and no mathematical overclaim or missing tail profile was found. The twelve-consumer minimum itself remains open.

## General statements and specialized applications

Affine-tree transfer is accurately stated as a partial removal of one outside entry, preserving other feedback. Its allowance counts missing translated physical values; it does not charge virtual span membership or claim that all exits disappear simultaneously. The triangle and cheap-return-difference refinements are used only where their actual labels and timing support them.

The general odd-forest statement is distinguished from the specialized clean-endpoint theorem. Independent computed even values give a forest, and source ports confined to even-valued wires give the clean-source cut identity. The stronger chain and endpoint description additionally uses the seven-gate mirror's three independent helpers and reader counts `(2,1,1)`. The synthesis explicitly warns that a clean source part of a consumer value is not a separately supplied source value, nor an early source operand.

The five-entry target-live closure is correctly limited to its independent-label, seven-mirror setting. Its two trace-class profiles yield source replay within `G_0+3`, physically supplying a clean triangle and an independent direction. The contradiction is to the established thirteen-gate supplier bound; it does not assume any new exact optimum.

## Outside-entry coverage is complete

The global saturated-tail theorem leaves at most one outside entry, with an eleven-gate relaxed target core of entry rank four and quotient rank one. The core has four or five entries. The four-entry case is covered by the separately reviewed chain extension and the four-entry tail closure.

For five core entries, zero nonclean occurrences contradict rank four. One nonclean occurrence would require three independent physical clean labels, violating the cap of two. Two nonclean occurrences leave three clean occurrences of rank at least two; the same cap forces exactly the repeated-clean profile `c,c,d,n,m`, covered by the two-nonclean tail closure.

With three nonclean entries, distinct traces and their parity relation force exactly two odd nonclean traces and one or both odd clean traces. Thus the unique actual-label relation has exactly three or four terms, the two profiles listed. With four nonclean entries, the permitted relation lengths are exactly three, four, or five. With five nonclean entries, the relation has four terms and gives the affine-plane profile. The triangle, affine-plane, all-distinct-odd, and final four-term arguments cover all of these possibilities.

The final [tail review](tail-final-review.md) is present and explicitly passes both the two-nonclean and three-nonclean four-term closures. Together with the prior core-reduction and four-entry reviews, the entire coverage table is reviewed. This is a classification by rank, parity, and label relations, not an exhaustive search over circuits. No relaxed core is mistaken for a complete smaller-consumer joint circuit without the requisite feedback repair.

Once outside gates are excluded, the target-live twelve-gate entry count is five or six. The new five-entry closure therefore leaves exactly six, as the opening reduction asserts.

## Source restrictions and physical-value accounting

The even-entry floor applies at any consumer budget and forces an odd-own actual entry in a small-source candidate. Combined with parity rank retraction, rank five gives exactly one nonzero wholly free direction `q`, which is even, and `U=D direct-sum span{q,h}` for any odd-own actual entry `h`. The three coset parities are stated correctly, and the free direction is not asserted to be an actual read label.

The residue-plane normalization is an existence reduction for a hypothetical circuit. It is not an equality of original and transformed physical source-value sets. Physical supply counts and replay credits must be recomputed in the transformed circuit; the source-floor proof and its review contain this qualification. The synthesis's free-section replay formula likewise counts original physical section values and correctly separates its general theorem from the now superseded even-own application.

## Remaining scope and forward direction

The six-entry trace identities now apply to every remaining twelve-consumer candidate, because target liveness has been proved globally for that budget. The synthesis retains possible repeated traces and does not infer that all returns lie in one selected complement. It does not claim to close the six-entry case, larger consumer budgets, or the unrestricted joint problem.

The proposed two-component forest direction is mathematically grounded: the six-gate ordinary mirror has four input vertices and two distinct nonzero even helper values, hence two independent even helpers; the general forest count is `4-2=2`. The extra trace ports can occur on odd wires, so the clean-boundary hypothesis fails without additional accounting. The synthesis presents analysis of those additional terms as a future research direction, not an established clean-endpoint or cost theorem.

The exact-ten, exact-eleven, and no-feedback joint minima remain 22. The block-monotone bound remains 85 and the unrestricted MixColumns interval remains `75<=L<=88`. The review-status language is supported by the saved independent reviews, with no formal-verification, human-certification, or literature-novelty claim.
