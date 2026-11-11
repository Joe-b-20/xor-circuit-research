/* Exhaustive search for XOR circuits of a double map with a prescribed number of non-output gates.
 *
 * build: gcc -O2 -o exh exh.c
 * usage: ./exh m N mode row_0 ... row_(m-1) [maxnodes]
 *    rows of T as decimal bit masks over w_0..w_(m-1) (zero diagonal, no zero row, no zero column);
 *    N = number of non-output gates ("extras": even signals and odd helpers); circuit size = 2m + N.
 *    mode 0: stop at the first solution;  mode 1: enumerate all solution sets and print statistics.
 *
 * Model.  A circuit with extras S (a set of masks, none an input or an output) exists iff the closure
 * "add any element of S or any output that is the XOR of two available signals" started from the inputs
 * reaches all outputs and all of S (order is irrelevant: the closure is monotone).  The search adds
 * extras one at a time; outputs are added by closure as soon as possible.  Each set S is visited at most
 * once (a candidate explored at a node is excluded in the later siblings' subtrees: every solution
 * containing it and the current prefix lies in its own subtree).
 * Pruning (valid for reduced T, Lemma A + partition lemma): the even signals must finally span a space of
 * dimension >= m, and each extra raises that dimension by at most one, so at most N - m extras may be
 * odd or linearly dependent on the earlier even signals.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXN 16
#define MAXSIG 200
#define MAXCAND 20000

static int n, m, N, mode;
static int ntargets;
static unsigned char is_target[1 << MAXN], avail[1 << MAXN];
static int excluded[1 << MAXN];
static int stamp[1 << MAXN], stamp_id = 0;
static int sig[MAXSIG], nsig;
static int targets_done;
static int ebasis[MAXN + 1], nebasis;
static int extras[64];
static long long nodes = 0, maxnodes = 0, nsol = 0;
static long long stat_h[64], stat_c[64], stat_pair = 0, stat_hc[16][32];
static int found = 0, aborted = 0;

static int par(int v) { return __builtin_popcount(v) & 1; }

static int reduce(int v) {
    for (int i = 0; i < nebasis; i++) {
        int b = ebasis[i];
        if ((v ^ b) < v) v ^= b;
    }
    return v;
}

static void add_signal(int s) {
    /* add s and close under "output = XOR of two available signals" */
    int head = nsig;
    avail[s] = 1;
    sig[nsig++] = s;
    while (head < nsig) {
        int t = sig[head++];
        int lim = nsig;
        for (int i = 0; i < lim; i++) {
            int u = sig[i] ^ t;
            if (is_target[u] && !avail[u]) {
                avail[u] = 1;
                sig[nsig++] = u;
                targets_done++;
            }
        }
    }
}

static void report(int depth) {
    nsol++;
    int h = 0;
    /* final partition from the even extras */
    int basis[MAXN + 1], nb = 0;
    for (int i = 0; i < depth; i++) {
        int v = extras[i];
        if (par(v)) { h++; continue; }
        for (int j = 0; j < nb; j++) if ((v ^ basis[j]) < v) v ^= basis[j];
        if (v) basis[nb++] = v;
    }
    int c = n - nb;
    /* pair partition test: every extra has u_k-bit != v_k-bit for at most one k */
    int pair = 1;
    for (int i = 0; i < depth; i++) {
        int v = extras[i];
        int d = (v ^ (v >> m)) & ((1 << m) - 1);
        if (__builtin_popcount(d) > 1) pair = 0;
    }
    stat_h[h]++;
    stat_c[c]++;
    stat_hc[h][c]++;
    if (pair) stat_pair++;
    if (nsol <= 3 || (pair && stat_pair <= 2)) {
        printf("  solution%s:", pair ? " (pair partition)" : "");
        for (int i = 0; i < depth; i++) printf(" %s%x", par(extras[i]) ? "h:" : "", extras[i]);
        printf("\n");
    }
}

static void dfs(int depth, int slack) {
    if (found && mode == 0) return;
    if (aborted) return;
    nodes++;
    if (maxnodes && nodes > maxnodes) { aborted = 1; return; }
    if (targets_done == ntargets) {
        /* all extras so far are available by construction */
        if (depth == N) { found = 1; report(depth); }
        else { found = 1; report(depth); }  /* fewer extras than N: also a solution */
        return;
    }
    if (depth == N) return;
    /* candidates */
    int *cand = (int *)malloc(sizeof(int) * MAXCAND);
    int nc = 0;
    stamp_id++;
    for (int i = 0; i < nsig; i++)
        for (int j = i + 1; j < nsig; j++) {
            int c = sig[i] ^ sig[j];
            if (avail[c] || is_target[c] || excluded[c] || stamp[c] == stamp_id) continue;
            stamp[c] = stamp_id;
            if (nc < MAXCAND) cand[nc++] = c;
        }
    int save_nsig = nsig, save_td = targets_done, save_nb = nebasis;
    for (int ci = 0; ci < nc; ci++) {
        int c = cand[ci];
        int inc = 0;
        if (!par(c)) {
            int r = reduce(c);
            if (r) inc = 1;
        }
        if (!inc && slack == 0) continue;   /* rank rule; such a candidate is simply not explored here */
        if (inc) { int rr = reduce(c); ebasis[nebasis] = rr; nebasis++; }
        extras[depth] = c;
        add_signal(c);
        dfs(depth + 1, inc ? slack : slack - 1);
        /* undo */
        while (nsig > save_nsig) avail[sig[--nsig]] = 0;
        targets_done = save_td;
        nebasis = save_nb;
        if (found && mode == 0) break;
        if (aborted) break;
        excluded[c]++;
        cand[ci] = -c - 1; /* mark explored */
    }
    for (int ci = 0; ci < nc; ci++)
        if (cand[ci] < 0) excluded[-cand[ci] - 1]--;
    free(cand);
}

int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "usage: exh m N mode rows... [maxnodes]\n"); return 2; }
    m = atoi(argv[1]);
    N = atoi(argv[2]);
    mode = atoi(argv[3]);
    n = 2 * m;
    int T[MAXN];
    for (int j = 0; j < m; j++) T[j] = atoi(argv[4 + j]) & ~(1 << j);
    if (argc > 4 + m) maxnodes = atoll(argv[4 + m]);
    ntargets = 0;
    for (int j = 0; j < m; j++) {
        int o1 = (1 << j) | T[j] | (T[j] << m);
        int o2 = (1 << (m + j)) | T[j] | (T[j] << m);
        is_target[o1] = 1;
        is_target[o2] = 1;
        ntargets += 2;
    }
    nsig = 0;
    for (int i = 0; i < n; i++) { avail[1 << i] = 1; sig[nsig++] = 1 << i; }
    targets_done = 0;
    nebasis = 0;
    dfs(0, N - m);
    printf("m=%d N=%d size=%d: %s nodes=%lld", m, N, 2 * m + N,
           aborted ? "ABORTED" : (found ? "SOLVABLE" : "NO CIRCUIT"), nodes);
    if (mode == 1 && found) {
        printf(" solution_sets=%lld pair_partition_sets=%lld\n  by (helpers h, blocks c):", nsol, stat_pair);
        for (int h = 0; h < 16; h++)
            for (int c = 0; c < 32; c++)
                if (stat_hc[h][c]) printf(" (h=%d,c=%d):%lld", h, c, stat_hc[h][c]);
    }
    printf("\n");
    return aborted ? 3 : (found ? 0 : 1);
}
