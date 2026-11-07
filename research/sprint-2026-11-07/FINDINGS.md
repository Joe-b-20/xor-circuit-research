# Sprint 2026-11-07: findings

Each entry: observation, mechanism (plain words), prediction that could be wrong, test, what
survived, limits. Tags: [proved] [checked] [measured] [cited] [guess]. Scripts are named; raw
data lives in `~/xs-campaigns/2026-11-07-sprint/`.

## F1. Descending to 88 on MixColumns is cheap; the difficulty is entirely below 88 [measured]

- Observation (hunt, first 25 min, 12 fresh-root chains, v8 uncapped): every chain reached <= 89
  within 10-162 s of its root; 4 of 12 reached 88 within 50-216 s. (`hunt/descents.py`)
- Compare: July 2026 engine, every 88 within 3,855 s of its root, median 2,234 s (restart.root_seconds
  doc string). The v5+ incremental kernel changed the picture: 88 is minutes away from any root.
- Prediction: with hours of such descents, the number of distinct 88 plateaus reached will tell
  whether the 88 level is a small finite set (saturating curve) or vast (linear growth).
- Status: open; curve to be read from `hunt/plateaus.py`.
