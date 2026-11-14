# Supplying the full clean diagonal requires fifteen source gates

2026-11-14. Structural hand proof by own-mask first occurrences, parity, and formal relation rank. No circuit search, enumeration, or computer-driven elimination. The lower bound permits arbitrary intermediate cancellation. No fifteen-gate attaining construction is asserted.

## Full-diagonal source bound

Use ordinary inputs `b_0,...,b_3` and a separate four-coordinate free block `a`. Require the four rows

    U_i=E_i(b)+s_i(a),
    E_i=sum of all ordinary units except i,
    s_i=e_i+e_(i+1),                  indices modulo four,

and every nonzero value of the three-dimensional clean diagonal

    D={v(b)+v(a): v is even}.

**Theorem.** Supplying the four rows and all seven nonzero clean diagonal values requires at least fifteen paid XOR gates.

Normalize a putative supplier with at most fourteen gates while retaining all eleven required values. Bypass zero, duplicates, and wholly free paid values. Write each physical value as `(beta,alpha)` on the ordinary and free coordinates. Every paid gate has nonzero `beta`. A source entry adds a free operand and repeats its earlier nonfree operand's `beta` mask; let `tau` count these entries.

The four row triples and seven nonzero even diagonal masks require eleven distinct non-input ordinary first occurrences. They cannot be entries. At least three entries are needed to span the rank-three free parts of the four rows. Therefore the circuit has exactly fourteen gates, `tau=3`, and eleven non-entry gates. Its three actual free labels span the even space on `a` and hence form a basis of that space. Every computed free part is consequently even; nominally available odd free labels are irrelevant because none is read.

Let `H` be the physical even-own gate values, `O` the odd-own physical nodes including ordinary inputs, and `V=span H`. Let `A_o` count odd gates other than the four row outputs. Then

    |H|=10-A_o,       |O|=8+A_o.

Use the residue map `rho(beta,alpha)=beta+alpha`. On values with even free part its kernel is precisely `D`. Since all of `D` is physically contained in `H`, writing `r=dim rho(V)` gives

    dim V=3+r.

The named odd nodes `N={b_i,U_i}` have the eight distinct odd residues: the four units and the four triples. Their only nonzero relation is their all-eight sum. Vanishing free part selects either no row or all four; in the latter case the ordinary row sum requires all four ordinary inputs. In particular a nonzero full value has at most one unordered pair representation using distinct named values.

Join odd nodes when their sum is in `H`, and let `g` count the components of this available-pair graph, including isolated nodes. The [formal relation-rank inequality](../tradeoff/RELATIONS.md) gives

    14-tau <= |O|-g+|H|-dim V,
    hence g+r<=tau+1=4.

The incidence projection has rank `|O|-g`, and its kernel is contained in the even evaluation kernel of dimension `|H|-dim V`. Actual non-entry equations are independent by their chronologically latest-result pivots. Every available odd edge preserves residue modulo `rho(V)`, while the named residues occupy all `2^(3-r)` odd affine classes. Thus `g>=2^(3-r)`, which excludes `r=0,1` and gives `r>=2`.

The seven physical clean values and at least two nonclean even values needed for residue rank two give `|H|>=9`, so `A_o<=1`. The remaining populations are excluded by pair capacities:

- If `A_o=0`, all odd nodes are named. A clean even value has no odd-pair representation because named residues are distinct. At most three nonclean even values have at most one named pair each. Even-only equations contribute rank at most `|H|-dim V<=10-5=5`. Total available non-entry relation rank is at most `3+5=8`, below the required eleven.
- If `A_o=1`, there are nine even values, including the seven clean ones and at most two nonclean ones. Each nonclean value has at most one named pair and one pair using the unique odd helper. Across all clean values, at most one pair exists: it joins that helper to the unique named node with the same residue. Thus odd-pair equations have rank at most their count `2*2+1=5`. Even-only equations contribute at most `9-5=4`. Their combined rank is at most nine, again below eleven.

Every non-entry gate is either an odd-pair equation (after rearranging an odd-plus-even gate) or an even-only equation. Both populations contradict the required eleven independent gate equations. This proves the fifteen-gate lower bound.

## A general chronological quotient complement

The following replay observation applies beyond the particular source targets above. Let actual consumer entry labels span a source space `U`, and fix any subspace `D subset U`. Let `A` be the original physical source-value set: source inputs, permitted free values, and all original source gate values, including exits. Let `c=dim(U/D)`.

Select actual entry occurrences greedily in chronological order when their images enlarge the span in `U/D`. Their labels `n1,...,nc` are independent modulo `D`, so

    C=span{n1,...,nc},       U=D direct-sum C.

This final decomposition splits every entry-prefix span. At an occurrence selected as a new quotient representative, the actual label itself is a pure `C` value. At any other occurrence, its quotient image is a combination of the representatives already read. Its `C` component is the same combination of those actual labels and therefore belongs to the preceding entry span. The remaining `D` component is supplied by subtracting that known component from the current label. Clean entries are pure `D` values. Induction gives exactly the prefix condition of [credited replay](CREDITED_REPLAY.md).

Define physical counts

    m_D=|A intersect (D minus {0})|,
    m_C=|A intersect (C minus {0})|.

The credited replay theorem supplies every original source value and all of `D,C` in at most

    G_0 + (2^dim(D)-1-m_D) + (2^c-1-m_C)

gates, preserving chronological source availability. In particular `m_C>=c`, because the selected representatives are original physical values. Other original group values reduce the budget even when their original production occurs later; early production is then credited to bypassing that later gate. Mere membership in the original value span gives no credit.

This is a fixed chronological construction, not an optimization over circuit families. It does not assume that the whole target subspace `D` was already physically supplied before the consumer began.

## Rank-five source supply

Return to the joint 0/1-sheet model with its rank-three clean diagonal `D`, and suppose the actual entry span has rank five. The chronological quotient complement has dimension two. Its full group sizes are seven and three, so replay supplies all seven nonzero diagonals with the source rows in at most

    G_0+10-m_D-m_C

gates. The new fifteen-gate source theorem implies

    G_0 >= 5+m_D+m_C >= 7+m_D.                         (1)

This lower bound holds for arbitrary consumer budgets and arbitrary feedback. It counts original physical clean values, not merely the dimension of their span.

For a joint candidate of total at most 21 with twelve consumer-bearing gates, the source budget is at most nine. The [rank-four source floor](RANK_FOUR_SOURCE_FLOOR.md) and entry deletion force rank-five entry span, so (1) applies and gives

    m_D<=2.

If `m_D=2`, then `G_0=9` and `m_C=2`. The sum of the two selected quotient representatives is not an original physical source value; otherwise `m_C=3` would force `G_0>=10`. This is a necessary condition for the remaining candidate, not its exclusion. Rank-five sources, larger entry spaces, and the unrestricted joint minimum remain open.
