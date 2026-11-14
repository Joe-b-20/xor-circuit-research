# Physical clean values strengthen rank-four source supply

2026-11-14. Structural hand proof using a chronological split and credits for original physical values. No circuit search, enumeration, or computer-driven elimination. The result permits arbitrary feedback and has no consumer-budget hypothesis.

Use the joint 0/1-sheet model with ordinary source coordinates `b`, free coordinates `a`, ordinary consumer coordinates `z`, and required source rows `U_i=E_i(b)+s_i(a)`. Let

    D={v(b)+v(a): v is even}

be the rank-three clean diagonal. Let `U` be the span of the actual source labels read by consumer-bearing gates, and suppose `dim U=4` and `D subset U`. Let `A` contain all original physical source values: ordinary source inputs, permitted free values, and every zero-`z` gate value, including exits. Write `G_0` for the number of zero-`z` gates.

**Theorem.** If `span(A intersect D)` has dimension at least two, then `G_0>=11`. If that span has dimension one, then `G_0>=10`.

The clean values in this statement need not be actual entry labels. They may be source outputs or other physical intermediates. A virtual clean direction in the span of nonclean values does not qualify.

## Choosing a plane compatible with the entry order

If the physical clean span has dimension three, the earlier [rank-four physical-supply theorem](RANK_FOUR_SUPPLY.md) already gives `G_0>=11`. Suppose it has dimension one or two. Choose a plane `W subset D` containing that span. In the dimension-two case this is the physical clean span itself. Every actual clean entry label lies in `W`.

Choose `n` to be the first actual nonclean label read by the consumer. Such a label exists because the full entry space has dimension four. Choose `k` to be the first actual label outside `W+<n>`. Since all actual clean labels belong to `W`, this `k` is nonclean. Their common nonzero quotient class modulo `D` gives

    e=n+k in D minus W.

Consequently

    U=W direct-sum Q,       Q=span{n,k}.

The only nonzero clean value of `Q` is `e`, so the two nonclean `W`-cosets in `U` are `n+W` and `k+W`. Every actual nonclean label belongs to one of these two cosets. Before `n` there are no nonclean entries. Before `k` every nonclean entry belongs to `n+W`. At the first occurrence of either representative, it is itself a pure `Q` value. Thereafter its `Q` component is an already-read representative. Clean entries are pure `W` values.

Thus every entry-prefix span splits between `W` and `Q`: at every new entry, either one component is zero or its `Q` component belongs to the preceding entry span. This is the chronological condition of [credited replay](CREDITED_REPLAY.md). It does not require an originally named clean basis to be available at the start. Differences of earlier nonclean entries can supply missing `W` components, with any early original physical value credited to its later producer.

## Counting only missing group values

The group `Q` has three nonzero values `n,k,e`, with `n,k` original physical values. It therefore contributes at most one missing value to the credited replay budget.

If the physical clean span has dimension two, `W` contains at least two original independent values, so its three nonzero values contribute at most one missing value. The source-only replay costs at most `G_0+2`. It supplies every original source value and every value of both groups, including the full clean triangle `W minus {0}` and the independent clean value `e`. The [four-diagonal supplier bound](FOUR_DIAGONALS.md) requires thirteen gates, yielding `G_0+2>=13` and hence `G_0>=11`.

If the physical clean span has dimension one, `W` contains its original nonzero value, so at most two of its nonzero values are missing. The replay now costs at most `G_0+3` and supplies the same triangle plus independent fourth value. Therefore `G_0+3>=13`, giving `G_0>=10`.

This strengthens the preceding rank-four statement from three to two physical clean directions, and supplies a separate bound for one physical clean direction. It uses the original physical value set in its accounting and does not convert arbitrary span membership into a gate credit.

## Scope

In particular, any putative joint circuit with at most nine source-side gates and rank-four entry span can have no nonzero original clean physical value. The zero-clean case needs a separate argument. This note does not constrain rank-five entry spaces or prove an unrestricted joint minimum.
