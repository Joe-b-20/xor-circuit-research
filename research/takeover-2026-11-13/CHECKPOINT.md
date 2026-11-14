# XOR structural research: checkpoint, 2026-11-13

Branch: `research-2026-11-13-structural`. Current [eleven-consumer closure](feedback/ELEVEN_CONSUMER_CLOSED.md)
follows reviewed commit `d8bfd65`. Original verified base:
`e89b8a25f69195266f1e24e815cb96c7526a3511` on `phase-2026-11-09`.
Other worktrees and `search/proposals/` are preserved. Our worktree is this chat's
`work/xor-structural`.

**New:** joint minimum 22 for exactly eleven consumer-bearing gates, allowing arbitrary
feedback and cancellation. A specified `(11,11)` circuit attains it. The ten-consumer
minimum was already 22. Any joint circuit below 22 must therefore use at least twelve
consumer-bearing gates and at most nine source-side gates.
**Still open:** larger consumer budgets and the unrestricted joint minimum.
**Retained:** no-feedback joint minimum 22; block-monotone MixColumns lower bound 85;
unrestricted `75<=L<=88`. No assumption that 88 is optimal.
Hand proofs have independent machine reviews, not formal verification or human certification.

## Read next

1. [Current result, complete case coverage, and judgment](feedback/ELEVEN_CONSUMER_CLOSED.md).
2. [Tight-fibre wire theorem](feedback/TIGHT_FIBRE_WIRES.md),
   [four-nonclean three-term closure](feedback/FOUR_NONCLEAN_PAIR_CLOSED.md),
   [affine-fibre restriction](feedback/AFFINE_FIBRE_CLOSURE.md),
   [six-value coset bound and final closure](feedback/SIX_COSET_VALUES.md).
3. [Prior two/three-nonclean closure](feedback/FIVE_ENTRY_PROGRESS.md),
   [four-entry and relaxed-cone reduction](feedback/FOUR_ENTRY_CLOSURE.md),
   [entry/trace geometry](compatibility/QUOTIENT.md),
   [collision and causal-return theorem](feedback/ENTRY_RETURN_RIGIDITY.md).
4. [Credited replay](feedback/CREDITED_REPLAY.md),
   [four-diagonal source bound](feedback/FOUR_DIAGONALS.md),
   [five-diagonal and ten-consumer bound](feedback/FIVE_DIAGONALS.md),
   [augmented minimum twelve](augmented/PROOF.md),
   [no-feedback joint and block-monotone consequences](augmented/CONSEQUENCES.md).
5. [Takeover history](SUMMARY.md), historical [record](../structure-2026-11-11/RECORD.md),
   [checkpoint](../structure-2026-11-11/CHECKPOINT.md),
   [visible account](../structure-2026-11-11/visible/VISIBLE.md).

## Current mechanisms

- Bypassing five entries of an eleven-gate consumer leaves the minimum six-gate
  ordinary triple circuit. Every ordinary-mask fibre has one root and entry edges
  form a tree. An exit is the label sum along its fibre path, using earlier labels.
- Literal marked-wire transposition preserves ordinary derivatives. At an adjacent
  pair of entry edges, a local accumulation exposes their trace sum with the common
  ordinary derivative. Two different even helpers cannot have equal nonzero wire
  derivatives. A path therefore cannot contain three consecutive distinct odd traces.
- All-five-odd traces give zero-overhead replay. In the three-term label-relation
  profile, the two even-trace entries lie in different fibres; completing the original
  three-value triangle gives zero-overhead replay as well.
- In either affine-plane profile, no two plane entries meet in the outside entry's
  fibre. There is at most one difficult return `h+qi+qj`, repaired with one extra
  `w=qi+qj`. Clean h yields the forbidden four-diagonal supplier. Nonclean h yields
  a sixth original value in the same diagonal coset as the five entries.
- A source supplying the four first rows and six distinct values in any diagonal
  coset needs at least twelve gates. At eleven, first-occurrence counts or odd-pair
  relation rank are insufficient. This applies to exports and arbitrary cancellation;
  attainment of five coset values at eleven gates is not claimed.

All four profiles retained in the preceding checkpoint are now excluded below 22.
The existing direct witness with eleven gates on each side gives equality. This
settles that consumer budget, not the unrestricted joint problem.

## General results and distinctions retained

For `U=P direct-sum Q`, if every entry-prefix span splits, source replay costs at most
`G0+B`, where B counts nonzero group values absent from the original physical source
set. An original value computed early receives credit by bypassing its later gate.
The rank-only allowance is `h(d)=2^ceil(d/2)+2^floor(d/2)-d-2`, sharp through rank four.

Five distinct rank-four labels, once available, need at most one extra XOR for one-XOR
access to the span. The fixed late-fifth-label example still needs two extra replay
gates; it is not a K=11 witness or a full-optimum separation. The fixed Sidon family
forces exponential offline source-preservation overhead; online and full-circuit
prefix results are separate metrics.

Three independent diagonals with the four rows need twelve source gates; a clean
triangle plus an independent fourth value needs thirteen (attained for one choice),
as do five distinct nonzero diagonals. Historical repair/HR statements retain their
sharing, charging, and output-window hypotheses.

## Next direction and verification

Analyze consumers with at least twelve gates and at most nine source-side gates.
The six-gate mirror is no longer automatic; identify what an extra ordinary gate
allows in root multiplicity, wire derivatives, and returned source directions.
Do not extrapolate the tight-fibre lemma to a larger mirror without proof.

Current independent reviews and the existing attaining witness checks are linked from
the summary. This pass used structural hand proofs, with no circuit search or new
numerical verification campaign. Use Git with `-c core.filemode=false`; shared config
is unchanged. Stage only intended research files and preserve other worktrees.
