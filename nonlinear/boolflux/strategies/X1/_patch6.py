s = open("bfw.c").read()
if "pmerge" not in s:
    s = s.replace("static double pshift = 0.0;",
                  "static double pmerge = 1.0;   /* above the best AND count a merge is accepted with this probability (unless a second merge follows at once) */\nstatic long st_double;\nstatic double pshift = 0.0;")
    # has_merge before step()
    hm = r"""static int has_merge(const Prog *p, Prog *out) {      /* one merge available? */
    u64 sig[NB]; int ks[NB], n = 0; u64 m = p->alive;
    while (m) { ks[n++] = __builtin_ctzll(m); m &= m - 1; }
    sigs(p, sig);
    for (int x = 0; x < n; x++) for (int y = x + 1; y < n; y++) if (sig[ks[x]] == sig[ks[y]]) {
        u64 a = common(p, ks[x], ks[y], 0);
        if (!a) continue;
        Prog q = *p;
        if (flip(&q, ks[x], ks[y], a) && remove_dead(&q)) { *out = q; return 1; }
    }
    return 0;
}

static int step("""
    s = s.replace("static int step(", hm, 1)
    old = """        if (a) {
            if (flip(p, ks[x], ks[y], a)) { if (remove_dead(p)) { st_merge++; return 1; } return 0; }
        } else { neq++; if (rint_(neq) == 0) { ei = ks[x]; ej = ks[y]; } }
    }
"""
    new = """        if (a) {
            Prog q = *p;
            if (!flip(&q, ks[x], ks[y], a) || !remove_dead(&q)) continue;
            if (n > bestA) { Prog q2; if (has_merge(&q, &q2)) { *p = q2; st_merge += 2; st_double++; return 1; } }
            ncand++; if (rint_(ncand) == 0) cand = q;
        } else { neq++; if (rint_(neq) == 0) { ei = ks[x]; ej = ks[y]; } }
    }
    if (ncand && (n <= bestA || rdbl() < pmerge)) { *p = cand; st_merge++; return 1; }
"""
    assert old in s; s = s.replace(old, new)
    old = "    int ei = -1, ej = -1, neq = 0;\n"
    new = "    int ei = -1, ej = -1, neq = 0, ncand = 0; Prog cand;\n"
    assert old in s; s = s.replace(old, new)
    old = "    pshift = argc > 12 ? atof(argv[12]) : 0.0;"
    new = old + "\n    pmerge = argc > 13 ? atof(argv[13]) : 1.0;"
    assert old in s; s = s.replace(old, new)
    s = s.replace('printf("spans at best A: %ld  product sets: %ld  rejected(adcap) %ld\\n", n_span, n_fam, st_rej);',
                  'printf("spans at best A: %ld  product sets: %ld  rejected(adcap) %ld  double merges %ld\\n", n_span, n_fam, st_rej, st_double);')
    assert "double merges" in s
    open("bfw.c", "w").write(s)
d = open("x1walkc.py").read()
if "pmerge" not in d:
    d = d.replace("tabu=0, shift=0.0):", "tabu=0, shift=0.0, pmerge=1.0):")
    d = d.replace("str(tabu), str(shift)],", "str(tabu), str(shift), str(pmerge)],")
    d = d.replace('opt("--shift", 0.0))', 'opt("--shift", 0.0), opt("--pmerge", 1.0))')
    open("x1walkc.py", "w").write(d)
print("ok")
