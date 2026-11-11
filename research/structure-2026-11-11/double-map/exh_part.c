/* Exhaustive search as in exh.c, with one more pruning rule: the partition lemma.
 *
 * build: gcc -O2 -o exh_part exh_part.c
 * usage: ./exh_part m N partfile maxnodes row_0 ... row_(m-1)
 *   partfile: first line "P n", then P lines of n block labels: ALL valid partitions of the 2m inputs
 *   with at least 2m - N blocks (python3 partitions.py T minblocks --dump file).
 *   Optional environment: EXH_HELPERS="mask,mask,..." (decimal) restricts the odd extras to these masks;
 *   EXH_NODEP=1 forbids even extras that are linearly dependent on the earlier even signals.
 *
 * Extra pruning.  At any time the inputs are partitioned by "e_i + e_j lies in the span E of the even
 * signals".  E only grows, so the current partition refines the final one, which is valid (every output
 * row odd on exactly one block) and has 2m - dim E >= 2m - N blocks.  An even extra that enlarges E is the
 * XOR of two odd signals congruent to inputs i and j of different blocks, and merges those blocks; the
 * branch is cut if no listed partition has i and j in one block together with all earlier merges.
 * Candidates cut by this rule or by the rank rule lie in no solution containing the current prefix, so
 * they are also excluded from the later siblings' subtrees.
 * Exit code 0: circuit found, 1: no circuit with at most N extras, 3: node limit reached.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define MAXN 16
#define MAXSIG 200
#define MAXCAND 20000
#define MAXW 128
#define MAXD 24

static int n, m, N;
static int ntargets;
static unsigned char is_target[1 << MAXN], avail[1 << MAXN];
static signed char rootof[1 << MAXN];
static unsigned char helper_ok[1 << MAXN];
static int use_helper_list = 0, nodep = 0;
static int excluded[1 << MAXN];
static int stamp[1 << MAXN], stamp_id = 0;
static int sig[MAXSIG], nsig;
static int targets_done;
static int ebasis[MAXN + 1], nebasis;
static int extras[64];
static long long nodes = 0, maxnodes = 0;
static int found = 0, aborted = 0;
static int W = 0, P = 0;
static uint64_t same[MAXN][MAXN][MAXW];
static uint64_t compat[MAXD][MAXW];
static int blk[MAXD][MAXN];

static int par(int v) { return __builtin_popcount(v) & 1; }

static int reduce(int v) {
    for (int i = 0; i < nebasis; i++) {
        int b = ebasis[i];
        if ((v ^ b) < v) v ^= b;
    }
    return v;
}

static void add_signal(int s, int root) {
    int head = nsig;
    avail[s] = 1;
    rootof[s] = (signed char)root;
    sig[nsig++] = s;
    while (head < nsig) {
        int t = sig[head++];
        int lim = nsig;
        for (int i = 0; i < lim; i++) {
            int u = sig[i] ^ t;
            if (is_target[u] && !avail[u]) {
                avail[u] = 1;
                rootof[u] = rootof[sig[i]] >= 0 ? rootof[sig[i]] : rootof[t];
                sig[nsig++] = u;
                targets_done++;
            }
        }
    }
}

static void dfs(int depth, int slack) {
    if (found || aborted) return;
    nodes++;
    if (maxnodes && nodes > maxnodes) { aborted = 1; return; }
    if (targets_done == ntargets) {
        found = 1;
        printf("  solution:");
        for (int i = 0; i < depth; i++) printf(" %s%x", par(extras[i]) ? "h:" : "", extras[i]);
        printf("\n");
        return;
    }
    if (depth == N) return;
    int *cand = (int *)malloc(sizeof(int) * MAXCAND * 3);
    int *cra = cand + MAXCAND, *crb = cand + 2 * MAXCAND;
    int nc = 0;
    stamp_id++;
    for (int i = 0; i < nsig; i++)
        for (int j = i + 1; j < nsig; j++) {
            int c = sig[i] ^ sig[j];
            if (avail[c] || is_target[c] || excluded[c] || stamp[c] == stamp_id) continue;
            stamp[c] = stamp_id;
            if (nc < MAXCAND) { cand[nc] = c; cra[nc] = rootof[sig[i]]; crb[nc] = rootof[sig[j]]; nc++; }
            else { fprintf(stderr, "candidate overflow\n"); exit(2); }
        }
    int save_nsig = nsig, save_td = targets_done, save_nb = nebasis;
    for (int ci = 0; ci < nc; ci++) {
        int c = cand[ci];
        int inc = 0, root = -1, ok = 1;
        if (par(c)) {
            root = cra[ci] >= 0 ? cra[ci] : crb[ci];
            if (slack == 0) ok = 0;
            if (use_helper_list && !helper_ok[c]) ok = 0;
        } else {
            int r = reduce(c);
            if (r) inc = 1;
            if (!inc && (slack == 0 || nodep)) ok = 0;
        }
        memcpy(blk[depth + 1], blk[depth], sizeof(int) * n);
        memcpy(compat[depth + 1], compat[depth], sizeof(uint64_t) * W);
        if (ok && inc) {
            int a = cra[ci], b = crb[ci];
            if (a < 0 || b < 0) {
                fprintf(stderr, "internal: rank increase without two odd operands: c=%x a=%d b=%d depth=%d\n", c, a, b, depth);
                for (int i = 0; i < nsig; i++) fprintf(stderr, " %x:%d", sig[i], rootof[sig[i]]);
                fprintf(stderr, "\n basis(%d):", nebasis);
                for (int i = 0; i < nebasis; i++) fprintf(stderr, " %x", ebasis[i]);
                fprintf(stderr, " slack=%d\n", slack);
                exit(2);
            }
            int A = blk[depth][a], Bk = blk[depth][b];
            if (A == Bk) { fprintf(stderr, "internal: rank increase inside a block\n"); exit(2); }
            int any = 0;
            for (int w = 0; w < W; w++) {
                compat[depth + 1][w] &= same[a][b][w];
                if (compat[depth + 1][w]) any = 1;
            }
            if (!any) ok = 0;
            for (int i = 0; i < n; i++) if (blk[depth + 1][i] == Bk) blk[depth + 1][i] = A;
        }
        if (ok) {
            if (inc) { int rr = reduce(c); ebasis[nebasis] = rr; nebasis++; }
            extras[depth] = c;
            add_signal(c, root);
            dfs(depth + 1, inc ? slack : slack - 1);
            while (nsig > save_nsig) { --nsig; avail[sig[nsig]] = 0; rootof[sig[nsig]] = -1; }
            targets_done = save_td;
            nebasis = save_nb;
            if (found || aborted) break;
        }
        excluded[c]++;
        cand[ci] = -c - 1;
        if (depth == 0 && getenv("EXH_PROGRESS"))
            fprintf(stderr, "top-level %d/%d done, nodes=%lld\n", ci + 1, nc, nodes);
    }
    for (int ci = 0; ci < nc; ci++)
        if (cand[ci] < 0) excluded[-cand[ci] - 1]--;
    free(cand);
}

int main(int argc, char **argv) {
    if (argc < 6) { fprintf(stderr, "usage: exh_part m N partfile maxnodes rows...\n"); return 2; }
    m = atoi(argv[1]);
    N = atoi(argv[2]);
    n = 2 * m;
    maxnodes = atoll(argv[4]);
    int T[MAXN];
    for (int j = 0; j < m; j++) T[j] = atoi(argv[5 + j]) & ~(1 << j);
    FILE *f = fopen(argv[3], "r");
    if (!f) { fprintf(stderr, "cannot open partition file\n"); return 2; }
    int nn;
    if (fscanf(f, "%d %d", &P, &nn) != 2 || nn != n) { fprintf(stderr, "bad partition file\n"); return 2; }
    W = (P + 63) / 64;
    if (W > MAXW) { fprintf(stderr, "too many partitions\n"); return 2; }
    for (int p = 0; p < P; p++) {
        int b[MAXN];
        for (int i = 0; i < n; i++) if (fscanf(f, "%d", &b[i]) != 1) { fprintf(stderr, "bad partition file\n"); return 2; }
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                if (b[i] == b[j]) same[i][j][p / 64] |= (uint64_t)1 << (p % 64);
    }
    fclose(f);
    const char *hl = getenv("EXH_HELPERS");
    if (hl && *hl) {
        use_helper_list = 1;
        char *copy = strdup(hl), *tok = strtok(copy, ",");
        while (tok) { helper_ok[atoi(tok)] = 1; tok = strtok(NULL, ","); }
    }
    if (getenv("EXH_NODEP")) nodep = 1;
    memset(rootof, -1, sizeof(rootof));
    ntargets = 0;
    for (int j = 0; j < m; j++) {
        int o1 = (1 << j) | T[j] | (T[j] << m);
        int o2 = (1 << (m + j)) | T[j] | (T[j] << m);
        is_target[o1] = 1;
        is_target[o2] = 1;
        ntargets += 2;
    }
    nsig = 0;
    for (int i = 0; i < n; i++) { avail[1 << i] = 1; rootof[1 << i] = (signed char)i; sig[nsig++] = 1 << i; blk[0][i] = i; }
    for (int p = 0; p < P; p++) compat[0][p / 64] |= (uint64_t)1 << (p % 64);
    targets_done = 0;
    nebasis = 0;
    dfs(0, N - m);
    printf("m=%d N=%d size=%d partitions=%d%s%s: %s nodes=%lld\n", m, N, 2 * m + N, P,
           use_helper_list ? " helpers=listed" : "", nodep ? " nodep" : "",
           aborted ? "ABORTED" : (found ? "SOLVABLE" : "NO CIRCUIT"), nodes);
    return aborted ? 3 : (found ? 0 : 1);
}
