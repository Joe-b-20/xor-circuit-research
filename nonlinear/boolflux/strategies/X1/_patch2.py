s = open("bfw.c").read()
if "tabu_len" not in s:
    s = s.replace("static long st_flip, st_split, st_merge, st_restart, st_step, st_redec;",
                  "static long st_flip, st_split, st_merge, st_restart, st_step, st_redec;\nstatic int tabu_i = -1, tabu_k = -1, tabu_len = 0; static long tabu_until = 0;   /* tabu_len > 0: no forced flip after a split, the split pair may not merge for tabu_len steps */")
    old = """    u64 c0 = c & ~1ULL;
    if (rint_(2)) { if (!depends(p, j, k)) flip(p, k, j, c0); }
    else { if (!depends(p, k, j)) flip(p, j, k, c0); }
    return 1;"""
    new = """    u64 c0 = c & ~1ULL;
    if (tabu_len > 0) { tabu_i = i; tabu_k = k; tabu_until = st_step + tabu_len; return 1; }
    if (rint_(2)) { if (!depends(p, j, k)) flip(p, k, j, c0); }
    else { if (!depends(p, k, j)) flip(p, j, k, c0); }
    return 1;"""
    assert old in s; s = s.replace(old, new)
    old = """        u64 a = common(p, ks[x], ks[y], 0);
        if (a) {"""
    new = """        u64 a = common(p, ks[x], ks[y], 0);
        if (a && st_step < tabu_until && ((ks[x] == tabu_i && ks[y] == tabu_k) || (ks[x] == tabu_k && ks[y] == tabu_i))) continue;
        if (a) {"""
    assert old in s; s = s.replace(old, new)
    old = "    int adcap = argc > 9 ? atoi(argv[9]) : 0; int dump = argc > 10 ? atoi(argv[10]) : 0;"
    new = old + "\n    tabu_len = argc > 11 ? atoi(argv[11]) : 0;"
    assert old in s; s = s.replace(old, new)
    open("bfw.c", "w").write(s)
d = open("x1walkc.py").read()
if "tabu" not in d:
    d = d.replace("adcap=0, dump=0):", "adcap=0, dump=0, tabu=0):")
    d = d.replace("str(adcap), str(dump)],", "str(adcap), str(dump), str(tabu)],")
    d = d.replace('opt("--adcap", 0), opt("--dump", 0))', 'opt("--adcap", 0), opt("--dump", 0), opt("--tabu", 0))')
    open("x1walkc.py", "w").write(d)
print("ok")
