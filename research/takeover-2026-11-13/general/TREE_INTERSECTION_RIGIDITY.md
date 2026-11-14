# Tree rigidity and the unavoidable joint cost of even aggregation

2026-11-14. Structural hand proofs for unrestricted binary XOR circuits. No
circuit search, enumeration, or computer-driven elimination is used. An
[independent machine review](reviews/tree-intersection-review.md) is saved; this
is not formal verification or human certification. No literature-novelty claim
is made.

The [ternary normal form](AVAILABLE_SUPPLY.md) preserves the combined resource
O+d, where O counts odd gates and d counts even-plus-even gates under total input
parity. It does not preserve total binary cost. This note proves a concrete
reason: eliminating even aggregation can force extra physical work, even when
the combined ternary resource stays unchanged in the displayed constructions.

The main result is an exact scalable tradeoff. There are explicit target maps
on N inputs, assembled from b disjoint pieces, such that every unrestricted
circuit satisfies

    G >= N-b,                 G+d >= N.                         (1)

Both inequalities are jointly sharp. For each 0<=j<=b there is a circuit with

    d=j,                      G=N-j.                           (2)

In particular, the unrestricted optimum is N-b, while eliminating all
even-plus-even gates costs exactly b additional gates. This is an obstruction
to a proposed unrestricted normal-form reduction, not a new fixed-budget case
classification. The proof charges actual connected components and actual cycles;
it does not assume a general direct-sum theorem for XOR complexity.

## 1. Full ancestor graphs and a general equality theorem

Let T be a collection of nonzero target vectors on ordinary coordinate inputs.
Let n be the number of input coordinates in the union of their supports. Define
the support-overlap graph of T by joining two targets when their input supports
intersect. Let kappa be its component count.

For a circuit computing T, retain the complete union of the targets' ancestor
cones. Every retained gate keeps both operand ports. Let g be its gate count,
c its undirected component count, and beta its undirected cycle rank, counting
parallel operand edges separately. Let a be the number of distinct input
ancestors. All n supported inputs occur, so a>=n; additional input coordinates
may occur and cancel. The graph has a+g vertices and 2g edges, so

    beta=g-a+c,              g=a-c+beta.                       (3)

Each cone is connected. Two targets with intersecting supports have a common
input ancestor, so their cones meet. Therefore c<=kappa and

    G >= g >= n-kappa.                                         (4)

Here G is the original circuit size before any pruning. These observations
allow arbitrary cancellation, fanout, repeated operands, zero values, and
duplicate values.

**Tree equality theorem.** If G=n-kappa, the circuit has no discarded gate,
a=n, c=kappa, and every undirected ancestor component is a tree. In a tree component:

1. Every gate combines disjoint, nonempty input supports. In particular, there
   is no cancellation anywhere in that component.
2. For any two physical values with nonempty support intersection, their
   intersection is itself the support of a physical value in that component.
   The same holds for every nonempty finite intersection.
3. The required targets belonging to that physical component have a connected
   support-overlap graph.

**Proof of the equality conditions.** Equation (3) and c<=kappa give
G>=g>=n-kappa. Equality forces G=g, a=n, c=kappa, and beta=0. A multigraph with cycle
rank zero is a forest. Repeated operand ports would make a parallel-edge cycle,
so they cannot occur in an equality component.

**Proof of statement 1.** There is at most one undirected path from an input to
any node in a tree, hence at most one directed path. An input has coefficient
one in a node's value exactly when that input is its ancestor. The supports of
a gate's two parents are disjoint: a shared input would give two different
paths to the gate. Parent supports are nonempty, by induction from coordinate
inputs. Every gate therefore forms their disjoint union.

**Proof of statement 2.** Let u and v have a common input ancestor. Their unique
undirected connecting path consists of two directed paths starting at a single
node w and ending at u and v; one path can have length zero. To see this, follow
the two directed paths from any common input and take their last common node.
The orientation of the unique u-v path determines this branching node uniquely.
Every common ancestor of u and v must consequently be an ancestor of w, and
every ancestor of w is a common ancestor. Thus

    Anc(u) intersect Anc(v) = Anc(w),
    supp(u) intersect supp(v) = supp(w).                        (5)

The support equality uses statement 1. Iterating the pairwise statement proves
the finite-intersection version. This concerns an actually present node w,
not merely a vector in the span of available values.

**Proof of statement 3.** Every node in the pruned component belongs to some
required target's cone. A connected union of those cones has a connected cone-
intersection graph: otherwise the unions belonging to its different graph
components would be disjoint and have no edge between them. Any edge between
two cones has its parent endpoint in both cones. When two cones intersect,
any node in their intersection has a nonempty input support by statement 1,
so the corresponding target supports intersect. The target support-overlap
graph is therefore connected. QED.

Statements 1-3 apply to any individual tree component of a pruned circuit,
even if other components have cycles or the whole circuit is not optimal.
This componentwise version is what makes the scalable tradeoff below work.

## 2. A three-supplier pattern

Take four base coordinate inputs a,b,c,d and private coordinate inputs

    x_1,...,x_p,    y_1,...,y_q,    z_1,...,z_r,

where p,q,r>=2. All coordinates are distinct. Put M=p+q+r and N_0=M+4. The
required targets are

    X_i=a+b+x_i,
    Y_j=c+d+y_j,
    Z_k=a+b+c+d+z_k.                                           (6)

Every target is odd under total input parity. Write

    e=a+b,             f=c+d,             h=e+f.                (7)

Computing e,f,h and adding the corresponding private input to each target
uses M+3=N_0-1 gates. The target support-overlap graph is connected: every
X target meets every Z target in {a,b}, and every Y target meets every Z target
in {c,d}. All N_0 inputs occur. Equation (4) therefore proves

    L_2(T)=N_0-1=M+3.                                          (8)

**Rigidity of every optimum.** Every optimum has a tree ancestor graph. Since
there are at least two targets of each type, their intersections force the
physical values

    supp(X_1) intersect supp(X_2) = {a,b},
    supp(Y_1) intersect supp(Y_2) = {c,d},
    supp(Z_1) intersect supp(Z_2) = {a,b,c,d}.                    (9)

Thus e,f,h are actual gate values. Together with the M distinct target values,
these account for all M+3 gates. There is no additional odd helper. All three
supplier values are even.

The gate producing h cannot read a target: each target contains its own private
coordinate, which cannot cancel in a tree component. Its only possible earlier
odd operands are coordinate inputs, and two coordinates cannot produce a
weight-four value. Its parents must therefore be the two even values e and f.
Every optimum has exactly one even-plus-even gate, namely h=e+f. The remaining
supplier gates are e=a+b and f=c+d; every target gate adds its private coordinate
to the appropriate supplier.

Consequently no optimum is free of even-plus-even gates. Conversely, the four
supplier/helper gates

    e=a+b,             f=c+d,
    t=a+f,             h=t+b                                   (10)

compute the same suppliers with no even-plus-even gate. Adding the M target
gates gives M+4=N_0 gates. Hence eliminating even-plus-even gates costs exactly
one additional gate for this whole target family, allowing complete rewiring
and arbitrary cancellations in the competing circuit.

The two displayed circuits have the same O+d=M+1. In (7), r=2,d=1,mu=0. In (10),
r=2,d=0,mu=1, with one additional odd helper t. Here r and mu are the effective
even rank and odd-occurrence graph cycle rank from the
[general parity account](ODD_COMPONENT_DEFECT.md). The identity
G=r+(O+d)+mu identifies the extra cost: the displayed replacement keeps the
combined ternary resource unchanged and pays for a cycle-closing even supplier.
This is an observation about these constructions, not an assertion that every
replacement has the same individual gate populations.

## 3. An exact scalable unrestricted tradeoff

Take b>=1 disjoint copies of the target pattern (6). Private multiplicities
may differ between copies, but each of their three types has at least two
outputs. Let N be the total number of coordinate inputs. The target support-
overlap graph has exactly b components, one per copy. The independent circuits
(7) show that N-b gates suffice, and (4) proves their optimality:

    L_2(T)=N-b.                                                (11)

Now consider any unrestricted circuit for this combined target map and use
total input parity. Let d count its even-plus-even gates. Prune to the target
ancestor union. Write g for the retained gate count, d'<=d for its retained
even-plus-even gates, c for its physical component count, and beta for its
full undirected cycle rank.

Each original copy is entirely contained in one physical component: its target
support-overlap graph is connected and its target supports cover all of its
inputs. A physical component can contain several copies if the circuit chooses
to mix them.

Let t be the number of physical components that are trees. By statement 3 of
the tree equality theorem, a tree component has a connected target support-
overlap graph. It therefore contains exactly one original copy, not several.
By the rigidity proof in Section 2, it contains an even-plus-even gate. Thus

    t<=d'.                                                    (12)

Every non-tree component has cycle rank at least one, so beta>=c-t. Using (3),

    G >= g = N-c+beta >= N-t >= N-d' >= N-d.                    (13)

This proves the unrestricted inequality G+d>=N. Nothing in the proof forbids
cross-copy sharing, cancellation, odd helpers, dependent even suppliers, or
additional input-component merging. Those possibilities are charged through
the full physical component and cycle counts.

For each 0<=j<=b, implement j copies with (7) and the remaining b-j copies with
(10). This gives exactly

    d=j,             G=sum_i N_i-j=N-j.                      (14)

Thus the precise optimum under an allowance of at most D even-plus-even gates
is, for every nonnegative integer D,

    min_{circuits with d<=D} G = N-min(D,b).            (15)

This comparison establishes the scope of an unrestricted transformation claim:
there is no universal constant additive overhead for converting arbitrary
all-odd target circuits into circuits with d=0. The required overhead is exactly
b for this specified family. The main universal statement about each map is
(1), not an assumption restricting the circuits being lower-bounded.

With two targets of each type in every copy, N=10b and there are 6b outputs.
The unrestricted optimum is 9b; without even-plus-even gates it is 10b. The
removal penalty is linear in the size of this explicit family, not merely a
one-time defect.

No general additivity theorem for XOR circuits was used. The decomposition is
visible in the targets, and any physical merging of those pieces is retained
and charged in (13).

## 4. Arbitrarily many even aggregations forced in one connected optimum

There is also a connected version with complete optimal wiring rigidity.
Take a full rooted binary tree with q>=2 leaves. For each leaf ell choose two
base coordinate inputs a_ell,b_ell. Let S_v be the union of the base input pairs
below a tree node v, and let h_v be their XOR. The tree has 2q-1 nodes. For each
node v choose m_v>=2 fresh private coordinate inputs z_{v,1},...,z_{v,m_v} and
require

    y_{v,i}=h_v+z_{v,i}.                                      (16)

Put M=sum_v m_v and N=2q+M. Compute each leaf supplier a_ell+b_ell, each internal
supplier as the sum of its two child suppliers, and each target as (16).
This uses

    q+(q-1)+M=N-1 gates.                                     (17)

All targets overlap the root's targets in base coordinates, so their support-
overlap graph is connected. Equation (4) proves (17) optimal.

In any optimum, the intersection of y_{v,1} and y_{v,2} forces h_v to be a
physical gate value. These 2q-1 distinct even suppliers together with the M odd
targets exhaust all N-1 gates. There is no other gate value. A supplier cannot
use any required target as an operand, since that would introduce a private
coordinate which cannot cancel. A leaf supplier must add its two base inputs.
An internal supplier has weight at least four, so it cannot add two coordinate
inputs; it must add two even suppliers. Their supports must be disjoint and
unite to S_v. In a full binary hierarchy, the only two proper node supports
with that property are the two children of v.

Likewise, a target gate must add its own private coordinate to h_v: no other
available even supplier contains that private coordinate, and any other odd
target introduces a different private coordinate. Thus every optimum has the
displayed wiring, apart from gate scheduling and operand order. In particular,

    O=M,       H=0,       E=2q-1,       d=q-1,
    r=q,       mu=0.                                         (18)

The q leaf pair suppliers are independent and span all even supplier values,
which gives r=q. The remaining equalities also follow from the exact parity
account. These values describe every optimal circuit, not an imposed circuit
shape. The independent-copy construction of Section 3 supplies the stronger
unbounded additive removal gap; no such gap formula is asserted for this
connected hierarchy by itself.

## 5. Consequence for the unrestricted research program

The ternary reformulation remains valid. What fails is the possible next step
of treating physical even aggregation as removable at bounded total cost.
Even when all final targets are odd, an optimal circuit can require arbitrarily
many even-plus-even gates, and eliminating them can have an arbitrarily large
additive cost after complete rewiring.

The mechanism is structural. At the basic n-kappa gate bound, the physical
ancestor graph is a forest. Shared support intersections must then exist as
actual computed values. Prescribed intersections can force a hierarchy of even
suppliers. Escaping that hierarchy requires extra cycles or extra component
merging, and those are counted in the unrestricted tradeoff.

This supplies a general equality theorem and a reduction obstruction. It does
not improve the MixColumns interval 75-88, assert that an optimal MixColumns
circuit must have even-plus-even gates, or solve the cost of arbitrary shared
pair supply. For maps farther from the forest bound, a useful continuation
would quantify how many intersection requirements one physical cycle can evade;
separate missing intersections cannot simply be charged one gate each.

The [specified checker](checks/check_joint_supply.py) verifies three instances
with b=3 and N=30, using d=3,1,0 and G=27,29,30 respectively, and one connected
three-leaf hierarchy with 16 inputs, 15 gates, and two EE gates. All target masks
and the displayed parity counts are checked directly. The
[saved result](checks/joint-supply-result.json) is construction verification,
not a search or a proof of optimality by computation.
