"""Reproducible bounded correctness coverage; never a quality benchmark.

Run from repository root: python3 -m search.engines.smoke
"""
import hashlib
import json
from pathlib import Path
from search import engine_api as api
from search import target as oracle


def main():
    root=Path(__file__).resolve().parents[1]
    report=[]
    for name in ('aes_sbox_bottom','fox_mu4','joltik'):
        t=oracle.load_target(name)
        seed=json.loads((root/t['seeds'][0]['path']).read_text())
        for engine in api.available_engines():
            scope=api.engine_applicability(t,engine,None)
            if not scope['applicable']:
                report.append({'target':name,'engine':engine,**scope});continue
            calls=[]
            seen_witnesses={}
            def check(gates):
                info=oracle.verify({'gates':gates},t)
                assert info['equivalent'] and info['dead_gates']==0
                return info
            def candidate(gates,note=None,metrics=None):
                info=check(gates);pair=(info['gate_count'],info['depth']);calls.append(pair)
                seen_witnesses.setdefault(pair,{'gates':gates,'gate_count':pair[0],'depth':pair[1]})
                return True
            result=api.run_chunk(t,engine,seed['gates'],seed=20261024,seconds=.45,
                                 depth_cap=None,knobs={'max_iterations':8},on_candidate=candidate)
            info=check(result['gates'])
            resumed=api.run_chunk(t,engine,result['gates'],seed=0,seconds=.08,
                                  state=json.loads(json.dumps(result['state'])),
                                  knobs={'max_iterations':1},on_candidate=candidate)
            check(resumed['gates'])
            report.append({'target':name,'matrix_sha256':t['matrix_sha256'],'engine':engine,**scope,
                           'metrics':result['metrics'],'resumed_metrics':resumed['metrics'],
                           'callback_checks':len(calls),'distinct_metric_pairs':len(set(calls)),
                           'verified_current':{'gate_count':info['gate_count'],'depth':info['depth']},
                           'auxiliary_keys':sorted(result['state']['auxiliary']),
                           'non_dominated_smoke_witnesses':[seen_witnesses[pair] for pair in sorted(seen_witnesses)
                               if not any(q[0]<=pair[0] and q[1]<=pair[1] and q!=pair for q in seen_witnesses)
                               and pair != (t['seeds'][0]['gates'],t['seeds'][0]['depth'])]})
            print(name,engine,'iterations',result['metrics']['iterations'],'proposals',result['metrics']['proposals'],
                  'changed',result['metrics']['changed'],'current',info['gate_count'],info['depth'],flush=True)
    out={'purpose':'Bounded correctness/operator smoke, not search quality or discovery-rate benchmark',
         'api_sha256':hashlib.sha256(Path(api.__file__).read_bytes()).hexdigest(),
         'verifier_sha256':hashlib.sha256(Path(oracle.__file__).read_bytes()).hexdigest(),
         'seed':20261024,'depth_cap':None,'seconds':.45,'max_iterations':8,
         'resume_seconds':.08,'resume_iterations':1,'results':report}
    (Path(__file__).parent/'real-target-smoke.json').write_text(json.dumps(out,indent=2)+'\n')


if __name__=='__main__':main()
