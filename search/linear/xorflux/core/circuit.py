"""Circuit model, independent verifier, normalisation, DAG hash and JSON / NCFF io.

Role in the method
------------------
The search kernel (``core.valueset``) is valid by construction, so nothing is verified per
proposal.  Every circuit that leaves the search -- a record, a checkpointed best, an imported
seed -- goes through ``verify`` here first.  ``verify`` deliberately shares no code with the
kernel: it replays the gate list as masks from scratch, so a kernel bug cannot certify itself.

Circuit JSON (records, seeds): ``gates`` (operand index pairs; signal i < n is input i, gate k
produces signal n + k), optional ``outputSignals`` (signal per target row) and metadata such as
``benchmark``, ``inputCount``, ``gateCount`` and ``depth``.  ``dag_sha256``, ``circuit_sha256``,
``value_set_sha256``, ``normalise`` and ``ncff`` are bit-identical to the reference verifier of
earlier versions (``tests/data/legacy_golden.json``) so hashes and files match earlier runs.  One
extension: output index -1 denotes a constant-zero output (a zero target row), which needs no
gate.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

OUTPUT_KEYS = ('outputSignals', 'outputs', 'output_signals')
INPUT_KEYS = ('inputCount', 'input_count', 'n_inputs')
ZERO_OUTPUT = -1        # output index of a constant-zero row


def _packed(value):
    """Canonical JSON bytes used by every hash (sorted keys, no spaces)."""
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def matrix_sha256(input_count, rows):
    """Canonical target hash, identical to earlier versions."""
    return hashlib.sha256(_packed({'input_count': input_count, 'rows': list(rows)})).hexdigest()


def _target_info(target):
    """(n_inputs, rows, name, matrix_sha256, affine constants) of a Target, an old-style target
    dict or an ``(n_inputs, rows)`` pair."""
    if isinstance(target, tuple) and len(target) == 2 and isinstance(target[0], int):
        n, rows = target[0], [int(r) for r in target[1]]
        return n, rows, 'custom', matrix_sha256(n, rows), None
    if isinstance(target, dict):
        n, rows = target['input_count'], list(target['rows'])
        return (n, rows, target.get('id', 'custom'), matrix_sha256(n, rows),
                target.get('affine_output_constants'))
    meta = getattr(target, 'meta', {}) or {}
    return (target.n_inputs, list(target.rows), target.name, target.matrix_sha256,
            meta.get('affine_output_constants'))


# --------------------------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------------------------
@dataclass
class Circuit:
    """An XOR straight-line program.

    ``gates[k] = (a, b)`` produces signal ``n_inputs + k`` = signal a XOR signal b, with
    a, b < n_inputs + k.  ``outputs[i]`` is the signal of target row i (-1: constant zero), or
    None to let the verifier infer the shallowest signal per row.  ``meta`` keeps every other
    JSON field (id, benchmark, provenance, ...) for round trips.
    """
    n_inputs: int
    gates: list
    outputs: list | None = None
    meta: dict = field(default_factory=dict)

    @property
    def gate_count(self):
        """Number of gates (dead ones included)."""
        return len(self.gates)

    def masks(self):
        """Mask of every signal (inputs first).  Raises ValueError on a malformed gate list."""
        return _evaluate(self.gates, self.n_inputs)[0]

    def depths(self):
        """Depth of every signal (inputs 0)."""
        return _evaluate(self.gates, self.n_inputs)[1]

    # ------------------------------------------------------------------------ json
    def to_json(self, target=None, verdict=None, **extra):
        """Record-format dict: ``benchmark``, ``inputCount``, ``gates``, ``outputSignals``,
        ``gateCount``, ``depth`` (and ``affine_output_constants`` / ``scope`` with a target, as
        earlier versions wrote them), then ``meta`` and ``extra``.

        ``outputs`` and ``depth`` come from ``verdict`` (or a fresh ``verify`` when a target is
        given) so inferred outputs are written explicitly.
        """
        out = {}
        outputs = self.outputs
        depth = None
        if target is not None:
            n, rows, name, _, affine = _target_info(target)
            if verdict is None:
                verdict = verify(self, target)
            out['benchmark'] = name
        if verdict is not None and verdict.equivalent:
            outputs = verdict.outputs
            depth = verdict.depth
        out['inputCount'] = self.n_inputs
        out['gates'] = [[a, b] for a, b in self.gates]
        if outputs is not None:
            out['outputSignals'] = list(outputs)
        out['gateCount'] = len(self.gates)
        if depth is not None:
            out['depth'] = depth
        if target is not None:
            affine = affine if affine is not None else [0] * len(rows)
            out['affine_output_constants'] = list(affine)
            out['scope'] = 'linear part only' if any(affine) else 'linear map'
        for key, value in self.meta.items():
            out.setdefault(key, value)
        out.update(extra)
        return out

    @classmethod
    def from_json(cls, data, n_inputs=None):
        """Circuit from a record / seed / engine JSON dict.

        Accepts ``inputCount``/``input_count``/``n_inputs`` (or the ``n_inputs`` argument),
        outputs under ``outputSignals``/``outputs``/``output_signals`` (a list or a
        ``{"0": ..}`` dict), also inside ``provenance``; outputs are left None when absent.
        """
        if not isinstance(data, dict) or not isinstance(data.get('gates'), list):
            raise ValueError('circuit JSON needs a "gates" list')
        n = None
        for key in INPUT_KEYS:
            if key in data:
                n = data[key]
                break
        if n is None:
            n = n_inputs
        elif n_inputs is not None and n != n_inputs:
            raise ValueError('circuit has %r inputs, expected %d' % (n, n_inputs))
        if type(n) is not int or n <= 0:
            raise ValueError('circuit input count unknown or invalid')
        gates = []
        for i, pair in enumerate(data['gates']):
            if (not isinstance(pair, (list, tuple)) or len(pair) != 2
                    or any(type(x) is not int for x in pair)):
                raise ValueError('gate %d is not an index pair' % i)
            gates.append((pair[0], pair[1]))
        outputs = _read_outputs(data)
        if outputs is None and isinstance(data.get('provenance'), dict):
            outputs = _read_outputs(data['provenance'])
        meta = {k: v for k, v in data.items()
                if k not in ('gates', 'gateCount', 'depth') and k not in OUTPUT_KEYS
                and k not in INPUT_KEYS}
        return cls(n, gates, outputs, meta)

    @classmethod
    def load(cls, path, n_inputs=None):
        """Read a circuit file: JSON by default, NCFF for ``.ncff`` / ``.circ.txt``."""
        path = Path(path)
        text = path.read_text()
        if path.suffix == '.ncff' or path.name.endswith('.circ.txt') or text.lstrip().startswith('%NCFF'):
            circuit = parse_ncff(text)
            if n_inputs is not None and circuit.n_inputs != n_inputs:
                raise ValueError('circuit has %d inputs, expected %d' % (circuit.n_inputs, n_inputs))
            return circuit
        return cls.from_json(json.loads(text), n_inputs)

    def save(self, path, target=None, **extra):
        """Write ``to_json(target, **extra)`` as indented JSON."""
        Path(path).write_text(json.dumps(self.to_json(target, **extra), indent=2) + '\n')


def _read_outputs(data):
    found = None
    for key in OUTPUT_KEYS:
        if key not in data:
            continue
        value = data[key]
        if isinstance(value, dict):
            try:
                value = [value[str(i)] for i in range(len(value))]
            except KeyError:
                raise ValueError('output map %s is not indexed 0..k-1' % key) from None
        if not isinstance(value, list) or any(type(x) is not int for x in value):
            raise ValueError('malformed output map ' + key)
        if found is not None and value != found:
            raise ValueError('conflicting output maps')
        found = value
    return found


def _evaluate(gates, n):
    """Replay masks and depths; ValueError on a malformed or non-topological gate."""
    masks = [1 << i for i in range(n)]
    depths = [0] * n
    for i, pair in enumerate(gates):
        try:
            a, b = pair
        except (TypeError, ValueError):
            raise ValueError('gate %d is not a pair' % i) from None
        limit = n + i
        if type(a) is not int or type(b) is not int or not (0 <= a < limit and 0 <= b < limit):
            raise ValueError('invalid or non-topological gate %d' % i)
        masks.append(masks[a] ^ masks[b])
        da = depths[a]
        db = depths[b]
        depths.append(1 + (da if da > db else db))
    return masks, depths


def _as_circuit(circuit, n):
    if isinstance(circuit, Circuit):
        return circuit
    if isinstance(circuit, dict):
        return Circuit.from_json(circuit, n)
    return Circuit(n, [tuple(p) for p in circuit])


# --------------------------------------------------------------------------------------------
# Verification
# --------------------------------------------------------------------------------------------
@dataclass
class Verdict:
    """Result of ``verify``.

    ``equivalent``      every target row is produced (explicit outputs must match exactly)
    ``within_cap``      output depth <= cap (True when no cap)
    ``ok``              equivalent and within_cap
    ``gate_count``      all gates; ``live_gates`` reachable from the outputs; ``dead_gates`` rest
    ``depth``           max output depth (0 if every row is free)
    ``outputs``         signal per row (explicit or inferred shallowest; -1 = zero row)
    ``dag_sha256``      over all gates, as earlier versions (None if two signals share a mask)
    ``reason``          why it is not ok (None when ok)
    """
    equivalent: bool
    within_cap: bool
    gate_count: int
    live_gates: int
    dead_gates: int
    depth: int
    outputs: list
    outputs_inferred: bool
    dag_sha256: str | None
    circuit_sha256: str | None
    value_set_sha256: str | None
    matrix_sha256: str
    cap: int | None
    reason: str | None = None

    @property
    def ok(self):
        return self.equivalent and self.within_cap

    def to_dict(self):
        """JSON-safe dict (adds ``ok``)."""
        out = dict(self.__dict__)
        out['ok'] = self.ok
        return out


def _fail(reason, n_gates, matrix_digest, cap):
    return Verdict(False, False, n_gates, 0, n_gates, 0, [], False, None, None, None,
                   matrix_digest, cap, reason)


def verify(circuit, target, cap=None):
    """Independently check that ``circuit`` computes ``target`` (and fits ``cap``).

    ``circuit`` is a ``Circuit``, a circuit JSON dict or a gate list; ``target`` a ``Target``,
    an old-style target dict or ``(n_inputs, rows)``.  Never raises on a bad circuit: problems
    are reported in ``Verdict.reason``.  A bad ``cap`` argument raises ValueError.
    """
    if cap is not None and (type(cap) is not int or cap < 0):
        raise ValueError('depth cap must be a nonnegative int')
    n, rows, _, digest, _ = _target_info(target)
    try:
        circuit = _as_circuit(circuit, n)
    except ValueError as exc:
        return _fail(str(exc), 0, digest, cap)
    gates = circuit.gates
    if circuit.n_inputs != n:
        return _fail('circuit has %d inputs, target %d' % (circuit.n_inputs, n),
                     len(gates), digest, cap)
    try:
        masks, depths = _evaluate(gates, n)
    except ValueError as exc:
        return _fail(str(exc), len(gates), digest, cap)
    outputs = circuit.outputs
    inferred = outputs is None
    reason = None
    if inferred:
        best = {}
        for i, value in enumerate(masks):
            j = best.get(value)
            if j is None or depths[i] < depths[j]:
                best[value] = i
        outputs = []
        for row in rows:
            if row == 0:
                outputs.append(ZERO_OUTPUT)
            elif row in best:
                outputs.append(best[row])
            else:
                reason = 'no signal computes target row %d' % len(outputs)
                outputs = []
                break
    else:
        outputs = list(outputs)
        if len(outputs) != len(rows):
            reason = 'output map has %d entries for %d rows' % (len(outputs), len(rows))
        else:
            for i, (x, row) in enumerate(zip(outputs, rows)):
                if x == ZERO_OUTPUT and row == 0:
                    continue
                if not 0 <= x < len(masks):
                    reason = 'output %d index %d out of range' % (i, x)
                    break
                if masks[x] != row:
                    reason = 'output %d does not equal its target row' % i
                    break
    equivalent = reason is None
    if not equivalent:
        outputs = []
    signals = [x for x in outputs if x != ZERO_OUTPUT]
    depth = max((depths[x] for x in signals), default=0)
    within = cap is None or not equivalent or depth <= cap
    if equivalent and not within:
        reason = 'output depth %d exceeds cap %d' % (depth, cap)
    live = set(signals)
    todo = [x for x in live if x >= n]
    while todo:
        index = todo.pop()
        for parent in gates[index - n]:
            if parent not in live:
                live.add(parent)
                if parent >= n:
                    todo.append(parent)
    live_gates = sum(1 for x in live if x >= n)
    unique = len(set(masks)) == len(masks)
    dag = None
    if unique:
        triples = sorted((masks[n + i], *sorted((masks[a], masks[b])))
                         for i, (a, b) in enumerate(gates))
        dag = hashlib.sha256(_packed({'matrix_sha256': digest, 'triples': triples})).hexdigest()
    body = {'input_count': n, 'rows': rows, 'gates': [sorted(pair) for pair in gates],
            'outputs': outputs}
    return Verdict(equivalent, within and equivalent, len(gates), live_gates,
                   len(gates) - live_gates, depth, outputs, inferred, dag,
                   hashlib.sha256(_packed(body)).hexdigest(),
                   hashlib.sha256(_packed(sorted(set(masks[n:])))).hexdigest(),
                   digest, cap, reason)


def dag_sha256(circuit, target):
    """DAG hash over all gates: SHA-256 of ``{"matrix_sha256", "triples"}`` where each gate
    contributes (value, smaller operand, larger operand) masks, sorted.  ``target`` is a
    Target-like object or the matrix hash string (then ``circuit`` must carry its input count:
    a ``Circuit`` or a circuit JSON dict).  None if two signals share a mask."""
    if isinstance(target, str):
        digest = target
        if isinstance(circuit, dict):
            circuit = Circuit.from_json(circuit)        # any of the accepted input-count keys
        elif not isinstance(circuit, Circuit):
            raise ValueError('a bare gate list needs a target, not only its matrix hash')
        n = circuit.n_inputs
    else:
        n, _, _, digest, _ = _target_info(target)
    circuit = _as_circuit(circuit, n)
    masks = _evaluate(circuit.gates, circuit.n_inputs)[0]
    if len(set(masks)) != len(masks):
        return None
    m = circuit.n_inputs
    triples = sorted((masks[m + i], *sorted((masks[a], masks[b])))
                     for i, (a, b) in enumerate(circuit.gates))
    return hashlib.sha256(_packed({'matrix_sha256': digest, 'triples': triples})).hexdigest()


# --------------------------------------------------------------------------------------------
# Normalisation
# --------------------------------------------------------------------------------------------
def normalise(circuit, target):
    """Live DAG only, each value rebuilt from its shallowest recipe, emitted depth-first from
    the outputs in row order (smaller operand mask first).  Gate order and pairs are identical
    to earlier versions.  Raises ValueError if a row is not computed."""
    n, rows, _, _, _ = _target_info(target)
    circuit = _as_circuit(circuit, n)
    gates = circuit.gates
    masks, depths = _evaluate(gates, circuit.n_inputs)
    best = {}
    for i, value in enumerate(masks):
        j = best.get(value)
        if j is None or depths[i] < depths[j]:
            best[value] = i
    if any(row and row not in best for row in rows):
        raise ValueError('circuit does not compute every target row')
    emitted = {1 << i: i for i in range(n)}
    result = []
    # Iterative post-order DFS (recursion would overflow on deep 1000-gate circuits).
    for row in rows:
        if row == 0 or row in emitted:
            continue
        stack = [[row, 0, None]]
        while stack:
            frame = stack[-1]
            value = frame[0]
            if frame[2] is None:
                a, b = gates[best[value] - n]
                frame[2] = sorted((masks[a], masks[b]))
            step = frame[1]
            if step < 2:
                frame[1] = step + 1
                parent = frame[2][step]
                if parent not in emitted:
                    stack.append([parent, 0, None])
                continue
            pa, pb = frame[2]
            emitted[value] = n + len(result)
            result.append((emitted[pa], emitted[pb]))
            stack.pop()
    outputs = [ZERO_OUTPUT if row == 0 else emitted[row] for row in rows]
    return Circuit(n, result, outputs, dict(circuit.meta))


# --------------------------------------------------------------------------------------------
# NCFF
# --------------------------------------------------------------------------------------------
def ncff(circuit, target):
    """NCFF text of a circuit, identical to earlier versions.  Zero rows cannot be
    expressed in NCFF and raise ValueError, as does a circuit that does not verify."""
    n, rows, name, digest, affine = _target_info(target)
    circuit = _as_circuit(circuit, n)
    info = verify(circuit, target)
    if not info.equivalent:
        raise ValueError('cannot export a circuit that does not verify: %s' % info.reason)
    if ZERO_OUTPUT in info.outputs:
        raise ValueError('NCFF has no constant outputs (zero target row)')
    names = {i: 'x' + str(i) for i in range(n)}
    for i, index in enumerate(info.outputs):
        if index >= n and index not in names:
            names[index] = 'y' + str(i)
    internal = []
    for i in range(n, n + len(circuit.gates)):
        if i not in names:
            names[i] = 't' + str(len(internal))
            internal.append(names[i])
    identity = re.sub(r'[^A-Za-z0-9_-]', '_', name or 'custom')
    lines = ['%NCFF-0.1-2026 (NIST Circuit File Format)',
             '% Exported by xorflux; not a NIST-issued circuit.',
             'begin circuit ' + identity,
             '% Linear target matrix SHA-256: ' + digest,
             '% Gates: ' + str(info.gate_count) + ' XOR; output depth: ' + str(info.depth)]
    if affine and any(affine):
        lines.append('% Linear part only; excluded affine output constants: '
                     + ' '.join(map(str, affine)))
    lines += ['Inputs: ' + ' '.join(names[i] for i in range(n)),
              'Outputs: ' + ' '.join(names[i] for i in info.outputs),
              'Internal: ' + ' '.join(internal),
              'GateSyntax: GateName Output Inputs', 'begin SLP']
    lines += ['XOR ' + names[n + i] + ' ' + names[a] + ' ' + names[b]
              for i, (a, b) in enumerate(circuit.gates)]
    return '\n'.join(lines + ['end SLP', 'end circuit', ''])


def _expand_names(spec):
    names = []
    for token in spec.split():
        if ':' not in token:
            names.append(token)
            continue
        match = re.fullmatch(r'([A-Za-z_]+)(\d+):([A-Za-z_]+)(\d+)', token)
        if not match or match[1] != match[3] or int(match[2]) > int(match[4]):
            raise ValueError('invalid NCFF wire range: ' + token)
        names.extend(match[1] + str(i) for i in range(int(match[2]), int(match[4]) + 1))
    return names


def parse_ncff(text):
    """Circuit from an XOR-only NCFF program (any input/output count; ``x0:x31`` ranges)."""
    inputs = outputs = None
    active = False
    operations = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith('Inputs:'):
            inputs = _expand_names(line.partition(':')[2])
        elif line.startswith('Outputs:'):
            outputs = _expand_names(line.partition(':')[2])
        elif line == 'begin SLP':
            active = True
        elif line == 'end SLP':
            active = False
        elif active and line and not line.startswith(('%', '#')):
            parts = line.split()
            if len(parts) != 4 or parts[0] != 'XOR':
                raise ValueError('not an XOR-only NCFF instruction: ' + line)
            operations.append(parts[1:])
    if inputs is None or outputs is None or len(set(inputs)) != len(inputs):
        raise ValueError('NCFF needs explicit, distinct Inputs and an Outputs line')
    wire = {name: i for i, name in enumerate(inputs)}
    n = len(inputs)
    gates = []
    for out, a, b in operations:
        if out in wire or a not in wire or b not in wire:
            raise ValueError('non-SSA or non-topological NCFF instruction: ' + out)
        wire[out] = n + len(gates)
        gates.append((wire[a], wire[b]))
    missing = [name for name in outputs if name not in wire]
    if missing:
        raise ValueError('NCFF output never assigned: ' + missing[0])
    return Circuit(n, gates, [wire[name] for name in outputs])
