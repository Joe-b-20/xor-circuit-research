# Private inputs expose the joint cost of computation and supply

2026-11-14. Unrestricted binary XOR circuits, ordinary coordinate inputs,
free fanout, and arbitrary cancellation throughout. These are hand proofs,
independently machine-reviewed in [the review](reviews/private-tagging-review.md),
not formal verification or a claim of literature novelty.

The preceding [ternary reformulation](AVAILABLE_SUPPLY.md) separates two
individually attainable minima: even rank and ternary computation. Here an
explicit family of invertible maps shows how badly their sum can underestimate
binary cost. The missing amount is exactly a graph's cycle-space dimension.
For complete graphs, every split of that amount among extra odd gates,
even-plus-even gates, and redundant pair gates is attained at the total optimum.

## 1. An exact private-input extension theorem

Let f_1,...,f_m be nonzero linear forms in coordinate inputs x. Repetitions
among the f_i are allowed. For each i take a nonempty private block Z_i of new
coordinate inputs; these blocks are pairwise disjoint and disjoint from x.
Set b_i=|Z_i|, B=sum_i b_i, and require

    t_i = f_i + XOR_{z in Z_i} z.

Then the exact binary circuit complexity is

    L_2(t_1,...,t_m) = L_2(f_1,...,f_m) + B.               (1)

**Upper bound.** Compute all f_i, then add the private inputs for target i in
b_i gates. The core computation, including its sharing, is performed once.

**Lower bound.** Take any circuit for the t_i and set the private coordinates
to zero one at a time, simplifying zero operands and rewiring copies after
each projection. Immediately before a remaining private coordinate z in Z_i
is projected, target i is f_i plus z and any other unprojected coordinates in
Z_i. It is a non-input value: f_i is nonzero on the disjoint core coordinates.

Consequently the current circuit has a gate whose value has coefficient one
in z. Choose the first such gate in its chronological order. Its operands
include the input z itself and an earlier value with z coefficient zero;
no earlier gate can have coefficient one. Projecting z to zero replaces this
gate by its other operand and removes at least one gate. This argument uses
the first coefficient-one value, not the first syntactic read, which could
be the canceling read z+z.

After each deletion the argument applies to the surviving circuit, so the
B projections delete at least B distinct gates. The remaining circuit
computes all f_i. Temporary zero values cause no difficulty: zero-producing
or zero-reading gates can be discarded or replaced by copies, with no new
gate required for these nonzero outputs. Thus G-B>=L_2(f), proving (1).

This is an unrestricted projection argument. It does not assume that a
private input stays in one branch, that it is read once, or that the circuit
avoids mixing private inputs before canceling them.

For any core map with nonzero rows, choose b_i=1 when f_i is even and b_i=2
when f_i is odd. Then every new target has odd total input parity, and (1)
gives its exact complexity in terms of the original map. Thus the all-odd
target class still contains arbitrary linear computation with an explicit
additive overhead. Odd targets alone are not a tractability condition.

This reduction can itself be made square and invertible. Order each block as
Z_i={z_{i,1},...,z_{i,b_i}}. Retain the core coordinates and the first b_i-1
private coordinates as identity outputs, and replace the last coordinate by
t_i. Applying the map twice restores every coordinate: all core and earlier
private coordinates remain fixed, and their contribution to the last one
cancels. Thus it is an involution with all rows odd and exact binary cost
L_2(f)+B. Here m<=B<=2m. Consequently even the invertible all-odd class contains
arbitrary nonzero-row linear computation with this explicit overhead.

## 2. Graph-tagged targets and an invertible version

Let H=(V,E) be any finite simple graph, with v vertices, m edges, and c connected
components, counting isolated vertices. Use one core input x_u per vertex
and one private input z_e per edge. Define

    t_e = x_u+x_w+z_e,             e={u,w}.

The m core pair sums are distinct non-input values. Computing each directly
is optimal, with exactly m gates. Equation (1) therefore gives

    L_2(T_H)=2m.                                            (2)

Every target is odd. Each is one ternary XOR of coordinate inputs, and the
m distinct non-input outputs require at least m ternary gates. Hence

    L_3(T_H)=m.                                             (3)

The square map

    S_H : (x,z) -> (x, z+B_H x),

where B_H is the edge-by-vertex incidence matrix over F_2, adds only the free
core identity outputs. It has the same complexities (2)-(3), is invertible,
and is its own inverse. All its output rows are odd. The conclusions are
therefore not an artifact of a rectangular or singular target map.

## 3. Exact minimum even rank

Write r_min for the minimum possible rank of computed even values under
total parity. The [component theorem](ODD_COMPONENT_DEFECT.md) gives this as
the coordinate count minus the largest compatible partition's part count.
For this family,

    r_min = v-c.                                           (4)

**Attainment.** Put the core vertices of each connected graph component in
one part, with every z_e in its own singleton part. Each target is even on
its core part and odd only on its private singleton, so the partition is
compatible and has rank cost v-c.

**Lower bound.** In any compatible partition let k be the number of parts
containing core vertices and let b count graph edges whose two core endpoints
lie in different parts. For each such edge, its private coordinate must lie
in one of its endpoint parts; otherwise its target would be odd on three
parts. These b distinct coordinates each reduce the potential part count by
one. The full partition therefore has at most k+(m-b) parts, so

    r >= (v+m)-(k+m-b) = v-k+b.

Contract the k core parts in the graph. This quotient has at most c connected
components, so its b cross edges satisfy b>=k-c. Therefore r>=v-c. QED.

Combining (2)-(4), the separated-minima bound misses exactly

    L_2(T_H) - (r_min+L_3(T_H)) = m-v+c = beta(H).           (5)

This is the ordinary cycle-space dimension of the specified target graph.
It is not the cycle rank of an arbitrarily chosen implementation.

## 4. A joint inequality for every unrestricted implementation

For any binary circuit for T_H or S_H, let H_o count odd gates other than
one first production of each of the m non-input targets; let d count
even-plus-even gates. Let r be its actual even rank and mu its odd-occurrence
graph cycle rank. The exact component account is

    G=m+r+H_o+d+mu.

Using the unrestricted optimum (2) yields the joint inequality

    (r-(v-c)) + H_o+d+mu >= beta(H).                        (6)

Thus the missing graph cycles cannot be erased by optimizing rank and
ternary computation separately. Their cost must appear in extra rank,
extra odd computation, even-plus-even work, or redundant pair supply.
No restriction on intermediate support, cancellation, or mixing of private
coordinates was used to obtain this statement.

## 5. Every split is sharp for a complete graph

Take H=K_q, q>=2. Let m=q(q-1)/2 and beta=m-q+1. Choose vertex 1 as a root and
compute the q-1 even star pairs p_i=x_1+x_i. For a star edge, produce its
target by adding its private z_e to p_i.

For each nonstar edge {i,j}, independently select one of three implementations:

- **Extra odd work:** compute z_e+p_i, then add p_j. This uses one odd helper
  and the target gate, and contributes one unit to H_o.
- **Even combination:** compute p_i+p_j, then add z_e. This uses one
  even-plus-even gate and the target gate, and contributes one unit to d.
- **Redundant pair supply:** compute x_i+x_j directly, then add z_e. Its
  pair joins core vertices already connected by the star and contributes
  one unit to mu.

Each option takes exactly two gates. The total is

    (q-1) + (q-1) + 2 beta = 2m,

with r=q-1. Every triple of nonnegative integers

    H_o+d+mu=beta                                           (7)

is attained by these choices. This is a full simplex of total-cost optima,
not merely three endpoint examples.

Writing k for odd-plus-odd gates and P=O+d for the ternary resource, the exact
discrete Pareto frontier is also explicit:

    (k,P)=(K,2m-K),       q-1<=K<=m, K integral.             (8)

Every circuit has k>=r_min=q-1, P>=m, and k+P=G>=2m. The construction realizes
all pairs in (8), for example by choosing mu=K-q+1 and H_o+d=m-K. These
inequalities also show that every other feasible pair is dominated by one
of the displayed pairs.

In particular, minimizing P forces k>=m, while minimizing k forces
P>=2m-q+1. The two independent minima q-1 and m are incompatible when q>=3.
The ratio of true binary cost to their sum is

    2m/(m+q-1) = 2q/(q+2),

which approaches two. This is a property of this explicit family, not a
universal upper bound on that ratio.

## 6. Research consequence and limits

Private-input projection preserves the entire core complexity, including
all sharing, while forcing a precise additional cost. For graph pairs it
turns that cost into a completely explicit joint resource law. The complete
graph exhibits how three physically different mechanisms can exchange cost
without changing the optimum.

This resolves two distinct questions. The sum r_min+L_3 can undercount binary
cost by an unbounded amount, even for invertible all-odd maps. Separately, the
minimum physical pair count k and minimum ternary resource P cannot be jointly
attained in this family when beta>0. Do not confuse this with incompatibility
of minimum rank r and minimum P: the direct-pair construction attains both of
those simultaneously, while paying mu=beta. Rank counts independent supply,
whereas k=r+mu also counts the redundant pairs that are physically needed.
It does not supply a new MixColumns bound. MixColumns has no such private
coordinate attached to each output; exporting (6) requires a new argument
that finds an analogous jointly forced cost despite its overlapping columns.
Unrestricted MixColumns remains 75<=L<=88.

The companion [tree rigidity theorem](TREE_INTERSECTION_RIGIDITY.md) shows a
different phenomenon: some maps force even-plus-even work at every total
optimum, and eliminating it can cost an unbounded number of gates. The
[single-target Pareto theorem](SINGLE_TARGET_PARETO.md) explains why this
joint sharing issue cannot be resolved by studying one output in isolation.

The [specified checker](checks/check_joint_supply.py) verifies the displayed
K_5 construction with H_o=d=mu=2, r=4, and G=20, including all target masks,
full rank of its square map, and the identity obtained by applying it twice.
The [saved result](checks/joint-supply-result.json) checks one chosen split;
the hand proof, not enumeration, establishes all splits and all parameters.
