# Structural study: checkpoint for resuming (phases 3-7, 2026-11-12)

Branch `phase-2026-11-09`. Published statement unchanged: 75 <= L(MixColumns) <= 88. Main agent from
2026-11-12: Opus 5.5 (previous main agent Fable; conserve Fable, do not use it for delegated work). All
reviews are machine reviews by separate model instances, not human reviews.

## Read first
`joint/ACCOUNT.md` (phase 7, the current account), `SUMMARY.md` (phase sections 3-7), `SHARING.md` (sections 1, 8, 9), `RECORD.md` sections 16-19,
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
  gates and readers plus coincidences; two-block overlap formula; the eight-block sum is only an average.
- Limitation (J5, check): restriction plus all-circuit waste bounds capped at 83 (one block), 85 (two blocks);
  from three blocks on, waste bounds for <= 87-gate circuits would be needed.
- Reader identity and group-rank bound (J6-J7); sharing classification for block-monotone circuits and the exit
  lemma (J8-J9); census: the triangle is the only exit-mediated sharing in the sampled cheap circuits.
- Conjecture |F_0 u ... u F_7| >= 80 (least sampled 82), compensation not pair-local (circuits_2.txt line 783).
- Finite-check disclosure corrected (`joint/FINITE_AUDIT.md`): some small exhaustive checks were run on
  2026-11-12 after the instruction; record wording fixed; nothing rerun.

## Next steps (the evidence suggests)
1. The cost of exit-mediated sharing in its realised form, the triangle: in the triangle circuits with
   |F_1 u F_2| = 19 (for example circuits_2.txt line 783), find where the missing charge reappears (F_0, F_3, F_4
   over-charges, uncharged gates) and prove that it must, following the cancelled block-2 component (J9) to the
   sheet-3 partner. The open pair lemma of `compose/tri/` is its first step.
2. Delivery of the reduction term s_c on block 7 to sheets 0, 1, 3, 4 with the reader identity: in block-monotone
   circuits only the pairs {0,1}, {3,4} can share it (J8); a lower bound on the readers plus uncharged gates there
   would test whether the delivery picture explains the overhead above 80.
3. Not recommended: further single- or multi-block restriction sums with all-circuit waste bounds (J4, J5).
The instruction stands: no SAT, no exhaustive enumeration, no case-elimination queue. It was not fully observed
on 2026-11-12 (see `joint/FINITE_AUDIT.md`).
