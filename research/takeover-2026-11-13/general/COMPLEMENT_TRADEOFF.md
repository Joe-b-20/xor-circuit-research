# Complement sums: an unrestricted tradeoff with an exact frontier

2026-11-14. Structural hand proofs and specified symbolic constructions; no circuit search or enumeration. The independent review is [here](reviews/complement-tradeoff-review.md). This is machine review, not formal verification or human certification. The elementary ancestor-cone counting argument is basic graph accounting; no literature-novelty claim is made for it or the resulting circuit complexity formula.

For n inputs, let J be their full XOR and require every complement sum y_i=J+x_i. For every n>=4,

    L(y_1,...,y_n)=2n-2.

For even n=2k this yields a sharp, unrestricted relation between odd helper gates, even-rank requirements, and dependent even work. At the minimum possible even rank, every division of the remaining cost between odd helpers and dependent even gates is attained. Thus dependent even work can replace odd helper work one gate for one gate, while the total optimum stays fixed.

## 1. An exact ancestor-cone identity

Consider any binary XOR circuit on coordinate inputs, with free fanout and no free non-coordinate values. Fix a nonzero output value of support size w. Retain its complete physical ancestor cone. Let g be the number of gates and t the number of distinct coordinate inputs in this cone. Let beta be the cycle rank of its underlying undirected multigraph, keeping both operand edges even if they are parallel.

The cone is connected, has g+t vertices, and has exactly 2g operand edges. Therefore

    beta = 2g-(g+t)+1 = g-t+1,
    g = (w-1)+(t-w)+beta.                                 (1)

All w supported coordinates are ancestors, so t>=w. In particular g>=w-1. The excess has two precise sources: input coordinates that appear among the ancestors but cancel from the output, and undirected cycles caused by repeated use inside the cone. Indeed beta is also the sum, over all non-root cone nodes, of their number of uses in the cone minus one.

If g=w-1, then t=w and beta=0. The underlying multigraph is a tree. Every non-root node has exactly one use in the cone, and each of the t coordinate inputs occurs only once in its rooted binary formula. The two child supports at every gate are disjoint. Consequently all cone-node supports form a laminar family: two are disjoint or one contains the other.

This equality characterization uses physical occurrences. It makes no cancellation-free assumption about the circuit in advance.

More generally, suppose the circuit has m distinct required non-input target values, and choose the first appearance of any target as the cone root. Every other target first appears outside this cone. If alpha is the number of other gate occurrences outside the cone after reserving one occurrence for each of the remaining m-1 targets, then

    G = m+w-2+(t-w)+beta+alpha,       alpha>=0.             (2)

Here alpha includes any additional target copies as well as non-target gates outside the cone. Formula (2) is exact for that chosen first target. It does not assume the different output cones are disjoint.

## 2. Exact complexity of all complement sums

Let n>=4 and require

    J=x_1+...+x_n,       y_i=J+x_i   (1<=i<=n),

where J is notation, not an additional required output.

**Upper bound.** Compute y_1 directly in n-2 gates. Compute J=y_1+x_1 in one more gate. Then compute each remaining y_i=J+x_i in one gate. Total:

    (n-2)+1+(n-1)=2n-2.                                  (3)

The first requested output itself helps produce the common shared value.

**Lower bound.** Choose the first target appearance, say y_i. Its weight is n-1, so its ancestor cone has at least n-2 gates. The other n-1 target values appear outside that cone. Hence G>=2n-3.

Suppose equality holds. By (1), the cone is a binary formula tree on exactly the n-1 inputs other than x_i, and its node supports are laminar. Every gate outside that cone is one of the remaining targets; there is no budget for another helper.

Consider the first target y_j produced outside the cone. It contains x_i. The only currently available value containing x_i is the input x_i itself, because all earlier non-input values lie in the cone. Therefore this gate must add x_i to the already available value

    q_j = y_j+x_i = J+x_i+x_j.

This value has support size n-2. It is a proper subtree value of the cone. There is at most one such subtree: two different subsets of size n-2 inside an (n-1)-element set overlap for n>=4 and neither contains the other. Moreover q_j must be a child of the cone root, with the singleton x_j as the other child. Otherwise its path to the root would add at least two leaves.

Now consider the next distinct target y_l, with l different from i and j. The available values containing x_i are precisely x_i and y_j. Since y_l contains x_i, exactly one of its operands must be one of those two values.

- Using x_i requires q_l=J+x_i+x_l. That is a second subtree of size n-2, which does not exist.
- Using y_j requires y_j+y_l=x_j+x_l. This pair crosses the root split between the singleton x_j and the q_j subtree. It is not a subtree value: the only node containing x_j together with any other leaf is the full root of size n-1>=3.

Neither required second operand is available. A sum of the two x_i-bearing values cancels x_i and also cannot give y_l. Thus the circuit cannot produce this next target, a contradiction. Equality at 2n-3 is impossible, proving G>=2n-2. Together with (3), this proves the theorem.

The small cases differ: n=2 is just an input permutation and costs zero; n=3 has its three pair sums and costs three. They are not included in the theorem.

## 3. The general odd/even cost identity specializes to a joint inequality

Now let n=2k>=4 and use total input parity. Every y_i is odd. Use the notation of [ODD_COMPONENT_DEFECT](ODD_COMPONENT_DEFECT.md):

- E is the number of even gates;
- r is the rank of their values;
- c is the component count of the odd-occurrence graph, so r=n-c;
- delta=E-r is the number of even gates beyond that rank;
- H counts odd gate occurrences beyond one occurrence of each of the n required targets.

All these counts belong to an arbitrary unrestricted circuit for this target family. In particular,

    G=n+H+(n-c)+delta.                                    (4)

The compatible-partition condition gives c<=k. To see this, let p record the parities of the sizes of the c input parts. For an input index i in part a, the target y_i has part-parity vector p+e_a, and this must be a unit vector. If c>=3, this condition for every part forces p=0: a nonzero p has even weight; if its weight is two, any third part produces weight three, and if its weight is at least four no one-coordinate toggle can give a unit vector. Thus every part is even and c<=n/2. If c is one or two, c<=k holds directly.

The general [first-odd-target theorem](FIRST_ODD_TARGET_TRADEOFF.md) gives a stronger joint inequality directly. Let d count even-plus-even gates and mu the odd-graph cycle rank, so delta=d+mu. Every required target has weight 2k-1. Hence every unrestricted circuit satisfies

    H+d >= k-2,       H+delta >= k-2.                     (5)

This bound holds for every c. Inserting it in (4), and using c<=k, proves G>=2n-2 again without the tight-budget argument of section 2. The exact cost decomposition is

    G-(2n-2) = (k-c) + (H+d-(k-2)) + mu.                 (6)

Each term on the right is nonnegative. Therefore every optimal circuit has c=k, H+d=k-2, and mu=0. In particular its dependent-even defect is exactly d. Extra even rank cannot replace the first-target requirement for combined odd and even-plus-even work.

The weaker consequences H+delta>=c-2 and H+(k-c)+delta>=k-2 also follow, but (5) is the stronger unrestricted statement. No particular component partition, independent even values, fixed gate budget, or special intermediate-value structure is assumed.

## 4. Every split between odd helpers and dependent even work is optimal

Fix two distinct input indices a,b. Pair the other 2k-2 input indices into k-1 pairs, and compute their pair sums p_1,...,p_{k-1}. Choose an integer j with 0<=j<=k-2.

First combine p_1,...,p_{j+1} into S with j even-plus-even gates; when j=0 use S=p_1 without a gate. Starting from x_b, add S and then the remaining pair sums p_{j+2},...,p_{k-1} one at a time. The final odd accumulator is

    y_a = x_b + p_1+...+p_{k-1}.

This uses k-j-1 odd gates, including y_a, so there are H=k-j-2 odd helpers. Compute

    J=y_a+x_a

with one even gate, then all other y_i=J+x_i with n-1 odd gates.

The even gate values are the k-1 disjoint pair sums, their j selected aggregate values, and J. The pair sums together with J are independent: only J has nonzero coefficients on x_a and x_b. Every selected aggregate is in their span. Therefore

    r=k,       c=k,       E=k+j,       delta=j,
    H=k-2-j,  H+delta=k-2,
    G=2n-2.                                               (7)

Every parameter choice attains the unrestricted optimum. At one endpoint, delta=0 and H=k-2: the odd accumulators perform all the combination work. At the other, H=0 and delta=k-2: even-plus-even gates combine the pair sums before the first target is made. Intermediate choices exchange one odd helper for one dependent even gate.

The odd graph has no cycles in these constructions. The dependent-even defect is entirely the j even-plus-even gates. This verifies that the two counts being traded are physical gates of the indicated types, not virtual ranks or projected values.

## 5. What this contributes to the unrestricted program

This is an exact scalable example of the combined-cost principle. Minimizing even rank alone does not determine the total cost; dependent even gates can reduce the necessary odd helper population. The combined inequality controls both alternatives and is attained across the whole interpolation.

For even n, its lower bound now follows directly from the general first-odd-target inequality together with the parity rank requirement. This proof couples the two resources without a fixed-budget classification. The earlier ancestor-tree proof remains an independent argument for every n>=4, including odd n: the first output leaves a physical supply of intermediate values, and at the putative cheaper total that supply is forced to be laminar. Subsequent outputs need a value outside that supply. A single additional shared value J resolves that obstruction in every dimension.

The proof does not extend by simply adding such inequalities for different output subsets: those subsets can share their helpers and first-output cones. Nor does it give a new unrestricted MixColumns bound. A useful next theorem would quantify how much additional work is necessary when several target families compete for the same non-laminar intermediate supply, counting that supply once.
