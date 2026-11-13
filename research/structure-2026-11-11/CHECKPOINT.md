# Structural study: checkpoint for resuming (phases 3-9, 2026-11-12)

Branch `phase-2026-11-09`. Published statement unchanged: 75 <= L(MixColumns) <= 88. Main agent from
2026-11-12: Opus 5.5 (previous main agent Fable; conserve Fable, do not use it for delegated work). All
reviews are machine reviews by separate model instances, not human reviews.

## Read first
`cancel/SUPERPOSITION.md` (phase 9), `cancel/CANCEL.md` (phase 8), `joint/ACCOUNT.md` (phase 7), `SUMMARY.md` (phase sections 3-7), `SHARING.md` (sections 1, 8, 9), `RECORD.md` sections 16-19,
`compose/TWOSIDED.md` (definitions), `compose/sb/REPORT.md`, `compose/sb2/REPORT.md` and their reviews.

## Established (statements with their hypotheses)
- Proposition 18.1: a circuit C with no exit across cut k has cost(C) >= M_k + M_(l-k) (not an inequality
  for M_l). Corollary 18.2: if M_j = 10 j for every j < l, a counterexample at length l saves exactly one
  gate and has an exit across every cut; so a 29 for three sheets needs exits across both cuts.
- Lemma R / Corollary R: at the open end an exit costs the first sheet at least one gate (every l).
- Theorem A: a 29-gate chain of three needs an adjacent exit (not: "skip exits never help").
- Phase 4 (RECORD 19): exact split near1 + far1; honest replacement 2.1, 2.1', 2.1*; Theorem 19.1 (three
  entries: cost >= 10 + M_(l-1), every l); 19.2 (all labels even: additive, every l); 19.3 (four entries,
  except Omega); 19.4 (O2). SB and SB' false (verified counterexamples). SB* => M_l = 10 l (explicit
  induction). All machine-reviewed.
- Rings (`compose/ring/`, unreviewed): only the split and honest replacement survive.
- Gate order (`causal-pair/`, reviewed): replacement only for forest-plus-exits configurations; no cost of
  executability shown.

## Phase 5 results (RECORD 20)
- TWOSIDED consolidated (SB, SB' refuted; SB* exact; what it depends on; Theorem 7.1; reconstruction
  inequality; proved classes with hypotheses).
- Transposition principle P3/P4 (independent clean labels): SB* for one exit and for near1 = 10; P5: SB* for
  four entries. Open: several exits with four or more types together; dependent labels with e1 >= 5
  (finite check shows where P4 breaks: four unit types at near1 = 11).
- Obstruction O: the T0/T1 templates at single primal blocks and mirror groups, with inequalities claimed for
  all circuits, are limited by verified witnesses to at most 86/87 (block 7: 68, or 66 over all exit-free
  witnesses; the earlier 73 was loose); witness ceilings, not attainable lower bounds (phase 6 exact form).
- Ring report reviewed and corrected; gate-order loop examples retired.

## Phase 6 results (RECORD 21)
- Obstruction O exact (`compose/mc/OBSTRUCTION.md`, numbers verified on the whole corpus in `review-O/`).
- Compatibility at a cut (`compose/compat/`): exact join for exit-free cuts; the label relation type does not
  determine the far cost (no claim that no smaller useful description exists); |T| = R_b + w_b (restriction plus
  waste); for the restriction form with all-circuit waste bounds, ceiling 83 (75 at block 7) from verified
  expensive low-waste circuits (not a limit on bounds for optimal or <= 87-gate circuits).
- Triangle mechanism worked through (`compose/tri/`); P(1,2) >= 21 for the observed partner form; open lemma
  for the general form.
- TWOSIDED corrected (deficit/slack, J_0, clean labels, finite checks).

## Phase 7 results (RECORD 22; `joint/ACCOUNT.md` is the coherent account)
- Exact accounting of several block restrictions of one circuit (J1-J4): value-set formula; one block = pure
  gates and readers plus coincidences; two-block overlap formula; the eight-block sum is an average (no information by itself).
- Limitation (J5, check): restriction plus all-circuit waste bounds capped at 83 (one block), 85 (two blocks), 87
  (four blocks); at three blocks {4,5,6} is not capped by known circuits.
- Reader identity and group-rank bound (J6-J7); sharing classification for block-monotone circuits and the exit
  lemma (J8-J9); census: the triangle dominates exit-mediated sharing in the sample (one variant).
- Conjecture |F_0 u ... u F_7| >= 80 (REFUTED in phase 9; least sampled 81), compensation not pair-local (circuits_2.txt line 783).
- Finite-check disclosure corrected (`joint/FINITE_AUDIT.md`): some small exhaustive checks were run on
  2026-11-12 after the instruction; record wording fixed; nothing rerun.

## Phase 8 results (RECORD 23; `cancel/CANCEL.md` is the coherent account)
- Lemma W (charge theorem with its slack); W1 "double charges collapse in window projections" refuted.
- Theorem K (cancellation chase): closures by plain charged work force a directed cycle of length <= t_j + t_k + 2
  in the window graph Gamma; girth 2 (Q_2), 3 (Q_3), 4 (MixColumns), acyclic (chains). MixColumns needs >= 2
  cancellations for a charged closure; observed triangle closures use one cancellation and an uncharged partner;
  Q_3 closes with the third sheet's charged work. No cost proved.
- Refuted: "every cancellation costs a gate", "each uncharged partner pays for its double charges".
- Conjecture G (girth >= 4 => |union F_j| >= 10 per sheet): REFUTED in phase 9.
- Scope corrections listed in RECORD 23.

## Phase 9 results (RECORD 24; `cancel/SUPERPOSITION.md` is the coherent account)
- Counterexample (user's construction, rebuilt and verified; machine-reviewed): byte parities H_c shared by all
  sheets, outputs y = H_c + remainder; 66 distinct charged gates (8m + 2 for Q_m), G 521-616. Refutes the
  distinct-charge conjecture and Conjecture G; not G >= 80. No unconditional distinct-charge bound exceeds 66.
- Theorem K kept as a classification (no cost or reuse constraint); interpretation and sheet-system repairs.
- Lemma S1 (cancellation needs a second copy of the cancelled part); dual identity G = sum (fan-out - 1).
- Two-sided charging (C and C^T) refuted: the witness and its reverse-order transpose both have 66.

## Next steps (the evidence suggests)
1. Copy-rank: count the rank of the copies that cancellations force (Lemma S1) and that are not values needed for
   other outputs; it combines reuse globally and separates Q_3 (copies are other sheets' required values), the
   triangle (one copy, three double charges) and the superposition witness (high-rank copies, uncharged). First
   task: a definition of "needed for other outputs" under which the count is a lower bound on gates and not a
   restatement of G >= 80; test it on the three examples.
2. Only if 1 gives a usable inequality: its restriction to cheap circuits, with the structural role of the
   hypothesis stated.
3. Not recommended: further distinct-charge statements (capped at 66), charging of transposes (refuted), and
   restriction sums with all-circuit waste bounds (phase 7).
Method restriction (applies to every agent): no SAT, no exhaustive enumeration or finite-family checks, no exact
least-gate searches (including BFS or Dijkstra over value sets), no exhaustive subset minimisation. It was not
observed on 2026-11-12 in the runs listed in `joint/FINITE_AUDIT.md`; nothing was rerun.
