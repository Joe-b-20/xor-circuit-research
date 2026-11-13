# Structural foundations audit

2026-11-13. Independent machine reconstruction from checkpoint e89b8a2. The derivations use symbolic linear algebra, circuit order, and specified constructions. No search or finite-family checking was performed.

## Model and status

Each gate XORs two existing wires over GF(2). The inputs are independent bits, grouped into four-bit blocks by bit position in the four bytes. An output sheet is the four outputs at one position. With byte indices modulo four, let $u_c$ be a block unit, $t=\sum_c u_c$, $E_c=t+u_c$, and $s_c=u_c+u_{c+1}$. Sheet $j$ has $E_c$ on its own block $j$ and $s_c$ on the preceding block (block 7 for sheet 0). For $j=1,3,4$ it also has $s_c$ on block 7. This follows by writing byte output $c$ as $b_{c+1}+b_{c+2}+b_{c+3}+2(b_c+b_{c+1})$ and reducing the bit-7 shift by $x^8+x^4+x^3+x+1$.

The unconditional bounds remain $75\le L(\mathrm{MixColumns})\le 88$. Block monotonicity here means that each gate in an output's ancestor cone has block support contained in that output's support. An event-free circuit, in which no gate cancels an entire nonzero block, is block-monotone because supports grow along each edge. Block monotonicity can allow a block to disappear at an intermediate gate and be reintroduced before the output.

[RECORD §§3, 7, 9, 10, 17](../../structure-2026-11-11/RECORD.md), [checkpoint](../../structure-2026-11-11/CHECKPOINT.md), [summary](../../structure-2026-11-11/SUMMARY.md).

## Ten and thirteen gates for a single sheet

In the two-block model, the own-block units are available and every vector on the neighbouring block is free. The four required values are $(E_c,s_c)$. In the three-block model, every vector on either neighbouring block alone is free. A vector meeting both neighbours needs a gate. The four required values are $(E_c,s_c,s_c)$.

Redirect gates whose values are free to those values, and prune gates outside the resulting selected output cones. Replace each use of a free operand by a distinct formal input $z_i$. Write $\tau$ for the number of formal inputs and $K$ for the remaining gate count. Transpose the circuit by propagating the four output adjoints in reverse order. Each signal's adjoint adds the contributions of its operand occurrences and terminal uses. A signal with $d$ contributions takes $d-1$ XORs, counting multiplicities and using a wire for $d=1$. All signals are live and all own units are used, so the transpose has $(2K+4)-(K+4+\tau)=K-\tau$ gates. It contains the four triple sums on its four input adjoints and every trace $\zeta_i$ listing which formal output masks contain $z_i$.

For each free block separately, the trace matrix for its $z_i$'s factors the four $s_c$'s through those formal inputs. Its column span contains the three-dimensional even space because the only nonzero relation of the $s_c$'s is their total sum. If a block contributes exactly three $z_i$'s, its three traces are distinct nonzero even masks. Each is a gate of the transpose distinct from the four odd output masks.

The four triple sums alone need six gates. With at most five there is room for at most one even gate, which must be the first gate. If its mask is zero, adding it only copies existing odd masks. If it is $u_i+u_j$, it can generate directly only the two triples containing both $i,j$. The other two differ by $u_i+u_j$, so neither can be produced first. Six gates suffice by computing two disjoint pairs and adding each of the remaining units to each pair.

For one free block, $\tau\ge 3$. Exactly three forces at least seven transposed gates, and at least four gives $K\ge6+4$. For two separately free blocks, $\tau\ge6$. Exactly six forces seven transposed gates by the same trace count for either block. At least seven gives $K\ge6+7$. The lower bounds are 10 and 13. The two-block bound is attained by computing the triples in six gates and adding each free $s_c$ in one gate. For the three-block bound, first make the three diagonals $D(f)=(f,f)$ for $f=s_1,d_1,t$, where $d_i=u_i+u_{i+2}$. On the own block make $s_0,d_0,d_1$, then in order make

$$
h=u_3+D(s_1),\quad v=s_0+D(d_1),\quad o_1=d_0+h,\quad o_2=h+v,\quad
h'=o_1+D(t),\quad o_3=d_1+h',\quad o_0=v+h'.
$$

The neighbouring labels of $o_1,o_2,o_3,o_0$ are $s_1,s_2,s_3,s_0$ respectively, and their own masks are the corresponding triples.

This proof uses one formal input per free operand occurrence. In the three-block model one gate can use two such operands if its value meets both free blocks. The transposition count includes both occurrences. The earlier nine-gate argument counted the triple-sum gates and the three entries independently. The traces couple those counts.

[Local hand proof](../../structure-2026-11-11/tenth-gate/PROOF.md), [specified construction](../../structure-2026-11-11/rotation/REPORT.md).

## Charges and block-monotone bounds

Let $F_j$ consist of the gates with a nonzero own-block $j$ component in the ancestor cones of sheet $j$, including its output gates. Restrict these cones to $j$ and its predecessor. Each omitted gate restricts to a free vector on the predecessor, so the remaining gates realize the two-block problem. Thus $|F_j|\ge10$ in every circuit. For $\mu(v)=|\{j:v\in F_j\}|$, let $E=\sum_j (|F_j|-10)$, $R=\sum_v\max(\mu(v)-1,0)$, and $U=|\{v:\mu(v)=0\}|$. Then $G=80+E-R+U$. The local lemma alone gives no global compensation inequality $E+U\ge R$.

The output windows $W_j$ for $j=0,\dots,7$ are

$$
\{7,0\},\ \{0,1,7\},\ \{1,2\},\ \{2,3,7\},\ \{3,4,7\},\ \{4,5\},\ \{5,6\},\ \{6,7\}.
$$

There is no pair $j\ne k$ with $j\in W_k$ and $k\in W_j$. Hence the $F_j$'s are disjoint in a block-monotone circuit. Enlarge $F_3$ by including all gates in the sheet-3 cone that meet both 2 and 7. Only $W_3$ contains both, so the enlarged family is still disjoint from all the others. It has size at least 13, by the three-block lemma with single-block vectors on 2 and 7 free. This gives 83.

For 84, replace the families for sheets 0 and 1 by the union $H$ of their cones, excluding values supported only on 7 and zero. The cones are supported on $\{7,0,1\}$ and every gate in the sheet-0 cone avoids block 1. The intersections of this window with $W_2,\dots,W_7$ are respectively $\{1\}$, $\{7\}$, $\{7\}$, empty, empty, and $\{7\}$. None can support a gate in $H$ and one of the remaining charge families. In particular a pure block-7 gate is excluded from $H$, and the extra sheet-3 gates meet block 2. The local bound $|H|\ge21$ below therefore gives $21+13+5\cdot10=84$.

[RECORD §§7, 9, 17](../../structure-2026-11-11/RECORD.md), [block-monotone decomposition](../../structure-2026-11-11/rotation/REPORT-PART2.md).

## The joint count for sheets 0 and 1

The local problem has blocks 7, 0 and 1 and makes block 7 free. Let $C_0$ be the gates of the sheet-0 cone after replacing pure block-7 and zero values by free values. Let $D_1$ be the sheet-1 cone's gates nonzero on block 1. If the sheet-0 cone avoids block 1, these sets are disjoint. Each costs at least ten. For $D_1$ treat all values off block 1 as free and apply the two-block proof with labels $(s_c,s_c)$ on blocks 0 and 7.

If $|D_1|=10$, its transpose has either seven gates and three entries or six gates and four entries. In the first case the three traces are independent. In the second case their span contains the even space and cannot equal it, since the six-gate transpose has room for at most two distinct nonzero even traces. The four traces are then independent. In either case the rows of the trace matrix span the space on the formal inputs $z_i$, so the entry operands span exactly the diagonal even subspace $\{(e,e):e\text{ even}\}$ on blocks 0 and 7. Three independent such operands are gates outside $D_1$. If any lies outside $C_0$ it is the twenty-first gate. Otherwise apply the following lemma to $C_0$.

**Diagonal extension lemma.** A sheet circuit with the four required values $A_i=(E_i,p_i)$, $p_i=u_i+u_{i-1}$, and three independent diagonal masks $X_m=(v_m,v_m)$, with $v_m$ even, needs at least eleven gates when the second block is free. Reversing the byte indices changes the primal $s_i$ convention to $p_i$ and preserves diagonals.

Suppose there are ten gates. The local lemma implies all ten gates are necessary even for the four $A_i$'s. Consequently no gate has own part zero and no value repeats an earlier wire or a free value. A gate with a free operand is an entry, which repeats an own part. The seven required own parts are distinct non-unit masks, so there are at least seven first gates in their respective own parts. At least three entries supply the rank-three labels of the $A_i$'s. Thus there are exactly seven such first gates and three entries, every duplicate of an own part is an entry, and the entry operands are independent even labels. Call the three non-required gates auxiliary. Let $p$ count the required entries. Each adds a free label to an auxiliary because there is only one required value in any own part and all seven required own parts are non-unit.

The following properties count the other $7-p$ required gates. A named signal is an own unit or a required value.

- No required value is the sum of two named signals. All required values have nonzero second part, excluding a pair of units. An own unit added to $A_i$ could give a diagonal only by using $E_i+p_i=t+u_{i-1}$ as the unit, which is a triple. This also excludes a unit added to a diagonal yielding $A_i$. An equality $A_i+A_j=X_m$ for $i\ne j$ would require $E_i+E_j=p_i+p_j$, contrary to $u_{i-1}\ne u_{j-1}$. This also excludes $A_i+X_m=A_j$. Two diagonals cannot sum to another because their masks are independent. All other sums mixing units and required values have incompatible parity or second part.
- The seven required masks are independent. Adding their two components maps each $X_m$ to zero and the $A_i$'s to the four triple sums, which are independent because their matrix $I+J$ (with $J$ the all-ones matrix) squares to $I$ over GF(2). The $v_m$'s are also independent. Two different required masks with equal second part must be $A_i$ and $X_m$ with $v_m=p_i$. Their difference has first part $t+u_{i-1}$, a triple. In particular no pair of required masks differs by a pure own unit or pair.
- An auxiliary mask $\beta$ has at most one unordered representation as a required mask plus a named signal. Two representations using units would give a difference of required masks equal to a pure pair. Two using required masks would contradict their independence. One of each would require three distinct required values to sum to a pure own unit. A triple of three $A$'s has second part equal to the missing $p_i$. A triple of one $A_i$ and two diagonals with zero second part has first part $E_i+p_i$, of weight three. The remaining triples have even first-part weight. A pure own pair has no representation. When the unique representation is $\beta=R+R'$, it can serve at most one of $R,R'$ as a named-partner gate, by circuit order. This count excludes services with a free operand.

Each required first gate reads at least one auxiliary, by the first property. Thus $7-p\le3+2$. There are at most three named-partner services and at most two required sums of two auxiliaries. All three pairwise auxiliary sums cannot be required, since their sum is zero. This excludes $p\le1$.

For $p=2$, all three named-partner services and both auxiliary-pair services are required. The first gate must be the unique auxiliary entry $\gamma=(u_k,\pi)$, since a pure own pair has no service. Before the second auxiliary $\beta$, the only possible required gate is $X_\pi=\gamma+u_i$, if such a named partner gives a diagonal. A required entry cannot use $\gamma$'s unit first part. A required first gate can only use $\gamma$ and an earlier own unit, so by uniqueness of named service there is at most one. The second auxiliary is a first gate. A sum of two units has no service. The sum $u_a+X_\pi$ has its unique representation involving an older $X_\pi$, so it cannot serve it. The sum $\gamma+X_\pi$ is a unit. The remaining candidate $\beta=u_a+\gamma$ has $\beta+\gamma=u_a$. The other two auxiliary sums would then have to be required and differ by a unit, contradicting the second property.

For $p=3$, the first auxiliary $\beta_1$ is a pure own pair with no named-partner service. Thus both later auxiliaries must have a named-partner service and both allowable auxiliary-pair sums must be required. Before $\beta_2$, the only possible required gate is the entry $X_1$ in $\beta_1$'s own part. A pure own pair cannot serve, and $\beta_2=u_a+X_1$ has its unique representation involving older $X_1$, so it cannot serve. The sum $\beta_1+X_1$ is free. For the remaining candidate $\beta_2=\beta_1+u_a$, the two required auxiliary sums would again differ by $u_a$. This completes the proof.

An auxiliary can serve one required entry by adding a free vector and also serve a required first gate with a named partner. The proof counts these separately. The transpose forces exact diagonal operands in the ten-gate case for $D_1$. This proves the 21 bound under the stated ancestry hypothesis. The unrestricted 20 case and the restricted 22 bound remain open.

[Joint-sheet report](../../structure-2026-11-11/joint01/REPORT.md), [joint-sheet review](../../structure-2026-11-11/joint01/review/REVIEW.md), [second review with symbolic properties](../../structure-2026-11-11/review-joint01b/REVIEW.md).

## Why unconditional charge counting fails

There is a reduced live circuit with just 66 distinct charged gates. Compute the eight-bit parity $z_c$ of each byte in seven gates, then the four triple sums $H_c=\sum_{i\ne c}z_i$ in six gates. Each $H_c$ contains $E_c$ on every block. For each output $y_{c,j}$ let $r_{c,j}=H_c+y_{c,j}$, then make the output by adding $H_c+r_{c,j}$. The remainder misses block $j$ and has exactly three bits on each of the other seven blocks, because adding $s_c$ to $E_c$ swaps the membership of coordinates $c$ and $c+1$. Build each remainder from its inputs, taking its first four inputs from four different blocks. Every prefix of length at most three has weight at most three. Every longer prefix meets at least four blocks. Neither kind equals a MixColumns output, whose weight is at least five and whose window has at most three blocks.

Reuse the earliest wire carrying each prefix mask. This can reuse a prior remainder prefix, an input, or one of the 34 global gates. Outside the output gates all operands have disjoint input support, so every gate feeding a remainder stays within its support. Each remainder gate therefore lacks the own block of every output it feeds. All 34 global gates remain charged through the $H_c$'s and all 32 output gates are charged on their own blocks. No global or output masks repeat, and repeated remainder values are bypassed. Pruning dead gates preserves the charge count. Even without prefix reuse the gate count is at most $34+32(20+1)=706$, sufficient for the refutation.

This refutes an unrestricted lower bound of 80 on the **number of distinct charged gates**, even for reduced live circuits. The large amount of uncharged work leaves the total gate-count question open. The record also shows that a fixed reverse-order transposition rule can yield 66 on both sides for a specified witness. That check does not rule out other choices of transpose. A cancellation requires a second copy of the eliminated block component, but a single copy or gate can serve many cancellations and can already be present for other outputs. Theorem K restricts the kinds of partner that can close a cancellation path. It supplies no separate cost for each closure.

[Superposition construction and scope](../../structure-2026-11-11/cancel/SUPERPOSITION.md), [cancellation chase](../../structure-2026-11-11/cancel/CANCEL.md), [copy-rank study](../../structure-2026-11-11/copies/COPIES.md).

## Implications for the takeover

Simultaneous repair uses the 84 bound and event-free support growth. The 83 bound uses only the single-sheet lemmas. Both use the natural bit-position windows and the repeated adjacent-pair labels. An arbitrary block partition or rotation with reciprocal windows requires a separate argument.

The historical section 7 still includes its original computer-check paragraph. Sections 10 and 17 give symbolic replacements. The historical finite checks and conditional claims are documented in the record and its audit. They were not rerun. Equal 88-gate corpus sizes with and without cancellation do not establish that eliminating the feature preserves cost. Neither distinct-charge counting, a fixed transpose, nor the rank of copied components supplies the missing global cost bound.

[Finite-check disclosure](../../structure-2026-11-11/joint/FINITE_AUDIT.md), [checkpoint](../../structure-2026-11-11/CHECKPOINT.md).
