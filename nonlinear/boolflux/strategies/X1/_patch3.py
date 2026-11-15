s = open("bfw.c").read()
if "pshift" not in s:
    s = s.replace("static long st_flip, st_split, st_merge, st_restart, st_step, st_redec;",
                  "static long st_flip, st_split, st_merge, st_restart, st_step, st_redec, st_shift;\nstatic double pshift = 0.0;   /* probability of a shift step: L*R = (L+R)*R + R, readers of the product also read R */")
    old = "    if (rdbl() < psplit && n < bestA + plus) return do_split(p) * 0;"
    new = """    if (pshift > 0 && rdbl() < pshift) {
        int k = ks[rint_(n)];
        if (rint_(2)) { u64 t = p->L[k]; p->L[k] = p->R[k]; p->R[k] = t; }
        u64 Rk = p->R[k];
        if (Rk & p->alive) {              /* only useful when R reads a product */
            substitute(p, k, Rk); p->L[k] ^= Rk; st_shift++;
            if (remove_dead(p)) { st_merge++; return 1; }
        }
        return 0;
    }
""" + old
    assert old in s; s = s.replace(old, new)
    old = "    tabu_len = argc > 11 ? atoi(argv[11]) : 0;"
    new = old + "\n    pshift = argc > 12 ? atof(argv[12]) : 0.0;"
    assert old in s; s = s.replace(old, new)
    s = s.replace('printf("end A %d steps %ld flips %ld splits %ld merges %ld redec %ld restarts %ld pool %d\\n", bestA, st_step, st_flip, st_split, st_merge, st_redec, st_restart, npool);',
                  'printf("end A %d steps %ld flips %ld splits %ld merges %ld redec %ld shifts %ld restarts %ld pool %d\\n", bestA, st_step, st_flip, st_split, st_merge, st_redec, st_shift, st_restart, npool);')
    assert "shifts %ld" in s
    open("bfw.c", "w").write(s)
d = open("x1walkc.py").read()
if "shift" not in d:
    d = d.replace("adcap=0, dump=0, tabu=0):", "adcap=0, dump=0, tabu=0, shift=0.0):")
    d = d.replace("str(adcap), str(dump), str(tabu)],", "str(adcap), str(dump), str(tabu), str(shift)],")
    d = d.replace('opt("--tabu", 0))', 'opt("--tabu", 0), opt("--shift", 0.0))')
    open("x1walkc.py", "w").write(d)
print("ok")
