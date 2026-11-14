# The four-nonclean three-term relation has zero replay overhead

2026-11-13. Structural hand proof using the original own-mask fibres, marked-wire transposition, and credits for advanced original source values. No circuit search, enumeration, or computer-driven case elimination is used.

## Statement

Use the unrestricted joint 0/1-sheet problem with free block `a`, ordinary source block `b`, and ordinary consumer block `z`. The required outputs are

    U_i=E_i(b)+s_i(a),
    Y_i=E_i(z)+s_i(b)+s_i(a),

and the clean diagonal is

    D={v(b)+v(a): v is even}.

Let `G_0` count all zero-`z` gates, including exits obtained by cancelling two consumer-bearing operands. Suppose the consumer has exactly eleven nonzero-`z` gates, all in its relaxed target cones after cutting at zero-`z` operand ports, and exactly five entry occurrences. Their actual labels are

    n1,n2,n3,n4,c,

where `n1,n2,n3,n4` are independent nonclean values and

    c=n1+n2

is clean. Thus this is the three-term-relation branch of the [remaining label profiles](FOUR_FIVE_FRONTIER.md).

**Theorem.** Every original source value has a chronological source-only realization with at most `G_0` gates. Hence this joint class has total cost at least 22, even with arbitrary original feedback.

The result does not depend on the earlier physical-clean-rank-one restriction. It does not use the nonclean unique-pair theorem.

## The two even traces have different own masks

The [five-entry interface theorem](../compatibility/QUOTIENT.md#five-entries-and-six-mirrored-gates) identifies the unique label relation with the support of the odd influence traces. Since the unique relation here is `n1+n2+c=0`, precisely these three entries have odd traces. The traces of `n3,n4` are even. All five traces are nonzero and distinct in the four-nonclean branch, so the latter two are distinct even masks.

The marked-wire argument applies to this eleven-gate, five-entry interface exactly as it does in [the earlier four-entry note](WIRE_DUALITY.md). Replace each entry use by its own formal input and expand fanout into binary copies. There are nine input ports, four output ports, eleven XOR nodes, and therefore six copy nodes by wire balance. Literal transposition has six XOR nodes and computes the four ordinary triples as well as the five trace outputs. Since six is the ordinary triple minimum, its only nonzero even gate values are its two distinct even helpers. These are exactly the traces of `n3,n4`.

Delete the five trace ports and suppress their unary entry-dual copies, marking the surviving wires. Reversing this reduced network returns the original own projection with the five entries bypassed. Therefore the ordinary derivative of each marked wire equals the own `z` mask of its original entry. This is a statement about the actual marked wires, rather than the full adjoint of a node that happens to carry the same value.

The two even helpers cannot have equal nonzero marked-wire derivatives. Each helper is read only by odd designated triple gates; the two helpers have disjoint reader sets, since a common reader would XOR two even masks and produce an impermissible third even gate. The full adjoints of the four designated triples are independent by their unitriangular terminal-output contributions. A nonzero derivative in either helper's copy tree sums a nonempty subset of its reader adjoints. Disjoint reader sets and independence make derivatives from the two trees unequal. The [central tight-fibre note](TIGHT_FIBRE_WIRES.md) records the general transfer and separation statements.

Consequently the `n3` and `n4` entries have different own masks. They lie in different original own-mask fibres.

## Every exit uses at most one of these two entries

Bypassing all five entries leaves exactly six non-entry gates in the ordinary `z` projection, computing the four triples. No projected gate can be zero, an input, or a duplicate: bypassing it would leave a triple circuit of at most five gates. Thus each own-mask fibre has exactly one ordinary-input or non-entry root. Every other node in that fibre is an entry, with one edge to its earlier nonfree operand. These edges form a rooted tree.

An exit's two consumer-bearing operands have equal own masks. The XOR of their full source parts is the sum of actual labels along the unique path between their nodes in that fibre tree. Every edge on that path is ancestral to one of the two operands, so its label was physically supplied and read before the exit.

The path cannot contain both the `n3` and `n4` entries, since those entries belong to different fibres. Its value is therefore the sum of

- a value in `span{n1,n2}={0,n1,n2,c}`, formed from the earlier path labels among `n1,n2,c`; and
- zero or the one earlier path label `n3` or `n4`.

There is no need to materialize the pair sum `n3+n4`.

## Chronological replay with credits

Replay all original zero-`z` gates in order, retaining previously supplied values. Ordinary source gates use at most their original XOR. Whenever two members of the triangle

    {n1,n2,c}

are physically available, compute the third if it is absent. Thus the span of the triangle members supplied so far is always physically available. An exit has the decomposition just established, with its first component in that maintained span and its second component already supplied. It uses at most its original one XOR. This induction applies even when later entry labels have feedback ancestors.

Triangle completion uses only original source values, each at most once. If a missing triangle value is an original ordinary input or permitted free value, it was already available initially and is never synthesized. Otherwise any completion preceding its original production receives credit by bypassing that later original zero-`z` gate. Distinct advanced masks receive distinct original gates. If the original producer occurred first, the value is already available and no completion is needed. The argument applies to `n1` and `n2` as well as to `c`; it does not assume the clean label arrives last or that the nonclean labels are paid gates.

If `R` is the set of triangle values supplied synthetically, at least `|R|` later original gates are bypassed. Hence total source replay cost is at most

    (G_0-|R|)+|R|=G_0.

Every original source value remains physically available no later than its original replay position.

## Joint consequence and scope

Compute this source-only realization first, then reproduce the original eleven consumer-bearing gates with the same entry labels. This gives a no-feedback joint realization of cost at most `G_0+11`. The [proved no-feedback joint minimum](../augmented/CONSEQUENCES.md#the-joint-two-sheet-problem) is 22. Therefore `G_0+11>=22`, proving the claimed lower bound.

This closes the four-nonclean three-term-relation branch. The proof by itself makes no assertion about the other four-nonclean label relations, the all-nonclean affine-plane branch, larger consumer budgets, or the unrestricted joint minimum. The unrestricted MixColumns interval remains 75 to 88.
