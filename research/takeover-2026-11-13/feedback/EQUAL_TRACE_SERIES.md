# Adjacent equal traces form a strict series segment

2026-11-14. Structural hand proof by local adjoint accumulation and the six-gate ordinary minimum. No circuit search or trace enumeration. The final source-count restrictions are conditional on a twelve-consumer candidate below 22.

## A zero accumulator is impossible in a tight mirror

Use a target-live consumer with `tau` entry occurrences and `K=tau+6` consumer-bearing gates for the four ordinary triples. Its literal mirror has six XORs and computes those four triples. After deleting the formal trace-output ports, it still has at most six XORs. The ordinary triple minimum is six, so it can contain no zero gate or dispensable gate. Every wire value in this mirror is nonzero: its inputs are coordinate units, and a zero gate would be removable.

At an original consumer node, any binary ordering of the reader-adjoint accumulation uses the same number of XORs. If a nonempty set of reader contributions has sum zero, it cannot consist of one contribution, because every contribution is a nonzero mirror wire value. If it has at least two contributions, accumulate that set first. This creates a paid zero XOR result in a literal mirror of the same six-gate budget. After discarding formal trace ports, deleting the zero gate and propagating zero would compute the four ordinary triples in at most five gates, a contradiction. The argument also covers the case in which the zero result becomes dead after trace ports are discarded.

Thus **no nonempty subset of the contributions accumulated at an original consumer node can have zero sum**.

## Equal traces can meet only in series

Suppose two adjacent entry edges have the same trace `alpha`.

They cannot be two outgoing edges of one original node. Their equal reader contributions would be a nonempty zero-sum subset, excluded above.

They must therefore be an incoming entry and an outgoing entry at their shared node `x`. The incoming trace is the full adjoint of `x`, while the outgoing trace is one reader contribution. Their equality means that all other reader and terminal contributions sum to zero. The zero-accumulator result forces that collection to be empty.

Consequently `x` has exactly one reader in the relaxed consumer graph, the second entry, and is not a designated consumer output. Source-exit uses are not edges of that cut graph and are not excluded. In particular, if the two entry equations are

    x=u+a,       y=x+b,

then every use of `x` other than the second entry is a zero-consumer exit in the full circuit. This is a restriction on the original wiring, not just equality of two trace columns.

## A physical pair sum would expose an already closed tail

Now suppose this segment belongs to a hypothetical joint circuit with twelve consumer gates and total at most 21. The [six-entry reduction](SIX_ENTRY_FRONTIER.md) supplies the tight-mirror hypotheses, and `G_0<=9`.

Let `A` be the original physical source-value set, including inputs, free values, and source gates. If `a+b` belongs to `A`, make it available no later than the second entry. If already present, reuse it. Otherwise compute it there from the already supplied `a,b`, and credit the later original first producer, which is bypassed when reached.

Replace the second entry equation by

    y=u+(a+b).

Its full value is unchanged. Retain the first entry `x=u+a` for any source-exit uses. Every other original value is preserved at its original time, while the source count does not increase. The first entry now lies outside the relaxed target cones, since its sole former consumer reader has been redirected. If it has no useful exit use, it can instead be removed.

The resulting circuit has either twelve consumer gates with an outside gate or at most eleven consumer gates, and still has total at most 21. Both are excluded by the [closed outside-entry and smaller-budget cases](SIX_ENTRY_FRONTIER.md). Hence

    a+b not in A.                                         (1)

This excludes a pair sum supplied anywhere in the original source, including later in the circuit. It is not restricted to a sum available before the original second entry.

## The conditional source count is exactly nine

Even without a physical credit, computing `a+b` requires at most one additional source gate. The same redirection leaves at most twelve consumer gates, with the first entry outside the target cones if it remains. The resulting total is at most `G_0+13`. The closed outside-entry and smaller-budget cases therefore give

    G_0+13>=22,       hence G_0>=9.

Together with the original candidate assumption `G_0<=9`, this forces `G_0=9`. Moreover, the intermediate `x` must have a useful source-exit reader. Otherwise remove it as well: the extra source gate is offset by one fewer consumer gate, giving a forbidden at-most-eleven-consumer circuit of no greater total.

Thus an adjacent equal-trace pair in a surviving twelve-consumer candidate requires a genuine feedback use of its intermediate value, exactly nine source gates, and an originally absent pair sum. These are conditional restrictions. They make no claim about equal traces in different fibres, nonadjacent equal traces, or circuits with other gate budgets.
