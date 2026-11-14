# XOR structural research: checkpoint, 2026-11-13

Branch: `research-2026-11-13-structural`. Current [five-entry continuation](feedback/FIVE_ENTRY_PROGRESS.md)
follows reviewed commit `577d8bc`. Original verified base:
`e89b8a25f69195266f1e24e815cb96c7526a3511` on `phase-2026-11-09`.
Other worktrees and `search/proposals/` are preserved. Our worktree is this chat's
`work/xor-structural`.

**New:** general source replay charges only group values absent from the original
physical source set, provided every chronological entry prefix splits between the
two groups. Five-entry eleven-consumer cases with two or three nonclean labels
require total at least 22. In the four-nonclean three-term-relation branch, a candidate
below 22 has exactly ten source gates and physical clean rank one.
**Still open:** four- and five-nonclean profiles, larger consumer budgets, full joint minimum.
**Retained:** ten-consumer and no-feedback joint minima 22; four-entry mixed
eleven-consumer minimum 22; block-monotone MixColumns lower bound 85;
unrestricted `75<=L<=88`. No assumption that 88 is optimal.
All proofs have independent machine reviews, not formal verification or human certification.

## Read next

1. [Current results and judgment](feedback/FIVE_ENTRY_PROGRESS.md),
   [general credited replay](feedback/CREDITED_REPLAY.md).
2. [Two-nonclean closure](feedback/TWO_NONCLEAN.md),
   [three-nonclean closure](feedback/THREE_NONCLEAN.md),
   [remaining four/five profiles](feedback/FOUR_FIVE_FRONTIER.md),
   [timing theorem and counterexample](feedback/FIVE_LABEL_TIMING.md).
3. [Four-diagonal bound](feedback/FOUR_DIAGONALS.md),
   [four-entry closure and cone correction](feedback/FOUR_ENTRY_CLOSURE.md),
   [rank-four physical supply](feedback/RANK_FOUR_SUPPLY.md).
4. [Entry/trace geometry](compatibility/QUOTIENT.md),
   [collision and causal-return theorem](feedback/ENTRY_RETURN_RIGIDITY.md),
   [diagonal confinement](feedback/DIAGONAL_CONFINEMENT.md).
5. [Augmented source minimum twelve](augmented/PROOF.md),
   [five diagonals and ten-consumer bound](feedback/FIVE_DIAGONALS.md),
   [general repair](feedback/GENERAL_REPAIR.md),
   [helper-value obstruction](feedback/SIDON_REPAIR.md).
6. [Takeover history](SUMMARY.md), historical [record](../structure-2026-11-11/RECORD.md),
   [checkpoint](../structure-2026-11-11/CHECKPOINT.md),
   [visible account](../structure-2026-11-11/visible/VISIBLE.md).

## Precise remaining eleven-consumer frontier

Every candidate of total at most 21 with exactly eleven consumer-bearing gates has
five distinct entry labels spanning rank four, four or five nonclean labels, and all
eleven gates in the relaxed target cones (cut zero-consumer operand ports). Original
physical clean rank is at most two. The unique label relation can be:

- Four nonclean: two nonclean labels plus the clean label. Here source cost is exactly
  ten and physical clean rank exactly one.
- Four nonclean: all four nonclean labels, forming an affine plane, with the clean
  label outside its linear span.
- Four nonclean: all five labels. The nonclean labels form a basis; the all-five-odd
  trace possibility is not excluded and must not be dropped.
- Five nonclean: four labels form an affine plane, with the fifth outside its span.

In either affine-plane case, exits before the outside label is first read can be
replayed without extra gates. A nonclean actual entry label has a unique physical
consumer pair and cannot be newly returned; direct return/re-entry is forbidden,
while indirect feedback changing the value remains possible.

## Mechanism and limitations

For `U=P direct-sum Q`, if every earlier-entry span splits between `P,Q`, source
replay costs at most `G0+B`, where `B` counts their nonzero values absent from the
original physical source set. A synthetic original value receives credit from
bypassing its later original gate. A virtual span member receives no credit.
A chronological greedy basis recovers the earlier rank-only bound.

Once five distinct rank-four labels are available, one extra XOR ensures one-XOR
access to their whole span. A fixed example nevertheless needs two extra source
replay gates when its fifth label arrives after the hard exits. This concerns
source-value preservation, not full circuit optima, and is not a K=11 witness.

Three independent diagonals plus four first rows require twelve source gates. A
clean triangle plus an independent fourth diagonal requires thirteen, attained for
one choice; five distinct nonzero diagonals also require thirteen. These bounds
permit arbitrary cancellation. All-clean actual entries force source cost twelve
at any consumer budget, as does the recorded even-own/odd-free nonclean parity class.

General rank-only replay has allowance `h(d)=2^ceil(d/2)+2^floor(d/2)-d-2`, sharp
through rank four. A fixed Sidon family forces `Omega(2^(d/3))` source-preservation
overhead offline; adaptive online repair and full-circuit prefix savings are separate
metrics. Historical repair/HR claims retain their sharing and charging hypotheses.

## Next direction and verification

Study the affine-plane interface after its outside label is read, combining causal
supply with collision constraints. For the five-term relation, determine what actual
entry positions in a six-gate transpose permit; algebraic label feasibility is not
circuit feasibility. The unrestricted joint problem also requires larger consumer
budgets, independently of these reductions.

Current independent reviews are linked from the summary. This pass used hand proofs
and symbolic verification of one specified counterexample, with no search. Use Git
with `-c core.filemode=false`; shared config is unchanged. Stage only intended research
files and preserve other worktrees.
