# One target has an exact two-resource frontier

2026-11-14. Structural proof for arbitrary binary XOR continuations from an
actual supplied dictionary. Arbitrary cancellation, dependent dictionary
values, and free fanout are allowed. This note is not a claim about optimal
multi-output circuits. An [independent machine review](reviews/single-target-pareto-review.md) is saved.
There is no claim of formal verification, human certification, or literature novelty.

The [available-supply theorem](AVAILABLE_SUPPLY.md) identifies one weighted
resource. Here the same argument gives the entire discrete frontier between
forming odd pairs and doing the other binary operations. For one designated
value, shared internal computation never improves this resource pair over an
appropriate formula. This is a consequence for unrestricted continuations,
not an assumption that the given circuit is a formula.

## 1. The two resources

Let S be a finite set of physically supplied nonzero vectors in a binary vector
space, and fix a parity functional lambda. The values in S may be dependent;
only its actual members are available as initial operands. Let z be a nonzero
vector in span(S), and put I=lambda(z), regarded as zero or one.

In a continuation circuit count

    K = number of odd-plus-odd gates,
    P = number of all other gates = odd gates + even-plus-even gates.

Thus the ordinary binary cost is G=K+P. Gates with zero or repeated values may
be retained and charged. They are not granted any special computational power.

For a subset R of S whose XOR is z, write o(R),e(R) for its numbers of odd and
even dictionary members. Its parity forces o(R)=I modulo two. Define

    K_R = (o(R)-I)/2,
    P_R = (o(R)+I)/2 + e(R)-1.                         (1)

Both numbers are nonnegative, and K_R+P_R=|R|-1.

**Theorem.** Every circuit computing z from S is componentwise dominated by
one representation point (K_R,P_R): there exists one subset R representing z
for which K_R<=K and P_R<=P. Conversely each point in (1) is attained by a
binary formula using the members of R once each. Therefore the exact discrete
Pareto frontier of achievable (K,P) is the set of coordinatewise minimal points
in (1).

The same R works for both inequalities. Separate minimization of the two
coordinates would lose this property. "Formula" here means no internal fanout
and no repeated dictionary leaf; coordinate-level cancellation between different
dictionary values remains possible.

## 2. Weighted prices and the proof

Give an odd value weight (alpha+beta)/2 and an even value weight beta, where
alpha,beta are arbitrary nonnegative prices. For any supplied dictionary D put

    Omega_D(x) = min_(R subset D, XOR R=x) sum_(s in R) w(s),
    Omega_D(0) = 0.

Every physically available nonzero value has its assigned weight. For an odd
value any representation contains an odd member. For a nonzero even value a
representation contains either an even member or at least two odd members,
whose total weight alpha+beta is at least beta. This also covers zero prices.

Adding the nonzero actual gate value v=a+b gives the exact update

    Omega_(D union {v})(x)
      = min(Omega_D(x), w(v)+Omega_D(x+v)).              (2)

Substitution of its two available parents raises the representation weight by
alpha at an odd-plus-odd gate, and by beta at either other gate type. Therefore
one such gate lowers any fixed word length by at most its stated price. A zero
result leaves the dictionary unchanged and cannot invalidate this lower bound.

Now take an arbitrary continuation circuit from S. Replace every dictionary
member s by a distinct formal independent coordinate f_s, with parity lambda(s).
Lift every gate using exactly its original two parents. Projection f_s -> s
recovers the physical circuit. Its final formal value is the XOR of some subset
R of the formal coordinates, and consequently the corresponding actual subset
R of S represents z. The formal circuit has exactly the same gate parities,
although a physical zero value need not have formal value zero.

The formal inputs are independent, so the initial weighted word length of that
final formal value is exactly

    o(R)*(alpha+beta)/2 + e(R)*beta.

Its final length is w(z). Summing the per-gate price bound gives

    alpha*K + beta*P >= alpha*K_R + beta*P_R.            (3)

Crucially R came from the fixed circuit before choosing prices. Taking
(alpha,beta)=(1,0) and then (0,1) proves both desired inequalities for this same
R. No enumeration of possible representations is involved in this proof.

To attain (1), if z is odd, leave one odd member of R as an anchor and pair the
other odd members. This uses (o-1)/2 odd-plus-odd gates. Add those actual even
pair sums and the e even dictionary members to the odd anchor one at a time;
this uses (o-1)/2+e odd gates. If z is even, pair all o odd members and then XOR
the resulting o/2+e even operands together. This uses o/2 odd-plus-odd gates
and o/2+e-1 even-plus-even gates. These are real binary formulas. The parity
counts stay valid even if a partial actual value is zero. This proves the theorem.

The proof uses a formal lift only to count the actual circuit. It neither makes
dictionary members independent in the physical problem nor supplies any new
physical value for free.

## 3. Exact prices, including ordinary binary cost

The theorem implies the exact formula for any nonnegative pair of prices:

    min_circuits (alpha*K+beta*P)
      = min_(XOR R=z) (alpha*K_R+beta*P_R)
      = Omega_S(z)-w(z).                                (4)

For alpha=beta=1 both types of dictionary member have unit weight. Writing
ell_S(z) for the minimum number of actual dictionary members whose XOR is z,

    min G = ell_S(z)-1.                                 (5)

This ordinary dictionary length retains the physical pair supply forgotten by
the earlier parity-weighted metric. Every actual gate changes it by

    ell_(S union {v})(z)=min(ell_S(z),1+ell_S(z+v)),

so the decrease is zero or one. For example, supplying a+b reduces the remaining
binary cost of a+b+c from two to one when a,b,c are independent odd inputs.

For alpha=0,beta=1, rescaling the weights by two recovers the exact O+d formula
from [available supply](AVAILABLE_SUPPLY.md). Equation (4) gives more than two
isolated minima, and the theorem gives more than the convex support function:
it identifies the discrete nondominated representation points themselves.

This does not mean that such points are computationally easy to find for an
arbitrary dependent dictionary. They are a structural characterization, not a
proposal to enumerate representations or run a circuit search.

## 4. Separate minima can fail even for one supplied target

Let q>=1. Choose 2q+1 independent odd vectors A={a_0,...,a_(2q)} and 2q
independent even vectors E={e_1,...,e_(2q)}, with A union E independent. Supply

    b = XOR(A) + XOR(E),       S=A union E union {b},
    z = XOR(A).

The supplied b is odd. The dictionary has exactly one nonzero formal linear
relation, namely XOR(A)+XOR(E)+b=0. Hence z has exactly two subset
representations: A and E union {b}. The theorem gives its exact frontier

    (K,P)=(q,q) or (0,2q).                              (6)

Neither point dominates the other. The separate minima are min K=0 and
min P=q, whereas min G=2q. Their sum undercounts the true continuation cost by
q. There are no intermediate nondominated points: this follows from the
componentwise theorem, not merely from a weighted-price comparison.

**Scope of this example.** This is a supplied-dictionary statement. If S is
built from ordinary coordinate inputs, every intermediate value used while
building b also remains available in a full chronological dictionary. Those
extra values can alter its representation frontier. Thus (6) is not, by itself,
a separation theorem for ordinary whole-map circuit complexity or for a full
coordinate-input prefix. The theorem applies to such actual full prefixes, but
their complete dictionaries must be retained. The [whole-map joint-cost
result](PRIVATE_TAGGING_TRADEOFF.md) addresses a different question.

## 5. What remains genuinely multi-output

For one target the formal lift finds one representation whose formula dominates
the entire circuit in both named resources. Applying this separately to several
outputs does not preserve their shared gates. The different formulas may count
the same physical preparation repeatedly and cannot simply be added.

For chronological target intervals the theorem is valid using the actual full
dictionary at each interval start. Those interval costs can be summed, but their
dictionaries depend on earlier computation. The unresolved whole-map issue is
therefore how a paid value changes several later representation frontiers at
once, while its creation and all retained alternatives are charged only once.

The [specified checker](checks/check_joint_supply.py) verifies the two displayed
q=2 dictionary formulas with resource pairs (2,2) and (0,4), as well as the
one-dimensional dictionary relation space. The
[saved result](checks/joint-supply-result.json) does not enumerate representations
or assert that this dictionary is a full coordinate-input prefix.
