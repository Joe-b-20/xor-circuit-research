# Marked-wire duality preserves the original entry's own mask

2026-11-13. Structural hand proof using explicit XOR and copy nodes. No search or circuit enumeration. The point is to preserve original internal wires, rather than infer internal identities from equality of output linear maps.

## The precise transfer lemma

Take a normalized ten-gate consumer for the four targets `E_c(z)+d_c`, where the `d_c` span rank three with their all-four sum as their unique relation. Suppose it has four entries. Replace each entry occurrence by its own formal input, even when actual labels repeat. Each formal input has exactly one reader, its designated entry gate.

Expand every fanout into binary copy nodes. A copy has one input and two identical outputs. An XOR has two inputs and one output. Include designated outputs as explicit terminal ports. With eight input ports, four output ports, and ten XOR nodes, the number of binary copies is six: balancing wire counts gives

    input ports + copies - XORs = output ports.

Transposition reverses all wires and swaps XOR and copy nodes. Its correctness follows locally from the transposes of `(x,y)->x+y` and `x->(x,x)`. Thus it is literally involutive on this expanded network; no reassociation is needed. The mirror has six XOR nodes, ten copies, four input ports, and eight output ports. Four outputs are the own triples, and four are the formal entry traces.

Now delete the four trace-output ports. Each is directly attached to the copy node dual to its original entry XOR, since the original formal input was read only at that entry. Suppress the resulting unary copy, but mark the surviving wire. Transposing this reduced network again returns exactly the original expanded consumer with its four entry XORs bypassed and formal input ports removed. In other words, it returns the original own projection, including its original wire positions.

Define the **ordinary derivative** of a mirror wire to be the coefficient vector at the four ordinary mirror outputs when a perturbation is injected on that particular wire. This is a wire derivative, not the derivative of every use of a signal sharing the same value. By local transposition, it is the value on that wire in the reduced reverse network. Therefore:

**Marked-wire transfer.** The marked mirror wire corresponding to an original entry carries that entry's trace, and its ordinary derivative is exactly the original entry's own mask.

The four-entry ordinary projection has six gates and computes all four triples, whose minimum is six. None of those six gates can become zero, a wire, a duplicate, or an input value, since deleting it would give a five-gate triple circuit. Consequently every original own fibre has exactly one input or non-entry root; all other nodes in that fibre are connected to earlier nodes by entries. These edges form a rooted tree. A difference between two original equal-own values is the sum of the actual labels along their fibre-tree path.

## Different even helpers cannot have equal marked-wire derivatives

Consider any six-gate ordinary circuit for the four triples, with explicit copies. Its four odd triple gates are designated outputs. Its other two gates have distinct nonzero even values, call them `p,q`: no other odd non-input mask exists on four coordinates, and a duplicate or zero would contradict the six-gate minimum.

Every reader of an even helper is an odd designated target gate. Reading two even helpers would produce a third even gate; reading the same helper twice would produce zero. Neither is possible. Moreover `p` and `q` cannot have a common reader, since that reader would XOR both and would be even.

Let `kappa_j` be the full ordinary adjoint of the designated target gate `E_j`. These four vectors are independent: in topological order of the designated targets, each contains its own terminal-output unit and can contain only later output units. Their matrix is unitriangular.

A nonzero-derivative wire carrying `p` lies in its copy tree and feeds some nonempty subset of its readers. Its derivative is the sum of the corresponding `kappa_j`. A wire carrying `q` gives the sum for a nonempty subset of a disjoint reader set. Independence of the four `kappa_j` makes those sums different. Hence

**Even-wire separation.** No marked wire carrying `p` and marked wire carrying `q`, both with nonzero ordinary derivative, have equal derivatives.

This proof concerns actual reader subsets and their ordinary adjoints. It does not identify an entry's own mask with the full adjoint of an unmarked mirror node.

## Repeated-label four-entry consumers have no ternary return

Suppose the four actual labels are `u,v,w,w`, with `u,v,w` independent. The four traces are independent. Otherwise their rank would be three; the label map would be injective on the formal target-row space, making every trace even. Three independent even traces would require three even mirror gates in addition to the four odd triples, contrary to six gates.

The parity vector of the four traces is the sum of the four formal target rows. It is nonzero and is in the kernel of the actual label map. That kernel is generated by the two repeated-label positions. Thus precisely the two `w` traces are odd; the `u,v` traces are even. They are the mirror's two distinct even helper values.

Marked-wire transfer and even-wire separation imply that the original entries carrying `u` and `v` have different own masks. They cannot lie in the same original own fibre.

Any original zero-consumer exit adds two equal-own consumer values. Its fibre-tree path contains at most one of the unique `u,v` entries, together with zero, one, or two `w` entries. After cancellation its source value is zero, one earlier label, or the sum of two earlier labels. All labels on the path were supplied before the exit, since they were read on the entry paths to its two operands.

Therefore every exit in this repeated-label class can be recreated chronologically with at most its original one source-side gate. All source-side work can be replayed without extra gates. In the joint problem with ten consumer-bearing gates, the resulting source-only circuit supplies the four first-sheet rows and three independent diagonal labels. The augmented minimum twelve then gives at least twelve source-side gates and at least twenty-two total gates for this class.

The [specified ternary consumer](TERNARY_CONSUMER.md) instead has a three-term relation among four distinct labels. It does not contradict this repeated-label result. In that class a local ternary return is possible, although a later-label credit removes its total repair overhead. The present note does not assert that double transposition preserves arbitrary simplified internal circuit descriptions; the explicit copy network is essential.
