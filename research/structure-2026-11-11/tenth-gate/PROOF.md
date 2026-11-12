# The ten-gate sheet lemma by hand

Main agent, 2026-11-12. Status: **proposed proof, under independent machine review** (see the end of
this file for the review outcome when available). It is meant to replace the computer check that
`RECORD.md` section 7 and everything depending on it (Theorems 7.1, 7.2, 9.1, 9.2) currently rest on.

## Statement

Blocks a and b have four inputs each. *Base signals:* the four unit vectors b_0..b_3 of block b, and
every vector supported on block a (zero included), all at no cost. A *local circuit* is a sequence of
gates, each the XOR of two operands taken among base signals and earlier gates. Nothing is assumed
distinct or nonzero. Write a value as (beta | alpha), beta its part on b, alpha its part on a. With
E_c = (all of b except b_c) and s_c = a_c + a_(c+1) (indices mod 4), the targets are t_c = (E_c | s_c),
c = 0..3.

**Lemma.** A local circuit containing four gates with the values t_0..t_3 has at least 10 gates.

## The reason in one paragraph

Count the gates in two groups: the tau *entry gates* (one operand is a free vector) and the rest. Mirror
the circuit (transposition): the rest becomes a circuit T on four inputs that computes the four
triple-sums of its inputs, and each entry gate leaves a trace in T: a signal of T equal to the set of
targets that entry influences. The a-parts of the targets force these traces to span all even-weight
vectors. Three entries can do that only if the traces are three independent even vectors, so T would
contain three even signals; but a circuit that computes the four triple-sums with six gates has room for
only two signals besides the four outputs, and the outputs and inputs are odd. So either a fourth entry
(6 + 4) or a seventh mirrored gate (7 + 3).

## Proof

**Step 0 (cleaning; cannot increase the number of gates).** Fix one gate g_c for each target. Delete
every gate that is not g_c or an ancestor of some g_c. If both operands of a gate are free vectors its
value is free: delete it and let its readers read that free vector; repeat. Now every gate has at most
one free operand. Call the gates with exactly one free operand *entry gates*, eps_1..eps_tau, with free
operands phi_1..phi_tau (vectors on a; repetitions and zero allowed).

**Step 1 (formal inputs).** Replace the free operand of eps_i by a new formal input z_i. This gives an
ordinary circuit C on the inputs b_0..b_3, z_1..z_tau with the same K gates, in which each z_i is read
exactly once. Every gate g has a formal mask (beta(g) | n(g)) with n(g) in F_2^tau, and its value in the
local circuit is (beta(g) | Phi n(g)), where Phi is the linear map sending the i-th unit vector to phi_i.
For the targets: beta(g_c) = E_c and Phi l_c = s_c, where l_c := n(g_c).

**Step 2 (what the a-parts force).** Let zeta_i in F_2^4 be the vector whose c-th coordinate is the i-th
coordinate of l_c ("which targets does entry i influence"). If a set I of targets has
sum over c in I of l_c = 0, then applying Phi gives sum over c in I of s_c = 0, so I is empty or all four
(the s_c have rank 3 with the single relation s_0 + s_1 + s_2 + s_3 = 0). Hence the 4 x tau matrix with
rows l_c has left kernel inside {0, 1111}, so its column space, which is the span of the zeta_i,
contains the orthogonal complement of 1111:

    span(zeta_1, .., zeta_tau) contains every vector of even weight.                          (*)

In particular tau >= 3, and if tau = 3 then zeta_1, zeta_2, zeta_3 are three independent vectors of even
weight.

**Step 3 (mirror).** In C every signal is read at least once (the b_c because every target but one
involves b_c; the gates by Step 0), the four g_c have in addition a terminal use, and each z_i is read
exactly once. Transpose C as in PROOF Lemma 3.1: attach a variable w_c to the terminal use of g_c and
define the adjoint a(v) of every signal v as the XOR of the adjoints of its readers, plus w_c if v = g_c.
Building a(v) from its d_v contributions takes d_v - 1 gates, so the resulting circuit T on the inputs
w_0..w_3 has

    sum over signals v of (d_v - 1) = (2K + 4) - (4 + tau + K) = K - tau   gates,

and every a(v) is the mask of a signal of T (an input, a gate, or a wire equal to another signal). By
linearity a(v) lists the targets whose formal mask contains v, so
- a(b_c) = sum of w_c' over c' != c: the four triple-sums of the inputs of T, call them E_c(w);
- a(z_i) = zeta_i, and since z_i is read only by eps_i, a(z_i) = a(eps_i).
So T is a circuit on four inputs with K - tau gates among whose signals are the four vectors E_c(w) and
the tau vectors zeta_i.

**Step 4 (six gates leave room for two even signals).** The inputs of T have weight 1 and the E_c(w)
weight 3, all odd; the E_c(w) are four distinct non-input vectors, so four distinct gates of T carry
them. *T has at least 6 gates:* an odd vector is the sum of an odd and an even vector, and every even
signal of T is a gate, so T has an even gate; suppose it has only five gates, i.e. exactly one even gate
v besides the four E_c(w). The first gate of T adds two inputs, so v = w_i + w_j. Each E_c(w) is v plus an
odd signal. Adding an input w_k gives the two triple-sums that contain both i and j. The other two,
E_i(w) and E_j(w), differ by v, so each would have to be made from the other: impossible.

**Step 5 (count).**
- tau >= 4: K = (K - tau) + tau >= 6 + 4 = 10.
- tau = 3: the three zeta_i are independent even vectors, hence nonzero and not inputs, so they are the
  masks of three distinct gates of T, none of which carries an E_c(w) (those are odd). T has at least
  3 + 4 = 7 gates and K >= 7 + 3 = 10.
- tau <= 2 is excluded by (*).  QED

Both cases are attained: the recorded 10-gate schemes have 3 entries and 7 mirrored gates.

## What the proof shows about the earlier "6 + 3" count

The hand count "six gates for the b-parts, three entries for the a-parts" treats the two requirements as
independent. They are not: with three entries, each entry must influence an even set of targets, and
those three sets must be visible as signals of the mirrored circuit. A six-gate mirrored circuit is
rigid (four outputs and two pair-sums), and two pair-sums cannot be three independent even vectors.

## A general form (same proof)

**Duality lemma (free side).** Let the targets be t_c = (p_c | q_c), c = 1..r, with p_c in F_2^B (a block
whose unit vectors are base signals) and q_c in F_2^A (a block all of whose vectors are free). Let P be
the r x |B| matrix of the p_c (no zero column) and Q the r x |A| matrix of the q_c. Then the least number
of gates of a local circuit containing the targets equals the least value of

    (number of gates of T) + tau

over circuits T on r inputs w_1..w_r that compute the columns of P (as vectors over the w) and lists
zeta_1..zeta_tau of masks of signals of T whose span contains the row space... more precisely the
orthogonal complement of the left kernel of Q.

Only the inequality ">=" is proved above (Steps 0-3 use nothing about E and s); the reverse inequality
is expected by transposing back but is not needed and not claimed here.

**Corollary (a sheet with nothing free costs exactly 12; proved by hand).** The 8-input, 4-output map
with rows (E_c | s_c) has no zero row or column, so its minimum is that of its transpose plus 8 - 4
(PROOF Lemma 3.1 and its count). The transpose has 4 inputs and the 8 outputs E_c(w) and
w_c + w_(c-1): eight distinct non-input vectors, so at least 8 gates, and 8 suffice (the four adjacent
pair-sums, then each triple-sum as a pair-sum plus an input). Hence 8 + 4 = 12. (The earlier computer
runs had only shown "at least 11".)
