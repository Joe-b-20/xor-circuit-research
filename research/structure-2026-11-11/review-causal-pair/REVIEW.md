# Review of causal-pair/REPORT.md (the time-order step of the pair proof)

Independent machine review, phase 4 (2026-11-12), separate model instance (Opus, medium effort) that
wrote none of the reviewed text. Saved by the main agent from its final message, lightly condensed. Not a
human review. `check_review.py` contains checks, not proofs; its part 1 is an exhaustive enumeration (6 trees x 8^5
labellings x exit paths), run on 2026-11-12 after the instruction excluding such runs (see
`../joint/FINITE_AUDIT.md`).

**Verdict.** On its stated premise (one fibre forest with 5 entry edges and 4 exits) the algebraic
replacement of the time-cycle step is correct. The headline "(X) cannot be part of any non-executable
mirror system" claims more: the forest premise and the split into entries and exits themselves come from
order. Examples (a) and (b) fail only because of their particular wiring; their value sets have
executable bases of the same size, so they show no complexity gap.

## 1. The replacement in (X)

- **Lemma 1: correct, given the forest premise.** With root and w'_k known, each vertex value is the root
  plus the edge values on its tree path; unit edges are known; an E_l edge has value B_l and each exit
  gives B_l = known part + sum of E-edge values on P_l: exactly (I + N) x = c. The leftover step is right
  (root and w'_k independent). The proof uses that each fibre is a tree.
- **Lemma 2: correct and complete on its premise.** Checked: all 6 five-edge trees, all 8^5 labellings by
  odd labels, all assignments of B_0..B_3 to distinct paths of length 3 or 5 with the right sums: 384
  configurations survive (path and 2-2-1 spider only); in all of them the nine formal relations have rank
  <= 8, none 9. So distinctness is not needed even in path (3) (rank 7); linear dependence alone does the
  work, which also removes the reliance on review gap G2 there.
- **"Independence is what a circuit guarantees":** correct but adds nothing for circuits (gate equations
  are triangular); for based cyclic systems it holds provided the nine relations are equations of the
  system.
- **The gap: what (X) is without order.** An entry {a, pi, a + pi} and an exit {x, y, B} are the same kind
  of relation (two signals with equal first part, one with first part 0); calling one an entry and the
  other an exit is an order distinction. Order-free, the object is a labelled graph on the fibre vertices
  with 9 edges; the report treats only the case in which the 4 edges carrying B_0..B_3 have a spanning
  forest as complement; a matching from det != 0 assigns each B_l a relation, but the remaining 5 matched
  edges can contain a cycle ("fibres are forests" fails without order). The counts producing (X) were not
  re-derived order-free.
- **Correct statement:** the time-cycle contradiction at the end of (X) (path and spider) can be replaced
  by F_2 dependence, for configurations already known to have the forest-plus-exits form.

## 2. Steps of the pair proof that still use order

Normalisation (deleting a gate equal to an earlier signal; gap G2; also behind "|P_i| = 1 duplicates a
signal"); the definitions of first gate and duplicate and the orientation of an entry; Lemma A and Steps
0-3 of the ten-gate proof (cleaning, K_c <= f + D, clean entries are entries); (I) f + tau >= 10 and
D >= t (argued to carry over, unreviewed); the mirror T* and (II) for cyclic systems (needs cyclic/REPORT
Lemma 2.3); configuration (Y) (operand-role and earliest-signal arguments); (*) (B_i is an exit; E_l labels
only after B_l); (X)'s "every duplicate is an entry, so each fibre is a tree". Not affected: Lemma B and
the parity/sum arguments (double star, cross sums), and "N_0 = 4 implies all labels odd". So the pair
theorem for cyclic systems remains open, and nothing here bounds the cyclic minimum.

## 3. Examples (a) and (b): the obstruction is the wiring

- (a): the 9 unknown values close greedily from {x0, w'_k} in 9 XORs (explicit executable order:
  x1 = x0 + w'1, x3 = x0 + w'0, x4 = x3 + w'2, x5 = x4 + w'3, B1 = x0 + x5, y2 = x5 + w'1, B0 = x3 + y2,
  y1 = y2 + w'0, x2 = x5 + w'0). Same value set, same size, executable.
- (b), m = 3, 4, 5: the 12m values close greedily; the original Design A wiring is determined and
  executable at the same 12m.
- Greedy closure is monotone, so it decides whether a fixed value set has an executable basis of size |V|;
  both value sets pass. The examples show only that the F_2 determinant test does not rule out borrowing
  loops; they do not show that causality costs anything. "A closed loop of borrowings cannot pay would be
  a genuinely causal constraint" is a framing, not a result.

## 4. Does executability exclude a profitable sharing pattern?

Nothing here shows it. What would: a based cyclic system (determined, distinct values) containing the
targets with size below the circuit minimum (for the pair, a cyclic mirror with |T| + tau <= 19; for the
ring, L_cyc(Q_3) < 28). Every value set of that size containing the targets must then fail greedy closure
from the base (which is just L > L_cyc). Cheap filter: a proposed cyclic example whose value set passes
greedy closure is an executable circuit in disguise.

| Claim | Verdict |
|---|---|
| Lemma 1 | correct, on the forest premise |
| Lemma 2 | correct and complete on the forest premise; all 384 have rank <= 8 |
| path (3) collapses to v_0 = v_4 | correct, not needed |
| "(X) cannot be part of any non-executable mirror" | over-claim: only for the forest-plus-exits form |
| "order step in (X) replaceable" | partly: the time cycle yes, the forest step that sets up (X) no |
| examples (a), (b) non-executable | as wirings only; executable bases of the same size exist |
| "genuinely causal constraint round the ring" | unsupported framing |
| Proposition 3, order-free (I), D >= t | not reviewed |
| pair theorem and cyclic minimum | open |
