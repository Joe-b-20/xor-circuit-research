# An unrestricted quadratic lift, and its 60-term MixColumns ceiling

2026-11-14. Structural identities and an explicit symbolic decomposition. No circuit
search or enumeration, no new MixColumns bound, and no literature-novelty claim.
This note records a general direction and a decisive limitation before investing
in stronger lower-bound estimates inside that relaxation.

## A target tensor charged once per physical gate

Let `V=F_2^n` have its ordinary coordinate basis `e_1,...,e_n`. Define the
coordinate-dependent quadratic lift

    q(v) = sum_(i<j) v_i v_j (e_i wedge e_j) in wedge^2 V.

Over `F_2`, `a wedge b=b wedge a`, and

    q(a+b)+q(a)+q(b) = a wedge b.                         (1)

Let the target map have rows `r_1,...,r_m`, with output-coordinate basis
`f_1,...,f_m`, and define

    T(M) = sum_j f_j tensor q(r_j).

For an arbitrary XOR circuit computing `M`, let `a_g,b_g` be the two input masks
of gate `g`, and let `u_g in F_2^m` be the influence of its result on all designated
outputs: its `j`th coordinate is the parity of paths from that result to output
`j`, including the trivial path when appropriate. Then

    T(M) = sum_g u_g tensor (a_g wedge b_g).               (2)

To prove this, insert the local defect (1) at each gate and propagate it through
the original linear circuit. Internal lifted values cancel by the same backwards
influence recurrence that defines `u_g`. At the inputs, `q(e_i)=0`; the remaining
boundary terms are precisely the lifted output rows. Equivalently, substitute
`q(a_g+b_g)=q(a_g)+q(b_g)+a_g wedge b_g` recursively at each output and collect
gate occurrences modulo two. Each physical gate contributes once with coefficient
`u_g`, regardless of fanout, sharing, cancellation, depth, or circuit size.

Define `R_wedge(M)` as the least number of terms in any decomposition

    T(M) = sum_(ell=1)^r u_ell tensor (a_ell wedge b_ell),

with arbitrary `u_ell in F_2^m` and `a_ell,b_ell in V`. Equation (2) proves

    L(M) >= R_wedge(M).                                  (3)

The relaxation permits arbitrary output influences and arbitrary parent masks,
chosen independently for different terms. It does not require those masks to
have been computed, the influences to come from one common network, or the
triples to admit a causal ordering. These missing compatibility conditions matter.

## A simple-bivector decomposition for an odd list

For any vectors `v_1,...,v_(2k+1)`, set

    Q(v_1,...,v_(2k+1)) = sum_(i<j) v_i wedge v_j.

Writing `s_(2j-1)=v_1+...+v_(2j-1)`, we have

    Q(v_1,...,v_(2k+1))
      = sum_(j=1)^k (s_(2j-1)+v_(2j)) wedge (v_(2j)+v_(2j+1)).  (4)

Indeed, adding the last two vectors changes `Q` by
`s_(2j-1) wedge (v_(2j)+v_(2j+1))+v_(2j) wedge v_(2j+1)`,
which is the displayed simple bivector. This proves (4) inductively, starting
with the empty sum for a one-vector list.

For an odd set `S` of coordinate indices of size `w`, formula (4) decomposes
`q(sum_(i in S)e_i)` into `(w-1)/2` simple bivectors. More usefully, let `T` be
any three-element subset of `S`, put `R=S minus T`, and put `s_T=sum_(i in T)e_i`.
Then

    q(sum_(i in S)e_i)
      = q(s_T) + q(sum_(i in R)e_i) + s_T wedge sum_(i in R)e_i.  (5)

The first term is one simple bivector by (4). The last two terms together are
`Q(s_T, (e_i)_(i in R))`, an odd list of length `w-2`, and use `(w-3)/2` simple
bivectors by the same formula. Thus the rowwise count `(w-1)/2` can be
attained while prescribing the three-coordinate term `q(s_T)` first. No minimum
claim for the full tensor is needed below.

## A specified 60-term decomposition for MixColumns

Use the standard eight blocks of four inputs, with `e_c` in block `j` denoted
`x_(c,j)` and `c` taken modulo four. The repository's
[row formula (3.1)](../../structure-2026-11-11/RECORD.md) is

    r_(c,j) = E_c on block j + s_c on block j-1
              + s_c on block 7 when j in {1,3,4},          j>=1,
    r_(c,0) = E_c on block 0 + s_c on block 7,

where `E_c=sum_(d!=c)e_d` and `s_c=e_c+e_(c+1)`.
Consequently all four rows of sheets `1,3,4` have weight seven, and all four rows
of the other five sheets have weight five. These are facts about the unrestricted
target matrix, not restrictions on a circuit.

For each sheet `j`, take the two row pairs `(c,c+1)` with `c=0,2`, and let
`a=j-1` for `j>=1`, or `a=7` for `j=0`. The pair shares the following three
input coordinates:

    T_(c,j) = { x_(c+2,j), x_(c+3,j), x_(c+1,a) }.         (6)

The first two belong to both own-block triples; the last belongs to both adjacent
pairs on block `a`. Apply (5) to each of the two rows with this common `T`.
Their common simple bivector `q(s_T)` becomes one tensor atom with influence
`f_(c,j)+f_(c+1,j)`. Every remaining simple bivector uses its own row's unit
influence. Thus a pair of weight-`w` rows uses

    1 + 2*(w-3)/2 = w-2

atoms, instead of the `w-1` obtained by keeping their decompositions separate.
There are two disjoint row pairs in each sheet. Therefore

    R_wedge(MixColumns) <= 5*(2*3) + 3*(2*5) = 60.         (7)

The displayed construction was also checked directly against the repository's
32-by-32 matrix in `circuits/aes-mixcolumns/aes-mixcolumns.mat.txt`: its sheet
weights are `5,7,5,7,7,5,5,5`, all sixteen prescribed triples (6) are contained
in both corresponding row supports, and the sixty prescribed tensor atoms sum
to all thirty-two quadratic rows. This was direct linear algebra for the
specified decomposition, with no optimization or enumeration.

The [specified verifier](checks/check_quadratic_lift.py) and its
[saved result](checks/quadratic-lift-result.json) make this check reproducible.
From the repository root run

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/takeover-2026-11-13/general/checks/check_quadratic_lift.py
```

## What this rules out

Even the exact value of `R_wedge` cannot prove a MixColumns lower bound above 60.
It cannot recover the existing 75 lower bound. Equation (2) handles unrestricted
cancellation and counts each physical gate once, but those properties alone do
not make its unconstrained atom model strong enough.

This is not a sixty-gate circuit: the decomposition grants arbitrary parent
linear forms without paying to supply them and grants output influences without
requiring a common realization. The lesson is to retain causal availability or
some equally substantive compatibility condition when turning conservation
identities into gate costs. Higher-degree lifts have formal local expansion
identities too; no claim is made here that they overcome this obstruction.
