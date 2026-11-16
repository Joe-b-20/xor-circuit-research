"""Bounded generic ports of historical constructor and first-unlock families."""
from __future__ import annotations
from collections import Counter
from itertools import combinations
import time
from .common import validate_target, legacy_extract


def constructor(engine, target, cap, rng, cfg, saved, stop):
    from .vendor_v2.deadline_search import _emit
    n, targets = validate_target(target)
    inputs = [1 << i for i in range(n)]
    if engine == 'legacy-constructor':
        recipes = {}
        order = list(dict.fromkeys(targets));rng.shuffle(order)
        for t in order:
            items = [m for m in inputs if m & t]
            rng.shuffle(items)
            while len(items) > 1:
                if stop():
                    return None, {'operator':'balanced-constructor','stopped':True}
                following = []
                for i in range(0,len(items)-1,2):
                    a,b = items[i:i+2]
                    recipes.setdefault(a^b,(a,b));following.append(a^b)
                if len(items)%2:following.append(items[-1])
                rng.shuffle(following);items=following
        return _emit(recipes,targets,inputs,cap), {'operator':'balanced-constructor'}
    # All incremental constructors retain incomplete construction state across
    # chunks; nothing is emitted until every output has a real gate program.
    gates = list(saved.get('construction_gates',[]))
    values = inputs[:]
    depths = [0]*n
    for a,b in gates:
        values.append(values[a]^values[b]);depths.append(1+max(depths[a],depths[b]))
    index = {m:i for i,m in enumerate(values)}
    if engine == 'legacy-paar':
        rows = [set(r) for r in saved.get('rows',[[i for i in range(n) if t & (1 << i)] for t in targets])]
        counts = Counter(p for row in rows for p in combinations(sorted(row),2))
        if not counts:
            result = _emit({values[n+i]:(values[a],values[b]) for i,(a,b) in enumerate(gates)},targets,inputs,cap)
            saved.clear()
            return result, {'operator':'paar-frequency','completed':True}
        legal = [p for p in counts if cap is None or 1+max(depths[p[0]],depths[p[1]]) <= cap]
        if not legal:
            saved.clear();return None, {'operator':'paar-frequency','depth_blocked':True}
        maximum = max(counts[p] for p in legal)
        pair = rng.choice(sorted(p for p in legal if counts[p]==maximum))
        a,b=pair;m=values[a]^values[b]
        if m not in index:
            index[m]=len(values);gates.append([a,b])
        z=index[m]
        for row in rows:
            if a in row and b in row:
                row.difference_update((a,b));row.symmetric_difference_update((z,))
        saved.update(construction_gates=gates,rows=[sorted(r) for r in rows])
        return None, {'operator':'paar-frequency','completed':False,'contracted_frequency':maximum,'construction_gates':len(gates)}
    # BP variants differ in their actual distance oracle: historical recursive
    # weight descent vs inverse exact tiers plus a constructive upper bound.
    unfinished = [t for t in dict.fromkeys(targets) if t not in index]
    if not unfinished:
        result = _emit({values[n+i]:(values[a],values[b]) for i,(a,b) in enumerate(gates)},targets,inputs,cap)
        saved.clear()
        return result, {'operator':engine,'completed':True}
    if len(gates) >= cfg['constructor_gate_limit']:
        saved.clear();return None, {'operator':engine,'restart':True}
    pairs = {}
    for a,b in combinations(range(len(values)),2):
        if stop():
            return None, {'operator':engine,'stopped':True}
        m=values[a]^values[b]
        if m and m not in index and (cap is None or 1+max(depths[a],depths[b]) <= cap):
            pairs.setdefault(m,(a,b))
    if not pairs:
        saved.clear();return None, {'operator':engine,'restart':True}
    candidate_masks=sorted(pairs)
    if len(candidate_masks)>cfg['constructor_samples']:
        candidate_masks=rng.sample(candidate_masks,cfg['constructor_samples'])
    candidate_masks=sorted(set(candidate_masks)|{t for t in unfinished if t in pairs})
    helper=values[n:]
    nodes=[0]
    def descent(v,best,extra):
        best=min(best,v.bit_count())
        if best<=1:return best
        for h in extra:
            nodes[0]+=1
            if nodes[0]>=cfg['distance_nodes'] or stop():return best
            r=v^h
            if r.bit_count()<=v.bit_count()-2:
                best=min(best,1+descent(r,best-1,extra))
        return best
    pair_values={a^b for a,b in combinations(values,2)} if engine=='inverse-bp' else set()
    def distance(v):
        if not v:return 0
        if v in index:return 1
        if v in pair_values:return 2
        if cfg['exact_tiers']>=3:
            for a in values:
                if stop():break
                if (v^a) in pair_values:return 3
        if cfg['exact_tiers']>=4:
            for p in sorted(pair_values):
                if stop():break
                if (v^p) in pair_values:return 4
        # Always constructive bounds, never exact-distance claims above tiers.
        if cfg['distance_fallback']==0:return None
        bound=v.bit_count()
        if cfg['distance_fallback']==2:
            bound=min([bound]+[1+(v^a).bit_count() for a in values])
        return bound
    old=saved.get('distances',{str(t):t.bit_count() for t in targets})
    best=None
    for m in candidate_masks:
        if stop():break
        if engine=='legacy-bp':
            ds=[descent(t,t.bit_count(),helper+[m]) for t in unfinished]
        else:
            ds=[]
            for t in unfinished:
                d=distance(t^m)
                ds.append(min(old.get(str(t),t.bit_count()),(d+1) if d is not None else old.get(str(t),t.bit_count())))
        norm=sum(d*d for d in ds)
        key=(sum(ds),-norm if cfg['norm']=='max' else norm if cfg['norm']=='min' else 0,rng.random())
        if best is None or key<best[0]:best=(key,m,ds)
    if best is None:
        return None, {'operator':engine,'stopped':True}
    _,m,ds=best;gates.append(list(pairs[m]))
    old.update({str(t):d for t,d in zip(unfinished,ds)})
    saved.update(construction_gates=gates,distances=old)
    return None, {'operator':engine,'completed':False,'construction_gates':len(gates),
                  'distance_nodes':nodes[0],'distance_is_upper_bound':True}


def window(current,target,cap,rng,cfg,stop):
    n,rows=validate_target(target)
    inputs={1 << i for i in range(n)}
    helpers=sorted(current['masks']-set(rows))
    if len(helpers)<2:return None,{'operator':'first-unlock','windows':0}
    victims=set(rng.sample(helpers,min(cfg['window_size'],len(helpers))))
    kept=set(current['masks'])-victims
    tested=0
    def closure(bank):
        available=set(inputs);locked=set(bank)-available
        changed=True
        while changed and not stop():
            changed=False
            for m in sorted(locked):
                if stop():return available,locked
                if any((m^a) in available for a in sorted(available)):
                    available.add(m);locked.remove(m);changed=True
        return available,locked
    def repairs(bank,budget):
        nonlocal tested
        if stop() or tested>=cfg['window_candidates']:return None
        available,locked=closure(bank)
        if set(rows)<=available:
            return legacy_extract(bank,target,cap,rng,{},stop)
        if budget==0:return None
        pair_sums={a^b for a,b in combinations(sorted(available),2)}-available
        candidates=set()
        for r in sorted(locked):
            if stop():return None
            candidates.update((r^a) for a in sorted(available) if (r^a) in pair_sums)
        candidates=sorted(candidates);rng.shuffle(candidates)
        for m in candidates:
            if stop() or tested>=cfg['window_candidates']:break
            tested+=1
            result=repairs(set(bank)|{m},budget-1)
            if result is not None and len(result['gates'])<len(current['gates']):return result
        return None
    result=repairs(kept,len(victims)-1)
    return result,{'operator':'first-unlock','windows':1,'candidates':tested,
                   'search_exhaustive':False,'scope':'selected window; anchored bounded search'}
