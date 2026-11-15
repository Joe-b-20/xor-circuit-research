# XOR structural research: checkpoint, 2026-11-14

Branch: `research-2026-11-13-structural`. This phase continues reviewed commit
`4136cf8`. Original base: `e89b8a25f69195266f1e24e815cb96c7526a3511` on
`phase-2026-11-09`. Isolated worktree: this chat's `work/xor-structural`.
Other worktrees and `search/proposals/` remain preserved.

## Direction

General unrestricted structural arguments take priority over incremental numerical
bounds and restricted casework. The fixed-budget queue is deferred. No SAT,
circuit/order/representation search or computer-driven case elimination. Symbolic
proofs, supporting linear algebra and specified construction checks are allowed.
Read [the synthesis](general/README.md) first.

## Exact nested credit and monotone output-layer activation

[Flag relation transport](general/FLAG_RELATION_TRANSPORT.md). For actual
supplied dictionary D and flag 0=W0<=...<=Wk=V, R_i is the span of dictionary
words of length at most two lying in W_i. Put r_i=dim R_i, layer dimensions
c_i=r_i-r_(i-1), d_i=dim W_i-dim W_(i-1), and q_i=dim W_i-r_i.

One new value changes r_i on a single interval [a,b), by one throughout. Thus
it moves one unit of layer rank from b to a. If this is an actual XOR gate
and its output belongs to W_j, then b<=j. Define

    Phi=sum_i max(0,q_i-q_(i-1))=(1/2)*sum_i |d_i-c_i|.

For general flags Phi changes by -1,0,+1. Exactly Phi abstract leftward rank
moves suffice if actual dictionary/parent restrictions are discarded; the greedy
proof fills the first positive run of q from its ending surplus layer.

For output-prefix flags every strict output step is one-dimensional. A layer
is occupied iff some current dictionary word of length <=2 lies in W_i outside
W_(i-1). That witness persists under all dictionary growth. Phi therefore
counts empty output layers and NEVER increases. The appended V layer is never
deficient. Each gate activates at most one previously empty output layer.

Choose the flag from M selected absent targets in their ACTUAL first-production
order. Every selected output gate has zero credit: earlier prefixes are already
spanned, later ones contain its value. Hence the exact unrestricted identity is

    G=M+Phi_initial+Z,

where Z counts auxiliary gates preserving Phi. Other required outputs count
as auxiliaries if not selected. Dependent targets and dictionaries are allowed.
For a target-only bound minimize Phi over possible orders; a favorable order
cannot be imposed on competitors.

If Phi>0, let Delta_* be the minimum initial escape word length W_i minus R_i
among unsaturated cuts. Before the first rank movement all earlier outside-W_i
gates are auxiliary, forcing Z>=Delta_*-3. Thus G>=M+Phi+Delta_*-3; both terms
must come from the SAME order. If Phi=0 use correction zero. This recovers
single-parity and common-offset costs. No order enumeration is prescribed.

Sharp family: each four-input block requires abc,abd,abcd,bcd. Every within-block
order has q=(0,1,1,0,0). Initial closures split over disjoint blocks, so every
interleaving of B blocks has Phi=B; exact unrestricted cost is 5B for 4B outputs,
including competitors mixing blocks. For coordinate complete flags,
Phi<=n-ceil(log2(n+1)); the bare 32-output certificate is at most 58. This bound
excludes the distance correction and does not bound circuit complexity.

## A known exact law and a general certificate barrier

[Common-anchor graphs](general/COMMON_ANCHOR_GRAPH.md). On inputs a,x_v and
simple graph F, require t_uv=a+x_u+x_v for every edge. The exact cost

    L=m+tau(F)

is ALREADY KNOWN: Boyar–Matthews–Peralta, January 2011 manuscript, Section 3.1.1,
Lemma 1, linked in the note. Our proof recovers the binary case through parity
partitions: from any compatible partition, select all vertices in the anchor
block and all but one in every other block. This is a vertex cover of size
r=n-#parts. Thus even rank and even gate count are at least tau; a cover gives
actual anchor-pair helpers attaining m+tau.

Every optimum has rank tau, H=d_EE=mu=0, exactly m odd gates and tau independent
even gates. This does NOT force algebraic cancellation-free wiring or anchor-pair
helpers. The five-gate triangle example cancels x_2 and uses only vertex-pair
helpers. Preserve that distinction.

For any selected edge set J, its initial target-span deficiency is c(J) when
its graph is bipartite (c counts active components), and zero if any odd cycle
exists. In the bipartite case short relations are within-side coordinate pairs;
in the nonbipartite case the anchor belongs to the span and all edge pairs become
short generators. This is accessibility, not free physical computation.

The minimum chronological Phi is c(F) for bipartite F and one for nonbipartite
nonempty F. Delta_*=3. On EVERY connected graph, even maximizing the
order-minimized, distance-augmented certificate over all selected target subsets
gives exactly m+1: a selected p-edge bipartite graph has at most m-p+1 active
components, and a nonbipartite selection gives p+1. The true cost is m+tau(F).

For a path, L=m+ceil(m/2) while this certificate stays m+1; all targets have
weight three. Retaining a,x_1 as identity outputs makes an all-odd square
invertible map. This limits the named raw certificate, not all subspace methods
or an argument first establishing a useful circuit normalization.

## Evidence and next direction

Both notes have independent machine reviews and primary-agent proof checks.
[Specified checks](general/checks/check_flag_and_anchor.py) and
[saved results](general/checks/flag-anchor-result.json) verify interleaved blocks,
a seven-edge path, a cancelling triangle, and actual chronological rank accounts.
No order, subset, representation or circuit search. Reviews are not formal
verification, human certification or literature-novelty assessments.
[Final scope review](general/reviews/flag-anchor-progress-review.md).

Next: the physical cost of supplying multiple useful representatives after
relations are already accessible. Couple actual supply with parity partitions
or stronger dictionary structure, without double counting. Nested rank credit
is now understood; non-nested overlap remains open. Avoid merely refining the
flag rank statistic, which has the explicit graph-family barrier above.
Unrestricted MixColumns remains 75<=L<=88, with no assumption that 88 is optimal.

Retain [subspace preparation](general/SUBSPACE_PREPARATION.md),
[Sidon supply tradeoff](general/SIDON_SUPPLY_TRADEOFF.md),
[joint dictionary normal form](general/JOINT_DICTIONARY_NORMAL_FORM.md),
[common-offset preparation](general/COMMON_OFFSET_PREPARATION.md), and
[odd-component account](general/ODD_COMPONENT_DEFECT.md). Rank, supplied values,
and physical gates are different; remaining cost excludes already paid prefixes.
History: [summary](SUMMARY.md), [record](../structure-2026-11-11/RECORD.md).
Use Git with `-c core.filemode=false`; stage only intended research files.
