# The joint 0/1 frontier: an exact interface theorem and a counterexample

2026-11-13. Hand arguments and direct evaluation of two specified constructions only. No search, enumeration, exact circuit search, or computer-driven case elimination. The known joint lower bound remains 21 under the recorded no-feedback hypothesis; this note does not prove 22 or supply a 21-gate construction. The unrestricted MixColumns statement remains `75<=L<=88`.

## The two genuine 21-gate possibilities

Use four-coordinate blocks `a,b,b'`, with all vectors on `a` free. Write `E_c` for the triple omitting coordinate `c` and `s_c=e_c+e_(c+1)`, indices modulo four. The targets are

    U_c=E_c(b)+s_c(a),
    V_c=E_c(b')+s_c(b)+s_c(a).

Assume that no ancestor of a designated `U_c` has nonzero content on `b'`. Let `G_0` count gates zero on `b'`, and `G_1` count those nonzero on `b'`, after discarding wholly free gates. The existing ten-gate sheet lemma and joint01 Theorem B give `G_0>=10`, `G_1>=10`, and `G_0+G_1>=21`.

Consequently a 21-gate candidate has `(G_0,G_1)=(11,10)` or `(10,11)`. In the first case the existing ten-gate equality argument makes the `b'`-free side supply three independent values of the diagonal space

    D={v(b)+v(a): v has even weight},       dim D=3.

Excluding that case still requires strengthening the known augmented-sheet bound from 11 to 12. In the second case all ten `b'`-free gates belong to the first sheet's computation. It is tempting to assert that such a ten-gate computation contains no clean diagonal value; the explicit example below refutes that assertion.

The later [causal span argument](../tradeoff/SUPPLY_PROFILE.md) supplies an implicit step
in the first reduction: an extra b'-zero gate created as a consumer exit cannot provide
the first new independent clean direction. Thus a viable (11,10) profile really yields
an eleven-gate source-only augmented supplier, even when feedback was initially allowed.

## A ten-gate first sheet can already contain a clean diagonal

Here is a complete circuit for the four `U_c`, with free `a`-parts:

    p=b_0+b_1,
    q=b_0+b_3,
    u=q+s_1(a),
    v=p+s_2(a),
    w=b_2+s_3(a),
    d=u+v,
    U_0=d+w,
    U_1=u+b_2,
    U_2=v+b_3,
    U_3=w+p.

There are exactly ten gates. Direct expansion gives

    d=b_1+b_3+a_1+a_3,

a nonzero clean diagonal value. The four final values are precisely `E_c(b)+s_c(a)`. All ten gate values are distinct and non-input, and each serves a designated output. These claims were also verified by direct evaluation of this specified circuit; no circuit family was searched.

The construction arose by transposing a specified seven-gate circuit for four triple sums and three even exports. Its existence means that a proof of 22 cannot simply demand an eleventh gate whenever the first sheet supplies any clean diagonal. It says nothing about supplying three independent diagonal values in eleven gates, which remains the relevant open augmented-sheet question.

## Exact cost of avoiding every clean entry label

The following interface theorem is general. It applies to the second sheet with `D` the clean diagonal above, but does not itself exclude either 21-gate joint possibility.

Take four own inputs `x_0,...,x_3` and a free vector space `F`. Consider a circuit containing the four targets

    E_c(x)+d_c,             c=0,...,3,

where `d_0,...,d_3` span a three-dimensional subspace `D` and have exactly one nonzero relation, `d_0+d_1+d_2+d_3=0`.

Every counted gate has a nonzero own-input part. Other operand values are supplied free from `F`. An **entry** is a counted gate with one free operand; its free value is its label. Clean the circuit by retaining only target ancestors. Assume that every entry label is outside `D`.

**Theorem N.** Such a circuit needs at least eleven counted gates. If it has at most eleven, then it has exactly eleven gates and exactly five entries, and the following hold:

1. Its transpose has exactly six gates and computes the four triple sums.
2. The five entry labels span a four-dimensional space `U` containing `D`, and all lie in its single nonzero coset modulo `D`.
3. Their five influence traces have rank four and their sole relation is the sum of all five.
4. Exactly four traces are odd and one is even. The labels corresponding to the four odd traces have sum zero, and this is the sole relation among the five labels. The label of the even trace is outside the span of the other four.
5. Subtracting that fifth label from each of the other four gives a four-element circuit spanning `D`: these differences have rank three and their only relation is their total sum.

The eleven-gate lower bound is attained by the explicit construction below whenever `F` contains a vector outside `D`. If `F=D`, the stipulated entry-label avoidance class is empty.

### Proof

Let `K` be the cleaned gate count, `tau` its entry count, and `Phi:F_2^tau -> F` the map sending formal entry units to their labels. Replace each entry label by its own formal input. Let `l_c in F_2^tau` be the formal free-part mask at target `c`, and put

    L=span{l_0,l_1,l_2,l_3},
    zeta_j=((l_0)_j,...,(l_3)_j) in F_2^4.

Then `Phi(l_c)=d_c`. The transposition lemma gives a circuit `T` on four inputs with `K-tau` gates, containing the four triple sums and each `zeta_j` as a signal. The triple sums require at least six gates. Since the labels span `D`, `tau>=3`. If `K<=11`, then `tau<=5`.

**Three entries are impossible.** Three labels whose span contains the three-dimensional `D` all belong to `D`, contrary to the hypothesis.

**Four entries are impossible.** Since at least one label is outside `D`, their span has dimension at least four, hence exactly four. Thus `Phi` is injective, and `L` has dimension three. The only relation among the target masks is therefore their total sum, so every `zeta_j` is even and their span has dimension three.

There is a linear functional on the four-dimensional label span with kernel `D`; it takes value one at each label because all four are outside `D`. Applying it to the target equations shows that every `l_c` has even coordinate sum. Equivalently, the four traces sum to zero. Four vectors of rank three whose total sum is zero are distinct and nonzero. They are four distinct even gate values in `T`, disjoint from its four odd triple-sum gate values. Hence `T` has at least eight gates and `K>=4+8=12`, a contradiction.

**Five entries force the stated structure.** Now `K<=11` and the six-gate triple-sum minimum imply `K=11` and `|T|=6`.

The space `L` cannot have dimension three. If it did, `Phi` would be injective on `L`, so the formal target masks would again have total sum zero and the traces would be even of rank three. Three distinct independent even traces need three gate values besides the four odd triple sums, requiring at least seven gates in `T`. Thus `dim L=4`.

The image `Phi(L)=D` has dimension three, so `ker Phi` is nonzero. The five labels span a space containing `D` and an outside vector, hence of dimension at least four. Consequently their span `U` has dimension exactly four, and `ker Phi` is one-dimensional and lies in `L`.

Let `lambda` be the nonzero functional on `U` with kernel `D`. Every label is outside `D`, so all five have `lambda` value one. The target equations imply `L` is contained in the even subspace of `F_2^5`. Both have dimension four, so they are equal. The trace matrix therefore has rank four and its unique column relation is the all-ones vector: the five traces form a five-element circuit.

Their sum being zero, the number of odd traces is even. The six-gate transpose has four distinct odd triple-sum gates; at most two of its remaining gate values are even, and its inputs are odd. The five distinct nonzero traces therefore cannot contain three or more even vectors. Exactly four are odd and one is even.

The vector `l_0+l_1+l_2+l_3` has a one in exactly those four coordinates whose traces are odd. It is nonzero and is killed by `Phi`, since the `d_c` sum to zero. It therefore spans `ker Phi`. This proves the claimed unique four-label relation and independence of the fifth label from their span.

All labels lie in the same nonzero coset of `D`. If `h` is the fifth label, the four differences `phi_j+h` lie in `D`; the just-proved unique label relation implies that their only nonzero relation is the sum of all four. They span the three-dimensional `D`. QED.

### Explicit eleven-gate attainment

Choose any `h outside D` and put `q_c=h+d_c`. All five labels `h,q_0,...,q_3` are outside `D`. Compute

    g_1=x_0+x_1,
    g_2=g_1+h,
    g_3=g_2+x_2,
    g_4=g_3+x_3,
    g_5=g_4+x_0,
    O_0=g_5+q_0,
    g_7=g_4+x_1,
    O_1=g_7+q_1,
    g_9=g_2+x_3,
    O_2=g_9+q_2,
    O_3=g_3+q_3.

There are eleven gates and exactly five entries. Expansion gives `O_c=E_c(x)+d_c`. This proves exactness for circuits whose used entry labels all avoid `D`, without asserting that avoidance is necessary or optimal when clean labels are also available.

The standalone `check_joint01.py` directly verifies both displayed constructions, including gate values, targets, distinctness, liveness, entry labels, and the second construction's trace and label ranks. It performs no circuit or configuration search.

## Consequence and remaining obligation for J01

For sheet 1, the clean free-part space is the diagonal `D`. If an at-most-eleven-gate `b'`-bearing portion uses no diagonal entry label, Theorem N forces the exact five-label affine configuration above among its actual available `b'`-free operands. That is a precise joint supply obligation; it does not treat these values as an arbitrary free basis or charge their pairwise differences as separate gates.

However, a ten-gate first sheet can already supply a clean diagonal, as the displayed counterexample shows. Thus an eleven-gate second sheet may use a mixture of clean and nonclean labels. Theorem N does not cover that mixed-label case. Nor does it prove that a ten-gate first sheet cannot supply its five nonclean labels.

To prove the full 22-gate joint bound, one still needs both of the following, or another argument covering them:

* rule out a first-sheet computation plus three independent diagonal suppliers in eleven `b'`-free gates;
* rule out all eleven-gate second-sheet interfaces that can be supplied by a ten-gate first-sheet computation, including interfaces with some diagonal labels.

No impossibility claim is made for either remaining task. The new exact interface theorem and the explicit counterexample narrow sound proof routes while leaving the existing 21-to-22 gap open.
