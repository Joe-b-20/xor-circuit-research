# Independent review of charged odd forests

2026-11-14. I independently reviewed [CHARGED_ODD_FOREST.md](../CHARGED_ODD_FOREST.md), including the general full-value identities, the six-entry rank decomposition, and the exact residual carrier. No material gap remains after the general terminal-input and physical-occurrence clarifications. This is machine review, not formal verification or human certification; no circuit search or enumeration was used.

**Verdict:** the charged cut identities, the global rank `t-4`, the independent residual sectors of total dimension `6-t`, and the port-hull carrier statement are sound under their stated hypotheses. They do not by themselves give a source-cost bound.

## General charged identities

The forest construction uses physical odd occurrences, including separate vertices when two odd masks happen to agree. The charge `S_v` is now explicitly attached to the copy tree rooted at that occurrence. This avoids identifying different physical adjoints merely because their ordinary masks are equal.

At an odd gate, its incoming forest edge is the full adjoint of its result, while its outgoing gate-reader contributions are the other incident fluxes. Terminal ordinary outputs and extra source ports account for the remaining terms. At an ordinary input, the full adjoint is a designated reversed target. These give the stated vertex equation with boundary `B_v` and source charge `S_v`. Summing over a component cancels every forest edge twice; summing over one side of an edge cut leaves exactly that edge. Both are full-value identities and require no retiming of ports.

Modulo `D`, the cut equation places every edge flux in the span of vertex charges, and the vertex equation places every charge in the span of incident edge fluxes. Thus the equality of their spans and ranks follows in both directions, including isolated forest vertices.

For an even helper, the corrected full adjoint equation includes `T_i`, the ordinary reversed inputs from any terminal outputs at that helper. This term has zero source part, so the aggregate helper-port label still belongs to `H=D+span{S_v}`. Ordinary gate-reader contributions are forest fluxes; ordinary terminal contributions have zero source part. Full roots and every non-source-port leaf of each value's copy tree therefore have source parts in `H`. A partial wire sum can differ modulo `H` only through the individual source ports below it. The general statement is containment, not a claim that every class residual is independent in an arbitrary circuit.

## The two mirror paths

For the six-gate ordinary mirror, the two even helpers are distinct and nonzero, hence independent. Its eight odd masks are the four inputs and four triples, all distinct. Edges preserve odd cosets modulo their rank-two helper span. There are two occupied cosets and two forest components, so each component is exactly one four-mask coset. At most one neighbour is possible in either helper direction; each three-edge component is consequently an alternating four-vertex path.

Neither path can contain all four ordinary input units because those units have affine rank three. The input subset in each component is therefore nonempty and proper. The target source labels have only their all-four relation, so each component's aggregate odd-port charge is the same nonzero clean value. The note correctly treats this as an aggregate identity rather than a physical clean supplier.

The path edge-colour totals give helper reader counts `(3,1)` or `(2,2)` after subtracting each helper's creation edge. The warning about an internal segment of a three-reader helper is justified; the earlier clean-endpoint conclusion is not imported without its reader hypothesis.

## Exact ranks of aggregate charges and local residuals

Let `V` be the formal span of the `t` disjoint trace-class indicators. Its dimension is `t`. The actual-label map has exactly one nonzero kernel vector, namely the indicator of all odd trace positions, and that vector lies in `V`. Hence the aggregate-label span has dimension `t-1`.

The target-row coefficients are constant on each trace class, so `D` lies in this aggregate span. Odd class aggregates are precisely the vertex charges in this mirror; even class aggregates lie in `H` by the helper adjoint equation. Conversely the defining generators of `H` all lie in the aggregate span. Thus `H` equals that span, giving `dim(H/D)=t-4` and `dim(U/H)=6-t`. The earlier exact span equality then gives forest-flux quotient rank exactly `t-4`.

Because the sole kernel of the actual-label map is contained in `V`, its induced map from the formal quotient by `V` to `U/H` is an isomorphism. The formal quotient is the direct sum of the separate class spaces modulo their all-ones vectors. Thus a class of multiplicity `m` contributes an independent residual sector of dimension `m-1`. This proves independence across classes rather than merely bounding their total dimension. The six-gate mirror has one physical producer for each ordinary value, so its class ports occupy the corresponding single marked copy tree.

## Exact physical carrier

On a copy-tree wire, the residual source value is the sum of the class-port generators below it; all ordinary leaves contribute zero modulo `H`. In that class sector, the only relation is the sum of all its ports. The wire residual therefore vanishes exactly for the empty subset or the whole class. An edge separates a nonempty proper set of port leaves exactly when it lies in their minimal undirected connecting subtree. This proves the asserted equality between the residual-nonzero carrier and the port hull.

A repeated pair gives a path. Three ports give a three-arm tree after suppressing degree-two vertices. Since trace rank is four, a class can have at most three occurrences among six entries. The statement is about the marked copy tree and its reversed physical wires; it supplies no source-gate credit, independent source availability, or preferred chronological orientation for that carrier.

## Added entry-graph separator consequence

I also checked the final corollary added after the initial review. At the dual copy node of an actual entry, the input wire and its non-port output wire carry the same ordinary mirror value. Reversing again identifies these with the two full consumer endpoint values, including any suppressed copies. Both endpoints therefore have residuals in that entry's trace-class sector.

If entry edges from different classes share a physical node, its residual belongs to their two independent sectors and is zero. A singleton sector is zero, so both endpoints of its entry lie in `H`. A repeated-pair sector has one nonzero vector, and the entry label has that vector as its residual; its two endpoint residuals must therefore be zero and nonzero in some order. With multiplicities at most two, no entry edge joins two residual-nonzero vertices, and a nonzero vertex can meet only the two possible edges of its own repeated pair. This is a property of the entry graph, not a degree bound on every kind of consumer edge. The corollary correctly treats the separating `H`-valued consumer nodes as physical vertices without granting their source parts separately.

The final scope is accurate. These theorems organize where the two nonclean quotient directions occur, and how repeated classes can carry directions absent from aggregate forest charges. They do not rule out the remaining multiplicity-two or all-distinct trace profiles, and do not close the twelve-consumer or unrestricted joint problem.
