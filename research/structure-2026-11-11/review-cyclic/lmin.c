/* Independent reviewer code (not derived from the author's scripts).
 * Exhaustive minimum sizes of cyclic sets and circuit sets containing E and given targets.
 * usage: lmin n maxk printk t1 t2 ...   (targets as decimal ints, bit i = coefficient of e_(i+1))
 * For k = 0..maxk extras (nonzero, non-unit, non-target vectors) counts the supersets
 * S = E + targets + extras that are (a) cyclic, (b) circuit sets, (c) cyclic but not circuit.
 * If printk >= 0, prints the extras of every cyclic set at k = printk (lines "C a b c [circ]").
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int n, N;
static int S[64], s;
static int idx[256];

static int is_cyclic(void) {
    /* rank over F2 of triples of S restricted to non-unit coordinates must equal s - n */
    int i, j, k;
    unsigned long long basis[64];
    int rank = 0;
    memset(basis, 0, sizeof(basis));
    for (i = 0; i < 256; i++) idx[i] = -1;
    for (i = 0; i < s; i++) idx[S[i]] = i;
    for (i = 0; i < s; i++)
        for (j = i + 1; j < s; j++) {
            k = idx[S[i] ^ S[j]];
            if (k > j) {
                unsigned long long v = 0;
                /* columns: indices >= n are non-units (S[0..n-1] are units) */
                if (i >= n) v |= 1ULL << i;
                if (j >= n) v |= 1ULL << j;
                v |= 1ULL << k;
                /* reduce */
                for (int b = 63; b >= 0 && v; b--) {
                    if (!((v >> b) & 1)) continue;
                    if (basis[b]) v ^= basis[b];
                    else { basis[b] = v; rank++; v = 0; }
                }
            }
        }
    return rank == s - n;
}

static int is_circuit(void) {
    unsigned char have[256];
    int i, j, changed, cnt = n;
    memset(have, 0, sizeof(have));
    for (i = 0; i < n; i++) have[S[i]] = 1;
    do {
        changed = 0;
        for (i = n; i < s; i++) {
            if (have[S[i]]) continue;
            for (j = 0; j < s; j++)
                if (have[S[j]] && have[S[i] ^ S[j]] && (S[i] ^ S[j]) != S[j]) {
                    have[S[i]] = 1; changed = 1; cnt++; break;
                }
        }
    } while (changed);
    return cnt == s;
}

int main(int argc, char **argv) {
    int maxk, printk, i, nt;
    int base[64], nb = 0;
    int cand[256], nc = 0;
    unsigned char inbase[256];
    if (argc < 5) { fprintf(stderr, "usage\n"); return 1; }
    n = atoi(argv[1]); maxk = atoi(argv[2]); printk = atoi(argv[3]);
    N = 1 << n;
    memset(inbase, 0, sizeof(inbase));
    for (i = 0; i < n; i++) { base[nb++] = 1 << i; inbase[1 << i] = 1; }
    nt = 0;
    for (i = 4; i < argc; i++) {
        int t = atoi(argv[i]);
        if (t <= 0 || t >= N) { fprintf(stderr, "bad target\n"); return 1; }
        if (!inbase[t]) { base[nb++] = t; inbase[t] = 1; nt++; }
    }
    for (i = 1; i < N; i++) if (!inbase[i]) cand[nc++] = i;
    printf("n=%d nonunit_targets=%d candidates=%d\n", n, nt, nc);
    for (int k = 0; k <= maxk; k++) {
        long long ncyc = 0, ncirc = 0, nboth = 0, tot = 0;
        int c[8];
        for (i = 0; i < k; i++) c[i] = i;
        if (k > nc) break;
        while (1) {
            s = 0;
            for (i = 0; i < nb; i++) S[s++] = base[i];
            for (i = 0; i < k; i++) S[s++] = cand[c[i]];
            tot++;
            int cy = is_cyclic();
            int ci = is_circuit();
            if (cy) ncyc++;
            if (ci) ncirc++;
            if (ci && !cy) nboth++; /* should never happen: circuit sets are cyclic */
            if (cy && k == printk) {
                printf("C");
                for (i = 0; i < k; i++) printf(" %d", cand[c[i]]);
                printf(ci ? " circ\n" : " noncirc\n");
            }
            /* next combination */
            if (k == 0) break;
            i = k - 1;
            while (i >= 0 && c[i] == nc - k + i) i--;
            if (i < 0) break;
            c[i]++;
            for (int j = i + 1; j < k; j++) c[j] = c[j - 1] + 1;
        }
        printf("k=%d size=%d sets=%lld cyclic=%lld circuit=%lld circuit_not_cyclic=%lld\n",
               k, nt + k, tot, ncyc, ncirc, nboth);
        fflush(stdout);
    }
    return 0;
}
