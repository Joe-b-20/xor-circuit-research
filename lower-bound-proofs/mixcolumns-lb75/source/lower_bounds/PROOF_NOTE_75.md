# A computer-assisted lower bound of 75 two-input XOR gates for AES MixColumns

**Review draft, version 1.1, 2026-10-02.** Joe Bachir. (Version 1.0 was 2026-10-01; 1.1 corrects one
cross-reference in section 10 and the commands of section 14 after a review of the verification runner.)

**Status.** Computer-assisted. The mathematical argument is written out in full below; the fourteen finite
facts about the fixed matrix that it uses (section 12) are computed by programs shipped next to this note, and
the last two steps are exact certificates checked by programs. The argument was produced with large-language-
model assistance and has been reviewed only by programs and by independent machine reviews (section 13). No human mathematician has refereed it, and nothing is formalized in a proof assistant. It is
offered for review, not as an established result.

---

## 0. Theorem and circuit model

**The map.** M is the 32 x 32 matrix over GF(2) of one column of AES MixColumns (FIPS-197). Bit i of a
32-bit state, 0 <= i <= 31, is bit (i mod 8) of byte floor(i/8), least significant bit first. Output byte c is
02·b_c + 03·b_(c+1) + 01·b_(c+2) + 01·b_(c+3) (byte indices mod 4) in GF(2^8) with reduction polynomial
x^8 + x^4 + x^3 + x + 1. M^T is its transpose. The repository files `matrix.txt` / `matrix.sha256` fix M
bit by bit; `verify.py` rebuilds it from the field arithmetic.

**Circuits.** A circuit is a straight-line program over GF(2): signals 0..31 are the inputs; gate k
(k = 0, 1, ...) computes signal 32+k as the XOR of two earlier signals a, b < 32+k. The circuit computes M
if each of the 32 rows of M is the coefficient vector of some signal; those 32 signals are the outputs.
Nothing else is restricted: outputs may be used by later gates, intermediate values are arbitrary,
cancellation (a gate whose result has fewer input bits than its operands) is allowed, there is no bound on
depth or fan-out, and the outputs may appear in any order. Every gate counts, including the gate that
produces an output. L(M) is the least number of gates of a circuit computing M.

**Theorem.** Every circuit computing M has at least 75 gates. With the verified 88-gate circuits in this
repository,

    75 <= L(M) <= 88.

The theorem does not say that 88 is optimal and gives no 87-gate circuit.

**Reading guide.** Sections 1-5 are elementary counting (they prove L(M) >= 69). Sections 6-9 use
transposition and a bounded potential (they prove L(M) >= 73 with one small rank computation). Sections
10-11 add a system of linear inequalities on "helper types" whose infeasibility, for every remaining count
profile at 73 and 74 gates, is certified by nonnegative integer multipliers (Farkas certificates) that a
standard-library program checks. Section 12 lists the finite facts, section 13 the review record, section
14 the commands.

---

## 1. Conventions, normalization, gate accounting

**Masks and parity.** The *mask* of a signal is its coefficient vector in GF(2)^32 over the inputs; a gate
XORs the masks of its operands. A signal is *odd* or *even* according to the Hamming weight of its mask.
The 32 inputs (unit vectors) are odd. The rows of M have weight 5 or 7, the rows of M^T (= columns of M)
weight 5 or 11; so all outputs are odd in both orientations, and no output is an input.

**Lemma 1.1 (normalization).** A minimum circuit has (i) all 32 + G masks distinct and nonzero, (ii) every
gate used, as an operand of a later gate or as an output, (iii) each row of M carried by exactly one signal,
which is a gate.

*Proof.* A gate with mask zero or equal to an earlier mask can be deleted after redirecting its uses to the
earlier signal; an unused gate can be deleted; both lower the gate count. (iii) follows from (i) and from
the rows not being inputs. The same holds for a minimum circuit of M^T. []

A circuit with these properties is called *normalized*. Throughout, C is a normalized minimum circuit of M
or of M^T with G gates. The *boundary* B is the set of the 64 odd signals consisting of the 32 inputs and
the 32 outputs; the h odd gate signals that are not outputs are the *helpers*, H.

**Lemma 1.2 (gate accounting).** Let x count the gates with two odd operands, y the gates with two even
operands, and h the helpers. Then

    G = 32 + x + y + h.

*Proof.* A gate with two odd or two even operands has an even result; a gate with one odd and one even
operand has an odd result. The odd gate results are exactly the 32 outputs and the h helpers. []

---

## 2. The even span: x >= 24 in both orientations

**Lemma 2.1 (partition lemma).** Let E be the span of the masks of the even signals computed so far.
Then every odd signal computed so far is congruent to an input unit vector modulo E, and E is spanned by
differences e_i + e_j of unit vectors. Consequently E is the space of vectors with even weight on every
block of a partition P of the 32 inputs, dim E = 32 - c where c is the number of blocks, and the number x
of odd+odd gates satisfies x >= 32 - c.

*Proof.* Induction over the gates. Initially E = 0 and the odd signals are the inputs. An odd+even gate
adds an element of E to a unit-congruent mask, so its result is congruent to the same unit. An even+even
gate does not enlarge E. An odd+odd gate with operands congruent to e_i and e_j has an even result equal to
e_i + e_j modulo the old E, so E grows by at most the span of e_i + e_j. A space spanned by unit
differences is the within-block even-parity space of the partition "i ~ j iff e_i + e_j in E", whose number
of blocks is c = 32 - dim E. Each odd+odd gate raises dim E by at most one. []

**Lemma 2.2.** Let b_C be the indicator vector of block C of the final partition. Every output row has odd
intersection with exactly one block; hence the c vectors M b_C are disjoint and cover the 32 output
coordinates, and the c pairs (b_C, M b_C) are disjoint nonzero words of the graph code
C_M = { (u, M u) : u in GF(2)^32 } that together cover all 64 coordinates.

*Proof.* An output o is odd, so o = e_i + (element of E) for some input i: o has odd weight on the block of
i and even weight on every other block. The coordinate of M b_C at output o is the inner product of row o
with b_C, i.e. the parity of o on block C. []

**Finite fact F1.** Neither C_M nor C_(M^T) contains nine disjoint nonzero words covering all 64
coordinates. (Eight exist: the eight bit families 0x01010101 << j are fixed by M.)

*How F1 is established.* All words of the graph code have even weight (every column of M is odd) and the
nonzero ones have weight at least 6; the complete lists of words of weight 6 and 8 are obtained by
enumerating all input halves of weight <= 4 and all output halves of weight <= 4 (one half of a word of
weight <= 8 has weight <= 4): 84 and 276 words for M, 60 and 248 for M^T. In a nine-part partition of 64
coordinates by such words, order the parts by weight; while k >= 3 parts remain, the lightest remaining part
has weight at most floor((64 - 6(9-k))/k) <= 9, hence <= 8. So the seven lightest parts belong to the short
list. The program enumerates every choice of seven disjoint short words in nondecreasing weight order and
tests whether the complement (itself a codeword, since (1, M 1) = (1, 1) is a codeword) splits into two
disjoint nonzero codewords: it does iff the code shortened to the complement's support has dimension >= 2,
i.e. |I| - rank(M[rows outside O, columns in I]) >= 2 for its input support I and output support O. No
choice splits (M: 1,485,213 search states, 62,112 final checks; M^T: 91,485 and 720; an independent
traversal over all unordered seven-packings gives 13,165,941 and 2,936,355 states, same verdict).

**Corollary 2.3.** c <= 8 and x >= 24 for every normalized circuit of M and of M^T.

---

## 3. Transposition and accumulation trees

**Fan-out.** For a signal v let d_v be the number of gates using v as an operand, plus one if v is an
output (its *terminal use*). In a normalized circuit every d_v >= 1. There are 2G operand uses and 32
terminal uses among 32 + G signals, so

    sum_v (d_v - 1) = (2G + 32) - (G + 32) = G.                                     (3.1)

**Lemma 3.1 (exact transposition).** Attach an independent variable z_j to the terminal use of output j.
Define the *adjoint* a(v) of every signal, in reverse order, as the XOR of a(w) over the gates w using v,
plus z_j if v is output j. Then a(input i) = (M^T z)_i, computing a(v) from its d_v contributions takes
d_v - 1 XOR gates in any binary association, and the resulting circuit has exactly G gates and computes M^T.
Hence L(M^T) = L(M), and every such *raw transpose* of a minimum circuit is a minimum, hence normalized,
circuit of the other orientation.

*Proof.* a(v) is the coefficient of v in sum_j z_j y_j by linearity, so a(input i) is column i of M applied
to z. The gate count is (3.1). The construction in both directions gives L(M^T) <= L(M) <= L(M^T). A raw
transpose with a removable gate would give a circuit of M^T with fewer than L(M^T) gates. []

**Accumulation trees.** The gates building a(v) form a binary tree whose leaves are the d_v contributions
(the signals a(w) for the users w of v, and z_j for a terminal use). Signals with d_v = 1 get no gate: their
adjoint *is* the single contribution, the same signal of the transpose (a *wire*). Every gate of the
transpose belongs to exactly one accumulation tree; v is the *origin* of those gates.

Contributions are odd or even as signals of the transpose (over the z's). Let k_v be the number of odd
contributions at v; z_j is odd. The parity of a(v) is k_v mod 2.

**Lemma 3.2 (even+even gates in a tree).** In any binary tree summing d terms of which k are odd, the
number of odd+odd gates is floor(k/2), and the number of even+even gates is at most

    f(d, k) = max(0, d - ceil(k/2) - 1),

with equality exactly for the associations in which the only odd-valued gate is the root: pair the odd
terms, sum all the even values in any order, add the leftover odd term (if k is odd) last. Such an
association is called *canonical*. Moreover

    d <= 3 + 2 f(d, k).                                                            (3.2)

*Proof.* Each odd+odd gate lowers the number of odd values by two, the other gate types keep it; the root's
parity is k mod 2, so there are floor(k/2) odd+odd gates. Count even values: there are d - k at the start,
each odd+odd gate creates one, each even+even gate consumes one net, each odd+even gate consumes one; at
the end one even value remains iff k is even. So #ee + #oe = d - k + floor(k/2) - [k even]. If k is odd
and d >= 2 the root is an odd+even gate, so #oe >= 1; if k is even #oe >= 0. Hence #ee <= d - ceil(k/2) - 1
(for d >= 2; for d = 1 there is no gate), with equality iff #oe = [k odd], i.e. iff no gate other than the
root is odd. The canonical association attains it. (3.2): f(d, k) >= d - ceil(d/2) - 1 >= (d - 3)/2. []

Write f_v = f(d_v, k_v) and F = sum_v f_v over all signals, F_H = sum over helpers. For a circuit C let
T(C) denote a raw transpose in which every accumulation is canonical (there may be several; everything below
holds for each of them). By Lemma 3.2,

    y(T(C)) = F,       x(T(C)) = sum_v floor(k_v / 2).                             (3.3)

---

## 4. The odd-signal graph

**Definition.** The *odd graph* of a normalized circuit has one vertex per odd signal (64 boundary vertices
B and h helper vertices H) and one edge per gate with exactly two odd signals in its equation: an odd+odd
gate gives an edge between its two operands, an odd+even gate an edge between its odd operand and its
result. The edge is *labelled* by the even signal of the equation. There are x + 32 + h edges and x + y
possible labels (the even signals).

**Finite fact F2 (Sidon boundaries).** The 64 boundary masks are distinct, and their 2,016 pairwise XORs
are distinct, for M and for M^T.

**Lemma 4.1.** The odd graph is simple; for each label the edges with that label form a matching; each
label has at most one edge with both ends in B (a *B-B edge*).

*Proof.* Two edges on the same pair {p, q} have the same label p + q, so the same gate equation {p, q, l};
two gates with the same equation would make the later result a duplicate of a signal that already existed
(it is an operand of the earlier gate). At a vertex v the edge with label l goes to v + l, so the label
determines the other end. Two B-B edges with label l give two boundary pairs with XOR l, contradicting F2. []

**Definitions.** A label is *represented* if it has a B-B edge and *missing* otherwise. Let q be the number
of missing labels, counted among ALL x + y even signals (an even signal that labels no edge at all is
missing), z the number of edges with both ends in H (*H-H edges*), and s = q + z. For a helper i let r_i be
the number of its edges to B with a represented label (*represented edges*), u_i the number of its edges to
B with a missing label, v_i the number of its H-H edges; (r_i, u_i, v_i) is the *type* of the helper. A
helper with r_i >= 1 is *anchored*; one with r_i = 3 is *full*. R = sum r_i, U = sum u_i.

**Lemma 4.2 (edge counts).** #(B-B edges) = x + y - q; #(H-B edges) = R + U = 32 + h - y + q - z; and

    sum_(v in H) d_v = 32 - y + q + z.                                             (4.1)

*Proof.* Each represented label has exactly one B-B edge (Lemma 4.1). The H-B edges are the rest minus the
H-H edges. A helper has degree d_v + 1 (its defining gate and one edge per use; no terminal), and the degree
sum over H is #(H-B) + 2z. []

**Lemma 4.3 (fan-out cap).** q + z <= 3h + 2F_H + y - 32 <= 3h + 2F + y - 32.

*Proof.* (4.1) and (3.2) summed over the helpers. []

**Finite fact F3 (triple multiplicity).** For both boundaries, the number of three-element subsets of B
with a given XOR is at most 3. Histograms (value: number of subsets): M: 40,704 values with one subset, 360
with two, 80 with three; M^T: 40,320 / 504 / 112.

**Lemma 4.4 (represented relations).** A represented edge i-a with label l = b + c (b-c its B-B edge)
gives the relation h_i = a + b + c with a, b, c distinct boundary signals. Writing each as a formal vector
H_i + B_a + B_b + B_c over the signal coordinates, the set of all represented relations of the circuit is
linearly independent. Hence the r_i triples at a helper are distinct and r_i <= 3.

*Proof.* The G gate equations are independent as formal vectors (the latest signal in a nonempty combination
cannot cancel). Take the subfamily consisting of all B-B edge equations and all represented H-B edge
equations, add to each H-B equation H_i + B_a + E_l the reference equation E_l + B_b + B_c, then delete the
reference rows; both operations preserve independence. a is not b or c since h_i is not a boundary value.
Distinct independent relations at one helper are distinct triples with XOR h_i, so r_i <= 3 by F3. []

**Finite fact F4 (adjacent full values).** Call a value *full* if it is the XOR of three boundary triples
(80 values for M, 112 for M^T) and *repeated* if it is the XOR of at least two (440 / 616). For two distinct
full values whose XOR is a boundary pair value, the six formal vectors H_1 + T (three triples T of the first)
and H_2 + T' (three of the second) have rank 5 (360 such pairs for M, 504 for M^T); for every other pair of
full values the rank is 6 (2,800 / 5,712 pairs).

**Lemma 4.5 (full helpers).** Two full helpers are never adjacent (their XOR is never a boundary pair
value). A missing label meets at most one full helper through an H-B edge, so

    sum_(i: r_i = 3) u_i <= q.                                                     (4.2)

*Proof.* Two adjacent full helpers would carry six represented relations of rank 5, contradicting Lemma 4.4.
Two full helpers i, j meeting the same missing label l through edges i-a, j-b have h_i + h_j = a + b. []

**Lemma 4.6 (missing pairs).** Two different helpers share at most one missing label. Hence

    sum_i C(u_i, 2) <= C(q, 2).                                                    (4.3)

*Proof.* Suppose helpers i, j both carry the missing labels l and m: edges i-a (label l), i-b (label m),
j-c (label l), j-d (label m), with a != b and a != c, b != d (matchings). Then a + c = h_i + h_j = b + d, and
F2 forces {a, c} = {b, d}, i.e. a = d and b = c. The four gate equations then sum to zero (each label occurs
twice), contradicting the independence of gate equations. []

**Lemma 4.7 (incidence inequality).** Every normalized circuit of either orientation satisfies

    32 <= 2h + y + z + C(q, 2).                                                    (4.4)

*Proof.* Let n_3 be the number of full helpers. R <= 2h + n_3 by Lemma 4.4. For the non-full helpers
u_i <= 1 + C(u_i, 2), so by (4.2), (4.3), U <= (h - n_3) + q + C(q, 2). Add: R + U <= 3h + q + C(q, 2), and
R + U = 32 + h - y + q - z by Lemma 4.2. []

---

## 5. The global maximum and the universal lemma: L(M) >= 69

**Definition.** Y is the largest number of even+even gates of any minimum circuit of M or of M^T. Note
y(C) <= Y for every minimum circuit C of either orientation, and y(T(C)) = F(C) <= Y by (3.3).

**Lemma 5.1 (universal lemma).** Every minimum circuit C of either orientation satisfies h_C + Y >= 13.

*Proof.* Suppose h + Y <= 12. Lemma 4.3 with F <= Y and y <= Y gives q + z <= 3(h + Y) - 32 <= 4. For
nonnegative integers with q + z <= 4, z + C(q, 2) <= 6 (the maxima for q = 0..4 are 4, 3, 3, 4, 6). Then
(4.4) with y <= Y gives 32 <= 2(h + Y) + 6 <= 30. []

**Corollary 5.2.** L(M) >= 69: a circuit attaining Y has x >= 24 and h + y = h + Y >= 13, so G >= 32 + 24 + 13.

---

## 6. Adjoint parities and the weighted-degree identity

Fix a normalized minimum circuit C and its adjoints a(v) (section 3); write a_v for the parity of a(v) and
let x' be the number of odd+odd gates of a raw transpose, which by Lemma 3.2 is sum_v floor(k_v/2) for any
association. Let Q be the number of gates of C with odd adjoint and e_1 the number of even+even gates of C
with odd adjoint.

**Lemma 6.1.** Q = 2x'.

*Proof.* sum_v k_v counts each odd gate adjoint at its two operands plus 32 odd terminals: 2Q + 32.
sum_v a_v counts the Q gates and the 32 inputs, whose adjoints (the rows of M^T) are odd: Q + 32. And
a_v = k_v mod 2, so 2 x' = sum_v (k_v - a_v) = Q. []

**Lemma 6.2 (weighted degrees).** Give each edge of the odd graph the weight a_g in {0, 1}, where g is the
result signal of its gate. Then (i) a helper has weighted degree 2 ceil(k_v/2); (ii) every boundary vertex
has odd weighted degree, hence at least 1; (iii) the sum of all weighted degrees is 2(Q - e_1). Consequently

    2x' >= 32 + sum_(v in H) ceil(k_v/2) + e_1,                                     (A)
    2x' + h + y + F_H >= 64 + q + z + e_1.                                          (B)

*Proof.* (i) At a helper v the defining edge has weight a_v and the use edges have total weight k_v;
a_v = k_v mod 2. (ii) An input has no defining edge and use weight k_v, which is odd since a(input) is a row of
M^T. An output has defining weight a_v and use weight k_v - 1 (the terminal is odd and is not an edge);
a_v + k_v - 1 is odd. (iii) The gates with odd adjoint are Q in number; e_1 of them are even+even gates,
which give no edge; the other Q - e_1 give one edge of weight 1 each. (A) is (i)-(iii) halved. For (B) use
ceil(k_v/2) >= d_v - f_v - 1 (from the definition of f_v) and (4.1). []

*Remark (exact form).* Keeping all terms, (B) is the identity
2x' + h + y + F_H = 64 + q + z + e_1 + L_H + sum_(v in B) (wdeg_v - 1)/2, where L_H counts helpers with
d_v = k_v = 1 and wdeg_v the weighted degree; and per boundary vertex (wdeg_v - 1)/2 + f_v = max(0, d_v - 2).
None of this is needed below, but it shows where the slack of (B) sits.

---

## 7. Double transposition: the origin identity and the inverse association

**Lemma 7.1 (origin identity).** Let D = T(C) (or any raw transpose), and let t be a gate of D built in the
accumulation tree of origin v. The adjoint of t in D, i.e. its coefficient vector over the outputs of D
(indexed by the inputs of C), equals the mask of v in C.

*Proof.* Consider a unit perturbation injected at t. Inside the accumulation tree it reaches the root a(v)
unchanged (the tree only XORs). From a(v) it propagates through the reversed network of C: a(v) contributes
to a(p) and a(q) for the gate v = p + q, and so on, down to the outputs of D, which are the adjoints of the
inputs of C. The number of paths (mod 2) from a(v) to a(input i) in the reversed network equals the number
of paths from input i to v in C, which is bit i of the mask of v. A signal p with d_p = 1 creates no gate:
a(p) is the same signal as the single contribution, and the paths through p are counted exactly once. []

**Lemma 7.2.** For any raw transpose D of C and any raw transpose of D, x(T(D)) = x(C). In particular the
odd+odd counts of a repeatedly transposed circuit alternate between two fixed values.

*Proof.* The gates of D with odd adjoint are those whose origin is odd: Q(D) = sum_(v odd) (d_v - 1). Count
the uses of odd signals of C: 2x (odd+odd gates) + (32 + h) (odd+even gates have one odd operand) + 32
(terminals) over 64 + h odd signals, so Q(D) = 2x. By Lemma 6.1 applied to D, Q(D) = 2 x(T(D)). []

**Lemma 7.3 (inverse association).** For every raw transpose D of C there is an association of the reverse
accumulation of D that rebuilds C gate for gate. Consequently, for canonical T, y(T(T(C))) >= y(C).

*Proof.* For a signal w of C let sigma(w) be the signal of D that carries a(w): the root of w's accumulation
tree if d_w >= 2; otherwise sigma(w) = sigma(g) for the unique gate g using w, or z_j if w is output j used
only terminally. For a signal s of D let S(s) = { w : sigma(w) = s }. All elements of S(s) except its latest
one have fan-out 1 and are used inside S(s), so the gates of S(s) form a binary expression tree whose leaves
are (i) operands p of gates of S(s) with p not in S(s) (then d_p >= 2, otherwise p would be in S(s)) and
(ii) inputs of C that belong to S(s). The uses of s in D are in bijection with these leaves: for a leaf of
type (i), s is one of the d_p contributions at p and is consumed by one gate of p's tree; for a leaf of
type (ii), s is the output of D for that input and has one terminal use. By Lemma 7.1 applied to D, the
adjoint (in D) of the gate consuming s in p's tree is the mask of p, and the terminal use carries the unit of
the input. Reverse D by associating, at every s, the contributions along the expression tree of S(s): this
creates exactly the gates of S(s) with their original operand masks, |leaves| - 1 = |S(s) gates| of them.
Over all s this is C. For the second claim, T(T(C)) maximizes the even+even count at every accumulation
(Lemma 3.2), and the association just described has y(C) even+even gates. []

**Lemma 7.4 (no odd helper leaves).** In a canonical transpose D = T(C) every odd helper has fan-out >= 2,
i.e. odd-graph degree r + u + v >= 3.

*Proof.* In a canonical association the only odd-valued gate of an accumulation tree is its root. Let t be
an odd gate of D that is not an output, with exactly one user g. Then a(t) = a(g) (no terminal), so by
Lemma 7.1 the origins of t and g have the same mask in C, hence are the same signal v (masks are distinct).
But t is the root of v's tree, and no gate of that tree consumes the root. []

---

## 8. The potential and the exclusion of 69, 70, 71 gates

**Definition.** For a normalized circuit C let e(C) be the number of its even+even gates with odd adjoint
(the e_1 of section 6). Then 0 <= e(C) <= y(C) <= G.

**Lemma 8.1 (P0).** e(T(C)) = sum_(v odd) f_v >= F_H.

*Proof.* The even+even gates of T(C) are the f_v even+even gates of the accumulation trees; by Lemma 7.1
such a gate has odd adjoint iff its origin v is odd. The helpers are among the odd signals. []

**Lemma 8.2 (one-step inequality, P1).** For every normalized minimum circuit C,

    e(T(C)) - e(C) >= s(C) + 96 - G + x(C) - 2 x(T(C)).

*Proof.* (B) with e_1 = e(C), h + y = G - 32 - x, and F_H <= e(T(C)). []

**The orbit.** Let C_0 be a minimum circuit (of M or M^T) attaining Y, and C_(j+1) = T(C_j) with any
canonical choices. All C_j are minimum circuits (Lemma 3.1), alternating in orientation; by Lemma 7.2
x(C_j) alternates between a = x(C_0) and b = x(C_1).

**Lemma 8.3 (two-step drift).** e(C_(j+2)) - e(C_j) >= s(C_j) + s(C_(j+1)) + 192 - 2G - a - b. If the
right-hand side is >= 1 for every j, then e is unbounded, which is impossible.

**Proposition 8.4.** L(M) is not 69, 70 or 71.

*Proof.* Let G be one of these values. By Lemma 5.1 and x >= 24: 24 <= a <= G - 45. Write t = h(C_0) + Y
= G - 32 - a. From (4.1) and (3.2) at C_0, 2 F_H >= 32 - Y + s - 3h, so Y - F_H <= floor((3t - 32)/2).
Since y(C_1) = F >= F_H and h(C_1) + Y >= 13, b = G - 32 - F - h(C_1) <= G - 45 + Y - F <=
G - 45 + floor((3t - 32)/2). For every iterate D, (4.4) with h + y = G - 32 - x and y >= 0 gives
max(s, C(s, 2)) >= z + C(q, 2) >= 96 - 2G + 2 x(D). Let m_G(x) be the least s with max(s, C(s,2))
>= 96 - 2G + 2x. Then every two-step drift is at least m_G(a) + m_G(b) + 192 - 2G - a - b. A finite
enumeration over all admissible (a, b) (4 pairs at G = 69, 12 at G = 70, 23 at G = 71) shows this is at
least 13, 9 and 3 respectively (program `check72.py`). By Lemma 8.3, contradiction. []

---

## 9. The steady regime and the exclusion of 72 gates

**Lemma 9.1.** In the orbit of section 8, y(C_(2j)) = Y for all j, and y(C_(2j+1)) is nondecreasing, hence
eventually equal to a constant V <= Y. In the *tail* (all j large) the count profiles are therefore fixed:

    even phase: (x, y, h) = (a, Y, h_e),  h_e = G - 32 - a - Y,   F = y(next) = V;
    odd phase:  (x, y, h) = (b, V, h_o),  h_o = G - 32 - b - V,   F = y(next) = Y.

Both phases are canonical transposes, so Lemma 7.4 applies to both.

*Proof.* Lemma 7.3 and the maximality of Y give y(C_(2j)) >= y(C_(2j-2)) >= ... >= Y >= y(C_(2j)); the odd
subsequence is nondecreasing and bounded by Y. []

**Proposition 9.2.** L(M) != 72.

*Proof.* Let G = 72 and take the tail. The scalar constraints are: 24 <= a <= G - 45, 24 <= b, 0 <= Y <=
G - 32 - a, 0 <= V <= min(Y, G - 32 - b), h_o + Y >= 13 (Lemma 5.1 at the odd phase). Lemma 4.3 at the two
phases gives s_e <= 3h_e + 2V + Y - 32 and s_o <= 3h_o + 2Y + V - 32, and (4.4) gives
max(s_e, C(s_e,2)) >= 96 - 2G + 2a + Y and max(s_o, C(s_o,2)) >= 96 - 2G + 2b + V. Let m(a, Y), m(b, V) be
the least s satisfying these; the two-step drift is at least m(a,Y) + m(b,V) + 192 - 2G - a - b. The program
`check73.py` enumerates every admissible tuple (1,010 pass the fan-out caps) and finds the drift positive
except for a = b = 24, Y = V = 0. In that case every circuit of the tail has y = 0, hence e = 0, and Lemma
8.2 gives 0 >= s at every iterate: q = z = 0. Take an iterate of orientation M^T: all 32 + h of its H-B
edges are represented (Lemma 4.2 with y = q = z = 0), giving 32 + h independent relations H_i + T (Lemma
4.4); every helper is anchored (degree >= 2, no H-H edges); choosing one relation per helper as a pivot and
adding it to the other relations of that helper leaves 32 independent boundary relations of weight 6. Their
span has dimension at most rho_6(M^T) = 28 (fact F5), a contradiction. []

**Finite fact F5 (weight-six relations).** A zero-sum subset of B of weight 6 is the union of two disjoint
boundary triples with equal XOR (weights 2 and 4 are excluded by F2). There are 60 such subsets for M,
spanning a space R_6 of dimension rho_6(M) = 20, and 84 for M^T, with rho_6(M^T) = 28.

---

## 10. Helper types and the local inequality system

From now on G is 73 or 74 and we work in the tail of Lemma 9.1. Fix one phase, with its parameters

    h (helpers), y (its even+even count), F (the even+even count of the next phase), q, z, and its orientation.

Every helper has a type (r, u, v) with 0 <= r <= 3 (Lemma 4.4), 0 <= u <= q, 0 <= v <= min(2z, h - 1)
(simplicity; v <= z would do), and r + u + v >= 3 when the phase is a canonical transpose (Lemma 7.4;
section 11 says where r + u + v >= 2 is used instead). Let n_(r,u,v) >= 0 be the number of helpers of each
type and put

    f_min(r, u, v) = max(0, floor((r + u + v - 3)/2)),

so that f_min <= f_v for a helper of that type (its fan-out is d_v = r + u + v - 1 and (3.2) holds). Define
the aggregates

    W = sum r u n,   A = sum_(r=3) u n,   Z = sum (r-1)_+ u n,   E = sum_(r=3) (u-2)_+ n,
    D0 = sum_(r=0) (u - 1) n   (this may be negative; helpers with r = u = 0 count -1).

**Lemma 10.1.** Every phase satisfies the following relations (the names are those of the checking program).

    (L1)  sum n = h
    (L2)  sum (r+u+v) n = 32 + h - y + q + z
    (L3)  sum v n = 2z
    (L4)  sum f_min n <= F                                       [reverse EE budget]
    (L5)  sum C(u,2) n <= C(q,2)                                 [missing pairs]
    (L6)  sum_(r=3) u n <= q                                     [full missing incidence]
    (L7)  W <= 7q                                                [label rank capacity]
    (L8)  sum_(r=3) (1 + 2 f_min) n <= 3h + 2F + y - 32          [full helper budget]
    (L9)  Z <= 3q                                                [weighted label capacity]
    (L10) sum (u + 2 f_min) n <= 4q + 2F                         [even signal fan-out]
    (L11) sum_(r=3) (u + v) n <= q + z                           [full helper incidence]
    (L12) sum (r-1)_+ n <= rho_6                                 [boundary rank six]
    (L13) W - 2 D0 <= 2y + 2z + 7q - 2 rho                       [quotient rank capacity]
    (L14) W + A - 2 D0 <= 2y + 2z + 7q - 2 rho + (2 if M, 0 if M^T)   [quotient full capacity]
    (L15) Z - D0 <= y + z + 3q - rho                             [quotient excess capacity]
    (L16) Z + E <= 3q                                            [full excess overflow]
    (L17) M:   2Z + 2E - 3 D0 <= 3y + 3z + 6q - 24;   M^T:  Z + E - 3 D0 <= 3y + 3z + 3q - 12  [coupled]
    (L18) M^T only:  W + A - 3 D0 <= 3y + 3z + 7q - 12           [strengthened full capacity]
    (L19) M^T only:  3 <= y + sum_(r=0) (u + v - 1) n + sum_(r=1) v n        [dark label rank]
    (L20) M^T only:  9 <= 3y + 2z + sum_(r=0) (3u + v - 3) n                [dark quotient rank]
    (L21) M^T, q = 0 only:  sum_(r=0) n >= 1;   (L22) M^T, q = 0 only:  3 <= y + sum_(r=0) (v - 1) n
    (L23) q = 6:  N3 + 3N4 + 4N5 + 4N6 <= 4;   q = 7:  2N3 + 7N4 + 12N5 + 14N6 + 14N7 <= 14,
          where N_j = sum_(u=j) n                                 [missing-label packing]

where rho_6 = 20 (M) or 28 (M^T) and rho = 32 - dim J = 8 (M) or 4 (M^T), with J the fixed space of
Lemma 10.2 chosen as in fact F9.

*Proof of (L1)-(L3).* Lemma 4.2 and the definition of v. []

*Proof of (L4).* sum f_min n <= F_H <= F, since F sums f over all signals of the phase and y(next) = F. []

*Proof of (L5), (L6).* Lemmas 4.6 and 4.5. []

**Finite fact F6 (label capacity).** For an even value l let C_l be the span of the formal vectors
E_l + sum_(b in D) B_b over all 2- and 4-element subsets D of B with XOR l (E_l is one extra coordinate).
Over all 637,392 such subsets, rank(C_l) <= 7 for every l; the rank histogram is 1: 578,900, 2: 18,032,
3: 5,846, 4: 778, 5: 200, 6: 108, 7: 10 for M and 1: 561,014, 2: 22,830, 3: 7,678, 4: 1,273, 5: 234,
6: 216, 7: 6 for M^T.

*Proof of (L7).* Fix a missing label l. For each helper i with an edge i-b_i of label l and each of its r_i
represented relations H_i + T, add the gate equation H_i + B_(b_i) + E_l: the result E_l + T + B_(b_i) lies
in C_l (T + {b_i} is a 2- or 4-subset with XOR l). These sum_i r_i vectors come from an independent family by
invertible operations (Lemma 4.4's family together with the missing H-B equations is a subset of the gate
equations after invertible operations), so they are independent and sum_(i meets l) r_i <= 7. Summing over
the q missing labels gives W <= 7q. []

**Finite fact F7 (weighted capacity).** For every potential label l, every full value h_3 with
h_3 + l in B, and every two further repeated values h_1, h_2 with h_1 + l, h_2 + l in B, and every choice
of two of the triples of h_1 and of h_2: the seven vectors E_l + T + B_b (three from h_3, two each from
h_1, h_2) are linearly dependent. There are 51,840 such configurations for M and 75,600 for M^T.

*Proof of (L9).* Fix a missing label l; the projected vectors of (L7) are independent of rank <= 7. If
sum_(i meets l, r_i >= 2) (r_i - 1) >= 4, then the incident helpers with r_i >= 2 contain either two full
helpers (excluded by Lemma 4.5), or one full and two with r_i = 2 (seven independent projected vectors,
excluded by F7), or four with r_i = 2 (eight independent vectors, exceeding rank 7). A helper with r_i >= 2
is a repeated value, so F7 covers every case. Hence the excess at each missing label is <= 3. []

*Proof of (L10).* A missing label l is the even signal of at most d_l + 1 <= 4 + 2 f_l gate equations
(its defining gate and its uses; (3.2)). Summing over missing labels, U <= 4q + 2 F_miss where F_miss sums
f over the missing even signals; F_miss + F_H <= F since helpers and even signals are disjoint. []

**Finite fact F8 (further full-helper incompatibilities).** (i) For two disjoint pairs of full values with
equal XOR, the twelve relation vectors have rank at most 10 (rank histogram 7: 180, 8: 720, 10: 288 for M;
7: 252, 8: 1,008, 10: 576 for M^T). (ii) For two full values with XOR l and a third full value in l + B,
the nine relation vectors have rank 8 (432 configurations for M, 864 for M^T).

*Proof of (L8) and (L11).* By Lemma 4.4 all represented relations of the circuit are independent, so none
of the configurations F4, F8(i), F8(ii) can occur among full helpers. Consequently, at a missing label l, at
most one "full event" occurs: an H-B edge at a full helper or an H-H edge with both ends full (two full H-B
incidences are adjacent by Lemma 4.5; two full-full H-H edges with label l are F8(i); one of each is
F8(ii)); and a represented label has no full-full H-H edge (its two ends would be adjacent). Let A_HH be the
number of full-full H-H edges, U_full = sum_(r=3) u and V_full = sum_(r=3) v. Then U_full + A_HH <= q and
V_full <= (z - A_HH) + 2 A_HH, so U_full + V_full <= q + z: this is (L11). For (L8), let
Delta = sum_(v in H) (3 + 2 f_v - d_v) >= 0; by (4.1), s + Delta + 2(F - F_H) = 3h + 2F + y - 32. At the
full helpers, d_v = 2 + u + v, so n_3 + 2 F_full = U_full + V_full + Delta_full <= q + z + Delta_full
<= 3h + 2F + y - 32, where F_full sums f over full helpers and Delta_full their part of Delta. Replace
f_v by f_min. []

*Proof of (L12).* Choose one represented relation at every anchored helper as a pivot and add it to the
other relations of that helper; the sum (r_i - 1)_+ modified relations are independent boundary relations
of weight 6, hence lie in R_6 (fact F5). []

**Lemma 10.2 (global elimination).** Call a missing label *dark* if it has no H-B edge at an anchored
helper, *bright* otherwise; let q_D be the number of dark labels, h_0 the number of unanchored helpers and
U_0 = sum_(r=0) u (so D0 = U_0 - h_0). For a missing label l let K_l be the span of the differences D + D'
of the 2- and 4-subsets of B with XOR l (a space of boundary relations of dimension rank(C_l) - 1). Let J
be any fixed space of boundary relations containing R_6 and put k_l = dim((K_l + J)/J). Then

    32 - dim J <= y + z + D0 - q_D + sum_(l bright) k_l.                              (G)

*Proof.* Retain every represented relation and every missing H-B gate equation at an anchored helper:
R + U - U_0 independent vectors (Lemma 4.4's argument). Pivot one represented relation at each of the
h - h_0 anchored helpers; the remaining represented relations become weight-6 boundary relations (in R_6)
and the remaining missing rows E_l + B_b + H_i become E_l + T + B_b, forms of label l. For each bright label
pivot one of its forms; the other forms of l become differences, i.e. elements of K_l. The residual
R + U - U_0 - (h - h_0) - (q - q_D) vectors are independent and lie in R_6 + sum_(l bright) K_l, whose
dimension is at most dim J + sum_(l bright) k_l. Substitute R + U = 32 + h - y + q - z. []

**Finite fact F9 (quotient table).** For M take J = R_6 + sum of all K_l with rank(C_l) = 7; dim J = 24.
For M^T take J = R_6, dim J = 28. The labels with k_l > 0 (*quotient-active*) and their (rank(C_l), k_l)
are: M: (2, 1) for 845 labels, (3, 2) for 44, (4, 1) for 1; M^T: (2, 1) for 102, (4, 1) for 1. For every
label, rank(C_l) + 2 k_l <= 7.

**Finite fact F10.** No quotient-active label meets a repeated helper value: for every active l and every
repeated value h, h + l is not in B.

**Finite fact F11 (full helpers at rank-7 labels).** For M^T, none of the six labels with rank(C_l) = 7
is h + b for a full value h and b in B. For M, exactly four of the ten rank-7 labels are of that form
(0x8181, 0x818100, 0x81000081, 0x81810000), each for exactly one full value (0x181, 0x18100, 0x81000001,
0x1810000), and for any three of these four values the nine relation vectors have rank 7.

*Proof of (L13)-(L15).* With W_l = sum_(i meets l) r_i: W_l <= rank(C_l) (proof of (L7)), W_l = 0 at a dark
label (all its incident helpers have r = 0), and rank(C_l) <= 7 - 2 k_l (F9). Summing over bright labels and
using (G): W <= 7(q - q_D) - 2 sum k_l <= 7q - 7 q_D - 2(32 - dim J - y - z - D0 + q_D); dropping the
nonpositive multiple of q_D gives (L13). For (L14), add A_l (1 if a full helper meets l): if A_l = 1 then
k_l = 0 (F10, full values are repeated) and rank(C_l) <= 6 except for the four M labels of F11, of which at
most two can meet full helpers simultaneously (three full helpers among the four values would carry nine
independent relations of rank 7); so W_l + A_l + 2 k_l <= 7 + ex_l with sum ex_l <= 2 for M and 0 for
M^T. For (L15): at a bright label the r_i - 1 differences T + T' at each incident helper with r_i >= 2 are
independent across helpers (they are differences within an independent family) and lie in K_l and in R_6,
so Z_l <= dim(K_l intersect J) = rank(C_l) - 1 - k_l; with Z_l <= 3 (L9) the table F9 gives Z_l + k_l <= 3
in every case. Sum and use (G). []

**Finite fact F12 (high-excess labels).** For each label l meeting at least one repeated value, the largest
sum_(i) (r_i - 1) over independent selections of r_i triples at the helpers i in (l + B) is at most 3; it
equals 3 for a set Q of 96 labels (M) or 192 labels (M^T). Every full value h has at most two labels of Q
among the 64 values h + b, b in B.

*Proof of (L16)-(L18).* Let q_L count the selected missing labels outside Q; Z <= 3(q - q_L) + 2 q_L =
3q - q_L. A full helper meets at most two Q labels, so at least (u_i - 2)_+ of its missing labels are outside
Q, and these labels are distinct across full helpers (Lemma 4.5): E <= q_L. Adding gives (L16). For the
coupled rows, the quotient-active bright labels have Z_l = 0 and meet no full helper (F10), so they are
disjoint from the labels charged for E; charging 3 for each of them, 3 for a Q label, and 2 (+1 if it pays
for E) for a low label gives Z + E + 3 n_act <= 3(q - q_D), where n_act is the number of active bright
labels. Since k_l <= 2 for M and <= 1 for M^T, n_act >= ceil(d/2) resp. d where d = sum_(bright) k_l
>= rho - y - z - D0 + q_D by (G). For M, 2Z + 2E + 3d <= 6(q - q_D) and substituting the bound on d gives
(L17, M); for M^T, Z + E + 3d <= 3(q - q_D) gives (L17, M^T). For (L18): in M^T an active label has
rank(C_l) <= 4 and A_l = 0, so W_l + A_l + 3 k_l <= 7 at every bright label; sum and substitute d. []

**Finite fact F13 (dark-label facts, M^T).** Let R_10 be the span of all zero-sum subsets of B of weight
<= 10; rho_10(M^T) = 29 (also rho_8(M^T) = 29; the weight-8, -10, -12 zero-sum subsets number 276, 1,300,
8,112, of which 736 weight-12 ones are nonzero modulo R_10). For an even value l let K6_l be the span,
modulo R_10, of the differences of the subsets of B of even size <= 6 with XOR l; every nonzero element
comes from a weight-12 word split into two 6-subsets of XOR l. dim K6_l is 1 for 193,172 values and 2 for
5,712 values (the *active* six-form labels), 0 otherwise. No active label is the XOR of a 2- or 4-subset of
B. An active label is the XOR of at most one pair of distinct repeated values (632 active labels are the
XOR of exactly one such pair).

*Proof of (L19), (L20).* Orientation M^T. Retain the B-B reference equations of all represented labels, the
represented H-B equations, the missing H-B equations at anchored helpers, and the H-H equations with two
anchored ends; this is a subset of the gate equations, hence independent. Pivot each represented label by
its reference, each anchored helper by one represented relation, and then one row for each missing label
that still occurs among the retained rows (q_A such labels). Let z_0 count the H-H edges with an unanchored
end. The residual rows number

    (x + y - q) + R + (U - U_0) + (z - z_0) - (x + y - q) - (h - h_0) - q_A = 32 - y + h_0 - U_0 - z_0 + (q - q_A),

are independent, and are boundary relations: extra represented relations have weight 6; an H-H row with a
represented label becomes T_i + T_j + B_b + B_c (weight <= 8); the rows of a missing label l are differences
of its forms, where an H-B form has size <= 4 and an H-H form (T_i + T_j) size <= 6. A difference involving
an H-B form has weight <= 10, so lies in R_10. Only missing labels all of whose retained rows are H-H forms
can contribute outside R_10, and their contribution lies in K6_l, of dimension <= 2 (F13). For such an
active label l, at most one retained H-H edge joins two repeated values (F13); choose it as the pivot of l
if present; every other retained edge of l then has an end of represented degree r = 1 (a helper with
r >= 2 is a repeated value). So the quotient contribution of l is at most the number of its retained H-H
edges touching an r = 1 helper, and in total at most z_1 = sum_(r=1) v. Hence
32 - y + h_0 - U_0 - z_0 + (q - q_A) <= 29 + z_1, and with q >= q_A, z_0 <= sum_(r=0) v this is (L19).
For (L20), bound the contribution of an active label with m retained H-H rows by min(2, m - 1) <= 2m/3
instead; sum_l m <= z - z_0; so 32 - y + h_0 - U_0 - z_0 <= 29 + 2(z - z_0)/3, which multiplied by 3 is
(L20). []

*Proof of (L21), (L22).* Orientation M^T with q = 0: every label is represented, so every residual row of
the elimination above lies in R_10 (weights <= 8): 32 - y + h_0 - z_0 <= 29, which is (L22). (L21) is
part of Lemma 10.3. []

**Lemma 10.3 (direct exclusions).** (i) No normalized circuit of either orientation has q = z = 0.
(ii) A canonical transpose of orientation M^T with q = 0 has at least four unanchored helpers and z >= 8.

*Proof.* (i) With q = 0, pivot every even signal by its B-B reference and every helper by a represented
relation (every helper is anchored: it has degree >= 2, no H-H edges, and every label is represented). The
G - (x + y) - h = 32 residual gate equations are independent boundary relations of weight <= 6 (an H-B
equation becomes T + B_a + B_b + B_c, an even+even equation the sum of three references), so they lie in
R_6, of dimension 20 or 28 < 32.
(ii) Let K be the set of unanchored helpers, k = |K|; with q = 0 they have only H-H edges. If k = 0, the
same elimination leaves 32 independent residual relations of weight <= 8 (an H-H row becomes
T_i + T_j + B_b + B_c), inside R_8(M^T) of dimension 29. If 1 <= k <= 3: each unanchored helper has degree
>= 3 (Lemma 7.4) and at most k - 1 <= 2 neighbours in K, so it has an anchored neighbour; pivot it by that
edge, which expresses it by <= 5 boundary elements. Every residual row then has weight <= 10 except the
rows of K-K edges (weight <= 12). Modulo R_10 (dimension 29), the classes of the K-K edge rows sum to zero
around every cycle of the graph on K (the pivot expressions cancel and the remaining labels' references have
weight <= 6), so they span at most k - c_K <= 2 dimensions (c_K the number of components of K); 29 + 2 < 32.
Hence k >= 4. Finally, for any normalized M^T circuit with q = 0: every component of the graph on K has an
edge to an anchored helper (every component of the odd graph contains an input, by the proof of Lemma 2.1
read on the graph: an odd+even gate attaches its result to its odd operand, so every odd signal is linked to
an input); choose a spanning forest of K plus one anchor edge per component (k edges) as pivots for the
unanchored helpers. Only z - k H-H rows remain unpivoted; every other residual row lies in R_6. So
32 <= rho_6 + (z - k) = 28 + z - k, i.e. z >= k + 4 >= 8. []

**Lemma 10.4 (packing rows).** (L23) holds.

*Proof.* The missing-label sets of the helpers with u >= 3 are subsets of a q-set pairwise intersecting
in at most one element (Lemma 4.6). q = 6: each element lies in at most two 3-sets, so N3 <= 4; at most one
set has size >= 4; with a 4-set every 3-set contains both outside elements, so there is at most one 3-set
(3 + 1 <= 4); a 5- or 6-set excludes all other sets of size >= 3 (weight 4 <= 4). q = 7: each element lies
in at most three 3-sets, so 2 N3 <= 14; one 4-set leaves three outside elements and every 3-set uses two of
them, with distinct pairs, so at most three 3-sets (7 + 6 <= 14); two 4-sets meet in one element, cover
everything and admit no further set of size >= 3 (14); a 5-set admits at most one 3-set (12 + 2); a 6- or
7-set stands alone (14). []

---

## 11. The exclusion of 73 and 74 gates

**The scalar domain.** With G fixed, the tail of Lemma 9.1 has parameters a, b, Y, V, h_e, h_o and the
constraints 24 <= a (hence a <= G - 45), 24 <= b <= G - 32, 0 <= Y <= G - 32 - a, 0 <= V <= Y, h_o >= 0,
h_o + Y >= 13. Upper bounds for the two s values:

    S_e = 3 h_e + 2V + Y - 32,       S_o = 3 h_o + 2Y + V - 32            (Lemma 4.3),

and at G = 74 also, from Lemma 8.2 with e(C) >= 0 and e(T(C)) <= y(T(C)),

    S_e = min(S_e, 2b - a + G - 96 + V),   S_o = min(S_o, 2a - b + G - 96 + Y).

Lower bounds: l(h, y) = the least s with 2h + y + max(s, C(s,2)) >= 32 (from (4.4)). A profile is
*admissible* if S_e, S_o >= 0, l(h_e, Y) <= S_e, l(h_o, V) <= S_o and l(h_e, Y) + l(h_o, V) <= a + b + 2G - 192
(otherwise Lemma 8.3 already excludes it). There are 262 admissible profiles at G = 73 and 1,102 at G = 74;
each has two *oriented claims* (the even phase is M or M^T).

**The local systems.** For a phase with parameters (h, y, F, q, z) and an orientation, the *local system*
consists of (L1)-(L12) over the types with r + u + v >= 2 at G = 73, and of (L1)-(L23) over the types with
r + u + v >= 3 at G = 74, in the unknowns n_(r,u,v) >= 0.

**Certificates.** Write a local system as A n <= b (each equality as two inequalities). A *certificate* is
a vector lambda of nonnegative integers with lambda^T A >= 0 in every coordinate and lambda^T b < 0: then
0 <= (lambda^T A) n <= lambda^T b < 0 for every real n >= 0, so the system has no solution. The files
`CERTIFICATES74.json` (484 certificates) and `CERTIFICATES75.json` (4,057 certificates, largest weighted
right-hand side -1) contain one certificate per excluded local system. They were found by a linear-programming
solver; the solver's output is not a premise, only the certificates are, and they are checked in exact
integer arithmetic.

**Coverage and the final test.** For each oriented claim the files state lower bounds k and l. The checker
verifies that every (q, z) with q + z < k on the even phase, and every (q, z) with q + z < l on the odd
phase, is excluded: by (4.4), by Lemma 10.3 (927 cases at G = 74), or by a certificate. It then verifies

    k > S_e   or   l > S_o   or   k + l > a + b + 2G - 192.

**Proposition 11.1.** L(M) is not 73 and not 74.

*Proof.* Let G be 73 or 74 and take the tail of the orbit. Its profile is admissible, so one of the oriented
claims applies. Every even-phase circuit of the tail satisfies its local system (Lemma 10.1, with
r + u + v >= 3 by Lemma 7.4 at G = 74), so its s is at least k; likewise s >= l at every odd phase. If
k > S_e or l > S_o there is no admissible s at all. Otherwise every two-step drift of Lemma 8.3 is at least
k + l + 192 - 2G - a - b >= 1, and e is unbounded. []

**Proof of the Theorem.** Corollary 5.2 gives L(M) >= 69; Propositions 8.4, 9.2 and 11.1 exclude 69
through 74. The 88-gate circuits of this repository are verified by `verify.py`. []

---

## 12. What the programs check, and what the argument must establish

| item | established by | checked by program |
|---|---|---|
| Lemmas 1.1-10.4, Propositions 8.4, 9.2, 11.1 (the argument) | the text above | no (stress tests only, section 13) |
| F1 no nine-part partition (both orientations) | finite enumeration | `checks/finite_facts.py` (and the bundle's `verify_bound63.py`, `audit67_check.py`) |
| F2 Sidon, F3 triple multiplicities, F5 rho_6 | finite | `checks/finite_facts.py`, `checks/check73.py` |
| F4, F8 full-value rank facts | finite | `checks/finite_facts.py` |
| F6 label capacities, F7 weighted capacity | finite | `checks/finite_facts.py` |
| F9-F12 quotient, active, rank-7 and high-excess labels | finite | `checks/finite_facts.py` |
| F13 dark-label facts, F14 rho_8(M^T) = rho_10(M^T) = 29 | finite | `checks/finite_facts.py`, `checks/check_dark_source.py` |
| the enumerations of Propositions 8.4 and 9.2 | finite | `checks/check72.py`, `checks/check73.py` |
| scalar domains, coverage and every certificate at G = 73, 74 | finite | `checks/certify74.py`, `checks/independent74.py`, `checks/certify75.py`, `checks/independent75.py` (two independent implementations each) |
| L(M) <= 88 | an explicit circuit | `verify.py` in this repository |

The programs compute numbers about the fixed matrix and check integer certificates. They do not, and
cannot, check that the inequalities (L1)-(L23) are necessary conditions for circuits, that the two-step
drift argument is sound, or that the tail of Lemma 9.1 exists: that is the mathematical content, sections
1-11, and it is what a reviewer must read.

---

## 13. Provenance and review record

*Provenance.* The argument (sections 1-11) was produced in September 2026 with large-language-model
assistance under the author's direction, in successive steps (bounds 63, 67, 69, 70, 72, 73, 74, 75, each
with its own documents and checkers, kept in the method repository `slp-plateau-search`). The Farkas
multipliers were found with an LP solver. This note consolidates those documents into one argument; the
numbered rows and finite facts are the ones the shipped checkers implement.

*Review.* All reviews so far were performed by programs and by machine reviews (language-model agents
working with their own code), never by a human mathematician. (a) 2026-09-23: three adversarial reviews (mathematics; recomputation
of every finite premise from scratch; stress tests on 14,000 circuits and 1.35 million local rewrites), all
clean. (b) 2026-10-01: a from-scratch recomputation of every finite fact (`checks/finite_facts.py`: all
numbers identical, the nine-part search with the same node and leaf counts); every identity and every row of
section 10 tested on 24,628 real circuits with their canonical and second transposes (`checks/stress.py`:
zero violations); an independent linear-programming model written from this text that regenerates every
one of the 2,204 oriented claims at G = 74 with the same bounds k, l (`checks/lp_regen.py`); mutation tests
of the certificate checker (every corrupted row constant, certificate or claim is rejected); and a further
adversarial review that re-derived every lemma, recomputed every finite fact with a differently structured
search, and ran 345,674 circuit states and 6,200 random small circuits of random matrices with no violation.
The method repository records all of it.

*What would refute this note.* A normalized minimum circuit of M or M^T violating one of (L1)-(L23) or
(4.4), or a counterexample to Lemma 7.3 or 7.4; the stress tests above looked for exactly that.

---

## 14. Reproduction

From the folder `lower_bounds/` of this repository (Python 3 standard library only; the optional LP cross-check
`lp_regen.py` needs numpy and scipy and is run only with `--with-lp`). The runner stops at the first failing
check and exits nonzero; a green run ends with `ALL CHECKS PASSED`.

    sh checks/run_all.sh                    # every check below except the LP cross-check (about 2 minutes)
    sh checks/run_all.sh --with-lp          # the same plus lp_regen.py

Script by script (each exits nonzero on failure):

    python3 checks/finite_facts.py          # every finite fact F1-F14; ends with ALL FINITE PREMISES RECOMPUTED AND MATCH (about 35 s)
    python3 checks/check72.py               # Proposition 8.4 enumeration (4, 12, 23 pairs; minimum increments 13, 9, 3)
    python3 checks/check73.py               # Proposition 9.2 enumeration (1,010 tuples, unique zero-drift tuple) and rho_6(M^T) = 28
    python3 checks/check_dark_source.py     # weight <= 12 zero-sum subsets (84, 276, 1300, 8112), rho_10 = 29, 736 words
    python3 checks/certify74.py             # G = 73: 262 profiles, 524 claims, 484 certificates, all checks passed
    python3 checks/independent74.py         # the same, second implementation
    python3 checks/certify75.py             # G = 74: 1,102 profiles, 2,204 claims, 4,057 certificates, largest rhs -1
    python3 checks/independent75.py         # the same, second implementation (9,604 references, 927 direct)
    python3 checks/stress.py                # identities and rows on the repository's circuits; ends with STRESS TEST PASSED
    python3 checks/lp_regen.py              # optional: regenerates the G = 74 claims with an LP (numpy, scipy); ends with LP CROSS-CHECK PASSED
    python3 ../verify.py                    # the 88-gate upper bound

Expected outputs are recorded in `checks/EXPECTED_RESULTS.md`.

---

## Appendix A. The finite facts in numbers

| fact | M | M^T |
|---|---|---|
| F1 graph-code words of weight 6 / 8 | 84 / 276 | 60 / 248 |
| F1 nine-part search: states / final checks / partitions | 1,485,213 / 62,112 / 0 | 91,485 / 720 / 0 |
| F2 distinct boundary pair XORs | 2,016 | 2,016 |
| F3 values with 1 / 2 / 3 boundary-triple representations | 40,704 / 360 / 80 | 40,320 / 504 / 112 |
| F4 adjacent full pairs (rank 5) / non-adjacent (rank 6) | 360 / 2,800 | 504 / 5,712 |
| F5 weight-6 zero-sum subsets / rho_6 | 60 / 20 | 84 / 28 |
| F6 labels of capacity 1..7 | 578,900 / 18,032 / 5,846 / 778 / 200 / 108 / 10 | 561,014 / 22,830 / 7,678 / 1,273 / 234 / 216 / 6 |
| F7 (3,2,2) seven-row configurations, all dependent | 51,840 | 75,600 |
| F8 (i) rank histogram of twelve rows; (ii) nine rows of rank 8 | 7: 180, 8: 720, 10: 288; 432 | 7: 252, 8: 1,008, 10: 576; 864 |
| F9 dim J; active labels (capacity, k) | 24; (2,1) 845, (3,2) 44, (4,1) 1 | 28; (2,1) 102, (4,1) 1 |
| F10 active labels meeting a repeated value | 0 | 0 |
| F11 rank-7 labels meeting a full value | 4 (one full value each; any three: rank 7) | 0 |
| F12 labels with excess 1 / 2 / 3; max Q labels per full value | 17,736 / 4,604 / 96; 2 | 24,186 / 6,388 / 192; 2 |
| F13 zero-sum subsets of weight 8 / 10 / 12; rho_8, rho_10; weight-12 words nonzero mod R_10 | (248 / 1,476 / 10,216; 32, 32; not used) | 276 / 1,300 / 8,112; 29, 29; 736 |
| F13 six-form labels with dim K6 = 1 / 2; active labels meeting a repeated pair | not used | 193,172 / 5,712; 632 (none meets two) |

## Appendix B. Notation

| symbol | meaning |
|---|---|
| G, L(M) | gate count of a circuit; minimum gate count |
| x, y, h | odd+odd gates, even+even gates, odd non-output gates (helpers) |
| B, H | the 64 boundary signals (inputs and outputs); the h helpers |
| d_v, k_v, f_v | fan-out (with terminal); odd contributions in the adjoint sum; max even+even gates of the accumulation at v |
| F, F_H | sum of f_v over all signals (= y of the canonical transpose); over helpers |
| T(C) | a canonical transpose of C |
| a(v), a_v | adjoint of v; its parity |
| q, z, s | missing labels; H-H edges; q + z |
| (r, u, v) | helper type: represented H-B edges, missing H-B edges, H-H edges |
| Y, V, a, b | the global maximum of y; the odd-phase y in the tail; the two alternating x counts |
| e(C) | even+even gates with odd adjoint (the potential) |
| W, A, Z, E, D0 | the aggregates of section 10 |
| R_6, R_8, R_10, rho | spans of zero-sum boundary subsets of weight <= 6, 8, 10 and their dimensions |
| C_l, K_l, J, k_l | label forms, their differences, the fixed quotient space, the quotient rank of a label |
