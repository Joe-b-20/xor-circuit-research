"""Behavioral controls for actual generic mechanisms, replay and continuation."""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import time
import unittest

from search import engine_api as api


def target(n, rows, name='test'):
    return {'id':name,'input_count':n,'output_count':len(rows),'rows':rows,
            'matrix_sha256':hashlib.sha256(json.dumps([n,rows]).encode()).hexdigest()}


def balanced(t):
    n=t['input_count']; values=[1 << i for i in range(n)];index={v:i for i,v in enumerate(values)};gates=[]
    def build(m):
        if m in index:return index[m]
        bits=[1 << i for i in range(n) if m & (1 << i)]
        a=sum(bits[:len(bits)//2]);b=m^a
        ia,ib=build(a),build(b)
        index[m]=len(values);values.append(m);gates.append([ia,ib]);return index[m]
    for m in t['rows']:build(m)
    return gates


def check(test, gates, t, cap=None):
    """Independent replay, live-ancestry test and full small truth tables."""
    n=t['input_count'];values=[1 << i for i in range(n)];depth=[0]*n
    for a,b in gates:
        test.assertTrue(type(a) is int and type(b) is int and 0 <= a < len(values) and 0 <= b < len(values))
        m=values[a]^values[b];test.assertNotIn(m,values);test.assertNotEqual(m,0)
        values.append(m);depth.append(1+max(depth[a],depth[b]))
    out=[values.index(m) for m in t['rows']]
    if cap is not None:test.assertLessEqual(max(depth[i] for i in out),cap)
    live=set();pending=out[:]
    while pending:
        i=pending.pop()
        if i < n or i in live:continue
        live.add(i);pending.extend(gates[i-n])
    test.assertEqual(len(live),len(gates))
    if n <= 6:
        for raw in range(1 << n):
            signal=[(raw >> i)&1 for i in range(n)]
            for a,b in gates:signal.append(signal[a]^signal[b])
            test.assertEqual([signal[i] for i in out],[(raw&m).bit_count()%2 for m in t['rows']])


class EngineTests(unittest.TestCase):
    def test_all_modes_execute_real_code_and_replay_callbacks(self):
        t=target(5,[31]);g=balanced(t)
        for engine in api.available_engines():
            with self.subTest(engine=engine):
                calls=[]
                def candidate(steps,note=None,metrics=None):
                    check(self,steps,t,3)
                    self.assertIn('operator',metrics);self.assertIn('proposal_depth_cap',metrics)
                    self.assertEqual(metrics['origin'],'chunk entry' if note=='entry' else 'search proposal')
                    if note=='entry':self.assertEqual(metrics['operator'],'entry')
                    calls.append((note,metrics));return True
                result=api.run_chunk(t,engine,g,seed=3,seconds=.4,depth_cap=3,
                                     knobs={'max_iterations':2},on_candidate=candidate)
                check(self,result['gates'],t,3)
                self.assertEqual(result['metrics']['iterations'],2)
                self.assertTrue(result['metrics']['operators'])
                self.assertTrue(calls)
                json.dumps(result,allow_nan=False)

    def test_dimension_and_output_count_are_independent(self):
        for n,rows in ((1,[1]),(4,[7,11]),(16,[3,15,63,255,1023,4095,16383,65535]),(32,[3,0x80000001])):
            t=target(n,rows);g=balanced(t)
            for engine in ('legacy-walk','legacy-lns','v2-walk','v2-lns','v2-translate','v2-cores','v3-component','v3-interface','v3-backward'):
                with self.subTest(n=n,engine=engine):
                    result=api.run_chunk(t,engine,g,seed=5,seconds=.08,depth_cap=None,knobs={'max_iterations':1})
                    check(self,result['gates'],t)

    def test_collision_and_first_unlock_really_reduce_a_gate(self):
        t=target(4,[7,11]);g=[[0,1],[0,3],[4,2],[5,1]]
        for engine in ('legacy-window','v3-component'):
            with self.subTest(engine=engine):
                r=api.run_chunk(t,engine,g,seed=1,seconds=1,depth_cap=2,knobs={'max_iterations':1,'proposal_seconds':.2})
                self.assertEqual(len(r['gates']),3);check(self,r['gates'],t,2)
                self.assertGreater(r['metrics']['changed'],0)

    def test_interface_basis_and_backward_package_really_execute(self):
        controls=[('v3-interface',target(4,[11,14,5]),[[0,1],[1,2],[4,3],[5,3],[0,2]],3,
                   {'move_knobs':{'interface_sets':[[3,6]],'basis_matrices':[[1,3]]}},4),
                  ('v3-backward',target(6,[31,47]),[[0,1],[6,2],[3,4],[3,5],[7,8],[7,9]],4,{},5)]
        for engine,t,g,cap,knobs,count in controls:
            with self.subTest(engine=engine):
                knobs.update(max_iterations=1,proposal_seconds=.3)
                r=api.run_chunk(t,engine,g,seed=1,seconds=1,depth_cap=cap,knobs=knobs)
                self.assertEqual(len(r['gates']),count);check(self,r['gates'],t,cap)
                self.assertGreater(r['metrics']['last_proposal']['candidates_verified'],0)

    def test_constructor_families_complete_new_roots(self):
        t=target(5,[31]);g=balanced(t)
        for engine in ('legacy-constructor','legacy-paar','legacy-bp','inverse-bp'):
            with self.subTest(engine=engine):
                r=api.run_chunk(t,engine,g,seed=3,seconds=1,depth_cap=3,knobs={'max_iterations':30})
                self.assertGreater(r['metrics']['proposals'],0)
                self.assertGreater(r['metrics']['changed'],0)
                check(self,r['gates'],t,3)

    def test_json_resume_retains_rng_trajectory_and_auxiliary(self):
        t=target(5,[31]);g=balanced(t)
        for engine in ('legacy-walk','legacy-lns','legacy-anneal3','v2-lns','v2-anneal3','legacy-paar','legacy-bp','inverse-bp'):
            with self.subTest(engine=engine):
                whole=api.run_chunk(t,engine,g,seed=7,seconds=5,depth_cap=3,knobs={'max_iterations':4})
                first=api.run_chunk(t,engine,g,seed=7,seconds=5,depth_cap=3,knobs={'max_iterations':2})
                resumed=api.run_chunk(t,engine,first['gates'],seed=999,seconds=5,depth_cap=3,
                                      state=json.loads(json.dumps(first['state'])),knobs={'max_iterations':2})
                self.assertEqual(whole['state'],resumed['state'])

    def test_state_cannot_cross_target_engine_or_cap(self):
        t=target(5,[31]);g=balanced(t)
        r=api.run_chunk(t,'legacy-lns',g,seed=1,seconds=0,depth_cap=3)
        for other,engine,cap in ((target(5,[15]),'legacy-lns',3),(t,'v2-lns',3),(t,'legacy-lns',None)):
            with self.assertRaises(ValueError):
                api.run_chunk(other,engine,g,seed=1,seconds=0,depth_cap=cap,state=r['state'])

    def test_invalid_scope_and_knobs_are_explicit(self):
        t=target(16,[65535])
        for engine in ('legacy-anneal3','v2-anneal3','v3-pairbank3'):
            self.assertFalse(api.engine_applicability(t,engine,None)['applicable'])
            with self.assertRaises(ValueError):api.run_chunk(t,engine,balanced(t),seed=1,seconds=.1)
        for settings in ({'unknown':1},{'temperature':0},{'max_iterations':True},{'proposal_seconds':float('nan')}):
            with self.assertRaises(ValueError):api.effective_knobs('legacy-walk',settings)
        with self.assertRaises(ValueError):api.effective_knobs('v3-interface',{'move_knobs':{'bad':1}})
        a=api.effective_knobs('v3-interface');a['move_knobs']['max_nodes']=0
        self.assertGreater(api.effective_knobs('v3-interface')['move_knobs']['max_nodes'],0)

    def test_early_stop_and_no_mutation(self):
        t=target(5,[31]);g=balanced(t);original=copy.deepcopy(g)
        for engine in api.available_engines():
            start=time.monotonic()
            r=api.run_chunk(t,engine,g,seed=1,seconds=10,depth_cap=3,should_stop=lambda:True)
            self.assertLess(time.monotonic()-start,.5)
            self.assertEqual(r['metrics']['iterations'],0)
            self.assertEqual(g,original)
        calls=[0]
        def stop():calls[0]+=1;return calls[0]>25
        start=time.monotonic()
        r=api.run_chunk(t,'v3-interface',g,seed=1,seconds=10,depth_cap=3,should_stop=stop)
        self.assertTrue(r['metrics']['stopped']);self.assertLess(time.monotonic()-start,1)

    def test_real_targets_all_applicable_families(self):
        from search.target import load_target, verify
        root=Path(__file__).resolve().parents[1]
        for name in ('aes_sbox_bottom','fox_mu4','joltik'):
            t=load_target(name)
            seed=json.loads((root/t['seeds'][0]['path']).read_text())
            for engine in api.available_engines():
                if not api.engine_applicability(t,engine,None)['applicable']:continue
                with self.subTest(target=name,engine=engine):
                    def candidate(gates,note=None,metrics=None):
                        self.assertTrue(verify({'gates':gates},t)['equivalent']);return True
                    r=api.run_chunk(t,engine,seed['gates'],seed=20261024,seconds=.1,
                                    knobs={'max_iterations':1},on_candidate=candidate)
                    self.assertTrue(verify({'gates':r['gates']},t)['equivalent'])
                    self.assertEqual(r['metrics']['iterations'],1)
                    self.assertTrue(r['metrics']['operators'])

    def test_depth_three_enters_its_scoped_trajectory(self):
        from search.target import load_target, verify
        root=Path(__file__).resolve().parents[1];t=load_target('joltik')
        seed=json.loads((root/t['seeds'][0]['path']).read_text())
        for engine in ('legacy-anneal3','v2-anneal3'):
            r=api.run_chunk(t,engine,seed['gates'],seed=3,seconds=.5,knobs={'max_iterations':2})
            self.assertLessEqual(verify({'gates':r['gates']},t)['depth'],3)
            self.assertTrue(r['state']['scope_initialized'])
            self.assertGreater(r['metrics']['changed'],0)

    def test_effective_config_roundtrip_includes_hidden_kernel_defaults(self):
        t=target(5,[31]);g=balanced(t)
        for engine in api.available_engines():
            settings=api.effective_knobs(engine,{'max_iterations':0})
            self.assertIn('kernel_signature_defaults',settings)
            self.assertIn('kernel_internal_calls',settings)
            r=api.run_chunk(t,engine,g,seed=1,seconds=1,knobs=json.loads(json.dumps(settings)))
            self.assertEqual(r['metrics']['iterations'],0)
        config=api.effective_knobs('v2-anneal3')
        self.assertEqual(config['kernel_signature_defaults']['vendor_v2.deadline_search.optimize_depth3']['existing_pairs'],[])
        config['kernel_signature_defaults']['vendor_v2.deadline_search.optimize_depth3']['max_nodes']=1
        with self.assertRaises(ValueError):api.effective_knobs('v2-anneal3',config)
        internal=api.effective_knobs('v2-cores')['kernel_internal_calls']
        sites=internal['vendor_v2.structured_search']
        self.assertTrue(any(site['keyword_arguments'].get('max_states',{}).get('value')==250 for site in sites))

    def test_depth_objective_prefers_more_gates_when_shallower(self):
        # Shared triple: four gates/depth three; separate final pairs: five/depth two.
        t=target(5,[15,23]);source=[[0,1],[5,2],[6,3],[6,4]]
        options={'max_iterations':20,'depth_rebuild_probability':0,'depth_tighten_probability':1}
        calls=[]
        def candidate(gates,note=None,metrics=None):
            check(self,gates,t,3);self.assertLessEqual(len(gates),5);calls.append(gates);return True
        depth=api.run_chunk(t,'legacy-constructor',source,seed=3,seconds=2,depth_cap=3,
                            objective='depth_then_gates',gate_limit=5,knobs=options,on_candidate=candidate)
        self.assertEqual((depth['metrics']['best_depth'],depth['metrics']['best_gate_count']),(2,5))
        gate=api.run_chunk(t,'legacy-constructor',source,seed=3,seconds=2,depth_cap=3,knobs={'max_iterations':20})
        self.assertEqual((gate['metrics']['best_depth'],gate['metrics']['best_gate_count']),(3,4))
        strict=api.run_chunk(t,'legacy-constructor',source,seed=3,seconds=2,depth_cap=3,
                             objective='depth_then_gates',gate_limit=4,knobs=options,
                             on_candidate=lambda g,**kw:self.assertLessEqual(len(g),4))
        self.assertEqual(strict['state']['best_gates'],source)
        self.assertGreater(strict['metrics']['filtered_over_gate_limit'],0)

    def test_hard_gate_feasibility_precedes_internal_depth_ranking(self):
        from unittest.mock import patch
        from search.engines.vendor_v2.deadline_search import objective_key
        from search.engines import common,value_search
        import random
        t=target(5,[15,23]);source=[[0,1],[5,2],[6,3],[6,4]]
        shallow=[[0,1],[2,3],[2,4],[5,6],[5,7]]
        feasible=common.replay(source,t,3);over=common.replay(shallow,t,3)
        # A shallower over-budget construction must not hide a usable candidate.
        self.assertLess(objective_key(feasible,'depth_then_gates',4),objective_key(over,'depth_then_gates',4))
        self.assertEqual(objective_key({'gates':source,'depth':3},'depth_then_gates',4),(0,3,4))
        counter=[0]
        def reconstructed(*args,**kwargs):
            counter[0]+=1;return over if counter[0]==1 else feasible
        with patch('search.engines.vendor_v2.deadline_search.reconstruct',side_effect=reconstructed):
            result,_=value_search.propose('v2-walk',feasible,t,3,random.Random(1),api.effective_knobs('v2-walk'),{},
                                         lambda:False,time.monotonic()+5,'depth_then_gates',4)
        self.assertGreater(counter[0],1);self.assertEqual(result['gates'],source)

    def test_depth_resume_and_objective_binding(self):
        t=target(5,[15,23]);g=[[0,1],[5,2],[6,3],[6,4]]
        kwargs={'objective':'depth_then_gates','gate_limit':5,'depth_cap':3}
        whole=api.run_chunk(t,'legacy-constructor',g,seed=9,seconds=5,knobs={'max_iterations':8},**kwargs)
        first=api.run_chunk(t,'legacy-constructor',g,seed=9,seconds=5,knobs={'max_iterations':4},**kwargs)
        last=api.run_chunk(t,'legacy-constructor',first['gates'],seed=999,seconds=5,
                           state=json.loads(json.dumps(first['state'])),knobs={'max_iterations':4},**kwargs)
        self.assertEqual(whole['state'],last['state'])
        for objective,limit in (('gates',5),('depth_then_gates',4)):
            with self.assertRaises(ValueError):
                api.run_chunk(t,'legacy-constructor',g,seed=1,seconds=0,depth_cap=3,
                              objective=objective,gate_limit=limit,state=first['state'])

    def test_all_generic_families_keep_bits_40_and_63(self):
        rows=[(1<<63)|(1<<40)|3,(1<<62)|(1<<39)|5]
        t=target(64,rows);g=balanced(t)
        for engine in api.available_engines():
            scope=api.engine_applicability(t,engine,3)
            if engine.endswith('anneal3') or engine=='v3-pairbank3':
                self.assertFalse(scope['applicable']);continue
            with self.subTest(engine=engine):
                r=api.run_chunk(t,engine,g,seed=4,seconds=.2,depth_cap=3,knobs={'max_iterations':1},
                                on_candidate=lambda steps,**kw:check(self,steps,t,3))
                check(self,r['gates'],t,3);self.assertEqual(r['metrics']['iterations'],1)
        from search.engines.vendor_v3 import pair_bank_search as pair
        from search.engines.vendor_v2.deadline_search import optimize_depth3
        high=(1<<63)|(1<<40)|(1<<20)|1
        self.assertTrue(any(p>1<<32 for p in pair.all_input_pairs(64)))
        self.assertTrue(pair.parent_pairings(high))
        result=optimize_depth3([high],max_seconds=.1)
        self.assertIn(high,result['recipes'])
        self.assertGreater(api.effective_knobs('v2-lns')['bank_limit'],540)
        self.assertGreater(api.effective_knobs('inverse-bp')['constructor_gate_limit'],540)

    def test_real_fox64_seed_replay_proposals_stop_and_resume(self):
        from search.target import load_target,verify
        root=Path(__file__).resolve().parents[1];t=load_target('fox_mu8')
        seed=json.loads((root/t['seeds'][0]['path']).read_text())
        self.assertEqual((t['input_count'],t['output_count'],len(seed['gates'])),(64,64,540))
        checks=[]
        def candidate(gates,note=None,metrics=None):
            info=verify({'gates':gates},t);self.assertTrue(info['equivalent']);checks.append(note);return True
        begin=time.monotonic()
        r=api.run_chunk(t,'v2-lns',seed['gates'],seed=7,seconds=.5,depth_cap=14,
                        knobs={'max_iterations':2,'proposal_seconds':.2},on_candidate=candidate)
        self.assertLess(time.monotonic()-begin,3)
        self.assertGreater(r['metrics']['proposals'],0)
        self.assertTrue(any(note!='entry' for note in checks))
        resumed=api.run_chunk(t,'v2-lns',r['gates'],seed=99,seconds=.2,depth_cap=14,
                              knobs={'max_iterations':1,'proposal_seconds':.2},state=json.loads(json.dumps(r['state'])))
        self.assertTrue(resumed['metrics']['resumed_rng']);self.assertTrue(verify({'gates':resumed['gates']},t)['equivalent'])
        stopped=api.run_chunk(t,'v3-interface',seed['gates'],seed=0,seconds=10,depth_cap=14,should_stop=lambda:True)
        self.assertEqual(stopped['metrics']['iterations'],0)

    def test_v2_and_legacy_are_different_algorithms(self):
        self.assertNotIn('beam_width',api.effective_knobs('legacy-lns'))
        self.assertIn('beam_width',api.effective_knobs('v2-lns'))
        self.assertIn('move_knobs',api.effective_knobs('v3-interface'))
        t=target(5,[31]);g=balanced(t)
        for e in ('legacy-anneal3','v2-anneal3','v3-pairbank3','v2-translate','v2-cores'):
            r=api.run_chunk(t,e,g,seed=3,seconds=1,depth_cap=3,knobs={'max_iterations':3})
            self.assertGreater(r['metrics']['proposals'],0)
            self.assertGreater(r['metrics']['changed'],0)


if __name__=='__main__':unittest.main()
