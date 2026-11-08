#!/usr/bin/env python3
"""exp2 REPORT.md = header/verdict text (report_head.md, written after the analysis) + the
measurement tables printed by analyze_exp2.py (analysis.out) + the design (DESIGN.md)."""
import os
E = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/translog/exp2")
head = open(os.path.join(E, "report_head.md")).read()
out = open(os.path.join(E, "analysis.out")).read()
design = open(os.path.join(E, "DESIGN.md")).read()
body = (head.rstrip() + "\n\n## Measurement tables (analysis.out, from analyze_exp2.py)\n\n```\n" + out.rstrip()
        + "\n```\n\n## Appendix: the pre-registered design (DESIGN.md, verbatim)\n\n"
        + design.replace("\n## ", "\n#### ").replace("# exp2 design", "### exp2 design", 1))
open(os.path.join(E, "REPORT.md"), "w").write(body)
print("wrote REPORT.md", len(body))
