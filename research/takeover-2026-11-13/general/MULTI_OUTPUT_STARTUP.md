# Shared preparation for several outputs, counted once

2026-11-14. Structural hand arguments for unrestricted binary XOR circuits.
Arbitrary sharing, cancellation, repeated values, fanout, and depth are allowed.
No circuit search or enumeration. No literature-novelty claim and no formal
verification or human certification.

[Independent review](reviews/multi-output-startup-review.md) checks the union
identity, the required-ancestor credits, the target-only profile, the sharp
families, and the explicit MixColumns limitation.

The [first odd target theorem](FIRST_ODD_TARGET_TRADEOFF.md) charges the work
needed before one required value appears. The extension here uses the union of
the first several target cones. Shared preparation appears once in that union.
Earlier required odd values receive their exact credit rather than being
charged again as helpers. A target-dependent support profile then gives an
unrestricted lower bound without specifying a circuit budget or shape.

## 1. Counts and an exact identity for a union of cones

Fix a nonzero parity functional `lambda` on the ordinary coordinate inputs.
Let `T_o` be the set of required non-input odd target values, and put `m=|T_o|>0`.
Distinguish the first occurrence of every value in `T_o`. In the whole circuit,
let `H` count all other odd gate occurrences and let `d` count even-plus-even
gates. A duplicate occurrence of a required value therefore counts in `H`.

Choose any nonempty collection of distinguished odd target occurrences and let
`C` be the union of their complete ancestor cones, including their roots.
Use the following counts, all confined to this one physical union:

- `O_C,E_C`: its odd and even gate occurrences;
- `a,f`: its distinct initially odd and initially even coordinate ancestors;
- `d_C`: its even-plus-even gates;
- `c`: connected components of its underlying undirected multigraph;
- `beta`: the cycle rank of that multigraph, with operand ports counted as edges;
- `B_e`: the sum of outdegree minus one over its computed even nodes and
  initially even input nodes, counting only uses inside `C`.

Every counted even node has a reader inside `C`, since all selected roots are
odd. Thus `B_e>=0`. Counting even operand ports gives exactly

    E_C+f+B_e = O_C+2*d_C.

Every gate retains both operand ports in the complete ancestor union. The
multigraph therefore has `2*(O_C+E_C)` edges and `O_C+E_C+a+f` vertices, giving

    beta=O_C+E_C-a-f+c.

Eliminating `E_C` proves

    2*(O_C+d_C)=a+2*f-c+beta+B_e.                         (1)

Now let `q_C` count all distinguished required odd occurrences inside `C`,
including those not selected as roots, and put `H_C=O_C-q_C`. Then

    2*(H_C+d_C)=a+2*f-c-2*q_C+beta+B_e.                  (2)

This is the correct required-target credit for an arbitrary cone union.
The number of selected roots cannot replace `q_C` unless there is a reason
that no other distinguished odd target is an ancestor. The identities allow
one selected target to be an ancestor of another. All physical nodes, shared
edges, and repeated operand ports are counted with their actual multiplicities.

## 2. A profile determined by the target supports

For a nonempty subset `S` of `T_o`, let `U(S)` be the union of its input
supports. Give each initially odd coordinate weight one and each initially
even coordinate weight two, and set

    omega(U)=|U intersect odd_inputs|+2*|U intersect even_inputs|.

Let `kappa(S)` count connected components of the target-overlap graph: vertices
are the targets in `S`, and two vertices are adjacent if their supports share
any input coordinate. Define

    b_lambda(S)=ceil((omega(U(S))-kappa(S)-2*|S|)/2),
    B_k=min_{S subset T_o, |S|=k} b_lambda(S),
    B_*=max_{1<=k<=m} B_k.                              (3)

These definitions describe a target invariant; no enumeration is used in its
proof. Useful lower estimates may instead be proved from support overlap or
other structural properties, as below. The one-target term is nonnegative.

**Theorem.** Every unrestricted circuit for the required targets satisfies

    H+d >= B_*.                                        (4)

More precisely, if `S_k` consists of its first `k` distinct required odd target
values to appear, then

    H+d >= b_lambda(S_k).                              (5)

**Proof.** Take the complete ancestor union of their distinguished first
occurrences. All `k` are in the union. No other distinguished required odd
occurrence can be in it: it would precede one of these roots and therefore
would already belong to the first `k`. Consequently `q_C=k` in (2), even if
some selected target is an ancestor of another or has repeated later copies.

Every supported input in `U(S_k)` is an ancestor, so `a+2*f>=omega(U(S_k))`.
If two target supports overlap, their cones share that coordinate-input node
and belong to one physical component. Hence `c<=kappa(S_k)`. Inputs or
intermediates that cancel can merge additional cones and only strengthen
this inequality. With `beta,B_e>=0`, equation (2) gives

    2*(H_C+d_C)>=omega(U(S_k))-kappa(S_k)-2*k.

Use `H_C<=H`, `d_C<=d`, and integrality to obtain (5). The actual `S_k` is
one subset in the minimum defining `B_k`, so `H+d>=B_k` for every `k`.
Taking their maximum proves (4). QED.

For `k=1`, this recovers exactly the preceding first-target bound
`(omega(z)-3)/2`. Several target groups are not charged separately: each
prefix uses one union of cones, and the resulting inequalities are maximized,
not added.

## 3. A support-rank interpretation and total gate cost

The quantity `omega(U(S))-kappa(S)` is a rank determined only by the targets.
Make one formal vertex per initially odd input and two per initially even
input. Replace each target support by its resulting weighted set of vertices.
On that set take the span, over `F_2`, of all pair-difference vectors of formal
vertices. The sum of these subspaces over `S` is the even-coordinate space on
each connected component of their union. Its dimension is

    rho_lambda(S)=omega(U(S))-kappa(S).

Thus (3) measures the expansion of this support rank beyond two per required
odd target. This is an auxiliary description of input overlap, not the span
of computed circuit values and not a supply of free operands.

To combine (4) with the [parity account](ODD_COMPONENT_DEFECT.md), let `s` be
the number of initially odd inputs, `r` the effective computed-even rank,
and `mu` the odd-graph cycle rank. Its exact accounting is

    G=m+r+H+d+mu.

Therefore the new theorem gives

    G>=m+r+B_*+mu,
    G>=m+max(t_e, s-c_max(T,lambda)+B_*),                (6)

where `t_e` counts distinct required nonzero non-input even values and `c_max`
is the maximum compatible input-partition size for the full required target
set. The maximum with `t_e` avoids charging even target gates twice. Bounds
from different parity choices may be maximized; no sum across parity choices
is asserted.

## 4. A general overlap estimate

Use total input parity, so all coordinate weights are one. Suppose every
required target has odd weight at least `w`, any two distinct target supports
intersect in at most `ell` coordinates, and every pair intersects nontrivially.
For any `k` targets, their overlap graph is connected. Also

    |U(S)|>=k*w-ell*binom(k,2).

This is the elementary union lower bound from the sum of individual sizes
minus pair intersections. A coordinate occurring `j>=1` times contributes
`j-binom(j,2)<=1` to that expression, so higher intersections do not invalidate
the lower bound. The theorem consequently gives

    H+d >= max_(1<=k<=m)
             ceil((k*(w-2)-ell*binom(k,2)-1)/2).         (7)

The right side need not be tight. It shows how a support-separation property
can force preparation for many outputs jointly, without knowing which outputs
appear first.

For a particularly direct family, take an even integer `v>=4`, one input per
edge of the complete graph on `v` vertices, and one target per vertex summing
its incident edge inputs. There are `m=v` odd targets of weight `w=v-1`; two
supports meet in exactly their shared edge. A `k`-target union has exactly

    k*(v-1)-binom(k,2)

inputs. Thus (3) is evaluated symbolically: its maximum is attained at
`k=v-3` or `k=v-2`, and

    H+d >= ceil(((v-2)*(v-3)-2)/4).                     (8)

The first-target theorem alone gives only `(v-4)/2`. The new preparation
bound grows quadratically in `v`, hence linearly in the number of inputs,
while the one-target bound grows only linearly in `v`.

This is not a claim of a new total gate-count result for that familiar family.
Its transpose computes all `binom(v,2)` pair sums, whose exact cost is their
number; ordinary circuit transposition gives the original exact cost
`2*binom(v,2)-v=v*(v-2)`. The role of (8) is to locate a substantial combined
cost in odd helpers and even-plus-even operations. Sharpness of (8) for those
two resources is not asserted.

## 5. Shared core and private preparation: a sharp family

Let a common core consist of `2a+1` input coordinates, with `a>=0`. For each
`i=1,...,m`, take a private group of `2b_i` further coordinates, with `b_i>=1`,
all private groups disjoint. Require the odd targets

    y_i = sum(core)+sum(private_group_i).               (9)

Every nonempty target collection has connected support overlap through the
core. For the full collection, the weighted union has size
`2a+1+2*sum_i b_i`, so (4) gives

    H+d >= a+sum_i (b_i-1).                            (10)

This is attained. Pair `2a` core inputs and add their pair values successively
to the remaining core input, computing the common odd core value `h`. This
uses `a` odd helpers and `a` even pair gates; if `a=0`, `h` is already an input.
Within private group `i`, form `b_i` even pairs and combine them with `b_i-1`
even-plus-even gates. One final odd gate adds that private parity to `h` and
produces `y_i`. Thus `H=a`, `d=sum_i(b_i-1)`, attaining (10) for all parameters.

The common core is paid once, while private preparation is paid per output.
The construction has `n-1` total gates, where `n=2a+1+2*sum_i b_i` is its input
count. This total is also optimal: the full ancestor union is connected through
the supported core inputs, includes all `n` inputs, and therefore has at least
`n-1` gates by the ordinary connected-DAG count.

For `a=1` and every `b_i=1`, this specializes to the preceding
[shared-helper amplification](SHARED_HELPER_AMPLIFICATION.md) family and gives
`H+d>=1` for every number of outputs. It does not falsely charge that one
shared odd helper once per target. With larger private groups, (10) exhibits
genuine additional preparation beyond the first-target requirement.

An alternative attaining implementation adds the private pair sums successively
to the common odd value. It has H=a+sum_i(b_i-1) and d=0, with the same total
binary cost. The [specified checker](checks/check_supply_certificates.py) verifies
this version at a=2 and (b_1,b_2,b_3)=(1,2,3): seventeen inputs, three outputs,
sixteen binary gates, and H+d=5. It also checks the single nested MixColumns
order used below. The [saved result](checks/supply-certificates-result.json)
contains these direct checks; the parameterized lower bounds remain hand proofs.

## 6. The total-parity MixColumns support profile is exactly one

The primary agent supplied the following explicit limitation, independently
checked from the repository's [row formula (3.1)](../../structure-2026-11-11/RECORD.md).
Under total input parity all 32 MixColumns rows are odd, and

    B_*(MixColumns, total parity)=1.                    (11)

For a hand certificate, order outputs by sheet `j=0,...,7` and within each
sheet by `c=0,1,2,3`. The row's own-block support is the triple `E_c`; its
other components are adjacent pairs `s_c` on the preceding block, with an
additional pair on block 7 for sheets 1, 3, and 4. Sheet 0 reads blocks 0 and 7.

The first sheet's prefix support sizes for `p=1,2,3,4` outputs are

    5, 7, 8, 8.

Every such prefix has connected support overlap, and its value in (3) is at
most one. After `j` complete sheets, for `1<=j<=6`, the union consists of
blocks `0,...,j-1` and block 7, with size `4*(j+1)`. The next `p` rows add only
coordinates of their own block `j`, at most `min(4,p+2)` of them. All foreign
blocks read by these rows are already present. Thus at `k=4j+p`,

    |U|<=4*(j+1)+min(4,p+2)<=2k+3.

Each newly added sheet intersects the preceding sheet's full own block, so
these prefixes also have connected overlap. In sheet 7 all 32 inputs are
already present and `k>=29`, again giving the same inequality. Hence every
prefix in this specified order satisfies

    ceil((|U|-1-2k)/2)<=1.

For each cardinality `k`, that one prefix is an admissible subset in the
minimum defining `B_k`, so `B_*<=1`. Conversely, the minimum MixColumns row
weight is five, which gives `B_1=1`. This proves (11) using a displayed nested
family of subsets, not a search over target subsets or circuits.

The eight bit-position blocks form a compatible parity partition: every row
is odd on its own block and even on every foreign block. Thus `c_max>=8` and
`s-c_max<=24`. With 32 odd targets, no even targets, and `B_*=1`, the standalone
target-only bound (6) under total parity cannot exceed `32+24+1=57`. It cannot
recover the existing 75 bound.

This ceiling applies to that separate parity-rank-plus-support-profile
certificate. It does not bound other parity choices, an argument coupling the
actual component rank to actual shared supply, or the full physical identity
with its cycle and fanout terms. The sharper general families above do not
justify extending this particular weak MixColumns certificate indefinitely.

## 7. Scope

The advance is a general target-dependent bound for unrestricted circuits,
not another fixed-budget or restricted-feedback classification. Its physical
basis is one union of actual ancestor cones; its causal step credits exactly
the required odd values that have already appeared. It allows a shared supplier
to help arbitrarily many later targets and counts that supplier once.

Support expansion alone may be weak when many targets have heavily overlapping
supports. Formula (2) retains the physical cycle and fanout terms that (3)
drops, but those terms are not automatically forced by the target supports.
Nor does (4) permit adding charges for arbitrary non-prefix output subsets.
Further strength would require an argument about actual supplied values or
the corresponding physical overlap, retaining their availability and cost.
No improvement to the unrestricted MixColumns interval is asserted here.
