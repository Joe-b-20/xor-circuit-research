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

## Next steps, in the order the evidence suggests
1. SB* for one sheet. Test it first where SB' fails (deep labels, five or more entries, free stacks) and in
   Omega1 (four entries, three or four odd labels, f1 = 7, h1 = 1, rigid 8-gate mirror). A proof would give
   M_l = 10 l for every chain; a counterexample to SB* would have to be confronted with a far side, which
   is the next place a net saving could appear.
2. For rings: the end-free formulation proposed in `compose/ring/REPORT.md` (local discharging from the
   charge theorem, triangle-free hypothesis for m >= 4); review that report first.
3. Only then MixColumns (block 7 five-group window, third interfaces at sheets 1, 3, 4, J_01 diagonal,
   triangle {1,2,7}).
No SAT, no exhaustive enumeration, no case-elimination queue (user instruction, still in force).
