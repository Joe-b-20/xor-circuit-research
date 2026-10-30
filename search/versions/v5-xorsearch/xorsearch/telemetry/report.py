"""Run directory -> CSV tables + one self-contained ``report.html``.

``build_report(run_dir, out_dir=None)`` is what ``xorsearch report DIR`` calls.  It reads the
formats in ``telemetry/schema.md``:

* ``campaign.jsonl`` (+ rotated segments): coordinator ``frontier``, ``fleet_diversity``,
  ``pool`` events;
* ``workers/*/events*.jsonl``: worker events (improve, epoch, plateau, restart, followup, ...);
* ``workers/*/dossiers/*.json``: improvement dossiers (used for links, and to recover an
  improvement whose ``improve`` line was lost in a crash).

and writes into ``out_dir`` (default ``RUN/report``):

==========================  ==================================================================
``improvements.csv``        one row per improvement with full attribution (move, components,
                            phase, chain, root, lineage parent, plateau shape, timing, follow-ups)
``epochs.csv``              one row per epoch per worker
``moves.csv``               per-move totals (fleet and per worker) with rates per CPU-hour
``combos.csv``              per (move, sub-operation combination) totals
``plateaus.csv``            one row per closed plateau
``restarts.csv``            one row per restart, with what the new chain achieved
``frontier.csv``            coordinator frontier changes
``fleet_diversity.csv``     coordinator diversity snapshots
``report.html``             charts (inline SVG + a few lines of JS for tooltips), tables, links
==========================  ==================================================================

The HTML has no external resources and follows ``prefers-color-scheme``.  Chart geometry is
presentation, not search behaviour, so its constants live here rather than in knobs.
"""
from __future__ import annotations

import csv
import html
import json
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

from .recorder import COUNTERS, Recorder, read_log

# ---------------------------------------------------------------- presentation constants
PANEL_W, PANEL_H = 360, 190          # small-multiple panel (viewBox units)
WIDE_W, WIDE_H = 720, 260            # full-width chart
MARGIN = (24, 16, 30, 46)            # top, right, bottom, left (top leaves room for the y label)
BAR_W = 480                          # horizontal bar charts (they sit in half-width cards)
MAX_TABLE_ROWS = 2000                # improvement rows shown in HTML (CSV has all)
MAX_COLORED = 8                      # categorical slots; further moves fold into "other"
PLATEAU_BINS = (0, 1, 10, 100, 1_000, 10_000, 100_000)   # seconds, log-spaced bin edges

# Validated categorical palette (light, dark) — fixed slot order, never cycled.
PALETTE = (("#2a78d6", "#3987e5"), ("#eb6834", "#d95926"), ("#1baf7a", "#199e70"),
           ("#eda100", "#c98500"), ("#e87ba4", "#d55181"), ("#008300", "#008300"),
           ("#6250d6", "#9085e9"), ("#e34948", "#e66767"))


# ===================================================================== loading

class Run:
    """Everything parsed from one run directory."""

    def __init__(self, run_dir: Path):
        self.dir = run_dir
        self.errors: list = []             # (file, line) of undecodable lines
        self.coord: list[dict] = []
        self.events: dict[str, list[dict]] = {}      # worker -> events sorted by t
        self.worker_dirs: dict[str, Path] = {}
        self.dossiers: dict[str, Path] = {}          # improvement id -> dossier path
        self._load()

    def _load(self) -> None:
        if (self.dir / "campaign.jsonl").exists() or any(self.dir.glob("campaign-*.jsonl")):
            self.coord = sorted(read_log(self.dir / "campaign.jsonl", self.errors),
                                key=lambda e: e.get("t") or 0.0)
        workers = self.dir / "workers"
        for wdir in sorted(p for p in workers.glob("*") if p.is_dir()) if workers.is_dir() else ():
            evs = list(read_log(wdir / "events.jsonl", self.errors))
            name = next((e["worker"] for e in evs if e.get("worker")), wdir.name)
            evs.sort(key=lambda e: e.get("t") or 0.0)
            self.events[name] = evs
            self.worker_dirs[name] = wdir
            for p in (wdir / "dossiers").glob("*.json"):
                self.dossiers[p.stem] = p

    def of(self, ev: str):
        """``(worker, event)`` for every worker event of one type, time ordered per worker."""
        for w, evs in self.events.items():
            for e in evs:
                if e.get("ev") == ev:
                    yield w, e

    def improvements(self) -> list[dict]:
        """Improve events, plus improvements recovered from dossiers without an event."""
        out = [dict(e, worker=w) for w, e in self.of("improve")]
        seen = {e.get("id") for e in out}
        for did, path in sorted(self.dossiers.items()):
            if did in seen:
                continue
            try:
                d = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            rel = os.path.relpath(path, self.worker_dirs.get(d.get("worker"), path.parent.parent))
            fields = Recorder._improve_fields(d, rel.replace(os.sep, "/"))
            fields.update(worker=d.get("worker"), t=d.get("t"), it=d.get("it"),
                          utc=d.get("utc"), recovered=True)
            out.append(fields)
        out.sort(key=lambda e: (e.get("t") or 0.0, e.get("id") or ""))
        return out


# ===================================================================== tables

def _g(score, key):
    return score.get(key) if isinstance(score, dict) else None


def _num(x, default=0):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else default


def _div(a, b):
    return a / b if b else None


def improvement_rows(run: Run, out_dir: Path) -> list[dict]:
    """improvements.csv rows (dossier paths relative to the run directory)."""
    follow: dict[tuple, dict] = {}
    for w, e in run.of("followup"):
        follow[(e.get("id"), e.get("horizon"))] = e   # the last per (id, horizon) wins
    horizons = sorted({h for _, h in follow if isinstance(h, int)})
    rows = []
    for e in run.improvements():
        b, a = e.get("before"), e.get("after")
        wdir = run.worker_dirs.get(e["worker"])
        dossier = None
        if e.get("dossier") and wdir is not None:
            dossier = os.path.relpath(wdir / e["dossier"], run.dir).replace(os.sep, "/")
        row = {
            "id": e.get("id"), "worker": e["worker"], "t": e.get("t"), "utc": e.get("utc"),
            "it": e.get("it"), "kind": e.get("kind"),
            "gates_before": _g(b, "gates"), "depth_before": _g(b, "depth"),
            "gates_after": _g(a, "gates"), "depth_after": _g(a, "depth"),
            "d_gates": _sub(_g(a, "gates"), _g(b, "gates")),
            "d_depth": _sub(_g(a, "depth"), _g(b, "depth")),
            "move": e.get("move"), "components": "+".join(e.get("components") or []),
            "phase": e.get("phase"), "chain": e.get("chain"), "root": e.get("root"),
            "root_source": e.get("root_source"), "parent": e.get("parent"),
            "donor": e.get("donor"),
        }
        for k in ("plateau_age_it", "plateau_age_s", "plateau_distinct", "plateau_drift",
                  "neutral_rate", "it_since_prev", "s_since_prev", "it_since_root",
                  "s_since_root", "symdiff", "verified", "deterministic"):
            row[k] = e.get(k)
        row["dossier"] = dossier
        row["recovered"] = bool(e.get("recovered"))
        for h in horizons:
            f = follow.get((e.get("id"), h)) or {}
            row[f"fu{h}_later"] = f.get("later")
            row[f"fu{h}_improved_chain"] = f.get("improved_chain")
            row[f"fu{h}_plateau_it"] = f.get("plateau_it")
            row[f"fu{h}_complete"] = f.get("complete")
        rows.append(row)
    return rows


def _sub(a, b):
    return a - b if isinstance(a, (int, float)) and isinstance(b, (int, float)) else None


def epoch_rows(run: Run) -> list[dict]:
    """epochs.csv rows."""
    rows = []
    for w, e in run.of("epoch"):
        moves = e.get("moves") or {}
        tot = {k: sum(_num(m.get(k)) for m in moves.values())
               for k in ("proposals", "accepted", "neutral", "improved_chain", "improved_worker")}
        plateau = e.get("plateau") if isinstance(e.get("plateau"), dict) else {}
        div = e.get("diversity") if isinstance(e.get("diversity"), dict) else {}
        rows.append({
            "worker": w, "epoch": e.get("epoch"), "t": e.get("t"), "it": e.get("it"),
            "dt": e.get("dt"), "its": e.get("its"), "it_rate": e.get("it_rate"),
            "cpu_s": e.get("cpu_s"), "cpu_est": e.get("cpu_est"), "phase": e.get("phase"),
            "chain_gates": _g(e.get("chain"), "gates"), "chain_depth": _g(e.get("chain"), "depth"),
            "best_gates": _g(e.get("best"), "gates"), "best_depth": _g(e.get("best"), "depth"),
            **tot,
            "plateau_age_s": plateau.get("age_s"), "plateau_distinct": plateau.get("distinct_states"),
            "diversity_mean": div.get("mean"), "diversity_distinct": div.get("distinct"),
            "partial": bool(e.get("partial")),
        })
    return rows


def move_rows(run: Run, improvements: list[dict]) -> list[dict]:
    """moves.csv rows: scope ``all`` first, then one block per worker."""
    per: dict[tuple, list] = defaultdict(lambda: [0] * len(COUNTERS))
    for w, e in run.of("epoch"):
        for m, c in (e.get("moves") or {}).items():
            for scope in ("all", w):
                acc = per[(scope, m)]
                for j, k in enumerate(COUNTERS):
                    acc[j] += _num(c.get(k))
    imp = Counter()
    for r in improvements:
        imp[("all", r["move"])] += 1
        imp[(r["worker"], r["move"])] += 1
    for key in imp:  # moves that improved but have no epoch counters (lost epoch)
        per.setdefault(key, [0] * len(COUNTERS))
    scope_cpu = Counter()
    for (scope, _), c in per.items():
        scope_cpu[scope] += c[COUNTERS.index("cpu_s")]
    rows = []
    for (scope, m), c in sorted(per.items(), key=lambda kv: (kv[0][0] != "all", kv[0][0],
                                                            str(kv[0][1]))):
        d = dict(zip(COUNTERS, c))
        cpu_h = d["cpu_s"] / 3600
        n = imp[(scope, m)]
        rows.append({
            "scope": scope, "move": m, **d, "cpu_h": cpu_h,
            "cpu_share": _div(d["cpu_s"], scope_cpu[scope]),
            "valid_rate": _div(d["valid"], d["proposals"]),
            "accept_rate": _div(d["accepted"], d["proposals"]),
            "neutral_rate": _div(d["neutral"], d["proposals"]),
            "uphill_rate": _div(d["uphill"], d["proposals"]),
            "improvements": n,
            "proposals_per_cpu_s": _div(d["proposals"], d["cpu_s"]),
            "improvements_per_cpu_h": _div(n, cpu_h),
            "chain_improvements_per_cpu_h": _div(d["improved_chain"], cpu_h),
        })
    return rows


def combo_rows(run: Run, improvements: list[dict]) -> list[dict]:
    """combos.csv rows (fleet totals per move + sub-operation combination)."""
    acc: dict[tuple, list] = defaultdict(lambda: [0, 0, 0, 0])
    for _, e in run.of("epoch"):
        for c in e.get("combos") or ():
            key = (c.get("move"), "+".join(c.get("components") or []))
            a = acc[key]
            for j, k in enumerate(("proposals", "accepted", "improved_chain", "improved_worker")):
                a[j] += _num(c.get(k))
    imp = Counter((r["move"], r["components"]) for r in improvements)
    for key in imp:
        acc.setdefault(key, [0, 0, 0, 0])
    rows = [{"move": m, "components": comp, "proposals": a[0], "accepted": a[1],
             "improved_chain": a[2], "improved_worker": a[3], "improvements": imp[(m, comp)],
             "improved_per_1k_proposals": _div(1000 * a[3], a[0])}
            for (m, comp), a in acc.items()]
    rows.sort(key=lambda r: (-r["improvements"], -r["proposals"]))
    return rows


def plateau_rows(run: Run) -> list[dict]:
    """plateaus.csv rows."""
    rows = []
    for w, e in run.of("plateau"):
        level = e.get("level")
        lg = level[0] if isinstance(level, list) and level else (_g(level, "gates"))
        ld = level[1] if isinstance(level, list) and len(level) > 1 else (_g(level, "depth"))
        rows.append({
            "worker": w, "id": e.get("id"), "chain": e.get("chain"), "t": e.get("t"),
            "it": e.get("it"), "level_gates": lg, "level_depth": ld,
            **{k: e.get(k) for k in ("entry_it", "entry_t", "age_it", "age_s", "proposals",
                                     "accepted", "neutral_accepts", "neutral_rate",
                                     "distinct_states", "distinct_exact", "revisit_ratio",
                                     "drift", "max_drift", "exit", "improvement")},
        })
    return rows


def restart_rows(run: Run, improvements: list[dict]) -> list[dict]:
    """restarts.csv rows, joined with the improvements made on each new chain."""
    by_chain = defaultdict(list)
    for r in improvements:
        by_chain[r["chain"]].append(r)
    rows = []
    for w, e in run.of("restart"):
        root = e.get("root") if isinstance(e.get("root"), dict) else {"id": e.get("root")}
        prev = e.get("prev") if isinstance(e.get("prev"), dict) else {}
        imps = by_chain.get(e.get("chain"), [])
        first = min((r["t"] for r in imps if r.get("t") is not None), default=None)
        rows.append({
            "worker": w, "t": e.get("t"), "it": e.get("it"), "reason": e.get("reason"),
            "source": e.get("source"), "chain": e.get("chain"), "root": root.get("id"),
            "root_constructor": root.get("constructor"), "root_seed": root.get("seed"),
            "root_gates": root.get("gates"), "parent": e.get("parent"), "donor": e.get("donor"),
            "prev_chain": prev.get("chain"), "prev_age_it": prev.get("age_it"),
            "prev_age_s": prev.get("age_s"), "prev_best_gates": _g(prev.get("best"), "gates"),
            "prev_improvements": prev.get("improvements"),
            "improvements_on_chain": len(imps),
            "s_to_first_improvement": (first - e["t"]) if first is not None and e.get("t") is not None
            else None,
        })
    return rows


def frontier_rows(run: Run) -> list[dict]:
    """frontier.csv rows."""
    rows = []
    for e in run.coord:
        if e.get("ev") != "frontier":
            continue
        p = e.get("point")
        rows.append({"t": e.get("t"), "utc": e.get("utc"), "by": e.get("by"),
                     "gates": _g(p, "gates"), "depth": _g(p, "depth"), "kind": e.get("kind"),
                     "improvement": e.get("improvement"), "record": e.get("record"),
                     "dag": e.get("dag"), "frontier_size": len(e.get("frontier") or [])})
    return rows


def diversity_rows(run: Run) -> list[dict]:
    """fleet_diversity.csv rows."""
    keys = ("scope", "point", "n", "distinct", "modal_fraction", "mean", "min", "max",
            "basins", "sampled", "alarm")
    rows = []
    for e in run.coord:
        if e.get("ev") == "fleet_diversity":
            row = {"t": e.get("t"), "utc": e.get("utc")}
            row.update({k: e.get(k) for k in keys})
            if isinstance(row["point"], dict):
                row["point"] = f"{row['point'].get('gates')}/{row['point'].get('depth')}"
            rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict], columns: list[str] | None = None) -> None:
    """Write rows with a stable header (first row's keys, extended by later rows)."""
    if columns is None:
        columns = []
        for r in rows:
            for k in r:
                if k not in columns:
                    columns.append(k)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow({k: _cell(r.get(k)) for k in columns})


def _cell(x):
    if x is None:
        return ""
    if isinstance(x, float):
        return f"{x:.6g}"
    if isinstance(x, (list, dict)):
        return json.dumps(x, separators=(",", ":"))
    return x


# ===================================================================== SVG helpers

def esc(x) -> str:
    """HTML-escape any value."""
    return html.escape("" if x is None else str(x), quote=True)


def nice_ticks(lo: float, hi: float, n: int = 5) -> list[float]:
    """Round tick values covering [lo, hi]."""
    if hi <= lo:
        hi = lo + 1
    raw = (hi - lo) / max(1, n)
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    start = math.ceil(lo / step) * step
    ticks, v = [], start
    while v <= hi + step * 1e-9:
        ticks.append(round(v, 10))
        v += step
    return ticks


def time_unit(t_max: float) -> tuple[float, str]:
    """Divisor and label for a time axis spanning ``t_max`` seconds."""
    if t_max >= 3 * 3600:
        return 3600.0, "h"
    if t_max >= 300:
        return 60.0, "min"
    return 1.0, "s"


def fmt(x, digits=3) -> str:
    """Short human number."""
    if x is None:
        return "–"
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, int):
        return f"{x:,}"
    if isinstance(x, float):
        if x == 0:
            return "0"
        if abs(x) >= 1000:
            return f"{x:,.0f}"
        return f"{x:.{digits}g}"
    return str(x)


def fmt_s(s) -> str:
    """Seconds as a short duration."""
    if s is None:
        return "–"
    s = float(s)
    if s < 120:
        return f"{s:.1f} s"
    if s < 7200:
        return f"{s / 60:.1f} min"
    return f"{s / 3600:.2f} h"


def fmt_short(s: float) -> str:
    """Compact duration for bin labels: 10 s, 17 min, 2.8 h."""
    if s < 600:
        return f"{s:g} s"
    if s < 3600:
        return f"{s / 60:.0f} min"
    return f"{s / 3600:.2g} h"


class Plot:
    """Linear x/y scales into a viewBox with margins; emits axes and gridlines."""

    def __init__(self, w, h, x0, x1, y0, y1, margin=MARGIN):
        self.w, self.h = w, h
        self.top, self.right, self.bottom, self.left = margin
        if x1 <= x0:
            x1 = x0 + 1
        if y1 <= y0:
            y1 = y0 + 1
        self.x0, self.x1, self.y0, self.y1 = x0, x1, y0, y1

    def sx(self, x) -> float:
        return self.left + (x - self.x0) / (self.x1 - self.x0) * (self.w - self.left - self.right)

    def sy(self, y) -> float:
        return self.h - self.bottom - (y - self.y0) / (self.y1 - self.y0) * (
            self.h - self.top - self.bottom)

    def axes(self, xfmt=fmt, yfmt=fmt, xlabel="", ylabel="", xticks=None, yticks=None) -> str:
        out = []
        for v in yticks if yticks is not None else nice_ticks(self.y0, self.y1, 4):
            if self.y0 - 1e-9 <= v <= self.y1 + 1e-9:
                y = self.sy(v)
                out.append(f'<line class="grid" x1="{self.left}" x2="{self.w - self.right}" '
                           f'y1="{y:.1f}" y2="{y:.1f}"/>'
                           f'<text class="tick" x="{self.left - 6}" y="{y + 3.5:.1f}" '
                           f'text-anchor="end">{esc(yfmt(v))}</text>')
        base = self.h - self.bottom
        out.append(f'<line class="axis" x1="{self.left}" x2="{self.w - self.right}" '
                   f'y1="{base}" y2="{base}"/>')
        for v in xticks if xticks is not None else nice_ticks(self.x0, self.x1, 5):
            if self.x0 - 1e-9 <= v <= self.x1 + 1e-9:
                x = self.sx(v)
                out.append(f'<text class="tick" x="{x:.1f}" y="{base + 14}" '
                           f'text-anchor="middle">{esc(xfmt(v))}</text>')
        if xlabel:
            out.append(f'<text class="tick" x="{self.w - self.right}" y="{self.h - 2}" '
                       f'text-anchor="end">{esc(xlabel)}</text>')
        if ylabel:
            out.append(f'<text class="tick" x="2" y="{self.top - 10}" '
                       f'text-anchor="start">{esc(ylabel)}</text>')
        return "".join(out)


def svg(w, h, body, label) -> str:
    """An SVG element sized by its container."""
    return (f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}" '
            f'preserveAspectRatio="xMidYMid meet">{body}</svg>')


def marker(kind, x, y, cls, tip, r=4.5) -> str:
    """Improvement marker: circle = gates, diamond = depth, square = frontier."""
    t = f' data-tip="{esc(tip)}"'
    if kind == "depth":
        return (f'<path class="{cls} mk"{t} d="M{x:.1f},{y - r - 1:.1f} L{x + r + 1:.1f},{y:.1f} '
                f'L{x:.1f},{y + r + 1:.1f} L{x - r - 1:.1f},{y:.1f}Z"/>')
    if kind == "frontier":
        return (f'<rect class="{cls} mk"{t} x="{x - r:.1f}" y="{y - r:.1f}" width="{2 * r}" '
                f'height="{2 * r}" rx="1"/>')
    return f'<circle class="{cls} mk"{t} cx="{x:.1f}" cy="{y:.1f}" r="{r}"/>'


def legend(items: list[tuple[str, str]], shapes: bool = False) -> str:
    """HTML legend: (css class, label) pairs; optional marker-shape key."""
    parts = [f'<span class="key"><i class="sw {c}"></i>{esc(label)}</span>' for c, label in items]
    if shapes:
        parts.append('<span class="key shape">● gates</span><span class="key shape">◆ depth'
                     '</span><span class="key shape">■ frontier</span>')
    return f'<div class="legend">{"".join(parts)}</div>'


# ===================================================================== charts

def move_classes(improvements, moves_rows) -> dict[str, str]:
    """Stable move -> css class.  Moves with improvements take the first slots (by count,
    then name); the rest share ``other``.  The mapping is fixed for the whole report so a
    move keeps its color in every chart."""
    counts = Counter(r["move"] for r in improvements)
    names = {r["move"] for r in moves_rows} | set(counts)
    ordered = sorted(names, key=lambda m: (-counts[m], str(m)))
    return {m: (f"s{i + 1}" if i < MAX_COLORED and counts[m] else "other")
            for i, m in enumerate(ordered)}


def chart_best_vs_time(run: Run, improvements, mcls) -> str:
    """Small multiples: best gates vs time per worker, improvement markers by move."""
    t_max = max((e.get("t") or 0.0 for evs in run.events.values() for e in evs), default=1.0)
    div, unit = time_unit(t_max)
    by_worker = defaultdict(list)
    for r in improvements:
        by_worker[r["worker"]].append(r)
    panels = []
    for w in run.events:
        imps = [r for r in by_worker.get(w, []) if r.get("gates_after") is not None]
        evs = run.events[w]
        t_end = max((e.get("t") or 0.0 for e in evs), default=0.0)
        t_start = min((e.get("t") or 0.0 for e in evs), default=0.0)
        if not imps:
            panels.append(f'<figure class="panel"><figcaption>{esc(w)}</figcaption>'
                          f'<p class="empty">no improvements</p></figure>')
            continue
        ys = [r["gates_after"] for r in imps] + [r["gates_before"] for r in imps
                                                  if r.get("gates_before") is not None]
        lo, hi = min(ys), max(ys)
        pad = max(1, (hi - lo) * 0.08)
        p = Plot(PANEL_W, PANEL_H, 0, t_max / div, lo - pad, hi + pad)
        # Step line of the best gate count so far.
        first = imps[0]
        best = first.get("gates_before") if first.get("gates_before") is not None else first["gates_after"]
        pts = [(t_start, best)]
        for r in imps:
            if r["gates_after"] < best:
                pts.append((r["t"], best))
                best = r["gates_after"]
                pts.append((r["t"], best))
        pts.append((t_end, best))
        path = " ".join(f"{'M' if i == 0 else 'L'}{p.sx(t / div):.1f},{p.sy(g):.1f}"
                        for i, (t, g) in enumerate(pts))
        body = [p.axes(xfmt=fmt, xlabel=unit, ylabel="gates"),
                f'<path class="line" d="{path}"/>']
        for r in imps:
            tip = (f"{r['id']} · {r['move']} [{r['components']}] · {r.get('phase')}\n"
                   f"{r.get('gates_before')}/{r.get('depth_before')} → "
                   f"{r['gates_after']}/{r.get('depth_after')} at {fmt_s(r['t'])}\n"
                   f"plateau {fmt_s(r.get('plateau_age_s'))}, root {r.get('root_source')}")
            body.append(marker(r.get("kind"), p.sx(r["t"] / div), p.sy(r["gates_after"]),
                               mcls.get(r["move"], "other"), tip))
        panels.append(f'<figure class="panel"><figcaption>{esc(w)} <span class="muted">best '
                      f'{esc(min(r["gates_after"] for r in imps))} gates · {len(imps)} '
                      f'improvements</span></figcaption>'
                      f'{svg(PANEL_W, PANEL_H, "".join(body), f"best gates vs time, {w}")}'
                      f'</figure>')
    return f'<div class="multiples">{"".join(panels)}</div>'


def chart_frontier(rows) -> str:
    """Campaign-wide best gates over time from coordinator frontier events."""
    rows = [r for r in rows if r.get("gates") is not None and r.get("t") is not None]
    if not rows:
        return '<p class="empty">No coordinator frontier events.</p>'
    t_max = max(r["t"] for r in rows) or 1.0
    div, unit = time_unit(t_max)
    lo, hi = min(r["gates"] for r in rows), max(r["gates"] for r in rows)
    pad = max(1, (hi - lo) * 0.08)
    p = Plot(WIDE_W, WIDE_H * 0.8, 0, t_max / div, lo - pad, hi + pad)
    best, pts = None, []
    for r in rows:
        if best is None or r["gates"] < best:
            if best is not None:
                pts.append((r["t"], best))
            best = r["gates"]
            pts.append((r["t"], best))
    pts.append((t_max, best))
    path = " ".join(f"{'M' if i == 0 else 'L'}{p.sx(t / div):.1f},{p.sy(g):.1f}"
                    for i, (t, g) in enumerate(pts))
    body = [p.axes(xlabel=unit, ylabel="gates"), f'<path class="line" d="{path}"/>']
    for r in rows:
        body.append(marker(r.get("kind"), p.sx(r["t"] / div), p.sy(r["gates"]), "ink",
                           f"{r['gates']}/{r['depth']} by {r['by']} at {fmt_s(r['t'])}"
                           f" ({r.get('improvement')})"))
    return svg(WIDE_W, WIDE_H * 0.8, "".join(body), "campaign frontier best gates vs time")


def chart_hbars(items: list[tuple[str, float, str, str]], label: str, value_fmt=fmt,
                width: int = BAR_W) -> str:
    """Horizontal bars: (name, value, css class, tooltip).  Values labelled at bar ends."""
    if not items:
        return '<p class="empty">No data.</p>'
    row_h, gap, left, right = 22, 6, 120, 92
    h = len(items) * (row_h + gap) + 10
    vmax = max(v for _, v, _, _ in items) or 1
    body = []
    for i, (name, v, cls, tip) in enumerate(items):
        y = 5 + i * (row_h + gap)
        wbar = max(0.0, v / vmax * (width - left - right))
        body.append(f'<text class="label" x="{left - 8}" y="{y + row_h / 2 + 4}" '
                    f'text-anchor="end">{esc(name)}</text>')
        if wbar > 0:
            # Bar with a 4px rounded end, anchored square at the baseline.
            r = min(4.0, wbar)
            body.append(f'<path class="bar {cls}" data-tip="{esc(tip)}" d="M{left},{y} '
                        f'H{left + wbar - r:.1f} Q{left + wbar:.1f},{y} {left + wbar:.1f},{y + r} '
                        f'V{y + row_h - r} Q{left + wbar:.1f},{y + row_h} {left + wbar - r:.1f},'
                        f'{y + row_h} H{left} Z"/>')
        body.append(f'<text class="value" x="{left + wbar + 6:.1f}" y="{y + row_h / 2 + 4}">'
                    f'{esc(value_fmt(v))}</text>')
    body.append(f'<line class="axis" x1="{left}" x2="{left}" y1="0" y2="{h}"/>')
    return svg(width, h, "".join(body), label)


def chart_plateaus(rows) -> str:
    """Histogram of plateau durations on log-spaced bins, split by exit (improvement or not)."""
    rows = [r for r in rows if isinstance(r.get("age_s"), (int, float))]
    if not rows:
        return '<p class="empty">No plateau events.</p>'
    edges = list(PLATEAU_BINS) + [float("inf")]
    labels = []
    for a, b in zip(edges, edges[1:]):
        if b == float("inf"):
            labels.append(f"≥ {fmt_short(a)}")
        elif not a:
            labels.append(f"< {fmt_short(b)}")
        else:
            labels.append(f"{fmt_short(a)} – {fmt_short(b)}")
    imp = [0] * (len(edges) - 1)
    other = [0] * (len(edges) - 1)
    for r in rows:
        i = next(k for k in range(len(edges) - 1) if edges[k] <= r["age_s"] < edges[k + 1])
        (imp if r.get("exit") == "improve" else other)[i] += 1
    vmax = max(a + b for a, b in zip(imp, other)) or 1
    p = Plot(WIDE_W, WIDE_H, 0, len(labels), 0, vmax * 1.08)
    body = [p.axes(xticks=[], ylabel="plateaus")]
    bw = (p.sx(1) - p.sx(0)) * 0.7
    for i, lab in enumerate(labels):
        x = p.sx(i + 0.5) - bw / 2
        y_base = p.sy(0)
        for cls, n, name in (("seq-strong", imp[i], "ended by an improvement"),
                             ("seq-light", other[i], "other exit")):
            if not n:
                continue
            hgt = y_base - p.sy(n)
            # 2px surface gap between stacked segments.
            body.append(f'<rect class="bar {cls}" x="{x:.1f}" y="{y_base - hgt + 1:.1f}" '
                        f'width="{bw:.1f}" height="{max(0.0, hgt - 1):.1f}" rx="2" '
                        f'data-tip="{esc(f"{lab}: {n} {name}")}"/>')
            y_base -= hgt
        body.append(f'<text class="tick" x="{p.sx(i + 0.5):.1f}" y="{p.h - p.bottom + 14}" '
                    f'text-anchor="middle">{esc(lab)}</text>')
        tot = imp[i] + other[i]
        if tot:
            body.append(f'<text class="value" x="{p.sx(i + 0.5):.1f}" y="{p.sy(tot) - 4:.1f}" '
                        f'text-anchor="middle">{tot}</text>')
    return (svg(WIDE_W, WIDE_H, "".join(body), "plateau duration distribution")
            + legend([("seq-strong", "ended by an improvement"), ("seq-light", "other exit")]))


def chart_series(points: list[tuple[float, float]], ylabel: str, y0=None, y1=None,
                 label="") -> str:
    """Single-series line over time with point tooltips (no legend: the title names it)."""
    points = [(t, v) for t, v in points if isinstance(v, (int, float)) and t is not None]
    if not points:
        return '<p class="empty">No data.</p>'
    t_max = max(t for t, _ in points) or 1.0
    div, unit = time_unit(t_max)
    lo = min(v for _, v in points) if y0 is None else y0
    hi = max(v for _, v in points) if y1 is None else y1
    p = Plot(PANEL_W, PANEL_H, 0, t_max / div, lo, hi if hi > lo else lo + 1)
    path = " ".join(f"{'M' if i == 0 else 'L'}{p.sx(t / div):.1f},{p.sy(v):.1f}"
                    for i, (t, v) in enumerate(points))
    body = [p.axes(xlabel=unit, ylabel=ylabel), f'<path class="line accent" d="{path}"/>']
    for t, v in points:
        body.append(f'<circle class="hit" cx="{p.sx(t / div):.1f}" cy="{p.sy(v):.1f}" r="6" '
                    f'data-tip="{esc(f"{fmt_s(t)}: {fmt(v)}")}"/>')
    return svg(PANEL_W, PANEL_H, "".join(body), label or ylabel)


def chart_lineage(run: Run, improvements, restarts, mcls) -> str:
    """Improvements as nodes (x = time, lane = worker), edges from lineage parent to child.

    Same-worker edges are thin; cross-worker edges (sharing) are dashed curves.  Hollow
    triangles mark restarts on each lane."""
    if not improvements:
        return '<p class="empty">No improvements.</p>'
    workers = list(run.events)
    lane = {w: i for i, w in enumerate(workers)}
    lane_h = 26
    left = 110
    h = len(workers) * lane_h + 40
    t_max = max((e.get("t") or 0.0 for evs in run.events.values() for e in evs), default=1.0)
    div, unit = time_unit(t_max)
    p = Plot(WIDE_W, h, 0, t_max / div, 0, 1, margin=(10, 16, 30, left))
    pos = {}
    for r in improvements:
        if r.get("t") is None or r["worker"] not in lane:
            continue
        pos[r["id"]] = (p.sx(r["t"] / div), 18 + lane[r["worker"]] * lane_h)
    body = [p.axes(xlabel=unit, yticks=[])]
    for w, i in lane.items():
        y = 18 + i * lane_h
        body.append(f'<line class="grid" x1="{left}" x2="{WIDE_W - 16}" y1="{y}" y2="{y}"/>'
                    f'<text class="label" x="{left - 8}" y="{y + 4}" text-anchor="end">'
                    f'{esc(w)}</text>')
    for r in improvements:
        parent = r.get("parent")
        if r["id"] in pos and parent in pos:
            (x1, y1), (x2, y2) = pos[parent], pos[r["id"]]
            if y1 == y2:
                body.append(f'<line class="edge" x1="{x1:.1f}" y1="{y1}" x2="{x2:.1f}" y2="{y2}"/>')
            else:
                mx = (x1 + x2) / 2
                tip = f"{parent} → {r['id']} (shared)"
                body.append(f'<path class="edge cross" d="M{x1:.1f},{y1} C{mx:.1f},{y1} '
                            f'{mx:.1f},{y2} {x2:.1f},{y2}" data-tip="{esc(tip)}"/>')
    for row in restarts:
        if row["worker"] in lane and row.get("t") is not None:
            x, y = p.sx(row["t"] / div), 18 + lane[row["worker"]] * lane_h
            tip = (f"restart {row.get('chain')} · {row.get('source')} ({row.get('reason')})"
                   f" root {row.get('root')} · {row.get('improvements_on_chain')} improvements")
            body.append(f'<path class="restart" d="M{x:.1f},{y - 9} l4,6 h-8 z" '
                        f'data-tip="{esc(tip)}"/>')
    for r in improvements:
        if r["id"] in pos:
            x, y = pos[r["id"]]
            tip = (f"{r['id']} · {r['move']} [{r['components']}]\n"
                   f"{r.get('gates_after')}/{r.get('depth_after')} · parent {r.get('parent')}")
            body.append(marker(r.get("kind"), x, y, mcls.get(r["move"], "other"), tip, r=4))
    return svg(WIDE_W, h, "".join(body), "improvement lineage")


# ===================================================================== HTML

CSS = """
:root{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;
--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;--border:rgba(11,11,11,.10);
--accent:#256abf;--seq-strong:#2a78d6;--seq-light:#9ec5f4;--other:#b5b3ab;
%LIGHT%}
@media (prefers-color-scheme:dark){:root{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;
--ink:#f0efec;--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;
--border:rgba(255,255,255,.10);--accent:#5598e7;--seq-strong:#3987e5;--seq-light:#1c5cab;
--other:#5f5e59;%DARK%}}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);
font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1120px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:36px 0 6px}
p.lede,.muted{color:var(--ink2)}.muted{font-weight:400}
section>p.note{color:var(--ink2);margin:0 0 10px;max-width:72ch}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 12px}
.tile b{display:block;font-size:20px}.tile span{color:var(--ink2);font-size:12px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px}
.multiples{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:10px}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:10px}
figure{margin:0}.panel{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:8px}
figcaption{font-weight:600;font-size:13px;margin:0 0 4px}
svg{width:100%;height:auto;display:block;overflow:visible}
line.grid,line.axis{stroke-width:1}line.grid{stroke:var(--grid)}line.axis{stroke:var(--axis)}
text{fill:var(--muted);font-size:10.5px;font-variant-numeric:tabular-nums}
text.label{fill:var(--ink2);font-size:11.5px}text.value{fill:var(--ink);font-size:11px}
.line{fill:none;stroke:var(--ink2);stroke-width:2;stroke-linejoin:round}
.line.accent{stroke:var(--accent)}
.mk{stroke:var(--surface);stroke-width:2;cursor:default}
.hit{fill:transparent}.hit:hover{fill:var(--accent)}
.edge{stroke:var(--axis);stroke-width:1.5;fill:none}.edge.cross{stroke:var(--ink2);stroke-dasharray:4 3}
.restart{fill:none;stroke:var(--ink2);stroke-width:1.2}
.ink{fill:var(--ink)}.other{fill:var(--other)}.seq-strong{fill:var(--seq-strong)}
.seq-light{fill:var(--seq-light)}.bar.accent{fill:var(--accent)}
%CLASSES%
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;margin:8px 0 2px;color:var(--ink2);font-size:12px}
.key{display:inline-flex;align-items:center;gap:6px}
.sw{width:10px;height:10px;border-radius:50%;display:inline-block;background:var(--other)}
.sw.seq-strong{background:var(--seq-strong)}.sw.seq-light{background:var(--seq-light)}
%SWATCHES%
.empty{color:var(--muted);font-style:italic}
.tablewrap{overflow-x:auto;max-height:560px;overflow-y:auto;border:1px solid var(--border);border-radius:8px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:12px;font-variant-numeric:tabular-nums}
th,td{padding:5px 8px;text-align:left;white-space:nowrap;border-bottom:1px solid var(--grid)}
th{position:sticky;top:0;background:var(--surface);color:var(--ink2);font-weight:600}
td.n{text-align:right}a{color:var(--accent)}
#tip{position:fixed;pointer-events:none;background:var(--surface);color:var(--ink);
border:1px solid var(--border);border-radius:6px;padding:6px 8px;font-size:12px;white-space:pre;
box-shadow:0 2px 10px rgba(0,0,0,.15);display:none;z-index:9;max-width:90vw}
footer{margin-top:40px;color:var(--muted);font-size:12px}
"""

JS = """
(function(){var tip=document.getElementById('tip');
document.addEventListener('mouseover',function(e){var t=e.target.closest('[data-tip]');
if(!t){tip.style.display='none';return;}tip.textContent=t.getAttribute('data-tip');tip.style.display='block';});
document.addEventListener('mousemove',function(e){if(tip.style.display!=='block')return;
var x=e.clientX+14,y=e.clientY+14,r=tip.getBoundingClientRect();
if(x+r.width>innerWidth-8)x=e.clientX-r.width-14;if(y+r.height>innerHeight-8)y=e.clientY-r.height-14;
tip.style.left=x+'px';tip.style.top=y+'px';});})();
"""


def _css(mcls: dict[str, str]) -> str:
    light = "".join(f"--s{i + 1}:{lt};" for i, (lt, _) in enumerate(PALETTE))
    dark = "".join(f"--s{i + 1}:{dk};" for i, (_, dk) in enumerate(PALETTE))
    classes = "".join(f".s{i + 1}{{fill:var(--s{i + 1})}}" for i in range(len(PALETTE)))
    swatches = "".join(f".sw.s{i + 1}{{background:var(--s{i + 1})}}" for i in range(len(PALETTE)))
    return (CSS.replace("%LIGHT%", light).replace("%DARK%", dark)
            .replace("%CLASSES%", classes).replace("%SWATCHES%", swatches))


def html_table(rows, columns, numeric=(), links=None, limit=None) -> str:
    """A plain HTML table; ``links`` maps column -> function(row) giving an href."""
    if not rows:
        return '<p class="empty">No rows.</p>'
    links = links or {}
    shown = rows if limit is None else rows[:limit]
    head = "".join(f"<th>{esc(c)}</th>" for c in columns)
    body = []
    for r in shown:
        cells = []
        for c in columns:
            v = r.get(c)
            is_seconds = c == "t" or c.endswith("_s")
            text = fmt_s(v) if is_seconds and isinstance(v, (int, float)) else fmt(v)
            if c in links and v is not None:
                href = links[c](r)
                text = f'<a href="{esc(href)}">{esc(text)}</a>' if href else esc(text)
            else:
                text = esc(text)
            cls = ' class="n"' if c in numeric else ""
            cells.append(f"<td{cls}>{text}</td>")
        body.append(f"<tr>{''.join(cells)}</tr>")
    more = (f'<p class="muted">Showing {len(shown):,} of {len(rows):,} rows; the CSV has all.</p>'
            if len(shown) < len(rows) else "")
    return (f'<div class="tablewrap"><table><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>{more}')


def render_html(run: Run, out_dir: Path, tables: dict) -> str:
    """The whole report page."""
    imps, moves, plats = tables["improvements"], tables["moves"], tables["plateaus"]
    restarts, frontier, divs = tables["restarts"], tables["frontier"], tables["fleet_diversity"]
    mcls = move_classes(imps, moves)
    fleet_moves = [r for r in moves if r["scope"] == "all"]
    cpu_h = sum(r["cpu_h"] for r in fleet_moves)
    t_end = max((e.get("t") or 0.0 for evs in run.events.values() for e in evs), default=0.0)
    best = min(((r["gates_after"], r["depth_after"] or 0) for r in imps
                if r.get("gates_after") is not None), default=None)

    def tile(value, label):
        return f'<div class="tile"><b>{esc(value)}</b><span>{esc(label)}</span></div>'

    tiles = "".join([
        tile(len(run.events), "workers"), tile(fmt_s(t_end), "campaign time"),
        tile(f"{cpu_h:.2f}", "CPU-hours in moves"), tile(f"{len(imps):,}", "worker improvements"),
        tile(f"{best[0]}/{best[1]}" if best else "–", "best gates/depth"),
        tile(f"{len(restarts):,}", "restarts"), tile(f"{len(plats):,}", "plateaus closed"),
    ])
    used = [(c, m) for m, c in sorted(mcls.items(), key=lambda kv: (kv[1] == "other", kv[1]))
            if c != "other" and any(r["move"] == m for r in imps)]
    if any(c == "other" for c in mcls.values()):
        used.append(("other", "other moves"))
    move_legend = legend(used, shapes=True)

    # Move contribution bars (fleet scope).
    contrib = sorted((r for r in fleet_moves if r["cpu_h"] > 0 or r["improvements"]),
                     key=lambda r: -(r["improvements_per_cpu_h"] or 0))
    bars_rate = chart_hbars(
        [(r["move"], r["improvements_per_cpu_h"] or 0.0, mcls.get(r["move"], "other"),
          f"{r['move']}: {r['improvements']} improvements in {r['cpu_h']:.3f} CPU-h; "
          f"{r['improved_chain']} chain bests") for r in contrib],
        "improvements per CPU-hour by move", lambda v: f"{v:.2f}/CPU-h")
    bars_cpu = chart_hbars(
        [(r["move"], 100 * (r["cpu_share"] or 0.0), "accent",
          f"{r['move']}: {r['cpu_h']:.3f} CPU-h, {fmt(r['proposals'])} proposals, accept "
          f"{fmt(r['accept_rate'])}") for r in sorted(contrib, key=lambda r: -(r["cpu_share"] or 0))],
        "CPU share by move", lambda v: f"{v:.1f}%")

    # Restart sources.
    src = Counter(r.get("source") or "unknown" for r in restarts)
    src_imp = Counter()
    for r in restarts:
        src_imp[r.get("source") or "unknown"] += r["improvements_on_chain"]
    bars_src = chart_hbars(
        [(s, n, "accent", f"{s}: {n} restarts, {src_imp[s]} improvements on those chains")
         for s, n in src.most_common()], "restarts by source", width=WIDE_W)
    src_note = " · ".join(f"{esc(s)}: {src_imp[s]} improvements on {n} chains"
                          for s, n in src.most_common())

    # Diversity over time (coordinator panel; fall back to worker archive diversity).
    chains = [r for r in divs if r.get("scope") in (None, "chains")] or divs
    div_mean = chart_series([(r["t"], r.get("mean")) for r in chains], "mean Jaccard", 0, 1,
                            "fleet mean pairwise Jaccard distance")
    div_distinct = chart_series([(r["t"], r.get("distinct")) for r in chains], "distinct", 0,
                                None, "distinct states across workers")
    if not divs:
        div_mean = chart_series([(r["t"], r.get("diversity_mean")) for r in tables["epochs"]],
                                "mean Jaccard", 0, 1, "archive diversity (from epochs)")
        div_distinct = chart_series([(r["t"], r.get("diversity_distinct"))
                                     for r in tables["epochs"]], "distinct", 0, None,
                                    "archive distinct (from epochs)")

    dossier_href = {"id": lambda r: _href(run, out_dir, r.get("dossier")),
                    "dossier": lambda r: _href(run, out_dir, r.get("dossier"))}
    imp_cols = ["id", "worker", "t", "kind", "gates_before", "depth_before", "gates_after",
                "depth_after", "move", "components", "phase", "root_source", "parent",
                "plateau_age_s", "plateau_distinct", "s_since_root", "s_since_prev", "verified"]
    move_cols = ["move", "proposals", "valid_rate", "accept_rate", "neutral_rate", "uphill_rate",
                 "improved_chain", "improvements", "cpu_h", "cpu_share",
                 "improvements_per_cpu_h", "chain_improvements_per_cpu_h"]
    num = set(move_cols[1:]) | {"t", "gates_before", "depth_before", "gates_after",
                                "depth_after", "plateau_age_s", "plateau_distinct",
                                "s_since_root", "s_since_prev", "proposals", "accepted",
                                "improved_worker", "improved_chain"}
    combos = tables["combos"]
    warns = [(w, e) for w, e in run.of("warn")]
    warn_html = ("".join(f"<li><b>{esc(w)}</b> {esc(e.get('kind'))}: {esc(e.get('message'))} "
                         f"<span class='muted'>at {esc(fmt_s(e.get('t')))}</span></li>"
                         for w, e in warns[:50]))
    errors = (f'<p class="muted">{len(run.errors)} undecodable log lines skipped.</p>'
              if run.errors else "")

    sections = [
        f'<h1>xorsearch run report</h1><p class="lede">{esc(run.dir)}</p>'
        f'<div class="tiles">{tiles}</div>{errors}',
        '<section><h2>Best gate count over time, per worker</h2><p class="note">Step line: '
        'best gates so far. Markers: each worker improvement, colored by the move that found it; '
        'shape gives the kind. Hover for move, sub-operations, phase and plateau age.</p>'
        f'{move_legend}{chart_best_vs_time(run, imps, mcls)}</section>',
        '<section><h2>Campaign frontier</h2><p class="note">Coordinator frontier changes; '
        'hover for the worker and improvement behind each point.</p>'
        f'<div class="card">{chart_frontier(frontier)}</div></section>',
        '<section><h2>Move contribution</h2><p class="note">Worker improvements per CPU-hour '
        'spent in each move (fleet total), and where the CPU went.</p><div class="two">'
        f'<div class="card"><figcaption>Improvements per CPU-hour</figcaption>{bars_rate}</div>'
        f'<div class="card"><figcaption>CPU share</figcaption>{bars_cpu}</div></div>'
        f'<h3 class="muted" style="font-size:14px;margin:16px 0 6px">Per-move totals</h3>'
        f'{html_table(fleet_moves, move_cols, num)}'
        f'<h3 class="muted" style="font-size:14px;margin:16px 0 6px">Sub-operation '
        f'combinations</h3>'
        f'{html_table(combos, list(combos[0]) if combos else [], set(combos[0]) - {"move", "components"} if combos else (), limit=40)}'
        '</section>',
        '<section><h2>Plateau durations</h2><p class="note">How long the chain best stayed at '
        'one level before the plateau closed.</p>'
        f'<div class="card">{chart_plateaus(plats)}</div></section>',
        '<section><h2>Diversity over time</h2><div class="two">'
        f'<div class="card"><figcaption>Mean pairwise Jaccard distance</figcaption>{div_mean}</div>'
        f'<div class="card"><figcaption>Distinct states</figcaption>{div_distinct}</div>'
        '</div></section>',
        f'<section><h2>Restart sources</h2><p class="note">{src_note or "No restarts."}</p>'
        f'<div class="card">{bars_src}</div></section>',
        '<section><h2>Improvement lineage</h2><p class="note">Each node is an improvement '
        '(x: time, lane: worker); lines join an improvement to its lineage parent, dashed when '
        'the parent is on another worker (sharing). Triangles mark restarts.</p>'
        f'{move_legend}<div class="card">{chart_lineage(run, imps, restarts, mcls)}</div></section>',
        '<section><h2>Improvements</h2><p class="note">Ids link to the dossiers (trace, ring '
        'of recent proposals, state before and after, RNG state).</p>'
        f'{html_table(imps, imp_cols, num, dossier_href, MAX_TABLE_ROWS)}</section>',
    ]
    if warns:
        sections.append(f"<section><h2>Warnings</h2><ul>{warn_html}</ul></section>")
    csvs = " · ".join(f'<a href="{name}.csv">{name}.csv</a>' for name in tables)
    sections.append(f"<footer>Tables: {csvs}. Formats: telemetry/schema.md (v1).</footer>")
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>xorsearch run report</title><style>{_css(mcls)}</style></head><body><main>"
            + "".join(sections) + f'</main><div id="tip" role="tooltip"></div><script>{JS}</script>'
            "</body></html>")


def _href(run: Run, out_dir: Path, rel: str | None) -> str | None:
    if not rel:
        return None
    return os.path.relpath(run.dir / rel, out_dir).replace(os.sep, "/")


# ===================================================================== entry point

def build_report(run_dir, out_dir=None) -> Path:
    """Read a campaign directory and write the CSV tables and ``report.html``.

    Returns the path of ``report.html``.  ``out_dir`` defaults to ``run_dir/report``."""
    run_dir = Path(run_dir).resolve()
    out = Path(out_dir).resolve() if out_dir is not None else run_dir / "report"
    out.mkdir(parents=True, exist_ok=True)
    run = Run(run_dir)
    imps = improvement_rows(run, out)
    tables = {
        "improvements": imps,
        "epochs": epoch_rows(run),
        "moves": move_rows(run, imps),
        "combos": combo_rows(run, imps),
        "plateaus": plateau_rows(run),
        "restarts": restart_rows(run, imps),
        "frontier": frontier_rows(run),
        "fleet_diversity": diversity_rows(run),
    }
    columns = {
        "frontier": ["t", "utc", "by", "gates", "depth", "kind", "improvement", "record", "dag",
                     "frontier_size"],
        "fleet_diversity": ["t", "utc", "scope", "point", "n", "distinct", "modal_fraction",
                            "mean", "min", "max", "basins", "sampled", "alarm"],
    }
    for name, rows in tables.items():
        write_csv(out / f"{name}.csv", rows, columns.get(name))
    page = out / "report.html"
    page.write_text(render_html(run, out, tables), encoding="utf-8")
    return page


def main(argv=None) -> int:
    """``python -m xorsearch.telemetry.report RUN [OUT]``."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print("usage: python -m xorsearch.telemetry.report RUN_DIR [OUT_DIR]")
        return 0 if args else 2
    page = build_report(args[0], args[1] if len(args) > 1 else None)
    print(page)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
