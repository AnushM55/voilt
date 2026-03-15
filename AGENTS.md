# AGENTS.md

## Purpose
- Single source of truth for how contributors and coding agents work in `voilt`.
- Keep delivery phase-based: edge first, then server, then UI.

## Project Structure
- `dataset/` - YOLO dataset config and data pointers (`data.yaml`, train/val splits).
- `edge/` - Raspberry Pi capture, detection, tracking, violation rules, queue, uploader.
- `server/` - ingest API, verification worker, OCR/plate extraction, PostGIS persistence.
- `ui/` - dashboard, map, event review, device and event monitoring.
- `shared/` - shared schemas, enums, payload contracts, config models.
- `tests/` - unit, integration, end-to-end, and on-device test harnesses.
- `scripts/` - helper scripts for setup, lint, test, export, and maintenance.

## Core Stack / Tools
- Python: `3.12+`
- Env + package management: `uv`
- Lint + format: `ruff` (mandatory)
- Type checks: `mypy`
- Tests: `pytest`
- Pre-commit hooks: `pre-commit`
- Edge vision runtime target: `ncnn`
- Backend API: `FastAPI`
- Database: `PostgreSQL + PostGIS`

## Mandatory Commands (before commit)
- Format: `uv run ruff format .`
- Lint fix: `uv run ruff check . --fix`
- Lint verify: `uv run ruff check .`
- Tests: `uv run pytest`

## Coding Style
- Use type hints on public functions, methods, and module-level constants.
- Keep functions small and single-purpose; prefer composition over deep nesting.
- Favor explicit names over abbreviations.
- Avoid hidden global state; inject dependencies where practical.
- Raise specific exceptions; do not silently swallow failures.
- Keep logs structured and actionable (include IDs: `event_id`, `device_id`, `track_id`).
- Keep modules cohesive; avoid circular imports.
- Use ASCII by default unless file/content requires Unicode.

## Edge-Side Rules
- Edge scope: detection + tracking + violation decision only.
- No OCR on edge (plate extraction/reading is backend concern).
- Deduplicate using tracking state and violation emission rules.
- Persist unsent events in lightweight durable queue (SQLite-based).
- Optimize for stable accuracy and low duplicate rate over raw FPS.

## Data / Contract Rules
- Do not change shared event payload schema without updating:
  - `shared/` schema definitions
  - server ingest validation
  - edge payload builders
  - contract tests
- Include idempotency key for every emitted event.
- Store coarse location with `lat`, `lon`, `accuracy_m`, `source`.

## Commit Rules
- Commit messages: imperative mood, concise, scoped.
  - Example: `edge: add track-based violation dedup logic`
- One logical change per commit; avoid mixing refactor + feature + formatting noise.
- Run format, lint, and tests before commit.
- Never commit secrets (`.env`, keys, credentials, tokens, private model artifacts).
- Do not amend shared history unless explicitly required by maintainers.

## Branch / PR Rules
- Branch naming:
  - `feat/<area>-<short-desc>`
  - `fix/<area>-<short-desc>`
  - `chore/<area>-<short-desc>`
- PR should include:
  - what changed
  - why it changed
  - how it was tested
  - rollout/ops notes if behavior changes

## Quality Gate
- Minimum acceptance for any code change:
  - formatted with `ruff`
  - lint passes
  - relevant tests pass
  - docs/contracts updated when interfaces change

## Security / Privacy
- Treat detection evidence as sensitive.
- Minimize retained media; keep retention policy explicit.
- Mask secrets in logs and never print credentials.

## Working Agreement
- Build phase-by-phase:
  1. Edge
  2. Server
  3. UI
- Do not start next phase core work until current phase exit criteria are met.
