# Replay by completing a section of the ordinary projection

2026-11-14. General structural hand proof, followed by an even-own-entry consequence for the two-sheet problem. No circuit search or enumeration. The bound charges original physical values rather than virtual span directions.

## General section-completion theorem

Partition coordinates into ordinary source coordinates `b`, a free source space `F`, and ordinary consumer coordinates `z`. Every vector of `F` is available without gates. Let `G_0` count all original zero-`z` gates, including exits, and let `A` be the original physical source-value set: source inputs, all permitted free values, and source gate values. Let `U` span the actual consumer entry labels, and let `pi` project source values onto their ordinary `b` parts. Put

    B=pi(U),       r=dim B.

Choose any fixed linear section `s:B -> B direct-sum F` satisfying `pi(s(beta))=beta`, and put `H=s(B)`. Thus every `u in U` differs from `s(pi(u))` by a free value. Define

    m_H=|A intersect (H minus {0})|.

**Theorem.** There is a source-only replay preserving every original source value and supplying all of `H`, with cost at most

    G_0+(2^r-1-m_H).

No condition that the original entry prefixes split under a fixed direct sum is needed. The remainder after taking the section is already free at every time.

To prove this, process the original circuit chronologically and omit its consumer-bearing gates. After the first `i` entries, maintain physically every value of `H_i=s(B_i)`, where `B_i` is the span of their ordinary projections. Initially this group is zero. Copy an ordinary source gate using its previously supplied operands, unless its value is already available.

At an entry `ell`, its actual source label has already been supplied. The value

    ell+s(pi(ell))

belongs to `F` and is free. Thus `s(pi(ell))` is obtained from the label by at most one XOR. If its ordinary projection enlarges `B_i`, complete the enlarged `H_i` by adding that new section value to the previously maintained group, omitting every value already available. Each synthetic gate has a distinct nonzero result in `H`.

Before an exit, its value lies in the span of earlier actual entry labels. Its ordinary projection therefore lies in the current `B_i`, and its section value is physically maintained. The exit is that section value plus a free remainder, requiring at most one XOR, covered by its original source-gate allowance. The invariant consequently respects the original timing and preserves every source value.

Finally use the credit argument from [credited replay](CREDITED_REPLAY.md). If a synthetic `H` value belongs to `A`, it was either available already and needed no synthetic gate, or its original first source gate occurs later. That later gate can be bypassed as a distinct credit. If `R` is the set of synthetic values, the total is at most

    G_0+|R minus A| <= G_0+(2^r-1-m_H).

By the last entry, `B_i=B`, so all of `H` has been supplied. This proves the theorem. Original physical values supplied later through exits count as credits; mere membership in their linear span does not.

## Even-own entries in the two-sheet problem

Use the usual source rows `U_i=E_i(b)+s_i(a)` and clean diagonal

    D={(v,v): v has even parity}.

Suppose **every actual entry has even ordinary `b` parity**. Since `D subset U`, the ordinary projection `B=pi(U)` is then the full three-dimensional even space. Choose the diagonal section

    s(beta)=(beta,beta).

Its image is `H=D`. The section theorem gives a source-only circuit preserving the four source rows and supplying all seven nonzero clean diagonal values in at most

    G_0+7-m_D,
    m_D=|A intersect (D minus {0})|.

The [fifteen-gate full-diagonal bound](FULL_DIAGONAL_SUPPLY.md) therefore implies

    G_0>=8+m_D.

This bound needs no restriction on entry rank, consumer budget, feedback, or the parity of the entries' free parts. Only their ordinary own parity is assumed even. Its free remainder is `(0,alpha+beta)`, which is available whether even or odd.

In particular, a twelve-consumer candidate of total at most 21 whose entries all have even own parity must satisfy `m_D<=1`. This strengthens the general rank-five necessary condition `m_D<=2` in this subclass. The section bound alone does not exclude zero or one clean value. The separate [even-entry source floor](EVEN_ENTRY_SOURCE_FLOOR.md) subsequently excludes the entire even-own-entry class by proving `G_0>=10`. The general section-completion theorem remains available beyond that application, and the twelve-consumer problem remains open.
