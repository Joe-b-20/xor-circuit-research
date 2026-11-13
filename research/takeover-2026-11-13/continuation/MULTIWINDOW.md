# One hidden computation can profit across arbitrarily many windows

2026-11-13. Hand proofs and explicit symbolic constructions only; no search, enumeration, exact circuit optimization, or computer-driven case elimination. This is a general limitation theorem. It changes no MixColumns bound and does not suggest that 88 is optimal.

Machine review: [multiwindow review](reviews/multiwindow-review.md). This is not formal
verification or human certification. [SPARSE.md](SPARSE.md) strengthens the example to
weights 5/7 and boundary relation distance six while preserving block/window bounds.

## Result

The single-window hidden-work bounds cannot be added across different windows, even when all of the following hold simultaneously:

* Every selected visible event has a different maximal-clique output window.
* The selected event values are linearly independent.
* Every window has at most three blocks, and the maximum block dimension is a fixed constant.
* Each output family has its own distinct designated block, and there is no reciprocal own-block incidence: no two families contain one another's own blocks.
* The circuit has exactly one hidden gate and no hidden events.
* Cancellation yields an advantage over every event-free circuit that grows linearly with the number of selected windows.

Thus neither a uniform positive hidden-gate credit per selected event nor a bounded local-partner capacity follows from these hypotheses. The source of the failure is one shared value carrying the difference of two common input coordinates. It can change the common coordinate in many separately retained prefix computations.

## Construction

Fix integers `r>=1` and `m>=2`. The block dimension `m` may be fixed, for example `m=3`, while `r` grows.

Use the following input blocks:

    X = {x},
    Y = {y},
    Z_i = {z_i1,...,z_im},           i=1,...,r,
    W_ik = {w_ik},                 i=1,...,r, k=1,...,m.

All displayed coordinates are independent. The required non-input outputs are

    A_ik = y + z_i1 + ... + z_ik + w_ik,
    T_i  = x + z_i1 + ... + z_im.

Optionally include the input outputs `x` and `y`; they require no gates and provide own-block families for the two common input blocks.

Compute

    a     = x + y,
    p_i1  = y + z_i1,
    p_ik  = p_i,k-1 + z_ik             (k=2,...,m),
    A_ik  = p_ik + w_ik,
    T_i   = a + p_im.

This is an explicit acyclic circuit with

    G = 1 + rm + rm + r = 2rm+r+1

gates. The only event gates are the `r` gates `T_i`, each cancelling block `Y`. Every `p_ik` has an event-free continuation to its own designated output `A_ik`, and every `A_ik` is itself a non-event output. All these gates are retained. The gate `a` is non-event, and every path from it to an output passes through some event `T_i`. Hence the hidden sets are

    Q={a},   E\F=empty,   F={T_1,...,T_r}.

In particular, the hidden-work count is exactly one. Every gate value is nonzero; the prefix, auxiliary-output, event-output, and shared values are distinct by their input-coordinate supports, so the circuit is reduced and fully live.

## Window geometry and independence

The output windows are

    V_i  = {X,Z_i},
    U_ik = {Y,Z_i,W_ik}.

Assign own block `Z_i` to the one-output family `T_i`, and own block `W_ik` to the one-output family `A_ik`. If the input outputs `x,y` are included, assign them own blocks `X,Y` and singleton windows.

There is no reciprocal own-block incidence:

* `U_ik` contains the own block `Z_i` of `V_i`, but `V_i` does not contain `W_ik`.
* Distinct `U` windows contain none of one another's private own blocks.
* Distinct `V` windows contain none of one another's own blocks.
* The singleton families contain no other family's own block.

The co-occurrence graph has edges `X--Z_i`, and, for each `(i,k)`, the three edges of the triangle on `Y,Z_i,W_ik`. There is no edge `X--Y` and no edge `X--W_ik`. Consequently each selected-event window `V_i={X,Z_i}` is a maximal clique. Each `U_ik` is also a maximal clique. All windows have size at most three, and all blocks have dimension at most `m`.

The gate `a=x+y` is nonlocal: no output window contains both `X` and `Y`. Its local partners `p_im` are supported on `{Y,Z_i}`, a subset of `U_im`. It therefore has `r` local-partner selected events, one in each of the distinct windows `V_i`.

The selected values `T_i` are independent. In a relation among them, the coefficient of `z_i1` is the coefficient of `T_i`, so every coefficient must vanish.

The nonlocal operand graph consists of the single vertex `a`, with no nonlocal/nonlocal edge. This is compatible with global event-value independence: a forest controls the number of edges between hidden vertices but places no limit on how many different local partners can attach to a vertex.

## Exact event-free complexity

For the specified block partition, the event-free minimum is

    L_eventfree = 3rm.

Here an event-free circuit may cancel individual coordinates inside a surviving block. Only disappearance of an entire nonzero block is forbidden, as in the preceding research.

### First remove the private coordinates

In an event-free circuit, block support grows along every edge. The only output containing block `W_ik` is `A_ik`. Thus no live gate containing `W_ik` can contain another private block `W_jl`: no output contains both.

For each private coordinate `w_ik`, its first gate of combination with any other value exists, since `A_ik` is not that input. These `rm` gates are distinct. At such a gate, one operand is the singleton input `w_ik` and the other has no private-coordinate content. To see the latter claim, any other private coordinate would persist to an output containing both, which is impossible. Gates carrying only the singleton block `W_ik` have no nonzero value other than the input and may be bypassed as duplicates.

Set all private coordinates to zero. Each of those `rm` first-combination gates becomes a wire and can be removed. Zeroing complete blocks preserves event-freeness: an equality of two nonzero components on a surviving block would have been the same equality before zeroing. Bypassing wires and reusing duplicates preserves operand values and event-freeness.

The remaining event-free circuit has at most `G'-rm` gates, where `G'` was the original event-free size, and computes

    P_ik = y + z_i1 + ... + z_ik,
    T_i  = x + z_i1 + ... + z_im.

### The reduced output problem costs exactly `2rm`

The `rm` distinct non-input output values `P_ik` each contain block `Y`, so they require `rm` distinct gates.

Every ancestor of `T_i` in an event-free circuit is supported on `{X,Z_i}` and therefore avoids `Y`. Computing `T_i`, which has weight `m+1`, requires at least `m` gates in its ancestor cone. This is the usual binary-DAG source count: a computation reaching `m+1` different input coordinates needs at least `m` binary gates, even when cancellation and fan-out are allowed.

The ancestor cones of distinct `T_i,T_j` share no gate in a reduced event-free circuit. A common gate would have support inside the intersection `{X,Z_i} intersect {X,Z_j}={X}`, whose only nonzero value is the coordinate input `x`; such a gate is a removable duplicate. These cones also contain none of the `P_ik` gates, since they avoid `Y`. Thus every event-free circuit for the reduced problem needs at least

    rm + sum_i m = 2rm

gates. Reducing duplicates first loses no event-free property.

This lower bound is attained. For each `i`, compute clean prefixes

    q_ik = z_i1 + ... + z_ik             (k=2,...,m)

with `m-1` gates, take `q_i1=z_i1`, compute each `P_ik=y+q_ik` with one gate (`m` gates), and compute `T_i=x+q_im` with one gate. The total is `2m` per group.

Therefore the original private-coordinate output problem has event-free size at least `2rm+rm=3rm`. Adding the `rm` gates `A_ik=P_ik+w_ik` to the displayed `2rm` construction attains `3rm`, proving equality.

## Cancellation advantage and its scope

The difference between the exact event-free minimum and the size of the displayed one-hidden-gate circuit is

    3rm - (2rm+r+1) = r(m-1)-1.

It is strictly positive when `r(m-1)>1`; the sole equality case in the stated parameter range is `r=1,m=2`.

For example, with the fixed block dimension `m=3`, this difference is `2r-1`, while the hidden-work count remains exactly one and the maximum window size remains three.

We do not claim that the displayed cancellation-using circuit is optimal. What is proved is

    L <= 2rm+r+1,
    L_eventfree = 3rm,
    L_eventfree - L >= r(m-1)-1.

The one-hidden-gate count is minimal for this selected-event profile: a visible event on a maximal-clique window has a nonlocal operand, by the earlier window-credit lemma, so zero nonlocal gates are impossible.

The private singleton outputs are not a cosmetic modification. They allow the prefix computations to remain retained while giving every output family its own distinct block and preserving the no-reciprocal-incidence property. The stripping argument above proves their precise event-free cost.

## Exact affine-completion calculation

The companion affine-completion theorem can account for the shared operand without adding one hidden gate per window. Write

    S_i = z_i1 + ... + z_im,
    K = span{T_i : i=1,...,r},
    C = a+K,                         a=x+y.

The `T_i` are independent, so `dim K=r`. A vector of the affine coset has the form

    a + sum_{i in I} T_i
      = (1+|I| mod 2)x + y + sum_{i in I} S_i.

Every such vector contains `y`. If it is local, it cannot contain `x`, since no output window contains both `X` and `Y`. Moreover a window containing `Y` contains at most one `Z_i` block. The independence and disjoint supports of the `S_i` therefore force `I` to be a singleton. Conversely every singleton gives the local prefix `p_im=y+S_i`.

Thus the geometrically possible local completions are exactly

    E = C intersect (union over output windows W of the subspace V_W)
      = {p_1m,...,p_rm}.

Choose the affine anchor `ell_0=p_1m`. The span of completion differences is

    Delta = span{p_im+p_1m : i=2,...,r}
          = span{S_i+S_1 : i=2,...,r}.

These `r-1` vectors are independent and belong to `K`, since `S_i+S_1=T_i+T_1`. Hence

    dim K - dim Delta = r-(r-1)=1.

The affine-completion hidden-work bound is exactly attained by the one nonlocal operand gate. The calculation uses one symbolic characterization of the coset; it does not enumerate its `2^r` elements or search over local completions.

## What a MixColumns extension must add

The obstruction does not have the full MixColumns row system. Each selected window has only one required event output; MixColumns has four structured rows per sheet, own-block triple sums, and neighbour-pair components. It also allows a growing number of windows through the common blocks `X` and `Y`, whereas MixColumns has a fixed eight-window incidence structure.

A successful multiwindow extension therefore must use more than maximal output windows, bounded window size, bounded block dimension, independent selected output values, and the absence of reciprocal own-block incidence. It may use the actual incidence degrees, the simultaneous row demands in each sheet, or constraints on local completions of a hidden value. Summing the existing single-window hidden-work credits does not become valid under any combination of the listed general hypotheses.
