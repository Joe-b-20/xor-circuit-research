# Adversarial review: flag transport, output credit, and the coordinate ceiling

2026-11-14. Independent symbolic review of
[FLAG_RELATION_TRANSPORT.md](../FLAG_RELATION_TRANSPORT.md), focusing on the
interval assertion, exact excess, chronological output order, sharp block
family, and bare-certificate ceiling. No circuit search, order enumeration,
SAT, or computer-driven case elimination was used. This is machine review,
not formal verification, human certification, or a novelty assessment.

**Verdict:** the mathematical claims reviewed below pass. The chronology
qualification is essential and makes the auxiliary-gate bound stronger than a
plain rank or output-count argument. The ceiling is a limit on the named bare
certificate, not a circuit upper bound and not a limit on the separate distance
correction.

## One gate may serve arbitrarily many cuts

A direct stress test starts with independent coordinates x,y,z_1,...,z_h and
targets t_j=x+y+z_j. For the nested subspaces
W_i=span(t_1,...,t_i), the initial relation space is
span(z_1+z_j:2<=j<=i), of dimension i-1. Thus every q_i is one. The single first
gate x+y adds t_1 as a new relation direction at every cut. It also advances
each of the h incomparable one-dimensional subspaces span(t_j), whose initial
relation spaces are zero. The targets themselves are independent. Neither
nesting nor target independence bounds the number of cuts improved by a gate.

The same phenomenon persists at arbitrary distance. Take h as a sum of D-1
private coordinate inputs, and targets h+z_j. Every nested target prefix has
q_i=1 and minimum escape word length D. The D-2-gate construction of h prepares
all prefixes at once, followed by one gate per target. Its exact total cost is
M+D-2 by the common-offset law. Thus even sharp individual distance bounds
cannot simply be added. The flag correction Phi=1 and Delta_*=D accounts for
this shared preparation exactly.

## Interval law and its physical endpoint

For one adjoined value v, choose the earliest flag index a at which v+u lies
in W_a for some old u, permitting u=0 as singleton notation. Fix w=v+u.
For every larger cut, all new pair generators differ from w by an old pair
generator in that cut's relation space. The enlarged relation space is therefore
R_i+span(w). Before a there are no new generators. Because the old R_i are
nested, w first belongs to them at some b>=a and remains there afterward.
This gives exactly one interval a<=i<b of rank increases, or none.

The endpoint b exists because R_k=V. The use of an actual gate is needed for
b<=j whenever v lies in W_j: its old operands already put v in R_j, and the
chosen u belongs to W_j as well. Arbitrarily granting an external new value
would preserve the interval property but need not preserve this endpoint
restriction. The source explicitly distinguishes these statements.

Zero outputs, repeated values, dependent supplied values, and repeated flag
spaces introduce no exception. They either add no generator or leave the
same interval reasoning valid. No intermediate support restriction appears.

## Potential and exact excess

The layer discrepancies sum to zero, so their positive sum equals half their
absolute sum. A transfer changes only two layer entries; the potential changes
by -1, 0, or +1. Equivalently, subtracting an interval indicator from the cut
deficiency profile changes only the two endpoint differences in its positive
variation. Final saturation makes the potential zero.

For a flag selected from actual first-production order, every selected output
gate has zero rank growth at all cuts: earlier cuts are already spanned by
available selected outputs, while later cuts contain the new output. This
is stronger than merely saying that each gate has bounded credit. It excludes
all M selected output gates from the preparation charge.

If N_down, N_up, and N_flat classify gates for a general flag by potential
change, then N_down-N_up=Phi(S). The stronger monotonicity claim for output
prefix flags also passes. After repeated spaces are omitted, every prefix
step has dimension one. Such a layer has c_i>0 exactly when a supplied
singleton or pair generator lies in W_i minus W_(i-1): if all its generators
lay in the earlier space, they would already generate R_(i-1). This witness
persists under every dictionary enlargement. An occupied layer therefore
cannot become empty, and its potential contribution is precisely [c_i=0].
The possibly larger appended V layer contributes no deficit because
c_i=d_i+q_(i-1)>=d_i. Hence Phi never increases for these flags, even under
arbitrary adjoining of dictionary values. The interval law limits a single
gate's decrease to one.

Thus N_up=0 in the chronological output-prefix setting. All M selected
first-production gates belong to N_flat, giving the simplified exact identity

    G=M+Phi(S)+(N_flat-M).

The neutral auxiliary count Z=N_flat-M is nonnegative. All terms are physical
counts, including useless or repeated gates. No reduced-circuit assumption is
hidden in this equality. Other required outputs are allowed and remain
auxiliary relative to the selected target collection. The general-flag
identity with 2*N_up is not incorrectly extended as a needed penalty here.

The added abstract-transport optimum is also correct. In the first positive
run [a,b) of q, the first layer is deficient and the layer immediately after
the run is surplus. Moving one unit from b to a keeps every layer nonnegative,
subtracts one only from positive q entries, and reduces Phi exactly once.
Repeating reaches c=d in Phi steps. This proves exactness only for the stated
rank relaxation, which deliberately forgets available values and parent gates.
It does not promise a circuit realizing those abstract transfers.

The lower bound may minimize the initial correction over target orders because
the actual first-production order is one of those orders. No arbitrary fixed
order can inherit zero output credit. The two-target counterexample in the note
correctly demonstrates that point. The minimum is a quantified theorem, not a
prescription to enumerate orders.

## Distance before any movement

Before the first gate changing any cut, the chosen successful cut retains its
initial relation space. Every earlier selected output lies inside that cut:
otherwise the chronological prefix spanning it would already be complete and
the cut could not grow. Thus all outside gates through the event are auxiliary.
The subspace absorption proof forces at least Delta_i-2 such gates. All except
the event precede every flag movement, so at least Delta_i-3 are neutral gates
in the exact excess term Z.

This validates the additive correction Phi+Delta_*-3. Its two terms must be
computed for the same order, and Delta_* is only defined when Phi>0. Both
qualifications are retained. The temporary grant of the initial relation space
remains a lower-bound relaxation, not physically free supplier preparation.

## Exact block family and interleavings

The four targets in the source form a basis, as its displayed reconstruction
of a,b,c,d verifies. Every singleton prefix has weight at least three, hence
zero initial relation rank. In any two-target prefix the third nonzero vector
is their difference and has weight one or two; it is the unique nonzero vector
of weight at most two in that two-dimensional space. Thus q_2=1. Every
three-target prefix is a coordinate-input hyperplane. Its quotient has exactly
one nonzero input color, so the initial relation rank equals the hyperplane
dimension and q_3=0. The full space gives q_4=0. Therefore every order has
profile (0,1,1,0,0), proved without listing orders.

For disjoint blocks, an output prefix is a direct sum of its local prefix
spaces. Initial relation generators split accordingly. A cross-block pair
of coordinates lies in that direct sum only if each coordinate belongs to
its own local prefix space; both then already belong to the block relation
spaces. It creates no additional cross-block direction. Hence the initial
R and q split as claimed.

An arbitrary interleaving changes only one block's prefix at each step. That
block contributes +1 exactly at its first target, -1 exactly at its third,
and zero at its second and fourth. Positive variation is therefore precisely
B for B blocks, regardless of interleaving. The lower bound 4B+B and the
specified five-gate block construction prove exact cost 5B. The lower argument
does not require the competing circuit to respect the block decomposition.

## Coordinate ceiling and its attainment for ordered flags

For a complete flag on n coordinate inputs, initial relation rank is n-t_i,
where t_i is the number of distinct nonzero coordinate colors. Thus
q_i=i-n+t_i. A positive deficiency step occurs exactly when t_i does not drop,
and contributes one. A quotient by a one-dimensional subspace has fibers of
size two, so counting the zero color gives

    t_i+1 >= ceil((t_(i-1)+1)/2),
    t_i >= floor(t_(i-1)/2).

After k strict drops the remaining count is at least floor(n/2^k). Reaching
zero therefore needs at least floor(log_2 n)+1=ceil(log_2(n+1)) strict drops.
The bare potential cannot exceed n-ceil(log_2(n+1)). For n=M=32 this limits
M+Phi to 58, even before minimizing over orders. This is not an assertion that
MixColumns has a 58-gate circuit.

The claimed ordered-flag attainment is also valid. The binary columns labeled
1,...,n contain the k coordinate powers of two and hence have rank k, where
k=ceil(log_2(n+1)). They are distinct and nonzero, so their kernel has no
weight-one/two vector. A flag beginning with a kernel basis consequently has
n-k plateau steps. Exactly k steps remain to reach zero colors, all of which
must drop. This constructs an ordered flag attaining the ceiling; it does not
prove attainment after order minimization for a fixed target basis. The source
states that distinction and excludes the distance correction from this ceiling.

## Fixed-weight path barrier, including every target subset

The revised source uses common-anchor path triples t_i=a+x_i+x_(i+1), all
of coordinate weight three. A natural i-edge prefix has no coordinate
singleton in its span, and its weight-two vectors are precisely same-parity
endpoint pairs. The two-step pairs x_j+x_(j+2), 1<=j<i, generate these on two
disjoint chains and have rank i-1. Thus q_i=1 throughout, Phi=1, and Delta_*=3.
The full target certificate is m+1, whereas the known common-anchor theorem
gives exact unrestricted cost m+ceil(m/2). This example no longer relies on
an increasingly long final target.

The all-subsets statement is valid. A selected p-edge subgraph of a path has
c nonempty components and p independent target rows. Initial short relations
within each component have rank one less than its edge count, totaling p-c.
There is no cross-component pair relation: any nonempty edge subset in each
component has at least two boundary vertices, so using two components cannot
produce coordinate weight two. The shared anchor does not alter that boundary
argument. Therefore the full selected prefix has deficiency c, forcing
Phi>=c. Processing the selected components consecutively attains Phi=c, and
the first target forces Delta_*=3 in every ordering.

Its minimized certificate is consequently p+c. At least c-1 omitted original
path edges separate its components, giving p+c<=m+1. The full selected set
attains equality. Thus maximizing the stated certificate over every subset
still gives m+1. Omitted target gates cannot simply be added: they may be
auxiliary gates that advance the chosen flag. This is a limitation of the
specified target-only certificate, not of all subspace arguments or all
unrestricted lower-bound methods.

The linked common-anchor theorem is explicitly attributed to Boyar, Matthews,
and Peralta. The source's all-odd invertible embedding is valid: keep a and
x_1 as identity outputs, and recover x_(i+1)=t_i+a+x_i successively. Accessible
relation closure continues to mean computability by additional inside gates,
not physical free supply.

The note makes no new numerical MixColumns claim. Its general mechanism,
exact examples, all-subsets barrier, and named bare-certificate ceiling are
mutually consistent.
