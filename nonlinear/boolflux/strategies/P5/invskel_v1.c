/* invskel.c: C port of invskel.py (P5), same search and cost model, k = 4 variables only.
 *
 * Input (stdin, all hex tables 16 bit):
 *   D NA MAXCOST SHARD_I SHARD_N
 *   NV  v_1 paid_1 ... v_NV paid_NV          (inputs; paid = 1: costs a gate, see boundary)
 *   NT  t_1 ... t_NT                         (targets; the first 4 span the target space)
 *   NB  b_1 ... b_NB                         (boundary forms: one gate each, any stage)
 *   NP  (lev L1 L2) x NP                     (prefix ANDs)
 * Output: one line per kept leaf: "cost kind lev:L1:L2 ..." and a final "STATS ..." line.
 * kind: 0 exact (one gate per form), 1 exact+1 (one helper), 2 lb+2 (proven bound only).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define ONES 0xffffu
typedef uint32_t u32;

static int D, NA, MAXC, SHI, SHN;
static int NV; static u32 V[8]; static int VPAID[8];
static int NT; static u32 TG[16];
static int NB; static u32 BND[8];
static long long nodes = 0, leaves = 0, kept = 0, nk[3] = {0, 0, 0}, topcnt = 0;

/* ---- echelon basis over GF(2)^16 ---- */
typedef struct { int n; u32 v[20]; } Basis;
static u32 reduce(const Basis *b, u32 x) {
    for (int i = 0; i < b->n; i++) { u32 y = x ^ b->v[i]; if (y < x) x = y; }
    return x;
}
static int badd(Basis *b, u32 x) {           /* returns 1 if added */
    x = reduce(b, x); if (!x) return 0;
    int i = b->n; b->v[b->n++] = x;
    while (i > 0 && b->v[i - 1] < b->v[i]) { u32 t = b->v[i]; b->v[i] = b->v[i - 1]; b->v[i - 1] = t; i--; }
    return 1;
}
static int inspan(const Basis *b, u32 x) { return reduce(b, x) == 0; }

/* enumerate all elements of span(b) into out (count 2^n) */
static int elements(const Basis *b, u32 *out) {
    int n = 1; out[0] = 0;
    for (int i = 0; i < b->n; i++) { for (int j = 0; j < n; j++) out[n + j] = out[j] ^ b->v[i]; n *= 2; }
    return n;
}

static Basis TB;  /* target span basis (main 4) */

static int r_of(const Basis *S) {
    Basis t = *S; int r = 0;
    for (int i = 0; i < 4; i++) r += badd(&t, TG[i]);
    return r;
}

/* ---- chosen ANDs ---- */
typedef struct { int lev; u32 L1, L2, P; } And;
static And ch[8];

/* ---- closure cost (level aware) ---- */
typedef struct { int n; u32 t[128]; int l[128]; } Avail;
static int av_find(const Avail *a, u32 t, int st) {
    for (int i = 0; i < a->n; i++) if (a->t[i] == t && a->l[i] <= st) return 1;
    return 0;
}
static void av_add(Avail *a, u32 t, int l) { a->t[a->n] = t; a->l[a->n] = l; a->n++; a->t[a->n] = t ^ ONES; a->l[a->n] = l; a->n++; }
static int isbound(u32 f) { for (int i = 0; i < NB; i++) if (f == BND[i] || f == (BND[i] ^ ONES)) return 1; return 0; }

/* bl: basis tables/levels, fl: forms/allowed levels. returns 1 if one gate per form suffices */
static int closure(const u32 *bt, const int *blv, int nb, const u32 *ft, const int *flv, int nf) {
    Avail a; a.n = 0;
    for (int i = 0; i < nb; i++) av_add(&a, bt[i], blv[i]);
    av_add(&a, 0, 0);
    int done[64] = {0}; int left = nf;
    for (int st = 0; st <= D; st++) {
        int ch_ = 1;
        while (ch_) {
            ch_ = 0;
            for (int i = 0; i < nf; i++) {
                if (done[i] || flv[i] < st) continue;
                u32 f = ft[i]; int ok = isbound(f);
                for (int j = 0; !ok && j < a.n; j++) if (a.l[j] <= st && av_find(&a, f ^ a.t[j], st)) ok = 1;
                if (ok) { done[i] = 1; left--; av_add(&a, f, st); ch_ = 1; }
            }
        }
        for (int i = 0; i < nf; i++) if (!done[i] && flv[i] == st) return 0;
    }
    return left == 0;
}

static void leaf(int k) {
    leaves++;
    u32 bt[16]; int bl[16]; int nb = 0;
    for (int i = 0; i < NV; i++) if (!VPAID[i]) { bt[nb] = V[i]; bl[nb] = 0; nb++; }
    for (int i = 0; i < k; i++) { bt[nb] = ch[i].P; bl[nb] = ch[i].lev; nb++; }
    u32 ft[64]; int fl[64]; int nf = 0;
#define INB(x) ({ int _r = 0; for (int _i = 0; _i < nb; _i++) if (bt[_i] == (x)) _r = 1; _r; })
#define ADDF(x, l) do { int _f = -1; for (int _i = 0; _i < nf; _i++) if (ft[_i] == (x)) _f = _i; \
        if (_f < 0) { ft[nf] = (x); fl[nf] = (l); nf++; } else if ((l) < fl[_f]) fl[_f] = (l); } while (0)
    for (int i = 0; i < k; i++) {
        if (!INB(ch[i].L1)) ADDF(ch[i].L1, ch[i].lev - 1);
        if (!INB(ch[i].L2)) ADDF(ch[i].L2, ch[i].lev - 1);
    }
    for (int i = 0; i < NT; i++) if (!INB(TG[i])) ADDF(TG[i], D);
    int bestc = 1 << 20, bestk = 2;
    int nmask = NB ? (1 << NB) : 1;
    for (int msk = 0; msk < nmask; msk++) {
        u32 b2[24]; int l2[24]; int n2 = nb, nu = 0;
        memcpy(b2, bt, sizeof(u32) * nb); memcpy(l2, bl, sizeof(int) * nb);
        for (int i = 0; i < NB; i++) if (msk >> i & 1) { b2[n2] = BND[i]; l2[n2] = 0; n2++; nu++; }
        u32 f2[64]; int fl2[64]; int m = 0;
        for (int i = 0; i < nf; i++) {
            int inb = 0; for (int j = 0; j < n2; j++) if (b2[j] == ft[i]) inb = 1;
            if (!inb) { f2[m] = ft[i]; fl2[m] = fl[i]; m++; }
        }
        int c, kind;
        if (closure(b2, l2, n2, f2, fl2, m)) { c = m; kind = 0; }
        else if (m + nu + NA + 1 > MAXC) { c = m + 2; kind = 2; }
        else {
            /* one helper: any XOR of two signals among basis, forms and complements */
            u32 sig[200]; int ns = 0;
            for (int i = 0; i < n2; i++) { sig[ns++] = b2[i]; sig[ns++] = b2[i] ^ ONES; }
            for (int i = 0; i < m; i++) { sig[ns++] = f2[i]; sig[ns++] = f2[i] ^ ONES; }
            c = m + 2; kind = 2;
            static u32 tried[65536 / 32];
            memset(tried, 0, sizeof tried);
            for (int i = 0; i < ns && kind == 2; i++) for (int j = i + 1; j < ns && kind == 2; j++) {
                u32 h = sig[i] ^ sig[j];
                if (h == 0 || h == ONES) continue;
                if (tried[h >> 5] >> (h & 31) & 1) continue;
                tried[h >> 5] |= 1u << (h & 31);
                int skip = 0;
                for (int q = 0; q < n2; q++) if (b2[q] == h) skip = 1;
                for (int q = 0; q < m; q++) if (f2[q] == h || f2[q] == (h ^ ONES)) skip = 1;
                if (skip) continue;
                f2[m] = h; fl2[m] = D;
                if (closure(b2, l2, n2, f2, fl2, m + 1)) { c = m + 1; kind = 1; }
            }
        }
        c += nu;
        if (c < bestc || (c == bestc && kind < bestk)) { bestc = c; bestk = kind; }
    }
    nk[bestk]++;
    if (bestc + NA > MAXC) return;
    kept++;
    printf("%d %d", bestc + NA, bestk);
    for (int i = 0; i < k; i++) printf(" %d:%04x:%04x", ch[i].lev, ch[i].L1, ch[i].L2);
    printf("\n"); fflush(stdout);
}

/* lower bound on linear cost for the chosen prefix */
static int lb_of(int k) {
    u32 B[16]; int nb = 0;
    for (int i = 0; i < NV; i++) if (!VPAID[i]) B[nb++] = V[i];
    for (int i = 0; i < k; i++) B[nb++] = ch[i].P;
    u32 F[32]; int nf = 0;
    for (int i = 0; i < k; i++) {
        u32 L[2] = {ch[i].L1, ch[i].L2};
        for (int q = 0; q < 2; q++) {
            int in = 0; for (int j = 0; j < nb; j++) if (B[j] == L[q]) in = 1;
            for (int j = 0; j < nf; j++) if (F[j] == L[q]) in = 1;
            if (!in) F[nf++] = L[q];
        }
    }
    int need = nf, tfree = 0;
    for (int i = 0; i < NT; i++) {
        int inB = 0, inF = 0;
        for (int j = 0; j < nb; j++) if (B[j] == TG[i]) inB = 1;
        for (int j = 0; j < nf; j++) if (F[j] == TG[i]) inF = 1;
        if (!inB && !inF) { need++; tfree++; }
    }
    int rem = NA - k;
    return need - (rem < tfree ? rem : tfree);
}

static int isfree(int k, u32 f) {      /* basis, operand forms already used, or target */
    for (int i = 0; i < NV; i++) if (!VPAID[i] && V[i] == f) return 1;
    for (int i = 0; i < k; i++) if (ch[i].P == f || ch[i].L1 == f || ch[i].L2 == f) return 1;
    for (int i = 0; i < NT; i++) if (TG[i] == f) return 1;
    return 0;
}

static u32 E1[1 << 12], E0[1 << 12];

static void dfs(int k, Basis *S, Basis *lsp, int hl, int lk_lev, u32 lk1, u32 lk2) {
    nodes++;
    if (k == 1 && SHN > 1) { topcnt++; if ((topcnt - 1) % SHN != SHI) return; }
    else if (k == 1) topcnt++;
    if (k == 1 && (topcnt % 20 == 0)) { fprintf(stderr, "top %lld nodes %lld leaves %lld kept %lld\n", topcnt, nodes, leaves, kept); }
    int r = r_of(S);
    if (r == 0 && k == NA) { leaf(k); return; }
    if (k == NA) return;
    if (r > NA - k) return;
    int lb = lb_of(k);
    int slack = MAXC - NA - lb;
    if (slack < 0) return;
    int curlev = k ? ch[k - 1].lev : 1;
    Basis TS = *S; for (int i = 0; i < 4; i++) badd(&TS, TG[i]);
    for (int lev = curlev; lev <= D; lev++) {
        Basis *src = &lsp[lev - 1];
        u32 *forms = (u32 *)malloc(sizeof(u32) * (1 << src->n));
        int ne = elements(src, E1), nfm = 0;
        for (int i = 0; i < ne; i++) if (E1[i] != 0 && E1[i] != ONES) forms[nfm++] = E1[i];
        /* sort ascending */
        int cmp(const void *a, const void *b) { u32 x = *(u32 *)a, y = *(u32 *)b; return x < y ? -1 : x > y; }
        qsort(forms, nfm, sizeof(u32), cmp);
        char *fr = (char *)malloc(nfm);
        for (int i = 0; i < nfm; i++) fr[i] = isfree(k, forms[i]);
        Basis *low = lev >= 2 ? &lsp[lev - 2] : NULL;
        for (int i = 0; i < nfm; i++) {
            u32 L1 = forms[i];
            int lowi = low ? inspan(low, L1) : 0;
            for (int j = i + 1; j < nfm; j++) {
                u32 L2 = forms[j];
                int nnew = (!fr[i]) + (!fr[j]);
                if (nnew > slack) continue;
                if (low && lowi && inspan(low, L2)) continue;
                if (lev == curlev && k > 0) {
                    if (L1 < lk1 || (L1 == lk1 && L2 <= lk2)) continue;
                }
                u32 P = L1 & L2;
                if (inspan(S, P)) continue;
                int lowers = inspan(&TS, P);
                int h = hl;
                if (!lowers) { if (h == 0) continue; h--; }
                ch[k].lev = lev; ch[k].L1 = L1; ch[k].L2 = L2; ch[k].P = P;
                if (NA + lb_of(k + 1) > MAXC) continue;
                Basis S2 = *S; badd(&S2, P);
                Basis l2[8]; memcpy(l2, lsp, sizeof(Basis) * (D + 1));
                for (int l = lev; l <= D; l++) badd(&l2[l], P);
                dfs(k + 1, &S2, l2, h, lev, L1, L2);
            }
        }
        free(forms); free(fr);
    }
}

int main(void) {
    if (scanf("%d %d %d %d %d", &D, &NA, &MAXC, &SHI, &SHN) != 5) return 1;
    scanf("%d", &NV); for (int i = 0; i < NV; i++) scanf("%x %d", &V[i], &VPAID[i]);
    scanf("%d", &NT); for (int i = 0; i < NT; i++) scanf("%x", &TG[i]);
    scanf("%d", &NB); for (int i = 0; i < NB; i++) scanf("%x", &BND[i]);
    int NP; scanf("%d", &NP);
    Basis S; S.n = 0; for (int i = 0; i < NV; i++) badd(&S, V[i]); badd(&S, ONES);
    Basis lsp[8]; for (int l = 0; l <= D; l++) lsp[l] = S;
    TB.n = 0; for (int i = 0; i < 4; i++) badd(&TB, TG[i]);
    int r0 = r_of(&S); int hl = NA - r0;
    int k = 0, ll = 0; u32 l1 = 0, l2 = 0;
    for (int i = 0; i < NP; i++) {
        int lev; u32 a, b; scanf("%d %x %x", &lev, &a, &b);
        if (a > b) { u32 t = a; a = b; b = t; }
        u32 P = a & b;
        Basis TS = S; for (int q = 0; q < 4; q++) badd(&TS, TG[q]);
        if (!(inspan(&TS, P) && !inspan(&S, P))) hl--;
        ch[k].lev = lev; ch[k].L1 = a; ch[k].L2 = b; ch[k].P = P; k++;
        badd(&S, P); for (int l = lev; l <= D; l++) badd(&lsp[l], P);
        ll = lev; l1 = a; l2 = b;
    }
    fprintf(stderr, "r0 %d helpers %d prefix %d\n", r0, hl, k);
    dfs(k, &S, lsp, hl, ll, l1, l2);
    printf("STATS nodes %lld leaves %lld kept %lld exact %lld exact+1 %lld lb+2 %lld top %lld\n",
           nodes, leaves, kept, nk[0], nk[1], nk[2], topcnt);
    return 0;
}
