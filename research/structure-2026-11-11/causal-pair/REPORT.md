# The time-order step of the pair proof: what it excludes

Delegated investigation, 2026-11-12 (phase 3), separate model instance (Opus); saved by the main agent
from its final message. Machine work, NOT yet independently reviewed. No SAT, no enumeration of circuits;
the two scripts verify the stated identities on the explicit configurations (checks, not proofs).

**Review (phase 4, `../review-causal-pair/REVIEW.md`) and corrected outcome.** The time-cycle step at the
end of configuration (X) can be replaced by F_2 dependence FOR CONFIGURATIONS ALREADY KNOWN TO HAVE THE
FOREST-PLUS-EXITS FORM (checked: all 384 such configurations have rank <= 8, so even path (3) falls to rank
alone). The claim below that (X) "cannot be part of any non-executable mirror system" over-claims: without
order, entries and exits are the same kind of relation and fibres need not be forests, so the order-free
version of (X) is a larger class that was not analysed. Many other steps of the pair proof still use order
(normalisation, cleaning, (Y), the forest premise). Examples (a) and (b) are non-executable only as the
given wirings: their value sets have executable bases of the same size (greedy closure), so they show no
complexity gap, and the "genuinely causal constraint round the ring" sentence is a framing, not a result.
Nothing here shows that executability excludes a profitable sharing pattern.

**Outcome (original wording, superseded where the paragraph above corrects it).** No 19-relation cyclic system was found. Configuration (X) of `../pair/PROOF.md` cannot be part
of any non-executable mirror system: its nine relations are always linearly dependent over F_2 (in two
sub-cases two signals coincide). So the order step in (X) is replaceable by algebra. Whether the whole pair
theorem holds for cyclic systems remains open, because other steps of the reduction to (X) use order.
Claims kept apart: (1) the proof uses order: true, removable at the (X) step; (2) the theorem fails for
cyclic systems: unsupported, open.

## A. The object and the replacement

One fibre with 6 signals, 5 entry relations {v, pi, v'} forming a forest F with edge labels
lambda(e) = s(pi); since N_0 = 4 every label is a unit u_k (pi = w'_k) or a triple-sum E_l (pi = B_l);
4 exit relations {x_l, y_l, B_l}, x_l and y_l the ends of a path P_l of F with label sum E_l.
*Borrowing digraph* on E-labelled edges: e -> f when lambda(e) = E_l and f lies in P_l; N its 0/1 matrix.
The temporal step excludes exactly the case that this digraph has a cycle.

**Lemma 1 (proved).** With the root and the w'_k known, rewrite in edge values and eliminate the B_l: the
nine relations determine all unknowns iff I + N is invertible over F_2; if singular, they are formally
dependent (the leftover combination lives on the root and the w'_k, independent and nonzero). In a circuit
N has no cycle, so I + N is unitriangular.

**Lemma 2 (proved by hand, without order).** Redoing the path and spider cases without order, every
surviving case has I + N singular or two fibre vertices equal:
- path (1a), labels (u_x, u_m, u_a, E_m, u_a): the E_m edge lies on its own path, N = [1];
- path (1b), labels (u_x, u_m, u_a, E_m, E_y): N = [[1,1],[0,0]];
- path (3), labels (E_a, u_m, u_a, E_m, E_c) (the proof's path case): l_1 + l_2 + l_3 + l_4 = 0, so
  v_0 = v_4; distinctness kills it without the time cycle;
- spider S1 (l_2 = l_3 = u_m) and S2 (l_2 = l_5 = u_p): self-loop, N = [1];
- spider S3 (the proof's case), labels (E_m, u_p, u_m, u_r, E_r): 2-cycle N = [[0,1],[1,0]]; explicit
  dependency entry1{c, B_m, a} + entry5{c, B_r, d} + exit_(B_r){a, b', B_r} + exit_(B_m){b', d, B_m} = 0.
**Replacement.** The nine gate equations of a circuit are distinct gates, hence independent; Lemma 2
contradicts that. The same independence holds for every basis of a based cyclic system, so (X) gives no
non-executable 19-mirror. *Checked* (`x_config_check.py`, all 24 index choices per case and reversal):
the relations hold as identities, rank <= 8, an explicit dependency, det(I + N) = 0 with a cycle, and the
coincidence in path (3). Completeness of the case list rests on the hand derivation.

## B. Primal side and transposition

**Proposition 3 (argued from reviewed lemmas: cyclic/REPORT Lemma 2.3 and Theorem C(iii), which need only
F_2-invertibility; not reviewed here).** A cyclic local system for the pair problem (base: units of b, b';
free part: vectors on a; K equations with F_2-invertible incidence matrix; WLOG no one-variable equations
and no two-variable equations with right side 0; exactly tau two-variable equations with a free right side
phi_j != 0, the entries) yields a based cyclic system T on w, w' containing A_i, B_i with at most tau
elements spanning a space containing Even(w) + 0 and |T| + tau <= K (formal inputs z_j for the phi_j,
Prop. 1(b), transpose; size K + 8 - (8 + tau); the span property by a left-kernel computation). Conversely
every such T yields a cyclic local system of size <= |T| + tau (transpose, set z_j := phi_j by solving
N Phi = (s_c ; 0), solvable exactly when the export span contains Even(w) + 0). So: a cyclic local system
with 19 equations exists iff a based cyclic mirror with |T| + tau <= 19 exists; any such object is
non-executable. Caveats: review gaps G2 (distinct values after dualising) and G3 (merging two-term stars)
apply and only lower counts.

**Where order is still used.** f and D can be defined without order; (I) f + tau >= 10 and D >= t carry
over (projection onto first parts gives a cyclic set of size f, then the inner inequality of Theorem 2.4;
invertibility gives a transversal). "Fibres are forests" FAILS without order (a fibre graph can contain a
cycle when no element of the fibre is produced by a first-part triple). The operand-role arguments of (Y),
the cleaning step and Lemma B in this setting were not audited.

## C. The principle

**Statement (proved).** Where an exit of one part (a path sum in a fibre forest) is used as an entry label:
executable implies the borrowing digraph is acyclic, so I + N is invertible over every field (an instance
of the leaf property, RECORD 6); F_2-determined (for the part checked here) holds exactly when
det_(F_2)(I + N) = 1. A pure permutation loop (each borrowed path contains exactly the next borrowed edge)
is always F_2-singular (the all-ones vector is in the kernel). In (X) only such loops and self-loops occur,
which is why algebra suffices there.

**Not a general F_2 fact: two explicit examples (checked, `loop_examples_check.py`).**
- (a) Sub-configuration (not a pair system): path x0-a1(u1)-x1-e(E0)-x2-f(E1)-x3-c1(u2)-x4-c2(u3)-x5 plus
  branch x2-d1(u1)-y1-d2(u0)-y2; exits B1 = x0 + x5, B0 = y2 + x3; N = [[0,1],[1,1]], det(I + N) = 1; the
  nine relations are F_2-determined, all values distinct, peeling stalls on all nine: not executable. A
  loop can be F_2-consistent once some borrowed path carries two borrowed edges.
- (b) Ring loop through the fibre roots: in Design A replace t_j = s0_j + s2_j by the exit
  t_j = u1_(j+1) + u2_(j+1); for m = 3, 4, 5 this gives 12m relations containing every Q_m target,
  F_2-determined, peeling stalls (not executable). N = 0: the dependency runs through the root, which
  cancels in x + y, invisible to the matrix. At 12m it gives no saving.

**Chains and rings.** The same criterion applies at every interface of a chain of three; whether the
residual 29-configurations of RECORD 16 are F_2-singular in the same way was not checked. The relay forced
in the Q_3 28-gate circuit is acyclic, as in any circuit. Example (b) shows F_2-consistent borrowing loops
round a ring exist, so round the ring "a closed loop of borrowings cannot pay" would be a genuinely causal
constraint, not an algebraic one. Whether L_cyc(Q_3) < 28 or L_cyc(Q_m) < L(Q_m) is open.

| Claim | Status |
|---|---|
| Lemma 1 | proved |
| Lemma 2 (order-free (X)) | proved by hand; instances checked |
| path case collapses to v_0 = v_4 | proved |
| Proposition 3 | argued from reviewed lemmas; not reviewed |
| order-free (I), D >= t | argued, unreviewed |
| fibres can fail to be forests without order | observed |
| examples (a), (b) | checked |
| pair theorem for cyclic systems | open |
