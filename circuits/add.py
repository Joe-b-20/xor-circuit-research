"""Add a circuit found by the search: python3 circuits/add.py RUN_DIR/workers/W/records/gG-dD-H.json

Writes circuits/<map>/<map>-xor<G>-depth<D>.circ.txt (NIST circuit file format) and its logs in
circuits/<map>/logs/<same name>/ (the record, the dossier of the improvement that found it, the
worker's events, the run plan, found.json), then checks the file. The map is found by matching the
circuit's outputs against every circuits/*/*.mat.txt.
"""
import argparse
import datetime
import gzip
import hashlib
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import check  # noqa: E402

ABOUT = {
    "aes-mixcolumns": ["AES MixColumns; 32-bit column; 2-input XOR basis",
                       "Description: AES MixColumns forward, compatible with NIST-FIPS 197",
                       "Interface: x_(8b+r) and y_(8b+r) are bit r (LSB=0) of byte b, b=0:3",
                       "Byte matrix: [02 03 01 01; 01 02 03 01; 01 01 02 03; 03 01 01 02]"],
    "aes-invmixcolumns": ["AES InvMixColumns; 32-bit column; 2-input XOR basis",
                          "Description: AES MixColumns inverse, compatible with NIST-FIPS 197",
                          "Interface: x_(8b+r) and y_(8b+r) are bit r (LSB=0) of byte b, b=0:3",
                          "Byte matrix: [0e 0b 0d 09; 09 0e 0b 0d; 0d 09 0e 0b; 0b 0d 09 0e]"],
    "aes-sbox-bottom": ["AES S-box bottom linear layer; 18 inputs, 8 outputs; 2-input XOR/XNOR basis",
                        "Description: y = A.x + c with A and c in aes-sbox-bottom.mat.txt"],
}


def about(name, n_in, n_out):
    return ABOUT.get(name, [f"{name}; {n_out}x{n_in} bit matrix; 2-input XOR basis",
                            f"Description: y = A.x with A in {name}.mat.txt (row i = y_i, column j = x_j)"])


def maps():
    for mat in sorted(ROOT.glob("*/*.mat.txt")):
        rows, consts, n = check.read_matrix(mat)
        yield mat.parent.name, rows, consts, n


def gates_of(rec):
    g = rec["gates"]
    return [tuple(x) for x in (json.loads(g) if isinstance(g, str) else g)]


def find_map(rec, prefer=None):
    """(name, rows, consts, n, output signals) of the map the circuit computes; ``prefer`` (the
    run's target name) is tried first, since some maps share a matrix."""
    n, gates = rec.get("inputCount"), gates_of(rec)
    for name, rows, consts, n_in in sorted(maps(), key=lambda m: m[0] != prefer):
        if n not in (None, n_in):
            continue
        val = [1 << j for j in range(n_in)]
        for a, b in gates:
            val.append(val[a] ^ val[b])
        outs = rec.get("outputSignals")
        if outs and [val[s] for s in outs] == rows:
            return name, rows, consts, n_in, list(outs)
        if not outs:
            where = {}
            for s in range(n_in, len(val)):
                where.setdefault(val[s], s)
            if all(r in where for r in rows):
                return name, rows, consts, n_in, [where[r] for r in rows]
    raise SystemExit("the circuit matches no circuits/*/*.mat.txt")


def ncff(rec, name, n, outs, consts, provenance):
    """NIST-style text: gates grouped by level, outputs named y_i, XNOR where a constant is due."""
    gates = gates_of(rec)
    assert len(set(outs)) == len(outs) and min(outs) >= n, "outputs must be distinct gates"
    depth, const, xnor = [0] * n, [0] * n, []
    want = {s: c for s, c in zip(outs, consts)}
    for a, b in gates:
        s = len(depth)
        depth.append(1 + max(depth[a], depth[b]))
        x = (want[s] ^ const[a] ^ const[b]) if s in want else 0
        xnor.append(x)
        const.append(const[a] ^ const[b] ^ x)
    order = sorted(range(len(gates)), key=lambda k: (depth[n + k], k))
    yname = {s: f"y{i}" for i, s in enumerate(outs)}
    names, t = {j: f"x{j}" for j in range(n)}, 0
    for k in order:
        if n + k not in yname:
            t += 1
        names[n + k] = yname.get(n + k) or f"t{t}"
    levels = max(depth[n:])
    per = [sum(1 for d in depth[n:] if d == L) for L in range(1, levels + 1)]
    kinds = [f"{len(gates) - sum(xnor)} XOR"] + ([f"{sum(xnor)} XNOR"] if any(xnor) else [])
    info = about(name, n, len(outs))
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    circ = f"{name}-xor{len(gates)}-depth{levels}"
    out = ["%NCFF-0.1-2026 (NIST Circuit File Format)", "", "## File source",
           f"  % Timestamp (UTC): {stamp}", "  % Not a NIST-issued circuit"]
    out += [f"  % {line}" for line in provenance]
    out += ["", "## Index of circuits (circuitName numOutputs numInputs)",
            f"  % {circ} {len(outs)} {n}   % {info[0]}", "", "## Circuit", f"begin circuit {circ}", ""]
    out += [f"  % {line}" for line in info[1:]]
    out += [f"  % Tally of variables ({n + len(gates)}): {n} inputs; {len(outs)} outputs; "
            f"{len(gates) - len(outs)} intermediates",
            f"  % Tally of gates ({len(gates)}): {'; '.join(kinds)}",
            f"  % Gate depth {levels}", f"  % Gates per gate level: {' '.join(map(str, per))}", "",
            f"Inputs: x0:x{n - 1}", f"Outputs: y0:y{len(outs) - 1}"]
    out += [f"Internal: t1:t{t}"] if t else []
    out += ["GateSyntax: GateName Output Inputs", "", "begin SLP"]
    level = 0
    for k in order:
        if depth[n + k] != level:
            level = depth[n + k]
            out.append(f"{'%' * 24} Gate level {level}")
        a, b = gates[k]
        out.append(f"{'XNOR' if xnor[k] else 'XOR'} {names[n + k]} {names[a]} {names[b]}")
    out += ["end SLP", "end circuit", ""]
    return circ, "\n".join(out)


def copy(src, dst_dir, name=None, gz=False):
    """Copy a log file into dst_dir (gzipped when gz); returns its name or None if missing."""
    src = pathlib.Path(src)
    if not src.is_file():
        return None
    name = name or src.name
    if gz:
        name += ".gz"
        with open(src, "rb") as f, open(dst_dir / name, "wb") as raw, \
                gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as g:
            shutil.copyfileobj(f, g)
    else:
        shutil.copyfile(src, dst_dir / name)
    return name


def write(rec, provenance, logs, found, force=False, prefer=None):
    """Write the circuit file and its logs folder. logs: [(src, name, gz)]; found: dict."""
    name, rows, consts, n, outs = find_map(rec, prefer)
    depth = [0] * n
    for a, b in gates_of(rec):
        depth.append(1 + max(depth[a], depth[b]))
    circ = f"{name}-xor{len(depth) - n}-depth{max(depth[n:])}"
    path = ROOT / name / f"{circ}.circ.txt"
    if path.exists() and not force:
        raise SystemExit(f"{path.relative_to(ROOT.parent)} exists (use --force to replace it)")
    _, text = ncff(rec, name, n, outs, consts, provenance + [f"Logs: logs/{circ}/"])
    log_dir = ROOT / name / "logs" / circ
    if log_dir.exists():
        shutil.rmtree(log_dir)
    log_dir.mkdir(parents=True)
    files = [f for f in (copy(src, log_dir, nm, gz) for src, nm, gz in logs) if f]
    path.write_text(text)
    found = {"circuit": path.name, **found, "circuit_sha256": hashlib.sha256(text.encode()).hexdigest(),
             "logs": sorted(files)}
    (log_dir / "found.json").write_text(json.dumps(found, indent=1) + "\n")
    res = check.check(path, rows, consts, n)
    if not isinstance(res, tuple):
        raise SystemExit(f"{path}: {res}")
    for other in path.parent.glob("*.circ.txt"):
        m = check.NAME.search(other.name)
        if other != path and m and int(m.group(1)) <= res[0] and int(m.group(2)) <= res[1]:
            print(f"note: {other.name} already has as few gates at no more depth")
    return path


def from_run(record_path, code="search/xorflux", version="latest", force=False):
    """Provenance and logs of a record written by xorflux inside a campaign run directory."""
    record_path = pathlib.Path(record_path).resolve()
    rec = json.loads(record_path.read_text())
    meta = rec.get("metadata") or {}
    worker_dir = record_path.parent.parent
    run = worker_dir.parent if (worker_dir.parent / "plan.json").exists() else worker_dir.parent.parent
    plan = json.loads((run / "plan.json").read_text()) if (run / "plan.json").exists() else {}
    dossier = None
    rel = str(record_path.relative_to(run)) if record_path.is_relative_to(run) else None
    for line in open(run / "campaign.jsonl") if (run / "campaign.jsonl").exists() else []:
        if '"frontier"' in line:
            e = json.loads(line)
            if e.get("record") == rel and e.get("improvement"):
                dossier = worker_dir / "dossiers" / f"{e['improvement']}.json"
    worker = next((w for w in plan.get("workers", []) if w["id"] == meta.get("worker")), {})
    seed, seed_file = worker.get("seed", {}), None
    if seed.get("sha256"):
        info = plan.get("seeds", {}).get(seed["sha256"], {})
        full = str(info.get("source"))
        nist = "nist" in full.lower() or "/targets/seeds/" in full    # search/seeds/ and the old catalog
        seed = {"kind": "file", "point": f"{info.get('gates')}@{info.get('depth')}",
                "by": "NIST" if nist else "us", "source": pathlib.Path(full).name}
        seed_file = run / info["snapshot"] if info.get("snapshot") else None
    found = {"version": version, "code": code, "found_utc": meta.get("saved_utc"),
             "seconds_into_run": meta.get("t"), "run": plan.get("name"), "run_id": meta.get("run_id"),
             "worker": meta.get("worker"), "depth_cap": meta.get("depth_cap"), "move": meta.get("move"),
             "seed": seed}
    start = (f"{'NIST' if seed['by'] == 'NIST' else 'our'} {seed['point']} circuit (seed.json in the logs)"
             if seed.get("kind") == "file" else "fresh roots")
    root = str(meta.get("root"))
    found["chain_root"] = root
    if "#" in root:
        started = f"a fresh root ({root})"
    elif root == "seed":
        started = start
    else:
        started = f"a restart from the worker's {root}; the worker began from {start}"
    provenance = [f"Found by: XORFlux {version} ({code}), run {plan.get('name')}, worker {meta.get('worker')}",
                  f"Started from: {started}"]
    logs = [(record_path, "record.json", False),
            (record_path.with_suffix(".verification.json"), "verification.json", False),
            (dossier, "dossier.json", False) if dossier else (None, None, False),
            (seed_file, "seed.json", False) if seed_file else (None, None, False),
            (worker_dir / "events.jsonl", None, True), (run / "plan.json", None, True),
            (run / "campaign.toml", None, False)]
    return write(rec, provenance, [l for l in logs if l[0]], found, force, worker.get("target"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("record", help="a record JSON written by xorflux inside a run directory")
    ap.add_argument("--version", default="latest", help="version label written into the file")
    ap.add_argument("--code", default="search/xorflux", help="where the code that found it lives")
    ap.add_argument("--force", action="store_true", help="replace an existing file at that point")
    a = ap.parse_args()
    path = from_run(a.record, a.code, a.version, a.force)
    print(f"wrote {path.relative_to(ROOT.parent)} and its logs/{path.name[:-len('.circ.txt')]}/")


if __name__ == "__main__":
    main()
