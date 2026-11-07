| # | run | map | matrix | cap | trial wh | started from | repo best <=cap | NIST | result <=cap (arm) | gain@cap | gain any (point) | slack | nearest prior depth | prior wh: cap / cap>= / total | 1st imp (min) | 1st gain (min) | last own drop (min, frac) | class |
|---|---|---|---|---:|---:|---|---|---|---|---:|---|---:|---:|---|---:|---:|---|---|
| 1 | x1a | grostl | 8x8/GF(2^8) | 12 | 2 | NIST 410@12; root | 366@12 | 410@12 | 364@11 (nist) | 2 | 4 (364@11 (was 368@11)) | 0 | 0 | 4 / 8 / 20 | 0 | 43 | 45 (0.74) | slowing |
| 2 | x1a | skop15-8x8-gf16 | 8x8/GF(2^4) | 19 | 2 | NIST 170@19; root | 146@14 | 170@19 | 151@13 (nist) | -5 | 46 (157@11 (was 203@5)) | 5 | 0 | 0 / 1 / 2 | 0 | - | 22 (0.36) | plateaued |
| 3 | x1a | klsw17-m-8x8-gf256-inv | 8x8/GF(2^8) | 12 | 2 | NIST 368@12; root | 346@12 | 368@12 | 327@12 (nist) | 19 | 19 (326@13 (was 345@13)) | 0 | 0 | 0 / 1 / 2 | 0 | 4 | 37 (0.61) | slowing |
| 4 | pt1 | skop15-8x8-gf16 | 8x8/GF(2^4) | 19 | 4 | NIST 170@19; ours 146@14 | 146@14 | 170@19 | 146@14 (nist/ours) | 0 | 0 (146@14 (was 146@14)) | 5 | 0 | 2 / 3 / 4 | 0 | - | 56 (0.46) | plateaued |
| 5 | pt1 | ss17-8x8-gf16 | 8x8/GF(2^4) | 10 | 4 | NIST 178@10; ours 167@10 | 167@10 | 178@10 | 161@10 (nist) | 6 | 10 (164@9 (was 174@9)) | 0 | 0 | 0 / 1 / 2 | 0 | 0 | 71 (0.59) | slowing |
| 6 | pt1 | klsw17-m-8x8-gf256-inv | 8x8/GF(2^8) | 12 | 4 | NIST 368@12; ours 346@12 | 346@12 | 368@12 | 330@12 (nist) | 16 | 23 (338@11 (was 361@11)) | 0 | 0 | 2 / 3 / 4 | 0 | 1 | 110 (0.92) | still improving |
| 7 | pt2 | khazad | 8x8/GF(2^8) | 18 | 4 | NIST 366@18; ours 345@15 | 345@15 | 366@18 | 340@15 (nist) | 5 | 88 (344@14 (was 432@11)) | 3 | 0 | 0 / 1 / 17 | 0 | 4 | 38 (0.32) | plateaued |
| 8 | pt2 | fox-mu8 | 8x8/GF(2^8) | 14 | 4 | NIST 540@14; ours 505@11 | 505@11 | 540@14 | 500@11 (ours) | 5 | 5 (500@11 (was 505@11)) | 3 | 0 | 0 / 10 / 210 | 0 | 3 | 90 (0.75) | still improving |
| 9 | sw1 | grostl | 8x8/GF(2^8) | 16 | 1 | ours 350@16 | 350@16 | 410@12 | 349@15 (ours) | 1 | 9 (349@15 (was 358@15)) | 0 | 0 | 0 / 4 / 22 | 6 | 6 | 6 (0.1) | plateaued |
| 10 | sw1 | khazad | 8x8/GF(2^8) | 18 | 1 | ours 345@15 | 345@15 | 366@18 | 343@16 (ours) | 2 | 2 (343@16 (was 345@15)) | 3 | 1 | 4 / 5 / 21 | 8 | 8 | 45 (0.75) | slowing |
| 11 | sw1 | whirlpool-maelstrom | 8x8/GF(2^8) | 11 | 1 | ours 394@9 | 394@9 | 425@11 | 390@10 (ours) | 4 | 4 (390@10 (was 394@9)) | 2 | 1 | 0 / 6 / 17 | 1 | 1 | 44 (0.73) | slowing |
| 12 | sw1 | fox-mu8 | 8x8/GF(2^8) | 14 | 1 | ours 505@11 | 505@11 | 540@14 | 500@11 (ours) | 5 | 5 (500@11 (was 505@11)) | 3 | 0 | 4 / 14 / 214 | 7 | 7 | 30 (0.49) | plateaued |
| 13 | sw1 | jpst17-8x8-gf256-inv | 8x8/GF(2^8) | 11 | 1 | ours 493@11 | 493@11 | 528@11 | 493@11 (ours) | 0 | 2 (494@10 (was 496@10)) | 0 | 0 | 0 / 1 / 2 | - | - | - (-) | no drop |
| 14 | sw1 | bkl16-8x8-gf256 | 8x8/GF(2^8) | 10 | 1 | ours 442@10 | 442@10 | 465@10 | 439@9 (ours) | 3 | 4 (439@9 (was 443@9)) | 0 | 0 | 0 / 1 / 2 | 2 | 2 | 7 (0.12) | plateaued |
| 15 | sw2 | klsw17-m-8x8-gf256 | 8x8/GF(2^8) | 11 | 1 | ours 347@6 | 347@6 | 364@11 | 321@10 (ours) | 26 | 26 (321@10 (was 347@6)) | 5 | 2 | 0 / 1 / 2 | 0 | 0 | 58 (0.96) | still improving |
| 16 | sw2 | skop15-8x8-gf256 | 8x8/GF(2^8) | 8 | 1 | ours 418@8 | 418@8 | 445@8 | 417@8 (ours) | 1 | 2 (416@9 (was 418@8)) | 0 | 0 | 0 / 1 / 2 | 19 | 19 | 19 (0.32) | plateaued |
| 17 | sw2 | skop15-8x8-gf256-inv | 8x8/GF(2^8) | 13 | 1 | ours 331@13 | 331@13 | 348@13 | 322@13 (ours) | 9 | 10 (323@12 (was 333@12)) | 0 | 0 | 0 / 1 / 2 | 0 | 0 | 44 (0.74) | slowing |
| 18 | sw2 | ss17-8x8-gf256 | 8x8/GF(2^8) | 9 | 1 | ours 392@8 | 392@8 | 418@9 | 390@8 (ours) | 2 | 3 (389@10 (was 392@8)) | 1 | 0 | 0 / 1 / 2 | 22 | 22 | 27 (0.46) | plateaued |
| 19 | sw2 | ls16-8x8-gf256 | 8x8/GF(2^8) | 9 | 1 | ours 404@8 | 404@8 | 427@9 | 403@8 (ours) | 1 | 1 (403@8 (was 404@8)) | 1 | 0 | 0 / 1 / 2 | 41 | 41 | 41 (0.69) | slowing |
| 20 | sw2 | klsw17-m-8x8-gf16-0x13-inv | 8x8/GF(2^4) | 12 | 1 | ours 163@12 | 163@12 | 176@12 | 163@11 (ours) | 0 | 27 (164@10 (was 191@6)) | 0 | 0 | 0 / 1 / 2 | - | - | - (-) | no drop |
| 21 | x1a | lw16-4x4-gf256-inv-circ | 4x4/GF(2^8) | 7 | 2 | NIST 89@7; root | 82@5 | 89@7 | 82@5 (fresh/nist) | 0 | 0 (82@5 (was 82@5)) | 2 | 0 | 0 / 1 / 2 | 0 | - | 1 (0.01) | plateaued |
| 22 | x1b | ss16-4x4-gf256 | 4x4/GF(2^8) | 6 | 2 | NIST 104@6; root | 97@6 | 104@6 | 96@5 (fresh) | 1 | 2 (96@5 (was 98@4)) | 0 | 1 | 0 / 1 / 2 | 0 | 1 | 12 (0.2) | plateaued |
| 23 | x1b | jpst17-4x4-gf256 | 4x4/GF(2^8) | 7 | 2 | NIST 82@7; root | 78@6 | 82@7 | 78@6 (fresh/nist) | 0 | 2 (80@5 (was 82@4)) | 1 | 0 | 0 / 1 / 2 | 0 | - | 1 (0.02) | plateaued |
| 24 | x1b | aes-mixcolumns | 4x4/GF(2^8) | 5 | 2 | ours 88@5; root | 88@5 | 88@5 | 88@5 (ours) | 0 | 0 (88@5 (was 88@5)) | 0 | 0 | 0 / 0 / 0 | - | - | - (-) | no drop |
| 25 | x1b | small-scale-aes | 4x4/GF(2^4) | 5 | 2 | NIST 43@5; root | 42@5 | 43@5 | 42@5 (fresh/nist) | 0 | 0 (42@5 (was 42@5)) | 0 | 0 | 6 / 6 / 7 | 19 | - | 19 (0.31) | plateaued |
| 26 | pt2 | skop15-4x4-gf256-inv | 4x4/GF(2^8) | 6 | 4 | NIST 91@6; ours 88@6 | 88@6 | 91@6 | 88@6 (nist/ours) | 0 | 1 (89@5 (was 90@4)) | 0 | 0 | 0 / 1 / 2 | 0 | - | 1 (0.01) | plateaued |
| 27 | pt2 | anubis-clefia-m0 | 4x4/GF(2^8) | 9 | 4 | NIST 98@9; ours 92@8 | 92@8 | 98@9 | 91@8 (nist/ours) | 1 | 2 (92@6 (was 94@6)) | 1 | 0 | 0 / 1 / 2 | 0 | 10 | 10 (0.09) | plateaued |


Per-worker table (what each worker started from and reached; 'drops' = times its own best at <= cap fell below its start):

| run | worker | start | best <=cap | best any | drops | restarts | first imp (s) | last drop (s) | it/s | sources of improvements |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| x1a | grostl-fresh-00 | root | 582@12 | 582@12 | 62 | 130 | - | 3393 | 308.7 | {"fresh": 34, "restart:best": 130, "best": 112} |
| x1a | grostl-nist-00 | NIST 410@12 | 364@11 | 364@11 | 44 | 8 | 5 | 2682 | 457.6 | {"seed": 50, "restart:best": 8, "best": 47} |
| x1a | skop15-8x8-gf16-fresh-00 | root | 157@11 | 157@11 | 47 | 0 | - | 801 | 752.8 | {"fresh": 120} |
| x1a | skop15-8x8-gf16-nist-00 | NIST 170@19 | 151@13 | 151@13 | 19 | 0 | 0 | 1304 | 548.6 | {"seed": 56} |
| x1a | klsw17-m-8x8-gf256-inv-fresh-00 | root | 398@12 | 398@12 | 381 | 48 | - | 3574 | 382.7 | {"fresh": 484, "restart:best": 48, "best": 133} |
| x1a | klsw17-m-8x8-gf256-inv-nist-00 | NIST 368@12 | 327@12 | 327@12 | 40 | 5 | 6 | 2203 | 534.7 | {"seed": 38, "restart:best": 5, "best": 45} |
| x1a | lw16-4x4-gf256-inv-circ-fresh-00 | root | 82@5 | 82@5 | 41 | 2 | - | 54 | 1373.1 | {"fresh": 60, "restart:fresh": 2} |
| x1a | lw16-4x4-gf256-inv-circ-nist-00 | NIST 89@7 | 82@5 | 82@5 | 7 | 1 | 1 | 31 | 1407.7 | {"seed": 19, "restart:fresh": 1} |
| x1b | ss16-4x4-gf256-fresh-00 | root | 96@5 | 96@5 | 8 | 2 | - | 78 | 1807.4 | {"fresh": 19, "restart:fresh": 2} |
| x1b | ss16-4x4-gf256-nist-00 | NIST 104@6 | 97@5 | 97@5 | 7 | 2 | 2 | 724 | 1602.6 | {"seed": 18, "restart:best": 1, "restart:fresh": 1} |
| x1b | jpst17-4x4-gf256-fresh-00 | root | 78@6 | 78@6 | 12 | 1 | - | 216 | 1977.7 | {"fresh": 28, "restart:fresh": 1} |
| x1b | jpst17-4x4-gf256-nist-00 | NIST 82@7 | 78@6 | 78@6 | 4 | 1 | 2 | 85 | 2014.2 | {"seed": 10, "restart:fresh": 1, "fresh": 1} |
| x1b | aes-mixcolumns-fresh-00 | root | 89@5 | 89@5 | 18 | 35 | - | 243 | 1895.5 | {"fresh": 25, "restart:best": 34, "best": 8, "restart:fresh": 1} |
| x1b | aes-mixcolumns-nist-00 | ours 88@5 | 88@5 | 88@5 | 0 | 2 | - | - | 2314.4 | {"restart:fresh": 2} |
| x1b | small-scale-aes-fresh-00 | root | 42@5 | 42@5 | 17 | 2 | - | 20 | 2435.0 | {"fresh": 23, "restart:best": 1, "best": 8, "restart:fresh": 1} |
| x1b | small-scale-aes-nist-00 | NIST 43@5 | 42@5 | 42@5 | 1 | 2 | 1117 | 1117 | 2656.4 | {"seed": 1, "restart:best": 1, "best": 1, "restart:fresh": 1} |
| pt1 | skop15-8x8-gf16-00 | ours 146@14 | 146@14 | 146@14 | 0 | 2 | - | - | 735.6 | {"seed": 1, "restart:fresh": 2} |
| pt1 | skop15-8x8-gf16-01 | NIST 170@19 | 146@14 | 146@14 | 20 | 1 | 1 | 3333 | 583.5 | {"seed": 66, "restart:shared": 1} |
| pt1 | ss17-8x8-gf16-00 | ours 167@10 | 165@9 | 165@9 | 2 | 3 | 23 | 1962 | 933.0 | {"seed": 4, "restart:best": 3, "best": 4} |
| pt1 | ss17-8x8-gf16-01 | NIST 178@10 | 161@10 | 161@10 | 17 | 4 | 3 | 4232 | 865.0 | {"seed": 42, "restart:best": 4, "best": 2} |
| pt1 | klsw17-m-8x8-gf256-inv-00 | ours 346@12 | 331@12 | 331@12 | 15 | 15 | 45 | 7077 | 572.0 | {"seed": 1, "restart:best": 15, "best": 32} |
| pt1 | klsw17-m-8x8-gf256-inv-01 | NIST 368@12 | 330@12 | 330@12 | 36 | 18 | 10 | 6608 | 558.5 | {"seed": 37, "restart:best": 18, "best": 51} |
| pt2 | skop15-4x4-gf256-inv-00 | ours 88@6 | 88@6 | 88@6 | 0 | 20 | - | - | 1621.1 | {"seed": 1, "restart:best": 19, "restart:fresh": 1, "fresh": 1} |
| pt2 | skop15-4x4-gf256-inv-01 | NIST 91@6 | 88@6 | 88@6 | 3 | 27 | 6 | 64 | 1689.9 | {"seed": 4, "restart:best": 27, "best": 4} |
| pt2 | anubis-clefia-m0-00 | ours 92@8 | 91@8 | 91@8 | 1 | 4 | 617 | 617 | 1460.0 | {"seed": 5, "restart:fresh": 2, "restart:best": 2} |
| pt2 | anubis-clefia-m0-01 | NIST 98@9 | 91@8 | 91@8 | 5 | 4 | 1 | 5248 | 1360.9 | {"seed": 11, "restart:best": 1, "restart:elite": 1, "elite": 2, "restart:fresh": 1, "fresh": 3, "restart:shared": 1, "shared": 1, "donor:anubis-clefia-m0-00": 1} |
| pt2 | khazad-00 | ours 345@15 | 342@16 | 342@16 | 3 | 0 | 268 | 3558 | 332.0 | {"seed": 8} |
| pt2 | khazad-01 | NIST 366@18 | 340@15 | 340@15 | 25 | 0 | 9 | 2275 | 343.6 | {"seed": 75} |
| pt2 | fox-mu8-00 | ours 505@11 | 500@11 | 500@11 | 5 | 0 | 185 | 5417 | 447.6 | {"seed": 13} |
| pt2 | fox-mu8-01 | NIST 540@14 | 508@11 | 508@11 | 32 | 0 | 12 | 3543 | 422.2 | {"seed": 92} |
| sw1 | grostl-00 | ours 350@16 | 349@15 | 349@15 | 1 | 0 | 377 | 377 | 515.3 | {"seed": 4} |
| sw1 | khazad-00 | ours 345@15 | 343@16 | 343@16 | 2 | 0 | 483 | 2693 | 377.0 | {"seed": 4} |
| sw1 | whirlpool-maelstrom-00 | ours 394@9 | 390@10 | 390@10 | 4 | 0 | 86 | 2628 | 624.1 | {"seed": 12} |
| sw1 | fox-mu8-00 | ours 505@11 | 500@11 | 500@11 | 5 | 0 | 446 | 1776 | 504.2 | {"seed": 17} |
| sw1 | jpst17-8x8-gf256-inv-00 | ours 493@11 | 493@11 | 493@11 | 0 | 1 | - | - | 509.3 | {"seed": 2, "restart:best": 1, "best": 1} |
| sw1 | bkl16-8x8-gf256-00 | ours 442@10 | 439@9 | 439@9 | 3 | 0 | 111 | 421 | 585.3 | {"seed": 8} |
| sw2 | klsw17-m-8x8-gf256-00 | ours 347@6 | 321@10 | 321@10 | 26 | 2 | 4 | 3466 | 734.7 | {"seed": 23, "restart:best": 2, "best": 42} |
| sw2 | skop15-8x8-gf256-00 | ours 418@8 | 417@8 | 417@8 | 1 | 1 | 1163 | 1163 | 671.1 | {"seed": 3, "restart:best": 1} |
| sw2 | skop15-8x8-gf256-inv-00 | ours 331@13 | 322@13 | 322@13 | 9 | 4 | 14 | 2650 | 537.6 | {"seed": 13, "restart:best": 4, "best": 8} |
| sw2 | ss17-8x8-gf256-00 | ours 392@8 | 390@8 | 390@8 | 2 | 1 | 1294 | 1638 | 681.9 | {"seed": 6, "restart:best": 1} |
| sw2 | ls16-8x8-gf256-00 | ours 404@8 | 403@8 | 403@8 | 1 | 0 | 2471 | 2471 | 681.8 | {"seed": 2} |
| sw2 | klsw17-m-8x8-gf16-0x13-inv-00 | ours 163@12 | 163@11 | 163@11 | 0 | 2 | - | - | 842.9 | {"seed": 1, "restart:best": 2, "best": 3} |
