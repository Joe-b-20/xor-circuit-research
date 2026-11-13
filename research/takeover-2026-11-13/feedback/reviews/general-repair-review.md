# Review of the general entry-space repair bound

2026-11-13. Independent machine proof review of [GENERAL_REPAIR](../GENERAL_REPAIR.md). No circuit search or finite-family checks were run.

## The half-span threshold

Let \(S\) be the currently available distinct nonzero values in the fixed entry space, and let \(r=\dim\operatorname{span}S\). A missing nonzero exit target \(t\) lies in \(\operatorname{span}S\) by the chronological entry-span invariant. If \(|S|\ge 2^{r-1}\), then \(S\) and \(S+t\) both avoid \(0,t\). They lie in a common set of size \(2^r-2\), so their intersection is nonempty. An intersection witness expresses \(t\) as the sum of two distinct members of \(S\).

When a missing \(t\) is not a pair sum, \(S\cup\{0\}\) cannot be closed under addition. A pair of distinct members of \(S\) therefore supplies a new nonzero intermediate by one XOR. This pair cannot sum to \(t\) yet. The intermediate remains in the same span and increases \(|S|\) by one. Repeating reaches either a one-gate realization of \(t\) or the threshold, at which a one-gate realization is guaranteed. Every added intermediate is a physical gate and uses only values available at that point. Other source values outside the entry space remain available and can permit cheaper replacements.

## Potential accounting and chronology

For \(r\ge1\), set \(P=\max(0,2^{r-1}-|S|)\), with \(P=0\) at \(r=0\). Each extra intermediate above the original exit's one-gate allowance occurs while \(P>0\) and decreases it by exactly one. The exit itself is in the current span, so its replacement cannot increase the rank. Ordinary source-gate replay may add a new independent value in the entry space, but its rank increase is at most one. At an increase \(r\to r+1\) for \(r\ge1\), \(|S|\) grows by one, so the increase in \(P\) is at most \(2^{r-1}-1\). The increase from rank zero to rank one leaves \(P=0\). Other additions leave \(P\) unchanged or lower it.

For \(f(0)=0\) and \(f(r)=2^{r-1}-r\) for \(r\ge1\), these increases are bounded by \(f(r+1)-f(r)\). Initially \(|S|\ge r\), hence \(P\le f(r)\). The nonnegative potential bounds the number of charged decrements by its initial value plus all increases. Since rank grows by single increments and never exceeds \(d\), this is at most \(f(d)\). Original source gates contribute at most one gate each, yielding \(G_0+f(d)\). Zero is available under the stated convention.

The chronological invariant supplies each actual earlier entry label before it is needed, even if that label originated at an earlier exit. The proof uses no future label and no virtual value as a gate operand. Once the complete source replay is available, the original consumer-bearing gates can be copied in their original relative order. Each source operand now comes from the source-only replay. The resulting full circuit computes the same values and has no consumer-bearing ancestor of a source output. Its gate count is at most \(G+f(d)\).

## Sharp rank-three example

For independent source inputs \(u,v,w\) and consumer input \(z\), designate \(p=z+u\), \(q=p+v\), \(r=z+w\), and \(e=q+r=u+v+w\). Their four distinct non-input output masks give an unrestricted lower bound of four gates, attained by these equations. In a no-feedback circuit the cone of \(e\) requires at least two source-only gates for its three independent input coordinates. The three consumer-bearing output gates are distinct and lie outside that cone. Thus at least five gates are needed. Computing \(e\) in two gates and then reproducing \(p,q,r\) attains five. This proves sharpness for \(d=3\), without a claim of sharpness in higher dimensions or an application to the unresolved joint MixColumns minimum.

## Balanced-basis improvement

The stronger bound
\[
h(d)=2^{\lceil d/2\rceil}+2^{\lfloor d/2\rfloor}-d-2
\]
also holds. Initialize a basis from the source base values in \(D\), selecting independent values greedily. Assign them alternately to two groups. Thereafter assign each newly independent available value of \(D\) to the next group, without changing earlier memberships. Maintain all nonzero sums in each group's span as physically available wires.

When a new basis value \(g\) joins a group of size \(k\), every new group mask is either \(g\) itself or \(g+x\) for a nonzero old group mask \(x\). The first is already supplied as a base or by the ordinary source replay. All the other masks cost at most \(2^k-1\) gates, each reading two available values. Across all insertions into a group of final size \(k\), the number of extra gates is at most \(2^k-1-k\). Skipping values already available only lowers the count. Added group sums remain in the existing basis span and never create an independent basis direction.

An exit is in the span of the earlier actual entry labels, all already supplied. Thus it is already in the current basis span and cannot create a new basis direction. The two group spaces form a direct sum because their generators partition an independent basis. Each exit is the sum of at most one physically available value from each group, so it costs at most its original one gate. This establishes the chronological invariant even when later ordinary source gates read earlier exits. Complete the source replay and then append the original consumer-bearing gates in order.

At final rank \(r\le d\), the group sizes are \(\lceil r/2\rceil,\lfloor r/2\rfloor\). Their summed overhead is at most \(h(r)\le h(d)\). Monotonicity follows because each new insertion adds at most \(2^k-1\ge0\) to the overhead bound for its group. The bound is zero at ranks zero through two, one at rank three, and two at rank four. The existing rank-three witness proves sharpness there. The half-span argument above remains a separate adaptive estimate for a replay that already has many available values or needs few intermediate sums.

## Final proof and exact rank-four example

The revised [GENERAL_REPAIR](../GENERAL_REPAIR.md) uses the balanced-basis argument for its primary bound and retains the density argument as a separate adaptive method. The displayed increment of \(h\) is correct: increasing rank from \(r\) to \(r+1\) grows the smaller group, with old size \(\lfloor r/2\rfloor\), so the allowance increases by \(2^{\lfloor r/2\rfloor}-1\). The construction establishes the source-only chronological bound before moving all source work ahead of the consumer. No extra gate is needed for that reordering.

For the rank-four witness, the three consumer prefixes and the one consumer branch \(q=z+u_4\) are four distinct non-input values with nonzero \(z\) part. The fifth required value is the non-input source sum \(e=u_1+u_2+u_3+u_4\), obtained by one exit from the last prefix and \(q\). The five distinct required values force five gates, and the displayed feedback circuit uses exactly five.

Under no feedback, the ancestor cone of \(e\) is a source-only computation depending on four independent coordinate inputs. A connected binary ancestor graph with \(g\) gates and at least four inputs has \(2g\) operand edges and at least \(g+4\) vertices. Connectivity gives \(2g\ge g+3\), so \(g\ge3\). The four consumer output gates are distinct and outside that cone by their nonzero \(z\) parts, giving a total of at least seven. The three-gate source chain plus the four consumer gates attain seven. Every entry label belongs to the rank-four source space, so the two-gate allowance \(h(4)\) is sharp for the full problem. This witness uses ordinary independent source coordinates as stated and assumes only zero free. It gives no sharpness claim above rank four.

The displayed [verifier](../check_feedback.py) checks the two fixed constructions at each of ranks three and four, and the two decorated one-exit circuits. Its checks cover masks, gate counts, liveness, exits, and first-side cone ancestry. The exact lower bounds use the arguments above rather than the verifier.
