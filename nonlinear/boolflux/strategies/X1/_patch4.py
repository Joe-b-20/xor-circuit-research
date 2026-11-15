s = open("walkcamp.py").read()
if "adcap_prob" not in s:
    old = "    hours = opt('--hours', 1.0); slc = opt('--slice', 600.0); shard = opt('--shard', 0); target = opt('--target', 27)\n"
    new = old + "    adcap_prob = opt('--adcap-prob', 0.0)       # share of runs that keep the start's AND depth (bfw adcap)\n"
    assert old in s; s = s.replace(old, new)
    old = "            res, wlog = W.run(c, wd, secs, seed, plus, psplit, horizon, redec, tag, 0, 12)\n"
    new = "            cap = m0[1] if rng.random() < adcap_prob else 0\n            res, wlog = W.run(c, wd, secs, seed, plus, psplit, horizon, redec, tag, cap, 12)\n"
    assert old in s; s = s.replace(old, new)
    s = s.replace("'seed': seed, 'seconds': round(time.time() - t0, 1),", "'seed': seed, 'adcap': cap, 'seconds': round(time.time() - t0, 1),")
    s = s.replace("    python3 walkcamp.py OUT_DIR --hours H [--slice 600] [--shard K] [--target 27] [--starts FILE...]",
                  "    python3 walkcamp.py OUT_DIR --hours H [--slice 600] [--shard K] [--target 27] [--adcap-prob P] --starts FILE...   (--starts last)")
    open("walkcamp.py", "w").write(s)
print("ok")
