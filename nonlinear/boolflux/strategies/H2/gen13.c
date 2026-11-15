/* General exact last-layer search: K members whose span contains T_full  <=>  their images in
   V / T_full lie in a (K-8)-dim subspace W' (and the preimages have rank K; checked in Python).
   Input (stdin): n q, then n lines "hi lo" = image of member i in V/T_full (u128, T_full-reduced).
   Method: seeds = consistent quadrangles img1+img2 = img3+img4 (4 distinct images spanning a
   3-dim B0); then extend one dimension at a time; at each step only extensions reaching the
   averaging bound  w(B_{k+1}) >= w(B_k) + ceil((K - w(B_k)) / (2^{D-k} - 1))  are kept (valid:
   the 2^{D-k}-1 subspaces of dim k+1 between B_k and W' partition W' \ B_k).
   Completeness: every solution whose images have >= 9 distinct nonzero points (K = 13; >= 12 for
   K = 14) contains a quadrangle (C(s,2) > 2^D - 1 pair sums), hence is found.
   Output: "SOL w m1 m2 ..." = all members with image in W' (deduplicated by W').  */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
typedef unsigned __int128 u128;
static int n, q, K, D;
static u128 *im;
static long nseeds = 0, nsol = 0, nodes = 0;
static int hib(u128 v) { int h = 127; while (h >= 0 && !((v >> h) & 1)) h--; return h; }
typedef struct { u128 b[16]; int p[16]; int d; } Sp;
static u128 red(const Sp *S, u128 v) { for (int i = 0; i < S->d; i++) if ((v >> S->p[i]) & 1) v ^= S->b[i]; return v; }
static int addv(Sp *S, u128 v) {
    v = red(S, v); if (!v) return 0;
    int h = hib(v);
    for (int i = 0; i < S->d; i++) if ((S->b[i] >> h) & 1) S->b[i] ^= v;
    S->b[S->d] = v; S->p[S->d] = h; S->d++; return 1;
}
#define HS (1 << 23)
static u128 *seenk;
static int seen_sp(const Sp *S) {
    /* canonical: fully reduced basis sorted by pivot -> hash */
    u128 bs[16]; int d = S->d;
    for (int i = 0; i < d; i++) bs[i] = S->b[i];
    /* sort by pivot */
    for (int i = 0; i < d; i++) for (int j = i + 1; j < d; j++) if (hib(bs[j]) > hib(bs[i])) { u128 t = bs[i]; bs[i] = bs[j]; bs[j] = t; }
    u128 h = (u128)0x9E3779B97F4A7C15ULL * (d + 1);
    for (int i = 0; i < d; i++) { h ^= bs[i]; h *= (u128)0x100000001B3ULL; h ^= h >> 61; }
    h |= 1;
    size_t k = (size_t)(h ^ (h >> 64)) & (HS - 1);
    while (seenk[k]) { if (seenk[k] == h) return 1; k = (k + 1) & (HS - 1); }
    seenk[k] = h; return 0;
}
static u128 *rr;  /* scratch: residues */
static void extend(const Sp *B, int w) {
    nodes++;
    int k = B->d;
    if (k == D) {
        if (w >= K) {
            nsol++;
            printf("SOL %d", w);
            for (int m = 0; m < n; m++) if (red(B, im[m]) == 0) printf(" %d", m);
            printf("\n"); fflush(stdout);
        }
        return;
    }
    long parts = (1L << (D - k)) - 1;
    int need = w + (int)((K - w + parts - 1) / parts);
    /* residues of all members mod B; count by residue with an open-addressing table */
    static u128 *hk = 0; static int *hc = 0, *hm = 0; static int HSZ = 0;
    if (!hk) { HSZ = 1; while (HSZ < 2 * n) HSZ <<= 1; int ns = D > 3 ? D - 2 : 1; hk = malloc(sizeof(u128) * HSZ * ns); hc = calloc((size_t)HSZ * ns, sizeof(int)); hm = malloc(sizeof(int) * HSZ * ns); }
    u128 *K_ = hk + (size_t)HSZ * (k - 3); int *C_ = hc + (size_t)HSZ * (k - 3); int *M_ = hm + (size_t)HSZ * (k - 3);
    int *used = malloc(sizeof(int) * n); int nu = 0;
    for (int m = 0; m < n; m++) {
        u128 v = red(B, im[m]); if (!v) continue;
        u128 h = v * (u128)0x9E3779B97F4A7C15ULL; size_t s2 = (size_t)((h >> 64) ^ h) & (HSZ - 1);
        while (C_[s2] && K_[s2] != v) s2 = (s2 + 1) & (HSZ - 1);
        if (!C_[s2]) { K_[s2] = v; M_[s2] = m; used[nu++] = (int)s2; }
        C_[s2]++;
    }
    for (int t = 0; t < nu; t++) {
        int s2 = used[t];
        if (w + C_[s2] >= need) {
            Sp B2 = *B; addv(&B2, im[M_[s2]]);
            int cnt = C_[s2];
            if (!seen_sp(&B2)) extend(&B2, w + cnt);
        }
    }
    for (int t = 0; t < nu; t++) C_[used[t]] = 0;
    free(used);
}
static int *clsg;
int cmpcls(const void *a, const void *b) { return clsg[*(const int *)a] - clsg[*(const int *)b]; }
int cmpres(const void *a, const void *b) {
    u128 x = rr[*(const int *)a], y = rr[*(const int *)b];
    return x < y ? -1 : x > y ? 1 : 0;
}
int main(int argc, char **argv) {
    K = argc > 1 ? atoi(argv[1]) : 13; D = K - 8;
    int n0arg = argc > 2 ? atoi(argv[2]) : 0;
    int *cls = 0;
    if (scanf("%d %d", &n, &q) != 2) return 1;
    im = malloc(sizeof(u128) * n);
    for (int i = 0; i < n; i++) { unsigned long long hi, lo; if (scanf("%llx %llx", &hi, &lo) != 2) return 1; im[i] = ((u128)hi << 64) | lo; }
    seenk = calloc(HS, sizeof(u128));
    if (argc > 3) { FILE *cf = fopen(argv[3], "r"); cls = malloc(sizeof(int) * n); for (int i = 0; i < n; i++) if (fscanf(cf, "%d", &cls[i]) != 1) cls[i] = -1; fclose(cf); n0arg = n; }
    /* pairs hashed by image sum */
    int n0 = (n0arg > 0 && n0arg < n) ? n0arg : n;
    long np = 0; long cap = (long)n0 * (n0 - 1) / 2;
    int *ordc = 0;
    if (cls) {
        ordc = malloc(sizeof(int) * n); for (int i = 0; i < n; i++) ordc[i] = i;
        clsg = cls; qsort(ordc, n, sizeof(int), cmpcls);
        cap = 0;
        for (int i = 0; i < n; ) { int j = i; while (j < n && cls[ordc[j]] == cls[ordc[i]]) j++;
            if (cls[ordc[i]] >= 0) cap += (long)(j - i) * (j - i - 1) / 2; i = j; }
    }
    u128 *ps = malloc(sizeof(u128) * cap); int *pa = malloc(sizeof(int) * cap), *pb = malloc(sizeof(int) * cap);
    long gi = 0, gj = 0, gend = 0; int pa_i = 0, pb_i = 0;
    for (int a = 0; a < n0; a++) for (int b = a + 1; b < n0; b++) {
        if (cls) break;
        if (im[a] == im[b] || !im[a] || !im[b]) continue;
        ps[np] = im[a] ^ im[b]; pa[np] = a; pb[np] = b; np++;
    }
    if (cls) {
        for (int i = 0; i < n; ) { int j = i; while (j < n && cls[ordc[j]] == cls[ordc[i]]) j++;
            if (cls[ordc[i]] >= 0)
                for (int u = i; u < j; u++) for (int t = u + 1; t < j; t++) {
                    int a = ordc[u], b = ordc[t];
                    if (im[a] == im[b] || !im[a] || !im[b]) continue;
                    ps[np] = im[a] ^ im[b]; pa[np] = a; pb[np] = b; np++;
                }
            i = j; }
    }
    fprintf(stderr, "pairs %ld\n", np);
    long HB = 1L << 22; long *bh = malloc(sizeof(long) * HB), *bn = malloc(sizeof(long) * np);
    for (long i = 0; i < HB; i++) bh[i] = -1;
    for (long i = 0; i < np; i++) { u128 h = ps[i] * (u128)0x9E3779B97F4A7C15ULL; long s = (long)((h ^ (h >> 64) ^ (h >> 23)) & (HB - 1)); bn[i] = bh[s]; bh[s] = i; }
    for (long s = 0; s < HB; s++) for (long i = bh[s]; i >= 0; i = bn[i]) for (long j = bn[i]; j >= 0; j = bn[j]) {
        if (ps[i] != ps[j]) continue;
        int a = pa[i], b = pb[i], c = pa[j], d = pb[j];
        if (im[a] == im[c] || im[a] == im[d] || im[b] == im[c] || im[b] == im[d]) continue;
        Sp B0; B0.d = 0; addv(&B0, im[a]); addv(&B0, im[b]); addv(&B0, im[c]);
        if (B0.d != 3) continue;
        nseeds++;
        if (seen_sp(&B0)) continue;
        int w = 0; for (int m = 0; m < n; m++) if (red(&B0, im[m]) == 0) w++;
        extend(&B0, w);
        if ((nseeds & 0x3FFFF) == 0) fprintf(stderr, "seeds %ld nodes %ld sols %ld\n", nseeds, nodes, nsol);
    }
    fprintf(stderr, "done K=%d seeds %ld nodes %ld sols %ld\n", K, nseeds, nodes, nsol);
    return 0;
}
