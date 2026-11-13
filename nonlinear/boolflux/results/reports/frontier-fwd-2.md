| target | model | objective | caps | start | start | result | gates by type | verified | wall s | CPU s | seeds x iters x rounds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| aes | nist | cost,gd | GD<=32,AD<=4,A<=28 | aes-sbox-a28-ad4-g131-gd32-xx103-47 | 131 (A28 GD32 AD4) | **131 (A28 GD26 AD4)** | AND 28 XNOR 50 XOR 53 | both | 68.1 | 512.2 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=36,AD<=4,A<=28 | aes-sbox-a28-ad4-g131-gd36-xx103-28 | 131 (A28 GD36 AD4) | **131 (A28 GD26 AD4)** | AND 28 XNOR 46 XOR 57 | both | 65.0 | 503.8 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=23,AD<=4,A<=28 | aes-sbox-a28-ad4-g132-gd23-xx104-27 | 132 (A28 GD23 AD4) | **132 (A28 GD22 AD4)** | AND 28 XNOR 50 XOR 54 | both | 54.0 | 418.2 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=16,AD<=4,A<=28 | aes-sbox-a28-ad4-g141-gd16-xx113-27 | 141 (A28 GD16 AD4) | **141 (A28 GD16 AD4)** | AND 28 XNOR 27 XOR 86 | both, no gain | 44.0 | 346.0 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=15,AD<=4,A<=28 | aes-sbox-a28-ad4-g154-gd15-xx126-28 | 154 (A28 GD15 AD4) | **153 (A28 GD15 AD4)** | AND 28 XNOR 64 XOR 61 | both | 42.0 | 331.8 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=14,AD<=4,A<=28 | aes-sbox-a28-ad4-g177-gd14-xx149-24 | 177 (A28 GD14 AD4) | **176 (A28 GD14 AD4)** | AND 28 XNOR 81 XOR 67 | both | 43.4 | 344.3 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=27,AD<=5,A<=28 | aes-sbox-a28-ad5-g124-gd27-xx96-26 | 124 (A28 GD27 AD5) | **124 (A28 GD27 AD5)** | AND 28 XNOR 26 XOR 70 | both, no gain | 54.8 | 424.8 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=20,AD<=5,A<=28 | aes-sbox-a28-ad5-g128-gd20-xx100-27 | 128 (A28 GD20 AD5) | **128 (A28 GD20 AD5)** | AND 28 XNOR 27 XOR 73 | both, no gain | 33.5 | 262.7 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=15,AD<=5,A<=28 | aes-sbox-a28-ad5-g150-gd15-xx122-23 | 150 (A28 GD15 AD5) | **150 (A28 GD15 AD5)** | AND 28 XNOR 23 XOR 99 | both, no gain | 28.6 | 226.4 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=32,AD<=5,A<=29 | aes-sbox-a29-ad5-g137-gd32-xx108-22 | 137 (A29 GD32 AD5) | **135 (A29 GD28 AD5)** | AND 29 XNOR 50 XOR 56 | both | 37.1 | 288.8 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=35,AD<=5,A<=29 | aes-sbox-a29-ad5-g139-gd35-xx110-20 | 139 (A29 GD35 AD5) | **136 (A29 GD30 AD5)** | AND 29 XNOR 56 XOR 51 | both | 37.7 | 296.8 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=16,AD<=5,A<=29 | aes-sbox-a29-ad5-g182-gd16-xx153-29 | 182 (A29 GD16 AD5) | **174 (A29 GD16 AD5)** | AND 29 XNOR 57 XOR 88 | both | 29.2 | 230.3 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=16,AD<=5,A<=29 | aes-sbox-a29-ad5-g184-gd16-xx155-26 | 184 (A29 GD16 AD5) | **174 (A29 GD16 AD5)** | AND 29 XNOR 61 XOR 84 | both | 29.6 | 235.2 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=36,AD<=4,A<=30 | aes-sbox-a30-ad4-g147-gd36-xx117-13 | 147 (A30 GD36 AD4) | **140 (A30 GD32 AD4)** | AND 30 NOT 1 XNOR 66 XOR 43 | both | 39.1 | 306.2 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=15,AD<=4,A<=30 | aes-sbox-a30-ad4-g205-gd15-xx175-54 | 205 (A30 GD15 AD4) | **181 (A30 GD15 AD4)** | AND 30 NOT 1 XNOR 70 XOR 80 | both | 28.7 | 226.4 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=30,AD<=5,A<=32 | aes-sbox-a32-ad5-g104-gd30-xx72-5 | 104 (A32 GD30 AD5) | **104 (A32 GD30 AD5)** | AND 32 XNOR 5 XOR 67 | both, no gain | 32.0 | 250.6 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=26,AD<=5,A<=32 | aes-sbox-a32-ad5-g105-gd26-xx73-5 | 105 (A32 GD26 AD5) | **105 (A32 GD26 AD5)** | AND 32 XNOR 5 XOR 68 | both, no gain | 39.5 | 313.4 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=20,AD<=5,A<=32 | aes-sbox-a32-ad5-g109-gd20-xx77-4 | 109 (A32 GD20 AD5) | **108 (A32 GD20 AD5)** | AND 32 XNOR 35 XOR 41 | both | 36.4 | 287.9 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=22,AD<=5,A<=32 | aes-sbox-a32-ad5-g110-gd22-xx78-3 | 110 (A32 GD22 AD5) | **110 (A32 GD22 AD5)** | AND 32 XNOR 3 XOR 75 | both, no gain | 39.1 | 305.0 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=23,AD<=5,A<=32 | aes-sbox-a32-ad5-g110-gd23-xx78-3 | 110 (A32 GD23 AD5) | **110 (A32 GD22 AD5)** | AND 32 XNOR 25 XOR 53 | both | 41.1 | 323.1 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=15,AD<=5,A<=32 | aes-sbox-a32-ad5-g131-gd15-xx99-17 | 131 (A32 GD15 AD5) | **129 (A32 GD15 AD5)** | AND 32 XNOR 29 XOR 68 | both | 38.7 | 306.8 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=15,AD<=5,A<=32 | aes-sbox-a32-ad5-g133-gd15-xx101-19 | 133 (A32 GD15 AD5) | **129 (A32 GD15 AD5)** | AND 32 XNOR 40 XOR 57 | both | 40.2 | 318.9 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=32,AD<=7,A<=32 | aes-sbox-a32-ad7-g103-gd32-xx71-10 | 103 (A32 GD32 AD7) | **103 (A32 GD32 AD7)** | AND 32 XNOR 10 XOR 61 | both, no gain | 44.9 | 355.2 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=25,AD<=4,A<=33 | aes-sbox-a33-ad4-g105-gd25-xx72-6 | 105 (A33 GD25 AD4) | **105 (A33 GD25 AD4)** | AND 33 XNOR 6 XOR 66 | both, no gain | 39.7 | 313.1 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=20,AD<=4,A<=33 | aes-sbox-a33-ad4-g108-gd20-xx75-5 | 108 (A33 GD20 AD4) | **108 (A33 GD19 AD4)** | AND 33 XNOR 22 XOR 53 | both | 36.9 | 291.2 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=20,AD<=4,A<=33 | aes-sbox-a33-ad4-g110-gd20-xx77-4 | 110 (A33 GD20 AD4) | **110 (A33 GD18 AD4)** | AND 33 XNOR 26 XOR 51 | both | 37.4 | 297.0 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=15,AD<=4,A<=33 | aes-sbox-a33-ad4-g116-gd15-xx83-7 | 116 (A33 GD15 AD4) | **116 (A33 GD15 AD4)** | AND 33 XNOR 7 XOR 76 | both, no gain | 32.0 | 254.0 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=22,AD<=4,A<=34 | aes-sbox-a34-ad4-g110-gd22-xx76-3 | 110 (A34 GD22 AD4) | **110 (A34 GD20 AD4)** | AND 34 XNOR 22 XOR 54 | both | 38.1 | 300.5 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=15,AD<=4,A<=34 | aes-sbox-a34-ad4-g124-gd15-xx90-4 | 124 (A34 GD15 AD4) | **122 (A34 GD15 AD4)** | AND 34 XNOR 39 XOR 49 | both | 34.3 | 270.2 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=15,AD<=4,A<=34 | aes-sbox-a34-ad4-g125-gd15-xx91-4 | 125 (A34 GD15 AD4) | **122 (A34 GD15 AD4)** | AND 34 XNOR 30 XOR 58 | both | 33.4 | 264.0 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=15,AD<=4,A<=34 | aes-sbox-a34-ad4-g128-gd15-xx94-4 | 128 (A34 GD15 AD4) | **122 (A34 GD15 AD4)** | AND 34 XNOR 39 XOR 49 | both | 32.7 | 259.7 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=27,AD<=3,A<=35 | aes-sbox-a35-ad3-g139-gd27-xx104-38 | 139 (A35 GD27 AD3) | **139 (A35 GD27 AD3)** | AND 35 XNOR 38 XOR 66 | both, no gain | 45.8 | 361.0 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=31,AD<=3,A<=35 | aes-sbox-a35-ad3-g139-gd31-xx104-25 | 139 (A35 GD31 AD3) | **139 (A35 GD27 AD3)** | AND 35 XNOR 31 XOR 73 | both | 50.9 | 400.5 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=15,AD<=3,A<=35 | aes-sbox-a35-ad3-g157-gd15-xx122-31 | 157 (A35 GD15 AD3) | **157 (A35 GD15 AD3)** | AND 35 XNOR 31 XOR 91 | both, no gain | 39.9 | 316.7 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=13,AD<=3,A<=35 | aes-sbox-a35-ad3-g183-gd13-xx148-29 | 183 (A35 GD13 AD3) | **183 (A35 GD13 AD3)** | AND 35 XNOR 29 XOR 119 | both, no gain | 38.6 | 304.8 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=14,AD<=4,A<=36 | aes-sbox-a36-ad4-g137-gd14-xx101-22 | 137 (A36 GD14 AD4) | **134 (A36 GD14 AD4)** | AND 36 XNOR 36 XOR 62 | both | 38.2 | 302.3 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=14,AD<=4,A<=36 | aes-sbox-a36-ad4-g138-gd14-xx102-22 | 138 (A36 GD14 AD4) | **135 (A36 GD14 AD4)** | AND 36 XNOR 49 XOR 50 | both | 38.1 | 301.5 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=13,AD<=4,A<=38 | aes-sbox-a38-ad4-g148-gd13-xx110-24 | 148 (A38 GD13 AD4) | **139 (A38 GD13 AD4)** | AND 38 XNOR 36 XOR 65 | both | 38.3 | 304.9 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=13,AD<=4,A<=39 | aes-sbox-a39-ad4-g148-gd13-xx109-24 | 148 (A39 GD13 AD4) | **137 (A39 GD13 AD4)** | AND 39 XNOR 41 XOR 57 | both | 38.0 | 301.3 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=12,AD<=4,A<=45 | aes-sbox-a45-ad4-g151-gd12-xx106-26 | 151 (A45 GD12 AD4) | **146 (A45 GD12 AD4)** | AND 45 XNOR 37 XOR 64 | both | 40.9 | 324.4 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=15,AD<=3,A<=46 | aes-sbox-a46-ad3-g250-gd15-xx204-4 | 250 (A46 GD15 AD3) | **207 (A46 GD15 AD3)** | AND 46 XNOR 87 XOR 74 | both | 35.9 | 284.7 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=22,AD<=3,A<=47 | aes-sbox-a47-ad3-g186-gd22-xx139-7 | 186 (A47 GD22 AD3) | **167 (A47 GD22 AD3)** | AND 47 XNOR 50 XOR 70 | both | 33.3 | 263.4 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=15,AD<=3,A<=47 | aes-sbox-a47-ad3-g225-gd15-xx178-4 | 225 (A47 GD15 AD3) | **190 (A47 GD15 AD3)** | AND 47 XNOR 59 XOR 84 | both | 33.9 | 269.1 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=11,AD<=4,A<=49 | aes-sbox-a49-ad4-g164-gd11-xx115-32 | 164 (A49 GD11 AD4) | **150 (A49 GD11 AD4)** | AND 49 XNOR 51 XOR 50 | both | 45.7 | 359.9 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=11,AD<=4,A<=51 | aes-sbox-a51-ad4-g157-gd11-xx106-28 | 157 (A51 GD11 AD4) | **152 (A51 GD11 AD4)** | AND 51 NOT 1 XNOR 37 XOR 63 | both | 46.4 | 366.6 | 1-8 x 100000 x 1 |
| aes | nist | cost,gd | GD<=11,AD<=4,A<=53 | aes-sbox-a53-ad4-g157-gd11-xx104-31 | 157 (A53 GD11 AD4) | **152 (A53 GD11 AD4)** | AND 53 XNOR 38 XOR 61 | both | 46.4 | 366.7 | 1-8 x 100000 x 1 |
