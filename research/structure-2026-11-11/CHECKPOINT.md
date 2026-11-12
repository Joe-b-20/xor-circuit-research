# Structural study: checkpoint for resuming (phase 3, 2026-11-12)

Branch `phase-2026-11-09`. Published statement unchanged: 75 <= L(MixColumns) <= 88. Main agent from
2026-11-12: Opus 5.5 (previous main agent Fable; conserve Fable, do not use it for delegated work). All
reviews are machine reviews by separate model instances, not human reviews.

## Read first
`SUMMARY.md` (guide, phase-3 section), `SHARING.md` (sharing question; section 1 now defines the counted
families separately), `RECORD.md` sections 16-18, `compose/FRAMEWORK.md`, `compose/prove3/REPORT.md`,
`review-compose/REVIEW.md`.

## Done in phase 3
- Focused checks requested by the user: A (counted families, SHARING 1), B (RECORD 17.2 short wording
  false, full proof fine; `review-joint01b/`), C (direct-sum bound needs s > 0, RECORD 12), D (corpus totals
  vs circuit-specific claims, RECORD 9, 14, SUMMARY), E (chain recurrence reviewed, `review-chain/`; the
  MixColumns run 5, 6, 7, 0 needs blocks 1-3 zeroed).
- Composition results (RECORD 18): exit-free cuts additive; a sub-10l chain needs exits across every cut;
  Lemma R and Corollary R (open end rigid, every l); skip-exit lemma; Theorem A (a 29 needs an adjacent
  exit); Proposition H; residual gap (G1), (G2). All machine-reviewed.
- Constructive side: no 29; Q_3 transplant = 36 (`compose/build29/`); two-pair inequality (reviewed).
- Gate order: (X) time step replaceable by an F_2 dependency (`causal-pair/`, unreviewed).
- Correction: M_3 = 30 gives only M_l >= 9l + 3.

## Next steps, in the order the evidence suggests
1. The two-sided statement: the cost of the pair (mirror MC_2) when an exit hands it one extra base vector
   at its open end, against the charge on the giving sheet (Lemma B / Corollary R). It would close (G1) and
   (G2), and a uniform version would give 10 per sheet for all chains. Test object: the pair with a 4E
   boundary (17 <= N_2, conjectured 18).
2. A ring interface lemma for m >= 4 (no triangle): a charge for adjacent exits without an end. Q_3 shows
   it must fail at m = 3; Q_4 (33..40) is the first test.
3. Review `causal-pair/REPORT.md`; then decide whether the pair theorem holds for cyclic systems.
4. Only then: relevance to MixColumns (ring of eight plus reduction terms, triangles through block 7).
No SAT, no exhaustive enumeration, no case-elimination queue (user instruction, still in force).
