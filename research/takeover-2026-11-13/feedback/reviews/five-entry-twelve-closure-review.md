# Independent review of the five-entry twelve-consumer closure

2026-11-14. I independently reviewed the cost and chronology argument in [FIVE_ENTRY_TWELVE_CLOSED.md](../FIVE_ENTRY_TWELVE_CLOSED.md). It is valid under the structural lemmas stated in [CHAIN_FIBRES.md](../CHAIN_FIBRES.md), which are being reviewed separately. This review checks the use of those lemmas, the replay construction, and the source-supplier contradiction. It is machine review, not formal verification or human certification; no circuit search or enumeration was used.

**Verdict:** no material gap in the cost closure. Both trace profiles have a chronological source-only replay of at most `G_0+3` gates supplying a clean triangle and an independent clean value. At `G_0<=9`, the thirteen-gate supplier theorem excludes them.

The starting scope is correct: the consumer has exactly twelve gates, every one in a relaxed target cone, and exactly five entry occurrences. The source floor and quotient tax force rank five, so these five actual labels are independent. The imported chain result is used to describe actual returns; it does not grant a later clean endpoint as an early source operand.

Independence gives the required timing bridge. Every exit lies in the span of earlier read actual labels. Its expansion in the five labels is unique, so each label appearing in that expansion has already been read. An exit equal to one actual label must occur after that label's entry read and cannot first supply it. This is particularly important for the singleton clean labels: their original availability cannot be attributed to a useful first return.

## The `(3,1,1)` profile

The two singleton labels `e,f` are distinct independent physical clean values. The original clean-value cap leaves no other nonzero clean value, so every clean exit is redundant. Internal returns with three labels would be the third class sum `d` and cannot be useful; the remaining internal returns cost at most one XOR of earlier labels.

The chain description confines useful crossing returns to the size-three class and permits at most two distinct nonclean positions. If both occur, they are adjacent. In the expanded form `r=t+w`, the fixed outside-class offset `w` belongs to `span{e,f}` and the nonclean part `t` is a one- or two-label subset of the three-label class. The same offset applies to both crossing values.

The proof that `w` is nonzero is sound. A one-label value is already supplied by the independence argument. For a two-label value, those two distinct class labels have independent quotient signatures. Saturated quotient cost makes any physical difference pair for their sum lie in the selected-edge tree formed from their two actual entry edges. Such a path cannot join different original entry components. This excludes a useful crossing return with zero outside offset.

For the first useful crossing, any needed pair helper and the offset helper `e+f` use only support labels already read. Its own XOR is therefore paid by the original exit. If a second distinct crossing occurs, it differs from the retained first value by the one actual label between their adjacent chain positions. Both endpoint nodes have been produced by the time of the later exit, regardless of which position was returned first. The joining entry label consequently has already been read, so this reuse is causal and costs only the second exit's original allowance.

The only extra allowance is for `e+f`, one pair of class labels, and completion of their full three-label sum `d`. Unneeded helpers can be deferred until all original labels have been replayed. Thus the stated three extra gates preserve all original source values and supply `e,f,e+f,d`. No additional cost is silently assigned to the later clean endpoint or to further crossing values.

## The `(2,2,1)` profile

Internal paths have length at most two. A repeated-fibre chain contains at most one nonclean position, hence at most one distinct nonclean crossing value. It has expanded form `t+epsilon*f+zeta*e`, where `t` is one actual label in the chain's two-label class. With both coefficients zero it is already supplied; otherwise one XOR suffices after the indicated clean helpers are available.

The three helpers `d=a+b`, `f=c+h`, and `g=e+f` provide a clean triangle and an independent direction. Every remaining clean value is `d+e`, `d+f`, or `d+g`, and therefore uses at most one original exit XOR after helper completion. The single possible nonclean crossing similarly uses `t` and one of `e,f,g`.

The helper timing follows from unique expanded support. A needed class sum has both class labels already read. Whenever `g` is needed, the support already includes `e,c,h`, including when the return equals `g` itself. A return equal to a helper may pay for that helper with its original source gate; counting it as an extra helper only weakens the upper bound. Helpers unused during replay are appended at the end. Thus all exits and ordinary source gates are replayed within the original allowance plus at most three gates.

In both profiles the four final clean values have exactly the required geometry for [FOUR_DIAGONALS.md](../FOUR_DIAGONALS.md): three form a nonzero clean triangle and the fourth is independent of its plane. The contradiction is therefore to the proved thirteen-gate bound, rather than to an assumed optimal circuit. The note correctly closes only the target-live five-entry twelve-consumer case; it does not settle six entries, an outside consumer gate, larger consumer budgets, or unrestricted MixColumns.
