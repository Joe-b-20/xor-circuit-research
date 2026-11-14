# Two repeated even trace pairs cannot give a cheaper six-entry consumer

2026-11-14. Structural hand proof with independent machine review. No circuit search, trace enumeration, or computer-driven elimination.

**Theorem.** In the remaining twelve-consumer, six-entry problem below total 22, the two even mirror helpers cannot each occur twice as entry traces.

Assume this profile occurs. Trace rank four forces the remaining two traces to be distinct odd values, independent together with the two even helpers. The unique actual-label relation is the indicator of odd trace positions, so these two odd occurrences have the same actual clean label `c`. Call the labels of the two repeated even classes `a,b` and `k,l`.

The five distinct labels `a,b,k,l,c` are independent. The four trace-class aggregates have their sole relation between the two singleton odd classes, and the target source span is

    D=span{c,d,f},       d=a+b,       f=k+l.

Thus `c,d,f` are independent clean diagonals. The pair classes have the two distinct nonzero quotient directions: `a,b` share one direction and `k,l` share another. This also follows from the two pair relations spanning `ker Z`. In particular all four pair labels are nonclean and occur once.

The original physical clean-value cap is two. Since `c` already occurs, at most one other nonzero clean source value can occur anywhere in the original circuit.

## Return paths in the two nonclean classes

Bypassing the six entries leaves the ordinary six-gate minimum, so each own-mask fibre is one entry tree. The [equal-even-trace chain lemma](TRIPLE_TRACE_CLOSED.md#equal-even-traces-in-one-fibre-form-a-chain) says that occurrences of one even trace in a fixed fibre form one connected chain. The two distinct even helpers have separated ordinary wire derivatives, so entries from the two pair classes cannot share a fibre.

Consequently a fibre containing nonclean entries consists of a chain of at most two labels from one pair, together with any `c` edges in that fibre. The two `c` edges cannot meet: their two-edge path would have zero full-value difference between distinct physical consumer nodes, contrary to saturated quotient rigidity. They cannot bridge separate pieces of the nonclean chain, because that chain is connected. Hence any `c` edges are leaves attached to it. Fibres without nonclean entries have no other possible labels.

An exit is the sum of labels on its fibre path, all read before the exit. With zero or two `c` edges its value is a sum of at most two nonclean labels and costs at most one source XOR. With one `c` edge and at most one nonclean edge the same bound holds. The only path expressions that can need another gate are

    c+a+b=c+d,       c+k+l=c+f.                           (1)

These are distinct nonzero clean values, and neither equals `c`. The physical clean-value cap therefore permits at most one of them to occur as an exit value. The argument does not assume that a path expression in (1) lacks some other cheap realization.

## One helper and one final clean sum

If no exit has one of the difficult path expressions (1), every exit is replayable within its original one-gate allowance. Chronological source-only replay would supply the four source rows with `G_0<=9` gates, contradicting their local minimum ten.

Otherwise rename the pair classes so the difficult value is `r=c+a+b`. Compute and retain the one helper

    t=c+a.

Every occurrence of `r` is then `t+b` and uses at most its original exit gate. The helper is introduced only when first needed. Both `c` and `a` have been read on the corresponding fibre path before that exit, so their source producers have already been replayed. All other exits cost at most their original allowance, and ordinary source gates are copied chronologically. Thus every original source value is preserved within `G_0+1` source gates.

After replay, append the other pair sum `f=k+l` in one gate. The resulting source-only circuit contains the four source rows and the independent clean values

    c, r=c+d, f.

Its cost is at most `G_0+2<=11`, contrary to the [three-diagonal supplier bound A12](../augmented/PROOF.md). This excludes the profile.

The proof does not need a clean endpoint for every mirror segment. It uses connected equal-even-trace chains, separation of the two helpers, and the fact that both possible difficult returns would themselves consume distinct physical clean-value slots. Other double-trace profiles remain outside this statement.

Independent review: [two repeated even pairs](reviews/double-even-pair-review.md). This is machine review, not formal verification or human certification.
