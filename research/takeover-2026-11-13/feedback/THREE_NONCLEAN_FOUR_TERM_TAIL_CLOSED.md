# A three-nonclean four-term target core cannot support an outside tail

2026-11-14. Structural hand proof with independent machine review. No circuit search, enumeration, or computer-driven case elimination.

## The remaining core profile

Suppose a joint circuit has at most 21 gates, twelve consumer-bearing gates, and one gate outside the relaxed consumer-target cones. The [saturated-tail theorem](SATURATED_TAILS.md) makes that gate an entry

    v=u+h,

used only by source exits, with at least two distinct useful return values. A useful return is a first supply of a nonzero source value; redundant returns may be bypassed.

Consider the five-entry target-core profile with three nonclean labels `a,b,k` and two clean labels `c,d`, whose sole actual relation is

    a+b+c+d=0.

Rename `a,b` so that `a` is read first. The four labels `a,k,c,d` are independent, and the clean diagonal has basis

    c,d,e,       e=a+k.

The outside label `h` is independent of the core entry span, by its coloop property. Write `G_0<=9` for the original source budget.

**Theorem.** This profile cannot support an outside tail below total 22.

The [five-entry interface equations](../compatibility/QUOTIENT.md) give distinct nonzero entry traces. The four traces of `a,b,c,d` are odd, and the trace `kappa` of `k` is even. The trace rank is four and its sole relation is the indicator of the nonclean labels, so

    alpha_a+alpha_b=kappa.

No other pair among the four odd traces has sum `kappa`; otherwise there would be a second trace relation.

## Only one four-edge shape needs more than the tree-transfer bound

Bypassing the five core entries leaves the six-gate ordinary minimum. Thus every own-mask fibre of the core is a single entry tree, and all tail partners lie in the entry tree containing `u`.

In the fibre containing the `k` edge, two adjacent odd entry edges expose their trace sum with that fibre's ordinary derivative. The marked `k` wire has the same derivative and carries `kappa`. By [even-wire separation](TIGHT_FIBRE_WIRES.md), the adjacent pair must therefore be exactly `a,b`. Any other adjacent odd pair would expose a different even helper with the same nonzero derivative.

Remove the `k` edge. Each of the two resulting components consists of odd entry edges. It can contain at most one edge, except that one component may contain the two adjacent edges `a,b`. The pair `a,b` cannot be used on both sides because its occurrences are unique. Consequently the whole fibre has at most four edges. If it has four, its shape is precisely a two-edge `a,b` path and a one-edge `c` or `d` path joined by the `k` edge. The bridge may attach to any vertex of either path; no more specific attachment is needed.

Any other fibre contains only distinct odd traces. The odd-run theorem makes it a tree of diameter at most two, hence a star. [Affine-tree transfer](AFFINE_TREE_TRANSFER.md) removes a tail from a star without increasing total cost, contradicting the established eleven-consumer minimum 22.

For the fibre containing `k`, let `T` be the minimal subtree containing `u` and all useful partners, and let `r` be their number. There are `r+1` requested vertices and `|E(T)|+1` vertices in total. At most `|E(T)|-r` translated values are unrequested. Thus affine-tree transfer again closes the case whenever `|E(T)|<=3` or `r>=3`.

The only remaining configuration has exactly two distinct useful partners `w_1,w_2`, and their connecting subtree with `u` is the entire four-edge fibre described above.

## Two groups supply every core return

Maintain the direct sum

    P=span{c,d}={0,c,d,t},       t=c+d=a+b,
    Q=span{a,k}={0,a,k,e},       e=a+k.

This decomposition splits every chronological core-entry prefix. The entries `c,d` are pure `P`, and `a,k` are pure `Q`. At the later entry `b=a+t`, its `Q` component `a` was read earlier by the chosen naming. If needed, its `P` component is computed as `t=a+b`; this does not require that `c,d` have already been read.

The [chronological group-replay theorem](CREDITED_REPLAY.md) therefore completes both groups using at most two extra source gates, for their only potentially missing nonzero values `t,e`. Each core-only exit costs at most its original one source XOR after these completions. The construction keeps all original source values available in order and defers unused completion values until the end.

Every tail return is `h+P_0+Q_0`. Its core difference belongs to the core-entry prefix preceding the exit, so the two components are available under this same prefix invariant. After group completion, one such return costs at most two XORs, or at most one if its core difference is an already supplied single group value.

## A cheap pair among the three requested vertices

The four-edge fibre has five vertices. Partition them into the three vertices of the `a,b` path and the two vertices of the clean one-edge path. In the first part every pair difference is one of

    a,b,t=a+b;

in the second part the pair difference is the clean edge label, either `c` or `d`. These are all original actual labels or the supplied group value `t`.

Among the three distinct requested vertices `u,w_1,w_2`, two lie in the same part. Their difference is consequently one of these cheap values.

If the cheap pair is `u,w_j`, the corresponding tail return is `h` plus that value, using at most its original one XOR. The other return costs at most two XORs, requiring at most one additional source gate overall. Their chronological order is irrelevant to this bound.

If the cheap pair is `w_1,w_2`, compute whichever of their two returns occurs first using at most two XORs. Retain it. The other return is the first XOR their cheap pair difference, so costs at most its own original one XOR. Again at most one additional source gate is needed.

The cheap difference is available in time. For a single edge label this follows because the path between the relevant endpoints lies in their two root paths. For the difference `t=a+b`, both entry labels on that two-edge path have been read by the time both endpoints have been produced, and `t` can be supplied as `a+b`. In the partner-partner case both endpoints have appeared by the second exit, independently of their order of use. Thus this shortcut does not assume early availability of `c,d` or of an uncomputed clean source part.

## The supplier contradiction

Replay all source gates in their original order. Core-only exits use the two-group replay, the two useful tail returns use at most one further helper as above, and repeated source values are retained and reused. The resulting source-only circuit preserves all source rows and costs at most

    G_0+2+1<=12.

At its end it also contains

    c,d,t=c+d,e=a+k.

The first three form a clean triangle and `e` is independent of that plane. The [four-diagonal supplier bound](FOUR_DIAGONALS.md) requires at least thirteen source gates. This contradiction closes the three-nonclean four-term core profile with an outside tail.

The argument uses a fixed four-edge geometry forced by wire derivatives and a two-part pigeonhole step. It does not enumerate circuits, assume source parts are separately available, or claim the unrestricted twelve-consumer problem is closed.

Independent review: [final tail-profile review](reviews/tail-final-review.md). This is machine review, not formal verification or human certification.
