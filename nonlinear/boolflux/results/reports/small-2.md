| target | model | objective | caps | start | start | result | gates by type | verified | wall s | CPU s | seeds x iters x rounds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ascon | bgc | cost | - | ANF (naive) | 35 (A8 GD4 AD1) | **16 (A5 GD7 AD2)** | AND 2 NOT 1 OR 3 XOR 10 | both | 21.3 | 135.5 | 1-8 x 100000 x 3 |
| ascon | gc6 | cost | - | ANF (naive) | 34 (A8 GD4 AD1) | **15 (A5 GD4 AD1)** | AND 1 NAND 1 OR 3 XNOR 2 XOR 8 | both | 27.5 | 186.5 | 1-8 x 100000 x 3 |
| chi3 | bgc | cost | - | ANF (naive) | 9 (A3 GD3 AD1) | **7 (A3 GD3 AD1)** | AND 2 OR 1 XOR 4 | both | 15.7 | 89.4 | 1-8 x 100000 x 3 |
| chi3 | gc6 | cost | - | ANF (naive) | 9 (A3 GD3 AD1) | **7 (A3 GD3 AD1)** | AND 2 OR 1 XOR 4 | both | 18.4 | 108.3 | 1-8 x 100000 x 3 |
| gift | bgc | cost | - | ANF (naive) | 22 (A7 GD5 AD2) | **11 (A4 GD6 AD3)** | AND 3 NOT 1 OR 1 XOR 6 | both | 15.9 | 93.5 | 1-8 x 100000 x 3 |
| gift | gc6 | cost | - | ANF (naive) | 21 (A7 GD4 AD2) | **10 (A4 GD10 AD4)** | AND 3 OR 1 XNOR 2 XOR 4 | both | 16.8 | 103.7 | 1-8 x 100000 x 3 |
| keccak_chi5 | bgc | cost | - | ANF (naive) | 15 (A5 GD3 AD1) | **13 (A5 GD6 AD2)** | AND 3 OR 2 XOR 8 | both | 20.3 | 127.0 | 1-8 x 100000 x 3 |
| keccak_chi5 | gc6 | cost | - | ANF (naive) | 15 (A5 GD3 AD1) | **13 (A5 GD3 AD1)** | AND 1 NAND 2 NOR 1 OR 1 XNOR 5 XOR 3 | both | 26.0 | 172.0 | 1-8 x 100000 x 3 |
| klein | bgc | cost | - | ANF (naive) | 38 (A10 GD6 AD2) | **17 (A7 GD14 AD6)** | AND 4 NOT 1 OR 3 XOR 9 | both | 22.3 | 136.1 | 1-8 x 100000 x 3 |
| klein | gc6 | cost | - | ANF (naive) | 35 (A10 GD5 AD2) | **15 (A7 GD14 AD7)** | AND 4 NAND 1 OR 2 XNOR 4 XOR 4 | both | 27.8 | 172.6 | 1-8 x 100000 x 3 |
| midori_sb0 | bgc | cost | - | ANF (naive) | 29 (A9 GD6 AD2) | **13 (A4 GD11 AD4)** | AND 2 NOT 1 OR 2 XOR 8 | both | 17.8 | 106.1 | 1-8 x 100000 x 3 |
| midori_sb0 | gc6 | cost | - | ANF (naive) | 27 (A9 GD5 AD2) | **12 (A4 GD9 AD4)** | AND 2 NAND 2 XNOR 2 XOR 6 | both | 20.3 | 131.2 | 1-8 x 100000 x 3 |
| midori_sb1 | bgc | cost | - | ANF (naive) | 35 (A9 GD6 AD2) | **16 (A8 GD8 AD5)** | AND 4 NOT 1 OR 4 XOR 7 | both | 23.9 | 147.4 | 1-8 x 100000 x 3 |
| midori_sb1 | gc6 | cost | - | ANF (naive) | 34 (A9 GD5 AD2) | **15 (A11 GD6 AD5)** | AND 2 NAND 1 NOR 6 OR 2 XNOR 1 XOR 3 | both | 31.6 | 201.6 | 1-8 x 100000 x 3 |
| noekeon | bgc | cost | - | ANF (naive) | 28 (A8 GD6 AD2) | **12 (A5 GD7 AD3)** | AND 3 NOT 1 OR 2 XOR 6 | both | 16.2 | 95.8 | 1-8 x 100000 x 3 |
| noekeon | gc6 | cost | - | ANF (naive) | 25 (A8 GD5 AD2) | **10 (A4 GD7 AD3)** | AND 3 NAND 1 XNOR 1 XOR 5 | both | 16.5 | 102.6 | 1-8 x 100000 x 3 |
| piccolo | bgc | cost | - | ANF (naive) | 31 (A8 GD6 AD2) | **10 (A4 GD5 AD2)** | AND 1 NOT 2 OR 3 XOR 4 | both | 15.8 | 93.3 | 1-8 x 100000 x 3 |
| piccolo | gc6 | cost | - | ANF (naive) | 28 (A8 GD6 AD2) | **8 (A4 GD4 AD2)** | NOR 3 OR 1 XOR 4 | both | 16.7 | 99.3 | 1-8 x 100000 x 3 |
| present | bgc | cost | - | ANF (naive) | 32 (A9 GD6 AD2) | **14 (A4 GD12 AD4)** | AND 3 NOT 1 OR 1 XOR 9 | both | 18.3 | 110.3 | 1-8 x 100000 x 3 |
| present | gc6 | cost | - | ANF (naive) | 30 (A9 GD5 AD2) | **13 (A4 GD10 AD4)** | NAND 2 NOR 2 XNOR 4 XOR 5 | both | 20.8 | 135.0 | 1-8 x 100000 x 3 |
| pride | bgc | cost | - | ANF (naive) | 17 (A7 GD5 AD2) | **8 (A4 GD6 AD3)** | AND 4 XOR 4 | both | 13.1 | 74.1 | 1-8 x 100000 x 3 |
| pride | gc6 | cost | - | ANF (naive) | 17 (A7 GD5 AD2) | **8 (A4 GD6 AD3)** | AND 3 NAND 1 XNOR 1 XOR 3 | both | 15.1 | 89.4 | 1-8 x 100000 x 3 |
| prince | bgc | cost | - | ANF (naive) | 35 (A10 GD6 AD2) | **16 (A7 GD10 AD5)** | AND 2 NOT 1 OR 5 XOR 8 | both | 23.9 | 145.3 | 1-8 x 100000 x 3 |
| prince | gc6 | cost | - | ANF (naive) | 32 (A10 GD5 AD2) | **15 (A9 GD9 AD6)** | AND 1 NAND 2 NOR 3 OR 3 XNOR 4 XOR 2 | both | 28.3 | 179.2 | 1-8 x 100000 x 3 |
| printcipher | bgc | cost | - | ANF (naive) | 9 (A3 GD3 AD1) | **6 (A3 GD6 AD3)** | AND 2 OR 1 XOR 3 | both | 15.2 | 83.5 | 1-8 x 100000 x 3 |
| printcipher | gc6 | cost | - | ANF (naive) | 9 (A3 GD3 AD1) | **6 (A3 GD6 AD3)** | AND 1 NAND 1 OR 1 XNOR 1 XOR 2 | both | 16.8 | 96.3 | 1-8 x 100000 x 3 |
| rectangle | bgc | cost | - | ANF (naive) | 27 (A8 GD6 AD2) | **12 (A4 GD7 AD3)** | AND 2 NOT 1 OR 2 XOR 7 | both | 17.0 | 102.1 | 1-8 x 100000 x 3 |
| rectangle | gc6 | cost | - | ANF (naive) | 25 (A8 GD5 AD2) | **11 (A4 GD8 AD4)** | AND 2 NOR 1 OR 1 XNOR 5 XOR 2 | both | 20.5 | 128.2 | 1-8 x 100000 x 3 |
| serpent_s0 | bgc | cost | - | ANF (naive) | 34 (A8 GD7 AD2) | **14 (A4 GD10 AD3)** | AND 4 NOT 1 XOR 9 | both | 17.2 | 108.4 | 1-8 x 100000 x 3 |
| serpent_s0 | gc6 | cost | - | ANF (naive) | 32 (A8 GD6 AD2) | **13 (A5 GD8 AD4)** | AND 1 NAND 2 NOR 1 OR 1 XNOR 3 XOR 5 | both | 21.4 | 137.8 | 1-8 x 100000 x 3 |
| serpent_s1 | bgc | cost | - | ANF (naive) | 36 (A9 GD7 AD2) | **14 (A4 GD10 AD3)** | NOT 1 OR 4 XOR 9 | both | 17.7 | 109.8 | 1-8 x 100000 x 3 |
| serpent_s1 | gc6 | cost | - | ANF (naive) | 32 (A9 GD6 AD2) | **13 (A4 GD12 AD4)** | AND 1 NAND 2 NOR 1 XNOR 3 XOR 6 | both | 20.6 | 135.6 | 1-8 x 100000 x 3 |
| serpent_s2 | bgc | cost | - | ANF (naive) | 32 (A9 GD6 AD2) | **13 (A4 GD10 AD4)** | AND 2 NOT 1 OR 2 XOR 8 | both | 17.1 | 102.8 | 1-8 x 100000 x 3 |
| serpent_s2 | gc6 | cost | - | ANF (naive) | 31 (A9 GD6 AD2) | **12 (A4 GD9 AD4)** | NAND 1 NOR 2 OR 1 XNOR 5 XOR 3 | both | 18.9 | 120.5 | 1-8 x 100000 x 3 |
| serpent_s3 | bgc | cost | - | ANF (naive) | 37 (A10 GD6 AD2) | **15 (A7 GD9 AD4)** | AND 4 OR 3 XOR 8 | both | 21.8 | 129.7 | 1-8 x 100000 x 3 |
| serpent_s3 | gc6 | cost | - | ANF (naive) | 37 (A10 GD6 AD2) | **15 (A6 GD13 AD5)** | AND 3 NOR 2 OR 1 XNOR 5 XOR 4 | both | 26.9 | 162.9 | 1-8 x 100000 x 3 |
| serpent_s4 | bgc | cost | - | ANF (naive) | 37 (A10 GD6 AD2) | **15 (A5 GD9 AD3)** | AND 3 NOT 1 OR 2 XOR 9 | both | 20.4 | 123.0 | 1-8 x 100000 x 3 |
| serpent_s4 | gc6 | cost | - | ANF (naive) | 36 (A10 GD6 AD2) | **13 (A6 GD11 AD5)** | AND 2 NAND 1 NOR 3 XNOR 2 XOR 5 | both | 25.0 | 156.5 | 1-8 x 100000 x 3 |
| serpent_s5 | bgc | cost | - | ANF (naive) | 37 (A10 GD6 AD2) | **15 (A5 GD9 AD3)** | AND 3 NOT 1 OR 2 XOR 9 | both | 21.6 | 127.3 | 1-8 x 100000 x 3 |
| serpent_s5 | gc6 | cost | - | ANF (naive) | 33 (A10 GD5 AD2) | **14 (A5 GD12 AD5)** | AND 1 NAND 2 NOR 2 XNOR 3 XOR 6 | both | 25.6 | 159.4 | 1-8 x 100000 x 3 |
| serpent_s6 | bgc | cost | - | ANF (naive) | 37 (A9 GD7 AD2) | **14 (A4 GD11 AD4)** | NOT 1 OR 4 XOR 9 | both | 16.9 | 104.8 | 1-8 x 100000 x 3 |
| serpent_s6 | gc6 | cost | - | ANF (naive) | 34 (A9 GD6 AD2) | **13 (A4 GD12 AD4)** | AND 2 NAND 1 NOR 1 XNOR 4 XOR 5 | both | 21.3 | 139.0 | 1-8 x 100000 x 3 |
| serpent_s7 | bgc | cost | - | ANF (naive) | 38 (A10 GD6 AD2) | **16 (A6 GD10 AD4)** | AND 1 NOT 1 OR 5 XOR 9 | both | 21.3 | 129.6 | 1-8 x 100000 x 3 |
| serpent_s7 | gc6 | cost | - | ANF (naive) | 37 (A10 GD6 AD2) | **14 (A5 GD12 AD4)** | AND 3 NOR 1 OR 1 XNOR 6 XOR 3 | both | 26.8 | 169.9 | 1-8 x 100000 x 3 |
| skinny64 | bgc | cost | - | ANF (naive) | 30 (A8 GD6 AD2) | **11 (A4 GD5 AD2)** | AND 1 NOT 2 OR 3 XOR 5 | both | 16.5 | 97.9 | 1-8 x 100000 x 3 |
| skinny64 | gc6 | cost | - | ANF (naive) | 28 (A8 GD6 AD2) | **8 (A4 GD4 AD2)** | NOR 1 OR 3 XNOR 3 XOR 1 | both | 15.5 | 93.6 | 1-8 x 100000 x 3 |
