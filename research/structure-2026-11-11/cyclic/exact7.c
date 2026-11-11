/* exact7.c -- the enumeration of exact6.c for n <= 7 inputs (128-bit point sets).
 *
 * Usage:  gcc -O2 -o exact7.bin exact7.c && ./exact7.bin KMAX CYC < matrices.txt
 *   KMAX = largest number of extra vectors tried; CYC = 1 to look for cyclic systems as well, 0 for
 *   circuits only.
 * Input lines:  n m r_1 ... r_m
 * Output line:  Lcyc L | cyclic witness extras | circuit witness extras
 *               (-1 = none with at most KMAX extra vectors; Lcyc is -2 when CYC = 0)
 * Same exhaustive method as exact6.c.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

typedef unsigned __int128 u128;

static int n, mt, ncand, cand[128];
static u128 UNITS, TB;
static int found_cyc, found_circ, want_cyc;
static int cur[16], wit_cyc[16], wit_circ[16];
static u128 M1, M2, M4, M8, M16, M32;

static inline int ctz128(u128 x) { uint64_t lo = (uint64_t)x; return lo ? __builtin_ctzll(lo) : 64 + __builtin_ctzll((uint64_t)(x >> 64)); }
static inline int clz128(u128 x) { uint64_t hi = (uint64_t)(x >> 64); return hi ? __builtin_clzll(hi) : 64 + __builtin_clzll((uint64_t)x); }
static inline int pop128(u128 x) { return __builtin_popcountll((uint64_t)x) + __builtin_popcountll((uint64_t)(x >> 64)); }
#define ONE ((u128)1)

static inline u128 xlate(u128 P, int v) {
    if (v & 1) P = ((P & M1) << 1) | ((P >> 1) & M1);
    if (v & 2) P = ((P & M2) << 2) | ((P >> 2) & M2);
    if (v & 4) P = ((P & M4) << 4) | ((P >> 4) & M4);
    if (v & 8) P = ((P & M8) << 8) | ((P >> 8) & M8);
    if (v & 16) P = ((P & M16) << 16) | ((P >> 16) & M16);
    if (v & 32) P = ((P & M32) << 32) | ((P >> 32) & M32);
    if (v & 64) P = (P << 64) | (P >> 64);
    return P;
}

static int is_circuit(u128 P) {
    u128 C = UNITS;
    for (;;) {
        u128 R = P & ~C, add = 0;
        if (!R) return 1;
        while (R) {
            int v = ctz128(R);
            R &= R - 1;
            if (C & xlate(C, v)) add |= ONE << v;
        }
        if (!add) return 0;
        C |= add;
    }
}

static int is_cyclic(u128 P, int need) {
    u128 R = P & ~UNITS;
    while (R) {
        int v = ctz128(R);
        R &= R - 1;
        if (!(P & xlate(P, v))) return 0;
    }
    static u128 basis[128];
    memset(basis, 0, sizeof basis);
    int rank = 0;
    u128 A = P;
    while (A) {
        int a = ctz128(A);
        A &= A - 1;
        u128 B = P & xlate(P, a) & ~((ONE << a) | ((ONE << a) - 1));
        while (B) {
            int b = ctz128(B);
            B &= B - 1;
            int c = a ^ b;
            if (c > b) {
                u128 r = (ONE << pop128(P & ((ONE << a) - 1))) | (ONE << pop128(P & ((ONE << b) - 1))) |
                         (ONE << pop128(P & ((ONE << c) - 1)));
                while (r) {
                    int h = 127 - clz128(r);
                    if (!basis[h]) { basis[h] = r; rank++; break; }
                    r ^= basis[h];
                }
                if (rank == need) return 1;
            }
        }
    }
    return rank == need;
}

static void rec(int start, int left, int k, u128 P) {
    if (found_circ) return;
    if (left == 0) {
        if (want_cyc && !found_cyc && is_cyclic(P, mt + k)) { found_cyc = 1; memcpy(wit_cyc, cur, sizeof cur); }
        if (is_circuit(P)) { found_circ = 1; memcpy(wit_circ, cur, sizeof cur); }
        return;
    }
    for (int i = start; i <= ncand - left; i++) {
        cur[k - left] = cand[i];
        rec(i + 1, left - 1, k, P | (ONE << cand[i]));
        if (found_circ) return;
    }
}

int main(int argc, char **argv) {
    int kmax = argc > 1 ? atoi(argv[1]) : 3;
    want_cyc = argc > 2 ? atoi(argv[2]) : 1;
    uint64_t m1 = 0x5555555555555555ULL, m2 = 0x3333333333333333ULL, m4 = 0x0F0F0F0F0F0F0F0FULL,
             m8 = 0x00FF00FF00FF00FFULL, m16 = 0x0000FFFF0000FFFFULL, m32 = 0x00000000FFFFFFFFULL;
    M1 = ((u128)m1 << 64) | m1; M2 = ((u128)m2 << 64) | m2; M4 = ((u128)m4 << 64) | m4;
    M8 = ((u128)m8 << 64) | m8; M16 = ((u128)m16 << 64) | m16; M32 = ((u128)m32 << 64) | m32;
    int m;
    while (scanf("%d %d", &n, &m) == 2) {
        u128 seen = 0;
        mt = 0;
        UNITS = 0;
        for (int j = 0; j < n; j++) UNITS |= ONE << (1 << j);
        for (int i = 0; i < m; i++) {
            int r;
            if (scanf("%d", &r) != 1) return 1;
            if (r == 0 || (r & (r - 1)) == 0) continue;
            if ((seen >> r) & 1) continue;
            seen |= ONE << r;
            mt++;
        }
        TB = seen;
        ncand = 0;
        for (int v = 1; v < (1 << n); v++)
            if ((v & (v - 1)) && !((seen >> v) & 1)) cand[ncand++] = v;
        int Lcyc = want_cyc ? -1 : -2, L = -1, kc = 0, kl = 0;
        found_cyc = found_circ = 0;
        for (int k = 0; k <= kmax && !found_circ; k++) {
            int had = found_cyc;
            rec(0, k, k, UNITS | TB);
            if (found_cyc && !had) { Lcyc = mt + k; kc = k; }
            if (found_circ) { L = mt + k; kl = k; }
        }
        printf("%d %d |", Lcyc, L);
        for (int i = 0; i < kc; i++) printf(" %d", wit_cyc[i]);
        printf(" |");
        for (int i = 0; i < kl; i++) printf(" %d", wit_circ[i]);
        printf("\n");
        fflush(stdout);
    }
    return 0;
}
