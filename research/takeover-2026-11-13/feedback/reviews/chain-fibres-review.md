# Independent review: clean endpoints and chain fibres

2026-11-14. Independent machine review of [CHAIN_FIBRES.md](../CHAIN_FIBRES.md). This is an audit of the structural proof, not formal verification or human certification. No circuit search or enumeration was used.

**Verdict:** the odd-value tree, clean-source flux lemma, class separation, and chain description of the repeated fibre all pass under the stated target-live twelve-gate, five-entry, independent-label hypotheses. The subsequently added general odd-forest principle also passes. The proof correctly separates full physical source values from ordinary masks and makes no premature availability claim for a later clean endpoint.

## Mirror structure and class separation

The seven mirror XORs are exhausted by the four distinct odd triples and the three independent nonzero even trace masks. Therefore a helper cannot be formed from previous even helpers: such a gate would express its mask as their sum. Each helper is created from two odd values, and every ordinary helper reader is an odd target gate. Every target reads one helper and one odd value. A helper with no ordinary reader would have zero ordinary derivative on every marked wire, contrary to the nonzero original consumer mask. Thus the three nonempty reader sets partition four targets with sizes `(2,1,1)`.

The ordinary target adjoints are independent because their terminal-output coefficient matrix is unitriangular in target order. A helper-copy wire's derivative is the sum of the adjoints of its downstream ordinary readers. The reader sets for different helpers are disjoint, so equal nonzero derivatives cannot occur across helpers. This proves the strong separation of different trace classes even when an ordinary-mask fibre has multiple roots.

## The odd-value tree

Start with the four odd input vertices. Each target gate introduces a new odd vertex and its target edge. A helper-creation edge connects existing odd vertices. If those vertices were already joined by a path, summing the edge equations on that path would express the newly created helper in the span of previously created helper masks. Independence excludes this. The graph remains a forest throughout. It ends with eight vertices and seven edges, hence is a tree.

This graph uses the eight distinct forward mirror values, with each value's copy tree represented at one vertex. It does not merge the different full source values obtained as adjoints of individual copy-tree wires. Those partial adjoints are treated separately later, which is essential to the argument.

## Full fluxes after restoring the trace ports

Restore the formal trace ports, assign their actual source labels, and transpose back. A helper-creation edge carries the full adjoint of its helper, identically duplicated to the two odd parents. A target edge carries the full adjoint of its target result on the odd-parent branch. No trace port interrupts this branch because all trace values are even.

At an odd mirror input, the sum of these outgoing contributions is exactly the original consumer target `Y_i`. At an odd mirror target, its own full adjoint plus all reader contributions leaves exactly the terminal original input `z_j`. These are the stated boundary equations. Their total sum is zero because the consumer targets have ordinary sum `sum z_j` and source sum zero.

Summing vertex equations over either component of a tree cut isolates the edge flux. Every boundary source part belongs to `D`, so the edge flux's source part does too. Each original physical value arising from an odd mirror copy wire is a sum of a subset of incident reader fluxes and possibly the terminal input. There are no trace ports in these odd copy trees. Therefore every such partial adjoint has source part in `D`, even though different wire occurrences may have different full values.

In particular both helper-root adjoints and ordinary reader-end adjoints are physical consumer-bearing values with clean source parts. Their ordinary derivatives are nonzero, respectively a nonempty sum of independent reader adjoints or one target adjoint. The proof does not promote their clean source parts to separately computed source values.

## Chain fibres and the possible merge

A helper with one ordinary reader has a single reader path. A helper with two readers has two branch segments and one common trunk. The derivatives of these three segments correspond to the two singleton reader subsets and their union, and are distinct. A marked entry must lie on one such segment because its ordinary derivative is nonzero. Removing the formal trace leaves makes each segment an entry chain in the original circuit. Different helpers cannot contribute another chain of the same ordinary mask by the class-separation result.

The clean reader-end adjoint terminates a branch chain, while the clean helper-root adjoint terminates a trunk chain. There is only one non-entry accumulation in the even copy trees, namely the merge of the two ordinary reader branches. Every other non-entry root comes from an odd mirror wire, already shown clean in source part.

If the exceptional merge has the repeated fibre's mask and its trunk contains entries, it is the root of that fibre's unique chain, so the other root is clean. If its trunk contains no entries, the merge equals the clean helper-root adjoint. Therefore the repeated fibre has either two isolated clean roots or one entry chain and a clean isolated root; the chain has a clean endpoint. This proves the asserted crossing-return form.

## Timing and scope

The crossing-return expression using a clean endpoint is an identity in five independent actual labels. Causal induction supplies its unique actual-label expansion using only labels already read before the return. This justifies the final support statement, including availability of every member of an entire other class that appears in that expansion. It does not make the reference endpoint itself available early and does not, by itself, establish a chronological replay cost.

The note appropriately leaves that cost argument to a separate result. The specialized chain conclusion is not being imported into arbitrary mirror budgets.

## Added general forest principle and the four-entry core

The general principle remains valid when odd gate values repeat: vertices are gate occurrences, and every odd gate still appends a new vertex. A helper edge inside an existing component would express its full ordinary mask as a sum of earlier even gate masks, contradicting their independence. Starting with `n` input vertices and adding `r` such joining edges gives `n-r` components. The parity assumption accounts for every operand type; no constant or extra free ordinary input is implicitly allowed.

The cut proof extends component by component. Restored extra source ports attach only to even wires, so every odd-vertex boundary has source part in `D`; terminal ordinary inputs contribute no source part. An edge cut isolates its full flux, and partial adjoints in odd copy trees are again sums of those fluxes and ordinary terminals. This proves the general clean-source conclusion without an assumption about distinct odd masks or connectedness.

The chain conclusion needs the additional seven-mirror reader counts. Those counts and the clean-flux proof also hold for the eleven-gate, four-entry target core: its mirror has the same four odd triples and three independent even helpers, now with trace classes `(1,1,2)`. The number of formal trace ports does not enter the tree-cut or reader-skeleton proof. Therefore its repeated fibre also has at most one entry chain, a clean endpoint, and a clean isolated root. This extension supports the separate four-entry tail proof; it does not itself supply that proof's replay costs.
