# XOR structural research: checkpoint, 2026-11-13

Branch: `research-2026-11-13-structural`. Current [eleven-consumer continuation](feedback/ELEVEN_FRONTIER.md)
follows reviewed commit `6801e98`. Original verified base:
`e89b8a25f69195266f1e24e815cb96c7526a3511` on `phase-2026-11-09`.
Other worktrees and `search/proposals/` are preserved. Our worktree is this chat's
`work/xor-structural`.

**New:** physical-collision cost bound; twelve source gates under diagonal confinement
at any consumer budget; precise necessary conditions for the four-entry mixed profile.
**Still open:** unrestricted eleven-consumer case and the full joint minimum.
**Retained:** ten-consumer joint minimum 22 even with feedback, no-feedback joint
minimum 22, block-monotone MixColumns lower bound 85, unrestricted `75<=L<=88`.
No claim that 88 is optimal. Hand proofs with independent machine review are not
formal verification or human certification.

## Read next

1. [Current judgment and open questions](feedback/ELEVEN_FRONTIER.md),
   [collision and causal-return theorem](feedback/ENTRY_RETURN_RIGIDITY.md).
2. [Diagonal confinement](feedback/DIAGONAL_CONFINEMENT.md),
   [four-entry mixed source constraints](feedback/FOUR_ENTRY_FEEDBACK.md).
3. [Five diagonals and the ten-consumer bound](feedback/FIVE_DIAGONALS.md),
   [rank-three replay](feedback/RANK_THREE.md),
   [entry/trace geometry](compatibility/QUOTIENT.md).
4. [Augmented minimum twelve](augmented/PROOF.md),
   [joint and block-monotone consequences](augmented/CONSEQUENCES.md),
   [general repair](feedback/GENERAL_REPAIR.md), [helper-value obstruction](feedback/SIDON_REPAIR.md).
5. [Takeover history](SUMMARY.md), historical [record](../structure-2026-11-11/RECORD.md),
   [checkpoint](../structure-2026-11-11/CHECKPOINT.md), and
   [visible account](../structure-2026-11-11/visible/VISIBLE.md).

## Current proved results

- **Every projected collision counts.** Let `D` span the required consumer source
  parts, `U` the actual entry span, and `L_D` the minimum cost with `D` free. For any
  `C subset U` disjoint from `D`, partition physical consumer gates and ordinary
  inputs by their full values modulo `C`. Then `K>=L_D+delta_C`, where `delta_C`
  is the sum of class sizes minus one. This counts physical multiplicities and
  needs neither source-first scheduling nor trimming of exit-only ancestors.
- **Direct nonclean returns cannot feed back at eleven.** Each nonclean difference
  has at most one physical pair. An actual entry uses that allowance; an exit
  returning its label is redundant. An exit followed by entries whose labels span
  a space disjoint from `D` and containing the return gives an extra deletion:
  `K>=L_D+|I|+1`. Indirect feedback changing the value before re-entry is still allowed.
- **All-clean source cost twelve.** If all actual entries lie in diagonal `D`,
  `G_0>=12` for every consumer budget. A free-block retraction proves the same when
  entries lie in `D+<h>` with even ordinary source part and odd free part of `h`.
  In these classes exactly eleven consumer gates require total at least 23.
- **Four-entry mixed profile.** Its labels are a basis `c,d,n,m`, with clean `c,d`
  and nonclean `n,m`; `e=n+m` completes a diagonal basis. Replay adds at most `e`
  and `p=c+d`. Any total at most 21 must have `G_0=10`, original nonzero diagonal
  values exactly `c,d`, no nonredundant clean exit, and a return `n+p` or `m+p`.
  Projecting out the other nonclean label places the corresponding ternary pair
  in the unique two-root own-mask fibre of a ten-gate three-entry consumer.
  These conditions do not exclude the profile.
- **All-nonclean five-entry profile.** Its five labels occupy one affine plane and
  one point of the complementary plane in the nonclean coset. A nonredundant
  nonclean return can only be one of the other three points. Clean exits are not
  confined by this argument.

## Next mathematical direction

For the four-entry profile, determine whether a twelve-gate source can contain the
four first-sheet rows and `c,d,c+d,e`, with `c,d,e` independent diagonal values.
A thirteen-gate lower bound would close that profile; it is not proved. The existing
five-diagonal bound does not automatically extend to four. Alternatively resolve the
necessary ternary pair in the projected consumer's two-root fibre. The five-entry
mixed profile and consumer budgets at least twelve remain separate obligations.
Do not infer source supply from a virtual diagonal span, or treat the direct-return
prohibition as a ban on indirect feedback.

## Earlier results and limits

Three independent diagonals plus the first rows require twelve source gates; five
distinct nonzero diagonals require thirteen. The latter closes every ten-consumer
joint circuit at 22 via rank-three replay. A specified ten-gate consumer nevertheless
permits a local ternary return; its later-label credit illustrates the difference
between one exit's cost and total replay cost.

General replay costs at most `h(d)=2^ceil(d/2)+2^floor(d/2)-d-2`, sharp through rank
four. The fixed Sidon family forces `Omega(2^(d/3))` extra source gates even offline;
this is a source-value-preservation bound, not an exponential full-circuit gap.
Adaptive online repair matches the upper asymptotic order; fixed prefixes have
exact full-circuit saving `d-2`. Keep those metrics distinct.

Generic event-free repairs may use baseline 85, but historical charged-slack formulas
retain their own hypotheses. HR/affine completion require sharing control, and the
sparse family still refutes savings bounds from hidden-gate count alone.

## Verification and repository discipline

Current independent reviews are linked from the current summary. All new arguments
are symbolic hand proofs; no SAT, circuit enumeration, exact search, or computer-driven
case elimination was used. Previous specified construction checks remain unchanged.
Use Git with `-c core.filemode=false`; shared config is unchanged. Stage only intended
research files and preserve other worktrees.
