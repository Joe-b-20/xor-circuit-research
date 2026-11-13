# The rank-two plane supported on three coordinates

2026-11-13. Hand arguments for a remaining first-sheet supplier profile. No circuit searches or finite-family checks. This note records the causal origin of the even directions specific to this plane.

Use the ten-gate producer of the four rows \(U_c=(E_c,s_c)\) and the actual clean span \(W\subset D\) of dimension two, where \(D=\{(v,v):v\text{ even}\}\). The own projections of all physical even gates span \(W_b\), by [Theorem E2](../frontier/EVEN_ESCAPE.md). Assume \(W_b\) does not contain the full four-coordinate parity. Then \(W_b\) is the even space supported on a three-coordinate set \(I\), since two independent pairs in a plane omitting parity cannot be disjoint. Let \(j\) be the omitted coordinate. An odd node is in class 0 or 1 according to its own bit at \(j\). In class 0 the named nodes are the three inputs in \(I\) and \(U_j\). In class 1 they are \(b_j\) and the other three outputs.

An odd entry is a gate reading a free value and an odd nonfree value. Its own class is that of the nonfree operand. The actual even gate values have zero own bit \(j\). An odd non-entry gate adds one physical even value to one odd value, so it preserves the class of its odd operand. An odd entry also preserves this class.

## Causal origin of the even directions

Both independent even own directions first arise in class 0 odd-pair gates. To see this, consider the span of even own masks already available at any time. Every earlier class-1 odd mask lies in the translate of that span by \(b_j\), by following the unique odd operand backwards. A sum of two class-1 odd masks therefore lies in the previously available even span. An even entry repeats an earlier even mask, and a gate combining even operands does not create a direction outside their span. Thus a new even direction must be produced by two class-0 odd operands. This uses gate order and holds even when there are repeated own masks or additional even-only gates.

In [the rank-two normal form](NORMAL_FORM.md) there are exactly two independent even own first occurrences. Both must therefore be generated in class 0. The projected class-0 tree has its two even-root equations and the odd first occurrence for \(U_j\). The projected class-1 tree is rooted at the lone input \(b_j\) and has its three odd target first occurrences. The normal form places one odd entry in each class, so each projected tree lifts to five physical odd nodes. The additional conclusion here is the chronological location of both even roots.
