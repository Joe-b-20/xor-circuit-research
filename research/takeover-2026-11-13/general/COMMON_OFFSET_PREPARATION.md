# Common offsets and the failure of separate target cost profiles

2026-11-14. Hand arguments for unrestricted binary XOR continuations from an
actual supplied dictionary. Arbitrary sharing and cancellation are allowed.
No circuit search, representation enumeration, or case elimination is used.
Independent machine review is recorded in
[the review](reviews/common-offset-review.md); this is not formal verification,
human certification, or a claim of literature novelty.

For one target, the [dictionary frontier](SINGLE_TARGET_PARETO.md) exactly
describes two resources: odd-plus-odd gates K, and all other gates P=O+d_EE.
Knowing that entire frontier separately for every target still does not
determine their joint cost. The example below uses two actual chronological
states of the SAME coordinate-input problem. Every individual frontier stays
unchanged, while the joint complexity differs by an unbounded factor.

## 1. An exact common-offset law

Let S be a finite dictionary of physically available nonzero values. Write
ell_S(v) for the minimum number of dictionary members whose XOR is v. Suppose
distinct targets t_1,...,t_m and a value h satisfy, for an integer q>=1,

    ell_S(h)=q,
    ell_S(t_i)=q+1 for every i,
    u_i=t_i+h belongs to S for every i.

Then their exact remaining binary complexity is

    L_S(t_1,...,t_m)=m+q-1.                              (1)

**Upper bound.** Compute h from a minimum representation in q-1 gates, then
compute each t_i=u_i+h in one gate. This uses actual supplied operands. No
target can appear during the q-1-gate preparation, since each target alone
requires q gates by the single-target dictionary theorem.

**Lower bound.** The first required target produced by any continuation needs
at least q gates. Every one of the m-1 remaining distinct targets needs its
own later first-production gate. Thus at least q+m-1 gates are required. This
does not assume that a competing circuit computes h or follows the displayed
order. QED.

The sum of the separate target minima is mq, whereas (1) is m+q-1. The exact
shared saving is (m-1)(q-1). The hypothesis concerns a physically supplied
translate of the target family; it does not grant the span of S for free.

## 2. Two actual states with identical individual frontiers

Fix integers r>=1 and m>=1. Use independent coordinate inputs

    a_1,...,a_(2r),
    x_(i,1),...,x_(i,2r),z_i,              1<=i<=m.

Use total coordinate parity. The required non-input targets are the disjoint
odd sums

    t_i=x_(i,1)+...+x_(i,2r)+z_i.                         (2)

Let S_0 consist of all coordinate inputs. Its continuation complexity is
exactly 2rm: compute each disjoint target in 2r gates. A general support bound
also proves optimality, since the target supports have m components and use
m(2r+1) coordinates. The unused a_j inputs cannot invalidate that bound.

Now execute the following actual prefix, retaining EVERY intermediate value:

    e_(i,j)=a_j+x_(i,j),                   1<=j<=2r,
    E_(i,1)=e_(i,1),
    E_(i,j)=E_(i,j-1)+e_(i,j),             2<=j<=2r,
    u_i=E_(i,2r)+z_i,                     1<=i<=m.

There are 2r pair gates, 2r-1 even accumulation gates, and one odd final gate
for each i. The prefix therefore costs 4rm gates. Let S_1 contain all original
coordinates and all values produced by this prefix. Nothing has been erased
from the chronological dictionary.

Writing h=a_1+...+a_(2r), the supplied values satisfy

    u_i=h+t_i.                                           (3)

The prefix has prepared a translated family without physically supplying h.

## 3. Every single-target resource frontier is unchanged

Define a linear quotient map F to a space with independent coordinate vectors
A_1,...,A_(2r),Z_1,...,Z_m by

    F(a_j)=F(x_(i,j))=A_j,          F(z_i)=Z_i.

Then

    F(e_(i,j))=F(E_(i,j))=0,       F(u_i)=Z_i,
    F(t_i)=A_1+...+A_(2r)+Z_i.

Every even member of S_1 maps to zero. Every odd member maps to one coordinate
vector. Therefore any dictionary subset representing t_i has at least 2r+1
odd members: fewer unit images cannot sum to its quotient image of weight
2r+1. If o,e are its numbers of odd and even members, the single-target
representation point is

    K_R=(o-1)/2,                 P_R=(o-1)/2+e.

Both coordinates are at least r. The original 2r+1 coordinate representation
of t_i attains K_R=P_R=r. The exact discrete single-target frontier is thus

    frontier_(S_0)(t_i)=frontier_(S_1)(t_i)={(r,r)}        (4)

for EVERY target. For S_0 this follows immediately from independence; for S_1
it uses the quotient and the general single-target frontier theorem, so it
allows arbitrary cancellation and internal sharing in the continuation.

In particular every nonnegative gate-price combination alpha*K+gamma*P has
the same one-target optimum r(alpha+gamma) at both states. Ordinary word
lengths also stay identical: ell_(S_0)(t_i)=ell_(S_1)(t_i)=2r+1.

Likewise F(h) has weight 2r, while every dictionary member has image zero or
one unit. Hence ell_(S_1)(h)=2r, attained by the supplied a_j. The common-offset
law gives

    L_(S_1)(t_1,...,t_m)=m+2r-1.                         (5)

The hidden h is absent from S_1: its quotient image has weight at least two,
whereas every supplied nonzero value has image zero or one unit.

## 4. The joint two-resource frontiers are exact too

At S_0 the joint frontier is the single point

    (K,P)=(rm,rm).                                      (6)

Here are independent lower bounds for its two coordinates. A compatible
parity partition meets a target block of size 2r+1 in at most r+1 parts: exactly
one intersection is odd and all other nonempty intersections have size at
least two. Across the m disjoint target blocks and the 2r unused a_j coordinates,
the total part count is at most m(r+1)+2r. Thus the effective even rank is at
least rm, and K is at least that rank by the
[component account](ODD_COMPONENT_DEFECT.md).

For P, the [multi-output preparation bound](MULTI_OUTPUT_STARTUP.md) applied to
all m disjoint target supports gives H+d_EE>=m(r-1): the support union has
m(2r+1) coordinates and m overlap components. Since O=m+H, this is P>=rm.
Independent target formulas attain both lower bounds. These arguments allow
the competing circuit to use the unused a_j coordinates or to mix target
blocks and cancel later; no direct-sum theorem is assumed.

At S_1 the exact joint frontier is

    (K,P)=(r,m+r-1).                                    (7)

The K lower bound follows from any one target's frontier (4). Before the first
required target appears, at least r units of P are necessary by (4). Each
remaining distinct odd target needs a later odd first-production gate, so
P>=r+m-1. For attainment, pair the 2r supplied a_j in r odd-plus-odd gates,
combine those r even pairs in r-1 even-plus-even gates to obtain h, and add h
to each supplied u_i in m odd gates. This has K=r and P=r-1+m.

Since (6) and (7) attain their respective coordinatewise lower bounds, they
are the complete joint Pareto frontiers, not just minimum total costs or
particular price optima.

Thus all individual frontiers agree, but the joint frontiers differ by

    reduction in K: (m-1)r,
    reduction in P: (m-1)(r-1).

The ratio of ordinary remaining costs is

    L_(S_0)(T)/L_(S_1)(T)=2rm/(m+2r-1).

Taking m=r and letting r grow makes this ratio unbounded. A collection of
complete individual cost profiles can therefore miss an unbounded factor in
remaining joint complexity, even at two actual states of one coordinate-input
computation.

## 5. Scope and what the example identifies

The prefix cost 4rm is real and has not been included in the remaining cost
(5). The example does NOT give a faster end-to-end circuit for (2); computing
the targets directly from S_0 is cheaper than this prefix plus its continuation.
Its purpose is to show what information a state invariant must retain if it
is to measure shared preparation. The prefix has changed joint opportunity
without improving ANY required target's individual two-resource frontier.

The complete dictionary metrics are not claimed to agree. For i!=j,

    t_i+t_j=u_i+u_j,

so its S_1 word length is two, while its S_0 word length is 4r+2. The two-term
length is exact: the difference contains both z_i and z_j, while no supplied
member has both. Relations between targets reveal the preparation that their
separate profiles miss.

The target computation can be made an all-odd square involution without changing
any gate count: retain the a_j and x_(i,j) as identity outputs and replace each
z_i by t_i. The core coordinates stay fixed and each z_i receives a fixed even
core sum. Identity outputs cost no continuation gates. Thus the example does
not depend on a singular target map or a non-coordinate initial domain.

The common-offset law is a genuine joint attainment theorem, but it does not
solve arbitrary multi-output dictionary complexity. It suggests retaining
affine relations among target representations and the cost of activating their
common offset. That information is absent from independent target distances
and from independent target price profiles. No new numerical MixColumns bound
is claimed; unrestricted MixColumns remains 75<=L<=88.

The [specified checker](checks/check_joint_dictionary.py) verifies r=m=3:
the actual prefix has 36 gates, the original continuation has 18, and the
prepared continuation has eight with resource counts (3,5). Quotient images
certify every individual frontier (3,3), while the fixed joint lifts expose
the common prepared pattern. It also checks the square involution and the
changed target-difference representation. The
[saved result](checks/joint-dictionary-result.json) charges the prefix separately
and performs no circuit or representation search.
