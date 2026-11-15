/* P4: for many target sets over GF(2)^8 (from the 8 unit vectors, no depth limit), the minimum
   number of helper values H (<= HMAX) such that targets + helpers is closure-feasible
   (every value the XOR of two earlier values).  The XOR count of the set is then (#targets + H).
   stdin: HMAX, then repeated records "n v1 ... vn" (non-unit distinct targets), terminated by EOF.
   stdout: one line per record: H (or HMAX+1 when none <= HMAX).
*/
#include <stdio.h>
#include <string.h>

static int inS[256];

static int feasible(const int *S, int ns) {
    unsigned char have[256];
    int hl[80], nh = 0;
    memset(have, 0, sizeof have);
    for (int i = 0; i < 8; i++) { have[1 << i] = 1; hl[nh++] = 1 << i; }
    int done[64];
    memset(done, 0, sizeof done);
    int left = ns, prog = 1;
    while (left && prog) {
        prog = 0;
        for (int i = 0; i < ns; i++) {
            if (done[i]) continue;
            int t = S[i];
            for (int q = 0; q < nh; q++) {
                if (have[hl[q] ^ t]) { have[t] = 1; hl[nh++] = t; done[i] = 1; left--; prog = 1; break; }
            }
        }
    }
    return left == 0;
}

int main(void) {
    int HMAX;
    if (scanf("%d", &HMAX) != 1) return 1;
    int n;
    while (scanf("%d", &n) == 1) {
        int T[64];
        for (int i = 0; i < n; i++) if (scanf("%d", &T[i]) != 1) return 1;
        memset(inS, 0, sizeof inS);
        for (int i = 0; i < n; i++) inS[T[i]] = 1;
        int cand[256], nc = 0;
        for (int v = 1; v < 256; v++) if ((v & (v - 1)) && !inS[v]) cand[nc++] = v;
        int found = -1;
        int S[64];
        for (int H = 0; H <= HMAX && found < 0; H++) {
            int idx[8];
            for (int i = 0; i < H; i++) idx[i] = i;
            while (1) {
                int ns = 0;
                for (int i = 0; i < n; i++) S[ns++] = T[i];
                for (int i = 0; i < H; i++) S[ns++] = cand[idx[i]];
                if (feasible(S, ns)) { found = H; break; }
                if (H == 0) break;
                int k = H - 1;
                while (k >= 0 && idx[k] == nc - H + k) k--;
                if (k < 0) break;
                idx[k]++;
                for (int j = k + 1; j < H; j++) idx[j] = idx[j - 1] + 1;
            }
        }
        printf("%d\n", found < 0 ? HMAX + 1 : found);
        fflush(stdout);
    }
    return 0;
}
