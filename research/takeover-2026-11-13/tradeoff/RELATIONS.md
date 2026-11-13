# Relation capacity of physical even gates

2026-11-13. Hand proof extending the one-crowded-coset count in [INTERFACES](../compatibility/INTERFACES.md). No search or finite-family checks. The inequalities constrain individual supplied interfaces without changing the joint or unrestricted MixColumns lower bounds.

## A count for a reduced circuit

Consider a reduced XOR circuit with ordinary coordinate inputs, all odd under a fixed linear parity, and a free subspace on which that parity vanishes. Assume every counted gate has nonzero ordinary part. An entry reads a free operand. Let \(G\) be the number of gates and \(\tau\) the number of entries. Let \(O\) be the odd values of physical gates and ordinary inputs, and \(H\) the even physical gate values. These are sets of distinct values because the circuit is reduced. For \(h\in H\), write
\[
m_O(h)=|\{\{u,v\}\subset O:u+v=h\}|.
\]
Let \(T(H)\) count unordered triples of distinct elements of \(H\) whose sum is zero, and write \(e=|H|\), \(d_H=\dim\operatorname{span}(H)\).

Every non-entry gate produces an unordered relation of one of two types. It can use or produce the even value in a relation \(\{h,u,v\}\) with \(u,v\) odd, or it can produce an even value as the sum of two physical even values. None of these relations contains zero or repeats an operand, since the gate has nonzero ordinary part and the circuit is reduced. In a fixed relation at most one value can be computed from the other two, by topological order and uniqueness of nodes. Consequently
\[
G-\tau\ \le\ \sum_{h\in H}m_O(h)+T(H).
\]

There is a separate bound on the number of actually used even-only relations. The even values produced by adding two physical even values lie in the span of the even values produced by other means, by induction on gate order. Thus at least \(d_H\) even gates must be produced by other means, and
\[
G-\tau\ \le\ \sum_{h\in H}m_O(h)+\min\bigl(T(H),e-d_H\bigr). \tag{1}
\]

These statements distinguish actual even physical gates from available free masks. An odd gate that adds an even free mask is an entry and is absent from the left side. An even physical gate can itself be an entry and still participate in relations at later gates.

## Rank of the available equations

Regard each physical nonfree node as a separate formal coordinate, even when its actual mask is a linear combination of other masks. The equation for a non-entry gate has ones at its result and two operands. These gate equations are linearly independent: in a nonempty combination, the latest result among the chosen gates occurs only in its own equation. Consequently \(G-\tau\) is bounded by the **rank** of all available three-node relations, which can be smaller than their number.

There is an exact graph expression for that rank. Use the odd values as vertices and put one edge \(\{u,v\}\) whenever \(u+v\in H\). Give that edge the colour \(h=u+v\). Let \(\partial\) be the binary vertex-edge incidence map and \(\chi\) the map from edge coefficients to the parity of their occurrences of each physical even value. Thus an odd-pair relation has formal vector \((\partial e,\chi e)\). Let \(Z\subseteq\mathbb F_2^H\) be the span of the formal even-only triple relations. Include isolated odd vertices in the graph, and let \(c_O\) be its number of connected components. Then
\[
\operatorname{rank}(\text{available three-node relations})
 = |O|-c_O+\dim\bigl(Z+\chi(\ker\partial)\bigr). \tag{3}
\]

Indeed, projection of the relation span onto the odd coordinates has image \(\operatorname{im}\partial\) and rank \(|O|-c_O\). Its kernel consists exactly of the even vectors obtained from even-only relations and from edge combinations in the cycle space \(\ker\partial\). This proves (3). In particular any cycle whose colours occur with even multiplicities gives a formal dependence among its odd-pair relations. A four-point affine plane of odd values with edges along two independent physical even directions gives a four-cycle with alternating colours. The four equations have rank three, since their sum is zero and a proper nonempty subset of the cycle edges has nonzero incidence. The dependence persists if the graph contains other edges or other colours.

A useful upper bound follows from the evaluation map \(M_H:\mathbb F_2^H\to\operatorname{span}(H)\) that sends each even coordinate to its actual mask. The even-only relation vectors are in \(\ker M_H\). For a cycle, evaluation of its colour vector equals the sum of the odd endpoint values, which is also zero. Hence \(Z+\chi(\ker\partial)\subseteq\ker M_H\), and
\[
G-\tau\ \le\ |O|-c_O+e-d_H.
\]
Equations (1) and (3) use different information. Pair counts bound the possible edges, whereas the graph expression removes dependencies among the equations even when every individual pair sum is present.

If there are n ordinary coordinate inputs, then `G=|O|-n+e`. Rearranging the last
inequality gives the useful entry requirement

    tau >= c_O + d_H - n.

Thus the number of connected components of the odd-value relation graph and the rank
of the physical even values jointly constrain entry cost. This uses the actual relation
graph, not just the span of the target labels. Unused ordinary inputs, if retained in
the notation, add one isolated component and one input and do not change the bound.

## Coset capacities for the four-row producer

Specialize to the first-sheet producer with \(U_c=(E_c,s_c)\), parity of the ordinary part, and even free masks actually used. This includes every ten-gate producer by the parity confinement in INTERFACES. Define \(\rho(\beta,\alpha)=\beta+\alpha\). The zero residue on the space with even free part is the clean diagonal \(D\).

The eight named odd values \(N\), consisting of the four own inputs and the four required outputs, occupy the eight odd residues, one each. Their only nonzero linear relation is their total sum. Hence a fixed nonzero value has at most one representation by a named pair. Let \(a_r\) count the odd non-output gates at odd residue \(r\), so \(b_r=1+a_r\) is the total odd population there. Write \(A=\sum_r a_r\).

For \(h\in H\) of residue \(s\), translation by \(h\) pairs values in \(O\) into disjoint unordered pairs. If \(s=0\), both members lie in the same residue class, giving
\[
m_O(h)\le \sum_r\left\lfloor\frac{b_r}{2}\right\rfloor.
\]
For \(s\ne0\), group the eight odd residues into unordered pairs \(\{r,r+s\}\). A match between their fibres uses at most the smaller population. Also, every representation except possibly one named pair must contain a helper, and disjointness allows each helper at most once. Therefore
\[
m_O(h)\le \min\left(1+A,\ \sum_{\{r,r+s\}}\min(b_r,b_{r+s})\right).
\]
These bounds cover arbitrarily many populated odd cosets. They depend on the physical even values through their residues.

There is a collective bound for the clean even gates. Let \(H_0=H\cap D\), \(k=|H_0|\), and \(D_0=\operatorname{span}(H_0)\). For an odd residue \(r\), let \(b_{r,L}\) count the odd values of that residue in each affine coset \(L\) of \(D_0\). A pair whose sum belongs to \(H_0\) must lie in one such coset, and a given pair has just one sum. Each possible sum separately uses a disjoint matching in that residue. It follows that
\[
\sum_{h\in H_0}m_O(h)
\ \le\
\sum_r\min\left(
k\left\lfloor\frac{b_r}{2}\right\rfloor,\
\sum_L {b_{r,L}\choose 2}
\right). \tag{2}
\]
Thus both the physical clean count and the actual clean span can reduce the permitted relation capacity. No free representative of \(D\) is being charged as a physical clean gate.

For example, a compact bound without the finer populations follows because any same-residue pair uses a helper, while a nonzero-residue even value permits at most one named pair. Equation (1) implies
\[
G-\tau\ \le\ eA+(e-k)+(e-d_H).
\]
The separate formula (2) is stronger when clean directions connect only small groups inside a crowded residue.

## Odd residues reached without an entry

A complementary restriction uses the whole even span \(V=\operatorname{span}(H)\). An odd non-entry gate must add a physical even value to an earlier odd value, so it stays in the earlier odd value's affine coset of \(V\). A \(V\)-coset containing a required odd output and no ordinary input must therefore contain an odd entry. Otherwise no odd value in that coset can appear first.

This origin constraint has a rank version. Partition the eight named values into their occupied \(V\)-cosets, and let \(m\) be the number of groups. The within-group differences lie in \(V\). Before mapping formal coordinates to the named values, they span the direct sum of the even coefficient spaces of the groups, of total dimension \(8-m\). The only nonzero relation of the named values is their total sum. Its coefficient vector belongs to this direct sum exactly when every group size is even. Therefore
\[
d_H\ \ge\ 8-m-[\text{every named group has even size}].
\]
This rank bound and the entry count apply even if two named values in the same group cannot be joined by a single physical even gate.

## A consequence when the producer has no odd helper

Suppose a ten-gate first sheet has no odd non-output gate. Each required output has a distinct own triple that has never appeared in any earlier odd node, since the only other odd nodes are own units or other required outputs. Thus no output gate is an entry. Every output uses a physical even gate, and its odd operand and odd result are a named pair.

These four output gates require four different physical even values. Indeed, a named pair has a unique sum, two different named pairs cannot have the same sum, and one pair can account for only one physical gate. Each of the four sums has nonzero residue because the two named endpoints have distinct residues. The six even gates in the circuit therefore include at most two clean diagonal values. In particular a ten-gate producer with no odd helper cannot supply a rank-three clean diagonal. This conclusion concerns the specified producer class; it gives no cap of two when odd helpers are present.

The general inequalities leave open whether the remaining helper populations and actual entry labels can coexist in a tight joint interface.
