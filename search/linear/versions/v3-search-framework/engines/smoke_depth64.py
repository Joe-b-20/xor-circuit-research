"""Bounded depth-objective/64-bit correctness receipt, not a discovery benchmark."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import platform
from search import engine_api as api
from search import target as oracle

FOX_OVERRIDES={e:{'proposal_seconds':.2} for e in ('v2-lns','v2-translate','v2-cores','v3-component','v3-interface','v3-backward')}
for e in ('v3-component','v3-interface','v3-backward'):
    FOX_OVERRIDES[e]['move_knobs']={'max_seconds':.2,'max_nodes':6000,'max_trials':48}


def main():
    root=Path(__file__).resolve().parents[1];rows=[]
    for name in ('fox_mu8','joltik'):
        t=oracle.load_target(name)
        path=(root/t['seeds'][0]['path']) if name=='fox_mu8' else root/'targets/seeds/joltik/local_g43_d8_217e20b57859.json'
        seed=json.loads(path.read_text());base=oracle.verify(seed,t)
        objective='gates' if name=='fox_mu8' else 'depth_then_gates'
        limit=None if name=='fox_mu8' else 43
        cap=14 if name=='fox_mu8' else 8
        for engine in api.available_engines():
            scope=api.engine_applicability(t,engine,cap,objective,limit)
            entry={'target':name,'matrix_sha256':t['matrix_sha256'],'engine':engine,**scope,
                   'seed_path':str(path.relative_to(root)),'seed_file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                   'seed_gate_count':base['gate_count'],'seed_depth':base['depth'],
                   'objective':objective,'gate_limit':limit,'depth_cap':cap}
            if not scope['applicable']:
                rows.append(entry);continue
            calls=[]
            def candidate(gates,note=None,metrics=None):
                info=oracle.verify({'gates':gates},t,cap=cap)
                assert info['equivalent'] and info['dead_gates']==0
                assert limit is None or info['gate_count']<=limit
                calls.append({'note':note,'gate_count':info['gate_count'],'depth':info['depth']})
                return True
            knobs={**FOX_OVERRIDES.get(engine,{}),'max_iterations':2} if name=='fox_mu8' else {'max_iterations':4}
            result=api.run_chunk(t,engine,seed['gates'],seed=20261027,seconds=.6,depth_cap=cap,
                                 objective=objective,gate_limit=limit,knobs=knobs,on_candidate=candidate)
            resumed=api.run_chunk(t,engine,result['gates'],seed=0,seconds=.3,depth_cap=cap,
                                  objective=objective,gate_limit=limit,knobs={**knobs,'max_iterations':1},
                                  state=json.loads(json.dumps(result['state'])),on_candidate=candidate)
            for state in (result,resumed):
                assert oracle.verify({'gates':state['gates']},t,cap=cap)['equivalent']
                best=oracle.verify({'gates':state['state']['best_gates']},t,cap=cap)
                assert best['equivalent'] and (limit is None or best['gate_count']<=limit)
            entry.update(knobs=knobs,metrics=result['metrics'],resume_metrics=resumed['metrics'],
                         candidates=calls,auxiliary_keys=sorted(result['state']['auxiliary']))
            rows.append(entry)
            print(name,engine,'proposals',result['metrics']['proposals'],'changed',result['metrics']['changed'],
                  'elapsed',round(result['metrics']['elapsed_seconds'],3),flush=True)
    receipt={'purpose':'Bounded correctness and proposal execution only; no discovery-rate or impossibility claim',
             'created_utc':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),
             'api_sha256':hashlib.sha256(Path(api.__file__).read_bytes()).hexdigest(),
             'verifier_sha256':hashlib.sha256(Path(oracle.__file__).read_bytes()).hexdigest(),
             'fox_profile_overrides':FOX_OVERRIDES,'results':rows}
    (Path(__file__).parent/'depth64-smoke.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':main()
