/* P4: exhaustive helper-set enumeration for 8-input top layers (C version of topenum.py).

   stdin:  NF  then NF lines "mask deadline"  then H  then NV and NV masks (vectors of interest; may be 0)
   stdout: one line per feasible helper set: "h1 h2 ... | maxlevel | nV"  where nV = number of
           helpers+forms+inputs lying in the span given by the NV masks (0 if NV = 0) and the rank of
           those vectors ("rank r").
   A set S = forms + helpers is feasible iff every element is reachable by the closure
   level(t) = 1 + min_{a^b=t, a,b in S u inputs} max(level a, level b) and every form meets its deadline.
   Exact for top layers whose gate values are exactly S (every gate a form or a helper).
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int NF, H, NV;
static int fm[64], fd[64], vv[64];
static int inS[256], isForm[256];

static int closure(int *S, int ns, int *lvl) {
    for (int v = 0; v < 256; v++) lvl[v] = 99;
    for (int i = 0; i < 8; i++) lvl[1 << i] = 0;
    int changed = 1;
    while (changed) {
        changed = 0;
        for (int i = 0; i < ns; i++) {
            int t = S[i];
            int best = lvl[t];
            /* a in S u inputs, b = a ^ t in S u inputs */
            for (int j = 0; j < ns + 8; j++) {
                int a = j < ns ? S[j] : (1 << (j - ns));
                int b = a ^ t;
                if (a > b) continue;
                if (lvl[a] >= 99 || lvl[b] >= 99) continue;
                if (!(inS[b] || (b && !(b & (b - 1))))) continue;
                int l = 1 + (lvl[a] > lvl[b] ? lvl[a] : lvl[b]);
                if (l < best) best = l;
            }
            if (best < lvl[t]) { lvl[t] = best; changed = 1; }
        }
    }
    for (int i = 0; i < ns; i++) if (lvl[S[i]] >= 99) return 0;
    for (int i = 0; i < NF; i++) if (lvl[fm[i]] > fd[i]) return 0;
    return 1;
}

static int rank_of(int *v, int n) {
    int b[8] = {0};
    int r = 0;
    for (int i = 0; i < n; i++) {
        int x = v[i];
        for (int k = 7; k >= 0; k--) {
            if (!((x >> k) & 1)) continue;
            if (!b[k]) { b[k] = x; r++; break; }
            x ^= b[k];
        }
    }
    return r;
}

int main(void) {
    if (scanf("%d", &NF) != 1) return 1;
    for (int i = 0; i < NF; i++) scanf("%d %d", &fm[i], &fd[i]);
    scanf("%d", &H);
    scanf("%d", &NV);
    for (int i = 0; i < NV; i++) scanf("%d", &vv[i]);
    int span[256] = {0};
    span[0] = 1;
    for (int i = 0; i < NV; i++) {
        int add[256]; int na = 0;
        for (int v = 0; v < 256; v++) if (span[v]) add[na++] = v ^ vv[i];
        for (int k = 0; k < na; k++) span[add[k]] = 1;
    }
    for (int i = 0; i < NF; i++) { inS[fm[i]] = 1; isForm[fm[i]] = 1; }
    int cand[256], nc = 0;
    for (int v = 1; v < 256; v++) if ((v & (v - 1)) && !isForm[v]) cand[nc++] = v;
    int idx[8];
    int S[64], lvl[256];
    long count = 0;
    for (int i = 0; i < H; i++) idx[i] = i;
    if (H == 0) {
        for (int i = 0; i < NF; i++) S[i] = fm[i];
        if (closure(S, NF, lvl)) printf("| feasible\n");
        return 0;
    }
    while (1) {
        int ns = 0;
        for (int i = 0; i < NF; i++) S[ns++] = fm[i];
        for (int i = 0; i < H; i++) { S[ns++] = cand[idx[i]]; inS[cand[idx[i]]] = 1; }
        if (closure(S, ns, lvl)) {
            int mx = 0;
            for (int i = 0; i < ns; i++) if (lvl[S[i]] > mx) mx = lvl[S[i]];
            int inV[80], niv = 0;
            if (NV) {
                for (int i = 0; i < ns; i++) if (span[S[i]]) inV[niv++] = S[i];
                for (int i = 0; i < 8; i++) if (span[1 << i]) inV[niv++] = 1 << i;
            }
            for (int i = 0; i < H; i++) printf("%d ", cand[idx[i]]);
            printf("| %d | rank %d\n", mx, NV ? rank_of(inV, niv) : 0);
            count++;
        }
        for (int i = 0; i < H; i++) inS[cand[idx[i]]] = 0;
        /* next combination */
        int k = H - 1;
        while (k >= 0 && idx[k] == nc - H + k) k--;
        if (k < 0) break;
        idx[k]++;
        for (int j = k + 1; j < H; j++) idx[j] = idx[j - 1] + 1;
    }
    fprintf(stderr, "feasible %ld\n", count);
    return 0;
}
