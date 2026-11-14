# A causal forest quotient, and an unbounded joint intersection-repair gap

2026-11-14. Structural hand proofs for unrestricted binary XOR circuits.
Arbitrary sharing, repeated reads, and cancellation are allowed. No circuit
search or case enumeration is used. Independent machine review is recorded in
[the review](reviews/causal-forest-quotient-review.md); this is not formal
verification, human certification, or a claim of literature novelty.

The [forest equality theorem](TREE_INTERSECTION_RIGIDITY.md) forces nonempty
support intersections to be physically present when the full ancestor graph
is a forest. Every unrestricted circuit has an exact forest representation
with one causal input identification per graph cycle. However, even a single
cycle can evade arbitrarily many independent intersection values. Requiring
all of those values physically can have an unbounded extra cost, even after
complete rewiring of an optimal circuit.

This does not contradict the companion
[individual intersection-repair theorem](BRANCH_INTERSECTION_REPAIR.md): each
intersection in the example is individually only one XOR away. The distinction
between individual and simultaneous repair is essential.

## 1. Every circuit is a forest with causal input identifications

Take the complete union of the ancestor cones of the required physical outputs.
Let a be its number of actual coordinate-input ancestors, g its number of gate
occurrences, and c its undirected component count. Keep both operand ports as
separate edges, including repeated reads. Its full undirected cycle rank is

    beta = g-a+c.

Choose any spanning forest on these physical vertices. There are exactly beta
operand edges outside that forest. For each such edge u_l -> v_l, cut the read
of its source occurrence u_l and replace that operand of v_l by a fresh formal
input s_l. Keep every original gate and its other operand port.

**Causal forest quotient theorem.** This construction has the following exact
properties.

1. The new circuit is a literal forest on a+beta independent formal inputs,
   with the same g gate occurrences and the same c components.
2. There is a linear projection pi onto the original a-dimensional coordinate
   space taking each original input to itself and s_l to the original physical
   value at u_l. Projecting every formal gate value recovers the original value.
3. The kernel of pi has dimension beta. It has a basis of causal relations

       rho_l = s_l + U_l,

   where U_l is the formal value computed at the cut source u_l. Ordering the
   cut edges by the chronological position of their reader gate v_l makes
   each U_l depend only on original inputs and earlier shadow inputs.

**Proof.** Removing the beta nonforest edges leaves a forest connecting all
original vertices within their original components. Adding one fresh leaf to
the reader of each cut edge preserves that forest and its component count.
Every gate still has two inputs, and fresh input leaves do not create a directed
cycle. There are a+g+beta vertices and 2g edges, consistently with cycle rank
zero. Thus statement 1 holds.

At a cut port, the prescribed projection supplies exactly the original value
of that operand. Induction over the original gate order proves statement 2.
If a shadow s_j occurs in U_l, its reader gate v_j precedes u_l, which precedes
v_l. Therefore j precedes l in the stated ordering. The relations rho_l are
triangular with a distinct leading shadow coordinate and coefficient one, so
they are independent. They all lie in ker(pi). The projection is the identity
on the original a input coordinates, hence has rank a and kernel dimension
beta. The beta relations form its full kernel. QED.

Some cut sources may cease to be ancestors of the original output set in the
formal forest. If a complete ancestor-union presentation is wanted there too,
designate those cut sources as additional formal outputs. Every original node
then remains in a designated cone. This changes no gate or relation count.

The relations do not grant beta arbitrary linear forms as free physical inputs.
Each U_l is the value at an actual earlier source occurrence in the same
chronological circuit. Discarding those availability constraints would be a
different relaxation. Likewise, the theorem does not say that original support
intersection commutes with pi: generally it does not. A kernel of dimension
one can already permit an unbounded collection of missing physical intersections.

## 2. One cycle evades many independent intersections

Fix m>=2. Use independent coordinate inputs

    r, a_1,b_1,...,a_m,b_m, z.

There are n=2m+2 inputs. Define the specified circuit

    e_i = a_i+b_i,                         1<=i<=m,
    p_0 = r,
    p_j = p_(j-1)+e_j,                     1<=j<=m,
    e_0 = r+z,
    q   = p_m+e_0.

Require all p_j and q. The inputs and all these targets have odd total parity;
the e_i, including e_0, are even. The circuit has

    G=m+m+1+1=2m+2=n.

Its full ancestor graph is connected. Each pair gate and each prefix extension
attaches a tree branch; the two routes from r to the final q create exactly
one undirected cycle. Equivalently beta=G-n+1=1.

This beta is the cycle rank of the full ancestor graph, not the cycle rank mu
of the parity-specific odd-occurrence graph. In this construction the m+1 even
pair values e_0,...,e_m are independent, so its even rank is m+1, d=0, and mu=0.
The obstruction therefore occurs even at zero even defect in the earlier
[parity account](ODD_COMPONENT_DEFECT.md).

Write

    c_j = e_1+...+e_j.

The actual target values are p_j=r+c_j and q=c_m+z, so

    supp(p_j) intersect supp(q) = supp(c_j).                (1)

For j=2,...,m none of the c_j is a physical value of the specified circuit:
the computed even values are only the weight-two e_i and e_0, whereas c_j has
weight 2j. All other gate values are odd. The m-1 vectors c_2,...,c_m are linearly
independent: in any nonempty combination, the largest-index c_j contributes
the pair e_j, which occurs in none of the smaller prefixes in that combination.

Thus one full physical cycle can evade arbitrarily many distinct and linearly
independent intersection values. Neither their number nor their raw vector
rank can be bounded by a universal constant times beta. This is about actual
availability, not membership in the span of all available values.

Each missing c_j nevertheless equals p_j+r, so its remaining ordinary binary
cost from the final dictionary is exactly one. It is absent, and one displayed
XOR supplies it. Individual repair and simultaneous repair have different costs.

## 3. The same construction is an invertible all-odd map

Retain the free identity outputs r,b_1,...,b_m, in addition to p_1,...,p_m,q.
This gives exactly 2m+2 outputs. The square map is invertible because

    a_1 = p_1+r+b_1,
    a_j = p_j+p_(j-1)+b_j,                 2<=j<=m,
    z   = q+p_m+r.

Together with the retained r and b_i these recover every original coordinate.
All output rows remain odd. The identity outputs add no gates and do not change
the complete ancestor graph, so the same beta=1 implementation applies.

This map is not claimed to be an involution. Its displayed inverse suffices.
The many prefix outputs have no separate private coordinate attached to each
of them: they share r and nested sums of the input pairs.

## 4. Exact cost under input-column cloning

We use an elementary projection lemma, stated here to keep the cost proofs
self-contained. The general [column-cloning theorem](COLUMN_CLONING.md)
also collapses arbitrary classes of identical active columns at once.

**Column-cloning lemma.** Let a nonzero coordinate column x of any linear target
map be replaced throughout by x+y, where y is a fresh coordinate. The exact
binary complexity increases by one. Repeating this for distinct active columns
increases complexity by the number of introduced clones.

**Upper bound.** Compute x+y once and run an optimal circuit for the original
map using it in place of x.

**Lower bound.** Set y to zero in any circuit for the expanded map. Some target
contains y, and every such target also contains the retained x, so it is not
the coordinate input y. In the current circuit, choose the first gate whose
value has y coefficient one. It must read the input y and a value with y
coefficient zero. Projection replaces this gate by its other operand, deleting
at least one gate. Simplify zeros and copies. The remaining circuit computes
the original map. For several clones, repeat on the surviving circuit; each
step deletes a distinct current gate and every unprojected clone still has its
original coordinate beside it in each affected target. QED.

The lemma permits arbitrary mixing and cancellation before projection. It is
not an assumption that an optimal expanded circuit first computes the column
pairs. The identities that make the example square are free outputs; the
following complexity calculations can therefore use its nonidentity targets.

## 5. Original optimum and exact simultaneous repair cost

First work before cloning, with independent inputs r,a_1,...,a_m,z. Put

    A_j=a_1+...+a_j,
    P_j=r+A_j,
    Q=A_m+z.

**Original uncloned map.** Projecting the private coordinate z to zero deletes
at least one gate, by the same first-coefficient-one argument. The remaining
required values P_1,...,P_m,A_m are m+1 distinct non-input vectors when m>=2,
so they require at least m+1 gates. Therefore the original map needs at least
m+2 gates. The prefix chain P_j followed by r+z and Q=P_m+(r+z) uses exactly
m+2 gates.

Clone every a_i into a_i+b_i. The column-cloning lemma proves that the targets
of Sections 2-3 have exact unrestricted complexity

    L_2(p_1,...,p_m,q) = 2m+2.                             (2)

Thus the one-cycle construction is actually optimal; the obstruction is not
created by deliberately using an unnecessarily cyclic implementation.

**Require all intersections too.** In the uncloned map, add A_1,...,A_m as
required values. Projecting z to zero again deletes at least one gate. The
remaining non-input targets are the m distinct P_j together with the m-1
distinct A_2,...,A_m. Their populations are disjoint, since only P_j contains r.
They require at least 2m-1 gates. Conversely, computing the A-prefixes costs
m-1 gates, attaching r to each costs m gates, and attaching z to A_m costs
one more. The exact uncloned complexity is therefore 2m.

After the m column clones, the exact complexity with all c_j physically
required is

    L_2(p_1,...,p_m,q,c_1,...,c_m) = 3m.                    (3)

The free identity outputs used for invertibility do not change (2) or (3).
Equations (2)-(3) allow arbitrary complete rewiring and arbitrary cancellation.
The exact extra cost of simultaneously making all those intersections available
is

    3m-(2m+2)=m-2.                                        (4)

It is unbounded as m grows, although the original optimal circuit has only
one full undirected cycle and every missing intersection individually costs
one additional XOR. The c_1 output is already supplied in the specified
circuit; requiring only the missing c_2,...,c_m gives the same cost (3), as
A_1 is an input in the uncloned argument.

## 6. What survives the obstruction

The causal forest quotient retains an exact small number of independent
relations, but those relations can be reused across many outputs. Therefore
their number alone cannot price every missing intersection or its simultaneous
repair. The independent-rank version of that proposed charge fails too.

The [branch intersection theorem](BRANCH_INTERSECTION_REPAIR.md) gives the
positive counterpart: one intersection has a short representation in actual
physical values, controlled by the cycles of its two-root ancestor union.
That statement is compatible with (4); several short representations can
still require many distinct extra gates when all their results are demanded.

These statements apply to unrestricted implementations and exhibit an
invertible all-odd family. They do not improve the numerical MixColumns bound,
assert a general direct-sum principle, or imply that the full physical cost
can be recovered from raw cycle rank alone. MixColumns remains 75<=L<=88.

The [specified checker](checks/check_intersection_repair.py) verifies m=4:
ten original gates, twelve gates after simultaneous repair, three independent
missing intersections, and the displayed inverse of the square map. It also
constructs a spanning-forest cut, checks every gate under projection, verifies
the causal shadow relation and kernel rank, and checks the individual two-term
intersection certificate. The [saved result](checks/intersection-repair-result.json)
is direct verification of the specified construction, not circuit search or
an optimality proof by computation.
