# Independent review: free-seeded chronological replay

2026-11-14. Independent machine review of [FREE_SEEDED_REPLAY.md](../FREE_SEEDED_REPLAY.md). This is an argument audit, not formal verification or human certification. No search or enumeration was used.

**Verdict:** the seeded-prefix theorem, canonical complement, and rank-five companion restriction pass. The seed is used as initially available data, without falsely treating it as an earlier actual entry.

Let `W_i=E_i+S`. The maintained groups are exactly `W_i intersect P` and `W_i intersect Q`, because `S subset Q` and `W_i` splits. Passing from one prefix to the next adds at most one dimension to `W_i`. If both components of the new label lay outside their previous groups, splitting the enlarged prefix would add two independent dimensions, which is impossible. Thus one component is already maintained, and the actual source label plus that component supplies the other with at most one XOR. This verifies the key asserted implication of the seeded split condition.

Group completion only synthesizes new nonzero values in `P` or `Q`. Every exit is in the span of earlier actual entries, hence in the maintained sum, and uses at most its original one XOR. Original source values remain available by chronological induction. A synthetic group value in the original physical set is either already present or advances a later original first producer, which is bypassed. Distinct values charge distinct source gates; seed values need no synthesis because they are free from the start. These are valid physical credits, and by the final entry both entire groups have been supplied.

For the canonical construction, representatives selected independently modulo `D+S` are independent modulo `D` together with a basis of `S`. Hence their span with `S` is a complement of `D` of dimension `c`. A selected representative is pure in this complement. An unselected label's complement component is a combination of earlier representatives and a seed value, so it belongs to the previous augmented prefix. This proves the seeded-prefix condition inductively. The lower bound on physical complement values counts the `2^s-1` free seed values and `c-s` distinct actual representatives outside the seed, with no overlap.

In the rank-five application, `D+<q>` is exactly the even-own part of `U`, so the first representative chosen modulo that space is the first odd-own entry `h`. The complement has nonzero values `q,h,h+q`; the first two are original physical values, while the third contributes precisely the stated indicator. Substituting into the replay budget gives `G_0>=7+m_D+1_{h+q in A}`. At `m_D=2` and `G_0<=9`, this forces `G_0=9` and excludes the companion from the entire original physical set, including values produced later.

The note correctly requires recomputing that physical set after any free-coordinate normalization. Its conclusion is a necessary condition and leaves the case with an absent companion open.
