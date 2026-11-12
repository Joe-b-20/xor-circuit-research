# Chains of adjacent sheets: nine gates per further sheet, the tenth open

Report of the delegated investigation of 2026-11-12, saved by the main agent from the investigator's
final message. Machine work. The main agent re-derived Lemmas 1 and 2 and Theorem 1 (they repeat, at
the last level of a chain, arguments that were machine-reviewed for the pair); the description of what
a 29 must look like (section 3) and the partial results on the missing lemma (section 4) have NOT been
checked by anyone else. No SAT and no search; the two programs verify the mirror form on recorded
circuits and test inequalities on perturbed ones, which proves nothing universal.

Dependency: the pair theorem (`../pair/PROOF.md`, 20 gates).

## 1. Mirror form (proved; checked by program on recorded circuits)

Chain of l sheets: blocks a, b_1..b_l; every vector on a free; targets (E_c on b_k) + (s_c on b_(k-1)),
b_0 = a. Cleaning, formal inputs and transposition give K = |T| + tau with
|T| = (2K + 4l) - (4l + tau + K) = K - tau, where T is a circuit on l groups w^1..w^l of four inputs
containing (E_i on w^k) + (p_i on w^(k+1)) for k < l and E_i on w^l, and tau signals spanning a space
containing Even(w^1) + 0. M_l := the minimum of |T| + tau. M_1 = 10, M_2 = 20.
`chain3.py` confirms the form on 3131 mirrors (every run of three sheets of 13 recorded rotation
circuits, 31 accumulation orders each); all have K = 30 and no exits.

## 2. Peeling the last group (proved)

Take T reduced (no zero gate, no repeated value). Write a signal as (omega | s), omega its part on
groups 1..l-1, s its part on w^l. Fibres, first gates (f), duplicates (D), pure gates (N: omega = 0),
entries (e) and labels as in pair/PROOF.md.

**Lemma 1: f + tau >= M_(l-1).** A first gate has two operands with nonzero omega in different fibres.
Replacing operands by fibre roots gives a circuit R on groups 1..l-1 with f gates containing every
occurring omega, hence the 4(l-1) required vectors of the shorter chain (the vectors of level l-1
project to E_i on w^(l-1)). The exports project to signals of R spanning a space containing
Even(w^1) + 0.

**Lemma 2: D + N >= 9.** The s-parts of the signals with omega != 0 lie in the span of the labels and
include the p_i, so e >= 3, and D >= e. N >= 4 (the E_i on w^l). Nonzero even labels are further pure
gates. If e = 3: three distinct even labels, N >= 7, D + N >= 10. If e >= 4: D, N >= 4, and D = N = 4 is
impossible by the tree argument of sharing/REPORT.md Lemma 3.2 (the earliest triple-sum is a path of
three unit labels; the fourth label must be the remaining unit; then every 3-subset of four forest
edges would be a path).

**Theorem 1 (proved given M_2 = 20).** M_l >= M_(l-1) + 9. Hence M_3 >= 29 and M_l >= 9l + 2 for l >= 2.

## 3. What a 29 must look like (investigator's derivation; unreviewed)

K = 29 forces f + tau = 20 (first two groups) and D + N = 9 at the last group. Then:
- Five entries are excluded: D = 5 all entries, N = 4 is configuration (X) of the pair proof, whose tree
  argument uses only the last level.
- So e = 4, the labels are a basis with o odd ones, and one of
  (Z') (D, N) = (4, 5), o >= 3, the fifth pure gate even;
  (Y') (D, N) = (5, 4), one non-entry duplicate h, every triple-sum of the last group an exit, all four
  labels units.
- One level up (Lemma A and Lemma B of the pair proof): the gates with omega != 0 are a local circuit
  with w^3 free; its mirror T* is itself a mirror-form pair circuit which, by Lemma B, contains four
  distinct nonzero pure even vectors; so its first group has at least 8 first gates and |T*| >= 17.
  In (Z'): tau = 3, f = 17 = |T*|, every gate clean. In (Y'): tau is 3 or 4, f = 20 - tau, |T*| <= 18.
- With the first-group peeling: if no gate with zero first part is a long level-1 exit, K >= 30. So a 29
  needs a long level-1 exit and (Y') or (Z') at the same time. No contradiction was derived from the
  conjunction.

## 4. The missing lemma (conjectured)

**Lemma C_l.** In a reduced mirror-form circuit for l sheets with D + N = 9 at the last group,
f + tau >= M_(l-1) + 1. With it, M_l = 10 l.

A sufficient piece, **L18** (conjectured): a circuit on (y | x) containing (E_j(y) | q_j(x)),
(0 | E_j(x)) and four distinct nonzero vectors (z | 0), z even, has at least 18 gates. Proved towards
it (unreviewed): at least 17; a 17 is again (Y')- or (Z')-shaped one level down; the sub-case (4,5)
with four odd labels is impossible. Open inside L18: (4,5) with three odd labels, and (5,4) with a
clean h.

**Why the pair method does not supply it.** For l = 2 the mirror T* has four inputs and eight
prescribed distinct vectors: counting gives |T*| >= 8 and at equality every signal of T* is known,
which forbids stacked entries. For l = 3, T* is a 17- or 18-gate pair circuit with only twelve
prescribed vectors: counting gives nothing, its bound comes from the pair theorem, and the residual
cases of that theorem reappear inside T*. Each level of the recursion T, T*, T** returns the same
residual with one unit less slack; that is the gate lost per level. A closed induction seems to need a
two-sided statement (a chain with four distinct pure even signals required in the first group and
odd-label entries at the last), since T* inherits a condition at each end.

## 5. Observed (proves nothing)

`chain3_perturb.py`: 600 randomly perturbed valid chain-of-three circuits (36 with last-group exits, 50
with level-1 exits, 99 with non-entry duplicates): all the inequalities above hold, the smallest
|T| + tau is 30, and D + N was never below 10.

## 6. Files

chain3.py, chain3_perturb.py.
