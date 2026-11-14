# Independent review: tree intersections and even aggregation

2026-11-14. Independent machine review of the complete
[TREE_INTERSECTION_RIGIDITY.md](../TREE_INTERSECTION_RIGIDITY.md). I reconstructed
the graph equalities, intersection argument, rigidity claims, and scalable
tradeoff symbolically. No circuit search, enumeration, or computer-driven case
elimination was used. This is not formal verification, human certification, or
a literature-novelty assessment.

## General equality theorem

For the pruned full ancestor graph every retained gate has two operand ports.
With a actual coordinate ancestors and g gates, the undirected multigraph has
2g edges and a+g vertices, giving g=a-c+beta. The note correctly distinguishes
a from the n supported input coordinates: additional ancestors may cancel, so
only a>=n is automatic. Target support overlap implies cone overlap and hence
c<=kappa. Equality G=n-kappa forces no discarded gates, a=n, c=kappa, and no
undirected cycles.

In a tree there is at most one path from any input to a node. Thus its coefficient
cannot cancel, and the two parents of each gate have disjoint nonempty supports.
For two nodes with a common input, the unique path between them has a uniquely
determined branching point w. Every common input reaches w, and every input
reaching w reaches both nodes. This proves that their support intersection is
the support of an actual physical node. Iteration proves the finite-intersection
claim; it is stronger than mere span membership.

The componentwise version is valid without global optimality. Complete ancestor
cones cover a pruned component, and an edge between two cones puts its parent
in both. Therefore a connected component has a connected cone-overlap graph.
In a tree any common node has a nonempty support, so cone overlap implies target
support overlap. This verifies the third statement, which is essential to the
scalable lower bound.

## Three-supplier construction and all optimal circuits

With two or more private targets for each of the three supplier supports,
intersections force e=a+b, f=c+d, and h=a+b+c+d as actual values in any tree
implementation. The M target values and these three distinct non-input values
exhaust the M+3 gates at equality. Private coordinates cannot cancel in a tree,
so a target cannot supply an operand of an even supplier. A weight-four supplier
cannot come from two coordinate inputs. Its parents must therefore be e and f,
forcing exactly one even-plus-even gate. The leaf suppliers and each final
private-target attachment are forced as stated.

The alternative e=a+b, f=c+d, t=a+f, h=t+b has no even-plus-even gate and uses
one extra gate. Its effective even rank is two, its odd-graph cycle rank one,
and O+d agrees with that of the optimum. These are correct construction counts;
they are not incorrectly promoted to claims about every nonoptimal circuit.

## Scalable tradeoff without a direct-sum assumption

Each support-connected copy is contained in one actual physical component.
By the tree-component overlap result, a tree component contains exactly one
copy. Its complete input support then forces exactly N_i-1 gates, allowing the
preceding rigidity argument to be applied. Consequently every such component
contains an even-plus-even gate, so t<=d'. Every remaining component contributes
at least one full undirected cycle. Therefore

    G>=g=N-c+beta>=N-t>=N-d'>=N-d.

Together with G>=N-b, this gives the claimed unrestricted tradeoff. Cross-copy
sharing and cancellation are not excluded; their actual graph components and
cycles remain in the count. Combining the two explicit implementations attains
G=N-j,d=j for every integer 0<=j<=b. The allowance formula is exact for
nonnegative integer D; I asked the author to state that integer condition
explicitly. This is a parameter-domain clarification, not a mathematical gap.

## Connected hierarchy and scope

The duplicated private attachments force every hierarchy-node supplier by the
same tree intersection theorem. Their count and the output count exhaust the
optimal gate budget. A supplier cannot use a private target. Two disjoint proper
node supports can cover an internal node support only when they are its two
children, so the even hierarchy wiring is forced. Each output must add its own
private coordinate to its prescribed supplier. The asserted O,E,d,r,mu counts
follow, including r=q from the independent leaf pairs and mu=0.

The note keeps the two conclusions distinct: arbitrarily many even aggregations
are forced in the connected optimum, while the disjoint-copy family proves an
unbounded additive cost of removing them after unrestricted rewiring. It does
not assume a direct-sum theorem or claim a new MixColumns lower bound. The main
structural statements and the limits of their use pass this review.
