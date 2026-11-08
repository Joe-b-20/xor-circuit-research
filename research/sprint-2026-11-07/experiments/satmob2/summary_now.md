## Component structures [checked: comp_*.json, fac_*.json]

Local fan structure at the member state (satmob's method) and the plateau's coupled factor at that state.

| circuit | plateau (radices) | depth | plateau core | local core | local mobile | neutral moves | local components (shapes) | coupled factor: choice size / locally core / local comps touched / roots (targets) | coupled instance (k, tW, free) | whole mobile part (k, tW, free) |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|
| kste:3146 | kste#43 33x3^7 | 8 | 45 | 47 | 9 | 18 | 9 (1+1 x9) | 4 / 2 / [0, 7] / 3 (1) | (12, 6, 5) | (36, 16, 19) |
| kste:2229 | kste#34 45x3^4 | 7 | 48 | 49 | 7 | 14 | 7 (1+1 x7) | 4 / 1 / [1, 5, 6] / 3 (2) | (17, 7, 9) | (27, 12, 14) |
| kste:1557 | kste#41 108x3^4 | 7 | 46 | 48 | 8 | 16 | 8 (1+1 x8) | 6 / 2 / [1, 2, 3, 7] / 4 (4) | (10, 4, 5) | (32, 13, 18) |
| sampleA:109 | hunt 2101x15x11x3x3 | 8 | 40 | 48 | 8 | 22 | 7 (1+1 x6, 2+1 x1) | 10 / 7 / [0, 1, 2] / 8 (8) | (18, 8, 9) | (22, 11, 10) |
| sampleA:48 | hunt 18927x15x3x3 | 9 | 40 | 45 | 11 | 29 | 9 (1+1 x6, 1+2 x1, 2+1 x1, 2+2 x1) | 12 / 5 / [0, 2, 4, 6, 7, 8] / 11 (9) | (31, 15, 15) | (29, 13, 15) |
| sampleA:781 | giant 62856x3 | 9 | 37 | 48 | 8 | 16 | 8 (1+1 x8) | 18 / 11 / [1, 2, 3, 4, 5, 6, 7] / 13 (11) | (36, 15, 20) | (28, 13, 14) |
| sampleC:131 | giant 69228x3x3 | 12 | 39 | 50 | 6 | 12 | 6 (1+1 x6) | 15 / 11 / [0, 1, 4, 5] / 11 (10) | (38, 17, 20) | (21, 10, 10) |

Per-circuit local components (k, tW, free) in component order, and the plateau's 3-way factors seen locally:

* kste:3146 (kste#43 33x3^7): local c0:1+1(7,4,2) c1:1+1(7,4,2) c2:1+1(4,2,1) c3:1+1(12,6,5) c4:1+1(5,2,2) c5:1+1(4,2,1) c6:1+1(2,1,0) c7:1+1(3,2,0) c8:1+1(4,2,1); plateau factors (radix | choice size | local comps) f0:r33|4|[0, 7] f1:r3|1|[5] f2:r3|1|[3] f3:r3|1|[4] f4:r3|1|[1] f5:r3|1|[6] f6:r3|1|[2] f7:r3|1|[8]
* kste:2229 (kste#34 45x3^4): local c0:1+1(3,2,0) c1:1+1(2,1,0) c2:1+1(4,2,1) c3:1+1(3,2,0) c4:1+1(4,2,1) c5:1+1(12,5,6) c6:1+1(3,2,0); plateau factors (radix | choice size | local comps) f0:r45|4|[1, 5, 6] f1:r3|1|[3] f2:r3|1|[0] f3:r3|1|[2] f4:r3|1|[4]
* kste:1557 (kste#41 108x3^4): local c0:1+1(4,2,1) c1:1+1(2,1,0) c2:1+1(5,2,2) c3:1+1(2,1,0) c4:1+1(4,2,1) c5:1+1(11,6,4) c6:1+1(4,2,1) c7:1+1(3,2,0); plateau factors (radix | choice size | local comps) f0:r108|6|[1, 2, 3, 7] f1:r3|1|[0] f2:r3|1|[5] f3:r3|1|[6] f4:r3|1|[4]
* sampleA:109 (hunt 2101x15x11x3x3): local c0:1+1(2,1,0) c1:1+1(5,3,1) c2:1+1(4,2,1) c3:2+1(5,2,2) c4:1+1(4,2,1) c5:1+1(2,1,0) c6:1+1(3,2,0); plateau factors (radix | choice size | local comps) f0:r2101|10|[0, 1, 2] f1:r15|2|[3] f2:r11|2|[6] f3:r3|1|[4] f4:r3|1|[5]
* sampleA:48 (hunt 18927x15x3x3): local c0:2+2(7,3,3) c1:1+1(3,2,0) c2:1+1(3,2,0) c3:2+1(5,2,2) c4:1+1(9,4,4) c5:1+1(2,1,0) c6:1+2(7,4,2) c7:1+1(2,1,0) c8:1+1(7,4,2); plateau factors (radix | choice size | local comps) f0:r18927|12|[0, 2, 4, 6, 7, 8] f1:r15|2|[3] f2:r3|1|[1] f3:r3|1|[5]
* sampleA:781 (giant 62856x3): local c0:1+1(7,4,2) c1:1+1(4,2,1) c2:1+1(3,2,0) c3:1+1(3,2,0) c4:1+1(8,4,3) c5:1+1(2,1,0) c6:1+1(7,4,2) c7:1+1(4,2,1); plateau factors (radix | choice size | local comps) f0:r62856|18|[1, 2, 3, 4, 5, 6, 7] f1:r3|1|[0]
* sampleC:131 (giant 69228x3x3): local c0:1+1(4,2,1) c1:1+1(3,2,0) c2:1+1(7,4,2) c3:1+1(4,2,1) c4:1+1(4,2,1) c5:1+1(3,2,0); plateau factors (radix | choice size | local comps) f0:r69228|15|[0, 1, 4, 5] f1:r3|1|[3] f2:r3|1|[2]

## Instance table [measured]

One row per distinct (circuit, W, pool); best record kept.  free = k - 1 - tW.  F = plateau coupled factor window (fac.py), M = local fan component window (mob2.py, satmob's method).  prior = sat/ campaigns' result on the identical (circuit, W) if any.

| circuit | scope | level | k | tW | free | pool | result | wall s | solve s | clauses | prior (sat/) |
|---|---|---|---:|---:|---:|---|---|---:|---:|---:|---|
| kste:3146 | F:f0(r33) | factor | 12 | 6 | 5 | full | TIMEOUT(120s) | 121.0 | - | - | - |
| kste:2229 | F:f0(r45) | factor | 17 | 7 | 9 | full | TIMEOUT(120s) | 121.1 | - | - | - |
| kste:1557 | F:f0(r108) | factor | 10 | 4 | 5 | full | TIMEOUT(120s) | 121.1 | - | - | - |
| sampleA:109 | F:f0(r2101) | factor | 18 | 8 | 9 | full | TIMEOUT(120s) | 121.0 | - | - | - |
| kste:3146 | M:c6 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.02 | 15470 | - |
| kste:3146 | M:c7 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.04 | 31170 | - |
| kste:3146 | M:c2 | 1 | 4 | 2 | 1 | full | UNSAT | 0.7 | 0.58 | 46953 | - |
| kste:3146 | M:c5 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.19 | 46935 | - |
| kste:3146 | M:c8 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.18 | 46887 | - |
| kste:3146 | M:c4 | 1 | 5 | 2 | 2 | full | UNSAT | 1.0 | 0.78 | 62680 | - |
| kste:3146 | M:c0 | 1 | 7 | 4 | 2 | full | UNSAT | 2.9 | 2.6 | 94924 | - |
| kste:3146 | M:c1 | 1 | 7 | 4 | 2 | full | UNSAT | 4.7 | 4.31 | 94948 | - |
| kste:3146 | M:c6+c7 | 2 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.17 | 46875 | - |
| kste:3146 | M:c2+c6 | 2 | 6 | 3 | 2 | full | UNSAT | 2.5 | 2.32 | 78740 | - |
| kste:3146 | M:c5+c6 | 2 | 6 | 3 | 2 | full | UNSAT | 1.8 | 1.49 | 78710 | - |
| kste:3146 | M:c6+c8 | 2 | 6 | 3 | 2 | full | UNSAT | 2.6 | 2.41 | 78630 | - |
| kste:3146 | M:c2+c7 | 2 | 7 | 4 | 2 | full | UNSAT | 7.1 | 6.75 | 94864 | - |
| kste:3146 | M:c5+c7 | 2 | 7 | 4 | 2 | full | UNSAT | 3.3 | 3.01 | 94828 | - |
| kste:3146 | M:c2+c8 | 2 | 7 | 3 | 3 | full | UNSAT | 9.9 | 9.73 | 94659 | - |
| kste:3146 | M:c4+c7 | 2 | 7 | 3 | 3 | full | UNSAT | 10.2 | 9.95 | 94563 | - |
| kste:3146 | M:c0+c6 | 2 | 8 | 4 | 3 | full | UNSAT | 23.3 | 23.02 | 110927 | - |
| kste:3146 | M:c2+c5 | 2 | 8 | 4 | 3 | full | UNSAT | 18.5 | 18.19 | 110997 | - |
| kste:3146 | M:c5+c8 | 2 | 8 | 4 | 3 | full | UNSAT | 18.1 | 17.8 | 110843 | - |
| kste:3146 | M:c7+c8 | 2 | 8 | 4 | 3 | full | UNSAT | 18.9 | 18.57 | 110745 | - |
| kste:3146 | M:c1+c6 | 2 | 9 | 5 | 3 | full | UNSAT | 39.8 | 39.45 | 127319 | - |
| kste:3146 | M:c1+c7 | 2 | 10 | 6 | 3 | full | UNSAT | 116.0 | 115.8 | 143795 | - |
| kste:2229 | M:c1 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.02 | 15432 | - |
| kste:2229 | M:c0 | 1 | 3 | 2 | 0 | full | UNSAT | 0.3 | 0.07 | 31118 | - |
| kste:2229 | M:c3 | 1 | 3 | 2 | 0 | full | UNSAT | 0.3 | 0.08 | 31098 | - |
| kste:2229 | M:c6 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.03 | 31102 | - |
| kste:2229 | M:c2 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.2 | 46791 | - |
| kste:2229 | M:c4 | 1 | 4 | 2 | 1 | full | UNSAT | 0.5 | 0.24 | 46791 | - |
| kste:2229 | M:c0+c1 | 2 | 5 | 3 | 1 | full | UNSAT | 0.8 | 0.61 | 62705 | - |
| kste:2229 | M:c1+c3 | 2 | 5 | 3 | 1 | full | UNSAT | 0.8 | 0.61 | 62665 | - |
| kste:2229 | M:c0+c3 | 2 | 6 | 4 | 1 | full | UNSAT | 0.9 | 0.77 | 78711 | - |
| kste:2229 | M:c0+c6 | 2 | 6 | 4 | 1 | full | UNSAT | 0.8 | 0.58 | 78721 | - |
| kste:2229 | M:c3+c6 | 2 | 6 | 4 | 1 | full | UNSAT | 1.0 | 0.65 | 78671 | - |
| kste:2229 | M:c1+c2 | 2 | 6 | 3 | 2 | full | UNSAT | 2.1 | 1.83 | 78510 | - |
| kste:2229 | M:c1+c4 | 2 | 6 | 3 | 2 | full | UNSAT | 2.6 | 2.33 | 78510 | - |
| kste:2229 | M:c1+c6 | 2 | 6 | 3 | 2 | full | UNSAT | 1.9 | 1.66 | 78550 | - |
| kste:2229 | M:c2+c3 | 2 | 6 | 3 | 2 | full | UNSAT | 1.6 | 1.44 | 78510 | - |
| kste:2229 | M:c0+c2 | 2 | 7 | 4 | 2 | full | UNSAT | 4.8 | 4.55 | 94660 | - |
| kste:2229 | M:c0+c4 | 2 | 7 | 4 | 2 | full | UNSAT | 3.2 | 2.99 | 94660 | - |
| kste:2229 | M:c2+c6 | 2 | 7 | 4 | 2 | full | UNSAT | 3.4 | 3.21 | 94612 | - |
| kste:2229 | M:c3+c4 | 2 | 7 | 4 | 2 | full | UNSAT | 3.9 | 3.68 | 94600 | - |
| kste:2229 | M:c4+c6 | 2 | 7 | 4 | 2 | full | UNSAT | 3.4 | 3.12 | 94612 | - |
| kste:2229 | M:c2+c4 | 2 | 8 | 4 | 3 | full | UNSAT | 16.1 | 15.85 | 110605 | - |
| kste:1557 | M:c1 | 1 | 2 | 1 | 0 | full | UNSAT | 0.1 | 0.02 | 15422 | - |
| kste:1557 | M:c3 | 1 | 2 | 1 | 0 | full | UNSAT | 0.1 | 0.02 | 15422 | - |
| kste:1557 | M:c7 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.03 | 31082 | - |
| kste:1557 | M:c0 | 1 | 4 | 2 | 1 | full | UNSAT | 0.3 | 0.15 | 46779 | - |
| kste:1557 | M:c4 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.2 | 46773 | - |
| kste:1557 | M:c6 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.19 | 46773 | - |
| kste:1557 | M:c2 | 1 | 5 | 2 | 2 | full | UNSAT | 1.5 | 1.15 | 62520 | - |
| kste:1557 | M:c3+c7 | 2 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.24 | 46767 | - |
| kste:1557 | M:c1+c7 | 2 | 5 | 3 | 1 | full | UNSAT | 0.6 | 0.32 | 62633 | - |
| kste:1557 | M:c1+c3 | 2 | 5 | 2 | 2 | full | UNSAT | 0.8 | 0.69 | 62520 | - |
| kste:1557 | M:c0+c1 | 2 | 6 | 3 | 2 | full | UNSAT | 1.8 | 1.69 | 78490 | - |
| kste:1557 | M:c0+c3 | 2 | 6 | 3 | 2 | full | UNSAT | 1.5 | 1.19 | 78490 | - |
| kste:1557 | M:c1+c6 | 2 | 6 | 3 | 2 | full | UNSAT | 2.8 | 2.53 | 78480 | - |
| kste:1557 | M:c3+c4 | 2 | 6 | 3 | 2 | full | UNSAT | 3.1 | 2.88 | 78480 | - |
| kste:1557 | M:c3+c6 | 2 | 6 | 3 | 2 | full | UNSAT | 2.1 | 1.87 | 78480 | - |
| kste:1557 | M:c4+c7 | 2 | 7 | 4 | 2 | full | UNSAT | 3.3 | 3.08 | 94576 | - |
| kste:1557 | M:c6+c7 | 2 | 7 | 4 | 2 | full | UNSAT | 3.3 | 3.12 | 94576 | - |
| kste:1557 | M:c0+c4 | 2 | 7 | 3 | 3 | full | UNSAT | 7.1 | 6.86 | 94419 | - |
| kste:1557 | M:c1+c2 | 2 | 7 | 3 | 3 | full | UNSAT | 10.4 | 10.16 | 94383 | - |
| kste:1557 | M:c1+c4 | 2 | 7 | 3 | 3 | full | UNSAT | 10.3 | 10.02 | 94431 | - |
| kste:1557 | M:c2+c7 | 2 | 7 | 3 | 3 | full | UNSAT | 11.6 | 11.18 | 94395 | - |
| kste:1557 | M:c0+c6 | 2 | 8 | 4 | 3 | full | UNSAT | 16.6 | 16.21 | 110605 | - |
| kste:1557 | M:c0+c7 | 2 | 8 | 4 | 3 | full | UNSAT | 13.4 | 13.01 | 110647 | - |
| kste:1557 | M:c4+c6 | 2 | 8 | 4 | 3 | full | UNSAT | 17.9 | 17.52 | 110591 | - |
| sampleA:109 | M:c0 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.03 | 15444 | - |
| sampleA:109 | M:c5 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.02 | 15444 | - |
| sampleA:109 | M:c6 | 1 | 3 | 2 | 0 | full | UNSAT | 0.4 | 0.07 | 31146 | - |
| sampleA:109 | M:c2 | 1 | 4 | 2 | 1 | full | UNSAT | -0.6 | 0.13 | 46833 | - |
| sampleA:109 | M:c4 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.16 | 46845 | - |
| sampleA:109 | M:c1 | 1 | 5 | 3 | 1 | full | UNSAT | 0.4 | 0.24 | 62769 | - |
| sampleA:109 | M:c3 | 1 | 5 | 2 | 2 | full | UNSAT | 1.4 | 1.14 | 62624 | - |
| sampleA:109 | M:c0+c5 | 2 | 4 | 2 | 1 | full | UNSAT | 0.5 | 0.28 | 46821 | - |
| sampleA:109 | M:c0+c6 | 2 | 5 | 3 | 1 | full | UNSAT | 0.9 | 0.69 | 62753 | - |
| sampleA:109 | M:c5+c6 | 2 | 5 | 3 | 1 | full | UNSAT | 1.0 | 0.69 | 62753 | - |
| sampleA:109 | M:c0+c1 | 2 | 6 | 3 | 2 | full | UNSAT | 1.3 | 1.03 | 78630 | - |
| sampleA:109 | M:c0+c4 | 2 | 6 | 3 | 2 | full | UNSAT | 2.6 | 2.28 | 78590 | - |
| sampleA:109 | M:c2+c5 | 2 | 6 | 3 | 2 | full | UNSAT | 2.0 | 1.75 | 78570 | - |
| sampleA:109 | M:c4+c5 | 2 | 6 | 3 | 2 | full | UNSAT | 2.2 | 1.88 | 78590 | - |
| sampleA:109 | M:c1+c5 | 2 | 7 | 4 | 2 | full | UNSAT | 3.9 | 3.62 | 94744 | - |
| sampleA:109 | M:c2+c6 | 2 | 7 | 4 | 2 | full | UNSAT | 4.7 | 4.35 | 94744 | - |
| sampleA:109 | M:c4+c6 | 2 | 7 | 4 | 2 | full | UNSAT | 4.4 | 4.04 | 94768 | - |
| sampleA:109 | M:c1+c6 | 2 | 8 | 5 | 2 | full | UNSAT | 5.9 | 5.64 | 111068 | - |
| sampleA:109 | M:c0+c3 | 2 | 7 | 3 | 3 | full | UNSAT | 9.8 | 9.51 | 94527 | - |
| sampleA:109 | M:c3+c5 | 2 | 7 | 3 | 3 | full | UNSAT | 6.6 | 6.29 | 94527 | - |
| sampleA:109 | M:c1+c2 | 2 | 8 | 4 | 3 | full | UNSAT | 25.5 | 25.22 | 110787 | - |
| sampleA:109 | M:c2+c4 | 2 | 8 | 4 | 3 | full | UNSAT | 19.0 | 18.77 | 110731 | - |
| sampleA:109 | M:c3+c6 | 2 | 8 | 4 | 3 | full | UNSAT | 29.0 | 28.75 | 110815 | - |
| sampleA:109 | M:c1+c4 | 2 | 9 | 5 | 3 | full | UNSAT | 35.2 | 34.82 | 127159 | - |
| sampleA:48 | M:c5 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.02 | 15450 | - |
| sampleA:48 | M:c7 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.02 | 15452 | - |
| sampleA:48 | M:c1 | 1 | 3 | 2 | 0 | full | UNSAT | 0.3 | 0.03 | 31146 | - |
| sampleA:48 | M:c2 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.04 | 31134 | - |
| sampleA:48 | M:c3 | 1 | 5 | 2 | 2 | full | UNSAT | 1.7 | 1.48 | 62648 | - |
| sampleA:48 | M:c6 | 1 | 7 | 4 | 2 | full | UNSAT | 2.2 | 2.01 | 94828 | - |
| sampleA:48 | M:c8 | 1 | 7 | 4 | 2 | full | UNSAT | 3.6 | 3.28 | 94756 | - |
| sampleA:48 | M:c0 | 1 | 7 | 3 | 3 | full | UNSAT | 6.3 | 6.03 | 94611 | - |
| sampleA:48 | M:c2+c7 | 2 | 4 | 2 | 1 | full | UNSAT | 0.3 | 0.16 | 46845 | - |
| sampleA:48 | M:c5+c7 | 2 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.2 | 46845 | - |
| sampleA:48 | M:c1+c5 | 2 | 5 | 3 | 1 | full | UNSAT | 0.9 | 0.74 | 62753 | - |
| sampleA:48 | M:c1+c7 | 2 | 5 | 3 | 1 | full | UNSAT | 0.8 | 0.63 | 62761 | - |
| sampleA:48 | M:c2+c5 | 2 | 5 | 3 | 1 | full | UNSAT | 0.6 | 0.36 | 62729 | - |
| sampleA:48 | M:c1+c2 | 2 | 6 | 4 | 1 | full | UNSAT | 1.0 | 0.76 | 78771 | - |
| sampleA:48 | M:c3+c5 | 2 | 7 | 3 | 3 | full | UNSAT | 8.0 | 7.8 | 94563 | - |
| sampleA:48 | M:c3+c7 | 2 | 7 | 3 | 3 | full | UNSAT | 12.0 | 11.74 | 94575 | - |
| sampleA:48 | M:c1+c3 | 2 | 8 | 4 | 3 | full | UNSAT | 25.0 | 24.53 | 110815 | - |
| sampleA:48 | M:c2+c3 | 2 | 8 | 4 | 3 | full | UNSAT | 25.3 | 24.89 | 110773 | - |
| sampleA:48 | M:c2+c8 | 2 | 8 | 4 | 3 | full | UNSAT | 17.8 | 17.48 | 110773 | - |
| sampleA:48 | M:c7+c8 | 2 | 8 | 4 | 3 | full | UNSAT | 20.2 | 19.93 | 110787 | - |
| sampleA:48 | M:c2+c6 | 2 | 9 | 5 | 3 | full | UNSAT | 49.5 | 49.0 | 127207 | - |
| sampleA:48 | M:c5+c6 | 2 | 9 | 5 | 3 | full | UNSAT | 57.8 | 57.61 | 127207 | - |
| sampleA:48 | M:c1+c6 | 2 | 10 | 6 | 3 | full | TIMEOUT(120s) | 122.1 | - | - | - |
| sampleA:48 | M:c1+c8 | 2 | 10 | 6 | 3 | full | UNSAT | 94.8 | 94.49 | 143633 | - |
| sampleA:781 | M:c5 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.02 | 15470 | - |
| sampleA:781 | M:c2 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.05 | 31186 | - |
| sampleA:781 | M:c3 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.05 | 31186 | - |
| sampleA:781 | M:c1 | 1 | 4 | 2 | 1 | full | UNSAT | 0.3 | 0.16 | 46917 | - |
| sampleA:781 | M:c7 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.25 | 46851 | - |
| sampleA:781 | M:c0 | 1 | 7 | 4 | 2 | full | UNSAT | 1.4 | 1.14 | 94864 | - |
| sampleA:781 | M:c6 | 1 | 7 | 4 | 2 | full | UNSAT | 2.0 | 1.69 | 94912 | - |
| sampleA:781 | M:c4 | 1 | 8 | 4 | 3 | full | UNSAT | 11.1 | 10.58 | 110885 | - |
| sampleA:781 | M:c2+c5 | 2 | 5 | 3 | 1 | full | UNSAT | 0.0 | 0.75 | 62833 | - |
| sampleA:781 | M:c3+c5 | 2 | 5 | 3 | 1 | full | UNSAT | 0.9 | 0.73 | 62833 | - |
| sampleA:781 | M:c2+c3 | 2 | 6 | 4 | 1 | full | UNSAT | 1.3 | 0.9 | 78901 | - |
| sampleA:781 | M:c2+c7 | 2 | 6 | 3 | 2 | full | UNSAT | 1.9 | 1.53 | 78630 | - |
| sampleA:781 | M:c5+c7 | 2 | 6 | 3 | 2 | full | UNSAT | 2.7 | 2.44 | 78600 | - |
| sampleA:781 | M:c1+c3 | 2 | 7 | 4 | 2 | full | UNSAT | 5.4 | 5.17 | 94876 | - |
| sampleA:781 | M:c3+c7 | 2 | 7 | 4 | 2 | full | UNSAT | 3.1 | 2.85 | 94744 | - |
| sampleA:781 | M:c0+c3 | 2 | 8 | 4 | 3 | full | UNSAT | 15.5 | 15.18 | 110941 | - |
| sampleA:781 | M:c1+c2 | 2 | 8 | 4 | 3 | full | UNSAT | 42.2 | 42.04 | 110983 | - |
| sampleA:781 | M:c1+c7 | 2 | 8 | 4 | 3 | full | UNSAT | 30.5 | 30.16 | 110759 | - |
| sampleA:781 | M:c0+c5 | 2 | 9 | 5 | 3 | full | UNSAT | 32.4 | 31.91 | 127255 | - |
| sampleA:781 | M:c5+c6 | 2 | 9 | 5 | 3 | full | UNSAT | 36.5 | 36.27 | 127319 | - |
| sampleA:781 | M:c0+c2 | 2 | 10 | 6 | 3 | full | UNSAT | 51.6 | 51.21 | 143795 | - |
| sampleA:781 | M:c2+c6 | 2 | 10 | 6 | 3 | full | UNSAT | 110.1 | 109.79 | 143867 | - |
| sampleA:781 | M:c3+c6 | 2 | 10 | 6 | 3 | full | UNSAT | 85.6 | 84.98 | 143867 | - |
| sampleC:131 | M:c1 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.03 | 31154 | - |
| sampleC:131 | M:c5 | 1 | 3 | 2 | 0 | full | UNSAT | 0.3 | 0.07 | 31158 | - |
| sampleC:131 | M:c0 | 1 | 4 | 2 | 1 | full | UNSAT | 0.3 | 0.12 | 46851 | - |
| sampleC:131 | M:c3 | 1 | 4 | 2 | 1 | full | UNSAT | 0.6 | 0.29 | 46845 | - |
| sampleC:131 | M:c4 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.17 | 46881 | - |
| sampleC:131 | M:c2 | 1 | 7 | 4 | 2 | full | UNSAT | 2.7 | 2.32 | 94804 | - |
| sampleC:131 | M:c1+c5 | 2 | 6 | 4 | 1 | full | UNSAT | 1.5 | 1.1 | 78821 | - |
| sampleC:131 | M:c1+c3 | 2 | 6 | 3 | 2 | full | UNSAT | 2.6 | 2.29 | 78610 | - |
| sampleC:131 | M:c0+c1 | 2 | 7 | 4 | 2 | full | UNSAT | 3.4 | 3.1 | 94732 | - |
| sampleC:131 | M:c0+c5 | 2 | 7 | 4 | 2 | full | UNSAT | 5.2 | 4.78 | 94744 | - |
| sampleC:131 | M:c1+c4 | 2 | 7 | 4 | 2 | full | UNSAT | 3.7 | 3.49 | 94792 | - |
| sampleC:131 | M:c3+c5 | 2 | 7 | 4 | 2 | full | UNSAT | 2.2 | 1.87 | 94732 | - |
| sampleC:131 | M:c4+c5 | 2 | 7 | 4 | 2 | full | UNSAT | 5.5 | 5.14 | 94804 | - |
| sampleC:131 | M:c0+c4 | 2 | 7 | 3 | 3 | full | UNSAT | 9.3 | 8.93 | 94563 | - |
| sampleC:131 | M:c0+c3 | 2 | 8 | 4 | 3 | full | UNSAT | 21.9 | 21.58 | 110689 | - |
| sampleC:131 | M:c2+c5 | 2 | 8 | 4 | 3 | full | UNSAT | 11.4 | 11.06 | 110871 | - |
| sampleC:131 | M:c3+c4 | 2 | 8 | 4 | 3 | full | UNSAT | 26.3 | 25.98 | 110759 | - |
| sampleC:131 | M:c1+c2 | 2 | 10 | 6 | 3 | full | UNSAT | 55.9 | 55.44 | 143687 | - |

## Counts per circuit and level [measured]

| circuit | level | pool | instances | UNSAT | SAT | TIMEOUT | max solved free | UNSAT solve-time median / max (s) |
|---|---|---|---:|---:|---:|---:|---:|---|
| kste:3146 | 1 | full | 8 | 8 | 0 | 0 | 2 | 0.6 / 4.3 |
| kste:3146 | 2 | full | 14 | 14 | 0 | 0 | 3 | 9.9 / 115.8 |
| kste:3146 | factor | full | 1 | 0 | 0 | 1 | - | - |
| kste:2229 | 1 | full | 6 | 6 | 0 | 0 | 1 | 0.1 / 0.2 |
| kste:2229 | 2 | full | 15 | 15 | 0 | 0 | 3 | 1.8 / 15.8 |
| kste:2229 | factor | full | 1 | 0 | 0 | 1 | - | - |
| kste:1557 | 1 | full | 7 | 7 | 0 | 0 | 2 | 0.1 / 1.1 |
| kste:1557 | 2 | full | 17 | 17 | 0 | 0 | 3 | 3.1 / 17.5 |
| kste:1557 | factor | full | 1 | 0 | 0 | 1 | - | - |
| sampleA:109 | 1 | full | 7 | 7 | 0 | 0 | 2 | 0.1 / 1.1 |
| sampleA:109 | 2 | full | 17 | 17 | 0 | 0 | 3 | 4.0 / 34.8 |
| sampleA:109 | factor | full | 1 | 0 | 0 | 1 | - | - |
| sampleA:48 | 1 | full | 8 | 8 | 0 | 0 | 3 | 1.5 / 6.0 |
| sampleA:48 | 2 | full | 16 | 15 | 0 | 1 | 3 | 11.7 / 94.5 |
| sampleA:781 | 1 | full | 8 | 8 | 0 | 0 | 3 | 0.2 / 10.6 |
| sampleA:781 | 2 | full | 15 | 15 | 0 | 0 | 3 | 15.2 / 109.8 |
| sampleC:131 | 1 | full | 6 | 6 | 0 | 0 | 2 | 0.2 / 2.3 |
| sampleC:131 | 2 | full | 12 | 12 | 0 | 0 | 3 | 5.1 / 55.4 |

## Hardness by free values (full pool) [measured]

| free | instances | UNSAT | TIMEOUT | UNSAT solve s min / median / max |
|---:|---:|---:|---:|---|
| 0 | 21 | 21 | 0 | 0.0 / 0.0 / 0.1 |
| 1 | 37 | 37 | 0 | 0.1 / 0.3 / 1.1 |
| 2 | 51 | 51 | 0 | 0.7 / 2.4 / 6.8 |
| 3 | 47 | 46 | 1 | 6.0 / 18.8 / 115.8 |
| 5 | 2 | 0 | 2 | - |
| 9 | 2 | 0 | 2 | - |

Totals: 160 distinct instances: {'UNSAT': 155, 'TIMEOUT': 5}; solver wall 2123 s
