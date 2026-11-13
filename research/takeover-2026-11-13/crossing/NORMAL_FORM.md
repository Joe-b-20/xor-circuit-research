# A normal form for every rank-two clean supplier

2026-11-13. Hand proof using class sums and formal relation rank. No search, enumeration, or computer-driven case elimination. This establishes the structure used to exclude odd-coset crossings in [ODD_CLOSURE](ODD_CLOSURE.md).

Use the ten-gate first-sheet model with ordinary inputs `b_i`, free block `a`, and required rows `U_c=(E_c,s_c)`. Let `W` be the span of actually available clean even diagonals, and assume `dim W=2`. All circuits are normalized as in [RANK_ONE](../frontier/RANK_ONE.md). Write

    rho(beta,alpha)=beta+alpha,
    H = set of physical even gate values,
    V = span H,                 R = rho(V),
    r = dim R,                  A = number of odd non-output gates,
    tau = number of actual free-entry gates.

By [E2](../frontier/EVEN_ESCAPE.md), every even own mask lies in the two-dimensional plane `W_b`. The earlier sheet lemmas give `3<=tau<=4` and `A>=1`.

**Theorem.** Every such ten-gate producer has

    A=2,       tau=4,       |H|=4,       rank(H)=4,       dim R=2.

Exactly two distinct nonzero even own masks occur; they are a basis of `W_b`. The six non-entry gates are precisely the first occurrences of these two masks and the four target triples. There are two odd entries and two even entries. In particular, the four physical even values consist of exactly two clean values and two nonclean values.

There is exactly one odd helper and one odd entry in each own class. The two even-entry labels form a basis of `R`; both odd-entry labels lie outside `R`.

The theorem applies to every plane `W_b`, including planes that contain the full-parity mask and planes that do not.

## The four named residues in either own class have nonzero sum

Let `t=1111` and let `P` be the cyclic coordinate shift, so `P e_c=e_(c+1)`. Choose a linear functional `F` whose kernel on the even-mask space is `W_b`, and write `w=(F(e_0),...,F(e_3))`. The vector `w` is neither zero nor `t`: those constant coefficient vectors vanish on the entire even-mask space.

Every odd node has an own class `F(beta)` in `{0,1}`. Even additions preserve this class. The eight named odd nodes are

    N={b_0,...,b_3,U_0,...,U_3},

with residues `e_i` and `E_(c+1)`, respectively. These are all eight odd four-bit residues, once each. Each own class contains exactly four named nodes. Indeed, if `F(t)=0`, the nonconstant vector `w` has weight two, giving two inputs and two outputs in each class. If `F(t)=1`, the output class of `U_c` is the opposite of `F(e_c)`, so the input and output counts complement each other.

The sum of the four named residues in either class is

    d=w+P w != 0.                                             (1)

For a direct calculation, the sum of all eight named residues is zero, so both class sums equal the residue sum weighted by `F(beta)`. Inputs contribute `w`. With `delta=F(t)`, outputs contribute

    sum_c (delta+F(e_c))(t+P e_c)
      = delta t+delta t+P w
      = P w.

Finally `w=P w` would force all four coordinates of `w` equal, contrary to its choice. Thus the four distinct residues in either own class do not form an affine plane. In particular, a fixed nonzero translation has at most one unordered pair wholly inside each such four-point set: two pairs would be disjoint and would make their four-point sum zero.

## Residue-component counting forces at most two helpers

By E2, the kernel of `rho` on `V` is exactly `W`. It contains `W`, and any vector in that kernel is a diagonal whose own mask lies in `W_b`, hence belongs to `W`. Therefore

    dim V=2+r.                                                (2)

There are `|H|=6-A` even gates and `|O|=8+A` physical odd nodes including the four inputs. Let `c` be the number of components of the available odd-pair relation graph, where a pair is an edge if its sum belongs to `H`. The [formal relation-rank bound](../tradeoff/RELATIONS.md) gives

    10-tau <= |O|-c+|H|-dim V = 12-c-r,

or equivalently

    c+r <= tau+2 <= 6.                                       (3)

Every edge preserves both the own class and the residue modulo `R`.

If `r=0`, the eight distinct named residues already require at least eight components, contradicting (3).

If `r=1`, the eight named residues form four translation pairs modulo `R`. By (1), each own class contains at most one wholly internal pair. At least two of the four pairs therefore meet both own classes. A pair lying in one class requires at least one graph component, while a split pair requires at least two. Hence `c>=6`, again contradicting (3) because now `c+r>=7`.

If `r=2`, there are two residue cosets, each containing four of the named residues. Each meets both own classes: otherwise one class's four named residues would be an affine plane, contradicting (1). Thus `c>=4`. Equation (3) then forces

    tau=4,       c=4.                                        (4)

We have proved `r>=2`. Since (2) and the physical even-gate count imply

    2+r <= 6-A,

we obtain `A<=2`.

## One helper cannot supply enough independent relations

Suppose `A=1`, with odd helper `x`; then there are five even values. If `r=3`, (2) makes these five values independent, so no even-only three-value relation exists. If `r=2`, (4) gives four entries. The four distinct target triples and two independent even own masks already require six first-occurrence gates, filling all six non-entry slots. Thus exactly two even own masks occur. Three nonzero masks drawn from these two independent masks cannot sum to zero, so there is again no even-only three-value relation.

In either situation there are exactly two physical clean values. For `r=3`, three clean values would be dependent inside `W`, contradicting independence of the five even values. For `r=2`, only two even own masks occur, and each mask admits only one clean value. The other three even values are nonclean.

Every available non-entry equation is consequently an odd-pair relation on `N union {x}`. A clean value has no wholly named pair, since named residues are distinct. Across both clean values, at most one relation uses `x`: its named endpoint must be the unique named value with residue `rho(x)`.

A nonclean value has at most one named-pair representation and at most one representation involving `x`. Call it doubled if both occur. For a doubled value,

    k_i=x+n_i=p_i+q_i,

where `n_i,p_i,q_i` are three distinct named nodes. The named nodes have no nonzero relation on at most six members, so every such expression writes `x` as the sum of the same three-element named set `S`; see the [named-triple rigidity lemma](../frontier/EVEN_ESCAPE.md).

This also bounds formal relation rank directly. Write the two formal equations for the doubled value as

    r_i=[k_i]+[x]+[n_i],
    s_i=[k_i]+sum_{n in S minus {n_i}}[n].

For every doubled value they satisfy

    r_i+s_i=z,       z=[x]+sum_{n in S}[n].

Thus, if there are `j>=1` doubled nonclean values, their `2j` equations span a space of dimension at most `j+1`: the vectors `r_i` and the one common vector `z` generate them all. The remaining `3-j` nonclean values contribute at most one relation each, and the clean values together contribute at most one. The total rank is at most

    (j+1)+(3-j)+1=5.

If there are no doubled values, the rank is at most four. But `10-tau>=6` actual non-entry gate equations must be independent. With no even-only relations available, this is impossible. Hence `A!=1`.

## The resulting two-helper form

Since `1<=A<=2`, the exclusion gives `A=2`. There are four even values, and (2) with `r>=2` forces `r=2` and `dim V=4`. Equation (4) gives `tau=4`. As above, four entries leave exactly six first-occurrence gates: two even masks and the four triples. Both even masks must be independent because actual clean values span `W_b`.

There are therefore two odd entries and two even entries. This counts gate types; an odd helper can be a first occurrence followed by an entry that creates its designated target. Four independent even values cannot contain three values in the two-dimensional clean space, so exactly two are clean. This proves the theorem.

## One odd entry in each own class

The six actual non-entry equations form a forest on the ten physical odd nodes. Indeed, a cycle would have a zero sum of its physical even colors. Independence of those colors would force each color to occur evenly, making the cycle's formal equations dependent. The forest therefore has four components. Each combination of own class and residue coset modulo `R` contains a named node, and no edge leaves its combination. Thus these four combinations are exactly the four components, two in each own class. The available graph has the same components by (4).

Project the free block to zero and bypass the four entries. The remaining six first-occurrence gates still produce distinct nonzero non-input own values: the two even basis masks and four triples. Their six odd-pair edges on the eight odd own masks form a forest by the same independent-color argument, now using independence of the two own masks. They have two components and preserve own class, so each class is a connected four-node tree.

Add the two physical odd-entry edges to the physical six-edge forest. Each joins two nodes of one own-mask fibre. These entry edges connect every such fibre; contracting the fibres gives the two projected trees. Hence the expanded graph is connected within each own class. Since each class initially had two components, it needs at least one odd-entry edge. Exactly two are available, so there is one in each class. The one extra odd physical node in each class is its unique odd helper, whether that extra node precedes or follows its designated target along the entry edge.

There are also two even entries. The four physical even values span their two first-occurrence roots and the two even-entry labels. The roots have independent own masks, so their span meets the pure-free space only at zero. Rank four therefore forces the two labels to be independent. Each is a difference of two physical even values and hence belongs to `R`; since `dim R=2`, they form a basis of `R`. Each odd entry joins the two distinct residue-coset components of its own class, so its label lies outside `R`.

This supplies the graph and entry structure used by [ODD_CLOSURE](ODD_CLOSURE.md) to exclude odd same-residue crossings. No new unrestricted joint or MixColumns lower bound is asserted here.
