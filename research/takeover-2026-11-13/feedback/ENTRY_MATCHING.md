# Entry edges in a ten-gate consumer with three entries

2026-11-13. Hand proof about the original consumer DAG. No circuit search or family checks. This is a sufficient condition excluding a three-term exit, with one own-fibre profile left open.

Use four own coordinate inputs \(z_0,\ldots,z_3\). The four required values have own triples \(E_c\) and source labels \(d_c\), where the \(d_c\) span a three-dimensional space \(D\) and have only their all-four relation. Count the ten physical gates with nonzero own part and treat every zero-own operand as freely supplied. An entry reads one such free operand. Suppose there are exactly three entries. Their labels \(\phi_1,\phi_2,\phi_3\) form a basis of \(D\). The ten-gate minimum implies that all ten gates are ancestors of one of the four required values in this local circuit, and that no gate can be bypassed as a duplicate or zero.

## Flexible adjoint accumulation

Give each entry operand a separate formal input, and transpose this original local DAG. The adjoint of an original signal is the sum of its reader adjoints, with a separate input contribution if it is a designated output. Every ordinary and formal input has a use, and every gate is live. Thus any order of binary accumulation at each node gives a transpose with \(10-3=7\) gates on four inputs. The four ordinary input adjoints are the four distinct odd triple sums.

For each entry \(i\), its adjoint is the influence trace \(\xi_i\) of its formal input, because the formal input is read just once. The free-label basis is independent. Applying it to the formal target free masks gives the \(d_c\), so the formal masks have rank three and total sum zero. Consequently the traces \(\xi_1,\xi_2,\xi_3\) are independent nonzero even masks. They and the four odd triples exhaust the seven gate values of every literal transpose. In particular its only nonzero even masks are those three traces. Any subset of reader and terminal contributions at a node can be accumulated first, and its sum is then a signal of that transpose. A singleton is already an available contribution. Thus the span of all contributions at any original node contains at most one independent even direction: two independent even masks in that span would be two of the \(\xi_i\), and their sum is not any of those three independent masks. The subset giving that sum could be accumulated first, a contradiction.

## Entry edges are a matching

Two entries cannot read the same nonfree operand. Its adjoint has both entry traces as contributions. Summing those first would give a nonzero even pair sum outside the allowed trace set.

An entry cannot read another entry as its nonfree operand either. If entry \(j\) reads entry \(i\), then the adjoint \(\xi_i\) of the latter contains the contribution \(\xi_j\). The sum of all its other contributions is \(\xi_i+\xi_j\). Those other contributions are nonempty because the traces differ. Summing them first again gives a forbidden even pair sum. These arguments use the same original DAG throughout; they do not identify any node with the adjoint of a second transpose.

Join each entry to its nonfree operand by an edge. The endpoints have the same own mask, and the edge records the addition of its actual label. The preceding restrictions imply that no two such edges share an endpoint. Thus these edges form a matching within each own-mask fibre.

## Consequence when every fibre has one root

Suppose every own-mask fibre has just one node other than entries, counting each ordinary input as the root of its unit fibre. Within a fibre, every entry edge then joins an entry to that root. By the matching condition each fibre has at most one entry. Consequently two different signals of the same own mask differ by one actual entry label, rather than the sum of three independent labels. If those signals are the operands of a zero-own exit in the original joint circuit, this one label was supplied before the entry and hence before the exit. Such an exit can be bypassed by the earlier supplied label in source-only replay.

In particular the one-root hypothesis holds if the circuit contains three distinct nonzero even own masks. They and the four required triples require seven distinct first-occurrence non-entry gates, exhausting the seven non-entry slots. The argument does not cover a fibre with a second non-entry root, or a four-entry consumer. It proves no unconditional exclusion of a three-term exit in a ten-gate consumer.
