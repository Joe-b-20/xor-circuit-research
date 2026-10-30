"""Shared test fixtures: the repository's maps plus extra circuits kept only for tests.

``tests/data/<map>/*.json`` holds circuits the suites need that are not campaign seeds (the
AES InvMixColumns 88-gate depth-19 circuit used by the kernel stress tests and benchmarks).
``tests/data/legacy_golden.json`` holds the reference verifier's outputs on every seed.
"""
import json
from pathlib import Path

from xorflux.core.target import Seed

DATA = Path(__file__).resolve().parent / "data"


def seeds(target):
    """The target's own seeds followed by its test-only circuits in ``tests/data/<name>/``."""
    folder = DATA / target.name
    extra = []
    if folder.is_dir():
        for path in sorted(folder.glob("*.json")):
            data = json.loads(path.read_text())
            extra.append(Seed(str(path), data.get("gateCount"), data.get("depth"),
                              path.name.split(".")[0]))
    return tuple(target.seeds) + tuple(extra)
