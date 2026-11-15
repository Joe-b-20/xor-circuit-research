"""Make bfx_dl.c = kernel/bfx.c + per-output gate-depth offsets (config `outoff o0,o1,...`): output k
counts as level + o_k against the GD cap (so o_k = D - deadline_k gives per-output deadlines), in the
metrics, the repair penalty and the required times.  The shared kernel is not modified."""
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE.parents[1] / 'kernel' / 'bfx.c').read_text()


def rep(a, b):
    global src
    assert src.count(a) == 1, a
    src = src.replace(a, b)


rep("static int cap_gd = -1, cap_ad = -1, cap_a = -1;",
    "static int cap_gd = -1, cap_ad = -1, cap_a = -1;\nstatic int OFF[MAXM];   /* T2: per-output gate-depth offsets */")
rep("        if (LG_tmp[c->out[k]] > m->gd) m->gd = LG_tmp[c->out[k]];",
    "        if (LG_tmp[c->out[k]] + OFF[k] > m->gd) m->gd = LG_tmp[c->out[k]] + OFF[k];")
rep("        for (int k = 0; k < M; k++) { HG_tmp[c->out[k]] = 0; HA_tmp[c->out[k]] = 0; }",
    "        for (int k = 0; k < M; k++) { if (OFF[k] > HG_tmp[c->out[k]]) HG_tmp[c->out[k]] = OFF[k]; HA_tmp[c->out[k]] = 0; }")
rep("        int cg = cap_gd >= 0 ? cap_gd : INF_LVL, ca = cap_ad >= 0 ? cap_ad : INF_LVL;",
    "        int cg = cap_gd >= 0 ? cap_gd - OFF[k] : INF_LVL, ca = cap_ad >= 0 ? cap_ad : INF_LVL;")
rep('        else if (!strcmp(k, "tracemoves")) strcpy(cfg_tracemoves, v);',
    '        else if (!strcmp(k, "tracemoves")) strcpy(cfg_tracemoves, v);\n'
    '        else if (!strcmp(k, "outoff")) { char *p = v; for (int q = 0; q < MAXM && *p; q++) { OFF[q] = (int)strtol(p, &p, 10); if (*p == \',\') p++; } }')
(HERE / 'bfx_dl.c').write_text(src)
print('ok')
