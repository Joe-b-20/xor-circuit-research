/* r1enum: exhaustive search for products a*b (a, b in V) whose class mod W lies in T \ {0}.
 *
 * V has basis e_0..e_{nv-1} (nv <= 63), W = span(1, V).  For a linear functional h annihilating W,
 * c_h(a*b) = sum_j b_j c_h(a*e_j) = <R_h(a), b>, R_h(a) = sum_i a_i G_h[i], G_h[i]_j = c_h(e_i e_j).
 * H_T = checks annihilating W + T (nh rows), C = r checks completing them to ann(W) (nc rows).
 * a*b in W + T  iff  <R_h(a), b> = 0 for h in H_T;  a*b notin W  iff  some <R_c(a), b> != 0.
 * So a admits a hit iff rank(H_T rows at a) < rank(all rows at a).  a itself is always in the
 * kernel (a*a = a in W), so the rank is <= nv - 1.
 *
 * Enumeration: a over the hyperplane a_{nv-1} = 0 (every 2-dim span{a,b} meets it, and a*b mod W
 * depends only on span{a,b}) by Gray code; a filter of nf random combinations of the H_T rows is
 * updated incrementally; only if the filter rank is < nv - 1 are all rows evaluated exactly.
 * No false negatives: rank(filter) >= nv-1 implies rank(H_T) = nv-1 = max, so no hit.
 *
 * Input (stdin): "nv nh nc nf" then nf, nh, nc rows of nv hex words.  Args: lo hi (Gray index
 * range, hex; default whole range) maxhits.  Output: "H a rankT rankAll" lines, then a summary.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

typedef uint64_t u64;
static int nv, nh, nc, nf;
static u64 *Gf, *Gh, *Gc;   /* [row*nv + i] */

static inline int rank_abort(const u64 *rows, int n, int stop) {
    u64 piv[64]; u64 used = 0; int rk = 0;
    for (int k = 0; k < n; k++) {
        u64 v = rows[k];
        while (v) {
            int h = 63 - __builtin_clzll(v);
            if (!((used >> h) & 1)) { piv[h] = v; used |= 1ULL << h; rk++; break; }
            v ^= piv[h];
        }
        if (rk >= stop) return rk;
    }
    return rk;
}

/* branch-light row echelon on a copy; returns 1 iff rank >= nv - 1 (at most one free column) */
static inline int full_minus1(const u64 *rows, int n) {
    u64 M[64]; for (int k = 0; k < n; k++) M[k] = rows[k];
    int rk = 0, freec = 0;
    for (int col = nv - 1; col >= 0; col--) {
        int p = -1;
        for (int k = rk; k < n; k++) if ((M[k] >> col) & 1) { p = k; break; }
        if (p < 0) { if (++freec >= 2) return 0; continue; }
        u64 pr = M[p]; M[p] = M[rk]; M[rk] = pr;
        for (int k = rk + 1; k < n; k++) M[k] ^= pr & (0 - ((M[k] >> col) & 1));
        rk++;
    }
    return 1;
}

static void eval_rows(const u64 *G, int n, u64 a, u64 *out) {
    for (int k = 0; k < n; k++) {
        u64 r = 0; u64 t = a;
        while (t) { int i = __builtin_ctzll(t); r ^= G[(size_t)k * nv + i]; t &= t - 1; }
        out[k] = r;
    }
}

int main(int argc, char **argv) {
    if (scanf("%d %d %d %d", &nv, &nh, &nc, &nf) != 4) return 2;
    Gf = malloc(sizeof(u64) * nf * nv); Gh = malloc(sizeof(u64) * nh * nv); Gc = malloc(sizeof(u64) * nc * nv);
    for (int k = 0; k < nf * nv; k++) if (scanf("%lx", &Gf[k]) != 1) return 2;
    for (int k = 0; k < nh * nv; k++) if (scanf("%lx", &Gh[k]) != 1) return 2;
    for (int k = 0; k < nc * nv; k++) if (scanf("%lx", &Gc[k]) != 1) return 2;
    u64 total = 1ULL << (nv - 1);
    u64 lo = argc > 1 ? strtoull(argv[1], 0, 16) : 1, hi = argc > 2 ? strtoull(argv[2], 0, 16) : total;
    long maxhits = argc > 3 ? atol(argv[3]) : 1000000;
    if (lo < 1) lo = 1;
    if (hi > total) hi = total;
    /* filter rows, transposed for incremental update: Gfi[i*nf + s] */
    u64 *Gfi = malloc(sizeof(u64) * nf * nv);
    for (int s = 0; s < nf; s++) for (int i = 0; i < nv; i++) Gfi[(size_t)i * nf + s] = Gf[(size_t)s * nv + i];
    u64 *R = malloc(sizeof(u64) * nf);
    u64 *Rall = malloc(sizeof(u64) * (nh + nc));
    u64 a = lo ^ (lo >> 1);
    eval_rows(Gf, nf, a, R);
    long hits = 0, fulls = 0;
    for (u64 g = lo; g < hi; g++) {
        if (g != lo) {
            int i = __builtin_ctzll(g);
            a ^= 1ULL << i;
            const u64 *gi = Gfi + (size_t)i * nf;
            for (int s = 0; s < nf; s++) R[s] ^= gi[s];
        }
        if (full_minus1(R, nf)) continue;
        fulls++;
        eval_rows(Gh, nh, a, Rall);
        int rT = rank_abort(Rall, nh, nv - 1);
        if (rT >= nv - 1) continue;
        eval_rows(Gc, nc, a, Rall + nh);
        int rA = rank_abort(Rall, nh + nc, 64);
        if (rT < rA) {
            hits++;
            if (hits <= maxhits) printf("H %lx %d %d\n", a, rT, rA);
        }
    }
    printf("DONE lo %lx hi %lx fulls %ld hits %ld\n", lo, hi, fulls, hits);
    return 0;
}
