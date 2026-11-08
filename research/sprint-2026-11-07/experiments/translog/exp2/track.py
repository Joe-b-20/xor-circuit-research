#!/usr/bin/env python3
"""exp2 online tracker (one process, nice 8, during the run): tails the eight translog.jsonl
files, computes the v3 signature of every new 88 identity (entries `v`; departure states `xv`
only when needed), keeps sig -> {worker: first (t, values)}, and spends the remaining time on
the exact work of measurement (d) with pes_lib.compress (per-call alarm timeout):
  priority 1: every v3 node shared by two chains of DIFFERENT groups (cross-seed);
  priority 2: a sample of 100 consecutive (departure xv, next entry v) hops of chain q0-00,
              starting at the first departure after t = 600 s (if q0-00 has too few, q1-00..);
  priority 3: every v3 node shared by the two chains of a same-start pair (excl. start node).
Outputs: sigcache.json {id: sig}, exact.jsonl (one row per exact test), track_status.json.
Loops until exp2/DONE exists, then a final read pass and remaining exact work up to the budget.
usage: track.py [EXACT_BUDGET_S=5400] [PER_CALL_S=60]"""
import glob, json, os, signal, sys, time
sys.path.insert(0, os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/translog"))
import plateau_sig as ps  # noqa: E402
import pes_lib  # noqa: E402  (path set by plateau_sig)

E = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/translog/exp2")
RUNS = os.path.join(E, "runs/E2/workers")
BUDGET = float(sys.argv[1]) if len(sys.argv) > 1 else 5400.0
PER_CALL = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
sp = ps.sp
SIGF = os.path.join(E, "sigcache.json")
sigc = json.load(open(SIGF)) if os.path.exists(SIGF) else {}
exact_out = open(os.path.join(E, "exact.jsonl"), "a")


class CompressTimeout(Exception):
    pass


def _alarm(signum, frame):
    raise CompressTimeout()


signal.signal(signal.SIGALRM, _alarm)


def hk_of(values):
    helpers = [v for v in values if v not in sp.tset]
    stt = sp.state(helpers)
    if stt.count() != 88 or stt.depth() is None:
        return None
    return sp.hkey(stt)


PL_CACHE = {}


def member(pl, values):
    hk = hk_of(values)
    if hk is None:
        return None
    for s in sp.shifts:
        rk = sp.rot(hk, s) if s else hk
        if pl.contains(frozenset(rk)):
            return True
    return False


exact_used = 0.0


def compress_state(values, sig):
    global exact_used
    for pl0, info0 in PL_CACHE.get(sig, ()):
        if member(pl0, values):
            return pl0, {**info0, "cached": True}
    hk = hk_of(values)
    if hk is None:
        return None, {"error": "not an 88 state"}
    t0 = time.time()
    signal.alarm(int(PER_CALL) + 5)
    try:
        pl, info = pes_lib.compress(sp, hk, verify_limit=20000, closure_limit=3000, time_limit=PER_CALL)
    except CompressTimeout:
        return None, {"error": "timeout", "seconds": PER_CALL}
    except Exception as exc:  # noqa: BLE001
        return None, {"error": repr(exc)[:200]}
    finally:
        signal.alarm(0)
        exact_used += time.time() - t0
    inexact = info.get("verified") == "closure-truncated" or (pl.kind != "product" and info.get("note"))
    out = {"kind": pl.kind, "size": pl.size(), "radices": pl.radices() if pl.kind == "product" else None,
           "verified": info.get("verified"), "inexact": bool(inexact), "seconds": round(time.time() - t0, 1),
           "downs": len(info.get("downs") or [])}
    PL_CACHE.setdefault(sig, []).append((pl, out))
    return pl, out


def sig_of_values(values, ident=None):
    if ident is not None and ident in sigc:
        return sigc[ident]
    try:
        s, info = ps.sig_of(values)
    except Exception:  # noqa: BLE001
        s = None
    if ident is not None:
        sigc[ident] = s
    return s


def group(w):
    return w.split("-")[0]


offsets = {}
first = {}            # sig -> {worker: (t, values)}
start_sig = {}        # worker -> sig of its first state
q_cross, q_same, done_shared = [], [], set()
hop_rows = {}         # worker -> rows (departures and entries) at t >= 600 for the hop sample
hop_worker = None
hop_done = 0
n_new = 0


def read_pass():
    global n_new
    for f in sorted(glob.glob(os.path.join(RUNS, "*/translog.jsonl"))):
        w = os.path.basename(os.path.dirname(f))
        with open(f, "rb") as fh:
            fh.seek(offsets.get(w, 0))
            data = fh.read()
        cut = data.rfind(b"\n")
        if cut < 0:
            continue
        offsets[w] = offsets.get(w, 0) + cut + 1
        for line in data[:cut + 1].decode().splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("k") not in ("step", "chain"):
                continue
            if r.get("g", 99) <= 88 and r.get("v"):
                s = sig_of_values(r["v"], r.get("id"))
                n_new += 1
                if w not in start_sig:
                    start_sig[w] = s
                if r["t"] >= 600:
                    hop_rows.setdefault(w, []).append(("e", r["t"], r["v"], r.get("id")))
                if s is None:
                    continue
                d = first.setdefault(s, {})
                if w not in d:
                    d[w] = (r["t"], r["v"])
                    if len(d) >= 2 and (s, w) not in done_shared:
                        done_shared.add((s, w))
                        others = [o for o in d if o != w]
                        cross = [o for o in others if group(o) != group(w)]
                        if cross:
                            q_cross.append((s, cross[0], w))
                        elif s != start_sig.get(w) and s != start_sig.get(others[0]):
                            q_same.append((s, others[0], w))
            elif "xv" in r and r["t"] >= 600:
                hop_rows.setdefault(w, []).append(("x", r["t"], r["xv"], r.get("xid")))


def hop_pairs(w):
    rows = hop_rows.get(w, [])
    out = []
    for i, a in enumerate(rows):
        if a[0] == "x" and i + 1 < len(rows) and rows[i + 1][0] == "e":
            out.append((a, rows[i + 1]))
    return out


def exact_shared(item, kind):
    s, w1, w2 = item
    t1, v1 = first[s][w1]
    t2, v2 = first[s][w2]
    pl, info = compress_state(v1, s)
    res = {"test": kind, "sig": s, "a": w1, "b": w2, "ta": t1, "tb": t2, **info}
    if pl is not None:
        res["b_in_a"] = member(pl, v2)
    exact_out.write(json.dumps(res) + "\n")
    exact_out.flush()


def exact_hop(k, a, b, w):
    sa = sig_of_values(a[2], None)
    sb = sig_of_values(b[2], b[3])
    pl, info = compress_state(a[2], sa) if sa else (None, {"error": "no sig"})
    res = {"test": "hop", "k": k, "worker": w, "t_dep": a[1], "t_entry": b[1], "sig_dep": sa,
           "sig_entry": sb, "same_state": a[3] == b[3], "sym_diff": len(set(a[2]) ^ set(b[2])), **info}
    if pl is not None:
        res["entry_in_dep"] = member(pl, b[2])
    exact_out.write(json.dumps(res) + "\n")
    exact_out.flush()


def status(tag):
    st = {"time": time.strftime("%H:%M:%SZ", time.gmtime()), "tag": tag, "sigs_cached": len(sigc),
          "entries_read": n_new, "distinct_sigs": len(first),
          "shared_cross": sum(1 for d in first.values() if len({group(w) for w in d}) > 1),
          "shared_any": sum(1 for d in first.values() if len(d) > 1),
          "q_cross": len(q_cross), "q_same": len(q_same), "hop_done": hop_done, "hop_worker": hop_worker,
          "exact_used_s": round(exact_used), "offsets": offsets}
    json.dump(st, open(os.path.join(E, "track_status.json"), "w"), indent=1)
    tmp = SIGF + ".tmp"
    json.dump(sigc, open(tmp, "w"))
    os.replace(tmp, SIGF)
    print(st["time"], tag, {k: st[k] for k in ("entries_read", "distinct_sigs", "shared_cross", "shared_any",
                                                "q_cross", "q_same", "hop_done", "exact_used_s")}, flush=True)


def exact_work(seconds):
    """Do exact work for about `seconds` (each compress capped by PER_CALL)."""
    global hop_done, hop_worker
    t_end = time.time() + seconds
    while time.time() < t_end and exact_used < BUDGET:
        if q_cross:
            exact_shared(q_cross.pop(0), "shared_cross")
            continue
        if hop_done < 100:
            if hop_worker is None:
                for w in ("q0-00", "q1-00", "q2-00", "q3-00", "q0-01", "q1-01", "q2-01", "q3-01"):
                    if len(hop_pairs(w)) >= 100:
                        hop_worker = w
                        break
            if hop_worker is not None:
                a, b = hop_pairs(hop_worker)[hop_done]
                exact_hop(hop_done, a, b, hop_worker)
                hop_done += 1
                continue
        if q_same:
            exact_shared(q_same.pop(0), "shared_same")
            continue
        return


while True:
    fin = os.path.exists(os.path.join(E, "DONE"))
    read_pass()
    status("pass")
    if fin:
        break
    t_w = time.time()
    exact_work(45)
    if time.time() - t_w < 20:
        time.sleep(30)
read_pass()
status("final-read")
while exact_used < BUDGET and (q_cross or q_same or hop_done < 100):
    before = (len(q_cross), len(q_same), hop_done)
    exact_work(60)
    status("final-exact")
    if before == (len(q_cross), len(q_same), hop_done):
        break
status("end")
