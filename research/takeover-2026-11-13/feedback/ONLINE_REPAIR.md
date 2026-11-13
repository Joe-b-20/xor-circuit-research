# Online feedback repair and a fixed prefix separation

2026-11-13. Symbolic counting and hand constructions only; no SAT, exhaustive enumeration, exact-gate search, or computer-driven case elimination. The two results below concern different questions. The adaptive result is **not itself** an offline lower bound for any one fixed map. The fixed prefix family gives only a linear full-circuit separation. A separate [fixed-family result](SIDON_REPAIR.md) gives an exponential lower bound for source-value-preserving repair, without proving an exponential full-circuit gap. None changes the unrestricted MixColumns bound.

## The adaptive chronological model

Let `D=F_2^d`, initially supplied by `d` independent source-coordinate inputs; zero is free. A source-only repair strategy receives an original circuit in chronological order and must make each original source-side value physically available when it occurs. It may use earlier source values and may proactively compute and retain additional source-only XOR gates. It has no information about future exit values until their consumer-bearing construction is presented. Consumer-bearing gates do not supply source-only operands for free.

Charge one source gate to each original exit. Every other source-only XOR used by the strategy is **overhead**, including gates computed proactively before the next exit is revealed. A strategy can retain all values it has made; deleting an available value cannot improve its ability to answer the next request. We consider an adaptive adversary that sees the strategy's current physically available source-only values before choosing the next part of the original circuit.

Define `M(d)` to be the least integer `m` with

    m(m+1)/2 >= 2^d-1.

For any such online strategy, the adversary can force overhead at least

    ceil((M(d)-d)/2) = Omega(2^(d/2)).                   (1)

The balanced-basis construction of [GENERAL_REPAIR](GENERAL_REPAIR.md) has overhead `h(d)=O(2^(d/2))`, so this establishes the correct asymptotic order for this online/no-lookahead model, up to constants. The statement also applies to a randomized strategy against an adversary that observes its realized available values; it is not a lower bound against an offline strategy that knows the entire future circuit.

## Adaptive lower bound

Let `S` be the currently available distinct nonzero source values. With `m=|S|`, at most

    m + binomial(m,2) = m(m+1)/2

nonzero values are already in `S` or are the sum of two distinct values in `S`. If `m<M(d)`, this is less than the `2^d-1` nonzero vectors of `D`. Therefore some value `t` is neither available nor one XOR away. This is an existence argument by a cardinality bound; it does not list possible vectors or circuits.

The adversary chooses such a `t` and extends the original circuit as follows. Starting from a one-bit consumer input `z`, XOR in the source basis coordinates occurring in `t`, one at a time. Every intermediate has nonzero `z` part, so these are consumer-bearing gates and every source entry is a basis input. Finally XOR the last intermediate with `z`; that single source-side exit has value `t`. The repair must supply `t` at this point. Since it was neither available nor one XOR away when chosen, supplying it requires at least two new source-only gates; at least one is overhead beyond the exit's single allowance. The strategy may see the consumer chain as it arrives and may do the required work during it: those extra source-only gates remain charged.

Repeat until the strategy's available nonzero source set has size at least `M(d)`. This happens after finitely many correct responses, or earlier by proactive computation: every requested value is new and the space is finite. Let `n` be the number of completed exits and `A` the total overhead, including any proactive gates. Every request was hard at its selection time, so `n<=A`. Initially there are `d` available nonzero source values, and every source-only gate creates at most one more. Therefore, at stopping,

    M(d) <= d+n+A <= d+2A,

which proves (1). The original circuit so constructed has only the requested exit gates on its source side, and all actual entry labels are among the `d` source inputs. This is an adversarial family depending on the repair strategy; it does **not** exhibit a single fixed circuit that defeats every offline realization. It also does not prove an exponential difference in full circuit size, since the original consumer-bearing chains themselves use gates.

## A separate explicit fixed-map separation of `d-2`

For any integer `d>=3`, let `b_1,...,b_d` be independent source inputs and `z` a one-bit consumer input. Require the `d+1` distinct non-input values

    p_i = z+b_1+...+b_i       (1<=i<d),
    q   = z+b_d,
    t   = b_1+...+b_d.

A feedback circuit computes the `d-1` prefixes `p_i` in order, computes `q` in one gate, and then computes `t=p_(d-1)+q` in one exit gate. It uses `d+1` gates, which is optimal because it has `d+1` distinct non-input outputs. Its entry labels are the `d` source inputs.

In a no-feedback circuit, the cone of `t` must avoid consumer-bearing gates. It needs at least `d-1` gates to connect the `d` essential source inputs. The `d` distinct consumer-bearing output gates `p_i,q` are outside that cone, so at least `2d-1` gates are required. Equality is attained by building the pure source prefixes in `d-1` gates and adding `z` to each required prefix or final input in `d` more. Thus the exact full-circuit saving is

    (2d-1) - (d+1) = d-2.

This is the familiar prefix mechanism written for arbitrary interface rank. It is a fixed-map full-circuit result, but it is only linear in `d` and does not establish an offline exponential lower bound.

## Scope for the MixColumns joint problem

At rank three the general `h(3)=1` upper bound and a one-gate prefix separation are sharp. The ten-gate consumer in the MixColumns 0/1 problem has a rank-three clean diagonal entry space. The separate [five-diagonal argument](FIVE_DIAGONALS.md) now rules out a 21-gate joint circuit with exactly ten consumer-bearing gates, including feedback; it does not use the adaptive high-rank bound. The remaining unrestricted joint problem concerns profiles with eleven or more consumer-bearing gates.
