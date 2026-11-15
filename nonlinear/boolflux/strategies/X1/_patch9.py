import re
d = open("x1walkc.py").read()
if "os.replace" not in d:
    old = d[d.index("    if not b.exists():"):d.index("    return b")]
    new = """    if not b.exists():
        import os
        Path(out).mkdir(parents=True, exist_ok=True)
        tmp = str(b) + ".tmp%d" % os.getpid()
        subprocess.run(["gcc", "-O3", "-march=native", "-o", tmp, str(src)], check=True)
        os.replace(tmp, b)            # atomic: several shards may start at once
"""
    d = d.replace(old, new)
    open("x1walkc.py", "w").write(d)
print("ok")
