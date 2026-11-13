# Second review of the hidden-operand theorem

2026-11-13. Independent machine proof review of [the theorem and application](../directions/independent.md). No search, circuit enumeration, or finite-family check was run.

## Operand graph

The three hypotheses used in Theorem H suffice. For an event with result support \(W\), any cancelled block \(q\) lies outside \(W\). The maximal-clique property supplies \(d\in W\) with no co-occurrence edge to \(q\). Both operands carry \(q\), and some operand carries \(d\). That operand is nonlocal. The property used here is maximality as a clique in the co-occurrence graph, which is stronger than being maximal among the listed windows.

For a fixed nonlocal operand \(a\), some \(q\in B(a)\setminus W\) exists because \(W\) is itself a window. Every local partner of \(a\) for a selected event carries \(q\), because the result vanishes outside \(W\). The same choice of a nonadjacent \(d\in W\) then excludes \(d\) from every such partner. All these event results have the same projection \(a|_d\). The blockwise-distinctness hypothesis limits the local-partner events to one per nonlocal operand. This argument does not need to choose a different cancelled block for each event.

For the other events, put one edge between the two physical nonlocal operands. A loop would give the zero value, contrary to the prescribed support. The sum of labels on any cycle is zero, including a two-edge parallel cycle. This gives a forest under linear independence, with \(h-c\) edges including the isolated vertices in \(h,c\). The at most \(h\) local-partner events give \(t\le2h-c\).

The rank-defect extension follows from the binary incidence matrix. Its rank is \(h-c\), so its kernel has dimension \(m-h+c\) for \(m\) nonlocal/nonlocal edges. Extending each kernel vector by zeros on the local-partner events gives an injective map into the space of relations among all selected values. Thus \(m-h+c\le t-r\), and combining with the local-partner count yields \(r\le2h-c\). The same proof works with any valid uniform local-partner capacity \(\lambda\).

## Sharp family

The displayed family has the claimed supports and dependencies. The designated values \(q+v_i\) and \(q+z_i\) force both local operand chains to remain. The only nonlocal gates are \(a_i=q+v_i+u_i\). Their readers are selected outputs and all such readers cancel block \(C\), so exactly these \(h\) gates are hidden. The two-block projections are distinct, by the unit coordinates on \(B\) and the independent \(v_i,z_i\) coordinates on \(D\). In any relation on the selected events, each \(z_i\) singles out its corresponding \(y_i\). The remaining relation is a sum of tree-edge incidence vectors, which vanishes only for the empty edge set. Hence equality holds. The construction also works with any forest in place of the tree, giving \(t=2h-c\) for any prescribed component count \(1\le c\le h\).

## MixColumns and combined class bounds

The co-occurrence graph has the 8-cycle and chords \(7\!-\!1,7\!-\!2,7\!-\!3,7\!-\!4\). The two-block windows for sheets 0 and 2 extend to triples. The windows for sheets 1, 3, 4, 5, 6, and 7 are maximal cliques. Every row in one sheet has its full window, the four own masks \(E_c\) are distinct, and the four adjacent-pair masks \(s_c\) on each other block are distinct. Independence follows already on the own block. Its row matrix is \(I+J\), where \(J\) is the \(4\times4\) all-ones matrix and \(J^2=4J=0\) over GF(2). Thus \((I+J)^2=I\).

An input's singleton block is covered by a window. A nonlocal operand is therefore a gate. It cannot have a path to any output with no later event, by monotone support along the continuation, so it belongs to \(Q\) or \(E\setminus F\). Distinct physical nodes each contribute once to \(H=|E\setminus F|+|Q|\). The lower bound on \(H\) is valid with additional visible or hidden events. The numerical class bounds further require that the selected output events be the **complete** visible set and should explicitly assume a reduced circuit, as in the historical Theorem V and the joint-repair application.

A maximal-window output event has \(J(f)=\{j\}\), including the trivial path to itself. Any other sheet reached without a later event would need a window containing its full support, and the MixColumns windows are distinct with no strict enlargement of this maximal clique. Therefore the penalties from Theorem V apply as displayed. Joint reconstruction saves at least one counted in-block gate per disjoint pair of selected own triples. Pairing gives \(\lfloor t/2\rfloor\), while the operand graph gives \(\lceil(t+1)/2\rceil\). Their sum is \(t+1\) for even \(t\) and \(t\) for odd \(t\). Using only the forest estimate, the bounds for \(t=1,2,3,4\) are:

| Sole visible sheet | Lower bounds in order |
| --- | --- |
| 1 | 82, 82, 80, 80 |
| 3 | 82, 81, 78, 77 |
| 4, 5, 6, 7 | 83, 83, 81, 81 |

These counts concern the stated event profiles. Separate applications to multiple sheets can count the same hidden operand and cannot be summed without a cross-sheet reuse argument.

## Componentwise projection rank

Theorem HR holds with just the maximal-clique window and the common support of the selected events. On an edge of the nonlocal operand graph, the difference of the two vertex values is zero outside \(W\). Hence the outside projection is constant on each component, including an isolated vertex. It is nonzero because \(W\) itself is an output window. Since \(W\) is a maximal clique, any block of this common outside projection fails to co-occur with at least one block of \(W\), giving a nonempty separated set \(D_i\).

A local partner assigned to component \(i\) must have exactly the same outside projection as that component's vertices. For each \(d\in D_i\), it therefore meets an outside block that cannot co-occur with \(d\). Locality forces its projection on \(d\) to vanish. The projected event values for that component are consequently sums of one or two of the \(h_i\) projected vertex values. Their rank is at most \(h_i\), regardless of dependencies or repeated gate masks. The distinct physical vertex sets allow the per-component ranks to be summed. In the sharpness family, the separated set consists of \(B\) and the selected projections include its independent units \(u_i\), so this rank bound is attained.

In MixColumns, the only nonzero relation among the four adjacent-pair labels \(s_c\) is their full sum. At coordinate \(c\), zero in a relation forces the coefficients of edges \(c-1,c\) to agree, hence all four coefficients agree. The own-block projections \(E_c\) are independent. Therefore any proper subset of a sheet's outputs is independent on each window block separately. Summing the component ranks gives \(h\ge t\) for \(t\le3\), and \(h\ge3\) for \(t=4\). With four outputs, either a split across components or separation on the own block raises the count to four.

When exactly three distinct nonlocal operands serve four selected outputs, they therefore form one component with only off-own separated blocks. The forest and one-local capacity arguments give two nonlocal/nonlocal edges and two events with one local partner. The three vertices form a path. The rank-three projection forces the three projected vertex values to be independent. The four event projections sum to zero on the separated blocks. Thus the events with a local partner attach at the path endpoints, since their projections must sum to the two endpoint projections supplied by the two edge labels. The two local partner values sum to the total of the four output rows, the parity on the own block. This describes the equality case without excluding it.

Replacing the forest estimate by the stronger profile \(h_t=(1,2,3,3)\) changes only \(t=3\) in the earlier table. For a reduced circuit whose complete visible set is the selected outputs, the resulting class bounds are:

| Sole visible sheet | \(t=1\) | \(t=2\) | \(t=3\) | \(t=4\) |
| --- | --- | --- | --- | --- |
| 1 | 82 | 82 | 81 | 80 |
| 3 | 82 | 81 | 79 | 77 |
| 4, 5, 6, 7 | 83 | 83 | 82 | 81 |

The respective starting bounds and penalties are \(83-2t\), \(84-3t\), and \(84-2t\). In each row add \(h_t+\lfloor t/2\rfloor\). No cross-sheet sum follows.
