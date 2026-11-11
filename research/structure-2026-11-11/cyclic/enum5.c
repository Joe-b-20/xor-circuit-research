/* enum5.c -- complete classification of 5-input target sets: circuits versus cyclic systems.
 *
 * Usage:  gcc -O2 -fopenmp -o enum5 enum5.c && OMP_NUM_THREADS=4 ./enum5 [n5_noncircuit_small.txt]
 *
 * Points: the 26 nonzero vectors of F_2^5 that are not unit vectors.  For every subset X of them
 * (2^26 subsets) let S = units + X.
 *   circuit set : the closure of the unit vectors under "two points of a collinear triple of S are
 *                 in, so the third is in" is all of S   (S is the mask set of a circuit with |X| gates)
 *   cyclic set  : the collinear triples of S span the whole relation space of S, i.e. their rank as
 *                 formal vectors over S is |S| - 5 = |X|
 * Then, by a superset-minimum transform,
 *   L(M)     = least |X| over circuit sets X containing M
 *   L_cyc(M) = least |X| over cyclic  sets X containing M
 * for EVERY set M of non-unit target vectors in F_2^5 at once.  Everything is exhaustive.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

#define NP 26
#define NSUB (1u << NP)
#define UNITS ((1u << 1) | (1u << 2) | (1u << 4) | (1u << 8) | (1u << 16))

static int pt[NP];          /* index -> vector */
static int idxOf[32];       /* vector -> index, -1 for units and 0 */
static uint32_t tabLo[1 << 13], tabHi[1 << 13];

static inline uint32_t bitmap_of(uint32_t X) { return UNITS | tabLo[X & 8191u] | tabHi[X >> 13]; }

static inline int is_circuit(uint32_t P) {
    uint32_t C = UNITS, F = UNITS;
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

static inline int tri_rank(uint32_t P) {
    int pos[32];
    int n = 0;
    uint32_t T = P;
    while (T) { int v = __builtin_ctz(T); T &= T - 1; pos[v] = n++; }
    uint32_t basis[32];
    memset(basis, 0, sizeof basis);
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
                uint32_t r = (1u << pos[a]) | (1u << pos[b]) | (1u << pos[c]);
                while (r) {
                    int h = 31 - __builtin_clz(r);
                    if (!basis[h]) { basis[h] = r; rank++; break; }
                    r ^= basis[h];
                }
            }
        }
    }
    return rank;
}

static void print_set(FILE *f, uint32_t X) {
    int first = 1;
    for (int i = 0; i < NP; i++)
        if ((X >> i) & 1u) {
            int v = pt[i];
            fprintf(f, "%s", first ? "" : " ");
            for (int j = 0; j < 5; j++) fputc(((v >> j) & 1) ? '1' : '0', f);
            first = 0;
        }
}

static uint32_t mask_of_rows(const int *rows, int m) { /* non-unit rows only */
    uint32_t X = 0;
    for (int i = 0; i < m; i++)
        if (idxOf[rows[i]] >= 0) X |= 1u << idxOf[rows[i]];
    return X;
}

static int invert5(const int *rows, int *inv) { /* rows: 5 masks; returns 0 if singular */
    int a[5], b[5];
    for (int i = 0; i < 5; i++) { a[i] = rows[i]; b[i] = 1 << i; }
    for (int col = 0; col < 5; col++) {
        int p = -1;
        for (int i = col; i < 5; i++) if ((a[i] >> col) & 1) { p = i; break; }
        if (p < 0) return 0;
        int t = a[p]; a[p] = a[col]; a[col] = t;
        t = b[p]; b[p] = b[col]; b[col] = t;
        for (int i = 0; i < 5; i++)
            if (i != col && ((a[i] >> col) & 1)) { a[i] ^= a[col]; b[i] ^= b[col]; }
    }
    /* now a = I and b = A^{-1} in the sense row_i(b) * A = e_i */
    for (int i = 0; i < 5; i++) inv[i] = b[i];
    return 1;
}

int main(int argc, char **argv) {
    int np = 0;
    for (int v = 0; v < 32; v++) idxOf[v] = -1;
    for (int v = 1; v < 32; v++)
        if (__builtin_popcount(v) >= 2) { pt[np] = v; idxOf[v] = np; np++; }
    if (np != NP) return 1;
    for (uint32_t h = 0; h < (1u << 13); h++) {
        uint32_t lo = 0, hi = 0;
        for (int i = 0; i < 13; i++)
            if ((h >> i) & 1u) { lo |= 1u << pt[i]; hi |= 1u << pt[13 + i]; }
        tabLo[h] = lo;
        tabHi[h] = hi;
    }
    uint8_t *circ = malloc(NSUB), *cyc = malloc(NSUB);
    uint8_t *rawcirc = malloc(NSUB), *rawcyc = malloc(NSUB);
    if (!circ || !cyc || !rawcirc || !rawcyc) return 2;

    long long ncirc[NP + 1], ncyc[NP + 1];
    memset(ncirc, 0, sizeof ncirc);
    memset(ncyc, 0, sizeof ncyc);
#pragma omp parallel
    {
        long long lc[NP + 1], ly[NP + 1];
        memset(lc, 0, sizeof lc);
        memset(ly, 0, sizeof ly);
#pragma omp for schedule(dynamic, 65536)
        for (uint32_t X = 0; X < NSUB; X++) {
            uint32_t P = bitmap_of(X);
            int k = __builtin_popcount(X);
            int c = is_circuit(P);
            int y = c ? 1 : (tri_rank(P) == k);
            circ[X] = c ? (uint8_t)k : 255;
            cyc[X] = y ? (uint8_t)k : 255;
            if (c) lc[k]++;
            if (y) ly[k]++;
        }
#pragma omp critical
        for (int k = 0; k <= NP; k++) { ncirc[k] += lc[k]; ncyc[k] += ly[k]; }
    }
    memcpy(rawcirc, circ, NSUB);
    memcpy(rawcyc, cyc, NSUB);

    printf("== sets S = units + X in F_2^5, by size |X| ==\n");
    printf("size  circuit_sets  cyclic_sets  cyclic_not_circuit\n");
    long long tc = 0, ty = 0;
    for (int k = 0; k <= NP; k++) {
        printf("%4d  %12lld  %11lld  %18lld\n", k, ncirc[k], ncyc[k], ncyc[k] - ncirc[k]);
        tc += ncirc[k];
        ty += ncyc[k];
    }
    printf("total %12lld  %11lld  %18lld\n", tc, ty, ty - tc);

    if (argc > 1) {
        FILE *f = fopen(argv[1], "w");
        long long cnt = 0;
        for (uint32_t X = 0; X < NSUB; X++)
            if (rawcyc[X] != 255 && rawcirc[X] == 255 && __builtin_popcount(X) <= 7) {
                fprintf(f, "%d %u : ", __builtin_popcount(X), X);
                print_set(f, X);
                fputc('\n', f);
                cnt++;
            }
        fclose(f);
        printf("wrote %lld non-circuit cyclic sets of size <= 7 to %s\n", cnt, argv[1]);
    }

    /* superset-minimum transforms */
    for (int b = 0; b < NP; b++) {
        uint32_t bit = 1u << b;
#pragma omp parallel for schedule(static)
        for (uint32_t X = 0; X < NSUB; X++)
            if (!(X & bit)) {
                if (circ[X | bit] < circ[X]) circ[X] = circ[X | bit];
                if (cyc[X | bit] < cyc[X]) cyc[X] = cyc[X | bit];
            }
    }

    /* all target sets M */
    static long long hist[NP + 1][NP + 1][NP + 1];
    long long bad = 0, ngap = 0;
    int maxgap = 0;
    for (uint32_t M = 0; M < NSUB; M++) {
        int m = __builtin_popcount(M), fc = cyc[M], fl = circ[M];
        if (fc > fl) bad++;
        if (fc < fl) { hist[m][fc][fl]++; ngap++; if (fl - fc > maxgap) maxgap = fl - fc; }
    }
    printf("\n== all 2^26 target sets M of non-unit vectors in F_2^5 ==\n");
    printf("sets with L_cyc > L (must be 0): %lld\n", bad);
    printf("sets with L_cyc < L: %lld   largest gap L - L_cyc: %d\n", ngap, maxgap);
    printf("rows  L_cyc  L  count\n");
    int minm = -1;
    for (int m = 0; m <= NP; m++)
        for (int a = 0; a <= NP; a++)
            for (int b = 0; b <= NP; b++)
                if (hist[m][a][b]) {
                    printf("%4d  %5d  %2d  %lld\n", m, a, b, hist[m][a][b]);
                    if (minm < 0) minm = m;
                }
    if (minm >= 0) {
        printf("\nexamples with the fewest rows (%d), first 6, each with one cyclic witness S:\n", minm);
        int shown = 0;
        for (uint32_t M = 0; M < NSUB && shown < 6; M++) {
            if (__builtin_popcount(M) != minm || cyc[M] >= circ[M]) continue;
            printf("  M = { "); print_set(stdout, M);
            printf(" }  L_cyc=%d L=%d\n", cyc[M], circ[M]);
            for (uint32_t X = 0; X < NSUB; X++)
                if ((X & M) == M && rawcyc[X] == cyc[M]) {
                    printf("     S\\units = { "); print_set(stdout, X); printf(" }\n");
                    break;
                }
            shown++;
        }
    }

    /* invertible 5x5 matrices, as row sets (row order does not matter for L or L_cyc) */
    long long nb = 0, d_inv_cyc = 0, d_tr_cyc = 0, d_tr_circ = 0, d_inv_circ = 0, gapinv = 0;
    long long nfl = 0, gapfl = 0, d_inv_fl = 0;
    static long long pairh[NP + 1][NP + 1];
    static long long flh[NP + 1][NP + 1][NP + 1];
    int rows[5], inv[5], tr[5];
    int shown_inv = 0, shown_gap = 0;
    for (rows[0] = 1; rows[0] < 32; rows[0]++)
    for (rows[1] = rows[0] + 1; rows[1] < 32; rows[1]++)
    for (rows[2] = rows[1] + 1; rows[2] < 32; rows[2]++)
    for (rows[3] = rows[2] + 1; rows[3] < 32; rows[3]++)
    for (rows[4] = rows[3] + 1; rows[4] < 32; rows[4]++) {
        if (!invert5(rows, inv)) continue;
        nb++;
        for (int j = 0; j < 5; j++) {
            tr[j] = 0;
            for (int i = 0; i < 5; i++) tr[j] |= ((rows[i] >> j) & 1) << i;
        }
        uint32_t MA = mask_of_rows(rows, 5), MI = mask_of_rows(inv, 5), MT = mask_of_rows(tr, 5);
        if (cyc[MA] != cyc[MI]) d_inv_cyc++;
        if (cyc[MA] != cyc[MT]) d_tr_cyc++;
        if (circ[MA] != circ[MT]) d_tr_circ++;
        if (circ[MA] != circ[MI]) {
            d_inv_circ++;
            if (shown_inv < 3 && circ[MA] < circ[MI] && circ[MI] <= 8) {
                printf("\n  invertible A with L(A)=%d, L(A^-1)=%d, L_cyc=%d: rows ", circ[MA], circ[MI], cyc[MA]);
                for (int i = 0; i < 5; i++) { for (int j = 0; j < 5; j++) putchar(((rows[i] >> j) & 1) ? '1' : '0'); putchar(' '); }
                printf("| inverse rows ");
                for (int i = 0; i < 5; i++) { for (int j = 0; j < 5; j++) putchar(((inv[i] >> j) & 1) ? '1' : '0'); putchar(' '); }
                printf("\n");
                shown_inv++;
            }
        }
        pairh[circ[MA]][circ[MI]]++;
        if (cyc[MA] < circ[MA]) {
            gapinv++;
            if (shown_gap < 3) {
                printf("\n  invertible A with L_cyc=%d < L=%d (L(A^-1)=%d): rows ", cyc[MA], circ[MA], circ[MI]);
                for (int i = 0; i < 5; i++) { for (int j = 0; j < 5; j++) putchar(((rows[i] >> j) & 1) ? '1' : '0'); putchar(' '); }
                printf("\n");
                shown_gap++;
            }
        }
        /* flavour: every row and every column of odd weight, no unit row */
        int ok = 1;
        for (int i = 0; i < 5; i++) {
            if (!(__builtin_popcount(rows[i]) & 1) || __builtin_popcount(rows[i]) < 3) ok = 0;
            if (!(__builtin_popcount(tr[i]) & 1)) ok = 0;
        }
        if (ok) {
            nfl++;
            flh[cyc[MA]][circ[MA]][circ[MI]]++;
            if (cyc[MA] < circ[MA]) gapfl++;
            if (circ[MA] != circ[MI]) d_inv_fl++;
        }
    }
    printf("\n== invertible 5x5 matrices up to row order: %lld ==\n", nb);
    printf("L_cyc(A) != L_cyc(A^-1): %lld (theorem: 0)\n", d_inv_cyc);
    printf("L_cyc(A) != L_cyc(A^T) : %lld (theorem: 0)\n", d_tr_cyc);
    printf("L(A) != L(A^T)         : %lld (transposition principle: 0)\n", d_tr_circ);
    printf("L(A) != L(A^-1)        : %lld\n", d_inv_circ);
    printf("L_cyc(A) < L(A)        : %lld\n", gapinv);
    printf("histogram  L(A)  L(A^-1)  count\n");
    for (int a = 0; a <= NP; a++)
        for (int b = 0; b <= NP; b++)
            if (pairh[a][b]) printf("           %4d  %7d  %lld\n", a, b, pairh[a][b]);
    printf("\n== flavour: invertible, all rows and columns of odd weight, rows of weight >= 3: %lld ==\n", nfl);
    printf("with L_cyc < L: %lld ; with L(A) != L(A^-1): %lld\n", gapfl, d_inv_fl);
    printf("histogram  L_cyc  L(A)  L(A^-1)  count\n");
    for (int c = 0; c <= NP; c++)
        for (int a = 0; a <= NP; a++)
            for (int b = 0; b <= NP; b++)
                if (flh[c][a][b]) printf("           %5d  %4d  %7d  %lld\n", c, a, b, flh[c][a][b]);
    return 0;
}
