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
| aes-sbox-a29-ad4-g135-gd16-xx106-50.circ.txt | 29 | 4 | **135** | 16 | 106 | 56 | 50 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a31-ad5-g124-gd17-xx93-35.circ.txt | 31 | 5 | **124** | 17 | 93 | 58 | 35 | 141 (A28 AD4 GD16) | 6 |
| aes-sbox-a29-ad4-g131-gd17-xx102-61.circ.txt | 29 | 4 | **131** | 17 | 102 | 41 | 61 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a31-ad5-g121-gd18-xx90-29.circ.txt | 31 | 5 | **121** | 18 | 90 | 61 | 29 | 141 (A28 AD4 GD16) | 5 |
| aes-sbox-a29-ad5-g130-gd18-xx101-43.circ.txt | 29 | 5 | **130** | 18 | 101 | 58 | 43 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a31-ad5-g118-gd19-xx87-39.circ.txt | 31 | 5 | **118** | 19 | 87 | 48 | 39 | 141 (A28 AD4 GD16) | 6 |
| aes-sbox-a29-ad4-g129-gd19-xx100-56.circ.txt | 29 | 4 | **129** | 19 | 100 | 44 | 56 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a31-ad5-g117-gd20-xx86-24.circ.txt | 31 | 5 | **117** | 20 | 86 | 62 | 24 | 128 (A28 AD5 GD20) | 3 |
| aes-sbox-a31-ad5-g116-gd22-xx85-6.circ.txt | 31 | 5 | **116** | 22 | 85 | 79 | 6 | 128 (A28 AD5 GD20) | 4 |
| aes-sbox-a29-ad4-g128-gd23-xx99-51.circ.txt | 29 | 4 | **128** | 23 | 99 | 48 | 51 | 132 (A28 AD4 GD22) | 3 |
| aes-sbox-a31-ad5-g115-gd24-xx84-19.circ.txt | 31 | 5 | **115** | 24 | 84 | 65 | 19 | 128 (A28 AD5 GD20) | 5 |
| aes-sbox-a31-ad5-g114-gd28-xx83-18.circ.txt | 31 | 5 | **114** | 28 | 83 | 65 | 18 | 124 (A28 AD5 GD27) | 4 |

### S-box with #AND = 28

| File | #AND (A) | AND depth | #Gates (G) | Gate depth | XX (x+x') | #XOR | #XNOR | published best within the same caps | other |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| aes-sbox-a28-ad4-g174-gd14-xx146-80.circ.txt | 28 | 4 | **174** | 14 | 146 | 66 | 80 | 176 (A28 AD4 GD14) | 1 |
| aes-sbox-a28-ad5-g136-gd17-xx108-58.circ.txt | 28 | 5 | **136** | 17 | 108 | 50 | 58 | 141 (A28 AD4 GD16) | 5 |
| aes-sbox-a28-ad4-g138-gd17-xx110-61.circ.txt | 28 | 4 | **138** | 17 | 110 | 49 | 61 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a28-ad5-g133-gd18-xx105-51.circ.txt | 28 | 5 | **133** | 18 | 105 | 54 | 51 | 141 (A28 AD4 GD16) | 8 |
| aes-sbox-a28-ad4-g135-gd18-xx107-55.circ.txt | 28 | 4 | **135** | 18 | 107 | 52 | 55 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a28-ad5-g129-gd19-xx101-56.circ.txt | 28 | 5 | **129** | 19 | 101 | 45 | 56 | 141 (A28 AD4 GD16) | 43 |
| aes-sbox-a28-ad4-g133-gd19-xx105-55.circ.txt | 28 | 4 | **133** | 19 | 105 | 50 | 55 | 141 (A28 AD4 GD16) | 3 |
| aes-sbox-a28-ad4-g132-gd20-xx104-56.circ.txt | 28 | 4 | **132** | 20 | 104 | 48 | 56 | 134 (A28 AD4 GD20) | 4 |
| aes-sbox-a28-ad5-g127-gd22-xx99-48.circ.txt | 28 | 5 | **127** | 22 | 99 | 51 | 48 | 128 (A28 AD5 GD20) | 5 |
| aes-sbox-a28-ad4-g131-gd22-xx103-52.circ.txt | 28 | 4 | **131** | 22 | 103 | 51 | 52 | 132 (A28 AD4 GD22) | 8 |
| aes-sbox-a28-ad5-g126-gd23-xx98-58.circ.txt | 28 | 5 | **126** | 23 | 98 | 40 | 58 | 128 (A28 AD5 GD20) | 1 |
| aes-sbox-a28-ad5-g125-gd24-xx97-50.circ.txt | 28 | 5 | **125** | 24 | 97 | 47 | 50 | 128 (A28 AD5 GD20) | 1 |
| aes-sbox-a28-ad4-g130-gd24-xx102-45.circ.txt | 28 | 4 | **130** | 24 | 102 | 57 | 45 | 132 (A28 AD4 GD22) | 0 |

### S-box with #AND = 32..36 / AD >= 4

| File | #AND (A) | AND depth | #Gates (G) | Gate depth | XX (x+x') | #XOR | #XNOR | published best within the same caps | other |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| aes-sbox-a36-ad4-g129-gd13-xx93-40.circ.txt | 36 | 4 | **129** | 13 | 93 | 53 | 40 | 133 (A35 AD4 GD13) | 3 |
| aes-sbox-a34-ad4-g134-gd13-xx100-43.circ.txt | 34 | 4 | **134** | 13 | 100 | 57 | 43 | 139 (A34 AD4 GD13) | 3 |
| aes-sbox-a34-ad4-g122-gd14-xx88-38.circ.txt | 34 | 4 | **122** | 14 | 88 | 50 | 38 | 125 (A33 AD4 GD14) | 1 |
| aes-sbox-a33-ad4-g115-gd15-xx82-19.circ.txt | 33 | 4 | **115** | 15 | 82 | 63 | 19 | 116 (A33 AD4 GD15) | 4 |
| aes-sbox-a32-ad4-g125-gd15-xx93-37.circ.txt | 32 | 4 | **125** | 15 | 93 | 56 | 37 | 127 (A32 AD4 GD15) | 6 |
| aes-sbox-a33-ad4-g112-gd16-xx79-28.circ.txt | 33 | 4 | **112** | 16 | 79 | 51 | 28 | 116 (A33 AD4 GD15) | 9 |
| aes-sbox-a32-ad4-g119-gd16-xx87-37.circ.txt | 32 | 4 | **119** | 16 | 87 | 50 | 37 | 127 (A32 AD4 GD15) | 0 |
| aes-sbox-a32-ad5-g115-gd17-xx83-31.circ.txt | 32 | 5 | **115** | 17 | 83 | 52 | 31 | 122 (A32 AD5 GD16) | 7 |
| aes-sbox-a32-ad4-g117-gd17-xx85-35.circ.txt | 32 | 4 | **117** | 17 | 85 | 50 | 35 | 127 (A32 AD4 GD15) | 4 |
| aes-sbox-a33-ad4-g110-gd18-xx77-26.circ.txt | 33 | 4 | **110** | 18 | 77 | 51 | 26 | 116 (A33 AD4 GD15) | 10 |
| aes-sbox-a32-ad5-g111-gd18-xx79-34.circ.txt | 32 | 5 | **111** | 18 | 79 | 45 | 34 | 122 (A32 AD5 GD16) | 1 |
| aes-sbox-a32-ad4-g115-gd18-xx83-35.circ.txt | 32 | 4 | **115** | 18 | 83 | 48 | 35 | 127 (A32 AD4 GD15) | 5 |
| aes-sbox-a33-ad4-g108-gd19-xx75-22.circ.txt | 33 | 4 | **108** | 19 | 75 | 53 | 22 | 116 (A33 AD4 GD15) | 3 |
| aes-sbox-a32-ad5-g110-gd19-xx78-31.circ.txt | 32 | 5 | **110** | 19 | 78 | 47 | 31 | 117 (A32 AD4 GD19) | 1 |
| aes-sbox-a32-ad4-g114-gd19-xx82-45.circ.txt | 32 | 4 | **114** | 19 | 82 | 37 | 45 | 117 (A32 AD4 GD19) | 16 |
| aes-sbox-a33-ad4-g107-gd20-xx74-26.circ.txt | 33 | 4 | **107** | 20 | 74 | 48 | 26 | 108 (A33 AD4 GD20) | 4 |
| aes-sbox-a32-ad5-g108-gd20-xx76-35.circ.txt | 32 | 5 | **108** | 20 | 76 | 41 | 35 | 109 (A32 AD5 GD20) | 6 |
| aes-sbox-a32-ad4-g113-gd20-xx81-36.circ.txt | 32 | 4 | **113** | 20 | 81 | 45 | 36 | 117 (A32 AD4 GD19) | 11 |
| aes-sbox-a32-ad5-g106-gd21-xx74-28.circ.txt | 32 | 5 | **106** | 21 | 74 | 46 | 28 | 109 (A32 AD5 GD20) | 1 |
| aes-sbox-a32-ad4-g112-gd21-xx80-33.circ.txt | 32 | 4 | **112** | 21 | 80 | 47 | 33 | 117 (A32 AD4 GD19) | 1 |
| aes-sbox-a32-ad5-g105-gd24-xx73-24.circ.txt | 32 | 5 | **105** | 24 | 73 | 49 | 24 | 107 (A32 AD5 GD22) | 1 |
| aes-sbox-a32-ad4-g111-gd25-xx79-30.circ.txt | 32 | 4 | **111** | 25 | 79 | 49 | 30 | 117 (A32 AD4 GD19) | 6 |
| aes-sbox-a32-ad7-g104-gd26-xx72-31.circ.txt | 32 | 7 | **104** | 26 | 72 | 41 | 31 | 105 (A32 AD5 GD26) | 1 |
| aes-sbox-a32-ad7-g103-gd29-xx71-25.circ.txt | 32 | 7 | **103** | 29 | 71 | 46 | 25 | 105 (A32 AD5 GD26) | 1 |
| aes-sbox-a32-ad5-g104-gd29-xx72-23.circ.txt | 32 | 5 | **104** | 29 | 72 | 49 | 23 | 105 (A32 AD5 GD26) | 5 |

### S-box with #AND <= 36 / AD3

| File | #AND (A) | AND depth | #Gates (G) | Gate depth | XX (x+x') | #XOR | #XNOR | published best within the same caps | other |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| aes-sbox-a35-ad3-g181-gd12-xx146-80.circ.txt | 35 | 3 | **181** | 12 | 146 | 66 | 80 | none | 2 |
| aes-sbox-a35-ad3-g165-gd13-xx130-60.circ.txt | 35 | 3 | **165** | 13 | 130 | 70 | 60 | 183 (A35 AD3 GD13) | 1 |
| aes-sbox-a36-ad3-g161-gd14-xx125-57.circ.txt | 36 | 3 | **161** | 14 | 125 | 68 | 57 | 172 (A35 AD3 GD14) | 3 |
| aes-sbox-a35-ad3-g162-gd14-xx127-61.circ.txt | 35 | 3 | **162** | 14 | 127 | 66 | 61 | 172 (A35 AD3 GD14) | 6 |
| aes-sbox-a35-ad3-g155-gd15-xx120-56.circ.txt | 35 | 3 | **155** | 15 | 120 | 64 | 56 | 157 (A35 AD3 GD15) | 3 |
| aes-sbox-a35-ad3-g147-gd16-xx112-56.circ.txt | 35 | 3 | **147** | 16 | 112 | 56 | 56 | 157 (A35 AD3 GD15) | 3 |
| aes-sbox-a35-ad3-g144-gd17-xx109-43.circ.txt | 35 | 3 | **144** | 17 | 109 | 66 | 43 | 157 (A35 AD3 GD15) | 3 |
| aes-sbox-a35-ad3-g143-gd18-xx108-49.circ.txt | 35 | 3 | **143** | 18 | 108 | 59 | 49 | 157 (A35 AD3 GD15) | 3 |
| aes-sbox-a35-ad3-g141-gd19-xx106-45.circ.txt | 35 | 3 | **141** | 19 | 106 | 61 | 45 | 157 (A35 AD3 GD15) | 5 |
| aes-sbox-a35-ad3-g139-gd21-xx104-50.circ.txt | 35 | 3 | **139** | 21 | 104 | 54 | 50 | 147 (A35 AD3 GD20) | 0 |
| aes-sbox-a35-ad3-g138-gd23-xx103-46.circ.txt | 35 | 3 | **138** | 23 | 103 | 57 | 46 | 147 (A35 AD3 GD20) | 1 |
| aes-sbox-a35-ad3-g137-gd28-xx102-47.circ.txt | 35 | 3 | **137** | 28 | 102 | 55 | 47 | 139 (A35 AD3 GD27) | 0 |

### S-box with #AND > 36 (gate depth traded for ANDs)

| File | #AND (A) | AND depth | #Gates (G) | Gate depth | XX (x+x') | #XOR | #XNOR | published best within the same caps | other |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| aes-sbox-a48-ad4-g151-gd11-xx103-39.circ.txt | 48 | 4 | **151** | 11 | 103 | 64 | 39 | none | 5 |
| aes-sbox-a47-ad4-g186-gd11-xx139-70.circ.txt | 47 | 4 | **186** | 11 | 139 | 69 | 70 | none | 3 |
| aes-sbox-a46-ad4-g200-gd11-xx154-63.circ.txt | 46 | 4 | **200** | 11 | 154 | 91 | 63 | none | 3 |
| aes-sbox-a44-ad4-g254-gd11-xx210-122.circ.txt | 44 | 4 | **254** | 11 | 210 | 88 | 122 | none | 3 |
| aes-sbox-a43-ad4-g278-gd11-xx235-123.circ.txt | 43 | 4 | **278** | 11 | 235 | 112 | 123 | none | 3 |
| aes-sbox-a42-ad4-g284-gd11-xx242-114.circ.txt | 42 | 4 | **284** | 11 | 242 | 128 | 114 | none | 3 |
| aes-sbox-a38-ad4-g135-gd12-xx97-25.circ.txt | 38 | 4 | **135** | 12 | 97 | 72 | 25 | none | 0 |
| aes-sbox-a37-ad4-g127-gd13-xx90-41.circ.txt | 37 | 4 | **127** | 13 | 90 | 49 | 41 | 133 (A35 AD4 GD13) | 0 |
| aes-sbox-a37-ad4-g121-gd14-xx84-36.circ.txt | 37 | 4 | **121** | 14 | 84 | 48 | 36 | 125 (A33 AD4 GD14) | 3 |
| aes-sbox-a37-ad3-g160-gd14-xx123-55.circ.txt | 37 | 3 | **160** | 14 | 123 | 68 | 55 | 172 (A35 AD3 GD14) | 3 |

### Fewest gates at each gate-depth cap

| GD <= | published best (A AD G GD) | ours (A AD G GD) |
|---|---|---|
| 12 | 45 4 141 12 | **38 4 135 12** |
| 13 | 35 4 133 13 | **37 4 127 13** |
| 14 | 33 4 125 14 | **37 4 121 14** |
| 15 | 33 4 116 15 | **33 4 115 15** |
| 16 | 33 4 116 15 | **33 4 112 16** |
| 17 | 33 4 116 15 | **33 4 112 16** |
| 18 | 33 4 116 15 | **33 4 110 18** |
| 19 | 33 4 116 15 | **33 4 108 19** |
| 20 | 33 4 108 20 | **33 4 107 20** |
| 21 | 33 4 108 20 | **32 5 106 21** |
| 24 | 33 4 106 22 | **32 5 105 24** |
| 26 | 32 5 105 26 | **32 7 104 26** |
| 27 | 32 5 105 26 | **32 7 104 26** |
| 28 | 32 5 105 26 | **32 7 104 26** |
| 29 | 32 5 105 26 | **32 7 103 29** |
| 30 | 32 5 104 30 | **32 7 103 29** |
| 31 | 32 5 104 30 | **32 7 103 29** |

Sources: results/aes

Candidates: 19209 files, 4474 distinct circuits, 1878 distinct tuples, 617 not dominated by the pinned set; 0 files could not be read.
