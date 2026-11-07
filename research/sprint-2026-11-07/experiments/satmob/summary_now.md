## Results table [measured]

One row per distinct (circuit, W, pool); best record kept (UNSAT/SAT over TIMEOUT, longest TIMEOUT).  free = k - 1 - tW.  prior = the sat/ campaigns' result for the identical (circuit, W) if any (full pool only).

| circuit | scope | level | k | tW | free | pool | result | wall s | solve s | clauses | prior (sat/) |
|---|---|---:|---:|---:|---:|---|---|---:|---:|---:|---|
| repo | M:c0 | 1 | 2 | 1 | 0 | full | UNSAT | 0.1 | 0.02 | 15412 | - |
| repo | M:c1 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.04 | 31082 | - |
| repo | M:c6 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.04 | 31058 | - |
| repo | M:c2 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.19 | 46743 | UNSAT@60s |
| repo | M:c5 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.25 | 46743 | UNSAT@60s |
| repo | M:c4 | 1 | 5 | 2 | 2 | full | UNSAT | 1.5 | 1.34 | 62480 | UNSAT@60s |
| repo | M:c3 | 1 | 8 | 4 | 3 | full | UNSAT | 12.4 | 11.99 | 110563 | - |
| repo | M:c0+c6 | 2 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.29 | 46731 | UNSAT@60s |
| repo | M:c0+c1 | 2 | 5 | 3 | 1 | full | UNSAT | 0.5 | 0.28 | 62633 | UNSAT@900s |
| repo | M:c1+c6 | 2 | 6 | 4 | 1 | full | UNSAT | 1.0 | 0.83 | 78621 | - |
| repo | M:c0+c2 | 2 | 6 | 3 | 2 | full | UNSAT | 1.5 | 1.33 | 78430 | UNSAT@900s |
| repo | M:c0+c5 | 2 | 6 | 3 | 2 | full | UNSAT | 1.9 | 1.75 | 78430 | UNSAT@900s |
| repo | M:c1+c2 | 2 | 7 | 4 | 2 | full | UNSAT | 3.2 | 2.96 | 94576 | - |
| repo | M:c1+c5 | 2 | 7 | 4 | 2 | full | UNSAT | 3.3 | 3.09 | 94576 | UNSAT@900s |
| repo | M:c2+c6 | 2 | 7 | 4 | 2 | full | UNSAT | 3.8 | 3.54 | 94504 | - |
| repo | M:c4+c6 | 2 | 7 | 3 | 3 | full | UNSAT | 7.9 | 7.68 | 94323 | UNSAT@900s |
| repo | M:c1+c4 | 2 | 8 | 4 | 3 | full | UNSAT | 20.3 | 20.14 | 110577 | UNSAT@900s |
| repo | M:c2+c5 | 2 | 8 | 4 | 3 | full | UNSAT | 15.5 | 15.84 | 110521 | UNSAT@900s |
| repo | M:c5+c6 | 2 | 8 | 4 | 3 | full | UNSAT | 12.0 | 11.76 | 110535 | - |
| repo | M:c0+c3 | 2 | 9 | 4 | 4 | full | UNSAT | 84.2 | 83.92 | 126630 | UNSAT@900s |
| repo | M:c2+c4 | 2 | 9 | 4 | 4 | full | TIMEOUT(120s) | 122.4 | - | - | - |
| repo | M:c4+c5 | 2 | 9 | 4 | 4 | full | TIMEOUT(120s) | 122.4 | - | - | - |
| repo | M:c1+c3 | 2 | 11 | 6 | 4 | full | TIMEOUT(120s) | 122.4 | - | - | - |
| repo | M:c3+c5 | 2 | 11 | 5 | 5 | full | TIMEOUT(120s) | 122.4 | - | - | - |
| repo | M:c2+c3 | 2 | 12 | 6 | 5 | full | TIMEOUT(120s) | 122.7 | - | - | - |
| repo | M:c3+c4 | 2 | 12 | 5 | 6 | full | TIMEOUT(120s) | 122.3 | - | - | - |
| sampleA:2667 | M:c1 | 1 | 3 | 2 | 0 | full | UNSAT | 0.3 | 0.07 | 31090 | - |
| sampleA:2667 | M:c3 | 1 | 3 | 2 | 0 | full | UNSAT | 0.3 | 0.05 | 31086 | - |
| sampleA:2667 | M:c2 | 1 | 4 | 2 | 1 | full | UNSAT | 0.5 | 0.23 | 46755 | UNSAT@1800s |
| sampleA:2667 | M:c4 | 1 | 5 | 3 | 1 | full | UNSAT | 0.5 | 0.31 | 62705 | UNSAT@1800s |
| sampleA:2667 | M:c0 | 1 | 8 | 4 | 3 | full | UNSAT | 12.2 | 11.92 | 110703 | - |
| sampleA:2667 | M:c5 | 1 | 8 | 4 | 3 | full | UNSAT | 11.6 | 11.14 | 110521 | - |
| sampleA:2667 | M:c1+c3 | 2 | 6 | 4 | 1 | full | UNSAT | 1.1 | 0.78 | 78651 | - |
| sampleA:2667 | M:c1+c2 | 2 | 7 | 4 | 2 | full | UNSAT | 3.5 | 3.29 | 94552 | - |
| sampleA:2667 | M:c2+c3 | 2 | 7 | 4 | 2 | full | UNSAT | 3.7 | 3.48 | 94540 | - |
| sampleA:2667 | M:c1+c4 | 2 | 8 | 5 | 2 | full | UNSAT | 5.9 | 5.42 | 110914 | - |
| sampleA:2667 | M:c3+c4 | 2 | 8 | 5 | 2 | full | UNSAT | 5.2 | 4.97 | 110900 | - |
| sampleA:2667 | M:c2+c4 | 2 | 9 | 5 | 3 | full | UNSAT | 48.3 | 47.77 | 126967 | - |
| sampleA:2667 | M:c0+c1 | 2 | 10 | 5 | 4 | full | TIMEOUT(120s) | 122.8 | - | - | - |
| sampleA:2667 | M:c0+c4 | 2 | 10 | 5 | 4 | full | TIMEOUT(120s) | 122.1 | - | - | - |
| sampleA:2667 | M:c0+c3 | 2 | 11 | 6 | 4 | full | TIMEOUT(120s) | 122.1 | - | - | - |
| sampleA:2667 | M:c1+c5 | 2 | 11 | 6 | 4 | full | TIMEOUT(120s) | 122.0 | - | - | - |
| sampleA:2667 | M:c3+c5 | 2 | 11 | 6 | 4 | full | TIMEOUT(120s) | 122.0 | - | - | - |
| sampleA:2667 | M:c0+c2 | 2 | 12 | 6 | 5 | full | TIMEOUT(120s) | 122.0 | - | - | - |
| sampleA:2667 | M:c4+c5 | 2 | 13 | 7 | 5 | full | TIMEOUT(120s) | 122.0 | - | - | - |
| sampleA:2667 | M:c0+c5 | 2 | 16 | 8 | 7 | full | TIMEOUT(120s) | 121.9 | - | - | - |
| sampleA:884 | M:c4 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.04 | 31138 | - |
| sampleA:884 | M:c0 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.21 | 46869 | UNSAT@1800s |
| sampleA:884 | M:c3 | 1 | 4 | 2 | 1 | full | UNSAT | 0.5 | 0.21 | 46851 | UNSAT@1800s |
| sampleA:884 | M:c5 | 1 | 4 | 2 | 1 | full | UNSAT | 0.6 | 0.31 | 46857 | UNSAT@1800s |
| sampleA:884 | M:c6 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.16 | 46785 | UNSAT@1800s |
| sampleA:884 | M:c2 | 1 | 5 | 3 | 1 | full | UNSAT | 0.5 | 0.31 | 62761 | - |
| sampleA:884 | M:c1 | 1 | 7 | 4 | 2 | full | UNSAT | 1.5 | 1.14 | 94732 | - |
| sampleA:884 | M:c2+c3 | 2 | 6 | 3 | 2 | full | UNSAT | 2.5 | 2.32 | 78640 | UNSAT@1800s |
| sampleA:884 | M:c4+c6 | 2 | 6 | 3 | 2 | full | UNSAT | 1.8 | 1.57 | 78510 | - |
| sampleA:884 | M:c0+c4 | 2 | 7 | 4 | 2 | full | UNSAT | 4.0 | 3.74 | 94768 | - |
| sampleA:884 | M:c3+c4 | 2 | 7 | 4 | 2 | full | UNSAT | 4.7 | 4.21 | 94732 | - |
| sampleA:884 | M:c4+c5 | 2 | 7 | 4 | 2 | full | UNSAT | 4.8 | 4.56 | 94744 | - |
| sampleA:884 | M:c2+c4 | 2 | 8 | 5 | 2 | full | UNSAT | 7.3 | 7.01 | 110998 | - |
| sampleA:884 | M:c0+c3 | 2 | 7 | 3 | 3 | full | UNSAT | 7.5 | 7.22 | 94587 | - |
| sampleA:884 | M:c0+c2 | 2 | 8 | 4 | 3 | full | UNSAT | 22.7 | 22.33 | 110829 | - |
| sampleA:884 | M:c0+c5 | 2 | 8 | 4 | 3 | full | UNSAT | 22.7 | 22.39 | 110815 | - |
| sampleA:884 | M:c0+c6 | 2 | 8 | 4 | 3 | full | UNSAT | 14.2 | 13.89 | 110647 | - |
| sampleA:884 | M:c3+c5 | 2 | 8 | 4 | 3 | full | UNSAT | 22.9 | 22.6 | 110773 | - |
| sampleA:884 | M:c3+c6 | 2 | 8 | 4 | 3 | full | UNSAT | 22.5 | 22.18 | 110605 | - |
| sampleA:884 | M:c5+c6 | 2 | 8 | 4 | 3 | full | UNSAT | 19.5 | 19.04 | 110619 | - |
| sampleA:884 | M:c2+c5 | 2 | 9 | 5 | 3 | full | UNSAT | 53.4 | 53.01 | 127143 | - |
| sampleA:884 | M:c2+c6 | 2 | 9 | 5 | 3 | full | UNSAT | 41.4 | 41.04 | 126951 | - |
| sampleA:884 | M:c1+c4 | 2 | 10 | 6 | 3 | full | UNSAT | 71.0 | 70.68 | 143579 | - |
| sampleA:884 | M:c1+c5 | 2 | 9 | 4 | 4 | full | TIMEOUT(120s) | 121.9 | - | - | UNSAT@900s |
| sampleA:884 | M:c0+c1 | 2 | 11 | 6 | 4 | full | TIMEOUT(120s) | 121.8 | - | - | - |
| sampleA:884 | M:c1+c3 | 2 | 11 | 6 | 4 | full | TIMEOUT(120s) | 121.8 | - | - | - |
| sampleA:884 | M:c1+c6 | 2 | 11 | 6 | 4 | full | TIMEOUT(120s) | 121.8 | - | - | - |
| sampleA:884 | M:c1+c2 | 2 | 12 | 7 | 4 | full | TIMEOUT(120s) | 122.6 | - | - | - |
| sampleC:1011 | M:c1 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.02 | 15448 | - |
| sampleC:1011 | M:c2 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.02 | 15448 | - |
| sampleC:1011 | M:c5 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.03 | 15448 | - |
| sampleC:1011 | M:c3 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.19 | 46851 | UNSAT@1800s |
| sampleC:1011 | M:c0 | 1 | 5 | 2 | 2 | full | UNSAT | 0.3 | 0.73 | 62656 | UNSAT@1800s |
| sampleC:1011 | M:c4 | 1 | 8 | 4 | 3 | full | UNSAT | 22.4 | 22.16 | 110815 | - |
| sampleC:1011 | M:c1+c2 | 2 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.28 | 46839 | - |
| sampleC:1011 | M:c1+c5 | 2 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.18 | 46839 | - |
| sampleC:1011 | M:c2+c5 | 2 | 4 | 2 | 1 | full | UNSAT | 0.7 | 0.44 | 46839 | - |
| sampleC:1011 | M:c1+c3 | 2 | 6 | 3 | 2 | full | UNSAT | 1.6 | 1.42 | 78610 | - |
| sampleC:1011 | M:c2+c3 | 2 | 6 | 3 | 2 | full | UNSAT | 1.6 | 1.38 | 78610 | - |
| sampleC:1011 | M:c3+c5 | 2 | 6 | 3 | 2 | full | UNSAT | 2.0 | 1.76 | 78610 | - |
| sampleC:1011 | M:c0+c1 | 2 | 7 | 3 | 3 | full | UNSAT | 8.6 | 8.4 | 94587 | - |
| sampleC:1011 | M:c0+c2 | 2 | 7 | 3 | 3 | full | UNSAT | 7.8 | 7.63 | 94587 | - |
| sampleC:1011 | M:c0+c5 | 2 | 7 | 3 | 3 | full | UNSAT | 10.3 | 10.03 | 94587 | - |
| sampleC:1011 | M:c0+c3 | 2 | 9 | 4 | 4 | full | TIMEOUT(120s) | 122.3 | - | - | - |
| sampleC:1011 | M:c2+c4 | 2 | 10 | 5 | 4 | full | TIMEOUT(120s) | 122.2 | - | - | - |
| sampleC:1011 | M:c4+c5 | 2 | 10 | 5 | 4 | full | TIMEOUT(120s) | 122.2 | - | - | - |
| sampleC:1011 | M:c3+c4 | 2 | 12 | 6 | 5 | full | TIMEOUT(120s) | 122.2 | - | - | - |
| sampleC:1011 | M:c0+c4 | 2 | 13 | 6 | 6 | full | TIMEOUT(120s) | 122.2 | - | - | - |

## Counts per circuit and level [measured]

| circuit | level | pool | instances | UNSAT | SAT | TIMEOUT | max solved free | max solved k | UNSAT solve-time median / max (s) |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| repo | 1 | full | 7 | 7 | 0 | 0 | 3 | 8 | 0.2 / 12.0 |
| repo | 2 | full | 19 | 13 | 0 | 6 | 4 | 9 | 3.1 / 83.9 |
| sampleA:2667 | 1 | full | 6 | 6 | 0 | 0 | 3 | 8 | 0.3 / 11.9 |
| sampleA:2667 | 2 | full | 14 | 6 | 0 | 8 | 3 | 9 | 5.0 / 47.8 |
| sampleA:884 | 1 | full | 7 | 7 | 0 | 0 | 2 | 7 | 0.2 / 1.1 |
| sampleA:884 | 2 | full | 21 | 16 | 0 | 5 | 3 | 10 | 19.0 / 70.7 |
| sampleC:1011 | 1 | full | 6 | 6 | 0 | 0 | 3 | 8 | 0.2 / 22.2 |
| sampleC:1011 | 2 | full | 14 | 9 | 0 | 5 | 3 | 7 | 1.4 / 10.0 |

## Hardness by free values (all circuits, full pool) [measured]

| free | instances | UNSAT | TIMEOUT | UNSAT solve s min / median / max |
|---:|---:|---:|---:|---|
| 0 | 9 | 9 | 0 | 0.0 / 0.0 / 0.1 |
| 1 | 17 | 17 | 0 | 0.2 / 0.3 / 0.8 |
| 2 | 21 | 21 | 0 | 0.7 / 3.0 / 7.0 |
| 3 | 22 | 22 | 0 | 7.2 / 19.0 / 70.7 |
| 4 | 17 | 1 | 16 | 83.9 / 83.9 / 83.9 |
| 5 | 5 | 0 | 5 | - |
| 6 | 2 | 0 | 2 | - |
| 7 | 1 | 0 | 1 | - |

## Component statistics per circuit [checked: comp_*.json]

| circuit | depth | core | mobile | neutral moves | components | shapes (mobile+roots) | per-component (k, tW, free) | whole mobile part (k, tW, free) | values with >1 split |
|---|---:|---:|---:|---:|---:|---|---|---|---:|
| repo | 5 | 49 | 7 | 14 | 7 | 1+1 x7 | (2,1,0) (3,2,0) (4,2,1) (8,4,3) (5,2,2) (4,2,1) (3,2,0) | (23,10,12) | 61 |
| sampleA:1626 | 8 | 48 | 8 | 16 | 8 | 1+1 x8 | (4,2,1) (3,2,0) (4,2,1) (7,4,2) (2,1,0) (4,2,1) (3,2,0) (4,2,1) | (30,14,15) | 64 |
| sampleA:1773 | 8 | 47 | 9 | 20 | 9 | 1+1 x9 | (6,3,2) (12,6,5) (9,5,3) (4,2,1) (5,2,2) (3,2,0) (4,2,1) (2,1,0) (4,2,1) | (32,14,17) | 63 |
| sampleA:2667 | 8 | 50 | 6 | 16 | 6 | 1+1 x6 | (8,4,3) (3,2,0) (4,2,1) (3,2,0) (5,3,1) (8,4,3) | (23,12,10) | 64 |
| sampleA:884 | 7 | 49 | 7 | 16 | 7 | 1+1 x7 | (4,2,1) (7,4,2) (5,3,1) (4,2,1) (3,2,0) (4,2,1) (4,2,1) | (24,11,12) | 64 |
| sampleC:1011 | 12 | 49 | 7 | 18 | 6 | 1+1 x5, 2+1 x1 | (5,2,2) (2,1,0) (2,1,0) (4,2,1) (8,4,3) (2,1,0) | (21,10,10) | 64 |

Totals: 94 distinct instances: {'UNSAT': 70, 'TIMEOUT': 24}; solver wall 3580 s
