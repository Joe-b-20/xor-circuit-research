# Independent review: even-entry supply, free sections, and parity retraction

2026-11-14. Independent machine review of [EVEN_ENTRY_SOURCE_FLOOR.md](../EVEN_ENTRY_SOURCE_FLOOR.md), [FREE_SECTION_REPLAY.md](../FREE_SECTION_REPLAY.md), and [PARITY_RANK_RETRACTION.md](../PARITY_RANK_RETRACTION.md). This is an argument audit, not formal verification or human certification. No circuit search or enumeration was used.

**Verdict:** all three arguments pass, including the rank-five free-line consequence and the final residue-plane normal form. Their stated physical-value and chronology limitations are necessary and are preserved.

## The seven actual source relations

Normalize only by replacing a zero, wholly free, or duplicate source value with an already available value. This is causal, preserves ordinary masks on all consumer entries, and cannot create an odd-own entry. The normalized source consists of the four required odd rows, `A_o` other odd gates, and the even gate set `H`, giving `|H|<=5-A_o` under a nine-gate assumption.

The actual entry projections span the rank-three ordinary even space. Wholly free entries contribute nothing to that projection, so `H` has own-projection rank three. A source exit cannot be the first supplier of a new direction of this rank: its projection lies in the span of earlier actual entry projections, supplied by earlier even source values. Thus the three rank increases are ordinary source gates joining two odd values.

Similarly, the first occurrence of each triple own mask cannot be an exit, because all exits are even-own, and cannot be a free addition, because that repeats an existing own mask. It joins an odd value and a nonfree even value. The three even rank increases and the four odd triple first occurrences are distinct actual gates, giving seven equations `h+u+v=0` on physical source nodes.

These are independent formal relations. In a nonempty sum, the latest selected gate result cannot occur in an earlier selected gate's operands. Normalization ensures that this result is not also a different earlier physical source node. Feedback in other gates does not affect this chronological argument.

## The odd-helper alternatives

The eight named source values have exactly one nonzero relation, their all-eight sum. The free-part map on the four rows is the four-cycle adjacent-pair map, whose kernel is the all-four vector; the ordinary part then forces all four inputs. This directly proves the stated named-pair uniqueness.

With no odd helper, each even value supports at most one pair equation, giving rank at most five. With one odd helper `y`, each even value supports at most one named pair and one pair containing `y`. Any difference between its two representations expresses `y` as a sum of three distinct named values. Two different triples would give a named relation of weight at most six, impossible. Thus all second representations contribute at most one common formal direction, and the full pair-relation rank is at most `|H|+1<=5`. Counting relation rank, rather than only pair occurrences, is the crucial point.

With two odd helpers, `|H|=3` and its own projections are independent. No such value can first arise from an exit, whose projection is in the span of earlier even source values. All normalized nonfree exits would have to be members of `H`, so none remains. The remaining source gates alone would compute the four rows within nine gates, contradicting the recorded local minimum ten. These arguments exhaust the possible number of odd helpers and prove the source floor for arbitrary consumer budget.

## Free-section replay

For an arbitrary section `s` of ordinary projection, the difference between a supplied label and its section value is a permitted free vector. Therefore a new ordinary entry direction can initialize its section representative with at most one synthetic source gate. Completing the enlarged section subspace uses one gate for each new section value and never needs to synthesize the same value twice.

An exit lies in the span of earlier actual entries, so its section representative is already maintained when the exit is reached. Adding its free remainder uses at most the original exit's allowance. This establishes the replay invariant without a direct-sum condition on entry prefixes.

Every synthetic section value that belongs to the original physical source set is either already available or can be credited to its later original first producer. That producer is bypassed after the value has been advanced. Distinct values have distinct first producers. Hence only section values absent from the original physical set contribute extra cost, exactly as claimed. With even-own entries, the diagonal section has dimension three, and the fifteen-gate full-diagonal bound gives `G_0>=8+m_D`.

## Rank retraction and the residue plane

If the entry span contains an even-own, odd-free value `(beta,alpha)`, it also contains the odd wholly free value `(0,alpha+beta)` because `(beta,beta)` lies in `D`. The map `P(x)=x+parity(x)*(alpha+beta)` fixes every even free mask and has precisely that odd line as kernel. Applying it to all free components preserves every target and every gate equation. Its kernel lies in the entry span, so the entry rank drops by exactly one before optional bypasses, while the source count does not increase.

The rank-four source floor therefore excludes such a direction at entry rank at most five and source budget at most nine. At entry rank at most four the image is exactly `D`, yielding the stated stronger diagonal-confinement consequence. Bypasses cannot introduce a new entry label outside the transformed span, because ordinary consumer masks remain unchanged.

Combining this with the even-entry source floor forces a rank-five small-source candidate to have ordinary projection rank four and a one-dimensional wholly free intersection. Its nonzero free vector is even. An odd-own entry then complements this free line and `D`, proving the direct-sum description.

For the normal form, projecting along any odd free line is injective on this entry span, fixes the required rows, and makes all computed free parts even. Within the resulting seven-dimensional space, `rho(beta,alpha)=beta+alpha` has kernel exactly `D`; the rank-five entry span is therefore the full preimage of its two-dimensional residue image. An odd residue makes the residue plane have one nonzero even vector and two odd vectors. The named inputs have the four unit residues, and the named rows have the four triple residues, so exactly two named values lie in this entry span.

The projection need not preserve physical source values outside the original entry span. Subsequent availability credits must use the transformed circuit's own value set, as the note explicitly requires. The normal form is a reduction, not a proof that the remaining rank-five case is impossible.
