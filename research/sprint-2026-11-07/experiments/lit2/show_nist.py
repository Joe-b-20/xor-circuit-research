import os
d=os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/lit2/dl")
for f in ["nist_97d3.txt","nist_90d4.txt","nist_88d5.txt","nist_top_README.md"]:
    p=os.path.join(d,f)
    print("===",f,os.path.getsize(p) if os.path.exists(p) else "MISSING")
    if os.path.exists(p):
        lines=open(p,errors="replace").read().splitlines()
        if f.endswith(".md"):
            for i,l in enumerate(lines):
                if "ixcol" in l.lower(): print(i+1,l[:200])
        else:
            for l in lines[:14]: print(l[:160])
