# Hidden operands across windows: local completions and their differences

2026-11-13. Hand proof, independently machine-reviewed in
`reviews/affine-review.md`, `reviews/affine-second-review.md`, and
`reviews/affine-third-review.md`. These reviews are not formal verification or human
certification. No circuit search or case elimination.
This is a general structural theorem, not a new unrestricted MixColumns bound.

## 1. Why a common projection is not enough

Single-window separation rank kills every local partner on a common set of blocks. Different
windows can admit different partners for the very same hidden value. The correct common
object is an affine set of possible partner values. Differences between its local members
measure exactly the directions that this argument must discard before counting hidden gates.

The construction in [MULTIWINDOW.md](MULTIWINDOW.md) has one hidden gate, arbitrarily many
independent visible events, bounded block dimension and window width, and a growing genuine
cancellation advantage. Thus the loss from possible local completions cannot in general be
bounded by a constant independent of the selected target family.

## 2. Setup

Work over F_2 with independent coordinate inputs, a fixed block partition, and output
windows W. Every designated output is supported in its window. For each window W let V_W
be the coordinate subspace supported there. Call a value local if it belongs to the union
of the V_W, and nonlocal otherwise. Include singleton windows for any uncovered input
blocks so that all nonlocal operands are gates. Zero is local.

Select a finite set T of physical gates, each with a nonzero local value and at least one
nonlocal operand. For output events on maximal-clique windows this last fact is automatic;
otherwise it is an explicit hypothesis. No independence, equal-window, or maximality
assumption is needed below. The selected gates need not be designated outputs.

Let A be their distinct nonlocal operand nodes. Join two nodes of A for each selected gate
that XORs them. This is a physical-node multigraph, with one edge per such gate; include
isolated vertices. Assign every selected gate to the connected component containing its
nonlocal operand(s). A gate with one nonlocal operand has a local partner, possibly an input.

For one component write A_i for its vertices, h_i=|A_i|, T_i for its assigned gates, and

    K_i = span { val(f) : f in T_i },       r_i = dim K_i.

Choose any reference vertex a_i in A_i and also use a_i for its linear value. Along every
edge, the two vertex values differ by a selected value. Therefore all vertices in A_i lie
in the same affine coset

    C_i = a_i + K_i.

Every actual local partner lies in C_i too: it differs from its nonlocal operand by the
corresponding selected value.

Define all geometrically possible local completions, without an optimal-circuit oracle:

    E_i = C_i intersect (union over output windows W of V_W).

This set may contain local values not computed by the circuit. Including them makes the
bound weaker but valid. It depends only on the selected values, reference operand value,
and prescribed output windows. It is not a span modulo all coordinate inputs.

## 3. Theorem AC: quotient by differences of local completions

If E_i is nonempty, choose any ell_i in E_i and define

    Delta_i = span { ell + ell_i : ell in E_i } subset K_i,
    delta_i = dim Delta_i.

Then

    h_i >= r_i - delta_i.                                    (AC)

If E_i is empty, then

    h_i >= r_i + 1.                                          (AC0)

The same stronger conclusion (AC0) holds whenever the actual component has no local-partner
gate, even if geometrically possible local completions exist. Bounds may be summed over
these disjoint physical components, each node counted once. Nonlocal gates have no
event-free continuation to an output, so their total is a lower bound on hidden work in
the visible-event framework.

### Proof of AC

Translate every vertex value by the chosen local anchor:

    z_v = val(v) + ell_i in K_i.

Take the quotient K_i/Delta_i. For a selected gate f=v+b with local partner b,

    val(f) = z_v + (b+ell_i),

and b+ell_i is in Delta_i by the definition of E_i. Thus [val(f)]=[z_v]. For a selected
gate f=v+w with two nonlocal operands,

    val(f) = z_v + z_w,

since the two copies of ell_i cancel. Thus [val(f)]=[z_v]+[z_w]. The images of all selected
values span the whole quotient K_i/Delta_i, and every such image is a sum of the h_i
vertex images. Its dimension r_i-delta_i is at most h_i. QED.

Translation makes the argument uniform, with no assumption that a_i is outside K_i.
Equivalently, one can quotient the ambient space by span(E_i):

    K_i intersect span(E_i) = Delta_i.

If a_i belongs to K_i, zero belongs to E_i, so Delta_i=span(E_i). If a_i is outside K_i,
all local completions have the same nonzero class modulo K_i. A sum of them lies in K_i
exactly when it has an even number of terms, and those sums are precisely the span of
completion differences. Thus the two formulations give the same bound. An early draft
incorrectly called the translated formulation stronger; the theorem and proof did not
depend on that comparison. The difference-space formulation makes the cross-window loss
explicit without treating an affine set as a linear subspace.

### Proof of AC0

If E_i is empty no actual local partner can exist, since each would belong to E_i. All
selected gates assigned to this component are edges between its vertices. Their coefficient
vectors have even weight in F_2^(h_i), a space of dimension h_i-1. Their value span K_i is
the image of a subspace of that space. Hence r_i<=h_i-1. The same argument applies if the
absence of actual local partners is known directly. QED.

### Optional affine-incidence refinement

For each f in T_i let beta_f be 1 if it has one nonlocal operand and 0 if it has two. In
the nonempty-E_i case the lifted rows

    ([val(f)], beta_f) in (K_i/Delta_i) direct-sum F_2

are sums of one or two lifted vertex vectors ([z_v],1). Therefore

    h_i >= rank { ([val(f)], beta_f) : f in T_i }.             (AC+)

This improves AC by at most one. The bit is physical incidence parity, not an extra
assumption about event values. It must be kept consistent across a component.

## 4. Finite descriptions by linear algebra, not value enumeration

The set E_i need not be enumerated. For each prescribed window W solve the linear affine
intersection (a_i+K_i) intersect V_W. If it is nonempty, choose one solution ell_W. The
whole intersection is

    ell_W + (K_i intersect V_W).

Fix one eligible window W_0 and use ell_(W_0) as anchor. Then

    Delta_i = sum over eligible W of (K_i intersect V_W)
              + span { ell_W + ell_(W_0) : W eligible }.      (3)

To prove this, write each local completion as ell_W+k with k in K_i intersect V_W.
Its difference from the anchor is the representative difference plus k. Conversely every
representative difference occurs among the generators, and every k is the difference of
two completions in the same window. This also proves that Delta_i does not depend on the
choice of anchor or representatives.

Equation (3) separates two causes of loss: moving within one admissible window, and switching
between different admissible windows. It uses linear systems on the actual target span and
the given list of output windows. No circuit completion, optimum, finite-case search, or
enumeration of the vectors of a subspace is invoked.

## 5. Relation to the earlier separation-rank theorem

For targets supported inside one envelope S, a component's outside-S value is fixed. Any
coordinate projection P_D that vanishes on every possible local completion also vanishes on
Delta_i. Consequently P_D restricted to K_i factors through K_i/Delta_i, and

    r_i - delta_i >= rank P_D(K_i).

Thus AC includes the earlier HR bound whenever its separated blocks exist, and can remain
informative when no single coordinate block kills all local partners. AC0 may strengthen
it further when no local completion is possible at all. It does not assert that AC is
always strong or that its quotient dimension by itself equals optimal hidden cost.

The method avoids the earlier copy-rank failure by removing only justified local-partner
directions before counting the actual physical nonlocal operands. The two-operand equations
and the connected component are essential: unconstrained target rank alone is not a cost.

## 6. Sharp cross-window sharing

In the bounded-width family of MULTIWINDOW, write S_i=sum_k z_ik, T_i=x+S_i, and a=x+y.
All r selected events belong to one nonlocal-operand component, with h=1 and K=span{T_i}
of dimension r. The local completions in a+K are exactly

    ell_i = y+S_i,       i=1,...,r.

Indeed any coset value still contains y, so cannot belong to a window {X,Z_j}; to lie in
{Y,Z_j,W_jk}, its x component must vanish and only one Z block may remain. Precisely one
T_j must have been added to a. Private w coordinates are absent throughout the coset.

The differences ell_i+ell_1=S_i+S_1, i>1, are independent and span Delta. Hence delta=r-1,
and AC says h>=r-(r-1)=1, with equality. The loss comes wholly from switching between
windows; each eligible-window intersection K intersect V_W is zero here.

The output-event values are independent but their local completions have r-1 independent
differences. That is the exact obstruction to treating those r events as r independent
hidden-gate expenses. The family has a proved growing cancellation advantage, so it cannot
be dismissed merely as a wasteful circuit used to defeat a count.

## 7. Combination with visible repair across different sheets

For a reduced MixColumns circuit, select any subset of visible events each having at least
one nonlocal operand. Partition their nonlocal operands into components once, globally,
using the graph above, rather than building separate copies for separate sheets.

For each component use `r_i+1` when there are no actual local-partner gates; otherwise use
the rank in AC+ (or the weaker `r_i-delta_i`). Let `L_AC` be the sum of these component
bounds. Every counted vertex is a hidden gate, so `H=|E\\F|+|Q| >= L_AC`. The two joint
repair inequalities from `../directions/JOINT.md` now give

    G >= 83 - sum_(f in F) kappa(f) + Delta_83 + L_AC,
    G >= 84 - sum_(f in F) (kappa(f)+x(f)) + Delta_84 + L_AC.

The sums in the penalties range over the full visible set; the operand rank bound may use
only the selected subset. `Delta_83` and `Delta_84` here denote the previously defined
charged-gate savings from shared reconstruction, not the local-completion subspaces
`Delta_i` of this note. This is a conditional per-circuit statement using the previously
audited 83/84 ingredients. It introduces no claim about the values of its terms in every
MixColumns circuit. It is valid across sheets because the counted physical components
are disjoint.

## 8. Explicit limitations and next concrete question

AC applies jointly across windows because its operand components partition the counted
physical nodes. It does not sum separate copies of a shared gate. It requires a nonlocal
operand at each selected gate; internal visible events can lack one, as INTERNAL.md shows.
Local hidden gates are not counted by this theorem.

**Actual MixColumns overlap.** In the reduced 156-gate construction of `OVERLAP.md`, for
the two selected sheet-3/4 row-0 output events, `K=span{F_0,G_0}` and the coset has three
local completions: `b`, `c`, and `s_7(0)`. Their differences span all of K. Thus AC gives
zero, while the physical incidence bit in AC+ gives one, matching the single counted
hidden operand. The theorem does not falsely add the two one-window credits; its geometric
part alone loses all information on this example.

**Full-span control.** If a component's selected values span the full input space, then
its coset is that entire space. The local completions include zero and every input unit,
so their difference space is also the entire space and AC gives zero. AC+ then gives at
most one. The separate AC0 argument still applies if there are no actual local partners.
This is a precise limitation of using every geometrically possible local completion; no
general lower bound is obtained merely by replacing arbitrary copies with this quotient.

For MixColumns the remaining concrete task is to constrain Delta_i for the actual selected
row or internal-event spans and actual operand cosets, or to relate its large dimension to
other gates already forced by the computation. Neither arbitrary rank nor a guessed
universal per-event credit supplies that constraint. The present theorem makes that
missing object explicit without defining it through an unknown optimal circuit.
