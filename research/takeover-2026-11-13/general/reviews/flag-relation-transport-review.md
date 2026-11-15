# Independent review: chronological flag transport

2026-11-14. Reviewer: independent `sparse_closure` agent. This is an independent mathematical machine review, not formal verification, human certification, or a literature-novelty assessment.

Reviewed [FLAG_RELATION_TRANSPORT.md](../FLAG_RELATION_TRANSPORT.md), reconstructing the interval law, exact potential ledger, production-order restriction, startup correction, sharp block family, and ceiling on the bare certificate. The review used structural proofs, not circuit search or output-order enumeration.

## Verdict

The main theorem and all reviewed consequences are sound. No consequential gap was found. The crucial distinctions are maintained: the flag is chosen from each competing circuit's actual production order, a flag-rank change need not decrease the potential, and the ceiling on the bare rank potential does not bound the separate distance correction.

## Interval and potential

For an old actual dictionary D, adjoin zero only as notation for singleton generators. If a new nonzero v is not already supplied, let a be the earliest flag index containing v+u for some u in D union {0}, and fix w=v+u. Every other new generator v+u' in a later W_i differs from w by the old two-term W_i relation u+u'. Thus each new relation space is old R_i plus span(w). The old R_i are nested, so w is absent until its first old membership index b, then present forever. The rank increases occur exactly on [a,b). Since the terminal space is V, this membership index exists.

The actual binary gate expression is necessary for the endpoint condition. If v belongs to W_j, its old parents show v already belongs to R_j. Since a<=j and w belongs to W_j, the fixed old u=v+w also belongs to W_j. Therefore w belongs to R_j and b<=j. Zero and repeated gate values leave every relation space unchanged while remaining physically charged.

Taking successive rank differences moves one unit from layer b to layer a. Both layer profiles sum to dim V, so the positive variation Phi is exactly half their L1 discrepancy. One transport changes Phi by at most one, and the exact identity G=Phi_initial+2*N_up+N_flat follows from the final value zero. Gates with zero potential change can still transport rank; the draft correctly keeps them in N_flat.

The added exact abstract-relaxation claim is also valid. At the beginning a of a positive run of q, the layer deficit is positive; at its ending b the layer surplus is positive. Transferring one unit b to a keeps the donor count nonnegative and subtracts one only from strictly positive prefix deficits. The positive variation decreases by exactly one. Iteration reaches zero in Phi moves. This establishes an optimum for the expressly relaxed layer problem; it makes no assertion that the moves have legal circuit operands or endpoints.

## Chronological output credit

For the flag of required target prefixes in actual first-production order, the first gate producing target t_j cannot increase any R_i. Earlier prefixes are already spanned by previously available targets; later prefixes contain the gate value. This remains true for linearly dependent targets, repeated prefix spaces, dependent initial dictionaries, and circuits producing additional unselected outputs.

There is a stronger monotonicity property on these flags. Every strict target-prefix step has dimension one. Its layer c_i is positive exactly when the current dictionary has a singleton or pair value in W_i outside W_(i-1): if no such generator exists, the definitions give R_i=R_(i-1); if one exists, it cannot belong to R_(i-1). Once this witness exists it remains in every later dictionary, so c_i cannot return to zero. Its potential contribution max(0,1-c_i) is exactly the indicator that the layer is empty. Repeated prefix steps contribute zero. The final jump to V contributes zero as well, because c_final=dim V-dim R_M>=dim V-dim W_M=d_final. Thus Phi is nonincreasing, and the interval law permits at most one formerly empty layer to activate per gate. This argument applies to any such one-dimensional-step flag; chronology is needed separately for zero output credit.

Exactly M selected first-production gates are flat. Consequently N_up=0 and subtracting them from N_flat yields the sharper exact account G=M+Phi_initial+Z. Exactly Phi_initial gates activate formerly empty prefix layers, while every other auxiliary gate contributes to Z. This is an exact count, not a heuristic allocation. A target-only bound must minimize over possible output orders. The two-target example t=a+b+c, u=a+b correctly demonstrates why maximizing over a convenient order is invalid.

## Startup distance

When Phi_initial>0, some cut is initially unsaturated and some later gate must change a flag relation space. At the first such gate, choose an affected W_i. Every previously produced selected target lies in W_i: if t_j outside W_i had already appeared then j>i, so all prefix targets through i had already appeared and W_i would be saturated, contradicting its current rank growth.

Consequently every outside-W_i gate through that event is auxiliary. The independently reviewed subspace first-collision argument requires at least Delta_i-2 such gates. All except the current event precede every flag-rank change, so at least Delta_i-3 auxiliary gates are flat and contribute to Z. This proves G>=M+Phi+Delta_*-3. It is harmless if the first event itself is flat rather than decreasing Phi; the exact ledger already charges that possibility. The monotonicity result rules out an increase on these prefix flags. If Phi=0, no first event or Delta_* is asserted. The order-dependent distance and potential must be kept together when taking a minimum.

For one D-coordinate parity, the parameters M=Phi=1 and Delta_*=D give exactly D-1 gates. For the complete retained common-offset dictionary, every nonempty target prefix has the even-combination relation subspace, giving Phi=1 and Delta_*=2r+1. The stated exact continuation cost follows.

## Exact block family

The four displayed targets form a basis by the displayed inverse expressions. Every target has weight at least three, and each pair's difference has weight one or two. A two-target span therefore has precisely one independent short relation. Every three-target span is a coordinate-input hyperplane; all such hyperplanes are already generated by their weight-one and weight-two members. Hence the deficiency sequence is (0,1,1,0,0) for every target order.

For disjoint coordinate blocks, an initial short relation crossing two blocks belongs to the direct-sum prefix space only when its individual coordinate components already belong blockwise. This proves the initial closure decomposes as a direct sum. An interleaved output order changes only one block's local deficiency at each step, producing exactly one positive increment per block. Thus Phi=B for every global order. The bound 5B and the supplied 5B-gate construction prove unrestricted optimality while allowing competing circuits to mix blocks freely.

## Bounded-weight path barrier and all selected subsets

For t_i=a+x_i+x_(i+1), a target combination has x-support equal to the boundary of selected path edges and anchor coefficient equal to their number modulo two. A nonempty edge subset has at least two boundary vertices. A weight-two target combination must be one even-length subpath. Its two-step endpoint pairs span a forest of rank i-1 on a natural i-edge prefix, proving q_i=1. Each first selected target supplies an unsaturated cut with escape length three, while every unsaturated cut has escape length at least three. Thus Delta_*=3 for every output order, and the natural order attains Phi=1.

The exact cost m+ceil(m/2) is correctly attributed to the known common-anchor graph theorem. Independently, the parity-partition proof gives it directly: if the anchor block contains k path vertices, at most 2k path edges touch that block. Every other block B can cover only internal path edges, at most |B|-1. Compatibility therefore implies m<=2k+sum_B(|B|-1)<=2r. The even-gate rank bound gives at least ceil(m/2) even gates in addition to the m odd targets. Alternating-vertex anchor helpers attain the bound.

For an arbitrary selected p-edge path subgraph with c nonempty components, each component contributes its number of edges minus one to the initial short-relation rank. Relations cannot join different components with only two coordinate terms. Hence final selected-span deficiency is c, forcing Phi>=c, and extending each component consecutively attains equality. There are at least c-1 omitted separating edges, so p+c<=m+1. The full selected set attains m+1. Unselected output gates cannot be added separately because the selected-flag proof treats them as auxiliaries that can contribute progress. This verifies the all-subsets limitation precisely as stated.

Retaining a and x_1 and replacing every x_(i+1) by t_i gives an invertible triangular recovery x_(i+1)=t_i+a+x_i. All output rows are odd. Thus the barrier applies to square invertible all-odd maps and to targets of uniformly bounded weight.

## Bare-potential ceiling

For a complete coordinate-input flag, q_i=i-n+t_i, with t_i the distinct nonzero initial quotient colors. Passing to the next quotient cannot increase t_i and can merge at most two old colors in one fiber. Including zero yields t_i>=floor(t_(i-1)/2). To descend from n to zero requires at least ceil(log_2(n+1)) strict-drop steps; the other steps are exactly the positive increments counted by Phi. This proves Phi<=n-ceil(log_2(n+1)).

The proposed attainment construction is valid: binary column labels 1 through n are nonzero, distinct, and span k=ceil(log_2(n+1)) dimensions. Their kernel has dimension n-k and no nonzero word of weight one or two. Beginning the flag with that kernel's basis gives n-k plateau steps; the remaining k steps must all drop. This concerns some ordered flag, not the minimum over orders of a fixed target set.

For n=M=32 the bare bound M+Phi is consequently at most 58. No ceiling on the distance-augmented bound is inferred. The present theorem supplies a rigorous way to count chronological relation preparation, but does not itself improve the numerical MixColumns bound.
