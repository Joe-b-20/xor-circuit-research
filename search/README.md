# XORFlux

**XORFlux: Adaptive Search for Size- and Depth-Efficient XOR Circuits.** It looks for XOR
circuits with few gates, then low depth, for any GF(2) linear map. It needs Python 3.11 or
newer and nothing outside the standard library.

The current version is v8, in [`xorflux/`](xorflux/). The search is still being developed, so
v8 is not the last version. Up to v8 it was called `xorsearch`, the name the logs of its runs
still use.

| Page | What is in it |
|---|---|
| [HOW-IT-WORKS.md](HOW-IT-WORKS.md) | the method of v8: workers, moves, campaigns, the soft depth cap, the polish |
| [USAGE.md](USAGE.md) | how to run v8: commands, campaigns, configuration, adding a map, output |
| [HISTORY.md](HISTORY.md) | how we got to v8: every version, the failed experiments and the decisions they led to |
| [xorflux/DESIGN.md](xorflux/DESIGN.md) | developer reference: interfaces, invariants, the evidence behind the defaults |
| [xorflux/telemetry/schema.md](xorflux/telemetry/schema.md) | event, record and dossier formats |

```bash
python3 search/xorflux map list                                # the maps in circuits/
python3 search/xorflux quick aes-mixcolumns --seconds 60       # one worker, in this terminal
```

Run every command from the repository root.

| Folder | Content |
|---|---|
| [xorflux/](xorflux/) | the current version's code (v8) |
| [campaigns/](campaigns/) | one campaign file per map, as run |
| [seeds/](seeds/) | known circuits campaigns start from (NIST's, per map) |
| [versions/](versions/) | older versions' code, as they ran |
