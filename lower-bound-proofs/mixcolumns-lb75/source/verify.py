#!/usr/bin/env python3
"""
Standalone verifier for the AES MixColumns XOR-circuit records in this folder.

Zero external dependencies (Python 3 standard library only). It rebuilds the AES
MixColumns specification FROM SCRATCH here in GF(2^8), so the verifier IS the
specification -- there is no hidden convention to mismatch. For each circuit JSON
in circuits/ it checks:

  1. every gate is a 2-input XOR of two earlier signals (indices strictly smaller);
  2. simulating the gate list produces, at the declared output signals, exactly
     the 32 AES MixColumns output bits (checked as a GF(2) linear map, which is
     complete: agreement on the 32 basis inputs proves agreement on all 2^32);
  3. the reported gateCount and depth match what the gate list actually is;
  4. the SHA-256 fields in bounds.json match both the circuit file on disk and
     the documented canonical gate encoding.

Usage:
    python3 verify.py                      # the shipped records in circuits/
    python3 verify.py --adhoc FILE [...]   # any circuit file, including yours

The default mode verifies the shipped records and runs all four checks, so a
circuit with no bounds.json entry fails check 4 by design: the shipped set is
exactly the set the repository makes claims about.

--adhoc runs checks 1-3 on files you name, anywhere on disk, and skips check 4
(there is nothing to compare a stranger's file against). It answers "is this a
correct MixColumns circuit, and how big and deep is it really?" -- it is not an
acceptance decision, which needs a bounds.json entry only the maintainer can
add. See the "Beat a row" paragraph in README.md for how that works.

Exit code 0 iff every circuit passes every check that applies to it.

Convention (fixed and self-contained):
  * The AES state is 4 bytes s0,s1,s2,s3. Bit index i in 0..31 refers to
    bit (i mod 8) of byte (i div 8), least-significant-bit-first within a byte.
  * MixColumns maps input column (a0,a1,a2,a3) to output column where
        out[c] = 2*a[c] XOR 3*a[(c+1)%4] XOR 1*a[(c+2)%4] XOR 1*a[(c+3)%4]
    with multiplication in GF(2^8) modulo x^8 + x^4 + x^3 + x + 1 (0x11b).
"""
import argparse
import json
import glob
import os
import hashlib
import sys


def xtime(a):
    a <<= 1
    return (a ^ 0x11B) & 0xFF if (a & 0x100) else (a & 0xFF)


def gf_mul(a, b):
    r = 0
    for i in range(8):
        if (b >> i) & 1:
            t = a
            for _ in range(i):
                t = xtime(t)
            r ^= t
    return r & 0xFF


def mixcolumns_target_masks():
    """Return the 32 output masks: mask[r] has bit c set iff input bit c feeds
    output bit r. Built directly from the GF(2^8) MixColumns definition."""
    coef = [2, 3, 1, 1]
    M = [[0] * 32 for _ in range(32)]
    for col in range(4):                       # output byte position
        for k in range(4):                     # input byte (col+k)%4, coefficient coef[k]
            c, ib = coef[k], (col + k) % 4
            for in_bit in range(8):
                v = gf_mul(c, 1 << in_bit)      # value contributed to output byte
                for out_bit in range(8):
                    if (v >> out_bit) & 1:
                        M[col * 8 + out_bit][ib * 8 + in_bit] ^= 1
    masks = []
    for r in range(32):
        m = 0
        for c in range(32):
            if M[r][c]:
                m |= (1 << c)
        masks.append(m)
    return masks


def canonical_gate_hash(gates):
    canon = json.dumps({"inputCount": 32, "gates": gates}, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def verify_circuit(path, spec, bounds_by_id, adhoc=False):
    with open(path, "rb") as f:
        raw = f.read()
    data = json.loads(raw)
    cid = data.get("id") or os.path.basename(path)
    gates = data["gates"]
    n_in = data.get("inputCount", 32)
    problems = []

    # 1. structural: 2-input XOR, parents earlier
    sig = [1 << i for i in range(n_in)]         # signal masks (input-dependency vectors)
    depth = [0] * n_in
    for k, g in enumerate(gates):
        if len(g) != 2:
            problems.append(f"gate {k} is not 2-input")
            continue
        a, b = g
        idx = n_in + k
        if not (0 <= a < idx and 0 <= b < idx):
            problems.append(f"gate {k} references a non-earlier signal")
            sig.append(0)
            depth.append(0)
            continue
        sig.append(sig[a] ^ sig[b])
        depth.append(max(depth[a], depth[b]) + 1)
    measured_depth = max(depth) if depth else 0

    # 2. correctness: declared outputs equal the spec masks (linear-map complete check)
    outs = data.get("outputSignals")
    if not isinstance(outs, list) or len(outs) != 32:
        problems.append("outputSignals must be a list of 32 entries")
    else:
        for j in range(32):
            s = outs[j]
            if not isinstance(s, int) or not (0 <= s < len(sig)):
                problems.append(f"output {j}: invalid signal index {s!r}")
                continue
            if sig[s] != spec[j]:
                problems.append(f"output {j}: signal {s} = {sig[s]:#010x}, expected {spec[j]:#010x}")

    # 3. metadata consistency. In --adhoc mode a field that is absent is not a
    #    defect -- the file simply makes no claim there -- but a field that is
    #    present must be right.
    if "gateCount" in data or not adhoc:
        if data["gateCount"] != len(gates):
            problems.append(f"gateCount {data['gateCount']} != actual {len(gates)}")
    if "depth" in data or not adhoc:
        if data["depth"] != measured_depth:
            problems.append(f"depth {data['depth']} != measured {measured_depth}")

    # 4. SHA-256 fields in bounds.json match this file and the documented
    #    canonical-gate encoding. Skipped for --adhoc files: a circuit that is
    #    not a shipped record has nothing to compare against.
    b = None if adhoc else bounds_by_id.get(cid)
    if adhoc:
        pass
    elif b is None:
        problems.append("no matching entry in bounds.json")
    else:
        sha = hashlib.sha256(raw).hexdigest()
        if b.get("sha256_circuit_json") != sha:
            problems.append("SHA-256 in bounds.json does not match circuits/ file on disk")
        canonical_sha = canonical_gate_hash(gates)
        if b.get("sha256_canonical_gates") != canonical_sha:
            problems.append("canonical gate SHA-256 in bounds.json does not match the documented inputCount+gates encoding")

    return cid, len(gates), measured_depth, problems


def main():
    ap = argparse.ArgumentParser(
        description="Verify AES MixColumns XOR circuits against a from-scratch "
                    "GF(2^8) rebuild of the specification.")
    ap.add_argument(
        "--adhoc", nargs="+", metavar="FILE", default=None,
        help="Verify these circuit files instead of the shipped records. Runs "
             "checks 1-3 (structure, correctness on all 32 outputs, declared "
             "gateCount/depth) and skips check 4, the bounds.json hash match, "
             "which only applies to circuits this repository makes claims about.")
    ap.add_argument(
        "files", nargs="*", metavar="FILE",
        help="Verify these files in full mode, all four checks. A file that is "
             "not a shipped record has no bounds.json entry and so fails check "
             "4; use --adhoc for those.")
    args = ap.parse_args()
    if args.adhoc and args.files:
        ap.error("give files either as --adhoc FILE ... or as bare arguments, not both")

    here = os.path.dirname(os.path.abspath(__file__))
    spec = mixcolumns_target_masks()
    # self-check: MixColumns has 20 weight-5 and 12 weight-7 outputs
    wts = [bin(m).count("1") for m in spec]
    assert wts.count(5) == 20 and wts.count(7) == 12, "spec self-check failed"

    bounds_path = os.path.join(here, "bounds.json")
    bounds_by_id = {}
    if os.path.exists(bounds_path):
        for e in json.load(open(bounds_path))["circuits"]:
            bounds_by_id[e["id"]] = e

    adhoc = args.adhoc is not None
    if adhoc:
        files = list(args.adhoc)
        missing = [f for f in files if not os.path.exists(f)]
        if missing:
            for f in missing:
                print(f"no such file: {f}")
            sys.exit(1)
    elif args.files:
        files = list(args.files)
        missing = [f for f in files if not os.path.exists(f)]
        if missing:
            for f in missing:
                print(f"no such file: {f}")
            sys.exit(1)
    else:
        files = sorted(glob.glob(os.path.join(here, "circuits", "*.json")))
        if not files:
            print("no circuits found")
            sys.exit(1)

    print("AES MixColumns rebuilt from GF(2^8): weight profile 20x5 + 12x7  [OK]\n")
    all_ok = True
    for path in files:
        cid, ng, dep, problems = verify_circuit(path, spec, bounds_by_id, adhoc=adhoc)
        if problems:
            all_ok = False
            print(f"[FAIL] {cid}: {ng} gates, depth {dep}")
            for p in problems[:6]:
                print(f"        - {p}")
            if problems == ["no matching entry in bounds.json"]:
                print("        (correct and well-formed, but not a shipped record. "
                      "Re-run with --adhoc to check just that; acceptance into the")
                print("         records needs a bounds.json entry -- see README.md, "
                      "\"Beat a row of the table?\")")
        elif adhoc:
            print(f"[ OK ] {cid}: {ng} gates, depth {dep} — all 32 outputs correct")
        else:
            print(f"[ OK ] {cid}: {ng} gates, depth {dep} — all 32 outputs correct, SHA fields match")
    print()
    if adhoc:
        print("ALL CIRCUITS CORRECT (ad-hoc mode: checks 1-3 only, no bounds.json"
              " hash match)." if all_ok else "ONE OR MORE CIRCUITS FAILED.")
    else:
        print("ALL CIRCUITS VERIFIED." if all_ok else "ONE OR MORE CIRCUITS FAILED.")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
