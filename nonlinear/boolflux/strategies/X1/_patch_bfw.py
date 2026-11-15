s = open("bfw.c").read()
mach = r"""
/* ---- truth tables (256 bits) and canonical hashes ------------------------------------------- */
typedef struct { u64 w[4]; } T256;
static T256 TIN[NIN + 1];
static void init_tables(void) {
    for (int w = 0; w < 4; w++) TIN[0].w[w] = ~0ULL;
    for (int i = 0; i < NIN; i++) {          /* input i = bit (7 - i) of x (core.input_tables) */
        int bit = NIN - 1 - i;
        for (int x = 0; x < 256; x++) if ((x >> bit) & 1) TIN[i + 1].w[x >> 6] |= 1ULL << (x & 63);
    }
}
static void eval_tables(const Prog *p, T256 *T, u64 *done, int k);
static void form_table(const Prog *p, T256 *T, u64 *done, u64 f, T256 *o) {
    memset(o, 0, sizeof *o);
    while (f) {
        int b = __builtin_ctzll(f); f &= f - 1;
        if (b > NIN && !((*done >> b) & 1)) eval_tables(p, T, done, b);
        for (int w = 0; w < 4; w++) o->w[w] ^= T[b].w[w];
    }
}
static void eval_tables(const Prog *p, T256 *T, u64 *done, int k) {
    T256 a, b;
    form_table(p, T, done, p->L[k], &a); form_table(p, T, done, p->R[k], &b);
    for (int w = 0; w < 4; w++) T[k].w[w] = a.w[w] & b.w[w];
    *done |= 1ULL << k;
}
static inline int tbit(const T256 *t, int x) { return (t->w[x >> 6] >> (x & 63)) & 1; }
static inline u64 mix(u64 h) { h ^= h >> 33; h *= 0xff51afd7ed558ccdULL; h ^= h >> 33; h *= 0xc4ceb9fe1a85ec53ULL; h ^= h >> 33; return h; }
/* hashes of the product set modulo affine functions (fam) and of its span modulo affine (span) */
static void hashes(const Prog *p, u64 *fam, u64 *span) {
    static T256 T[NB]; u64 done = 0; T256 g[NB]; int n = 0;
    for (int i = 0; i <= NIN; i++) T[i] = TIN[i];
    u64 m = p->alive;
    while (m) { int k = __builtin_ctzll(m); m &= m - 1; if (!((done >> k) & 1)) eval_tables(p, T, &done, k); }
    m = p->alive; *fam = 0;
    while (m) {
        int k = __builtin_ctzll(m); m &= m - 1;
        T256 t = T[k]; int c0 = tbit(&t, 0);
        if (c0) for (int w = 0; w < 4; w++) t.w[w] ^= TIN[0].w[w];
        for (int i = 0; i < NIN; i++) { int x = 1 << (NIN - 1 - i); if (tbit(&T[k], x) ^ c0) for (int w = 0; w < 4; w++) t.w[w] ^= TIN[i + 1].w[w]; }
        u64 h = mix(t.w[0] + 1) ^ mix(t.w[1] + 2) ^ mix(t.w[2] + 3) ^ mix(t.w[3] + 4);
        *fam += mix(h);
        g[n++] = t;
    }
    /* reduced row echelon form */
    int piv[NB], r = 0;
    for (int i = 0; i < n; i++) {
        T256 t = g[i];
        for (int j = 0; j < r; j++) if (tbit(&t, piv[j])) for (int w = 0; w < 4; w++) t.w[w] ^= g[j].w[w];
        int pb = -1;
        for (int w = 3; w >= 0 && pb < 0; w--) if (t.w[w]) pb = w * 64 + 63 - __builtin_clzll(t.w[w]);
        if (pb < 0) continue;
        for (int j = 0; j < r; j++) if (tbit(&g[j], pb)) for (int w = 0; w < 4; w++) g[j].w[w] ^= t.w[w];
        g[r] = t; piv[r] = pb; r++;
    }
    u64 h = 0;
    for (int j = 0; j < r; j++) h += mix(mix(g[j].w[0] + 1) ^ mix(g[j].w[1] + 2) ^ mix(g[j].w[2] + 3) ^ mix(g[j].w[3] + 4));
    *span = h ^ (u64)r;
}
#define HS (1 << 20)
static u64 hset_span[HS], hset_fam[HS]; static long n_span, n_fam;
static int hadd(u64 *hs, u64 h) {
    if (!h) h = 1;
    u64 i = h & (HS - 1);
    for (int probe = 0; probe < HS; probe++) { if (hs[i] == h) return 0; if (!hs[i]) { hs[i] = h; return 1; } i = (i + 1) & (HS - 1); }
    return 0;
}
static int and_depth(const Prog *p) {
    int lv[NB]; u64 done = (1ULL << (NIN + 1)) - 1; int mx = 0, left = popc(p->alive), guard = 0;
    memset(lv, 0, sizeof lv);
    while (left && guard++ < NB) {
        u64 m = p->alive & ~done;
        while (m) {
            int k = __builtin_ctzll(m); m &= m - 1;
            u64 f = (p->L[k] | p->R[k]) & p->alive;
            if (f & ~done) continue;
            int l = 0; while (f) { int b = __builtin_ctzll(f); f &= f - 1; if (lv[b] > l) l = lv[b]; }
            lv[k] = l + 1; if (l + 1 > mx) mx = l + 1; done |= 1ULL << k; left--;
        }
    }
    return left ? 999 : mx;
}

static void write_prog"""
s = s.replace("\nstatic void write_prog", mach, 1)
old = s[s.index("    double seconds = atof(argv[3]);"):s.index("    (void)t0;")]
new = r"""    double seconds = atof(argv[3]); u64 seed = strtoull(argv[4], 0, 10); int plus = atoi(argv[5]);
    double psplit = atof(argv[6]); long horizon = atol(argv[7]); double predec = atof(argv[8]);
    int adcap = argc > 9 ? atoi(argv[9]) : 0; int dump = argc > 10 ? atoi(argv[10]) : 0;
    rs[0] = seed * 0x9E3779B97F4A7C15ULL + 1; rs[1] = seed ^ 0xD1B54A32D192ED03ULL; rs[2] = 0x8CB92BA72F3D8DD7ULL + seed; rs[3] = 0x2545F4914F6CDD1DULL;
    for (int i = 0; i < 20; i++) rnd();
    for (int i = 0; i < 2 * NB + 16; i++) RS[i] = rnd() | 1;
    init_tables();
    remove_dead(&p);
    #define POOL 256
    static Prog pool[POOL]; int npool = 1; pool[0] = p;
    int bestA = nA(&p); long since = 0, st_rej = 0, ndump = 0;
    u64 hf, hsp; hashes(&p, &hf, &hsp); n_fam += hadd(hset_fam, hf); n_span += hadd(hset_span, hsp);
    time_t t0 = time(0); struct timespec ts0, ts; clock_gettime(CLOCK_MONOTONIC, &ts0);
    printf("start A %d AD %d adcap %d\n", bestA, and_depth(&p), adcap); fflush(stdout);
    for (;;) {
        clock_gettime(CLOCK_MONOTONIC, &ts);
        double el = (ts.tv_sec - ts0.tv_sec) + 1e-9 * (ts.tv_nsec - ts0.tv_nsec);
        if (el > seconds) break;
        for (int it = 0; it < 2000; it++) {
            Prog saved; if (adcap) saved = p;
            int red = step(&p, bestA, plus, psplit, predec); since++;
            if (adcap && and_depth(&p) > adcap) { p = saved; st_rej++; continue; }
            if (red) {
                int a = nA(&p);
                if (a < bestA) {
                    bestA = a; npool = 1; pool[0] = p; since = 0;
                    memset(hset_fam, 0, sizeof hset_fam); memset(hset_span, 0, sizeof hset_span); n_fam = n_span = 0; ndump = 0;
                    hashes(&p, &hf, &hsp); n_fam += hadd(hset_fam, hf); n_span += hadd(hset_span, hsp);
                    char path[1024]; snprintf(path, sizeof path, "%s.%d.prog", argv[2], a); write_prog(&p, path);
                    printf("best A %d AD %d t %.1f steps %ld flips %ld splits %ld merges %ld redec %ld\n", a, and_depth(&p), el, st_step, st_flip, st_split, st_merge, st_redec); fflush(stdout);
                } else if (a == bestA) {
                    hashes(&p, &hf, &hsp);
                    int nf = hadd(hset_fam, hf), ns = hadd(hset_span, hsp);
                    n_fam += nf; n_span += ns;
                    if (ns) {
                        if (npool < POOL) pool[npool++] = p; else pool[rint_(POOL)] = p;
                        if (ndump < dump) { char path[1024]; snprintf(path, sizeof path, "%s.span%ld.A%d.prog", argv[2], ndump++, a); write_prog(&p, path); }
                    }
                }
            }
            if (since > horizon) { p = pool[rint_(npool)]; since = 0; st_restart++; }
        }
    }
    printf("spans at best A: %ld  product sets: %ld  rejected(adcap) %ld\n", n_span, n_fam, st_rej);
"""
s = s.replace(old, new)
open("bfw.c", "w").write(s)
d = open("x1walkc.py").read()
d = d.replace('def run(c, out, seconds, seed, plus=1, psplit=0.02, horizon=20000, redec=0.2, tag="w"):',
              'def run(c, out, seconds, seed, plus=1, psplit=0.02, horizon=20000, redec=0.2, tag="w", adcap=0, dump=0):')
d = d.replace("str(horizon), str(redec)],", "str(horizon), str(redec), str(adcap), str(dump)],")
d = d.replace('        if f.name.endswith(".in.prog"): continue', '        if f.name.endswith(".in.prog") or ".span" in f.name: continue')
d = d.replace('opt("--redec", 0.2), tag)', 'opt("--redec", 0.2), tag, opt("--adcap", 0), opt("--dump", 0))')
open("x1walkc.py", "w").write(d)
print("patched")
