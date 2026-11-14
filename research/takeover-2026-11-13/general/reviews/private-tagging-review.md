# Independent review: private tagging and joint supply cost

2026-11-14. Independent machine review of the complete
[PRIVATE_TAGGING_TRADEOFF.md](../PRIVATE_TAGGING_TRADEOFF.md).
I reconstructed the projection argument, the partition optimization, and all
resource counts. No circuit enumeration, SAT, or case elimination was used.
This is not formal verification or a literature-novelty claim.

## Exact projection and the invertible reduction

After any subset of private coordinates is set to zero, each target with a
remaining private coordinate still has a nonzero core part. It therefore
cannot already be a coordinate input. The first gate whose value has
coefficient one in the next private coordinate must read that coordinate
itself and a coefficient-zero parent. Projecting the coordinate to zero
replaces this gate by the other parent. This is a gate of the surviving
circuit, so successive projections remove distinct gates.

This proof must use value coefficients, rather than the first syntactic read:
a repeated read can cancel. The note makes that distinction. Zero values may
be simplified away without introducing a gate for any of the nonzero final
core targets. The resulting circuit has at most G-B gates and computes all
core targets. The reverse construction adds precisely B gates, proving the
stated equality even when core targets repeat or are input coordinates.

Choosing one private coordinate for an even core row and two for an odd row
makes every transformed row odd. Retaining all core coordinates and all but
the final coordinate of each private block turns the reduction into a square
involution: the fixed coordinates determine the added term, which cancels
on the second application. Identity outputs add no gate cost. The note now
includes this explicit general invertible reduction.

## Graph family and its exact even rank

Distinct edges of a simple graph give distinct non-input core pair sums, so
their binary complexity is exactly the edge count m. Private tagging raises
this to 2m. The tagged rows each have weight three; one ternary gate per row
attains m, while distinct non-input outputs require at least m such gates.
The square graph lift only adds coordinate identity outputs and preserves
both complexities and all relevant parity constraints.

For an arbitrary compatible partition, let k count parts containing core
vertices and b count edges crossing between them. Each crossing edge has a
distinct private tag, and that tag must be in one endpoint part. Otherwise
the three coordinates of its target occupy three odd parts. At most m-b
parts can therefore consist only of tags, giving rank at least v-k+b.
Identifying core vertices within parts cannot increase the graph's number
of connected components. The quotient has at most c components, whence
b>=k-c and rank is at least v-c. Core connected components together with
singleton tags attain this bound. Isolated vertices cause no exception.

The exact difference 2m-((v-c)+m)=m-v+c is consequently the cycle-space
dimension of the specified target graph. It is properly distinguished from
the odd-occurrence cycle rank of an implementation.

## Joint resource law and complete-graph attainments

Substituting the exact 2m binary lower bound into
G=m+r+H_o+d+mu gives the stated joint inequality for every unrestricted
circuit. This substitution does not assume that intermediate values avoid
private coordinates or that separate resource minima are jointly attained.

For K_q, the q-1 star pair values are independent and span all core even
pair sums. Every missing edge may be implemented by one extra odd helper,
one even-plus-even combination, or one direct pair gate. Each choice costs
two gates including its target. Private tags keep the displayed odd helpers
distinct from all required targets. A direct nonstar pair closes a cycle,
whereas the even-combination option increases d. All constructions have
r=q-1 and attain every nonnegative integer triple H_o+d+mu=m-q+1.

The exact Pareto frontier follows from k>=q-1, P>=m, and k+P>=2m, with all
boundary pairs attained by those constructions. The ratio 2q/(q+2) is
correct and tends to two. It is explicitly a family-specific ratio, not a
universal claim. The full note passes review. It supplies an unrestricted
structural separation and exact tradeoffs, while making no new numerical
claim for MixColumns.
