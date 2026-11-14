# A five-entry core with two nonclean entries cannot support a cheaper tail

2026-11-14. Structural hand proof using trace separation, unique physical difference pairs, and chronological source replay. No circuit search or enumeration. The theorem concerns the one-tail twelve-consumer case with the stated core profile.

## Statement and interface

**Theorem.** Suppose a joint two-sheet circuit has twelve consumer-bearing gates, exactly one outside the relaxed target cones, and its eleven-gate target core has five entry occurrences, exactly two of them nonclean. Then the total cost is at least 22.

Assume a total at most 21, so the original source count satisfies `G_0<=9`. Reduce zero and duplicate values and redundant exits. If reduction lowers the consumer count below twelve, the [closed smaller budgets](ELEVEN_CONSUMER_CLOSED.md) already exclude the candidate. The [saturated-tail theorem](SATURATED_TAILS.md) gives an entry span of rank five for the full consumer and rank four for its target core. Write the unique outside entry as

    v=u+h.

Every useful reader of `v` is a zero-consumer exit `v+w`; useful means that its nonzero source value was not already physically supplied. There are at least two distinct useful returns. The outside quotient-label occurrence is a coloop, so `h` lies outside the full span of the core entry labels.

The [full-diagonal supply bound](FULL_DIAGONAL_SUPPLY.md) permits at most two distinct nonzero original physical clean values. The two nonclean core labels are distinct by [saturated unique pairs](SATURATED_QUOTIENT.md); call them `n,m`. The three clean occurrences must span rank at least two, because all five occurrences span rank four. They consequently have values

    c,c,d,

with `c,d` independent. The four distinct core labels `c,d,n,m` form a basis. Since the core has quotient rank one over `D`,

    e=n+m in D,

and `e` is independent of `c,d`. The five full-circuit values `c,d,n,m,h` are independent.

## Only one four-edge fibre can obstruct affine transfer

The core has five entries and six ordinary non-entry gates. Its ordinary projection is therefore a minimum triple circuit, so each ordinary-mask fibre is one entry tree. All useful partners `w` have the same ordinary mask as `u` and belong to that same core tree.

The [five-entry trace identities](../compatibility/QUOTIENT.md) identify the unique actual-label relation with the odd-trace indicator. Here that relation is the pair of `c` occurrences. Thus those two traces are odd, while the traces at `d,n,m` are even. The two nonclean traces coincide; the `d` trace is different. The [even-wire separation theorem](TIGHT_FIBRE_WIRES.md) consequently prevents the `d` edge from sharing an ordinary-mask fibre with either `n` or `m`.

A core fibre can therefore have at most four entry edges. A four-edge fibre must use exactly `c,c,n,m`.

In such a fibre, the two `c` edges cannot be adjacent. Their two outer vertices would have the same full value, contrary to saturated collision rigidity. They also cannot be separated by just one edge. A path `c,n,c` would give a physical endpoint pair with difference `n`, different from the unique actual `n` entry pair; similarly for `c,m,c`. Both violate the saturated unique-pair theorem.

The simple path containing both `c` edges must consequently use both remaining edges. Since the tree has only four edges, the entire fibre is the path

    c - n - m - c,

up to reversal and exchange of `n,m`. Its two endpoint values differ by `e=n+m`.

Let `T` be the minimal subtree connecting `u` and all `r` distinct useful return partners, and let it have `s` edges. The [affine-tree transfer theorem](AFFINE_TREE_TRANSFER.md) bounds the number of uncredited translated values by `s-r`. If `s<=3` or `r>=3`, then `s-r<=1`, so the outside entry can be removed without increasing the total. This produces at most eleven consumer gates below total 22 and is impossible.

The only remaining possibility is therefore `s=4,r=2`. The subtree is the entire four-edge path. Its endpoints must belong to the three-element terminal set consisting of `u` and its two useful partners.

## Two core helpers replay all other returns

Complete the two groups

    P=span{c,d},       Q=span{n,m}

by retaining the helpers

    g=c+d,       e=n+m.

Each costs at most one extra source gate. They are computed when first needed, or appended after replay if unused. Every exit between two core nodes has value in `span{c,d,n,m}` and is the sum of at most one value from `P` and one from `Q`. It therefore costs at most its original source XOR once the indicated helpers are available.

This completion is causal. Every return belongs to the span of labels already read. Its expansion in the five independent values `c,d,n,m,h` is unique; a nonzero coefficient implies that the corresponding value has already been read at some occurrence. In particular a needed `g` has both `c,d` available, and a needed `e` has both `n,m` available. The repeated occurrence of `c` causes no ambiguity about its full value. Ordinary source gates and all unrelated exits are then copied or bypassed in chronological order.

## The two tail returns cost at most one further gate

Write the two distinct useful tail returns as `r_1,r_2`. Each equals `h` plus a sum of labels on the path from `u` to its partner. It can be written as

    h+P_0+Q_0,       P_0 in P,       Q_0 in Q,

and thus needs at most two XORs after the two core helpers have been supplied. Whenever such an expression is used, its nonzero group coefficients are already available by the preceding unique-support argument.

If `u` is an endpoint of the four-edge path, one partner is the opposite endpoint. That return is `h+e` and costs at most its original one XOR. The other return costs at most two, using at most one additional source gate. This reasoning does not require the endpoint return to occur first.

Otherwise both useful partners are the two endpoints. Their values differ by `e`. Produce whichever useful return occurs first with at most two XORs, spending at most one extra gate beyond its original allowance. Retain it, and produce the second as the first plus `e`, using its original one XOR.

The latter reuse does not assume that `e` was available before the first return. The unique expanded supports of the two return values differ in both the `n` and `m` coefficients. Hence both labels have been read by the time of the second exit: each occurs in at least one of the two supports. Compute `e` then if necessary, within its already counted helper allowance. Other intervening source and feedback operations are preserved inductively. Repeated tail returns are bypassed.

Thus all source values can be replayed without the consumer using at most

    G_0+2+1<=12

gates. The replay contains the four rows and the four clean values `c,d,g,e`, where `g=c+d` and `e` is independent of their plane. This contradicts the [thirteen-gate clean-triangle supplier bound](FOUR_DIAGONALS.md), proving the theorem.

## Scope

The proof closes the one-tail profile whose five-entry target core has exactly two nonclean entries. It uses the complete consumer's saturated collision theorem and the core's six-gate ordinary geometry; it does not identify the relaxed core with a standalone joint circuit. Other core profiles, six-entry target-live consumers, and larger consumer budgets require their own arguments. No unrestricted MixColumns lower-bound change is asserted.
