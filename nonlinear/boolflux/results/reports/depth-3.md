| target | model | objective | caps | start | start | result | gates by type | verified | wall s | CPU s | seeds x iters x rounds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| aes | nist | cost,gd | GD<=10 | aes-sbox-a51-ad4-g157-gd11-xx106-28 | 157 (A51 GD11 AD4) | **153 (A52 GD11 AD4)** | AND 52 XNOR 44 XOR 57 | NO (function, library, metrics or caps), no gain | 461.6 | 3593.1 | 1-8 x 300000 x 3 |
| aes | nist | cost,gd | GD<=11 | aes-sbox-a51-ad4-g157-gd11-xx106-28 | 157 (A51 GD11 AD4) | **152 (A51 GD11 AD4)** | AND 51 NOT 1 XNOR 45 XOR 55 | both | 480.1 | 3752.7 | 1-8 x 300000 x 3 |
| aes | nist | cost,gd | GD<=12 | aes-sbox-a45-ad4-g151-gd12-xx106-26 | 151 (A45 GD12 AD4) | **146 (A45 GD12 AD4)** | AND 45 XNOR 46 XOR 55 | both | 471.4 | 3673.9 | 1-8 x 300000 x 3 |
| aes | nist | cost,gd | GD<=13 | aes-sbox-a38-ad4-g148-gd13-xx110-24 | 148 (A38 GD13 AD4) | **138 (A38 GD13 AD4)** | AND 38 XNOR 48 XOR 52 | both | 507.8 | 3894.3 | 1-8 x 300000 x 3 |
| aes | nist | cost,gd | GD<=14 | aes-sbox-a33-ad4-g116-gd15-xx83-7 | 116 (A33 GD15 AD4) | **126 (A41 GD14 AD4)** | AND 41 XNOR 40 XOR 45 | both | 460.0 | 3558.0 | 1-8 x 300000 x 3 |
| aes | nist | cost,gd | GD<=15 | aes-sbox-a33-ad4-g116-gd15-xx83-7 | 116 (A33 GD15 AD4) | **116 (A33 GD15 AD4)** | AND 33 XNOR 7 XOR 76 | both, no gain | 370.8 | 2904.4 | 1-8 x 300000 x 3 |
