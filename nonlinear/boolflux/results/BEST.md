# Best BoolFlux AES S-box circuits so far (not dominated by the pinned NIST set 3d80774)


Every row: verified by two independent implementations on all 256 inputs, NIST gate library
{AND, XOR, XNOR, NOT}, every gate counted. "Published best" = fewest gates among published
circuits within the same caps (#AND <= A, AND depth <= AD, gate depth <= GD); ** = better.
One row per (A, AD, G, GD); "other" = further distinct circuits with the same tuple (BEST.json lists them).

### S-box with 29 <= #AND <= 31 (published circuits here have G >= 137)

| File | #AND (A) | AND depth | #Gates (G) | Gate depth | XX (x+x') | #XOR | #XNOR | published best within the same caps | other |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| aes-sbox-a30-ad4-g138-gd15-xx108-61.circ.txt | 30 | 4 | **138** | 15 | 108 | 47 | 61 | 153 (A28 AD4 GD15) | 3 |
| aes-sbox-a29-ad4-g141-gd15-xx112-56.circ.txt | 29 | 4 | **141** | 15 | 112 | 56 | 56 | 153 (A28 AD4 GD15) | 3 |
| aes-sbox-a29-ad4-g136-gd16-xx107-59.circ.txt | 29 | 4 | **136** | 16 | 107 | 48 | 59 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a31-ad5-g124-gd17-xx93-35.circ.txt | 31 | 5 | **124** | 17 | 93 | 58 | 35 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a29-ad4-g134-gd17-xx105-51.circ.txt | 29 | 4 | **134** | 17 | 105 | 54 | 51 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a31-ad5-g121-gd18-xx90-29.circ.txt | 31 | 5 | **121** | 18 | 90 | 61 | 29 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a29-ad5-g130-gd18-xx101-43.circ.txt | 29 | 5 | **130** | 18 | 101 | 58 | 43 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a29-ad4-g133-gd18-xx104-64.circ.txt | 29 | 4 | **133** | 18 | 104 | 40 | 64 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a31-ad5-g118-gd19-xx87-39.circ.txt | 31 | 5 | **118** | 19 | 87 | 48 | 39 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a29-ad4-g132-gd19-xx103-52.circ.txt | 29 | 4 | **132** | 19 | 103 | 51 | 52 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a31-ad5-g117-gd20-xx86-24.circ.txt | 31 | 5 | **117** | 20 | 86 | 62 | 24 | 128 (A28 AD5 GD20) | 3 |
| aes-sbox-a29-ad4-g129-gd20-xx100-52.circ.txt | 29 | 4 | **129** | 20 | 100 | 48 | 52 | 134 (A28 AD4 GD20) | 0 |
| aes-sbox-a31-ad5-g116-gd22-xx85-6.circ.txt | 31 | 5 | **116** | 22 | 85 | 79 | 6 | 128 (A28 AD5 GD20) | 3 |
| aes-sbox-a29-ad4-g128-gd23-xx99-51.circ.txt | 29 | 4 | **128** | 23 | 99 | 48 | 51 | 132 (A28 AD4 GD22) | 0 |
| aes-sbox-a31-ad5-g115-gd24-xx84-19.circ.txt | 31 | 5 | **115** | 24 | 84 | 65 | 19 | 128 (A28 AD5 GD20) | 5 |
| aes-sbox-a31-ad5-g114-gd28-xx83-18.circ.txt | 31 | 5 | **114** | 28 | 83 | 65 | 18 | 124 (A28 AD5 GD27) | 3 |

### S-box with #AND = 28

| File | #AND (A) | AND depth | #Gates (G) | Gate depth | XX (x+x') | #XOR | #XNOR | published best within the same caps | other |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| aes-sbox-a28-ad4-g175-gd14-xx147-68.circ.txt | 28 | 4 | **175** | 14 | 147 | 79 | 68 | 176 (A28 AD4 GD14) | 6 |
| aes-sbox-a28-ad5-g136-gd17-xx108-58.circ.txt | 28 | 5 | **136** | 17 | 108 | 50 | 58 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a28-ad4-g138-gd17-xx110-61.circ.txt | 28 | 4 | **138** | 17 | 110 | 49 | 61 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a28-ad5-g133-gd18-xx105-51.circ.txt | 28 | 5 | **133** | 18 | 105 | 54 | 51 | 141 (A28 AD4 GD16) | 6 |
| aes-sbox-a28-ad4-g135-gd18-xx107-55.circ.txt | 28 | 4 | **135** | 18 | 107 | 52 | 55 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a28-ad5-g130-gd19-xx102-53.circ.txt | 28 | 5 | **130** | 19 | 102 | 49 | 53 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a28-ad4-g133-gd19-xx105-55.circ.txt | 28 | 4 | **133** | 19 | 105 | 50 | 55 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a28-ad4-g132-gd20-xx104-56.circ.txt | 28 | 4 | **132** | 20 | 104 | 48 | 56 | 134 (A28 AD4 GD20) | 3 |
| aes-sbox-a28-ad5-g127-gd22-xx99-48.circ.txt | 28 | 5 | **127** | 22 | 99 | 51 | 48 | 128 (A28 AD5 GD20) | 3 |
| aes-sbox-a28-ad4-g131-gd22-xx103-52.circ.txt | 28 | 4 | **131** | 22 | 103 | 51 | 52 | 132 (A28 AD4 GD22) | 5 |
| aes-sbox-a28-ad5-g126-gd24-xx98-45.circ.txt | 28 | 5 | **126** | 24 | 98 | 53 | 45 | 128 (A28 AD5 GD20) | 4 |
| aes-sbox-a28-ad5-g125-gd25-xx97-43.circ.txt | 28 | 5 | **125** | 25 | 97 | 54 | 43 | 128 (A28 AD5 GD20) | 3 |

### S-box with #AND = 32..36 / AD >= 4

| File | #AND (A) | AND depth | #Gates (G) | Gate depth | XX (x+x') | #XOR | #XNOR | published best within the same caps | other |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| aes-sbox-a36-ad4-g129-gd13-xx93-40.circ.txt | 36 | 4 | **129** | 13 | 93 | 53 | 40 | 133 (A35 AD4 GD13) | 3 |
| aes-sbox-a34-ad4-g134-gd13-xx100-43.circ.txt | 34 | 4 | **134** | 13 | 100 | 57 | 43 | 139 (A34 AD4 GD13) | 3 |
| aes-sbox-a35-ad4-g123-gd14-xx88-31.circ.txt | 35 | 4 | **123** | 14 | 88 | 57 | 31 | 125 (A33 AD4 GD14) | 3 |
| aes-sbox-a33-ad4-g115-gd15-xx82-19.circ.txt | 33 | 4 | **115** | 15 | 82 | 63 | 19 | 116 (A33 AD4 GD15) | 3 |
| aes-sbox-a32-ad4-g125-gd15-xx93-37.circ.txt | 32 | 4 | **125** | 15 | 93 | 56 | 37 | 127 (A32 AD4 GD15) | 3 |
| aes-sbox-a33-ad4-g112-gd16-xx79-28.circ.txt | 33 | 4 | **112** | 16 | 79 | 51 | 28 | 116 (A33 AD4 GD15) | 7 |
| aes-sbox-a32-ad5-g115-gd17-xx83-31.circ.txt | 32 | 5 | **115** | 17 | 83 | 52 | 31 | 122 (A32 AD5 GD16) | 4 |
| aes-sbox-a32-ad4-g121-gd17-xx89-35.circ.txt | 32 | 4 | **121** | 17 | 89 | 54 | 35 | 127 (A32 AD4 GD15) | 3 |
| aes-sbox-a33-ad4-g110-gd18-xx77-26.circ.txt | 33 | 4 | **110** | 18 | 77 | 51 | 26 | 116 (A33 AD4 GD15) | 7 |
| aes-sbox-a32-ad5-g112-gd18-xx80-36.circ.txt | 32 | 5 | **112** | 18 | 80 | 44 | 36 | 122 (A32 AD5 GD16) | 3 |
| aes-sbox-a32-ad4-g119-gd18-xx87-30.circ.txt | 32 | 4 | **119** | 18 | 87 | 57 | 30 | 127 (A32 AD4 GD15) | 3 |
| aes-sbox-a33-ad4-g108-gd19-xx75-22.circ.txt | 33 | 4 | **108** | 19 | 75 | 53 | 22 | 116 (A33 AD4 GD15) | 3 |
| aes-sbox-a32-ad5-g111-gd19-xx79-27.circ.txt | 32 | 5 | **111** | 19 | 79 | 52 | 27 | 117 (A32 AD4 GD19) | 3 |
| aes-sbox-a33-ad4-g107-gd20-xx74-26.circ.txt | 33 | 4 | **107** | 20 | 74 | 48 | 26 | 108 (A33 AD4 GD20) | 3 |
| aes-sbox-a32-ad5-g108-gd20-xx76-35.circ.txt | 32 | 5 | **108** | 20 | 76 | 41 | 35 | 109 (A32 AD5 GD20) | 3 |
| aes-sbox-a32-ad4-g116-gd20-xx84-6.circ.txt | 32 | 4 | **116** | 20 | 84 | 78 | 6 | 117 (A32 AD4 GD19) | 3 |
| aes-sbox-a32-ad4-g115-gd22-xx83-20.circ.txt | 32 | 4 | **115** | 22 | 83 | 63 | 20 | 117 (A32 AD4 GD19) | 3 |
| aes-sbox-a32-ad5-g106-gd24-xx74-22.circ.txt | 32 | 5 | **106** | 24 | 74 | 52 | 22 | 107 (A32 AD5 GD22) | 15 |
| aes-sbox-a32-ad4-g114-gd26-xx82-18.circ.txt | 32 | 4 | **114** | 26 | 82 | 64 | 18 | 117 (A32 AD4 GD19) | 3 |
| aes-sbox-a32-ad5-g104-gd29-xx72-23.circ.txt | 32 | 5 | **104** | 29 | 72 | 49 | 23 | 105 (A32 AD5 GD26) | 3 |

### S-box with #AND <= 36 / AD3

| File | #AND (A) | AND depth | #Gates (G) | Gate depth | XX (x+x') | #XOR | #XNOR | published best within the same caps | other |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| aes-sbox-a35-ad3-g177-gd13-xx142-61.circ.txt | 35 | 3 | **177** | 13 | 142 | 81 | 61 | 183 (A35 AD3 GD13) | 3 |
| aes-sbox-a36-ad3-g161-gd14-xx125-57.circ.txt | 36 | 3 | **161** | 14 | 125 | 68 | 57 | 172 (A35 AD3 GD14) | 3 |
| aes-sbox-a35-ad3-g162-gd14-xx127-61.circ.txt | 35 | 3 | **162** | 14 | 127 | 66 | 61 | 172 (A35 AD3 GD14) | 6 |
| aes-sbox-a35-ad3-g151-gd16-xx116-57.circ.txt | 35 | 3 | **151** | 16 | 116 | 59 | 57 | 157 (A35 AD3 GD15) | 3 |
| aes-sbox-a35-ad3-g148-gd17-xx113-51.circ.txt | 35 | 3 | **148** | 17 | 113 | 62 | 51 | 157 (A35 AD3 GD15) | 3 |
| aes-sbox-a35-ad3-g143-gd18-xx108-49.circ.txt | 35 | 3 | **143** | 18 | 108 | 59 | 49 | 157 (A35 AD3 GD15) | 0 |
| aes-sbox-a35-ad3-g142-gd19-xx107-50.circ.txt | 35 | 3 | **142** | 19 | 107 | 57 | 50 | 157 (A35 AD3 GD15) | 0 |
| aes-sbox-a35-ad3-g141-gd24-xx106-38.circ.txt | 35 | 3 | **141** | 24 | 106 | 68 | 38 | 147 (A35 AD3 GD20) | 8 |
| aes-sbox-a35-ad3-g140-gd25-xx105-35.circ.txt | 35 | 3 | **140** | 25 | 105 | 70 | 35 | 141 (A35 AD3 GD25) | 3 |

### S-box with #AND > 36 (gate depth traded for ANDs)

| File | #AND (A) | AND depth | #Gates (G) | Gate depth | XX (x+x') | #XOR | #XNOR | published best within the same caps | other |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| aes-sbox-a48-ad4-g151-gd11-xx103-39.circ.txt | 48 | 4 | **151** | 11 | 103 | 64 | 39 | none | 5 |
| aes-sbox-a47-ad4-g186-gd11-xx139-70.circ.txt | 47 | 4 | **186** | 11 | 139 | 69 | 70 | none | 0 |
| aes-sbox-a46-ad4-g203-gd11-xx157-78.circ.txt | 46 | 4 | **203** | 11 | 157 | 79 | 78 | none | 0 |
| aes-sbox-a44-ad4-g254-gd11-xx210-122.circ.txt | 44 | 4 | **254** | 11 | 210 | 88 | 122 | none | 0 |
| aes-sbox-a43-ad4-g278-gd11-xx235-123.circ.txt | 43 | 4 | **278** | 11 | 235 | 112 | 123 | none | 0 |
| aes-sbox-a42-ad4-g284-gd11-xx242-114.circ.txt | 42 | 4 | **284** | 11 | 242 | 128 | 114 | none | 0 |
| aes-sbox-a43-ad4-g141-gd12-xx98-37.circ.txt | 43 | 4 | **141** | 12 | 98 | 61 | 37 | none | 3 |
| aes-sbox-a42-ad4-g230-gd12-xx188-97.circ.txt | 42 | 4 | **230** | 12 | 188 | 91 | 97 | none | 0 |
| aes-sbox-a39-ad3-g172-gd13-xx133-62.circ.txt | 39 | 3 | **172** | 13 | 133 | 71 | 62 | 183 (A35 AD3 GD13) | 0 |
| aes-sbox-a37-ad4-g121-gd14-xx84-36.circ.txt | 37 | 4 | **121** | 14 | 84 | 48 | 36 | 125 (A33 AD4 GD14) | 3 |
| aes-sbox-a37-ad3-g160-gd14-xx123-55.circ.txt | 37 | 3 | **160** | 14 | 123 | 68 | 55 | 172 (A35 AD3 GD14) | 3 |
| aes-sbox-a37-ad3-g155-gd15-xx118-48.circ.txt | 37 | 3 | **155** | 15 | 118 | 70 | 48 | 157 (A35 AD3 GD15) | 3 |

### Fewest gates at each gate-depth cap

| GD <= | published best (A AD G GD) | ours (A AD G GD) |
|---|---|---|
| 13 | 35 4 133 13 | **36 4 129 13** |
| 14 | 33 4 125 14 | **37 4 121 14** |
| 15 | 33 4 116 15 | **33 4 115 15** |
| 16 | 33 4 116 15 | **33 4 112 16** |
| 17 | 33 4 116 15 | **33 4 112 16** |
| 18 | 33 4 116 15 | **33 4 110 18** |
| 19 | 33 4 116 15 | **33 4 108 19** |
| 20 | 33 4 108 20 | **33 4 107 20** |
| 21 | 33 4 108 20 | **33 4 107 20** |
| 29 | 32 5 105 26 | **32 5 104 29** |

Sources: long, results/aes

Candidates: 17931 files, 3370 distinct circuits, 1518 distinct tuples, 409 not dominated by the pinned set; 0 files could not be read.
