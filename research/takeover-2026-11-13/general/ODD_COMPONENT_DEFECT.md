# Odd components and the cost of dependent even work

2026-11-14. General structural hand arguments for unrestricted linear XOR circuits. No circuit search, enumeration, or computer-driven elimination is used. These arguments have independent machine review, not formal verification or human certification. No literature-novelty claim is made.

The parity partition itself is an existing foundation: see [causal/REPORT, Lemma 2.2](../../structure-2026-11-11/causal/REPORT.md#lemma-22-parity-structure-of-a-cyclic-set-proved), where it is proved for the more general cyclic-set model. We reconstruct its circuit version because its chronological graph gives an exact physical accounting:

    even gates - effective even rank
      = odd-graph cycle rank + even-plus-even gates.

This removes the independent-even-helper assumption from the preceding [charged forest theorem](../feedback/CHARGED_ODD_FOREST.md). The resulting marked-network inequality says that independent even aggregate directions outside the boundary and odd charges require this many redundant even gates. A target-only consequence also gives the exact minimum number of even gates for any collection of odd targets, while leaving total circuit cost unresolved.

## 1. Arbitrary parity and the occurrence graph

Let the ordinary inputs be the coordinate vectors of V=F_2^n. Gates add two earlier values. Fanout is free. Repeated values, repeated operands, zero values, and arbitrary cancellation are allowed; counts below are counts of physical gate occurrences.

Fix a nonzero linear functional lambda. Put

    I={i : lambda(e_i)=1},   s=|I|,
    F=span{e_j : j not in I}.

Thus the s input coordinates in I are odd, and F is the span of the initially available even coordinate inputs. Using F in a quotient does not make its sums separately available for free. Let E count computed even gates and O computed odd gates. Define

    W=F+span{values of all computed even gates},
    r=dim(W/F).

Construct a multigraph Gamma with one vertex at each odd input or odd gate occurrence.

- An odd gate y=u+h, with u odd and h even, adds an edge from its odd parent u to its new result y, labelled by h.
- An even gate h=u+v with two odd parents adds an edge between those parent occurrences, labelled by h.
- An even gate with two even parents adds no graph edge.

Let k be the number of odd-plus-odd even gates and d the number of even-plus-even gates, so E=k+d. Loops and parallel edges are permitted; a loop has zero binary incidence. Every odd gate attaches a new vertex to an existing one, so every component contains an odd coordinate input. Let c be the component count and P the corresponding partition of I.

## 2. The parity partition, reconstructed

**Theorem 1.** The full even span is

    W = F direct-sum {v in F_2^I :
                       v has even parity on each part of P}.

In particular r=s-c.

**Proof.** Map each odd coordinate input to the unit vector of its final graph component, and map each even coordinate input to zero. Induction over the original gate order shows that every even gate maps to zero and every odd occurrence maps to the unit vector of its graph component. At an odd-plus-odd gate the two parents are joined in the final graph and therefore have the same component; at an odd gate its odd parent and result are in the same component. Even-plus-even gates preserve zero. This proves that W lies in the displayed subspace.

Conversely, along a graph path the XOR of its edge labels is the sum of its endpoint values. If two odd coordinate inputs belong to the same component, their pair sum therefore belongs to W. These within-part pair sums span the even subspace of each part, and F already belongs to W. This proves the reverse containment. QED.

The same proof applies to every chronological prefix. Thus an odd-plus-odd even gate increases effective even rank exactly when it joins two previously separate components. A gate closing an existing path is dependent on the previously available even span modulo F.

## 3. Every cycle has a paid even gate

Let mu be the binary cycle-space dimension of Gamma. It has s+O vertices and O+k edges, so

    mu = (O+k)-(s+O)+c = k-r.

Consequently

    E-r = mu+d.                                           (1)

This is an exact identity for every circuit, not a bound requiring helper independence. A chronological spanning forest consists of all odd-gate edges together with the r component-joining odd-plus-odd edges. Its mu omitted edges are exactly the remaining odd-plus-odd even gates. Together with the d even-plus-even gates, they are exactly the even gates whose creation does not increase W/F.

The independent-helper case has E=r. Then d=mu=0, so the odd graph is a forest and every even gate joins two components. Formula (1) identifies the two ways an unrestricted circuit can depart from that case: a cycle-closing even gate or an even-plus-even gate. Both are physical XOR gates.

## 4. What targets force, and what this count misses

Call a partition P of the odd input indices I compatible with a target set T if every even target has even support in each part and every odd target has odd support in exactly one part. Let c_max(T,lambda) be the maximum number of parts in a compatible partition. Such a partition always exists: the single part I is compatible. Components of every circuit give a compatible partition by Theorem 1 and the odd-occurrence component map.

Let t_o and t_e count distinct nonzero required non-input target values of odd and even parity, respectively. Every unrestricted circuit obeys

    E >= s-c_max(T,lambda),
    G >= t_o + max(t_e, s-c_max(T,lambda)).                 (2)

The second inequality only combines disjoint physical odd/even gate counts. It does not add lower bounds from different parity choices; lambda may be selected to obtain a useful individual bound.

**Exact even-count theorem for odd targets.** If every required target is lambda-odd, the minimum possible number of computed even gates, among all circuits for T, is exactly

    s-c_max(T,lambda).                                    (3)

**Proof of attainment.** Choose a compatible partition attaining c_max. In each part choose a coordinate input as its root and compute the pair of that root with every other coordinate input in the part. There are s-c_max such even gates. Their values are independent modulo F and span the partition's even space. Each required odd target is its unique odd part's root plus a combination of these star pairs and the initially even coordinate inputs. Start from that root and add the needed even operands one at a time. Every additional gate is odd. This computes all targets with exactly the stated number of even gates. QED.

Equation (3) concerns the even-gate population alone. Its construction can use many odd gates. It shows why merely strengthening an even-rank count cannot by itself settle total complexity: the parity component requirement is already attainable, and a stronger total bound must couple it to the cost of the odd computations or to dependent even work.

In fact the construction has E=r and hence defect zero. Thus no all-odd target set can force positive defect in every circuit, independently of the other costs. If h_o counts odd gate occurrences beyond one occurrence of each required odd non-input target, every circuit has the exact cost decomposition

    G = t_o + h_o + (s-c) + (E-r).                        (4)

A stronger unrestricted lower bound must force a tradeoff in this sum: a circuit may avoid dependent even work by paying for more odd gates or merging more input components. The existence of the zero-defect construction does not bound the odd work cheaply.

## 5. Arbitrary marked ports and source-valued adjoints

Expand fanout into physical binary copy trees. Attach arbitrary additional formal output ports at specified wire positions, and transpose the marked XOR/copy network literally. Give those added ports actual source labels in a separate vector space. Reversed ordinary output terminals are ordinary inputs and have zero source part.

Each original value occurrence v owns its physical copy tree. Let S_v be the sum of actual source labels attached in that tree. An equal-valued occurrence elsewhere has its own aggregate: occurrences are not merged by their masks.

Let f_v be the source part of the full adjoint at the root of that occurrence's copy tree. At an original coordinate input this is the source part of the corresponding designated reversed target. Assume all those input-boundary values f_i belong to a subspace D. At every occurrence,

    f_v = S_v + sum_{g a gate reader of v} f_g,            (5)

where an ordinary terminal contributes zero source part. Multiplicities are counted; two reads by the same XOR cancel in this identity. The equation sums the whole copy tree and does not move any individual source port to an earlier physical position.

Define

    H_0 = D + span{S_v : v is an odd occurrence},
    Q   = span{f_g : g is an ordinary gate occurrence},
    q   = dim((H_0+Q)/H_0).

The quotient uses ONLY odd occurrence aggregates. Quotienting by all aggregates would make the proposed adjoint inequality vacuous, because reverse recursion already expresses every gate adjoint in their span.

**Theorem 2 (dependent-even transport bound).**

    q <= E-r = mu+d.                                     (6)

Moreover,

    H_0+Q = D + span{S_v : all ordinary occurrences v}.    (7)

Thus q is exactly the rank of the even occurrence aggregates modulo D and the odd aggregates. Each independent direction of this kind requires a distinct unit of redundant even-gate count.

**Graph proof of (6).** Put flux f_g on the edge corresponding to an odd gate g, and flux f_h on the creation edge of an odd-plus-odd even gate h. At every odd vertex the sum of incident fluxes is S_v plus its boundary source part: the latter is f_i in D for an odd coordinate input, and zero for a computed odd vertex. Therefore the vertex boundary is zero modulo H_0.

Choose the chronological spanning forest. Summing vertex equations over one side of a forest-edge cut expresses that edge flux, modulo H_0, as the sum of the chord fluxes crossing the cut. Hence every odd-graph edge flux is generated modulo H_0 by the mu chord fluxes. Every ordinary gate adjoint is either one of these edge fluxes or the adjoint of an even-plus-even gate. The latter contribute at most d further directions. This proves q<=mu+d. The boundary terms from ordinary terminals, including terminals at even values, have zero source part. QED.

**Proof of (7).** Reverse-topological use of (5) expresses every gate adjoint in the span of occurrence aggregates, so H_0+Q is contained in the right side. Conversely, for an even computed occurrence, (5) expresses S_v as its own gate adjoint plus its gate-reader adjoints, all in Q. For an even coordinate input, its own adjoint belongs to D and its readers belong to Q. Odd aggregates already belong to H_0. This gives the other containment. QED.

## 6. Independent matrix proof and local residuals

The rank part has a short independent proof. Let M_even have as columns the ordinary values of all even occurrences, including the n-s even coordinate inputs. Its rank is n-s+r and it has n-s+E columns.

The full boundary identity for source labels is

    (f_1,...,f_n) = sum_v ordinary_value(v) tensor S_v.

Modulo H_0, both the input-boundary values and all odd aggregates vanish. Thus the vector-valued coefficients of the even columns give a relation on M_even. Their rank is at most its nullity,

    (n-s+E)-(n-s+r) = E-r.

By (7) that rank is q. This proves (6) without any graph choice. The kernel inequality is elementary; the graph identifies the physical cycle-closing and even-plus-even gates that account for its entire allowance.

Put H=H_0+Q. Every ordinary copy-tree root and every non-port reader contribution has source part in H. Therefore each physical reversed wire, modulo H, is a subset sum of the marked source labels belonging to its own occurrence's copy tree. The remaining source directions are local to those port trees. The possibly transported aggregate directions beyond the odd charges have dimension q, bounded by the paid defect E-r.

This is a source-part statement. Membership in H does not assert that a source value has been separately computed or is chronologically available. Root/readers and internal partial accumulators are also different: the latter may carry individual port sums outside H.

## 7. A sharp physical circulation

Use three ordinary inputs and the three gates

    h_12 = x_1+x_2,
    h_23 = x_2+x_3,
    h_13 = x_1+x_3.

Use total parity. All three gates are even, their rank is two, and the odd graph is a triangle. Thus E-r=mu=1 and d=0.

Designate all three h values as ordinary outputs, and also attach one marked output port of actual source label a to each helper. The ordinary reversed input contributions have source part zero. Each helper's root adjoint has source part a. At each original coordinate input the two incident source parts cancel, so all reversed input-boundary source parts are zero.

There are no odd marked ports. With D=0, H_0=0 and Q=span{a}. Hence q=1=E-r. The nonzero source direction circulates around the odd cycle while disappearing from the whole boundary. It is paid for by the third, dependent even gate.

The second term of (1) can be sharp too: replace the final gate by h_13=h_12+h_23 and attach the same three source ports. Now the odd graph is a path, mu=0 and d=1. The final helper adjoint has source part a; the other two helper root adjoints have source part a+a=0. Boundary source parts still vanish and q=1. Disjoint copies with independent labels make either construction sharp at any prescribed rank.

These are specified symbolic constructions, not search results.

## 8. Scope and research consequence

Theorems 1–2 allow arbitrary cancellation, fanout, feedback after reversing a marked network, even-helper dependence, and any chosen nonzero parity functional. They impose no MixColumns sheet restriction or small gate budget. Equation (1) is exact physical accounting, and (6) turns independent even aggregate directions into a necessary number of redundant even gates.

Their numerical usefulness still needs a target-forced quantity. If the marked input-boundary space D already contains every source label, q is zero. In particular, an invertible whole-map boundary does not automatically give a positive penalty merely by adding ports. Nor may penalties from several markings or parity choices be added without controlling shared physical gates.

A valid application would establish, from the target map and an appropriate marking, that every implementation must carry a positive rank of even aggregate labels outside its boundary and odd charges, or establish a joint cost for avoiding that rank through additional odd work. Extracting such a requirement for unrestricted MixColumns remains open. The unrestricted 75–88 interval is unchanged.

The earlier restricted frontiers remain evidence and examples, not the next task list. The purpose here is to expose the unrestricted cost mechanism and its present limitation, rather than extend another fixed-budget classification.

Independent review: [odd components, exact defect, and marked transport](reviews/odd-component-defect-review.md).
