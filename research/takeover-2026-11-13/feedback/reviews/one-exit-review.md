# Review of the specified one-exit separation

2026-11-13. Independent machine proof review of [ONE_EXIT](../ONE_EXIT.md). The direct verifier was run on the two specified circuits only. No circuit search or finite-family checks were run.

## Constructions and unrestricted lower bound

The four consumer prefixes and one exit in the feedback circuit have the displayed masks. The exit cancels exactly the one-bit consumer block, and the private attachments introduce no event. The alternative builds the common three-coordinate source sum in two gates and computes the four consumer prefixes separately. It has no consumer-block content in the first-side cones.

The direct verifier requires both gate operands to be currently available, rejects zero and repeated values, checks all eight output masks and their rank, and traverses the actual ancestor graph to check liveness and the no-feedback property. It detects an event by equality of two nonzero operand components on a block. The run reported 21 gates and one event for the feedback circuit, and 22 gates and no events for the no-feedback circuit. The verifier checks only these two explicit constructions and uses row reduction on their specified output masks.

Each of the sixteen private coordinates still occurs in its designated output when selected for deletion. The same output retains its fixed non-input base value, so a live gate reads that private coordinate. After restriction such a reader becomes its other projected operand or zero. Copy and zero bypasses and pruning delete it without increasing the gate count. This counts one physical deletion in each successive restricted circuit, even if some coordinates shared the same direct reader before any restrictions. The final five base values are distinct non-input masks and cost at least five gates. This gives the unconditional \(16+5=21\) lower bound.

## No-feedback lower bound

First remove the eight consumer-side private coordinates. The proof uses only zero/copy bypasses and pruning at this step. Each redirect goes to an ancestor of the deleted gate; it does not choose an unrelated equal-value wire. Therefore the new first-side cones stay inside the original first-side cones. Restriction leaves the consumer bit unchanged. Every surviving first-side ancestor consequently still has zero consumer component, which is the needed no-feedback condition.

In the restricted circuit the first-side cone can be analyzed alone. Removing its eight private coordinates costs at least eight gates and leaves the weight-three source sum, which needs at least two gates. Thus the first-side cone has at least ten gates. The four distinct consumer base outputs each have nonzero consumer bit and are disjoint from that cone. Adding four output gates and the eight gates lost in the first restriction gives 22. This proof does not require the no-feedback circuit to be event-free.

## Boundary and scope

The output rows are independent by their private coordinates and have weight five. A single row and its five coordinate inputs give a boundary relation of length six. For two first-side rows, four private coordinates survive. For a cross-side pair, two first-side private coordinates, at least one consumer-side private coordinate, and the consumer bit survive. Of the consumer-side pairs, only those involving the unique one-tag output and one of the two-tag outputs have just three private coordinates, and their different source masks give another surviving coordinate. Three or more selected outputs retain at least one private coordinate per output. In all cases the number of selected outputs plus the weight of their XOR is at least six. This proves the boundary distance independently of the verifier.

The optional extra free block can be set to zero without changing any target or the consumer bit, using ancestor-only bypasses, so it cannot invalidate the lower bounds. The example refutes a general cost-preserving no-feedback normalization even with one one-bit exit, four outputs per side, and the stated boundary properties. It has different row structure from the joint MixColumns map and does not resolve that map.
