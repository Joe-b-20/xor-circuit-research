# Twelve consumer gates: what survives from the six-gate mirror

**Later continuation:** [five-entry closure](FIVE_ENTRY_TWELVE_CLOSED.md) excludes
the target-live five-entry case below 22. The six-entry restrictions and specified
seven-gate counterexample below remain in force.

2026-11-14. Structural deductions and one specified counterexample. No circuit search, enumeration, or computer-driven case elimination. These statements do not settle the twelve-consumer joint minimum.

## The wire theorem depends on the ordinary budget, not the entry count

Consider a relaxed consumer graph for four outputs with ordinary masks equal to the four triples on four ordinary coordinates. Assume every counted consumer-bearing gate lies in a target cone, and there are `tau` entry occurrences and

    K=tau+6

consumer-bearing gates. Treat each entry source operand as a separate formal input used once.

Bypassing the entries leaves six ordinary non-entry gates computing the four triples. This is the ordinary minimum, so all six remaining values are nonzero, non-input, and distinct. Every ordinary-mask fibre of the original graph therefore has one input or non-entry root, and its entry edges form a rooted tree. An exit is the sum of labels along the path between its equal-mask operands, using labels read before the exit.

There are `4+tau` formal/ordinary inputs, four designated outputs, and `tau+6` XOR gates. Binary-copy expansion therefore has exactly six copies, by wire balance. Literal transposition has six XORs. Removing the `tau` trace ports and suppressing their unary entry-dual copies gives the same marked-wire correspondence as in [TIGHT_FIBRE_WIRES](TIGHT_FIBRE_WIRES.md).

Consequently that note's proofs apply unchanged:

- The marked wire for an entry carries its influence trace and has ordinary derivative equal to the original entry's own mask.
- Wires carrying the two distinct even helper values cannot have the same nonzero ordinary derivative.
- Two adjacent entry edges expose their trace sum on a wire with their common own derivative; exposures at different original vertices can be made simultaneously.
- No fibre path contains three consecutive entry edges with distinct odd traces.

In particular, if **all entry traces are odd and pairwise distinct**, every exit path has at most two edges. Chronological source replay then has zero overhead. In the two-sheet MixColumns application, copying the original consumer after that replay gives a no-feedback circuit of the same total cost, so the [no-feedback minimum 22](../augmented/CONSEQUENCES.md) excludes a total below 22 in this subclass.

These facts apply to `K=12,tau=6`. They are not automatically applicable to an arbitrary twelve-gate consumer, which may have fewer entries or gates outside the relaxed target cones.

## Trace equations in the six-entry rank-five interface

For the MixColumns consumer, the four required source parts span a three-dimensional `D` and have their all-four sum as their sole relation. Let `Z` be the four-by-six matrix of formal entry traces, let `L` be its row space, and let `Phi` send the six formal entry units to their actual labels. Then `Phi(L)=D`.

The trace rank is four. If it were three, `Phi` would be injective on `L`. The total sum of the four formal target rows would then vanish, because its image is the zero sum of the actual target labels. All traces would be even. Three independent even traces would require three distinct even gate values in addition to the four odd triples, contradicting the six-gate mirror.

Suppose the actual entry span `U` has dimension five, equivalently `dim(U/D)=2`. Let `Q` map formal entry coefficients to their quotient signatures in `U/D`. Its kernel has dimension four, and `L subset ker Q`, so

    L=ker Q,       ker Z=rowspace Q.

Thus the two-dimensional relation space on the six traces is precisely the row space of the quotient-signature map. This is a relation-space identity, not a classification of circuit shapes.

The actual label map has a one-dimensional kernel. Let `o` be the indicator of the odd trace positions. Since

    o=Z^T(1,1,1,1)^T,

rank four makes `o` nonzero, and the all-four relation among the actual targets gives `Phi(o)=0`. Hence

    ker Phi=span{o}.

The unique relation among the six actual label occurrences is exactly the sum over the odd trace positions.

Here the consumer count also saturates quotient cost: `K=12=10+dim(U/D)`. The [saturated projection theorem](SATURATED_QUOTIENT.md) therefore gives a unique physical difference pair for every actual nonclean label. Such a label cannot repeat and cannot be newly supplied by a consumer exit. A zero label is also impossible: its entry would duplicate the nonfree operand, contradicting the same saturated collision structure (or giving an additional deletion beyond a quotient basis).

These equations permit repeated traces and may permit a repeated clean label. They do not justify treating the six traces as distinct or assuming that every return is a pair of entry labels. The zero-overhead conclusion above is conditional on odd, pairwise distinct traces.

## Five entries with independent labels require a repeated ordinary root

Keep the target-cone hypothesis, and now suppose `K=12,tau=5` and the actual entry span has rank five. The label map `Phi` is injective, so the formal target-row space has rank three and all entry traces are even. The literal mirror has seven gates. Its four odd triple gates and three independent even trace values exhaust that budget. Every trace is nonzero and belongs to those three independent even values; a zero trace would need a zero signal unavailable in that exhausted mirror.

The five traces therefore form three classes with multiplicities `(3,1,1)` or `(2,2,1)`. Their class sums of actual labels form a basis of `D`: the three trace values are independent, the five labels are independent, and the formal target-row space consists of coefficient vectors constant on each trace class.

Two adjacent entry edges with different traces are impossible. Flexible local accumulation would expose their nonzero even trace sum. That sum is outside the three independent even masks already required in every seven-gate mirror, and is neither an odd input nor an odd triple. An eighth gate would be needed. Thus every connected entry tree contains only one trace class.

Suppose every own-mask fibre had only one ordinary-input or non-entry root. Each fibre would be one entry tree, so every exit would be the sum of a subset of one trace class, with all those labels supplied earlier. In the `(2,2,1)` profile each such sum costs at most one XOR; source replay has zero overhead. A source budget `G_0<=9` would then contradict the ten-gate local source-row minimum.

In the `(3,1,1)` profile, the only possible harder return is the sum of all three labels in the size-three class. If it never occurs, replay again has zero overhead. If it occurs, compute one pair of its already supplied labels in a single extra gate and finish the return with its original XOR. Retaining that pair repairs any repetition of the same value. The returned class sum and the two actual singleton-class labels form three independent physical clean diagonals. The source-only replay therefore contains the four source rows and a diagonal basis within `G_0+1<=10` gates, contrary to [A12](../augmented/PROOF.md).

Consequently a twelve-consumer candidate of total at most 21 in this five-entry, rank-five class must have a fibre with at least two roots. Its seven non-entry own occurrences include at least the four triple first occurrences and two distinct even first occurrences. There is at most one remaining occurrence. Therefore it has exactly one two-root fibre and all other fibres have one root; there are exactly two distinct nonzero even own masks. The additional root is a non-entry occurrence repeating an earlier own mask, possibly that of an ordinary input. This is a necessary structural reduction, not an exclusion of the two-root case.

A stronger necessary condition is that **some nonredundant exit connects the two entry-tree components in that unique two-root fibre**. Here nonredundant means that its value was not already physically available as a source value before the exit. The preceding replay argument only requires the two operands of each useful exit to belong to the same entry-tree component; it does not require every fibre to be connected. Within a component the root contribution cancels, the exit is a path sum, and all edges have one trace class. If every exit between different components merely repeats an earlier source value, bypass those exits and apply the same componentwise replay. The `(2,2,1)` case then has zero overhead. The `(3,1,1)` case either has zero overhead or has its sole difficult triple-class return, repaired with at most one extra gate and supplying a clean diagonal basis together with the two singleton labels. The same local-ten or A12 contradiction follows at `G_0<=9`. Therefore at least one exit must newly return a value using parents from the two separate trees. All other fibres have one root, so the required exit belongs to the unique two-root fibre. This does not identify the returned value or assert that it cannot be computed by some other source-side expression.


## A seventh ordinary gate breaks even-wire separation

A fixed seven-gate ordinary circuit demonstrates why the six-gate derivative argument cannot simply be reused for a larger mirror. On four ordinary inputs compute

    p=x0+x1,
    q=x2+x3,
    t=p+q,
    E_i=t+x_i       for i=0,1,2,3.

These are seven XOR gates, all live, and the four outputs are exactly the ordinary triples. Perturbing the wire `p -> t` flips all four outputs. Perturbing the different wire `q -> t` also flips all four outputs. Thus these two wires carry distinct nonzero even values but have the same nonzero ordinary derivative `(1,1,1,1)`.

The new even gate `t` is a common reader of the two earlier even helpers. This is precisely the possibility excluded by the six-gate proof, where no third even gate is available. The example is a direct symbolic construction, not a search or an optimality claim for a new task.

A twelve-gate consumer with five entries has seven ordinary non-entry slots. Its literal mirror may consequently admit the mechanism above. The example by itself is not a twelve-gate mixed-label consumer or a smaller joint circuit; it only refutes an unqualified extension of even-wire separation beyond six ordinary gates.
