# Rebuild the formatted review PDF

The mathematical source is `../PROOF.md`. These LaTeX files are the exact typeset source of the included PDF.

From this directory, run `xelatex -interaction=nonstopmode -halt-on-error proof.tex` three times to resolve the contents and page references. Copy the resulting `proof.pdf` to `../PROOF.pdf` if desired.

Requirements: XeLaTeX with the packages listed in `proof.tex`, Latin Modern text and math fonts, and DejaVu Sans Mono. No external image files are required. Rebuilding the PDF is separate from checking the proof; the mathematical verifier needs only the dependencies listed in the main README.
