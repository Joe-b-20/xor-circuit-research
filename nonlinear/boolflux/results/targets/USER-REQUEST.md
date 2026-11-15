# The user's request (2026-11-15 ~15:10 UTC), verbatim

I want ten targeted campaigns against specific NIST AES S-box circuits, each with its own priorities.

Non-negotiable constraints
For every target, AND count (A) and AND depth (AD) must be less than or equal to the corresponding NIST reference. Never accept a tradeoff that increases either.
These are hard constraints on retained search states and recorded results, not soft objectives.
Gate count (G) and gate depth (GD) may trade off according to each target's priorities below.
Keep two categories of results separate:

* Strict improvements: G and GD are both no worse than the reference, with at least one strictly better.
* Tradeoff improvements: a substantial gain in the primary objective with a small, explicitly permitted cost in the other. Never describe these as dominating the reference.

A small increase in depth means at most one or two additional levels, where explicitly allowed. It must buy a meaningful reduction in gates, not merely one gate.
For depth-first targets, prioritize reducing depth without increasing gates. Record any useful depth-versus-gate-count tradeoffs separately.
All comparisons must use NIST's {AND, XOR, XNOR, NOT} gate library, with consistent gate counting.
Pinned NIST reference: `3d807741f937d29d3bef4f32f142ccda0cda9070`

Targets
All files are in: https://github.com/usnistgov/Circuits/tree/master/data/slp/aes/aes-sbox

1. A28 / AD4 / G132 / GD22 — `aes-sbox-a28-ad4-g132-gd22-xx104-40.circ.txt`
* Hard limits: A≤28, AD≤4.
* Primary: G<132 while GD≤22.
* Also explore substantial gate reductions with GD≤24.
* Ideal: reduce both G and GD.

2. A28 / AD4 / G176 / GD14 — `aes-sbox-a28-ad4-g176-gd14-xx148-25.circ.txt`
* Hard limits: A≤28, AD≤4.
* Primary: GD<14 while G≤176.
* Equally valuable: G<176 while GD≤14.
* Ideal: improve both.

3. A28 / AD5 / G128 / GD20 — `aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt`
* Hard limits: A≤28, AD≤5.
* Primary: G<128 while GD≤20.
* Also pursue GD<20 without increasing G.
* Ideal: improve both. Do not increase GD for minor gate savings.

4. A32 / AD4 / G117 / GD19 — `aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt`
* Hard limits: A≤32, AD≤4.
* Primary: G<117 while GD≤19.
* Also explore substantial gate reductions with GD≤21.
* Ideal: reduce both.

5. A32 / AD7 / G103 / GD32 — `aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt`
* Hard limits: A≤32, AD≤7.
* Primary: break 103 total gates while preserving GD≤32.
* Independently pursue reducing AND depth to 6, 5, 4 or lower while keeping G as close to 103 as possible.
* Also value improvements to GD without increasing G.
* Give this target substantial research attention: the overall gate-count record and nonlinear-depth improvements are separate achievements.

6. A34 / AD4 / G139 / GD13 — `aes-sbox-a34-ad4-g139-gd13-xx105-22.circ.txt`
* Hard limits: A≤34, AD≤4.
* Primary: GD<13 while G≤139.
* Secondary: G<139 while GD≤13.
* Ideal: improve both.
* Depth reduction is the main research objective.

7. A35 / AD3 / G139 / GD27 — `aes-sbox-a35-ad3-g139-gd27-xx104-38.circ.txt`
* Hard limits: A≤35, AD≤3.
* Primary: G<139 while GD≤27.
* Also explore substantial gate reductions with GD≤29.
* Ideal: improve both.
* AND depth 3 is already optimal, so preserve it.

8. A35 / AD3 / G183 / GD13 — `aes-sbox-a35-ad3-g183-gd13-xx148-29.circ.txt`
* Hard limits: A≤35, AD≤3.
* Primary: GD≤12, preferably with G≤183.
* Secondary: reduce G substantially while preserving GD≤13.
* A significant depth improvement is valuable even if total gates increase modestly; record that as an explicit tradeoff.
* Never sacrifice AND depth 3.

9. A45 / AD4 / G141 / GD12 — `aes-sbox-a45-ad4-g141-gd12-xx96-25.circ.txt`
* Hard limits: A≤45, AD≤4.
* Primary: G<141 while GD≤12.
* Equally interesting: GD≤11 while keeping G≤141.
* A major depth improvement with a modest gate-count penalty may be retained separately.
* Ideal: improve both.

10. A59 / AD4 / G159 / GD10 — `aes-sbox-a59-ad4-g159-gd10-xxn100-30-3.circ.txt`
* Hard limits: A≤59, AD≤4.
* Primary: G<159 while preserving GD≤10.
* Ambitious alternative: GD≤9, preferably without increasing G.
* Record worthwhile depth reductions with modest gate-count tradeoffs separately.
* Treat depth 10 as the best currently listed depth, not a proven lower bound.

27 ANDs is still among the main objectives. You may spawn as many subagents as useful.

For each target, maintain:
* Best strict improvement and best permitted tradeoff.
* Exact A, AD, G and GD.
* Starting circuit, search method, seed, elapsed time and verification.
* Comparison against both its specified NIST reference and the complete pinned NIST collection.
* Whether the result was already known in our archive, newly discovered, or reproduced.

Verify every saved circuit independently against all 256 AES inputs. Preserve the full Pareto frontier rather than selecting only one winner.
Keep results, logs, failed experiments, configurations and reproduction instructions organized for eventual publication, following the documentation standard of XORFlux.
