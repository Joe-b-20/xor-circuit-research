# General arguments for unrestricted XOR circuits

2026-11-14, continuing `d295965`. The priority remains general structural
understanding and unrestricted arguments. Restricted lemmas need a specified
role in such an argument. The fixed-budget twelve-consumer case queue is deferred.

## Shared preparation for several outputs

[The multi-output theorem](MULTI_OUTPUT_STARTUP.md) extends the first-target
argument by taking one union of the first k odd-target ancestor cones. Every
shared helper appears once. Earlier required odd values receive their exact
credit, including required values that are ancestors of other selected outputs.

Choose a nonzero parity with at least one required non-input odd target. Let H
count other odd gates, and d even-plus-even gates. For a target subset S, let
U(S) be its input-support union, omega give odd input coordinates weight one and
even coordinates weight two, and kappa count components of its support-overlap
graph. Every unrestricted circuit satisfies

    H+d >= max_k min_(|S|=k)
                ceil((omega(U(S))-kappa(S)-2k)/2).        (1)

The minima are over required non-input odd targets. This is a mathematical
invariant, not a proposal to enumerate subsets. The proof uses actual first
appearances; arbitrary non-prefix target groups need extra ancestor credits.
Separate prefix inequalities are maximized, not summed.

The bound is sharp for targets sharing a common odd core of 2a+1 inputs and
having disjoint private groups of sizes 2b_i. Their exact minimum combined
preparation is

    min(H+d)=a+sum_i(b_i-1).

The common core is paid once and private work is paid per output. Their full
binary minimum is n-1, attained by the displayed constructions. Complete-graph
star targets also show that the multi-output resource bound can be quadratically
larger than the first-target bound as a function of row weight.

## Actual available values and an exact resource model

[Available supply](AVAILABLE_SUPPLY.md) treats a finite dictionary S of physically
available values. Its span is not granted as free input. Give an odd dictionary
value weight one and an even value weight two, and let Omega_S(z) be the minimum
weighted XOR representation of z using that dictionary.

Adding an actual gate value v changes the metric exactly by

    Omega_(S+v)(z)=min(Omega_S(z), w(v)+Omega_S(z+v)).

An odd-plus-odd gate leaves this metric unchanged. An odd gate or an even-plus-
even gate shortens each target by zero or two, possibly helping many targets
at once. The exact minimum number of these latter gates needed for one nonzero
value z is (Omega_S(z)-w(z))/2. Actual chronological intervals can be summed
when their actual successive dictionaries are retained. An exact progress ledger
separates shared preparation from progress made by required output gates.

Starting from ordinary coordinate inputs, under total parity and with all targets
odd, there is a whole-map reformulation:

    min_binary(O+d)=L_3(T),       min_binary(H+d)=L_3(T)-m.

Here L_3 is the minimum number of three-input XOR gates on earlier odd values,
O counts all odd binary gates, and m counts required non-input targets. The
translation is chronological in both directions. It preserves the named
resource, not total binary cost or even rank. Consequently

    L_2(T) >= r_min+L_3(T),

but these separate minima need not be jointly attainable. Supplying the even
pair values still costs real binary gates. Indeed S={a,b,c} and
S+{a+b} have the same Omega everywhere but different binary cost for a+b+c.
The metric alone therefore cannot price all physical availability.

## What the MixColumns check rules out

Under total parity the support profile in (1) is exactly one. A specified nested
output order proves the upper bound by hand, and the weight-five row minimum
proves equality. The eight bit-position blocks are a compatible partition, so
the standalone rank-plus-support-profile certificate cannot exceed 57. It cannot
recover 75. This ceiling applies only to that specific certificate, not to other
parities or arguments retaining actual supply, cycle, and fanout information.

The [direct checks](checks/check_supply_certificates.py) verify that fixed order,
one common-core construction, and the ternary translation of one recorded
88-gate MixColumns circuit. Its counts O=48,d=16 produce a 64-gate ternary circuit;
all 32 outputs are checked. This is an upper witness for L_3, not a new binary
construction or an optimality claim. No circuit or subset search is used.

## Retained foundations and judgment

The [first-odd-target theorem](FIRST_ODD_TARGET_TRADEOFF.md),
[exact complement tradeoff](COMPLEMENT_TRADEOFF.md),
[unbounded shared-helper benefit](SHARED_HELPER_AMPLIFICATION.md), and
[causal versus cyclic gaps](CAUSAL_BOOTSTRAP_GAP.md) remain established. In
particular, one helper can benefit arbitrarily many targets, and executable
circuits can cost almost twice their cheapest independent XOR equation systems.
[Parity components](ODD_COMPONENT_DEFECT.md) give exact physical accounting;
[the quadratic relaxation](QUADRATIC_LIFT_LIMIT.md) remains too weak for MixColumns.

The multi-output theorem solves the overlap problem for its cone-union charge.
It does not solve unrestricted complexity: support coverage can miss the cost
of supplying the particular values that later gates require. The dictionary
model and ternary normal form identify that remaining issue precisely.

The next task is to couple whole-map computation on actual odd values to the
physical supply and reuse of even pair values. A useful result must price their
joint realization rather than optimize two independent minima or assume a fixed
benefit per helper. A different invariant remains welcome if it handles that
coupling more directly. Sharpening the support-only total-parity MixColumns
certificate is not a useful next step because its ceiling is proved.

Unrestricted MixColumns remains 75 to 88, with no assumption that 88 is optimal.
Both new notes have hand proofs and independent machine reviews, linked within
them. These are not formal verification, human certification, or claims of
literature novelty. The [saved check result](checks/supply-certificates-result.json)
records specified-construction verification only.

[Final scope review](reviews/shared-supply-progress-review.md) checks this synthesis,
the checkpoint, and the specified-construction evidence against the reviewed proofs.
