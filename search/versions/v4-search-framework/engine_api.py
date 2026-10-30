"""Resumable generic adapters for archived XOR search families.

Both ``from search import engine_api`` and ``import engine_api`` from the
search directory are supported. Frozen originals are never modified/imported
through mutable global target settings. See engines/README.md for lineage.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
import random
import time
try:
    from .engines import common
except ImportError:
    from engines import common

_ENGINES = ('legacy-constructor', 'legacy-paar', 'legacy-bp', 'inverse-bp', 'legacy-window',
            'legacy-walk', 'legacy-lns', 'legacy-anneal3',
            'v2-walk', 'v2-lns', 'v2-anneal3', 'v2-translate', 'v2-cores',
            'v3-component', 'v3-interface', 'v3-backward', 'v3-pairbank3')


def available_engines():
    return list(_ENGINES)


def _module(name):
    import importlib
    prefix = (__package__ + '.engines.') if __package__ else 'engines.'
    return importlib.import_module(prefix + name)


def engine_applicability(target, engine, depth_cap=None, objective="gates", gate_limit=None):
    if engine not in _ENGINES:
        raise ValueError('unknown engine: ' + str(engine))
    n, rows = common.validate_target(target)
    _validate_objective(objective, gate_limit)
    if n > 32 and (engine.endswith('anneal3') or engine == 'v3-pairbank3'):
        return {'applicable': False, 'reason': 'depth-three catalogues are excluded above 32 inputs to bound combinatorial setup'}
    if depth_cap is not None and (type(depth_cap) is not int or depth_cap < 0):
        raise ValueError('depth_cap must be nonnegative or None')
    minimum = max((m.bit_count()-1).bit_length() for m in rows)
    if depth_cap is not None and depth_cap < minimum:
        return {'applicable': False, 'reason': 'row support exceeds the fan-in-two depth cap'}
    if engine.endswith('anneal3'):
        if any(m.bit_count() > 8 for m in rows):
            return {'applicable': False, 'reason': 'partition model requires every row support <= 8'}
        if depth_cap is not None and depth_cap < 3:
            return {'applicable': False, 'reason': 'partition annealer is scoped to depth three; use walk/LNS below depth three'}
    if engine == 'v3-pairbank3':
        if any(m.bit_count() not in (5, 7) for m in rows):
            return {'applicable': False, 'reason': 'archived pair-bank model requires row weights five or seven'}
        if depth_cap is not None and depth_cap < 3:
            return {'applicable': False, 'reason': 'pair-bank model requires a depth cap of at least three'}
    return {'applicable': True, 'reason': 'generic linear target; no MixColumns symmetry or field assumption'}


def _merge(base, supplied):
    if not isinstance(supplied, dict) or set(supplied) - set(base):
        raise ValueError('unknown or malformed engine knobs: ' + str(set(supplied) - set(base) if isinstance(supplied, dict) else supplied))
    for key, value in supplied.items():
        if isinstance(base[key], dict):
            _merge(base[key], value)
        else:
            base[key] = copy.deepcopy(value)
    return base


def effective_knobs(engine, overrides=None):
    """Fully resolved controls used by this adapter (not archived fleet defaults)."""
    if engine not in _ENGINES:
        raise ValueError('unknown engine: ' + str(engine))
    cfg = {'max_iterations': None, 'proposal_seconds': .04,
           'temperature': 1.2, 'cooling': .9997, 'max_uphill_gates': 4,
           'snapback': 8, 'depth_rebuild_probability': .35,
           'depth_tighten_probability': .65, 'depth_temperature': .2, 'max_uphill_depth': 1}
    if engine in ('legacy-constructor','legacy-paar'):
        pass
    elif engine in ('legacy-bp','inverse-bp'):
        cfg.update(constructor_gate_limit=1024, constructor_samples=30, norm='max')
        if engine == 'legacy-bp':
            cfg['distance_nodes'] = 2000
        else:
            cfg.update(exact_tiers=3, distance_fallback=2)
    elif engine == 'legacy-window':
        cfg.update(window_size=2, window_candidates=128)
    elif engine.endswith(('walk', 'lns')):
        cfg.update(destroy_max=4, cone_probability=.45, injection_samples=24,
                   repair_candidates=16, expansion_candidates=16,
                   pool_probability=.5, pool_limit=2048, bank_limit=1024,
                   victim_cost=3)
        if engine.startswith('v2-'):
            cfg.update(beam_width=8, deadline_states=800)
    elif engine.endswith('anneal3'):
        cfg.update(constructor_nodes=1500)
    elif engine in ('v2-translate', 'v2-cores'):
        cfg.update(max_parent_edges=6, root_trials=8,
                   constructor_seconds=.03, max_roots=4)
    elif engine.startswith('v3-') and engine != 'v3-pairbank3':
        module = _module('vendor_v3.advanced_moves')
        cfg['move_knobs'] = copy.deepcopy(module.DEFAULT_KNOBS)
        # This is capped again by remaining wall time for every proposal.
        cfg['move_knobs']['max_seconds'] = cfg['proposal_seconds']
    else:
        cfg.update(selection_sweeps=2, selection_restarts=1,
                   constructor_sweeps=1, mutation_weights={'swap':.5,'add':.25,'remove':.15,'shake':.1},
                   shake_remove=2, shake_add=3, addition_sample=32)
    supplied = copy.deepcopy({} if overrides is None else overrides)
    if not isinstance(supplied,dict):
        raise ValueError('engine knobs must be a dictionary')
    readonly = {key:supplied.pop(key) for key in ('kernel_signature_defaults','kernel_effective_calls','kernel_internal_calls') if key in supplied}
    cfg = _merge(cfg, supplied)
    for key, value in cfg.items():
        if key in ('move_knobs', 'mutation_weights', 'norm'):
            continue
        if key == 'max_iterations' and value is None:
            continue
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError(key + ' must be finite and nonnegative')
        if key not in ('proposal_seconds', 'temperature', 'cooling', 'cone_probability',
                       'pool_probability', 'constructor_seconds', 'depth_rebuild_probability',
                       'depth_tighten_probability', 'depth_temperature') and type(value) is not int:
            raise ValueError(key + ' must be an integer')
    if cfg['depth_temperature'] <= 0:
        raise ValueError('depth_temperature must be positive')
    if cfg['proposal_seconds'] <= 0 or cfg['temperature'] <= 0 or not 0 < cfg['cooling'] <= 1:
        raise ValueError('proposal_seconds/temperature must be positive and cooling in (0,1]')
    for key in ('cone_probability', 'pool_probability', 'depth_rebuild_probability', 'depth_tighten_probability'):
        if key in cfg and cfg[key] > 1:
            raise ValueError(key + ' must be a probability')
    if 'bank_limit' in cfg and (cfg['bank_limit'] < 1 or cfg['pool_limit'] < 1 or cfg['destroy_max'] < 1):
        raise ValueError('bank_limit, pool_limit and destroy_max must be positive')
    if 'norm' in cfg and cfg['norm'] not in ('none','min','max'):
        raise ValueError('norm must be none, min or max')
    if 'exact_tiers' in cfg and cfg['exact_tiers'] not in (2,3,4):
        raise ValueError('exact_tiers must be 2,3 or 4')
    if 'distance_fallback' in cfg and cfg['distance_fallback'] not in (0,1,2):
        raise ValueError('distance_fallback must be 0,1 or 2')
    if 'window_size' in cfg and cfg['window_size'] not in (2,3):
        raise ValueError('window_size must be 2 or 3')
    if 'constructor_samples' in cfg and min(cfg['constructor_samples'],cfg.get('distance_nodes',1),cfg['constructor_gate_limit']) < 1:
        raise ValueError('constructor limits must be positive')
    if 'move_knobs' in cfg:
        # Target-dependent focus validation happens at proposal time.
        _module('vendor_v3.advanced_moves')._configuration(cfg['move_knobs'], cfg['move_knobs'].get('focus_outputs') or ())
    if 'mutation_weights' in cfg:
        if any(type(v) not in (int,float) or not math.isfinite(v) or v < 0 for v in cfg['mutation_weights'].values()) or sum(cfg['mutation_weights'].values()) <= 0:
            raise ValueError('mutation weights must be finite, nonnegative and not all zero')
        if cfg['addition_sample'] < 1:
            raise ValueError('addition_sample must be positive')
    cfg.update(_kernel_metadata(engine,cfg))
    for key,value in readonly.items():
        if json.loads(json.dumps(value)) != json.loads(json.dumps(cfg[key])):
            raise ValueError(key + ' is derived read-only metadata')
    return json.loads(json.dumps(cfg))


def _kernel_metadata(engine,cfg):
    """Literal signature defaults plus actual adapter overrides; no hidden AES inputs."""
    import inspect
    modules = {}
    calls = {}
    if engine in ('v2-walk','v2-lns'):
        modules['vendor_v2.deadline_search'] = ('reconstruct','earliest_witness')
        calls['reconstruct'] = {'inputs':'target singleton masks', 'cap':'depth_cap argument',
            'preferred':'current/victim/injected value costs', 'rng':'restored RNG',
            'max_seconds':'min(proposal_seconds, remaining chunk seconds)',
            'beam_width':cfg['beam_width'],'max_states':cfg['deadline_states'],'fallback_masks':None,
            'objective':'run_chunk objective argument','gate_limit':'hard publication gate_limit'}
    elif engine in ('v2-translate','v2-cores'):
        modules['vendor_v2.structured_search'] = ('propose','_finish','_raw_splits','_core_moves')
        modules['vendor_v2.deadline_search'] = ('reconstruct','earliest_witness','optimize_depth3')
        calls['structured.propose'] = {'targets':'target rows','inputs':'target singleton masks',
            'cap':'depth_cap argument','rng':'restored RNG',
            'max_seconds':'min(proposal_seconds, remaining chunk seconds)',
            'max_parent_edges':cfg['max_parent_edges'],'root_trials':cfg['root_trials'],
            'constructor_budget':cfg['constructor_seconds'],'max_roots':cfg['max_roots'],
            'kind':'translate' if engine=='v2-translate' else 'cores','stats':'fresh proposal metrics',
            'objective':'run_chunk objective argument','gate_limit':'hard publication gate_limit',
            'source_depth_cap':'outer depth_cap, kept separate from tighter proposal cap'}
    elif engine == 'v2-anneal3':
        modules['vendor_v2.deadline_search'] = ('optimize_depth3',)
        calls['optimize_depth3'] = {'parents':'current partition parent masks','existing_pairs':[],
            'rng':'restored RNG','max_seconds':'min(proposal_seconds, remaining chunk seconds)',
            'max_nodes':cfg['constructor_nodes']}
    elif engine == 'v3-pairbank3':
        modules['vendor_v3.pair_bank_search'] = ('solve_pair_bank','_masks','all_input_pairs','enumerate_output_splits','_restore_assignment','_integer','_seconds','_Selection.extension')
        calls['solve_pair_bank'] = {'pair_bank':'resumed/mutated depth-one pair bank','targets':'target rows',
            'n_inputs':'target input_count','rng':'restored RNG','incumbent':None,
            'max_seconds':'min(proposal_seconds, remaining chunk seconds)',
            'sweeps':cfg['selection_sweeps'],'restarts':cfg['selection_restarts'],
            'constructor_sweeps':cfg['constructor_sweeps'],'focus_outputs':[],'obstructions':[],
            'should_stop':'shared deadline and caller stop hook'}
    elif engine.startswith('v3-'):
        modules['vendor_v3.advanced_moves'] = ('propose','verify_steps','_Constructor.ensure')
        modules['vendor_v3.deadline_search'] = ('objective_key',)
        calls['advanced.propose'] = {'kind':{'v3-component':'component_merge','v3-interface':'interface_basis',
            'v3-backward':'backward_package'}[engine],'steps':'current chronological program',
            'targets':'target rows','n_inputs':'target input_count','depth_cap':'depth_cap argument',
            'rng':'restored RNG','knobs':'resolved move_knobs; max_seconds capped by proposal/chunk',
            'should_stop':'shared deadline and caller stop hook',
            'objective':'run_chunk objective argument','gate_limit':'hard publication gate_limit',
            'source_depth_cap':'outer depth_cap or current source depth'}
    modules['vendor_v2.deadline_search'] = tuple(dict.fromkeys(modules.get('vendor_v2.deadline_search',()) + ('reconstruct','objective_key')))
    calls['depth_squeeze.reconstruct'] = {'active_when': 'objective=depth_then_gates',
        'cap':'min(depth_cap, best feasible depth minus one)', 'objective':'run_chunk objective argument',
        'gate_limit':'hard publication gate_limit; over-limit proposals remain possible when no feasible alternative' ,
        'inputs':'target singleton masks','rng':'restored RNG',
        'beam_width':cfg.get('beam_width',8),'max_states':cfg.get('deadline_states',800),
        'max_seconds':'min(proposal_seconds, remaining chunk seconds)',
        'preferred':None,'fallback_masks':None}
    defaults = {}
    internal_calls = {}
    for module,names in modules.items():
        loaded = _module(module)
        for name in names:
            function = loaded
            for component in name.split('.'):
                function = getattr(function,component)
            values = {key:parameter.default for key,parameter in inspect.signature(function).parameters.items()
                      if parameter.default is not inspect.Parameter.empty}
            if values:
                defaults[module+'.'+name] = values
        internal_calls[module] = _internal_calls(module,tuple(names))
    return {'kernel_internal_calls':internal_calls, 'kernel_signature_defaults':json.loads(json.dumps(defaults)),
            'kernel_effective_calls':calls}


def _internal_calls(module,names):
    """Preserve nested effective literal settings/formulas, not just entry knobs."""
    return copy.deepcopy(_cached_internal_calls(module,names))


from functools import lru_cache
@lru_cache(maxsize=32)
def _cached_internal_calls(module,names):
    import ast
    import inspect
    tree=ast.parse(inspect.getsource(_module(module)))
    wanted={name.split('.')[-1] for name in names} | {'reconstruct','earliest_witness','optimize_depth3'}
    sites=[]
    def value(node):
        try:
            literal=ast.literal_eval(node)
            json.dumps(literal,allow_nan=False)
            return {'value':literal}
        except (ValueError,TypeError,SyntaxError):
            return {'expression':ast.unparse(node)}
    for node in ast.walk(tree):
        if not isinstance(node,ast.Call):continue
        name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else None
        if name in wanted:
            sites.append({'function':ast.unparse(node.func),'line':node.lineno,
                          'positional_arguments':[value(arg) for arg in node.args],
                          'keyword_arguments':{arg.arg or '**kwargs':value(arg.value) for arg in node.keywords}})
    return sorted(sites,key=lambda item:item['line'])


def _validate_objective(objective, gate_limit):
    if objective not in ('gates','depth_then_gates'):
        raise ValueError('objective must be gates or depth_then_gates')
    if gate_limit is not None and (type(gate_limit) is not int or gate_limit < 0):
        raise ValueError('gate_limit must be nonnegative or None')


def _binding(target, engine, cap, objective='gates', gate_limit=None):
    value = {'id':target['id'], 'input_count':target['input_count'], 'rows':target['rows'],
             'matrix_sha256':target.get('matrix_sha256'), 'engine':engine, 'depth_cap':cap}
    if objective != 'gates' or gate_limit is not None:
        value.update(objective=objective, gate_limit=gate_limit)
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def _pairbank(current, target, cap, rng, cfg, saved, stop, deadline):
    module = _module('vendor_v3.pair_bank_search')
    n, rows = common.validate_target(target)
    pairs = set(saved.get('pair_bank', ())) or {m for m in current['masks'] if m.bit_count() == 2}
    universe = module.all_input_pairs(n)
    mutation = rng.choices(list(cfg['mutation_weights']),weights=list(cfg['mutation_weights'].values()))[0]
    if mutation in ('remove', 'swap', 'shake') and pairs:
        count = min(len(pairs),cfg['shake_remove'] if mutation == 'shake' else 1)
        pairs.difference_update(rng.sample(sorted(pairs),count))
    if mutation in ('add','swap','shake'):
        count = cfg['shake_add'] if mutation == 'shake' else 1
        pairs.update(rng.sample(universe,min(count,len(universe))))
    result = module.solve_pair_bank(pairs, rows, n_inputs=n, rng=rng,
                                    max_seconds=min(cfg['proposal_seconds'],max(0.,deadline-time.monotonic())),
                                    sweeps=cfg['selection_sweeps'],restarts=cfg['selection_restarts'],
                                    constructor_sweeps=cfg['constructor_sweeps'], should_stop=stop)
    if result is None and not stop():
        # A high-depth starting program need not fit the scoped pair model.
        # A bounded growth step supplies candidates for the next chunk.
        pairs.update(rng.sample(universe,min(cfg['addition_sample'],len(universe))))
    saved['pair_bank'] = sorted(result['pair_bank'] if result else pairs)
    return result, {'operator':'pair-bank-first','mutation':mutation, **(result.get('stats',{}) if result else {})}


def run_chunk(target, engine, gates, *, seed, seconds, depth_cap=None,
              state=None, knobs=None, on_candidate=None, should_stop=None,
              objective="gates", gate_limit=None):
    """Run a bounded chunk and return current trajectory, JSON state and metrics.

    State is bound to engine/ordered target/depth cap/objective/gate limit. It retains the actual
    Python RNG state, current/best programs and algorithm auxiliary state.
    A supplied state restores its trajectory; seed initializes fresh state only.
    Callback signature: on_candidate(gates, note=None, metrics=None) -> bool.
    The callback's acceptance does not govern this engine's exploration.
    """
    start = time.monotonic()
    applicable = engine_applicability(target,engine,depth_cap,objective,gate_limit)
    if not applicable['applicable']:
        raise ValueError(engine + ': ' + applicable['reason'])
    if type(seed) is not int or type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds < 0:
        raise ValueError('seed must be integer; seconds must be finite and nonnegative')
    cfg = effective_knobs(engine,knobs)
    binding = _binding(target,engine,depth_cap,objective,gate_limit)
    saved = copy.deepcopy(state) if state is not None else {}
    if saved and (saved.get('schema') != 1 or saved.get('binding') != binding):
        raise ValueError('engine state belongs to another engine, target, depth cap or schema')
    rng = random.Random(seed)
    if saved:
        rng.setstate(common.tuple_tree(saved['rng_state']))
    current = common.replay(saved.get('current_gates',gates),target,depth_cap)
    best = common.replay(saved.get('best_gates',current['gates']),target,depth_cap)
    score = lambda witness: common.metric(witness,objective)
    feasible = lambda witness: gate_limit is None or len(witness['gates']) <= gate_limit
    if not feasible(best):
        raise ValueError('a fresh start or checkpoint best must satisfy gate_limit')
    if feasible(current) and score(current) < score(best):
        best = current
    deadline = start + seconds
    stop = common.clock_stop(deadline,should_stop)
    metrics = {'engine':engine,'objective':objective,'gate_limit':gate_limit,
               'filtered_over_gate_limit':0,'depth_squeeze_calls':0,'applicable':True,'iterations':0,'proposals':0,
               'accepted':0,'changed':0,'uphill':0,'callbacks':0,'resumed_rng':bool(saved),
               'operators':{},'best_gate_count':len(best['gates'])}
    total = int(saved.get('iterations',0))
    temperature = float(saved.get('temperature',cfg['temperature']))
    auxiliary = copy.deepcopy(saved.get('auxiliary',{}))
    constructors = ('legacy-constructor','legacy-paar','legacy-bp','inverse-bp')
    scoped_model = engine.endswith('anneal3') or engine == 'v3-pairbank3'
    scope_initialized = bool(saved.get('scope_initialized',False))

    def emit(witness, note):
        if not feasible(witness):
            metrics['filtered_over_gate_limit'] += 1
            return
        if on_candidate is not None:
            metrics['callbacks'] += 1
            on_candidate(copy.deepcopy(witness['gates']),note=note,
                         metrics={'engine':engine,'gate_count':len(witness['gates']),
                                  'depth':witness['depth'],'iteration':total,
                                  'objective':objective,'gate_limit':gate_limit,
                                  'operator':'entry' if note == 'entry' else metrics.get('last_proposal',{}).get('operator',engine),
                                  'proposal_depth_cap':depth_cap if note == 'entry' else metrics.get('last_proposal',{}).get('proposal_depth_cap'),
                                  'origin':'chunk entry' if note == 'entry' else 'search proposal'})
    if not stop():
        emit(current,'entry')
    while not stop() and (cfg['max_iterations'] is None or metrics['iterations'] < cfg['max_iterations']):
        metrics['iterations'] += 1
        total += 1
        proposal_auxiliary = copy.deepcopy(auxiliary)
        proposal_cap = depth_cap
        soft_limit = None if gate_limit is None else gate_limit + cfg['max_uphill_gates']
        strict_cap = max(0,best['depth']-1)
        if depth_cap is not None:
            strict_cap = min(strict_cap,depth_cap)
        tighten = objective == 'depth_then_gates' and rng.random() < cfg['depth_tighten_probability']
        if tighten:
            proposal_cap = strict_cap
        # Rewire the existing finite bank at a strictly smaller output deadline.
        # This never replays/rejects the retained deeper seed at that deadline.
        squeeze = objective == 'depth_then_gates' and (total==1 or rng.random()<cfg['depth_rebuild_probability'])
        if squeeze:
            metrics['depth_squeeze_calls'] += 1
            result = _module('vendor_v2.deadline_search').reconstruct(
                current['masks'],target['rows'],inputs=[1 << i for i in range(target['input_count'])],
                cap=strict_cap,rng=rng,max_seconds=min(cfg['proposal_seconds'],max(0.,deadline-time.monotonic())),
                beam_width=cfg.get('beam_width',8),max_states=cfg.get('deadline_states',800),
                objective=objective,gate_limit=gate_limit)
            details = {'operator':'depth-deadline-squeeze','proposal_depth_cap':strict_cap}
        elif engine in ('legacy-constructor','legacy-paar','legacy-bp','inverse-bp'):
            result, details = _module('historical_extra').constructor(engine,target,proposal_cap,rng,cfg,proposal_auxiliary,stop)
        elif engine == 'legacy-window':
            result, details = _module('historical_extra').window(current,target,proposal_cap,rng,cfg,stop)
        elif engine.endswith(('walk','lns')):
            result, details = _module('value_search').propose(engine,current,target,proposal_cap,rng,cfg,proposal_auxiliary,stop,deadline,objective,gate_limit)
        elif engine.endswith('anneal3'):
            result, details = _module('depth_three').propose(engine,target,rng,cfg,proposal_auxiliary,stop,deadline)
        elif engine.startswith('v2-'):
            module = _module('vendor_v2.structured_search')
            details = {}
            result = module.propose(current['masks'],proposal_cap,rng,
                                    max_seconds=min(cfg['proposal_seconds'],max(0.,deadline-time.monotonic())),
                                    max_parent_edges=cfg['max_parent_edges'],root_trials=cfg['root_trials'],
                                    constructor_budget=cfg['constructor_seconds'],
                                    kind='translate' if engine=='v2-translate' else 'cores',
                                    targets=target['rows'],inputs=[1 << i for i in range(target['input_count'])],
                                    max_roots=cfg['max_roots'],stats=details,objective=objective,gate_limit=gate_limit,
                                    source_depth_cap=depth_cap)
        elif engine == 'v3-pairbank3':
            result, details = _pairbank(current,target,depth_cap,rng,cfg,proposal_auxiliary,stop,deadline)
        else:
            kind = {'v3-component':'component_merge','v3-interface':'interface_basis',
                    'v3-backward':'backward_package'}[engine]
            move_knobs = copy.deepcopy(cfg['move_knobs'])
            move_knobs['max_seconds'] = min(move_knobs['max_seconds'],cfg['proposal_seconds'],max(0.,deadline-time.monotonic()))
            steps, details = _module('vendor_v3.advanced_moves').propose(kind,current['gates'],target['rows'],target['input_count'],proposal_cap,rng,move_knobs,should_stop=stop,
                                                                                     objective=objective,gate_limit=gate_limit,
                                                                                     source_depth_cap=depth_cap if depth_cap is not None else current['depth'])
            result = None if steps is None else {'gates':steps}
        details.setdefault('proposal_depth_cap',3 if scoped_model and not squeeze else (strict_cap if squeeze else proposal_cap))
        metrics['operators'][details.get('operator',engine)] = metrics['operators'].get(details.get('operator',engine),0)+1
        metrics['last_proposal'] = details
        # Vocabulary growth and a partially expanded pair bank are exploration
        # state even when no full witness was produced.
        if result is None:
            if engine.endswith(('walk','lns')) or engine == 'v3-pairbank3' or engine in ('legacy-paar','legacy-bp','inverse-bp'):
                auxiliary = proposal_auxiliary
            continue
        proposed = common.replay(result['gates'],target,depth_cap)
        metrics['proposals'] += 1
        if proposed['gates'] != current['gates']:
            emit(proposed,engine+' proposal')
        delta = len(proposed['gates']) - len(current['gates'])
        if objective == 'depth_then_gates':
            depth_delta = proposed['depth'] - current['depth']
            gate_scale = max(1, gate_limit or len(current['gates']))
            loss = depth_delta + delta / (gate_scale+1)
            exploratory = soft_limit is None or len(proposed['gates']) <= soft_limit
            accept = exploratory and (score(proposed) <= score(current) or
                (depth_delta <= cfg['max_uphill_depth'] and rng.random() < math.exp(-max(0.,loss)/cfg['depth_temperature'])))
        else:
            accept = engine in constructors or (scoped_model and not scope_initialized) or delta <= 0 or (delta <= cfg['max_uphill_gates'] and rng.random() < math.exp(-delta/max(temperature,1e-9)))
            if soft_limit is not None and len(proposed['gates']) > soft_limit:
                accept = False
        temperature = max(1e-9,temperature * cfg['cooling'])
        if feasible(proposed) and score(proposed) < score(best):
            best = proposed
        if accept:
            metrics['accepted'] += 1
            metrics['changed'] += proposed['gates'] != current['gates']
            metrics['uphill'] += delta > 0
            current = proposed
            auxiliary = proposal_auxiliary
            if scoped_model:
                scope_initialized = True
        if ((objective == 'gates' and engine not in constructors and not scoped_model and len(current['gates']) > len(best['gates']) + cfg['snapback']) or
            (objective == 'depth_then_gates' and current['depth'] > best['depth'] + cfg['max_uphill_depth'])):
            current = best
            # Physical assignments / partitions are tied to that trajectory.
            auxiliary = {}
    metrics.update(elapsed_seconds=time.monotonic()-start,
                   best_gate_count=len(best['gates']),best_depth=best['depth'],
                   current_gate_count=len(current['gates']),current_depth=current['depth'],
                   stopped=bool(should_stop and should_stop()))
    checkpoint = {'schema':1,'binding':binding,'engine':engine,'seed_initial':saved.get('seed_initial',seed),
                  'iterations':total,'rng_state':rng.getstate(),'temperature':temperature,
                  'scope_initialized':scope_initialized,'objective':objective,'gate_limit':gate_limit,
                  'current_gates':current['gates'],'best_gates':best['gates'],'auxiliary':auxiliary}
    return {'gates':copy.deepcopy(current['gates']),
            'state':json.loads(json.dumps(checkpoint)), 'metrics':metrics}
