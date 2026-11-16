#!/usr/bin/env python3
"""Rebuild targets/seeds from preserved pinned NIST bytes; no network or search."""
from collections import Counter
from pathlib import Path
from functools import lru_cache
import hashlib,json,re,sys

SEARCH=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SEARCH.parent))
from search.target import matrix_sha256,normalise,verify,ncff
ROOT=Path(__file__).resolve().parent
ORIGINAL=ROOT/'nist/original'
CATALOG=ROOT/'nist/source_catalog.json'
CANONICAL='data/slp/aes/old-2020/aes-sbox-fwd-g113-a32-d27-ad6.slp'


def expand(spec):
    result=[]
    for token in spec.split():
        if ':' not in token:result.append(token);continue
        match=re.fullmatch(r'([A-Za-z_]+)(\d+):([A-Za-z_]+)(\d+)',token)
        if not match or match[1]!=match[3]:raise ValueError('Unsupported variable range '+token)
        result.extend(match[1]+str(i) for i in range(int(match[2]),int(match[4])+1))
    return result


def parse(text):
    inputs=outputs=None;operations=[];active=False
    for raw in text.splitlines():
        line=raw.strip()
        if line.startswith('Inputs:'):inputs=expand(line.split(':',1)[1])
        if line.startswith('Outputs:'):outputs=expand(line.split(':',1)[1])
        if line=='begin SLP':active=True;continue
        if line=='end SLP':active=False;continue
        if not active or not line or line.startswith(('#','%')):continue
        parts=line.split()
        if len(parts)!=4 or parts[0] not in ('AND','XOR','XNOR'):
            raise ValueError('Unsupported original instruction '+line)
        operations.append(parts)
    if not inputs or not outputs:raise ValueError('Missing original interface')
    known=set(inputs)|{'0','1'}
    for op,out,a,b in operations:
        if out in known or a not in known or b not in known:raise ValueError('Bad original topology')
        known.add(out)
    if any(out not in known for out in outputs):raise ValueError('Missing original output')
    return inputs,outputs,operations


def extract(program):
    inputs,outputs,operations=program
    byout={row[1]:row for row in operations};boundary=set();used=set()
    def visit(name):
        if name in ('0','1'):return
        row=byout.get(name)
        if row is None or row[0]=='AND':boundary.add(name);return
        if name in used:return
        used.add(name);visit(row[2]);visit(row[3])
    for out in outputs:visit(out)
    ordered=[name for name in inputs+[row[1] for row in operations] if name in boundary]
    masks={name:1<<i for i,name in enumerate(ordered)};masks.update({'0':0,'1':0})
    constants={name:0 for name in ordered};constants.update({'0':0,'1':1})
    depths={name:0 for name in ordered};depths.update({'0':0,'1':0})
    for op,out,a,b in operations:
        if out in used:
            masks[out]=masks[a]^masks[b]
            constants[out]=constants[a]^constants[b]^(op=='XNOR')
            depths[out]=1+max(depths[a],depths[b])
    rows=[masks[name] for name in outputs]
    columns=[sum(((row>>i)&1)<<j for j,row in enumerate(rows)) for i in range(len(ordered))]
    return {'inputs':ordered,'rows':rows,'columns':columns,
            'constants':[constants[name] for name in outputs],
            'operations':[row for row in operations if row[1] in used],
            'raw_gate_count':len(used),'raw_depth':max(depths[name] for name in outputs)}


def mul(a,b):
    result=0
    while b:
        if b&1:result^=a
        a<<=1
        if a&256:a^=0x11b
        b>>=1
    return result


@lru_cache(None)
def aes(value):
    inverse=0 if value==0 else next(v for v in range(1,256) if mul(value,v)==1)
    return inverse^((inverse<<1)|(inverse>>7))&255^((inverse<<2)|(inverse>>6))&255^((inverse<<3)|(inverse>>5))&255^((inverse<<4)|(inverse>>4))&255^0x63


def full_truth(program):
    inputs,outputs,operations=program;mask=(1<<256)-1
    values={name:sum(((x>>(7-i))&1)<<x for x in range(256)) for i,name in enumerate(inputs)}
    values.update({'0':0,'1':mask})
    for op,out,a,b in operations:
        values[out]=values[a]&values[b] if op=='AND' else values[a]^values[b]^(mask if op=='XNOR' else 0)
    for i,name in enumerate(outputs):
        expected=sum(((aes(x)>>(7-i))&1)<<x for x in range(256))
        if values[name]!=expected:raise ValueError('Original full Sbox does not match AES truth table')
    return values


def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2)+'\n')


def main():
    catalog=json.loads(CATALOG.read_text());byname={entry['path']:entry for entry in catalog['files']}
    for entry in catalog['files']:
        raw=(ORIGINAL/entry['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==entry['sha256']
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==entry['git_blob']
    base=extract(parse((ORIGINAL/CANONICAL).read_text()))
    assert len(base['inputs'])==18 and len(set(base['columns']))==18
    bottom={'id':'aes_sbox_bottom','name':'AES S-box Boyar–Peralta bottom linear layer',
            'input_count':18,'output_count':8,'rows':base['rows'],
            'matrix_sha256':matrix_sha256(18,base['rows']),
            'affine_output_constants':base['constants'],'output_bit_order':'S0 is most significant AES output bit',
            'input_names':['z'+str(i) for i in range(18)],'output_names':['S'+str(i) for i in range(8)],
            'scope':'Linear part only. Add the recorded affine output constants when reconnecting to the original nonlinear S-box.',
            'matrix_source':{'kind':'symbolic extraction from pinned official full S-box; no standalone NIST bottom matrix exists in the pinned tree',
                             'path':'targets/nist/original/'+CANONICAL,'cut_inputs':base['inputs'],'source_url':byname[CANONICAL]['url']},
            'nist_commit':catalog['commit'],'seeds':[]}
    scans=[];unique={};allones=(1<<256)-1
    for entry in catalog['files']:
        path=entry['path']
        if '/aes/' not in path:continue
        program=parse((ORIGINAL/path).read_text());values=full_truth(program);tail=extract(program)
        scan={'source_path':path,'source_sha256':entry['sha256'],'full_aes_256_cases_checked':True,
              'boundary_count':len(tail['inputs']),'tail_gate_count':tail['raw_gate_count'],'tail_depth':tail['raw_depth']}
        if len(tail['inputs'])!=18 or Counter(tail['columns'])!=Counter(base['columns']):
            scan.update(compatible=False,reason='Different final-product boundary or linear column signatures; not imported into this target')
            scans.append(scan);continue
        permutation=[base['columns'].index(column) for column in tail['columns']]
        wire={name:permutation[i] for i,name in enumerate(tail['inputs'])};wire.update({'0':None,'1':None});gates=[]
        for op,out,a,b in tail['operations']:
            if wire[a] is None:wire[out]=wire[b]
            elif wire[b] is None:wire[out]=wire[a]
            else:wire[out]=18+len(gates);gates.append([wire[a],wire[b]])
        circuit=normalise(gates,bottom);checked=verify(circuit,bottom)
        if tail['constants']!=bottom['affine_output_constants']:raise ValueError('Unexpected affine constant change')
        # Independently reconnect the extracted linear matrix to the actual
        # nonlinear boundary truth vectors, including every affine complement.
        canonical_inputs=[0]*18
        for name,index in zip(tail['inputs'],permutation):canonical_inputs[index]=values[name]
        for i,row in enumerate(bottom['rows']):
            actual=allones if bottom['affine_output_constants'][i] else 0
            for j in range(18):
                if row>>j&1:actual^=canonical_inputs[j]
            assert actual==values[program[1][i]]
        provenance={'source_path':path,'source_url':entry['url'],'source_sha256':entry['sha256'],
                    'source_cut_names':tail['inputs'],'canonical_input_for_source_cut':permutation,
                    'full_gate_count':len(program[2]),'affine_output_constants':tail['constants'],
                    'full_aes_256_cases_checked':True,'reattachment_256_cases_checked':True}
        digest=checked['circuit_sha256'];scan.update(compatible=True,circuit_sha256=digest,
                verified_gate_count=checked['gate_count'],verified_depth=checked['depth'],input_permutation=permutation)
        scans.append(scan)
        if digest in unique:unique[digest]['provenance']['sources'].append(provenance);continue
        circuit['provenance']={'derivation':'XOR-only tail; XNOR constants factored into explicit target affine metadata; input-wire permutation only','sources':[provenance]}
        filename='aes_bottom_g'+str(checked['gate_count'])+'_d'+str(checked['depth'])+'_'+digest[:12]+'.json'
        seedpath=ROOT/'seeds/aes_sbox_bottom'/filename
        unique[digest]=circuit
        bottom['seeds'].append({'path':str(seedpath.relative_to(SEARCH)),'gates':checked['gate_count'],'depth':checked['depth'],'circuit_sha256':digest,'source_kind':'derived from pinned NIST full S-box tail'})
    for seed in bottom['seeds']:
        save(SEARCH/seed['path'],unique[seed['circuit_sha256']])
    for identifier,matrixname,circuitname in (
        ('fox_mu4','data/slp/2021-linearmaps/matrices/ciphers-32x32/FoxMu4.mat.txt','data/slp/2021-linearmaps/circuits/ciphers-32x32/FoxMu4--XOR=130-rs=471.circ.txt'),
        ('joltik','data/slp/2021-linearmaps/matrices/ciphers-16x16/Joltik.mat.txt','data/slp/2021-linearmaps/circuits/ciphers-16x16/Joltik--XOR=44--XZLBZ20.circ.txt')):
        tokens=list(map(int,(ORIGINAL/matrixname).read_text().split()))
        assert tokens[0]==1
        m,n=tokens[1:3];assert len(tokens[3:])==m*n
        rows=[sum(tokens[3+i*n+j]<<j for j in range(n)) for i in range(m)]
        target={'id':identifier,'name':'FOX Mu4' if identifier=='fox_mu4' else 'Joltik diffusion layer','input_count':n,'output_count':m,'rows':rows,'matrix_sha256':matrix_sha256(n,rows),'nist_commit':catalog['commit'],'affine_output_constants':[0]*m,'matrix_source':{'kind':'official NIST matrix bytes','path':'targets/nist/original/'+matrixname,'source_url':byname[matrixname]['url'],'source_sha256':byname[matrixname]['sha256']},'seeds':[]}
        inputs,outputs,operations=parse((ORIGINAL/circuitname).read_text());wire={name:i for i,name in enumerate(inputs)};gates=[]
        for op,out,a,b in operations:
            assert op=='XOR';wire[out]=n+len(gates);gates.append([wire[a],wire[b]])
        circuit={'benchmark':identifier,'inputCount':n,'gates':gates,'outputSignals':[wire[name] for name in outputs]}
        checked=verify(circuit,target);assert checked['equivalent'] and checked['dead_gates']==0
        circuit.update(gateCount=checked['gate_count'],depth=checked['depth'],provenance={'source_path':circuitname,'source_url':byname[circuitname]['url'],'source_sha256':byname[circuitname]['sha256'],'matrix_independently_verified':True,'matrix_metadata_note':'Original circuit vecRows/vecCols comments are transposed relative to its official .mat file. Replayed outputs match .mat rows; .mat bytes define this target.'})
        seedpath=ROOT/'seeds'/identifier/(identifier+'_g'+str(checked['gate_count'])+'_d'+str(checked['depth'])+'.json');save(seedpath,circuit)
        target['seeds']=[{'path':str(seedpath.relative_to(SEARCH)),'gates':checked['gate_count'],'depth':checked['depth'],'circuit_sha256':checked['circuit_sha256'],'source_kind':'official NIST circuit'}]
        save(ROOT/(identifier+'.json'),target)
    bottom['seeds'].sort(key=lambda item:(item['gates'],item['depth'],item['path']))
    for seed in bottom['seeds']:
        seed['pareto']=not any(other['gates']<=seed['gates'] and other['depth']<=seed['depth'] and (other['gates'],other['depth'])!=(seed['gates'],seed['depth']) for other in bottom['seeds'])
    compatible_seeds=list(bottom['seeds'])
    for seed in compatible_seeds:
        if not seed['pareto']:
            source=SEARCH/seed['path'];destination=ROOT/'nist/derived_tails'/source.name
            destination.parent.mkdir(parents=True,exist_ok=True);source.replace(destination)
            seed['path']=str(destination.relative_to(SEARCH))
    bottom['seeds']=[seed for seed in compatible_seeds if seed['pareto']]
    save(ROOT/'aes_sbox_bottom.json',bottom)
    save(ROOT/'nist/aes_bottom_scan.json',{'nist_commit':catalog['commit'],'canonical_source':CANONICAL,'sources_scanned':len(scans),'compatible_sources':sum(x['compatible'] for x in scans),'distinct_compatible_circuits':len(compatible_seeds),'active_frontier_circuits':len(bottom['seeds']),'compatible_tail_circuits':compatible_seeds,'results':scans})
    for identifier in ('aes_sbox_bottom','fox_mu4','joltik'):
        target=json.loads((ROOT/(identifier+'.json')).read_text())
        for seed in target['seeds']:
            path=SEARCH/seed['path'];circuit=json.loads(path.read_text());exported=path.with_suffix('.ncff')
            exported.write_text(ncff(circuit,target));seed['ncff_path']=str(exported.relative_to(SEARCH))
        save(ROOT/(identifier+'.json'),target)
        print(identifier,target['input_count'],target['output_count'],[(x['gates'],x['depth']) for x in target['seeds']],flush=True)


if __name__=='__main__':main()
