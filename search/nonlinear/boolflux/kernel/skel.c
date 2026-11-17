/* skel.c -- BoolFlux AND-skeleton search.
 *
 * A skeleton is a list of K AND gates g_k = L_k * R_k, where L_k and R_k are affine forms over
 * the basis (1, x_0..x_{n-1}, g_0..g_{k-1}); it implements a function when every output truth
 * table lies in the GF(2) span of the basis tables (the outputs are then affine forms, computed
 * by XOR gates).  K is the number of nonlinear gates (multiplicative complexity of the circuit).
 *
 * Moves (every accepted state is checked exactly on the complete truth tables):
 *   swap   replace a leaf AND j (one no other AND reads) by any product q = L*R with
 *          q = g_j (mod U_j), U_j = span(basis without g_j): the outputs stay in the span.  If the
 *          outputs do not need g_j at all, j is deleted.
 *   merge  for two leaves j,k whose output usage has rank <= 1, replace both by one product
 *          q = r (mod U_jk), r the common residual: K decreases by 1.
 *   split  replace a leaf L*R by L*(R+Z) and L*Z (K+1; a kick, accepted under annealing).
 *   perturb add a random basis element to one operand of a random AND; accept if the outputs
 *          stay in the span.
 * Objective: w_a*K + w_lin*E, E = sum over operand and output forms of (weight-1)^+ (an XOR
 * count without sharing), optional cap on AND depth; optional cap.k adds a penalty of 10^6 per AND
 * above K = cap.k, and max_acc > 0 stops the run after that many accepted moves.
 *
 * Usage: skel CONFIG    (one "key value" per line; keys: in out seconds iters seed w.a w.lin cap.ad cap.k max_acc
 *                        T0 Tperiod_it mv.swap mv.merge mv.split mv.perturb pairs fext emit_current clock;
 *                        unknown keys are errors)
 * Skeleton file: "n N m M k K mw MW w W" then K lines "L R" (MW hex words each, word 0 first),
 * then M lines of output tables (W hex words), all words as 16-digit hex.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <time.h>

typedef uint64_t u64;
#define MW 8                 /* mask words: positions < 512 */
#define MAXW 16              /* table words: n <= 10 */
#define MAXK 480
#define MAXP (MW * 64)

static int N, M, W, K;
static u64 LASTMASK;
static inline u64 wmask(int w) { return w == W - 1 ? LASTMASK : ~0ULL; }

typedef struct { u64 L[MW], R[MW]; } And;
static And ands[MAXK], sv_ands[MAXK], best_ands[MAXK];
static int sv_K, best_K;
static u64 TGT[64][MAXW];
static u64 TAB[MAXP][MAXW];          /* basis tables by position */
static u64 Y[64][MW];                /* output forms */
static int AD[MAXK], LEAF[MAXK];

/* ---------------- rng */
static u64 rs[4];
static inline u64 rotl(u64 x, int k) { return (x << k) | (x >> (64 - k)); }
static u64 rnd(void) { u64 r = rotl(rs[1] * 5, 7) * 9, t = rs[1] << 17; rs[2] ^= rs[0]; rs[3] ^= rs[1]; rs[1] ^= rs[2]; rs[0] ^= rs[3]; rs[2] ^= t; rs[3] = rotl(rs[3], 45); return r; }
static void seed_rng(u64 s) { for (int i = 0; i < 4; i++) { s += 0x9E3779B97F4A7C15ULL; u64 z = s; z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL; z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL; rs[i] = z ^ (z >> 31); } }
static inline int rndint(int n) { return (int)((rnd() >> 11) % (u64)n); }
static inline double rnd01(void) { return (rnd() >> 11) * (1.0 / 9007199254740992.0); }

/* ---------------- masks */
static inline int mget(const u64 *m, int p) { return (m[p >> 6] >> (p & 63)) & 1; }
static inline void mflip(u64 *m, int p) { m[p >> 6] ^= 1ULL << (p & 63); }
static inline int mweight(const u64 *m) { int c = 0; for (int i = 0; i < MW; i++) c += __builtin_popcountll(m[i]); return c; }
static inline int mzero(const u64 *m) { for (int i = 0; i < MW; i++) if (m[i]) return 0; return 1; }
static inline int meq(const u64 *a, const u64 *b) { return !memcmp(a, b, 8 * MW); }
/* remove bit p, shifting higher bits down */
static void mdel(u64 *m, int p) {
    u64 out[MW] = {0}; int q = 0;
    for (int i = 0; i < MAXP; i++) { if (i == p) continue; if (mget(m, i)) out[q >> 6] |= 1ULL << (q & 63); q++; }
    memcpy(m, out, 8 * MW);
}
static inline int POS(int k) { return 1 + N + k; }
static void form_table(const u64 *m, u64 *t) {
    for (int w = 0; w < W; w++) t[w] = 0;
    for (int i = 0; i < MW; i++) { u64 x = m[i]; while (x) { int b = __builtin_ctzll(x); x &= x - 1; int p = i * 64 + b; for (int w = 0; w < W; w++) t[w] ^= TAB[p][w]; } }
    for (int w = 0; w < W; w++) t[w] &= wmask(w);
}
static void eval_all(void) {
    for (int k = 0; k < K; k++) {
        u64 a[MAXW], b[MAXW];
        form_table(ands[k].L, a); form_table(ands[k].R, b);
        for (int w = 0; w < W; w++) TAB[POS(k)][w] = a[w] & b[w];
    }
}

/* ---------------- elimination */
typedef struct { u64 t[MAXW]; u64 c[MW]; int piv; } Row;
static Row ROWS[MAXP]; static int NR;
static int lowbit(const u64 *t) { for (int w = 0; w < W; w++) if (t[w]) return w * 64 + __builtin_ctzll(t[w]); return -1; }
static void reduce(u64 *t, u64 *c) {
    for (int i = 0; i < NR; i++) {
        Row *r = &ROWS[i];
        if ((t[r->piv >> 6] >> (r->piv & 63)) & 1) {
            for (int w = 0; w < W; w++) t[w] ^= r->t[w];
            if (c) for (int j = 0; j < MW; j++) c[j] ^= r->c[j];
        }
    }
}
/* eliminate basis positions 0..1+N+K-1 except those set in excl; return -1 or a dependent
 * AND index (first g found dependent on earlier positions) */
static int elim(const u64 *excl) {
    NR = 0; int dep = -1;
    for (int p = 0; p < 1 + N + K; p++) {
        if (excl && mget(excl, p)) continue;
        Row *r = &ROWS[NR];
        memcpy(r->t, TAB[p], 8 * W); memset(r->c, 0, 8 * MW); mflip(r->c, p);
        reduce(r->t, r->c);
        int lb = lowbit(r->t);
        if (lb < 0) { if (p > N && dep < 0) dep = p - 1 - N; continue; }
        r->piv = lb; NR++;
    }
    return dep;
}

/* ---------------- analysis */
static double w_a = 1, w_lin = 0.001; static int cap_ad = -1, cap_k = -1, max_acc = -1; static long nacc = 0;
static double E_lin; static int feasible;
static double objective(void) { return w_a * K + w_lin * E_lin + (cap_k >= 0 && K > cap_k ? 1e6 * (K - cap_k) : 0); }

static int analyze(void) {    /* returns feasibility; deletes redundant ANDs */
    for (;;) {
        eval_all();
        int dep = elim(0);
        if (dep < 0) break;
        /* g_dep is in the span of earlier positions: substitute and delete it */
        u64 t[MAXW], c[MW]; memcpy(t, TAB[POS(dep)], 8 * W); memset(c, 0, 8 * MW);
        /* express via elimination over positions < POS(dep) */
        u64 ex[MW]; memset(ex, 0, sizeof ex);
        for (int p = POS(dep); p < 1 + N + K; p++) mflip(ex, p);
        elim(ex); reduce(t, c);
        int P = POS(dep);
        for (int k = dep + 1; k < K; k++) {
            if (mget(ands[k].L, P)) { mflip(ands[k].L, P); for (int i = 0; i < MW; i++) ands[k].L[i] ^= c[i]; }
            if (mget(ands[k].R, P)) { mflip(ands[k].R, P); for (int i = 0; i < MW; i++) ands[k].R[i] ^= c[i]; }
        }
        for (int k = dep + 1; k < K; k++) { mdel(ands[k].L, P); mdel(ands[k].R, P); }
        memmove(&ands[dep], &ands[dep + 1], sizeof(And) * (K - dep - 1)); K--;
    }
    feasible = 1;
    for (int j = 0; j < M; j++) {
        u64 t[MAXW]; memcpy(t, TGT[j], 8 * W); memset(Y[j], 0, 8 * MW);
        reduce(t, Y[j]);
        for (int w = 0; w < W; w++) if (t[w] & wmask(w)) feasible = 0;
    }
    E_lin = 0;
    for (int k = 0; k < K; k++) {
        LEAF[k] = 1;
        int a = 0;
        for (int p = 1 + N; p < POS(k); p++) if (mget(ands[k].L, p) || mget(ands[k].R, p)) { int d = AD[p - 1 - N]; if (d > a) a = d; }
        AD[k] = a + 1;
        int wl = mweight(ands[k].L) - mget(ands[k].L, 0), wr = mweight(ands[k].R) - mget(ands[k].R, 0);
        E_lin += (wl > 1 ? wl - 1 : 0) + (wr > 1 ? wr - 1 : 0);
    }
    for (int k = 0; k < K; k++)
        for (int k2 = k + 1; k2 < K; k2++) if (mget(ands[k2].L, POS(k)) || mget(ands[k2].R, POS(k))) { LEAF[k] = 0; break; }
    for (int j = 0; j < M; j++) { int wy = mweight(Y[j]) - mget(Y[j], 0); E_lin += wy > 1 ? wy - 1 : 0; }
    if (cap_ad >= 0) for (int k = 0; k < K; k++) if (AD[k] > cap_ad) feasible = 0;
    return feasible;
}

/* ---------------- operand forms for enumeration */
static u64 FM[200000][MW]; static u64 FT[200000][MAXW]; static int FAD[200000]; static int NF, NXF;
static int fext = 400, pairs_cap = 60000, emit_current = 0;
static int form_ad(const u64 *m) { int a = 0; for (int p = 1 + N; p < 1 + N + K; p++) if (mget(m, p)) { int d = AD[p - 1 - N]; if (d > a) a = d; } return a; }
static void add_form(const u64 *m, const u64 *excl) {
    if (NF >= 200000 || mzero(m)) return;
    for (int i = 0; i < MW; i++) if (m[i] & excl[i]) return;
    if (mget(m, 0)) return;                            /* constants are irrelevant mod U */
    memcpy(FM[NF], m, 8 * MW); form_table(m, FT[NF]); FAD[NF] = form_ad(m); NF++;
}
static void build_forms(const u64 *excl) {
    NF = 0; u64 m[MW];
    if (N <= 10) for (int v = 1; v < (1 << N); v++) { memset(m, 0, sizeof m); for (int i = 0; i < N; i++) if ((v >> (N - 1 - i)) & 1) mflip(m, 1 + i); add_form(m, excl); }
    NXF = NF;
    int base = NF;
    /* existing operand forms (without constant) and AND outputs */
    for (int k = 0; k < K; k++) {
        memcpy(m, ands[k].L, sizeof m); if (mget(m, 0)) mflip(m, 0); add_form(m, excl);
        memcpy(m, ands[k].R, sizeof m); if (mget(m, 0)) mflip(m, 0); add_form(m, excl);
        memset(m, 0, sizeof m); mflip(m, POS(k)); add_form(m, excl);
    }
    int top = NF;
    for (int s = 0; s < fext && top > base + 1; s++) {
        int i = base + rndint(top - base), j = base + rndint(top - base);
        for (int q = 0; q < MW; q++) m[q] = FM[i][q] ^ FM[j][q];
        add_form(m, excl);
        int x = rndint(N); memcpy(m, FM[i], sizeof m); mflip(m, 1 + x); add_form(m, excl);
    }
}

/* candidates q = L*R = r (mod span of current ROWS) */
typedef struct { int i, j; double e; } QC;
static QC QCS[256]; static int NQ;
/* the first NXF forms are the linear forms over the inputs */
static void try_pair(int i, int j, const u64 *rr, int max_ad, const u64 *avoidL, const u64 *avoidR, int *seen) {
    if (i == j) return;
    int ad = (FAD[i] > FAD[j] ? FAD[i] : FAD[j]) + 1;
    if (max_ad >= 0 && ad > max_ad) return;
    u64 q[MAXW];
    for (int w = 0; w < W; w++) q[w] = FT[i][w] & FT[j][w];
    reduce(q, 0);
    for (int w = 0; w < W; w++) if ((q[w] ^ rr[w]) & wmask(w)) return;
    if (avoidL && ((meq(FM[i], avoidL) && meq(FM[j], avoidR)) || (meq(FM[j], avoidL) && meq(FM[i], avoidR)))) return;
    (*seen)++;
    double e = mweight(FM[i]) + mweight(FM[j]);
    if (NQ < 256) { QCS[NQ].i = i; QCS[NQ].j = j; QCS[NQ].e = e; NQ++; }
    else { int s = rndint(*seen); if (s < 256) { QCS[s].i = i; QCS[s].j = j; QCS[s].e = e; } }
}
/* candidates q = L*R = r (mod span of current ROWS): every pair of input-linear forms when that
 * fits the budget, then random pairs over all forms with the rest of the budget */
static void find_products(const u64 *r, int max_ad, const u64 *avoidL, const u64 *avoidR) {
    NQ = 0; int seen = 0; long budget = pairs_cap;
    u64 rr[MAXW]; memcpy(rr, r, 8 * W); reduce(rr, 0);
    long nx = (long)NXF * (NXF - 1) / 2;
    if (nx <= budget) {
        for (int i = 0; i < NXF; i++) for (int j = i + 1; j < NXF; j++) try_pair(i, j, rr, max_ad, avoidL, avoidR, &seen);
        budget -= nx;
    }
    if (NF > NXF || nx > pairs_cap) {
        long all = (long)NF * (NF - 1) / 2;
        if (all - (nx <= pairs_cap ? nx : 0) <= budget) {
            for (int i = 0; i < NF; i++) for (int j = (i < NXF ? NXF : i + 1); j < NF; j++) try_pair(i, j, rr, max_ad, avoidL, avoidR, &seen);
        } else
            for (long t = 0; t < budget; t++) try_pair(rndint(NF), rndint(NF), rr, max_ad, avoidL, avoidR, &seen);
    }
}

/* ---------------- state save/restore */
static void save(void) { memcpy(sv_ands, ands, sizeof(And) * K); sv_K = K; }
static void restore(void) { memcpy(ands, sv_ands, sizeof(And) * sv_K); K = sv_K; analyze(); }
static void delete_and(int j) {       /* j must not be read by any later AND */
    int P = POS(j);
    for (int k = j + 1; k < K; k++) { mdel(ands[k].L, P); mdel(ands[k].R, P); }
    memmove(&ands[j], &ands[j + 1], sizeof(And) * (K - j - 1)); K--;
}
static void append_and(const u64 *L, const u64 *R) { memcpy(ands[K].L, L, 8 * MW); memcpy(ands[K].R, R, 8 * MW); K++; }
/* masks built while ANDs j (and k) still exist: remap to the numbering after deleting them */
static void remap_after_delete(u64 *m, int j, int k) {
    int a = j > k ? j : k, b = j > k ? k : j;
    if (k >= 0) { mdel(m, POS(a)); mdel(m, POS(b)); } else mdel(m, POS(j));
}

/* ---------------- moves */
static double T0 = 0.3, Tperiod_it = 5000, T;
static double mvw[4] = {4, 3, 1, 1};
static const char *MVN[4] = {"swap", "merge", "split", "perturb"};
static long st_p[4], st_a[4], st_i[4];

static int accept_obj(double oldo, double newo) {
    double d = newo - oldo;
    if (d <= 1e-12) return 1;
    return T > 0 && rnd01() < exp(-d / T);
}

static int mv_swap(double cur) {
    int nl = 0, leaves[MAXK]; for (int k = 0; k < K; k++) if (LEAF[k]) leaves[nl++] = k;
    if (!nl) return 0;
    int j = leaves[rndint(nl)];
    u64 ex[MW]; memset(ex, 0, sizeof ex); mflip(ex, POS(j));
    elim(ex);
    /* residual: the outputs' g_j components; any output with Y containing g_j has residual = g_j mod U */
    int used = 0; for (int o = 0; o < M; o++) if (mget(Y[o], POS(j))) used = 1;
    save();
    if (!used) { delete_and(j); if (analyze()) return 1; restore(); return 0; }
    build_forms(ex);
    find_products(TAB[POS(j)], cap_ad, ands[j].L, ands[j].R);
    if (!NQ) return 0;
    QC *c = &QCS[rndint(NQ)];
    u64 L[MW], R[MW]; memcpy(L, FM[c->i], sizeof L); memcpy(R, FM[c->j], sizeof R);
    remap_after_delete(L, j, -1); remap_after_delete(R, j, -1);
    delete_and(j); append_and(L, R);
    if (analyze() && accept_obj(cur, objective())) return 1;
    restore(); return 0;
}

static int mv_merge(double cur) {
    int nl = 0, leaves[MAXK]; for (int k = 0; k < K; k++) if (LEAF[k]) leaves[nl++] = k;
    if (nl < 2) return 0;
    /* pairs of leaves with output usage of rank <= 1 */
    static int pj[100000], pk[100000]; int np = 0;
    for (int a = 0; a < nl; a++) for (int b = a + 1; b < nl && np < 100000; b++) {
        int j = leaves[a], k = leaves[b], uj = 0, uk = 0, same = 1;
        for (int o = 0; o < M; o++) { int x = mget(Y[o], POS(j)), y = mget(Y[o], POS(k)); uj |= x; uk |= y; if (x != y) same = 0; }
        if (!uj || !uk || same) { pj[np] = j; pk[np] = k; np++; }
    }
    if (!np) return 0;
    int s = rndint(np), j = pj[s], k = pk[s];
    int uj = 0, uk = 0; for (int o = 0; o < M; o++) { uj |= mget(Y[o], POS(j)); uk |= mget(Y[o], POS(k)); }
    save();
    if (!uj || !uk) {      /* one is unused: delete it */
        int d = !uj ? j : k; delete_and(d);
        if (analyze()) return 1; restore(); return 0;
    }
    u64 ex[MW]; memset(ex, 0, sizeof ex); mflip(ex, POS(j)); mflip(ex, POS(k));
    elim(ex);
    u64 r[MAXW]; for (int w = 0; w < W; w++) r[w] = TAB[POS(j)][w] ^ TAB[POS(k)][w];
    build_forms(ex);
    find_products(r, cap_ad, 0, 0);
    if (!NQ) return 0;
    /* prefer lighter operands */
    int bi = 0; for (int q = 1; q < NQ; q++) if (QCS[q].e < QCS[bi].e) bi = q;
    if (rnd01() < 0.5) bi = rndint(NQ);
    u64 L[MW], R[MW]; memcpy(L, FM[QCS[bi].i], sizeof L); memcpy(R, FM[QCS[bi].j], sizeof R);
    remap_after_delete(L, j, k); remap_after_delete(R, j, k);
    int a = j > k ? j : k, b = j > k ? k : j;
    delete_and(a); delete_and(b); append_and(L, R);
    if (analyze()) return 1;
    restore(); return 0;
}

static int mv_split(double cur) {
    int nl = 0, leaves[MAXK]; for (int k = 0; k < K; k++) if (LEAF[k]) leaves[nl++] = k;
    if (!nl || K + 1 >= MAXK) return 0;
    int j = leaves[rndint(nl)];
    save();
    u64 Z[MW]; memset(Z, 0, sizeof Z);
    int p = 1 + rndint(N + j);       /* a basis element available to g_j */
    mflip(Z, p);
    u64 L[MW], R1[MW], R2[MW];
    int side = rnd() & 1;
    memcpy(L, side ? ands[j].L : ands[j].R, sizeof L);
    memcpy(R1, side ? ands[j].R : ands[j].L, sizeof R1);
    for (int i = 0; i < MW; i++) R1[i] ^= Z[i];
    memcpy(R2, Z, sizeof R2);
    remap_after_delete(L, j, -1); remap_after_delete(R1, j, -1); remap_after_delete(R2, j, -1);
    delete_and(j); append_and(L, R1); append_and(L, R2);
    if (analyze() && accept_obj(cur, objective())) return 1;
    restore(); return 0;
}

static int mv_perturb(double cur) {
    if (!K) return 0;
    int j = rndint(K);
    save();
    int p = rndint(1 + N + j);
    if (rnd() & 1) mflip(ands[j].L, p); else mflip(ands[j].R, p);
    if (analyze() && accept_obj(cur, objective())) return 1;
    restore(); return 0;
}

/* ---------------- io */
static void read_skel(const char *path) {
    FILE *f = fopen(path, "r"); if (!f) { fprintf(stderr, "skel: cannot open %s\n", path); exit(2); }
    int mw, w;
    if (fscanf(f, " n %d m %d k %d mw %d w %d", &N, &M, &K, &mw, &w) != 5) { fprintf(stderr, "skel: bad header\n"); exit(2); }
    if (N > 10 || M > 64 || K >= MAXK || mw != MW) { fprintf(stderr, "skel: size limits\n"); exit(2); }
    W = N >= 6 ? 1 << (N - 6) : 1; LASTMASK = N >= 6 ? ~0ULL : ((1ULL << (1 << N)) - 1);
    if (w != W) { fprintf(stderr, "skel: W mismatch\n"); exit(2); }
    for (int k = 0; k < K; k++) {
        for (int i = 0; i < MW; i++) if (fscanf(f, "%lx", &ands[k].L[i]) != 1) exit(2);
        for (int i = 0; i < MW; i++) if (fscanf(f, "%lx", &ands[k].R[i]) != 1) exit(2);
    }
    for (int j = 0; j < M; j++) for (int i = 0; i < W; i++) if (fscanf(f, "%lx", &TGT[j][i]) != 1) exit(2);
    fclose(f);
    for (int w2 = 0; w2 < W; w2++) TAB[0][w2] = wmask(w2);
    for (int i = 0; i < N; i++) { for (int w2 = 0; w2 < W; w2++) TAB[1 + i][w2] = 0;
        for (int x = 0; x < (1 << N); x++) if ((x >> (N - 1 - i)) & 1) TAB[1 + i][x >> 6] |= 1ULL << (x & 63); }
}
static void write_skel(const char *path, const char *note) {
    char tmp[1200]; snprintf(tmp, sizeof tmp, "%s.tmp", path);
    FILE *f = fopen(tmp, "w");
    fprintf(f, "n %d m %d k %d mw %d w %d\n", N, M, K, MW, W);
    for (int k = 0; k < K; k++) {
        for (int i = 0; i < MW; i++) fprintf(f, "%016lx ", ands[k].L[i]);
        for (int i = 0; i < MW; i++) fprintf(f, "%016lx%c", ands[k].R[i], i == MW - 1 ? '\n' : ' ');
    }
    for (int j = 0; j < M; j++) for (int i = 0; i < W; i++) fprintf(f, "%016lx%c", TGT[j][i], i == W - 1 ? '\n' : ' ');
    fprintf(f, "Y\n");
    for (int j = 0; j < M; j++) for (int i = 0; i < MW; i++) fprintf(f, "%016lx%c", Y[j][i], i == MW - 1 ? '\n' : ' ');
    fprintf(f, "# K %d E %.0f %s\n", K, E_lin, note);
    fclose(f); rename(tmp, path);
}

/* seconds budget clock, as in bfx.c: `clock real` (default; never runs backwards), `clock cpu`, `clock mono` (old) */
static int cfg_clock = 0;
static double now_s(void) {
    static double last = -1e300;
    struct timespec t;
    clock_gettime(cfg_clock == 1 ? CLOCK_PROCESS_CPUTIME_ID : cfg_clock == 2 ? CLOCK_MONOTONIC : CLOCK_REALTIME, &t);
    double x = t.tv_sec + t.tv_nsec * 1e-9;
    if (x < last) x = last;
    return last = x;
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: skel CONFIG\n"); return 2; }
    char in[1024] = "", out[1024] = "", k[256], v[1024];
    double seconds = 10; long iters = -1; u64 seed = 1;
    FILE *cf = fopen(argv[1], "r"); if (!cf) { fprintf(stderr, "skel: cannot open config %s\n", argv[1]); return 2; }
    /* one "key value" per line, as in bfx.c (the old token reader took tokens in pairs, so a stray token
     * shifted every later key, and an unknown mv.* key was silently ignored).  Blank lines and lines
     * starting with # are skipped; in/out take the rest of the line (paths may contain spaces). */
    char line[2048];
    while (fgets(line, sizeof line, cf)) {
        char *p = line + strspn(line, " \t\r\n");
        if (!*p || *p == '#') continue;
        if (sscanf(p, "%255s %1023s", k, v) != 2) { fprintf(stderr, "skel: config key %s has no value\n", k); return 2; }
        if (!strcmp(k, "in") || !strcmp(k, "out")) {
            char *q = p + strlen(k); q += strspn(q, " \t");
            size_t L = strlen(q); while (L && strchr(" \t\r\n", q[L - 1])) L--;
            if (L > 1023) { fprintf(stderr, "skel: path too long\n"); return 2; }
            memcpy(v, q, L); v[L] = 0;
        }
        if (!strcmp(k, "in")) strcpy(in, v); else if (!strcmp(k, "out")) strcpy(out, v);
        else if (!strcmp(k, "seconds")) seconds = atof(v); else if (!strcmp(k, "iters")) iters = atol(v);
        else if (!strcmp(k, "seed")) seed = strtoull(v, 0, 10);
        else if (!strcmp(k, "w.a")) w_a = atof(v); else if (!strcmp(k, "w.lin")) w_lin = atof(v);
        else if (!strcmp(k, "cap.ad")) cap_ad = atoi(v); else if (!strcmp(k, "cap.k")) cap_k = atoi(v); else if (!strcmp(k, "max_acc")) max_acc = atoi(v);
        else if (!strcmp(k, "T0")) T0 = atof(v); else if (!strcmp(k, "Tperiod_it")) Tperiod_it = atof(v);
        else if (!strcmp(k, "emit_current")) emit_current = atoi(v);
        else if (!strcmp(k, "pairs")) pairs_cap = atoi(v); else if (!strcmp(k, "fext")) fext = atoi(v);
        else if (!strcmp(k, "clock")) {
            if (!strcmp(v, "real")) cfg_clock = 0; else if (!strcmp(v, "cpu")) cfg_clock = 1; else if (!strcmp(v, "mono")) cfg_clock = 2;
            else { fprintf(stderr, "skel: clock must be real, cpu or mono\n"); return 2; }
        }
        else if (!strncmp(k, "mv.", 3)) {
            int hit = 0;
            for (int i = 0; i < 4; i++) if (!strcmp(k + 3, MVN[i])) { mvw[i] = atof(v); hit = 1; }
            if (!hit) { fprintf(stderr, "skel: unknown move %s\n", k); return 2; }
        }
        else { fprintf(stderr, "skel: unknown key %s\n", k); return 2; }
    }
    fclose(cf);
    seed_rng(seed);
    read_skel(in);
    if (!analyze()) { fprintf(stderr, "skel: start skeleton does not implement the target\n"); return 3; }
    double cur = objective(), bobj = cur;
    memcpy(best_ands, ands, sizeof(And) * K); best_K = K;
    printf("start K %d E %.0f obj %.6f\n", K, E_lin, cur);
    write_skel(out, "start");
    double t0 = now_s(), msum = 0; for (int i = 0; i < 4; i++) msum += mvw[i];
    long it = 0;
    while (1) {
        double t = now_s() - t0;
        if (t >= seconds || (iters >= 0 && it >= iters) || (max_acc > 0 && nacc >= max_acc)) break;
        it++;
        T = T0 > 0 ? T0 * (1.0 - fmod((double)it, Tperiod_it) / Tperiod_it) : 0;
        double r = rnd01() * msum; int mv = 0; while (mv < 3 && r >= mvw[mv]) { r -= mvw[mv]; mv++; }
        st_p[mv]++;
        int ok = mv == 0 ? mv_swap(cur) : mv == 1 ? mv_merge(cur) : mv == 2 ? mv_split(cur) : mv_perturb(cur);
        if (ok) {
            st_a[mv]++; cur = objective(); nacc++;
            if (cur < bobj - 1e-12) {
                st_i[mv]++; bobj = cur; memcpy(best_ands, ands, sizeof(And) * K); best_K = K;
                write_skel(out, "best");
                printf("best t %.3f it %ld mv %s K %d E %.0f obj %.6f\n", t, it, MVN[mv], K, E_lin, cur); fflush(stdout);
            }
        }
    }
    /* emit_current: return the drifted current skeleton when it has no more ANDs than the best
     * (its linear cost estimate may be worse; the gate level judges the real cost) */
    if (!(emit_current && K <= best_K)) { memcpy(ands, best_ands, sizeof(And) * best_K); K = best_K; }
    if (!analyze()) { fprintf(stderr, "skel: INTERNAL best infeasible\n"); return 4; }
    write_skel(out, "final");
    printf("final K %d E %.0f obj %.6f iters %ld seconds %.2f\n", K, E_lin, objective(), it, now_s() - t0);
    for (int i = 0; i < 4; i++) printf("move %s prop %ld acc %ld imp %ld\n", MVN[i], st_p[i], st_a[i], st_i[i]);
    return 0;
}
