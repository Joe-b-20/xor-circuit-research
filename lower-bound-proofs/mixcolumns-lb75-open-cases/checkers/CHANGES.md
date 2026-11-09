# Changes to the checkers

The checkers are the sprint's independent standard-library checkers, copied from
`research/sprint-2026-11-07/experiments/qcert*/` (branch `sprint-2026-11-07-linear-maps`). In the
originals each checker looks for its certificate file next to itself. Here the certificate files are in
`../certificates/`, so one line per checker was changed: the default certificate path. Nothing else
changed: not the rows, the coefficients, the case trees, the coverage logic, the pinned `EXPECTED`
counts, or the output file name.

| File | Source | Line | Original | Here |
|---|---|---:|---|---|
| `check_ext75.py` | `qcert/check_ext75.py` | 225 | `Path(__file__).with_name('CERTIFICATES_EXT75.json')` | `Path(__file__).resolve().parent.parent / 'certificates' / 'CERTIFICATES_EXT75.json'` |
| `check_cases75.py` | `qcert2/check_cases75.py` | 390 | `Path(__file__).with_name('CERTIFICATES_CASES75.json')` | `Path(__file__).resolve().parent.parent / 'certificates' / 'CERTIFICATES_CASES75.json'` |
| `check_cases3.py` | `qcert3/check_cases3.py` | 437 | `Path(__file__).with_name('CERTIFICATES_CASES75_B3.json')` | `Path(__file__).resolve().parent.parent / 'certificates' / 'CERTIFICATES_CASES75_B3.json'` |
| `check_cases4.py` | `qcert4/check_cases4.py` | 298 | `Path(__file__).with_name('CERTIFICATES_CASES75_B4.json')` | `Path(__file__).resolve().parent.parent / 'certificates' / 'CERTIFICATES_CASES75_B4.json'` |
| `check_cases3_copy.py` | `qcert4/check_cases3_copy.py` = `qcert3/check_cases3.py` | none | unchanged, byte-identical (SHA-256 `9319b103e1f6c7a4cbff28214cd1e1ed9b80c38d9470adde55f7ee8412b8f8ec`) | |

Full SHA-256 values of the originals:

```text
1b61d02cad7916eae7d492b83a55f21567d9b040be4aeb615e67404ed503ac9f  qcert/check_ext75.py
34acb0deb4fc396e1e182dc1a53f86f3ddeea26824bc7073c6c7258d3973f98e  qcert2/check_cases75.py
9319b103e1f6c7a4cbff28214cd1e1ed9b80c38d9470adde55f7ee8412b8f8ec  qcert3/check_cases3.py
12385c854111b26b9e0b32ada473394b93138eeee3060ea7800f2cd1b6ee94f2  qcert4/check_cases4.py
9319b103e1f6c7a4cbff28214cd1e1ed9b80c38d9470adde55f7ee8412b8f8ec  qcert4/check_cases3_copy.py
```

`diff` of each original against its copy here shows exactly the one line above. The usage lines in
the docstrings still name the bare certificate file; passing a path as the first argument works as
before.

Two behaviours are unchanged and worth knowing:

- Each checker writes its report (`CHECKED_*.json`) next to itself. `verify_all.py` runs the checkers
  in a temporary copy, so this folder stays clean. A direct run such as
  `python3 checkers/check_ext75.py` leaves an untracked `CHECKED_EXT75.json` in `checkers/`.
- `check_cases4.py` imports `check_cases3_copy.py` from its own directory. It also checks
  `CERTIFICATES_PARTIAL75_B4.json` if that file sits next to the certificate file. That file is not
  included, so its `partial_*` counts are skipped, as the checker's pinned-count logic allows.

## Added 2026-11-09: the combined checker and the October finite facts

Both programs come from the recon-check audit folder `~/xs-campaigns/2026-11-09-phase/recon-check/`.

| File | Source (SHA-256 of the original) | Change |
|---|---|---|
| `check_combined75.py` | `check_combined75.py` (`d39893d4f11ce08b7a95e96f2f792b1bc906d9cd5aeb94ef2ffe6bc7398bcfd5`) | lines 32-34, paths only (below) |
| `finite_facts_october.py` | `finite_facts_check.py` (`c7d9bc075edf4a4bb38e285486fcc86adee91f9de599ea9bb068f1b9b531ee68`) | renamed only; content byte-identical |
| `finite_facts_october.recorded.json` | `finite_facts_check.json` (`a5deae2157f7941d99824686e59673caa42c13116455f4b67fe7b64a2f311357`) | renamed only; the audit's recorded run, which `verify_all.py` compares against (timing excluded) |

`check_combined75.py`, lines 32-34:

```text
original:  REPO = Path("/home/joebachir20/xor-circuit-research")
           CHK = REPO / "lower-bound-proofs/mixcolumns-lb75-open-cases/checkers"
           RECON = Path("/home/joebachir20/xs-campaigns/2026-11-09-phase/recon")
here:      HERE = Path(__file__).resolve().parent
           CHK = HERE
           RECON = HERE.parent / "combined"
```

`CHK` is the directory from which it imports `check_cases4.py` and, through it, `check_cases3_copy.py`.
In the original, that directory was this repository's `checkers/`, the same files as here. `RECON` is
where it finds its two default certificate files, now `../combined/`. `REPO` was used only to build
`CHK`. Nothing else changed: not the push-row transcription, the coverage code, or the pinned
`EXPECTED` counts. The checker writes `CHECKED_COMBINED75.json` next to itself.

`finite_facts_october.py` reads no files. It writes its output next to itself as
`finite_facts_october.json` (the original wrote `finite_facts_check.json`; the name follows the
script's file name). The script asserts only a few internal facts, such as the FIPS-197 example. The
expected counts are checked by `verify_all.py`, which pins the headline counts and requires the whole
output to equal the recorded run.
