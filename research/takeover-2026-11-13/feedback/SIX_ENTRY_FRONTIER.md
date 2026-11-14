# The twelve-consumer problem reduces to six target-live entries

**Later continuation:** [charged six-entry frontier](CHARGED_FRONTIER.md) identifies
the global/local rank split, excludes trace multiplicity three, and adds source
parity and physical-supply restrictions. The reduction proved here remains valid.

2026-11-14, continuing reviewed commit `8ab0b3e`. Structural hand arguments with independent machine reviews, not formal verification or human certification. No circuit search, enumeration, or computer-driven elimination was used. No literature-novelty claim is made.

**Current reduction.** Any joint two-sheet circuit of total at most 21 with exactly twelve consumer-bearing gates must have all twelve gates in the relaxed consumer-target cones and exactly six entry occurrences. Its actual entry span has rank five and two quotient directions over the clean diagonal. The consumer must read an odd-own source label. The five-entry target-live class and every outside-entry case are now excluded.

This does **not** close the twelve-consumer problem or the unrestricted joint problem. The previously proved exact-ten and exact-eleven joint minima remain 22. The no-feedback minimum remains 22, the block-monotone MixColumns bound remains 85, and unrestricted MixColumns remains `75<=L<=88`.

## Shared returns are charged by the values needed to connect them

The [affine-tree transfer theorem](AFFINE_TREE_TRANSFER.md) removes an outside entry `v=u+h` when its useful return partners lie in one entry tree. Root the connecting subtree at `u` and translate each vertex value `x` to `h+u+x`. Every edge is one actual source label, already read before the return that needs it. Original translated values receive credits from their source producers; only missing translated values cost extra.

If there are `B` such missing values, source cost increases by at most `B` while deleting the outside entry saves one consumer gate. In particular, at most one missing intermediate value makes the transfer cost preserving. This handles other feedback in place; it does not require replaying every exit at once. Stars and trees with at most three edges cannot support a cheaper tail with two useful returns.

A useful refinement completes an actual triangle early at zero net cost, or uses a cheap difference between two requested returns. These shortcuts explain why counting the original path length alone can overcharge the shared work.

## Independent even helpers give an odd-value forest

The general [odd-forest principle](CHAIN_FIBRES.md#general-odd-forest-principle) applies to any ordinary XOR circuit whose computed even gate values are independent. Join odd occurrences across each even helper and across each odd gate using that helper. Chronology forces this graph to be a forest. In a literal transpose with extra source ports only on even-valued wires, cutting a forest edge expresses its full adjoint as a sum of target boundary values. When those boundary source parts lie in `D`, every odd-wire source part is clean.

For the relevant seven-gate mirror, three independent even helpers serve four odd target gates. Their reader counts are `(2,1,1)`. Each nonzero derivative segment then corresponds to an entry chain with a clean endpoint. A repeated ordinary fibre contains at most one such chain and an isolated clean root. The clean endpoint is a physical consumer value; its source part is not assumed to be separately supplied or available early.

This is why the [five-entry target-live case closes](FIVE_ENTRY_TWELVE_CLOSED.md). The class sizes `(3,1,1)` and `(2,2,1)` allow at most two or one nonclean crossing values, respectively. Expanding each return in the independent actual labels supplies its chronology. A source-only replay uses at most three extra gates and supplies a clean triangle plus an independent clean direction. At `G_0<=9` that would cost at most twelve gates, contradicting the established thirteen-gate supplier bound.

The general forest statement remains useful beyond this application. The clean-endpoint conclusion uses the additional restriction of at most two ordinary readers per helper. With more readers, a segment can lie between internal merges, and this argument does not force a clean endpoint there.

## Complete coverage of the outside-entry case

The preceding [saturated-tail theorem](SATURATED_TAILS.md) left at most one outside entry, with at least two useful returns and an eleven-gate target core of entry rank four. The core has four or five entries. All possibilities are now excluded below 22:

| Core profile | Obstruction |
| --- | --- |
| Four entries | The seven-gate mirror gives one chain and a clean isolated root. Two group sums and at most one tail helper supply four diagonals within twelve gates. [Proof](FOUR_ENTRY_TAIL_CLOSED.md). |
| Five entries, zero or one nonclean | Rank four excludes zero; one nonclean requires three independent physical clean labels, contradicting the cap of two. |
| Five entries, two nonclean | The only possible four-edge obstruction is `c-n-m-c`. Its endpoint difference repairs the two useful returns with one extra gate after group completion. [Proof](TWO_NONCLEAN_TAIL_CLOSED.md). |
| Five entries, three nonclean, three-term relation | Complete the actual triangle and retain one translated helper. [Proof](TAIL_CORE_REDUCTIONS.md). |
| Five entries, three nonclean, four-term relation | The forced four-edge tree partitions into two sets with cheap pair differences. Among the three requested vertices a cheap pair repairs one return from another. [Proof](THREE_NONCLEAN_FOUR_TERM_TAIL_CLOSED.md). |
| Five entries, four nonclean | The three-term case uses a triangle or the stronger three-edge fibre bound; the four-term case uses the affine-plane restriction; the five-term case has distinct odd traces and star fibres. [Proofs](TAIL_CORE_REDUCTIONS.md), [odd case](AFFINE_TREE_TRANSFER.md). |
| Five entries, five nonclean | The affine-plane restriction gives a star or a fibre with at most three edges. [Proof](TAIL_CORE_REDUCTIONS.md). |

The [existing interface classification](FOUR_FIVE_FRONTIER.md) and [three-nonclean relation lemma](THREE_NONCLEAN.md) give the listed relation types. With two nonclean occurrences, the cap of two physical clean values forces the repeated-clean profile treated in its proof. This is a structural classification of label relations, not an enumeration of circuits.

No outside gate remains in a candidate below 22. The target-live entry count is then five or six; the new five-entry closure leaves exactly six.

## What the source must supply

The [even-entry source floor](EVEN_ENTRY_SOURCE_FLOOR.md) proves `G_0>=10` whenever all actual entries have even ordinary source parity, at any consumer budget. Three even-projection rank increases and four first triple masks force seven independent odd-pair equations. At nine source gates, the available odd nodes cannot support them; in the last population, every exit is redundant. Thus a candidate below 22 must use an odd-own entry.

[Parity rank retraction](PARITY_RANK_RETRACTION.md) excludes an odd wholly free direction in a rank-five small-source interface. Combined with the even-entry floor, its entry span has exactly one nonzero wholly free value `q`, which is even, and for any odd-own actual entry `h`,

    U=D direct-sum span{q,h}.

The three nonclean diagonal cosets are `q+D`, `h+D`, and `h+q+D`; the first is even-own and the other two are odd-own. The free direction need not be an actual entry. A permitted free-coordinate projection puts a hypothetical circuit into the residue-plane normal form described in the source-floor note. That normalization does not preserve physical credits outside the entry span; subsequent physical counts and credits must be computed from the transformed circuit's own value set.

A separate [free-section replay theorem](FREE_SECTION_REPLAY.md) completes a chosen linear section of the ordinary source projection. If the projected entry space has dimension `r`, replay costs at most `G_0+2^r-1-m_H`, where `m_H` counts original physical section values. This removes the chronological splitting requirement when the remainder is already free. Its even-own specialization remains valid but is superseded for exclusion by the stronger source floor.

## Remaining six-entry problem and research judgment

The [six-entry trace identities](TWELVE_ENTRY_WIRES.md) now describe the entire possible twelve-consumer frontier. Trace rank is four. The unique actual-label relation is the indicator of odd trace positions, and the two-dimensional relation space on traces is the quotient-signature row space. There are at most two original nonzero physical clean values. Nonclean actual labels have unique physical difference pairs and cannot be newly returned. Repeated traces remain possible; the all-odd, pairwise-distinct trace case is already excluded.

The next promising step is to combine the six-gate mirror's two-component odd forest with the source parity restriction. Source ports on odd mirror wires contribute additional terms to the cut equations, so the clean-endpoint theorem cannot simply be reused. Understanding those terms and internal reader merges offers a structural route; merely subdividing lists of six traces is less explanatory. Larger consumer budgets remain open as well.

## Reviews

Independent reviews cover [tree transfer](reviews/affine-tree-transfer-review.md), [the mirror forest and chains](reviews/chain-fibres-review.md), [five-entry closure](reviews/five-entry-twelve-closure-review.md), [source parity and section replay](reviews/even-entry-and-retraction-review.md), [the core reductions](reviews/tail-core-reductions-review.md), [four-entry tails](reviews/four-entry-tail-review.md), and [the final two tail profiles](reviews/tail-final-review.md). The primary agent checked the proofs and chronological accounting as well. A [final scope review](reviews/six-entry-frontier-review.md) checks this synthesis and its complete coverage.
