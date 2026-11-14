# A four-entry target core cannot support a twelve-consumer tail

2026-11-14. Structural hand proof by the marked-mirror forest, two-group chronological replay, and the four-diagonal supplier bound. No circuit search, configuration enumeration, or computer-driven elimination.

**Theorem.** A joint two-sheet circuit with twelve consumer-bearing gates, a unique gate outside the relaxed consumer target cones, and four entry occurrences inside those cones has total cost at least 22.

This closes the four-entry outside-tail case. It does not close every twelve-consumer circuit.

## The core and its repeated fibre

Suppose the total is at most 21, so the source gate count is `G_0<=9`. The [saturated-tail theorem](SATURATED_TAILS.md) makes the outside gate an entry

    v=u+h,

with at least two distinct nonredundant source returns `v+w`. Its target core has eleven gates, entry rank four, and quotient rank one over the clean diagonal `D`. The four actual core labels are an independent basis

    c,d,n,m,

where `c,d` are clean, `n,m` are nonclean, and

    e=n+m,       c,d,e independent in D.

The outside label is independent of the core entry span, so `c,d,n,m,h` are independent. These statements use the [four-entry interface theorem](../compatibility/QUOTIENT.md) and the outside label's coloop property.

By [TAIL_CORE_REDUCTIONS](TAIL_CORE_REDUCTIONS.md), a surviving tail must use a return between two different entry components of its ordinary-mask fibre. That is the unique fibre with two ordinary roots; all other fibres have one root.

The chain and clean-endpoint argument of [CHAIN_FIBRES](CHAIN_FIBRES.md) applies to this core too. Its mirror has the same seven gates: four odd triples and three independent even helpers, now carrying trace classes of sizes `(1,1,2)`, namely `{c}`, `{d}`, and `{n,m}`. The general odd-forest argument makes the odd-wire source parts clean. The three helper reader sets again have sizes `(2,1,1)`, so each derivative class occupies one chain, with a clean endpoint. The only possibly nonclean non-entry root is the two-reader merge; if it belongs to the repeated fibre, it is the root of that fibre's chain. Consequently the repeated fibre consists of one chain and a clean isolated root, or two clean isolated roots with no chain.

For a chain, choose a clean endpoint as reference. Its difference from the isolated root is a value `delta in D`. A return between the chain and the isolated root has the form `delta` plus a chain interval, all of whose labels belong to one trace class. This is a full-value identity; no early availability of the reference endpoint is assumed.

## A chronological two-group supply

Maintain the two groups

    P=span{c,d}={0,c,d,g},       g=c+d,
    Q=span{n,m}={0,n,m,e},       e=n+m.

Their sum is direct and equals the core entry span. Complete each group when needed using its one pair sum, for at most two extra source gates in total. If a pair sum has not been needed during replay, append it at the end.

Process the original gates in order, omitting consumer-bearing gates and retaining their entry times for the availability invariant. An ordinary source gate can be copied from its already replayed source operands. Any exit between two core values belongs to `P direct-sum Q`; its unique basis expansion uses only actual labels already read before that exit. Its `P` component and `Q` component can therefore be supplied in time, and the exit itself uses at most its original one XOR after the group completions.

The same independence controls tail returns. Every such value belongs to `h+(P direct-sum Q)`. Any nonzero `P` or `Q` component appearing in its expansion uses only basis labels read by that exit. Thus a structural formula involving a later clean endpoint can still be implemented from its actual expanded support. The remaining task is to supply all tail returns with at most one further extra source gate.

## A chain in the nonclean class

Suppose the repeated fibre's chain uses labels from `{n,m}`. All differences within the chain lie in `Q`. Its clean reference difference has the form

    delta=P_0+gamma*e,       P_0 in P,       gamma in {0,1}.

If `u` is on the chain, every tail return to another chain node is `h+Q_j` for some `Q_j in Q`, so uses at most its original one source XOR. There is at most one return to the isolated root. It has the form `h+P_0+Q_0`; compute `h+P_0` if necessary for at most one extra gate, then add `Q_0` using the exit allowance.

If `u` is the isolated root, every tail return has the form

    h+P_0+Q_j,

with the same `P_0` and possibly different `Q_j`. Retain the single helper `h+P_0`; each return then uses at most its original one XOR. If `P_0=0`, the helper is just the already supplied `h`.

The `P_0` used by a crossing return is its actual `P` component. Independence therefore guarantees its basis operands are available when the helper is first needed. The corresponding `Q_j` has the same timing guarantee. No more than one extra tail helper is required.

## A chain in a clean singleton class

Suppose the chain is the one edge labelled `c`; the `d` case is identical with the names interchanged. The repeated fibre has exactly three nodes: the two chain endpoints and the isolated root. At least two distinct useful tail partners are required, so the partners are precisely the two nodes other than `u`.

If `u` is on the chain, the internal return is `h+c`, costing at most its original one XOR. The sole crossing return is `h+delta'` for some `delta' in D`. Write

    delta'=P_0+gamma*e.

After the group completions, this return needs at most two XORs, one more than its original allowance. Its expanded support supplies the required operands in time.

If `u` is isolated, the two returns differ by `c`. Compute the chronologically first return as `h+P_0+gamma*e`, again using at most one extra XOR beyond its original allowance. Retain that result. Compute the second return by adding `c`, using only its own exit allowance.

The linking label `c` is available by the second exit. By that time both chain endpoints have appeared as exit operands, and the entry joining them has therefore already read `c`. This remains true if the later-produced chain endpoint was used by the earlier exit. Thus this reuse does not assume that the clean reference endpoint existed at the first return.

If the repeated fibre has no chain, it contains only two core nodes. There is at most one distinct partner other than `u`, contrary to the required two useful returns. No additional case remains.

## The supplier contradiction

The replay preserves every original source value. Completing `P,Q` costs at most two extra gates, and the preceding tail argument costs at most one more. The resulting source-only circuit therefore has at most

    G_0+3<=12

gates. It supplies all four source rows and the four distinct diagonal values

    c,d,c+d,e,

where the first three form a clean triangle and `e` is independent of that triangle. The [four-diagonal supplier theorem](FOUR_DIAGONALS.md) requires at least thirteen gates. This contradiction proves the theorem.

The proof counts only the two specified group sums and one translated tail helper. Clean source parts of consumer nodes are used to identify the algebraic form of a return, not as separately available source operands. Their timing is supplied instead by the independent actual-label expansion.
