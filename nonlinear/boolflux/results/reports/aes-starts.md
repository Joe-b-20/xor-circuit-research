| target | model | objective | caps | start | start | result | gates by type | verified | wall s | CPU s | seeds x iters x rounds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| aes | nist | cost,gd | - | ANF (naive) | 1247 (A246 GD14 AD6) | **717 (A264 GD50 AD19)** | AND 264 NOT 1 XNOR 194 XOR 258 | both | 510.0 | 4004.8 | 1-8 x 300000 x 2 |
| aes | nist | cost,gd | - | aes-sbox-fwd-g113-a32-d27-ad6.slp | 113 (A32 GD27 AD6) | **108 (A33 GD26 AD5)** | AND 33 XNOR 21 XOR 54 | both | 246.2 | 1938.6 | 1-8 x 300000 x 2 |
| aes | nist | cost,gd | GD<=27,AD<=6 | aes-sbox-fwd-g113-a32-d27-ad6.slp | 113 (A32 GD27 AD6) | **108 (A33 GD23 AD5)** | AND 33 XNOR 30 XOR 45 | both | 223.4 | 1721.0 | 1-8 x 300000 x 2 |
