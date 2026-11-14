# An odd free direction lowers the entry rank at no source cost

2026-11-14. Structural argument by a linear retraction fixing all required outputs. No circuit search or enumeration. This is a proved reduction, not an exclusion of every rank-five interface.

## A rank-lowering retraction

Use the joint two-sheet problem, with source values written `(beta,alpha)` on ordinary coordinates `b` and free coordinates `a`. The clean diagonal is

    D={(v,v): v has even parity}.

The required source and consumer rows have even `a` parts. Let `U` span every actual entry label read by a consumer-bearing gate, so `D subset U`, and let `d=dim U`. Count all zero-consumer gates, including exits, as `G_0`.

**Theorem.** Suppose `U` contains a value `h=(beta,alpha)` with even `beta` and odd `alpha`. There is a linear transformation of the full circuit that preserves all required outputs, does not increase `G_0`, and gives actual entry rank at most `d-1`. Before optional bypasses, the transformed entry span has rank exactly `d-1` and still contains `D`.

Put `sigma=alpha+beta`, an odd mask, and define the free-coordinate map

    P(x)=x+parity(x)*sigma.

It fixes every even mask and has kernel `span{sigma}`. Apply `P` to every `a` component of the full circuit, leaving `b` and the consumer coordinates unchanged. Free inputs remain free, every XOR equation remains valid, and every required output is fixed because its `a` part is even. Keeping the original wiring therefore retains the source and consumer gate counts; bypassing free, zero, or duplicate values can only lower them.

The induced source map `T(beta',alpha')=(beta',P(alpha'))` fixes `D` and sends `h` to `(beta,beta) in D`. Moreover,

    h+(beta,beta)=(0,sigma) in U.

The one-dimensional kernel of `T` is therefore contained in `U`, giving `dim T(U)=d-1`. Every actual entry label in the unshortened transformed circuit is the image of its original label, so its entry span is exactly `T(U)`. Subsequent bypasses cannot introduce an entry label outside this space.

The hypothesis has an equivalent form: **`U` contains an odd wholly free value.** One direction follows from the displayed identity; the converse takes `beta=0`. The useful point is that this value need only be in the entry span. It need not already occur as a physical entry or source gate.

## Consequences for small source budgets

If `d<=5`, the transformed circuit has entry rank at most four. The [rank-four source floor](RANK_FOUR_SOURCE_FLOOR.md) consequently proves

    G_0>=10.

If `d<=4`, the transformed entry span is exactly `D`; [diagonal confinement](DIAGONAL_CONFINEMENT.md) gives the stronger `G_0>=12`. These conclusions hold for arbitrary consumer budgets and arbitrary feedback.

For a twelve-consumer candidate of total at most 21, the existing reductions give `G_0<=9` and `dim U=5`. Such a candidate cannot contain the parity signature `(even own, odd free)` anywhere in `U`. Since the signature map

    (beta,alpha) -> (parity(beta),parity(alpha))

is linear, its image on `U` is one of

    {0},       span{(1,0)},       span{(1,1)}.

Equivalently, either every entry-space value has even free part, or its free parity always equals its own parity. In particular, no odd wholly free value lies in `U`, and no such value can be an actual entry.

This restriction concerns the entry space and therefore also all exits, whose values lie in it by chronological span. It does **not** assert that all original source intermediates have even free parts or belong to `U`. A global free-coordinate projection can change those other intermediates, so physical supply claims about their original values cannot simply be transferred back from the projected circuit.

The theorem extends the earlier rank-one parity projection by using the new rank-four source floor after projection. Rank-five interfaces with the remaining parity images are still open.
