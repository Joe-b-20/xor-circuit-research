# Four-entry feedback and the target-cone trimming issue

2026-11-13. Hand proof by chronological replay and the four-diagonal supplier bound. Arbitrary feedback and intermediate cancellation are allowed. No circuit search or finite-family checks are used. These deductions leave the five-entry mixed eleven-gate consumer open; they do not prove an unrestricted joint minimum of 22.

Use ordinary source coordinates `b`, free coordinates `a`, and ordinary consumer coordinates `z`. The required rows are

    U_i = E_i(b)+s_i(a),
    Y_i = E_i(z)+s_i(b)+s_i(a).

Let `G_0` count gates with zero `z` part and `K` count all gates with nonzero `z` part, including gates used only by source exits. An actual entry is a gate reading a zero-`z` operand together with a nonzero-`z` operand. Its label is the former operand's full source value. Put

    D = { v(b)+v(a) : v is even }.

Every consumer-bearing source part is in the span of earlier entry labels. Consequently every source exit, obtained by adding two equal nonzero-`z` masks, is in the span of entry labels read earlier than that exit. This chronological span fact holds with feedback.

## The two-clean/two-nonclean four-entry pattern

Suppose the four actual labels form a basis `c,d,n,m`, with `c,d` in `D`, `n,m` outside `D`, and their span containing `D`. Then

    e=n+m,       p=c+d

satisfy that `c,d,e` are independent in `D`.

The [two-pair replay](FOUR_ENTRY_FEEDBACK.md#replay-with-two-specified-extra-values) reproduces every original source value in at most `G_0+2` source-only gates: use the fixed groups `{c,d}` and `{n,m}` and retain their sums `p,e` once made. Every exit is the sum of at most one available value from each group. If a group sum is needed before its original physical production, compute it then; chronological independence guarantees both labels are already supplied. Complete any unused group sum after replay.

The replay supplies the four rows and the four distinct diagonals `c,d,c+d,e`. The [four-diagonal lower bound](FOUR_DIAGONALS.md) therefore gives

    G_0+2 >= 13,       hence G_0 >= 11.                 (1)

In particular, with `K=11` this pattern has total cost at least 22. No target-cone trimming hypothesis is used in (1); the basis pattern is the explicit hypothesis.

## A single nonclean label

**Lemma.** If all actual nonclean entry labels are equal to one value `h` outside `D`, then `G_0>=11`, irrespective of the consumer-bearing budget.

Let the actual clean labels span `W`, a subspace of `D`. All consumer-bearing source parts are in `W+<h>`. Since the required consumer source parts span `D` and `h` is outside `D`, intersection with `D` gives `D=W`. Thus the clean actual labels span all three dimensions of `D`.

Choose their chronological greedy basis `a,b,c`: each is the first clean label read outside the span of its predecessors. These are actual physically supplied source values, and their independence makes `a,b,c,h` a basis of the full entry-label span. Any entry already read lies in the span of the selected basis values read by that time; hence the same is true of every earlier exit.

Replay the original zero-`z` gates in chronological order using the fixed groups

    {a,b},       {c,h}.

Compute and retain `a+b` and `c+h` when first needed, if absent. There are at most two additional XORs. A group sum is requested only when both basis values have already been physically supplied, by the preceding chronological span assertion. An original source gate with two source operands uses at most its original XOR. For an exit, take its unique basis expansion and use the corresponding value of each group, giving it in at most its original one XOR after the group sums are available. The process preserves earlier labels even when their original production had feedback ancestors.

At the end append either group sum if still absent. The resulting source-only supplier uses at most `G_0+2` gates and contains `a,b,a+b,c` together with all four `U_i`. These are four distinct diagonals of the triangle-plus-independent form. The four-diagonal bound proves the lemma. The argument only needs the first group sum for the lower bound, but allowing both preserves the uniform replay budget.

With `K=11`, the lemma gives total cost at least 22. Repeated occurrences of `h` are harmless for this replay statement; no distinct-label assumption is needed.

## All eleven gates versus the consumer target cones

Now suppose `K=11`. Cut the circuit at every zero-`z` operand port and treat that operand as a freely supplied label. In this relaxed consumer graph, let `K_Y` count the nonzero-`z` gates in the union of the four target cones. This is ancestry in the cut consumer graph, not ancestry through the full original source circuit. All target-cone statements in this section use this definition. The local sheet bound gives `10<=K_Y<=11`.

If `K_Y=10`, [entry deletion](../compatibility/QUOTIENT.md#general-projection-bound) forces all entries in that target-cone computation to belong to `D`: any label outside `D` would cost at least eleven consumer gates. Every consumer-bearing value in those cones consequently has source part in `D`.

There is only one additional consumer-bearing gate `v`. Both of its nonzero-`z` operands, if it has two, belong to the target cones or are ordinary inputs, so its source part is in `D`. If it has an entry operand, that is the sole possible occurrence of a nonclean actual entry label anywhere in the full consumer. Thus either all actual labels are clean, or all nonclean actual labels consist of one value `h`. In the former case [diagonal confinement](DIAGONAL_CONFINEMENT.md) gives `G_0>=12`; in the latter the preceding lemma gives `G_0>=11`. Both rule out a joint total at most 21.

It follows that in any candidate below 22 with `K=11`, all eleven consumer-bearing gates must belong to the consumer target cones. This justifies applying the trimmed [interface theorem](../compatibility/QUOTIENT.md#an-eleven-gate-interface-with-nonclean-labels) to all eleven gates. All-clean entries are already excluded by diagonal confinement. With a nonclean label, entry deletion leaves quotient rank exactly one, and equality in the interface theorem leaves only four or five entries. The four-entry pattern is exactly the two-clean/two-nonclean basis treated in (1), so it too is excluded.

**Remaining eleven-gate frontier.** Any joint circuit of total at most 21 with exactly eleven consumer-bearing gates must have five actual entries, entry-label span of dimension four with quotient dimension one over `D`, and all eleven consumer-bearing gates in the consumer target cones. The five-entry trace and label restrictions of `QUOTIENT.md` apply. This assertion does not exclude that remaining class or address other consumer budgets.

## An attained 22-gate four-entry pattern

The lower bound 22 for the four-entry pattern is attained. Start with the [specified twelve-gate source](../compatibility/DIAGONALS.md#explicit-event-free-12-gate-circuit), omit its gate `D12=U_1+E_2(b)`, and retain the other eleven gates. They supply all four source rows, the two diagonals

    c=D(01),       d=D(23),

and the two nonclean values

    n=U_1,         m=E_2(b),       n+m=D(12).

These four values form the required basis. For an explicit eleven-gate consumer, compute

    g = z2+z3
    q = g+z1
    u = q+c
    v0 = z0+n
    v = v0+m
    w = z3+d
    Y0 = u
    Y1 = g+v
    j = w+z0
    Y2 = j+z1
    k = u+v
    Y3 = k+w.

The [direct checker](check_four_diagonals.py) and its [recorded result](four-diagonal-check.json) evaluate this specified construction. The line `Y0=u` is an output alias, not a gate. The eleven XORs have entry labels `c,n,m,d`; all consumer gates belong to the target cones. Their outputs have free source parts `D(01),D(12),D(23),D(30)` and the required own triples. This is the recorded ten-gate consumer with its `D12` entry split into consecutive entries labelled `U_1` and `E_2(b)`, exactly offsetting the omitted source gate. Thus the source/consumer counts are `(11,11)` and the total is 22. Every gate is event-free by direct inspection, including the split entry: its two nonzero source-own masks are unequal, so they do not cancel the whole source block.

This construction witnesses sharpness of the closed four-entry subclass. It provides no lower bound for the remaining five-entry mixed consumer and no change to the unrestricted MixColumns interval 75 to 88.
