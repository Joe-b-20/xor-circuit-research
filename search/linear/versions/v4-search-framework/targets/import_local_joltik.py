#!/usr/bin/env python3
"""Import the earliest genuine 43-XOR/depth-8 Joltik discovery, not a NIST seed."""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,shutil,sys,tarfile

SEARCH=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SEARCH.parent))
from search.target import load_target,verify,ncff
ROOT=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def digest(value):return hashlib.sha256((json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()).hexdigest()

def read(path):return json.loads(path.read_text())

def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',nargs='?',type=Path,default=SEARCH/'runs/three-targets20')
    args=parser.parse_args();run=args.run.resolve();config=read(run/'config.json')
    accepted=(run/'config.sha256').read_text().strip()
    assert digest(config)==accepted and sha(run/'source.tar.gz')==config['source']['archive_sha256']
    assert digest(config['source']['files'])==config['source']['manifest_sha256']
    with tarfile.open(run/'source.tar.gz','r:gz') as archive:
        members=archive.getmembers();expected={'search/'+path:value for path,value in config['source']['files'].items()}
        assert {entry.name for entry in members}==set(expected)
        for entry in members:
            assert entry.isfile();assert hashlib.sha256(archive.extractfile(entry).read()).hexdigest()==expected[entry.name]
    for path,expected in config['source']['files'].items():assert sha(run/'source/search'/path)==expected
    events=[];log_inventory=[]
    for logfile in sorted(run.glob('workers/joltik-*/discoveries.jsonl')):
        log_inventory.append({'path':logfile.relative_to(run).as_posix(),'sha256':sha(logfile),'bytes':logfile.stat().st_size})
        for line_no,line in enumerate(logfile.read_text().splitlines(),1):
            event=json.loads(line);record=event.get('record',{})
            if event.get('event')=='new_search_record' and (record.get('gate_count'),record.get('depth'))==(43,8):
                path=(run/record['path']).resolve();assert path.is_relative_to(run)
                obj=read(path);metadata=obj['metadata']
                assert metadata['origin']=='new_search_record' and metadata['run_id']==config['run_id']
                assert metadata['worker']==record['worker'] and sha(path)==record['file_sha256']
                events.append((event['utc'],record['path'],event,logfile,line_no))
    assert events;events.sort(key=lambda value:(value[0],value[1]));utc,relative,event,logfile,line_no=events[0]
    original=run/relative;record=read(original);metadata=record['metadata'];worker=metadata['worker']
    expected_binding={'run_id':config['run_id'],'worker':worker,'target_id':'joltik','config_sha256':accepted,
                      'source_manifest_sha256':config['source']['manifest_sha256']}
    assert all(metadata[key]==value for key,value in expected_binding.items())
    frozen_spec=importlib.util.spec_from_file_location('local_joltik_frozen_verifier',run/'source/search/target.py')
    frozen=importlib.util.module_from_spec(frozen_spec);frozen_spec.loader.exec_module(frozen)
    oldtarget=config['targets']['joltik']['definition'];current=load_target('joltik')
    oldcheck=frozen.verify(record,oldtarget,cap=8);fresh=verify(record,current,cap=8)
    assert (fresh['gate_count'],fresh['depth'],fresh['dead_gates'],fresh['equivalent'])==(43,8,0,True)
    assert oldcheck==read(original.with_suffix('.verification.json'))
    assert original.with_suffix('.ncff').read_text()==frozen.ncff(record,oldtarget)==ncff(record,current)
    rng=read(original.with_suffix('.rng-start.json'))
    assert all(rng[key]==value for key,value in expected_binding.items())
    assert rng['engine']==metadata['engine'] and rng['chunk']==metadata['chunk']
    assert metadata['chunk_start_state_path']==original.with_suffix('.rng-start.json').relative_to(run).as_posix()
    program_hash=fresh['circuit_sha256'];folder=ROOT/'local'/('joltik_g43_d8_'+program_hash[:12]);folder.mkdir(parents=True,exist_ok=True)
    paths=['source.tar.gz','config.json','config.sha256','status.json',logfile.relative_to(run).as_posix(),
           'sessions/'+event['owner_token']+'.json','workers/'+worker+'/environment.json',
           'workers/'+worker+'/environments/'+event['owner_token']+'.json','workers/'+worker+'/worker.log',
           config['targets']['joltik']['matrix_snapshot']['path']]
    paths += [item['path'] for item in log_inventory]
    paths += [original.with_suffix(suffix).relative_to(run).as_posix() for suffix in ('.json','.ncff','.verification.json','.rng-start.json')]
    paths += [seed['path'] for seed in config['targets']['joltik']['seed_snapshots']]
    copies=[]
    for relative_path in dict.fromkeys(paths):
        source=run/relative_path;destination=folder/'original'/relative_path
        destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
        assert sha(source)==sha(destination)
        copies.append({'source_path':relative_path,'preserved_path':destination.relative_to(folder).as_posix(),
                       'sha256':sha(destination),'bytes':destination.stat().st_size})
    write(folder/'discovery_event.json',event)
    origin={'kind':'local_search_record_import','not_a_nist_record':True,'imported_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'origin_run_path':run.relative_to(SEARCH.parent).as_posix() if run.is_relative_to(SEARCH.parent) else str(run),
            'run_id':config['run_id'],'source_commit':config['source']['git_commit'],
            'source_commit_is_exact_snapshot':config['source']['commit_is_exact_snapshot'],
            'source_archive_sha256':config['source']['archive_sha256'],'source_manifest_sha256':config['source']['manifest_sha256'],
            'accepted_config_sha256':accepted,'original_record_path':original.relative_to(run).as_posix(),
            'original_record_sha256':sha(original),'record_saved_utc':metadata['saved_utc'],'discovery_utc':utc,
            'worker':worker,'engine':metadata['engine'],'chunk':metadata['chunk'],'engine_seed':metadata['engine_seed'],
            'matrix_sha256':current['matrix_sha256'],'circuit_sha256':program_hash,'dag_sha256':fresh['dag_sha256'],
            'selected_discovery_log_line':line_no,'discovery_logs_scanned':log_inventory,
            'qualifying_new_search_records':[{'utc':entry[0],'record_path':entry[1],'circuit_sha256':entry[2]['record']['circuit_sha256']} for entry in events],
            'preserved_files':copies,'frozen_verification_sidecar_exact_match':True,
            'rng_scope':'Original chunk-start engine/RNG state is retained. Callback-time RNG state was not recorded; no exact discovery-time state is invented.',
            'default_seed_policy':'Explicit local override only; the built-in Joltik NIST 44-XOR/depth-7 seed remains unchanged.'}
    write(folder/'origin.json',origin)
    seed={key:value for key,value in record.items() if key!='metadata'}
    seed['provenance']={'source_kind':'local search record; not NIST','origin_manifest':(folder/'origin.json').relative_to(SEARCH).as_posix(),
                        'origin_manifest_sha256':sha(folder/'origin.json'),'source_record_sha256':sha(original),
                        'source_run_id':config['run_id'],'source_commit':config['source']['git_commit'],
                        'source_archive_sha256':config['source']['archive_sha256'],'original_metadata':metadata}
    seedpath=ROOT/'seeds/joltik'/('local_g43_d8_'+program_hash[:12]+'.json')
    write(seedpath,seed);write(seedpath.with_suffix('.verification.json'),verify(seed,current,cap=8))
    seedpath.with_suffix('.ncff').write_text(ncff(seed,current))
    assert verify(read(seedpath),current,cap=8)['circuit_sha256']==program_hash
    print(seedpath.relative_to(SEARCH), '43 XOR / depth 8; origin',worker,utc,flush=True)


if __name__=='__main__':main()
