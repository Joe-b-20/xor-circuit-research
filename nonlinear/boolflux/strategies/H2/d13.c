/* Exact search for 13 bilinearly independent members forming a last layer (see d13prep.py).
   Input: n q, then n lines "b jhi jlo".  Finds 5-dim W <= F_2^8 and linear phi: W -> J with
   >= NEED consistent members (j_m = phi(b_m)), via seeds (consistent lines / quadrangles spanning a
   3-dim B0 with >= 4 consistent points), then B1 (4-dim, >= 7), then W (5-dim, >= NEED).
   Correctness of the chain: a NEED=13 set in PG(4,2) has a hyperplane with >= 7 points, which has
   a plane with >= 4 points; 4 points of PG(2,2) contain a line or are a quadrangle (sum 0).
   Output: "SOL" lines with member indices (deduplicated by (W, phi) hash).  */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
typedef unsigned __int128 u128;
static int n, q, NEED = 13;
static int *bv; static u128 *jv;
static int head[256], nxt[4096];       /* members by b */
static long nlines = 0, nquads = 0, nb0 = 0, nb1 = 0, nsol = 0;
/* phi table on current subspace: val[b] valid if inB[b] */
typedef struct { int pts[32]; int np; u128 val[256]; unsigned char in[256]; } Sub;

static void sub_init(Sub *S) { memset(S->in, 0, 256); S->np = 0; S->in[0] = 1; S->val[0] = 0; }
/* add direction b with value v (b not in S) */
static void sub_add(Sub *S, const Sub *P, int b, u128 v) {
    *S = *P;
    int cur[32]; int nc = 0; cur[nc++] = 0;
    for (int i = 0; i < P->np; i++) cur[nc++] = P->pts[i];
    for (int i = 0; i < nc; i++) {
        int p = cur[i] ^ b; S->in[p] = 1; S->val[p] = P->val[cur[i]] ^ v; S->pts[S->np++] = p;
    }
}
static int count_cons(const Sub *S, int *list) {
    int c = 0;
    for (int i = 0; i < S->np; i++) {
        int p = S->pts[i];
        for (int m = head[p]; m >= 0; m = nxt[m]) if (jv[m] == S->val[p]) { if (list) list[c] = m; c++; }
    }
    return c;
}
#define HS (1 << 22)
static unsigned long long seenh[HS];
static int seen_check(const Sub *S) {
    /* hash of (set of points, values) */
    unsigned long long h = 1469598103934665603ULL;
    for (int p = 1; p < 256; p++) if (S->in[p]) {
        h ^= (unsigned long long)p; h *= 1099511628211ULL;
        h ^= (unsigned long long)(S->val[p] & 0xffffffffffffffffULL); h *= 1099511628211ULL;
        h ^= (unsigned long long)(S->val[p] >> 64); h *= 1099511628211ULL;
    }
    unsigned long long k = h | 1; size_t i = h & (HS - 1);
    while (seenh[i]) { if (seenh[i] == k) return 1; i = (i + 1) & (HS - 1); }
    seenh[i] = k; return 0;
}
static void extend_W(const Sub *B1) {
    for (int m = 0; m < n; m++) {
        int b = bv[m]; if (B1->in[b]) continue;
        Sub W; sub_add(&W, B1, b, jv[m]);
        int c = count_cons(&W, NULL);
        if (c >= NEED) {
            if (seen_check(&W)) continue;
            nsol++;
            printf("SOL %d", c);
            for (int i = 0; i < W.np; i++) { int p = W.pts[i];
                for (int mm = head[p]; mm >= 0; mm = nxt[mm]) if (jv[mm] == W.val[p]) printf(" %d", mm); }
            printf("\n"); fflush(stdout);
        }
    }
}
static void extend_B1(const Sub *B0) {
    nb0++;
    for (int m = 0; m < n; m++) {
        int b = bv[m]; if (B0->in[b]) continue;
        Sub B1; sub_add(&B1, B0, b, jv[m]);
        if (count_cons(&B1, NULL) >= 7) { nb1++; extend_W(&B1); }
    }
}
static int idx_bj(int b, u128 j) { for (int m = head[b]; m >= 0; m = nxt[m]) if (jv[m] == j) return m; return -1; }

int main(int argc, char **argv) {
    if (argc > 1) NEED = atoi(argv[1]);
    if (scanf("%d %d", &n, &q) != 2) return 1;
    bv = malloc(sizeof(int) * n); jv = malloc(sizeof(u128) * n);
    for (int i = 0; i < 256; i++) head[i] = -1;
    for (int i = 0; i < n; i++) {
        unsigned long long hi, lo; if (scanf("%d %llx %llx", &bv[i], &hi, &lo) != 3) return 1;
        jv[i] = ((u128)hi << 64) | lo;
    }
    for (int i = n - 1; i >= 0; i--) { nxt[i] = head[bv[i]]; head[bv[i]] = i; }
    Sub E; sub_init(&E);
    if (argc > 2) { /* line seeds disabled: quadrangles suffice (>= 47 per 13-set) */ }
    fprintf(stderr, "lines %ld, B0 from lines %ld, B1 %ld, sols %ld\n", nlines, nb0, nb1, nsol);
    /* quadrangle seeds: pairs with equal (b1^b2, j1^j2) */
    {
        long np = (long)n * (n - 1) / 2;
        typedef struct { int b; u128 j; int m1, m2; } P;
        P *ps = malloc(sizeof(P) * np); long k = 0;
        for (int m1 = 0; m1 < n; m1++) for (int m2 = m1 + 1; m2 < n; m2++) {
            if (bv[m1] == bv[m2]) continue;
            ps[k].b = bv[m1] ^ bv[m2]; ps[k].j = jv[m1] ^ jv[m2]; ps[k].m1 = m1; ps[k].m2 = m2; k++;
        }
        /* hash buckets */
        long HB = 1 << 21; long *bh = malloc(sizeof(long) * HB); long *bn = malloc(sizeof(long) * k);
        for (long i = 0; i < HB; i++) bh[i] = -1;
        for (long i = 0; i < k; i++) {
            unsigned long long h = (unsigned long long)ps[i].b * 0x9E3779B97F4A7C15ULL ^ (unsigned long long)ps[i].j ^ (unsigned long long)(ps[i].j >> 64) * 0xC2B2AE3D27D4EB4FULL;
            long s = h & (HB - 1); bn[i] = bh[s]; bh[s] = i;
        }
        for (long s = 0; s < HB; s++) for (long i = bh[s]; i >= 0; i = bn[i]) for (long i2 = bn[i]; i2 >= 0; i2 = bn[i2]) {
            if (ps[i].b != ps[i2].b || ps[i].j != ps[i2].j) continue;
            int a = ps[i].m1, b = ps[i].m2, c = ps[i2].m1, d = ps[i2].m2;
            if (bv[a] == bv[c] || bv[a] == bv[d] || bv[b] == bv[c] || bv[b] == bv[d]) continue;
            Sub A, L, B0; sub_add(&A, &E, bv[a], jv[a]); sub_add(&L, &A, bv[b], jv[b]);
            if (L.in[bv[c]]) continue;     /* would be a line case */
            sub_add(&B0, &L, bv[c], jv[c]);
            if (!B0.in[bv[d]] || B0.val[bv[d]] != jv[d]) continue;
            nquads++;
            if ((nquads & 0xFFFF) == 0) fprintf(stderr, "quads %ld B0 %ld B1 %ld sols %ld\n", nquads, nb0, nb1, nsol);
            if (seen_check(&B0)) continue;
            extend_B1(&B0);
        }
    }
    fprintf(stderr, "quads %ld, B0 total %ld, B1 %ld, sols %ld\n", nquads, nb0, nb1, nsol);
    return 0;
}
