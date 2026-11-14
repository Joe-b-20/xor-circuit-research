# Joint dictionary computation and one shared value for two targets

2026-11-14. Structural hand arguments for unrestricted binary XOR continuations
from actual supplied values. Dependent dictionaries, arbitrary cancellation,
intermediate sharing, and free fanout are allowed. No circuit search or
representation enumeration is used. An
[independent machine review](reviews/joint-dictionary-review.md) is saved; this
is not formal verification, human certification, or a literature-novelty claim.

The [single-target theorem](SINGLE_TARGET_PARETO.md) chooses one representation
of one target. Choosing representations separately for several targets can
lose their sharing. The correct generalization chooses a JOINT formal lift.
Column compression then gives an exact normal form for every number of outputs.
For two outputs this has a concrete consequence: one shared intermediate value
suffices in some optimum, even when the supplied dictionary is dependent.

## 1. Actual dictionaries and a joint formal lift

Let S=(s_1,...,s_q) be a finite list of distinct nonzero supplied vectors in
F_2^n. Its members are actual free operands; arbitrary elements of their span
are not. Write B for the q-by-n matrix with those vectors as rows. Let T be
a matrix of required nonzero target rows in span(S), and write L_S(T) for the
minimum number of further binary XOR gates. Repeated target rows are harmless.

For a matrix R with q columns, R B=T means that its rows choose simultaneous
dictionary representations of the target rows. Let L_2(R) mean ordinary binary
complexity on q independent coordinate inputs, ignoring unused columns. Then

    L_S(T) = min_(R B=T) L_2(R).                         (1)

**Lower bound.** In any actual continuation replace each supplied vector s_i by
its own independent formal input e_i, retaining every gate and its two parents.
Projection e_i -> s_i recovers every actual gate. The formal target matrix R
therefore satisfies R B=T, and the lifted circuit computes R with the same gate
count. Thus every actual circuit has at least the right side of (1) gates.

**Upper bound.** For any R satisfying R B=T, run a circuit for R with s_i in
place of its i-th formal input. The projected circuit computes T, with no more
gates than the original. Taking the minimum proves (1).

This lift is joint: every output comes from the SAME formal circuit and the
same dictionary labels. It does not replace a shared gate with separate copies
in different output formulas. Dependence among supplied values is retained in
the constraint R B=T, rather than being ignored or treated as free computation.

## 2. An exact normal form that retains all shared work

For a chosen lift R let n(R) be the number of its nonzero columns, and let t(R)
be the number of distinct nonzero column patterns. Let R_red contain one
representative of each such pattern. The [column-cloning theorem](COLUMN_CLONING.md)
gives

    L_S(T) = min_(R B=T)
               [ n(R)-t(R)+L_2(R_red) ].               (2)

In particular, some optimal unrestricted continuation has this form:

1. Partition the used supplied values into disjoint groups according to their
   column patterns in one optimal lift. Each pattern records which formal
   target representations contain that dictionary member.
2. Compute each group sum once, using |group|-1 gates.
3. Run a circuit for R_red on those computed group sums, preserving all its
   sharing among targets.

The preparation groups are disjoint as sets of dictionary MEMBERS, not
necessarily as supports in the original n coordinates. Their projected sums
may be dependent. Equation (2) remains valid: the lift provides the lower
bound and projection provides the matching realization. No group sum or
residual combination is granted for free.

There are at most 2^k-1 distinct patterns when k target rows are required. This
is a structural parameter bound, not an instruction to enumerate patterns or
solve the minimization by exhaustive search. The residual term L_2(R_red) is
essential. With an independent coordinate dictionary B=I, the lift is uniquely
R=T; a matrix already having distinct nonzero columns retains its entire
original circuit problem as R_red. Thus the normal form does not turn arbitrary
multi-output computation into a word-length or rank calculation.

Equations (1)-(2) concern ordinary binary size. The column compression is not
claimed to preserve separate odd/even gate populations, even rank, or the
two-resource Pareto frontier.

## 3. Exact two-target complexity

Now let u,v be distinct nonzero desired values. A joint lift consists of two
subsets A,B of the supplied dictionary, with XOR(A)=u and XOR(B)=v. Put

    kappa(A,B)=1 if A intersect B is nonempty, and 2 otherwise.

For these fixed formal representations the exact coordinate-input complexity is

    L_2(A,B)=|A union B|-kappa(A,B).                      (3)

**Lower bound.** The complete ancestor union has at least |A union B| input
ancestors and at most kappa(A,B) components, because overlapping target supports
force overlapping cones. The graph count gives (3) as a lower bound, allowing
arbitrary cancellation and extra ancestors.

**Attainment.** If the sets are disjoint, compute their two sums separately.
If they meet, compute the common sum, the A-only sum when nonempty, and the
B-only sum when nonempty, then attach each exclusive sum to the common value.
This uses exactly |A union B|-1 gates. The common value is computed once.

Combining (1) and (3) gives the exact joint dictionary formula

    L_S(u,v) = min_(XOR A=u, XOR B=v)
                  [ |A union B|-kappa(A,B) ].            (4)

This theorem applies to all competing continuations. It does not assume that
they have only one shared helper or that their actual coordinate supports are
disjoint. Rather, some optimum can be put in that form after choosing its
joint dictionary representations.

## 4. An equivalent formula in actual dictionary distances

Let ell_S(w) be the minimum number of supplied dictionary members whose XOR
is w, with ell_S(0)=0. The single-target binary cost is ell_S(w)-1 for w nonzero.
Then (4) is equivalently

    L_S(u,v) = min {
        ell_S(u)+ell_S(v)-2,
        min_(h in span(S), h!=0)
            [ ell_S(h)+ell_S(u+h)+ell_S(v+h)-1 ]
    }.                                                    (5)

The first term computes the two values independently. In the second, compute
one actual shared value h and the two residual values u+h and v+h, then attach
each nonzero residual to h. A zero residual means that target already equals
h; it is omitted, with no physical zero supplied. The resulting gate count is
at most the displayed expression, including h=u or h=v. Every nonzero h is
charged through ell_S(h); arbitrary span elements are not free helpers.

For the reverse inequality choose optimal joint subsets A,B from (4). If they
are disjoint, the first expression in (5) is at most their cost. Otherwise let
C=A intersect B and h=XOR(C). The case h=0 cannot occur in an optimal choice:
both A minus C and B minus C still represent the nonzero u,v and are disjoint,
giving cost |A union B|-|C|-2, strictly below |A union B|-1.

Hence h is nonzero. The three disjoint dictionary groups C, A minus C, B minus C
represent h, u+h, v+h, so their sizes bound the three respective ell values
from above. The second expression in (5) is therefore at most
|A union B|-1. Together with the constructions proving the other direction,
this establishes (5).

This is an exact unrestricted shared-value theorem for two targets, not merely
a lower bound from their separate representation lengths. It allows the best
h to differ from every individually shortest representation. The full distance
function, or equivalently a joint lift, matters; the theorem does not assert an
efficient way to find the minimizing h for a dependent dictionary.

## 5. Consequence for joint repair

The [branch-value identity](BRANCH_INTERSECTION_REPAIR.md) supplies joint
representations of many desired overlaps using one physical dictionary.
Equation (2) identifies two different costs that those representations retain:
forming the repeated pattern groups and computing the residual distinct-pattern
map. Discarding the latter would discard precisely the multi-output sharing
problem. Merely knowing that each desired value has a short representation
does not determine either jointly optimal term.

For two targets the residual has at most three nonzero patterns, and its exact
cost reduces to the single-shared-value formula above. For arbitrary numbers
of targets it is a genuine remaining linear circuit problem. Applying (5)
independently to many target pairs can count their shared gates repeatedly;
no additive pairwise lower bound is inferred.

These are general normal forms and exact continuation identities. They do not
improve the MixColumns interval 75-88, solve the optimization over joint lifts,
or permit replacing an actual dictionary by all vectors in its span.

The [specified checker](checks/check_joint_dictionary.py) verifies fixed joint
lifts before and after the common-offset prefix: 21 used members with three
patterns and 18 preparation gates initially, versus nine used members with
four patterns and five preparation gates afterward. The residual costs are
zero and three respectively. It also checks the displayed two-target shared
budget of seven gates against the independently proved common-offset lower
bound. The [saved result](checks/joint-dictionary-result.json) contains no lift
or helper search.
