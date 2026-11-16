# Overnight runner status

Updated 2026-11-16T10:38:21Z. Plan `/home/joebachir20/xs-campaigns/2026-11-16-night/plan.json` (night-2026-11-16). Root `/home/joebachir20/xs-campaigns/2026-11-16-night`. Deadline 13:30:00 UTC (hard stop). Runner pid 166647. Leftover pool 161.8 min (carry mode flagged).

| block | target | state | planned min | start | end/stop | jobs done | running | new files | beyond known (class) |
|---|---|---|---|---|---|---|---|---|---|
| T05 | T05 | done | 90 | 02:04:29 | 03:34:38 | 121 | 0 | 64 | 32/7/103/29 (strict), 32/7/104/26 (other), 32/5/105/24 (tradeoff:and_depth_for_gates), 32/5/106/21 (tradeoff:and_depth_for_gates) |
| T03 | T03 | early-stopped | 120 | 03:34:38 | 04:48:08 | 89 | 0 | 30 | 28/5/125/24 (other) |
| T01 | T01 | early-stopped | 60 | 04:48:08 | 05:33:21 | 72 | 0 | 18 | - |
| T06 | T06 | early-stopped | 60 | 05:33:21 | 06:27:03 | 120 | 0 | 6 | 34/4/122/14 (other), 34/4/123/14 (other), 34/4/124/14 (other) |
| T10 | T10 | done | 15 | 06:27:03 | 06:42:09 | 40 | 0 | 4 | - |
| T07 | T07 | early-stopped | 110 | 06:42:09 | 07:45:43 | 200 | 0 | 14 | 35/3/138/23 (strict) |
| T04 | T04 | early-stopped | 75 | 07:45:43 | 08:52:41 | 88 | 0 | 24 | 32/4/119/16 (other) |
| T08 | T08 | early-stopped | 70 | 08:52:41 | 09:22:59 | 60 | 0 | 8 | - |
| T09 | T09 | done | 45 | 09:22:59 | 10:08:05 | 76 | 0 | 16 | 37/4/127/13 (other), 37/4/128/13 (other), 39/4/135/12 (strict), 38/4/135/12 (strict) |
| T02 | T02 | done | 30 | 10:08:05 | 10:38:15 | 46 | 0 | 11 | - |

## Frontier per target (ROOT/<T>/found, (G, GD) Pareto within the hard limits; class by TARGETS.json)

- T05 (ref 32/7/103/32): 64 files; frontier 103@29 strict, 104@26, 105@24 tradeoff, 106@21 tradeoff, 108@20 tradeoff, 110@19 tradeoff, 111@18 tradeoff, 115@17 tradeoff, 120@16 tradeoff, 127@15 tradeoff
- T03 (ref 28/5/128/20): 30 files; frontier 125@24, 126@23, 127@22, 128@21, 129@20, 131@19, 133@18, 136@17
- T01 (ref 28/4/132/22): 18 files; frontier 131@22 strict, 132@20 strict, 135@19, 136@18
- T06 (ref 34/4/139/13): 6 files; frontier 122@14, 135@13 strict
- T10 (ref 59/4/159/10): 4 files; frontier 148@11
- T07 (ref 35/3/139/27): 14 files; frontier 138@23 strict, 140@22
- T04 (ref 32/4/117/19): 24 files; frontier 112@21 tradeoff, 113@20 tradeoff, 114@19 strict, 115@18 strict, 117@17 strict, 119@16, 126@15
- T08 (ref 35/3/183/13): 8 files; frontier 165@13 strict, 189@12 tradeoff
- T09 (ref 45/4/141/12): 16 files; frontier 127@13, 135@12 strict
- T02 (ref 28/4/176/14): 11 files; frontier 152@17, 155@16, 160@15, 174@14 strict
