# XOR structural research: checkpoint, 2026-11-13

Research branch: `research-2026-11-13-structural`. Current continuation follows reviewed
commit `eb9191a`; see [complete-row cost summary](row-cost/README.md).
Verified base: `e89b8a25f69195266f1e24e815cb96c7526a3511` on local and remote
`phase-2026-11-09`. The original worktree, the other research worktree, and untracked
`search/proposals/` were preserved. Our worktree is under this chat's `work/xor-structural`.

**Unchanged: 75 <= L(MixColumns) <= 88.** No claim that 88 is optimal.
Results have hand proofs and independent machine review, not formal verification or
human certification. Local and conditional bounds are not unrestricted bounds.

## Read next

1. [Current summary and judgment](row-cost/README.md).
2. [Exact free/ordinary-neighbor costs](row-cost/PORTS.md) and
   [source-interface saturation](row-cost/FOUR_ROWS.md).
3. [Completion geometry and sharp three-hidden-gate witness](row-cost/COMPLETIONS.md).
4. [Joint 0/1 interface rigidity and counterexample](row-cost/JOINT01.md).
5. [Earlier continuation](continuation/README.md): [sparse sharing](continuation/SPARSE.md),
   [affine completion theorem](continuation/AFFINE.md), [internal events](continuation/INTERNAL.md).
6. [First-pass summary](SUMMARY.md), [H/HR](directions/independent.md),
   [joint reconstruction](directions/JOINT.md), [projection repair](directions/PROJECTION.md),
   [foundational review](reviews/foundations-audit.md).

Reviews are linked from each pass's summary. The [historical checkpoint](../structure-2026-11-11/CHECKPOINT.md)
and [record](../structure-2026-11-11/RECORD.md) remain the earlier research trail.

## New results and their limits

- **Exact local cost.** A four-row sheet with `p` ordinary neighboring blocks and `f`
  separately free neighboring blocks costs `6` if both vanish, `3f+7` if `p=0,f>=1`,
  and `4p+3f+8` if `p>=1`. The lower bound allows arbitrary cancellation; explicit
  event-free constructions attain it. This counts one sheet, not disjoint global charges.
- **Source saturation.** For `r` disjoint own blocks each producing `k>=2` alternative
  four-row source variants, event-free cost is at least `(6+4k)r+min(r,4k)`, exactly
  `(6+4k)r+4k` for `r>=4k`. Local equality forces all `4k` physical source pairs.
  A tagged two-source version has exact event-free cost `22r+8` for `r>=8`; its natural
  shared-translation circuit costs `22r+12`. This specific lift loses its advantage;
  no general prohibition on four-row cancellation follows.
- **Completion geometry.** In a single maximal MixColumns sheet, completion differences
  vanish except possibly for the own-parity line. Four output events with only three
  nonlocal operands force a path and two parity-related local partners. A reduced
  145-gate MixColumns witness has exactly those four sheet-5 events and three hidden
  gates; the extra partner is retained and charged to sheet 6. It is not extra hidden
  cost. Exact two-sheet window equations include a two-dimensional `R^2` kernel.
- **Interface avoidance.** A four-triple sheet whose required free labels span a rank-three
  space D, but whose actual entry labels all avoid D, needs exactly eleven gates when
  an outside label is available. Equality forces five entries in one affine coset and
  a six-gate transpose with four odd traces and one even trace. A separate ten-gate
  first-sheet construction already supplies one clean diagonal. The joint 21-to-22 gap
  stays open.

## Earlier results that constrain future claims

The sparse family costs `13r+3` versus event-free optimum `15r+2` with just two hidden
gates, despite weights 5/7, boundary distance 6 and small blocks/windows. It disproves
any universal fixed multiple of hidden work as a bound on savings under those hypotheses.
It is rectangular with one row per own-block family, not MixColumns.

The global affine-completion bound is `h>=dim K-dim Delta`, or `dim K+1` with no actual
local partner; only physical components may be summed. It can be zero. Actual MixColumns
controls have one hidden gate shared across windows (156 gates), or one internal event
and no hidden gates (149 gates). These expensive witnesses do not constrain optimal cost.

The reconstructed 10/13 sheet lemmas, 83/84 block-monotone bounds, Theorem V, joint repair,
H/HR, and simultaneous projection repair remain available with their stated hypotheses.
The projection repair is one-sided; an optimal five-gate example refutes its converse.
The 66-distinct-charge counterexample still refutes unconditional distinct-charge counting.

## Next mathematical obligation

Seek a compatibility theorem that forces a paid interface when a local circuit is tight,
using the fixed MixColumns windows. Source saturation proves one model instance; the
sharp parity-partner witness rules out automatically charging forced partners again.

The focused joint 0/1 problem still needs both: exclude three independent diagonal
suppliers in an eleven-gate first-sheet computation, and exclude eleven-gate second-sheet
interfaces supplied by a ten-gate first sheet. The new avoidance theorem covers only
interfaces with no clean label; mixed interfaces remain. No universal compatibility lemma
or improved unrestricted MixColumns lower bound is established.

## Method and reproducibility

No SAT, exhaustive enumeration, exact least-gate search, heuristic circuit search, or
computer-driven case elimination was run. Universal claims rely on hand proofs.
[Current checks](row-cost/README.md#review-and-direct-verification) evaluate specified
constructions: local port cases, the 188/184-gate tagged comparison, the 145-gate
MixColumns witness, and the two joint-interface circuits.
[Earlier checks](checks/README.md) and [continuation checks](continuation/check-results.json)
remain reproducible; three small external circuit fixtures are saved in the repository.

The Windows-backed checkout reports executable-bit differences; use Git with
`-c core.filemode=false`. Shared repository config was not changed. Stage only intended
research paths, and preserve other worktrees and `search/proposals/`.
