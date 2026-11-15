# T4 status (goal G: A <= 44, AD <= 4, G <= 140, GD <= 11)

Updated 2026-11-15 03:35 UTC.

## Best verified (all aes_check OK on pin 3d80774, all new Pareto points; files in
`~/xs-campaigns/2026-11-15-study/T4/found/` with JSON sidecars)

| A | AD | G | GD | file | note |
|---:|---:|---:|---:|---|---|
| 42 | 4 | 301 | 11 | t4-a42-ad4-g301-gd11-kernel.circ.txt | A, AD, GD meet goal G; G does not |
| 42 | 4 | 452 | 11 | t4-a42-ad4-g452-gd11-depthsynth.circ.txt | construction (also -b01 variant, 454) |
| 42 | 4 | 230 | 12 | t4-a42-ad4-g230-gd12-kernel.circ.txt | |
| 43 | 4 | 278 | 11 | t4-a43-ad4-g278-gd11-kernel.circ.txt | |
| 44 | 4 | 254 | 11 | t4-a44-ad4-g254-gd11-kernel.circ.txt | |
| 46 | 4 | 203 | 11 | t4-a46-ad4-g203-gd11-kernel.circ.txt | |
| 47 | 4 | 186 | 11 | t4-a47-ad4-g186-gd11-kernel.circ.txt | |

Before: ours 48/4/151/11 and 43/4/141/12; published 49/4/148/11 and 45/4/141/12.

## Running (all end by 06:35 UTC)
- CPU 9: queue/session_tail.sh -> polish_job.sh 42/4/301/11 gate seed 21 (run-s42g21), verified into found/ at the end
- CPU 8: s42/runmix2.sh (p2/p3 mixed basis search, log s42/runmix2.log), then polish_job.sh trb seed 22 (run-s42t22)

## Overnight
QUEUE.md section "T4: kernel polish ..." (polish_job.sh, 5 jobs).
