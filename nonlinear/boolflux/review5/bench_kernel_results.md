# Gate kernel speed: f9fe6f7 vs the review-5 commits

Written by `review5/bench_kernel.sh` on 2026-11-15 06:47 UTC.  20000 iterations per run, seeds 1,2, 3 repetitions (minimum taken), gcc -O3 -march=native, one CPU per (workload, seed) group: CPUs 8 9 10 11 12 13 14 15.  Time = user CPU seconds of the kernel process (/usr/bin/time); load on the same core or its hyperthread still inflates it, so use idle CPUs.  "same" = best/final/move lines and the result circuit are identical to f9fe6f7.

| commit | subject |
|---|---|
| f9fe6f7 | Hub long3 results, scheduler hot op registration, study agents H1-H4/R |
| 695a90b | Review 5 kernel K1-K3: line-based config reader (comment no longer eat |
| 764ac97 | Review 5 kernel P1-P3 (same trajectories): pair table with GF(2)-linea |
| d221d2b | Review 5 kernel K4, S1, S2 (all off by default, default trajectories u |
| 162953b | Review 5 kernel S3 + bench: nl_root (AND-like roots only / all divisor |

| workload | seed | f9fe6f7 s | 695a90b s | 764ac97 s | d221d2b s | 162953b s | 695a90b/f9fe6f7 | 764ac97/f9fe6f7 | d221d2b/f9fe6f7 | 162953b/f9fe6f7 | trajectories | final (162953b) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| polish-a29 (a,ad,cost,gd; caps A29 AD5) | 1 | 8.38 | 7.07 | 5.73 | 5.71 | 5.08 | 0.844 | 0.684 | 0.681 | 0.606 | same same same same | G 137 A 29 GD 31 AD 5 |
| polish-a29 (a,ad,cost,gd; caps A29 AD5) | 2 | 8.37 | 6.95 | 5.78 | 5.69 | 5.08 | 0.830 | 0.691 | 0.680 | 0.607 | same same same same | G 136 A 29 GD 30 AD 5 |
| cost-a32 (cost,gd; no caps) | 1 | 8.00 | 7.85 | 5.73 | 5.22 | 5.34 | 0.981 | 0.716 | 0.652 | 0.667 | same same same same | G 103 A 32 GD 32 AD 7 |
| cost-a32 (cost,gd; no caps) | 2 | 7.97 | 8.02 | 5.63 | 5.28 | 5.25 | 1.006 | 0.706 | 0.662 | 0.659 | same same same same | G 103 A 32 GD 32 AD 7 |
| descend-a29 (caps A29 AD5 GD20 from G182) | 1 | 6.69 | 6.67 | 6.28 | 5.97 | 5.03 | 0.997 | 0.939 | 0.892 | 0.752 | same same same same | G 166 A 29 GD 20 AD 5 |
| descend-a29 (caps A29 AD5 GD20 from G182) | 2 | 6.64 | 6.90 | 6.41 | 6.26 | 5.09 | 1.039 | 0.965 | 0.943 | 0.767 | same same same same | G 167 A 29 GD 20 AD 5 |
| repair-a32 (cap GD24 from GD30) | 1 | 6.29 | 6.42 | 5.83 | 5.92 | 5.74 | 1.021 | 0.927 | 0.941 | 0.913 | same same same same | G 107 A 32 GD 24 AD 5 |
| repair-a32 (cap GD24 from GD30) | 2 | 6.49 | 6.65 | 6.16 | 6.11 | 5.67 | 1.025 | 0.949 | 0.941 | 0.874 | same same same same | G 108 A 33 GD 24 AD 5 |
| **total** | | 58.83 | 56.53 | 47.55 | 46.16 | 42.28 | **0.961** | **0.808** | **0.785** | **0.719** | all same | |

Total wall time of this benchmark: 123 s.
