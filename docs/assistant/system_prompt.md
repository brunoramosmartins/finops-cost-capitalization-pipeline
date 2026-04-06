# Assistant System Guidance

This repository is centered on Codex and related code assistants that can use
local repository context and project-specific skills.

Priorities:

1. Preserve clarity, reproducibility, and documentation quality.
2. Prefer deterministic code paths over clever but opaque implementations.
3. Keep the repository ready for dbt, DuckDB, Dagster, and ML handoff work.
4. Add docstrings to public modules, classes, and functions when they add real value.
5. Align implementation with the repository structure documented in `ROADMAP.md`.

Do not introduce hidden assumptions about accounting logic. If a rule is not
documented, surface it explicitly in code comments or project documentation.
