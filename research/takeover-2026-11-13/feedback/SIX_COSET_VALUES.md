# Six values in one diagonal coset require twelve source gates

2026-11-13. Structural hand proof by own-mask first occurrences, parity, and physical relation rank. No circuit search, enumeration, or computer-driven case elimination. The source bound permits arbitrary cancellation. No claim of literature novelty or formal verification is made.

## Source supply theorem

Use four ordinary source inputs `b_0,...,b_3` and a separate four-coordinate free block `a`. Put

    E_i = sum of the three coordinates other than i,
    s_i = e_i+e_(i+1),                  indices modulo four,
    U_i = E_i(b)+s_i(a),
    D = {v(b)+v(a): v has even weight}.

An available value is an ordinary coordinate input, any permitted free value on `a`, or a physical gate value. A coset here is an affine coset of the three-dimensional clean diagonal `D` in the full source-value space.

**Theorem.** A source circuit supplying all four rows `U_i` and six distinct available values in one coset of `D` requires at least twelve paid XOR gates. Equivalently, in any source circuit of at most eleven gates computing the four rows, every `D` coset contains at most five distinct available values.

The six values need not be ancestors of the row outputs. All six may be required exports. The theorem bounds physical supply, not the number of virtual sums in the available span. It makes no assertion that a five-value coset is attained at eleven gates.

Normalize a purported circuit of at most eleven gates by bypassing zero, duplicates, and wholly free paid values, retaining ancestors of the four rows and the six values. Write each value as `(beta,alpha)` on `b,a`. Every paid gate then has `beta!=0`. An entry reads a free operand and repeats its earlier nonfree operand's own mask `beta`.

The four row free parts span a three-dimensional space, so there are at least three source entries. Also at least two distinct nonzero even own masks must occur. With only one such mask `p`, its first occurrence is a pair of ordinary units. All reachable odd own masks then lie among the units and the units plus `p`; only two of the four triples occur there. With none, no triple can occur. Thus producing all four triples requires at least two distinct nonzero even own masks.

Both the parity of `beta` and the parity of `alpha` are constant on a `D` coset, and projection onto `beta` is injective within a coset. We use these structural distinctions, without enumerating cosets or circuits.

## A coset with even own parity

Among six distinct coset values, at most one has zero own mask and can be free. The other five have distinct nonzero even own masks and must be paid gates. Together with the four distinct row triples, they require at least nine non-input own first occurrences. The at least three entries are disjoint from those first occurrences. This gives at least twelve gates, a contradiction.

## Odd own parity with odd free parity

No value in this coset is an ordinary input or a row output, since those all have even free part. Nor is it wholly free, since its own parity is odd. Six coset values therefore give six odd-own gates in addition to the four row gates. The two necessary even-own masks require two more gates. Again the cost is at least twelve.

## Odd own parity with even free parity

Define the named set and residue map

    N={b_0,b_1,b_2,b_3,U_0,U_1,U_2,U_3},
    rho(beta,alpha)=beta+alpha.

On values with even free part, the kernel of `rho` is exactly `D`. The named residues are the eight distinct odd masks: `rho(b_i)=e_i` and `rho(U_i)=E_(i+1)`. Thus the coset has exactly one named value. At least five additional odd-own gates lie in it. The four row gates and the two required even-own gates exhaust the eleven-gate budget. Consequently there are exactly five odd helpers, all in this one coset; exactly two even gate values, call them `h_1,h_2`; and exactly six available values in the coset, a set `B` with `|B intersect N|=1`. A larger coset would already exceed the budget.

Every odd physical value belongs to `N union B` and has even free part. The two even gate own masks are distinct and nonzero. They and the four row triples require at least six non-entry own first occurrences. Thus at least six non-entry gates are present. This count does not assume that every gate lies in a row target cone and uses no transposition bound on the number of entries.

There is no gate with two even nonfree operands: before the later of the two even gates only one even value is available, and adding it to itself gives zero. Equivalently, the two distinct nonzero even own masks cannot support an even-only production. Every non-entry gate therefore corresponds to an odd-pair relation

    h_j=u+v

for two odd physical values, with one of the three values being the result gate.

### Named pair sums are unique

The sole nonzero relation among the eight named values is their all-eight sum. Vanishing free part selects either no rows or all four rows, since the row labels have only their all-four relation. In the latter case the own row sum is the sum of all four inputs, requiring every input as well. In particular a nonzero value has at most one expression as a pair of distinct named values.

### If an even value is nonclean, there are too few pairs

A clean even value has residue zero, so both members of any representing odd pair must lie in `B`: all other odd residues have only their one named representative. Translation by a nonzero value is a matching, hence it gives at most three pairs within the six-element set `B`.

For a nonclean even value with even free part, its residue is nonzero. No representing pair lies wholly inside `B`. A pair with one endpoint in `B` has its other endpoint at a uniquely specified named residue outside `B`. That named endpoint and the fixed sum determine at most one pair. Pairs entirely outside `B` are named pairs, with at most one by the preceding property. Thus a nonclean even value has at most two representing odd pairs. If an even value has odd free part, it has no odd-pair representation at all, because all odd physical nodes have even free part.

If either `h_1` or `h_2` is nonclean, the two values therefore have at most `3+2=5` odd-pair representations altogether. Each three-value relation can produce at most one gate: in a normalized acyclic circuit only the latest of its three distinct physical values can be obtained from the other two. This cannot supply the required six non-entry gates.

### If both even values are clean, the pairs have insufficient rank

It remains that `h_1,h_2` are clean. They are distinct nonzero binary values, hence linearly independent. All odd-pair relations are supported on the six odd nodes in `B` together with these two even nodes.

Consider their equations as formal vectors on physical nodes. Project onto the odd-node coordinates. The image lies in the incidence space of a graph on six vertices, of rank at most five. This projection is injective on the equation span: a formal combination with zero odd part is supported only on `h_1,h_2`, and evaluation makes it a linear relation on those two independent values, so its even coefficients also vanish. Therefore all available non-entry relation equations have rank at most five.

Actual non-entry gate equations are independent in formal physical-node coordinates. In a nonempty selected sum, the chronologically latest result appears in its own equation and cannot appear as an operand of an earlier selected gate, so it cannot cancel. The at least six non-entry gates would give rank at least six, a contradiction.

All cases are excluded, proving the source theorem. This extends the earlier [ten-gate coset cap](../compatibility/INTERFACES.md) from at most four available values at ten gates to at most five at eleven gates.

## The all-nonclean eleven-consumer case

Consider the unrestricted joint 0/1-sheet problem with exactly eleven consumer-bearing gates and suppose the total is at most 21, so the source side has `G_0<=10` gates. Earlier reductions place all eleven gates in relaxed consumer target cones and leave five distinct rank-four entry labels. The remaining all-nonclean profile has an affine plane of four labels `Q=q+W` and a fifth label `h` outside its linear span, all in the same nonzero `D` coset.

The [affine-fibre replay theorem](AFFINE_FIBRE_CLOSURE.md) shows that there is at most one exit value requiring extra repair:

    f=h+w,       w=q_i+q_j in W minus {0},

where `q_i,q_j` are plane labels read before the exit. Every other exit is replayed at no extra cost; this one costs at most one extra source gate. If no extra work is needed, cost-preserving replay contradicts the [no-feedback joint lower bound 22](../augmented/CONSEQUENCES.md). Thus the return `f` must occur as an original physical source value.

It is a sixth distinct value in the same nonclean `D` coset. It differs from `h` since `w!=0`. It is outside `Q`, since `h` is outside `span Q` while `w` belongs to that span. Source replay retains the original five labels and this returned value, together with all four source rows, in at most

    G_0+1 <= 11

source-only gates. The six-value coset theorem requires twelve, a contradiction. Hence the all-nonclean profile also has total cost at least 22, even with arbitrary feedback.

## Exact eleven-consumer joint minimum

Combining this last exclusion with [two-nonclean closure](TWO_NONCLEAN.md), [three-nonclean closure](THREE_NONCLEAN.md), [the three-term four-nonclean case](FOUR_NONCLEAN_PAIR_CLOSED.md), [the clean-outside affine-plane case](AFFINE_FIBRE_CLOSURE.md), and [the all-five-odd case](TIGHT_FIBRE_WIRES.md), as well as the earlier [four-entry and cone reduction](FOUR_ENTRY_CLOSURE.md), proves:

**Every joint circuit with exactly eleven consumer-bearing gates has total cost at least 22, with arbitrary feedback and cancellation.**

For completeness, normalize any putative counterexample before applying the interface classification. If deletion of redundant gates lowers the consumer count, the local sheet minimum leaves at least ten consumer-bearing gates. The [proved ten-consumer lower bound](FIVE_DIAGONALS.md) already excludes a normalized count of ten below total 22. Otherwise the count remains eleven and the preceding reductions apply. Thus normalization does not leave an unhandled smaller-budget case.

The specified [eleven-source/eleven-consumer construction](FOUR_ENTRY_CLOSURE.md#an-attained-22-gate-four-entry-pattern) attains 22. Thus the joint minimum at exactly eleven consumer-bearing gates is 22.

This does not settle larger consumer budgets or the unrestricted joint minimum. It does not change the unrestricted MixColumns interval 75 to 88 or the block-monotone lower bound 85.
