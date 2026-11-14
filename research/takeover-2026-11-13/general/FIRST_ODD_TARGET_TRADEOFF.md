# The first odd target forces a combined cost

2026-11-14. General structural hand proof for unrestricted XOR circuits, with no search or enumeration. Independent machine review is linked [here](reviews/first-odd-target-review.md); it is not formal verification or human certification. No literature-novelty claim is made for the elementary graph and operand-port counts.

A heavy first target cannot be built using only independent even pair formation and the required output gates. It forces a combined amount of extra odd work and even-plus-even work. The theorem counts those two interchangeable resources together, allows arbitrary cancellation and fanout, and gives a bound determined by the required target set.

## 1. One parity choice and three physical counts

Use coordinate inputs e_1,...,e_n and a fixed nonzero linear functional lambda. An input or gate is odd or even according to lambda. Let I be the set of initially odd input indices and s=|I|. The initially even inputs are individually available coordinates; their arbitrary sums are not free.

For the complete circuit let:

- t_o be the number of distinct required non-input odd target values;
- t_e be the number of distinct nonzero required non-input even target values;
- H be the number of odd gate occurrences beyond one occurrence for each of the t_o odd targets;
- E be the number of even gate occurrences;
- d be the number of even-plus-even gates;
- r be the rank of computed even values modulo the span of the initially even coordinate inputs.

The [odd-component identity](ODD_COMPONENT_DEFECT.md) gives

    r=s-c,       delta=E-r=d+mu,                          (1)

where c counts the odd-occurrence graph components and mu is its cycle rank. Thus delta counts dependent even work; d is one part of it.

Assume there is at least one non-input odd target. For such a target z, let w_o(z) and w_e(z) count its supported initially odd and initially even coordinate inputs. Define its weighted support

    omega(z)=w_o(z)+2*w_e(z),
    b(z)=(omega(z)-3)/2.

Here w_o(z) is odd. Since z is non-input, omega(z)>=3, so b(z) is a nonnegative integer. Put b_min=min_z b(z), over the required non-input odd targets.

## 2. The combined-cost theorem

**Theorem.** Every unrestricted circuit for these targets satisfies

    H+d >= b_min,                                        (2)
    H+delta >= b_min.                                    (3)

More precisely, if z is the first required non-input odd value to appear, the right side in (2) can be replaced by b(z).

**Proof.** Retain the complete ancestor cone of that first target. Let h be its odd gate count excluding the target gate, let E_C count its even gates, and let d_C count its even-plus-even gates. Let a and f count its distinct initially odd and initially even coordinate ancestors.

Every even gate in this cone must be read at least once within the cone, since its root is odd. Every initially even coordinate ancestor is likewise read at least once. The h+1 odd gates have one even operand port each, and the d_C even-plus-even gates have two each. These are all the even operand ports. Hence

    E_C+f <= h+1+2*d_C.                                  (4)

The cone is connected and has g=h+1+E_C gates, so the basic ancestor count gives g>=a+f-1. Combining this with (4) gives

    a+2*f <= 2*(h+d_C)+3.

The supported coordinates of z are among its ancestors, so a>=w_o(z) and f>=w_e(z). Therefore

    h+d_C >= (w_o(z)+2*w_e(z)-3)/2 = b(z).

No earlier odd gate in this cone can be a required non-input odd target: z was chosen as the first appearance of any such value. Thus h<=H. Also d_C<=d<=delta by (1). This proves (2) and (3). QED.

The argument does not assume independent even helpers, a fixed gate budget, disjoint output cones, or monotone supports. It also allows even required targets to appear before the first odd target.

Under total input parity all coordinate inputs are odd. The simple form is then

    H+d >= (w_min-3)/2,                                  (5)

where w_min is the minimum support size of a required odd target. In particular, if every non-input odd target has weight at least five, at least one odd helper or one even-plus-even gate is unavoidable.

## 3. An exact identity behind the inequality

The same cone count records where slack comes from. Let beta be the cycle rank of the cone's underlying undirected multigraph. Let B_e be the sum of outdegree minus one over its computed even nodes and initially even coordinate ancestors, counting uses only inside the cone. Every such node has positive outdegree, so B_e>=0.

The even-port count is exactly

    E_C+f+B_e = (h+1)+2*d_C.

The ancestor identity is beta=g-a-f+1. Eliminating E_C gives

    2*(h+d_C) = a+2*f-3+beta+B_e.                         (6)

Equivalently,

    2*(h+d_C) = omega(z)-3
                 +(a-w_o(z))+2*(f-w_e(z))+beta+B_e.       (7)

Thus missing supported coordinates are never credited as free work. Extra coordinate ancestors that cancel, and repeated use inside the cone, contribute explicit nonnegative terms. Sharing within this one cone may help other outputs; equation (7) does not add separate charges for those other outputs.

## 4. A target-only unrestricted lower bound

Let c_max(T,lambda) be the largest part count among partitions of I compatible with all required targets, as defined in [the component theorem](ODD_COMPONENT_DEFECT.md#4-what-targets-force-and-what-this-count-misses). Every circuit has r>=s-c_max.

Since

    G=t_o+H+r+d+mu,

the combined-cost theorem gives

    G >= t_o+r+b_min+mu,
    G >= t_o+max(t_e, s-c_max(T,lambda)+b_min).            (8)

The second inequality is determined by the target set and the chosen parity. The maximum with t_e retains the elementary count of distinct even target gates. It does not charge the same even gates twice.

Equation (8) applies to unrestricted circuits. It may be weak for a particular matrix, and computing a useful compatible-partition constraint is a separate mathematical task. Bounds from different parity choices may be maximized; they may not be added without a proof controlling overlap.

## 5. Sharpness and exchange of the two resources

The weighted coefficient is already sharp for one target. Suppose its support consists of 2a+1 initially odd coordinates and f initially even coordinates, with a+f>=1. Pair 2a of the odd coordinates into a independent even pair sums, leaving one odd coordinate x. These pair sums and the f even coordinate inputs give q=a+f available even operands.

Choose any j with 0<=j<=q-1. Combine j+1 of those even operands with j even-plus-even gates. Add that aggregate and the remaining even operands to x, accumulating through odd gates. The last odd gate is the target. This has

    h=q-1-j,       d_C=j,       h+d_C=q-1=b(z).

All input leaves are used once. The total gate count is 2a+f, the ordinary support-size minimum for that single target. The two resource types exchange one for one.

The [complement family](COMPLEMENT_TRADEOFF.md) gives a simultaneous-output version. For n=2k>=4 and targets J+x_i, every target has weight 2k-1, so H+d>=k-2. The component condition gives r>=k. Therefore

    G>=2k+k+(k-2)=4k-2=2n-2.

The explicit circuits there attain equality with every split

    H=k-2-j,       d=delta=j,       0<=j<=k-2,

and all 2k required outputs present. This proof of their even-n lower bound requires no tight-budget case classification.

## 6. Scope

The advance is a combined unrestricted argument: independent even rank, extra odd computation, and dependent even computation are accounted for together. The first-target step is essential; later required odd outputs can help generate other required outputs without being counted in H.

The theorem can be applied to a whole target map immediately. A stronger result for many output groups needs a shared-supply argument, because one odd helper may help many targets. Applying the first-target inequality separately to those groups and summing is not justified.

No improvement to the unrestricted MixColumns interval 75–88 is asserted here. The next task is to couple the cost of a shared supplier to how many target groups it can serve, retaining the actual gates and their chronological availability.
