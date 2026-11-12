# Structural study: checkpoint for resuming (phases 3-4, 2026-11-12)

Branch `phase-2026-11-09`. Published statement unchanged: 75 <= L(MixColumns) <= 88. Main agent from
2026-11-12: Opus 5.5 (previous main agent Fable; conserve Fable, do not use it for delegated work). All
reviews are machine reviews by separate model instances, not human reviews.

## Read first
`SUMMARY.md` (phase-3 and phase-4 sections), `SHARING.md` (sections 1, 8, 9), `RECORD.md` sections 16-19,
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
- Obstruction O: untyped single-cut arguments cannot exclude an 87 for MixColumns (bounds at most 73 at
  block 7, at most 87 anywhere, for SB*-type compositions); scope: inequalities claimed for all circuits.
- Ring report reviewed and corrected; gate-order loop examples retired.

## Phase 6 results (RECORD 21)
- Obstruction O exact (`compose/mc/OBSTRUCTION.md`, numbers verified on the whole corpus in `review-O/`).
- Compatibility at a cut (`compose/compat/`): exact join for exit-free cuts; no small faithful interface;
  |T| = R_b + w_b (restriction plus waste); single-cut ceiling 83 (75 at block 7) from verified low-waste circuits.
- Triangle mechanism worked through (`compose/tri/`); P(1,2) >= 21 for the observed partner form; open lemma
  for the general form.
- TWOSIDED corrected (deficit/slack, J_0, clean labels, finite checks).

## Next steps (the evidence suggests)
1. The missing coupling at one block: do circuits with few wasted gates under zeroing block b need more
   surviving work (a tradeoff R_b + w_b against w_b)? Start with block 7, where K_7 is between 60 and 69.
2. Several cuts at once without double counting: the identity |T| = R_b + w_b holds for every b; combine the
   waste sets of different blocks (they overlap) into one count.
3. The open pair-circuit lemma behind the triangle (no 20-gate pair circuit with a non-unit pure-block-2
   ancestor of a sheet-1 target), which would make the triangle's one-gate cost unconditional.
4. Supporting chain work only where it tests these mechanisms (dependent labels: how dependencies change the
   supplier's obligations).
No SAT, no exhaustive enumeration, no case-elimination queue (user instruction, still in force).
