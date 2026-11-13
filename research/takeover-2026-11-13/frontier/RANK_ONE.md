# A rank-one clean supplier cannot meet the eleven-gate consumer interface

2026-11-13. Hand proof only; no search, enumeration, exact-gate optimization, or computer-driven case elimination. This closes one remaining supplier class, not the full joint 21-to-22 gap.

## Main result

Use the first-sheet model: four ordinary coordinates `b_i`, all vectors of a separate block `a` free, and targets

    U_c=E_c(b)+s_c(a),       s_c=e_c+e_(c+1).

Let

    D={v(b)+v(a): v is even}

be the three-dimensional clean diagonal. For a fixed ten-gate producer let `W` be the span of its actually available clean values, including gates and base values.

**Theorem R1.** If `dim W<=1`, the supplied values cannot support an eleven-gate second-sheet consumer for the four triples with required free-part span `D`. Here all counted consumer gates have nonzero consumer-own part, and every actual free operand must belong to the fixed supplied set; additional zero-own supplier gates are treated separately in the joint consequence below.

The result includes arbitrary internal cancellation in the producer and consumer. With the standard no-feedback hypothesis on the first-sheet target cones, any joint circuit using such a ten-gate producer needs at least 22 gates, even if an additional supplier gate is allowed to be a consumer-block-cancelling exit.

The central new statement is the following four-value incompatibility.

**Theorem F4.** Suppose the available nonzero clean values of a ten-gate producer span `W=<h>`, with `h!=0`. If a nonzero `D` coset contains four available values `B`, and

    Delta_B=span{v+v_0 : v in B},

then

    W+Delta_B != D.

Thus a rank-one clean supplier cannot use a saturated four-value nonclean coset to provide the missing clean directions, even as virtual differences.

## Previously established ingredients

The proof uses the hand-proved ten-gate sheet lemma and results recorded in `../compatibility/INTERFACES.md`, `../compatibility/QUOTIENT.md`, and `../tradeoff/RELATIONS.md`:

* A normalized ten-gate producer has no free, zero, duplicate, or dead gate. Every gate has nonzero `b` part.
* Every actual entry label on `a` is even, so every computed `a` part is even. There are `3<=tau<=4` entries.
* At least two physical gates have even `b` parity.
* Each `D` coset contains at most four available values.
* With `rho(beta|alpha)=beta+alpha`, the eight named odd values `N={b_i,U_c}` occupy all eight odd residues once each. Their only nonzero relation is their all-eight sum. In particular a value has at most one named-pair representation.
* Physical gate equations are independent in the formal node-coordinate space. In a fixed three-value relation, at most one orientation can be a gate, because only its latest node can be the result.

For odd node set `O` and physical even-value set `H`, the available odd-pair relation graph has an edge when two odd values sum to a member of `H`. If its number of components is `c_O`, the relation-rank bound gives

    G-tau <= |O|-c_O+|H|-rank(H).

We will also use its elementary pair-count form when no even/even/even relation is available.

An available coset containing four values has even `a` parity: otherwise it could contain only its one possible free value. On the even-`a` space, a `D` coset is precisely a `rho` fibre.

## Proof of F4 when the nonclean coset has even b parity

Write its nonzero residue as `e`. Four values in an even-parity coset must consist of the unique free point `f=(0|e)` and three gates `g_1,g_2,g_3` with distinct nonzero even `b` projections `v_1,v_2,v_3`. Four nonzero even projections would already need eight first-occurrence gates, including the four target triples, plus at least three entries.

These three even projections and the four triples force exactly seven first gates and three entries, with no other duplicates. The entry labels are independent. Every clean diagonal has ordinary projection among the `v_i`, since a fourth even projection would again force at least eleven gates. In particular `h=D(v_j)` for one `j`, and

    g_i=f+D(v_i),
    Delta_B=span{D(v_1),D(v_2),D(v_3)},
    h in Delta_B.

The assumed equality `W+Delta_B=D` therefore forces `v_1,v_2,v_3` independent.

### Independent even-fibre values

Let `A` count the producer's odd non-output gates, and let `H` be its physical even values. There are `4+A` odd gates and `|H|=6-A` even gates. Since `H` contains the three `g_i` and the distinct clean value `h`, `A<=2`.

All values of `H` have one of the three independent ordinary projections `v_i`. Each of these fibres has a first gate; every other gate in it is an entry, because the total budget is seven first gates plus three entries. The span of `H` equals the span of its three fibre roots plus the span of its even-fibre entry labels. One inclusion follows by following entry paths; conversely each such label is a difference of two adjacent physical values in its fibre.

The roots have independent ordinary projections, so their span meets the free space only at zero. The even-fibre entry labels are a subset of the three independent entry labels. Consequently

    rank(H)=3+(number of even-fibre entries)=|H|.

In particular there are no even/even/even relations. All seven non-entry gates must therefore use odd-pair relations.

### No odd helper

If `A=0`, all odd nodes are named. Each even value has at most one named-pair representation, while the clean `h` has none because named residues are distinct. With six even values there are at most five available relations, fewer than the seven required non-entry gates. Contradiction.

### Two odd helpers

If `A=2`, the four even values are exactly `g_1,g_2,g_3,h`. Their residues span `<e>`. Every edge in the odd relation graph therefore stays within a residue coset modulo `<e>`. The eight named odd residues occupy four such cosets, so `c_O>=4`.

There are ten odd nodes, including the four ordinary inputs. Since the even values are independent, the relation-rank bound gives

    7=G-tau <= |O|-c_O <= 10-4=6,

a contradiction.

### One odd helper

If `A=1`, denote the odd helper by `x`. There are five independent even values: `g_1,g_2,g_3,h` and one other value `k`.

Each `g_i` has at most one named-pair representation. Across all three `g_i`, at most one further representation can use `x`: their common residue `e` fixes the named partner at residue `rho(x)+e`, and that partner together with `x` fixes the sum. Thus the three `g_i` have at most four odd-pair representations in total.

The clean `h` has at most the one representation using `x` and the named value at residue `rho(x)`; it has no named-pair representation. The remaining `k` has at most two representations, one named and one involving the single helper. The total is at most seven.

All seven are needed. Hence all three `g_i` have named-pair representations, and there are named nodes `n_0,n_e` and some `g_j` with

    h=x+n_0,       g_j=x+n_e,
    rho(n_0)=rho(x),       rho(n_e)=rho(x)+e.

The named residues pair into four unordered pairs under translation by `e`. The three named-pair representations of the `g_i` occupy three different pairs. The pair `{n_0,n_e}` is not one of them: its sum is `h+g_j`, which cannot equal any `g_i` because the five even values are independent.

Thus these are all four named residue pairs. Their sums add to the sum of all eight named values, which is zero. Therefore

    g_1+g_2+g_3+h+g_j=0.

After cancelling `g_j`, this is a nonzero relation among `h` and the other two `g_i`, again contradicting independence. This finishes the even-parity case.

## Proof of F4 when the nonclean coset has odd b parity

Let `B` be the four odd nodes in the coset, of residue `e`. Exactly one is named, and the other three are odd helpers. The condition `W+Delta_B=D` implies

    at most one unordered pair in B has sum h.                 (4)

Indeed, two disjoint `h` pairs would make `B` an affine plane invariant under `h`. Its difference span would have dimension at most two and contain `h`, so `W+Delta_B` would still have dimension at most two. This contradicts the required dimension three. Translation by nonzero `h` makes the pairs disjoint, so the argument covers every way to have two such pairs.

There are either three or four odd helpers, since the ten-gate circuit needs at least two even gates.

### Four odd helpers: two even values

The physical even values are `h` and one nonclean value `k`. The fourth odd helper is outside `B`, by the four-value coset cap. It enlarges one other odd residue class to a two-node set `C`. All remaining odd residue classes are singletons.

The clean `h` has at most one pair inside `B` by (4), and at most one inside `C`. Hence it has at most two odd-pair representations.

The nonclean `k` has at most three. If its residue pairs `B` with `C`, at most two matches occur between those classes, and at most one further wholly named pair exists. If it does not pair those two classes, `B` and `C` can each match at most one singleton named node, and at most one further wholly named pair exists. These are consequences of matching and named-pair uniqueness, not a list of circuit shapes.

There is no even/even/even relation with only two even values. Thus there are at most five available non-entry relations, whereas `G-tau>=6`. Contradiction.

### Three odd helpers: three even values

The physical even values are `h` and two nonclean values `k,l`. Every other odd residue has its single named value. The clean `h` has at most one odd-pair representation, and each nonclean value at most two: one pair involving `B` and at most one wholly named pair. Thus there are at most five odd-pair relations.

To supply at least six non-entry gates, the even-only relation `h+k+l=0` must exist, all five odd-pair capacities must be met, and all six available relations would have to be executed. In particular `rho(k)=rho(l)` is nonzero. Their pairs involving `B` therefore have the same outside named endpoint `n`:

    k=x+n,       l=y+n,       x,y in B.

Since `k!=l`, the two endpoints `x,y` are distinct. The even-only relation gives `h=x+y`, which is the unique `h` pair permitted by (4).

But the four formal node relations

    h+x+y=0,
    k+x+n=0,
    l+y+n=0,
    h+k+l=0

sum to zero. They are distinct and cannot all be equations of physical gates in one acyclic circuit. Therefore six independent non-entry equations are unavailable. This contradiction completes the odd-parity case and proves F4. QED.

No restriction was imposed on whether the four nonclean labels form an affine plane or are affinely independent. In particular, the case where a clean label equals the sum of all four nonclean labels is not silently discarded; condition (4) and the relation arguments cover it.

## From F4 to consumer cost and joint cost

The earlier compatibility result already proves that a ten-gate producer of clean rank at most one could support an at-most-eleven-gate consumer only in the following form: exactly five entries, four distinct nonclean labels in one coset and one nonzero clean label. The labels must span the required `D`, so the actual four-value set `B` would satisfy `W+Delta_B=D`. F4 excludes it. If `W=0`, the necessary nonzero clean label is unavailable from the outset. Thus every such fixed-supplier consumer needs at least twelve gates, proving R1.

For a joint circuit using this ten-gate first-sheet producer under the no-feedback hypothesis, a total of at most 21 has only two possible splits. With no extra zero-consumer-block gate, there are at most eleven consumer-bearing gates, excluded by R1. With one extra supplier gate, there are only ten consumer-bearing gates. All their entries must be clean and must span the three-dimensional `D`; adding one physical supplier value can raise the producer's clean span from at most one to at most two. This remains true if the added value is a consumer-block exit. Therefore this split is also impossible. Two or more additional supplier gates already bring the total to at least 22 by the ten-gate consumer minimum.

## Remaining joint frontier

In a hypothetical 21-gate joint circuit with a ten-gate first-sheet cone, that producer must now have clean rank exactly two. The nonclean part of its eleven-gate consumer interface then consists of two or three labels; four are excluded by the clean-rank/coset tradeoff, and the remaining trace constraints are recorded in [QUOTIENT](../compatibility/QUOTIENT.md).

[Theorem E2](EVEN_ESCAPE.md) further shows that all physical even own masks of the rank-two producer lie in its clean own span; a completing nonclean coset must be odd.

The other profile, eleven source-side gates and ten consumer-bearing gates, remains the three-independent-diagonal augmented-supplier problem. Neither remaining profile is excluded here. The general joint interval remains 21 to 22, and the unrestricted MixColumns interval remains `75<=L<=88`.
