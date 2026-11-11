/* Reviewer's exhaustive closure search for the local lemma (second independent method).
 *
 * Vectors are 8-bit: bits 0..3 = block a (index c), bits 4..7 = block b (index c).
 * Base = all 16 vectors supported on a (0 included) + the 4 units of b.
 * A circuit = sequence of gates, each the XOR of two available signals (base or earlier gate).
 * Reduction (sound for a lower bound): delete every gate whose value equals the base or an earlier
 * gate (redirect its uses); delete unused gates.  What remains is a set V of distinct, non-base
 * values containing the 4 targets, such that the greedy closure from the base reaches all of V
 * (availability is monotone, so a valid ordering exists iff greedy closure succeeds).
 * Write V = T u H (H = helpers).  The search enumerates H by canonical augmentation:
 *   state S = closure of base u {h_1..h_i} in which every reachable TARGET is added at once;
 *   h_{i+1} must be reachable from S (a sum of two elements of S) and not in S;
 *   canonical rule: h_{i+1} > h_i, or h_{i+1} was NOT reachable before h_i was added.
 * Completeness: for valid H take h_i = the smallest remaining helper reachable from S_{i-1}
 * (one exists: the first element of the valid ordering of H u T missing from S_{i-1} is
 * reachable; it is not a target, since reachable targets are in S).  That sequence satisfies the
 * canonical rule.  So: if no H with |H| <= MAXH is found, no circuit has <= MAXH + 4 gates.
 * Usage: ./lemma_exh MAXH [stop_at_first]
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

typedef struct { uint64_t w[4]; } bs;
static inline void bset(bs *b, int i) { b->w[i >> 6] |= 1ULL << (i & 63); }
static inline int bget(const bs *b, int i) { return (b->w[i >> 6] >> (i & 63)) & 1; }

typedef struct {
    bs avail, reach;
    int list[64];
    int n;
} state;

static int T[4];
static int MAXH, STOP;
static long long nodes[16];
static long long found[16];
static int path[16];

static void add(state *s, int x) {
    for (int i = 0; i < s->n; i++) bset(&s->reach, x ^ s->list[i]);
    s->list[s->n++] = x;
    bset(&s->avail, x);
    for (int k = 0; k < 4; k++) s->reach.w[k] &= ~s->avail.w[k];
}

static void closure(state *s) {
    int changed = 1;
    while (changed) {
        changed = 0;
        for (int k = 0; k < 4; k++)
            if (!bget(&s->avail, T[k]) && bget(&s->reach, T[k])) { add(s, T[k]); changed = 1; }
    }
}

static int done(const state *s) {
    for (int k = 0; k < 4; k++) if (!bget(&s->avail, T[k])) return 0;
    return 1;
}

static void dfs(const state *s, int d, int hprev, const bs *reach_before_prev) {
    nodes[d]++;
    if (done(s)) {
        found[d]++;
        if (found[d] <= 3) {
            printf("FOUND with %d helpers (%d gates):", d, d + 4);
            for (int i = 0; i < d; i++) printf(" %02x", path[i]);
            printf("\n");
        }
        if (STOP) { fflush(stdout); exit(0); }
        return;
    }
    if (d == MAXH) return;
    for (int h = 0; h < 256; h++) {
        if (!bget(&s->reach, h)) continue;
        if (d > 0 && h < hprev && bget(reach_before_prev, h)) continue;
        state t = *s;
        add(&t, h);
        closure(&t);
        path[d] = h;
        dfs(&t, d + 1, h, &s->reach);
    }
}

int main(int argc, char **argv) {
    MAXH = atoi(argv[1]);
    STOP = argc > 2 ? atoi(argv[2]) : 0;
    for (int c = 0; c < 4; c++) {
        int E = (1 << (4 + (c + 1) % 4)) | (1 << (4 + (c + 2) % 4)) | (1 << (4 + (c + 3) % 4));
        int sv = (1 << (c % 4)) | (1 << ((c + 1) % 4));
        T[c] = E | sv;
    }
    if (argc > 6) for (int c = 0; c < 4; c++) T[c] = (int)strtol(argv[3 + c], 0, 16);
    state s;
    memset(&s, 0, sizeof s);
    /* base: add one by one (reach computed from pairwise sums) */
    for (int a = 0; a < 16; a++) add(&s, a);
    for (int i = 0; i < 4; i++) add(&s, 1 << (4 + i));
    closure(&s);
    printf("targets %02x %02x %02x %02x ; initial reach size:", T[0], T[1], T[2], T[3]);
    int cnt = 0;
    for (int h = 0; h < 256; h++) cnt += bget(&s.reach, h);
    printf(" %d\n", cnt);
    bs empty; memset(&empty, 0, sizeof empty);
    dfs(&s, 0, -1, &empty);
    for (int d = 0; d <= MAXH; d++)
        printf("depth %d: nodes %lld, complete circuits %lld\n", d, nodes[d], found[d]);
    printf("result for <= %d gates: %s\n", MAXH + 4, 0 ? "" : "see counts above");
    return 0;
}
