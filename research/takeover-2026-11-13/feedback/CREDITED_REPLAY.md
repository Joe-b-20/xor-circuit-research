# Source replay charged only for missing group values

2026-11-13. General structural hand proof. No search, enumeration, or computer-driven case elimination. This strengthens balanced-basis repair by counting original physical values that can be produced early and charged to their later original gates. No claim of literature novelty is made.

## Model and statement

Partition ordinary coordinates into source coordinates and consumer coordinates `z`; all free values are supported on the source side. A source-side gate has zero `z` part, and a consumer-bearing gate has nonzero `z` part. Let `G_0` be the number of original source-side gates. Let `A` be the set of all originally available source values: ordinary source inputs, every permitted free value, and every source-side gate value, including exits. Zero is available without charge. An exit is a source gate whose two consumer-bearing operands have equal `z` parts.

List actual entry occurrences in chronological order, with source labels

    ell_1,...,ell_t,
    E_i=span{ell_1,...,ell_i},       E_0={0},       U=E_t.

Choose a direct sum decomposition `U=P+Q`, with `P intersect Q={0}`. Require that it split every entry prefix:

    E_i=(E_i intersect P)+(E_i intersect Q)       for every i.       (S)

Write `ell_i=p_i+q_i` for its unique components in `P,Q`. Equivalently, at each occurrence at least one of `p_i,q_i` belongs to the span of the preceding components on its own side. The equivalence follows by induction: each entry raises the total rank by at most one. Two new component directions would raise the sum of the projection ranks by two and violate (S); conversely, if one component is in the preceding split space, subtracting it supplies the other component within the new prefix span.

Define the number of missing group values

    B=|(P minus {0}) minus A|+|(Q minus {0}) minus A|.

**Credited replay theorem.** Under (S), every original source value and every value of `P` and `Q` can be supplied in a source-only circuit of at most

    G_0+B

gates. Original source values are available no later than the corresponding point in the chronological replay. Consequently the original full computation has a no-feedback realization using at most `G+B` gates and the same consumer entry labels.

The set `A` consists of actual physical values, not the span of those values. It is defined using the original circuit, not using synthetic values introduced during replay. Condition (S) is a condition on the entire entry order; a decomposition of the final span alone is insufficient.

## Chronological construction

Replay the original operations in order, omitting consumer-bearing gates. Process each entry occurrence as an instruction to maintain source values, without reproducing its consumer computation. After the first `i` occurrences, maintain physically every value of each projection space

    P_i=span{p_1,...,p_i},       Q_i=span{q_1,...,q_i}.

Initially both spaces are zero. An ordinary source gate has two previously supplied source operands and can be copied in one XOR, or bypassed when its value is already available.

Before an exit, the source part of every earlier consumer-bearing value lies in the span of the entries already read. This is the [causal span invariant](GENERAL_REPAIR.md). Hence the exit has one component in the currently maintained `P_i` and the other in `Q_i`. It is supplied by at most one XOR of two physically available values, covered by its original one-gate allowance.

At the next entry `ell_i`, the label itself has already been physically supplied: it is an original earlier source operand. By (S), at least one of its components is in the preceding maintained subgroup. If the other component is not yet physically available, compute it as the XOR of the label and the known component. This is a single value in `P` or `Q`; zero components need no gate. If the new component enlarges one subgroup, complete the enlarged subgroup by adding it to all previously maintained subgroup values as needed. Each added mask is computed only once and lies in `P` or `Q`. The invariant follows.

Since actual labels span `U`, their final projections span all of `P,Q`. Thus the construction supplies both entire groups by the last entry. It also preserves all original source values and their causal uses.

## Charging advances to later original gates

Call a gate synthetic if it was added to split an entry or complete a subgroup, rather than to replay an original source gate. Every synthetic result lies in `(P union Q) minus {0}`, and distinct synthetic gates have distinct values: an available value is never recomputed.

If a synthetic result belongs to `A`, it cannot be a source input or permitted free value, because those were already available. Nor can its first original source gate have been replayed earlier: that too would make the result available. Its original first source gate therefore occurs later and can be bypassed when reached. Distinct synthetic values receive distinct later original gates as credits. This remains true if the later original gate was an exit; an already supplied value needs no replay gate. Synthetic computations use only values available at their time, so the credit does not assume a future operand is accessible early.

Let `R` be the set of synthetic values. Replaying all other original source gates costs at most `G_0-|R intersect A|`, while the synthetic gates cost `|R|`. Therefore

    replay cost <= G_0+|R minus A| <= G_0+B.

Finally compute this source-only circuit before replaying all original consumer-bearing gates. The same labels are supplied and their consumer predecessors remain in order, giving the asserted full no-feedback bound.

## Relation to rank-based repair

A chronological greedy basis of the entry labels can be divided into two fixed groups. Their spans satisfy (S): each entry prefix is spanned by the basis elements selected up to that time. If the group dimensions are `p,q`, their basis vectors are original physical values, giving

    B <= (2^p-1-p)+(2^q-1-q).

Balanced dimensions recover the allowance `h(d)` in [general repair](GENERAL_REPAIR.md). The present theorem can be strictly stronger because other original physical values, including values supplied later, also reduce `B`.

The decomposition need not come from assigning the initially read labels to separate groups. For example, suppose the five labels `c,d,n,m,k` span rank four, where `c,d` are independent clean labels, `n,m,k` lie in one nonclean coset, and `n+m=t` is a nonzero member of `span{c,d}`. Rename the related pair so `n` is read first. The groups

    P=span{c,d},       Q=span{n,k}

split every entry prefix. Each label except `m` lies in one group; at `m=n+t`, its `Q` component `n` is already read, so the condition holds even if the clean component `t` has not been physically supplied. Four of the six nonzero group values are original labels. The only potentially missing ones are `c+d` and `n+k`, so `B<=2`. Early computation of `c` or `d` is recovered by the theorem's charging argument. This is the general mechanism behind [three-nonclean closure](THREE_NONCLEAN.md).

If instead the actual labels lie in the union of two planes, each prefix automatically splits. When one plane's three nonzero values are all original source values and the other plane's two basis values are original, `B<=1`. This explains the [four-nonclean pair-relation restriction](FOUR_FIVE_FRONTIER.md) without assuming that the original values arrive before the first exit.

These bounds concern a fixed supplied-value set and a decomposition compatible with its chronology. They do not assert that every useful decomposition satisfies (S), or that minimizing `B` without the prefix condition gives a valid replay bound. The [five-label timing example](FIVE_LABEL_TIMING.md) shows why eventual supply alone cannot justify an earlier completion.
