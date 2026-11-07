"""Closure deficiency of a target set (exact, small e): over n inputs, targets T (nonzero, nonbasis,
distinct), the least number e of NON-target values a circuit must create so that every target is the
XOR of two earlier values.  Then C(T) = |T| + e exactly (a circuit with |T| + e gates has exactly e
non-target gate values, WLOG distinct and nonzero).  We search e = 0, 1, 2, ... up to e_max with
greedy target closure (sound: adding a target costs 1 whenever it is added and only enlarges the
available set) and extras restricted to XORs of two available values (every circuit value is).

usage: python3 closure_dfs.py "6,7" 3        -> deficiency of the TRANSPOSED pair map (4k inputs)
       python3 closure_dfs.py "0" 3 fwd      -> forward map of group 0
Prints one json line; appends to closure.jsonl.
"""
import json
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from submaps import submatrix

HERE = os.path.dirname(os.path.abspath(__file__))


def close_targets(avail, todo):
    """Greedy: add every target that is a XOR of two available values, to a fixpoint."""
    avail = set(avail); todo = set(todo)
    changed = True
    while changed:
        changed = False
        for t in list(todo):
            for a in avail:
                if (a ^ t) in avail and (a ^ t) != a:
                    avail.add(t); todo.discard(t); changed = True
                    break
    return frozenset(avail), frozenset(todo)


def deficiency(n, targets, e_max):
    inputs = frozenset(1 << j for j in range(n))
    tset = frozenset(targets)
    start_av, start_todo = close_targets(inputs, tset)
    if not start_todo:
        return 0, 1
    nodes = 0
    for e in range(1, e_max + 1):
        seen = set()
        stack = [(start_av, start_todo, 0)]
        while stack:
            av, todo, used = stack.pop()
            nodes += 1
            if not todo:
                return e, nodes
            if used == e:
                continue
            # candidate extras: XOR of two available values, not available, not a target
            avl = sorted(av)
            cands = set()
            for i in range(len(avl)):
                for j in range(i + 1, len(avl)):
                    u = avl[i] ^ avl[j]
                    if u and u not in av and u not in tset:
                        cands.add(u)
            # pruning: with r = e - used extras left, need at least one target to become closable;
            # a target t becomes closable only if some u in cands satisfies u ^ t in av (or two extras combine)
            for u in cands:
                av2, todo2 = close_targets(av | {u}, todo)
                key = (av2, used + 1)
                if key in seen:
                    continue
                seen.add(key)
                if used + 1 == e and todo2:
                    continue
                stack.append((av2, todo2, used + 1))
    return None, nodes


if __name__ == "__main__":
    K = [int(x) for x in sys.argv[1].split(",")]
    e_max = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    mode = sys.argv[3] if len(sys.argv) > 3 else "transposed"
    sup, fwd, cols = submatrix(K)
    n = len(sup); k4 = 4 * len(K)
    t0 = time.time()
    if mode == "transposed":
        T = sorted(set(c for c in cols if bin(c).count("1") >= 2))
        e, nodes = deficiency(k4, T, e_max)
        res = {"K": K, "mode": mode, "n_inputs": k4, "n_targets": len(T), "e": e, "e_max": e_max, "nodes": nodes,
               "secs": round(time.time() - t0, 1)}
        if e is not None:
            res["C_transposed"] = len(T) + e
            res["C_forward_exact"] = len(T) + e + n - k4
        else:
            res["C_transposed_lb"] = len(T) + e_max + 1
            res["C_forward_lb"] = len(T) + e_max + 1 + n - k4
    else:
        T = sorted(set(fwd))
        e, nodes = deficiency(n, T, e_max)
        res = {"K": K, "mode": mode, "n_inputs": n, "n_targets": len(T), "e": e, "e_max": e_max, "nodes": nodes,
               "secs": round(time.time() - t0, 1)}
        if e is not None:
            res["C_forward_exact"] = len(T) + e
        else:
            res["C_forward_lb"] = len(T) + e_max + 1
    print(json.dumps(res))
    open(os.path.join(HERE, "closure.jsonl"), "a").write(json.dumps(res) + "\n")
