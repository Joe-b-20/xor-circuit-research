#!/usr/bin/env python3
"""Transition graph of the 88 level as seen by the hunt samplers (arms A, B, C).

Nodes = 88 plateaus identified by the v3 signature (sigs2.json), merged where plateaus.json
gives the same exact plateau key.  A chain = (arm, worker, engine chain index), delimited by the
'restart' events in events.jsonl (chain index = number of restarts with t <= sample t, as in
chains_plateaus.py).  Along a chain the 30 s samples (gates 88 or 89) are ordered by wall time;
consecutive distinct 88 nodes give a directed edge, with the 89 excursion between them measured
in samples, seconds (worker clock) and steps.
Also: fans (depth, downs, neutral count) of every sampled 88 state via pes_lib, Jaccard distance
of value sets across hops (modulo byte rotation), landings (first 88 node per chain) vs later.
Writes graph_data.json and prints the report numbers.  Usage: graph.py HUNT_DIR OUT_DIR
"""
import collections, glob, json, os, sys, time, statistics

HUNT = sys.argv[1]
OUT = sys.argv[2]
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import pes_lib  # noqa: E402

sp = pes_lib.make_space("mc", None)
store = json.load(open(os.path.join(HUNT, "plateaus.json")))
h2key = store["states"]
P = store["plateaus"]
sigs = json.load(open(os.path.join(HUNT, "sigs2.json")))


def med(xs, f="{:.0f}"):
    xs = sorted(xs)
    if not xs:
        return "-"
    n = len(xs)
    return (f"n={n} min=" + f + " q1=" + f + " med=" + f + " q3=" + f + " max=" + f).format(
        xs[0], xs[n // 4], xs[n // 2], xs[(3 * n) // 4], xs[-1])


# ------------------------------------------------------------------ samples per chain
restarts = {}
for arm in sorted(os.listdir(os.path.join(HUNT, "runs"))):
    wdir = os.path.join(HUNT, "runs", arm, "workers")
    if not os.path.isdir(wdir):
        continue
    for w in sorted(os.listdir(wdir)):
        p = os.path.join(wdir, w, "events.jsonl")
        if not os.path.exists(p):
            continue
        ts = []
        for line in open(p):
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get("ev") == "restart":
                ts.append(e["t"])
        restarts[(arm, w)] = sorted(ts)


def chain_index(arm, w, t):
    ts = restarts.get((arm, w), [])
    i = 0
    while i < len(ts) and ts[i] <= t:
        i += 1
    return i


samples = []
for path, arms in ((os.path.join(HUNT, "samples.jsonl"), {"A", "B"}),
                   (os.path.join(HUNT, "samplesC", "samples.jsonl"), {"C"})):
    for line in open(path):
        r = json.loads(line)
        if r["arm"] in arms:
            samples.append(r)
samples.sort(key=lambda r: (r["arm"], r["worker"], r["wall"]))
gate_counts = collections.Counter((r["arm"], r["gates"]) for r in samples)
print("samples by (arm, gates):", sorted(gate_counts.items()))
below88 = [r for r in samples if r["gates"] < 88]
print("samples with gates < 88:", len(below88))

# steps per second from consecutive samples of one worker
rates = []
by_w = collections.defaultdict(list)
for r in samples:
    by_w[(r["arm"], r["worker"])].append(r)
for k, rs in by_w.items():
    for a, b in zip(rs, rs[1:]):
        if a["t"] and b["t"] and b["t"] > a["t"] and b["steps"] is not None and a["steps"] is not None:
            dt = b["t"] - a["t"]
            if 20 <= dt <= 40 and b["steps"] > a["steps"]:
                rates.append((b["steps"] - a["steps"]) / dt)
print("steps per second (consecutive samples 20-40 s apart):", med(rates))

# ------------------------------------------------------------------ nodes: union-find on signatures
parent = {}


def find(x):
    parent.setdefault(x, x)
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb


state_sig = {}
for h, (s, arm, w, wall) in sigs.items():
    state_sig[h] = s
    find(s)
    k = h2key.get(h)
    if k:
        union(s, "key:" + k)
node_of_hash = {h: find(s) for h, s in state_sig.items()}
nodes_all = set(node_of_hash.values())
node_key = {}
for h, n in node_of_hash.items():
    k = h2key.get(h)
    if k:
        node_key.setdefault(n, set()).add(k)
multi_key = {n: ks for n, ks in node_key.items() if len(ks) > 1}
print(f"signatures: {len(set(state_sig.values()))}; nodes after exact-key merge (all 1869 states): {len(nodes_all)}; "
      f"nodes with an exact key: {len(node_key)}; nodes merging >1 exact key (should be 0): {len(multi_key)}")
sig_per_node = collections.Counter(find(s) for s in set(state_sig.values()))
merged_nodes = {n: c for n, c in sig_per_node.items() if c > 1}
print(f"nodes made of >1 signature (merged by exact key): {len(merged_nodes)}; signature counts: "
      f"{collections.Counter(merged_nodes.values())}")


def node_size(n):
    ks = node_key.get(n)
    if not ks:
        return None
    return P[next(iter(ks))]["size"]


# ------------------------------------------------------------------ fans of every sampled 88 state
t0 = time.time()
fan_info = {}
values_of = {}
for r in samples:
    if r["gates"] != 88 or r["hash"] in fan_info:
        continue
    values_of[r["hash"]] = r["values"]
    helpers = [v for v in r["values"] if v not in sp.tset]
    st = sp.state(helpers)
    if st.count() != 88:
        fan_info[r["hash"]] = None
        continue
    S = frozenset(sp.hkey(st))
    g, d, neutral, downs, binds = pes_lib.fan(sp, S)
    fan_info[r["hash"]] = {"depth": d, "downs": len(downs), "neutral": len(neutral)}
print(f"fans: {len(fan_info)} sampled 88 states in {time.time() - t0:.0f} s; "
      f"not 88 after trim: {sum(1 for v in fan_info.values() if v is None)}")
downs_pos = {h: v for h, v in fan_info.items() if v and v["downs"] > 0}
print(f"states with downs > 0 in fan terms: {len(downs_pos)}")
neutral_dist = collections.Counter(v["neutral"] for v in fan_info.values() if v)
print("neutral-move counts per state (top):", neutral_dist.most_common(12))

# ------------------------------------------------------------------ rotation-invariant Jaccard
def jaccard_rot(A, B, drop_targets):
    if drop_targets:
        A = [v for v in A if v not in sp.tset]
        B = [v for v in B if v not in sp.tset]
    A = set(A)
    best = 0.0
    for s in sp.shifts:
        Bs = set(sp.rot(tuple(B), s)) if s else set(B)
        j = len(A & Bs) / len(A | Bs)
        best = max(best, j)
    return 1.0 - best


# ------------------------------------------------------------------ trajectories
chains = collections.defaultdict(list)
missing = 0
for r in samples:
    c = chain_index(r["arm"], r["worker"], r["t"] or 0)
    chains[(r["arm"], r["worker"], c)].append(r)
visits = {}      # chain -> list of dict(node, first, last, n_samples, exc_samples, exc_s, exc_steps, exc_wall)
hops = []        # dicts per transition
for ck, rs in sorted(chains.items()):
    vs = []
    cur = None
    exc = 0
    last88 = None
    for r in rs:
        if r["gates"] != 88:
            if cur is not None:
                exc += 1
            continue
        h = r["hash"]
        n = node_of_hash.get(h)
        if n is None:
            missing += 1
            continue
        if cur is not None and n == cur["node"]:
            if exc:
                cur["returns"] += 1          # left to 89 and came back to the same node
                cur["return_exc"].append(exc)
            cur["last"] = r
            cur["n_samples"] += 1
            exc = 0
            continue
        v = {"node": n, "first": r, "last": r, "n_samples": 1, "returns": 0, "return_exc": [],
             "exc_samples": exc if cur is not None else None}
        if cur is not None:
            a, b = cur["last"], r
            hop = {"chain": ck, "u": cur["node"], "v": n, "exc_samples": exc,
                   "exc_wall": b["wall"] - a["wall"],
                   "exc_t": (b["t"] - a["t"]) if (a["t"] is not None and b["t"] is not None) else None,
                   "exc_steps": (b["steps"] - a["steps"]) if (a["steps"] is not None and b["steps"] is not None) else None,
                   "jac_h": jaccard_rot(a["values"], b["values"], True),
                   "jac_all": jaccard_rot(a["values"], b["values"], False),
                   "revisit": n in {x["node"] for x in vs}}
            hops.append(hop)
        vs.append(v)
        cur = v
        exc = 0
    if vs:
        visits[ck] = vs
print(f"88 samples without a node (not in sigs2): {missing}")
print(f"chains with sampled 88 states: {len(visits)} (per arm: "
      f"{dict(collections.Counter(k[0] for k in visits))}); hops: {len(hops)}")

# within-plateau drift for comparison: consecutive 88 samples inside the same visit
drift = []
for ck, rs in chains.items():
    prev = None
    for r in rs:
        if r["gates"] != 88:
            prev = None
            continue
        n = node_of_hash.get(r["hash"])
        if prev is not None and n == prev[0]:
            drift.append(jaccard_rot(prev[1], r["values"], True))
        prev = (n, r["values"])
print("within-plateau Jaccard distance (helpers, consecutive samples, same node):", med(drift, "{:.3f}"))

# ------------------------------------------------------------------ graph
nodes = set()
chains_of_node = collections.defaultdict(set)
workers_of_node = collections.defaultdict(set)
for ck, vs in visits.items():
    for v in vs:
        nodes.add(v["node"])
        chains_of_node[v["node"]].add(ck)
        workers_of_node[v["node"]].add(ck[:2])
edges = collections.Counter((h["u"], h["v"]) for h in hops)
edge_set = set(edges)
outdeg = collections.Counter(u for u, v in edge_set)
indeg = collections.Counter(v for u, v in edge_set)
deg = collections.Counter()
for u, v in edge_set:
    deg[u] += 1
    deg[v] += 1
# components
cp = {}


def cfind(x):
    cp.setdefault(x, x)
    while cp[x] != x:
        cp[x] = cp[cp[x]]
        x = cp[x]
    return x


for n in nodes:
    cfind(n)
for u, v in edge_set:
    ru, rv = cfind(u), cfind(v)
    if ru != rv:
        cp[ru] = rv
comp = collections.defaultdict(set)
for n in nodes:
    comp[cfind(n)].add(n)
comp_sizes = sorted((len(s) for s in comp.values()), reverse=True)
chains_per_comp = {c: {ck for n in s for ck in chains_of_node[n]} for c, s in comp.items()}
multi_chain_comps = sum(1 for c in comp if len(chains_per_comp[c]) > 1)
print(f"\nGRAPH: nodes {len(nodes)}, directed edges (distinct) {len(edge_set)}, edge traversals {sum(edges.values())}, "
      f"edges traversed >1 times {sum(1 for e, c in edges.items() if c > 1)}")
print(f"weakly connected components: {len(comp)}; sizes (top 15): {comp_sizes[:15]}; "
      f"size distribution: {sorted(collections.Counter(comp_sizes).items())}")
print(f"components containing >1 chain: {multi_chain_comps}; components that are exactly one chain's path: "
      f"{sum(1 for c in comp if len(chains_per_comp[c]) == 1)}")
print(f"nodes entered by >1 chain: {sum(1 for n in nodes if len(chains_of_node[n]) > 1)}; "
      f"by >1 worker: {sum(1 for n in nodes if len(workers_of_node[n]) > 1)}; "
      f"by >1 arm: {sum(1 for n in nodes if len({w[0] for w in workers_of_node[n]}) > 1)}")
print("total degree distribution (distinct edges, undirected count):",
      sorted(collections.Counter(deg[n] for n in nodes).items()))
print("out-degree distribution:", sorted(collections.Counter(outdeg[n] for n in nodes).items()))
print("in-degree distribution:", sorted(collections.Counter(indeg[n] for n in nodes).items()))
# simple-path test: component is a path iff edges = nodes-1 and max degree <= 2
paths = 0
for c, s in comp.items():
    es = [e for e in edge_set if e[0] in s]
    if len(es) == len(s) - 1 and all(deg[n] <= 2 for n in s):
        paths += 1
print(f"components that are simple paths (nodes-1 edges, degree <= 2): {paths} of {len(comp)}")
shared = [(n, sorted(chains_of_node[n])) for n in nodes if len(chains_of_node[n]) > 1]
for n, cks in shared:
    print(f"  shared node {n if isinstance(n, str) else hex(n)} size={node_size(n)} chains={cks}")

# ------------------------------------------------------------------ hop statistics
print("\nHOPS")
exc_samples = [h["exc_samples"] for h in hops]
print("89 excursion length in samples (89 records between consecutive 88 nodes):",
      sorted(collections.Counter(exc_samples).items()))
print("  zero-sample excursions (88 -> 88 with no 89 seen):", sum(1 for x in exc_samples if x == 0), "of", len(hops))
exw = [h["exc_wall"] for h in hops]
print("excursion wall seconds between last 88 sample and next 88 sample:", med(exw))
print("  same, only hops with >= 1 sampled 89:", med([h["exc_wall"] for h in hops if h["exc_samples"] > 0]))
exs = [h["exc_steps"] for h in hops if h["exc_steps"] is not None]
print("excursion in steps (upper bound, includes time on both plateaus inside the 30 s windows):", med(exs))
print("  same, only hops with >= 1 sampled 89:", med([h["exc_steps"] for h in hops if h["exc_steps"] is not None and h["exc_samples"] > 0]))
print("Jaccard distance across a hop, helpers only, mod rotation:", med([h["jac_h"] for h in hops], "{:.3f}"))
print("Jaccard distance across a hop, all values incl. outputs:", med([h["jac_all"] for h in hops], "{:.3f}"))
print("  helpers, hops with >= 1 sampled 89:", med([h["jac_h"] for h in hops if h["exc_samples"] > 0], "{:.3f}"))
print("  helpers, hops with 0 sampled 89:", med([h["jac_h"] for h in hops if h["exc_samples"] == 0], "{:.3f}"))
for arm in "ABC":
    print(f"  arm {arm}: hops {sum(1 for h in hops if h['chain'][0] == arm)}; exc samples "
          f"{med([h['exc_samples'] for h in hops if h['chain'][0] == arm])}; jac_h "
          f"{med([h['jac_h'] for h in hops if h['chain'][0] == arm], '{:.3f}')}")
# cycles / returns
returns_same = sum(v["returns"] for vs in visits.values() for v in vs)
ret_exc = [x for vs in visits.values() for v in vs for x in v["return_exc"]]
revisits = sum(1 for h in hops if h["revisit"])
print(f"returns to the SAME node after a sampled 89 excursion (node unchanged): {returns_same}; their excursion lengths in samples: "
      f"{sorted(collections.Counter(ret_exc).items())}")
print(f"hops landing on a node the chain visited earlier (cycle, length >= 2): {revisits} of {len(hops)}")
revisited_nodes = {v["node"] for vs in visits.values() for v in vs if v["returns"] > 0}
revisited_nodes |= {h["v"] for h in hops if h["revisit"]}
revisited_nodes |= {n for n in nodes if len(chains_of_node[n]) > 1}
print(f"nodes ever revisited (same-node return, in-chain cycle, or entered by another chain): {len(revisited_nodes)} of {len(nodes)}")
# per-chain rates
print("\nPER CHAIN")
rows = []
for ck, vs in sorted(visits.items()):
    rs = chains[ck]
    first88 = vs[0]["first"]
    last = rs[-1]
    span = last["wall"] - first88["wall"]
    distinct = len({v["node"] for v in vs})
    rows.append((ck, len(vs), distinct, span, distinct / (span / 3600) if span > 600 else None))
for arm in "ABC":
    rr = [r for r in rows if r[0][0] == arm]
    print(f"arm {arm}: chains {len(rr)}; visits per chain {med([r[1] for r in rr])}; distinct nodes per chain "
          f"{med([r[2] for r in rr])}; span s {med([r[3] for r in rr])}; distinct nodes per hour (chains with span > 600 s) "
          f"{med([r[4] for r in rr if r[4] is not None], '{:.1f}')}")
print("all arms: distinct nodes per hour (span > 600 s):", med([r[4] for r in rows if r[4] is not None], "{:.1f}"))
tot_nodes = sum(r[2] for r in rows)
tot_h = sum(r[3] for r in rows) / 3600
print(f"pooled: {tot_nodes} node-visits over {tot_h:.1f} chain-hours at/after first 88 = {tot_nodes / tot_h:.1f} per hour")

# ------------------------------------------------------------------ landings
print("\nLANDINGS")
first_nodes, later_nodes = [], []
first_depth, later_depth = [], []
for ck, vs in visits.items():
    for i, v in enumerate(vs):
        fi = fan_info.get(v["first"]["hash"])
        d = fi["depth"] if fi else None
        (first_nodes if i == 0 else later_nodes).append(v["node"])
        if d is not None:
            (first_depth if i == 0 else later_depth).append(d)


def size_summary(ns):
    sz = [node_size(n) for n in ns]
    known = [s for s in sz if s is not None]
    cat = collections.Counter()
    for s in known:
        cat["1"] += s == 1
        cat["<=1e3"] += 1 < s <= 1000
        cat["1e3-1e4"] += 1000 < s <= 10000
        cat["1e4-1e5"] += 10000 < s <= 100000
        cat[">1e5"] += s > 100000
    return (f"n={len(ns)} catalogued={len(known)} unknown={len(ns) - len(known)}; size {med(known)}; "
            f"bins {dict(cat)}")


print("first 88 node per chain:", size_summary(first_nodes))
print("later 88 nodes:         ", size_summary(later_nodes))
print("depth of first 88 state per chain:", sorted(collections.Counter(first_depth).items()))
print("depth of later 88 states (first sample of each later visit):", sorted(collections.Counter(later_depth).items()))
fn = set(first_nodes)
print(f"distinct first nodes {len(fn)} of {len(first_nodes)} chains; first nodes later entered by another chain: "
      f"{sum(1 for n in fn if len(chains_of_node[n]) > 1)}; first nodes revisited by the same chain: "
      f"{sum(1 for ck, vs in visits.items() if vs[0]['node'] in {v['node'] for v in vs[1:]} or vs[0]['returns'] > 0)}")
# depth along the chain
for arm in "ABC":
    fd = [d for ck, vs in visits.items() if ck[0] == arm for i, v in enumerate(vs) if i == 0
          for d in [fan_info[v["first"]["hash"]]["depth"]] if fan_info.get(v["first"]["hash"])]
    ld = [d for ck, vs in visits.items() if ck[0] == arm for i, v in enumerate(vs) if i > 0
          for d in [fan_info[v["first"]["hash"]]["depth"]] if fan_info.get(v["first"]["hash"])]
    print(f"  arm {arm}: first depth {med(fd)}; later depth {med(ld)}")

# per-chain listing
print("\nCHAIN LISTING (arm worker chain: visits, distinct, hops with sampled 89 / without, returns, revisits)")
for ck, vs in sorted(visits.items()):
    hs = [h for h in hops if h["chain"] == ck]
    print(f"  {ck[0]} {ck[1]} c{ck[2]}: visits {len(vs)} distinct {len({v['node'] for v in vs})} "
          f"hops89 {sum(1 for h in hs if h['exc_samples'] > 0)} hops0 {sum(1 for h in hs if h['exc_samples'] == 0)} "
          f"returns {sum(v['returns'] for v in vs)} revisits {sum(1 for h in hs if h['revisit'])} "
          f"sizes {[node_size(v['node']) for v in vs][:10]}")

json.dump({"nodes": [str(n) for n in nodes], "edges": [[str(u), str(v), c] for (u, v), c in edges.items()],
           "hops": [{k: (str(v) if k in ("u", "v") else (list(v) if k == "chain" else v)) for k, v in h.items()} for h in hops],
           "fan": fan_info, "comp_sizes": comp_sizes},
          open(os.path.join(OUT, "graph_data.json"), "w"))
print("wrote graph_data.json")
