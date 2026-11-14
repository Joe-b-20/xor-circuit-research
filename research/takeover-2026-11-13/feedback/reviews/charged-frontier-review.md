# Independent scope review of the charged frontier

2026-11-14. I independently audited [CHARGED_FRONTIER.md](../CHARGED_FRONTIER.md) against the charged-forest, trace-profile, source-parity, seeded-replay, series, and exposure-counterexample notes and their saved reviews. This is a synthesis and scope audit, not formal verification or human certification. No new research, circuit search, or enumeration was used.

**Verdict:** the synthesis matches the reviewed results and leaves the twelve-consumer problem open. Its structural decomposition is not presented as a source-cost theorem.

## Global charges and local residuals

The general charged cut equations retain target boundary terms, and their quotient-span equality is correctly exact in both directions. The numerical formulas `dim(H/D)=t-4` and `dim(U/H)=6-t` are explicitly specialized to the six-entry rank-five interface; they are not claimed for arbitrary circuits. The class-sector dimensions and the exact port-hull carriers agree with the reviewed label-map quotient argument.

The entry-graph separator consequence is also accurately limited: different trace classes meet only at a consumer vertex whose source part lies in `H`. Such a source part need not have been separately computed. The two four-vertex forest paths lie in odd cosets of the span of the two even helpers. Their common nonzero clean component charge is an aggregate identity and receives no original physical-value credit.

## Trace-profile exclusions

Triple-trace closure excludes multiplicity three or larger, so the table's remaining repetition shapes are exhaustive: two pairs for four distinct traces, one pair for five, and no repetition for six. The table describes their global and local quotient dimensions; it does not assert that every algebraic shape has a circuit realization.

The two repeated-pair exclusions described in the synthesis match their precise hypotheses. The first requires both repeated pairs to have even traces. Its two possible difficult returns are distinct additional clean physical values, and at most one can occur under the cap. The second requires the three-term actual-label relation and the separated even pair/singleton geometry. Its zero-net-cost triangle completion uses original physical labels with valid producer credits. Neither theorem is widened to every two-pair interface.

The same-even-trace chain fact is used without an unjustified clean-endpoint assumption when a helper has three ordinary readers. The source replay arguments keep actual path-label timing, rather than granting a consumer node's clean source part as a source operand.

## Source-own parity and initially free values

The odd-only obstruction is stated in source-own parity, explicitly distinguished from influence-trace parity. Its normalized physical populations and causal first production of the all-four own mask agree with the reviewed proof. Together with the earlier even-entry floor, it forces mixed own parities. Applying own parity to the target-source equations makes the odd-own indicator a trace-kernel vector. It is nonzero, cannot have weight one because no trace is zero, and cannot have weight six by the new obstruction. Thus the stated range of two through five odd-own occurrences is justified.

The unique even free direction `q` belongs to the entry span but need not be an actual entry. Free-seeded replay legitimately uses it from time zero. Choosing the first odd-own actual entry as the remaining quotient representative gives exactly the displayed companion inequality. At two physical clean values, the conclusion `G_0=9` and absence of `h+q` includes values supplied later in the original circuit, because the theorem credits advancement of their original producers. The synthesis correctly requires recomputing the physical set after a free-coordinate normalization.

## Equal-trace series restrictions

The no-zero-accumulator argument uses the tight six-gate mirror, not an unrestricted claim about all circuits. It forces adjacent equal traces into a strict series segment only in the relaxed target graph; source-exit readers are retained. Replacing the second entry by the pair-sum entry is causal and exposes the first entry outside the target cones. A physically original pair sum has a valid advancement credit, while an absent sum costs at most one additional source gate.

The three resulting restrictions are all conditional on a surviving adjacent equal-trace pair: a useful exit reader at the intermediate node, an originally absent pair sum, and `G_0=9`. They do not apply to arbitrary nonadjacent or cross-fibre equal traces. The argument invokes the already closed outside and smaller-consumer cases only at total at most 21.

## Exposure counterexample and the withdrawn inference

I checked the final addition against [TRACE_EXPOSURE_LIMIT.md](../TRACE_EXPOSURE_LIMIT.md) and its independent review. The ordinary circuit has six XORs and computes all four triples. Its transposed node with three target-reader branches has three pairwise trace-class adjacencies. Each pair sum can be exposed by a different local accumulator order, while only the chosen sum and the all-four helper coexist in any one of those mirrors. Thus the global adjacency-edge bound does not follow from the per-mirror two-helper budget.

The twelve-gate decoration has six target-live entry occurrences, rank-five actual labels, and the prescribed four diagonal target parts. It is an interface construction, not a joint circuit with a nine-gate source. The synthesis correctly withdraws the proposed all-odd, four-distinct-trace closure while retaining the desired lower bound as an open question. Its optional free-direction shape does not provide the missing source supplier.

The failure does not affect the odd-run theorem: its two local accumulation choices occur at different original vertices and can be imposed simultaneously. The other exposure-based closures used in the synthesis retain the relevant even values as marked actual traces, or use a single forbidden zero accumulator. Their proofs do not combine incompatible alternative helper choices at one vertex. The charged-forest identities and carrier statements likewise concern a fixed marked network and do not count helper values across different accumulation orders. The independent source-population and seeded-replay arguments do not use this inference at all.

## Status and remaining scope

All eight linked independent review records were present at the final audit, including the exposure-counterexample review. The synthesis includes the reviewed triple-trace and two specified pair exclusions and explicitly leaves the all-odd repeated-trace case open. The forest-path wording now correctly uses odd cosets of the helper span.

The previous six-target-live-entry reduction, exact-ten and exact-eleven minima 22, no-feedback minimum 22, block-monotone bound 85, and unrestricted MixColumns interval `75<=L<=88` remain unchanged. The final discussion properly treats a joint cost bound for forest charges and local carriers as future work. Four-, five-, and six-distinct-trace cases remain open subject to the stated exclusions, as do larger consumer budgets and the unrestricted joint minimum.
