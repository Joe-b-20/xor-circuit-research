# Direct sums of XOR circuits: literature and theory

Report of the delegated investigation of 2026-11-12, saved by the main agent from the investigator's
final message. Machine work; no human review; no second machine review yet. No SAT, no exhaustive
search. Status words: **proved**, **conditional**, **conjectured**, **observed**, **disproved**,
**literature [level]**, with level S (read in the source), S-ocr (read in the source through garbled
OCR), W (read on the author's web page via a fetch summary), 2 (secondary citation), R (recalled, not
verified).

Model: A acts on input set X, B on input set Y, A + B block-diagonal; L = least number of 2-input XOR
gates, unbounded depth and fan-out, cancellation allowed.

**Review (`../review-phase2/REVIEW.md`).** Section 2 is confirmed (Theorem 2's proof, missing here, is
supplied in the review; Lemma 3(c) needs one extra sentence). Literature: the two Jukna notes and Find
et al. were confirmed from the pages; the first note credits only "Igor" (the attribution to Sergeev is
an inference) and does not itself say "unbounded depth" (that follows from the depth-2 additivity in
the second note).

## 0. Summary

**Known.** L(A + B) = L(A) + L(B) is **false** for XOR circuits of unbounded depth, but only
existentially: a fast matrix-multiplication algorithm computes n copies of A (I_n (x) A) with O(n^2.81)
gates, while a typical n x n matrix has L(A) ~ n^2 / (2 log n). No explicit or small counterexample is
known; by the investigator's computation the counting argument certifies a failure only at n about 2^37.
Additivity does hold for depth-2 XOR circuits, SUM and OR circuits, monotone Boolean circuits, and
cancellation-free XOR circuits.

**Proved here** (every circuit, every A unless stated): a gate-count identity; N_X >= L(A) (a partner can
never let A use a smaller cyclic system); a span lemma bounding the gates that are new on both sides;
additivity whenever one part has helper count h <= 3 (this covers every part with at most 4 inputs);
L(A + B) >= L(A) + n_B - c_B; a floor for any counterexample (both parts with h >= 4, at least 5 inputs,
at least 3 nontrivial rows, joint size at least 13).

## 1. Literature

**1.1 Unbounded-depth XOR: additivity refuted, existentially.**
- Jukna web note "On XOR complexity of direct sum of matrices" (22.05.2015, credited to Sergeev) [W]:
  take A n x n with XOR(A) ~ n^2/(2 log n) (exists by counting). If additivity held then
  XOR(I_n (x) A) >= n XOR(A) = Omega(n^3 / log n). But y = (I_n (x) A) x is Y = AX with X an n x n
  variable matrix, and Strassen's algorithm over GF(2) with A fixed is a linear circuit with O(n^omega)
  gates.
- Jukna note "Problem 7.7 solved" (04.06.2017) [W]: depth-2 additivity combined with the above gives a
  gap between depth-2 and unbounded-depth XOR complexity; the argument was "told to Wolfgang Paul by an
  anonymous referee" (Paul 1976, Corollary 2).
- W. J. Paul, TCS 2 (1976) 383-396 [S-ocr]: for every eps there are arbitrarily complex f with
  C(f x f) <= (1 + eps) C(f), general Boolean circuits; cites Fischer for additivity of monotone circuits.
- Find, Goos, Jarvisalo, Kaski, Koivisto, Korhonen, "Separating OR, SUM, and XOR circuits"
  (arXiv 1304.0513) [S]: x -> (I (x) A) x "famously admits non-trivial" XOR circuits because fast matrix
  multiplication is a small bilinear circuit over GF(2); for OR circuits the cost is exactly n times.
- Size of the certificate (threshold.py, computed by the investigator): n = 2^37 with Strassen-Winograd
  recursion and a naive base.

**1.2 Jukna-Sergeev, "Complexity of Linear Boolean Operators", FnT TCS 9(1), 2013** [S]: L(A + B) <=
L(A) + L(B); Theorem 3.18 (SUM and OR circuits: additivity with an extra rank term for block-triangular
matrices), with the remark that no analogue is known for XOR circuits, even in depth 2; equation (3.8):
depth-2 additivity for SUM, OR and XOR (measured in wires), which fails above depth 2 for OR. The 2013
text does not mention the failure of XOR additivity.

**1.3 Other models.** SUM and OR circuits: additive [S]. Cancellation-free XOR circuits: additive (easy
consequence). Monotone Boolean circuits: additive (Fischer, cited in Paul) [S-ocr]. General Boolean
circuits: mass production (Uhlig 1974; Paterson 1992) [2]. Depth >= 3 XOR: nothing found.

**1.4 Tensor rank.** Strassen's additivity conjecture (1973) concerns tensor rank, which counts bilinear
multiplications and makes additions free: the opposite measure. Shitov (Acta Math. 222, 2019) refuted it
over infinite fields [W]; finite fields open. Neither failure implies the other; the one link runs one
way: a low-rank algorithm for matrix multiplication gives XOR savings for I_n (x) A.

**1.5 Sergeev (Math. Notes 118:4, 2025)** [abstract only]: 5n - o(n) for an explicit matrix; "direct sum
of matrices" appears among the keywords; how it is used was not seen.

## 2. Theory

**Setting.** Signals s = (s_X, s_Y). The X-part of a gate is *new* if it is not in {0, X-units, X-parts
of earlier gates}; likewise Y. N_X, N_Y: gates with a new X-part, a new Y-part. d: gates new on both
sides; w: gates new on neither. *Mixed*: both parts nonzero. m*_B: number of distinct rows of B of weight
>= 2; h_B = L(B) - m*_B, the helper count.

**Lemma 1 (projection; proved).** N_X >= L(A) for every circuit for A + B. (The gates with a new X-part,
in order, form a circuit for A.)

**Lemma 2 (gate count identity; proved; checked on 20,000 random circuits).** G = N_X + N_Y - d + w. With
H the bipartite graph with one vertex per distinct X-part and per distinct Y-part and one edge per
signal: G = N_X + N_Y - (c - 2) + beta, c and beta the components and cycle rank of H. Every saved gate is
a *floating* component of H: it consists of mixed signals only, none of its values is ever carried by a
pure signal, and none is an output.

**Lemma 3 (where mixed signals come from; proved).** (a) A gate new on both sides has two mixed operands
with distinct X-parts and distinct Y-parts. (b) The first mixed gate is a "mixer": a nonzero pure-X
operand plus a nonzero pure-Y operand; it is new on neither side. (c) **Span lemma.** Let Omega_mix be the
mixed gates that are not X-new. Every mixed signal has its Y-part in the span V of the Y-parts of the
Omega_mix gates so far. Hence d <= 2^r - r - 1 with r = dim V. The bound is attained (3 mixers plus their
4 subset sums give d = 4).

**Theorem 1 (proved).** Let s = L(A) + L(B) - L(A + B). If s > 0 then 2^(h_B - s) >= h_B + 2, that is,
s <= h_B - ceil(log2(h_B + 2)). The same holds with h_A.
*Proof.* In an optimal circuit the gates that are not X-new are one first-occurrence pure gate (0, B_r)
for each distinct row of weight >= 2, and the rest, Omega; so G = N_X + m*_B + |Omega| and
|Omega| <= h_B - s. From Lemma 2, d >= s + w, and w >= 1 by Lemma 3(b). Lemma 3(c) gives
s + 1 <= 2^r - r - 1 with r <= |Omega| <= h_B - s. QED

**Corollaries (proved).** Additivity holds if L(B) <= m*_B + 3; every B with at most 4 inputs qualifies;
L(I_k (x) A) = k L(A) when h_A <= 3. The cyclic examples 1 and 2 of ../cyclic/REPORT.md (h = 1, 2) are
additive with every partner.

**Theorem 2 (proved).** L(A + B) >= L(A) + n_B - c_B, n_B the number of inputs of B met by rows of weight
>= 2 and c_B the number of components of the hypergraph those rows form. Additivity follows for
forest-computable B, for example any B with at most two nontrivial rows.

**Corollary (floor for a counterexample; proved).** Both parts must have h >= 4, at least 5 inputs, at
least 3 nontrivial rows, and must not be forest-computable; then L(A + B) >= 13.

**Theorem 3 (proved, easy).** If no mixed signal is an ancestor of an output, then G >= L(A) + L(B).

**Costs of mixing and of separating.** Each independent mixing direction costs a gate useless for A's
projection and charged against B's helper budget; the gain from r directions is at most 2^r - r - 1 gates
new on both sides. A gate that turns a mixed signal pure is either (i) mixed + pure signal of the other
side: new on neither side, so it costs a gate; or (ii) two mixed signals with equal foreign parts: free
in the count, but it needs a linear coincidence.

**The cyclic route (disproved as stated).** Lemma 1 holds whatever B does, so no partner can supply A's
"missing first step"; the only lever is d > w.

**How the known failure works** (strassen_ds.py: one Strassen-Winograd level for A + A with naive block
circuits, verified on random A; an illustration, not a counterexample, since neither circuit is
optimal): at n = 64, 3,724 gates against 3,990 for two naive copies; 32 mixers; all 96 separations are of
type (ii), produced by identities among the Strassen sums. The mixing overhead is O(n) per level against
a saving of order n^2 / log n, which pays only when the blocks are far more complex than their dimension.

**Two copies and unrelated pairs (from Nechiporuk's asymptotic plus counting; the investigator's own
derivation, not found published).** L(A + A) <= (7/8 + o(1)) 2 L(A) for almost every large A; random
unrelated pairs are additive to first order. So savings need shared structure between the parts.

## 3. Near direct sums (chains, cycles, triangle)

1. For window W_j = {j-1, j} with the neighbour block free, call a gate j-new if its restriction to W_j
   is new and nonzero on block j. These gates form a circuit of the local problem, so their number is at
   least the local minimum, with no ancestry needed; hence G >= sum of local minima - sum over gates of
   (nu(g) - 1)+, nu counting the windows for which g is new. (Proved.)
2. Disjoint windows: zeroing all other blocks yields a genuine direct sum of run maps; Theorem 1 does not
   bite there because their helper counts are too large. (The sheet-with-free-neighbour version is
   settled by ../sharing/INDEPENDENT-SHEETS.md.)
3. Adjacent windows: the mixer [j: u] + [j+1: v] is new for no window in a direct sum, but in a chain it
   is a translation entry of part j+1, since block j is free in part j+1's local problem. So the span
   lemma has no analogue: the mixing directions are paid by gates the neighbour needs anyway. The cost
   reappears only at the exit, where part j drops the block-(j+1) component: a type (i) exit is new for
   no window; type (ii) exits are free in the count but need equal foreign components.
4. Cycles: zeroing one block turns a cycle into a path.
5. Triangle: every pair of blocks lies in a window, so there are no mixed signals at all, and cancelling
   the shared block takes two window-local gates of two parts to a window-local gate of the third; even
   the exit cost vanishes. This is the mechanism of the 28-gate circuit for three positions.

## 4. Open

Constant depth >= 3; an explicit or small counterexample (any needs both parts with h >= 4); whether the
logarithmic term in Theorem 1 is tight; additivity for the run maps.

## Sources

- Jukna, note on the XOR complexity of direct sums: https://web.vu.lt/mif/s.jukna/Knizka/comment3.html
- Jukna, "Problem 7.7 solved": https://web.vu.lt/mif/s.jukna/Knizka/problem-7.7.html
- Jukna-Sergeev survey: https://web.vu.lt/mif/s.jukna/Knizka/linear.pdf
- Paul 1976 (scan): https://web.vu.lt/mif/s.jukna/Knizka/Paul-disjoint76.pdf
- Find et al.: https://arxiv.org/pdf/1304.0513
- Shitov: https://ar5iv.labs.arxiv.org/html/1712.08660
- Ja'Ja'-Takche: https://epubs.siam.org/doi/10.1137/0215071
- Sergeev 2025: https://m.math-net.ru/eng/mzm14541

Scripts in this directory: ledger.py, check_random.py, strassen_ds.py, threshold.py, small_checks.py,
each with its .out file.
