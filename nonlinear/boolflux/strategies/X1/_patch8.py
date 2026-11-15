s = open("walkcamp.py").read()
if "REACHED" not in s:
    old = "            if m[0] >= m0[0]: continue\n"
    new = ("            if m[0] >= m0[0]: continue\n"
           "            if m[0] >= amin:          # lower than its start, but not below the campaign's lowest AND count: log only\n"
           "                rec['results'].append(m); log('REACHED', m, 'from', Path(f).name, m0); continue\n")
    assert old in s; s = s.replace(old, new)
    open("walkcamp.py", "w").write(s)
print("ok")
