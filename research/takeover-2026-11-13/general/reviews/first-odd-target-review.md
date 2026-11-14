# Independent review: weighted first-odd-target cost

2026-11-14. Independent machine review of
[FIRST_ODD_TARGET_TRADEOFF.md](../FIRST_ODD_TARGET_TRADEOFF.md). I reconstructed
the counting identities and checked the complete saved proof and sharpness
construction. No search or enumeration; not formal verification or a claim
of literature novelty.

## The physical port count

In the complete ancestor cone of the first required non-input odd target,
every computed even gate and every initially even coordinate ancestor has
at least one use. The root is odd, so none of those even nodes is an unused
root exception. An odd gate has exactly one even operand port; an even-plus-
even gate has two; an odd-plus-odd gate has none. Consequently

    E_C+f <= h+1+2*d_C.

This counts physical occurrences. Repeated reads consume multiple ports and
do not invalidate the inequality. Duplicate values remain separate nodes.
Initially even coordinate inputs are counted individually; arbitrary sums
of them are not granted for free.

The connected ancestor graph gives h+1+E_C>=a+f-1, regardless of cancellation
or repeated operands. Combining the inequalities proves

    h+d_C >= (a+2*f-3)/2
            >= (w_o(z)+2*w_e(z)-3)/2.

All other odd gates in this cone are auxiliary relative to the required
non-input odd target set: otherwise that earlier occurrence would have been
the first target. Thus h<=H. Even required targets may appear in the cone
without causing a problem; they belong to E_C and retain their physical
operand ports. Since d_C<=d, the asserted stronger bound H+d>=b(z) follows.
The inequality H+delta>=b(z) is its valid weaker consequence.

The assumption that at least one non-input odd target exists is explicit.
For such a target, w_o is odd and weighted support is at least three, so
b(z) is a nonnegative integer. Coordinate inputs requested as outputs are
correctly excluded from the counted target population.

## Exact slack identity

Counting all even reads exactly gives E_C+f+B_e=h+1+2*d_C. With
beta=(h+1+E_C)-a-f+1, substitution yields

    2*(h+d_C)=a+2*f-3+beta+B_e.

Subtracting supported-coordinate counts gives precisely the stated weighted
identity. Every slack term is nonnegative. The cone cycle rank counts
repeated use within that cone; B_e additionally identifies the part due to
even-node fanout. Uses outside this cone are not counted and no independent
charge to other outputs is inferred.

## Target-only lower bound

The exact global decomposition is G=t_o+H+r+d+mu. Applying H+d>=b_min gives
G>=t_o+r+b_min+mu. The compatible-partition theorem gives r>=s-c_max, while
the required even values separately give G>=t_o+t_e. Taking the maximum
therefore proves the stated target-only inequality. It does not double-count
even output gates. Maximizing over parity choices is legitimate; adding
their bounds remains unjustified without another overlap argument.

## Sharpness and complement consequence

For one target on 2a+1 odd and f even input coordinates, the specified a
pair sums, j even combinations, and a+f-j odd accumulations total 2a+f
gates. Its auxiliary odd population is a+f-j-1 and its even-plus-even
population j, attaining b(z)=a+f-1 for every permitted j. The construction
uses each input once and attains the ordinary single-output support bound.

For even complement size n=2k, all targets have total-parity weight 2k-1.
Hence H+d>=k-2. The compatible-component argument gives r>=k, proving
G>=4k-2 directly. Equality forces r=k, mu=0, and H+d=k-2. Therefore every
optimal complement circuit has minimum even rank and no odd-graph cycles;
the displayed circuits attain every split between H and d=delta.

## Conclusion

The theorem passes independent review. It is a combined-cost statement for
unrestricted circuits, rather than an assumption of independent even work
or a fixed-budget classification. Its limit is also accurately stated:
one odd helper can serve many groups, so first-target arguments for several
groups cannot simply be summed. No stronger MixColumns numerical bound is
claimed.
