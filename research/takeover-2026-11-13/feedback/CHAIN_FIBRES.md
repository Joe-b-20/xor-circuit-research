# Independent even mirror helpers force chain fibres with clean endpoints

2026-11-14. Structural hand proof for the target-live twelve-consumer, five-entry, rank-five case. No search or configuration enumeration. This note supplies geometric lemmas; source replay and its timing are treated separately.

## Hypotheses and marked mirror

Use the joint two-sheet model and the notation of [TWELVE_ENTRY_WIRES](TWELVE_ENTRY_WIRES.md). Assume all twelve consumer-bearing gates lie in the four relaxed target cones, there are five entry occurrences, and their actual labels are independent. Their three nonzero even trace masks `h_1,h_2,h_3` are independent. The entry classes have sizes `(3,1,1)` or `(2,2,1)`. Write `S_i` for the sum of the actual labels in class `i`; the three `S_i` form a basis of the clean diagonal `D`.

Expand copies and transpose literally. After deleting the five trace ports and suppressing their unary copies, the reduced mirror has seven XORs, the four ordinary triples as outputs, and the original marked wire positions. Its gate values are precisely the four odd triples and the three independent even helpers `h_i`. Restoring the trace ports recovers the original literal network. In particular, a wire carrying `h_i` can carry class-`i` trace ports, whereas no odd-valued mirror wire carries a trace port.

Every helper has an ordinary reader: otherwise every wire carrying it would have zero ordinary derivative, contrary to the nonzero own mask of its marked entry wires.

The structural proof below uses only this seven-gate marked mirror, its three independent even helpers, the absence of odd trace ports, and clean source parts at the designated original targets. It does not use the number five again until a particular class size is imposed. Thus the same tree, chain, and clean-endpoint lemmas apply to another port count whenever these mirror hypotheses have been independently established.

## Separated classes and the odd-value tree

No even helper can read another even helper. An even result would then be the sum of two available even helpers, contradicting independence of the three helper values. Consequently every helper is the sum of two odd values, and every helper reader is an odd target gate. An odd target reads exactly one helper and one odd value. The three nonempty helper-reader sets partition the four odd target gates. Their sizes are therefore `(2,1,1)`.

Let `kappa_j` be the full ordinary adjoint of odd target gate `j`. The four `kappa_j` are independent: in topological target order their coefficients are unitriangular. A wire in a helper copy tree has ordinary derivative equal to the sum of the `kappa_j` for the ordinary readers below it. Distinct helpers have disjoint reader sets, so their nonzero wire derivatives cannot agree. Thus **different trace classes never occupy the same own-mask fibre**, even in different entry components.

Construct a graph on the eight odd mirror values: four input units and four target triples. For each helper, join its two odd parents by an edge labelled by that helper. For each target gate, join its odd parent to its new odd result by an edge labelled by the helper it reads.

This seven-edge graph is a tree. Chronologically, a target edge introduces a new vertex. A helper-creation edge must join two different existing components: a pre-existing path between its parents would express the new helper as a sum of previously introduced helper masks, contradicting their independence. The final forest has eight vertices and seven edges, so is connected. This is a tree on value occurrences that are distinct; it does not identify different physical source values by their ordinary masks.

## Tree cuts make odd-wire source parts clean

Restore all formal trace ports and transpose back, retaining actual entry labels at those ports. The following values are full physical values, including source parts, not just ordinary projections.

For a helper-creation edge, assign its flux to be the full adjoint `H_i` of that helper. The transpose of its XOR duplicates this same value to its two odd parents. For a target edge ending at odd target vertex `v`, assign its flux to be the full adjoint `F_v` of that target gate. Its odd-parent branch is unaffected by trace ports, which attach only to even-valued mirror wires.

At an odd input vertex `i`, the XOR of all incident fluxes is the designated original consumer target `Y_i`. At an odd target vertex `j`, the XOR of all incident fluxes is the original ordinary input `z_j`: the incoming target edge carries `F_j`, and its adjoint equation cancels all other incident contributions, leaving that terminal input. Therefore this tree has boundary values

    B_i=Y_i  at its four input vertices,
    B_j=z_j  at its four target vertices.

Each edge flux is the sum of the boundary values on either component obtained by deleting that edge. This follows by summing the vertex equations on that component. The two component sums agree because the sum of all boundary values is zero: the four `Y_i` have ordinary sum `sum z_j` and their source parts sum to zero.

Every boundary value has source part in `D`, so every edge flux does too. A wire in the copy tree of an odd mirror value is a sum of a subset of that vertex's reader contributions and, when present, its terminal `z_j`. These contributions are the incident fluxes just described. There are no trace ports in an odd copy tree. Hence **every physical original value corresponding to an odd-valued mirror wire has source part in `D`**. This is a statement about the source part of a consumer-bearing value; it does not assert that the corresponding clean source value has been separately computed.

In particular the reader-end values `F_j` and the helper-root values `H_i` all have clean source parts. The identity `H_i=sum F_j + S_i`, with the sum over that helper's ordinary readers, is consistent with this cut description; individual entries can still create nonclean intermediate values along its copy tree.

## Each occupied entry fibre is one chain

A helper copy tree has at most two ordinary reader leaves, in addition to its trace-port leaves. A marked entry wire has nonzero ordinary derivative, so its descendants include at least one ordinary reader. With one reader, all marked positions lie on the single path to that reader. With two readers, the nonzero derivative subsets are the two singletons and their union; each subset occupies one path segment of the copy tree. Independence of the `kappa_j` makes their three derivatives distinct.

After transposition, each of these path segments is an entry chain. Distinct helpers cannot share its own mask by the separation lemma. Therefore **every own-mask fibre contains at most one entry chain**. Any other node of the fibre is an isolated ordinary-input or non-entry root. No branching entry tree occurs.

Each such chain has an endpoint with clean source part. On a branch toward a single ordinary reader, use its reader-end value `F_j`. On the common trunk of a two-reader helper, use the helper-root value `H_i`. Both are physical consumer values. The clean endpoint may occur later than another node of the chain; this statement alone gives no permission to use it early in a chronological replay.

There is only one non-entry accumulation in the even-helper copy trees: the merge of the two ordinary reader branches for the helper with two readers. All other non-entry roots correspond to odd-valued mirror wires and hence have clean source parts. If that merge exists in a repeated fibre, it is the root of its unique entry chain, whose opposite endpoint is clean. If the trunk has no entries, the merge itself is the clean `H_i`.

It follows that in the unique two-root fibre retained by `TWELVE_ENTRY_WIRES`, there is either no entry or one entry chain plus one isolated root. The isolated root is clean in source part. Choose the clean endpoint of the chain as the reference. Every crossing return is then

    delta + sum of an interval from that endpoint,

where `delta` belongs to `D`, and the interval consists of labels from just one trace class. With no chain, the sole possible crossing value is clean.

The formula is an identity in the five independent actual labels. Although the reference endpoint may be later, the actual return's expanded support uses only labels already read before the exit, by causal induction on the original graph. Any entire other class occurring in that support has therefore been completely read by then. This distinguishes the structural identity from a source-side availability assertion.

## General odd-forest principle

The tree mechanism is not specific to four triples. Consider any ordinary XOR circuit on `n` coordinate inputs, with no constant inputs, and suppose its computed even-parity gate values are linearly independent. Odd gate values need not be distinct. Let `r` be the number of even gates.

Make one vertex for each ordinary input and each odd gate occurrence. Each even gate joins its two odd parents by a helper-creation edge. Each odd gate joins its odd parent to its new result by an edge labelled by its even operand. These are all possibilities: an even gate reading two even values would violate the assumed independence, and parity determines the operand types of an odd gate.

This graph is a forest with `n-r` components. Odd gates append vertices. Every even gate joins different existing components, since an old path would express its value as a sum of earlier even gate values. This proof uses actual gate chronology and does not require a classification of odd masks or circuit topologies.

Now attach additional formal output ports only to even-valued wires and transpose literally. Interpret those ports as source labels in the reversed computation. Suppose the reversed designated targets, corresponding to the ordinary circuit's input vertices, all have source parts in a fixed subspace `D`; the reversed ordinary inputs have zero source parts. For every forest edge use the full adjoint flux defined above. An odd vertex's boundary is its reversed designated target when it was an original input, plus any reversed ordinary inputs from terminal output ports at that vertex. At other odd vertices the boundary consists only of such terminal ordinary inputs. All boundary source parts therefore belong to `D`.

Cutting any forest edge and summing the vertex equations on one resulting component expresses its flux as a sum of boundary values. Every flux has source part in `D`. An odd-valued wire carries an adjoint partial sum of these fluxes and ordinary terminal inputs, with no extra source ports. Consequently **every odd-valued wire has a reversed full value whose source part lies in `D`**.

This principle concerns a particular marked circuit and its literal transpose. It does not identify equal-valued wires across unrelated implementations, assume that clean source parts are physically supplied separately, or grant early availability of a later adjoint. The special seven-gate mirror above has `n=4,r=3`, so the forest is one tree. Its additional reader-count restriction supplies the stronger chain conclusion.
