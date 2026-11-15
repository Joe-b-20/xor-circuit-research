/* Exact small-cover enumeration.
   Input (stdin): n t K maxsol
                  t target vectors (hex, already reduced mod the free space, independent)
                  n candidate vectors (hex, reduced mod free space)
   Vectors are up to 128 bits (two hex words: hi lo).
   Output: every candidate subset X (|X| = K, independent) whose span contains the targets, found as
   S = T + W, W spanned by e = K - t candidate images mod T, S spanned by candidates inside S.
   Prints "SOL i1 i2 ... iK" (a basis of S drawn from candidates) for each distinct S.
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

typedef unsigned __int128 u128;
static int n, t, K, maxsol;
static u128 *cand, *img, tgt[64];
static u128 tb[128]; static int tbp[128]; static int nt = 0;  /* echelon basis of T */

static int hibit(u128 v) { int h = 127; while (h >= 0 && !((v >> h) & 1)) h--; return h; }
static u128 redT(u128 v) {
    for (int i = 0; i < nt; i++) if ((v >> tbp[i]) & 1) v ^= tb[i];
    return v;
}
static void addT(u128 v) {
    v = redT(v); if (!v) return;
    int h = hibit(v);
    for (int i = 0; i < nt; i++) if ((tb[i] >> h) & 1) tb[i] ^= v;
    tb[nt] = v; tbp[nt] = h; nt++;
}
static u128 rd(u128 v) {
    unsigned long long hi, lo;
    if (scanf("%llx %llx", &hi, &lo) != 2) { fprintf(stderr, "read error\n"); exit(1); }
    v = ((u128)hi << 64) | lo; return v;
}

/* W echelon (on images) */
static u128 wb[16]; static int wbp[16]; static int nw = 0;
static int sel[16]; static long nsol = 0; static long tested = 0;

static u128 redW(u128 v) { for (int i = 0; i < nw; i++) if ((v >> wbp[i]) & 1) v ^= wb[i]; return v; }

static void test(void) {
    tested++;
    /* candidates with image in W */
    u128 sb[160]; int sbp[160]; int ns = 0; int chosen[160]; int nc = 0;
    for (int i = 0; i < n; i++) {
        if (redW(img[i]) != 0) continue;
        u128 v = cand[i];
        for (int j = 0; j < ns; j++) if ((v >> sbp[j]) & 1) v ^= sb[j];
        if (!v) continue;
        int h = hibit(v);
        for (int j = 0; j < ns; j++) if ((sb[j] >> h) & 1) sb[j] ^= v;
        sb[ns] = v; sbp[ns] = h; ns++; chosen[nc++] = i;
        if (ns > K) break;
    }
    if (ns == K) {
        /* T inside? guaranteed if rank = t + e and all images in W, but check */
        for (int a = 0; a < t; a++) {
            u128 v = tgt[a];
            for (int j = 0; j < ns; j++) if ((v >> sbp[j]) & 1) v ^= sb[j];
            if (v) return;
        }
        nsol++;
        printf("SOL");
        for (int j = 0; j < nc; j++) printf(" %d", chosen[j]);
        printf("\n");
        if (maxsol && nsol >= maxsol) { fflush(stdout); exit(0); }
    }
}

/* greedy-basis check: sel[0..d-1] must be the index-order greedy basis of the span of their images */
static int greedy_ok(int d) {
    u128 gb[16]; int gp[16]; int ng = 0; int q = 0;
    int last = sel[d - 1];
    for (int j = 0; j <= last; j++) {
        u128 v = img[j];
        for (int a = 0; a < ng; a++) if ((v >> gp[a]) & 1) v ^= gb[a];
        int is_sel = (q < d && sel[q] == j);
        if (is_sel) {
            if (!v) return 0;
            int h = hibit(v);
            for (int a = 0; a < ng; a++) if ((gb[a] >> h) & 1) gb[a] ^= v;
            gb[ng] = v; gp[ng] = h; ng++; q++;
        } else if (v) {
            /* not in span of earlier selected: is it in span of ALL selected (prefix)? then not greedy */
            u128 r = v;
            for (int a = q; a < d; a++) { /* reduce by later selected images */ }
            u128 full = img[j];
            u128 fb[16]; int fp[16]; int nf = 0;
            for (int a = 0; a < d; a++) {
                u128 x = img[sel[a]];
                for (int b = 0; b < nf; b++) if ((x >> fp[b]) & 1) x ^= fb[b];
                int h = hibit(x);
                for (int b = 0; b < nf; b++) if ((fb[b] >> h) & 1) fb[b] ^= x;
                fb[nf] = x; fp[nf] = h; nf++;
            }
            for (int b = 0; b < nf; b++) if ((full >> fp[b]) & 1) full ^= fb[b];
            if (!full) return 0;
            (void)r;
        }
    }
    return 1;
}

static void rec(int start, int depth, int e) {
    if (depth == e) {
        /* full greedy check against W: every candidate index < sel[e-1] already checked; indices
           beyond the last selected are irrelevant for greedy-ness */
        test(); return;
    }
    for (int i = start; i < n; i++) {
        u128 v = redW(img[i]);
        if (!v) continue;
        int h = hibit(v);
        u128 saved[16]; int savedp[16];
        for (int j = 0; j < nw; j++) { saved[j] = wb[j]; savedp[j] = wbp[j]; }
        for (int j = 0; j < nw; j++) if ((wb[j] >> h) & 1) wb[j] ^= v;
        wb[nw] = v; wbp[nw] = h; nw++;
        sel[depth] = i;
        if (greedy_ok(depth + 1)) rec(i + 1, depth + 1, e);
        nw--; for (int j = 0; j < nw; j++) { wb[j] = saved[j]; wbp[j] = savedp[j]; }
    }
}

int main(void) {
    if (scanf("%d %d %d %d", &n, &t, &K, &maxsol) != 4) return 1;
    for (int i = 0; i < t; i++) { tgt[i] = rd(0); addT(tgt[i]); }
    if (nt != t) { fprintf(stderr, "targets dependent\n"); }
    cand = malloc(sizeof(u128) * n); img = malloc(sizeof(u128) * n);
    for (int i = 0; i < n; i++) { cand[i] = rd(0); img[i] = redT(cand[i]); }
    int e = K - t;
    if (e < 0) return 0;
    if (e == 0) test(); else rec(0, 0, e);
    fprintf(stderr, "done K=%d tested=%ld sols=%ld\n", K, tested, nsol);
    return 0;
}
