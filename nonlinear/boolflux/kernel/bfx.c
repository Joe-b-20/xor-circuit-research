/* bfx.c -- BoolFlux search kernel.
 *
 * Searches for cheaper circuits of a complete multi-output Boolean function, starting from a
 * correct circuit.  Every state the search visits is a correct circuit: a move replaces the
 * function of ONE signal s by a new expression (0..3 new gates over existing signals) that agrees
 * with s on s's exact care set (the input patterns on which flipping s changes some output,
 * computed from the complete truth table), so the outputs are unchanged on every input.  The
 * kernel re-simulates every candidate on all 2^n inputs and aborts if an output ever differs
 * from the target (a guard against bugs, not part of the method).
 *
 * Gates are 2-input Boolean functions encoded by their 4-bit truth table op, with
 * f(a,b) = (op >> ((a<<1)|b)) & 1:   AND=8 OR=14 XOR=6 XNOR=9 NAND=7 NOR=1 ANDN=4 (a&~b)
 * ORN=13 (a|~b) NOT=3 (~a, unary, b==a).  The gate library and costs come from the config.
 *
 * Usage: bfx CONFIG            (key value lines; see parse_config)
 *        bfx --stats CIRCUIT   (print metrics of a circuit file under default unit costs)
 *
 * Circuit file:  "n N" / "m M" / "g G" / G lines "op a b" / "o s_0 ... s_{M-1}".
 * Signals 0..N-1 are inputs (input i is bit N-1-i of the pattern index: msb first),
 * signal N+j is gate j; gate operands must be smaller signal numbers.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <time.h>

typedef uint64_t u64;
#define MAXN 16
#define MAXM 64
#define GCAP 20000
#define INF_LVL 1000000

static int N, M, W;
static u64 LASTMASK;

/* ------------------------------------------------------------------ ops */
static double op_cost[16];
static int op_ok[16];          /* allowed in library */
static int op_gdw[16];         /* gate-depth weight */
static inline int op_nl(int op) { return __builtin_popcount(op) & 1; }   /* AND-like */
static inline int op_unary(int op) { return op == 3; }
static inline int op_sym(int op) { return ((op >> 1) & 1) == ((op >> 2) & 1); }
static inline int op_adw(int op) { return op_nl(op); }

static inline u64 apply(int op, u64 a, u64 b) {
    switch (op) {
    case 8: return a & b;   case 6: return a ^ b;   case 9: return ~(a ^ b);
    case 14: return a | b;  case 7: return ~(a & b); case 1: return ~(a | b);
    case 4: return a & ~b;  case 2: return ~a & b;  case 13: return a | ~b;
    case 11: return ~a | b; case 3: return ~a;      case 5: return ~b;
    case 12: return a;      case 10: return b;      case 0: return 0;
    default: return ~0ULL;
    }
}
static inline void eval_gate(int op, const u64 *a, const u64 *b, u64 *o) {
    for (int w = 0; w < W; w++) o[w] = apply(op, a[w], b[w]);
}
static inline u64 wmask(int w) { return w == W - 1 ? LASTMASK : ~0ULL; }

/* ------------------------------------------------------------------ rng */
static u64 rs[4];
static inline u64 rotl(u64 x, int k) { return (x << k) | (x >> (64 - k)); }
static u64 rnd(void) {
    u64 r = rotl(rs[1] * 5, 7) * 9, t = rs[1] << 17;
    rs[2] ^= rs[0]; rs[3] ^= rs[1]; rs[1] ^= rs[2]; rs[0] ^= rs[3]; rs[2] ^= t; rs[3] = rotl(rs[3], 45);
    return r;
}
static void seed_rng(u64 s) {
    for (int i = 0; i < 4; i++) {
        s += 0x9E3779B97F4A7C15ULL; u64 z = s;
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL; z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
        rs[i] = z ^ (z >> 31);
    }
}
static inline int rndint(int n) { return (int)((rnd() >> 11) % (u64)n); }
static inline double rnd01(void) { return (rnd() >> 11) * (1.0 / 9007199254740992.0); }

/* ------------------------------------------------------------------ circuits */
typedef struct { unsigned char op; int a, b; } Gate;
typedef struct { int ng; Gate *g; int out[MAXM]; } Circ;

static void circ_alloc(Circ *c) { c->ng = 0; c->g = calloc(GCAP, sizeof(Gate)); }   /* zeroed padding: skip_noop memcmp */
static void circ_copy(Circ *d, const Circ *s) {
    d->ng = s->ng; memcpy(d->g, s->g, sizeof(Gate) * s->ng); memcpy(d->out, s->out, sizeof(int) * M);
}

static u64 *INV;   /* input tables N*W */
static u64 *TGT;   /* target outputs M*W */

static void sim(const Circ *c, u64 *V) {
    memcpy(V, INV, sizeof(u64) * N * W);
    for (int j = 0; j < c->ng; j++) {
        const Gate *g = &c->g[j];
        eval_gate(g->op, V + (size_t)g->a * W, V + (size_t)g->b * W, V + (size_t)(N + j) * W);
    }
}
static int outputs_ok(const Circ *c, const u64 *V) {
    for (int k = 0; k < M; k++) {
        const u64 *o = V + (size_t)c->out[k] * W, *t = TGT + (size_t)k * W;
        for (int w = 0; w < W; w++) if ((o[w] ^ t[w]) & wmask(w)) return 0;
    }
    return 1;
}

typedef struct { double cost, obj; int g, a, gd, ad, feas, viol; } Metrics;
#define VIOL_PENALTY 1e6
static double w_cost = 1, w_g = 0, w_a = 0, w_gd = 0, w_ad = 0;
static int cap_gd = -1, cap_ad = -1, cap_a = -1;

static void levels(const Circ *c, int *lg, int *la) {
    for (int i = 0; i < N; i++) lg[i] = la[i] = 0;
    for (int j = 0; j < c->ng; j++) {
        const Gate *g = &c->g[j];
        int x = lg[g->a] > lg[g->b] ? lg[g->a] : lg[g->b];
        int y = la[g->a] > la[g->b] ? la[g->a] : la[g->b];
        lg[N + j] = x + op_gdw[g->op]; la[N + j] = y + op_adw(g->op);
    }
}
static int *LG_tmp, *LA_tmp, *HG_tmp, *HA_tmp;
static void metrics(const Circ *c, Metrics *m) {
    levels(c, LG_tmp, LA_tmp);
    m->cost = 0; m->g = c->ng; m->a = 0; m->gd = 0; m->ad = 0;
    for (int j = 0; j < c->ng; j++) { m->cost += op_cost[c->g[j].op]; m->a += op_nl(c->g[j].op); }
    for (int k = 0; k < M; k++) {
        if (LG_tmp[c->out[k]] > m->gd) m->gd = LG_tmp[c->out[k]];
        if (LA_tmp[c->out[k]] > m->ad) m->ad = LA_tmp[c->out[k]];
    }
    m->viol = (cap_gd >= 0 && m->gd > cap_gd ? m->gd - cap_gd : 0) + (cap_ad >= 0 && m->ad > cap_ad ? m->ad - cap_ad : 0)
            + (cap_a >= 0 && m->a > cap_a ? m->a - cap_a : 0);
    m->feas = m->viol == 0;
    /* A state that violates a cap is penalised, so a start outside the caps is repaired first.
     * Besides the largest excess, the penalty counts, over all gates, by how much the longest
     * path through the gate exceeds the cap: shortening any one too-deep path is progress. */
    double vsum = 0;
    if (m->viol && (cap_gd >= 0 || cap_ad >= 0)) {
        int tot = N + c->ng;
        for (int v = 0; v < tot; v++) { HG_tmp[v] = -INF_LVL; HA_tmp[v] = -INF_LVL; }
        for (int k = 0; k < M; k++) { HG_tmp[c->out[k]] = 0; HA_tmp[c->out[k]] = 0; }
        for (int j = c->ng - 1; j >= 0; j--) {
            const Gate *g = &c->g[j]; int v = N + j;
            int hg = HG_tmp[v] + op_gdw[g->op], ha = HA_tmp[v] + op_adw(g->op);
            if (hg > HG_tmp[g->a]) HG_tmp[g->a] = hg;
            if (ha > HA_tmp[g->a]) HA_tmp[g->a] = ha;
            if (hg > HG_tmp[g->b]) HG_tmp[g->b] = hg;
            if (ha > HA_tmp[g->b]) HA_tmp[g->b] = ha;
        }
        for (int j = 0; j < c->ng; j++) {
            int v = N + j;
            if (cap_gd >= 0 && LG_tmp[v] + HG_tmp[v] > cap_gd) vsum += LG_tmp[v] + HG_tmp[v] - cap_gd;
            if (cap_ad >= 0 && LA_tmp[v] + HA_tmp[v] > cap_ad) vsum += LA_tmp[v] + HA_tmp[v] - cap_ad;
        }
    }
    m->obj = w_cost * m->cost + w_g * m->g + w_a * m->a + w_gd * m->gd + w_ad * m->ad
             + VIOL_PENALTY * m->viol + 1e4 * vsum;
}

/* Rebuild: apply remap (signal -> signal, may chain) to every operand and output of c plus the
 * appended gates `add` (signals N+c->ng+t), keep only gates reachable from the outputs, order
 * them topologically (DFS post-order), simplify gates with equal operands, structurally hash.
 * Returns 0, or -1 if a gate became constant (not representable) or a cycle was found. */
static Gate *RB_g; static int *RB_map, *RB_mark, *RB_new, *RB_stk, *RB_ht; static int RB_htsize;
static inline int rb_resolve(int x) { while (RB_map[x] != x) x = RB_map[x]; return x; }
static inline u64 gkey(int op, int a, int b) { return ((u64)op << 56) ^ ((u64)a << 28) ^ (u64)b; }
static int rebuild(const Circ *c, int s, int r, const Gate *add, int nadd, const int *remap, Circ *o, int strash) {
    int tot = N + c->ng + nadd;
    for (int v = 0; v < tot; v++) RB_map[v] = remap ? remap[v] : v;
    if (s >= 0) RB_map[s] = r;
    for (int j = 0; j < c->ng; j++) RB_g[j] = c->g[j];
    for (int t = 0; t < nadd; t++) RB_g[c->ng + t] = add[t];
    memset(RB_mark, 0, sizeof(int) * tot);
    for (int i = 0; i < N; i++) { RB_new[i] = i; RB_mark[i] = 2; }
    int hts = 64; while (hts < 2 * tot) hts <<= 1;
    if (hts > RB_htsize) hts = RB_htsize;
    if (strash) for (int i = 0; i < hts; i++) RB_ht[i] = -1;
    o->ng = 0;
    for (int k = 0; k < M; k++) {
        int root = rb_resolve(c->out[k]);
        if (RB_mark[root] != 2) {
            int sp = 0; RB_stk[sp++] = root;
            while (sp) {
                int v = RB_stk[sp - 1];
                if (RB_mark[v] == 2) { sp--; continue; }
                Gate *g = &RB_g[v - N];
                int a = rb_resolve(g->a), b = rb_resolve(g->b);
                if (RB_mark[v] == 0) {
                    RB_mark[v] = 1;
                    if (RB_mark[a] == 1 || RB_mark[b] == 1) return -1;   /* cycle */
                    if (RB_mark[a] == 0) RB_stk[sp++] = a;
                    if (RB_mark[b] == 0 && b != a) RB_stk[sp++] = b;
                    continue;
                }
                if (RB_mark[a] != 2 || RB_mark[b] != 2) {   /* a child still pending */
                    if (RB_mark[a] == 1 || RB_mark[b] == 1) return -1;
                    if (RB_mark[a] == 0) RB_stk[sp++] = a;
                    if (RB_mark[b] == 0) RB_stk[sp++] = b;
                    continue;
                }
                sp--;
                int op = g->op, na = RB_new[a], nb = RB_new[b], res;
                if (op_unary(op)) nb = na;
                else if (na == nb) {          /* f(x,x) */
                    int v0 = op & 1, v1 = (op >> 3) & 1;
                    if (v0 == v1) return -1;                       /* constant */
                    if (!v0) { RB_new[v] = na; RB_mark[v] = 2; continue; }  /* = x */
                    if (op_ok[3]) op = 3;                           /* = ~x */
                }
                if (!op_unary(op) && op_sym(op) && na > nb) { int t = na; na = nb; nb = t; }
                res = -1;
                if (strash) {
                    u64 key = gkey(op, na, nb); unsigned h = (unsigned)((key * 0x9E3779B97F4A7C15ULL) >> 40) & (hts - 1);
                    while (RB_ht[h] >= 0) {
                        Gate *e = &o->g[RB_ht[h]];
                        if (e->op == op && e->a == na && e->b == nb) { res = N + RB_ht[h]; break; }
                        h = (h + 1) & (hts - 1);
                    }
                    if (res < 0) RB_ht[h] = o->ng;
                }
                if (res < 0) {
                    if (o->ng >= GCAP) return -1;
                    o->g[o->ng].op = op; o->g[o->ng].a = na; o->g[o->ng].b = nb;
                    res = N + o->ng; o->ng++;
                }
                RB_new[v] = res; RB_mark[v] = 2;
            }
        }
        o->out[k] = RB_new[root];
    }
    return 0;
}

/* ------------------------------------------------------------------ config */
static char cfg_in[1024], cfg_out[1024], cfg_trace[1024];
static double Tperiod_it = 0, stall_it = 0;
static double cfg_seconds = 10, T0 = 0.0, Tperiod = 30.0, stall = 60.0, max_excess = 1e18, uphill = 1.0;
static u64 cfg_seed = 1;
#define NMOVES 3
static double mv_w[NMOVES] = {1, 1, 1};
static const char *MVNAME[NMOVES] = {"resub1", "resub2", "resub3"};
static int dmax = 200, pdiv = 90, nl_samples = 12, cand_cap = 40, use_fraig = 1;
static int use_neutral = 1, use_odc = 1, linear_mode = 0;   /* ablation switches; linear: see main */
static int skip_noop = 1;    /* v2: a candidate whose rebuilt circuit equals the current one is no move */
static long st_noop;
static char cfg_tracemoves[1024];
static long max_iters = -1;

static void die(const char *m) { fprintf(stderr, "bfx: %s\n", m); exit(2); }

static void parse_config(const char *path) {
    FILE *f = fopen(path, "r"); if (!f) die("cannot open config");
    char k[256], v[1024];
    for (int i = 0; i < 16; i++) { op_ok[i] = 0; op_cost[i] = 0; op_gdw[i] = 1; }
    while (fscanf(f, "%255s %1023s", k, v) == 2) {
        if (k[0] == '#') { int ch; while ((ch = fgetc(f)) != '\n' && ch != EOF); continue; }
        if (!strcmp(k, "in")) strcpy(cfg_in, v);
        else if (!strcmp(k, "out")) strcpy(cfg_out, v);
        else if (!strcmp(k, "trace")) strcpy(cfg_trace, v);
        else if (!strcmp(k, "seconds")) cfg_seconds = atof(v);
        else if (!strcmp(k, "iters")) max_iters = atol(v);
        else if (!strcmp(k, "seed")) cfg_seed = strtoull(v, 0, 10);
        else if (!strncmp(k, "cost.", 5)) { int op = atoi(k + 5); op_ok[op] = 1; op_cost[op] = atof(v); }
        else if (!strncmp(k, "gdw.", 4)) op_gdw[atoi(k + 4)] = atoi(v);
        else if (!strcmp(k, "w.cost")) w_cost = atof(v);
        else if (!strcmp(k, "w.g")) w_g = atof(v);
        else if (!strcmp(k, "w.a")) w_a = atof(v);
        else if (!strcmp(k, "w.gd")) w_gd = atof(v);
        else if (!strcmp(k, "w.ad")) w_ad = atof(v);
        else if (!strcmp(k, "cap.gd")) cap_gd = atoi(v);
        else if (!strcmp(k, "cap.ad")) cap_ad = atoi(v);
        else if (!strcmp(k, "cap.a")) cap_a = atoi(v);
        else if (!strcmp(k, "T0")) T0 = atof(v);
        else if (!strcmp(k, "Tperiod")) Tperiod = atof(v);
        else if (!strcmp(k, "stall")) stall = atof(v);
        else if (!strcmp(k, "Tperiod_it")) Tperiod_it = atof(v);
        else if (!strcmp(k, "stall_it")) stall_it = atof(v);
        else if (!strcmp(k, "max_excess")) max_excess = atof(v);
        else if (!strcmp(k, "uphill")) uphill = atof(v);
        else if (!strncmp(k, "mv.", 3)) { for (int i = 0; i < NMOVES; i++) if (!strcmp(k + 3, MVNAME[i])) mv_w[i] = atof(v); }
        else if (!strcmp(k, "dmax")) dmax = atoi(v);
        else if (!strcmp(k, "pdiv")) pdiv = atoi(v);
        else if (!strcmp(k, "nl_samples")) nl_samples = atoi(v);
        else if (!strcmp(k, "cand_cap")) cand_cap = atoi(v);
        else if (!strcmp(k, "fraig")) use_fraig = atoi(v);
        else if (!strcmp(k, "neutral")) use_neutral = atoi(v);
        else if (!strcmp(k, "skip_noop")) skip_noop = atoi(v);
        else if (!strcmp(k, "odc")) use_odc = atoi(v);
        else if (!strcmp(k, "linear")) linear_mode = atoi(v);
        else if (!strcmp(k, "tracemoves")) strcpy(cfg_tracemoves, v);
        else { fprintf(stderr, "bfx: unknown key %s\n", k); exit(2); }
    }
    fclose(f);
}

static void read_circuit(const char *path, Circ *c) {
    FILE *f = fopen(path, "r"); if (!f) die("cannot open circuit");
    int ng;
    if (fscanf(f, " n %d m %d g %d", &N, &M, &ng) != 3) die("bad circuit header");
    if (N < 1 || N > MAXN || M < 1 || M > MAXM || ng > GCAP) die("circuit too large");
    W = N >= 6 ? 1 << (N - 6) : 1;
    LASTMASK = N >= 6 ? ~0ULL : ((1ULL << (1 << N)) - 1);
    c->ng = ng;
    for (int j = 0; j < ng; j++) {
        int op, a, b;
        if (fscanf(f, "%d %d %d", &op, &a, &b) != 3) die("bad gate line");
        if (op < 0 || op > 15 || a < 0 || b < 0 || a >= N + j || b >= N + j) die("bad gate");
        if (op_unary(op)) b = a;
        c->g[j].op = op; c->g[j].a = a; c->g[j].b = b;
    }
    char tag[8]; if (fscanf(f, "%7s", tag) != 1 || strcmp(tag, "o")) die("bad output line");
    for (int k = 0; k < M; k++) if (fscanf(f, "%d", &c->out[k]) != 1 || c->out[k] < 0 || c->out[k] >= N + ng) die("bad output");
    fclose(f);
}
static void write_circuit(const char *path, const Circ *c, const Metrics *m, const char *note) {
    char tmp[1100]; snprintf(tmp, sizeof tmp, "%s.tmp", path);
    FILE *f = fopen(tmp, "w"); if (!f) die("cannot write circuit");
    fprintf(f, "n %d\nm %d\ng %d\n", N, M, c->ng);
    for (int j = 0; j < c->ng; j++) fprintf(f, "%d %d %d\n", c->g[j].op, c->g[j].a, c->g[j].b);
    fprintf(f, "o"); for (int k = 0; k < M; k++) fprintf(f, " %d", c->out[k]); fprintf(f, "\n");
    fprintf(f, "# cost %.4f G %d A %d GD %d AD %d %s\n", m->cost, m->g, m->a, m->gd, m->ad, note);
    fclose(f); rename(tmp, path);
}

/* ------------------------------------------------------------------ search state */
static Circ cur, best, cand_c, tmp_c;
static u64 *Vcur, *Vcand, *ALT;
static int *LGc, *LAc, *RGc, *RAc, *REF;
static unsigned char *TFO;
static Metrics mcur, mbest;
static int *DIV; static int ndiv;
static u64 CARE[1024], GT[1024], TT[1024], CC[1024];

static void state_refresh(void) {
    sim(&cur, Vcur);
    if (!outputs_ok(&cur, Vcur)) die("INTERNAL: current circuit does not match target");
    metrics(&cur, &mcur);
    levels(&cur, LGc, LAc);
    int tot = N + cur.ng;
    for (int v = 0; v < tot; v++) { RGc[v] = INF_LVL; RAc[v] = INF_LVL; REF[v] = 0; }
    for (int k = 0; k < M; k++) {
        int o = cur.out[k]; REF[o]++;
        int cg = cap_gd >= 0 ? cap_gd : INF_LVL, ca = cap_ad >= 0 ? cap_ad : INF_LVL;
        if (cg < RGc[o]) RGc[o] = cg;
        if (ca < RAc[o]) RAc[o] = ca;
    }
    for (int j = cur.ng - 1; j >= 0; j--) {
        Gate *g = &cur.g[j]; int v = N + j;
        int rg = RGc[v] - op_gdw[g->op], ra = RAc[v] - op_adw(g->op);
        if (rg < RGc[g->a]) RGc[g->a] = rg;
        if (ra < RAc[g->a]) RAc[g->a] = ra;
        REF[g->a]++;
        if (!op_unary(g->op)) {
            if (rg < RGc[g->b]) RGc[g->b] = rg;
            if (ra < RAc[g->b]) RAc[g->b] = ra;
            REF[g->b]++;
        }
    }
}

/* care set of signal s (a gate) and its transitive fanout */
static void tfo_care(int s) {
    int tot = N + cur.ng;
    memset(TFO, 0, tot);
    TFO[s] = 1;
    u64 *as = ALT + (size_t)s * W, *vs = Vcur + (size_t)s * W;
    for (int w = 0; w < W; w++) as[w] = ~vs[w];
    for (int j = s - N + 1; j < cur.ng; j++) {
        Gate *g = &cur.g[j]; int v = N + j;
        if (TFO[g->a] || TFO[g->b]) {
            TFO[v] = 1;
            const u64 *pa = (TFO[g->a] ? ALT : Vcur) + (size_t)g->a * W;
            const u64 *pb = (TFO[g->b] ? ALT : Vcur) + (size_t)g->b * W;
            eval_gate(g->op, pa, pb, ALT + (size_t)v * W);
        }
    }
    for (int w = 0; w < W; w++) CARE[w] = 0;
    for (int k = 0; k < M; k++) {
        int o = cur.out[k];
        if (!TFO[o]) continue;
        for (int w = 0; w < W; w++) CARE[w] |= Vcur[(size_t)o * W + w] ^ ALT[(size_t)o * W + w];
    }
    int observable = 0;
    for (int w = 0; w < W; w++) if (CARE[w] & wmask(w)) observable = 1;
    if (!use_odc && observable) for (int w = 0; w < W; w++) CARE[w] = ~0ULL;   /* ablation: exact equality */
    for (int w = 0; w < W; w++) { CARE[w] &= wmask(w); GT[w] = Vcur[(size_t)s * W + w] & CARE[w]; }
}

static double mffc_cost(int s) {
    static int *ref = 0, *stk = 0;
    if (!ref) { ref = malloc(sizeof(int) * (MAXN + GCAP + 8)); stk = malloc(sizeof(int) * (MAXN + GCAP + 8)); }
    int tot = N + cur.ng; memcpy(ref, REF, sizeof(int) * tot);
    double c = 0; int sp = 0; stk[sp++] = s;
    while (sp) {
        int v = stk[--sp]; Gate *g = &cur.g[v - N]; c += op_cost[g->op];
        if (g->a >= N && --ref[g->a] == 0) stk[sp++] = g->a;
        if (!op_unary(g->op) && g->b >= N && --ref[g->b] == 0) stk[sp++] = g->b;
    }
    return c;
}

/* pair table: values of op(d1,d2) (and NOT d) over a divisor subset, masked by CARE */
typedef struct { unsigned char op; int a, b; int lg, la; } PEnt;
static PEnt *PE; static u64 *PV; static int np, PCAP;
static int *PHT; static int phts, phmask;
static inline unsigned hval(const u64 *v) {
    u64 h = 0x12345;
    for (int w = 0; w < W; w++) { h ^= v[w]; h *= 0x9E3779B97F4A7C15ULL; h ^= h >> 31; }
    return (unsigned)(h >> 17);
}
static inline int eqc(const u64 *a, const u64 *b, const u64 *c) {
    for (int w = 0; w < W; w++) if ((a[w] ^ b[w]) & c[w]) return 0;
    return 1;
}

/* candidates */
typedef struct { int k; Gate g[3]; int root; double ncost; } Cand;
static Cand *CAND; static int ncand, nseen;
static void add_cand(const Cand *c) {
    nseen++;
    if (ncand < cand_cap) CAND[ncand++] = *c;
    else { int i = rndint(nseen); if (i < cand_cap) CAND[i] = *c; }
}

static int lib2[16], nlib2;   /* binary ops in library, canonical orientation */
static double budget;          /* max new-gate cost for this move */
static int req_g, req_a;       /* required levels at s */

static inline int arr_g(int op, int la_, int lb_) { return (la_ > lb_ ? la_ : lb_) + op_gdw[op]; }
static inline int arr_a(int op, int la_, int lb_) { return (la_ > lb_ ? la_ : lb_) + op_adw(op); }

static void build_pairs(void) {
    np = 0;
    int nd = ndiv < pdiv ? ndiv : pdiv;   /* DIV is shuffled: first nd are the pair divisors */
    long bound = (long)nd * (nd + 1) / 2 * (2 * nlib2) + nd + 16;
    if (bound > PCAP) bound = PCAP;
    int hs = 64; while (hs < 2 * bound) hs <<= 1;
    phmask = hs - 1;
    for (int i = 0; i < hs; i++) PHT[i] = -1;
    for (int i = 0; i < nd; i++) {
        int d1 = DIV[i];
        for (int j = (op_ok[3] ? i : i + 1); j < nd; j++) {
            int d2 = DIV[j];
            for (int t = 0; t < (i == j ? 1 : nlib2 * 2); t++) {
                int op, a, b;
                if (i == j) { op = 3; a = b = d1; }
                else {
                    op = lib2[t >> 1];
                    if (t & 1) { if (op_sym(op)) continue; a = d2; b = d1; } else { a = d1; b = d2; }
                }
                if (op_cost[op] > budget) continue;
                if (np >= PCAP) return;
                PEnt *e = &PE[np]; e->op = op; e->a = a; e->b = b;
                e->lg = arr_g(op, LGc[a], LGc[b]); e->la = arr_a(op, LAc[a], LAc[b]);
                if (e->lg > req_g || e->la > req_a) continue;
                u64 *pv = PV + (size_t)np * W; const u64 *va = Vcur + (size_t)a * W, *vb = Vcur + (size_t)b * W;
                for (int w = 0; w < W; w++) pv[w] = apply(op, va[w], vb[w]) & CARE[w];
                unsigned h = hval(pv) & phmask;
                while (PHT[h] >= 0) h = (h + 1) & phmask;
                PHT[h] = np; np++;
            }
        }
    }
}
/* find up to `lim` pair entries whose masked value equals v (v already masked) */
static int lookup(const u64 *v, int *hits, int lim) {
    int nh = 0; unsigned h = hval(v) & phmask;
    while (PHT[h] >= 0 && nh < lim) {
        int i = PHT[h];
        const u64 *pv = PV + (size_t)i * W; int eq = 1;
        for (int w = 0; w < W; w++) if (pv[w] != v[w]) { eq = 0; break; }
        if (eq) hits[nh++] = i;
        h = (h + 1) & phmask;
    }
    return nh;
}

/* enumerate candidates for signal s up to `lev` new gates */
static void find_cands(int lev) {
    int base = N + cur.ng;
    Cand c;
    ncand = 0; nseen = 0;
    /* level 0: an existing divisor */
    for (int i = 0; i < ndiv; i++) {
        int d = DIV[i];
        if (LGc[d] > req_g || LAc[d] > req_a) continue;
        if (eqc(Vcur + (size_t)d * W, GT, CARE)) { c.k = 0; c.root = d; c.ncost = 0; add_cand(&c); }
    }
    if (lev < 1) return;
    build_pairs();
    /* level 1 */
    for (int i = 0; i < np; i++)
        if (eqc(PV + (size_t)i * W, GT, CARE)) {
            PEnt *e = &PE[i]; c.k = 1; c.g[0].op = e->op; c.g[0].a = e->a; c.g[0].b = e->b;
            c.root = base; c.ncost = op_cost[e->op]; add_cand(&c);
        }
    if (lev < 2) return;
    int hits[8];
    /* level 2, XOR/XNOR root:  s = X ^ d3  (or ~) */
    for (int r = 6; r <= 9; r += 3) {
        if (!op_ok[r]) continue;
        for (int i = 0; i < ndiv; i++) {
            int d3 = DIV[i];
            for (int w = 0; w < W; w++) TT[w] = ((r == 6 ? GT[w] : ~GT[w]) ^ Vcur[(size_t)d3 * W + w]) & CARE[w];
            int nh = lookup(TT, hits, 4);
            for (int h = 0; h < nh; h++) {
                PEnt *e = &PE[hits[h]];
                double nc = op_cost[e->op] + op_cost[r];
                if (nc > budget) continue;
                if (arr_g(r, e->lg, LGc[d3]) > req_g || arr_a(r, e->la, LAc[d3]) > req_a) continue;
                c.k = 2; c.g[0].op = e->op; c.g[0].a = e->a; c.g[0].b = e->b;
                c.g[1].op = r; c.g[1].a = base; c.g[1].b = d3; c.root = base + 1; c.ncost = nc; add_cand(&c);
            }
        }
    }
    /* level 2, any library root (sampled):  s = op2(X, d3) or op2(d3, X) */
    for (int smp = 0; smp < nl_samples && nlib2 > 0; smp++) {
        int d3 = DIV[rndint(ndiv)];
        int op2 = lib2[rndint(nlib2)];
        int xfirst = op_sym(op2) ? 1 : (int)(rnd() & 1);
        /* f(x,y) with x = X: bit index (x<<1)|y if X first, else (y<<1)|x */
        int f[2][2];
        for (int x = 0; x < 2; x++) for (int y = 0; y < 2; y++)
            f[x][y] = xfirst ? (op2 >> ((x << 1) | y)) & 1 : (op2 >> ((y << 1) | x)) & 1;
        int bad = 0;
        const u64 *vd = Vcur + (size_t)d3 * W;
        for (int w = 0; w < W && !bad; w++) {
            u64 y1 = vd[w] & CARE[w], y0 = ~vd[w] & CARE[w], g = GT[w];
            u64 t = 0, cc = 0;
            for (int y = 0; y < 2; y++) {
                u64 lane = y ? y1 : y0;
                if (f[0][y] == f[1][y]) {          /* X free; need g == f */
                    u64 viol = lane & (f[0][y] ? ~g : g);
                    if (viol) { bad = 1; break; }
                } else {                            /* X = g ^ f(0,y) */
                    t |= lane & (f[0][y] ? ~g : g); cc |= lane;
                }
            }
            TT[w] = t; CC[w] = cc;
        }
        if (bad) continue;
        double nc0 = op_cost[op2];
        for (int i = 0; i < np; i++) {
            PEnt *e = &PE[i];
            if (op_cost[e->op] + nc0 > budget) continue;
            if (!eqc(PV + (size_t)i * W, TT, CC)) continue;
            if (arr_g(op2, e->lg, LGc[d3]) > req_g || arr_a(op2, e->la, LAc[d3]) > req_a) continue;
            c.k = 2; c.g[0].op = e->op; c.g[0].a = e->a; c.g[0].b = e->b;
            c.g[1].op = op2; c.g[1].a = xfirst ? base : d3; c.g[1].b = xfirst ? d3 : base;
            c.root = base + 1; c.ncost = op_cost[e->op] + nc0; add_cand(&c);
        }
    }
    if (lev < 3) return;
    /* level 3, XOR/XNOR root of two pair values:  s = X1 ^ X2 */
    for (int r = 6; r <= 9; r += 3) {
        if (!op_ok[r]) continue;
        int lim = np < 30000 ? np : 30000;
        for (int q = 0; q < lim; q++) {
            int i = np <= 30000 ? q : rndint(np);
            PEnt *e = &PE[i];
            const u64 *pv = PV + (size_t)i * W;
            for (int w = 0; w < W; w++) TT[w] = ((r == 6 ? GT[w] : ~GT[w]) ^ pv[w]) & CARE[w];
            int nh = lookup(TT, hits, 2);
            for (int h = 0; h < nh; h++) {
                if (hits[h] <= i) continue;
                PEnt *e2 = &PE[hits[h]];
                double nc = op_cost[e->op] + op_cost[e2->op] + op_cost[r];
                if (nc > budget) continue;
                if (arr_g(r, e->lg, e2->lg) > req_g || arr_a(r, e->la, e2->la) > req_a) continue;
                c.k = 3; c.g[0].op = e->op; c.g[0].a = e->a; c.g[0].b = e->b;
                c.g[1].op = e2->op; c.g[1].a = e2->a; c.g[1].b = e2->b;
                c.g[2].op = r; c.g[2].a = base; c.g[2].b = base + 1; c.root = base + 2; c.ncost = nc; add_cand(&c);
            }
        }
    }
}

/* fraig: merge gates whose complete function equals an earlier signal (never deeper) */
static int *FR_map; static int *FR_ht; static int FR_hts;
static int fraig(Circ *c, u64 *V) {
    int tot = N + c->ng, any = 0;
    levels(c, LG_tmp, LA_tmp);
    int hts = 64; while (hts < 2 * tot) hts <<= 1;
    if (hts > FR_hts) hts = FR_hts;
    for (int i = 0; i < hts; i++) FR_ht[i] = -1;
    for (int v = 0; v < tot; v++) {
        FR_map[v] = v;
        const u64 *pv = V + (size_t)v * W;
        u64 h = 0x777; for (int w = 0; w < W; w++) { h ^= pv[w] & wmask(w); h *= 0x9E3779B97F4A7C15ULL; h ^= h >> 29; }
        unsigned hh = (unsigned)(h >> 20) & (hts - 1);
        int found = -1;
        while (FR_ht[hh] >= 0) {
            int u = FR_ht[hh]; const u64 *pu = V + (size_t)u * W; int eq = 1;
            for (int w = 0; w < W; w++) if ((pu[w] ^ pv[w]) & wmask(w)) { eq = 0; break; }
            if (eq) { found = u; break; }
            hh = (hh + 1) & (hts - 1);
        }
        if (found >= 0 && LG_tmp[found] <= LG_tmp[v] && LA_tmp[found] <= LA_tmp[v]) { FR_map[v] = found; any = 1; }
        else if (found < 0) FR_ht[hh] = v;
    }
    if (!any) return 0;
    if (rebuild(c, -1, -1, 0, 0, FR_map, &tmp_c, 1) < 0) return 0;
    circ_copy(c, &tmp_c); sim(c, V);
    return 1;
}

/* evaluate candidate: build into cand_c, return obj (or +inf if invalid) */
static int eval_cand(int s, const Cand *k, Metrics *m) {
    if (rebuild(&cur, s, k->root, k->g, k->k, 0, &cand_c, 1) < 0) return 0;
    sim(&cand_c, Vcand);
    if (!outputs_ok(&cand_c, Vcand)) {
        fprintf(stderr, "INTERNAL: candidate breaks the function (s=%d k=%d)\n", s, k->k); exit(3);
    }
    if (use_fraig) for (int it = 0; it < 3 && fraig(&cand_c, Vcand); it++);
    metrics(&cand_c, m);
    return 1;
}

/* ------------------------------------------------------------------ move trace */
static FILE *tmv; static Circ tmp_before; static Metrics mprev_dummy;
static const char *OPNAME[16] = {"C0", "NOR", "BANDN", "NOT", "ANDN", "NOTB", "XOR", "NAND",
                                 "AND", "XNOR", "BUFB", "BORN", "BUF", "ORN", "OR", "C1"};
static int popc_care(void) { int c = 0; for (int w = 0; w < W; w++) c += __builtin_popcountll(CARE[w] & wmask(w)); return c; }
static int patterns(void) { int c = 0; for (int w = 0; w < W; w++) c += __builtin_popcountll(wmask(w)); return c; }

/* ------------------------------------------------------------------ main loop */
static double now_s(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }
static long st_prop[NMOVES], st_acc[NMOVES], st_imp[NMOVES], st_cands[NMOVES];
static double st_time[NMOVES];

int main(int argc, char **argv) {
    if (argc < 2) die("usage: bfx CONFIG");
    circ_alloc(&cur); circ_alloc(&best); circ_alloc(&cand_c); circ_alloc(&tmp_c);
    int S = MAXN + GCAP + 16;
    RB_g = malloc(sizeof(Gate) * S); RB_map = malloc(sizeof(int) * S); RB_mark = malloc(sizeof(int) * S);
    RB_new = malloc(sizeof(int) * S); RB_stk = malloc(sizeof(int) * S * 2);
    RB_htsize = 1 << 16; RB_ht = malloc(sizeof(int) * RB_htsize);
    LG_tmp = malloc(sizeof(int) * S); LA_tmp = malloc(sizeof(int) * S);
    HG_tmp = malloc(sizeof(int) * S); HA_tmp = malloc(sizeof(int) * S);
    LGc = malloc(sizeof(int) * S); LAc = malloc(sizeof(int) * S); RGc = malloc(sizeof(int) * S);
    RAc = malloc(sizeof(int) * S); REF = malloc(sizeof(int) * S); TFO = malloc(S); DIV = malloc(sizeof(int) * S);
    FR_map = malloc(sizeof(int) * S); FR_hts = 1 << 16; FR_ht = malloc(sizeof(int) * FR_hts);

    int stats_only = !strcmp(argv[1], "--stats");
    if (stats_only) {
        for (int i = 0; i < 16; i++) { op_ok[i] = 1; op_cost[i] = 1; op_gdw[i] = 1; }
        strcpy(cfg_in, argv[2]);
    } else parse_config(argv[1]);
    seed_rng(cfg_seed);
    read_circuit(cfg_in, &cur);
    if (linear_mode) {
        /* Every gate of an XOR/XNOR/NOT library is affine, and an affine function of n inputs is
         * determined by its values at 0 and at the n unit vectors.  Simulating these n+1 patterns
         * is therefore exact: two affine circuits agree on all 2^n inputs iff they agree here,
         * and a signal's care set is all-or-nothing (path parities do not depend on the input). */
        for (int op = 0; op < 16; op++) if (op_ok[op] && op_nl(op)) die("linear mode needs a linear library");
        if (N + 1 > 64) die("linear mode supports at most 63 inputs");
        W = 1; LASTMASK = N + 1 == 64 ? ~0ULL : ((1ULL << (N + 1)) - 1);
    }
    INV = calloc((size_t)N * W, 8); TGT = calloc((size_t)M * W, 8);
    if (linear_mode) for (int i = 0; i < N; i++) INV[i] = 1ULL << (i + 1);   /* pattern 0 = zero vector */
    else
    for (int i = 0; i < N; i++)
        for (int x = 0; x < (1 << N); x++)
            if ((x >> (N - 1 - i)) & 1) INV[(size_t)i * W + (x >> 6)] |= 1ULL << (x & 63);
    Vcur = malloc(sizeof(u64) * (size_t)S * W); Vcand = malloc(sizeof(u64) * (size_t)S * W);
    ALT = malloc(sizeof(u64) * (size_t)S * W);
    /* the start circuit defines the target */
    sim(&cur, Vcur);
    for (int k = 0; k < M; k++) memcpy(TGT + (size_t)k * W, Vcur + (size_t)cur.out[k] * W, 8 * W);
    for (int j = 0; j < cur.ng; j++)
        if (!stats_only && !op_ok[cur.g[j].op]) { fprintf(stderr, "bfx: start circuit uses op %d outside the library\n", cur.g[j].op); exit(2); }
    if (rebuild(&cur, -1, -1, 0, 0, 0, &tmp_c, 1) < 0) die("start circuit cannot be cleaned");
    circ_copy(&cur, &tmp_c);
    state_refresh();
    if (stats_only) {
        printf("cost %.4f G %d A %d GD %d AD %d\n", mcur.cost, mcur.g, mcur.a, mcur.gd, mcur.ad); return 0;
    }
    nlib2 = 0;
    int canon[] = {8, 14, 6, 9, 7, 1, 4, 13};
    for (int i = 0; i < 8; i++) if (op_ok[canon[i]]) lib2[nlib2++] = canon[i];
    PCAP = 200000; if ((size_t)PCAP * W > 16000000) PCAP = 16000000 / W;
    PE = malloc(sizeof(PEnt) * PCAP); PV = malloc(sizeof(u64) * (size_t)PCAP * W);
    phts = 1; while (phts < PCAP * 2) phts <<= 1; PHT = malloc(sizeof(int) * phts);
    CAND = malloc(sizeof(Cand) * (cand_cap + 1));

    circ_copy(&best, &cur); mbest = mcur;
    FILE *trace = cfg_trace[0] ? fopen(cfg_trace, "w") : 0;
    tmv = cfg_tracemoves[0] ? fopen(cfg_tracemoves, "w") : 0;
    if (tmv) circ_alloc(&tmp_before);
    double t0 = now_s(), last_best = 0, mvsum = 0;
    for (int i = 0; i < NMOVES; i++) mvsum += mv_w[i];
    printf("start cost %.4f G %d A %d GD %d AD %d feas %d obj %.6f\n", mcur.cost, mcur.g, mcur.a, mcur.gd, mcur.ad, mcur.feas, mcur.obj);
    if (!mcur.feas) printf("note: start circuit violates a cap; the search first repairs it (penalised objective)\n");
    write_circuit(cfg_out, &best, &mbest, "start");
    long it = 0, restarts = 0, last_best_it = 0;
    while (1) {
        double t = now_s() - t0;
        if (t >= cfg_seconds || (max_iters >= 0 && it >= max_iters)) break;
        it++;
        double ph = Tperiod_it > 0 ? fmod((double)it, Tperiod_it) / Tperiod_it : fmod(t, Tperiod) / Tperiod;
        double T = T0 > 0 ? T0 * (1.0 - ph) : 0;
        int stalled = stall_it > 0 ? (it - last_best_it > stall_it) : (t - last_best > stall);
        if (stalled && mcur.obj > mbest.obj + 1e-9) {
            circ_copy(&cur, &best); state_refresh(); last_best = t; last_best_it = it; restarts++;
        }
        if (cur.ng == 0) break;
        double r = rnd01() * mvsum; int mv = 0;
        while (mv < NMOVES - 1 && r >= mv_w[mv]) { r -= mv_w[mv]; mv++; }
        double tm = now_s();
        st_prop[mv]++;
        int s = N + rndint(cur.ng);
        tfo_care(s);
        /* required levels; in repair mode (current state violates a cap) never deeper than s */
        req_g = RGc[s] > LGc[s] ? RGc[s] : LGc[s]; req_a = RAc[s] > LAc[s] ? RAc[s] : LAc[s];
        double mc = mffc_cost(s);
        budget = mc + uphill;
        ndiv = 0;
        for (int v = 0; v < N + cur.ng; v++) if (!TFO[v]) DIV[ndiv++] = v;
        for (int i = ndiv - 1; i > 0; i--) { int j = rndint(i + 1); int x = DIV[i]; DIV[i] = DIV[j]; DIV[j] = x; }
        if (ndiv > dmax && dmax > 0) ndiv = dmax;
        if (ndiv == 0) continue;
        find_cands(mv + 1);
        st_cands[mv] += ncand;
        /* evaluate all candidates; take the best improvement, else a random one under Metropolis */
        int bi = -1, bfeas = 0; double bobj = 1e300; Metrics m;
        static int order[1024], neu[1024], up[1024]; static double upd[1024];
        int no = ncand < 1024 ? ncand : 1024, nneu = 0, nup = 0;
        for (int i = 0; i < no; i++) order[i] = i;
        for (int i = no - 1; i > 0; i--) { int j = rndint(i + 1); int x = order[i]; order[i] = order[j]; order[j] = x; }
        for (int q = 0; q < no; q++) {
            int i = order[q];
            if (!eval_cand(s, &CAND[i], &m)) continue;
            if (skip_noop && cand_c.ng == cur.ng && !memcmp(cand_c.g, cur.g, sizeof(Gate) * cur.ng)
                && !memcmp(cand_c.out, cur.out, sizeof(int) * M)) { st_noop++; continue; }
            double d = m.obj - mcur.obj;
            if ((m.feas || !mcur.feas) && m.obj < bobj) { bobj = m.obj; bi = i; bfeas = m.feas; }
            if (fabs(d) <= 1e-9 && m.feas >= mcur.feas) neu[nneu++] = i;
            else if (d > 0 && m.obj <= mbest.obj + max_excess && m.feas >= mcur.feas) { upd[nup] = d; up[nup++] = i; }
        }
        int accept = -1;
        /* feasibility first: a feasible state is never left for an infeasible one */
        if (bi >= 0 && bobj < mcur.obj - 1e-9 && (bfeas || !mcur.feas)) accept = bi;
        else if (use_neutral && nneu && (nup == 0 || T <= 0 || rnd01() < 0.75)) accept = neu[rndint(nneu)];
        else if (nup && T > 0) { int q = rndint(nup); if (rnd01() < exp(-upd[q] / T)) accept = up[q]; }
        if (accept >= 0) {
            if (tmv) {
                Cand *k = &CAND[accept]; Gate *gs = &cur.g[s - N];
                fprintf(tmv, "it %ld t %.4f mv %s target s%d=%s(s%d,s%d) mffc_cost %.2f care %d/%d cands %d | new %d gate(s):",
                        it, t, MVNAME[mv], s, OPNAME[gs->op], gs->a, gs->b, mc, popc_care(), patterns(), ncand, k->k);
                for (int q = 0; q < k->k; q++) fprintf(tmv, " n%d=%s(%s%d,%s%d)", q, OPNAME[k->g[q].op],
                    k->g[q].a >= N + cur.ng ? "n" : "s", k->g[q].a >= N + cur.ng ? k->g[q].a - N - cur.ng : k->g[q].a,
                    k->g[q].b >= N + cur.ng ? "n" : "s", k->g[q].b >= N + cur.ng ? k->g[q].b - N - cur.ng : k->g[q].b);
                fprintf(tmv, " root %s%d | before cost %.2f G %d A %d GD %d AD %d", k->root >= N + cur.ng ? "n" : "s",
                        k->root >= N + cur.ng ? k->root - N - cur.ng : k->root, mcur.cost, mcur.g, mcur.a, mcur.gd, mcur.ad);
            }
            Circ *before = tmv ? &tmp_before : 0;
            if (before) circ_copy(before, &cur);
            eval_cand(s, &CAND[accept], &m);
            circ_copy(&cur, &cand_c); state_refresh();
            if (tmv) {
                fprintf(tmv, " -> after cost %.2f G %d A %d GD %d AD %d\n", mcur.cost, mcur.g, mcur.a, mcur.gd, mcur.ad);
                if (mcur.obj < mbest.obj - 1e-9) {
                    char fn[1200];
                    snprintf(fn, sizeof fn, "%s.it%ld.before", cfg_tracemoves, it); write_circuit(fn, before, &mprev_dummy, "before");
                    snprintf(fn, sizeof fn, "%s.it%ld.after", cfg_tracemoves, it); write_circuit(fn, &cur, &mcur, "after");
                }
                fflush(tmv);
            }
            st_acc[mv]++;
            if ((mcur.feas || !mbest.feas) && (mcur.obj < mbest.obj - 1e-9 || (mcur.feas && !mbest.feas))) {
                st_imp[mv]++;
                circ_copy(&best, &cur); mbest = mcur; last_best = t; last_best_it = it;
                write_circuit(cfg_out, &best, &mbest, "best");
                printf("best t %.3f it %ld mv %s cost %.4f G %d A %d GD %d AD %d obj %.6f\n", t, it, MVNAME[mv],
                       mbest.cost, mbest.g, mbest.a, mbest.gd, mbest.ad, mbest.obj);
                fflush(stdout);
            }
            if (trace) fprintf(trace, "%.3f %ld %s %.4f %d %d %d %d\n", t, it, MVNAME[mv], mcur.cost, mcur.g, mcur.a, mcur.gd, mcur.ad);
        }
        st_time[mv] += now_s() - tm;
    }
    if (trace) fclose(trace);
    /* final guard: re-simulate the best from scratch */
    sim(&best, Vcur);
    if (!outputs_ok(&best, Vcur)) die("INTERNAL: best circuit does not match target");
    write_circuit(cfg_out, &best, &mbest, "final");
    printf("final cost %.4f G %d A %d GD %d AD %d obj %.6f feas %d iters %ld restarts %ld seconds %.2f\n",
           mbest.cost, mbest.g, mbest.a, mbest.gd, mbest.ad, mbest.obj, mbest.feas, it, restarts, now_s() - t0);
    for (int i = 0; i < NMOVES; i++)
        printf("move %s prop %ld acc %ld imp %ld cands %ld time %.2f\n", MVNAME[i], st_prop[i], st_acc[i], st_imp[i], st_cands[i], st_time[i]);
    printf("noop_candidates_skipped %ld\n", st_noop);
    return 0;
}
