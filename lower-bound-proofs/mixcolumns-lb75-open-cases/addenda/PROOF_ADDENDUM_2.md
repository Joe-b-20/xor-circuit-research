<!-- Provenance: Addendum B (batch 2), written by the qcert2 agent on 2026-11-07; copied verbatim from research/sprint-2026-11-07/experiments/qcert2/PROOF_ADDENDUM_2.md (sha256 cee6517fe004fa324eb47b2a73bed3dc01cb397a8f2b5ae5741fc2752db9c008; sprint branch sprint-2026-11-07-linear-maps, commit a4d055a). Only this line was added; delete it to recover the source byte for byte. Paths such as REPORT.md and qcert/ in the text refer to that source folder. -->
# Addendum B. Hub helpers, the dark-label split, and per-case certificates

qcert2, 2026-11-07. This addendum is written in the notation of PROOF.md (the 75-gate note in
`lower-bound-proofs/mixcolumns-lb75/`) and of Addendum A (`qcert/PROOF_ADDENDUM.md`); lemma, fact and row numbers
refer to PROOF.md unless they carry the letters A or B. It adds to the local systems of Lemma 10.1 and Addendum A two
*case splits* (on the number A of missing labels that meet a full helper, and on the number $q_D$ of dark labels),
with rows valid in each case, and it records exactly which package lemmas and finite facts every statement uses. It
does **not** change the Theorem of PROOF.md and claims **no** lower bound beyond 75: at $G=75$ the extended systems
with both splits leave 996 of the 7,416 oriented claims open by LP status (REPORT.md, sections 1 and 4).

Every statement carries one of the labels **[proved]** (proof below, package lemmas and finite facts used as black
boxes), **[finite-checked]** (computed exactly by a program named here), **[certified]** (an exact integer
certificate checked by two independently written programs), **[read, not checked]** (a package statement relied on
as is). The finite fact H1 is stated exactly in B.2 and is [finite-checked] by three programs of two agents.

---

## B.1 Definitions

Throughout, a normalized circuit of either orientation is fixed (Lemma 1.1), with its odd graph (section 4), labels,
helper types $(r_i,u_i,v_i)$, the aggregates $W,A,Z,E,D_0$ of section 10, the notions *anchored* ($r_i\ge1$), *full*
($r_i=3$), *bright* / *dark* missing labels, $h_0$, $U_0$, $q_D$, $K_\ell$, $J$, $k_\ell$ of Lemma 10.2, and the
kinds of even+even gates with their counts $y_0,y_1,y_2$ and the per-label counts $Y_\ell$, $W_\ell$ of A.1.

**Full values, $N(h)$, cap.** A *full value* is an odd value with three boundary-triple representations (F3, F4: 80 for
$M$, 112 for $M^{\mathsf T}$). By Lemma 4.4 and F3 the mask of a full helper is a full value. For an odd value $h\notin B$
let

$$
N(h)=\{f\ \text{full}:\ h+f\ \text{is a boundary-pair value}\},
$$

and call a set $S$ of full values *jointly independent* if the $3|S|$ formal vectors $H_f+T$ ($f\in S$, $T$ one of the
three triples of $f$, $H_f$ a coordinate private to $f$) are linearly independent; by Lemma 4.4 the full helpers of a
circuit form a jointly independent set. Put

$$
\operatorname{cap}(h)=\max\{|S|:\ S\subseteq N(h)\ \text{jointly independent}\}\qquad(\operatorname{cap}(h)=0\text{ if }N(h)=\emptyset).
$$

**Full-met labels and $A$.** A missing label is *full-met* if it has an H-B edge at a full helper. By Lemma 4.5 a missing
label meets at most one full helper, and by Lemma 4.1 (the edges of one label form a matching) a full helper carries
each label at most once; hence the number of full-met labels is exactly $A=\sum_{r=3}u_i$, and $A\le q$ ((4.2)).

**Dark refinements of the even+even counts.** Among the $y_2$ kind-2 gates (A.1: exactly one missing signal, which is
dark, or two or three missing signals) let $y_{2d}$ be the number with exactly one missing signal and
$y_{2m}=y_2-y_{2d}$ the number with at least two. Let $F_b=\sum_{\ell\ \mathrm{bright}}f_\ell$,
$F_d=\sum_{\ell\ \mathrm{dark}}f_\ell$ ($f_\ell$ as in (3.2)), $U_A=\sum_{r\ge1}u_i$ (missing H-B edges at anchored
helpers), $U=\sum u_i$, and for a missing label $\ell$: $U_\ell$ (its H-B edges), $V_\ell$ (its H-H edges), $ee_\ell$
(the even+even gates containing it), $UA_\ell$ (its H-B edges at anchored helpers), $Z_\ell=\sum_{i\text{ meets }\ell}(r_i-1)_+$,
$A_\ell\in\{0,1\}$ (1 if a full helper meets $\ell$).

---

## B.2 Finite fact H1 and Lemma H1 (hub helpers)

**Finite fact H1 (hub capacity).** [finite-checked] For each orientation and every odd value $h\notin B$,
$\operatorname{cap}(h)\le4$. Exactly: $N(h)\ne\emptyset$ for 128,068 ($M$) / 177,412 ($M^{\mathsf T}$) values $h$ (those of
the form $f+p$, $f$ full, $p$ a pair value, $h\notin B$); the histogram of $|N(h)|$ over them is
$M$: 1: 114,060, 2: 1,280, 3: 10,992, 4: 444, 5: 100, 6: 672, 8: 260, 9: 160, 11: 88, 12: 4, 15: 8;
$M^{\mathsf T}$: 1: 157,472, 2: 2,352, 3: 14,432, 4: 892, 5: 192, 6: 1,344, 8: 308, 9: 224, 11: 172, 12: 4, 15: 20;
the histogram of $\operatorname{cap}(h)$ is $M$: 1: 125,128, 2: 2,840, 3: 92, 4: 8 and $M^{\mathsf T}$: 1: 172,060,
2: 5,156, 3: 176, 4: 20; over the triple values (possible masks of anchored helpers) it is $M$: 1: 10,984, 2: 1,496,
3: 92, 4: 8 and $M^{\mathsf T}$: 1: 14,236, 2: 2,708, 3: 176, 4: 20. The value 4 is attained only at values with exactly two
boundary-triple representations (the eight $M$ values are 0x404040, 0x808080, 0x40004040, 0x40400040, 0x40404000,
0x80008080, 0x80800080, 0x80808000); every value with 0, 1 or 3 representations has $\operatorname{cap}\le2$.
Computed by `qreal/hub.py` (exhaustive descent over the subsets of $N(h)$, independence through the six-set
differences), independently by `qrealcheck/h1_check.py` (branch-and-bound DFS with the $3|S|$ relation vectors;
all per-value caps identical), and again here: `qcert2/synthetic_hub.py` recomputes every value with $\operatorname{cap}=4$
and verifies for each that every 5-subset of $N(h)$ is dependent; `qcert2/stress_ext2.py` recomputes
$\operatorname{cap}(h_i)$ by exhaustive search for every non-full helper mask met on 1,264 phases and compares it with
the table `hub_cap_{M,Mt}.json`.

**Lemma H1.** [proved] In every normalized circuit of either orientation, for every helper $i$ with $r_i\le2$, the number
$m_i$ of full-met missing labels at $i$ satisfies

$$
m_i\le\operatorname{cap}(h_i)\le4,\qquad\text{and consequently}\qquad u_i\le4+(q-A).
$$

*Proof.* Let $\ell$ be a full-met missing label at $i$: an H-B edge $i$-$b$ with $\ell=h_i+b$ and an H-B edge $f$-$c$ at a
full helper $f$ with $\ell=f+c$ (we write $f$ for the helper and its mask). (a) $h_i+f=b+c$; $b\ne c$, since $b=c$ would
give $h_i=f$, two distinct signals with one mask (Lemma 1.1); so $h_i+f$ is a boundary-pair value and $f\in N(h_i)$ ($f$ is a
full value by Lemma 4.4 and F3; $h_i$ is odd and not in $B$). (b) Two distinct full-met labels at $i$ meet distinct full
helpers: if both met $f$, the helpers $i$ and $f$ ($i\ne f$ since $r_i\le2$) would carry two common missing labels on
their H-B edges, against Lemma 4.6. (c) The full helpers so met are therefore $m_i$ distinct elements of $N(h_i)$, and
they are jointly independent because all represented relations of the circuit are independent (Lemma 4.4); hence
$m_i\le\operatorname{cap}(h_i)\le4$ (H1). (d) Every missing label at $i$ that is not full-met is one of the $q-A$ missing
labels meeting no full helper (B.1), and distinct edges at $i$ carry distinct labels (Lemma 4.1); so
$u_i\le m_i+(q-A)\le4+(q-A)$. $\square$

Uses: Lemmas 1.1, 4.1, 4.4, 4.5, 4.6 (hence F2, F3, F4) and H1. Nothing beyond normalization is used, so Lemma H1
holds on raw circuits as well as on canonical transposes.

**Row (HUB) and its exact case split.** [proved] In the local system of a phase the statement of Lemma H1 is not
linear in the type counts (it bounds $u$ per helper by a quantity containing $A$). It is used as a disjunction.
First, $u_i\le q$ for every helper (one edge per label at $i$, Lemma 4.1), so for $q\le4$ the bound
$u_i\le4+(q-A)$ follows from $A\le q$ and nothing is gained: no split is made. For $q\ge5$:

- **Case $A=a$ for an integer $a$ with $5\le a\le q$.** The equality $\sum_{r=3}un=a$ holds, and by Lemma H1 every
  helper with $r\le2$ has $u\le4+(q-a)$, i.e. $n_{r,u,v}=0$ for every type with $r\le2$ and $u>4+(q-a)$; these columns
  are removed from the system.
- **Case $A\le4$.** The row $\sum_{r=3}un\le4$ holds; the bound $u_i\le4+(q-A)\ge q$ is vacuous, no column is removed.

*Exhaustiveness.* $A$ is a count of labels, hence a nonnegative integer, and $A\le q$ by (4.2); so $A$ lies in
$\{0,\dots,4\}\cup\{5\}\cup\dots\cup\{q\}$, and every phase falls into exactly one of the $q-3$ cases. *Soundness of
each case.* In its case a phase satisfies every row of the case system and has no helper of a removed type, so its
type counts are a nonnegative solution of the case system: the case system is a relaxation of the phase's
constraints. Hence **if every case system of a key is infeasible, no phase with that key exists.** $\square$

The case $A\le4$ admits fractional LP solutions with $A$ non-integral; refining it to the five integer cases
$A=0,\dots,4$ gives the same key sets at $G=75$ (qrealcheck, variant HUBX) and is not used.

---

## B.3 Lemma D1: the quotient rows with the dark count retained

**Lemma D1.** [proved] Every phase (normalized circuit, either orientation) with $q_D=d$ dark labels satisfies, with
$\rho=32-\dim J$ for the space $J$ of F9 ($\rho_M=8$, $\rho_{M^{\mathsf T}}=4$) and $\varepsilon_M=2$,
$\varepsilon_{M^{\mathsf T}}=0$:

$$
\begin{aligned}
W+y_1-2D_0&\le2y_2+2z+7q-2\rho-9d,&&\text{(L13d)}\\
W+A+y_1-2D_0&\le2y_2+2z+7q-2\rho+\varepsilon-9d,&&\text{(L14d)}\\
Z-D_0&\le y_2+z+3q-\rho-4d,&&\text{(L15d)}\\
2Z+2E-3D_0&\le3y_2+3z+6q-24-9d\quad(M),&&\text{(L17Md)}\\
Z+E-3D_0&\le3y_2+3z+3q-12-6d\quad(M^{\mathsf T}),&&\text{(L17Td)}\\
W+A-3D_0&\le3y_2+3z+7q-12-10d\quad(M^{\mathsf T}).&&\text{(L18d)}
\end{aligned}
$$

*Proof.* Let $d_k=\sum_{\ell\ \mathrm{bright}}k_\ell$. Lemma G\* (A.3) with the space $J$ of F9 reads
$\rho\le y_2+z+D_0-d+d_k$, i.e.

$$
d_k\ \ge\ \rho-y_2-z-D_0+d.\qquad(*)
$$

*(i) Dark labels contribute nothing.* At a dark label $\ell$ every helper with an H-B edge of label $\ell$ is unanchored
(definition of dark, Lemma 10.2), so $W_\ell=Z_\ell=0$ and $A_\ell=0$ (a full helper is anchored); and $Y_\ell=0$ because
the missing signal of a kind-1 gate is bright by definition (A.1). Hence $W$, $Z$, $A$ and $y_1=\sum_\ell Y_\ell$ are
sums over the $q-d$ bright labels, and so is $E$'s charging below.

*(ii) Per bright label.* These are the per-label inequalities of the package's proofs of (L13)-(L18) (section 10), with
$W_\ell$ replaced by $W_\ell+Y_\ell$ where (L7\*) allows it:

- $W_\ell+Y_\ell\le\operatorname{rank}(C_\ell)\le7-2k_\ell$ [(L7\*), A.4; F9];
- $W_\ell+Y_\ell+A_\ell+2k_\ell\le7+ex_\ell$ with $\sum_\ell ex_\ell\le\varepsilon$ [proof of (L14): if $A_\ell=1$ then
  $k_\ell=0$ by F10 and $\operatorname{rank}(C_\ell)\le6$ except for the four $M$ labels of F11, at most two of which meet
  full helpers at once by Lemma 4.4];
- $Z_\ell+k_\ell\le3$ [proof of (L15): F7 through (L9), F9];
- the charging argument of the proof of (L16)-(L18) [F10, F12, Lemma 4.5] gives $Z+E+3n_{\mathrm{act}}\le3(q-d)$, where
  $n_{\mathrm{act}}$ is the number of quotient-active bright labels, with $n_{\mathrm{act}}\ge\lceil d_k/2\rceil$ for $M$
  ($k_\ell\le2$) and $n_{\mathrm{act}}\ge d_k$ for $M^{\mathsf T}$ ($k_\ell\le1$) [F9];
- for $M^{\mathsf T}$: $W_\ell+A_\ell+3k_\ell\le7$ [proof of (L18): an active label has $\operatorname{rank}(C_\ell)\le4$ and
  $A_\ell=0$; F9, F10].

*(iii) Sum and substitute.* Summing (ii) over the $q-d$ bright labels and using (i):

$$
W+y_1\le7(q-d)-2d_k,\quad W+A+y_1\le7(q-d)+\varepsilon-2d_k,\quad Z\le3(q-d)-d_k,
$$
$$
M:\ 2Z+2E+3d_k\le6(q-d);\qquad M^{\mathsf T}:\ Z+E+3d_k\le3(q-d),\quad W+A+3d_k\le7(q-d).
$$

In each of these $d_k$ has a negative coefficient, so the lower bound $(*)$ may be substituted. For instance
$W+y_1\le7(q-d)-2(\rho-y_2-z-D_0+d)=2y_2+2z+2D_0+7q-2\rho-9d$, which is (L13d); the others follow in the same way,
with the coefficients $-2(\ldots)$, $-1(\ldots)$, $-3(\ldots)$, $-3(\ldots)$, $-3(\ldots)$ and $\rho=8$ resp. $4$ inserted
in the constants $6q-3\rho=6q-24$, $3q-3\rho=3q-12$, $7q-3\rho=7q-12$. $\square$

*Remarks.* PROOF.md's proofs of (L13)-(L18) carry the terms in $q_D$ and drop them in the last line ("dropping the
nonpositive multiple of $q_D$"); Lemma D1 is those proofs with the terms retained and (G) replaced by (G\*) (hence
$y\to y_2$, $+y_1$). Since $d\ge0$, each row of D1 implies the corresponding starred row of A.4 (and the package row);
in the case split $d$ is fixed to the case's value, where the rows are strictly stronger. Uses: Lemma G\* (A.3), Lemmas
4.4, 4.5, (L7\*), (L9); F7, F9, F10, F11, F12; the proofs of (L13)-(L18) [read, not checked].

---

## B.4 Lemma D2: occurrence budgets, and the dark-label split

**Lemma D2.** [proved] Every phase with $q_D=d$ dark labels satisfies

$$
\begin{aligned}
U_A&\ge q-d,&&\text{(O1)}\\
U_A+y_1&\le4(q-d)+2F_b,&&\text{(O2)}\\
y_{2d}&\le4d+2F_d,&&\text{(O3)}\\
F_b+F_d+\sum f_{\min}n&\le F,&&\text{(O4)}\\
y_{2d}\le y_2,\qquad y_2-y_{2d}&\le\binom q2,&&\text{(O5)}\\
y_1+2y_2-y_{2d}+U+2\sum f_{\min}n&\le4q+2F,&&\text{(O6)}\\
d=q\Rightarrow F_b=0;\qquad d=0&\Rightarrow F_d=0,\ y_{2d}=0.&&\text{(O7)}
\end{aligned}
$$

*Proof.* A missing even signal $\ell$ occurs in exactly $d_\ell+1$ gate equations: its defining gate and its $d_\ell$
uses, there being no terminal use (outputs are odd, section 1). By (3.2), $d_\ell+1\le4+2f_\ell$. An equation
containing the even signal $\ell$ contains either two odd signals (it is an edge of label $\ell$: H-B or H-H, since a
B-B edge would make $\ell$ represented) or none (an even+even gate); so $d_\ell+1=U_\ell+V_\ell+ee_\ell$ for every
missing label. (This equality is asserted per label on every phase by `stress_ext2.py`.)

(O1) Every bright label has an H-B edge at an anchored helper (definition); distinct labels have distinct edges; every
such edge is counted once in $U_A$. (O2) Each of the $U_A$ edges sits at a bright label (an anchored helper's missing
edge makes its label bright by definition), and each of the $y_1$ kind-1 gates contains its missing signal, which is
bright (A.1); both are occurrences of bright labels, so $U_A+y_1\le\sum_{\mathrm{bright}}(U_\ell+ee_\ell)\le\sum_{\mathrm{bright}}(4+2f_\ell)=4(q-d)+2F_b$.
(O3) Each of the $y_{2d}$ gates is an occurrence $ee_\ell$ of a dark $\ell$: $y_{2d}\le\sum_{\mathrm{dark}}(d_\ell+1)\le4d+2F_d$.
(O4) $F$ is the sum of $f_v$ over all signals of the phase (section 10, proof of (L4)); helpers, bright labels and dark
labels are pairwise disjoint sets of signals, and $F_H\ge\sum f_{\min}n$ (section 10). (O5) $y_{2d}\le y_2$ by
definition. A gate containing two missing signals $\ell,\ell'$ has the equation $\{\ell,\ell',\ell+\ell'\}$, which the pair
determines; two distinct gates with the same equation do not occur in a normalized circuit (the later result would
duplicate an existing signal; proof of Lemma 4.1). So each pair of missing labels lies in at most one gate, and mapping
each of the $y_{2m}$ gates to one pair of its missing signals is injective: $y_{2m}=y_2-y_{2d}\le\binom q2$.
(O6) $\sum_{\ell\ \mathrm{missing}}ee_\ell$ counts, over the even+even gates, the number of missing signals in the gate:
0 for a kind-0 gate, 1 for a kind-1 gate, 1 for a single-missing kind-2 gate, at least 2 for a multi-missing gate. Hence
$y_1+y_{2d}+2y_{2m}+U\le\sum_{\mathrm{missing}}(U_\ell+ee_\ell)\le4q+2F_{\mathrm{miss}}\le4q+2(F-F_H)$ (as in the proof
of (L10)); insert $y_{2m}=y_2-y_{2d}$ and $F_H\ge\sum f_{\min}n$. This is (I) of A.4 with every multi-missing gate
counted twice. (O7) With $d=q$ there is no bright label and $F_b$ is an empty sum; with $d=0$ there is no dark label,
so $F_d=0$ and $y_{2d}=0$. $\square$

Uses: Lemma 1.1 (through the proof of Lemma 4.1), (3.2), Lemma 4.1, the definitions of section 4, section 10 and A.1.
Nothing beyond normalization.

**The dark-label split.** [proved] $q_D$ is the number of dark labels, an integer with $0\le q_D\le q$ (dark labels are
missing labels). For $d=0,\dots,q$ the *dark case $d$* adds to the system the rows of Lemmas D1 and D2 with $q_D=d$ and
the three unknowns $y_{2d},F_b,F_d\ge0$. *Exhaustiveness:* the $q+1$ cases partition the possible values of $q_D$, so
every phase lies in exactly one. *Soundness:* in its case a phase satisfies every added row (D1, D2) with its actual
$y_{2d},F_b,F_d$, which are nonnegative integers. Hence a key whose dark-case systems are all infeasible admits no
phase. $\square$ Both splits together: a phase lies in exactly one pair (hub case, dark case), and the pair's system
(both sets of rows, the hub case's column deletion) is a relaxation of its constraints; a key is excluded iff every
pair is infeasible. For $q\ge5$ there are $(q-3)(q+1)$ pairs, for $q\le4$ there are $q+1$.

---

## B.5 Lemma O1 (chronology of full helpers) [proved]

**Lemma O1.** Let $f$ be a full helper with represented edges $f$-$a_j$ of labels $\ell_j$, whose B-B edges are
$b_j$-$c_j$ ($T_j=\{a_j,b_j,c_j\}$, $j=1,2,3$). Every edge $f$-$a_j$ whose gate is not the defining gate of $f$ *defines an
output in $T_j$*: either the gate's result is $a_j$ (then $a_j$ is an output), or it is $\ell_j$, and then the B-B gate of
$\ell_j$ has result $b_j$ or $c_j$, an output. At least two of the three edges are not the defining gate of $f$, so $f$
defines at least two outputs in two different triples; and the outputs so defined, over all full helpers of the circuit,
are pairwise distinct.

*Proof.* The gate of the edge $f$-$a_j$ has equation $\{f,a_j,\ell_j\}$; its result is one of the three. Each signal is
the result of exactly one gate (Lemma 1.1 (i), (iii): distinct masks, every gate used), so at most one of the three
edges of $f$ is its defining gate. If the result is $a_j$: a boundary signal that is a gate result is an output
(inputs are not gate results, section 1). If the result is $\ell_j$: the B-B gate $\{b_j,c_j,\ell_j\}$ of the represented
label $\ell_j$ (unique by Lemma 4.1) cannot have result $\ell_j$ (one producer per signal), so its result is $b_j$ or
$c_j$, an output. Both lie in $T_j$. Distinctness: an output is the result of exactly one gate, so distinct gates define
distinct outputs; the gates $\{f,a_j,\ell_j\}$ differ for distinct $(f,j)$ (the helper and the boundary end identify them);
the B-B gates $\{b_j,c_j,\ell_j\}$ differ for distinct labels, and the labels of the represented edges of all full
helpers are pairwise distinct (Lemma N1, A.2); a gate with a helper operand differs from a gate with two boundary
operands. $\square$

Uses: Lemma 1.1, section 1 (outputs are gates, inputs are not), Lemma 4.1, Lemma N1 (A.2). Lemma O1 enters no row of
the local systems; it is a structural statement checked on every full helper of every phase by `stress_ext2.py`
(every full helper met defines exactly two outputs, all distinct). Its finite consequences (qreal section 2: no bound on
$n_3$ follows) are not used here.

---

## B.6 The case systems and their certificates

For a phase with parameters $(h,y,F,q,z)$, an orientation and a case $(\mathrm{hub},\mathrm{dark})$, the **case system**
has the unknowns $n_{r,u,v}\ge0$ over the types with $r+u+v\ge3$ (section 11), minus in a hub case $A=a$ the types with
$r\le2$ and $u>4+(q-a)$, the unknowns $y_0,y_1,y_2\ge0$ (A.6) and in a dark case $y_{2d},F_b,F_d\ge0$, and the rows, in
this order:

1. the package rows (L1)-(L23) of Lemma 10.1, unchanged, in the order of `certify75.py`;
2. the batch-1 rows of A.6: $y_0+y_1+y_2=y$ (two inequalities), (N1) with $G=75$, (L7\*), (L12\*), (L13\*), (L14\*),
   (L15\*), (L17-M\*) | (L17-MT\*), (L18\*), (L19\*), (L20\*), [$q=0$: (L22\*)], (I), [$q=0$: (Q0)];
3. hub $=A=a$: $\sum_{r=3}un=a$ (two inequalities); hub $=A\le4$: $\sum_{r=3}un\le4$; hub = none: nothing;
4. dark $=d$: (L13d), (L14d), (L15d), (L17Md) | (L17Td), (L18d), (O1), (O2), (O3), (O4), $y_{2d}\le y_2$,
   $y_2-y_{2d}\le\binom q2$, (O6), [$d=q$: $F_b\le0$], [$d=0$: $F_d+y_{2d}\le0$]; dark = none: nothing.

The **cases** of a key are hub $\in\{\text{none}\}$ if $q\le4$ and hub $\in\{A=5,\dots,A=q,\ A\le4\}$ if $q\ge5$, and
dark $\in\{0,\dots,q\}$; the *leaves* are the pairs. A **certificate** for a case is a vector $\lambda$ of nonnegative
integers over the rows of its case system with $\lambda^{\mathsf T}A\ge0$ in every column of the case system and
$\lambda^{\mathsf T}b<0$; as in section 11 it proves that the case system has no nonnegative real solution.

**Lemma C1 (certificates persist under relaxation of the case).** [proved] A certificate for the case system of
$(\mathrm{hub},\text{none})$ is, extended by zeros on the dark rows, a certificate for every $(\mathrm{hub},d)$; one for
$(\text{none},d)$, extended by zeros on the hub rows, is a certificate for every $(\mathrm{hub},d)$; one for
$(\text{none},\text{none})$ is a certificate for every leaf. *Proof.* Adding rows with multiplier 0 changes neither
$\lambda^{\mathsf T}A$ nor $\lambda^{\mathsf T}b$; the new columns $y_{2d},F_b,F_d$ have nonzero entries only in the added
rows, so their weighted sums are 0; removing columns removes constraints. $\square$

**Coverage.** A key is *covered* if for every leaf $(hc,d)$ of its case tree the file contains a certificate for
$(hc,d)$, for $(hc,\text{none})$, for $(\text{none},d)$ or for $(\text{none},\text{none})$. By Lemma C1 and B.2, B.4, a covered
key admits no phase. A certificate for $(\text{none},\text{none})$ whose multipliers vanish outside the package rows is a
*package* certificate (valid at every $G$); one using a batch-1 row is a *batch-1* certificate; the others are *case*
certificates, and each records its hub case ($A=a$ or $A\le4$) and its dark case ($q_D=d$) explicitly.

**What is certified.** [certified] The file `qcert2/CERTIFICATES_CASES75.json` contains 4,523 certificates for 2,460
keys at $G=75$: all 300 keys that the batch-1 system leaves LP-feasible and the two splits exclude (the
$681\to381$ reduction) are covered, with 4,344 leaves; and for each of the 317 oriented claims that the two splits
exclude and the batch-1 system does not (the $1{,}313\to996$ reduction), every $(q,z)$ below the stated $k,l$ is
excluded by (4.4), by Lemma 10.3 or by a covered key (2,232 distinct keys, 11,788 leaves), and
$k>S_e$ or $l>S_o$ or $k+l>a+b+2G-192$. Two programs check every certificate and every coverage:
`gen_certs2.py` (the generator, package rows imported from `certify75.system`) and `check_cases75.py` (every row and
column written out by hand, standard library only, cases enumerated independently); `crosscheck2.py` shows the two
system definitions are identical matrices on all 23,593 (key, case) nodes the file and the coverage touch. Counts,
commands and times: REPORT.md.

---

## B.7 What the new statements need: normalization only

Lemma H1, Lemmas D1, D2, Lemma O1 and the two case splits hold for **every normalized circuit of either orientation**
(raw minimum circuits as well as canonical transposes); none uses Lemma 7.4, the potential or the tail. Lemma 7.4 enters
the case systems exactly where it enters the package system: through the restriction of the helper types to
$r+u+v\ge3$ (section 11). `stress_ext2.py` accordingly evaluates every new row and strong form on the raw circuits
(orbit step 0) as well as on their canonical transposes. The HUB row is consistent with but not exercised by any known
circuit ($A=0$ on all 1,264 phases); `synthetic_hub.py` builds local helper configurations (not circuits) with $A=m\ge1$
full-met labels at one hub, on which the HUB row is exercised at level $m$ (REPORT.md, section 3). Observation
[finite-checked], not used in any certificate: for every hub value with $\operatorname{cap}(h)=4$ and every 4-witness, the
gate equations of the configuration (the $3m$ relations plus the $2m$ missing-edge equations) are dependent, so $m=4$ is not
realizable; the largest realizable $m$ is 3 in both orientations (192 configurations at 8 hub values for $M$, 480 at 20
for $M^{\mathsf T}$), where Lemma H1 and the HUB row have slack 1. The certificates of this directory use the proved
constant 4 of H1; the sharper realizable capacity is the subject of the qhub agent's work.

| statement | package lemmas used | finite facts used |
|---|---|---|
| Lemma H1 | 1.1, 4.1, 4.4, 4.5, 4.6 | F2, F3, F4 (through 4.4-4.6), H1 |
| HUB split (exhaustive, sound) | 4.1, 4.5 / (4.2) | none |
| Lemma D1 | G\* (A.3), 4.4, 4.5, (L7\*), (L9); proofs of (L13)-(L18) | F7, F9, F10, F11, F12 |
| Lemma D2 | 1.1, 3.2 / (3.2), 4.1; definitions of sections 4, 10, A.1 | none |
| DARK split (exhaustive, sound) | definition of dark (10.2) | none |
| Lemma C1, coverage | section 11 (certificates), 10.3, 4.7 / (4.4) | none |
| Lemma O1 | 1.1, section 1, 4.1, N1 (A.2) | F2, F3, F4 (through N1) |

---

## B.8 Status of the statements of this addendum

| statement | label |
|---|---|
| Finite fact H1 ($\operatorname{cap}(h)\le4$; histograms; cap 4 only at two-representation values) | [finite-checked] (qreal `hub.py`; qrealcheck `h1_check.py`; here `synthetic_hub.py` for the cap-4 values, `stress_ext2.py` for the helper masks met) |
| Lemma H1; the HUB case split is exhaustive and each case system a relaxation | [proved] |
| Lemma D1 (L13d)-(L18d) | [proved], relative to the package's proofs of (L13)-(L18) [read, not checked] and Lemma G\* (A.3) |
| Lemma D2 (O1)-(O7); the DARK split is exhaustive and each case system a relaxation | [proved] |
| Lemma O1 | [proved] |
| Lemma C1 | [proved] |
| F2-F14, Lemmas 1.1-4.7, 10.1-10.3 and their proofs | [read, not checked] (package; `verify_all.py` replayed by lb76) |
| 300 killed keys covered; 317 claims covered (4,523 certificates) | [certified] (`check_cases75.py`, `gen_certs2.py`) |
| zero violations of every row and strong form on 316 circuits / 1,264 phases; O1 on every full helper | [finite-checked] (`stress_ext2.py`; a positive control, not a proof) |
| the synthetic $A=3$ configurations (HUB exercised, slack 1); $m=4$ never realizable | [finite-checked] (`synthetic_hub.py`; local configurations, not circuits) |
| 996 claims and 381 keys remain by LP status | [measured]; **no bound beyond 75 is claimed** |
