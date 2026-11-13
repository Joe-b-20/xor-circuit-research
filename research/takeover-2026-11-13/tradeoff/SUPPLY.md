# Four values in one nonclean coset exclude two independent clean suppliers

2026-11-13. Hand proof only; no search, enumeration, exact-gate optimization, or computer-driven case elimination. This is a coupled producer constraint, not a proof of the general 22-gate joint bound.

## Result

Use the first-sheet problem and clean diagonal from `../compatibility/INTERFACES.md`. There are four ordinary inputs `b_i`, all vectors of a separate block `a` are free, and the required values are

    U_c=E_c(b)+s_c(a),       s_c=e_c+e_(c+1).

The clean subspace is

    D={v(b)+v(a): v is even},       dim D=3.

Available values include gates, the ordinary inputs, and the free `a` values.

**Theorem T.** If a ten-gate producer supplies four distinct available values in one nonzero coset of `D`, then its available clean-diagonal values span at most one dimension.

Equivalently, a ten-gate producer supplying two independent clean diagonals has at most three available values in every nonzero `D` coset.

This does not assume that every ten-gate producer has clean rank at most one, and does not replace the established four-value coset cap by a universal three-value cap. It proves that the two resources cannot both reach those levels in the same producer.

## Facts used from the ten-gate argument

Normalize the circuit. The ten-gate minimum means no gate can be removed as dead, free, zero, or a duplicate. Write each signal as `(beta|alpha)` and call a gate even or odd according to the parity of its nonzero ordinary part `beta`.

The earlier arguments establish:

1. Every actual free entry label, and hence every computed `alpha`, is even.
2. If `tau` counts entry gates, then `3<=tau<=4`; the transpose computes the four triples with `10-tau>=6` gates.
3. At least two even gates are necessary. With only one nonzero even ordinary projection `p`, every odd projection would lie in `{b_i,b_i+p}`, which cannot contain all four triples.
4. Every `D` coset contains at most four available values (Theorem S).

Define `rho(beta|alpha)=beta+alpha`. On signals with even `alpha`, its kernel is `D`. The eight named odd values

    N={b_0,b_1,b_2,b_3,U_0,U_1,U_2,U_3}

have residues consisting of the four units and the four triples, each once. They have rank seven with unique nonzero relation their all-eight sum. Thus each value has at most one representation as a sum of two distinct named values.

If a coset had odd `alpha` parity, it could contain only its unique possible free value, and not four available values. Hence any four-value coset considered below lies in the even-`alpha` subspace and is a residue fibre. Let its nonzero residue be `e`.

## Even ordinary parity: independent entries separate the fibres

Suppose the four-value coset has even `beta` parity. Its projection to `beta` is injective. At most one value has zero projection and is free. If all four had nonzero projections, they would require four nonzero even first-occurrence projections in addition to the four target triple projections. Eight first gates plus at least three entries would exceed ten.

Therefore the coset consists of its unique free value `(0|e)` and three gates with distinct nonzero even projections `v_1,v_2,v_3`. These three projections and the four triple projections require at least seven first-occurrence gates. With at least three entries, the ten-gate budget forces exactly seven first gates and three entries, with no other duplicates. The three entry labels span the even free space and are independent.

Any clean diagonal gate must have its ordinary projection among `v_1,v_2,v_3`: a fourth nonzero even projection would again force at least eleven gates.

Suppose two distinct clean diagonal gates exist, on projections `v_i,v_j`. In each of these two ordinary-projection fibres, the clean value and the coset value differ by the same nonzero free vector `(0|e)`.

All duplicate gates are entries. Consequently each ordinary-projection fibre is a rooted tree: its first signal is the root, and an entry joins its value to its earlier nonfree operand, with the free entry label on the edge. The difference of any two values in one fibre is the sum of the labels on their unique tree path. The paths in distinct fibres use disjoint sets of entry occurrences.

The two fibre paths just described would thus be two disjoint nonempty subsets of the three independent entry labels with the same sum `e`. Their union would give a nonzero relation among those labels. This is impossible. There is at most one nonzero clean diagonal, proving the theorem in this case.

The argument is a general independent-entry principle: when every duplicate is an entry and all entry labels are independent, a fixed nonzero free displacement cannot occur between two pairs of signals in different ordinary-projection fibres.

## Odd ordinary parity: physical gate relations impose the tradeoff

Suppose the four-value coset has odd `beta` parity. Its residue `e` is odd, and exactly one named value has that residue. The other three available values in the coset must be non-output odd gates. Thus there are at least seven odd gates. There are also at least two even gates. The ten-gate budget leaves only the gate-count alternatives

    eight odd and two even,     or     seven odd and three even.

This split follows from the count, not from a list of circuit configurations. We show that neither alternative can supply two independent clean diagonals.

### Physical relation principle

A non-entry gate with one even and two odd nodes in its three-node relation corresponds to a decomposition

    h=u+v

of an even value `h` into two distinct odd values. A given three-value relation can be executed by at most one gate: in a reduced circuit, the latest of its three unique nodes is the only possible output.

We will also use the stronger fact that distinct physical gate equations of an acyclic circuit are linearly independent when written in formal variables indexed by physical nodes, including the inputs. Each equation has coefficient one on its gate node and only earlier nodes elsewhere, so their rows are triangular in topological order. In particular, a dependent family of formal three-node relations cannot all occur as physical gate equations.

### Eight odd gates and two even gates

If two independent clean diagonals are available, they must be exactly the two even gate values. The four-value coset contains three of the four non-output odd gates. The remaining odd helper has a different residue; otherwise the coset would have five values, contrary to Theorem S.

Thus the odd residue classes have sizes four, two, and one for all the others: the size-four class is the chosen coset, and the other helper enlarges one further named residue class to size two.

Every clean even value has residue zero, so its odd-pair decompositions join equal-residue nodes. In the size-four class, translation by a fixed nonzero value gives at most two disjoint pairs. Across the two clean even values, the sole pair in the size-two class can belong to at most one of them. Therefore there are at most `2+2+1=5` relevant odd-pair decompositions in total.

No non-entry gate can add two nonzero even nodes: while either of the two even gates is being created, at most one earlier even gate exists, and adding it to itself has zero ordinary projection. Hence every non-entry gate corresponds to one of the five odd-pair relations. But there must be at least `10-tau>=6` non-entry gates. Contradiction.

### Seven odd gates and three even gates: all three even values clean

Let `B` be the four odd nodes in the chosen coset and `H` the three even gate nodes. Every other odd residue has just its one named value. If all three even values are clean, every non-entry gate relation is supported entirely on `B union H`: an even/odd/odd relation must pair equal-residue odd nodes, which can only lie in `B`, while an even/even/even relation uses only `H`.

There are seven nodes in this union. Their actual values have rank at least three: the clean values have rank at least two by hypothesis, and any odd-`beta` value is independent of their even-`beta` span. Therefore the space of formal relations among these seven node variables has dimension at most `7-3=4`.

All physical non-entry gate equations would lie in this relation space, and they are independent by the physical relation principle. At most four can occur. The transpose bound requires at least six. This contradiction excludes the all-clean alternative without selecting a gate order or enumerating a shape.

### Seven odd gates and three even gates: two clean values and one nonclean value

Write the clean values as `h_1,h_2` and the third even value as `k`, with `rho(k)!=0`. There is no relation among these three even values: two clean values sum to a clean value, and adding `k` to a clean value remains nonclean but cannot equal `k`. Thus no non-entry gate has two nonzero even operands. Every non-entry gate again corresponds to an odd-pair relation.

For each clean value, all odd-pair decompositions lie inside the four-node chosen coset, giving at most two pairs. The nonclean `k` also has at most two odd-pair decompositions. One can join the chosen coset to the named value at the uniquely determined residue `e+rho(k)`; at most one other can be wholly named, by the rank-seven property of `N`.

There are at most six relations in total, while at least six non-entry gates are required. Equality would have to hold everywhere, and all six relations would have to be executed. In particular, each of the two clean values would have two disjoint pairs covering all four odd nodes of the coset.

The resulting four clean relations are formally dependent. Each of the four odd-node variables occurs once in each matching, hence twice overall; each clean-even variable occurs in its two relations. Their sum is zero in the formal node-coordinate space. They are four distinct relations because `h_1!=h_2`. By the physical relation principle, they cannot all be gate equations of one acyclic circuit. This contradiction finishes the odd-parity case and proves Theorem T. QED.

## Consequences for actual eleven-gate consumer supply

The combined supplier and consumer constraints now distinguish two resource patterns, rather than permitting them to be credited independently.

For a ten-gate producer, the established augmented-sheet bound says its available clean-diagonal span has dimension at most two. The earlier compatibility result says an eleven-gate consumer cannot use only nonclean labels, while using only clean labels would require clean rank three. For a mixed interface, the quotient theorem gives one nonzero coset for all distinct nonclean labels.

* If the producer has clean rank at most one, the earlier trace argument forces exactly five entries: four nonclean labels saturating one coset and one nonzero clean label. Thus its clean rank is exactly one.
* If it has clean rank two, Theorem T prevents a four-label nonclean coset. The remaining mixed interfaces use two or three nonclean labels and require two independent actual clean suppliers. Their virtual nonclean differences must complete the required three-space.

These are necessary conditions, not existence claims. In particular, Theorem T alone does **not** force every hypothetical joint 21 into the first pattern: the rank-two supplier with two or three nonclean labels remains open.

The other joint split, eleven first-side gates and ten second-side gates, remains the separate augmented-sheet problem. Neither split is resolved here, and `75<=L(MixColumns)<=88` is unchanged.
