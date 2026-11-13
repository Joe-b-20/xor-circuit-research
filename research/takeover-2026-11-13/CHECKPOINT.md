# XOR structural research: checkpoint, 2026-11-13

Branch: `research-2026-11-13-structural`. Current continuation follows reviewed commit
`a04558e`; see [current results and judgment](augmented/README.md).
Verified original base: `e89b8a25f69195266f1e24e815cb96c7526a3511`, local and remote
`phase-2026-11-09`. The original and other research worktrees, including untracked
`search/proposals/`, are preserved. Our worktree is this chat's `work/xor-structural`.

**New:** augmented supplier minimum 12; no-feedback joint minimum 22;
block-monotone MixColumns lower bound 85, also applying to event-free circuits.
**Unchanged:** unrestricted `75 <= L(MixColumns) <= 88`. No optimality claim about 88.
Hand proofs and independent machine reviews are not formal verification or human
certification.

## Read next

1. [Current summary](augmented/README.md), [consolidated exact local proof](augmented/PROOF.md).
2. [Three-entry exclusion](augmented/THREE_ENTRIES.md),
   [four-entry exclusion](augmented/FOUR_ENTRIES.md), and
   [joint 22 / block-monotone 85 consequences](augmented/CONSEQUENCES.md).
3. [Previous supplier closure](crossing/ODD_CLOSURE.md),
   [rank-two normal form](crossing/NORMAL_FORM.md), [previous summary](crossing/README.md).
4. [Rank-one / even-confinement pass](frontier/README.md), [tradeoffs](tradeoff/README.md),
   [compatibility](compatibility/README.md), [row costs](row-cost/README.md).
5. [Earlier continuation](continuation/README.md), [first-pass summary](SUMMARY.md),
   historical [record](../structure-2026-11-11/RECORD.md),
   [checkpoint](../structure-2026-11-11/CHECKPOINT.md), and
   [visible-event account](../structure-2026-11-11/visible/VISIBLE.md).

Independent reviews are linked from the current summary. The exact local proof includes
a short independent replacement for the older ten-gate augmented exclusion; it does not
rely on the historical finite basis checks or on the ten-gate supplier-closure theorem.

## New proved results and limits

- **Augmented minimum twelve.** Four first-sheet rows and any three independent even
  diagonal values require at least twelve gates, allowing arbitrary cancellation.
  A specified event-free twelve-gate circuit attains this for one basis. Attainment
  for every prescribed basis is not asserted.
- **Why eleven fails.** Seven required ordinary masks leave three or four entries.
  The three-entry case requires too many connections between residue classes. The
  four-entry case has no even-only equations; named-pair rigidity, common formal sums,
  and an alternating cycle bound the available independent relations. The last tight
  configuration would make the three requested diagonals dependent.
- **Exact joint 22 under no feedback.** The previous ten-gate first-cone branch was
  already closed. The remaining eleven-gate cone with ten consumer-bearing gates
  would have to contain three independent diagonals, contradicting the new minimum.
  The explicit 22-gate construction attains the result. First-sheet ancestors carrying
  the consumer block and later cancelling it remain outside this hypothesis.
- **Block-monotone lower bound 85.** The joint charge family is disjoint from the
  sheet-3 family of at least thirteen gates and five own-charge families of at least
  ten: `22+13+5*10=85`. Block monotonicity is the output-cone support condition, which
  includes event-free circuits but can also permit internal block cancellation.
- **Repair baseline.** Generic theorems whose repaired circuit is event-free may use
  baseline 85. For the reduced projected-value form this gives
  `G>=85+|V minus P|-|P minus V|`. The correction may be negative; charged-slack formulas
  require their own justification and cannot all be updated by numerical substitution.

## Next mathematical direction

The augmented 11-versus-12 gap and no-feedback joint 21-versus-22 gap are settled.
The next priority is the cost of feedback: can an ancestor of a first-sheet output
introduce the consumer block and later cancel it cheaply enough to beat the exact
no-feedback cost 22? The unrestricted local joint problem and unrestricted MixColumns
bound remain open. Track the physical values and independent equations that feedback
makes available, rather than treating each cancellation or hidden gate as a separate
credit. Do not assume the full 88-gate circuit is optimal.

## Earlier constraints that still matter

At ten producer gates, clean rank is at most two and is attained. Rank two has a rigid
four-entry/two-helper normal form and all within-diagonal-coset differences stay in its
actual clean span. Rank at most one also cannot support an eleven-gate consumer.
Entry deletion bounds actual nonclean quotient directions; physical relation rank is
`|O|-components+dim(even-only relations + colours(cycle space))`.

The sparse family permits unbounded savings with only two hidden gates under the
recorded restrictions. HR and affine-completion bounds need sharing control before
summing physical components. Projection repair is one-sided. The historical 83/84
bounds and Theorem V remain valid with their hypotheses; 85 is the new block-monotone
baseline, not an automatic replacement for every charge-accounting constant.

## Method and repository state

No SAT, circuit enumeration, exact least-gate search, heuristic circuit search, or
computer-driven case elimination was used. Universal lower bounds are hand arguments.
The [direct verifier](augmented/check_witnesses.py) checks the specified 12-/22-gate
constructions; [results](augmented/check-results.json) record the required values,
diagonal rank, liveness, event-freeness, and absence of first-sheet feedback.

Use Git with `-c core.filemode=false` for this Windows-backed checkout. Shared config
is unchanged. Stage only intended research paths; preserve other worktrees and
`search/proposals/`.
