"""Knob and Section declarations: the single source of truth for every tunable value.

Each module that reads settings declares a module-level ``KNOBS = Section(...)`` next to the
code that uses it.  ``config.registry`` imports those modules so the full schema can be listed,
validated and documented without running a search.  Nothing tunable is a literal in an algorithm.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

#: Strings that mean null for a nullable, non-string knob.  TOML has no null, so profiles,
#: campaign files and ``--set`` write ``"none"`` (``config show`` prints nulls that way too).
NULL_WORDS = ("none", "null")


@dataclass(frozen=True)
class Knob:
    """One tunable value.

    ``default`` fixes the type unless ``kind`` is given (needed when the default is None).
    ``choices`` restricts the value to a fixed set; ``min``/``max`` bound numbers.  Lists may
    have any length; when the default is a non-empty list of one scalar type, every element
    must have that type.  ``nullable`` knobs accept null (written ``"none"`` in TOML).
    ``doc`` is shown by ``xorflux config explain`` and ``config show``.
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

    @property
    def accepts_null(self) -> bool:
        """True when null is a legal value."""
        return self.nullable or self.default is None

    def _element_type(self):
        """Scalar type every list element must have, or None when unconstrained."""
        if not isinstance(self.default, list) or not self.default:
            return None
        types = {bool if isinstance(x, bool) else float if isinstance(x, float) else type(x)
                 for x in self.default}
        if len(types) != 1:
            return None
        (kind,) = types
        return kind if kind in (bool, int, float, str) else None

    def validate(self, key: str, value: Any) -> Any:
        """Return ``value`` coerced to the knob type, or raise ValueError naming ``key``."""
        expected = self.value_type()
        if isinstance(value, str) and value.lower() in NULL_WORDS and self.accepts_null \
                and expected is not str:
            value = None
        if value is None:
            if self.accepts_null:
                return None
            raise ValueError(f"{key}: may not be null")
        # bool is an int subclass; never let True stand in for a number or vice versa.
        if isinstance(value, bool) != (expected is bool) or not isinstance(value, expected):
            raise ValueError(f"{key}: expected {_type_name(expected)}, got {value!r}")
        if expected == (float, int):
            value = float(value)
        if isinstance(value, list):
            value = self._validate_elements(key, value)
        if self.choices is not None and value not in self.choices:
            raise ValueError(f"{key}: {value!r} not in {list(self.choices)}")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if self.min is not None and value < self.min:
                raise ValueError(f"{key}: {value!r} is below the minimum {self.min}")
            if self.max is not None and value > self.max:
                raise ValueError(f"{key}: {value!r} is above the maximum {self.max}")
        return value

    def _validate_elements(self, key: str, value: list) -> list:
        kind = self._element_type()
        if kind is None:
            return value
        out = []
        for item in value:
            ok = (isinstance(item, bool) == (kind is bool)
                  and isinstance(item, (float, int) if kind is float else kind))
            if not ok:
                raise ValueError(f"{key}: list elements must be {kind.__name__}, got {item!r}")
            out.append(float(item) if kind is float else item)
        return out

    def constraint(self) -> str:
        """Short human summary of type and legal values, e.g. ``float >= 0.1`` (docs, show)."""
        if self.choices is not None:
            text = "one of " + " | ".join(str(c) for c in self.choices)
        else:
            text = _type_name(self.value_type()).replace("float or int", "float")
            element = self._element_type()
            if element is not None:
                text = f"list of {element.__name__}"
            if self.min is not None and self.max is not None:
                text += f" in [{self.min:g}, {self.max:g}]"
            elif self.min is not None:
                text += f" >= {self.min:g}"
            elif self.max is not None:
                text += f" <= {self.max:g}"
        if self.accepts_null:
            text += ', or "none"'
        return text


@dataclass(frozen=True)
class Section:
    """A named group of knobs, addressed by a dotted path such as ``moves.walk.expand``."""
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
        """Flat ``{key: default}`` for every knob (list defaults copied: never shared)."""
        return {key: copy.deepcopy(knob.default) if isinstance(knob.default, (list, dict))
                else knob.default for key, knob in self.knobs.items()}

    def section_of(self, key: str) -> Section:
        """The section that declares knob ``key``."""
        return self.sections[key.rsplit(".", 1)[0]]

    def suggest(self, key: str) -> str:
        """Closest known key, for error messages about typos."""
        import difflib
        match = difflib.get_close_matches(key, list(self.knobs), n=1)
        return f" (did you mean {match[0]}?)" if match else ""
