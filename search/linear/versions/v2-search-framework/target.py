"""Exact arbitrary-dimension XOR targets. Inputs have depth zero.

verify accepts gates-only engine candidates and infers outputs. Explicit output
maps must match the target in order. cap limits output depth, not unused gates.
normalise emits the live DAG using the shallowest available recipe per value.
Target seeds use paths relative to SEARCH_ROOT; target_path resolves target IDs.
"""
from pathlib import Path
import hashlib
import json
import re

SEARCH_ROOT = Path(__file__).resolve().parent
TARGET_ROOT = SEARCH_ROOT / 'targets'
IDS = ('aes_sbox_bottom', 'fox_mu4', 'joltik')
VERIFIER_VERSION = 'xor-linear-target-verifier-1'
VERIFIER_SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _packed(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def matrix_sha256(input_count, rows):
    return hashlib.sha256(_packed({'input_count': input_count, 'rows': rows})).hexdigest()


def target_path(id_or_path):
    """Resolve a built-in ID or a JSON path independently of the caller's cwd."""
    value = str(id_or_path)
    if value in IDS:
        return TARGET_ROOT / (value + '.json')
    path = Path(id_or_path).expanduser()
    for candidate in (path, SEARCH_ROOT/path, TARGET_ROOT/path):
        if candidate.is_file():
            return candidate.resolve()
    raise ValueError('Unknown target ID or JSON path: ' + value)


def _validated_target(target):
    if not isinstance(target, dict):
        target = load_target(target)
    n = target.get('input_count')
    rows = target.get('rows')
    if type(n) is not int or n <= 0 or not isinstance(rows, list) or not rows:
        raise ValueError('Target requires positive input_count and nonempty rows')
    if any(type(row) is not int or not 0 <= row < (1 << n) for row in rows):
        raise ValueError('Target row outside its declared input dimension')
    if type(target.get('output_count')) is not int or target['output_count'] != len(rows):
        raise ValueError('Target output_count differs from its rows')
    affine = target.get('affine_output_constants', [0]*len(rows))
    if (not isinstance(affine, list) or len(affine) != len(rows)
            or any(type(x) is not int or x not in (0, 1) for x in affine)):
        raise ValueError('Target affine output constants are malformed')
    digest = matrix_sha256(n, rows)
    if target.get('matrix_sha256', digest) != digest:
        raise ValueError('Target matrix hash mismatch')
    return target


def load_target(id_or_path):
    path = target_path(id_or_path)
    result = _validated_target(json.loads(path.read_text()))
    result['target_path'] = str(path)
    return result


def _evaluate(gates, n):
    if not isinstance(gates, (list, tuple)):
        raise ValueError('gates must be a sequence of operand pairs')
    masks = [1 << i for i in range(n)]
    depths = [0] * n
    for i, pair in enumerate(gates):
        if (not isinstance(pair, (list, tuple)) or len(pair) != 2
                or any(type(a) is not int or not 0 <= a < n+i for a in pair)):
            raise ValueError('Invalid or non-topological gate ' + str(i))
        a, b = pair
        masks.append(masks[a] ^ masks[b])
        depths.append(1 + max(depths[a], depths[b]))
    return masks, depths


def _explicit_outputs(circuit, count):
    found = []
    for key in ('outputSignals', 'outputs', 'output_signals'):
        if key not in circuit:
            continue
        value = circuit[key]
        if isinstance(value, dict) and set(value) == {str(i) for i in range(count)}:
            value = [value[str(i)] for i in range(count)]
        if not isinstance(value, list) or len(value) != count or any(type(x) is not int for x in value):
            raise ValueError('Malformed explicit output map: ' + key)
        found.append(value)
    if found and any(value != found[0] for value in found[1:]):
        raise ValueError('Conflicting explicit output maps')
    return found[0] if found else None


def verify(circuit, target, cap=None):
    target = _validated_target(target)
    n, rows = target['input_count'], target['rows']
    if not isinstance(circuit, dict) or 'gates' not in circuit:
        raise ValueError('Circuit must contain gates')
    for key in ('inputCount', 'input_count', 'n_inputs'):
        if key in circuit and (type(circuit[key]) is not int or circuit[key] != n):
            raise ValueError('Circuit input dimension mismatch')
    if 'benchmark' in circuit and circuit['benchmark'] != target.get('id', 'custom'):
        raise ValueError('Circuit benchmark identity mismatch')
    if 'affine_output_constants' in circuit:
        declared = circuit['affine_output_constants']
        expected = target.get('affine_output_constants', [0]*len(rows))
        if (not isinstance(declared, list) or any(type(x) is not int or x not in (0, 1) for x in declared)
                or declared != expected):
            raise ValueError('Circuit affine output constants mismatch')
    gates = circuit['gates']
    masks, depths = _evaluate(gates, n)
    outputs = _explicit_outputs(circuit, len(rows))
    inferred = outputs is None
    if inferred:
        best = {}
        for i, value in enumerate(masks):
            if value not in best or (depths[i], i) < (depths[best[value]], best[value]):
                best[value] = i
        equivalent = all(row in best for row in rows)
        outputs = [best[row] for row in rows] if equivalent else []
    else:
        if any(not 0 <= x < len(masks) for x in outputs):
            raise ValueError('Explicit output index out of range')
        if [masks[x] for x in outputs] != rows:
            raise ValueError('Explicit output map does not equal target rows')
        equivalent = True
    depth = max((depths[i] for i in outputs), default=0)
    if cap is not None:
        if type(cap) is not int or cap < 0:
            raise ValueError('Depth cap must be a nonnegative integer')
        if equivalent and depth > cap:
            raise ValueError('Circuit exceeds output depth cap')
    live, todo = set(outputs), list(outputs)
    while todo:
        index = todo.pop()
        if index >= n:
            for parent in gates[index-n]:
                if parent not in live:
                    live.add(parent)
                    todo.append(parent)
    unique_values = len(set(masks)) == len(masks)
    triples = sorted((masks[n+i], *sorted((masks[a], masks[b])))
                     for i, (a, b) in enumerate(gates))
    dag_digest = (hashlib.sha256(_packed({'matrix_sha256': matrix_sha256(n, rows),
                                        'triples': triples})).hexdigest()
                  if unique_values else None)
    body = {'input_count': n, 'rows': rows,
            'gates': [sorted(pair) for pair in gates], 'outputs': outputs}
    return {'gate_count': len(gates), 'depth': depth, 'outputs': outputs,
            'masks': masks, 'dead_gates': sum(n+i not in live for i in range(len(gates))),
            'equivalent': equivalent, 'outputs_inferred': inferred,
            'dag_sha256': dag_digest,
            'verifier_version': VERIFIER_VERSION, 'verifier_source_sha256': VERIFIER_SOURCE_SHA256,
            'circuit_sha256': hashlib.sha256(_packed(body)).hexdigest(),
            'value_set_sha256': hashlib.sha256(_packed(sorted(set(masks[n:])))).hexdigest()}


def normalise(gates, target):
    target = _validated_target(target)
    n = target['input_count']
    masks, depths = _evaluate(gates, n)
    best = {}
    for i, value in enumerate(masks):
        if value not in best or (depths[i], i) < (depths[best[value]], best[value]):
            best[value] = i
    if any(row not in best for row in target['rows']):
        raise ValueError('Candidate does not contain every target output')
    emitted = {1 << i: i for i in range(n)}
    result = []

    def emit(value):
        if value in emitted:
            return emitted[value]
        original = best[value]
        parent_values = sorted(masks[x] for x in gates[original-n])
        pair = [emit(parent) for parent in parent_values]
        emitted[value] = n + len(result)
        result.append(pair)
        return emitted[value]

    outputs = [emit(row) for row in target['rows']]
    circuit = {'benchmark': target.get('id', 'custom'), 'inputCount': n,
               'gates': result, 'outputSignals': outputs}
    info = verify(circuit, target)
    circuit.update(gateCount=info['gate_count'], depth=info['depth'],
                   affine_output_constants=target.get('affine_output_constants', [0]*len(target['rows'])),
                   scope='linear part only' if any(target.get('affine_output_constants', [])) else 'linear map')
    return circuit


def ncff(circuit, target):
    target = _validated_target(target)
    info = verify(circuit, target)
    if not info['equivalent']:
        raise ValueError('Cannot export a circuit missing target outputs')
    n = target['input_count']
    names = {i: 'x'+str(i) for i in range(n)}
    for i, index in enumerate(info['outputs']):
        if index >= n and index not in names:
            names[index] = 'y'+str(i)
    internal = []
    for i in range(n, n+len(circuit['gates'])):
        if i not in names:
            names[i] = 't'+str(len(internal))
            internal.append(names[i])
    identity = re.sub(r'[^A-Za-z0-9_-]', '_', target.get('id', 'custom'))
    lines = ['%NCFF-0.1-2026 (NIST Circuit File Format)',
             '% Exported by xor-circuit-lab; not a NIST-issued circuit.',
             'begin circuit '+identity,
             '% Linear target matrix SHA-256: '+matrix_sha256(n, target['rows']),
             '% Gates: '+str(info['gate_count'])+' XOR; output depth: '+str(info['depth'])]
    if any(target.get('affine_output_constants', [])):
        lines.append('% Linear part only; excluded affine output constants: '+
                     ' '.join(map(str, target['affine_output_constants'])))
    lines += ['Inputs: '+' '.join(names[i] for i in range(n)),
              'Outputs: '+' '.join(names[i] for i in info['outputs']),
              'Internal: '+' '.join(internal),
              'GateSyntax: GateName Output Inputs', 'begin SLP']
    lines += ['XOR '+names[n+i]+' '+names[a]+' '+names[b]
              for i, (a, b) in enumerate(circuit['gates'])]
    return '\n'.join(lines+['end SLP', 'end circuit', ''])
