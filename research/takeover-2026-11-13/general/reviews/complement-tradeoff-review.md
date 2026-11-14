# Independent review: complement sums and their cost tradeoff

2026-11-14. Independent machine review of
[COMPLEMENT_TRADEOFF.md](../COMPLEMENT_TRADEOFF.md). I checked the complete
saved hand proof and symbolic construction. No circuit search or enumeration
was used; this is not formal verification or a literature-novelty claim.

## Exact ancestor accounting

The complete ancestor cone of a nonzero value is connected and has g+t
physical vertices and 2g operand edges, including parallel edges when an
operand is repeated. Thus its undirected cycle rank is beta=g-t+1 and
g=(w-1)+(t-w)+beta. Every supported input is an ancestor, so both extra terms
are nonnegative. A tree cone has no repeated use: every non-root occurrence
has one outgoing use within the cone. Its leaves are distinct coordinate
inputs, so child supports are disjoint and all node supports are laminar.

Choosing the earliest required non-input target ensures that the other
target first occurrences lie outside its cone. The exact alpha term counts
every additional outside occurrence, including gates before the chosen
target that are not its ancestors. No disjoint-output-cone assumption enters.

## The unrestricted lower bound

For n>=4, assuming total 2n-3 forces the first target cone to be a tree on
exactly n-1 inputs and all outside gates to be other required targets.
The first later target containing the missing input x_i must use that input
and a cone value of support n-2. Laminarity permits at most one such value,
and it must be a root child with the omitted singleton x_j as its sibling.

At the next target, the only available x_i-bearing values are x_i and the
first later target y_j. Their possible partners would respectively be a
second (n-2)-support cone value or the pair x_j+x_l. The first does not exist;
the second crosses the forced root split and is not a cone node. The pair
is not an input either. Using both x_i-bearing values cancels x_i. Therefore
the next target is impossible, ruling out equality and proving 2n-2.

The specified construction attains 2n-2 and pays for its shared full sum J.
The exclusions n=2 and n=3 are necessary and correctly stated.

## Compatible partitions and the sharp interpolation

For n=2k, every required target is odd. In a compatible partition let p
record the parity of the part sizes. Each p+e_a must be a unit. Since p has
even weight, c>=3 forces p=0 and hence every part even. At c=2 both parts
may instead be odd; this exception was raised during review and is correctly
handled by the saved proof. In either case c<=k for k>=2.

Combining the proved total lower bound with the exact physical decomposition
G=n+H+n-c+delta gives H+delta>=c-2, equivalently
H+(k-c)+delta>=k-2. This applies to every circuit and counts the same gates
only once. It is not an assumption of independent even helpers.

In the construction, the k-1 disjoint pair values and J are independent,
while the j aggregate even values are in their span. Their count is E=k+j,
their rank k, and their defect j. The odd accumulation creates k-j-2 helper
values before its first required target. All later odd gates produce the
remaining targets. Consequently H=k-2-j, c=k, delta=j and total 2n-2 for
every 0<=j<=k-2. The odd graph remains a forest; the defect is exactly the
j even-plus-even gates. Every claimed split is therefore attained physically.

## Conclusion

The theorem and its full interpolation pass review. They give an exact
unrestricted family in which odd auxiliary work and dependent even work
exchange while total optimum stays fixed. The final scope correctly refuses
to sum such bounds across overlapping target families without accounting
for shared supply, and claims no new MixColumns bound.

## Strengthening by the weighted first-target theorem

The subsequent [general theorem](../FIRST_ODD_TARGET_TRADEOFF.md), independently
reviewed in [its own record](first-odd-target-review.md), strengthens the
complement statement to H+d>=k-2 for every circuit, regardless of c. Combining
it with G=n+H+r+d+mu and r>=k yields the same exact optimum directly for even
n. At that optimum, all inequalities are tight: r=k, c=k, mu=0, and
H+d=H+delta=k-2. Thus minimum even rank and absence of odd-graph cycles are
necessary for every optimum, not merely properties of the displayed family.
The earlier laminar-cone proof still establishes the formula for odd n.
