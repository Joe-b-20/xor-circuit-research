# Independent review: free and ordinary neighbour ports

Hand review of `../PORTS.md` and its dependence on the transposition argument of `tenth-gate/PROOF.md`. No SAT, enumeration, exact-gate search, or computer-driven case elimination was used. This is not formal verification.

## Verdict

Under the stated model of four-coordinate blocks, separately free vectors for each free neighbour, and unrestricted binary XOR gates, the exact formula and the displayed event-free constructions are correct:

    L(0,0)=6;  L(0,f)=3f+7 for f>=1;  L(p,f)=4p+3f+8 for p>=1.

The proof establishes the lower bound even when whole-block cancellations are permitted. The separate construction shows the same value is attainable without such cancellations. These are isolated-sheet port costs and cannot automatically be summed over sheets of a larger circuit.

## Formal inputs and transposition

After trimming and replacing any value confined to a single free block by that free value, give every remaining use of such a free operand a distinct formal input. A paid gate joining values from two different free blocks remains paid and receives two formal inputs. Remove zero/copy gates if necessary, then trim dead gates again. Every remaining gate is live, each formal input is read once, and every ordinary coordinate is read because its target column is nonzero.

For `K` original gates, the formal circuit has `4+4p+tau` inputs, `K` gate signals, and four designated terminal uses. The sum of all signal use-counts is `2K+4`; every signal has at least one use, so reverse accumulation uses exactly

    (2K+4) - (K+4+4p+tau) = K-4p-tau

binary XOR operations in the literal construction. Coinciding or zero adjoints do not invalidate the count: they may be computed literally and discarded only afterwards. Each formal input's adjoint is the adjoint of its sole reader and so is represented by a signal in the transpose.

For each free block, the row relations of its four components are exactly the span of the all-four relation. Applying the free-value map to any formal target relation shows that the left kernel of the trace matrix is contained in that relation space. Its column space consequently contains the three-dimensional even subspace, giving `tau_j>=3`; if equality holds, the three distinct nonzero traces are independent and even.

The transpose contains the four distinct triple outputs. At most five gates cannot produce them: besides the four odd triples, at most one gate remains; the first gate is an even pair or zero, and a single pair can start only the two triples containing that pair, while the two remaining triples differ by the same pair and cannot each precede the other. Hence six are necessary. If all `f>=1` free sides use exactly three formal inputs, one side supplies three distinct even signals in addition to the four odd triples, forcing seven gates. Otherwise the additional formal use and the six-gate mirror bound already give the same total. For `p>=1`, the transpose additionally contains the four distinct adjacent pairs of its own four input signals. They and the four triples are eight distinct non-input values, so at least eight mirror gates are required; repeated traces from different ordinary blocks may share these same four gates. The `4p` term is the input/output-count correction, not an assumption that these traces are separately computed for every block.

## Explicit attainability

For `p=0,f>=1`, the `U,V,W` chains cost `(f+1)+f+f=3f+1` gates. Their listed final combinations cost six. On every free block, the masks `alpha,beta,gamma` are distinct nonzero pairs and satisfy `alpha+beta=s_1`, `beta+gamma=s_2`, `alpha=s_0`, `gamma=s_3`; the own-block portions form the correct four triples. Every combine step either adds a previously absent block component or XORs unequal nonzero components on the same block, leaving it nonzero. Thus no whole block is cancelled.

For `p>=1`, the four initial chains cost `(p+f)+(p+f)+(p+f)+p=4p+3f`. Their four two-gate output combinations add eight gates. On every ordinary neighbour the appropriate distinct coordinate pairs produce `s_0,s_1,s_2,s_3`; the free parts use the same identities as above. The own-block pairs and the final added own coordinates are disjoint at each step, and all nonzero neighbouring-block components remain nonzero. This proves event-free attainability. The `p=f=0` case is attained by two complementary own-block pair sums followed by the four triples.

The stated incremental interpretation follows algebraically: replacing the first of at least one free neighbours by an ordinary neighbour raises the cost by two; replacing each later one raises it by one. No claim is made here about adding these local charges across overlapping sheet circuits.
