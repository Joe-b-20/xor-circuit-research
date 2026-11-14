# Exact column cloning and unrestricted coordinate projection

2026-11-14. Hand proofs for ordinary binary XOR circuit size, with arbitrary
cancellation, sharing, and intermediate values. No circuit search or enumeration
is used. An [independent machine review](reviews/column-cloning-review.md) is
saved; this is not formal verification, human certification, or a
literature-novelty claim.

Identical input columns can be compressed at an exact cost. This is a reduction
of an arbitrary target map, not an assumption that a competing circuit first
groups those inputs. It also supplies the precise cost needed when a construction
duplicates coordinates to control target parity.

## 1. A deletion lemma that does not require private inputs

Let a circuit compute specified linear forms in coordinate inputs. Suppose an
input z occurs with coefficient one in a required value that is not itself a
coordinate input. If that value still contains another unprojected coordinate,
then setting z to zero permits at least one gate to be deleted.

Indeed, choose the first gate whose value has coefficient one in z. Such a
gate exists because the required value is non-input. No earlier gate has that
coefficient, so one parent must be the coordinate z and the other parent has
coefficient zero. Projection to z=0 replaces this gate by its other parent.
Rewire copies and simplify zero operands; this cannot increase gate count.
The argument concerns the first coefficient-one value, not the first syntactic
read, since a read z+z can cancel.

After one deletion, the same argument applies to the surviving projected
circuit. Thus a sequence of projections with a non-input target witness at each
step deletes at least one distinct gate per step. Inputs need not be private
to one target, and may be mixed and canceled elsewhere in the original circuit.

## 2. Exact compression of identical columns

Let M be a binary target matrix. Ignore zero input columns, which no target
uses, and let n be the number of remaining coordinates. Partition these input
coordinates into t classes C_1,...,C_t according to their identical nonzero
columns in M. Let M_red have one representative column from each class. Then

    L_2(M) = (n-t) + L_2(M_red).                         (1)

Zero output rows may be omitted; they do not affect the nonzero target problem.
Repeated target rows are allowed. The zero map has n=t=0 and cost zero in this
convention.

**Upper bound.** Compute s_j=XOR_{i in C_j} x_i for each class, in |C_j|-1 gates.
Each target either contains every input of C_j or contains none, so applying a
circuit for M_red to the actual values s_1,...,s_t computes M. The total is
sum_j(|C_j|-1)+L_2(M_red)=n-t+L_2(M_red).

**Lower bound.** Keep one representative input in each class and project its
other members to zero, in any order. Before a member z is projected, any target
using that class contains both z and the still-present representative. It is
therefore non-input and the deletion lemma removes at least one current gate.
There are n-t projections. The surviving circuit computes precisely M_red, so
G-(n-t)>=L_2(M_red). This proves (1).

Zero input columns may also be projected away without increasing size, since
all specified nonzero target values remain unchanged. Conversely, a circuit
that ignores those coordinates is available from the outset. Hence deleting
zero columns preserves binary complexity exactly.

For example, replacing every coordinate of any target map by the XOR of b_i
fresh coordinates with identical incidence raises exact binary complexity by
sum_i(b_i-1). The original computation may have arbitrary sharing; the added
cost remains exact after unrestricted rewiring.

Equation (1) concerns total binary size only. Grouping or projecting inputs can
change their parity roles, the numbers of particular gate types, and the rank
of even values. No preservation of those additional resources is asserted.

## 3. A general projection bound from input co-occurrence

For a target map on n active coordinates, form the undirected graph in which
two coordinates are adjacent when some target contains both. Include isolated
active coordinates, which occur only in singleton targets. For a retained set
X of active coordinates, let kappa_0 be the number of graph components disjoint
from X. Let M|X denote the matrix obtained by setting all other coordinates to
zero. Then

    L_2(M) >= n-|X|-kappa_0 + L_2(M|X).                  (2)

**Proof.** In each component meeting X, choose a spanning forest rooted at the
vertices of X in that component; every other vertex has a parent closer to a
root. Such a forest is obtained by growing from all those roots. In every
component disjoint from X, choose one temporary retained root and a spanning
tree. Delete non-root vertices in decreasing distance from their roots.

When z is deleted, its parent is still present, and an original target contains
both endpoints of that co-occurrence edge. The current projection therefore
still has a non-input target containing z and its parent. The deletion lemma
applies. Exactly n-|X|-kappa_0 such projections are made.

The surviving map is M|X together with possible singleton outputs on the
temporary roots. No target spans distinct co-occurrence components. Those
additional singleton outputs cost zero and their independent inputs can be
ignored, or projected to zero, without affecting M|X. The surviving complexity
is consequently L_2(M|X), proving (2).

When X meets every component, the loss is exactly the number of projected
coordinates in the lower bound. When X is empty, (2) recovers the general
n-minus-components support bound. Equation (2) need not be an equality for an
arbitrary retained set. Column cloning is a special setting in which the
projection lower bound has the matching construction (1).

These facts give reductions and lower bounds for unrestricted circuits. They
do not assume that individual components are computed separately, and make no
new numerical claim for MixColumns.
