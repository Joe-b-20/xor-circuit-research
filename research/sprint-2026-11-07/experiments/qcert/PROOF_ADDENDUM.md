# Addendum A. New universal rows for the local systems

qcert, 2026-11-07. This addendum is written in the notation of PROOF.md (the 75-gate note in
`lower-bound-proofs/mixcolumns-lb75/`); lemma, fact and row numbers refer to it. It extends the row set of
Lemma 10.1 by rows that every normalized circuit satisfies, and it records exactly which package lemmas and
finite facts each row uses. It does **not** change the Theorem of PROOF.md and claims **no** lower bound
beyond 75: at G = 75 the extended systems leave 1,313 of 7,416 oriented claims open (REPORT.md, section 3).

Every statement carries one of the labels **[proved]** (proof below, package lemmas and finite facts used as
black boxes), **[finite-checked]** (computed exactly by a program named here), **[certified]** (an exact
integer certificate checked by two programs), **[read, not checked]** (a package statement relied on as is).

---

## A.1 Definitions

Throughout, a normalized circuit of either orientation is fixed, with its odd graph (section 4), labels,
helper types $(r_i,u_i,v_i)$, the aggregates $W, A, Z, E, D_0$ of section 10, and the notions *anchored*
($r_i\ge1$), *full* ($r_i=3$), *bright* / *dark* missing labels, $h_0$, $U_0$, $q_D$, $K_\ell$, $J$, $k_\ell$
of Lemma 10.2. Recall that in both gate types that give an edge of the odd graph (odd+odd, odd+even) the mask of the
label is the XOR of the masks of the two ends, and that distinct signals have distinct masks (Lemma 1.1).

**Boundary pair of a represented label.** A represented label $\ell$ has exactly one B-B edge (Lemma 4.1); its two
ends form the *boundary pair* $P_\ell\subset B$, $|P_\ell|=2$, with XOR $\ell$. Distinct represented labels
have distinct pairs (distinct masks).

**Pivot triple.** For an anchored helper $i$ and a chosen represented edge $i$-$a$ with label $\ell$,
$T_i^0=\{a\}\cup P_\ell$ is a boundary triple with XOR $h_i$ (Lemma 4.4); $H_i+T_i^0$ is the *pivot* of $i$.

**Kinds of even+even gates.** An even+even gate has three even signals: its two operands and its result.
It is of
- **kind 0** if all three signals are represented labels;
- **kind 1** if exactly one of the three is missing and that missing label is bright;
- **kind 2** otherwise (exactly one missing and dark, or two or three missing).

Let $y_0,y_1,y_2$ be the numbers of gates of kinds 0, 1, 2, so $y_0+y_1+y_2=y$. For a missing label $\ell$ let
$Y_\ell$ be the number of kind-1 gates whose missing signal is $\ell$ (so $Y_\ell=0$ for dark $\ell$ and
$\sum_\ell Y_\ell=y_1$), and $W_\ell=\sum_{i\text{ meets }\ell}r_i$ as in the proof of (L13). Let $n_3$ (resp.
$n_2$) be the number of helpers with $r_i=3$ (resp. $r_i=2$).

**The pair rank.** For a boundary pair $P$ let $\sigma(P)$ be the rank (over GF(2), as subsets of $B$) of the
family of zero-sum subsets of $B$ of weight 6 that contain $P$. A pair is *rich* if $\sigma(P)\ge2$ and *poor*
otherwise.

---

## A.2 Lemma N1 (labels of full helpers) [proved]

**Lemma N1.** In every normalized circuit of either orientation, $3n_3\le x+y-q$.

*Proof.* A full helper $i$ has three represented edges $i$-$a_1$, $i$-$a_2$, $i$-$a_3$ to three distinct
boundary vertices (the odd graph is simple, Lemma 4.1), with labels of masks $h_i+a_1,h_i+a_2,h_i+a_3$;
these masks are distinct, so the three labels are distinct. Suppose two distinct full helpers $i\ne j$ have
represented edges $i$-$a$ and $j$-$a'$ with the same label: $h_i+a=h_j+a'$. If $a=a'$ then $h_i=h_j$, two
distinct signals with one mask, contradicting Lemma 1.1. If $a\ne a'$ then $h_i+h_j=a+a'$ is a boundary-pair
value, contradicting Lemma 4.5. Hence the $3n_3$ represented edges at full helpers carry $3n_3$ pairwise
distinct represented labels, and there are exactly $x+y-q$ represented labels (Lemma 4.2). $\square$

**Local form.** $x+y=G-32-h$ (Lemma 1.2), so every phase of a circuit with $G$ gates satisfies

$$
\sum_{r=3}3n\ \le\ G-32-h-q.\qquad\text{(N1)}
$$

(N1) is the only row of the extended system whose constant depends on $G$; in the certificate file $G=75$ is
recorded once and both checkers rebuild the constant from it. Uses: Lemmas 1.1, 1.2, 4.1, 4.2, 4.5 (hence F2, F3, F4).

---

## A.3 Lemma G* (global elimination with the short even+even equations retained) [proved]

**Lemma G\*.** Let $J$ be any fixed space of boundary relations containing $R_6$ and $k_\ell=\dim((K_\ell+J)/J)$
as in Lemma 10.2. Every normalized circuit of either orientation satisfies

$$
32-\dim J\ \le\ y_2+z+D_0-q_D+\sum_{\ell\ \mathrm{bright}}k_\ell.\qquad\text{(G*)}
$$

Lemma 10.2's inequality (G) is (G\*) with $y_2$ replaced by the larger $y$.

*Proof.* **The family.** Let $\mathcal F$ consist of the following gate equations, written as formal vectors over
the signal coordinates ($B_b$ for $b\in B$, $H_i$ for helpers, $E_\ell$ for even signals):

- (a) the $x+y-q$ B-B reference equations $E_\ell+B_b+B_c$, one per represented label $\ell$ with $P_\ell=\{b,c\}$;
- (b) the $R$ represented H-B equations $H_i+B_a+E_\ell$ ($\ell$ represented);
- (c) the $U-U_0$ missing H-B equations $H_i+B_b+E_\ell$ at anchored helpers $i$ ($\ell$ missing, hence bright);
- (d) the $y_0$ kind-0 equations $E_\ell+E_{\ell'}+E_{\ell''}$;
- (e) the $y_1$ kind-1 equations $E_\ell+E_{\ell'}+E_{\ell''}$, say with $\ell''$ the missing (bright) signal.

$\mathcal F$ is a subfamily of the $G$ gate equations, which are linearly independent (the latest signal in a
nonempty combination cannot cancel; proof of Lemma 4.4). Hence $\mathcal F$ is independent, of size

$$
N=(x+y-q)+R+(U-U_0)+y_0+y_1 .
$$

Independence is established **before** any row operation; the operations below are invertible (each adds to a
row a combination of other rows of the current family) and therefore preserve independence and the span.

**Operation 1 (references).** Add to every row of (b), (d), (e) the reference rows of its represented labels.
A (b) row becomes $H_i+T$ with $T=\{a\}\cup P_\ell$ a boundary triple of XOR $h_i$ (the represented relation of
Lemma 4.4). A (d) row becomes the boundary vector of the set $P_\ell\,\triangle\,P_{\ell'}\,\triangle\,P_{\ell''}$,
whose masks XOR to $\ell+\ell'+\ell''=0$: a zero-sum subset of $B$ of even weight $\le6$. Weight 0 would make the
row zero, contradicting independence; weight 2 would be two distinct boundary signals with equal masks
(Lemma 1.1); weight 4 would be two distinct boundary pairs with equal XOR (F2). So it has weight exactly 6 and
lies in $R_6$ (F5). An (e) row becomes $E_{\ell''}+\sum_{b\in D}B_b$ with $D=P_\ell\,\triangle\,P_{\ell'}$; the two
pairs are distinct, so $|D|\in\{2,4\}$ and the XOR of $D$ is $\ell+\ell'=\ell''$: the row is a 2- or 4-form of
$\ell''$, an element of $C_{\ell''}$ (F6).

**Operation 2 (helper pivots).** At each of the $h-h_0$ anchored helpers $i$ choose one represented row
$H_i+T_i^0$ (the pivot) and add it to the other $r_i-1$ represented rows of $i$ and to the $u_i$ rows of (c) at $i$.
A represented row becomes $T_i^0\,\triangle\,T$ for a triple $T\ne T_i^0$ of XOR $h_i$: a zero-sum boundary set of
even weight $\le6$, nonzero, not of weight 2 or 4 (Lemma 1.1, F2), hence of weight 6, in $R_6$. A (c) row
$H_i+B_b+E_\ell$ becomes $E_\ell+(T_i^0\,\triangle\,\{b\})$; since $h_i+b=\ell$, $T_i^0\,\triangle\,\{b\}$ is a 2- or
4-subset of $B$ with XOR $\ell$: a form of $\ell$ in $C_\ell$.

**Operation 3 (label pivots).** Each bright label $\ell$ has, by definition, a missing H-B edge at an anchored
helper, hence at least one form produced by Operation 2. Choose one such form $\varphi_\ell$ (the pivot of $\ell$)
and add it to every other form of $\ell$ in the family: the remaining Operation-2 forms of $\ell$ and the
Operation-1 forms of $\ell$ coming from (e). Each becomes a difference of two forms of $\ell$, an element of
$K_\ell$.

**Counting coordinates (rank-nullity).** Call $\mathcal F'$ the family after the three operations; it is
independent, $|\mathcal F'|=N$, and $\operatorname{span}\mathcal F'=\operatorname{span}\mathcal F=:V$,
$\dim V=N$. The non-boundary coordinates occurring in $\mathcal F'$ are exactly

- $E_\ell$ for the $x+y-q$ represented labels (only in the reference rows (a)),
- $H_i$ for the $h-h_0$ anchored helpers (only in the pivots $H_i+T_i^0$),
- $E_\ell$ for the $q-q_D$ bright labels (only in the pivots $\varphi_\ell$);

unanchored helpers and dark labels never occur: a (c) row sits at an anchored helper and its label is bright, and the
missing signal of a kind-1 gate is bright by definition. Let $m=(x+y-q)+(h-h_0)+(q-q_D)$ be the number of these
*pivot rows*. Every one of the other $N-m$ rows of $\mathcal F'$ is a boundary vector (it has no $H$ or $E$
coordinate), and by Operations 1-3 it lies in $R_6+\sum_{\ell\ \mathrm{bright}}K_\ell$. Let $V_B$ be the
subspace of $V$ of vectors with zero non-boundary part. The $N-m$ non-pivot rows are independent (a subfamily
of an independent family) and lie in $V_B$, so $\dim V_B\ge N-m$; conversely, each pivot row is the only row of
$\mathcal F'$ carrying its pivot coordinate, so an element of $V_B$ is a combination of non-pivot rows only;
hence $V_B$ is exactly their span, $\dim V_B=N-m$, and

$$
V_B\subseteq R_6+\sum_{\ell\ \mathrm{bright}}K_\ell\subseteq J+\sum_{\ell\ \mathrm{bright}}K_\ell ,
\qquad
\dim\Bigl(J+\sum_{\ell\ \mathrm{bright}}K_\ell\Bigr)\le\dim J+\sum_{\ell\ \mathrm{bright}}k_\ell .
$$

Therefore $N-m\le\dim J+\sum_{\mathrm{bright}}k_\ell$. By Lemma 4.2, $R+U=32+h-y+q-z$, so

$$
N-m=R+(U-U_0)+y_0+y_1-(h-h_0)-(q-q_D)=32-(y-y_0-y_1)-z-(U_0-h_0)+q_D=32-y_2-z-D_0+q_D ,
$$

which is (G\*). $\square$

*Uses:* Lemmas 1.1, 4.1, 4.2, 4.4 (independence of the gate equations and of the represented relations), 4.5
is not needed; finite facts F2, F5, F6 (definition of $C_\ell$ only). The choice of $J$ enters only through
$\dim J$ and $k_\ell$.

**Remarks.** (i) The kind-1 gates contribute to the count without requiring a new pivot coordinate because
their missing signal is bright; a gate with exactly one missing signal that is dark would need its own pivot
and gain nothing, which is why it is counted in $y_2$. (ii) The three Operation-1 reductions are where the finite
facts enter: weight 6 for kind-0 rows (F2 and independence), size 2 or 4 for kind-1 rows (distinct pairs).

---

## A.4 Consequences for the rows

### (L7\*) label rank capacity with kind-1 forms [proved]

$$
W_\ell+Y_\ell\le\operatorname{rank}(C_\ell)\le7\ \text{ at every missing label }\ell,\qquad\text{hence}\qquad
W+y_1\le7q.\qquad\text{(L7*)}
$$

*Proof.* Fix a missing label $\ell$. Take the subfamily of the gate equations consisting of all references (a), the
represented H-B equations of the helpers that meet $\ell$ through an H-B edge, the missing H-B equations of label
$\ell$, and the kind-1 equations whose missing signal is $\ell$; it is independent. Operation 1 turns the
represented rows into $H_i+T$ and the kind-1 rows into forms $E_\ell+D$ of $\ell$. Then, exactly as in the proof of
(L7), for each helper $i$ meeting $\ell$ through $i$-$b_i$ add $H_i+B_{b_i}+E_\ell$ to each of its $r_i$ rows $H_i+T$,
obtaining the forms $E_\ell+T+B_{b_i}$. The $W_\ell+Y_\ell$ forms so obtained belong to an independent family, hence are
independent, and lie in $C_\ell$, of rank $\le7$ (F6). A kind-1 gate has exactly one missing signal, so summing
over the $q$ missing labels counts each kind-1 gate once: $W+y_1\le7q$. $\square$ (The argument does not use that
$\ell$ is bright; brightness of the kind-1 label is needed only in Lemma G\*.) Uses: Lemma 4.4, F6.

### (L12\*) boundary rank six with kind-0 relations [proved]

$$
\sum_i(r_i-1)_++y_0\le\rho_6.\qquad\text{(L12*)}
$$

*Proof.* Take the subfamily (a), (b), (d); it is independent. Apply Operation 1 and Operation 2 (helper pivots).
The $\sum_i(r_i-1)_+$ non-pivot represented rows $T_i^0\,\triangle\,T$ and the $y_0$ kind-0 rows are, as shown in
the proof of Lemma G\*, zero-sum boundary sets of weight 6; they are members of an independent family, hence
independent elements of $R_6$, whose dimension is $\rho_6$ (F5). $\square$ Uses: Lemmas 1.1, 4.4, F2, F5.

### (I) incidences of missing labels including even+even gates [proved]

$$
y_1+y_2+U+2F_H\le4q+2F.\qquad\text{(I)}
$$

*Proof.* A kind-1 or kind-2 gate contains at least one missing signal. A missing even signal $\ell$ occurs in exactly
$d_\ell+1$ gate equations (its defining gate and its $d_\ell$ uses; an even signal has no terminal use), and
$d_\ell+1\le4+2f_\ell$ by (3.2), which holds for every signal. These occurrences are its $U_\ell$ H-B edges, its $V_\ell$
H-H edges and its $ee_\ell$ occurrences in even+even gates (a B-B edge would make it represented). Summing over the
missing labels, $U+\sum_\ell ee_\ell\le4q+2F_{\mathrm{miss}}$, and $\sum_\ell ee_\ell\ge y_1+y_2$. Finally
$F_{\mathrm{miss}}+F_H\le F$ because helpers and even signals are disjoint (as in the proof of (L10)). In the local
system $F_H\ge\sum f_{\min}n$. $\square$ Uses: Lemma 3.2 / (3.2), the definitions of section 4; the same ingredients as (L10).

### (Q0) the case $q=0$ [proved]

$$
q=0\ \Longrightarrow\ z\ \ge\ 32-\rho_6+h_0,\qquad\text{i.e. } \sum_{r=0}n\le z-(32-\rho_6).\qquad\text{(Q0)}
$$

*Proof.* With $q=0$ every label is represented: every even+even gate is of kind 0 ($y_2=0$), there are no
missing H-B edges ($U_0=0$), no bright or dark labels ($q_D=0$, empty sum). Lemma G\* with $J=R_6$ gives
$32-\rho_6\le z+D_0=z-h_0$. $\square$ Uses: Lemma G\*, F5.

For $M$ this reads $z\ge12+h_0$ and is new. For $M^{\mathsf T}$ it reads $z\ge4+h_0$: this is the inequality
$z\ge k+4$ with which the proof of Lemma 10.3(ii) ends (there obtained by the same elimination with a spanning
forest of the unanchored helpers), without the additional statement $k\ge4$ that Lemma 10.3(ii) proves for
canonical transposes. So for $M^{\mathsf T}$ (Q0) is neither new nor weaker than Lemma 10.3(ii): it is the
same inequality, valid for every normalized circuit, while Lemma 10.3(ii) adds $h_0\ge4$ under Lemma 7.4. (This corrects the
phrase "weaker than Lemma 10.3(ii)" of the qbound report.)

### $y\to y_2$ in the quotient rows, row by row [proved]

In (L13)-(L18) the quantity $y$ enters only through Lemma 10.2's inequality (G); in (L19), (L20), (L22) it enters
only because the even+even equations were not retained. Replacing (G) by (G\*), or retaining the kind-0 and
kind-1 equations in the eliminations, gives the following rows. Each proof is the package's with the indicated
change; the facts named are the ones the package's proof uses at the corresponding step.

**(L13\*)** $\;W+y_1-2D_0\le2y_2+2z+7q-2\rho$. By (L7\*), $W_\ell+Y_\ell\le\operatorname{rank}(C_\ell)$, and
$\operatorname{rank}(C_\ell)\le7-2k_\ell$ for every label (F9); at a dark label $W_\ell=Y_\ell=0$. Summing over the bright
labels, $W+y_1\le7(q-q_D)-2\sum_{\mathrm{bright}}k_\ell$; insert (G\*) with the $J$ of F9 ($\rho=32-\dim J$) and
drop the nonpositive term $-9q_D$. Facts: F6, F9; Lemma G\*.

**(L14\*)** $\;W+A+y_1-2D_0\le2y_2+2z+7q-2\rho+\varepsilon$. Add $A_\ell$ (1 if a full helper meets $\ell$). If
$A_\ell=1$ then $k_\ell=0$ (F10: a full value is repeated and no quotient-active label meets a repeated value), and
$\operatorname{rank}(C_\ell)\le6$ except for the four $M$ labels of F11, of which at most two can meet full helpers at once
(three would carry nine independent represented relations of rank 7, against Lemma 4.4). So
$W_\ell+Y_\ell+A_\ell+2k_\ell\le7+ex_\ell$ with $\sum ex_\ell\le\varepsilon$ ($\varepsilon_M=2$, $\varepsilon_{M^{\mathsf T}}=0$); sum and use (G\*). Facts: F6, F9, F10, F11; Lemma 4.4; Lemma G\*.

**(L15\*)** $\;Z-D_0\le y_2+z+3q-\rho$. At a bright label the differences $T+T'$ of the incident helpers with
$r_i\ge2$ are independent elements of $K_\ell\cap J$, so $Z_\ell\le\operatorname{rank}(C_\ell)-1-k_\ell$, and with
$Z_\ell\le3$ (L9) the table F9 gives $Z_\ell+k_\ell\le3$; $Z_\ell=0$ at dark labels. Sum and use (G\*) (the term
$-4q_D$ is dropped). The kind-1 forms play no role here (they are not differences of represented relations), so $y_1$
does not enter. Facts: F7 (through (L9)), F9; Lemma G\*.

**(L16)** contains no $y$ and is unchanged.

**(L17-M\*)** $\;2Z+2E-3D_0\le3y_2+3z+6q-24$ and **(L17-MT\*)** $\;Z+E-3D_0\le3y_2+3z+3q-12$. The package's
charging argument gives $Z+E+3n_{\mathrm{act}}\le3(q-q_D)$ with $n_{\mathrm{act}}\ge\lceil d/2\rceil$ ($M$, since
$k_\ell\le2$) resp. $n_{\mathrm{act}}\ge d$ ($M^{\mathsf T}$, $k_\ell\le1$), where $d=\sum_{\mathrm{bright}}k_\ell$; now
$d\ge\rho-y_2-z-D_0+q_D$ by (G\*) instead of (G). Facts: F9, F10, F12; Lemma 4.5; Lemma G\*.

**(L18\*)** ($M^{\mathsf T}$) $\;W+A-3D_0\le3y_2+3z+7q-12$. An active label of $M^{\mathsf T}$ has
$\operatorname{rank}(C_\ell)\le4$ and $A_\ell=0$, so $W_\ell+A_\ell+3k_\ell\le7$ at every bright label; sum and insert (G\*)
for $d$. Facts: F9, F10; Lemma G\*. (By (L7\*) the same bound holds for $W_\ell+Y_\ell+A_\ell+3k_\ell$, so (L18) is
also valid with $W\to W+y_1$; this free strengthening is **not** used in the certificates.)

**(L19\*)** ($M^{\mathsf T}$) $\;3\le y_2+\sum_{r=0}(u+v-1)n+\sum_{r=1}vn$ and **(L20\*)**
$\;9\le3y_2+2z+\sum_{r=0}(3u+v-3)n$. Run the elimination of the proof of (L19), (L20) with the kind-0 and
kind-1 equations added to the retained family (still a subfamily of the gate equations, hence independent).
No new pivot is needed: after the references are added, a kind-0 row is a boundary vector (weight 6, in
$R_6\subseteq R_{10}$), and a kind-1 row is a form $E_\ell+D$ of a bright label $\ell$, which already occurs among the
retained missing rows (its missing H-B edge at an anchored helper) and is therefore one of the $q_A$ pivoted
labels. The residual count rises by $y_0+y_1$:

$$
32-y+y_0+y_1+h_0-U_0-z_0+(q-q_A)=32-y_2+h_0-U_0-z_0+(q-q_A).
$$

Membership modulo $R_{10}$: a kind-0 row lies in $R_6\subseteq R_{10}$. A label $\ell$ carrying a kind-1 row has a
2- or 4-form, so by F13 ("no active label is the XOR of a 2- or 4-subset of $B$") $\ell$ is not an active
six-form label, and every difference of two of its retained rows (forms of size $\le4$, H-H forms $T_i+T_j$ of
size $\le6$) has weight $\le10$, hence lies in $R_{10}$. So only active labels all of whose retained rows are H-H
forms contribute modulo $R_{10}$, exactly as in the package, and their contribution is bounded by $z_1$ (for
(L19)) resp. $2(z-z_0)/3$ (for (L20)) as there. With $\rho_{10}(M^{\mathsf T})=29$ (F13/F14):
$32-y_2+h_0-U_0-z_0+(q-q_A)\le29+z_1$, which with $q\ge q_A$ and $z_0\le\sum_{r=0}vn$ is (L19\*); and
$32-y_2+h_0-U_0-z_0\le29+2(z-z_0)/3$, which times 3 is (L20\*). Facts: F13, F14 ($\rho_{10}=29$).

**(L22\*)** ($M^{\mathsf T}$, $q=0$) $\;3\le y_2+\sum_{r=0}(v-1)n$. With $q=0$ every label is represented, so
$y_2=0$ and every even+even equation is of kind 0; retain them in the elimination of the proof of (L21)-(L22).
The $32-z_0+h_0$ residual rows (the count $32-y+h_0-z_0$ of the package plus the $y$ kind-0 rows) are
independent boundary relations of weight $\le8$ (weight 6 for the kind-0 rows), inside $R_8(M^{\mathsf T})$ of
dimension 29 (F14): $z_0-h_0\ge3$, i.e. $3\le\sum_{r=0}(v-1)n$. The certified row keeps the (nonnegative) term
$y_2$ on the right, which is valid and matches the LP of the qbound/qcheck reports; the exact statement at $q=0$ is
the stronger one with $y_2=0$. Facts: F14 ($\rho_8(M^{\mathsf T})=29$).

### (L7\*)-(L22\*) in the local system

All starred rows are linear in $n_{r,u,v}$ and in the three new unknowns $y_0,y_1,y_2\ge0$ with
$y_0+y_1+y_2=y$ (a relaxation: the three kinds are counts, so any phase supplies integer values). Each starred row
implies its unstarred original (set $y_2\le y$, $y_0,y_1\ge0$), so the extended system in section A.6 may list
both without loss.

---

## A.5 Lemma S (rich labels) [proved], finite fact S1 [finite-checked], Corollary S2 [proved]

**Lemma S.** In every normalized circuit of either orientation, at every represented label $\ell$ with boundary pair
$P_\ell$,

$$
\sum_{i:\ \text{H-B edge at } i \text{ with label } \ell}(r_i-1)_+\ \le\ \sigma(P_\ell).
$$

*Proof.* A helper $i$ meeting $\ell$ through the represented edge $i$-$a_i$ carries the represented relation
$H_i+T_i^0$ with $T_i^0=\{a_i\}\cup P_\ell$ ($a_i\notin P_\ell$: otherwise $h_i$ would be the other element of $P_\ell$,
a boundary mask). Take $T_i^0$ as the pivot of $i$. For every other triple $T$ of $i$ (another represented relation
$H_i+T$, Lemma 4.4), $T\cap T_i^0=\emptyset$: a shared element would leave two distinct boundary pairs with equal
XOR, against F2. Hence $(H_i+T_i^0)+(H_i+T)=T_i^0\cup T$ is a zero-sum subset of $B$ of weight 6 containing
$P_\ell$. This gives $\sum_{i\text{ meets }\ell}(r_i-1)_+$ such sets. They are linearly independent: a vanishing
nontrivial combination of them, expanded, is a combination of represented relations in which every $H_i+T$ with
$T\ne T_i^0$ occurs at most once and at least one of them occurs, i.e. a nontrivial vanishing combination of
represented relations, against Lemma 4.4. Independent weight-6 zero-sum sets through $P_\ell$ number at most
$\sigma(P_\ell)$. $\square$ Uses: Lemmas 1.1, 4.4, F2.

**Finite fact S1 (pair ranks).** For a boundary pair $P$ with XOR $\ell$, every weight-6 zero-sum subset of $B$
containing $P$ is $P\cup D$ for a 4-subset $D$ of XOR $\ell$ disjoint from $P$ (a 4-form of $\ell$ meeting $P$ would
produce a weight-4 zero-sum set, against F2), so $\sigma(P)=\dim K_\ell=\operatorname{rank}(C_\ell)-1$ for the 2,016
pair values. The histogram of $\sigma$ over the 2,016 pairs is
$M$: $\{0{:}\,1{,}704,\ 2{:}\,66,\ 3{:}\,228,\ 4{:}\,6,\ 5{:}\,12\}$;
$M^{\mathsf T}$: $\{0{:}\,1{,}590,\ 2{:}\,78,\ 3{:}\,312,\ 4{:}\,12,\ 5{:}\,24\}$; in particular $\sigma=1$ never
occurs, and the rich pairs number 312 ($M$) and 426 ($M^{\mathsf T}$). Let $\mathrm{top}(m)$ be the sum of the $m$
largest values of $\sigma$. **[finite-checked]** by `qbound/pair_sigma.py`, independently by `qcheck/ff_check.py`, and
again (histogram and $\mathrm{top}$) by `qcert/stress_ext.py` (its `sigma_hist` output).

**Corollary S2.** A represented label met by a helper with $r_i\ge2$ is rich; and
$6n_3+2n_2\le\mathrm{top}(x+y-q)$.

*Proof.* Lemma S gives $\sigma(P_\ell)\ge r_i-1\ge1$ and S1 excludes $\sigma=1$. Summing Lemma S over all
represented labels, the left side is $\sum_i r_i(r_i-1)_+=6n_3+2n_2$ and the right side is a sum of $\sigma$ over at
most $x+y-q$ distinct pairs, at most $\mathrm{top}(x+y-q)$. $\square$

The aggregate row of S2 is evaluated in the stress test only; it is not part of the certified system because it
excludes nothing at $G=75$ (REPORT.md, section 3).

---

## A.6 The extended local system and its certificates

For a phase with parameters $(h,y,F,q,z)$ and an orientation, the **extended local system** has the unknowns
$n_{r,u,v}\ge0$ over the types with $r+u+v\ge3$ (as in section 11) and $y_0,y_1,y_2\ge0$, and the rows, in this
order:

1. the package rows (L1)-(L23) of Lemma 10.1, unchanged (with the constant $y$), in the order of `certify75.py`;
2. $y_0+y_1+y_2=y$ (two inequalities);
3. (N1) with the constant $G-32-h-q$, $G=75$;
4. (L7\*), (L12\*), (L13\*), (L14\*), (L15\*);
5. for $M$: (L17-M\*); for $M^{\mathsf T}$: (L17-MT\*), (L18\*), (L19\*), (L20\*), and if $q=0$ (L22\*);
6. (I);
7. if $q=0$: (Q0).

A **certificate** is a vector $\lambda$ of nonnegative integers over these rows with $\lambda^{\mathsf T}A\ge0$ in every
column (every helper type and each of $y_0,y_1,y_2$) and $\lambda^{\mathsf T}b<0$; as in section 11 it proves that the
system has no nonnegative real solution, hence that no phase with these parameters exists. A certificate whose
multipliers vanish on rows 2-7 is a certificate for the package system alone. The file
`qcert/CERTIFICATES_EXT75.json` marks each certificate `new` (uses at least one of rows 2-7; the package rows alone
leave the key LP-feasible) or `package` (rows 2-7 unused). Two programs check every certificate and the coverage of
every listed claim exactly as `certify75.py` / `independent75.py` do at $G=74$: `qcert/gen_certs.py` (the
generator, package rows imported from `certify75.system`) and `qcert/check_ext75.py` (rows written out by hand,
standard library only). **[certified]**

**Remark ($q=0$).** At $q=0$ one also has $y_1=y_2=0$ exactly (every even+even gate is of kind 0). This row is not
included: (Q0) already excludes every $q=0$ key that the package rows leave feasible at $G=75$, and the counts of
REPORT.md are those of the system above, which is the one the qbound and qcheck reports measured.

---

## A.7 What the new rows need: normalization only

Every row of sections A.2-A.5 holds for **every normalized circuit of either orientation**: raw minimum circuits as
well as canonical transposes. None uses Lemma 7.4 (no odd helper of degree $<3$ in a canonical transpose), the
potential, or the tail. Lemma 7.4 enters the extended system only where it enters the package system: through
the restriction of the helper types to $r+u+v\ge3$ (section 11). The stress test of `qcert/stress_ext.py`
accordingly evaluates every new row on the raw circuits (orbit step 0) as well as on their canonical transposes.

| row | package lemmas used | finite facts used |
|---|---|---|
| (N1) | 1.1, 1.2, 4.1, 4.2, 4.5 | F2, F3, F4 (through 4.4, 4.5) |
| (G\*) | 1.1, 4.1, 4.2, 4.4 (independence of gate equations) | F2, F5, F6 (definition of $C_\ell$) |
| (L7\*) | 4.4 | F6 |
| (L12\*) | 1.1, 4.4 | F2, F5 |
| (I) | 3.2 / (3.2), 4.1, 4.2 | none |
| (Q0) | G\* | F5 |
| (L13\*), (L14\*) | G\*, 4.4 | F6, F9, F10, F11 |
| (L15\*) | G\*, (L9) | F7, F9 |
| (L17\*), (L18\*) | G\*, 4.5 | F9, F10, F12 |
| (L19\*), (L20\*) | the elimination of (L19)-(L20), 4.4 | F13, F14 ($\rho_{10}=29$) |
| (L22\*) | the elimination of (L21)-(L22) | F14 ($\rho_8=29$) |
| Lemma S, S2 | 1.1, 4.4 | F2, S1 |

---

## A.8 Wording corrected relative to the qbound report

1. *(Q0) for $M^{\mathsf T}$ "weaker than Lemma 10.3(ii)".* Replaced by: the same inequality as the last step of
   Lemma 10.3(ii), valid for every normalized circuit, without the part $h_0\ge4$ (section A.4).
2. *"(G\*) with $J=R_6$ has slack 0..10 on known circuits".* The upper end of the range depends on the corpus
   (0..10 on the 1,264 phases of `qbound/circuit_check.py`, 0..6 on the 2,236 phases of `qcheck/circ_check.py`);
   `qcert/stress_ext.py` records the minimum only: 0, attained on 9 control phases and 12 real $M^{\mathsf T}$ phases
   (REPORT.md, section 3). The statement that matters, slack $\ge0$ with equality attained, holds in all three runs.
3. *"after adding references it is a subset of the gate equations"* (proof of (G\*)). The order is the reverse:
   the family is a subfamily of the gate equations, hence independent; the references are added afterwards as an
   invertible operation (section A.3).
4. *Weight 0 for kind-0 rows.* A kind-0 equation plus its three references cannot vanish, because the family is
   independent; this case is now stated (Operation 1).

---

## A.9 Status of the statements of this addendum

| statement | label |
|---|---|
| Lemma N1; local form (N1) | [proved] |
| Lemma G\* (every $J\supseteq R_6$) | [proved] |
| (L7\*), (L12\*), (I), (Q0) | [proved] |
| (L13\*)-(L15\*), (L17\*), (L18\*), (L19\*), (L20\*), (L22\*) | [proved], relative to the package's proofs of (L13)-(L22) [read, not checked] |
| Lemma S, Corollary S2 | [proved] |
| S1 (histogram, $\sigma=\operatorname{rank}(C_\ell)-1$, no $\sigma=1$) | [finite-checked] (three programs) |
| F2-F14, Lemmas 1.1-4.7, 10.1-10.3 and their proofs | [read, not checked] (package; replayed `verify_all.py` passes) |
| certificates and coverage for the 195 claims (REPORT.md) | [certified] |
| zero violations of every new row on 316 circuits / 1,264 phases | [finite-checked] (`stress_ext.py`; a positive control, not a proof) |
| any bound beyond 75 | **not claimed** |
