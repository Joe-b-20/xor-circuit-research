# At most two nonclean entry values force eleven source gates

2026-11-13. Hand proof by chronological basis selection and source replay. No circuit search, enumeration, or computer-driven case elimination is used.

Consider the unrestricted joint source/consumer problem with free coordinates `a`, ordinary source coordinates `b`, ordinary consumer coordinates `z`, and targets

    U_i=E_i(b)+s_i(a),
    Y_i=E_i(z)+s_i(b)+s_i(a).

Let `G_0` count all gates with zero `z` part, including source values obtained through feedback, and let

    D={v(b)+v(a): v is even}.

Actual entry labels are the zero-`z` values read by nonzero-`z` gates. Labels are counted as distinct values in the theorem below; their occurrences may repeat.

**Theorem.** Suppose the actual entry labels span a four-dimensional space `U` containing `D`, and at most two distinct actual entry labels lie outside `D`. Then `G_0>=11`, with no restriction on the number of consumer-bearing gates.

## Proof

Let `W` be the span of the actual clean entry labels, those in `D`. Since at most two other values complete them to rank four, `dim W>=2`.

If `dim W=3`, three independent clean diagonals are original physical source values. The [rank-four physical-supply theorem](RANK_FOUR_SUPPLY.md) gives `G_0>=11`. Each nonzero clean label is a paid physical source value because it is neither an ordinary coordinate input nor wholly supported on the free block.

Otherwise `dim W=2`. There must be exactly two distinct nonclean labels, call them `n,m`, and their classes are independent modulo `W`; otherwise the full entry span would have dimension at most three. Since `U/D` has dimension one, their sum

    e=n+m

lies in `D`. It is outside `W`, again because the full entry span has dimension four.

Select a basis greedily in the order of actual entry-label occurrences. It consists of two independent clean labels `c,d` spanning `W` and both nonclean labels `n,m`. Earlier actual labels always lie in the span of the basis elements selected by that time. Every source exit likewise belongs to the span of earlier entry labels, by induction through the consumer-bearing gates. Therefore the unique expansion of any exit in the final basis `c,d,n,m` uses only basis elements already physically supplied.

Replay source-side gates chronologically, using the fixed groups

    {c,d},       {n,m}.

Retain the pair sums `p=c+d` and `e=n+m`, computing each on first need if absent. Each pair sum costs at most one additional gate. Its operands are already physically supplied whenever its coefficient pair occurs in an exit. Every exit is then the sum of at most one available value from each group and uses at most its original one gate. Ordinary source gates are reproduced from their earlier source operands or bypassed when their values are already available. Append either pair sum if unused during replay.

The replay preserves all original source values and uses at most `G_0+2` source-only gates. It supplies the four rows and the four distinct diagonals

    c,d,c+d,e,

where `c,d,e` are independent. The [four-diagonal bound](FOUR_DIAGONALS.md) requires thirteen gates. Hence `G_0+2>=13`, proving the theorem.

The greedy basis is important here: a third clean entry may be dependent on the other two and may occur before either one in a chosen naming. Selecting by actual occurrence order ensures that this dependence cannot request a label before it has been supplied. Repeated entry occurrences do not change this argument.

## A physical clean triangle saves another replay gate

In the rank-two clean-entry branch, suppose the original source values already contain all three nonzero values of `W`. In particular the pair sum `p=c+d` is an original physical source value. Its completion contributes no net extra gate: if the original production comes first, replay reuses it; if completion comes first, replay bypasses its later original production. The sole possible net addition is `e=n+m`.

The same source-only replay therefore has cost at most `G_0+1` and still supplies `c,d,c+d,e`. The four-diagonal bound now gives

    G_0>=12.                                             (2)

This strengthening requires a physical triangle in the rank-two span of the actual clean entry labels. It does not infer physical availability merely from membership in their span.

## Consequence for the five-entry eleven-gate frontier

Suppose an eleven-consumer circuit has five actual entry occurrences, entry-label rank four, and exactly two nonclean occurrences. Their values are distinct by [entry deletion](../compatibility/QUOTIENT.md), and the three remaining clean occurrences either have rank three or have rank two. The theorem gives `G_0>=11` in both cases, so the joint total is at least 22 even with arbitrary feedback.

If those three clean entry values are distinct and have rank two, they are exactly a physical clean triangle. Equation (2) then gives `G_0>=12`, for joint total at least 23 in that subclass. If they are independent, only the bound 22 is asserted here.

Consequently the remaining five-entry mixed candidate below 22 must use at least three nonclean entry occurrences. The [three-nonclean case](THREE_NONCLEAN.md) is closed by a separate dynamic completion argument; the four- and five-nonclean cases remain open. No unrestricted joint minimum or MixColumns lower bound is changed by this partial closure.
