"""Telemetry: event logs, dossiers, metrics and run reports.

* ``recorder``: ``Recorder`` / ``NullRecorder`` (one per worker), ``EventLog`` (coordinator),
  log readers; the ``telemetry`` knobs.
* ``metrics``: Jaccard distance, diversity panels, ``PlateauTracker``, ``RateCounter``,
  circuit-shape summaries.
* ``report``: ``build_report(run_dir, out_dir=None)`` -> CSV tables + ``report.html``.
* ``schema.md``: the event and dossier formats (the contract for all of the above).
"""
from .metrics import (PlateauTracker, RateCounter, diversity, jaccard_distance,
                      shape_from_gates, shape_from_values)
from .recorder import (SCHEMA_VERSION, CampaignClock, EventLog, NullRecorder, Recorder,
                       read_log)


def build_report(run_dir, out_dir=None):
    """Write CSV tables and ``report.html`` for a run directory (see ``telemetry.report``)."""
    from .report import build_report as _build
    return _build(run_dir, out_dir)


__all__ = ["Recorder", "NullRecorder", "EventLog", "CampaignClock", "read_log",
           "SCHEMA_VERSION", "PlateauTracker", "RateCounter", "diversity", "jaccard_distance",
           "shape_from_gates", "shape_from_values", "build_report"]
