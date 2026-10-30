"""Campaign runtime: plans, frozen run directories, coordinator, workers, records and sharing.

Modules (data flows top to bottom)::

    freeze.py       campaign TOML -> plan (layered settings with origins) -> frozen run directory
    coordinator.py  owns the run directory: starts workers, collects and re-verifies records,
                    global frontier, campaign pool, fleet diversity, staged shutdown
    worker.py       one process: Engine + checkpoints + status + records + pool
    records.py      record files, independent verification, and the Backend seam to
                    core / engine / telemetry
    sharing.py      pool files (coordinator) and the engine's Pool (pull / off)
    checkpoint.py   atomic files, process identity, campaign lock, checkpoint envelopes

Run-directory layout and file formats are documented in ``search/README.md``.
Submodules are imported explicitly; this file imports nothing so ``config.registry`` can load
each module's ``KNOBS`` cheaply.
"""
