# Tight ordinary fibres constrain the order of entry traces

2026-11-13. Structural hand proof using literal transposition with explicit copy nodes. No circuit search or configuration enumeration. The result concerns an eleven-gate consumer with five entries and a six-gate ordinary projection; its joint consequence permits arbitrary feedback.

## The tight consumer and its two ordinary circuits

Use four ordinary consumer coordinates `z_0,...,z_3` and a disjoint source space. Require four consumer outputs whose ordinary parts are the four triples `E_j(z)`. Suppose the relaxed consumer graph has eleven consumer-bearing gates, five actual entry occurrences, and every counted gate belongs to one of the four target cones. Each entry reads one source value and one consumer-bearing value. Replace its source operand by its own formal input, even if two actual labels are equal. The formal input has exactly one reader, its entry gate. An entry's trace is the four-vector of its influence on the designated targets.

Bypass all five entries in the ordinary projection. Six non-entry gates remain and compute all four ordinary triples, whose minimum is six. Therefore no remaining gate can have zero value, repeat a previous gate or input value, or be otherwise bypassed: that would produce a five-gate triple circuit. Its gate values consist of the four odd triples and two distinct nonzero even values, because every odd four-coordinate value is either an input unit or a triple.

Consequently each original own-mask fibre contains exactly one ordinary input or non-entry gate, its root. Every other node in that fibre is an entry connected to its earlier nonfree operand. These entry edges form a rooted tree. For two original nodes in the same fibre, their source-part difference is the XOR of the labels along their unique simple tree path. Every path edge belongs to a root-to-endpoint path and is read at or before that endpoint is produced, hence strictly before an exit using both endpoints.

The literal transpose also has six gates. To see the exact wire correspondence, expand fanout into binary copy nodes, with designated outputs represented by terminal ports. There are nine input ports (four ordinary and five formal), four output ports, and eleven XOR nodes. Wire balance gives six binary copies. Reverse every wire and interchange XOR and copy nodes. This gives six XOR nodes, eleven copies, four inputs and nine outputs: the four ordinary input adjoints and five entry traces. The ordinary input adjoints are the four triples because the ordinary target matrix is symmetric.

Each trace output attaches to the copy node dual to its original entry XOR. Delete the five trace-output ports and suppress those five unary copies. Transposing the resulting network returns exactly the original expanded ordinary projection, with each original entry bypassed. Thus the reduced mirror is a six-gate ordinary triple circuit, retaining the original wire positions. This is the [marked-wire construction](WIRE_DUALITY.md) with five rather than four formal ports; the copy count remains six.

For a mirror wire, its ordinary derivative is the four-vector of coefficients at the ordinary mirror outputs caused by perturbing only that wire. A marked wire carrying an entry's trace has ordinary derivative equal to the entry's own mask. This follows by literal double transposition, not by identifying equal-valued internal nodes in unrelated implementations.

## The two even helpers have separated wire derivatives

In any six-gate ordinary triple circuit, let its two even helper values be `p,q`. Every reader of either helper is one of the four designated odd triple gates. A reader cannot be a third even gate, and the two helpers cannot share a reader: such a reader would add two even values and be even.

Let `kappa_j` be the full output adjoint of the designated gate for triple `E_j`. Ordered topologically, their coefficient matrix is unitriangular: each includes its own terminal output and can include only later output units. Thus the four `kappa_j` are independent.

A wire in the copy tree of `p` with nonzero ordinary derivative feeds a nonempty subset of its reader gates, so its derivative is the sum of the corresponding `kappa_j`. A wire carrying `q` gives the sum for a subset of a disjoint reader set. Independence makes these nonzero sums different. Therefore two wires carrying the different even helpers cannot have the same nonzero ordinary derivative. The statement is about particular wires and the reader subsets they feed, not full adjoints of all uses of a mask.

## An adjacent pair exposes its trace difference

Suppose two entry edges meet at a node `v` of an original own fibre. Let their traces be `alpha,beta`. They are either two outgoing edges from `v`, or one incoming and one outgoing edge; there cannot be two incoming edges in a rooted tree.

- For two outgoing edges, `alpha,beta` are two contributions to the adjoint of `v`. Accumulate those contributions first in the mirror.
- For an incoming edge and an outgoing edge, the trace of the incoming edge is the full adjoint of `v`, and the outgoing trace is one of its reader contributions. Accumulate all the other reader and terminal contributions first. Their sum is `alpha+beta`.

Whenever `alpha+beta` is nonzero, this makes it a wire value of a literal transpose with the same six-XOR budget. A single contribution needs no accumulation gate. The selected wire feeds the adjoint accumulator for `v`; perturbing it is therefore transmitted to the ordinary mirror outputs with derivative exactly the ordinary mask of `v`. Deleting trace-output ports does not change that ordinary derivative. All counted original own masks are nonzero.

The fanout expansion at each original node may be chosen independently. Thus adjacent-pair sums at two different original nodes can be exposed simultaneously in one literal mirror. Every resulting mirror still has six XORs and computes the four triples; it is consequently a minimal ordinary triple circuit after deletion of the trace ports. Its two even helper values satisfy the preceding separation theorem.

## Three consecutive distinct odd traces are impossible

**Odd-run theorem.** A simple path in an original own fibre cannot contain three consecutive entry edges whose traces are distinct odd vectors.

Suppose their traces in path order are `alpha,beta,gamma`. The two internal path vertices are distinct. Choose their accumulation orders to expose both

    alpha+beta,       beta+gamma

simultaneously. These sums are nonzero even masks, and they are distinct because `alpha!=gamma`. They therefore are the two even helper values of that six-gate mirror. Both selected wires have the same ordinary derivative, namely the common nonzero own mask of the fibre. This contradicts even-wire separation.

The proof allows the path to traverse entries in either direction. It uses no assumption that its three entry gates form a chronological chain; the pair at a branching point is handled by the outgoing/outgoing case above.

## All-five-odd traces admit cost-preserving source replay

Suppose all five entry traces are distinct and odd. Every simple path in any own fibre then has at most two edges by the odd-run theorem. Every zero-consumer exit, being a difference of two equal-own nodes, is consequently zero, one earlier actual entry label, or the sum of two earlier actual labels.

Replay source-side gates chronologically. Copy an ordinary source gate from its already replayed source operands, or bypass it when already supplied. An exit uses at most one XOR of the earlier entry labels on its fibre path. Those labels' source producers have already been replayed, even when their original production had feedback ancestors. Thus every original source value is preserved with no extra source gates. Computing that source-only replay first and then the original consumer gives a full no-feedback realization of no greater size.

In the MixColumns joint 0/1 problem, the recorded [no-feedback joint lower bound](../augmented/CONSEQUENCES.md) is 22. Therefore the all-five-odd eleven-consumer class also has total cost at least 22 with arbitrary feedback.

In particular this excludes the previously retained four-nonclean profile whose sole label relation uses all five labels. The [five-entry interface theorem](../compatibility/QUOTIENT.md#five-entries-and-six-mirrored-gates) identifies that relation's support with the odd trace positions and ensures that all five traces are distinct when at least three entries are nonclean. Algebraic trace feasibility alone had not excluded this profile; the wire-derivative condition now supplies the additional obstruction. This statement gives a joint lower bound, not an assertion that the local consumer profile itself has no realization.
