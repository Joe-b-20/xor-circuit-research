# Independent review: scalable causal startup gaps

2026-11-14. Independent machine review of the complete saved
[CAUSAL_BOOTSTRAP_GAP.md](../CAUSAL_BOOTSTRAP_GAP.md). Hand verification of
the specified families and universal lower bounds, with no circuit search or
enumeration. This is not formal verification or a literature-novelty claim.

## First-target lower bound and the full three-arm family

The first produced required value has no other required non-input value in
its ancestor cone. The connected cone with g gates and s actual coordinate
inputs has 2g operand-edge occurrences, hence g>=s-1. At least its w supported
coordinates are ancestors. The remaining m-1 distinct target occurrences are
outside that cone, proving L>=m+w-2 without summing overlapping output cones.

For three length-k arms, the full target set has exactly 3k+1 distinct values
and minimum weight 2k. Its 3k tree-edge equations leave one unknown center;
the three-endpoint equation fixes that center to the total input sum p.
Thus the equations are uniquely solvable and attain cyclic size 3k+1. The
target count is a matching cyclic lower bound. Producing one endpoint from
its 2k inputs, then walking the target tree, attains the causal bound 5k-1.
The preparatory values can be ordinary prefix sums of those 2k inputs; all
proper prefixes have smaller weight than any target.

## Square invertible family and exact inverse cost

Deleting the C endpoint leaves 3k target values. Their adjacent differences
give every input unit except c_k. The retained center p has c_k coefficient
one, so the target values form a basis and define a square invertible map.
Minimum target weight is still 2k. The same tree walk, stopping before the
deleted endpoint, attains the exact causal cost 5k-2.

The available-triple classification is exhaustive for k>=2. Three units are
independent; a target of weight at least four cannot equal two units. Two
targets differ in one coordinate exactly on a retained arm edge. A sum of
three targets is zero only when their removed prefixes cover all three
blocks, requiring the three full endpoints. One endpoint is absent. Hence
there are exactly 3k-1 available triples, the retained tree edges. The
relation space on 3k inputs and 3k target vectors has dimension 3k. Those
triples cannot span it, so a cyclic realization needs an extra value. Adding
the deleted endpoint supplies a realization of size 3k+1, proving exactness.

For the inverse, the two retained endpoints produce the deleted endpoint in
one XOR. All 3k original coordinate outputs then arise as differences along
the full arm edges, for a total of 3k+1. A putative 3k-gate inverse would
have no auxiliary values, leaving exactly the same boundary vector set after
an invertible coordinate change. Its triple relations still number only
3k-1 and cannot contain 3k independent gate equations. Thus the inverse cost
is also exactly 3k+1. Both additive gaps 2k-3 are proved, not inferred from
an assumed general relation between inversion and circuit complexity.

## Odd numbers of arms

For odd r, the r endpoint values sum to zero. The specified r-3 auxiliary
partial sums and r-2 equations express that relation, and together with the
rk tree-edge equations determine the center uniquely. The auxiliary values
are nonzero whole-block prefixes or suffixes of 2 through r-3 blocks. They
are distinct from one another, from inputs, and from every target, whose
support omits at most one block prefix. Thus the cyclic upper bound rk+r-2
counts actual distinct additional values.

The causal lower bound and traversal both give (2r-1)k-1. The displayed ratio
lower bound tends to 2-1/r for fixed odd r as k grows. The target-count lower
bound L_cyc>=rk+1 also gives the matching ratio upper bound in this limit,
so taking k large and then r large indeed gives ratios approaching two.
The note correctly claims no exact cyclic minimum for r>3 and no universal
upper ratio for arbitrary target maps.

## Scope

All target families are solved in the unrestricted circuit model. The cyclic
comparison isolates a linear amount of work that correct independent
equations omit when they do not require executable first production. The
saved interpretation correctly treats this as an obstruction to a general
proof method, not a new MixColumns lower bound. Its stated numerical
first-target bound of 35 for MixColumns is only a limitation of that lemma.

The complete note passes review.

## Exact square maps for every odd arm count

I also checked the later Section 5, which proves exact square-map cyclic
and inverse costs for all odd r>=3 and k>=2. Removing one endpoint preserves
the tree-difference basis argument and gives forward cost (2r-1)k-2.

In inverse coordinates, the exceptional original input is the sum of the
r vertices consisting of the retained full endpoints and the truncated
arm's final vertex. These vertices form an independent set S of the retained
tree. This uses k>=2: no selected vertex is the center or adjacent to a
selected vertex on another arm.

Granting the N-1 ordinary edge outputs removes their unknown columns from
an invertible cyclic system. The remaining g columns have full rank, so g
rows can be selected with an invertible matrix on them. After projection
outside S, each granted edge output becomes zero or one coordinate unit,
since no edge has both endpoints in S. Known inverse inputs also become
zero or units. Formal unknown columns are retained even if their projected
values vanish or coincide, preserving matrix invertibility.

For the resulting parity target on r independent coordinates, select the
s rows whose unknown sum is that target variable. Independence gives at
least s occurring unknown columns u. Those columns contribute at least
2u-1 term occurrences, and the known terms contribute at least r. Each
selected row has at most three terms after substitution and projection.
Thus 3s>=2u-1+r>=2s-1+r, proving g>=r-1 and G>=N+r-2.

The inverse construction attains N+r-2 by computing the omitted endpoint
from the r-1 full endpoints and then taking all N coordinate differences.
The final re-rooting argument is valid: invertible coordinate change and
exchange of the two boundary bases preserve triples, full relation rank,
and value-set size excess. Hence the forward cyclic minimum equals this
inverse cyclic minimum. The new exact formulas and square-map ratios pass
independent review, and remain free of any universal ratio-upper-bound claim.
