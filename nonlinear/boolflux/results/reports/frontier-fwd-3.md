| target | model | objective | caps | start | start | result | gates by type | verified | wall s | CPU s | seeds x iters x rounds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| aes | nist | cost,gd | GD<=31,AD<=4,A<=28 | aes-sbox-a28-ad4-g131-gd31-xx103-43 | 131 (A28 GD31 AD4) | **131 (A28 GD29 AD4)** | AND 28 XNOR 62 XOR 41 | both | 55.2 | 430.6 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=22,AD<=4,A<=28 | aes-sbox-a28-ad4-g132-gd22-xx104-40 | 132 (A28 GD22 AD4) | **132 (A28 GD22 AD4)** | AND 28 XNOR 40 XOR 64 | both, no gain | 51.7 | 401.3 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=20,AD<=4,A<=28 | aes-sbox-a28-ad4-g134-gd20-xx106-41 | 134 (A28 GD20 AD4) | **133 (A28 GD20 AD4)** | AND 28 XNOR 55 XOR 50 | both | 45.7 | 359.9 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=15,AD<=4,A<=28 | aes-sbox-a28-ad4-g153-gd15-xx125-29 | 153 (A28 GD15 AD4) | **153 (A28 GD15 AD4)** | AND 28 XNOR 29 XOR 96 | both, no gain | 44.4 | 350.2 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=14,AD<=4,A<=28 | aes-sbox-a28-ad4-g176-gd14-xx148-25 | 176 (A28 GD14 AD4) | **176 (A28 GD14 AD4)** | AND 28 XNOR 25 XOR 123 | both, no gain | 44.6 | 352.0 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=19,AD<=4,A<=32 | aes-sbox-a32-ad4-g117-gd19-xx85-6 | 117 (A32 GD19 AD4) | **117 (A32 GD19 AD4)** | AND 32 XNOR 6 XOR 79 | both, no gain | 41.3 | 323.5 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=15,AD<=4,A<=32 | aes-sbox-a32-ad4-g127-gd15-xx95-7 | 127 (A32 GD15 AD4) | **126 (A32 GD15 AD4)** | AND 32 XNOR 32 XOR 62 | both | 42.2 | 329.8 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=18,AD<=4,A<=32 | aes-sbox-a32-ad4-g137-gd18-xx105-7 | 137 (A32 GD18 AD4) | **122 (A32 GD18 AD4)** | AND 32 XNOR 39 XOR 51 | both | 44.8 | 349.2 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=22,AD<=5,A<=32 | aes-sbox-a32-ad5-g107-gd22-xx75-4 | 107 (A32 GD22 AD5) | **107 (A32 GD22 AD5)** | AND 32 XNOR 4 XOR 71 | both, no gain | 45.6 | 357.2 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=16,AD<=5,A<=32 | aes-sbox-a32-ad5-g122-gd16-xx90-15 | 122 (A32 GD16 AD5) | **122 (A32 GD16 AD5)** | AND 32 XNOR 15 XOR 75 | both, no gain | 43.3 | 341.3 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=15,AD<=5,A<=32 | aes-sbox-a32-ad5-g127-gd15-xx95-20 | 127 (A32 GD15 AD5) | **127 (A32 GD15 AD5)** | AND 32 XNOR 20 XOR 75 | both, no gain | 43.8 | 346.6 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=15,AD<=5,A<=32 | aes-sbox-a32-ad5-g128-gd15-xx96-21 | 128 (A32 GD15 AD5) | **127 (A32 GD15 AD5)** | AND 32 XNOR 42 XOR 53 | both | 46.9 | 363.1 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=22,AD<=4,A<=33 | aes-sbox-a33-ad4-g106-gd22-xx73-5 | 106 (A33 GD22 AD4) | **106 (A33 GD22 AD4)** | AND 33 XNOR 5 XOR 68 | both, no gain | 44.7 | 343.5 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=14,AD<=4,A<=33 | aes-sbox-a33-ad4-g127-gd14-xx94-23 | 127 (A33 GD14 AD4) | **127 (A33 GD14 AD4)** | AND 33 XNOR 23 XOR 71 | both, no gain | 45.0 | 351.6 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=14,AD<=4,A<=33 | aes-sbox-a33-ad4-g128-gd14-xx95-20 | 128 (A33 GD14 AD4) | **128 (A33 GD14 AD4)** | AND 33 XNOR 20 XOR 75 | both, no gain | 46.4 | 363.5 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=13,AD<=4,A<=34 | aes-sbox-a34-ad4-g140-gd13-xx106-27 | 140 (A34 GD13 AD4) | **139 (A34 GD13 AD4)** | AND 34 XNOR 42 XOR 63 | both | 49.0 | 374.7 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=13,AD<=4,A<=34 | aes-sbox-a34-ad4-g142-gd13-xx108-28 | 142 (A34 GD13 AD4) | **141 (A34 GD13 AD4)** | AND 34 XNOR 48 XOR 59 | both | 45.3 | 349.1 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=25,AD<=3,A<=35 | aes-sbox-a35-ad3-g141-gd25-xx106-37 | 141 (A35 GD25 AD3) | **141 (A35 GD25 AD3)** | AND 35 XNOR 37 XOR 69 | both, no gain | 55.6 | 434.7 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=20,AD<=3,A<=35 | aes-sbox-a35-ad3-g147-gd20-xx112-36 | 147 (A35 GD20 AD3) | **144 (A35 GD20 AD3)** | AND 35 XNOR 52 XOR 57 | both | 49.2 | 388.9 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=20,AD<=3,A<=35 | aes-sbox-a35-ad3-g148-gd20-xx113-35 | 148 (A35 GD20 AD3) | **144 (A35 GD20 AD3)** | AND 35 XNOR 56 XOR 53 | both | 48.7 | 383.5 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=14,AD<=3,A<=35 | aes-sbox-a35-ad3-g172-gd14-xx137-30 | 172 (A35 GD14 AD3) | **167 (A35 GD14 AD3)** | AND 35 XNOR 58 XOR 74 | both | 47.1 | 369.9 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=13,AD<=4,A<=35 | aes-sbox-a35-ad4-g133-gd13-xx98-21 | 133 (A35 GD13 AD4) | **133 (A35 GD13 AD4)** | AND 35 XNOR 21 XOR 77 | both, no gain | 42.4 | 333.8 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=13,AD<=4,A<=35 | aes-sbox-a35-ad4-g135-gd13-xx100-21 | 135 (A35 GD13 AD4) | **135 (A35 GD13 AD4)** | AND 35 XNOR 21 XOR 79 | both, no gain | 42.6 | 339.1 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=13,AD<=4,A<=36 | aes-sbox-a36-ad4-g134-gd13-xx98-20 | 134 (A36 GD13 AD4) | **133 (A36 GD13 AD4)** | AND 36 NOT 1 XNOR 43 XOR 53 | both | 43.3 | 340.9 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=13,AD<=4,A<=36 | aes-sbox-a36-ad4-g141-gd13-xx105-21 | 141 (A36 GD13 AD4) | **134 (A36 GD13 AD4)** | AND 36 XNOR 43 XOR 55 | both | 45.4 | 354.0 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=13,AD<=4,A<=36 | aes-sbox-a36-ad4-g142-gd13-xx106-19 | 142 (A36 GD13 AD4) | **131 (A36 GD13 AD4)** | AND 36 XNOR 42 XOR 53 | both | 46.2 | 360.2 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=12,AD<=4,A<=45 | aes-sbox-a45-ad4-g141-gd12-xx96-25 | 141 (A45 GD12 AD4) | **141 (A45 GD12 AD4)** | AND 45 XNOR 25 XOR 71 | both, no gain | 42.7 | 339.3 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=12,AD<=4,A<=45 | aes-sbox-a45-ad4-g147-gd12-xx102-29 | 147 (A45 GD12 AD4) | **146 (A45 GD12 AD4)** | AND 45 XNOR 42 XOR 59 | both | 46.5 | 365.0 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=11,AD<=4,A<=49 | aes-sbox-a49-ad4-g148-gd11-xx99-23 | 148 (A49 GD11 AD4) | **148 (A49 GD11 AD4)** | AND 49 XNOR 23 XOR 76 | both, no gain | 47.8 | 375.7 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=11,AD<=4,A<=49 | aes-sbox-a49-ad4-g149-gd11-xx100-23 | 149 (A49 GD11 AD4) | **148 (A49 GD11 AD4)** | AND 49 XNOR 31 XOR 68 | both | 45.6 | 360.1 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=10,AD<=4,A<=59 | aes-sbox-a59-ad4-g159-gd10-xxn100-30-3 | 159 (A59 GD10 AD4) | **159 (A59 GD10 AD4)** | AND 59 NOT 3 XNOR 30 XOR 67 | both, no gain | 50.3 | 384.8 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=10,AD<=4,A<=60 | aes-sbox-a60-ad4-g163-gd10-xxn103-29-4 | 163 (A60 GD10 AD4) | **163 (A60 GD10 AD4)** | AND 60 NOT 4 XNOR 29 XOR 70 | both, no gain | 47.6 | 366.1 | 1-8 x 100000 x 1 |
