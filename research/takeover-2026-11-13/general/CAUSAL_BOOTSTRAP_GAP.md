# The cost of starting: scalable gaps between cyclic systems and XOR circuits

2026-11-14. Structural hand proofs for unrestricted binary XOR circuits, with
arbitrary sharing, cancellation, depth, and fanout. No search or enumeration.
No literature-novelty claim, no new MixColumns numerical bound, and no formal
verification or human certification.

[Independent review](reviews/causal-bootstrap-gap-review.md) checks the causal
certificate, the exact three-arm and square results, and the general odd-arm
square theorem, including the projection and formal-variable arguments.

The historical [cyclic-system report](../../structure-2026-11-11/cyclic/REPORT.md)
distinguishes a system of independent three-term equations from a circuit that
can execute those equations one at a time. Its small examples show a one-gate
gap. The families below make the missing cost explicit and scalable: the
equations can explain all required values together, while producing the first
required value already needs many additional intermediate values.

Write `L(T)` for the minimum gate count on ordinary coordinate inputs computing
a target set `T`. Write `L_cyc(T)` for the minimum cyclic-system size, using the
historical definition: a set of distinct nonzero values containing the inputs
and targets, whose three-term relations span its whole relation space. All
inputs are coordinate units; arbitrary additional linear forms are not free.

## 1. A general first-target certificate

**Lemma.** Let `T` contain `m` distinct nonzero, non-input target values, each of
input Hamming weight at least `w`. Then every XOR circuit for `T` satisfies

    L(T) >= m+w-2.                                      (1)

Take the first produced target. Its ancestor cone contains no other target
value. If the cone has `g` gates and `s` coordinate input nodes, its underlying
undirected graph is connected and has `g+s` vertices and `2g` operand-edge
occurrences. Therefore `2g>=g+s-1`, so `g>=s-1>=w-1`.
Cancellation cannot create a dependence on an input absent from the cone, which
justifies `s>=w`. The other `m-1` target first occurrences lie outside that cone.
Adding these disjoint physical gate counts proves (1).

This argument uses causal first production. In a cyclic system, a target can
participate in the explanation of its own prerequisites, and there need not be
a first target. The bound is not asserted for cyclic systems.

## 2. Three arms: exact unrestricted and cyclic costs

Fix `k>=2`. Take `n=3k` coordinate inputs in disjoint lists

    A=(a_1,...,a_k), B=(b_1,...,b_k), C=(c_1,...,c_k).

Let `A_j=a_1+...+a_j`, and define `B_j,C_j` similarly, with all zero-index
prefixes zero. Put `p=A_k+B_k+C_k`. The target set is

    Q = {p} union {p+A_j,p+B_j,p+C_j : 1<=j<=k}.          (2)

These are `m=3k+1` distinct values. Their supports are all inputs minus a prefix
of one arm, so their minimum weight is `2k`. Write `q_(D,j)=p+D_j`, with
`q_(D,0)=p` identifying the three zero-index vertices. The graph of the three
arms has `3k` edges and `3k+1` vertices.

**Theorem.** For the full target set (2),

    L_cyc(Q)=3k+1,      L(Q)=5k-1.                       (3)

For a cyclic realization, take one relation per arm edge,

    q_(D,j-1)+d_j+q_(D,j)=0,

and the endpoint relation

    q_(A,k)+q_(B,k)+q_(C,k)=0.                           (4)

There are `3k+1` equations on the `3k+1` target unknowns. The edge equations
express every unknown as the common center plus its prefix. Substitution into
(4) gives `center+A_k+B_k+C_k=0`, so the center and every other unknown are
uniquely determined. The system is therefore cyclic of size `3k+1`; the target
count itself gives the matching lower bound.

Lemma (1) gives `L(Q)>=3k+1+2k-2=5k-1`. For attainment, first compute the endpoint
`p+A_k=B_k+C_k` by summing its `2k` inputs in `2k-1` gates. Walk from that
endpoint up its arm to `p`, then down the other two arms, adding the relevant
coordinate input at each step. This uses exactly `3k` further gates, one for
each remaining target. Thus the causal lower bound is attained.

The additional `2k-2` values used to prepare the first endpoint have weights
below `2k` and are not targets. They are precisely the cost omitted by the
cyclic explanation in this construction.

## 3. Square invertible maps and their inverses

Remove one endpoint from the required outputs:

    Q' = Q minus {p+C_k}.                               (5)

There are now exactly `n=3k` outputs. They are linearly independent. Indeed,
differences along their retained arm edges give all coordinate units except
`c_k`; the center `p`, also retained, has coefficient one on `c_k` and supplies
the missing dimension. Let `M_k` be the resulting invertible square map.

**Theorem.** For `k>=2`,

    L(M_k)=5k-2,      L_cyc(M_k)=3k+1,
    L(M_k^(-1))=3k+1.                                 (6)

The first-target lower bound is `3k+2k-2=5k-2`. The previous construction, omitting
the last step to the deleted endpoint, attains it.

Adding the omitted endpoint gives the previous cyclic realization, so
`L_cyc(M_k)<=3k+1`. To exclude size `3k`, a cyclic system of that size would have
to contain exactly the inputs and the `3k` target values, with no auxiliary value.
We classify all triples in that particular set directly from their supports:

- No triple has three input units, since the units are independent.
- No triple has two inputs and one target, since target weights are at least
  `2k>=4`.
- A triple with one input and two targets corresponds to targets differing in
  one coordinate. On one arm this means consecutive prefixes, including the
  center and its first vertex. Prefixes from different nonempty arms differ in
  at least two coordinates. Thus these triples are exactly the retained tree
  edges, of which there are `3k-1`.
- Three targets sum to zero only if their three removed prefixes sum to `p`.
  Every one of the three input blocks must be covered. Hence the targets must
  lie on the three different arms and all three prefixes must be full. This is
  exactly the endpoint triple (4), which is absent after (5).

There are only `3k-1` triples, whereas the relation space of the input/target
set has dimension `3k`. They cannot span it. Hence `L_cyc(M_k)>3k`, proving
the claimed exact cyclic cost without enumerating value sets or circuits.

For the inverse map, the new inputs are the vectors in `Q'`, and the requested
outputs are the original coordinate units. Compute the missing endpoint from
the two retained endpoints using (4), in one gate. Then compute each of the
`3k` original coordinate units as the difference across its arm edge. This
gives an inverse circuit of size `3k+1`.

The inverse cannot have size `3k`: that would use precisely the same boundary
value set, merely with the choice of inputs changed. The triples classified
above are unchanged under the invertible coordinate change, and their number
is still below the relation-space dimension. Such a set is not even cyclic.
This proves the inverse equality in (6), without assuming a general equality
between cyclic and causal complexities.

Consequently square invertible maps can have the exact gaps

    L(M_k)-L_cyc(M_k)=L(M_k)-L(M_k^(-1))=2k-3.

The gap grows linearly with the input dimension. This is an explicit family,
not a claim about the maximum possible gap or about MixColumns.

## 4. Odd numbers of arms give ratios approaching two

The primary agent observed a further extension. Let `r>=3` be odd, use `r`
disjoint arms of length `k>=2`, put `N=rk`, and let `p` be the sum of all inputs.
Require `p` and all values `p+D_j` along all `r` arms. There are `N+1` targets,
of minimum weight `(r-1)k`. The same first-target argument and traversal give

    L(Q_(r,k))=(2r-1)k-1.                               (7)

Write `q_i=p+D_(i,k)` for the `r` endpoints. Since `r` is odd,

    q_1+...+q_r=0.

In addition to the `N` arm-edge equations, encode this relation with `r-2`
three-term equations and `r-3` extra unknowns:

    z_2=q_1+q_2,
    z_j=z_(j-1)+q_j              for 3<=j<=r-2,
    z_(r-2)+q_(r-1)+q_r=0.

For `r=3`, use just the three-endpoint relation and no `z` variables. The arm
equations express the endpoints in terms of the center; their odd-length sum
then determines the center to be `p`, as before. Thus this is a uniquely
solvable system with `N+r-2` equations and unknowns.

For completeness, the additional values are distinct and nonzero: for even
`j`, `z_j` is the sum of the first `j` whole blocks; for odd `j`, it is the sum
of the whole blocks after `j`. These supports are distinct prefixes or suffixes
of between two and `r-3` blocks. They differ from every target, which omits a
prefix of at most one block, and from every input. Therefore

    L_cyc(Q_(r,k)) <= rk+r-2,
    L(Q_(r,k))/L_cyc(Q_(r,k))
      >= ((2r-1)k-1)/(rk+r-2).                           (8)

First letting `k` grow makes this lower bound tend to `2-1/r`; letting odd `r`
grow makes these ratios arbitrarily close to two. The next result gives exact
costs for the corresponding square maps. No universal upper bound of two, and
no counterexample to such an upper bound, is asserted.

## 5. Exact square maps with ratios approaching two

Delete the endpoint on the last arm from the `r`-arm target set, leaving
`N=rk` targets; call the square map `M_(r,k)`. As in the three-arm case, all
input units except the last unit of the last arm are differences of retained
adjacent target values, and the center supplies the missing dimension. Thus
`M_(r,k)` is invertible.

**Theorem.** For every odd `r>=3` and `k>=2`,

    L(M_(r,k)) = (2r-1)k-2,
    L_cyc(M_(r,k)) = L(M_(r,k)^(-1)) = rk+r-2.            (9)

The first-target bound gives the first equality's lower bound. Computing an
endpoint on another arm first, then traversing the retained target tree, gives
the matching construction: `(r-1)k-1` preparation gates and `rk-1` remaining
target gates.

For the inverse, its coordinate inputs are the retained target-tree vertices.
All but one of its requested outputs are the `N-1` edge differences of that
tree. The remaining output, the last original coordinate on the truncated arm,
is the sum of the `r-1` retained full endpoints and the truncated arm's final
retained vertex. Call this set of `r` inverse input vertices `S`. No two are
adjacent in the retained tree: each lies on a different arm, and `k>=2` keeps
all of them away from the center.

An inverse circuit first computes the omitted endpoint as the sum of the
`r-1` full endpoint inputs, using `r-2` gates. Every original input coordinate
is now obtained as an arm-edge difference, using `N` more gates. This gives
the upper bound `N+r-2`.

The following argument supplies a matching lower bound even for cyclic systems.
Consider any such inverse system of size `G`. Its `N` required output values
are distinct and non-input. Grant the `N-1` ordinary tree-edge outputs for free.
There remain `g=G-(N-1)` unknowns. The original square coefficient matrix on
all non-input unknowns is invertible, so its columns on these remaining
unknowns have rank `g`. Select `g` rows forming a basis on those columns.
After substituting the granted values, these rows form a uniquely solvable
system for the remaining unknowns. Each row still has at most three terms,
where a granted value counts as one known term.

Now project the inverse input coordinates outside `S` to zero. Every original
inverse input projects to zero or a coordinate unit. Since `S` is an independent
set of tree vertices, every granted edge difference also projects to zero or
a coordinate unit. The exceptional requested output becomes the sum of all
`r` remaining independent coordinates. The coefficient matrix on formal
unknowns is unchanged by this projection and remains invertible; unknowns with
coincident or zero projected values are retained as distinct formal variables.

An invertible `g`-unknown system of equations with at most three terms per row
cannot produce this `r`-coordinate sum from unit known terms with `g<r-1`.
Indeed, take the unique subset of rows whose unknown part is just that output
variable. Write `s` for the number of selected rows and `u` for the number of
unknown columns occurring in them. Row independence on unknown columns gives
`u>=s`. Every occurring unknown other than the output occurs at least twice;
the output occurs at least once. The known terms must contribute every one of
the `r` coordinates at least once. Counting all term occurrences gives

    3s >= 2u-1+r >= 2s-1+r,

so `g>=s>=r-1`. Consequently `G>=N+r-2`.

Finally, cyclic complexity is unchanged by exchanging the two boundary bases.
An invertible change of coordinates takes any value set containing the original
inputs and outputs to a set containing the inverse inputs and outputs; it
preserves triples, their relation span, and the size excess over `N`. Applying
this change in both directions proves equality of the two cyclic minima.
The inverse circuit upper bound and the inverse cyclic lower bound therefore
prove the second line of (9).

Thus the exact ratio for these square invertible maps is

    L(M_(r,k))/L_cyc(M_(r,k))
      = L(M_(r,k))/L(M_(r,k)^(-1))
      = ((2r-1)k-2)/(rk+r-2).

These ratios approach two by taking large odd `r` and then sufficiently large
`k`. The result establishes a lower limit on any proposed universal comparison
constant; it does not prove that two is a universal upper bound.

The [specified verifier](checks/check_causal_bootstrap.py) checks the single
instance `r=5,k=3`: a rank-fifteen square matrix, its 25-gate forward circuit,
its 18-gate inverse circuit, and its eighteen independent cyclic equations.
It also checks the selected independent vertex set and the projection used in
the lower-bound proof. The [saved result](checks/causal-bootstrap-result.json)
records success. This verifies only the displayed construction; the universal
claims and lower bounds are the preceding hand arguments. Run from the
repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/takeover-2026-11-13/general/checks/check_causal_bootstrap.py
```

## 6. Relevance and limits

These families show that independent, correct equations can omit a linear
amount of the work needed to start a computation. This is a causal obstruction
that does not restrict circuit depth, allowed cancellation, feedback patterns,
or the number of gates devoted to one chosen subproblem.

The first-target inequality alone is weak for MixColumns: its 32 target rows
have minimum weight five, giving only 35. It does not improve 75 and should not
be pursued as another numerical bound on that matrix. Its role is to isolate
what a stronger general method must retain: the cost of producing actual
operands before shared target relations become usable. Combining that cost with
shared-intermediate accounting remains an open task.
