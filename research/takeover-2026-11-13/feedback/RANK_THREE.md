# A rank-three interface permits feedback removal for at most one extra gate

2026-11-13. Causal hand construction and linear algebra only; no circuit search, enumeration, or computer-driven case elimination. The [general rank theorem](GENERAL_REPAIR.md) extends this construction to arbitrary entry rank. This note gives its sharp rank-three form and a necessary condition for the unrestricted joint problem. It does not prove an unrestricted joint lower bound of twenty-two.

**Subsequent result:** [five physical diagonals](FIVE_DIAGONALS.md) close the exceptional joint case: exactly ten consumer-bearing gates require at least 22 total gates, even with feedback. The replay theorem below is unchanged.

## General causal setting

Assume zero is freely available; equivalently, only nonzero source values need to be reproduced and zero uses can be bypassed. This holds in the joint model because the free block includes zero.

Partition the ordinary coordinates into source coordinates and consumer coordinates `z`; any free coordinates belong to the source side. Count a gate as consumer-bearing when its `z` part is nonzero, and otherwise as a source-side gate. A source-side gate with two consumer-bearing operands is an **exit**: their equal nonzero `z` parts cancel. Every other source-side gate has two source-side operands.

Let `D` be a fixed source-value space of dimension at most three. Assume every source-side operand read by a consumer-bearing gate lies in `D`. Such a use is an actual entry; only physically available source values count as entry labels. Assume consumer-coordinate inputs have zero source part.

By induction in the original gate order, every consumer-bearing source part belongs to the span of earlier actual entry labels. Consequently every exit belongs to `D` and to the span of entry labels already available before that exit. This remains valid when earlier entry labels themselves came from exits.

**Theorem R3.** If the original circuit has `G_0` source-side gates, all source-side gate values can be supplied by a circuit on the source inputs alone using at most `G_0+1` gates. The construction preserves the chronological availability of every original source-side value. If `dim D<=2`, at most `G_0` gates suffice.

The theorem does not charge virtual combinations as available operands. Every replacement XOR reads source values already physically supplied by the replacement circuit.

## Small-space addition lemma

Let `S` be the set of currently available distinct nonzero values in `D`. Every value in `span S` has a one-XOR realization from available values, or is already available, except possibly when `dim span S=3` and `S` consists of exactly three independent values. In that exception the only unavailable value needing two XORs is their three-term sum.

For rank at most two, choose an available basis: its span consists of its basis values and their possible pair sum. For rank three, choose available independent values `u,v,w`. If any fourth distinct nonzero value is available, it is either a pair sum of this basis or the triple sum. If it is a pair sum, for example `u+v`, then `u+v+w=(u+v)+w` is a one-XOR value, as are the other pair sums. If it is the triple sum, the three pair sums are obtained by adding it to the complementary basis value. Thus every value in the three-dimensional span is either available or one XOR away.

If precisely `u,v,w` are available, their triple sum can be produced by two gates, first `u+v` and then `(u+v)+w`. These are genuine new physical values. After the first such gate there are already four available distinct nonzero values spanning `D`.

## Chronological removal of all exits

Replay the original source-side gates in topological order and omit the consumer-bearing gates.

* At an ordinary source-side gate, both source operands have already been supplied, so recreate its XOR with one gate, or bypass it if its value is already available.
* At an exit, all original entry labels preceding it have already been supplied. Its source value lies in their span, by the causal induction above. Use the small-space lemma to supply that value from currently available values in `D`.

An exit therefore costs at most one replacement gate unless it is the exceptional three-term sum of exactly three available independent values. At most one exit incurs that exception. Replacing it with two gates makes at least four distinct nonzero clean values available, and availability never decreases. All later exits then cost at most one gate.

Replacing the original one gate at each exit by at most one, except for this single possible two-gate replacement, proves `G_0+1`. In dimension at most two the exception never occurs, proving the cost-preserving form. Added intermediate values are retained for later reuse; no assumption of consecutiveness of entry labels or of exit gates is made.

## Application to a ten-gate consumer in the unrestricted joint problem

Use free block `a`, ordinary blocks `b,z`, and targets

    U_c=E_c(b)+s_c(a),
    Y_c=E_c(z)+s_c(b)+s_c(a),
    D={v(b)+v(a): v even}.

Allow arbitrary feedback into the first-sheet ancestors. Suppose exactly ten gates have nonzero `z` part. Treat every zero-`z` operand as freely supplied when considering the consumer. The [entry-deletion bound](../compatibility/QUOTIENT.md) and the exact ten-gate sheet minimum force every actual consumer entry label to belong to `D`. Their span is all of `D`, because the source parts of the four `Y_c` span `D`.

The hypotheses of R3 therefore hold. Its source-only replacement contains every original zero-`z` value, in particular all four `U_c` and three independent actual entry labels in `D`. No nonzero value of `D` is a base source coordinate or a wholly free `a` value, so these labels are physical supplied values. The replacement is an augmented first-sheet supplier, whose minimum is [twelve](../augmented/PROOF.md). Therefore

    G_0+1 >= 12,       G_0>=11.

**Corollary.** An unrestricted joint circuit with exactly ten consumer-bearing gates has at least twenty-one total gates. If it has exactly twenty-one, cost-preserving removal of all exits is impossible.

More specifically, in the chronological replay there must be an exit at which the available clean values consist of three independent values and the exit is their three-term sum. It cannot have a one-XOR decomposition using earlier available source values; otherwise using that decomposition at the only potentially costly step would give an eleven-gate source-only augmented supplier. Both replacement gates at the exceptional step are needed to reach the twelve-gate minimum, and no savings elsewhere can cancel that one-gate overhead.

This is a necessary structural obstruction, not an existence claim for such a joint circuit. The ten-gate consumer may impose further conditions that make this exceptional exit impossible. R3 alone does not cover a consumer with eleven or more gates, whose entry labels may extend outside `D`.

## Why the one-gate allowance is necessary in the general theorem

The following directly specified fragment shows that causal span containment alone does not imply cost-preserving exit removal. Suppose the only available nonzero source values are independent `u,v,w`, and let `z` be one consumer coordinate. Compute

    p=z+u,
    q=p+v,
    r=z+w,
    e=q+r=u+v+w.

There are three consumer-bearing gates and one exit. All actual entry labels lie in the rank-three space `span{u,v,w}`. Recreating `e` from the three given source values alone needs two XOR gates: no one XOR of two available values can equal the sum of all three independent values. This demonstrates sharpness of the one-gate repair allowance for the general causal model. It does not compute the four joint targets and is not a counterexample to an unrestricted twenty-two-gate joint bound.

## Unproved mirror route for a four-entry consumer

A bounded attempt considered a ten-gate consumer with four entries, including the possible pattern of three independent label values with one repeated. Its six-gate ordinary transpose has four independent entry traces; the two repeated-label occurrences have odd traces and the other two have the transpose's two even helper values as traces. The tentative route was to use properties of the ordinary adjoints of these two even helpers to place the two unrepeated entry labels in different own-mask fibres, thereby limiting a same-own exit to a one-XOR source expression.

The missing step is an identification between the **original** consumer's internal own-mask fibres and the adjoint signals obtained by transposing its mirror again. Transposition preserves the output linear map, but that does not establish preservation of internal nodes, equal-own operand pairs, or the entry-label paths relevant to an original exit. No such identification has been proved. The route supplies no four-entry feedback exclusion and is not used in any theorem above. Eventual availability of four distinct labels would also be insufficient by itself: a difficult exit could occur before the fourth label is physically supplied.

The later [marked-wire lemma](WIRE_DUALITY.md) resolves the identification for the repeated-label case by retaining explicit XOR/copy nodes. The broader joint consequence is now proved through five physical diagonals, without requiring a consumer classification.
