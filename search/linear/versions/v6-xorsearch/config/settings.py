"""Layered, validated settings with per-value provenance.

Layers, lowest to highest, with the origin label each value keeps (``campaign/freeze.py`` builds
them from a campaign file)::

    default < profile:<name> < campaign < campaign:set < group:<name> < worker:<id> < cli

Every layer is a nested or flat-dotted mapping plus a label, so a run can always say where each
setting came from.  ``to_toml`` writes settings back as a commented TOML profile.
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
    """Read a TOML file into a nested dict (ValueError naming the file on bad TOML)."""
    with open(path, "rb") as handle:
        try:
            return tomllib.load(handle)
        except tomllib.TOMLDecodeError as exc:
            raise ValueError(f"{path}: {exc}") from None


def builtin_profiles() -> list[str]:
    """Names of the profiles shipped in ``config/profiles/``."""
    return sorted(p.stem for p in PROFILE_DIR.glob("*.toml"))


def profile_path(name: str, base: str | Path | None = None) -> Path:
    """A built-in profile name, or a ``.toml`` path (relative to ``base``, default the cwd)."""
    candidate = Path(name)
    if candidate.suffix == ".toml":
        path = candidate if candidate.is_absolute() or base is None else Path(base) / candidate
        if not path.is_file():
            raise ValueError(f"profile file not found: {path}")
        return path
    path = PROFILE_DIR / f"{name}.toml"
    if not path.is_file():
        raise ValueError(f"unknown profile {name!r}; built-in profiles: "
                         f"{', '.join(builtin_profiles())} (or give a path ending in .toml)")
    return path


def toml_value(value: Any) -> str:
    """One settings value in TOML syntax (null is written ``"none"``, which knobs accept)."""
    return '"none"' if value is None else json.dumps(value)


def to_toml(settings: "Settings", keys: Iterable[str] | None = None, docs: bool = True,
            width: int = 98) -> str:
    """Settings as a TOML document, one ``[section]`` table per knob section.

    With ``docs`` each table and knob is preceded by its documentation and legal values, so the
    output is a commented starting point for a profile.  Values that do not come from the
    defaults carry their origin as a trailing comment.  ``load_toml`` of the result applied to
    fresh Settings reproduces the same values.
    """
    import textwrap
    schema = settings.schema
    wanted = set(settings.values if keys is None else keys)
    lines: list[str] = []
    for path in sorted(schema.sections):
        section = schema.sections[path]
        names = [name for name in section.knobs if f"{path}.{name}" in wanted]
        if not names:
            continue
        if lines:
            lines.append("")
        if docs:
            lines += textwrap.wrap(section.doc, width, initial_indent="# ", subsequent_indent="# ")
        lines.append(f"[{path}]")
        for name in names:
            key, knob = f"{path}.{name}", section.knobs[name]
            if docs:
                text = textwrap.wrap(knob.doc, width, initial_indent="# ", subsequent_indent="#   ")
                legal = f"[{knob.constraint()}]"   # kept whole on one line
                if len(text[-1]) + 1 + len(legal) <= width:
                    text[-1] += " " + legal
                else:
                    text.append("#   " + legal)
                lines += text
            line = f"{name} = {toml_value(settings[key])}"
            if settings.origin(key) != "default":
                line += f"  # {settings.origin(key)}"
            lines.append(line)
    return "\n".join(lines) + "\n"


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

    def __getitem__(self, key: str) -> Any:
        return self.values[key]

    def origin(self, key: str) -> str:
        """Label of the layer that set ``key``."""
        return self.origins[key]

    def view(self, path: str) -> "View":
        """Attribute access to the knobs under ``path`` (e.g. ``view('moves.walk').expand.weight``)."""
        return View(self.values, path)

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
    settings = Settings(Schema(sections))
    if overrides:
        settings.apply(overrides, "test")
    return settings


def build(profiles: Iterable[str] = ("default",), layers: Iterable[tuple[str, Mapping]] = (),
          assignments: Iterable[str] = (), schema: Schema | None = None) -> Settings:
    """Resolve settings from profiles, extra layers and ``key=value`` assignments (origins
    ``profile:<name>``, each layer's label, ``cli``) over ``schema`` (default: the full one)."""
    if schema is None:
        from .registry import schema as full_schema
        schema = full_schema()
    settings = Settings(schema)
    for name in profiles:
        path = profile_path(name)
        settings.apply(load_toml(path), f"profile:{path.stem}")
    for label, layer in layers:
        settings.apply(layer, label)
    for text in assignments:
        key, value = parse_assignment(text)
        settings.apply({key: value}, "cli")
    return settings
