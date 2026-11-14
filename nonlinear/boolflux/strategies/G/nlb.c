/* nlb.c -- direct nonlinear-basis local search (track G).
 *
 * A basis is an ordered list of K products p_i = A_i * B_i, where A_i, B_i are XORs of elements
 * (free wires f_0..f_{NF-1}, e.g. 1 and the inputs, and earlier products p_j, j < i), given as
 * bit masks over the element index (free wires first, then products).  Every element is in the
 * linear span.  Target groups: (weight w, targets T, addends Z); the deficit of a group is
 *     dim span(F, P, Z, T) - dim span(F, P, Z)
 * and the score is sum_g w_g * deficit_g.  Score 0 means: every target is an affine combination of
 * the free wires, products and addends.
 *
 * Moves (on non-fixed slots): bit flip of one operand (SA acceptance), and exact/sampled re-choice
 * of one slot: all 2-dim operand subspaces of the slot's allowed element space are evaluated
 * (sampled if the space is large) and one of the best is taken uniformly (plateau walk).
 *
 * usage: nlb PROBLEM OUTPREFIX SEED SECONDS [key=value ...]
 *   pe=0.2 (prob. of a re-choice move), T=0.3 (SA temperature), stall=20000 (moves without a new
 *   best before a partial restart), rr=0.3 (fraction of slots re-randomised on restart),
 *   exmax=8 (exact re-choice if the slot's allowed space has dim <= exmax, else ns samples),
 *   ns=3000, dens=0.25 (bit density of random operands), stop=1 (stop at score 0),
 *   init=1 (use the initial operands of the file; 0 = random start), report=10 (seconds)
 * Output: OUTPREFIX.log lines (time, steps, best score), OUTPREFIX.best (best state), and
 * OUTPREFIX.sol (state at score 0).
 */
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef uint64_t u64;
#define MAXW 4
#define MAXE 64
#define MAXV 160

static int NW;
static u64 LAST;            /* mask of the last word */
static int NF, K, NE;
static u64 tab[MAXE][MAXW];
static u64 opA[MAXE], opB[MAXE], allow[MAXE];
static int fixedslot[MAXE];
static int freeslots[MAXE], nfree;

typedef struct {
    double w;
    int nt, na;
    u64 t[64][MAXW];
    u64 a[MAXV][MAXW];
    int nb;                 /* precomputed echelon of free wires + addends */
    u64 b[MAXV][MAXW];
    int piv[MAXV];
} group_t;
static group_t *G;
static int NG;

/* ---------------- rng */
static u64 rs = 88172645463325252ULL;
static inline u64 rnd(void) { rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; return rs; }
static inline double urand(void) { return (rnd() >> 11) * (1.0 / 9007199254740992.0); }

static double now(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + 1e-9 * ts.tv_nsec;
}

/* ---------------- echelon */
static inline int is_zero(const u64 *v) {
    for (int i = 0; i < NW; i++) if (v[i]) return 0;
    return 1;
}
static inline int first_bit(const u64 *v) {
    for (int i = 0; i < NW; i++) if (v[i]) return i * 64 + __builtin_ctzll(v[i]);
    return -1;
}
/* reduce v by basis (b, piv, n); returns 1 if v became nonzero and was appended */
static inline int ech_insert(u64 (*b)[MAXW], int *piv, int *n, const u64 *vin) {
    u64 v[MAXW];
    for (int i = 0; i < NW; i++) v[i] = vin[i];
    for (int j = 0; j < *n; j++) {
        int p = piv[j];
        if ((v[p >> 6] >> (p & 63)) & 1)
            for (int i = 0; i < NW; i++) v[i] ^= b[j][i];
    }
    if (is_zero(v)) return 0;
    int p = first_bit(v);
    for (int i = 0; i < NW; i++) b[*n][i] = v[i];
    piv[*n] = p; (*n)++;
    return 1;
}

/* ---------------- evaluation */
static void compute_from(int s) {
    /* recompute product tables for slots s..K-1 */
    for (int k = s; k < K; k++) {
        int e = NF + k;
        u64 a[MAXW] = {0}, bb[MAXW] = {0};
        u64 m = opA[e];
        while (m) { int j = __builtin_ctzll(m); m &= m - 1; for (int i = 0; i < NW; i++) a[i] ^= tab[j][i]; }
        m = opB[e];
        while (m) { int j = __builtin_ctzll(m); m &= m - 1; for (int i = 0; i < NW; i++) bb[i] ^= tab[j][i]; }
        for (int i = 0; i < NW; i++) tab[e][i] = a[i] & bb[i];
        tab[e][NW - 1] &= LAST;
    }
}

static u64 wb[MAXV + MAXE + 64][MAXW];
static int wpiv[MAXV + MAXE + 64];

static double LAM = 0; static int DMAX = 20;
static inline int popw(const u64 *v) { int c = 0; for (int i = 0; i < NW; i++) c += __builtin_popcountll(v[i]); return c; }
/* min Hamming weight of t + span(wb[0..n-1]) by Gray-code enumeration */
static int coset_min(const u64 *t, int n) {
    u64 v[MAXW];
    for (int i = 0; i < NW; i++) v[i] = t[i];
    int best = popw(v);
    u64 lim = 1ULL << n;
    for (u64 g = 1; g < lim; g++) {
        int j = __builtin_ctzll(g);
        for (int i = 0; i < NW; i++) v[i] ^= wb[j][i];
        int c = popw(v);
        if (c < best) best = c;
    }
    return best;
}
static int NPTS;

/* ---------------- quadratic mode (n = 8): span(P) & {deg <= 2}, scored by residual ranks */
static int QMODE = 0; static double QLAM = 1.0, QMU = 1.0;
static u64 HMASK[4];
static int qpos[28], qi[28], qj[28];
static void mobius(u64 *f) {
    static const u64 M[6] = {0xAAAAAAAAAAAAAAAAULL, 0xCCCCCCCCCCCCCCCCULL, 0xF0F0F0F0F0F0F0F0ULL,
                             0xFF00FF00FF00FF00ULL, 0xFFFF0000FFFF0000ULL, 0xFFFFFFFF00000000ULL};
    for (int i = 0; i < 6; i++) { int s = 1 << i; for (int w = 0; w < 4; w++) f[w] ^= (f[w] << s) & M[i]; }
    f[1] ^= f[0]; f[3] ^= f[2];
    f[2] ^= f[0]; f[3] ^= f[1];
}
static void quad_init(void) {
    int c = 0;
    for (int w = 0; w < 4; w++) HMASK[w] = 0;
    for (int u = 0; u < 256; u++) {
        int pc = __builtin_popcount(u);
        if (pc >= 3) HMASK[u >> 6] |= 1ULL << (u & 63);
        if (pc == 2) { qpos[c] = u; qi[c] = __builtin_ctz(u); qj[c] = 31 - __builtin_clz(u); c++; }
    }
}
static inline uint32_t quad28(const u64 *anf) {
    uint32_t q = 0;
    for (int c = 0; c < 28; c++) if ((anf[qpos[c] >> 6] >> (qpos[c] & 63)) & 1) q |= 1u << c;
    return q;
}
static inline int rank_alt(uint32_t q) {
    uint8_t r[8] = {0};
    while (q) { int c = __builtin_ctz(q); q &= q - 1; r[qi[c]] |= 1 << qj[c]; r[qj[c]] |= 1 << qi[c]; }
    int rk = 0;
    for (int b = 0; b < 8; b++) {
        int p = -1;
        for (int i = rk; i < 8; i++) if ((r[i] >> b) & 1) { p = i; break; }
        if (p < 0) continue;
        uint8_t t = r[p]; r[p] = r[rk]; r[rk] = t;
        for (int i = 0; i < 8; i++) if (i != rk && ((r[i] >> b) & 1)) r[i] ^= r[rk];
        rk++;
    }
    return rk;
}
static uint32_t TQ[64];
static double BOUND = 1e18;
static double score_quad(int *defs) {
    u64 hb[MAXE][4]; uint32_t hq[MAXE]; int hp[MAXE], nh = 0;
    uint32_t p2[64]; int np2 = 0;
    for (int k = 0; k < K; k++) {
        u64 a[4]; memcpy(a, tab[NF + k], sizeof a);
        mobius(a);
        uint32_t q = quad28(a);
        u64 h[4]; for (int w = 0; w < 4; w++) h[w] = a[w] & HMASK[w];
        for (int j = 0; j < nh; j++) {
            int p = hp[j];
            if ((h[p >> 6] >> (p & 63)) & 1) { for (int w = 0; w < 4; w++) h[w] ^= hb[j][w]; q ^= hq[j]; }
        }
        if (h[0] | h[1] | h[2] | h[3]) {
            int p = first_bit(h); memcpy(hb[nh], h, sizeof h); hq[nh] = q; hp[nh] = p; nh++;
        } else {
            for (int j = 0; j < np2; j++) if ((q ^ p2[j]) < q) q ^= p2[j];
            if (q) {
                p2[np2++] = q;
                /* keep p2 sorted by leading bit descending for the min-reduction above */
                for (int j = np2 - 1; j > 0 && p2[j] > p2[j - 1]; j--) { uint32_t t = p2[j]; p2[j] = p2[j - 1]; p2[j - 1] = t; }
            }
        }
    }
    /* deficit */
    uint32_t e[64]; int ne = np2; memcpy(e, p2, sizeof(uint32_t) * np2);
    int d = 0;
    for (int t = 0; t < G[0].nt; t++) {
        uint32_t q = TQ[t];
        for (int j = 0; j < ne; j++) if ((q ^ e[j]) < q) q ^= e[j];
        if (q) {
            e[ne++] = q; d++;
            for (int j = ne - 1; j > 0 && e[j] > e[j - 1]; j--) { uint32_t tt = e[j]; e[j] = e[j - 1]; e[j - 1] = tt; }
        }
    }
    double fine = 0;
    if (QMU * d > BOUND + 1e-9) { if (defs) defs[0] = d; return QMU * d + 1000; }
    if (QLAM > 0) {
        for (int t = 0; t < G[0].nt; t++) {
            uint32_t v = TQ[t]; int best = rank_alt(v);
            uint32_t lim = 1u << np2;
            for (uint32_t g = 1; g < lim && best > 0; g++) {
                v ^= p2[__builtin_ctz(g)];
                int r = rank_alt(v); if (r < best) best = r;
            }
            fine += best / 2;
        }
    }
    if (defs) defs[0] = d;
    return QMU * d + QLAM * fine;
}

static double score_groups(int *defs) {
    if (QMODE) return score_quad(defs);
    double sc = 0;
    for (int g = 0; g < NG; g++) {
        group_t *gr = &G[g];
        int n = gr->nb;
        memcpy(wb, gr->b, sizeof(u64) * MAXW * n);
        memcpy(wpiv, gr->piv, sizeof(int) * n);
        for (int k = 0; k < K; k++) ech_insert(wb, wpiv, &n, tab[NF + k]);
        int d = 0;
        int n0 = n;
        if (LAM > 0 && n0 <= DMAX) {
            double ds = 0;
            for (int t = 0; t < gr->nt; t++) ds += coset_min(gr->t[t], n0);
            sc += LAM * gr->w * ds / NPTS;
        }
        for (int t = 0; t < gr->nt; t++) d += ech_insert(wb, wpiv, &n, gr->t[t]);
        if (defs) defs[g] = d;
        sc += gr->w * d;
    }
    return sc;
}

/* ---------------- io */
static void read_tab(FILE *f, u64 *v) {
    for (int i = 0; i < NW; i++) if (fscanf(f, "%lx", &v[i]) != 1) { fprintf(stderr, "bad table\n"); exit(1); }
}
static void load(const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) { perror(path); exit(1); }
    int npts;
    if (fscanf(f, "%d %d", &NW, &npts) != 2) exit(1);
    NPTS = npts;
    LAST = (npts % 64) ? ((1ULL << (npts % 64)) - 1) : ~0ULL;
    if (fscanf(f, "%d", &NF) != 1) exit(1);
    for (int e = 0; e < NF; e++) read_tab(f, tab[e]);
    if (fscanf(f, "%d", &K) != 1) exit(1);
    NE = NF + K;
    if (NE > MAXE) { fprintf(stderr, "too many elements\n"); exit(1); }
    for (int k = 0; k < K; k++) {
        int e = NF + k;
        if (fscanf(f, "%d %lx %lx %lx", &fixedslot[e], &allow[e], &opA[e], &opB[e]) != 4) exit(1);
        u64 below = (e >= 64) ? ~0ULL : ((1ULL << e) - 1);
        allow[e] &= below; opA[e] &= below; opB[e] &= below;
        if (!fixedslot[e]) freeslots[nfree++] = e;
    }
    if (fscanf(f, "%d", &NG) != 1) exit(1);
    G = calloc(NG, sizeof(group_t));
    for (int g = 0; g < NG; g++) {
        group_t *gr = &G[g];
        if (fscanf(f, "%lf %d %d", &gr->w, &gr->nt, &gr->na) != 3) exit(1);
        if (gr->nt > 64 || gr->na + NF > MAXV) { fprintf(stderr, "group too big\n"); exit(1); }
        for (int t = 0; t < gr->nt; t++) read_tab(f, gr->t[t]);
        for (int t = 0; t < gr->na; t++) read_tab(f, gr->a[t]);
        gr->nb = 0;
        for (int e = 0; e < NF; e++) ech_insert(gr->b, gr->piv, &gr->nb, tab[e]);
        for (int t = 0; t < gr->na; t++) ech_insert(gr->b, gr->piv, &gr->nb, gr->a[t]);
    }
    fclose(f);
}

static void dump(const char *path, double sc, const char *tag) {
    FILE *f = fopen(path, "w");
    if (!f) return;
    fprintf(f, "%s score %.4f K %d NF %d\n", tag, sc, K, NF);
    for (int k = 0; k < K; k++) fprintf(f, "%lx %lx\n", opA[NF + k], opB[NF + k]);
    fclose(f);
}

/* ---------------- helpers */
static inline u64 rand_mask(u64 al, double dens) {
    u64 m = 0, a = al;
    while (a) { int j = __builtin_ctzll(a); a &= a - 1; if (urand() < dens) m |= 1ULL << j; }
    return m;
}
static inline int nonconst(u64 m) { return (m & ~1ULL) != 0; }   /* element 0 = constant 1 */
static inline u64 rand_operand(u64 al, double dens) {
    u64 m;
    int tries = 0;
    do { m = rand_mask(al, dens); } while (!nonconst(m) && ++tries < 100);
    if (!nonconst(m)) { u64 a = al & ~1ULL; if (a) m = a & (~a + 1); }
    return m;
}
/* map a coefficient vector c over the allowed elements (bit list) to an element mask */
static inline u64 expand(u64 c, const int *bits) {
    u64 m = 0;
    while (c) { int j = __builtin_ctzll(c); c &= c - 1; m |= 1ULL << bits[j]; }
    return m;
}

int main(int argc, char **argv) {
    if (argc < 5) { fprintf(stderr, "usage: nlb PROBLEM OUTPREFIX SEED SECONDS [k=v]\n"); return 1; }
    const char *prob = argv[1], *out = argv[2];
    long seed = atol(argv[3]);
    double secs = atof(argv[4]);
    double pe = 0.2, T = 0.3, rr = 0.3, dens = 0.25;
    long stall = 20000, ns = 3000;
    int exmax = 8, stop = 1, init = 1;
    double report = 10;
    for (int i = 5; i < argc; i++) {
        char k[64]; double v;
        if (sscanf(argv[i], "%63[^=]=%lf", k, &v) != 2) continue;
        if (!strcmp(k, "pe")) pe = v; else if (!strcmp(k, "T")) T = v;
        else if (!strcmp(k, "stall")) stall = (long)v; else if (!strcmp(k, "rr")) rr = v;
        else if (!strcmp(k, "exmax")) exmax = (int)v; else if (!strcmp(k, "ns")) ns = (long)v;
        else if (!strcmp(k, "dens")) dens = v; else if (!strcmp(k, "stop")) stop = (int)v;
        else if (!strcmp(k, "init")) init = (int)v;
        else if (!strcmp(k, "q")) QMODE = (int)v; else if (!strcmp(k, "qlam")) QLAM = v; else if (!strcmp(k, "qmu")) QMU = v;
        else if (!strcmp(k, "lam")) LAM = v; else if (!strcmp(k, "dmax")) DMAX = (int)v; else if (!strcmp(k, "report")) report = v;
    }
    rs ^= (u64)seed * 0x9E3779B97F4A7C15ULL; for (int i = 0; i < 20; i++) rnd();
    load(prob);
    if (QMODE) {
        if (NW != 4 || NG != 1) { fprintf(stderr, "q mode needs n = 8 and one group\n"); return 1; }
        quad_init();
        for (int t = 0; t < G[0].nt; t++) {
            u64 a[4]; memcpy(a, G[0].t[t], sizeof a); mobius(a);
            if ((a[0] & HMASK[0]) | (a[1] & HMASK[1]) | (a[2] & HMASK[2]) | (a[3] & HMASK[3])) { fprintf(stderr, "target %d not quadratic\n", t); return 1; }
            TQ[t] = quad28(a);
        }
    }
    char lp[512], bp[512], sp[512];
    snprintf(lp, sizeof lp, "%s.log", out); snprintf(bp, sizeof bp, "%s.best", out);
    snprintf(sp, sizeof sp, "%s.sol", out);
    FILE *lg = fopen(lp, "a");
    if (!init)
        for (int q = 0; q < nfree; q++) {
            int e = freeslots[q];
            opA[e] = rand_operand(allow[e], dens); opB[e] = rand_operand(allow[e], dens);
        }
    compute_from(0);
    int defs[64];
    double cur = score_groups(defs), best = cur;
    u64 bA[MAXE], bB[MAXE];
    memcpy(bA, opA, sizeof opA); memcpy(bB, opB, sizeof opB);
    double t0 = now(), tlast = t0;
    long step = 0, lastimp = 0, nrestart = 0;
    fprintf(lg, "start seed %ld score %.3f K %d NF %d free %d groups %d\n", seed, cur, K, NF, nfree, NG);
    fflush(lg);
    if (nfree == 0) { fprintf(lg, "no free slots\n"); return 0; }
    int bits[64];
    while (1) {
        step++;
        int e = freeslots[rnd() % nfree];
        int s = e - NF;
        if (urand() < pe) {
            /* re-choice of slot e */
            int m = 0; u64 a = allow[e] & ~1ULL;
            while (a) { bits[m++] = __builtin_ctzll(a); a &= a - 1; }
            if (m < 2) continue;
            u64 sa = opA[e], sb = opB[e];
            double bestv = 1e18; long nbest = 0; u64 cA = sa, cB = sb;
            BOUND = 1e18;
            if (m <= exmax) {
                u64 lim = 1ULL << m;
                for (u64 x = 1; x < lim; x++)
                    for (u64 y = x + 1; y < lim; y++) {
                        if ((x ^ y) < y) continue;
                        opA[e] = expand(x, bits); opB[e] = expand(y, bits);
                        compute_from(s);
                        double v = score_groups(NULL);
                        if (v < bestv - 1e-9) { bestv = v; nbest = 1; cA = opA[e]; cB = opB[e]; BOUND = bestv; }
                        else if (v < bestv + 1e-9) { nbest++; if (rnd() % nbest == 0) { cA = opA[e]; cB = opB[e]; } }
                    }
            } else {
                for (long q = 0; q < ns; q++) {
                    u64 x = rand_operand(allow[e], dens), y = rand_operand(allow[e], dens);
                    if (x == y) continue;
                    opA[e] = x; opB[e] = y;
                    compute_from(s);
                    double v = score_groups(NULL);
                    if (v < bestv - 1e-9) { bestv = v; nbest = 1; cA = x; cB = y; BOUND = bestv; }
                    else if (v < bestv + 1e-9) { nbest++; if (rnd() % nbest == 0) { cA = x; cB = y; } }
                }
                /* keep current if not worse */
                BOUND = 1e18;
                opA[e] = sa; opB[e] = sb; compute_from(s);
                double v0 = score_groups(NULL);
                if (v0 <= bestv + 1e-9 && urand() < 0.5) { bestv = v0; cA = sa; cB = sb; }
            }
            BOUND = 1e18;
            opA[e] = cA; opB[e] = cB; compute_from(s);
            cur = score_groups(defs);
        } else {
            u64 sa = opA[e], sb = opB[e];
            u64 al = allow[e];
            int na = __builtin_popcountll(al);
            if (na == 0) continue;
            int pick = rnd() % na; u64 a = al;
            for (int q = 0; q < pick; q++) a &= a - 1;
            u64 bit = a & (~a + 1);
            if (rnd() & 1) opA[e] ^= bit; else opB[e] ^= bit;
            if (!nonconst(opA[e]) || !nonconst(opB[e]) || opA[e] == opB[e]) { opA[e] = sa; opB[e] = sb; continue; }
            compute_from(s);
            double v = score_groups(defs);
            if (v <= cur + 1e-9 || (T > 0 && urand() < exp(-(v - cur) / T))) cur = v;
            else { opA[e] = sa; opB[e] = sb; compute_from(s); }
        }
        if (cur < best - 1e-9) {
            best = cur; lastimp = step;
            memcpy(bA, opA, sizeof opA); memcpy(bB, opB, sizeof opB);
            fprintf(lg, "t %.1f step %ld best %.3f defs", now() - t0, step, best);
            for (int g = 0; g < NG; g++) fprintf(lg, " %d", defs[g]);
            fprintf(lg, "\n"); fflush(lg);
            dump(bp, best, "best");
            int solved = 1; for (int g = 0; g < NG; g++) if (defs[g]) solved = 0;
            if (solved) {
                dump(sp, best, "solution");
                fprintf(lg, "SOLVED t %.2f step %ld restarts %ld\n", now() - t0, step, nrestart); fflush(lg);
                if (stop) return 0;
            }
        }
        if (step - lastimp > stall) {
            /* partial restart from the best state */
            memcpy(opA, bA, sizeof opA); memcpy(opB, bB, sizeof opB);
            for (int q = 0; q < nfree; q++)
                if (urand() < rr) {
                    int f2 = freeslots[q];
                    opA[f2] = rand_operand(allow[f2], dens); opB[f2] = rand_operand(allow[f2], dens);
                }
            compute_from(0); cur = score_groups(defs);
            lastimp = step; nrestart++;
        }
        if ((step & 15) == 0) {
            double tn = now();
            if (tn - t0 > secs) break;
            if (tn - tlast > report) {
                tlast = tn;
                fprintf(lg, "t %.0f step %ld cur %.3f best %.3f restarts %ld\n", tn - t0, step, cur, best, nrestart);
                fflush(lg);
            }
        }
    }
    fprintf(lg, "END t %.1f step %ld best %.3f restarts %ld\n", now() - t0, step, best, nrestart);
    fclose(lg);
    return 2;
}
