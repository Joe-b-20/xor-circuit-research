# H1 status

Updated 2026-11-15 00:50 UTC. CPU 12.

Running: `xs-H-h1-zdfs2` (CPU 12, started 00:40): exhaustive dim Z <= 2 case of 13-member (or
12-member over 10+5 / 9+6 prefixes) GF(4)-norm last layers, 5 prefixes x 16 gamma, ~20 s each.
Log `~/xs-campaigns/2026-11-15-study/H1/zdfs2/run.log`. Next on CPU 12: track C's zdfs/zdfs3
over umizame's prefix, gamma none, k = 13, (dim Z, rank) = (3,3), (3,4), (4,4)
(`~/xs-campaigns/2026-11-15-study/H1/zdfs/queue.sh`).

Done: per-AND XAG analysis of 63 circuits, decomposition, junk ranks, keep-sets, z/rank map,
n-block equations verified, MC >= 13 [P], TRICKS.md. Stopped: rho2 SAT (positive control did not
finish in 13 min; see NOTES section 6).
Best: no circuit (not a search agent).
