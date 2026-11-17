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
/* T0, uphill and max_excess are given in units of one gate of the first objective key
 * (`scale_abs 1` keeps them absolute, the behaviour before 2026-11-14).  unit = cheapest allowed gate cost
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
/* size of the difference a - b for Metropolis and max_excess, measured on the first
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
static double mv_w[NMOVES] = {1, 1, 1, 0};      /* xspan is off unless mv.xspan > 0 */
static const char *MVNAME[NMOVES] = {"resub1", "resub2", "resub3", "xspan"};
static int xspan_tries = 3, xspan_any = 0;
/* repair_keep: the violation is the SUM of the cap excesses, so a repair may pay for one unit of
 * gate depth with an AND above cap.a (or AND depth above cap.ad) and then sit at violation 1 in
 * a cap that is much harder to repair.  repair_keep 1: while the current circuit violates a cap,
 * no move may raise the excess of any single cap. */
static int repair_keep = 0;
/* nl_root: root op of the sampled two-gate candidates s = op2(X, d3).  0 (old): op2 uniform over
 * the binary library, although XOR/XNOR roots were already enumerated exactly just before (with
 * the NIST library 2 of 3 samples repeat that work).  1: op2 only among the AND-like library ops.
 * 2: no sampling, every divisor d3 with every AND-like op and orientation (most d3 fail the
 * one-pass feasibility test before the pair table is scanned). */
static int nl_root = 0;
static int sweep = 0;     /* 1 = target gates in index order instead of at random (exact scans) */
/* Options added 2026-11-16 (phase 2, W1), all off by default (the defaults keep the old trajectory):
 * tgt_w.mffc1 / tgt_w.and / tgt_w.viol: target weights (U1 B1).  The target s is drawn with weight
 *   (mffc1 ? tgt_w.mffc1 : 1) * (AND-like ? tgt_w.and : 1) * (on a violating path ? tgt_w.viol : 1), where
 *   mffc1 = the fanout-free cone of s is s alone and "violating path" counts only while the current state
 *   violates a GD/AD cap; all 1 = uniform (the old draw).
 * uphill.resub2 / uphill.resub3: new-gate budget slack of that move kind (U1 B2; default = uphill; same units).
 * repair_uphill R: while the current state violates a cap, a candidate with the same violation and at most R more
 *   summed path excess (or equal path excess, worse keys within max_excess) is an uphill step (Metropolis, R in
 *   path-excess units, each priced as one cheapest gate) instead of being out of reach (U1 B4).
 * stop_stall_it N: stop when N iterations passed without a new best (U1 F7; stop reason "stall"). */
static double tw_mffc1 = 1, tw_and = 1, tw_viol = 1, uphill_mv[3] = {-1, -1, -1}, repair_uphill = 0;
static long stop_stall_it = 0;
static int pair_xor = 0, pxor = 0;   /* pair_xor option / in effect (see build_pairs) */
/* chain_p P (idea 04, 2026-11-17; default 0 = off, and then no code path, random draw or output line changes):
 * with probability P per iteration (only while the current state meets every cap) a two-step compound move
 * replaces the ordinary move; see chain_move.  chain.k1 step-1 circuits expanded, chain.k2 step-2 targets per
 * step-1 circuit, chain.rand2 random extra step-2 targets, chain.up1 step-1 new-gate budget slack (units as
 * uphill), chain.maxup largest actual step-1 rise expanded (default = up1), chain.lev1 / chain.lev2 new gates
 * per step (1..3), chain.accept 1 also takes a neutral compound (0: improvements only), chain.freed 0: step-2
 * targets drawn at random only (ablation of the freed-signal choice). */
#define CH_K1MAX 16
/* l3n N (idea 04; default 0 = off): resub3 also tries s = r(X1, X2) with r an AND-like library op and X1, X2 pair-table
 * values (3 new gates, e.g. AND(a^b, c^d)); at most N pair checks per root op and move.  See l3n_cands. */
static long l3n_lim = 0; static long st_l3n_moves, st_l3n_ea, st_l3n_chk, st_l3n_hit;
static double chain_p = 0, ch_up1 = 2, ch_maxup = -1, ch_up1s, ch_maxups;
static int ch_k1 = 4, ch_k2 = 8, ch_rand2 = 2, ch_lev1 = 2, ch_lev2 = 3, ch_accept = 1, ch_freed = 1;
static int l1_fast = 1;   /* resub1 through l1_direct (same result; config `l1_direct 0` = the old scan, for tests) */
static int dmax = 200, pdiv = 90, nl_samples = 12, cand_cap = 40, use_fraig = 1;
static int use_neutral = 1, use_odc = 1, linear_mode = 0;   /* ablation switches; linear: see main */
static int skip_noop = 1;    /* v2: a candidate whose rebuilt circuit equals the current one is no move */
static long st_noop;
static char cfg_tracemoves[1024];
static char cfg_keep_bests[1024];   /* keep_bests DIR: every new best also written to DIR/best-<k>.bfx (instrumentation) */
static long n_kept_bests;
static long max_iters = -1;
/* Instrumentation (2026-11-16): `kstat` lines.  The final summary (stop reason, acceptance kinds, empty
 * moves, evaluations, repair phase) is always printed after the old final lines; `stats_every_it N` /
 * `stats_every_s S` (default 0 = off) add a periodic `kstat periodic` line.  None of this draws a random
 * number or changes a decision: the search trajectory is the same with or without it. */
static long stats_every_it = 0; static double stats_every_s = 0; static int kst_time = 0;   /* kstat_time 1: phase times */
static int cfg_clock = 0;     /* clock: 0 real (default), 1 cpu, 2 mono; see now_s */

static void die(const char *m) { fprintf(stderr, "bfx: %s\n", m); exit(2); }

/* op number of a cost.N / gdw.N key; anything outside 0..15 is an error (it would write past the op tables) */
static int cfg_op(const char *t) {
    char *e; long op = strtol(t, &e, 10);
    if (e == t || *e || op < 0 || op > 15) { fprintf(stderr, "bfx: bad op number in config key (%s)\n", t); exit(2); }
    return (int)op;
}
static void parse_config(const char *path) {
    FILE *f = fopen(path, "r"); if (!f) die("cannot open config");
    char k[256], v[1024], line[2048];
    for (int i = 0; i < 16; i++) { op_ok[i] = 0; op_cost[i] = 0; op_gdw[i] = 1; }
    /* one "key value" per line (a token reader would take the first word of the next line as the
     * value of a one-word comment and then drop the rest of that line).
     * Blank lines and lines starting with # are skipped; a path value is the rest of the line. */
    while (fgets(line, sizeof line, f)) {
        char *p = line + strspn(line, " \t\r\n");
        if (!*p || *p == '#') continue;
        if (sscanf(p, "%255s %1023s", k, v) != 2) { fprintf(stderr, "bfx: config key %s has no value\n", k); exit(2); }
        if (!strcmp(k, "in") || !strcmp(k, "out") || !strcmp(k, "trace") || !strcmp(k, "tracemoves") || !strcmp(k, "keep_bests")) {
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
        else if (!strcmp(k, "uphill.resub2")) uphill_mv[1] = atof(v);
        else if (!strcmp(k, "uphill.resub3")) uphill_mv[2] = atof(v);
        else if (!strcmp(k, "tgt_w.mffc1")) tw_mffc1 = atof(v);
        else if (!strcmp(k, "tgt_w.and")) tw_and = atof(v);
        else if (!strcmp(k, "tgt_w.viol")) tw_viol = atof(v);
        else if (!strcmp(k, "repair_uphill")) repair_uphill = atof(v);
        else if (!strcmp(k, "stop_stall_it")) stop_stall_it = atol(v);
        else if (!strcmp(k, "pair_xor")) pair_xor = atoi(v);
        else if (!strcmp(k, "l1_direct")) l1_fast = atoi(v);
        else if (!strcmp(k, "chain_p")) chain_p = atof(v);
        else if (!strcmp(k, "l3n")) l3n_lim = atol(v);
        else if (!strcmp(k, "chain.k1")) ch_k1 = atoi(v);
        else if (!strcmp(k, "chain.k2")) ch_k2 = atoi(v);
        else if (!strcmp(k, "chain.rand2")) ch_rand2 = atoi(v);
        else if (!strcmp(k, "chain.up1")) ch_up1 = atof(v);
        else if (!strcmp(k, "chain.maxup")) ch_maxup = atof(v);
        else if (!strcmp(k, "chain.lev1")) ch_lev1 = atoi(v);
        else if (!strcmp(k, "chain.lev2")) ch_lev2 = atoi(v);
        else if (!strcmp(k, "chain.accept")) ch_accept = atoi(v);
        else if (!strcmp(k, "chain.freed")) ch_freed = atoi(v);
        else if (!strncmp(k, "mv.", 3)) {
            int hit = 0;
            for (int i = 0; i < NMOVES; i++) if (!strcmp(k + 3, MVNAME[i])) { mv_w[i] = atof(v); hit = 1; }
            if (!hit) { fprintf(stderr, "bfx: unknown move %s\n", k); exit(2); }   /* never ignored */
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
        else if (!strcmp(k, "stats_every_it")) stats_every_it = atol(v);
        else if (!strcmp(k, "stats_every_s")) stats_every_s = atof(v);
        else if (!strcmp(k, "kstat_time")) kst_time = atoi(v);
        else if (!strcmp(k, "keep_bests")) strcpy(cfg_keep_bests, v);
        else if (!strcmp(k, "clock")) {
            if (!strcmp(v, "real")) cfg_clock = 0; else if (!strcmp(v, "cpu")) cfg_clock = 1; else if (!strcmp(v, "mono")) cfg_clock = 2;
            else die("clock must be real, cpu or mono");
        }
        else { fprintf(stderr, "bfx: unknown key %s\n", k); exit(2); }
    }
    fclose(f);
    if (cand_cap < 1) die("cand_cap must be at least 1");
    if (chain_p < 0 || chain_p > 1) die("chain_p must be in 0..1");
    if (ch_k1 < 1 || ch_k1 > CH_K1MAX || ch_k2 < 0 || ch_rand2 < 0 || ch_lev1 < 1 || ch_lev1 > 3 || ch_lev2 < 1 || ch_lev2 > 3
        || ch_accept < 0 || ch_accept > 1 || ch_up1 < 0) die("chain.*: k1 1..16, k2/rand2 >= 0, lev1/lev2 1..3, accept 0/1, up1 >= 0");
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
static Circ cur, best, tmp_c;
static u64 *Vcur, *Vcand, *ALT;
static int *LGc, *LAc, *RGc, *RAc, *REF;
static unsigned char *TFO;
static Metrics mcur, mbest;
static int *DIV; static int ndiv;
static u64 CARE[1024], GT[1024], TT[1024], CC[1024];

static int SH_ycached;   /* same_structure's cache of the current circuit */
static unsigned NO_gen;   /* state number (bumped by state_refresh; the no-op pre-check's tables follow it) */
static void state_refresh(void) {
    SH_ycached = 0; NO_gen++;
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
 * Each entry keeps a 64-bit digest of its masked value that is GF(2)-linear in the
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
/* form (kstat only): 0 level 0, 1 level 1, 2 level-2 XOR/XNOR root, 3 level-2 sampled root, 4 level 3, 5 xspan */
#define NFORM 7
static const char *FORMNAME[NFORM] = {"L0", "L1", "L2x", "L2n", "L3", "XS", "L3n"};
static int nform_p = 6;     /* forms printed: the old six unless l3n is on (idea 04; same output lines when off) */
typedef struct { int k; Gate g[3]; int root; double ncost; const Gate *ext; unsigned char form; } Cand;   /* ext: gate list of an xspan candidate (k may exceed 3) */
static inline const Gate *cand_gates(const Cand *c) { return c->ext ? c->ext : c->g; }
static Cand *CAND; static int ncand, nseen;
static long mv_seen[NFORM];      /* candidates of each form seen by the current move (reservoir input) */
static void add_cand(const Cand *c) {
    nseen++; mv_seen[c->form]++;
    if (ncand < cand_cap) CAND[ncand++] = *c;
    else { int i = rndint(nseen); if (i < cand_cap) CAND[i] = *c; }
}

/* kstat_time 1 (default 0): time of each phase of a move, per move kind (clock reads only, no other effect) */
static double now_s(void);
static int cur_mv = 0;
#define NPH 12
static const char *PHNAME[NPH] = {"care_div", "l0_pairs", "l2x", "l2n", "l3", "xspan", "rebuild", "sim", "fraig", "metrics",
                                  "noop_check", "accept"};
static double st_ph[NMOVES][NPH], ph_last; static int ph_hold;
static inline void ph_mark(int p) { if (kst_time && !ph_hold) { double x = now_s(); st_ph[cur_mv][p] += x - ph_last; ph_last = x; } }
static long mv_probes;           /* hash probe steps of lookup() and of the level-3 loop in the current move */

static int lib2[16], nlib2;   /* binary ops in library, canonical orientation */
static int libnl[16], nlibnl; /* the AND-like ones among them */
static double budget;          /* max new-gate cost for this move */
static double pmin_cost = 0;   /* cheapest op that a pair-table entry can have (binary library ops, NOT) */
static int req_g, req_a;       /* required levels at s */
/* pair_xor 1 (U1 F1, U5 #3; default 0): the pair table keeps XOR entries but no XNOR ones; an XOR entry also
 * stands for its XNOR (its masked value XOR CARE, digest XOR ldig(CARE)), found by a second, complemented
 * lookup.  Same candidate set (same costs and gate-depth weights of XOR and XNOR required, else off), ~1/3
 * fewer entries to build; candidates come in another order, so the trajectory changes. */
static u64 dcare;   /* ldig(CARE) of the current move (pair_xor) */

static inline int arr_g(int op, int la_, int lb_) { return (la_ > lb_ ? la_ : lb_) + op_gdw[op]; }
static inline int arr_a(int op, int la_, int lb_) { return (la_ > lb_ ? la_ : lb_) + op_adw(op); }

/* word 0 of op(a, b) (unmasked): the level-1 early reject of resub1 */
static inline u64 pair_w0(int op, u64 a, u64 b) {
    switch (op) {
    case 8: return a & b; case 6: return a ^ b; case 9: return ~(a ^ b); case 14: return a | b; case 3: return ~a;
    default: return apply(op, a, b);
    }
}
/* resub1 without the pair scan (U1 F4): the level-1 entries op(d1, d2) == GT on the care set are found directly.
 * XOR/XNOR: d2's masked value is d1's XOR GT (or XOR ~GT): hash lookups.  NOT: one compare per divisor.  Every
 * other library op is AND-like: one input combination (x*, y*) gives the odd output o*, so on S = {care, GT = o*}
 * the operands must equal x* and y*: only divisors passing that filter are paired, then checked exactly.  The hits
 * are put in the order of the old enumeration (i, j, t) and pass the same cost and level filters, so L1 is
 * the same list.  Returns 0 (caller enumerates as before) when S is empty for an op (GT constant on the care
 * set), when the table could reach PCAP, or for more than 512 pair divisors. */
typedef struct { long key; int op, a, b; } L1Hit;
static long st_l1_direct, st_l1_scan;   /* kstat l1: resub1 moves served by l1_direct / that fell back to the scan */
static int l1_direct(int nd) {
    long T = 2L * nlib2;
    if (nd > 512 || (long)nd * (nd + 1) / 2 * T + nd + 16 > PCAP) return 0;
    static u64 MVd[512 * 16], MDg[512]; static int HT[1024]; static L1Hit H[4096];
    if (W > 16) return 0;
    int nh = 0, hs = 64; while (hs < 2 * nd) hs <<= 1;
    for (int i = 0; i < nd; i++) {
        const u64 *v = Vcur + (size_t)DIV[i] * W; u64 *m = MVd + (size_t)i * W;
        for (int w = 0; w < W; w++) m[w] = v[w] & CARE[w];
        MDg[i] = ldig(m);
    }
#define L1ADD(K, OP, A, B) do { if (nh >= 4096) return 0; H[nh].key = (K); H[nh].op = (OP); H[nh].a = (A); H[nh].b = (B); nh++; } while (0)
    /* NOT d (i == j, t = 0) */
    if (op_ok[3] && op_cost[3] <= budget)
        for (int i = 0; i < nd; i++) {
            const u64 *m = MVd + (size_t)i * W; int eq = 1;
            for (int w = 0; w < W; w++) if ((m[w] ^ CARE[w]) != GT[w]) { eq = 0; break; }
            if (eq) L1ADD(((long)i * nd + i) * T, 3, DIV[i], DIV[i]);
        }
    int built = 0;
    for (int k = 0; k < nlib2; k++) {
        int op = lib2[k];
        if (op_cost[op] > budget) continue;
        if (op == 6 || op == 9) {
            if (!built) {
                for (int q = 0; q < hs; q++) HT[q] = -1;
                for (int i = 0; i < nd; i++) { unsigned h = dslot(MDg[i]) & (hs - 1); while (HT[h] >= 0) h = (h + 1) & (hs - 1); HT[h] = i; }
                built = 1;
            }
            u64 want[16], dg = ldig(GT) ^ (op == 9 ? ldig(CARE) : 0);
            for (int i = 0; i < nd; i++) {
                const u64 *m = MVd + (size_t)i * W;
                for (int w = 0; w < W; w++) want[w] = m[w] ^ GT[w] ^ (op == 9 ? CARE[w] : 0);
                u64 d = MDg[i] ^ dg;
                for (unsigned h = dslot(d) & (hs - 1); HT[h] >= 0; h = (h + 1) & (hs - 1)) {
                    int j = HT[h];
                    if (j <= i || MDg[j] != d || !eqw(MVd + (size_t)j * W, want)) continue;
                    L1ADD(((long)i * nd + j) * T + 2 * k, op, DIV[i], DIV[j]);
                }
            }
            continue;
        }
        if (!op_nl(op)) return 0;                     /* not expected in the canonical library */
        int xs = -1, ys = -1, os = -1;
        for (int x = 0; x < 2; x++) for (int y = 0; y < 2; y++) {
            int o = (op >> ((x << 1) | y)) & 1, n1 = 0;
            for (int x2 = 0; x2 < 2; x2++) for (int y2 = 0; y2 < 2; y2++) n1 += ((op >> ((x2 << 1) | y2)) & 1) == o;
            if (n1 == 1) { xs = x; ys = y; os = o; }
        }
        u64 S[16]; int any = 0;
        for (int w = 0; w < W; w++) { S[w] = CARE[w] & (os ? GT[w] : ~GT[w]); any |= S[w] != 0; }
        if (!any) return 0;
        /* operand masks: divisor i fits as the first operand (agrees with xs on S) / as the second (ys) */
        static int LA_[512], LB_[512]; int na = 0, nb = 0;
        for (int i = 0; i < nd; i++) {
            const u64 *v = MVd + (size_t)i * W; int fa = 1, fb = 1;
            for (int w = 0; w < W; w++) {
                u64 x = v[w] & S[w];
                if (x != (xs ? S[w] : 0)) fa = 0;
                if (x != (ys ? S[w] : 0)) fb = 0;
            }
            if (fa) LA_[na++] = i;
            if (fb) LB_[nb++] = i;
        }
        u64 pv[16];
        /* t = 2k: a = DIV[i], b = DIV[j], i < j; t = 2k+1 (asymmetric ops): a = DIV[j], b = DIV[i] */
        for (int p = 0; p < na; p++) {
            int ia = LA_[p];
            for (int q = 0; q < nb; q++) {
                int ib = LB_[q];
                if (ia == ib) continue;
                int i, j, t;
                if (ia < ib) { i = ia; j = ib; t = 2 * k; }
                else { if (op_sym(op)) continue; i = ib; j = ia; t = 2 * k + 1; }
                int a = DIV[ia], b = DIV[ib];
                pair_val(op, Vcur + (size_t)a * W, Vcur + (size_t)b * W, CARE, pv);
                if (!eqw(pv, GT)) continue;
                L1ADD(((long)i * nd + j) * T + t, op, a, b);
            }
        }
    }
#undef L1ADD
    /* old order, then the cost (done per op above) and level filters of the scan */
    for (int x = 1; x < nh; x++) { L1Hit h = H[x]; int y = x; while (y > 0 && H[y - 1].key > h.key) { H[y] = H[y - 1]; y--; } H[y] = h; }
    np = 0; nl1 = 0;
    for (int x = 0; x < nh; x++) {
        int op = H[x].op, a = H[x].a, b = H[x].b;
        PEnt *e = &PE[np]; e->op = op; e->a = a; e->b = b;
        e->lg = arr_g(op, LGc[a], LGc[b]); e->la = arr_a(op, LAc[a], LAc[b]);
        if (e->lg > req_g || e->la > req_a) continue;
        L1[nl1++] = np << 1; np++;
    }
    return 1;
}
static void build_pairs(int want_table) {
    np = 0; nl1 = 0;
    int nd = ndiv < pdiv ? ndiv : pdiv;   /* DIV is shuffled: first nd are the pair divisors */
    if (!want_table && l1_fast) { if (l1_direct(nd)) { st_l1_direct++; return; } st_l1_scan++; }
    np = 0; nl1 = 0;
    u64 dgt = ldig(GT), care0 = CARE[0], gt0 = GT[0];
    if (pxor) dcare = ldig(CARE);
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
                if (pxor && want_table && op == 9) continue;       /* pair_xor: XNOR stands behind its XOR entry */
                if (np >= PCAP) goto table;
                PEnt *e = &PE[np]; e->op = op; e->a = a; e->b = b;
                e->lg = arr_g(op, LGc[a], LGc[b]); e->la = arr_a(op, LAc[a], LAc[b]);
                if (e->lg > req_g || e->la > req_a) continue;
                /* resub1 (no table) needs only the entries equal to GT: reject on word 0 before the full value
                 * (np still counts the entry, so the PCAP limit and the kstat counts are those of the full build) */
                if (!want_table && ((pair_w0(op, Vcur[(size_t)a * W], Vcur[(size_t)b * W]) & care0) != gt0)) { np++; continue; }
                u64 *pv = PV + (size_t)np * W;
                pair_val(op, Vcur + (size_t)a * W, Vcur + (size_t)b * W, CARE, pv);
                u64 d = ldig(pv); PD[np] = d; PV0[np] = pv[0];
                if (d == dgt && eqw(pv, GT)) L1[nl1++] = np << 1;
                else if (pxor && want_table && op == 6 && (d ^ dcare) == dgt) {     /* XNOR form equals GT */
                    int eq = 1; for (int w = 0; w < W; w++) if ((pv[w] ^ CARE[w]) != GT[w]) { eq = 0; break; }
                    if (eq) L1[nl1++] = (np << 1) | 1;
                }
                np++;
            }
        }
    }
table:
    /* hash table sized by the entries actually built (linear probing in index order; entries with equal
     * digests keep their insertion order for any table size, so every lookup returns the same entries
     * in the same order as with the old size bound, and the smaller table stays in cache) */
    if (want_table) {
        int hs = 64; while (hs < 2 * np) hs <<= 1;
        phmask = hs - 1;
        if (++pgen == 0) { memset(PHT, 0, sizeof(PSlot) * phts); pgen = 1; }
        for (int q = 0; q < np; q++) {
            unsigned h = dslot(PD[q]);
            while (PHT[h].gen == pgen) h = (h + 1) & phmask;
            PHT[h].gen = pgen; PHT[h].idx = q;
        }
    }
}
/* find up to `lim` pair entries whose masked value equals v (v already masked; d = ldig(v)) */
static int lookup(u64 d, const u64 *v, int *hits, int lim) {
    int nh = 0; unsigned h = dslot(d);
    while (PHT[h].gen == pgen && nh < lim) {
        int i = PHT[h].idx; mv_probes++;
        if (PD[i] == d && eqw(PV + (size_t)i * W, v)) hits[nh++] = i;
        h = (h + 1) & phmask;
    }
    return nh;
}

/* level 3 under pair_xor: X1 ^ X2 = GX (CC) where each of X1, X2 is a stored entry or, for an XOR entry, its
 * XNOR form; every (entry, form) pair once (form key 2*index + complemented, partner key larger) */
static void l3_pxor(int r, int lim, u64 dgx, int base) {
    Cand c; c.ext = 0; c.form = 4;
    u64 X2[1024];
    for (int q = 0; q < lim; q++) {
        int i = np <= 30000 ? q : rndint(np);
        PEnt *e = &PE[i];
        const u64 *pv = PV + (size_t)i * W;
        for (int ci = 0; ci <= (e->op == 6); ci++) {
            int o1 = ci ? 9 : e->op;
            for (int w = 0; w < W; w++) X2[w] = CC[w] ^ pv[w] ^ (ci ? CARE[w] : 0);
            u64 dw = dgx ^ PD[i] ^ (ci ? dcare : 0);
            for (int cj = 0; cj < 2; cj++) {
                u64 d = dw ^ (cj ? dcare : 0);     /* stored digest of the wanted partner entry */
                int hits[2], nh = 0; unsigned hh = dslot(d);
                while (PHT[hh].gen == pgen && nh < 2) {
                    int j = PHT[hh].idx; mv_probes++;
                    if (PD[j] == d && (!cj || PE[j].op == 6)) {
                        const u64 *pj = PV + (size_t)j * W; int eq = 1;
                        for (int w = 0; w < W; w++) if (pj[w] != (X2[w] ^ (cj ? CARE[w] : 0))) { eq = 0; break; }
                        if (eq) hits[nh++] = j;
                    }
                    hh = (hh + 1) & phmask;
                }
                for (int h = 0; h < nh; h++) {
                    int j = hits[h];
                    if (2 * j + cj <= 2 * i + ci) continue;
                    PEnt *e2 = &PE[j]; int o2 = cj ? 9 : e2->op;
                    double nc = op_cost[o1] + op_cost[o2] + op_cost[r];
                    if (nc > budget) continue;
                    if (arr_g(r, e->lg, e2->lg) > req_g || arr_a(r, e->la, e2->la) > req_a) continue;
                    c.k = 3; c.g[0].op = o1; c.g[0].a = e->a; c.g[0].b = e->b;
                    c.g[1].op = o2; c.g[1].a = e2->a; c.g[1].b = e2->b;
                    c.g[2].op = r; c.g[2].a = base; c.g[2].b = base + 1; c.root = base + 2; c.ncost = nc; add_cand(&c);
                }
            }
        }
    }
}

/* level 3, AND-like root of two pair values (idea 04):  s = r(X1, X2).  r gives its odd output o* only at (x*, y*), so
 * on T = {care, s == o*} both operands are fixed (X1 = x*, X2 = y*) and on the rest of the care set they may not be
 * (x*, y*) together.  With A = X1 (x* = 1) or ~X1 on the care set (x* = 0), B likewise: T within A, T within B, and
 * A & B & care & ~T == 0.  Entries passing the T filter are listed (one pass over the table), then pairs are checked,
 * starting at a random entry, at most l3n_lim pair checks per root op.  The pair table holds the entries of the
 * pair divisors within the budget (pair_xor 1: XNOR forms are not tried here). */
static int *L3N_A, *L3N_B;
static void l3n_cands(int base) {
    Cand c; c.ext = 0; c.form = 6;
    if (!L3N_A) { L3N_A = malloc(sizeof(int) * PCAP); L3N_B = malloc(sizeof(int) * PCAP); }
    st_l3n_moves++;
    u64 T[1024], NT[1024];
    for (int ri = 0; ri < nlibnl; ri++) {
        int r = libnl[ri];
        if (pmin_cost + pmin_cost + op_cost[r] > budget) continue;
        int xs = -1, ys = -1, os = -1;
        for (int x = 0; x < 2; x++) for (int y = 0; y < 2; y++) {
            int o = (r >> ((x << 1) | y)) & 1, n1 = 0;
            for (int x2 = 0; x2 < 2; x2++) for (int y2 = 0; y2 < 2; y2++) n1 += ((r >> ((x2 << 1) | y2)) & 1) == o;
            if (n1 == 1) { xs = x; ys = y; os = o; }
        }
        if (xs < 0) continue;
        int any = 0;
        for (int w = 0; w < W; w++) { T[w] = CARE[w] & (os ? GT[w] : ~GT[w]); NT[w] = CARE[w] & ~T[w]; any |= T[w] != 0; }
        if (!any) continue;                       /* s never o* on the care set: lower levels cover it */
        int na = 0, nb = 0, same = xs == ys;
        for (int i = 0; i < np; i++) {
            const u64 *pv = PV + (size_t)i * W; int fa = 1, fb = 1;
            for (int w = 0; w < W && (fa || fb); w++) {
                u64 v1 = pv[w], v0 = ~pv[w] & CARE[w];
                if (T[w] & ~(xs ? v1 : v0)) fa = 0;
                if (T[w] & ~(ys ? v1 : v0)) fb = 0;
            }
            if (fa) L3N_A[na++] = i;
            if (fb && !same) L3N_B[nb++] = i;
        }
        int *LB = same ? L3N_A : L3N_B; if (same) nb = na;
        st_l3n_ea += na;
        if (!na || !nb) continue;
        long chk = 0; int p0 = rndint(na);
        for (int pp = 0; pp < na && chk < l3n_lim; pp++) {
            int i = L3N_A[(p0 + pp) % na]; PEnt *e = &PE[i];
            if (op_cost[e->op] + pmin_cost + op_cost[r] > budget) continue;
            const u64 *pi = PV + (size_t)i * W;
            u64 Ai[1024];
            for (int w = 0; w < W; w++) Ai[w] = (xs ? pi[w] : ~pi[w] & CARE[w]) & NT[w];
            for (int qq = 0; qq < nb && chk < l3n_lim; qq++) {
                int j = LB[qq];
                if (same && j <= i && op_sym(r)) continue;
                if (j == i) continue;
                chk++;
                const u64 *pj = PV + (size_t)j * W; int ok = 1;
                for (int w = 0; w < W; w++) if (Ai[w] & (ys ? pj[w] : ~pj[w])) { ok = 0; break; }
                if (!ok) continue;
                PEnt *e2 = &PE[j];
                double nc = op_cost[e->op] + op_cost[e2->op] + op_cost[r];
                if (nc > budget) continue;
                if (arr_g(r, e->lg, e2->lg) > req_g || arr_a(r, e->la, e2->la) > req_a) continue;
                st_l3n_hit++;
                c.k = 3; c.g[0].op = e->op; c.g[0].a = e->a; c.g[0].b = e->b;
                c.g[1].op = e2->op; c.g[1].a = e2->a; c.g[1].b = e2->b;
                c.g[2].op = r; c.g[2].a = base; c.g[2].b = base + 1; c.root = base + 2; c.ncost = nc; add_cand(&c);
            }
        }
        st_l3n_chk += chk;
    }
}

/* enumerate candidates for signal s up to `lev` new gates */
static void find_cands(int lev) {
    int base = N + cur.ng;
    Cand c; c.ext = 0;
    ncand = 0; nseen = 0; memset(mv_seen, 0, sizeof mv_seen);
    /* level 0: an existing divisor */
    c.form = 0;
    for (int i = 0; i < ndiv; i++) {
        int d = DIV[i];
        if (LGc[d] > req_g || LAc[d] > req_a) continue;
        if (eqc(Vcur + (size_t)d * W, GT, CARE)) { c.k = 0; c.root = d; c.ncost = 0; add_cand(&c); }
    }
    if (lev < 1) return;
    build_pairs(lev >= 2);
    ph_mark(1);
    /* level 1 */
    c.form = 1;
    for (int q = 0; q < nl1; q++) {
        PEnt *e = &PE[L1[q] >> 1]; int op = (L1[q] & 1) ? 9 : e->op;
        c.k = 1; c.g[0].op = op; c.g[0].a = e->a; c.g[0].b = e->b;
        c.root = base; c.ncost = op_cost[op]; add_cand(&c);
    }
    if (lev < 2) return;
    int hits[8];
    /* level 2, XOR/XNOR root:  s = X ^ d3  (or ~) */
    c.form = 2;
    for (int r = 6; r <= 9; r += 3) {
        if (!op_ok[r]) continue;
        /* no pair entry fits the budget with this root (pmin_cost = cheapest op of the pair table; the
         * same left-to-right sum as below, and rounded addition is monotone): nothing to look up */
        if (pmin_cost + op_cost[r] > budget) continue;
        for (int i = 0; i < ndiv; i++) {
            int d3 = DIV[i];
            for (int w = 0; w < W; w++) TT[w] = ((r == 6 ? GT[w] : ~GT[w]) ^ Vcur[(size_t)d3 * W + w]) & CARE[w];
            u64 dtt = ldig(TT);
            for (int cx = 0; cx <= pxor; cx++) {        /* cx 1 (pair_xor): XNOR forms of XOR entries */
                int nh;
                if (!cx) nh = lookup(dtt, TT, hits, 4);
                else { for (int w = 0; w < W; w++) CC[w] = TT[w] ^ CARE[w]; nh = lookup(dtt ^ dcare, CC, hits, 4); }
                for (int h = 0; h < nh; h++) {
                    PEnt *e = &PE[hits[h]];
                    if (cx && e->op != 6) continue;
                    int op = cx ? 9 : e->op;
                    double nc = op_cost[op] + op_cost[r];
                    if (nc > budget) continue;
                    if (arr_g(r, e->lg, LGc[d3]) > req_g || arr_a(r, e->la, LAc[d3]) > req_a) continue;
                    c.k = 2; c.g[0].op = op; c.g[0].a = e->a; c.g[0].b = e->b;
                    c.g[1].op = r; c.g[1].a = base; c.g[1].b = d3; c.root = base + 1; c.ncost = nc; add_cand(&c);
                }
            }
        }
    }
    ph_mark(2);
    /* level 2, any library root (sampled):  s = op2(X, d3) or op2(d3, X) */
    c.form = 3;
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
        if (pmin_cost + nc0 > budget) continue;       /* no entry can fit (no random draw below) */
        u64 t0 = TT[0], c0 = CC[0];
        for (int i = 0; i < np; i++) {
            int op;
            if (!((PV0[i] ^ t0) & c0)) {               /* first word, from a dense array */
                op = PE[i].op;
                if (!eqc(PV + (size_t)i * W, TT, CC)) {
                    if (!pxor || op != 6) continue;
                    goto compl;
                }
            } else {
                if (!pxor || PE[i].op != 6 || ((PV0[i] ^ CARE[0] ^ t0) & c0)) continue;
            compl:                                      /* pair_xor: the XNOR form of an XOR entry */
                {
                    const u64 *pv = PV + (size_t)i * W; int ok = 1;
                    for (int w = 0; w < W; w++) if ((pv[w] ^ CARE[w] ^ TT[w]) & CC[w]) { ok = 0; break; }
                    if (!ok) continue;
                    op = 9;
                }
            }
            PEnt *e = &PE[i];
            if (op_cost[op] + nc0 > budget) continue;
            if (arr_g(op2, e->lg, LGc[d3]) > req_g || arr_a(op2, e->la, LAc[d3]) > req_a) continue;
            c.k = 2; c.g[0].op = op; c.g[0].a = e->a; c.g[0].b = e->b;
            c.g[1].op = op2; c.g[1].a = xfirst ? base : d3; c.g[1].b = xfirst ? d3 : base;
            c.root = base + 1; c.ncost = op_cost[op] + nc0; add_cand(&c);
        }
    }
    ph_mark(3);
    if (lev < 3) return;
    /* level 3, XOR/XNOR root of two pair values:  s = X1 ^ X2 */
    c.form = 4;
    for (int r = 6; r <= 9; r += 3) {
        if (!op_ok[r]) continue;
        int lim = np < 30000 ? np : 30000;
        /* budget below the cheapest three-gate form (U1 F2: e.g. every MFFC-1 target with unit costs):
         * every candidate would fail the cost test below, so skip the probing; the random partner
         * draws of a large table are still made, so the random stream is the same */
        if (pmin_cost + pmin_cost + op_cost[r] > budget) {
            if (np > 30000) for (int q = 0; q < lim; q++) (void)rndint(np);
            continue;
        }
        /* wanted partner value = GX ^ pv with GX = GT (XOR) or ~GT on the care set (XNOR) */
        for (int w = 0; w < W; w++) CC[w] = (r == 6 ? GT[w] : ~GT[w]) & CARE[w];
        u64 dgx = ldig(CC);
        if (pxor) { l3_pxor(r, lim, dgx, base); continue; }
        for (int q = 0; q < lim; q++) {
            int i = np <= 30000 ? q : rndint(np);
            PEnt *e = &PE[i];
            const u64 *pv = PV + (size_t)i * W;
            u64 d = dgx ^ PD[i];
            int nh = 0; unsigned hh = dslot(d);
            while (PHT[hh].gen == pgen && nh < 2) {
                int j = PHT[hh].idx; mv_probes++;
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
    if (l3n_lim > 0) l3n_cands(base);
}

/* ------------------------------------------------------------------ xspan
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
    ncand = 0; nseen = 0; memset(mv_seen, 0, sizeof mv_seen);
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
        Cand c; c.k = nx; c.ext = xg; c.root = XSEL[0]; c.ncost = nc; c.form = 5; add_cand(&c);
    }
}

/* fraig: merge gates whose complete function equals an earlier signal (never deeper).
 * fraig 1 looks only at the first signal with the same function and merges the later one into it;
 * when the earlier one is deeper nothing happens and the later one is not even remembered.  With fraig 2 the pair is merged into whichever of the two
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
                if (!lv) { levels(c, LG_tmp, LA_tmp); lv = 1; }      /* only when two signals are equal */
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
/* y is always the current circuit; its hashes, their sum and the sorted order are kept
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

/* evaluate candidate: build into o (rebuild, simulate, fraig, metrics); 0 if the rebuild fails */
static int ev_fraig_n;      /* kstat: fraig passes that merged something in the last eval_cand */
static int eval_cand(int s, const Cand *k, Metrics *m, Circ *o) {
    ev_fraig_n = 0;
    if (rebuild(&cur, s, k->root, cand_gates(k), k->k, 0, o, 1) < 0) { ph_mark(6); return 0; }
    ph_mark(6);
    sim(o, Vcand);
    if (!outputs_ok(o, Vcand)) {
        fprintf(stderr, "INTERNAL: candidate breaks the function (s=%d k=%d)\n", s, k->k); exit(3);
    }
    ph_mark(7);
    if (use_fraig) for (int it = 0; it < 3 && fraig(o, Vcand); it++) ev_fraig_n++;
    ph_mark(8);
    metrics(o, m);
    ph_mark(9);
    return 1;
}

/* Exact no-op test before the evaluation (U1 F3).  A candidate is a no-op when its rebuilt circuit is
 * the current one up to gate numbering.  Sufficient condition checked here: resolving the new gates
 * against the current circuit's own gates (exact (op, operands) match, as strash does; operands sorted
 * for symmetric ops, which is how rebuild stores them) maps the root to s itself.  The rebuild then
 * gives a circuit isomorphic to the current one (s is replaced by a gate of the same structure; the
 * current circuit is already reachable-only and strashed), and when no two signals of the current
 * circuit have the same complete function (`dupfree`, checked once per state), fraig finds nothing to
 * merge in it either, so the full evaluation would have counted exactly this no-op.  Anything else
 * (a new gate with equal operands, a current circuit with equal functions) goes the old way. */
static int NO_state = -1, NO_dupfree, NO_hts, NO_hts_cur; static int *NO_ht; static u64 *NO_hv; static long st_noop_pre;
static void noop_prepare(void) {
    if (NO_state == (int)NO_gen) return;
    NO_state = (int)NO_gen;
    int tot = N + cur.ng;
    if (!NO_ht) { NO_hts = 1 << 16; NO_ht = malloc(sizeof(int) * NO_hts); NO_hv = malloc(sizeof(u64) * NO_hts); }
    int hs = 64; while (hs < 2 * tot) hs <<= 1;
    if (hs > NO_hts) { NO_dupfree = 0; return; }
    /* duplicate complete functions (masked, as fraig compares them) */
    for (int i = 0; i < hs; i++) NO_ht[i] = -1;
    NO_dupfree = 1;
    for (int v = 0; v < tot && NO_dupfree; v++) {
        const u64 *pv = Vcur + (size_t)v * W;
        u64 h = 0x777; for (int w = 0; w < W; w++) { h ^= pv[w] & wmask(w); h *= 0x9E3779B97F4A7C15ULL; h ^= h >> 29; }
        unsigned q = (unsigned)(h >> 20) & (hs - 1);
        while (NO_ht[q] >= 0) {
            if (NO_hv[q] == h) {
                const u64 *pu = Vcur + (size_t)NO_ht[q] * W; int eq = 1;
                for (int w = 0; w < W; w++) if ((pu[w] ^ pv[w]) & wmask(w)) { eq = 0; break; }
                if (eq) { NO_dupfree = 0; break; }
            }
            q = (q + 1) & (hs - 1);
        }
        NO_ht[q] = v; NO_hv[q] = h;
    }
    if (!NO_dupfree) return;
    /* structural table of the current gates: (op, a, b) -> signal */
    NO_hts_cur = hs;
    for (int i = 0; i < hs; i++) NO_ht[i] = -1;
    for (int j = 0; j < cur.ng; j++) {
        const Gate *g = &cur.g[j];
        unsigned q = (unsigned)((gkey(g->op, g->a, g->b) * 0x9E3779B97F4A7C15ULL) >> 36) & (hs - 1);
        while (NO_ht[q] >= 0) q = (q + 1) & (hs - 1);
        NO_ht[q] = N + j;
    }
}
static int noop_pre(int s, const Cand *k) {
    if (k->k == 0 || k->k > XMAX + 2) return 0;
    noop_prepare();
    if (!NO_dupfree) return 0;
    static int res[XMAX + 4];
    const Gate *g = cand_gates(k); int base = N + cur.ng, hs = NO_hts_cur;
    for (int t = 0; t < k->k; t++) {
        int op = g[t].op, a = g[t].a, b = g[t].b;
        if (a >= base) a = res[a - base];
        if (b >= base) b = res[b - base];
        res[t] = -1;
        if (a < 0 || b < 0) continue;                 /* reads a genuinely new gate: new itself */
        if (op_unary(op)) b = a;
        else if (a == b) return 0;                    /* f(x,x): rebuild simplifies it; not handled here */
        else if (op_sym(op) && a > b) { int x = a; a = b; b = x; }
        unsigned q = (unsigned)((gkey(op, a, b) * 0x9E3779B97F4A7C15ULL) >> 36) & (hs - 1);
        while (NO_ht[q] >= 0) {
            const Gate *e = &cur.g[NO_ht[q] - N];
            if (e->op == op && e->a == a && e->b == b) { res[t] = NO_ht[q]; break; }
            q = (q + 1) & (hs - 1);
        }
    }
    int r = k->root >= base ? res[k->root - base] : k->root;
    return r == s;
}

/* ------------------------------------------------------------------ move trace */
static FILE *tmv; static Circ tmp_before; static Metrics mprev;
static const char *OPNAME[16] = {"C0", "NOR", "BANDN", "NOT", "ANDN", "NOTB", "XOR", "NAND",
                                 "AND", "XNOR", "BUFB", "BORN", "BUF", "ORN", "OR", "C1"};
static int popc_care(void) { int c = 0; for (int w = 0; w < W; w++) c += __builtin_popcountll(CARE[w] & wmask(w)); return c; }
static int patterns(void) { int c = 0; for (int w = 0; w < W; w++) c += __builtin_popcountll(wmask(w)); return c; }

/* ------------------------------------------------------------------ main loop */
/* The kernel's own clock (seconds budget, time-based Tperiod/stall, the t of best lines): `clock real` (default
 * since 2026-11-16; never allowed to run backwards), `clock cpu` (process CPU time: equal budgets for paired
 * runs on a busy host) or `clock mono` (CLOCK_MONOTONIC, the old clock, which runs 3-6 % fast on WSL, U5). */

static double now_s(void) {
    static double last = -1e300;
    struct timespec t;
    clock_gettime(cfg_clock == 1 ? CLOCK_PROCESS_CPUTIME_ID : cfg_clock == 2 ? CLOCK_MONOTONIC : CLOCK_REALTIME, &t);
    double x = t.tv_sec + t.tv_nsec * 1e-9;
    if (x < last) x = last;
    return last = x;
}
static double clk_s(clockid_t c) { struct timespec t; clock_gettime(c, &t); return t.tv_sec + t.tv_nsec * 1e-9; }
static long st_prop[NMOVES], st_acc[NMOVES], st_imp[NMOVES], st_cands[NMOVES];
static double st_time[NMOVES];
/* kstat counters: moves without candidates, accepted moves by kind (strict improvement of the current
 * state / neutral / uphill), uphill steps refused by Metropolis, moves with candidates but nothing
 * accepted, candidates rebuilt (evaluated) or failing the rebuild, repair_keep refusals, moves with no
 * divisor, iterations spent in repair (current state outside a cap) */
static long st_nocand[NMOVES], st_aimp[NMOVES], st_aneu[NMOVES], st_aup[NMOVES];
static long st_uprej, st_noacc, st_eval, st_rbfail, st_rkskip, st_ndiv0, st_repair_it, st_neu_avail, st_up_avail;
static void kstat_periodic(long it, double t, double T, long restarts, const Metrics *c, const Metrics *b) {
    long ai = 0, an = 0, au = 0, nc = 0;
    for (int i = 0; i < NMOVES; i++) { ai += st_aimp[i]; an += st_aneu[i]; au += st_aup[i]; nc += st_nocand[i]; }
    printf("kstat periodic it %ld t %.3f T %.6g cur_cost %.10g cur_G %d cur_A %d cur_GD %d cur_AD %d cur_feas %d "
           "best_cost %.10g best_G %d best_A %d best_GD %d best_AD %d best_feas %d acc_improve %ld acc_neutral %ld "
           "acc_uphill %ld uphill_refused %ld no_accept %ld nocand %ld evaluated %ld noop %ld restarts %ld repair_it %ld\n",
           it, t, T, c->cost, c->g, c->a, c->gd, c->ad, c->feas, b->cost, b->g, b->a, b->gd, b->ad, b->feas,
           ai, an, au, st_uprej, st_noacc, nc, st_eval, st_noop, restarts, st_repair_it);
    fflush(stdout);
}

/* kstat movex (per move kind): candidate forms seen by / kept in the reservoir, moves whose reservoir was
 * full (nseen > cand_cap), moves where a level-0/1 candidate was seen but not kept, the fate of every
 * evaluated candidate (rebuild fail, no-op, repair_keep, would leave feasibility, better / equal / uphill
 * within max_excess / uphill beyond it, all against the current state), Metropolis draws, the form of
 * accepted / strictly improving / new-best candidates, pair-table entries and hash probes per move. */
static long sx_seen[NMOVES][NFORM], sx_kept[NMOVES][NFORM], sx_full[NMOVES], sx_drop01[NMOVES];
static long sx_eval[NMOVES], sx_rbfail[NMOVES], sx_noop[NMOVES], sx_rkeep[NMOVES], sx_infeas[NMOVES];
static long sx_better[NMOVES], sx_equal[NMOVES], sx_upok[NMOVES], sx_upfar[NMOVES], sx_uptry[NMOVES];
static long sx_accf[NMOVES][NFORM], sx_impf[NMOVES][NFORM], sx_bestf[NMOVES][NFORM];
static long sx_np_sum[NMOVES], sx_np_max[NMOVES], sx_pr_sum[NMOVES], sx_pr_max[NMOVES];
/* kstat dcost: nominal cost change (new gates' cost - MFFC cost of s) against the actual change after
 * rebuild/strash/fraig (candidate cost - current cost), in units of the cheapest gate, clipped to -3..+3,
 * over evaluated (0), accepted (1) and strictly improving accepted (2) candidates; fraig passes that merged
 * (0 / 1 / 2+) per evaluated candidate; resub3 proposals whose budget is below 3 cheapest gates */
static long sx_dc[3][7][7], sx_fr[NMOVES][3], st_r3low; static double st_r3low_t, cheap_cost = 1;
static inline int dcb(double x) { long v = lround(x / cheap_cost); return v < -3 ? 0 : v > 3 ? 6 : (int)v + 3; }
/* kstat tgt: proposals / accepts / strict improvements / new bests by strata of the target signal s */
#define NSTRAT 6
static const char *STRNAME[NSTRAT] = {"s_andlike", "mffc_and", "mffc_cost", "care", "on_violating_path", "ndiv"};
static const char *STRB[NSTRAT][6] = {{"no", "yes"}, {"0", ">=1"}, {"<=1", "2", "3-4", ">=5"},
                                      {"0", "<=1/4", "<=1/2", "<=200/256", "<all", "all"}, {"no", "yes"}, {"<=45", "46-90", ">90"}};
static const int STRN[NSTRAT] = {2, 2, 4, 6, 2, 3};
static long sx_tgt[NSTRAT][6][4];
static long sx_viol_prop;        /* proposals made while the current state violates a cap (stratum 4 counts only those) */
static void put_vec(const char *name, const long *v) {
    printf(" %s ", name);
    for (int f = 0; f < nform_p; f++) printf(f ? ",%ld" : "%ld", v[f]);
}
/* kstat walk: distinct structures (structural hash, as in same_structure) and distinct (G, A, GD, AD)
 * of the accepted states, in saturating hash sets; the iterations of the first 64 restarts */
#define WSET_BITS 18
#define MSET_SIZE 4096
static u64 *WSET, MSET[MSET_SIZE]; static long walk_n, walk_m, walk_acc; static int walk_sat, mset_sat;
static long restarts_at[64]; static int nrestarts_at;
static void shash(const Circ *c, u64 *h);
static u64 shash_mix(u64 h);
static void walk_note(void) {
    if (!WSET) WSET = calloc((size_t)1 << WSET_BITS, sizeof(u64));
    walk_acc++;
    if (!walk_sat) {
        shash(&cur, SH_x);
        u64 h = 0x5bd1e995ULL;
        for (int j = 0; j < cur.ng; j++) h += SH_x[N + j];
        for (int k = 0; k < M; k++) h ^= shash_mix(SH_x[cur.out[k]] + 0x9E3779B97F4A7C15ULL * (u64)(k + 1));
        h = shash_mix(h) | 1;
        u64 mask = ((u64)1 << WSET_BITS) - 1, i = h & mask;
        while (WSET[i] && WSET[i] != h) i = (i + 1) & mask;
        if (!WSET[i]) { WSET[i] = h; if (++walk_n * 10 > (long)(mask + 1) * 7) walk_sat = 1; }
    }
    if (!mset_sat) {
        u64 k = ((u64)mcur.g << 40) | ((u64)mcur.a << 24) | ((u64)mcur.gd << 12) | (u64)mcur.ad | ((u64)1 << 62);
        unsigned i = (unsigned)(shash_mix(k) & (MSET_SIZE - 1));
        while (MSET[i] && MSET[i] != k) i = (i + 1) & (MSET_SIZE - 1);
        if (!MSET[i]) { MSET[i] = k; if (++walk_m * 10 > MSET_SIZE * 7) mset_sat = 1; }
    }
}

/* weighted target draw (tgt_w.*): weights of the current state's gates, rebuilt when the state changes */
static int weighted_tgt = 0; static double *TW_cum; static unsigned TW_gen = ~0u;
static int pick_target(void) {
    if (!TW_cum) TW_cum = malloc(sizeof(double) * (GCAP + 1));
    if (TW_gen != NO_gen) {
        TW_gen = NO_gen;
        double acc = 0;
        for (int j = 0; j < cur.ng; j++) {
            const Gate *g = &cur.g[j]; int v = N + j;
            int m1 = (g->a < N || REF[g->a] > 1) && (op_unary(g->op) || g->b < N || REF[g->b] > 1);
            double w = (m1 ? tw_mffc1 : 1) * (op_nl(g->op) ? tw_and : 1);
            if (!mcur.feas && ((cap_gd >= 0 && LGc[v] > RGc[v]) || (cap_ad >= 0 && LAc[v] > RAc[v]))) w *= tw_viol;
            acc += w; TW_cum[j] = acc;
        }
        if (acc <= 0) for (int j = 0; j < cur.ng; j++) TW_cum[j] = j + 1;   /* every weight 0: uniform */
    }
    double u = rnd01() * TW_cum[cur.ng - 1];
    int lo = 0, hi = cur.ng - 1;
    while (lo < hi) { int mid = (lo + hi) / 2; if (TW_cum[mid] > u) hi = mid; else lo = mid + 1; }
    return N + lo;
}

/* ------------------------------------------------------------------ chain: two-step compound move (idea 04)
 * The ordinary move replaces one signal s within the cost of s's fanout-free cone (+ uphill).  Mature circuits
 * are fixed points of that neighbourhood (U1): a gate g whose fanout is shared by s1 and s2 dies only if both
 * are replaced, and the new gates of one replacement can be the divisors that make another cheap.  The compound
 * move searches two replacements as ONE move:
 *   step 1: target s1 (uniform), candidates with up to chain.lev1 new gates within mffc(s1) + chain.up1;
 *           up to chain.k1 of them (random order, no-ops skipped, actual rise <= chain.maxup) give circuits C1;
 *   step 2: in each C1, targets s2 = the signals whose fanout count dropped against the current circuit C0
 *           ("freed": matched by complete function, so their care sets shrank and the fanout that is left may
 *           now own them in its cone), the gate fanouts of those, and chain.rand2 random gates; chain.k2 of
 *           them (random) are searched with the ordinary candidate generator (chain.lev2 new gates, budget
 *           mffc(s2) + uphill of that level) and every candidate is evaluated;
 *   result: every C1 and every two-step circuit C2 is compared with C0: the best strict improvement is taken;
 *           else (chain.accept 1) a uniformly drawn neutral one (equal keys, other structure than C0).
 * Every intermediate state is a correct circuit (each step is an ordinary exact-care-set replacement in its own
 * circuit), so the compound result is correct; the evaluation guards (outputs re-simulated) apply as usual.
 * Uphill compounds are never taken: the move is an escape, the walk stays with the ordinary moves. */
static Circ CH_save, CH_pool[CH_K1MAX], CH_best, CH_neu, CH_tmp; static int CH_ok;
static Metrics ch_mb, ch_mn; static int ch_bset; static long ch_nneu;
static u64 *CH_hk; static int *CH_hr, *CH_list; static unsigned char *CH_mark; static Cand *CH_c1;
static long ch_prop, ch_c1, ch_tg, ch_tgfreed, ch_ev, ch_acc_imp, ch_acc_neu, ch_nbest, ch_none, ch_c1imp, ch_c2imp; static double ch_time;
static int ch_bfrom2;
static long ch_eqm, ch_eqs, ch_h1[7], ch_h2[7]; static double ch_b2;   /* kstat chain_hist: step-1 rise, best step-2 change per C1 (cheapest-gate units vs C0) */
static inline u64 ch_vhash(const u64 *pv) {
    u64 h = 0x777; for (int w = 0; w < W; w++) { h ^= pv[w] & wmask(w); h *= 0x9E3779B97F4A7C15ULL; h ^= h >> 29; }
    return h | 1;
}
/* target s: care set, required levels, budget = mffc cost + slack, divisors (as the main loop does) */
static void ch_prep(int s, double slack) {
    tfo_care(s);
    req_g = RGc[s] > LGc[s] ? RGc[s] : LGc[s]; req_a = RAc[s] > LAc[s] ? RAc[s] : LAc[s];
    budget = mffc_cost(s) + slack;
    ndiv = 0;
    for (int v = 0; v < N + cur.ng; v++) if (!TFO[v]) DIV[ndiv++] = v;
    for (int i = ndiv - 1; i > 0; i--) { int j = rndint(i + 1); int x = DIV[i]; DIV[i] = DIV[j]; DIV[j] = x; }
    if (ndiv > dmax && dmax > 0) ndiv = dmax;
}
static void ch_consider(const Circ *x, const Metrics *m, const Metrics *m0, int from2) {
    if (!m->feas) return;
    int c = mcmp(m, m0);
    if (from2 && m->cost - m0->cost < ch_b2) ch_b2 = m->cost - m0->cost;
    if (c < 0) {
        if (!ch_bset || mcmp(m, &ch_mb) < 0) { circ_copy(&CH_best, x); ch_mb = *m; ch_bset = 1; ch_bfrom2 = from2; }
        return;
    }
    if (c || !ch_accept) return;
    ch_eqm++;
    SH_ycached = 0; int same = same_structure(x, &CH_save); SH_ycached = 0;   /* y = C0 here; cache dropped again */
    if (same) { ch_eqs++; return; }
    ch_nneu++;
    if (rndint((int)ch_nneu) == 0) { circ_copy(&CH_neu, x); ch_mn = *m; }
}
/* 0 nothing, 1 improvement in CH_best, 2 neutral in CH_neu.  The current state is unchanged on return. */
static int chain_move(void) {
    int S = N + GCAP + 16;
    if (!CH_ok) {
        circ_alloc(&CH_save); circ_alloc(&CH_best); circ_alloc(&CH_neu); circ_alloc(&CH_tmp);
        for (int i = 0; i < CH_K1MAX; i++) circ_alloc(&CH_pool[i]);
        CH_hk = calloc(1 << 16, sizeof(u64)); CH_hr = malloc(sizeof(int) * (1 << 16));
        CH_list = malloc(sizeof(int) * S); CH_mark = calloc(S, 1); CH_c1 = malloc(sizeof(Cand) * (cand_cap + 1));
        CH_ok = 1;
    }
    Metrics m0 = mcur; circ_copy(&CH_save, &cur);
    ch_bset = 0; ch_nneu = 0;
    /* complete function -> fanout count in C0 (first signal of each function) */
    int tot0 = N + cur.ng, hs = 64; while (hs < 2 * tot0) hs <<= 1;
    if (hs > (1 << 16)) return 0;
    for (int i = 0; i < hs; i++) CH_hk[i] = 0;
    for (int v = 0; v < tot0; v++) {
        u64 h = ch_vhash(Vcur + (size_t)v * W); unsigned q = (unsigned)(h >> 20) & (hs - 1);
        while (CH_hk[q] && CH_hk[q] != h) q = (q + 1) & (hs - 1);
        if (!CH_hk[q]) { CH_hk[q] = h; CH_hr[q] = REF[v]; }
    }
    /* step 1 */
    int s1 = N + rndint(cur.ng);
    ch_prep(s1, ch_up1s);
    if (!ndiv) return 0;
    find_cands(ch_lev1);
    int nc = ncand; memcpy(CH_c1, CAND, sizeof(Cand) * nc);
    int order[64 + 1], *ord = nc <= 64 ? order : malloc(sizeof(int) * nc);
    for (int i = 0; i < nc; i++) ord[i] = i;
    for (int i = nc - 1; i > 0; i--) { int j = rndint(i + 1); int x = ord[i]; ord[i] = ord[j]; ord[j] = x; }
    Metrics m; int n1 = 0;
    for (int q = 0; q < nc && n1 < ch_k1; q++) {
        Cand *k = &CH_c1[ord[q]];
        if (noop_pre(s1, k)) continue;
        if (!eval_cand(s1, k, &m, &CH_pool[n1])) continue;
        ch_ev++;
        if (!m.feas) continue;
        if (m.g == mcur.g && m.a == mcur.a && m.gd == mcur.gd && m.ad == mcur.ad && same_structure(&CH_pool[n1], &cur)) continue;
        ch_consider(&CH_pool[n1], &m, &m0, 0);
        ch_h1[dcb(m.cost - m0.cost)]++;
        if (ldelta(&m, &m0) > ch_maxups + 1e-9) continue;
        n1++;
    }
    if (ord != order) free(ord);
    ch_c1 += n1;
    double up2 = uphill_mv[ch_lev2 - 1];
    for (int a = 0; a < n1; a++) {
        circ_copy(&cur, &CH_pool[a]); state_refresh();
        int tot = N + cur.ng, nt = 0;
        memset(CH_mark, 0, tot);
        if (ch_freed) {
            /* freed signals: same complete function as a C0 signal with more fanout */
            for (int v = 0; v < tot; v++) {
                u64 h = ch_vhash(Vcur + (size_t)v * W); unsigned q = (unsigned)(h >> 20) & (hs - 1);
                while (CH_hk[q] && CH_hk[q] != h) q = (q + 1) & (hs - 1);
                if (CH_hk[q] && REF[v] < CH_hr[q]) CH_mark[v] = 1;
            }
            for (int j = 0; j < cur.ng; j++) {
                const Gate *g = &cur.g[j];
                if (CH_mark[g->a] == 1 || (!op_unary(g->op) && CH_mark[g->b] == 1)) { if (!CH_mark[N + j]) CH_mark[N + j] = 2; }
            }
            for (int v = N; v < tot; v++) if (CH_mark[v]) { CH_list[nt++] = v; ch_tgfreed++; }
        }
        for (int r = 0; r < ch_rand2; r++) { int v = N + rndint(cur.ng); if (!CH_mark[v]) { CH_mark[v] = 3; CH_list[nt++] = v; } }
        for (int i = nt - 1; i > 0; i--) { int j = rndint(i + 1); int x = CH_list[i]; CH_list[i] = CH_list[j]; CH_list[j] = x; }
        if (nt > ch_k2) nt = ch_k2;
        ch_b2 = 1e300;
        for (int t = 0; t < nt; t++) {
            int s2 = CH_list[t];
            ch_tg++;
            ch_prep(s2, up2);
            if (!ndiv) continue;
            find_cands(ch_lev2);
            for (int i = 0; i < ncand; i++) {
                if (noop_pre(s2, &CAND[i])) continue;
                if (!eval_cand(s2, &CAND[i], &m, &CH_tmp)) continue;
                ch_ev++;
                ch_consider(&CH_tmp, &m, &m0, 1);
            }
        }
        if (ch_b2 < 1e299) ch_h2[dcb(ch_b2)]++;
    }
    if (n1) { circ_copy(&cur, &CH_save); state_refresh(); }
    if (ch_bset) { if (ch_bfrom2) ch_c2imp++; else ch_c1imp++; return 1; }
    if (ch_nneu) return 2;
    ch_none++;
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) die("usage: bfx CONFIG");
    circ_alloc(&cur); circ_alloc(&best); circ_alloc(&tmp_c);
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
        cheap_cost = u > 0 ? u : 1;      /* kstat dcost unit */
        if (!scale_abs) { T0 *= cost_unit_v; uphill *= cost_unit_v; if (max_excess < 1e17) max_excess *= cost_unit_v; }
        for (int q = 0; q < 3; q++) uphill_mv[q] = uphill_mv[q] < 0 ? uphill : scale_abs ? uphill_mv[q] : uphill_mv[q] * cost_unit_v;
        ch_up1s = scale_abs ? ch_up1 : ch_up1 * cost_unit_v;           /* chain (idea 04): same units as uphill */
        ch_maxups = ch_maxup < 0 ? ch_up1s : scale_abs ? ch_maxup : ch_maxup * cost_unit_v;
        if (l3n_lim > 0) nform_p = NFORM;
        if (tw_mffc1 < 0 || tw_and < 0 || tw_viol < 0) die("tgt_w.* must be >= 0");
        weighted_tgt = tw_mffc1 != 1 || tw_and != 1 || tw_viol != 1;
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
    pxor = pair_xor && op_ok[6] && op_ok[9] && op_cost[6] == op_cost[9] && op_gdw[6] == op_gdw[9];
    if (pair_xor && !pxor) printf("note: pair_xor off (needs XOR and XNOR with equal cost and gate-depth weight)\n");
    pmin_cost = 1e300;
    for (int i = 0; i < nlib2; i++) if (op_cost[lib2[i]] < pmin_cost) pmin_cost = op_cost[lib2[i]];
    if (op_ok[3] && op_cost[3] < pmin_cost) pmin_cost = op_cost[3];
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
    double treal0 = clk_s(CLOCK_REALTIME), tcpu0 = clk_s(CLOCK_PROCESS_CPUTIME_ID);   /* kstat clock: the WSL monotonic clock drifts */
    for (int i = 0; i < NMOVES; i++) mvsum += mv_w[i];
    printf("start cost %.10g G %d A %d GD %d AD %d feas %d obj %.17g\n", mcur.cost, mcur.g, mcur.a, mcur.gd, mcur.ad, mcur.feas, mcur.obj);
    if (!mcur.feas) printf("note: start circuit violates a cap; the search first repairs it (penalised objective)\n");
    write_circuit(cfg_out, &best, &mbest, "start");
    walk_note(); walk_acc = 0;          /* kstat walk: the start is a visited state */
    long it = 0, restarts = 0, last_best_it = 0;
    /* kstat: why the loop ended, when the best was last improved (not reset by a restart), when the
     * current state first met every cap (0: the start did), the last restart */
    const char *stop_reason = "?"; long imp_it = 0, feas_it = mcur.feas ? 0 : -1, last_restart_it = -1;
    double imp_t = 0, feas_t = mcur.feas ? 0 : -1, next_stats_t = stats_every_s > 0 ? stats_every_s : 0;
    while (1) {
        double t = now_s() - t0;
        if (t >= cfg_seconds) { stop_reason = "time"; break; }
        if (max_iters >= 0 && it >= max_iters) { stop_reason = "iters"; break; }
        if (stop_stall_it > 0 && it - imp_it >= stop_stall_it) { stop_reason = "stall"; break; }
        it++;
        double ph = Tperiod_it > 0 ? fmod((double)it, Tperiod_it) / Tperiod_it : fmod(t, Tperiod) / Tperiod;
        double T = T0 > 0 ? T0 * (1.0 - ph) : 0;
        if ((stats_every_it > 0 && it % stats_every_it == 0) || (stats_every_s > 0 && t >= next_stats_t)) {
            kstat_periodic(it, t, T, restarts, &mcur, &mbest);
            if (stats_every_s > 0) while (next_stats_t <= t) next_stats_t += stats_every_s;
        }
        int stalled = stall_it > 0 ? (it - last_best_it > stall_it) : (t - last_best > stall);
        if (stalled && mcmp(&mcur, &mbest) > 0) {
            circ_copy(&cur, &best); state_refresh(); last_best = t; last_best_it = it; restarts++; last_restart_it = it;
            if (nrestarts_at < 64) restarts_at[nrestarts_at++] = it;
        }
        if (cur.ng == 0) { stop_reason = "empty"; break; }
        if (chain_p > 0 && mcur.feas && rnd01() < chain_p) {      /* idea 04 compound move (off by default: no draw) */
            double tm = now_s(); ph_hold = 1; ch_prop++;
            int k = chain_move();
            if (k) {
                circ_copy(&cur, k == 1 ? &CH_best : &CH_neu); state_refresh();
                if (k == 1) ch_acc_imp++; else ch_acc_neu++;
                int newbest = (mcur.feas || !mbest.feas) && (mcmp(&mcur, &mbest) < 0 || (mcur.feas && !mbest.feas));
                walk_note();
                if (newbest) {
                    imp_it = it; imp_t = t; ch_nbest++;
                    circ_copy(&best, &cur); mbest = mcur; last_best = t; last_best_it = it;
                    write_circuit(cfg_out, &best, &mbest, "best");
                    if (cfg_keep_bests[0]) {
                        char fn[1200], note[160];
                        snprintf(fn, sizeof fn, "%s/best-%ld.bfx", cfg_keep_bests, n_kept_bests);
                        snprintf(note, sizeof note, "best %ld t %.3f it %ld mv chain", n_kept_bests, t, it);
                        write_circuit(fn, &best, &mbest, note); n_kept_bests++;
                    }
                    printf("best t %.3f it %ld mv chain%d cost %.10g G %d A %d GD %d AD %d obj %.17g\n", t, it, ch_bfrom2 + 1,
                           mbest.cost, mbest.g, mbest.a, mbest.gd, mbest.ad, mbest.obj);
                    printf("kstat best it %ld treal %.3f cpu %.3f\n", it, clk_s(CLOCK_REALTIME) - treal0, clk_s(CLOCK_PROCESS_CPUTIME_ID) - tcpu0);
                    fflush(stdout);
                }
                if (trace) fprintf(trace, "%.3f %ld %s %.10g %d %d %d %d\n", t, it, "chain", mcur.cost, mcur.g, mcur.a, mcur.gd, mcur.ad);
            }
            ph_hold = 0; ch_time += now_s() - tm;
            continue;
        }
        if (!mcur.feas) st_repair_it++;
        double r = rnd01() * mvsum; int mv = 0;
        while (mv < NMOVES - 1 && r >= mv_w[mv]) { r -= mv_w[mv]; mv++; }
        while (mv > 0 && mv_w[mv] <= 0) mv--;          /* a move with weight 0 is never chosen (rounding) */
        double tm = now_s();
        cur_mv = mv; ph_last = tm; mv_probes = 0;
        st_prop[mv]++;
        int s = sweep ? N + (int)((it - 1) % cur.ng) : weighted_tgt ? pick_target() : N + rndint(cur.ng);
        tfo_care(s);
        /* required levels; in repair mode (current state violates a cap) never deeper than s */
        req_g = RGc[s] > LGc[s] ? RGc[s] : LGc[s]; req_a = RAc[s] > LAc[s] ? RAc[s] : LAc[s];
        double mc = mffc_cost(s);
        budget = mc + (mv < 3 ? uphill_mv[mv] : uphill);
        ndiv = 0;
        for (int v = 0; v < N + cur.ng; v++) if (!TFO[v]) DIV[ndiv++] = v;
        for (int i = ndiv - 1; i > 0; i--) { int j = rndint(i + 1); int x = DIV[i]; DIV[i] = DIV[j]; DIV[j] = x; }
        if (ndiv > dmax && dmax > 0) ndiv = dmax;
        if (ndiv == 0) { st_ndiv0++; continue; }
        ph_mark(0);
        double l3_before = st_ph[mv][4];
        if (mv == MV_XSPAN) xspan_cands(); else find_cands(mv + 1);
        ph_mark(mv == MV_XSPAN ? 5 : 4);
        if (mv == 2 && budget < 3 * cheap_cost - 1e-9) { st_r3low++; st_r3low_t += st_ph[mv][4] - l3_before; }
        st_cands[mv] += ncand;
        if (ncand == 0) st_nocand[mv]++;
        /* kstat: forms seen / kept, reservoir, pair table; strata of s (counters only) */
        {
            long k01 = 0;
            for (int f = 0; f < NFORM; f++) sx_seen[mv][f] += mv_seen[f];
            for (int i = 0; i < ncand; i++) { sx_kept[mv][CAND[i].form]++; if (CAND[i].form <= 1) k01++; }
            if (nseen > cand_cap) sx_full[mv]++;
            if (mv_seen[0] + mv_seen[1] > k01) sx_drop01[mv]++;
            if (mv != MV_XSPAN) { sx_np_sum[mv] += np; if (np > sx_np_max[mv]) sx_np_max[mv] = np; }
        }
        int sb[NSTRAT];
        {
            int pc = popc_care(), P = patterns();
            sb[0] = op_nl(cur.g[s - N].op); sb[1] = mffc_a > 0;
            sb[2] = mc <= 1 + 1e-9 ? 0 : mc <= 2 + 1e-9 ? 1 : mc <= 4 + 1e-9 ? 2 : 3;
            sb[3] = pc == 0 ? 0 : 4 * pc <= P ? 1 : 2 * pc <= P ? 2 : 256 * pc <= 200 * P ? 3 : pc < P ? 4 : 5;
            sb[4] = mcur.feas ? -1 : ((cap_gd >= 0 && LGc[s] > RGc[s]) || (cap_ad >= 0 && LAc[s] > RAc[s]));
            sb[5] = ndiv <= 45 ? 0 : ndiv <= 90 ? 1 : 2;
            if (!mcur.feas) sx_viol_prop++;
            for (int q = 0; q < NSTRAT; q++) if (sb[q] >= 0) sx_tgt[q][sb[q]][0]++;
        }
        /* evaluate all candidates; take the best improvement, else a random one under Metropolis */
        int bi = -1, bfeas = 0; Metrics m, bm;
        /* sized by cand_cap (fixed 1024-entry arrays would leave candidates past the first 1024
         * kept but never evaluated) */
        static int *order, *neu, *up; static double *upd;
        /* every evaluated candidate keeps its circuit and metrics (CPOOL[i], CMET[i]), so the accepted one is
         * not rebuilt a second time (same circuit: the evaluation is deterministic) */
        static Circ *CPOOL; static Metrics *CMET; static unsigned char *CPOK; static long *CREV;
        if (!order) {
            order = malloc(sizeof(int) * (cand_cap + 1)); neu = malloc(sizeof(int) * (cand_cap + 1));
            up = malloc(sizeof(int) * (cand_cap + 1)); upd = malloc(sizeof(double) * (cand_cap + 1));
            CPOOL = calloc(cand_cap + 1, sizeof(Circ)); CMET = malloc(sizeof(Metrics) * (cand_cap + 1));
            CPOK = calloc(cand_cap + 1, 1); CREV = calloc(cand_cap + 1, sizeof(long));
        }
        int no = ncand, nneu = 0, nup = 0;
        for (int i = 0; i < no; i++) order[i] = i;
        for (int i = no - 1; i > 0; i--) { int j = rndint(i + 1); int x = order[i]; order[i] = order[j]; order[j] = x; }
        for (int q = 0; q < no; q++) {
            int i = order[q];
            sx_eval[mv]++;
            if (skip_noop && noop_pre(s, &CAND[i])) {      /* exact no-op, known without the evaluation */
                st_eval++; st_noop_pre++;
                sx_dc[0][dcb(CAND[i].ncost - mc)][3]++; sx_fr[mv][0]++;
                st_noop++; sx_noop[mv]++; ph_mark(10); continue;
            }
            if (!CPOK[i]) { circ_alloc(&CPOOL[i]); CPOK[i] = 1; }
            long rev0 = st_fraig_rev;
            if (!eval_cand(s, &CAND[i], &m, &CPOOL[i])) { st_rbfail++; sx_rbfail[mv]++; continue; }
            CMET[i] = m; CREV[i] = st_fraig_rev - rev0;
            st_eval++;
            sx_dc[0][dcb(CAND[i].ncost - mc)][dcb(m.cost - mcur.cost)]++;
            sx_fr[mv][ev_fraig_n < 2 ? ev_fraig_n : 2]++;
            if (skip_noop && m.g == mcur.g && m.a == mcur.a && m.gd == mcur.gd && m.ad == mcur.ad
                && same_structure(&CPOOL[i], &cur)) { st_noop++; sx_noop[mv]++; ph_mark(10); continue; }
            if (repair_keep && !mcur.feas && (m.xa > mcur.xa || m.xad > mcur.xad || m.xgd > mcur.xgd)) { st_rkskip++; sx_rkeep[mv]++; ph_mark(10); continue; }
            double d = ldelta(&m, &mcur); int cc = mcmp(&m, &mcur);
            if (m.feas < mcur.feas) sx_infeas[mv]++;
            else if (cc < 0) sx_better[mv]++;
            else if (cc == 0) sx_equal[mv]++;
            else if (ldelta(&m, &mbest) <= max_excess) sx_upok[mv]++;
            else sx_upfar[mv]++;
            ph_mark(10);
            if ((m.feas || !mcur.feas) && (bi < 0 || mcmp(&m, &bm) < 0)) { bm = m; bi = i; bfeas = m.feas; }
            if (cc == 0 && m.feas >= mcur.feas) neu[nneu++] = i;
            else if (repair_uphill > 0 && !mcur.feas) {      /* bounded uphill in path excess while repairing */
                if (cc > 0 && m.viol == mcur.viol) {
                    double dv = m.vsum - mcur.vsum, du = dv > 1e-9 ? dv * cost_unit_v : ldelta(&m, &mcur);
                    if (dv <= repair_uphill + 1e-9 && du <= max_excess) { upd[nup] = du > 1e-12 ? du : 1e-12; up[nup++] = i; }
                }
            }
            else if (cc > 0 && ldelta(&m, &mbest) <= max_excess && m.feas >= mcur.feas) { upd[nup] = d > 1e-12 ? d : 1e-12; up[nup++] = i; }
        }
        int accept = -1, akind = 0;      /* akind (kstat only): 1 improvement, 2 neutral, 3 uphill */
        if (nneu) st_neu_avail++;
        if (nup) st_up_avail++;
        /* feasibility first: a feasible state is never left for an infeasible one */
        if (bi >= 0 && mcmp(&bm, &mcur) < 0 && (bfeas || !mcur.feas)) { accept = bi; akind = 1; }
        else if (use_neutral && nneu && (nup == 0 || T <= 0 || rnd01() < 0.75)) { accept = neu[rndint(nneu)]; akind = 2; }
        else if (nup && T > 0) { int q = rndint(nup); sx_uptry[mv]++; if (rnd01() < exp(-upd[q] / T)) { accept = up[q]; akind = 3; } else st_uprej++; }
        if (accept < 0 && no > 0) st_noacc++;
        if (akind == 1) st_aimp[mv]++; else if (akind == 2) st_aneu[mv]++; else if (akind == 3) st_aup[mv]++;
        if (accept >= 0) {
            int fm = CAND[accept].form;
            sx_accf[mv][fm]++; if (akind == 1) sx_impf[mv][fm]++;
            for (int q = 0; q < NSTRAT; q++) if (sb[q] >= 0) { sx_tgt[q][sb[q]][1]++; if (akind == 1) sx_tgt[q][sb[q]][2]++; }
            ph_hold = 1;
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
            m = CMET[accept];               /* evaluated above; its circuit is CPOOL[accept] */
            st_fraig_rev += CREV[accept];   /* fraig_reverse_merges keeps counting the accepted candidate twice, as before */
            {
                int nb = dcb(CAND[accept].ncost - mc), ab = dcb(m.cost - mcur.cost);
                sx_dc[1][nb][ab]++; if (akind == 1) sx_dc[2][nb][ab]++;
            }
            circ_copy(&cur, &CPOOL[accept]); state_refresh();
            if (feas_it < 0 && mcur.feas) { feas_it = it; feas_t = t; }
            int newbest = (mcur.feas || !mbest.feas) && (mcmp(&mcur, &mbest) < 0 || (mcur.feas && !mbest.feas));
            if (newbest) {
                imp_it = it; imp_t = t; sx_bestf[mv][fm]++;
                for (int q = 0; q < NSTRAT; q++) if (sb[q] >= 0) sx_tgt[q][sb[q]][3]++;
            }
            walk_note();
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
                if (cfg_keep_bests[0]) {
                    char fn[1200], note[160];
                    snprintf(fn, sizeof fn, "%s/best-%ld.bfx", cfg_keep_bests, n_kept_bests);
                    snprintf(note, sizeof note, "best %ld t %.3f it %ld mv %s", n_kept_bests, t, it, MVNAME[mv]);
                    write_circuit(fn, &best, &mbest, note); n_kept_bests++;
                }
                printf("best t %.3f it %ld mv %s cost %.10g G %d A %d GD %d AD %d obj %.17g\n", t, it, MVNAME[mv],
                       mbest.cost, mbest.g, mbest.a, mbest.gd, mbest.ad, mbest.obj);
                printf("kstat best it %ld treal %.3f cpu %.3f\n", it, clk_s(CLOCK_REALTIME) - treal0, clk_s(CLOCK_PROCESS_CPUTIME_ID) - tcpu0);
                fflush(stdout);
            }
            if (trace) fprintf(trace, "%.3f %ld %s %.10g %d %d %d %d\n", t, it, MVNAME[mv], mcur.cost, mcur.g, mcur.a, mcur.gd, mcur.ad);
            ph_hold = 0; ph_mark(11);
        }
        sx_pr_sum[mv] += mv_probes; if (mv_probes > sx_pr_max[mv]) sx_pr_max[mv] = mv_probes;
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
    if (l3n_lim > 0) printf("kstat l3n moves %ld listed %ld checks %ld hits %ld\n", st_l3n_moves, st_l3n_ea, st_l3n_chk, st_l3n_hit);
    if (chain_p > 0)
        printf("kstat chain prop %ld step1_circuits %ld targets2 %ld targets2_freed %ld evaluated %ld acc_improve %ld"
               " (from_step1 %ld from_step2 %ld) acc_neutral %ld none %ld new_best %ld time %.2f\n", ch_prop, ch_c1, ch_tg,
               ch_tgfreed, ch_ev, ch_acc_imp, ch_c1imp, ch_c2imp, ch_acc_neu, ch_none, ch_nbest, ch_time);
    if (chain_p > 0) {
        printf("kstat chain_hist equal_keys %ld equal_is_start %ld step1_rise", ch_eqm, ch_eqs);
        for (int i = 0; i < 7; i++) printf(" %+d:%ld", i - 3, ch_h1[i]);
        printf(" best_step2_change");
        for (int i = 0; i < 7; i++) printf(" %+d:%ld", i - 3, ch_h2[i]);
        putchar('\n');
    }
    /* kstat summary (after every older line, so parsers of those see the same text) */
    {
        double tf = now_s() - t0;
        printf("kstat clock mono_s %.3f real_s %.3f cpu_s %.3f\n", tf, clk_s(CLOCK_REALTIME) - treal0, clk_s(CLOCK_PROCESS_CPUTIME_ID) - tcpu0);
        printf("kstat stop %s it %ld t %.3f last_improve_it %ld last_improve_t %.3f restarts %ld last_restart_it %ld "
               "first_feasible_it %ld first_feasible_t %.3f repair_it %ld best_feas %d\n",
               stop_reason, it, tf, imp_it, imp_t, restarts, last_restart_it, feas_it, feas_t, st_repair_it, mbest.feas);
        long ai = 0, an = 0, au = 0, nc = 0;
        for (int i = 0; i < NMOVES; i++) { ai += st_aimp[i]; an += st_aneu[i]; au += st_aup[i]; nc += st_nocand[i]; }
        printf("kstat accept improve %ld neutral %ld uphill %ld uphill_refused %ld no_accept %ld neutral_available %ld "
               "uphill_available %ld\n", ai, an, au, st_uprej, st_noacc, st_neu_avail, st_up_avail);
        printf("kstat cands evaluated %ld rebuild_fail %ld noop %ld repair_keep_refused %ld nocand_moves %ld no_divisor_moves %ld"
               " noop_pre %ld\n", st_eval, st_rbfail, st_noop, st_rkskip, nc, st_ndiv0, st_noop_pre);
        for (int i = 0; i < NMOVES; i++)
            if (i < 3 || mv_w[i] > 0) printf("kstat move %s nocand %ld acc_improve %ld acc_neutral %ld acc_uphill %ld new_best %ld\n",
                                             MVNAME[i], st_nocand[i], st_aimp[i], st_aneu[i], st_aup[i], st_imp[i]);
        /* form vectors are L0,L1,L2x,L2n,L3,XS (FORMNAME) */
        printf("kstat forms");
        for (int f = 0; f < nform_p; f++) printf(f ? ",%s" : " %s", FORMNAME[f]);
        printf("\n");
        for (int i = 0; i < NMOVES; i++) {
            if (!(i < 3 || mv_w[i] > 0)) continue;
            printf("kstat movex %s", MVNAME[i]);
            put_vec("seen", sx_seen[i]); put_vec("kept", sx_kept[i]);
            printf(" full_res %ld drop01 %ld zero_cand %ld eval %ld rbfail %ld noop %ld rkeep %ld infeas %ld better %ld equal %ld"
                   " up_ok %ld up_far %ld acc_imp %ld acc_neu %ld acc_up %ld up_tried %ld",
                   sx_full[i], sx_drop01[i], st_nocand[i], sx_eval[i], sx_rbfail[i], sx_noop[i], sx_rkeep[i], sx_infeas[i],
                   sx_better[i], sx_equal[i], sx_upok[i], sx_upfar[i], st_aimp[i], st_aneu[i], st_aup[i], sx_uptry[i]);
            put_vec("accform", sx_accf[i]); put_vec("impform", sx_impf[i]); put_vec("bestform", sx_bestf[i]);
            printf(" np_sum %ld np_max %ld probe_sum %ld probe_max %ld fraig0 %ld fraig1 %ld fraig2p %ld\n", sx_np_sum[i], sx_np_max[i],
                   sx_pr_sum[i], sx_pr_max[i], sx_fr[i][0], sx_fr[i][1], sx_fr[i][2]);
        }
        {
            static const char *DCS[3] = {"evaluated", "accepted", "improving"};
            for (int q = 0; q < 3; q++) {
                printf("kstat dcost %s", DCS[q]);
                for (int a = 0; a < 7; a++) for (int b = 0; b < 7; b++)
                    if (sx_dc[q][a][b]) printf(" n%da%d %ld", a - 3, b - 3, sx_dc[q][a][b]);
                printf("\n");
            }
            if (cfg_keep_bests[0]) printf("kstat keep_bests files %ld dir %s\n", n_kept_bests, cfg_keep_bests);
            printf("kstat l1 direct %ld scan %ld", st_l1_direct, st_l1_scan); putchar(10);
            printf("kstat r3_lowbudget moves %ld l3_s %.4f unit %.10g\n", st_r3low, st_r3low_t, cheap_cost);
        }
        for (int q = 0; q < NSTRAT; q++)
            for (int b = 0; b < STRN[q]; b++)
                printf("kstat tgt %s %s prop %ld acc %ld imp %ld best %ld\n", STRNAME[q], STRB[q][b],
                       sx_tgt[q][b][0], sx_tgt[q][b][1], sx_tgt[q][b][2], sx_tgt[q][b][3]);
        printf("kstat walk distinct_struct %ld distinct_metrics %ld acc %ld struct_saturated %d metrics_saturated %d restarts_at ",
               walk_n, walk_m, walk_acc, walk_sat, mset_sat);
        if (!nrestarts_at) printf("-");
        for (int i = 0; i < nrestarts_at; i++) printf(i ? ",%ld" : "%ld", restarts_at[i]);
        printf("\n");
        if (kst_time)
            for (int i = 0; i < NMOVES; i++) {
                if (!(i < 3 || mv_w[i] > 0)) continue;
                printf("kstat time %s", MVNAME[i]);
                for (int p = 0; p < NPH; p++) printf(" %s %.4f", PHNAME[p], st_ph[i][p]);
                printf("\n");
            }
    }
    return 0;
}
