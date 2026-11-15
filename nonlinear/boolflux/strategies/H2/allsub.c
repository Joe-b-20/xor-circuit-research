/* Enumerate ALL D-dim subspaces of F_2^q (q <= 20) and print those containing >= NEED weight of
   the given points (members' images mod free + T_full, compressed to q bits).
   Input: n q, then n lines "hi lo" (only the low q bits are used; must be < 2^q).
   Output: "SOL w i1 i2 ..." with all members whose image lies in the subspace (0 excluded).
   usage: allsub D NEED < file.img   (exhaustive; cost ~ [q choose D]_2 * 2^D) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int n, q, D, NEED;
static unsigned *img; static unsigned *fullv; static int *wt; static int **lists; static int *lcnt;
static long nsub = 0, nsol = 0;
static unsigned rows[32]; static int piv[32];
static void check(void) {
    nsub++;
    /* enumerate span */
    unsigned pts[1 << 8]; int np = 1; pts[0] = 0;
    for (int i = 0; i < D; i++) { int m = np; for (int j = 0; j < m; j++) pts[np++] = pts[j] ^ rows[i]; }
    int w = 0;
    for (int j = 1; j < np; j++) w += wt[pts[j]];
    if (w < NEED) return;
    /* rank test: span of the full vectors of all members in the subspace must contain e_0..e_7 */
    unsigned bs[64]; int nb = 0;
    for (int j = 1; j < np; j++) for (int k = 0; k < lcnt[pts[j]]; k++) {
        unsigned v = fullv[lists[pts[j]][k]];
        for (int a = 0; a < nb; a++) if ((v ^ bs[a]) < v) v ^= bs[a];
        if (v) { bs[nb++] = v; for (int a = nb - 1; a > 0 && bs[a] > bs[a - 1]; a--) { unsigned t = bs[a]; bs[a] = bs[a - 1]; bs[a - 1] = t; } }
    }
    for (int e = 0; e < 8; e++) { unsigned v = 1u << e; for (int a = 0; a < nb; a++) if ((v ^ bs[a]) < v) v ^= bs[a]; if (v) return; }
    nsol++;
    printf("SOL %d", w);
    for (int j = 1; j < np; j++) for (int k = 0; k < lcnt[pts[j]]; k++) printf(" %d", lists[pts[j]][k]);
    printf("\n");
}
/* RREF: choose pivot positions p_0 > p_1 > ... ; row i has leading bit p_i, zeros at other pivots,
   free bits below p_i at non-pivot positions */
static void rec(int i, int maxp) {
    if (i == D) {
        /* now enumerate free bits: rows[i] free positions = non-pivot positions below piv[i] */
        int fpos[32][32], nf[32]; long tot = 1;
        for (int r = 0; r < D; r++) {
            nf[r] = 0;
            for (int b = piv[r] - 1; b >= 0; b--) {
                int isp = 0; for (int s = 0; s < D; s++) if (piv[s] == b) isp = 1;
                if (!isp) fpos[r][nf[r]++] = b;
            }
        }
        int totbits = 0; for (int r = 0; r < D; r++) totbits += nf[r];
        for (long m = 0; m < (1L << totbits); m++) {
            long mm = m;
            for (int r = 0; r < D; r++) {
                unsigned v = 1u << piv[r];
                for (int k = 0; k < nf[r]; k++) { if (mm & 1) v |= 1u << fpos[r][k]; mm >>= 1; }
                rows[r] = v;
            }
            check();
        }
        (void)tot;
        return;
    }
    for (int p = maxp; p >= D - 1 - i; p--) { piv[i] = p; rec(i + 1, p - 1); }
}
int main(int argc, char **argv) {
    D = atoi(argv[1]); NEED = atoi(argv[2]);
    if (scanf("%d %d", &n, &q) != 2) return 1;
    int qq = q - 8;               /* images have the T bits (0..7) cleared: shift them out */
    img = malloc(sizeof(unsigned) * n);
    wt = calloc(1 << qq, sizeof(int)); lcnt = calloc(1 << qq, sizeof(int)); lists = calloc(1 << qq, sizeof(int *));
    for (int i = 0; i < n; i++) {
        unsigned long long hi, lo; if (scanf("%llx %llx", &hi, &lo) != 2) return 1;
        if (hi || (lo >> q)) { fprintf(stderr, "image too wide\n"); return 1; }
        img[i] = (unsigned)(lo >> 8); wt[img[i]]++;
    }
    for (int i = 0; i < n; i++) { unsigned p = img[i]; lists[p] = realloc(lists[p], sizeof(int) * (lcnt[p] + 1)); lists[p][lcnt[p]++] = i; }
    { FILE *ff = fopen(argv[3], "r"); fullv = malloc(sizeof(unsigned) * n); for (int i = 0; i < n; i++) if (fscanf(ff, "%x", &fullv[i]) != 1) return 2; fclose(ff); }
    q = qq;
    rec(0, q - 1);
    fprintf(stderr, "done D=%d q=%d subspaces %ld sols %ld\n", D, q, nsub, nsol);
    return 0;
}
