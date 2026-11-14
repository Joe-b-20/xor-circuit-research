# Odd trace ports become charges on the mirror forest

2026-11-14. Structural hand arguments with independent machine review. No circuit search, enumeration, or computer-driven elimination. The general cut identities apply beyond MixColumns; the final rank identities use the remaining six-entry interface.

## A forest with source charges

Consider an ordinary XOR circuit on coordinate inputs whose computed even gate values are independent. As in [CHAIN_FIBRES](CHAIN_FIBRES.md#general-odd-forest-principle), put one vertex at each odd input or odd gate occurrence. An even gate joins its two odd parents; an odd gate joins its odd parent to its new result. Label each edge by the corresponding even helper. Chronology makes this graph a forest: a new even gate cannot close a path of earlier helper labels without violating independence.

Attach formal trace-output ports to arbitrary mirror wires, and transpose literally. The attached ports become actual source labels in the reversed circuit. Suppose the designated reversed targets have source parts in a subspace `D`; ordinary reversed inputs have zero source parts. All statements concern this particular marked network and its full physical values.

For an odd vertex occurrence `v`, let `S_v` be the sum of actual labels attached within the physical copy tree rooted at that occurrence. Equal odd masks at different occurrences are kept separate here. Let `B_v` be its uncharged boundary: a reversed target at an original input vertex, together with any ordinary reversed inputs from terminal output ports at that vertex. Thus every `B_v` has source part in `D`. Let `X_e` be the full adjoint flux on a forest edge: the helper's full adjoint for a helper-creation edge, or the odd result's full adjoint for an odd-gate edge.

The vertex equation is

    sum_(e incident to v) X_e = B_v + S_v.                 (1)

Odd trace ports may attach at different positions in this occurrence's copy tree. Their total contribution to its full adjoint is still exactly `S_v`, so (1) does not move a source label to an earlier physical position.

Summing (1) over a whole forest component `T` gives the component charge identity

    sum_(v in T) S_v = sum_(v in T) B_v.                   (2)

In particular, every component's aggregate odd-port label is in `D`. Cutting an edge `e` and summing over either side `A` gives

    X_e = sum_(v in A) B_v + sum_(v in A) S_v.             (3)

The sums from the two sides agree by (2). These are full-value identities, not assertions that the individual source parts are already supplied separately.

Write bars for source parts modulo `D`. Equation (3) says `bar X_e=sum_(v in A) bar S_v`, while (1) says `bar S_v=sum_(e incident to v) bar X_e`. Consequently

    span{bar X_e : forest edges e}
      = span{bar S_v : odd vertices v}.                   (4)

This is an exact rank identity. All forest fluxes have clean source parts if and only if every odd vertex's aggregate port label is clean.

## What local copy trees can still hide

Let

    H = D + span{S_v : odd vertices v}.

Every forest flux has source part in `H`. The aggregate label `E_i` on an even helper's trace ports also belongs to `H`: its full adjoint equation is

    E_i = H_i + sum_(j a gate reader of helper i) F_j + T_i,

where `H_i` and the `F_j` are forest-edge fluxes, and `T_i` is the sum of reversed ordinary inputs contributed by any terminal ordinary-output ports at that helper. The term `T_i` has zero source part. The ordinary parts cancel in the displayed full-value identity, and the source parts on the right belong to `H`.

At an odd vertex, each ordinary-reader contribution is an incident flux, and each ordinary terminal contribution has zero source part. At an even helper, every gate-reader contribution is an odd-gate adjoint flux, and every ordinary terminal contribution again has zero source part. Thus every non-port leaf of every value's copy tree has source part in `H`; its full root adjoint does too. The only contributions outside `H` come from individual source ports inside that copy tree.

It follows that a physical reversed wire in the copy tree of trace value `tau` has source part modulo `H` equal to the sum of some of the labels whose trace is `tau`. This confines any source direction invisible to aggregate charges to a single repeated trace class. A singleton trace class has no such hidden direction, since its aggregate label already belongs to `H`.

This statement concerns containment of a physical value's source part. It supplies neither a chronological source-only computation of that part nor a gate credit for virtual group membership.

## The six-gate mirror consists of two four-vertex paths

Now specialize to the remaining target-live MixColumns consumer with twelve gates and six entries. Its ordinary mirror has six gates: four odd triples and two distinct nonzero even helpers `p,q`. The helpers are independent. Its odd forest has eight distinct odd masks and two components.

Put `W=span{p,q}`. Every forest edge preserves the odd mask modulo `W`. There are exactly two odd `W`-cosets, each containing four masks, and all eight odd masks occur. Since the forest has two components, those components are precisely the two cosets.

Within a component, a mask has at most one neighbour in direction `p` and at most one in direction `q`. The three-edge tree on its four vertices therefore has maximum degree two: it is a path. Its edge colours alternate, `p,q,p` or `q,p,q`. The two components are not assumed to have the same orientation or chronological order.

Let `I` be the indices of mirror input units in one component. Both components contain input units: the four units have affine rank three and cannot fit in a coset of the rank-two `W`. Hence `I` is nonempty and proper, with size one, two, or three. The complementary component has the remaining units. Formula (2), restricted to source parts, gives

    sum_(odd trace ports in component 1) label
      = sum_(i in I) D_i
      = sum_(odd trace ports in component 2) label
      = delta,                                            (5)

where `D_i` are the four required consumer source parts. Their only nonzero relation is their all-four sum, so `delta` is a nonzero clean value. Both components must contain odd trace ports. The value `delta` is a component aggregate; it need not be an original physical source value.

Each odd vertex has degree at most two. Its copy tree has at most two ordinary readers, counting an ordinary terminal output as a reader and omitting trace ports. At an input vertex the reader count is its degree. At a target vertex the incoming target edge accounts for its full adjoint, so its remaining incident readers plus its terminal output again number its degree.

Across the two paths the total counts of coloured edges are either `(4,2)` or `(3,3)`. Removing one helper-creation edge of each colour shows that the two even helpers have ordinary reader counts `(3,1)` or `(2,2)`. A three-reader helper can have a segment between two internal merges; the two-reader clean-endpoint conclusion cannot automatically be applied there.

## An exact split between global charges and repeated trace classes

Let `t` be the number of distinct trace values among the six entries, and let `A_tau` be the sum of actual labels in trace class `tau`. The [six-entry identities](TWELVE_ENTRY_WIRES.md#trace-equations-in-the-six-entry-rank-five-interface) give trace rank four and actual-label rank five. The sole actual-label relation is the indicator of all odd trace positions.

Class indicators have disjoint supports. A relation among the `A_tau` corresponds to an actual-label relation constant on each class. Its sole nonzero possibility is exactly the union of odd classes. Thus

    dim span{A_tau}=t-1.

Every required target source part is a sum of these class aggregates, so their span contains the rank-three `D`. The odd class aggregates are the `S_v`. The even class aggregates lie in `D+span{S_v}` by the helper adjoint equation above. Therefore

    H=span{A_tau},
    dim(H/D)=t-4,
    dim(U/H)=6-t.                                        (6)

By (4), the forest-edge source quotients have rank exactly `t-4`. Since trace rank is four, `t` is four, five, or six. Accordingly the forest carries zero, one, or two source directions modulo `D`. The remaining two, one, or zero quotient directions are confined to splitting repeated trace classes inside their copy trees.

There is also a direct-sum statement. Let `m_tau` be a class's number of occurrences. In the formal six-dimensional label space, quotienting by all class indicators gives

    direct-sum_tau (F_2^(m_tau) / span{all-ones_tau}).

The sole kernel of the actual-label map lies in that indicator space. Hence this formal quotient maps isomorphically onto `U/H`. The repeated classes therefore contribute independent residual sectors of dimensions `m_tau-1`. A physical consumer wire's residual source part lies in the one sector belonging to its mirror trace value; different class sectors do not mix inside a single physical wire.

For example, with five distinct traces there is one repeated pair. Both labels of that pair have the same nonzero image in the one-dimensional `U/H`; every other actual label and every ordinary reader boundary lies in `H`. With four distinct traces all aggregate charges are clean, and the entire two-dimensional quotient over `D` is accounted for by local splitting of repeated classes. These are structural identities, not exclusions of those profiles.

## The physical carrier of one repeated-class sector

The residual-sector description also identifies its supporting wires. Fix a trace class of size `m>=2` and consider its marked copy tree. All ordinary reader leaves and the root have zero source part modulo `H`. Its `m` trace-port leaves carry the class sector's standard generators, whose sole relation is their all-ports sum.

A copy-tree wire therefore has nonzero residual exactly when the ports below it form a nonempty proper subset of that class. Equivalently, the residual-nonzero wires are precisely the edges of the smallest undirected subtree connecting the class's trace-port leaves. Ordinary reader branches can attach to this subtree, but their residual values are zero.

For a repeated pair this carrier is one path. Both port labels carry the same nonzero residual, and every wire on the connecting path has that residual. In original chronological direction it may appear as one chain or as two branches meeting at a cancellation; the tree statement does not choose a causal orientation or imply that its intermediate source parts are free.

For a class of size three, its carrier is the three-arm subtree joining its ports. Each arm carries the residual of its own port, and the three residual directions sum to zero. With six ports and at least four distinct traces, no class can have more than three members. Thus every local residual carrier is a path or a three-arm tree; different classes occupy independent sectors. These shapes follow from the marked copy tree and the label-map kernel, not from enumerating consumer circuits.

## Different trace sectors meet only at aggregate-valued entry vertices

Both consumer endpoints of an entry edge with trace `tau` correspond to wires at its dual copy node, carrying that same mirror value. Their source parts modulo `H` therefore lie in the sector for `tau`. If two entry edges of different trace classes meet at a physical consumer node, that node's residual belongs to both independent sectors. It must be zero: its source part lies in `H`.

A singleton-class entry has both endpoints in `H`. For a repeated pair, the class sector is one-dimensional and either port label has its unique nonzero residual. Each of the pair's entry edges consequently has exactly one endpoint in `H` and one outside `H`.

If every trace class has size at most two, every residual-nonzero vertex of the entry graph can be incident only to edges of its own repeated pair, and at most two such edges exist. There is no entry edge between two residual-nonzero vertices. Connections between different trace classes therefore pass through vertices whose source parts lie in `H`. These are physical consumer vertices, not separately available source values; the statement is a separator property, not a free-replay assertion.

## Scope

The charged equations explain exactly what fails when odd trace ports are added to the clean odd-forest theorem: their vertex aggregates are the forest's source charges. The charge rank and local residual-sector decomposition distinguish information transported across the forest from information retained inside one trace class. No source-cost lower bound or chronological replay is inferred from these identities alone. The six-entry twelve-consumer case remains open here.

Independent review: [charged forest, residual carrier, and entry separators](reviews/charged-odd-forest-review.md). This is machine review, not formal verification or human certification.
