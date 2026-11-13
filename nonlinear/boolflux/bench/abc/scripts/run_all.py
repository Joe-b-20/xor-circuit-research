#!/usr/bin/env python3
"""Run the whole ABC comparator matrix: 4 slots, slot i pinned to CPU 16+i (taskset -c).
Usage: run_all.py EXT_DIR REPO_DIR [small|aes|all]
"""
import os
import queue
import subprocess
import sys
import threading
import time

EXT, REPO = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
WHICH = sys.argv[3] if len(sys.argv) > 3 else "all"
BF = os.path.join(REPO, "nonlinear/boolflux")
CPUS = [16, 17, 18, 19]

jobs = []


def add(target, lib, start, budget, chunks, extra="", tag=None):
    tag = tag or target
    for flow, seeds in (("classic", [0]), ("deepsyn", [1, 2, 3, 4, 5]), ("eslim", [1, 2, 3, 4, 5])):
        for s in seeds:
            out = os.path.join(EXT, "results", f"{tag}__{lib}__{flow}__s{s}")
            jobs.append([
                sys.executable, os.path.join(EXT, "scripts/abc_run.py"),
                "--abc", os.path.join(EXT, "abc-src/abc"), "--rc", os.path.join(EXT, "abc-src/abc.rc"),
                "--lib", os.path.join(EXT, "genlib", f"{lib}.genlib"),
                "--start", os.path.join(EXT, "targets", start),
                "--fn", os.path.join(EXT, "targets", f"{target}.fn.json"),
                "--model", os.path.join(BF, "models", f"{lib}.json"),
                "--verify", os.path.join(BF, "independent/verify.py"),
                "--flow", flow, "--seed", str(s), "--budget", str(budget),
                "--chunk", str(chunks[flow]), "--out", out] + ([f"--extra-verify={extra}"] if extra else []))


SMALL = {"classic": 0, "deepsyn": 5, "eslim": 10}
BIG = {"classic": 0, "deepsyn": 25, "eslim": 50}
if WHICH in ("small", "all"):
    for t in ("present", "rectangle", "ascon", "prince"):
        for lib in ("bgc", "gc6"):
            add(t, lib, f"{t}.blif", 60, SMALL)
    for lib in ("xag", "nist"):
        add("gf16-mul", lib, "gf16-mul.blif", 60, SMALL)
if WHICH in ("aes", "all"):
    add("aes", "nist", "aes.blif", 300, BIG, "--aes", tag="aes-naive")
    add("aes", "nist", "aes-nist104.blif", 300, BIG, "--aes", tag="aes-warm104")

jobs.sort(key=lambda j: -float(j[j.index("--budget") + 1]))  # long jobs first
q = queue.Queue()
for j in jobs:
    q.put(j)
lock = threading.Lock()


def worker(cpu):
    while True:
        try:
            j = q.get_nowait()
        except queue.Empty:
            return
        t = time.time()
        r = subprocess.run(["taskset", "-c", str(cpu)] + j, capture_output=True, text=True)
        with lock:
            print(f"[cpu{cpu} {time.strftime('%H:%M:%S')} {time.time()-t:6.1f}s] "
                  f"{os.path.basename(j[-1] if j[-2] == '--out' else j[j.index('--out')+1])} "
                  f"{r.stdout.strip()} {r.stderr.strip()[-300:]}", flush=True)


print(f"{len(jobs)} jobs, start {time.strftime('%H:%M:%S')}", flush=True)
ths = [threading.Thread(target=worker, args=(c,)) for c in CPUS]
for th in ths:
    th.start()
for th in ths:
    th.join()
print("done", time.strftime("%H:%M:%S"), flush=True)
