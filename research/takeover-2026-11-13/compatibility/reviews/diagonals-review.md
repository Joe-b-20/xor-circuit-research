# Independent review of diagonal supply

2026-11-13, primary agent reviewing the separately developed [DIAGONALS](../DIAGONALS.md). Hand review, not formal verification or human certification.

The displayed twelve-gate construction is correct. The last two own-part identities are `E1+E2=b1+b2` and `p01+E1=E0`. Their free parts are respectively `s1` and `s0`, so they give the missing diagonal and row. The three diagonal masks `01,23,12` are independent. No whole block vanishes at either join; the other joins also preserve all nonzero blocks. The circuit omits the pure-own `E0` value, a distinction needed for the following result.

Under event-freeness, every ancestor of a pure-own triple is pure-own. A circuit containing all four such triples therefore has at least six pure-own gates, by the established unrestricted four-triple lemma. The four required mixed rows and three independent nonzero diagonals are seven further distinct physical values: they have nonzero free parts, while diagonals have even own parity and rows have odd own parity. Hence at least thirteen gates are required. The displayed thirteen-gate construction supplies them and is event-free. The proof does not extend this disjoint-ancestor count to arbitrary circuits that may cancel the free block.

The even-label restriction on a hypothetical eleven follows from the independently reviewed entry-deletion theorem and the recorded augmented-sheet lower bound eleven. The designated diagonal nodes may be included among the targets even when they do not feed the four rows. A projected circuit with only even free labels is still in the original unrestricted augmented problem, so the lower bound applies. This gives a necessary condition, not a twelfth gate.

Both constructions are also evaluated by [the direct checker](../check_compatibility.py). The universal lower bound is the hand argument above; no enumeration supplies evidence for it.
