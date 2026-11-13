# Independent review: matching of three tight consumer entries

Hand review of `../ENTRY_MATCHING.md`. No SAT, exhaustive enumeration, circuit search, exact-gate search, or computer-driven case elimination was used. This is not formal verification.

## Verdict

The flexible-adjoint argument, the entry-edge matching conclusion, and the one-root exit bypass are correct under their stated hypotheses. They are a sufficient condition for avoiding a three-term exit, not an unconditional result for every ten-gate consumer. In particular, the note properly leaves fibres with an additional non-entry root and four-entry consumers open.

## Flexible accumulation

Give each of the three entries its own formal input. The actual free labels are independent, because they span the three-dimensional target free-part space. Their label map is therefore injective on all three formal coordinates. The four formal target masks have rank three and their total sum is zero. Consequently the three formal-input adjoints are independent nonzero even four-bit traces.

The literal reverse accumulation uses `10-3=7` gates, regardless of the order in which the reader and terminal contributions at a node are combined. Its four ordinary-input adjoints are the distinct odd non-input triples. The three independent even traces are distinct non-input signals, so these seven values already consume all seven gate outputs in any literal transpose. A zero signal, if treated as freely available, does not help to represent a nonzero even pair sum.

Every reader contribution to a node is available before the node is accumulated in reverse topological order, as is any terminal contribution. Thus any chosen subset of at least two contributions can be XORed first while preserving the total `d-1` accumulation-gate count; a singleton is already a signal. If the span of the contributions contained two independent nonzero even vectors, the span would also contain their sum. The only possible nonzero even signals are the three independent entry traces, and the sum of two different traces is not one of those three. Arranging for the corresponding subset sum to be a signal would contradict the seven-gate budget. This reasoning uses the original DAG and one transpose; it does not assume that an internal adjoint becomes the same node after transposing again.

## Matching and the exit consequence

If two entry gates read the same nonfree operand, their two distinct entry traces occur as reader contributions to that operand; accumulating the two first would create the forbidden even pair sum. If one entry reads another, the earlier entry's total adjoint is its own trace and the later entry contributes its distinct trace. The nonempty remaining contributions sum to their forbidden pair sum; they can be accumulated first. Hence no two entry edges share an endpoint, either as siblings or in a chain.

In a fibre with one non-entry root, every entry must connect to that root: an entry cannot have another entry as its parent. The matching property then permits at most one entry. Any two different physical signals in the fibre are its root and that single entry, whose difference is exactly the actual free label read by the entry. The label was available before the entry, and therefore before any later exit reading the two signals. Replacing that exit with the already supplied label preserves causal availability and uses no extra source gate.

If three distinct nonzero even own masks occur, they and the four distinct triple masks require seven first-occurrence non-entry gates. The ten-gate circuit has exactly three entries, so these seven first occurrences exhaust its seven non-entry slots. Every other nonunit fibre is absent, each present nonunit fibre has one first root, and a unit fibre has its ordinary input as its sole root. Thus the one-root hypothesis holds. Without this exhaustion, a second non-entry root in a fibre is not ruled out by the matching argument, and no conclusion for that profile is claimed.
