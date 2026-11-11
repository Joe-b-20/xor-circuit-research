# Structural study of linear XOR circuits (started 2026-11-11)

Branch `phase-2026-11-09`. This directory replaces the earlier proof-work plan (SAT, enumeration,
case elimination at G = 75). Nothing here continues that queue. The published bound stays 75; the
best construction stays 88; optimality is open.

Aim: understand what forces XOR circuits to have unavoidable cost, with AES MixColumns as the
central example, and obtain arguments that cover whole families of circuits by one reason.

- `RECORD.md`: the research record. Proved statements, conjectures, counterexamples, failed ideas
  and unresolved dependencies, kept apart, each with its status.
- `tools/`: small standard-library scripts that examine recorded circuits or check algebra. They
  search nothing and prove nothing by themselves.
- One sub-directory per delegated investigation, each with its own `REPORT.md` and scripts.

Status words used throughout: **proved** (complete argument written here), **conditional** (proved
given a named hypothesis), **conjectured**, **observed** (seen on recorded circuits or small cases;
not a statement about all circuits), **disproved**. Reviews by language models are called machine
reviews; none is a human review or a formal verification.
