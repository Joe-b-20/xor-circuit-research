# Supplement: four inherited modules

The 2026-10-23 ZIP edition of this package omits four modules that `technical/verify_structure.py`
imports from `technical/inherited/`: `build_lp.py`, `model3.py`, and their dependencies `cuts.py`
and `mcmatrix.py`. Its full command failed with `ModuleNotFoundError`.

- `inherited/` holds the four files unchanged from the author's `slp-plateau-search` repository,
  commit `bdcf83be629b81a0560366845e203f9317243858`, path `bounds/depth3_gte81/`.
  [SOURCE_HASHES.json](SOURCE_HASHES.json) gives their SHA-256 values and Git blobs.
  Matching them to the older source ZIP named in `../PROVENANCE.md` is not established.
- `../verify_all.py` checks these hashes and copies the files into its temporary `technical/`
  tree. No original file or certificate is modified.
- [LICENSE](LICENSE) is that repository's MIT notice, kept verbatim. The paths in its scope note
  refer to that repository, not to this one.

A full replay with these modules passed on 2026-10-23; its run records are not included here. `../verification/fresh_audit_2026-10-23/` is the earlier full run, made directly
from the source archive.
