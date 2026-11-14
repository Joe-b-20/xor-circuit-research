# A parity-resolved sharing obstruction for Sidon boundaries

2026-11-14. Hand arguments for unrestricted binary XOR circuits on ordinary
coordinate inputs. Arbitrary sharing, cancellation, duplicate occurrences, and
even-plus-even gates are allowed. No circuit search or case enumeration is used.
An [independent machine review](reviews/SIDON_SUPPLY_TRADEOFF_REVIEW.md) audits
the proof; this is not formal verification or human certification. No
literature-novelty claim is made.

The repository already uses the relation between XOR sharing and four-cycle-free
graphs: see the general auxiliary-count argument in
[Sidon repair](../feedback/SIDON_REPAIR.md), and boundary-label uniqueness in
[the 75 proof, Section 4](../../../lower-bound-proofs/mixcolumns-lb75/PROOF.md).
This note resolves that argument by gate parity and separates actual even supply
from nonterminal odd helpers. The result is a joint unrestricted tradeoff with
no free input-count term. An explicit incidence family shows that its overhead
exponent is sharp.

## 1. Boundary hypothesis and counted resources

Use total input parity, so every coordinate input is odd. Let T consist of m>=1
distinct required non-input odd values. Put

    A_0 = {all coordinate inputs} union T.

Assume A_0 is Sidon in the following sense: no four DISTINCT members XOR to
zero. Equivalently, different unordered pairs of distinct members have different
nonzero XORs. This is a target hypothesis, not a restriction on circuit shape.

In an arbitrary circuit, mark the first occurrence of each target. Let E count
all even gate occurrences and H count odd gates other than these m marked target
gates. Thus its total binary size is exactly

    G=m+H+E.

Let s=H+E denote its overhead beyond the required target gates. Repeated target
values and recomputed inputs count in H when they occur at odd gates. Distinct
nonterminal odd values number at most H, and distinct nonzero computed even
values number at most E. No reduction to a circuit without repetitions is needed.

## 2. Two ways a target can be produced

Each marked target gate has one odd parent u and one even parent e, with y=u+e.
Since y is a first occurrence, e is nonzero and y differs from u. There are no
initial even coordinate inputs under the chosen parity.

Call a marked gate terminal-parent if the VALUE u belongs to A_0, regardless
of which occurrence supplies it. There are at most E such gates. Indeed, for
each fixed nonzero even value e, the pair {u,y} in A_0 is unique by the Sidon
hypothesis. The same pair cannot serve two marked gates in opposite directions:
the parent value is already available, so that direction would contradict one
target's first production. Thus each such gate needs a distinct supplied even
value.

For every other marked target, the odd parent is one of at most H nonterminal
odd values. Form a bipartite graph with those odd values on the left and the
used nonzero even values on the right. Its edge (h,e) represents the marked
target h+e. Each target gives one edge, and the graph is simple.

This graph has no four-cycle. If (h_1,e_1),(h_1,e_2),(h_2,e_1),(h_2,e_2) were
four edges, their four labels would be distinct target values, since only one
marked gate was chosen per target. Their XOR would be zero. This contradicts
the Sidon hypothesis, already restricted to the subset T.

If b denotes the number of these helper-parent target gates, then

    m<=E+b,                                                   (1)

and b is the edge count of a four-cycle-free bipartite graph on at most H and E
vertices. All earlier supplier computation remains charged in E and H.

## 3. A joint inequality and a general overhead lower bound

Pad the two vertex classes by isolated vertices to sizes H and E. Every pair
of right vertices has at most one common left neighbor, so

    sum_(left h) binom(deg(h),2) <= binom(E,2).

For H>0, Cauchy's inequality gives sum deg(h)^2>=b^2/H, hence

    b^2-H*b <= H*E*(E-1).

The positive root, together with (1), yields the unrestricted joint tradeoff

    m <= E + [ H+sqrt(H^2+4*H*E*(E-1)) ]/2.              (2)

For H=0, the helper-parent graph has no edges and (2) correctly reads m<=E.
Interchanging the two graph sides also gives

    m <= E + [ E+sqrt(E^2+4*E*H*(H-1)) ]/2               (3)

when E>0. The zero-E case cannot compute any non-input odd target, so is excluded
by m>=1. Using both inequalities can sharpen a particular tradeoff, but neither
assumes a fixed even basis or a small helper budget.

For a simpler consequence, (2) implies b<=H+E*sqrt(H). Therefore

    m <= E+H+E*sqrt(H)
      <= s + (2/(3*sqrt(3)))*s^(3/2),       s=E+H.        (4)

The last step maximizes (s-H)*sqrt(H) on 0<=H<=s; its maximum occurs at H=s/3.
Equivalently,

    27*max(m-s,0)^2 <= 4*s^3.                             (5)

In particular s>=1 and m<=s+s^(3/2)<=2*s^(3/2), giving the explicit bound

    G >= m + ceil((m/2)^(2/3)).                            (6)

Thus a Sidon boundary forces a superconstant number of non-target gates as the
target count grows. These are total overhead gates, allowing the implementation
to trade additional odd helpers against more even supply and aggregation.
The exponent in (6) cannot be raised for this target class, as the next family
shows. No sharp constant is claimed for (6).

### General difference multiplicities

There is a version for arbitrary odd target maps, without the Sidon hypothesis.
For a set A of odd values define

    nu(A)=max_(e!=0) #{unordered pairs {a,b} subset A : a+b=e}.

Put alpha=nu(A_0) and nu=nu(T), taking nu(T)=0 when T has only one member.
The same physical classification gives

    m <= alpha*E
           + [ H+sqrt(H^2+4*nu*H*E*(E-1)) ]/2.           (7)

Indeed a fixed even label can now serve at most alpha terminal-parent target
gates. In the helper-parent graph, two fixed even vertices have at most nu
common odd neighbors: each common neighbor gives an unordered target pair
with their fixed difference. Different neighbors give different pairs because
every edge has a globally distinct marked target label. Counting these pairs
gives sum_h binom(deg(h),2)<=nu*binom(E,2), and the same Cauchy argument proves
(7). The graph itself may now have four-cycles; their capacity is bounded
rather than forbidden.

Thus, with s=H+E and alpha>=1,

    m <= alpha*s + (2*sqrt(nu)/(3*sqrt(3)))*s^(3/2).      (8)

In particular bounded difference multiplicities force the same m^(2/3)
overhead order. All multiplicities here belong to the specified boundary or
target set. The circuit's internal values remain completely unrestricted.
The Sidon theorem is the alpha=nu=1 specialization (with the one-target case
already covered directly by the sharper counting argument).

## 4. A symbolic family attaining the overhead exponent

Let q be a prime. Take the q^2 points (x,y) in F_q^2 and the q^2 nonvertical
lines indexed by (s,t), with incidence y=s*x+t. There are m=q^3 incidences,
because each point lies on exactly one line of each slope.

The point-line incidence graph has no four-cycle. Two distinct points with
different x coordinates determine at most one slope and intercept by the two
linear equations; points with equal x and different y lie on no common
nonvertical line. Thus two points cannot share two lines.

For each point p introduce three private coordinate inputs whose XOR is h_p.
For each line l introduce two private coordinate inputs whose XOR is e_l.
All these coordinate blocks are disjoint. Require the target

    t_(p,l)=h_p+e_l

for each incident point-line pair. There are n=5q^2 coordinate inputs, and every
target has weight five and odd total parity.

The input-and-target boundary A_0 is Sidon. Consider a putative zero sum of
four distinct boundary members, classified by its number of targets.

- With no target, four coordinate inputs are independent.
- One target has weight five and cannot equal a sum of three inputs.
- Two distinct targets differ in at least four coordinates: they differ in
  two line blocks, two point blocks, or both. They cannot differ by two inputs.
- A sum of three targets has an odd number of point-block occurrences. Some
  complete three-coordinate point block survives, so the sum cannot be one
  coordinate input.
- Four distinct targets sum to zero only if their four incidence edges have
  even degree at every point and line. A simple bipartite even subgraph with
  four edges would be a four-cycle, which has been ruled out.

These arguments cover all q symbolically. They do not enumerate target subsets.

Before cloning the coordinate blocks, the reduced target map consists of the
m distinct pair sums X_p+Y_l, one per incidence. Its exact binary cost is m:
each distinct non-input target needs a gate and each pair sum needs only one.
The [exact column-cloning theorem](COLUMN_CLONING.md) then gives

    L_2(T)=q^3+2*q^2+q^2 = m+3*m^(2/3).                  (9)

Concretely, computing the q^2 triple helpers costs 2q^2 gates, computing the
q^2 line pairs costs q^2 gates, and attaching each pair to its point helper
costs m gates. The construction has

    H=q^2,       E=2q^2,       G=m+3q^2.

Its even suppliers are independent, so d=mu=0 and even rank is 2q^2, but no
claim that this is the target-forced minimum rank is needed for (9). The exact
cloning argument proves total optimality after arbitrary rewiring and
cancellation, not just for the displayed incidence-shaped construction.

As primes grow, (6) and (9) show that the overhead order m^(2/3) is sharp for
the general Sidon-boundary class. The example does not rely on a growing
fixed-budget case classification or on an assumed independent-supplier model.

## 5. Scope

The condition is on the complete input-and-target boundary, not just the
target set. Using only a target Sidon condition would not justify the E bound
on terminal-parent gates, because input-containing pairs must also be unique.
Conversely the competing circuit's internal values need not be Sidon at all.

This result retains actual supplier and helper populations in the old
four-cycle counting mechanism. It supplies a general obstruction to perfect
target-only odd work with too little even supply, and an exact family showing
its order of growth. It is not a new Sidon technique, does not claim a stronger
MixColumns bound, and does not certify the boundary condition for MixColumns
by finite computation. Unrestricted MixColumns remains 75<=L<=88.

The [specified checker](checks/check_subspace_and_sidon.py) and
[saved result](checks/subspace-sidon-result.json) verify the q=3 construction:
45 inputs, 27 targets, 54 gates, H=9,E=18, and 18 distinct input column classes.
The Sidon condition and all-prime optimality are proved above symbolically;
the checker does not enumerate relations or search for circuits.
