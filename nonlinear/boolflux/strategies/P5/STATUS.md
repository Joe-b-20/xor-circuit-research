# P5 status (T05 AND-depth half)

Updated 2026-11-15 22:55 UTC.  **No P5 job is running** (all stopped 22:52).

Best per AND depth at A <= 32 (best G, then GD), within T05's hard limits (A <= 32, AD <= 7):
| AD | best G/GD | file | status |
|---|---|---|---|
| 7 | 103/32 | NIST reference | P4's half |
| 6 | 104 (any AD6 104 is dominated by the AD5 104/29) | archive 3f7a2fec7b7d.bfx (104/31) | [C, case S] 103 impossible |
| 5 | 104/29 | archive E-polish 104/29 | [C, case S] 103 impossible; P5 runs: 105/28 (dominated by NIST 105/26) |
| 4 | **111/25** (certified, new) | found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt | also certified 111/26, **112/22**, 112/23, 113/20, 113/21 |
| 3 | none at A <= 32 | | [C, tower layout] impossible |

A32/AD4 frontier from P5 (certified): 111/25, 112/22, 113/20 (P3 had 113/20 uncertified, 114/19).
Bars at the start: AD4 114/26 (archive), 113/20 (P3, 17:4x).

Overnight queue: P5-ad4lin (QUEUE.md); P5-allbasis-d4 is done.
