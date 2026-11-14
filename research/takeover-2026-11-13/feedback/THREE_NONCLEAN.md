# Three nonclean entries: causal clean-plane completion

2026-11-13. Hand proof by the entry-label relation and chronological replay. The dynamic completion argument was proposed by the visible-interface reviewer and independently checked by the structural and primary agents. No circuit search, enumeration, or computer-driven case elimination is used.

Use the unrestricted joint 0/1-sheet model, with source rows `U_i=E_i(b)+s_i(a)`, consumer rows `Y_i=E_i(z)+s_i(b)+s_i(a)`, free block `a`, and clean diagonal

    D={v(b)+v(a): v is even}.

Let `G_0` count every zero-`z` gate, including source values obtained through consumer exits. The number of consumer-bearing gates is eleven. Suppose there are five actual entry occurrences, exactly three of them nonclean, and that all eleven consumer-bearing gates lie in the relaxed consumer target cones, obtained by cutting at every zero-`z` operand port.

**Theorem.** This class has `G_0>=11` and therefore total cost at least 22, with arbitrary feedback allowed.

## The relation forced by five entries

The [five-entry interface theorem](../compatibility/QUOTIENT.md#five-entries-and-six-mirrored-gates) gives entry-label span of dimension four, with a unique label relation supported on the entries whose influence traces are odd. All five traces are distinct in the present three-nonclean case, and at most two are even. The number of odd nonclean traces is even, and cannot be zero since three distinct even traces cannot fit in the six-gate mirror. Hence exactly two nonclean traces are odd. At least one of the two clean traces is odd as well.

Write the two clean labels as `c,d`. They are distinct: equality would give the unique label relation supported on those two clean occurrences, whereas that relation must include the two odd nonclean occurrences. Both are nonzero in the normalized interface, so they are independent. Put

    W=span{c,d},       p=c+d.

Name the two nonclean labels with odd traces `n1,n2`, and the third `k`. The unique label relation is therefore

    n1+n2=t,       t in {c,d,p}.                         (1)

Choose the naming so that `n1` is read earlier than `n2`. The value

    e=n1+k

is clean and outside `W`: otherwise all five labels would belong to the three-dimensional space `W+<n1>`, contrary to their rank four. Thus `c,d,e` are independent in `D`, and

    U=W direct-sum span{n1,k}.

Here `U` denotes the full entry-label span, not an output row. The sum is direct because the only nonzero clean value in `span{n1,k}` is `e`, which lies outside `W`.

## Dynamic replay with two net extra values

The following argument also proves a supplier lemma for any consumer budget when its actual entry labels are contained in `c,d,n1,n2,k`, satisfy (1), and have the stated rank. It uses the trace theorem only to establish this label geometry.

Replay original source-side gates in chronological order, preserving every original source value. Prepare extra values only by XORs of values already physically available in the replay. Keep every prepared value. Maintain these two closures:

1. Within the clean plane `W`, keep all values in the span of the currently available members of `{c,d,p}`. If two independent members are available, compute the third if absent.
2. Within `span{n1,k}`, compute `e=n1+k` once both `n1,k` are physically available, if it is not already available.

When the entry labelled `n2` is reached, `n1` is already physically available because its entry occurred earlier. The source value `n2` is also available: its original zero-`z` producer has already been replayed, or it was available initially. If `t` is absent, compute

    t=n1+n2

and apply the clean-plane closure. This prepares the decomposition `n2=n1+t` without reading a future value.

At every stage, each entry label already read is consequently the sum of one physically available value from each of the two groups. The groups are closed under sums of their currently supplied directions. Therefore every value in the span of those earlier labels has such a decomposition with both components available. In particular every source exit does: its source value lies in the span of earlier entry labels by induction through the consumer-bearing gates. Reproduce that exit using at most its original one XOR. An ordinary source gate is reproduced using its earlier source operands, or bypassed if its value is already available.

This proves the causal invariant throughout the original gate order, including when entry labels themselves have feedback ancestors. No basis value or clean group component is declared freely available before it is physically supplied or computed.

## Accounting for an advanced clean value

The clean-plane closure can compute only the three masks `c,d,p`, each at most once. The value `p` contributes at most one extra gate. If closure advances `c` or `d` before its original physical production, that original producer is later bypassed. These are distinct original zero-`z` gates: nonzero diagonals are neither ordinary coordinate inputs nor wholly free values. Thus each advanced `c` or `d` has its own later gate credit. If its original production occurred earlier, the value is already present and no completion gate is needed.

The second group contributes at most the one extra gate for `e`. All original source gates otherwise cost at most their original allowance. Hence the net replay cost is at most

    G_0+2.

After the original source values have been replayed, complete either group if necessary. All original labels are then available. The same accounting applies, and the resulting source-only supplier contains all four source rows together with

    c,d,c+d,e.

These four diagonals form a clean triangle plus an independent fourth value. Their [supplier lower bound](FOUR_DIAGONALS.md) is thirteen, giving `G_0+2>=13` and proving the theorem.

The credit for advancing `c` or `d` is necessary. A fixed greedy basis may omit one of them and leave three nonclean basis elements; merely naming a desired clean basis would not justify its availability at earlier exits. The dynamic closure supplies it causally and pays for it using its later original production.

## Scope

Combined with [the two-nonclean closure](TWO_NONCLEAN.md) and [the earlier four-entry and relaxed-cone reductions](FOUR_ENTRY_CLOSURE.md), a candidate of total at most 21 with exactly eleven consumer-bearing gates can now have only four or five nonclean occurrences among its five entries. Those cases are not excluded here. Larger consumer budgets and the unrestricted joint minimum remain open, and the unrestricted MixColumns interval remains 75 to 88.
