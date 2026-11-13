# Two tempting interface inferences that fail

2026-11-13. Explicit symbolic constructions, not circuit search. These controls were checked while developing the compatibility proofs. They are not lower-bound results.

## Two even helpers need not span the all-ones mask

A minimum six-gate circuit for the four triples can use two overlapping pairs:

    p=b0+b1,
    q=b0+b2,
    E3=b1+q,
    E2=b3+p,
    E1=b3+q,
    E0=E2+q.

All four targets are correct. The span of its two even helper values is
`{0, b0+b1, b0+b2, b1+b2}`, which excludes `b0+b1+b2+b3`.
Thus a six-gate transpose is not restricted to complementary pairs or to a pair plus
the all-ones mask. The proofs in [QUOTIENT](QUOTIENT.md) use only the valid fact that
there are two distinct nonzero even helper values, not a particular geometry of their span.

## Three independent pure even suppliers do not force an eleventh gate

This ten-gate construction is already recorded in the earlier
[foundational review](../reviews/foundations-audit.md). With the free block `a`, let
`s_i(a)=a_i+a_(i+1)`, `d_i(a)=a_i+a_(i+2)`, and `t(a)=a0+a1+a2+a3`.

    p=b0+b1,
    r=b0+b2,
    s=b1+b3,
    h=b3+s1(a),
    v=p+d1(a),
    U1=r+h,
    U2=h+v,
    h'=U1+t(a),
    U3=s+h',
    U0=v+h'.

The four final values are `U_c=E_c(b)+s_c(a)`. For the free parts the identities are
`s1+d1=s2`, `s1+t=s3`, and `d1+s3=s0`. The own-part identities give the four respective
triples directly. The three initially computed pure-own masks `01,02,13` are independent:
coordinate 2 isolates `02`, coordinate 3 isolates `13`, and then `01` remains.
Every gate is live, and all ten physical values are distinct.

Consequently, needing a rank-three basis of pure even own-block values does not by itself
increase the ten-gate sheet minimum. This is different from requiring three diagonal
suppliers, whose exact 11-versus-12 cost is open. It also does not contradict the
source-saturation theorem: a basis of three pairs is weaker than all four prescribed
cycle pairs, and that theorem requires several alternative complete row sets.

The [direct checker](check_compatibility.py) evaluates these two specified circuits along
with the compatibility constructions; no families of circuits are generated or eliminated.
