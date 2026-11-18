"""Structural features of a circuit, from its file alone (cheap enough to score search candidates).

``features(d, lib_models)`` -> dict of numbers.  Groups:

  counts      A, AD, G, GD, XOR, XNOR, NOT
  fanout      mean, max, sd, number of signals with fanout >= 3 / >= 5, sum of squares, the
              inputs' total and max fanout (the load the input drivers see)
  depth       outputs' mean depth and sd, outputs at the maximum depth, gates with zero slack
              (on a longest path), mean slack (ALAP - ASAP level), operand depth imbalance
  sharing     fraction of gates with fanout > 1
  reconv      gates whose two operands have overlapping fan-in cones; mean overlap / cone size
  sta_<lib>   a load-aware longest path: each gate costs intrinsic + slope x load, with intrinsic
              and slope of its 2-input cell fitted on the Liberty delay tables (lib_models), load
              = input capacitance of its fanout cells (+ the output load); ``sta_crit_<lib>`` the
              number of gates on that path
  area_<lib>  sum of the 2-input cells' areas (the preserve flow's area, exactly)
  pwr_<lib>   zero-delay switching estimate: sum over nets of toggle probability x load
              capacitance (toggle probability 2p(1-p), p from the truth table, 1/2 for linear maps)
"""
from __future__ import annotations

import math
import re
import statistics as st

from hwbench import verilog as V

OUT_LOAD_FF = {'nangate45': 3.898, 'sky130hd': 5.0}


def _nums(s):
    return [float(x) for x in re.findall(r'-?[\d.]+(?:e-?\d+)?', s)]


def lib_models(platform, lib_text):
    """For each of the platform's 2-input cells: (area, input cap fF, intrinsic ns, slope ns/fF),
    from the cell_rise/cell_fall tables at the table's second input-transition index, fitted
    linearly over the first four load points and averaged over arcs and edges."""
    unit = 1e3 if 'pf' in re.search(r'capacitive_load_unit\s*\(([^)]*)\)', lib_text).group(1).lower() \
        else 1.0
    models = {}
    for op, (cell, *pins) in platform.gate_cells.items():
        m0 = re.search(r'\bcell\s*\(\s*"?%s"?\s*\)\s*\{' % re.escape(cell), lib_text)
        i = j = m0.end()
        level = 1
        while level:
            level += {'{': 1, '}': -1}.get(lib_text[j], 0)
            j += 1
        body = lib_text[i:j]
        area = float(re.search(r'area\s*:\s*([\d.]+)', body).group(1))
        caps = [float(x) for x in re.findall(r'\bcapacitance\s*:\s*([\d.]+)', body)][:len(pins) - 1]
        ints, slopes = [], []
        for m in re.finditer(r'cell_(?:rise|fall)\s*\([^)]*\)\s*\{(.*?)\}', body, re.S):
            g = m.group(1)
            i1 = _nums(re.search(r'index_1\s*\(([^)]*)\)', g).group(1))
            i2 = [x * unit for x in _nums(re.search(r'index_2\s*\(([^)]*)\)', g).group(1))]
            vals = _nums(re.search(r'values\s*\((.*)\)', g, re.S).group(1))
            row = vals[len(i2) * 1:len(i2) * 2] if len(i1) > 1 else vals[:len(i2)]
            xs, ys = i2[:4], row[:4]
            mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
            b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
            slopes.append(b)
            ints.append(my - b * mx)
        models[op] = (area, sum(caps) / len(caps) * unit, sum(ints) / len(ints),
                      sum(slopes) / len(slopes))
    return models


def features(d, models_by_lib):
    gates = [(op, o, a) for op, o, a in V.simplified_gates(d)]
    alias = {}
    for op, o, a in gates:
        if op == 'BUF':
            alias[o] = a[0]

    def r(w):
        while w in alias:
            w = alias[w]
        return w

    consts = {o: op[-1] for op, o, a in gates if op.startswith('CONST')}
    for o, v in consts.items():
        alias[o] = v                      # a constant gate is the constant
    real = [(op, o, [r(x) for x in a]) for op, o, a in gates if op in ('AND', 'XOR', 'XNOR', 'NOT')]
    ins = list(d.circuit.inputs)
    outs = [r(w) for w in d.circuit.outputs]
    fan = {w: 0 for w in ins + ['0', '1']}
    users = {w: [] for w in ins + ['0', '1']}
    depth = {w: 0 for w in ins + ['0', '1']}
    for op, o, a in real:
        fan[o] = 0
        users[o] = []
        for x in a:
            if x in fan:
                fan[x] += 1
                users[x].append(op)
        depth[o] = 1 + max(depth.get(x, 0) for x in a)
    for w in outs:
        if w in fan:
            fan[w] += 1
    gd = max(depth[w] for w in outs)
    # ALAP levels: the latest level each gate could take without exceeding gd
    succ = {}
    for op, o, a in real:
        for x in a:
            succ.setdefault(x, []).append(o)
    alap = {}
    for op, o, a in reversed(real):
        cand = [alap[s] - 1 for s in succ.get(o, [])]
        if o in outs or not cand:
            cand.append(gd)
        alap[o] = min(cand)
    slack = [alap[o] - depth[o] for _, o, _ in real]
    fo = [fan[o] for _, o, _ in real]
    allfo = list(fan.values())
    # reconvergence: fan-in cones as bitsets over gates
    idx = {o: k for k, (_, o, _) in enumerate(real)}
    cone = {w: 0 for w in ins}
    reconv = 0
    overlaps = []
    for k, (op, o, a) in enumerate(real):
        cs = [cone.get(x, 0) | ((1 << idx[x]) if x in idx else 0) for x in a]
        if len(cs) == 2:
            ov = bin(cs[0] & cs[1]).count('1')
            un = bin(cs[0] | cs[1]).count('1')
            if ov:
                reconv += 1
            overlaps.append(ov / un if un else 0.0)
        cone[o] = cs[0] | (cs[1] if len(cs) > 1 else 0)
    imb = [abs(depth.get(a[0], 0) - depth.get(a[1], 0)) for op, o, a in real if len(a) == 2]
    od = [depth[w] for w in outs]
    f = {'A': d.metrics['A'], 'AD': d.metrics['AD'], 'G': d.metrics['G'], 'GD': d.metrics['GD'],
         'XOR': sum(op == 'XOR' for op, _, _ in real), 'XNOR': sum(op == 'XNOR' for op, _, _ in real),
         'NOT': sum(op == 'NOT' for op, _, _ in real),
         'fo_mean': st.mean(fo), 'fo_max': max(fo), 'fo_sd': st.pstdev(fo),
         'fo_ge3': sum(x >= 3 for x in allfo), 'fo_ge5': sum(x >= 5 for x in allfo),
         'fo_sumsq': sum(x * x for x in allfo),
         'in_fo_sum': sum(fan[w] for w in ins), 'in_fo_max': max(fan[w] for w in ins),
         'out_depth_mean': st.mean(od), 'out_depth_sd': st.pstdev(od),
         'out_at_max': sum(x == gd for x in od),
         'zero_slack': sum(s == 0 for s in slack), 'slack_mean': st.mean(slack),
         'imbalance_mean': st.mean(imb) if imb else 0.0,
         'shared_frac': sum(x > 1 for x in fo) / len(fo),
         'reconv_frac': reconv / len(real), 'overlap_mean': st.mean(overlaps) if overlaps else 0.0}
    # exact signal probabilities (zero-delay toggle 2p(1-p))
    if d.kind == 'boolean':
        from boolcirc import truth
        n = d.n_in
        base = truth.input_tables(n)
        bits = d.in_bit
        tables = {w: base[bits[i]] for i, w in enumerate(ins)}
        ones = (1 << (1 << n)) - 1
        tables['0'], tables['1'] = 0, ones
        for op, o, a in real:
            t = [tables[x] for x in a]
            tables[o] = (t[0] & t[1]) if op == 'AND' else (t[0] ^ t[1]) if op == 'XOR' else \
                (ones ^ t[0] ^ t[1]) if op == 'XNOR' else (ones ^ t[0])
        tog = {w: 2 * (bin(t).count('1') / (1 << n)) * (1 - bin(t).count('1') / (1 << n))
               for w, t in tables.items()}
    else:
        tog = {w: 0.5 for w in fan}
    for lib, models in models_by_lib.items():
        load = {}
        for w in fan:
            c = sum(models[op][1] for op in users[w]) + (OUT_LOAD_FF[lib] * outs.count(w))
            load[w] = c
        arr = {w: 0.0 for w in ins + ['0', '1']}
        cnt = {w: 0 for w in ins + ['0', '1']}
        for op, o, a in real:
            _, _, t0, k = models[op]
            src = max(a, key=lambda x: arr.get(x, 0.0))
            arr[o] = arr.get(src, 0.0) + t0 + k * load[o]
            cnt[o] = cnt.get(src, 0) + 1
        crit = max(outs, key=lambda w: arr[w])
        f['sta_' + lib] = arr[crit]
        f['sta_crit_' + lib] = cnt[crit]
        f['area_' + lib] = sum(models[op][0] for op, _, _ in real)
        f['pwr_' + lib] = sum(tog[w] * load[w] for w in fan)
    return f


def finite(f):
    return {k: (v if isinstance(v, (int, float)) and math.isfinite(v) else 0.0) for k, v in f.items()}
