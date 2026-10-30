import hashlib,json,os,re,tempfile,unittest
from pathlib import Path
from search.target import (IDS,SEARCH_ROOT,VERIFIER_VERSION,load_target,matrix_sha256,
                           ncff,normalise,target_path,verify)
from search.targets.import_nist import parse

# FIPS 197, Table 4; independent of the imported programs and matrix replay.
AES=bytes.fromhex('''
637c777bf26b6fc53001672bfed7ab76 ca82c97dfa5947f0add4a2af9ca472c0
b7fd9326363ff7cc34a5e5f171d83115 04c723c31896059a071280e2eb27b275
09832c1a1b6e5aa0523bd6b329e32f84 53d100ed20fcb15b6acbbe394a4c58cf
d0efaafb434d338545f9027f503c9fa8 51a3408f929d38f5bcb6da2110fff3d2
cd0c13ec5f974417c4a77e3d645d1973 60814fdc222a908846eeb814de5e0bdb
e0323a0a4906245cc2d3ac629195e479 e7c8376d8dd54ea96c56f4ea657aae08
ba78252e1ca6b4c6e8dd741f4bbd8b8a 703eb5664803f60e613557b986c11d9e
e1f8981169d98e949b1e87e9ce5528df 8ca1890dbfe6426841992d0fb054bb16
''')
ROOT=SEARCH_ROOT/'targets'


def scalar(program,byte):
    inputs,outputs,ops=program
    values={name:(byte>>(7-i))&1 for i,name in enumerate(inputs)}
    values.update({'0':0,'1':1})
    for op,out,a,b in ops:
        values[out]=(values[a]&values[b]) if op=='AND' else values[a]^values[b]^(op=='XNOR')
    return values,sum(values[name]<<(7-i) for i,name in enumerate(outputs))


class OfficialTargets(unittest.TestCase):
    def test_all_preserved_git_blobs(self):
        catalog=json.loads((ROOT/'nist/source_catalog.json').read_text())
        self.assertEqual(catalog['commit'],'8366158a4324ef902ce740f29ddc9f7ebb1018b2')
        for entry in catalog['files']:
            raw=(ROOT/'nist/original'/entry['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),entry['sha256'])
            self.assertEqual(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),entry['git_blob'])

    def test_every_official_full_aes_source_all_256_inputs(self):
        scan=json.loads((ROOT/'nist/aes_bottom_scan.json').read_text())
        self.assertEqual(scan['sources_scanned'],61)
        for entry in scan['results']:
            program=parse((ROOT/'nist/original'/entry['source_path']).read_text())
            for byte in range(256):
                self.assertEqual(scalar(program,byte)[1],AES[byte],entry['source_path'])

    def test_aes_bottom_boundary_and_affine_reattachment(self):
        target=load_target('aes_sbox_bottom')
        self.assertEqual(target['rows'],[100056,100035,184645,99867,99894,122269,111024,110637])
        self.assertEqual((target['input_count'],target['output_count']),(18,8))
        self.assertEqual(target['affine_output_constants'],[0,1,1,0,0,0,1,1])
        scan=json.loads((ROOT/'nist/aes_bottom_scan.json').read_text())
        self.assertEqual(scan['active_frontier_circuits'],2)
        self.assertEqual(scan['compatible_sources'],9)
        for tail in scan['compatible_tail_circuits']:
            circuit=json.loads((SEARCH_ROOT/tail['path']).read_text())
            for source in circuit['provenance']['sources']:
                program=parse((ROOT/'nist/original'/source['source_path']).read_text())
                self.assertEqual(sorted(source['canonical_input_for_source_cut']),list(range(18)))
                for byte in range(256):
                    values,full=scalar(program,byte)
                    inputs=[0]*18
                    for name,index in zip(source['source_cut_names'],source['canonical_input_for_source_cut']):
                        inputs[index]=values[name]
                    computed=[]
                    for row,constant in zip(target['rows'],target['affine_output_constants']):
                        bit=constant
                        for j,value in enumerate(inputs):
                            if row>>j&1:bit^=value
                        computed.append(bit)
                    self.assertEqual(sum(bit<<(7-i) for i,bit in enumerate(computed)),full)

    def test_separate_official_matrices(self):
        for ident in ('fox_mu4','joltik'):
            target=load_target(ident)
            tokens=list(map(int,(SEARCH_ROOT/target['matrix_source']['path']).read_text().split()))
            m,n=tokens[1:3]
            expected=[sum(tokens[3+i*n+j]<<j for j in range(n)) for i in range(m)]
            self.assertEqual(target['rows'],expected)
            self.assertEqual(target['matrix_sha256'],hashlib.sha256(json.dumps({'input_count':n,'rows':expected},sort_keys=True,separators=(',',':')).encode()).hexdigest())

    def test_active_seeds_and_ncff_exports(self):
        counts={'aes_sbox_bottom':[(28,5),(38,4)],'fox_mu4':[(130,13)],'joltik':[(44,7)]}
        for ident in IDS:
            target=load_target(ident)
            self.assertEqual([(s['gates'],s['depth']) for s in target['seeds']],counts[ident])
            for seed in target['seeds']:
                circuit=json.loads((SEARCH_ROOT/seed['path']).read_text())
                info=verify(circuit,target,cap=seed['depth'])
                self.assertTrue(info['equivalent'])
                self.assertEqual((info['gate_count'],info['depth'],info['dead_gates']),(seed['gates'],seed['depth'],0))
                self.assertEqual(info['verifier_version'],VERIFIER_VERSION)
                self.assertIsNotNone(info['dag_sha256'])
                text=ncff(circuit,target)
                self.assertEqual(text,(SEARCH_ROOT/seed['ncff_path']).read_text())
                inputs,outputs,ops=parse(text)
                wire={name:i for i,name in enumerate(inputs)};gates=[]
                for op,out,a,b in ops:
                    self.assertEqual(op,'XOR');wire[out]=len(inputs)+len(gates);gates.append([wire[a],wire[b]])
                roundtrip={'inputCount':len(inputs),'gates':gates,'outputSignals':[wire[out] for out in outputs]}
                self.assertEqual(verify(roundtrip,target)['circuit_sha256'],info['circuit_sha256'])
                self.assertEqual(verify(normalise(gates,target),target)['gate_count'],seed['gates'])
                if ident=='aes_sbox_bottom':self.assertIn('excluded affine output constants',text)


class GenericVerifier(unittest.TestCase):
    def setUp(self):
        self.target={'id':'synthetic','input_count':3,'output_count':2,'rows':[3,7]}
        self.circuit={'benchmark':'synthetic','inputCount':3,'gates':[[0,1],[3,2]],'outputSignals':[3,4]}

    def test_malformed_or_wrong_explicit_outputs_never_inferred(self):
        for outputs in (None,[],[4,3],[3,True],[3,100],{'0':3}):
            with self.subTest(outputs=outputs),self.assertRaises(ValueError):
                verify({**self.circuit,'outputSignals':outputs},self.target)
        with self.assertRaises(ValueError):verify({**self.circuit,'outputs':[4,3]},self.target)
        self.assertFalse(verify({'gates':[[0,1]]},self.target)['equivalent'])
        self.assertTrue(verify({'gates':self.circuit['gates']},self.target)['outputs_inferred'])

    def test_invalid_wiring_dimensions_and_identity(self):
        for gates in ([[0,3]],[[True,1]],[[-1,0]],[[0,1,2]]):
            with self.assertRaises(ValueError):verify({'gates':gates},self.target)
        for extra in ({'inputCount':32},{'benchmark':'other'},{'affine_output_constants':[0,1]}):
            with self.assertRaises(ValueError):verify({**self.circuit,**extra},self.target)
        with self.assertRaises(ValueError):verify(self.circuit,self.target,cap=1)
        self.assertTrue(verify(self.circuit,self.target,cap=2)['equivalent'])

    def test_dead_and_duplicate_normalization(self):
        raw=[[0,1],[2,2],[3,4],[5,2]]
        info=verify({'gates':raw},self.target)
        self.assertIsNone(info['dag_sha256'])
        result=normalise(raw,self.target)
        self.assertEqual(result['gateCount'],2)
        self.assertEqual(result['depth'],2)
        self.assertEqual(result['affine_output_constants'],[0,0])
        self.assertEqual(verify(result,self.target)['dead_gates'],0)
        one={'id':'one','input_count':3,'output_count':1,'rows':[3]}
        self.assertEqual(verify({'gates':[[0,1],[3,2],[4,2]],'outputSignals':[3]},one,cap=1)['dead_gates'],2)

    def test_schedule_independent_dag_hash(self):
        target={'id':'four','input_count':4,'output_count':3,'rows':[3,12,15]}
        left={'gates':[[0,1],[2,3],[4,5]],'outputSignals':[4,5,6]}
        right={'gates':[[3,2],[1,0],[5,4]],'outputSignals':[5,4,6]}
        a,b=verify(left,target),verify(right,target)
        self.assertEqual(a['dag_sha256'],b['dag_sha256'])
        self.assertNotEqual(a['circuit_sha256'],b['circuit_sha256'])
        self.assertEqual(a['value_set_sha256'],b['value_set_sha256'])

    def test_large_dimension_zero_repeated_and_input_outputs(self):
        target={'id':'large','input_count':40,'output_count':1,'rows':[(1<<39)|1]}
        self.assertTrue(verify({'gates':[[0,39]]},target)['equivalent'])
        other={'id':'alias','input_count':2,'output_count':4,'rows':[1,3,3,0]}
        result=normalise([[0,1],[0,0]],other)
        self.assertTrue(verify(result,other)['equivalent'])
        self.assertEqual(result['outputSignals'][1],result['outputSignals'][2])

    def test_resolution_independent_of_cwd_and_hash_validation(self):
        old=Path.cwd()
        with tempfile.TemporaryDirectory() as temp:
            try:
                os.chdir(temp)
                self.assertTrue(target_path('fox_mu4').is_file())
                self.assertEqual(load_target('targets/joltik.json')['id'],'joltik')
                path=Path(temp)/'custom.json';path.write_text(json.dumps(self.target))
                self.assertEqual(load_target(path)['rows'],[3,7])
            finally:os.chdir(old)
        with self.assertRaises(ValueError):verify(self.circuit,{**self.target,'matrix_sha256':'bad'})
        self.assertEqual(matrix_sha256(3,[3,7]),'6e9dd3e707a943f6f370ca64652b0363720c715576e169884dea7f131d0cde10')


if __name__=='__main__':unittest.main()
