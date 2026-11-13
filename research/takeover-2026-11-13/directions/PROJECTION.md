# Global repair by projected uses

2026-11-13. New in this research phase; no claim of literature novelty.
Status: hand proof, independently machine-reviewed by two agents in
`../reviews/projection-review.md` and `../reviews/projection-second-review.md`.
This is not formal verification or human certification.

## 1. Question and answer

Counting cancellations separately loses information when several cancellations use the same work.
There is a simultaneous repair that remembers a physical gate together with the part of its value
needed by a downstream use. Equal requests share one computation, even when they arise behind
different, interacting events.

**Projection repair theorem.** For any input-block partition and any XOR circuit C, define q(v)
as below. Its required nonzero outputs have an event-free circuit with at most

    K = sum over physical gates v of q(v)

gates. In particular, if B is an event-free lower bound for the target map, let

    Z = #{gates v : q(v) = 0},
    X = sum over gates v of max(q(v) - 1, 0).

Then

    G >= B + Z - X.                                             (1)

Thus saving s below the event-free optimum requires X >= Z + s: at least s net extra
productive projected uses of shared computations. Event count alone does not express this.
Here X and Z are computable features of the given circuit, not unknown optima.

There is a stronger value version. Let V be the gate-value set of a reduced circuit, and let
P contain every requested projected value except the coordinate input values. Then P itself
has an event-free execution, and

    G >= B + |V minus P| - |P minus V|.                         (2)

Only genuinely missing clean values are paid for; original values not requested anywhere
are credited. This identifies equal projected values even when they come from different
physical gates. It is always at least as strong as (1).

The statements are constructive upper bounds on repair overhead, and consequently lower bounds
on G. It does NOT assert that the constructed repair is smallest, or that a positive X-Z
actually saves gates. It does not yet raise the unrestricted MixColumns lower bound.

## 2. Definitions

Inputs are independent coordinates over F_2, partitioned into nonempty blocks. A node v has
linear value a_v and block support B(v). For a set S of blocks, P_S keeps those blocks and
zeros the others. An event is a gate whose two operands agree nontrivially on at least one
whole block. Partial cancellation inside a surviving block is permitted in an event-free circuit.

Assume all designated output values are nonzero. Zero outputs can be omitted if zero is free;
otherwise their constant-generation convention must be handled separately. The theorem needs
neither reducedness nor liveness. The circuit has no free nontrivial linear forms: only its
coordinate inputs are free.

At each node v form a set D(v) of nonempty block sets, called its requested projections:

1. For each designated output node o, insert B(o) in D(o).
2. In reverse topological order, for every S in D(v), and each operand u of gate v, insert
   S intersect B(u) in D(u) if this intersection is nonempty.
3. Identical sets at the same physical node are identified.

Every S in D(v) is a subset of B(v). These are only the requests reached from the specified
outputs; do not insert arbitrary subsets. Equivalently they are the nonempty intersections
of the block supports along directed paths from v to designated outputs. This equivalence
is a description, not an instruction to enumerate paths.

A request (v,S), for a gate v=a+b, is **productive** if both P_S(a_a) and P_S(a_b) are nonzero.
Let q(v) be the number of productive requests at v. Nonproductive nonempty requests have
exactly one nonzero operand projection, so they require only a wire.

Different requests at one node have different projected values: if S and T differ at block d,
then a_v is nonzero on d and exactly one projection keeps it. Projections at different physical
nodes can still agree; the construction below need not exploit such additional reuse.

## 3. Proof

Process physical nodes in their original topological order, providing P_S(a_v) for each S in
D(v). For an input, its sole possible nonempty request is its original block and is supplied
by that input. For a gate v=a+b and request S, the needed nonzero operands have already been
provided under the requests S intersect B(a) and S intersect B(b).

If just one operand is nonzero, use its wire. If both are nonzero, compute their XOR using
one new gate. It has value P_S(a_v).

This new gate cannot cancel a whole block. If its operands agreed nontrivially on block d,
then d would lie in S and a_v would vanish on d, contradicting S subset B(v). In particular,
the two projected operands cannot be equal nonzero vectors. This proves event-freeness at
each new gate, including copies arising from original events.

Every designated output o requests B(o), so its value is preserved. Original topological
order proves acyclicity even when events feed other events. There is exactly one allocated
gate for each productive request before optional duplicate removal and pruning. Hence at
most K gates suffice. Finally K = G - Z + X, proving (1). QED.

### Value identification proves (2)

Preseed a global value table with all coordinate inputs. Process the same requests in original
physical-node order. If a requested value already exists, reuse its earlier representative.
Otherwise, it cannot be a nonproductive request: the identical nonzero operand projection
would already have been requested at an earlier original node. Hence it has a productive
realization with two earlier available operands, and one new gate computes it. The proof
above shows that this gate is event-free; replacing operands by earlier equal values does
not change that property.

Consequently exactly one gate is allocated for each value in P, before optional pruning.
The required outputs are present and the execution is acyclic. Therefore B<=|P|<=K.
For a reduced circuit G=|V| and

    |P| = G - |V minus P| + |P minus V|,

which proves (2), including its dominance over (1). This establishes that the projected
value set is executable; no search over wirings is implicit in the theorem.

Unreduced circuits also admit the construction and B<=|P|. For bookkeeping, let V be the
set of distinct original gate values, even if it includes zero or an input value, and put
T=G-|V|. Then G>=B+T+|V minus P|-|P minus V| by the same set identity. We use reduced
circuits in the interpretation to avoid mixing normalization savings with cancellation.

## 4. What it explains

**A sufficient condition for cancellation to have no advantage.** If q(v) <= 1 at every
gate, repair costs at most G-Z. More generally X <= Z suffices. The statement applies to
the whole circuit and does not require isolating a first or sole event.

**No-event control.** In an event-free circuit, supports grow on every edge. Every live
node therefore has only its full support requested, and each live gate has q(v)=1. Dead
gates have q(v)=0. Thus the construction adds no work to a live event-free circuit.

**Where duplication comes from.** A shared physical computation can be asked for different
cleaned versions. Each version may itself require a gate. Requests propagated through
different downstream paths are identified whenever their retained block sets coincide.
The burden is therefore the diversity of productive projected uses, with all wire-only
and unused original gates credited. It is not the number of cancelled blocks, events,
paths, or ranks of copied material.

**Scope of 'shared'.** A gate with q(v)>1 has different requested downstream uses, possibly
after a common immediate reader. It need not itself have physical fan-out greater than one.
Do not infer that an immediate fan-out count bounds X.

**No window-only shortcut.** The requests intersect supports at every intermediate node,
not only at the final outputs. A block that disappears and is later reintroduced must
remain absent on the earlier portion of that path. Forgetting intermediate supports does
not in general produce an event-free repair.

## 5. Sharpness: the prefix family

Let x,y_1,...,y_n be singleton blocks, n>=2. Outputs are p_i=x+y_1+...+y_i for 1<=i<=n,
and T=y_1+...+y_n. The circuit computes the p_i as a chain, then T=p_n+x, in n+1 gates.

At every p_i there are exactly two requests: its full support and {y_1,...,y_i}.
At p_1 the clean request is a wire, so q(p_1)=1. For i>=2 both requests are productive,
so q(p_i)=2. At T its sole request is a wire, so q(T)=0. Thus

    X=n-1, Z=1, K=2n-1, K-G=n-2.

The event-free optimum is exactly 2n-1. Ancestors of T avoid x and require at least n-1
gates; the n distinct p_i output gates contain x and are disjoint from those ancestors.
The clean y-prefix chain followed by adding x attains this bound. The original n+1 is
also optimal because all n+1 distinct outputs are non-input values. Hence (1) is sharp,
and a single event can force arbitrarily many productive projected versions.

**Attribution.** This prefix construction is the matrix in Boyar and Find,
*Cancellation-free circuits: An approach for proving superlinear lower bounds for linear
Boolean operators*, Theorem 2 (2012), with the parameter shifted by one; that paper
attributes the construction to Svensson. It already appears in phase 11 of this repository.
The construction and its separation are not new here.
Primary source: https://arxiv.org/pdf/1207.5321 (Theorem 2, page 4 of PDF).

## 6. MixColumns and limitations

For the eight bit-position blocks, the event-free bound B=84 (foundational audit in
`../reviews/foundations-audit.md`) gives

    G >= 84 + Z - X.

For example, a hypothetical 75-gate circuit must have X-Z>=9; any circuit of at most 83
gates must have X>Z. These are structural necessary conditions, not a new unrestricted
lower bound, and do not assert that 88 is optimal.

This repair follows the original wiring; alternative event-free constructions can be much
smaller. An abundance of projected uses can reflect a poor repair strategy rather than
useful cancellation. Equation (2) explicitly accounts for equal values across original
nodes; it still need not find the best event-free computation. Neither the theorem nor the
prefix sharpness controls X-Z for all MixColumns circuits.

### An arbitrarily bad converse to the request-count version

In the prefix family additionally designate each clean prefix t_i=y_1+...+y_i, 2<=i<n,
as an output. Compute them by a separate chain, retain all original p_i, and compute
t_n=T=p_n+x as before. This has G=2n-1 distinct non-input output gates, so it is optimal.
An event-free circuit of the same size computes all clean prefixes first, then the p_i.
Nevertheless the unmerged request count still has X-Z=n-2: it asks for clean versions of
the p_i while they are already present at other nodes. Thus positive, even unbounded,
X-Z does not imply a cancellation advantage, even for an optimal reduced live circuit.

The value version fixes this specific obstruction exactly: every requested value is an
original output or input, so P=V and (2) incurs zero penalty. This is why value identification
is part of the main result, not merely an implementation optimization. It does not prove
the converse to (2).

### The value version also has no converse

Use singleton inputs a,b,c,d and require the five outputs

    ab=a+b, abc=a+b+c, abcd=a+b+c+d, bcd=b+c+d, cd=c+d.

One five-gate circuit builds the ascending prefixes ab,abc,abcd, then bcd=abcd+a and
cd=bcd+b. It is reduced and live; every gate is a distinct required non-input output,
so it is optimal. The projection repair additionally requests bc=b+c at the original
abc node. Its value set is exactly V union {bc}, giving six repaired gates, A=1,D=0.

Nevertheless there is an event-free five-gate circuit: compute ab and cd, then
abc=ab+c, bcd=b+cd, and abcd=ab+cd. The unrestricted and event-free optima coincide.
This specified counterexample separates *repairing the given wiring by projections*
from *choosing a different event-free wiring*. Even at a reduced live optimum, a missing
clean value need not express an unavoidable cancellation advantage. Equation (2) is a
one-sided repair theorem, not a characterization of optimal savings.

Direct evaluation of specified circuits is recorded in `../checks/projection-results.json`:
the two prefix constructions, recorded MixColumns examples, Q_3, and the explicit
superposition witness. The verifier builds the repaired circuits and checks their values
and event-freeness. It searches neither circuits nor configurations.
