# Independent review: saturation by a shared difference basis

2026-11-14. Independent machine review of the complete
[COSET_SATURATION.md](../COSET_SATURATION.md). I reconstructed the compatible
partition argument, the physically supplied basis construction, and the claims
about every optimum. No circuit search or case enumeration was used. This is
not formal verification, human certification, or a literature-novelty assessment.

## Target set and the forced rank

The part-parity map has rank c because every part is nonempty. Its kernel W_P
therefore has dimension n-c=r. The c chosen unit-pattern cosets are disjoint,
each has size 2^r, and each coordinate input belongs to exactly its own part's
coset. Thus the number of distinct non-input required targets is correctly
m=c*2^r-n. Every target is odd under total coordinate parity.

For any compatible circuit partition Q with at least three parts, a split of
one P-part supplies coordinates i,j in two different Q-parts. A coordinate k
in a third Q-part is distinct from both. The triple e_i+e_j+e_k has unit
P-parity because the first two contributions cancel there, even when k is in
their same P-part. It is therefore a required target, but has three odd Q-parts,
contradicting compatibility. Hence such a Q cannot split any P-part and is a
coarsening of P. Partitions Q with at most two parts already have at most c
parts under the explicit c>=2 hypothesis.

Consequently c_max=c, since P itself is compatible, and every circuit has even
rank at least n-c. Combining that with the m required non-input odd values
counts disjoint physical gate populations and gives G>=m+r. No input-support
or cancellation restriction on the competing circuit is introduced.

## Paid basis and a target-only traversal

The root-to-other-coordinate pairs inside each P-part are independent and
span its even-support space. Across all parts they give exactly r actual
even values spanning W_P. Computing them costs r XOR gates.

In each required coset, adding the r basis values gives a connected Cayley
graph. The coordinate inputs in that part are distinct vertices already
physically available in that coset. A spanning forest rooted at all these
vertices exists, for example by growing outward from them simultaneously.
Each other vertex has one forest parent closer to a root. Traversing in that
order uses its parent's actual odd value and one actual paid basis value.
Thus each non-input target is computed once, with no non-target odd helper.

The total is r plus the total number m of missing vertices. No arbitrary sum
of basis values is supplied for free: all traversal edges read a single
previously computed basis member. The construction also handles r=0, when
all P-parts are singletons, every required coset consists of its one input,
and no gate is needed.

## Every-optimum claims

The exact identity G=m+r_C+H+d+mu has nonnegative H,d,mu, and r_C>=r.
Attainment of m+r therefore forces r_C=r and H=d=mu=0. In particular O=m and
E=r, as stated. This concerns the parity-specific odd-occurrence graph; it
does not force the full ancestor graph to be a forest, and the note correctly
keeps those notions distinct.

For c>=3, an optimal circuit's partition has exactly c parts and the preceding
argument makes it a coarsening of P. Equal part counts force equality with P.
For c=2 that argument's three-part premise is unavailable, and the note properly
does not assert uniqueness. Indeed every two-part partition is compatible
with the complete set of total-parity odd vectors.

For c=2 the target union is exactly all odd forms. Substituting r=n-2 gives
L_2=2^(n-1)-2, O=2^(n-1)-n, and E=n-2 for every optimum. The stated n>=2
domain includes the zero-gate n=2 endpoint and avoids an invalid n=1 formula.

The complete note passes review. It supplies an unrestricted exact family and
a structural explanation based on target closure, without claiming that sparse
target sets admit the same traversal or that missing targets have an additive
penalty. No new numerical MixColumns claim is made.
