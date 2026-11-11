# Pilot specification: complete local realizability enumeration for the M^T, q = 3 block at G = 75

Proof agent, 2026-11-10. Notation of PROOF.md (sections 1, 4, 10, 11) and Addenda A-D
(`lower-bound-proofs/mixcolumns-lb75-open-cases/addenda/`). Orientation M^T throughout (the boundary B is the 32 inputs
and the 32 columns of M); everything is stated for a fixed key K = (h, y, F, 'Mt', 3, z) and a fixed leaf (A = a, q_D = d)
of its exact case tree (D.8, B.4). Tags: **[proved]** (proof here, package lemmas and finite facts as black boxes),
**[finite-checked]** (program named), **[measured]** (solver status), **[read, not checked]** (package or addendum
statement relied on as is). Nothing here claims or suggests a bound above 75.

Written BEFORE the enumeration was run; the program `enum_q3.py` implements exactly the rules of section 3 and the
search of section 8; `verify_q3.py` re-checks every output object against section 3 with separately written code.

---

## 1. The object: the label configuration of a phase

Fix a normalized circuit C of orientation M^T (Lemma 1.1) whose phase has key K and lies in the leaf (A, q_D) = (a, d).
Its **label configuration** O(C) is the following data.

1. **The labels.** The set Λ = {ℓ1, ℓ2, ℓ3} of the q = 3 missing labels (section 4): three distinct nonzero even
   32-bit values (even signals have even masks; distinct signals have distinct masks, Lemma 1.1 (i)).
2. **The carriers.** The set I of helpers i with u_i >= 1 (at least one H-B edge with a missing label); for each i in I:
   - its mask h_i (odd, not in B: a helper is an odd gate signal that is not an output; its mask differs from every
     input and output mask by Lemma 1.1 (i));
   - its represented count r_i in {0,1,2,3} and its set R_i of r_i boundary triples T with XOR h_i, one per represented
     edge i-a with label l = b + c: T = {a, b, c} (Lemma 4.4; the triples of one helper are distinct and r_i <= 3 by
     F3); for r_i = 3 (a *full* helper) R_i is the set of all three triples of the full value h_i;
   - its label set L_i, a subset of Λ with |L_i| = u_i (the missing labels on its H-B edges: distinct labels, since two
     edges at a vertex with a common label would coincide, Lemma 4.1);
   - for every l in L_i the boundary end b_{i,l} in B of the edge i-b with label l. The gate of that edge has equation
     {h_i, b, l} in masks, so **b_{i,l} = h_i + l**; it is determined by h_i and l.
3. **The statuses.** A label is *full-met* if it lies in L_f for some f in I with r_f = 3 (an H-B edge at a full
   helper); exactly a labels are full-met (D.8: A = a is the number of full-met labels; by Lemma 4.5 each full-met label
   lies in L_f for exactly one full helper f, and by Lemma 4.1 each f carries it once, so A = sum_{r_f = 3} u_f). A label is
   *dark* if no i in I with r_i >= 1 carries it (Lemma 10.2: no H-B edge at an anchored helper; a missing label with no
   H-B edge at all is dark); exactly d labels are dark. The remaining 3 - a - d labels are *bright hub-only*: each has a
   carrier with r_i >= 1 and none with r_i = 3.

**What O(C) does not contain.** The H-H counts v_i and the H-H edges, the even+even gates and the kinds y0, y1, y2,
y2d, F_b, F_d, the helpers with u_i = 0 (full or not), the represented labels' values, the gate order (chronology), the
circuit outside the odd graph. In particular a full helper with u_f = 0 is not in I, and the a full helpers in I are those
carrying a full-met label.

**Lemma 1.1' (one object per circuit).** [proved] Every normalized circuit of the leaf induces exactly one object O(C), and
O(C) satisfies every rule of section 3. *Proof.* The odd graph (section 4) is determined by the circuit; it fixes the
missing labels, the helpers' H-B edges, their labels and boundary ends, and the represented relations (Lemma 4.4), hence
every item 1-3. Each rule of section 3 is a statement proved for every normalized circuit, see the citations there. QED

Two objects are the *same* if they differ only by the names of the labels and of the helpers (Λ and I are sets).

---

## 2. Allowed ranges (the finite domains) and the bounds from the rows

Finite facts about the fixed boundary B of M^T, recomputed by `geo_q3.py` (own parse of the repository matrix through
`jc_geo.read_boundary`, cross-checked against the package's `stress.BOUNDARY`) **[finite-checked]**:

- F2: the 64 boundary masks and their 2,016 pairwise XORs (*pair values*) are distinct; PM maps a pair value to its pair.
- F3: triple values: 40,936 odd values are the XOR of a boundary triple (40,320 with one triple, 504 with two, 112 with
  three = the *full values*). 10,234 orbits under the byte rotation (section 4).
- F6: for an even value l let forms(l) be the set of 2- and 4-subsets D of B with XOR l and C_l the span of the vectors
  E_l + sum_{b in D} B_b. Λ_1 := {l : forms(l) nonempty} has 593,251 elements; rank(C_l) = 1 + rank{D + D0 : D in forms(l)}
  has the histogram 1: 561,014, 2: 22,830, 3: 7,678, 4: 1,273, 5: 234, 6: 216, 7: 6 (PROOF.md F6 for M^T, identical).
  Labels with rank >= 2 / 3 / 4 / 5 / 6 / 7: 32,237 / 9,407 / 1,729 / 456 / 222 / 6; orbit representatives 8,127 / 2,387
  / 457 / 138 / 60 / 6.

**Ranges of the data.** [proved]

- (D-l) A bright label lies in Λ_1 and has rank(C_l) >= W_l := sum over the carriers i of l of r_i. *Proof.* A bright
  label has an anchored carrier i (r_i >= 1) with a triple T in R_i and end b = h_i + l; D = T xor {b} has XOR h_i + b = l
  and size 2 or 4 (b in T gives size 2, b not in T size 4), so l is in Λ_1. The rank bound is the per-label statement of
  (L7) / (L7*): the W_l forms E_l + T + B_{b_i} over the anchored carriers and their triples are independent elements of
  C_l (proof of (L7), PROOF.md section 10; it is also the single-label case of Lemma J*, 3.7 below). QED
  A dark label is any even value: it is constrained only through the masks of its (unanchored) carriers.
- (D-h) A helper with r_i >= 1 has a mask with at least r_i triples (Lemma 4.4, F3): 40,936 values for r = 1, 616 for
  r = 2, 112 for r = 3. A helper with r_i = 0 has any odd mask not in B.
- (D-b) For i in I and l in L_i, b_{i,l} = h_i + l in B. Equivalently h_i is in l + B: **once l is fixed, a carrier of l has
  at most 64 masks**, and once h_i is fixed, a label at i has at most 64 values h_i + b.
- (D-2) A helper carrying two labels l, l' has b_{i,l} + b_{i,l'} = l + l', so {b_{i,l}, b_{i,l'}} is THE pair of the pair
  value l + l' (F2): **two labels carried by a common helper have a pair value as XOR, and the helper's mask is one of the
  two values l + b, b in that pair.** (This is the mechanism of Lemma 4.6.)
- (D-shared) Two carriers i, i' of a label l have h_i + h_{i'} = b_{i,l} + b_{i',l}, a pair value (the ends differ since
  the masks differ); a hub i and a full helper f sharing l have f in N(h_i) (C.1, (C1)(a)).

**Multiplicity bounds from the rows.** [proved, relative to the rows] The type vector n of the phase (helpers by type
(r,u,v), r+u+v >= 3 by Lemma 7.4 for the phases of the claims, PROOF.md section 11) is a nonnegative integer solution of the
leaf's **combined case system** S(K, a, d) = `check_combined75.matrix(K, ('eq', a), d)`: the package rows (L1)-(L23), the
batch-1 rows (A.6), the flat rows PK/FM (C.7), the hub rows sum_{r=3} u n = a and the deletion of the types with r <= 2 and
u > (3 - r) + (3 - a) (HUB2, C.4), the joint rows P1-P5 and LIM of case a (D.6-D.7), the dark rows of case d (B.6 item 4)
and the October rows push5/push6 (README "Relation to the October 2026 campaigns"; `check_combined75.push_rows`), with the
auxiliary unknowns y0, y1, y2, y2d, F_b, F_d. Every row is proved for every normalized circuit in its document
[read, not checked]; the type counts of C restricted to u >= 1 are exactly c_{r,u} := #{i in I : (r_i,u_i) = (r,u)}. Hence:

- (B-LP) the system S(K,a,d) together with the twelve rows sum_v n_{r,u,v} = c_{r,u} (r = 0..3, u = 1..3; the deleted types
  count 0) has a nonnegative real solution. This is rule R8 of section 3; it is **the** finite bound on multiplicities,
  used as stated and not tightened. Its consequences, computed once per leaf by LP (`lp_bounds.py`, [measured], used only
  to size the search, never as a rule): over the 207 open leaves of the 66 LP-feasible keys of the block, W = sum r u n
  lies in [12, 21], the number of carriers sum_{u>=1} n is at most 11, the number of unanchored carriers sum_{r=0,u>=1} n at
  most 2, and U = sum u n at most 14; the per-class maxima over all leaves are at most (0,1): 1, (0,2): 2, (0,3): 1,
  (1,1): 4, (1,2): 3, (1,3): 1, (2,1): 7, (2,2): 3, (2,3): 0, (3,1): 2, (3,2): 0 (floors of the LP maxima; the enumeration
  does not use these numbers, it applies R8 at every node). All 207 leaves have a <= 2 and d <= 1.
- (B-1) Row (L7*)/F6 per label: W_l <= rank(C_l) <= 7 for every l (section 10; (D-l)). In particular a label has at most
  seven carriers with r = 1, three with r = 2, and a full helper contributes 3 to W_l of each of its labels.
- (B-2) Lemma 4.6: two carriers share at most one label. With q = 3: at most one helper has u = 3, and then no other
  helper has u >= 2; otherwise at most three helpers have u = 2, one per pair of labels.
- (B-3) Lemma 4.5 / D.8: the full helpers in I number at most a (each carries >= 1 full-met label, no label is at two full
  helpers) and sum_{r_f=3} u_f = a exactly.

---

## 3. The rules: necessary conditions of a normalized circuit, each with its lemma

Every rule below is a property of O(C) for EVERY normalized circuit C of the leaf; none restricts the object to shapes seen
in known circuits (the known circuits all have A = 0 and q >= 7, Addendum C.8, and play no role here).

- **R1 (Lemma 1.1).** The masks h_i, i in I, are pairwise distinct, odd, and not in B. The labels are pairwise distinct,
  even, nonzero.
- **R2 (Lemma 4.1).** L_i is a set of |L_i| = u_i labels; the ends b_{i,l} = h_i + l at one helper are distinct (they are,
  since the labels are); the carriers of a label are distinct helpers with distinct ends (they are, since the masks are).
- **R3 (Lemma 4.4, F3).** R_i consists of r_i distinct boundary triples with XOR h_i; r_i <= 3; if r_i = 3, h_i is a full
  value and R_i its three triples.
- **R4 (Lemma 4.5, D.8).** Each label lies in L_f for at most one f with r_f = 3; the labels in L_f (r_f = 3) are
  full-met; exactly a labels are full-met. (The statement of 4.5 that two full helpers never have a pair-value XOR is
  implied by R7 through F4 and is also checked explicitly.)
- **R5 (Lemma 4.6).** |L_i intersect L_{i'}| <= 1 for i different from i'.
- **R6 (Lemma 10.2, B.4).** Exactly d labels have no carrier with r_i >= 1; each of the other 3 - d labels has one.
- **R7 (Lemma J*, below).** The joint family F(O) is linearly independent over GF(2).
- **R8 (the rows; (B-LP)).** S(K,a,d) with the count rows sum_v n_{r,u,v} = c_{r,u} (u >= 1) is LP-feasible. Implementation:
  scipy HiGHS; the rule prunes ONLY on status 2 (infeasible); every other status counts as "not pruned" [measured]. An
  infeasibility reported by the solver is a solver statement, not an exact certificate; the report states where R8 was
  load-bearing, and the pruned count vectors are recorded so that exact Farkas certificates can be produced for them.
- **R8-int (the rows, integrality).** The type vector n of the phase is a vector of nonnegative INTEGERS (counts of
  helpers; y0, y1, y2, y2d are counts of gates, F_b, F_d sums of integers). Hence S(K,a,d) with the exact count rows of R8
  has a nonnegative integer solution. Implementation: scipy HiGHS MILP (`verify_q3.milp_status`, time limit 20 s), applied
  to every complete skeleton after R8; prunes ONLY on status 2 (infeasible); a time limit (status 1) or any other status
  counts as "not pruned" [measured]. It is the same relaxation as R8 with integrality kept; no exact certificate is
  produced for its prunes, and the report lists per leaf how many skeletons R8-int removed, so that what rests on it is
  visible. Witnesses report the same MILP status for their own counts (section 9).

### 3.7 Lemma J* (the joint family of a configuration) [proved]

Let O be the object of a normalized circuit. Write H_i for a formal coordinate of i in I and B_b (b in B) for the boundary
coordinates; a boundary subset stands for the sum of its B_b. For each label l let C(l) = {i in I : l in L_i} be its carriers
and T_l the edge set of any spanning tree of the complete graph on C(l) (empty if |C(l)| <= 1). Put

  F(O) = { H_i + T : i in I, T in R_i }  union  (over l)  { H_i + H_{i'} + {b_{i,l}, b_{i',l}} : {i,i'} in T_l }.

(The pair {b_{i,l}, b_{i',l}} is PM(h_i + h_{i'}) by (D-shared).) **Then F(O) is linearly independent.**

*Proof.* Consider the gate equations, as formal vectors over all signal coordinates (E_m for even signals): (1) the B-B
reference E_m + B_b + B_c of every represented label m carried by a represented edge of some i in I (unique, Lemma 4.1; one
row per label); (2) the represented H-B equations E_m + H_i + B_a, sum r_i of them; (3) the missing H-B equations
E_l + H_i + B_{b_{i,l}} for every i in I and l in L_i, sum u_i of them. These are equations of pairwise distinct gates
(distinct edges of the odd graph: a reference is a B-B edge, the others are H-B edges at distinct (helper, end) pairs by
Lemma 4.1, and represented and missing labels differ), so they are linearly independent: in a nonempty sum the result
signal of the latest gate occurs in its own equation only (Lemma 1.1; the argument of the proof of Lemma 4.4).
*Pivot 1.* Add each reference to the rows of (2) carrying its label: E_m + H_i + B_a becomes H_i + T with T the triple of
the relation (Lemma 4.4); E_m now occurs only in the reference row, which is deleted. *Pivot 2.* For each label l with
carriers i_1, ..., i_t (t >= 1): add the row of i_1 to the rows of i_2, ..., i_t; row j becomes
H_{i_1} + H_{i_j} + B_{b_1} + B_{b_j}; E_l now occurs only in the row of i_1, which is deleted (for t = 1 the row is simply
deleted). Row additions are invertible and the deletion of a row holding a coordinate that occurs in no other row preserves
the independence of the remaining rows; so the surviving family -- the triple vectors and, per label, the star centred at
i_1 -- is independent. *Any spanning tree.* For i, i' in C(l), {b_{i,l}, b_{i',l}} = {b_1, b_i} xor {b_1, b_{i'}}, so every
tree vector of l is the sum of two star vectors and every star vector the sum of the tree vectors along the tree path from
i_1; the t - 1 tree vectors span the same space as the t - 1 star vectors, and replacing a part of an independent family
by an equally large set with the same span keeps it independent. QED

Uses: Lemmas 1.1, 4.1, 4.4 (and its proof); F2, F3. Nothing beyond normalization. Lemma J* is Lemma J of D.2 with K = the
hubs of I and S = the full helpers in I (pivot 2 at a full-met label is D.2's pivot 2, the star at f; at a shared hub-only
label it is D.2's pivot 3), plus the triple vectors of the full helpers of I that meet no hub (added gate equations keep
the family independent). It implies, as the subfamilies named: condition (C1) and Lemma H2 (C.3-C.4, the family
F(h_i, R_i, S_i) is contained in F(O)), finite fact J1's consequence and row LIM (D.3, D.7), Lemma 4.5's pair-value
statement (F4), (L7)/(L7*) per label and (D-l) (project away the H coordinates of a single label's carriers: the forms),
FM's rank >= 3 of full-met labels, and (L9)/(L12) per label. These are therefore not separate rules of the enumeration; the
report records them as implied.

**Lemma 3.8 (hereditary).** [proved] Let O be an object satisfying R7 and O' a sub-object: a subset I' of its helpers with
label sets L'_i contained in L_i intersect Λ' for a subset Λ' of Λ (and the same masks, triples and ends). Then F(O') is
independent. *Proof.* Build F(O) with, for each l in Λ', a spanning tree of C(l) that contains a spanning tree of
C'(l) = C(l) intersect I' (extend a tree of C'(l) to one of C(l)). Then F(O') is literally a subfamily of F(O); a subfamily
of an independent family is independent; and by the last paragraph of Lemma J* the choice of trees for O' is immaterial.
QED Consequently every partial configuration visited by a depth-first construction of a valid object (section 8) satisfies
R7, and R1-R6 restricted to the present helpers and labels: the depth-first pruning by R1-R7 is complete. R8 is hereditary
in its relaxed form (section 8, step S).

**Lemma 3.9 (free riders).** [proved] Let i in I have r_i = 0 and u_i = 1, l its label. Choose the trees T_l so that i is a
leaf (possible: take a star centred at another carrier, or any tree if |C(l)| = 2). Then H_i occurs in exactly one vector of
F(O) (if |C(l)| >= 2) or in none; that vector cannot occur in a vanishing combination. Hence F(O) is independent iff
F(O minus {i}) is, for every mask h_i; and the constraints on h_i are R1 (h_i = l + b for some b in B with l + b not in B
and l + b distinct from the other masks; at most 2 + |I| of the 64 values are excluded). Such helpers are therefore
realizable whenever |I| <= 61, and they are added to witnesses explicitly but not branched over.

**Lemma 3.10 (free components).** [proved] Call two labels *linked* if a common carrier has both; a *component* of O is a
class of labels under linking together with their carriers. Suppose a component Γ has at most one anchored helper k
(r_k >= 1) and its incidence graph (labels of Γ and carriers of Γ, an edge for each incidence) is acyclic. Then F(O) is
independent iff F(O minus Γ) is, for every realization of Γ's masks and labels obeying R1-R3; and such realizations exist.
*Proof.* A vanishing combination of F(O) uses, at every helper, an even number of vectors containing its H coordinate.
Choose the trees of Γ's labels as stars centred at a carrier that is nearest to k in the incidence tree (or arbitrary when
k is not in the component). The subgraph on Γ's helpers whose edges are Γ's tree vectors is then a forest (a cycle would
project to a closed walk, hence a cycle, in the acyclic incidence graph), and the only other vectors at Γ's helpers are
the triple vectors of k. Peeling leaves of the forest (a leaf helper's H occurs in exactly one tree vector and, k apart, in
no triple vector) shows that no tree vector of Γ occurs in a vanishing combination. So the combination uses, inside Γ, only
triple vectors of k, an even number of them: none, or two with sum T + T' different from 0 (distinct triples; for r_k = 3
the same for every pair). Hence the combination lives entirely outside Γ. Realizations: pick h_k with >= r_k triples (R_k
any r_k of them), ends b in B arbitrary subject to distinctness, unanchored carriers as in Lemma 3.9 (their masks l + b, b
free), dark labels as h + b of their first carrier; finitely many values are excluded by R1 at each step and more than
64 - 2 - |I| remain. QED
Free components impose nothing beyond their counts (which R8 sees); the enumeration realizes them explicitly in witnesses
and does not branch over them. A component with two or more anchored helpers, or with a cycle in its incidence graph, is
*constrained* and is enumerated completely (section 8).

---

## 4. Symmetry: the byte rotation [proved]

Let ρ be the permutation of the 32 bit positions i -> i + 8 (mod 32) and, by abuse, the induced linear map on masks.
**[finite-checked]** (`geo_q3.py`): ρ maps the 32 input masks to input masks and the 32 columns of M (the output masks of
M^T) to columns of M, so ρ(B) = B; likewise for the rows of M. (Reason: MixColumns is byte-circulant, output byte c =
02 b_c + 03 b_{c+1} + 01 b_{c+2} + 01 b_{c+3}, so ρ M ρ^{-1} = M.)

**Lemma 4.1' (ρ acts on circuits of the leaf).** For a normalized circuit C of orientation M^T, let ρC be the circuit with
inputs relabelled by ρ and outputs reordered accordingly. (i) ρC computes M^T (ρ M^T ρ^{-1} = M^T) and is normalized; every
signal mask is rotated, so parities, the boundary, the helpers, the odd graph with its labels, the represented / missing
status, the types (r,u,v), x, y, h, q, z, A, q_D are preserved; F (the sum of f_v over the signals, section 10, a function
of the gate graph and the parities) is preserved. So ρC is a normalized circuit of the same key K and the same leaf (a,d),
and O(ρC) = ρ(O(C)) (masks, labels, ends, triples all rotated). (ii) Independently of (i): every rule R1-R8 is invariant
under ρ (ρ permutes B, maps triples to triples, pairs to pairs, forms to forms, and induces a coordinate permutation of
the formal space that preserves GF(2) ranks; the counts are unchanged). *Consequence.* If every object with its root label
(section 8) in a fixed set of orbit representatives violates some rule, then every object violates some rule: for an
object O choose j with ρ^j(root label) a representative; ρ^j(O) violates a rule, hence so does O by (ii). Orbits have size
1, 2 or 4. No other symmetry is used.

---

## 5. Unanchored components and dark labels

A dark label has only carriers with r = 0 (R6). By Lemma 3.10 the component containing a dark label is free unless it
contains a cycle through the dark label (two or more helpers with u >= 2 carrying it) or two anchored helpers (through
bright labels of the same component). Treatment in the enumeration:

- A dark label whose component is free: its value is **symbolic** (any even value distinct from the other labels and not
  making a carrier's mask coincide with another mask or lie in B); Lemma 3.10 shows every such choice is accepted by
  every rule, so no choice is enumerated. Witnesses receive an explicit value (the first admissible h + b of its first
  carrier, or, if it has no carrier at all, the first admissible even value).
- A dark label inside a constrained component: it is reached through a helper i with u_i >= 2 whose other label is already
  concrete, so h_i is already concrete up to the 64 choices of (D-b), and the dark label is enumerated over the 64 values
  h_i + b, b in B (minus R1 exclusions); its other carriers are then enumerated by (D-b) (<= 64 masks each; r = 0, u = 1
  carriers by Lemma 3.9). The mixed vectors of a tree of r = 0 carriers are independent for every value (their H
  coordinates alone are independent); dependencies arise only around cycles through bright labels, and those are detected
  by R7 on concrete values.

With d <= 1 in every open leaf of the block (section 2), at most one label is dark.

---

## 6. The exact conclusion of an empty result

If, for the leaf (a, d) of K, the enumeration of section 8 finds no object satisfying R1-R8, then: **no normalized
circuit of orientation M^T with key K and (A, q_D) = (a, d) exists at G = 75** (Lemma 1.1': such a circuit would induce an
object satisfying every rule; sections 7-8: the enumeration visits, up to ρ and up to the free parts of Lemmas 3.9-3.10,
every object satisfying R1-R7, and discards only objects violating a rule). The leaf is then **excluded** in the sense
of D.8 / B.4. If every open leaf of K is excluded (the leaves not open are already LP-infeasible, hence excluded by the
case systems' relaxation argument, B.4 / D.8), the key K admits no phase: K is excluded. Which claims this bears on is
read from `../scope/ladders.json` (a claim closes only when every LP-feasible key at its first feasible even level and
odd level dies in a way that pushes k + l beyond the budget; a key's exclusion raises the first feasible level of a
claim only when it is the last feasible key at that level).

The enumeration represents LOCAL configurations satisfying necessary conditions, not circuits. An empty enumeration is an
impossibility result for the leaf. **A surviving configuration is NOT a circuit**: it is a local witness that the rules
R1-R8 do not exclude; it would still have to be completed by H-H edges, even+even gates and a chronology, and to satisfy
every condition not represented here (the represented labels' gates, the accumulation trees of section 3, Lemma 7.4 per
helper, the drift argument). The grade of an exclusion is [finite-checked] by `enum_q3.py` (one implementation, with
`verify_q3.py` re-checking the controls and witnesses), with R8 at [measured] grade where the pruning used solver status
(section 3, R8), stated per leaf in the report.

---

## 7. Completeness argument

**Claim.** Let C be a hypothetical normalized circuit of orientation M^T with key K and leaf (a, d) at G = 75, O = O(C).
Then the enumeration of section 8 either visits an object ρ^j(O) (j in {0,1,2,3}) and accepts it, or it prunes a partial
configuration that ρ^j(O) extends, by a rule that ρ^j(O) itself violates -- which cannot happen. Hence if the enumeration
accepts nothing, C does not exist.

*Proof.* (1) O satisfies R1-R8 (Lemma 1.1', section 3). (2) **Skeleton.** The skeleton of O -- the statuses of the three
labels and, for each i in I, the pair (r_i, L_i) -- is one of the skeletons enumerated in step S of section 8: step S
enumerates every assignment of statuses (a full-met, d dark, 3 - a - d bright hub-only labels), every multiset of roles
(r, L) with L a nonempty subset of Λ subject only to R4 (full helpers' labels full-met, one full helper per full-met label,
a full-met labels), R5, R6 (anchored carrier at each bright label, none at a dark one), (B-1) (sum of r_i over the
carriers of a slot <= 7, a consequence of R7), the column set of S(K,a,d) (a type deleted by HUB2 in case a has count 0),
and R8 in its monotone form (at every prefix: the counts so far are lower bounds, sum_v n_{r,u,v} >= c_{r,u}; at the
complete skeleton: equality), followed by R8-int at the complete skeleton. Since adding roles only increases counts, every
prefix of O's skeleton (in step S's canonical order) passes the monotone form, and the complete skeleton passes R8 exactly
and R8-int (the type vector of C is an integer solution with these counts), by (1). Step S's canonical
representative of O's skeleton under the status-preserving permutations of the slots is visited; O, with its labels renamed
accordingly, has that skeleton. (3) **Rotation.** Let l* be the root label of that skeleton (section 8, the bright slot of
largest W in the first constrained component, ties broken by the canonical slot order). Choose j with ρ^j(l*) an orbit
representative; O' := ρ^j(O) satisfies R1-R8 (Lemma 4.1' (ii)) and has the same skeleton. (4) **Realization.** Step G of
section 8 enumerates, for the skeleton, every assignment of concrete values to the constrained components' roles in the
fixed role order: the root label over the orbit representatives with rank(C_l) >= W_{l*} (O' has rank(C_{l*}) >= W_{l*} by
(D-l)); each anchored role over the <= 64 masks l + b of a concrete label of the role, b in B, with each choice of r_i
triples of that mask (R3; O' s mask is one of them by (D-b) and its triples are among the triples of its mask); each further
label of the role either checked (concrete) or set to h_i + b over b in B (O' s value is one of them by (D-b)); each role
with r = 0 and u >= 2 likewise; a new constrained component's first anchored role over all labels with rank >= W (no further
rotation) and then as above. Roles with r = 0 and u = 1, and whole free components, are not branched over (Lemmas 3.9,
3.10): they are realizable for every state of the rest, and O' s own values for them show that O' restricted to the
constrained part is an object the enumeration can reach. Along the path to O' s constrained part, every intermediate node
is a sub-object of O' (Lemma 3.8's sense: a subset of helpers, labels restricted to those already concrete), and each
pruning rule applied at a node (R1, R3, R5 on the present helpers, R7 on the present family, the root's rank condition) is
a condition O' s sub-object inherits from O' (Lemma 3.8 for R7; R1, R3, R5 restrict). So no node on the path is pruned,
and the complete constrained part of O' is reached and accepted; the enumeration then extends it by explicit free parts
(Lemmas 3.9-3.10 guarantee their existence) and reports a survivor. (5) The same argument with "O' is pruned at node N by
rule R" shows: a pruned node is a configuration no valid O' extends. QED

What the argument does not cover, and the conclusion is restricted accordingly: (i) the rows of S(K,a,d) [read, not checked];
(ii) solver status for R8 [measured]; (iii) the finite facts F2, F3, F6 recomputed here [finite-checked] and the GF(2) rank
routine (two implementations, `jc_geo.rank` lowest-bit pivots and `geo_q3.rank_hi` highest-bit pivots, compared on every
accepted object and on the controls).

---

## 8. The enumeration (what `enum_q3.py` does)

**Step S (skeletons).** Slots 1..3 with statuses: slots 1..a full-met, a+1..3-d bright hub-only, 4-d..3 dark. Roles
(r, L): r in {0,1,2,3}, L a nonempty subset of {1,2,3}; r = 3 requires L inside the full-met slots; r >= 1 requires L
disjoint from the dark slots; (r, |L|) must be a column class of S(K,a,d) (HUB2 deletion). Roles in a fixed order;
multisets as non-decreasing sequences; after each role R5 (pairwise), (B-1) per slot and R8 monotone (LP with
sum_v n_{r,u,v} >= counts) are checked; a complete skeleton must satisfy R4 (full-met slots each covered by exactly one
r = 3 role, a in total), R6 (each bright slot has an r >= 1 role, dark slots none) and R8 exact (equality). Skeletons are
canonicalized under the status-preserving slot permutations (duplicates dropped). Node counts and LP prunes recorded; the
LP-pruned count vectors recorded for later exact certification.

**Step G (geometric realization) per skeleton.** Components by linking (section 3.10); free components set aside.
Constrained components are processed in order of decreasing largest W of their slots. Role order within a component:
anchored roles first, breadth-first from the component's root slot through shared slots; then roles with r = 0, u >= 2;
roles with r = 0, u = 1 set aside (Lemma 3.9). Branching:
  - root label of the first constrained component: orbit representatives l with rank(C_l) >= W_{root}; root label of
    every further constrained component, and of every anchored role that touches no concrete slot when its turn comes
    (its link to the concrete part runs only through r = 0 helpers, which are placed after all anchored roles): all l
    with rank(C_l) >= W of the role's largest-W slot (no rotation);
  - an anchored role touching a concrete slot l: b in B with h = l + b not in B, h having >= r triples, h new (R1); R_i
    over the r-subsets of the triples of h (all three if r = 3); each further slot of the role: concrete -> check
    h + l' in B; not concrete -> b' in B minus the ends at i, l' := h + b' (R1 on l': even nonzero, new);
  - a role with r = 0, u >= 2 touching a concrete slot l: h = l + b (b in B, R1), other slots as above (if a second slot is
    concrete, h + l' in B forces b into the pair of l + l', (D-2));
  - after every assignment: R1, R3, R5 (skeleton), R7 incrementally (basis with the vectors of the realized roles: triple
    vectors, and per concrete label the star tree centred at its first realized carrier), prune on failure;
  - identical roles (same (r, L), hence |L| = 1 by R5, attached to the same slot one after the other) are interchangeable
    helpers of the object (section 1: I is a set); they are placed with increasing mask, which visits each object once.
  - several segments (anchored roles reachable from different roots): each segment is enumerated on its own (all its
    realizations stored, up to a cap); a segment without realization excludes the skeleton (every realization of the whole
    restricts to one of each segment, Lemma 3.8); otherwise the product of the segment lists is searched lazily for a
    combination passing R1 across segments, R7 on the union and the placement of the r = 0, u >= 2 helpers; the first
    combination found is a witness, an exhausted product is an exclusion, a cap or a CPU deadline makes the skeleton (and
    the leaf) UNRESOLVED, never excluded.
  - leaves of step G: every constrained role realized -> add explicit free parts (Lemmas 3.9-3.10), run `verify_q3.py`
    (independent re-check of R1-R8 with the second rank routine and a fresh LP), run the MILP of section 9, record.

**Recording.** Per leaf: skeletons visited / LP-pruned / accepted; geometric nodes by depth; prunes by rule (R1, R3, no
candidate (D-b), R7, root rank); the first few pruned configurations at the deepest level reached; witnesses.

**Size estimate (before the run).** For each leaf and each accepted skeleton: (number of root representatives with
rank >= W_root) x product over the roles of the first component of the maximal candidate count (<= 64 x C(3, r) for
anchored roles, 64 or 2 for r = 0 roles), x for every further constrained component (number of labels with rank >= W) x
its product -- an upper bound on the geometric nodes without R7 pruning; and a refined estimate using the actual
candidate counts c_r(l) = #{(b, R) : l + b not in B has >= r triples} summed over the root set. Both are written to the
report before the main run; the run is started only if the refined estimate fits the budget of 4 CPU-hours (nice -n 10),
else the pilot stops and reports.

---

## 9. Witnesses

For every surviving configuration: masks, triples, labels, ends, statuses; the output of `verify_q3.py` (every rule, both
rank routines); and the integer status of the leaf's case system with the configuration's counts imposed
(`scipy.optimize.milp`, status recorded; "integer-feasible" only on status 0 with an exact re-check of the solution against
every row; "integer-infeasible" only on status 2). A witness is a local object, not a circuit (section 6); the report lists
the compatibility conditions it would still have to satisfy.

---

## 10. Status of the statements of this specification

| statement | tag |
|---|---|
| Lemma 1.1' (one object per circuit); (D-l), (D-h), (D-b), (D-2), (D-shared); (B-1)-(B-3) | [proved] |
| Lemma J* (joint family of a configuration), Lemma 3.8 (hereditary), 3.9 (free riders), 3.10 (free components) | [proved] |
| Lemma 4.1' (rotation), both parts | [proved]; ρ(B) = B [finite-checked] (`geo_q3.py`) |
| the completeness argument (section 7) | [proved], relative to the items listed at its end |
| F2, F3, F6 for M^T (counts of section 2) | [finite-checked] (`geo_q3.py`; identical to PROOF.md Appendix A) |
| the rows of S(K,a,d) (package, Addenda A-D, October rows) | [read, not checked] |
| R8 pruning decisions (HiGHS status 2) | [measured] |
| any bound above 75 | **not claimed** |

---

## 11. Addendum of 2026-11-11 (after the first run; nothing above was changed today)

1. **Order of the roles in step G.** The program does not use the static breadth-first order of section 8 inside a
   segment: after the root, it branches at every node on the remaining role with the fewest viable candidates (a role
   with none prunes the node). The completeness argument of section 7 (4) does not depend on the order: at every node the
   target object O' has a helper for each remaining role, that helper is among the viable candidates of its role ((D-b),
   (D-2), R1, R3 and the increasing-mask convention for identical roles), so whichever role is chosen, the branch of O' is
   present and is not pruned by a rule O' satisfies. [proved, same argument]
2. **A bug found and fixed before the second pass** (`patch_20261111.py`; the first-run code is
   `enum_q3_pass1_snapshot.py`). In skeletons with several segments, the product phase placed every r = 0, u >= 2 helper of
   the order, including those already placed inside a segment, i.e. twice. This could report "no combination" for a
   realizable skeleton: a possible FALSE exclusion. It affects only multi-segment skeletons with an r = 0, u >= 2 role
   whose segments all had realizations. The second pass (`pass2_q3.py`) re-ran every such skeleton with the corrected
   code (one skeleton; its outcome did not change) and reused a first-run outcome only when it could not be affected.
   The final results are those of `results_final/`.
3. **Search-level control P5** (`controls_p5.py`): 9,651 valid three-label objects that do not come from the enumerator
   (hereditary sub-configurations of real phases in both orientations, and planted M^T objects with full-met labels);
   step S must produce each one's skeleton and step G must reach each one's constrained part. This tests the search, not
   only the rules; see the report for the shapes covered and not covered.
4. **Exact certificates for R8.** `farkas_q3.py` / `farkas_run.py` produce, for every LP decision "infeasible" of step S,
   a nonnegative integer vector lambda with lambda^T A >= 0 on every column and lambda^T b < 0, checked in exact integer
   arithmetic. Where every LP prune of a leaf has one, the leaf's R8 prunes are [certified] instead of [measured].
   R8-int (MILP) prunes remain [measured].
5. **Caps.** Step G runs under CPU caps per skeleton; a capped skeleton makes its leaf UNRESOLVED unless another skeleton
   of the leaf survives (SURVIVING) -- never EXCLUDED.
6. **Join for several segments** (`pass2d_q3.run_join`, rounds D and E). Before the product of the segment
   realizations, a label combination is discarded when some deferred helper with r = 0, u >= 2 has no mask h with
   h + l_s in B for all its concrete slots s and h not in B. This is a necessary condition for placing that helper
   ((D-b), (D-2), R1), so no realizable combination is lost; the remaining combinations go through the product phase
   unchanged. [proved, one line; validated as described in the report, section 3.4]
