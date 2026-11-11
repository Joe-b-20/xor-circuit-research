/* exact6.c -- exact L and L_cyc of small target sets (n <= 6 inputs) by exhaustive enumeration.
 *
 * Usage:  gcc -O2 -o exact6.bin exact6.c && ./exact6.bin KMAX < matrices.txt
 * Input lines:  n m r_1 ... r_m      (rows as integers, bit j = coefficient of input j)
 * Output line:  Lcyc L | cyclic witness extras | circuit witness extras   (-1 = not found with <= KMAX extras)
 *
 * Method.  T = the distinct non-unit rows.  A normalized circuit (resp. a cyclic system) with
 * |T| + k non-input elements is a set S = units + T + X with |X| = k such that the closure of the
 * units under collinear triples of S is S (resp. the collinear triples of S have rank |T| + k as
 * formal vectors).  All k-subsets X of the remaining nonzero non-unit vectors are tried, k = 0, 1, ...
 * The first k with a cyclic S gives L_cyc, the first k with a circuit S gives L.  Exhaustive, so both
 * values are exact (given k <= KMAX).
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

static int n, mt, ncand, cand[64], tgt[64];
static uint64_t UNITS, TB;
static int found_cyc, found_circ;
static int wit_cyc[16], wit_circ[16], cur[16];

static inline uint64_t xlate(uint64_t P, int v) {
    if (v & 1) P = ((P & 0x5555555555555555ULL) << 1) | ((P >> 1) & 0x5555555555555555ULL);
    if (v & 2) P = ((P & 0x3333333333333333ULL) << 2) | ((P >> 2) & 0x3333333333333333ULL);
    if (v & 4) P = ((P & 0x0F0F0F0F0F0F0F0FULL) << 4) | ((P >> 4) & 0x0F0F0F0F0F0F0F0FULL);
    if (v & 8) P = ((P & 0x00FF00FF00FF00FFULL) << 8) | ((P >> 8) & 0x00FF00FF00FF00FFULL);
    if (v & 16) P = ((P & 0x0000FFFF0000FFFFULL) << 16) | ((P >> 16) & 0x0000FFFF0000FFFFULL);
    if (v & 32) P = (P << 32) | (P >> 32);
    return P;
}

static int is_circuit(uint64_t P) {
    uint64_t C = UNITS;
    for (;;) {
        uint64_t R = P & ~C, add = 0;
        if (!R) return 1;
        while (R) {
            int v = __builtin_ctzll(R);
            R &= R - 1;
            if (C & xlate(C, v)) add |= 1ULL << v;
        }
        if (!add) return 0;
        C |= add;
    }
}

static int is_cyclic(uint64_t P, int need) {
    /* quick necessary conditions: every non-unit element lies on a collinear triple of S */
    uint64_t R = P & ~UNITS;
    int deg2 = 0;
    while (R) {
        int v = __builtin_ctzll(R);
        R &= R - 1;
        int d = __builtin_popcountll(P & xlate(P, v));
        if (d == 0) return 0;
        deg2 += d;
    }
    (void)deg2;
    uint64_t basis[64];
    memset(basis, 0, sizeof basis);
    int rank = 0;
    uint64_t A = P;
    while (A) {
        int a = __builtin_ctzll(A);
        A &= A - 1;
        uint64_t B = P & xlate(P, a) & ~((2ULL << a) - 1); /* b > a with a^b in P */
        while (B) {
            int b = __builtin_ctzll(B);
            B &= B - 1;
            int c = a ^ b;
            if (c > b) {
                uint64_t r = (1ULL << __builtin_popcountll(P & ((1ULL << a) - 1))) |
                             (1ULL << __builtin_popcountll(P & ((1ULL << b) - 1))) |
                             (1ULL << __builtin_popcountll(P & ((1ULL << c) - 1)));
                while (r) {
                    int h = 63 - __builtin_clzll(r);
                    if (!basis[h]) { basis[h] = r; rank++; break; }
                    r ^= basis[h];
                }
                if (rank == need) return 1;
            }
        }
    }
    return rank == need;
}

static void rec(int start, int left, int k, uint64_t P) {
    if (found_circ) return;
    if (left == 0) {
        if (!found_cyc && is_cyclic(P, mt + k)) {
            found_cyc = 1;
            memcpy(wit_cyc, cur, sizeof cur);
        }
        if (is_circuit(P)) {
            found_circ = 1;
            memcpy(wit_circ, cur, sizeof cur);
        }
        return;
    }
    for (int i = start; i <= ncand - left; i++) {
        cur[k - left] = cand[i];
        rec(i + 1, left - 1, k, P | (1ULL << cand[i]));
        if (found_circ) return;
    }
}

static void pr(int v) { for (int j = 0; j < n; j++) putchar(((v >> j) & 1) ? '1' : '0'); }

int main(int argc, char **argv) {
    int kmax = argc > 1 ? atoi(argv[1]) : 6;
    int m;
    while (scanf("%d %d", &n, &m) == 2) {
        uint64_t seen = 0;
        mt = 0;
        UNITS = 0;
        for (int j = 0; j < n; j++) UNITS |= 1ULL << (1 << j);
        for (int i = 0; i < m; i++) {
            int r;
            if (scanf("%d", &r) != 1) return 1;
            if (r == 0 || (r & (r - 1)) == 0) continue; /* zero or unit row: free */
            if ((seen >> r) & 1ULL) continue;
            seen |= 1ULL << r;
            tgt[mt++] = r;
        }
        TB = seen;
        ncand = 0;
        for (int v = 1; v < (1 << n); v++)
            if ((v & (v - 1)) && !((seen >> v) & 1ULL)) cand[ncand++] = v;
        int Lcyc = -1, L = -1, kc = -1, kl = -1;
        found_cyc = found_circ = 0;
        for (int k = 0; k <= kmax && !found_circ; k++) {
            int had = found_cyc;
            rec(0, k, k, UNITS | TB);
            if (found_cyc && !had) { Lcyc = mt + k; kc = k; }
            if (found_circ) { L = mt + k; kl = k; }
        }
        printf("%d %d |", Lcyc, L);
        for (int i = 0; i < kc; i++) { putchar(' '); pr(wit_cyc[i]); }
        printf(" |");
        for (int i = 0; i < kl; i++) { putchar(' '); pr(wit_circ[i]); }
        printf("\n");
        fflush(stdout);
    }
    return 0;
}
