# Five target-live entries cannot fit a twelve-consumer circuit below total 22

2026-11-14. Structural hand proof with independent machine review. No circuit search, enumeration, or computer-driven elimination. The theorem is restricted to the target-live five-entry case.

## Statement and imported facts

**Theorem.** Suppose a joint two-sheet circuit has twelve consumer-bearing gates, all in the relaxed consumer-target cones, and exactly five entry occurrences. Then its total cost is at least 22.

Assume otherwise and write `G_0<=9` for its source gates. The [rank-four source floor](RANK_FOUR_SOURCE_FLOOR.md) and entry-deletion bound force the five actual labels to be independent, with span of rank five containing the clean diagonal `D`. The established trace classes have sizes `(3,1,1)` or `(2,2,1)`; their class sums form a basis of `D`.

The [full-diagonal supply bound](FULL_DIAGONAL_SUPPLY.md) gives at most two original physical nonzero clean source values. The [twelve-entry wire reduction](TWELVE_ENTRY_WIRES.md) gives exactly one two-root own fibre and at least one nonredundant exit between its entry components. All other exits are internal to an entry component. Here nonredundant means that the returned source value was not already physically available before that exit.

Use the [chain-fibre theorem](CHAIN_FIBRES.md): each fibre contains at most one entry chain. In the repeated fibre, the other root is isolated with clean source part, and the chain has a physical endpoint with clean source part. Crossing values therefore equal a fixed element of `D` plus successive sums from an endpoint of this one chain. With no chain they are clean. A chain uses only one trace class.

For timing, every returned value lies in the span of actual labels read before it. Since the five actual labels are independent, its expanded support is unique and contains only such earlier labels. In particular an exit cannot first supply any of the five actual labels: if it returns that label, its entry has already read it. A structural formula using a later clean endpoint will only be used after expansion into this unique earlier-label support.

We construct a source-only replay using at most `G_0+3` gates and supplying four clean diagonals consisting of a triangle and an independent direction. This contradicts the [thirteen-gate four-diagonal supplier bound](FOUR_DIAGONALS.md).

## Class sizes `(3,1,1)`

Call the size-three labels `a,b,c` and the singleton labels `e,f`. Put

    d=a+b+c.

Then `d,e,f` are a basis of `D`. The only original physical nonzero clean source values are `e,f`, by the clean-value cap. Neither can be newly supplied by an exit, by the independence observation above. Hence every clean exit is redundant. In particular an internal length-three return `d` cannot occur as a useful exit; every useful internal return costs at most one XOR of its earlier path labels.

A useful crossing exit must be nonclean, so its chain is in the size-three class. From a clean endpoint, the quotient signatures along a chain of at most three distinct class labels are

    0, q_a, q_a+q_b, 0

when all three occur, with an initial or reversed partial segment in the shorter cases. The three class-label signatures are the three distinct nonzero directions of `U/D`. Thus there are at most two nonclean positions. If both occur, they are adjacent along the chain and their crossing values differ by the single actual label on the joining entry edge. There are at most two distinct useful crossing values.

Expand a first useful crossing value as

    r=t+w,

where `t` is a sum of a subset of `a,b,c` and `w` is in `span{e,f}`. Since `r` is nonclean, `t` has size one or two. The same outside-class offset `w` applies to every crossing value in this fibre.

The offset is nonzero. If `w=0` and `t` has size one, that actual label is already physically supplied. If `t` has size two, choose those two labels as a quotient basis. The [saturated quotient theorem](SATURATED_QUOTIENT.md) says their full-value difference pairs are connected by a path using just their selected entry edges. Such a path stays in one original entry component, whereas the crossing exit has parents in different components. This is impossible.

Set `g=e+f`. If the first useful crossing value uses a two-label sum `t`, compute that pair `p=t` once when needed. If it uses a single label, choose any pair `p` of `a,b,c` and defer its computation to the end. The three additional gates are

    g=e+f,
    p=one pair of a,b,c,
    d=p+the remaining class label.

Compute `g` early only if the first crossing requires offset `e+f`; otherwise defer it. Whenever a helper is needed early, all its support labels have already been read, by the unique-support observation. The first crossing then costs at most its original one XOR, using `t` and its already supplied offset `e`, `f`, or `g`.

If the second distinct useful crossing value occurs, compute it from the first and the single entry label between their two positions. That label is available before the second exit: the later chain node has been produced by whichever of the two exits first uses it. This step costs its original one source XOR. Repeated values are bypassed. All internal exits cost at most one original XOR, and all other source gates are copied chronologically from their replayed operands.

At the end, append any deferred helpers. The source replay uses at most `G_0+3` gates and contains `e,f,e+f,d`. The first three form a clean triangle, and `d` is independent of their plane. The thirteen-gate bound contradicts `G_0+3<=12`.

## Class sizes `(2,2,1)`

Write the two size-two classes as `a,b` and `c,h`, and the singleton as `e`. Put

    d=a+b,       f=c+h.

Then `d,f,e` are a basis of `D`. Every internal exit is zero, a single earlier label, or a two-label sum, so costs at most its original one XOR.

In the repeated fibre, a chain of a size-two class has at most one nonclean position: its two label signatures agree and sum to zero, so the quotient sequence from a clean endpoint is `0,q,0`, or a partial segment. A singleton-class chain has only clean positions. Therefore there is at most one distinct nonclean crossing value.

If that value exists, exchange the two size-two classes if necessary so its chain is in `a,b`. Its unique expanded form is

    r=t + epsilon*f + zeta*e,

where `t` is either `a` or `b`. The `d` coefficient has been absorbed by exchanging `a` and `b`. A return with `epsilon=zeta=0` is an already supplied actual label. Otherwise it can be made with one XOR once `f` and `e+f` are available.

Use at most three additional gates, introduced only when needed or appended at the end:

    d=a+b,       f=c+h,       g=e+f.

After these helpers are available, every clean value in `D` is already supplied or is one XOR of available values: the remaining possibilities are `d+e`, `d+f`, and `d+g`. The sole nonclean crossing value is one XOR of `t` with `e`, `f`, or `g`. All later occurrences of it are bypassed.

This completion can be performed chronologically. If a return needs `d` or `f`, its unique expanded support contains both labels of that class, so both have already been read. A return using `g` is either `g` itself, the nonclean value with both outside offsets, or the clean value `d+e+f`; in each case its expanded support already contains `e,c,h`. A return equal to a helper may be supplied using its original gate rather than a new one; counting each helper as an extra gate is a valid upper bound. Helpers that no exit needs are appended after replay.

The replay uses at most `G_0+3` gates and contains `e,f,g,d`. Again `e,f,g` form a clean triangle and `d` is independent, contradicting the thirteen-gate source bound.

## Scope

Both trace profiles are excluded below total 22. This closes the target-live, five-entry, twelve-consumer case. It does not address six entries, the possible consumer gate outside the target cones, or larger consumer budgets. No change to the unrestricted MixColumns interval is asserted.

Independent reviews: [chain and forest structure](reviews/chain-fibres-review.md), [source replay and timing](reviews/five-entry-twelve-closure-review.md). These are machine reviews, not formal verification or human certification.
