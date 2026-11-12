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

## Next steps (phase 5 plan; MixColumns no longer deferred)
1. Main line: whether the export-reuse insight gives a general principle (TWOSIDED section 8: gain <=
   reconstruction surplus - receiver's marginal cost of the reconstructed sums). Challenge SB* seriously
   (`compose/refute/`); do not make proving SB* or defending 10 per sheet the required outcome.
2. In parallel: MixColumns relevance of the interface language (`compose/mc/`) and the review of the ring
   transfer report (`review-ring/`), with every locality assumption stated.
3. Gate order: the borrowing-loop examples are retired; pursue order only from a concrete new obstruction.
No SAT, no exhaustive enumeration, no case-elimination queue (user instruction, still in force).
