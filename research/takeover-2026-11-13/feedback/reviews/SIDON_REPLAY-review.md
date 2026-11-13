# Review of the exponential source-replay lower bound

2026-11-13. Independent machine proof review of [SIDON_REPAIR](../SIDON_REPAIR.md). The finite-field family and gate bounds were checked symbolically. No target subsets, circuits, or finite families were enumerated.

## Unified count on non-target nodes

Take distinct nonzero non-input targets and a reduced circuit with no nonzero free forms. The non-target physical values form a set \(Q\) of size \(R=d+A\), including the \(d\) coordinate inputs and the \(A\) auxiliary gates. A nonzero target cannot be the XOR of two targets: equal operands give zero and unequal operands would yield a three-target relation. A zero operand can only copy the other value, so it does not contribute a target gate in a reduced circuit.

For a fixed \(q\in Q\), two distinct unordered target pairs summing to \(q\) would be disjoint, because a shared endpoint would force equality of the other endpoints. Their XOR would give a forbidden four-target relation. Thus \(q\) supplies at most one such unordered pair. Only its later endpoint could be computed by using the earlier endpoint and \(q\), so the \(Q+T\) count is at most \(R\).

Draw an edge for every target gate with two \(Q\) operands, labelled by its target value. Distinct target gates have distinct target masks and hence different operand pairs. The graph is simple. A four-cycle would have four distinct edge labels whose sum is zero, which is forbidden. Therefore every pair of vertices has at most one common neighbour. If the edge count is \(m\), then
\[
\sum_v \binom{\deg(v)}2\le\binom R2,\qquad
\sum_v\deg(v)^2\ge \frac{4m^2}{R}.
\]
Together these give \(m\le R(1+\sqrt{4R-3})/4\) for \(R\ge1\). Adding the \(Q+T\) count gives
\[
N\le \tfrac12R^{3/2}+\tfrac54R\le\tfrac74R^{3/2}.
\]
Thus \(A\ge (4N/7)^{2/3}-d\), with the lower bound truncated at zero if desired. The nonzero-target and \(R\ge1\) conditions avoid degenerate cases involving a free zero or an empty circuit, and hold for the stated family.

## The finite-field family and replay scope

For \(t_x=(x,x^3)\) with \(x\ne0\) in \(\mathbb F_{2^k}\), both coordinate blocks are nonzero, so no target is a coordinate unit. A three-term zero sum would imply \(z=x+y\) and then \(x^3+y^3+z^3=xy(x+y)\ne0\), a contradiction. For four distinct terms with the same first-coordinate pair sum \(h\ne0\), the difference of the two cube-pair sums is \(h(x+z)(h+x+z)\). This cannot vanish unless the two pairs coincide. The forbidden relations therefore do not occur.

There are \(N=2^k-1\) targets on \(d=2k\) input coordinates. The explicit bound \((4N/7)^{2/3}-d\) is \(\Omega(2^{d/3})\). A feedback circuit computes each \(z+t_x\) by adding coordinate inputs to \(z\), keeping every prefix consumer-bearing, then uses one exit to produce \(t_x\). It has exactly \(N\) source-side gates. The separate designated \(z+e_j\) outputs guarantee that all \(d\) independent coordinate inputs are actual entry labels. Reusing equal consumer-bearing values does not introduce source gates or remove any designated target.

A source-only circuit preserving the designated source values contains all targets and therefore needs at least \(N+\Omega(2^{d/3})\) gates, regardless of what it knows about the original circuit's future. The bound also applies to chronological repair. It is an overhead relative to the original \(N\) source gates, and does not compare the full circuit optima. In particular, the consumer chain cost is not controlled by this lower bound.
