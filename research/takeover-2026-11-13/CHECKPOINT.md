# XOR structural research: checkpoint, 2026-11-13

Research branch: `research-2026-11-13-structural`.
Verified base: `e89b8a25f69195266f1e24e815cb96c7526a3511` on local and remote
`phase-2026-11-09`. The original worktree, `boolflux-2026-11-13` worktree, and untracked
`search/proposals/` were preserved. The new worktree is under this chat's `work/xor-structural`.

**Unchanged: 75 <= L(MixColumns) <= 88.** No claim that 88 is optimal.
All new results have hand proofs and independent machine review; no formal verification
or human certification is claimed.

## Read next

1. [Summary and judgment](SUMMARY.md).
2. [Hidden operands: Theorems H and HR](directions/independent.md), especially HR and the
   MixColumns consequence. This is the strongest new direction.
3. [Joint reconstruction](directions/JOINT.md), then its combination table in the hidden-work note.
4. [Global projection repair](directions/PROJECTION.md), including both counterexamples to converses.
5. [Reviews](reviews/hidden-review.md), [second hidden review](reviews/hidden-second-review.md),
   [foundational reconstruction](reviews/foundations-audit.md).

The earlier entry point is [the phase-12 checkpoint](../structure-2026-11-11/CHECKPOINT.md).
The old [record](../structure-2026-11-11/RECORD.md) now has a continuation entry.

## Reliable results and limits

- Reconstructed the 10/13 sheet lemmas and the 83/84 block-monotone bounds from symbolic proofs.
  Checked visible repair and Theorem V. One overstatement about sharing different repair chains
  was corrected; the theorem itself survives. The old 66-distinct-charge counterexample survives.
- **H:** independent selected event values on a maximal window, pairwise distinct on each block,
  force `t <= 2h-c`, where `h` counts distinct nonlocal operand gates and `c` their operand-graph
  components. A symbolic family attains the bound.
- **HR (stronger mechanism):** within each nonlocal-operand component, all operands have the
  same nonzero value outside the window. Project onto blocks incompatible with that outside
  value: every local partner disappears. The rank of the remaining target projections is at
  most the number of physical nonlocal operands in that component. Sum only over disjoint
  components. No target-independence assumption is needed for HR.
- **MixColumns:** `t=1,2,3,4` output events in any one of sheets `1,3,4,5,6,7` force at least
  `1,2,3,3` distinct hidden operand gates, even with other visible/hidden events present.
  Do not add these per-sheet bounds without controlling overlap.
- Sharing in-block pieces strengthens both forms of V. If the entire visible set consists of
  `t` output events in one of these sheets, joint reconstruction plus HR gives:

  | Sheet | t=1 | t=2 | t=3 | t=4 |
  |---|---:|---:|---:|---:|
  | 1 | 82 | 82 | 81 | 80 |
  | 3 | 82 | 81 | 79 | 77 |
  | 4,5,6,7 | 83 | 83 | 82 | 81 |

  These are lower bounds for reduced circuits with that exact visible-event profile;
  hidden events are unrestricted. The numbers are not claimed attainable.
- **Projection repair:** propagate requested block projections backward through the circuit;
  their distinct non-input values form an executable event-free value set `P`. For reduced
  original gate values `V`, `G >= B + |V\P| - |P\V|`. This handles all interacting events
  simultaneously and reuses equal values globally. It is an upper bound on repair cost, not
  a characterization of cancellation savings. A specified five-gate optimum refutes the converse.

## Next mathematical target

Pursue the componentwise separation-rank mechanism. The new rank argument works because it
first makes every uncounted local partner zero on the chosen coordinates. Rank of cancelled
copies, without that exclusion, failed in phase 10 and should not be revived.

Two genuine extensions remain open: selected internal visible values (which need not span
their entire output window), and sharing the same hidden operands between different sheets.
Seek a common separated projection or a proved overlap bound. Do not sum incompatible rank
claims or infer a global hidden-gate capacity from the single-window theorem.

The projection repair is a useful constructive control and source of counterexamples, but
its five-output limitation makes optimizing its overhead a weaker priority than HR.

## Method and reproducibility

No SAT, exhaustive enumeration, exact least-gate search, heuristic circuit search, or
computer-driven case elimination was run. Hand proofs are the evidence for universal claims.
[Direct checks](checks/README.md) verify 12 specified repair cases and one explicit sharp
hidden-work circuit by exact masks and linear algebra. Three named external corpus circuits
are saved as small fixtures; reruns do not require their original external location.

Windows-backed checkout reports executable-bit differences; Git commands used
`-c core.filemode=false` and staged only intended research paths. Shared repository config
was not changed. No model-conservation instruction from the earlier sprint was adopted:
the current user explicitly allowed purposeful independent agents.
