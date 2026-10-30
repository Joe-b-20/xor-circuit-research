"""Knob and Section declarations: the single source of truth for every tunable value.

Each module that reads settings declares a module-level ``KNOBS = Section(...)`` next to the
code that uses it.  ``config.registry`` imports those modules so the full schema can be listed,
validated and documented without running a search.  Nothing tunable is a literal in an algorithm.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_MISSING = object()


@dataclass(frozen=True)
class Knob:
    """One tunable value.

    ``default`` fixes the type unless ``kind`` is given (needed when the default is None).
    ``choices`` restricts the value to a fixed set; ``min``/``max`` bound numbers and the
    length of lists is unrestricted.  ``doc`` is shown by ``xorsearch config explain``.
    """
    default: Any
    doc: str
    min: float | None = None
    max: float | None = None
    choices: tuple | None = None
    kind: type | tuple | None = None
    nullable: bool = False

    def value_type(self):
        """Python type(s) accepted for this knob."""
        if self.kind is not None:
            return self.kind
        if isinstance(self.default, bool):
            return bool
        if isinstance(self.default, float):
            return (float, int)
        if isinstance(self.default, int):
            return int
        return type(self.default)

    def validate(self, key: str, value: Any) -> Any:
        """Return ``value`` coerced to the knob type, or raise ValueError naming ``key``."""
        if value is None:
            if self.nullable or self.default is None:
                return None
            raise ValueError(f"{key}: may not be null")
        expected = self.value_type()
        # bool is an int subclass; never let True stand in for a number or vice versa.
        if isinstance(value, bool) != (expected is bool):
            raise ValueError(f"{key}: expected {_type_name(expected)}, got {value!r}")
        if not isinstance(value, expected):
            raise ValueError(f"{key}: expected {_type_name(expected)}, got {value!r}")
        if expected == (float, int):
            value = float(value)
        if self.choices is not None and value not in self.choices:
            raise ValueError(f"{key}: {value!r} not in {list(self.choices)}")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if self.min is not None and value < self.min:
                raise ValueError(f"{key}: {value!r} is below the minimum {self.min}")
            if self.max is not None and value > self.max:
                raise ValueError(f"{key}: {value!r} is above the maximum {self.max}")
        return value


@dataclass(frozen=True)
class Section:
    """A named group of knobs, addressed by a dotted path such as ``moves.walk.hub``."""
    path: str
    doc: str
    knobs: dict[str, Knob] = field(default_factory=dict)

    def keys(self):
        """Fully qualified keys of this section's knobs."""
        return [f"{self.path}.{name}" for name in self.knobs]


def _type_name(kind) -> str:
    if isinstance(kind, tuple):
        return " or ".join(k.__name__ for k in kind)
    return kind.__name__


class Schema:
    """All declared sections, indexed by fully qualified knob key."""

    def __init__(self, sections):
        self.sections: dict[str, Section] = {}
        self.knobs: dict[str, Knob] = {}
        for section in sections:
            if section.path in self.sections:
                raise ValueError(f"section {section.path} declared twice")
            self.sections[section.path] = section
            for name, knob in section.knobs.items():
                key = f"{section.path}.{name}"
                if key in self.knobs or key in self.sections:
                    raise ValueError(f"knob {key} collides with another declaration")
                self.knobs[key] = knob

    def defaults(self) -> dict[str, Any]:
        """Flat ``{key: default}`` for every knob."""
        return {key: knob.default for key, knob in self.knobs.items()}

    def suggest(self, key: str) -> str:
        """Closest known key, for error messages about typos."""
        import difflib
        match = difflib.get_close_matches(key, list(self.knobs), n=1)
        return f" (did you mean {match[0]}?)" if match else ""
