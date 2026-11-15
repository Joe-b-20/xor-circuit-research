# Common-anchor triples: a known exact law through parity partitions

2026-11-14. Structural arguments for unrestricted binary XOR circuits. Arbitrary sharing, cancellation, repeated gate values, and arbitrary intermediate values are allowed. An [independent machine review](reviews/common-anchor-graph-review.md) audits the arguments. No formal verification, human certification, or literature novelty is claimed.

The exact cost theorem below is already proved by Joan Boyar, Philip Matthews, and Rene Peralta in [Logic Minimization Techniques with Applications to Cryptology](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=908384), January 2011 manuscript, Section 3.1.1, Lemma 1, pp. 10–14. Their result applies to linear straight-line programs over arbitrary fields and includes a procedure extracting a vertex cover from a program. We recover its binary case with a short parity-partition argument, identify its even-rank and optimal-circuit consequences, and use it to expose a limitation of the new chronological relation potential.

## 1. Graph targets and their exact cost

Let F=(X,E) be a finite simple loop-free graph, with m=|E|. Supply independent coordinate inputs a and x_v for v in X. For every edge uv require the distinct odd target

    t_uv = a+x_u+x_v.

Let tau(F) be the minimum size of a vertex cover: a set of vertices meeting every edge. Isolated vertices are allowed and cost nothing. Then

    exact unrestricted XOR cost = m+tau(F),              (1)
    minimum possible even-gate count = tau(F),           (2)
    minimum compatible-partition rank = tau(F).          (3)

No optimization or enumeration is used here; tau(F) remains a symbolic graph invariant.

**Lower bound through parity.** Use total coordinate parity. The [odd-component theorem](ODD_COMPONENT_DEFECT.md) associates to every unrestricted circuit a partition P of all input coordinates such that each odd target meets exactly one part oddly. If r is the partition rank, meaning the number of input coordinates minus the number of parts, then the number N_even of even gates satisfies N_even>=r.

Let A be the part containing a, and let C_0 be the graph vertices whose coordinates lie in A. For an edge uv not incident to C_0, its two endpoints must belong to the same other part: otherwise the target a+x_u+x_v meets three different parts oddly. From this partition form a vertex set C by taking every vertex in C_0 and all but one vertex from each other part B. Every edge incident to C_0 is covered, and any remaining edge is internal to some B, where at most one vertex was omitted. Thus C is a vertex cover, with

    |C| = |C_0| + sum_(B!=A)(|B|-1) = r.

Consequently tau(F)<=r<=N_even. The m distinct odd targets need at least m odd gates. These are disjoint from the even gates, so every circuit has at least m+tau(F) gates. This argument does not restrict its internal values or require it to compute anchor pairs.

**Attainment.** Choose a minimum vertex cover C. For each v in C compute the actual even helper h_v=a+x_v in one gate. For each edge uv, choose one endpoint v in C and compute t_uv=h_v+x_u in one gate. There are tau(F) helper gates and m output gates. The partition with anchor part {a} union {x_v:v in C}, and every other input in its own part, has rank tau(F). This proves all three claims.

The zero-edge case gives zero cost. Simplicity and absence of loops ensure every edge specifies a different non-input target.

## 2. What equality forces in every optimum

Write H for odd gates beyond the m target first productions, and use the exact odd-component ledger

    G = m+H+r+mu+d,

where mu is the odd-graph cycle rank and d counts even-plus-even gates. Since r>=tau(F), equality in (1) forces

    H=0,        r=tau(F),        mu=0,        d=0.         (4)

Thus every optimum has exactly m odd gates and tau(F) even gates; its even values are independent, its odd occurrence graph is a forest, and no even-plus-even gate occurs. Every optimal component partition yields a minimum vertex cover by the selection rule above.

These are consequences of unrestricted optimality, not assumptions about the competing circuits. They do not assert that every optimum literally uses the displayed anchor-star helpers.

In particular H=mu=d=0 does not mean cancellation-free wiring. For a triangle on vertices 1,2,3, the following five gates are optimal:

    p=x_1+x_2,       t_12=a+p,
    q=x_2+x_3,       t_23=a+q,
    t_13=t_12+q.

The last gate cancels x_2. Neither even helper is an anchor pair. The two independent even values still give r=2 and mu=d=0, while H=0. A cover-star optimum exists, but optimal circuits can have other wiring and genuine cancellation.

## 3. What the initial relation closure sees

Let J be a selected set of graph edges and W_J the span of their target values. The actual initial dictionary S consists of all coordinate inputs. Let R_J=R_(W_J)(S) be the [short-relation closure](SUBSPACE_PREPARATION.md): the span of supplied singleton and pair values that lie in W_J. Ignore isolated vertices when counting the nonempty connected components c(J) of the selected-edge graph.

There is an exact description:

    dim(W_J/R_J) = c(J),     if the selected graph is bipartite;
    dim(W_J/R_J) = 0,        if it is nonbipartite.        (5)

For the empty edge set both spaces are zero.

**Bipartite case.** Fix a bipartition L_C,R_C of each nonempty connected component C. A linear combination of the selected targets has zero coefficients on inactive vertices and even total x-coordinate parity in each C. Its coefficient of a equals the sum of its x-coordinate parities on the chosen L_C sides. Conversely these conditions describe W_J: the edge incidence vectors span the even-coordinate subspace of each connected component, as can be proved by summing edges along tree paths. Therefore, if v_J is the number of vertices incident to selected edges,

    dim W_J = v_J-c(J).

No coordinate singleton lies in W_J. Its weight-two vectors are exactly x_u+x_v with u,v in the same side of the same connected component. Such vectors arise by summing the targets along an even-length path. They span the separate even-coordinate spaces on all the L_C and R_C sides, whose total dimension is v_J-2c(J). This is R_J and proves the first case of (5).

Every selected target has weight three and lies outside R_J. Hence whenever the deficiency in (5) is positive,

    min_(w in W_J minus R_J) ell_S(w) = 3.               (6)

**Nonbipartite case.** Summing the targets around an odd cycle gives a, so a belongs to W_J. Then each selected edge gives the short vector x_u+x_v=t_uv+a in W_J. The singleton a and these pairs span all selected targets, so R_J=W_J. One odd cycle can therefore saturate the initial relation closure even in other selected-edge components. This is span membership, not a free physical supply of a+x_u or other helpers.

## 4. The flag potential can miss a growing helper cost

Apply the [chronological flag potential](FLAG_RELATION_TRANSPORT.md) to all graph targets. Equation (5) gives its initial deficiency at every output prefix, irrespective of its order. If the whole graph is bipartite, each new edge either starts a new component, extends one, joins two components, or stays in one component. Only starting a new component increases the deficiency. Every final nonempty component needs a start; ordering its spanning-tree edges consecutively and then its remaining edges achieves just one start. Therefore

    min_order Phi = c(F)       for nonempty bipartite F.

If F is nonbipartite, start with the edges of one odd cycle in cyclic order. There is one positive increment at its first edge, and closing the odd cycle saturates the closure. Every subsequent prefix remains nonbipartite and has deficiency zero. At least one increment is unavoidable because the first target has weight three. Thus

    min_order Phi = 1          for nonbipartite F.         (7)

Every unsaturated prefix has escape length three by (6), so the distance correction is zero. These facts compare two exact target invariants: the true auxiliary cost tau(F), and the smaller amount of preparation detected by this closure potential. They do not weaken the valid flag inequality; they locate work counted in its flat auxiliary remainder.

**Even selecting different target subsets cannot repair the gap on connected graphs.** Suppose F is connected and nonempty. A selected nonempty edge set with p edges has best-order certificate p+c if its graph is bipartite with c nonempty components, and p+1 otherwise. Deleting the m-p omitted edges from a connected graph increases the number of nonempty components by at most m-p. Thus c<=m-p+1, and both cases give a certificate at most m+1. Taking every edge attains m+1, since the whole graph is connected. Therefore

    maximum over selected target subsets of their
    distance-augmented best-order flag certificate = m+1. (7a)

The exact cost remains m+tau(F). This limitation concerns the target-only flag bound obtained by minimizing over each subset's possible output orders. It does not bound unrelated methods, a stronger invariant that retains the flat auxiliary work, or an argument that first proves a circuit normalization permitting a useful production order. Omitted required-output gates cannot simply be added again, since they may advance the selected flag and are already allowed among its auxiliary gates.

For a path of m>=1 edges, the targets are

    t_i=a+x_i+x_(i+1),        1<=i<=m.

A path has vertex-cover size ceil(m/2): alternating vertices attain it, while ceil(m/2) pairwise disjoint path edges require that many different covering vertices. Hence

    exact unrestricted cost = m+ceil(m/2).              (8)

In the natural path order each nonempty prefix is connected and bipartite, so q_i=1, Phi=1, and Delta_*=3. More explicitly,

    R_i=span{x_j+x_(j+2):1<=j<i},     dim R_i=i-1.

The m targets are independent, and all have fixed coordinate weight three. The flag certificate gives only m+1, while the actual helper cost grows as ceil(m/2). This gap is not caused by one increasingly long target.

For a path, the general subset ceiling (7a) is also visible directly: p selected edges in c nonempty runs have c-1 omitted gaps between those runs, so p+c<=m+1.

Finally retain a and x_1 as identity outputs and replace every x_(i+1) by t_i. This gives a square all-odd invertible map, since x_(i+1)=t_i+a+x_i recursively recovers the inputs. Identity outputs are already supplied and change no gate count. The barrier therefore persists for all-odd invertible maps.

## 5. Research consequence

The known graph theorem illustrates an exact unrestricted sharing law: vertex-cover choices determine how many even directions must physically be supplied, and cancellation cannot reduce that count. The relation closure sees directions recoverable by W-valued gates, while the parity account counts required even supply. On these examples their difference is unbounded. A more complete general argument must retain that physical preparation cost or couple the two accounts without charging one gate twice.

No numerical MixColumns improvement is asserted.



The [specified checker](checks/check_flag_and_anchor.py) and
[saved results](checks/flag-anchor-result.json) verify a seven-edge path using
four specified cover helpers and seven output gates. A displayed four-edge
matching certifies the cover size without optimization. Its square all-odd
embedding has rank nine; the actual flag trace has one activating and three
neutral auxiliary gates. The five-gate triangle check verifies its even rank
two and the cancelled coordinate at its last gate. All graph formulas and
subset/order claims are proved symbolically above, not by enumeration.
