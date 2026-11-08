# Addendum D. The joint gate-equation family, finite fact J1, the label-class rows of Lemma P, row LIM, and per-case certificates for the exact hub split

qcert4, 2026-11-08. Written in the notation of PROOF.md (the 75-gate note in `lower-bound-proofs/mixcolumns-lb75/`) and
of Addenda A (`qcert/PROOF_ADDENDUM.md`), B (`qcert2/PROOF_ADDENDUM_2.md`) and C (`qcert3/PROOF_ADDENDUM_3.md`); lemma,
fact and row numbers refer to PROOF.md unless they carry the letters A-D. It replaces the hub split of Addendum C
(cases $A=2,\dots,q$ and $A\le1$ for $q\ge2$, no split for $q\le1$) by the **exact integer split** $A=a$, $a=0,\dots,q$,
for every $q$, and adds in each case $A=a$ the rows P1-P5 of Lemma P and the row LIM. The mathematics was found by the
qjoint agent (`qjoint/REPORT.md`) and confirmed by the qjointcheck agent (`qjointcheck/REPORT.md`); this addendum
states it in package style, corrects one wording (the spanning-tree statement of D.2), and records the certificates.
It does **not** change the Theorem of PROOF.md and claims **no** lower bound beyond 75: at $G=75$ the new systems leave
**686** of the 7,416 oriented claims open by LP status (REPORT.md).

Labels: **[proved]** (proof below; package lemmas, Addenda A-C and finite facts as black boxes), **[finite-checked]**
(computed exactly by named programs), **[certified]** (exact integer certificate checked by two independently written
programs), **[read, not checked]** (relied on as is).

---

## D.1 Definitions

A normalized circuit of either orientation is fixed (Lemma 1.1), with its odd graph, labels, helper types
$(r_i,u_i,v_i)$, full helpers ($r_i=3$), full values, pair values and their pairs $P(\cdot)$ (F2), $N(h)$, the
family $\mathcal F(h,R,S)$ and $\operatorname{cap}_r(h)$ of C.1, finite fact H2 (C.2), and $\operatorname{top}(a)$ of
finite fact FM (C.6). For a helper $i$ let $L_i$ be the set of missing labels on its H-B edges; $|L_i|=u_i$ (Lemma
4.1) and $|L_i\cap L_j|\le1$ for distinct helpers (Lemma 4.6).

**The two label classes.** $\Lambda_A$ is the set of *full-met* missing labels (an H-B edge at a full helper), $|\Lambda_A|=A=\sum_{r=3}u\,n$
(C.1, by Lemmas 4.1, 4.5); $\Lambda_0$ is the set of the other $q-A$ missing labels, called *hub-only*. Every label of a
full helper is full-met: $L_f\subseteq\Lambda_A$. For a helper $i$ with $r_i\le2$ (a *hub*) put
$m_i=|L_i\cap\Lambda_A|$ (this is C.1's $m_i$) and $e_i=|L_i\cap\Lambda_0|=u_i-m_i$.

**Limit hubs.** A hub with $r_i+m_i=3$ (by Lemma H2, $r_i+m_i\le3$ always). A *limit configuration* is a triple
$(h,R,S)$ with $h$ an odd value not in $B$, $R$ a set of $r\le2$ distinct triples with XOR $h$, $S\subseteq N(h)$,
$r+|S|=3$ and $\mathcal F(h,R,S)$ linearly independent. By (C1) (C.3) a limit hub $i$ gives the limit configuration
$(h_i,R_i,S_i)$, $S_i$ the full helpers meeting it.

**Sharing.** Two hubs *share* a missing label $\ell$ if $\ell\in L_i\cap L_{i'}$. If $\ell$ is full-met, met by the full
helper $f$ at its edge $f$-$c$, and $\ell=h_i+b=h_{i'}+b'$, then $P(h_i+f)=\{b,c\}$ and $P(h_{i'}+f)=\{b',c\}$: **the
pairs of the two hubs at $f$ intersect.** If $\ell$ is hub-only, then $h_i+h_{i'}=b+b'$ with $b\ne b'$ (otherwise
$h_i=h_{i'}$, against Lemma 1.1 (i)): **$h_i+h_{i'}$ is a pair value**, with pair $\{b,b'\}$ (F2).

---

## D.2 Lemma J: the joint gate-equation family [proved]

**Setting.** Let $K$ be a set of hubs of the circuit, with masks $h_k$ and represented triples $R_k$ ($|R_k|=r_k$,
Lemma 4.4), $S_k$ the set of full helpers meeting $k$ at a full-met label (by (C1)(a), $|S_k|=m_k$, the $f\in S_k$
distinct, $f\in N(h_k)$), and $S=\bigcup_kS_k$. Let $X$ be the set of hub-only labels carried by at least two hubs of
$K$; for $\ell\in X$ let $K_\ell\subseteq K$ be its carriers in $K$, $t_\ell=|K_\ell|\ge2$, and let $T_\ell$ be the edge
set of **any spanning tree** of the complete graph on $K_\ell$. Over the formal coordinates $H_k$ ($k\in K$), $H_f$
($f\in S$), $B_b$ ($b\in B$) put

$$
\mathcal F_{\rm joint}=\{H_f+T:\ f\in S,\ T\ \text{a triple of}\ f\}\ \cup\ \{H_k+T:\ k\in K,\ T\in R_k\}\ \cup\
\{H_k+H_f+P(h_k+f):\ k\in K,\ f\in S_k\}\ \cup\ \bigcup_{\ell\in X}\{H_k+H_{k'}+P(h_k+h_{k'}):\ \{k,k'\}\in T_\ell\},
$$

the vectors $H_f+T$ listed once per full helper however many hubs meet it.

**Lemma J.** $\mathcal F_{\rm joint}$ is linearly independent over GF(2). In particular, for $K=\{k\}$ it is
$\mathcal F(h_k,R_k,S_k)$ (condition (C1)); for two hubs it is the union of their families with the common $H_f$
identified, plus the vector $H_k+H_{k'}+P(h_k+h_{k'})$ if they share a hub-only label.

*Proof.* *The gate-equation family.* Take the following gate equations, as formal vectors over all signal
coordinates ($E_\lambda$ for an even signal $\lambda$):

1. the B-B reference $E_\lambda+B_b+B_c$ of every represented label $\lambda$ carried by a represented edge of a hub
   of $K$ or of a full helper of $S$ (unique, Lemma 4.1; one row per label even if several such edges carry it);
2. the represented H-B equations $E_\lambda+H_x+B_a$ of the hubs of $K$ ($r_k$ each) and of the full helpers of $S$
   (three each);
3. for every full-met label $\ell$ carried by a hub of $K$, met by the full helper $f$: the missing H-B equation of
   $\ell$ at $f$ and at every hub of $K$ carrying $\ell$;
4. for every $\ell\in X$: the missing H-B equations of $\ell$ at the hubs of $K_\ell$.

Each is the equation of the gate of one edge of the odd graph, and the listed edges are pairwise distinct (a
reference is a B-B edge; the other rows are H-B edges at pairwise distinct (helper, boundary) pairs, since a helper
carries each label at most once, Lemma 4.1, and a represented and a missing label differ). Equations of distinct gates
are linearly independent as formal vectors: in a nonempty sum, the result signal of the latest gate occurs in its own
equation and in no other (Lemma 1.1, the argument of the proof of Lemma 4.4).

*Pivot 1 (references).* As in C.3: adding each reference row to the rows of item 2 carrying its label turns
$E_\lambda+H_x+B_a$ into $H_x+T$ ($T$ the triple of the represented relation, Lemma 4.4); then $E_\lambda$ occurs only in
the reference row, which is deleted. What remains of items 1-2 is $\{H_f+T\}\cup\{H_k+T:\ T\in R_k\}$.

*Pivot 2 (full-met labels).* For a full-met label $\ell$ met by $f$ (edge $f$-$c$) and carried by the hubs
$k_1,\dots,k_s$ of $K$ (edges $k_j$-$b_j$), add $f$'s row $E_\ell+H_f+B_c$ to each hub row $E_\ell+H_{k_j}+B_{b_j}$:
it becomes $H_{k_j}+H_f+B_{b_j}+B_c=H_{k_j}+H_f+P(h_{k_j}+f)$ (D.1). Then $E_\ell$ occurs only in $f$'s row; delete it.
Distinct full-met labels at one hub have distinct full helpers ((C1)(a)), so each pair $(k,f)$, $f\in S_k$, arises from
exactly one label, and this step produces exactly the vectors $H_k+H_f+P(h_k+f)$.

*Pivot 3 (shared hub-only labels).* For $\ell\in X$ with carriers $k_1,\dots,k_t$ (edges $k_j$-$b_j$), add $k_1$'s row
$E_\ell+H_{k_1}+B_{b_1}$ to each $E_\ell+H_{k_j}+B_{b_j}$, $j\ge2$: it becomes $H_{k_1}+H_{k_j}+P(h_{k_1}+h_{k_j})$
(D.1). Then $E_\ell$ occurs only in $k_1$'s row; delete it. This gives the star $T^\star_\ell$ centred at $k_1$.

Each step is invertible row addition or deletion of a row holding a coordinate private to it, so the surviving
family -- $\mathcal F_{\rm joint}$ with the stars $T^\star_\ell$ -- is independent. *Any spanning tree.* For $k,k'\in
K_\ell$, $P(h_k+h_{k'})=\{b_k,b_{k'}\}=P(h_{k_1}+h_k)\,\triangle\,P(h_{k_1}+h_{k'})$, so each tree vector
$H_k+H_{k'}+P(h_k+h_{k'})$ is the sum of the two star vectors of $k$ and $k'$ (one of them absent if $k$ or $k'$ is
$k_1$), and conversely each star vector is the sum of the tree vectors along the tree path from $k_1$. The $t-1$ vectors
of $T_\ell$ therefore span the same space as the $t-1$ vectors of $T^\star_\ell$, and replacing a part of an
independent family by an equally large set with the same span keeps it independent. $\square$

**The spanning-tree wording.** For $t_\ell\ge3$ hubs at one hub-only label the family carries $t_\ell-1$ mixed
vectors, **not one per pair**: the three pair vectors of a triangle $k,k',k''$ sum to
$P(h_k+h_{k'})+P(h_{k'}+h_{k''})+P(h_k+h_{k''})=\{b_k,b_{k'}\}\triangle\{b_{k'},b_{k''}\}\triangle\{b_k,b_{k''}\}=\emptyset$,
so "one vector per pair" (the wording of qjoint/REPORT.md section 2) is dependent for $t\ge3$ (qjointcheck's
correction). At a full-met label carried by $s$ hubs the family carries the $s$ vectors of the star at $f$ (a spanning
tree of $\{f\}\cup\{k_1,\dots,k_s\}$). **Finite fact J1 and row LIM use two hubs only** ($t=2$, one mixed vector).

Uses: Lemmas 1.1, 4.1, 4.4 (and its proof), 4.5 (one full helper per full-met label), 4.6 (through (C1)(a)); F2, F3.
Nothing beyond normalization. The family does not depend on which end of a pair is the hub's (same vector).

---

## D.3 Finite fact J1 [finite-checked, two implementations]

**Finite fact J1.** For each orientation and any two limit configurations $(h,R,S)$, $(h',R',S')$ with $h\ne h'$:

- **(J1a) intersecting pairs at a common full value.** If some $f\in S\cap S'$ has $P(h+f)\cap P(h'+f)\ne\emptyset$, the
  family $\mathcal F(h,R,S)\cup\mathcal F(h',R',S')$ (common $H_f$ identified, $H_f+T$ listed once) is linearly dependent;
- **(J1b) pair-value neighbours.** If $h+h'$ is a pair value, the family
  $\mathcal F(h,R,S)\cup\mathcal F(h',R',S')\cup\{H_h+H_{h'}+P(h+h')\}$ (common $H_f$ identified) is linearly dependent.

**Consequence (two limit hubs never share a missing label).** [proved from J1 and Lemma J] If two limit hubs $i\ne i'$
shared a full-met label, their pairs at its full helper would intersect (D.1) and Lemma J ($K=\{i,i'\}$, $X=\emptyset$)
would make the family of (J1a) independent; if they shared a hub-only label, $h_i+h_{i'}$ would be a pair value (D.1) and
Lemma J ($K=\{i,i'\}$, $X=\{\ell\}$) would make the family of (J1b) independent. Both contradict J1.

*The enumerations.* For each orientation: the 64 boundary masks, triples, full values (80 / 112), pair values (2,016)
and their pairs; the limit configurations from H2's enumeration (C.2): **192 / 352 / 48** at **8 / 64 / 12** values for
$r=0/1/2$ ($M$), **480 / 720 / 96** at **20 / 120 / 24** values ($M^{\mathsf T}$); for every pair of limit configurations
in the position of (J1a) or (J1b), the GF(2) rank of the family.

- `qjoint/qj_limit.py` (first implementation; geometry `qj_geo.py`, a re-implementation of `qhub/hub2.py`): for every
  limit configuration, (b) every hub-only partner $h'=h+p$ over all 2,016 pair values with **every** partner configuration
  $(R',S')$ of class $r'+|S'|\le3$ (independent alone), and (a) every partner meeting a common $f$ with intersecting
  pairs; $M$: **2,773,888** joint tests (1,005,920 / 1,534,992 / 232,976 for $r=0/1/2$), $M^{\mathsf T}$: **6,498,128**
  (2,583,200 / 3,418,384 / 496,544). The largest partner class $r'+|S'|$ with an independent joint family is **1-2 for
  hub-only sharing and 2 for same-label sharing, never 3**, in every class ($M$: hub-only $r=0$: 1 for all 192, $r=1$: 1
  for 112, 2 for 240, $r=2$: 2 for 48; same-label 2 except 1 for 40 at $r=1$; $M^{\mathsf T}$: hub-only 1 for 480 /
  1 for 160, 2 for 560 / 2 for 96; same-label 2 except 1 for 76 at $r=1$) (`qj_limit.out`, `limit_{M,Mt}.json`).
- `qjointcheck/jc_geo.py` (second implementation: own boundary parse, pair values, triples, full values, $N(h)$, limit
  configurations enumerated directly, lowest-bit elimination, no Lemma-4.6 pre-skip). (J1b): all pairs of limit
  configurations with $h+h'$ a pair value, **75,192** ($M$) / **208,272** ($M^{\mathsf T}$): **0 independent** in every
  class pair. (J1a): pairs sharing a full value $f$, counted per common $f$, 10,880 / 35,280; of them with intersecting
  pairs at $f$ **4,544** / **14,816**: **0 independent**; with disjoint pairs at $f$ (different labels): 1,936 / 9,680
  independent and 4,400 / 10,784 dependent (two limit hubs **can** share a full helper at different labels); different
  labels plus a shared hub-only label: 0 independent (1,248 / 2,880 dependent). The two $r=2$ limit hubs: 12 / 24 values,
  34 / 76 value pairs with XOR a pair value, 0 independent. Its partner mode redoes qj_limit's enumeration without
  pre-skip (3,033,600 / 7,104,432 joint tests) and reproduces qj_limit's partner tables number for number; H2 re-verified
  (0 independent sets with $|S|=4-r$) (`jc_j1.log`, `jc_partners.log`, `jc_j1_{M,Mt}.json`, `jc_partners_{M,Mt}.json`).

Both: **J1 holds in both orientations.** J1 rests on gate-equation independence alone (Lemma J), not on Lemma O1, the
degree excess or the budget. [finite-checked; programs of two agents; not re-run here]

---

## D.4 Lemma P: the label-class rows [proved]

**Lemma P.** In every normalized circuit of either orientation, with $a=A$ and the sums over hubs ($r_i\le2$) or full
helpers ($r_f=3$) as indicated:

$$
\begin{aligned}
&(\mathrm{P1})\quad \textstyle\sum_{r_i\le2}\binom{m_i}{2}+\sum_{r_f=3}\binom{u_f}{2}\le\binom{a}{2},\qquad
(\mathrm{P2})\quad \textstyle\sum_{r_i\le2}m_ie_i\le a(q-a),\qquad
(\mathrm{P3})\quad \textstyle\sum_{r_i\le2}\binom{e_i}{2}\le\binom{q-a}{2},\\
&(\mathrm{P4f})\quad \#\{i:\ |L_i\cap\Lambda_A|\ge3\}\le D(a),\qquad
(\mathrm{P4h})\quad \#\{i:\ r_i\le2,\ e_i\ge3\}\le D(q-a),\qquad
(\mathrm{P5})\quad \textstyle\sum_{r_i\le2}r_im_i\le\operatorname{top}(a)-3a,
\end{aligned}
$$

with $D(n)$ the packing bound of D.5 ($D(0..12)=0,0,0,1,1,2,4,7,8,12,13,17,20$).

*Proof.* By Lemma 4.6 every unordered pair of distinct missing labels lies in $L_i$ for at most one helper $i$.
(P1): the pairs inside $\Lambda_A$; a hub $i$ holds $\binom{m_i}2$ of them, a full helper $\binom{u_f}2$ ($L_f\subseteq\Lambda_A$).
(P2): the pairs with one label in $\Lambda_A$ and one in $\Lambda_0$; a hub holds $m_ie_i$, a full helper none.
(P3): the pairs inside $\Lambda_0$. (P4f, P4h): the sets $L_i\cap\Lambda_A$ of size $\ge3$ (resp. $L_i\cap\Lambda_0$ of
size $\ge3$) of distinct helpers are distinct (two equal sets of size $\ge3$ would share $\ge2$ labels) and pairwise
meet in $\le1$ element, so they form a family as in D.5 on the $a$-set $\Lambda_A$ (resp. the $(q-a)$-set $\Lambda_0$).
(P5): fix $\ell\in\Lambda_A$, met by the full helper $f$ (unique, Lemma 4.5). By the proof of (L7) per label ((L7\*),
A.4), the forms $E_\ell+T+B_b$, over the helpers $x$ meeting $\ell$ (edge $x$-$b$) and the represented triples $T$ of
$x$, are $W_\ell=\sum_{x\ \text{meets}\ \ell}r_x$ independent elements of $C_\ell$, so $3+\sum_{i\ \text{hub},\ \ell\in L_i}r_i\le W_\ell\le\operatorname{rank}(C_\ell)$.
The $a$ labels of $\Lambda_A$ are distinct elements of $\Lambda=\{f+c\}$ (C.6), so summing over $\Lambda_A$ gives
$3a+\sum_ir_im_i\le\sum_{\ell\in\Lambda_A}\operatorname{rank}(C_\ell)\le\operatorname{top}(a)$. $\square$

Uses: Lemmas 4.1, 4.5, 4.6; for P5 the proof of (L7) per label [read, not checked], F3, F6, FM (C.6). The values
$\operatorname{top}(a)-3a$: $M$: $4a$ for $a\le4$, then $16+3(a-4)$; $M^{\mathsf T}$: $3a$.

---

## D.5 The packing bound $D(n)$ [proved]

**Lemma D5.** A family of distinct subsets of size $\ge3$ of an $n$-set, pairwise meeting in at most one element, has at
most $D(n)$ members, where $D(n)=0$ for $n<3$ and otherwise $D(n)$ is the largest $N\le\lfloor n\lfloor(n-1)/2\rfloor/3\rfloor$
such that, for odd $n$, $\binom n2-3N\notin\{1,2\}$. Equivalently $D(n)=\lfloor n\lfloor(n-1)/2\rfloor/3\rfloor-[n\equiv5\pmod 6]$.

*Proof.* Replace each set by one of its 3-subsets: pairwise intersections stay $\le1$, so the triples are distinct and
pairwise share no pair. The triples through a point $x$ have pairwise disjoint pairs $T\setminus\{x\}$ in the remaining
$n-1$ points, so $x$ lies in at most $\lfloor(n-1)/2\rfloor$ of them; counting incidences, $3N\le n\lfloor(n-1)/2\rfloor$.
For odd $n$, let $\Gamma$ be the graph of the pairs covered by no triple: $\deg_\Gamma(x)=(n-1)-2t_x$ is even at every
$x$, so $\Gamma$ is empty or contains a cycle, hence has $0$ or $\ge3$ edges; $|E(\Gamma)|=\binom n2-3N$. For
$n\equiv5\pmod6$, $\binom n2\equiv1\pmod3$ and $3\lfloor n(n-1)/6\rfloor=\binom n2-1$, which leaves one edge; so $N$
drops by one (leaving four). For $n\equiv1,3\pmod6$ the leave is empty. $\square$

The bound equals the packing number $D(n,3,2)$ for all $n$ (Schönheim; Spencer 1968) [read, not checked; not needed:
soundness uses only the upper bound]. Exhaustive search confirms it is attained for $n\le7$ (`check_cases4.py`) and
$n\le9$ (`qjointcheck/jc_patch_lp.py`). The checker computes $D(n)$ by the proof's procedure; the generator by the
closed formula; they agree for $n\le20$ (the file's table is checked against the checker's bound).

---

## D.6 The rows in the exact hub case $A=a$: per-row relaxation [proved]

The rows of Lemma P bound sums of per-helper terms $\varphi(m_i)$; the local system has only the type counts
$n_t$, $t=(r,u,v)$. In the case $A=a$ (D.8) every hub $i$ of a kept type $t$ ($r\le2$, $u\le(3-r)+(q-a)$) has

$$
m_i\in I_t=\{m\in\mathbb Z:\ \max(0,\,u-(q-a))\le m\le\min(u,\,3-r)\}:
$$

$m_i\le3-r_i$ (Lemma H2), $m_i\le u_i$, and $e_i=u_i-m_i\le q-a$ because the $e_i$ labels are distinct elements of
$\Lambda_0$ (Lemma 4.1). $I_t\ne\emptyset$ exactly for the kept types. (The further restriction $m_i\le a$ is valid
and **not used**.) Each per-helper term is replaced by its minimum over $I_t$,
$c_t(\varphi)=\min_{m\in I_t}\varphi(m)\le\varphi(m_i)$; summing over the helpers,
$\sum_tc_t(\varphi)\,n_t\le\sum_i\varphi(m_i)\le$ (right side), so **each LP row is implied by the corresponding row of
Lemma P**. Explicitly, with $m_{\rm lb}=\max(0,u-(q-a))$ and $m_{\rm ub}=\min(u,3-r)$:

| row | term $\varphi(m)$ at a hub of type $(r,u,v)$ | monotonicity on $I_t$ | LP coefficient | full type $(3,u,v)$ | constant |
|---|---|---|---|---|---|
| P1 | $\binom m2$ | non-decreasing | $\binom{m_{\rm lb}}2$ | $\binom u2$ | $\binom a2$ |
| P2 | $m(u-m)$ | **concave** (second difference $-2$) | $\min\big(m_{\rm lb}(u-m_{\rm lb}),\ m_{\rm ub}(u-m_{\rm ub})\big)$ | 0 | $a(q-a)$ |
| P3 | $\binom{u-m}2$ | non-increasing | $\binom{u-m_{\rm ub}}2$ | 0 | $\binom{q-a}2$ |
| P4f | $[m\ge3]$ | non-decreasing | $[m_{\rm lb}\ge3]$ | $[u\ge3]$ | $D(a)$ |
| P4h | $[u-m\ge3]$ | non-increasing | $[u-m_{\rm ub}\ge3]$ | 0 | $D(q-a)$ |
| P5 | $r\,m$ | non-decreasing | $r\,m_{\rm lb}$ | 0 | $\operatorname{top}(a)-3a$ |

*The concave term.* $g(m)=m(u-m)$ satisfies $g(m+1)-2g(m)+g(m-1)=-2<0$; a concave function on an integer interval
attains its minimum at an endpoint (if $m_{\rm lb}<m<m_{\rm ub}$ then $g(m)\ge\min(g(m-1),g(m+1))$, and inductively
$g(m)\ge\min(g(m_{\rm lb}),g(m_{\rm ub}))$). Hence the P2 coefficient is the minimum of the two endpoint values; the
value at an interior point may be larger and is not used. The full-type coefficients are exact (all $u$ labels of a
full helper are full-met, Lemma 4.5). The generator uses the closed forms of the table (`qjoint/qj_lp.joint_rows`); the
independent checker computes every coefficient as the brute-force minimum over $I_t$ (`check_cases4.joint_column`);
`crosscheck4.py` shows they are identical on every node.

---

## D.7 Row LIM [proved from J1, Lemma J and Lemma 4.6]

In case $A=a$ call a type $t=(r,u,v)$ with $r\le2$ a **limit type** if $u=(3-r)+(q-a)$, i.e. $I_t=\{3-r\}$. A
helper of a limit type has $m_i=3-r_i$ (a limit hub) and $e_i=q-a$, so $\Lambda_0\subseteq L_i$: **it carries every
hub-only label**. Row LIM:

$$
a<q:\quad \sum_{t\ \text{limit}}n_t\le1,\qquad\qquad a=q:\quad \sum_{t\ \text{limit}}u_t\,n_t\le q .
$$

*Proof, in three cases.* (i) $a\le q-2$: two helpers of limit types would both contain $\Lambda_0$, $|\Lambda_0|\ge2$,
against Lemma 4.6; at most one. (ii) $a=q-1$: two helpers of limit types would share the single hub-only label, and both
are limit hubs: impossible by J1 (D.3, (J1b) with Lemma J); at most one. (iii) $a=q$: a limit type has $u=3-r=m$, all its
labels full-met; two limit hubs share no label (D.3, (J1a) with Lemma J), so the $L_i$ of the helpers of limit types are
pairwise disjoint subsets of $\Lambda_A$, $|\Lambda_A|=q$: $\sum u_tn_t\le q$. $\square$

(For $q=0$ there is no limit type, $u\ge1>q$; the row is $0\le0$.) Case (i) needs only Lemma 4.6; J1 enters cases (ii)
and (iii) only. Uses: Lemmas 4.1, 4.5, 4.6, H2 (C.4), Lemma J, finite fact J1.

**Where the certificates use LIM.** [certified] Only in case (ii): 78 certificates, each for a whole hub case
$(A=q-1,\text{none})$ -- 66 at $(q,A)=(4,3)$ for $M$, 12 at $(3,2)$ for $M^{\mathsf T}$; no certificate uses LIM in case
(i) or (iii). So of finite fact J1 **only part (J1b), hub-only sharing, is load-bearing**; part (J1a) enters no
certificate. The generator seeks a certificate without LIM first (D.9), so these 78 are exactly the hub cases where none
was found.

---

## D.8 The exact integer split $A=0,\dots,q$ as the disjunction [proved]

$A=\sum_{r=3}u\,n$ is the number of full-met labels, an integer with $0\le A\le q$ ((4.2), row (L6)). For every key
(every $q$, including $q\le1$) the **hub cases** are $A=a$, $a=0,\dots,q$. In case $A=a$ the case system has: the
equality $\sum_{r=3}un=a$ (two inequalities); the types with $r\le2$ and $u>(3-r)+(q-a)$ removed (row HUB2, C.4:
such helpers do not exist when $A=a$); and the rows P1, P2, P3, P4f, P4h, P5, LIM of D.6-D.7 with this $a$.

*Exhaustiveness.* $A$ takes exactly one of the values $0,\dots,q$. *Soundness.* A phase with $A=a$ satisfies the rows
of Lemma P and LIM with $a$ (D.4, D.7), hence their LP forms (D.6), has no helper of a removed type, and its type counts
satisfy every other row of the case system (Addenda A-C): it is a nonnegative solution of the case system of $a$. So
**if every leaf case of a key is infeasible, no phase with that key exists.**

*Relation to Addendum C.* Batch 3's case $A\le1$ ($q\ge2$) is split into $A=0$ and $A=1$ (each contains $A\le1$: a
multiplier on "$A\le1$" moves to "$A\le a$" with constant $a\le1$); its other cases $A=a\ge2$ are kept with rows added;
for $q\le1$ the unsplit system of batch 3 is split, rows added. Every new case system is at least as strong as a
batch-3 case system containing it, so the bounds $(k,l)$ of every claim are monotone (checked on all 7,416 claims by
`gen_certs4.py`). The integer split is not only a carrier of the joint rows: **five batch-3-feasible keys die by the
split alone**, the $M^{\mathsf T}$, $q=1$ keys $(h,y,F,q,z)=(12,5,F,1,4)$, $F=1,\dots,5$ (among them the load-bearing
$(12,5,1,1,4)$ of qjoint's section 5): each has four leaf certificates $(A,q_D)\in\{0,1\}^2$ using no joint row and no
FM or PK row (package rows L1-L3, the batch-1 rows N1, L19\*, L20\*, the hub rows $A\le0$ resp. $A\ge1$, and the DARK
rows; `rows_used.py`). Batch 3 did not split at $q\le1$ (row HUB2 is vacuous there), so its system admitted a fractional
$A\in(0,1)$; the exact split forbids it. (Addendum C's remark (i), that the integer refinement changes no key set at
$G=75$, came from qhubcheck's variant HUB2X on the key lists compared there [read, not checked]; it does not extend to
these five keys.)

---

## D.9 Case systems, certificates, coverage

For a key $(h,y,F,{\rm ori},q,z)$ and a case (hub, dark) the **case system** has the columns of C.7 (types with
$r+u+v\ge3$, minus in hub case $A=a$ the types of D.8; $y_0,y_1,y_2$; in a dark case $y_{2d},F_b,F_d$) and the rows,
in this order: 1. the package rows (L1)-(L23); 2. the batch-1 rows of A.6; 3. the flat batch-3 rows (PK4/PK5, the
FM7/FM9 chords, C.6); 4. hub $A=a$: $\sum_{r=3}un=a$ (two inequalities); 5. dark $q_D=d$: the rows of B.6 item 4;
6. hub $A=a$ only: P1, P2, P3, P4f, P4h, P5, LIM of case $a$ (zero on the auxiliary columns). Cases: hub
$\in\{\text{none}\}\cup\{A=0,\dots,A=q\}$, dark $\in\{\text{none},0,\dots,q\}$; leaves $(A=a,q_D=d)$, $(q+1)^2$ of them.
A certificate for a case is a nonnegative integer vector $\lambda$ over its rows with $\lambda^{\mathsf T}A\ge0$ on every
column and $\lambda^{\mathsf T}b<0$ (section 11).

**Lemma C1 (B.6) applies verbatim.** [proved] The joint rows are hub rows: they occur only in hub cases and have zero
coefficients on $y_0,y_1,y_2,y_{2d},F_b,F_d$. A certificate for (none, none), extended by zeros and restricted to the
columns of a case, is one for every leaf (deleting columns deletes constraints); a certificate for $(A=a,\text{none})$,
extended by zeros on the dark rows, is one for every $(A=a,d)$ (the dark columns occur only in dark rows). **Coverage:**
a key is covered if every leaf $(a,d)$ has a certificate for $(a,d)$, $(a,\text{none})$, $(\text{none},d)$ or
(none, none); by D.8, B.4 and Lemma C1 a covered key admits no phase. Each certificate records its hub case ($A$ value)
and its dark case ($q_D$, or none).

**What is certified.** [certified] `qcert4/CERTIFICATES_CASES75_B4.json`: **4,361 certificates for 1,307 keys** (745
package, 101 batch-1, 9 flat, **3,506 per case**: 2,350 for a whole hub case $(A=a,\text{none})$, 1,156 for a leaf
$(A=a,q_D=d)$; largest weighted right side $-1$): complete case coverage of **all 375 keys** that are LP-feasible under
the batch-3 systems and infeasible under the systems above, the batch-3-feasible keys being (a) those of qcert3's files
(the 859 LP-feasible keys of the batch-3 scan and the 1,177 batch-3 survivors of the 1,713 batch-2-feasible keys; union
1,437; 343 of them killed) and (b) the 242 keys the new scan touched outside these lists that are batch-3-feasible (210
new-feasible, hence batch-3-feasible by D.8; 32 new-infeasible, batch-3 feasibility evaluated with the unmodified batch-3
system; all 32 killed) -- among them **all 163 of the 551 load-bearing keys** killed (the $551\to388$ recount) -- 14,096
leaves; and, for each of the **103 oriented claims** excluded by the new systems and not by batch 3 (the $789\to686$
reduction), every $(q,z)$ below the stated $k,l$ is excluded by (4.4), Lemma 10.3 or a covered key (980 keys, 18,418
leaves), and $k>S_e$ or $l>S_o$ or $k+l>a+b+2G-192$. Two programs check everything: `gen_certs4.py` (rows from
`certify75.system` and gen_certs3, joint rows in closed form) and `check_cases4.py` (hand-written rows of check_cases3
plus brute-force joint rows, standard library only, own case tree); `crosscheck4.py` shows their matrices are identical
on every case node of the keys with case certificates (REPORT.md). For the 1,304 batch-3-feasible keys that survive,
`CERTIFICATES_PARTIAL75_B4.json` certifies every killed case (22,586 certificates; 44,058 of their 47,987 leaves dead,
3,929 open by LP status); no exclusion rests on it.

**J1-free first, and what holds without J1.** In every hub case the generator first seeks a certificate without the
row LIM (padded by a zero on LIM and re-verified), and uses LIM only where none exists. 78 certificates use LIM, all in
case (ii) of D.7 (J1b). Without them: **297 of the 375 killed keys and 65 of the 103 claims are covered**
(`check_cases4.py`, coverage recomputed over the J1-free certificates); the other 78 keys ($M$, $q=4$: 66; $M^{\mathsf
T}$, $q=3$: 12) and 38 claims rest on J1. The LP scan without LIM agrees: 724 survivors, i.e. 65 of the 103 excluded
without LIM [measured].

---

## D.10 What the statements use

| statement | package lemmas used | finite facts used |
|---|---|---|
| Lemma J (joint family, spanning trees) | 1.1, 4.1, 4.4 (and its proof), 4.5, 4.6 via (C1)(a) | F2, F3 |
| Finite fact J1 and its consequence | Lemma J; (C1) | F2, F3, H2 (limit configurations), J1 |
| Lemma P (P1-P5) | 4.1, 4.5, 4.6; proof of (L7) per label / (L7\*) (A.4) for P5 | F3, F6, FM (P5) |
| Lemma D5 (packing bound) | none (elementary) | none |
| LP forms (D.6) | Lemma H2 (C.4), 4.1 | H2 |
| Row LIM | 4.1, 4.5, 4.6, H2, Lemma J | J1 (cases a = q-1, q) |
| Exact split, soundness, monotonicity | (4.2) / (L6); row HUB2 (C.4) | none |
| Lemma C1, coverage | section 11, 10.3, 4.7 / (4.4) | none |
| rows 1-5 of the case systems | Addenda A, B, C [read, not checked here] | F2-F14, H2, FM (through them) |

Lemma 7.4 enters only through the column set $r+u+v\ge3$, as in the package. Nothing uses the potential or the tail.

---

## D.11 Positive controls [finite-checked; not a proof]

`stress_ext4.py`: on the 13 controls and 303 real circuits (1,264 phases, 4 orbit steps each, own odd-graph
extraction) every strong form (P1-P5 with the actual $m_i$, H2, HUB2's column deletion, J1, LIM) and both LP forms
hold, the two LP implementations agree on every type met, and each LP coefficient is at most the helper's actual
term (20,745 helpers): **0 violations**. As in batches 1-3, $A=0$ on every phase and no phase has a limit hub, so the
new rows are exercised only through $\Lambda_0$ (P3, P4h). On qjointcheck's synthetic two-hub phases (102,792 phases
built by `jc_circ.synthetic` from `jc_geo`'s limit configurations, up to 6,000 per kind, 11,912 of them with
independent $\mathcal F_{\rm joint}$) every realizable phase satisfies every row (0 violations; P2, P3, P4h, H2, J1,
LIM tight on some), and every phase of a J1-excluded kind is dependent and violates the LP row LIM. Local
configurations, not circuits: whether any normalized circuit has $A\ge1$ is open.

---

## D.12 Status

| statement | label |
|---|---|
| Lemma J, with $t_\ell-1$ tree vectors per shared hub-only label | [proved] |
| Finite fact J1 ((J1a), (J1b)); counts of D.3 | [finite-checked] (qjoint `qj_limit.py`; qjointcheck `jc_geo.py`, two modes) |
| two limit hubs never share a missing label | [proved] from J1 and Lemma J |
| Lemma P (P1-P5); Lemma D5; the LP forms of D.6 | [proved] |
| Row LIM (three cases) | [proved] (case (i) from Lemma 4.6; (ii), (iii) from J1) |
| exact split $A=0..q$ exhaustive; case systems relaxations; Lemma C1 | [proved] |
| 375 killed keys covered (163 load-bearing); 103 claims covered; 4,361 certificates (3,506 per case) | [certified] (`check_cases4.py`, `gen_certs4.py`) |
| without J1: 297 of the 375 keys and 65 of the 103 claims covered; LIM used only in case (ii) (J1b), 78 certificates | [certified] (`check_cases4.py`) |
| five $M^{\mathsf T}$, $q=1$ keys killed by the integer split alone | [certified] |
| 44,058 of the 47,987 leaves of the 1,304 surviving batch-3-feasible keys dead (22,586 certificates) | [certified] (`check_cases4.py`); the 3,929 open leaves [measured] |
| the two system definitions coincide on 22,301 case nodes of 452 keys | [finite-checked] (`crosscheck4.py`) |
| 686 claims remain open; 1,304 batch-3-feasible keys, 814 LP-feasible / 483 load-bearing scan keys remain | [measured] (LP status) |
| zero violations on 1,264 phases and on 102,792 synthetic phases | [finite-checked] (positive control) |
| Addenda A-C, package Lemmas 1.1-10.4, F2-F14, H2, FM | [read, not checked here] |
| any bound beyond 75 | **not claimed** |
