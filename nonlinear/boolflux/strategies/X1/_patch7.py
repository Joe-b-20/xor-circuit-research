s = open("walkcamp.py").read()
if "pmerge" not in s:
    a = s.index("PARAMS = ["); b = s.index("\n\n\ndef main")
    s = s[:a] + """PARAMS = [  # plus, psplit, horizon, redec, pmerge
    (1, 0.02, 20000, 0.2, 1.0), (2, 0.05, 5000, 0.2, 1.0), (2, 0.05, 5000, 0.3, 0.05), (1, 0.05, 5000, 0.2, 0.05),
    (3, 0.05, 20000, 0.3, 0.2), (2, 0.02, 20000, 0.2, 0.01), (1, 0.02, 2000, 0.2, 0.2), (3, 0.1, 5000, 0.2, 0.05)]""" + s[b:]
    old = "        plus, psplit, horizon, redec = rng.choice(PARAMS)\n"
    new = "        plus, psplit, horizon, redec, pmerge = rng.choice(PARAMS)\n"
    assert old in s; s = s.replace(old, new)
    old = "            res, wlog = W.run(c, wd, secs, seed, plus, psplit, horizon, redec, tag, cap, 12)\n"
    new = "            res, wlog = W.run(c, wd, secs, seed, plus, psplit, horizon, redec, tag, cap, 12, 0, 0.0, pmerge)\n"
    assert old in s; s = s.replace(old, new)
    s = s.replace("'horizon': horizon, 'redec': redec,", "'horizon': horizon, 'redec': redec, 'pmerge': pmerge,")
    s = s.replace("'params', (plus, psplit, horizon, redec),", "'params', (plus, psplit, horizon, redec, pmerge),")
    open("walkcamp.py", "w").write(s)
print("ok")
