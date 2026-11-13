# Joint reconstruction of visible-event block pieces

## Result

For a reduced MixColumns circuit, the separate-chain proof of Theorem V can be strengthened by sharing the in-block pieces of visible-event values. The saving is an explicit, nonnegative integer determined by the pieces actually shared and their output descendants. This is a circuit-dependent improvement, not a new unconditional lower bound for MixColumns. It uses no search. The parent agent independently checked this proof; its concrete combination with hidden-work bounds has two additional machine reviews in `../reviews/hidden-review.md` and `../reviews/hidden-second-review.md`.

Use the notation of `visible/VISIBLE.md`: `F` is the set of visible events, `H=|E\F|+|Q|`, `J(f)` is the set of sheets reached from `f` without a later event, and `in(f)` counts the charged gates in its original private chain. In what follows, physical gates with equal values may be deliberately kept separate, and all output nodes are explicitly designated.

For each block `d`, write `p_d(f)` for the block-`d` component of `val(f)`. In the private construction choose a binary in-block XOR tree for each nonzero `p_d(f)`, with its leaves distinct inputs of `d`. All such gates are event-free. Some of these trees may be replaced by a shared in-block DAG, by identifying gates whose operands and values are equal. (Identifying shared prefix gates in input-order chains is one simple, always available choice.) Keep all gates combining different blocks private to their event, in the order specified in VISIBLE §5.2. A root that is also an event's entire value is redirected to all of that event's retained readers.

For each shared in-block gate `g` on block `d`, let `S(g)` be the events whose reconstructed values use `g`. A trivial path counts if the value of `g` itself represents an event. Set

    a_d(f) = 1 if d belongs to J(f), and 0 otherwise;
    a(g)   = max{a_d(f): f in S(g)}.

Let `P_d(f)` be the number of gates in the original private block-`d` tree for `f`, namely `max(w_d(f)-1,0)`, and define

    Delta_83 = sum_{f,d} a_d(f) P_d(f) - sum_{shared in-block gates g} a(g).

The second sum includes each resulting physical in-block gate once, whether shared or not. Then

    Delta_83 >= 0,
    G >= 83 + H - sum_{f in F} kappa(f) + Delta_83.             (1)

The per-sheet form is also improved: for each `d`, the reconstructed in-block gates of block `d` contribute only the number whose descendant events have `d` in their `J`; the private multiblock joins contribute as before. Hence the nonnegative saving of block-`d` charged pieces can be subtracted from the supply in the `d`-th family inequality.

## Proof

An in-block gate `g` has support exactly `{d}`, because its leaves are distinct and nonempty. Its designated-output descendants are exactly the union of the sheets in `J(f)` over `f in S(g)`: the shared gadget has no retained inputs, and the only paths from its reconstructed event values to outputs proceed along retained gates. If a piece also represents a whole event, its retained uses are included in this union.

By the definition of the families, this single-block gate is in family `F_d` exactly when `d` is in that union. It is in no other own-block family and cannot satisfy the extra family-3 condition of carrying both blocks 2 and 7. Its contribution to the eight-family union is therefore exactly `a(g)`.

Every private multiblock join is still used only by its own event's reconstruction, so its family membership is exactly as in Theorem V. If an event's entire value is a single block, its root has already been counted as an in-block gate rather than as a multiblock join. All retained gates have the same descendants and operand values as before. Thus the total number of charged rebuilt gates is the former `sum in(f)` less `Delta_83`. Apply the disjoint-family bound `|R| + (charged rebuilt gates) >= 83`, and use `G=|R|+|F|+H` and `kappa(f)=in(f)-1` to obtain (1).

For nonnegativity, every gate `g` on the right arises from one or more private-tree copies. If `a(g)=1`, at least one of those copies was charged before sharing. Hence charge each resulting charged gate to one of its distinct former charged copies. Equivalently, if `m_g` is the number of former copies with `d in J(f)`, then its contribution to `Delta_83` is `m_g-[m_g>0]`, which is nonnegative. A gate shared only by uncharged copies contributes zero.

The counting must follow descendant sets, not just values: sharing an uncharged piece with a charged one makes the resulting physical gate charged, but the saving formula already accounts for this.

## The 84 form

Assume, as in VISIBLE §5.5, the joint local 21-gate result and the resulting `G' >= 84 + |U\X|`. For a single-block gate on `d`, membership in the counted set `(union F_j) union X` is equivalent to

    b_d(f) = 1 if d in J(f), or if d=0 and 1 in J(f).

Indeed, for block 0, a gate reaching sheet 0 is in `F_0`, while one reaching sheet 1 and not sheet 0 is in `X`. The predicate remains true under unions of descendant sets. No single-block gate lies in the special `{2,7}` part of family 3. Define

    Delta_84 = sum_{f,d} b_d(f) P_d(f)
               - sum_{shared in-block gates g} max{b_d(f): f in S(g)}.

The same copy-to-result argument gives `Delta_84 >= 0`, and

    G >= 84 + H - sum_{f in F} (kappa(f)+x(f)) + Delta_84.      (2)

Private multiblock joins keep the same family or `X` membership as in §5.5. In particular, a block-0 piece shared between a sheet-0 descendant and a sheet-1-only descendant becomes an `F_0` gate rather than an `X` gate, but it is counted exactly once either way. Equation (2) accounts for this change.

## Concrete savings without search

* If `m` visible events all have `d in J(f)` and the same nonzero block-`d` piece of weight `r`, build that piece once as an in-block tree. This saves at least `(m-1)(r-1)` charged gates in (1), and at least as many in (2). Other pieces may be left entirely private.
* Suppose the four designated outputs of some sheet `d` are all visible events. Their block-`d` pieces are the four triple sums `E_0,...,E_3`. Four private trees use eight charged gates. Instead compute `p01=x_0+x_1` and `p23=x_2+x_3`, then the four triples `p01+x_2`, `p01+x_3`, `p23+x_0`, `p23+x_1`. This uses six charged in-block gates, yielding `Delta_83>=2` and `Delta_84>=2`; all other pieces may remain private. Each triple belongs to the appropriate event and all four events reach sheet `d` by the trivial path.

Holding the other terms fixed, these two shared gates strengthen the applicable separate-chain bound by at least two. They do not alone force a stronger unrestricted gate lower bound: the remaining visible events can still incur penalties, and this reconstruction argument supplies no lower bound on hidden work. The companion `independent.md` supplies such a bound for maximal-window target families.

## Scope and next question

Equations (1)-(2) cover nontrivial joint reconstruction while maintaining the original charged-family accounting. They do not optimize shared DAGs, and they make no assertion that every collection of several visible events yields a positive saving. Distinct block pieces of weight one have no in-block gate to share; different weight-two pieces can also have no common non-input subgate. Thus a universal positive saving per extra visible event does not follow from this construction. Sharing multiblock portions may give more, but its output-descendant union can create family-3 membership or change `X` membership; it needs separate accounting.

## All-output control

If `R` is empty and all visible events are designated outputs, then `G=|F|+H`. Equation (1) simplifies to

    sum_f in(f) - Delta_83 >= 83,

which is a statement about the reconstructed circuit alone, independent of `G` and `H`. Similarly, (2) becomes `sum_f(in(f)+x(f))-Delta_84>=84`. A positive sharing saving in this regime does not by itself lower-bound the original hidden work.

For the 32 distinct MixColumns outputs, use the two-pair/six-gate construction above in each sheet's own block and keep all other pieces private. The four output events in each sheet other than 3 contribute 12 charged gates before this sharing and 10 after it; sheet 3 contributes 16 before and 14 after. Thus the charged reconstructed total is `7*10+14=84`, giving only `84>=83`. This explicit control shows why even a saving of two charged gates on each sheet does not yield a new bound on the original circuit without a separate estimate for hidden work.
