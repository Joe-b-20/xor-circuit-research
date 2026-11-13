# Sparse outputs and boundary distance six still allow shared hidden work

2026-11-13. Explicit symbolic construction and hand proofs only. No search, enumeration, exact circuit optimization, or computer-driven case elimination. The construction strengthens the general obstruction in `MULTIWINDOW.md`; it establishes no new unrestricted MixColumns bound.

Independent machine reviews of the final packed-block proof are in
[the first review](reviews/sparse-review.md) and [the second review](reviews/sparse-second-review.md).
These are not formal verification or human certification. The specified `r=2` circuits
are checked in `check_continuation.py`: 29 gates, two hidden gates, and a 32-gate event-free
construction computing the same eight masks. Optimality of the latter and the universal
boundary-distance statement rely on the hand proofs below.

## Statement

For every integer `r>=1`, there is a binary linear map and an explicit circuit with the following properties:

* Every required output has weight five or seven.
* The set of coordinate input vectors and output vectors has minimum nonzero relation weight exactly six.
* All output vectors are linearly independent.
* Blocks have dimension at most four, and output windows contain at most three blocks.
* Every output family has a distinct designated own block, with no reciprocal own-block incidence.
* There are `r` visible event outputs on distinct maximal-clique windows.
* There is exactly one nonlocal gate and exactly two hidden gates, independent of `r`.
* The displayed circuit has `13r+3` gates, while the event-free minimum for the specified block partition is exactly `15r+2`.

Consequently

    L_eventfree - L >= 2r-1,

although the hidden-work count remains two. The construction does not claim that the displayed circuit is optimal among circuits permitting events.

## Inputs, blocks, and outputs

Use two two-coordinate blocks

    X={x_1,x_2},       Y={y_1,y_2},

and `r` three-coordinate blocks

    Z_i={z_i1,z_i2,z_i3},              i=1,...,r.

Write

    Xsum=x_1+x_2,
    Ysum=y_1+y_2,
    S_ik=z_i1+...+z_ik,
    S_i=S_i3.

For each `(i,k)`, with `k=1,2,3`, introduce `p_k=5-k` private coordinates

    w_ik,1,...,w_ik,p_k,

together forming one private block `W_ik` of dimension `p_k`. No private coordinate is used by any other output. Thus each group has `p_1+p_2+p_3=4+3+2=9` private coordinates, packed into three blocks of dimensions four, three, and two.

The required outputs are

    A_ik = Ysum + S_ik + sum_{ell=1}^{p_k} w_ik,ell,
    T_i  = Xsum + S_i.

Each `A_ik` has weight `2+k+(5-k)=7`. Each `T_i` has weight `2+3=5`. There are `3r` outputs of the first kind and `r` of the second kind.

The output supports are distinct, and all outputs are nonzero and non-input values. The entire output set is independent: every `A_ik` has a private coordinate appearing in no other output, which forces its coefficient to vanish in any output relation. The remaining `T_i` are independent because their `Z_i` supports are disjoint and nonzero.

## Explicit circuit and its hidden gates

Compute `Xsum`, `Ysum`, and then

    a=Xsum+Ysum.

For each `i`, compute the three retained prefixes

    P_i1=Ysum+z_i1,
    P_i2=P_i1+z_i2,
    P_i3=P_i2+z_i3.

From each `P_ik`, attach its `p_k` private coordinate inputs one at a time to obtain `A_ik`. Finally compute

    T_i=a+P_i3.

The count is

    3                       for Xsum, Ysum, a,
    3r                      for the prefixes,
    9r                      for private attachments,
    r                       for the T_i events,
    total 13r+3.

Every gate before the final `T_i` gates is event-free: its block support grows, and in-block additions build sums of distinct input coordinates. Each `T_i` cancels exactly block `Y` and preserves nonzero content on `X` and `Z_i`.

Every prefix and every private-attachment gate has an event-free path to its designated `A_ik` output. `Ysum` also has such a path. Thus these gates are retained. The only uses of `Xsum` and `a` lead to outputs through events `T_i`; both gates are hidden non-events. There are no hidden events, and

    F={T_1,...,T_r},       Q={Xsum,a},       E\F=empty.

All displayed gate values are distinct: the private attachments are distinguished by their unique private coordinates, prefixes by their nonzero `Y` and partial `Z_i` values, and `Xsum`, `Ysum`, `a`, and the `T_i` by their remaining block supports. Every gate serves a required output. The circuit is therefore reduced and fully live.

## Window geometry

The target window of `T_i` is

    V_i={X,Z_i}.

The output window `U_ik` of `A_ik` is `{Y,Z_i,W_ik}`. Its size is three. All block dimensions are at most four.

Assign own block `Z_i` to the one-output family `T_i`, and own block `W_ik` to the one-output family `A_ik`. These designated blocks are distinct. The `U_ik` window contains `Z_i`, but `V_i` contains no private block; distinct `U` windows contain none of one another's private blocks; and distinct `V` windows contain none of one another's own blocks. Thus there is no reciprocal own-block incidence.

No window contains both `X` and `Y`, or both `X` and any private block. The only neighbours of `X` in the co-occurrence graph are the different `Z_i` blocks, and distinct `Z_i` blocks are not adjacent. Consequently every selected target window `V_i={X,Z_i}` is a maximal clique.

The gate `a` is nonlocal because it meets `X` and `Y`. All other gates are local: `Xsum` and `Ysum` are supported on one covered block, prefixes are supported on `{Y,Z_i}`, attachments lie inside `U_ik`, and targets lie inside `V_i`. Hence exactly one nonlocal gate supplies all `r` selected events, while the total hidden count is two because the local gate `Xsum` is hidden as well.

This own-block property does not assert the entire MixColumns sheet structure: some input blocks are not designated own blocks, and each selected family here contains one row rather than four.

## Exact event-free minimum

We prove

    L_eventfree=15r+2.

An event-free circuit may cancel coordinates inside a block while that block remains nonzero. The counting argument below zeros private coordinates one at a time, allowing the intermediate restricted circuits to have events. Only the final restriction, which zeros every private block completely, is used as an event-free circuit. The normalization invariant establishing that distinction is proved explicitly.

### Removing the private inputs loses at least `9r` gates

Start with an event-free circuit for all `A_ik,T_i`, reducing duplicates and dead gates when needed. Set the `9r` private coordinates to zero successively, bypassing wires, eliminating zero gates, reusing earlier equal values, and pruning dead gates after each step. These operations delete gates and redirect readers; they never add a gate. Intermediate circuits are not asserted to be event-free.

At any step, the currently selected private coordinate still occurs in its projected designated `A_ik`. That output still contains `Ysum+S_ik`, of weight at least three, so it is not a coordinate input. The private coordinate must therefore enter a live gate. Take its earliest live direct reader in the current topological order. Its other operand has no earlier computation depending on that input; otherwise an earlier direct reader would exist. On setting the coordinate to zero, this gate becomes its other operand and disappears. Further normalization can only delete more gates.

Thus each of the `9r` successive restrictions removes at least one physical gate from the current circuit. We next verify that the final circuit is event-free despite the finer intermediate restrictions.

**Normalization invariant.** After any prefix of the restrictions, each surviving original physical gate has operand values equal to the current projections of its original operand values. This holds before normalization. A bypass or duplicate reuse redirects a reader to an equal current value and therefore preserves the invariant. An equality established at one restriction remains an equality under every further coordinate projection. Gate pruning changes no remaining operand value. Induction proves the invariant throughout the sequence.

After all private coordinates are zero, the cumulative projection deletes complete private blocks and leaves `X,Y,Z_i` unchanged. If a surviving gate cancelled a nonzero whole block, its two operand values would agree nontrivially on a surviving block. By the invariant these are exactly the original gate's components on that block, so the original event-free gate would already have cancelled it, a contradiction. Gates with a zero operand have been bypassed. Hence the final circuit is event-free.

It computes

    P_ik=Ysum+S_ik,
    T_i=Xsum+S_i,

with at most `G'-9r` gates if the starting event-free circuit had `G'` gates. The argument does not claim that zeroing only part of a private block preserves event-freeness. It proves the gate loss one coordinate at a time, and event-freeness only after every private block has been removed completely.

### The reduced problem needs at least `6r+2` gates

First, its `3r` distinct required prefix values `P_ik` all have nonzero `Y` components. They require `3r` distinct gates. There is at least one additional `Y`-bearing gate before the earliest such output gate.

To verify that last claim, consider the earliest `P_ik` gate. If neither operand is a proper `Y`-bearing gate, any operand carrying `Y` is one of the two coordinate inputs `y_1,y_2`. To produce the `Y` component `Ysum`, both operands would have to be exactly these inputs; their sum would have no `Z_i` component and could not equal `P_ik`. Therefore a proper `Y`-bearing gate ancestor exists. By earliestness it is not any of the designated `P` gates. Hence the circuit contains at least `3r+1` `Y`-bearing gates.

Next consider the ancestor cone of `T_i` in a reduced event-free circuit. Every gate in it is supported on `{X,Z_i}` and hence avoids `Y`. The target has weight five, so its cone contains at least four gates: a binary gate DAG reaching five distinct input coordinates needs at least four binary gates.

If a gate belongs to the cones of two different `T_i,T_j`, its support lies inside `V_i intersect V_j={X}`. The only nonzero values on the two-coordinate block `X` are `x_1,x_2,Xsum`. Reducedness removes gate copies of the coordinate inputs and leaves at most one gate of value `Xsum`. Therefore this single possible gate accounts for all intersections between distinct target cones.

If it belongs to `s` cones, summing the cone sizes counts it `s` times instead of once and no other gate more than once. The union of the `r` target cones consequently contains at least

    4r-(r-1)=3r+1

gates. If no shared `Xsum` gate exists, the stronger count `4r` holds. All these gates avoid `Y`, so they are disjoint from the `3r+1` `Y`-bearing gates already counted. This proves the reduced lower bound `6r+2`.

Combining the restriction loss and the reduced bound gives

    G' >= 9r+(6r+2)=15r+2.

### Matching event-free construction

Compute `Xsum` and `Ysum` with two gates. For each `i`, compute the clean prefixes `S_i2` and `S_i3` with two gates, taking `S_i1=z_i1` as an input. Compute the three `P_ik=Ysum+S_ik` and the one `T_i=Xsum+S_i3`. This uses

    2+2r+3r+r=6r+2

gates. Attach the `9r` private coordinates to the appropriate `P_ik`, one gate each, to obtain all `A_ik`. Every step is event-free. The total is `15r+2`, proving the exact event-free minimum.

The explicit cancellation circuit therefore uses `2r-1` fewer gates than every event-free circuit, for every `r>=1`.

## Boundary minimum relation weight is exactly six

The boundary set consists of all distinct coordinate input vectors and all distinct required output vectors. A nonzero relation in this set must include at least one output, because the coordinate inputs are independent.

For a selected nonempty output subset `O`, the unique coordinate-input subset that completes it to a relation is the support of `sum_{o in O} o`. The resulting relation weight is therefore

    |O| + wt(sum_{o in O} o).

Let `a` be the number of selected `A` outputs and `t` the number of selected `T` outputs.

* If `a>=2`, each selected `A` contributes at least two unique private coordinates that no other output can cancel. Thus the relation weight is at least `(a+t)+2a>=6`.
* If `a=1` and `t>=1`, at least two private coordinates and both coordinates of `Ysum` survive. There are at least two selected outputs. The relation weight is at least `2+2+2=6`.
* If `a=1,t=0`, the sole output has weight seven, giving relation weight eight.
* If `a=0,t>=1`, the `Z_i` contributions are disjoint triples. Their sum has weight `3t`, and `Xsum` adds two further coordinates exactly when `t` is odd. The relation weight is `4t+2[t is odd]`, at least six.

These alternatives are a symbolic proof for arbitrary output subsets, not a finite subset check. Finally any one `T_i`, together with its five input coordinates, gives a relation of weight six. Thus the minimum nonzero boundary relation weight is exactly six.

## Affine-completion control

For the selected `T_i` events, the nonlocal operand graph again has just the single vertex `a`. Put `K=span{T_i}`. Every value in `a+K` still contains `Ysum`; locality therefore forces its `X` component to vanish and permits at most one `Z_i` component. The local completions are exactly

    E={Ysum+S_i : i=1,...,r}.

Their differences from the first completion are the independent vectors `S_i+S_1`, `i>1`. Hence `dim K=r` and `dim Delta=r-1`; the affine-completion theorem gives exactly one nonlocal operand, attained here. It counts nonlocal gates, so the additional hidden but local `Xsum` gate is outside that count, as required by its stated scope.

## What this does and does not show

Sparse row weights five and seven, boundary relation distance six, independent output rows, fixed block dimension, bounded window width, maximal selected windows, and no reciprocal own-block incidence do not prevent a constant amount of hidden work from serving arbitrarily many windows profitably.

In particular, under these hypotheses there is no universal constant `c` such that the saving of an arbitrary circuit below the event-free optimum is at most `c` times its hidden-gate count. Here that count is two while the proved saving is `2r-1`. The same obstruction applies if only nonlocal gates are counted, since there is exactly one.

The map remains rectangular and has a different incidence structure from MixColumns. It has one selected event output per own-block family, rather than all four structured MixColumns rows, and its common input blocks occur in a growing number of windows. The result therefore identifies insufficient hypotheses for a general multiwindow argument; it neither proves a MixColumns counterexample nor changes `75<=L(MixColumns)<=88`.
