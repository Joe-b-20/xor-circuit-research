# Rank-four entry spaces cannot reduce the source below ten gates

2026-11-14. Structural hand proof by chronological replay, physical coset caps, and the first nonredundant return. No circuit search, enumeration, or computer-driven elimination. The theorem has no consumer-budget hypothesis.

Use the joint 0/1-sheet model and clean diagonal

    D={v(b)+v(a): v is even}.

Let `G_0` count all zero-consumer gates, including exits, and let `U` span the actual source labels read by consumer-bearing gates. The consumer targets ensure `D subset U`.

**Theorem.** If `dim U<=4`, then `G_0>=10`.

When `U=D`, [diagonal confinement](DIAGONAL_CONFINEMENT.md) gives the stronger `G_0>=12`. For rank-four `U`, [the physical-clean supply lemma](RANK_FOUR_TWO_CLEAN.md) gives `G_0>=11` when the original physical clean span has rank at least two, and `G_0>=10` when it has rank one. It remains to exclude `G_0<=9` with no nonzero original physical clean value. No normalization assumption about the original consumer budget is needed: zero or redundant uses can simply be ignored in the following value-set argument.

## At most five original values in the nonclean coset

Let `A` be the original physical source-value set, including ordinary source inputs, permitted free values and all source gate values. Assume

    G_0<=9,       A intersect D={0},       dim U=4.

The set `C=U minus D` is one affine coset of `D`. Rank-four [general replay](GENERAL_REPAIR.md) preserves every original source value using at most `G_0+2<=11` source-only gates. The [six-value coset theorem](SIX_COSET_VALUES.md) therefore implies

    |A intersect C|<=5.                                  (1)

Otherwise that replay would supply the four source rows and six distinct physical values in the same diagonal coset within eleven gates, which is impossible. This count includes original values supplied through feedback, not just actual entry labels.

All nonzero entry labels belong to `C`, since there is no nonzero original clean value. Choose a chronological greedy basis of their rank-four span:

    n1,n2,n3,n4.

These are four distinct original physical values in `C`. By (1), there is at most one other original physical value in `C`; call it `t` when it exists.

## Only one value can first be supplied by an exit

Every exit lies in the span of earlier actual entry labels. A nonzero exit cannot be clean under the assumption `A intersect D={0}`, so its value belongs to `C` and is among the four basis values and possibly `t`.

A basis value `ni` cannot first be supplied by an exit. Before its first actual entry occurrence, it is outside the span of all preceding entry labels, by the greedy choice. An earlier exit cannot produce it by the causal span invariant. After that entry occurrence, it was already physically supplied before the entry. Any such exit would merely repeat an existing source value.

Thus every first supply of a nonzero source value by an exit must be the single additional value `t`. If no exit supplies a new value, all exits can be bypassed during source-only replay, giving a source circuit with at most nine gates for the four rows. Their [local minimum ten](../compatibility/INTERFACES.md#basic-ten-gate-facts) excludes this. Hence a first nonredundant exit producing `t` must occur.

Before that exit, `t` has not appeared as an entry: an entry would require its physical source operand already to exist. All earlier nonzero entries are therefore among `n1,n2,n3,n4`. Causal span implies that `t` is a combination of those basis values already read.

The quotient functional on `U` that vanishes on `D` takes value one on each `ni` and on `t`. The basis expansion of `t` has odd weight. It is not one basis value, so in rank four its expansion has exactly three terms. All three basis values in this expansion have already been physically supplied and read before the exit.

## A single extra gate violates the ten-gate coset cap

Replay ordinary source gates chronologically. Earlier exits merely repeated available values and are bypassed. At the first exit producing `t`, compute a pair sum of two of its three available basis terms, and then add the third term. The latter XOR uses the original exit's one-gate allowance. Only the pair sum is an extra gate.

Retain the result `t`. Every later exit returns zero, an already supplied basis value, or the already supplied `t`, and can be bypassed. All other original source gates can be copied or bypassed in order. This gives a source-only realization preserving every original source value with at most

    G_0+1<=10

gates. It supplies the four source rows and the five distinct values `n1,n2,n3,n4,t` in one diagonal coset. The [ten-gate coset cap](../compatibility/INTERFACES.md) permits at most four available values in a coset. A circuit with fewer than ten gates cannot supply the rows at all. Both possibilities are excluded, proving the rank-four source floor.

The argument uses two different replay bounds for different purposes. The generic two-gate replay first bounds how many original coset values can exist. That physical scarcity then confines all useful returns to one value and permits the stronger one-gate replay. It is not a claim that generic rank-four replay always has overhead one.

## Consequence for a twelve-gate consumer

For `K=12`, [entry deletion](../compatibility/QUOTIENT.md) gives

    dim(U/D)<=2,       hence dim U<=5.

A joint total at most 21 would have `G_0<=9`. The theorem excludes entry rank at most four, so any such candidate has entry rank exactly five and two independent nonclean quotient directions. This is a structural reduction, not an exclusion of that rank-five case or a proof of the unrestricted joint minimum.
