# XOR structural research: checkpoint, 2026-11-14

Branch: `research-2026-11-13-structural`. This phase continues reviewed commit
`44fa588`. Original verified base: `e89b8a25f69195266f1e24e815cb96c7526a3511`
on `phase-2026-11-09`. Isolated worktree: this chat's `work/xor-structural`.
Other worktrees and `search/proposals/` are preserved.

## Direction

General unrestricted mathematics is the priority. The user rejects incremental
numerical bounds and restricted casework without an unrestricted payoff. The
fixed-budget queue remains deferred. No SAT, circuit enumeration, exact search,
or computer-driven elimination. Supporting linear algebra and checks of specified
constructions are allowed. Read [the synthesis](general/README.md) first.

## A joint state barrier stronger than separate word lengths

[Common-offset preparation](general/COMMON_OFFSET_PREPARATION.md): two actual
coordinate-prefix states S0,S1 have every target's complete individual (K,P)
frontier equal to (r,r), but exact joint frontiers (rm,rm) and (r,m+r-1).
K counts OO gates; P=O+d_EE counts all others. Remaining costs 2rm and m+2r-1
have unbounded ratio when m=r grows. ALL intermediate values remain in S1.
The prefix costs 4rm and is explicitly charged separately; this is not a faster
end-to-end circuit. The target map also admits a square all-odd involution.

Construction: anchors a_j, local x_(i,j),z_i, j=1..2r; t_i=sum_j x_(i,j)+z_i.
Prefix e_(i,j)=a_j+x_(i,j), their successive even sums, then u_i=h+t_i,
h=sum_j a_j. Quotient a_j,x_(i,j)->A_j, z_i->Z_i sends every supplied even to zero
and every odd to a unit, forcing o>=2r+1 in every target representation. Thus
individual frontier stays (r,r). Supplying h once gives the joint optimum.
Pair-difference lengths change; full dictionary metrics are NOT claimed equal.

General law: if t_i+h are supplied, ell(h)=q and ell(t_i)=q+1 for all distinct
targets, then exact L_S(T)=m+q-1. First target lower bound plus output count
matches actual common-offset preparation. Competing circuits are unrestricted.

## Exact joint representations and two-target formula

[Joint normal form](general/JOINT_DICTIONARY_NORMAL_FORM.md): dictionary row
matrix B and targets T satisfy

    L_S(T)=min_(RB=T)L_2(R)
          =min_(RB=T)[n(R)-t(R)+L_2(R_red)].

The lift is joint, preserving shared gates. n is used dictionary members, t
is distinct nonzero output patterns. Some optimum computes disjoint groups
of members with equal patterns once, then a residual distinct-pattern circuit.
Groups need not have disjoint ordinary supports; sums may be dependent. No
free span values. The residual can contain the entire original problem when
B=I; neither minimization is claimed efficient or solved by enumeration.

For distinct nonzero u,v, some optimum needs at most one shared value:
L_S(u,v)=min{ell(u)+ell(v)-2, min_(h!=0)[ell(h)+ell(u+h)+ell(v+h)-1]}.
The helper is paid for; zero arms are omitted. Pairwise bounds cannot simply
be added across targets. Do not turn this into a small-output casework queue.

## Exact saturation by target closure

[Coset saturation](general/COSET_SATURATION.md): partition n inputs into c>=2
nonempty parts, r=n-c, require ALL values odd on exactly one part. There are
c*2^r targets, including inputs. Exact L_2=c*(2^r-1). Supply r actual pair-basis
values, then traverse the required cosets, one gate per missing odd output.
Compatible partitions force even rank r. Every optimum has r even gates and
c*2^r-n odd gates, with H=d_EE=mu=0; for c>=3 its parity partition equals the
specified one. This does not assert a full-ancestor forest. With c=2 this is
all odd forms and L_2=2^(n-1)-2. Sparse target sets are not claimed to saturate.

## Evidence and next task

All three notes have independent machine reviews and primary-agent proof checks;
no formal verification, human certification, or literature-novelty claim. A
[final scope review](general/reviews/joint-dictionary-progress-review.md) checks
the synthesis and specified evidence.
[Specified checks](general/checks/check_joint_dictionary.py) and
[saved results](general/checks/joint-dictionary-result.json) verify r=m=3:
prefix 36, remaining 18 versus 8, joint resource frontiers (9,9)/(3,5), individual (3,3),
fixed lifts (21 members/3 patterns and 9 members/4 patterns), square involution,
and the two-target shared budget 7. Also a five-input coset construction has
twelve targets, nine gates, even rank 2, H=d_EE=mu=0. No optimization or search.

Next: joint affine sharing patterns and the residual distinct-pattern map.
Target closure explains when intermediate odd costs vanish; a useful converse
must allow all competing supply bases, extra rank, EE work, and cancellation.
Do not fix a basis as a restriction or grant it free. Other frameworks allowed.
Unrestricted MixColumns remains 75<=L<=88. The previous 57/58/60 certificate
ceilings retain their named limits, not circuit upper bounds.

Retained [branch repair](general/BRANCH_INTERSECTION_REPAIR.md),
[simultaneous repair gap](general/CAUSAL_FOREST_QUOTIENT.md), and
[pair-supply tradeoffs](general/PRIVATE_TAGGING_TRADEOFF.md). Keep full beta distinct
from odd mu, physical pair count distinct from rank, and remaining cost distinct
from end-to-end cost. History: [summary](SUMMARY.md),
[record](../structure-2026-11-11/RECORD.md). Use Git with `-c core.filemode=false`;
shared configuration is unchanged. Stage only intended research files.
