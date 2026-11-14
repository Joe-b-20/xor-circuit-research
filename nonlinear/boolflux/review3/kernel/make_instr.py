"""Build bfx_instr.c: a copy of kernel/bfx.c that counts accepted moves whose result is the
same circuit up to gate renumbering (structural hash equal before and after), and prints the
count at the end.  The search itself is unchanged (no extra RNG calls, same decisions).

    python3 make_instr.py && gcc -O2 -o bfx_instr bfx_instr.c -lm
"""
from pathlib import Path

here = Path(__file__).resolve().parent
src = (here.parents[1] / 'kernel' / 'bfx.c').read_text()
helper = r'''
/* review3: structural hash, invariant under gate renumbering and operand order of symmetric ops */
static u64 *SH;
static u64 mix64(u64 z) { z += 0x9E3779B97F4A7C15ULL; z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL; z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL; return z ^ (z >> 31); }
static u64 struct_hash(const Circ *c) {
    if (!SH) SH = malloc(sizeof(u64) * (MAXN + GCAP + 16));
    for (int i = 0; i < N; i++) SH[i] = mix64(1000 + i);
    u64 tot = 0;
    for (int j = 0; j < c->ng; j++) {
        const Gate *g = &c->g[j]; u64 ha = SH[g->a], hb = SH[g->b];
        if (op_sym(g->op) && ha > hb) { u64 t = ha; ha = hb; hb = t; }
        SH[N + j] = mix64(mix64(g->op * 7919ULL + ha) ^ (hb * 31));
        tot += mix64(SH[N + j]);           /* multiset of gate signatures */
    }
    for (int k = 0; k < M; k++) tot ^= mix64(SH[c->out[k]] + 77 * k);
    return tot;
}
static long st_iso_acc;
'''
marker = '/* ------------------------------------------------------------------ main loop */'
assert marker in src
src = src.replace(marker, helper + marker)
old = '            eval_cand(s, &CAND[accept], &m);\n            circ_copy(&cur, &cand_c); state_refresh();'
assert old in src
src = src.replace(old, '            u64 h_before = struct_hash(&cur);\n' + old
                  + '\n            int iso = struct_hash(&cur) == h_before; if (iso) st_iso_acc++;'
                  + '\n            if (tmv) fprintf(tmv, " | review3_iso %d", iso);')
old2 = '    printf("noop_candidates_skipped %ld\\n", st_noop);'
assert old2 in src
src = src.replace(old2, old2 + '\n    printf("review3_accepted_structurally_identical %ld of %ld accepted\\n", st_iso_acc, st_acc[0] + st_acc[1] + st_acc[2]);')
(here / 'bfx_instr.c').write_text(src)
print('wrote', here / 'bfx_instr.c')
