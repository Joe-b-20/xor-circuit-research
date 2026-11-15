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

static void circ_alloc(Circ *c) { c->ng = 0; c->g = calloc(GCAP, sizeof(Gate)); }   /* zeroed padding (deterministic memory contents) */
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

typedef struct { double cost, obj, vsum; int g, a, gd, ad, feas, viol, xgd, xad, xa; } Metrics;   /* x*: excess over each cap */
#define VIOL_PENALTY 1e6
static double w_cost = 1, w_g = 0, w_a = 0, w_gd = 0, w_ad = 0;
static int cap_gd = -1, cap_ad = -1, cap_a = -1;
/* Lexicographic objective (config `lex cost,gd`): keys compared in order after feasibility
 * (largest cap excess, then summed path excess).  The weighted obj is used only for the size
 * of an uphill step (Metropolis) and for printing.  0 cost 1 g 2 a 3 gd 4 ad. */
static int lex_n = 0, lex_k[5];
/* review4 M1: T0, uphill and max_excess are given in units of one gate of the first objective key
 * (`scale_abs 1` keeps them absolute, the pre-review-4 behaviour).  unit = cheapest allowed gate cost
 * when the first key is cost, else 1; applied once after the config is read. */
static double cost_unit_v = 1; static int scale_abs = 0;


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
    m->xgd = cap_gd >= 0 && m->gd > cap_gd ? m->gd - cap_gd : 0;
    m->xad = cap_ad >= 0 && m->ad > cap_ad ? m->ad - cap_ad : 0;
    m->xa = cap_a >= 0 && m->a > cap_a ? m->a - cap_a : 0;
    m->viol = m->xgd + m->xad + m->xa;
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
    m->vsum = vsum;
    m->obj = w_cost * m->cost + w_g * m->g + w_a * m->a + w_gd * m->gd + w_ad * m->ad
             + VIOL_PENALTY * m->viol + 1e4 * vsum;
}
static double keyval(const Metrics *m, int k) {
    switch (k) { case 0: return m->cost; case 1: return m->g; case 2: return m->a; case 3: return m->gd; default: return m->ad; }
}
static int dcmp(double x, double y) {
    double tol = 1e-9 * (1 + fabs(x) + fabs(y));
    return x < y - tol ? -1 : x > y + tol ? 1 : 0;
}
/* -1: a better than b, 0: equal, 1: worse.  Feasibility first (viol, then vsum), then the
 * lexicographic keys; without `lex` the weighted objective (old behaviour). */
/* review4 m1: size of the difference a - b for Metropolis and max_excess, measured on the first
 * key in which they differ (in cost units for cost, x cost_unit_v for the count keys), so a cost-only
 * uphill step is judged on its own scale even when A or GD is the first key.  Feasibility terms keep
 * the penalised weighted difference (repair mode). */
static double ldelta(const Metrics *a, const Metrics *b);
static int mcmp(const Metrics *a, const Metrics *b) {
    if (a->viol != b->viol) return a->viol < b->viol ? -1 : 1;
    int c = dcmp(a->vsum, b->vsum); if (c) return c;
    if (!lex_n) return dcmp(a->obj - VIOL_PENALTY * a->viol - 1e4 * a->vsum, b->obj - VIOL_PENALTY * b->viol - 1e4 * b->vsum);
    for (int i = 0; i < lex_n; i++) { c = dcmp(keyval(a, lex_k[i]), keyval(b, lex_k[i])); if (c) return c; }
    return 0;
}
static double ldelta(const Metrics *a, const Metrics *b) {
    /* cost-first objectives keep the weighted difference (measured behaviour of every campaign so far:
     * secondary keys such as GD drift almost freely, which helps plateau walks) */
    if (!lex_n || lex_k[0] == 0 || a->viol != b->viol || dcmp(a->vsum, b->vsum)) return a->obj - b->obj;
    for (int i = 0; i < lex_n; i++) {
        double x = keyval(a, lex_k[i]), y = keyval(b, lex_k[i]);
        if (dcmp(x, y)) return (x - y) * (lex_k[i] == 0 ? 1.0 : cost_unit_v);
    }
    return 0;
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
#define NMOVES 4
#define MV_XSPAN 3
static double mv_w[NMOVES] = {1, 1, 1, 0};      /* xspan (review5 S1) is off unless mv.xspan > 0 */
static const char *MVNAME[NMOVES] = {"resub1", "resub2", "resub3", "xspan"};
static int xspan_tries = 3, xspan_any = 0;
/* review5 S2: the violation is the SUM of the cap excesses, so a repair may pay for one unit of
 * gate depth with an AND above cap.a (or AND depth above cap.ad) and then sit at violation 1 in
 * a cap that is much harder to repair.  repair_keep 1: while the current circuit violates a cap,
 * no move may raise the excess of any single cap. */
static int repair_keep = 0;
/* review5 S3: root op of the sampled two-gate candidates s = op2(X, d3).  0 (old): op2 uniform over
 * the binary library, although XOR/XNOR roots were already enumerated exactly just before (with
 * the NIST library 2 of 3 samples repeat that work).  1: op2 only among the AND-like library ops.
 * 2: no sampling, every divisor d3 with every AND-like op and orientation (most d3 fail the
 * one-pass feasibility test before the pair table is scanned). */
static int nl_root = 0;
static int sweep = 0;     /* review5: 1 = target gates in index order instead of at random (exact scans) */
static int dmax = 200, pdiv = 90, nl_samples = 12, cand_cap = 40, use_fraig = 1;
static int use_neutral = 1, use_odc = 1, linear_mode = 0;   /* ablation switches; linear: see main */
static int skip_noop = 1;    /* v2: a candidate whose rebuilt circuit equals the current one is no move */
static long st_noop;
static char cfg_tracemoves[1024];
static long max_iters = -1;

static void die(const char *m) { fprintf(stderr, "bfx: %s\n", m); exit(2); }

/* review5 K1: op number of a cost.N / gdw.N key; anything outside 0..15 wrote past the op tables */
static int cfg_op(const char *t) {
    char *e; long op = strtol(t, &e, 10);
    if (e == t || *e || op < 0 || op > 15) { fprintf(stderr, "bfx: bad op number in config key (%s)\n", t); exit(2); }
    return (int)op;
}
static void parse_config(const char *path) {
    FILE *f = fopen(path, "r"); if (!f) die("cannot open config");
    char k[256], v[1024], line[2048];
    for (int i = 0; i < 16; i++) { op_ok[i] = 0; op_cost[i] = 0; op_gdw[i] = 1; }
    /* review5 K1: one "key value" per line.  (The old token reader took the first word of the
     * next line as the value of a one-word comment and then dropped the rest of that line.)
     * Blank lines and lines starting with # are skipped; a path value is the rest of the line. */
    while (fgets(line, sizeof line, f)) {
        char *p = line + strspn(line, " \t\r\n");
        if (!*p || *p == '#') continue;
        if (sscanf(p, "%255s %1023s", k, v) != 2) { fprintf(stderr, "bfx: config key %s has no value\n", k); exit(2); }
        if (!strcmp(k, "in") || !strcmp(k, "out") || !strcmp(k, "trace") || !strcmp(k, "tracemoves")) {
            char *q = p + strlen(k); q += strspn(q, " \t");
            size_t L = strlen(q); while (L && strchr(" \t\r\n", q[L - 1])) L--;
            if (L > 1023) die("config: path too long");
            memcpy(v, q, L); v[L] = 0;
        }
        if (!strcmp(k, "in")) strcpy(cfg_in, v);
        else if (!strcmp(k, "out")) strcpy(cfg_out, v);
        else if (!strcmp(k, "trace")) strcpy(cfg_trace, v);
        else if (!strcmp(k, "seconds")) cfg_seconds = atof(v);
        else if (!strcmp(k, "iters")) max_iters = atol(v);
        else if (!strcmp(k, "seed")) cfg_seed = strtoull(v, 0, 10);
        else if (!strncmp(k, "cost.", 5)) { int op = cfg_op(k + 5); op_ok[op] = 1; op_cost[op] = atof(v); }
        else if (!strncmp(k, "gdw.", 4)) op_gdw[cfg_op(k + 4)] = atoi(v);
        else if (!strcmp(k, "w.cost")) w_cost = atof(v);
        else if (!strcmp(k, "w.g")) w_g = atof(v);
        else if (!strcmp(k, "w.a")) w_a = atof(v);
        else if (!strcmp(k, "w.gd")) w_gd = atof(v);
        else if (!strcmp(k, "w.ad")) w_ad = atof(v);
        else if (!strcmp(k, "scale_abs")) scale_abs = atoi(v);
        else if (!strcmp(k, "lex")) {
            static const char *KN[5] = {"cost", "g", "a", "gd", "ad"};
            lex_n = 0;
            for (char *t = strtok(v, ","); t; t = strtok(0, ",")) {
                int f = -1; for (int q = 0; q < 5; q++) if (!strcmp(t, KN[q])) f = q;
                if (f < 0 || lex_n >= 5) die("lex: unknown key");
                lex_k[lex_n++] = f;
            }
        }
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
        else if (!strncmp(k, "mv.", 3)) {
            int hit = 0;
            for (int i = 0; i < NMOVES; i++) if (!strcmp(k + 3, MVNAME[i])) { mv_w[i] = atof(v); hit = 1; }
            if (!hit) { fprintf(stderr, "bfx: unknown move %s\n", k); exit(2); }   /* review5 K1: was ignored */
        }
        else if (!strcmp(k, "dmax")) dmax = atoi(v);
        else if (!strcmp(k, "pdiv")) pdiv = atoi(v);
        else if (!strcmp(k, "nl_samples")) nl_samples = atoi(v);
        else if (!strcmp(k, "cand_cap")) cand_cap = atoi(v);
        else if (!strcmp(k, "fraig")) use_fraig = atoi(v);
        else if (!strcmp(k, "neutral")) use_neutral = atoi(v);
        else if (!strcmp(k, "skip_noop")) skip_noop = atoi(v);
        else if (!strcmp(k, "odc")) use_odc = atoi(v);
        else if (!strcmp(k, "repair_keep")) repair_keep = atoi(v);
        else if (!strcmp(k, "sweep")) sweep = atoi(v);
        else if (!strcmp(k, "nl_root")) nl_root = atoi(v);
        else if (!strcmp(k, "xspan_tries")) xspan_tries = atoi(v);
        else if (!strcmp(k, "xspan_any")) xspan_any = atoi(v);
        else if (!strcmp(k, "linear")) linear_mode = atoi(v);
        else if (!strcmp(k, "tracemoves")) strcpy(cfg_tracemoves, v);
        else { fprintf(stderr, "bfx: unknown key %s\n", k); exit(2); }
    }
    fclose(f);
    if (cand_cap < 1) die("cand_cap must be at least 1");
    if (xspan_tries < 1 || xspan_tries > 16) die("xspan_tries must be 1..16");
    if (!cfg_in[0] || !cfg_out[0]) die("config needs in and out");
}

static void read_circuit(const char *path, Circ *c) {
    FILE *f = fopen(path, "r"); if (!f) die("cannot open circuit");
    int ng;
    if (fscanf(f, " n %d m %d g %d", &N, &M, &ng) != 3) die("bad circuit header");
    if (N < 1 || N > MAXN || M < 1 || M > MAXM || ng < 0 || ng > GCAP) die("circuit too large");
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
    fprintf(f, "# cost %.10g G %d A %d GD %d AD %d %s\n", m->cost, m->g, m->a, m->gd, m->ad, note);
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

static int SH_ycached;   /* same_structure's cache of the current circuit */
static void state_refresh(void) {
    SH_ycached = 0;
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

static int mffc_a;      /* AND-like gates in the cone counted by the last mffc_cost call */
static unsigned *MFM, mfm_gen;   /* MFM[v] == mfm_gen: v is in that cone (it dies when s is replaced) */
static double mffc_cost(int s) {
    static int *ref = 0, *stk = 0;
    if (!ref) { ref = malloc(sizeof(int) * (MAXN + GCAP + 8)); stk = malloc(sizeof(int) * (MAXN + GCAP + 8)); MFM = calloc(MAXN + GCAP + 8, sizeof(unsigned)); }
    if (++mfm_gen == 0) { memset(MFM, 0, sizeof(unsigned) * (MAXN + GCAP + 8)); mfm_gen = 1; }
    int tot = N + cur.ng; memcpy(ref, REF, sizeof(int) * tot);
    double c = 0; int sp = 0; stk[sp++] = s; mffc_a = 0;
    while (sp) {
        int v = stk[--sp]; Gate *g = &cur.g[v - N]; c += op_cost[g->op]; mffc_a += op_nl(g->op); MFM[v] = mfm_gen;
        if (g->a >= N && --ref[g->a] == 0) stk[sp++] = g->a;
        if (!op_unary(g->op) && g->b >= N && --ref[g->b] == 0) stk[sp++] = g->b;
    }
    return c;
}

/* pair table: values of op(d1,d2) (and NOT d) over a divisor subset, masked by CARE.
 * review5 P1: each entry keeps a 64-bit digest of its masked value that is GF(2)-linear in the
 * value: ldig(x ^ y) == ldig(x) ^ ldig(y).  The value wanted from the table at level 3 is
 * GT ^ X for a stored X, so its digest is one XOR of two stored digests and no words are touched
 * unless a slot holds the same digest.  Slots are stamped with the build number instead of being
 * cleared for every move.  Entries with equal values share a digest and therefore a probe
 * sequence, in which they stay in insertion order for any table size, so lookups return the same
 * entries in the same order as the previous table (same search trajectory). */
typedef struct { unsigned char op; int a, b; int lg, la; } PEnt;
typedef struct { int idx; unsigned gen; } PSlot;
static PEnt *PE; static u64 *PV, *PD, *PV0; static int np, PCAP;
static PSlot *PHT; static int phts, phmask; static unsigned pgen;
static int *L1; static int nl1;      /* entries whose value equals GT (level-1 candidates) */
static inline u64 ldig(const u64 *v) {
    u64 h = 0;      /* per-word linear maps, no dependency chain between words */
    for (int w = 0; w < W; w++) { u64 x = v[w]; int r = (w * 21 + 1) & 63; h ^= ((x << r) | (x >> ((64 - r) & 63))) ^ (x >> ((w % 29) + 3)); }
    return h;
}
static inline unsigned dslot(u64 d) { return (unsigned)((d * 0x9E3779B97F4A7C15ULL) >> 40) & phmask; }
static inline int eqc(const u64 *a, const u64 *b, const u64 *c) {
    for (int w = 0; w < W; w++) if ((a[w] ^ b[w]) & c[w]) return 0;
    return 1;
}
static inline int eqw(const u64 *a, const u64 *b) {
    for (int w = 0; w < W; w++) if (a[w] != b[w]) return 0;
    return 1;
}
/* o = op(a, b) & c, the op chosen once per entry instead of once per word */
static inline void pair_val(int op, const u64 *a, const u64 *b, const u64 *c, u64 *o) {
    switch (op) {
    case 8: for (int w = 0; w < W; w++) o[w] = a[w] & b[w] & c[w]; break;
    case 6: for (int w = 0; w < W; w++) o[w] = (a[w] ^ b[w]) & c[w]; break;
    case 9: for (int w = 0; w < W; w++) o[w] = ~(a[w] ^ b[w]) & c[w]; break;
    case 14: for (int w = 0; w < W; w++) o[w] = (a[w] | b[w]) & c[w]; break;
    case 3: for (int w = 0; w < W; w++) o[w] = ~a[w] & c[w]; break;
    default: for (int w = 0; w < W; w++) o[w] = apply(op, a[w], b[w]) & c[w];
    }
}

/* candidates */
typedef struct { int k; Gate g[3]; int root; double ncost; const Gate *ext; } Cand;   /* ext: gate list of an xspan candidate (k may exceed 3) */
static inline const Gate *cand_gates(const Cand *c) { return c->ext ? c->ext : c->g; }
static Cand *CAND; static int ncand, nseen;
static void add_cand(const Cand *c) {
    nseen++;
    if (ncand < cand_cap) CAND[ncand++] = *c;
    else { int i = rndint(nseen); if (i < cand_cap) CAND[i] = *c; }
}

static int lib2[16], nlib2;   /* binary ops in library, canonical orientation */
static int libnl[16], nlibnl; /* the AND-like ones among them */
static double budget;          /* max new-gate cost for this move */
static int req_g, req_a;       /* required levels at s */

static inline int arr_g(int op, int la_, int lb_) { return (la_ > lb_ ? la_ : lb_) + op_gdw[op]; }
static inline int arr_a(int op, int la_, int lb_) { return (la_ > lb_ ? la_ : lb_) + op_adw(op); }

static void build_pairs(int want_table) {
    np = 0; nl1 = 0;
    int nd = ndiv < pdiv ? ndiv : pdiv;   /* DIV is shuffled: first nd are the pair divisors */
    if (want_table) {
        long bound = (long)nd * (nd + 1) / 2 * (2 * nlib2) + nd + 16;
        if (bound > PCAP) bound = PCAP;
        int hs = 64; while (hs < 2 * bound) hs <<= 1;
        phmask = hs - 1;
        if (++pgen == 0) { memset(PHT, 0, sizeof(PSlot) * phts); pgen = 1; }
    }
    u64 dgt = ldig(GT);
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
                u64 *pv = PV + (size_t)np * W;
                pair_val(op, Vcur + (size_t)a * W, Vcur + (size_t)b * W, CARE, pv);
                u64 d = ldig(pv); PD[np] = d; PV0[np] = pv[0];
                if (d == dgt && eqw(pv, GT)) L1[nl1++] = np;
                if (want_table) {
                    unsigned h = dslot(d);
                    while (PHT[h].gen == pgen) h = (h + 1) & phmask;
                    PHT[h].gen = pgen; PHT[h].idx = np;
                }
                np++;
            }
        }
    }
}
/* find up to `lim` pair entries whose masked value equals v (v already masked; d = ldig(v)) */
static int lookup(u64 d, const u64 *v, int *hits, int lim) {
    int nh = 0; unsigned h = dslot(d);
    while (PHT[h].gen == pgen && nh < lim) {
        int i = PHT[h].idx;
        if (PD[i] == d && eqw(PV + (size_t)i * W, v)) hits[nh++] = i;
        h = (h + 1) & phmask;
    }
    return nh;
}

/* enumerate candidates for signal s up to `lev` new gates */
static void find_cands(int lev) {
    int base = N + cur.ng;
    Cand c; c.ext = 0;
    ncand = 0; nseen = 0;
    /* level 0: an existing divisor */
    for (int i = 0; i < ndiv; i++) {
        int d = DIV[i];
        if (LGc[d] > req_g || LAc[d] > req_a) continue;
        if (eqc(Vcur + (size_t)d * W, GT, CARE)) { c.k = 0; c.root = d; c.ncost = 0; add_cand(&c); }
    }
    if (lev < 1) return;
    build_pairs(lev >= 2);
    /* level 1 */
    for (int q = 0; q < nl1; q++) {
        PEnt *e = &PE[L1[q]]; c.k = 1; c.g[0].op = e->op; c.g[0].a = e->a; c.g[0].b = e->b;
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
            int nh = lookup(ldig(TT), TT, hits, 4);
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
    long nsmp = nl_root == 2 ? (long)ndiv * nlibnl * 2 : nl_samples;
    for (long smp = 0; smp < nsmp && (nl_root ? nlibnl : nlib2) > 0; smp++) {
        int d3, op2, xfirst;
        if (nl_root == 2) {
            d3 = DIV[smp / (nlibnl * 2)]; op2 = libnl[(smp >> 1) % nlibnl]; xfirst = (int)(smp & 1);
            if (!xfirst && op_sym(op2)) continue;
            if (op_cost[op2] > budget || LGc[d3] + op_gdw[op2] > req_g || LAc[d3] + op_adw(op2) > req_a) continue;
        } else {
            d3 = DIV[rndint(ndiv)];
            op2 = nl_root ? libnl[rndint(nlibnl)] : lib2[rndint(nlib2)];
            xfirst = op_sym(op2) ? 1 : (int)(rnd() & 1);
        }
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
        u64 t0 = TT[0], c0 = CC[0];
        for (int i = 0; i < np; i++) {
            if ((PV0[i] ^ t0) & c0) continue;          /* first word, from a dense array */
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
        /* wanted partner value = GX ^ pv with GX = GT (XOR) or ~GT on the care set (XNOR) */
        for (int w = 0; w < W; w++) CC[w] = (r == 6 ? GT[w] : ~GT[w]) & CARE[w];
        u64 dgx = ldig(CC);
        for (int q = 0; q < lim; q++) {
            int i = np <= 30000 ? q : rndint(np);
            PEnt *e = &PE[i];
            const u64 *pv = PV + (size_t)i * W;
            u64 d = dgx ^ PD[i];
            int nh = 0; unsigned hh = dslot(d);
            while (PHT[hh].gen == pgen && nh < 2) {
                int j = PHT[hh].idx;
                if (PD[j] == d) {
                    const u64 *pj = PV + (size_t)j * W; int eq = 1;
                    for (int w = 0; w < W; w++) if (pj[w] != (CC[w] ^ pv[w])) { eq = 0; break; }
                    if (eq) hits[nh++] = j;
                }
                hh = (hh + 1) & phmask;
            }
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

/* ------------------------------------------------------------------ xspan (review5 S1)
 * Linear-span resubstitution: is signal s, on its care set, the XOR of ANY number of signals
 * outside its fanout cone (optionally complemented)?  Decided exactly by Gaussian elimination
 * over GF(2) on the divisor tables masked by CARE; resub1-3 reach at most four XORed divisors
 * and only within the cost budget.  The replacement has no AND gate, so every AND-like gate in
 * the fanout-free cone of s disappears: the move is tried only when that cone holds one
 * (xspan_any 1: always).  Gates of that cone are not divisors (s is trivially the XOR of its own
 * operands; using a cone gate would keep its ANDs alive), so every solution found removes at
 * least one AND.  Divisors must respect the AND-depth requirement at s; the XOR tree is
 * built smallest-arrival-first, and the ordinary evaluation and acceptance decide the rest
 * (feasibility, lexicographic objective), so cost may go up when A is the first key.
 * Each of the xspan_tries solves uses another divisor order: by gate level (shallow first), then
 * random orders; elimination stops at the first prefix whose span contains s. */
#define XMAX 1024
#define XCW (XMAX / 64)
static u64 *XB, *XC; static int *XP, *XORD, *XSEL, *XLV; static Gate *XG;
static long st_xspan_solved;
static int xspan_solve(const int *ord, int nd, int use_const, int *sel, int *cst) {
    u64 tc[XCW]; memset(tc, 0, sizeof tc);
    int nz = 0, rank = 0, nv = nd + use_const;
    for (int w = 0; w < W; w++) { TT[w] = GT[w]; nz |= TT[w] != 0; }
    for (int q = 0; q < nv && nz; q++) {
        u64 *b = XB + (size_t)rank * W, *bc = XC + (size_t)rank * XCW;
        if (use_const && q == 0) for (int w = 0; w < W; w++) b[w] = CARE[w];
        else { const u64 *vd = Vcur + (size_t)ord[q - use_const] * W; for (int w = 0; w < W; w++) b[w] = vd[w] & CARE[w]; }
        memset(bc, 0, sizeof(u64) * XCW); bc[q >> 6] |= 1ULL << (q & 63);
        for (int i = 0; i < rank; i++) {
            int pv = XP[i];
            if ((b[pv >> 6] >> (pv & 63)) & 1) {
                const u64 *o = XB + (size_t)i * W, *oc = XC + (size_t)i * XCW;
                for (int w = 0; w < W; w++) b[w] ^= o[w];
                for (int w = 0; w < XCW; w++) bc[w] ^= oc[w];
            }
        }
        int pv = -1;
        for (int w = 0; w < W; w++) if (b[w]) { pv = w * 64 + __builtin_ctzll(b[w]); break; }
        if (pv < 0) continue;                       /* dependent on the earlier ones */
        XP[rank++] = pv;
        if ((TT[pv >> 6] >> (pv & 63)) & 1) {
            nz = 0;
            for (int w = 0; w < W; w++) { TT[w] ^= b[w]; nz |= TT[w] != 0; }
            for (int w = 0; w < XCW; w++) tc[w] ^= bc[w];
        }
    }
    if (nz) return 0;
    int ns = 0; *cst = 0;
    for (int q = 0; q < nv; q++) if ((tc[q >> 6] >> (q & 63)) & 1) {
        if (use_const && q == 0) *cst = 1; else sel[ns++] = ord[q - use_const];
    }
    return ns;
}
static void xspan_cands(void) {
    ncand = 0; nseen = 0;
    if (linear_mode || !op_ok[6] || (mffc_a < 1 && !xspan_any)) return;
    int base = N + cur.ng, nd = 0, use_const = op_ok[9] || op_ok[3];
    for (int i = 0; i < ndiv && nd < XMAX - 1; i++)
        if (LAc[DIV[i]] <= req_a && (xspan_any || MFM[DIV[i]] != mfm_gen)) XORD[nd++] = DIV[i];
    if (!nd) return;
    for (int tr = 0; tr < xspan_tries; tr++) {
        if (tr == 0) {                 /* stable insertion sort by gate level; DIV was shuffled, so ties are random */
            for (int i = 1; i < nd; i++) { int x = XORD[i], j = i; while (j > 0 && LGc[XORD[j - 1]] > LGc[x]) { XORD[j] = XORD[j - 1]; j--; } XORD[j] = x; }
        } else for (int i = nd - 1; i > 0; i--) { int j = rndint(i + 1); int x = XORD[i]; XORD[i] = XORD[j]; XORD[j] = x; }
        int cst, ns = xspan_solve(XORD, nd, use_const, XSEL, &cst);
        if (ns < 1) return;            /* not in the span of all divisors (no order helps), or constant on the care set */
        if (cst && ns == 1 && !op_ok[3]) continue;
        if (cur.ng + ns + 1 > GCAP) continue;
        st_xspan_solved++;
        Gate *xg = XG + (size_t)tr * (XMAX + 2); int nx = 0, n = ns;
        for (int i = 0; i < ns; i++) XLV[i] = LGc[XSEL[i]];
        double nc = 0;
        while (n > 1) {
            int i0 = 0, i1 = 1; if (XLV[i1] < XLV[i0]) { i0 = 1; i1 = 0; }
            for (int i = 2; i < n; i++) { if (XLV[i] < XLV[i0]) { i1 = i0; i0 = i; } else if (XLV[i] < XLV[i1]) i1 = i; }
            int op = 6; if (n == 2 && cst && op_ok[9]) { op = 9; cst = 0; }
            xg[nx].op = op; xg[nx].a = XSEL[i0]; xg[nx].b = XSEL[i1]; nc += op_cost[op];
            int lv = (XLV[i0] > XLV[i1] ? XLV[i0] : XLV[i1]) + op_gdw[op];
            int lo = i0 < i1 ? i0 : i1, hi = i0 < i1 ? i1 : i0;
            XSEL[lo] = base + nx; XLV[lo] = lv; XSEL[hi] = XSEL[n - 1]; XLV[hi] = XLV[n - 1]; n--; nx++;
        }
        if (cst) { xg[nx].op = 3; xg[nx].a = xg[nx].b = XSEL[0]; nc += op_cost[3]; XSEL[0] = base + nx; nx++; }
        Cand c; c.k = nx; c.ext = xg; c.root = XSEL[0]; c.ncost = nc; add_cand(&c);
    }
}

/* fraig: merge gates whose complete function equals an earlier signal (never deeper).
 * review5 K4 (`fraig 2`): the old rule looked only at the first signal with the same function
 * and merged the later one into it; when the earlier one was deeper nothing happened and the
 * later one was not even remembered.  With fraig 2 the pair is merged into whichever of the two
 * is not deeper in both gate depth and AND depth (the later signal cannot depend on a strictly
 * deeper earlier one, so replacing the earlier by the later makes no cycle; rebuild checks
 * anyway), and signals with incomparable depths are all kept as representatives. */
static int *FR_map; static int *FR_ht; static int FR_hts; static long st_fraig_rev;
static int fraig(Circ *c, u64 *V) {
    int tot = N + c->ng, any = 0, lv = 0;
    int hts = 64; while (hts < 2 * tot) hts <<= 1;
    if (hts > FR_hts) hts = FR_hts;
    for (int i = 0; i < hts; i++) FR_ht[i] = -1;
    for (int v = 0; v < tot; v++) {
        FR_map[v] = v;
        const u64 *pv = V + (size_t)v * W;
        u64 h = 0x777; for (int w = 0; w < W; w++) { h ^= pv[w] & wmask(w); h *= 0x9E3779B97F4A7C15ULL; h ^= h >> 29; }
        unsigned hh = (unsigned)(h >> 20) & (hts - 1);
        int done = 0;
        while (FR_ht[hh] >= 0) {
            int u = FR_ht[hh]; const u64 *pu = V + (size_t)u * W; int eq = 1;
            for (int w = 0; w < W; w++) if ((pu[w] ^ pv[w]) & wmask(w)) { eq = 0; break; }
            if (eq) {
                if (!lv) { levels(c, LG_tmp, LA_tmp); lv = 1; }      /* review5 P3: only when two signals are equal */
                if (LG_tmp[u] <= LG_tmp[v] && LA_tmp[u] <= LA_tmp[v]) { FR_map[v] = u; any = 1; done = 1; break; }
                if (use_fraig < 2) { done = 1; break; }              /* old rule: first equal signal decides */
                if (LG_tmp[v] <= LG_tmp[u] && LA_tmp[v] <= LA_tmp[u]) {   /* earlier one is the deeper: replace it */
                    FR_map[u] = v; FR_ht[hh] = v; any = 1; done = 1; st_fraig_rev++; break;
                }
            }
            hh = (hh + 1) & (hts - 1);
        }
        if (!done) FR_ht[hh] = v;
    }
    if (!any) return 0;
    if (rebuild(c, -1, -1, 0, 0, FR_map, &tmp_c, 1) < 0) return 0;
    circ_copy(c, &tmp_c); sim(c, V);
    return 1;
}

/* Is circuit x the same as y up to the numbering of gates?  Each gate gets a structural hash
 * (op, operand hashes; operands sorted for symmetric ops).  After strash no two gates of one
 * circuit are structurally equal, so gates are paired by sorting on the hash, and the pairing
 * is then checked exactly (op and mapped operands), so a hash collision cannot give a false
 * 'same'.  rebuild() renumbers gates (DFS post-order), so a raw memcmp misses most no-ops. */
static u64 *SH_x, *SH_y; static int *SH_ix, *SH_iy, *SH_map; static const u64 *SH_key;
static u64 shash_mix(u64 h) { h ^= h >> 33; h *= 0xff51afd7ed558ccdULL; h ^= h >> 33; h *= 0xc4ceb9fe1a85ec53ULL; return h ^ (h >> 33); }
static void shash(const Circ *c, u64 *h) {
    for (int i = 0; i < N; i++) h[i] = shash_mix(0x1234567ULL + i);
    for (int j = 0; j < c->ng; j++) {
        const Gate *g = &c->g[j]; u64 x = h[g->a], y = op_unary(g->op) ? 0 : h[g->b];
        if (!op_unary(g->op) && op_sym(g->op) && x > y) { u64 t = x; x = y; y = t; }
        h[N + j] = shash_mix(shash_mix(x * 31 + g->op) ^ (y + 0x9E3779B97F4A7C15ULL));
    }
}
static int sh_cmp(const void *p, const void *q) { u64 a = SH_key[*(const int *)p], b = SH_key[*(const int *)q]; return a < b ? -1 : a > b; }
/* review5 P2: y is always the current circuit; its hashes, their sum and the sorted order are kept
 * until it changes (SH_ycached, cleared in state_refresh).  Equal structures have equal hash
 * multisets, so a different sum or output hash means "different" before anything is sorted. */
static u64 SH_ysum;
static int same_structure(const Circ *x, const Circ *y) {
    if (x->ng != y->ng) return 0;
    if (!SH_ycached) {
        shash(y, SH_y); SH_ysum = 0;
        for (int j = 0; j < y->ng; j++) { SH_iy[j] = N + j; SH_ysum += SH_y[N + j]; }
        SH_key = SH_y; qsort(SH_iy, y->ng, sizeof(int), sh_cmp);
        SH_ycached = 1;
    }
    shash(x, SH_x);
    u64 xsum = 0; for (int j = 0; j < x->ng; j++) xsum += SH_x[N + j];
    if (xsum != SH_ysum) return 0;
    for (int k = 0; k < M; k++) if (SH_x[x->out[k]] != SH_y[y->out[k]]) return 0;
    for (int j = 0; j < x->ng; j++) SH_ix[j] = N + j;
    SH_key = SH_x; qsort(SH_ix, x->ng, sizeof(int), sh_cmp);
    for (int i = 0; i < N; i++) SH_map[i] = i;
    for (int j = 0; j < x->ng; j++) { if (SH_x[SH_ix[j]] != SH_y[SH_iy[j]]) return 0; SH_map[SH_ix[j]] = SH_iy[j]; }
    for (int j = 0; j < x->ng; j++) {
        const Gate *g = &x->g[j], *h = &y->g[SH_map[N + j] - N];
        if (g->op != h->op) return 0;
        int a = SH_map[g->a], b = op_unary(g->op) ? h->b : SH_map[g->b];
        if (a == h->a && b == h->b) continue;
        if (!op_unary(g->op) && op_sym(g->op) && a == h->b && b == h->a) continue;
        return 0;
    }
    for (int k = 0; k < M; k++) if (SH_map[x->out[k]] != y->out[k]) return 0;
    return 1;
}

/* evaluate candidate: build into cand_c, return obj (or +inf if invalid) */
static int eval_cand(int s, const Cand *k, Metrics *m) {
    if (rebuild(&cur, s, k->root, cand_gates(k), k->k, 0, &cand_c, 1) < 0) return 0;
    sim(&cand_c, Vcand);
    if (!outputs_ok(&cand_c, Vcand)) {
        fprintf(stderr, "INTERNAL: candidate breaks the function (s=%d k=%d)\n", s, k->k); exit(3);
    }
    if (use_fraig) for (int it = 0; it < 3 && fraig(&cand_c, Vcand); it++);
    metrics(&cand_c, m);
    return 1;
}

/* ------------------------------------------------------------------ move trace */
static FILE *tmv; static Circ tmp_before; static Metrics mprev;
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
    SH_x = malloc(sizeof(u64) * S); SH_y = malloc(sizeof(u64) * S);
    SH_ix = malloc(sizeof(int) * S); SH_iy = malloc(sizeof(int) * S); SH_map = malloc(sizeof(int) * S);

    int stats_only = !strcmp(argv[1], "--stats");
    if (stats_only) {
        if (argc < 3) die("usage: bfx --stats CIRCUIT");
        for (int i = 0; i < 16; i++) { op_ok[i] = 1; op_cost[i] = 1; op_gdw[i] = 1; }
        strcpy(cfg_in, argv[2]);
    } else parse_config(argv[1]);
    seed_rng(cfg_seed);
    if (!stats_only) {
        int cost_first = lex_n ? lex_k[0] == 0 : (w_cost >= w_g && w_cost >= w_a && w_cost >= w_gd && w_cost >= w_ad);
        double u = 0;
        for (int op = 0; op < 16; op++) if (op_ok[op] && op_cost[op] > 0 && (u == 0 || op_cost[op] < u)) u = op_cost[op];
        cost_unit_v = cost_first && u > 0 ? u : 1;
        if (!scale_abs) { T0 *= cost_unit_v; uphill *= cost_unit_v; if (max_excess < 1e17) max_excess *= cost_unit_v; }
        if (cost_unit_v != 1) printf("scale unit %.10g (T0, uphill, max_excess in units of the cheapest gate)\n", cost_unit_v);
    }
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
    Metrics mraw; metrics(&cur, &mraw);
    if (rebuild(&cur, -1, -1, 0, 0, 0, &tmp_c, 1) < 0) die("start circuit cannot be cleaned");
    circ_copy(&cur, &tmp_c);
    if (!stats_only && tmp_c.ng != mraw.g)   /* strash / dead-gate removal of the start, before the clock */
        printf("start_cleanup raw cost %.10g G %d A %d GD %d AD %d\n", mraw.cost, mraw.g, mraw.a, mraw.gd, mraw.ad);
    state_refresh();
    if (stats_only) {
        printf("cost %.10g G %d A %d GD %d AD %d\n", mcur.cost, mcur.g, mcur.a, mcur.gd, mcur.ad); return 0;
    }
    nlib2 = 0;
    int canon[] = {8, 14, 6, 9, 7, 1, 4, 13};
    for (int i = 0; i < 8; i++) if (op_ok[canon[i]]) lib2[nlib2++] = canon[i];
    nlibnl = 0;
    for (int i = 0; i < nlib2; i++) if (op_nl(lib2[i])) libnl[nlibnl++] = lib2[i];
    PCAP = 200000; if ((size_t)PCAP * W > 16000000) PCAP = 16000000 / W;
    PE = malloc(sizeof(PEnt) * PCAP); PV = malloc(sizeof(u64) * (size_t)PCAP * W);
    PD = malloc(sizeof(u64) * PCAP); PV0 = malloc(sizeof(u64) * PCAP); L1 = malloc(sizeof(int) * PCAP);
    phts = 1; while (phts < PCAP * 2) phts <<= 1; PHT = calloc(phts, sizeof(PSlot));
    CAND = malloc(sizeof(Cand) * (cand_cap + 1));
    if (mv_w[MV_XSPAN] > 0) {
        XB = malloc(sizeof(u64) * (size_t)XMAX * W); XC = malloc(sizeof(u64) * XMAX * XCW); XP = malloc(sizeof(int) * XMAX);
        XORD = malloc(sizeof(int) * XMAX); XSEL = malloc(sizeof(int) * XMAX); XLV = malloc(sizeof(int) * XMAX);
        XG = malloc(sizeof(Gate) * (size_t)xspan_tries * (XMAX + 2));
    }

    circ_copy(&best, &cur); mbest = mcur;
    FILE *trace = cfg_trace[0] ? fopen(cfg_trace, "w") : 0;
    tmv = cfg_tracemoves[0] ? fopen(cfg_tracemoves, "w") : 0;
    if (tmv) circ_alloc(&tmp_before);
    double t0 = now_s(), last_best = 0, mvsum = 0;
    for (int i = 0; i < NMOVES; i++) mvsum += mv_w[i];
    printf("start cost %.10g G %d A %d GD %d AD %d feas %d obj %.17g\n", mcur.cost, mcur.g, mcur.a, mcur.gd, mcur.ad, mcur.feas, mcur.obj);
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
        if (stalled && mcmp(&mcur, &mbest) > 0) {
            circ_copy(&cur, &best); state_refresh(); last_best = t; last_best_it = it; restarts++;
        }
        if (cur.ng == 0) break;
        double r = rnd01() * mvsum; int mv = 0;
        while (mv < NMOVES - 1 && r >= mv_w[mv]) { r -= mv_w[mv]; mv++; }
        while (mv > 0 && mv_w[mv] <= 0) mv--;          /* a move with weight 0 is never chosen (rounding) */
        double tm = now_s();
        st_prop[mv]++;
        int s = sweep ? N + (int)((it - 1) % cur.ng) : N + rndint(cur.ng);
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
        if (mv == MV_XSPAN) xspan_cands(); else find_cands(mv + 1);
        st_cands[mv] += ncand;
        /* evaluate all candidates; take the best improvement, else a random one under Metropolis */
        int bi = -1, bfeas = 0; Metrics m, bm;
        /* review5 K2: these were fixed 1024-entry arrays, so with cand_cap > 1024 the candidates
         * past the first 1024 were kept but never evaluated */
        static int *order, *neu, *up; static double *upd;
        if (!order) {
            order = malloc(sizeof(int) * (cand_cap + 1)); neu = malloc(sizeof(int) * (cand_cap + 1));
            up = malloc(sizeof(int) * (cand_cap + 1)); upd = malloc(sizeof(double) * (cand_cap + 1));
        }
        int no = ncand, nneu = 0, nup = 0;
        for (int i = 0; i < no; i++) order[i] = i;
        for (int i = no - 1; i > 0; i--) { int j = rndint(i + 1); int x = order[i]; order[i] = order[j]; order[j] = x; }
        for (int q = 0; q < no; q++) {
            int i = order[q];
            if (!eval_cand(s, &CAND[i], &m)) continue;
            if (skip_noop && m.g == mcur.g && m.a == mcur.a && m.gd == mcur.gd && m.ad == mcur.ad
                && same_structure(&cand_c, &cur)) { st_noop++; continue; }
            if (repair_keep && !mcur.feas && (m.xa > mcur.xa || m.xad > mcur.xad || m.xgd > mcur.xgd)) continue;
            double d = ldelta(&m, &mcur); int cc = mcmp(&m, &mcur);
            if ((m.feas || !mcur.feas) && (bi < 0 || mcmp(&m, &bm) < 0)) { bm = m; bi = i; bfeas = m.feas; }
            if (cc == 0 && m.feas >= mcur.feas) neu[nneu++] = i;
            else if (cc > 0 && ldelta(&m, &mbest) <= max_excess && m.feas >= mcur.feas) { upd[nup] = d > 1e-12 ? d : 1e-12; up[nup++] = i; }
        }
        int accept = -1;
        /* feasibility first: a feasible state is never left for an infeasible one */
        if (bi >= 0 && mcmp(&bm, &mcur) < 0 && (bfeas || !mcur.feas)) accept = bi;
        else if (use_neutral && nneu && (nup == 0 || T <= 0 || rnd01() < 0.75)) accept = neu[rndint(nneu)];
        else if (nup && T > 0) { int q = rndint(nup); if (rnd01() < exp(-upd[q] / T)) accept = up[q]; }
        if (accept >= 0) {
            if (tmv) {
                Cand *k = &CAND[accept]; Gate *gs = &cur.g[s - N];
                fprintf(tmv, "it %ld t %.4f mv %s target s%d=%s(s%d,s%d) mffc_cost %.10g care %d/%d cands %d | new %d gate(s):",
                        it, t, MVNAME[mv], s, OPNAME[gs->op], gs->a, gs->b, mc, popc_care(), patterns(), ncand, k->k);
                const Gate *kg = cand_gates(k);
                for (int q = 0; q < k->k; q++) fprintf(tmv, " n%d=%s(%s%d,%s%d)", q, OPNAME[kg[q].op],
                    kg[q].a >= N + cur.ng ? "n" : "s", kg[q].a >= N + cur.ng ? kg[q].a - N - cur.ng : kg[q].a,
                    kg[q].b >= N + cur.ng ? "n" : "s", kg[q].b >= N + cur.ng ? kg[q].b - N - cur.ng : kg[q].b);
                fprintf(tmv, " root %s%d | before cost %.10g G %d A %d GD %d AD %d", k->root >= N + cur.ng ? "n" : "s",
                        k->root >= N + cur.ng ? k->root - N - cur.ng : k->root, mcur.cost, mcur.g, mcur.a, mcur.gd, mcur.ad);
            }
            Circ *before = tmv ? &tmp_before : 0;
            if (before) { circ_copy(before, &cur); mprev = mcur; }
            eval_cand(s, &CAND[accept], &m);
            circ_copy(&cur, &cand_c); state_refresh();
            int newbest = (mcur.feas || !mbest.feas) && (mcmp(&mcur, &mbest) < 0 || (mcur.feas && !mbest.feas));
            if (tmv) {
                fprintf(tmv, " -> after cost %.10g G %d A %d GD %d AD %d\n", mcur.cost, mcur.g, mcur.a, mcur.gd, mcur.ad);
                if (newbest) {
                    char fn[1200];
                    snprintf(fn, sizeof fn, "%s.it%ld.before", cfg_tracemoves, it); write_circuit(fn, before, &mprev, "before");
                    snprintf(fn, sizeof fn, "%s.it%ld.after", cfg_tracemoves, it); write_circuit(fn, &cur, &mcur, "after");
                }
                fflush(tmv);
            }
            st_acc[mv]++;
            if (newbest) {
                st_imp[mv]++;
                circ_copy(&best, &cur); mbest = mcur; last_best = t; last_best_it = it;
                write_circuit(cfg_out, &best, &mbest, "best");
                printf("best t %.3f it %ld mv %s cost %.10g G %d A %d GD %d AD %d obj %.17g\n", t, it, MVNAME[mv],
                       mbest.cost, mbest.g, mbest.a, mbest.gd, mbest.ad, mbest.obj);
                fflush(stdout);
            }
            if (trace) fprintf(trace, "%.3f %ld %s %.10g %d %d %d %d\n", t, it, MVNAME[mv], mcur.cost, mcur.g, mcur.a, mcur.gd, mcur.ad);
        }
        st_time[mv] += now_s() - tm;
    }
    if (trace) fclose(trace);
    /* final guard: re-simulate the best from scratch */
    sim(&best, Vcur);
    if (!outputs_ok(&best, Vcur)) die("INTERNAL: best circuit does not match target");
    write_circuit(cfg_out, &best, &mbest, "final");
    printf("final cost %.10g G %d A %d GD %d AD %d obj %.17g feas %d iters %ld restarts %ld seconds %.2f\n",
           mbest.cost, mbest.g, mbest.a, mbest.gd, mbest.ad, mbest.obj, mbest.feas, it, restarts, now_s() - t0);
    for (int i = 0; i < NMOVES; i++)
        if (i < 3 || mv_w[i] > 0) printf("move %s prop %ld acc %ld imp %ld cands %ld time %.2f\n", MVNAME[i], st_prop[i], st_acc[i], st_imp[i], st_cands[i], st_time[i]);
    printf("noop_candidates_skipped %ld\n", st_noop);
    if (use_fraig >= 2) printf("fraig_reverse_merges %ld\n", st_fraig_rev);
    if (mv_w[MV_XSPAN] > 0) printf("xspan_solutions %ld\n", st_xspan_solved);
    return 0;
}
