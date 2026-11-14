# Independent review: rank-four source floor and physical clean values

2026-11-14. I independently reviewed [RANK_FOUR_SOURCE_FLOOR.md](../RANK_FOUR_SOURCE_FLOOR.md) and [RANK_FOUR_TWO_CLEAN.md](../RANK_FOUR_TWO_CLEAN.md). I found no material gap. The review used chronological linear algebra and the existing hand-proved source bounds; no circuit search or family enumeration was used. This is machine review, not formal verification or human certification.

## Physical clean directions

For physical clean rank one or two, a clean plane `W` can be chosen to contain every original physical clean value. In rank two this is that span itself. The first actual nonclean label `n` and the first actual label `k` outside `W+<n>` exist because the entry span has dimension four. The latter label is nonclean, since all actual clean labels lie in `W`. Their sum is clean and outside `W`, so `Q=span{n,k}` is a complementary plane.

The chronology is valid even when original clean values are not entry labels or have not been produced yet. Every actual nonclean label is in `n+W` or `k+W`. Before the first `k` occurrence only the first coset has been read; the first occurrence of either representative is itself a pure `Q` value, and later labels in its coset have that already-read representative as their `Q` component. Actual clean labels are pure `W` values. Hence each entry-prefix span splits, exactly as required by credited replay. No unsupplied physical clean basis is assumed available.

The plane `Q` has only its clean pair sum potentially missing from the original value set. The plane `W` has at most one missing value at physical clean rank two, or at most two at rank one. Replay therefore supplies its full clean triangle and the independent clean value `n+k` within `G0+2` or `G0+3` gates. The four-diagonal lower bound thirteen gives the asserted source bounds eleven and ten. Physical clean rank three is already covered by the cited earlier theorem.

## No original nonzero clean value

Under `G0<=9` and entry rank four, generic two-extra-gate replay would preserve every original source value in at most eleven source gates. The six-value coset theorem consequently limits the original nonclean coset to five distinct physical values, including inputs and free values. Every nonzero actual entry is in that coset, so a chronological greedy basis accounts for four of its values and there is at most one additional value `t`.

Every exit belongs to the span of earlier actual entries. No greedy basis value can first be supplied by an exit: an exit preceding its first entry would contradict that basis choice, while one after its first entry merely repeats a source value already supplied before the entry. No nonzero clean exit exists under the physical clean assumption. Thus the sole possible first supply through feedback is `t`.

If no such first supply occurs, all exits can be bypassed and the source rows would cost at most nine source-only gates, contrary to their local minimum ten. Before the first exit producing `t`, no entry can yet read `t`; every earlier nonzero entry is a basis value. The first return is therefore a sum of already-read basis elements. All four basis elements and `t` have the same nonzero quotient coordinate over the clean diagonal, so that sum has odd weight. Since `t` is not itself a basis value, its weight is exactly three. One pair intermediate and the original exit gate supply it with one extra XOR.

Thereafter all exits are redundant: any returned basis value has already been physically supplied, and `t` is retained. The one-extra-gate replay preserves the four basis values and `t` in at most ten source-only gates. At ten this violates the earlier four-value coset cap; below ten the row minimum is already violated. The two generic replay budgets are used in a sound order: the initial two-extra bound only limits the original physical value set, and that limitation proves the later one-extra bound. It is not a claim that arbitrary rank-four replay costs only one extra gate.

Combining the cases proves `G0>=10` whenever the actual entry span has dimension at most four and contains the clean diagonal, independently of the number of consumer-bearing gates. At twelve consumer gates the entry-deletion bound limits the span to dimension five, so a joint candidate below 22 must have rank exactly five. The notes correctly leave that case and the unrestricted joint minimum open.
