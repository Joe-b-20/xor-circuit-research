# XOR structural research: checkpoint, 2026-11-13

Research branch: `research-2026-11-13-structural`.
Current continuation follows reviewed commit `14b89e6`; see
[continuation summary](continuation/README.md).
Verified base: `e89b8a25f69195266f1e24e815cb96c7526a3511` on local and remote
`phase-2026-11-09`. The original worktree, `boolflux-2026-11-13` worktree, and untracked
`search/proposals/` were preserved. The new worktree is under this chat's `work/xor-structural`.

**Unchanged: 75 <= L(MixColumns) <= 88.** No claim that 88 is optimal.
All new results have hand proofs and independent machine review; no formal verification
or human certification is claimed.

## Read next

1. [Current summary and judgment](continuation/README.md).
2. [Sparse sharing counterexample](continuation/SPARSE.md): constant hidden work can save
   arbitrarily many gates even with output weights 5/7, boundary relation distance 6,
   window width 3 and block dimension at most 4.
3. [Affine local completions](continuation/AFFINE.md): a valid joint count across windows,
   including its explicit zero-bound controls.
4. [Internal-event extension](continuation/INTERNAL.md) and [actual overlap](continuation/OVERLAP.md).
5. [First-pass summary](SUMMARY.md), [H/HR](directions/independent.md),
   [joint reconstruction](directions/JOINT.md), [projection repair](directions/PROJECTION.md).
6. [Sparse review](continuation/reviews/sparse-review.md),
   [second sparse review](continuation/reviews/sparse-second-review.md),
   [affine reviews](continuation/reviews/affine-second-review.md),
   [foundational reconstruction](reviews/foundations-audit.md).

The earlier entry point is [the phase-12 checkpoint](../structure-2026-11-11/CHECKPOINT.md).
The old [record](../structure-2026-11-11/RECORD.md) now has a continuation entry.

## Reliable results and limits

- **Continuation: sharp limits of hidden-work counting.** A reduced live family has
  `13r+3` gates versus event-free optimum `15r+2`, exactly two hidden gates (one nonlocal),
  and independent output rows of weights 5/7. Its boundary minimum relation weight is 6,
  windows have at most 3 blocks, blocks at most 4 coordinates, and own blocks have no
  reciprocal incidence. This disproves a universal constant multiple of hidden work as
  a bound on savings, even under these combined hypotheses. It is rectangular, with
  one output per own-block family, so is not a MixColumns counterexample.
- **AC (proved).** In a connected nonlocal-operand component, let K span its selected
  event values and let E be all local vectors in the operand coset `a+K`. If E is nonempty,
  put `Delta=span{ell+ell_0:ell in E}`. Then `h>=dim K-dim Delta`; an incidence bit can
  strengthen this by one. With no actual local partner, `h>=dim K+1`. Sum over the global
  physical components, not separate per-sheet copies. All spaces are obtained by linear
  systems on given masks. AC includes HR but can be zero, including for full target span.
- **Internal events (proved).** Two local operands with surviving support R and cancelled
  support C are algebraically possible iff two windows containing C cover R. Exact window
  membership gives a stronger separator than pairwise co-occurrence. A specified independent
  sheet-3 internal-event profile gives `G>=84-2m` when it is the complete visible set.
- **Actual MixColumns controls (directly checked).** A reduced 156-gate circuit has one hidden
  gate shared between two maximal-window output events. A reduced 149-gate circuit has one
  proper-support internal visible event and no hidden gates. These expensive witnesses
  refute unconditional overlap/support inferences, not constraints limited to cheap circuits.

The first-pass foundations remain valid: the reconstructed 10/13 sheet lemmas, 83/84
block-monotone bounds, visible repair, H/HR and their exact-visible-profile table, shared
in-block reconstruction, and simultaneous projection repair. Their proofs, counterexamples,
and reviews remain linked in [the first-pass summary](SUMMARY.md). The projection repair
is one-sided; an optimal five-gate example refutes its converse. The 66-distinct-charge
counterexample still rules out unconditional distinct-charge counting.

## Next mathematical target

The internal and multiwindow rank extensions are now proved, with the limits above. The
next useful question is the extra cost of supplying several local completions of one
hidden value while computing all four rows of each implicated MixColumns sheet. Use the
actual fixed incidence and triple/pair row demands. No generic hidden-gate credit follows
from sparsity, boundary distance, or bounded windows; SPARSE disproves it.

The completion-difference space Delta is an explicit place to state a compatibility lemma,
but a large Delta alone does not force extra hidden gates or rule out useful cancellation.
Production/ancestry constraints must identify additional cost without charging gates
already counted by the repair families. No such universal MixColumns lemma is established.

The projection repair is a useful constructive control and source of counterexamples, but
its five-output limitation makes optimizing its overhead a weaker priority than HR.

## Method and reproducibility

No SAT, exhaustive enumeration, exact least-gate search, heuristic circuit search, or
computer-driven case elimination was run. Hand proofs are the evidence for universal claims.
[Direct checks](checks/README.md) verify 12 specified repair cases and one explicit sharp
hidden-work circuit by exact masks and linear algebra. Three named external corpus circuits
are saved as small fixtures; reruns do not require their original external location.
[Continuation checks](continuation/check-results.json) verify five specified constructions,
including both actual MixColumns controls and the packed sparse family at `r=2` (29 gates
versus an explicit event-free 32). Universal optimum and boundary-distance claims are
proved by hand, not by enumeration.

Windows-backed checkout reports executable-bit differences; Git commands used
`-c core.filemode=false` and staged only intended research paths. Shared repository config
was not changed. No model-conservation instruction from the earlier sprint was adopted:
the current user explicitly allowed purposeful independent agents.
