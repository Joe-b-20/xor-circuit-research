# Six odd-own entries cannot supply a nine-gate source

2026-11-14. Structural hand proof by physical source populations, causal own-mask span, and named-pair uniqueness. No circuit search or enumeration. Own parity here refers to the ordinary source block, not to the influence traces.

**Theorem.** A joint circuit of total at most 21 with twelve consumer-bearing gates cannot have all its actual entry labels odd in the ordinary source coordinates.

Together with the [even-entry source floor](EVEN_ENTRY_SOURCE_FLOOR.md), this means that every remaining twelve-consumer candidate must read both even-own and odd-own labels. The six-entry problem itself remains open.

In fact at least two entries have odd own parity. Their indicator vector `p` satisfies `Zp=0`, because the target source parts have even own parity. Every trace column is nonzero in the tight six-gate mirror, so a nonzero `p` cannot have weight one. The number of odd-own entry occurrences is therefore between two and five. This is a statement about source-own parity, separate from the parity of the trace vectors.

## Normal form and physical populations

Use the [six-entry reduction](SIX_ENTRY_FRONTIER.md): the twelve consumer gates are target-live, there are six actual entry occurrences, their span `U` has rank five, and `G_0<=9`. Suppose all six labels have odd ordinary `b` parity.

Apply the free-coordinate projection from the [source parity normal form](EVEN_ENTRY_SOURCE_FLOOR.md#a-residue-plane-normal-form), and recompute physical source availability in the projected circuit. This fixes the required rows and preserves own masks. Its kernel is an odd wholly free line disjoint from `U`, so it is injective on the entry span and preserves rank five. Every computed free component is now even. Bypass duplicate, zero, and wholly free source gates. This preserves the six entry occurrences and their full values while not increasing `G_0`.

Write source values as `(beta,alpha)` and use `rho(beta,alpha)=beta+alpha`. In the even-free-part space, the entry span is `rho^{-1}(R)` for a rank-two residue plane `R` containing odd masks. The plane contains exactly two odd vectors. The eight named odd values

    N={b_0,b_1,b_2,b_3,U_0,U_1,U_2,U_3}

have the eight distinct odd residues. Exactly two named values therefore lie in `U`.

Let `A_o` count odd source gate values other than the four required rows, and let `H` be the set of even-own source gate values. Source normalization makes these distinct nonfree physical values. The source budget gives

    4+A_o+|H|<=9.

Every odd-own entry is nonclean. [Saturated unique-pair rigidity](SATURATED_QUOTIENT.md) makes the six actual labels distinct and prevents any of them from being first supplied by an exit. Six distinct physical odd values in `U`, of which at most two are named, require at least four odd helpers. Consequently

    A_o>=4,       |H|<=1.

## No even source value is impossible

Suppose `H` is empty. There are at most five odd helpers, hence at most seven physical odd source values in `U`: its two named values and those helpers. Six of them are actual nonclean entry labels and cannot be useful first returns. Thus at most one distinct odd value could first be supplied by an exit.

Without a nonfree even source value, an ordinary source gate producing an odd value can only add a wholly free operand and retain the earlier odd operand's own mask. An XOR of two odd source values would be even. Therefore each of the four distinct first triple-own occurrences must be an exit. These would be four distinct useful odd return values, contradicting the preceding bound of one. Hence `|H|=1`.

The budget now forces `G_0=9` and `A_o=4`. Write `H={w}`. Exactly six odd physical source values lie in `U`, and they are precisely the six actual labels: the two named values and all four odd helpers. No odd exit can supply a new value.

## The sole even value must first return all four own coordinates

Put `p=beta(w)`. It is nonzero and even. Since there are no useful odd exits, every odd source own mask is an ordinary input unit, possibly toggled by `p`. Adding free operands changes no own mask, and adding `w` toggles by `p`.

If `p` is a pair mask, only two of the four triples occur among the units and their translates by `p`: adding that pair to either unit outside its support gives a triple, while adding it to a unit in its support gives a unit. To obtain all four required triples, therefore,

    beta(w)=J=(1,1,1,1).

Before `w` first appears, every odd source value has a unit own mask. An ordinary source XOR of two such values has own weight zero or two, and a free addition cannot introduce the new mask `J`. Hence `w` must first be supplied by an exit. In particular `w in U`.

Let `i` be the number of named ordinary inputs in `U`. Its other `2-i` named values are source rows. Before the first supply of `w`, the actual entries have unit own masks. Causal span must generate `J`, so all four unit directions must have appeared. Only `i` of those directions can use named ordinary inputs in `U`; the others need distinct odd helpers of unit own mask. Thus at least

    4-i

odd helpers are physically present before `w`.

## Rows outside the entry span need too many additional helpers

There are `4-(2-i)=2+i` required source rows outside `U`. None can be an exit, since all exits lie in `U`. An ordinary source gate producing such a row either adds the sole even value `w` to an odd operand, or adds a free operand to an earlier odd value with the same triple own mask.

All odd helpers belong to `U`, and `w in U`, so `w` plus a helper cannot produce a row outside `U`. If the odd operand is another named row, its triple own mask plus `J` is a unit, again not a row mask. The only remaining direct production of the first type is `w+b_j` for a named ordinary input.

A fixed nonzero full value has at most one unordered pair representation among `N`: the only nonzero relation on the eight named values is their all-eight sum, so two different pair representations would give a shorter nonzero relation. Therefore at most one of the outside rows can be produced directly as `w+b_j`.

Every other outside row must be obtained by adding a free operand to a preceding odd helper with that row's own triple mask. It cannot use a coordinate input, and no other required row has the same own mask. The outside rows have distinct triple masks, so these predecessors are distinct helpers. Their number is at least

    (2+i)-1=1+i.

These triple-own helpers are different from the earlier unit-own helpers. The total odd-helper count is therefore at least

    (4-i)+(1+i)=5,

contradicting `A_o=4`. This proves the theorem.

The proof uses the projected circuit's own physical values throughout. It does not preserve or credit original source values outside the entry span through normalization. Its conclusion concerns the actual entry labels' source-own parity, and makes no claim that the remaining influence traces have any particular parity pattern.
