# A fixed family with exponential source-value repair overhead

2026-11-13. Symbolic finite-field construction and hand counting only; no SAT, circuit enumeration, exact-gate search, or computer-driven case elimination. No literature novelty is claimed. This is a lower bound for the **source-value-preserving repair problem**, not an exponential separation of full circuit sizes and not a new MixColumns bound.

## Result

For arbitrarily large `d`, there are fixed rank-`d` feedback circuits with `G_0` source-side gates such that every source-only XOR circuit containing all their source-side output values needs

    G_0 + Omega(2^(d/3))

gates, even when it knows the entire circuit in advance. The original circuits use a one-bit consumer block and have entry-label span exactly `d`.

The construction uses many consumer-bearing gates. Therefore this result does **not** prove that the smallest full no-feedback circuit exceeds the smallest full unrestricted circuit by an exponential amount. It rules out a universally linear-in-`d` overhead for a repair theorem that preserves all source-side values, even offline. The general balanced-basis upper bound is `O(2^(d/2))`, leaving an exponential gap in the exponent between the present lower and upper bounds.

## A general auxiliary-gate obstruction

Let `d` coordinate inputs be available and let `T` be a set of `N` distinct nonzero, non-input target vectors. Suppose:

1. no three distinct vectors of `T` sum to zero; and
2. no four distinct vectors of `T` sum to zero.

Take any reduced binary-XOR circuit containing all values in `T`, with no nonzero free input forms. It has exactly `N` gates whose values are targets; call the remaining `A` gates auxiliary, and put `R=d+A`. Assume `R>=1`. Then

    N <= R + (R/4)(1+sqrt(4R-3)).                         (1)

In particular `N <= (7/4)R^(3/2)` and hence

    A >= (4N/7)^(2/3) - d.                                (2)

To prove (1), put all physical non-target values into one set `Q`: the `d` coordinate inputs and the `A` auxiliary gate values. Classify each target gate by its two operands. This is an argument for an arbitrary circuit, not a procedure that lists circuits.

* Two target operands cannot produce another target, because that would give a forbidden three-target relation. Two equal operands produce zero, not a target.
* At most `R` target gates have one target operand and one non-target operand. Indeed, for any fixed `q in Q`, there is at most one unordered pair of distinct target values with difference `q`: two different pairs would either share an endpoint and hence be identical, or give a forbidden four-target relation. Acyclicity allows that pair to be used in at most one direction. Sum this bound over `q`.
* For target gates with two non-target operands, draw a simple graph on the `R` physical nodes of `Q`, putting one edge for each such target gate. Distinct target values cannot arise from the same operand pair. The graph has no four-cycle: the XOR of its four edge labels would be a forbidden relation among four distinct target values. If it has `m` edges, every pair of vertices has at most one common neighbour. Thus

      sum_v binom(deg(v),2) <= binom(R,2).

  Cauchy's inequality gives `sum deg(v)^2 >= (2m)^2/R`, and solving the resulting quadratic yields

      m <= (R/4)(1+sqrt(4R-3)).

Adding the categories proves (1). For `R>=1`, `sqrt(4R-3)<=2 sqrt(R)` and `R<=R^(3/2)`, yielding `N<=(7/4)R^(3/2)` and then (2). The bound counts physical auxiliary values and uses no assumed linear independence of the entire target set. In particular it allows target gates to feed later target gates.

## A binary Sidon family

Let `F=GF(2^k)`, fix any binary coordinate basis of `F`, and take the `d=2k` source inputs to be the coordinate units in `F x F`. Define

    t_x = (x,x^3),       x in F and x != 0.

There are `N=2^k-1` distinct targets. Neither component of any `t_x` is zero, so none is a coordinate input.

They satisfy the two relation properties above. For three distinct nonzero `x,y,z`, a first-coordinate zero sum forces `z=x+y`. In characteristic two,

    x^3+y^3+(x+y)^3 = xy(x+y),

which is nonzero. For four distinct parameters with zero sum, set `h=x+y=z+w`; then `h!=0`, and equality of the two cube-pair sums gives

    0 = x^3+(x+h)^3+z^3+(z+h)^3
      = h(x+z)(h+x+z).

A field has no zero divisors, so `x=z` or `z=x+h=y`, contradicting distinctness. Hence no three or four distinct target vectors sum to zero. These identities cover every field size symbolically; they do not enumerate field elements or target subsets.

Since `N` grows as `2^(d/2)`, inequality (2) gives `A>= (4N/7)^(2/3)-d = Omega(2^(d/3))` for sufficiently large `d`.

## A fixed feedback circuit with only `N` source gates

Add one consumer coordinate `z` and no additional nonzero free source forms. Designate the consumer values `z+e_j` for all `d` source-coordinate inputs `e_j`; these make the span of actual source entries exactly the full `d`-dimensional source space.

For each nonzero field element `x`, construct the consumer-bearing value `z+t_x` by starting from `z` and adding the coordinate inputs in the fixed binary expansion of `t_x`, one at a time. Every intermediate has nonzero `z` part; equal already available consumer-bearing values may be reused. Then make the source-side exit

    (z+t_x)+z = t_x.

Designate every `t_x` as a source output. They are distinct, non-input values, so the circuit has exactly `G_0=N` source-side gates, one for each exit. Every added consumer-bearing chain is live through its exit, and the `z+e_j` nodes are live designated outputs.

Any source-only circuit preserving these outputs contains all `N` target values. By (1), it needs at least `N+Omega(2^(d/3))` gates. This lower bound holds even if the whole future target set and original circuit are known before construction, and even if the source-only circuit changes the wiring arbitrarily. It therefore applies a fortiori to chronological value-preserving repair. An additional independent source-side block whose every vector is free does not weaken the lower bound: set that block to zero in a proposed source-only realization, simplify without adding gates, and apply the same target-value bound.

It does not compare full circuit optima: the many `z+t_x` chains contribute to the original `G_1`, and an unrelated no-feedback realization may reorganize the consumer side. Nor is the target set a model of the four structured MixColumns rows. The result identifies a genuine higher-rank obstacle for the general value-preservation theorem, not a new bound on the joint 0/1 problem.
