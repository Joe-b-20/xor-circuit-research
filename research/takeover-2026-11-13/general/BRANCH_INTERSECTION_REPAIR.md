# Physical branch values control intersection repair

2026-11-14. General hand proofs for unrestricted binary XOR circuits, with
ordinary coordinate inputs and free fanout. Arbitrary cancellations, repeated
operands, zero values, and duplicate occurrences are allowed. Independent
machine review is recorded in [the review](reviews/branch-intersection-review.md);
this is not formal verification or a literature-novelty claim.

The [forest equality theorem](TREE_INTERSECTION_RIGIDITY.md) says that an
intersection of two physical supports is itself physically available in a tree.
Here is a quantitative extension to every circuit: an intersection can be
assembled from at most beta+1 already available values, where beta counts cycles
in the union of the two ancestor cones. This is sharp at every beta. A common
dictionary of branch values handles all Boolean functions of the output-column
patterns, but its rank alone collapses to a much weaker transposition bound.

## 1. The physical graph and its branch budget

Select k>=1 output ports at specified value occurrences in a circuit. Ports
may coincide or lie at ancestors of other selected ports. Keep the complete
union of their ancestor cones, including both operand ports of every gate.
Let a,g,c be its numbers of coordinate input ancestors, gates, and undirected
components. Parallel operand edges are retained. Its undirected cycle rank is

    beta = g-a+c.

This is the FULL ancestor graph's cycle rank, not the parity-based odd-occurrence
cycle rank mu used in [even-rank accounting](ODD_COMPONENT_DEFECT.md).

For each ordinary occurrence v let d_v count its gate-reader operand ports plus
its selected terminal ports. Every retained occurrence has d_v>=1. There are
2g gate-operand reads and k terminal reads in total, so

    sum_v (d_v-1) = (2g+k)-(a+g) = beta+k-c.              (1)

Let B be the set of occurrences with d_v>=2. These are actual branch values,
including input occurrences when an input is shared. Consequently

    |B| <= beta+k-c.                                    (2)

This counts occurrences, not distinct masks. Equal masks remain separate
physical branch points, though they may cancel in a representation below.

## 2. An exact boundary identity

Write a_v for the ordinary input mask at occurrence v. Let eta_v in F_2^k
record the parities of paths from that occurrence to the k selected ports,
including trivial paths. Reverse recursion gives

    eta_v = sum_(gate-reader ports v->h) eta_h
              + sum_(terminal ports j at v) e_j.         (3)

Each operand port is counted, so two reads by the same gate cancel in (3).
For a function phi:F_2^k->F_2 with phi(0)=0, put

    Delta_v(phi) = phi(eta_v)
                    + sum_(gate-reader ports v->h) phi(eta_h)
                    + sum_(terminal ports j at v) phi(e_j).

If d_v=1, its single reader has the same eta as v, or is its unique terminal;
in either case Delta_v=0. The following equality uses actual available values:

    sum_(v in B) Delta_v(phi) a_v
      = sum_(input i) phi(eta_i) e_i
          + sum_(selected j) phi(e_j) r_j,               (4)

where r_j is the selected output mask.

**Proof.** Sum a_v Delta_v over all retained occurrences. For each gate h, the
terms multiplying phi(eta_h) have coefficient a_h plus its two parent masks,
which is zero. Only input terms and the terminal contributions remain. Nodes
outside B have zero Delta. This proves (4), including cancellations and repeated
ports. No span element is substituted for a physical operand. QED.

For normalized phi satisfying also phi(e_j)=0, the right side is the coordinate
vector obtained by applying phi to each input's output-incidence pattern. Every
such vector is therefore represented using the SAME branch dictionary B;
only its coefficients Delta_v(phi) vary with phi. This simultaneous statement
does not give those different sums as free, separately available outputs.

## 3. A sharp pair-intersection theorem

For k=2 choose phi(s,t)=st. Let u,v be the selected ordinary values. Equation
(4) becomes

    u elementwise-product v
      = sum_(w in B) Delta_w(phi) a_w.                   (5)

The elementwise product is the XOR mask of the support intersection. If the
cones are connected, (2) gives at most beta+1 terms. If they are disconnected,
the intersection is zero, since their coordinate ancestors are disjoint. Thus
for the dictionary S of values actually available once both ports are reached,

    ell_S(u elementwise-product v) <= beta+1,             (6)

with ell_S(0)=0. Here ell is minimum unweighted XOR representation length in
the actual dictionary. The bound remains valid using the whole circuit's cycle
rank, because cycle rank cannot decrease when this subgraph is enlarged.

For distinct selected occurrences, every branch in their cone union precedes
the later occurrence: that last occurrence has no retained gate reader and
only one selected terminal. Thus (5) uses values available even before the
later selected result. If the ports coincide, the intersection is already the
same available value; no strict timing claim is needed.

When the intersection is nonzero, its exact remaining single-target binary
cost is ell_S-1 by [the dictionary theorem](SINGLE_TARGET_PARETO.md). Therefore
it can be made physically available with at most beta additional XOR gates.
For beta=0 it is already available, recovering forest intersection rigidity.
The zero vector requires no support repair; no extra zero-output convention
is being asserted by this statement.

### Sharpness at every cycle rank

Fix t>=1. Take independent coordinate inputs c_i,a_i,b_i for 1<=i<=t and
two additional anchors x,y. Compute

    A_i=c_i+a_i,       B_i=c_i+b_i,
    U=x+sum_i A_i,     V=y+sum_i B_i,

using one chain to sum the A_i and one to sum the B_i. There are 2t pair gates,
2(t-1) chain gates, and two final anchor additions. The two-output ancestor
union is connected, with

    g=4t,       a=3t+2,       beta=t-1.

Its support intersection is C=sum_i c_i. Define a linear map F to F_2^t by
F(c_i)=F(a_i)=F(b_i)=e_i and F(x)=F(y)=0. Every computed value maps to zero;
each supplied input maps either to zero or to one coordinate vector. Since
F(C) is the all-ones vector, any representation of C from the actual dictionary
needs at least t terms. The t inputs c_i attain this. Hence

    ell_S(C)=t=beta+1,

and exactly beta appended XOR gates are necessary to supply C. This quotient
argument proves the lower bound without searching representations. The displayed
two-output circuit need not be optimal for those two outputs; it establishes
sharpness of the theorem for arbitrary circuits.

Sharpness can also occur in an optimal all-odd invertible circuit. Let E be
the 4t-2 distinct even values produced before U,V. Give each h in E its own
new input s_h and required output h+s_h. Keep U,V and all 3t core coordinate
identity outputs. This is a square all-odd involution on 7t inputs: the core
coordinates are fixed and every other coordinate receives a fixed core sum.
The displayed circuit uses 8t-2 gates and still has beta=t-1, since each private
attachment adds one input, one gate, and two edges. Projecting all s_h to zero
deletes at least 4t-2 gates and leaves the 4t distinct non-input values E,U,V
as required outputs. Therefore 8t-2 gates are necessary. Extending F by
F(s_h)=0 preserves the representation lower bound ell_S(C)=t. This uses the
[private-input projection theorem](PRIVATE_TAGGING_TRADEOFF.md), not an
optimal-circuit search. It asserts the cost of appending C to this dictionary,
not the optimum after freely rewiring the enlarged target problem.

## 4. What all Boolean functions give, and what their rank loses

The common physical dictionary in (4) is more informative than independent
representations chosen for different intersections. However, forgetting its
actual values and keeping only the dimension of the boundary vectors loses
nearly all that information.

For the k selected rows, let p be the number of DISTINCT occurring input-column
patterns whose Hamming weight is at least two. With phi(0)=phi(e_j)=0, the
vectors on the right of (4) range over exactly the span of the p indicator masks
of those column-pattern classes. Indeed an arbitrary phi chooses one bit for
each such pattern, and their disjoint nonempty classes give independent masks.
Therefore their exact span dimension is p, and (2) yields

    p <= |B| <= beta+k-c,       g >= a+p-k.                (7)

If n coordinates occur in the selected rows, a>=n gives the target-only bound
G>=n+p-k. This is the familiar count obtained by transposing a circuit and
counting its distinct non-input targets; (4) supplies a physical branch-value
interpretation. No novelty claim is made for (7).

Allowing arbitrary phi instead of normalized phi does not enlarge the boundary
span when the correction term in (4) is retained. For phi supported on a unit
pattern e_j, that boundary is its class indicator plus row j, which is the sum
of the nonunit class indicators having coordinate j equal to one. Linear phi
have zero boundary altogether. Thus adding higher-degree Boolean functions
cannot improve a certificate that retains ONLY this boundary-space rank.

For at most 32 supported coordinates and any k selected rows,

    n+p-k <= 32+min(32, 2^k-k-1)-k <= 58.                (8)

For 1<=k<=5 the maximum on that range is 53 (the k=1,2 values are 31);
for k>=6 the expression is at most 64-k<=58. Thus even maximizing this
rank-only certificate over arbitrary subsets of MixColumns rows cannot reach
75. This is a limitation of that certificate, not a bound on the circuit or
on arguments retaining the constrained coefficients and actual branch values.
No subsets are enumerated in this ceiling proof.

## 5. Local repair does not imply cheap simultaneous repair

The [causal forest quotient and one-cycle family](CAUSAL_FOREST_QUOTIENT.md)
give an exact counterweight to (6). There are optimal all-odd invertible circuits
with full cycle rank one that omit arbitrarily many independent intersections.
Each missing value needs just one additional XOR from the existing dictionary,
consistent with this theorem. Requiring all of them at once can nevertheless
raise optimal total cost by an unbounded amount, even after complete rewiring.

Accordingly (6) is a local availability theorem. It does not charge each missing
intersection one independent cycle, give all intersections for beta gates, or
turn simultaneous spans into free values. A useful next invariant must retain
the common branch dictionary together with the cost of forming its several
different combinations. Unrestricted MixColumns remains 75<=L<=88.

The [specified checker](checks/check_intersection_repair.py) evaluates one
one-cycle representation with two terms and the t=3 sharp optimal involution
with a three-term representation. It verifies the block-quotient certificate,
all target masks, and the square involution. The
[saved result](checks/intersection-repair-result.json) checks these constructions
without searching circuits or representations; the all-parameter conclusions
come from the hand proofs.
