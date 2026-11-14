# Equality in quotient cost makes every projected collision an entry-tree path

2026-11-14. General structural hand proof by projection, physical collision counting, and chronological entry edges. No circuit search, enumeration, or computer-driven case elimination. No literature-novelty or formal-verification claim is made.

## Model

Use ordinary consumer coordinates `z` and a disjoint source-value space. Let `K` count every physical gate with nonzero `z` part, including gates used only for source exits. A consumer entry reads one zero-`z` source operand, its actual label, and one consumer-bearing operand. Let `U` span all actual entry labels, and let `D` span the source parts required at the consumer targets. Causal induction gives `D subset U`.

Let `L_D` be the minimum number of consumer-bearing gates for those targets when every value of `D` is free, and put

    c=dim(U/D).

The [entry-deletion bound](../compatibility/QUOTIENT.md) gives `K>=L_D+c`. Assume equality:

    K=L_D+c.                                               (E)

For the physical graph below, include one node for each ordinary consumer-coordinate input and each counted consumer-bearing gate. Free copies are wires, not additional nodes. The [collision-defect bound](ENTRY_RETURN_RIGIDITY.md) applies without a target-cone trimming assumption and counts duplicate physical nodes if any.

## Saturated projection theorem

Choose `c` actual entry occurrences whose label images form a basis of `U/D`; write their labels as `f_1,...,f_c` and put

    C=span{f_1,...,f_c}.

These labels are independent and `U=D direct-sum C`. In the physical consumer graph retain just the chosen entry edges: the edge for `f_i` joins that entry's earlier nonfree operand to its result. Include every other consumer node as an isolated vertex when necessary.

**Theorem.** Under (E), the connected components of this selected-entry forest are exactly the classes of physical consumer nodes with equal full values modulo `C`.

Every selected edge preserves full value modulo `C`. The selected edges form a forest: each result has at most one incoming selected entry edge, all edges point forward in the original order, and an undirected cycle in such a graph would force a directed cycle. There are exactly `c` edges, so the forest components contribute total defect `c`, where a component's defect is its number of vertices minus one.

Each forest component lies inside one `C`-coset class. Merging two forest components into one occupied `C`-coset increases the defect by one. Thus, if `delta_C` is the total physical collision defect,

    delta_C >= c,

with equality exactly when the two partitions coincide. The collision theorem gives

    K >= L_D+delta_C.

Together with (E), this forces `delta_C=c`, proving the theorem. In particular, no additional node or separate selected component can share an occupied coset with a selected component without already belonging to it through selected entry edges.

This is stronger than counting only the chosen deletions. It identifies all physical collisions under this projection with actual causal entry paths.

## Path labels and chronological return values

For two nodes with the same full value modulo `C`, their difference is the sum of the labels on their unique selected-tree path. All selected labels are globally independent, and each appears on exactly one selected edge. Hence the support of this sum is precisely that path's edge set.

Each selected component is a rooted directed tree. A path between two nodes lies in the union of their root paths. Every selected label on that path was read at or before one of the endpoint nodes was produced. Therefore an exit using those two nodes occurs strictly after all the relevant labels were read.

Consequently an exit whose returned value belongs to `C` is the sum of a set of earlier actual selected labels, along that physical path. It can be replayed using at most one fewer XOR than the number of path edges, or no XOR if the path has at most one edge. When `c<=2`, every such exit is already supplied or costs at most its original one source XOR.

The conclusion requires the returned value itself to belong to this particular complement `C`; membership in `U` alone does not ensure that. The consumer may return values with nonzero components in both `D` and `C`.

## Every actual nonclean label still has a unique pair

Assume `c>0`, and let `f` be any actual entry label outside `D`. Extend its nonzero quotient image to a basis of `U/D` using actual entry labels, choosing the occurrence of `f` as one selected entry. Apply the theorem to the resulting complement `C`.

Any unordered pair of distinct physical consumer nodes with difference `f` lies in one `C`-coset and hence in one selected tree. Independence of the selected labels means its path sum equals `f` only if its path consists of the single selected `f` edge. Thus:

**Unique-pair corollary.** At equality `K=L_D+dim(U/D)`, the entry edge for any actual nonclean label `f` is its unique unordered physical difference pair. That label occurs at exactly one entry.

For the last assertion, another occurrence would supply a second edge with the same difference. Such an edge cannot be the selected physical edge: its result is a different original gate node. The same argument also rules out two equal-valued physical consumer nodes, since their selected-tree path would have zero sum of independent edge labels.

A source exit returning the actual nonclean label `f` would have to read this unique entry pair. But the label `f` had to be physically supplied before the entry result was produced, hence before that exit. It cannot be a first supplier of `f`; in a reduced full circuit it is redundant and can be bypassed. This conclusion does not exclude indirect feedback that returns another value and then changes it before entry use.

The corollary extends the earlier one-extra-gate unique-pair theorem from quotient rank one to every quotient rank at equality. A quotient-rank assumption is essential: a consumer with two gates above `L_D` but only one nonclean quotient direction has unused projection slack, so the preceding equality argument does not apply.

## Application to twelve consumer gates

For the two-sheet MixColumns problem, the required consumer source space is the rank-three clean diagonal and `L_D=10`. If a consumer has exactly twelve gates and its actual entry space has quotient rank two over `D`, then it satisfies (E).

Choose any two actual labels with independent quotient signatures. Their two selected entry edges form either two disjoint one-edge components or one two-edge tree; all other nodes are singleton components. These are exactly the physical classes modulo their two-dimensional complement. Every return in that chosen complement is already supplied or the sum of the two earlier selected labels. Every actual nonclean entry label has a unique pair and cannot be newly returned, despite the two-gate consumer slack relative to `L_D`.

This restricts the rank-five interface without assuming six entries, an ordinary six-gate mirror, or that all gates lie in the consumer target cones. It does not show that all returns lie in one chosen complement, and does not prove the twelve-consumer joint minimum or the unrestricted joint minimum.
