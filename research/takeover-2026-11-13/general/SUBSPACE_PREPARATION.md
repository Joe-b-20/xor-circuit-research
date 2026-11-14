# Preparing a target subspace through quotient collisions

2026-11-14. Structural arguments for unrestricted binary XOR circuits from an
actual supplied dictionary. Sharing, cancellation, dependent supplied values,
and arbitrary intermediate values are allowed. An
[independent machine review](reviews/subspace-preparation-review.md) is saved.
No formal verification, human certification, or literature novelty is claimed.

Separate target distances miss shared preparation. This note measures the
directions in a target subspace that can already be recovered without producing
another value outside that subspace. Each additional such direction must be
prepared by an outside gate, and the first new direction has a dictionary
distance cost. The resulting theorem applies to every circuit, without imposing
a basis, cancellation pattern, or intermediate-value restriction.

## 1. The relation space of an actual dictionary

Let S be a finite set of physically supplied nonzero values, V=span(S), and
W<=V a subspace. Write pi:V->V/W for the quotient map. Call a nonzero quotient
value a color. Define

    R(S) = span((S intersect W) union
                {u+v : u,v in S, pi(u)=pi(v)!=0}) <= W.       (1)

This is a space of relations already accessible inside W. It is not an assertion
that its members are physically supplied for free.

**Closure lemma.** R(S) is exactly the set of W-values obtainable from S by a
continuation all of whose new gate outputs lie in W.

For attainment, each generator in S intersect W is supplied; each other
generator is the sum of two supplied same-color values and needs one W-valued
gate. Further sums remain in W. Conversely, a W-valued gate either adds two
W-values or adds two outside values with the same color. If all new outputs
are in W, its outside parents must come from S. Induction therefore keeps every
new W-value in (1). Zero can be omitted throughout. QED.

Thus R(S) describes zero OUTSIDE-W cost, not zero physical gate cost. An element
of this space can still require many W-valued gates to compute.

Now follow an arbitrary actual continuation, retaining all values in its
dictionary S_t, and put R_t=R(S_t). Its evolution is especially simple:

* A W-valued gate does not enlarge R_t: its value is already in R_t by (1).
* An outside-W gate with a previously absent color does not enlarge R_t.
* An outside-W gate v with an existing color has an old representative u of
  that color and changes the relation space to

      R_(t+1) = R_t + span{v+u}.                            (2)

For the last assertion, every other old same-color representative u' satisfies
u+u' in R_t. All newly introduced relation generators therefore agree modulo
R_t. Such a gate increases the relation-space dimension by either zero or one.
Call the dimension-increasing event a successful collision. A collision need
not repeat a physical value: its difference from an old representative is a
new direction in W.

Suppose the required W-valued outputs span W. Other required outputs may lie
outside W; they are allowed and are charged in the same circuit. Set

    R_0=R(S),                 q=dim(W/R_0),
    H=number of continuation gates whose outputs lie outside W.

At completion R_t=W, since all the required spanning values are available.
Consequently there are exactly q successful collisions. More precisely, if
t_0 and t_f count the distinct nonzero colors initially and finally, and zeta
counts outside gates at an existing color that do not increase dim(R_t), then

    H = (t_f-t_0) + q + zeta.                              (3)

These are counts from the actual chronological circuit. Repeated values and
unhelpful gates remain charged. Equation (3) does not grant a circuit freedom
to choose its final color set without paying for its causal construction.

For ordinary independent coordinate inputs e_1,...,e_n, write d=codim(W).
The zero-color coordinates and the differences within each nonzero color
class give independent contributions to R_0. A class of k coordinates
contributes k-1 dimensions; every zero-color coordinate contributes one.
Hence dim(R_0)=n-t_0 and q=t_0-d. Equation (3) becomes

    H = t_f-d+zeta.                                        (4)

## 2. A distance cost before the first new relation

For x in V, let ell_S(x) be its minimum XOR representation length in the actual
dictionary S, with ell_S(0)=0. When q>0 define

    Delta = min{ell_S(w) : w in W minus R_0}.               (5)

Necessarily Delta>=3. A W-value represented by one supplied member belongs to
R_0. A representation by two supplied members either uses two W-values or a
same-nonzero-color pair, and its sum again belongs to R_0.

**Subspace preparation theorem.** Every continuation whose required W-valued
outputs span W satisfies, when q>0,

    H >= q+Delta-3.                                        (6)

If M distinct required W-values are absent from S, its total gate count G also
satisfies

    G >= M+q+Delta-3.                                      (7)

If q=0, the conclusion is only H>=0; (5) is not defined. Required values can
be a selected collection of a larger output map. Nothing in the theorem
restricts which intermediate values the competing circuit may compute.

If W=V, every supplied member already lies in W and R_0=span(S)=W. Thus
treating a full invertible map as one target subspace gives no outside-work
obstruction. Proper target subspaces still constrain the full unrestricted
circuit, but their outside gate counts overlap and cannot simply be added.

**Absorption lemma.** For any U<=W,

    min_(w in W minus U) ell_(S union (U minus {0}))(w)
      = min_(w in W minus U) ell_S(w),                     (8)

whenever U is proper in W. Indeed, combine all U terms in an enlarged-dictionary
representation into u in U. The remaining S terms represent w+u, which is still
in W minus U, so there must be at least the right-hand minimum many S terms.
The reverse inequality holds because the enlarged dictionary includes S.
This proves an equality of minima over the set, not an equality for every
individual w.

**Proof of (6).** Before the first successful collision, R_t=R_0. Every
W-valued gate output before it therefore lies in R_0. At the first successful
collision v, choose an old same-color value u. Then

    w=v+u belongs to W minus R_0.

For this lower-bound argument only, grant all nonzero members of R_0 as extra
initial operands. Omit the earlier W-valued gates, using their granted values
where needed, and keep the outside gates in their original order. If H_* is
the number of outside gates through this first successful collision, appending
the gate w=v+u computes a member of W minus R_0 in at most H_*+1 gates.
Zero and copy operations can simply be omitted or rewired in this relaxation.

The [single-target dictionary theorem](SINGLE_TARGET_PARETO.md) says that
computing a nonzero value from a supplied dictionary needs its word length
minus one gates. Equation (8), with U=R_0, therefore gives

    H_*+1 >= Delta-1,            so H_* >= Delta-2.

There remain q-1 further successful collisions, each at a distinct later
outside gate. Thus H>=(Delta-2)+(q-1), proving (6). Each of the M absent
required W-values needs its own W-valued first-production gate, disjoint from
the H outside gates. This proves (7). QED.

The temporary grant of R_0 is a relaxation inside the proof. It is never used
as a free physical supply in an asserted construction.

## 3. The whole short-word rank profile also gives bounds

The same proof can discard already short directions before measuring the
next ones. For any proper subspace U<=W containing R_0, grant U as additional
initial supply. Its relation space is exactly U: the new supplied members
have zero quotient color, and the original same-color relations were already
in R_0<=U. The original circuit is still a valid continuation with the same
outside gate count in this relaxation. By (8) and (6),

    H >= dim(W/U) + min_(w in W minus U) ell_S(w) - 3.       (9)

In particular, for integers k>=2 put

    R_[k] = span{w in W : ell_S(w)<=k}.

Then R_[2]=R_0 exactly. If R_[k] is proper in W, every w outside it has
ell_S(w)>=k+1, giving

    H >= dim(W/R_[k])+k-2.                               (10)

All these inequalities hold simultaneously. The profile measures how many
independent W-directions have short joint representations; it is not a list
of distances of the designated targets separately. Computing this profile
efficiently for an arbitrary dictionary is not claimed.

## 4. Coordinate inputs: distance plus dimension

Suppose S is an independent coordinate basis, W has dimension r>=1, and its
minimum nonzero coordinate Hamming weight is D>=3. No coordinate and no sum
of two coordinates lies in W, so R_0=0, q=r, and Delta=D. Consequently every
circuit computing a spanning collection of W-values satisfies

    H >= r+D-3,             G >= M+r+D-3.                 (11)

For minimum distance one or two, use the actual R_0 theorem instead. The
hypothesis D>=3 cannot simply be dropped from this specialization.

**When independent triples cannot save work.** If m linearly independent
required targets each have coordinate weight three and their span contains no
nonzero vector of weight one or two, their exact unrestricted complexity is
2m. Indeed r=M=m and D=3 in (11), while separate two-gate formulas attain 2m.
Consequently any saving for independent triples requires a weight-one or
weight-two combination somewhere in their full span. This is a necessary
condition, not a claim that every such combination produces a saving.

The outside count is sharp in three families, proved without search:

**Distance three, any dimension.** Use independent coordinates a,x_i,y_i for
1<=i<=r and targets w_i=a+x_i+y_i. They are independent. A nonempty sum indexed
by J has weight 2|J|+(|J| mod 2), so W has minimum distance three. Compute
h_i=a+x_i outside W, followed by w_i=h_i+y_i inside W. This has H=r and total
cost 2r, attaining both bounds in (11).

**Distance four, any dimension.** Use r+1 disjoint coordinate pairs
e_i=a_i+b_i for 0<=i<=r and targets w_i=e_0+e_i for 1<=i<=r. These targets
are independent. A nonempty sum indexed by J uses |J| pair blocks and also
block zero exactly when |J| is odd, so its weight is
2(|J|+(|J| mod 2)), with minimum four. Compute all r+1 pair values e_i outside
W, then all r targets in one W-valued gate each. This gives H=r+1 and
G=2r+1, again attaining (11).

**Dimension one, any distance D>=3.** Let W be generated by the sum of D
independent coordinates. A successive-sum formula uses D-1 gates; its first
D-2 nonzero proper partial sums lie outside W and its final gate lies in W.
Thus H=D-2 and G=D-1, attaining (11).

These are constructions meeting a bound for unrestricted competing circuits,
not optimality claims limited to circuits following the displayed formulas.

## 5. Exact recovery of the common-offset preparation

Use the actual dictionary S_1 from
[the common-offset construction](COMMON_OFFSET_PREPARATION.md), including every
intermediate of its 4rm-gate prefix. Its independent coordinates are
a_1,...,a_(2r), x_(i,1),...,x_(i,2r),z_i for 1<=i<=m, and

    t_i = x_(i,1)+...+x_(i,2r)+z_i,
    h = a_1+...+a_(2r),               u_i=h+t_i in S_1.

Let W=span{t_1,...,t_m}. For this actual dictionary,

    R_0 = {sum_i alpha_i*t_i : sum_i alpha_i=0},
    dim(R_0)=m-1,          q=1,          Delta=2r+1.        (12)

Here is a check that includes the retained intermediates. Use the map F with
independent images A_1,...,A_(2r),Z_1,...,Z_m defined by

    F(a_j)=F(x_(i,j))=A_j,             F(z_i)=Z_i.

Every S_1 member maps to zero or one coordinate vector: the retained pair
values and their accumulations map to zero, and F(u_i)=Z_i. For a nonempty
target combination indexed by J,

    F(sum_(i in J) t_i)
      = (|J| mod 2)*(A_1+...+A_(2r)) + sum_(i in J) Z_i.

No nonzero W-value is supplied, since this image has weight at least two,
whereas supplied images have weight at most one. A sum of two supplied values
has image weight at most two, so if it belongs to W it cannot be an odd target
combination: those images have weight at least 2r+1>=3. Thus R_0 is contained
in the even-combination subspace in (12). Conversely u_i+u_j=t_i+t_j, so the
same-color pair relations generate that entire subspace. This also covers
m=1, when R_0=0.

Every W-value outside R_0 is an odd target combination, whose F-image has
weight 2r+|J|>=2r+1. Since every dictionary member has image weight at most
one, its dictionary length is at least 2r+1. A single t_i has its original
coordinate representation of that length. This proves Delta=2r+1.

The theorem therefore gives

    H >= 2r-1,                 G >= m+2r-1.              (13)

Compute h in 2r-1 gates from the supplied anchors, with every intermediate
outside W, and then compute t_i=u_i+h in m W-valued gates. This attains both
bounds. In particular the exact remaining complexity m+2r-1 is recovered by
the new joint invariant, while every separate target frontier stayed unchanged
through the prefix.

The preparation's concrete progress is that R(S) grew from zero at the
coordinate-input state to dimension m-1 at S_1. Those relations are accessible
using W-valued gates; they are not all physically free. The 4rm prefix cost
remains real and separate. No improved end-to-end algorithm for the disjoint
targets, and no improved numerical MixColumns bound, is claimed.

The [specified checker](checks/check_subspace_and_sidon.py) and
[saved result](checks/subspace-sidon-result.json) verify the exact chronological
identity on three sharp coordinate constructions and the common-offset
continuation at r=m=3. The latter has initial relation rank two, one missing
direction, and five outside gates plus three target gates; its 36 prefix gates
are charged separately. A fixed quotient certifies the escape length seven.
The checks use linear algebra and specified circuits, without circuit,
representation, or codeword search. General distances and the rank-profile
corollary are established by the hand arguments, not by enumeration.
