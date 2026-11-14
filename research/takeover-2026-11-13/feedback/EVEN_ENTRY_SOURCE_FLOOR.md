# Even-own entries cannot reduce the source below ten gates

2026-11-14. Structural hand proof by own-projection rank and independent odd-pair relations. No circuit search or enumeration. The theorem permits arbitrary consumer budget and arbitrary feedback.

Use ordinary source coordinates `b`, free coordinates `a`, and ordinary consumer coordinates `z`. Require the four source rows

    U_i=E_i(b)+s_i(a),
    E_i=sum of all b units except i,
    s_i=e_i+e_(i+1),                  indices modulo four,

and the usual consumer rows, whose source parts span

    D={(v,v): v has even parity}.

Let `G_0` count all zero-`z` gates, including exits. The actual consumer entry labels span `U` containing `D`.

**Theorem.** If every actual consumer entry has even ordinary `b` parity, then `G_0>=10`.

## Seven source relations must be present

Suppose `G_0<=9`. Bypass zero, duplicate, and wholly free source values, retaining the required rows. This cannot increase either gate count or introduce an entry with odd own parity. Source gate values are now distinct, and each has a nonzero ordinary `b` part; their own masks need not be distinct.

Let `H` be the set of physical even-own source gate values. Let `A_o` count odd-own source gate values other than the four rows. The physical odd source nodes are the eight named values

    N={b_0,b_1,b_2,b_3,U_0,U_1,U_2,U_3}

and these `A_o` helpers. Thus

    |H|<=5-A_o.

All actual entry labels have even own parity. They can be wholly free or members of `H`, since ordinary coordinate inputs are odd. Their own projections span the entire rank-three even space because `D subset U`. Consequently the own projections of `H` have rank three, giving `|H|>=3` and `A_o<=2`.

Choose the three chronological source gates that enlarge the span of even own projections. Each is an ordinary source XOR of two odd source values. Adding a free value or two preceding even values cannot enlarge that span. An exit cannot enlarge it either: its own projection lies in the span of earlier actual entry projections, which were supplied by earlier even source values.

Independently, the first occurrences of the four required triple own masks must be ordinary source XORs of an odd value and an even value. A free addition repeats an existing own mask, and every exit has even own parity by causal entry span. These four gates are distinct from the three even rank-growing gates.

Rearranging an odd-plus-even production therefore gives, in total, at least seven actual gate equations of the form

    h+u+v=0,       h in H,       u,v distinct odd physical nodes.

These seven equations are independent as formal vectors on the physical source nodes. In any nonempty selected sum, the chronologically latest result occurs in its own equation and cannot occur as an operand of an earlier selected gate. Its coefficient cannot cancel. This independence does not assume that other source gates are free of feedback.

## No odd helper

The sole nonzero relation among the eight named values is their all-eight sum. Indeed, vanishing free part selects either no row or all four rows; in the latter case their own sum requires all four inputs. In particular every nonzero full value has at most one unordered pair representation by distinct named values.

If `A_o=0`, each `h in H` supports at most one available odd-pair equation. Their total number is at most `|H|<=5`, contradicting the seven independent equations just obtained.

## One odd helper

Suppose `A_o=1`, with helper `y` outside `N`. For each `h`, there is at most one named pair and at most one pair using `y`; the latter has the form `{y,n}` with `n in N`.

If both pair representations occur, their formal difference has the form

    y+n_i+n_j+n_k,

where the three named nodes are distinct. A repeated named node would imply `y in N`, contrary to normalization. Evaluation gives a three-named expansion of `y`.

All such expansions have the same three-element support. The symmetric difference of two three-element supports has size at most six, whereas the only nonzero relation among `N` uses all eight nodes. Thus every second pair equation, after subtracting the first equation for its `h`, gives the same formal vector.

Choose one pair equation for each `h` that has any representation. These contribute at most `|H|` dimensions. All additional pair equations contribute at most one further dimension. Hence the entire available odd-pair relation space has rank at most

    |H|+1<=5,

again contradicting the seven independent actual equations.

## Two odd helpers

If `A_o=2`, the inequalities force `|H|=3`, with independent own projections. No value of `H` can first be supplied by an exit: its own projection would lie in the span of earlier actual entry projections, hence in the span of the other earlier `H` projections, contrary to independence.

Every nonzero, nonfree exit would have to be one of these even values. Thus all exits are redundant; under normalization none remains. The ordinary source gates alone supply the four rows using at most nine gates, contradicting their established [local minimum ten](../compatibility/INTERFACES.md#basic-ten-gate-facts).

These populations exhaust `A_o<=2`, proving the theorem.

## Consequences for the twelve-consumer frontier

Any twelve-consumer joint candidate of total at most 21 has `G_0<=9`. Therefore it must read an entry with odd ordinary source parity. This excludes the entire all-even-own-entry class, including both zero and one physically supplied clean value. The earlier section-completion inequality `G_0>=8+m_D` in [FREE_SECTION_REPLAY](FREE_SECTION_REPLAY.md) remains valid but is weaker for the purpose of excluding this class.

Combining the theorem with the rank-five interface reduction and [parity rank retraction](PARITY_RANK_RETRACTION.md) gives a sharper description. Such a candidate has `dim U=5`; its ordinary projection has rank four, because it contains the rank-three even space and an odd value. Its wholly free intersection consequently has dimension one. That direction is even, since parity retraction excludes an odd wholly free direction. Thus `U` contains exactly one nonzero wholly free value, an even mask `q`.

For any actual odd-own entry `h`,

    U=D direct-sum span{q,h}.

The independence follows from ordinary parity for `h` and from `D` meeting the free space only at zero for `q`; the dimensions then give equality. The three nonclean `D` cosets are `q+D`, `h+D`, and `h+q+D`. The first has even own parity and the other two have odd own parity. The free value `q` belongs to the entry span but is not asserted to occur as an actual entry. These are necessary structural conditions, not a closure of the remaining rank-five case.

## A residue-plane normal form

For further analysis of a hypothetical candidate, choose any odd mask `sigma` and project every free component by

    P(x)=x+parity(x)*sigma.

All required outputs are fixed, all computed gate values now have even free parts, and gate counts do not increase. The kernel on source values is the odd wholly free line `span{(0,sigma)}`. By parity retraction, this line does not meet the original `U` nontrivially. Thus the transformation is injective on `U` and preserves its rank five before optional bypasses.

In this transformed circuit, define `rho(beta,alpha)=beta+alpha` on the seven-dimensional space where `alpha` is even. Its kernel is exactly `D`. The entry span consequently has the form

    U=rho^{-1}(R),

where `R` is a two-dimensional residue plane containing odd masks. Equality here is within that even-free-part space: both sides have dimension five. The plane has one nonzero even vector `r` and two odd vectors. Its unique nonzero wholly free direction is `q=(0,r)`.

The eight named values `N` have the eight distinct odd residues, one each. Exactly two named values therefore belong to this normalized entry span, corresponding to the two odd vectors of `R`.

This is an existence reduction for a hypothetical circuit. It does not preserve all original physical source values outside `U`. Any subsequent physical supply counts or replay credits must use the transformed circuit's own available-value set. Nominally available odd free values also remain permitted; they are simply not used by the displayed projected computation. The normal form does not establish that either possible nonclean odd coset is absent or cheap to supply.
