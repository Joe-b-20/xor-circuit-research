# Independent review: two repeated even trace pairs

2026-11-14. Independent machine review of [DOUBLE_EVEN_PAIR_CLOSED.md](../DOUBLE_EVEN_PAIR_CLOSED.md). This is an argument audit, not formal verification or human certification. No search or enumeration was used.

**Verdict:** the closure passes. It uses physical clean-value scarcity and chronological one-helper replay correctly, without assuming clean endpoints for the even-helper chains.

Two repeated even classes already contribute two independent trace relations, exhausting the two-dimensional kernel. Rank four forces the remaining traces to be two distinct odd values. Their occurrence pair is the unique actual-label relation, so their actual labels coincide. The quotient-signature identity makes this common label `c` clean, and makes the two repeated classes distinct nonzero quotient directions. The class sums give the independent clean basis `c,a+b,k+l` as claimed.

The connected equal-even-trace-chain lemma applies to both helpers, while even-wire separation keeps their entries in different own-mask fibres. Therefore any return path contains at most one of the two nonclean classes. The two `c` edges cannot be adjacent, because their outer physical values would coincide. Since the nonclean entries in a fibre form one connected chain, any `c` edges are leaves. A path with zero or two `c` edges needs at most the sum of its two possible nonclean labels; a path with one `c` can require an extra XOR only for `c+a+b` or `c+k+l`.

Those two possible values are distinct nonzero clean values, both different from the already physical `c`. The cap of two original nonzero clean values consequently permits at most one to appear as an exit. This counts actual physical exit values, not virtual path sums that need never be returned.

If neither occurs, all exits have one-XOR replay and the nine-gate source budget contradicts the local minimum ten. Otherwise `t=c+a` repairs every occurrence of the single difficult value `c+a+b`. Its operands have been read along that return's path before the exit, so the extra gate is causal; ordinary source gates and unrelated returns can be replayed in order. At most one extra source gate is needed.

Appending `k+l` then supplies the independent clean basis `c,c+a+b,k+l` within `G_0+2<=11` source gates, contradicting A12. Redundant or already available values only improve this bound. The scope remains the stated two repeated-even-class profile.
