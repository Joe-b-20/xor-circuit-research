# When a shared difference basis makes every further gate an output

2026-11-14. Structural hand proof for unrestricted binary XOR circuits on
ordinary coordinate inputs. Arbitrary cancellation and sharing are allowed
in the lower bound. No circuit or matrix enumeration is used. An
[independent machine review](reviews/coset-saturation-review.md) is saved; this
is not formal verification, human certification, or a literature-novelty claim.

Shared preparation can be completely effective when the required values are
closed under its differences. This note gives a general exact family: pay for
one even basis, then every remaining gate produces a required odd output.
The construction does not make the basis span freely available.

## 1. The target family

Partition n coordinate inputs into c>=2 nonempty parts P_1,...,P_c. Define

    W_P = {v : v has even parity on each part},
    r = dim W_P = n-c.

Let T_P contain every vector whose parity on the parts is exactly one unit
vector: it is odd on one part and even on all the others. Equivalently,

    T_P = union_(j=1)^c (e_(root_j)+W_P),

where root_j is any coordinate in P_j. These c cosets are disjoint, so

    |T_P|=c*2^r.

All targets are odd under total input parity. Every coordinate input is itself
a target, leaving m=c*2^r-n distinct non-input targets.

**Saturation theorem.** The exact unrestricted binary complexity is

    L_2(T_P)=c*(2^r-1)=m+r.                              (1)

Moreover every optimal circuit has exactly m odd gates and r even gates, with
no extra odd gates, no even-plus-even gates, and no odd-occurrence graph cycles.
This does not assert that its full ancestor graph is a forest.

## 2. Why every circuit needs the even rank r

Use the [parity component theorem](ODD_COMPONENT_DEFECT.md). A circuit's odd
components induce a partition Q of the coordinate inputs compatible with all
required odd targets: each target must be odd on exactly one Q-part. If Q has
k parts, the circuit's even rank is n-k.

Any compatible Q has at most c parts. To prove this, there is nothing to show
when Q has at most two parts. Otherwise suppose a P-part contains coordinates
i,j lying in different Q-parts. Choose coordinate k in a third Q-part. The
triple e_i+e_j+e_k is in T_P: i,j cancel in the P-parity pattern, leaving the
unit pattern of k, even if all three lie in the same P-part. But this triple is
odd in three Q-parts, contrary to compatibility. Thus Q with at least three
parts cannot split any P-part. It must be a coarsening of P, and has at most c
parts as claimed.

The partition P itself is compatible. Hence the exact minimum possible even
rank is n-c=r. Every circuit also needs one odd gate for each of the m distinct
non-input targets. These are disjoint physical gate populations, giving

    G>=m+r.                                               (2)

No intermediate values, cancellation patterns, or component mergers were
restricted in this argument.

## 3. Attainment by one paid basis and target-only traversal

In each part P_j choose root_j and compute the pairs

    e_(root_j)+e_i,       i in P_j except root_j.

There are exactly r such gates. Their even values form a basis B of W_P and
are now individually physically available. Their coordinate-pair graph is a
forest with the specified parts, so these r values are independent.

Within each coset e_(root_j)+W_P, join two target values when their difference
is one member of B. This Cayley graph is connected, since B spans W_P. It
already contains every coordinate input belonging to that coset as a free
available vertex. Choose a spanning forest rooted at all of these available
inputs, and traverse it away from the roots. Each new vertex is the XOR of
one previously reached odd value and one of the paid even basis values.

Every new vertex is a required target, because adding a member of W_P preserves
the coset. Exactly one odd gate is used for each of the m missing vertices,
with no extra odd helper. This gives r+m gates and proves (1).

This is a finite existence construction, not an enumeration used to prove a
lower bound. No unspecified vector in W_P is granted as a free operand: the
only even operands read by the traversal are the r actual basis values.

## 4. All optima saturate the same resource lower bound

Let r_C be actual even rank, H the number of extra odd gate occurrences beyond
the m required ones, d the number of even-plus-even gates, and mu the cycle
rank of the odd-occurrence graph. The exact parity accounting is

    G=m+r_C+H+d+mu.

We proved r_C>=r. Equality G=m+r therefore forces

    r_C=r,        H=d=mu=0,
    O=m,          E=r.                                   (3)

Thus the result describes every optimum, not just the displayed construction.
For c>=3, its compatible input partition also equals P: it has c parts, cannot
split P, and a proper coarsening would have fewer parts. When c=2, another
compatible two-part partition may attain the same bound; uniqueness is not
claimed.

## 5. All odd forms as a special case

For c=2, being odd on exactly one part is the same as having odd total parity.
The target set is therefore every odd linear form on n>=2 coordinates, and
the theorem gives

    L_2(all odd forms)=2^(n-1)-2,
    O=2^(n-1)-n,            E=n-2                         (4)

in every optimum. The displayed shared even basis has only n-2 values, yet it
supports all 2^(n-1) odd targets through one gate per non-input target.

The mechanism is closure, not free access to an even span. Once the basis is
paid for, the required set contains the intermediate odd values needed to move
through each coset. In less complete target sets, analogous paths can require
extra intermediate values that are not outputs, or different supplied even
directions. The theorem supplies an exact endpoint for studying that joint
cost; it does not bound it by the number of missing targets.

These are unrestricted optimality statements for a broad algebraic target
family. They do not claim that MixColumns has this closure property or improve
its numerical interval, which remains 75<=L<=88.

The [specified checker](checks/check_joint_dictionary.py) verifies one explicit
nine-gate construction for parts of sizes 2,2,1: two even basis gates and seven
odd target gates. Its twelve distinct values satisfy the required part-parity
condition and exhaust the family by the proved cardinality, without listing
all coordinate vectors. The [saved result](checks/joint-dictionary-result.json)
records this construction check, not an optimality search.
