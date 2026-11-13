# The cost of entry labels outside the target span

2026-11-13. Hand proof by projection, transposition, and linear algebra. No search or circuit-family enumeration; the explicit constructions are directly evaluated. The result extends the all-nonclean case in [JOINT01](../row-cost/JOINT01.md) and leaves its 21-to-22 gap open.

## General projection bound

Let a circuit have ordinary coordinate inputs and a free vector space \(F\) on disjoint coordinates. Count only gates with nonzero ordinary part, and assume the required targets have nonzero ordinary parts. Let \(D\subseteq F\) be the span of their free parts. Trim to their designated cones and treat every operand with ordinary part zero as free. Each remaining gate reads at most one free operand. Call such a use an entry and its free operand its label.

Let \(U\) be the span of the entry labels. In particular \(D\subseteq U\): induction over the gates puts every computed free part in \(U\). Denote by \(L_D\) the minimum gate count for the same targets with only \(D\) free.

**Entry deletion certificate.** Choose any set \(I\) of entry occurrences whose label span \(C\) has \(C\cap D=\{0\}\). Then
\[
K\ge L_D+|I|.
\]
The labels need not be linearly independent. Distinct occurrences of an equal label count as distinct gates.

Extend \(C\) to a complement of \(D\) in \(U\), and project all free parts from \(U\) onto \(D\) along that complement, keeping the ordinary coordinates unchanged. The resulting gates still compute the required targets because the projection fixes their free parts. At each chosen entry the projected free operand is zero, so the gate becomes its other operand. Redirect and delete these gates in topological order. The argument also works if one chosen gate reads another: each redirect supplies the same projected mask to its readers. Every surviving gate still has nonzero ordinary part. Thus the circuit with only \(D\) free uses at most \(K-|I|\) gates. No restriction on the intermediate ordinary masks or cancellation is needed.

In particular choose actual entry labels whose images form a basis of \(U/D\). Their span is disjoint from \(D\). With \(c=\dim(U/D)\) this gives \(K\ge L_D+c\).

## Four triples and equality in the bound

Now take four own coordinates \(x_0,\ldots,x_3\) and require four targets \(E_c(x)+d_c\), where the \(E_c\) are the own triples and the \(d_c\) span a three-dimensional \(D\), with sole relation their all-four sum. A clean entry label lies in \(D\); a nonclean label lies outside \(D\). The ten-gate local sheet proof applies because it uses only the rank and relation of the labels. Thus \(L_D=10\) and \(K\ge10+c\), with no unknown optimum in this specialization. The following alternate proof tracks the counts needed for equality.

Replace each entry use by a formal input and let \(\Phi:\mathbb F_2^\tau\to F\) send formal units to the corresponding labels. Let \(Z\) be the \(4\times\tau\) matrix of formal free-input coefficients at the targets, and \(L\) its row space. The columns \(\zeta_i\) of \(Z\) are the entry traces. The target equations give \(\Phi(L)=D\). In particular the full label span has dimension \(3+c\), and \(L\) lies in the kernel of the map to \(F/D\). Writing \(r=\dim L\), we have
\[
r\in\{3,4\},\qquad \tau\ge r+c.
\]

The transpose on four inputs contains the four own triples and each trace as a signal, and its literal adjoint accumulation uses \(K-\tau\) gates. Its inputs are odd, and the four required triples are distinct odd non-input masks. If \(r=3\), \(\Phi|_L\) is injective, so the total sum of the four formal target rows is zero. Every trace is even, and three independent traces require three distinct nonzero even gate masks. Then \(K-\tau\ge7\). If \(r=4\), the six-gate triple-sum lower bound gives \(K-\tau\ge6\). Both cases imply \(K\ge10+c\). The argument permits repeated or zero traces. An individual label need not introduce a new direction modulo \(D\).

The coefficient of \(c\) is sharp. A ten-gate three-entry scheme exists for any such \(D\). Use a basis \(\alpha=d_0\), \(\beta=d_0+d_1\), \(\gamma=d_3\), and compute
\[
U=(x_2+x_3)+\alpha,\qquad V=x_0+\beta,\qquad W=x_1+\gamma,
\]
followed by \(U+x_1,\ U+V,\ (V+W)+x_3,\ (x_0+x_2)+W\). The label identities are \(\alpha,\alpha+\beta,\beta+\gamma,\gamma=d_0,d_1,d_2,d_3\), respectively. To realize a prescribed quotient rank \(c>0\), choose \(h_1,\ldots,h_c\) independent modulo \(D\) and replace the single entry adding \(\alpha\) by \(c+1\) consecutive entries with labels
\[
h_1,\ldots,h_c,\quad \alpha+\sum_{i=1}^c h_i.
\]
Their sum is \(\alpha\) and all intermediate own masks remain nonzero. This gives \(10+c\) gates. The construction concerns the free-label model. It does not guarantee these labels are jointly available in a producer circuit.

## An eleven-gate interface with nonclean labels

If \(K\le11\) and any label is nonclean, then \(c=1\) and \(K=11\). All nonclean labels have the same nonzero image modulo \(D\). No nonclean label value can occur twice, and no entry can have a zero label. Two occurrences of the same nonclean value, or one nonclean occurrence together with a zero label, would give a deletion certificate of size two. There are only two possibilities for the counts: \((\tau,r)=(4,3)\) or \((5,4)\). This follows from equality in the two branches of the proof, and does not require checking finite circuit configurations.

Write \(N\) for the set of nonclean entry occurrences and \(n\in\mathbb F_2^\tau\) for its indicator vector. In each case \(\tau=r+1\). Since the quotient map has kernel \(n^\perp\), the dimension condition yields
\[
L=n^\perp,\qquad \ker Z=\langle n\rangle.
\]
Thus the nonclean occurrences are exactly the support of the sole nonzero relation on the traces. In particular any trace repetition can occur only if \(|N|=2\), and then it is precisely the two nonclean traces.

### Four entries and seven mirrored gates

Here \(\Phi\) is injective, since its image has dimension four. The traces are all even, of rank three. Seven gates permit only three gate masks beyond the four odd triples. The trace rank already needs three distinct nonzero even masks, so there is no zero gate and no room for a fourth distinct trace. Every trace is nonzero, and exactly two traces coincide. Their relation shows that precisely those two labels are nonclean. The remaining two labels are clean. The two clean labels together with the sum of the two nonclean labels form a basis of \(D\): they are images under injective \(\Phi\) of the natural basis of \(n^\perp\).

This branch is attained by the split-entry construction above with \(c=1\). The two new nonclean entries have equal influence traces because they are consecutive additions on the same wire. In a joint circuit their sum is a required direction in \(D\), but need not be a physical gate.

### Five entries and six mirrored gates

In this case \(\ker\Phi\) is one-dimensional and lies in \(L\). Define \(o\in\mathbb F_2^5\) by \(o_i=1\) if the trace \(\zeta_i\) is odd and \(o_i=0\) otherwise. Then
\[
o=Z^\mathsf{T}(1,1,1,1)^\mathsf{T}\ne0,\qquad
\ker\Phi=\langle o\rangle,\qquad n\cdot o=0.
\]
The first identity follows by parity, and rank four implies nonzeroness. The image under \(\Phi\) is the sum of the four target labels, which vanishes. The dot product identity follows from \(o\in L=n^\perp\).

A six-gate transpose computing all triples cannot contain zero or repeated values. A gate equal to an earlier gate or an input could be bypassed. A zero gate could be removed by replacing all uses of zero by wires or further zeros and discarding the zeros. The remaining circuit would still compute the nonzero triple values in at most five gates. Thus the two gate masks beyond the required triples are distinct nonzero even masks, since every odd four-coordinate mask is an input or a triple. Consequently:

- There are at least two nonclean labels. A one-term relation on the traces would be a zero trace.
- With exactly two nonclean entries, their traces coincide, and the other three trace masks are distinct and independent together with one copy of the repeated mask.
- With at least three nonclean entries all five traces are distinct. At most two are even, and among nonclean entries the number of odd traces is even. In particular if all five are nonclean, there are exactly four odd traces and one even trace, recovering the all-nonclean structure.
- The unique label relation is the sum of the labels of the odd trace occurrences. It controls repetitions of *labels*, which need not coincide with repetitions of traces. Nonclean labels are distinct by the deletion certificate. Clean labels can repeat, consistently with the unique relation.

For example, if an interface in this branch has four nonclean entries, their traces are either all odd or have two even occurrences. If it has three nonclean entries, their traces contain exactly one even occurrence. These conclusions follow from the two available even masks and the relation \(n\cdot o=0\); they do not assert that every permitted pattern is realizable.

The label geometry has a useful equivalent form. Fix any nonclean label \(h\). The clean labels and the differences \(\phi_i+h\) for the other nonclean labels span \(D\), because their formal coefficient vectors span \(n^\perp\). Among these four formal generators there is exactly one relation, obtained from \(o\). In particular the dimension of the span of the clean labels alone is the number of clean labels, less one exactly when the support of \(o\) lies entirely among the clean entries.

Conversely, at the level of linear equations, a rank-four \(4\times5\) trace matrix \(Z\) with sole relation \(n\ne0\) determines which label assignments are possible. Let \(d:\mathbb F_2^4\to D\) send the four units to the target labels. On \(L=\operatorname{im} Z^\mathsf{T}\) define \(\Phi(Z^\mathsf{T}u)=d(u)\), which is well-defined by rank four. Extend \(\Phi\) to the remaining one-dimensional direction by a value outside \(D\). This produces a rank-four label assignment, nonclean exactly on \(\operatorname{supp}(n)\). This algebraic sufficiency does not by itself construct a circuit with that trace list or an actual producer that supplies its labels.

The five-entry branch can actually repeat a clean label. Choose \(h\notin D\) and \(\lambda=d_0+d_1=d_2+d_3\). Compute
\[
A=((x_2+x_3)+h)+(h+d_1),\qquad B=(x_0+x_1)+d_3.
\]
Then compute the four outputs in order as
\[
(A+x_1)+\lambda,\qquad A+x_0,\qquad (B+x_3)+\lambda,\qquad B+x_2.
\]
The first two values cost five gates and the outputs cost six. The five entries are \(h,h+d_1,d_3,\lambda,\lambda\), with two distinct nonclean labels and the clean label \(\lambda\) used twice. The two nonclean traces are both the even mask supported on rows 0 and 1. The other even trace is supported on rows 2 and 3. The repeated clean label has two different odd singleton traces, on rows 0 and 2. Thus distinctions among label values and among trace masks are separate even in an attained tight interface.

## Interfaces using only clean labels

If \(c=0\), the same gate count bounds the possible \((\tau,r)\) when \(K\le11\), without imposing a rank-one quotient relation on the traces:

- Three entries force \(r=3\), independent clean labels, and three independent even traces. The mirror has at least seven gates.
- Four entries with \(r=3\) require \(K=11\) and a seven-gate mirror. There are exactly three distinct nonzero even trace masks, one repeated.
- Four entries with \(r=4\) have four independent traces. The mirror has six or seven gates.
- Five entries force \(r=4\), \(K=11\), and a six-gate mirror. The kernel of the label map has dimension two, so the parity vector is a nonzero label relation but need not be the only one.

If \(K=11\), at most one entry can have label zero, by the deletion certificate applied to zero labels. For the specific joint 0/1 problem with a reduced first-sheet producer, an available zero label is unnecessary and can be bypassed.

## Consequence for the first two MixColumns sheets

For the eleven-gate second-sheet portion in the \((10,11)\) joint profile, any two independent quotient signatures among its actual entry labels are impossible. If a nonclean entry is present, every nonclean entry must therefore have the same image modulo the clean diagonal. The four-entry possibility then requires two actual clean suppliers and two actual nonclean suppliers whose difference completes a basis of the diagonal. The five-entry possibility requires the affine configuration and the unique label relation determined by the transpose's parity vector.

These conditions filter possible producer and consumer interfaces without assigning a paid gate to a virtual pairwise difference. They do not exclude the case where all entries are clean, show that a ten-gate producer cannot meet these constraints, or raise the established joint lower bound.

For the full joint problem, another direct consequence is useful. Under the recorded
no-feedback hypothesis, any joint circuit that actually reads an odd free-block-
`a` label has at least 22 gates. Otherwise project `a` onto its even subspace along
one such odd label. The required free parts are fixed, and its entry gate disappears.
The ordinary `b,b'` parts remain unchanged. Bypassing an entry follows its original
nonfree operand, so every resulting ancestor path to a first-sheet target follows an
original path; no-feedback survives. A circuit of size at most 21 would therefore
produce one of size at most 20 in the same class, contrary to the recorded lower bound 21.
Thus every actually read free label of a hypothetical joint 21 is even. This does not
restrict which free vectors are nominally available.

The [supplier theorem](INTERFACES.md) adds a constraint on actual available values that
is not implied by these linear label equations: it excludes the entirely nonclean
eleven-gate interface after a ten-gate first sheet.
