# Necessary source-side conditions for a four-entry mixed consumer

2026-11-13. Hand proof by chronological replay and paid-value counting. No circuit search or family checks. The result constrains the four-entry mixed profile and does not exclude it.

Consider the unrestricted joint 0/1-sheet problem, with source own block \(b\), free block \(a\), and consumer own block \(z\). The source targets are the four first-sheet rows \(U_c=E_c(b)+s_c(a)\). The consumer targets have own triples on \(z\) and source parts spanning the three-dimensional diagonal
\[
D=\{(v,v):v\text{ even}\}
\]
on \(b,a\). Count eleven gates with nonzero \(z\) part and suppose their actual entry labels span a four-dimensional space. Suppose there are four entries. The [four-entry interface theorem](../compatibility/QUOTIENT.md#four-entries-and-seven-mirrored-gates) says that their labels form a basis \(c,d,n,m\), where \(c,d\in D\) and \(n,m\notin D\). Put
\[
e=n+m,\qquad p=c+d.
\]
Then \(c,d,e\) is a basis of \(D\). We may work in a reduced circuit. In this tight profile the reductions cannot reduce the consumer-bearing count while leaving a joint circuit of total at most 21, since ten consumer-bearing gates already require 22 by [the five-diagonal consequence](FIVE_DIAGONALS.md). Fewer than ten are impossible by the local sheet bound.

## Replay with two specified extra values

Let \(G_0\) count the source-side gates, those zero on \(z\). In original gate order, the source part of each consumer-bearing gate is in the span of the entry labels that precede it. Accordingly, a source-side exit, the XOR of two operands with the same nonzero \(z\) mask, is in the span of the entry labels already read before it. Because the four actual labels form a basis, the representation of each exit in that basis uses only earlier labels.

Replay the original source-side gates in order. An ordinary source gate has source-side operands already available in replay. Copy it using one XOR or bypass it if its value is already available. To reproduce an exit, write its basis representation as a sum of one value from \(\operatorname{span}\{c,d\}\) and one from \(\operatorname{span}\{n,m\}\). Single labels are already physically supplied whenever needed. If the representation uses both \(c,d\), their sum \(p\) is either available or can be computed in one additional gate at that time. Likewise the sum \(e\) of \(n,m\) can be computed on the first need for both. Retain each of these pair sums once made. The two group values then give the exit in at most its original one gate. The argument uses only earlier physically supplied values, even if an earlier label was supplied through a source gate that originally followed a consumer gate.

After replay, append the XOR for \(e\) if it is still absent, using the now-supplied \(n,m\). If \(p\) has not been used, it may also be added at the end. In either case both pair sums and every original source value can be supplied in at most \(G_0+2\) gates. In particular this source-only supplier contains the four \(U_c\) and the independent diagonals \(c,d,e\). By [A12](../augmented/PROOF.md), it needs at least twelve gates, so \(G_0\ge10\).

## What equality forces

If the joint total is at most 21, then \(G_0=10\). The source-only replay therefore has no spare gate beyond the allowance for the two pair sums.

Neither \(e\) nor \(p\) is an original physical source value. If one is originally supplied before the replay needs to compute it, the corresponding additional pair gate is unnecessary. If the pair is computed before its original production, then that original paid gate is bypassed when the replay reaches it. These alternatives save at least one gate, even when the pair is only appended after replay. The replay would still supply all four source rows and the independent diagonals \(c,d,e\) in at most eleven gates, contradicting A12. Nonzero members of \(D\) are neither coordinate inputs of \(b\) nor wholly free values, so this count does not charge a free operand as a physical gate.

The original source values also cannot contain any other nonzero diagonal outside \(\{c,d,e,p\}\). Otherwise the replay supplying both pair sums in at most twelve gates would contain five distinct nonzero diagonals along with the four source rows. The [five-diagonal lower bound](FIVE_DIAGONALS.md) requires thirteen gates for such a supplier. Thus the only original nonzero diagonal values are \(c,d\).

No nonredundant original exit is clean. A nonzero clean exit would have to produce \(c\) or \(d\). Its unique basis representation uses that same label, so the label would have to be supplied and read already. This cannot be the first physical occurrence of its value, and a later copy is redundant. A zero exit likewise requires no replay gate.

Every nonclean exit has exactly one of \(n,m\) in its basis representation, since their classes modulo \(D\) agree and are nonzero. Thus a nonclean exit never needs the pair \(e\) during the grouped replay. If its representation omits at least one of \(c,d\), it can be replayed without any intermediate using at most its original one gate. If both occur, its value is \(n+p\) or \(m+p\). If no such exit occurs, no replay intermediate is needed. Appending only \(e\) would then give an augmented supplier in at most eleven gates, contradicting A12. Consequently at least one nonclean exit with value \(n+c+d\) or \(m+c+d\) is necessary.

## The consumer fibre of the required exit

For a return \(n+c+d\), project the consumer's source labels onto \(D\) along \(m\), fixing \(D\). The entry labelled \(m\) becomes a wire and can be bypassed. The resulting ten nonzero-own gates compute the same four consumer targets with the three independent labels \(c,d,e\). By the exact ten-gate bound, there can be no further duplicate, zero, or dead gate in this local computation. The two consumer operands of the original exit have the same nonzero own mask, and their projected source difference is \(e+c+d\), the sum of those three independent labels. If one original operand was the deleted entry, its nonfree parent supplies its projected value. The operands remain distinct under projection since their projected difference is nonzero. The case of return \(m+c+d\) uses the projection along \(n\).

By [the entry-matching lemma](ENTRY_MATCHING.md), a ten-gate three-entry consumer with one non-entry root per own-mask fibre cannot have such a pair of equal-own signals. The projected consumer must therefore have a fibre with multiple roots. It has at least two distinct nonzero even own masks: with only one, its first occurrence would be a pair \(q\) of own units and every odd own mask would lie among the units and those units plus \(q\), yielding at most two of the four triples. The four triples and two even masks require six non-entry first occurrences. Seven non-entry gates are available. Hence there are exactly two distinct even own masks and exactly one repeated non-entry own occurrence. There is one two-root fibre, which must contain the projected operands of the required return.

These conditions do not settle whether the required nonclean exit and the tight source budget can coexist. They also do not cover the five-entry mixed consumer.
