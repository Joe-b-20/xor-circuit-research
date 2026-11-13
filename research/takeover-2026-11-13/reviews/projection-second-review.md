# Second review: global projection repair

Review of `directions/PROJECTION.md`, together with the scope of `directions/JOINT.md`. No SAT, enumeration, exact gate search, computer-driven case elimination, or numerical scripts were used. This is a hand review, not formal verification. The bibliographic attribution in §5 was not independently checked here.

## Verdict

The projection-repair theorem and the inequality `G >= B + Z - X` are correct under the document's stated model: independent coordinate inputs, XOR gates, a partition into nonempty blocks, and nonzero designated output values. No reducedness or liveness assumption is required. The proof handles partial cancellation inside a surviving block, repeated values, zero-valued internal gates, dead gates, output nodes reused later, repeated output designations, and arbitrarily interacting events.

The MixColumns conclusion is conditional on an event-free lower bound of 84. The separate local case analysis underlying that 84 was not re-proved in this review; the earlier visible audit traced its interface but did not independently certify every case. Calling 84 simply an independently audited bound risks implying a stronger verification result than this review establishes. Prefer “using the recorded event-free bound 84, conditional on its underlying local theorem.”

## Induction and edge cases

For a requested pair `(v,S)`, reverse propagation maintains `S subset B(v)`. Thus `P_S(a_v)` is nonzero on every block of `S`, and exactly on those blocks. At a gate `v=a+b`, the operands needed for its projection are exactly the already requested values `P_{S intersect B(a)}(a_a)` and `P_{S intersect B(b)}(a_b)`; empty intersections mean zero. The original topological order provides them before `(v,S)`. If just one is nonzero, the output is its wire; if both are nonzero, XOR them once. Both cannot be zero because the request value is nonzero. Therefore at most one gate per productive physical-node/request pair suffices.

If the new XOR cancelled a whole block `d`, its operand parts there would be equal and nonzero, forcing the original value `a_v` to vanish on `d`. But `d in S subset B(v)`, a contradiction. Partial cancellation within a block is allowed: for example, `(x_1+x_2)+x_1=x_2` has two nonzero unequal block operands and remains an event-free gate. The proof correctly excludes only equality of the entire nonzero block components.

The argument uses actual values, not distinctness or gate liveness. An internal zero-valued gate has empty block support and receives no nonempty request, and its projected zero never needs to be materialized. Duplicate nonzero values at different physical gates are not assumed shared; the claimed bound remains an upper bound. A gate whose two physical operands coincide cannot receive a nonempty request because its output is zero. Dead gates receive no output-derived requests. If a designated output is an input, its requested projection is the input itself. Multiple physical paths or output designations making the same request at a node are correctly deduplicated.

A later event can remove blocks produced by an earlier event, and a still later gate can reintroduce them. Intersecting with every intermediate node's actual support ensures that each request propagates only through blocks surviving at that point. The topological induction does not assume an order between different output paths or independence of events, so these interactions require no additional case split. The equivalent path description follows by induction: each request is the nonempty intersection of supports along at least one actual directed path to a designated output, and every such nonempty intersection survives each reverse-propagation step.

For each gate, the identity `q(v) = 1 - [q(v)=0] + max(q(v)-1,0)` gives `K=G-Z+X`; because the constructed event-free circuit has at most `K` gates and an event-free lower bound is `B`, `B<=K` yields the stated inequality. A cheaper alternative event-free repair does not invalidate this inequality, but positive `X-Z` does not by itself measure realized savings or prove that cancellation is useful.

The no-event control also holds for unreduced circuits in this model: support can only grow along each non-event edge, so a live node receives only its full support. No zero-valued gate can be created in an event-free circuit from nonzero coordinate inputs, because its two operands would have to be equal and nonzero. Hence each live gate has two nonzero operands and its one request is productive; dead gates have no requests.

## Scope of the joint-piece saving when all visible events are outputs

In the case `R=empty` and all visible events are designated outputs, `G=|F|+H`, so the 83-form joint inequality

    G >= 83 + H - sum_f (in(f)-1) + Delta_83

reduces exactly to

    sum_f in(f) - Delta_83 >= 83.

It is a lower bound on the charged gates of the chosen event-free reconstruction, independent of the original circuit size `G` or hidden work `H`. Thus even a positive shared-piece saving is not, by itself, a new lower bound on the original circuit. The 84 form similarly reduces to `sum_f (in(f)+x(f)) - Delta_84 >= 84`.

For the 32 distinct MixColumns output values in this all-output case, the eight own-block sets each consist of four triple sums. Use the explicit two-pair/six-gate construction of `JOINT.md` for each sheet and keep the other pieces private. For each sheet other than 3, the four output chains initially contribute 12 family gates, reduced by two to 10. For sheet 3 they initially contribute 16, reduced by two to 14. The reconstructed total counted in the 83-family decomposition is therefore `7*10+14=84`. The resulting necessary inequality is just `84>=83`, regardless of `G`. This concrete calculation confirms both that the reconstruction really saves charged gates and that the saving alone does not control the original hidden work.

Joint sharing can still be informative when retained work is present or when one independently constrains `H`: then it lowers the maximum family contribution assigned to the visible-event reconstructions and forces more retained gates. The result in `JOINT.md` correctly calls its improvement circuit-dependent; it would benefit from explicitly stating the cancellation above and this all-output control.
