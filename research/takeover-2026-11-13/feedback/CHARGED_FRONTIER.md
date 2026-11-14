# Global forest charges and local repeated-trace directions

**Research direction superseded:** the [general unrestricted program](../general/README.md)
is now active at the user's request. The results and open cases below remain
recorded; the local case breakdown is not the current task list.

2026-11-14, continuing reviewed commit `ed374d1`. Structural hand arguments with independent machine reviews, not formal verification or human certification. No circuit search, trace enumeration, or computer-driven elimination was used. No literature-novelty claim is made.

The main result is an exact structural decomposition of the remaining six-entry interface. Some source directions are carried by aggregate charges across the mirror forest; all others are confined to the copy tree of a repeated trace. The decomposition locates the latter directions on explicit paths or subtrees. It does not itself assign them a source computation cost.

The twelve-consumer case remains open. The previous reduction to six target-live entries, exact-ten and exact-eleven joint minima 22, no-feedback minimum 22, block-monotone MixColumns bound 85, and unrestricted interval `75<=L<=88` are unchanged.

## A charged forest, with an exact local remainder

[Charged odd forests](CHARGED_ODD_FOREST.md) extend the preceding clean-wire theorem. Independent even mirror helpers give a forest on odd value occurrences. An odd vertex carries the sum `S_v` of the actual labels at its trace ports. The full edge fluxes satisfy a vertex conservation equation with target boundary terms. Across a cut, a flux is the sum of the boundary values and port charges on one side.

Modulo the clean target space `D`, the span of all edge fluxes is **exactly** the span of the odd vertex charges. Let `H` be `D` plus that charge span. Even trace-class aggregates also belong to `H`. Every wire's source part modulo `H` consequently comes only from ports of its own trace class.

For the six-entry rank-five interface, if `t` is the number of distinct traces, the class aggregates span a space of dimension `t-1` containing `D`. Hence

    dim(H/D)=t-4,       dim(U/H)=6-t.

Moreover, `U/H` is the direct sum of one sector of dimension `m-1` for each trace class of size `m`. In its copy tree, that sector is nonzero precisely on the smallest subtree joining its trace-port leaves. A repeated pair therefore carries its residual direction on a single path. Different trace classes can meet in the entry graph only at a consumer node whose source part belongs to `H`. Such a part is not automatically a separately supplied source value.

The ordinary six-gate mirror itself has two odd-forest components. Each is a four-vertex path in an odd coset of the span of its two even helpers. Each component must carry odd trace ports, and both components' label sums equal the same nonzero clean value `delta`. This value is an aggregate identity, not an original physical-value credit.

## Large trace classes and two repeated-pair profiles are excluded

[Triple-trace closure](TRIPLE_TRACE_CLOSED.md) proves that no trace can occur three times in a candidate below 22. A triple would exhaust the two trace relations and force labels `a,b,k,c,c,d`: three independent nonclean labels share an even trace, while the other labels are two independent clean values. Same even traces in one ordinary fibre form a chain even with three ordinary readers. All difficult returns share one source helper. Appending one clean value would then supply a diagonal basis within eleven gates, contrary to A12.

Consequently only the following repetition shapes remain possible before further exclusions:

| Distinct traces `t` | Global quotient rank `dim(H/D)` | Local residual structure |
| --- | --- | --- |
| 4 | 0 | Two repeated pairs, each confined to one port-connecting path |
| 5 | 1 | One repeated pair, confined to one port-connecting path |
| 6 | 2 | No repeated-class residual direction |

Two four-trace profiles are also closed:

- [Two repeated even pairs](DOUBLE_EVEN_PAIR_CLOSED.md): their possible difficult returns are distinct clean values, so the physical clean cap permits at most one. One shared helper and one appended pair sum violate A12.
- [A triangle and a separated pair](TRIANGLE_SEPARATED_PAIR.md): in the three-term actual-label relation, completing the original triangle costs no net extra source gates. The other pair needs one helper, and even-wire separation prevents the incompatible extra singleton from sharing its fibre. The resulting supplier contains a clean basis too cheaply.

These are structural replay arguments. They do not claim that every two-pair interface is impossible.

## Source-own parity must be mixed

The new [odd-only source obstruction](ODD_ONLY_SIX_ENTRIES.md) excludes six odd-own actual labels. After the permitted free-coordinate normalization, exactly two named source inputs/rows lie in `U`. Six distinct nonclean labels then force at least four extra odd source values. With no even source value, too many first triple masks would need useful exits. With one, its own mask must be the all-four sum and it must first arrive through an exit. Preparing that return and then producing the required rows outside `U` forces five odd helpers, while the budget allows four.

Together with the earlier all-even source floor, every remaining candidate has **both source-own parities** among its actual labels. More precisely, the odd-own indicator is a nonzero trace relation and cannot have weight one, so there are between two and five odd-own entries. This parity concerns source-coordinate masks, not the parity of the influence traces.

The rank-five entry space still has its unique even free direction `q` and an odd-own entry `h`, with `U=D direct-sum span{q,h}`. The new [free-seeded replay theorem](FREE_SEEDED_REPLAY.md) permits `q` to be used from time zero even if the consumer never reads it. Choosing `h` as the first odd-own actual entry gives

    G_0 >= 7+m_D+1_{h+q in A}.

Thus, at two original nonzero physical clean values, the source count is nine and the companion `h+q` is absent from the entire original physical source set, including later values. If normalization is used, these physical counts are recomputed in that circuit.

## Adjacent equal traces need genuine feedback

[Equal-trace series](EQUAL_TRACE_SERIES.md) proves that no nonempty subset of the reader-adjoint contributions at a node can sum to zero in a tight mirror. Adjacent equal trace entries therefore form a strict series segment in the relaxed target graph. The intermediate node may still feed source exits.

Replace the two entries `u+a`, then `+b`, by one target-facing entry with label `a+b`, retaining the first gate for its exits. This exposes an outside entry, a case already closed below 22. If `a+b` was an original source value, its early computation receives a producer credit. Even without a credit it costs only one extra source gate.

It follows that any surviving adjacent equal-trace pair requires all three conditions: the intermediate has a useful source-exit reader, its pair sum is absent from the original physical source set, and `G_0=9`. This does not cover equal traces in different fibres or arbitrary nonadjacent positions.

## A failed adjacency bound and its counterexample

An attempted closure of the all-odd, four-distinct-trace profile inferred that its trace-class adjacency graph had at most two edges because a six-gate mirror has only two even helpers. The [exposure counterexample](TRACE_EXPOSURE_LIMIT.md) refutes that inference. Three branches at one original vertex can expose three different pair sums in three different accumulator orders. The available even helper values can change with the order; the three sums need not coexist in one mirror.

The specified example has a twelve-gate target-live consumer with six entries, four distinct odd traces, actual rank five, and the required four diagonal target parts. It is not a joint circuit with a nine-gate source. It invalidates the proposed local-to-global counting step, not the desired cost bound. That attempted closure is withdrawn; the all-odd repeated-trace case remains open. The valid odd-run theorem exposes its two sums at different original vertices simultaneously and is unaffected. The other closures in this phase use fixed marked even traces or a forbidden zero accumulator, so they do not use the failed inference.

## Judgment and next direction

The global/local decomposition is the most transferable advance. It turns repeated traces into physical paths carrying the directions invisible to the forest cuts. The source results then identify genuinely missing values and compulsory feedback uses on those paths. These are stronger constraints than an abstract list of feasible traces.

The next question is whether the charged forest and its local port-connecting paths admit a joint cost bound, including the timing of their source labels. The rank identities alone do not provide that bound. Four-, five-, and six-distinct-trace cases remain to be settled as specified above; larger consumer budgets and the unrestricted joint problem remain open.

## Reviews

Independent reviews cover [charged forests](reviews/charged-odd-forest-review.md), [triple-trace closure](reviews/triple-trace-review.md), [two even pairs](reviews/double-even-pair-review.md), [triangle/pair replay](reviews/triangle-separated-pair-review.md), [odd-only entries](reviews/odd-only-six-entry-review.md), [seeded replay](reviews/free-seeded-replay-review.md), [equal-trace series](reviews/equal-trace-series-review.md), and [the exposure counterexample](reviews/trace-exposure-limit-review.md). The primary agent also checked the proofs and their chronology. A [final scope review](reviews/charged-frontier-review.md) checks the synthesis and its open cases.
