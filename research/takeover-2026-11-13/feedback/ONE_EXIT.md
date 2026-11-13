# A one-exit feedback separation with four outputs on each side

2026-11-13. Explicit construction and hand lower bounds. No SAT, exhaustive enumeration, circuit search, exact-gate search, or computer-driven case elimination. This is a general linear-map counterexample to cost-free no-feedback normalization. It is **not** a MixColumns counterexample, and it does not change the `75<=L(MixColumns)<=88` interval or the established conditional 0/1-sheet result.

## Result

There is a binary linear map with four designated first-side outputs and four designated consumer-side outputs such that:

* every output has weight five, and the eight outputs are independent;
* the input/output boundary has minimum nonzero relation weight six;
* every input block has dimension at most three, and every individual output window meets at most three blocks;
* a reduced 21-gate circuit computes the map with exactly one whole-block cancellation, an exit from a **one-bit** consumer block;
* every circuit in which the four first-side output cones have no nonzero consumer-block gate requires at least **22** gates, and a no-feedback 22-gate circuit exists.

Consequently the unrestricted minimum is exactly 21 and the no-feedback minimum is exactly 22. An independently free input block can be added without changing the argument, provided its coordinates do not occur in the targets. The construction gives an explicit setting in which eliminating one unit-dimensional feedback exit necessarily increases total size.

This construction adapts the [earlier attributed prefix mechanism](../directions/PROJECTION.md#5-sharpness-the-prefix-family) using private coordinates, but the bookkeeping here fixes four outputs on each side and makes **all eight** rows weight five with boundary distance six. The four first-side rows do not have the distinct own-block triples of MixColumns, and the map is rectangular. Those differences prevent importing the result as a counterexample to a MixColumns-specific normalization.

## Inputs and output values

Use the ordinary input blocks

    Y = {y0,y1,y2},                 Z = {z},
    U_j = {u_j0,u_j1}               (j=0,1,2,3),
    V_1 = {v_10,v_11,v_12},         V_2 = {v_20,v_21},
    V_3 = {v_30},                   V_4 = {v_40,v_41}.

All coordinates are independent. Write `y=y0+y1+y2`. The first-side required outputs are

    A_j = y + u_j0+u_j1,                     j=0,1,2,3.

The consumer-side required outputs are

    C_1 = z+y0       + v_10+v_11+v_12,
    C_2 = z+y0+y1    + v_20+v_21,
    C_3 = z+y0+y1+y2 + v_30,
    C_4 = z+y0+y2    + v_40+v_41.

There are 20 ordinary coordinates and eight output rows. Each `A_j` has block support `{Y,U_j}`; each `C_i` has support `{Y,Z,V_i}`. Every row has weight five. Each row contains private coordinates not occurring in any other row, so the eight outputs are independent.

## A 21-gate circuit with one exit

Compute

    g1=z+y0,
    g2=g1+y1,
    g3=g2+y2,
    g4=g1+y2,
    y=g3+z.

The last gate cancels exactly the whole consumer block `Z`. All other gates shown are event-free. Attach the two private coordinates of `U_j` to `y` in two gates for each `A_j`. Attach the private coordinates of `V_i` to `g_i` in three, two, one, and two gates for `C_1,...,C_4`.

The total is

    4 prefix gates + 1 exit + 8 first-side tags + 8 consumer tags = 21.

All intermediate values are distinct non-input values and are live. None of the private-coordinate additions cancels a whole block, so the exit `g3+z` is the only event. It feeds every first-side output, while `g3` is also retained by its consumer output. The [direct verifier](check_one_exit.py) checks these two specified constructions, including all eight output masks, rank, liveness, and event counts; no circuit search is used.

## Unrestricted lower bound 21

There are 16 private tag coordinates: eight on the first side and eight on the consumer side. Set them to zero one at a time in an arbitrary XOR circuit, bypassing the resulting wire or zero gates and pruning dead gates as needed. At each step the private coordinate being removed still appears in its designated output together with the corresponding nonzero base `y` or `z+...`, which does not depend on any private coordinate. That output is not a coordinate input. Hence some live gate must read the private coordinate; its first direct reader becomes a wire or zero when the coordinate is set to zero. At least one gate is removed at each of the 16 steps. No event-free hypothesis is used here.

After all tags are zero, the designated outputs include the following five distinct non-input values:

    y0+y1+y2,
    z+y0,  z+y0+y1,  z+y0+y1+y2,  z+y0+y2.

Each requires a distinct paid gate. The original circuit therefore has at least `16+5=21` gates, matching the displayed circuit.

## No-feedback lower bound 22

Here *no feedback to the first side* means that every gate in the ancestor union of `A_0,...,A_3` has zero `Z` component. The condition applies to physical gate values and does not require the whole circuit to be event-free.

First set the eight consumer-private coordinates in the `V_i` blocks to zero, one at a time. As above, each step removes at least one gate because its designated `C_i` still contains its fixed non-input base `z+...`. Use only zero/copy bypasses and pruning; do not redirect to an unrelated equal-valued node. These operations only replace a node by its own ancestors. Since the restriction does not change `Z` components, every gate left in a first-side output cone is still an original first-cone ancestor with zero `Z` part. Thus the no-feedback property survives this restriction, even though no restriction on intermediate events is needed.

In the resulting circuit, the first-side cone has at least ten gates. To see this, set its eight private `U_j` coordinates to zero one at a time, bypassing gates within that cone. Each removal costs at least one gate because the associated output retains the non-input base `y0+y1+y2`. The remaining circuit computes that sum of three independent coordinate inputs, which requires at least two binary XOR gates. So the original first-side cone contained at least `8+2=10` gates.

The four distinct non-input consumer outputs remaining after the `V_i` restriction are `g1,g2,g3,g4`. Each has a nonzero `Z` component, so its physical output gate is outside the first-side cone. The restricted circuit has at least `10+4=14` gates. Restoring the eight gates lost to consumer-tag restriction yields at least `14+8=22` gates in the original circuit.

For equality, compute `y0+y1`, then `y`; attach all eight `U_j` tag coordinates. Separately compute `g1,g2,g3,g4` in the first four gates displayed above and attach all eight `V_i` tag coordinates. This uses `2+8+4+8=22` gates and has no nonzero-`Z` gate in a first-side output cone. It is in fact event-free, although the lower bound did not assume that.

## Boundary relation distance

Every output has weight five, so an output plus its five input coordinates gives a relation of weight six. To prove no shorter relation exists, choose any nonempty subset of outputs. Because each output has private coordinates unique to it, the chosen subset's XOR retains at least one private coordinate per chosen output.

* One selected output gives relation weight six.
* Two selected outputs differ in at least four input coordinates. Two first-side rows differ in four private coordinates. A first-side row and a consumer row differ in the first row's two private coordinates, the consumer's at least one private coordinate, and `z`. For two consumer rows, any pair with only three private coordinates in total has different `Y` components (the pairs `C_2,C_3` and `C_3,C_4`); every other pair has at least four private coordinates.
* Three selected outputs retain at least three private coordinates, so their relation weight is at least six. Four or more retain at least four private coordinates, making the relation weight larger still.

For a chosen output subset, its XOR support is the unique set of coordinate inputs needed to complete a relation. Thus the boundary minimum is exactly six. This is a symbolic argument over arbitrary subsets, not a finite subset check.

## Scope

The single exit creates the dynamic clean value `y` from an already useful consumer-bearing value `g3`; the consumer prefixes remain useful as outputs. The proof counts actual gates, not the dimension of a virtual supplier span. The example rules out a general theorem saying that one consumer-block exit or one-dimensional contamination can always be removed at no extra cost, even with four rows on each side, weight-five independent outputs, bounded block size/window width, and boundary relation distance six.

It does not exhibit the four `E_c/s_c` rows of either MixColumns sheet and does not establish any fact about the unresolved unrestricted 0/1 joint minimum. A MixColumns-specific triangularization argument would have to use row structure or incidence properties beyond those listed here.
