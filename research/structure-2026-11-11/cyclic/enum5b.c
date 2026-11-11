/* enum5b.c -- are the non-circuit cyclic sets of F_2^5 circuits with respect to OTHER inputs?
 *
 * Usage:  gcc -O2 -fopenmp -o enum5b.bin enum5b.c && OMP_NUM_THREADS=4 ./enum5b.bin
 *
 * For every set S = units + X (X a subset of the 26 non-unit points) that is cyclic but not a circuit
 * set, try every basis B of F_2^5 contained in S and test whether the closure of B under collinear
 * triples of S is S ("S is a circuit set with B as inputs").  Also compute the rank over F_3 of the
 * 0/1 matrix of collinear triples: if it is below |S| - 5, no basis can work (REPORT.md, Theorem W
 * with all weights 1 over F_3).
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

#define NP 26
#define NSUB (1u << NP)
#define UNITS ((1u << 1) | (1u << 2) | (1u << 4) | (1u << 8) | (1u << 16))

static int pt[NP];
static uint32_t tabLo[1 << 13], tabHi[1 << 13];

static inline int closes(uint32_t P, uint32_t start) {
    uint32_t C = start, F = start;
    while (F) {
        int a = __builtin_ctz(F);
        F &= F - 1;
        uint32_t B = C & ~(1u << a);
        while (B) {
            int b = __builtin_ctz(B);
            B &= B - 1;
            int c = a ^ b;
            if (((P >> c) & 1u) && !((C >> c) & 1u)) { C |= 1u << c; F |= 1u << c; }
        }
    }
    return C == P;
}

static int tri_rank_p(uint32_t P, int p) { /* rank of the triple matrix over F_p, p = 2 or 3 */
    int pos[32], n = 0;
    uint32_t T = P;
    while (T) { int v = __builtin_ctz(T); T &= T - 1; pos[v] = n++; }
    int8_t basis[32][32];
    int has[32];
    memset(has, 0, sizeof has);
    int rank = 0;
    uint32_t A = P;
    while (A) {
        int a = __builtin_ctz(A);
        A &= A - 1;
        uint32_t B = A;
        while (B) {
            int b = __builtin_ctz(B);
            B &= B - 1;
            int c = a ^ b;
            if (c > b && ((P >> c) & 1u)) {
                int8_t r[32];
                memset(r, 0, sizeof r);
                r[pos[a]] = r[pos[b]] = r[pos[c]] = 1;
                for (int h = n - 1; h >= 0; h--) {
                    if (!r[h]) continue;
                    if (!has[h]) {
                        int inv = (r[h] == 1) ? 1 : (p == 3 ? 2 : 1);
                        for (int j = 0; j <= h; j++) basis[h][j] = (int8_t)((r[j] * inv) % p);
                        has[h] = 1;
                        rank++;
                        break;
                    }
                    int f = r[h];
                    for (int j = 0; j <= h; j++) r[j] = (int8_t)(((r[j] - f * basis[h][j]) % p + p) % p);
                }
            }
        }
    }
    return rank;
}

static int some_basis_closes(uint32_t P) {
    int el[32], n = 0;
    uint32_t T = P;
    while (T) { el[n++] = __builtin_ctz(T); T &= T - 1; }
    for (int i0 = 0; i0 < n; i0++)
    for (int i1 = i0 + 1; i1 < n; i1++)
    for (int i2 = i1 + 1; i2 < n; i2++) {
        int a = el[i0], b = el[i1], c = el[i2];
        if ((a ^ b) == c) continue;
        uint32_t span3 = (1u << a) | (1u << b) | (1u << c) | (1u << (a ^ b)) | (1u << (a ^ c)) | (1u << (b ^ c)) | (1u << (a ^ b ^ c));
        for (int i3 = i2 + 1; i3 < n; i3++) {
            int d = el[i3];
            if ((span3 >> d) & 1u) continue;
            uint32_t span4 = span3 | (1u << d);
            for (int v = 1; v < 32; v++) if ((span3 >> v) & 1u) span4 |= 1u << (v ^ d);
            for (int i4 = i3 + 1; i4 < n; i4++) {
                int e = el[i4];
                if ((span4 >> e) & 1u) continue;
                if (closes(P, (1u << a) | (1u << b) | (1u << c) | (1u << d) | (1u << e))) return 1;
            }
        }
    }
    return 0;
}

int main(void) {
    int np = 0;
    for (int v = 1; v < 32; v++) if (__builtin_popcount(v) >= 2) pt[np++] = v;
    for (uint32_t h = 0; h < (1u << 13); h++) {
        uint32_t lo = 0, hi = 0;
        for (int i = 0; i < 13; i++) if ((h >> i) & 1u) { lo |= 1u << pt[i]; hi |= 1u << pt[13 + i]; }
        tabLo[h] = lo; tabHi[h] = hi;
    }
    long long nonc[NP + 1], nobasis[NP + 1], lowf3[NP + 1];
    memset(nonc, 0, sizeof nonc); memset(nobasis, 0, sizeof nobasis); memset(lowf3, 0, sizeof lowf3);
#pragma omp parallel
    {
        long long a[NP + 1], b[NP + 1], c[NP + 1];
        memset(a, 0, sizeof a); memset(b, 0, sizeof b); memset(c, 0, sizeof c);
#pragma omp for schedule(dynamic, 65536)
        for (uint32_t X = 0; X < NSUB; X++) {
            uint32_t P = UNITS | tabLo[X & 8191u] | tabHi[X >> 13];
            int k = __builtin_popcount(X);
            if (k < 6 || closes(P, UNITS)) continue;
            if (tri_rank_p(P, 2) != k) continue;
            a[k]++;
            if (!some_basis_closes(P)) b[k]++;
            if (tri_rank_p(P, 3) < k) c[k]++;
        }
#pragma omp critical
        for (int k = 0; k <= NP; k++) { nonc[k] += a[k]; nobasis[k] += b[k]; lowf3[k] += c[k]; }
    }
    printf("size  cyclic_not_circuit  no_basis_of_S_closes  F3_rank_below_size\n");
    long long t1 = 0, t2 = 0, t3 = 0;
    for (int k = 0; k <= NP; k++)
        if (nonc[k]) {
            printf("%4d  %18lld  %20lld  %18lld\n", k, nonc[k], nobasis[k], lowf3[k]);
            t1 += nonc[k]; t2 += nobasis[k]; t3 += lowf3[k];
        }
    printf("total %18lld  %20lld  %18lld\n", t1, t2, t3);
    return 0;
}
