# Hidden operands of internal visible events

2026-11-13. Hand arguments and explicit symbolic constructions extending Theorem HR. No circuit searches or finite-family checks were run.

Independently machine-reviewed in [the internal-event review](reviews/internal-review.md);
not formally verified or human-certified. A direct check of the prescribed MixColumns
construction below gives 149 distinct non-input live gates, one internal visible event,
and no hidden gates (`check_continuation.py`, `check-results.json`). No circuit search was used.

## Exact window tests

Use the input blocks, output windows, and visibility of [Theorem HR](../directions/independent.md) and [VISIBLE §3](../../structure-2026-11-11/visible/VISIBLE.md). A local value is supported inside some output window. Include a singleton window for any input block not covered by an output window. An event is a gate whose operands cancel an entire nonzero block. An event is visible if it reaches a designated output along a path with no later event. A nonlocal operand is a physical gate with no event-free path to any output, so it contributes one to the hidden count \(H=|E\setminus F|+|Q|\).

Let \(R\) be an event's surviving block support and \(C\) its cancelled block set. The two operands carry the same nonzero component on every block of \(C\). If both operands are local, two windows containing \(C\) must cover \(R\). This test uses the actual windows even when all the blocks under consideration are pairwise adjacent.

The condition is exact for algebraic feasibility. Given a value of support \(R\), a nonzero mask of support \(C\) disjoint from \(R\), and two windows containing \(C\) whose union covers \(R\), partition \(R\) between the two windows. Give each operand the part of the event value in its assigned blocks and add the same cancelled mask to both. Both operands are local, their sum is the prescribed value, and the cancelled blocks are exactly \(C\). This construction asserts feasibility of the two masks. Producing those masks in a particular circuit can impose additional costs.

## Component rank with an enclosing window

Choose any block set \(S\) contained in a window. Select events with values supported inside \(S\), possibly on different proper subsets of \(S\). Include in the argument those events that have at least one nonlocal operand. The exact window test can certify membership using the cancelled set \(C\). It can also be applied with the support of the common operand mask outside \(S\), which is a subset of \(C\).

Make a graph on the distinct physical nonlocal operand gates. Put an edge for each selected event with two nonlocal operands. Assign each selected event to the component containing its nonlocal operand. Let \(A_i\) be the vertices, \(T_i\) the assigned events, and \(h_i=|A_i|\) in component \(i\). Vertices have a common mask \(z_i\) outside \(S\), because the event value on each connecting edge is supported inside \(S\). This mask is nonzero because every vertex is nonlocal and \(S\) is contained in a window. Define the exact separated set by

$$
D_i=S\setminus\bigcup_{\substack{W\text{ an output window}\\ B(z_i)\subseteq W}}W.
$$

An empty family of windows gives \(D_i=S\). For comparison, pairwise separation only includes a block \(d\in S\) if some \(q\in B(z_i)\) is not adjacent to \(d\). Such a \(d\) also belongs to \(D_i\).

If \(f\in T_i\) has a local partner, that operand carries the full \(z_i\) outside \(S\). Its containing window therefore meets the condition in the union and it vanishes on \(D_i\). The projection of any assigned event on \(D_i\) is thus the sum of the projections of its one or two nonlocal operands. With \(P_{D_i}\) denoting block projection, this proves

$$
H\ \ge\ \sum_i h_i\ \ge\ \sum_i \operatorname{rank}\{P_{D_i}(\operatorname{val}(f)):f\in T_i\}.
$$

The projection \(D_i\) captures all linear constraints that follow solely from locality and the fixed outside mask. The possible restrictions to \(S\) of local partners span the entire coordinate space on \(S\setminus D_i\). For each coordinate unit \(e\) in that space, the mask \(z_i+e\) fits a window containing its block and the signature support. Conversely every admissible partner is zero on \(D_i\). Any linear map on \(S\) that annihilates all those possible restrictions therefore factors through \(P_{D_i}\). This assertion uses all algebraically possible partners. The realized operands or a more restrictive cancellation pattern may support additional constraints.

The bound also holds for nonvisible selected events, since nonlocality of the operand itself excludes an event-free path to an output. Selecting visible events allows the count to be used with the reconstruction inequalities. Multiple uses within the chosen graph share the same vertex. A separate application with a different enclosing set can reuse those vertices. Adding estimates for different enclosing sets requires an argument that controls that overlap.

Two refinements use the graph as well as the projections.

- Append a bit to each projected event, equal to one for a local-partner event and zero for a two-nonlocal-operand event. The resulting vectors are sums of the augmented vertex vectors \((P_{D_i}(\operatorname{val}(a)),1)\). Their rank still bounds \(h_i\) from below and can exceed the ordinary projected rank. If all projected event values sum to zero for some combination containing an odd number of local-partner events, the augmented rank is one larger.
- When a component has no assigned local-partner event, use the full event values. Their coefficient vectors on the vertices all have even parity, so their rank is at most \(h_i-1\). Thus such a component forces \(h_i\ge1+\operatorname{rank}\{\operatorname{val}(f):f\in T_i\}\), including when \(D_i\) is empty. One may take the larger of this and the projected-rank estimate in each such component.

## Sharpness with proper-support internal events

Use three blocks \(A,C,D\), each with independent coordinates. Take \(u_i\) in \(A\), \(q\) in \(C\), and \(r\) in \(D\). Make \(a_i=q+u_i\) for \(1\le i\le h\). For the edges \(ij\) of any tree on these vertices, make \(f_{ij}=a_i+a_j=u_i+u_j\) and designate \(f_{ij}+r\) as an output on \(\{A,D\}\). Also designate the input \(q\) as an output with singleton window \(\{C\}\). For \(h\ge2\), the \(a_i\) are precisely the \(h\) hidden gates. Each \(f_{ij}\) is a proper-support internal visible event and has two nonlocal operands. Every path out of an \(a_i\) toward an output passes through an \(f_{ij}\). The \(h-1\) event masks are independent by successively removing tree leaves. This attains the full-rank-plus-one estimate.

The exact-window projected bound is attained in a reduced circuit where the pairwise separator gives no credit on the event support. Use independent \(u_i\) in block \(A\) and single inputs \(b,c,r,w\) in blocks \(B,C,L,D\). Make \(z=b+c\) and designate \(\ell=z+r\), \(b+u_1\), and \(c+u_1\) as outputs on \(\{B,C,L\}\), \(\{A,B\}\), and \(\{A,C\}\). For each \(i\), make
\[
a_i=z+u_i,\qquad f_i=a_i+\ell=u_i+r,\qquad y_i=f_i+w.
\]
Designate \(y_i\) on \(\{A,L,D\}\). The only hidden gates are the \(a_i\), whose support \(\{A,B,C\}\) lies in no window. The internal visible events \(f_i\) have support \(\{A,L\}\), strictly inside \(S=\{A,L,D\}\). Each is assigned to its own isolated vertex. The signature has support \(\{B,C\}\), and only \(\{B,C,L\}\) contains both blocks. Thus \(D_i=\{A,D\}\) and the projection of \(f_i\) there is \(u_i\). The sum of component ranks is exactly \(h\). The pairwise test misses both \(A\) and \(L\), since each is adjacent to both \(B\) and \(C\). Every gate has a distinct non-input value, and all gates are live.


The added bit can improve the bound even in a reduced circuit. Use \(x,x'\) in block \(A\), \(q\) in \(C\), and \(r\) in \(D\). Designate \(p=q+x\), \(k=r+x'\), and \(b=q+r\) on their two-block windows. Make \(a=p+k=q+r+x+x'\), then \(f=a+b=x+x'\), and designate \(f+r\) on \(\{A,D\}\). The only hidden gate is \(a\), whose support meets all three blocks. For \(S=\{A,D\}\), the signature is \(q\), and the two windows containing \(C\) cover \(S\). Thus \(D_i\) is empty. The ordinary projected rank is zero, and the single local-partner event gives augmented rank one, attaining the hidden count. The exact two-window feasibility test allows two local masks here, so this count uses the observed operand wiring.

## Why proper support alone does not force hidden work

A reduced symbolic family can have arbitrarily many independent internal visible events and no hidden gates. Use \(q\) in block \(C\), independent \(x_i,y_i\) in block \(A\), and independent \(r_i\) in block \(D\). Designate the values \(a_i=q+x_i\) and \(b_i=q+y_i\) on \(\{A,C\}\). Use those gates to make \(f_i=a_i+b_i=x_i+y_i\) and designate \(f_i+r_i\) on \(\{A,D\}\). Each \(f_i\) is internal and visible. Its operands are themselves designated outputs, and every other gate is retained. Hence \(H=0\). Each event fills a proper subset of the maximal-clique window \(\{A,D\}\), with linearly independent values. The windows containing its cancelled block \(C\) cover its support.

The same obstruction occurs within an actual MixColumns circuit. In sheet 2 use \(x_i\) for own inputs (block 2) and \(z_i\) for predecessor inputs (block 1). Make

$$
u=z_0+z_1,\qquad a=u+x_1,\qquad b=u+x_2,\qquad f=a+b=x_1+x_2.
$$

Then realize the four sheet-2 outputs as follows:

- \(y_0=(a+x_2)+x_3\).
- \(y_1=(b+(z_0+z_2))+(x_0+x_3)\).
- \(y_2=((z_2+z_3)+x_0)+x_1+x_3\), with left association.
- \(y_3=(f+x_0)+(z_3+z_0)\).

These expressions have the required own triples and predecessor pairs. Only \(f\) cancels a whole block. For example the update of \(b\) in \(y_1\) changes its predecessor pair from \(z_0+z_1\) to \(z_1+z_2\) and leaves that block nonzero. Both \(a\) and \(b\) reach outputs along event-free paths. The sheet-2 gates are distinct and live. Compute all other outputs by chains over their input supports, reusing the earliest existing wire whenever a mask matches. This preserves the same operand values and does not add events. All gates created by these chains are retained after pruning. Choose the chain orders so \(f\) is not a prefix in another sheet's output chain. Outside sheet 2 only sheet 3 contains block 2, and its pair on that block can equal \(f\) only for its output with byte index 1. One can choose its input order to begin on block 3, so that chain never requests the pure \(f\) prefix. Thus \(f\) remains internal and has only its sheet-2 event-free continuation. This is a reduced live MixColumns circuit with one proper-support internal visible event and \(H=0\). It asserts no small total gate count.

## A MixColumns profile detected by the exact windows

Take \(S=\{2,3\}\) inside sheet 3's window. Suppose selected internal visible events are supported inside \(S\), reach sheet 3 without a later event, and both their operands have common outside-\(S\) support containing blocks 1 and 7. The sole output window containing both 1 and 7 is \(W_1=\{0,1,7\}\), which misses \(S\). Both operands cannot be local, and every component has \(D_i=S\). Consequently \(H\) is at least the rank of the full selected event values, or the larger sum of the component ranks. In particular, an internal event on block 2 cancelling blocks 1 and 7 must have a nonlocal operand although all three blocks are pairwise adjacent.

If these \(m\) events are linearly independent and are the complete visible set of a reduced circuit, then \(H\ge m\). In the 84 form of [Theorem V](../../structure-2026-11-11/visible/VISIBLE.md), the sheet-1 borrower penalty is zero because these values lack block 0. Each \(\kappa\) is at most 3 because no selected value meets both blocks 2 and 7. Therefore \(G\ge84-2m\), with the sharper expression \(84+m-\sum_f\kappa(f)\) available for known values. The complete-visible-set and support hypotheses are needed for this numerical class bound.
