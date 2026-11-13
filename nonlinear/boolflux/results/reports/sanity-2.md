| target | model | objective | caps | start | start | result | gates by type | verified | wall s | CPU s | seeds x iters x rounds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| fulladd | xag | a,cost | - | ANF (naive) | 7 (A3 GD3 AD1) | **5 (A1 GD3 AD1)** | AND 1 XOR 4 | both | 0.3 | 0.9 | 1-4 x 20000 x 1 |
| gf16-inv | xag | a,cost | - | ANF (naive) | 33 (A10 GD5 AD2) | **17 (A5 GD12 AD4)** | AND 5 XOR 12 | both | 15.0 | 38.5 | 1-4 x 50000 x 3 |
| gf16-inv | xag | cost | - | ANF (naive) | 33 (A10 GD5 AD2) | **15 (A6 GD12 AD5)** | AND 6 XOR 9 | both | 14.0 | 34.5 | 1-4 x 50000 x 3 |
| gf16-mul | xag | a,cost | - | ANF (naive) | 34 (A16 GD4 AD1) | **32 (A9 GD9 AD1)** | AND 9 XOR 23 | both | 81.5 | 230.1 | 1-8 x 30000 x 3 |
| gf16-mul | xag | a,cost | - | ANF (naive) | 34 (A16 GD4 AD1) | **30 (A14 GD6 AD1)** | AND 14 XOR 16 | both | 16.9 | 66.6 | 1-8 x 30000 x 3 |
| maj3 | xag | a,cost | - | ANF (naive) | 5 (A3 GD3 AD1) | **4 (A1 GD3 AD1)** | AND 1 XOR 3 | both | 0.2 | 0.8 | 1-4 x 20000 x 1 |
