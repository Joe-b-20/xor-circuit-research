"""Bounded inverse-target adapter/resume checks; not a search-quality benchmark."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from search import engine_api as api
from search import target as oracle


def main():
    root = Path(__file__).resolve().parents[1]
    profile_path = root / 'configs/invmixcolumns-13.json'
    profile = json.loads(profile_path.read_text())
    target = oracle.load_target('invmixcolumns')
    results = []
    for seed_index, cap in ((0, 5), (4, 9), (7, 19)):
        path = root / target['seeds'][seed_index]['path']
        seed = json.loads(path.read_text())
        for engine in api.available_engines():
            scope = api.engine_applicability(target, engine, cap)
            entry = {'engine': engine, 'depth_cap': cap, **scope,
                     'seed_path': path.relative_to(root).as_posix(),
                     'seed_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            if not scope['applicable']:
                results.append(entry)
                continue
            checked_candidates = []

            def candidate(gates, note=None, metrics=None):
                checked = oracle.verify({'gates': gates}, target, cap=cap)
                assert checked['equivalent'] and checked['dead_gates'] == 0
                checked_candidates.append([checked['gate_count'], checked['depth']])
                return True

            knobs = {**profile['engine_knobs'].get(engine, {}), 'max_iterations': 2}
            first = api.run_chunk(target, engine, seed['gates'], seed=20261028,
                                  seconds=.6, depth_cap=cap, knobs=knobs, on_candidate=candidate)
            resumed = api.run_chunk(target, engine, first['gates'], seed=0,
                                    seconds=.3, depth_cap=cap,
                                    knobs={**knobs, 'max_iterations': 1},
                                    state=json.loads(json.dumps(first['state'])),
                                    on_candidate=candidate)
            for result in (first, resumed):
                for gates in (result['gates'], result['state']['best_gates']):
                    assert oracle.verify({'gates': gates}, target, cap=cap)['equivalent']
            assert resumed['metrics']['resumed_rng']
            entry.update(knobs=knobs, metrics=first['metrics'], resume_metrics=resumed['metrics'],
                         checked_candidates=checked_candidates)
            results.append(entry)
            print(cap, engine, 'proposals', first['metrics']['proposals'],
                  'resumed', resumed['metrics']['proposals'], flush=True)
    receipt = {'purpose': 'Bounded target, adapter and RNG-resume checks; not a discovery-rate benchmark',
               'created_utc': datetime.now(timezone.utc).isoformat(),
               'matrix_sha256': target['matrix_sha256'],
               'profile_sha256': hashlib.sha256(profile_path.read_bytes()).hexdigest(),
               'api_sha256': hashlib.sha256(Path(api.__file__).read_bytes()).hexdigest(),
               'verifier_sha256': hashlib.sha256(Path(oracle.__file__).read_bytes()).hexdigest(),
               'random_seed': 20261028, 'seconds': .6, 'resume_seconds': .3,
               'results': results}
    (root / 'engines/invmixcolumns-smoke.json').write_text(json.dumps(receipt, indent=2) + '\n')


if __name__ == '__main__':
    main()
