# Second review of the local port costs

2026-11-13. Independent machine proof review of [PORTS](../PORTS.md). No search or circuit-family check was run.

## Cancellation and transposition

The cleanup may redirect any gate with a free mask to that free value, even if that gate was produced through cancellation. In the free-neighbour model the redirect preserves the target map and can only reduce the paid count. Bypass zero operands and trim again after redirects, since an originally live signal can lose its last reader. Every ordinary coordinate still has a nonzero target column, and each newly introduced formal free-use input has one reader. All remaining gate signals have a reader or a terminal use. The last condition is needed for the \(d-1\) sum.

Give each use of a free operand its own formal coordinate, including both operands of a paid gate mixing two free blocks. Accumulating all reader adjoints in reverse topological order uses exactly \(d-1\) XOR gates for a signal with \(d\) occurrences, including terminal occurrences. Equal contributions are counted with multiplicity and may XOR to zero. A literal accumulation can keep those zero and repeated values; the lower bounds apply to such circuits. Thus no cancellation-free assumption is needed for the count \(K-4p-\tau\). The transpose gives the own triple columns, the adjacent pair columns from any ordinary neighbour, and a signal for every formal free-use trace.

For each free block independently, the matrix of its target labels factors through its own formal inputs. The span of the traces therefore contains the column space of the four adjacent pair labels, which is the full even subspace because the only nonzero row relation uses all four labels. Exactly three uses require three distinct nonzero even traces. The five-gate obstruction for the four triples remains valid even with zero values and copies: the first gate is the only available even gate in a hypothetical five-gate circuit. If nonzero, it is a pair. It can first produce only the triples containing that pair, and the two other triples would each have to read the other. If zero, it cannot produce a first new odd value. Consequently the three stated lower bounds hold with arbitrary intermediate cancellations.

## Upper bounds and scope

For the free-only construction, the own masks from \(U+b_1\), \(U+V\), \(V+W+b_3\), and \((b_0+b_2)+W\) are \(E_0,E_1,E_2,E_3\). Their free masks are \(\alpha,\alpha+\beta,\beta+\gamma,\gamma\), respectively, giving \(s_0,s_1,s_2,s_3\). There are \(3f+1\) preliminary gates and six final gates. Each addition preserves every nonzero block of its operands.

With ordinary neighbours, the four \(U\) values have different own coordinates and different ordinary coordinates on each neighbour. The prescribed four pairwise joins leave each involved block nonzero, and the subsequent own-coordinate additions give the four own triples. On every free block the pairwise joins give the same four labels just verified. The four chains cost \(4p+3f\) and the final joins and own additions cost eight. These identities prove attainment in the event-free class as well as the unrestricted local model.

The first free neighbour added to the bare triple problem raises the cost from six to ten. Further free neighbours cost three each, as does adding a free neighbour when an ordinary neighbour is already present. Reclassifying a first neighbour from free to ordinary costs two, and later reclassifications cost one each. Each free block is a four-coordinate block under the stated \(s_c\) convention. The result is an exact local cost for simultaneous neighbouring terms. Summing those costs in a larger circuit would require control of overlapping physical work.
