# Independent review of RELATIONS.md

2026-11-13. Review by the structural-direction agent, independent of the author. Hand proof audit only; no search, enumeration, finite-family computation, or exact circuit optimization. This is machine review, not human certification or formal verification.

## Verdict

The general counting bound, its even-span refinement, the exact graph formula for formal relation rank, the coset-capacity bounds, the origin constraint, and the no-odd-helper corollary are correct under the stated reduced-circuit hypotheses. No repair is required.

The distinction between physical nonfree even gates and available free even masks is maintained throughout. The results constrain a given circuit; they do not claim a new unrestricted MixColumns bound or a general two-sheet lower bound of 22.

## Counting and even-only capacity

Every non-entry gate has either one even and two odd nodes in its unordered three-node relation or three physical even nodes. Ordinary coordinate inputs are odd, and a free operand makes the gate an entry, so there are no omitted even-input sources in this classification.

In a reduced circuit, a relation's three values identify three distinct nodes. Its latest node in topological order is the only possible result, so the same unordered relation cannot account for two physical gates. This justifies the initial pair-plus-triple bound.

For the refinement, let the even gates produced by means other than even-plus-even be the generating set. Induction over gate order puts every physical even value in their span. At least `d_H` such generators are necessary. Therefore at most `e-d_H` even-only gates can occur, independently of the count `T(H)` of available even-only relations. Taking their minimum gives equation (1).

## Exact formal-rank formula

The physical equations of selected non-entry gates are independent as formal node-coordinate vectors. In any nonempty sum of these equations, choose the latest result node among the selected gates. It occurs in its own row and cannot occur in another selected row, since all their result nodes are earlier and operands precede their results. This proves the triangular independence used to bound `G-tau` by the rank of all available relations.

For the graph formula, the span of available odd-pair and even-only relations is

    R = { (partial x, chi x + z) : x in F_2^edges, z in Z }.

Projection onto odd coordinates has image `im partial`, of dimension `|O|-c_O`, including the stated convention for isolated vertices. Its kernel is exactly

    {0} direct-sum (chi(ker partial)+Z).

Rank-nullity therefore gives equation (3) exactly. It is not merely an upper bound.

Evaluation of a cycle-colour vector is zero because every odd endpoint appears an even number of times. Evaluation of an even-only triple relation is zero by its definition. Thus `Z+chi(ker partial)` is contained in the kernel of the even-value evaluation map, whose dimension is `e-d_H`. This proves the resulting upper bound.

For a four-cycle with alternating colours, its four formal relation rows sum to zero. No proper nonempty subset has zero incidence, so those four rows have rank three. Additional edges elsewhere do not change this dependence among the four selected rows.

## Coset-capacity bounds

The eight named values occupy the eight odd residues exactly once and have no relation of weight four or less. Consequently a fixed nonzero value has at most one named-pair representation.

For a fixed physical even value, translation is a matching on the actual odd-value set. At zero residue, each edge stays in one residue class, giving the floor-of-half-population bound. At nonzero residue, matching between a paired pair of residue classes uses at most the smaller population. Independently, all but at most one named-pair edge use a helper, and the matching can use each helper at most once. Taking the minimum of these two bounds is valid.

For the collective clean bound, pairs with sum in `H_0` must lie in one affine coset of `D_0=span(H_0)`. Each unordered pair has only one actual sum and is therefore counted at most once across the clean even values. In each residue class there is both the `k`-matchings bound and the sum-of-binomial-coefficients bound. The minimum may be taken separately in each class before summing, exactly as equation (2) does.

The compact inequality follows by bounding each clean matching by `A` and each nonclean matching by `A+1`, then using `e-d_H` for even-only gates. No free clean direction is counted as a physical gate in these arguments.

## Origin constraint and named-group rank

An odd non-entry gate adds a physical even value, so it cannot change its odd predecessor's affine coset modulo the physical even span `V`. Therefore a required odd-output coset without an ordinary input needs an odd entry to introduce its first odd node. This reasoning uses chronology and does not assume every vector of `V` is physically available.

For the named-group bound, the direct sum of the even coefficient spaces on the occupied groups has dimension `8-m`. Its image consists of within-group differences and lies in `V`. The evaluation kernel on the eight named coordinates is exactly the all-ones relation. That relation lies in the coefficient subspace precisely when every group has even size. Subtracting this possible one-dimensional intersection gives the stated lower bound on `d_H`.

## No odd helper

When there are no odd non-output gates, an output's ordinary triple projection has not occurred at any earlier odd node. It therefore cannot be an entry. Each of the four outputs uses a physical even value joining its named odd operand and result.

The four output gates require four different even values: one named pair can be used only once as a gate relation, and two distinct named pairs have different sums. Their residues are nonzero because all named residues are distinct. Of the six even physical gates in a ten-gate circuit, at most two can consequently be clean. This is a physical-value count in the specified class; the proof does not extend it to arbitrary helper populations.

## Scope

The graph formula uses all available formal relations on physical node values; an actual circuit realizes an independent subset of them. It is therefore legitimate for the available relation graph to contain cycles or dependencies. The conclusions neither assume all available relations are executed nor infer realizability merely from satisfying the rank bound.
