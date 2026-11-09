<!-- Provenance: Addendum C (batch 3), written by the qcert3 agent on 2026-11-08; copied verbatim from research/sprint-2026-11-07/experiments/qcert3/PROOF_ADDENDUM_3.md (sha256 096f4c60f59f2641ae7cceea4c35ffe1f6b8e36d22037b7e262b11b261c0630c; sprint branch sprint-2026-11-07-linear-maps, commit d351a6f). Only this line was added; delete it to recover the source byte for byte. Paths such as REPORT.md and qcert/ in the text refer to that source folder. -->
# Addendum C. The exact hub capacity (finite fact H2), the packing rows at q = 4, 5, the full-met rank rows, and per-case certificates

qcert3, 2026-11-08. This addendum is written in the notation of PROOF.md (the 75-gate note in
`lower-bound-proofs/mixcolumns-lb75/`), of Addendum A (`qcert/PROOF_ADDENDUM.md`) and of Addendum B
(`qcert2/PROOF_ADDENDUM_2.md`); lemma, fact and row numbers refer to PROOF.md unless they carry the letters A, B or C.
It replaces the hub split of Addendum B (Lemma H1, capacity 4 for every non-full helper) by the exact per-helper
capacity $3-r_i$ of finite fact H2 (Lemma H2, row HUB2), adds the packing rows PK4, PK5 of Lemma 10.4's argument at
$q=4,5$ and the rows FM7, FM9 of finite fact FM (the ranks of the labels that a full helper can meet), and records
exactly which package lemmas and finite facts every statement uses. It does **not** change the Theorem of PROOF.md and
claims **no** lower bound beyond 75: at $G=75$ the full systems leave 789 of the 7,416 oriented claims open by LP
status (REPORT.md, sections 1 and 4).

Every statement carries one of the labels **[proved]** (proof below, package lemmas and finite facts used as black
boxes), **[finite-checked]** (computed exactly by a program named here), **[certified]** (an exact integer
certificate checked by two independently written programs), **[read, not checked]** (a package or earlier-addendum
statement relied on as is). Finite fact H2 is stated exactly in C.2 and is [finite-checked] by four programs of three
agents; finite fact FM in C.6 by three programs of three agents.

---

## C.1 Definitions

Throughout, a normalized circuit of either orientation is fixed (Lemma 1.1), with its odd graph (section 4), labels,
helper types $(r_i,u_i,v_i)$, the aggregates $W,A,Z,E,D_0$ of section 10, *anchored* ($r_i\ge1$), *full* ($r_i=3$),
*bright* / *dark* missing labels and $q_D$ (Lemma 10.2), the spaces $C_\ell$ and $\operatorname{rank}(C_\ell)\le7$
(F6), the kinds of even+even gates with their counts $y_0,y_1,y_2$ and the per-label counts $Y_\ell,W_\ell,Z_\ell$ of
A.1, and the dark unknowns $y_{2d},F_b,F_d$ of B.1.

**Full values, pair values, $N(h)$.** A *full value* is an odd value with three boundary-triple representations
(F3: 80 for $M$, 112 for $M^{\mathsf T}$); by Lemma 4.4 and F3 the mask of a full helper is a full value and its three
represented relations use its three triples. A *pair value* is the XOR of two distinct boundary masks; it determines
its pair (F2). For an odd value $h\notin B$ put $N(h)=\{f\ \text{full}:\ h+f\ \text{a pair value}\}$ and, for
$f\in N(h)$, $P_f=$ the pair with XOR $h+f$. (B.1 used the same $N(h)$.)

**Full-met labels, $m_i$, $A$.** A missing label is *full-met* if it has an H-B edge at a full helper. For a helper $i$
let $m_i$ be the number of missing labels on the H-B edges of $i$ that have an H-B edge at a full helper *other than*
$i$. By Lemma 4.5 a missing label meets at most one full helper and by Lemma 4.1 a helper carries each label at most
once, so the number of full-met labels is exactly $A=\sum_{r=3}u_i\le q$ ((4.2)), and for $r_i\le2$ every full-met
label at $i$ is counted in $m_i$.

**The family of condition (C1).** For an odd value $h\notin B$, a set $R$ of $r\le2$ distinct triples with XOR $h$
and a set $S\subseteq N(h)$, write, over the formal coordinates $H_i$ (the hub), $H_f$ ($f\in S$) and $B_b$ ($b\in B$),

$$
\mathcal F(h,R,S)=\{H_f+T:\ f\in S,\ T\ \text{a triple of}\ f\}\ \cup\ \{H_i+T:\ T\in R\}\ \cup\ \{H_i+H_f+P_f:\ f\in S\},
$$

a family of $4|S|+r$ vectors (a triple $T$ or a pair $P$ stands for the sum of its $B_b$). Define

$$
\operatorname{cap}_r(h)=\max\{|S|:\ S\subseteq N(h),\ R\ \text{an}\ r\text{-set of triples of}\ h,\ \mathcal F(h,R,S)\ \text{linearly independent}\}
$$

($\operatorname{cap}_r(h)=0$ if $N(h)=\emptyset$ or $h$ has fewer than $r$ triples). The capacity $\operatorname{cap}(h)$ of
B.1 (finite fact H1) is the same maximum for the subfamily $\{H_f+T\}$ alone, so $\operatorname{cap}_0(h)\le\operatorname{cap}(h)$.

**Ranks of the labels $f+c$; $\operatorname{top}$, $\operatorname{top}_3$.** For each orientation let
$\Lambda=\{f+c:\ f\ \text{full},\ c\in B\}$ (distinct even values; 4,640 for $M$, 6,496 for $M^{\mathsf T}$). For
$a\ge0$ let $\operatorname{top}(a)$ be the sum of the $a$ largest values of $\operatorname{rank}(C_\ell)$, $\ell\in\Lambda$,
and $\operatorname{top}_3(a)$ the sum of the $a$ largest values of $\min(3,\operatorname{rank}(C_\ell)-1)$. Both are
concave in $a$ (sums of a non-increasing sequence).

**Counts by $u$.** $n_j=\#\{i:\ u_i=j\}$, so that $\#\{i:\ u_i\ge3\}=n_3+n_4+\dots+n_q$. (PROOF.md's (L23) writes
$N_j$ for the same count; the qhub report's statement of PK5 with $N_j=\#\{u\ge j\}$ is a notation slip, see C.5.)

---

## C.2 Finite fact H2 (the hub capacity under condition (C1))

**Finite fact H2.** [finite-checked] For each orientation and every odd value $h\notin B$,

$$
\operatorname{cap}_r(h)\le3-r\qquad(r=0,1,2),
$$

and the bound is attained. Exactly: $N(h)\ne\emptyset$ for 128,068 ($M$) / 177,412 ($M^{\mathsf T}$) values $h$;
$h$ has at least one triple for 12,580 / 17,140 of them and at least two for 440 / 616 (the values with fewer triples
than $r$ do not arise as masks of helpers with $r_i=r$, Lemma 4.4). The histograms of $\operatorname{cap}_r(h)$ over
these values are

| orientation | $r=0$ | $r=1$ | $r=2$ |
|---|---|---|---|
| $M$ | 1: 126,412; 2: 1,648; **3: 8** | 0: 11,392; 1: 1,124; **2: 64** | 0: 428; **1: 12** |
| $M^{\mathsf T}$ | 1: 174,320; 2: 3,072; **3: 20** | 0: 15,216; 1: 1,804; **2: 120** | 0: 592; **1: 24** |

The eight ($M$) / twenty ($M^{\mathsf T}$) values with $\operatorname{cap}_0(h)=3$ are exactly the values with
$\operatorname{cap}(h)=4$ of finite fact H1 (B.2): the mixed vectors $H_i+H_f+P_f$ make every 4-set of H1 dependent.

*The enumeration it rests on.* For each orientation: the 64 boundary masks (F2), the 41,664 boundary triples and the
full values (F3), the pair values and their pairs; for every $h$ with $N(h)\ne\emptyset$, every $r\in\{0,1,2\}$ with
$r\le\#\text{triples}(h)$, every $r$-subset $R$ of the triples of $h$ and every subset $S\subseteq N(h)$ ($|N(h)|\le15$),
the rank of $\mathcal F(h,R,S)$ over GF(2); since independence of $\mathcal F(h,R,S)$ is hereditary in $S$, a depth-first
extension of $S$ in increasing order is exhaustive. Computed by `qhub/hub2.py` (incremental basis with undo, DFS),
independently by `qhub/hub2_check.py` (batch elimination over all subsets of $N(h)$, no pruning, for $|N(h)|\le11$ and
over all subsets of size $\le5-r$ otherwise: a $(4-r)$-set would already refute the bound), and by
`qhubcheck/h2_check.py` (own matrix parse, own basis with lowest-bit pivots, all subsets by DFS): identical histograms,
identical attaining sets, 0 violations. Here, `qcert3/h2_tab3.py` (fourth implementation: own boundary parse, the rank
recomputed from scratch at every node of the depth-first extension by a fully reduced elimination, no incremental basis
and no size cap) reproduces the histograms, the attaining counts and the H1 histogram, finds 0 violations, and agrees with
the per-value table of `hub2.py` on all 141,088 ($M$) / 195,168 ($M^{\mathsf T}$) pairs $(r,h)$; `qcert3/stress_ext3.py` recomputes $\operatorname{cap}_{R_i}(h_i)$
(the maximum over $S$ for the helper's *actual* triples $R_i$) by exhaustive search for every non-full helper of every
phase of the 316 circuits and compares it with the table of `hub2.py`, and re-enumerates every maximal configuration
$(h,R,S)$ with $|S|=3-r$ at the attaining values (section C.8; counts identical to `qhubcheck/h2_check.py`).

The qhub report also tabulates the capacity under two further per-configuration conditions (the output assignment of
Lemma O1 and a boundary-degree excess $X$); they do not lower any maximum and **enter no row** of this addendum.

---

## C.3 Condition (C1): the gate-equation family and the two pivot steps [proved]

**Condition (C1).** Let $i$ be a helper with $r_i\le2$ and mask $h$, let $R$ be the set of its $r_i$ represented
triples (distinct, Lemma 4.4), and let $\ell_1,\dots,\ell_m$ be distinct missing labels at $i$, met through the H-B
edges $i$-$b_j$ ($\ell_j=h+b_j$), each of which has an H-B edge $f_j$-$c_j$ at a full helper $f_j$ ($\ell_j=f_j+c_j$;
we write $f_j$ for the helper and its mask). Then:

(a) $h+f_j=b_j+c_j$ is a pair value with pair $P_{f_j}=\{b_j,c_j\}$, $f_j\in N(h)$, and the $f_j$ are pairwise distinct;

(b) with $S=\{f_1,\dots,f_m\}$, the family $\mathcal F(h,R,S)$ is linearly independent.

*Proof.* (a) $h+b_j=f_j+c_j$ gives $h+f_j=b_j+c_j$. Here $b_j\ne c_j$: otherwise $h=f_j$, two distinct signals with
one mask (Lemma 1.1 (i)); so $h+f_j$ is a pair value, its pair is $\{b_j,c_j\}$ (F2), and $f_j$ is a full value
(Lemma 4.4, F3), so $f_j\in N(h)$. If $f_j=f_{j'}$ for $j\ne j'$, the helpers $i$ and $f_j$ ($i\ne f_j$ since $r_i\le2$)
would carry the two missing labels $\ell_j,\ell_{j'}$ on their H-B edges, against Lemma 4.6.

(b) *The gate-equation family.* Consider the following gate equations of the circuit, written as formal vectors over
the coordinates of all signals ($E_\lambda$ for an even signal $\lambda$):

1. for every represented label $\lambda$ carried by a represented edge of $i$ or of some $f_j$: its B-B reference
   equation $E_\lambda+B_b+B_c$ (unique, Lemma 4.1);
2. the $r_i$ represented H-B equations $E_\lambda+H_i+B_a$ of $i$ and the $3m$ represented H-B equations
   $E_\lambda+H_{f_j}+B_a$ of the $f_j$;
3. for every $j$ the two missing H-B equations $E_{\ell_j}+H_i+B_{b_j}$ and $E_{\ell_j}+H_{f_j}+B_{c_j}$.

These are equations of pairwise distinct gates (distinct edges of the odd graph; a reference is a B-B edge, the others
H-B edges at distinct (helper, boundary) pairs; a label with two represented edges at $i$ and at $f_j$ contributes one
reference), hence linearly independent as formal vectors: in a nonempty combination the latest result signal cannot
cancel (Lemma 1.1, the argument of the proof of Lemma 4.4). The missing labels $\ell_j$ are distinct from every
represented label and from each other (distinct edges at $i$ carry distinct labels, Lemma 4.1), so after the two steps
below each $E_{\ell_j}$ and each $E_\lambda$ is *private* to the rows named.

*Pivot step 1 (references).* For every represented label $\lambda$ of item 1, add its reference row to every row of
item 2 carrying $\lambda$. A row $E_\lambda+H_x+B_a$ becomes $H_x+B_a+B_b+B_c=H_x+T$ with $T=\{a,b,c\}$ the triple of
that represented relation (Lemma 4.4; $a\notin\{b,c\}$ since $h_x\notin B$). Now $E_\lambda$ occurs only in the
reference row; delete the reference rows. (Adding a row to others is invertible; deleting a row that holds a coordinate
occurring in no other row preserves the independence of the remaining rows.) What remains of items 1-2 is
$\{H_i+T:\ T\in R\}\cup\{H_{f_j}+T:\ T\ \text{a triple of}\ f_j\}$.

*Pivot step 2 (the missing labels).* For every $j$, add the hub's missing row $E_{\ell_j}+H_i+B_{b_j}$ to the full
helper's missing row $E_{\ell_j}+H_{f_j}+B_{c_j}$: the latter becomes $H_i+H_{f_j}+B_{b_j}+B_{c_j}=H_i+H_{f_j}+P_{f_j}$.
Now $E_{\ell_j}$ occurs only in the hub's row; delete it.

The surviving rows are exactly $\mathcal F(h,R,S)$, obtained from an independent family by invertible operations and
deletions of rows with private coordinates; hence independent. $\square$

Uses: Lemma 1.1, Lemma 4.1, Lemma 4.4 (and its proof), Lemma 4.6; F2, F3 (through 4.4). Nothing beyond normalization.
The family does not depend on which end of $P_{f_j}$ is the hub's (the two choices give the same vector). Finite fact H1
(B.2) is the special case that keeps only the $3m$ vectors $H_{f_j}+T$; the per-label rank condition
$\operatorname{rank}(C_{\ell_j})\ge3+r_i$ of qreal is a consequence (project away the hub) and is not used as a row.

---

## C.4 Lemma H2, row HUB2 and its exact case split [proved]

**Lemma H2.** In every normalized circuit of either orientation, every helper $i$ satisfies

$$
r_i+m_i\le3 .
$$

*Proof.* If $r_i=3$: $i$ is full, and a missing label at $i$ meets no other full helper (Lemma 4.5), so $m_i=0$. If
$r_i\le2$: let $\ell_1,\dots,\ell_{m_i}$ be the missing labels at $i$ met by full helpers $f_1,\dots,f_{m_i}$, and $R$ the
$r_i$ represented triples of $i$. By (C1)(a) the $f_j$ are distinct elements of $N(h_i)$ and by (C1)(b)
$\mathcal F(h_i,R,S)$ is independent, $S=\{f_j\}$; hence $m_i=|S|\le\operatorname{cap}_{r_i}(h_i)\le3-r_i$ (finite
fact H2). $\square$

Uses: Lemmas 1.1, 4.1, 4.4, 4.5, 4.6 (hence F2, F3, F4), (C1), H2.

**Row HUB2.** [proved] Every helper $i$ with $r_i\le2$ satisfies

$$
u_i\ \le\ (3-r_i)+(q-A),\qquad A=\sum_{r=3}u\,n .
$$

*Proof.* The $u_i$ missing labels at $i$ are distinct (Lemma 4.1); $m_i$ of them are full-met and the other $u_i-m_i$
are among the $q-A$ missing labels that meet no full helper (C.1: the full-met labels number exactly $A$). So
$u_i\le m_i+(q-A)\le(3-r_i)+(q-A)$ by Lemma H2. $\square$

**The exact case split.** [proved] In the local system the row is not linear in the type counts (it bounds $u$ per
helper by a quantity containing $A$) and is used as a disjunction on the integer $A\in\{0,\dots,q\}$ ((4.2)):

- **$q\le1$: no split.** For every $r\le2$ and every $A\le q$: $u_i\le q\le(3-r)+(q-1)\le(3-r)+(q-A)$ when $q=1$, and
  $u_i=0$ when $q=0$; the row is vacuous.
- **$q\ge2$, case $A=a$ for an integer $2\le a\le q$.** The equality $\sum_{r=3}un=a$ holds (two inequalities), and
  every helper with $r\le2$ has $u\le(3-r)+(q-a)$: the types $(r,u,v)$ with $r\le2$ and $u>(3-r)+(q-a)$ have $n=0$ and
  their columns are removed. (For $a=2$ only the types $(2,q,v)$ go; for $a=q$ the types with $u>3-r$.)
- **$q\ge2$, case $A\le1$.** The row $\sum_{r=3}un\le1$ holds; the bound $u_i\le(3-r_i)+(q-A)\ge(3-r_i)+q-1\ge q$ is
  vacuous, no column is removed.

*Exhaustiveness.* $A$ is a count of labels, an integer with $0\le A\le q$; so it lies in exactly one of
$\{0,1\},\{2\},\dots,\{q\}$ ($q$ cases). *Soundness.* In its case a phase satisfies every row of the case system and
has no helper of a removed type, so its type counts are a nonnegative solution of the case system: the case system is
a relaxation. Hence **if every case system of a key is infeasible, no phase with that key exists.** $\square$

Remarks. (i) The case $A\le1$ admits fractional LP solutions with $A$ non-integral; the refinement to the integer cases
$A=0,1$ gives the same key sets at $G=75$ (qhubcheck, variant HUB2X) and is not used. (ii) Every HUB2 case system is at
least as strong as the H1 case system containing it (the H1 split removes only the types with $u>4+q-a$, and
$A\le1\Rightarrow A\le4$), so a key infeasible under Addendum B's systems is infeasible here: the bounds $k,l$ of every
claim are monotone (REPORT.md, section 1). (iii) No known circuit has $A\ge1$ (section C.8), so the row is a positive
control only on synthetic local configurations.

---

## C.5 The packing rows PK4, PK5 [proved]

**Lemma PK (Lemma 10.4's argument at $q=4,5$).** Every phase satisfies

$$
q=4:\quad n_3+n_4\le1\quad\text{(PK4)},\qquad\qquad q=5:\quad n_3+2n_4+2n_5\le2\quad\text{(PK5)},
$$

with $n_j=\#\{i:\ u_i=j\}$ (C.1).

*Proof.* The sets of missing labels on the H-B edges of distinct helpers intersect in at most one label (Lemma 4.6).
The helpers with $u_i\ge3$ therefore carry pairwise distinct subsets of size $\ge3$ of the $q$-set of missing labels,
pairwise meeting in at most one element (this is the premise of the proof of Lemma 10.4). $q=4$: two distinct subsets
of size $\ge3$ of a 4-set meet in at least $3+3-4=2$ elements; so at most one helper has $u\ge3$: $n_3+n_4\le1$.
$q=5$: a subset of size $\ge4$ meets every other subset of size $\ge3$ in at least $4+3-5=2$ elements, so if
$n_4+n_5\ge1$ then $n_4+n_5=1$ and $n_3=0$; three 3-subsets pairwise meeting in at most one element cover at least
$3\cdot3-3=6>5$ points, so $n_3\le2$. Hence the achievable count vectors $(n_3,n_4,n_5)$ are
$(0,0,0),(1,0,0),(2,0,0),(0,1,0),(0,0,1)$, and each satisfies $n_3+2n_4+2n_5\le2$. $\square$

Uses: Lemma 4.6 and the definitions of section 4 (nothing beyond normalization). [finite-checked] in addition by
`qhubcheck/pk_enum.py`: the 6 ($q=4$) / 32 ($q=5$) families of distinct $\ge3$-subsets pairwise meeting in $\le1$
element, their count vectors as listed, PK4 and PK5 valid and tight, PK5 the unique nontrivial facet of the convex hull
of the count vectors; the package's (L23) at $q=6,7$ re-derived there as well (353 / 8,390 families). *Notation.* The
qhub report writes PK5 as "$N_3+2N_4\le2$ with $N_j=\#\{u\ge j\}$"; read literally that is $n_3+3n_4+3n_5\le2$, which
a single helper with $u=4$ violates. The row implemented there (`qh_lp.py`), by qhubcheck, and here is PK5 as stated
above (coefficients 1, 2, 2 on $u=3,4,5$, constant 2).

---

## C.6 Finite fact FM and the rows FM7, FM9

**Finite fact FM.** [finite-checked] For each orientation, over the distinct labels $\ell\in\Lambda=\{f+c\}$ (C.1)
the histogram of $\operatorname{rank}(C_\ell)$ is

$$
M:\ \{3{:}\,3{,}696,\ 4{:}\,692,\ 5{:}\,140,\ 6{:}\,108,\ 7{:}\,4\}\ (4{,}640\ \text{labels}),\qquad
M^{\mathsf T}:\ \{3{:}\,4{,}960,\ 4{:}\,1{,}176,\ 5{:}\,144,\ 6{:}\,216\}\ (6{,}496\ \text{labels});
$$

every label $f+c$ has rank $\ge3$ (the three forms $E_\ell+T\triangle\{c\}$, $T$ a triple of $f$, lie in $C_\ell$ and
their differences have rank 2) and rank $\le7$ (F6; rank 7 only at the four labels of F11, for $M$). Consequently

$$
\operatorname{top}(a)=\begin{cases}7a&a\le4\\28+6(a-4)&4\le a\le112\end{cases}\ (M),\qquad\operatorname{top}(a)=6a\ (a\le216)\ (M^{\mathsf T}),\qquad
\operatorname{top}_3(a)=3a\ (a\le944\ /\ 1{,}536).
$$

Computed by `qreal/fullmet.py`, independently by `qhubcheck/fm_check.py` and here by `qcert3/fm_tab3.py` (own matrix
parse, own elimination; also the per-full-value statistics: each full value has 12-23 of its 64 labels with rank
$\ge4$); identical histograms and tables.

**Lemma FM (rows FM7, FM9).** [proved] Every phase satisfies

$$
W+y_1\ \le\ 7(q-A)+\operatorname{top}(A)\quad\text{(FM7)},\qquad\qquad Z\ \le\ 3(q-A)+\operatorname{top}_3(A)\quad\text{(FM9)}.
$$

*Proof.* Fix a missing label $\ell$. (i) $W_\ell+Y_\ell\le\operatorname{rank}(C_\ell)\le7$: this is (L7\*) per label (A.4;
the $W_\ell$ forms $E_\ell+T+B_b$ and the $Y_\ell$ kind-1 forms lie in $C_\ell$ and come from an independent family of
gate equations). (ii) $Z_\ell\le\min(3,\operatorname{rank}(C_\ell)-1)$ when $\ell$ is bright: $Z_\ell\le3$ is the proof
of (L9) (F7, Lemma 4.5); and $Z_\ell=\sum_{i\ \text{meets}\ \ell}(r_i-1)_+\le W_\ell-1$ because some anchored helper
meets $\ell$, while $W_\ell\le\operatorname{rank}(C_\ell)$ by the proof of (L7). At a dark label $Z_\ell=0$. (iii) If $\ell$
is full-met through the edge $f$-$c$ of the full helper $f$, then $\ell=f+c$ with $f$ a full value (Lemma 4.4, F3), so
$\ell\in\Lambda$, and $\ell$ is bright. The $A$ full-met labels are distinct elements of $\Lambda$ (each is met by
exactly one full helper, Lemma 4.5, and distinct labels are distinct values), so by (i)
$\sum_{\ell\ \text{full-met}}(W_\ell+Y_\ell)\le\operatorname{top}(A)$ and by (ii)
$\sum_{\ell\ \text{full-met}}Z_\ell\le\operatorname{top}_3(A)$ (the sum of $A$ values of a function over distinct
arguments is at most the sum of its $A$ largest values). At the remaining $q-A$ missing labels use
$W_\ell+Y_\ell\le7$ and $Z_\ell\le3$. Summing, with $W=\sum_\ell W_\ell$, $y_1=\sum_\ell Y_\ell$ (a kind-1 gate has
exactly one missing signal, A.1) and $Z=\sum_\ell Z_\ell$, gives FM7 and FM9. $\square$

Uses: (L7\*) (A.4), the proofs of (L7) and (L9) [read, not checked], Lemmas 4.1, 4.4, 4.5; F3, F6, F7, FM.

**Linearisation by chords.** [proved] $\operatorname{top}$ and $\operatorname{top}_3$ are concave on the integers, so for every
integer $a_0\ge0$ and every integer $A\ge0$, $\operatorname{top}(A)\le\operatorname{top}(a_0)+s_{a_0}(A-a_0)$ with
$s_{a_0}=\operatorname{top}(a_0+1)-\operatorname{top}(a_0)$ (the chord through $a_0,a_0+1$ lies above a concave function
outside $[a_0,a_0+1]$ and coincides with it on the two points), and likewise for $\operatorname{top}_3$ with slopes
$s^{(3)}_{a_0}$. Hence the rows of the local system, for $a_0=0,\dots,q-1$:

$$
\text{FM7}(a_0):\ W+y_1+(7-s_{a_0})A\le7q+\operatorname{top}(a_0)-s_{a_0}a_0,\qquad
\text{FM9}(a_0):\ Z+(3-s^{(3)}_{a_0})A\le3q+\operatorname{top}_3(a_0)-s^{(3)}_{a_0}a_0 .
$$

Explicitly, with FM's tables: for $M$, FM7$(a_0)$ is (L7\*) for $a_0\le3$ and $W+y_1+A\le7q+4$ for $4\le a_0\le q-1$;
for $M^{\mathsf T}$ it is $W+y_1+A\le7q$ for every $a_0$; FM9$(a_0)$ is $Z\le3q$, i.e. (L9), in both orientations. The
LP of qhub and qhubcheck and the case systems below carry all $2q$ chord rows (duplicates are harmless); the certificates
record which of them they use (REPORT.md: 47 certificates use an FM7 row, none needs an FM9 row).

---

## C.7 The case systems, their certificates and the coverage

For a phase with parameters $(h,y,F,q,z)$, an orientation and a case $(\mathrm{hub},\mathrm{dark})$, the **case system**
has the unknowns $n_{r,u,v}\ge0$ over the types with $r+u+v\ge3$ (section 11), minus in a hub case $A=a$ the types with
$r\le2$ and $u>(3-r)+(q-a)$, the unknowns $y_0,y_1,y_2\ge0$ (A.6) and in a dark case $y_{2d},F_b,F_d\ge0$ (B.4), and the
rows, in this order:

1. the package rows (L1)-(L23) of Lemma 10.1, unchanged, in the order of `certify75.py`;
2. the batch-1 rows of A.6: $y_0+y_1+y_2=y$ (two inequalities), (N1) with $G=75$, (L7\*), (L12\*), (L13\*), (L14\*),
   (L15\*), (L17-M\*) | (L17-MT\*), (L18\*), (L19\*), (L20\*), [$q=0$: (L22\*)], (I), [$q=0$: (Q0)];
3. the flat batch-3 rows: [$q=4$: PK4] [$q=5$: PK5], then FM7$(a_0)$, FM9$(a_0)$ for $a_0=0,\dots,q-1$;
4. hub $=A=a$: $\sum_{r=3}un=a$ (two inequalities); hub $=A\le1$: $\sum_{r=3}un\le1$; hub = none: nothing;
5. dark $=d$: the rows of B.6 item 4 ((L13d), (L14d), (L15d), (L17Md) | (L17Td), (L18d), (O1)-(O6), [$d=q$: $F_b\le0$],
   [$d=0$: $F_d+y_{2d}\le0$]); dark = none: nothing.

The **cases** of a key are hub $\in\{\text{none}\}$ if $q\le1$ and hub $\in\{A=2,\dots,A=q,\ A\le1\}$ if $q\ge2$, and
dark $\in\{0,\dots,q\}$; the *leaves* are the pairs ($q(q+1)$ of them for $q\ge2$, $q+1$ for $q\le1$). A
**certificate** for a case is a vector $\lambda$ of nonnegative integers over the rows of its case system with
$\lambda^{\mathsf T}A\ge0$ in every column of the case system and $\lambda^{\mathsf T}b<0$ (section 11).

**Lemma C1 (B.6) applies verbatim.** [proved] The flat rows 3 are present in every case system, so a certificate for
$(\text{none},\text{none})$ is a certificate for every leaf; one for $(\mathrm{hub},\text{none})$, extended by zeros on
the dark rows, is one for every $(\mathrm{hub},d)$ (the columns $y_{2d},F_b,F_d$ have nonzero entries only in the dark
rows); one for $(\text{none},d)$, extended by zeros on the hub rows and restricted to the columns of a hub case, is one for
every $(\mathrm{hub},d)$ (removing columns removes constraints). **Coverage** is as in B.6: a key is *covered* if for every
leaf $(hc,d)$ the file contains a certificate for $(hc,d)$, $(hc,\text{none})$, $(\text{none},d)$ or
$(\text{none},\text{none})$; by C.4, B.4 and Lemma C1 a covered key admits no phase. A certificate for
$(\text{none},\text{none})$ is *package* (multipliers vanish outside the package rows), *batch-1* (uses a row of item 2,
none of item 3), or *flat* (uses PK4, PK5 or an FM row); the others are *case* certificates and record their hub case
($A=a$ or $A\le1$) and dark case ($q_D=d$).

**What is certified.** [certified] `qcert3/CERTIFICATES_CASES75_B3.json` contains 4,950 certificates for 2,471 keys at
$G=75$: complete case coverage of all **536 keys** that were LP-feasible under the systems of Addendum B (the 381
baseline keys of qcert2 together with qrealcheck's complete list of 1,661 batch-2-feasible keys of its scan; union 1,713)
and are infeasible under the systems above (among them all **265** of the baseline $381\to116$ reduction), 14,312 leaves;
and for each of the **207 oriented claims** that the full systems exclude and Addendum B's do not (the $996\to789$
reduction), every $(q,z)$ below the stated $k,l$ is excluded by (4.4), by Lemma 10.3 or by a covered key (2,054 distinct
keys, 27,153 leaves), and $k>S_e$ or $l>S_o$ or $k+l>a+b+2G-192$. Two programs check every certificate and every
coverage: `gen_certs3.py` (the generator, package rows imported from `certify75.system`) and `check_cases3.py` (every
row and column written out by hand, standard library only, cases enumerated independently); `crosscheck3.py` shows the
two system definitions are identical matrices on all 24,790 (key, case) nodes of the killed keys and of the keys with
case certificates. Counts, commands and times: REPORT.md.

---

## C.8 What the new statements need: normalization only; positive controls

Condition (C1), Lemma H2, row HUB2 and its split, Lemma PK and Lemma FM hold for **every normalized circuit of either
orientation**; none uses Lemma 7.4, the potential or the tail. Lemma 7.4 enters the case systems exactly where it enters
the package system (the restriction $r+u+v\ge3$, section 11). `stress_ext3.py` evaluates every new row and strong form on
the raw circuits (orbit step 0) and on their canonical transposes (steps 1-3) of the 13 controls and 303 real circuits:
1,264 phases, 0 violations; on every phase $A=0$ and $m_i=0$ at every helper, so H2 and HUB2 are consistent with but
not exercised by any known circuit (REPORT.md, section 3); PK4 / PK5 are not exercised either (no phase has $q\le6$);
FM7 / FM9 reduce to (L7\*) / (L9) at $A=0$. The rows are exercised on the **synthetic local configurations** of H2: all
maximal configurations $(h,R,S)$, $|S|=3-r$, at the attaining hub values of both orientations (re-enumerated here) and
the nine explicit witnesses of the qhub report: their gate equations are independent and the two pivot steps of C.3
return exactly $\mathcal F(h,R,S)$; Lemma H2 holds with equality; HUB2 with $q=A=m$ holds with slack 0 and its
constant-$(2-r)$ mutation fails; the pairs $P_{f_j}$ are disjoint, the full helpers pairwise non-adjacent (F4), the
labels distinct and each of rank $\ge3+r$ (FM's per-label condition); the H1 cap-4 witness sets ($m=4$ at $r=0$) give a
dependent family and dependent gate equations and are flagged. These are local configurations, not circuits; whether
any extends to a normalized circuit is open.

| statement | package lemmas used | finite facts used |
|---|---|---|
| Condition (C1) | 1.1, 4.1, 4.4 (and its proof), 4.6 | F2, F3 |
| Lemma H2 | (C1), 4.1, 4.4, 4.5, 4.6 | F2, F3, F4 (through 4.4-4.6), H2 |
| Row HUB2; split exhaustive and sound | H2 (Lemma), 4.1, 4.5 / (4.2) | none |
| Lemma PK (PK4, PK5) | 4.6; the premise of the proof of 10.4 | none (pk_enum.py as a check) |
| Lemma FM (FM7, FM9) and the chord rows | (L7\*) (A.4), proofs of (L7), (L9); 4.1, 4.4, 4.5 | F3, F6, F7, FM |
| Lemma C1 (B.6), coverage | section 11 (certificates), 10.3, 4.7 / (4.4) | none |
| the DARK rows (items 5) | Addendum B (Lemmas D1, D2) [read, not checked here] | F7, F9, F10, F11, F12 (through D1) |

---

## C.9 Status of the statements of this addendum

| statement | label |
|---|---|
| Finite fact H2 ($\operatorname{cap}_r(h)\le3-r$; histograms; attaining values = H1's cap-4 values) | [finite-checked] (qhub `hub2.py`, `hub2_check.py`; qhubcheck `h2_check.py`; here `h2_tab3.py` for the full histograms and per-value capacities, `stress_ext3.py` for the helper masks met and all maximal configurations at the attaining values) |
| Condition (C1): the family $\mathcal F(h,R,S)$ is independent in any normalized circuit containing the configuration | [proved] |
| Lemma H2; row HUB2; the split is exhaustive and each case system a relaxation | [proved] |
| Lemma PK: PK4, PK5 (with $n_j=\#\{u=j\}$) | [proved]; [finite-checked] (qhubcheck `pk_enum.py`) |
| Finite fact FM (rank histograms of the labels $f+c$; top tables) | [finite-checked] (qreal `fullmet.py`; qhubcheck `fm_check.py`; here `fm_tab3.py`) |
| Lemma FM: FM7, FM9 and their chord rows | [proved], relative to (L7\*) and the proofs of (L7), (L9) [read, not checked] |
| Lemma C1 (B.6) for the new case systems | [proved] |
| Lemmas D1, D2 and the DARK split; Lemma G\*, N1, (L7\*)-(L22\*), (I), (Q0); F2-F14; Lemmas 1.1-10.4 | [read, not checked] (Addenda A, B; package; `verify_all.py` replayed by lb76) |
| 536 killed keys covered (265 baseline); 207 claims covered (4,950 certificates, 2,925 per case) | [certified] (`check_cases3.py`, `gen_certs3.py`) |
| zero violations of every row and strong form on 316 circuits / 1,264 phases; $A=m_i=0$ everywhere | [finite-checked] (`stress_ext3.py`; a positive control, not a proof) |
| the synthetic maximal configurations (H2 tight, HUB2 slack 0, mutation fails; cap-4 sets flagged) | [finite-checked] (`stress_ext3.py`; local configurations, not circuits) |
| 789 claims and 116 baseline keys (859 LP-feasible / 551 load-bearing keys of the scan) remain by LP status | [measured]; **no bound beyond 75 is claimed** |
