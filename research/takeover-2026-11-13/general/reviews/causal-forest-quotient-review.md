# Independent review: causal forest quotient and simultaneous repair

2026-11-14. Independent machine review of the complete
[CAUSAL_FOREST_QUOTIENT.md](../CAUSAL_FOREST_QUOTIENT.md). I reconstructed the
forest transformation, causal kernel basis, specified family, and both exact
complexity arguments. No enumeration, circuit search, or computer-driven case
elimination was used. This is not formal verification, human certification, or
a literature-novelty assessment.

## Exact forest representation

With both operand ports retained, the full ancestor multigraph has 2g edges
and a+g vertices, so its cycle rank is g-a+c. Cutting precisely the edges
outside a spanning forest and replacing each read by its own fresh input
leaves a literal forest with the same components and gate occurrences.
Repeated operand ports are separate edges; parallel reads cause no exception.

Projection of each new input to its original source value reconstructs every
gate by chronological induction. The original coordinate inputs remain fixed,
so the projection has full rank a and kernel dimension beta. For a cut read
at gate v_l, its formal source U_l can depend only on shadows introduced at
earlier reader gates. The relations s_l+U_l are therefore triangular and
independent. If several cut reads enter one gate, none of their source values
can depend on those same-gate shadows, so arbitrary tie ordering is harmless.
These beta relations form the complete kernel.

Cutting a read may leave its old source outside the original output cones.
The optional designation of cut sources as extra formal outputs correctly
restores a full ancestor-union presentation without changing any counts.
The note does not confuse these formal inputs with freely supplied physical
values or assume that coordinatewise intersection commutes with projection.

## The one-cycle family

The specified pair and prefix construction has 2m+2 inputs and 2m+2 gates,
and its ancestor graph is connected, giving beta=1. Its target p_j has
support r together with the first j input pairs, while q has all pairs and
the separate input z. Their intersection is exactly c_j, the first j pairs.
For j>=2 this even value has weight at least four and is neither an input
nor one of the computed weight-two even values; every other computed value
is odd. Thus all stated intersections are physically absent. Their linear
independence follows by considering the largest prefix index in any nonempty
combination.

Each missing c_j equals the already available p_j+r, so its remaining
individual cost is exactly one. Adding identity outputs r,b_1,...,b_m gives
a square map, and the displayed inverse recovers every coordinate. All its
rows are odd. No involution claim is made for this family.

## Exact optimality and global repair cost

The cloning lemma is valid for any active input column. In an expanded map,
every output containing the new clone y also contains the retained x. Thus
some non-input target depends on y. The first current gate with coefficient
one in y directly reads y and a coefficient-zero value. Projecting y to zero
deletes that gate. Sequential clone projections act on the surviving circuit,
so they remove distinct gates. The original coordinates remain, preserving
the premise at every step. Computing each x+y first supplies the matching
upper bound. Arbitrary mixing and cancellation were not excluded.

Before cloning, projecting the private z leaves the m+1 distinct non-input
targets P_1,...,P_m,A_m for m>=2. Their output count gives the stated m+2
lower bound before projection, and the displayed prefix construction attains
it. Cloning all m active columns therefore gives the exact original cost
2m+2. The one-cycle example is an optimal implementation.

When all A_j are required as well, projection leaves 2m-1 distinct non-input
targets: m values P_j and m-1 prefixes A_j with j>=2. Computing the A-prefixes,
attaching r to each, and attaching z to the last attains the matching total
2m before cloning. The exact cloned cost is consequently 3m. Omitting c_1
from the extra required set changes nothing: its uncloned counterpart A_1
is already an input, and the same cloning argument applies.

Thus the extra optimal cost m-2 is exact even after unrestricted rewiring.
It does not assert that appending one gate per absent intersection to the
specified circuit is optimal. It correctly distinguishes individual cheap
repair from the cost of requiring all repaired values simultaneously.

The complete note passes review. Its unbounded missing-intersection count,
independent rank, and simultaneous repair gap are all compatible with the
positive bound on representing one intersection from actual available values.
The unrestricted scope and unchanged MixColumns interval are accurately stated.
