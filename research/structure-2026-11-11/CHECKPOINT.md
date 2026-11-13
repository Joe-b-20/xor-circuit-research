# Structural study: checkpoint for resuming (phases 3-12, 2026-11-12/13)

**Continuation, 2026-11-13:** the current takeover checkpoint is
[`../takeover-2026-11-13/CHECKPOINT.md`](../takeover-2026-11-13/CHECKPOINT.md), on
`research-2026-11-13-structural` based on verified `e89b8a2`. It records independent
foundational review, joint repair, and new hidden-operand and projection-rank theorems.
The phase-12 state below remains the historical starting point.

Branch `phase-2026-11-09`. Published statement unchanged: 75 <= L(MixColumns) <= 88. Main agent from
2026-11-12: Opus 5.5 (previous main agent Fable; conserve Fable, do not use it for delegated work). All
reviews are machine reviews by separate model instances, not human reviews.

## Read first
`visible/VISIBLE.md` (phase 12), `repair/REPAIR.md` (phase 11), `copies/COPIES.md` (phase 10), `cancel/SUPERPOSITION.md` (phase 9), `cancel/CANCEL.md` (phase 8), `joint/ACCOUNT.md` (phase 7), `SUMMARY.md` (phase sections 3-7), `SHARING.md` (sections 1, 8, 9), `RECORD.md` sections 16-19,
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
  Q_3 closes with the third sheet's charged work. K forces only a non-confined or escaping partner (confinement
  is a support condition), not an uncharged one. No cost proved.
- Refuted: "every cancellation costs a gate", "each uncharged partner pays for its double charges".
- Conjecture G (girth >= 4 => |union F_j| >= 10 per sheet): REFUTED in phase 9.
- Scope corrections listed in RECORD 23.

## Phase 9 results (RECORD 24; `cancel/SUPERPOSITION.md` is the coherent account)
- Counterexample (user's construction, rebuilt and verified; machine-reviewed): byte parities H_c shared by all
  sheets, outputs y = H_c + remainder; 66 distinct charged gates (8m + 2 for Q_m), G 521-616. Refutes the
  distinct-charge conjecture and Conjecture G; not G >= 80. No unconditional distinct-charge bound exceeds 66.
- Theorem K kept as a classification (no cost or reuse constraint); interpretation and sheet-system repairs.
- Lemma S1 (cancellation needs a second copy of the cancelled part); dual identity G = sum (fan-out - 1).
- Two-sided charging under one fixed transposition rule refuted: the witness and its reverse-order transpose
  both have 66 (other strategies not ruled out; "some transposition has >= 80" is sufficient for G >= 80, the
  converse is not established).

## Phase 10 results (RECORD 25; `copies/COPIES.md` is the coherent account)
- Copy-rank candidate defined precisely and left: C1 (global linear baselines give 0), C2 (rank carried by the
  cancelling gates), C3 (G = |Y| with copy rank n - 1), C4 (quadratic partner capacity, sharp), C5 (requirement
  is a coset; "needed elsewhere" needs the circuit). One definition gives Q_3 4, triangle 1-2, witness 32 (all on
  outputs), r88 0.
- Theorem F (first-exit identity; J6 an instance) and Corollary Z (unconstrained rank-one-term counting at one
  cut cannot see removal; circuit-constrained single-cut arguments not ruled out).
- Proposition V (reviewer, from RECORD 7, 9, 17): no whole-block cancellation => block-monotone => G >= 84;
  doubly charged gates lie in the ancestor cones of cancelling gates (J9).
- Proposition R (conditioning) holds; a conditional bound by this route carries the obligation of the same
  unconditional one (an obligation for the route, not an impossibility).
- Machine review `copies/review/REVIEW.md`; all fixes applied. Phase-11 correction: zeroing a cancelled block can make
  the event removable (an earlier projected value may equal it).

## Phase 11 results (RECORD 26; `repair/REPAIR.md` is the coherent account)
- Repair lemma (user's; verified): G >= 84 + |E| - K for every event-free D computing the event values (K gates);
  event-free => block-monotone => Corollary 17.4 (84). Sequential version: gadgets may read earlier nodes.
- Direct repair: G >= 84 - sum (w(e) - 2); sole event at a weight-7 output (sheets 1, 3, 4) => 79, weight 5 =>
  81; G <= 78 => two events or one of weight >= 8 (internal).
- Sharpness (prefix family): one event saves w - 2 for general maps.
- Theorem P (new): saving <= s_e + delta_e - 1 (shared ancestors carrying the cancelled blocks without clean
  projections, counted as in review: gates, nonzero, not values of nodes other than e; circuit reduced and live,
  first event); private cancelled content is free; Lemma Z (zeroing keeps circuits event-free). Formula exact on
  the prefix family, triangle circuits (2; G >= 82 for them) and per step on Q_3; an upper bound elsewhere.
- Lemma L (reviewer): shared carriers of a sole output event lie in (W_j u C) n W_j'.
- Phase-10 corrections (restriction remark, C5, Corollary Z, Proposition R wording).

## Phase 12 results (RECORD 27; `visible/VISIBLE.md` is the coherent account)
- Theorem G (user's; verified): only visible events (reached from outputs before any further event) need
  rebuilding; G >= B + |E| + |Q| - K. Lemma S: visible events lie in windows (<= 3 blocks, <= 2 for two
  sheets, {7} for three). Window credit (user's): sole event >= 84 - (w - 3); tail family shows it sharp in
  general.
- Theorem V (new): rebuild visible events off the charge families of Theorem 9.2 (G' >= 83 + U):
  G >= 83 + |E \ F| + |Q| - sum kappa, kappa <= 4 any weight; per-sheet form. 84 form via Theorem 17.3
  (G' >= 84 + |U \ X|). One visible event => >= 80; sole output event => 82-83; G <= 79 => two visible
  events, G <= 76 => three. Machine-reviewed (one false sentence fixed: kappa = 0 not -1 when t = 1).
- Limits: up to 4 per visible event; lower bound on the retained part only; vacuous when all outputs are
  visible events (witness). Phase-11 overstatements corrected in REPAIR.md.

## Next steps (the evidence suggests)
1. A lower bound on hidden work in terms of visible events: Theorem V reduces "below 80" to circuits with
   several visible events and little hidden work; the per-sheet form says each visible event replaces at most
   five charged gates of one sheet. What must the gates behind a sheet's visible events contain?
2. Sheet-1 borrowers: their rebuilt block-0 gates are where 83 and 84 differ.
3. Not recommended: per-event carrier lemmas, "one event then two" sequences, bounds on s_e alone, copy or
   rank-of-copy measures (phase 10), relative complexity for the byte parities as an easier first case,
   further distinct-charge statements (capped at 66), fixed-rule transposes, restriction sums with
   all-circuit waste bounds (phase 7).
Method restriction (applies to every agent): no SAT, no exhaustive enumeration or finite-family checks, no exact
least-gate searches (including BFS or Dijkstra over value sets), no exhaustive subset minimisation. It was not
observed on 2026-11-12 in the runs listed in `joint/FINITE_AUDIT.md`; nothing was rerun.
