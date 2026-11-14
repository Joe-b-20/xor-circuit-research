/* llay.c -- last-layer search by exact coordinate descent (track G).
 *
 * Given E (span of everything before the last layer: 1, x, prefix products), an operand space
 * O = span(o_1..o_r) with O inside E, targets T and K slots, find products q_j = l_j * m_j
 * (l_j, m_j in O) with  T  inside  E + span(q_1..q_K).  Score = deficit
 * d = dim(E + Q + T) - dim(E + Q).
 *
 * Move on slot j: B = E + span(q_i, i != j), tau = basis of (T + B)/B (d0 = dim).  For EVERY
 * l in O \ 0 (Gray code) the map m -> l*m mod B is linear (precomputed R[a][i] = o_a o_i mod B);
 * the m with l*m in (span tau + B) \ B are found by elimination.  One such (l, m) is drawn
 * uniformly (weighted over l by the number of good m) and put in slot j, so the deficit becomes
 * d0 - 1: an exact best re-choice over all ~2^(2r)/6 products of the slot.  If no product of O x O
 * reduces the deficit, the slot gets a random product with probability pjunk (else it is kept).
 *
 * usage: llay PROBLEM OUTPREFIX SEED SECONDS [pkick=0.02 pjunk=0.5 stall=2000 rr=0.3 report=10]
 * PROBLEM: 'NW npts' / nE + tables / nO + tables / nT + tables / K   (tables: NW hex words)
 * Output: OUTPREFIX.log, OUTPREFIX.best / .sol (K lines 'l m' as hex coefficient vectors over O).
 */
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef uint64_t u64;
#define W 4
#define MAXB 128
#define MAXO 24
#define MAXK 40

static int NW, nE, nO, nT, K;
static u64 Et[MAXB][W], Ot[MAXO][W], Tt[16][W];
static u64 Lc[MAXK], Mc[MAXK];        /* coefficient vectors over O */
static u64 Q[MAXK][W];

static u64 rs = 88172645463325252ULL;
static inline u64 rnd(void) { rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; return rs; }
static inline double urand(void) { return (rnd() >> 11) * (1.0 / 9007199254740992.0); }
static double now(void) { struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts); return ts.tv_sec + 1e-9 * ts.tv_nsec; }

typedef struct { int n; u64 v[MAXB + MAXK + 32][W]; int piv[MAXB + MAXK + 32]; } ech_t;

static inline int nz(const u64 *v) { for (int i = 0; i < NW; i++) if (v[i]) return 1; return 0; }
static inline int fbit(const u64 *v) { for (int i = 0; i < NW; i++) if (v[i]) return i * 64 + __builtin_ctzll(v[i]); return -1; }
static inline void ech_reduce(const ech_t *e, u64 *v) {
    for (int j = 0; j < e->n; j++) { int p = e->piv[j]; if ((v[p >> 6] >> (p & 63)) & 1) for (int i = 0; i < NW; i++) v[i] ^= e->v[j][i]; }
}
static inline int ech_add(ech_t *e, const u64 *vin) {
    u64 v[W]; memcpy(v, vin, sizeof v); ech_reduce(e, v);
    if (!nz(v)) return 0;
    memcpy(e->v[e->n], v, sizeof v); e->piv[e->n] = fbit(v); e->n++; return 1;
}

static void prod(u64 l, u64 m, u64 *out) {
    u64 a[W] = {0}, b[W] = {0};
    for (int i = 0; i < nO; i++) {
        if ((l >> i) & 1) for (int w = 0; w < NW; w++) a[w] ^= Ot[i][w];
        if ((m >> i) & 1) for (int w = 0; w < NW; w++) b[w] ^= Ot[i][w];
    }
    for (int w = 0; w < NW; w++) out[w] = a[w] & b[w];
}

static ech_t EB, ET;
static int deficit_all(void) {
    ech_t *e = &EB; e->n = 0;
    for (int i = 0; i < nE; i++) ech_add(e, Et[i]);
    for (int k = 0; k < K; k++) ech_add(e, Q[k]);
    int d = 0;
    for (int t = 0; t < nT; t++) d += ech_add(e, Tt[t]);
    return d;
}

static void rd(FILE *f, u64 *v) { for (int i = 0; i < NW; i++) if (fscanf(f, "%lx", &v[i]) != 1) { fprintf(stderr, "bad\n"); exit(1); } }
static void load(const char *p) {
    FILE *f = fopen(p, "r"); if (!f) { perror(p); exit(1); }
    int npts;
    if (fscanf(f, "%d %d", &NW, &npts) != 2) exit(1);
    if (fscanf(f, "%d", &nE) != 1 || nE > MAXB) exit(1);
    for (int i = 0; i < nE; i++) rd(f, Et[i]);
    if (fscanf(f, "%d", &nO) != 1 || nO > MAXO) exit(1);
    for (int i = 0; i < nO; i++) rd(f, Ot[i]);
    if (fscanf(f, "%d", &nT) != 1 || nT > 16) exit(1);
    for (int i = 0; i < nT; i++) rd(f, Tt[i]);
    if (fscanf(f, "%d", &K) != 1 || K > MAXK) exit(1);
    fclose(f);
}
static void dump(const char *path, int d, const char *tag) {
    FILE *f = fopen(path, "w"); if (!f) return;
    fprintf(f, "%s deficit %d K %d nO %d\n", tag, d, K, nO);
    for (int k = 0; k < K; k++) fprintf(f, "%lx %lx\n", Lc[k], Mc[k]);
    fclose(f);
}
static u64 rand_coef(void) { u64 m; do { m = rnd() & ((1ULL << nO) - 1); } while (!m); return m; }

static u64 R[MAXO][MAXO][W];

/* exact re-choice of slot j; returns 1 if a deficit-reducing product was installed */
static int rechoose(int j, int *d0out, long *nhit_out) {
    /* B = E + other products */
    EB.n = 0;
    for (int i = 0; i < nE; i++) ech_add(&EB, Et[i]);
    for (int k = 0; k < K; k++) if (k != j) ech_add(&EB, Q[k]);
    /* tau: T reduced mod B, echelon among themselves (separate structure for tags) */
    ET.n = 0;
    for (int t = 0; t < nT; t++) { u64 v[W]; memcpy(v, Tt[t], sizeof v); ech_reduce(&EB, v); ech_add(&ET, v); }
    int d0 = ET.n; *d0out = d0;
    if (d0 == 0) { *nhit_out = 0; return 0; }
    /* R[a][i] = o_a o_i mod B */
    for (int a = 0; a < nO; a++)
        for (int i = a; i < nO; i++) {
            u64 v[W]; for (int w = 0; w < NW; w++) v[w] = Ot[a][w] & Ot[i][w];
            ech_reduce(&EB, v);
            memcpy(R[a][i], v, sizeof v); memcpy(R[i][a], v, sizeof v);
        }
    u64 vv[MAXO][W]; memset(vv, 0, sizeof vv);
    u64 l = 0; u64 lim = 1ULL << nO;
    double total = 0; u64 bl = 0, bm = 0;
    for (u64 g = 1; g < lim; g++) {
        int a = __builtin_ctzll(g); l ^= 1ULL << a;
        for (int i = 0; i < nO; i++) for (int w = 0; w < NW; w++) vv[i][w] ^= R[a][i][w];
        /* rows: (v_i reduced by tau with tag, mcoef) eliminated among themselves */
        u64 rv[MAXO][W]; u64 rt[MAXO], rm[MAXO]; int rp[MAXO], nr = 0;
        u64 zt[MAXO], zm[MAXO]; int nzr = 0;
        for (int i = 0; i < nO; i++) {
            u64 v[W]; memcpy(v, vv[i], sizeof v);
            u64 tg = 0, mc = 1ULL << i;
            for (int q = 0; q < ET.n; q++) { int p = ET.piv[q]; if ((v[p >> 6] >> (p & 63)) & 1) { for (int w = 0; w < NW; w++) v[w] ^= ET.v[q][w]; tg ^= 1ULL << q; } }
            for (int q = 0; q < nr; q++) { int p = rp[q]; if ((v[p >> 6] >> (p & 63)) & 1) { for (int w = 0; w < NW; w++) v[w] ^= rv[q][w]; tg ^= rt[q]; mc ^= rm[q]; } }
            if (nz(v)) { memcpy(rv[nr], v, sizeof v); rt[nr] = tg; rm[nr] = mc; rp[nr] = fbit(v); nr++; }
            else { zt[nzr] = tg; zm[nzr] = mc; nzr++; }
        }
        if (nzr == 0) continue;
        /* rank of the tag vectors of the zero rows */
        u64 tb[16]; int ntb = 0;
        for (int q = 0; q < nzr; q++) {
            u64 t = zt[q];
            for (int s = 0; s < ntb; s++) if ((t ^ tb[s]) < t) t ^= tb[s];
            if (t) { tb[ntb++] = t; for (int s = ntb - 1; s > 0 && tb[s] > tb[s - 1]; s--) { u64 x = tb[s]; tb[s] = tb[s - 1]; tb[s - 1] = x; } }
        }
        if (ntb == 0) continue;
        double hits = ldexp(1.0, nzr) - ldexp(1.0, nzr - ntb);
        total += hits;
        if (urand() * total < hits) {
            /* random combination of zero rows with nonzero tag */
            u64 mt, mm;
            do {
                mt = 0; mm = 0;
                for (int q = 0; q < nzr; q++) if (rnd() & 1) { mt ^= zt[q]; mm ^= zm[q]; }
            } while (mt == 0);
            bl = l; bm = mm;
        }
    }
    *nhit_out = (long)total;
    if (total > 0) {
        Lc[j] = bl; Mc[j] = bm; prod(bl, bm, Q[j]);
        return 1;
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 5) { fprintf(stderr, "usage: llay PROBLEM OUT SEED SECONDS [k=v]\n"); return 1; }
    long seed = atol(argv[3]); double secs = atof(argv[4]);
    double pkick = 0.02, pjunk = 0.5, rr = 0.3, report = 10; long stall = 2000;
    const char *initf = NULL;
    for (int i = 5; i < argc; i++) {
        char k[64]; char vs[400];
        if (sscanf(argv[i], "%63[^=]=%399s", k, vs) != 2) continue;
        double v = atof(vs);
        if (!strcmp(k, "pkick")) pkick = v; else if (!strcmp(k, "pjunk")) pjunk = v;
        else if (!strcmp(k, "stall")) stall = (long)v; else if (!strcmp(k, "rr")) rr = v;
        else if (!strcmp(k, "report")) report = v; else if (!strcmp(k, "init")) initf = strdup(vs);
    }
    rs ^= (u64)seed * 0x9E3779B97F4A7C15ULL; for (int i = 0; i < 20; i++) rnd();
    load(argv[1]);
    char lp[512], bp[512], sp[512];
    snprintf(lp, sizeof lp, "%s.log", argv[2]); snprintf(bp, sizeof bp, "%s.best", argv[2]); snprintf(sp, sizeof sp, "%s.sol", argv[2]);
    FILE *lg = fopen(lp, "a");
    for (int k = 0; k < K; k++) { Lc[k] = rand_coef(); Mc[k] = rand_coef(); prod(Lc[k], Mc[k], Q[k]); }
    if (initf) {
        FILE *f = fopen(initf, "r"); char buf[256];
        if (f && fgets(buf, sizeof buf, f)) {
            for (int k = 0; k < K; k++) if (fscanf(f, "%lx %lx", &Lc[k], &Mc[k]) != 2) break; else prod(Lc[k], Mc[k], Q[k]);
            fclose(f);
        }
    }
    int cur = deficit_all(), best = cur;
    u64 bL[MAXK], bM[MAXK]; memcpy(bL, Lc, sizeof Lc); memcpy(bM, Mc, sizeof Mc);
    fprintf(lg, "start seed %ld deficit %d K %d nE %d nO %d nT %d\n", seed, cur, K, nE, nO, nT); fflush(lg);
    double t0 = now(), tl = t0; long step = 0, lastimp = 0, nrest = 0;
    while (now() - t0 < secs) {
        step++;
        int j = rnd() % K;
        if (urand() < pkick) {
            Lc[j] = rand_coef(); Mc[j] = rand_coef(); prod(Lc[j], Mc[j], Q[j]);
            cur = deficit_all();
        } else {
            int d0; long nh;
            u64 sl = Lc[j], sm = Mc[j]; u64 sq[W]; memcpy(sq, Q[j], sizeof sq);
            if (rechoose(j, &d0, &nh)) cur = d0 - 1;
            else {
                if (urand() < pjunk) { Lc[j] = rand_coef(); Mc[j] = rand_coef(); prod(Lc[j], Mc[j], Q[j]); }
                else { Lc[j] = sl; Mc[j] = sm; memcpy(Q[j], sq, sizeof sq); }
                cur = deficit_all();
            }
        }
        if (cur < best) {
            best = cur; lastimp = step; memcpy(bL, Lc, sizeof Lc); memcpy(bM, Mc, sizeof Mc);
            fprintf(lg, "t %.1f step %ld best %d\n", now() - t0, step, best); fflush(lg);
            dump(bp, best, "best");
            if (best == 0) { dump(sp, 0, "solution"); fprintf(lg, "SOLVED t %.1f step %ld\n", now() - t0, step); fclose(lg); return 0; }
        }
        if (step - lastimp > stall) {
            memcpy(Lc, bL, sizeof Lc); memcpy(Mc, bM, sizeof Mc);
            for (int k = 0; k < K; k++) { if (urand() < rr) { Lc[k] = rand_coef(); Mc[k] = rand_coef(); } prod(Lc[k], Mc[k], Q[k]); }
            cur = deficit_all(); lastimp = step; nrest++;
        }
        if (now() - tl > report) { tl = now(); fprintf(lg, "t %.0f step %ld cur %d best %d restarts %ld\n", tl - t0, step, cur, best, nrest); fflush(lg); }
    }
    fprintf(lg, "END t %.1f step %ld best %d restarts %ld\n", now() - t0, step, best, nrest);
    fclose(lg);
    return 2;
}
