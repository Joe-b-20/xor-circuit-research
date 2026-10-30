# Benchmarks: xorsearch against the previous `search/` framework

Short head-to-head runs, to check that the unified method is at least as good as the framework it
replaces on the targets both can run. **These are short runs, not optimality claims**: nine
minutes say nothing about where either method ends after days, and two workers per target is a
small sample.

## Setup

- 9 minutes of wall time per target, 2 workers per target, for both frameworks.
- The same seed circuits for both.
- Every record of both runs was re-verified with the old framework's verifier
  (`search/target.py`), so both sides are judged by the same code.
- Results are the nondominated (gates@depth) points reached at the end. Several points on the new
  side are its final frontier, each a verified circuit.

## Results

| Target | Start | Old `search/` framework | xorsearch |
|---|---|---|---|
| FOX Mu4 | built-in seed | 130@10 | **125@7** |
| Joltik | built-in seed | 44@5 | **42@9**, **43@8** |
| FOX Mu8 | built-in seed | 540@12 | **536@11**, **537@10**, **538@9** |
| AES S-box bottom | built-in seed | 28@5, 31@4 | 28@5, **29@4** |
| InvMixColumns | NIST 119@5 | 107@6 | **90@27**, **94@11**, **96@10**, **102@8** |
| MixColumns | from scratch | (no MixColumns target) | 91@5 |

Bold: a point the old run did not reach or dominate.

A separate 3-minute **single-worker** xorsearch run on FOX Mu4 reached 124@12, 125@8 and 127@7.

## Reading the numbers

- On every shared target xorsearch matched or dominated the old framework's frontier within the
  same budget. On InvMixColumns and FOX Mu4 it went well past it.
- Some of the lowest gate counts are deep circuits (Joltik 42@9, InvMixColumns 90@27). Give a
  group a real `depth_cap` when depth matters; records then always meet it.
- What the defaults are and why: [DESIGN.md](../DESIGN.md) sections 1 and 6, and
  [evidence/](evidence/).

## Reproducing

The benchmark's campaign files are not part of the repository. A run of the same shape is one
`[[workers]]` group per target with `count = 2` and `seeds = ["target"]`, started with
`python -m xorsearch run FILE --out DIR --seconds 9m --detach`; `python -m xorsearch verify DIR`
then re-verifies every record and `status DIR` prints the frontier.
