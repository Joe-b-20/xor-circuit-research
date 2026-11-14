# XOR structural research: checkpoint, 2026-11-14

Branch: `research-2026-11-13-structural`. This phase continues reviewed commit
`095f142`. Original verified base: `e89b8a25f69195266f1e24e815cb96c7526a3511`
on `phase-2026-11-09`. Other worktrees and `search/proposals/` are preserved.
Our worktree is this chat's `work/xor-structural`.

## Research direction

General unrestricted arguments are the priority. The user explicitly rejects
incremental numerical improvements or restricted bounds without a specified
unrestricted use. The twelve-consumer case breakdown is deferred; do not resume
it simply because cases remain open. No SAT, enumeration, exact circuit search,
or computer-driven elimination. Specified construction checks are allowed.

Read [the general synthesis](general/README.md) first.

## Current general theorem

[First odd target](general/FIRST_ODD_TARGET_TRADEOFF.md): choose a nonzero parity
with at least one required non-input odd target. H extra odd gates and d
even-plus-even gates satisfy

    H+d >= b_min = min_z (w_o(z)+2*w_e(z)-3)/2,

where z ranges over required non-input odd targets and w_o,w_e count supported
initially odd/even coordinate inputs. The first target's ancestor cone gives the
exact identity 2(h+d_C)=a+2f-3+beta+B_e: a,f count its odd/even input ancestors,
beta is its full undirected cycle rank, and B_e is excess even-node fanout.
This allows arbitrary sharing and cancellation and counts actual operand ports.

Together with r=s-c and delta=d+mu from the earlier parity account,
G=t_o+r+H+d+mu>=t_o+r+b_min+mu. A compatible-partition bound on r yields a
fully target-dependent inequality. Do not add separate parity or output-group
bounds without controlling their overlapping physical gates.

## Exact examples and obstructions

[Complement sums](general/COMPLEMENT_TRADEOFF.md): L(J+x_i : 1<=i<=n)=2n-2 for
all n>=4. For n=2k, the general theorem plus r>=k proves the bound directly.
Every optimum has r=k, mu=0, H+d=k-2; every split between H and d is attained.
An independent first-target laminar-tree proof covers odd n as well.

[Shared helper](general/SHARED_HELPER_AMPLIFICATION.md): m targets
x+a+b+c_i+d_i have unrestricted optimum 2m+2, attained with one odd helper.
Without odd helpers their optimum is 3m+1. Removing one shared odd helper can
therefore cost an unbounded m-1 additional gates, even with complete rewiring.
This directly rules out a universal constant-overhead removal argument.

[Causal separation](general/CAUSAL_BOOTSTRAP_GAP.md): explicit invertible rk by rk
maps for odd r>=3,k>=2 satisfy

    L(M)=(2r-1)k-2,      L_cyc(M)=L(M^(-1))=rk+r-2.

The ratio approaches two. Independent ternary equations can omit a linear
amount of the work needed to prepare the first output. The exact cyclic/inverse
bound uses freezing, projection, and an incidence count on independent equations.
The specified r=5,k=3 construction is checked directly: rank 15, forward 25,
inverse/cyclic 18. No search is involved; proofs cover all parameters.

All four notes have independent machine reviews; a
[final scope audit](general/reviews/unrestricted-progress-review.md) checks the
synthesis. The primary agent independently checked the proofs. These are not formal verification or human certification,
and no literature-novelty claim is made.

## Retained facts and limits

Unrestricted MixColumns remains 75<=L<=88; 88 is not assumed optimal. The older
restricted 85 bound and local 22 results are retained in the
[previous frontier](feedback/CHARGED_FRONTIER.md), without an active casework queue.
The [parity foundation](general/ODD_COMPONENT_DEFECT.md) and
[quadratic relaxation ceiling](general/QUADRATIC_LIFT_LIMIT.md) remain important:
zero even defect is always achievable for all-odd targets at some odd-work cost,
and the unconstrained quadratic tensor model cannot prove more than 60 for
MixColumns. Physical occurrence aggregates and separately available values differ.

## Next mathematical task

Develop a general account of shared supply across several output groups or stages:
what is already physically computed, how it helps later targets, and what new
work remains unavoidable. The first-target theorem applies once without overlap;
the shared-helper family shows why repeating it independently can overcount.
Preserve causal availability and charge each helper once. A different invariant
may be preferable to parity if it handles this directly.

History: [takeover summary](SUMMARY.md),
[record](../structure-2026-11-11/RECORD.md). Use Git with
`-c core.filemode=false`; shared configuration is unchanged. Stage intended files only.
