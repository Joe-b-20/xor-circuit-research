"""invskel: paid inputs (inputs that cost one gate, with extra one-gate boundary forms)."""
p = "invskel.py"; s = open(p).read()
# closure: boundary forms buildable in one gate at any stage
s = s.replace("""            for f in [f for f, l in rem.items() if l >= st]:
                if any((f ^ g) in alset for g in al):""", """            for f in [f for f, l in rem.items() if l >= st]:
                if f in PAIDX or any((f ^ g) in alset for g in al):""")
s = s.replace("ONES = 0xffff\n", "ONES = 0xffff\nPAIDX = set()\n", 1)
s = s.replace("""    global ONES
    ONES = (1 << (1 << spec["k"])) - 1
    V = [int(i['table'], 16) for i in spec['inputs']]""", """    global ONES, PAIDX
    ONES = (1 << (1 << spec["k"])) - 1
    V = [int(i['table'], 16) for i in spec['inputs']]
    VF = [int(i['table'], 16) for i in spec['inputs'] if not i.get('paid')]
    for bf in spec.get('boundary', []):
        t = int(bf['table'], 16); PAIDX.add(t); PAIDX.add(t ^ ONES)""")
s = s.replace("""        blev = {v: 0 for v in V}""", """        blev = {v: 0 for v in VF}""")
s = s.replace("""        B = set(V) | {c[3] for c in chosen}""", """        B = set(VF) | {c[3] for c in chosen}""")
open(p, "w").write(s)
print(s.count("VF"), s.count("PAIDX"))
