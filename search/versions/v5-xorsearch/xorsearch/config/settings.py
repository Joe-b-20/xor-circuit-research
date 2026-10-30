"""Layered, validated settings with per-value provenance.

Layers, lowest to highest: built-in defaults, profile TOML files, campaign file, worker-group
overrides, per-worker overrides, command-line ``--set key=value``.  Every layer is a nested or
flat-dotted mapping plus a label; the label of the layer that set a value is kept so a run can
always say where each setting came from.
"""
from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path
from typing import Any, Iterable, Mapping

from .schema import Schema

PROFILE_DIR = Path(__file__).with_name("profiles")


def flatten(mapping: Mapping, prefix: str = "") -> dict[str, Any]:
    """Nested mapping to ``{dotted.key: value}``.  Lists and scalars are leaves."""
    out: dict[str, Any] = {}
    for key, value in mapping.items():
        full = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, Mapping):
            out.update(flatten(value, full))
        else:
            out[full] = value
    return out


def parse_assignment(text: str) -> tuple[str, Any]:
    """Parse ``a.b.c=value`` using TOML value syntax; bare words become strings."""
    key, sep, raw = text.partition("=")
    if not sep or not key.strip():
        raise ValueError(f"expected key=value, got {text!r}")
    raw = raw.strip()
    try:
        value = tomllib.loads(f"v = {raw}")["v"]
    except tomllib.TOMLDecodeError:
        value = raw
    return key.strip(), value


def load_toml(path: str | Path) -> dict[str, Any]:
    """Read a TOML file into a nested dict."""
    with open(path, "rb") as handle:
        return tomllib.load(handle)


def profile_path(name: str) -> Path:
    """A built-in profile name or an explicit TOML path."""
    candidate = Path(name)
    if candidate.suffix == ".toml" and candidate.exists():
        return candidate
    path = PROFILE_DIR / f"{name}.toml"
    if not path.exists():
        known = sorted(p.stem for p in PROFILE_DIR.glob("*.toml"))
        raise ValueError(f"unknown profile {name!r}; known: {known}")
    return path


class Settings:
    """Resolved settings: flat validated values plus the origin of each value."""

    def __init__(self, schema: Schema, layers: Iterable[tuple[str, Mapping]] = ()):
        self.schema = schema
        self.values: dict[str, Any] = schema.defaults()
        self.origins: dict[str, str] = {key: "default" for key in self.values}
        for label, layer in layers:
            self.apply(layer, label)

    def apply(self, layer: Mapping, label: str) -> "Settings":
        """Overlay one layer in place.  Unknown keys are errors, with a suggestion."""
        for key, value in flatten(layer).items():
            knob = self.schema.knobs.get(key)
            if knob is None:
                raise ValueError(f"{label}: unknown setting {key}{self.schema.suggest(key)}")
            self.values[key] = knob.validate(key, value)
            self.origins[key] = label
        return self

    def with_overrides(self, layer: Mapping, label: str) -> "Settings":
        """A copy with one more layer applied (the original is unchanged)."""
        copy = Settings(self.schema)
        copy.values = dict(self.values)
        copy.origins = dict(self.origins)
        return copy.apply(layer, label)

    def __getitem__(self, key: str) -> Any:
        return self.values[key]

    def origin(self, key: str) -> str:
        """Label of the layer that set ``key``."""
        return self.origins[key]

    def view(self, path: str) -> "View":
        """Attribute access to the knobs under ``path`` (e.g. ``view('moves.walk').hub.weight``)."""
        return View(self.values, path)

    def nested(self) -> dict[str, Any]:
        """Nested dict of all values (for TOML/JSON output)."""
        root: dict[str, Any] = {}
        for key, value in sorted(self.values.items()):
            node = root
            *parents, leaf = key.split(".")
            for part in parents:
                node = node.setdefault(part, {})
            node[leaf] = value
        return root

    def digest(self) -> str:
        """SHA-256 of the canonical JSON of all values; identifies a configuration."""
        body = json.dumps(self.values, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(body).hexdigest()

    def non_default(self) -> dict[str, tuple[Any, str]]:
        """``{key: (value, origin)}`` for every value not taken from the defaults."""
        return {k: (self.values[k], o) for k, o in self.origins.items() if o != "default"}


class View:
    """Read-only attribute view of one settings subtree.

    Attribute lookups are dict lookups; hot code should copy the few values it needs into locals
    once per call rather than reading the view inside inner loops.
    """
    __slots__ = ("_values", "_path")

    def __init__(self, values: dict[str, Any], path: str):
        object.__setattr__(self, "_values", values)
        object.__setattr__(self, "_path", path)

    def __getattr__(self, name: str):
        key = f"{self._path}.{name}" if self._path else name
        values = self._values
        if key in values:
            return values[key]
        prefix = key + "."
        if any(k.startswith(prefix) for k in values):
            return View(values, key)
        raise AttributeError(f"no setting {key}")

    def __getitem__(self, name: str):
        return self.__getattr__(name)

    def __setattr__(self, name, value):
        raise AttributeError("settings views are read-only")

    def get(self, name: str, default=None):
        try:
            return self.__getattr__(name)
        except AttributeError:
            return default

    def as_dict(self) -> dict[str, Any]:
        """Flat ``{relative.key: value}`` for this subtree (for traces and dossiers)."""
        prefix = self._path + "." if self._path else ""
        return {k[len(prefix):]: v for k, v in self._values.items() if k.startswith(prefix)}

    @property
    def path(self) -> str:
        return self._path


def for_sections(*sections, overrides: Mapping | None = None) -> Settings:
    """Settings over only the given sections (unit tests of one module)."""
    from .schema import Schema
    settings = Settings(Schema(sections))
    if overrides:
        settings.apply(overrides, "test")
    return settings


def build(profiles: Iterable[str] = ("default",), layers: Iterable[tuple[str, Mapping]] = (),
          assignments: Iterable[str] = ()) -> Settings:
    """Resolve settings from profiles, extra layers and ``key=value`` assignments."""
    from .registry import schema
    settings = Settings(schema())
    for name in profiles:
        path = profile_path(name)
        settings.apply(load_toml(path), f"profile:{path.stem}")
    for label, layer in layers:
        settings.apply(layer, label)
    for text in assignments:
        key, value = parse_assignment(text)
        settings.apply({key: value}, "cli")
    return settings
